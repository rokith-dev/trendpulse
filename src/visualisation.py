"""Chart output helpers."""

from pathlib import Path


def chart_output_path(name: str, output_dir: str | Path = "results/charts") -> Path:
    """Build a path for a generated chart."""
    return Path(output_dir) / f"{name}.png"
