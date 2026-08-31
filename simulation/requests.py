"""Deterministic charging-request generators for queueing-ready simulations."""

import math

from scenarios import DepartureMode, Scenario
from simulation.arrivals import generate_arrivals_count_by_timestep
from simulation.result import ChargingRequestResult
from simulation.time import (
    TIMESTEP_MINUTES,
    TIMESTEPS_PER_DAY,
    get_time_window_indices,
    time_to_timestep_index,
)


def generate_charging_requests(
    scenario: Scenario,
    arrivals_count_by_timestep: list[int] | None = None,
) -> list[ChargingRequestResult]:
    """Return one deterministic charging request per vehicle for one day.

    Requests are generated directly from the per-timestep arrival counts and are
    ordered first by arrival timestep and then by ascending ``vehicle_index``.
    This stable ordering defines the later FIFO-ready ordering for vehicles
    that arrive in the same timestep.

    This phase creates request identities, arrival timing, departure deadlines,
    and requested energy only. Charging outcome fields remain at neutral
    defaults until charger assignment is implemented in later phases.
    """
    if arrivals_count_by_timestep is None:
        arrivals_count_by_timestep = generate_arrivals_count_by_timestep(scenario)

    _validate_arrivals_count_by_timestep(
        arrivals_count_by_timestep,
        expected_vehicle_count=scenario.vehicles,
    )

    request_timings: list[tuple[int, int]] = []
    departure_adjustment_timestep_count_by_vehicle_index = (
        _build_request_departure_adjustments(scenario)
    )
    window_end_departure_context = _build_window_end_departure_context(scenario)

    for arrival_timestep, arrival_count in enumerate(arrivals_count_by_timestep):
        for _ in range(arrival_count):
            vehicle_index = len(request_timings)
            request_timings.append(
                (
                    arrival_timestep,
                    _resolve_departure_timestep(
                        scenario,
                        arrival_timestep,
                        departure_adjustment_timestep_count_by_vehicle_index[
                            vehicle_index
                        ],
                        window_end_departure_context=window_end_departure_context,
                    ),
                )
            )

    energy_requested_kwh_by_vehicle_index = _build_request_energy_targets(
        scenario,
        request_timings=request_timings,
    )

    charging_requests: list[ChargingRequestResult] = []
    for vehicle_index, (
        arrival_timestep,
        departure_timestep,
    ) in enumerate(request_timings):
        charging_requests.append(
            ChargingRequestResult(
                request_id=f"request-{vehicle_index}",
                vehicle_index=vehicle_index,
                arrival_timestep=arrival_timestep,
                departure_timestep=departure_timestep,
                charging_start_timestep=None,
                charging_completion_timestep=None,
                energy_requested_kwh=energy_requested_kwh_by_vehicle_index[
                    vehicle_index
                ],
                energy_delivered_kwh=0.0,
                unmet_energy_kwh=0.0,
                waiting_time_hours=None,
                not_started_within_window=False,
                delayed_start_reason=None,
                unmet_energy_reason=None,
                strategy_extended_occupancy=None,
            )
        )

    return charging_requests


def _validate_arrivals_count_by_timestep(
    arrivals_count_by_timestep: list[int],
    *,
    expected_vehicle_count: int,
) -> None:
    """Reject malformed arrival-count series before creating requests."""
    if len(arrivals_count_by_timestep) != TIMESTEPS_PER_DAY:
        raise ValueError(
            "arrivals_count_by_timestep must contain one full simulated day."
        )

    for arrival_count in arrivals_count_by_timestep:
        if not isinstance(arrival_count, int):
            raise TypeError("arrivals_count_by_timestep values must be integers.")
        if arrival_count < 0:
            raise ValueError(
                "arrivals_count_by_timestep values must be non-negative."
            )

    if sum(arrivals_count_by_timestep) != expected_vehicle_count:
        raise ValueError(
            "arrivals_count_by_timestep total must match scenario vehicle count."
        )


def _resolve_departure_timestep(
    scenario: Scenario,
    arrival_timestep: int,
    departure_adjustment_timestep_count: int,
    *,
    window_end_departure_context: tuple[list[int], dict[int, int], int] | None,
) -> int:
    if scenario.departure_mode is DepartureMode.WINDOW_END:
        return _resolve_window_end_departure_timestep(
            arrival_timestep,
            departure_advance_timestep_count=departure_adjustment_timestep_count,
            window_end_departure_context=window_end_departure_context,
        )

    session_dwell_timestep_count = scenario.session_dwell_minutes // TIMESTEP_MINUTES
    resolved_session_dwell_timestep_count = max(
        1,
        session_dwell_timestep_count + departure_adjustment_timestep_count,
    )
    return (
        arrival_timestep + resolved_session_dwell_timestep_count
    ) % TIMESTEPS_PER_DAY


def _build_request_energy_targets(
    scenario: Scenario,
    *,
    request_timings: list[tuple[int, int]] | None = None,
) -> list[float]:
    """Return one deterministic per-request energy target list."""
    if scenario.vehicles == 0:
        return []

    if (
        scenario.vehicles == 1
        or scenario.request_energy_variability_percent <= 0
    ):
        if scenario.departure_mode is not DepartureMode.SESSION_DWELL:
            return [scenario.daily_energy_per_vehicle] * scenario.vehicles

    total_requested_energy_kwh = scenario.vehicles * scenario.daily_energy_per_vehicle
    request_energy_weights = _build_request_energy_weights(
        scenario,
        request_timings=request_timings,
    )
    if all(weight == 0 for weight in request_energy_weights):
        return [0.0] * scenario.vehicles

    total_request_energy_weight = sum(request_energy_weights)
    raw_energy_targets = [
        total_requested_energy_kwh * weight / total_request_energy_weight
        for weight in request_energy_weights
    ]
    rounded_energy_targets = [
        round(energy_target_kwh, 4)
        for energy_target_kwh in raw_energy_targets[:-1]
    ]
    rounded_energy_targets.append(
        round(
            total_requested_energy_kwh - sum(rounded_energy_targets),
            4,
        )
    )
    return rounded_energy_targets


def _build_request_energy_weights(
    scenario: Scenario,
    *,
    request_timings: list[tuple[int, int]] | None = None,
) -> list[float]:
    variability_fraction = scenario.request_energy_variability_percent / 100
    variability_weights = [
        1 + variability_fraction * _normalized_request_position(
            vehicle_index,
            scenario.vehicles,
        )
        for vehicle_index in range(scenario.vehicles)
    ]

    if scenario.departure_mode is not DepartureMode.SESSION_DWELL:
        return variability_weights

    if request_timings is None:
        raise ValueError(
            "request_timings are required when session-dwell energy weighting is used."
        )

    dwell_timestep_counts = [
        (departure_timestep - arrival_timestep) % TIMESTEPS_PER_DAY
        for arrival_timestep, departure_timestep in request_timings
    ]
    return [
        variability_weight * max(dwell_timestep_count, 1)
        for variability_weight, dwell_timestep_count in zip(
            variability_weights,
            dwell_timestep_counts,
            strict=True,
        )
    ]


def _build_request_departure_adjustments(scenario: Scenario) -> list[int]:
    """Return deterministic per-request departure adjustments in timesteps."""
    if scenario.vehicles == 0:
        return []

    spread_timestep_count = (
        scenario.departure_time_spread_minutes // TIMESTEP_MINUTES
    )
    if scenario.vehicles == 1 or spread_timestep_count <= 0:
        return [0] * scenario.vehicles

    if scenario.departure_mode is DepartureMode.WINDOW_END:
        return [
            _round_half_up_non_negative(
                spread_timestep_count
                * (scenario.vehicles - 1 - vehicle_index)
                / (scenario.vehicles - 1)
            )
            for vehicle_index in range(scenario.vehicles)
        ]

    return [
        _round_half_away_from_zero(
            spread_timestep_count
            * _normalized_request_position(vehicle_index, scenario.vehicles)
        )
        for vehicle_index in range(scenario.vehicles)
    ]


def _build_window_end_departure_context(
    scenario: Scenario,
) -> tuple[list[int], dict[int, int], int] | None:
    if scenario.departure_mode is not DepartureMode.WINDOW_END:
        return None

    charging_window_indices = get_time_window_indices(
        scenario.charging_window_start,
        scenario.charging_window_end,
    )
    return (
        charging_window_indices,
        {
            timestep: position
            for position, timestep in enumerate(charging_window_indices)
        },
        time_to_timestep_index(scenario.charging_window_end),
    )


def _resolve_window_end_departure_timestep(
    arrival_timestep: int,
    *,
    departure_advance_timestep_count: int,
    window_end_departure_context: tuple[list[int], dict[int, int], int] | None,
) -> int:
    if window_end_departure_context is None:
        raise ValueError(
            "window_end_departure_context is required for window-end departures."
        )

    (
        charging_window_indices,
        window_position_by_timestep,
        charging_window_end_timestep,
    ) = window_end_departure_context

    if departure_advance_timestep_count <= 0:
        return charging_window_end_timestep

    arrival_position = window_position_by_timestep.get(arrival_timestep)
    if arrival_position is None:
        return charging_window_end_timestep

    desired_departure_position = max(
        len(charging_window_indices) - departure_advance_timestep_count,
        0,
    )
    resolved_departure_position = max(
        desired_departure_position,
        arrival_position + 1,
    )

    if resolved_departure_position >= len(charging_window_indices):
        return charging_window_end_timestep

    return charging_window_indices[resolved_departure_position]


def _normalized_request_position(vehicle_index: int, vehicle_count: int) -> float:
    if vehicle_count <= 1:
        return 0.0

    return ((2 * vehicle_index) / (vehicle_count - 1)) - 1


def _round_half_up_non_negative(value: float) -> int:
    return int(math.floor(value + 0.5))


def _round_half_away_from_zero(value: float) -> int:
    if value >= 0:
        return int(math.floor(value + 0.5))

    return -int(math.floor(abs(value) + 0.5))
