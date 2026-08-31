"""Planner-facing diagnostic values layered on top of direct metric outputs."""

from metrics.constraint_analysis import (
    NO_PRIMARY_CONSTRAINT_REASON,
    calculate_recommended_connection_capacity_kw,
    classify_primary_constraint_reason,
    connection_capacity_is_adequate,
    resolve_connection_capacity_recommendation_reason,
)
from metrics.core_metrics import _PlannerDiagnosticsInputs
from metrics.metrics import Metrics, MetricsData
from scenarios import Scenario
from simulation.result import SimulationResult


def _build_planner_context_metrics(
    planner_inputs: _PlannerDiagnosticsInputs,
    *,
    primary_constraint_reason: str,
) -> Metrics:
    """Return the reduced Metrics context used by planner rerun helpers."""

    return Metrics(
        total_daily_energy=planner_inputs.total_daily_energy,
        available_capacity=planner_inputs.available_capacity,
        energy_delivery_sufficient=planner_inputs.energy_delivery_sufficient,
        peak_load=planner_inputs.peak_load,
        capacity_utilization=planner_inputs.capacity_utilization,
        delivered_energy=planner_inputs.delivered_energy,
        unmet_energy=planner_inputs.unmet_energy,
        queue_present_indicator=planner_inputs.queue_present_indicator,
        maximum_waiting_time_hours=planner_inputs.maximum_waiting_time_hours,
        charger_service_waiting_tolerance_hours=(
            planner_inputs.charger_service_waiting_tolerance_hours
        ),
        vehicles_not_started_count=planner_inputs.vehicles_not_started_count,
        vehicles_with_unmet_energy_count=(
            planner_inputs.vehicles_with_unmet_energy_count
        ),
        primary_constraint_reason=primary_constraint_reason,
    )


def _calculate_planner_diagnostic_values(
    simulation_result: SimulationResult,
    scenario: Scenario,
    planner_inputs: _PlannerDiagnosticsInputs,
    *,
    include_primary_constraint_reason: bool,
    include_charger_count_recommendation: bool,
) -> MetricsData:
    """Return planner-diagnostic values, including optional rerun helpers."""

    primary_constraint_reason = NO_PRIMARY_CONSTRAINT_REASON
    if include_primary_constraint_reason:
        primary_constraint_reason = classify_primary_constraint_reason(
            scenario=scenario,
            simulation_result=simulation_result,
            queue_present_indicator=planner_inputs.queue_present_indicator,
            vehicles_not_started_count=(
                planner_inputs.vehicles_not_started_count
            ),
            vehicles_with_unmet_energy_count=(
                planner_inputs.vehicles_with_unmet_energy_count
            ),
        )
    connection_capacity_adequate_indicator = (
        connection_capacity_is_adequate(
            persistent_capacity_exceedance_indicator=(
                planner_inputs.persistent_capacity_exceedance_indicator
            ),
            primary_constraint_reason=primary_constraint_reason,
        )
    )
    connection_capacity_recommendation_reason = (
        resolve_connection_capacity_recommendation_reason(
            persistent_capacity_exceedance_indicator=(
                planner_inputs.persistent_capacity_exceedance_indicator
            ),
            primary_constraint_reason=primary_constraint_reason,
        )
    )
    recommended_connection_capacity_kw = (
        calculate_recommended_connection_capacity_kw(
            configured_connection_capacity_kw=(
                planner_inputs.configured_connection_capacity_kw
            ),
            required_connection_capacity_kw=(
                planner_inputs.required_connection_capacity_kw
            ),
            planning_margin_percent=scenario.planning_margin_percent,
            connection_capacity_adequate_indicator=(
                connection_capacity_adequate_indicator
            ),
        )
    )
    required_charger_count: int | None = None
    additional_chargers_required: int | None = None
    charger_count_sufficient_indicator = False
    if include_charger_count_recommendation:
        from metrics.planning import search_minimum_feasible_charger_count

        planner_context_metrics = _build_planner_context_metrics(
            planner_inputs,
            primary_constraint_reason=primary_constraint_reason,
        )
        charger_count_search_result = search_minimum_feasible_charger_count(
            scenario,
            simulation_result,
            planner_context_metrics,
        )
        recommendation_available = (
            charger_count_search_result.service_rule_already_met
            or (
                charger_count_search_result.charger_count_resolvable
                and charger_count_search_result.feasible_candidate_found
            )
        )
        if recommendation_available:
            required_charger_count = (
                charger_count_search_result.first_feasible_candidate_charger_count
            )
            additional_chargers_required = max(
                (required_charger_count or 0) - scenario.charger_count,
                0,
            )
            charger_count_sufficient_indicator = (
                additional_chargers_required == 0
            )

    return {
        "recommended_connection_capacity_kw": (
            recommended_connection_capacity_kw
        ),
        "connection_capacity_adequate_indicator": (
            connection_capacity_adequate_indicator
        ),
        "connection_capacity_recommendation_reason": (
            connection_capacity_recommendation_reason
        ),
        "required_charger_count": required_charger_count,
        "additional_chargers_required": additional_chargers_required,
        "charger_count_sufficient_indicator": (
            charger_count_sufficient_indicator
        ),
        "primary_constraint_reason": primary_constraint_reason,
    }
