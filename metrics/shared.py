"""Stable shared metric primitives used across metrics, planning, and capacity code."""

from scenarios import Scenario
from simulation.result import SimulationResult
from simulation.time import TIMESTEPS_PER_DAY, get_time_window_indices, get_timestep_hours


PERCENT_MULTIPLIER = 100.0
DAYS_PER_YEAR = 365.0
FLOATING_POINT_TOLERANCE = 1e-9


def calculate_annual_energy(total_daily_energy: float) -> float:
    """Return annual charging energy in kWh/year."""

    return DAYS_PER_YEAR * total_daily_energy


def calculate_peak_load(load_profile: list[float]) -> float:
    """Return the maximum simulated charging load in kW."""

    if not load_profile:
        return 0.0
    return max(load_profile)


def extract_window_values(
    values: list[float] | list[int],
    scenario: Scenario,
) -> list[float] | list[int]:
    """Return charging-window values while remaining compatible with legacy data."""

    if not values:
        return [0] * len(
            get_time_window_indices(
                scenario.charging_window_start,
                scenario.charging_window_end,
            )
        )

    if len(values) != TIMESTEPS_PER_DAY:
        return list(values)

    charging_window_indices = get_time_window_indices(
        scenario.charging_window_start,
        scenario.charging_window_end,
    )
    return [values[timestep] for timestep in charging_window_indices]


def extract_window_count_values(
    values: list[int],
    scenario: Scenario,
) -> list[int]:
    """Return safe charging-window count values from a full-day raw series."""

    charging_window_indices = get_time_window_indices(
        scenario.charging_window_start,
        scenario.charging_window_end,
    )

    if not values or len(values) != TIMESTEPS_PER_DAY:
        return [0] * len(charging_window_indices)

    return [values[timestep] for timestep in charging_window_indices]


def calculate_average_count(counts: list[float] | list[int]) -> float:
    """Return the mean value for one series or zero when unavailable."""

    if not counts:
        return 0.0
    return sum(counts) / len(counts)


def calculate_average_charger_utilization_percent(
    delivered_window_load_profile_kw: list[float] | list[int],
    installed_charger_capacity_kw: float,
    daily_energy_demand: float,
) -> float | None:
    """Return average charger utilization or an undefined marker when needed."""

    if installed_charger_capacity_kw <= 0:
        if daily_energy_demand <= FLOATING_POINT_TOLERANCE:
            return 0.0
        return None

    return min(
        max(
            calculate_average_count(delivered_window_load_profile_kw)
            / installed_charger_capacity_kw
            * PERCENT_MULTIPLIER,
            0.0,
        ),
        PERCENT_MULTIPLIER,
    )


def calculate_peak_charger_utilization_percent(
    delivered_window_load_profile_kw: list[float] | list[int],
    installed_charger_capacity_kw: float,
    daily_energy_demand: float,
) -> float | None:
    """Return peak charger utilization or an undefined marker when needed."""

    if installed_charger_capacity_kw <= 0:
        if daily_energy_demand <= FLOATING_POINT_TOLERANCE:
            return 0.0
        return None

    return min(
        max(
            max(delivered_window_load_profile_kw, default=0.0)
            / installed_charger_capacity_kw
            * PERCENT_MULTIPLIER,
            0.0,
        ),
        PERCENT_MULTIPLIER,
    )


def collect_started_request_waiting_times(
    simulation_result: SimulationResult,
) -> list[float]:
    """Return waiting times for requests that actually started charging."""

    waiting_times_hours: list[float] = []

    for request in simulation_result.charging_requests:
        if request.charging_start_timestep is None:
            continue

        if request.waiting_time_hours is not None:
            waiting_times_hours.append(request.waiting_time_hours)
            continue

        waiting_timestep_count = (
            request.charging_start_timestep - request.arrival_timestep
        ) % TIMESTEPS_PER_DAY
        waiting_times_hours.append(waiting_timestep_count * get_timestep_hours())

    return waiting_times_hours


def calculate_average_waiting_time_hours(
    started_request_waiting_times_hours: list[float],
    *,
    request_count: int,
) -> float | None:
    """Return the average waiting time for started requests."""

    if request_count == 0:
        return 0.0
    if not started_request_waiting_times_hours:
        return None
    return sum(started_request_waiting_times_hours) / len(
        started_request_waiting_times_hours
    )


def calculate_maximum_waiting_time_hours(
    started_request_waiting_times_hours: list[float],
    *,
    request_count: int,
) -> float | None:
    """Return the maximum waiting time for started requests."""

    if request_count == 0:
        return 0.0
    if not started_request_waiting_times_hours:
        return None
    return max(started_request_waiting_times_hours, default=0.0)


def copy_full_day_count_series(values: list[int]) -> list[int]:
    """Return a stable full-day count series when the raw contract is complete."""

    if len(values) != TIMESTEPS_PER_DAY:
        return []
    return list(values)


def copy_full_day_float_series(values: list[float]) -> list[float]:
    """Return a stable full-day float series when the raw contract is complete."""

    if len(values) != TIMESTEPS_PER_DAY:
        return []
    return list(values)
