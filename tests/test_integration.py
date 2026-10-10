import json
import subprocess
import sys

import numpy as np
import pytest

from embodiedsense.core.config import load_config
from embodiedsense.core.pipeline import RGBDPipeline
from embodiedsense.sensors.synthetic import make_fixture
from embodiedsense.storage import RecordingWriter, replay


def test_record_replay_integrity(tmp_path):
    dataset = tmp_path / "synthetic"
    make_fixture(dataset, frames=3)
    config = load_config("configs/synthetic.yaml")
    source = list(RGBDPipeline(dataset, config).iter_observations())
    output = tmp_path / "recording"
    writer = RecordingWriter(output, config, "synthetic")
    for obs in source:
        writer.write(obs)
    writer.close()
    loaded = list(replay(output))
    assert len(loaded) == 3
    for original, restored in zip(source, loaded, strict=True):
        assert original.rgb.timestamp_ns == restored.rgb.timestamp_ns
        assert original.quality == restored.quality
        np.testing.assert_array_equal(original.points_m, restored.points_m)
        np.testing.assert_array_equal(original.rgb.payload, restored.rgb.payload)
    with pytest.raises(FileExistsError):
        RecordingWriter(output, config, "synthetic")
    (output / "frames/000000.npz").write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="checksum"):
        list(replay(output))


def test_cli_roundtrip(tmp_path):
    data = tmp_path / "synthetic"
    output = tmp_path / "run"
    make_fixture(data, frames=3)
    command = [sys.executable, "-m", "embodiedsense.cli"]
    result = subprocess.run(
        command
        + [
            "run",
            "--config",
            "configs/synthetic.yaml",
            "--data-root",
            str(data),
            "--out",
            str(output),
            "--ply",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((output / "report.json").read_text())
    assert report["observations"] == 3
    assert report["total_points"] == 3 * (32 * 24 - 1)
    assert len(list(output.glob("frames/*.ply"))) == 3
    result = subprocess.run(
        command + ["replay", "--recording", str(output)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["replayed_observations"] == 3
    result = subprocess.run(
        command
        + [
            "run",
            "--config",
            "configs/synthetic.yaml",
            "--data-root",
            str(data),
            "--out",
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2  # refuse overwriting an existing run


def test_rerun_headless(tmp_path):
    pytest.importorskip("rerun")
    from embodiedsense.visualization.viewer import RerunWriter

    data = tmp_path / "synthetic"
    make_fixture(data, frames=2)
    target = tmp_path / "test.rrd"
    viz = RerunWriter(target)
    for obs in RGBDPipeline(data, load_config("configs/synthetic.yaml")).iter_observations():
        viz.write(obs)
    viz.close()
    assert target.stat().st_size > 100


def test_incomplete_recording_rejected(tmp_path):
    writer = RecordingWriter(tmp_path / "incomplete", load_config("configs/synthetic.yaml"), "test")
    writer.close(complete=False)
    with pytest.raises(ValueError, match="incomplete"):
        list(replay(tmp_path / "incomplete"))


def test_no_core_viewer_import():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from embodiedsense.core.pipeline import RGBDPipeline; "
            "import sys; assert 'rerun' not in sys.modules",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_depth_reuse_and_bad_frame_do_not_stop_pipeline(tmp_path):
    data = tmp_path / "synthetic"
    make_fixture(data, frames=4)
    lines = (data / "depth.txt").read_text().splitlines()
    (data / "depth.txt").write_text("\n".join(lines[:2]))
    (data / "rgb/0.png").write_bytes(b"broken")
    from dataclasses import replace

    config = replace(load_config("configs/synthetic.yaml"), max_delta_ms=100)
    observations = list(RGBDPipeline(data, config).iter_observations())
    assert len(observations) == 4
    assert observations[0].quality.status == "INVALID"
    assert "DEPTH_REUSED" in observations[1].quality.flags
    assert len(observations[1].points_m) > 0
