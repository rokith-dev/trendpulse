"""Data ingestion entry points."""

import csv
from pathlib import Path


def read_csv(path: str | Path) -> list[dict[str, str]]:
    """Read a CSV file into a list of dictionaries."""
    with Path(path).open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))
