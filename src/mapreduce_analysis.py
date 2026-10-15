
"""MongoDB MapReduce analysis for TrendPulse."""

from collections import Counter
from collections.abc import Iterable

from bson.code import Code
from pymongo import MongoClient

MONGODB_URI = "mongodb://localhost:27017"
DATABASE_NAME = "trendpulse"
INPUT_COLLECTION = "events"
OUTPUT_COLLECTION = "event_type_counts"


def map_terms(
    records: Iterable[dict], field: str = "term"
) -> Counter[str]:
    """Map records to term counts."""
    return Counter(
        str(record[field])
        for record in records
        if field in record
    )


def reduce_counts(*counters: Counter[str]) -> Counter[str]:
    """Reduce multiple term-count mappings into one."""
    result: Counter[str] = Counter()
    for counter in counters:
        result.update(counter)
    return result


def run_event_type_mapreduce() -> list[dict]:
    """Run MongoDB MapReduce to count e-commerce event types."""
    map_function = Code("""
        function () {
            emit(this.event_type, 1);
        }
    """)

    reduce_function = Code("""
        function (key, values) {
            return Array.sum(values);
        }
    """)

    with MongoClient(
        MONGODB_URI, serverSelectionTimeoutMS=5000
    ) as client:
        client.admin.command("ping")
        database = client[DATABASE_NAME]

        database.command(
            "mapReduce",
            INPUT_COLLECTION,
            map=map_function,
            reduce=reduce_function,
            out={"replace": OUTPUT_COLLECTION},
        )

        results = list(
            database[OUTPUT_COLLECTION].find(
                {}, {"_id": 1, "value": 1}
            ).sort("_id", 1)
        )

        return results


def main() -> None:
    """Run the event-type analysis and display its results."""
    results = run_event_type_mapreduce()

    print("\nTrendPulse: Event Type Analysis")
    print("-" * 35)

    total = 0
    for result in results:
        event_type = result["_id"]
        count = int(result["value"])
        total += count
        print(f"{event_type}: {count:,}")

    print("-" * 35)
    print(f"Total events analyzed: {total:,}")
    print(f"Results saved to: {OUTPUT_COLLECTION}")


if __name__ == "__main__":
    main()
