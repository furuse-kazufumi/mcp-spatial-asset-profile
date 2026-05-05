"""CLI demo: generate a vllm-summary asset from an existing bundle directory."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(
        description="Generate a vllm-summary asset from a v3 bundle (Layer 3 demo)"
    )
    p.add_argument("bundle_dir", help="Directory produced by the synthetic pipeline")
    p.add_argument("--language", default="en", help="BCP-47 language tag (default: en)")
    p.add_argument("--out", default=None,
                   help="Output JSON path (default: <bundle_dir>/vllm-summary.json)")
    args = p.parse_args()

    bundle_dir = Path(args.bundle_dir)
    manifest_path = bundle_dir / "bundle_manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: bundle_manifest.json not found in {bundle_dir}", file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(manifest_path.read_bytes().decode("utf-8"))

    # Load all assets referenced in the manifest
    assets: list[dict] = []
    for entry in manifest.get("assets", []):
        fpath = bundle_dir / entry["file"]
        if fpath.exists():
            assets.append(json.loads(fpath.read_bytes().decode("utf-8")))

    from ..vllm import summarise
    summary = summarise(assets, language=args.language, source_id="bundle_manifest")

    out_path = Path(args.out) if args.out else bundle_dir / "vllm-summary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"[vllm-summary] text: {summary['text'][:80]}...")
    print(f"[vllm-summary] model: {summary['provenance']['model']}")
    print(f"[vllm-summary] written to: {out_path}")


if __name__ == "__main__":
    main()
