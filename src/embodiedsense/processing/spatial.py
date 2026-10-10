import numpy as np

from embodiedsense.core.types import CameraCalibration


def project_depth(depth, rgb, camera: CameraCalibration, min_depth=0.2, max_depth=10.0, stride=1):
    """Project registered pinhole pixels; optical axes: x right, y down, z forward.

    Output remains in the camera frame. Does not estimate camera pose or build a world map.
    """
    if depth.shape != (camera.height, camera.width) or rgb.shape != (*depth.shape, 3):
        raise ValueError("Image dimensions do not match calibration")
    if not isinstance(stride, int) or stride < 1:
        raise ValueError("stride must be positive integer")
    if not np.isfinite([min_depth, max_depth]).all() or not 0 < min_depth < max_depth:
        raise ValueError("Invalid depth range")
    z = depth[::stride, ::stride].astype(np.float64) / camera.depth_scale
    v, u = np.mgrid[0 : camera.height : stride, 0 : camera.width : stride]
    valid = np.isfinite(z) & (z >= min_depth) & (z <= max_depth)
    points = np.stack(
        ((u - camera.cx) * z / camera.fx, (v - camera.cy) * z / camera.fy, z), axis=-1
    )[valid]
    return points.astype(np.float32), rgb[::stride, ::stride][valid].copy()


def transform_points(points, target_from_source):
    """Apply a proper rigid 4x4 T_target_source transform to Nx3 metric points."""
    transform = np.asarray(target_from_source, dtype=np.float64)
    if transform.shape != (4, 4) or not np.isfinite(transform).all():
        raise ValueError("Expected finite 4x4 transform")
    rotation = transform[:3, :3]
    if (
        not np.allclose(transform[3], [0, 0, 0, 1])
        or not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-6)
        or not np.isclose(np.linalg.det(rotation), 1, atol=1e-6)
    ):
        raise ValueError("Expected proper rigid transform")
    points = np.asarray(points)
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise ValueError("Expected finite Nx3 points")
    return points @ rotation.T + transform[:3, 3]
