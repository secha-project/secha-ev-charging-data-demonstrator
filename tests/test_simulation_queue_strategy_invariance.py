from dataclasses import replace
from datetime import time

from scenarios import ChargingStrategy, Scenario, create_internal_scenario
from simulation import calculate_delivered_energy, simulate


def test_uncontrolled_and_smart_share_arrival_series_and_request_identity_ordering():
    base_scenario = Scenario(
        vehicles=4,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
    )

    uncontrolled_result = simulate(
        replace(base_scenario, charging_strategy=ChargingStrategy.UNCONTROLLED)
    )
    smart_result = simulate(
        replace(base_scenario, charging_strategy=ChargingStrategy.SMART)
    )

    assert smart_result.arrivals_count_by_timestep == (
        uncontrolled_result.arrivals_count_by_timestep
    )
    assert [request.request_id for request in smart_result.charging_requests] == [
        request.request_id for request in uncontrolled_result.charging_requests
    ]
    assert [request.vehicle_index for request in smart_result.charging_requests] == [
        request.vehicle_index for request in uncontrolled_result.charging_requests
    ]
    assert [
        request.arrival_timestep for request in smart_result.charging_requests
    ] == [
        request.arrival_timestep for request in uncontrolled_result.charging_requests
    ]


def test_simultaneous_arrivals_follow_identical_fifo_start_order_under_both_strategies():
    base_scenario = Scenario(
        vehicles=5,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
    )

    uncontrolled_result = simulate(
        replace(base_scenario, charging_strategy=ChargingStrategy.UNCONTROLLED)
    )
    smart_result = simulate(
        replace(base_scenario, charging_strategy=ChargingStrategy.SMART)
    )

    assert [
        request.vehicle_index
        for request in sorted(
            uncontrolled_result.charging_requests,
            key=lambda request: (
                request.charging_start_timestep
                if request.charging_start_timestep is not None
                else 10**9,
                request.vehicle_index,
            ),
        )
    ] == [
        request.vehicle_index
        for request in sorted(
            smart_result.charging_requests,
            key=lambda request: (
                request.charging_start_timestep
                if request.charging_start_timestep is not None
                else 10**9,
                request.vehicle_index,
            ),
        )
    ]


def test_smart_charging_does_not_allow_later_arrival_to_bypass_earlier_waiting_request():
    smart_result = simulate(
        Scenario(
            vehicles=3,
            daily_energy_per_vehicle=50.0,
            charger_count=1,
            charger_power=100.0,
            grid_capacity=100.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(10, 0),
            charging_strategy=ChargingStrategy.SMART,
        )
    )

    assert [
        (request.vehicle_index, request.arrival_timestep, request.charging_start_timestep)
        for request in smart_result.charging_requests
    ] == [
        (0, 32, 32),
        (1, 32, 34),
        (2, 32, 36),
    ]


def test_both_strategies_respect_same_configured_charger_count_limit():
    base_scenario = Scenario(
        vehicles=6,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
    )

    uncontrolled_result = simulate(
        replace(base_scenario, charging_strategy=ChargingStrategy.UNCONTROLLED)
    )
    smart_result = simulate(
        replace(base_scenario, charging_strategy=ChargingStrategy.SMART)
    )

    assert max(uncontrolled_result.occupied_charger_count_by_timestep) <= 2
    assert max(smart_result.occupied_charger_count_by_timestep) <= 2


def test_strategy_differences_in_later_starts_follow_completion_timing_not_queue_reordering():
    base_scenario = Scenario(
        vehicles=3,
        daily_energy_per_vehicle=50.0,
        charger_count=1,
        charger_power=100.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
    )

    uncontrolled_result = simulate(
        replace(base_scenario, charging_strategy=ChargingStrategy.UNCONTROLLED)
    )
    smart_result = simulate(
        replace(base_scenario, charging_strategy=ChargingStrategy.SMART)
    )

    assert [request.vehicle_index for request in uncontrolled_result.charging_requests] == [
        0,
        1,
        2,
    ]
    assert [request.vehicle_index for request in smart_result.charging_requests] == [
        0,
        1,
        2,
    ]
    assert smart_result.charging_requests[0].charging_completion_timestep >= (
        uncontrolled_result.charging_requests[0].charging_completion_timestep
    )
    assert smart_result.charging_requests[1].charging_start_timestep >= (
        uncontrolled_result.charging_requests[1].charging_start_timestep
    )
    assert smart_result.charging_requests[1].delayed_start_reason == (
        uncontrolled_result.charging_requests[1].delayed_start_reason
    )


def test_queue_aware_smart_charging_does_not_extend_initial_queue_duration():
    base_scenario = Scenario(
        vehicles=4,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
    )

    uncontrolled_result = simulate(
        replace(base_scenario, charging_strategy=ChargingStrategy.UNCONTROLLED)
    )
    smart_result = simulate(
        replace(base_scenario, charging_strategy=ChargingStrategy.SMART)
    )

    assert [
        request.charging_start_timestep
        for request in uncontrolled_result.charging_requests[:2]
    ] == [
        request.charging_start_timestep
        for request in smart_result.charging_requests[:2]
    ] == [32, 32]
    assert [
        request.charging_completion_timestep
        for request in smart_result.charging_requests[:2]
    ] == [
        request.charging_completion_timestep
        for request in uncontrolled_result.charging_requests[:2]
    ]
    assert uncontrolled_result.occupied_charger_count_by_timestep[32:40] == [
        2,
        2,
        0,
        0,
        0,
        0,
        0,
        0,
    ]
    assert smart_result.occupied_charger_count_by_timestep[32:40] == [2] * 8
    assert uncontrolled_result.waiting_vehicle_count_by_timestep[32:40] == [
        2,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ]
    assert smart_result.waiting_vehicle_count_by_timestep[32:40] == [
        2,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ]
    assert [
        request.charging_start_timestep
        for request in smart_result.charging_requests[2:]
    ] == [33, 33]
    assert all(
        request.delayed_start_reason == "charger_availability"
        for request in smart_result.charging_requests[2:]
    )
    assert all(
        request.unmet_energy_reason == "none"
        for request in smart_result.charging_requests
    )


def test_smart_charging_does_not_create_queue_differences_when_capacity_is_abundant():
    base_scenario = Scenario(
        vehicles=2,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )

    uncontrolled_result = simulate(
        replace(base_scenario, charging_strategy=ChargingStrategy.UNCONTROLLED)
    )
    smart_result = simulate(
        replace(base_scenario, charging_strategy=ChargingStrategy.SMART)
    )

    assert uncontrolled_result.arrivals_count_by_timestep == (
        smart_result.arrivals_count_by_timestep
    )
    assert uncontrolled_result.charging_start_count_by_timestep == (
        smart_result.charging_start_count_by_timestep
    )
    assert uncontrolled_result.waiting_vehicle_count_by_timestep == (
        smart_result.waiting_vehicle_count_by_timestep
    )
    assert max(uncontrolled_result.waiting_vehicle_count_by_timestep) == 0
    assert max(smart_result.waiting_vehicle_count_by_timestep) == 0


def test_request_energy_and_delivered_profile_energy_match_for_both_strategies():
    base_scenario = Scenario(
        vehicles=4,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
    )

    for charging_strategy in (
        ChargingStrategy.UNCONTROLLED,
        ChargingStrategy.SMART,
    ):
        result = simulate(
            replace(base_scenario, charging_strategy=charging_strategy)
        )
        delivered_request_energy = sum(
            request.energy_delivered_kwh
            for request in result.charging_requests
        )

        assert calculate_delivered_energy(result.delivered_load_profile_kw) == (
            delivered_request_energy
        )
        assert result.delivered_energy == delivered_request_energy


def test_strategy_comparison_outputs_remain_deterministic_across_repeated_runs():
    base_scenario = Scenario(
        vehicles=4,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
    )

    for charging_strategy in (
        ChargingStrategy.UNCONTROLLED,
        ChargingStrategy.SMART,
    ):
        scenario = replace(base_scenario, charging_strategy=charging_strategy)

        assert simulate(scenario) == simulate(scenario)


def test_zero_vehicles_and_zero_chargers_remain_safe_and_deterministic_across_strategies():
    zero_vehicle_scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        charging_strategy=ChargingStrategy.SMART,
    )
    zero_charger_scenario = create_internal_scenario(
        vehicles=3,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        charging_strategy=ChargingStrategy.SMART,
    )

    zero_vehicle_result = simulate(zero_vehicle_scenario)
    zero_charger_result = simulate(zero_charger_scenario)

    assert zero_vehicle_result.charging_requests == []
    assert set(zero_vehicle_result.arrivals_count_by_timestep) == {0}
    assert set(zero_charger_result.occupied_charger_count_by_timestep) == {0}
    assert all(
        request.charging_start_timestep is None
        for request in zero_charger_result.charging_requests
    )


def test_existing_uncontrolled_behavior_remains_unchanged_for_reference_queue_case():
    result = simulate(
        Scenario(
            vehicles=2,
            daily_energy_per_vehicle=25.0,
            charger_count=1,
            charger_power=100.0,
            grid_capacity=100.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(10, 0),
            charging_strategy=ChargingStrategy.UNCONTROLLED,
        )
    )

    assert [
        (
            request.vehicle_index,
            request.charging_start_timestep,
            request.charging_completion_timestep,
        )
        for request in result.charging_requests
    ] == [
        (0, 32, 33),
        (1, 33, 34),
    ]
