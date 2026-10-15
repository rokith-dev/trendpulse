
"""TrendPulse interactive e-commerce analytics dashboard."""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
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
st.caption("MongoDB MapReduce • Shopping Funnel • Event Analytics")

@st.cache_data(ttl=60)
def load_event_counts():
    """Read the latest MapReduce event counts from MongoDB."""
    with MongoClient(
        MONGODB_URI, serverSelectionTimeoutMS=5000
    ) as client:
        client.admin.command("ping")
        collection = client[DATABASE_NAME][OUTPUT_COLLECTION]
        return {
            item["_id"]: int(item["value"])
            for item in collection.find({})
        }

try:
    counts = load_event_counts()

    views = counts.get("view", 0)
    carts = counts.get("cart", 0)
    purchases = counts.get("purchase", 0)
    total = sum(counts.values())

    st.success("Connected to MongoDB successfully.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Events", f"{total:,}")
    col2.metric("Product Views", f"{views:,}")
    col3.metric("Cart Events", f"{carts:,}")
    col4.metric("Purchase Events", f"{purchases:,}")

    st.divider()
    st.header("Event Type Analysis")

    if counts:
        chart_data = pd.DataFrame({
            "Event Type": list(counts.keys()),
            "Number of Events": list(counts.values()),
        }).sort_values("Number of Events", ascending=False)

        st.bar_chart(
            chart_data,
            x="Event Type",
            y="Number of Events",
        )

        st.dataframe(chart_data, hide_index=True, use_container_width=True)
    else:
        st.warning("No MapReduce results found. Run the analysis first.")

    st.divider()
    st.header("Shopping Funnel")

    funnel_data = pd.DataFrame({
        "Shopping Activity": [
            "Product Views",
            "Cart Events",
            "Purchase Events",
        ],
        "Event Count": [views, carts, purchases],
    })

    st.bar_chart(
        funnel_data,
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
        "These ratios compare event counts. They are not unique-customer "
        "conversion rates, because a customer can generate multiple events."
    )

    st.caption(
        "Data source: MongoDB trendpulse.event_type_counts. "
        "Refresh the page after rerunning MapReduce to see updated results."
    )

except Exception as exc:
    st.error("Could not load data from MongoDB.")
    st.code(str(exc))
    st.info(
        "Check that MongoDB Server is running and that the MapReduce "
        "analysis has created the event_type_counts collection."
    )
