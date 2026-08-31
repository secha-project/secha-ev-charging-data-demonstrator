"""Difference metrics for independent Scenario A/B comparisons."""

from dataclasses import dataclass
from typing import Any

from metrics.comparison_assembly import (
    ScenarioDifferenceFieldSpec,
    build_scenario_difference_fields,
)
from metrics.metrics import Metrics


PERCENT_MULTIPLIER = 100.0
ScenarioComparisonMetricsData = dict[str, Any]


@dataclass(frozen=True)
class ScenarioComparisonMetrics:
    """Deterministic differences between Scenario A and Scenario B metrics."""

    peak_load_difference_kw: float
    peak_load_change_percent: float | None
    capacity_utilization_difference_percentage_points: float
    capacity_utilization_change_percent: float | None
    delivered_energy_difference_kwh: float
    delivered_energy_change_percent: float | None
    unmet_energy_difference_kwh: float
    unmet_energy_change_percent: float | None
    average_transformer_loading_percent_difference: float = 0.0
    peak_transformer_loading_percent_difference: float = 0.0
    transformer_overload_duration_hours_difference: float = 0.0
    transformer_maximum_overload_kw_difference: float = 0.0
    maximum_feeder_loading_percent_difference: float = 0.0
    overloaded_feeder_count_difference: int = 0
    peak_harmonic_risk_score_difference: float = 0.0
    average_harmonic_risk_score_difference: float = 0.0
    harmonic_risk_duration_hours_difference: float = 0.0
    peak_current_imbalance_percent_difference: float = 0.0
    average_current_imbalance_percent_difference: float = 0.0
    imbalance_duration_hours_difference: float = 0.0
    overall_pq_risk_score_difference: float = 0.0
    power_quality_warning_count_difference: int = 0
    average_occupied_charger_count_difference: float = 0.0
    peak_occupied_charger_count_difference: int = 0
    maximum_queue_length_difference: int = 0
    average_queue_length_difference: float = 0.0
    queue_duration_hours_difference: float = 0.0
    average_waiting_time_hours_difference: float | None = None
    maximum_waiting_time_hours_difference: float | None = None
    vehicles_waiting_count_difference: int = 0
    vehicles_not_started_count_difference: int = 0
    vehicles_with_unmet_energy_count_difference: int = 0
    charger_capacity_vs_demand_balance_difference: int = 0
    required_charger_count_difference: int | None = None
    additional_chargers_required_difference: int | None = None


_SCENARIO_DIFFERENCE_FIELD_SPECS = (
    ScenarioDifferenceFieldSpec(
        "peak_load",
        "peak_load_difference_kw",
        "peak_load_change_percent",
    ),
    ScenarioDifferenceFieldSpec(
        "capacity_utilization",
        "capacity_utilization_difference_percentage_points",
        "capacity_utilization_change_percent",
    ),
    ScenarioDifferenceFieldSpec(
        "delivered_energy",
        "delivered_energy_difference_kwh",
        "delivered_energy_change_percent",
    ),
    ScenarioDifferenceFieldSpec(
        "unmet_energy",
        "unmet_energy_difference_kwh",
        "unmet_energy_change_percent",
    ),
    ScenarioDifferenceFieldSpec(
        "average_transformer_loading_percent",
        "average_transformer_loading_percent_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "peak_transformer_loading_percent",
        "peak_transformer_loading_percent_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "transformer_overload_duration_hours",
        "transformer_overload_duration_hours_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "transformer_maximum_overload_kw",
        "transformer_maximum_overload_kw_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "maximum_feeder_loading_percent",
        "maximum_feeder_loading_percent_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "overloaded_feeder_count",
        "overloaded_feeder_count_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "peak_harmonic_risk_score",
        "peak_harmonic_risk_score_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "average_harmonic_risk_score",
        "average_harmonic_risk_score_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "harmonic_risk_duration_hours",
        "harmonic_risk_duration_hours_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "peak_current_imbalance_percent",
        "peak_current_imbalance_percent_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "average_current_imbalance_percent",
        "average_current_imbalance_percent_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "imbalance_duration_hours",
        "imbalance_duration_hours_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "overall_pq_risk_score",
        "overall_pq_risk_score_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "power_quality_warning_count",
        "power_quality_warning_count_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "average_occupied_charger_count",
        "average_occupied_charger_count_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "peak_occupied_charger_count",
        "peak_occupied_charger_count_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "maximum_queue_length",
        "maximum_queue_length_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "average_queue_length",
        "average_queue_length_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "queue_duration_hours",
        "queue_duration_hours_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "average_waiting_time_hours",
        "average_waiting_time_hours_difference",
        difference_kind="defined",
    ),
    ScenarioDifferenceFieldSpec(
        "maximum_waiting_time_hours",
        "maximum_waiting_time_hours_difference",
        difference_kind="defined",
    ),
    ScenarioDifferenceFieldSpec(
        "vehicles_waiting_count",
        "vehicles_waiting_count_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "vehicles_not_started_count",
        "vehicles_not_started_count_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "vehicles_with_unmet_energy_count",
        "vehicles_with_unmet_energy_count_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "charger_capacity_vs_demand_balance",
        "charger_capacity_vs_demand_balance_difference",
    ),
    ScenarioDifferenceFieldSpec(
        "required_charger_count",
        "required_charger_count_difference",
        difference_kind="defined",
    ),
    ScenarioDifferenceFieldSpec(
        "additional_chargers_required",
        "additional_chargers_required_difference",
        difference_kind="defined",
    ),
)


def calculate_scenario_difference_metrics(
    metrics_a: Metrics,
    metrics_b: Metrics,
) -> ScenarioComparisonMetrics:
    """Calculate Scenario B minus Scenario A metric differences."""
    return ScenarioComparisonMetrics(
        **build_scenario_difference_fields(
            metrics_a,
            metrics_b,
            _SCENARIO_DIFFERENCE_FIELD_SPECS,
            calculate_percent_change=_calculate_percent_change,
        )
    )


def scenario_comparison_metrics_to_dict(
    comparison_metrics: ScenarioComparisonMetrics,
) -> ScenarioComparisonMetricsData:
    """Return a Dash-store-safe dictionary of Scenario A/B differences."""
    return {
        "peak_load_difference_kw": comparison_metrics.peak_load_difference_kw,
        "peak_load_change_percent": comparison_metrics.peak_load_change_percent,
        "capacity_utilization_difference_percentage_points": (
            comparison_metrics.capacity_utilization_difference_percentage_points
        ),
        "capacity_utilization_change_percent": (
            comparison_metrics.capacity_utilization_change_percent
        ),
        "delivered_energy_difference_kwh": (
            comparison_metrics.delivered_energy_difference_kwh
        ),
        "delivered_energy_change_percent": (
            comparison_metrics.delivered_energy_change_percent
        ),
        "unmet_energy_difference_kwh": (
            comparison_metrics.unmet_energy_difference_kwh
        ),
        "unmet_energy_change_percent": (
            comparison_metrics.unmet_energy_change_percent
        ),
        "average_transformer_loading_percent_difference": (
            comparison_metrics.average_transformer_loading_percent_difference
        ),
        "peak_transformer_loading_percent_difference": (
            comparison_metrics.peak_transformer_loading_percent_difference
        ),
        "transformer_overload_duration_hours_difference": (
            comparison_metrics.transformer_overload_duration_hours_difference
        ),
        "transformer_maximum_overload_kw_difference": (
            comparison_metrics.transformer_maximum_overload_kw_difference
        ),
        "maximum_feeder_loading_percent_difference": (
            comparison_metrics.maximum_feeder_loading_percent_difference
        ),
        "overloaded_feeder_count_difference": (
            comparison_metrics.overloaded_feeder_count_difference
        ),
        "peak_harmonic_risk_score_difference": (
            comparison_metrics.peak_harmonic_risk_score_difference
        ),
        "average_harmonic_risk_score_difference": (
            comparison_metrics.average_harmonic_risk_score_difference
        ),
        "harmonic_risk_duration_hours_difference": (
            comparison_metrics.harmonic_risk_duration_hours_difference
        ),
        "peak_current_imbalance_percent_difference": (
            comparison_metrics.peak_current_imbalance_percent_difference
        ),
        "average_current_imbalance_percent_difference": (
            comparison_metrics.average_current_imbalance_percent_difference
        ),
        "imbalance_duration_hours_difference": (
            comparison_metrics.imbalance_duration_hours_difference
        ),
        "overall_pq_risk_score_difference": (
            comparison_metrics.overall_pq_risk_score_difference
        ),
        "power_quality_warning_count_difference": (
            comparison_metrics.power_quality_warning_count_difference
        ),
        "average_occupied_charger_count_difference": (
            comparison_metrics.average_occupied_charger_count_difference
        ),
        "peak_occupied_charger_count_difference": (
            comparison_metrics.peak_occupied_charger_count_difference
        ),
        "maximum_queue_length_difference": (
            comparison_metrics.maximum_queue_length_difference
        ),
        "average_queue_length_difference": (
            comparison_metrics.average_queue_length_difference
        ),
        "queue_duration_hours_difference": (
            comparison_metrics.queue_duration_hours_difference
        ),
        "average_waiting_time_hours_difference": (
            comparison_metrics.average_waiting_time_hours_difference
        ),
        "maximum_waiting_time_hours_difference": (
            comparison_metrics.maximum_waiting_time_hours_difference
        ),
        "vehicles_waiting_count_difference": (
            comparison_metrics.vehicles_waiting_count_difference
        ),
        "vehicles_not_started_count_difference": (
            comparison_metrics.vehicles_not_started_count_difference
        ),
        "vehicles_with_unmet_energy_count_difference": (
            comparison_metrics.vehicles_with_unmet_energy_count_difference
        ),
        "charger_capacity_vs_demand_balance_difference": (
            comparison_metrics.charger_capacity_vs_demand_balance_difference
        ),
        "required_charger_count_difference": (
            comparison_metrics.required_charger_count_difference
        ),
        "additional_chargers_required_difference": (
            comparison_metrics.additional_chargers_required_difference
        ),
    }


def scenario_comparison_metrics_from_dict(
    data: ScenarioComparisonMetricsData,
) -> ScenarioComparisonMetrics:
    """Rebuild Scenario A/B difference metrics from serialized data."""
    return ScenarioComparisonMetrics(
        peak_load_difference_kw=data["peak_load_difference_kw"],
        peak_load_change_percent=data["peak_load_change_percent"],
        capacity_utilization_difference_percentage_points=(
            data["capacity_utilization_difference_percentage_points"]
        ),
        capacity_utilization_change_percent=(
            data["capacity_utilization_change_percent"]
        ),
        delivered_energy_difference_kwh=data["delivered_energy_difference_kwh"],
        delivered_energy_change_percent=data["delivered_energy_change_percent"],
        unmet_energy_difference_kwh=data["unmet_energy_difference_kwh"],
        unmet_energy_change_percent=data["unmet_energy_change_percent"],
        average_transformer_loading_percent_difference=data.get(
            "average_transformer_loading_percent_difference",
            0.0,
        ),
        peak_transformer_loading_percent_difference=data.get(
            "peak_transformer_loading_percent_difference",
            0.0,
        ),
        transformer_overload_duration_hours_difference=data.get(
            "transformer_overload_duration_hours_difference",
            0.0,
        ),
        transformer_maximum_overload_kw_difference=data.get(
            "transformer_maximum_overload_kw_difference",
            0.0,
        ),
        maximum_feeder_loading_percent_difference=data.get(
            "maximum_feeder_loading_percent_difference",
            0.0,
        ),
        overloaded_feeder_count_difference=data.get(
            "overloaded_feeder_count_difference",
            0,
        ),
        peak_harmonic_risk_score_difference=data.get(
            "peak_harmonic_risk_score_difference",
            0.0,
        ),
        average_harmonic_risk_score_difference=data.get(
            "average_harmonic_risk_score_difference",
            0.0,
        ),
        harmonic_risk_duration_hours_difference=data.get(
            "harmonic_risk_duration_hours_difference",
            0.0,
        ),
        peak_current_imbalance_percent_difference=data.get(
            "peak_current_imbalance_percent_difference",
            0.0,
        ),
        average_current_imbalance_percent_difference=data.get(
            "average_current_imbalance_percent_difference",
            0.0,
        ),
        imbalance_duration_hours_difference=data.get(
            "imbalance_duration_hours_difference",
            0.0,
        ),
        overall_pq_risk_score_difference=data.get(
            "overall_pq_risk_score_difference",
            0.0,
        ),
        power_quality_warning_count_difference=data.get(
            "power_quality_warning_count_difference",
            0,
        ),
        average_occupied_charger_count_difference=data.get(
            "average_occupied_charger_count_difference",
            0.0,
        ),
        peak_occupied_charger_count_difference=data.get(
            "peak_occupied_charger_count_difference",
            0,
        ),
        maximum_queue_length_difference=data.get(
            "maximum_queue_length_difference",
            0,
        ),
        average_queue_length_difference=data.get(
            "average_queue_length_difference",
            0.0,
        ),
        queue_duration_hours_difference=data.get(
            "queue_duration_hours_difference",
            0.0,
        ),
        average_waiting_time_hours_difference=data.get(
            "average_waiting_time_hours_difference",
        ),
        maximum_waiting_time_hours_difference=data.get(
            "maximum_waiting_time_hours_difference",
        ),
        vehicles_waiting_count_difference=data.get(
            "vehicles_waiting_count_difference",
            0,
        ),
        vehicles_not_started_count_difference=data.get(
            "vehicles_not_started_count_difference",
            0,
        ),
        vehicles_with_unmet_energy_count_difference=data.get(
            "vehicles_with_unmet_energy_count_difference",
            0,
        ),
        charger_capacity_vs_demand_balance_difference=data.get(
            "charger_capacity_vs_demand_balance_difference",
            0,
        ),
        required_charger_count_difference=data.get(
            "required_charger_count_difference",
        ),
        additional_chargers_required_difference=data.get(
            "additional_chargers_required_difference",
        ),
    )


def _calculate_percent_change(
    difference: float,
    baseline: float,
) -> float | None:
    """Return relative percent change or None for a zero baseline."""
    if baseline == 0.0:
        return None

    return difference / baseline * PERCENT_MULTIPLIER
