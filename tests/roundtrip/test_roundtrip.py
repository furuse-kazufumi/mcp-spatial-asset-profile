"""
tests/roundtrip/test_roundtrip.py — Full encode → decode round-trip tests.

Run from repository root:
    pytest tests/roundtrip/ -v
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
SDK_PATH = REPO_ROOT / "sdk" / "python"
sys.path.insert(0, str(SDK_PATH))

from spatial_asset_v2.codec import encode_asset, decode_asset, migrate_v1_to_v2
from spatial_asset_v2.models import (
    SpatialAsset, Representation, Spatial, BoundingBox,
    Viewpoint, RenderHints, Workflow, WorkflowLabel
)
from spatial_asset_v2.validators import validate_asset, validate_pipeline
from spatial_asset_v2.workflow import WorkflowMockRunner


class TestEncodeDecodeRoundTrip:
    def _roundtrip(self, asset: SpatialAsset) -> SpatialAsset:
        return decode_asset(encode_asset(asset))

    def test_minimal_roundtrip(self):
        asset = SpatialAsset(
            asset_id="urn:uuid:rt-001",
            kind="point-cloud",
            representations=[Representation(format="ply", uri="test.ply")],
        )
        rt = self._roundtrip(asset)
        assert rt.asset_id == asset.asset_id
        assert rt.kind == asset.kind

    def test_spatial_roundtrip(self):
        asset = SpatialAsset(
            asset_id="urn:uuid:rt-002",
            kind="mesh",
            representations=[Representation(format="obj", uri="m.obj")],
            spatial=Spatial(
                frame="ECEF",
                up_axis="+Z",
                unit="mm",
                bounds=BoundingBox(min=[0.0, 0.0, 0.0], max=[10.0, 10.0, 10.0]),
            ),
        )
        rt = self._roundtrip(asset)
        assert rt.spatial is not None
        assert rt.spatial.frame == "ECEF"
        assert rt.spatial.up_axis == "+Z"
        assert rt.spatial.unit == "mm"
        assert rt.spatial.bounds.max == [10.0, 10.0, 10.0]

    def test_viewpoints_roundtrip(self):
        asset = SpatialAsset(
            asset_id="urn:uuid:rt-003",
            kind="rendered-view",
            representations=[Representation(format="png", uri="rv.png", image_width=640, image_height=480)],
            viewpoints=[
                Viewpoint(
                    viewpoint_id="vp-test",
                    position=[0.0, 0.0, 1.0],
                    target=[0.0, 0.0, 0.0],
                    up=[0.0, 1.0, 0.0],
                    fov_y_deg=60.0,
                )
            ],
            workflow=Workflow(
                step="render",
                target_asset_id="urn:uuid:src",
                viewpoint_id="vp-test",
            ),
        )
        rt = self._roundtrip(asset)
        assert len(rt.viewpoints) == 1
        assert rt.viewpoints[0].viewpoint_id == "vp-test"
        assert rt.viewpoints[0].fov_y_deg == 60.0

    def test_workflow_labels_roundtrip(self):
        asset = SpatialAsset(
            asset_id="urn:uuid:rt-004",
            kind="segmentation-mask-3d",
            representations=[Representation(format="npy", uri="labels.npy", point_count=1000)],
            workflow=Workflow(
                step="lift-3d",
                target_asset_id="urn:uuid:src",
                labels=[
                    WorkflowLabel(id=0, name="background", color=[0, 0, 0]),
                    WorkflowLabel(id=1, name="object", color=[255, 128, 0]),
                ],
                confidence=0.87,
            ),
        )
        rt = self._roundtrip(asset)
        assert rt.workflow.step == "lift-3d"
        assert len(rt.workflow.labels) == 2
        assert rt.workflow.labels[1].color == [255, 128, 0]
        assert rt.workflow.confidence == 0.87

    def test_render_hints_roundtrip(self):
        asset = SpatialAsset(
            asset_id="urn:uuid:rt-005",
            kind="gaussian-splat",
            representations=[
                Representation(
                    format="splat", uri="scene.splat",
                    rep_id="rep-splat",
                    capabilities_required=["splat-render"],
                )
            ],
            render_hints=RenderHints(
                point_size=3.0,
                opacity=0.8,
                color_mode="rgb",
                preferred_representation="rep-splat",
            ),
        )
        rt = self._roundtrip(asset)
        assert rt.render_hints.point_size == 3.0
        assert rt.render_hints.opacity == 0.8
        assert rt.render_hints.preferred_representation == "rep-splat"

    def test_derived_from_roundtrip(self):
        asset = SpatialAsset(
            asset_id="urn:uuid:rt-006",
            kind="object-asset",
            representations=[Representation(format="ply", uri="obj.ply")],
            derived_from=["urn:uuid:src-001", "urn:uuid:mask-001"],
            workflow=Workflow(
                step="extract-object",
                target_asset_id="urn:uuid:src-001",
                instance_id="obj-001",
                label="bunny",
            ),
        )
        rt = self._roundtrip(asset)
        assert rt.derived_from == ["urn:uuid:src-001", "urn:uuid:mask-001"]
        assert rt.workflow.instance_id == "obj-001"


class TestWorkflowPipelineRoundTrip:
    def test_full_pipeline_roundtrip(self):
        runner = WorkflowMockRunner()
        source_id = "urn:uuid:test-source"
        pipeline = runner.run_full_pipeline(source_id)

        # Encode → decode each asset
        for asset_dict in pipeline:
            asset = decode_asset(asset_dict)
            re_encoded = encode_asset(asset)
            errors = validate_asset(re_encoded)
            assert errors == [], f"{asset.kind}: {errors}"

    def test_pipeline_traceability_preserved_after_roundtrip(self):
        runner = WorkflowMockRunner()
        source_id = "urn:uuid:test-source"
        source = {
            "version": "2.0",
            "asset_id": source_id,
            "kind": "point-cloud",
            "representations": [{"format": "ply", "uri": "src.ply"}],
        }
        pipeline = runner.run_full_pipeline(source_id)

        # Round-trip all assets
        rt_pipeline = [decode_asset(encode_asset(decode_asset(a))) for a in pipeline]
        rt_dicts = [encode_asset(a) for a in rt_pipeline]

        errors = validate_pipeline([source] + rt_dicts)
        assert errors == [], f"Traceability broken after roundtrip: {errors}"
