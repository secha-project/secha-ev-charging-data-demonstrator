"""Deterministic planner-facing PQ KPI helpers.

The demonstrator keeps harmonic and overall PQ scores on a bounded ``0-100``
scale. Current imbalance remains a simplified percent-style metric on a
``0-200`` bounded scale in the Simulation layer and is normalized to
``0-100`` only when contributing to the aggregate overall PQ score.
"""

from simulation.time import get_timestep_hours


POWER_QUALITY_RISK_LOW = "low"
POWER_QUALITY_RISK_MODERATE = "moderate"
POWER_QUALITY_RISK_HIGH = "high"
POWER_QUALITY_PRIMARY_ISSUE_NONE = "none"
POWER_QUALITY_PRIMARY_ISSUE_HARMONIC = "harmonic_risk"
POWER_QUALITY_PRIMARY_ISSUE_CURRENT_IMBALANCE = "current_imbalance"

HARMONIC_RISK_MODERATE_SCORE_THRESHOLD = 35.0
HARMONIC_RISK_HIGH_SCORE_THRESHOLD = 70.0
CURRENT_IMBALANCE_MODERATE_PERCENT_THRESHOLD = 25.0
CURRENT_IMBALANCE_HIGH_PERCENT_THRESHOLD = 75.0
OVERALL_PQ_MODERATE_SCORE_THRESHOLD = 30.0
OVERALL_PQ_HIGH_SCORE_THRESHOLD = 60.0

POWER_QUALITY_MODERATE_DURATION_HOURS_THRESHOLD = 1.0
POWER_QUALITY_HIGH_DURATION_HOURS_THRESHOLD = 2.0

HARMONIC_WEIGHT = 0.6
CURRENT_IMBALANCE_WEIGHT = 0.4

POWER_QUALITY_RISK_ORDER = {
    POWER_QUALITY_RISK_LOW: 0,
    POWER_QUALITY_RISK_MODERATE: 1,
    POWER_QUALITY_RISK_HIGH: 2,
}


def classify_power_quality_risk(
    values: list[float],
    *,
    moderate_threshold: float,
    high_threshold: float,
) -> str:
    """Return a deterministic low/moderate/high risk level from one PQ series."""
    peak_value = max(values, default=0.0)
    high_duration_hours = calculate_threshold_duration_hours(
        values,
        threshold=high_threshold,
    )
    moderate_duration_hours = calculate_threshold_duration_hours(
        values,
        threshold=moderate_threshold,
    )

    if peak_value >= high_threshold:
        return POWER_QUALITY_RISK_HIGH
    if high_duration_hours >= POWER_QUALITY_HIGH_DURATION_HOURS_THRESHOLD:
        return POWER_QUALITY_RISK_HIGH
    if moderate_duration_hours >= POWER_QUALITY_MODERATE_DURATION_HOURS_THRESHOLD:
        return POWER_QUALITY_RISK_MODERATE
    if peak_value >= moderate_threshold:
        return POWER_QUALITY_RISK_MODERATE
    return POWER_QUALITY_RISK_LOW


def calculate_threshold_duration_hours(
    values: list[float],
    *,
    threshold: float,
) -> float:
    """Return total duration where values meet or exceed one threshold."""
    return sum(value >= threshold for value in values) * get_timestep_hours()


def build_overall_pq_risk_score_series(
    harmonic_risk_score_by_timestep: list[float],
    current_imbalance_percent_by_timestep: list[float],
) -> list[float]:
    """Return bounded overall PQ scores derived from harmonic and imbalance."""
    if len(harmonic_risk_score_by_timestep) != len(
        current_imbalance_percent_by_timestep
    ):
        return []

    return [
        round(
            min(
                max(
                    (
                        HARMONIC_WEIGHT * harmonic_risk_score
                        + CURRENT_IMBALANCE_WEIGHT
                        * _normalize_current_imbalance_percent(
                            current_imbalance_percent
                        )
                    ),
                    0.0,
                ),
                100.0,
            ),
            4,
        )
        for harmonic_risk_score, current_imbalance_percent in zip(
            harmonic_risk_score_by_timestep,
            current_imbalance_percent_by_timestep,
            strict=True,
        )
    ]


def highest_power_quality_risk_level(risk_levels: list[str]) -> str:
    """Return the highest deterministic PQ risk level from a list."""
    if not risk_levels:
        return POWER_QUALITY_RISK_LOW

    return max(
        risk_levels,
        key=lambda risk_level: POWER_QUALITY_RISK_ORDER.get(risk_level, 0),
    )


def identify_primary_power_quality_issue(
    *,
    peak_harmonic_risk_score: float,
    peak_current_imbalance_percent: float,
) -> str:
    """Return the dominant weighted PQ issue for summary messaging."""
    harmonic_contribution = HARMONIC_WEIGHT * max(peak_harmonic_risk_score, 0.0)
    imbalance_contribution = CURRENT_IMBALANCE_WEIGHT * _normalize_current_imbalance_percent(
        peak_current_imbalance_percent
    )

    if (
        harmonic_contribution <= 0.0
        and imbalance_contribution <= 0.0
    ):
        return POWER_QUALITY_PRIMARY_ISSUE_NONE
    if harmonic_contribution >= imbalance_contribution:
        return POWER_QUALITY_PRIMARY_ISSUE_HARMONIC
    return POWER_QUALITY_PRIMARY_ISSUE_CURRENT_IMBALANCE


def derive_overall_power_quality_risk_level(
    *,
    overall_pq_risk_score_by_timestep: list[float],
    harmonic_risk_level: str,
    current_imbalance_risk_level: str,
    primary_issue: str,
) -> str:
    """Return overall PQ risk while respecting the dominant weighted issue."""
    blended_risk_level = classify_power_quality_risk(
        overall_pq_risk_score_by_timestep,
        moderate_threshold=OVERALL_PQ_MODERATE_SCORE_THRESHOLD,
        high_threshold=OVERALL_PQ_HIGH_SCORE_THRESHOLD,
    )

    dominant_issue_risk_level = POWER_QUALITY_RISK_LOW
    if primary_issue == POWER_QUALITY_PRIMARY_ISSUE_HARMONIC:
        dominant_issue_risk_level = harmonic_risk_level
    elif primary_issue == POWER_QUALITY_PRIMARY_ISSUE_CURRENT_IMBALANCE:
        dominant_issue_risk_level = current_imbalance_risk_level

    return highest_power_quality_risk_level(
        [
            blended_risk_level,
            dominant_issue_risk_level,
        ]
    )


def build_power_quality_message(
    *,
    overall_pq_risk_level: str,
    harmonic_risk_level: str,
    current_imbalance_risk_level: str,
    primary_issue: str,
) -> str:
    """Return a short deterministic planner-facing PQ explanation."""
    if overall_pq_risk_level == POWER_QUALITY_RISK_LOW:
        return (
            "Modeled overall PQ risk is low because harmonic risk and current "
            "imbalance remain below warning thresholds."
        )

    if primary_issue == POWER_QUALITY_PRIMARY_ISSUE_HARMONIC:
        return (
            f"Modeled overall PQ risk is {overall_pq_risk_level} because "
            f"harmonic risk is {harmonic_risk_level} and dominates the weighted "
            "PQ score."
        )

    if primary_issue == POWER_QUALITY_PRIMARY_ISSUE_CURRENT_IMBALANCE:
        return (
            f"Modeled overall PQ risk is {overall_pq_risk_level} because "
            f"current imbalance is {current_imbalance_risk_level} and "
            "dominates the weighted PQ score."
        )

    return (
        f"Modeled overall PQ risk is {overall_pq_risk_level} based on the "
        "demonstrator's weighted harmonic and imbalance signals."
    )


def _normalize_current_imbalance_percent(current_imbalance_percent: float) -> float:
    return min(max(current_imbalance_percent, 0.0), 100.0)
