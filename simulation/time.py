"""Shared time configuration for formula-based simulations."""

import math
from datetime import time

from scenarios import Scenario

MINUTES_PER_HOUR: int = 60
HOURS_PER_DAY: int = 24
MINUTES_PER_DAY: int = HOURS_PER_DAY * MINUTES_PER_HOUR
SECONDS_PER_MINUTE: int = 60
SECONDS_PER_HOUR: int = MINUTES_PER_HOUR * SECONDS_PER_MINUTE
SECONDS_PER_DAY: int = HOURS_PER_DAY * SECONDS_PER_HOUR

TIMESTEP_MINUTES: int = 15
TIMESTEP_HOURS: float = TIMESTEP_MINUTES / MINUTES_PER_HOUR
TIMESTEPS_PER_HOUR: int = MINUTES_PER_HOUR // TIMESTEP_MINUTES
TIMESTEPS_PER_DAY: int = MINUTES_PER_DAY // TIMESTEP_MINUTES
TIME_INDICES: range = range(TIMESTEPS_PER_DAY)


def get_time_indices() -> list[int]:
    """Return the discrete timestep indices for one complete day."""
    return list(TIME_INDICES)


def get_timestep_hours() -> float:
    """Return the duration of one simulation timestep in hours."""
    return TIMESTEP_HOURS


def get_timestep_minutes() -> int:
    """Return the duration of one simulation timestep in minutes."""
    return TIMESTEP_MINUTES


def get_time_labels() -> list[str]:
    """Return one display label for each simulation timestep in a day."""
    return [format_time_label(index) for index in TIME_INDICES]


def format_time_label(timestep_index: int) -> str:
    """Return an HH:MM label for one simulation timestep index."""
    timestep_time = timestep_index_to_time(timestep_index)
    return timestep_time.strftime("%H:%M")


def time_to_timestep_index(value: time) -> int:
    """Return the containing timestep index for a clock time."""
    minutes_since_midnight = value.hour * MINUTES_PER_HOUR + value.minute
    return minutes_since_midnight // TIMESTEP_MINUTES


def timestep_index_to_time(timestep_index: int) -> time:
    """Return the clock time at the start of one timestep index."""
    normalized_index = timestep_index % TIMESTEPS_PER_DAY
    total_minutes = normalized_index * TIMESTEP_MINUTES
    hour = total_minutes // MINUTES_PER_HOUR
    minute = total_minutes % MINUTES_PER_HOUR
    return time(hour, minute)


def calculate_time_window_duration_minutes(start: time, end: time) -> int:
    """Return the duration of one time window in minutes."""
    start_seconds = _time_to_seconds(start)
    end_seconds = _time_to_seconds(end)

    duration_seconds = end_seconds - start_seconds
    if duration_seconds <= 0:
        duration_seconds += SECONDS_PER_DAY

    return math.ceil(duration_seconds / SECONDS_PER_MINUTE)


def calculate_time_window_duration_hours(start: time, end: time) -> float:
    """Return the duration of one time window in hours."""
    return calculate_time_window_duration_minutes(start, end) / MINUTES_PER_HOUR


def calculate_time_window_timestep_count(start: time, end: time) -> int:
    """Return the number of timesteps covered by one time window."""
    duration_minutes = calculate_time_window_duration_minutes(start, end)
    return math.ceil(duration_minutes / TIMESTEP_MINUTES)


def get_time_window_indices(start: time, end: time) -> list[int]:
    """Return timestep indices covered by one time window."""
    start_index = time_to_timestep_index(start)
    timestep_count = calculate_time_window_timestep_count(start, end)
    return [
        (start_index + offset) % TIMESTEPS_PER_DAY
        for offset in range(timestep_count)
    ]


def calculate_charging_window_duration(scenario: Scenario) -> float:
    """Return the scenario charging window duration in hours."""
    return calculate_time_window_duration_hours(
        scenario.charging_window_start,
        scenario.charging_window_end,
    )


def _time_to_seconds(value: time) -> float:
    return (
        value.hour * SECONDS_PER_HOUR
        + value.minute * SECONDS_PER_MINUTE
        + value.second
        + value.microsecond / 1_000_000
    )
