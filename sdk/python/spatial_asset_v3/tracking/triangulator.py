"""Multi-view triangulation: 2D pixel observations → 3D world position.

Uses the midpoint of the closest approach between two unit-direction rays
(closed-form solution). For N > 2 cameras, pairs are averaged.

T_world_cam convention is inherited from CameraSpec: the camera origin in
world frame is T_world_cam[:3, 3] and the rotation is T_world_cam[:3, :3].
"""
from __future__ import annotations

import numpy as np
from .._config import CameraSpec


def triangulate(
    pixels: dict[str, tuple[float, float]],
    cam_map: dict[str, CameraSpec],
) -> tuple[np.ndarray | None, float]:
    """Triangulate a 3D world point from pixel observations in ≥2 cameras.

    Parameters
    ----------
    pixels : {cam_id: (x_px, y_px)}
    cam_map : {cam_id: CameraSpec}

    Returns
    -------
    P_world : np.ndarray shape (3,) or None if fewer than 2 cameras
    reprojection_error_px : mean error across cameras (float)
    """
    cam_ids = [cid for cid in pixels if cid in cam_map]
    if len(cam_ids) < 2:
        return None, float("inf")

    # Collect all pairwise estimates, then average
    points = []
    for i in range(len(cam_ids)):
        for j in range(i + 1, len(cam_ids)):
            cid0, cid1 = cam_ids[i], cam_ids[j]
            P = _two_ray(pixels[cid0], cam_map[cid0], pixels[cid1], cam_map[cid1])
            if P is not None:
                points.append(P)

    if not points:
        return None, float("inf")

    P_world = np.mean(points, axis=0)
    reproj_err = _reprojection_error(P_world, pixels, cam_map)
    return P_world, reproj_err


def _two_ray(
    px0: tuple[float, float], cam0: CameraSpec,
    px1: tuple[float, float], cam1: CameraSpec,
) -> np.ndarray | None:
    """Midpoint of closest approach between two camera rays (closed form)."""
    o0 = cam0.position_world
    d0 = cam0.R_world_cam @ cam0.intrinsics.unproject(px0[0], px0[1])  # unit vector in world

    o1 = cam1.position_world
    d1 = cam1.R_world_cam @ cam1.intrinsics.unproject(px1[0], px1[1])

    # Minimise |P0 - P1|² where P0 = o0 + t*d0, P1 = o1 + s*d1
    # Solution: [A, -B; B, -C] [t; s] = [e0; e1]
    #   A = d0·d0, B = d0·d1, C = d1·d1
    #   e0 = d0·(o0-o1), e1 = d1·(o0-o1)
    A = float(np.dot(d0, d0))
    B = float(np.dot(d0, d1))
    C = float(np.dot(d1, d1))
    diff = o0 - o1
    e0 = float(np.dot(d0, diff))
    e1 = float(np.dot(d1, diff))

    det = B * B - A * C
    if abs(det) < 1e-12:
        return None  # parallel rays

    t = (C * e0 - B * e1) / det
    s = (B * e0 - A * e1) / det

    P0 = o0 + t * d0
    P1 = o1 + s * d1
    return (P0 + P1) * 0.5


def _reprojection_error(
    P_world: np.ndarray,
    pixels: dict[str, tuple[float, float]],
    cam_map: dict[str, CameraSpec],
) -> float:
    errors = []
    for cid, (x_obs, y_obs) in pixels.items():
        cam = cam_map.get(cid)
        if cam is None:
            continue
        proj = cam.project_world(P_world)
        if proj is None:
            errors.append(1e6)
            continue
        dx = proj[0] - x_obs
        dy = proj[1] - y_obs
        errors.append(float(np.sqrt(dx * dx + dy * dy)))
    return float(np.mean(errors)) if errors else float("inf")
