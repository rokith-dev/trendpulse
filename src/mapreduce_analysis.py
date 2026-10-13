"""MapReduce-style trend aggregation."""

from collections import Counter
from collections.abc import Iterable


def map_terms(records: Iterable[dict], field: str = "term") -> Counter[str]:
    """Map records to term counts."""
    return Counter(str(record[field]) for record in records if field in record)


def reduce_counts(*counters: Counter[str]) -> Counter[str]:
    """Reduce multiple term-count mappings into one."""
    result: Counter[str] = Counter()
    for counter in counters:
        result.update(counter)
    return result
