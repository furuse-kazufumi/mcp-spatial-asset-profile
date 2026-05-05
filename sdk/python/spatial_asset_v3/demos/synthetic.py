"""CLI entry point: python -m spatial_asset_v3.demos.synthetic"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from ..pipeline import run


def main() -> None:
    p = argparse.ArgumentParser(description="Synthetic multi-event-camera debug demo (v3 Layer 1)")
    p.add_argument("--config",   required=True, help="Path to scene.json")
    p.add_argument("--cameras",  required=True, help="Path to cameras.json")
    p.add_argument("--out",      required=True, help="Output directory")
    p.add_argument("--seed",     type=int, default=None, help="RNG seed override")
    p.add_argument("--window-us", type=int, default=10_000, dest="window_us",
                   help="Event accumulation window width in microseconds (default: 10000)")
    p.add_argument("--dt-us",   type=int, default=1_000, dest="dt_us",
                   help="Event generation sample step in microseconds (default: 1000)")
    p.add_argument("--inject",  choices=["calibration_error", "time_skew", "hot_pixel", "drop_polarity"],
                   default=None, help="Failure injection mode")
    args = p.parse_args()

    t0 = time.perf_counter()
    out_dir = run(
        scene_path=args.config,
        cameras_path=args.cameras,
        out_dir=args.out,
        seed=args.seed,
        window_us=args.window_us,
        dt_us=args.dt_us,
        inject=args.inject,
    )
    elapsed = time.perf_counter() - t0

    import json
    manifest = json.loads((out_dir / "bundle_manifest.json").read_bytes().decode("utf-8"))
    n_assets = len(manifest["assets"])
    valid = manifest.get("schema_valid", False)
    n_err = len(manifest.get("schema_errors", []))

    print(f"[synthetic] done in {elapsed:.2f}s | assets={n_assets} | schema_valid={valid} | errors={n_err}")
    if manifest.get("schema_errors"):
        for e in manifest["schema_errors"]:
            print(f"  SCHEMA ERR: {e}", file=sys.stderr)
    print(f"[synthetic] output: {out_dir}")


if __name__ == "__main__":
    main()
