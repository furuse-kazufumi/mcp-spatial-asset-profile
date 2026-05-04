"""test_validators.py — Tests for schema and traceability validators"""

import json
import pytest
from pathlib import Path
from spatial_asset_v2.validators import validate_asset, validate_pipeline, build_asset_graph


_EXAMPLES_DIR = Path(__file__).parents[3] / "spec" / "examples"


class TestSchemaValidator:
    def test_valid_pointcloud(self):
        asset = {
            "version": "2.0",
            "asset_id": "urn:uuid:test-001",
            "kind": "point-cloud",
            "representations": [{"format": "ply", "uri": "test.ply"}],
        }
        errors = validate_asset(asset)
        assert errors == []

    def test_missing_version(self):
        asset = {
            "asset_id": "urn:uuid:x",
            "kind": "point-cloud",
            "representations": [{"format": "ply", "uri": "test.ply"}],
        }
        errors = validate_asset(asset)
        assert any("version" in e for e in errors)

    def test_wrong_version(self):
        asset = {
            "version": "1.0",
            "asset_id": "urn:uuid:x",
            "kind": "point-cloud",
            "representations": [{"format": "ply", "uri": "test.ply"}],
        }
        errors = validate_asset(asset)
        assert any("version" in e for e in errors)

    def test_missing_asset_id(self):
        asset = {
            "version": "2.0",
            "kind": "point-cloud",
            "representations": [{"format": "ply", "uri": "test.ply"}],
        }
        errors = validate_asset(asset)
        assert any("asset_id" in e for e in errors)

    def test_missing_representations(self):
        asset = {
            "version": "2.0",
            "asset_id": "urn:uuid:x",
            "kind": "point-cloud",
        }
        errors = validate_asset(asset)
        assert any("representations" in e for e in errors)

    def test_invalid_depth_scale(self):
        asset = {
            "version": "2.0",
            "asset_id": "urn:uuid:x",
            "kind": "depth-image",
            "representations": [{"format": "png-depth", "uri": "d.png", "depth_scale": -1}],
        }
        errors = validate_asset(asset)
        assert any("depth_scale" in e for e in errors)

    def test_rendered_view_requires_workflow(self):
        asset = {
            "version": "2.0",
            "asset_id": "urn:uuid:x",
            "kind": "rendered-view",
            "representations": [{"format": "png", "uri": "view.png"}],
            "workflow": {
                "target_asset_id": "",
                "viewpoint_id": "vp-1",
            },
        }
        errors = validate_asset(asset)
        assert any("target_asset_id" in e for e in errors)

    def test_object_asset_requires_instance_id(self):
        asset = {
            "version": "2.0",
            "asset_id": "urn:uuid:x",
            "kind": "object-asset",
            "representations": [{"format": "ply", "uri": "obj.ply"}],
            "workflow": {
                "target_asset_id": "urn:uuid:src",
                "instance_id": "",
            },
        }
        errors = validate_asset(asset)
        assert any("instance_id" in e for e in errors)

    def test_confidence_out_of_range(self):
        asset = {
            "version": "2.0",
            "asset_id": "urn:uuid:x",
            "kind": "segmentation-mask-2d",
            "representations": [{"format": "png-mask", "uri": "mask.png"}],
            "workflow": {
                "target_asset_id": "urn:uuid:rv",
                "viewpoint_id": "vp-1",
                "confidence": 1.5,
            },
        }
        errors = validate_asset(asset)
        assert any("confidence" in e for e in errors)

    def test_example_files_valid(self):
        """All example JSON files in spec/examples/ should be valid."""
        if not _EXAMPLES_DIR.exists():
            pytest.skip("spec/examples/ not found")
        for json_path in _EXAMPLES_DIR.glob("*.json"):
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            errors = validate_asset(data)
            assert errors == [], f"{json_path.name}: {errors}"


class TestTraceabilityValidator:
    def _make_source(self, asset_id: str = "urn:uuid:src") -> dict:
        return {
            "version": "2.0",
            "asset_id": asset_id,
            "kind": "point-cloud",
            "representations": [{"format": "ply", "uri": "src.ply"}],
        }

    def _make_rv(self, rv_id: str, src_id: str) -> dict:
        return {
            "version": "2.0",
            "asset_id": rv_id,
            "kind": "rendered-view",
            "representations": [{"format": "png", "uri": "rv.png"}],
            "derived_from": [src_id],
            "workflow": {"step": "render", "target_asset_id": src_id, "viewpoint_id": "vp-1"},
        }

    def _make_mask2d(self, m2d_id: str, rv_id: str) -> dict:
        return {
            "version": "2.0",
            "asset_id": m2d_id,
            "kind": "segmentation-mask-2d",
            "representations": [{"format": "png-mask", "uri": "m.png"}],
            "derived_from": [rv_id],
            "workflow": {"step": "seg-2d", "target_asset_id": rv_id, "viewpoint_id": "vp-1"},
        }

    def _make_mask3d(self, m3d_id: str, src_id: str, mask2d_ids: list) -> dict:
        return {
            "version": "2.0",
            "asset_id": m3d_id,
            "kind": "segmentation-mask-3d",
            "representations": [{"format": "npy", "uri": "m3d.npy"}],
            "derived_from": [src_id] + mask2d_ids,
            "workflow": {
                "step": "lift-3d",
                "target_asset_id": src_id,
                "source_masks": mask2d_ids,
            },
        }

    def _make_obj(self, obj_id: str, src_id: str, m3d_id: str) -> dict:
        return {
            "version": "2.0",
            "asset_id": obj_id,
            "kind": "object-asset",
            "representations": [{"format": "ply", "uri": "obj.ply"}],
            "derived_from": [src_id, m3d_id],
            "workflow": {
                "step": "extract",
                "target_asset_id": src_id,
                "instance_id": "obj-001",
            },
        }

    def test_valid_full_pipeline(self):
        src = self._make_source("urn:uuid:src")
        rv = self._make_rv("urn:uuid:rv", "urn:uuid:src")
        m2d = self._make_mask2d("urn:uuid:m2d", "urn:uuid:rv")
        m3d = self._make_mask3d("urn:uuid:m3d", "urn:uuid:src", ["urn:uuid:m2d"])
        obj = self._make_obj("urn:uuid:obj", "urn:uuid:src", "urn:uuid:m3d")
        errors = validate_pipeline([src, rv, m2d, m3d, obj])
        assert errors == []

    def test_broken_derived_from(self):
        src = self._make_source("urn:uuid:src")
        rv = self._make_rv("urn:uuid:rv", "urn:uuid:UNKNOWN")
        errors = validate_pipeline([src, rv])
        assert any("unknown" in e.lower() for e in errors)

    def test_wrong_kind_for_rendered_view(self):
        m2d = {
            "version": "2.0",
            "asset_id": "urn:uuid:m2d",
            "kind": "segmentation-mask-2d",
            "representations": [{"format": "png-mask", "uri": "m.png"}],
            "workflow": {"step": "seg", "target_asset_id": "urn:uuid:src", "viewpoint_id": "vp-1"},
        }
        # src is a rendered-view, but mask-2d expects rendered-view as target - that's fine
        # Let's test rendered-view pointing to mask-2d (wrong)
        rv_wrong = {
            "version": "2.0",
            "asset_id": "urn:uuid:rv",
            "kind": "rendered-view",
            "representations": [{"format": "png", "uri": "rv.png"}],
            "workflow": {"step": "render", "target_asset_id": "urn:uuid:m2d", "viewpoint_id": "vp-1"},
        }
        errors = validate_pipeline([m2d, rv_wrong])
        assert any("rendered-view" in e for e in errors)

    def test_build_asset_graph(self):
        src = self._make_source("urn:uuid:src")
        rv = self._make_rv("urn:uuid:rv", "urn:uuid:src")
        graph = build_asset_graph([src, rv])
        assert "urn:uuid:src" in graph
        assert "urn:uuid:rv" in graph
        assert "urn:uuid:src" in graph["urn:uuid:rv"]
