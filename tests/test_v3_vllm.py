"""Tests for Layer 3: vllm-summary mock generation."""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

import pytest

from sdk.python.spatial_asset_v3.vllm.mock import summarise
from sdk.python.spatial_asset_v3._validator import validate_bundle
from sdk.python.spatial_asset_v3.pipeline import run as pipeline_run


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_tracklet(tid: str, cam_ids: list[str], n_points: int = 3) -> dict:
    points = [
        {
            "t_us": i * 10_000,
            "position": [float(i) * 0.1, 0.5, 1.0],
            "reprojection_error_px": 0.5 + i * 0.1,
            "source_cameras": cam_ids,
        }
        for i in range(n_points)
    ]
    return {
        "version": "3.0",
        "kind": "event-tracklet-3d",
        "id": f"tracklet:{tid}",
        "tracklet_id": tid,
        "camera_ids": cam_ids,
        "crs": "world",
        "time_range": {"t_start_us": 0, "t_end_us": (n_points - 1) * 10_000},
        "points": points,
    }


def _make_motion(tracklets: list[dict]) -> dict:
    return {
        "version": "3.0",
        "kind": "motion-evidence-3d",
        "id": "motion:bundle",
        "tracklet_ids": [t["id"] for t in tracklets],
        "crs": "world",
        "time_range": {"t_start_us": 0, "t_end_us": 20_000},
        "scene_bounds": {
            "min": [-1.0, -1.0, -1.0],
            "max": [1.0, 1.0, 1.0],
        },
    }


def _make_frame(cam_id: str, idx: int) -> dict:
    return {
        "version": "3.0",
        "kind": "event-frame-2d",
        "id": f"frame:{cam_id}:{idx}",
        "camera_id": cam_id,
        "time_window": {"t_start_us": idx * 10_000, "t_end_us": (idx + 1) * 10_000},
        "accumulator": "polarity-signed",
        "event_count": 42,
        "sensor": {
            "resolution": [346, 260],
            "intrinsics": {"fx": 200.0, "fy": 200.0, "cx": 173.0, "cy": 130.0},
        },
    }


# ---------------------------------------------------------------------------
# Unit tests: mock.summarise
# ---------------------------------------------------------------------------

class TestSummariseBasic:
    def test_returns_vllm_summary_kind(self):
        assets = [_make_tracklet("t1", ["cam0", "cam1"])]
        s = summarise(assets)
        assert s["kind"] == "vllm-summary"

    def test_text_is_nonempty(self):
        assets = [_make_tracklet("t1", ["cam0", "cam1"])]
        s = summarise(assets)
        assert isinstance(s["text"], str) and len(s["text"]) > 0

    def test_provenance_model_is_mock(self):
        assets = [_make_tracklet("t1", ["cam0", "cam1"])]
        s = summarise(assets)
        assert s["provenance"]["model"] == "mock"

    def test_provenance_temperature_zero(self):
        assets = [_make_tracklet("t1", ["cam0", "cam1"])]
        s = summarise(assets)
        assert s["provenance"]["temperature"] == 0.0

    def test_provenance_has_prompt_hash(self):
        assets = [_make_tracklet("t1", ["cam0", "cam1"])]
        s = summarise(assets)
        ph = s["provenance"]["prompt_hash"]
        assert re.fullmatch(r"[0-9a-f]{16}", ph)

    def test_language_default_en(self):
        s = summarise([])
        assert s["language"] == "en"

    def test_language_override(self):
        s = summarise([], language="ja")
        assert s["language"] == "ja"

    def test_has_id_and_created_at(self):
        s = summarise([])
        assert "id" in s and s["id"].startswith("vllm-summary:")
        assert "created_at" in s

    def test_version_is_3_0(self):
        s = summarise([])
        assert s["version"] == "3.0"


class TestSummariseDerivedFrom:
    def test_derived_from_includes_tracklets(self):
        t = _make_tracklet("t1", ["cam0", "cam1"])
        s = summarise([t])
        ids = {d["id"] for d in s["derived_from"]}
        assert t["id"] in ids

    def test_derived_from_includes_motion(self):
        t = _make_tracklet("t1", ["cam0", "cam1"])
        m = _make_motion([t])
        s = summarise([t, m])
        ids = {d["id"] for d in s["derived_from"]}
        assert m["id"] in ids

    def test_derived_from_source_id(self):
        s = summarise([], source_id="config:scene")
        ids = {d["id"] for d in s["derived_from"]}
        assert "config:scene" in ids

    def test_derived_from_empty_no_source(self):
        s = summarise([])
        assert s["derived_from"] == []


class TestSummariseStats:
    def test_n_tracklets_in_text(self):
        assets = [
            _make_tracklet("t1", ["cam0", "cam1"]),
            _make_tracklet("t2", ["cam0", "cam1"]),
        ]
        s = summarise(assets)
        assert "2 moving object" in s["text"]

    def test_zero_tracklets(self):
        s = summarise([])
        assert "0 moving object" in s["text"]

    def test_camera_names_in_text(self):
        t = _make_tracklet("t1", ["cam_alpha", "cam_beta"])
        s = summarise([t])
        assert "cam_alpha" in s["text"] and "cam_beta" in s["text"]

    def test_frame_count_in_text(self):
        frames = [_make_frame("cam0", i) for i in range(5)]
        s = summarise(frames)
        assert "5" in s["text"]

    def test_scene_bounds_from_motion(self):
        t = _make_tracklet("t1", ["cam0", "cam1"])
        m = _make_motion([t])
        s = summarise([t, m])
        assert "-1.000" in s["text"] and "1.000" in s["text"]

    def test_reprojection_error_nonzero(self):
        t = _make_tracklet("t1", ["cam0", "cam1"], n_points=3)
        s = summarise([t])
        assert "0.00 px" not in s["text"]

    def test_empty_assets_no_crash(self):
        s = summarise([])
        assert s["kind"] == "vllm-summary"

    def test_deterministic_prompt_hash(self):
        """Same asset structure → same prompt hash (text is template-based)."""
        t = _make_tracklet("t1", ["cam0", "cam1"])
        s1 = summarise([t])
        s2 = summarise([t])
        assert s1["provenance"]["prompt_hash"] == s2["provenance"]["prompt_hash"]


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

class TestSummariseSchemaValid:
    def test_schema_validates(self):
        assets = [_make_tracklet("t1", ["cam0", "cam1"])]
        s = summarise(assets)
        errors = validate_bundle([s])
        assert errors == [], errors

    def test_full_bundle_with_summary_validates(self):
        t = _make_tracklet("t1", ["cam0", "cam1"])
        m = _make_motion([t])
        f = _make_frame("cam0", 0)
        s = summarise([t, m, f])
        errors = validate_bundle([t, m, f, s])
        assert errors == [], errors


# ---------------------------------------------------------------------------
# Pipeline integration
# ---------------------------------------------------------------------------

SCENE_CFG = Path("samples/v3/synthetic-debug-demo/config/scene.json")
CAMERAS_CFG = Path("samples/v3/synthetic-debug-demo/config/cameras.json")


@pytest.mark.skipif(
    not SCENE_CFG.exists() or not CAMERAS_CFG.exists(),
    reason="synthetic config not found",
)
class TestPipelineIncludesVllmSummary:
    def test_pipeline_produces_vllm_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pipeline_run(
                scene_path=SCENE_CFG,
                cameras_path=CAMERAS_CFG,
                out_dir=tmp,
                seed=42,
            )
            manifest = json.loads((out / "bundle_manifest.json").read_bytes().decode("utf-8"))
            kinds = [a["kind"] for a in manifest["assets"]]
            assert "vllm-summary" in kinds

    def test_pipeline_vllm_summary_schema_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pipeline_run(
                scene_path=SCENE_CFG,
                cameras_path=CAMERAS_CFG,
                out_dir=tmp,
                seed=42,
            )
            manifest = json.loads((out / "bundle_manifest.json").read_bytes().decode("utf-8"))
            assert manifest["schema_valid"] is True, manifest.get("schema_errors")

    def test_pipeline_vllm_file_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pipeline_run(
                scene_path=SCENE_CFG,
                cameras_path=CAMERAS_CFG,
                out_dir=tmp,
                seed=42,
            )
            manifest = json.loads((out / "bundle_manifest.json").read_bytes().decode("utf-8"))
            summary_entry = next(
                (a for a in manifest["assets"] if a["kind"] == "vllm-summary"), None
            )
            assert summary_entry is not None
            assert (out / summary_entry["file"]).exists()
