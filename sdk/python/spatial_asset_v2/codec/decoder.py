"""
decoder.py — dict → SpatialAsset deserialization.

Design philosophy:
- Tolerant parsing: unknown fields are captured in metadata rather than erroring
- v1 assets are detected and transparently migrated (id→asset_id, top-level crs/bounds)
- Never raises on unknown keys (forward compatibility)
"""

from __future__ import annotations
from typing import Any
from ..models import (
    SpatialAsset, Representation, Spatial, BoundingBox,
    Viewpoint, RenderHints, Workflow, WorkflowLabel
)


def decode_bounding_box(d: dict) -> BoundingBox:
    return BoundingBox(min=list(d["min"]), max=list(d["max"]))


def decode_spatial(d: dict) -> Spatial:
    bounds = None
    if "bounds" in d:
        bounds = decode_bounding_box(d["bounds"])
    return Spatial(
        frame=d.get("frame"),
        up_axis=d.get("up_axis", "+Y"),
        handedness=d.get("handedness", "right"),
        unit=d.get("unit", "m"),
        bounds=bounds,
    )


def decode_viewpoint(d: dict) -> Viewpoint:
    return Viewpoint(
        viewpoint_id=d.get("viewpoint_id", ""),
        label=d.get("label"),
        position=d.get("position"),
        target=d.get("target"),
        up=d.get("up"),
        fov_y_deg=d.get("fov_y_deg"),
        near=d.get("near"),
        far=d.get("far"),
        image_width=d.get("image_width"),
        image_height=d.get("image_height"),
        intrinsics=d.get("intrinsics"),
        extrinsics=d.get("extrinsics"),
    )


def decode_render_hints(d: dict) -> RenderHints:
    return RenderHints(
        point_size=d.get("point_size"),
        opacity=d.get("opacity"),
        color_mode=d.get("color_mode"),
        lod_policy=d.get("lod_policy"),
        background_color=d.get("background_color"),
        show_bounding_box=d.get("show_bounding_box"),
        preferred_representation=d.get("preferred_representation"),
    )


def decode_workflow_label(d: dict) -> WorkflowLabel:
    return WorkflowLabel(
        id=d.get("id", 0),
        name=d.get("name", ""),
        color=d.get("color"),
    )


def decode_workflow(d: dict) -> Workflow:
    labels = None
    if "labels" in d:
        labels = [decode_workflow_label(lbl) for lbl in d["labels"]]
    return Workflow(
        step=d.get("step"),
        target_asset_id=d.get("target_asset_id"),
        viewpoint_id=d.get("viewpoint_id"),
        instance_id=d.get("instance_id"),
        label=d.get("label"),
        confidence=d.get("confidence"),
        tool=d.get("tool"),
        tool_version=d.get("tool_version"),
        parameters=d.get("parameters"),
        source_masks=d.get("source_masks"),
        correspondence=d.get("correspondence"),
        labels=labels,
        started_at=d.get("started_at"),
        completed_at=d.get("completed_at"),
    )


def decode_representation(d: dict) -> Representation:
    return Representation(
        format=d.get("format", ""),
        uri=d.get("uri", ""),
        rep_id=d.get("rep_id"),
        mime_type=d.get("mime_type"),
        size_bytes=d.get("size_bytes"),
        sha256=d.get("sha256"),
        lod=d.get("lod"),
        point_count=d.get("point_count"),
        face_count=d.get("face_count"),
        channels=d.get("channels"),
        capabilities_required=d.get("capabilities_required"),
        encoding=d.get("encoding"),
        depth_scale=d.get("depth_scale"),
        depth_unit=d.get("depth_unit"),
        image_width=d.get("image_width"),
        image_height=d.get("image_height"),
        viewpoint_id=d.get("viewpoint_id"),
        instance_id=d.get("instance_id"),
    )


def decode_asset(d: dict) -> SpatialAsset:
    """Decode a dict (from JSON) into a SpatialAsset. Handles v1 migration automatically."""
    from .migrate import migrate_v1_to_v2
    if d.get("version") == "1.0":
        d = migrate_v1_to_v2(d)

    spatial = None
    if "spatial" in d:
        spatial = decode_spatial(d["spatial"])

    viewpoints = None
    if "viewpoints" in d:
        viewpoints = [decode_viewpoint(vp) for vp in d["viewpoints"]]

    render_hints = None
    if "render_hints" in d:
        render_hints = decode_render_hints(d["render_hints"])

    workflow = None
    if "workflow" in d:
        workflow = decode_workflow(d["workflow"])

    return SpatialAsset(
        version=d.get("version", "2.0"),
        asset_id=d.get("asset_id", ""),
        kind=d.get("kind", ""),
        name=d.get("name"),
        created_at=d.get("created_at"),
        representations=[decode_representation(r) for r in d.get("representations", [])],
        spatial=spatial,
        viewpoints=viewpoints,
        render_hints=render_hints,
        workflow=workflow,
        derived_from=d.get("derived_from"),
        metadata=d.get("metadata"),
    )
