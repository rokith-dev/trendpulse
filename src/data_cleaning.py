
"""Data cleaning helpers for TrendPulse."""

from datetime import datetime, timezone
from typing import Any


def drop_empty_rows(rows: list[dict]) -> list[dict]:
    """Remove rows where every value is missing or empty."""
    return [
        row
        for row in rows
        if any(value not in (None, "") for value in row.values())
    ]


def parse_event_time(value: Any) -> datetime | None:
    """Parse the dataset's UTC timestamp into a timezone-aware datetime."""
    if not isinstance(value, str) or not value.strip():
        return None

    try:
        return datetime.strptime(
            value.strip(), "%Y-%m-%d %H:%M:%S UTC"
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def parse_price(value: Any) -> float | None:
    """Return a non-negative numeric price, or None if invalid."""
    try:
        price = float(value)
        if price < 0:
            return None
        return price
    except (TypeError, ValueError):
        return None


def parse_identifier(value: Any) -> int | None:
    """Convert a valid identifier to an integer."""
    if value in (None, ""):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def clean_record(row: dict[str, Any]) -> dict[str, Any]:
    """Clean one e-commerce event while preserving useful information."""
    record = dict(row)

    record["event_time"] = parse_event_time(record.get("event_time"))
    record["price"] = parse_price(record.get("price"))

    for field in ("product_id", "category_id", "user_id"):
        record[field] = parse_identifier(record.get(field))

    for field in ("brand", "category_code", "user_session"):
        if record.get(field) == "":
            record[field] = None

    return record
