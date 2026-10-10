from pathlib import Path

import cv2
import numpy as np


def make_fixture(root: Path, frames=12):
    """Deterministic synthetic RGB-D plane, explicitly marked as synthetic."""
    if frames <= 0:
        raise ValueError("frames must be positive")
    root.mkdir(parents=True, exist_ok=False)
    (root / "rgb").mkdir()
    (root / "depth").mkdir()
    rgb_lines, depth_lines = [], []
    y, x = np.mgrid[:48, :64]
    for index in range(frames):
        rgb = np.stack((x * 4, y * 5, np.full_like(x, index * 17 % 256)), axis=-1).astype(np.uint8)
        depth = np.full((48, 64), 5000 + index * 50, np.uint16)
        depth[0, 0] = 0
        cv2.imwrite(str(root / f"rgb/{index}.png"), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        cv2.imwrite(str(root / f"depth/{index}.png"), depth)
        ns = index * 33_333_333
        seconds, fraction = divmod(ns, 1_000_000_000)
        rgb_lines.append(f"{seconds}.{fraction:09d} rgb/{index}.png")
        seconds, fraction = divmod(ns + 2_000_000, 1_000_000_000)
        depth_lines.append(f"{seconds}.{fraction:09d} depth/{index}.png")
    for name, lines in (("rgb", rgb_lines), ("depth", depth_lines)):
        (root / f"{name}.txt").write_text("# SYNTHETIC DATA\n" + "\n".join(lines) + "\n")
    (root / "SOURCE.txt").write_text("Synthetic pinhole plane. Not recorded robot data.\n")
