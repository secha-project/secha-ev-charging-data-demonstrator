"""Constraint and connection-capacity reasoning shared by metrics consumers."""

from dataclasses import dataclass

from scenarios import Scenario, copy_scenario_with_updates
from simulation import simulate
from simulation.result import SimulationResult
from simulation.time import TIMESTEPS_PER_DAY, get_timestep_hours

from metrics.shared import (
    FLOATING_POINT_TOLERANCE,
    PERCENT_MULTIPLIER,
    extract_window_count_values,
)


CONNECTION_CAPACITY_EXCEEDANCE_PERSISTENCE_TIMESTEP_THRESHOLD = 2
NO_PRIMARY_CONSTRAINT_REASON = "none"
CHARGER_AVAILABILITY_CONSTRAINT_REASON = "charger_availability"
CHARGER_POWER_CONSTRAINT_REASON = "charger_power"
GRID_CONNECTION_CAPACITY_CONSTRAINT_REASON = "grid_connection_capacity"
CHARGING_WINDOW_CONSTRAINT_REASON = "charging_window"
MIXED_CONSTRAINT_REASON = "mixed"
PRIMARY_CONSTRAINT_REASON_LABELS = {
    NO_PRIMARY_CONSTRAINT_REASON: "No primary constraint identified",
    CHARGER_AVAILABILITY_CONSTRAINT_REASON: "Charger availability",
    CHARGER_POWER_CONSTRAINT_REASON: "Charger power",
    GRID_CONNECTION_CAPACITY_CONSTRAINT_REASON: "Grid connection capacity",
    CHARGING_WINDOW_CONSTRAINT_REASON: "Charging allowed window",
    MIXED_CONSTRAINT_REASON: "Multiple modeled constraints",
}
CONFIGURED_CONNECTION_CAPACITY_ADEQUATE_REASON = "configured_capacity_adequate"
PERSISTENT_CONNECTION_CAPACITY_EXCEEDANCE_REASON = (
    "persistent_requested_exceedance"
)
GRID_CONNECTION_SERVICE_PRESSURE_REASON = "grid_capacity_service_pressure"


def format_primary_constraint_reason_label(reason: str) -> str:
    """Return a planner-facing label for one primary-constraint code."""

    return PRIMARY_CONSTRAINT_REASON_LABELS.get(
        reason,
        PRIMARY_CONSTRAINT_REASON_LABELS[NO_PRIMARY_CONSTRAINT_REASON],
    )


@dataclass(frozen=True)
class _PrimaryConstraintProbe:
    """Minimal rerun outputs needed for primary-constraint classification."""

    queue_present_indicator: bool
    vehicles_not_started_count: int
    vehicles_with_unmet_energy_count: int


def classify_primary_constraint_reason(
    *,
    scenario: Scenario,
    simulation_result: SimulationResult,
    queue_present_indicator: bool,
    vehicles_not_started_count: int,
    vehicles_with_unmet_energy_count: int,
) -> str:
    """Classify the main planner-facing constraint through deterministic reruns."""

    if not _has_primary_constraint_problem(
        queue_present_indicator=queue_present_indicator,
        vehicles_not_started_count=vehicles_not_started_count,
        vehicles_with_unmet_energy_count=vehicles_with_unmet_energy_count,
    ):
        return NO_PRIMARY_CONSTRAINT_REASON

    if scenario.vehicles == 0:
        return NO_PRIMARY_CONSTRAINT_REASON

    if not _has_complete_primary_constraint_inputs(
        simulation_result,
        scenario,
    ):
        return MIXED_CONSTRAINT_REASON

    if _has_ambiguous_request_level_reasons(simulation_result):
        return MIXED_CONSTRAINT_REASON

    ample_charger_count = _calculate_ample_charger_count(scenario)
    chargers_only_metrics = _run_counterfactual_metrics(
        copy_scenario_with_updates(
            scenario,
            charger_count=ample_charger_count,
        )
    )
    if _metrics_problem_resolved(chargers_only_metrics):
        return CHARGER_AVAILABILITY_CONSTRAINT_REASON

    ample_charger_power_kw = _calculate_ample_charger_power_kw(scenario)
    charger_power_metrics = _run_counterfactual_metrics(
        copy_scenario_with_updates(
            scenario,
            charger_count=ample_charger_count,
            charger_power=ample_charger_power_kw,
        )
    )
    if _metrics_problem_resolved(charger_power_metrics):
        if _has_direct_availability_limitation(scenario, simulation_result):
            return MIXED_CONSTRAINT_REASON
        return CHARGER_POWER_CONSTRAINT_REASON

    ample_grid_capacity_kw = _calculate_ample_grid_capacity_kw(
        scenario,
        ample_charger_count=ample_charger_count,
        ample_charger_power_kw=ample_charger_power_kw,
    )
    grid_capacity_metrics = _run_counterfactual_metrics(
        copy_scenario_with_updates(
            scenario,
            charger_count=ample_charger_count,
            charger_power=ample_charger_power_kw,
            grid_capacity=ample_grid_capacity_kw,
        )
    )
    if _metrics_problem_resolved(grid_capacity_metrics):
        if _has_direct_availability_limitation(
            scenario,
            simulation_result,
        ) or _has_direct_charger_power_limitation(simulation_result):
            return MIXED_CONSTRAINT_REASON
        return GRID_CONNECTION_CAPACITY_CONSTRAINT_REASON

    if _has_primary_constraint_problem(
        queue_present_indicator=grid_capacity_metrics.queue_present_indicator,
        vehicles_not_started_count=grid_capacity_metrics.vehicles_not_started_count,
        vehicles_with_unmet_energy_count=(
            grid_capacity_metrics.vehicles_with_unmet_energy_count
        ),
    ):
        if _has_non_window_constraint_evidence(
            scenario,
            simulation_result,
        ):
            return MIXED_CONSTRAINT_REASON
        return CHARGING_WINDOW_CONSTRAINT_REASON

    return MIXED_CONSTRAINT_REASON


def calculate_exceedance_values(
    requested_load_profile_kw: list[float],
    configured_connection_capacity_kw: float,
) -> list[float]:
    """Return positive connection-capacity exceedances from requested load."""

    return [
        max(load_kw - configured_connection_capacity_kw, 0.0)
        for load_kw in requested_load_profile_kw
    ]


def count_exceeded_timesteps(exceedance_values: list[float]) -> int:
    """Return the number of timesteps with a positive exceedance."""

    return sum(exceedance_kw > 0.0 for exceedance_kw in exceedance_values)


def has_persistent_connection_capacity_exceedance(
    exceeded_timestep_count: int,
) -> bool:
    """Return whether requested-load exceedance persists beyond a brief spike."""

    return (
        exceeded_timestep_count
        >= CONNECTION_CAPACITY_EXCEEDANCE_PERSISTENCE_TIMESTEP_THRESHOLD
    )


def connection_capacity_is_adequate(
    *,
    persistent_capacity_exceedance_indicator: bool,
    primary_constraint_reason: str,
) -> bool:
    """Return whether configured capacity is adequate for planning purposes."""

    return not (
        persistent_capacity_exceedance_indicator
        or primary_constraint_reason
        == GRID_CONNECTION_CAPACITY_CONSTRAINT_REASON
    )


def resolve_connection_capacity_recommendation_reason(
    *,
    persistent_capacity_exceedance_indicator: bool,
    primary_constraint_reason: str,
) -> str:
    """Return the deterministic reason for the current capacity recommendation."""

    if primary_constraint_reason == GRID_CONNECTION_CAPACITY_CONSTRAINT_REASON:
        return GRID_CONNECTION_SERVICE_PRESSURE_REASON

    if persistent_capacity_exceedance_indicator:
        return PERSISTENT_CONNECTION_CAPACITY_EXCEEDANCE_REASON

    return CONFIGURED_CONNECTION_CAPACITY_ADEQUATE_REASON


def calculate_recommended_connection_capacity_kw(
    *,
    configured_connection_capacity_kw: float,
    required_connection_capacity_kw: float,
    planning_margin_percent: float,
    connection_capacity_adequate_indicator: bool,
) -> float:
    """Return the planner-facing capacity recommendation from adequacy evidence."""

    if required_connection_capacity_kw <= FLOATING_POINT_TOLERANCE:
        return 0.0

    if connection_capacity_adequate_indicator:
        return configured_connection_capacity_kw

    return max(
        configured_connection_capacity_kw,
        required_connection_capacity_kw
        * _planning_margin_multiplier(planning_margin_percent),
    )


def calculate_peak_capacity_margin_percent(
    configured_connection_capacity_kw: float,
    required_connection_capacity_kw: float,
) -> float | None:
    """Return peak margin relative to configured connection capacity."""

    if configured_connection_capacity_kw == 0.0:
        return None

    peak_capacity_margin_kw = (
        configured_connection_capacity_kw - required_connection_capacity_kw
    )
    return (
        peak_capacity_margin_kw
        / configured_connection_capacity_kw
        * PERCENT_MULTIPLIER
    )


def _run_counterfactual_metrics(
    scenario: Scenario,
) -> _PrimaryConstraintProbe:
    """Return the minimal primary-constraint probe for one rerun."""

    rerun_result = simulate(scenario)
    waiting_vehicle_count_window = extract_window_count_values(
        rerun_result.waiting_vehicle_count_by_timestep,
        scenario,
    )
    return _PrimaryConstraintProbe(
        queue_present_indicator=any(
            waiting_count > 0 for waiting_count in waiting_vehicle_count_window
        ),
        vehicles_not_started_count=sum(
            request.charging_start_timestep is None
            for request in rerun_result.charging_requests
        ),
        vehicles_with_unmet_energy_count=sum(
            request.unmet_energy_kwh > FLOATING_POINT_TOLERANCE
            for request in rerun_result.charging_requests
        ),
    )


def _metrics_problem_resolved(metrics: _PrimaryConstraintProbe) -> bool:
    return not _has_primary_constraint_problem(
        queue_present_indicator=metrics.queue_present_indicator,
        vehicles_not_started_count=metrics.vehicles_not_started_count,
        vehicles_with_unmet_energy_count=metrics.vehicles_with_unmet_energy_count,
    )


def _has_primary_constraint_problem(
    *,
    queue_present_indicator: bool,
    vehicles_not_started_count: int,
    vehicles_with_unmet_energy_count: int,
) -> bool:
    return (
        queue_present_indicator
        or vehicles_not_started_count > 0
        or vehicles_with_unmet_energy_count > 0
    )


def _has_complete_primary_constraint_inputs(
    simulation_result: SimulationResult,
    scenario: Scenario,
) -> bool:
    if (
        simulation_result.daily_energy_demand <= FLOATING_POINT_TOLERANCE
        and not simulation_result.charging_requests
    ):
        return True

    return (
        len(simulation_result.charging_requests) == scenario.vehicles
        and len(simulation_result.requested_charger_slots_by_timestep)
        == TIMESTEPS_PER_DAY
        and len(simulation_result.waiting_vehicle_count_by_timestep)
        == TIMESTEPS_PER_DAY
    )


def _has_ambiguous_request_level_reasons(
    simulation_result: SimulationResult,
) -> bool:
    for request in simulation_result.charging_requests:
        if request.delayed_start_reason == MIXED_CONSTRAINT_REASON:
            return True
        if request.unmet_energy_reason == MIXED_CONSTRAINT_REASON:
            return True
    return False


def _has_direct_availability_limitation(
    scenario: Scenario,
    simulation_result: SimulationResult,
) -> bool:
    if (
        scenario.charger_count == 0
        and simulation_result.daily_energy_demand > FLOATING_POINT_TOLERANCE
    ):
        return True

    if len(simulation_result.requested_charger_slots_by_timestep) == TIMESTEPS_PER_DAY:
        if any(
            requested_slot_count > scenario.charger_count
            for requested_slot_count in simulation_result.requested_charger_slots_by_timestep
        ):
            return True

    if len(simulation_result.waiting_vehicle_count_by_timestep) == TIMESTEPS_PER_DAY:
        if any(
            waiting_vehicle_count > 0
            for waiting_vehicle_count in simulation_result.waiting_vehicle_count_by_timestep
        ):
            return True

    return any(
        request.unmet_energy_reason == CHARGER_AVAILABILITY_CONSTRAINT_REASON
        and request.charging_start_timestep is None
        and request.arrival_timestep != request.departure_timestep
        for request in simulation_result.charging_requests
    )


def _has_direct_charger_power_limitation(
    simulation_result: SimulationResult,
) -> bool:
    return any(
        request.unmet_energy_reason == CHARGER_POWER_CONSTRAINT_REASON
        for request in simulation_result.charging_requests
    )


def _has_direct_grid_connection_capacity_limitation(
    scenario: Scenario,
    simulation_result: SimulationResult,
) -> bool:
    if (
        scenario.grid_capacity <= FLOATING_POINT_TOLERANCE
        and simulation_result.daily_energy_demand > FLOATING_POINT_TOLERANCE
    ):
        return True

    return any(
        request.unmet_energy_reason
        == GRID_CONNECTION_CAPACITY_CONSTRAINT_REASON
        for request in simulation_result.charging_requests
    )


def _has_non_window_constraint_evidence(
    scenario: Scenario,
    simulation_result: SimulationResult,
) -> bool:
    return (
        _has_direct_availability_limitation(scenario, simulation_result)
        or _has_direct_charger_power_limitation(simulation_result)
        or _has_direct_grid_connection_capacity_limitation(
            scenario,
            simulation_result,
        )
    )


def _calculate_ample_charger_count(scenario: Scenario) -> int:
    """Return a deterministic charger count that removes physical slot scarcity."""

    return max(scenario.charger_count, scenario.vehicles)


def _calculate_ample_charger_power_kw(scenario: Scenario) -> float:
    """Return a deterministic per-charger power level for counterfactual reruns."""

    if scenario.daily_energy_per_vehicle <= FLOATING_POINT_TOLERANCE:
        return max(scenario.charger_power, 0.0)

    return max(
        scenario.charger_power,
        scenario.daily_energy_per_vehicle / get_timestep_hours(),
    )


def _calculate_ample_grid_capacity_kw(
    scenario: Scenario,
    *,
    ample_charger_count: int,
    ample_charger_power_kw: float,
) -> float:
    """Return a deterministic grid capacity that avoids artificial site limits."""

    return max(
        scenario.grid_capacity,
        ample_charger_count * ample_charger_power_kw,
    )


def _planning_margin_multiplier(planning_margin_percent: float) -> float:
    """Return the scaling factor for a percentage planning margin."""

    return 1.0 + planning_margin_percent / PERCENT_MULTIPLIER
