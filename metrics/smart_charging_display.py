"""Prepared Smart Charging card data for dashboard views."""

from dataclasses import dataclass
from typing import Any

from metrics.comparison import ComparisonMetrics
from metrics.comparison_semantics import (
    COMPARISON_OUTCOME_IMPROVEMENT,
    COMPARISON_OUTCOME_NEUTRAL,
    COMPARISON_OUTCOME_TRADE_OFF,
    classify_directional_outcome,
    default_materiality_threshold,
    is_numeric_change_material,
    normalize_numeric_delta_for_display,
)
from metrics.metrics import Metrics
from metrics.planning import (
    NO_MODELED_SERVICE_PRESSURE_SUMMARY,
    QUEUE_PRESSURE_REDUCED_SUMMARY,
    QUEUE_PRESSURE_WORSENED_SUMMARY,
    SERVICE_PRESSURE_UNCHANGED_SUMMARY,
    SERVICE_RULE_RESOLVED_SUMMARY,
    SERVICE_RULE_WORSENED_SUMMARY,
    SERVICE_SHORTFALL_REDUCED_SUMMARY,
    SERVICE_SHORTFALL_WORSENED_SUMMARY,
    SERVICE_TRADEOFF_CHANGED_SUMMARY,
    WAITING_REDUCED_SUMMARY,
    WAITING_WORSENED_SUMMARY,
)


SMART_CHARGING_VALUE_FORMAT_TEXT = "text"
SMART_CHARGING_DISPLAY_DELTA_DIRECTION = "higher"


@dataclass(frozen=True)
class SmartChargingCardField:
    """Prepared field value for one Smart Charging card row."""

    label: str
    value: Any
    value_format: str


@dataclass(frozen=True)
class SmartChargingCardDescriptor:
    """Prepared Smart Charging KPI card descriptor."""

    card_id: str
    title: str
    outcome: str
    delta: SmartChargingCardField
    before: SmartChargingCardField
    after: SmartChargingCardField
    supporting_text: str | None = None


def prepare_smart_charging_card_descriptors(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
    comparison_metrics: ComparisonMetrics,
) -> tuple[SmartChargingCardDescriptor, ...]:
    """Return prepared Smart Charging executive-card descriptors."""

    return (
        _prepare_peak_load_card(uncontrolled_metrics, smart_metrics, comparison_metrics),
        _prepare_required_connection_capacity_card(
            uncontrolled_metrics,
            smart_metrics,
            comparison_metrics,
        ),
        _prepare_peak_transformer_loading_card(
            uncontrolled_metrics,
            smart_metrics,
            comparison_metrics,
        ),
        _prepare_service_impact_card(comparison_metrics),
        _prepare_power_quality_impact_card(comparison_metrics),
        _prepare_grid_infrastructure_card(
            uncontrolled_metrics,
            smart_metrics,
            comparison_metrics,
        ),
    )


def _prepare_peak_load_card(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
    comparison_metrics: ComparisonMetrics,
) -> SmartChargingCardDescriptor:
    delta_value, outcome = _classify_numeric_uncontrolled_minus_smart_delta(
        comparison_metrics.peak_reduction,
        "power_kw_signed",
        baseline_value=uncontrolled_metrics.peak_load,
        relative_change_percent=comparison_metrics.relative_peak_reduction,
        relative_materiality_threshold=0.1,
    )
    return SmartChargingCardDescriptor(
        card_id="peak_load",
        title="Peak Load",
        outcome=outcome,
        delta=SmartChargingCardField(
            label="Uncontrolled - Smart",
            value=delta_value,
            value_format="power_kw_signed",
        ),
        before=SmartChargingCardField(
            label="Uncontrolled",
            value=uncontrolled_metrics.peak_load,
            value_format="power_kw",
        ),
        after=SmartChargingCardField(
            label="Smart Charging",
            value=smart_metrics.peak_load,
            value_format="power_kw",
        ),
    )


def _prepare_required_connection_capacity_card(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
    comparison_metrics: ComparisonMetrics,
) -> SmartChargingCardDescriptor:
    delta_value, outcome = _classify_numeric_uncontrolled_minus_smart_delta(
        comparison_metrics.required_connection_capacity_difference_kw,
        "power_kw_signed",
        baseline_value=uncontrolled_metrics.required_connection_capacity_kw,
    )
    return SmartChargingCardDescriptor(
        card_id="required_connection_capacity",
        title="Required Connection Capacity",
        outcome=outcome,
        delta=SmartChargingCardField(
            label="Uncontrolled - Smart",
            value=delta_value,
            value_format="power_kw_signed",
        ),
        before=SmartChargingCardField(
            label="Uncontrolled",
            value=uncontrolled_metrics.required_connection_capacity_kw,
            value_format="power_kw",
        ),
        after=SmartChargingCardField(
            label="Smart Charging",
            value=smart_metrics.required_connection_capacity_kw,
            value_format="power_kw",
        ),
    )


def _prepare_peak_transformer_loading_card(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
    comparison_metrics: ComparisonMetrics,
) -> SmartChargingCardDescriptor:
    delta_value, outcome = _classify_numeric_uncontrolled_minus_smart_delta(
        comparison_metrics.peak_transformer_loading_percent_difference,
        "percentage_points_signed",
        baseline_value=uncontrolled_metrics.peak_transformer_loading_percent,
    )
    return SmartChargingCardDescriptor(
        card_id="peak_transformer_loading",
        title="Peak Transformer Loading",
        outcome=outcome,
        delta=SmartChargingCardField(
            label="Uncontrolled - Smart",
            value=delta_value,
            value_format="percentage_points_signed",
        ),
        before=SmartChargingCardField(
            label="Uncontrolled",
            value=uncontrolled_metrics.peak_transformer_loading_percent,
            value_format="percent",
        ),
        after=SmartChargingCardField(
            label="Smart Charging",
            value=smart_metrics.peak_transformer_loading_percent,
            value_format="percent",
        ),
    )


def _prepare_service_impact_card(
    comparison_metrics: ComparisonMetrics,
) -> SmartChargingCardDescriptor:
    waiting_delta_value, waiting_outcome = _classify_smart_charging_displayed_delta(
        comparison_metrics.average_waiting_time_difference_hours,
        "hours_signed",
        baseline_value=comparison_metrics.uncontrolled_average_waiting_time_hours or 0.0,
    )

    if waiting_outcome != COMPARISON_OUTCOME_NEUTRAL:
        delta = SmartChargingCardField(
            label="Uncontrolled - Smart waiting",
            value=waiting_delta_value,
            value_format="hours_signed",
        )
        outcome = waiting_outcome
    else:
        summary_value = _service_delta_summary(comparison_metrics)
        delta = SmartChargingCardField(
            label="Prepared planner-facing summary",
            value=summary_value,
            value_format=SMART_CHARGING_VALUE_FORMAT_TEXT,
        )
        outcome = _service_summary_outcome(comparison_metrics, summary_value)

    return SmartChargingCardDescriptor(
        card_id="service_impact",
        title="Service Impact",
        outcome=outcome,
        delta=delta,
        before=SmartChargingCardField(
            label="Uncontrolled",
            value=_service_state_text(
                queue_present=comparison_metrics.uncontrolled_queue_present_indicator,
                maximum_queue_length=comparison_metrics.uncontrolled_maximum_queue_length,
                average_waiting_time_hours=(
                    comparison_metrics.uncontrolled_average_waiting_time_hours
                ),
            ),
            value_format=SMART_CHARGING_VALUE_FORMAT_TEXT,
        ),
        after=SmartChargingCardField(
            label="Smart Charging",
            value=_service_state_text(
                queue_present=comparison_metrics.smart_queue_present_indicator,
                maximum_queue_length=comparison_metrics.smart_maximum_queue_length,
                average_waiting_time_hours=(
                    comparison_metrics.smart_average_waiting_time_hours
                ),
            ),
            value_format=SMART_CHARGING_VALUE_FORMAT_TEXT,
        ),
        supporting_text=_service_supporting_text(comparison_metrics),
    )


def _prepare_grid_infrastructure_card(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
    comparison_metrics: ComparisonMetrics,
) -> SmartChargingCardDescriptor:
    delta_value = comparison_metrics.grid_capacity_status
    outcome = _grid_status_outcome(comparison_metrics.grid_capacity_status)
    return SmartChargingCardDescriptor(
        card_id="grid_infrastructure_status",
        title="Grid / Infrastructure Status",
        outcome=outcome,
        delta=SmartChargingCardField(
            label="Prepared planner-facing summary",
            value=delta_value,
            value_format=SMART_CHARGING_VALUE_FORMAT_TEXT,
        ),
        before=SmartChargingCardField(
            label="Uncontrolled",
            value=_grid_state_text(
                adequacy_indicator=(
                    comparison_metrics.uncontrolled_connection_capacity_adequate_indicator
                ),
                peak_transformer_loading_percent=(
                    uncontrolled_metrics.peak_transformer_loading_percent
                ),
                maximum_feeder_loading_percent=(
                    uncontrolled_metrics.maximum_feeder_loading_percent
                ),
            ),
            value_format=SMART_CHARGING_VALUE_FORMAT_TEXT,
        ),
        after=SmartChargingCardField(
            label="Smart Charging",
            value=_grid_state_text(
                adequacy_indicator=(
                    comparison_metrics.smart_connection_capacity_adequate_indicator
                ),
                peak_transformer_loading_percent=smart_metrics.peak_transformer_loading_percent,
                maximum_feeder_loading_percent=smart_metrics.maximum_feeder_loading_percent,
            ),
            value_format=SMART_CHARGING_VALUE_FORMAT_TEXT,
        ),
        supporting_text=comparison_metrics.infrastructure_impact_summary or None,
    )


def _classify_smart_charging_displayed_delta(
    delta_value: float | int | None,
    change_format: str,
    *,
    baseline_value: float | int,
    relative_change_percent: float | None = None,
    relative_materiality_threshold: float | None = None,
) -> tuple[float | int | None, str]:
    """Return outcome based on the displayed Smart Charging delta convention."""

    normalized_delta = normalize_numeric_delta_for_display(delta_value, change_format)
    material = is_numeric_change_material(
        delta_value,
        absolute_materiality_threshold=default_materiality_threshold(change_format),
        relative_materiality_threshold=relative_materiality_threshold,
        relative_change_percent=relative_change_percent,
        baseline_value=baseline_value,
    )
    if not material:
        return normalized_delta, COMPARISON_OUTCOME_NEUTRAL

    return normalized_delta, classify_directional_outcome(
        normalized_delta,
        SMART_CHARGING_DISPLAY_DELTA_DIRECTION,
    )


def _prepare_power_quality_impact_card(
    comparison_metrics: ComparisonMetrics,
) -> SmartChargingCardDescriptor:
    if _power_quality_low_in_both(comparison_metrics):
        delta = SmartChargingCardField(
            label="Prepared planner-facing summary",
            value="Low risk in both",
            value_format=SMART_CHARGING_VALUE_FORMAT_TEXT,
        )
        outcome = COMPARISON_OUTCOME_NEUTRAL
    elif _power_quality_unchanged(comparison_metrics):
        delta = SmartChargingCardField(
            label="Prepared planner-facing summary",
            value="PQ impact unchanged",
            value_format=SMART_CHARGING_VALUE_FORMAT_TEXT,
        )
        outcome = COMPARISON_OUTCOME_NEUTRAL
    else:
        score_difference_value, outcome = _classify_smart_charging_displayed_delta(
            comparison_metrics.overall_pq_risk_score_difference,
            "score_points_signed",
            baseline_value=comparison_metrics.uncontrolled_overall_pq_risk_score,
        )
        delta = SmartChargingCardField(
            label="Uncontrolled - Smart PQ score",
            value=score_difference_value,
            value_format="score_points_signed",
        )

    return SmartChargingCardDescriptor(
        card_id="power_quality_impact",
        title="Power Quality Impact",
        outcome=outcome,
        delta=delta,
        before=SmartChargingCardField(
            label="Uncontrolled",
            value=_power_quality_state_text(
                comparison_metrics.uncontrolled_overall_pq_risk_level,
                comparison_metrics.uncontrolled_power_quality_warning_count,
                comparison_metrics.uncontrolled_overall_pq_risk_score,
            ),
            value_format=SMART_CHARGING_VALUE_FORMAT_TEXT,
        ),
        after=SmartChargingCardField(
            label="Smart Charging",
            value=_power_quality_state_text(
                comparison_metrics.smart_overall_pq_risk_level,
                comparison_metrics.smart_power_quality_warning_count,
                comparison_metrics.smart_overall_pq_risk_score,
            ),
            value_format=SMART_CHARGING_VALUE_FORMAT_TEXT,
        ),
        supporting_text=(
            "Message "
            f"{comparison_metrics.uncontrolled_power_quality_message} -> "
            f"{comparison_metrics.smart_power_quality_message}"
            if comparison_metrics.uncontrolled_power_quality_message
            or comparison_metrics.smart_power_quality_message
            else None
        ),
    )


def _classify_numeric_uncontrolled_minus_smart_delta(
    delta_value: float | int | None,
    change_format: str,
    *,
    baseline_value: float | int,
    relative_change_percent: float | None = None,
    relative_materiality_threshold: float | None = None,
) -> tuple[float | int | None, str]:
    """Return normalized delta and semantic outcome for U-S numeric comparisons."""

    return _classify_smart_charging_displayed_delta(
        delta_value,
        change_format,
        baseline_value=baseline_value,
        relative_change_percent=relative_change_percent,
        relative_materiality_threshold=relative_materiality_threshold,
    )


def _service_delta_summary(comparison_metrics: ComparisonMetrics) -> str:
    summary = comparison_metrics.service_impact_summary
    if summary:
        return summary

    queue_present_changed = (
        comparison_metrics.uncontrolled_queue_present_indicator
        != comparison_metrics.smart_queue_present_indicator
    )
    maximum_queue_difference = comparison_metrics.maximum_queue_length_difference
    if (
        comparison_metrics.uncontrolled_queue_present_indicator
        and not comparison_metrics.smart_queue_present_indicator
    ):
        return "Queue resolved"
    if (
        not comparison_metrics.uncontrolled_queue_present_indicator
        and comparison_metrics.smart_queue_present_indicator
    ):
        return "Queue introduced"
    if maximum_queue_difference > 0:
        return "Queue reduced"
    if maximum_queue_difference < 0:
        return "Queue worsened"
    if queue_present_changed:
        return "Queue pattern changed"
    return "Service unchanged"


def _service_summary_outcome(
    comparison_metrics: ComparisonMetrics,
    summary_value: str,
) -> str:
    if comparison_metrics.service_rule_resolved_by_smart:
        return COMPARISON_OUTCOME_IMPROVEMENT
    if comparison_metrics.service_rule_worsened_by_smart:
        return COMPARISON_OUTCOME_TRADE_OFF
    if summary_value in {
        SERVICE_RULE_RESOLVED_SUMMARY,
        SERVICE_SHORTFALL_REDUCED_SUMMARY,
        WAITING_REDUCED_SUMMARY,
        QUEUE_PRESSURE_REDUCED_SUMMARY,
        "Queue resolved",
        "Queue reduced",
    }:
        return COMPARISON_OUTCOME_IMPROVEMENT
    if summary_value in {
        SERVICE_RULE_WORSENED_SUMMARY,
        SERVICE_TRADEOFF_CHANGED_SUMMARY,
        SERVICE_SHORTFALL_WORSENED_SUMMARY,
        WAITING_WORSENED_SUMMARY,
        QUEUE_PRESSURE_WORSENED_SUMMARY,
        "Queue introduced",
        "Queue worsened",
        "Queue pattern changed",
    }:
        return COMPARISON_OUTCOME_TRADE_OFF
    if summary_value in {
        NO_MODELED_SERVICE_PRESSURE_SUMMARY,
        SERVICE_PRESSURE_UNCHANGED_SUMMARY,
        "Service unchanged",
    }:
        return COMPARISON_OUTCOME_NEUTRAL

    shortfall_delta = normalize_numeric_delta_for_display(
        comparison_metrics.vehicles_not_started_count_difference,
        "vehicle_count_0_signed",
    )
    if shortfall_delta not in (None, 0, 0.0):
        return classify_directional_outcome(shortfall_delta, "higher")

    unmet_vehicle_delta = normalize_numeric_delta_for_display(
        comparison_metrics.vehicles_with_unmet_energy_count_difference,
        "vehicle_count_0_signed",
    )
    if unmet_vehicle_delta not in (None, 0, 0.0):
        return classify_directional_outcome(unmet_vehicle_delta, "higher")

    queue_delta = normalize_numeric_delta_for_display(
        comparison_metrics.maximum_queue_length_difference,
        "vehicle_count_0_signed",
    )
    if queue_delta not in (None, 0, 0.0):
        return classify_directional_outcome(queue_delta, "higher")

    queue_presence_delta = int(
        comparison_metrics.uncontrolled_queue_present_indicator
    ) - int(comparison_metrics.smart_queue_present_indicator)
    return classify_directional_outcome(queue_presence_delta, "higher")


def _service_state_text(
    *,
    queue_present: bool,
    maximum_queue_length: int,
    average_waiting_time_hours: float | None,
) -> str:
    return (
        f"Queue present: {'Yes' if queue_present else 'No'}; "
        f"Max queue: {maximum_queue_length}; "
        f"Avg wait: {average_waiting_time_hours}"
    )


def _service_supporting_text(comparison_metrics: ComparisonMetrics) -> str:
    return (
        "Not started "
        f"{comparison_metrics.uncontrolled_vehicles_not_started_count} -> "
        f"{comparison_metrics.smart_vehicles_not_started_count}; "
        "Unmet vehicles "
        f"{comparison_metrics.uncontrolled_vehicles_with_unmet_energy_count} -> "
        f"{comparison_metrics.smart_vehicles_with_unmet_energy_count}"
    )


def _power_quality_low_in_both(comparison_metrics: ComparisonMetrics) -> bool:
    return (
        comparison_metrics.uncontrolled_overall_pq_risk_level == "low"
        and comparison_metrics.smart_overall_pq_risk_level == "low"
        and comparison_metrics.uncontrolled_power_quality_warning_count == 0
        and comparison_metrics.smart_power_quality_warning_count == 0
    )


def _power_quality_unchanged(comparison_metrics: ComparisonMetrics) -> bool:
    return (
        comparison_metrics.uncontrolled_overall_pq_risk_level
        == comparison_metrics.smart_overall_pq_risk_level
        and comparison_metrics.power_quality_warning_count_difference == 0
        and abs(comparison_metrics.overall_pq_risk_score_difference) < 1.0
    )


def _power_quality_state_text(
    risk_level: str,
    warning_count: int,
    risk_score: float,
) -> str:
    return (
        f"Level: {risk_level}; Warnings: {warning_count}; Score: {risk_score}"
    )


def _grid_state_text(
    *,
    adequacy_indicator: bool,
    peak_transformer_loading_percent: float,
    maximum_feeder_loading_percent: float,
) -> str:
    return (
        f"Adequacy: {'Adequate' if adequacy_indicator else 'Not adequate'}; "
        f"Transformer: {peak_transformer_loading_percent}; "
        f"Feeder: {maximum_feeder_loading_percent}"
    )


def _grid_status_outcome(grid_capacity_status: str) -> str:
    if grid_capacity_status in {"Constraint resolved", "Constraint reduced"}:
        return classify_directional_outcome(
            1.0,
            SMART_CHARGING_DISPLAY_DELTA_DIRECTION,
        )
    if grid_capacity_status == "Constraint worsened":
        return classify_directional_outcome(
            -1.0,
            SMART_CHARGING_DISPLAY_DELTA_DIRECTION,
        )
    return COMPARISON_OUTCOME_NEUTRAL

