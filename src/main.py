
"""Main application entry point for TrendPulse."""

from src.mapreduce_analysis import run_event_type_mapreduce
from src.funnel_analysis import analyze_funnel
from src.visualisation import (
    create_event_type_chart,
    create_shopping_funnel_chart,
)


def main() -> None:
    """Run the complete TrendPulse analysis pipeline."""
    print("=" * 50)
    print("TREND PULSE: E-COMMERCE BEHAVIOUR ANALYSIS")
    print("=" * 50)

    # Step 1: Run MongoDB MapReduce
    print("\n[1/3] Running MongoDB MapReduce...")
    results = run_event_type_mapreduce()

    for result in results:
        print(f"{result['_id']}: {int(result['value']):,}")

    # Step 2: Analyze the shopping funnel
    print("\n[2/3] Analyzing shopping funnel...")
    analyze_funnel()

    # Step 3: Generate charts
    print("\n[3/3] Generating visualizations...")
    event_chart = create_event_type_chart()
    print(f"Event chart saved: {event_chart}")

    funnel_chart = create_shopping_funnel_chart()
    print(f"Funnel chart saved: {funnel_chart}")

    print("\nTrendPulse analysis completed successfully!")


if __name__ == "__main__":
    main()
