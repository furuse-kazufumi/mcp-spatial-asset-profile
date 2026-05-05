"""Tests for Layer 2 dataset adapters and the dataset_convert CLI.

Coverage:
  TestCsvAdapter      — load from CSV, column remapping, time units, polarity normalisation
  TestNumpyAdapter    — load from .npy (plain array), .npz (events key / separate keys)
  TestTxtAdapter      — load from whitespace-separated text with comments
  TestAutoDetect      — extension-based adapter selection, unknown-extension error
  TestDatasetConvert  — end-to-end CLI: CSV → v3 bundle with schema_valid=True
  TestSampleDataset   — sample_events.csv loads correctly and converts to a valid bundle
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

ROOT    = Path(__file__).parents[1]
PYTHON  = sys.executable
SAMPLES = ROOT / "samples" / "v3" / "datasets"

sys.path.insert(0, str(ROOT))

from sdk.python.spatial_asset_v3.adapters import (
    CsvAdapter, NumpyAdapter, TxtAdapter, auto_detect,
)
from sdk.python.spatial_asset_v3.event.generator import Event


# ── helpers ───────────────────────────────────────────────────────────────────

def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def _make_events(n: int = 10, t_start_us: int = 0, dt_us: int = 1000) -> list[dict]:
    return [{"x": 100 + i, "y": 50, "t": t_start_us + i * dt_us, "p": 1}
            for i in range(n)]


# ── TestCsvAdapter ────────────────────────────────────────────────────────────

class TestCsvAdapter:
    def test_load_basic(self, tmp_path):
        rows = _make_events(5)
        _write_csv(tmp_path / "ev.csv", rows, ["x", "y", "t", "p"])
        events = CsvAdapter().load(tmp_path / "ev.csv")
        assert len(events) == 5
        assert all(isinstance(e, Event) for e in events)

    def test_sorted_output(self, tmp_path):
        rows = [{"x": 1, "y": 0, "t": 3000, "p": 1},
                {"x": 0, "y": 0, "t": 1000, "p": 1},
                {"x": 2, "y": 0, "t": 2000, "p": 1}]
        _write_csv(tmp_path / "ev.csv", rows, ["x", "y", "t", "p"])
        events = CsvAdapter().load(tmp_path / "ev.csv")
        ts = [e.t_us for e in events]
        assert ts == sorted(ts)

    def test_time_unit_ms(self, tmp_path):
        rows = [{"x": 10, "y": 20, "t": 1.5, "p": 1}]
        _write_csv(tmp_path / "ev.csv", rows, ["x", "y", "t", "p"])
        events = CsvAdapter(time_unit="ms").load(tmp_path / "ev.csv")
        assert events[0].t_us == 1500

    def test_time_unit_s(self, tmp_path):
        rows = [{"x": 10, "y": 20, "t": 0.001, "p": 1}]
        _write_csv(tmp_path / "ev.csv", rows, ["x", "y", "t", "p"])
        events = CsvAdapter(time_unit="s").load(tmp_path / "ev.csv")
        assert events[0].t_us == 1000

    def test_polarity_normalisation(self, tmp_path):
        rows = [{"x": 0, "y": 0, "t": 0, "p": 0},   # 0 → -1
                {"x": 1, "y": 0, "t": 1, "p": 1},   # 1 → +1
                {"x": 2, "y": 0, "t": 2, "p": -1}]  # -1 → -1
        _write_csv(tmp_path / "ev.csv", rows, ["x", "y", "t", "p"])
        events = CsvAdapter().load(tmp_path / "ev.csv")
        assert events[0].polarity == -1
        assert events[1].polarity == +1
        assert events[2].polarity == -1

    def test_custom_column_names(self, tmp_path):
        rows = [{"px": 5, "py": 6, "ts": 100, "pol": 1}]
        _write_csv(tmp_path / "ev.csv", rows, ["px", "py", "ts", "pol"])
        events = CsvAdapter(x_col="px", y_col="py", t_col="ts", p_col="pol").load(tmp_path / "ev.csv")
        assert events[0].x == 5
        assert events[0].y == 6
        assert events[0].t_us == 100

    def test_pixel_coordinates_preserved(self, tmp_path):
        rows = [{"x": 173, "y": 130, "t": 500000, "p": 1}]
        _write_csv(tmp_path / "ev.csv", rows, ["x", "y", "t", "p"])
        e = CsvAdapter().load(tmp_path / "ev.csv")[0]
        assert e.x == 173
        assert e.y == 130

    def test_invalid_time_unit(self):
        with pytest.raises(ValueError, match="time_unit"):
            CsvAdapter(time_unit="min")


# ── TestNumpyAdapter ──────────────────────────────────────────────────────────

class TestNumpyAdapter:
    def _make_array(self, n=5) -> np.ndarray:
        arr = np.zeros((n, 4), dtype=np.float64)
        for i in range(n):
            arr[i] = [100 + i, 50, i * 1000, 1]
        return arr

    def test_load_npy_plain(self, tmp_path):
        arr = self._make_array(6)
        np.save(tmp_path / "ev.npy", arr)
        events = NumpyAdapter().load(tmp_path / "ev.npy")
        assert len(events) == 6

    def test_sorted_output(self, tmp_path):
        arr = np.array([[5, 0, 5000, 1], [3, 0, 3000, 1], [1, 0, 1000, 1]], dtype=float)
        np.save(tmp_path / "ev.npy", arr)
        events = NumpyAdapter().load(tmp_path / "ev.npy")
        ts = [e.t_us for e in events]
        assert ts == sorted(ts)

    def test_time_unit_ms(self, tmp_path):
        arr = np.array([[10, 20, 2.5, 1]], dtype=float)
        np.save(tmp_path / "ev.npy", arr)
        events = NumpyAdapter(time_unit="ms").load(tmp_path / "ev.npy")
        assert events[0].t_us == 2500

    def test_load_npz_events_key(self, tmp_path):
        arr = self._make_array(4)
        np.savez(tmp_path / "ev.npz", events=arr)
        events = NumpyAdapter().load(tmp_path / "ev.npz")
        assert len(events) == 4

    def test_load_npz_separate_keys(self, tmp_path):
        n = 3
        np.savez(tmp_path / "ev.npz",
                 x=np.array([10, 11, 12]),
                 y=np.array([50, 50, 50]),
                 t=np.array([0, 1000, 2000]),
                 p=np.array([1, 1, 1]))
        events = NumpyAdapter(npz_key=None).load(tmp_path / "ev.npz")
        assert len(events) == n

    def test_structured_array(self, tmp_path):
        dt = np.dtype([("x", np.int16), ("y", np.int16), ("t", np.int64), ("p", np.int8)])
        arr = np.array([(100, 50, 5000, 1), (101, 51, 6000, -1)], dtype=dt)
        np.save(tmp_path / "ev.npy", arr)
        events = NumpyAdapter().load(tmp_path / "ev.npy")
        assert len(events) == 2
        assert events[0].x == 100
        assert events[1].polarity == -1

    def test_polarity_normalisation(self, tmp_path):
        arr = np.array([[0, 0, 0, 0], [1, 0, 1000, 1]], dtype=float)
        np.save(tmp_path / "ev.npy", arr)
        events = NumpyAdapter().load(tmp_path / "ev.npy")
        assert events[0].polarity == -1
        assert events[1].polarity == +1

    def test_invalid_shape_raises(self, tmp_path):
        arr = np.zeros((5, 2))  # too few columns
        np.save(tmp_path / "ev.npy", arr)
        with pytest.raises(ValueError, match="shape"):
            NumpyAdapter().load(tmp_path / "ev.npy")


# ── TestTxtAdapter ────────────────────────────────────────────────────────────

class TestTxtAdapter:
    def _write(self, path: Path, lines: list[str]) -> None:
        path.write_text("\n".join(lines), encoding="utf-8")

    def test_load_basic(self, tmp_path):
        self._write(tmp_path / "ev.txt",
                    ["100 50 0 1", "101 51 1000 1", "102 52 2000 1"])
        events = TxtAdapter().load(tmp_path / "ev.txt")
        assert len(events) == 3

    def test_comments_skipped(self, tmp_path):
        self._write(tmp_path / "ev.txt",
                    ["# header comment", "100 50 0 1", "# another comment", "101 51 1000 1"])
        events = TxtAdapter().load(tmp_path / "ev.txt")
        assert len(events) == 2

    def test_blank_lines_skipped(self, tmp_path):
        self._write(tmp_path / "ev.txt", ["", "100 50 0 1", "", "101 51 1000 1", ""])
        events = TxtAdapter().load(tmp_path / "ev.txt")
        assert len(events) == 2

    def test_sorted_output(self, tmp_path):
        self._write(tmp_path / "ev.txt", ["100 50 3000 1", "100 50 1000 1", "100 50 2000 1"])
        events = TxtAdapter().load(tmp_path / "ev.txt")
        assert [e.t_us for e in events] == [1000, 2000, 3000]

    def test_custom_col_order(self, tmp_path):
        # order: t x y p
        self._write(tmp_path / "ev.txt", ["500 99 77 1"])
        events = TxtAdapter(col_order=(1, 2, 0, 3)).load(tmp_path / "ev.txt")
        assert events[0].x == 99
        assert events[0].y == 77
        assert events[0].t_us == 500

    def test_time_unit_ms(self, tmp_path):
        self._write(tmp_path / "ev.txt", ["10 20 1.5 1"])
        events = TxtAdapter(time_unit="ms").load(tmp_path / "ev.txt")
        assert events[0].t_us == 1500

    def test_polarity_normalisation(self, tmp_path):
        self._write(tmp_path / "ev.txt", ["0 0 0 0", "1 0 1000 1"])
        events = TxtAdapter().load(tmp_path / "ev.txt")
        assert events[0].polarity == -1
        assert events[1].polarity == +1


# ── TestAutoDetect ────────────────────────────────────────────────────────────

class TestAutoDetect:
    def test_csv_extension(self):
        adapter = auto_detect("events.csv")
        assert isinstance(adapter, CsvAdapter)

    def test_npy_extension(self):
        adapter = auto_detect("events.npy")
        assert isinstance(adapter, NumpyAdapter)

    def test_npz_extension(self):
        adapter = auto_detect("events.npz")
        assert isinstance(adapter, NumpyAdapter)

    def test_txt_extension(self):
        adapter = auto_detect("events.txt")
        assert isinstance(adapter, TxtAdapter)

    def test_dat_extension(self):
        adapter = auto_detect("events.dat")
        assert isinstance(adapter, TxtAdapter)

    def test_unknown_extension_raises(self):
        with pytest.raises(ValueError, match="auto-detect"):
            auto_detect("events.aedat")

    def test_kwargs_forwarded(self):
        adapter = auto_detect("events.csv", time_unit="ms")
        assert isinstance(adapter, CsvAdapter)
        assert adapter._scale == 1000.0


# ── TestDatasetConvert (CLI end-to-end) ───────────────────────────────────────

class TestDatasetConvert:
    def _make_csv(self, path: Path, n: int = 20) -> None:
        with open(path, "w", newline="") as f:
            f.write("x,y,t,p\n")
            for i in range(n):
                f.write(f"{100 + i},50,{i * 10000},1\n")

    def _run(self, *args) -> subprocess.CompletedProcess:
        cmd = [PYTHON, "-m", "sdk.python.spatial_asset_v3.demos.dataset_convert"] + list(args)
        return subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)

    def test_basic_csv_to_bundle(self, tmp_path):
        csv_path = tmp_path / "ev.csv"
        out_dir  = tmp_path / "bundle"
        self._make_csv(csv_path)
        r = self._run("--input", str(csv_path), "--out", str(out_dir))
        assert r.returncode == 0, f"CLI failed:\n{r.stderr}"
        assert (out_dir / "bundle_manifest.json").exists()

    def test_bundle_manifest_schema_valid(self, tmp_path):
        csv_path = tmp_path / "ev.csv"
        out_dir  = tmp_path / "bundle"
        self._make_csv(csv_path)
        self._run("--input", str(csv_path), "--out", str(out_dir))
        manifest = json.loads((out_dir / "bundle_manifest.json").read_bytes())
        assert manifest["schema_valid"] is True, \
            f"schema_errors: {manifest.get('schema_errors')}"

    def test_bundle_has_event_frame_2d_assets(self, tmp_path):
        csv_path = tmp_path / "ev.csv"
        out_dir  = tmp_path / "bundle"
        self._make_csv(csv_path, n=30)
        self._run("--input", str(csv_path), "--out", str(out_dir),
                  "--window-us", "50000")
        manifest = json.loads((out_dir / "bundle_manifest.json").read_bytes())
        assert len(manifest["assets"]) >= 1
        kinds = {a["kind"] for a in manifest["assets"]}
        assert "event-frame-2d" in kinds

    def test_npy_input(self, tmp_path):
        arr = np.array([[100 + i, 50, i * 10000, 1] for i in range(15)], dtype=float)
        npy_path = tmp_path / "ev.npy"
        np.save(npy_path, arr)
        out_dir = tmp_path / "bundle"
        r = self._run("--input", str(npy_path), "--format", "npy", "--out", str(out_dir))
        assert r.returncode == 0, f"CLI failed:\n{r.stderr}"
        manifest = json.loads((out_dir / "bundle_manifest.json").read_bytes())
        assert manifest["schema_valid"] is True

    def test_custom_resolution_and_intrinsics(self, tmp_path):
        csv_path = tmp_path / "ev.csv"
        out_dir  = tmp_path / "bundle"
        self._make_csv(csv_path)
        r = self._run(
            "--input", str(csv_path), "--out", str(out_dir),
            "--resolution", "640", "480",
            "--intrinsics", "320", "320", "320", "240",
        )
        assert r.returncode == 0, f"CLI failed:\n{r.stderr}"
        # Check that the sensor resolution in the first asset matches
        manifest = json.loads((out_dir / "bundle_manifest.json").read_bytes())
        first_asset = json.loads((out_dir / manifest["assets"][0]["file"]).read_bytes())
        assert first_asset["sensor"]["resolution"] == [640, 480]

    def test_layer_field_is_2(self, tmp_path):
        csv_path = tmp_path / "ev.csv"
        out_dir  = tmp_path / "bundle"
        self._make_csv(csv_path)
        self._run("--input", str(csv_path), "--out", str(out_dir))
        manifest = json.loads((out_dir / "bundle_manifest.json").read_bytes())
        assert manifest.get("layer") == 2


# ── TestSampleDataset ─────────────────────────────────────────────────────────

class TestSampleDataset:
    SAMPLE_CSV = SAMPLES / "sample_events.csv"

    def test_sample_file_exists(self):
        assert self.SAMPLE_CSV.exists(), f"sample_events.csv missing: {self.SAMPLE_CSV}"

    def test_sample_loads_correctly(self):
        events = CsvAdapter().load(self.SAMPLE_CSV)
        assert len(events) == 101
        assert events[0].t_us == 0
        assert events[-1].t_us == 1_000_000
        assert all(e.polarity == 1 for e in events)
        assert all(e.y == 130 for e in events)

    def test_sample_x_range(self):
        events = CsvAdapter().load(self.SAMPLE_CSV)
        xs = [e.x for e in events]
        assert min(xs) >= 130
        assert max(xs) <= 210

    def test_sample_converts_to_valid_bundle(self, tmp_path):
        events = CsvAdapter().load(self.SAMPLE_CSV)

        from sdk.python.spatial_asset_v3._config import CameraSpec, Intrinsics
        from sdk.python.spatial_asset_v3.event.accumulator import accumulate
        from sdk.python.spatial_asset_v3._validator import validate_bundle
        import numpy as np

        cam = CameraSpec(
            id="cam0",
            resolution=(346, 260),
            intrinsics=Intrinsics(fx=200.0, fy=200.0, cx=173.0, cy=130.0),
            T_world_cam=np.eye(4),
        )
        frames = accumulate(events, cam, window_us=50_000)
        for f in frames:
            f.pop("_frame", None)

        errors = validate_bundle(frames)
        assert errors == [], f"Schema errors: {errors}"

    def test_sample_produces_multiple_frames(self, tmp_path):
        events = CsvAdapter().load(self.SAMPLE_CSV)

        from sdk.python.spatial_asset_v3._config import CameraSpec, Intrinsics
        from sdk.python.spatial_asset_v3.event.accumulator import accumulate
        import numpy as np

        cam = CameraSpec(
            id="cam0",
            resolution=(346, 260),
            intrinsics=Intrinsics(fx=200.0, fy=200.0, cx=173.0, cy=130.0),
            T_world_cam=np.eye(4),
        )
        frames = accumulate(events, cam, window_us=50_000)
        # 1s / 50ms = 20 frames expected
        assert len(frames) >= 15
