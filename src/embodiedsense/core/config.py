from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml

from embodiedsense.core.types import CameraCalibration


@dataclass(frozen=True)
class PipelineConfig:
    camera: CameraCalibration
    max_delta_ms: float = 20.0
    min_depth_m: float = 0.2
    max_depth_m: float = 10.0
    stride: int = 4
    max_gap_ms: float = 100.0

    def __post_init__(self):
        values = [self.max_delta_ms, self.min_depth_m, self.max_depth_m, self.max_gap_ms]
        if not np.isfinite(values).all():
            raise ValueError("Thresholds must be finite")
        if self.max_delta_ms < 0 or self.max_gap_ms <= 0:
            raise ValueError("Invalid timestamp tolerance/gap threshold")
        if not 0 < self.min_depth_m < self.max_depth_m:
            raise ValueError("Invalid depth range")
        if not isinstance(self.stride, int) or self.stride < 1:
            raise ValueError("stride must be a positive integer")


def load_config(path: str | Path) -> PipelineConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    camera = CameraCalibration(**data.pop("camera"))
    return PipelineConfig(camera=camera, **data)
