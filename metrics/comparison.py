"""Comparison KPIs derived from two metric sets."""

from dataclasses import dataclass, field

from metrics.comparison_assembly import (
    StrategyMetricFieldSpec,
    build_strategy_metric_fields,
    copy_metric_sequence,
    copy_summary_rows_for_comparison,
)
from metrics.constraint_analysis import (
    CONFIGURED_CONNECTION_CAPACITY_ADEQUATE_REASON,
    GRID_CONNECTION_CAPACITY_CONSTRAINT_REASON,
)
from metrics.metrics import Metrics
from metrics.planning import (
    charger_expansion_avoided_by_smart,
    connection_upgrade_avoided_by_smart,
    connection_upgrade_required,
    infrastructure_impact_summary,
    infrastructure_recommendation_changed_by_smart,
    primary_constraint_shift_summary,
    primary_constraint_shifted_by_smart,
    service_impact_summary,
    service_rule_resolved_by_smart,
    service_rule_worsened_by_smart,
)


PERCENT_MULTIPLIER = 100.0


@dataclass(frozen=True)
class ComparisonMetrics:
    """Reusable KPIs comparing uncontrolled and smart charging metrics."""

    peak_reduction: float
    relative_peak_reduction: float
    capacity_utilization_difference: float
    unmet_energy_difference: float
    peak_capacity_margin_improvement_kw: float = 0.0
    grid_capacity_status: str = "No modeled constraint"
    uncontrolled_required_connection_capacity_kw: float = 0.0
    smart_required_connection_capacity_kw: float = 0.0
    required_connection_capacity_difference_kw: float = 0.0
    connection_capacity_avoided_by_smart_kw: float = 0.0
    uncontrolled_recommended_connection_capacity_kw: float = 0.0
    smart_recommended_connection_capacity_kw: float = 0.0
    recommended_connection_capacity_difference_kw: float = 0.0
    recommended_connection_capacity_avoided_by_smart_kw: float = 0.0
    uncontrolled_connection_upgrade_required: bool = False
    smart_connection_upgrade_required: bool = False
    uncontrolled_connection_capacity_adequate_indicator: bool = True
    smart_connection_capacity_adequate_indicator: bool = True
    uncontrolled_connection_capacity_recommendation_reason: str = (
        CONFIGURED_CONNECTION_CAPACITY_ADEQUATE_REASON
    )
    smart_connection_capacity_recommendation_reason: str = (
        CONFIGURED_CONNECTION_CAPACITY_ADEQUATE_REASON
    )
    uncontrolled_capacity_exceedance_duration_hours: float = 0.0
    smart_capacity_exceedance_duration_hours: float = 0.0
    exceedance_duration_reduction_hours: float = 0.0
    uncontrolled_average_transformer_loading_percent: float = 0.0
    smart_average_transformer_loading_percent: float = 0.0
    average_transformer_loading_percent_difference: float = 0.0
    uncontrolled_peak_transformer_loading_percent: float = 0.0
    smart_peak_transformer_loading_percent: float = 0.0
    peak_transformer_loading_percent_difference: float = 0.0
    uncontrolled_transformer_overload_indicator: bool = False
    smart_transformer_overload_indicator: bool = False
    uncontrolled_transformer_overload_duration_hours: float = 0.0
    smart_transformer_overload_duration_hours: float = 0.0
    transformer_overload_duration_difference_hours: float = 0.0
    uncontrolled_transformer_maximum_overload_kw: float = 0.0
    smart_transformer_maximum_overload_kw: float = 0.0
    transformer_maximum_overload_difference_kw: float = 0.0
    uncontrolled_transformer_thermal_risk_level: str = "low"
    smart_transformer_thermal_risk_level: str = "low"
    uncontrolled_maximum_feeder_loading_percent: float = 0.0
    smart_maximum_feeder_loading_percent: float = 0.0
    maximum_feeder_loading_percent_difference: float = 0.0
    uncontrolled_feeder_overload_indicator: bool = False
    smart_feeder_overload_indicator: bool = False
    uncontrolled_overloaded_feeder_count: int = 0
    smart_overloaded_feeder_count: int = 0
    overloaded_feeder_count_difference: int = 0
    uncontrolled_highest_feeder_thermal_risk_level: str = "low"
    smart_highest_feeder_thermal_risk_level: str = "low"
    uncontrolled_peak_harmonic_risk_score: float = 0.0
    smart_peak_harmonic_risk_score: float = 0.0
    peak_harmonic_risk_score_difference: float = 0.0
    uncontrolled_average_harmonic_risk_score: float = 0.0
    smart_average_harmonic_risk_score: float = 0.0
    average_harmonic_risk_score_difference: float = 0.0
    uncontrolled_harmonic_risk_duration_hours: float = 0.0
    smart_harmonic_risk_duration_hours: float = 0.0
    harmonic_risk_duration_difference_hours: float = 0.0
    uncontrolled_harmonic_risk_level: str = "low"
    smart_harmonic_risk_level: str = "low"
    uncontrolled_harmonic_warning_indicator: bool = False
    smart_harmonic_warning_indicator: bool = False
    uncontrolled_peak_current_imbalance_percent: float = 0.0
    smart_peak_current_imbalance_percent: float = 0.0
    peak_current_imbalance_percent_difference: float = 0.0
    uncontrolled_average_current_imbalance_percent: float = 0.0
    smart_average_current_imbalance_percent: float = 0.0
    average_current_imbalance_percent_difference: float = 0.0
    uncontrolled_imbalance_duration_hours: float = 0.0
    smart_imbalance_duration_hours: float = 0.0
    imbalance_duration_difference_hours: float = 0.0
    uncontrolled_current_imbalance_risk_level: str = "low"
    smart_current_imbalance_risk_level: str = "low"
    uncontrolled_imbalance_warning_indicator: bool = False
    smart_imbalance_warning_indicator: bool = False
    uncontrolled_overall_pq_risk_score: float = 0.0
    smart_overall_pq_risk_score: float = 0.0
    overall_pq_risk_score_difference: float = 0.0
    uncontrolled_overall_pq_risk_level: str = "low"
    smart_overall_pq_risk_level: str = "low"
    uncontrolled_overall_pq_warning_indicator: bool = False
    smart_overall_pq_warning_indicator: bool = False
    uncontrolled_power_quality_warning_count: int = 0
    smart_power_quality_warning_count: int = 0
    power_quality_warning_count_difference: int = 0
    uncontrolled_power_quality_message: str = ""
    smart_power_quality_message: str = ""
    uncontrolled_average_charger_utilization_percent: float | None = 0.0
    smart_average_charger_utilization_percent: float | None = 0.0
    uncontrolled_peak_charger_utilization_percent: float | None = 0.0
    smart_peak_charger_utilization_percent: float | None = 0.0
    peak_charger_utilization_percent_difference: float | None = None
    uncontrolled_average_occupied_charger_count: float = 0.0
    smart_average_occupied_charger_count: float = 0.0
    average_occupied_charger_count_difference: float = 0.0
    uncontrolled_peak_occupied_charger_count: int = 0
    smart_peak_occupied_charger_count: int = 0
    peak_occupied_charger_count_difference: int = 0
    uncontrolled_charger_shortage_indicator: bool = False
    smart_charger_shortage_indicator: bool = False
    uncontrolled_queue_present_indicator: bool = False
    smart_queue_present_indicator: bool = False
    uncontrolled_maximum_queue_length: int = 0
    smart_maximum_queue_length: int = 0
    maximum_queue_length_difference: int = 0
    uncontrolled_average_queue_length: float = 0.0
    smart_average_queue_length: float = 0.0
    average_queue_length_difference: float = 0.0
    uncontrolled_queue_duration_hours: float = 0.0
    smart_queue_duration_hours: float = 0.0
    queue_duration_difference_hours: float = 0.0
    uncontrolled_average_waiting_time_hours: float | None = 0.0
    smart_average_waiting_time_hours: float | None = 0.0
    average_waiting_time_difference_hours: float | None = None
    uncontrolled_maximum_waiting_time_hours: float | None = 0.0
    smart_maximum_waiting_time_hours: float | None = 0.0
    maximum_waiting_time_difference_hours: float | None = None
    uncontrolled_vehicles_waiting_count: int = 0
    smart_vehicles_waiting_count: int = 0
    vehicles_waiting_count_difference: int = 0
    uncontrolled_vehicles_not_started_count: int = 0
    smart_vehicles_not_started_count: int = 0
    vehicles_not_started_count_difference: int = 0
    uncontrolled_vehicles_with_unmet_energy_count: int = 0
    smart_vehicles_with_unmet_energy_count: int = 0
    vehicles_with_unmet_energy_count_difference: int = 0
    uncontrolled_charger_capacity_vs_demand_balance: int = 0
    smart_charger_capacity_vs_demand_balance: int = 0
    charger_capacity_vs_demand_balance_difference: int = 0
    uncontrolled_required_charger_count: int | None = 0
    smart_required_charger_count: int | None = 0
    required_charger_count_difference: int | None = None
    uncontrolled_additional_chargers_required: int | None = 0
    smart_additional_chargers_required: int | None = 0
    additional_chargers_required_difference: int | None = None
    uncontrolled_primary_constraint_reason: str = "none"
    smart_primary_constraint_reason: str = "none"
    charger_expansion_avoided_by_smart: bool = False
    connection_upgrade_avoided_by_smart: bool = False
    service_rule_resolved_by_smart: bool = False
    service_rule_worsened_by_smart: bool = False
    infrastructure_recommendation_changed_by_smart: bool = False
    primary_constraint_shifted_by_smart: bool = False
    primary_constraint_shift_summary: str = ""
    service_impact_summary: str = ""
    infrastructure_impact_summary: str = ""
    uncontrolled_feeder_summary_rows: list[dict[str, object]] = field(
        default_factory=list
    )
    smart_feeder_summary_rows: list[dict[str, object]] = field(default_factory=list)
    uncontrolled_transformer_total_load_kw_by_timestep: list[float] = field(
        default_factory=list
    )
    smart_transformer_total_load_kw_by_timestep: list[float] = field(
        default_factory=list
    )
    uncontrolled_transformer_loading_percent_by_timestep: list[float] = field(
        default_factory=list
    )
    smart_transformer_loading_percent_by_timestep: list[float] = field(
        default_factory=list
    )
    uncontrolled_transformer_overload_kw_by_timestep: list[float] = field(
        default_factory=list
    )
    smart_transformer_overload_kw_by_timestep: list[float] = field(
        default_factory=list
    )
    uncontrolled_occupied_charger_count_by_timestep: list[int] = field(
        default_factory=list
    )
    smart_occupied_charger_count_by_timestep: list[int] = field(
        default_factory=list
    )
    uncontrolled_waiting_vehicle_count_by_timestep: list[int] = field(
        default_factory=list
    )
    smart_waiting_vehicle_count_by_timestep: list[int] = field(
        default_factory=list
    )
    uncontrolled_harmonic_risk_score_by_timestep: list[float] = field(
        default_factory=list
    )
    smart_harmonic_risk_score_by_timestep: list[float] = field(default_factory=list)
    uncontrolled_current_imbalance_percent_by_timestep: list[float] = field(
        default_factory=list
    )
    smart_current_imbalance_percent_by_timestep: list[float] = field(
        default_factory=list
    )
    uncontrolled_overall_pq_risk_score_by_timestep: list[float] = field(
        default_factory=list
    )
    smart_overall_pq_risk_score_by_timestep: list[float] = field(
        default_factory=list
    )
    uncontrolled_phase_a_load_kw_by_timestep: list[float] = field(
        default_factory=list
    )
    smart_phase_a_load_kw_by_timestep: list[float] = field(default_factory=list)
    uncontrolled_phase_b_load_kw_by_timestep: list[float] = field(
        default_factory=list
    )
    smart_phase_b_load_kw_by_timestep: list[float] = field(default_factory=list)
    uncontrolled_phase_c_load_kw_by_timestep: list[float] = field(
        default_factory=list
    )
    smart_phase_c_load_kw_by_timestep: list[float] = field(default_factory=list)


_COMPARISON_VALUE_FIELD_SPECS = (
    StrategyMetricFieldSpec(
        "required_connection_capacity_kw",
        difference_field="required_connection_capacity_difference_kw",
    ),
    StrategyMetricFieldSpec(
        "recommended_connection_capacity_kw",
        difference_field="recommended_connection_capacity_difference_kw",
    ),
    StrategyMetricFieldSpec("connection_capacity_recommendation_reason"),
    StrategyMetricFieldSpec(
        "capacity_exceedance_duration_hours",
        difference_field="exceedance_duration_reduction_hours",
    ),
    StrategyMetricFieldSpec(
        "average_transformer_loading_percent",
        difference_field="average_transformer_loading_percent_difference",
    ),
    StrategyMetricFieldSpec(
        "peak_transformer_loading_percent",
        difference_field="peak_transformer_loading_percent_difference",
    ),
    StrategyMetricFieldSpec("transformer_overload_indicator"),
    StrategyMetricFieldSpec(
        "transformer_overload_duration_hours",
        difference_field="transformer_overload_duration_difference_hours",
    ),
    StrategyMetricFieldSpec(
        "transformer_maximum_overload_kw",
        difference_field="transformer_maximum_overload_difference_kw",
    ),
    StrategyMetricFieldSpec("transformer_thermal_risk_level"),
    StrategyMetricFieldSpec(
        "maximum_feeder_loading_percent",
        difference_field="maximum_feeder_loading_percent_difference",
    ),
    StrategyMetricFieldSpec("feeder_overload_indicator"),
    StrategyMetricFieldSpec(
        "overloaded_feeder_count",
        difference_field="overloaded_feeder_count_difference",
    ),
    StrategyMetricFieldSpec("highest_feeder_thermal_risk_level"),
    StrategyMetricFieldSpec(
        "peak_harmonic_risk_score",
        difference_field="peak_harmonic_risk_score_difference",
    ),
    StrategyMetricFieldSpec(
        "average_harmonic_risk_score",
        difference_field="average_harmonic_risk_score_difference",
    ),
    StrategyMetricFieldSpec(
        "harmonic_risk_duration_hours",
        difference_field="harmonic_risk_duration_difference_hours",
    ),
    StrategyMetricFieldSpec("harmonic_risk_level"),
    StrategyMetricFieldSpec("harmonic_warning_indicator"),
    StrategyMetricFieldSpec(
        "peak_current_imbalance_percent",
        difference_field="peak_current_imbalance_percent_difference",
    ),
    StrategyMetricFieldSpec(
        "average_current_imbalance_percent",
        difference_field="average_current_imbalance_percent_difference",
    ),
    StrategyMetricFieldSpec(
        "imbalance_duration_hours",
        difference_field="imbalance_duration_difference_hours",
    ),
    StrategyMetricFieldSpec("current_imbalance_risk_level"),
    StrategyMetricFieldSpec("imbalance_warning_indicator"),
    StrategyMetricFieldSpec(
        "overall_pq_risk_score",
        difference_field="overall_pq_risk_score_difference",
    ),
    StrategyMetricFieldSpec("overall_pq_risk_level"),
    StrategyMetricFieldSpec("overall_pq_warning_indicator"),
    StrategyMetricFieldSpec(
        "power_quality_warning_count",
        difference_field="power_quality_warning_count_difference",
    ),
    StrategyMetricFieldSpec("power_quality_message"),
    StrategyMetricFieldSpec("average_charger_utilization_percent"),
    StrategyMetricFieldSpec(
        "peak_charger_utilization_percent",
        difference_field="peak_charger_utilization_percent_difference",
        difference_kind="defined",
    ),
    StrategyMetricFieldSpec(
        "average_occupied_charger_count",
        difference_field="average_occupied_charger_count_difference",
    ),
    StrategyMetricFieldSpec(
        "peak_occupied_charger_count",
        difference_field="peak_occupied_charger_count_difference",
    ),
    StrategyMetricFieldSpec("charger_shortage_indicator"),
    StrategyMetricFieldSpec("queue_present_indicator"),
    StrategyMetricFieldSpec(
        "maximum_queue_length",
        difference_field="maximum_queue_length_difference",
    ),
    StrategyMetricFieldSpec(
        "average_queue_length",
        difference_field="average_queue_length_difference",
    ),
    StrategyMetricFieldSpec(
        "queue_duration_hours",
        difference_field="queue_duration_difference_hours",
    ),
    StrategyMetricFieldSpec(
        "average_waiting_time_hours",
        difference_field="average_waiting_time_difference_hours",
        difference_kind="defined",
    ),
    StrategyMetricFieldSpec(
        "maximum_waiting_time_hours",
        difference_field="maximum_waiting_time_difference_hours",
        difference_kind="defined",
    ),
    StrategyMetricFieldSpec(
        "vehicles_waiting_count",
        difference_field="vehicles_waiting_count_difference",
    ),
    StrategyMetricFieldSpec(
        "vehicles_not_started_count",
        difference_field="vehicles_not_started_count_difference",
    ),
    StrategyMetricFieldSpec(
        "vehicles_with_unmet_energy_count",
        difference_field="vehicles_with_unmet_energy_count_difference",
    ),
    StrategyMetricFieldSpec(
        "charger_capacity_vs_demand_balance",
        difference_field="charger_capacity_vs_demand_balance_difference",
    ),
    StrategyMetricFieldSpec(
        "required_charger_count",
        difference_field="required_charger_count_difference",
        difference_kind="defined",
    ),
    StrategyMetricFieldSpec(
        "additional_chargers_required",
        difference_field="additional_chargers_required_difference",
        difference_kind="defined",
    ),
    StrategyMetricFieldSpec("primary_constraint_reason"),
    StrategyMetricFieldSpec(
        "feeder_summary_rows",
        copy_transform=copy_summary_rows_for_comparison,
    ),
    StrategyMetricFieldSpec(
        "transformer_total_load_kw_by_timestep",
        copy_transform=copy_metric_sequence,
    ),
    StrategyMetricFieldSpec(
        "transformer_loading_percent_by_timestep",
        copy_transform=copy_metric_sequence,
    ),
    StrategyMetricFieldSpec(
        "transformer_overload_kw_by_timestep",
        copy_transform=copy_metric_sequence,
    ),
    StrategyMetricFieldSpec(
        "occupied_charger_count_by_timestep",
        copy_transform=copy_metric_sequence,
    ),
    StrategyMetricFieldSpec(
        "waiting_vehicle_count_by_timestep",
        copy_transform=copy_metric_sequence,
    ),
    StrategyMetricFieldSpec(
        "harmonic_risk_score_by_timestep",
        copy_transform=copy_metric_sequence,
    ),
    StrategyMetricFieldSpec(
        "current_imbalance_percent_by_timestep",
        copy_transform=copy_metric_sequence,
    ),
    StrategyMetricFieldSpec(
        "overall_pq_risk_score_by_timestep",
        copy_transform=copy_metric_sequence,
    ),
    StrategyMetricFieldSpec(
        "phase_a_load_kw_by_timestep",
        copy_transform=copy_metric_sequence,
    ),
    StrategyMetricFieldSpec(
        "phase_b_load_kw_by_timestep",
        copy_transform=copy_metric_sequence,
    ),
    StrategyMetricFieldSpec(
        "phase_c_load_kw_by_timestep",
        copy_transform=copy_metric_sequence,
    ),
)


def calculate_comparison_metrics(
    uncontrolled: Metrics,
    smart: Metrics,
) -> ComparisonMetrics:
    """Calculate comparison KPIs from completed strategy metrics."""
    peak_reduction = uncontrolled.peak_load - smart.peak_load
    repeated_fields = build_strategy_metric_fields(
        uncontrolled,
        smart,
        _COMPARISON_VALUE_FIELD_SPECS,
    )
    required_connection_capacity_difference_kw = repeated_fields[
        "required_connection_capacity_difference_kw"
    ]
    recommended_connection_capacity_difference_kw = repeated_fields[
        "recommended_connection_capacity_difference_kw"
    ]
    connection_capacity_avoided_by_smart_kw = max(
        required_connection_capacity_difference_kw,
        0.0,
    )
    recommended_connection_capacity_avoided_by_smart_kw = max(
        recommended_connection_capacity_difference_kw,
        0.0,
    )
    uncontrolled_connection_upgrade_required = connection_upgrade_required(
        uncontrolled
    )
    smart_connection_upgrade_required = connection_upgrade_required(smart)
    connection_upgrade_avoided = connection_upgrade_avoided_by_smart(
        uncontrolled,
        smart,
    )
    infrastructure_recommendation_changed = (
        infrastructure_recommendation_changed_by_smart(
            uncontrolled,
            smart,
        )
    )

    return ComparisonMetrics(
        peak_reduction=peak_reduction,
        relative_peak_reduction=_calculate_relative_peak_reduction(
            peak_reduction,
            uncontrolled.peak_load,
        ),
        capacity_utilization_difference=(
            uncontrolled.capacity_utilization - smart.capacity_utilization
        ),
        unmet_energy_difference=uncontrolled.unmet_energy - smart.unmet_energy,
        peak_capacity_margin_improvement_kw=(
            smart.peak_capacity_margin_kw - uncontrolled.peak_capacity_margin_kw
        ),
        grid_capacity_status=_calculate_grid_capacity_status(
            uncontrolled,
            smart,
        ),
        connection_capacity_avoided_by_smart_kw=(
            connection_capacity_avoided_by_smart_kw
        ),
        recommended_connection_capacity_avoided_by_smart_kw=(
            recommended_connection_capacity_avoided_by_smart_kw
        ),
        uncontrolled_connection_upgrade_required=(
            uncontrolled_connection_upgrade_required
        ),
        smart_connection_upgrade_required=smart_connection_upgrade_required,
        uncontrolled_connection_capacity_adequate_indicator=(
            _connection_capacity_is_adequate(uncontrolled)
        ),
        smart_connection_capacity_adequate_indicator=(
            _connection_capacity_is_adequate(smart)
        ),
        charger_expansion_avoided_by_smart=(
            charger_expansion_avoided_by_smart(uncontrolled, smart)
        ),
        connection_upgrade_avoided_by_smart=connection_upgrade_avoided,
        service_rule_resolved_by_smart=(
            service_rule_resolved_by_smart(uncontrolled, smart)
        ),
        service_rule_worsened_by_smart=(
            service_rule_worsened_by_smart(uncontrolled, smart)
        ),
        infrastructure_recommendation_changed_by_smart=(
            infrastructure_recommendation_changed
        ),
        primary_constraint_shifted_by_smart=(
            primary_constraint_shifted_by_smart(uncontrolled, smart)
        ),
        primary_constraint_shift_summary=primary_constraint_shift_summary(
            uncontrolled,
            smart,
        ),
        service_impact_summary=service_impact_summary(
            uncontrolled,
            smart,
        ),
        infrastructure_impact_summary=infrastructure_impact_summary(
            uncontrolled,
            smart,
            connection_capacity_avoided_by_smart_kw=(
                connection_capacity_avoided_by_smart_kw
            ),
            recommended_connection_capacity_avoided_by_smart_kw=(
                recommended_connection_capacity_avoided_by_smart_kw
            ),
            connection_upgrade_avoided_by_smart=connection_upgrade_avoided,
            infrastructure_recommendation_changed_by_smart=(
                infrastructure_recommendation_changed
            ),
        ),
        **repeated_fields,
    )


def _calculate_relative_peak_reduction(
    peak_reduction: float,
    uncontrolled_peak_load: float,
) -> float:
    """Return peak reduction relative to uncontrolled peak load."""
    if uncontrolled_peak_load == 0.0:
        return 0.0

    return peak_reduction / uncontrolled_peak_load * PERCENT_MULTIPLIER


def _calculate_grid_capacity_status(
    uncontrolled: Metrics,
    smart: Metrics,
) -> str:
    """Summarize how smart charging changes modeled grid and capacity stress."""
    uncontrolled_has_constraint = _has_grid_capacity_constraint(uncontrolled)
    smart_has_constraint = _has_grid_capacity_constraint(smart)

    if not uncontrolled_has_constraint and not smart_has_constraint:
        return "No modeled constraint"

    if uncontrolled_has_constraint and not smart_has_constraint:
        return "Constraint resolved"

    if not uncontrolled_has_constraint and smart_has_constraint:
        return "Constraint worsened"

    uncontrolled_score = _grid_capacity_stress_score(uncontrolled)
    smart_score = _grid_capacity_stress_score(smart)

    if smart_score < uncontrolled_score:
        return "Constraint reduced"

    if smart_score > uncontrolled_score:
        return "Constraint worsened"

    return "Constraint unchanged"


def _has_grid_capacity_constraint(metrics: Metrics) -> bool:
    """Return whether any modeled connection or grid-asset stress is indicated."""
    return (
        not _connection_capacity_is_adequate(metrics)
        or metrics.transformer_overload_indicator
        or metrics.feeder_overload_indicator
        or metrics.transformer_thermal_risk_level != "low"
        or metrics.highest_feeder_thermal_risk_level != "low"
    )


def _grid_capacity_stress_score(metrics: Metrics) -> int:
    """Return a coarse severity score for modeled grid and capacity stress."""
    risk_score = 0
    if not _connection_capacity_is_adequate(metrics):
        risk_score += 5
    if metrics.transformer_overload_indicator:
        risk_score += 4
    if metrics.feeder_overload_indicator:
        risk_score += 3

    risk_score += _thermal_risk_score(metrics.transformer_thermal_risk_level)
    risk_score += _thermal_risk_score(metrics.highest_feeder_thermal_risk_level)
    return risk_score


def _thermal_risk_score(risk_level: str) -> int:
    """Map thermal risk labels to a coarse comparable severity score."""
    if risk_level == "high":
        return 2
    if risk_level == "moderate":
        return 1
    return 0


def _connection_capacity_is_adequate(metrics: Metrics) -> bool:
    """Return the planner-facing adequacy state with legacy fallback behavior."""
    if not metrics.connection_capacity_adequate_indicator:
        return False

    if (
        metrics.connection_capacity_recommendation_reason
        != CONFIGURED_CONNECTION_CAPACITY_ADEQUATE_REASON
    ):
        return False

    if connection_upgrade_required(metrics):
        return False

    if (
        metrics.primary_constraint_reason
        == GRID_CONNECTION_CAPACITY_CONSTRAINT_REASON
    ):
        return False

    return True
