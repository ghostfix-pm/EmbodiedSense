"""Run from the repository root: uv run python examples/read_observations.py."""

from embodiedsense.core.config import load_config
from embodiedsense.core.pipeline import RGBDPipeline

pipeline = RGBDPipeline("data/synthetic", load_config("configs/synthetic.yaml"))
for observation in pipeline.iter_observations(limit=3):
    print(
        observation.rgb.original_timestamp,
        observation.quality.status,
        observation.points_m.shape,
        observation.calibration.frame_id,
    )
