from datetime import time

from scenarios import (
    ArrivalProfileShape,
    DepartureMode,
    Scenario,
    create_internal_scenario,
)
from simulation import assign_chargers_fifo, generate_charging_requests


def test_all_arrivals_start_immediately_when_enough_chargers_are_available():
    scenario = Scenario(
        vehicles=4,
        daily_energy_per_vehicle=25.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    assigned_requests = assign_chargers_fifo(scenario)

    assert all(
        request.charging_start_timestep == request.arrival_timestep
        for request in assigned_requests
    )
    assert all(
        request.not_started_within_window is False
        for request in assigned_requests
    )
    assert all(
        request.delayed_start_reason == "none"
        for request in assigned_requests
    )


def test_request_completes_and_releases_charger_when_power_and_time_are_sufficient():
    scenario = Scenario(
        vehicles=1,
        daily_energy_per_vehicle=25.0,
        charger_count=1,
        charger_power=100.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    assigned_requests = assign_chargers_fifo(scenario)

    assert len(assigned_requests) == 1
    assert assigned_requests[0].charging_start_timestep == 32
    assert assigned_requests[0].charging_completion_timestep == 33
    assert assigned_requests[0].energy_delivered_kwh == 25.0
    assert assigned_requests[0].unmet_energy_kwh == 0.0
    assert assigned_requests[0].delayed_start_reason == "none"
    assert assigned_requests[0].unmet_energy_reason == "none"


def test_waiting_request_starts_after_earlier_request_completes_and_releases_charger():
    scenario = Scenario(
        vehicles=2,
        daily_energy_per_vehicle=25.0,
        charger_count=1,
        charger_power=100.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    assigned_requests = assign_chargers_fifo(scenario)

    assert [
        (
            request.vehicle_index,
            request.charging_start_timestep,
            request.charging_completion_timestep,
        )
        for request in assigned_requests
    ] == [
        (0, 32, 33),
        (1, 33, 34),
    ]
    assert [request.waiting_time_hours for request in assigned_requests] == [
        0.0,
        0.25,
    ]


def test_earlier_requests_start_first_when_simultaneous_arrivals_exceed_chargers():
    scenario = Scenario(
        vehicles=5,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    assigned_requests = assign_chargers_fifo(scenario)

    assert [
        (request.vehicle_index, request.charging_start_timestep)
        for request in assigned_requests
    ] == [
        (0, 32),
        (1, 32),
        (2, 34),
        (3, 34),
        (4, 36),
    ]
    assert all(
        request.not_started_within_window is False
        for request in assigned_requests
    )


def test_same_timestep_arrivals_follow_stable_vehicle_index_order():
    scenario = Scenario(
        vehicles=5,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    assigned_requests = assign_chargers_fifo(scenario)

    started_vehicle_indices = [
        request.vehicle_index
        for request in assigned_requests
        if request.charging_start_timestep is not None
    ]
    unstarted_vehicle_indices = [
        request.vehicle_index
        for request in assigned_requests
        if request.charging_start_timestep is None
    ]

    assert started_vehicle_indices == [0, 1, 2, 3, 4]
    assert unstarted_vehicle_indices == []


def test_previously_waiting_requests_remain_ahead_of_later_arrivals_in_fifo_order():
    scenario = Scenario(
        vehicles=4,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(10, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
    )

    assigned_requests = assign_chargers_fifo(scenario)

    assert [
        (request.vehicle_index, request.arrival_timestep, request.charging_start_timestep)
        for request in assigned_requests
    ] == [
        (0, 32, 32),
        (1, 33, 34),
        (2, 34, 36),
        (3, 35, 38),
    ]


def test_zero_chargers_cause_no_starts_and_mark_requests_not_started():
    scenario = create_internal_scenario(
        vehicles=4,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    assigned_requests = assign_chargers_fifo(scenario)

    assert all(
        request.charging_start_timestep is None
        for request in assigned_requests
    )
    assert all(
        request.not_started_within_window is True
        for request in assigned_requests
    )
    assert all(
        request.energy_delivered_kwh == 0.0
        for request in assigned_requests
    )
    assert all(
        request.unmet_energy_kwh == request.energy_requested_kwh
        for request in assigned_requests
    )
    assert all(
        request.delayed_start_reason == "charger_availability"
        for request in assigned_requests
    )
    assert all(
        request.unmet_energy_reason == "charger_availability"
        for request in assigned_requests
    )


def test_zero_vehicles_produce_no_assignments():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
    )

    assert assign_chargers_fifo(scenario) == []


def test_repeated_runs_with_identical_inputs_produce_identical_assignments():
    scenario = Scenario(
        vehicles=5,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    first_run = assign_chargers_fifo(scenario)
    second_run = assign_chargers_fifo(scenario)

    assert first_run == second_run


def test_delivered_energy_equals_requested_energy_for_feasible_scenario():
    scenario = Scenario(
        vehicles=2,
        daily_energy_per_vehicle=25.0,
        charger_count=1,
        charger_power=100.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    assigned_requests = assign_chargers_fifo(scenario)

    assert all(
        request.energy_delivered_kwh == request.energy_requested_kwh
        for request in assigned_requests
    )
    assert all(request.unmet_energy_kwh == 0.0 for request in assigned_requests)


def test_delivered_energy_never_exceeds_requested_energy():
    scenario = Scenario(
        vehicles=1,
        daily_energy_per_vehicle=10.0,
        charger_count=1,
        charger_power=100.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    assigned_requests = assign_chargers_fifo(scenario)

    assert assigned_requests[0].energy_delivered_kwh == 10.0
    assert assigned_requests[0].energy_delivered_kwh <= (
        assigned_requests[0].energy_requested_kwh
    )


def test_insufficient_charger_power_produces_unmet_energy_by_deadline():
    scenario = Scenario(
        vehicles=1,
        daily_energy_per_vehicle=100.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    assigned_requests = assign_chargers_fifo(scenario)

    assert assigned_requests[0].charging_start_timestep == 32
    assert assigned_requests[0].charging_completion_timestep is None
    assert assigned_requests[0].energy_delivered_kwh == 50.0
    assert assigned_requests[0].unmet_energy_kwh == 50.0
    assert assigned_requests[0].delayed_start_reason == "none"
    assert assigned_requests[0].unmet_energy_reason == "charger_power"


def test_insufficient_available_site_capacity_produces_unmet_energy_by_deadline():
    scenario = Scenario(
        vehicles=1,
        daily_energy_per_vehicle=50.0,
        charger_count=1,
        charger_power=100.0,
        grid_capacity=25.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    assigned_requests = assign_chargers_fifo(scenario)

    assert assigned_requests[0].energy_delivered_kwh == 25.0
    assert assigned_requests[0].unmet_energy_kwh == 25.0
    assert assigned_requests[0].delayed_start_reason == "none"
    assert assigned_requests[0].unmet_energy_reason == "grid_connection_capacity"


def test_waiting_request_uses_charger_availability_as_delayed_start_reason():
    scenario = Scenario(
        vehicles=2,
        daily_energy_per_vehicle=25.0,
        charger_count=1,
        charger_power=100.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    assigned_requests = assign_chargers_fifo(scenario)

    assert assigned_requests[0].delayed_start_reason == "none"
    assert assigned_requests[1].delayed_start_reason == "charger_availability"
    assert assigned_requests[1].unmet_energy_reason == "none"


def test_short_window_case_classifies_conservatively_from_current_raw_facts():
    scenario = Scenario(
        vehicles=1,
        daily_energy_per_vehicle=30.0,
        charger_count=1,
        charger_power=100.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(8, 15),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    assigned_requests = assign_chargers_fifo(scenario)

    assert assigned_requests[0].energy_delivered_kwh == 25.0
    assert assigned_requests[0].unmet_energy_kwh == 5.0
    assert assigned_requests[0].unmet_energy_reason == "charger_power"


def test_ambiguous_unmet_case_uses_mixed_reason():
    scenario = Scenario(
        vehicles=2,
        daily_energy_per_vehicle=30.0,
        charger_count=1,
        charger_power=100.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(8, 45),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    assigned_requests = assign_chargers_fifo(scenario)

    assert assigned_requests[0].unmet_energy_reason == "none"
    assert assigned_requests[1].delayed_start_reason == "charger_availability"
    assert assigned_requests[1].unmet_energy_reason == "mixed"


def test_zero_energy_requests_complete_safely_without_unmet_energy():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=100.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )
    zero_energy_request = generate_charging_requests(scenario)[0]
    zero_energy_request = zero_energy_request.__class__(
        request_id=zero_energy_request.request_id,
        vehicle_index=zero_energy_request.vehicle_index,
        arrival_timestep=zero_energy_request.arrival_timestep,
        departure_timestep=zero_energy_request.departure_timestep,
        charging_start_timestep=zero_energy_request.charging_start_timestep,
        charging_completion_timestep=zero_energy_request.charging_completion_timestep,
        energy_requested_kwh=0.0,
        energy_delivered_kwh=zero_energy_request.energy_delivered_kwh,
        unmet_energy_kwh=zero_energy_request.unmet_energy_kwh,
        waiting_time_hours=zero_energy_request.waiting_time_hours,
        not_started_within_window=zero_energy_request.not_started_within_window,
        delayed_start_reason=zero_energy_request.delayed_start_reason,
        unmet_energy_reason=zero_energy_request.unmet_energy_reason,
    )

    assigned_requests = assign_chargers_fifo(scenario, [zero_energy_request])

    assert assigned_requests[0].charging_start_timestep == 32
    assert assigned_requests[0].charging_completion_timestep == 32
    assert assigned_requests[0].energy_delivered_kwh == 0.0
    assert assigned_requests[0].unmet_energy_kwh == 0.0
    assert assigned_requests[0].waiting_time_hours == 0.0
    assert assigned_requests[0].not_started_within_window is False
    assert assigned_requests[0].delayed_start_reason == "none"
    assert assigned_requests[0].unmet_energy_reason == "none"


def test_varying_request_lengths_create_deterministic_turnover_and_waiting_times():
    scenario = Scenario(
        vehicles=3,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
        request_energy_variability_percent=50.0,
    )

    assigned_requests = assign_chargers_fifo(scenario)

    assert [
        (
            request.vehicle_index,
            request.energy_requested_kwh,
            request.charging_start_timestep,
            request.charging_completion_timestep,
            request.waiting_time_hours,
        )
        for request in assigned_requests
    ] == [
        (0, 10.0, 32, 33, 0.0),
        (1, 20.0, 33, 35, 0.25),
        (2, 30.0, 35, 38, 0.75),
    ]
    assert sum(
        request.energy_delivered_kwh for request in assigned_requests
    ) == 60.0
    assert all(request.unmet_energy_kwh == 0.0 for request in assigned_requests)


def test_departure_deadline_pressure_preserves_fifo_outcomes_from_one_lifecycle():
    scenario = Scenario(
        vehicles=3,
        daily_energy_per_vehicle=50.0,
        charger_count=1,
        charger_power=100.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
        departure_mode=DepartureMode.WINDOW_END,
        departure_time_spread_minutes=30,
    )

    assigned_requests = assign_chargers_fifo(scenario)

    assert [
        (
            request.vehicle_index,
            request.departure_timestep,
            request.charging_start_timestep,
            request.charging_completion_timestep,
            request.energy_delivered_kwh,
            request.unmet_energy_kwh,
            request.waiting_time_hours,
            request.delayed_start_reason,
            request.unmet_energy_reason,
        )
        for request in assigned_requests
    ] == [
        (0, 34, 32, 34, 50.0, 0.0, 0.0, "none", "none"),
        (
            1,
            35,
            34,
            None,
            25.0,
            25.0,
            0.5,
            "charger_availability",
            "mixed",
        ),
        (
            2,
            36,
            35,
            None,
            25.0,
            25.0,
            0.75,
            "charger_availability",
            "mixed",
        ),
    ]


def test_assign_chargers_fifo_preserves_request_energy_and_identity_contract():
    scenario = Scenario(
        vehicles=4,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )
    charging_requests = generate_charging_requests(scenario)

    assigned_requests = assign_chargers_fifo(scenario, charging_requests)

    assert [request.request_id for request in assigned_requests] == [
        "request-0",
        "request-1",
        "request-2",
        "request-3",
    ]
    assert all(request.energy_requested_kwh == 20.0 for request in assigned_requests)


def test_dwell_departures_release_active_chargers_and_expire_waiting_requests():
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

    assigned_requests = assign_chargers_fifo(scenario)

    assert [
        (
            request.vehicle_index,
            request.charging_start_timestep,
            request.departure_timestep,
            request.energy_delivered_kwh,
            request.unmet_energy_kwh,
        )
        for request in assigned_requests
    ] == [
        (0, 32, 34, 25.0, 25.0),
        (1, None, 34, 0.0, 50.0),
    ]
    assert assigned_requests[0].charging_completion_timestep is None
    assert assigned_requests[0].unmet_energy_reason == "charger_power"
    assert assigned_requests[1].not_started_within_window is True
    assert assigned_requests[1].delayed_start_reason == "charger_availability"
