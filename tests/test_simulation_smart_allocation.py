from collections import deque
from dataclasses import replace
from datetime import time

from scenarios import ArrivalProfileShape, ChargingStrategy, DepartureMode, Scenario
from simulation import simulate
from simulation.assignment import _calculate_smart_power_allocation_step
from simulation.result import ChargingRequestResult
from simulation.time import get_timestep_hours


def test_smart_charging_preserves_arrivals_and_start_order_when_chargers_are_available():
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

    assert smart_result.arrivals_count_by_timestep == uncontrolled_result.arrivals_count_by_timestep
    assert [
        request.vehicle_index
        for request in smart_result.charging_requests
        if request.charging_start_timestep is not None
    ] == [
        request.vehicle_index
        for request in uncontrolled_result.charging_requests
        if request.charging_start_timestep is not None
    ]
    assert [
        request.charging_start_timestep
        for request in smart_result.charging_requests
    ] == [
        request.charging_start_timestep
        for request in uncontrolled_result.charging_requests
    ]
    assert smart_result.waiting_vehicle_count_by_timestep == (
        uncontrolled_result.waiting_vehicle_count_by_timestep
    )


def test_smart_charging_allocates_average_required_power_across_connected_vehicles():
    scenario = Scenario(
        vehicles=2,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
        charging_strategy=ChargingStrategy.SMART,
    )

    result = simulate(scenario)
    active_profile = result.delivered_load_profile_kw[32:36]

    assert active_profile == [50.0, 50.0, 50.0, 50.0]
    assert all(
        request.energy_delivered_kwh == request.energy_requested_kwh
        for request in result.charging_requests
    )


def test_smart_charging_scales_deterministically_when_site_capacity_is_tighter_than_targets():
    scenario = Scenario(
        vehicles=3,
        daily_energy_per_vehicle=50.0,
        charger_count=3,
        charger_power=30.0,
        grid_capacity=60.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
        charging_strategy=ChargingStrategy.SMART,
    )

    result = simulate(scenario)
    active_profile = result.delivered_load_profile_kw[32:36]

    assert active_profile == [60.0, 60.0, 60.0, 60.0]
    assert max(result.delivered_load_profile_kw) <= scenario.grid_capacity
    assert max(result.requested_load_profile_kw) <= (
        scenario.charger_count * scenario.charger_power
    )
    assert all(
        request.energy_delivered_kwh == 20.0
        for request in result.charging_requests
    )


def test_smart_charging_allocation_step_caps_power_by_timestep_demand_and_site_capacity():
    scenario = Scenario(
        vehicles=2,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=60.0,
        grid_capacity=70.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
        charging_strategy=ChargingStrategy.SMART,
    )
    active_requests = {
        0: ChargingRequestResult(
            request_id="request-0",
            vehicle_index=0,
            arrival_timestep=32,
            departure_timestep=36,
            charging_start_timestep=32,
            charging_completion_timestep=None,
            energy_requested_kwh=5.0,
            energy_delivered_kwh=0.0,
            unmet_energy_kwh=5.0,
            waiting_time_hours=None,
            not_started_within_window=False,
            delayed_start_reason="none",
            unmet_energy_reason=None,
        ),
        1: ChargingRequestResult(
            request_id="request-1",
            vehicle_index=1,
            arrival_timestep=32,
            departure_timestep=36,
            charging_start_timestep=32,
            charging_completion_timestep=None,
            energy_requested_kwh=50.0,
            energy_delivered_kwh=0.0,
            unmet_energy_kwh=50.0,
            waiting_time_hours=None,
            not_started_within_window=False,
            delayed_start_reason="none",
            unmet_energy_reason=None,
        ),
    }

    allocation = _calculate_smart_power_allocation_step(
        scenario,
        [0, 1],
        active_requests,
        remaining_window_timestep_count=4,
        power_limit_kw=70.0,
    )
    timestep_hours = get_timestep_hours()

    assert allocation.power_by_vehicle_index == {
        0: 20.0,
        1: 50.0,
    }
    assert sum(allocation.power_by_vehicle_index.values()) == 70.0
    assert all(
        allocated_power_kw <= scenario.charger_power
        for allocated_power_kw in allocation.power_by_vehicle_index.values()
    )
    assert all(
        allocation.power_by_vehicle_index[vehicle_index] * timestep_hours
        <= active_requests[vehicle_index].energy_requested_kwh
        for vehicle_index in active_requests
    )


def test_smart_charging_prioritizes_less_flexible_connected_requests_under_capacity_pressure():
    scenario = Scenario(
        vehicles=2,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=50.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
        charging_strategy=ChargingStrategy.SMART,
    )
    active_requests = {
        0: ChargingRequestResult(
            request_id="request-0",
            vehicle_index=0,
            arrival_timestep=32,
            departure_timestep=34,
            charging_start_timestep=32,
            charging_completion_timestep=None,
            energy_requested_kwh=20.0,
            energy_delivered_kwh=0.0,
            unmet_energy_kwh=20.0,
            waiting_time_hours=None,
            not_started_within_window=False,
            delayed_start_reason="none",
            unmet_energy_reason=None,
        ),
        1: ChargingRequestResult(
            request_id="request-1",
            vehicle_index=1,
            arrival_timestep=32,
            departure_timestep=36,
            charging_start_timestep=32,
            charging_completion_timestep=None,
            energy_requested_kwh=30.0,
            energy_delivered_kwh=0.0,
            unmet_energy_kwh=30.0,
            waiting_time_hours=None,
            not_started_within_window=False,
            delayed_start_reason="none",
            unmet_energy_reason=None,
        ),
    }

    allocation = _calculate_smart_power_allocation_step(
        scenario,
        [0, 1],
        active_requests,
        remaining_window_timestep_count=4,
        current_window_position=0,
        window_position_by_timestep={32: 0, 33: 1, 34: 2, 35: 3},
        charging_window_end_timestep=36,
        power_limit_kw=50.0,
    )

    assert allocation.power_by_vehicle_index == {
        0: 40.0,
        1: 10.0,
    }
    assert allocation.grid_capacity_limited_vehicle_indices == {1}


def test_smart_charging_is_deterministic_across_repeated_runs():
    scenario = Scenario(
        vehicles=3,
        daily_energy_per_vehicle=50.0,
        charger_count=3,
        charger_power=30.0,
        grid_capacity=60.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
        charging_strategy=ChargingStrategy.SMART,
    )

    first_result = simulate(scenario)
    second_result = simulate(scenario)

    assert first_result == second_result


def test_smart_charging_uses_queue_pressure_to_release_initial_blocking_sessions():
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

    assert smart_result.delivered_load_profile_kw[32] == (
        uncontrolled_result.delivered_load_profile_kw[32]
    )
    assert max(smart_result.delivered_load_profile_kw[33:40]) < max(
        uncontrolled_result.delivered_load_profile_kw[33:40]
    )
    assert [
        (
            request.vehicle_index,
            request.charging_start_timestep,
            request.charging_completion_timestep,
        )
        for request in smart_result.charging_requests
    ] == [
        (0, 32, 33),
        (1, 32, 33),
        (2, 33, 40),
        (3, 33, 40),
    ]
    assert all(
        request.energy_delivered_kwh == request.energy_requested_kwh
        for request in smart_result.charging_requests
    )


def test_uncontrolled_requests_do_not_receive_strategy_extended_occupancy_flags():
    result = simulate(
        Scenario(
            vehicles=4,
            daily_energy_per_vehicle=25.0,
            charger_count=2,
            charger_power=100.0,
            grid_capacity=200.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(10, 0),
            charging_strategy=ChargingStrategy.UNCONTROLLED,
        )
    )

    assert all(
        request.strategy_extended_occupancy is None
        for request in result.charging_requests
    )


def test_smart_charging_can_flag_connected_requests_with_strategy_extended_occupancy():
    result = simulate(
        Scenario(
            vehicles=4,
            daily_energy_per_vehicle=25.0,
            charger_count=2,
            charger_power=100.0,
            grid_capacity=200.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(10, 0),
            charging_strategy=ChargingStrategy.SMART,
        )
    )

    assert [
        request.strategy_extended_occupancy
        for request in result.charging_requests
    ] == [None, None, True, True]
    assert [
        (
            request.vehicle_index,
            request.charging_start_timestep,
            request.charging_completion_timestep,
        )
        for request in result.charging_requests
    ] == [
        (0, 32, 33),
        (1, 32, 33),
        (2, 33, 40),
        (3, 33, 40),
    ]
    assert result.delivered_load_profile_kw[32] == 200.0
    assert max(result.delivered_load_profile_kw[33:40]) < 100.0
    assert result.occupied_charger_count_by_timestep[32:40] == [2] * 8


def test_queue_pressure_can_shift_more_power_to_soonest_releasable_connected_request():
    scenario = Scenario(
        vehicles=3,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
        charging_strategy=ChargingStrategy.SMART,
    )
    active_requests = {
        0: ChargingRequestResult(
            request_id="request-0",
            vehicle_index=0,
            arrival_timestep=32,
            departure_timestep=36,
            charging_start_timestep=32,
            charging_completion_timestep=None,
            energy_requested_kwh=10.0,
            energy_delivered_kwh=0.0,
            unmet_energy_kwh=10.0,
            waiting_time_hours=None,
            not_started_within_window=False,
            delayed_start_reason="none",
            unmet_energy_reason=None,
        ),
        1: ChargingRequestResult(
            request_id="request-1",
            vehicle_index=1,
            arrival_timestep=32,
            departure_timestep=36,
            charging_start_timestep=32,
            charging_completion_timestep=None,
            energy_requested_kwh=30.0,
            energy_delivered_kwh=0.0,
            unmet_energy_kwh=30.0,
            waiting_time_hours=None,
            not_started_within_window=False,
            delayed_start_reason="none",
            unmet_energy_reason=None,
        ),
        2: ChargingRequestResult(
            request_id="request-2",
            vehicle_index=2,
            arrival_timestep=32,
            departure_timestep=36,
            charging_start_timestep=None,
            charging_completion_timestep=None,
            energy_requested_kwh=25.0,
            energy_delivered_kwh=0.0,
            unmet_energy_kwh=25.0,
            waiting_time_hours=None,
            not_started_within_window=False,
            delayed_start_reason=None,
            unmet_energy_reason=None,
        ),
    }

    allocation_without_queue = _calculate_smart_power_allocation_step(
        scenario,
        [0, 1],
        {
            0: active_requests[0],
            1: active_requests[1],
        },
        remaining_window_timestep_count=4,
        power_limit_kw=100.0,
    )
    allocation_with_queue = _calculate_smart_power_allocation_step(
        scenario,
        [0, 1],
        active_requests,
        waiting_queue=deque([active_requests[2]]),
        current_timestep=32,
        remaining_window_timestep_count=4,
        current_window_position=0,
        window_position_by_timestep={32: 0, 33: 1, 34: 2, 35: 3},
        charging_window_end_timestep=36,
        power_limit_kw=100.0,
    )

    assert allocation_without_queue.power_by_vehicle_index == {
        0: 20.0,
        1: 30.0,
    }
    assert allocation_with_queue.power_by_vehicle_index[0] > (
        allocation_without_queue.power_by_vehicle_index[0]
    )
    assert allocation_with_queue.power_by_vehicle_index[1] >= (
        allocation_without_queue.power_by_vehicle_index[1]
    )


def test_waiting_before_connection_remains_charger_availability_under_smart():
    result = simulate(
        Scenario(
            vehicles=4,
            daily_energy_per_vehicle=25.0,
            charger_count=2,
            charger_power=100.0,
            grid_capacity=200.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(10, 0),
            charging_strategy=ChargingStrategy.SMART,
        )
    )

    assert result.charging_requests[2].delayed_start_reason == "charger_availability"
    assert result.charging_requests[3].delayed_start_reason == "charger_availability"
    assert result.charging_requests[2].unmet_energy_reason == "none"
    assert result.charging_requests[3].unmet_energy_reason == "none"


def test_feasible_smart_charging_keeps_none_unmet_energy_reasons():
    result = simulate(
        Scenario(
            vehicles=2,
            daily_energy_per_vehicle=25.0,
            charger_count=2,
            charger_power=100.0,
            grid_capacity=200.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(9, 0),
            charging_strategy=ChargingStrategy.SMART,
        )
    )

    assert all(
        request.unmet_energy_reason == "none"
        for request in result.charging_requests
    )
    assert all(
        request.strategy_extended_occupancy is True
        for request in result.charging_requests
    )


def test_ambiguous_smart_constraint_case_keeps_conservative_existing_reason():
    result = simulate(
        Scenario(
            vehicles=2,
            daily_energy_per_vehicle=30.0,
            charger_count=1,
            charger_power=100.0,
            grid_capacity=100.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(8, 45),
            charging_strategy=ChargingStrategy.SMART,
        )
    )

    assert result.charging_requests[0].strategy_extended_occupancy is None
    assert result.charging_requests[0].unmet_energy_reason == "none"
    assert result.charging_requests[1].strategy_extended_occupancy is None
    assert result.charging_requests[1].delayed_start_reason == "charger_availability"
    assert result.charging_requests[1].unmet_energy_reason == "mixed"


def test_uncontrolled_charging_behavior_remains_unchanged():
    scenario = Scenario(
        vehicles=2,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
        charging_strategy=ChargingStrategy.UNCONTROLLED,
    )

    result = simulate(scenario)
    active_profile = result.delivered_load_profile_kw[32:36]

    assert active_profile == [200.0, 0.0, 0.0, 0.0]
    assert all(
        request.charging_completion_timestep == 33
        for request in result.charging_requests
    )


def test_infeasible_smart_charging_retains_unmet_energy_without_changing_deadlines():
    scenario = Scenario(
        vehicles=2,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=40.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
        charging_strategy=ChargingStrategy.SMART,
    )

    result = simulate(scenario)

    assert all(
        request.charging_start_timestep == 32
        for request in result.charging_requests
    )
    assert all(
        request.charging_completion_timestep is None
        for request in result.charging_requests
    )
    assert all(
        request.unmet_energy_kwh > 0.0
        for request in result.charging_requests
    )
    assert max(result.delivered_load_profile_kw) == 40.0


def test_smart_charging_responds_to_deadline_pressure_without_exceeding_site_capacity():
    smart_result = simulate(
        Scenario(
            vehicles=2,
            daily_energy_per_vehicle=25.0,
            charger_count=2,
            charger_power=100.0,
            grid_capacity=50.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(9, 0),
            arrival_window_start=time(8, 0),
            arrival_window_end=time(8, 0),
            arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
            departure_mode=DepartureMode.WINDOW_END,
            departure_time_spread_minutes=30,
            request_energy_variability_percent=20.0,
            charging_strategy=ChargingStrategy.SMART,
        )
    )
    uncontrolled_result = simulate(
        Scenario(
            vehicles=2,
            daily_energy_per_vehicle=25.0,
            charger_count=2,
            charger_power=100.0,
            grid_capacity=50.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(9, 0),
            arrival_window_start=time(8, 0),
            arrival_window_end=time(8, 0),
            arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
            departure_mode=DepartureMode.WINDOW_END,
            departure_time_spread_minutes=30,
            request_energy_variability_percent=20.0,
            charging_strategy=ChargingStrategy.UNCONTROLLED,
        )
    )

    assert smart_result.delivered_load_profile_kw[32:36] == [50.0, 50.0, 50.0, 50.0]
    assert max(smart_result.delivered_load_profile_kw) == 50.0
    assert [
        (
            request.vehicle_index,
            request.departure_timestep,
            request.energy_delivered_kwh,
            request.unmet_energy_kwh,
        )
        for request in smart_result.charging_requests
    ] == [
        (0, 34, 20.0, 0.0),
        (1, 36, 30.0, 0.0),
    ]
    assert uncontrolled_result.charging_requests[0].unmet_energy_kwh == 7.5
    assert uncontrolled_result.charging_requests[1].unmet_energy_kwh == 0.0
