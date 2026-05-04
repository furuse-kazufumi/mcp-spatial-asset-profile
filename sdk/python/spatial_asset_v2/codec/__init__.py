"""
codec — Encoder / decoder for MCP Spatial Asset Profile v2.

Design philosophy:
- encode_asset: SpatialAsset → dict (JSON-serializable)
- decode_asset: dict → SpatialAsset
- No I/O in this module; all operations are pure dict transformations
"""

from .encoder import encode_asset
from .decoder import decode_asset
from .migrate import migrate_v1_to_v2

__all__ = ["encode_asset", "decode_asset", "migrate_v1_to_v2"]
