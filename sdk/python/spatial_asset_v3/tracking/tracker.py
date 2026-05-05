"""Build event-tracklet-3d and motion-evidence-3d assets from accumulated frames.

For each time window:
  1. Compute weighted centroid of each camera's event frame.
  2. Match centroids across cameras by window timestamp (exact match, no gap filling).
  3. Triangulate → TrackletPoint.
Link points in time order to produce one tracklet per trajectory (identified
by index order in scene config).
"""
from __future__ import annotations

import datetime
from typing import Any

import numpy as np

from .._config import CameraSpec
from ..event.accumulator import frame_centroid
from .triangulator import triangulate


def build_tracklets(
    frames_by_cam: dict[str, list[dict]],
    cam_map: dict[str, CameraSpec],
    n_trajectories: int = 1,
) -> list[dict[str, Any]]:
    """Build event-tracklet-3d assets.

    Assumes one trajectory → one tracklet (reference fixture assumption).
    For multi-trajectory scenes, n_trajectories controls the expected cluster count
    per frame (not yet implemented; n_trajectories > 1 currently falls back to 1).

    Returns list of event-tracklet-3d asset dicts.
    """
    cam_ids = list(frames_by_cam.keys())
    if len(cam_ids) < 2:
        raise ValueError("Need at least two cameras for triangulation")

    # Index frames by (cam_id, t_start_us) for O(1) lookup
    frame_index: dict[tuple[str, int], dict] = {}
    for cam_id, frames in frames_by_cam.items():
        for f in frames:
            frame_index[(cam_id, f["time_window"]["t_start_us"])] = f

    # Collect all window start times present in ALL cameras
    starts_per_cam = [
        {f["time_window"]["t_start_us"] for f in frames}
        for frames in frames_by_cam.values()
    ]
    common_starts = sorted(set.intersection(*starts_per_cam))

    points = []
    source_frame_ids: list[str] = []

    for t_start in common_starts:
        # Get centroid per camera
        pixels: dict[str, tuple[float, float]] = {}
        for cam_id in cam_ids:
            f = frame_index.get((cam_id, t_start))
            if f is None:
                continue
            frame_arr = f.get("_frame")
            if frame_arr is None:
                continue
            c = frame_centroid(frame_arr)
            if c is not None:
                pixels[cam_id] = c
                if f["id"] not in source_frame_ids:
                    source_frame_ids.append(f["id"])

        if len(pixels) < 2:
            continue  # no match this window

        P_world, reproj = triangulate(pixels, cam_map)
        if P_world is None:
            continue

        t_mid = t_start + (
            frame_index[(cam_ids[0], t_start)]["time_window"]["t_end_us"] - t_start
        ) // 2

        point: dict[str, Any] = {
            "t_us": t_mid,
            "position": P_world.tolist(),
            "reprojection_error_px": round(reproj, 4),
            "source_cameras": list(pixels.keys()),
        }
        points.append(point)

    if not points:
        return []

    tracklet_id = "t_obj0"
    tracklet: dict[str, Any] = {
        "version": "3.0",
        "kind": "event-tracklet-3d",
        "id": f"tracklet_{tracklet_id}",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "tracklet_id": tracklet_id,
        "camera_ids": cam_ids,
        "crs": "world",
        "time_range": {
            "t_start_us": points[0]["t_us"],
            "t_end_us": points[-1]["t_us"],
        },
        "points": points,
        "derived_from": [{"id": fid, "role": "event-frame-2d"} for fid in source_frame_ids],
    }
    return [tracklet]


def build_motion_evidence(
    tracklets: list[dict],
    crs: str = "world",
) -> dict[str, Any]:
    """Aggregate tracklets into a motion-evidence-3d asset."""
    all_t = [p["t_us"] for t in tracklets for p in t["points"]]
    all_pos = np.array([p["position"] for t in tracklets for p in t["points"]])

    bounds = {
        "min": all_pos.min(axis=0).tolist(),
        "max": all_pos.max(axis=0).tolist(),
    }

    return {
        "version": "3.0",
        "kind": "motion-evidence-3d",
        "id": "motion_evidence",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "tracklet_ids": [t["tracklet_id"] for t in tracklets],
        "crs": crs,
        "time_range": {"t_start_us": min(all_t), "t_end_us": max(all_t)},
        "scene_bounds": bounds,
        "derived_from": [{"id": t["id"], "role": "event-tracklet-3d"} for t in tracklets],
    }
