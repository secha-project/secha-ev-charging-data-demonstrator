from dataclasses import replace
from datetime import time
from math import isclose

from scenarios import (
    ChargingStrategy,
    PowerQualityPhaseAllocationMethod,
    create_internal_scenario,
)
from simulation import (
    FeederPhaseAllocation,
    allocate_feeder_ev_load_to_phases,
    build_feeder_phase_allocations,
    build_power_quality_result,
    build_site_phase_load_series,
    calculate_current_imbalance_percent,
    simulate,
)


def _build_reference_power_quality_scenario(
    *,
    vehicles: int = 3,
    charger_count: int = 3,
    charger_power: float = 50.0,
    grid_capacity: float = 150.0,
    charging_window_end: time = time(8, 15),
    charging_strategy: ChargingStrategy = ChargingStrategy.UNCONTROLLED,
    charger_harmonic_factor: float = 1.0,
    power_quality_phase_allocation_method: PowerQualityPhaseAllocationMethod = (
        PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
    ),
):
    return create_internal_scenario(
        vehicles=vehicles,
        daily_energy_per_vehicle=25.0,
        charger_count=charger_count,
        charger_power=charger_power,
        grid_capacity=grid_capacity,
        charging_window_start=time(8, 0),
        charging_window_end=charging_window_end,
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        charging_strategy=charging_strategy,
        single_phase_charger_share_percent=100.0,
        charger_harmonic_factor=charger_harmonic_factor,
        power_quality_phase_allocation_method=(
            power_quality_phase_allocation_method
        ),
    )


def test_build_site_phase_load_series_balances_single_phase_chargers_round_robin():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=25.0,
        charger_count=3,
        charger_power=50.0,
        grid_capacity=150.0,
        single_phase_charger_share_percent=100.0,
        power_quality_phase_allocation_method=(
            PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
        ),
    )

    phase_a_load_kw_by_timestep, phase_b_load_kw_by_timestep, phase_c_load_kw_by_timestep = (
        build_site_phase_load_series(scenario, [90.0])
    )

    assert phase_a_load_kw_by_timestep == [30.0]
    assert phase_b_load_kw_by_timestep == [30.0]
    assert phase_c_load_kw_by_timestep == [30.0]
    assert isclose(
        phase_a_load_kw_by_timestep[0]
        + phase_b_load_kw_by_timestep[0]
        + phase_c_load_kw_by_timestep[0],
        90.0,
    )


def test_build_site_phase_load_series_can_intentionally_front_load_phase_a():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=25.0,
        charger_count=3,
        charger_power=50.0,
        grid_capacity=150.0,
        single_phase_charger_share_percent=100.0,
        power_quality_phase_allocation_method=(
            PowerQualityPhaseAllocationMethod.FRONT_LOADED_PHASE_A
        ),
    )

    phase_a_load_kw_by_timestep, phase_b_load_kw_by_timestep, phase_c_load_kw_by_timestep = (
        build_site_phase_load_series(scenario, [90.0])
    )

    assert phase_a_load_kw_by_timestep == [90.0]
    assert phase_b_load_kw_by_timestep == [0.0]
    assert phase_c_load_kw_by_timestep == [0.0]


def test_build_site_phase_load_series_keeps_zero_load_series_zero():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=25.0,
        charger_count=3,
        charger_power=50.0,
        grid_capacity=150.0,
        single_phase_charger_share_percent=100.0,
        power_quality_phase_allocation_method=(
            PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
        ),
    )

    phase_a_load_kw_by_timestep, phase_b_load_kw_by_timestep, phase_c_load_kw_by_timestep = (
        build_site_phase_load_series(scenario, [0.0, 0.0, 0.0])
    )

    assert phase_a_load_kw_by_timestep == [0.0, 0.0, 0.0]
    assert phase_b_load_kw_by_timestep == [0.0, 0.0, 0.0]
    assert phase_c_load_kw_by_timestep == [0.0, 0.0, 0.0]


def test_build_feeder_phase_allocations_preserves_deterministic_feeder_order():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=25.0,
        charger_count=5,
        charger_power=50.0,
        grid_capacity=250.0,
        feeder_count=2,
        single_phase_charger_share_percent=40.0,
        power_quality_phase_allocation_method=(
            PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
        ),
    )

    feeder_phase_allocations = build_feeder_phase_allocations(scenario)

    assert [allocation.feeder_id for allocation in feeder_phase_allocations] == [
        "feeder-1",
        "feeder-2",
    ]
    assert feeder_phase_allocations == [
        FeederPhaseAllocation(
            feeder_id="feeder-1",
            charger_count=3,
            single_phase_charger_count=1,
            three_phase_charger_count=2,
            phase_a_equivalent_charger_count=1 + (2 / 3),
            phase_b_equivalent_charger_count=2 / 3,
            phase_c_equivalent_charger_count=2 / 3,
        ),
        FeederPhaseAllocation(
            feeder_id="feeder-2",
            charger_count=2,
            single_phase_charger_count=1,
            three_phase_charger_count=1,
            phase_a_equivalent_charger_count=1 / 3,
            phase_b_equivalent_charger_count=1 + (1 / 3),
            phase_c_equivalent_charger_count=1 / 3,
        ),
    ]


def test_allocate_feeder_ev_load_to_phases_returns_zeroes_when_no_load_exists():
    feeder_phase_allocation = FeederPhaseAllocation(
        feeder_id="feeder-1",
        charger_count=3,
        single_phase_charger_count=3,
        three_phase_charger_count=0,
        phase_a_equivalent_charger_count=1.0,
        phase_b_equivalent_charger_count=1.0,
        phase_c_equivalent_charger_count=1.0,
    )

    assert allocate_feeder_ev_load_to_phases(
        0.0,
        feeder_phase_allocation,
    ) == (0.0, 0.0, 0.0)


def test_build_power_quality_result_higher_concurrent_load_raises_harmonic_risk():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=25.0,
        charger_count=3,
        charger_power=50.0,
        grid_capacity=150.0,
        single_phase_charger_share_percent=100.0,
        charger_harmonic_factor=1.0,
    )

    low_load_result = build_power_quality_result(scenario, [30.0])
    high_load_result = build_power_quality_result(scenario, [120.0])

    assert len(low_load_result.harmonic_risk_score_by_timestep) == 1
    assert len(high_load_result.harmonic_risk_score_by_timestep) == 1
    assert 0.0 <= low_load_result.harmonic_risk_score_by_timestep[0] <= 100.0
    assert 0.0 <= high_load_result.harmonic_risk_score_by_timestep[0] <= 100.0
    assert (
        high_load_result.harmonic_risk_score_by_timestep[0]
        > low_load_result.harmonic_risk_score_by_timestep[0]
    )


def test_build_power_quality_result_higher_single_phase_share_raises_harmonic_risk():
    base_scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=25.0,
        charger_count=3,
        charger_power=50.0,
        grid_capacity=150.0,
        single_phase_charger_share_percent=0.0,
        charger_harmonic_factor=1.0,
    )

    low_share_result = build_power_quality_result(base_scenario, [90.0])
    high_share_result = build_power_quality_result(
        replace(base_scenario, single_phase_charger_share_percent=100.0),
        [90.0],
    )

    assert len(low_share_result.harmonic_risk_score_by_timestep) == 1
    assert len(high_share_result.harmonic_risk_score_by_timestep) == 1
    assert (
        high_share_result.harmonic_risk_score_by_timestep[0]
        > low_share_result.harmonic_risk_score_by_timestep[0]
    )


def test_calculate_current_imbalance_percent_returns_zero_for_balanced_loads():
    assert calculate_current_imbalance_percent((30.0, 30.0, 30.0)) == 0.0


def test_build_power_quality_result_heavier_single_phase_loading_raises_current_imbalance():
    balanced_scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=25.0,
        charger_count=3,
        charger_power=50.0,
        grid_capacity=150.0,
        single_phase_charger_share_percent=100.0,
        power_quality_phase_allocation_method=(
            PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
        ),
    )
    unbalanced_scenario = replace(
        balanced_scenario,
        power_quality_phase_allocation_method=(
            PowerQualityPhaseAllocationMethod.FRONT_LOADED_PHASE_A
        ),
    )

    balanced_result = build_power_quality_result(balanced_scenario, [90.0])
    unbalanced_result = build_power_quality_result(unbalanced_scenario, [90.0])

    assert balanced_result.current_imbalance_percent_by_timestep == [0.0]
    assert (
        unbalanced_result.current_imbalance_percent_by_timestep[0]
        > balanced_result.current_imbalance_percent_by_timestep[0]
    )
    assert (
        unbalanced_result.current_imbalance_percent_by_timestep[0]
        == 200.0
    )
    assert (
        unbalanced_result.feeder_power_quality_results[0]
        .current_imbalance_percent_by_timestep
        == [200.0]
    )


def test_build_power_quality_result_zero_load_keeps_current_imbalance_zero():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=25.0,
        charger_count=3,
        charger_power=50.0,
        grid_capacity=150.0,
        single_phase_charger_share_percent=100.0,
        power_quality_phase_allocation_method=(
            PowerQualityPhaseAllocationMethod.FRONT_LOADED_PHASE_A
        ),
    )

    result = build_power_quality_result(scenario, [0.0, 0.0, 0.0])

    assert result.current_imbalance_percent_by_timestep == [0.0, 0.0, 0.0]
    assert (
        result.feeder_power_quality_results[0].current_imbalance_percent_by_timestep
        == [0.0, 0.0, 0.0]
    )


def test_simulate_strategy_variants_can_change_harmonic_risk_profile_shape_consistently():
    base_scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
        single_phase_charger_share_percent=100.0,
        charger_harmonic_factor=1.2,
    )

    uncontrolled_result = simulate(
        replace(base_scenario, charging_strategy=ChargingStrategy.UNCONTROLLED)
    )
    smart_result = simulate(
        replace(base_scenario, charging_strategy=ChargingStrategy.SMART)
    )

    assert len(uncontrolled_result.power_quality.harmonic_risk_score_by_timestep) == len(
        uncontrolled_result.delivered_load_profile_kw
    )
    assert len(smart_result.power_quality.harmonic_risk_score_by_timestep) == len(
        smart_result.delivered_load_profile_kw
    )
    assert len(uncontrolled_result.power_quality.feeder_power_quality_results) == 1
    assert len(smart_result.power_quality.feeder_power_quality_results) == 1
    assert (
        uncontrolled_result.power_quality.feeder_power_quality_results[0].feeder_id
        == smart_result.power_quality.feeder_power_quality_results[0].feeder_id
        == "feeder-1"
    )
    assert len(
        uncontrolled_result.power_quality.feeder_power_quality_results[
            0
        ].harmonic_risk_score_by_timestep
    ) == len(uncontrolled_result.delivered_load_profile_kw)
    assert len(
        smart_result.power_quality.feeder_power_quality_results[
            0
        ].harmonic_risk_score_by_timestep
    ) == len(smart_result.delivered_load_profile_kw)
    assert (
        uncontrolled_result.power_quality.harmonic_risk_score_by_timestep
        != smart_result.power_quality.harmonic_risk_score_by_timestep
    )
    assert max(
        uncontrolled_result.power_quality.harmonic_risk_score_by_timestep
    ) > max(smart_result.power_quality.harmonic_risk_score_by_timestep)


def test_simulate_power_quality_regression_balanced_reference_case():
    scenario = _build_reference_power_quality_scenario()

    result = simulate(scenario).power_quality

    assert [
        (index, value)
        for index, value in enumerate(result.harmonic_risk_score_by_timestep)
        if value
    ] == [(32, 61.25)]
    assert result.current_imbalance_percent_by_timestep == [0.0] * 96
    assert result.phase_a_load_kw_by_timestep[32] == 50.0
    assert result.phase_b_load_kw_by_timestep[32] == 50.0
    assert result.phase_c_load_kw_by_timestep[32] == 50.0
    assert result.feeder_power_quality_results[0].harmonic_risk_score_by_timestep == (
        result.harmonic_risk_score_by_timestep
    )
    assert (
        result.feeder_power_quality_results[0].current_imbalance_percent_by_timestep
        == result.current_imbalance_percent_by_timestep
    )


def test_simulate_power_quality_regression_unbalanced_reference_case():
    scenario = _build_reference_power_quality_scenario(
        power_quality_phase_allocation_method=(
            PowerQualityPhaseAllocationMethod.FRONT_LOADED_PHASE_A
        )
    )

    result = simulate(scenario).power_quality

    assert [
        (index, value)
        for index, value in enumerate(result.harmonic_risk_score_by_timestep)
        if value
    ] == [(32, 87.5)]
    assert [
        (index, value)
        for index, value in enumerate(result.current_imbalance_percent_by_timestep)
        if value
    ] == [(32, 200.0)]
    assert result.phase_a_load_kw_by_timestep[32] == 150.0
    assert result.phase_b_load_kw_by_timestep[32] == 0.0
    assert result.phase_c_load_kw_by_timestep[32] == 0.0


def test_simulate_power_quality_regression_high_harmonic_reference_case():
    scenario = _build_reference_power_quality_scenario(
        vehicles=2,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=200.0,
        charging_window_end=time(9, 0),
        charger_harmonic_factor=2.0,
        power_quality_phase_allocation_method=(
            PowerQualityPhaseAllocationMethod.FRONT_LOADED_PHASE_A
        ),
    )

    result = simulate(scenario).power_quality

    assert [
        (index, value)
        for index, value in enumerate(result.harmonic_risk_score_by_timestep)
        if value
    ] == [(32, 100.0)]
    assert [
        (index, value)
        for index, value in enumerate(result.current_imbalance_percent_by_timestep)
        if value
    ] == [(32, 200.0)]
    assert result.phase_a_load_kw_by_timestep[32] == 200.0
    assert result.phase_b_load_kw_by_timestep[32] == 0.0
    assert result.phase_c_load_kw_by_timestep[32] == 0.0


def test_simulate_power_quality_regression_smart_charging_tradeoff_case():
    base_scenario = _build_reference_power_quality_scenario(
        vehicles=2,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=200.0,
        charging_window_end=time(9, 0),
        charger_harmonic_factor=1.2,
        power_quality_phase_allocation_method=(
            PowerQualityPhaseAllocationMethod.FRONT_LOADED_PHASE_A
        ),
    )

    uncontrolled_result = simulate(
        replace(base_scenario, charging_strategy=ChargingStrategy.UNCONTROLLED)
    ).power_quality
    smart_result = simulate(
        replace(base_scenario, charging_strategy=ChargingStrategy.SMART)
    ).power_quality

    assert [
        (index, value)
        for index, value in enumerate(uncontrolled_result.harmonic_risk_score_by_timestep)
        if value
    ] == [(32, 90.0)]
    assert [
        (index, value)
        for index, value in enumerate(smart_result.harmonic_risk_score_by_timestep)
        if value
    ] == [(32, 22.5), (33, 22.5), (34, 22.5), (35, 22.5)]
    assert [
        (index, value)
        for index, value in enumerate(smart_result.current_imbalance_percent_by_timestep)
        if value
    ] == [(32, 200.0), (33, 200.0), (34, 200.0), (35, 200.0)]
    assert uncontrolled_result.phase_a_load_kw_by_timestep[32] == 200.0
    assert smart_result.phase_a_load_kw_by_timestep[32:36] == [50.0, 50.0, 50.0, 50.0]
