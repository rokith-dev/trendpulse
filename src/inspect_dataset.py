
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/raw")

for file_path in sorted(DATA_DIR.glob("*.csv")):
    print("\n" + "=" * 60)
    print(f"File: {file_path.name}")
    print(f"Size: {file_path.stat().st_size / (1024**3):.2f} GB")

    try:
        # Read only the header first
        columns = pd.read_csv(file_path, nrows=0).columns.tolist()
        print("\nColumns:")
        print(columns)

        # Read only the first five rows
        sample = pd.read_csv(file_path, nrows=5)
        print("\nFirst five rows:")
        print(sample.to_string(index=False))

    except Exception as error:
        print(f"Could not inspect {file_path.name}: {error}")
