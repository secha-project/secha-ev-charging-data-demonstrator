from __future__ import annotations

from collections.abc import Iterable

from scenarios import Scenario
from simulation.result import ChargingRequestResult
from simulation.time import (
    TIMESTEPS_PER_DAY,
    get_time_window_indices,
    time_to_timestep_index,
)

FLOATING_POINT_TOLERANCE_KWH = 1e-9


def build_request_timestep_series(
    scenario: Scenario,
    charging_requests: Iterable[ChargingRequestResult],
) -> dict[str, list[int]]:
    """Build full-day timestep series from deterministic request outcomes."""

    requests = list(charging_requests)
    arrivals_count_by_timestep = [0] * TIMESTEPS_PER_DAY
    charging_start_count_by_timestep = [0] * TIMESTEPS_PER_DAY
    charging_completion_count_by_timestep = [0] * TIMESTEPS_PER_DAY
    requested_charger_slots_by_timestep = [0] * TIMESTEPS_PER_DAY
    occupied_charger_count_by_timestep = [0] * TIMESTEPS_PER_DAY
    waiting_vehicle_count_by_timestep = [0] * TIMESTEPS_PER_DAY

    for request in requests:
        arrivals_count_by_timestep[request.arrival_timestep] += 1

        if not _requires_physical_charger_slot(request):
            continue

        if request.charging_start_timestep is not None:
            charging_start_count_by_timestep[request.charging_start_timestep] += 1

        if request.charging_completion_timestep is not None:
            charging_completion_count_by_timestep[
                request.charging_completion_timestep
            ] += 1

    charging_window_indices = get_time_window_indices(
        scenario.charging_window_start,
        scenario.charging_window_end,
    )
    active_release_count_by_position = [0] * len(charging_window_indices)
    arrival_count_by_position = [0] * len(charging_window_indices)
    charging_start_count_by_position = [0] * len(charging_window_indices)
    waiting_departure_count_by_position = [0] * len(charging_window_indices)
    window_position_by_timestep = {
        timestep: position
        for position, timestep in enumerate(charging_window_indices)
    }
    charging_window_end_timestep = time_to_timestep_index(scenario.charging_window_end)

    for request in requests:
        if not _requires_physical_charger_slot(request):
            continue

        arrival_position = window_position_by_timestep.get(request.arrival_timestep)
        if arrival_position is not None:
            arrival_count_by_position[arrival_position] += 1

        if request.charging_start_timestep is None:
            waiting_departure_position = _resolve_waiting_departure_position(
                request=request,
                window_position_by_timestep=window_position_by_timestep,
                charging_window_end_timestep=charging_window_end_timestep,
                charging_window_length=len(charging_window_indices),
            )
            if waiting_departure_position is not None:
                waiting_departure_count_by_position[waiting_departure_position] += 1
            continue

        charging_start_position = window_position_by_timestep.get(
            request.charging_start_timestep
        )
        if charging_start_position is not None:
            charging_start_count_by_position[charging_start_position] += 1

        release_position = _resolve_release_position(
            request=request,
            window_position_by_timestep=window_position_by_timestep,
            charging_window_end_timestep=charging_window_end_timestep,
            charging_window_length=len(charging_window_indices),
        )
        if release_position is not None:
            active_release_count_by_position[release_position] += 1

        waiting_departure_position = _resolve_waiting_departure_position(
            request=request,
            window_position_by_timestep=window_position_by_timestep,
            charging_window_end_timestep=charging_window_end_timestep,
            charging_window_length=len(charging_window_indices),
        )
        if waiting_departure_position is not None:
            waiting_departure_count_by_position[waiting_departure_position] += 1

    active_request_count = 0
    waiting_request_count = 0

    for position, timestep in enumerate(charging_window_indices):
        active_request_count -= active_release_count_by_position[position]
        waiting_request_count += arrival_count_by_position[position]
        waiting_request_count -= waiting_departure_count_by_position[position]
        waiting_request_count -= charging_start_count_by_position[position]
        active_request_count += charging_start_count_by_position[position]

        requested_charger_slots_by_timestep[timestep] = (
            active_request_count + waiting_request_count
        )
        occupied_charger_count_by_timestep[timestep] = active_request_count
        waiting_vehicle_count_by_timestep[timestep] = waiting_request_count

    return {
        "arrivals_count_by_timestep": arrivals_count_by_timestep,
        "charging_start_count_by_timestep": charging_start_count_by_timestep,
        "charging_completion_count_by_timestep": charging_completion_count_by_timestep,
        "requested_charger_slots_by_timestep": requested_charger_slots_by_timestep,
        "occupied_charger_count_by_timestep": occupied_charger_count_by_timestep,
        "waiting_vehicle_count_by_timestep": waiting_vehicle_count_by_timestep,
    }


def _requires_physical_charger_slot(request: ChargingRequestResult) -> bool:
    return request.energy_requested_kwh > FLOATING_POINT_TOLERANCE_KWH


def _resolve_release_position(
    request: ChargingRequestResult,
    window_position_by_timestep: dict[int, int],
    charging_window_end_timestep: int,
    charging_window_length: int,
) -> int | None:
    if request.charging_start_timestep is None:
        return None

    release_timestep = request.charging_completion_timestep
    if release_timestep is None:
        release_timestep = request.departure_timestep

    if release_timestep == charging_window_end_timestep:
        return None

    charging_start_position = window_position_by_timestep.get(request.charging_start_timestep)
    release_position = window_position_by_timestep.get(release_timestep)

    if charging_start_position is None or release_position is None:
        return None

    if release_position <= charging_start_position:
        return None

    if release_position >= charging_window_length:
        return None

    return release_position


def _resolve_waiting_departure_position(
    request: ChargingRequestResult,
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
