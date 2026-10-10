from dataclasses import replace
from pathlib import Path

import numpy as np

from embodiedsense.core.config import PipelineConfig
from embodiedsense.core.types import RGBDObservation
from embodiedsense.processing.spatial import project_depth
from embodiedsense.processing.sync import associate
from embodiedsense.processing.validation import validate
from embodiedsense.sensors.rgbd_loader import load_packet, read_index


class RGBDPipeline:
    """Lazy image decoding; holds metadata indexes, at most one RGB-D pair in core."""

    def __init__(self, data_root: str | Path, config: PipelineConfig):
        self.root = Path(data_root).resolve()
        self.config = config
        gap = int(config.max_gap_ms * 1_000_000)
        self.rgb_refs = read_index(self.root, "rgb.txt", gap)
        self.depth_refs = read_index(self.root, "depth.txt", gap)

    def iter_observations(self, limit: int | None = None):
        if limit is not None and limit <= 0:
            raise ValueError("limit must be positive")
        config = self.config
        used = set()
        for index, (rgb_ref, depth_ref) in enumerate(
            associate(self.rgb_refs, self.depth_refs, int(config.max_delta_ms * 1_000_000))
        ):
            if limit is not None and index >= limit:
                break
            rgb = load_packet(rgb_ref, "rgb", self.root.name, config.camera)
            depth = None
            delta = None
            if depth_ref is not None:
                depth = load_packet(depth_ref, "depth", self.root.name, config.camera)
                delta = depth.timestamp_ns - rgb.timestamp_ns
                if depth_ref.sequence_id in used:
                    depth = replace(depth, flags=depth.flags + ("DEPTH_REUSED",))
                used.add(depth_ref.sequence_id)
            quality = validate(rgb, depth, config)
            points = np.empty((0, 3), dtype=np.float32)
            colors = np.empty((0, 3), dtype=np.uint8)
            if quality.status in ("OK", "WARN"):
                points, colors = project_depth(
                    depth.payload,
                    rgb.payload,
                    config.camera,
                    config.min_depth_m,
                    config.max_depth_m,
                    config.stride,
                )
            points.setflags(write=False)
            colors.setflags(write=False)
            yield RGBDObservation(rgb, depth, config.camera, quality, delta, points, colors)
