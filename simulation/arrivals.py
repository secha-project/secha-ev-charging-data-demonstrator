"""Deterministic arrival generators for queueing-ready simulation inputs."""

import hashlib
import random

from scenarios import ArrivalMode, ArrivalProfileShape, Scenario
from simulation.time import TIMESTEPS_PER_DAY, get_time_window_indices, time_to_timestep_index


def generate_arrivals_count_by_timestep(scenario: Scenario) -> list[int]:
    """Return one full-day deterministic arrival-count series for a scenario.

    The generator uses the validated scenario arrival window and profile shape
    to produce a full-day count series whose total equals ``scenario.vehicles``.

    Deterministic profile rules:

    * ``front_loaded`` assigns all arrivals to the earliest timestep in the
      arrival window.
    * ``front_weighted`` assigns more arrivals to earlier timesteps while still
      spreading arrivals across the full arrival window.
    * ``mid_peak`` assigns more arrivals around the middle of the arrival
      window using a symmetric deterministic peak.
    * ``even`` distributes arrivals as evenly as possible across the arrival
      window and assigns any remainder to the earliest timesteps first.
    """
    arrivals_count_by_timestep = [0 for _ in range(TIMESTEPS_PER_DAY)]

    if scenario.vehicles == 0:
        return arrivals_count_by_timestep

    arrival_window_indices = _get_arrival_window_indices(scenario)

    if scenario.arrival_mode is ArrivalMode.RANDOM:
        return _generate_random_arrivals_count_by_timestep(
            scenario,
            arrival_window_indices,
            arrivals_count_by_timestep,
        )

    if scenario.arrival_profile_shape is ArrivalProfileShape.FRONT_LOADED:
        arrivals_count_by_timestep[arrival_window_indices[0]] = scenario.vehicles
        return arrivals_count_by_timestep

    if scenario.arrival_profile_shape is ArrivalProfileShape.FRONT_WEIGHTED:
        return _generate_weighted_profile_arrivals_count_by_timestep(
            scenario.vehicles,
            arrival_window_indices,
            arrivals_count_by_timestep,
            _build_front_weighted_profile_weights(len(arrival_window_indices)),
        )

    if scenario.arrival_profile_shape is ArrivalProfileShape.MID_PEAK:
        return _generate_weighted_profile_arrivals_count_by_timestep(
            scenario.vehicles,
            arrival_window_indices,
            arrivals_count_by_timestep,
            _build_mid_peak_profile_weights(len(arrival_window_indices)),
        )

    if scenario.arrival_profile_shape is ArrivalProfileShape.EVEN:
        base_count = scenario.vehicles // len(arrival_window_indices)
        remainder = scenario.vehicles % len(arrival_window_indices)

        for timestep_index in arrival_window_indices:
            arrivals_count_by_timestep[timestep_index] = base_count

        for timestep_index in arrival_window_indices[:remainder]:
            arrivals_count_by_timestep[timestep_index] += 1

        return arrivals_count_by_timestep

    raise ValueError(
        f"Unsupported arrival profile shape: {scenario.arrival_profile_shape!r}."
    )


def _get_arrival_window_indices(scenario: Scenario) -> list[int]:
    """Return arrival timesteps, treating equal arrival endpoints as a point."""
    if scenario.arrival_window_start == scenario.arrival_window_end:
        return [time_to_timestep_index(scenario.arrival_window_start)]

    return get_time_window_indices(
        scenario.arrival_window_start,
        scenario.arrival_window_end,
    )


def _generate_random_arrivals_count_by_timestep(
    scenario: Scenario,
    arrival_window_indices: list[int],
    arrivals_count_by_timestep: list[int],
) -> list[int]:
    """Return a deterministic pseudo-random arrival distribution.

    The public-fast-charging scenario needs more variable arrivals than depot
    charging, but the demonstrator still depends on repeatable comparisons.
    """

    random_generator = random.Random(_build_arrival_mode_seed(scenario))
    weights = _build_random_arrival_weights(
        scenario.arrival_profile_shape,
        len(arrival_window_indices),
    )
    for timestep_index in random_generator.choices(
        arrival_window_indices,
        weights=weights,
        k=scenario.vehicles,
    ):
        arrivals_count_by_timestep[timestep_index] += 1

    return arrivals_count_by_timestep


def _build_random_arrival_weights(
    arrival_profile_shape: ArrivalProfileShape,
    window_length: int,
) -> list[int]:
    """Return weighted-random arrival preferences for one arrival window."""
    if arrival_profile_shape is ArrivalProfileShape.FRONT_LOADED:
        return [
            (window_length - position) ** 2
            for position in range(window_length)
        ]

    if arrival_profile_shape is ArrivalProfileShape.FRONT_WEIGHTED:
        return _build_front_weighted_profile_weights(window_length)

    if arrival_profile_shape is ArrivalProfileShape.MID_PEAK:
        return _build_mid_peak_profile_weights(window_length)

    if arrival_profile_shape is ArrivalProfileShape.EVEN:
        return [1] * window_length

    raise ValueError(
        f"Unsupported arrival profile shape: {arrival_profile_shape!r}."
    )


def _generate_weighted_profile_arrivals_count_by_timestep(
    vehicles: int,
    arrival_window_indices: list[int],
    arrivals_count_by_timestep: list[int],
    weights: list[int],
) -> list[int]:
    """Allocate arrivals across one window using deterministic profile weights."""
    total_weight = sum(weights)
    base_counts: list[int] = []
    remainder_order: list[tuple[float, int, int]] = []

    for position, (timestep_index, weight) in enumerate(
        zip(arrival_window_indices, weights, strict=True)
    ):
        exact_count = (vehicles * weight) / total_weight
        base_count = int(exact_count)
        arrivals_count_by_timestep[timestep_index] = base_count
        base_counts.append(base_count)
        remainder_order.append(
            (
                exact_count - base_count,
                weight,
                position,
            )
        )

    remaining_vehicles = vehicles - sum(base_counts)
    ranked_positions = sorted(
        range(len(remainder_order)),
        key=lambda position: (
            -remainder_order[position][0],
            -remainder_order[position][1],
            remainder_order[position][2],
        ),
    )

    for position in ranked_positions[:remaining_vehicles]:
        timestep_index = arrival_window_indices[position]
        arrivals_count_by_timestep[timestep_index] += 1

    return arrivals_count_by_timestep


def _build_front_weighted_profile_weights(window_length: int) -> list[int]:
    """Return descending weights that favor earlier arrival timesteps."""
    return [window_length - position for position in range(window_length)]


def _build_mid_peak_profile_weights(window_length: int) -> list[int]:
    """Return symmetric triangular weights centered on the arrival window."""
    return [
        min(position + 1, window_length - position)
        for position in range(window_length)
    ]


def _build_arrival_mode_seed(scenario: Scenario) -> int:
    seed_material = "|".join(
        (
            str(scenario.vehicles),
            str(scenario.daily_energy_per_vehicle),
            str(scenario.charger_count),
            str(scenario.charger_power),
            str(scenario.grid_capacity),
            scenario.charging_window_start.isoformat(),
            scenario.charging_window_end.isoformat(),
            scenario.arrival_window_start.isoformat(),
            scenario.arrival_window_end.isoformat(),
            scenario.arrival_mode.value,
            scenario.arrival_profile_shape.value,
            scenario.departure_mode.value,
            str(scenario.session_dwell_minutes),
        )
    )
    return int(hashlib.sha256(seed_material.encode("ascii")).hexdigest()[:16], 16)
