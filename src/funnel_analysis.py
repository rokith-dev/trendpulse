
"""Shopping funnel analysis for TrendPulse."""

from pymongo import MongoClient

MONGODB_URI = "mongodb://localhost:27017"
DATABASE_NAME = "trendpulse"
OUTPUT_COLLECTION = "event_type_counts"


def conversion_rates(stages: list[int]) -> list[float]:
    """Calculate each stage as a share of the first stage."""
    if not stages or stages[0] == 0:
        return []

    return [count / stages[0] for count in stages]


def load_event_counts() -> dict[str, int]:
    """Load event counts produced by MongoDB MapReduce."""
    with MongoClient(
        MONGODB_URI, serverSelectionTimeoutMS=5000
    ) as client:
        client.admin.command("ping")
        collection = client[DATABASE_NAME][OUTPUT_COLLECTION]

        return {
            document["_id"]: int(document["value"])
            for document in collection.find({})
        }


def analyze_funnel() -> None:
    """Display shopping event counts and event-based rates."""
    counts = load_event_counts()

    views = counts.get("view", 0)
    carts = counts.get("cart", 0)
    purchases = counts.get("purchase", 0)

    print("\nTrendPulse: Shopping Funnel Analysis")
    print("-" * 40)
    print(f"Product views: {views:,}")
    print(f"Cart events:   {carts:,}")
    print(f"Purchase events: {purchases:,}")

    stages = [views, carts, purchases]
    shares = conversion_rates(stages)

    if shares:
        print("\nEach event count as a share of views:")
        print(f"Views:     {shares[0]:.2%}")
        print(f"Cart:      {shares[1]:.2%}")
        print(f"Purchases: {shares[2]:.2%}")

    print("\nEvent-count comparison rates:")
    if views:
        print(f"View-to-cart: {carts / views:.2%}")
        print(f"View-to-purchase: {purchases / views:.2%}")
    else:
        print("View-based rates unavailable: no view events.")

    if carts:
        print(f"Cart-to-purchase: {purchases / carts:.2%}")
    else:
        print("Cart-to-purchase rate unavailable: no cart events.")

    print(
        "\nNote: These are event-count ratios, not unique-customer "
        "conversion rates."
    )


if __name__ == "__main__":
    analyze_funnel()
