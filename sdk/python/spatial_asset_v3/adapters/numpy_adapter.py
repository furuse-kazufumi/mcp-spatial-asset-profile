"""NumPy adapter — reads event arrays from .npy / .npz files.

Supported array formats:
  - Shape (N, 4) with column order [x, y, t, p]  (default)
  - Structured array with fields 'x', 'y', 't'/'timestamp', 'p'/'polarity'
  - .npz with key 'events' (array shape (N,4)) or 'x','y','t','p' separate keys
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .base import DatasetAdapter, TIME_SCALES
from ..event.generator import Event

_FIELD_ALIASES = {
    "x": ("x", "x_px"),
    "y": ("y", "y_px"),
    "t": ("t", "timestamp", "t_us", "ts"),
    "p": ("p", "polarity", "pol"),
}


class NumpyAdapter(DatasetAdapter):
    """Read events from a NumPy .npy or .npz file.

    Args:
        col_order:  Column indices [x, y, t, p] for plain (N,4) arrays.
        time_unit:  Unit of the time column ('us', 'ms', 's', 'ns').
        npz_key:    Key to use when loading a .npz file (default 'events').
                    If None, will also try 'x','y','t','p' separate keys.
    """

    name = "npy"

    def __init__(
        self,
        col_order: tuple[int, int, int, int] = (0, 1, 2, 3),
        time_unit: str = "us",
        npz_key: str | None = "events",
    ) -> None:
        if time_unit not in TIME_SCALES:
            raise ValueError(f"time_unit must be one of {list(TIME_SCALES)}, got {time_unit!r}")
        self._col = col_order
        self._scale = TIME_SCALES[time_unit]
        self._npz_key = npz_key

    def load(self, path: str | Path) -> list[Event]:
        path = Path(path)
        if path.suffix == ".npz":
            arr = self._load_npz(path)
        else:
            arr = np.load(path, allow_pickle=False)

        return self._array_to_events(arr)

    def _load_npz(self, path: Path) -> np.ndarray:
        data = np.load(path, allow_pickle=False)
        if self._npz_key and self._npz_key in data:
            return data[self._npz_key]
        # try separate x/y/t/p keys
        for t_key in ("t", "timestamp", "t_us"):
            if "x" in data and "y" in data and t_key in data:
                p_key = next((k for k in ("p", "polarity", "pol") if k in data), None)
                p_arr = data[p_key] if p_key else np.ones(len(data["x"]), dtype=np.int8)
                return np.column_stack([data["x"], data["y"], data[t_key], p_arr])
        raise KeyError(f"Cannot find events in {path}. Keys: {list(data.keys())}")

    def _array_to_events(self, arr: np.ndarray) -> list[Event]:
        if arr.dtype.names:
            return self._structured_to_events(arr)
        if arr.ndim != 2 or arr.shape[1] < 4:
            raise ValueError(f"Expected shape (N,4+), got {arr.shape}")
        xi, yi, ti, pi = self._col
        events = [
            Event(
                x=int(row[xi]),
                y=int(row[yi]),
                t_us=self._to_us(float(row[ti]), self._scale),
                polarity=self._norm_polarity(int(row[pi])),
            )
            for row in arr
        ]
        events.sort(key=lambda e: e.t_us)
        return events

    def _structured_to_events(self, arr: np.ndarray) -> list[Event]:
        names = arr.dtype.names

        def _find(aliases: tuple) -> str:
            for a in aliases:
                if a in names:
                    return a
            raise KeyError(f"None of {aliases} found in structured array fields {names}")

        xf = _find(_FIELD_ALIASES["x"])
        yf = _find(_FIELD_ALIASES["y"])
        tf = _find(_FIELD_ALIASES["t"])
        pf = _find(_FIELD_ALIASES["p"])

        events = [
            Event(
                x=int(r[xf]),
                y=int(r[yf]),
                t_us=self._to_us(float(r[tf]), self._scale),
                polarity=self._norm_polarity(int(r[pf])),
            )
            for r in arr
        ]
        events.sort(key=lambda e: e.t_us)
        return events
