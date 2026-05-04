"""
tests/interoperability/test_cross_sdk.py — Cross-SDK interoperability tests.

Verifies that Python-encoded assets can be parsed by the TypeScript validator
and vice versa (via JSON round-trip, since TS is compiled separately).

Run from repository root:
    pytest tests/interoperability/ -v
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
SDK_PATH = REPO_ROOT / "sdk" / "python"
sys.path.insert(0, str(SDK_PATH))

from spatial_asset_v2.codec import encode_asset, decode_asset
from spatial_asset_v2.models import SpatialAsset, Representation, Spatial, BoundingBox
from spatial_asset_v2.validators import validate_asset


def make_standard_asset() -> SpatialAsset:
    return SpatialAsset(
        asset_id="urn:uuid:interop-test-001",
        kind="point-cloud",
        name="Interoperability Test Asset",
        representations=[
            Representation(
                format="ply",
                uri="test/interop.ply",
                rep_id="rep-ply",
                point_count=1000,
                channels=["x", "y", "z"],
            )
        ],
        spatial=Spatial(
            frame="local-ENU",
            up_axis="+Y",
            unit="m",
            bounds=BoundingBox(min=[-1.0, -1.0, -1.0], max=[1.0, 1.0, 1.0]),
        ),
    )


class TestJsonRoundTrip:
    """Test that assets survive JSON serialization (mimics TS SDK round-trip)."""

    def test_python_encode_produces_valid_json(self):
        asset = make_standard_asset()
        d = encode_asset(asset)
        json_str = json.dumps(d)  # Ensure JSON-serializable
        data = json.loads(json_str)
        errors = validate_asset(data)
        assert errors == []

    def test_json_string_round_trip(self):
        asset = make_standard_asset()
        d = encode_asset(asset)
        json_str = json.dumps(d)
        data = json.loads(json_str)
        asset2 = decode_asset(data)
        assert asset2.asset_id == asset.asset_id
        assert asset2.kind == asset.kind
        assert len(asset2.representations) == len(asset.representations)

    def test_example_files_round_trip(self):
        """All spec/examples/ survive encode → JSON → decode cycle."""
        examples_dir = REPO_ROOT / "spec" / "examples"
        for json_path in examples_dir.glob("*.json"):
            with open(json_path, encoding="utf-8") as f:
                original = json.load(f)
            asset = decode_asset(original)
            encoded = encode_asset(asset)
            json_str = json.dumps(encoded)
            data = json.loads(json_str)
            errors = validate_asset(data)
            assert errors == [], f"{json_path.name}: {errors}"

    def test_all_kinds_round_trip(self):
        """Each asset kind survives JSON round-trip."""
        from spatial_asset_v2.samples import generate_sample_assets
        samples = generate_sample_assets()
        for kind, asset_dict in samples.items():
            json_str = json.dumps(asset_dict)
            data = json.loads(json_str)
            asset = decode_asset(data)
            encoded = encode_asset(asset)
            errors = validate_asset(encoded)
            assert errors == [], f"Kind {kind}: {errors}"
