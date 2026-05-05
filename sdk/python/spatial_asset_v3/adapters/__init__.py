"""Layer 2 dataset adapters — convert public event-camera datasets to v3 Event lists."""
from .base import DatasetAdapter
from .csv_adapter import CsvAdapter
from .numpy_adapter import NumpyAdapter
from .txt_adapter import TxtAdapter
from .auto import auto_detect

__all__ = ["DatasetAdapter", "CsvAdapter", "NumpyAdapter", "TxtAdapter", "auto_detect"]
