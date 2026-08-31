"""Strategy-aware simulation engine for EV charging scenarios."""

from dataclasses import dataclass

from scenarios import Scenario

from simulation.formulas import (
    calculate_available_site_capacity,
    calculate_daily_energy_demand,
    calculate_installed_charger_capacity,
    calculate_transformer_loading_percent,
    calculate_transformer_overload_kw,
    calculate_transformer_total_load,
)
from simulation.grid_loading import build_feeder_loading_results
from simulation.assignment import (
    ChargingSimulationInvariantContext,
    build_charging_simulation_invariant_context,
    simulate_charging_requests,
)
from simulation.arrivals import generate_arrivals_count_by_timestep
from simulation.load_profiles import (
    calculate_delivered_energy,
    calculate_unmet_energy,
)
from simulation.power_quality import build_power_quality_result
from simulation.requests import generate_charging_requests
from simulation.result import (
    ChargingRequestResult,
    GridLoadingResult,
    PlannerCandidateSimulationResult,
    SimulationResult,
    TransformerLoadingResult,
)
from simulation.series import build_request_timestep_series
from simulation.time import (
    TIMESTEPS_PER_DAY,
    get_time_window_indices,
    time_to_timestep_index,
)


FLOATING_POINT_TOLERANCE_KWH = 1e-9


@dataclass(frozen=True)
class PlannerCandidateSimulationContext:
    """Scenario-invariant planner inputs reused within one charger search."""

    daily_energy_demand: float
    charging_request_templates: tuple[ChargingRequestResult, ...]
    assignment_invariant_context: ChargingSimulationInvariantContext
    scenario_signature: tuple[tuple[str, object], ...]


def simulate(scenario: Scenario) -> SimulationResult:
    """Transform a validated scenario into raw simulation outputs."""
    daily_energy_demand = calculate_daily_energy_demand(scenario)
    arrivals_count_by_timestep = generate_arrivals_count_by_timestep(scenario)
    charging_requests = generate_charging_requests(
        scenario,
        arrivals_count_by_timestep,
    )
    requested_trace, delivered_trace = _generate_requested_and_delivered_traces(
        scenario,
        charging_requests,
    )
    request_timestep_series = build_request_timestep_series(
        scenario,
        delivered_trace.charging_requests,
    )
    installed_charger_capacity_kw = calculate_installed_charger_capacity(scenario)
    available_site_charging_capacity_kw = calculate_available_site_capacity(scenario)
    delivered_energy = calculate_delivered_energy(delivered_trace.load_profile_kw)
    transformer_loading = _build_transformer_loading_result(
        scenario,
        delivered_trace.load_profile_kw,
    )
    feeder_loading_results = build_feeder_loading_results(
        scenario,
        delivered_trace.load_profile_kw,
    )
    power_quality = build_power_quality_result(
        scenario,
        delivered_trace.load_profile_kw,
    )

    return SimulationResult(
        daily_energy_demand=daily_energy_demand,
        configured_connection_capacity_kw=scenario.grid_capacity,
        installed_charger_capacity_kw=installed_charger_capacity_kw,
        available_site_charging_capacity_kw=available_site_charging_capacity_kw,
        requested_load_profile_kw=requested_trace.load_profile_kw,
        delivered_load_profile_kw=delivered_trace.load_profile_kw,
        delivered_energy=delivered_energy,
        unmet_energy=calculate_unmet_energy(daily_energy_demand, delivered_energy),
        charging_requests=delivered_trace.charging_requests,
        arrivals_count_by_timestep=request_timestep_series[
            "arrivals_count_by_timestep"
        ],
        charging_start_count_by_timestep=request_timestep_series[
            "charging_start_count_by_timestep"
        ],
        charging_completion_count_by_timestep=request_timestep_series[
            "charging_completion_count_by_timestep"
        ],
        requested_charger_slots_by_timestep=request_timestep_series[
            "requested_charger_slots_by_timestep"
        ],
        occupied_charger_count_by_timestep=request_timestep_series[
            "occupied_charger_count_by_timestep"
        ],
        waiting_vehicle_count_by_timestep=request_timestep_series[
            "waiting_vehicle_count_by_timestep"
        ],
        grid_loading=GridLoadingResult(
            transformer_loading=transformer_loading,
            feeder_loading_results=feeder_loading_results,
        ),
        power_quality=power_quality,
    )


def simulate_planner_candidate(
    scenario: Scenario,
    *,
    simulation_context: PlannerCandidateSimulationContext | None = None,
) -> PlannerCandidateSimulationResult:
    """Return the minimal raw outputs needed for charger-planning reruns."""

    resolved_context = simulation_context
    if resolved_context is None:
        resolved_context = build_planner_candidate_simulation_context(scenario)
    else:
        _validate_planner_candidate_simulation_context(
            scenario,
            resolved_context,
        )

    delivered_trace = simulate_charging_requests(
        scenario,
        charging_requests=resolved_context.charging_request_templates,
        charging_strategy=scenario.charging_strategy,
        power_limit_kw=calculate_available_site_capacity(scenario),
        invariant_context=resolved_context.assignment_invariant_context,
    )
    waiting_vehicle_count_by_timestep = (
        _build_planner_candidate_waiting_vehicle_count_by_timestep(
            scenario,
            delivered_trace.charging_requests,
        )
    )
    started_request_waiting_times_hours = [
        request.waiting_time_hours
        for request in delivered_trace.charging_requests
        if request.charging_start_timestep is not None
        and request.waiting_time_hours is not None
    ]
    vehicles_not_started_count = sum(
        request.charging_start_timestep is None
        for request in delivered_trace.charging_requests
    )
    vehicles_with_unmet_energy_count = sum(
        request.unmet_energy_kwh > 0.0
        for request in delivered_trace.charging_requests
    )

    return PlannerCandidateSimulationResult(
        daily_energy_demand=resolved_context.daily_energy_demand,
        request_count=len(delivered_trace.charging_requests),
        started_request_waiting_times_hours=started_request_waiting_times_hours,
        vehicles_waiting_count=sum(
            waiting_time_hours > 0.0
            for waiting_time_hours in started_request_waiting_times_hours
        ),
        vehicles_not_started_count=vehicles_not_started_count,
        vehicles_with_unmet_energy_count=vehicles_with_unmet_energy_count,
        waiting_vehicle_count_by_timestep=waiting_vehicle_count_by_timestep,
    )


def build_planner_candidate_simulation_context(
    scenario: Scenario,
) -> PlannerCandidateSimulationContext:
    """Return the reusable scenario-invariant inputs for planner reruns."""

    daily_energy_demand = calculate_daily_energy_demand(scenario)
    arrivals_count_by_timestep = generate_arrivals_count_by_timestep(scenario)
    charging_requests = generate_charging_requests(
        scenario,
        arrivals_count_by_timestep,
    )

    return PlannerCandidateSimulationContext(
        daily_energy_demand=daily_energy_demand,
        charging_request_templates=tuple(charging_requests),
        assignment_invariant_context=build_charging_simulation_invariant_context(
            scenario,
            charging_requests,
        ),
        scenario_signature=_planner_candidate_context_signature(scenario),
    )


def _validate_planner_candidate_simulation_context(
    scenario: Scenario,
    simulation_context: PlannerCandidateSimulationContext,
) -> None:
    if (
        _planner_candidate_context_signature(scenario)
        == simulation_context.scenario_signature
    ):
        return

    raise ValueError(
        "planner candidate simulation context can only be reused for scenarios "
        "that differ by charger_count."
    )


def _planner_candidate_context_signature(
    scenario: Scenario,
) -> tuple[tuple[str, object], ...]:
    return tuple(
        (
            field_name,
            getattr(scenario, field_name),
        )
        for field_name in (
            "vehicles",
            "daily_energy_per_vehicle",
            "request_energy_variability_percent",
            "charging_window_start",
            "charging_window_end",
            "arrival_window_start",
            "arrival_window_end",
            "arrival_mode",
            "arrival_profile_shape",
            "departure_mode",
            "session_dwell_minutes",
            "departure_time_spread_minutes",
        )
    )


def _build_planner_candidate_waiting_vehicle_count_by_timestep(
    scenario: Scenario,
    charging_requests: list[ChargingRequestResult],
) -> list[int]:
    """Return the planner-only waiting-count series without other timestep data."""

    waiting_vehicle_count_by_timestep = [0] * TIMESTEPS_PER_DAY
    charging_window_indices = get_time_window_indices(
        scenario.charging_window_start,
        scenario.charging_window_end,
    )
    if not charging_window_indices:
        return waiting_vehicle_count_by_timestep

    arrival_count_by_position = [0] * len(charging_window_indices)
    charging_start_count_by_position = [0] * len(charging_window_indices)
    waiting_departure_count_by_position = [0] * len(charging_window_indices)
    window_position_by_timestep = {
        timestep: position
        for position, timestep in enumerate(charging_window_indices)
    }
    charging_window_end_timestep = time_to_timestep_index(
        scenario.charging_window_end
    )

    for request in charging_requests:
        if request.energy_requested_kwh <= FLOATING_POINT_TOLERANCE_KWH:
            continue

        arrival_position = window_position_by_timestep.get(request.arrival_timestep)
        if arrival_position is not None:
            arrival_count_by_position[arrival_position] += 1

        if request.charging_start_timestep is not None:
            charging_start_position = window_position_by_timestep.get(
                request.charging_start_timestep
            )
            if charging_start_position is not None:
                charging_start_count_by_position[charging_start_position] += 1
            continue

        waiting_departure_position = _resolve_planner_candidate_waiting_departure_position(
            request,
            window_position_by_timestep=window_position_by_timestep,
            charging_window_end_timestep=charging_window_end_timestep,
            charging_window_length=len(charging_window_indices),
        )
        if waiting_departure_position is not None:
            waiting_departure_count_by_position[waiting_departure_position] += 1

    waiting_request_count = 0
    for position, timestep in enumerate(charging_window_indices):
        waiting_request_count += arrival_count_by_position[position]
        waiting_request_count -= waiting_departure_count_by_position[position]
        waiting_request_count -= charging_start_count_by_position[position]
        waiting_vehicle_count_by_timestep[timestep] = waiting_request_count

    return waiting_vehicle_count_by_timestep


def _resolve_planner_candidate_waiting_departure_position(
    request: ChargingRequestResult,
    *,
    window_position_by_timestep: dict[int, int],
    charging_window_end_timestep: int,
    charging_window_length: int,
) -> int | None:
    if request.charging_start_timestep is not None:
        return None

    if request.departure_timestep == charging_window_end_timestep:
        return None

    arrival_position = window_position_by_timestep.get(request.arrival_timestep)
    departure_position = window_position_by_timestep.get(request.departure_timestep)

    if arrival_position is None or departure_position is None:
        return None

    if departure_position <= arrival_position:
        return None

    if departure_position >= charging_window_length:
        return None

    return departure_position


def _generate_requested_and_delivered_traces(
    scenario: Scenario,
    charging_requests,
):
    """Return requested and delivered traces for one simulation scenario."""
    installed_charger_capacity_kw = calculate_installed_charger_capacity(scenario)
    available_site_charging_capacity_kw = calculate_available_site_capacity(
        scenario
    )
    requested_trace = simulate_charging_requests(
        scenario,
        charging_requests=charging_requests,
        charging_strategy=scenario.charging_strategy,
        power_limit_kw=installed_charger_capacity_kw,
    )
    delivered_trace = simulate_charging_requests(
        scenario,
        charging_requests=charging_requests,
        charging_strategy=scenario.charging_strategy,
        power_limit_kw=available_site_charging_capacity_kw,
    )
    return requested_trace, delivered_trace


def _generate_requested_and_delivered_load_profiles(
    scenario: Scenario,
) -> tuple[list[float], list[float]]:
    """Return requested and delivered profiles for one simulation scenario."""
    charging_requests = generate_charging_requests(
        scenario,
        generate_arrivals_count_by_timestep(scenario),
    )
    requested_trace, delivered_trace = _generate_requested_and_delivered_traces(
        scenario,
        charging_requests,
    )
    return requested_trace.load_profile_kw, delivered_trace.load_profile_kw


def _build_transformer_loading_result(
    scenario: Scenario,
    delivered_load_profile_kw: list[float],
) -> TransformerLoadingResult:
    """Return timestep transformer loading outputs from the delivered EV load."""
    total_load_kw_by_timestep = [
        calculate_transformer_total_load(
            ev_charging_load_kw=load_kw,
            transformer_other_load_kw=scenario.transformer_other_load_kw,
        )
        for load_kw in delivered_load_profile_kw
    ]
    loading_percent_by_timestep = [
        calculate_transformer_loading_percent(
            total_transformer_load_kw=total_load_kw,
            transformer_capacity_kw=scenario.transformer_capacity_kw,
        )
        for total_load_kw in total_load_kw_by_timestep
    ]
    overload_kw_by_timestep = [
        calculate_transformer_overload_kw(
            total_transformer_load_kw=total_load_kw,
            transformer_capacity_kw=scenario.transformer_capacity_kw,
        )
        for total_load_kw in total_load_kw_by_timestep
    ]
    return TransformerLoadingResult(
        total_load_kw_by_timestep=total_load_kw_by_timestep,
        loading_percent_by_timestep=loading_percent_by_timestep,
        overload_kw_by_timestep=overload_kw_by_timestep,
    )
