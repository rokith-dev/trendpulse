
"""TrendPulse interactive e-commerce analytics dashboard."""

import pandas as pd
import streamlit as st
from pymongo import MongoClient

MONGODB_URI = "mongodb://localhost:27017"
DATABASE_NAME = "trendpulse"
OUTPUT_COLLECTION = "event_type_counts"


st.set_page_config(
    page_title="TrendPulse Analytics",
    page_icon="📊",
    layout="wide",
)

st.title("📊 TrendPulse")
st.subheader("Big Data-Driven E-Commerce Behaviour Analysis")
st.caption(
    "MongoDB MapReduce • Shopping Funnel • Product Trends"
)


@st.cache_data(ttl=60)
def load_collection(collection_name: str) -> list[dict]:
    """Load summary documents from a MongoDB collection."""
    with MongoClient(
        MONGODB_URI, serverSelectionTimeoutMS=5000
    ) as client:
        client.admin.command("ping")
        collection = client[DATABASE_NAME][collection_name]

        return list(
            collection.find({}, {"_id": 1, "value": 1})
        )


def load_event_counts() -> dict[str, int]:
    """Load event counts from MapReduce results."""
    return {
        item["_id"]: int(item["value"])
        for item in load_collection(OUTPUT_COLLECTION)
    }


try:
    counts = load_event_counts()

    views = counts.get("view", 0)
    carts = counts.get("cart", 0)
    purchases = counts.get("purchase", 0)
    total = sum(counts.values())

    st.success("Connected to MongoDB successfully.")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Events", f"{total:,}")
    col2.metric("Product Views", f"{views:,}")
    col3.metric("Cart Events", f"{carts:,}")
    col4.metric("Purchase Events", f"{purchases:,}")

    # Event type analysis
    st.divider()
    st.header("📊 Event Type Analysis")

    if counts:
        event_df = pd.DataFrame(
            [
                {"Event Type": event, "Number of Events": count}
                for event, count in counts.items()
            ]
        ).sort_values("Number of Events", ascending=False)

        st.bar_chart(
            event_df,
            x="Event Type",
            y="Number of Events",
        )
        st.dataframe(
            event_df, hide_index=True, use_container_width=True
        )
    else:
        st.warning("No MapReduce results found. Run the analysis first.")

    # Shopping funnel
    st.divider()
    st.header("🛒 Shopping Funnel")

    funnel_df = pd.DataFrame({
        "Shopping Activity": [
            "Product Views",
            "Cart Events",
            "Purchase Events",
        ],
        "Event Count": [views, carts, purchases],
    })

    st.bar_chart(
        funnel_df,
        x="Shopping Activity",
        y="Event Count",
    )

    rate1 = carts / views * 100 if views else 0
    rate2 = purchases / views * 100 if views else 0
    rate3 = purchases / carts * 100 if carts else None

    st.subheader("Event-Count Ratios")
    r1, r2, r3 = st.columns(3)
    r1.metric("Cart Events / Views", f"{rate1:.2f}%")
    r2.metric("Purchase Events / Views", f"{rate2:.2f}%")
    r3.metric(
        "Purchase Events / Cart Events",
        f"{rate3:.2f}%" if rate3 is not None else "N/A",
    )

    st.info(
        "These ratios compare event counts, not unique-customer "
        "conversion rates. Customers may generate multiple events, "
        "and purchase events do not necessarily follow cart events."
    )

    # Popular brands
    st.divider()
    st.header("🏷️ Popular Brands")

    brand_results = load_collection("brand_event_counts")
    if brand_results:
        brand_df = pd.DataFrame({
            "Brand": [item["_id"] for item in brand_results],
            "Events": [int(item["value"]) for item in brand_results],
        }).sort_values("Events", ascending=False).head(10)

        st.bar_chart(brand_df, x="Brand", y="Events")
        st.dataframe(
            brand_df, hide_index=True, use_container_width=True
        )
    else:
        st.info(
            "No brand results found. Run "
            "`python -m src.product_trends` first."
        )

    # Popular product categories
    st.divider()
    st.header("📦 Popular Product Categories")

    category_results = load_collection("category_event_counts")
    if category_results:
        category_df = pd.DataFrame({
            "Category": [
                item["_id"] for item in category_results
            ],
            "Events": [
                int(item["value"]) for item in category_results
            ],
        }).sort_values("Events", ascending=False).head(10)

        st.bar_chart(
            category_df,
            x="Category",
            y="Events",
        )
        st.dataframe(
            category_df, hide_index=True, use_container_width=True
        )
    else:
        st.info(
            "No category results found. Run "
            "`python -m src.product_trends` first."
        )

    st.divider()
    st.caption(
        "Data source: MongoDB database `trendpulse`. "
        "Brand and category counts represent events, not sales."
    )

except Exception as exc:
    st.error("Could not load data from MongoDB.")
    st.code(str(exc))
    st.info(
        "Check that MongoDB Server is running and that the MapReduce "
        "analysis has generated its output collections."
    )
