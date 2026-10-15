
"""Batch-based, duplicate-safe CSV ingestion for TrendPulse."""

import argparse
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError

DATA_DIR = Path("data/raw")
MONGODB_URI = "mongodb://localhost:27017"
DATABASE_NAME = "trendpulse"
COLLECTION_NAME = "events"
BATCH_SIZE = 1_000


def clean_record(row: dict[str, str]) -> dict:
    """Convert CSV values to appropriate MongoDB types."""
    record = dict(row)

    timestamp = record.get("event_time", "")
    try:
        record["event_time"] = datetime.strptime(
            timestamp, "%Y-%m-%d %H:%M:%S UTC"
        ).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError, AttributeError):
        record["event_time"] = None

    try:
        price = float(record["price"])
        record["price"] = price if price >= 0 else None
    except (ValueError, TypeError, KeyError):
        record["price"] = None

    for field in ("product_id", "category_id", "user_id"):
        value = record.get(field, "")
        try:
            record[field] = int(value) if value else None
        except (ValueError, TypeError):
            record[field] = None

    for field in ("category_code", "brand", "user_session"):
        if not record.get(field):
            record[field] = None

    return record


def make_source_id(filename: str, row_number: int) -> str:
    """Create a stable identifier for a row in a source CSV."""
    source_key = f"{filename}:{row_number}"
    return hashlib.sha256(source_key.encode("utf-8")).hexdigest()


def ingest_csv(
    csv_path: Path,
    collection,
    limit: int | None = None,
    batch_size: int = BATCH_SIZE,
) -> int:
    """Upsert CSV records in batches without duplicating source rows."""
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    processed = 0
    batch = []

    with csv_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row_number, row in enumerate(reader, start=1):
            record = clean_record(row)
            record["_source_id"] = make_source_id(csv_path.name, row_number)

            batch.append(
                UpdateOne(
                    {"_source_id": record["_source_id"]},
                    {"$setOnInsert": record},
                    upsert=True,
                )
            )

            if len(batch) >= batch_size:
                collection.bulk_write(batch, ordered=False)
                processed += len(batch)
                print(
                    f"Processed {processed:,} source rows "
                    f"from {csv_path.name}"
                )
                batch.clear()

            if limit is not None and processed + len(batch) >= limit:
                break

        if batch:
            if limit is not None:
                batch = batch[: max(0, limit - processed)]
            if batch:
                collection.bulk_write(batch, ordered=False)
                processed += len(batch)

    return processed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest TrendPulse CSV records into MongoDB."
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--file", type=str, default=None)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
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

        # Existing documents receive the same unique index.
        collection.create_index("_source_id", unique=True, sparse=True)

        for path in files:
            print(f"\nProcessing {path.name}")
            processed = ingest_csv(
                path,
                collection,
                limit=args.limit,
                batch_size=args.batch_size,
            )
            print(f"Processed {processed:,} source rows from {path.name}")

        print(
            "\nTotal documents in collection: "
            f"{collection.count_documents({}):,}"
        )


if __name__ == "__main__":
    main()
