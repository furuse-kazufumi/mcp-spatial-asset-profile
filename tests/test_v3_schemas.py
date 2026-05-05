"""CI tests for v3 JSON Schema files.

Coverage:
  TestSchemaStructure    — each schema file is valid JSON with required meta-fields
  TestSpatialAssetV3     — structure, asset kinds, required properties
  TestCamerasSchema      — camera array, intrinsics, extrinsics
  TestSceneSchema        — duration, trajectory types
  TestGroundTruthSchema  — trajectories, expected_assets
  TestSampleFilesConform — sample config / ground-truth files validate against schemas
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT       = Path(__file__).parents[1]
SPEC_V3    = ROOT / "spec" / "v3"
SAMPLES_V3 = ROOT / "samples" / "v3" / "synthetic-debug-demo"

sys.path.insert(0, str(ROOT))

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# ── helpers ───────────────────────────────────────────────────────────────────

def _load(name: str) -> dict:
    return json.loads((SPEC_V3 / name).read_bytes().decode("utf-8"))

def _load_sample(rel: str) -> dict:
    return json.loads((SAMPLES_V3 / rel).read_bytes().decode("utf-8"))


# ── TestSchemaStructure ───────────────────────────────────────────────────────

class TestSchemaStructure:
    """All four v3 schema files must exist, be valid JSON, and carry meta-fields."""

    SCHEMA_FILES = [
        "spatial-asset-v3.schema.json",
        "cameras.schema.json",
        "scene.schema.json",
        "ground-truth.schema.json",
    ]

    @pytest.mark.parametrize("fname", SCHEMA_FILES)
    def test_file_exists(self, fname):
        assert (SPEC_V3 / fname).exists(), f"Schema missing: {SPEC_V3 / fname}"

    @pytest.mark.parametrize("fname", SCHEMA_FILES)
    def test_valid_json(self, fname):
        data = _load(fname)
        assert isinstance(data, dict)

    @pytest.mark.parametrize("fname", SCHEMA_FILES)
    def test_has_schema_meta(self, fname):
        data = _load(fname)
        assert "$schema" in data, f"{fname} missing $schema"
        assert "$id"     in data, f"{fname} missing $id"
        assert "title"   in data, f"{fname} missing title"

    @pytest.mark.parametrize("fname", SCHEMA_FILES)
    def test_has_type_or_oneof(self, fname):
        data = _load(fname)
        assert "type" in data or "oneOf" in data or "$ref" in data, \
            f"{fname} has no type/oneOf/$ref at root"


# ── TestSpatialAssetV3 ────────────────────────────────────────────────────────

class TestSpatialAssetV3:
    def setup_method(self):
        self.schema = _load("spatial-asset-v3.schema.json")

    def test_root_requires_version_and_kind(self):
        assert "version" in self.schema["required"]
        assert "kind"    in self.schema["required"]

    def test_kind_enum_has_four_values(self):
        kind_prop = self.schema["properties"]["kind"]
        assert set(kind_prop["enum"]) == {
            "event-frame-2d", "event-tracklet-3d",
            "motion-evidence-3d", "vllm-summary",
        }

    def test_version_const_is_3_0(self):
        assert self.schema["properties"]["version"]["const"] == "3.0"

    def test_has_oneof_for_kinds(self):
        assert "oneOf" in self.schema
        assert len(self.schema["oneOf"]) == 4

    def test_defs_contain_all_kinds(self):
        defs = self.schema.get("$defs", {})
        for name in ("EventFrame2D", "EventTracklet3D", "MotionEvidence3D", "VllmSummary"):
            assert name in defs, f"$defs missing {name}"

    def test_tracklet_point_has_required_fields(self):
        tp = self.schema["$defs"]["TrackletPoint"]
        assert "t_us"     in tp["required"]
        assert "position" in tp["required"]

    def test_event_frame_2d_required_fields(self):
        ef = self.schema["$defs"]["EventFrame2D"]
        for field in ("camera_id", "time_window", "accumulator", "sensor"):
            assert field in ef["required"]

    def test_event_tracklet_3d_required_fields(self):
        et = self.schema["$defs"]["EventTracklet3D"]
        for field in ("tracklet_id", "camera_ids", "crs", "points"):
            assert field in et["required"]

    def test_motion_evidence_required_fields(self):
        me = self.schema["$defs"]["MotionEvidence3D"]
        assert "tracklet_ids" in me["required"]
        assert "crs"          in me["required"]

    def test_vllm_summary_requires_text(self):
        vs = self.schema["$defs"]["VllmSummary"]
        assert "text" in vs["required"]

    def test_asset_ref_requires_id(self):
        ar = self.schema["$defs"]["AssetRef"]
        assert "id" in ar["required"]

    def test_vec3_is_3_element_array(self):
        v = self.schema["$defs"]["Vec3"]
        assert v["minItems"] == 3
        assert v["maxItems"] == 3

    def test_time_window_has_start_and_end(self):
        tw = self.schema["$defs"]["TimeWindow"]
        assert "t_start_us" in tw["required"]
        assert "t_end_us"   in tw["required"]

    def test_camera_intrinsics_requires_fx_fy_cx_cy(self):
        ci = self.schema["$defs"]["CameraIntrinsics"]
        for f in ("fx", "fy", "cx", "cy"):
            assert f in ci["required"]

    def test_representation2d_requires_format_and_uri(self):
        r = self.schema["$defs"]["Representation2D"]
        assert "format" in r["required"]
        assert "uri"    in r["required"]

    def test_accumulator_enum_values(self):
        ef = self.schema["$defs"]["EventFrame2D"]
        acc = ef["properties"]["accumulator"]
        assert set(acc["enum"]) == {"polarity-signed", "count", "time-surface"}


# ── TestCamerasSchema ─────────────────────────────────────────────────────────

class TestCamerasSchema:
    def setup_method(self):
        self.schema = _load("cameras.schema.json")

    def test_root_type_is_object(self):
        assert self.schema["type"] == "object"

    def test_cameras_array_required(self):
        assert "cameras" in self.schema["required"]

    def test_cameras_array_min_two(self):
        assert self.schema["properties"]["cameras"]["minItems"] == 2

    def test_camera_spec_required_fields(self):
        cs = self.schema["$defs"]["CameraSpec"]
        for f in ("id", "resolution", "intrinsics", "T_world_cam"):
            assert f in cs["required"]

    def test_t_world_cam_is_4x4(self):
        mat = self.schema["$defs"]["Mat4x4"]
        assert mat["minItems"] == 4
        assert mat["maxItems"] == 4
        assert mat["items"]["minItems"] == 4
        assert mat["items"]["maxItems"] == 4

    def test_resolution_is_2_element_array(self):
        cs = self.schema["$defs"]["CameraSpec"]
        res = cs["properties"]["resolution"]
        assert res["minItems"] == 2
        assert res["maxItems"] == 2

    def test_intrinsics_requires_focal_lengths(self):
        ci = self.schema["$defs"]["CameraIntrinsics"]
        for f in ("fx", "fy", "cx", "cy"):
            assert f in ci["required"]

    def test_time_offset_is_integer(self):
        cs = self.schema["$defs"]["CameraSpec"]
        assert cs["properties"]["time_offset_us"]["type"] == "integer"

    def test_no_extra_root_properties(self):
        assert self.schema.get("additionalProperties") is False


# ── TestSceneSchema ───────────────────────────────────────────────────────────

class TestSceneSchema:
    def setup_method(self):
        self.schema = _load("scene.schema.json")

    def test_root_requires_duration_and_trajectories(self):
        for f in ("duration_us", "trajectories"):
            assert f in self.schema["required"]

    def test_duration_is_positive_integer(self):
        d = self.schema["properties"]["duration_us"]
        assert d["type"] == "integer"
        assert d.get("exclusiveMinimum") == 0

    def test_trajectories_min_one(self):
        assert self.schema["properties"]["trajectories"]["minItems"] == 1

    def test_three_trajectory_types_defined(self):
        defs = self.schema["$defs"]
        for name in ("LinearTrajectory", "CircularTrajectory", "ZigzagTrajectory"):
            assert name in defs

    def test_linear_trajectory_requires_start_end_pos(self):
        lt = self.schema["$defs"]["LinearTrajectory"]
        # allOf[1] carries the type-specific required fields
        type_specific = lt["allOf"][1]
        for f in ("start_pos", "end_pos"):
            assert f in type_specific["required"]

    def test_circular_trajectory_requires_center_radius(self):
        ct = self.schema["$defs"]["CircularTrajectory"]
        type_specific = ct["allOf"][1]
        for f in ("center", "radius_m", "axis"):
            assert f in type_specific["required"]

    def test_zigzag_trajectory_requires_waypoints(self):
        zt = self.schema["$defs"]["ZigzagTrajectory"]
        type_specific = zt["allOf"][1]
        assert "waypoints" in type_specific["required"]

    def test_trajectory_discriminator_is_oneof(self):
        assert "oneOf" in self.schema["$defs"]["Trajectory"]
        assert len(self.schema["$defs"]["Trajectory"]["oneOf"]) == 3

    def test_no_extra_root_properties(self):
        assert self.schema.get("additionalProperties") is False


# ── TestGroundTruthSchema ─────────────────────────────────────────────────────

class TestGroundTruthSchema:
    def setup_method(self):
        self.schema = _load("ground-truth.schema.json")

    def test_root_requires_duration_and_trajectories(self):
        for f in ("scene_duration_us", "trajectories"):
            assert f in self.schema["required"]

    def test_trajectories_min_one(self):
        assert self.schema["properties"]["trajectories"]["minItems"] == 1

    def test_trajectory_gt_requires_id_and_sample_points(self):
        tgt = self.schema["$defs"]["TrajectoryGroundTruth"]
        for f in ("id", "sample_points"):
            assert f in tgt["required"]

    def test_sample_point_requires_t_us_and_position(self):
        tp = self.schema["$defs"]["TrajectoryPoint"]
        for f in ("t_us", "position"):
            assert f in tp["required"]

    def test_tracklet_expectation_has_quality_thresholds(self):
        te = self.schema["$defs"]["TrackletExpectation"]
        props = te["properties"]
        for f in ("max_position_error_m", "max_time_error_us", "max_reprojection_error_px"):
            assert f in props

    def test_expected_assets_has_tracklet_count(self):
        ea = self.schema["$defs"]["ExpectedAssets"]
        assert "tracklet_count" in ea["properties"]

    def test_camera_projection_gt_required_fields(self):
        cp = self.schema["$defs"]["CameraProjectionGroundTruth"]
        for f in ("camera_id", "trajectory_id", "sample_points"):
            assert f in cp["required"]

    def test_no_extra_root_properties(self):
        assert self.schema.get("additionalProperties") is False


# ── TestSampleFilesConform ────────────────────────────────────────────────────

class TestSampleFilesConform:
    """Sample config/ground-truth files in samples/v3/ must match their schemas."""

    def test_cameras_json_has_two_cameras(self):
        data = _load_sample("config/cameras.json")
        assert "cameras" in data
        assert len(data["cameras"]) >= 2

    def test_cameras_each_have_required_fields(self):
        data = _load_sample("config/cameras.json")
        for cam in data["cameras"]:
            for f in ("id", "resolution", "intrinsics", "T_world_cam"):
                assert f in cam, f"camera {cam.get('id')} missing {f}"

    def test_cameras_intrinsics_have_focal_lengths(self):
        data = _load_sample("config/cameras.json")
        for cam in data["cameras"]:
            intr = cam["intrinsics"]
            for f in ("fx", "fy", "cx", "cy"):
                assert f in intr

    def test_cameras_t_world_cam_is_4x4(self):
        data = _load_sample("config/cameras.json")
        for cam in data["cameras"]:
            mat = cam["T_world_cam"]
            assert len(mat) == 4
            for row in mat:
                assert len(row) == 4

    def test_scene_json_has_trajectories(self):
        data = _load_sample("config/scene.json")
        assert "duration_us" in data
        assert len(data["trajectories"]) >= 1

    def test_scene_trajectory_is_linear(self):
        data = _load_sample("config/scene.json")
        traj = data["trajectories"][0]
        assert traj["type"] == "linear"
        assert "start_pos" in traj
        assert "end_pos"   in traj

    def test_ground_truth_trajectory_count_matches_scene(self):
        scene = _load_sample("config/scene.json")
        gt    = _load_sample("assertions/ground-truth.json")
        assert len(gt["trajectories"]) == len(scene["trajectories"])

    def test_ground_truth_has_expected_assets(self):
        gt = _load_sample("assertions/ground-truth.json")
        ea = gt["expected_assets"]
        assert ea["tracklet_count"] >= 1
        assert ea.get("derived_from_dag_closed") is True

    def test_ground_truth_position_error_threshold(self):
        gt = _load_sample("assertions/ground-truth.json")
        for texp in gt["expected_assets"].get("tracklets", []):
            assert texp["max_position_error_m"] > 0

    @pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
    def test_cameras_validates_against_schema(self):
        schema = _load("cameras.schema.json")
        data   = _load_sample("config/cameras.json")
        jsonschema.validate(instance=data, schema=schema)

    @pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
    def test_ground_truth_validates_against_schema(self):
        schema = _load("ground-truth.schema.json")
        data   = _load_sample("assertions/ground-truth.json")
        jsonschema.validate(instance=data, schema=schema)
