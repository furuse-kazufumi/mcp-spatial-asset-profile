"""
models — Dataclass models for MCP Spatial Asset Profile v2.

Design philosophy:
- Standard library dataclasses only (no pydantic required)
- All fields optional except asset_id, kind, representations
- Mirrors the JSON schema structure exactly for easy round-trip
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional

VERSION = "2.0"

VALID_KINDS = frozenset({
    "point-cloud", "mesh", "gaussian-splat", "depth-image",
    "rendered-view", "segmentation-mask-2d", "segmentation-mask-3d", "object-asset"
})

VALID_FORMATS = frozenset({
    "ply", "pcd", "las", "laz", "obj", "gltf", "glb", "splat",
    "png-depth", "png-mask", "png", "jpeg", "npy", "npz", "json-pc"
})


@dataclass
class BoundingBox:
    min: list[float]  # [x, y, z]
    max: list[float]  # [x, y, z]


@dataclass
class Spatial:
    frame: Optional[str] = None
    up_axis: str = "+Y"
    handedness: str = "right"
    unit: str = "m"
    bounds: Optional[BoundingBox] = None


@dataclass
class Viewpoint:
    viewpoint_id: str = ""
    label: Optional[str] = None
    position: Optional[list[float]] = None
    target: Optional[list[float]] = None
    up: Optional[list[float]] = None
    fov_y_deg: Optional[float] = None
    near: Optional[float] = None
    far: Optional[float] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    intrinsics: Optional[dict[str, float]] = None
    extrinsics: Optional[dict[str, Any]] = None


@dataclass
class RenderHints:
    point_size: Optional[float] = None
    opacity: Optional[float] = None
    color_mode: Optional[str] = None
    lod_policy: Optional[str] = None
    background_color: Optional[list[float]] = None
    show_bounding_box: Optional[bool] = None
    preferred_representation: Optional[str] = None


@dataclass
class WorkflowLabel:
    id: int = 0
    name: str = ""
    color: Optional[list[int]] = None


@dataclass
class Workflow:
    step: Optional[str] = None
    target_asset_id: Optional[str] = None
    viewpoint_id: Optional[str] = None
    instance_id: Optional[str] = None
    label: Optional[str] = None
    confidence: Optional[float] = None
    tool: Optional[str] = None
    tool_version: Optional[str] = None
    parameters: Optional[dict[str, Any]] = None
    source_masks: Optional[list[str]] = None
    correspondence: Optional[str] = None
    labels: Optional[list[WorkflowLabel]] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class Representation:
    format: str = ""
    uri: str = ""
    rep_id: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    sha256: Optional[str] = None
    lod: Optional[int] = None
    point_count: Optional[int] = None
    face_count: Optional[int] = None
    channels: Optional[list[str]] = None
    capabilities_required: Optional[list[str]] = None
    encoding: Optional[str] = None
    depth_scale: Optional[float] = None
    depth_unit: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    viewpoint_id: Optional[str] = None
    instance_id: Optional[str] = None


@dataclass
class SpatialAsset:
    """Top-level MCP Spatial Asset Profile v2 envelope."""
    asset_id: str = ""
    kind: str = ""
    representations: list[Representation] = field(default_factory=list)
    version: str = VERSION
    name: Optional[str] = None
    created_at: Optional[str] = None
    spatial: Optional[Spatial] = None
    viewpoints: Optional[list[Viewpoint]] = None
    render_hints: Optional[RenderHints] = None
    workflow: Optional[Workflow] = None
    derived_from: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None

    def validate_basic(self) -> list[str]:
        """Return list of validation errors (without JSON schema)."""
        errors: list[str] = []
        if not self.asset_id:
            errors.append("asset_id must be non-empty")
        if self.kind not in VALID_KINDS:
            errors.append(f"kind '{self.kind}' not in {sorted(VALID_KINDS)}")
        if not self.representations:
            errors.append("representations must be non-empty")
        for i, rep in enumerate(self.representations):
            if rep.format not in VALID_FORMATS:
                errors.append(f"representations[{i}].format '{rep.format}' not recognized")
            if not rep.uri:
                errors.append(f"representations[{i}].uri must be non-empty")
        return errors
