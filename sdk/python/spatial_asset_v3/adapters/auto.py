"""Auto-detect adapter from file extension."""
from __future__ import annotations

from pathlib import Path

from .base import DatasetAdapter
from .csv_adapter import CsvAdapter
from .numpy_adapter import NumpyAdapter
from .txt_adapter import TxtAdapter

_EXT_MAP: dict[str, type[DatasetAdapter]] = {
    ".csv": CsvAdapter,
    ".npy": NumpyAdapter,
    ".npz": NumpyAdapter,
    ".txt": TxtAdapter,
    ".dat": TxtAdapter,
    ".events": TxtAdapter,
}


def auto_detect(path: str | Path, **kwargs) -> DatasetAdapter:
    """Return an adapter instance inferred from *path*'s file extension.

    Extra keyword arguments are forwarded to the adapter constructor, allowing
    callers to override defaults (e.g. ``time_unit="ms"``).

    Raises:
        ValueError: if the extension is not recognised.
    """
    ext = Path(path).suffix.lower()
    cls = _EXT_MAP.get(ext)
    if cls is None:
        supported = sorted(_EXT_MAP)
        raise ValueError(
            f"Cannot auto-detect adapter for extension {ext!r}. "
            f"Supported: {supported}. Use an explicit adapter instead."
        )
    return cls(**kwargs)
