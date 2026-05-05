"""
Mock VLLM summariser: produces a vllm-summary asset from a v3 asset bundle.

Uses template-based text generation so tests are fully deterministic and
require no external API calls. The provenance block records model='mock'
and a SHA-256 hash of the rendered prompt so reproducibility can be checked.
"""
from __future__ import annotations

import datetime
import hashlib
import uuid
from typing import Any


_PROMPT_VERSION = "v1"
_TEMPLATE = (
    "Scene analysis: {n_tracklets} moving object(s) detected over "
    "{duration_ms:.1f} ms. "
    "Scene bounds: X=[{xmin:.3f},{xmax:.3f}] Y=[{ymin:.3f},{ymax:.3f}] "
    "Z=[{zmin:.3f},{zmax:.3f}] m. "
    "Mean reprojection error: {mean_reproj:.2f} px. "
    "Total event frames: {n_frames}. "
    "Cameras: {camera_list}."
)


def summarise(
    assets: list[dict[str, Any]],
    language: str = "en",
    source_id: str | None = None,
) -> dict[str, Any]:
    """Return a vllm-summary asset dict derived from *assets*.

    Parameters
    ----------
    assets:
        All assets in the bundle (event-frame-2d, event-tracklet-3d,
        motion-evidence-3d). The function selects what it needs.
    language:
        BCP-47 language tag for the generated text.
    source_id:
        If given, added to derived_from.
    """
    tracklets = [a for a in assets if a.get("kind") == "event-tracklet-3d"]
    frames    = [a for a in assets if a.get("kind") == "event-frame-2d"]
    motion    = next((a for a in assets if a.get("kind") == "motion-evidence-3d"), None)

    stats = _extract_stats(tracklets, frames, motion)
    prompt_text = _TEMPLATE.format(**stats)
    prompt_hash = hashlib.sha256(prompt_text.encode()).hexdigest()[:16]

    derived: list[dict] = []
    if motion:
        derived.append({"id": motion["id"], "role": "motion-evidence-3d"})
    for t in tracklets:
        derived.append({"id": t["id"], "role": "event-tracklet-3d"})
    if source_id:
        derived.append({"id": source_id, "role": "source"})

    tokens_in  = len(prompt_text.split())
    tokens_out = len(prompt_text.split())

    asset: dict[str, Any] = {
        "version": "3.0",
        "kind": "vllm-summary",
        "id": f"vllm-summary:{uuid.uuid4()}",
        "name": "Scene motion summary",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "derived_from": derived,
        "text": prompt_text,
        "language": language,
        "provenance": {
            "model": "mock",
            "prompt_version": _PROMPT_VERSION,
            "temperature": 0.0,
            "prompt_hash": prompt_hash,
            "tokens_input": tokens_in,
            "tokens_output": tokens_out,
        },
    }
    return asset


def _extract_stats(
    tracklets: list[dict],
    frames: list[dict],
    motion: dict | None,
) -> dict[str, Any]:
    n_tracklets = len(tracklets)
    n_frames    = len(frames)

    # time range from motion or tracklets
    t_start, t_end = _get_time_range(tracklets, motion)
    duration_ms = (t_end - t_start) / 1_000.0 if t_end > t_start else 0.0

    # scene bounds from motion or tracklet points
    xmin, xmax, ymin, ymax, zmin, zmax = _get_bounds(tracklets, motion)

    # mean reprojection error across all tracklet points
    mean_reproj = _mean_reproj(tracklets)

    # camera list
    cam_ids: set[str] = set()
    for t in tracklets:
        cam_ids.update(t.get("camera_ids", []))
    for f in frames:
        cid = f.get("camera_id")
        if cid:
            cam_ids.add(cid)
    camera_list = ", ".join(sorted(cam_ids)) if cam_ids else "unknown"

    return {
        "n_tracklets": n_tracklets,
        "n_frames": n_frames,
        "duration_ms": duration_ms,
        "xmin": xmin, "xmax": xmax,
        "ymin": ymin, "ymax": ymax,
        "zmin": zmin, "zmax": zmax,
        "mean_reproj": mean_reproj,
        "camera_list": camera_list,
    }


def _get_time_range(
    tracklets: list[dict],
    motion: dict | None,
) -> tuple[int, int]:
    if motion and "time_range" in motion:
        tr = motion["time_range"]
        return tr["t_start_us"], tr["t_end_us"]
    starts, ends = [], []
    for t in tracklets:
        if "time_range" in t:
            starts.append(t["time_range"]["t_start_us"])
            ends.append(t["time_range"]["t_end_us"])
        for pt in t.get("points", []):
            starts.append(pt["t_us"])
            ends.append(pt["t_us"])
    return (min(starts) if starts else 0, max(ends) if ends else 0)


def _get_bounds(
    tracklets: list[dict],
    motion: dict | None,
) -> tuple[float, float, float, float, float, float]:
    if motion and "scene_bounds" in motion:
        b = motion["scene_bounds"]
        mn, mx = b["min"], b["max"]
        return mn[0], mx[0], mn[1], mx[1], mn[2], mx[2]
    xs, ys, zs = [], [], []
    for t in tracklets:
        for pt in t.get("points", []):
            pos = pt.get("position", [])
            if len(pos) == 3:
                xs.append(pos[0]); ys.append(pos[1]); zs.append(pos[2])
    if not xs:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def _mean_reproj(tracklets: list[dict]) -> float:
    errors = []
    for t in tracklets:
        for pt in t.get("points", []):
            e = pt.get("reprojection_error_px")
            if e is not None:
                errors.append(e)
    return sum(errors) / len(errors) if errors else 0.0
