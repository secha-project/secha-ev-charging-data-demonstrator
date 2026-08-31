"""Smart-charging comparison rendering helpers."""

from ._shared import *
from .formatters import *

def render_comparison_kpi_cards(
    comparison_metrics: ComparisonMetrics,
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> list[Any]:
    """Render Smart Charging KPI cards from prepared descriptor data."""

    return _render_smart_charging_kpi_cards_from_descriptors(
        prepare_smart_charging_card_descriptors(
            uncontrolled_metrics,
            smart_metrics,
            comparison_metrics,
        )
    )

def _render_smart_charging_kpi_cards_from_descriptors(
    descriptors: tuple[Any, ...],
) -> list[Any]:
    """Render prepared Smart Charging KPI descriptors with shared presentation."""

    return [_smart_charging_kpi_card(descriptor) for descriptor in descriptors]

def _smart_charging_kpi_card(descriptor: Any) -> Any:
    """Render one Smart Charging KPI card from prepared descriptor data."""

    children = [
        html.Strong(descriptor.title),
        html.Span(
            _smart_charging_main_result(descriptor),
            style=_scenario_ab_executive_change_style(descriptor.outcome),
        ),
        html.Span(
            _smart_charging_headline_label(descriptor),
            style=KPI_LABEL_TEXT_STYLE,
        ),
    ]
    supporting_context = _smart_charging_supporting_context(descriptor)
    if supporting_context:
        children.append(
            html.Span(
                supporting_context,
                style=SUPPORTING_TEXT_STYLE,
            )
        )

    return html.Div(
        children,
        style=_scenario_ab_executive_card_style(descriptor.outcome),
    )

def _smart_charging_headline_label(descriptor: Any) -> str:
    """Return the compact label shown below one Smart Charging headline."""

    if descriptor.card_id == "service_impact":
        if descriptor.delta.value_format == "hours_signed":
            return "Average waiting time change"
        return "Planner-facing service outcome"
    if descriptor.card_id == "power_quality_impact":
        return "Smart Charging overall PQ risk"
    if descriptor.card_id == "grid_infrastructure_status":
        return "Planner-facing grid status"
    return descriptor.delta.label

def _smart_charging_main_result(descriptor: Any) -> str:
    """Return the primary compact result for one Smart Charging card."""

    if descriptor.card_id == "service_impact":
        if descriptor.delta.value_format == "hours_signed":
            return f"Avg. wait {_format_smart_charging_delta_value(descriptor.delta)}"
        return str(descriptor.delta.value)
    if descriptor.card_id == "power_quality_impact":
        return _power_quality_card_main_result(descriptor)

    return _format_smart_charging_delta_value(descriptor.delta)

def _smart_charging_supporting_context(descriptor: Any) -> str | None:
    """Return one compact before-after context line for a Smart Charging card."""

    before_value = _format_prepared_card_field_value(
        descriptor.before.value_format,
        descriptor.before.value,
    )
    after_value = _format_prepared_card_field_value(
        descriptor.after.value_format,
        descriptor.after.value,
    )

    if descriptor.card_id == "grid_infrastructure_status":
        if before_value == after_value:
            return _compact_grid_context(after_value)
        return _changed_grid_context(before_value, after_value)

    if descriptor.card_id == "service_impact":
        return _service_waiting_context(before_value, after_value)

    if descriptor.card_id == "power_quality_impact":
        return _power_quality_score_context(before_value, after_value)

    if before_value == "N/A" and after_value == "N/A":
        return None

    return _comparison_before_after_text(before_value, after_value)

def _service_waiting_context(before_value: str, after_value: str) -> str | None:
    """Return compact service wait context from prepared service text."""

    before_wait = _extract_service_average_wait(before_value)
    after_wait = _extract_service_average_wait(after_value)
    if before_wait is None and after_wait is None:
        return None
    return _comparison_before_after_text(
        before_wait or "N/A",
        after_wait or "N/A",
    )

def _extract_service_average_wait(value: str) -> str | None:
    """Extract and format the average-wait field from prepared service text."""

    marker = "Avg wait:"
    if marker not in value:
        return None
    raw_value = value.split(marker, 1)[1].strip()
    if raw_value in {"", "None", "N/A"}:
        return "N/A"
    try:
        return format_hours(float(raw_value))
    except ValueError:
        return raw_value

def _power_quality_card_main_result(descriptor: Any) -> str:
    """Return compact PQ risk and score text for the executive card."""

    after_text = _format_prepared_card_field_value(
        descriptor.after.value_format,
        descriptor.after.value,
    )
    level = _extract_labeled_text_value(after_text, "Level")
    score = _extract_labeled_text_value(after_text, "Score")
    if level is not None and score is not None:
        try:
            formatted_score = f"{float(score):,.1f}"
        except ValueError:
            formatted_score = score
        return f"{level.capitalize()} risk · {formatted_score} / 100"

    if descriptor.delta.value_format == "text":
        return str(descriptor.delta.value)

    return _format_smart_charging_delta_value(descriptor.delta)

def _power_quality_score_context(before_value: str, after_value: str) -> str | None:
    """Return compact PQ score before-after text."""

    before_score = _extract_labeled_text_value(before_value, "Score")
    after_score = _extract_labeled_text_value(after_value, "Score")
    if before_score is None and after_score is None:
        return None
    return _comparison_before_after_text(
        _format_compact_score(before_score),
        _format_compact_score(after_score),
    )

def _extract_labeled_text_value(value: str, label: str) -> str | None:
    """Extract a semicolon-delimited labeled value."""

    marker = f"{label}:"
    for part in value.split(";"):
        stripped = part.strip()
        if stripped.startswith(marker):
            return stripped.removeprefix(marker).strip()
    return None

def _format_compact_score(value: str | None) -> str:
    """Format one compact score value."""

    if value is None:
        return "N/A"
    try:
        return f"{float(value):,.1f}"
    except ValueError:
        return value

def _changed_grid_context(before_value: str, after_value: str) -> str:
    """Return changed grid context without repeating unchanged fragments."""

    before_parts = _split_grid_context(before_value)
    after_parts = _split_grid_context(after_value)
    changed_parts = [
        after_part
        for before_part, after_part in zip(before_parts, after_parts, strict=False)
        if before_part != after_part
    ]
    if not changed_parts:
        return _compact_grid_context(after_value)
    return " · ".join(changed_parts)

def _split_grid_context(value: str) -> list[str]:
    """Normalize prepared grid context fragments for compact card display."""

    return [
        _compact_grid_context_part(part)
        for part in value.split(";")
        if part.strip()
    ]

def _compact_grid_context(value: str) -> str:
    """Return a compact grid status context line."""

    return " · ".join(_split_grid_context(value))

def _compact_grid_context_part(value: str) -> str:
    """Return one compact grid context fragment."""

    part = value.replace("Adequacy: ", "").strip()
    if part.startswith("Transformer:"):
        return f"{_format_grid_percent_fragment(part.removeprefix('Transformer:'))} transformer"
    if part.startswith("Transformer "):
        return f"{_format_grid_percent_fragment(part.removeprefix('Transformer '))} transformer"
    if part.startswith("Feeder:"):
        return f"{_format_grid_percent_fragment(part.removeprefix('Feeder:'))} feeder"
    if part.startswith("Feeder "):
        return f"{_format_grid_percent_fragment(part.removeprefix('Feeder '))} feeder"
    return part

def _format_grid_percent_fragment(value: str) -> str:
    """Return a compact percentage fragment from prepared grid text."""

    cleaned_value = value.strip().removesuffix("%").strip()
    try:
        return format_percent(float(cleaned_value))
    except ValueError:
        return value.strip()

def _format_smart_charging_delta_value(delta: Any) -> str:
    """Return a compact Smart Charging delta with explicit change direction."""

    if delta.value_format == "text":
        return str(delta.value)

    formatted_value = _format_scenario_ab_absolute_change_value(
        delta.value_format,
        delta.value,
    )
    if delta.value in (None, 0, 0.0):
        return "No change"
    if float(delta.value) > 0:
        return f"↓ {formatted_value}"
    return f"↑ {formatted_value}"

def _format_prepared_card_field_value(format_id: str, value: Any) -> str:
    """Format one prepared Smart Charging card field using presentation-only rules."""

    if format_id == "text":
        return str(value)

    return _format_scenario_ab_scalar_value(format_id, value)

def _comparison_before_after_text(uncontrolled_value: str, smart_value: str) -> str:
    """Return one compact before/after context string for a comparison KPI."""
    return f"{uncontrolled_value} -> {smart_value}"

def _format_connection_capacity_adequacy_change(
    comparison_metrics: ComparisonMetrics,
) -> str:
    """Return how connection-capacity adequacy changes by strategy."""
    uncontrolled_adequate = (
        comparison_metrics.uncontrolled_connection_capacity_adequate_indicator
    )
    smart_adequate = (
        comparison_metrics.smart_connection_capacity_adequate_indicator
    )
    if uncontrolled_adequate and not smart_adequate:
        return "Worsened"

    if not uncontrolled_adequate and smart_adequate:
        return "Improved"

    return "No change"

def build_charging_performance_comparison_rows(
    comparison_metrics: ComparisonMetrics,
) -> list[tuple[str, Any, Any, Any]]:
    """Map completed comparison metrics into charging-performance summary rows."""
    rows = [
        (
            "Peak occupied chargers",
            format_charger_count(
                comparison_metrics.uncontrolled_peak_occupied_charger_count
            ),
            format_charger_count(
                comparison_metrics.smart_peak_occupied_charger_count
            ),
            format_signed_charger_count(
                comparison_metrics.peak_occupied_charger_count_difference
            ),
        ),
        (
            "Queue present",
            _format_queue_present_value(
                comparison_metrics.uncontrolled_queue_present_indicator
            ),
            _format_queue_present_value(
                comparison_metrics.smart_queue_present_indicator
            ),
            _undefined_metric_value(
                "Queue present difference",
                NON_NUMERIC_DIFFERENCE_NOT_APPLICABLE_HELPER,
                text=NOT_APPLICABLE_METRIC_TEXT,
            ),
        ),
        (
            "Maximum queue length",
            format_vehicle_count(
                comparison_metrics.uncontrolled_maximum_queue_length
            ),
            format_vehicle_count(comparison_metrics.smart_maximum_queue_length),
            format_signed_vehicle_count(
                comparison_metrics.maximum_queue_length_difference
            ),
        ),
        (
            "Average waiting time (h)",
            _optional_metric_value(
                comparison_metrics.uncontrolled_average_waiting_time_hours,
                format_hours,
                label="Uncontrolled average waiting time",
                explanation=WAITING_TIME_UNAVAILABLE_HELPER,
            ),
            _optional_metric_value(
                comparison_metrics.smart_average_waiting_time_hours,
                format_hours,
                label="Smart average waiting time",
                explanation=WAITING_TIME_UNAVAILABLE_HELPER,
            ),
            _optional_metric_value(
                comparison_metrics.average_waiting_time_difference_hours,
                format_signed_hours,
                label="Average waiting time difference",
                explanation=DIFFERENCE_UNAVAILABLE_HELPER,
            ),
        ),
    ]

    if not _comparison_has_queue_pressure(comparison_metrics):
        return rows[:1]

    return rows

def build_power_quality_comparison_rows(
    comparison_metrics: ComparisonMetrics,
) -> list[tuple[str, Any, Any, Any]]:
    """Map completed comparison metrics into power-quality summary rows."""
    rows = [
        (
            "Overall PQ risk score",
            format_risk_score(comparison_metrics.uncontrolled_overall_pq_risk_score),
            format_risk_score(comparison_metrics.smart_overall_pq_risk_score),
            format_signed_score_points(
                comparison_metrics.overall_pq_risk_score_difference
            ),
        ),
        (
            "PQ warning count",
            format_warning_count(
                comparison_metrics.uncontrolled_power_quality_warning_count
            ),
            format_warning_count(comparison_metrics.smart_power_quality_warning_count),
            format_signed_warning_count(
                comparison_metrics.power_quality_warning_count_difference
            ),
        ),
    ]

    if _comparison_has_changed_power_quality_level(comparison_metrics):
        rows.insert(
            1,
            (
                "Overall PQ risk level",
                format_power_quality_risk_level(
                    comparison_metrics.uncontrolled_overall_pq_risk_level
                ),
                format_power_quality_risk_level(
                    comparison_metrics.smart_overall_pq_risk_level
                ),
                _undefined_metric_value(
                    "Overall PQ risk level difference",
                    NON_NUMERIC_DIFFERENCE_NOT_APPLICABLE_HELPER,
                    text=NOT_APPLICABLE_METRIC_TEXT,
                ),
            ),
        )

    return rows

def _smart_charging_queue_evidence_state(
    comparison_metrics: ComparisonMetrics,
) -> tuple[dict[str, Any], Any, dict[str, Any]]:
    """Return queue-chart and status visibility for progressive disclosure."""
    if _comparison_has_queue_pressure(comparison_metrics):
        return {}, "", {"display": "none"}

    return (
        {"display": "none"},
        create_compact_status_message("No queues formed during the simulation."),
        {},
    )

def _smart_charging_power_quality_status_state(
    comparison_metrics: ComparisonMetrics,
) -> tuple[Any, dict[str, Any]]:
    """Return a compact PQ status message when the qualitative level is unchanged."""
    message = _power_quality_status_message(comparison_metrics)
    if message is None:
        return "", {"display": "none"}

    return create_compact_status_message(message), {}

def _compact_status_summary(
    headline: str,
    rows: list[tuple[str, str]],
) -> Any:
    """Render a compact labeled summary block."""

    return html.Div(
        [
            html.P(html.Strong(headline), style={"margin": "0 0 0.65rem 0"}),
            _status_metric_rows(rows),
        ],
        style=STATUS_BLOCK_STYLE,
    )

def build_technical_details_comparison_rows(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
    comparison_metrics: ComparisonMetrics,
) -> list[tuple[str, Any, Any, Any]]:
    """Map completed comparison metrics into lower-priority diagnostic rows."""
    return [
        (
            "Capacity utilization (%)",
            format_percent(uncontrolled_metrics.capacity_utilization),
            format_percent(smart_metrics.capacity_utilization),
            format_signed_percentage_points(
                comparison_metrics.capacity_utilization_difference
            ),
        ),
        (
            "Recommended connection capacity (kW)",
            format_power_kw(uncontrolled_metrics.recommended_connection_capacity_kw),
            format_power_kw(smart_metrics.recommended_connection_capacity_kw),
            format_signed_power_kw(
                comparison_metrics.recommended_connection_capacity_difference_kw
            ),
        ),
        (
            "Connection capacity adequacy",
            format_connection_capacity_adequacy_value(
                comparison_metrics.uncontrolled_connection_capacity_adequate_indicator
            ),
            format_connection_capacity_adequacy_value(
                comparison_metrics.smart_connection_capacity_adequate_indicator
            ),
            _format_connection_capacity_adequacy_change(comparison_metrics),
        ),
        (
            "Capacity recommendation basis",
            format_connection_capacity_recommendation_reason(
                comparison_metrics.uncontrolled_connection_capacity_recommendation_reason
            ),
            format_connection_capacity_recommendation_reason(
                comparison_metrics.smart_connection_capacity_recommendation_reason
            ),
            _format_status_transition_change(
                format_connection_capacity_recommendation_reason(
                    comparison_metrics.uncontrolled_connection_capacity_recommendation_reason
                ),
                format_connection_capacity_recommendation_reason(
                    comparison_metrics.smart_connection_capacity_recommendation_reason
                ),
            ),
        ),
        (
            "Connection capacity exceeded",
            format_connection_capacity_exceeded_value(
                uncontrolled_metrics.connection_capacity_exceeded
            ),
            format_connection_capacity_exceeded_value(
                smart_metrics.connection_capacity_exceeded
            ),
            _format_worse_when_true_change(
                uncontrolled_metrics.connection_capacity_exceeded,
                smart_metrics.connection_capacity_exceeded,
            ),
        ),
        (
            "Maximum capacity exceedance (kW)",
            format_power_kw(uncontrolled_metrics.maximum_capacity_exceedance_kw),
            format_power_kw(smart_metrics.maximum_capacity_exceedance_kw),
            format_signed_power_kw(
                uncontrolled_metrics.maximum_capacity_exceedance_kw
                - smart_metrics.maximum_capacity_exceedance_kw
            ),
        ),
        (
            "Capacity exceedance duration (h)",
            format_hours(uncontrolled_metrics.capacity_exceedance_duration_hours),
            format_hours(smart_metrics.capacity_exceedance_duration_hours),
            format_signed_hours(
                comparison_metrics.exceedance_duration_reduction_hours
            ),
        ),
        (
            "Average transformer loading (%)",
            format_percent(uncontrolled_metrics.average_transformer_loading_percent),
            format_percent(smart_metrics.average_transformer_loading_percent),
            format_signed_percentage_points(
                comparison_metrics.average_transformer_loading_percent_difference
            ),
        ),
        (
            "Transformer overload",
            _format_overload_indicator_value(
                uncontrolled_metrics.transformer_overload_indicator
            ),
            _format_overload_indicator_value(
                smart_metrics.transformer_overload_indicator
            ),
            _format_worse_when_true_change(
                uncontrolled_metrics.transformer_overload_indicator,
                smart_metrics.transformer_overload_indicator,
            ),
        ),
        (
            "Transformer overload duration (h)",
            format_hours(uncontrolled_metrics.transformer_overload_duration_hours),
            format_hours(smart_metrics.transformer_overload_duration_hours),
            format_signed_hours(
                comparison_metrics.transformer_overload_duration_difference_hours
            ),
        ),
        (
            "Maximum transformer overload (kW)",
            format_power_kw(uncontrolled_metrics.transformer_maximum_overload_kw),
            format_power_kw(smart_metrics.transformer_maximum_overload_kw),
            format_signed_power_kw(
                comparison_metrics.transformer_maximum_overload_difference_kw
            ),
        ),
        (
            "Transformer thermal risk",
            format_thermal_risk_level(uncontrolled_metrics.transformer_thermal_risk_level),
            format_thermal_risk_level(smart_metrics.transformer_thermal_risk_level),
            _format_status_transition_change(
                format_thermal_risk_level(
                    uncontrolled_metrics.transformer_thermal_risk_level
                ),
                format_thermal_risk_level(smart_metrics.transformer_thermal_risk_level),
            ),
        ),
        (
            "Feeder overload",
            _format_overload_indicator_value(uncontrolled_metrics.feeder_overload_indicator),
            _format_overload_indicator_value(smart_metrics.feeder_overload_indicator),
            _format_worse_when_true_change(
                uncontrolled_metrics.feeder_overload_indicator,
                smart_metrics.feeder_overload_indicator,
            ),
        ),
        (
            "Overloaded feeders",
            format_feeder_count(uncontrolled_metrics.overloaded_feeder_count),
            format_feeder_count(smart_metrics.overloaded_feeder_count),
            format_signed_feeder_count(
                comparison_metrics.overloaded_feeder_count_difference
            ),
        ),
        (
            "Highest feeder thermal risk",
            format_thermal_risk_level(
                uncontrolled_metrics.highest_feeder_thermal_risk_level
            ),
            format_thermal_risk_level(smart_metrics.highest_feeder_thermal_risk_level),
            _format_status_transition_change(
                format_thermal_risk_level(
                    uncontrolled_metrics.highest_feeder_thermal_risk_level
                ),
                format_thermal_risk_level(smart_metrics.highest_feeder_thermal_risk_level),
            ),
        ),
        (
            "Peak harmonic risk score",
            format_risk_score(uncontrolled_metrics.peak_harmonic_risk_score),
            format_risk_score(smart_metrics.peak_harmonic_risk_score),
            format_signed_score_points(
                comparison_metrics.peak_harmonic_risk_score_difference
            ),
        ),
        (
            "Harmonic risk duration (h)",
            format_hours(uncontrolled_metrics.harmonic_risk_duration_hours),
            format_hours(smart_metrics.harmonic_risk_duration_hours),
            format_signed_hours(
                comparison_metrics.harmonic_risk_duration_difference_hours
            ),
        ),
        (
            "Harmonic risk level",
            format_power_quality_risk_level(uncontrolled_metrics.harmonic_risk_level),
            format_power_quality_risk_level(smart_metrics.harmonic_risk_level),
            _format_status_transition_change(
                format_power_quality_risk_level(uncontrolled_metrics.harmonic_risk_level),
                format_power_quality_risk_level(smart_metrics.harmonic_risk_level),
            ),
        ),
        (
            "Peak current imbalance (%)",
            format_percent(uncontrolled_metrics.peak_current_imbalance_percent),
            format_percent(smart_metrics.peak_current_imbalance_percent),
            format_signed_percentage_points(
                comparison_metrics.peak_current_imbalance_percent_difference
            ),
        ),
        (
            "Current imbalance duration (h)",
            format_hours(uncontrolled_metrics.imbalance_duration_hours),
            format_hours(smart_metrics.imbalance_duration_hours),
            format_signed_hours(comparison_metrics.imbalance_duration_difference_hours),
        ),
        (
            "Current imbalance risk level",
            format_power_quality_risk_level(
                uncontrolled_metrics.current_imbalance_risk_level
            ),
            format_power_quality_risk_level(smart_metrics.current_imbalance_risk_level),
            _format_status_transition_change(
                format_power_quality_risk_level(
                    uncontrolled_metrics.current_imbalance_risk_level
                ),
                format_power_quality_risk_level(smart_metrics.current_imbalance_risk_level),
            ),
        ),
        (
            "Peak charger utilization (%)",
            _optional_metric_value(
                uncontrolled_metrics.peak_charger_utilization_percent,
                format_percent,
                label="Uncontrolled peak charger utilization",
                explanation=CHARGER_UTILIZATION_UNAVAILABLE_HELPER,
            ),
            _optional_metric_value(
                smart_metrics.peak_charger_utilization_percent,
                format_percent,
                label="Smart peak charger utilization",
                explanation=CHARGER_UTILIZATION_UNAVAILABLE_HELPER,
            ),
            _optional_metric_value(
                comparison_metrics.peak_charger_utilization_percent_difference,
                format_signed_percentage_points,
                label="Peak charger utilization difference",
                explanation=DIFFERENCE_UNAVAILABLE_HELPER,
            ),
        ),
        (
            "Average occupied chargers",
            format_charger_count(
                uncontrolled_metrics.average_occupied_charger_count,
                decimals=1,
            ),
            format_charger_count(
                smart_metrics.average_occupied_charger_count,
                decimals=1,
            ),
            format_signed_charger_count(
                comparison_metrics.average_occupied_charger_count_difference,
                decimals=1,
            ),
        ),
        (
            "Average queue length",
            format_vehicle_count(uncontrolled_metrics.average_queue_length, decimals=1),
            format_vehicle_count(smart_metrics.average_queue_length, decimals=1),
            format_signed_vehicle_count(
                comparison_metrics.average_queue_length_difference,
                decimals=1,
            ),
        ),
        (
            "Queue duration (h)",
            format_hours(uncontrolled_metrics.queue_duration_hours),
            format_hours(smart_metrics.queue_duration_hours),
            format_signed_hours(comparison_metrics.queue_duration_difference_hours),
        ),
        (
            "Maximum waiting time (h)",
            _optional_metric_value(
                uncontrolled_metrics.maximum_waiting_time_hours,
                format_hours,
                label="Uncontrolled maximum waiting time",
                explanation=WAITING_TIME_UNAVAILABLE_HELPER,
            ),
            _optional_metric_value(
                smart_metrics.maximum_waiting_time_hours,
                format_hours,
                label="Smart maximum waiting time",
                explanation=WAITING_TIME_UNAVAILABLE_HELPER,
            ),
            _optional_metric_value(
                comparison_metrics.maximum_waiting_time_difference_hours,
                format_signed_hours,
                label="Maximum waiting time difference",
                explanation=DIFFERENCE_UNAVAILABLE_HELPER,
            ),
        ),
        (
            "Vehicles waiting",
            format_vehicle_count(uncontrolled_metrics.vehicles_waiting_count),
            format_vehicle_count(smart_metrics.vehicles_waiting_count),
            format_signed_vehicle_count(
                comparison_metrics.vehicles_waiting_count_difference
            ),
        ),
    ]

def _render_strategy_comparison_table(
    rows: list[tuple[Any, Any, Any, Any]],
) -> Any:
    """Render a compact four-column strategy comparison table."""
    return html.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Metric", style=TABLE_HEADER_CELL_STYLE),
                        html.Th("Uncontrolled charging", style=TABLE_HEADER_CELL_STYLE),
                        html.Th("Smart charging", style=TABLE_HEADER_CELL_STYLE),
                        html.Th(
                            [
                                html.Span("Delta / Status"),
                                html.Br(),
                                html.Span(
                                    "Numeric delta = Uncontrolled - Smart",
                                    style={
                                        "fontSize": "0.74rem",
                                        "fontWeight": "500",
                                        "color": TEXT_SECONDARY_COLOR,
                                    },
                                ),
                            ],
                            style=TABLE_HEADER_CELL_STYLE,
                        ),
                    ]
                )
            ),
            html.Tbody([_comparison_table_row(row) for row in rows]),
        ],
        style=TABLE_STYLE,
    )

def render_charging_performance_comparison_table(
    comparison_metrics: ComparisonMetrics,
) -> Any:
    """Render the Smart Charging charging-performance summary table."""
    return _render_strategy_comparison_table(
        build_charging_performance_comparison_rows(comparison_metrics)
    )

def render_power_quality_comparison_table(
    comparison_metrics: ComparisonMetrics,
) -> Any:
    """Render the Smart Charging power-quality summary table."""
    return _render_strategy_comparison_table(
        build_power_quality_comparison_rows(comparison_metrics)
    )

def _comparison_table_row(row: tuple[Any, ...]) -> Any:
    """Render one detailed comparison table row."""
    return html.Tr([html.Td(value, style=TABLE_CELL_STYLE) for value in row])

def render_detailed_comparison_table(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> Any:
    """Render the Smart Charging technical-details comparison table."""
    comparison_metrics = calculate_comparison_metrics(
        uncontrolled_metrics,
        smart_metrics,
    )
    rows = build_connection_capacity_comparison_rows(
        uncontrolled_metrics,
        smart_metrics,
        comparison_metrics,
    )

    return _render_strategy_comparison_table(rows)

def build_connection_capacity_comparison_rows(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
    comparison_metrics: ComparisonMetrics | None = None,
) -> list[tuple[Any, Any, Any, Any]]:
    """Map completed strategy metrics into technical-details comparison rows."""
    resolved_comparison_metrics = comparison_metrics or calculate_comparison_metrics(
        uncontrolled_metrics,
        smart_metrics,
    )
    return build_technical_details_comparison_rows(
        uncontrolled_metrics,
        smart_metrics,
        resolved_comparison_metrics,
    )

__all__ = [

    'render_comparison_kpi_cards',

    '_render_smart_charging_kpi_cards_from_descriptors',

    '_smart_charging_kpi_card',

    '_smart_charging_headline_label',

    '_smart_charging_main_result',

    '_smart_charging_supporting_context',

    '_service_waiting_context',

    '_extract_service_average_wait',

    '_power_quality_card_main_result',

    '_power_quality_score_context',

    '_extract_labeled_text_value',

    '_format_compact_score',

    '_changed_grid_context',

    '_split_grid_context',

    '_compact_grid_context',

    '_compact_grid_context_part',

    '_format_grid_percent_fragment',

    '_format_smart_charging_delta_value',

    '_format_prepared_card_field_value',

    '_comparison_before_after_text',

    '_format_connection_capacity_adequacy_change',

    'build_charging_performance_comparison_rows',

    'build_power_quality_comparison_rows',

    '_smart_charging_queue_evidence_state',

    '_smart_charging_power_quality_status_state',

    '_compact_status_summary',

    'build_technical_details_comparison_rows',

    '_render_strategy_comparison_table',

    'render_charging_performance_comparison_table',

    'render_power_quality_comparison_table',

    '_comparison_table_row',

    'render_detailed_comparison_table',

    'build_connection_capacity_comparison_rows',

]

