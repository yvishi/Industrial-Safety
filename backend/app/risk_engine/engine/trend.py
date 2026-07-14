"""Score-over-time trend: a pure comparison against the prior snapshot's score, if any."""

from app.risk_engine.config.schema import TrendDirection


def compute_trend(current_score: int, previous_score: int | None) -> tuple[int | None, TrendDirection | None]:
    """Returns (score_delta, trend_direction). If previous_score is None (no prior snapshot
    exists for this zone yet), returns (None, None)."""
    if previous_score is None:
        return None, None

    delta = current_score - previous_score
    if delta > 0:
        direction = TrendDirection.UP
    elif delta < 0:
        direction = TrendDirection.DOWN
    else:
        direction = TrendDirection.FLAT

    return delta, direction
