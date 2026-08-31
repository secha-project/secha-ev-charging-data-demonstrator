"""Prepared Scenario A/B comparison display data for dashboard views."""

from dataclasses import dataclass, field, replace
from typing import Any

from metrics.comparison_semantics import (
    COMPARISON_OUTCOME_IMPROVEMENT,
    COMPARISON_OUTCOME_NEUTRAL,
    COMPARISON_OUTCOME_TRADE_OFF,
    classify_directional_outcome,
    default_materiality_threshold,
    is_numeric_change_material,
    normalize_numeric_delta_for_display,
    relative_shift_percent,
)
from metrics.metrics import Metrics
from metrics.scenario_difference import ScenarioComparisonMetrics


SCENARIO_VALUE_REQUIRED = "required"
SCENARIO_VALUE_OPTIONAL_UNAVAILABLE = "optional_unavailable"
SCENARIO_VALUE_OPTIONAL_NOT_APPLICABLE = "optional_not_applicable"
SCENARIO_CHANGE_DELTA = "delta"
SCENARIO_CHANGE_OPTIONAL_DELTA = "optional_delta"
SCENARIO_CHANGE_NOT_APPLICABLE = "not_applicable"
SCENARIO_CHANGE_NONE = "none"
SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT = COMPARISON_OUTCOME_IMPROVEMENT
SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF = COMPARISON_OUTCOME_TRADE_OFF
SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL = COMPARISON_OUTCOME_NEUTRAL
SCENARIO_SECTION_SUMMARY_MAJOR_CHANGES = "major_changes"
SCENARIO_SECTION_SUMMARY_TRADE_OFFS = "trade_offs"
SCENARIO_SECTION_SUMMARY_LITTLE_NO_CHANGE = "little_no_change"
SCENARIO_SECTION_IMPACT_MAJOR = "major"
SCENARIO_SECTION_IMPACT_MINOR = "minor"
SCENARIO_SECTION_IMPACT_NONE = "none"
SCENARIO_SECTION_VISUALIZATION_NONE = "none"
SCENARIO_SECTION_VISUALIZATION_SUPPORTING_WHEN_USEFUL = (
    "supporting_when_useful"
)
SCENARIO_SEMANTIC_PRIORITY_LOW = 1
SCENARIO_SEMANTIC_PRIORITY_MEDIUM = 2
SCENARIO_SEMANTIC_PRIORITY_HIGH = 3
SCENARIO_SEMANTIC_PRIORITY_CRITICAL = 4


@dataclass(frozen=True)
class ScenarioComparisonInterpretationRule:
    """Interpretation metadata for one prepared comparison metric."""

    preferred_direction: str | None = None
    absolute_materiality_threshold: float = 0.0
    relative_materiality_threshold: float | None = None
    semantic_priority_tier: int = 0
    always_meaningful_status_change: bool = False


@dataclass(frozen=True)
class ScenarioComparisonDisplayMetric:
    """Prepared display data for one Scenario A/B comparison metric."""

    metric_id: str
    label: str
    value_format: str
    scenario_a_value: Any
    scenario_b_value: Any
    change_format: str | None = None
    change_value: Any | None = None
    relative_change_percent: float | None = None
    scenario_value_state: str = SCENARIO_VALUE_REQUIRED
    scenario_value_reason: str | None = None
    change_mode: str = SCENARIO_CHANGE_DELTA
    change_reason: str | None = None
    display_priority: int = 100
    preferred_direction: str | None = None
    section_signal_weight: float = 0.0
    absolute_materiality_threshold: float = 0.0
    relative_materiality_threshold: float | None = None
    semantic_priority_tier: int = 0
    always_meaningful_status_change: bool = False


@dataclass(frozen=True)
class ScenarioComparisonDisplayMetricBuckets:
    """Prepared grouped metric buckets for one decision-area dashboard card."""

    primary_metrics: tuple[ScenarioComparisonDisplayMetric, ...] = ()
    secondary_metrics: tuple[ScenarioComparisonDisplayMetric, ...] = ()
    unchanged_metrics: tuple[ScenarioComparisonDisplayMetric, ...] = ()


@dataclass(frozen=True)
class ScenarioComparisonDisplaySection:
    """Prepared section data for the Scenario Comparison dashboard."""

    section_id: str
    title: str
    description: str
    numeric_metrics: tuple[ScenarioComparisonDisplayMetric, ...] = ()
    status_metrics: tuple[ScenarioComparisonDisplayMetric, ...] = ()
    summary_label: str = "Minimal change"
    summary_tone: str = SCENARIO_SECTION_SUMMARY_LITTLE_NO_CHANGE
    impact_level: str = SCENARIO_SECTION_IMPACT_NONE
    outcome_tone: str = SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL
    summary_text: str = ""
    metric_buckets: ScenarioComparisonDisplayMetricBuckets = field(
        default_factory=ScenarioComparisonDisplayMetricBuckets
    )
    visualization_intent: str = SCENARIO_SECTION_VISUALIZATION_NONE
    default_expanded: bool = False
    signal_score: float = 0.0


@dataclass(frozen=True)
class ScenarioComparisonExecutiveMetric:
    """Prepared executive-summary metric for the Scenario Comparison dashboard."""

    metric_id: str
    title: str
    why_it_matters: str
    value_format: str
    change_format: str
    scenario_a_value: Any
    scenario_b_value: Any
    change_value: Any
    relative_change_percent: float | None = None
    relative_shift_percent: float = 0.0
    outcome: str = SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL
    display_outcome: str = SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL


@dataclass(frozen=True)
class ScenarioComparisonHighlightItem:
    """Prepared ranked improvement or trade-off item for dashboard summaries."""

    label: str
    theme: str
    outcome: str
    ranking_score: float
    signal_score: float
    display_priority: int
    value_format: str
    scenario_a_value: Any
    scenario_b_value: Any
    change_format: str | None = None
    change_value: Any | None = None
    relative_change_percent: float | None = None
    is_categorical: bool = False
    semantic_priority_tier: int = 0
    interpretation_reason: str | None = None


@dataclass(frozen=True)
class ScenarioComparisonMetricInterpretation:
    """Prepared interpretation result for executive highlight selection."""

    meaningful: bool
    outcome: str
    ranking_score: float
    signal_score: float
    interpretation_reason: str
    semantic_priority_tier: int


@dataclass(frozen=True)
class ScenarioComparisonOverviewItem:
    """Prepared high-level difference item for the overview chart."""

    label: str
    theme: str
    change_format: str
    raw_change: float | int
    relative_shift_percent: float
    direction_label: str


@dataclass(frozen=True)
class ScenarioComparisonDisplayData:
    """Prepared Scenario A/B dashboard data derived from Metrics outputs."""

    executive_metrics: tuple[ScenarioComparisonExecutiveMetric, ...]
    improvement_highlights: tuple[ScenarioComparisonHighlightItem, ...]
    trade_off_highlights: tuple[ScenarioComparisonHighlightItem, ...]
    overview_items: tuple[ScenarioComparisonOverviewItem, ...]
    sections: tuple[ScenarioComparisonDisplaySection, ...]


def _numeric_rule(
    change_format: str,
    *,
    preferred_direction: str | None,
    semantic_priority_tier: int,
    relative_materiality_threshold: float | None = None,
) -> ScenarioComparisonInterpretationRule:
    """Return one numeric interpretation rule with format-aware defaults."""

    return ScenarioComparisonInterpretationRule(
        preferred_direction=preferred_direction,
        absolute_materiality_threshold=default_materiality_threshold(change_format),
        relative_materiality_threshold=relative_materiality_threshold,
        semantic_priority_tier=semantic_priority_tier,
    )


def _status_rule(
    *,
    preferred_direction: str | None,
    semantic_priority_tier: int,
    always_meaningful_status_change: bool,
) -> ScenarioComparisonInterpretationRule:
    """Return one categorical interpretation rule."""

    return ScenarioComparisonInterpretationRule(
        preferred_direction=preferred_direction,
        semantic_priority_tier=semantic_priority_tier,
        always_meaningful_status_change=always_meaningful_status_change,
    )


SCENARIO_COMPARISON_INTERPRETATION_RULES = {
    "peak_load": _numeric_rule(
        "power_kw_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_MEDIUM,
        relative_materiality_threshold=0.1,
    ),
    "capacity_utilization": _numeric_rule(
        "percentage_points_signed",
        preferred_direction=None,
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_LOW,
        relative_materiality_threshold=0.1,
    ),
    "delivered_energy": _numeric_rule(
        "energy_kwh_signed",
        preferred_direction="higher",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_MEDIUM,
        relative_materiality_threshold=0.1,
    ),
    "unmet_energy": _numeric_rule(
        "energy_kwh_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_CRITICAL,
        relative_materiality_threshold=0.1,
    ),
    "average_charger_utilization": _numeric_rule(
        "percentage_points_signed",
        preferred_direction=None,
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_LOW,
    ),
    "peak_charger_utilization": _numeric_rule(
        "percentage_points_signed",
        preferred_direction=None,
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_LOW,
    ),
    "average_occupied_chargers": _numeric_rule(
        "charger_count_1_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_LOW,
    ),
    "peak_occupied_chargers": _numeric_rule(
        "charger_count_0_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_HIGH,
    ),
    "charger_capacity_vs_demand_balance": _numeric_rule(
        "charger_count_0_signed",
        preferred_direction="higher",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_HIGH,
    ),
    "required_charger_count": _numeric_rule(
        "charger_count_0_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_HIGH,
    ),
    "additional_chargers_required": _numeric_rule(
        "charger_count_0_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_HIGH,
    ),
    "primary_constraint_reason": _status_rule(
        preferred_direction=None,
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_HIGH,
        always_meaningful_status_change=True,
    ),
    "maximum_queue_length": _numeric_rule(
        "vehicle_count_0_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_CRITICAL,
    ),
    "average_queue_length": _numeric_rule(
        "vehicle_count_1_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_LOW,
    ),
    "queue_duration_hours": _numeric_rule(
        "hours_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_LOW,
    ),
    "average_waiting_time_hours": _numeric_rule(
        "hours_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_LOW,
    ),
    "maximum_waiting_time_hours": _numeric_rule(
        "hours_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_LOW,
    ),
    "vehicles_waiting": _numeric_rule(
        "vehicle_count_0_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_MEDIUM,
    ),
    "vehicles_not_started": _numeric_rule(
        "vehicle_count_0_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_CRITICAL,
    ),
    "vehicles_with_unmet_energy": _numeric_rule(
        "vehicle_count_0_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_HIGH,
    ),
    "queue_present": _status_rule(
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_CRITICAL,
        always_meaningful_status_change=True,
    ),
    "average_transformer_loading": _numeric_rule(
        "percentage_points_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_MEDIUM,
    ),
    "peak_transformer_loading": _numeric_rule(
        "percentage_points_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_HIGH,
    ),
    "transformer_overload_duration": _numeric_rule(
        "hours_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_HIGH,
    ),
    "maximum_transformer_overload": _numeric_rule(
        "power_kw_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_HIGH,
    ),
    "maximum_feeder_loading": _numeric_rule(
        "percentage_points_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_HIGH,
    ),
    "overloaded_feeders": _numeric_rule(
        "feeder_count_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_HIGH,
    ),
    "transformer_overload": _status_rule(
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_CRITICAL,
        always_meaningful_status_change=True,
    ),
    "transformer_thermal_risk": _status_rule(
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_HIGH,
        always_meaningful_status_change=True,
    ),
    "feeder_overload": _status_rule(
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_CRITICAL,
        always_meaningful_status_change=True,
    ),
    "highest_feeder_thermal_risk": _status_rule(
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_HIGH,
        always_meaningful_status_change=True,
    ),
    "peak_harmonic_risk_score": _numeric_rule(
        "score_points_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_MEDIUM,
    ),
    "harmonic_risk_duration": _numeric_rule(
        "hours_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_LOW,
    ),
    "peak_current_imbalance": _numeric_rule(
        "percentage_points_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_MEDIUM,
    ),
    "current_imbalance_duration": _numeric_rule(
        "hours_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_LOW,
    ),
    "overall_pq_risk_score": _numeric_rule(
        "score_points_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_HIGH,
    ),
    "overall_pq_risk": _numeric_rule(
        "score_points_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_HIGH,
    ),
    "pq_warning_count": _numeric_rule(
        "warning_count_signed",
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_HIGH,
    ),
    "harmonic_risk_level": _status_rule(
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_MEDIUM,
        always_meaningful_status_change=True,
    ),
    "current_imbalance_risk_level": _status_rule(
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_MEDIUM,
        always_meaningful_status_change=True,
    ),
    "overall_pq_risk_level": _status_rule(
        preferred_direction="lower",
        semantic_priority_tier=SCENARIO_SEMANTIC_PRIORITY_HIGH,
        always_meaningful_status_change=True,
    ),
}


def prepare_scenario_comparison_display_data(
    metrics_a: Metrics,
    metrics_b: Metrics,
    comparison_metrics: ScenarioComparisonMetrics,
) -> ScenarioComparisonDisplayData:
    """Prepare grouped Scenario A/B display data from Metrics outputs only."""

    executive_metrics = _prepare_executive_metrics(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )
    sections = _prepare_sections(metrics_a, metrics_b, comparison_metrics)
    return ScenarioComparisonDisplayData(
        executive_metrics=executive_metrics,
        improvement_highlights=_prepare_highlight_items(
            sections,
            SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT,
        ),
        trade_off_highlights=_prepare_highlight_items(
            sections,
            SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF,
        ),
        overview_items=_prepare_overview_items(sections),
        sections=sections,
    )


def _prepare_executive_metrics(
    metrics_a: Metrics,
    metrics_b: Metrics,
    comparison_metrics: ScenarioComparisonMetrics,
) -> tuple[ScenarioComparisonExecutiveMetric, ...]:
    """Return prepared headline metrics for the executive-summary card row."""

    return (
        _executive_metric(
            "peak_load",
            "Peak Load",
            "Shows how much connection-capacity and infrastructure pressure the scenario creates.",
            "power_kw",
            "power_kw_signed",
            metrics_a.peak_load,
            metrics_b.peak_load,
            comparison_metrics.peak_load_difference_kw,
            comparison_metrics.peak_load_change_percent,
            preferred_direction="lower",
        ),
        _executive_metric(
            "capacity_utilization",
            "Capacity Utilization",
            "Shows how intensely the configured charging capacity is used at the modeled peak.",
            "percent",
            "percentage_points_signed",
            metrics_a.capacity_utilization,
            metrics_b.capacity_utilization,
            comparison_metrics.capacity_utilization_difference_percentage_points,
            comparison_metrics.capacity_utilization_change_percent,
            preferred_direction="lower",
        ),
        _executive_metric(
            "unmet_energy",
            "Unmet Energy",
            "Shows how much charging demand the modeled infrastructure still fails to serve.",
            "energy_kwh",
            "energy_kwh_signed",
            metrics_a.unmet_energy,
            metrics_b.unmet_energy,
            comparison_metrics.unmet_energy_difference_kwh,
            comparison_metrics.unmet_energy_change_percent,
            preferred_direction="lower",
        ),
        _executive_metric(
            "maximum_queue_length",
            "Maximum Queue Length",
            "Indicates how much user waiting pressure builds up at the busiest point.",
            "vehicle_count_0",
            "vehicle_count_0_signed",
            metrics_a.maximum_queue_length,
            metrics_b.maximum_queue_length,
            comparison_metrics.maximum_queue_length_difference,
            None,
            preferred_direction="lower",
        ),
        _executive_metric(
            "peak_transformer_loading",
            "Peak Transformer Loading",
            "Highlights how close the site comes to stressing the transformer rating.",
            "percent",
            "percentage_points_signed",
            metrics_a.peak_transformer_loading_percent,
            metrics_b.peak_transformer_loading_percent,
            comparison_metrics.peak_transformer_loading_percent_difference,
            None,
            preferred_direction="lower",
        ),
        _executive_metric(
            "overall_pq_risk",
            "Overall PQ Risk",
            "Summarizes the modeled power-quality risk level across the charging profile.",
            "risk_score",
            "score_points_signed",
            metrics_a.overall_pq_risk_score,
            metrics_b.overall_pq_risk_score,
            comparison_metrics.overall_pq_risk_score_difference,
            None,
            preferred_direction="lower",
        ),
    )

def _prepare_highlight_items(
    sections: tuple[ScenarioComparisonDisplaySection, ...],
    outcome: str,
) -> tuple[ScenarioComparisonHighlightItem, ...]:
    """Return ranked highlight cards for one comparison outcome type."""

    candidates: list[ScenarioComparisonHighlightItem] = []
    for section in sections:
        for metric in section.numeric_metrics:
            interpretation = _interpret_metric_for_highlight(metric)
            if (
                not interpretation.meaningful
                or interpretation.outcome != outcome
                or interpretation.signal_score <= 0.0
            ):
                continue
            candidates.append(
                ScenarioComparisonHighlightItem(
                    label=metric.label,
                    theme=section.title,
                    outcome=interpretation.outcome,
                    ranking_score=interpretation.ranking_score,
                    signal_score=interpretation.signal_score,
                    display_priority=metric.display_priority,
                    value_format=metric.value_format,
                    scenario_a_value=metric.scenario_a_value,
                    scenario_b_value=metric.scenario_b_value,
                    change_format=metric.change_format,
                    change_value=metric.change_value,
                    relative_change_percent=metric.relative_change_percent,
                    semantic_priority_tier=interpretation.semantic_priority_tier,
                    interpretation_reason=interpretation.interpretation_reason,
                )
            )

        for metric in section.status_metrics:
            interpretation = _interpret_metric_for_highlight(metric)
            if (
                not interpretation.meaningful
                or interpretation.outcome != outcome
                or interpretation.signal_score <= 0.0
            ):
                continue
            candidates.append(
                ScenarioComparisonHighlightItem(
                    label=metric.label,
                    theme=section.title,
                    outcome=interpretation.outcome,
                    ranking_score=interpretation.ranking_score,
                    signal_score=interpretation.signal_score,
                    display_priority=metric.display_priority,
                    value_format=metric.value_format,
                    scenario_a_value=metric.scenario_a_value,
                    scenario_b_value=metric.scenario_b_value,
                    is_categorical=True,
                    semantic_priority_tier=interpretation.semantic_priority_tier,
                    interpretation_reason=interpretation.interpretation_reason,
                )
            )

    ranked_candidates = sorted(
        candidates,
        key=lambda candidate: (
            -candidate.ranking_score,
            candidate.display_priority,
            candidate.theme,
            candidate.label,
        ),
    )
    return tuple(ranked_candidates[:3])


def _interpret_metric_for_highlight(
    metric: ScenarioComparisonDisplayMetric,
) -> ScenarioComparisonMetricInterpretation:
    """Return highlight-selection interpretation for one prepared metric."""

    if metric.change_mode == SCENARIO_CHANGE_NONE:
        return _interpret_status_metric_for_highlight(metric)

    return _interpret_numeric_metric_for_highlight(metric)


def _interpret_executive_metric(
    metric: ScenarioComparisonExecutiveMetric,
) -> ScenarioComparisonMetricInterpretation:
    """Return materiality-aware interpretation for one executive KPI."""

    rule = SCENARIO_COMPARISON_INTERPRETATION_RULES[metric.metric_id]
    proxy_metric = ScenarioComparisonDisplayMetric(
        metric_id=metric.metric_id,
        label=metric.title,
        value_format=metric.value_format,
        scenario_a_value=metric.scenario_a_value,
        scenario_b_value=metric.scenario_b_value,
        change_format=metric.change_format,
        change_value=metric.change_value,
        relative_change_percent=metric.relative_change_percent,
        preferred_direction=rule.preferred_direction,
        absolute_materiality_threshold=rule.absolute_materiality_threshold,
        relative_materiality_threshold=rule.relative_materiality_threshold,
        semantic_priority_tier=rule.semantic_priority_tier,
    )
    return _interpret_numeric_metric_for_highlight(proxy_metric)


def _interpret_numeric_metric_for_highlight(
    metric: ScenarioComparisonDisplayMetric,
) -> ScenarioComparisonMetricInterpretation:
    """Return highlight interpretation for one numeric comparison metric."""

    if metric.change_mode == SCENARIO_CHANGE_NOT_APPLICABLE:
        return ScenarioComparisonMetricInterpretation(
            meaningful=False,
            outcome=SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL,
            ranking_score=0.0,
            signal_score=0.0,
            interpretation_reason="not_applicable",
            semantic_priority_tier=metric.semantic_priority_tier,
        )

    if metric.change_value is None:
        return ScenarioComparisonMetricInterpretation(
            meaningful=False,
            outcome=SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL,
            ranking_score=0.0,
            signal_score=0.0,
            interpretation_reason="difference_unavailable",
            semantic_priority_tier=metric.semantic_priority_tier,
        )

    if not _numeric_change_is_material(metric):
        return ScenarioComparisonMetricInterpretation(
            meaningful=False,
            outcome=SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL,
            ranking_score=0.0,
            signal_score=0.0,
            interpretation_reason="below_materiality_threshold",
            semantic_priority_tier=metric.semantic_priority_tier,
        )

    signal_score = _numeric_metric_signal_score(metric)
    if metric.preferred_direction is None:
        return ScenarioComparisonMetricInterpretation(
            meaningful=False,
            outcome=SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL,
            ranking_score=0.0,
            signal_score=signal_score,
            interpretation_reason="direction_not_defined",
            semantic_priority_tier=metric.semantic_priority_tier,
        )

    outcome = _executive_outcome(
        metric.change_value,
        metric.preferred_direction,
    )
    return ScenarioComparisonMetricInterpretation(
        meaningful=outcome != SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL,
        outcome=outcome,
        ranking_score=_highlight_ranking_score(metric.semantic_priority_tier, signal_score),
        signal_score=signal_score,
        interpretation_reason="material_numeric_change",
        semantic_priority_tier=metric.semantic_priority_tier,
    )


def _interpret_status_metric_for_highlight(
    metric: ScenarioComparisonDisplayMetric,
) -> ScenarioComparisonMetricInterpretation:
    """Return highlight interpretation for one categorical comparison metric."""

    if metric.scenario_a_value == metric.scenario_b_value:
        return ScenarioComparisonMetricInterpretation(
            meaningful=False,
            outcome=SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL,
            ranking_score=0.0,
            signal_score=0.0,
            interpretation_reason="unchanged_status",
            semantic_priority_tier=metric.semantic_priority_tier,
        )

    if not metric.always_meaningful_status_change:
        return ScenarioComparisonMetricInterpretation(
            meaningful=False,
            outcome=SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL,
            ranking_score=0.0,
            signal_score=0.0,
            interpretation_reason="status_change_not_prioritized",
            semantic_priority_tier=metric.semantic_priority_tier,
        )

    signal_score = metric.section_signal_weight
    if metric.preferred_direction is None:
        return ScenarioComparisonMetricInterpretation(
            meaningful=False,
            outcome=SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL,
            ranking_score=0.0,
            signal_score=signal_score,
            interpretation_reason="direction_not_defined",
            semantic_priority_tier=metric.semantic_priority_tier,
        )

    severity_a = _status_metric_severity(metric.value_format, metric.scenario_a_value)
    severity_b = _status_metric_severity(metric.value_format, metric.scenario_b_value)
    if severity_a is None or severity_b is None:
        return ScenarioComparisonMetricInterpretation(
            meaningful=False,
            outcome=SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL,
            ranking_score=0.0,
            signal_score=signal_score,
            interpretation_reason="status_severity_unavailable",
            semantic_priority_tier=metric.semantic_priority_tier,
        )

    outcome = _executive_outcome(
        severity_b - severity_a,
        metric.preferred_direction,
    )
    return ScenarioComparisonMetricInterpretation(
        meaningful=outcome != SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL,
        outcome=outcome,
        ranking_score=_highlight_ranking_score(metric.semantic_priority_tier, signal_score),
        signal_score=signal_score,
        interpretation_reason="meaningful_status_change",
        semantic_priority_tier=metric.semantic_priority_tier,
    )


def _highlight_ranking_score(
    semantic_priority_tier: int,
    signal_score: float,
) -> float:
    """Return one stable numeric ranking score for executive highlights."""

    del semantic_priority_tier
    return float(signal_score)

def _prepare_overview_items(
    sections: tuple[ScenarioComparisonDisplaySection, ...],
) -> tuple[ScenarioComparisonOverviewItem, ...]:
    """Return ranked high-level difference items for the overview chart."""

    overview_metric_labels = {
        "peak_load": "Peak load",
        "unmet_energy": "Unmet energy",
        "capacity_utilization": "Capacity utilization",
        "peak_occupied_chargers": "Peak occupied chargers",
        "maximum_queue_length": "Maximum queue length",
        "peak_transformer_loading": "Peak transformer loading",
        "overall_pq_risk_score": "Overall PQ risk score",
    }
    candidates: list[tuple[ScenarioComparisonOverviewItem, float]] = []

    for section in sections:
        for metric in section.numeric_metrics:
            if metric.metric_id not in overview_metric_labels:
                continue

            interpretation = _interpret_metric_for_highlight(metric)
            if not interpretation.meaningful:
                continue

            candidates.append(
                (
                    _overview_item(
                        overview_metric_labels[metric.metric_id],
                        section.title,
                        metric.change_format or metric.value_format,
                        metric.change_value or 0.0,
                        metric.scenario_a_value or 0.0,
                    ),
                    interpretation.ranking_score,
                )
            )

    ranked_candidates = sorted(
        candidates,
        key=lambda item: (
            -item[1],
            -item[0].relative_shift_percent,
            item[0].label,
        ),
    )
    return tuple(
        candidate
        for candidate, _ranking_score in ranked_candidates
        if candidate.relative_shift_percent > 0.0
    )[:5]


def _prepare_sections(
    metrics_a: Metrics,
    metrics_b: Metrics,
    comparison_metrics: ScenarioComparisonMetrics,
) -> tuple[ScenarioComparisonDisplaySection, ...]:
    """Return prepared detailed-comparison sections."""

    sections = (
        ScenarioComparisonDisplaySection(
            section_id="energy_performance",
            title="Energy & Performance",
            description="Core charging demand, utilization, and service outcomes.",
            numeric_metrics=(
                _metric(
                    "peak_load",
                    "Peak load (kW)",
                    "power_kw",
                    metrics_a.peak_load,
                    metrics_b.peak_load,
                    change_format="power_kw_signed",
                    change_value=comparison_metrics.peak_load_difference_kw,
                    relative_change_percent=comparison_metrics.peak_load_change_percent,
                    display_priority=3,
                ),
                _metric(
                    "capacity_utilization",
                    "Capacity utilization (%)",
                    "percent",
                    metrics_a.capacity_utilization,
                    metrics_b.capacity_utilization,
                    change_format="percentage_points_signed",
                    change_value=(
                        comparison_metrics.capacity_utilization_difference_percentage_points
                    ),
                    relative_change_percent=(
                        comparison_metrics.capacity_utilization_change_percent
                    ),
                    display_priority=5,
                ),
                _metric(
                    "delivered_energy",
                    "Delivered energy (kWh)",
                    "energy_kwh",
                    metrics_a.delivered_energy,
                    metrics_b.delivered_energy,
                    change_format="energy_kwh_signed",
                    change_value=comparison_metrics.delivered_energy_difference_kwh,
                    relative_change_percent=(
                        comparison_metrics.delivered_energy_change_percent
                    ),
                    display_priority=4,
                ),
                _metric(
                    "unmet_energy",
                    "Unmet energy (kWh)",
                    "energy_kwh",
                    metrics_a.unmet_energy,
                    metrics_b.unmet_energy,
                    change_format="energy_kwh_signed",
                    change_value=comparison_metrics.unmet_energy_difference_kwh,
                    relative_change_percent=(
                        comparison_metrics.unmet_energy_change_percent
                    ),
                    display_priority=1,
                ),
            ),
        ),
        ScenarioComparisonDisplaySection(
            section_id="infrastructure",
            title="Infrastructure",
            description="Charger usage and charger-planning assumptions.",
            numeric_metrics=(
                _metric(
                    "average_charger_utilization",
                    "Average charger utilization (%)",
                    "percent",
                    metrics_a.average_charger_utilization_percent,
                    metrics_b.average_charger_utilization_percent,
                    change_format="percentage_points_signed",
                    change_value=_calculate_defined_difference(
                        metrics_b.average_charger_utilization_percent,
                        metrics_a.average_charger_utilization_percent,
                    ),
                    relative_change_percent=_calculate_defined_relative_change_percent(
                        metrics_b.average_charger_utilization_percent,
                        metrics_a.average_charger_utilization_percent,
                    ),
                    scenario_value_state=SCENARIO_VALUE_OPTIONAL_UNAVAILABLE,
                    scenario_value_reason="charger_utilization_unavailable",
                    change_mode=SCENARIO_CHANGE_OPTIONAL_DELTA,
                    change_reason="difference_unavailable",
                    display_priority=6,
                ),
                _metric(
                    "peak_charger_utilization",
                    "Peak charger utilization (%)",
                    "percent",
                    metrics_a.peak_charger_utilization_percent,
                    metrics_b.peak_charger_utilization_percent,
                    change_format="percentage_points_signed",
                    change_value=_calculate_defined_difference(
                        metrics_b.peak_charger_utilization_percent,
                        metrics_a.peak_charger_utilization_percent,
                    ),
                    relative_change_percent=_calculate_defined_relative_change_percent(
                        metrics_b.peak_charger_utilization_percent,
                        metrics_a.peak_charger_utilization_percent,
                    ),
                    scenario_value_state=SCENARIO_VALUE_OPTIONAL_UNAVAILABLE,
                    scenario_value_reason="charger_utilization_unavailable",
                    change_mode=SCENARIO_CHANGE_OPTIONAL_DELTA,
                    change_reason="difference_unavailable",
                    display_priority=5,
                ),
                _metric(
                    "average_occupied_chargers",
                    "Average occupied chargers",
                    "charger_count_1",
                    metrics_a.average_occupied_charger_count,
                    metrics_b.average_occupied_charger_count,
                    change_format="charger_count_1_signed",
                    change_value=(
                        comparison_metrics.average_occupied_charger_count_difference
                    ),
                    display_priority=4,
                ),
                _metric(
                    "peak_occupied_chargers",
                    "Peak occupied chargers",
                    "charger_count_0",
                    metrics_a.peak_occupied_charger_count,
                    metrics_b.peak_occupied_charger_count,
                    change_format="charger_count_0_signed",
                    change_value=comparison_metrics.peak_occupied_charger_count_difference,
                    display_priority=4,
                ),
                _metric(
                    "charger_capacity_vs_demand_balance",
                    "Charger capacity vs demand balance",
                    "charger_count_0",
                    metrics_a.charger_capacity_vs_demand_balance,
                    metrics_b.charger_capacity_vs_demand_balance,
                    change_format="charger_count_0_signed",
                    change_value=(
                        comparison_metrics.charger_capacity_vs_demand_balance_difference
                    ),
                    display_priority=1,
                ),
                _metric(
                    "required_charger_count",
                    "Required charger count",
                    "charger_count_0",
                    metrics_a.required_charger_count,
                    metrics_b.required_charger_count,
                    change_format="charger_count_0_signed",
                    change_value=_calculate_defined_difference(
                        metrics_b.required_charger_count,
                        metrics_a.required_charger_count,
                    ),
                    relative_change_percent=_calculate_defined_relative_change_percent(
                        metrics_b.required_charger_count,
                        metrics_a.required_charger_count,
                    ),
                    scenario_value_state=SCENARIO_VALUE_OPTIONAL_NOT_APPLICABLE,
                    scenario_value_reason="required_charger_count_not_applicable",
                    change_mode=SCENARIO_CHANGE_OPTIONAL_DELTA,
                    change_reason="difference_unavailable",
                    display_priority=2,
                    section_signal_weight=24.0,
                ),
                _metric(
                    "additional_chargers_required",
                    "Additional chargers required",
                    "charger_count_0",
                    metrics_a.additional_chargers_required,
                    metrics_b.additional_chargers_required,
                    change_format="charger_count_0_signed",
                    change_value=_calculate_defined_difference(
                        metrics_b.additional_chargers_required,
                        metrics_a.additional_chargers_required,
                    ),
                    relative_change_percent=_calculate_defined_relative_change_percent(
                        metrics_b.additional_chargers_required,
                        metrics_a.additional_chargers_required,
                    ),
                    scenario_value_state=SCENARIO_VALUE_OPTIONAL_NOT_APPLICABLE,
                    scenario_value_reason="additional_chargers_not_applicable",
                    change_mode=SCENARIO_CHANGE_OPTIONAL_DELTA,
                    change_reason="difference_unavailable",
                    display_priority=3,
                    section_signal_weight=24.0,
                ),
            ),
            status_metrics=(
                _status_metric(
                    "primary_constraint_reason",
                    "Primary constraint reason",
                    "primary_constraint_reason",
                    metrics_a.primary_constraint_reason,
                    metrics_b.primary_constraint_reason,
                    display_priority=1,
                    section_signal_weight=18.0,
                ),
            ),
        ),
        ScenarioComparisonDisplaySection(
            section_id="queueing",
            title="Queueing",
            description="Waiting-pressure signals and service shortfalls.",
            numeric_metrics=(
                _metric(
                    "maximum_queue_length",
                    "Maximum queue length",
                    "vehicle_count_0",
                    metrics_a.maximum_queue_length,
                    metrics_b.maximum_queue_length,
                    change_format="vehicle_count_0_signed",
                    change_value=comparison_metrics.maximum_queue_length_difference,
                    display_priority=1,
                ),
                _metric(
                    "average_queue_length",
                    "Average queue length",
                    "vehicle_count_1",
                    metrics_a.average_queue_length,
                    metrics_b.average_queue_length,
                    change_format="vehicle_count_1_signed",
                    change_value=comparison_metrics.average_queue_length_difference,
                    display_priority=5,
                ),
                _metric(
                    "queue_duration_hours",
                    "Queue duration (h)",
                    "hours",
                    metrics_a.queue_duration_hours,
                    metrics_b.queue_duration_hours,
                    change_format="hours_signed",
                    change_value=comparison_metrics.queue_duration_hours_difference,
                    display_priority=5,
                ),
                _metric(
                    "average_waiting_time_hours",
                    "Average waiting time (h)",
                    "hours",
                    metrics_a.average_waiting_time_hours,
                    metrics_b.average_waiting_time_hours,
                    change_format="hours_signed",
                    change_value=comparison_metrics.average_waiting_time_hours_difference,
                    relative_change_percent=_calculate_defined_relative_change_percent(
                        metrics_b.average_waiting_time_hours,
                        metrics_a.average_waiting_time_hours,
                    ),
                    scenario_value_state=SCENARIO_VALUE_OPTIONAL_UNAVAILABLE,
                    scenario_value_reason="waiting_time_unavailable",
                    change_mode=SCENARIO_CHANGE_OPTIONAL_DELTA,
                    change_reason="difference_unavailable",
                    display_priority=7,
                ),
                _metric(
                    "maximum_waiting_time_hours",
                    "Maximum waiting time (h)",
                    "hours",
                    metrics_a.maximum_waiting_time_hours,
                    metrics_b.maximum_waiting_time_hours,
                    change_format="hours_signed",
                    change_value=comparison_metrics.maximum_waiting_time_hours_difference,
                    relative_change_percent=_calculate_defined_relative_change_percent(
                        metrics_b.maximum_waiting_time_hours,
                        metrics_a.maximum_waiting_time_hours,
                    ),
                    scenario_value_state=SCENARIO_VALUE_OPTIONAL_UNAVAILABLE,
                    scenario_value_reason="waiting_time_unavailable",
                    change_mode=SCENARIO_CHANGE_OPTIONAL_DELTA,
                    change_reason="difference_unavailable",
                    display_priority=8,
                ),
                _metric(
                    "vehicles_waiting",
                    "Vehicles waiting",
                    "vehicle_count_0",
                    metrics_a.vehicles_waiting_count,
                    metrics_b.vehicles_waiting_count,
                    change_format="vehicle_count_0_signed",
                    change_value=comparison_metrics.vehicles_waiting_count_difference,
                    display_priority=4,
                ),
                _metric(
                    "vehicles_not_started",
                    "Vehicles not started",
                    "vehicle_count_0",
                    metrics_a.vehicles_not_started_count,
                    metrics_b.vehicles_not_started_count,
                    change_format="vehicle_count_0_signed",
                    change_value=comparison_metrics.vehicles_not_started_count_difference,
                    display_priority=2,
                ),
                _metric(
                    "vehicles_with_unmet_energy",
                    "Vehicles with unmet energy",
                    "vehicle_count_0",
                    metrics_a.vehicles_with_unmet_energy_count,
                    metrics_b.vehicles_with_unmet_energy_count,
                    change_format="vehicle_count_0_signed",
                    change_value=(
                        comparison_metrics.vehicles_with_unmet_energy_count_difference
                    ),
                    display_priority=3,
                ),
            ),
            status_metrics=(
                _status_metric(
                    "queue_present",
                    "Queue present",
                    "queue_present",
                    metrics_a.queue_present_indicator,
                    metrics_b.queue_present_indicator,
                    display_priority=1,
                    section_signal_weight=30.0,
                ),
            ),
        ),
        ScenarioComparisonDisplaySection(
            section_id="grid",
            title="Grid",
            description="Transformer and feeder loading outcomes.",
            numeric_metrics=(
                _metric(
                    "average_transformer_loading",
                    "Average transformer loading (%)",
                    "percent",
                    metrics_a.average_transformer_loading_percent,
                    metrics_b.average_transformer_loading_percent,
                    change_format="percentage_points_signed",
                    change_value=(
                        comparison_metrics.average_transformer_loading_percent_difference
                    ),
                    display_priority=5,
                ),
                _metric(
                    "peak_transformer_loading",
                    "Peak transformer loading (%)",
                    "percent",
                    metrics_a.peak_transformer_loading_percent,
                    metrics_b.peak_transformer_loading_percent,
                    change_format="percentage_points_signed",
                    change_value=(
                        comparison_metrics.peak_transformer_loading_percent_difference
                    ),
                    display_priority=1,
                ),
                _metric(
                    "transformer_overload_duration",
                    "Transformer overload duration (h)",
                    "hours",
                    metrics_a.transformer_overload_duration_hours,
                    metrics_b.transformer_overload_duration_hours,
                    change_format="hours_signed",
                    change_value=(
                        comparison_metrics.transformer_overload_duration_hours_difference
                    ),
                    display_priority=4,
                ),
                _metric(
                    "maximum_transformer_overload",
                    "Maximum transformer overload (kW)",
                    "power_kw",
                    metrics_a.transformer_maximum_overload_kw,
                    metrics_b.transformer_maximum_overload_kw,
                    change_format="power_kw_signed",
                    change_value=(
                        comparison_metrics.transformer_maximum_overload_kw_difference
                    ),
                    display_priority=3,
                ),
                _metric(
                    "maximum_feeder_loading",
                    "Maximum feeder loading (%)",
                    "percent",
                    metrics_a.maximum_feeder_loading_percent,
                    metrics_b.maximum_feeder_loading_percent,
                    change_format="percentage_points_signed",
                    change_value=(
                        comparison_metrics.maximum_feeder_loading_percent_difference
                    ),
                    display_priority=2,
                ),
                _metric(
                    "overloaded_feeders",
                    "Overloaded feeders",
                    "feeder_count",
                    metrics_a.overloaded_feeder_count,
                    metrics_b.overloaded_feeder_count,
                    change_format="feeder_count_signed",
                    change_value=comparison_metrics.overloaded_feeder_count_difference,
                    display_priority=2,
                ),
            ),
            status_metrics=(
                _status_metric(
                    "transformer_overload",
                    "Transformer overload",
                    "overload_indicator",
                    metrics_a.transformer_overload_indicator,
                    metrics_b.transformer_overload_indicator,
                    display_priority=1,
                    section_signal_weight=30.0,
                ),
                _status_metric(
                    "transformer_thermal_risk",
                    "Transformer thermal risk",
                    "thermal_risk_level",
                    metrics_a.transformer_thermal_risk_level,
                    metrics_b.transformer_thermal_risk_level,
                    display_priority=2,
                    section_signal_weight=24.0,
                ),
                _status_metric(
                    "feeder_overload",
                    "Feeder overload",
                    "overload_indicator",
                    metrics_a.feeder_overload_indicator,
                    metrics_b.feeder_overload_indicator,
                    display_priority=3,
                    section_signal_weight=30.0,
                ),
                _status_metric(
                    "highest_feeder_thermal_risk",
                    "Highest feeder thermal risk",
                    "thermal_risk_level",
                    metrics_a.highest_feeder_thermal_risk_level,
                    metrics_b.highest_feeder_thermal_risk_level,
                    display_priority=4,
                    section_signal_weight=24.0,
                ),
            ),
        ),
        ScenarioComparisonDisplaySection(
            section_id="power_quality",
            title="Power Quality",
            description="Planner-facing PQ indicators and categorical risk levels.",
            numeric_metrics=(
                _metric(
                    "peak_harmonic_risk_score",
                    "Peak harmonic risk score",
                    "risk_score",
                    metrics_a.peak_harmonic_risk_score,
                    metrics_b.peak_harmonic_risk_score,
                    change_format="score_points_signed",
                    change_value=comparison_metrics.peak_harmonic_risk_score_difference,
                    display_priority=3,
                ),
                _metric(
                    "harmonic_risk_duration",
                    "Harmonic risk duration (h)",
                    "hours",
                    metrics_a.harmonic_risk_duration_hours,
                    metrics_b.harmonic_risk_duration_hours,
                    change_format="hours_signed",
                    change_value=(
                        comparison_metrics.harmonic_risk_duration_hours_difference
                    ),
                    display_priority=5,
                ),
                _metric(
                    "peak_current_imbalance",
                    "Peak current imbalance (%)",
                    "percent",
                    metrics_a.peak_current_imbalance_percent,
                    metrics_b.peak_current_imbalance_percent,
                    change_format="percentage_points_signed",
                    change_value=(
                        comparison_metrics.peak_current_imbalance_percent_difference
                    ),
                    display_priority=4,
                ),
                _metric(
                    "current_imbalance_duration",
                    "Current imbalance duration (h)",
                    "hours",
                    metrics_a.imbalance_duration_hours,
                    metrics_b.imbalance_duration_hours,
                    change_format="hours_signed",
                    change_value=comparison_metrics.imbalance_duration_hours_difference,
                    display_priority=6,
                ),
                _metric(
                    "overall_pq_risk_score",
                    "Overall PQ risk score",
                    "risk_score",
                    metrics_a.overall_pq_risk_score,
                    metrics_b.overall_pq_risk_score,
                    change_format="score_points_signed",
                    change_value=comparison_metrics.overall_pq_risk_score_difference,
                    display_priority=1,
                ),
                _metric(
                    "pq_warning_count",
                    "PQ warning count",
                    "warning_count",
                    metrics_a.power_quality_warning_count,
                    metrics_b.power_quality_warning_count,
                    change_format="warning_count_signed",
                    change_value=comparison_metrics.power_quality_warning_count_difference,
                    display_priority=2,
                ),
            ),
            status_metrics=(
                _status_metric(
                    "harmonic_risk_level",
                    "Harmonic risk level",
                    "power_quality_risk_level",
                    metrics_a.harmonic_risk_level,
                    metrics_b.harmonic_risk_level,
                    display_priority=2,
                    section_signal_weight=20.0,
                ),
                _status_metric(
                    "current_imbalance_risk_level",
                    "Current imbalance risk level",
                    "power_quality_risk_level",
                    metrics_a.current_imbalance_risk_level,
                    metrics_b.current_imbalance_risk_level,
                    display_priority=3,
                    section_signal_weight=20.0,
                ),
                _status_metric(
                    "overall_pq_risk_level",
                    "Overall PQ risk level",
                    "power_quality_risk_level",
                    metrics_a.overall_pq_risk_level,
                    metrics_b.overall_pq_risk_level,
                    display_priority=1,
                    section_signal_weight=24.0,
                ),
            ),
        ),
    )

    return tuple(_finalize_section(section) for section in sections)


def _finalize_section(
    section: ScenarioComparisonDisplaySection,
) -> ScenarioComparisonDisplaySection:
    """Return one section with ordered metrics and prepared summary metadata."""

    ordered_numeric_metrics = tuple(
        sorted(
            section.numeric_metrics,
            key=lambda metric: (metric.display_priority, metric.label),
        )
    )
    ordered_status_metrics = tuple(
        sorted(
            section.status_metrics,
            key=lambda metric: (metric.display_priority, metric.label),
        )
    )
    summary_tone, summary_label, signal_score = _classify_section_summary(
        ordered_numeric_metrics,
        ordered_status_metrics,
    )
    interpretations = _meaningful_section_interpretations(
        ordered_numeric_metrics,
        ordered_status_metrics,
    )
    top_change_label = _top_section_change_label(
        replace(
            section,
            numeric_metrics=ordered_numeric_metrics,
            status_metrics=ordered_status_metrics,
        )
    )
    impact_level = _classify_section_impact_level(signal_score)
    outcome_tone = _classify_section_outcome_tone(interpretations)
    return replace(
        section,
        numeric_metrics=ordered_numeric_metrics,
        status_metrics=ordered_status_metrics,
        summary_tone=summary_tone,
        summary_label=summary_label,
        impact_level=impact_level,
        outcome_tone=outcome_tone,
        summary_text=_build_section_summary_text(
            section.title,
            impact_level,
            outcome_tone,
            top_change_label,
            summary_label,
        ),
        metric_buckets=_build_metric_buckets(
            ordered_numeric_metrics,
            ordered_status_metrics,
        ),
        visualization_intent=_section_visualization_intent(section.section_id),
        default_expanded=summary_tone != SCENARIO_SECTION_SUMMARY_LITTLE_NO_CHANGE,
        signal_score=signal_score,
    )


def _classify_section_summary(
    numeric_metrics: tuple[ScenarioComparisonDisplayMetric, ...],
    status_metrics: tuple[ScenarioComparisonDisplayMetric, ...],
) -> tuple[str, str, float]:
    """Return summary tone, label, and signal score for one section."""

    interpretations = _meaningful_section_interpretations(
        numeric_metrics,
        status_metrics,
    )
    if not interpretations:
        return (
            SCENARIO_SECTION_SUMMARY_LITTLE_NO_CHANGE,
            "Minimal change",
            0.0,
        )

    improvement_present = False
    trade_off_present = False
    max_signal_score = 0.0

    for _metric, interpretation in interpretations:
        max_signal_score = max(max_signal_score, interpretation.signal_score)
        if interpretation.outcome == SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT:
            improvement_present = True
        elif interpretation.outcome == SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF:
            trade_off_present = True

    if trade_off_present and improvement_present:
        return (
            SCENARIO_SECTION_SUMMARY_TRADE_OFFS,
            "Mixed",
            max_signal_score,
        )

    if trade_off_present:
        return (
            SCENARIO_SECTION_SUMMARY_TRADE_OFFS,
            "Trade-off",
            max_signal_score,
        )

    return (
        SCENARIO_SECTION_SUMMARY_MAJOR_CHANGES,
        "Improvement",
        max_signal_score,
    )


def _classify_section_impact_level(signal_score: float) -> str:
    """Return badge-oriented impact level without changing section summary math."""

    if signal_score <= 0.0:
        return SCENARIO_SECTION_IMPACT_NONE

    if signal_score >= 10.0:
        return SCENARIO_SECTION_IMPACT_MAJOR

    return SCENARIO_SECTION_IMPACT_MINOR


def _classify_section_outcome_tone(
    interpretations: tuple[
        tuple[
            ScenarioComparisonDisplayMetric,
            ScenarioComparisonMetricInterpretation,
        ],
        ...,
    ],
) -> str:
    """Return the dominant outcome tone for one prepared decision area."""

    improvement_present = False
    trade_off_present = False

    for _metric, interpretation in interpretations:
        if interpretation.outcome == SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT:
            improvement_present = True
        elif interpretation.outcome == SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF:
            trade_off_present = True

    if trade_off_present:
        return SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF

    if improvement_present:
        return SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT

    return SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL


def _build_section_summary_text(
    title: str,
    impact_level: str,
    outcome_tone: str,
    top_change_label: str | None,
    summary_label: str,
) -> str:
    """Return one concise planner-facing summary sentence for a section card."""

    section_label = title.lower()
    lead_metric = (
        top_change_label
        if top_change_label is not None
        else f"{section_label} outcomes"
    )

    if impact_level == SCENARIO_SECTION_IMPACT_NONE:
        return f"No material differences detected in {section_label}."

    if summary_label == "Mixed":
        if impact_level == SCENARIO_SECTION_IMPACT_MAJOR:
            return (
                f"Scenario B improves some {section_label} outcomes but introduces "
                f"trade-offs, led by {lead_metric}."
            )
        return (
            f"Scenario B slightly reshapes {section_label} with both benefits and "
            f"trade-offs, led by {lead_metric}."
        )

    if outcome_tone == SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT:
        if impact_level == SCENARIO_SECTION_IMPACT_MAJOR:
            return (
                f"Scenario B shows a strong improvement signal in {section_label}, "
                f"led by {lead_metric}."
            )
        return (
            f"Scenario B shows a limited improvement signal in {section_label}, "
            f"led by {lead_metric}."
        )

    if outcome_tone == SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF:
        if impact_level == SCENARIO_SECTION_IMPACT_MAJOR:
            return (
                f"Scenario B changes {section_label} with a material trade-off "
                f"signal, led by {lead_metric}."
            )
        return (
            f"Scenario B changes {section_label} with a limited trade-off "
            f"signal, led by {lead_metric}."
        )

    if impact_level == SCENARIO_SECTION_IMPACT_MAJOR:
        return f"Scenario B materially shifts {section_label}, led by {lead_metric}."

    return f"Scenario B slightly shifts {section_label}, led by {lead_metric}."


def _top_section_change_label(
    section: ScenarioComparisonDisplaySection,
) -> str | None:
    """Return the highest-priority meaningful change label for one decision area."""

    for metric in section.numeric_metrics:
        if _interpret_metric_for_highlight(metric).meaningful:
            return metric.label

    for metric in section.status_metrics:
        if _interpret_metric_for_highlight(metric).meaningful:
            return metric.label

    return None


def _build_metric_buckets(
    numeric_metrics: tuple[ScenarioComparisonDisplayMetric, ...],
    status_metrics: tuple[ScenarioComparisonDisplayMetric, ...],
) -> ScenarioComparisonDisplayMetricBuckets:
    """Return grouped metric buckets for summary-first card rendering."""

    primary_metrics: list[ScenarioComparisonDisplayMetric] = []
    secondary_metrics: list[ScenarioComparisonDisplayMetric] = []
    unchanged_metrics: list[ScenarioComparisonDisplayMetric] = []

    for metric in (*numeric_metrics, *status_metrics):
        interpretation = _interpret_metric_for_highlight(metric)
        if interpretation.meaningful:
            primary_metrics.append(metric)
            continue

        if _metric_is_unchanged(metric):
            unchanged_metrics.append(metric)
            continue

        secondary_metrics.append(metric)

    return ScenarioComparisonDisplayMetricBuckets(
        primary_metrics=tuple(primary_metrics),
        secondary_metrics=tuple(secondary_metrics),
        unchanged_metrics=tuple(unchanged_metrics),
    )


def _metric_is_unchanged(metric: ScenarioComparisonDisplayMetric) -> bool:
    """Return whether one prepared comparison metric should count as unchanged."""

    if metric.change_mode in {
        SCENARIO_CHANGE_NONE,
        SCENARIO_CHANGE_NOT_APPLICABLE,
    }:
        return metric.scenario_a_value == metric.scenario_b_value

    if metric.change_value is None:
        return metric.scenario_a_value == metric.scenario_b_value

    return (
        metric.change_value in (0, 0.0)
        and metric.scenario_a_value == metric.scenario_b_value
    )


def _section_visualization_intent(section_id: str) -> str:
    """Return whether a decision area should look for supporting visuals."""

    if section_id in {"infrastructure", "queueing", "grid", "power_quality"}:
        return SCENARIO_SECTION_VISUALIZATION_SUPPORTING_WHEN_USEFUL

    return SCENARIO_SECTION_VISUALIZATION_NONE


def _meaningful_section_interpretations(
    numeric_metrics: tuple[ScenarioComparisonDisplayMetric, ...],
    status_metrics: tuple[ScenarioComparisonDisplayMetric, ...],
) -> tuple[tuple[ScenarioComparisonDisplayMetric, ScenarioComparisonMetricInterpretation], ...]:
    """Return meaningful section interpretations in section display order."""

    interpretations: list[
        tuple[ScenarioComparisonDisplayMetric, ScenarioComparisonMetricInterpretation]
    ] = []

    for metric in numeric_metrics:
        interpretation = _interpret_metric_for_highlight(metric)
        if interpretation.meaningful:
            interpretations.append((metric, interpretation))

    for metric in status_metrics:
        interpretation = _interpret_metric_for_highlight(metric)
        if interpretation.meaningful:
            interpretations.append((metric, interpretation))

    return tuple(interpretations)


def _numeric_change_is_material(
    metric: ScenarioComparisonDisplayMetric,
) -> bool:
    """Return whether one numeric comparison delta is large enough to summarize."""

    return is_numeric_change_material(
        metric.change_value,
        absolute_materiality_threshold=metric.absolute_materiality_threshold,
        relative_materiality_threshold=metric.relative_materiality_threshold,
        relative_change_percent=metric.relative_change_percent,
        baseline_value=metric.scenario_a_value or 0.0,
    )


def _numeric_metric_signal_score(
    metric: ScenarioComparisonDisplayMetric,
) -> float:
    """Return magnitude-based signal score for one numeric comparison metric."""

    if metric.relative_change_percent is not None:
        return abs(float(metric.relative_change_percent))

    return relative_shift_percent(
        metric.change_value,
        metric.scenario_a_value or 0.0,
    )


def _status_metric_severity(
    value_format: str,
    value: Any,
) -> float | None:
    """Return an ordinal severity score for supported categorical comparisons."""

    if value_format in {"queue_present", "overload_indicator"}:
        return 1.0 if bool(value) else 0.0

    if value_format in {"thermal_risk_level", "power_quality_risk_level"}:
        return {
            "low": 0.0,
            "moderate": 1.0,
            "high": 2.0,
        }.get(str(value).lower())

    return None


def _metric(
    metric_id: str,
    label: str,
    value_format: str,
    scenario_a_value: Any,
    scenario_b_value: Any,
    *,
    change_format: str | None = None,
    change_value: Any | None = None,
    relative_change_percent: float | None = None,
    scenario_value_state: str = SCENARIO_VALUE_REQUIRED,
    scenario_value_reason: str | None = None,
    change_mode: str = SCENARIO_CHANGE_DELTA,
    change_reason: str | None = None,
    display_priority: int = 100,
    section_signal_weight: float = 0.0,
) -> ScenarioComparisonDisplayMetric:
    """Return one prepared numeric comparison metric."""

    rule = SCENARIO_COMPARISON_INTERPRETATION_RULES[metric_id]
    normalized_change_value = (
        normalize_numeric_delta_for_display(
            change_value,
            change_format or value_format,
        )
        if change_value is not None
        else None
    )

    return ScenarioComparisonDisplayMetric(
        metric_id=metric_id,
        label=label,
        value_format=value_format,
        scenario_a_value=scenario_a_value,
        scenario_b_value=scenario_b_value,
        change_format=change_format,
        change_value=normalized_change_value,
        relative_change_percent=relative_change_percent,
        scenario_value_state=scenario_value_state,
        scenario_value_reason=scenario_value_reason,
        change_mode=change_mode,
        change_reason=change_reason,
        display_priority=display_priority,
        preferred_direction=rule.preferred_direction,
        section_signal_weight=section_signal_weight,
        absolute_materiality_threshold=rule.absolute_materiality_threshold,
        relative_materiality_threshold=rule.relative_materiality_threshold,
        semantic_priority_tier=rule.semantic_priority_tier,
        always_meaningful_status_change=rule.always_meaningful_status_change,
    )


def _calculate_defined_difference(
    value_b: int | float | None,
    value_a: int | float | None,
) -> int | float | None:
    """Return Scenario B minus Scenario A only when both values exist."""

    if value_b is None or value_a is None:
        return None

    return value_b - value_a


def _calculate_defined_relative_change_percent(
    value_b: int | float | None,
    value_a: int | float | None,
) -> float | None:
    """Return relative percent change only when both values exist and baseline is nonzero."""

    if value_b is None or value_a in (None, 0, 0.0):
        return None

    return (float(value_b) - float(value_a)) / float(value_a) * 100.0


def _status_metric(
    metric_id: str,
    label: str,
    value_format: str,
    scenario_a_value: Any,
    scenario_b_value: Any,
    *,
    display_priority: int = 100,
    section_signal_weight: float = 0.0,
) -> ScenarioComparisonDisplayMetric:
    """Return one prepared categorical comparison metric."""

    rule = SCENARIO_COMPARISON_INTERPRETATION_RULES[metric_id]

    return ScenarioComparisonDisplayMetric(
        metric_id=metric_id,
        label=label,
        value_format=value_format,
        scenario_a_value=scenario_a_value,
        scenario_b_value=scenario_b_value,
        change_mode=SCENARIO_CHANGE_NONE,
        display_priority=display_priority,
        preferred_direction=rule.preferred_direction,
        section_signal_weight=section_signal_weight,
        absolute_materiality_threshold=rule.absolute_materiality_threshold,
        relative_materiality_threshold=rule.relative_materiality_threshold,
        semantic_priority_tier=rule.semantic_priority_tier,
        always_meaningful_status_change=rule.always_meaningful_status_change,
    )


def _overview_item(
    label: str,
    theme: str,
    change_format: str,
    raw_change: float | int,
    baseline_value: float | int,
) -> ScenarioComparisonOverviewItem:
    """Return one prepared overview item for the difference chart."""

    if raw_change > 0:
        direction_label = "Scenario B higher"
    elif raw_change < 0:
        direction_label = "Scenario B lower"
    else:
        direction_label = "No change"

    return ScenarioComparisonOverviewItem(
        label=label,
        theme=theme,
        change_format=change_format,
        raw_change=raw_change,
        relative_shift_percent=relative_shift_percent(raw_change, baseline_value),
        direction_label=direction_label,
    )


def _executive_metric(
    metric_id: str,
    title: str,
    why_it_matters: str,
    value_format: str,
    change_format: str,
    scenario_a_value: Any,
    scenario_b_value: Any,
    change_value: Any,
    relative_change_percent: float | None,
    *,
    preferred_direction: str,
) -> ScenarioComparisonExecutiveMetric:
    """Return one prepared executive-summary KPI."""

    normalized_change_value = normalize_numeric_delta_for_display(
        change_value,
        change_format,
    )
    executive_metric = ScenarioComparisonExecutiveMetric(
        metric_id=metric_id,
        title=title,
        why_it_matters=why_it_matters,
        value_format=value_format,
        change_format=change_format,
        scenario_a_value=scenario_a_value,
        scenario_b_value=scenario_b_value,
        change_value=normalized_change_value,
        relative_change_percent=relative_change_percent,
        relative_shift_percent=relative_shift_percent(
            normalized_change_value,
            scenario_a_value,
        ),
        outcome=_executive_outcome(normalized_change_value, preferred_direction),
    )
    return replace(
        executive_metric,
        display_outcome=_interpret_executive_metric(executive_metric).outcome,
    )


def _executive_outcome(
    change_value: Any,
    preferred_direction: str,
) -> str:
    """Classify whether Scenario B is better, worse, or unchanged for one KPI."""

    return classify_directional_outcome(
        change_value,
        preferred_direction,
    )
