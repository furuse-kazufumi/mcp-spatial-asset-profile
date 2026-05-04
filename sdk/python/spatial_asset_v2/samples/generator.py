"""
generator.py — Sample spatial asset generators.

All functions return JSON-serializable dicts conforming to asset.schema.json v2.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone


def _new_id() -> str:
    return f"urn:uuid:{uuid.uuid4()}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_pointcloud_asset(
    name: str = "Sample Point Cloud",
    uri: str = "sample.ply",
    point_count: int = 1000,
    bounds_half: float = 1.0,
) -> dict:
    """Generate a minimal valid point-cloud asset dict."""
    h = bounds_half
    return {
        "version": "2.0",
        "asset_id": _new_id(),
        "kind": "point-cloud",
        "name": name,
        "created_at": _now(),
        "representations": [
            {
                "rep_id": "rep-ply-full",
                "format": "ply",
                "uri": uri,
                "mime_type": "application/x-ply",
                "lod": 0,
                "point_count": point_count,
                "channels": ["x", "y", "z"],
            }
        ],
        "spatial": {
            "up_axis": "+Y",
            "handedness": "right",
            "unit": "m",
            "bounds": {
                "min": [-h, -h, -h],
                "max": [h, h, h],
            }
        },
        "render_hints": {
            "point_size": 2.0,
            "color_mode": "rgb",
        },
        "metadata": {"generator": "spatial-asset-v2-sdk"}
    }


def generate_mesh_asset(
    name: str = "Sample Mesh",
    uri: str = "sample.obj",
    face_count: int = 320,
) -> dict:
    """Generate a minimal valid mesh asset dict."""
    return {
        "version": "2.0",
        "asset_id": _new_id(),
        "kind": "mesh",
        "name": name,
        "created_at": _now(),
        "representations": [
            {
                "rep_id": "rep-obj-default",
                "format": "obj",
                "uri": uri,
                "mime_type": "model/obj",
                "lod": 0,
                "face_count": face_count,
                "channels": ["position", "normal"],
            }
        ],
        "spatial": {
            "up_axis": "+Y",
            "handedness": "right",
            "unit": "m",
            "bounds": {"min": [-1.0, -1.0, -1.0], "max": [1.0, 1.0, 1.0]},
        },
        "metadata": {"generator": "spatial-asset-v2-sdk"}
    }


def generate_gaussian_splat_asset(
    name: str = "Sample Gaussian Splat",
    uri: str = "scene.splat",
    gaussian_count: int = 1000,
) -> dict:
    """Generate a minimal valid gaussian-splat asset dict."""
    return {
        "version": "2.0",
        "asset_id": _new_id(),
        "kind": "gaussian-splat",
        "name": name,
        "created_at": _now(),
        "representations": [
            {
                "rep_id": "rep-splat-full",
                "format": "splat",
                "uri": uri,
                "mime_type": "application/x-gaussian-splat",
                "lod": 0,
                "point_count": gaussian_count,
                "channels": [
                    "x", "y", "z", "opacity",
                    "scale_0", "scale_1", "scale_2",
                    "rot_0", "rot_1", "rot_2", "rot_3",
                    "f_dc_0", "f_dc_1", "f_dc_2",
                ],
                "capabilities_required": ["splat-render"],
            }
        ],
        "spatial": {
            "up_axis": "+Y",
            "handedness": "right",
            "unit": "m",
            "bounds": {"min": [-2.0, -1.5, -2.0], "max": [2.0, 1.5, 2.0]},
        },
        "metadata": {"generator": "spatial-asset-v2-sdk"}
    }


def generate_depth_image_asset(
    name: str = "Sample Depth Image",
    uri: str = "depth.png",
    width: int = 640,
    height: int = 480,
) -> dict:
    """Generate a minimal valid depth-image asset dict."""
    return {
        "version": "2.0",
        "asset_id": _new_id(),
        "kind": "depth-image",
        "name": name,
        "created_at": _now(),
        "representations": [
            {
                "rep_id": "rep-png-depth",
                "format": "png-depth",
                "uri": uri,
                "mime_type": "image/png",
                "depth_scale": 0.001,
                "depth_unit": "mm",
                "image_width": width,
                "image_height": height,
            }
        ],
        "metadata": {"generator": "spatial-asset-v2-sdk"}
    }


def generate_sample_assets() -> dict[str, dict]:
    """
    Generate one sample asset for each core kind.

    Returns: {kind: asset_dict}
    """
    return {
        "point-cloud":   generate_pointcloud_asset(),
        "mesh":          generate_mesh_asset(),
        "gaussian-splat": generate_gaussian_splat_asset(),
        "depth-image":   generate_depth_image_asset(),
    }
