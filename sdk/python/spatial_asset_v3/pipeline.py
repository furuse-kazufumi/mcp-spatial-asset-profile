"""End-to-end synthetic demo pipeline: scene + cameras → v3 asset bundle."""
from __future__ import annotations

import json
import datetime
from pathlib import Path
from typing import Any

import numpy as np

from ._config import load_cameras, load_scene
from ._validator import validate_bundle
from .event.generator import generate
from .event.accumulator import accumulate
from .tracking.tracker import build_tracklets, build_motion_evidence
from .vllm import summarise


def run(
    scene_path: str | Path,
    cameras_path: str | Path,
    out_dir: str | Path,
    seed: int | None = None,
    window_us: int = 10_000,
    dt_us: int = 1_000,
    inject: str | None = None,
) -> Path:
    """Run the full pipeline. Returns the output directory path."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data_dir = out_dir / "data"
    data_dir.mkdir(exist_ok=True)

    scene = load_scene(scene_path)
    cameras = load_cameras(cameras_path)
    if seed is not None:
        scene.seed = seed

    cam_map = {c.id: c for c in cameras}

    # 1. Generate events
    streams = generate(scene, cameras, dt_us=dt_us, inject=inject)

    # 2. Accumulate → event-frame-2d assets (per camera)
    frames_by_cam: dict[str, list[dict]] = {}
    frame_assets: list[dict] = []
    for cam in cameras:
        frames = accumulate(
            streams[cam.id], cam,
            window_us=window_us,
            source_id="config:scene",
        )
        frames_by_cam[cam.id] = frames
        frame_assets.extend(frames)

    # 3. Tracking: centroids + triangulation → tracklets
    tracklets = build_tracklets(frames_by_cam, cam_map)

    # 4. Aggregate → motion-evidence-3d
    motion = build_motion_evidence(tracklets) if tracklets else None

    # 5. Serialise assets (strip internal _frame key, save .npy)
    all_assets: list[dict] = []

    for asset in frame_assets:
        frame_arr: np.ndarray = asset.pop("_frame", None)
        if frame_arr is not None:
            npy_name = f"{asset['id']}.npy"
            np.save(data_dir / npy_name, frame_arr)
            asset["representations"] = [{
                "format": "npy",
                "uri": f"data/{npy_name}",
                "shape": list(frame_arr.shape),
                "dtype": str(frame_arr.dtype),
            }]
        all_assets.append(asset)

    all_assets.extend(tracklets)
    if motion:
        all_assets.append(motion)

    # 5b. VLLM summary — generated from assembled assets before serialisation
    summary = summarise(all_assets, source_id="config:scene")
    all_assets.append(summary)

    # 6. Write individual asset JSON files
    for asset in all_assets:
        fname = _safe_fname(asset["id"]) + ".json"
        _write_json(out_dir / fname, asset)

    # 7. Bundle manifest
    manifest = {
        "version": "3.0",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scene": str(scene_path),
        "cameras": str(cameras_path),
        "inject": inject,
        "source_ids": ["config:cameras", "config:scene"],
        "assets": [{"id": a["id"], "kind": a["kind"],
                    "file": _safe_fname(a["id"]) + ".json"}
                   for a in all_assets],
    }
    _write_json(out_dir / "bundle_manifest.json", manifest)

    # 8. Schema validation
    errors = validate_bundle(all_assets)
    manifest["schema_valid"] = len(errors) == 0
    manifest["schema_errors"] = errors
    _write_json(out_dir / "bundle_manifest.json", manifest)

    return out_dir


def _safe_fname(asset_id: str) -> str:
    """Convert an asset ID to a safe filesystem name (replaces : with _)."""
    return asset_id.replace(":", "_")


def _write_json(path: Path, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
