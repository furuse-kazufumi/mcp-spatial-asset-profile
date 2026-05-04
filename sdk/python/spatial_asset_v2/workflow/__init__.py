"""
workflow — Mock workflow runner for MCP Spatial Asset Profile v2.

Design philosophy:
- No actual rendering or segmentation; produces plausible JSON envelopes
- Demonstrates the full pipeline: source → render → segment-2d → lift-3d → extract
- All generated assets have valid structure and traceability
"""

from .mock_runner import WorkflowMockRunner

__all__ = ["WorkflowMockRunner"]
