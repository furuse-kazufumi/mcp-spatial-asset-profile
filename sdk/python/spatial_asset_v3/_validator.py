"""Schema validation for v3 asset envelopes.

Schema path is resolved relative to this file so the package works regardless
of cwd. Caches the parsed schema in a module-level variable.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_SCHEMA_PATH = Path(__file__).resolve().parents[3] / "spec" / "v3" / "spatial-asset-v3.schema.json"
_schema_cache: dict[str, Any] | None = None


def _get_schema() -> dict[str, Any]:
    global _schema_cache
    if _schema_cache is None:
        with open(_SCHEMA_PATH, encoding="utf-8") as f:
            _schema_cache = json.load(f)
    return _schema_cache


class V3ValidationError(Exception):
    """Raised when a v3 asset envelope fails schema validation."""


def validate_v3_asset(asset: dict[str, Any]) -> None:
    """Validate *asset* against spatial-asset-v3.schema.json.

    Raises :exc:`V3ValidationError` on failure; returns None on success.
    """
    try:
        import jsonschema
    except ImportError:
        raise ImportError("pip install jsonschema to use validate_v3_asset()")

    schema = _get_schema()
    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(asset))
    if errors:
        msgs = "; ".join(e.message for e in errors[:5])
        raise V3ValidationError(f"v3 asset validation failed ({asset.get('kind', '?')}): {msgs}")


def validate_bundle(assets: list[dict[str, Any]]) -> list[str]:
    """Validate all assets in a bundle. Returns a list of error strings (empty = all valid)."""
    errors = []
    for asset in assets:
        try:
            validate_v3_asset(asset)
        except V3ValidationError as e:
            errors.append(str(e))
    return errors
