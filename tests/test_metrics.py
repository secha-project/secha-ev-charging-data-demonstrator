import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import time

import pytest

from metrics import (
    FeederSummaryMetrics,
    Metrics,
    POWER_QUALITY_RISK_HIGH,
    POWER_QUALITY_RISK_LOW,
    POWER_QUALITY_RISK_MODERATE,
    SCENARIO_CHANGE_NONE,
    SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT,
    SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL,
    SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF,
    SCENARIO_SECTION_IMPACT_MAJOR,
    SCENARIO_SECTION_IMPACT_MINOR,
    SCENARIO_SECTION_IMPACT_NONE,
    SCENARIO_SECTION_SUMMARY_LITTLE_NO_CHANGE,
    SCENARIO_SECTION_SUMMARY_MAJOR_CHANGES,
    SCENARIO_SECTION_SUMMARY_TRADE_OFFS,
    SCENARIO_SECTION_VISUALIZATION_NONE,
    SCENARIO_SECTION_VISUALIZATION_SUPPORTING_WHEN_USEFUL,
    SCENARIO_CHANGE_OPTIONAL_DELTA,
    SCENARIO_VALUE_OPTIONAL_NOT_APPLICABLE,
    THERMAL_RISK_HIGH,
    THERMAL_RISK_LOW,
    THERMAL_RISK_MODERATE,
    build_overall_pq_risk_score_series,
    calculate_threshold_duration_hours,
    calculate_annual_energy,
    calculate_comparison_metrics,
    classify_thermal_risk,
    classify_power_quality_risk,
    calculate_metrics,
    ScenarioComparisonMetrics,
    calculate_scenario_comparison_metrics,
    highest_thermal_risk_level,
    metrics_from_dict,
    metrics_to_dict,
    prepare_scenario_comparison_display_data,
)
import metrics.metrics as metrics_module
from metrics.metrics import format_primary_constraint_reason_label
from metrics.metrics import (
    _calculate_direct_metrics_values,
    _calculate_planner_diagnostic_values,
)
from metrics.planning import (
    connection_upgrade_avoided_by_smart,
    connection_upgrade_required,
    infrastructure_recommendation_changed_by_smart,
    infrastructure_impact_summary,
    primary_constraint_shift_summary,
    service_impact_summary,
    service_rule_is_met,
    service_rule_worsened_by_smart,
)
from scenarios import (
    ChargingStrategy,
    PowerQualityPhaseAllocationMethod,
    create_internal_scenario,
    default_scenario,
)
from simulation import (
    SimulationResult,
    simulate,
    simulate_strategy_comparison,
    simulation_result_from_dict,
)
from simulation.result import (
    ChargingRequestResult,
    FeederLoadingResult,
    GridLoadingResult,
    PowerQualityResult,
    TransformerLoadingResult,
)
from simulation.time import TIMESTEPS_PER_DAY, get_timestep_hours, time_to_timestep_index


def _build_status_test_result(
    *,
    daily_energy_demand: float,
    configured_connection_capacity_kw: float,
    requested_load_profile_kw: list[float],
    delivered_load_profile_kw: list[float],
    installed_charger_capacity_kw: float | None = None,
    available_site_charging_capacity_kw: float | None = None,
) -> SimulationResult:
    """Build a simulation result for feasibility-status tests."""
    if installed_charger_capacity_kw is None:
        installed_charger_capacity_kw = max(requested_load_profile_kw, default=0.0)

    if available_site_charging_capacity_kw is None:
        available_site_charging_capacity_kw = min(
            installed_charger_capacity_kw,
            configured_connection_capacity_kw,
        )

    return SimulationResult(
        daily_energy_demand=daily_energy_demand,
        configured_connection_capacity_kw=configured_connection_capacity_kw,
        installed_charger_capacity_kw=installed_charger_capacity_kw,
        available_site_charging_capacity_kw=available_site_charging_capacity_kw,
        requested_load_profile_kw=requested_load_profile_kw,
        delivered_load_profile_kw=delivered_load_profile_kw,
    )


def _build_full_day_series(
    window_start: time,
    window_values: list[float] | list[int],
) -> list[float] | list[int]:
    series = [0] * TIMESTEPS_PER_DAY
    start_index = time_to_timestep_index(window_start)
    for offset, value in enumerate(window_values):
        series[(start_index + offset) % TIMESTEPS_PER_DAY] = value
    return series


def _build_transformer_regression_series(
    window_start: time,
    window_values: list[float],
    *,
    default_value: float = 0.0,
) -> list[float]:
    """Build a deterministic full-day transformer series for regression tests."""
    series = [default_value] * TIMESTEPS_PER_DAY
    start_index = time_to_timestep_index(window_start)
    for offset, value in enumerate(window_values):
        series[(start_index + offset) % TIMESTEPS_PER_DAY] = value
    return series


def _build_transformer_regression_loading(
    *,
    total_load_kw_by_timestep: list[float],
    loading_percent_by_timestep: list[float],
    overload_kw_by_timestep: list[float],
) -> GridLoadingResult:
    """Build a grid-loading fixture for transformer-focused regression coverage."""
    return GridLoadingResult(
        transformer_loading=TransformerLoadingResult(
            total_load_kw_by_timestep=total_load_kw_by_timestep,
            loading_percent_by_timestep=loading_percent_by_timestep,
            overload_kw_by_timestep=overload_kw_by_timestep,
        ),
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
):
    """Return a compact deterministic scenario for grid-loading KPI regressions."""
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


def _build_reference_power_quality_scenario(
    *,
    vehicles: int = 3,
    charger_count: int = 3,
    charger_power: float = 50.0,
    grid_capacity: float = 150.0,
    charging_window_end: time = time(8, 15),
    charging_strategy: ChargingStrategy = ChargingStrategy.UNCONTROLLED,
    charger_harmonic_factor: float = 1.0,
    single_phase_charger_share_percent: float = 100.0,
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
        single_phase_charger_share_percent=single_phase_charger_share_percent,
        charger_harmonic_factor=charger_harmonic_factor,
    )


def test_metrics_contains_phase_4_outputs():
    assert [field.name for field in fields(Metrics)] == [
        "total_daily_energy",
        "available_capacity",
        "energy_delivery_sufficient",
        "peak_load",
        "capacity_utilization",
        "delivered_energy",
        "unmet_energy",
        "annual_energy",
        "configured_connection_capacity_kw",
        "required_connection_capacity_kw",
        "recommended_connection_capacity_kw",
        "planning_margin_percent",
        "peak_capacity_margin_kw",
        "peak_capacity_margin_percent",
        "connection_capacity_exceeded",
        "maximum_capacity_exceedance_kw",
        "exceeded_timestep_count",
        "capacity_exceedance_duration_hours",
        "persistent_capacity_exceedance_indicator",
        "connection_capacity_adequate_indicator",
        "connection_capacity_recommendation_reason",
        "average_transformer_loading_percent",
        "peak_transformer_loading_percent",
        "transformer_overload_indicator",
        "transformer_overload_duration_hours",
        "transformer_maximum_overload_kw",
        "transformer_thermal_risk_level",
        "maximum_feeder_loading_percent",
        "feeder_overload_indicator",
        "overloaded_feeder_count",
        "highest_feeder_thermal_risk_level",
        "most_loaded_feeder_id",
        "peak_feeder_loading_spread_percentage_points",
        "feeder_loading_distribution_label",
        "feeder_status_message",
        "show_feeder_detail_indicator",
        "peak_harmonic_risk_score",
        "average_harmonic_risk_score",
        "harmonic_risk_duration_hours",
        "harmonic_risk_level",
        "harmonic_warning_indicator",
        "peak_current_imbalance_percent",
        "average_current_imbalance_percent",
        "imbalance_duration_hours",
        "current_imbalance_risk_level",
        "imbalance_warning_indicator",
        "overall_pq_risk_score",
        "overall_pq_risk_level",
        "overall_pq_warning_indicator",
        "power_quality_warning_count",
        "power_quality_message",
        "average_charger_utilization_percent",
        "peak_charger_utilization_percent",
        "average_occupied_charger_count",
        "peak_occupied_charger_count",
        "charger_shortage_indicator",
        "queue_present_indicator",
        "maximum_queue_length",
        "average_queue_length",
        "queue_duration_hours",
        "average_waiting_time_hours",
        "maximum_waiting_time_hours",
        "charger_service_waiting_tolerance_hours",
        "vehicles_waiting_count",
        "vehicles_not_started_count",
        "vehicles_with_unmet_energy_count",
        "charger_capacity_vs_demand_balance",
        "required_charger_count",
        "additional_chargers_required",
        "charger_count_sufficient_indicator",
        "primary_constraint_reason",
        "feeder_summary_rows",
        "transformer_total_load_kw_by_timestep",
        "transformer_loading_percent_by_timestep",
        "transformer_overload_kw_by_timestep",
        "occupied_charger_count_by_timestep",
        "waiting_vehicle_count_by_timestep",
        "harmonic_risk_score_by_timestep",
        "current_imbalance_percent_by_timestep",
        "overall_pq_risk_score_by_timestep",
        "phase_a_load_kw_by_timestep",
        "phase_b_load_kw_by_timestep",
        "phase_c_load_kw_by_timestep",
    ]


def test_calculate_metrics_uses_simulation_result_values():
    simulation_result = simulate(default_scenario)

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.total_daily_energy == simulation_result.daily_energy_demand
    assert metrics.available_capacity == simulation_result.available_site_capacity
    assert metrics.delivered_energy == simulation_result.delivered_energy
    assert metrics.unmet_energy == simulation_result.unmet_energy
    assert metrics.charger_service_waiting_tolerance_hours == pytest.approx(2.0)
    assert (
        metrics.configured_connection_capacity_kw
        == simulation_result.configured_connection_capacity_kw
    )


def test_service_rule_is_met_uses_prepared_planning_outputs_only():
    assert service_rule_is_met(
        Metrics(
            total_daily_energy=100.0,
            available_capacity=50.0,
            energy_delivery_sufficient=True,
            queue_present_indicator=False,
            vehicles_not_started_count=0,
            vehicles_with_unmet_energy_count=0,
        )
    )
    assert service_rule_is_met(
        Metrics(
            total_daily_energy=100.0,
            available_capacity=50.0,
            energy_delivery_sufficient=True,
            queue_present_indicator=True,
            vehicles_not_started_count=0,
            vehicles_with_unmet_energy_count=0,
        )
    )
    assert not service_rule_is_met(
        Metrics(
            total_daily_energy=100.0,
            available_capacity=50.0,
            energy_delivery_sufficient=True,
            queue_present_indicator=True,
            maximum_waiting_time_hours=0.75,
            charger_service_waiting_tolerance_hours=0.5,
            vehicles_not_started_count=0,
            vehicles_with_unmet_energy_count=0,
        )
    )
    assert service_rule_is_met(
        Metrics(
            total_daily_energy=100.0,
            available_capacity=50.0,
            energy_delivery_sufficient=True,
            queue_present_indicator=True,
            maximum_waiting_time_hours=0.75,
            charger_service_waiting_tolerance_hours=1.0,
            vehicles_not_started_count=0,
            vehicles_with_unmet_energy_count=0,
        )
    )


def test_planning_summary_helpers_prepare_shift_and_no_change_messages():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        vehicles_with_unmet_energy_count=2,
        additional_chargers_required=2,
        primary_constraint_reason="charger_availability",
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        vehicles_with_unmet_energy_count=2,
        additional_chargers_required=2,
        primary_constraint_reason="grid_connection_capacity",
    )
    feasible_uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        required_charger_count=4,
        additional_chargers_required=0,
        primary_constraint_reason="none",
    )
    feasible_smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        required_charger_count=4,
        additional_chargers_required=0,
        primary_constraint_reason="none",
    )

    assert format_primary_constraint_reason_label("charger_availability") == (
        "Charger availability"
    )
    assert primary_constraint_shift_summary(uncontrolled, smart) == (
        "Primary modeled bottleneck shifts from Charger availability to "
        "Grid connection capacity."
    )
    assert infrastructure_impact_summary(
        feasible_uncontrolled,
        feasible_smart,
        connection_capacity_avoided_by_smart_kw=0.0,
    ) == (
        "Both strategies satisfy the modeled service rule and lead to the "
        "same infrastructure recommendation."
    )


def test_calculate_metrics_exposes_current_power_quality_contract():
    simulation_result = simulate(default_scenario)

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.harmonic_risk_score_by_timestep == (
        simulation_result.power_quality.harmonic_risk_score_by_timestep
    )
    assert metrics.current_imbalance_percent_by_timestep == (
        simulation_result.power_quality.current_imbalance_percent_by_timestep
    )
    assert metrics.overall_pq_risk_score_by_timestep == (
        build_overall_pq_risk_score_series(
            simulation_result.power_quality.harmonic_risk_score_by_timestep,
            simulation_result.power_quality.current_imbalance_percent_by_timestep,
        )
    )
    assert metrics.phase_a_load_kw_by_timestep == (
        simulation_result.power_quality.phase_a_load_kw_by_timestep
    )
    assert metrics.phase_b_load_kw_by_timestep == (
        simulation_result.power_quality.phase_b_load_kw_by_timestep
    )
    assert metrics.phase_c_load_kw_by_timestep == (
        simulation_result.power_quality.phase_c_load_kw_by_timestep
    )
    assert metrics.peak_harmonic_risk_score == max(
        metrics.harmonic_risk_score_by_timestep,
        default=0.0,
    )
    assert metrics.average_harmonic_risk_score == pytest.approx(
        sum(metrics.harmonic_risk_score_by_timestep) / TIMESTEPS_PER_DAY
    )
    assert metrics.harmonic_risk_duration_hours == calculate_threshold_duration_hours(
        metrics.harmonic_risk_score_by_timestep,
        threshold=35.0,
    )
    assert metrics.peak_current_imbalance_percent == max(
        metrics.current_imbalance_percent_by_timestep,
        default=0.0,
    )
    assert metrics.average_current_imbalance_percent == pytest.approx(
        sum(metrics.current_imbalance_percent_by_timestep) / TIMESTEPS_PER_DAY
    )
    assert metrics.imbalance_duration_hours == calculate_threshold_duration_hours(
        metrics.current_imbalance_percent_by_timestep,
        threshold=25.0,
    )
    assert metrics.harmonic_risk_level == POWER_QUALITY_RISK_LOW
    assert metrics.current_imbalance_risk_level == POWER_QUALITY_RISK_LOW
    assert metrics.overall_pq_risk_level == POWER_QUALITY_RISK_LOW
    assert metrics.harmonic_warning_indicator is False
    assert metrics.imbalance_warning_indicator is False
    assert metrics.overall_pq_warning_indicator is False
    assert metrics.power_quality_warning_count == 0
    assert metrics.power_quality_message == (
        "Modeled overall PQ risk is low because harmonic risk and current "
        "imbalance remain below warning thresholds."
    )


def test_connection_upgrade_prepared_metrics_use_recommended_capacity():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        configured_connection_capacity_kw=700.0,
        required_connection_capacity_kw=800.0,
        recommended_connection_capacity_kw=880.0,
        required_charger_count=4,
        additional_chargers_required=0,
        primary_constraint_reason="grid_connection_capacity",
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        configured_connection_capacity_kw=700.0,
        required_connection_capacity_kw=650.0,
        recommended_connection_capacity_kw=700.0,
        required_charger_count=4,
        additional_chargers_required=0,
        primary_constraint_reason="none",
    )

    assert connection_upgrade_required(uncontrolled) is True
    assert connection_upgrade_required(smart) is False
    assert connection_upgrade_avoided_by_smart(uncontrolled, smart) is True
    assert infrastructure_recommendation_changed_by_smart(
        uncontrolled,
        smart,
    ) is True
    assert infrastructure_impact_summary(
        uncontrolled,
        smart,
        connection_capacity_avoided_by_smart_kw=150.0,
        recommended_connection_capacity_avoided_by_smart_kw=180.0,
        connection_upgrade_avoided_by_smart=True,
        infrastructure_recommendation_changed_by_smart=True,
    ) == (
        "Smart Charging avoids the modeled connection-capacity upgrade "
        "recommendation for this scenario."
    )


def test_service_rule_worsened_by_smart_detects_introduced_service_failure():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        queue_present_indicator=False,
        vehicles_not_started_count=0,
        vehicles_with_unmet_energy_count=0,
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        queue_present_indicator=True,
        vehicles_not_started_count=0,
        vehicles_with_unmet_energy_count=1,
    )

    assert service_rule_worsened_by_smart(uncontrolled, smart) is True
    assert service_impact_summary(uncontrolled, smart) == (
        "Service-rule violation introduced."
    )


def test_service_impact_summary_can_report_operational_tradeoff_without_rule_change():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        queue_present_indicator=True,
        maximum_queue_length=4,
        queue_duration_hours=2.0,
        average_waiting_time_hours=1.0,
        vehicles_waiting_count=4,
        vehicles_not_started_count=0,
        vehicles_with_unmet_energy_count=1,
        unmet_energy=25.0,
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        queue_present_indicator=False,
        maximum_queue_length=1,
        queue_duration_hours=0.5,
        average_waiting_time_hours=0.25,
        vehicles_waiting_count=1,
        vehicles_not_started_count=1,
        vehicles_with_unmet_energy_count=1,
        unmet_energy=25.0,
    )

    assert service_rule_is_met(uncontrolled) is False
    assert service_rule_is_met(smart) is False
    assert service_impact_summary(uncontrolled, smart) == (
        "Service trade-off changed."
    )


def test_service_impact_summary_treats_average_waiting_gain_and_maximum_waiting_penalty_as_tradeoff():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        queue_present_indicator=True,
        maximum_queue_length=4,
        queue_duration_hours=2.0,
        average_waiting_time_hours=3.1,
        maximum_waiting_time_hours=6.5,
        vehicles_waiting_count=40,
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        queue_present_indicator=True,
        maximum_queue_length=4,
        queue_duration_hours=2.0,
        average_waiting_time_hours=2.95,
        maximum_waiting_time_hours=6.75,
        vehicles_waiting_count=40,
    )

    assert service_impact_summary(uncontrolled, smart) == (
        "Service trade-off changed."
    )


def test_infrastructure_impact_summary_can_show_smaller_upgrade_recommendation():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        configured_connection_capacity_kw=700.0,
        required_connection_capacity_kw=800.0,
        recommended_connection_capacity_kw=880.0,
        required_charger_count=4,
        additional_chargers_required=0,
        primary_constraint_reason="grid_connection_capacity",
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        configured_connection_capacity_kw=700.0,
        required_connection_capacity_kw=700.0,
        recommended_connection_capacity_kw=770.0,
        required_charger_count=4,
        additional_chargers_required=0,
        primary_constraint_reason="grid_connection_capacity",
    )

    assert connection_upgrade_required(uncontrolled) is True
    assert connection_upgrade_required(smart) is True
    assert connection_upgrade_avoided_by_smart(uncontrolled, smart) is False
    assert infrastructure_recommendation_changed_by_smart(
        uncontrolled,
        smart,
    ) is True
    assert infrastructure_impact_summary(
        uncontrolled,
        smart,
        connection_capacity_avoided_by_smart_kw=100.0,
        recommended_connection_capacity_avoided_by_smart_kw=110.0,
        connection_upgrade_avoided_by_smart=False,
        infrastructure_recommendation_changed_by_smart=True,
    ) == (
        "Smart Charging reduces the modeled connection-capacity upgrade "
        "recommendation but does not eliminate it."
    )


def test_classify_power_quality_risk_maps_high_raw_score_to_high():
    assert classify_power_quality_risk(
        [70.0],
        moderate_threshold=35.0,
        high_threshold=70.0,
    ) == POWER_QUALITY_RISK_HIGH


def test_classify_power_quality_risk_maps_moderate_duration_to_moderate():
    assert classify_power_quality_risk(
        [35.0, 35.0, 35.0, 35.0],
        moderate_threshold=35.0,
        high_threshold=70.0,
    ) == POWER_QUALITY_RISK_MODERATE


def test_classify_power_quality_risk_maps_zero_series_to_low():
    assert classify_power_quality_risk(
        [0.0] * TIMESTEPS_PER_DAY,
        moderate_threshold=35.0,
        high_threshold=70.0,
    ) == POWER_QUALITY_RISK_LOW


def test_calculate_metrics_derives_power_quality_risk_levels_and_durations():
    harmonic_series = [0.0] * TIMESTEPS_PER_DAY
    current_imbalance_series = [0.0] * TIMESTEPS_PER_DAY
    for timestep_index in range(4):
        harmonic_series[timestep_index] = 40.0
        current_imbalance_series[timestep_index] = 30.0

    simulation_result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[100.0] * TIMESTEPS_PER_DAY,
        delivered_load_profile_kw=[100.0] * TIMESTEPS_PER_DAY,
        power_quality=PowerQualityResult(
            harmonic_risk_score_by_timestep=harmonic_series,
            current_imbalance_percent_by_timestep=current_imbalance_series,
            phase_a_load_kw_by_timestep=[100.0] * TIMESTEPS_PER_DAY,
            phase_b_load_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
            phase_c_load_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
        ),
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.harmonic_risk_duration_hours == 1.0
    assert metrics.imbalance_duration_hours == 1.0
    assert metrics.harmonic_risk_level == POWER_QUALITY_RISK_MODERATE
    assert metrics.current_imbalance_risk_level == POWER_QUALITY_RISK_MODERATE
    assert metrics.harmonic_warning_indicator is True
    assert metrics.imbalance_warning_indicator is True
    assert metrics.overall_pq_warning_indicator is True
    assert metrics.power_quality_warning_count == 3


def test_calculate_metrics_maps_high_power_quality_scores_to_high_risk():
    harmonic_series = [80.0] + ([0.0] * (TIMESTEPS_PER_DAY - 1))
    current_imbalance_series = [0.0] * TIMESTEPS_PER_DAY

    simulation_result = SimulationResult(
        daily_energy_demand=25.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[25.0] * TIMESTEPS_PER_DAY,
        delivered_load_profile_kw=[25.0] * TIMESTEPS_PER_DAY,
        power_quality=PowerQualityResult(
            harmonic_risk_score_by_timestep=harmonic_series,
            current_imbalance_percent_by_timestep=current_imbalance_series,
            phase_a_load_kw_by_timestep=[25.0] * TIMESTEPS_PER_DAY,
            phase_b_load_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
            phase_c_load_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
        ),
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.peak_harmonic_risk_score == 80.0
    assert metrics.harmonic_risk_level == POWER_QUALITY_RISK_HIGH
    assert metrics.overall_pq_risk_level == POWER_QUALITY_RISK_HIGH
    assert metrics.overall_pq_warning_indicator is True
    assert metrics.harmonic_warning_indicator is True
    assert metrics.power_quality_message == (
        "Modeled overall PQ risk is high because harmonic risk is high and "
        "dominates the weighted PQ score."
    )


def test_power_quality_warning_count_only_includes_triggered_warnings():
    harmonic_series = [40.0] * 4 + ([0.0] * (TIMESTEPS_PER_DAY - 4))
    current_imbalance_series = [0.0] * TIMESTEPS_PER_DAY

    metrics = calculate_metrics(
        SimulationResult(
            daily_energy_demand=25.0,
            configured_connection_capacity_kw=100.0,
            installed_charger_capacity_kw=100.0,
            available_site_charging_capacity_kw=100.0,
            requested_load_profile_kw=[25.0] * TIMESTEPS_PER_DAY,
            delivered_load_profile_kw=[25.0] * TIMESTEPS_PER_DAY,
            power_quality=PowerQualityResult(
                harmonic_risk_score_by_timestep=harmonic_series,
                current_imbalance_percent_by_timestep=current_imbalance_series,
                phase_a_load_kw_by_timestep=[25.0] * TIMESTEPS_PER_DAY,
                phase_b_load_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                phase_c_load_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
            ),
        ),
        default_scenario,
    )

    assert metrics.harmonic_warning_indicator is True
    assert metrics.imbalance_warning_indicator is False
    assert metrics.overall_pq_warning_indicator is True
    assert metrics.power_quality_warning_count == 2


def test_power_quality_message_is_deterministic_for_repeated_runs():
    harmonic_series = [40.0] * 4 + ([0.0] * (TIMESTEPS_PER_DAY - 4))
    current_imbalance_series = [0.0] * TIMESTEPS_PER_DAY
    simulation_result = SimulationResult(
        daily_energy_demand=25.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[25.0] * TIMESTEPS_PER_DAY,
        delivered_load_profile_kw=[25.0] * TIMESTEPS_PER_DAY,
        power_quality=PowerQualityResult(
            harmonic_risk_score_by_timestep=harmonic_series,
            current_imbalance_percent_by_timestep=current_imbalance_series,
            phase_a_load_kw_by_timestep=[25.0] * TIMESTEPS_PER_DAY,
            phase_b_load_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
            phase_c_load_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
        ),
    )

    first_metrics = calculate_metrics(simulation_result, default_scenario)
    second_metrics = calculate_metrics(simulation_result, default_scenario)

    assert first_metrics.power_quality_message == second_metrics.power_quality_message
    assert first_metrics.power_quality_message == (
        "Modeled overall PQ risk is moderate because harmonic risk is "
        "moderate and dominates the weighted PQ score."
    )


def test_calculate_metrics_power_quality_regression_reference_cases():
    balanced_metrics = calculate_metrics(
        simulate(_build_reference_power_quality_scenario()),
        _build_reference_power_quality_scenario(),
    )
    unbalanced_scenario = replace(
        _build_reference_power_quality_scenario(),
        power_quality_phase_allocation_method=(
            PowerQualityPhaseAllocationMethod.FRONT_LOADED_PHASE_A
        ),
    )
    unbalanced_metrics = calculate_metrics(
        simulate(unbalanced_scenario),
        unbalanced_scenario,
    )
    high_harmonic_scenario = replace(
        _build_reference_power_quality_scenario(
            vehicles=2,
            charger_count=2,
            charger_power=100.0,
            grid_capacity=200.0,
            charging_window_end=time(9, 0),
            charger_harmonic_factor=2.0,
        ),
        power_quality_phase_allocation_method=(
            PowerQualityPhaseAllocationMethod.FRONT_LOADED_PHASE_A
        ),
    )
    high_harmonic_metrics = calculate_metrics(
        simulate(high_harmonic_scenario),
        high_harmonic_scenario,
    )

    assert balanced_metrics.peak_harmonic_risk_score == 61.25
    assert balanced_metrics.average_harmonic_risk_score == pytest.approx(
        0.6380208333333334
    )
    assert balanced_metrics.harmonic_risk_duration_hours == 0.25
    assert balanced_metrics.harmonic_risk_level == POWER_QUALITY_RISK_MODERATE
    assert balanced_metrics.peak_current_imbalance_percent == 0.0
    assert balanced_metrics.overall_pq_risk_score == 36.75
    assert balanced_metrics.overall_pq_risk_level == POWER_QUALITY_RISK_MODERATE
    assert balanced_metrics.power_quality_warning_count == 2

    assert unbalanced_metrics.peak_harmonic_risk_score == 87.5
    assert unbalanced_metrics.average_harmonic_risk_score == pytest.approx(
        0.9114583333333334
    )
    assert unbalanced_metrics.peak_current_imbalance_percent == 200.0
    assert unbalanced_metrics.average_current_imbalance_percent == pytest.approx(
        2.0833333333333335
    )
    assert unbalanced_metrics.overall_pq_risk_score == 92.5
    assert unbalanced_metrics.overall_pq_risk_level == POWER_QUALITY_RISK_HIGH
    assert unbalanced_metrics.power_quality_warning_count == 3

    assert high_harmonic_metrics.peak_harmonic_risk_score == 100.0
    assert high_harmonic_metrics.average_harmonic_risk_score == pytest.approx(
        1.0416666666666667
    )
    assert high_harmonic_metrics.peak_current_imbalance_percent == 200.0
    assert high_harmonic_metrics.overall_pq_risk_score == 100.0
    assert high_harmonic_metrics.overall_pq_risk_level == POWER_QUALITY_RISK_HIGH
    assert high_harmonic_metrics.power_quality_message == (
        "Modeled overall PQ risk is high because harmonic risk is high and "
        "dominates the weighted PQ score."
    )


def test_calculate_metrics_power_quality_regression_smart_charging_tradeoff_case():
    base_scenario = replace(
        _build_reference_power_quality_scenario(
            vehicles=2,
            charger_count=2,
            charger_power=100.0,
            grid_capacity=200.0,
            charging_window_end=time(9, 0),
            charger_harmonic_factor=1.2,
        ),
        power_quality_phase_allocation_method=(
            PowerQualityPhaseAllocationMethod.FRONT_LOADED_PHASE_A
        ),
    )

    uncontrolled_metrics = calculate_metrics(
        simulate(replace(base_scenario, charging_strategy=ChargingStrategy.UNCONTROLLED)),
        replace(base_scenario, charging_strategy=ChargingStrategy.UNCONTROLLED),
    )
    smart_metrics = calculate_metrics(
        simulate(replace(base_scenario, charging_strategy=ChargingStrategy.SMART)),
        replace(base_scenario, charging_strategy=ChargingStrategy.SMART),
    )

    assert uncontrolled_metrics.peak_harmonic_risk_score == 90.0
    assert uncontrolled_metrics.average_harmonic_risk_score == pytest.approx(0.9375)
    assert uncontrolled_metrics.peak_current_imbalance_percent == 200.0
    assert uncontrolled_metrics.overall_pq_risk_score == 94.0
    assert uncontrolled_metrics.power_quality_warning_count == 3

    assert smart_metrics.peak_harmonic_risk_score == 22.5
    assert smart_metrics.average_harmonic_risk_score == pytest.approx(0.9375)
    assert smart_metrics.harmonic_risk_level == POWER_QUALITY_RISK_LOW
    assert smart_metrics.peak_current_imbalance_percent == 200.0
    assert smart_metrics.average_current_imbalance_percent == pytest.approx(
        8.333333333333334
    )
    assert smart_metrics.imbalance_duration_hours == 1.0
    assert smart_metrics.current_imbalance_risk_level == POWER_QUALITY_RISK_HIGH
    assert smart_metrics.overall_pq_risk_score == 53.5
    assert smart_metrics.overall_pq_risk_level == POWER_QUALITY_RISK_HIGH
    assert smart_metrics.power_quality_warning_count == 2
    assert smart_metrics.power_quality_message == (
        "Modeled overall PQ risk is high because current imbalance is high and "
        "dominates the weighted PQ score."
    )


def test_calculate_metrics_ignores_grid_loading_contract_when_computing_current_kpis():
    simulation_result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[100.0, 0.0],
        delivered_load_profile_kw=[100.0, 0.0],
        grid_loading=GridLoadingResult(
            transformer_loading=TransformerLoadingResult(
                total_load_kw_by_timestep=[125.0, 25.0],
                loading_percent_by_timestep=[83.3, 16.7],
                overload_kw_by_timestep=[0.0, 0.0],
            ),
            feeder_loading_results=[
                FeederLoadingResult(
                    feeder_id="feeder-1",
                    charger_count=1,
                    total_load_kw_by_timestep=[125.0, 25.0],
                    loading_percent_by_timestep=[83.3, 16.7],
                    overload_kw_by_timestep=[0.0, 0.0],
                )
            ],
        ),
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.total_daily_energy == 100.0
    assert metrics.available_capacity == 100.0
    assert metrics.peak_load == 100.0
    assert metrics.delivered_energy == 25.0
    assert metrics.unmet_energy == 75.0
    assert metrics.average_transformer_loading_percent == 0.0
    assert metrics.peak_transformer_loading_percent == 0.0
    assert metrics.transformer_overload_indicator is False
    assert metrics.transformer_overload_duration_hours == 0.0
    assert metrics.transformer_maximum_overload_kw == 0.0
    assert metrics.transformer_thermal_risk_level == THERMAL_RISK_LOW
    assert metrics.maximum_feeder_loading_percent == 83.3
    assert metrics.feeder_overload_indicator is False
    assert metrics.overloaded_feeder_count == 0
    assert metrics.highest_feeder_thermal_risk_level == THERMAL_RISK_LOW
    assert metrics.feeder_summary_rows == [
        FeederSummaryMetrics(
            feeder_id="feeder-1",
            charger_count=1,
            peak_loading_percent=83.3,
            overload_indicator=False,
            overload_duration_hours=0.0,
            maximum_overload_kw=0.0,
            thermal_risk_level=THERMAL_RISK_LOW,
        )
    ]
    assert metrics.transformer_total_load_kw_by_timestep == []
    assert metrics.transformer_loading_percent_by_timestep == []
    assert metrics.transformer_overload_kw_by_timestep == []


@pytest.mark.parametrize(
    "grid_loading",
    [
        _build_transformer_regression_loading(
            total_load_kw_by_timestep=_build_transformer_regression_series(
                time(8, 0),
                [120.0],
                default_value=20.0,
            ),
            loading_percent_by_timestep=_build_transformer_regression_series(
                time(8, 0),
                [80.0],
                default_value=(20.0 / 150.0) * 100.0,
            ),
            overload_kw_by_timestep=_build_transformer_regression_series(
                time(8, 0),
                [0.0],
            ),
        ),
        _build_transformer_regression_loading(
            total_load_kw_by_timestep=_build_transformer_regression_series(
                time(8, 0),
                [120.0],
                default_value=20.0,
            ),
            loading_percent_by_timestep=_build_transformer_regression_series(
                time(8, 0),
                [100.0],
                default_value=(20.0 / 120.0) * 100.0,
            ),
            overload_kw_by_timestep=_build_transformer_regression_series(
                time(8, 0),
                [0.0],
            ),
        ),
        _build_transformer_regression_loading(
            total_load_kw_by_timestep=_build_transformer_regression_series(
                time(8, 0),
                [120.0],
                default_value=20.0,
            ),
            loading_percent_by_timestep=_build_transformer_regression_series(
                time(8, 0),
                [120.0],
                default_value=20.0,
            ),
            overload_kw_by_timestep=_build_transformer_regression_series(
                time(8, 0),
                [20.0],
            ),
        ),
        _build_transformer_regression_loading(
            total_load_kw_by_timestep=[90.0] * TIMESTEPS_PER_DAY,
            loading_percent_by_timestep=[112.5] * TIMESTEPS_PER_DAY,
            overload_kw_by_timestep=[10.0] * TIMESTEPS_PER_DAY,
        ),
    ],
)
def test_calculate_metrics_preserves_current_kpis_across_transformer_regression_fixtures(
    grid_loading: GridLoadingResult,
):
    simulation_result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[100.0, 0.0],
        delivered_load_profile_kw=[100.0, 0.0],
        grid_loading=grid_loading,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.total_daily_energy == 100.0
    assert metrics.available_capacity == 100.0
    assert metrics.peak_load == 100.0
    assert metrics.delivered_energy == 25.0
    assert metrics.unmet_energy == 75.0


@pytest.mark.parametrize(
    (
        "grid_loading",
        "expected_average_loading_percent",
        "expected_peak_loading_percent",
        "expected_overload_indicator",
        "expected_overload_duration_hours",
        "expected_maximum_overload_kw",
        "expected_transformer_thermal_risk_level",
    ),
    [
        (
            _build_transformer_regression_loading(
                total_load_kw_by_timestep=[96.0] * TIMESTEPS_PER_DAY,
                loading_percent_by_timestep=[80.0] * TIMESTEPS_PER_DAY,
                overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
            ),
            80.0,
            80.0,
            False,
            0.0,
            0.0,
            THERMAL_RISK_LOW,
        ),
        (
            _build_transformer_regression_loading(
                total_load_kw_by_timestep=[120.0] * TIMESTEPS_PER_DAY,
                loading_percent_by_timestep=[100.0] * TIMESTEPS_PER_DAY,
                overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
            ),
            100.0,
            100.0,
            False,
            0.0,
            0.0,
            THERMAL_RISK_HIGH,
        ),
        (
            _build_transformer_regression_loading(
                total_load_kw_by_timestep=[135.0] * TIMESTEPS_PER_DAY,
                loading_percent_by_timestep=[112.5] * TIMESTEPS_PER_DAY,
                overload_kw_by_timestep=[15.0] * TIMESTEPS_PER_DAY,
            ),
            112.5,
            112.5,
            True,
            24.0,
            15.0,
            THERMAL_RISK_HIGH,
        ),
        (
            _build_transformer_regression_loading(
                total_load_kw_by_timestep=[60.0] * TIMESTEPS_PER_DAY,
                loading_percent_by_timestep=[50.0] * TIMESTEPS_PER_DAY,
                overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
            ),
            50.0,
            50.0,
            False,
            0.0,
            0.0,
            THERMAL_RISK_LOW,
        ),
    ],
)
def test_calculate_metrics_exposes_transformer_loading_kpis_from_raw_series(
    grid_loading: GridLoadingResult,
    expected_average_loading_percent: float,
    expected_peak_loading_percent: float,
    expected_overload_indicator: bool,
    expected_overload_duration_hours: float,
    expected_maximum_overload_kw: float,
    expected_transformer_thermal_risk_level: str,
):
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = SimulationResult(
        daily_energy_demand=0.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=50.0,
        available_site_charging_capacity_kw=50.0,
        requested_load_profile_kw=[0.0] * TIMESTEPS_PER_DAY,
        delivered_load_profile_kw=[0.0] * TIMESTEPS_PER_DAY,
        grid_loading=grid_loading,
    )

    metrics = calculate_metrics(simulation_result, scenario)

    assert metrics.average_transformer_loading_percent == pytest.approx(
        expected_average_loading_percent
    )
    assert metrics.peak_transformer_loading_percent == pytest.approx(
        expected_peak_loading_percent
    )
    assert metrics.transformer_overload_indicator is expected_overload_indicator
    assert metrics.transformer_overload_duration_hours == pytest.approx(
        expected_overload_duration_hours
    )
    assert metrics.transformer_maximum_overload_kw == pytest.approx(
        expected_maximum_overload_kw
    )
    assert (
        metrics.transformer_thermal_risk_level
        == expected_transformer_thermal_risk_level
    )
    assert metrics.transformer_total_load_kw_by_timestep == (
        grid_loading.transformer_loading.total_load_kw_by_timestep
    )
    assert metrics.transformer_loading_percent_by_timestep == (
        grid_loading.transformer_loading.loading_percent_by_timestep
    )
    assert metrics.transformer_overload_kw_by_timestep == (
        grid_loading.transformer_loading.overload_kw_by_timestep
    )


@pytest.mark.parametrize(
    (
        "loading_percent_by_timestep",
        "overload_kw_by_timestep",
        "expected_risk_level",
    ),
    [
        ([89.75] * 4, [0.0] * 4, THERMAL_RISK_LOW),
        ([90.0] * 4, [0.0] * 4, THERMAL_RISK_MODERATE),
        ([95.0] * 8, [0.0] * 8, THERMAL_RISK_HIGH),
        ([105.0], [5.0], THERMAL_RISK_MODERATE),
        ([101.0] * 4, [1.0] * 4, THERMAL_RISK_HIGH),
    ],
)
def test_classify_thermal_risk_applies_threshold_boundary_rules(
    loading_percent_by_timestep: list[float],
    overload_kw_by_timestep: list[float],
    expected_risk_level: str,
):
    assert (
        classify_thermal_risk(
            loading_percent_by_timestep,
            overload_kw_by_timestep,
        )
        == expected_risk_level
    )


def test_classify_thermal_risk_distinguishes_short_overload_from_sustained_high_loading():
    short_overload_risk = classify_thermal_risk(
        [105.0],
        [5.0],
    )
    sustained_high_loading_risk = classify_thermal_risk(
        [95.0] * 8,
        [0.0] * 8,
    )

    assert short_overload_risk == THERMAL_RISK_MODERATE
    assert sustained_high_loading_risk == THERMAL_RISK_HIGH


def test_thermal_risk_helpers_are_deterministic_across_repeated_calls():
    loading_percent_by_timestep = [95.0] * 8 + [80.0] * 4
    overload_kw_by_timestep = [0.0] * 12

    first_risk_level = classify_thermal_risk(
        loading_percent_by_timestep,
        overload_kw_by_timestep,
    )
    second_risk_level = classify_thermal_risk(
        loading_percent_by_timestep,
        overload_kw_by_timestep,
    )

    assert first_risk_level == second_risk_level == THERMAL_RISK_HIGH
    assert highest_thermal_risk_level(
        [THERMAL_RISK_LOW, first_risk_level]
    ) == THERMAL_RISK_HIGH


@pytest.mark.parametrize(
    (
        "feeder_loading_results",
        "expected_maximum_feeder_loading_percent",
        "expected_feeder_overload_indicator",
        "expected_overloaded_feeder_count",
        "expected_summary_rows",
    ),
    [
        (
            [
                FeederLoadingResult(
                    feeder_id="feeder-1",
                    charger_count=2,
                    total_load_kw_by_timestep=[70.0] * TIMESTEPS_PER_DAY,
                    loading_percent_by_timestep=[70.0] * TIMESTEPS_PER_DAY,
                    overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                ),
                FeederLoadingResult(
                    feeder_id="feeder-2",
                    charger_count=1,
                    total_load_kw_by_timestep=[90.0] * TIMESTEPS_PER_DAY,
                    loading_percent_by_timestep=[110.0] + [90.0] * (TIMESTEPS_PER_DAY - 1),
                    overload_kw_by_timestep=[10.0] + [0.0] * (TIMESTEPS_PER_DAY - 1),
                ),
            ],
            110.0,
            True,
            1,
            [
                FeederSummaryMetrics(
                    feeder_id="feeder-1",
                    charger_count=2,
                    peak_loading_percent=70.0,
                    overload_indicator=False,
                    overload_duration_hours=0.0,
                    maximum_overload_kw=0.0,
                    thermal_risk_level=THERMAL_RISK_LOW,
                ),
                FeederSummaryMetrics(
                    feeder_id="feeder-2",
                    charger_count=1,
                    peak_loading_percent=110.0,
                    overload_indicator=True,
                    overload_duration_hours=0.25,
                    maximum_overload_kw=10.0,
                    thermal_risk_level=THERMAL_RISK_MODERATE,
                ),
            ],
        ),
        (
            [
                FeederLoadingResult(
                    feeder_id="feeder-1",
                    charger_count=2,
                    total_load_kw_by_timestep=[95.0] * TIMESTEPS_PER_DAY,
                    loading_percent_by_timestep=[105.0, 105.0] + [95.0] * (TIMESTEPS_PER_DAY - 2),
                    overload_kw_by_timestep=[5.0, 5.0] + [0.0] * (TIMESTEPS_PER_DAY - 2),
                ),
                FeederLoadingResult(
                    feeder_id="feeder-2",
                    charger_count=2,
                    total_load_kw_by_timestep=[100.0] * TIMESTEPS_PER_DAY,
                    loading_percent_by_timestep=[120.0] + [100.0] * (TIMESTEPS_PER_DAY - 1),
                    overload_kw_by_timestep=[20.0] + [0.0] * (TIMESTEPS_PER_DAY - 1),
                ),
            ],
            120.0,
            True,
            2,
            [
                FeederSummaryMetrics(
                    feeder_id="feeder-1",
                    charger_count=2,
                    peak_loading_percent=105.0,
                    overload_indicator=True,
                    overload_duration_hours=0.5,
                    maximum_overload_kw=5.0,
                    thermal_risk_level=THERMAL_RISK_HIGH,
                ),
                FeederSummaryMetrics(
                    feeder_id="feeder-2",
                    charger_count=2,
                    peak_loading_percent=120.0,
                    overload_indicator=True,
                    overload_duration_hours=0.25,
                    maximum_overload_kw=20.0,
                    thermal_risk_level=THERMAL_RISK_HIGH,
                ),
            ],
        ),
        (
            [
                FeederLoadingResult(
                    feeder_id="feeder-1",
                    charger_count=1,
                    total_load_kw_by_timestep=[60.0] * TIMESTEPS_PER_DAY,
                    loading_percent_by_timestep=[60.0] * TIMESTEPS_PER_DAY,
                    overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                ),
                FeederLoadingResult(
                    feeder_id="feeder-2",
                    charger_count=1,
                    total_load_kw_by_timestep=[75.0] * TIMESTEPS_PER_DAY,
                    loading_percent_by_timestep=[75.0] * TIMESTEPS_PER_DAY,
                    overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                ),
            ],
            75.0,
            False,
            0,
            [
                FeederSummaryMetrics(
                    feeder_id="feeder-1",
                    charger_count=1,
                    peak_loading_percent=60.0,
                    overload_indicator=False,
                    overload_duration_hours=0.0,
                    maximum_overload_kw=0.0,
                    thermal_risk_level=THERMAL_RISK_LOW,
                ),
                FeederSummaryMetrics(
                    feeder_id="feeder-2",
                    charger_count=1,
                    peak_loading_percent=75.0,
                    overload_indicator=False,
                    overload_duration_hours=0.0,
                    maximum_overload_kw=0.0,
                    thermal_risk_level=THERMAL_RISK_LOW,
                ),
            ],
        ),
        (
            [
                FeederLoadingResult(
                    feeder_id="feeder-1",
                    charger_count=4,
                    total_load_kw_by_timestep=[110.0] * TIMESTEPS_PER_DAY,
                    loading_percent_by_timestep=[95.0] * TIMESTEPS_PER_DAY,
                    overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                ),
            ],
            95.0,
            False,
            0,
            [
                FeederSummaryMetrics(
                    feeder_id="feeder-1",
                    charger_count=4,
                    peak_loading_percent=95.0,
                    overload_indicator=False,
                    overload_duration_hours=0.0,
                    maximum_overload_kw=0.0,
                    thermal_risk_level=THERMAL_RISK_HIGH,
                ),
            ],
        ),
    ],
)
def test_calculate_metrics_exposes_feeder_loading_summary_kpis(
    feeder_loading_results: list[FeederLoadingResult],
    expected_maximum_feeder_loading_percent: float,
    expected_feeder_overload_indicator: bool,
    expected_overloaded_feeder_count: int,
    expected_summary_rows: list[FeederSummaryMetrics],
):
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = SimulationResult(
        daily_energy_demand=0.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=50.0,
        available_site_charging_capacity_kw=50.0,
        requested_load_profile_kw=[0.0] * TIMESTEPS_PER_DAY,
        delivered_load_profile_kw=[0.0] * TIMESTEPS_PER_DAY,
        grid_loading=GridLoadingResult(
            transformer_loading=TransformerLoadingResult(
                total_load_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                loading_percent_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
            ),
            feeder_loading_results=feeder_loading_results,
        ),
    )

    metrics = calculate_metrics(simulation_result, scenario)

    assert metrics.maximum_feeder_loading_percent == pytest.approx(
        expected_maximum_feeder_loading_percent
    )
    assert metrics.feeder_overload_indicator is expected_feeder_overload_indicator
    assert metrics.overloaded_feeder_count == expected_overloaded_feeder_count
    assert metrics.highest_feeder_thermal_risk_level == highest_thermal_risk_level(
        [row.thermal_risk_level for row in expected_summary_rows]
    )
    if expected_summary_rows:
        expected_most_loaded_feeder = max(
            expected_summary_rows,
            key=lambda feeder_summary: feeder_summary.peak_loading_percent,
        )
        expected_peak_loading_spread = (
            max(
                feeder_summary.peak_loading_percent
                for feeder_summary in expected_summary_rows
            )
            - min(
                feeder_summary.peak_loading_percent
                for feeder_summary in expected_summary_rows
            )
        )
    else:
        expected_most_loaded_feeder = None
        expected_peak_loading_spread = 0.0

    assert metrics.most_loaded_feeder_id == (
        expected_most_loaded_feeder.feeder_id
        if expected_most_loaded_feeder is not None
        else None
    )
    assert metrics.peak_feeder_loading_spread_percentage_points == pytest.approx(
        expected_peak_loading_spread
    )
    assert metrics.feeder_summary_rows == expected_summary_rows


@pytest.mark.parametrize(
    (
        "feeder_loading_results",
        "expected_distribution_label",
        "expected_status_message",
        "expected_show_detail_indicator",
    ),
    [
        pytest.param(
            [],
            "No feeders modeled",
            "No feeder-level load was modeled.",
            False,
            id="no-feeders",
        ),
        pytest.param(
            [
                FeederLoadingResult(
                    feeder_id="feeder-1",
                    charger_count=2,
                    total_load_kw_by_timestep=[47.7] * TIMESTEPS_PER_DAY,
                    loading_percent_by_timestep=[47.7] * TIMESTEPS_PER_DAY,
                    overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                ),
                FeederLoadingResult(
                    feeder_id="feeder-2",
                    charger_count=2,
                    total_load_kw_by_timestep=[47.7] * TIMESTEPS_PER_DAY,
                    loading_percent_by_timestep=[47.7] * TIMESTEPS_PER_DAY,
                    overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                ),
            ],
            "Balanced",
            "All feeders are evenly loaded. No local feeder bottleneck detected.",
            False,
            id="balanced",
        ),
        pytest.param(
            [
                FeederLoadingResult(
                    feeder_id="feeder-1",
                    charger_count=2,
                    total_load_kw_by_timestep=[60.0] * TIMESTEPS_PER_DAY,
                    loading_percent_by_timestep=[60.0] * TIMESTEPS_PER_DAY,
                    overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                ),
                FeederLoadingResult(
                    feeder_id="feeder-2",
                    charger_count=2,
                    total_load_kw_by_timestep=[75.0] * TIMESTEPS_PER_DAY,
                    loading_percent_by_timestep=[75.0] * TIMESTEPS_PER_DAY,
                    overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                ),
            ],
            "Uneven",
            "Feeder loading is uneven. feeder-2 is the most loaded feeder.",
            True,
            id="uneven",
        ),
        pytest.param(
            [
                FeederLoadingResult(
                    feeder_id="feeder-1",
                    charger_count=2,
                    total_load_kw_by_timestep=[20.0] * TIMESTEPS_PER_DAY,
                    loading_percent_by_timestep=[20.0] * TIMESTEPS_PER_DAY,
                    overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                ),
                FeederLoadingResult(
                    feeder_id="feeder-2",
                    charger_count=2,
                    total_load_kw_by_timestep=[85.0] * TIMESTEPS_PER_DAY,
                    loading_percent_by_timestep=[85.0] * TIMESTEPS_PER_DAY,
                    overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                ),
            ],
            "Concentrated",
            "Feeder loading is concentrated on feeder-2. Review local feeder balance.",
            True,
            id="concentrated",
        ),
        pytest.param(
            [
                FeederLoadingResult(
                    feeder_id="feeder-1",
                    charger_count=2,
                    total_load_kw_by_timestep=[120.0] * TIMESTEPS_PER_DAY,
                    loading_percent_by_timestep=[120.0] * TIMESTEPS_PER_DAY,
                    overload_kw_by_timestep=[20.0] * TIMESTEPS_PER_DAY,
                ),
                FeederLoadingResult(
                    feeder_id="feeder-2",
                    charger_count=2,
                    total_load_kw_by_timestep=[70.0] * TIMESTEPS_PER_DAY,
                    loading_percent_by_timestep=[70.0] * TIMESTEPS_PER_DAY,
                    overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                ),
            ],
            "Concentrated",
            "1 feeder is overloaded. feeder-1 is the most loaded feeder.",
            True,
            id="overloaded",
        ),
        pytest.param(
            [
                FeederLoadingResult(
                    feeder_id="feeder-1",
                    charger_count=2,
                    total_load_kw_by_timestep=[120.0] * TIMESTEPS_PER_DAY,
                    loading_percent_by_timestep=[120.0] * TIMESTEPS_PER_DAY,
                    overload_kw_by_timestep=[20.0] * TIMESTEPS_PER_DAY,
                ),
                FeederLoadingResult(
                    feeder_id="feeder-2",
                    charger_count=2,
                    total_load_kw_by_timestep=[115.0] * TIMESTEPS_PER_DAY,
                    loading_percent_by_timestep=[115.0] * TIMESTEPS_PER_DAY,
                    overload_kw_by_timestep=[15.0] * TIMESTEPS_PER_DAY,
                ),
            ],
            "Balanced",
            "2 feeders are overloaded. feeder-1 is the most loaded feeder.",
            True,
            id="multiple-overloaded-feeders",
        ),
    ],
)
def test_calculate_metrics_exposes_feeder_distribution_status_outputs(
    feeder_loading_results: list[FeederLoadingResult],
    expected_distribution_label: str,
    expected_status_message: str,
    expected_show_detail_indicator: bool,
):
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = SimulationResult(
        daily_energy_demand=0.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=50.0,
        available_site_charging_capacity_kw=50.0,
        requested_load_profile_kw=[0.0] * TIMESTEPS_PER_DAY,
        delivered_load_profile_kw=[0.0] * TIMESTEPS_PER_DAY,
        grid_loading=GridLoadingResult(
            transformer_loading=TransformerLoadingResult(
                total_load_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                loading_percent_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
                overload_kw_by_timestep=[0.0] * TIMESTEPS_PER_DAY,
            ),
            feeder_loading_results=feeder_loading_results,
        ),
    )

    metrics = calculate_metrics(simulation_result, scenario)

    assert metrics.feeder_loading_distribution_label == expected_distribution_label
    assert metrics.feeder_status_message == expected_status_message
    assert metrics.show_feeder_detail_indicator is expected_show_detail_indicator


@pytest.mark.parametrize(
    (
        "scenario",
        "expected_peak_load",
        "expected_average_transformer_loading_percent",
        "expected_peak_transformer_loading_percent",
        "expected_transformer_overload_indicator",
        "expected_transformer_overload_duration_hours",
        "expected_transformer_maximum_overload_kw",
        "expected_transformer_thermal_risk_level",
        "expected_maximum_feeder_loading_percent",
        "expected_feeder_overload_indicator",
        "expected_overloaded_feeder_count",
        "expected_highest_feeder_thermal_risk_level",
        "expected_feeder_summary_rows",
    ),
    [
        pytest.param(
            _build_reference_grid_loading_scenario(),
            100.0,
            (95 * ((20.0 / 150.0) * 100.0) + 80.0) / 96.0,
            80.0,
            False,
            0.0,
            0.0,
            THERMAL_RISK_LOW,
            (110.0 / 140.0) * 100.0,
            False,
            0,
            THERMAL_RISK_LOW,
            [
                FeederSummaryMetrics(
                    feeder_id="feeder-1",
                    charger_count=1,
                    peak_loading_percent=(110.0 / 140.0) * 100.0,
                    overload_indicator=False,
                    overload_duration_hours=0.0,
                    maximum_overload_kw=0.0,
                    thermal_risk_level=THERMAL_RISK_LOW,
                )
            ],
            id="reference-no-overload",
        ),
        pytest.param(
            _build_reference_grid_loading_scenario(
                transformer_capacity_kw=100.0,
            ),
            100.0,
            (95 * 20.0 + 120.0) / 96.0,
            120.0,
            True,
            0.25,
            20.0,
            THERMAL_RISK_MODERATE,
            (110.0 / 140.0) * 100.0,
            False,
            0,
            THERMAL_RISK_LOW,
            [
                FeederSummaryMetrics(
                    feeder_id="feeder-1",
                    charger_count=1,
                    peak_loading_percent=(110.0 / 140.0) * 100.0,
                    overload_indicator=False,
                    overload_duration_hours=0.0,
                    maximum_overload_kw=0.0,
                    thermal_risk_level=THERMAL_RISK_LOW,
                )
            ],
            id="reference-transformer-only-overload",
        ),
        pytest.param(
            _build_reference_grid_loading_scenario(
                feeder_capacity_kw=100.0,
            ),
            100.0,
            (95 * ((20.0 / 150.0) * 100.0) + 80.0) / 96.0,
            80.0,
            False,
            0.0,
            0.0,
                THERMAL_RISK_LOW,
                (110.0 / 100.0) * 100.0,
                True,
                1,
                THERMAL_RISK_MODERATE,
                [
                    FeederSummaryMetrics(
                        feeder_id="feeder-1",
                        charger_count=1,
                        peak_loading_percent=(110.0 / 100.0) * 100.0,
                        overload_indicator=True,
                        overload_duration_hours=0.25,
                        maximum_overload_kw=10.0,
                    thermal_risk_level=THERMAL_RISK_MODERATE,
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
            0.0,
            112.5,
            112.5,
            True,
            24.0,
            10.0,
            THERMAL_RISK_HIGH,
            0.0,
            False,
            0,
            THERMAL_RISK_LOW,
            [
                FeederSummaryMetrics(
                    feeder_id="feeder-1",
                    charger_count=1,
                    peak_loading_percent=0.0,
                    overload_indicator=False,
                    overload_duration_hours=0.0,
                    maximum_overload_kw=0.0,
                    thermal_risk_level=THERMAL_RISK_LOW,
                )
            ],
            id="reference-base-load-driven-overload",
        ),
    ],
)
def test_reference_loading_scenarios_expose_expected_grid_loading_kpis(
    scenario,
    expected_peak_load,
    expected_average_transformer_loading_percent,
    expected_peak_transformer_loading_percent,
    expected_transformer_overload_indicator,
    expected_transformer_overload_duration_hours,
    expected_transformer_maximum_overload_kw,
    expected_transformer_thermal_risk_level,
    expected_maximum_feeder_loading_percent,
    expected_feeder_overload_indicator,
    expected_overloaded_feeder_count,
    expected_highest_feeder_thermal_risk_level,
    expected_feeder_summary_rows,
):
    metrics = calculate_metrics(simulate(scenario), scenario)

    assert metrics.peak_load == pytest.approx(expected_peak_load)
    assert metrics.average_transformer_loading_percent == pytest.approx(
        expected_average_transformer_loading_percent
    )
    assert metrics.peak_transformer_loading_percent == pytest.approx(
        expected_peak_transformer_loading_percent
    )
    assert (
        metrics.transformer_overload_indicator
        is expected_transformer_overload_indicator
    )
    assert metrics.transformer_overload_duration_hours == pytest.approx(
        expected_transformer_overload_duration_hours
    )
    assert metrics.transformer_maximum_overload_kw == pytest.approx(
        expected_transformer_maximum_overload_kw
    )
    assert (
        metrics.transformer_thermal_risk_level
        == expected_transformer_thermal_risk_level
    )
    assert metrics.maximum_feeder_loading_percent == pytest.approx(
        expected_maximum_feeder_loading_percent
    )
    assert metrics.feeder_overload_indicator is expected_feeder_overload_indicator
    assert metrics.overloaded_feeder_count == expected_overloaded_feeder_count
    assert (
        metrics.highest_feeder_thermal_risk_level
        == expected_highest_feeder_thermal_risk_level
    )
    assert metrics.feeder_summary_rows == expected_feeder_summary_rows


def test_reference_smart_charging_comparison_exposes_expected_grid_loading_kpis():
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
    uncontrolled_metrics = calculate_metrics(uncontrolled_result, scenario)
    smart_metrics = calculate_metrics(smart_result, scenario)
    comparison_metrics = calculate_comparison_metrics(
        uncontrolled_metrics,
        smart_metrics,
    )

    assert uncontrolled_metrics.peak_load == 400.0
    assert smart_metrics.peak_load == 100.0
    assert uncontrolled_metrics.peak_transformer_loading_percent == 168.0
    assert smart_metrics.peak_transformer_loading_percent == 48.0
    assert uncontrolled_metrics.transformer_overload_indicator is True
    assert smart_metrics.transformer_overload_indicator is False
    assert uncontrolled_metrics.transformer_overload_duration_hours == 0.25
    assert smart_metrics.transformer_overload_duration_hours == 0.0
    assert uncontrolled_metrics.transformer_maximum_overload_kw == 170.0
    assert smart_metrics.transformer_maximum_overload_kw == 0.0
    assert (
        uncontrolled_metrics.transformer_thermal_risk_level
        == THERMAL_RISK_MODERATE
    )
    assert smart_metrics.transformer_thermal_risk_level == THERMAL_RISK_LOW
    assert uncontrolled_metrics.maximum_feeder_loading_percent == 175.0
    assert smart_metrics.maximum_feeder_loading_percent == 50.0
    assert uncontrolled_metrics.feeder_overload_indicator is True
    assert smart_metrics.feeder_overload_indicator is False
    assert uncontrolled_metrics.overloaded_feeder_count == 2
    assert smart_metrics.overloaded_feeder_count == 0
    assert (
        uncontrolled_metrics.highest_feeder_thermal_risk_level
        == THERMAL_RISK_MODERATE
    )
    assert smart_metrics.highest_feeder_thermal_risk_level == THERMAL_RISK_LOW
    assert comparison_metrics.peak_reduction == 300.0
    assert comparison_metrics.relative_peak_reduction == 75.0
    assert comparison_metrics.average_transformer_loading_percent_difference == 0.0
    assert comparison_metrics.peak_transformer_loading_percent_difference == 120.0
    assert (
        comparison_metrics.transformer_overload_duration_difference_hours
        == 0.25
    )
    assert comparison_metrics.transformer_maximum_overload_difference_kw == 170.0
    assert comparison_metrics.maximum_feeder_loading_percent_difference == 125.0
    assert comparison_metrics.overloaded_feeder_count_difference == 2


def test_new_queueing_kpis_match_small_deterministic_raw_fixture():
    scenario = create_internal_scenario(
        vehicles=3,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = SimulationResult(
        daily_energy_demand=60.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=_build_full_day_series(time(8, 0), [50.0, 100.0, 50.0, 0.0]),
        delivered_load_profile_kw=_build_full_day_series(time(8, 0), [50.0, 100.0, 50.0, 0.0]),
        charging_requests=[
            ChargingRequestResult(
                request_id="request-0",
                vehicle_index=0,
                arrival_timestep=32,
                departure_timestep=36,
                charging_start_timestep=32,
                charging_completion_timestep=34,
                energy_requested_kwh=20.0,
                energy_delivered_kwh=20.0,
                unmet_energy_kwh=0.0,
                waiting_time_hours=None,
                not_started_within_window=False,
                delayed_start_reason="none",
                unmet_energy_reason="none",
            ),
            ChargingRequestResult(
                request_id="request-1",
                vehicle_index=1,
                arrival_timestep=32,
                departure_timestep=36,
                charging_start_timestep=32,
                charging_completion_timestep=35,
                energy_requested_kwh=30.0,
                energy_delivered_kwh=30.0,
                unmet_energy_kwh=0.0,
                waiting_time_hours=None,
                not_started_within_window=False,
                delayed_start_reason="none",
                unmet_energy_reason="none",
            ),
            ChargingRequestResult(
                request_id="request-2",
                vehicle_index=2,
                arrival_timestep=32,
                departure_timestep=36,
                charging_start_timestep=34,
                charging_completion_timestep=None,
                energy_requested_kwh=20.0,
                energy_delivered_kwh=10.0,
                unmet_energy_kwh=10.0,
                waiting_time_hours=None,
                not_started_within_window=False,
                delayed_start_reason="charger_availability",
                unmet_energy_reason="charging_window",
            ),
        ],
        arrivals_count_by_timestep=_build_full_day_series(time(8, 0), [3, 0, 0, 0]),
        charging_start_count_by_timestep=_build_full_day_series(time(8, 0), [2, 0, 1, 0]),
        charging_completion_count_by_timestep=_build_full_day_series(time(8, 0), [0, 0, 1, 1]),
        requested_charger_slots_by_timestep=_build_full_day_series(time(8, 0), [3, 3, 2, 1]),
        occupied_charger_count_by_timestep=_build_full_day_series(time(8, 0), [2, 2, 2, 1]),
        waiting_vehicle_count_by_timestep=_build_full_day_series(time(8, 0), [1, 1, 0, 0]),
    )

    metrics = calculate_metrics(simulation_result, scenario)

    assert metrics.average_charger_utilization_percent == 50.0
    assert metrics.peak_charger_utilization_percent == 100.0
    assert metrics.average_occupied_charger_count == 1.75
    assert metrics.peak_occupied_charger_count == 2
    assert metrics.charger_shortage_indicator is True
    assert metrics.queue_present_indicator is True
    assert metrics.maximum_queue_length == 1
    assert metrics.average_queue_length == 0.5
    assert metrics.queue_duration_hours == 0.5
    assert metrics.average_waiting_time_hours == pytest.approx(1.0 / 6.0)
    assert metrics.maximum_waiting_time_hours == 0.5
    assert metrics.vehicles_waiting_count == 1
    assert metrics.vehicles_not_started_count == 0
    assert metrics.vehicles_with_unmet_energy_count == 1
    assert metrics.charger_capacity_vs_demand_balance == -1
    assert metrics.required_charger_count == 3
    assert metrics.additional_chargers_required == 1
    assert metrics.charger_count_sufficient_indicator is False
    assert metrics.occupied_charger_count_by_timestep == _build_full_day_series(
        time(8, 0),
        [2, 2, 2, 1],
    )
    assert metrics.waiting_vehicle_count_by_timestep == _build_full_day_series(
        time(8, 0),
        [1, 1, 0, 0],
    )


def test_additional_chargers_required_is_zero_when_current_scenario_already_meets_planning_rule():
    scenario = create_internal_scenario(
        vehicles=3,
        daily_energy_per_vehicle=20.0,
        charger_count=3,
        charger_power=50.0,
        grid_capacity=150.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = simulate(scenario)

    metrics = calculate_metrics(simulation_result, scenario)

    assert metrics.required_charger_count == 3
    assert metrics.additional_chargers_required == 0
    assert metrics.charger_count_sufficient_indicator is True
    assert metrics.charger_capacity_vs_demand_balance == 0


def test_charger_recommendation_respects_waiting_tolerance_for_default_reference_scenario():
    simulation_result = simulate(default_scenario)

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.maximum_waiting_time_hours is not None
    assert metrics.maximum_waiting_time_hours > 0.5
    assert metrics.required_charger_count is not None
    assert metrics.required_charger_count > default_scenario.charger_count
    assert metrics.additional_chargers_required is not None
    assert metrics.additional_chargers_required > 0
    assert metrics.charger_count_sufficient_indicator is False


def test_already_feasible_recommendation_does_not_depend_on_constraint_classification_data():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = simulate(scenario)

    metrics = calculate_metrics(
        simulation_result,
        scenario,
        include_primary_constraint_reason=False,
    )

    assert metrics.primary_constraint_reason == "none"
    assert metrics.required_charger_count == scenario.charger_count
    assert metrics.additional_chargers_required == 0
    assert metrics.charger_count_sufficient_indicator is True


def test_charger_capacity_vs_demand_balance_remains_independent_of_delivered_power_and_site_capacity():
    scenario = create_internal_scenario(
        vehicles=4,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=40.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=40.0,
        installed_charger_capacity_kw=200.0,
        available_site_charging_capacity_kw=40.0,
        requested_load_profile_kw=_build_full_day_series(time(8, 0), [200.0, 200.0, 200.0, 200.0]),
        delivered_load_profile_kw=_build_full_day_series(time(8, 0), [40.0, 40.0, 40.0, 40.0]),
        requested_charger_slots_by_timestep=_build_full_day_series(time(8, 0), [4, 4, 4, 4]),
        waiting_vehicle_count_by_timestep=_build_full_day_series(time(8, 0), [2, 2, 2, 2]),
        occupied_charger_count_by_timestep=_build_full_day_series(time(8, 0), [2, 2, 2, 2]),
    )

    metrics = calculate_metrics(simulation_result, scenario)

    assert metrics.required_charger_count is None
    assert metrics.additional_chargers_required is None
    assert metrics.charger_count_sufficient_indicator is False
    assert metrics.charger_capacity_vs_demand_balance == -2


def test_zero_chargers_with_positive_demand_return_numeric_recommendation_only_for_availability_constraint():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )

    metrics = calculate_metrics(simulate(scenario), scenario)

    assert metrics.primary_constraint_reason == "charger_availability"
    assert metrics.required_charger_count == 1
    assert metrics.additional_chargers_required == 1
    assert metrics.charger_count_sufficient_indicator is False


def test_chart_ready_series_pass_through_unchanged_and_remain_distinct_from_power():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=50.0,
        charger_count=1,
        charger_power=100.0,
        grid_capacity=25.0,
        transformer_other_load_kw=10.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    result = simulate(scenario)
    metrics = calculate_metrics(result, scenario)

    assert metrics.occupied_charger_count_by_timestep == (
        result.occupied_charger_count_by_timestep
    )
    assert metrics.waiting_vehicle_count_by_timestep == (
        result.waiting_vehicle_count_by_timestep
    )
    assert metrics.transformer_total_load_kw_by_timestep == (
        result.grid_loading.transformer_loading.total_load_kw_by_timestep
    )
    assert metrics.transformer_loading_percent_by_timestep == (
        result.grid_loading.transformer_loading.loading_percent_by_timestep
    )
    assert metrics.transformer_overload_kw_by_timestep == (
        result.grid_loading.transformer_loading.overload_kw_by_timestep
    )
    assert metrics.occupied_charger_count_by_timestep != (
        result.delivered_load_profile_kw
    )
    assert metrics.transformer_total_load_kw_by_timestep != (
        result.delivered_load_profile_kw
    )
    assert len(metrics.occupied_charger_count_by_timestep) == len(
        result.delivered_load_profile_kw
    )
    assert len(metrics.transformer_total_load_kw_by_timestep) == len(
        result.delivered_load_profile_kw
    )
    assert len(metrics.waiting_vehicle_count_by_timestep) == len(
        result.requested_load_profile_kw
    )
    assert len(metrics.transformer_loading_percent_by_timestep) == len(
        result.requested_load_profile_kw
    )


def test_overnight_window_uses_correct_timestep_range_for_charger_capacity_vs_demand_balance():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    )
    requested_slots = [0] * TIMESTEPS_PER_DAY
    requested_slots[10] = 9
    requested_slots[88] = 1
    requested_slots[89] = 2
    requested_slots[90] = 1
    requested_slots[0] = 1
    requested_slots[1] = 1

    metrics = calculate_metrics(
        SimulationResult(
            daily_energy_demand=40.0,
            configured_connection_capacity_kw=100.0,
            installed_charger_capacity_kw=50.0,
            available_site_charging_capacity_kw=50.0,
            requested_load_profile_kw=[0.0] * TIMESTEPS_PER_DAY,
            delivered_load_profile_kw=[0.0] * TIMESTEPS_PER_DAY,
            requested_charger_slots_by_timestep=requested_slots,
        ),
        scenario,
    )

    assert metrics.required_charger_count is None
    assert metrics.additional_chargers_required is None
    assert metrics.charger_count_sufficient_indicator is False
    assert metrics.charger_capacity_vs_demand_balance == -1


def test_capacity_sufficiency_is_true_when_no_energy_is_unmet():
    simulation_result = SimulationResult(
        daily_energy_demand=300.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=150.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[100.0] * 12,
        delivered_load_profile_kw=[100.0] * 12,
        delivered_energy=300.0,
        unmet_energy=0.0,
    )

    assert calculate_metrics(simulation_result, default_scenario).capacity_sufficiency is True


def test_capacity_sufficiency_is_false_when_energy_is_unmet():
    simulation_result = SimulationResult(
        daily_energy_demand=1200.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=150.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[100.0] * 10 + [0.0] * 2,
        delivered_load_profile_kw=[100.0] * 10 + [0.0] * 2,
        delivered_energy=1000.0,
        unmet_energy=200.0,
    )

    assert (
        calculate_metrics(simulation_result, default_scenario).capacity_sufficiency
        is False
    )


def test_delivered_energy_is_calculated_from_delivered_profile():
    simulation_result = SimulationResult(
        daily_energy_demand=1200.0,
        configured_connection_capacity_kw=200.0,
        installed_charger_capacity_kw=200.0,
        available_site_charging_capacity_kw=200.0,
        requested_load_profile_kw=[200.0, 200.0, 200.0],
        delivered_load_profile_kw=[150.0, 150.0, 150.0],
        delivered_energy=9999.0,
        unmet_energy=9999.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.delivered_energy == 3 * 150.0 * get_timestep_hours()


def test_unmet_energy_is_calculated_from_delivered_profile():
    simulation_result = SimulationResult(
        daily_energy_demand=1200.0,
        configured_connection_capacity_kw=200.0,
        installed_charger_capacity_kw=200.0,
        available_site_charging_capacity_kw=200.0,
        requested_load_profile_kw=[200.0] * 12,
        delivered_load_profile_kw=[150.0] * 12,
        delivered_energy=0.0,
        unmet_energy=0.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.delivered_energy == 450.0
    assert metrics.unmet_energy == 750.0


def test_unmet_energy_is_zero_when_delivered_energy_meets_daily_demand():
    simulation_result = SimulationResult(
        daily_energy_demand=300.0,
        configured_connection_capacity_kw=300.0,
        installed_charger_capacity_kw=300.0,
        available_site_charging_capacity_kw=300.0,
        requested_load_profile_kw=[100.0] * 12,
        delivered_load_profile_kw=[100.0] * 12,
        delivered_energy=0.0,
        unmet_energy=999.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.delivered_energy == 300.0
    assert metrics.unmet_energy == 0.0
    assert metrics.energy_delivery_sufficient is True


def test_unmet_energy_is_zero_when_delivered_energy_exceeds_daily_demand():
    simulation_result = SimulationResult(
        daily_energy_demand=250.0,
        configured_connection_capacity_kw=300.0,
        installed_charger_capacity_kw=300.0,
        available_site_charging_capacity_kw=300.0,
        requested_load_profile_kw=[100.0] * 12,
        delivered_load_profile_kw=[100.0] * 12,
        delivered_energy=0.0,
        unmet_energy=999.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.delivered_energy == 300.0
    assert metrics.unmet_energy == 0.0
    assert metrics.energy_delivery_sufficient is True


def test_energy_delivery_sufficient_matches_capacity_sufficiency_alias():
    metrics = Metrics(
        total_daily_energy=7500.0,
        available_capacity=1000.0,
        energy_delivery_sufficient=True,
    )

    assert metrics.energy_delivery_sufficient is True
    assert metrics.capacity_sufficiency is True


def test_capacity_sufficiency_alias_matches_calculated_energy_delivery_sufficient():
    simulation_result = SimulationResult(
        daily_energy_demand=500.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=150.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[150.0, 150.0, 150.0, 50.0],
        delivered_load_profile_kw=[100.0, 100.0, 100.0, 50.0],
        delivered_energy=0.0,
        unmet_energy=0.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.energy_delivery_sufficient is False
    assert metrics.capacity_sufficiency is False


def test_legacy_capacity_sufficiency_constructor_argument_remains_supported():
    metrics = Metrics(
        total_daily_energy=7500.0,
        available_capacity=1000.0,
        capacity_sufficiency=False,
    )

    assert metrics.energy_delivery_sufficient is False
    assert metrics.capacity_sufficiency is False


def test_heavy_duty_default_scenario_is_capacity_sufficient():
    metrics = calculate_metrics(simulate(default_scenario), default_scenario)

    assert metrics.total_daily_energy == 7500.0
    assert metrics.available_capacity == 1000.0
    assert metrics.energy_delivery_sufficient is True
    assert metrics.peak_load == 1000.0
    assert metrics.capacity_utilization == 100.0
    assert metrics.delivered_energy == 7500.0
    assert metrics.unmet_energy == 0.0
    assert metrics.annual_energy == 2737500.0
    assert metrics.required_connection_capacity_kw == 1500.0
    assert metrics.recommended_connection_capacity_kw == pytest.approx(1650.0)
    assert metrics.planning_margin_percent == default_scenario.planning_margin_percent
    assert metrics.peak_capacity_margin_kw == -500.0
    assert metrics.peak_capacity_margin_percent == -50.0
    assert metrics.connection_capacity_exceeded is True
    assert metrics.maximum_capacity_exceedance_kw == 500.0
    assert metrics.exceeded_timestep_count == 18
    assert metrics.capacity_exceedance_duration_hours == 4.5


def test_calculate_annual_energy_uses_daily_energy():
    assert calculate_annual_energy(total_daily_energy=7500.0) == 2737500.0


def test_calculate_metrics_uses_total_daily_energy_for_annual_energy():
    simulation_result = simulate(default_scenario)

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.annual_energy == metrics.total_daily_energy * 365.0


def test_metrics_work_for_smart_strategy_simulation_result():
    scenario = replace(default_scenario, charging_strategy=ChargingStrategy.SMART)
    simulation_result = simulate(scenario)

    metrics = calculate_metrics(simulation_result, scenario)

    assert metrics.peak_load == max(simulation_result.delivered_load_profile_kw)
    assert metrics.capacity_utilization == pytest.approx(
        metrics.peak_load
        / simulation_result.available_site_charging_capacity_kw
        * 100.0
    )
    assert metrics.delivered_energy == simulation_result.delivered_energy
    assert metrics.unmet_energy == simulation_result.unmet_energy


def test_average_power_based_utilization_differs_from_count_based_occupancy_in_smart_scenario():
    scenario = create_internal_scenario(
        vehicles=4,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
        charging_strategy=ChargingStrategy.SMART,
    )

    metrics = calculate_metrics(simulate(scenario), scenario)

    assert metrics.average_charger_utilization_percent == 25.0
    assert metrics.peak_charger_utilization_percent == 100.0
    assert metrics.average_occupied_charger_count == 2.0
    assert metrics.peak_occupied_charger_count == 2


def test_energy_delivery_sufficiency_can_be_true_while_connection_capacity_is_exceeded():
    simulation_result = SimulationResult(
        daily_energy_demand=25.0,
        configured_connection_capacity_kw=80.0,
        installed_charger_capacity_kw=120.0,
        available_site_charging_capacity_kw=80.0,
        requested_load_profile_kw=[100.0],
        delivered_load_profile_kw=[100.0],
        delivered_energy=0.0,
        unmet_energy=0.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.energy_delivery_sufficient is True
    assert metrics.connection_capacity_exceeded is True


def test_energy_delivery_sufficiency_can_be_false_without_connection_capacity_exceedance():
    simulation_result = SimulationResult(
        daily_energy_demand=300.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[100.0, 100.0],
        delivered_load_profile_kw=[100.0, 100.0],
        delivered_energy=0.0,
        unmet_energy=0.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.energy_delivery_sufficient is False
    assert metrics.connection_capacity_exceeded is False


def test_status_combination_energy_sufficient_and_capacity_not_exceeded():
    simulation_result = _build_status_test_result(
        daily_energy_demand=50.0,
        configured_connection_capacity_kw=100.0,
        requested_load_profile_kw=[100.0, 100.0],
        delivered_load_profile_kw=[100.0, 100.0],
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=100.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.energy_delivery_sufficient is True
    assert metrics.connection_capacity_exceeded is False
    assert metrics.capacity_sufficiency is True


def test_status_combination_energy_sufficient_and_capacity_exceeded():
    simulation_result = _build_status_test_result(
        daily_energy_demand=25.0,
        configured_connection_capacity_kw=80.0,
        requested_load_profile_kw=[100.0],
        delivered_load_profile_kw=[100.0],
        installed_charger_capacity_kw=120.0,
        available_site_charging_capacity_kw=80.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.energy_delivery_sufficient is True
    assert metrics.connection_capacity_exceeded is True
    assert metrics.capacity_sufficiency is True


def test_status_combination_energy_insufficient_and_capacity_not_exceeded():
    simulation_result = _build_status_test_result(
        daily_energy_demand=300.0,
        configured_connection_capacity_kw=100.0,
        requested_load_profile_kw=[100.0, 100.0],
        delivered_load_profile_kw=[100.0, 100.0],
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=100.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.energy_delivery_sufficient is False
    assert metrics.connection_capacity_exceeded is False
    assert metrics.capacity_sufficiency is False


def test_status_combination_energy_insufficient_and_capacity_exceeded():
    simulation_result = _build_status_test_result(
        daily_energy_demand=400.0,
        configured_connection_capacity_kw=100.0,
        requested_load_profile_kw=[150.0, 150.0],
        delivered_load_profile_kw=[100.0, 100.0],
        installed_charger_capacity_kw=150.0,
        available_site_charging_capacity_kw=100.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.energy_delivery_sufficient is False
    assert metrics.connection_capacity_exceeded is True
    assert metrics.capacity_sufficiency is False


def test_connection_capacity_status_is_based_on_requested_load_only():
    simulation_result = _build_status_test_result(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=80.0,
        requested_load_profile_kw=[100.0],
        delivered_load_profile_kw=[50.0],
        installed_charger_capacity_kw=120.0,
        available_site_charging_capacity_kw=80.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.connection_capacity_exceeded is True


def test_energy_delivery_status_is_based_on_delivered_load_only():
    simulation_result = _build_status_test_result(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=120.0,
        requested_load_profile_kw=[100.0],
        delivered_load_profile_kw=[50.0],
        installed_charger_capacity_kw=120.0,
        available_site_charging_capacity_kw=120.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.energy_delivery_sufficient is False
    assert metrics.connection_capacity_exceeded is False


def test_capacity_sufficiency_alias_survives_serialization_for_legacy_consumers():
    metrics = calculate_metrics(
        _build_status_test_result(
            daily_energy_demand=300.0,
            configured_connection_capacity_kw=100.0,
            requested_load_profile_kw=[100.0, 100.0],
            delivered_load_profile_kw=[100.0, 100.0],
            installed_charger_capacity_kw=100.0,
            available_site_charging_capacity_kw=100.0,
        ),
        default_scenario,
    )

    serialized = metrics_to_dict(metrics)
    restored = metrics_from_dict(serialized)

    assert serialized["capacity_sufficiency"] is False
    assert restored.capacity_sufficiency == restored.energy_delivery_sufficient


def test_calculate_metrics_exposes_connection_planning_fields():
    metrics = calculate_metrics(simulate(default_scenario), default_scenario)

    assert metrics.required_connection_capacity_kw == 1500.0
    assert metrics.recommended_connection_capacity_kw == pytest.approx(1650.0)
    assert metrics.planning_margin_percent == default_scenario.planning_margin_percent
    assert metrics.peak_capacity_margin_kw == -500.0
    assert metrics.peak_capacity_margin_percent == -50.0
    assert metrics.connection_capacity_exceeded is True
    assert metrics.maximum_capacity_exceedance_kw == 500.0
    assert metrics.exceeded_timestep_count == 18
    assert metrics.capacity_exceedance_duration_hours == 4.5


def test_required_connection_capacity_uses_requested_profile_peak():
    simulation_result = SimulationResult(
        daily_energy_demand=1200.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=150.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[0.0, 25.0, 150.0, 50.0],
        delivered_load_profile_kw=[0.0, 25.0, 100.0, 50.0],
        delivered_energy=175.0,
        unmet_energy=1025.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.required_connection_capacity_kw == 150.0


def test_peak_capacity_margin_is_positive_when_requested_peak_is_below_capacity():
    simulation_result = SimulationResult(
        daily_energy_demand=1200.0,
        configured_connection_capacity_kw=200.0,
        installed_charger_capacity_kw=150.0,
        available_site_charging_capacity_kw=150.0,
        requested_load_profile_kw=[0.0, 25.0, 150.0, 50.0],
        delivered_load_profile_kw=[0.0, 25.0, 150.0, 50.0],
        delivered_energy=225.0,
        unmet_energy=975.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.peak_capacity_margin_kw == 50.0
    assert metrics.peak_capacity_margin_percent == 25.0


def test_peak_capacity_margin_is_negative_when_requested_peak_exceeds_capacity():
    simulation_result = SimulationResult(
        daily_energy_demand=1200.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=150.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[0.0, 25.0, 150.0, 50.0],
        delivered_load_profile_kw=[0.0, 25.0, 100.0, 50.0],
        delivered_energy=175.0,
        unmet_energy=1025.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.peak_capacity_margin_kw == -50.0
    assert metrics.peak_capacity_margin_percent == -50.0


def test_requested_load_equal_to_capacity_is_not_an_exceedance():
    simulation_result = SimulationResult(
        daily_energy_demand=1200.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[100.0, 100.0, 0.0],
        delivered_load_profile_kw=[100.0, 100.0, 0.0],
        delivered_energy=200.0,
        unmet_energy=1000.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.connection_capacity_exceeded is False
    assert metrics.maximum_capacity_exceedance_kw == 0.0
    assert metrics.exceeded_timestep_count == 0
    assert metrics.capacity_exceedance_duration_hours == 0.0


def test_connection_capacity_exceedance_counts_and_duration_follow_requested_profile():
    simulation_result = SimulationResult(
        daily_energy_demand=1200.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=200.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[100.0, 120.0, 140.0, 90.0, 130.0],
        delivered_load_profile_kw=[100.0, 100.0, 100.0, 90.0, 100.0],
        delivered_energy=490.0,
        unmet_energy=710.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.connection_capacity_exceeded is True
    assert metrics.maximum_capacity_exceedance_kw == 40.0
    assert metrics.exceeded_timestep_count == 3
    assert metrics.capacity_exceedance_duration_hours == (
        3 * get_timestep_hours()
    )


def test_recommended_connection_capacity_applies_planning_margin():
    scenario = replace(default_scenario, planning_margin_percent=15.0)
    simulation_result = SimulationResult(
        daily_energy_demand=1200.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=200.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[100.0, 120.0, 140.0],
        delivered_load_profile_kw=[100.0, 100.0, 100.0],
        delivered_energy=300.0,
        unmet_energy=900.0,
    )

    metrics = calculate_metrics(simulation_result, scenario)

    assert metrics.required_connection_capacity_kw == 140.0
    assert metrics.recommended_connection_capacity_kw == pytest.approx(161.0)
    assert metrics.persistent_capacity_exceedance_indicator is True
    assert metrics.connection_capacity_adequate_indicator is False
    assert metrics.connection_capacity_recommendation_reason == (
        "persistent_requested_exceedance"
    )


def test_brief_connection_capacity_spike_does_not_force_upgrade_recommendation():
    scenario = replace(default_scenario, planning_margin_percent=15.0)
    simulation_result = SimulationResult(
        daily_energy_demand=1200.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=160.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[100.0, 140.0, 100.0],
        delivered_load_profile_kw=[100.0, 100.0, 100.0],
        delivered_energy=300.0,
        unmet_energy=900.0,
    )

    metrics = calculate_metrics(simulation_result, scenario)

    assert metrics.required_connection_capacity_kw == 140.0
    assert metrics.connection_capacity_exceeded is True
    assert metrics.exceeded_timestep_count == 1
    assert metrics.persistent_capacity_exceedance_indicator is False
    assert metrics.connection_capacity_adequate_indicator is True
    assert metrics.connection_capacity_recommendation_reason == (
        "configured_capacity_adequate"
    )
    assert metrics.recommended_connection_capacity_kw == 100.0


def test_delivered_load_does_not_affect_requested_profile_capacity_kpis():
    simulation_result = SimulationResult(
        daily_energy_demand=1200.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=200.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[100.0, 150.0, 120.0],
        delivered_load_profile_kw=[50.0, 50.0, 50.0],
        delivered_energy=150.0,
        unmet_energy=1050.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.required_connection_capacity_kw == 150.0
    assert metrics.maximum_capacity_exceedance_kw == 50.0
    assert metrics.exceeded_timestep_count == 2


def test_zero_configured_capacity_handles_peak_margin_percent_safely():
    simulation_result = SimulationResult(
        daily_energy_demand=1200.0,
        configured_connection_capacity_kw=0.0,
        installed_charger_capacity_kw=150.0,
        available_site_charging_capacity_kw=0.0,
        requested_load_profile_kw=[0.0, 25.0, 150.0, 50.0],
        delivered_load_profile_kw=[0.0, 0.0, 0.0, 0.0],
        delivered_energy=0.0,
        unmet_energy=1200.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.required_connection_capacity_kw == 150.0
    assert metrics.peak_capacity_margin_kw == -150.0
    assert metrics.peak_capacity_margin_percent is None
    assert metrics.connection_capacity_exceeded is True
    assert metrics.maximum_capacity_exceedance_kw == 150.0
    assert metrics.exceeded_timestep_count == 3


def test_metrics_use_delivered_profile_not_requested_profile():
    simulation_result = SimulationResult(
        daily_energy_demand=1200.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=150.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[0.0, 25.0, 150.0, 50.0],
        delivered_load_profile_kw=[0.0, 25.0, 100.0, 50.0],
        delivered_energy=175.0,
        unmet_energy=1025.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.peak_load == 100.0
    assert metrics.capacity_utilization == 100.0


def test_metrics_calculates_peak_load_from_simulated_load_profile():
    simulation_result = SimulationResult(
        daily_energy_demand=1200.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=150.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[0.0, 25.0, 100.0, 50.0],
        delivered_load_profile_kw=[0.0, 25.0, 100.0, 50.0],
        delivered_energy=175.0,
        unmet_energy=1025.0,
    )

    assert calculate_metrics(simulation_result, default_scenario).peak_load == 100.0


def test_metrics_calculates_delivered_energy_from_delivered_profile():
    simulation_result = SimulationResult(
        daily_energy_demand=1200.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=150.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[0.0, 25.0, 100.0, 50.0],
        delivered_load_profile_kw=[0.0, 25.0, 100.0, 50.0],
        delivered_energy=175.0,
        unmet_energy=1025.0,
    )

    assert (
        calculate_metrics(simulation_result, default_scenario).delivered_energy
        == 43.75
    )


def test_metrics_calculates_capacity_utilization_from_peak_and_available_capacity():
    simulation_result = SimulationResult(
        daily_energy_demand=1200.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=150.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[0.0, 25.0, 80.0, 50.0],
        delivered_load_profile_kw=[0.0, 25.0, 80.0, 50.0],
        delivered_energy=155.0,
        unmet_energy=1045.0,
    )

    assert (
        calculate_metrics(simulation_result, default_scenario).capacity_utilization
        == 80.0
    )


def test_metrics_limits_capacity_utilization_to_100_percent():
    simulation_result = SimulationResult(
        daily_energy_demand=1200.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=150.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[120.0],
        delivered_load_profile_kw=[120.0],
        delivered_energy=120.0,
        unmet_energy=1080.0,
    )

    assert (
        calculate_metrics(simulation_result, default_scenario).capacity_utilization
        == 100.0
    )


def test_metrics_uses_zero_peak_load_for_empty_profiles():
    simulation_result = SimulationResult(
        daily_energy_demand=1200.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=150.0,
        available_site_charging_capacity_kw=100.0,
        unmet_energy=1200.0,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.peak_load == 0.0
    assert metrics.capacity_utilization == 0.0


def test_metrics_handle_zero_vehicle_internal_scenario_without_infeasibility():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=150.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=500.0,
    )

    metrics = calculate_metrics(simulate(scenario), scenario)

    assert metrics.total_daily_energy == 0.0
    assert metrics.available_capacity == 100.0
    assert metrics.energy_delivery_sufficient is True
    assert metrics.peak_load == 0.0
    assert metrics.capacity_utilization == 0.0
    assert metrics.delivered_energy == 0.0
    assert metrics.unmet_energy == 0.0
    assert metrics.annual_energy == 0.0
    assert metrics.required_connection_capacity_kw == 0.0
    assert metrics.recommended_connection_capacity_kw == 0.0
    assert metrics.connection_capacity_exceeded is False
    assert metrics.required_charger_count == 0
    assert metrics.additional_chargers_required == 0
    assert metrics.charger_count_sufficient_indicator is True
    assert len(metrics.occupied_charger_count_by_timestep) == TIMESTEPS_PER_DAY
    assert len(metrics.waiting_vehicle_count_by_timestep) == TIMESTEPS_PER_DAY
    assert set(metrics.occupied_charger_count_by_timestep) == {0}
    assert set(metrics.waiting_vehicle_count_by_timestep) == {0}
    assert metrics.average_waiting_time_hours == 0.0
    assert metrics.maximum_waiting_time_hours == 0.0
    assert metrics.vehicles_waiting_count == 0
    assert metrics.vehicles_not_started_count == 0
    assert metrics.vehicles_with_unmet_energy_count == 0
    assert metrics.average_charger_utilization_percent == 0.0
    assert metrics.peak_charger_utilization_percent == 0.0


def test_metrics_handle_zero_chargers_with_vehicles_as_deterministic_insufficiency():
    scenario = create_internal_scenario(
        vehicles=5,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=500.0,
    )

    metrics = calculate_metrics(simulate(scenario), scenario)

    assert metrics.total_daily_energy == 100.0
    assert metrics.available_capacity == 0.0
    assert metrics.energy_delivery_sufficient is False
    assert metrics.peak_load == 0.0
    assert metrics.capacity_utilization == 0.0
    assert metrics.delivered_energy == 0.0
    assert metrics.unmet_energy == 100.0
    assert metrics.required_connection_capacity_kw == 0.0
    assert metrics.recommended_connection_capacity_kw == 0.0
    assert metrics.connection_capacity_exceeded is False
    assert metrics.maximum_capacity_exceedance_kw == 0.0
    assert metrics.exceeded_timestep_count == 0
    assert metrics.required_charger_count == 3
    assert metrics.additional_chargers_required == 3
    assert metrics.charger_count_sufficient_indicator is False
    assert len(metrics.occupied_charger_count_by_timestep) == TIMESTEPS_PER_DAY
    assert set(metrics.occupied_charger_count_by_timestep) == {0}
    assert len(metrics.waiting_vehicle_count_by_timestep) == TIMESTEPS_PER_DAY
    assert max(metrics.waiting_vehicle_count_by_timestep) > 0
    assert metrics.average_charger_utilization_percent is None
    assert metrics.peak_charger_utilization_percent is None
    assert metrics.average_waiting_time_hours is None
    assert metrics.maximum_waiting_time_hours is None
    assert metrics.vehicles_not_started_count == 5


def test_required_charger_recommendation_fields_are_none_for_non_availability_constraints():
    scenarios = [
        (
            "charger_power",
            create_internal_scenario(
                vehicles=1,
                daily_energy_per_vehicle=20.0,
                charger_count=1,
                charger_power=10.0,
                grid_capacity=100.0,
                charging_window_start=time(8, 0),
                charging_window_end=time(9, 0),
            ),
        ),
        (
            "grid_connection_capacity",
            create_internal_scenario(
                vehicles=2,
                daily_energy_per_vehicle=20.0,
                charger_count=2,
                charger_power=50.0,
                grid_capacity=20.0,
                charging_window_start=time(8, 0),
                charging_window_end=time(9, 0),
            ),
        ),
        (
            "charging_window",
            create_internal_scenario(
                vehicles=1,
                daily_energy_per_vehicle=20.0,
                charger_count=1,
                charger_power=50.0,
                grid_capacity=100.0,
                charging_window_start=time(8, 0),
                charging_window_end=time(8, 15),
                arrival_window_start=time(8, 15),
                arrival_window_end=time(8, 15),
            ),
        ),
        (
            "mixed",
            create_internal_scenario(
                vehicles=2,
                daily_energy_per_vehicle=20.0,
                charger_count=1,
                charger_power=10.0,
                grid_capacity=100.0,
                charging_window_start=time(8, 0),
                charging_window_end=time(9, 0),
            ),
        ),
    ]

    for expected_reason, scenario in scenarios:
        metrics = calculate_metrics(simulate(scenario), scenario)

        assert metrics.primary_constraint_reason == expected_reason
        assert metrics.required_charger_count is None
        assert metrics.additional_chargers_required is None
        assert metrics.charger_count_sufficient_indicator is False


def test_charger_recommendation_fields_remain_none_when_evidence_is_incomplete():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
    )
    simulation_result = SimulationResult(
        daily_energy_demand=40.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=50.0,
        available_site_charging_capacity_kw=50.0,
        requested_load_profile_kw=[50.0, 50.0],
        delivered_load_profile_kw=[50.0, 50.0],
        charging_requests=[],
        waiting_vehicle_count_by_timestep=[],
    )

    metrics = calculate_metrics(simulation_result, scenario)

    assert metrics.required_charger_count is None
    assert metrics.additional_chargers_required is None
    assert metrics.charger_count_sufficient_indicator is False


def test_charger_capacity_balance_does_not_imply_full_feasibility():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=10.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )

    metrics = calculate_metrics(simulate(scenario), scenario)

    assert metrics.charger_capacity_vs_demand_balance == 0
    assert metrics.required_charger_count is None
    assert metrics.additional_chargers_required is None
    assert metrics.vehicles_with_unmet_energy_count == 1


def test_metrics_handle_zero_vehicles_and_zero_chargers_safely():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=150.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=500.0,
    )

    metrics = calculate_metrics(simulate(scenario), scenario)

    assert metrics.total_daily_energy == 0.0
    assert metrics.available_capacity == 0.0
    assert metrics.energy_delivery_sufficient is True
    assert metrics.peak_load == 0.0
    assert metrics.capacity_utilization == 0.0
    assert metrics.delivered_energy == 0.0
    assert metrics.unmet_energy == 0.0
    assert metrics.required_connection_capacity_kw == 0.0
    assert metrics.recommended_connection_capacity_kw == 0.0
    assert metrics.connection_capacity_exceeded is False
    assert metrics.required_charger_count == 0
    assert metrics.additional_chargers_required == 0
    assert metrics.charger_count_sufficient_indicator is True
    assert len(metrics.occupied_charger_count_by_timestep) == TIMESTEPS_PER_DAY
    assert len(metrics.waiting_vehicle_count_by_timestep) == TIMESTEPS_PER_DAY
    assert set(metrics.occupied_charger_count_by_timestep) == {0}
    assert set(metrics.waiting_vehicle_count_by_timestep) == {0}
    assert metrics.average_charger_utilization_percent == 0.0
    assert metrics.peak_charger_utilization_percent == 0.0
    assert metrics.average_waiting_time_hours == 0.0
    assert metrics.maximum_waiting_time_hours == 0.0


def test_zero_demand_without_unresolved_outcomes_returns_zero_recommendation_values():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
    )
    metrics = calculate_metrics(
        SimulationResult(
            daily_energy_demand=0.0,
            configured_connection_capacity_kw=100.0,
            installed_charger_capacity_kw=50.0,
            available_site_charging_capacity_kw=50.0,
            requested_load_profile_kw=[0.0] * TIMESTEPS_PER_DAY,
            delivered_load_profile_kw=[0.0] * TIMESTEPS_PER_DAY,
            charging_requests=[],
            requested_charger_slots_by_timestep=[0] * TIMESTEPS_PER_DAY,
            waiting_vehicle_count_by_timestep=[],
        ),
        scenario,
    )

    assert metrics.required_charger_count == 0
    assert metrics.additional_chargers_required == 0
    assert metrics.charger_capacity_vs_demand_balance == 1


def test_no_queue_scenario_returns_zero_queue_metrics():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=10.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = SimulationResult(
        daily_energy_demand=20.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=_build_full_day_series(
            time(8, 0),
            [50.0, 50.0, 0.0, 0.0],
        ),
        delivered_load_profile_kw=_build_full_day_series(
            time(8, 0),
            [50.0, 50.0, 0.0, 0.0],
        ),
        charging_requests=[
            ChargingRequestResult(
                request_id="request-0",
                vehicle_index=0,
                arrival_timestep=32,
                departure_timestep=36,
                charging_start_timestep=32,
                charging_completion_timestep=33,
                energy_requested_kwh=10.0,
                energy_delivered_kwh=10.0,
                unmet_energy_kwh=0.0,
                waiting_time_hours=0.0,
                not_started_within_window=False,
                delayed_start_reason="none",
                unmet_energy_reason="none",
            ),
            ChargingRequestResult(
                request_id="request-1",
                vehicle_index=1,
                arrival_timestep=33,
                departure_timestep=36,
                charging_start_timestep=33,
                charging_completion_timestep=34,
                energy_requested_kwh=10.0,
                energy_delivered_kwh=10.0,
                unmet_energy_kwh=0.0,
                waiting_time_hours=0.0,
                not_started_within_window=False,
                delayed_start_reason="none",
                unmet_energy_reason="none",
            ),
        ],
        requested_charger_slots_by_timestep=_build_full_day_series(
            time(8, 0),
            [1, 1, 0, 0],
        ),
        occupied_charger_count_by_timestep=_build_full_day_series(
            time(8, 0),
            [1, 1, 0, 0],
        ),
        waiting_vehicle_count_by_timestep=_build_full_day_series(
            time(8, 0),
            [0, 0, 0, 0],
        ),
    )

    metrics = calculate_metrics(simulation_result, scenario)

    assert metrics.queue_present_indicator is False
    assert metrics.maximum_queue_length == 0
    assert metrics.average_queue_length == 0.0
    assert metrics.queue_duration_hours == 0.0
    assert metrics.average_waiting_time_hours == 0.0
    assert metrics.maximum_waiting_time_hours == 0.0
    assert metrics.vehicles_waiting_count == 0


def test_incomplete_legacy_raw_queueing_series_fall_back_to_safe_defaults():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=10.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = SimulationResult(
        daily_energy_demand=20.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[100.0, 0.0],
        delivered_load_profile_kw=[100.0, 0.0],
        requested_charger_slots_by_timestep=[2, 1],
        occupied_charger_count_by_timestep=[1],
        waiting_vehicle_count_by_timestep=[1, 0],
    )

    metrics = calculate_metrics(simulation_result, scenario)

    assert metrics.average_occupied_charger_count == 0.0
    assert metrics.peak_occupied_charger_count == 0
    assert metrics.charger_shortage_indicator is False
    assert metrics.queue_present_indicator is False
    assert metrics.maximum_queue_length == 0
    assert metrics.average_queue_length == 0.0
    assert metrics.queue_duration_hours == 0.0
    assert metrics.required_charger_count is None
    assert metrics.additional_chargers_required is None
    assert metrics.charger_count_sufficient_indicator is False
    assert metrics.charger_capacity_vs_demand_balance == 2
    assert metrics.occupied_charger_count_by_timestep == []
    assert metrics.waiting_vehicle_count_by_timestep == []


def test_vehicles_with_unmet_energy_count_uses_floating_point_tolerance():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=10.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = SimulationResult(
        daily_energy_demand=20.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=_build_full_day_series(
            time(8, 0),
            [50.0, 50.0, 0.0, 0.0],
        ),
        delivered_load_profile_kw=_build_full_day_series(
            time(8, 0),
            [50.0, 50.0, 0.0, 0.0],
        ),
        charging_requests=[
            ChargingRequestResult(
                request_id="request-0",
                vehicle_index=0,
                arrival_timestep=32,
                departure_timestep=36,
                charging_start_timestep=32,
                charging_completion_timestep=33,
                energy_requested_kwh=10.0,
                energy_delivered_kwh=10.0,
                unmet_energy_kwh=1e-10,
                waiting_time_hours=0.0,
                not_started_within_window=False,
                delayed_start_reason="none",
                unmet_energy_reason="none",
            ),
            ChargingRequestResult(
                request_id="request-1",
                vehicle_index=1,
                arrival_timestep=32,
                departure_timestep=36,
                charging_start_timestep=32,
                charging_completion_timestep=33,
                energy_requested_kwh=10.0,
                energy_delivered_kwh=9.99999999,
                unmet_energy_kwh=1e-8,
                waiting_time_hours=0.0,
                not_started_within_window=False,
                delayed_start_reason="none",
                unmet_energy_reason="charging_window",
            ),
        ],
    )

    metrics = calculate_metrics(simulation_result, scenario)

    assert metrics.vehicles_with_unmet_energy_count == 1


def test_waiting_time_metrics_exclude_requests_that_never_start():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = SimulationResult(
        daily_energy_demand=40.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=50.0,
        available_site_charging_capacity_kw=50.0,
        requested_load_profile_kw=_build_full_day_series(time(8, 0), [50.0, 50.0, 50.0, 50.0]),
        delivered_load_profile_kw=_build_full_day_series(time(8, 0), [50.0, 50.0, 50.0, 50.0]),
        charging_requests=[
            ChargingRequestResult(
                request_id="request-0",
                vehicle_index=0,
                arrival_timestep=32,
                departure_timestep=36,
                charging_start_timestep=33,
                charging_completion_timestep=None,
                energy_requested_kwh=20.0,
                energy_delivered_kwh=20.0,
                unmet_energy_kwh=0.0,
                waiting_time_hours=None,
                not_started_within_window=False,
                delayed_start_reason="charger_availability",
                unmet_energy_reason="none",
            ),
            ChargingRequestResult(
                request_id="request-1",
                vehicle_index=1,
                arrival_timestep=32,
                departure_timestep=36,
                charging_start_timestep=None,
                charging_completion_timestep=None,
                energy_requested_kwh=20.0,
                energy_delivered_kwh=0.0,
                unmet_energy_kwh=20.0,
                waiting_time_hours=None,
                not_started_within_window=True,
                delayed_start_reason="charger_availability",
                unmet_energy_reason="charger_availability",
            ),
        ],
    )

    metrics = calculate_metrics(simulation_result, scenario)

    assert metrics.average_waiting_time_hours == 0.25
    assert metrics.maximum_waiting_time_hours == 0.25
    assert metrics.vehicles_waiting_count == 1
    assert metrics.vehicles_not_started_count == 1


def test_primary_constraint_reason_is_none_for_feasible_scenario():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )

    metrics = calculate_metrics(simulate(scenario), scenario)

    assert metrics.primary_constraint_reason == "none"


def test_primary_constraint_reason_identifies_charger_availability():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )

    metrics = calculate_metrics(simulate(scenario), scenario)

    assert metrics.queue_present_indicator is True
    assert metrics.vehicles_with_unmet_energy_count == 0
    assert metrics.primary_constraint_reason == "charger_availability"


def test_primary_constraint_reason_identifies_charger_power():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=10.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )

    metrics = calculate_metrics(simulate(scenario), scenario)

    assert metrics.vehicles_with_unmet_energy_count == 1
    assert metrics.primary_constraint_reason == "charger_power"


def test_primary_constraint_reason_identifies_grid_connection_capacity():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=20.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )

    metrics = calculate_metrics(simulate(scenario), scenario)

    assert metrics.vehicles_with_unmet_energy_count == 2
    assert metrics.primary_constraint_reason == "grid_connection_capacity"


def test_primary_constraint_reason_identifies_charging_window():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(8, 15),
        arrival_window_start=time(8, 15),
        arrival_window_end=time(8, 15),
    )

    metrics = calculate_metrics(simulate(scenario), scenario)

    assert metrics.vehicles_not_started_count == 1
    assert metrics.primary_constraint_reason == "charging_window"


def test_primary_constraint_reason_returns_mixed_for_combined_limitations():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=10.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )

    metrics = calculate_metrics(simulate(scenario), scenario)

    assert metrics.primary_constraint_reason == "mixed"


@pytest.mark.parametrize(
    ("expected_reason", "scenario"),
    [
        (
            "none",
            create_internal_scenario(
                vehicles=2,
                daily_energy_per_vehicle=20.0,
                charger_count=2,
                charger_power=50.0,
                grid_capacity=100.0,
                charging_window_start=time(8, 0),
                charging_window_end=time(9, 0),
            ),
        ),
        (
            "charger_availability",
            create_internal_scenario(
                vehicles=2,
                daily_energy_per_vehicle=20.0,
                charger_count=1,
                charger_power=50.0,
                grid_capacity=100.0,
                charging_window_start=time(8, 0),
                charging_window_end=time(9, 0),
            ),
        ),
        (
            "charger_power",
            create_internal_scenario(
                vehicles=1,
                daily_energy_per_vehicle=20.0,
                charger_count=1,
                charger_power=10.0,
                grid_capacity=100.0,
                charging_window_start=time(8, 0),
                charging_window_end=time(9, 0),
            ),
        ),
        (
            "grid_connection_capacity",
            create_internal_scenario(
                vehicles=2,
                daily_energy_per_vehicle=20.0,
                charger_count=2,
                charger_power=50.0,
                grid_capacity=20.0,
                charging_window_start=time(8, 0),
                charging_window_end=time(9, 0),
            ),
        ),
        (
            "charging_window",
            create_internal_scenario(
                vehicles=1,
                daily_energy_per_vehicle=20.0,
                charger_count=1,
                charger_power=50.0,
                grid_capacity=100.0,
                charging_window_start=time(8, 0),
                charging_window_end=time(8, 15),
                arrival_window_start=time(8, 15),
                arrival_window_end=time(8, 15),
            ),
        ),
        (
            "mixed",
            create_internal_scenario(
                vehicles=2,
                daily_energy_per_vehicle=20.0,
                charger_count=1,
                charger_power=10.0,
                grid_capacity=100.0,
                charging_window_start=time(8, 0),
                charging_window_end=time(9, 0),
            ),
        ),
    ],
    ids=[
        "feasible",
        "availability",
        "power",
        "grid-capacity",
        "window",
        "mixed",
    ],
)
def test_primary_constraint_reason_matches_current_counterfactual_fixtures(
    expected_reason,
    scenario,
):
    metrics = calculate_metrics(simulate(scenario), scenario)

    assert metrics.primary_constraint_reason == expected_reason


def test_primary_constraint_reason_counterfactual_reruns_skip_planner_diagnostics(
    monkeypatch,
):
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=10.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = simulate(scenario)
    original_helper = metrics_module._calculate_planner_diagnostic_values
    planner_diagnostic_call_count = 0

    def wrapped_planner_diagnostic_values(*args, **kwargs):
        nonlocal planner_diagnostic_call_count
        planner_diagnostic_call_count += 1
        return original_helper(*args, **kwargs)

    monkeypatch.setattr(
        metrics_module,
        "_calculate_planner_diagnostic_values",
        wrapped_planner_diagnostic_values,
    )

    metrics = calculate_metrics(simulation_result, scenario)

    assert metrics.primary_constraint_reason == "mixed"
    assert planner_diagnostic_call_count == 1


def test_primary_constraint_reason_is_none_for_zero_vehicle_scenario():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )

    metrics = calculate_metrics(simulate(scenario), scenario)

    assert metrics.primary_constraint_reason == "none"


def test_primary_constraint_reason_is_none_for_zero_demand_scenario():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = SimulationResult(
        daily_energy_demand=0.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=50.0,
        available_site_charging_capacity_kw=50.0,
        requested_load_profile_kw=[0.0] * TIMESTEPS_PER_DAY,
        delivered_load_profile_kw=[0.0] * TIMESTEPS_PER_DAY,
        charging_requests=[],
        requested_charger_slots_by_timestep=[0] * TIMESTEPS_PER_DAY,
        waiting_vehicle_count_by_timestep=[0] * TIMESTEPS_PER_DAY,
    )

    metrics = calculate_metrics(simulation_result, scenario)

    assert metrics.primary_constraint_reason == "none"


def test_primary_constraint_reason_handles_zero_chargers_with_demand_via_counterfactual_sequence():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )

    metrics = calculate_metrics(simulate(scenario), scenario)

    assert metrics.vehicles_not_started_count == 2
    assert metrics.primary_constraint_reason == "charger_availability"


def test_primary_constraint_reason_is_deterministic_across_repeated_runs():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=20.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )

    first_metrics = calculate_metrics(simulate(scenario), scenario)
    second_metrics = calculate_metrics(simulate(scenario), scenario)

    assert first_metrics.primary_constraint_reason == (
        second_metrics.primary_constraint_reason
    )


def test_primary_constraint_reason_counterfactuals_do_not_mutate_original_inputs_or_existing_metrics():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=10.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    original_result = simulate(scenario)

    metrics = calculate_metrics(original_result, scenario)

    assert scenario == create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=10.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    assert original_result == simulate(scenario)
    assert metrics.peak_load == 10.0
    assert metrics.unmet_energy == pytest.approx(30.0)
    assert metrics.primary_constraint_reason == "mixed"


@pytest.mark.parametrize(
    ("scenario"),
    [
        default_scenario,
        create_internal_scenario(
            vehicles=2,
            daily_energy_per_vehicle=20.0,
            charger_count=1,
            charger_power=10.0,
            grid_capacity=100.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(9, 0),
        ),
        create_internal_scenario(
            vehicles=2,
            daily_energy_per_vehicle=20.0,
            charger_count=2,
            charger_power=50.0,
            grid_capacity=20.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(9, 0),
        ),
    ],
    ids=[
        "default",
        "charger-availability-and-window-pressure",
        "grid-capacity-pressure",
    ],
)
def test_internal_metrics_helper_paths_reconstruct_full_metrics_result(scenario):
    simulation_result = simulate(scenario)

    direct_metrics = _calculate_direct_metrics_values(
        simulation_result,
        scenario,
    )
    planner_diagnostics = _calculate_planner_diagnostic_values(
        simulation_result,
        scenario,
        direct_metrics.planner_diagnostics_inputs,
        include_primary_constraint_reason=True,
        include_charger_count_recommendation=True,
    )
    helper_metrics = Metrics(
        **direct_metrics.metrics_kwargs,
        **planner_diagnostics,
    )
    public_metrics = calculate_metrics(simulation_result, scenario)

    assert helper_metrics == public_metrics
    assert metrics_to_dict(helper_metrics) == metrics_to_dict(public_metrics)


def test_internal_metrics_helper_paths_cover_full_metrics_contract_without_overlap():
    simulation_result = simulate(default_scenario)

    direct_metrics = _calculate_direct_metrics_values(
        simulation_result,
        default_scenario,
    )
    planner_diagnostics = _calculate_planner_diagnostic_values(
        simulation_result,
        default_scenario,
        direct_metrics.planner_diagnostics_inputs,
        include_primary_constraint_reason=True,
        include_charger_count_recommendation=True,
    )

    direct_keys = set(direct_metrics.metrics_kwargs)
    planner_keys = set(planner_diagnostics)
    metric_field_names = {field.name for field in fields(Metrics)}

    assert direct_keys.isdisjoint(planner_keys)
    assert direct_keys | planner_keys == metric_field_names


def test_primary_constraint_reason_returns_mixed_when_legacy_queueing_inputs_are_incomplete():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = SimulationResult(
        daily_energy_demand=40.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=50.0,
        available_site_charging_capacity_kw=50.0,
        requested_load_profile_kw=_build_full_day_series(time(8, 0), [50.0, 50.0, 0.0, 0.0]),
        delivered_load_profile_kw=_build_full_day_series(time(8, 0), [50.0, 50.0, 0.0, 0.0]),
        charging_requests=[
            ChargingRequestResult(
                request_id="request-0",
                vehicle_index=0,
                arrival_timestep=32,
                departure_timestep=36,
                charging_start_timestep=None,
                charging_completion_timestep=None,
                energy_requested_kwh=20.0,
                energy_delivered_kwh=0.0,
                unmet_energy_kwh=20.0,
                waiting_time_hours=None,
                not_started_within_window=True,
                delayed_start_reason="charger_availability",
                unmet_energy_reason="charger_availability",
            ),
        ],
        requested_charger_slots_by_timestep=[1, 1],
        waiting_vehicle_count_by_timestep=[1, 1],
    )

    metrics = calculate_metrics(simulation_result, scenario)

    assert metrics.primary_constraint_reason == "mixed"


def test_new_metric_fields_survive_serialization_and_legacy_payloads():
    metrics = calculate_metrics(simulate(default_scenario), default_scenario)

    data = metrics_to_dict(metrics)
    restored_metrics = metrics_from_dict(data)
    legacy_restored_metrics = metrics_from_dict(
        {
            "total_daily_energy": 7500.0,
            "available_capacity": 1000.0,
            "capacity_sufficiency": True,
            "peak_load": 1000.0,
            "capacity_utilization": 100.0,
            "delivered_energy": 7500.0,
            "unmet_energy": 0.0,
            "annual_energy": 2737500.0,
        }
    )

    for field_name in [
        "average_transformer_loading_percent",
        "peak_transformer_loading_percent",
        "transformer_overload_indicator",
        "transformer_overload_duration_hours",
        "transformer_maximum_overload_kw",
        "maximum_feeder_loading_percent",
        "feeder_overload_indicator",
        "overloaded_feeder_count",
        "transformer_thermal_risk_level",
        "highest_feeder_thermal_risk_level",
        "most_loaded_feeder_id",
        "peak_feeder_loading_spread_percentage_points",
        "feeder_loading_distribution_label",
        "feeder_status_message",
        "show_feeder_detail_indicator",
        "peak_harmonic_risk_score",
        "average_harmonic_risk_score",
        "harmonic_risk_duration_hours",
        "harmonic_risk_level",
        "harmonic_warning_indicator",
        "peak_current_imbalance_percent",
        "average_current_imbalance_percent",
        "imbalance_duration_hours",
        "current_imbalance_risk_level",
        "imbalance_warning_indicator",
        "overall_pq_risk_score",
        "overall_pq_risk_level",
        "overall_pq_warning_indicator",
        "power_quality_warning_count",
        "power_quality_message",
        "average_charger_utilization_percent",
        "peak_charger_utilization_percent",
        "average_occupied_charger_count",
        "peak_occupied_charger_count",
        "charger_shortage_indicator",
        "queue_present_indicator",
        "maximum_queue_length",
        "average_queue_length",
        "queue_duration_hours",
        "average_waiting_time_hours",
        "maximum_waiting_time_hours",
        "charger_service_waiting_tolerance_hours",
        "vehicles_waiting_count",
        "vehicles_not_started_count",
        "vehicles_with_unmet_energy_count",
        "charger_capacity_vs_demand_balance",
        "required_charger_count",
        "additional_chargers_required",
        "charger_count_sufficient_indicator",
        "primary_constraint_reason",
        "feeder_summary_rows",
        "transformer_total_load_kw_by_timestep",
        "transformer_loading_percent_by_timestep",
        "transformer_overload_kw_by_timestep",
        "occupied_charger_count_by_timestep",
        "waiting_vehicle_count_by_timestep",
        "harmonic_risk_score_by_timestep",
        "current_imbalance_percent_by_timestep",
        "overall_pq_risk_score_by_timestep",
        "phase_a_load_kw_by_timestep",
        "phase_b_load_kw_by_timestep",
        "phase_c_load_kw_by_timestep",
    ]:
        assert field_name in data
    assert restored_metrics == metrics
    assert legacy_restored_metrics.average_transformer_loading_percent == 0.0
    assert legacy_restored_metrics.peak_transformer_loading_percent == 0.0
    assert legacy_restored_metrics.transformer_overload_indicator is False
    assert legacy_restored_metrics.transformer_overload_duration_hours == 0.0
    assert legacy_restored_metrics.transformer_maximum_overload_kw == 0.0
    assert legacy_restored_metrics.transformer_thermal_risk_level == THERMAL_RISK_LOW
    assert legacy_restored_metrics.maximum_feeder_loading_percent == 0.0
    assert legacy_restored_metrics.feeder_overload_indicator is False
    assert legacy_restored_metrics.overloaded_feeder_count == 0
    assert legacy_restored_metrics.highest_feeder_thermal_risk_level == THERMAL_RISK_LOW
    assert legacy_restored_metrics.most_loaded_feeder_id is None
    assert (
        legacy_restored_metrics.peak_feeder_loading_spread_percentage_points
        == 0.0
    )
    assert (
        legacy_restored_metrics.feeder_loading_distribution_label
        == "No feeders modeled"
    )
    assert (
        legacy_restored_metrics.feeder_status_message
        == "No feeder-level load was modeled."
    )
    assert legacy_restored_metrics.show_feeder_detail_indicator is False
    assert legacy_restored_metrics.peak_harmonic_risk_score == 0.0
    assert legacy_restored_metrics.average_harmonic_risk_score == 0.0
    assert legacy_restored_metrics.harmonic_risk_duration_hours == 0.0
    assert legacy_restored_metrics.harmonic_risk_level == "low"
    assert legacy_restored_metrics.harmonic_warning_indicator is False
    assert legacy_restored_metrics.peak_current_imbalance_percent == 0.0
    assert legacy_restored_metrics.average_current_imbalance_percent == 0.0
    assert legacy_restored_metrics.imbalance_duration_hours == 0.0
    assert legacy_restored_metrics.current_imbalance_risk_level == "low"
    assert legacy_restored_metrics.imbalance_warning_indicator is False
    assert legacy_restored_metrics.overall_pq_risk_score == 0.0
    assert legacy_restored_metrics.overall_pq_risk_level == "low"
    assert legacy_restored_metrics.overall_pq_warning_indicator is False
    assert legacy_restored_metrics.power_quality_warning_count == 0
    assert legacy_restored_metrics.power_quality_message == ""
    assert legacy_restored_metrics.average_charger_utilization_percent == 0.0
    assert legacy_restored_metrics.maximum_waiting_time_hours == 0.0
    assert legacy_restored_metrics.charger_capacity_vs_demand_balance == 0
    assert legacy_restored_metrics.required_charger_count == 0
    assert legacy_restored_metrics.additional_chargers_required == 0
    assert legacy_restored_metrics.charger_count_sufficient_indicator is True
    assert legacy_restored_metrics.primary_constraint_reason == "none"
    assert legacy_restored_metrics.feeder_summary_rows == []
    assert legacy_restored_metrics.transformer_total_load_kw_by_timestep == []
    assert legacy_restored_metrics.transformer_loading_percent_by_timestep == []
    assert legacy_restored_metrics.transformer_overload_kw_by_timestep == []
    assert legacy_restored_metrics.occupied_charger_count_by_timestep == []
    assert legacy_restored_metrics.waiting_vehicle_count_by_timestep == []
    assert legacy_restored_metrics.harmonic_risk_score_by_timestep == []
    assert legacy_restored_metrics.current_imbalance_percent_by_timestep == []
    assert legacy_restored_metrics.overall_pq_risk_score_by_timestep == []
    assert legacy_restored_metrics.phase_a_load_kw_by_timestep == []
    assert legacy_restored_metrics.phase_b_load_kw_by_timestep == []
    assert legacy_restored_metrics.phase_c_load_kw_by_timestep == []


def test_serialized_metrics_are_json_safe_with_none_boolean_string_and_series_values():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )

    metrics = calculate_metrics(simulate(scenario), scenario)
    data = metrics_to_dict(metrics)
    json_loaded = json.loads(json.dumps(data))

    assert json_loaded["average_charger_utilization_percent"] is None
    assert json_loaded["peak_charger_utilization_percent"] is None
    assert json_loaded["average_waiting_time_hours"] is None
    assert json_loaded["maximum_waiting_time_hours"] is None
    assert json_loaded["required_charger_count"] == 1
    assert json_loaded["additional_chargers_required"] == 1
    assert json_loaded["charger_count_sufficient_indicator"] is False
    assert json_loaded["queue_present_indicator"] is True
    assert json_loaded["primary_constraint_reason"] == "charger_availability"
    assert isinstance(json_loaded["feeder_summary_rows"], list)
    assert isinstance(json_loaded["transformer_total_load_kw_by_timestep"], list)
    assert isinstance(json_loaded["transformer_loading_percent_by_timestep"], list)
    assert isinstance(json_loaded["transformer_overload_kw_by_timestep"], list)
    assert isinstance(json_loaded["occupied_charger_count_by_timestep"], list)
    assert isinstance(json_loaded["waiting_vehicle_count_by_timestep"], list)
    assert isinstance(json_loaded["harmonic_risk_score_by_timestep"], list)
    assert isinstance(json_loaded["current_imbalance_percent_by_timestep"], list)
    assert isinstance(json_loaded["overall_pq_risk_score_by_timestep"], list)
    assert isinstance(json_loaded["phase_a_load_kw_by_timestep"], list)
    assert isinstance(json_loaded["phase_b_load_kw_by_timestep"], list)
    assert isinstance(json_loaded["phase_c_load_kw_by_timestep"], list)
    assert len(json_loaded["transformer_total_load_kw_by_timestep"]) == TIMESTEPS_PER_DAY
    assert len(json_loaded["transformer_loading_percent_by_timestep"]) == TIMESTEPS_PER_DAY
    assert len(json_loaded["transformer_overload_kw_by_timestep"]) == TIMESTEPS_PER_DAY
    assert len(json_loaded["occupied_charger_count_by_timestep"]) == TIMESTEPS_PER_DAY
    assert len(json_loaded["waiting_vehicle_count_by_timestep"]) == TIMESTEPS_PER_DAY
    assert len(json_loaded["harmonic_risk_score_by_timestep"]) == TIMESTEPS_PER_DAY
    assert len(json_loaded["current_imbalance_percent_by_timestep"]) == TIMESTEPS_PER_DAY
    assert len(json_loaded["overall_pq_risk_score_by_timestep"]) == TIMESTEPS_PER_DAY
    assert set(json_loaded["overall_pq_risk_score_by_timestep"]) == {0.0}
    assert len(json_loaded["phase_a_load_kw_by_timestep"]) == TIMESTEPS_PER_DAY
    assert len(json_loaded["phase_b_load_kw_by_timestep"]) == TIMESTEPS_PER_DAY
    assert len(json_loaded["phase_c_load_kw_by_timestep"]) == TIMESTEPS_PER_DAY


def test_two_independent_scenarios_expose_the_same_serialized_metric_key_contract():
    scenario_a = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    scenario_b = create_internal_scenario(
        vehicles=5,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=500.0,
    )

    data_a = metrics_to_dict(calculate_metrics(simulate(scenario_a), scenario_a))
    data_b = metrics_to_dict(calculate_metrics(simulate(scenario_b), scenario_b))

    assert list(data_a.keys()) == list(data_b.keys())
    assert data_a["primary_constraint_reason"] == "none"
    assert data_b["primary_constraint_reason"] == "charger_availability"


def test_zero_vehicle_metrics_serialize_with_full_day_zero_series():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )

    data = metrics_to_dict(calculate_metrics(simulate(scenario), scenario))

    assert data["primary_constraint_reason"] == "none"
    assert data["vehicles_waiting_count"] == 0
    assert data["vehicles_not_started_count"] == 0
    assert data["vehicles_with_unmet_energy_count"] == 0
    assert len(data["occupied_charger_count_by_timestep"]) == TIMESTEPS_PER_DAY
    assert len(data["waiting_vehicle_count_by_timestep"]) == TIMESTEPS_PER_DAY
    assert set(data["occupied_charger_count_by_timestep"]) == {0}
    assert set(data["waiting_vehicle_count_by_timestep"]) == {0}


def test_no_started_vehicle_and_infeasible_metrics_serialize_with_explicit_none_values():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(8, 15),
        arrival_window_start=time(8, 15),
        arrival_window_end=time(8, 15),
    )

    data = metrics_to_dict(calculate_metrics(simulate(scenario), scenario))

    assert data["average_waiting_time_hours"] is None
    assert data["maximum_waiting_time_hours"] is None
    assert data["vehicles_not_started_count"] == 1
    assert data["vehicles_with_unmet_energy_count"] == 1
    assert data["primary_constraint_reason"] == "charging_window"


def test_legacy_or_incomplete_raw_queueing_outputs_serialize_safely_with_defaults():
    metrics = calculate_metrics(
        SimulationResult(
            daily_energy_demand=100.0,
            configured_connection_capacity_kw=100.0,
            installed_charger_capacity_kw=100.0,
            available_site_charging_capacity_kw=100.0,
            requested_load_profile_kw=[100.0, 0.0],
            delivered_load_profile_kw=[100.0, 0.0],
            requested_charger_slots_by_timestep=[2, 1],
            occupied_charger_count_by_timestep=[1],
            waiting_vehicle_count_by_timestep=[1, 0],
        ),
        default_scenario,
    )
    data = metrics_to_dict(metrics)

    assert data["occupied_charger_count_by_timestep"] == []
    assert data["waiting_vehicle_count_by_timestep"] == []
    assert data["primary_constraint_reason"] == "none"
    assert data["average_occupied_charger_count"] == 0.0
    assert data["maximum_queue_length"] == 0


def test_serialized_metrics_preserve_none_recommendation_values_when_adding_chargers_cannot_solve_problem():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=10.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )

    data = metrics_to_dict(calculate_metrics(simulate(scenario), scenario))

    assert data["required_charger_count"] is None
    assert data["additional_chargers_required"] is None
    assert data["charger_capacity_vs_demand_balance"] == 0


def test_metrics_serialization_does_not_mutate_metrics_scenario_or_simulation_result():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)
    original_occupied_series = list(metrics.occupied_charger_count_by_timestep)
    original_waiting_series = list(metrics.waiting_vehicle_count_by_timestep)

    data = metrics_to_dict(metrics)
    data["occupied_charger_count_by_timestep"][0] = 999
    data["waiting_vehicle_count_by_timestep"][0] = 999

    assert metrics.occupied_charger_count_by_timestep == original_occupied_series
    assert metrics.waiting_vehicle_count_by_timestep == original_waiting_series
    assert scenario == create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    assert simulation_result == simulate(scenario)


def test_missing_legacy_occupancy_and_waiting_series_remain_safe_and_empty():
    metrics = calculate_metrics(
        SimulationResult(
            daily_energy_demand=100.0,
            configured_connection_capacity_kw=100.0,
            installed_charger_capacity_kw=100.0,
            available_site_charging_capacity_kw=100.0,
            requested_load_profile_kw=[100.0, 0.0],
            delivered_load_profile_kw=[100.0, 0.0],
        ),
        default_scenario,
    )

    assert metrics.occupied_charger_count_by_timestep == []
    assert metrics.waiting_vehicle_count_by_timestep == []


def test_metrics_are_immutable():
    metrics = calculate_metrics(simulate(default_scenario), default_scenario)

    with pytest.raises(FrozenInstanceError):
        metrics.total_daily_energy = 1.0


def test_metrics_serialization_round_trip_preserves_values():
    metrics = calculate_metrics(simulate(default_scenario), default_scenario)

    data = metrics_to_dict(metrics)
    restored_metrics = metrics_from_dict(data)

    assert data == {
        "total_daily_energy": metrics.total_daily_energy,
        "available_capacity": metrics.available_capacity,
        "energy_delivery_sufficient": metrics.energy_delivery_sufficient,
        "capacity_sufficiency": metrics.capacity_sufficiency,
        "peak_load": metrics.peak_load,
        "capacity_utilization": metrics.capacity_utilization,
        "delivered_energy": metrics.delivered_energy,
        "unmet_energy": metrics.unmet_energy,
        "annual_energy": metrics.annual_energy,
        "configured_connection_capacity_kw": (
            metrics.configured_connection_capacity_kw
        ),
        "required_connection_capacity_kw": metrics.required_connection_capacity_kw,
        "recommended_connection_capacity_kw": (
            metrics.recommended_connection_capacity_kw
        ),
        "planning_margin_percent": metrics.planning_margin_percent,
        "peak_capacity_margin_kw": metrics.peak_capacity_margin_kw,
        "peak_capacity_margin_percent": metrics.peak_capacity_margin_percent,
        "connection_capacity_exceeded": metrics.connection_capacity_exceeded,
        "maximum_capacity_exceedance_kw": (
            metrics.maximum_capacity_exceedance_kw
        ),
        "exceeded_timestep_count": metrics.exceeded_timestep_count,
        "capacity_exceedance_duration_hours": (
            metrics.capacity_exceedance_duration_hours
        ),
        "persistent_capacity_exceedance_indicator": (
            metrics.persistent_capacity_exceedance_indicator
        ),
        "connection_capacity_adequate_indicator": (
            metrics.connection_capacity_adequate_indicator
        ),
        "connection_capacity_recommendation_reason": (
            metrics.connection_capacity_recommendation_reason
        ),
        "average_transformer_loading_percent": (
            metrics.average_transformer_loading_percent
        ),
        "peak_transformer_loading_percent": (
            metrics.peak_transformer_loading_percent
        ),
        "transformer_overload_indicator": (
            metrics.transformer_overload_indicator
        ),
        "transformer_overload_duration_hours": (
            metrics.transformer_overload_duration_hours
        ),
        "transformer_maximum_overload_kw": (
            metrics.transformer_maximum_overload_kw
        ),
        "transformer_thermal_risk_level": (
            metrics.transformer_thermal_risk_level
        ),
        "maximum_feeder_loading_percent": (
            metrics.maximum_feeder_loading_percent
        ),
        "feeder_overload_indicator": metrics.feeder_overload_indicator,
        "overloaded_feeder_count": metrics.overloaded_feeder_count,
        "highest_feeder_thermal_risk_level": (
            metrics.highest_feeder_thermal_risk_level
        ),
        "most_loaded_feeder_id": metrics.most_loaded_feeder_id,
        "peak_feeder_loading_spread_percentage_points": (
            metrics.peak_feeder_loading_spread_percentage_points
        ),
        "feeder_loading_distribution_label": (
            metrics.feeder_loading_distribution_label
        ),
        "feeder_status_message": metrics.feeder_status_message,
        "show_feeder_detail_indicator": (
            metrics.show_feeder_detail_indicator
        ),
        "peak_harmonic_risk_score": metrics.peak_harmonic_risk_score,
        "average_harmonic_risk_score": metrics.average_harmonic_risk_score,
        "harmonic_risk_duration_hours": metrics.harmonic_risk_duration_hours,
        "harmonic_risk_level": metrics.harmonic_risk_level,
        "harmonic_warning_indicator": metrics.harmonic_warning_indicator,
        "peak_current_imbalance_percent": (
            metrics.peak_current_imbalance_percent
        ),
        "average_current_imbalance_percent": (
            metrics.average_current_imbalance_percent
        ),
        "imbalance_duration_hours": metrics.imbalance_duration_hours,
        "current_imbalance_risk_level": (
            metrics.current_imbalance_risk_level
        ),
        "imbalance_warning_indicator": metrics.imbalance_warning_indicator,
        "overall_pq_risk_score": metrics.overall_pq_risk_score,
        "overall_pq_risk_level": metrics.overall_pq_risk_level,
        "overall_pq_warning_indicator": metrics.overall_pq_warning_indicator,
        "power_quality_warning_count": metrics.power_quality_warning_count,
        "power_quality_message": metrics.power_quality_message,
        "average_charger_utilization_percent": (
            metrics.average_charger_utilization_percent
        ),
        "peak_charger_utilization_percent": (
            metrics.peak_charger_utilization_percent
        ),
        "average_occupied_charger_count": (
            metrics.average_occupied_charger_count
        ),
        "peak_occupied_charger_count": metrics.peak_occupied_charger_count,
        "charger_shortage_indicator": metrics.charger_shortage_indicator,
        "queue_present_indicator": metrics.queue_present_indicator,
        "maximum_queue_length": metrics.maximum_queue_length,
        "average_queue_length": metrics.average_queue_length,
        "queue_duration_hours": metrics.queue_duration_hours,
        "average_waiting_time_hours": metrics.average_waiting_time_hours,
        "maximum_waiting_time_hours": metrics.maximum_waiting_time_hours,
        "charger_service_waiting_tolerance_hours": (
            metrics.charger_service_waiting_tolerance_hours
        ),
        "vehicles_waiting_count": metrics.vehicles_waiting_count,
        "vehicles_not_started_count": metrics.vehicles_not_started_count,
        "vehicles_with_unmet_energy_count": (
            metrics.vehicles_with_unmet_energy_count
        ),
        "charger_capacity_vs_demand_balance": (
            metrics.charger_capacity_vs_demand_balance
        ),
        "required_charger_count": metrics.required_charger_count,
        "additional_chargers_required": (
            metrics.additional_chargers_required
        ),
        "charger_count_sufficient_indicator": (
            metrics.charger_count_sufficient_indicator
        ),
        "primary_constraint_reason": metrics.primary_constraint_reason,
        "feeder_summary_rows": [
            {
                "feeder_id": feeder_summary.feeder_id,
                "charger_count": feeder_summary.charger_count,
                "peak_loading_percent": feeder_summary.peak_loading_percent,
                "overload_indicator": feeder_summary.overload_indicator,
                "overload_duration_hours": (
                    feeder_summary.overload_duration_hours
                ),
                "maximum_overload_kw": feeder_summary.maximum_overload_kw,
                "thermal_risk_level": feeder_summary.thermal_risk_level,
            }
            for feeder_summary in metrics.feeder_summary_rows
        ],
        "transformer_total_load_kw_by_timestep": (
            metrics.transformer_total_load_kw_by_timestep
        ),
        "transformer_loading_percent_by_timestep": (
            metrics.transformer_loading_percent_by_timestep
        ),
        "transformer_overload_kw_by_timestep": (
            metrics.transformer_overload_kw_by_timestep
        ),
        "occupied_charger_count_by_timestep": (
            metrics.occupied_charger_count_by_timestep
        ),
        "waiting_vehicle_count_by_timestep": (
            metrics.waiting_vehicle_count_by_timestep
        ),
        "harmonic_risk_score_by_timestep": (
            metrics.harmonic_risk_score_by_timestep
        ),
        "current_imbalance_percent_by_timestep": (
            metrics.current_imbalance_percent_by_timestep
        ),
        "overall_pq_risk_score_by_timestep": (
            metrics.overall_pq_risk_score_by_timestep
        ),
        "phase_a_load_kw_by_timestep": metrics.phase_a_load_kw_by_timestep,
        "phase_b_load_kw_by_timestep": metrics.phase_b_load_kw_by_timestep,
        "phase_c_load_kw_by_timestep": metrics.phase_c_load_kw_by_timestep,
    }
    assert restored_metrics == metrics


def test_metrics_deserialization_supports_legacy_capacity_sufficiency_payload():
    legacy_data = {
        "total_daily_energy": 7500.0,
        "available_capacity": 1000.0,
        "capacity_sufficiency": True,
        "peak_load": 1000.0,
        "capacity_utilization": 100.0,
        "delivered_energy": 7500.0,
        "unmet_energy": 0.0,
        "annual_energy": 2737500.0,
    }

    metrics = metrics_from_dict(legacy_data)

    assert metrics.energy_delivery_sufficient is True
    assert metrics.capacity_sufficiency is True
    assert metrics.configured_connection_capacity_kw == 0.0
    assert metrics.required_connection_capacity_kw == 0.0
    assert metrics.average_transformer_loading_percent == 0.0
    assert metrics.transformer_thermal_risk_level == THERMAL_RISK_LOW
    assert metrics.maximum_feeder_loading_percent == 0.0
    assert metrics.highest_feeder_thermal_risk_level == THERMAL_RISK_LOW
    assert metrics.most_loaded_feeder_id is None
    assert metrics.peak_feeder_loading_spread_percentage_points == 0.0
    assert metrics.feeder_loading_distribution_label == "No feeders modeled"
    assert metrics.feeder_status_message == "No feeder-level load was modeled."
    assert metrics.show_feeder_detail_indicator is False
    assert metrics.peak_harmonic_risk_score == 0.0
    assert metrics.average_harmonic_risk_score == 0.0
    assert metrics.harmonic_risk_duration_hours == 0.0
    assert metrics.harmonic_risk_level == "low"
    assert metrics.harmonic_warning_indicator is False
    assert metrics.peak_current_imbalance_percent == 0.0
    assert metrics.average_current_imbalance_percent == 0.0
    assert metrics.imbalance_duration_hours == 0.0
    assert metrics.current_imbalance_risk_level == "low"
    assert metrics.imbalance_warning_indicator is False
    assert metrics.overall_pq_risk_score == 0.0
    assert metrics.overall_pq_risk_level == "low"
    assert metrics.overall_pq_warning_indicator is False
    assert metrics.power_quality_warning_count == 0
    assert metrics.power_quality_message == ""
    assert metrics.feeder_summary_rows == []
    assert metrics.transformer_total_load_kw_by_timestep == []
    assert metrics.harmonic_risk_score_by_timestep == []
    assert metrics.current_imbalance_percent_by_timestep == []
    assert metrics.overall_pq_risk_score_by_timestep == []
    assert metrics.phase_a_load_kw_by_timestep == []
    assert metrics.phase_b_load_kw_by_timestep == []
    assert metrics.phase_c_load_kw_by_timestep == []


def test_metrics_deserialization_treats_null_grid_loading_fields_as_safe_defaults():
    metrics = metrics_from_dict(
        {
            "total_daily_energy": 7500.0,
            "available_capacity": 1000.0,
            "capacity_sufficiency": True,
            "peak_load": 1000.0,
            "capacity_utilization": 100.0,
            "delivered_energy": 7500.0,
            "unmet_energy": 0.0,
            "annual_energy": 2737500.0,
            "primary_constraint_reason": None,
            "transformer_thermal_risk_level": None,
            "highest_feeder_thermal_risk_level": None,
            "most_loaded_feeder_id": None,
            "peak_feeder_loading_spread_percentage_points": None,
            "feeder_loading_distribution_label": None,
            "feeder_status_message": None,
            "show_feeder_detail_indicator": None,
            "feeder_summary_rows": None,
            "transformer_total_load_kw_by_timestep": None,
            "transformer_loading_percent_by_timestep": None,
            "transformer_overload_kw_by_timestep": None,
            "occupied_charger_count_by_timestep": None,
            "waiting_vehicle_count_by_timestep": None,
            "harmonic_risk_duration_hours": None,
            "harmonic_risk_level": None,
            "imbalance_duration_hours": None,
            "current_imbalance_risk_level": None,
            "overall_pq_risk_level": None,
            "power_quality_message": None,
            "harmonic_risk_score_by_timestep": None,
            "current_imbalance_percent_by_timestep": None,
            "overall_pq_risk_score_by_timestep": None,
            "phase_a_load_kw_by_timestep": None,
            "phase_b_load_kw_by_timestep": None,
            "phase_c_load_kw_by_timestep": None,
        }
    )

    assert metrics.primary_constraint_reason == "none"
    assert metrics.transformer_thermal_risk_level == THERMAL_RISK_LOW
    assert metrics.highest_feeder_thermal_risk_level == THERMAL_RISK_LOW
    assert metrics.most_loaded_feeder_id is None
    assert metrics.peak_feeder_loading_spread_percentage_points == 0.0
    assert metrics.feeder_loading_distribution_label == "No feeders modeled"
    assert metrics.feeder_status_message == "No feeder-level load was modeled."
    assert metrics.show_feeder_detail_indicator is False
    assert metrics.harmonic_risk_duration_hours == 0.0
    assert metrics.harmonic_risk_level == "low"
    assert metrics.imbalance_duration_hours == 0.0
    assert metrics.current_imbalance_risk_level == "low"
    assert metrics.overall_pq_risk_level == "low"
    assert metrics.power_quality_message == ""
    assert metrics.feeder_summary_rows == []
    assert metrics.transformer_total_load_kw_by_timestep == []
    assert metrics.transformer_loading_percent_by_timestep == []
    assert metrics.transformer_overload_kw_by_timestep == []
    assert metrics.occupied_charger_count_by_timestep == []
    assert metrics.waiting_vehicle_count_by_timestep == []
    assert metrics.harmonic_risk_score_by_timestep == []
    assert metrics.current_imbalance_percent_by_timestep == []
    assert metrics.overall_pq_risk_score_by_timestep == []
    assert metrics.phase_a_load_kw_by_timestep == []
    assert metrics.phase_b_load_kw_by_timestep == []
    assert metrics.phase_c_load_kw_by_timestep == []


def test_calculate_metrics_handles_legacy_simulation_result_without_power_quality_block():
    legacy_result = simulation_result_from_dict(
        {
            "daily_energy_demand": 1200.0,
            "installed_charger_capacity": 150.0,
            "available_site_capacity": 100.0,
            "load_profile": [0.0, 25.0, 100.0, 50.0],
            "delivered_energy": 175.0,
            "unmet_energy": 1025.0,
        }
    )

    metrics = calculate_metrics(legacy_result, default_scenario)

    assert metrics.harmonic_risk_score_by_timestep == []
    assert metrics.current_imbalance_percent_by_timestep == []
    assert metrics.overall_pq_risk_score_by_timestep == []
    assert metrics.phase_a_load_kw_by_timestep == []
    assert metrics.phase_b_load_kw_by_timestep == []
    assert metrics.phase_c_load_kw_by_timestep == []
    assert metrics.peak_harmonic_risk_score == 0.0
    assert metrics.average_harmonic_risk_score == 0.0
    assert metrics.harmonic_risk_duration_hours == 0.0
    assert metrics.harmonic_risk_level == POWER_QUALITY_RISK_LOW
    assert metrics.harmonic_warning_indicator is False
    assert metrics.peak_current_imbalance_percent == 0.0
    assert metrics.average_current_imbalance_percent == 0.0
    assert metrics.imbalance_duration_hours == 0.0
    assert metrics.current_imbalance_risk_level == POWER_QUALITY_RISK_LOW
    assert metrics.imbalance_warning_indicator is False
    assert metrics.overall_pq_risk_score == 0.0
    assert metrics.overall_pq_risk_level == POWER_QUALITY_RISK_LOW
    assert metrics.overall_pq_warning_indicator is False
    assert metrics.power_quality_warning_count == 0
    assert metrics.power_quality_message == (
        "Modeled overall PQ risk is low because harmonic risk and current "
        "imbalance remain below warning thresholds."
    )


def test_calculate_metrics_treats_incomplete_power_quality_series_as_safe_defaults():
    incomplete_power_quality = PowerQualityResult(
        harmonic_risk_score_by_timestep=[45.0, 50.0],
        current_imbalance_percent_by_timestep=[30.0, 35.0],
        overall_pq_risk_score_by_timestep=[40.0],
        phase_a_load_kw_by_timestep=[60.0, 55.0],
        phase_b_load_kw_by_timestep=[20.0, 25.0],
        phase_c_load_kw_by_timestep=[20.0, 20.0],
    )
    simulation_result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[100.0, 100.0],
        delivered_load_profile_kw=[100.0, 100.0],
        power_quality=incomplete_power_quality,
    )

    metrics = calculate_metrics(simulation_result, default_scenario)

    assert metrics.harmonic_risk_score_by_timestep == []
    assert metrics.current_imbalance_percent_by_timestep == []
    assert metrics.overall_pq_risk_score_by_timestep == []
    assert metrics.phase_a_load_kw_by_timestep == []
    assert metrics.phase_b_load_kw_by_timestep == []
    assert metrics.phase_c_load_kw_by_timestep == []
    assert metrics.peak_harmonic_risk_score == 0.0
    assert metrics.harmonic_risk_level == POWER_QUALITY_RISK_LOW
    assert metrics.peak_current_imbalance_percent == 0.0
    assert metrics.current_imbalance_risk_level == POWER_QUALITY_RISK_LOW
    assert metrics.overall_pq_risk_score == 0.0
    assert metrics.overall_pq_risk_level == POWER_QUALITY_RISK_LOW
    assert metrics.power_quality_warning_count == 0
    assert metrics.power_quality_message == (
        "Modeled overall PQ risk is low because harmonic risk and current "
        "imbalance remain below warning thresholds."
    )


def test_calculate_scenario_comparison_metrics_reuses_standard_metrics():
    scenario_a = default_scenario
    scenario_b = replace(default_scenario, vehicles=75, charger_count=12)
    result_a = simulate(scenario_a)
    result_b = simulate(scenario_b)

    metrics_a, metrics_b = calculate_scenario_comparison_metrics(
        scenario_a,
        result_a,
        scenario_b,
        result_b,
    )

    assert metrics_a == calculate_metrics(result_a, scenario_a)
    assert metrics_b == calculate_metrics(result_b, scenario_b)
    assert metrics_a is not metrics_b
    assert metrics_a.total_daily_energy != metrics_b.total_daily_energy


def test_calculate_scenario_comparison_metrics_uses_shared_flat_price():
    scenario_a = default_scenario
    scenario_b = replace(default_scenario, vehicles=60)
    result_a = simulate(scenario_a)
    result_b = simulate(scenario_b)

    metrics_a, metrics_b = calculate_scenario_comparison_metrics(
        scenario_a,
        result_a,
        scenario_b,
        result_b,
    )


def test_prepare_scenario_comparison_display_data_groups_metrics_for_dashboard():
    metrics_a = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=1000.0,
        capacity_utilization=80.0,
        delivered_energy=750.0,
        unmet_energy=250.0,
        average_transformer_loading_percent=92.0,
        peak_transformer_loading_percent=110.0,
        transformer_overload_indicator=True,
        transformer_overload_duration_hours=1.5,
        transformer_maximum_overload_kw=18.0,
        transformer_thermal_risk_level="high",
        maximum_feeder_loading_percent=104.0,
        feeder_overload_indicator=True,
        overloaded_feeder_count=2,
        highest_feeder_thermal_risk_level="high",
        harmonic_risk_level="moderate",
        current_imbalance_risk_level="high",
        overall_pq_risk_level="high",
        peak_harmonic_risk_score=64.0,
        harmonic_risk_duration_hours=2.0,
        peak_current_imbalance_percent=24.0,
        imbalance_duration_hours=1.0,
        overall_pq_risk_score=58.0,
        power_quality_warning_count=3,
        average_charger_utilization_percent=75.0,
        peak_charger_utilization_percent=100.0,
        average_occupied_charger_count=3.5,
        peak_occupied_charger_count=5,
        queue_present_indicator=True,
        maximum_queue_length=3,
        average_queue_length=1.5,
        queue_duration_hours=2.0,
        average_waiting_time_hours=None,
        maximum_waiting_time_hours=None,
        vehicles_waiting_count=4,
        vehicles_not_started_count=2,
        vehicles_with_unmet_energy_count=3,
        charger_capacity_vs_demand_balance=-2,
        required_charger_count=None,
        additional_chargers_required=None,
        primary_constraint_reason="mixed",
    )
    metrics_b = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=1200.0,
        capacity_utilization=100.0,
        delivered_energy=1125.0,
        unmet_energy=0.0,
        average_transformer_loading_percent=68.0,
        peak_transformer_loading_percent=84.0,
        transformer_overload_indicator=False,
        transformer_overload_duration_hours=0.0,
        transformer_maximum_overload_kw=0.0,
        transformer_thermal_risk_level="low",
        maximum_feeder_loading_percent=79.0,
        feeder_overload_indicator=False,
        overloaded_feeder_count=0,
        highest_feeder_thermal_risk_level="low",
        harmonic_risk_level="low",
        current_imbalance_risk_level="low",
        overall_pq_risk_level="low",
        peak_harmonic_risk_score=32.0,
        harmonic_risk_duration_hours=0.5,
        peak_current_imbalance_percent=14.0,
        imbalance_duration_hours=0.0,
        overall_pq_risk_score=26.0,
        power_quality_warning_count=1,
        average_charger_utilization_percent=50.0,
        peak_charger_utilization_percent=80.0,
        average_occupied_charger_count=2.0,
        peak_occupied_charger_count=3,
        queue_present_indicator=False,
        maximum_queue_length=1,
        average_queue_length=0.5,
        queue_duration_hours=0.5,
        average_waiting_time_hours=0.25,
        maximum_waiting_time_hours=0.5,
        vehicles_waiting_count=1,
        vehicles_not_started_count=0,
        vehicles_with_unmet_energy_count=1,
        charger_capacity_vs_demand_balance=0,
        required_charger_count=4,
        additional_chargers_required=1,
        primary_constraint_reason="charger_availability",
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=200.0,
        peak_load_change_percent=20.0,
        capacity_utilization_difference_percentage_points=20.0,
        capacity_utilization_change_percent=25.0,
        delivered_energy_difference_kwh=375.0,
        delivered_energy_change_percent=50.0,
        unmet_energy_difference_kwh=-250.0,
        unmet_energy_change_percent=-100.0,
        average_transformer_loading_percent_difference=-24.0,
        peak_transformer_loading_percent_difference=-26.0,
        transformer_overload_duration_hours_difference=-1.5,
        transformer_maximum_overload_kw_difference=-18.0,
        maximum_feeder_loading_percent_difference=-25.0,
        overloaded_feeder_count_difference=-2,
        peak_harmonic_risk_score_difference=-32.0,
        harmonic_risk_duration_hours_difference=-1.5,
        peak_current_imbalance_percent_difference=-10.0,
        imbalance_duration_hours_difference=-1.0,
        overall_pq_risk_score_difference=-32.0,
        power_quality_warning_count_difference=-2,
        average_occupied_charger_count_difference=-1.5,
        peak_occupied_charger_count_difference=-2,
        maximum_queue_length_difference=-2,
        average_queue_length_difference=-1.0,
        queue_duration_hours_difference=-1.5,
        average_waiting_time_hours_difference=None,
        maximum_waiting_time_hours_difference=None,
        vehicles_waiting_count_difference=-3,
        vehicles_not_started_count_difference=-2,
        vehicles_with_unmet_energy_count_difference=-2,
        charger_capacity_vs_demand_balance_difference=2,
        required_charger_count_difference=None,
        additional_chargers_required_difference=None,
    )

    display_data = prepare_scenario_comparison_display_data(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )

    assert [metric.title for metric in display_data.executive_metrics] == [
        "Peak Load",
        "Capacity Utilization",
        "Unmet Energy",
        "Maximum Queue Length",
        "Peak Transformer Loading",
        "Overall PQ Risk",
    ]
    assert [metric.outcome for metric in display_data.executive_metrics] == [
        SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF,
        SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF,
        SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT,
        SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT,
        SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT,
        SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT,
    ]
    assert [
        metric.title
        for metric in display_data.executive_metrics
        if metric.display_outcome == SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT
    ] == [
        "Unmet Energy",
        "Maximum Queue Length",
        "Peak Transformer Loading",
        "Overall PQ Risk",
    ]
    assert [
        metric.title
        for metric in display_data.executive_metrics
        if metric.display_outcome == SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF
    ] == [
        "Peak Load",
    ]
    assert [
        metric.title
        for metric in display_data.executive_metrics
        if metric.display_outcome == SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL
    ] == [
        "Capacity Utilization",
    ]
    assert [item.label for item in display_data.improvement_highlights] == [
        "Unmet energy (kWh)",
        "Charger capacity vs demand balance",
        "Overloaded feeders",
    ]
    assert display_data.improvement_highlights[0].semantic_priority_tier == 4
    assert (
        display_data.improvement_highlights[0].interpretation_reason
        == "material_numeric_change"
    )
    assert display_data.improvement_highlights[0].ranking_score == pytest.approx(100.0)
    assert display_data.improvement_highlights[1].ranking_score == pytest.approx(100.0)
    assert [item.label for item in display_data.trade_off_highlights] == [
        "Peak load (kW)",
    ]
    assert display_data.trade_off_highlights[0].semantic_priority_tier == 2
    assert (
        display_data.trade_off_highlights[0].interpretation_reason
        == "material_numeric_change"
    )
    assert [section.title for section in display_data.sections] == [
        "Energy & Performance",
        "Infrastructure",
        "Queueing",
        "Grid",
        "Power Quality",
    ]
    assert [
        section.metric_buckets.primary_metrics[0].label
        for section in display_data.sections
        if section.metric_buckets.primary_metrics
    ] == [
        "Unmet energy (kWh)",
        "Charger capacity vs demand balance",
        "Maximum queue length",
        "Peak transformer loading (%)",
        "Overall PQ risk score",
    ]
    assert [item.label for item in display_data.overview_items] == [
        "Unmet energy",
        "Maximum queue length",
        "Overall PQ risk score",
        "Peak occupied chargers",
        "Peak transformer loading",
    ]
    assert [section.section_id for section in display_data.sections] == [
        "energy_performance",
        "infrastructure",
        "queueing",
        "grid",
        "power_quality",
    ]
    assert [section.summary_tone for section in display_data.sections] == [
        SCENARIO_SECTION_SUMMARY_TRADE_OFFS,
        SCENARIO_SECTION_SUMMARY_MAJOR_CHANGES,
        SCENARIO_SECTION_SUMMARY_MAJOR_CHANGES,
        SCENARIO_SECTION_SUMMARY_MAJOR_CHANGES,
        SCENARIO_SECTION_SUMMARY_MAJOR_CHANGES,
    ]
    assert [section.impact_level for section in display_data.sections] == [
        SCENARIO_SECTION_IMPACT_MAJOR,
        SCENARIO_SECTION_IMPACT_MAJOR,
        SCENARIO_SECTION_IMPACT_MAJOR,
        SCENARIO_SECTION_IMPACT_MAJOR,
        SCENARIO_SECTION_IMPACT_MAJOR,
    ]
    assert [section.outcome_tone for section in display_data.sections] == [
        SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF,
        SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT,
        SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT,
        SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT,
        SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT,
    ]
    assert [section.visualization_intent for section in display_data.sections] == [
        SCENARIO_SECTION_VISUALIZATION_NONE,
        SCENARIO_SECTION_VISUALIZATION_SUPPORTING_WHEN_USEFUL,
        SCENARIO_SECTION_VISUALIZATION_SUPPORTING_WHEN_USEFUL,
        SCENARIO_SECTION_VISUALIZATION_SUPPORTING_WHEN_USEFUL,
        SCENARIO_SECTION_VISUALIZATION_SUPPORTING_WHEN_USEFUL,
    ]
    assert all(section.default_expanded for section in display_data.sections)

    energy_section = display_data.sections[0]
    infrastructure_section = display_data.sections[1]
    queueing_section = display_data.sections[2]
    power_quality_section = display_data.sections[4]
    assert [metric.label for metric in energy_section.numeric_metrics[:4]] == [
        "Unmet energy (kWh)",
        "Peak load (kW)",
        "Delivered energy (kWh)",
        "Capacity utilization (%)",
    ]
    assert [metric.label for metric in queueing_section.numeric_metrics[:4]] == [
        "Maximum queue length",
        "Vehicles not started",
        "Vehicles with unmet energy",
        "Vehicles waiting",
    ]
    assert [metric.label for metric in power_quality_section.numeric_metrics[:3]] == [
        "Overall PQ risk score",
        "PQ warning count",
        "Peak harmonic risk score",
    ]
    assert energy_section.summary_label == "Mixed"
    assert energy_section.summary_text == (
        "Scenario B improves some energy & performance outcomes but introduces "
        "trade-offs, led by Unmet energy (kWh)."
    )
    assert [metric.label for metric in energy_section.metric_buckets.primary_metrics] == [
        "Unmet energy (kWh)",
        "Peak load (kW)",
        "Delivered energy (kWh)",
    ]
    assert [metric.label for metric in energy_section.metric_buckets.secondary_metrics] == [
        "Capacity utilization (%)",
    ]
    assert energy_section.metric_buckets.unchanged_metrics == ()
    assert [metric.label for metric in infrastructure_section.metric_buckets.primary_metrics] == [
        "Charger capacity vs demand balance",
        "Average occupied chargers",
        "Peak occupied chargers",
    ]
    assert [metric.label for metric in infrastructure_section.metric_buckets.secondary_metrics] == [
        "Required charger count",
        "Additional chargers required",
        "Peak charger utilization (%)",
        "Average charger utilization (%)",
        "Primary constraint reason",
    ]
    assert infrastructure_section.metric_buckets.unchanged_metrics == ()
    assert energy_section.impact_level == SCENARIO_SECTION_IMPACT_MAJOR
    assert energy_section.outcome_tone == SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF
    assert energy_section.visualization_intent == SCENARIO_SECTION_VISUALIZATION_NONE
    required_charger_metric = next(
        metric
        for metric in infrastructure_section.numeric_metrics
        if metric.label == "Required charger count"
    )
    peak_utilization_metric = next(
        metric
        for metric in infrastructure_section.numeric_metrics
        if metric.label == "Peak charger utilization (%)"
    )
    primary_constraint_metric = infrastructure_section.status_metrics[0]

    assert (
        required_charger_metric.scenario_value_state
        == SCENARIO_VALUE_OPTIONAL_NOT_APPLICABLE
    )
    assert required_charger_metric.metric_id == "required_charger_count"
    assert required_charger_metric.change_mode == SCENARIO_CHANGE_OPTIONAL_DELTA
    assert required_charger_metric.absolute_materiality_threshold == pytest.approx(0.5)
    assert required_charger_metric.semantic_priority_tier > 0
    assert peak_utilization_metric.change_mode == SCENARIO_CHANGE_OPTIONAL_DELTA
    assert peak_utilization_metric.change_value == pytest.approx(-20.0)
    assert primary_constraint_metric.label == "Primary constraint reason"
    assert primary_constraint_metric.metric_id == "primary_constraint_reason"
    assert primary_constraint_metric.change_mode == SCENARIO_CHANGE_NONE
    assert primary_constraint_metric.always_meaningful_status_change is True


def test_prepare_scenario_comparison_display_data_filters_exact_zero_highlights():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=0,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=0,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=0.0,
        peak_load_change_percent=0.0,
        capacity_utilization_difference_percentage_points=0.0,
        capacity_utilization_change_percent=0.0,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=0.0,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=0.0,
    )

    display_data = prepare_scenario_comparison_display_data(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )

    assert display_data.improvement_highlights == ()
    assert display_data.trade_off_highlights == ()
    assert display_data.overview_items == ()
    assert [metric.outcome for metric in display_data.executive_metrics] == [
        SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL,
        SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL,
        SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL,
        SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL,
        SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL,
        SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL,
    ]
    assert [
        metric.title
        for metric in display_data.executive_metrics
        if metric.display_outcome == SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT
    ] == []
    assert [
        metric.title
        for metric in display_data.executive_metrics
        if metric.display_outcome == SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF
    ] == []
    assert [metric.title for metric in display_data.executive_metrics] == [
        "Peak Load",
        "Capacity Utilization",
        "Unmet Energy",
        "Maximum Queue Length",
        "Peak Transformer Loading",
        "Overall PQ Risk",
    ]
    assert all(
        section.summary_tone == SCENARIO_SECTION_SUMMARY_LITTLE_NO_CHANGE
        for section in display_data.sections
    )
    assert all(
        section.impact_level == SCENARIO_SECTION_IMPACT_NONE
        for section in display_data.sections
    )
    assert all(
        section.outcome_tone == SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL
        for section in display_data.sections
    )
    assert all(
        section.summary_text.startswith("No material differences detected in ")
        for section in display_data.sections
    )
    assert all(
        not section.metric_buckets.primary_metrics
        and not section.metric_buckets.secondary_metrics
        for section in display_data.sections
    )
    assert all(
        not section.metric_buckets.primary_metrics
        for section in display_data.sections
    )


def test_prepare_scenario_comparison_display_data_computes_defined_infrastructure_recommendation_deltas():
    metrics_a = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        charger_capacity_vs_demand_balance=-40,
        required_charger_count=50,
        additional_chargers_required=40,
        primary_constraint_reason="charger_availability",
    )
    metrics_b = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        charger_capacity_vs_demand_balance=-80,
        required_charger_count=90,
        additional_chargers_required=80,
        primary_constraint_reason="charger_availability",
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=0.0,
        peak_load_change_percent=None,
        capacity_utilization_difference_percentage_points=0.0,
        capacity_utilization_change_percent=None,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=None,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=None,
        charger_capacity_vs_demand_balance_difference=-40,
        required_charger_count_difference=None,
        additional_chargers_required_difference=None,
    )

    display_data = prepare_scenario_comparison_display_data(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )

    infrastructure_section = next(
        section
        for section in display_data.sections
        if section.section_id == "infrastructure"
    )
    required_metric = next(
        metric
        for metric in infrastructure_section.numeric_metrics
        if metric.metric_id == "required_charger_count"
    )
    additional_metric = next(
        metric
        for metric in infrastructure_section.numeric_metrics
        if metric.metric_id == "additional_chargers_required"
    )

    assert required_metric.change_value == 40
    assert additional_metric.change_value == 40
    assert [metric.metric_id for metric in infrastructure_section.metric_buckets.primary_metrics] == [
        "charger_capacity_vs_demand_balance",
        "required_charger_count",
        "additional_chargers_required",
    ]


def test_prepare_scenario_comparison_display_data_filters_tiny_nonzero_trade_off():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=0,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.04,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=0,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=0.04,
        peak_load_change_percent=0.04,
        capacity_utilization_difference_percentage_points=0.0,
        capacity_utilization_change_percent=0.0,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=0.0,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=0.0,
    )

    display_data = prepare_scenario_comparison_display_data(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )

    assert display_data.trade_off_highlights == ()
    assert display_data.overview_items == ()
    assert all(
        metric.display_outcome != SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF
        for metric in display_data.executive_metrics
    )
    assert display_data.sections[0].summary_tone == SCENARIO_SECTION_SUMMARY_LITTLE_NO_CHANGE
    assert display_data.sections[0].metric_buckets.primary_metrics == ()


def test_prepare_scenario_comparison_display_data_preserves_shared_executive_outcomes():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=5,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.04,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=4,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=30.0,
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=0.04,
        peak_load_change_percent=0.04,
        capacity_utilization_difference_percentage_points=0.0,
        capacity_utilization_change_percent=0.0,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=0.0,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=0.0,
        peak_transformer_loading_percent_difference=0.0,
        overall_pq_risk_score_difference=10.0,
        maximum_queue_length_difference=-1,
    )

    display_data = prepare_scenario_comparison_display_data(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )
    outcomes = {
        metric.metric_id: metric.display_outcome
        for metric in display_data.executive_metrics
    }

    assert outcomes["peak_load"] == SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL
    assert outcomes["maximum_queue_length"] == SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT
    assert outcomes["overall_pq_risk"] == SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF


def test_prepare_scenario_comparison_display_data_filters_rounding_to_zero_percentage_point_change():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=0,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=80.04,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=0,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=0.0,
        peak_load_change_percent=0.0,
        capacity_utilization_difference_percentage_points=0.04,
        capacity_utilization_change_percent=0.05,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=0.0,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=0.0,
    )

    display_data = prepare_scenario_comparison_display_data(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )

    capacity_metric = next(
        metric
        for metric in display_data.sections[0].numeric_metrics
        if metric.metric_id == "capacity_utilization"
    )

    assert capacity_metric.absolute_materiality_threshold == pytest.approx(0.05)
    assert capacity_metric.relative_materiality_threshold == pytest.approx(0.1)
    assert display_data.trade_off_highlights == ()
    assert display_data.sections[0].summary_tone == SCENARIO_SECTION_SUMMARY_LITTLE_NO_CHANGE


def test_prepare_scenario_comparison_display_data_keeps_section_minimal_when_only_neutral_change_exists():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=0,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=100.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=0,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=0.0,
        peak_load_change_percent=0.0,
        capacity_utilization_difference_percentage_points=20.0,
        capacity_utilization_change_percent=25.0,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=0.0,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=0.0,
    )

    display_data = prepare_scenario_comparison_display_data(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )

    energy_section = display_data.sections[0]

    assert energy_section.summary_tone == SCENARIO_SECTION_SUMMARY_LITTLE_NO_CHANGE
    assert energy_section.summary_label == "Minimal change"
    assert energy_section.default_expanded is False
    assert energy_section.metric_buckets.primary_metrics == ()


def test_prepare_scenario_comparison_display_data_expands_section_for_single_meaningful_change_without_cutoff():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=1000.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=100,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=1000.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=99,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=0.0,
        peak_load_change_percent=0.0,
        capacity_utilization_difference_percentage_points=0.0,
        capacity_utilization_change_percent=0.0,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=0.0,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=0.0,
        maximum_queue_length_difference=-1,
    )

    display_data = prepare_scenario_comparison_display_data(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )

    queueing_section = display_data.sections[2]

    assert queueing_section.summary_tone == SCENARIO_SECTION_SUMMARY_MAJOR_CHANGES
    assert queueing_section.summary_label == "Improvement"
    assert queueing_section.impact_level == SCENARIO_SECTION_IMPACT_MINOR
    assert queueing_section.outcome_tone == SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT
    assert queueing_section.default_expanded is True
    assert queueing_section.signal_score == pytest.approx(1.0)
    assert queueing_section.summary_text == (
        "Scenario B shows a limited improvement signal in queueing, led by "
        "Maximum queue length."
    )
    assert [metric.label for metric in queueing_section.metric_buckets.primary_metrics] == [
        "Maximum queue length",
    ]
    assert queueing_section.metric_buckets.primary_metrics[0].label == "Maximum queue length"


def test_prepare_scenario_comparison_display_data_classifies_major_minor_and_none_impact_levels():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=100,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=150.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=99,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=50.0,
        peak_load_change_percent=50.0,
        capacity_utilization_difference_percentage_points=0.0,
        capacity_utilization_change_percent=0.0,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=0.0,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=0.0,
        maximum_queue_length_difference=-1,
    )

    display_data = prepare_scenario_comparison_display_data(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )

    assert display_data.sections[0].impact_level == SCENARIO_SECTION_IMPACT_MAJOR
    assert display_data.sections[0].outcome_tone == SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF
    assert display_data.sections[2].impact_level == SCENARIO_SECTION_IMPACT_MINOR
    assert display_data.sections[2].outcome_tone == SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT
    assert display_data.sections[3].impact_level == SCENARIO_SECTION_IMPACT_NONE
    assert display_data.sections[3].outcome_tone == SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL


def test_prepare_scenario_comparison_display_data_groups_unchanged_rows_into_unchanged_bucket():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        average_occupied_charger_count=3.0,
        peak_occupied_charger_count=5,
        queue_present_indicator=True,
        maximum_queue_length=3,
        average_queue_length=1.5,
        queue_duration_hours=2.0,
        vehicles_waiting_count=4,
        vehicles_not_started_count=1,
        vehicles_with_unmet_energy_count=1,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        average_occupied_charger_count=3.0,
        peak_occupied_charger_count=5,
        queue_present_indicator=True,
        maximum_queue_length=1,
        average_queue_length=1.5,
        queue_duration_hours=2.0,
        vehicles_waiting_count=4,
        vehicles_not_started_count=1,
        vehicles_with_unmet_energy_count=1,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=0.0,
        peak_load_change_percent=0.0,
        capacity_utilization_difference_percentage_points=0.0,
        capacity_utilization_change_percent=0.0,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=0.0,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=0.0,
        maximum_queue_length_difference=-2,
        average_queue_length_difference=0.0,
        queue_duration_hours_difference=0.0,
        vehicles_waiting_count_difference=0,
        vehicles_not_started_count_difference=0,
        vehicles_with_unmet_energy_count_difference=0,
    )

    display_data = prepare_scenario_comparison_display_data(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )

    queueing_section = display_data.sections[2]

    assert [metric.label for metric in queueing_section.metric_buckets.primary_metrics] == [
        "Maximum queue length",
    ]
    assert queueing_section.metric_buckets.secondary_metrics == ()
    assert [metric.label for metric in queueing_section.metric_buckets.unchanged_metrics] == [
        "Vehicles not started",
        "Vehicles with unmet energy",
        "Vehicles waiting",
        "Average queue length",
        "Queue duration (h)",
        "Average waiting time (h)",
        "Maximum waiting time (h)",
        "Queue present",
    ]


def test_prepare_scenario_comparison_display_data_keeps_no_difference_cards_compact():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=0,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=0,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=0.0,
        peak_load_change_percent=0.0,
        capacity_utilization_difference_percentage_points=0.0,
        capacity_utilization_change_percent=0.0,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=0.0,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=0.0,
    )

    display_data = prepare_scenario_comparison_display_data(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )

    assert len(display_data.sections) == 5
    assert [section.summary_label for section in display_data.sections] == [
        "Minimal change",
        "Minimal change",
        "Minimal change",
        "Minimal change",
        "Minimal change",
    ]
    assert all(section.default_expanded is False for section in display_data.sections)
    assert all(
        section.summary_text.startswith("No material differences detected in ")
        for section in display_data.sections
    )
    assert all(
        section.metric_buckets.primary_metrics == ()
        for section in display_data.sections
    )
    assert all(section.metric_buckets.primary_metrics == () for section in display_data.sections)
    assert all(section.metric_buckets.secondary_metrics == () for section in display_data.sections)
    assert all(section.metric_buckets.unchanged_metrics for section in display_data.sections)


def test_prepare_scenario_comparison_display_data_sets_section_visualization_intents():
    metrics = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=0,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=0.0,
        peak_load_change_percent=0.0,
        capacity_utilization_difference_percentage_points=0.0,
        capacity_utilization_change_percent=0.0,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=0.0,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=0.0,
    )

    display_data = prepare_scenario_comparison_display_data(
        metrics,
        metrics,
        comparison_metrics,
    )

    assert {
        section.section_id: section.visualization_intent
        for section in display_data.sections
    } == {
        "energy_performance": SCENARIO_SECTION_VISUALIZATION_NONE,
        "infrastructure": SCENARIO_SECTION_VISUALIZATION_SUPPORTING_WHEN_USEFUL,
        "queueing": SCENARIO_SECTION_VISUALIZATION_SUPPORTING_WHEN_USEFUL,
        "grid": SCENARIO_SECTION_VISUALIZATION_SUPPORTING_WHEN_USEFUL,
        "power_quality": SCENARIO_SECTION_VISUALIZATION_SUPPORTING_WHEN_USEFUL,
    }
    assert {
        section.section_id: section.visualization_intent
        for section in display_data.sections
    } == {
        "energy_performance": SCENARIO_SECTION_VISUALIZATION_NONE,
        "infrastructure": SCENARIO_SECTION_VISUALIZATION_SUPPORTING_WHEN_USEFUL,
        "queueing": SCENARIO_SECTION_VISUALIZATION_SUPPORTING_WHEN_USEFUL,
        "grid": SCENARIO_SECTION_VISUALIZATION_SUPPORTING_WHEN_USEFUL,
        "power_quality": SCENARIO_SECTION_VISUALIZATION_SUPPORTING_WHEN_USEFUL,
    }


def test_prepare_scenario_comparison_display_data_prioritizes_meaningful_status_highlights():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=1,
        queue_present_indicator=True,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.1,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=0,
        queue_present_indicator=False,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=0.1,
        peak_load_change_percent=0.1,
        capacity_utilization_difference_percentage_points=0.0,
        capacity_utilization_change_percent=0.0,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=0.0,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=0.0,
        maximum_queue_length_difference=-1,
        power_quality_warning_count_difference=0,
    )

    display_data = prepare_scenario_comparison_display_data(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )

    assert [item.label for item in display_data.improvement_highlights][:2] == [
        "Maximum queue length",
        "Queue present",
    ]
    queue_present_highlight = next(
        item
        for item in display_data.improvement_highlights
        if item.label == "Queue present"
    )
    assert queue_present_highlight.is_categorical is True
    assert queue_present_highlight.semantic_priority_tier == 4
    assert queue_present_highlight.ranking_score == pytest.approx(30.0)
    assert queue_present_highlight.interpretation_reason == "meaningful_status_change"


def test_prepare_scenario_comparison_display_data_treats_overload_and_risk_level_changes_as_meaningful():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=0,
        peak_transformer_loading_percent=90.0,
        transformer_overload_indicator=True,
        transformer_thermal_risk_level="high",
        overall_pq_risk_score=60.0,
        overall_pq_risk_level="high",
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        maximum_queue_length=0,
        peak_transformer_loading_percent=90.0,
        transformer_overload_indicator=False,
        transformer_thermal_risk_level="low",
        overall_pq_risk_score=60.0,
        overall_pq_risk_level="low",
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=0.0,
        peak_load_change_percent=0.0,
        capacity_utilization_difference_percentage_points=0.0,
        capacity_utilization_change_percent=0.0,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=0.0,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=0.0,
        overall_pq_risk_score_difference=0.0,
        power_quality_warning_count_difference=0,
    )

    display_data = prepare_scenario_comparison_display_data(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )

    assert [item.label for item in display_data.improvement_highlights] == [
        "Transformer overload",
        "Overall PQ risk level",
        "Transformer thermal risk",
    ]
    assert display_data.trade_off_highlights == ()

    transformer_overload_highlight = display_data.improvement_highlights[0]
    overall_risk_highlight = display_data.improvement_highlights[1]

    assert transformer_overload_highlight.is_categorical is True
    assert transformer_overload_highlight.semantic_priority_tier == 4
    assert transformer_overload_highlight.ranking_score == pytest.approx(30.0)
    assert (
        transformer_overload_highlight.interpretation_reason
        == "meaningful_status_change"
    )
    assert overall_risk_highlight.semantic_priority_tier == 3
    assert overall_risk_highlight.ranking_score == pytest.approx(24.0)
    assert overall_risk_highlight.interpretation_reason == "meaningful_status_change"
    assert display_data.sections[3].summary_tone == SCENARIO_SECTION_SUMMARY_MAJOR_CHANGES
    assert display_data.sections[4].summary_tone == SCENARIO_SECTION_SUMMARY_MAJOR_CHANGES
    assert display_data.sections[3].metric_buckets.primary_metrics[0].label == "Transformer overload"
    assert display_data.sections[4].metric_buckets.primary_metrics[0].label == "Overall PQ risk level"


def test_prepare_scenario_comparison_display_data_ranks_equal_signal_improvements_deterministically():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        peak_occupied_charger_count=2,
        maximum_queue_length=2,
        vehicles_not_started_count=2,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        peak_occupied_charger_count=1,
        maximum_queue_length=1,
        vehicles_not_started_count=1,
        peak_transformer_loading_percent=75.0,
        overall_pq_risk_score=20.0,
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=0.0,
        peak_load_change_percent=0.0,
        capacity_utilization_difference_percentage_points=0.0,
        capacity_utilization_change_percent=0.0,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=0.0,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=0.0,
        peak_occupied_charger_count_difference=-1,
        maximum_queue_length_difference=-1,
        vehicles_not_started_count_difference=-1,
        power_quality_warning_count_difference=0,
    )

    display_data = prepare_scenario_comparison_display_data(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )

    assert [item.label for item in display_data.improvement_highlights] == [
        "Maximum queue length",
        "Vehicles not started",
        "Peak occupied chargers",
    ]
    assert [item.ranking_score for item in display_data.improvement_highlights] == [
        pytest.approx(50.0),
        pytest.approx(50.0),
        pytest.approx(50.0),
    ]
