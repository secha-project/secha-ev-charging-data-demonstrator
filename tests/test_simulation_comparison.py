from dataclasses import replace

from datetime import time

from metrics import calculate_scenario_comparison_metrics
from scenarios import (
    ArrivalProfileShape,
    ChargingStrategy,
    Scenario,
    create_strategy_variants,
    default_scenario,
)
from simulation import (
    ChargingRequestResult,
    FeederLoadingResult,
    FeederPowerQualityResult,
    GridLoadingResult,
    PowerQualityResult,
    SimulationResult,
    TransformerLoadingResult,
    assign_chargers_fifo,
    build_request_timestep_series,
    calculate_transformer_loading_percent,
    calculate_transformer_overload_kw,
    calculate_transformer_total_load,
    charging_request_result_from_dict,
    charging_request_result_to_dict,
    feeder_power_quality_result_from_dict,
    feeder_power_quality_result_to_dict,
    power_quality_result_from_dict,
    power_quality_result_to_dict,
    simulate,
    simulate_scenario_comparison,
    simulate_strategy_comparison,
    simulation_result_from_dict,
    simulation_result_to_dict,
)


def test_simulate_strategy_comparison_returns_two_simulation_results():
    uncontrolled_result, smart_result = simulate_strategy_comparison(default_scenario)

    assert isinstance(uncontrolled_result, SimulationResult)
    assert isinstance(smart_result, SimulationResult)
    assert uncontrolled_result is not smart_result


def test_simulate_strategy_comparison_matches_direct_variant_simulations():
    uncontrolled_scenario, smart_scenario = create_strategy_variants(default_scenario)

    uncontrolled_result, smart_result = simulate_strategy_comparison(default_scenario)

    assert uncontrolled_result == simulate(uncontrolled_scenario)
    assert smart_result == simulate(smart_scenario)


def test_simulate_strategy_comparison_uses_same_base_inputs_for_both_results():
    base_scenario = replace(
        default_scenario,
        vehicles=12,
        daily_energy_per_vehicle=80.0,
        charger_count=3,
        charger_power=75.0,
        grid_capacity=200.0,
        charging_strategy=ChargingStrategy.SMART,
    )

    uncontrolled_result, smart_result = simulate_strategy_comparison(base_scenario)

    assert uncontrolled_result.daily_energy_demand == smart_result.daily_energy_demand
    assert (
        uncontrolled_result.installed_charger_capacity
        == smart_result.installed_charger_capacity
    )
    assert uncontrolled_result.available_site_capacity == (
        smart_result.available_site_capacity
    )
    assert uncontrolled_result.uncontrolled_load_profile != (
        smart_result.uncontrolled_load_profile
    )


def test_simulate_strategy_comparison_returns_raw_results_only():
    uncontrolled_result, smart_result = simulate_strategy_comparison(default_scenario)

    assert not hasattr(uncontrolled_result, "peak_reduction")
    assert not hasattr(smart_result, "peak_reduction")


def test_simulate_scenario_comparison_returns_two_simulation_results():
    scenario_b = replace(default_scenario, vehicles=75)

    result_a, result_b = simulate_scenario_comparison(default_scenario, scenario_b)

    assert isinstance(result_a, SimulationResult)
    assert isinstance(result_b, SimulationResult)
    assert result_a is not result_b


def test_simulate_scenario_comparison_matches_direct_simulations():
    scenario_a = replace(default_scenario, vehicles=50, charger_count=10)
    scenario_b = replace(
        default_scenario,
        vehicles=75,
        charger_count=12,
        charger_power=180.0,
        grid_capacity=1200.0,
    )

    result_a, result_b = simulate_scenario_comparison(scenario_a, scenario_b)

    assert result_a == simulate(scenario_a)
    assert result_b == simulate(scenario_b)
    assert result_a.daily_energy_demand != result_b.daily_energy_demand
    assert result_a.installed_charger_capacity != result_b.installed_charger_capacity


def test_simulate_scenario_comparison_uses_each_selected_strategy():
    scenario_a = replace(default_scenario, charging_strategy=ChargingStrategy.UNCONTROLLED)
    scenario_b = replace(default_scenario, charging_strategy=ChargingStrategy.SMART)

    result_a, result_b = simulate_scenario_comparison(scenario_a, scenario_b)

    assert result_a == simulate(scenario_a)
    assert result_b == simulate(scenario_b)
    assert result_a.load_profile != result_b.load_profile


def test_scenario_comparison_metrics_handle_mismatched_feeder_topologies():
    scenario_a = replace(
        default_scenario,
        charger_count=4,
        feeder_count=1,
        feeder_capacity_kw=400.0,
    )
    scenario_b = replace(
        default_scenario,
        charger_count=4,
        feeder_count=2,
        feeder_capacity_kw=220.0,
    )

    result_a, result_b = simulate_scenario_comparison(scenario_a, scenario_b)
    metrics_a, metrics_b = calculate_scenario_comparison_metrics(
        scenario_a,
        result_a,
        scenario_b,
        result_b,
    )

    assert len(result_a.grid_loading.feeder_loading_results) == 1
    assert len(result_b.grid_loading.feeder_loading_results) == 2
    assert len(metrics_a.feeder_summary_rows) == 1
    assert len(metrics_b.feeder_summary_rows) == 2
    assert (
        metrics_a.maximum_feeder_loading_percent
        == metrics_a.feeder_summary_rows[0].peak_loading_percent
    )
    assert metrics_b.maximum_feeder_loading_percent == max(
        feeder_summary.peak_loading_percent
        for feeder_summary in metrics_b.feeder_summary_rows
    )


def test_simulation_result_serialization_round_trip_preserves_raw_result():
    result = simulate(default_scenario)
    request_timestep_series = build_request_timestep_series(
        default_scenario,
        result.charging_requests,
    )
    expected_transformer_total_load = [
        calculate_transformer_total_load(
            load_kw,
            default_scenario.transformer_other_load_kw,
        )
        for load_kw in result.delivered_load_profile_kw
    ]
    expected_feeder_total_load = [
        (load_kw / 2.0) + default_scenario.feeder_base_load_kw
        for load_kw in result.delivered_load_profile_kw
    ]

    data = simulation_result_to_dict(result)
    restored_result = simulation_result_from_dict(data)

    assert data == {
        "daily_energy_demand": result.daily_energy_demand,
        "configured_connection_capacity_kw": result.configured_connection_capacity_kw,
        "installed_charger_capacity_kw": result.installed_charger_capacity_kw,
        "available_site_charging_capacity_kw": (
            result.available_site_charging_capacity_kw
        ),
        "requested_load_profile_kw": result.requested_load_profile_kw,
        "delivered_load_profile_kw": result.delivered_load_profile_kw,
        "load_profile": result.delivered_load_profile_kw,
        "uncontrolled_load_profile": result.delivered_load_profile_kw,
        "delivered_energy": result.delivered_energy,
        "unmet_energy": result.unmet_energy,
        "charging_requests": [
            charging_request_result_to_dict(request_result)
            for request_result in assign_chargers_fifo(default_scenario)
        ],
        "arrivals_count_by_timestep": request_timestep_series[
            "arrivals_count_by_timestep"
        ],
        "charging_start_count_by_timestep": request_timestep_series[
            "charging_start_count_by_timestep"
        ],
        "charging_completion_count_by_timestep": request_timestep_series[
            "charging_completion_count_by_timestep"
        ],
        "requested_charger_slots_by_timestep": request_timestep_series[
            "requested_charger_slots_by_timestep"
        ],
        "occupied_charger_count_by_timestep": request_timestep_series[
            "occupied_charger_count_by_timestep"
        ],
        "waiting_vehicle_count_by_timestep": request_timestep_series[
            "waiting_vehicle_count_by_timestep"
        ],
        "grid_loading": {
            "transformer_loading": {
                "total_load_kw_by_timestep": expected_transformer_total_load,
                "loading_percent_by_timestep": [
                    calculate_transformer_loading_percent(
                        total_load_kw,
                        default_scenario.transformer_capacity_kw,
                    )
                    for total_load_kw in expected_transformer_total_load
                ],
                "overload_kw_by_timestep": [
                    calculate_transformer_overload_kw(
                        total_load_kw,
                        default_scenario.transformer_capacity_kw,
                    )
                    for total_load_kw in expected_transformer_total_load
                ],
            },
            "feeder_loading_results": [
                {
                    "feeder_id": "feeder-1",
                    "charger_count": 5,
                    "total_load_kw_by_timestep": expected_feeder_total_load,
                    "loading_percent_by_timestep": [
                        calculate_transformer_loading_percent(
                            total_load_kw,
                            default_scenario.feeder_capacity_kw,
                        )
                        for total_load_kw in expected_feeder_total_load
                    ],
                    "overload_kw_by_timestep": [
                        calculate_transformer_overload_kw(
                            total_load_kw,
                            default_scenario.feeder_capacity_kw,
                        )
                        for total_load_kw in expected_feeder_total_load
                    ],
                },
                {
                    "feeder_id": "feeder-2",
                    "charger_count": 5,
                    "total_load_kw_by_timestep": expected_feeder_total_load,
                    "loading_percent_by_timestep": [
                        calculate_transformer_loading_percent(
                            total_load_kw,
                            default_scenario.feeder_capacity_kw,
                        )
                        for total_load_kw in expected_feeder_total_load
                    ],
                    "overload_kw_by_timestep": [
                        calculate_transformer_overload_kw(
                            total_load_kw,
                            default_scenario.feeder_capacity_kw,
                        )
                        for total_load_kw in expected_feeder_total_load
                    ],
                },
            ],
        },
        "power_quality": power_quality_result_to_dict(result.power_quality),
    }
    assert restored_result == result
    assert (
        restored_result.requested_load_profile_kw
        is not result.requested_load_profile_kw
    )
    assert (
        restored_result.delivered_load_profile_kw
        is not result.delivered_load_profile_kw
    )


def test_simulation_result_from_dict_reads_legacy_load_profile_payload():
    legacy_data = {
        "daily_energy_demand": 1200.0,
        "installed_charger_capacity": 150.0,
        "available_site_capacity": 100.0,
        "load_profile": [0.0, 25.0, 100.0, 50.0],
        "delivered_energy": 175.0,
        "unmet_energy": 1025.0,
    }

    result = simulation_result_from_dict(legacy_data)

    assert result.configured_connection_capacity_kw == 100.0
    assert result.installed_charger_capacity_kw == 150.0
    assert result.available_site_charging_capacity_kw == 100.0
    assert result.requested_load_profile_kw == [0.0, 25.0, 100.0, 50.0]
    assert result.delivered_load_profile_kw == [0.0, 25.0, 100.0, 50.0]
    assert result.load_profile == result.delivered_load_profile_kw
    assert result.charging_requests == []
    assert result.arrivals_count_by_timestep == []
    assert result.charging_start_count_by_timestep == []
    assert result.charging_completion_count_by_timestep == []
    assert result.requested_charger_slots_by_timestep == []
    assert result.occupied_charger_count_by_timestep == []
    assert result.waiting_vehicle_count_by_timestep == []
    assert result.grid_loading == GridLoadingResult(
        transformer_loading=TransformerLoadingResult(),
        feeder_loading_results=[],
    )
    assert result.power_quality == PowerQualityResult()


def test_charging_request_result_serialization_round_trip_preserves_optional_nones():
    request_result = ChargingRequestResult(
        request_id="request-0",
        vehicle_index=0,
        arrival_timestep=68,
        departure_timestep=24,
        charging_start_timestep=None,
        charging_completion_timestep=None,
        energy_requested_kwh=150.0,
        energy_delivered_kwh=0.0,
        unmet_energy_kwh=150.0,
        waiting_time_hours=None,
        not_started_within_window=True,
        delayed_start_reason=None,
        unmet_energy_reason="charger_availability_constraint",
        strategy_extended_occupancy=None,
    )

    data = charging_request_result_to_dict(request_result)
    restored_request_result = charging_request_result_from_dict(data)

    assert data == {
        "request_id": "request-0",
        "vehicle_index": 0,
        "arrival_timestep": 68,
        "departure_timestep": 24,
        "charging_start_timestep": None,
        "charging_completion_timestep": None,
        "energy_requested_kwh": 150.0,
        "energy_delivered_kwh": 0.0,
        "unmet_energy_kwh": 150.0,
        "waiting_time_hours": None,
        "not_started_within_window": True,
        "delayed_start_reason": None,
        "unmet_energy_reason": "charger_availability_constraint",
        "strategy_extended_occupancy": None,
    }
    assert restored_request_result == request_result


def test_charging_request_result_deserialization_defaults_missing_strategy_flag_to_none():
    restored_request_result = charging_request_result_from_dict(
        {
            "request_id": "request-0",
            "vehicle_index": 0,
            "arrival_timestep": 68,
            "departure_timestep": 24,
            "charging_start_timestep": None,
            "charging_completion_timestep": None,
            "energy_requested_kwh": 150.0,
            "energy_delivered_kwh": 0.0,
            "unmet_energy_kwh": 150.0,
            "waiting_time_hours": None,
            "not_started_within_window": True,
            "delayed_start_reason": None,
            "unmet_energy_reason": "charger_availability_constraint",
        }
    )

    assert restored_request_result.strategy_extended_occupancy is None


def test_simulated_reason_flags_serialize_and_deserialize_with_current_raw_values():
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

    result = simulate(scenario)
    data = simulation_result_to_dict(result)
    restored_result = simulation_result_from_dict(data)

    assert [
        request["delayed_start_reason"]
        for request in data["charging_requests"]
    ] == ["none", "charger_availability"]
    assert [
        request["unmet_energy_reason"]
        for request in data["charging_requests"]
    ] == ["none", "mixed"]
    assert restored_result == result


def test_simulation_result_serialization_round_trip_preserves_queueing_raw_contract():
    request_result_a = ChargingRequestResult(
        request_id="request-0",
        vehicle_index=0,
        arrival_timestep=68,
        departure_timestep=24,
        charging_start_timestep=69,
        charging_completion_timestep=72,
        energy_requested_kwh=150.0,
        energy_delivered_kwh=150.0,
        unmet_energy_kwh=0.0,
        waiting_time_hours=0.25,
        not_started_within_window=False,
        delayed_start_reason="charger_availability_constraint",
        unmet_energy_reason=None,
        strategy_extended_occupancy=True,
    )
    request_result_b = ChargingRequestResult(
        request_id="request-1",
        vehicle_index=1,
        arrival_timestep=68,
        departure_timestep=24,
        charging_start_timestep=None,
        charging_completion_timestep=None,
        energy_requested_kwh=150.0,
        energy_delivered_kwh=0.0,
        unmet_energy_kwh=150.0,
        waiting_time_hours=None,
        not_started_within_window=True,
        delayed_start_reason="charger_availability_constraint",
        unmet_energy_reason="charger_availability_constraint",
        strategy_extended_occupancy=None,
    )
    result = SimulationResult(
        daily_energy_demand=300.0,
        configured_connection_capacity_kw=150.0,
        installed_charger_capacity_kw=200.0,
        available_site_charging_capacity_kw=150.0,
        requested_load_profile_kw=[150.0, 150.0, 0.0, 0.0],
        delivered_load_profile_kw=[150.0, 150.0, 0.0, 0.0],
        delivered_energy=75.0,
        unmet_energy=225.0,
        charging_requests=[request_result_a, request_result_b],
        arrivals_count_by_timestep=[2, 0, 0, 0],
        charging_start_count_by_timestep=[0, 1, 0, 0],
        charging_completion_count_by_timestep=[0, 0, 0, 1],
        requested_charger_slots_by_timestep=[2, 2, 1, 0],
        occupied_charger_count_by_timestep=[0, 1, 1, 0],
        waiting_vehicle_count_by_timestep=[2, 1, 1, 0],
    )

    data = simulation_result_to_dict(result)
    restored_result = simulation_result_from_dict(data)

    assert data["requested_load_profile_kw"] == [150.0, 150.0, 0.0, 0.0]
    assert data["delivered_load_profile_kw"] == [150.0, 150.0, 0.0, 0.0]
    assert data["load_profile"] == [150.0, 150.0, 0.0, 0.0]
    assert data["uncontrolled_load_profile"] == [150.0, 150.0, 0.0, 0.0]
    assert data["charging_requests"] == [
        charging_request_result_to_dict(request_result_a),
        charging_request_result_to_dict(request_result_b),
    ]
    assert data["arrivals_count_by_timestep"] == [2, 0, 0, 0]
    assert data["charging_start_count_by_timestep"] == [0, 1, 0, 0]
    assert data["charging_completion_count_by_timestep"] == [0, 0, 0, 1]
    assert data["requested_charger_slots_by_timestep"] == [2, 2, 1, 0]
    assert data["occupied_charger_count_by_timestep"] == [0, 1, 1, 0]
    assert data["waiting_vehicle_count_by_timestep"] == [2, 1, 1, 0]
    assert data["power_quality"] == {
        "harmonic_risk_score_by_timestep": [],
        "current_imbalance_percent_by_timestep": [],
        "overall_pq_risk_score_by_timestep": [],
        "phase_a_load_kw_by_timestep": [],
        "phase_b_load_kw_by_timestep": [],
        "phase_c_load_kw_by_timestep": [],
        "feeder_power_quality_results": [],
    }
    assert restored_result == result
    assert restored_result.charging_requests is not result.charging_requests
    assert (
        restored_result.arrivals_count_by_timestep
        is not result.arrivals_count_by_timestep
    )
    assert (
        restored_result.charging_start_count_by_timestep
        is not result.charging_start_count_by_timestep
    )
    assert (
        restored_result.charging_completion_count_by_timestep
        is not result.charging_completion_count_by_timestep
    )
    assert (
        restored_result.requested_charger_slots_by_timestep
        is not result.requested_charger_slots_by_timestep
    )
    assert (
        restored_result.occupied_charger_count_by_timestep
        is not result.occupied_charger_count_by_timestep
    )
    assert (
        restored_result.waiting_vehicle_count_by_timestep
        is not result.waiting_vehicle_count_by_timestep
    )
    assert restored_result.grid_loading == result.grid_loading
    assert restored_result.power_quality == result.power_quality


def test_feeder_power_quality_result_serialization_round_trip_preserves_values():
    feeder_result = FeederPowerQualityResult(
        feeder_id="feeder-1",
        harmonic_risk_score_by_timestep=[5.0, 10.0, 0.0],
        current_imbalance_percent_by_timestep=[0.0, 12.5, 6.0],
    )

    data = feeder_power_quality_result_to_dict(feeder_result)
    restored_result = feeder_power_quality_result_from_dict(data)

    assert data == {
        "feeder_id": "feeder-1",
        "harmonic_risk_score_by_timestep": [5.0, 10.0, 0.0],
        "current_imbalance_percent_by_timestep": [0.0, 12.5, 6.0],
    }
    assert restored_result == feeder_result


def test_power_quality_result_serialization_round_trip_preserves_values():
    power_quality_result = PowerQualityResult(
        harmonic_risk_score_by_timestep=[20.0, 15.0, 0.0],
        current_imbalance_percent_by_timestep=[5.0, 7.5, 0.0],
        overall_pq_risk_score_by_timestep=[16.0, 12.0, 0.0],
        phase_a_load_kw_by_timestep=[40.0, 30.0, 0.0],
        phase_b_load_kw_by_timestep=[35.0, 30.0, 0.0],
        phase_c_load_kw_by_timestep=[25.0, 20.0, 0.0],
        feeder_power_quality_results=[
            FeederPowerQualityResult(
                feeder_id="feeder-1",
                harmonic_risk_score_by_timestep=[12.0, 8.0, 0.0],
                current_imbalance_percent_by_timestep=[4.0, 5.0, 0.0],
            ),
            FeederPowerQualityResult(
                feeder_id="feeder-2",
                harmonic_risk_score_by_timestep=[8.0, 7.0, 0.0],
                current_imbalance_percent_by_timestep=[6.0, 10.0, 0.0],
            ),
        ],
    )

    data = power_quality_result_to_dict(power_quality_result)
    restored_result = power_quality_result_from_dict(data)

    assert data == {
        "harmonic_risk_score_by_timestep": [20.0, 15.0, 0.0],
        "current_imbalance_percent_by_timestep": [5.0, 7.5, 0.0],
        "overall_pq_risk_score_by_timestep": [16.0, 12.0, 0.0],
        "phase_a_load_kw_by_timestep": [40.0, 30.0, 0.0],
        "phase_b_load_kw_by_timestep": [35.0, 30.0, 0.0],
        "phase_c_load_kw_by_timestep": [25.0, 20.0, 0.0],
        "feeder_power_quality_results": [
            {
                "feeder_id": "feeder-1",
                "harmonic_risk_score_by_timestep": [12.0, 8.0, 0.0],
                "current_imbalance_percent_by_timestep": [4.0, 5.0, 0.0],
            },
            {
                "feeder_id": "feeder-2",
                "harmonic_risk_score_by_timestep": [8.0, 7.0, 0.0],
                "current_imbalance_percent_by_timestep": [6.0, 10.0, 0.0],
            },
        ],
    }
    assert restored_result == power_quality_result


def test_simulation_result_serialization_round_trip_preserves_grid_loading_raw_contract():
    result = SimulationResult(
        daily_energy_demand=300.0,
        configured_connection_capacity_kw=150.0,
        installed_charger_capacity_kw=200.0,
        available_site_charging_capacity_kw=150.0,
        requested_load_profile_kw=[150.0, 150.0, 0.0, 0.0],
        delivered_load_profile_kw=[125.0, 150.0, 25.0, 0.0],
        grid_loading=GridLoadingResult(
            transformer_loading=TransformerLoadingResult(
                total_load_kw_by_timestep=[175.0, 200.0, 75.0, 50.0],
                loading_percent_by_timestep=[70.0, 80.0, 30.0, 20.0],
                overload_kw_by_timestep=[0.0, 0.0, 0.0, 0.0],
            ),
            feeder_loading_results=[
                FeederLoadingResult(
                    feeder_id="feeder-1",
                    charger_count=2,
                    total_load_kw_by_timestep=[90.0, 100.0, 40.0, 20.0],
                    loading_percent_by_timestep=[60.0, 66.7, 26.7, 13.3],
                    overload_kw_by_timestep=[0.0, 0.0, 0.0, 0.0],
                ),
                FeederLoadingResult(
                    feeder_id="feeder-2",
                    charger_count=2,
                    total_load_kw_by_timestep=[85.0, 100.0, 35.0, 30.0],
                    loading_percent_by_timestep=[56.7, 66.7, 23.3, 20.0],
                    overload_kw_by_timestep=[0.0, 0.0, 0.0, 0.0],
                ),
            ],
        ),
        power_quality=PowerQualityResult(
            harmonic_risk_score_by_timestep=[22.0, 24.0, 8.0, 0.0],
            current_imbalance_percent_by_timestep=[5.0, 6.0, 3.0, 0.0],
            overall_pq_risk_score_by_timestep=[18.0, 19.0, 6.0, 0.0],
            phase_a_load_kw_by_timestep=[50.0, 60.0, 15.0, 0.0],
            phase_b_load_kw_by_timestep=[40.0, 50.0, 10.0, 0.0],
            phase_c_load_kw_by_timestep=[35.0, 40.0, 0.0, 0.0],
            feeder_power_quality_results=[
                FeederPowerQualityResult(
                    feeder_id="feeder-1",
                    harmonic_risk_score_by_timestep=[12.0, 13.0, 4.0, 0.0],
                    current_imbalance_percent_by_timestep=[4.0, 5.0, 2.0, 0.0],
                ),
                FeederPowerQualityResult(
                    feeder_id="feeder-2",
                    harmonic_risk_score_by_timestep=[10.0, 11.0, 4.0, 0.0],
                    current_imbalance_percent_by_timestep=[6.0, 7.0, 4.0, 0.0],
                ),
            ],
        ),
    )

    data = simulation_result_to_dict(result)
    restored_result = simulation_result_from_dict(data)

    assert data["grid_loading"] == {
        "transformer_loading": {
            "total_load_kw_by_timestep": [175.0, 200.0, 75.0, 50.0],
            "loading_percent_by_timestep": [70.0, 80.0, 30.0, 20.0],
            "overload_kw_by_timestep": [0.0, 0.0, 0.0, 0.0],
        },
        "feeder_loading_results": [
            {
                "feeder_id": "feeder-1",
                "charger_count": 2,
                "total_load_kw_by_timestep": [90.0, 100.0, 40.0, 20.0],
                "loading_percent_by_timestep": [60.0, 66.7, 26.7, 13.3],
                "overload_kw_by_timestep": [0.0, 0.0, 0.0, 0.0],
            },
            {
                "feeder_id": "feeder-2",
                "charger_count": 2,
                "total_load_kw_by_timestep": [85.0, 100.0, 35.0, 30.0],
                "loading_percent_by_timestep": [56.7, 66.7, 23.3, 20.0],
                "overload_kw_by_timestep": [0.0, 0.0, 0.0, 0.0],
            },
        ],
    }
    assert data["power_quality"] == {
        "harmonic_risk_score_by_timestep": [22.0, 24.0, 8.0, 0.0],
        "current_imbalance_percent_by_timestep": [5.0, 6.0, 3.0, 0.0],
        "overall_pq_risk_score_by_timestep": [18.0, 19.0, 6.0, 0.0],
        "phase_a_load_kw_by_timestep": [50.0, 60.0, 15.0, 0.0],
        "phase_b_load_kw_by_timestep": [40.0, 50.0, 10.0, 0.0],
        "phase_c_load_kw_by_timestep": [35.0, 40.0, 0.0, 0.0],
        "feeder_power_quality_results": [
            {
                "feeder_id": "feeder-1",
                "harmonic_risk_score_by_timestep": [12.0, 13.0, 4.0, 0.0],
                "current_imbalance_percent_by_timestep": [4.0, 5.0, 2.0, 0.0],
            },
            {
                "feeder_id": "feeder-2",
                "harmonic_risk_score_by_timestep": [10.0, 11.0, 4.0, 0.0],
                "current_imbalance_percent_by_timestep": [6.0, 7.0, 4.0, 0.0],
            },
        ],
    }
    assert restored_result == result
    assert restored_result.grid_loading is not result.grid_loading
    assert (
        restored_result.grid_loading.transformer_loading
        is not result.grid_loading.transformer_loading
    )
    assert (
        restored_result.grid_loading.feeder_loading_results
        is not result.grid_loading.feeder_loading_results
    )
    assert restored_result.power_quality is not result.power_quality
    assert (
        restored_result.power_quality.feeder_power_quality_results
        is not result.power_quality.feeder_power_quality_results
    )


def test_simulation_result_from_dict_reads_legacy_payload_without_power_quality_block():
    result = simulation_result_from_dict(
        {
            "daily_energy_demand": 300.0,
            "configured_connection_capacity_kw": 150.0,
            "installed_charger_capacity_kw": 200.0,
            "available_site_charging_capacity_kw": 150.0,
            "requested_load_profile_kw": [150.0, 150.0, 0.0, 0.0],
            "delivered_load_profile_kw": [125.0, 150.0, 25.0, 0.0],
            "delivered_energy": 75.0,
            "unmet_energy": 225.0,
            "grid_loading": {
                "transformer_loading": {
                    "total_load_kw_by_timestep": [175.0, 200.0, 75.0, 50.0],
                    "loading_percent_by_timestep": [70.0, 80.0, 30.0, 20.0],
                    "overload_kw_by_timestep": [0.0, 0.0, 0.0, 0.0],
                },
                "feeder_loading_results": [],
            },
        }
    )

    assert result.power_quality == PowerQualityResult()


def test_simulate_serializes_generated_charging_requests_for_current_phase_contract():
    result = simulate(default_scenario)

    data = simulation_result_to_dict(result)
    restored_result = simulation_result_from_dict(data)
    request_timestep_series = build_request_timestep_series(
        default_scenario,
        result.charging_requests,
    )

    assert len(result.charging_requests) == default_scenario.vehicles
    assert sum(result.arrivals_count_by_timestep) == default_scenario.vehicles
    assert result.charging_requests == assign_chargers_fifo(default_scenario)
    assert result.arrivals_count_by_timestep == request_timestep_series[
        "arrivals_count_by_timestep"
    ]
    assert result.charging_start_count_by_timestep == request_timestep_series[
        "charging_start_count_by_timestep"
    ]
    assert result.charging_completion_count_by_timestep == request_timestep_series[
        "charging_completion_count_by_timestep"
    ]
    assert result.requested_charger_slots_by_timestep == request_timestep_series[
        "requested_charger_slots_by_timestep"
    ]
    assert result.occupied_charger_count_by_timestep == request_timestep_series[
        "occupied_charger_count_by_timestep"
    ]
    assert result.waiting_vehicle_count_by_timestep == request_timestep_series[
        "waiting_vehicle_count_by_timestep"
    ]
    assert data["charging_requests"] == [
        charging_request_result_to_dict(request_result)
        for request_result in result.charging_requests
    ]
    assert restored_result == result
