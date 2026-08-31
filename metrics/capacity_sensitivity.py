"""Deterministic orchestration for connection-capacity sensitivity reruns."""

from dataclasses import dataclass, replace
from typing import Any

from metrics.constraint_analysis import (
    CONFIGURED_CONNECTION_CAPACITY_ADEQUATE_REASON,
    PERSISTENT_CONNECTION_CAPACITY_EXCEEDANCE_REASON,
    calculate_exceedance_values,
    calculate_peak_capacity_margin_percent,
    classify_primary_constraint_reason,
    connection_capacity_is_adequate,
    count_exceeded_timesteps,
    has_persistent_connection_capacity_exceedance,
    resolve_connection_capacity_recommendation_reason,
)
from metrics.metrics import Metrics, calculate_metrics
from metrics.shared import (
    FLOATING_POINT_TOLERANCE,
    extract_window_count_values,
)
from scenarios import Scenario
from simulation import get_timestep_hours, simulate


CAPACITY_REDUCTION_FACTOR = 0.8
CAPACITY_INCREASE_FACTOR = 1.2
CapacityAlternativeMetricsData = dict[str, Any]


@dataclass(frozen=True)
class CapacityAlternativeMetrics:
    """Planner-facing results for one connection-capacity alternative."""

    capacity_option_kw: float
    required_connection_capacity_kw: float
    headroom_kw: float
    headroom_percent: float | None
    capacity_exceeded: bool
    time_above_capacity_hours: float
    capacity_adequate_indicator: bool = True
    capacity_recommendation_reason: str = (
        CONFIGURED_CONNECTION_CAPACITY_ADEQUATE_REASON
    )


def create_capacity_alternative_metrics(
    capacity_option_kw: float,
    metrics: Metrics,
) -> CapacityAlternativeMetrics:
    """Map completed rerun metrics into one capacity-sensitivity result row."""
    return CapacityAlternativeMetrics(
        capacity_option_kw=capacity_option_kw,
        required_connection_capacity_kw=(
            metrics.required_connection_capacity_kw
        ),
        headroom_kw=metrics.peak_capacity_margin_kw,
        headroom_percent=metrics.peak_capacity_margin_percent,
        capacity_exceeded=metrics.connection_capacity_exceeded,
        time_above_capacity_hours=metrics.capacity_exceedance_duration_hours,
        capacity_adequate_indicator=(
            metrics.connection_capacity_adequate_indicator
        ),
        capacity_recommendation_reason=(
            metrics.connection_capacity_recommendation_reason
        ),
    )


def capacity_alternative_metrics_to_dict(
    row: CapacityAlternativeMetrics,
) -> CapacityAlternativeMetricsData:
    """Return a Dash-store-safe dictionary for one sensitivity result row."""
    return {
        "capacity_option_kw": row.capacity_option_kw,
        "required_connection_capacity_kw": (
            row.required_connection_capacity_kw
        ),
        "headroom_kw": row.headroom_kw,
        "headroom_percent": row.headroom_percent,
        "capacity_exceeded": row.capacity_exceeded,
        "time_above_capacity_hours": row.time_above_capacity_hours,
        "capacity_adequate_indicator": row.capacity_adequate_indicator,
        "capacity_recommendation_reason": row.capacity_recommendation_reason,
    }


def capacity_alternative_metrics_from_dict(
    data: CapacityAlternativeMetricsData,
) -> CapacityAlternativeMetrics:
    """Rebuild one sensitivity result row from serialized row data."""
    headroom_kw = data.get(
        "headroom_kw",
        data.get("peak_capacity_margin_kw", 0.0),
    )
    capacity_option_kw = data["capacity_option_kw"]
    required_connection_capacity_kw = data.get(
        "required_connection_capacity_kw",
        capacity_option_kw - headroom_kw,
    )
    capacity_exceeded = data.get(
        "capacity_exceeded",
        data.get("connection_capacity_exceeded", False),
    )
    capacity_adequate_indicator = data.get(
        "capacity_adequate_indicator",
        not capacity_exceeded,
    )
    return CapacityAlternativeMetrics(
        capacity_option_kw=capacity_option_kw,
        required_connection_capacity_kw=required_connection_capacity_kw,
        headroom_kw=headroom_kw,
        headroom_percent=data.get(
            "headroom_percent",
            data.get("peak_capacity_margin_percent"),
        ),
        capacity_exceeded=capacity_exceeded,
        time_above_capacity_hours=data.get(
            "time_above_capacity_hours",
            data.get("capacity_exceedance_duration_hours", 0.0),
        ),
        capacity_adequate_indicator=capacity_adequate_indicator,
        capacity_recommendation_reason=data.get(
            "capacity_recommendation_reason",
            (
                CONFIGURED_CONNECTION_CAPACITY_ADEQUATE_REASON
                if capacity_adequate_indicator
                else PERSISTENT_CONNECTION_CAPACITY_EXCEEDANCE_REASON
            ),
        ),
    )


def generate_connection_capacity_alternatives(
    configured_connection_capacity_kw: float,
    required_connection_capacity_kw: float,
    recommended_connection_capacity_kw: float,
) -> list[float]:
    """Return deterministic connection-capacity alternatives for one base run."""
    alternatives = [
        CAPACITY_REDUCTION_FACTOR * configured_connection_capacity_kw,
        configured_connection_capacity_kw,
        CAPACITY_INCREASE_FACTOR * configured_connection_capacity_kw,
        required_connection_capacity_kw,
        recommended_connection_capacity_kw,
    ]
    return sorted({max(value, 0.0) for value in alternatives})


def _create_lightweight_capacity_alternative_metrics(
    capacity_option_kw: float,
    simulation_result,
    scenario: Scenario,
    *,
    required_connection_capacity_kw: float,
) -> CapacityAlternativeMetrics:
    """Return one sensitivity row using only connection-sizing diagnostics."""

    exceedance_values = calculate_exceedance_values(
        simulation_result.requested_load_profile_kw,
        capacity_option_kw,
    )
    exceeded_timestep_count = count_exceeded_timesteps(exceedance_values)
    persistent_capacity_exceedance_indicator = (
        has_persistent_connection_capacity_exceedance(
            exceeded_timestep_count
        )
    )
    queue_present_indicator = any(
        waiting_count > 0
        for waiting_count in extract_window_count_values(
            simulation_result.waiting_vehicle_count_by_timestep,
            scenario,
        )
    )
    vehicles_not_started_count = sum(
        request.charging_start_timestep is None
        for request in simulation_result.charging_requests
    )
    vehicles_with_unmet_energy_count = sum(
        request.unmet_energy_kwh > FLOATING_POINT_TOLERANCE
        for request in simulation_result.charging_requests
    )
    primary_constraint_reason = classify_primary_constraint_reason(
        scenario=scenario,
        simulation_result=simulation_result,
        queue_present_indicator=queue_present_indicator,
        vehicles_not_started_count=vehicles_not_started_count,
        vehicles_with_unmet_energy_count=vehicles_with_unmet_energy_count,
    )
    capacity_adequate_indicator = connection_capacity_is_adequate(
        persistent_capacity_exceedance_indicator=(
            persistent_capacity_exceedance_indicator
        ),
        primary_constraint_reason=primary_constraint_reason,
    )
    capacity_recommendation_reason = (
        resolve_connection_capacity_recommendation_reason(
            persistent_capacity_exceedance_indicator=(
                persistent_capacity_exceedance_indicator
            ),
            primary_constraint_reason=primary_constraint_reason,
        )
    )
    headroom_kw = capacity_option_kw - required_connection_capacity_kw

    return CapacityAlternativeMetrics(
        capacity_option_kw=capacity_option_kw,
        required_connection_capacity_kw=required_connection_capacity_kw,
        headroom_kw=headroom_kw,
        headroom_percent=calculate_peak_capacity_margin_percent(
            capacity_option_kw,
            required_connection_capacity_kw,
        ),
        capacity_exceeded=any(
            exceedance_kw > 0.0 for exceedance_kw in exceedance_values
        ),
        time_above_capacity_hours=(
            exceeded_timestep_count * get_timestep_hours()
        ),
        capacity_adequate_indicator=capacity_adequate_indicator,
        capacity_recommendation_reason=capacity_recommendation_reason,
    )


def run_connection_capacity_sensitivity(
    scenario: Scenario,
    capacity_alternatives_kw: list[float] | None = None,
    *,
    base_metrics: Metrics | None = None,
) -> list[CapacityAlternativeMetrics]:
    """Rerun one scenario across connection-capacity alternatives."""
    alternative_values = list(capacity_alternatives_kw or [])
    resolved_base_metrics = base_metrics
    if resolved_base_metrics is None:
        base_result = simulate(scenario)
        resolved_base_metrics = calculate_metrics(base_result, scenario)

    assert resolved_base_metrics is not None
    if not alternative_values:
        alternative_values = generate_connection_capacity_alternatives(
            scenario.grid_capacity,
            resolved_base_metrics.required_connection_capacity_kw,
            resolved_base_metrics.recommended_connection_capacity_kw,
        )
    alternative_values = sorted(alternative_values)

    sensitivity_results: list[CapacityAlternativeMetrics] = []
    for configured_connection_capacity_kw in alternative_values:
        if configured_connection_capacity_kw == scenario.grid_capacity:
            sensitivity_results.append(
                create_capacity_alternative_metrics(
                    configured_connection_capacity_kw,
                    resolved_base_metrics,
                )
            )
            continue

        alternative_scenario = replace(
            scenario,
            grid_capacity=configured_connection_capacity_kw,
        )
        rerun_result = simulate(alternative_scenario)
        sensitivity_results.append(
            _create_lightweight_capacity_alternative_metrics(
                configured_connection_capacity_kw,
                rerun_result,
                alternative_scenario,
                required_connection_capacity_kw=(
                    resolved_base_metrics.required_connection_capacity_kw
                ),
            )
        )

    return sensitivity_results
