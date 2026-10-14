
from pathlib import Path
from collections import Counter
import pandas as pd

DATA_DIR = Path("data/raw")
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

        # Count missing values in each column
        for column, count in chunk.isna().sum().items():
            missing_counts[column] += int(count)

        # Count each event type
        event_counts.update(
            chunk["event_type"].fillna("<MISSING>").astype(str)
        )

        # Check whether price is numeric and non-negative
        prices = pd.to_numeric(chunk["price"], errors="coerce")
        invalid_price_count += int(
            (prices.isna() | (prices < 0)).sum()
        )

        # Check event_time parsing
        parsed_times = pd.to_datetime(
            chunk["event_time"], errors="coerce", utc=True
        )
        invalid_time_count += int(parsed_times.isna().sum())

    print(f"Rows processed: {file_rows:,}")

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
