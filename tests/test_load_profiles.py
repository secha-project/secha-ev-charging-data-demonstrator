from datetime import time

import pytest

from scenarios import Scenario, default_scenario
from simulation import (
    calculate_available_site_capacity,
    calculate_daily_energy_demand,
    calculate_delivered_energy,
)
from simulation.load_profiles import (
    calculate_unmet_energy,
    generate_smart_load_profile,
    generate_uncontrolled_load_profile,
)
from simulation.time import (
    TIMESTEPS_PER_DAY,
    get_timestep_hours,
    get_time_window_indices,
    time_to_timestep_index,
)


def test_uncontrolled_load_profile_contains_one_value_per_timestep():
    profile = generate_uncontrolled_load_profile(
        default_scenario,
        capacity_limit_kw=calculate_available_site_capacity(default_scenario),
    )

    assert len(profile) == TIMESTEPS_PER_DAY
    assert all(load >= 0 for load in profile)


def test_uncontrolled_load_profile_never_exceeds_available_capacity():
    available_capacity = calculate_available_site_capacity(default_scenario)
    profile = generate_uncontrolled_load_profile(
        default_scenario,
        capacity_limit_kw=available_capacity,
    )

    assert all(load <= available_capacity for load in profile)


def test_uncontrolled_load_profile_preserves_energy_when_capacity_allows():
    profile = generate_uncontrolled_load_profile(
        default_scenario,
        capacity_limit_kw=calculate_available_site_capacity(default_scenario),
    )
    delivered_energy = calculate_delivered_energy(profile)

    assert delivered_energy == calculate_daily_energy_demand(default_scenario)


def test_calculate_delivered_energy_uses_timestep_hours():
    load_profile = [100.0, 50.0]

    assert calculate_delivered_energy(load_profile) == 150.0 * get_timestep_hours()


def test_uncontrolled_load_profile_starts_at_charging_window_start():
    scenario = Scenario(
        vehicles=5,
        daily_energy_per_vehicle=50.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=500.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(16, 0),
    )

    profile = generate_uncontrolled_load_profile(
        scenario,
        capacity_limit_kw=calculate_available_site_capacity(scenario),
    )

    start_index = time_to_timestep_index(time(8, 0))
    positive_indices = [index for index, load in enumerate(profile) if load > 0.0]

    assert profile[:start_index] == [0.0] * start_index
    assert positive_indices[0] == start_index
    assert positive_indices == list(
        range(start_index, start_index + len(positive_indices))
    )
    assert max(profile) == 100.0
    assert min(load for load in profile if load > 0.0) == 50.0
    assert calculate_delivered_energy(profile) == calculate_daily_energy_demand(
        scenario
    )


def test_uncontrolled_load_profile_wraps_across_midnight():
    profile = generate_uncontrolled_load_profile(
        default_scenario,
        capacity_limit_kw=calculate_available_site_capacity(default_scenario),
    )

    active_indices = get_time_window_indices(time(17, 0), time(0, 30))
    assert all(0.0 < profile[index] <= 1000.0 for index in active_indices)
    assert max(profile[index] for index in active_indices) == 1000.0
    charging_window_indices = set(
        get_time_window_indices(
            default_scenario.charging_window_start,
            default_scenario.charging_window_end,
        )
    )
    positive_indices = {
        index for index, load in enumerate(profile) if load > 0.0
    }
    assert positive_indices.issubset(charging_window_indices)
    assert any(index < time_to_timestep_index(time(1, 0)) for index in positive_indices)


def test_uncontrolled_load_profile_stops_at_window_end_when_capacity_is_limited():
    scenario = Scenario(
        vehicles=20,
        daily_energy_per_vehicle=100.0,
        charger_count=1,
        charger_power=100.0,
        grid_capacity=100.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    )

    profile = generate_uncontrolled_load_profile(scenario, capacity_limit_kw=100.0)

    active_indices = get_time_window_indices(time(22, 0), time(2, 0))
    assert all(profile[index] == 100.0 for index in active_indices)
    assert sum(load > 0.0 for load in profile) == len(active_indices)
    assert calculate_delivered_energy(profile) == 400.0


def test_smart_load_profile_contains_one_value_per_timestep():
    profile = generate_smart_load_profile(
        default_scenario,
        capacity_limit_kw=calculate_available_site_capacity(default_scenario),
    )

    assert len(profile) == TIMESTEPS_PER_DAY
    assert all(load >= 0 for load in profile)


def test_smart_load_profile_spreads_energy_with_lower_peak_than_uncontrolled():
    scenario = Scenario(
        vehicles=4,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=80.0,
        grid_capacity=500.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
    )

    profile = generate_smart_load_profile(scenario, capacity_limit_kw=500.0)
    uncontrolled_profile = generate_uncontrolled_load_profile(
        scenario,
        capacity_limit_kw=500.0,
    )

    active_indices = get_time_window_indices(time(8, 0), time(12, 0))
    assert all(
        profile[index] == 0.0
        for index in range(TIMESTEPS_PER_DAY)
        if index not in active_indices
    )
    assert sum(load > 0.0 for load in profile) == len(active_indices)
    assert max(profile) < max(uncontrolled_profile)
    assert max(profile) <= 200.0
    assert calculate_delivered_energy(profile) == calculate_daily_energy_demand(
        scenario
    )


def test_smart_load_profile_never_exceeds_available_capacity():
    available_capacity = calculate_available_site_capacity(default_scenario)
    profile = generate_smart_load_profile(
        default_scenario,
        capacity_limit_kw=available_capacity,
    )

    assert all(load <= available_capacity + 1e-9 for load in profile)


def test_smart_load_profile_wraps_across_midnight():
    scenario = Scenario(
        vehicles=4,
        daily_energy_per_vehicle=100.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=500.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    )

    profile = generate_smart_load_profile(scenario, capacity_limit_kw=500.0)

    active_indices = get_time_window_indices(time(22, 0), time(2, 0))
    assert all(profile[index] == 100.0 for index in active_indices)
    assert sum(load > 0.0 for load in profile) == len(active_indices)
    assert calculate_delivered_energy(profile) == calculate_daily_energy_demand(
        scenario
    )


def test_smart_load_profile_uses_available_capacity_when_power_is_limited():
    scenario = Scenario(
        vehicles=20,
        daily_energy_per_vehicle=100.0,
        charger_count=1,
        charger_power=100.0,
        grid_capacity=100.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    )

    profile = generate_smart_load_profile(scenario, capacity_limit_kw=100.0)
    delivered_energy = calculate_delivered_energy(profile)

    active_indices = get_time_window_indices(time(22, 0), time(2, 0))
    assert all(profile[index] == 100.0 for index in active_indices)
    assert sum(load > 0.0 for load in profile) == len(active_indices)
    assert delivered_energy == 400.0
    assert calculate_unmet_energy(
        calculate_daily_energy_demand(scenario),
        delivered_energy,
    ) == 1600.0


def test_uncontrolled_load_profile_uses_supplied_capacity_limit():
    scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=50.0,
        charger_count=4,
        charger_power=100.0,
        grid_capacity=500.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
    )

    lower_limit_profile = generate_uncontrolled_load_profile(
        scenario,
        capacity_limit_kw=80.0,
    )
    higher_limit_profile = generate_uncontrolled_load_profile(
        scenario,
        capacity_limit_kw=200.0,
    )

    assert lower_limit_profile != higher_limit_profile
    assert max(lower_limit_profile) == pytest.approx(80.0)
    assert max(higher_limit_profile) == 200.0
    active_indices = set(get_time_window_indices(time(8, 0), time(12, 0)))
    assert all(
        lower_limit_profile[index] == 0.0 and higher_limit_profile[index] == 0.0
        for index in range(TIMESTEPS_PER_DAY)
        if index not in active_indices
    )


def test_smart_load_profile_uses_supplied_capacity_limit():
    scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=50.0,
        charger_count=4,
        charger_power=100.0,
        grid_capacity=500.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
    )

    lower_limit_profile = generate_smart_load_profile(
        scenario,
        capacity_limit_kw=80.0,
    )
    higher_limit_profile = generate_smart_load_profile(
        scenario,
        capacity_limit_kw=200.0,
    )

    assert lower_limit_profile != higher_limit_profile
    assert max(lower_limit_profile) == pytest.approx(80.0)
    assert max(higher_limit_profile) > max(lower_limit_profile)
    assert max(higher_limit_profile) <= 200.0
    assert calculate_delivered_energy(higher_limit_profile) == calculate_daily_energy_demand(
        scenario
    )
    active_indices = set(get_time_window_indices(time(8, 0), time(12, 0)))
    assert all(
        lower_limit_profile[index] == 0.0 and higher_limit_profile[index] == 0.0
        for index in range(TIMESTEPS_PER_DAY)
        if index not in active_indices
    )


def test_uncontrolled_load_profile_matches_existing_delivered_behavior_with_available_site_capacity():
    available_capacity = calculate_available_site_capacity(default_scenario)

    profile = generate_uncontrolled_load_profile(
        default_scenario,
        capacity_limit_kw=available_capacity,
    )

    active_indices = get_time_window_indices(time(17, 0), time(0, 30))
    assert all(0.0 < profile[index] <= available_capacity for index in active_indices)
    assert max(profile[index] for index in active_indices) == available_capacity
    charging_window_indices = set(
        get_time_window_indices(
            default_scenario.charging_window_start,
            default_scenario.charging_window_end,
        )
    )
    positive_indices = {
        index for index, load in enumerate(profile) if load > 0.0
    }
    assert positive_indices.issubset(charging_window_indices)
