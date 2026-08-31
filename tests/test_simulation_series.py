from datetime import time

from scenarios import (
    ArrivalProfileShape,
    DepartureMode,
    Scenario,
    create_internal_scenario,
)
from simulation import TIMESTEPS_PER_DAY, simulate


def test_timestep_series_match_request_level_events():
    scenario = Scenario(
        vehicles=4,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=40.0,
        grid_capacity=200.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(0, 0),
        arrival_window_start=time(22, 0),
        arrival_window_end=time(22, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    result = simulate(scenario)

    assert len(result.arrivals_count_by_timestep) == TIMESTEPS_PER_DAY
    assert len(result.charging_start_count_by_timestep) == TIMESTEPS_PER_DAY
    assert len(result.charging_completion_count_by_timestep) == TIMESTEPS_PER_DAY
    assert len(result.requested_charger_slots_by_timestep) == TIMESTEPS_PER_DAY
    assert len(result.occupied_charger_count_by_timestep) == TIMESTEPS_PER_DAY
    assert len(result.waiting_vehicle_count_by_timestep) == TIMESTEPS_PER_DAY

    for timestep in range(TIMESTEPS_PER_DAY):
        assert result.arrivals_count_by_timestep[timestep] == sum(
            request.arrival_timestep == timestep
            for request in result.charging_requests
        )
        assert result.charging_start_count_by_timestep[timestep] == sum(
            request.charging_start_timestep == timestep
            for request in result.charging_requests
        )
        assert result.charging_completion_count_by_timestep[timestep] == sum(
            request.charging_completion_timestep == timestep
            for request in result.charging_requests
        )


def test_constrained_fifo_series_show_waiting_and_bounded_occupancy():
    scenario = Scenario(
        vehicles=4,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=40.0,
        grid_capacity=200.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(0, 0),
        arrival_window_start=time(22, 0),
        arrival_window_end=time(22, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    result = simulate(scenario)

    assert max(result.waiting_vehicle_count_by_timestep) > 0
    assert max(result.occupied_charger_count_by_timestep) == scenario.charger_count
    assert all(
        occupied_count <= scenario.charger_count
        for occupied_count in result.occupied_charger_count_by_timestep
    )
    assert max(result.requested_charger_slots_by_timestep) > scenario.charger_count


def test_released_charger_starts_later_request_in_expected_timestep():
    scenario = Scenario(
        vehicles=4,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=40.0,
        grid_capacity=200.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(0, 0),
        arrival_window_start=time(22, 0),
        arrival_window_end=time(22, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    result = simulate(scenario)
    requests = result.charging_requests

    assert requests[0].charging_completion_timestep == requests[1].charging_start_timestep
    assert requests[1].charging_completion_timestep == requests[2].charging_start_timestep
    assert requests[2].charging_completion_timestep == requests[3].charging_start_timestep
    assert max(result.requested_charger_slots_by_timestep) > max(
        result.occupied_charger_count_by_timestep
    )


def test_zero_chargers_produce_zero_occupancy_and_non_negative_waiting_series():
    scenario = create_internal_scenario(
        vehicles=3,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=500.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
        arrival_window_start=time(22, 0),
        arrival_window_end=time(22, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    result = simulate(scenario)

    assert sum(result.charging_start_count_by_timestep) == 0
    assert set(result.occupied_charger_count_by_timestep) == {0}
    assert all(
        waiting_count >= 0
        for waiting_count in result.waiting_vehicle_count_by_timestep
    )
    assert all(
        requested_count >= occupied_count
        for requested_count, occupied_count in zip(
            result.requested_charger_slots_by_timestep,
            result.occupied_charger_count_by_timestep,
            strict=True,
        )
    )


def test_zero_vehicles_produce_all_zero_timestep_series():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=500.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
        arrival_window_start=time(22, 0),
        arrival_window_end=time(22, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    result = simulate(scenario)

    assert set(result.arrivals_count_by_timestep) == {0}
    assert set(result.charging_start_count_by_timestep) == {0}
    assert set(result.charging_completion_count_by_timestep) == {0}
    assert set(result.requested_charger_slots_by_timestep) == {0}
    assert set(result.occupied_charger_count_by_timestep) == {0}
    assert set(result.waiting_vehicle_count_by_timestep) == {0}


def test_timestep_series_are_deterministic_across_repeated_runs():
    scenario = Scenario(
        vehicles=4,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=40.0,
        grid_capacity=200.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(0, 0),
        arrival_window_start=time(22, 0),
        arrival_window_end=time(22, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    first_result = simulate(scenario)
    second_result = simulate(scenario)

    assert first_result.arrivals_count_by_timestep == second_result.arrivals_count_by_timestep
    assert (
        first_result.charging_start_count_by_timestep
        == second_result.charging_start_count_by_timestep
    )
    assert (
        first_result.charging_completion_count_by_timestep
        == second_result.charging_completion_count_by_timestep
    )
    assert (
        first_result.requested_charger_slots_by_timestep
        == second_result.requested_charger_slots_by_timestep
    )
    assert (
        first_result.occupied_charger_count_by_timestep
        == second_result.occupied_charger_count_by_timestep
    )
    assert (
        first_result.waiting_vehicle_count_by_timestep
        == second_result.waiting_vehicle_count_by_timestep
    )


def test_dwell_departures_drop_waiting_and_occupancy_counts_when_requests_leave():
    scenario = Scenario(
        vehicles=2,
        daily_energy_per_vehicle=50.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
        departure_mode=DepartureMode.SESSION_DWELL,
        session_dwell_minutes=30,
    )

    result = simulate(scenario)

    assert result.requested_charger_slots_by_timestep[32:36] == [2, 2, 0, 0]
    assert result.occupied_charger_count_by_timestep[32:36] == [1, 1, 0, 0]
    assert result.waiting_vehicle_count_by_timestep[32:36] == [1, 1, 0, 0]
