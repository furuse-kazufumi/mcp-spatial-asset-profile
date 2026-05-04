"""
main.py — CLI for MCP Spatial Asset Profile v2 SDK.

Commands:
    validate   <path>          Validate a JSON asset file
    generate   --output <dir>  Generate sample assets
    workflow   --source <path> Run mock segmentation pipeline
    migrate    <in> <out>      Migrate v1 asset to v2
    info       <path>          Print asset summary
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path


def cmd_validate(args: argparse.Namespace) -> int:
    from ..validators import validate_asset_file
    errors = validate_asset_file(args.path)
    if errors:
        print(f"[FAIL] {args.path}")
        for e in errors:
            print(f"  - {e}")
        return 1
    else:
        print(f"[OK]   {args.path} — valid v2 asset")
        return 0


def cmd_generate(args: argparse.Namespace) -> int:
    from ..samples import generate_sample_assets
    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)
    assets = generate_sample_assets()
    for kind, asset in assets.items():
        out_path = outdir / f"{kind}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(asset, f, indent=2, ensure_ascii=False)
        print(f"  Generated: {out_path}")
    print(f"[OK] Generated {len(assets)} sample assets in {outdir}")
    return 0


def cmd_workflow(args: argparse.Namespace) -> int:
    from ..workflow import WorkflowMockRunner
    from ..validators import validate_pipeline

    # Load source asset
    try:
        with open(args.source, encoding="utf-8") as f:
            source = json.load(f)
    except Exception as e:
        print(f"[ERROR] Could not load source: {e}")
        return 1

    source_id = source.get("asset_id", "urn:uuid:unknown")
    runner = WorkflowMockRunner()
    pipeline_assets = runner.run_full_pipeline(source_id)

    all_assets = [source] + pipeline_assets
    errors = validate_pipeline(all_assets)

    print(f"[OK] Pipeline: {len(pipeline_assets)} steps")
    for a in pipeline_assets:
        print(f"  {a['kind']:30s} {a['asset_id']}")

    if errors:
        print(f"\n[WARN] Traceability issues:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("\n[OK] Traceability: all references valid")

    # Optionally write output
    if args.output:
        outdir = Path(args.output)
        outdir.mkdir(parents=True, exist_ok=True)
        for a in pipeline_assets:
            fname = outdir / f"{a['kind'].replace('-','_')}.json"
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(a, f, indent=2, ensure_ascii=False)
            print(f"  Wrote: {fname}")

    return 0


def cmd_migrate(args: argparse.Namespace) -> int:
    from ..codec import migrate_v1_to_v2
    try:
        with open(args.input, encoding="utf-8") as f:
            v1 = json.load(f)
    except Exception as e:
        print(f"[ERROR] Could not load input: {e}")
        return 1

    v2 = migrate_v1_to_v2(v1)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(v2, f, indent=2, ensure_ascii=False)
    print(f"[OK] Migrated {args.input} → {args.output}")
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    from ..codec import decode_asset
    try:
        with open(args.path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1
    asset = decode_asset(data)
    print(f"asset_id     : {asset.asset_id}")
    print(f"kind         : {asset.kind}")
    print(f"version      : {asset.version}")
    print(f"name         : {asset.name}")
    print(f"representations: {len(asset.representations)}")
    for r in asset.representations:
        print(f"  [{r.format:12s}] {r.uri}  points={r.point_count}  faces={r.face_count}")
    if asset.spatial:
        s = asset.spatial
        print(f"spatial      : unit={s.unit} up={s.up_axis} hand={s.handedness}")
    if asset.workflow:
        print(f"workflow.step: {asset.workflow.step}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="spatial-asset-v2",
        description="MCP Spatial Asset Profile v2 CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # validate
    p_val = sub.add_parser("validate", help="Validate a JSON asset file")
    p_val.add_argument("path", help="Path to asset JSON file")

    # generate
    p_gen = sub.add_parser("generate", help="Generate sample assets")
    p_gen.add_argument("--output", default="./generated_samples", help="Output directory")

    # workflow
    p_wf = sub.add_parser("workflow", help="Run mock segmentation pipeline")
    p_wf.add_argument("--source", required=True, help="Source asset JSON file")
    p_wf.add_argument("--output", default=None, help="Optional output directory for pipeline assets")

    # migrate
    p_mig = sub.add_parser("migrate", help="Migrate v1 asset to v2")
    p_mig.add_argument("input", help="Input v1 asset JSON file")
    p_mig.add_argument("output", help="Output v2 asset JSON file")

    # info
    p_info = sub.add_parser("info", help="Print asset summary")
    p_info.add_argument("path", help="Path to asset JSON file")

    args = parser.parse_args()
    commands = {
        "validate": cmd_validate,
        "generate": cmd_generate,
        "workflow": cmd_workflow,
        "migrate": cmd_migrate,
        "info": cmd_info,
    }
    sys.exit(commands[args.command](args))


if __name__ == "__main__":
    main()
