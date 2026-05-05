"""Assertion harness: compare bundle output against ground-truth.json."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def main() -> None:
    p = argparse.ArgumentParser(description="Validate synthetic demo bundle against ground truth")
    p.add_argument("--bundle", required=True, help="Bundle output directory (contains bundle_manifest.json)")
    p.add_argument("--ground-truth", required=True, dest="gt", help="Path to ground-truth.json")
    args = p.parse_args()

    bundle_dir = Path(args.bundle)
    manifest = json.loads((bundle_dir / "bundle_manifest.json").read_bytes().decode("utf-8"))
    gt = json.loads(Path(args.gt).read_bytes().decode("utf-8"))

    failures: list[str] = []
    passes:   list[str] = []

    # AC-1: schema valid
    if manifest.get("schema_valid"):
        passes.append("AC-1 schema_valid=True")
    else:
        failures.append(f"AC-1 schema_valid=False: {manifest.get('schema_errors')}")

    # Load all assets
    assets_by_id = {}
    for entry in manifest["assets"]:
        path = bundle_dir / entry["file"]
        if path.exists():
            assets_by_id[entry["id"]] = json.loads(path.read_bytes().decode("utf-8"))

    # AC-3: derived_from DAG is closed
    known_ids = set(assets_by_id.keys()) | set(manifest.get("source_ids", []))
    dag_errors = []
    for asset in assets_by_id.values():
        for ref in asset.get("derived_from", []):
            if ref["id"] not in known_ids:
                dag_errors.append(f"{asset['id']} -> {ref['id']} (unknown)")
    if not dag_errors:
        passes.append("AC-3 derived_from DAG closed")
    else:
        failures.append(f"AC-3 DAG not closed: {dag_errors}")

    # Find tracklets
    tracklets = [a for a in assets_by_id.values() if a.get("kind") == "event-tracklet-3d"]
    expected_assets = gt.get("expected_assets", {})
    expected_count = expected_assets.get("tracklet_count", 1)

    if len(tracklets) >= expected_count:
        passes.append(f"AC tracklet_count={len(tracklets)} >= {expected_count}")
    else:
        failures.append(f"AC tracklet_count={len(tracklets)} < expected {expected_count}")

    # AC-2: triangulation position error vs ground truth
    gt_trajs = {t["id"]: t for t in gt.get("trajectories", [])}
    for expect in expected_assets.get("tracklets", []):
        traj_id = expect["trajectory_id"]
        gt_traj = gt_trajs.get(traj_id)
        if gt_traj is None:
            continue
        gt_samples = {s["t_us"]: np.array(s["position"]) for s in gt_traj["sample_points"]}

        # Find the tracklet (use first if only one expected)
        tracklet = tracklets[0] if tracklets else None
        if tracklet is None:
            failures.append(f"AC-2 no tracklet for {traj_id}")
            continue

        min_pts = expect.get("min_point_count", 1)
        pts = tracklet.get("points", [])
        if len(pts) >= min_pts:
            passes.append(f"AC point_count={len(pts)} >= {min_pts}")
        else:
            failures.append(f"AC point_count={len(pts)} < {min_pts}")

        # Position error against nearest GT sample
        max_err_m = expect.get("max_position_error_m", 0.01)
        max_reproj = expect.get("max_reprojection_error_px", 1.0)
        errors = []
        reproj_errors = []
        gt_t_list = sorted(gt_samples.keys())
        for pt in pts:
            t_pt = pt["t_us"]
            # interpolate GT position at t_pt
            P_gt = _interp_gt(t_pt, gt_t_list, gt_samples)
            if P_gt is not None:
                errors.append(float(np.linalg.norm(np.array(pt["position"]) - P_gt)))
            re = pt.get("reprojection_error_px")
            if re is not None:
                reproj_errors.append(re)

        if errors:
            rms = float(np.sqrt(np.mean(np.square(errors))))
            if rms <= max_err_m:
                passes.append(f"AC-2 position RMS={rms:.4f}m <= {max_err_m}m")
            else:
                failures.append(f"AC-2 position RMS={rms:.4f}m > {max_err_m}m")

        if reproj_errors:
            mean_re = float(np.mean(reproj_errors))
            if mean_re <= max_reproj:
                passes.append(f"AC reprojection={mean_re:.3f}px <= {max_reproj}px")
            else:
                failures.append(f"AC reprojection={mean_re:.3f}px > {max_reproj}px")

    # Print report
    print(f"\n=== Validation Report ({len(passes)} pass, {len(failures)} fail) ===")
    for msg in passes:
        print(f"  [PASS] {msg}")
    for msg in failures:
        print(f"  [FAIL] {msg}")

    if failures:
        sys.exit(1)
    else:
        print("\nAll acceptance criteria met.")


def _interp_gt(t_us: int, gt_t_list: list, gt_samples: dict) -> np.ndarray | None:
    if not gt_t_list:
        return None
    if t_us <= gt_t_list[0]:
        return gt_samples[gt_t_list[0]]
    if t_us >= gt_t_list[-1]:
        return gt_samples[gt_t_list[-1]]
    for i in range(len(gt_t_list) - 1):
        t0, t1 = gt_t_list[i], gt_t_list[i + 1]
        if t0 <= t_us <= t1:
            alpha = (t_us - t0) / (t1 - t0)
            return gt_samples[t0] + alpha * (gt_samples[t1] - gt_samples[t0])
    return None


if __name__ == "__main__":
    main()
