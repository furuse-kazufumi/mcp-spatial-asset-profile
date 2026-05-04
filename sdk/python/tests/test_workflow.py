"""test_workflow.py — Tests for WorkflowMockRunner"""

import pytest
from spatial_asset_v2.workflow import WorkflowMockRunner
from spatial_asset_v2.validators import validate_asset, validate_pipeline


class TestWorkflowMockRunner:
    def setup_method(self):
        self.runner = WorkflowMockRunner(base_dir="samples/test")
        self.source_id = "urn:uuid:550e8400-e29b-41d4-a716-446655440001"

    def test_render_produces_valid_asset(self):
        rv = self.runner.render(self.source_id)
        errors = validate_asset(rv)
        assert errors == [], f"render output invalid: {errors}"
        assert rv["kind"] == "rendered-view"
        assert rv["workflow"]["target_asset_id"] == self.source_id

    def test_segment_2d_produces_valid_asset(self):
        rv = self.runner.render(self.source_id)
        m2d = self.runner.segment_2d(rv)
        errors = validate_asset(m2d)
        assert errors == [], f"segment_2d output invalid: {errors}"
        assert m2d["kind"] == "segmentation-mask-2d"
        assert m2d["workflow"]["target_asset_id"] == rv["asset_id"]

    def test_lift_3d_produces_valid_asset(self):
        rv = self.runner.render(self.source_id)
        m2d = self.runner.segment_2d(rv)
        m3d = self.runner.lift_3d(self.source_id, [m2d])
        errors = validate_asset(m3d)
        assert errors == [], f"lift_3d output invalid: {errors}"
        assert m3d["kind"] == "segmentation-mask-3d"
        assert m3d["workflow"]["target_asset_id"] == self.source_id

    def test_extract_object_produces_valid_asset(self):
        rv = self.runner.render(self.source_id)
        m2d = self.runner.segment_2d(rv)
        m3d = self.runner.lift_3d(self.source_id, [m2d])
        obj = self.runner.extract_object(self.source_id, m3d)
        errors = validate_asset(obj)
        assert errors == [], f"extract_object output invalid: {errors}"
        assert obj["kind"] == "object-asset"
        assert obj["workflow"]["target_asset_id"] == self.source_id
        assert "instance_id" in obj["workflow"]

    def test_full_pipeline_length(self):
        pipeline = self.runner.run_full_pipeline(self.source_id)
        assert len(pipeline) == 4

    def test_full_pipeline_kinds(self):
        pipeline = self.runner.run_full_pipeline(self.source_id)
        kinds = [a["kind"] for a in pipeline]
        assert kinds == [
            "rendered-view",
            "segmentation-mask-2d",
            "segmentation-mask-3d",
            "object-asset",
        ]

    def test_full_pipeline_unique_ids(self):
        pipeline = self.runner.run_full_pipeline(self.source_id)
        ids = [a["asset_id"] for a in pipeline]
        assert len(ids) == len(set(ids)), "All pipeline asset IDs should be unique"

    def test_full_pipeline_traceability(self):
        source = {
            "version": "2.0",
            "asset_id": self.source_id,
            "kind": "point-cloud",
            "representations": [{"format": "ply", "uri": "src.ply"}],
        }
        pipeline = self.runner.run_full_pipeline(self.source_id)
        all_assets = [source] + pipeline
        errors = validate_pipeline(all_assets)
        assert errors == [], f"Traceability errors: {errors}"

    def test_all_pipeline_assets_valid(self):
        pipeline = self.runner.run_full_pipeline(self.source_id)
        for asset in pipeline:
            errors = validate_asset(asset)
            assert errors == [], f"Pipeline asset {asset['kind']} invalid: {errors}"

    def test_pipeline_asset_ids_are_urns(self):
        pipeline = self.runner.run_full_pipeline(self.source_id)
        for asset in pipeline:
            assert asset["asset_id"].startswith("urn:uuid:"), \
                f"asset_id should be URN: {asset['asset_id']}"

    def test_pipeline_has_timestamps(self):
        pipeline = self.runner.run_full_pipeline(self.source_id)
        for asset in pipeline:
            wf = asset.get("workflow", {})
            assert wf.get("completed_at"), f"Missing completed_at in {asset['kind']}"


class TestSampleGenerator:
    def test_generate_sample_assets(self):
        from spatial_asset_v2.samples import generate_sample_assets
        samples = generate_sample_assets()
        assert set(samples.keys()) == {"point-cloud", "mesh", "gaussian-splat", "depth-image"}
        for kind, asset in samples.items():
            errors = validate_asset(asset)
            assert errors == [], f"Sample {kind} invalid: {errors}"
