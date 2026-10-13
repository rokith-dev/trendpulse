"""Funnel conversion analysis."""


def conversion_rates(stages: list[int]) -> list[float]:
    """Calculate each funnel stage as a share of the first stage."""
    if not stages or stages[0] == 0:
        return []
    return [count / stages[0] for count in stages]
