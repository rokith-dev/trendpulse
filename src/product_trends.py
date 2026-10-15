
"""Product and brand trend analysis for TrendPulse."""

from bson.code import Code
from pymongo import MongoClient

MONGODB_URI = "mongodb://localhost:27017"
DATABASE_NAME = "trendpulse"
INPUT_COLLECTION = "events"


def run_mapreduce(
    field: str,
    output_collection: str,
    limit: int = 10,
) -> list[dict]:
    """Count events grouped by a selected product field."""
    allowed_fields = {"brand", "category_code"}

    if field not in allowed_fields:
        raise ValueError(f"Unsupported field: {field}")

    if limit <= 0:
        raise ValueError("limit must be greater than zero")

    map_function = Code(f"""
        function () {{
            var value = this.{field};
            if (value !== null &&
                value !== undefined &&
                value !== "") {{
                emit(value, 1);
            }}
        }}
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
            out={"replace": output_collection},
        )

        return list(
            database[output_collection]
            .find({}, {"_id": 1, "value": 1})
            .sort("value", -1)
            .limit(limit)
        )


def main() -> None:
    """Display the most frequent brands and product categories."""
    analyses = [
        ("brand", "brand_event_counts", "Top Brands"),
        (
            "category_code",
            "category_event_counts",
            "Top Product Categories",
        ),
    ]

    for field, output_collection, title in analyses:
        print(f"\n{title}")
        print("-" * 45)

        results = run_mapreduce(field, output_collection)

        if not results:
            print("No values available.")
            continue

        for rank, item in enumerate(results, start=1):
            print(f"{rank:2}. {item['_id']}: {int(item['value']):,}")


if __name__ == "__main__":
    main()
