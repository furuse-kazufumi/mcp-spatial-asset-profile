"""test_models.py — Tests for spatial_asset_v2.models"""

import pytest
from spatial_asset_v2.models import (
    SpatialAsset, Representation, Spatial, BoundingBox,
    Viewpoint, RenderHints, Workflow, WorkflowLabel, VALID_KINDS, VALID_FORMATS
)


class TestRepresentation:
    def test_minimal_valid(self):
        r = Representation(format="ply", uri="test.ply")
        assert r.format == "ply"
        assert r.uri == "test.ply"

    def test_with_all_optional(self):
        r = Representation(
            format="npy", uri="labels.npy",
            rep_id="rep-1", point_count=1000,
            channels=["x", "y", "z"],
        )
        assert r.rep_id == "rep-1"
        assert r.point_count == 1000
        assert r.channels == ["x", "y", "z"]


class TestSpatial:
    def test_defaults(self):
        s = Spatial()
        assert s.up_axis == "+Y"
        assert s.handedness == "right"
        assert s.unit == "m"
        assert s.frame is None
        assert s.bounds is None

    def test_with_bounds(self):
        bb = BoundingBox(min=[-1.0, -1.0, -1.0], max=[1.0, 1.0, 1.0])
        s = Spatial(unit="mm", bounds=bb)
        assert s.unit == "mm"
        assert s.bounds.min == [-1.0, -1.0, -1.0]


class TestSpatialAsset:
    def test_minimal_asset(self):
        asset = SpatialAsset(
            asset_id="urn:uuid:test-001",
            kind="point-cloud",
            representations=[Representation(format="ply", uri="test.ply")],
        )
        assert asset.version == "2.0"
        assert asset.asset_id == "urn:uuid:test-001"
        assert asset.kind == "point-cloud"
        assert len(asset.representations) == 1

    def test_validate_basic_ok(self):
        asset = SpatialAsset(
            asset_id="urn:uuid:test-001",
            kind="mesh",
            representations=[Representation(format="obj", uri="mesh.obj")],
        )
        errors = asset.validate_basic()
        assert errors == []

    def test_validate_missing_asset_id(self):
        asset = SpatialAsset(
            asset_id="",
            kind="point-cloud",
            representations=[Representation(format="ply", uri="test.ply")],
        )
        errors = asset.validate_basic()
        assert any("asset_id" in e for e in errors)

    def test_validate_invalid_kind(self):
        asset = SpatialAsset(
            asset_id="urn:uuid:x",
            kind="invalid-kind",
            representations=[Representation(format="ply", uri="test.ply")],
        )
        errors = asset.validate_basic()
        assert any("kind" in e for e in errors)

    def test_validate_empty_representations(self):
        asset = SpatialAsset(
            asset_id="urn:uuid:x",
            kind="point-cloud",
            representations=[],
        )
        errors = asset.validate_basic()
        assert any("representations" in e for e in errors)

    def test_all_kinds_valid(self):
        for kind in VALID_KINDS:
            asset = SpatialAsset(
                asset_id="urn:uuid:x",
                kind=kind,
                representations=[Representation(format="ply", uri="test.ply")],
            )
            errors = asset.validate_basic()
            # Only kind-specific format errors possible for some, but kind itself should be valid
            kind_errors = [e for e in errors if "kind" in e]
            assert kind_errors == [], f"Unexpected kind error for '{kind}': {kind_errors}"


class TestWorkflow:
    def test_workflow_fields(self):
        wf = Workflow(
            step="render",
            target_asset_id="urn:uuid:source",
            viewpoint_id="vp-front",
            confidence=0.95,
        )
        assert wf.step == "render"
        assert wf.confidence == 0.95

    def test_workflow_labels(self):
        labels = [
            WorkflowLabel(id=0, name="background", color=[0, 0, 0]),
            WorkflowLabel(id=1, name="object", color=[255, 128, 0]),
        ]
        wf = Workflow(labels=labels)
        assert len(wf.labels) == 2
        assert wf.labels[0].name == "background"
