"""
mock_runner.py — WorkflowMockRunner

Runs a mock segmentation pipeline and emits valid v2 asset dicts.
No actual rendering, geometry, or ML inference is performed.

Pipeline steps:
  1. render(source) → rendered-view asset
  2. segment_2d(rendered-view) → segmentation-mask-2d asset
  3. lift_3d(source, mask-2d) → segmentation-mask-3d asset
  4. extract_object(source, mask-3d) → object-asset
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return f"urn:uuid:{uuid.uuid4()}"


class WorkflowMockRunner:
    """
    Produces a full chain of v2 asset dicts without performing actual computation.

    Usage:
        runner = WorkflowMockRunner(base_dir="samples/inspection")
        assets = runner.run_full_pipeline(
            source_asset_id="urn:uuid:...",
            source_ply_path="bunny_full.ply"
        )
        # assets: list of dicts for [rendered-view, mask-2d, mask-3d, object-asset]
    """

    def __init__(self, base_dir: str = "samples/inspection"):
        self.base_dir = str(base_dir)

    def render(
        self,
        source_asset_id: str,
        viewpoint_id: str = "vp-front",
        image_width: int = 640,
        image_height: int = 480,
    ) -> dict:
        """Produce a mock rendered-view asset."""
        asset_id = _new_id()
        return {
            "version": "2.0",
            "asset_id": asset_id,
            "kind": "rendered-view",
            "name": f"Mock render of {source_asset_id[-8:]}",
            "created_at": _now(),
            "derived_from": [source_asset_id],
            "representations": [
                {
                    "rep_id": "rep-png-render",
                    "format": "png",
                    "uri": f"{self.base_dir}/mock_render_{asset_id[-8:]}.png",
                    "image_width": image_width,
                    "image_height": image_height,
                    "viewpoint_id": viewpoint_id,
                }
            ],
            "viewpoints": [
                {
                    "viewpoint_id": viewpoint_id,
                    "label": "Front view",
                    "position": [0.0, 0.09, 0.4],
                    "target":   [0.0, 0.09, 0.0],
                    "up":       [0.0, 1.0,  0.0],
                    "fov_y_deg": 45.0,
                    "image_width": image_width,
                    "image_height": image_height,
                }
            ],
            "workflow": {
                "step": "render",
                "target_asset_id": source_asset_id,
                "viewpoint_id": viewpoint_id,
                "tool": "workflow-mock-runner",
                "tool_version": "2.0.0",
                "started_at": _now(),
                "completed_at": _now(),
            },
        }

    def segment_2d(
        self,
        rendered_view_asset: dict,
        labels: list[dict] | None = None,
        confidence: float = 0.90,
    ) -> dict:
        """Produce a mock segmentation-mask-2d asset."""
        if labels is None:
            labels = [
                {"id": 0, "name": "background", "color": [0, 0, 0]},
                {"id": 1, "name": "object",      "color": [255, 128, 0]},
            ]
        rv_id = rendered_view_asset["asset_id"]
        vp_id = rendered_view_asset.get("workflow", {}).get("viewpoint_id", "vp-front")
        rep = rendered_view_asset["representations"][0]
        w = rep.get("image_width", 640)
        h = rep.get("image_height", 480)

        asset_id = _new_id()
        return {
            "version": "2.0",
            "asset_id": asset_id,
            "kind": "segmentation-mask-2d",
            "name": f"Mock 2D mask for {rv_id[-8:]}",
            "created_at": _now(),
            "derived_from": [rv_id],
            "representations": [
                {
                    "rep_id": "rep-mask-png",
                    "format": "png-mask",
                    "uri": f"{self.base_dir}/mock_mask2d_{asset_id[-8:]}.png",
                    "image_width": w,
                    "image_height": h,
                }
            ],
            "workflow": {
                "step": "segmentation-2d",
                "target_asset_id": rv_id,
                "viewpoint_id": vp_id,
                "labels": labels,
                "confidence": confidence,
                "tool": "workflow-mock-runner",
                "tool_version": "2.0.0",
                "started_at": _now(),
                "completed_at": _now(),
            },
        }

    def lift_3d(
        self,
        source_asset_id: str,
        mask_2d_assets: list[dict],
        point_count: int = 35947,
        confidence: float = 0.85,
    ) -> dict:
        """Produce a mock segmentation-mask-3d asset."""
        mask_ids = [m["asset_id"] for m in mask_2d_assets]
        labels = (mask_2d_assets[0].get("workflow", {}).get("labels")
                  if mask_2d_assets else None)

        asset_id = _new_id()
        return {
            "version": "2.0",
            "asset_id": asset_id,
            "kind": "segmentation-mask-3d",
            "name": f"Mock 3D mask from {source_asset_id[-8:]}",
            "created_at": _now(),
            "derived_from": [source_asset_id] + mask_ids,
            "representations": [
                {
                    "rep_id": "rep-labels-npy",
                    "format": "npy",
                    "uri": f"{self.base_dir}/mock_mask3d_{asset_id[-8:]}.npy",
                    "point_count": point_count,
                }
            ],
            "workflow": {
                "step": "lift-3d",
                "target_asset_id": source_asset_id,
                "source_masks": mask_ids,
                "labels": labels,
                "confidence": confidence,
                "tool": "workflow-mock-runner",
                "tool_version": "2.0.0",
                "parameters": {"strategy": "nearest-point"},
                "started_at": _now(),
                "completed_at": _now(),
            },
        }

    def extract_object(
        self,
        source_asset_id: str,
        mask_3d_asset: dict,
        label_id: int = 1,
        label_name: str = "object",
        point_count: int = 31204,
        confidence: float = 0.91,
    ) -> dict:
        """Produce a mock object-asset."""
        mask_id = mask_3d_asset["asset_id"]
        instance_id = f"obj-{label_name}-001"

        asset_id = _new_id()
        return {
            "version": "2.0",
            "asset_id": asset_id,
            "kind": "object-asset",
            "name": f"Extracted '{label_name}' from {source_asset_id[-8:]}",
            "created_at": _now(),
            "derived_from": [source_asset_id, mask_id],
            "representations": [
                {
                    "rep_id": "rep-ply-object",
                    "format": "ply",
                    "uri": f"{self.base_dir}/mock_object_{asset_id[-8:]}.ply",
                    "point_count": point_count,
                    "channels": ["x", "y", "z"],
                }
            ],
            "workflow": {
                "step": "extract-object",
                "target_asset_id": source_asset_id,
                "instance_id": instance_id,
                "label": label_name,
                "confidence": confidence,
                "tool": "workflow-mock-runner",
                "tool_version": "2.0.0",
                "parameters": {"label_id": label_id},
                "started_at": _now(),
                "completed_at": _now(),
            },
        }

    def run_full_pipeline(
        self,
        source_asset_id: str,
        source_ply_path: str = "bunny_full.ply",
        point_count: int = 35947,
    ) -> list[dict]:
        """
        Run the full mock pipeline.

        Returns: [rendered-view, segmentation-mask-2d, segmentation-mask-3d, object-asset]
        """
        rv = self.render(source_asset_id)
        m2d = self.segment_2d(rv)
        m3d = self.lift_3d(source_asset_id, [m2d], point_count=point_count)
        obj = self.extract_object(source_asset_id, m3d)
        return [rv, m2d, m3d, obj]
