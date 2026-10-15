
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


def load_event_counts() -> dict[str, int]:
    """Load event counts from MongoDB MapReduce results."""
    with MongoClient(
        MONGODB_URI, serverSelectionTimeoutMS=5000
    ) as client:
        client.admin.command("ping")
        collection = client[DATABASE_NAME][OUTPUT_COLLECTION]

        return {
            item["_id"]: int(item["value"])
            for item in collection.find({})
        }


def create_event_type_chart() -> Path:
    """Create a bar chart of e-commerce event counts."""
    counts = load_event_counts()

    if not counts:
        raise ValueError(
            "No MapReduce results found. Run the MapReduce analysis first."
        )

    event_types = sorted(counts)
    values = [counts[event_type] for event_type in event_types]

    output_path = chart_output_path("event_type_counts")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(9, 5))
    bars = plt.bar(event_types, values)

    plt.title("TrendPulse: E-commerce Event Counts")
    plt.xlabel("Event Type")
    plt.ylabel("Number of Events")
    plt.grid(axis="y", linestyle="--", alpha=0.4)

    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:,}",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def create_shopping_funnel_chart() -> Path:
    """Create a chart comparing views, cart events, and purchases."""
    counts = load_event_counts()

    stages = [
        "Product Views",
        "Cart Events",
        "Purchase Events",
    ]

    values = [
        counts.get("view", 0),
        counts.get("cart", 0),
        counts.get("purchase", 0),
    ]

    if not any(values):
        raise ValueError(
            "No event counts found. Run the MapReduce analysis first."
        )

    output_path = chart_output_path("shopping_funnel")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(9, 5))
    bars = plt.bar(stages, values)

    plt.title("TrendPulse: Shopping Funnel Event Counts")
    plt.xlabel("Shopping Activity")
    plt.ylabel("Number of Events")
    plt.grid(axis="y", linestyle="--", alpha=0.4)

    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:,}",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def main() -> None:
    """Generate all TrendPulse charts."""
    event_chart = create_event_type_chart()
    print(f"Event chart saved: {event_chart}")

    funnel_chart = create_shopping_funnel_chart()
    print(f"Shopping funnel chart saved: {funnel_chart}")


if __name__ == "__main__":
    main()
