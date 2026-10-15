
"""Chart output helpers for TrendPulse."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from pymongo import MongoClient


MONGODB_URI = "mongodb://localhost:27017"
DATABASE_NAME = "trendpulse"
OUTPUT_COLLECTION = "event_type_counts"


def chart_output_path(
    name: str, output_dir: str | Path = "results/charts"
) -> Path:
    """Build a path for a generated chart."""
    return Path(output_dir) / f"{name}.png"


def create_event_type_chart() -> Path:
    """Create a bar chart from MongoDB MapReduce results."""
    with MongoClient(
        MONGODB_URI, serverSelectionTimeoutMS=5000
    ) as client:
        client.admin.command("ping")
        collection = client[DATABASE_NAME][OUTPUT_COLLECTION]

        results = list(
            collection.find({}).sort("_id", 1)
        )

    if not results:
        raise ValueError(
            "No MapReduce results found. Run the MapReduce analysis first."
        )

    event_types = [item["_id"] for item in results]
    counts = [int(item["value"]) for item in results]

    output_path = chart_output_path("event_type_counts")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(9, 5))
    plt.bar(event_types, counts)
    plt.title("TrendPulse: E-commerce Event Counts")
    plt.xlabel("Event Type")
    plt.ylabel("Number of Events")
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


if __name__ == "__main__":
    path = create_event_type_chart()
    print(f"Chart saved successfully: {path}")
