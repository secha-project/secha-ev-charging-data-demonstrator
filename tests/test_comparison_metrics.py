import json
from dataclasses import FrozenInstanceError, asdict, fields
from datetime import time

import pytest

from metrics import (
    ComparisonMetrics,
    FeederSummaryMetrics,
    Metrics,
    ScenarioComparisonMetrics,
    calculate_comparison_metrics,
    calculate_metrics,
    calculate_scenario_difference_metrics,
    scenario_comparison_metrics_from_dict,
    scenario_comparison_metrics_to_dict,
)
from dataclasses import replace

from scenarios import (
    ArrivalProfileShape,
    ChargingStrategy,
    DepartureMode,
    PowerQualityPhaseAllocationMethod,
    Scenario,
    create_internal_scenario,
    default_scenario,
)
from simulation import SimulationResult, simulate_strategy_comparison


def _build_reference_power_quality_strategy_scenario() -> Scenario:
    return create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        single_phase_charger_share_percent=100.0,
        charger_harmonic_factor=1.2,
        power_quality_phase_allocation_method=(
            PowerQualityPhaseAllocationMethod.FRONT_LOADED_PHASE_A
        ),
    )


def test_comparison_metrics_contains_strategy_comparison_kpis():
    assert [field.name for field in fields(ComparisonMetrics)] == [
        "peak_reduction",
        "relative_peak_reduction",
        "capacity_utilization_difference",
        "unmet_energy_difference",
        "peak_capacity_margin_improvement_kw",
        "grid_capacity_status",
        "uncontrolled_required_connection_capacity_kw",
        "smart_required_connection_capacity_kw",
        "required_connection_capacity_difference_kw",
        "connection_capacity_avoided_by_smart_kw",
        "uncontrolled_recommended_connection_capacity_kw",
        "smart_recommended_connection_capacity_kw",
        "recommended_connection_capacity_difference_kw",
        "recommended_connection_capacity_avoided_by_smart_kw",
        "uncontrolled_connection_upgrade_required",
        "smart_connection_upgrade_required",
        "uncontrolled_connection_capacity_adequate_indicator",
        "smart_connection_capacity_adequate_indicator",
        "uncontrolled_connection_capacity_recommendation_reason",
        "smart_connection_capacity_recommendation_reason",
        "uncontrolled_capacity_exceedance_duration_hours",
        "smart_capacity_exceedance_duration_hours",
        "exceedance_duration_reduction_hours",
        "uncontrolled_average_transformer_loading_percent",
        "smart_average_transformer_loading_percent",
        "average_transformer_loading_percent_difference",
        "uncontrolled_peak_transformer_loading_percent",
        "smart_peak_transformer_loading_percent",
        "peak_transformer_loading_percent_difference",
        "uncontrolled_transformer_overload_indicator",
        "smart_transformer_overload_indicator",
        "uncontrolled_transformer_overload_duration_hours",
        "smart_transformer_overload_duration_hours",
        "transformer_overload_duration_difference_hours",
        "uncontrolled_transformer_maximum_overload_kw",
        "smart_transformer_maximum_overload_kw",
        "transformer_maximum_overload_difference_kw",
        "uncontrolled_transformer_thermal_risk_level",
        "smart_transformer_thermal_risk_level",
        "uncontrolled_maximum_feeder_loading_percent",
        "smart_maximum_feeder_loading_percent",
        "maximum_feeder_loading_percent_difference",
        "uncontrolled_feeder_overload_indicator",
        "smart_feeder_overload_indicator",
        "uncontrolled_overloaded_feeder_count",
        "smart_overloaded_feeder_count",
        "overloaded_feeder_count_difference",
        "uncontrolled_highest_feeder_thermal_risk_level",
        "smart_highest_feeder_thermal_risk_level",
        "uncontrolled_peak_harmonic_risk_score",
        "smart_peak_harmonic_risk_score",
        "peak_harmonic_risk_score_difference",
        "uncontrolled_average_harmonic_risk_score",
        "smart_average_harmonic_risk_score",
        "average_harmonic_risk_score_difference",
        "uncontrolled_harmonic_risk_duration_hours",
        "smart_harmonic_risk_duration_hours",
        "harmonic_risk_duration_difference_hours",
        "uncontrolled_harmonic_risk_level",
        "smart_harmonic_risk_level",
        "uncontrolled_harmonic_warning_indicator",
        "smart_harmonic_warning_indicator",
        "uncontrolled_peak_current_imbalance_percent",
        "smart_peak_current_imbalance_percent",
        "peak_current_imbalance_percent_difference",
        "uncontrolled_average_current_imbalance_percent",
        "smart_average_current_imbalance_percent",
        "average_current_imbalance_percent_difference",
        "uncontrolled_imbalance_duration_hours",
        "smart_imbalance_duration_hours",
        "imbalance_duration_difference_hours",
        "uncontrolled_current_imbalance_risk_level",
        "smart_current_imbalance_risk_level",
        "uncontrolled_imbalance_warning_indicator",
        "smart_imbalance_warning_indicator",
        "uncontrolled_overall_pq_risk_score",
        "smart_overall_pq_risk_score",
        "overall_pq_risk_score_difference",
        "uncontrolled_overall_pq_risk_level",
        "smart_overall_pq_risk_level",
        "uncontrolled_overall_pq_warning_indicator",
        "smart_overall_pq_warning_indicator",
        "uncontrolled_power_quality_warning_count",
        "smart_power_quality_warning_count",
        "power_quality_warning_count_difference",
        "uncontrolled_power_quality_message",
        "smart_power_quality_message",
        "uncontrolled_average_charger_utilization_percent",
        "smart_average_charger_utilization_percent",
        "uncontrolled_peak_charger_utilization_percent",
        "smart_peak_charger_utilization_percent",
        "peak_charger_utilization_percent_difference",
        "uncontrolled_average_occupied_charger_count",
        "smart_average_occupied_charger_count",
        "average_occupied_charger_count_difference",
        "uncontrolled_peak_occupied_charger_count",
        "smart_peak_occupied_charger_count",
        "peak_occupied_charger_count_difference",
        "uncontrolled_charger_shortage_indicator",
        "smart_charger_shortage_indicator",
        "uncontrolled_queue_present_indicator",
        "smart_queue_present_indicator",
        "uncontrolled_maximum_queue_length",
        "smart_maximum_queue_length",
        "maximum_queue_length_difference",
        "uncontrolled_average_queue_length",
        "smart_average_queue_length",
        "average_queue_length_difference",
        "uncontrolled_queue_duration_hours",
        "smart_queue_duration_hours",
        "queue_duration_difference_hours",
        "uncontrolled_average_waiting_time_hours",
        "smart_average_waiting_time_hours",
        "average_waiting_time_difference_hours",
        "uncontrolled_maximum_waiting_time_hours",
        "smart_maximum_waiting_time_hours",
        "maximum_waiting_time_difference_hours",
        "uncontrolled_vehicles_waiting_count",
        "smart_vehicles_waiting_count",
        "vehicles_waiting_count_difference",
        "uncontrolled_vehicles_not_started_count",
        "smart_vehicles_not_started_count",
        "vehicles_not_started_count_difference",
        "uncontrolled_vehicles_with_unmet_energy_count",
        "smart_vehicles_with_unmet_energy_count",
        "vehicles_with_unmet_energy_count_difference",
        "uncontrolled_charger_capacity_vs_demand_balance",
        "smart_charger_capacity_vs_demand_balance",
        "charger_capacity_vs_demand_balance_difference",
        "uncontrolled_required_charger_count",
        "smart_required_charger_count",
        "required_charger_count_difference",
        "uncontrolled_additional_chargers_required",
        "smart_additional_chargers_required",
        "additional_chargers_required_difference",
        "uncontrolled_primary_constraint_reason",
        "smart_primary_constraint_reason",
        "charger_expansion_avoided_by_smart",
        "connection_upgrade_avoided_by_smart",
        "service_rule_resolved_by_smart",
        "service_rule_worsened_by_smart",
        "infrastructure_recommendation_changed_by_smart",
        "primary_constraint_shifted_by_smart",
        "primary_constraint_shift_summary",
        "service_impact_summary",
        "infrastructure_impact_summary",
        "uncontrolled_feeder_summary_rows",
        "smart_feeder_summary_rows",
        "uncontrolled_transformer_total_load_kw_by_timestep",
        "smart_transformer_total_load_kw_by_timestep",
        "uncontrolled_transformer_loading_percent_by_timestep",
        "smart_transformer_loading_percent_by_timestep",
        "uncontrolled_transformer_overload_kw_by_timestep",
        "smart_transformer_overload_kw_by_timestep",
        "uncontrolled_occupied_charger_count_by_timestep",
        "smart_occupied_charger_count_by_timestep",
        "uncontrolled_waiting_vehicle_count_by_timestep",
        "smart_waiting_vehicle_count_by_timestep",
        "uncontrolled_harmonic_risk_score_by_timestep",
        "smart_harmonic_risk_score_by_timestep",
        "uncontrolled_current_imbalance_percent_by_timestep",
        "smart_current_imbalance_percent_by_timestep",
        "uncontrolled_overall_pq_risk_score_by_timestep",
        "smart_overall_pq_risk_score_by_timestep",
        "uncontrolled_phase_a_load_kw_by_timestep",
        "smart_phase_a_load_kw_by_timestep",
        "uncontrolled_phase_b_load_kw_by_timestep",
        "smart_phase_b_load_kw_by_timestep",
        "uncontrolled_phase_c_load_kw_by_timestep",
        "smart_phase_c_load_kw_by_timestep",
    ]


def test_calculate_comparison_metrics_uses_existing_metrics_values():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=400.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        peak_capacity_margin_kw=-75.0,
        connection_capacity_exceeded=True,
        configured_connection_capacity_kw=400.0,
        required_connection_capacity_kw=500.0,
        recommended_connection_capacity_kw=550.0,
        capacity_exceedance_duration_hours=3.0,
        average_transformer_loading_percent=82.5,
        peak_transformer_loading_percent=110.0,
        transformer_overload_indicator=True,
        transformer_overload_duration_hours=2.0,
        transformer_maximum_overload_kw=25.0,
        transformer_thermal_risk_level="high",
        maximum_feeder_loading_percent=105.0,
        feeder_overload_indicator=True,
        overloaded_feeder_count=2,
        highest_feeder_thermal_risk_level="high",
        peak_harmonic_risk_score=78.0,
        average_harmonic_risk_score=52.0,
        harmonic_risk_duration_hours=3.0,
        harmonic_risk_level="high",
        harmonic_warning_indicator=True,
        peak_current_imbalance_percent=42.0,
        average_current_imbalance_percent=28.0,
        imbalance_duration_hours=1.5,
        current_imbalance_risk_level="moderate",
        imbalance_warning_indicator=True,
        overall_pq_risk_score=64.0,
        overall_pq_risk_level="high",
        overall_pq_warning_indicator=True,
        power_quality_warning_count=3,
        power_quality_message=(
            "Modeled overall PQ risk is high because harmonic risk is high "
            "and dominates the weighted demonstrator score."
        ),
        average_occupied_charger_count=2.5,
        peak_occupied_charger_count=4,
        maximum_queue_length=3,
        average_queue_length=1.5,
        queue_duration_hours=2.0,
        average_waiting_time_hours=0.75,
        maximum_waiting_time_hours=1.5,
        vehicles_waiting_count=4,
        vehicles_not_started_count=1,
        vehicles_with_unmet_energy_count=2,
        charger_capacity_vs_demand_balance=-2,
        required_charger_count=6,
        additional_chargers_required=2,
        primary_constraint_reason="charger_availability",
        feeder_summary_rows=[
            FeederSummaryMetrics(
                feeder_id="feeder_1",
                charger_count=2,
                peak_loading_percent=105.0,
                overload_indicator=True,
                overload_duration_hours=1.0,
                maximum_overload_kw=5.0,
                thermal_risk_level="high",
            )
        ],
        transformer_total_load_kw_by_timestep=[360.0, 400.0, 325.0],
        transformer_loading_percent_by_timestep=[90.0, 100.0, 81.25],
        transformer_overload_kw_by_timestep=[0.0, 25.0, 0.0],
        occupied_charger_count_by_timestep=[1, 2, 3],
        waiting_vehicle_count_by_timestep=[0, 1, 2],
        harmonic_risk_score_by_timestep=[40.0, 78.0, 38.0],
        current_imbalance_percent_by_timestep=[18.0, 42.0, 24.0],
        overall_pq_risk_score_by_timestep=[31.0, 64.0, 32.4],
        phase_a_load_kw_by_timestep=[140.0, 160.0, 120.0],
        phase_b_load_kw_by_timestep=[110.0, 120.0, 105.0],
        phase_c_load_kw_by_timestep=[110.0, 120.0, 100.0],
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=250.0,
        capacity_utilization=50.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        peak_capacity_margin_kw=125.0,
        connection_capacity_exceeded=False,
        configured_connection_capacity_kw=400.0,
        required_connection_capacity_kw=350.0,
        recommended_connection_capacity_kw=385.0,
        capacity_exceedance_duration_hours=1.0,
        average_transformer_loading_percent=60.0,
        peak_transformer_loading_percent=85.0,
        transformer_overload_indicator=False,
        transformer_overload_duration_hours=0.0,
        transformer_maximum_overload_kw=0.0,
        transformer_thermal_risk_level="low",
        maximum_feeder_loading_percent=70.0,
        feeder_overload_indicator=False,
        overloaded_feeder_count=0,
        highest_feeder_thermal_risk_level="low",
        peak_harmonic_risk_score=44.0,
        average_harmonic_risk_score=30.0,
        harmonic_risk_duration_hours=1.0,
        harmonic_risk_level="moderate",
        harmonic_warning_indicator=True,
        peak_current_imbalance_percent=20.0,
        average_current_imbalance_percent=12.0,
        imbalance_duration_hours=0.0,
        current_imbalance_risk_level="low",
        imbalance_warning_indicator=False,
        overall_pq_risk_score=34.0,
        overall_pq_risk_level="moderate",
        overall_pq_warning_indicator=True,
        power_quality_warning_count=2,
        power_quality_message=(
            "Modeled overall PQ risk is moderate because harmonic risk is "
            "moderate and dominates the weighted demonstrator score."
        ),
        average_occupied_charger_count=1.5,
        peak_occupied_charger_count=3,
        maximum_queue_length=1,
        average_queue_length=0.5,
        queue_duration_hours=1.0,
        average_waiting_time_hours=0.25,
        maximum_waiting_time_hours=0.75,
        vehicles_waiting_count=2,
        vehicles_not_started_count=0,
        vehicles_with_unmet_energy_count=0,
        charger_capacity_vs_demand_balance=0,
        required_charger_count=4,
        additional_chargers_required=0,
        primary_constraint_reason="none",
        feeder_summary_rows=[
            FeederSummaryMetrics(
                feeder_id="feeder_1",
                charger_count=2,
                peak_loading_percent=70.0,
                overload_indicator=False,
                overload_duration_hours=0.0,
                maximum_overload_kw=0.0,
                thermal_risk_level="low",
            )
        ],
        transformer_total_load_kw_by_timestep=[250.0, 240.0, 200.0],
        transformer_loading_percent_by_timestep=[62.5, 60.0, 50.0],
        transformer_overload_kw_by_timestep=[0.0, 0.0, 0.0],
        occupied_charger_count_by_timestep=[1, 1, 2],
        waiting_vehicle_count_by_timestep=[0, 0, 1],
        harmonic_risk_score_by_timestep=[24.0, 44.0, 22.0],
        current_imbalance_percent_by_timestep=[8.0, 20.0, 8.0],
        overall_pq_risk_score_by_timestep=[17.6, 34.4, 16.4],
        phase_a_load_kw_by_timestep=[90.0, 95.0, 70.0],
        phase_b_load_kw_by_timestep=[80.0, 80.0, 65.0],
        phase_c_load_kw_by_timestep=[80.0, 65.0, 65.0],
    )

    comparison = calculate_comparison_metrics(uncontrolled, smart)

    assert comparison.peak_reduction == 150.0
    assert comparison.relative_peak_reduction == 37.5
    assert comparison.capacity_utilization_difference == 30.0
    assert comparison.unmet_energy_difference == 0.0
    assert comparison.peak_capacity_margin_improvement_kw == 200.0
    assert not hasattr(comparison, "energy_cost_savings")
    assert not hasattr(comparison, "flat_price_cost_message")
    assert comparison.grid_capacity_status == "Constraint resolved"
    assert comparison.uncontrolled_required_connection_capacity_kw == 500.0
    assert comparison.smart_required_connection_capacity_kw == 350.0
    assert comparison.required_connection_capacity_difference_kw == 150.0
    assert comparison.connection_capacity_avoided_by_smart_kw == 150.0
    assert comparison.uncontrolled_recommended_connection_capacity_kw == 550.0
    assert comparison.smart_recommended_connection_capacity_kw == 385.0
    assert comparison.recommended_connection_capacity_difference_kw == 165.0
    assert comparison.recommended_connection_capacity_avoided_by_smart_kw == 165.0
    assert comparison.uncontrolled_connection_upgrade_required is True
    assert comparison.smart_connection_upgrade_required is False
    assert comparison.uncontrolled_capacity_exceedance_duration_hours == 3.0
    assert comparison.smart_capacity_exceedance_duration_hours == 1.0
    assert comparison.exceedance_duration_reduction_hours == 2.0
    assert comparison.uncontrolled_average_transformer_loading_percent == 82.5
    assert comparison.smart_average_transformer_loading_percent == 60.0
    assert comparison.average_transformer_loading_percent_difference == 22.5
    assert comparison.uncontrolled_peak_transformer_loading_percent == 110.0
    assert comparison.smart_peak_transformer_loading_percent == 85.0
    assert comparison.peak_transformer_loading_percent_difference == 25.0
    assert comparison.uncontrolled_transformer_overload_indicator is True
    assert comparison.smart_transformer_overload_indicator is False
    assert comparison.uncontrolled_transformer_overload_duration_hours == 2.0
    assert comparison.smart_transformer_overload_duration_hours == 0.0
    assert comparison.transformer_overload_duration_difference_hours == 2.0
    assert comparison.uncontrolled_transformer_maximum_overload_kw == 25.0
    assert comparison.smart_transformer_maximum_overload_kw == 0.0
    assert comparison.transformer_maximum_overload_difference_kw == 25.0
    assert comparison.uncontrolled_transformer_thermal_risk_level == "high"
    assert comparison.smart_transformer_thermal_risk_level == "low"
    assert comparison.uncontrolled_maximum_feeder_loading_percent == 105.0
    assert comparison.smart_maximum_feeder_loading_percent == 70.0
    assert comparison.maximum_feeder_loading_percent_difference == 35.0
    assert comparison.uncontrolled_feeder_overload_indicator is True
    assert comparison.smart_feeder_overload_indicator is False
    assert comparison.uncontrolled_overloaded_feeder_count == 2
    assert comparison.smart_overloaded_feeder_count == 0
    assert comparison.overloaded_feeder_count_difference == 2
    assert comparison.uncontrolled_highest_feeder_thermal_risk_level == "high"
    assert comparison.smart_highest_feeder_thermal_risk_level == "low"
    assert comparison.uncontrolled_peak_harmonic_risk_score == 78.0
    assert comparison.smart_peak_harmonic_risk_score == 44.0
    assert comparison.peak_harmonic_risk_score_difference == 34.0
    assert comparison.uncontrolled_average_harmonic_risk_score == 52.0
    assert comparison.smart_average_harmonic_risk_score == 30.0
    assert comparison.average_harmonic_risk_score_difference == 22.0
    assert comparison.uncontrolled_harmonic_risk_duration_hours == 3.0
    assert comparison.smart_harmonic_risk_duration_hours == 1.0
    assert comparison.harmonic_risk_duration_difference_hours == 2.0
    assert comparison.uncontrolled_harmonic_risk_level == "high"
    assert comparison.smart_harmonic_risk_level == "moderate"
    assert comparison.uncontrolled_harmonic_warning_indicator is True
    assert comparison.smart_harmonic_warning_indicator is True
    assert comparison.uncontrolled_peak_current_imbalance_percent == 42.0
    assert comparison.smart_peak_current_imbalance_percent == 20.0
    assert comparison.peak_current_imbalance_percent_difference == 22.0
    assert comparison.uncontrolled_average_current_imbalance_percent == 28.0
    assert comparison.smart_average_current_imbalance_percent == 12.0
    assert comparison.average_current_imbalance_percent_difference == 16.0
    assert comparison.uncontrolled_imbalance_duration_hours == 1.5
    assert comparison.smart_imbalance_duration_hours == 0.0
    assert comparison.imbalance_duration_difference_hours == 1.5
    assert comparison.uncontrolled_current_imbalance_risk_level == "moderate"
    assert comparison.smart_current_imbalance_risk_level == "low"
    assert comparison.uncontrolled_imbalance_warning_indicator is True
    assert comparison.smart_imbalance_warning_indicator is False
    assert comparison.uncontrolled_overall_pq_risk_score == 64.0
    assert comparison.smart_overall_pq_risk_score == 34.0
    assert comparison.overall_pq_risk_score_difference == 30.0
    assert comparison.uncontrolled_overall_pq_risk_level == "high"
    assert comparison.smart_overall_pq_risk_level == "moderate"
    assert comparison.uncontrolled_overall_pq_warning_indicator is True
    assert comparison.smart_overall_pq_warning_indicator is True
    assert comparison.uncontrolled_power_quality_warning_count == 3
    assert comparison.smart_power_quality_warning_count == 2
    assert comparison.power_quality_warning_count_difference == 1
    assert comparison.uncontrolled_power_quality_message == (
        "Modeled overall PQ risk is high because harmonic risk is high "
        "and dominates the weighted demonstrator score."
    )
    assert comparison.smart_power_quality_message == (
        "Modeled overall PQ risk is moderate because harmonic risk is "
        "moderate and dominates the weighted demonstrator score."
    )
    assert comparison.uncontrolled_average_occupied_charger_count == 2.5
    assert comparison.smart_average_occupied_charger_count == 1.5
    assert comparison.average_occupied_charger_count_difference == 1.0
    assert comparison.uncontrolled_maximum_queue_length == 3
    assert comparison.smart_maximum_queue_length == 1
    assert comparison.maximum_queue_length_difference == 2
    assert comparison.queue_duration_difference_hours == 1.0
    assert comparison.average_waiting_time_difference_hours == 0.5
    assert comparison.maximum_waiting_time_difference_hours == 0.75
    assert comparison.vehicles_waiting_count_difference == 2
    assert comparison.vehicles_not_started_count_difference == 1
    assert comparison.vehicles_with_unmet_energy_count_difference == 2
    assert comparison.charger_capacity_vs_demand_balance_difference == -2
    assert comparison.required_charger_count_difference == 2
    assert comparison.additional_chargers_required_difference == 2
    assert comparison.service_rule_worsened_by_smart is False
    assert comparison.service_impact_summary == "Service shortfall reduced."
    assert comparison.uncontrolled_primary_constraint_reason == (
        "charger_availability"
    )
    assert comparison.smart_primary_constraint_reason == "none"
    assert comparison.charger_expansion_avoided_by_smart is True
    assert comparison.connection_upgrade_avoided_by_smart is True
    assert comparison.service_rule_resolved_by_smart is False
    assert comparison.infrastructure_recommendation_changed_by_smart is True
    assert comparison.primary_constraint_shifted_by_smart is True
    assert comparison.primary_constraint_shift_summary == (
        "Primary modeled bottleneck shifts from Charger availability to "
        "No primary constraint identified."
    )
    assert comparison.infrastructure_impact_summary == (
        "Smart Charging avoids the additional charger expansion indicated "
        "under uncontrolled charging."
    )
    assert comparison.uncontrolled_feeder_summary_rows == [
        {
            "feeder_id": "feeder_1",
            "charger_count": 2,
            "peak_loading_percent": 105.0,
            "overload_indicator": True,
            "overload_duration_hours": 1.0,
            "maximum_overload_kw": 5.0,
            "thermal_risk_level": "high",
        }
    ]
    assert comparison.smart_feeder_summary_rows == [
        {
            "feeder_id": "feeder_1",
            "charger_count": 2,
            "peak_loading_percent": 70.0,
            "overload_indicator": False,
            "overload_duration_hours": 0.0,
            "maximum_overload_kw": 0.0,
            "thermal_risk_level": "low",
        }
    ]
    assert comparison.uncontrolled_transformer_total_load_kw_by_timestep == [
        360.0,
        400.0,
        325.0,
    ]
    assert comparison.smart_transformer_loading_percent_by_timestep == [
        62.5,
        60.0,
        50.0,
    ]
    assert comparison.uncontrolled_transformer_overload_kw_by_timestep == [
        0.0,
        25.0,
        0.0,
    ]
    assert comparison.uncontrolled_occupied_charger_count_by_timestep == [1, 2, 3]
    assert comparison.smart_waiting_vehicle_count_by_timestep == [0, 0, 1]
    assert comparison.uncontrolled_harmonic_risk_score_by_timestep == [
        40.0,
        78.0,
        38.0,
    ]
    assert comparison.smart_current_imbalance_percent_by_timestep == [
        8.0,
        20.0,
        8.0,
    ]
    assert comparison.uncontrolled_overall_pq_risk_score_by_timestep == [
        31.0,
        64.0,
        32.4,
    ]
    assert comparison.smart_phase_a_load_kw_by_timestep == [90.0, 95.0, 70.0]


def test_relative_peak_reduction_is_zero_when_uncontrolled_peak_is_zero():
    uncontrolled = Metrics(
        total_daily_energy=0.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=0.0,
    )
    smart = Metrics(
        total_daily_energy=0.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=0.0,
    )

    comparison = calculate_comparison_metrics(uncontrolled, smart)

    assert comparison.relative_peak_reduction == 0.0


def test_comparison_metrics_drop_flat_price_cost_messaging():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        delivered_energy=1000.0,
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        delivered_energy=1000.0,
    )

    comparison = calculate_comparison_metrics(uncontrolled, smart)

    assert not hasattr(comparison, "energy_cost_savings")
    assert not hasattr(comparison, "flat_price_cost_message")


def test_comparison_metrics_ignore_flat_price_cost_differences():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        delivered_energy=900.0,
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        delivered_energy=1000.0,
    )

    comparison = calculate_comparison_metrics(uncontrolled, smart)

    assert not hasattr(comparison, "energy_cost_savings")
    assert not hasattr(comparison, "flat_price_cost_message")


def test_comparison_metrics_work_from_strategy_simulation_metrics():
    uncontrolled_result, smart_result = simulate_strategy_comparison(default_scenario)
    uncontrolled_metrics = calculate_metrics(uncontrolled_result, default_scenario)
    smart_metrics = calculate_metrics(smart_result, default_scenario)

    comparison = calculate_comparison_metrics(uncontrolled_metrics, smart_metrics)

    assert comparison.peak_reduction == pytest.approx(
        uncontrolled_metrics.peak_load - smart_metrics.peak_load
    )
    assert comparison.relative_peak_reduction == pytest.approx(
        comparison.peak_reduction / uncontrolled_metrics.peak_load * 100.0
    )
    assert comparison.capacity_utilization_difference == pytest.approx(
        uncontrolled_metrics.capacity_utilization - smart_metrics.capacity_utilization
    )
    assert comparison.unmet_energy_difference == pytest.approx(
        uncontrolled_metrics.unmet_energy - smart_metrics.unmet_energy
    )
    assert not hasattr(comparison, "energy_cost_savings")
    assert (
        comparison.uncontrolled_required_connection_capacity_kw
        == uncontrolled_metrics.required_connection_capacity_kw
    )
    assert (
        comparison.smart_required_connection_capacity_kw
        == smart_metrics.required_connection_capacity_kw
    )
    assert comparison.required_connection_capacity_difference_kw == pytest.approx(
        uncontrolled_metrics.required_connection_capacity_kw
        - smart_metrics.required_connection_capacity_kw
    )
    assert comparison.connection_capacity_avoided_by_smart_kw == pytest.approx(
        max(comparison.required_connection_capacity_difference_kw, 0.0)
    )
    assert comparison.uncontrolled_recommended_connection_capacity_kw == pytest.approx(
        uncontrolled_metrics.recommended_connection_capacity_kw
    )
    assert comparison.smart_recommended_connection_capacity_kw == pytest.approx(
        smart_metrics.recommended_connection_capacity_kw
    )
    assert comparison.recommended_connection_capacity_difference_kw == pytest.approx(
        uncontrolled_metrics.recommended_connection_capacity_kw
        - smart_metrics.recommended_connection_capacity_kw
    )
    assert comparison.recommended_connection_capacity_avoided_by_smart_kw == pytest.approx(
        max(
            uncontrolled_metrics.recommended_connection_capacity_kw
            - smart_metrics.recommended_connection_capacity_kw,
            0.0,
        )
    )
    assert comparison.uncontrolled_connection_upgrade_required is (
        uncontrolled_metrics.recommended_connection_capacity_kw
        > uncontrolled_metrics.configured_connection_capacity_kw
    )
    assert comparison.smart_connection_upgrade_required is (
        smart_metrics.recommended_connection_capacity_kw
        > smart_metrics.configured_connection_capacity_kw
    )
    assert comparison.connection_upgrade_avoided_by_smart is (
        comparison.uncontrolled_connection_upgrade_required
        and not comparison.smart_connection_upgrade_required
    )
    assert (
        comparison.uncontrolled_capacity_exceedance_duration_hours
        == uncontrolled_metrics.capacity_exceedance_duration_hours
    )
    assert (
        comparison.smart_capacity_exceedance_duration_hours
        == smart_metrics.capacity_exceedance_duration_hours
    )
    assert comparison.exceedance_duration_reduction_hours == pytest.approx(
        uncontrolled_metrics.capacity_exceedance_duration_hours
        - smart_metrics.capacity_exceedance_duration_hours
    )
    assert (
        comparison.uncontrolled_average_occupied_charger_count
        == uncontrolled_metrics.average_occupied_charger_count
    )
    assert (
        comparison.smart_average_occupied_charger_count
        == smart_metrics.average_occupied_charger_count
    )
    assert (
        comparison.uncontrolled_required_charger_count
        == uncontrolled_metrics.required_charger_count
    )
    assert (
        comparison.smart_required_charger_count
        == smart_metrics.required_charger_count
    )
    assert (
        comparison.uncontrolled_primary_constraint_reason
        == uncontrolled_metrics.primary_constraint_reason
    )
    assert (
        comparison.smart_primary_constraint_reason
        == smart_metrics.primary_constraint_reason
    )
    assert (
        comparison.uncontrolled_occupied_charger_count_by_timestep
        == uncontrolled_metrics.occupied_charger_count_by_timestep
    )
    assert (
        comparison.smart_waiting_vehicle_count_by_timestep
        == smart_metrics.waiting_vehicle_count_by_timestep
    )
    assert not hasattr(comparison, "flat_price_cost_message")


def test_comparison_metrics_do_not_create_boolean_or_reason_delta_fields():
    comparison = calculate_comparison_metrics(
        Metrics(
            total_daily_energy=1000.0,
            available_capacity=500.0,
            energy_delivery_sufficient=True,
            queue_present_indicator=True,
            primary_constraint_reason="charger_availability",
        ),
        Metrics(
            total_daily_energy=1000.0,
            available_capacity=500.0,
            energy_delivery_sufficient=True,
            queue_present_indicator=False,
            primary_constraint_reason="none",
        ),
    )

    assert not hasattr(comparison, "queue_present_indicator_difference")
    assert not hasattr(comparison, "charger_shortage_indicator_difference")
    assert not hasattr(comparison, "primary_constraint_reason_difference")
    assert not hasattr(comparison, "transformer_overload_indicator_difference")
    assert not hasattr(comparison, "feeder_overload_indicator_difference")
    assert not hasattr(comparison, "transformer_thermal_risk_level_difference")
    assert not hasattr(
        comparison,
        "highest_feeder_thermal_risk_level_difference",
    )


def test_comparison_metrics_preserve_none_values_and_omit_misleading_deltas():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        average_waiting_time_hours=None,
        maximum_waiting_time_hours=None,
        required_charger_count=None,
        additional_chargers_required=None,
        primary_constraint_reason="charging_window",
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        average_waiting_time_hours=1.0,
        maximum_waiting_time_hours=2.0,
        required_charger_count=4,
        additional_chargers_required=1,
        primary_constraint_reason="charger_availability",
    )

    comparison = calculate_comparison_metrics(uncontrolled, smart)

    assert comparison.uncontrolled_average_waiting_time_hours is None
    assert comparison.average_waiting_time_difference_hours is None
    assert comparison.uncontrolled_required_charger_count is None
    assert comparison.required_charger_count_difference is None
    assert comparison.uncontrolled_additional_chargers_required is None
    assert comparison.additional_chargers_required_difference is None
    assert comparison.uncontrolled_primary_constraint_reason == "charging_window"
    assert comparison.smart_primary_constraint_reason == "charger_availability"
    assert comparison.charger_expansion_avoided_by_smart is False
    assert comparison.connection_upgrade_avoided_by_smart is False
    assert comparison.service_rule_resolved_by_smart is False
    assert comparison.infrastructure_recommendation_changed_by_smart is True
    assert comparison.primary_constraint_shifted_by_smart is True
    assert comparison.primary_constraint_shift_summary == (
        "Primary modeled bottleneck shifts from Charging allowed window to "
        "Charger availability."
    )
    assert comparison.infrastructure_impact_summary == (
        "Primary modeled bottleneck shifts from Charging allowed window to "
        "Charger availability."
    )


def test_queue_aware_smart_charging_comparison_no_longer_relies_on_worse_queueing():
    base_scenario = Scenario(
        vehicles=4,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
    )

    uncontrolled_result, smart_result = simulate_strategy_comparison(base_scenario)
    uncontrolled_metrics = calculate_metrics(uncontrolled_result, base_scenario)
    smart_metrics = calculate_metrics(smart_result, base_scenario)
    comparison = calculate_comparison_metrics(uncontrolled_metrics, smart_metrics)

    assert comparison.peak_reduction == pytest.approx(0.0)
    assert (
        comparison.smart_average_occupied_charger_count
        > comparison.uncontrolled_average_occupied_charger_count
    )
    assert comparison.queue_duration_difference_hours == pytest.approx(0.0)
    assert comparison.average_waiting_time_difference_hours == pytest.approx(0.0)
    assert comparison.smart_queue_present_indicator is True


def test_comparison_time_series_remain_strategy_separated_aligned_and_copied():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        transformer_total_load_kw_by_timestep=[350.0, 375.0, 325.0],
        transformer_loading_percent_by_timestep=[87.5, 93.75, 81.25],
        transformer_overload_kw_by_timestep=[0.0, 5.0, 0.0],
        occupied_charger_count_by_timestep=[1, 2, 3],
        waiting_vehicle_count_by_timestep=[0, 1, 1],
        harmonic_risk_score_by_timestep=[30.0, 45.0, 25.0],
        current_imbalance_percent_by_timestep=[10.0, 18.0, 8.0],
        overall_pq_risk_score_by_timestep=[22.0, 34.2, 18.2],
        phase_a_load_kw_by_timestep=[120.0, 135.0, 110.0],
        phase_b_load_kw_by_timestep=[115.0, 120.0, 107.5],
        phase_c_load_kw_by_timestep=[115.0, 120.0, 107.5],
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        transformer_total_load_kw_by_timestep=[300.0, 310.0, 290.0],
        transformer_loading_percent_by_timestep=[75.0, 77.5, 72.5],
        transformer_overload_kw_by_timestep=[0.0, 0.0, 0.0],
        occupied_charger_count_by_timestep=[1, 1, 2],
        waiting_vehicle_count_by_timestep=[0, 0, 1],
        harmonic_risk_score_by_timestep=[20.0, 28.0, 18.0],
        current_imbalance_percent_by_timestep=[6.0, 10.0, 5.0],
        overall_pq_risk_score_by_timestep=[14.4, 20.8, 12.8],
        phase_a_load_kw_by_timestep=[105.0, 110.0, 100.0],
        phase_b_load_kw_by_timestep=[97.5, 100.0, 95.0],
        phase_c_load_kw_by_timestep=[97.5, 100.0, 95.0],
    )

    comparison = calculate_comparison_metrics(uncontrolled, smart)

    assert comparison.uncontrolled_occupied_charger_count_by_timestep == [1, 2, 3]
    assert comparison.smart_occupied_charger_count_by_timestep == [1, 1, 2]
    assert comparison.uncontrolled_waiting_vehicle_count_by_timestep == [0, 1, 1]
    assert comparison.smart_waiting_vehicle_count_by_timestep == [0, 0, 1]
    assert comparison.uncontrolled_transformer_total_load_kw_by_timestep == [
        350.0,
        375.0,
        325.0,
    ]
    assert comparison.smart_transformer_loading_percent_by_timestep == [
        75.0,
        77.5,
        72.5,
    ]
    assert comparison.uncontrolled_transformer_overload_kw_by_timestep == [
        0.0,
        5.0,
        0.0,
    ]
    assert comparison.uncontrolled_harmonic_risk_score_by_timestep == [
        30.0,
        45.0,
        25.0,
    ]
    assert comparison.smart_current_imbalance_percent_by_timestep == [
        6.0,
        10.0,
        5.0,
    ]
    assert comparison.uncontrolled_overall_pq_risk_score_by_timestep == [
        22.0,
        34.2,
        18.2,
    ]
    assert comparison.smart_phase_b_load_kw_by_timestep == [97.5, 100.0, 95.0]
    assert len(comparison.uncontrolled_occupied_charger_count_by_timestep) == len(
        comparison.smart_occupied_charger_count_by_timestep
    )
    assert len(comparison.uncontrolled_transformer_total_load_kw_by_timestep) == len(
        comparison.smart_transformer_total_load_kw_by_timestep
    )
    assert len(comparison.uncontrolled_harmonic_risk_score_by_timestep) == len(
        comparison.smart_harmonic_risk_score_by_timestep
    )
    assert len(comparison.uncontrolled_phase_a_load_kw_by_timestep) == len(
        comparison.smart_phase_a_load_kw_by_timestep
    )
    assert (
        comparison.uncontrolled_occupied_charger_count_by_timestep
        is not uncontrolled.occupied_charger_count_by_timestep
    )
    assert (
        comparison.uncontrolled_transformer_total_load_kw_by_timestep
        is not uncontrolled.transformer_total_load_kw_by_timestep
    )
    assert (
        comparison.smart_waiting_vehicle_count_by_timestep
        is not smart.waiting_vehicle_count_by_timestep
    )
    assert (
        comparison.smart_transformer_loading_percent_by_timestep
        is not smart.transformer_loading_percent_by_timestep
    )
    assert (
        comparison.uncontrolled_harmonic_risk_score_by_timestep
        is not uncontrolled.harmonic_risk_score_by_timestep
    )
    assert (
        comparison.smart_phase_c_load_kw_by_timestep
        is not smart.phase_c_load_kw_by_timestep
    )


def test_comparison_metrics_keep_power_quality_risk_states_side_by_side():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        harmonic_risk_level="high",
        harmonic_warning_indicator=True,
        current_imbalance_risk_level="moderate",
        imbalance_warning_indicator=True,
        overall_pq_risk_level="high",
        overall_pq_warning_indicator=True,
        power_quality_message="High modeled PQ risk from harmonic dominance.",
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        harmonic_risk_level="low",
        harmonic_warning_indicator=False,
        current_imbalance_risk_level="low",
        imbalance_warning_indicator=False,
        overall_pq_risk_level="low",
        overall_pq_warning_indicator=False,
        power_quality_message="Modeled overall PQ risk is low.",
    )

    comparison = calculate_comparison_metrics(uncontrolled, smart)

    assert comparison.uncontrolled_harmonic_risk_level == "high"
    assert comparison.smart_harmonic_risk_level == "low"
    assert comparison.uncontrolled_overall_pq_warning_indicator is True
    assert comparison.smart_overall_pq_warning_indicator is False
    assert comparison.uncontrolled_power_quality_message == (
        "High modeled PQ risk from harmonic dominance."
    )
    assert comparison.smart_power_quality_message == (
        "Modeled overall PQ risk is low."
    )
    assert not hasattr(comparison, "harmonic_risk_level_difference")
    assert not hasattr(comparison, "harmonic_warning_indicator_difference")
    assert not hasattr(comparison, "current_imbalance_risk_level_difference")
    assert not hasattr(comparison, "overall_pq_risk_level_difference")
    assert not hasattr(comparison, "overall_pq_warning_indicator_difference")
    assert not hasattr(comparison, "power_quality_message_difference")


def test_zero_vehicle_infeasible_and_legacy_comparisons_remain_safe_and_serializable():
    zero_vehicle = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        required_charger_count=0,
        additional_chargers_required=0,
        primary_constraint_reason="none",
        occupied_charger_count_by_timestep=[0, 0],
        waiting_vehicle_count_by_timestep=[0, 0],
    )
    legacy_metrics = calculate_metrics(
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

    comparison = calculate_comparison_metrics(zero_vehicle, legacy_metrics)
    data = json.loads(json.dumps(asdict(comparison)))

    assert data["uncontrolled_required_charger_count"] == 0
    assert data["smart_required_charger_count"] is None
    assert data["smart_primary_constraint_reason"] == "none"
    assert data["uncontrolled_transformer_loading_percent_by_timestep"] == []
    assert data["smart_feeder_summary_rows"] == []
    assert data["smart_occupied_charger_count_by_timestep"] == []
    assert data["smart_waiting_vehicle_count_by_timestep"] == []
    assert data["charger_expansion_avoided_by_smart"] is False
    assert data["connection_upgrade_avoided_by_smart"] is False
    assert data["service_rule_resolved_by_smart"] is False
    assert data["infrastructure_recommendation_changed_by_smart"] is False
    assert data["primary_constraint_shifted_by_smart"] is False
    assert data["primary_constraint_shift_summary"] == "No primary constraint shift."
    assert data["infrastructure_impact_summary"] == (
        "Both strategies satisfy the modeled service rule and lead to the "
        "same infrastructure recommendation."
    )


def test_comparison_metrics_include_grid_loading_deltas_for_peak_comparison():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_transformer_loading_percent=112.0,
        transformer_overload_duration_hours=1.5,
        transformer_maximum_overload_kw=18.0,
        maximum_feeder_loading_percent=108.0,
        overloaded_feeder_count=1,
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_transformer_loading_percent=88.0,
        transformer_overload_duration_hours=0.0,
        transformer_maximum_overload_kw=0.0,
        maximum_feeder_loading_percent=84.0,
        overloaded_feeder_count=0,
    )

    comparison = calculate_comparison_metrics(uncontrolled, smart)

    assert comparison.peak_transformer_loading_percent_difference == 24.0
    assert comparison.transformer_overload_duration_difference_hours == 1.5
    assert comparison.transformer_maximum_overload_difference_kw == 18.0
    assert comparison.maximum_feeder_loading_percent_difference == 24.0
    assert comparison.overloaded_feeder_count_difference == 1


def test_comparison_metrics_prepare_grid_capacity_status_for_worsening_case():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_capacity_margin_kw=40.0,
        connection_capacity_exceeded=False,
        transformer_thermal_risk_level="low",
        highest_feeder_thermal_risk_level="low",
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_capacity_margin_kw=-20.0,
        connection_capacity_exceeded=False,
        transformer_thermal_risk_level="moderate",
        highest_feeder_thermal_risk_level="low",
    )

    comparison = calculate_comparison_metrics(uncontrolled, smart)

    assert comparison.peak_capacity_margin_improvement_kw == -60.0
    assert comparison.grid_capacity_status == "Constraint worsened"


def test_comparison_metrics_keep_zero_grid_loading_deltas_for_unchanged_results():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        average_transformer_loading_percent=72.5,
        peak_transformer_loading_percent=96.0,
        transformer_overload_indicator=False,
        transformer_overload_duration_hours=0.0,
        transformer_maximum_overload_kw=0.0,
        transformer_thermal_risk_level="low",
        maximum_feeder_loading_percent=78.0,
        feeder_overload_indicator=False,
        overloaded_feeder_count=0,
        highest_feeder_thermal_risk_level="low",
        feeder_summary_rows=[
            FeederSummaryMetrics(
                feeder_id="feeder_1",
                charger_count=3,
                peak_loading_percent=78.0,
                overload_indicator=False,
                overload_duration_hours=0.0,
                maximum_overload_kw=0.0,
                thermal_risk_level="low",
            )
        ],
        transformer_total_load_kw_by_timestep=[290.0, 300.0],
        transformer_loading_percent_by_timestep=[72.5, 75.0],
        transformer_overload_kw_by_timestep=[0.0, 0.0],
    )

    comparison = calculate_comparison_metrics(metrics, metrics)

    assert comparison.average_transformer_loading_percent_difference == 0.0
    assert comparison.peak_transformer_loading_percent_difference == 0.0
    assert comparison.transformer_overload_duration_difference_hours == 0.0
    assert comparison.transformer_maximum_overload_difference_kw == 0.0
    assert comparison.maximum_feeder_loading_percent_difference == 0.0
    assert comparison.overloaded_feeder_count_difference == 0
    assert comparison.uncontrolled_feeder_summary_rows == (
        comparison.smart_feeder_summary_rows
    )
    assert comparison.uncontrolled_transformer_total_load_kw_by_timestep == [
        290.0,
        300.0,
    ]


def test_comparison_metrics_do_not_mutate_source_metrics():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        occupied_charger_count_by_timestep=[1, 2],
        waiting_vehicle_count_by_timestep=[0, 1],
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        occupied_charger_count_by_timestep=[1, 1],
        waiting_vehicle_count_by_timestep=[0, 0],
    )
    before_uncontrolled = asdict(uncontrolled)
    before_smart = asdict(smart)

    calculate_comparison_metrics(uncontrolled, smart)

    assert asdict(uncontrolled) == before_uncontrolled
    assert asdict(smart) == before_smart


def test_smart_charging_lower_required_capacity_is_reflected_in_comparison_metrics():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        configured_connection_capacity_kw=700.0,
        required_connection_capacity_kw=800.0,
        recommended_connection_capacity_kw=880.0,
        capacity_exceedance_duration_hours=4.0,
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        configured_connection_capacity_kw=700.0,
        required_connection_capacity_kw=650.0,
        recommended_connection_capacity_kw=715.0,
        capacity_exceedance_duration_hours=1.5,
    )

    comparison = calculate_comparison_metrics(uncontrolled, smart)

    assert comparison.required_connection_capacity_difference_kw == 150.0
    assert comparison.connection_capacity_avoided_by_smart_kw == 150.0
    assert comparison.recommended_connection_capacity_avoided_by_smart_kw == 165.0
    assert comparison.uncontrolled_connection_upgrade_required is True
    assert comparison.smart_connection_upgrade_required is True
    assert comparison.connection_upgrade_avoided_by_smart is False
    assert comparison.infrastructure_recommendation_changed_by_smart is True


def test_required_capacity_difference_preserves_negative_value_when_smart_requires_more():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        required_connection_capacity_kw=600.0,
        recommended_connection_capacity_kw=660.0,
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        required_connection_capacity_kw=700.0,
        recommended_connection_capacity_kw=770.0,
    )

    comparison = calculate_comparison_metrics(uncontrolled, smart)

    assert comparison.required_connection_capacity_difference_kw == -100.0


def test_avoided_capacity_is_clamped_to_zero_for_negative_difference():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        required_connection_capacity_kw=600.0,
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        required_connection_capacity_kw=700.0,
    )

    comparison = calculate_comparison_metrics(uncontrolled, smart)

    assert comparison.required_connection_capacity_difference_kw == -100.0
    assert comparison.connection_capacity_avoided_by_smart_kw == 0.0


def test_comparison_metrics_prepare_grid_connection_resolution_summary_from_existing_capacity_outputs():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        required_connection_capacity_kw=650.0,
        connection_capacity_exceeded=True,
        vehicles_with_unmet_energy_count=2,
        primary_constraint_reason="grid_connection_capacity",
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        required_connection_capacity_kw=500.0,
        connection_capacity_exceeded=False,
        primary_constraint_reason="none",
    )

    comparison = calculate_comparison_metrics(uncontrolled, smart)

    assert comparison.connection_capacity_avoided_by_smart_kw == 150.0
    assert comparison.service_rule_resolved_by_smart is True
    assert comparison.primary_constraint_shifted_by_smart is True
    assert comparison.infrastructure_impact_summary == (
        "Smart Charging resolves the modeled grid connection-capacity "
        "constraint under current infrastructure."
    )


def test_comparison_metrics_prepare_explicit_connection_upgrade_avoidance_metrics():
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

    comparison = calculate_comparison_metrics(uncontrolled, smart)

    assert comparison.recommended_connection_capacity_avoided_by_smart_kw == 180.0
    assert comparison.uncontrolled_connection_upgrade_required is True
    assert comparison.smart_connection_upgrade_required is False
    assert comparison.connection_upgrade_avoided_by_smart is True
    assert comparison.infrastructure_recommendation_changed_by_smart is True
    assert comparison.infrastructure_impact_summary == (
        "Smart Charging avoids the modeled connection-capacity upgrade "
        "recommendation for this scenario."
    )


def test_comparison_metrics_prepare_no_planning_change_summary_for_feasible_equal_outcome():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        required_connection_capacity_kw=500.0,
        required_charger_count=4,
        additional_chargers_required=0,
        primary_constraint_reason="none",
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        required_connection_capacity_kw=500.0,
        required_charger_count=4,
        additional_chargers_required=0,
        primary_constraint_reason="none",
    )

    comparison = calculate_comparison_metrics(uncontrolled, smart)

    assert comparison.charger_expansion_avoided_by_smart is False
    assert comparison.service_rule_resolved_by_smart is False
    assert comparison.primary_constraint_shifted_by_smart is False
    assert comparison.infrastructure_impact_summary == (
        "Both strategies satisfy the modeled service rule and lead to the "
        "same infrastructure recommendation."
    )


def test_recommended_capacity_difference_is_calculated_correctly():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        recommended_connection_capacity_kw=990.0,
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        recommended_connection_capacity_kw=825.0,
    )

    comparison = calculate_comparison_metrics(uncontrolled, smart)

    assert comparison.recommended_connection_capacity_difference_kw == 165.0


def test_exceedance_duration_reduction_is_calculated_correctly():
    uncontrolled = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        capacity_exceedance_duration_hours=5.0,
    )
    smart = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        capacity_exceedance_duration_hours=2.5,
    )

    comparison = calculate_comparison_metrics(uncontrolled, smart)

    assert comparison.uncontrolled_capacity_exceedance_duration_hours == 5.0
    assert comparison.smart_capacity_exceedance_duration_hours == 2.5
    assert comparison.exceedance_duration_reduction_hours == 2.5


def test_comparison_metrics_are_immutable():
    comparison = ComparisonMetrics(
        peak_reduction=150.0,
        relative_peak_reduction=37.5,
        capacity_utilization_difference=30.0,
        unmet_energy_difference=0.0,
    )

    with pytest.raises(FrozenInstanceError):
        comparison.peak_reduction = 1.0


def test_scenario_difference_metrics_contains_scenario_ab_fields():
    assert [field.name for field in fields(ScenarioComparisonMetrics)] == [
        "peak_load_difference_kw",
        "peak_load_change_percent",
        "capacity_utilization_difference_percentage_points",
        "capacity_utilization_change_percent",
        "delivered_energy_difference_kwh",
        "delivered_energy_change_percent",
        "unmet_energy_difference_kwh",
        "unmet_energy_change_percent",
        "average_transformer_loading_percent_difference",
        "peak_transformer_loading_percent_difference",
        "transformer_overload_duration_hours_difference",
        "transformer_maximum_overload_kw_difference",
        "maximum_feeder_loading_percent_difference",
        "overloaded_feeder_count_difference",
        "peak_harmonic_risk_score_difference",
        "average_harmonic_risk_score_difference",
        "harmonic_risk_duration_hours_difference",
        "peak_current_imbalance_percent_difference",
        "average_current_imbalance_percent_difference",
        "imbalance_duration_hours_difference",
        "overall_pq_risk_score_difference",
        "power_quality_warning_count_difference",
        "average_occupied_charger_count_difference",
        "peak_occupied_charger_count_difference",
        "maximum_queue_length_difference",
        "average_queue_length_difference",
        "queue_duration_hours_difference",
        "average_waiting_time_hours_difference",
        "maximum_waiting_time_hours_difference",
        "vehicles_waiting_count_difference",
        "vehicles_not_started_count_difference",
        "vehicles_with_unmet_energy_count_difference",
        "charger_capacity_vs_demand_balance_difference",
        "required_charger_count_difference",
        "additional_chargers_required_difference",
    ]


def test_scenario_difference_metrics_use_scenario_b_minus_scenario_a():
    metrics_a = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=400.0,
        capacity_utilization=80.0,
        delivered_energy=900.0,
        unmet_energy=100.0,
        average_transformer_loading_percent=72.5,
        peak_transformer_loading_percent=95.0,
        transformer_overload_duration_hours=0.5,
        transformer_maximum_overload_kw=10.0,
        maximum_feeder_loading_percent=88.0,
        overloaded_feeder_count=1,
        peak_harmonic_risk_score=30.0,
        average_harmonic_risk_score=18.0,
        harmonic_risk_duration_hours=0.5,
        harmonic_risk_level="low",
        harmonic_warning_indicator=False,
        peak_current_imbalance_percent=12.0,
        average_current_imbalance_percent=8.0,
        imbalance_duration_hours=0.0,
        current_imbalance_risk_level="low",
        imbalance_warning_indicator=False,
        overall_pq_risk_score=20.0,
        overall_pq_risk_level="low",
        overall_pq_warning_indicator=False,
        power_quality_warning_count=0,
        average_occupied_charger_count=2.0,
        peak_occupied_charger_count=3,
        maximum_queue_length=1,
        average_queue_length=0.5,
        queue_duration_hours=1.0,
        average_waiting_time_hours=0.25,
        maximum_waiting_time_hours=0.5,
        vehicles_waiting_count=1,
        vehicles_not_started_count=0,
        vehicles_with_unmet_energy_count=1,
        charger_capacity_vs_demand_balance=-1,
        required_charger_count=3,
        additional_chargers_required=1,
    )
    metrics_b = Metrics(
        total_daily_energy=1200.0,
        available_capacity=600.0,
        energy_delivery_sufficient=True,
        peak_load=500.0,
        capacity_utilization=75.0,
        delivered_energy=1000.0,
        unmet_energy=50.0,
        average_transformer_loading_percent=86.0,
        peak_transformer_loading_percent=110.0,
        transformer_overload_duration_hours=1.75,
        transformer_maximum_overload_kw=24.0,
        maximum_feeder_loading_percent=103.0,
        overloaded_feeder_count=3,
        peak_harmonic_risk_score=66.0,
        average_harmonic_risk_score=44.0,
        harmonic_risk_duration_hours=2.0,
        harmonic_risk_level="moderate",
        harmonic_warning_indicator=True,
        peak_current_imbalance_percent=34.0,
        average_current_imbalance_percent=20.0,
        imbalance_duration_hours=1.25,
        current_imbalance_risk_level="moderate",
        imbalance_warning_indicator=True,
        overall_pq_risk_score=52.0,
        overall_pq_risk_level="moderate",
        overall_pq_warning_indicator=True,
        power_quality_warning_count=3,
        average_occupied_charger_count=3.5,
        peak_occupied_charger_count=5,
        maximum_queue_length=4,
        average_queue_length=2.0,
        queue_duration_hours=3.5,
        average_waiting_time_hours=1.0,
        maximum_waiting_time_hours=1.5,
        vehicles_waiting_count=4,
        vehicles_not_started_count=2,
        vehicles_with_unmet_energy_count=3,
        charger_capacity_vs_demand_balance=-4,
        required_charger_count=6,
        additional_chargers_required=3,
    )

    comparison = calculate_scenario_difference_metrics(metrics_a, metrics_b)

    assert comparison.peak_load_difference_kw == 100.0
    assert comparison.peak_load_change_percent == 25.0
    assert comparison.capacity_utilization_difference_percentage_points == -5.0
    assert comparison.capacity_utilization_change_percent == -6.25
    assert comparison.delivered_energy_difference_kwh == 100.0
    assert comparison.delivered_energy_change_percent == pytest.approx(100.0 / 9.0)
    assert comparison.unmet_energy_difference_kwh == -50.0
    assert comparison.unmet_energy_change_percent == -50.0
    assert comparison.average_transformer_loading_percent_difference == 13.5
    assert comparison.peak_transformer_loading_percent_difference == 15.0
    assert comparison.transformer_overload_duration_hours_difference == 1.25
    assert comparison.transformer_maximum_overload_kw_difference == 14.0
    assert comparison.maximum_feeder_loading_percent_difference == 15.0
    assert comparison.overloaded_feeder_count_difference == 2
    assert comparison.peak_harmonic_risk_score_difference == 36.0
    assert comparison.average_harmonic_risk_score_difference == 26.0
    assert comparison.harmonic_risk_duration_hours_difference == 1.5
    assert comparison.peak_current_imbalance_percent_difference == 22.0
    assert comparison.average_current_imbalance_percent_difference == 12.0
    assert comparison.imbalance_duration_hours_difference == 1.25
    assert comparison.overall_pq_risk_score_difference == 32.0
    assert comparison.power_quality_warning_count_difference == 3
    assert comparison.average_occupied_charger_count_difference == 1.5
    assert comparison.peak_occupied_charger_count_difference == 2
    assert comparison.maximum_queue_length_difference == 3
    assert comparison.average_queue_length_difference == 1.5
    assert comparison.queue_duration_hours_difference == 2.5
    assert comparison.average_waiting_time_hours_difference == 0.75
    assert comparison.maximum_waiting_time_hours_difference == 1.0
    assert comparison.vehicles_waiting_count_difference == 3
    assert comparison.vehicles_not_started_count_difference == 2
    assert comparison.vehicles_with_unmet_energy_count_difference == 2
    assert comparison.charger_capacity_vs_demand_balance_difference == -3
    assert comparison.required_charger_count_difference == 3
    assert comparison.additional_chargers_required_difference == 2


def test_scenario_difference_metrics_support_zero_difference():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=400.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=100.0,
    )

    comparison = calculate_scenario_difference_metrics(metrics, metrics)

    assert comparison.peak_load_difference_kw == 0.0
    assert comparison.peak_load_change_percent == 0.0
    assert comparison.capacity_utilization_difference_percentage_points == 0.0
    assert comparison.delivered_energy_difference_kwh == 0.0
    assert comparison.unmet_energy_difference_kwh == 0.0
    assert comparison.average_transformer_loading_percent_difference == 0.0
    assert comparison.peak_transformer_loading_percent_difference == 0.0
    assert comparison.transformer_overload_duration_hours_difference == 0.0
    assert comparison.transformer_maximum_overload_kw_difference == 0.0
    assert comparison.maximum_feeder_loading_percent_difference == 0.0
    assert comparison.overloaded_feeder_count_difference == 0
    assert comparison.peak_harmonic_risk_score_difference == 0.0
    assert comparison.average_harmonic_risk_score_difference == 0.0
    assert comparison.harmonic_risk_duration_hours_difference == 0.0
    assert comparison.peak_current_imbalance_percent_difference == 0.0
    assert comparison.average_current_imbalance_percent_difference == 0.0
    assert comparison.imbalance_duration_hours_difference == 0.0
    assert comparison.overall_pq_risk_score_difference == 0.0
    assert comparison.power_quality_warning_count_difference == 0
    assert comparison.average_occupied_charger_count_difference == 0.0
    assert comparison.maximum_queue_length_difference == 0
    assert comparison.average_waiting_time_hours_difference == 0.0
    assert comparison.required_charger_count_difference == 0


def test_scenario_difference_metrics_return_none_for_zero_baseline_percentages():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=0.0,
        capacity_utilization=0.0,
        delivered_energy=0.0,
        unmet_energy=0.0,
    )
    metrics_b = Metrics(
        total_daily_energy=100.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        capacity_utilization=20.0,
        delivered_energy=100.0,
        unmet_energy=10.0,
    )

    comparison = calculate_scenario_difference_metrics(metrics_a, metrics_b)

    assert comparison.peak_load_difference_kw == 100.0
    assert comparison.peak_load_change_percent is None
    assert comparison.capacity_utilization_difference_percentage_points == 20.0
    assert comparison.capacity_utilization_change_percent is None
    assert comparison.delivered_energy_difference_kwh == 100.0
    assert comparison.delivered_energy_change_percent is None
    assert comparison.unmet_energy_difference_kwh == 10.0
    assert comparison.unmet_energy_change_percent is None


def test_scenario_difference_metrics_preserve_none_for_undefined_queueing_and_recommendation_values():
    metrics_a = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        average_waiting_time_hours=None,
        maximum_waiting_time_hours=None,
        required_charger_count=None,
        additional_chargers_required=None,
        primary_constraint_reason="charging_window",
    )
    metrics_b = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        average_waiting_time_hours=1.0,
        maximum_waiting_time_hours=2.0,
        required_charger_count=4,
        additional_chargers_required=1,
        primary_constraint_reason="charger_availability",
    )

    comparison = calculate_scenario_difference_metrics(metrics_a, metrics_b)

    assert comparison.average_waiting_time_hours_difference is None
    assert comparison.maximum_waiting_time_hours_difference is None
    assert comparison.required_charger_count_difference is None
    assert comparison.additional_chargers_required_difference is None
    assert not hasattr(comparison, "queue_present_indicator_difference")
    assert not hasattr(comparison, "primary_constraint_reason_difference")
    assert not hasattr(comparison, "transformer_overload_indicator_difference")
    assert not hasattr(comparison, "feeder_overload_indicator_difference")
    assert not hasattr(comparison, "transformer_thermal_risk_level_difference")
    assert not hasattr(
        comparison,
        "highest_feeder_thermal_risk_level_difference",
    )
    assert not hasattr(comparison, "harmonic_risk_level_difference")
    assert not hasattr(comparison, "current_imbalance_risk_level_difference")
    assert not hasattr(comparison, "overall_pq_risk_level_difference")
    assert not hasattr(comparison, "harmonic_warning_indicator_difference")
    assert not hasattr(comparison, "imbalance_warning_indicator_difference")
    assert not hasattr(comparison, "overall_pq_warning_indicator_difference")
    assert not hasattr(comparison, "power_quality_message_difference")


def test_scenario_ab_serialized_metrics_preserve_independent_constraint_reasons_and_none_recommendations():
    metrics_a = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        required_charger_count=2,
        additional_chargers_required=0,
        primary_constraint_reason="none",
    )
    metrics_b = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        required_charger_count=None,
        additional_chargers_required=None,
        primary_constraint_reason="charging_window",
    )

    data_a = json.loads(json.dumps(asdict(metrics_a)))
    data_b = json.loads(json.dumps(asdict(metrics_b)))

    assert data_a["required_charger_count"] == 2
    assert data_a["additional_chargers_required"] == 0
    assert data_a["primary_constraint_reason"] == "none"
    assert data_b["required_charger_count"] is None
    assert data_b["additional_chargers_required"] is None
    assert data_b["primary_constraint_reason"] == "charging_window"


def test_scenario_difference_metrics_do_not_compare_timestep_series_point_by_point():
    metrics_a = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        occupied_charger_count_by_timestep=[1, 2, 3],
        waiting_vehicle_count_by_timestep=[0, 1, 1],
        harmonic_risk_score_by_timestep=[10.0, 20.0, 15.0],
        current_imbalance_percent_by_timestep=[4.0, 8.0, 6.0],
        overall_pq_risk_score_by_timestep=[7.6, 15.2, 11.4],
    )
    metrics_b = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        occupied_charger_count_by_timestep=[2, 2],
        waiting_vehicle_count_by_timestep=[0, 0],
        harmonic_risk_score_by_timestep=[12.0, 18.0],
        current_imbalance_percent_by_timestep=[5.0, 7.0],
        overall_pq_risk_score_by_timestep=[9.2, 13.6],
    )

    comparison = calculate_scenario_difference_metrics(metrics_a, metrics_b)

    assert not hasattr(comparison, "occupied_charger_count_by_timestep_difference")
    assert not hasattr(comparison, "waiting_vehicle_count_by_timestep_difference")
    assert not hasattr(comparison, "harmonic_risk_score_by_timestep_difference")
    assert not hasattr(
        comparison,
        "current_imbalance_percent_by_timestep_difference",
    )
    assert not hasattr(comparison, "overall_pq_risk_score_by_timestep_difference")


def test_scenario_difference_metrics_serialization_round_trip_preserves_values():
    comparison = ScenarioComparisonMetrics(
        peak_load_difference_kw=-60.0,
        peak_load_change_percent=-33.3,
        capacity_utilization_difference_percentage_points=-30.0,
        capacity_utilization_change_percent=-33.3,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=0.0,
        unmet_energy_difference_kwh=-40.0,
        unmet_energy_change_percent=-100.0,
        average_transformer_loading_percent_difference=-12.5,
        peak_transformer_loading_percent_difference=-20.0,
        transformer_overload_duration_hours_difference=-0.5,
        transformer_maximum_overload_kw_difference=-10.0,
        maximum_feeder_loading_percent_difference=-15.0,
        overloaded_feeder_count_difference=-2,
        peak_harmonic_risk_score_difference=-20.0,
        average_harmonic_risk_score_difference=-12.0,
        harmonic_risk_duration_hours_difference=-1.5,
        peak_current_imbalance_percent_difference=-10.0,
        average_current_imbalance_percent_difference=-5.5,
        imbalance_duration_hours_difference=-0.75,
        overall_pq_risk_score_difference=-18.0,
        power_quality_warning_count_difference=-2,
        average_occupied_charger_count_difference=1.5,
        peak_occupied_charger_count_difference=2,
        maximum_queue_length_difference=3,
        average_queue_length_difference=1.25,
        queue_duration_hours_difference=2.0,
        average_waiting_time_hours_difference=None,
        maximum_waiting_time_hours_difference=1.0,
        vehicles_waiting_count_difference=4,
        vehicles_not_started_count_difference=1,
        vehicles_with_unmet_energy_count_difference=2,
        charger_capacity_vs_demand_balance_difference=-3,
        required_charger_count_difference=None,
        additional_chargers_required_difference=2,
    )

    data = scenario_comparison_metrics_to_dict(comparison)
    restored_comparison = scenario_comparison_metrics_from_dict(data)

    assert restored_comparison == comparison


def test_scenario_difference_metrics_handle_mismatched_feeder_topologies():
    metrics_a = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        average_transformer_loading_percent=60.0,
        peak_transformer_loading_percent=82.0,
        transformer_overload_duration_hours=0.0,
        transformer_maximum_overload_kw=0.0,
        maximum_feeder_loading_percent=74.0,
        feeder_overload_indicator=False,
        overloaded_feeder_count=0,
        highest_feeder_thermal_risk_level="low",
        feeder_summary_rows=[
            FeederSummaryMetrics(
                feeder_id="feeder-1",
                charger_count=4,
                peak_loading_percent=74.0,
                overload_indicator=False,
                overload_duration_hours=0.0,
                maximum_overload_kw=0.0,
                thermal_risk_level="low",
            )
        ],
    )
    metrics_b = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        average_transformer_loading_percent=71.0,
        peak_transformer_loading_percent=98.0,
        transformer_overload_duration_hours=1.0,
        transformer_maximum_overload_kw=12.0,
        maximum_feeder_loading_percent=101.0,
        feeder_overload_indicator=True,
        overloaded_feeder_count=2,
        highest_feeder_thermal_risk_level="high",
        feeder_summary_rows=[
            FeederSummaryMetrics(
                feeder_id="feeder-1",
                charger_count=2,
                peak_loading_percent=96.0,
                overload_indicator=False,
                overload_duration_hours=0.0,
                maximum_overload_kw=0.0,
                thermal_risk_level="moderate",
            ),
            FeederSummaryMetrics(
                feeder_id="feeder-2",
                charger_count=2,
                peak_loading_percent=101.0,
                overload_indicator=True,
                overload_duration_hours=1.0,
                maximum_overload_kw=12.0,
                thermal_risk_level="high",
            ),
        ],
    )

    comparison = calculate_scenario_difference_metrics(metrics_a, metrics_b)

    assert comparison.average_transformer_loading_percent_difference == 11.0
    assert comparison.peak_transformer_loading_percent_difference == 16.0
    assert comparison.transformer_overload_duration_hours_difference == 1.0
    assert comparison.transformer_maximum_overload_kw_difference == 12.0
    assert comparison.maximum_feeder_loading_percent_difference == 27.0
    assert comparison.overloaded_feeder_count_difference == 2
    assert comparison.peak_harmonic_risk_score_difference == 0.0
    assert comparison.average_harmonic_risk_score_difference == 0.0
    assert comparison.overall_pq_risk_score_difference == 0.0
    assert comparison.power_quality_warning_count_difference == 0
    assert not hasattr(comparison, "feeder_summary_rows_difference")


def test_scenario_difference_metrics_preserve_safe_defaults_for_missing_power_quality_fields():
    legacy_data = {
        "peak_load_difference_kw": 100.0,
        "peak_load_change_percent": 25.0,
        "capacity_utilization_difference_percentage_points": -5.0,
        "capacity_utilization_change_percent": -6.25,
        "delivered_energy_difference_kwh": 100.0,
        "delivered_energy_change_percent": 11.11111111111111,
        "unmet_energy_difference_kwh": -50.0,
        "unmet_energy_change_percent": -50.0,
    }

    comparison = scenario_comparison_metrics_from_dict(legacy_data)

    assert comparison.peak_harmonic_risk_score_difference == 0.0
    assert comparison.average_harmonic_risk_score_difference == 0.0
    assert comparison.harmonic_risk_duration_hours_difference == 0.0
    assert comparison.peak_current_imbalance_percent_difference == 0.0
    assert comparison.average_current_imbalance_percent_difference == 0.0
    assert comparison.imbalance_duration_hours_difference == 0.0
    assert comparison.overall_pq_risk_score_difference == 0.0
    assert comparison.power_quality_warning_count_difference == 0


def test_scenario_difference_metrics_do_not_mutate_source_metrics():
    metrics_a = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        required_charger_count=2,
        additional_chargers_required=0,
    )
    metrics_b = Metrics(
        total_daily_energy=1200.0,
        available_capacity=600.0,
        energy_delivery_sufficient=False,
        required_charger_count=None,
        additional_chargers_required=None,
    )
    before_a = asdict(metrics_a)
    before_b = asdict(metrics_b)

    calculate_scenario_difference_metrics(metrics_a, metrics_b)

    assert asdict(metrics_a) == before_a
    assert asdict(metrics_b) == before_b


def test_calculate_comparison_metrics_power_quality_regression_tradeoff_case():
    base_scenario = _build_reference_power_quality_strategy_scenario()

    uncontrolled_result, smart_result = simulate_strategy_comparison(base_scenario)
    uncontrolled_scenario = replace(
        base_scenario,
        charging_strategy=ChargingStrategy.UNCONTROLLED,
    )
    smart_scenario = replace(
        base_scenario,
        charging_strategy=ChargingStrategy.SMART,
    )
    uncontrolled_metrics = calculate_metrics(
        uncontrolled_result,
        uncontrolled_scenario,
    )
    smart_metrics = calculate_metrics(
        smart_result,
        smart_scenario,
    )
    comparison = calculate_comparison_metrics(uncontrolled_metrics, smart_metrics)

    assert comparison.uncontrolled_peak_harmonic_risk_score == 90.0
    assert comparison.smart_peak_harmonic_risk_score == 22.5
    assert comparison.peak_harmonic_risk_score_difference == 67.5
    assert comparison.uncontrolled_average_harmonic_risk_score == pytest.approx(0.9375)
    assert comparison.smart_average_harmonic_risk_score == pytest.approx(0.9375)
    assert comparison.average_harmonic_risk_score_difference == 0.0
    assert comparison.uncontrolled_peak_current_imbalance_percent == 200.0
    assert comparison.smart_peak_current_imbalance_percent == 200.0
    assert comparison.peak_current_imbalance_percent_difference == 0.0
    assert comparison.average_current_imbalance_percent_difference == pytest.approx(
        -6.25
    )
    assert comparison.overall_pq_risk_score_difference == 40.5
    assert comparison.power_quality_warning_count_difference == 1
    assert comparison.uncontrolled_power_quality_message == (
        "Modeled overall PQ risk is high because harmonic risk is high and "
        "dominates the weighted PQ score."
    )
    assert comparison.smart_power_quality_message == (
        "Modeled overall PQ risk is high because current imbalance is high and "
        "dominates the weighted PQ score."
    )
    assert [
        (index, value)
        for index, value in enumerate(comparison.uncontrolled_harmonic_risk_score_by_timestep)
        if value
    ] == [(32, 90.0)]
    assert [
        (index, value)
        for index, value in enumerate(comparison.smart_harmonic_risk_score_by_timestep)
        if value
    ] == [(32, 22.5), (33, 22.5), (34, 22.5), (35, 22.5)]


def test_peak_shaving_comparison_does_not_claim_service_gain_from_worse_service():
    base_scenario = Scenario(
        vehicles=4,
        daily_energy_per_vehicle=25.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
        departure_mode=DepartureMode.WINDOW_END,
        charging_strategy=ChargingStrategy.SMART,
    )

    uncontrolled_result, smart_result = simulate_strategy_comparison(base_scenario)
    uncontrolled_metrics = calculate_metrics(
        uncontrolled_result,
        replace(base_scenario, charging_strategy=ChargingStrategy.UNCONTROLLED),
    )
    smart_metrics = calculate_metrics(
        smart_result,
        replace(base_scenario, charging_strategy=ChargingStrategy.SMART),
    )
    comparison = calculate_comparison_metrics(
        uncontrolled_metrics,
        smart_metrics,
    )

    assert comparison.peak_reduction == pytest.approx(0.0)
    assert comparison.unmet_energy_difference == 0.0
    assert comparison.vehicles_with_unmet_energy_count_difference == 0
    assert comparison.service_rule_resolved_by_smart is False
