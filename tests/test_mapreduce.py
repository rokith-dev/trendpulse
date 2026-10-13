"""Tests for MapReduce analysis."""

from collections import Counter

from src.mapreduce_analysis import map_terms, reduce_counts


def test_map_terms_counts_values() -> None:
    records = [{"term": "python"}, {"term": "python"}, {"term": "data"}]
    assert map_terms(records) == Counter({"python": 2, "data": 1})


def test_reduce_counts_combines_counters() -> None:
    assert reduce_counts(Counter({"python": 1}), Counter({"python": 2})) == Counter({"python": 3})
