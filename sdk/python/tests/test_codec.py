"""test_codec.py — Tests for spatial_asset_v2.codec (encode/decode round-trip)"""

import pytest
from spatial_asset_v2.models import (
    SpatialAsset, Representation, Spatial, BoundingBox,
    Viewpoint, RenderHints, Workflow, WorkflowLabel
)
from spatial_asset_v2.codec import encode_asset, decode_asset, migrate_v1_to_v2


def make_full_asset() -> SpatialAsset:
    return SpatialAsset(
        asset_id="urn:uuid:550e8400-e29b-41d4-a716-446655440001",
        kind="point-cloud",
        name="Test Bunny",
        created_at="2025-05-01T09:00:00Z",
        representations=[
            Representation(
                format="ply",
                uri="test.ply",
                rep_id="rep-ply",
                lod=0,
                point_count=35947,
                channels=["x", "y", "z"],
            ),
            Representation(
                format="npy",
                uri="test.npy",
                lod=1,
                point_count=5000,
            ),
        ],
        spatial=Spatial(
            frame="local-ENU",
            up_axis="+Y",
            handedness="right",
            unit="m",
            bounds=BoundingBox(min=[-1.0, -1.0, -1.0], max=[1.0, 1.0, 1.0]),
        ),
        viewpoints=[
            Viewpoint(
                viewpoint_id="vp-front",
                label="Front",
                position=[0.0, 0.0, 1.0],
                target=[0.0, 0.0, 0.0],
                up=[0.0, 1.0, 0.0],
                fov_y_deg=45.0,
            )
        ],
        render_hints=RenderHints(point_size=2.0, opacity=1.0),
        workflow=Workflow(
            step="render",
            target_asset_id="urn:uuid:source",
            confidence=0.9,
            labels=[
                WorkflowLabel(id=0, name="bg", color=[0, 0, 0]),
                WorkflowLabel(id=1, name="obj", color=[255, 0, 0]),
            ],
        ),
        derived_from=["urn:uuid:parent"],
        metadata={"source": "test"},
    )


class TestRoundTrip:
    def test_encode_returns_dict(self):
        asset = make_full_asset()
        d = encode_asset(asset)
        assert isinstance(d, dict)

    def test_version_preserved(self):
        asset = make_full_asset()
        d = encode_asset(asset)
        assert d["version"] == "2.0"

    def test_asset_id_preserved(self):
        asset = make_full_asset()
        d = encode_asset(asset)
        assert d["asset_id"] == "urn:uuid:550e8400-e29b-41d4-a716-446655440001"

    def test_kind_preserved(self):
        asset = make_full_asset()
        d = encode_asset(asset)
        assert d["kind"] == "point-cloud"

    def test_representations_count(self):
        asset = make_full_asset()
        d = encode_asset(asset)
        assert len(d["representations"]) == 2

    def test_spatial_preserved(self):
        asset = make_full_asset()
        d = encode_asset(asset)
        assert "spatial" in d
        assert d["spatial"]["unit"] == "m"
        assert d["spatial"]["bounds"]["min"] == [-1.0, -1.0, -1.0]

    def test_viewpoints_preserved(self):
        asset = make_full_asset()
        d = encode_asset(asset)
        assert len(d["viewpoints"]) == 1
        assert d["viewpoints"][0]["viewpoint_id"] == "vp-front"

    def test_workflow_preserved(self):
        asset = make_full_asset()
        d = encode_asset(asset)
        assert d["workflow"]["step"] == "render"
        assert d["workflow"]["confidence"] == 0.9
        assert len(d["workflow"]["labels"]) == 2

    def test_full_roundtrip(self):
        original = make_full_asset()
        encoded = encode_asset(original)
        decoded = decode_asset(encoded)

        assert decoded.asset_id == original.asset_id
        assert decoded.kind == original.kind
        assert decoded.name == original.name
        assert len(decoded.representations) == len(original.representations)
        assert decoded.representations[0].format == "ply"
        assert decoded.representations[0].point_count == 35947
        assert decoded.spatial.unit == "m"
        assert decoded.spatial.bounds.min == [-1.0, -1.0, -1.0]
        assert decoded.viewpoints[0].viewpoint_id == "vp-front"
        assert decoded.workflow.step == "render"
        assert len(decoded.workflow.labels) == 2

    def test_none_fields_omitted(self):
        asset = SpatialAsset(
            asset_id="urn:uuid:x",
            kind="mesh",
            representations=[Representation(format="obj", uri="mesh.obj")],
        )
        d = encode_asset(asset)
        assert "spatial" not in d
        assert "viewpoints" not in d
        assert "workflow" not in d
        assert "derived_from" not in d


class TestMigrateV1:
    def test_version_updated(self):
        v1 = {
            "version": "1.0",
            "kind": "point-cloud",
            "representations": [{"format": "ply", "uri": "test.ply"}],
        }
        v2 = migrate_v1_to_v2(v1)
        assert v2["version"] == "2.0"

    def test_id_renamed_to_asset_id(self):
        v1 = {
            "version": "1.0",
            "id": "urn:uuid:old-id",
            "kind": "point-cloud",
            "representations": [{"format": "ply", "uri": "test.ply"}],
        }
        v2 = migrate_v1_to_v2(v1)
        assert v2["asset_id"] == "urn:uuid:old-id"
        assert "id" not in v2

    def test_crs_moved_to_spatial(self):
        v1 = {
            "version": "1.0",
            "id": "x",
            "kind": "point-cloud",
            "crs": "EPSG:4326",
            "representations": [{"format": "ply", "uri": "test.ply"}],
        }
        v2 = migrate_v1_to_v2(v1)
        assert v2["spatial"]["frame"] == "EPSG:4326"
        assert "crs" not in v2

    def test_bounds_moved_to_spatial(self):
        v1 = {
            "version": "1.0",
            "id": "x",
            "kind": "point-cloud",
            "bounds": {"min": [-1, -1, -1], "max": [1, 1, 1]},
            "representations": [{"format": "ply", "uri": "test.ply"}],
        }
        v2 = migrate_v1_to_v2(v1)
        assert v2["spatial"]["bounds"] == {"min": [-1, -1, -1], "max": [1, 1, 1]}
        assert "bounds" not in v2

    def test_original_not_mutated(self):
        v1 = {
            "version": "1.0",
            "id": "x",
            "kind": "point-cloud",
            "crs": "local",
            "representations": [{"format": "ply", "uri": "test.ply"}],
        }
        _ = migrate_v1_to_v2(v1)
        assert v1["version"] == "1.0"
        assert "crs" in v1

    def test_decode_auto_migrates_v1(self):
        v1 = {
            "version": "1.0",
            "id": "urn:uuid:v1-asset",
            "kind": "point-cloud",
            "crs": "local-ENU",
            "representations": [{"format": "ply", "uri": "test.ply"}],
        }
        asset = decode_asset(v1)
        assert asset.version == "2.0"
        assert asset.asset_id == "urn:uuid:v1-asset"
        assert asset.spatial.frame == "local-ENU"
