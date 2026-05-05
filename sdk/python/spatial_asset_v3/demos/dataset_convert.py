"""Layer 2 CLI: convert a public event-camera dataset file to a v3 bundle.

Produces event-frame-2d assets suitable for offline analysis or MCP serving.
For monocular datasets (single camera), stereo triangulation is skipped.

Usage examples:

  # CSV file with default x,y,t,p columns (timestamps in microseconds):
  python -m sdk.python.spatial_asset_v3.demos.dataset_convert \\
      --input events.csv --out out/my_bundle/

  # CSV with millisecond timestamps:
  python -m sdk.python.spatial_asset_v3.demos.dataset_convert \\
      --input events.csv --time-unit ms --out out/my_bundle/

  # NumPy array (.npy shape (N,4)):
  python -m sdk.python.spatial_asset_v3.demos.dataset_convert \\
      --input events.npy --format npy --out out/my_bundle/

  # Whitespace-separated text (x y t_us p per line):
  python -m sdk.python.spatial_asset_v3.demos.dataset_convert \\
      --input events.txt --out out/my_bundle/

  # Custom camera intrinsics:
  python -m sdk.python.spatial_asset_v3.demos.dataset_convert \\
      --input events.csv --resolution 640 480 --intrinsics 320 320 320 240 \\
      --out out/my_bundle/
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

import numpy as np


def _make_camera(args):
    """Build a CameraSpec from CLI arguments (identity extrinsics = world == camera)."""
    from .._config import CameraSpec, Intrinsics
    fx, fy, cx, cy = args.intrinsics
    return CameraSpec(
        id=args.camera_id,
        resolution=tuple(args.resolution),
        intrinsics=Intrinsics(fx=fx, fy=fy, cx=cx, cy=cy),
        T_world_cam=np.eye(4),
    )


def _load_events(args):
    from ..adapters import auto_detect, CsvAdapter, NumpyAdapter, TxtAdapter

    fmt = args.format
    kw = {"time_unit": args.time_unit}

    if fmt == "auto":
        adapter = auto_detect(args.input, **kw)
    elif fmt == "csv":
        adapter = CsvAdapter(
            x_col=args.x_col, y_col=args.y_col,
            t_col=args.t_col, p_col=args.p_col,
            **kw,
        )
    elif fmt in ("npy", "npz"):
        adapter = NumpyAdapter(**kw)
    else:
        adapter = TxtAdapter(**kw)

    return adapter.load(args.input)


def _build_bundle(events, cam, out_dir: Path, window_us: int, source_id: str) -> dict:
    from ..event.accumulator import accumulate
    from .._validator import validate_bundle

    out_dir.mkdir(parents=True, exist_ok=True)
    data_dir = out_dir / "data"
    data_dir.mkdir(exist_ok=True)

    frames = accumulate(events, cam, window_us=window_us, source_id=source_id)

    all_assets = []
    for asset in frames:
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
        fname = f"{asset['id']}.json"
        with open(out_dir / fname, "w", encoding="utf-8") as f:
            json.dump(asset, f, indent=2, ensure_ascii=False)
        all_assets.append(asset)

    errors = validate_bundle(all_assets)
    manifest = {
        "version": "3.0",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "layer": 2,
        "source": source_id,
        "schema_valid": len(errors) == 0,
        "schema_errors": errors,
        "assets": [{"id": a["id"], "kind": a["kind"], "file": f"{a['id']}.json"}
                   for a in all_assets],
    }
    with open(out_dir / "bundle_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return manifest


def main() -> None:
    p = argparse.ArgumentParser(
        description="Convert a dataset event file to a v3 event-frame-2d bundle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--input",  required=True,  help="Input events file (.csv/.npy/.npz/.txt)")
    p.add_argument("--format", default="auto",
                   choices=["auto", "csv", "npy", "npz", "txt"],
                   help="Input format (default: auto-detect from extension)")
    p.add_argument("--out", required=True, help="Output bundle directory")

    # Camera
    p.add_argument("--camera-id", default="cam0", metavar="ID")
    p.add_argument("--resolution", nargs=2, type=int, default=[346, 260],
                   metavar=("W", "H"), help="Sensor resolution in pixels (default: 346 260)")
    p.add_argument("--intrinsics", nargs=4, type=float,
                   default=[200.0, 200.0, 173.0, 130.0],
                   metavar=("FX", "FY", "CX", "CY"),
                   help="Camera intrinsics (default: 200 200 173 130)")

    # Time
    p.add_argument("--time-unit", default="us",
                   choices=["us", "ms", "s", "ns"],
                   help="Timestamp unit in the input file (default: us)")

    # Accumulation
    p.add_argument("--window-us", type=int, default=50_000,
                   help="Event accumulation window width in microseconds (default: 50000)")

    # CSV column names
    csv_g = p.add_argument_group("CSV column names (ignored for npy/txt)")
    csv_g.add_argument("--x-col", default="x")
    csv_g.add_argument("--y-col", default="y")
    csv_g.add_argument("--t-col", default="t")
    csv_g.add_argument("--p-col", default="p")

    args = p.parse_args()

    print(f"Loading events from: {args.input}")
    events = _load_events(args)
    if not events:
        print("ERROR: no events loaded.", file=sys.stderr)
        sys.exit(1)
    print(f"  {len(events)} events loaded  "
          f"(t_us: {events[0].t_us} to {events[-1].t_us})")

    cam = _make_camera(args)
    out_dir = Path(args.out)
    source_id = f"file:{Path(args.input).name}"

    print(f"Accumulating into {args.window_us} us frames ...")
    manifest = _build_bundle(events, cam, out_dir, args.window_us, source_id)

    n = len(manifest["assets"])
    valid = manifest["schema_valid"]
    print(f"Bundle written: {out_dir}  ({n} assets, schema_valid={valid})")
    if manifest["schema_errors"]:
        for err in manifest["schema_errors"]:
            print(f"  SCHEMA ERROR: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
