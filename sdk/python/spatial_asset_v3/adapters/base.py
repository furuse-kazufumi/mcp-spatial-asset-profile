"""Abstract base class for Layer 2 dataset adapters."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..event.generator import Event

# Supported time units → multiplier to convert to microseconds
TIME_SCALES: dict[str, float] = {
    "us": 1.0,
    "ms": 1_000.0,
    "s": 1_000_000.0,
    "ns": 0.001,
}


class DatasetAdapter(ABC):
    """Load events from a dataset file and return them as Event namedtuples.

    Subclasses implement `load(path) -> list[Event]`. Events must be returned
    sorted in ascending t_us order. Polarity values outside {-1, +1} are
    normalised: 0 → -1, any other non-zero → +1.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Short format identifier (e.g. 'csv', 'npy', 'txt')."""

    @abstractmethod
    def load(self, path: str | Path) -> list[Event]:
        """Load events from *path*, return sorted list of Event(x, y, t_us, polarity)."""

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _norm_polarity(p: int) -> int:
        # Normalise both 0/1 and -1/+1 encodings to {-1, +1}.
        # 0 → -1 (negative event in 0/1 datasets); negative values → -1; positive → +1.
        return -1 if p <= 0 else +1

    @staticmethod
    def _to_us(t: float, scale: float) -> int:
        return int(t * scale)
