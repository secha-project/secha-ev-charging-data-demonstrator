from dataclasses import FrozenInstanceError, fields, replace
from datetime import time

import pytest

from scenarios import (
    PUBLIC_FAST_CHARGING_PRESET_ID,
    ChargingStrategy,
    FeederEVAllocationMethod,
    Scenario,
    create_internal_scenario,
    default_scenario,
    get_scenario_preset,
)
from simulation import (
    ChargingRequestResult,
    FeederLoadingResult,
    FeederPowerQualityResult,
    GridLoadingResult,
    ModeledFeeder,
    build_planner_candidate_simulation_context,
    PlannerCandidateSimulationResult,
    PowerQualityResult,
    SimulationResult,
    TransformerLoadingResult,
    assign_chargers_fifo,
    build_request_timestep_series,
    build_power_quality_result,
    expand_feeder_assets,
    generate_arrivals_count_by_timestep,
    simulate,
    simulate_planner_candidate,
    simulate_strategy_comparison,
    simulation_result_from_dict,
    simulation_result_to_dict,
)
from simulation.engine import _generate_requested_and_delivered_load_profiles
from simulation.formulas import (
    calculate_available_site_capacity,
    calculate_daily_energy_demand,
    calculate_installed_charger_capacity,
    calculate_transformer_loading_percent,
    calculate_transformer_overload_kw,
    calculate_transformer_total_load,
)
from simulation.load_profiles import (
    calculate_delivered_energy,
    calculate_unmet_energy,
    generate_smart_load_profile,
    generate_uncontrolled_load_profile,
)
from simulation.time import TIMESTEPS_PER_DAY, time_to_timestep_index


def _build_full_day_transformer_series(
    window_start: time,
    window_values: list[float],
    *,
    default_value: float = 0.0,
) -> list[float]:
    """Build a full-day timestep series with explicit window values."""
    series = [default_value] * TIMESTEPS_PER_DAY
    start_index = time_to_timestep_index(window_start)
    for offset, value in enumerate(window_values):
        series[(start_index + offset) % TIMESTEPS_PER_DAY] = value
    return series


def _build_transformer_regression_scenario(
    *,
    transformer_capacity_kw: float,
    transformer_other_load_kw: float,
    vehicles: int = 1,
) -> Scenario:
    """Return a small deterministic scenario for transformer regression tests."""
    return create_internal_scenario(
        vehicles=vehicles,
        daily_energy_per_vehicle=25.0,
        charger_count=1,
        charger_power=100.0,
        grid_capacity=100.0,
        transformer_capacity_kw=transformer_capacity_kw,
        transformer_other_load_kw=transformer_other_load_kw,
        charging_window_start=time(8, 0),
        charging_window_end=time(8, 15),
    )


def _build_reference_grid_loading_scenario(
    *,
    vehicles: int = 1,
    charger_count: int = 1,
    charger_power: float = 100.0,
    grid_capacity: float = 100.0,
    transformer_capacity_kw: float = 150.0,
    transformer_other_load_kw: float = 20.0,
    feeder_count: int = 1,
    feeder_capacity_kw: float = 140.0,
    feeder_base_load_kw: float = 10.0,
    charging_window_end: time = time(8, 15),
    charging_strategy: ChargingStrategy = ChargingStrategy.UNCONTROLLED,
) -> Scenario:
    """Return a compact deterministic scenario for grid-loading regressions."""
    return create_internal_scenario(
        vehicles=vehicles,
        daily_energy_per_vehicle=25.0,
        charger_count=charger_count,
        charger_power=charger_power,
        grid_capacity=grid_capacity,
        transformer_capacity_kw=transformer_capacity_kw,
        transformer_other_load_kw=transformer_other_load_kw,
        feeder_count=feeder_count,
        feeder_capacity_kw=feeder_capacity_kw,
        feeder_base_load_kw=feeder_base_load_kw,
        charging_window_start=time(8, 0),
        charging_window_end=charging_window_end,
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        charging_strategy=charging_strategy,
    )


def test_simulation_result_contains_raw_simulation_outputs():
    assert [field.name for field in fields(SimulationResult)] == [
        "daily_energy_demand",
        "configured_connection_capacity_kw",
        "installed_charger_capacity_kw",
        "available_site_charging_capacity_kw",
        "requested_load_profile_kw",
        "delivered_load_profile_kw",
        "delivered_energy",
        "unmet_energy",
        "charging_requests",
        "arrivals_count_by_timestep",
        "charging_start_count_by_timestep",
        "charging_completion_count_by_timestep",
        "requested_charger_slots_by_timestep",
        "occupied_charger_count_by_timestep",
        "waiting_vehicle_count_by_timestep",
        "grid_loading",
        "power_quality",
    ]


def test_planner_candidate_simulation_result_contains_expected_service_rule_fields():
    assert [field.name for field in fields(PlannerCandidateSimulationResult)] == [
        "daily_energy_demand",
        "request_count",
        "started_request_waiting_times_hours",
        "vehicles_waiting_count",
        "vehicles_not_started_count",
        "vehicles_with_unmet_energy_count",
        "waiting_vehicle_count_by_timestep",
    ]


def test_feeder_loading_result_contains_expected_raw_series_fields():
    assert [field.name for field in fields(FeederLoadingResult)] == [
        "feeder_id",
        "charger_count",
        "total_load_kw_by_timestep",
        "loading_percent_by_timestep",
        "overload_kw_by_timestep",
    ]


def test_power_quality_result_contains_expected_raw_series_fields():
    assert [field.name for field in fields(PowerQualityResult)] == [
        "harmonic_risk_score_by_timestep",
        "current_imbalance_percent_by_timestep",
        "overall_pq_risk_score_by_timestep",
        "phase_a_load_kw_by_timestep",
        "phase_b_load_kw_by_timestep",
        "phase_c_load_kw_by_timestep",
        "feeder_power_quality_results",
    ]


def test_feeder_power_quality_result_contains_expected_raw_series_fields():
    assert [field.name for field in fields(FeederPowerQualityResult)] == [
        "feeder_id",
        "harmonic_risk_score_by_timestep",
        "current_imbalance_percent_by_timestep",
    ]


def test_simulate_returns_raw_outputs_for_scenario():
    result = simulate(default_scenario)
    charging_requests = assign_chargers_fifo(default_scenario)
    request_timestep_series = build_request_timestep_series(
        default_scenario,
        charging_requests,
    )
    delivered_load_profile = generate_uncontrolled_load_profile(
        default_scenario,
        capacity_limit_kw=calculate_available_site_capacity(default_scenario),
    )
    expected_transformer_total_load = [
        calculate_transformer_total_load(
            load_kw,
            default_scenario.transformer_other_load_kw,
        )
        for load_kw in delivered_load_profile
    ]
    expected_feeder_total_load = [
        (load_kw / 2.0) + default_scenario.feeder_base_load_kw
        for load_kw in delivered_load_profile
    ]
    expected_power_quality = build_power_quality_result(
        default_scenario,
        delivered_load_profile,
    )

    assert result == SimulationResult(
        daily_energy_demand=calculate_daily_energy_demand(default_scenario),
        configured_connection_capacity_kw=default_scenario.grid_capacity,
        installed_charger_capacity_kw=calculate_installed_charger_capacity(
            default_scenario
        ),
        available_site_charging_capacity_kw=calculate_available_site_capacity(
            default_scenario
        ),
        requested_load_profile_kw=generate_uncontrolled_load_profile(
            default_scenario,
            capacity_limit_kw=calculate_installed_charger_capacity(default_scenario),
        ),
        delivered_load_profile_kw=generate_uncontrolled_load_profile(
            default_scenario,
            capacity_limit_kw=calculate_available_site_capacity(default_scenario),
        ),
        delivered_energy=calculate_delivered_energy(
            generate_uncontrolled_load_profile(
                default_scenario,
                capacity_limit_kw=calculate_available_site_capacity(default_scenario),
            )
        ),
        unmet_energy=calculate_unmet_energy(
            calculate_daily_energy_demand(default_scenario),
            calculate_delivered_energy(
                generate_uncontrolled_load_profile(
                    default_scenario,
                    capacity_limit_kw=calculate_available_site_capacity(
                        default_scenario
                    ),
                )
            ),
        ),
        charging_requests=charging_requests,
        arrivals_count_by_timestep=request_timestep_series[
            "arrivals_count_by_timestep"
        ],
        charging_start_count_by_timestep=request_timestep_series[
            "charging_start_count_by_timestep"
        ],
        charging_completion_count_by_timestep=request_timestep_series[
            "charging_completion_count_by_timestep"
        ],
        requested_charger_slots_by_timestep=request_timestep_series[
            "requested_charger_slots_by_timestep"
        ],
        occupied_charger_count_by_timestep=request_timestep_series[
            "occupied_charger_count_by_timestep"
        ],
        waiting_vehicle_count_by_timestep=request_timestep_series[
            "waiting_vehicle_count_by_timestep"
        ],
        grid_loading=GridLoadingResult(
            transformer_loading=TransformerLoadingResult(
                total_load_kw_by_timestep=expected_transformer_total_load,
                loading_percent_by_timestep=[
                    calculate_transformer_loading_percent(
                        total_load_kw,
                        default_scenario.transformer_capacity_kw,
                    )
                    for total_load_kw in expected_transformer_total_load
                ],
                overload_kw_by_timestep=[
                    calculate_transformer_overload_kw(
                        total_load_kw,
                        default_scenario.transformer_capacity_kw,
                    )
                    for total_load_kw in expected_transformer_total_load
                ],
            ),
            feeder_loading_results=[
                FeederLoadingResult(
                    feeder_id="feeder-1",
                    charger_count=5,
                    total_load_kw_by_timestep=expected_feeder_total_load,
                    loading_percent_by_timestep=[
                        calculate_transformer_loading_percent(
                            total_load_kw,
                            default_scenario.feeder_capacity_kw,
                        )
                        for total_load_kw in expected_feeder_total_load
                    ],
                    overload_kw_by_timestep=[
                        calculate_transformer_overload_kw(
                            total_load_kw,
                            default_scenario.feeder_capacity_kw,
                        )
                        for total_load_kw in expected_feeder_total_load
                    ],
                ),
                FeederLoadingResult(
                    feeder_id="feeder-2",
                    charger_count=5,
                    total_load_kw_by_timestep=expected_feeder_total_load,
                    loading_percent_by_timestep=[
                        calculate_transformer_loading_percent(
                            total_load_kw,
                            default_scenario.feeder_capacity_kw,
                        )
                        for total_load_kw in expected_feeder_total_load
                    ],
                    overload_kw_by_timestep=[
                        calculate_transformer_overload_kw(
                            total_load_kw,
                            default_scenario.feeder_capacity_kw,
                        )
                        for total_load_kw in expected_feeder_total_load
                    ],
                ),
            ],
        ),
        power_quality=expected_power_quality,
    )


def test_simulate_returns_heavy_duty_reference_outputs():
    result = simulate(default_scenario)
    request_timestep_series = build_request_timestep_series(
        default_scenario,
        result.charging_requests,
    )
    expected_transformer_total_load = [
        load_kw + default_scenario.transformer_other_load_kw
        for load_kw in result.delivered_load_profile_kw
    ]
    expected_feeder_total_load = [
        (load_kw / 2.0) + default_scenario.feeder_base_load_kw
        for load_kw in result.delivered_load_profile_kw
    ]

    assert result.daily_energy_demand == 7500.0
    assert result.configured_connection_capacity_kw == 1000.0
    assert result.installed_charger_capacity_kw == 1500.0
    assert result.available_site_charging_capacity_kw == 1000.0
    assert result.installed_charger_capacity == 1500.0
    assert result.available_site_capacity == 1000.0
    assert result.requested_load_profile_kw == generate_uncontrolled_load_profile(
        default_scenario,
        capacity_limit_kw=calculate_installed_charger_capacity(default_scenario),
    )
    assert result.delivered_load_profile_kw == generate_uncontrolled_load_profile(
        default_scenario,
        capacity_limit_kw=calculate_available_site_capacity(default_scenario),
    )
    assert result.uncontrolled_load_profile == generate_uncontrolled_load_profile(
        default_scenario,
        capacity_limit_kw=calculate_available_site_capacity(default_scenario),
    )
    assert result.delivered_energy == 7500.0
    assert result.unmet_energy == 0.0
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


@pytest.mark.parametrize(
    ("scenario"),
    [
        pytest.param(default_scenario, id="heavy-duty"),
        pytest.param(
            get_scenario_preset(PUBLIC_FAST_CHARGING_PRESET_ID).scenario,
            id="public-fast",
        ),
        pytest.param(
            create_internal_scenario(
                vehicles=0,
                daily_energy_per_vehicle=20.0,
                charger_count=0,
                charger_power=50.0,
                grid_capacity=100.0,
                charging_window_start=time(8, 0),
                charging_window_end=time(9, 0),
            ),
            id="zero-vehicles",
        ),
        pytest.param(
            create_internal_scenario(
                vehicles=2,
                daily_energy_per_vehicle=20.0,
                charger_count=0,
                charger_power=50.0,
                grid_capacity=100.0,
                charging_window_start=time(8, 0),
                charging_window_end=time(9, 0),
            ),
            id="zero-chargers",
        ),
    ],
)
def test_simulate_planner_candidate_matches_full_simulation_service_rule_outputs(
    scenario,
):
    assert scenario is not None

    full_result = simulate(scenario)
    planner_candidate_result = simulate_planner_candidate(scenario)
    started_request_waiting_times_hours = [
        request.waiting_time_hours
        for request in full_result.charging_requests
        if request.charging_start_timestep is not None
        and request.waiting_time_hours is not None
    ]

    assert planner_candidate_result.daily_energy_demand == (
        full_result.daily_energy_demand
    )
    assert planner_candidate_result.request_count == len(
        full_result.charging_requests
    )
    assert planner_candidate_result.started_request_waiting_times_hours == pytest.approx(
        started_request_waiting_times_hours
    )
    assert planner_candidate_result.vehicles_waiting_count == sum(
        waiting_time_hours > 0.0
        for waiting_time_hours in started_request_waiting_times_hours
    )
    assert planner_candidate_result.vehicles_not_started_count == sum(
        request.charging_start_timestep is None
        for request in full_result.charging_requests
    )
    assert planner_candidate_result.vehicles_with_unmet_energy_count == sum(
        request.unmet_energy_kwh > 0.0
        for request in full_result.charging_requests
    )
    assert planner_candidate_result.waiting_vehicle_count_by_timestep == (
        full_result.waiting_vehicle_count_by_timestep
    )


def test_simulate_planner_candidate_context_reuse_does_not_mutate_cached_requests():
    scenario = default_scenario
    context = build_planner_candidate_simulation_context(scenario)
    original_templates = tuple(context.charging_request_templates)

    simulate_planner_candidate(
        replace(scenario, charger_count=scenario.charger_count + 5),
        simulation_context=context,
    )
    simulate_planner_candidate(
        replace(scenario, charger_count=scenario.charger_count + 10),
        simulation_context=context,
    )

    assert context.charging_request_templates == original_templates


def test_simulate_planner_candidate_context_reuse_preserves_strategy_isolation():
    uncontrolled_scenario = replace(
        default_scenario,
        charging_strategy=ChargingStrategy.UNCONTROLLED,
    )
    smart_scenario = replace(
        default_scenario,
        charging_strategy=ChargingStrategy.SMART,
    )
    context = build_planner_candidate_simulation_context(uncontrolled_scenario)

    uncontrolled_with_context = simulate_planner_candidate(
        uncontrolled_scenario,
        simulation_context=context,
    )
    uncontrolled_without_context = simulate_planner_candidate(
        uncontrolled_scenario
    )
    smart_with_context = simulate_planner_candidate(
        smart_scenario,
        simulation_context=context,
    )
    smart_without_context = simulate_planner_candidate(smart_scenario)

    assert uncontrolled_with_context == uncontrolled_without_context
    assert smart_with_context == smart_without_context


def test_simulate_populates_aligned_power_quality_series_for_current_contract():
    result = simulate(default_scenario)

    assert len(result.power_quality.harmonic_risk_score_by_timestep) == (
        TIMESTEPS_PER_DAY
    )
    assert len(result.power_quality.current_imbalance_percent_by_timestep) == (
        TIMESTEPS_PER_DAY
    )
    assert len(result.power_quality.phase_a_load_kw_by_timestep) == TIMESTEPS_PER_DAY
    assert len(result.power_quality.phase_b_load_kw_by_timestep) == TIMESTEPS_PER_DAY
    assert len(result.power_quality.phase_c_load_kw_by_timestep) == TIMESTEPS_PER_DAY
    assert result.power_quality.overall_pq_risk_score_by_timestep == []
    assert len(result.power_quality.feeder_power_quality_results) == (
        default_scenario.feeder_count
    )

    for timestep_index, delivered_load_kw in enumerate(result.delivered_load_profile_kw):
        assert (
            result.power_quality.phase_a_load_kw_by_timestep[timestep_index]
            + result.power_quality.phase_b_load_kw_by_timestep[timestep_index]
            + result.power_quality.phase_c_load_kw_by_timestep[timestep_index]
        ) == pytest.approx(delivered_load_kw)

    for feeder_result in result.power_quality.feeder_power_quality_results:
        assert len(feeder_result.harmonic_risk_score_by_timestep) == TIMESTEPS_PER_DAY
        assert len(feeder_result.current_imbalance_percent_by_timestep) == (
            TIMESTEPS_PER_DAY
        )


def test_simulate_populates_transformer_loading_for_overnight_window_with_full_day_alignment():
    scenario = default_scenario

    result = simulate(scenario)

    assert len(result.grid_loading.transformer_loading.total_load_kw_by_timestep) == 96
    assert len(result.grid_loading.transformer_loading.loading_percent_by_timestep) == 96
    assert len(result.grid_loading.transformer_loading.overload_kw_by_timestep) == 96
    assert (
        result.grid_loading.transformer_loading.total_load_kw_by_timestep[0]
        == result.delivered_load_profile_kw[0] + scenario.transformer_other_load_kw
    )
    assert (
        result.grid_loading.transformer_loading.total_load_kw_by_timestep[-1]
        == result.delivered_load_profile_kw[-1] + scenario.transformer_other_load_kw
    )


def test_simulate_transformer_loading_is_deterministic_across_repeated_runs():
    first_result = simulate(default_scenario)
    second_result = simulate(default_scenario)

    assert first_result.grid_loading == second_result.grid_loading


@pytest.mark.parametrize(
    ("scenario", "expected_total_load", "expected_loading_percent", "expected_overload"),
    [
        (
            _build_transformer_regression_scenario(
                transformer_capacity_kw=150.0,
                transformer_other_load_kw=20.0,
            ),
            _build_full_day_transformer_series(time(8, 0), [120.0], default_value=20.0),
            _build_full_day_transformer_series(
                time(8, 0),
                [80.0],
                default_value=(20.0 / 150.0) * 100.0,
            ),
            _build_full_day_transformer_series(time(8, 0), [0.0]),
        ),
        (
            _build_transformer_regression_scenario(
                transformer_capacity_kw=120.0,
                transformer_other_load_kw=20.0,
            ),
            _build_full_day_transformer_series(time(8, 0), [120.0], default_value=20.0),
            _build_full_day_transformer_series(
                time(8, 0),
                [100.0],
                default_value=(20.0 / 120.0) * 100.0,
            ),
            _build_full_day_transformer_series(time(8, 0), [0.0]),
        ),
        (
            _build_transformer_regression_scenario(
                transformer_capacity_kw=100.0,
                transformer_other_load_kw=20.0,
            ),
            _build_full_day_transformer_series(time(8, 0), [120.0], default_value=20.0),
            _build_full_day_transformer_series(
                time(8, 0),
                [120.0],
                default_value=20.0,
            ),
            _build_full_day_transformer_series(time(8, 0), [20.0]),
        ),
        (
            _build_transformer_regression_scenario(
                transformer_capacity_kw=80.0,
                transformer_other_load_kw=90.0,
                vehicles=0,
            ),
            [90.0] * TIMESTEPS_PER_DAY,
            [112.5] * TIMESTEPS_PER_DAY,
            [10.0] * TIMESTEPS_PER_DAY,
        ),
    ],
)
def test_simulate_matches_transformer_regression_reference_series(
    scenario: Scenario,
    expected_total_load: list[float],
    expected_loading_percent: list[float],
    expected_overload: list[float],
):
    result = simulate(scenario)

    assert result.grid_loading.transformer_loading == TransformerLoadingResult(
        total_load_kw_by_timestep=expected_total_load,
        loading_percent_by_timestep=expected_loading_percent,
        overload_kw_by_timestep=expected_overload,
    )


@pytest.mark.parametrize(
    (
        "scenario",
        "expected_transformer_loading",
        "expected_feeder_loading_results",
    ),
    [
        pytest.param(
            _build_reference_grid_loading_scenario(),
            TransformerLoadingResult(
                total_load_kw_by_timestep=_build_full_day_transformer_series(
                    time(8, 0),
                    [120.0],
                    default_value=20.0,
                ),
                loading_percent_by_timestep=_build_full_day_transformer_series(
                    time(8, 0),
                    [80.0],
                    default_value=(20.0 / 150.0) * 100.0,
                ),
                overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
            ),
            [
                FeederLoadingResult(
                    feeder_id="feeder-1",
                    charger_count=1,
                    total_load_kw_by_timestep=_build_full_day_transformer_series(
                        time(8, 0),
                        [110.0],
                        default_value=10.0,
                    ),
                    loading_percent_by_timestep=_build_full_day_transformer_series(
                        time(8, 0),
                        [(110.0 / 140.0) * 100.0],
                        default_value=(10.0 / 140.0) * 100.0,
                    ),
                    overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                )
            ],
            id="reference-no-overload",
        ),
        pytest.param(
            _build_reference_grid_loading_scenario(
                transformer_capacity_kw=100.0,
            ),
            TransformerLoadingResult(
                total_load_kw_by_timestep=_build_full_day_transformer_series(
                    time(8, 0),
                    [120.0],
                    default_value=20.0,
                ),
                loading_percent_by_timestep=_build_full_day_transformer_series(
                    time(8, 0),
                    [120.0],
                    default_value=20.0,
                ),
                overload_kw_by_timestep=_build_full_day_transformer_series(
                    time(8, 0),
                    [20.0],
                ),
            ),
            [
                FeederLoadingResult(
                    feeder_id="feeder-1",
                    charger_count=1,
                    total_load_kw_by_timestep=_build_full_day_transformer_series(
                        time(8, 0),
                        [110.0],
                        default_value=10.0,
                    ),
                    loading_percent_by_timestep=_build_full_day_transformer_series(
                        time(8, 0),
                        [(110.0 / 140.0) * 100.0],
                        default_value=(10.0 / 140.0) * 100.0,
                    ),
                    overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                )
            ],
            id="reference-transformer-only-overload",
        ),
        pytest.param(
            _build_reference_grid_loading_scenario(
                feeder_capacity_kw=100.0,
            ),
            TransformerLoadingResult(
                total_load_kw_by_timestep=_build_full_day_transformer_series(
                    time(8, 0),
                    [120.0],
                    default_value=20.0,
                ),
                loading_percent_by_timestep=_build_full_day_transformer_series(
                    time(8, 0),
                    [80.0],
                    default_value=(20.0 / 150.0) * 100.0,
                ),
                overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
            ),
            [
                FeederLoadingResult(
                    feeder_id="feeder-1",
                    charger_count=1,
                    total_load_kw_by_timestep=_build_full_day_transformer_series(
                        time(8, 0),
                        [110.0],
                        default_value=10.0,
                    ),
                    loading_percent_by_timestep=_build_full_day_transformer_series(
                        time(8, 0),
                        [(110.0 / 100.0) * 100.0],
                        default_value=(10.0 / 100.0) * 100.0,
                    ),
                    overload_kw_by_timestep=_build_full_day_transformer_series(
                        time(8, 0),
                        [10.0],
                    ),
                )
            ],
            id="reference-feeder-only-overload",
        ),
        pytest.param(
            _build_reference_grid_loading_scenario(
                vehicles=0,
                transformer_capacity_kw=80.0,
                transformer_other_load_kw=90.0,
                feeder_base_load_kw=0.0,
                charging_window_end=time(9, 0),
            ),
            TransformerLoadingResult(
                total_load_kw_by_timestep=[90.0] * TIMESTEPS_PER_DAY,
                loading_percent_by_timestep=[112.5] * TIMESTEPS_PER_DAY,
                overload_kw_by_timestep=[10.0] * TIMESTEPS_PER_DAY,
            ),
            [
                FeederLoadingResult(
                    feeder_id="feeder-1",
                    charger_count=1,
                    total_load_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                    loading_percent_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                    overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                )
            ],
            id="reference-base-load-driven-overload",
        ),
    ],
)
def test_reference_loading_scenarios_produce_expected_raw_grid_outputs(
    scenario: Scenario,
    expected_transformer_loading: TransformerLoadingResult,
    expected_feeder_loading_results: list[FeederLoadingResult],
):
    result = simulate(scenario)

    assert result.grid_loading.transformer_loading == expected_transformer_loading
    assert (
        result.grid_loading.feeder_loading_results
        == expected_feeder_loading_results
    )


def test_reference_smart_charging_comparison_produces_expected_grid_loading_outputs():
    scenario = _build_reference_grid_loading_scenario(
        vehicles=4,
        charger_count=4,
        grid_capacity=400.0,
        transformer_capacity_kw=250.0,
        transformer_other_load_kw=20.0,
        feeder_count=2,
        feeder_capacity_kw=120.0,
        feeder_base_load_kw=10.0,
        charging_window_end=time(9, 0),
    )

    uncontrolled_result, smart_result = simulate_strategy_comparison(scenario)

    assert uncontrolled_result.delivered_load_profile_kw == (
        _build_full_day_transformer_series(time(8, 0), [400.0, 0.0, 0.0, 0.0])
    )
    assert smart_result.delivered_load_profile_kw == (
        _build_full_day_transformer_series(time(8, 0), [100.0, 100.0, 100.0, 100.0])
    )
    assert uncontrolled_result.grid_loading.transformer_loading == (
        TransformerLoadingResult(
            total_load_kw_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [420.0, 20.0, 20.0, 20.0],
                default_value=20.0,
            ),
            loading_percent_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [168.0, 8.0, 8.0, 8.0],
                default_value=8.0,
            ),
            overload_kw_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [170.0, 0.0, 0.0, 0.0],
            ),
        )
    )
    assert smart_result.grid_loading.transformer_loading == (
        TransformerLoadingResult(
            total_load_kw_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [120.0, 120.0, 120.0, 120.0],
                default_value=20.0,
            ),
            loading_percent_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [48.0, 48.0, 48.0, 48.0],
                default_value=8.0,
            ),
            overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
        )
    )
    assert uncontrolled_result.grid_loading.feeder_loading_results == [
        FeederLoadingResult(
            feeder_id="feeder-1",
            charger_count=2,
            total_load_kw_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [210.0, 10.0, 10.0, 10.0],
                default_value=10.0,
            ),
            loading_percent_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [175.0, (10.0 / 120.0) * 100.0, (10.0 / 120.0) * 100.0, (10.0 / 120.0) * 100.0],
                default_value=(10.0 / 120.0) * 100.0,
            ),
            overload_kw_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [90.0, 0.0, 0.0, 0.0],
            ),
        ),
        FeederLoadingResult(
            feeder_id="feeder-2",
            charger_count=2,
            total_load_kw_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [210.0, 10.0, 10.0, 10.0],
                default_value=10.0,
            ),
            loading_percent_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [175.0, (10.0 / 120.0) * 100.0, (10.0 / 120.0) * 100.0, (10.0 / 120.0) * 100.0],
                default_value=(10.0 / 120.0) * 100.0,
            ),
            overload_kw_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [90.0, 0.0, 0.0, 0.0],
            ),
        ),
    ]
    assert smart_result.grid_loading.feeder_loading_results == [
        FeederLoadingResult(
            feeder_id="feeder-1",
            charger_count=2,
            total_load_kw_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [60.0, 60.0, 60.0, 60.0],
                default_value=10.0,
            ),
            loading_percent_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [50.0, 50.0, 50.0, 50.0],
                default_value=(10.0 / 120.0) * 100.0,
            ),
            overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
        ),
        FeederLoadingResult(
            feeder_id="feeder-2",
            charger_count=2,
            total_load_kw_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [60.0, 60.0, 60.0, 60.0],
                default_value=10.0,
            ),
            loading_percent_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [50.0, 50.0, 50.0, 50.0],
                default_value=(10.0 / 120.0) * 100.0,
            ),
            overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
        ),
    ]


def test_simulate_populates_feeder_loading_results_from_delivered_load_profile():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=22.5,
        charger_count=3,
        charger_power=100.0,
        grid_capacity=100.0,
        feeder_count=2,
        feeder_capacity_kw=80.0,
        feeder_base_load_kw=10.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(8, 15),
    )

    result = simulate(scenario)

    assert result.delivered_load_profile_kw[32:36] == [90.0, 0.0, 0.0, 0.0]
    assert result.grid_loading.feeder_loading_results == [
        FeederLoadingResult(
            feeder_id="feeder-1",
            charger_count=2,
            total_load_kw_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [70.0],
                default_value=10.0,
            ),
            loading_percent_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [87.5],
                default_value=12.5,
            ),
            overload_kw_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [0.0],
            ),
        ),
        FeederLoadingResult(
            feeder_id="feeder-2",
            charger_count=1,
            total_load_kw_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [40.0],
                default_value=10.0,
            ),
            loading_percent_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [50.0],
                default_value=12.5,
            ),
            overload_kw_by_timestep=_build_full_day_transformer_series(
                time(8, 0),
                [0.0],
            ),
        ),
    ]


def test_simulation_result_round_trip_preserves_ordered_feeder_loading_results():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=22.5,
        charger_count=3,
        charger_power=100.0,
        grid_capacity=100.0,
        feeder_count=2,
        feeder_capacity_kw=80.0,
        feeder_base_load_kw=10.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(8, 15),
    )
    result = simulate(scenario)

    restored_result = simulation_result_from_dict(simulation_result_to_dict(result))

    assert restored_result.grid_loading.feeder_loading_results == (
        result.grid_loading.feeder_loading_results
    )
    assert [
        feeder_result.feeder_id
        for feeder_result in restored_result.grid_loading.feeder_loading_results
    ] == ["feeder-1", "feeder-2"]
    assert [
        feeder_result.charger_count
        for feeder_result in restored_result.grid_loading.feeder_loading_results
    ] == [2, 1]


def test_simulate_preserves_stable_feeder_ordering_for_raw_feeder_series():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=25.0,
        charger_count=5,
        charger_power=100.0,
        grid_capacity=200.0,
        feeder_count=3,
        feeder_capacity_kw=120.0,
        feeder_base_load_kw=10.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(8, 30),
    )

    result = simulate(scenario)

    assert [
        feeder_result.feeder_id
        for feeder_result in result.grid_loading.feeder_loading_results
    ] == ["feeder-1", "feeder-2", "feeder-3"]
    assert [
        feeder_result.charger_count
        for feeder_result in result.grid_loading.feeder_loading_results
    ] == [2, 2, 1]


def test_feeder_ev_allocations_sum_to_site_ev_load_for_each_timestep():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=22.5,
        charger_count=3,
        charger_power=100.0,
        grid_capacity=100.0,
        transformer_capacity_kw=120.0,
        transformer_other_load_kw=15.0,
        feeder_count=2,
        feeder_capacity_kw=80.0,
        feeder_base_load_kw=10.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(8, 15),
    )

    result = simulate(scenario)
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


def test_expand_feeder_assets_evenly_splits_chargers_across_feeders():
    scenario = create_internal_scenario(
        vehicles=6,
        daily_energy_per_vehicle=25.0,
        charger_count=6,
        charger_power=100.0,
        grid_capacity=600.0,
        feeder_count=3,
        feeder_capacity_kw=250.0,
        feeder_base_load_kw=10.0,
    )

    modeled_feeders = expand_feeder_assets(scenario)

    assert modeled_feeders == [
        ModeledFeeder(
            feeder_id="feeder-1",
            feeder_index=0,
            charger_count=2,
            allocation_share=pytest.approx(1.0 / 3.0),
            capacity_kw=250.0,
            base_load_kw=10.0,
        ),
        ModeledFeeder(
            feeder_id="feeder-2",
            feeder_index=1,
            charger_count=2,
            allocation_share=pytest.approx(1.0 / 3.0),
            capacity_kw=250.0,
            base_load_kw=10.0,
        ),
        ModeledFeeder(
            feeder_id="feeder-3",
            feeder_index=2,
            charger_count=2,
            allocation_share=pytest.approx(1.0 / 3.0),
            capacity_kw=250.0,
            base_load_kw=10.0,
        ),
    ]


def test_expand_feeder_assets_assigns_remainder_to_earliest_feeder_indices():
    scenario = create_internal_scenario(
        vehicles=8,
        daily_energy_per_vehicle=25.0,
        charger_count=8,
        charger_power=100.0,
        grid_capacity=800.0,
        feeder_count=3,
        feeder_capacity_kw=300.0,
        feeder_base_load_kw=15.0,
    )

    modeled_feeders = expand_feeder_assets(scenario)

    assert modeled_feeders == [
        ModeledFeeder(
            feeder_id="feeder-1",
            feeder_index=0,
            charger_count=3,
            allocation_share=pytest.approx(3.0 / 8.0),
            capacity_kw=300.0,
            base_load_kw=15.0,
        ),
        ModeledFeeder(
            feeder_id="feeder-2",
            feeder_index=1,
            charger_count=3,
            allocation_share=pytest.approx(3.0 / 8.0),
            capacity_kw=300.0,
            base_load_kw=15.0,
        ),
        ModeledFeeder(
            feeder_id="feeder-3",
            feeder_index=2,
            charger_count=2,
            allocation_share=pytest.approx(2.0 / 8.0),
            capacity_kw=300.0,
            base_load_kw=15.0,
        ),
    ]


def test_expand_feeder_assets_returns_single_feeder_when_only_one_feeder_is_configured():
    scenario = create_internal_scenario(
        vehicles=4,
        daily_energy_per_vehicle=25.0,
        charger_count=4,
        charger_power=100.0,
        grid_capacity=400.0,
        feeder_count=1,
        feeder_capacity_kw=500.0,
        feeder_base_load_kw=20.0,
    )

    modeled_feeders = expand_feeder_assets(scenario)

    assert modeled_feeders == [
        ModeledFeeder(
            feeder_id="feeder-1",
            feeder_index=0,
            charger_count=4,
            allocation_share=1.0,
            capacity_kw=500.0,
            base_load_kw=20.0,
        )
    ]


def test_expand_feeder_assets_preserves_zero_charger_internal_boundary_scenario():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=25.0,
        charger_count=0,
        charger_power=100.0,
        grid_capacity=400.0,
        feeder_count=3,
        feeder_capacity_kw=200.0,
        feeder_base_load_kw=12.5,
    )

    modeled_feeders = expand_feeder_assets(scenario)

    assert modeled_feeders == [
        ModeledFeeder(
            feeder_id="feeder-1",
            feeder_index=0,
            charger_count=0,
            allocation_share=0.0,
            capacity_kw=200.0,
            base_load_kw=12.5,
        ),
        ModeledFeeder(
            feeder_id="feeder-2",
            feeder_index=1,
            charger_count=0,
            allocation_share=0.0,
            capacity_kw=200.0,
            base_load_kw=12.5,
        ),
        ModeledFeeder(
            feeder_id="feeder-3",
            feeder_index=2,
            charger_count=0,
            allocation_share=0.0,
            capacity_kw=200.0,
            base_load_kw=12.5,
        ),
    ]


def test_expand_feeder_assets_supports_deterministic_configured_shares():
    scenario = create_internal_scenario(
        vehicles=8,
        daily_energy_per_vehicle=25.0,
        charger_count=8,
        charger_power=100.0,
        grid_capacity=800.0,
        feeder_count=3,
        feeder_capacity_kw=300.0,
        feeder_base_load_kw=15.0,
        feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CONFIGURED_SHARE,
        feeder_allocation_shares=[0.5, 0.3, 0.2],
    )

    modeled_feeders = expand_feeder_assets(scenario)

    assert modeled_feeders == [
        ModeledFeeder(
            feeder_id="feeder-1",
            feeder_index=0,
            charger_count=4,
            allocation_share=0.5,
            capacity_kw=300.0,
            base_load_kw=15.0,
        ),
        ModeledFeeder(
            feeder_id="feeder-2",
            feeder_index=1,
            charger_count=2,
            allocation_share=0.3,
            capacity_kw=300.0,
            base_load_kw=15.0,
        ),
        ModeledFeeder(
            feeder_id="feeder-3",
            feeder_index=2,
            charger_count=2,
            allocation_share=0.2,
            capacity_kw=300.0,
            base_load_kw=15.0,
        ),
    ]


def test_simulate_supports_public_fast_charging_preset_outputs():
    public_fast_charging = get_scenario_preset(
        PUBLIC_FAST_CHARGING_PRESET_ID
    ).scenario
    assert public_fast_charging is not None

    result = simulate(public_fast_charging)

    assert result.daily_energy_demand == (
        public_fast_charging.vehicles
        * public_fast_charging.daily_energy_per_vehicle
    )
    assert result.configured_connection_capacity_kw == 1200.0
    assert result.installed_charger_capacity_kw == 1800.0
    assert result.available_site_charging_capacity_kw == 1200.0
    assert len(result.charging_requests) == public_fast_charging.vehicles
    assert len(result.arrivals_count_by_timestep) == 96
    assert len(result.requested_charger_slots_by_timestep) == 96
    assert len(result.occupied_charger_count_by_timestep) == 96
    assert len(result.waiting_vehicle_count_by_timestep) == 96
    assert sum(result.arrivals_count_by_timestep) == public_fast_charging.vehicles
    assert {
        (request.departure_timestep - request.arrival_timestep) % 96
        for request in result.charging_requests
    } == {1, 2, 3}
    assert max(result.requested_load_profile_kw) <= 1800.0
    assert max(result.delivered_load_profile_kw) <= 1200.0
    assert result.charging_requests == assign_chargers_fifo(public_fast_charging)


def test_simulate_selects_smart_profile_for_smart_strategy():
    scenario = replace(default_scenario, charging_strategy=ChargingStrategy.SMART)

    result = simulate(scenario)

    assert isinstance(result, SimulationResult)
    assert result.requested_load_profile_kw == generate_smart_load_profile(
        scenario,
        capacity_limit_kw=calculate_installed_charger_capacity(scenario),
    )
    assert result.delivered_load_profile_kw == generate_smart_load_profile(
        scenario,
        capacity_limit_kw=calculate_available_site_capacity(scenario),
    )
    assert result.uncontrolled_load_profile == generate_smart_load_profile(
        scenario,
        capacity_limit_kw=calculate_available_site_capacity(scenario),
    )
    assert result.uncontrolled_load_profile != generate_uncontrolled_load_profile(
        scenario,
        capacity_limit_kw=calculate_available_site_capacity(scenario),
    )
    assert result.delivered_energy == calculate_daily_energy_demand(scenario)
    assert result.unmet_energy == 0.0


def test_simulate_preserves_uncontrolled_behavior_for_uncontrolled_strategy():
    scenario = replace(
        default_scenario,
        charging_strategy=ChargingStrategy.UNCONTROLLED,
    )

    result = simulate(scenario)

    assert isinstance(result, SimulationResult)
    assert result.requested_load_profile_kw == generate_uncontrolled_load_profile(
        scenario,
        capacity_limit_kw=calculate_installed_charger_capacity(scenario),
    )
    assert result.uncontrolled_load_profile == generate_uncontrolled_load_profile(
        scenario,
        capacity_limit_kw=calculate_available_site_capacity(scenario),
    )


def test_simulate_raises_clear_error_for_unsupported_strategy():
    scenario = replace(default_scenario)
    object.__setattr__(scenario, "charging_strategy", "Grid Aware")

    with pytest.raises(ValueError, match="Unsupported charging strategy"):
        simulate(scenario)


def test_simulate_reports_limited_delivered_energy_when_capacity_is_insufficient():
    scenario = Scenario(
        vehicles=20,
        daily_energy_per_vehicle=100.0,
        charger_count=1,
        charger_power=100.0,
        grid_capacity=100.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    )

    result = simulate(scenario)

    assert result.daily_energy_demand == 2000.0
    assert result.delivered_energy == 400.0
    assert result.unmet_energy == 1600.0
    assert result.delivered_energy < result.daily_energy_demand
    assert result.unmet_energy > 0.0


def test_existing_scenario_without_explicit_arrival_inputs_still_simulates():
    scenario = Scenario(
        vehicles=20,
        daily_energy_per_vehicle=100.0,
        charger_count=4,
        charger_power=100.0,
        grid_capacity=150.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    )

    result = simulate(scenario)

    assert result.daily_energy_demand == 2000.0
    assert len(result.requested_load_profile_kw) == len(result.delivered_load_profile_kw)
    assert result.requested_load_profile_kw
    assert result.delivered_load_profile_kw
    assert result.charging_requests == assign_chargers_fifo(scenario)
    assert result.arrivals_count_by_timestep == generate_arrivals_count_by_timestep(
        scenario
    )


def test_requested_profile_ignores_configured_connection_capacity_clipping():
    scenario = Scenario(
        vehicles=20,
        daily_energy_per_vehicle=100.0,
        charger_count=4,
        charger_power=100.0,
        grid_capacity=150.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    )

    requested_profile, delivered_profile = _generate_requested_and_delivered_load_profiles(
        scenario
    )

    assert max(requested_profile) == 400.0
    assert max(delivered_profile) == 150.0
    assert max(requested_profile) > scenario.grid_capacity


def test_simulation_result_exposes_dual_profiles_and_explicit_capacity_fields():
    result = simulate(default_scenario)

    assert result.configured_connection_capacity_kw == default_scenario.grid_capacity
    assert (
        result.installed_charger_capacity_kw
        == default_scenario.charger_count * default_scenario.charger_power
    )
    assert result.available_site_charging_capacity_kw == min(
        result.installed_charger_capacity_kw,
        result.configured_connection_capacity_kw,
    )
    assert len(result.requested_load_profile_kw) == len(result.delivered_load_profile_kw)


def test_load_profile_alias_returns_delivered_profile_values():
    result = simulate(default_scenario)

    assert result.load_profile == result.delivered_load_profile_kw
    assert result.uncontrolled_load_profile == result.delivered_load_profile_kw


def test_requested_profile_never_exceeds_installed_charger_capacity():
    scenario = Scenario(
        vehicles=20,
        daily_energy_per_vehicle=100.0,
        charger_count=4,
        charger_power=100.0,
        grid_capacity=150.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    )

    requested_profile, _delivered_profile = _generate_requested_and_delivered_load_profiles(
        scenario
    )

    assert all(
        load <= calculate_installed_charger_capacity(scenario)
        for load in requested_profile
    )


def test_delivered_profile_never_exceeds_available_site_capacity():
    scenario = Scenario(
        vehicles=20,
        daily_energy_per_vehicle=100.0,
        charger_count=4,
        charger_power=100.0,
        grid_capacity=150.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    )

    _requested_profile, delivered_profile = _generate_requested_and_delivered_load_profiles(
        scenario
    )

    assert all(
        load <= calculate_available_site_capacity(scenario)
        for load in delivered_profile
    )


def test_requested_and_delivered_profiles_are_identical_when_connection_capacity_is_not_limiting():
    scenario = Scenario(
        vehicles=20,
        daily_energy_per_vehicle=100.0,
        charger_count=4,
        charger_power=100.0,
        grid_capacity=500.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    )

    requested_profile, delivered_profile = _generate_requested_and_delivered_load_profiles(
        scenario
    )

    assert requested_profile == delivered_profile


def test_requested_and_delivered_profiles_differ_when_connection_capacity_is_limiting():
    scenario = Scenario(
        vehicles=20,
        daily_energy_per_vehicle=100.0,
        charger_count=4,
        charger_power=100.0,
        grid_capacity=150.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    )

    requested_profile, delivered_profile = _generate_requested_and_delivered_load_profiles(
        scenario
    )

    assert requested_profile != delivered_profile


@pytest.mark.parametrize("charging_strategy", list(ChargingStrategy))
def test_dual_profile_generation_uses_selected_strategy_for_requested_and_delivered_profiles(
    charging_strategy: ChargingStrategy,
):
    scenario = Scenario(
        vehicles=20,
        daily_energy_per_vehicle=100.0,
        charger_count=4,
        charger_power=100.0,
        grid_capacity=150.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
        charging_strategy=charging_strategy,
    )

    requested_profile, delivered_profile = _generate_requested_and_delivered_load_profiles(
        scenario
    )

    assert requested_profile
    assert delivered_profile
    assert len(requested_profile) == len(delivered_profile)
    assert all(
        load <= calculate_installed_charger_capacity(scenario)
        for load in requested_profile
    )
    assert all(
        load <= calculate_available_site_capacity(scenario)
        for load in delivered_profile
    )


def test_simulate_continues_to_expose_delivered_profile_when_connection_capacity_is_limiting():
    scenario = Scenario(
        vehicles=20,
        daily_energy_per_vehicle=100.0,
        charger_count=4,
        charger_power=100.0,
        grid_capacity=150.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    )

    requested_profile, delivered_profile = _generate_requested_and_delivered_load_profiles(
        scenario
    )
    result = simulate(scenario)

    assert requested_profile != delivered_profile
    assert result.delivered_load_profile_kw == delivered_profile
    assert result.uncontrolled_load_profile == delivered_profile


def test_calculate_unmet_energy_is_never_negative():
    assert calculate_unmet_energy(
        daily_energy_demand=100.0,
        delivered_energy=120.0,
    ) == 0.0


def test_simulate_zero_vehicles_with_available_chargers_returns_zero_demand_and_load():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=150.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=500.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    )

    result = simulate(scenario)

    assert result.daily_energy_demand == 0.0
    assert result.installed_charger_capacity_kw == 100.0
    assert result.available_site_charging_capacity_kw == 100.0
    assert set(result.requested_load_profile_kw) == {0.0}
    assert set(result.delivered_load_profile_kw) == {0.0}
    assert set(result.arrivals_count_by_timestep) == {0}
    assert result.delivered_energy == 0.0
    assert result.unmet_energy == 0.0
    assert result.charging_requests == []


def test_simulate_zero_chargers_with_vehicles_returns_zero_load_and_unmet_demand():
    scenario = create_internal_scenario(
        vehicles=5,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=500.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    )

    result = simulate(scenario)

    assert result.daily_energy_demand == 100.0
    assert result.installed_charger_capacity_kw == 0.0
    assert result.available_site_charging_capacity_kw == 0.0
    assert set(result.requested_load_profile_kw) == {0.0}
    assert set(result.delivered_load_profile_kw) == {0.0}
    assert sum(result.arrivals_count_by_timestep) == scenario.vehicles
    assert result.delivered_energy == 0.0
    assert result.unmet_energy == 100.0
    assert len(result.charging_requests) == scenario.vehicles
    assert all(
        request.charging_start_timestep is None
        for request in result.charging_requests
    )


def test_simulate_keeps_request_trace_and_queue_series_aligned_under_turnover():
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
        request_energy_variability_percent=50.0,
    )

    result = simulate(scenario)

    assert [request.waiting_time_hours for request in result.charging_requests] == [
        0.0,
        0.25,
        0.75,
    ]
    assert result.charging_start_count_by_timestep[32:39] == [1, 1, 0, 1, 0, 0, 0]
    assert result.charging_completion_count_by_timestep[32:39] == [
        0,
        1,
        0,
        1,
        0,
        0,
        1,
    ]
    assert result.requested_charger_slots_by_timestep[32:39] == [3, 2, 2, 1, 1, 1, 0]
    assert result.occupied_charger_count_by_timestep[32:39] == [1, 1, 1, 1, 1, 1, 0]
    assert result.waiting_vehicle_count_by_timestep[32:39] == [2, 1, 1, 0, 0, 0, 0]
    assert result.delivered_load_profile_kw[32:39] == [
        40.0,
        50.0,
        30.0,
        50.0,
        50.0,
        20.0,
        0.0,
    ]


def test_simulate_zero_vehicles_and_zero_chargers_returns_zero_outputs():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=150.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=500.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    )

    result = simulate(scenario)

    assert result.daily_energy_demand == 0.0
    assert result.installed_charger_capacity_kw == 0.0
    assert result.available_site_charging_capacity_kw == 0.0
    assert set(result.requested_load_profile_kw) == {0.0}
    assert set(result.delivered_load_profile_kw) == {0.0}
    assert set(result.arrivals_count_by_timestep) == {0}
    assert result.delivered_energy == 0.0
    assert result.unmet_energy == 0.0
    assert result.charging_requests == []


def test_simulation_result_is_immutable():
    result = simulate(default_scenario)

    with pytest.raises(FrozenInstanceError):
        result.daily_energy_demand = 1.0


def test_simulation_result_constructor_uses_backward_compatible_defaults():
    result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=120.0,
        installed_charger_capacity_kw=150.0,
        available_site_charging_capacity_kw=120.0,
        delivered_load_profile_kw=[80.0, 40.0],
    )

    assert result.requested_load_profile_kw == [80.0, 40.0]
    assert result.delivered_load_profile_kw == [80.0, 40.0]
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


def test_simulation_result_rejects_mismatched_load_profile_lengths():
    with pytest.raises(
        ValueError,
        match=(
            "requested_load_profile_kw and delivered_load_profile_kw must have "
            "matching timestep lengths."
        ),
    ):
        SimulationResult(
            daily_energy_demand=100.0,
            configured_connection_capacity_kw=120.0,
            installed_charger_capacity_kw=150.0,
            available_site_charging_capacity_kw=120.0,
            requested_load_profile_kw=[100.0, 0.0],
            delivered_load_profile_kw=[80.0],
        )


def test_charging_request_result_is_immutable():
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
        delayed_start_reason="charger_availability_constraint",
        unmet_energy_reason="charger_availability_constraint",
    )

    with pytest.raises(FrozenInstanceError):
        request_result.request_id = "request-1"
