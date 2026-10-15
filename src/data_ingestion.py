
"""Batch-based, duplicate-safe CSV ingestion for TrendPulse."""

import argparse
import csv
import hashlib
from pathlib import Path

from pymongo import MongoClient, UpdateOne

from data_cleaning import clean_record as clean_event_record

DATA_DIR = Path("data/raw")
MONGODB_URI = "mongodb://localhost:27017"
DATABASE_NAME = "trendpulse"
COLLECTION_NAME = "events"

BATCH_SIZE = 1_000


def clean_record(row: dict[str, str]) -> dict:
    """Use the shared data-cleaning module."""
    return clean_event_record(row)


def make_source_id(filename: str, row_number: int) -> str:
    """Create a stable ID for a row in a source CSV."""
    source_key = f"{filename}:{row_number}"
    return hashlib.sha256(source_key.encode("utf-8")).hexdigest()


def ingest_csv(
    csv_path: Path,
    collection,
    limit: int | None = None,
    batch_size: int = BATCH_SIZE,
) -> int:
    """Read a CSV incrementally and upsert records in batches."""
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    processed = 0
    batch = []

    with csv_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row_number, row in enumerate(reader, start=1):
            record = clean_record(row)
            source_id = make_source_id(csv_path.name, row_number)
            record["_source_id"] = source_id

            batch.append(
                UpdateOne(
                    {"_source_id": source_id},
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
            remaining = batch
            if limit is not None:
                remaining = batch[:max(0, limit - processed)]

            if remaining:
                collection.bulk_write(remaining, ordered=False)
                processed += len(remaining)

    return processed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest TrendPulse CSV records into MongoDB."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum source rows to process per CSV file.",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="CSV filename, such as 2019-Oct.csv.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Records per batch (default: {BATCH_SIZE}).",
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
        collection.create_index(
            "_source_id", unique=True, sparse=True
        )

        total_processed = 0

        for path in files:
            print(f"\nProcessing {path.name}")

            processed = ingest_csv(
                csv_path=path,
                collection=collection,
                limit=args.limit,
                batch_size=args.batch_size,
            )

            total_processed += processed
            print(
                f"Processed {processed:,} source rows "
                f"from {path.name}"
            )

        print(f"\nSource rows processed this run: {total_processed:,}")
        print(
            "Total documents in collection: "
            f"{collection.count_documents({}):,}"
        )


if __name__ == "__main__":
    main()
