"""Utilities for inspecting incoming datasets."""

from pathlib import Path


def inspect_path(path: str | Path) -> dict[str, object]:
    """Return basic metadata for a dataset path."""
    dataset_path = Path(path)
    return {
        "path": str(dataset_path),
        "exists": dataset_path.exists(),
        "is_file": dataset_path.is_file(),
    }
