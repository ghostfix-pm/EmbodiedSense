from dataclasses import replace

import cv2
import numpy as np
import pytest

from embodiedsense.core.config import PipelineConfig
from embodiedsense.core.pipeline import RGBDPipeline
from embodiedsense.core.types import CameraCalibration
from embodiedsense.processing.spatial import project_depth, transform_points
from embodiedsense.processing.validation import validate
from embodiedsense.sensors.rgbd_loader import load_packet, read_index


@pytest.fixture
def dataset(tmp_path):
    rgb = np.zeros((2, 2, 3), dtype=np.uint8)
    rgb[:, :, 2] = 255  # OpenCV BGR red
    cv2.imwrite(str(tmp_path / "rgb.png"), rgb)
    cv2.imwrite(str(tmp_path / "depth.png"), np.array([[5000, 0], [10000, 5000]], np.uint16))
    (tmp_path / "rgb.txt").write_text("# rgb\n1300000000.000000001 rgb.png\n")
    (tmp_path / "depth.txt").write_text("1300000000.001000001 depth.png\n")
    return tmp_path


@pytest.fixture
def config():
    return PipelineConfig(CameraCalibration(2, 2, 1, 1, 0, 0, 5000, "test"), stride=1)


def test_geometry_and_color(dataset, config):
    obs = next(RGBDPipeline(dataset, config).iter_observations())
    np.testing.assert_allclose(obs.points_m, [[0, 0, 1], [0, 2, 2], [1, 1, 1]])
    np.testing.assert_array_equal(obs.colors_rgb, [[255, 0, 0]] * 3)
    assert obs.rgb.timestamp_ns == 1300000000000000001
    assert obs.sync_delta_ns == 1_000_000
    assert obs.quality.metrics["valid_depth_fraction"] == 0.75
    assert not obs.rgb.payload.flags.writeable


def test_missing_and_corruption(dataset, config):
    pipeline = RGBDPipeline(dataset, replace(config, max_delta_ms=0))
    obs = next(pipeline.iter_observations())
    assert obs.quality.status == "MISSING" and len(obs.points_m) == 0
    (dataset / "depth.png").write_bytes(b"broken")
    obs = next(RGBDPipeline(dataset, config).iter_observations())
    assert obs.quality.status == "INVALID" and "DECODE_FAILED" in obs.quality.flags


def test_index_anomalies_and_exact_time(dataset):
    (dataset / "rgb.txt").write_text("1.0 rgb.png\n1.0 rgb.png\n0.9 rgb.png\n2.0 rgb.png\n")
    refs = read_index(dataset, "rgb.txt", 100_000_000)
    assert refs[1].flags == ("DUPLICATE_TIMESTAMP",)
    assert refs[2].flags == ("TIMESTAMP_BACKWARD",)
    assert refs[3].flags == ("TIMESTAMP_GAP",)


@pytest.mark.parametrize("line", ["nan rgb.png", "1 ../escape.png", "bad", "-1 rgb.png"])
def test_invalid_index(dataset, line):
    (dataset / "rgb.txt").write_text(line)
    with pytest.raises(ValueError):
        read_index(dataset, "rgb.txt", 100)


def test_invalid_shape_and_nonfinite(dataset, config):
    refs = read_index(dataset, "rgb.txt", 100)
    rgb = load_packet(refs[0], "rgb", "test", config.camera)
    bad_depth = replace(rgb, modality="depth", payload=np.full((2, 2), np.nan))
    report = validate(rgb, bad_depth, config)
    assert report.status == "INVALID" and "NONFINITE_DEPTH" in report.flags
    assert (
        validate(replace(rgb, payload=np.zeros((3, 3, 3))), bad_depth, config).status == "INVALID"
    )


def test_rigid_transform():
    transform = np.eye(4)
    transform[:3, 3] = [1, 2, 3]
    np.testing.assert_allclose(transform_points([[0, 0, 1]], transform), [[1, 2, 4]])
    transform[0, 0] = 2
    with pytest.raises(ValueError):
        transform_points([[0, 0, 1]], transform)


def test_project_filters_nan(config):
    depth = np.array([[np.nan, 5000], [0, 60000]])
    points, _ = project_depth(depth, np.zeros((2, 2, 3)), config.camera)
    np.testing.assert_allclose(points, [[1, 0, 1]])
