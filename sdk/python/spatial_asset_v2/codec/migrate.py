"""
migrate.py — v1 → v2 asset migration utility.

Design philosophy:
- Non-destructive: original dict is not modified
- Transparent: field renames are documented
- Tolerant: missing v1 fields are silently handled
"""

from __future__ import annotations
import copy


def migrate_v1_to_v2(v1: dict) -> dict:
    """
    Migrate a v1 (version='1.0') asset dict to v2 (version='2.0').

    Field mapping:
        id          → asset_id
        crs         → spatial.frame
        bounds      → spatial.bounds
        version     → '2.0'
    """
    v2 = copy.deepcopy(v1)
    v2["version"] = "2.0"

    # Rename id → asset_id
    if "id" in v2 and "asset_id" not in v2:
        v2["asset_id"] = v2.pop("id")
    elif "asset_id" not in v2:
        # Mint a placeholder
        import uuid
        v2["asset_id"] = f"urn:uuid:{uuid.uuid4()}"

    # Move crs and bounds into spatial block
    spatial: dict = v2.get("spatial", {})
    if "crs" in v2:
        spatial.setdefault("frame", v2.pop("crs"))
    if "bounds" in v2 and "bounds" not in spatial:
        spatial["bounds"] = v2.pop("bounds")

    if spatial:
        # Ensure defaults
        spatial.setdefault("up_axis", "+Y")
        spatial.setdefault("handedness", "right")
        spatial.setdefault("unit", "m")
        v2["spatial"] = spatial

    return v2
