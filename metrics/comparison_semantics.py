"""Shared comparison materiality and outcome helpers for Metrics consumers."""

from typing import Any


COMPARISON_OUTCOME_IMPROVEMENT = "improvement"
COMPARISON_OUTCOME_TRADE_OFF = "trade_off"
COMPARISON_OUTCOME_NEUTRAL = "neutral"


def default_materiality_threshold(change_format: str) -> float:
    """Return the smallest raw delta that should survive display rounding."""

    if change_format in {
        "power_kw_signed",
        "energy_kwh_signed",
        "hours_signed",
        "charger_count_1_signed",
        "vehicle_count_1_signed",
        "percentage_points_signed",
        "score_points_signed",
    }:
        return 0.05

    if change_format in {
        "charger_count_0_signed",
        "vehicle_count_0_signed",
        "feeder_count_signed",
        "warning_count_signed",
    }:
        return 0.5

    return 0.0


def classify_directional_outcome(
    change_value: Any,
    preferred_direction: str,
) -> str:
    """Classify whether a directional comparison is better, worse, or neutral."""

    if change_value in (None, 0, 0.0):
        return COMPARISON_OUTCOME_NEUTRAL

    if preferred_direction == "lower":
        return (
            COMPARISON_OUTCOME_IMPROVEMENT
            if change_value < 0
            else COMPARISON_OUTCOME_TRADE_OFF
        )

    return (
        COMPARISON_OUTCOME_IMPROVEMENT
        if change_value > 0
        else COMPARISON_OUTCOME_TRADE_OFF
    )


def relative_shift_percent(
    raw_change: float | int | None,
    baseline_value: float | int,
) -> float:
    """Return a stable absolute relative shift for cross-metric comparisons."""

    if raw_change in (None, 0, 0.0):
        return 0.0

    baseline_magnitude = abs(float(baseline_value))
    if baseline_magnitude == 0.0:
        return 100.0

    return abs(float(raw_change)) / baseline_magnitude * 100.0


def is_numeric_change_material(
    change_value: Any,
    *,
    absolute_materiality_threshold: float,
    relative_materiality_threshold: float | None = None,
    relative_change_percent: float | None = None,
    baseline_value: float | int = 0.0,
) -> bool:
    """Return whether a numeric comparison delta is large enough to summarize."""

    if change_value in (None, 0, 0.0):
        return False

    absolute_change = abs(float(change_value))
    if absolute_change < absolute_materiality_threshold:
        return False

    if relative_materiality_threshold is None:
        return True

    if relative_change_percent is not None:
        return abs(float(relative_change_percent)) >= relative_materiality_threshold

    return (
        relative_shift_percent(change_value, baseline_value)
        >= relative_materiality_threshold
    )


def normalize_numeric_delta_for_display(
    change_value: float | int | None,
    change_format: str,
) -> float | int | None:
    """Normalize exact or display-rounded zero deltas to a stable zero value."""

    if change_value is None:
        return None

    if change_value in (0, 0.0):
        return 0 if isinstance(change_value, int) else 0.0

    threshold = default_materiality_threshold(change_format)
    if abs(float(change_value)) < threshold:
        return 0 if isinstance(change_value, int) else 0.0

    return change_value
