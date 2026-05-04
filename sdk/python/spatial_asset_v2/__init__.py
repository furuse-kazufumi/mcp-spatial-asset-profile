"""
spatial_asset_v2 — MCP Spatial Asset Profile v2 Python SDK

Design philosophy:
- Pure Python dataclasses; no required heavy 3D/ML dependencies
- Codec (encode/decode) separates data from I/O
- Validators are optional (jsonschema) but integrated
- Traceability is a first-class concern
"""

from .models import SpatialAsset, Representation, Spatial, Viewpoint, RenderHints, Workflow
from .codec import encode_asset, decode_asset

__version__ = "2.0.0"
__all__ = [
    "SpatialAsset",
    "Representation",
    "Spatial",
    "Viewpoint",
    "RenderHints",
    "Workflow",
    "encode_asset",
    "decode_asset",
]
