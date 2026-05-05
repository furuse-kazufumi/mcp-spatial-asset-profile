"""Synthetic event stream generation from scene + camera configs.

Model: at each dt_us step, project each active trajectory centre onto each
camera. Emit one positive event at the nearest integer pixel. This simplified
model is sufficient for testing the pipeline against known-answer ground truth;
it does not attempt to model contrast thresholds or sensor noise.

Failure injection (opt-in via generate() inject parameter):
  calibration_error — 5-degree X-axis rotation added to cam1 extrinsics
  time_skew         — 5000 us offset added to cam1 timestamps
  hot_pixel         — 50 fixed-position spurious events spread uniformly
  drop_polarity     — all polarities set to +1 (already the default, this is a no-op test)
"""
from __future__ import annotations

import numpy as np
from typing import NamedTuple

from .._config import CameraSpec, SceneConfig


class Event(NamedTuple):
    x: int
    y: int
    t_us: int
    polarity: int  # +1 or -1


def generate(
    scene: SceneConfig,
    cameras: list[CameraSpec],
    dt_us: int = 1000,
    inject: str | None = None,
) -> dict[str, list[Event]]:
    """Generate synthetic event streams for each camera.

    Returns {camera_id: [Event, ...]} with events in ascending t_us order.
    """
    cameras = _apply_inject_pre(cameras, inject, scene)
    rng = np.random.default_rng(scene.seed)

    streams: dict[str, list[Event]] = {cam.id: [] for cam in cameras}

    times = range(0, scene.duration_us + dt_us, dt_us)
    for t in times:
        for traj in scene.trajectories:
            P_world = traj.eval(t)
            if P_world is None:
                continue
            for cam in cameras:
                proj = cam.project_world(P_world)
                if proj is None:
                    continue
                x_px = int(round(proj[0]))
                y_px = int(round(proj[1]))
                # clamp to sensor bounds
                w, h = cam.resolution
                x_px = max(0, min(w - 1, x_px))
                y_px = max(0, min(h - 1, y_px))
                t_emit = t + cam.time_offset_us
                streams[cam.id].append(Event(x=x_px, y=y_px, t_us=t_emit, polarity=+1))

    if inject == "hot_pixel":
        _inject_hot_pixels(streams, cameras, scene, rng, n=50)

    return streams


# ── Inject helpers ────────────────────────────────────────────────────────────

def _apply_inject_pre(cameras: list[CameraSpec], inject: str | None, scene: SceneConfig) -> list[CameraSpec]:
    """Return a (possibly modified) camera list for the given inject mode."""
    import copy
    cameras = copy.deepcopy(cameras)
    if inject == "calibration_error":
        # 5-degree rotation around X axis added to cam1 extrinsics
        theta = np.radians(5.0)
        c, s = np.cos(theta), np.sin(theta)
        Rx = np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]], dtype=float)
        cam = next(cam for cam in cameras if cam.id != cameras[0].id)
        cam.T_world_cam = cam.T_world_cam @ Rx
    elif inject == "time_skew":
        # 5 ms clock offset on cam1
        cam = next(cam for cam in cameras if cam.id != cameras[0].id)
        cam.time_offset_us += 5000
    return cameras


def _inject_hot_pixels(
    streams: dict[str, list[Event]],
    cameras: list[CameraSpec],
    scene: SceneConfig,
    rng: np.random.Generator,
    n: int,
) -> None:
    """Add n spurious events at random fixed pixels spread over the scene duration."""
    for cam in cameras:
        w, h = cam.resolution
        xs = rng.integers(0, w, size=n)
        ys = rng.integers(0, h, size=n)
        ts = rng.integers(0, scene.duration_us, size=n)
        for x, y, t in zip(xs.tolist(), ys.tolist(), ts.tolist()):
            streams[cam.id].append(Event(x=int(x), y=int(y), t_us=int(t), polarity=+1))
        streams[cam.id].sort(key=lambda e: e.t_us)
