"""
tests/schema/test_examples.py — Validate all spec/examples/*.json against schemas.

Run from the repository root:
    pytest tests/schema/test_examples.py -v
"""

import json
import sys
from pathlib import Path

import pytest

# Add SDK to path
REPO_ROOT = Path(__file__).parents[2]
SDK_PATH = REPO_ROOT / "sdk" / "python"
sys.path.insert(0, str(SDK_PATH))

from spatial_asset_v2.validators import validate_asset

EXAMPLES_DIR = REPO_ROOT / "spec" / "examples"
EXAMPLE_FILES = list(EXAMPLES_DIR.glob("*.json"))


@pytest.mark.parametrize("json_path", EXAMPLE_FILES, ids=[p.name for p in EXAMPLE_FILES])
def test_example_validates(json_path: Path):
    """Every example file must validate as a v2 asset."""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    errors = validate_asset(data)
    assert errors == [], f"{json_path.name}: {errors}"


def test_all_examples_present():
    """Ensure the expected example files exist."""
    expected = [
        "pointcloud-asset.json",
        "mesh-asset.json",
        "gaussian-splat-asset.json",
        "rendered-view.json",
        "segmentation-mask-2d.json",
        "segmentation-mask-3d.json",
        "object-asset.json",
    ]
    existing = {p.name for p in EXAMPLE_FILES}
    for name in expected:
        assert name in existing, f"Missing example file: {name}"
