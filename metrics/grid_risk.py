from simulation.time import get_timestep_hours


THERMAL_RISK_LOW = "low"
THERMAL_RISK_MODERATE = "moderate"
THERMAL_RISK_HIGH = "high"

MODERATE_LOADING_PERCENT_THRESHOLD = 90.0
HIGH_LOADING_PERCENT_THRESHOLD = 95.0
MODERATE_LOADING_DURATION_HOURS_THRESHOLD = 1.0
HIGH_LOADING_DURATION_HOURS_THRESHOLD = 2.0
HIGH_OVERLOAD_DURATION_HOURS_THRESHOLD = 1.0

THERMAL_RISK_ORDER = {
    THERMAL_RISK_LOW: 0,
    THERMAL_RISK_MODERATE: 1,
    THERMAL_RISK_HIGH: 2,
}


def classify_thermal_risk(
    loading_percent_by_timestep: list[float],
    overload_kw_by_timestep: list[float],
) -> str:
    """Return a deterministic thermal-risk category from loading severity data."""
    overload_duration_hours = _count_positive_timesteps(
        overload_kw_by_timestep
    ) * get_timestep_hours()
    high_loading_duration_hours = _count_timesteps_at_or_above(
        loading_percent_by_timestep,
        HIGH_LOADING_PERCENT_THRESHOLD,
    ) * get_timestep_hours()
    moderate_loading_duration_hours = _count_timesteps_at_or_above(
        loading_percent_by_timestep,
        MODERATE_LOADING_PERCENT_THRESHOLD,
    ) * get_timestep_hours()

    if overload_duration_hours >= HIGH_OVERLOAD_DURATION_HOURS_THRESHOLD:
        return THERMAL_RISK_HIGH
    if high_loading_duration_hours >= HIGH_LOADING_DURATION_HOURS_THRESHOLD:
        return THERMAL_RISK_HIGH
    if overload_duration_hours > 0.0:
        return THERMAL_RISK_MODERATE
    if moderate_loading_duration_hours >= MODERATE_LOADING_DURATION_HOURS_THRESHOLD:
        return THERMAL_RISK_MODERATE
    return THERMAL_RISK_LOW


def highest_thermal_risk_level(risk_levels: list[str]) -> str:
    """Return the highest deterministic thermal-risk level from a list."""
    if not risk_levels:
        return THERMAL_RISK_LOW

    return max(
        risk_levels,
        key=lambda risk_level: THERMAL_RISK_ORDER.get(risk_level, 0),
    )


def _count_timesteps_at_or_above(
    values: list[float],
    threshold: float,
) -> int:
    return sum(value >= threshold for value in values)


def _count_positive_timesteps(values: list[float]) -> int:
    return sum(value > 0.0 for value in values)
