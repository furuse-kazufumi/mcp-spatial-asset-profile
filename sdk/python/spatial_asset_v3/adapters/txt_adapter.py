"""Text adapter — reads whitespace-separated event files.

Format (one event per line, no header):
    <x> <y> <t> <p>

Common in: N-MNIST, N-Caltech101, and many DVS recording tools.
Lines starting with '#' are treated as comments and skipped.
"""
from __future__ import annotations

from pathlib import Path

from .base import DatasetAdapter, TIME_SCALES
from ..event.generator import Event


class TxtAdapter(DatasetAdapter):
    """Read events from a whitespace-separated text file (no header).

    Args:
        col_order:  Column indices (0-based) for [x, y, t, p] within each line.
        time_unit:  Unit of the time column ('us', 'ms', 's', 'ns').
        delimiter:  Field separator (default None = any whitespace).
        comment:    Line prefix to skip (default '#').
    """

    name = "txt"

    def __init__(
        self,
        col_order: tuple[int, int, int, int] = (0, 1, 2, 3),
        time_unit: str = "us",
        delimiter: str | None = None,
        comment: str = "#",
    ) -> None:
        if time_unit not in TIME_SCALES:
            raise ValueError(f"time_unit must be one of {list(TIME_SCALES)}, got {time_unit!r}")
        self._col = col_order
        self._scale = TIME_SCALES[time_unit]
        self._delim = delimiter
        self._comment = comment

    def load(self, path: str | Path) -> list[Event]:
        xi, yi, ti, pi = self._col
        events: list[Event] = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(self._comment):
                    continue
                parts = line.split(self._delim)
                x = int(parts[xi])
                y = int(parts[yi])
                t_us = self._to_us(float(parts[ti]), self._scale)
                p = self._norm_polarity(int(float(parts[pi])))
                events.append(Event(x=x, y=y, t_us=t_us, polarity=p))
        events.sort(key=lambda e: e.t_us)
        return events
