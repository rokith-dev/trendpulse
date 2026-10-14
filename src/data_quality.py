
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import json

import pandas as pd

DATA_DIR = Path("data/raw")
REPORT_DIR = Path("results/summaries")
REPORT_PATH = REPORT_DIR / "data_quality_report.json"
CHUNK_SIZE = 200_000

total_rows = 0
missing_counts = Counter()
event_counts = Counter()
invalid_price_count = 0
invalid_time_count = 0

for file_path in sorted(DATA_DIR.glob("*.csv")):
    print(f"\nInspecting: {file_path.name}")

    file_rows = 0

    for chunk in pd.read_csv(file_path, chunksize=CHUNK_SIZE):
        rows = len(chunk)
        file_rows += rows
        total_rows += rows

        # Count missing values in each column.
        for column, count in chunk.isna().sum().items():
            missing_counts[column] += int(count)

        # Count event types.
        event_counts.update(
            chunk["event_type"].fillna("<MISSING>").astype(str)
        )

        # Check for non-numeric or negative prices.
        prices = pd.to_numeric(chunk["price"], errors="coerce")
        invalid_price_count += int(
            (prices.isna() | (prices < 0)).sum()
        )

        # Check event timestamp validity.
        parsed_times = pd.to_datetime(
            chunk["event_time"], errors="coerce", utc=True
        )
        invalid_time_count += int(parsed_times.isna().sum())

    print(f"Rows processed: {file_rows:,}")

# Prepare the report.
report = {
    "project": "TrendPulse",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "total_rows_processed": total_rows,
    "missing_values_by_column": dict(sorted(missing_counts.items())),
    "event_type_counts": dict(event_counts.most_common()),
    "invalid_or_negative_prices": invalid_price_count,
    "invalid_event_timestamps": invalid_time_count,
}

# Save the report.
REPORT_DIR.mkdir(parents=True, exist_ok=True)

with REPORT_PATH.open("w", encoding="utf-8") as report_file:
    json.dump(report, report_file, indent=4)

# Display a readable summary.
print("\n" + "=" * 50)
print("DATA QUALITY REPORT")
print("=" * 50)
print(f"Total rows processed: {total_rows:,}")

print("\nMissing values by column:")
for column, count in sorted(missing_counts.items()):
    print(f"{column}: {count:,}")

print("\nEvent type counts:")
for event, count in event_counts.most_common():
    print(f"{event}: {count:,}")

print(f"\nInvalid or negative prices: {invalid_price_count:,}")
print(f"Invalid event timestamps: {invalid_time_count:,}")
print(f"\nJSON report saved to: {REPORT_PATH}")
