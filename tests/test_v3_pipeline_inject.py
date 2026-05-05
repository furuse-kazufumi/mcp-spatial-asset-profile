"""AC-4: Verify the assertion harness detects failure for all damaging inject modes.

Each test runs the full synthetic pipeline with an inject mode, then runs
validate.py and checks whether the exit code is 0 (pass) or non-zero (fail).

Inject mode behaviour (empirically verified):
  calibration_error  5-deg cam1 extrinsic rotation → large triangulation error     → FAIL
  time_skew          5ms cam1 clock offset          → frame-pair mismatch, 0 tracklets → FAIL
  hot_pixel          50 spurious events             → centroid shift, RMS ~1.36m   → FAIL
  drop_polarity      no-op (polarity already +1)                                   → PASS

AC-4 gate: all three damaging modes must be detected (harness exits non-zero).
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
PYTHON = sys.executable

SCENE   = ROOT / "samples" / "v3" / "synthetic-debug-demo" / "config" / "scene.json"
CAMERAS = ROOT / "samples" / "v3" / "synthetic-debug-demo" / "config" / "cameras.json"
GT      = ROOT / "samples" / "v3" / "synthetic-debug-demo" / "assertions" / "ground-truth.json"


def _run_pipeline(out_dir: Path, inject: str | None) -> int:
    cmd = [
        PYTHON, "-m", "sdk.python.spatial_asset_v3.demos.synthetic",
        "--config",  str(SCENE),
        "--cameras", str(CAMERAS),
        "--out",     str(out_dir),
        "--seed",    "42",
    ]
    if inject:
        cmd += ["--inject", inject]
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True)
    return r.returncode


def _run_validate(out_dir: Path) -> tuple[int, str]:
    cmd = [
        PYTHON, "-m", "sdk.python.spatial_asset_v3.demos.validate",
        "--bundle",       str(out_dir),
        "--ground-truth", str(GT),
    ]
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


# ── prerequisite: config files must exist ─────────────────────────────────────

def test_config_files_exist():
    assert SCENE.exists(),   f"scene.json missing: {SCENE}"
    assert CAMERAS.exists(), f"cameras.json missing: {CAMERAS}"
    assert GT.exists(),      f"ground-truth.json missing: {GT}"


# ── baseline ──────────────────────────────────────────────────────────────────

def test_baseline_no_inject_passes():
    """Pipeline without injection must satisfy all ACs."""
    with tempfile.TemporaryDirectory() as tmp:
        rc = _run_pipeline(Path(tmp), inject=None)
        assert rc == 0, "pipeline returned non-zero"
        rc_v, out = _run_validate(Path(tmp))
        assert rc_v == 0, f"Baseline harness failed:\n{out}"


# ── AC-4: calibration_error must be detected ──────────────────────────────────

def test_calibration_error_detected():
    """5-degree cam1 extrinsic rotation causes ~260mm position error; harness must exit non-zero."""
    with tempfile.TemporaryDirectory() as tmp:
        rc = _run_pipeline(Path(tmp), inject="calibration_error")
        assert rc == 0, "pipeline returned non-zero with calibration_error inject"
        rc_v, out = _run_validate(Path(tmp))
        assert rc_v != 0, (
            "AC-4 FAIL: calibration_error inject was NOT detected by harness.\n"
            f"Harness output:\n{out}"
        )


# ── no-op modes: harness should still pass ────────────────────────────────────

def test_drop_polarity_passes():
    """drop_polarity is a no-op (all events already +1), so harness must still pass."""
    with tempfile.TemporaryDirectory() as tmp:
        rc = _run_pipeline(Path(tmp), inject="drop_polarity")
        assert rc == 0, "pipeline returned non-zero with drop_polarity inject"
        rc_v, out = _run_validate(Path(tmp))
        assert rc_v == 0, f"drop_polarity (no-op) incorrectly failed harness:\n{out}"


# ── AC-4: remaining damaging modes must also be detected ─────────────────────

def test_time_skew_detected():
    """5ms cam1 clock offset causes frame-pair temporal mismatch → 0 tracklets → harness FAIL.

    The 5ms skew (time_offset_us += 5000) shifts cam1 events so the accumulator
    windows no longer align with cam0. build_tracklets finds no matching frame
    pairs across cameras, producing zero tracklets — well below the expected 1.
    """
    with tempfile.TemporaryDirectory() as tmp:
        rc = _run_pipeline(Path(tmp), inject="time_skew")
        assert rc == 0, "pipeline returned non-zero with time_skew inject"
        rc_v, out = _run_validate(Path(tmp))
        assert rc_v != 0, (
            "AC-4 FAIL: time_skew inject was NOT detected by harness.\n"
            f"Harness output:\n{out}"
        )


def test_hot_pixel_detected():
    """50 spurious events uniformly distributed shift centroids by ~1.36m RMS → harness FAIL.

    Hot pixels add random fixed-position events that dominate centroid estimation
    in some frames, causing the triangulated 3D positions to diverge far beyond
    the 0.015m position tolerance.
    """
    with tempfile.TemporaryDirectory() as tmp:
        rc = _run_pipeline(Path(tmp), inject="hot_pixel")
        assert rc == 0, "pipeline returned non-zero with hot_pixel inject"
        rc_v, out = _run_validate(Path(tmp))
        assert rc_v != 0, (
            "AC-4 FAIL: hot_pixel inject was NOT detected by harness.\n"
            f"Harness output:\n{out}"
        )
