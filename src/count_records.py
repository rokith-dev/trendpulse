
from pathlib import Path

DATA_DIR = Path("data/raw")
BUFFER_SIZE = 8 * 1024 * 1024  # 8 MB

for file_path in sorted(DATA_DIR.glob("*.csv")):
    print(f"\nCounting records in {file_path.name}...")

    line_count = 0

    with file_path.open("rb") as file:
        while True:
            chunk = file.read(BUFFER_SIZE)
            if not chunk:
                break
            line_count += chunk.count(b"\n")

    print(f"Data rows: {line_count - 1:,}")
