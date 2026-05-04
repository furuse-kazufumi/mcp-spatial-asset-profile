"""
schema_validator.py — JSON Schema Draft 2020-12 validation.

Design philosophy:
- Gracefully degrades if jsonschema is not installed
- Schema path is relative to the repository root spec/schema/ directory
- validate_asset: accepts a dict, returns list of error messages
- validate_asset_file: accepts a file path, loads JSON, delegates to validate_asset
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Union

# Locate spec/schema/ relative to this file
_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parents[3]  # sdk/python/spatial_asset_v2/validators → repo root
_SCHEMA_DIR = _REPO_ROOT / "spec" / "schema"

# Kind → overlay schema filename
_KIND_SCHEMA_MAP = {
    "rendered-view": "rendered-view.schema.json",
    "segmentation-mask-2d": "segmentation-mask-2d.schema.json",
    "segmentation-mask-3d": "segmentation-mask-3d.schema.json",
    "object-asset": "object-asset.schema.json",
}


def _load_schema(filename: str) -> dict:
    path = _SCHEMA_DIR / filename
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_asset(asset_dict: dict) -> list[str]:
    """
    Validate asset_dict against the appropriate JSON Schema.

    Returns a list of error message strings. Empty list = valid.

    Falls back to basic structural checks if jsonschema is not installed.
    """
    # Basic structural checks (no jsonschema dependency)
    errors: list[str] = []

    if not isinstance(asset_dict, dict):
        return ["asset must be a JSON object (dict)"]

    for required in ("version", "asset_id", "kind", "representations"):
        if required not in asset_dict:
            errors.append(f"missing required field: '{required}'")

    if asset_dict.get("version") != "2.0":
        errors.append(f"version must be '2.0', got: {asset_dict.get('version')!r}")

    if not asset_dict.get("asset_id"):
        errors.append("asset_id must be non-empty")

    reps = asset_dict.get("representations", [])
    if not isinstance(reps, list) or len(reps) == 0:
        errors.append("representations must be a non-empty array")
    else:
        for i, rep in enumerate(reps):
            if "format" not in rep:
                errors.append(f"representations[{i}]: missing 'format'")
            if "uri" not in rep:
                errors.append(f"representations[{i}]: missing 'uri'")
            depth_scale = rep.get("depth_scale")
            if depth_scale is not None and depth_scale <= 0:
                errors.append(f"representations[{i}].depth_scale must be > 0")

    # Segmentation-kind specific checks
    kind = asset_dict.get("kind", "")
    workflow = asset_dict.get("workflow", {})

    if kind == "rendered-view":
        if not workflow.get("target_asset_id"):
            errors.append("rendered-view: workflow.target_asset_id is required")
        if not workflow.get("viewpoint_id"):
            errors.append("rendered-view: workflow.viewpoint_id is required")

    elif kind == "segmentation-mask-2d":
        if not workflow.get("target_asset_id"):
            errors.append("segmentation-mask-2d: workflow.target_asset_id is required")
        if not workflow.get("viewpoint_id"):
            errors.append("segmentation-mask-2d: workflow.viewpoint_id is required")

    elif kind == "segmentation-mask-3d":
        if not workflow.get("target_asset_id"):
            errors.append("segmentation-mask-3d: workflow.target_asset_id is required")

    elif kind == "object-asset":
        if not workflow.get("target_asset_id"):
            errors.append("object-asset: workflow.target_asset_id is required")
        if not workflow.get("instance_id"):
            errors.append("object-asset: workflow.instance_id is required")

    # Confidence range check
    conf = workflow.get("confidence")
    if conf is not None and not (0.0 <= conf <= 1.0):
        errors.append(f"workflow.confidence must be in [0, 1], got {conf}")

    # Try jsonschema if available
    try:
        import jsonschema  # noqa: F401
        _jsonschema_validate(asset_dict, errors)
    except ImportError:
        pass

    return errors


def _jsonschema_validate(asset_dict: dict, errors: list[str]) -> None:
    """Append jsonschema validation errors to `errors` list."""
    try:
        import jsonschema
        from jsonschema import Draft202012Validator

        schema = _load_schema("asset.schema.json")
        validator = Draft202012Validator(schema)
        for error in validator.iter_errors(asset_dict):
            errors.append(f"[schema] {error.json_path}: {error.message}")
    except FileNotFoundError as e:
        errors.append(f"[schema] could not load schema: {e}")
    except Exception as e:
        errors.append(f"[schema] validation error: {e}")


def validate_asset_file(path: Union[str, Path]) -> list[str]:
    """Load a JSON file and validate it. Returns list of error strings."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"JSON parse error: {e}"]
    except OSError as e:
        return [f"File error: {e}"]
    return validate_asset(data)
