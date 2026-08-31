"""Deterministic request-level charging simulation helpers."""

from __future__ import annotations

import math
from collections import defaultdict, deque
from collections.abc import Iterable
from dataclasses import dataclass, replace

from scenarios import ChargingStrategy, Scenario
from simulation.formulas import (
    calculate_available_site_capacity,
    calculate_installed_charger_capacity,
)
from simulation.requests import generate_charging_requests
from simulation.result import ChargingRequestResult
from simulation.time import (
    TIMESTEPS_PER_DAY,
    get_time_window_indices,
    get_timestep_hours,
)


CHARGER_AVAILABILITY_REASON = "charger_availability"
CHARGER_POWER_REASON = "charger_power"
GRID_CONNECTION_CAPACITY_REASON = "grid_connection_capacity"
CHARGING_WINDOW_REASON = "charging_window"
MIXED_REASON = "mixed"
NO_REASON = "none"
FLOATING_POINT_TOLERANCE_KWH = 1e-9


@dataclass(frozen=True)
class ChargingSimulationTrace:
    """Internal request-lifecycle trace for one deterministic simulation run."""

    charging_requests: list[ChargingRequestResult]
    load_profile_kw: list[float]


@dataclass(frozen=True)
class ChargingSimulationInvariantContext:
    """Scenario-invariant request ordering and window metadata."""

    ordered_requests: tuple[ChargingRequestResult, ...]
    requests_by_arrival_timestep: dict[int, tuple[ChargingRequestResult, ...]]
    charging_window_indices: tuple[int, ...]
    window_position_by_timestep: dict[int, int]
    charging_window_end_timestep: int


@dataclass
class RequestConstraintFacts:
    """Internal raw facts used to classify request-level outcome reasons."""

    delayed_by_charger_availability: bool = False
    saw_charger_power_limit: bool = False
    saw_grid_connection_capacity_limit: bool = False
    shadow_uncontrolled_energy_delivered_kwh: float = 0.0
    strategy_extended_occupancy: bool = False


@dataclass(frozen=True)
class PowerAllocationStep:
    """Deterministic per-timestep power allocation for connected requests."""

    power_by_vehicle_index: dict[int, float]
    charger_power_limited_vehicle_indices: set[int]
    grid_capacity_limited_vehicle_indices: set[int]


@dataclass(frozen=True)
class SmartChargingRequestState:
    """Derived connected-session state used by the smart-charging heuristic."""

    vehicle_index: int
    remaining_energy_kwh: float
    remaining_connection_timestep_count: int
    average_power_needed_kw: float
    current_timestep_max_power_kw: float
    minimum_full_power_timestep_count: int
    flexibility_timestep_count: int
    mandatory_power_kw: float
    smoothing_target_power_kw: float


@dataclass(frozen=True)
class WaitingQueuePressureState:
    """Summary of FIFO waiting pressure used by the smart heuristic."""

    waiting_request_count: int
    waiting_count_pressure: float
    waiting_time_pressure: float
    deadline_pressure: float
    aggregate_pressure: float


def assign_chargers_fifo(
    scenario: Scenario,
    charging_requests: list[ChargingRequestResult] | None = None,
) -> list[ChargingRequestResult]:
    """Return deterministic request outcomes for the scenario's strategy."""
    return simulate_charging_requests(
        scenario,
        charging_requests=charging_requests,
    ).charging_requests


def simulate_charging_requests(
    scenario: Scenario,
    charging_requests: list[ChargingRequestResult] | None = None,
    *,
    charging_strategy: ChargingStrategy | None = None,
    power_limit_kw: float | None = None,
    invariant_context: ChargingSimulationInvariantContext | None = None,
) -> ChargingSimulationTrace:
    """Simulate request starts, charging energy, and load for one scenario.

    Shared timestep event order for every charging strategy:

    1. Release chargers for requests whose completion timestep equals the
       current timestep.
    2. Add newly arrived requests to the back of the FIFO waiting queue.
    3. Resolve zero-energy requests immediately without occupying a charger.
    4. Assign newly available chargers from the front of the FIFO queue.
    5. Allocate power only among already connected requests according to the
       selected charging strategy.
    """
    if charging_requests is None:
        charging_requests = generate_charging_requests(scenario)

    if charging_strategy is None:
        charging_strategy = scenario.charging_strategy
    charging_strategy = _validate_charging_strategy(charging_strategy)

    if power_limit_kw is None:
        power_limit_kw = calculate_available_site_capacity(scenario)

    _validate_power_limit_kw(power_limit_kw)
    effective_power_limit_kw = min(
        power_limit_kw,
        calculate_installed_charger_capacity(scenario),
    )
    load_profile_kw = [0.0] * TIMESTEPS_PER_DAY

    if not charging_requests:
        return ChargingSimulationTrace(
            charging_requests=[],
            load_profile_kw=load_profile_kw,
        )

    resolved_invariant_context = invariant_context
    if resolved_invariant_context is None:
        resolved_invariant_context = build_charging_simulation_invariant_context(
            scenario,
            charging_requests,
        )

    ordered_requests = resolved_invariant_context.ordered_requests
    requests_by_arrival_timestep = (
        resolved_invariant_context.requests_by_arrival_timestep
    )
    updated_requests_by_vehicle_index: dict[int, ChargingRequestResult] = {
        request.vehicle_index: request
        for request in ordered_requests
    }
    request_constraint_facts_by_vehicle_index = {
        request.vehicle_index: RequestConstraintFacts()
        for request in ordered_requests
    }
    waiting_queue: deque[ChargingRequestResult] = deque()
    active_vehicle_indices: list[int] = []
    charging_window_indices = resolved_invariant_context.charging_window_indices
    charging_window_end_timestep = (
        resolved_invariant_context.charging_window_end_timestep
    )
    window_position_by_timestep = (
        resolved_invariant_context.window_position_by_timestep
    )

    for position, current_timestep in enumerate(charging_window_indices):
        active_vehicle_indices = _release_completed_active_requests(
            active_vehicle_indices,
            updated_requests_by_vehicle_index,
            current_timestep,
            charging_window_end_timestep=charging_window_end_timestep,
        )

        waiting_queue.extend(
            requests_by_arrival_timestep.get(current_timestep, [])
        )
        waiting_queue = _expire_departed_waiting_requests(
            waiting_queue,
            current_timestep=current_timestep,
            charging_window_end_timestep=charging_window_end_timestep,
        )

        waiting_queue = _complete_zero_energy_requests(
            waiting_queue,
            updated_requests_by_vehicle_index,
            current_timestep,
        )

        available_charger_slots = max(
            scenario.charger_count - len(active_vehicle_indices),
            0,
        )

        active_vehicle_indices = _assign_available_chargers_fifo(
            waiting_queue=waiting_queue,
            active_vehicle_indices=active_vehicle_indices,
            updated_requests_by_vehicle_index=updated_requests_by_vehicle_index,
            request_constraint_facts_by_vehicle_index=(
                request_constraint_facts_by_vehicle_index
            ),
            current_timestep=current_timestep,
            available_charger_slots=available_charger_slots,
        )

        load_profile_kw[current_timestep] = _deliver_energy_for_active_requests(
            scenario,
            active_vehicle_indices,
            updated_requests_by_vehicle_index,
            request_constraint_facts_by_vehicle_index,
            waiting_queue,
            current_timestep=current_timestep,
            remaining_window_timestep_count=len(charging_window_indices) - position,
            current_window_position=position,
            window_position_by_timestep=window_position_by_timestep,
            charging_window_end_timestep=charging_window_end_timestep,
            charging_strategy=charging_strategy,
            power_limit_kw=effective_power_limit_kw,
        )

    for request in ordered_requests:
        updated_request = updated_requests_by_vehicle_index[request.vehicle_index]
        if updated_request.charging_start_timestep is None:
            updated_requests_by_vehicle_index[request.vehicle_index] = replace(
                updated_request,
                charging_start_timestep=None,
                charging_completion_timestep=None,
                energy_delivered_kwh=0.0,
                unmet_energy_kwh=updated_request.energy_requested_kwh,
                not_started_within_window=True,
                delayed_start_reason=CHARGER_AVAILABILITY_REASON,
                unmet_energy_reason=CHARGER_AVAILABILITY_REASON,
                strategy_extended_occupancy=None,
            )
            continue

        updated_requests_by_vehicle_index[request.vehicle_index] = replace(
            updated_request,
            delayed_start_reason=updated_request.delayed_start_reason or NO_REASON,
            unmet_energy_reason=_resolve_unmet_energy_reason(
                updated_request,
                request_constraint_facts_by_vehicle_index[request.vehicle_index],
            ),
            strategy_extended_occupancy=(
                True
                if request_constraint_facts_by_vehicle_index[
                    request.vehicle_index
                ].strategy_extended_occupancy
                else None
            ),
        )

    return ChargingSimulationTrace(
        charging_requests=[
            updated_requests_by_vehicle_index[request.vehicle_index]
            for request in ordered_requests
        ],
        load_profile_kw=load_profile_kw,
    )


def build_charging_simulation_invariant_context(
    scenario: Scenario,
    charging_requests: list[ChargingRequestResult] | tuple[ChargingRequestResult, ...],
) -> ChargingSimulationInvariantContext:
    """Return reusable request ordering and charging-window metadata."""

    ordered_requests = tuple(
        sorted(
            charging_requests,
            key=lambda request: (request.arrival_timestep, request.vehicle_index),
        )
    )
    grouped_requests = _group_requests_by_arrival_timestep(ordered_requests)
    charging_window_indices = tuple(
        get_time_window_indices(
            scenario.charging_window_start,
            scenario.charging_window_end,
        )
    )
    charging_window_end_timestep = 0
    if charging_window_indices:
        charging_window_end_timestep = (
            charging_window_indices[-1] + 1
        ) % TIMESTEPS_PER_DAY

    return ChargingSimulationInvariantContext(
        ordered_requests=ordered_requests,
        requests_by_arrival_timestep={
            timestep: tuple(requests)
            for timestep, requests in grouped_requests.items()
        },
        charging_window_indices=charging_window_indices,
        window_position_by_timestep={
            timestep: position
            for position, timestep in enumerate(charging_window_indices)
        },
        charging_window_end_timestep=charging_window_end_timestep,
    )


def _release_completed_active_requests(
    active_vehicle_indices: list[int],
    updated_requests_by_vehicle_index: dict[int, ChargingRequestResult],
    current_timestep: int,
    *,
    charging_window_end_timestep: int,
) -> list[int]:
    return [
        vehicle_index
        for vehicle_index in active_vehicle_indices
        if not _request_releases_at_timestep(
            updated_requests_by_vehicle_index[vehicle_index],
            current_timestep,
            charging_window_end_timestep=charging_window_end_timestep,
        )
    ]


def _request_releases_at_timestep(
    request: ChargingRequestResult,
    current_timestep: int,
    *,
    charging_window_end_timestep: int,
) -> bool:
    return (
        request.charging_completion_timestep == current_timestep
        or (
            request.departure_timestep == current_timestep
            and request.departure_timestep != charging_window_end_timestep
        )
    )


def _expire_departed_waiting_requests(
    waiting_queue: deque[ChargingRequestResult],
    *,
    current_timestep: int,
    charging_window_end_timestep: int,
) -> deque[ChargingRequestResult]:
    remaining_queue: deque[ChargingRequestResult] = deque()

    while waiting_queue:
        request = waiting_queue.popleft()
        if (
            request.departure_timestep == current_timestep
            and request.departure_timestep != charging_window_end_timestep
        ):
            continue

        remaining_queue.append(request)

    return remaining_queue


def _assign_available_chargers_fifo(
    *,
    waiting_queue: deque[ChargingRequestResult],
    active_vehicle_indices: list[int],
    updated_requests_by_vehicle_index: dict[int, ChargingRequestResult],
    request_constraint_facts_by_vehicle_index: dict[int, RequestConstraintFacts],
    current_timestep: int,
    available_charger_slots: int,
) -> list[int]:
    updated_active_vehicle_indices = list(active_vehicle_indices)

    while available_charger_slots > 0 and waiting_queue:
        request = waiting_queue.popleft()
        updated_requests_by_vehicle_index[request.vehicle_index] = replace(
            updated_requests_by_vehicle_index[request.vehicle_index],
            charging_start_timestep=current_timestep,
            waiting_time_hours=_calculate_waiting_time_hours(
                request.arrival_timestep,
                current_timestep,
            ),
            not_started_within_window=False,
            delayed_start_reason=_resolve_delayed_start_reason(
                request.arrival_timestep,
                current_timestep,
            ),
        )
        if current_timestep != request.arrival_timestep:
            request_constraint_facts_by_vehicle_index[
                request.vehicle_index
            ].delayed_by_charger_availability = True
        updated_active_vehicle_indices.append(request.vehicle_index)
        available_charger_slots -= 1

    return updated_active_vehicle_indices


def _group_requests_by_arrival_timestep(
    charging_requests: Iterable[ChargingRequestResult],
) -> dict[int, list[ChargingRequestResult]]:
    grouped_requests: dict[int, list[ChargingRequestResult]] = defaultdict(list)
    for request in charging_requests:
        grouped_requests[request.arrival_timestep].append(request)
    return grouped_requests


def _complete_zero_energy_requests(
    waiting_queue: deque[ChargingRequestResult],
    updated_requests_by_vehicle_index: dict[int, ChargingRequestResult],
    current_timestep: int,
) -> deque[ChargingRequestResult]:
    remaining_queue: deque[ChargingRequestResult] = deque()

    while waiting_queue:
        request = waiting_queue.popleft()
        if request.energy_requested_kwh <= FLOATING_POINT_TOLERANCE_KWH:
            updated_requests_by_vehicle_index[request.vehicle_index] = replace(
                updated_requests_by_vehicle_index[request.vehicle_index],
                charging_start_timestep=current_timestep,
                charging_completion_timestep=current_timestep,
                energy_delivered_kwh=0.0,
                unmet_energy_kwh=0.0,
                waiting_time_hours=_calculate_waiting_time_hours(
                    request.arrival_timestep,
                    current_timestep,
                ),
                not_started_within_window=False,
                delayed_start_reason=NO_REASON,
                unmet_energy_reason=NO_REASON,
            )
            continue

        remaining_queue.append(request)

    return remaining_queue


def _deliver_energy_for_active_requests(
    scenario: Scenario,
    active_vehicle_indices: list[int],
    updated_requests_by_vehicle_index: dict[int, ChargingRequestResult],
    request_constraint_facts_by_vehicle_index: dict[int, RequestConstraintFacts],
    waiting_queue: deque[ChargingRequestResult],
    *,
    current_timestep: int,
    remaining_window_timestep_count: int,
    current_window_position: int,
    window_position_by_timestep: dict[int, int],
    charging_window_end_timestep: int,
    charging_strategy: ChargingStrategy,
    power_limit_kw: float,
) -> float:
    if not active_vehicle_indices:
        return 0.0

    if power_limit_kw <= 0:
        for vehicle_index in active_vehicle_indices:
            request_constraint_facts_by_vehicle_index[
                vehicle_index
            ].saw_grid_connection_capacity_limit = True
        return 0.0

    power_allocation_step = _calculate_power_allocation_step(
        scenario,
        active_vehicle_indices,
        updated_requests_by_vehicle_index,
        waiting_queue=waiting_queue,
        current_timestep=current_timestep,
        remaining_window_timestep_count=remaining_window_timestep_count,
        current_window_position=current_window_position,
        window_position_by_timestep=window_position_by_timestep,
        charging_window_end_timestep=charging_window_end_timestep,
        charging_strategy=charging_strategy,
        power_limit_kw=power_limit_kw,
    )
    uncontrolled_reference_step = None
    if charging_strategy == ChargingStrategy.SMART:
        uncontrolled_reference_step = _calculate_uncontrolled_power_allocation_step(
            scenario,
            active_vehicle_indices,
            updated_requests_by_vehicle_index,
            power_limit_kw=power_limit_kw,
        )
    timestep_hours = get_timestep_hours()
    completion_timestep = (current_timestep + 1) % TIMESTEPS_PER_DAY
    delivered_load_kw = 0.0

    for vehicle_index in active_vehicle_indices:
        request = updated_requests_by_vehicle_index[vehicle_index]
        request_constraint_facts = request_constraint_facts_by_vehicle_index[
            vehicle_index
        ]
        requested_power_kw = power_allocation_step.power_by_vehicle_index[
            vehicle_index
        ]
        remaining_energy_kwh = max(
            request.energy_requested_kwh - request.energy_delivered_kwh,
            0.0,
        )
        if vehicle_index in power_allocation_step.charger_power_limited_vehicle_indices:
            request_constraint_facts.saw_charger_power_limit = True
        if vehicle_index in power_allocation_step.grid_capacity_limited_vehicle_indices:
            request_constraint_facts.saw_grid_connection_capacity_limit = True

        delivered_increment_kwh = min(
            remaining_energy_kwh,
            requested_power_kw * timestep_hours,
        )
        delivered_energy_kwh = request.energy_delivered_kwh + delivered_increment_kwh
        if (
            delivered_energy_kwh
            > request.energy_requested_kwh - FLOATING_POINT_TOLERANCE_KWH
        ):
            delivered_energy_kwh = request.energy_requested_kwh

        unmet_energy_kwh = max(
            request.energy_requested_kwh - delivered_energy_kwh,
            0.0,
        )
        charging_completion_timestep = request.charging_completion_timestep
        unmet_energy_reason = request.unmet_energy_reason

        if unmet_energy_kwh <= FLOATING_POINT_TOLERANCE_KWH:
            unmet_energy_kwh = 0.0
            charging_completion_timestep = completion_timestep
            unmet_energy_reason = NO_REASON

        if uncontrolled_reference_step is not None:
            _update_strategy_explanation_facts(
                request=request,
                request_constraint_facts=request_constraint_facts,
                reference_power_kw=uncontrolled_reference_step.power_by_vehicle_index[
                    vehicle_index
                ],
                actual_unmet_energy_kwh=unmet_energy_kwh,
                timestep_hours=timestep_hours,
            )

        updated_requests_by_vehicle_index[vehicle_index] = replace(
            request,
            charging_completion_timestep=charging_completion_timestep,
            energy_delivered_kwh=delivered_energy_kwh,
            unmet_energy_kwh=unmet_energy_kwh,
            unmet_energy_reason=unmet_energy_reason,
        )
        delivered_load_kw += delivered_increment_kwh / timestep_hours

    return delivered_load_kw


def _update_strategy_explanation_facts(
    *,
    request: ChargingRequestResult,
    request_constraint_facts: RequestConstraintFacts,
    reference_power_kw: float,
    actual_unmet_energy_kwh: float,
    timestep_hours: float,
) -> None:
    """Track when smart charging clearly extends a connected request."""
    reference_remaining_energy_kwh = max(
        request.energy_requested_kwh
        - request_constraint_facts.shadow_uncontrolled_energy_delivered_kwh,
        0.0,
    )
    reference_delivered_increment_kwh = min(
        reference_remaining_energy_kwh,
        reference_power_kw * timestep_hours,
    )
    request_constraint_facts.shadow_uncontrolled_energy_delivered_kwh = min(
        request.energy_requested_kwh,
        request_constraint_facts.shadow_uncontrolled_energy_delivered_kwh
        + reference_delivered_increment_kwh,
    )

    if (
        not request_constraint_facts.strategy_extended_occupancy
        and request_constraint_facts.shadow_uncontrolled_energy_delivered_kwh
        >= request.energy_requested_kwh - FLOATING_POINT_TOLERANCE_KWH
        and actual_unmet_energy_kwh > FLOATING_POINT_TOLERANCE_KWH
    ):
        request_constraint_facts.strategy_extended_occupancy = True


def _calculate_power_allocation_step(
    scenario: Scenario,
    active_vehicle_indices: list[int],
    updated_requests_by_vehicle_index: dict[int, ChargingRequestResult],
    waiting_queue: deque[ChargingRequestResult],
    *,
    current_timestep: int,
    remaining_window_timestep_count: int,
    current_window_position: int,
    window_position_by_timestep: dict[int, int],
    charging_window_end_timestep: int,
    charging_strategy: ChargingStrategy,
    power_limit_kw: float,
) -> PowerAllocationStep:
    if charging_strategy == ChargingStrategy.SMART:
        return _calculate_smart_power_allocation_step(
            scenario,
            active_vehicle_indices,
            updated_requests_by_vehicle_index,
            waiting_queue=waiting_queue,
            current_timestep=current_timestep,
            remaining_window_timestep_count=remaining_window_timestep_count,
            current_window_position=current_window_position,
            window_position_by_timestep=window_position_by_timestep,
            charging_window_end_timestep=charging_window_end_timestep,
            power_limit_kw=power_limit_kw,
        )

    return _calculate_uncontrolled_power_allocation_step(
        scenario,
        active_vehicle_indices,
        updated_requests_by_vehicle_index,
        power_limit_kw=power_limit_kw,
    )


def _calculate_uncontrolled_power_allocation_step(
    scenario: Scenario,
    active_vehicle_indices: list[int],
    updated_requests_by_vehicle_index: dict[int, ChargingRequestResult],
    *,
    power_limit_kw: float,
) -> PowerAllocationStep:
    aggregate_capacity_limit_kw = min(
        power_limit_kw,
        len(active_vehicle_indices) * scenario.charger_power,
    )
    if aggregate_capacity_limit_kw <= 0:
        return PowerAllocationStep(
            power_by_vehicle_index={
                vehicle_index: 0.0 for vehicle_index in active_vehicle_indices
            },
            charger_power_limited_vehicle_indices=set(),
            grid_capacity_limited_vehicle_indices=set(active_vehicle_indices),
        )

    per_request_power_kw = min(
        scenario.charger_power,
        power_limit_kw / len(active_vehicle_indices),
    )
    requested_power_by_vehicle_index: dict[int, float] = {}
    charger_power_limited_vehicle_indices: set[int] = set()
    grid_capacity_limited_vehicle_indices: set[int] = set()
    timestep_hours = get_timestep_hours()

    for vehicle_index in active_vehicle_indices:
        request = updated_requests_by_vehicle_index[vehicle_index]
        remaining_energy_kwh = max(
            request.energy_requested_kwh - request.energy_delivered_kwh,
            0.0,
        )
        requested_power_kw = min(
            per_request_power_kw,
            remaining_energy_kwh / timestep_hours,
        )
        requested_power_by_vehicle_index[vehicle_index] = requested_power_kw

        if remaining_energy_kwh > requested_power_kw * timestep_hours + FLOATING_POINT_TOLERANCE_KWH:
            if aggregate_capacity_limit_kw < (
                len(active_vehicle_indices) * scenario.charger_power
                - FLOATING_POINT_TOLERANCE_KWH
            ):
                grid_capacity_limited_vehicle_indices.add(vehicle_index)
            elif requested_power_kw >= scenario.charger_power - FLOATING_POINT_TOLERANCE_KWH:
                charger_power_limited_vehicle_indices.add(vehicle_index)

    return PowerAllocationStep(
        power_by_vehicle_index=requested_power_by_vehicle_index,
        charger_power_limited_vehicle_indices=charger_power_limited_vehicle_indices,
        grid_capacity_limited_vehicle_indices=grid_capacity_limited_vehicle_indices,
    )


def _calculate_smart_power_allocation_step(
    scenario: Scenario,
    active_vehicle_indices: list[int],
    updated_requests_by_vehicle_index: dict[int, ChargingRequestResult],
    waiting_queue: deque[ChargingRequestResult] | None = None,
    *,
    current_timestep: int | None = None,
    remaining_window_timestep_count: int,
    current_window_position: int | None = None,
    window_position_by_timestep: dict[int, int] | None = None,
    charging_window_end_timestep: int | None = None,
    power_limit_kw: float,
) -> PowerAllocationStep:
    """Allocate connected smart-charging power from urgency and flexibility.

    The current heuristic uses three deterministic passes:

    1. Protect the least-flexible connected requests first by allocating the
       minimum power each one needs to stay on pace for its own deadline.
    2. If a FIFO queue is building, use waiting-pressure signals to accelerate
       the connected requests most likely to release a charger sooner.
    3. Use any remaining headroom to smooth the connected fleet toward a shared
       planning floor, without exceeding per-charger or per-timestep demand.
    """
    remaining_window_hours = remaining_window_timestep_count * get_timestep_hours()
    if remaining_window_hours <= 0:
        return PowerAllocationStep(
            power_by_vehicle_index={
                vehicle_index: 0.0 for vehicle_index in active_vehicle_indices
            },
            charger_power_limited_vehicle_indices=set(),
            grid_capacity_limited_vehicle_indices=set(),
        )

    charger_power_limited_vehicle_indices: set[int] = set()
    grid_capacity_limited_vehicle_indices: set[int] = set()
    timestep_hours = get_timestep_hours()
    remaining_total_unfinished_energy_kwh = sum(
        max(
            request.energy_requested_kwh - request.energy_delivered_kwh,
            0.0,
        )
        for request in updated_requests_by_vehicle_index.values()
    )
    fleet_average_power_per_connected_request_kw = (
        remaining_total_unfinished_energy_kwh
        / remaining_window_hours
        / len(active_vehicle_indices)
    )
    aggregate_capacity_limit_kw = min(
        power_limit_kw,
        len(active_vehicle_indices) * scenario.charger_power,
    )
    if aggregate_capacity_limit_kw <= 0:
        return PowerAllocationStep(
            power_by_vehicle_index={
                vehicle_index: 0.0 for vehicle_index in active_vehicle_indices
            },
            charger_power_limited_vehicle_indices=set(),
            grid_capacity_limited_vehicle_indices=set(active_vehicle_indices),
        )

    request_states: list[SmartChargingRequestState] = []

    for vehicle_index in active_vehicle_indices:
        request = updated_requests_by_vehicle_index[vehicle_index]
        request_state = _build_smart_charging_request_state(
            scenario,
            request,
            remaining_window_timestep_count=remaining_window_timestep_count,
            current_window_position=current_window_position,
            window_position_by_timestep=window_position_by_timestep,
            charging_window_end_timestep=charging_window_end_timestep,
            fleet_average_power_per_connected_request_kw=(
                fleet_average_power_per_connected_request_kw
            ),
        )
        request_states.append(request_state)

        if (
            request_state.average_power_needed_kw
            > scenario.charger_power + FLOATING_POINT_TOLERANCE_KWH
        ):
            charger_power_limited_vehicle_indices.add(vehicle_index)

    requested_power_by_vehicle_index = {
        vehicle_index: 0.0 for vehicle_index in active_vehicle_indices
    }
    remaining_capacity_kw = _allocate_mandatory_smart_power(
        request_states,
        aggregate_capacity_limit_kw,
        requested_power_by_vehicle_index,
        grid_capacity_limited_vehicle_indices,
    )
    queue_pressure_state = _summarize_waiting_queue_pressure(
        scenario,
        waiting_queue,
        current_timestep=current_timestep,
        remaining_window_timestep_count=remaining_window_timestep_count,
        current_window_position=current_window_position,
        window_position_by_timestep=window_position_by_timestep,
        charging_window_end_timestep=charging_window_end_timestep,
    )
    remaining_capacity_kw = _allocate_queue_relief_smart_power(
        request_states,
        queue_pressure_state,
        remaining_capacity_kw,
        requested_power_by_vehicle_index,
    )
    _allocate_smoothing_smart_power(
        request_states,
        remaining_capacity_kw,
        requested_power_by_vehicle_index,
        grid_capacity_limited_vehicle_indices,
    )

    return PowerAllocationStep(
        power_by_vehicle_index=requested_power_by_vehicle_index,
        charger_power_limited_vehicle_indices=charger_power_limited_vehicle_indices,
        grid_capacity_limited_vehicle_indices=grid_capacity_limited_vehicle_indices,
    )


def _build_smart_charging_request_state(
    scenario: Scenario,
    request: ChargingRequestResult,
    *,
    remaining_window_timestep_count: int,
    current_window_position: int | None,
    window_position_by_timestep: dict[int, int] | None,
    charging_window_end_timestep: int | None,
    fleet_average_power_per_connected_request_kw: float,
) -> SmartChargingRequestState:
    remaining_energy_kwh = max(
        request.energy_requested_kwh - request.energy_delivered_kwh,
        0.0,
    )
    remaining_connection_timestep_count = _resolve_remaining_connection_timestep_count(
        request,
        remaining_window_timestep_count=remaining_window_timestep_count,
        current_window_position=current_window_position,
        window_position_by_timestep=window_position_by_timestep,
        charging_window_end_timestep=charging_window_end_timestep,
    )
    timestep_hours = get_timestep_hours()
    remaining_connection_hours = (
        remaining_connection_timestep_count * timestep_hours
    )
    if remaining_connection_hours <= 0:
        average_power_needed_kw = remaining_energy_kwh / timestep_hours
    else:
        average_power_needed_kw = remaining_energy_kwh / remaining_connection_hours
    current_timestep_max_power_kw = min(
        scenario.charger_power,
        remaining_energy_kwh / timestep_hours,
    )
    minimum_full_power_timestep_count = _calculate_minimum_full_power_timestep_count(
        remaining_energy_kwh,
        scenario.charger_power,
    )
    flexibility_timestep_count = max(
        remaining_connection_timestep_count - minimum_full_power_timestep_count,
        0,
    )
    mandatory_power_kw = min(
        average_power_needed_kw,
        current_timestep_max_power_kw,
    )
    smoothing_target_power_kw = min(
        max(
            mandatory_power_kw,
            fleet_average_power_per_connected_request_kw,
        ),
        current_timestep_max_power_kw,
    )
    return SmartChargingRequestState(
        vehicle_index=request.vehicle_index,
        remaining_energy_kwh=remaining_energy_kwh,
        remaining_connection_timestep_count=remaining_connection_timestep_count,
        average_power_needed_kw=average_power_needed_kw,
        current_timestep_max_power_kw=current_timestep_max_power_kw,
        minimum_full_power_timestep_count=minimum_full_power_timestep_count,
        flexibility_timestep_count=flexibility_timestep_count,
        mandatory_power_kw=mandatory_power_kw,
        smoothing_target_power_kw=smoothing_target_power_kw,
    )


def _summarize_waiting_queue_pressure(
    scenario: Scenario,
    waiting_queue: deque[ChargingRequestResult] | None,
    *,
    current_timestep: int | None,
    remaining_window_timestep_count: int,
    current_window_position: int | None,
    window_position_by_timestep: dict[int, int] | None,
    charging_window_end_timestep: int | None,
) -> WaitingQueuePressureState:
    if not waiting_queue:
        return WaitingQueuePressureState(
            waiting_request_count=0,
            waiting_count_pressure=0.0,
            waiting_time_pressure=0.0,
            deadline_pressure=0.0,
            aggregate_pressure=0.0,
        )

    waiting_request_count = len(waiting_queue)
    waiting_count_pressure = min(
        waiting_request_count / max(scenario.charger_count, 1),
        1.0,
    )

    head_waiting_request = waiting_queue[0]
    waiting_time_pressure = 0.0
    waiting_tolerance_hours = (
        scenario.charger_service_max_waiting_time_minutes / 60
    )
    queue_urgency_factor = 1.0
    if waiting_tolerance_hours > 0:
        queue_urgency_factor = min(
            get_timestep_hours() / waiting_tolerance_hours,
            1.0,
        )
    if current_timestep is not None:
        if scenario.charger_service_max_waiting_time_minutes <= 0:
            waiting_time_pressure = (
                1.0
                if current_timestep != head_waiting_request.arrival_timestep
                else 0.0
            )
        else:
            waiting_time_pressure = min(
                _calculate_waiting_time_hours(
                    head_waiting_request.arrival_timestep,
                    current_timestep,
                )
                / (scenario.charger_service_max_waiting_time_minutes / 60),
                1.0,
            )

    head_remaining_connection_timestep_count = _resolve_remaining_connection_timestep_count(
        head_waiting_request,
        remaining_window_timestep_count=remaining_window_timestep_count,
        current_window_position=current_window_position,
        window_position_by_timestep=window_position_by_timestep,
        charging_window_end_timestep=charging_window_end_timestep,
    )
    if head_remaining_connection_timestep_count <= 0:
        deadline_pressure = 1.0
    else:
        deadline_pressure = min(
            _calculate_minimum_full_power_timestep_count(
                max(head_waiting_request.energy_requested_kwh, 0.0),
                scenario.charger_power,
            )
            / head_remaining_connection_timestep_count,
            1.0,
            )

    aggregate_pressure = max(
        waiting_time_pressure,
        min(
            1.0,
            deadline_pressure
            + (waiting_count_pressure * queue_urgency_factor),
        ),
    )
    return WaitingQueuePressureState(
        waiting_request_count=waiting_request_count,
        waiting_count_pressure=waiting_count_pressure,
        waiting_time_pressure=waiting_time_pressure,
        deadline_pressure=deadline_pressure,
        aggregate_pressure=aggregate_pressure,
    )


def _calculate_minimum_full_power_timestep_count(
    remaining_energy_kwh: float,
    charger_power_kw: float,
) -> int:
    if (
        remaining_energy_kwh <= FLOATING_POINT_TOLERANCE_KWH
        or charger_power_kw <= FLOATING_POINT_TOLERANCE_KWH
    ):
        return 0

    full_power_energy_per_timestep_kwh = charger_power_kw * get_timestep_hours()
    return max(
        math.ceil(
            (
                remaining_energy_kwh - FLOATING_POINT_TOLERANCE_KWH
            )
            / full_power_energy_per_timestep_kwh
        ),
        1,
    )


def _allocate_mandatory_smart_power(
    request_states: list[SmartChargingRequestState],
    aggregate_capacity_limit_kw: float,
    requested_power_by_vehicle_index: dict[int, float],
    grid_capacity_limited_vehicle_indices: set[int],
) -> float:
    remaining_capacity_kw = aggregate_capacity_limit_kw
    flexibility_bands = sorted(
        {
            request_state.flexibility_timestep_count
            for request_state in request_states
        }
    )

    for flexibility_timestep_count in flexibility_bands:
        band_request_states = sorted(
            [
                request_state
                for request_state in request_states
                if request_state.flexibility_timestep_count
                == flexibility_timestep_count
            ],
            key=lambda request_state: (
                request_state.remaining_connection_timestep_count,
                -request_state.average_power_needed_kw,
                request_state.vehicle_index,
            ),
        )
        band_mandatory_power_kw = sum(
            request_state.mandatory_power_kw
            for request_state in band_request_states
        )
        if (
            band_mandatory_power_kw
            <= remaining_capacity_kw + FLOATING_POINT_TOLERANCE_KWH
        ):
            for request_state in band_request_states:
                requested_power_by_vehicle_index[request_state.vehicle_index] = (
                    request_state.mandatory_power_kw
                )
            remaining_capacity_kw -= band_mandatory_power_kw
            continue

        _allocate_proportional_power(
            band_request_states,
            remaining_capacity_kw,
            requested_power_by_vehicle_index,
            target_power_by_vehicle_index={
                request_state.vehicle_index: request_state.mandatory_power_kw
                for request_state in band_request_states
            },
        )
        for request_state in band_request_states:
            if (
                requested_power_by_vehicle_index[request_state.vehicle_index]
                + FLOATING_POINT_TOLERANCE_KWH
                < request_state.mandatory_power_kw
            ):
                grid_capacity_limited_vehicle_indices.add(
                    request_state.vehicle_index
                )
        return 0.0

    return max(remaining_capacity_kw, 0.0)


def _allocate_queue_relief_smart_power(
    request_states: list[SmartChargingRequestState],
    queue_pressure_state: WaitingQueuePressureState,
    remaining_capacity_kw: float,
    requested_power_by_vehicle_index: dict[int, float],
) -> float:
    if (
        remaining_capacity_kw <= FLOATING_POINT_TOLERANCE_KWH
        or queue_pressure_state.aggregate_pressure <= FLOATING_POINT_TOLERANCE_KWH
        or not request_states
    ):
        return max(remaining_capacity_kw, 0.0)

    queue_relief_request_count = min(
        len(request_states),
        queue_pressure_state.waiting_request_count,
        max(
            1,
            math.ceil(
                queue_pressure_state.aggregate_pressure
                * len(request_states)
            ),
        ),
    )
    queue_relief_request_states = sorted(
        request_states,
        key=lambda request_state: (
            request_state.minimum_full_power_timestep_count,
            request_state.remaining_energy_kwh,
            request_state.flexibility_timestep_count,
            request_state.remaining_connection_timestep_count,
            request_state.vehicle_index,
        ),
    )[:queue_relief_request_count]
    return _allocate_prioritized_power(
        queue_relief_request_states,
        remaining_capacity_kw,
        requested_power_by_vehicle_index,
        target_power_by_vehicle_index={
            request_state.vehicle_index: request_state.current_timestep_max_power_kw
            for request_state in queue_relief_request_states
        },
    )


def _allocate_smoothing_smart_power(
    request_states: list[SmartChargingRequestState],
    remaining_capacity_kw: float,
    requested_power_by_vehicle_index: dict[int, float],
    grid_capacity_limited_vehicle_indices: set[int],
) -> None:
    if remaining_capacity_kw <= FLOATING_POINT_TOLERANCE_KWH:
        return

    smoothing_request_states = [
        request_state
        for request_state in sorted(
            request_states,
            key=lambda request_state: (
                request_state.flexibility_timestep_count,
                request_state.remaining_connection_timestep_count,
                -request_state.smoothing_target_power_kw,
                request_state.vehicle_index,
            ),
        )
        if (
            request_state.smoothing_target_power_kw
            - requested_power_by_vehicle_index[request_state.vehicle_index]
            > FLOATING_POINT_TOLERANCE_KWH
        )
    ]
    if not smoothing_request_states:
        return

    _allocate_proportional_power(
        smoothing_request_states,
        remaining_capacity_kw,
        requested_power_by_vehicle_index,
        target_power_by_vehicle_index={
            request_state.vehicle_index: request_state.smoothing_target_power_kw
            for request_state in smoothing_request_states
        },
    )
    for request_state in smoothing_request_states:
        if (
            requested_power_by_vehicle_index[request_state.vehicle_index]
            + FLOATING_POINT_TOLERANCE_KWH
            < request_state.smoothing_target_power_kw
        ):
            grid_capacity_limited_vehicle_indices.add(request_state.vehicle_index)


def _allocate_proportional_power(
    request_states: list[SmartChargingRequestState],
    available_power_kw: float,
    requested_power_by_vehicle_index: dict[int, float],
    *,
    target_power_by_vehicle_index: dict[int, float],
) -> None:
    remaining_power_kw = max(available_power_kw, 0.0)
    power_gap_by_vehicle_index = {
        request_state.vehicle_index: max(
            target_power_by_vehicle_index[request_state.vehicle_index]
            - requested_power_by_vehicle_index[request_state.vehicle_index],
            0.0,
        )
        for request_state in request_states
    }
    remaining_total_gap_kw = sum(power_gap_by_vehicle_index.values())

    if remaining_total_gap_kw <= FLOATING_POINT_TOLERANCE_KWH:
        return

    for index, request_state in enumerate(request_states):
        vehicle_index = request_state.vehicle_index
        power_gap_kw = power_gap_by_vehicle_index[vehicle_index]
        if power_gap_kw <= FLOATING_POINT_TOLERANCE_KWH:
            continue

        if index == len(request_states) - 1:
            additional_power_kw = min(power_gap_kw, remaining_power_kw)
        else:
            additional_power_kw = min(
                power_gap_kw,
                remaining_power_kw * power_gap_kw / remaining_total_gap_kw,
            )
        requested_power_by_vehicle_index[vehicle_index] += additional_power_kw
        remaining_power_kw -= additional_power_kw
        remaining_total_gap_kw -= power_gap_kw
        if remaining_power_kw <= FLOATING_POINT_TOLERANCE_KWH:
            break


def _allocate_prioritized_power(
    request_states: list[SmartChargingRequestState],
    available_power_kw: float,
    requested_power_by_vehicle_index: dict[int, float],
    *,
    target_power_by_vehicle_index: dict[int, float],
) -> float:
    remaining_power_kw = max(available_power_kw, 0.0)

    for request_state in request_states:
        vehicle_index = request_state.vehicle_index
        power_gap_kw = max(
            target_power_by_vehicle_index[vehicle_index]
            - requested_power_by_vehicle_index[vehicle_index],
            0.0,
        )
        if power_gap_kw <= FLOATING_POINT_TOLERANCE_KWH:
            continue

        additional_power_kw = min(power_gap_kw, remaining_power_kw)
        requested_power_by_vehicle_index[vehicle_index] += additional_power_kw
        remaining_power_kw -= additional_power_kw
        if remaining_power_kw <= FLOATING_POINT_TOLERANCE_KWH:
            break

    return max(remaining_power_kw, 0.0)


def _resolve_remaining_connection_timestep_count(
    request: ChargingRequestResult,
    *,
    remaining_window_timestep_count: int,
    current_window_position: int | None,
    window_position_by_timestep: dict[int, int] | None,
    charging_window_end_timestep: int | None,
) -> int:
    if (
        current_window_position is None
        or window_position_by_timestep is None
    ):
        return remaining_window_timestep_count

    if (
        charging_window_end_timestep is not None
        and request.departure_timestep == charging_window_end_timestep
    ):
        return remaining_window_timestep_count

    departure_position = window_position_by_timestep.get(request.departure_timestep)
    if departure_position is None:
        return remaining_window_timestep_count

    remaining_connection_timestep_count = departure_position - current_window_position
    if remaining_connection_timestep_count <= 0:
        return 0

    return min(
        remaining_connection_timestep_count,
        remaining_window_timestep_count,
    )


def _resolve_delayed_start_reason(
    arrival_timestep: int,
    charging_start_timestep: int,
) -> str | None:
    if charging_start_timestep != arrival_timestep:
        return CHARGER_AVAILABILITY_REASON
    return NO_REASON


def _calculate_waiting_time_hours(
    arrival_timestep: int,
    charging_start_timestep: int,
) -> float:
    waiting_timestep_count = (
        charging_start_timestep - arrival_timestep
    ) % TIMESTEPS_PER_DAY
    return waiting_timestep_count * get_timestep_hours()


def _resolve_unmet_energy_reason(
    request: ChargingRequestResult,
    request_constraint_facts: RequestConstraintFacts,
) -> str:
    if request.unmet_energy_kwh <= FLOATING_POINT_TOLERANCE_KWH:
        return NO_REASON

    if request.charging_start_timestep is None:
        return CHARGER_AVAILABILITY_REASON

    contributing_reasons: list[str] = []
    if request_constraint_facts.delayed_by_charger_availability:
        contributing_reasons.append(CHARGER_AVAILABILITY_REASON)
    if request_constraint_facts.saw_charger_power_limit:
        contributing_reasons.append(CHARGER_POWER_REASON)
    if request_constraint_facts.saw_grid_connection_capacity_limit:
        contributing_reasons.append(GRID_CONNECTION_CAPACITY_REASON)

    if not contributing_reasons:
        return CHARGING_WINDOW_REASON

    if len(contributing_reasons) == 1:
        return contributing_reasons[0]

    return MIXED_REASON


def _validate_power_limit_kw(power_limit_kw: float) -> None:
    if power_limit_kw < 0:
        raise ValueError("power_limit_kw must be non-negative.")


def _validate_charging_strategy(
    charging_strategy: ChargingStrategy,
) -> ChargingStrategy:
    if not isinstance(charging_strategy, ChargingStrategy):
        raise ValueError(f"Unsupported charging strategy: {charging_strategy!r}.")
    return charging_strategy
