from datetime import time

from scenarios import ArrivalMode, ArrivalProfileShape, Scenario, create_internal_scenario
from simulation import TIMESTEPS_PER_DAY, generate_arrivals_count_by_timestep


def test_front_loaded_arrivals_total_equals_vehicle_count():
    scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    arrivals = generate_arrivals_count_by_timestep(scenario)

    assert sum(arrivals) == scenario.vehicles


def test_even_arrivals_total_equals_vehicle_count():
    scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
    )

    arrivals = generate_arrivals_count_by_timestep(scenario)

    assert sum(arrivals) == scenario.vehicles


def test_front_weighted_arrivals_total_equals_vehicle_count():
    scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_WEIGHTED,
    )

    arrivals = generate_arrivals_count_by_timestep(scenario)

    assert sum(arrivals) == scenario.vehicles


def test_mid_peak_arrivals_total_equals_vehicle_count():
    scenario = Scenario(
        vehicles=12,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.MID_PEAK,
    )

    arrivals = generate_arrivals_count_by_timestep(scenario)

    assert sum(arrivals) == scenario.vehicles


def test_arrival_series_contains_full_day_of_non_negative_integer_counts():
    scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
    )

    arrivals = generate_arrivals_count_by_timestep(scenario)

    assert len(arrivals) == TIMESTEPS_PER_DAY
    assert all(isinstance(value, int) for value in arrivals)
    assert all(value >= 0 for value in arrivals)


def test_arrivals_occur_only_inside_daytime_arrival_window():
    scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
    )

    arrivals = generate_arrivals_count_by_timestep(scenario)

    assert arrivals[32:36] == [3, 3, 2, 2]
    assert set(arrivals[:32]) == {0}
    assert set(arrivals[36:]) == {0}


def test_front_loaded_places_arrivals_earlier_than_even_for_same_window():
    front_loaded_scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )
    even_scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
    )

    front_loaded_arrivals = generate_arrivals_count_by_timestep(front_loaded_scenario)
    even_arrivals = generate_arrivals_count_by_timestep(even_scenario)

    assert front_loaded_arrivals[32:36] == [10, 0, 0, 0]
    assert even_arrivals[32:36] == [3, 3, 2, 2]
    assert front_loaded_arrivals[32] > even_arrivals[32]


def test_front_weighted_profile_tapers_arrivals_across_the_window():
    scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_WEIGHTED,
    )

    arrivals = generate_arrivals_count_by_timestep(scenario)

    assert arrivals[32:36] == [4, 3, 2, 1]
    assert arrivals[32] > arrivals[33] > arrivals[34] > arrivals[35]


def test_mid_peak_profile_concentrates_arrivals_in_the_middle_of_the_window():
    scenario = Scenario(
        vehicles=12,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.MID_PEAK,
    )

    arrivals = generate_arrivals_count_by_timestep(scenario)

    assert arrivals[32:36] == [2, 4, 4, 2]
    assert arrivals[33] == arrivals[34]
    assert arrivals[33] > arrivals[32]
    assert arrivals[34] > arrivals[35]


def test_even_arrivals_assign_remainder_to_earliest_timesteps():
    scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
    )

    arrivals = generate_arrivals_count_by_timestep(scenario)

    assert arrivals[32:36] == [3, 3, 2, 2]


def test_overnight_arrival_window_distributes_arrivals_across_midnight():
    scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(4, 0),
        arrival_window_start=time(23, 30),
        arrival_window_end=time(0, 30),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
    )

    arrivals = generate_arrivals_count_by_timestep(scenario)

    assert arrivals[94:96] == [3, 3]
    assert arrivals[0:2] == [2, 2]
    assert set(arrivals[2:94]) == {0}
    assert sum(arrivals) == scenario.vehicles


def test_front_weighted_overnight_arrival_window_preserves_cross_midnight_ordering():
    scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(4, 0),
        arrival_window_start=time(23, 30),
        arrival_window_end=time(0, 30),
        arrival_profile_shape=ArrivalProfileShape.FRONT_WEIGHTED,
    )

    arrivals = generate_arrivals_count_by_timestep(scenario)

    assert arrivals[94:96] == [4, 3]
    assert arrivals[0:2] == [2, 1]
    assert set(arrivals[2:94]) == {0}
    assert sum(arrivals) == scenario.vehicles


def test_zero_vehicle_arrivals_return_all_zero_full_day_series():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
    )

    arrivals = generate_arrivals_count_by_timestep(scenario)

    assert arrivals == [0] * TIMESTEPS_PER_DAY


def test_arrival_generator_is_deterministic_for_identical_inputs():
    scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
    )

    first_run = generate_arrivals_count_by_timestep(scenario)
    second_run = generate_arrivals_count_by_timestep(scenario)

    assert first_run == second_run


def test_new_profile_shapes_stay_deterministic_for_identical_inputs():
    front_weighted_scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_WEIGHTED,
    )
    mid_peak_scenario = Scenario(
        vehicles=12,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.MID_PEAK,
    )

    assert generate_arrivals_count_by_timestep(front_weighted_scenario) == (
        generate_arrivals_count_by_timestep(front_weighted_scenario)
    )
    assert generate_arrivals_count_by_timestep(mid_peak_scenario) == (
        generate_arrivals_count_by_timestep(mid_peak_scenario)
    )


def test_random_arrival_mode_stays_deterministic_and_within_the_arrival_window():
    scenario = Scenario(
        vehicles=12,
        daily_energy_per_vehicle=80.0,
        charger_count=6,
        charger_power=300.0,
        grid_capacity=1200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(18, 0),
        arrival_window_start=time(10, 0),
        arrival_window_end=time(12, 0),
        arrival_mode=ArrivalMode.RANDOM,
    )

    first_run = generate_arrivals_count_by_timestep(scenario)
    second_run = generate_arrivals_count_by_timestep(scenario)

    assert first_run == second_run
    assert sum(first_run) == scenario.vehicles
    assert set(first_run[:40]) == {0}
    assert set(first_run[48:]) == {0}
    assert any(value > 0 for value in first_run[40:48])


def test_random_arrival_mode_uses_profile_shape_weighting_rules():
    even_scenario = Scenario(
        vehicles=96,
        daily_energy_per_vehicle=80.0,
        charger_count=6,
        charger_power=300.0,
        grid_capacity=1200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(18, 0),
        arrival_window_start=time(10, 0),
        arrival_window_end=time(12, 0),
        arrival_mode=ArrivalMode.RANDOM,
        arrival_profile_shape=ArrivalProfileShape.EVEN,
    )
    front_weighted_scenario = Scenario(
        vehicles=96,
        daily_energy_per_vehicle=80.0,
        charger_count=6,
        charger_power=300.0,
        grid_capacity=1200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(18, 0),
        arrival_window_start=time(10, 0),
        arrival_window_end=time(12, 0),
        arrival_mode=ArrivalMode.RANDOM,
        arrival_profile_shape=ArrivalProfileShape.FRONT_WEIGHTED,
    )
    mid_peak_scenario = Scenario(
        vehicles=96,
        daily_energy_per_vehicle=80.0,
        charger_count=6,
        charger_power=300.0,
        grid_capacity=1200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(18, 0),
        arrival_window_start=time(10, 0),
        arrival_window_end=time(12, 0),
        arrival_mode=ArrivalMode.RANDOM,
        arrival_profile_shape=ArrivalProfileShape.MID_PEAK,
    )

    even_window_arrivals = generate_arrivals_count_by_timestep(even_scenario)[40:48]
    front_weighted_window_arrivals = generate_arrivals_count_by_timestep(
        front_weighted_scenario
    )[40:48]
    mid_peak_window_arrivals = generate_arrivals_count_by_timestep(mid_peak_scenario)[
        40:48
    ]

    assert sum(front_weighted_window_arrivals[:4]) > sum(
        front_weighted_window_arrivals[4:]
    )
    assert sum(front_weighted_window_arrivals[:4]) > sum(even_window_arrivals[:4])
    assert sum(mid_peak_window_arrivals[2:6]) > (
        sum(mid_peak_window_arrivals[:2]) + sum(mid_peak_window_arrivals[6:])
    )


def test_default_point_arrival_window_puts_all_front_loaded_arrivals_in_one_timestep():
    scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(17, 0),
        charging_window_end=time(6, 0),
    )

    arrivals = generate_arrivals_count_by_timestep(scenario)

    assert arrivals[68] == 10
    assert sum(arrivals) == scenario.vehicles
    assert sum(value > 0 for value in arrivals) == 1
