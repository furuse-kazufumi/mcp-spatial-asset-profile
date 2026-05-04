"""
samples — Sample asset generator for MCP Spatial Asset Profile v2.

Design philosophy:
- Generate minimal but valid v2 assets for all 8 kinds
- No file I/O; returns dicts only (callers decide where to write)
- numpy used only if available (for point cloud data generation)
"""

from .generator import generate_sample_assets, generate_pointcloud_asset, generate_mesh_asset
from .generator import generate_gaussian_splat_asset, generate_depth_image_asset

__all__ = [
    "generate_sample_assets",
    "generate_pointcloud_asset",
    "generate_mesh_asset",
    "generate_gaussian_splat_asset",
    "generate_depth_image_asset",
]
