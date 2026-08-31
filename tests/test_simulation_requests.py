from datetime import time

from scenarios import (
    ArrivalMode,
    ArrivalProfileShape,
    DepartureMode,
    Scenario,
    create_internal_scenario,
)
from simulation import (
    TIMESTEPS_PER_DAY,
    generate_arrivals_count_by_timestep,
    generate_charging_requests,
)


def _build_even_arrival_scenario() -> Scenario:
    return Scenario(
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


def test_request_count_equals_vehicle_count():
    scenario = _build_even_arrival_scenario()

    requests = generate_charging_requests(scenario)

    assert len(requests) == scenario.vehicles


def test_every_vehicle_has_one_unique_deterministic_request_id():
    scenario = _build_even_arrival_scenario()

    requests = generate_charging_requests(scenario)

    assert [request.vehicle_index for request in requests] == list(
        range(scenario.vehicles)
    )
    assert [request.request_id for request in requests] == [
        f"request-{vehicle_index}"
        for vehicle_index in range(scenario.vehicles)
    ]
    assert len({request.request_id for request in requests}) == scenario.vehicles


def test_request_arrival_timesteps_match_generated_arrival_series():
    scenario = _build_even_arrival_scenario()
    arrivals_count_by_timestep = generate_arrivals_count_by_timestep(scenario)

    requests = generate_charging_requests(scenario, arrivals_count_by_timestep)

    request_counts_by_timestep = [0 for _ in range(TIMESTEPS_PER_DAY)]
    for request in requests:
        request_counts_by_timestep[request.arrival_timestep] += 1

    assert request_counts_by_timestep == arrivals_count_by_timestep


def test_simultaneous_arrivals_keep_fifo_ready_ordering_by_vehicle_index():
    scenario = _build_even_arrival_scenario()

    requests = generate_charging_requests(scenario)

    assert [
        (request.vehicle_index, request.arrival_timestep)
        for request in requests
    ] == [
        (0, 32),
        (1, 32),
        (2, 32),
        (3, 33),
        (4, 33),
        (5, 33),
        (6, 34),
        (7, 34),
        (8, 35),
        (9, 35),
    ]


def test_window_end_departure_mode_uses_shared_charging_window_end_as_departure_timestep():
    scenario = _build_even_arrival_scenario()

    requests = generate_charging_requests(scenario)

    assert {request.departure_timestep for request in requests} == {48}


def test_window_end_departure_spread_assigns_earlier_deadlines_to_some_requests():
    scenario = Scenario(
        vehicles=5,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
        departure_time_spread_minutes=30,
    )

    requests = generate_charging_requests(scenario)

    assert [request.departure_timestep for request in requests] == [
        46,
        46,
        47,
        47,
        48,
    ]


def test_session_dwell_departure_mode_offsets_each_request_from_its_arrival():
    scenario = Scenario(
        vehicles=6,
        daily_energy_per_vehicle=80.0,
        charger_count=6,
        charger_power=300.0,
        grid_capacity=1200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(18, 0),
        arrival_window_start=time(10, 0),
        arrival_window_end=time(12, 0),
        arrival_mode=ArrivalMode.RANDOM,
        departure_mode=DepartureMode.SESSION_DWELL,
        session_dwell_minutes=30,
    )

    requests = generate_charging_requests(scenario)

    assert all(
        request.departure_timestep == (request.arrival_timestep + 2) % TIMESTEPS_PER_DAY
        for request in requests
    )


def test_session_dwell_departure_spread_varies_dwell_durations_deterministically():
    scenario = Scenario(
        vehicles=6,
        daily_energy_per_vehicle=80.0,
        charger_count=6,
        charger_power=300.0,
        grid_capacity=1200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(18, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
        departure_mode=DepartureMode.SESSION_DWELL,
        session_dwell_minutes=30,
        departure_time_spread_minutes=15,
    )

    requests = generate_charging_requests(scenario)

    assert [
        (request.departure_timestep - request.arrival_timestep) % TIMESTEPS_PER_DAY
        for request in requests
    ] == [1, 1, 2, 2, 3, 3]


def test_session_dwell_request_energy_tracks_resolved_dwell_duration():
    scenario = Scenario(
        vehicles=6,
        daily_energy_per_vehicle=80.0,
        charger_count=6,
        charger_power=300.0,
        grid_capacity=1200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(18, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
        departure_mode=DepartureMode.SESSION_DWELL,
        session_dwell_minutes=30,
        departure_time_spread_minutes=15,
    )

    requests = generate_charging_requests(scenario)

    assert [request.energy_requested_kwh for request in requests] == [
        40.0,
        40.0,
        80.0,
        80.0,
        120.0,
        120.0,
    ]


def test_session_dwell_request_energy_preserves_total_site_energy():
    scenario = Scenario(
        vehicles=6,
        daily_energy_per_vehicle=80.0,
        charger_count=6,
        charger_power=300.0,
        grid_capacity=1200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(18, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
        departure_mode=DepartureMode.SESSION_DWELL,
        session_dwell_minutes=30,
        departure_time_spread_minutes=15,
        request_energy_variability_percent=25.0,
    )

    requests = generate_charging_requests(scenario)

    assert sum(request.energy_requested_kwh for request in requests) == (
        scenario.vehicles * scenario.daily_energy_per_vehicle
    )
    assert requests[0].energy_requested_kwh < requests[-1].energy_requested_kwh


def test_total_requested_energy_equals_total_daily_energy_demand():
    scenario = Scenario(
        vehicles=5,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
        request_energy_variability_percent=20.0,
    )

    requests = generate_charging_requests(scenario)

    assert sum(request.energy_requested_kwh for request in requests) == (
        scenario.vehicles * scenario.daily_energy_per_vehicle
    )


def test_request_energy_variability_is_deterministic_and_bounded():
    scenario = Scenario(
        vehicles=5,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
        request_energy_variability_percent=20.0,
    )

    requests = generate_charging_requests(scenario)

    assert [request.energy_requested_kwh for request in requests] == [
        16.0,
        18.0,
        20.0,
        22.0,
        24.0,
    ]


def test_request_outcome_fields_use_safe_pre_assignment_defaults():
    scenario = _build_even_arrival_scenario()

    requests = generate_charging_requests(scenario)
    first_request = requests[0]

    assert first_request.charging_start_timestep is None
    assert first_request.charging_completion_timestep is None
    assert first_request.energy_delivered_kwh == 0.0
    assert first_request.unmet_energy_kwh == 0.0
    assert first_request.waiting_time_hours is None
    assert first_request.not_started_within_window is False
    assert first_request.delayed_start_reason is None
    assert first_request.unmet_energy_reason is None
    assert first_request.strategy_extended_occupancy is None


def test_zero_vehicles_produce_no_requests():
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

    requests = generate_charging_requests(scenario)

    assert requests == []


def test_repeated_runs_with_identical_inputs_produce_identical_requests():
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
        request_energy_variability_percent=10.0,
        departure_time_spread_minutes=30,
    )

    first_run = generate_charging_requests(scenario)
    second_run = generate_charging_requests(scenario)

    assert first_run == second_run


def test_generate_charging_requests_accepts_precomputed_arrival_series():
    scenario = _build_even_arrival_scenario()
    arrivals_count_by_timestep = generate_arrivals_count_by_timestep(scenario)

    requests = generate_charging_requests(scenario, arrivals_count_by_timestep)

    assert len(requests) == scenario.vehicles
    assert requests == generate_charging_requests(scenario)
