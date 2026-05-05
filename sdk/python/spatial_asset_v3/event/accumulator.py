"""Accumulate event streams into event-frame-2d asset envelopes."""
from __future__ import annotations

import datetime
import numpy as np
from typing import Any

from .generator import Event
from .._config import CameraSpec


def accumulate(
    events: list[Event],
    cam: CameraSpec,
    window_us: int = 10_000,
    stride_us: int | None = None,
    acc_type: str = "polarity-signed",
    bundle_id: str = "bundle",
    source_id: str = "config:scene",
) -> list[dict[str, Any]]:
    """Split events into windows and produce event-frame-2d asset envelopes.

    Returns a list of asset dicts (without 'representations' data paths —
    caller should save .npy files and fill 'representations' if needed).
    """
    if stride_us is None:
        stride_us = window_us

    if not events:
        return []

    duration_us = max(e.t_us for e in events)
    assets = []
    t = min(e.t_us for e in events)
    w, h = cam.resolution

    while t < duration_us:
        t_end = t + window_us
        window = [e for e in events if t <= e.t_us < t_end]

        frame = _accumulate_frame(window, w, h, acc_type)
        frame_id = f"{cam.id}_w{t:010d}"

        asset: dict[str, Any] = {
            "version": "3.0",
            "kind": "event-frame-2d",
            "id": frame_id,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "camera_id": cam.id,
            "time_window": {"t_start_us": t, "t_end_us": t_end},
            "accumulator": acc_type,
            "sensor": {
                "resolution": list(cam.resolution),
                "intrinsics": cam.intrinsics.to_dict(),
            },
            "event_count": len(window),
            "derived_from": [{"id": source_id, "role": "event-stream"}],
            "_frame": frame,   # internal: numpy array; stripped before serialisation
        }
        assets.append(asset)
        t += stride_us

    return assets


def _accumulate_frame(events: list[Event], w: int, h: int, acc_type: str) -> np.ndarray:
    frame = np.zeros((h, w), dtype=np.float32)
    for e in events:
        if 0 <= e.x < w and 0 <= e.y < h:
            if acc_type == "polarity-signed":
                frame[e.y, e.x] += e.polarity
            elif acc_type == "count":
                frame[e.y, e.x] += 1.0
            elif acc_type == "time-surface":
                # store raw t_us; caller normalises after the window is complete
                frame[e.y, e.x] = float(e.t_us)
    return frame


def frame_centroid(frame: np.ndarray) -> tuple[float, float] | None:
    """Weighted centroid of activated pixels. Returns (x_px, y_px) or None."""
    total = np.abs(frame).sum()
    if total == 0:
        return None
    h, w = frame.shape
    ys, xs = np.mgrid[0:h, 0:w]
    weights = np.abs(frame)
    cx = float((xs * weights).sum() / total)
    cy = float((ys * weights).sum() / total)
    return cx, cy
