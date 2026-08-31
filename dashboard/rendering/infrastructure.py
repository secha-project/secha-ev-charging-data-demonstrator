"""Infrastructure, grid, and power-quality rendering helpers."""

from ._shared import *
from .formatters import *
from .scenario_comparison import _comparison_kpi_card

def render_infrastructure_summary(metrics: Metrics, scenario: Scenario) -> Any:
    """Render the executive Infrastructure status from existing Metrics fields."""
    status_is_sufficient = _infrastructure_status_is_adequate(metrics)
    status_label = "ADEQUATE" if status_is_sufficient else "CONSTRAINED"
    status_color = STATUS_GREEN if status_is_sufficient else STATUS_RED
    status_background = (
        STATUS_GREEN_BACKGROUND if status_is_sufficient else STATUS_RED_BACKGROUND
    )

    return html.Div(
        [
            html.Span(
                status_label,
                style={
                    **INFRASTRUCTURE_STATUS_BADGE_BASE_STYLE,
                    "backgroundColor": status_background,
                    "border": f"1px solid {status_color}",
                    "color": status_color,
                },
            ),
            _infrastructure_status_rows(
                (
                    (
                        "Decision Summary",
                        _format_infrastructure_decision_summary(metrics),
                    ),
                    (
                        "Constraint Diagnosis",
                        _format_infrastructure_constraint_diagnosis(metrics),
                    ),
                    (
                        "Planning Impact",
                        _format_infrastructure_planning_impact(metrics),
                    ),
                    (
                        "Recommended Planning Focus",
                        _format_infrastructure_planning_focus(metrics),
                    ),
                )
            ),
        ],
        style=INFRASTRUCTURE_STATUS_PANEL_STYLE,
    )

def _infrastructure_status_rows(metric_rows: tuple[tuple[str, Any], ...]) -> Any:
    """Return compact rows for the Infrastructure status panel."""
    return html.Div(
        [
            html.Div(
                [
                    html.Span(
                        f"{label}:",
                        style=INFRASTRUCTURE_STATUS_ROW_LABEL_STYLE,
                    ),
                    html.Span(value, style=INFRASTRUCTURE_STATUS_ROW_VALUE_STYLE),
                ],
                style=INFRASTRUCTURE_STATUS_ROW_STYLE,
            )
            for label, value in metric_rows
        ],
        style={"marginTop": "0.2rem", "display": "flex", "flexDirection": "column", "gap": "0.35rem"},
    )

def _infrastructure_status_is_adequate(metrics: Metrics) -> bool:
    """Return whether the current infrastructure remains adequate."""
    return (
        _charger_planning_rule_is_met(metrics)
        and metrics.connection_capacity_adequate_indicator
    )

def _format_infrastructure_decision_summary(metrics: Metrics) -> str:
    """Return the planner-facing infrastructure decision outcome."""
    if _infrastructure_status_is_adequate(metrics):
        return "Infrastructure is adequate for the modeled service rule."

    if metrics.primary_constraint_reason == "charger_power":
        return "Infrastructure is constrained by charger-power limits."

    if (
        metrics.primary_constraint_reason == "grid_connection_capacity"
        or not metrics.connection_capacity_adequate_indicator
    ):
        return "Infrastructure is constrained by connection-capacity pressure."

    if metrics.primary_constraint_reason == "mixed":
        return "Infrastructure is constrained by multiple interacting limits."

    if metrics.primary_constraint_reason == "charging_window":
        return "Infrastructure is constrained by charging-window limits."

    return "Infrastructure is constrained under the current scenario."

def _format_infrastructure_constraint_diagnosis(metrics: Metrics) -> str:
    """Return the dominant modeled infrastructure diagnosis."""
    if _infrastructure_status_is_adequate(metrics):
        return (
            "No dominant infrastructure bottleneck is indicated under current "
            "assumptions."
        )

    if metrics.primary_constraint_reason == "charger_availability":
        return "Charger availability is the dominant modeled bottleneck."

    if metrics.primary_constraint_reason == "charger_power":
        return "Charger power is the dominant modeled bottleneck."

    if metrics.primary_constraint_reason == "grid_connection_capacity":
        return "Grid connection capacity is the dominant modeled bottleneck."

    if metrics.primary_constraint_reason == "mixed":
        return (
            "No single infrastructure change resolves the dominant modeled "
            "pressure."
        )

    if metrics.primary_constraint_reason == "charging_window":
        return "Available charging time is the dominant modeled bottleneck."

    if not metrics.connection_capacity_adequate_indicator:
        return "Grid connection capacity is the dominant modeled bottleneck."

    return (
        "No single dominant infrastructure bottleneck is isolated by the "
        "available outputs."
    )

def _format_infrastructure_planning_impact(metrics: Metrics) -> str:
    """Return the planning consequence implied by the modeled result."""
    if _infrastructure_status_is_adequate(metrics):
        return (
            "The scenario does not currently create clear infrastructure "
            "expansion pressure."
        )

    if metrics.primary_constraint_reason == "charger_availability":
        return (
            "Queueing pressure is likely to affect service performance during "
            "the charging-allowed window."
        )

    if metrics.primary_constraint_reason == "charger_power":
        return (
            "Increasing charger count alone is unlikely to resolve the modeled "
            "service limitation."
        )

    if (
        metrics.primary_constraint_reason == "grid_connection_capacity"
        or not metrics.connection_capacity_adequate_indicator
    ):
        return (
            "Additional chargers alone are unlikely to resolve the modeled "
            "service limitation."
        )

    if metrics.primary_constraint_reason == "mixed":
        return (
            "Incremental investment in only one area may leave the scenario "
            "materially constrained."
        )

    if metrics.primary_constraint_reason == "charging_window":
        return (
            "Infrastructure expansion alone is unlikely to resolve the modeled "
            "service limitation."
        )

    return (
        "The scenario indicates modeled infrastructure pressure that should be "
        "reviewed before investment decisions are finalized."
    )

def _format_infrastructure_planning_focus(metrics: Metrics) -> str:
    """Return the next planner-facing area of focus."""
    if _infrastructure_status_is_adequate(metrics):
        return (
            "Maintain the baseline and test sensitivity to higher demand or "
            "tighter service expectations."
        )

    if metrics.primary_constraint_reason == "charger_availability":
        return (
            "Prioritize charger provision before reviewing larger "
            "connection-capacity changes."
        )

    if metrics.primary_constraint_reason == "charger_power":
        return "Review charger power sizing before expanding charger count."

    if (
        metrics.primary_constraint_reason == "grid_connection_capacity"
        or not metrics.connection_capacity_adequate_indicator
    ):
        return "Review connection-capacity sizing before expanding charger count."

    if metrics.primary_constraint_reason == "mixed":
        return (
            "Review charger count, charger power, and connection-capacity "
            "assumptions together."
        )

    if metrics.primary_constraint_reason == "charging_window":
        return (
            "Review charging-window and scheduling assumptions before resizing "
            "infrastructure."
        )

    return (
        "Recheck the dominant constraint and supporting assumptions before "
        "committing to infrastructure changes."
    )

def render_charger_planning_status(
    metrics: Metrics,
    scenario: Scenario,
) -> Any:
    """Render planner-facing charger-count status from completed metrics only."""
    rule_is_met = _charger_planning_rule_is_met(metrics)
    waiting_tolerance_text = format_service_waiting_tolerance_minutes(
        scenario.charger_service_max_waiting_time_minutes
    )
    data_is_available = _charger_planning_status_data_is_available(
        metrics,
        scenario,
        rule_is_met=rule_is_met,
    )

    if not data_is_available:
        return _charger_planning_status_block(
            title="Recommendation unavailable",
            summary=(
                "The dashboard cannot produce a charger recommendation from "
                "the available metrics."
            ),
            detail=(
                "Run the scenario again with completed charger-planning metrics. "
                f"This scenario applies a waiting tolerance of {waiting_tolerance_text}."
            ),
        )

    if rule_is_met:
        summary = "Current charger count satisfies the modeled service rule."
        detail = "No charger expansion is indicated under current assumptions."
        if scenario.vehicles == 0:
            detail = "This scenario has no modeled vehicle charging demand."
        elif _charger_planning_has_tolerated_waiting(metrics):
            detail = (
                "Waiting is present but remains within the "
                f"{waiting_tolerance_text} service expectation for this "
                "scenario, so no charger expansion is indicated under current "
                "assumptions."
            )

        return _charger_planning_status_block(
            title="No charger expansion indicated",
            summary=summary,
            detail=detail,
            metric_rows=[
                ("Applied waiting tolerance", waiting_tolerance_text),
                (
                    "Required charger count",
                    format_optional_charger_count(metrics.required_charger_count),
                ),
            ],
        )

    if (
        metrics.primary_constraint_reason == "charger_availability"
        and metrics.required_charger_count is not None
        and metrics.additional_chargers_required is not None
    ):
        summary = "Physical charger availability is the primary planning constraint."
        if _charger_planning_is_waiting_limited(metrics):
            detail = (
                "Add "
                f"{format_charger_count(metrics.additional_chargers_required)} "
                f"({format_charger_count(metrics.required_charger_count)} total) "
                f"to keep waiting within the {waiting_tolerance_text} service "
                "expectation for this scenario."
            )
        else:
            detail = (
                "Add "
                f"{format_charger_count(metrics.additional_chargers_required)} "
                f"({format_charger_count(metrics.required_charger_count)} total) "
                "under current assumptions."
            )
        metric_rows = [
            ("Applied waiting tolerance", waiting_tolerance_text),
            ("Current charger count", format_charger_count(scenario.charger_count)),
            (
                "Required charger count",
                format_optional_charger_count(metrics.required_charger_count),
            ),
        ]

        return _charger_planning_status_block(
            title="Add chargers",
            summary=summary,
            detail=detail,
            metric_rows=metric_rows,
        )

    reason_label = CHARGER_PLANNING_REASON_LABELS.get(
        metrics.primary_constraint_reason,
        "the limiting condition cannot be determined reliably",
    )
    return _charger_planning_status_block(
        title="Review non-charger constraint",
        summary=(
            "Adding chargers alone is not the primary recommendation for this "
            "scenario."
        ),
        detail=(
            f"Primary modeled constraint: {reason_label}. "
            f"This scenario applies a waiting tolerance of {waiting_tolerance_text}."
        ),
        metric_rows=[("Applied waiting tolerance", waiting_tolerance_text)],
    )

def _charger_planning_rule_is_met(metrics: Metrics) -> bool:
    """Return whether the completed charger-planning service rule is met."""
    return (
        metrics.energy_delivery_sufficient
        and charger_planning_service_rule_is_met(metrics)
    )

def _charger_planning_has_tolerated_waiting(metrics: Metrics) -> bool:
    """Return whether waiting is present but still acceptable for sizing."""
    return _charger_planning_rule_is_met(metrics) and (
        metrics.queue_present_indicator
        or metrics.vehicles_waiting_count > 0
        or (
            metrics.maximum_waiting_time_hours is not None
            and metrics.maximum_waiting_time_hours > 0.0
        )
        or (
            metrics.average_waiting_time_hours is not None
            and metrics.average_waiting_time_hours > 0.0
        )
    )

def _charger_planning_is_waiting_limited(metrics: Metrics) -> bool:
    """Return whether excess waiting is the only modeled charger shortfall."""
    return (
        not _charger_planning_rule_is_met(metrics)
        and metrics.primary_constraint_reason == "charger_availability"
        and metrics.vehicles_not_started_count == 0
        and metrics.vehicles_with_unmet_energy_count == 0
    )

def _charger_planning_status_data_is_available(
    metrics: Metrics,
    scenario: Scenario,
    *,
    rule_is_met: bool,
) -> bool:
    """Return whether the planning-status metrics are internally consistent."""
    reason = metrics.primary_constraint_reason
    if reason not in CHARGER_PLANNING_REASON_LABELS:
        return False

    if (metrics.required_charger_count is None) != (
        metrics.additional_chargers_required is None
    ):
        return False

    if rule_is_met:
        if metrics.required_charger_count is None:
            return False
        if metrics.additional_chargers_required != 0:
            return False
        if scenario.vehicles == 0:
            return metrics.required_charger_count == 0
        return metrics.required_charger_count == scenario.charger_count

    if reason == "none":
        return False

    if reason == "charger_availability":
        if metrics.required_charger_count is None:
            return True
        return (
            metrics.required_charger_count > scenario.charger_count
            and metrics.additional_chargers_required is not None
            and metrics.additional_chargers_required > 0
            and metrics.additional_chargers_required
            == metrics.required_charger_count - scenario.charger_count
        )

    return (
        metrics.required_charger_count is None
        and metrics.additional_chargers_required is None
    )

def _charger_planning_status_block(
    *,
    title: str,
    summary: str,
    detail: str,
    metric_rows: list[tuple[str, str]] | None = None,
) -> Any:
    """Return a concise charger-planning status block."""
    children: list[Any] = [
        html.P(
            html.Strong(title),
            style={"margin": "0 0 0.5rem 0"},
        ),
        html.P(summary, style={"margin": "0 0 0.5rem 0"}),
        html.P(
            detail,
            style={"margin": "0", "color": TEXT_SECONDARY_COLOR},
        ),
    ]

    if metric_rows:
        children.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.Strong(f"{label}: "),
                            html.Span(value),
                        ],
                        style={"padding": "0.15rem 0"},
                    )
                    for label, value in metric_rows
                ],
                style={"marginTop": "0.75rem"},
            )
        )

    return html.Div(
        children,
        style=STATUS_BLOCK_STYLE,
    )

def _status_metric_rows(metric_rows: list[tuple[str, str]]) -> Any:
    """Return a compact list of label-value status rows."""
    return html.Div(
        [
            html.Div(
                [
                    html.Strong(f"{label}: "),
                    html.Span(value),
                ],
                style={"padding": "0.15rem 0"},
            )
            for label, value in metric_rows
        ],
        style={"marginTop": "0.75rem"},
    )

def _grid_asset_status_block(
    *,
    title: str,
    summary: str,
    detail: str,
    metric_rows: list[tuple[str, str]] | None = None,
) -> Any:
    """Return a concise planner-facing grid-asset status block."""
    children: list[Any] = [
        html.P(
            html.Strong(title),
            style={"margin": "0 0 0.5rem 0"},
        ),
        html.P(summary, style={"margin": "0 0 0.5rem 0"}),
        html.P(
            detail,
            style={"margin": "0", "color": TEXT_SECONDARY_COLOR},
        ),
    ]
    if metric_rows:
        children.append(_status_metric_rows(metric_rows))

    return html.Div(
        children,
        style=STATUS_BLOCK_STYLE,
    )

def render_capacity_planning_kpi_cards(
    metrics: Metrics,
    simulation_result: SimulationResult,
) -> list[Any]:
    """Render active-scenario capacity-planning metrics as KPI cards."""
    margin_is_shortfall = metrics.peak_capacity_margin_kw < 0.0
    margin_title = "Capacity Shortfall" if margin_is_shortfall else "Peak Capacity Margin"
    margin_value = (
        format_power_kw(abs(metrics.peak_capacity_margin_kw))
        if margin_is_shortfall
        else format_signed_power_kw(metrics.peak_capacity_margin_kw)
    )
    return [
        _comparison_kpi_card(
            "Simulated Peak Load",
            "",
            format_power_kw(metrics.peak_load),
        ),
        _comparison_kpi_card(
            "Required Connection Capacity",
            "",
            format_power_kw(metrics.required_connection_capacity_kw),
        ),
        _comparison_kpi_card(
            "Recommended Connection Capacity",
            "",
            format_power_kw(metrics.recommended_connection_capacity_kw),
        ),
        _comparison_kpi_card(
            margin_title,
            "",
            margin_value,
        ),
    ]

def render_charger_availability_kpi_cards(metrics: Metrics) -> list[Any]:
    """Render active-scenario charger-availability KPIs from metrics only."""
    return [
        _comparison_kpi_card(
            "Peak Charger Utilization",
            "",
            _optional_metric_value(
                metrics.peak_charger_utilization_percent,
                format_percent,
                label="Peak Charger Utilization",
                explanation=CHARGER_UTILIZATION_UNAVAILABLE_HELPER,
            ),
        ),
        _comparison_kpi_card(
            "Peak Occupied Chargers",
            "",
            format_charger_count(metrics.peak_occupied_charger_count),
        ),
        _comparison_kpi_card(
            "Maximum Queue Length",
            "",
            format_vehicle_count(metrics.maximum_queue_length),
        ),
        _comparison_kpi_card(
            "Vehicles Not Started",
            "",
            format_vehicle_count(metrics.vehicles_not_started_count),
        ),
    ]

def render_grid_loading_kpi_cards(metrics: Metrics) -> list[Any]:
    """Render active-scenario grid-loading KPIs from metrics only."""
    return [
        _comparison_kpi_card(
            "Peak Transformer Loading",
            "Highest modeled loading",
            format_percent(metrics.peak_transformer_loading_percent),
        ),
        _comparison_kpi_card(
            "Transformer Overload Duration",
            "Timesteps above transformer rating",
            format_hours(metrics.transformer_overload_duration_hours),
        ),
        _comparison_kpi_card(
            "Maximum Transformer Overload",
            "Peak amount above transformer rating",
            format_power_kw(metrics.transformer_maximum_overload_kw),
        ),
        _comparison_kpi_card(
            "Maximum Feeder Loading",
            "Highest modeled feeder peak",
            format_percent(metrics.maximum_feeder_loading_percent),
        ),
        _comparison_kpi_card(
            "Overloaded Feeders",
            "Count of feeders above rating",
            format_feeder_count(metrics.overloaded_feeder_count),
        ),
    ]

def render_grid_loading_status(metrics: Metrics) -> Any:
    """Render a concise planner-facing grid summary from metrics only."""
    if (
        metrics.transformer_thermal_risk_level == "high"
        or metrics.highest_feeder_thermal_risk_level == "high"
        or metrics.transformer_overload_indicator
        or metrics.feeder_overload_indicator
    ):
        return _grid_asset_status_block(
            title="Grid stress indicated",
            summary=(
                "Modeled transformer or feeder stress is indicated under "
                "current assumptions."
            ),
            detail=(
                "Use the KPI row, transformer chart, and feeder loading section to "
                "locate the main loading constraint. Review Power Quality "
                "separately if PQ indicators are also relevant."
            ),
        )

    if (
        metrics.transformer_thermal_risk_level != "low"
        or metrics.highest_feeder_thermal_risk_level != "low"
    ):
        return _grid_asset_status_block(
            title="Review grid loading",
            summary=(
                "Modeled transformer or feeder loading deserves review under "
                "current assumptions."
            ),
            detail=(
                "Use the KPI row, transformer chart, and feeder loading section to "
                "see where loading pressure is concentrated."
            ),
        )

    return _grid_asset_status_block(
        title="No grid loading caution",
        summary=(
            "No modeled transformer or feeder loading caution is indicated "
            "under current assumptions."
        ),
        detail=(
            "Use the chart and feeder loading section for supporting detail, or "
            "review Power Quality separately if PQ indicators are needed."
        ),
    )

def render_power_quality_kpi_cards(metrics: Metrics) -> list[Any]:
    """Render active-scenario power-quality KPIs from metrics only."""
    return [
        _comparison_kpi_card(
            "Overall PQ Risk",
            "",
            format_power_quality_risk_level(metrics.overall_pq_risk_level),
        ),
        _comparison_kpi_card(
            "PQ Warnings",
            "",
            format_warning_count(metrics.power_quality_warning_count),
        ),
        _comparison_kpi_card(
            "Peak Harmonic Risk",
            "",
            format_risk_score(metrics.peak_harmonic_risk_score),
        ),
        _comparison_kpi_card(
            "Harmonic Risk Duration",
            "",
            format_hours(metrics.harmonic_risk_duration_hours),
        ),
        _comparison_kpi_card(
            "Peak Current Imbalance",
            "",
            format_percent(metrics.peak_current_imbalance_percent),
        ),
        _comparison_kpi_card(
            "Current Imbalance Duration",
            "",
            format_hours(metrics.imbalance_duration_hours),
        ),
    ]

def render_power_quality_status(metrics: Metrics) -> Any:
    """Render compact supplemental power-quality status from metrics only."""
    if not _power_quality_status_data_is_available(metrics):
        return html.Span(
            "PQ status unavailable: completed PQ series are needed before "
            "the dashboard can show planner-facing PQ status.",
        )

    overlap_with_grid_stress = _power_quality_overlaps_with_grid_stress(metrics)
    supplemental_messages: list[str] = []
    if (
        metrics.overall_pq_risk_level != "low"
        or metrics.power_quality_warning_count > 0
    ) and metrics.power_quality_message:
        supplemental_messages.append(metrics.power_quality_message)

    if overlap_with_grid_stress and metrics.power_quality_warning_count > 0:
        supplemental_messages.append(
            "PQ warnings also overlap with modeled transformer or feeder "
            "stress, so both results should be reviewed together."
        )

    return " ".join(supplemental_messages)

def _power_quality_status_data_is_available(metrics: Metrics) -> bool:
    """Return whether the PQ status can be rendered from completed series."""
    expected_length = len(get_time_labels())
    return (
        len(metrics.harmonic_risk_score_by_timestep) == expected_length
        and len(metrics.current_imbalance_percent_by_timestep) == expected_length
        and len(metrics.overall_pq_risk_score_by_timestep) == expected_length
    )

def _power_quality_overlaps_with_grid_stress(metrics: Metrics) -> bool:
    """Return whether active PQ warnings coincide with modeled grid stress."""
    if metrics.power_quality_warning_count <= 0:
        return False

    return (
        metrics.transformer_overload_indicator
        or metrics.feeder_overload_indicator
        or metrics.transformer_thermal_risk_level != "low"
        or metrics.highest_feeder_thermal_risk_level != "low"
    )

def render_grid_asset_planning_status(metrics: Metrics) -> Any:
    """Render planner-facing transformer and feeder status from metrics only."""
    if (
        metrics.transformer_thermal_risk_level == "high"
        or metrics.highest_feeder_thermal_risk_level == "high"
        or metrics.transformer_overload_indicator
        or metrics.feeder_overload_indicator
    ):
        return _grid_asset_status_block(
            title="Grid stress indicated",
            summary=(
                "Modeled transformer or feeder stress is indicated under "
                "current assumptions."
            ),
            detail=(
                "Review Grid & Capacity for transformer, feeder, and PQ "
                "diagnostics."
            ),
        )

    if (
        metrics.transformer_thermal_risk_level != "low"
        or metrics.highest_feeder_thermal_risk_level != "low"
    ):
        return _grid_asset_status_block(
            title="Review grid loading",
            summary=(
                "Modeled transformer or feeder loading deserves review under "
                "current assumptions."
            ),
            detail=(
                "Review Grid & Capacity for transformer, feeder, and PQ "
                "diagnostics."
            ),
        )

    return _grid_asset_status_block(
        title="No grid caution",
        summary=(
            "No modeled transformer or feeder caution is indicated under "
            "current assumptions."
        ),
        detail=(
            "Review Grid & Capacity if transformer, feeder, or PQ diagnostics "
            "are needed."
        ),
    )

def render_feeder_summary_section(metrics: Metrics) -> Any:
    """Render a feeder-status summary with conditional detail."""
    if not metrics.feeder_summary_rows:
        return DEFAULT_GRID_LOADING_MESSAGE

    if metrics.overloaded_feeder_count > 0:
        section_title = "Feeder bottleneck indicated"
    elif metrics.feeder_loading_distribution_label.lower() == "balanced":
        section_title = "Balanced feeder loading"
    elif metrics.feeder_loading_distribution_label.lower() == "uneven":
        section_title = "Uneven feeder loading"
    else:
        section_title = "Feeder loading review"

    return html.Div(
        [
            html.Div(
                [
                    html.P(
                        html.Strong(section_title),
                        style={"margin": "0 0 0.45rem 0"},
                    ),
                    html.P(
                        metrics.feeder_status_message,
                        style={"margin": "0"},
                    ),
                    _status_metric_rows(
                        [
                            (
                                "Most loaded feeder",
                                metrics.most_loaded_feeder_id or "N/A",
                            ),
                            (
                                "Loading spread",
                                format_percentage_points(
                                    metrics.peak_feeder_loading_spread_percentage_points
                                ),
                            ),
                            (
                                "Loading distribution",
                                metrics.feeder_loading_distribution_label,
                            ),
                            (
                                "Thermal risk",
                                format_thermal_risk_level(
                                    metrics.highest_feeder_thermal_risk_level
                                ),
                            ),
                        ]
                    ),
                ],
                style=STATUS_BLOCK_STYLE,
            )
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "0.75rem"},
    )

def build_connection_capacity_sensitivity_rows(
    sensitivity_rows: list[CapacityAlternativeMetrics],
) -> list[tuple[str, str, str, str, str]]:
    """Format completed connection-sizing rows for compact dashboard display."""
    ordered_rows = sorted(
        sensitivity_rows,
        key=lambda row: row.capacity_option_kw,
    )
    return [
        (
            format_power_kw(row.capacity_option_kw),
            format_power_kw(row.required_connection_capacity_kw),
            format_signed_power_kw(row.headroom_kw),
            format_connection_sizing_status(
                row.capacity_adequate_indicator
            ),
            format_hours(row.time_above_capacity_hours),
        )
        for row in ordered_rows
    ]

def render_connection_capacity_sensitivity_table(
    sensitivity_rows: list[CapacityAlternativeMetrics],
    *,
    configured_capacity_kw: float | None = None,
    recommended_capacity_kw: float | None = None,
) -> Any:
    """Render read-only connection-sizing rows in a compact table."""
    ordered_rows = sorted(
        sensitivity_rows,
        key=lambda row: row.capacity_option_kw,
    )
    return html.Div(
        html.Table(
            [
                html.Thead(
                    html.Tr(
                        [
                            html.Th("Connection capacity", style=TABLE_HEADER_CELL_STYLE),
                            html.Th("Required peak demand", style=TABLE_HEADER_CELL_STYLE),
                            html.Th("Headroom", style=TABLE_HEADER_CELL_STYLE),
                            html.Th("Status", style=TABLE_HEADER_CELL_STYLE),
                            html.Th("Time above capacity", style=TABLE_HEADER_CELL_STYLE),
                        ]
                    )
                ),
                html.Tbody(
                    [
                        _connection_capacity_sensitivity_row(
                            row,
                            configured_capacity_kw=configured_capacity_kw,
                            recommended_capacity_kw=recommended_capacity_kw,
                        )
                        for row in ordered_rows
                    ]
                ),
            ],
            style=TABLE_STYLE,
        ),
        className="grid-capacity-sensitivity-table-inner",
    )

def _connection_capacity_sensitivity_row(
    row: CapacityAlternativeMetrics,
    *,
    configured_capacity_kw: float | None,
    recommended_capacity_kw: float | None,
) -> Any:
    """Render one styled connection-capacity sensitivity row."""
    is_configured = _capacity_value_matches(
        row.capacity_option_kw,
        configured_capacity_kw,
    )
    is_recommended = _capacity_value_matches(
        row.capacity_option_kw,
        recommended_capacity_kw,
    )

    row_style = {"backgroundColor": SURFACE_BACKGROUND_COLOR}
    if is_recommended:
        row_style.update(
            {
                "backgroundColor": STATUS_GREEN_BACKGROUND,
                "boxShadow": f"inset 3px 0 0 {STATUS_GREEN}",
            }
        )
    elif is_configured:
        row_style.update(
            {
                "backgroundColor": STATUS_BLUE_BACKGROUND,
                "boxShadow": f"inset 3px 0 0 {ACCENT_BLUE}",
            }
        )

    badges: list[Any] = []
    if is_configured:
        badges.append(
            _capacity_row_badge(
                "Configured",
                background_color=STATUS_BLUE_BACKGROUND,
                text_color=ACCENT_BLUE,
                border_color=ACCENT_BLUE,
            )
        )
    if is_recommended:
        badges.append(
            _capacity_row_badge(
                "Recommended",
                background_color=STATUS_GREEN_BACKGROUND,
                text_color=STATUS_GREEN,
                border_color=STATUS_GREEN,
            )
        )

    first_cell_children: list[Any] = [
        html.Div(
            [
                html.Span(format_power_kw(row.capacity_option_kw)),
                *badges,
            ],
            style={
                "display": "inline-flex",
                "alignItems": "center",
                "gap": "0.4rem",
                "flexWrap": "nowrap",
                "whiteSpace": "nowrap",
            },
        )
    ]

    return html.Tr(
        [
            html.Td(first_cell_children, style=TABLE_CELL_STYLE),
            html.Td(
                format_power_kw(row.required_connection_capacity_kw),
                style=TABLE_CELL_STYLE,
            ),
            html.Td(format_signed_power_kw(row.headroom_kw), style=TABLE_CELL_STYLE),
            html.Td(
                format_connection_sizing_status(row.capacity_adequate_indicator),
                style=TABLE_CELL_STYLE,
            ),
            html.Td(
                format_hours(row.time_above_capacity_hours),
                style=TABLE_CELL_STYLE,
            ),
        ],
        style=row_style,
    )

def _capacity_row_badge(
    label: str,
    *,
    background_color: str,
    text_color: str,
    border_color: str,
) -> Any:
    """Return one compact capacity-row badge."""
    return html.Span(
        label,
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "padding": "0.16rem 0.5rem",
            "borderRadius": "999px",
            "border": f"1px solid {border_color}",
            "backgroundColor": background_color,
            "color": text_color,
            "fontSize": "0.74rem",
            "fontWeight": "600",
            "lineHeight": "1.2",
        },
    )

def _capacity_value_matches(
    value: float,
    reference: float | None,
) -> bool:
    """Return whether one capacity value matches a reference capacity."""
    if reference is None:
        return False

    return math.isclose(value, reference, rel_tol=0.0, abs_tol=1e-6)

__all__ = [

    'render_infrastructure_summary',

    '_infrastructure_status_rows',

    '_infrastructure_status_is_adequate',

    '_format_infrastructure_decision_summary',

    '_format_infrastructure_constraint_diagnosis',

    '_format_infrastructure_planning_impact',

    '_format_infrastructure_planning_focus',

    'render_charger_planning_status',

    '_charger_planning_rule_is_met',

    '_charger_planning_has_tolerated_waiting',

    '_charger_planning_is_waiting_limited',

    '_charger_planning_status_data_is_available',

    '_charger_planning_status_block',

    '_status_metric_rows',

    '_grid_asset_status_block',

    'render_capacity_planning_kpi_cards',

    'render_charger_availability_kpi_cards',

    'render_grid_loading_kpi_cards',

    'render_grid_loading_status',

    'render_power_quality_kpi_cards',

    'render_power_quality_status',

    '_power_quality_status_data_is_available',

    '_power_quality_overlaps_with_grid_stress',

    'render_grid_asset_planning_status',

    'render_feeder_summary_section',

    'build_connection_capacity_sensitivity_rows',

    'render_connection_capacity_sensitivity_table',

    '_connection_capacity_sensitivity_row',

    '_capacity_row_badge',

    '_capacity_value_matches',

]

