"""Data cleaning helpers."""


def drop_empty_rows(rows: list[dict]) -> list[dict]:
    """Remove rows that contain no populated values."""
    return [row for row in rows if any(value not in (None, "") for value in row.values())]
