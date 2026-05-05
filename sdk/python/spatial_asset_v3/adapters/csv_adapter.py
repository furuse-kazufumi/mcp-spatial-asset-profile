"""CSV adapter — reads event CSV files with configurable column names.

Supported column layouts (configurable via constructor):
  Default:    x, y, t, p
  N-Caltech:  x, y, timestamp, polarity   (with --time-unit us)
  Custom:     any column names via x_col/y_col/t_col/p_col parameters
"""
from __future__ import annotations

import csv
from pathlib import Path

from .base import DatasetAdapter, TIME_SCALES
from ..event.generator import Event


class CsvAdapter(DatasetAdapter):
    """Read events from a CSV file.

    Args:
        x_col:      Column name for x pixel coordinate.
        y_col:      Column name for y pixel coordinate.
        t_col:      Column name for timestamp.
        p_col:      Column name for polarity.
        time_unit:  Unit of the timestamp column ('us', 'ms', 's', 'ns').
        delimiter:  CSV field separator (default ',').
        skip_rows:  Number of non-header rows to skip at the start.
    """

    name = "csv"

    def __init__(
        self,
        x_col: str = "x",
        y_col: str = "y",
        t_col: str = "t",
        p_col: str = "p",
        time_unit: str = "us",
        delimiter: str = ",",
        skip_rows: int = 0,
    ) -> None:
        if time_unit not in TIME_SCALES:
            raise ValueError(f"time_unit must be one of {list(TIME_SCALES)}, got {time_unit!r}")
        self._x = x_col
        self._y = y_col
        self._t = t_col
        self._p = p_col
        self._scale = TIME_SCALES[time_unit]
        self._delim = delimiter
        self._skip = skip_rows

    def load(self, path: str | Path) -> list[Event]:
        events: list[Event] = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=self._delim)
            for i, row in enumerate(reader):
                if i < self._skip:
                    continue
                x = int(row[self._x])
                y = int(row[self._y])
                t_us = self._to_us(float(row[self._t]), self._scale)
                p = self._norm_polarity(int(float(row[self._p])))
                events.append(Event(x=x, y=y, t_us=t_us, polarity=p))
        events.sort(key=lambda e: e.t_us)
        return events
