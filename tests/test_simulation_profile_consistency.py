from dataclasses import replace
from datetime import time

import pytest

from scenarios import ChargingStrategy, Scenario, create_internal_scenario
from simulation import (
    TIMESTEPS_PER_DAY,
    build_request_timestep_series,
    calculate_available_site_capacity,
    calculate_daily_energy_demand,
    calculate_delivered_energy,
    simulate,
)
from simulation.time import time_to_timestep_index


def _assert_feeder_and_transformer_grid_loading_consistency(
    result,
    scenario,
) -> None:
    """Assert feeder EV and transformer totals stay internally consistent."""
    feeder_loading_results = result.grid_loading.feeder_loading_results
    total_feeder_base_load_kw = scenario.feeder_count * scenario.feeder_base_load_kw

    for timestep_index, site_ev_load_kw in enumerate(result.delivered_load_profile_kw):
        feeder_total_load_kw = sum(
            feeder_result.total_load_kw_by_timestep[timestep_index]
            for feeder_result in feeder_loading_results
        )
        feeder_ev_load_kw = feeder_total_load_kw - total_feeder_base_load_kw

        assert feeder_ev_load_kw == pytest.approx(site_ev_load_kw)
        assert (
            feeder_ev_load_kw + scenario.transformer_other_load_kw
        ) == pytest.approx(
            result.grid_loading.transformer_loading.total_load_kw_by_timestep[
                timestep_index
            ]
        )


def test_delivered_profile_energy_matches_summed_request_delivered_energy():
    base_scenario = Scenario(
        vehicles=6,
        daily_energy_per_vehicle=100.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=500.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
    )

    for charging_strategy in (
        ChargingStrategy.UNCONTROLLED,
        ChargingStrategy.SMART,
    ):
        result = simulate(
            replace(base_scenario, charging_strategy=charging_strategy)
        )

        assert calculate_delivered_energy(result.delivered_load_profile_kw) == sum(
            request.energy_delivered_kwh
            for request in result.charging_requests
        )


def test_feasible_scenario_preserves_expected_energy_through_requests_and_profile():
    scenario = Scenario(
        vehicles=2,
        daily_energy_per_vehicle=25.0,
        charger_count=1,
        charger_power=100.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
    )

    result = simulate(scenario)
    expected_energy_kwh = calculate_daily_energy_demand(scenario)

    assert result.delivered_energy == expected_energy_kwh
    assert calculate_delivered_energy(result.delivered_load_profile_kw) == expected_energy_kwh
    assert sum(
        request.energy_delivered_kwh
        for request in result.charging_requests
    ) == expected_energy_kwh


def test_constrained_site_capacity_caps_delivered_profile_and_preserves_profile_distinction():
    base_scenario = Scenario(
        vehicles=2,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=40.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    available_site_capacity_kw = calculate_available_site_capacity(base_scenario)

    for charging_strategy in (
        ChargingStrategy.UNCONTROLLED,
        ChargingStrategy.SMART,
    ):
        result = simulate(
            replace(base_scenario, charging_strategy=charging_strategy)
        )

        assert result.requested_load_profile_kw != result.delivered_load_profile_kw
        assert max(result.requested_load_profile_kw) <= (
            base_scenario.charger_count * base_scenario.charger_power
        )
        assert max(result.delivered_load_profile_kw) <= available_site_capacity_kw


def test_uncontrolled_and_smart_profiles_share_full_day_timestep_basis():
    base_scenario = Scenario(
        vehicles=4,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
    )
    charging_window_start_index = time_to_timestep_index(
        base_scenario.charging_window_start
    )

    uncontrolled_result = simulate(
        replace(base_scenario, charging_strategy=ChargingStrategy.UNCONTROLLED)
    )
    smart_result = simulate(
        replace(base_scenario, charging_strategy=ChargingStrategy.SMART)
    )

    assert len(uncontrolled_result.requested_load_profile_kw) == TIMESTEPS_PER_DAY
    assert len(uncontrolled_result.delivered_load_profile_kw) == TIMESTEPS_PER_DAY
    assert len(smart_result.requested_load_profile_kw) == TIMESTEPS_PER_DAY
    assert len(smart_result.delivered_load_profile_kw) == TIMESTEPS_PER_DAY
    assert next(
        index
        for index, load in enumerate(uncontrolled_result.requested_load_profile_kw)
        if load > 0.0
    ) == charging_window_start_index
    assert next(
        index
        for index, load in enumerate(uncontrolled_result.delivered_load_profile_kw)
        if load > 0.0
    ) == charging_window_start_index
    assert next(
        index
        for index, load in enumerate(smart_result.requested_load_profile_kw)
        if load > 0.0
    ) == charging_window_start_index
    assert next(
        index
        for index, load in enumerate(smart_result.delivered_load_profile_kw)
        if load > 0.0
    ) == charging_window_start_index


def test_simulated_profiles_match_full_day_timestep_length():
    result = simulate(Scenario(
        vehicles=4,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=150.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    ))

    assert len(result.requested_load_profile_kw) == TIMESTEPS_PER_DAY
    assert len(result.delivered_load_profile_kw) == TIMESTEPS_PER_DAY


def test_zero_total_demand_and_zero_charger_profiles_remain_safe_and_deterministic():
    for charging_strategy in (
        ChargingStrategy.UNCONTROLLED,
        ChargingStrategy.SMART,
    ):
        zero_vehicle_result = simulate(
            create_internal_scenario(
                vehicles=0,
                daily_energy_per_vehicle=20.0,
                charger_count=2,
                charger_power=50.0,
                grid_capacity=500.0,
                charging_window_start=time(22, 0),
                charging_window_end=time(2, 0),
                charging_strategy=charging_strategy,
            )
        )
        zero_charger_result = simulate(
            create_internal_scenario(
                vehicles=4,
                daily_energy_per_vehicle=20.0,
                charger_count=0,
                charger_power=50.0,
                grid_capacity=500.0,
                charging_window_start=time(22, 0),
                charging_window_end=time(2, 0),
                charging_strategy=charging_strategy,
            )
        )

        assert set(zero_vehicle_result.requested_load_profile_kw) == {0.0}
        assert set(zero_vehicle_result.delivered_load_profile_kw) == {0.0}
        assert set(zero_charger_result.requested_load_profile_kw) == {0.0}
        assert set(zero_charger_result.delivered_load_profile_kw) == {0.0}


def test_overnight_profiles_preserve_feeder_and_transformer_loading_consistency():
    scenario = create_internal_scenario(
        vehicles=4,
        daily_energy_per_vehicle=25.0,
        charger_count=5,
        charger_power=80.0,
        grid_capacity=160.0,
        transformer_capacity_kw=220.0,
        transformer_other_load_kw=30.0,
        feeder_count=3,
        feeder_capacity_kw=90.0,
        feeder_base_load_kw=12.5,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
        charging_strategy=ChargingStrategy.SMART,
    )

    result = simulate(scenario)

    assert len(result.delivered_load_profile_kw) == TIMESTEPS_PER_DAY
    assert len(result.grid_loading.transformer_loading.total_load_kw_by_timestep) == (
        TIMESTEPS_PER_DAY
    )
    assert len(result.grid_loading.feeder_loading_results) == scenario.feeder_count
    _assert_feeder_and_transformer_grid_loading_consistency(result, scenario)


def test_matching_constant_base_loads_allow_feeder_total_sum_to_match_transformer_total():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=25.0,
        charger_count=4,
        charger_power=100.0,
        grid_capacity=150.0,
        transformer_capacity_kw=210.0,
        transformer_other_load_kw=30.0,
        feeder_count=3,
        feeder_capacity_kw=80.0,
        feeder_base_load_kw=10.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )

    result = simulate(scenario)

    _assert_feeder_and_transformer_grid_loading_consistency(result, scenario)

    for timestep_index, transformer_total_load_kw in enumerate(
        result.grid_loading.transformer_loading.total_load_kw_by_timestep
    ):
        feeder_total_load_kw = sum(
            feeder_result.total_load_kw_by_timestep[timestep_index]
            for feeder_result in result.grid_loading.feeder_loading_results
        )

        assert feeder_total_load_kw == pytest.approx(transformer_total_load_kw)


def test_queue_only_constraints_do_not_redefine_requested_profile_as_site_limited_delivery():
    scenario = Scenario(
        vehicles=4,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
        charging_strategy=ChargingStrategy.SMART,
    )

    result = simulate(scenario)

    assert max(result.waiting_vehicle_count_by_timestep) > 0
    assert result.requested_load_profile_kw == result.delivered_load_profile_kw
    assert max(result.requested_load_profile_kw) <= (
        scenario.charger_count * scenario.charger_power
    )


def test_occupancy_and_waiting_series_remain_request_based_not_power_derived():
    scenario = Scenario(
        vehicles=1,
        daily_energy_per_vehicle=50.0,
        charger_count=1,
        charger_power=100.0,
        grid_capacity=25.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )

    result = simulate(scenario)
    request_based_series = build_request_timestep_series(
        scenario,
        result.charging_requests,
    )

    assert result.occupied_charger_count_by_timestep == request_based_series[
        "occupied_charger_count_by_timestep"
    ]
    assert result.waiting_vehicle_count_by_timestep == request_based_series[
        "waiting_vehicle_count_by_timestep"
    ]
    assert max(result.occupied_charger_count_by_timestep) == 1
    assert max(result.delivered_load_profile_kw) == 25.0
