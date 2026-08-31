"""Scenario A/B comparison rendering helpers."""

from ._shared import *
from .formatters import *
from .figures import *
from .smart_charging import _comparison_table_row
from dashboard.state import _comparison_metrics_from_dict, _normalize_scenario_comparison_builder_ui_state, _resolve_scenario_ab_display_labels, _scenario_comparison_builder_is_collapsed, _scenario_comparison_collapsed_status_summary

def _comparison_kpi_card(
    title: str,
    subtitle: str,
    value: Any,
    *,
    context: str | None = None,
    emphasized: bool = False,
) -> Any:
    """Return a compact presentation card for a comparison KPI."""
    children = [html.Strong(title)]
    if subtitle:
        children.append(html.Span(subtitle, style=KPI_LABEL_TEXT_STYLE))
    children.append(
        html.Span(
            value,
            style=(
                INFRASTRUCTURE_KPI_VALUE_EMPHASIS_STYLE
                if emphasized
                else KPI_VALUE_TEXT_STYLE
            ),
        )
    )
    if context is not None:
        children.append(
            html.Span(
                context,
                style=SUPPORTING_TEXT_STYLE,
            )
        )

    return html.Div(
        children,
        style=(
            {**KPI_CARD_STYLE, **INFRASTRUCTURE_KPI_EMPHASIS_STYLE}
            if emphasized
            else KPI_CARD_STYLE
        ),
    )

def _scenario_ab_kpi_card(
    metric: ScenarioComparisonExecutiveMetric,
    *,
    scenario_a_label: str = "Scenario A",
    scenario_b_label: str = "Scenario B",
) -> Any:
    """Return a compact headline Scenario A/B KPI card."""

    scenario_a_value = _format_scenario_ab_scalar_value(
        metric.value_format,
        metric.scenario_a_value,
    )
    scenario_b_value = _format_scenario_ab_scalar_value(
        metric.value_format,
        metric.scenario_b_value,
    )
    change_value = _scenario_ab_compact_change_text(metric)
    children = [
        html.Strong(metric.title),
        html.Span(
            change_value,
            style=_scenario_ab_executive_change_style(metric.display_outcome),
        ),
        html.Span(
            (
                f"{_scenario_ab_compact_context_label(scenario_a_label, 'A')} "
                f"{scenario_a_value} -> "
                f"{_scenario_ab_compact_context_label(scenario_b_label, 'B')} "
                f"{scenario_b_value}"
            ),
            style=KPI_LABEL_TEXT_STYLE,
        ),
    ]

    return html.Div(children, style=_scenario_ab_executive_card_style(metric.display_outcome))

def _scenario_ab_compact_change_text(
    metric: ScenarioComparisonExecutiveMetric,
) -> str:
    """Return the compact primary change text for one executive KPI."""

    difference_value = _format_scenario_ab_scalar_value(
        metric.change_format,
        metric.change_value,
    )
    difference_value = difference_value.removeprefix("+").removeprefix("-")
    if metric.display_outcome == SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT:
        return f"↓ {difference_value}"
    if metric.display_outcome == SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF:
        return f"↑ {difference_value}"
    return difference_value

def _scenario_ab_executive_change_style(outcome: str) -> dict[str, str]:
    """Return compact value styling for one Scenario A/B executive KPI."""

    style = {
        **KPI_VALUE_TEXT_STYLE,
        "fontSize": "1.35rem",
        "lineHeight": "1.2",
    }
    if outcome == SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT:
        return {
            **style,
            "color": STATUS_GREEN,
        }
    if outcome == SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF:
        return {
            **style,
            "color": STATUS_RED,
        }
    return {
        **style,
        "color": TEXT_SECONDARY_COLOR,
    }

def _scenario_ab_executive_card_style(outcome: str) -> dict[str, str]:
    """Return compact card styling for one Scenario A/B executive KPI."""

    style = {
        **KPI_CARD_STYLE,
        "padding": "0.95rem 1rem",
        "gap": "0.28rem",
    }
    if outcome == SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT:
        return {
            **style,
            "backgroundColor": STATUS_GREEN_BACKGROUND,
            "boxShadow": f"inset 3px 0 0 {STATUS_GREEN}",
        }
    if outcome == SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF:
        return {
            **style,
            "backgroundColor": STATUS_RED_BACKGROUND,
            "boxShadow": f"inset 3px 0 0 {STATUS_RED}",
        }
    return {
        **style,
        "backgroundColor": SUBTLE_SURFACE_BACKGROUND_COLOR,
    }

def _scenario_ab_compact_context_label(label: str, fallback: str) -> str:
    """Return a short context label for compact executive KPI cards."""

    normalized = label.strip()
    if normalized in {"Scenario A", "Scenario B"}:
        return normalized.replace("Scenario ", "")
    return fallback

def _format_scenario_ab_absolute_change_value(
    change_format: str | None,
    change_value: Any,
) -> str:
    """Return an unsigned narrative-friendly change magnitude for one value."""

    absolute_change = abs(float(change_value))

    if change_format == "power_kw_signed":
        return format_power_kw(absolute_change)
    if change_format == "percentage_points_signed":
        return format_percentage_points(absolute_change)
    if change_format == "energy_kwh_signed":
        return format_energy_kwh(absolute_change)
    if change_format == "score_points_signed":
        return f"{absolute_change:,.1f} pts"
    if change_format == "vehicle_count_0_signed":
        return format_vehicle_count(absolute_change)
    if change_format == "vehicle_count_1_signed":
        return format_vehicle_count(absolute_change, decimals=1)
    if change_format == "charger_count_0_signed":
        return format_charger_count(absolute_change)
    if change_format == "charger_count_1_signed":
        return format_charger_count(absolute_change, decimals=1)
    if change_format == "warning_count_signed":
        return format_warning_count(int(absolute_change))
    if change_format == "hours_signed":
        return format_hours(absolute_change)
    if change_format == "feeder_count_signed":
        return format_feeder_count(int(absolute_change))

    return _format_scenario_ab_scalar_value(change_format, change_value)

def render_scenario_ab_executive_summary_cards(
    metrics_a: Metrics,
    metrics_b: Metrics,
    comparison_metrics: ScenarioComparisonMetrics,
    *,
    scenario_a_label: str = "Scenario A",
    scenario_b_label: str = "Scenario B",
) -> list[Any]:
    """Render headline Scenario A/B comparison KPIs as summary cards."""

    display_data = prepare_scenario_comparison_display_data(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )
    return _render_scenario_ab_executive_summary_cards_from_display_data(
        display_data,
        scenario_a_label=scenario_a_label,
        scenario_b_label=scenario_b_label,
    )

def _render_scenario_ab_executive_summary_cards_from_display_data(
    display_data: ScenarioComparisonDisplayData,
    *,
    scenario_a_label: str,
    scenario_b_label: str,
) -> list[Any]:
    """Render headline cards from prepared executive-summary display data."""

    return [
        _scenario_ab_kpi_card(
            metric,
            scenario_a_label=scenario_a_label,
            scenario_b_label=scenario_b_label,
        )
        for metric in display_data.executive_metrics
    ]

def build_scenario_ab_comparison_rows(
    metrics_a: Metrics,
    metrics_b: Metrics,
    comparison_metrics: ScenarioComparisonMetrics,
) -> list[tuple[str, str, str, str, str]]:
    """Map existing Scenario A/B metrics into display table rows."""
    return [
        (
            "Peak load (kW)",
            format_power_kw(metrics_a.peak_load),
            format_power_kw(metrics_b.peak_load),
            format_signed_power_kw(comparison_metrics.peak_load_difference_kw),
            format_change_percent(comparison_metrics.peak_load_change_percent),
        ),
        (
            "Capacity utilization (%)",
            format_percent(metrics_a.capacity_utilization),
            format_percent(metrics_b.capacity_utilization),
            format_signed_percentage_points(
                comparison_metrics.capacity_utilization_difference_percentage_points
            ),
            format_change_percent(
                comparison_metrics.capacity_utilization_change_percent
            ),
        ),
        (
            "Delivered energy (kWh)",
            format_energy_kwh(metrics_a.delivered_energy),
            format_energy_kwh(metrics_b.delivered_energy),
            format_signed_energy_kwh(
                comparison_metrics.delivered_energy_difference_kwh
            ),
            format_change_percent(
                comparison_metrics.delivered_energy_change_percent
            ),
        ),
        (
            "Unmet energy (kWh)",
            format_energy_kwh(metrics_a.unmet_energy),
            format_energy_kwh(metrics_b.unmet_energy),
            format_signed_energy_kwh(comparison_metrics.unmet_energy_difference_kwh),
            format_change_percent(comparison_metrics.unmet_energy_change_percent),
        ),
        (
            "Peak harmonic risk score",
            format_risk_score(metrics_a.peak_harmonic_risk_score),
            format_risk_score(metrics_b.peak_harmonic_risk_score),
            format_signed_score_points(
                comparison_metrics.peak_harmonic_risk_score_difference
            ),
            NOT_APPLICABLE_METRIC_TEXT,
        ),
        (
            "Harmonic risk duration (h)",
            format_hours(metrics_a.harmonic_risk_duration_hours),
            format_hours(metrics_b.harmonic_risk_duration_hours),
            format_signed_hours(
                comparison_metrics.harmonic_risk_duration_hours_difference
            ),
            NOT_APPLICABLE_METRIC_TEXT,
        ),
        (
            "Peak current imbalance (%)",
            format_percent(metrics_a.peak_current_imbalance_percent),
            format_percent(metrics_b.peak_current_imbalance_percent),
            format_signed_percentage_points(
                comparison_metrics.peak_current_imbalance_percent_difference
            ),
            NOT_APPLICABLE_METRIC_TEXT,
        ),
        (
            "Current imbalance duration (h)",
            format_hours(metrics_a.imbalance_duration_hours),
            format_hours(metrics_b.imbalance_duration_hours),
            format_signed_hours(
                comparison_metrics.imbalance_duration_hours_difference
            ),
            NOT_APPLICABLE_METRIC_TEXT,
        ),
        (
            "Overall PQ risk score",
            format_risk_score(metrics_a.overall_pq_risk_score),
            format_risk_score(metrics_b.overall_pq_risk_score),
            format_signed_score_points(
                comparison_metrics.overall_pq_risk_score_difference
            ),
            NOT_APPLICABLE_METRIC_TEXT,
        ),
        (
            "PQ warning count",
            format_warning_count(metrics_a.power_quality_warning_count),
            format_warning_count(metrics_b.power_quality_warning_count),
            format_signed_warning_count(
                comparison_metrics.power_quality_warning_count_difference
            ),
            NOT_APPLICABLE_METRIC_TEXT,
        ),
    ]

def build_scenario_ab_charger_availability_rows(
    metrics_a: Metrics,
    metrics_b: Metrics,
    comparison_metrics: ScenarioComparisonMetrics,
) -> list[tuple[str, Any, Any, Any]]:
    """Map Scenario A/B charger-availability metrics into display rows."""
    return [
        (
            "Average transformer loading (%)",
            format_percent(metrics_a.average_transformer_loading_percent),
            format_percent(metrics_b.average_transformer_loading_percent),
            format_signed_percentage_points(
                comparison_metrics.average_transformer_loading_percent_difference
            ),
        ),
        (
            "Peak transformer loading (%)",
            format_percent(metrics_a.peak_transformer_loading_percent),
            format_percent(metrics_b.peak_transformer_loading_percent),
            format_signed_percentage_points(
                comparison_metrics.peak_transformer_loading_percent_difference
            ),
        ),
        (
            "Transformer overload",
            _format_overload_indicator_value(
                metrics_a.transformer_overload_indicator
            ),
            _format_overload_indicator_value(
                metrics_b.transformer_overload_indicator
            ),
            _undefined_metric_value(
                "Transformer overload difference",
                NON_NUMERIC_DIFFERENCE_NOT_APPLICABLE_HELPER,
                text=NOT_APPLICABLE_METRIC_TEXT,
            ),
        ),
        (
            "Transformer overload duration (h)",
            format_hours(metrics_a.transformer_overload_duration_hours),
            format_hours(metrics_b.transformer_overload_duration_hours),
            format_signed_hours(
                comparison_metrics.transformer_overload_duration_hours_difference
            ),
        ),
        (
            "Maximum transformer overload (kW)",
            format_power_kw(metrics_a.transformer_maximum_overload_kw),
            format_power_kw(metrics_b.transformer_maximum_overload_kw),
            format_signed_power_kw(
                comparison_metrics.transformer_maximum_overload_kw_difference
            ),
        ),
        (
            "Transformer thermal risk",
            format_thermal_risk_level(metrics_a.transformer_thermal_risk_level),
            format_thermal_risk_level(metrics_b.transformer_thermal_risk_level),
            _undefined_metric_value(
                "Transformer thermal risk difference",
                NON_NUMERIC_DIFFERENCE_NOT_APPLICABLE_HELPER,
                text=NOT_APPLICABLE_METRIC_TEXT,
            ),
        ),
        (
            "Maximum feeder loading (%)",
            format_percent(metrics_a.maximum_feeder_loading_percent),
            format_percent(metrics_b.maximum_feeder_loading_percent),
            format_signed_percentage_points(
                comparison_metrics.maximum_feeder_loading_percent_difference
            ),
        ),
        (
            "Feeder overload",
            _format_overload_indicator_value(metrics_a.feeder_overload_indicator),
            _format_overload_indicator_value(metrics_b.feeder_overload_indicator),
            _undefined_metric_value(
                "Feeder overload difference",
                NON_NUMERIC_DIFFERENCE_NOT_APPLICABLE_HELPER,
                text=NOT_APPLICABLE_METRIC_TEXT,
            ),
        ),
        (
            "Overloaded feeders",
            format_feeder_count(metrics_a.overloaded_feeder_count),
            format_feeder_count(metrics_b.overloaded_feeder_count),
            format_signed_feeder_count(
                comparison_metrics.overloaded_feeder_count_difference
            ),
        ),
        (
            "Highest feeder thermal risk",
            format_thermal_risk_level(metrics_a.highest_feeder_thermal_risk_level),
            format_thermal_risk_level(metrics_b.highest_feeder_thermal_risk_level),
            _undefined_metric_value(
                "Highest feeder thermal risk difference",
                NON_NUMERIC_DIFFERENCE_NOT_APPLICABLE_HELPER,
                text=NOT_APPLICABLE_METRIC_TEXT,
            ),
        ),
        (
            "Harmonic risk level",
            format_power_quality_risk_level(metrics_a.harmonic_risk_level),
            format_power_quality_risk_level(metrics_b.harmonic_risk_level),
            _undefined_metric_value(
                "Harmonic risk level difference",
                NON_NUMERIC_DIFFERENCE_NOT_APPLICABLE_HELPER,
                text=NOT_APPLICABLE_METRIC_TEXT,
            ),
        ),
        (
            "Current imbalance risk level",
            format_power_quality_risk_level(metrics_a.current_imbalance_risk_level),
            format_power_quality_risk_level(metrics_b.current_imbalance_risk_level),
            _undefined_metric_value(
                "Current imbalance risk difference",
                NON_NUMERIC_DIFFERENCE_NOT_APPLICABLE_HELPER,
                text=NOT_APPLICABLE_METRIC_TEXT,
            ),
        ),
        (
            "Overall PQ risk level",
            format_power_quality_risk_level(metrics_a.overall_pq_risk_level),
            format_power_quality_risk_level(metrics_b.overall_pq_risk_level),
            _undefined_metric_value(
                "Overall PQ risk level difference",
                NON_NUMERIC_DIFFERENCE_NOT_APPLICABLE_HELPER,
                text=NOT_APPLICABLE_METRIC_TEXT,
            ),
        ),
        (
            "Average charger utilization (%)",
            _optional_metric_value(
                metrics_a.average_charger_utilization_percent,
                format_percent,
                label="Scenario A average charger utilization",
                explanation=CHARGER_UTILIZATION_UNAVAILABLE_HELPER,
            ),
            _optional_metric_value(
                metrics_b.average_charger_utilization_percent,
                format_percent,
                label="Scenario B average charger utilization",
                explanation=CHARGER_UTILIZATION_UNAVAILABLE_HELPER,
            ),
            _undefined_metric_value(
                "Average charger utilization difference",
                NON_NUMERIC_DIFFERENCE_NOT_APPLICABLE_HELPER,
                text=NOT_APPLICABLE_METRIC_TEXT,
            ),
        ),
        (
            "Peak charger utilization (%)",
            _optional_metric_value(
                metrics_a.peak_charger_utilization_percent,
                format_percent,
                label="Scenario A peak charger utilization",
                explanation=CHARGER_UTILIZATION_UNAVAILABLE_HELPER,
            ),
            _optional_metric_value(
                metrics_b.peak_charger_utilization_percent,
                format_percent,
                label="Scenario B peak charger utilization",
                explanation=CHARGER_UTILIZATION_UNAVAILABLE_HELPER,
            ),
            _undefined_metric_value(
                "Peak charger utilization difference",
                NON_NUMERIC_DIFFERENCE_NOT_APPLICABLE_HELPER,
                text=NOT_APPLICABLE_METRIC_TEXT,
            ),
        ),
        (
            "Average occupied chargers",
            format_charger_count(
                metrics_a.average_occupied_charger_count,
                decimals=1,
            ),
            format_charger_count(
                metrics_b.average_occupied_charger_count,
                decimals=1,
            ),
            format_signed_charger_count(
                comparison_metrics.average_occupied_charger_count_difference,
                decimals=1,
            ),
        ),
        (
            "Peak occupied chargers",
            format_charger_count(metrics_a.peak_occupied_charger_count),
            format_charger_count(metrics_b.peak_occupied_charger_count),
            format_signed_charger_count(
                comparison_metrics.peak_occupied_charger_count_difference
            ),
        ),
        (
            "Queue present",
            _format_queue_present_value(metrics_a.queue_present_indicator),
            _format_queue_present_value(metrics_b.queue_present_indicator),
            _undefined_metric_value(
                "Queue present difference",
                NON_NUMERIC_DIFFERENCE_NOT_APPLICABLE_HELPER,
                text=NOT_APPLICABLE_METRIC_TEXT,
            ),
        ),
        (
            "Maximum queue length",
            format_vehicle_count(metrics_a.maximum_queue_length),
            format_vehicle_count(metrics_b.maximum_queue_length),
            format_signed_vehicle_count(
                comparison_metrics.maximum_queue_length_difference
            ),
        ),
        (
            "Average queue length",
            format_vehicle_count(metrics_a.average_queue_length, decimals=1),
            format_vehicle_count(metrics_b.average_queue_length, decimals=1),
            format_signed_vehicle_count(
                comparison_metrics.average_queue_length_difference,
                decimals=1,
            ),
        ),
        (
            "Queue duration (h)",
            format_hours(metrics_a.queue_duration_hours),
            format_hours(metrics_b.queue_duration_hours),
            format_signed_hours(comparison_metrics.queue_duration_hours_difference),
        ),
        (
            "Average waiting time (h)",
            _optional_metric_value(
                metrics_a.average_waiting_time_hours,
                format_hours,
                label="Scenario A average waiting time",
                explanation=WAITING_TIME_UNAVAILABLE_HELPER,
            ),
            _optional_metric_value(
                metrics_b.average_waiting_time_hours,
                format_hours,
                label="Scenario B average waiting time",
                explanation=WAITING_TIME_UNAVAILABLE_HELPER,
            ),
            _optional_metric_value(
                comparison_metrics.average_waiting_time_hours_difference,
                format_signed_hours,
                label="Average waiting time difference",
                explanation=DIFFERENCE_UNAVAILABLE_HELPER,
            ),
        ),
        (
            "Maximum waiting time (h)",
            _optional_metric_value(
                metrics_a.maximum_waiting_time_hours,
                format_hours,
                label="Scenario A maximum waiting time",
                explanation=WAITING_TIME_UNAVAILABLE_HELPER,
            ),
            _optional_metric_value(
                metrics_b.maximum_waiting_time_hours,
                format_hours,
                label="Scenario B maximum waiting time",
                explanation=WAITING_TIME_UNAVAILABLE_HELPER,
            ),
            _optional_metric_value(
                comparison_metrics.maximum_waiting_time_hours_difference,
                format_signed_hours,
                label="Maximum waiting time difference",
                explanation=DIFFERENCE_UNAVAILABLE_HELPER,
            ),
        ),
        (
            "Vehicles waiting",
            format_vehicle_count(metrics_a.vehicles_waiting_count),
            format_vehicle_count(metrics_b.vehicles_waiting_count),
            format_signed_vehicle_count(
                comparison_metrics.vehicles_waiting_count_difference
            ),
        ),
        (
            "Vehicles not started",
            format_vehicle_count(metrics_a.vehicles_not_started_count),
            format_vehicle_count(metrics_b.vehicles_not_started_count),
            format_signed_vehicle_count(
                comparison_metrics.vehicles_not_started_count_difference
            ),
        ),
        (
            "Vehicles with unmet energy",
            format_vehicle_count(metrics_a.vehicles_with_unmet_energy_count),
            format_vehicle_count(metrics_b.vehicles_with_unmet_energy_count),
            format_signed_vehicle_count(
                comparison_metrics.vehicles_with_unmet_energy_count_difference
            ),
        ),
        (
            "Charger capacity vs demand balance",
            format_charger_count(metrics_a.charger_capacity_vs_demand_balance),
            format_charger_count(metrics_b.charger_capacity_vs_demand_balance),
            format_signed_charger_count(
                comparison_metrics.charger_capacity_vs_demand_balance_difference
            ),
        ),
        (
            "Required charger count",
            _optional_metric_value(
                metrics_a.required_charger_count,
                format_charger_count,
                label="Scenario A required charger count",
                explanation=REQUIRED_CHARGER_COUNT_NOT_APPLICABLE_HELPER,
                text=NOT_APPLICABLE_METRIC_TEXT,
            ),
            _optional_metric_value(
                metrics_b.required_charger_count,
                format_charger_count,
                label="Scenario B required charger count",
                explanation=REQUIRED_CHARGER_COUNT_NOT_APPLICABLE_HELPER,
                text=NOT_APPLICABLE_METRIC_TEXT,
            ),
            _optional_metric_value(
                comparison_metrics.required_charger_count_difference,
                format_signed_charger_count,
                label="Required charger count difference",
                explanation=DIFFERENCE_UNAVAILABLE_HELPER,
            ),
        ),
        (
            "Additional chargers required",
            _optional_metric_value(
                metrics_a.additional_chargers_required,
                format_charger_count,
                label="Scenario A additional chargers required",
                explanation=ADDITIONAL_CHARGERS_NOT_APPLICABLE_HELPER,
                text=NOT_APPLICABLE_METRIC_TEXT,
            ),
            _optional_metric_value(
                metrics_b.additional_chargers_required,
                format_charger_count,
                label="Scenario B additional chargers required",
                explanation=ADDITIONAL_CHARGERS_NOT_APPLICABLE_HELPER,
                text=NOT_APPLICABLE_METRIC_TEXT,
            ),
            _optional_metric_value(
                comparison_metrics.additional_chargers_required_difference,
                format_signed_charger_count,
                label="Additional chargers required difference",
                explanation=DIFFERENCE_UNAVAILABLE_HELPER,
            ),
        ),
        (
            "Primary constraint reason",
            format_primary_constraint_reason(metrics_a.primary_constraint_reason),
            format_primary_constraint_reason(metrics_b.primary_constraint_reason),
            _undefined_metric_value(
                "Primary constraint reason difference",
                NON_NUMERIC_DIFFERENCE_NOT_APPLICABLE_HELPER,
                text=NOT_APPLICABLE_METRIC_TEXT,
            ),
        ),
    ]

def render_scenario_ab_comparison_table(
    metrics_a: Metrics,
    metrics_b: Metrics,
    comparison_metrics: ScenarioComparisonMetrics,
    *,
    scenario_a_label: str = "Scenario A",
    scenario_b_label: str = "Scenario B",
) -> Any:
    """Render existing Scenario A/B metrics in a side-by-side table."""
    rows = build_scenario_ab_comparison_rows(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )
    return html.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Metric", style=TABLE_HEADER_CELL_STYLE),
                        html.Th(scenario_a_label, style=TABLE_HEADER_CELL_STYLE),
                        html.Th(scenario_b_label, style=TABLE_HEADER_CELL_STYLE),
                        html.Th("Difference", style=TABLE_HEADER_CELL_STYLE),
                        html.Th("Change", style=TABLE_HEADER_CELL_STYLE),
                    ]
                )
            ),
            html.Tbody([_comparison_table_row(row) for row in rows]),
        ],
        style=TABLE_STYLE,
    )

def render_scenario_ab_charger_availability_table(
    metrics_a: Metrics,
    metrics_b: Metrics,
    comparison_metrics: ScenarioComparisonMetrics,
    *,
    scenario_a_label: str = "Scenario A",
    scenario_b_label: str = "Scenario B",
) -> Any:
    """Render Scenario A/B charger-availability metrics in a table."""
    rows = build_scenario_ab_charger_availability_rows(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )
    return html.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Metric", style=TABLE_HEADER_CELL_STYLE),
                        html.Th(scenario_a_label, style=TABLE_HEADER_CELL_STYLE),
                        html.Th(scenario_b_label, style=TABLE_HEADER_CELL_STYLE),
                        html.Th("Difference", style=TABLE_HEADER_CELL_STYLE),
                    ]
                )
            ),
            html.Tbody([_comparison_table_row(row) for row in rows]),
        ],
        style=TABLE_STYLE,
    )

def _render_scenario_ab_chart_or_message(
    title: str,
    *,
    figure: go.Figure | None = None,
    graph_id: str | None = None,
    hidden_message: str | None = None,
) -> Any:
    """Render a chart when it adds value, otherwise a concise helper message."""

    if figure is None:
        return html.Div(
            [
                html.H4(
                    title,
                    className="scenario-ab-evidence-chart-title",
                    style={"margin": "0"},
                ),
                html.Div(
                    html.P(
                        hidden_message or "This comparison chart is not shown.",
                        style={"color": TEXT_SECONDARY_COLOR, "marginBottom": "0"},
                    ),
                    className=(
                        "scenario-ab-evidence-chart-shell "
                        "scenario-ab-evidence-chart-shell--message"
                    ),
                    style={"marginTop": "0", "width": "100%"},
                ),
            ],
            className="scenario-ab-evidence-chart-block",
            style={"marginTop": "0", "width": "100%"},
        )

    return html.Div(
        [
            html.H4(
                title,
                className="scenario-ab-evidence-chart-title",
                style={"margin": "0"},
            ),
            html.Div(
                dcc.Graph(
                    id=graph_id,
                    figure=figure,
                    config={"responsive": True},
                    style={**GRAPH_STYLE, "width": "100%"},
                ),
                className="scenario-ab-evidence-chart-shell",
                style={"marginTop": "0", "width": "100%"},
            )
        ],
        className="scenario-ab-evidence-chart-block",
        style={"marginTop": "0", "width": "100%"},
    )

def _should_show_scenario_ab_occupancy_chart(
    metrics_a: Metrics,
    metrics_b: Metrics,
    comparison_metrics: ScenarioComparisonMetrics,
    *,
    scenario_a_label: str = "Scenario A",
    scenario_b_label: str = "Scenario B",
) -> tuple[bool, str]:
    """Return whether the occupancy chart adds useful comparison value."""

    if not metrics_a.occupied_charger_count_by_timestep or not metrics_b.occupied_charger_count_by_timestep:
        return (
            False,
            "Occupied-charger traces are unavailable for one or both scenarios.",
        )

    if (
        metrics_a.occupied_charger_count_by_timestep
        == metrics_b.occupied_charger_count_by_timestep
        and comparison_metrics.average_occupied_charger_count_difference == 0.0
        and comparison_metrics.peak_occupied_charger_count_difference == 0
    ):
        return (
            False,
            f"Hidden because {scenario_a_label} and {scenario_b_label} have identical occupied-charger traces.",
        )

    return True, ""

def _should_show_scenario_ab_queue_chart(
    metrics_a: Metrics,
    metrics_b: Metrics,
    comparison_metrics: ScenarioComparisonMetrics,
) -> tuple[bool, str]:
    """Return whether the queue chart adds useful comparison value."""

    if not metrics_a.waiting_vehicle_count_by_timestep or not metrics_b.waiting_vehicle_count_by_timestep:
        return False, "Queue-length traces are unavailable for one or both scenarios."

    if (
        metrics_a.waiting_vehicle_count_by_timestep
        == metrics_b.waiting_vehicle_count_by_timestep
        and not metrics_a.queue_present_indicator
        and not metrics_b.queue_present_indicator
        and comparison_metrics.maximum_queue_length_difference == 0
    ):
        return (
            False,
            "Hidden because neither scenario shows meaningful queueing pressure.",
        )

    return True, ""

def _should_show_scenario_ab_power_quality_chart(
    metrics_a: Metrics,
    metrics_b: Metrics,
    comparison_metrics: ScenarioComparisonMetrics,
    *,
    scenario_a_label: str = "Scenario A",
    scenario_b_label: str = "Scenario B",
) -> tuple[bool, str]:
    """Return whether the PQ chart adds useful comparison value."""

    if not metrics_a.overall_pq_risk_score_by_timestep or not metrics_b.overall_pq_risk_score_by_timestep:
        return (
            False,
            "Overall PQ risk traces are unavailable for one or both scenarios.",
        )

    if (
        metrics_a.overall_pq_risk_level == metrics_b.overall_pq_risk_level
        and comparison_metrics.power_quality_warning_count_difference == 0
        and abs(comparison_metrics.overall_pq_risk_score_difference) < 1.0
        and _float_series_are_nearly_identical(
            metrics_a.overall_pq_risk_score_by_timestep,
            metrics_b.overall_pq_risk_score_by_timestep,
            tolerance=1.0,
        )
    ):
        return (
            False,
            f"Hidden because {scenario_a_label} and {scenario_b_label} have nearly identical overall PQ risk traces.",
        )

    return True, ""

def _should_show_scenario_ab_transformer_loading_chart(
    metrics_a: Metrics,
    metrics_b: Metrics,
    comparison_metrics: ScenarioComparisonMetrics,
    *,
    scenario_a_label: str = "Scenario A",
    scenario_b_label: str = "Scenario B",
) -> tuple[bool, str]:
    """Return whether the transformer-loading chart adds useful grid evidence."""

    if (
        not metrics_a.transformer_loading_percent_by_timestep
        or not metrics_b.transformer_loading_percent_by_timestep
    ):
        return (
            False,
            "Transformer-loading traces are unavailable for one or both scenarios.",
        )

    if (
        metrics_a.transformer_loading_percent_by_timestep
        == metrics_b.transformer_loading_percent_by_timestep
        and comparison_metrics.average_transformer_loading_percent_difference == 0.0
        and comparison_metrics.peak_transformer_loading_percent_difference == 0.0
        and comparison_metrics.transformer_overload_duration_hours_difference == 0.0
        and comparison_metrics.transformer_maximum_overload_kw_difference == 0.0
    ):
        return (
            False,
            f"Hidden because {scenario_a_label} and {scenario_b_label} have identical transformer-loading traces.",
        )

    transformer_signal_present = any(
        (
            metrics_a.transformer_overload_indicator
            != metrics_b.transformer_overload_indicator,
            metrics_a.transformer_thermal_risk_level
            != metrics_b.transformer_thermal_risk_level,
            abs(comparison_metrics.peak_transformer_loading_percent_difference) >= 1.0,
            abs(comparison_metrics.average_transformer_loading_percent_difference) >= 1.0,
            abs(comparison_metrics.transformer_overload_duration_hours_difference)
            >= 0.05,
            abs(comparison_metrics.transformer_maximum_overload_kw_difference) >= 0.05,
        )
    )
    if not transformer_signal_present and _float_series_are_nearly_identical(
        metrics_a.transformer_loading_percent_by_timestep,
        metrics_b.transformer_loading_percent_by_timestep,
        tolerance=1.0,
    ):
        return (
            False,
            "Hidden because transformer-loading differences are too small to add explanatory value.",
        )

    return True, ""

def _float_series_are_nearly_identical(
    series_a: list[float],
    series_b: list[float],
    *,
    tolerance: float,
) -> bool:
    """Return whether two float series differ by no more than the tolerance."""

    if len(series_a) != len(series_b):
        return False

    return all(abs(value_a - value_b) <= tolerance for value_a, value_b in zip(series_a, series_b))

def render_scenario_ab_detailed_sections(
    metrics_a: Metrics,
    metrics_b: Metrics,
    comparison_metrics: ScenarioComparisonMetrics,
    *,
    selected_section_id: str | None = None,
    scenario_a_label: str = "Scenario A",
    scenario_b_label: str = "Scenario B",
) -> Any:
    """Render Scenario A/B detailed comparison content in themed sections."""

    display_data = prepare_scenario_comparison_display_data(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )
    return _render_scenario_ab_detailed_sections_from_display_data(
        display_data,
        metrics_a,
        metrics_b,
        comparison_metrics,
        selected_section_id=selected_section_id,
        scenario_a_label=scenario_a_label,
        scenario_b_label=scenario_b_label,
    )

def _render_scenario_ab_detailed_sections_from_display_data(
    display_data: ScenarioComparisonDisplayData,
    metrics_a: Metrics,
    metrics_b: Metrics,
    comparison_metrics: ScenarioComparisonMetrics,
    *,
    selected_section_id: str | None = None,
    scenario_a_label: str = "Scenario A",
    scenario_b_label: str = "Scenario B",
) -> Any:
    """Render Scenario A/B detailed sections from one prepared display object."""

    show_occupancy_chart, occupancy_hidden_message = (
        _should_show_scenario_ab_occupancy_chart(
            metrics_a,
            metrics_b,
            comparison_metrics,
            scenario_a_label=scenario_a_label,
            scenario_b_label=scenario_b_label,
        )
    )
    show_queue_chart, queue_hidden_message = _should_show_scenario_ab_queue_chart(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )
    show_pq_chart, pq_hidden_message = _should_show_scenario_ab_power_quality_chart(
        metrics_a,
        metrics_b,
        comparison_metrics,
        scenario_a_label=scenario_a_label,
        scenario_b_label=scenario_b_label,
    )
    show_grid_chart, grid_hidden_message = (
        _should_show_scenario_ab_transformer_loading_chart(
            metrics_a,
            metrics_b,
            comparison_metrics,
            scenario_a_label=scenario_a_label,
            scenario_b_label=scenario_b_label,
        )
    )
    selected_section = _resolve_scenario_ab_selected_section(
        display_data,
        selected_section_id,
    )

    return html.Div(
        [
            _render_scenario_ab_decision_summary(
                display_data,
                scenario_a_label=scenario_a_label,
                scenario_b_label=scenario_b_label,
            ),
            html.Div(
                [
                    html.Div(
                        [
                            _render_scenario_ab_detail_section(
                                section,
                                selected=(selected_section is not None)
                                and (selected_section.section_id == section.section_id),
                                scenario_a_label=scenario_a_label,
                                scenario_b_label=scenario_b_label,
                            )
                            for section in display_data.sections
                        ],
                        id="scenario-ab-detail-card-grid",
                        className="scenario-ab-detail-card-grid",
                        style=SCENARIO_AB_DETAIL_GRID_STYLE,
                    ),
                    _render_scenario_ab_evidence_panel(
                        selected_section,
                        metrics_a=metrics_a,
                        metrics_b=metrics_b,
                        show_occupancy_chart=show_occupancy_chart,
                        occupancy_hidden_message=occupancy_hidden_message,
                        show_queue_chart=show_queue_chart,
                        queue_hidden_message=queue_hidden_message,
                        show_pq_chart=show_pq_chart,
                        pq_hidden_message=pq_hidden_message,
                        show_grid_chart=show_grid_chart,
                        grid_hidden_message=grid_hidden_message,
                        scenario_a_label=scenario_a_label,
                        scenario_b_label=scenario_b_label,
                    ),
                ],
                id="scenario-ab-comparison-workspace",
                className="scenario-ab-comparison-workspace",
                style=SCENARIO_AB_WORKSPACE_STYLE,
            ),
        ]
    )

def _resolve_scenario_ab_selected_section(
    display_data: ScenarioComparisonDisplayData,
    selected_section_id: str | None,
) -> ScenarioComparisonDisplaySection | None:
    """Return the selected decision-area section when one is currently active."""

    if selected_section_id is None:
        return None

    return next(
        (
            section
            for section in display_data.sections
            if section.section_id == selected_section_id
        ),
        None,
    )

def _render_scenario_ab_decision_summary(
    display_data: ScenarioComparisonDisplayData,
    *,
    scenario_a_label: str,
    scenario_b_label: str,
) -> Any:
    """Render the decision-oriented comparison summary above detailed sections."""

    return html.Div(
        [
            html.H3("Decision Summary", style={"marginTop": "0"}),
            html.Div(
                [
                    _render_scenario_ab_highlight_group(
                        "Biggest Improvements",
                        display_data.improvement_highlights,
                        empty_message="No material improvements were identified.",
                        section_id="scenario-ab-biggest-improvements",
                        scenario_a_label=scenario_a_label,
                        scenario_b_label=scenario_b_label,
                    ),
                    _render_scenario_ab_highlight_group(
                        "Key Trade-offs",
                        display_data.trade_off_highlights,
                        empty_message="No significant trade-offs were identified.",
                        section_id="scenario-ab-key-trade-offs",
                        scenario_a_label=scenario_a_label,
                        scenario_b_label=scenario_b_label,
                    ),
                ],
                className="scenario-ab-decision-summary-grid",
                style=SCENARIO_AB_DECISION_SUMMARY_GRID_STYLE,
            ),
        ],
        id="scenario-ab-decision-summary",
        className="scenario-ab-decision-summary",
        style=SCENARIO_AB_DETAIL_SECTION_STYLE,
    )

def _render_scenario_ab_highlight_group(
    title: str,
    items: tuple[ScenarioComparisonHighlightItem, ...],
    *,
    empty_message: str,
    section_id: str,
    scenario_a_label: str,
    scenario_b_label: str,
) -> Any:
    """Render one ranked comparison-highlight group."""

    children: list[Any] = [html.H4(title, style={"margin": "0"})]
    if not items:
        children.append(
            html.P(
                empty_message,
                className="scenario-ab-highlight-empty",
                style={"color": TEXT_SECONDARY_COLOR, "marginBottom": "0"},
            )
        )
    else:
        children.extend(
            _render_scenario_ab_highlight_card(
                item,
                scenario_a_label=scenario_a_label,
                scenario_b_label=scenario_b_label,
            )
            for item in items[:2]
        )

    return html.Div(
        children,
        id=section_id,
        className="scenario-ab-highlight-group",
        style=SCENARIO_AB_DECISION_CARD_STYLE,
    )

def _render_scenario_ab_highlight_card(
    item: ScenarioComparisonHighlightItem,
    *,
    scenario_a_label: str,
    scenario_b_label: str,
) -> Any:
    """Render one compact improvement or trade-off summary row."""

    return html.Div(
        [
            html.Strong(
                item.theme,
                className="scenario-ab-highlight-theme",
            ),
            html.Div(
                _scenario_ab_highlight_primary_line(item),
                className="scenario-ab-highlight-primary",
            ),
            html.Span(
                (
                    f"{_scenario_ab_compact_context_label(scenario_a_label, 'A')} "
                    f"{_scenario_ab_highlight_value(item.scenario_a_value, item.value_format)} -> "
                    f"{_scenario_ab_compact_context_label(scenario_b_label, 'B')} "
                    f"{_scenario_ab_highlight_value(item.scenario_b_value, item.value_format)}"
                ),
                className="scenario-ab-highlight-context",
                style=SUPPORTING_TEXT_STYLE,
            ),
        ],
        className="scenario-ab-highlight-row",
        style=_scenario_ab_highlight_row_style(item.outcome),
    )

def _scenario_ab_highlight_primary_line(
    item: ScenarioComparisonHighlightItem,
) -> str:
    """Return the main one-line summary for one decision-summary highlight."""

    if item.is_categorical:
        return (
            f"{item.label}: "
            f"{_scenario_ab_highlight_value(item.scenario_b_value, item.value_format)}"
        )

    return f"{item.label} {_scenario_ab_highlight_delta_text(item)}"

def _scenario_ab_highlight_delta_text(
    item: ScenarioComparisonHighlightItem,
) -> str:
    """Return compact signed change text for one summary highlight."""

    if item.change_value in (None,):
        return "not available"

    formatted_change = _format_scenario_ab_scalar_value(
        item.change_format,
        item.change_value,
    )
    if item.change_value in (0, 0.0):
        return formatted_change.removeprefix("+").removeprefix("-")
    return formatted_change

def _scenario_ab_highlight_row_style(outcome: str) -> dict[str, str]:
    """Return one compact highlight-row style."""

    style = {
        "display": "flex",
        "flexDirection": "column",
        "gap": "0.15rem",
        "padding": "0.55rem 0",
        "borderTop": f"1px solid {BORDER_COLOR}",
    }
    if outcome == SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT:
        return {
            **style,
            "borderLeft": f"3px solid {STATUS_GREEN}",
            "paddingLeft": "0.65rem",
        }
    if outcome == SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF:
        return {
            **style,
            "borderLeft": f"3px solid {STATUS_RED}",
            "paddingLeft": "0.65rem",
        }
    return {
        **style,
        "borderLeft": f"3px solid {STATUS_AMBER}",
        "paddingLeft": "0.65rem",
    }

def _scenario_ab_highlight_value(value: Any, value_format: str) -> str:
    """Format a highlight-card scenario value."""

    return str(_format_scenario_ab_scalar_value(value_format, value))

def _scenario_ab_section_visual_children(
    section_id: str,
    metrics_a: Metrics,
    metrics_b: Metrics,
    show_occupancy_chart: bool,
    occupancy_hidden_message: str,
    show_queue_chart: bool,
    queue_hidden_message: str,
    show_pq_chart: bool,
    pq_hidden_message: str,
    show_grid_chart: bool,
    grid_hidden_message: str,
    scenario_a_label: str,
    scenario_b_label: str,
) -> list[Any] | None:
    """Return section-specific chart content for one detailed comparison area."""

    if section_id == "infrastructure":
        return [
            _render_scenario_ab_chart_or_message(
                "Occupied Chargers Over Time",
                figure=(
                    create_scenario_ab_occupancy_figure(
                        metrics_a,
                        metrics_b,
                        scenario_a_label=scenario_a_label,
                        scenario_b_label=scenario_b_label,
                        show_figure_title=False,
                    )
                    if show_occupancy_chart
                    else None
                ),
                graph_id="scenario-ab-occupancy-chart",
                hidden_message=occupancy_hidden_message,
            )
        ]

    if section_id == "queueing":
        return [
            _render_scenario_ab_chart_or_message(
                "Queue Length Over Time",
                figure=(
                    create_scenario_ab_queue_figure(
                        metrics_a,
                        metrics_b,
                        scenario_a_label=scenario_a_label,
                        scenario_b_label=scenario_b_label,
                        show_figure_title=False,
                    )
                    if show_queue_chart
                    else None
                ),
                graph_id="scenario-ab-queue-chart",
                hidden_message=queue_hidden_message,
            )
        ]

    if section_id == "power_quality":
        return [
            _render_scenario_ab_chart_or_message(
                "Overall PQ Risk Over Time",
                figure=(
                    create_scenario_ab_power_quality_figure(
                        metrics_a,
                        metrics_b,
                        scenario_a_label=scenario_a_label,
                        scenario_b_label=scenario_b_label,
                        show_figure_title=False,
                    )
                    if show_pq_chart
                    else None
                ),
                graph_id="scenario-ab-pq-risk-chart",
                hidden_message=pq_hidden_message,
            )
        ]

    if section_id == "grid":
        if not show_grid_chart:
            return None

        return [
            _render_scenario_ab_chart_or_message(
                "Transformer Loading Over Time",
                figure=(
                    create_scenario_ab_transformer_loading_figure(
                        metrics_a,
                        metrics_b,
                        scenario_a_label=scenario_a_label,
                        scenario_b_label=scenario_b_label,
                        show_figure_title=False,
                    )
                ),
                graph_id="scenario-ab-transformer-loading-chart",
                hidden_message=grid_hidden_message,
            )
        ]

    return None

def _scenario_ab_section_select_id(section_id: str) -> dict[str, str]:
    """Return the pattern id for one decision-area section selection target."""

    return {
        "type": SCENARIO_AB_SECTION_SELECT_ID_TYPE,
        "section_id": section_id,
    }

def _scenario_ab_detail_card_style(
    section: ScenarioComparisonDisplaySection,
    *,
    selected: bool,
) -> dict[str, Any]:
    """Return one stable detail-card style with optional selected emphasis."""

    base_style = (
        dict(SCENARIO_AB_COMPACT_SECTION_CARD_STYLE)
        if section.impact_level == SCENARIO_SECTION_IMPACT_NONE
        else dict(SCENARIO_AB_DETAIL_CARD_STYLE)
    )
    if selected:
        base_style.update(
            {
                "borderColor": ACCENT_BLUE,
                "boxShadow": "0 0 0 2px rgba(33, 113, 181, 0.16)",
            }
        )

    return base_style

def _render_scenario_ab_section_summary_content(
    section: ScenarioComparisonDisplaySection,
    *,
    scenario_a_label: str,
    scenario_b_label: str,
) -> Any:
    """Render the compact summary content for one decision-area card."""

    return html.Div(
        [
            html.Div(
                [
                    html.H3(section.title, style={"margin": "0"}),
                    html.Span(
                        section.summary_label,
                        id=f"scenario-ab-section-badge-{section.section_id}",
                        style=_scenario_ab_section_summary_badge_style(
                            section.summary_tone
                        ),
                    ),
                ],
                style=SCENARIO_AB_SECTION_HEADER_ROW_STYLE,
            ),
            html.P(
                section.summary_text,
                style={
                    "margin": "0",
                    "fontWeight": "bold",
                    "color": "#24292f",
                },
            ),
        ],
        style=SCENARIO_AB_SECTION_SUMMARY_STACK_STYLE,
    )

def _render_scenario_ab_evidence_metric_cards(
    rows: list[ScenarioComparisonDisplayMetric],
    *,
    scenario_a_label: str,
    scenario_b_label: str,
    grid_style: dict[str, Any],
    card_style: dict[str, Any],
    grid_class_name: str,
    card_class_name: str,
) -> Any:
    """Render compact evidence cards that use available width efficiently."""

    return html.Div(
        [
            _render_scenario_ab_evidence_metric_card(
                row,
                scenario_a_label=scenario_a_label,
                scenario_b_label=scenario_b_label,
                card_style=card_style,
                card_class_name=card_class_name,
            )
            for row in rows
        ],
        className=grid_class_name,
        style=grid_style,
    )

def _render_scenario_ab_evidence_metric_card(
    metric: ScenarioComparisonDisplayMetric,
    *,
    scenario_a_label: str,
    scenario_b_label: str,
    card_style: dict[str, Any],
    card_class_name: str,
) -> Any:
    """Render one evidence metric card with KPI-style hierarchy."""

    lead_text = _scenario_ab_evidence_metric_primary_value(metric)
    card_outcome = _scenario_ab_evidence_metric_outcome(metric)
    before_after = _scenario_ab_evidence_metric_context(
        metric,
        scenario_a_label=scenario_a_label,
        scenario_b_label=scenario_b_label,
    )

    return html.Div(
        [
            html.Span(
                metric.label,
                className="scenario-ab-evidence-card-label",
                style=_scenario_ab_evidence_metric_label_style(),
            ),
            html.Div(
                lead_text,
                className="scenario-ab-evidence-card-value",
                style=_scenario_ab_evidence_metric_value_style(card_outcome),
            ),
            html.Div(
                before_after,
                className="scenario-ab-evidence-card-context",
                style=_scenario_ab_evidence_metric_context_style(),
            ),
        ],
        className=card_class_name,
        style=_scenario_ab_evidence_metric_card_style(card_outcome, card_style),
    )

def _scenario_ab_evidence_metric_primary_value(
    metric: ScenarioComparisonDisplayMetric,
) -> Any:
    """Return the KPI-style primary value for one evidence metric card."""

    raw_change, formatted_change, _relative_change = _render_scenario_ab_metric_change(
        metric
    )
    if metric.change_mode == SCENARIO_CHANGE_NONE:
        if metric.scenario_a_value != metric.scenario_b_value:
            return _render_scenario_ab_metric_value(
                metric,
                metric.scenario_b_value,
                scenario_label="Scenario B",
            )

        return _scenario_ab_evidence_delta_text(0, formatted_change or "No change")

    if raw_change is not None:
        return _scenario_ab_evidence_delta_text(raw_change, formatted_change)

    if raw_change is None:
        if metric.scenario_b_value is not None and metric.scenario_a_value is None:
            return _render_scenario_ab_metric_value(
                metric,
                metric.scenario_b_value,
                scenario_label="Scenario B",
            )

        if metric.scenario_a_value is not None and metric.scenario_b_value is None:
            return _render_scenario_ab_metric_value(
                metric,
                metric.scenario_a_value,
                scenario_label="Scenario A",
            )

        return formatted_change

    return formatted_change

def _scenario_ab_evidence_metric_card_style(
    outcome: str,
    base_style: dict[str, Any],
) -> dict[str, Any]:
    """Return the shared Evidence-panel card style."""

    return {
        **base_style,
        **_scenario_ab_executive_card_style(outcome),
        "minHeight": "8.75rem",
    }

def _scenario_ab_evidence_metric_label_style() -> dict[str, str]:
    """Return the smallest label style used across Evidence cards."""

    return {
        "fontSize": "0.8rem",
        "fontWeight": "600",
        "lineHeight": "1.35",
        "color": TEXT_SECONDARY_COLOR,
    }

def _scenario_ab_evidence_metric_value_style(outcome: str) -> dict[str, str]:
    """Return the promoted primary-value style for one Evidence card."""

    return {
        **_scenario_ab_executive_change_style(outcome),
        "fontSize": "clamp(1.45rem, 1.2rem + 0.55vw, 1.95rem)",
        "lineHeight": "1.15",
    }

def _scenario_ab_evidence_metric_context_style() -> dict[str, str]:
    """Return the supporting before/after style for one Evidence card."""

    return {
        **SUPPORTING_TEXT_STYLE,
        "fontSize": "0.92rem",
        "lineHeight": "1.35",
    }

def _scenario_ab_evidence_delta_text(
    raw_change: float | int,
    formatted_change: Any,
) -> Any:
    """Return a signed delta with a directional indicator for one metric."""

    if raw_change > 0:
        direction = "↑"
    elif raw_change < 0:
        direction = "↓"
    else:
        return _scenario_ab_unsigned_display_text(formatted_change)

    return f"{direction} {_scenario_ab_unsigned_display_text(formatted_change)}"

def _scenario_ab_unsigned_display_text(value: Any) -> Any:
    """Return one display value without a leading numeric sign."""

    if isinstance(value, str):
        return value.removeprefix("+").removeprefix("-")

    return value

def _scenario_ab_evidence_metric_outcome(
    metric: ScenarioComparisonDisplayMetric,
) -> str:
    """Return the executive-style outcome tone for one Evidence metric."""

    if metric.change_mode == SCENARIO_CHANGE_NONE:
        return _scenario_ab_evidence_status_outcome(metric)

    raw_change, _formatted_change, _relative_change = _render_scenario_ab_metric_change(
        metric
    )
    if raw_change in (None,):
        return SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL
    if metric.preferred_direction is None:
        return SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL

    return classify_directional_outcome(raw_change, metric.preferred_direction)

def _scenario_ab_evidence_status_outcome(
    metric: ScenarioComparisonDisplayMetric,
) -> str:
    """Return the executive-style outcome tone for one categorical metric."""

    if metric.scenario_a_value == metric.scenario_b_value:
        return SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL
    if not metric.always_meaningful_status_change:
        return SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL
    if metric.preferred_direction is None:
        return SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL

    severity_a = _scenario_ab_evidence_status_severity(
        metric.value_format,
        metric.scenario_a_value,
    )
    severity_b = _scenario_ab_evidence_status_severity(
        metric.value_format,
        metric.scenario_b_value,
    )
    if severity_a is None or severity_b is None:
        return SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL

    return classify_directional_outcome(
        severity_b - severity_a,
        metric.preferred_direction,
    )

def _scenario_ab_evidence_status_severity(
    value_format: str,
    value: Any,
) -> float | None:
    """Return an ordinal severity for supported Evidence status cards."""

    if value_format in {"queue_present", "overload_indicator"}:
        return 1.0 if bool(value) else 0.0
    if value_format in {"thermal_risk_level", "power_quality_risk_level"}:
        return {
            "low": 0.0,
            "moderate": 1.0,
            "high": 2.0,
        }.get(str(value).lower())

    return None

def _scenario_ab_evidence_metric_context(
    metric: ScenarioComparisonDisplayMetric,
    *,
    scenario_a_label: str,
    scenario_b_label: str,
) -> Any:
    """Return a compact before/after context line for one evidence metric."""

    return [
        f"{_scenario_ab_compact_context_label(scenario_a_label, 'A')} ",
        _render_scenario_ab_metric_value(
            metric,
            metric.scenario_a_value,
            scenario_label=scenario_a_label,
        ),
        " -> ",
        f"{_scenario_ab_compact_context_label(scenario_b_label, 'B')} ",
        _render_scenario_ab_metric_value(
            metric,
            metric.scenario_b_value,
            scenario_label=scenario_b_label,
        ),
    ]

def _scenario_ab_select_evidence_metrics(
    section: ScenarioComparisonDisplaySection,
) -> tuple[list[ScenarioComparisonDisplayMetric], list[ScenarioComparisonDisplayMetric]]:
    """Return top-driver and supporting metrics for one evidence panel."""

    primary_metrics = _scenario_ab_sort_evidence_metrics(
        section.section_id,
        list(section.metric_buckets.primary_metrics),
    )
    secondary_metrics = _scenario_ab_sort_evidence_metrics(
        section.section_id,
        list(section.metric_buckets.secondary_metrics),
    )
    unchanged_metrics = _scenario_ab_sort_evidence_metrics(
        section.section_id,
        list(section.metric_buckets.unchanged_metrics),
    )

    top_driver_metrics = list(primary_metrics[:2])
    selected_metric_ids = {metric.metric_id for metric in top_driver_metrics}

    if section.impact_level == SCENARIO_SECTION_IMPACT_NONE:
        supporting_metrics: list[ScenarioComparisonDisplayMetric] = []
        for metric in unchanged_metrics:
            if metric.metric_id in selected_metric_ids:
                continue
            priority_index = _scenario_ab_evidence_priority_index(
                section.section_id,
                metric,
            )
            if (
                priority_index >= 3
                and _scenario_ab_metric_is_empty_verification(metric)
            ):
                continue
            supporting_metrics.append(metric)
            if len(supporting_metrics) >= 4:
                break
        return top_driver_metrics, supporting_metrics

    supporting_candidates = _scenario_ab_sort_evidence_metrics(
        section.section_id,
        [
            *primary_metrics[2:],
            *secondary_metrics,
        ],
    )
    supporting_metrics = []
    for metric in supporting_candidates:
        if metric.metric_id in selected_metric_ids:
            continue
        if not _scenario_ab_metric_has_visible_difference(metric):
            continue
        supporting_metrics.append(metric)
        if len(supporting_metrics) >= SCENARIO_AB_EVIDENCE_MAX_SUPPORTING_METRICS:
            break

    return top_driver_metrics, supporting_metrics

def _scenario_ab_sort_evidence_metrics(
    section_id: str,
    metrics: list[ScenarioComparisonDisplayMetric],
) -> list[ScenarioComparisonDisplayMetric]:
    """Return evidence metrics ordered for quick decision scanning."""

    return sorted(
        metrics,
        key=lambda metric: (
            _scenario_ab_evidence_priority_index(section_id, metric),
            metric.display_priority,
            metric.label,
        ),
    )

def _scenario_ab_evidence_priority_index(
    section_id: str,
    metric: ScenarioComparisonDisplayMetric,
) -> int:
    """Return one stable evidence priority index for a section metric."""

    ordered_metric_ids = SCENARIO_AB_EVIDENCE_PRIORITY.get(section_id, ())
    try:
        return ordered_metric_ids.index(metric.metric_id)
    except ValueError:
        return len(ordered_metric_ids) + metric.display_priority

def _scenario_ab_metric_has_visible_difference(
    metric: ScenarioComparisonDisplayMetric,
) -> bool:
    """Return whether a metric provides visible comparison value in evidence."""

    if metric.change_mode == SCENARIO_CHANGE_NONE:
        return metric.scenario_a_value != metric.scenario_b_value

    if metric.change_value not in (None, 0, 0.0):
        return True

    if metric.change_mode == SCENARIO_CHANGE_OPTIONAL_DELTA and metric.change_value is None:
        return (
            metric.scenario_a_value is not None
            and metric.scenario_b_value is not None
            and metric.scenario_a_value != metric.scenario_b_value
        )

    return metric.scenario_a_value != metric.scenario_b_value

def _scenario_ab_metric_is_empty_verification(
    metric: ScenarioComparisonDisplayMetric,
) -> bool:
    """Return whether an unchanged metric adds little neutral-state evidence."""

    if metric.scenario_a_value != metric.scenario_b_value:
        return False

    value = metric.scenario_a_value
    if value in (None, 0, 0.0, False):
        return True

    if isinstance(value, str) and value.lower() in {"none", "low"}:
        return True

    return False

def _render_scenario_ab_section_evidence_content(
    section: ScenarioComparisonDisplaySection,
    *,
    metrics_a: Metrics,
    metrics_b: Metrics,
    show_occupancy_chart: bool,
    occupancy_hidden_message: str,
    show_queue_chart: bool,
    queue_hidden_message: str,
    show_pq_chart: bool,
    pq_hidden_message: str,
    show_grid_chart: bool,
    grid_hidden_message: str,
    scenario_a_label: str,
    scenario_b_label: str,
) -> list[Any]:
    """Render the supporting evidence content for one decision-area card."""
    primary_metrics, supporting_metrics = _scenario_ab_select_evidence_metrics(section)

    evidence_children: list[Any] = []

    if primary_metrics:
        evidence_children.append(
            html.Section(
                [
                    html.H4(
                        "Top Drivers",
                        style=SCENARIO_AB_EVIDENCE_BLOCK_TITLE_STYLE,
                    ),
                    _render_scenario_ab_evidence_metric_cards(
                        primary_metrics,
                        scenario_a_label=scenario_a_label,
                        scenario_b_label=scenario_b_label,
                        grid_style=SCENARIO_AB_EVIDENCE_DRIVER_GRID_STYLE,
                        card_style=SCENARIO_AB_EVIDENCE_DRIVER_CARD_STYLE,
                        grid_class_name=(
                            "scenario-ab-evidence-grid "
                            "scenario-ab-evidence-grid--drivers"
                        ),
                        card_class_name=(
                            "scenario-ab-evidence-card "
                            "scenario-ab-evidence-card--driver"
                        ),
                    ),
                ],
                className="scenario-ab-evidence-block scenario-ab-evidence-block--drivers",
                style=SCENARIO_AB_EVIDENCE_BLOCK_STYLE,
            )
        )

    visual_children = (
        _scenario_ab_section_visual_children(
            section.section_id,
            metrics_a,
            metrics_b,
            show_occupancy_chart,
            occupancy_hidden_message,
            show_queue_chart,
            queue_hidden_message,
            show_pq_chart,
            pq_hidden_message,
            show_grid_chart,
            grid_hidden_message,
            scenario_a_label,
            scenario_b_label,
        )
        if section.visualization_intent
        == SCENARIO_SECTION_VISUALIZATION_SUPPORTING_WHEN_USEFUL
        else None
    )
    if visual_children:
        evidence_children.append(
            html.Section(
                visual_children,
                className="scenario-ab-evidence-block scenario-ab-evidence-block--chart",
                style=SCENARIO_AB_EVIDENCE_BLOCK_STYLE,
            )
        )

    if supporting_metrics:
        evidence_children.append(
            html.Section(
                [
                    html.H4(
                        "Supporting Facts",
                        style=SCENARIO_AB_EVIDENCE_BLOCK_TITLE_STYLE,
                    ),
                    _render_scenario_ab_evidence_metric_cards(
                        supporting_metrics,
                        scenario_a_label=scenario_a_label,
                        scenario_b_label=scenario_b_label,
                        grid_style=SCENARIO_AB_EVIDENCE_FACT_GRID_STYLE,
                        card_style=SCENARIO_AB_EVIDENCE_FACT_CARD_STYLE,
                        grid_class_name=(
                            "scenario-ab-evidence-grid "
                            "scenario-ab-evidence-grid--facts"
                        ),
                        card_class_name=(
                            "scenario-ab-evidence-card "
                            "scenario-ab-evidence-card--fact"
                        ),
                    ),
                ],
                className="scenario-ab-evidence-block scenario-ab-evidence-block--facts",
                style=SCENARIO_AB_EVIDENCE_BLOCK_STYLE,
            )
        )

    if not evidence_children:
        evidence_children.append(
            html.P(
                "No additional evidence.",
                style={"color": TEXT_SECONDARY_COLOR, "marginBottom": "0"},
            )
        )

    return evidence_children

def _render_scenario_ab_evidence_panel(
    selected_section: ScenarioComparisonDisplaySection | None,
    *,
    metrics_a: Metrics,
    metrics_b: Metrics,
    show_occupancy_chart: bool,
    occupancy_hidden_message: str,
    show_queue_chart: bool,
    queue_hidden_message: str,
    show_pq_chart: bool,
    pq_hidden_message: str,
    show_grid_chart: bool,
    grid_hidden_message: str,
    scenario_a_label: str,
    scenario_b_label: str,
) -> Any:
    """Render the dedicated evidence panel for the currently selected section."""

    if selected_section is None:
        return html.Aside(
            [
                html.Div("Evidence", style=COMPARISON_EYEBROW_STYLE),
                html.Div(
                    html.P(
                        "Select a decision area to view detailed evidence.",
                        style={"margin": "0", "color": TEXT_PRIMARY_COLOR},
                    ),
                    id="scenario-ab-evidence-panel-empty-state",
                    className="scenario-ab-evidence-panel-empty-state",
                    style=SCENARIO_AB_EVIDENCE_EMPTY_STATE_STYLE,
                ),
            ],
            id="scenario-ab-evidence-panel",
            className="scenario-ab-evidence-panel scenario-ab-evidence-panel--empty",
            style=SCENARIO_AB_EVIDENCE_PANEL_STYLE,
        )

    evidence_children = _render_scenario_ab_section_evidence_content(
        selected_section,
        metrics_a=metrics_a,
        metrics_b=metrics_b,
        show_occupancy_chart=show_occupancy_chart,
        occupancy_hidden_message=occupancy_hidden_message,
        show_queue_chart=show_queue_chart,
        queue_hidden_message=queue_hidden_message,
        show_pq_chart=show_pq_chart,
        pq_hidden_message=pq_hidden_message,
        show_grid_chart=show_grid_chart,
        grid_hidden_message=grid_hidden_message,
        scenario_a_label=scenario_a_label,
        scenario_b_label=scenario_b_label,
    )

    return html.Aside(
        [
            html.Div("Evidence", style=COMPARISON_EYEBROW_STYLE),
            html.Div(
                [
                    html.H3(
                        selected_section.title,
                        style=SCENARIO_AB_EVIDENCE_PANEL_TITLE_STYLE,
                    ),
                    html.Span(
                        selected_section.summary_label,
                        style=_scenario_ab_section_summary_badge_style(
                            selected_section.summary_tone
                        ),
                    ),
                ],
                style=SCENARIO_AB_SECTION_HEADER_ROW_STYLE,
            ),
            html.Div(
                evidence_children,
                id=f"scenario-ab-section-content-{selected_section.section_id}",
                className="scenario-ab-evidence-panel-content",
                style=SCENARIO_AB_EVIDENCE_BODY_STYLE,
            ),
        ],
        id="scenario-ab-evidence-panel",
        className="scenario-ab-evidence-panel",
        style=SCENARIO_AB_EVIDENCE_PANEL_STYLE,
    )

def _scenario_ab_reason_explanation(reason_key: str | None) -> str:
    """Return the user-facing helper text for one prepared missing-value reason."""

    explanations = {
        "charger_utilization_unavailable": CHARGER_UTILIZATION_UNAVAILABLE_HELPER,
        "waiting_time_unavailable": WAITING_TIME_UNAVAILABLE_HELPER,
        "required_charger_count_not_applicable": (
            REQUIRED_CHARGER_COUNT_NOT_APPLICABLE_HELPER
        ),
        "additional_chargers_not_applicable": (
            ADDITIONAL_CHARGERS_NOT_APPLICABLE_HELPER
        ),
        "difference_unavailable": DIFFERENCE_UNAVAILABLE_HELPER,
    }
    return explanations.get(reason_key, DIFFERENCE_UNAVAILABLE_HELPER)

def _format_scenario_ab_scalar_value(format_id: str, value: Any) -> str:
    """Format one prepared comparison value using presentation-only rules."""

    if format_id == "power_kw":
        return format_power_kw(value)
    if format_id == "power_kw_signed":
        return format_signed_power_kw(value)
    if format_id == "percent":
        return format_percent(value)
    if format_id == "percentage_points_signed":
        return format_signed_percentage_points(value)
    if format_id == "energy_kwh":
        return format_energy_kwh(value)
    if format_id == "energy_kwh_signed":
        return format_signed_energy_kwh(value)
    if format_id == "risk_score":
        return format_risk_score(value)
    if format_id == "score_points_signed":
        return format_signed_score_points(value)
    if format_id == "warning_count":
        return format_warning_count(value)
    if format_id == "warning_count_signed":
        return format_signed_warning_count(value)
    if format_id == "charger_count_0":
        return format_charger_count(value)
    if format_id == "charger_count_0_signed":
        return format_signed_charger_count(value)
    if format_id == "charger_count_1":
        return format_charger_count(value, decimals=1)
    if format_id == "charger_count_1_signed":
        return format_signed_charger_count(value, decimals=1)
    if format_id == "vehicle_count_0":
        return format_vehicle_count(value)
    if format_id == "vehicle_count_0_signed":
        return format_signed_vehicle_count(value)
    if format_id == "vehicle_count_1":
        return format_vehicle_count(value, decimals=1)
    if format_id == "vehicle_count_1_signed":
        return format_signed_vehicle_count(value, decimals=1)
    if format_id == "hours":
        return format_hours(value)
    if format_id == "hours_signed":
        return format_signed_hours(value)
    if format_id == "feeder_count":
        return format_feeder_count(value)
    if format_id == "feeder_count_signed":
        return format_signed_feeder_count(value)
    if format_id == "queue_present":
        return _format_queue_present_value(value)
    if format_id == "overload_indicator":
        return _format_overload_indicator_value(value)
    if format_id == "thermal_risk_level":
        return format_thermal_risk_level(value)
    if format_id == "power_quality_risk_level":
        return format_power_quality_risk_level(value)
    if format_id == "primary_constraint_reason":
        return format_primary_constraint_reason(value)

    raise ValueError(f"Unsupported Scenario A/B display format: {format_id}")

def _render_scenario_ab_metric_value(
    metric: ScenarioComparisonDisplayMetric,
    value: Any,
    *,
    scenario_label: str,
) -> Any:
    """Render one prepared scenario value with the appropriate missing state."""

    if value is None and metric.scenario_value_state == SCENARIO_VALUE_OPTIONAL_UNAVAILABLE:
        return _undefined_metric_value(
            f"{scenario_label} {metric.label}",
            _scenario_ab_reason_explanation(metric.scenario_value_reason),
            text=UNAVAILABLE_METRIC_TEXT,
        )

    if value is None and metric.scenario_value_state == SCENARIO_VALUE_OPTIONAL_NOT_APPLICABLE:
        return _undefined_metric_value(
            f"{scenario_label} {metric.label}",
            _scenario_ab_reason_explanation(metric.scenario_value_reason),
            text=NOT_APPLICABLE_METRIC_TEXT,
        )

    return _format_scenario_ab_scalar_value(metric.value_format, value)

def _render_scenario_ab_metric_change(
    metric: ScenarioComparisonDisplayMetric,
) -> tuple[float | int | None, Any, str | None]:
    """Return the rendered change payload for one prepared comparison metric."""

    if metric.change_mode == SCENARIO_CHANGE_NOT_APPLICABLE:
        return (
            None,
            _undefined_metric_value(
                f"{metric.label} change",
                NON_NUMERIC_DIFFERENCE_NOT_APPLICABLE_HELPER,
                text=NOT_APPLICABLE_METRIC_TEXT,
            ),
            None,
        )

    if metric.change_mode == SCENARIO_CHANGE_OPTIONAL_DELTA and metric.change_value is None:
        return (
            None,
            _undefined_metric_value(
                f"{metric.label} change",
                _scenario_ab_reason_explanation(metric.change_reason),
                text=UNAVAILABLE_METRIC_TEXT,
            ),
            None,
        )

    if metric.change_mode == SCENARIO_CHANGE_NONE:
        return None, "", None

    return (
        metric.change_value,
        _format_scenario_ab_scalar_value(
            metric.change_format or metric.value_format,
            metric.change_value,
        ),
        format_change_percent(metric.relative_change_percent),
    )

def _render_scenario_ab_detail_section(
    section: ScenarioComparisonDisplaySection,
    *,
    selected: bool,
    scenario_a_label: str = "Scenario A",
    scenario_b_label: str = "Scenario B",
) -> Any:
    """Render one stable decision-area summary card."""

    if section.impact_level == SCENARIO_SECTION_IMPACT_NONE:
        return _render_scenario_ab_compact_no_difference_section(
            section,
            selected=selected,
            scenario_a_label=scenario_a_label,
            scenario_b_label=scenario_b_label,
        )

    return html.Div(
        html.Div(
            [
                _render_scenario_ab_section_summary_content(
                    section,
                    scenario_a_label=scenario_a_label,
                    scenario_b_label=scenario_b_label,
                ),
            ],
            id=_scenario_ab_section_select_id(section.section_id),
            n_clicks=0,
            role="button",
            tabIndex=0,
            style=SCENARIO_AB_SECTION_SELECT_SURFACE_STYLE,
        ),
        id=f"scenario-ab-detail-section-{section.section_id}",
        className=(
            "scenario-ab-detail-card scenario-ab-detail-card--selected"
            if selected
            else "scenario-ab-detail-card"
        ),
        style=_scenario_ab_detail_card_style(section, selected=selected),
    )

def _render_scenario_ab_compact_no_difference_section(
    section: ScenarioComparisonDisplaySection,
    *,
    selected: bool,
    scenario_a_label: str = "Scenario A",
    scenario_b_label: str = "Scenario B",
) -> Any:
    """Render a compact summary card when a decision area has no material differences."""

    return html.Div(
        html.Div(
            [
                html.Div(
                    [
                        html.H3(section.title, style={"margin": "0"}),
                        html.Span(
                            section.summary_label,
                            id=f"scenario-ab-section-badge-{section.section_id}",
                            style=_scenario_ab_section_summary_badge_style(
                                section.summary_tone
                            ),
                        ),
                    ],
                    style=SCENARIO_AB_SECTION_HEADER_ROW_STYLE,
                ),
                html.P(
                    section.summary_text,
                    style={"margin": "0", "fontWeight": "bold", "color": "#24292f"},
                ),
            ],
            id=_scenario_ab_section_select_id(section.section_id),
            n_clicks=0,
            role="button",
            tabIndex=0,
            style=SCENARIO_AB_SECTION_SELECT_SURFACE_STYLE,
        ),
        id=f"scenario-ab-detail-section-{section.section_id}",
        className=(
            "scenario-ab-detail-card scenario-ab-detail-card--compact "
            "scenario-ab-detail-card--selected"
            if selected
            else "scenario-ab-detail-card scenario-ab-detail-card--compact"
        ),
        style=_scenario_ab_detail_card_style(section, selected=selected),
    )

def _render_scenario_ab_numeric_table(
    rows: list[ScenarioComparisonDisplayMetric],
    *,
    scenario_a_label: str = "Scenario A",
    scenario_b_label: str = "Scenario B",
) -> Any:
    """Render a numeric detailed-comparison table with change badges."""

    return html.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Metric", style=SCENARIO_AB_DETAIL_HEADER_CELL_STYLE),
                        html.Th(scenario_a_label, style=SCENARIO_AB_DETAIL_HEADER_CELL_STYLE),
                        html.Th(scenario_b_label, style=SCENARIO_AB_DETAIL_HEADER_CELL_STYLE),
                        html.Th("Change", style=SCENARIO_AB_DETAIL_HEADER_CELL_STYLE),
                    ]
                )
            ),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td(
                                row.label,
                                style=SCENARIO_AB_DETAIL_CELL_STYLE,
                            ),
                            html.Td(
                                _render_scenario_ab_value_chip(
                                    _render_scenario_ab_metric_value(
                                        row,
                                        row.scenario_a_value,
                                        scenario_label=scenario_a_label,
                                    )
                                ),
                                style=SCENARIO_AB_DETAIL_CELL_STYLE,
                            ),
                            html.Td(
                                _render_scenario_ab_value_chip(
                                    _render_scenario_ab_metric_value(
                                        row,
                                        row.scenario_b_value,
                                        scenario_label=scenario_b_label,
                                    )
                                ),
                                style=SCENARIO_AB_DETAIL_CELL_STYLE,
                            ),
                            html.Td(
                                _render_scenario_ab_change_indicator(*_render_scenario_ab_metric_change(row)),
                                style=SCENARIO_AB_DETAIL_CELL_STYLE,
                            ),
                        ]
                    )
                    for row in rows
                ]
            ),
        ],
        style=SCENARIO_AB_DETAIL_TABLE_STYLE,
    )

def _render_scenario_ab_status_table(
    rows: list[ScenarioComparisonDisplayMetric],
    *,
    scenario_a_label: str = "Scenario A",
    scenario_b_label: str = "Scenario B",
) -> Any:
    """Render a categorical detailed-comparison table without a change column."""

    return html.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Metric", style=SCENARIO_AB_DETAIL_HEADER_CELL_STYLE),
                        html.Th(scenario_a_label, style=SCENARIO_AB_DETAIL_HEADER_CELL_STYLE),
                        html.Th(scenario_b_label, style=SCENARIO_AB_DETAIL_HEADER_CELL_STYLE),
                    ]
                )
            ),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td(
                                row.label,
                                style=SCENARIO_AB_DETAIL_CELL_STYLE,
                            ),
                            html.Td(
                                _render_scenario_ab_status_chip(
                                    _format_scenario_ab_scalar_value(
                                        row.value_format,
                                        row.scenario_a_value,
                                    )
                                ),
                                style=SCENARIO_AB_DETAIL_CELL_STYLE,
                            ),
                            html.Td(
                                _render_scenario_ab_status_chip(
                                    _format_scenario_ab_scalar_value(
                                        row.value_format,
                                        row.scenario_b_value,
                                    )
                                ),
                                style=SCENARIO_AB_DETAIL_CELL_STYLE,
                            ),
                        ]
                    )
                    for row in rows
                ]
            ),
        ],
        style=SCENARIO_AB_DETAIL_TABLE_STYLE,
    )

def _render_scenario_ab_value_chip(value: Any) -> Any:
    """Render one scenario-specific comparison value as a compact chip."""

    return html.Span(value, style=SCENARIO_AB_VALUE_CHIP_BASE_STYLE)

def _render_scenario_ab_status_chip(value: Any) -> Any:
    """Render one categorical scenario value as a tone-coded chip."""

    return html.Span(
        value,
        style={
            **SCENARIO_AB_VALUE_CHIP_BASE_STYLE,
            **_scenario_ab_status_chip_colors(value),
        },
    )

def _render_scenario_ab_change_indicator(
    raw_change: float | int | None,
    formatted_change: Any,
    relative_change: str | None,
) -> Any:
    """Render a badge-style Scenario B vs Scenario A change indicator."""

    if raw_change is None:
        return html.Div(
            [_scenario_ab_change_badge("Unavailable", formatted_change, "neutral")],
            style={"display": "flex", "flexDirection": "column", "gap": "0.25rem"},
        )

    if raw_change > 0:
        direction_label = "Higher"
        tone = "positive"
    elif raw_change < 0:
        direction_label = "Lower"
        tone = "negative"
    else:
        direction_label = "No change"
        tone = "neutral"

    children = [_scenario_ab_change_badge(direction_label, formatted_change, tone)]
    if relative_change not in (None, "N/A", NOT_APPLICABLE_METRIC_TEXT):
        children.append(
            html.Span(
                f"Relative change: {relative_change}",
                style=SUPPORTING_TEXT_STYLE,
            )
        )

    return html.Div(
        children,
        style={"display": "flex", "flexDirection": "column", "gap": "0.25rem"},
    )

def _scenario_ab_change_badge(
    label: str,
    value: Any,
    tone: str,
) -> Any:
    """Return one change badge for the detailed comparison tables."""

    tone_colors = {
        "positive": {"backgroundColor": STATUS_BLUE_BACKGROUND, "color": ACCENT_BLUE},
        "negative": {"backgroundColor": STATUS_BLUE_BACKGROUND, "color": TEXT_PRIMARY_COLOR},
        "neutral": {"backgroundColor": SUBTLE_SURFACE_BACKGROUND_COLOR, "color": TEXT_SECONDARY_COLOR},
    }
    resolved_colors = tone_colors[tone]

    return html.Span(
        [html.Strong(f"{label}: "), value],
        style={
            **SCENARIO_AB_CHANGE_BADGE_BASE_STYLE,
            **resolved_colors,
        },
    )

def _scenario_ab_semantic_badge_style(tone: str) -> dict[str, str]:
    """Return shared badge styling for comparison semantics across the page."""

    tone_colors = {
        "improvement": {
            "backgroundColor": STATUS_GREEN_BACKGROUND,
            "border": f"1px solid {STATUS_GREEN}",
            "color": STATUS_GREEN,
        },
        "trade_off": {
            "backgroundColor": STATUS_AMBER_BACKGROUND,
            "border": f"1px solid {STATUS_AMBER}",
            "color": STATUS_AMBER,
        },
        "major_change": {
            "backgroundColor": STATUS_BLUE_BACKGROUND,
            "border": f"1px solid {ACCENT_BLUE}",
            "color": ACCENT_BLUE,
        },
        "minimal_change": {
            "backgroundColor": SUBTLE_SURFACE_BACKGROUND_COLOR,
            "border": f"1px solid {BORDER_COLOR}",
            "color": TEXT_SECONDARY_COLOR,
        },
    }
    resolved_colors = tone_colors[tone]

    return {
        **resolved_colors,
        "borderRadius": "999px",
        "fontSize": "0.8rem",
        "fontWeight": "600",
        "padding": "0.25rem 0.65rem",
        "width": "fit-content",
    }

def _scenario_ab_section_summary_badge_style(summary_tone: str) -> dict[str, str]:
    """Return badge styling for one detailed-comparison section summary."""

    if summary_tone == SCENARIO_SECTION_SUMMARY_MAJOR_CHANGES:
        return _scenario_ab_semantic_badge_style("improvement")
    if summary_tone == SCENARIO_SECTION_SUMMARY_TRADE_OFFS:
        return _scenario_ab_semantic_badge_style("trade_off")
    return _scenario_ab_semantic_badge_style("minimal_change")

def _scenario_ab_status_chip_colors(value: Any) -> dict[str, str]:
    """Return tone colors for categorical side-by-side comparison chips."""

    if not isinstance(value, str):
        return {"backgroundColor": SUBTLE_SURFACE_BACKGROUND_COLOR, "color": TEXT_SECONDARY_COLOR}

    normalized_value = value.lower()
    if any(
        token in normalized_value
        for token in (
            "not overloaded",
            "not present",
            "no warning",
        )
    ):
        return {"backgroundColor": STATUS_GREEN_BACKGROUND, "color": STATUS_GREEN}
    if any(
        token in normalized_value
        for token in (
            "high",
            "overloaded",
            "present",
            "warning",
            "insufficient",
            "exceeded",
        )
    ):
        return {"backgroundColor": STATUS_RED_BACKGROUND, "color": STATUS_RED}
    if any(
        token in normalized_value
        for token in (
            "moderate",
            "mixed",
        )
    ):
        return {"backgroundColor": STATUS_AMBER_BACKGROUND, "color": STATUS_AMBER}
    if any(
        token in normalized_value
        for token in (
            "low",
            "sufficient",
            "none",
        )
    ):
        return {"backgroundColor": STATUS_GREEN_BACKGROUND, "color": STATUS_GREEN}

    return {"backgroundColor": SUBTLE_SURFACE_BACKGROUND_COLOR, "color": TEXT_SECONDARY_COLOR}

def render_scenario_preset_details(preset_id: str) -> Any:
    """Return read-only dashboard content for the selected scenario preset."""

    preset = get_scenario_preset(preset_id)
    return build_scenario_preset_overview(preset)

def render_comparison_scenario_preset_details(preset_id: str) -> Any:
    """Return compact disclosure-first content for comparison templates."""

    preset = get_scenario_preset(preset_id)
    return build_compact_scenario_preset_details(preset)

def _render_changed_assumptions_summary(
    comparison_state: dict[str, dict[str, Any]] | None,
) -> list[Any]:
    """Return planner-facing changed-assumptions content for Scenario A vs B."""
    if comparison_state is None:
        return create_default_changed_assumptions_children()

    change_overview = summarize_scenario_assumption_change_overview(comparison_state)
    summaries = change_overview["all_summaries"]
    if summaries == ("Comparison scenario matches the current scenario.",):
        return [
            html.Div(
                [
                    html.Strong("No comparison changes yet."),
                    html.Span(
                        "Adjust Scenario B to test an alternative.",
                        style={
                            "color": TEXT_SECONDARY_COLOR,
                        },
                    ),
                ],
                className="scenario-comparison-assumptions-inline",
            )
        ]

    area_count = len(change_overview["category_counts"])
    summary_line = (
        f"{change_overview['change_count']} assumption changes"
        if change_overview["change_count"] != 1
        else "1 assumption change"
    )
    summary_line = (
        f"{summary_line} · {area_count} areas"
        if area_count != 1
        else f"{summary_line} · 1 area"
    )
    visible_highlights = change_overview["highlights"][:1]
    return [
        html.Div(
            [
                html.Div(
                    [
                        html.Strong(summary_line),
                        *[
                            html.Span(
                                visible_highlights[0],
                                style={
                                    "color": TEXT_SECONDARY_COLOR,
                                },
                            )
                        ],
                    ],
                    className="scenario-comparison-assumptions-inline",
                ),
                html.Details(
                    [
                        html.Summary(
                            "View changes",
                            style={
                                "cursor": "pointer",
                                "color": ACCENT_BLUE,
                                "fontWeight": "600",
                            },
                        ),
                        html.Ul(
                            [html.Li(summary) for summary in summaries],
                            style={"marginBottom": "0", "marginTop": "0.75rem"},
                        ),
                    ],
                    style={"marginTop": "0.35rem"},
                ),
            ],
        ),
    ]

def _comparison_empty_state_children(
    comparison_state: dict[str, dict[str, Any]] | None,
) -> list[Any]:
    """Return the empty-state guidance for the comparison results area."""
    if comparison_state is None:
        return create_default_scenario_comparison_empty_state_children()

    return []

def _render_scenario_comparison_collapsed_bar(
    active_scenario_state: dict[str, Any] | None,
    comparison_state: dict[str, dict[str, Any]] | None,
    run_status_state: dict[str, Any] | None,
    builder_ui_state: dict[str, Any] | None,
) -> tuple[str, str, str, dict[str, str]]:
    """Return collapsed-bar text and status styling for one comparison state."""

    scenario_a_label, scenario_b_label = _resolve_scenario_ab_display_labels(
        active_scenario_state,
        comparison_state,
    )
    change_overview = (
        summarize_scenario_assumption_change_overview(comparison_state)
        if comparison_state is not None
        else {
            "change_count": 0,
            "category_counts": (),
        }
    )
    if change_overview["change_count"] == 0:
        change_summary = "No assumption changes selected."
    elif change_overview["change_count"] == 1:
        change_summary = "1 assumption change selected."
    else:
        change_summary = (
            f"{change_overview['change_count']} assumption changes selected."
        )

    category_summary = ", ".join(
        f"{count} {category.lower()}"
        for category, count in change_overview["category_counts"][:2]
    )
    if category_summary:
        change_summary = f"{change_summary} {category_summary}."

    status_label, status_style = _scenario_comparison_collapsed_status_summary(
        run_status_state,
        builder_ui_state,
    )
    return (
        f"Scenario A: {scenario_a_label} -> Scenario B: {scenario_b_label}",
        change_summary,
        status_label,
        status_style,
    )

def _build_scenario_ab_results_render_state(
    active_scenario_state: dict[str, Any] | None,
    comparison_state: dict[str, dict[str, Any]] | None,
    metrics_state: dict[str, dict[str, Any]] | None,
    difference_metrics_state: dict[str, Any] | None,
    builder_ui_state: dict[str, Any] | None,
    selected_section_id: str | None = None,
) -> tuple[Any, ...]:
    """Return the render payload for Scenario Comparison result widgets."""

    scenario_a_label, scenario_b_label = _resolve_scenario_ab_display_labels(
        active_scenario_state,
        comparison_state,
    )
    builder_is_collapsed = _scenario_comparison_builder_is_collapsed(builder_ui_state)
    run_section_style = (
        dict(COMPARISON_BUILDER_RUN_SECTION_HIDDEN_STYLE)
        if builder_is_collapsed
        else dict(COMPARISON_BUILDER_RUN_SECTION_VISIBLE_STYLE)
    )
    if metrics_state is None or difference_metrics_state is None:
        return (
            run_section_style,
            _comparison_empty_state_children(comparison_state),
            build_dashboard_widget_style(
                SCENARIO_COMPARISON_EXECUTIVE_SUMMARY_WIDGET_SPEC,
                base_style=DASHBOARD_WIDGET_SECTION_STYLE,
                hidden=True,
            ),
            create_default_scenario_ab_executive_summary_cards(
                scenario_a_label,
                scenario_b_label,
            ),
            build_dashboard_widget_style(
                SCENARIO_AB_COMPARISON_TABLE_WIDGET_SPEC,
                base_style=DASHBOARD_WIDGET_SECTION_STYLE,
                hidden=True,
            ),
            "",
        )

    metrics_a = metrics_from_dict(metrics_state["scenario_a"])
    metrics_b = metrics_from_dict(metrics_state["scenario_b"])
    comparison_metrics = scenario_comparison_metrics_from_dict(
        difference_metrics_state
    )
    display_data = prepare_scenario_comparison_display_data(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )
    return (
        run_section_style,
        [],
        build_dashboard_widget_style(
            SCENARIO_COMPARISON_EXECUTIVE_SUMMARY_WIDGET_SPEC,
            base_style=DASHBOARD_WIDGET_SECTION_STYLE,
        ),
        _render_scenario_ab_executive_summary_cards_from_display_data(
            display_data,
            scenario_a_label=scenario_a_label,
            scenario_b_label=scenario_b_label,
        ),
        build_dashboard_widget_style(
            SCENARIO_AB_COMPARISON_TABLE_WIDGET_SPEC,
            base_style=DASHBOARD_WIDGET_SECTION_STYLE,
        ),
        _render_scenario_ab_detailed_sections_from_display_data(
            display_data,
            metrics_a,
            metrics_b,
            comparison_metrics,
            selected_section_id=selected_section_id,
            scenario_a_label=scenario_a_label,
            scenario_b_label=scenario_b_label,
        ),
    )

__all__ = [

    '_comparison_kpi_card',

    '_scenario_ab_kpi_card',

    '_scenario_ab_compact_change_text',

    '_scenario_ab_executive_change_style',

    '_scenario_ab_executive_card_style',

    '_scenario_ab_compact_context_label',

    '_format_scenario_ab_absolute_change_value',

    'render_scenario_ab_executive_summary_cards',

    '_render_scenario_ab_executive_summary_cards_from_display_data',

    'build_scenario_ab_comparison_rows',

    'build_scenario_ab_charger_availability_rows',

    'render_scenario_ab_comparison_table',

    'render_scenario_ab_charger_availability_table',

    '_render_scenario_ab_chart_or_message',

    '_should_show_scenario_ab_occupancy_chart',

    '_should_show_scenario_ab_queue_chart',

    '_should_show_scenario_ab_power_quality_chart',

    '_should_show_scenario_ab_transformer_loading_chart',

    '_float_series_are_nearly_identical',

    'render_scenario_ab_detailed_sections',

    '_render_scenario_ab_detailed_sections_from_display_data',

    '_resolve_scenario_ab_selected_section',

    '_render_scenario_ab_decision_summary',

    '_render_scenario_ab_highlight_group',

    '_render_scenario_ab_highlight_card',

    '_scenario_ab_highlight_primary_line',

    '_scenario_ab_highlight_delta_text',

    '_scenario_ab_highlight_row_style',

    '_scenario_ab_highlight_value',

    '_scenario_ab_section_visual_children',

    '_scenario_ab_section_select_id',

    '_scenario_ab_detail_card_style',

    '_render_scenario_ab_section_summary_content',

    '_render_scenario_ab_evidence_metric_cards',

    '_render_scenario_ab_evidence_metric_card',

    '_scenario_ab_evidence_metric_primary_value',

    '_scenario_ab_evidence_metric_card_style',

    '_scenario_ab_evidence_metric_label_style',

    '_scenario_ab_evidence_metric_value_style',

    '_scenario_ab_evidence_metric_context_style',

    '_scenario_ab_evidence_delta_text',

    '_scenario_ab_unsigned_display_text',

    '_scenario_ab_evidence_metric_outcome',

    '_scenario_ab_evidence_status_outcome',

    '_scenario_ab_evidence_status_severity',

    '_scenario_ab_evidence_metric_context',

    '_scenario_ab_select_evidence_metrics',

    '_scenario_ab_sort_evidence_metrics',

    '_scenario_ab_evidence_priority_index',

    '_scenario_ab_metric_has_visible_difference',

    '_scenario_ab_metric_is_empty_verification',

    '_render_scenario_ab_section_evidence_content',

    '_render_scenario_ab_evidence_panel',

    '_scenario_ab_reason_explanation',

    '_format_scenario_ab_scalar_value',

    '_render_scenario_ab_metric_value',

    '_render_scenario_ab_metric_change',

    '_render_scenario_ab_detail_section',

    '_render_scenario_ab_compact_no_difference_section',

    '_render_scenario_ab_numeric_table',

    '_render_scenario_ab_status_table',

    '_render_scenario_ab_value_chip',

    '_render_scenario_ab_status_chip',

    '_render_scenario_ab_change_indicator',

    '_scenario_ab_change_badge',

    '_scenario_ab_semantic_badge_style',

    '_scenario_ab_section_summary_badge_style',

    '_scenario_ab_status_chip_colors',

    'render_scenario_preset_details',

    'render_comparison_scenario_preset_details',

    '_render_changed_assumptions_summary',

    '_comparison_empty_state_children',

    '_render_scenario_comparison_collapsed_bar',

    '_build_scenario_ab_results_render_state',

]

