from datetime import time

import pytest

from scenarios import Scenario, default_scenario
from simulation.time import (
    HOURS_PER_DAY,
    TIME_INDICES,
    TIMESTEP_HOURS,
    TIMESTEP_MINUTES,
    TIMESTEPS_PER_HOUR,
    TIMESTEPS_PER_DAY,
    calculate_charging_window_duration,
    calculate_time_window_timestep_count,
    format_time_label,
    get_time_indices,
    get_time_labels,
    get_time_window_indices,
    get_timestep_hours,
    get_timestep_minutes,
    time_to_timestep_index,
    timestep_index_to_time,
)


def test_internal_timestep_is_fifteen_minutes():
    assert TIMESTEP_MINUTES == 15
    assert TIMESTEP_HOURS == 0.25
    assert TIMESTEPS_PER_HOUR == 4
    assert get_timestep_minutes() == 15
    assert get_timestep_hours() == 0.25


def test_simulation_timeline_represents_one_complete_day():
    assert HOURS_PER_DAY == 24
    assert TIMESTEPS_PER_DAY == 96
    assert list(TIME_INDICES) == list(range(96))


def test_get_time_indices_returns_quarter_hour_indices_for_day():
    indices = get_time_indices()

    assert indices == list(range(96))


def test_get_time_indices_returns_a_new_list():
    indices = get_time_indices()
    indices.append(96)

    assert get_time_indices() == list(range(96))


def test_get_time_labels_returns_one_label_per_timestep():
    labels = get_time_labels()

    assert len(labels) == TIMESTEPS_PER_DAY
    assert labels[:5] == ["00:00", "00:15", "00:30", "00:45", "01:00"]
    assert labels[-1] == "23:45"


@pytest.mark.parametrize(
    ("clock_time", "expected_index"),
    [
        (time(0, 0), 0),
        (time(0, 14), 0),
        (time(0, 15), 1),
        (time(1, 0), 4),
        (time(8, 0), 32),
        (time(17, 0), 68),
        (time(23, 45), 95),
    ],
)
def test_time_to_timestep_index_uses_shared_quarter_hour_basis(
    clock_time,
    expected_index,
):
    assert time_to_timestep_index(clock_time) == expected_index


@pytest.mark.parametrize(
    ("index", "expected_time"),
    [
        (0, time(0, 0)),
        (1, time(0, 15)),
        (4, time(1, 0)),
        (32, time(8, 0)),
        (68, time(17, 0)),
        (95, time(23, 45)),
        (96, time(0, 0)),
    ],
)
def test_timestep_index_to_time_maps_indices_back_to_clock_times(index, expected_time):
    assert timestep_index_to_time(index) == expected_time


def test_format_time_label_uses_shared_timestep_conversion():
    assert format_time_label(0) == "00:00"
    assert format_time_label(1) == "00:15"
    assert format_time_label(68) == "17:00"
    assert format_time_label(95) == "23:45"


@pytest.mark.parametrize(
    ("start", "end", "expected_duration"),
    [
        (time(8, 0), time(16, 0), 8),
        (time(17, 0), time(6, 0), 13),
        (time(22, 0), time(2, 0), 4),
        (time(0, 0), time(12, 0), 12),
        (time(0, 0), time(0, 0), 24),
    ],
)
def test_calculate_charging_window_duration(start, end, expected_duration):
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        charging_window_start=start,
        charging_window_end=end,
    )

    duration = calculate_charging_window_duration(scenario)

    assert duration == expected_duration
    assert 0 < duration <= HOURS_PER_DAY


@pytest.mark.parametrize(
    ("start", "end", "expected_count"),
    [
        (time(8, 0), time(16, 0), 32),
        (time(17, 0), time(6, 0), 52),
        (time(22, 0), time(2, 0), 16),
        (time(0, 0), time(12, 0), 48),
        (time(0, 0), time(0, 0), 96),
    ],
)
def test_calculate_time_window_timestep_count_matches_internal_resolution(
    start,
    end,
    expected_count,
):
    assert calculate_time_window_timestep_count(start, end) == expected_count


def test_get_time_window_indices_returns_expected_range_for_daytime_window():
    assert get_time_window_indices(time(8, 0), time(9, 0)) == [32, 33, 34, 35]


def test_get_time_window_indices_wraps_across_midnight():
    assert get_time_window_indices(time(23, 30), time(0, 30)) == [94, 95, 0, 1]


def test_default_heavy_duty_charging_window_duration_crosses_midnight():
    assert calculate_charging_window_duration(default_scenario) == 13
