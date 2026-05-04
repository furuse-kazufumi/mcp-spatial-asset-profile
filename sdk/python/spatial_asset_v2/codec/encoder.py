"""
encoder.py — SpatialAsset → dict serialization.

Design philosophy:
- Omit None values to keep output minimal
- Preserve all explicitly set fields (no lossy encoding)
- Output is always JSON-serializable (no numpy arrays, no custom types)
"""

from __future__ import annotations
from typing import Any
from ..models import (
    SpatialAsset, Representation, Spatial, BoundingBox,
    Viewpoint, RenderHints, Workflow, WorkflowLabel
)


def _omit_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


def encode_bounding_box(bb: BoundingBox) -> dict:
    return {"min": list(bb.min), "max": list(bb.max)}


def encode_spatial(s: Spatial) -> dict:
    d: dict[str, Any] = {}
    if s.frame is not None:
        d["frame"] = s.frame
    if s.up_axis != "+Y":
        d["up_axis"] = s.up_axis
    if s.handedness != "right":
        d["handedness"] = s.handedness
    if s.unit != "m":
        d["unit"] = s.unit
    # Always include unit for clarity
    d["unit"] = s.unit
    if s.bounds is not None:
        d["bounds"] = encode_bounding_box(s.bounds)
    return d


def encode_viewpoint(vp: Viewpoint) -> dict:
    d: dict[str, Any] = {"viewpoint_id": vp.viewpoint_id}
    for attr in ("label", "position", "target", "up", "fov_y_deg", "near", "far",
                 "image_width", "image_height", "intrinsics", "extrinsics"):
        v = getattr(vp, attr)
        if v is not None:
            d[attr] = v
    return d


def encode_render_hints(rh: RenderHints) -> dict:
    return _omit_none({
        "point_size": rh.point_size,
        "opacity": rh.opacity,
        "color_mode": rh.color_mode,
        "lod_policy": rh.lod_policy,
        "background_color": rh.background_color,
        "show_bounding_box": rh.show_bounding_box,
        "preferred_representation": rh.preferred_representation,
    })


def encode_workflow_label(wl: WorkflowLabel) -> dict:
    d: dict[str, Any] = {"id": wl.id, "name": wl.name}
    if wl.color is not None:
        d["color"] = wl.color
    return d


def encode_workflow(w: Workflow) -> dict:
    d: dict[str, Any] = {}
    for attr in ("step", "target_asset_id", "viewpoint_id", "instance_id",
                 "label", "confidence", "tool", "tool_version", "parameters",
                 "source_masks", "correspondence", "started_at", "completed_at"):
        v = getattr(w, attr)
        if v is not None:
            d[attr] = v
    if w.labels is not None:
        d["labels"] = [encode_workflow_label(lbl) for lbl in w.labels]
    return d


def encode_representation(rep: Representation) -> dict:
    d: dict[str, Any] = {"format": rep.format, "uri": rep.uri}
    for attr in ("rep_id", "mime_type", "size_bytes", "sha256", "lod",
                 "point_count", "face_count", "channels", "capabilities_required",
                 "encoding", "depth_scale", "depth_unit", "image_width",
                 "image_height", "viewpoint_id", "instance_id"):
        v = getattr(rep, attr)
        if v is not None:
            d[attr] = v
    return d


def encode_asset(asset: SpatialAsset) -> dict:
    """Encode a SpatialAsset to a JSON-serializable dict."""
    d: dict[str, Any] = {
        "version": asset.version,
        "asset_id": asset.asset_id,
        "kind": asset.kind,
        "representations": [encode_representation(r) for r in asset.representations],
    }
    if asset.name is not None:
        d["name"] = asset.name
    if asset.created_at is not None:
        d["created_at"] = asset.created_at
    if asset.spatial is not None:
        d["spatial"] = encode_spatial(asset.spatial)
    if asset.viewpoints is not None:
        d["viewpoints"] = [encode_viewpoint(vp) for vp in asset.viewpoints]
    if asset.render_hints is not None:
        d["render_hints"] = encode_render_hints(asset.render_hints)
    if asset.workflow is not None:
        d["workflow"] = encode_workflow(asset.workflow)
    if asset.derived_from is not None:
        d["derived_from"] = list(asset.derived_from)
    if asset.metadata is not None:
        d["metadata"] = asset.metadata
    return d
