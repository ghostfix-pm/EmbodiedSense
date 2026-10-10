from pathlib import Path

import pytest

from embodiedsense.core.config import load_config
from embodiedsense.core.types import FrameRef
from embodiedsense.processing.sync import associate


def ref(t):
    return FrameRef(t, str(t), Path("image.png"), "image.png", 0)


def test_config():
    assert load_config("configs/tum_rgbd.yaml").camera.depth_scale == 5000


def test_match_boundary_tie_missing():
    result = list(associate([ref(10), ref(30)], [ref(12), ref(8)], 2))
    assert result[0][1].timestamp_ns == 8
    assert result[1][1] is None


def test_empty_depth():
    assert list(associate([ref(10)], [], 2))[0][1] is None


def test_negative_tolerance():
    with pytest.raises(ValueError):
        list(associate([], [], -1))
