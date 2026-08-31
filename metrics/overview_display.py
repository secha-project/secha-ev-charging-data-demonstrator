"""Prepared Overview display data for executive-summary dashboard views."""

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
from metrics.constraint_analysis import (
    CHARGER_AVAILABILITY_CONSTRAINT_REASON,
    MIXED_CONSTRAINT_REASON,
    format_primary_constraint_reason_label,
)
from metrics.metrics import Metrics
from metrics.shared import FLOATING_POINT_TOLERANCE
from metrics.planning import connection_upgrade_required, service_rule_is_met
from scenarios import Scenario


OVERVIEW_VALUE_FORMAT_TEXT = "text"
OVERVIEW_OUTCOME_FEASIBLE = "Feasible"
OVERVIEW_OUTCOME_UPGRADE_RECOMMENDED = "Upgrade Recommended"
OVERVIEW_OUTCOME_CHARGER_EXPANSION_RECOMMENDED = (
    "Charger Expansion Recommended"
)
OVERVIEW_OUTCOME_MULTIPLE_CONSTRAINTS = "Multiple Constraints"
OVERVIEW_OUTCOME_CONSTRAINED = "Constrained"


@dataclass(frozen=True)
class OverviewDisplayField:
    """Prepared field value for one Overview display surface."""

    label: str
    value: Any
    value_format: str


@dataclass(frozen=True)
class OverviewKpiDescriptor:
    """Prepared executive KPI descriptor for the Overview tab."""

    card_id: str
    title: str
    outcome: str
    headline: OverviewDisplayField
    supporting_fields: tuple[OverviewDisplayField, ...] = ()
    supporting_text: str | None = None


@dataclass(frozen=True)
class OverviewSmartChargingPreview:
    """Prepared compact Smart Charging preview for the Overview tab."""

    title: str
    outcome: str
    summary_title: str
    summary_value: str
    summary: str
    baseline: OverviewDisplayField
    comparison: OverviewDisplayField
    delta: OverviewDisplayField


@dataclass(frozen=True)
class OverviewDisplayData:
    """Prepared Overview executive-summary data derived from Metrics outputs."""

    kpis: tuple[OverviewKpiDescriptor, ...]
    smart_charging_preview: OverviewSmartChargingPreview


def prepare_overview_display_data(
    active_scenario: Scenario,
    active_metrics: Metrics,
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
    comparison_metrics: ComparisonMetrics,
) -> OverviewDisplayData:
    """Return prepared Overview display data from Metrics outputs only."""

    return OverviewDisplayData(
        kpis=(
            _prepare_scenario_outcome_kpi(active_metrics),
            _prepare_peak_load_kpi(active_metrics),
            _prepare_grid_connection_need_kpi(active_metrics),
            _prepare_charger_expansion_need_kpi(active_scenario, active_metrics),
        ),
        smart_charging_preview=_prepare_smart_charging_preview(
            uncontrolled_metrics,
            smart_metrics,
            comparison_metrics,
        ),
    )


def _prepare_scenario_outcome_kpi(
    active_metrics: Metrics,
) -> OverviewKpiDescriptor:
    outcome_label = _scenario_outcome_label(active_metrics)
    primary_bottleneck = _primary_bottleneck_text(active_metrics)
    recommendation_hint = _scenario_outcome_hint(active_metrics)

    return OverviewKpiDescriptor(
        card_id="scenario_outcome",
        title="Scenario Outcome",
        outcome=_scenario_outcome_tone(active_metrics),
        headline=OverviewDisplayField(
            label="Overall modeled outcome",
            value=outcome_label,
            value_format=OVERVIEW_VALUE_FORMAT_TEXT,
        ),
        supporting_fields=(
            OverviewDisplayField(
                label="Primary bottleneck",
                value=primary_bottleneck,
                value_format=OVERVIEW_VALUE_FORMAT_TEXT,
            ),
        ),
        supporting_text=recommendation_hint,
    )


def _prepare_peak_load_kpi(active_metrics: Metrics) -> OverviewKpiDescriptor:
    peak_outcome = (
        COMPARISON_OUTCOME_TRADE_OFF
        if not active_metrics.connection_capacity_adequate_indicator
        else COMPARISON_OUTCOME_NEUTRAL
    )
    return OverviewKpiDescriptor(
        card_id="peak_load",
        title="Peak Load",
        outcome=peak_outcome,
        headline=OverviewDisplayField(
            label="Maximum charging demand",
            value=active_metrics.peak_load,
            value_format="power_kw",
        ),
        supporting_fields=(
            OverviewDisplayField(
                label="Capacity utilization",
                value=active_metrics.capacity_utilization,
                value_format="percent",
            ),
            OverviewDisplayField(
                label="Configured capacity",
                value=active_metrics.configured_connection_capacity_kw,
                value_format="power_kw",
            ),
        ),
    )


def _prepare_grid_connection_need_kpi(
    active_metrics: Metrics,
) -> OverviewKpiDescriptor:
    recommended_capacity = active_metrics.recommended_connection_capacity_kw
    configured_capacity = active_metrics.configured_connection_capacity_kw
    recommended_gap_kw = max(
        recommended_capacity - configured_capacity,
        0.0,
    )

    return OverviewKpiDescriptor(
        card_id="grid_connection_need",
        title="Grid Connection Need",
        outcome=_grid_connection_need_outcome(active_metrics),
        headline=OverviewDisplayField(
            label="Planner recommendation",
            value=recommended_capacity,
            value_format="power_kw",
        ),
        supporting_fields=(
            OverviewDisplayField(
                label="Current capacity",
                value=configured_capacity,
                value_format="power_kw",
            ),
            OverviewDisplayField(
                label="Required increase",
                value=recommended_gap_kw,
                value_format="power_kw_signed",
            ),
        ),
    )


def _prepare_charger_expansion_need_kpi(
    active_scenario: Scenario,
    active_metrics: Metrics,
) -> OverviewKpiDescriptor:
    additional_required = active_metrics.additional_chargers_required
    required_count = active_metrics.required_charger_count
    if additional_required is None or required_count is None:
        return OverviewKpiDescriptor(
            card_id="charger_expansion_need",
            title="Charger Expansion Need",
            outcome=COMPARISON_OUTCOME_NEUTRAL,
            headline=OverviewDisplayField(
                label="Planning signal",
                value="Not the primary constraint",
                value_format=OVERVIEW_VALUE_FORMAT_TEXT,
            ),
            supporting_fields=(
                OverviewDisplayField(
                    label="Current chargers",
                    value=active_scenario.charger_count,
                    value_format="charger_count_0",
                ),
            ),
        )

    return OverviewKpiDescriptor(
        card_id="charger_expansion_need",
        title="Charger Expansion Need",
        outcome=(
            COMPARISON_OUTCOME_TRADE_OFF
            if additional_required > 0
            else COMPARISON_OUTCOME_IMPROVEMENT
        ),
        headline=OverviewDisplayField(
            label="Additional chargers required",
            value=additional_required,
            value_format="charger_count_0",
        ),
        supporting_fields=(
            OverviewDisplayField(
                label="Current chargers",
                value=active_scenario.charger_count,
                value_format="charger_count_0",
            ),
            OverviewDisplayField(
                label="Required chargers",
                value=required_count,
                value_format="charger_count_0",
            ),
        ),
    )


def _prepare_smart_charging_preview(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
    comparison_metrics: ComparisonMetrics,
) -> OverviewSmartChargingPreview:
    delta_value = normalize_numeric_delta_for_display(
        comparison_metrics.peak_reduction,
        "power_kw_signed",
    )
    summary = _smart_charging_summary_text(comparison_metrics)
    return OverviewSmartChargingPreview(
        title="Smart Charging Impact",
        outcome=_smart_charging_delta_outcome(
            comparison_metrics.peak_reduction,
            baseline_value=uncontrolled_metrics.peak_load,
            relative_change_percent=comparison_metrics.relative_peak_reduction,
        ),
        summary_title=_smart_charging_summary_title(comparison_metrics),
        summary_value=_smart_charging_summary_value_text(comparison_metrics),
        summary=summary,
        baseline=OverviewDisplayField(
            label="Uncontrolled peak load",
            value=uncontrolled_metrics.peak_load,
            value_format="power_kw",
        ),
        comparison=OverviewDisplayField(
            label="Smart Charging peak load",
            value=smart_metrics.peak_load,
            value_format="power_kw",
        ),
        delta=OverviewDisplayField(
            label="Peak reduction",
            value=delta_value,
            value_format="power_kw_signed",
        ),
    )


def _scenario_outcome_label(active_metrics: Metrics) -> str:
    service_rule_met = service_rule_is_met(active_metrics)
    connection_adequate = active_metrics.connection_capacity_adequate_indicator

    if service_rule_met and connection_adequate:
        return OVERVIEW_OUTCOME_FEASIBLE

    if (
        active_metrics.primary_constraint_reason == MIXED_CONSTRAINT_REASON
        or (not service_rule_met and not connection_adequate)
    ):
        return OVERVIEW_OUTCOME_MULTIPLE_CONSTRAINTS

    if not connection_adequate:
        return OVERVIEW_OUTCOME_UPGRADE_RECOMMENDED

    if (
        active_metrics.primary_constraint_reason
        == CHARGER_AVAILABILITY_CONSTRAINT_REASON
        and active_metrics.additional_chargers_required not in (None, 0)
    ):
        return OVERVIEW_OUTCOME_CHARGER_EXPANSION_RECOMMENDED

    return OVERVIEW_OUTCOME_CONSTRAINED


def _scenario_outcome_tone(active_metrics: Metrics) -> str:
    if _scenario_outcome_label(active_metrics) == OVERVIEW_OUTCOME_FEASIBLE:
        return COMPARISON_OUTCOME_IMPROVEMENT
    return COMPARISON_OUTCOME_TRADE_OFF


def _scenario_outcome_hint(active_metrics: Metrics) -> str:
    outcome_label = _scenario_outcome_label(active_metrics)
    if outcome_label == OVERVIEW_OUTCOME_FEASIBLE:
        return "Daily charging demand can be served within the modeled limits."
    if outcome_label == OVERVIEW_OUTCOME_UPGRADE_RECOMMENDED:
        return "Connection-capacity review is the main next planning action."
    if outcome_label == OVERVIEW_OUTCOME_CHARGER_EXPANSION_RECOMMENDED:
        return "Charger availability is the main next planning action."
    if outcome_label == OVERVIEW_OUTCOME_MULTIPLE_CONSTRAINTS:
        return "More than one modeled bottleneck should be addressed."
    return "The scenario remains constrained under current assumptions."


def _primary_bottleneck_text(active_metrics: Metrics) -> str:
    if active_metrics.primary_constraint_reason == "none":
        return "No primary bottleneck indicated"
    return format_primary_constraint_reason_label(
        active_metrics.primary_constraint_reason
    )


def _smart_charging_delta_outcome(
    peak_reduction_kw: float | int | None,
    *,
    baseline_value: float | int,
    relative_change_percent: float | None,
) -> str:
    normalized_delta = normalize_numeric_delta_for_display(
        peak_reduction_kw,
        "power_kw_signed",
    )
    if not is_numeric_change_material(
        peak_reduction_kw,
        absolute_materiality_threshold=default_materiality_threshold(
            "power_kw_signed"
        ),
        relative_materiality_threshold=0.1,
        relative_change_percent=relative_change_percent,
        baseline_value=baseline_value,
    ):
        return COMPARISON_OUTCOME_NEUTRAL

    return classify_directional_outcome(normalized_delta, "higher")


def _smart_charging_summary_text(comparison_metrics: ComparisonMetrics) -> str:
    peak_reduction_kw = comparison_metrics.peak_reduction
    relative_peak_reduction = comparison_metrics.relative_peak_reduction
    if _smart_charging_delta_outcome(
        peak_reduction_kw,
        baseline_value=_resolve_peak_reduction_baseline_value(comparison_metrics),
        relative_change_percent=relative_peak_reduction,
    ) == COMPARISON_OUTCOME_IMPROVEMENT:
        return (
            "Smart Charging reduces peak demand by "
            f"{_format_power_kw_text(abs(peak_reduction_kw))} "
            f"({_format_percent_text(abs(relative_peak_reduction))})."
        )

    if _smart_charging_delta_outcome(
        peak_reduction_kw,
        baseline_value=_resolve_peak_reduction_baseline_value(comparison_metrics),
        relative_change_percent=relative_peak_reduction,
    ) == COMPARISON_OUTCOME_TRADE_OFF:
        return (
            "Smart Charging increases peak demand by "
            f"{_format_power_kw_text(abs(peak_reduction_kw))} "
            f"({_format_percent_text(abs(relative_peak_reduction))})."
        )

    return "Smart Charging shows limited additional peak-demand benefit."


def _format_power_kw_text(value: float) -> str:
    return f"{value:,.1f} kW"


def _format_percent_text(value: float) -> str:
    return f"{value:,.1f}%"


def _grid_connection_need_outcome(active_metrics: Metrics) -> str:
    if connection_upgrade_required(active_metrics):
        return COMPARISON_OUTCOME_TRADE_OFF

    if _requested_peak_exceeds_current_capacity(active_metrics):
        return COMPARISON_OUTCOME_NEUTRAL

    return COMPARISON_OUTCOME_IMPROVEMENT


def _requested_peak_exceeds_current_capacity(active_metrics: Metrics) -> bool:
    return active_metrics.required_connection_capacity_kw > (
        active_metrics.configured_connection_capacity_kw
        + FLOATING_POINT_TOLERANCE
    )


def _resolve_peak_reduction_baseline_value(
    comparison_metrics: ComparisonMetrics,
) -> float:
    baseline_from_relative = comparison_metrics.uncontrolled_required_connection_capacity_kw
    peak_reduction_kw = comparison_metrics.peak_reduction
    relative_peak_reduction = comparison_metrics.relative_peak_reduction

    if (
        peak_reduction_kw not in (None, 0, 0.0)
        and relative_peak_reduction not in (None, 0, 0.0)
    ):
        inferred_baseline = abs(peak_reduction_kw) / abs(relative_peak_reduction / 100.0)
        if inferred_baseline > 0.0:
            return inferred_baseline

    return baseline_from_relative


def _smart_charging_summary_title(
    comparison_metrics: ComparisonMetrics,
) -> str:
    if _smart_charging_delta_outcome(
        comparison_metrics.peak_reduction,
        baseline_value=_resolve_peak_reduction_baseline_value(comparison_metrics),
        relative_change_percent=comparison_metrics.relative_peak_reduction,
    ) == COMPARISON_OUTCOME_TRADE_OFF:
        return "Peak Increase"

    return "Peak Reduction"


def _smart_charging_summary_value_text(
    comparison_metrics: ComparisonMetrics,
) -> str:
    peak_delta_kw = abs(comparison_metrics.peak_reduction or 0.0)
    relative_delta_percent = abs(comparison_metrics.relative_peak_reduction or 0.0)
    return (
        f"{_format_power_kw_text(peak_delta_kw)} "
        f"({_format_percent_text(relative_delta_percent)})"
    )
