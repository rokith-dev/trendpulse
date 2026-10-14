
"""Batch-based CSV ingestion into MongoDB for TrendPulse."""

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

from pymongo import MongoClient

DATA_DIR = Path("data/raw")
MONGODB_URI = "mongodb://localhost:27017"
DATABASE_NAME = "trendpulse"
COLLECTION_NAME = "events"

BATCH_SIZE = 1_000


def clean_record(row: dict[str, str]) -> dict:
    """Convert CSV fields into appropriate MongoDB document types."""
    record = dict(row)

    # Parse timestamps such as: 2019-10-01 00:00:00 UTC
    timestamp = record.get("event_time", "")
    try:
        record["event_time"] = datetime.strptime(
            timestamp, "%Y-%m-%d %H:%M:%S UTC"
        ).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError, AttributeError):
        record["event_time"] = None

    # Convert price to a numeric, non-negative value.
    try:
        price = float(record["price"])
        record["price"] = price if price >= 0 else None
    except (ValueError, TypeError, KeyError):
        record["price"] = None

    # Convert identifiers to integers.
    for field in ("product_id", "category_id", "user_id"):
        value = record.get(field, "")
        try:
            record[field] = int(value) if value else None
        except (ValueError, TypeError):
            record[field] = None

    # Preserve records with missing optional values.
    for field in ("category_code", "brand", "user_session"):
        if not record.get(field):
            record[field] = None

    return record


def ingest_csv(
    csv_path: Path,
    collection,
    limit: int | None = None,
    batch_size: int = BATCH_SIZE,
) -> int:
    """Read a CSV incrementally and insert documents in batches."""
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    inserted = 0
    batch = []

    with csv_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            batch.append(clean_record(row))

            # Flush each complete batch.
            if len(batch) >= batch_size:
                collection.insert_many(batch, ordered=False)
                inserted += len(batch)
                print(
                    f"Inserted {inserted:,} records "
                    f"from {csv_path.name}"
                )
                batch.clear()

            # Stop after reaching the requested limit.
            if limit is not None and inserted + len(batch) >= limit:
                break

        # Insert the remaining records, respecting the limit.
        if batch:
            remaining = batch
            if limit is not None:
                remaining = batch[: max(0, limit - inserted)]

            if remaining:
                collection.insert_many(remaining, ordered=False)
                inserted += len(remaining)

    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest TrendPulse CSV data into MongoDB."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum records to insert per CSV file.",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="CSV filename, for example 2019-Oct.csv.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Records per insertion batch (default: {BATCH_SIZE}).",
    )
    args = parser.parse_args()

    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be greater than zero")

    if args.batch_size <= 0:
        parser.error("--batch-size must be greater than zero")

    if args.file:
        files = [DATA_DIR / args.file]
    else:
        files = sorted(DATA_DIR.glob("*.csv"))

    files = [path for path in files if path.is_file()]

    if not files:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR}")

    with MongoClient(
        MONGODB_URI, serverSelectionTimeoutMS=5000
    ) as client:
        client.admin.command("ping")
        collection = client[DATABASE_NAME][COLLECTION_NAME]

        total_inserted = 0

        for path in files:
            print(f"\nProcessing {path.name}")

            count = ingest_csv(
                csv_path=path,
                collection=collection,
                limit=args.limit,
                batch_size=args.batch_size,
            )

            total_inserted += count
            print(f"Inserted {count:,} records from {path.name}")

        print(f"\nInserted during this run: {total_inserted:,}")
        print(
            "Total documents in collection: "
            f"{collection.count_documents({}):,}"
        )


if __name__ == "__main__":
    main()
