from typing import Any

from dash import dcc, html
from scenarios import (
    create_active_scenario_state,
    create_scenario_comparison_snapshot,
    default_scenario,
    default_scenario_preset,
)


FONT_FAMILY_STACK = '"Segoe UI", Arial, sans-serif'
PAGE_BACKGROUND_COLOR = "#f4f6f8"
SURFACE_BACKGROUND_COLOR = "#ffffff"
SUBTLE_SURFACE_BACKGROUND_COLOR = "#f8fafc"
BORDER_COLOR = "#d8e0e8"
TEXT_PRIMARY_COLOR = "#17212b"
TEXT_SECONDARY_COLOR = "#5f6f82"
ACCENT_BLUE = "#1f6fb2"
STATUS_GREEN = "#2f7d4a"
STATUS_GREEN_BACKGROUND = "#edf7f1"
STATUS_AMBER = "#9a6a16"
STATUS_AMBER_BACKGROUND = "#fff7e6"
STATUS_RED = "#b63a3a"
STATUS_RED_BACKGROUND = "#fdf0ef"
STATUS_BLUE_BACKGROUND = "#eef5fb"
CHART_GRID_COLOR = "#dfe6ee"
SECTION_TITLE_STYLE = {
    "marginTop": "0",
    "marginBottom": "0.875rem",
    "color": TEXT_PRIMARY_COLOR,
    "fontSize": "1.2rem",
    "fontWeight": "600",
    "lineHeight": "1.3",
}
SUBSECTION_TITLE_STYLE = {
    "marginTop": "0",
    "marginBottom": "0.625rem",
    "color": TEXT_PRIMARY_COLOR,
    "fontSize": "1.05rem",
    "fontWeight": "600",
    "lineHeight": "1.35",
}
SECTION_LEAD_TEXT_STYLE = {
    "marginTop": "0",
    "marginBottom": "0.875rem",
    "color": TEXT_SECONDARY_COLOR,
    "fontSize": "1rem",
    "lineHeight": "1.55",
}
KPI_LABEL_TEXT_STYLE = {
    "color": TEXT_SECONDARY_COLOR,
    "fontSize": "1rem",
    "lineHeight": "1.4",
}
KPI_VALUE_TEXT_STYLE = {
    "color": TEXT_PRIMARY_COLOR,
    "fontSize": "clamp(1.7rem, 1.5rem + 0.7vw, 2.15rem)",
    "fontWeight": "700",
    "lineHeight": "1.15",
    "display": "block",
    "maxWidth": "100%",
    "minWidth": "0",
    "whiteSpace": "normal",
    "overflowWrap": "break-word",
}
SUPPORTING_TEXT_STYLE = {
    "color": TEXT_SECONDARY_COLOR,
    "fontSize": "0.95rem",
    "lineHeight": "1.45",
}
TABLE_STYLE = {
    "borderCollapse": "collapse",
    "width": "100%",
}
TABLE_HEADER_CELL_STYLE = {
    "padding": "0.75rem 0.875rem",
    "borderBottom": f"1px solid {BORDER_COLOR}",
    "color": TEXT_SECONDARY_COLOR,
    "fontSize": "0.8rem",
    "fontWeight": "600",
    "letterSpacing": "0.01em",
    "textAlign": "left",
    "verticalAlign": "middle",
    "backgroundColor": SUBTLE_SURFACE_BACKGROUND_COLOR,
}
TABLE_CELL_STYLE = {
    "padding": "0.8rem 0.875rem",
    "borderBottom": f"1px solid {BORDER_COLOR}",
    "color": TEXT_PRIMARY_COLOR,
    "fontSize": "0.875rem",
    "textAlign": "left",
    "verticalAlign": "top",
    "lineHeight": "1.45",
}
TABLE_EMPTY_CELL_STYLE = {
    **TABLE_CELL_STYLE,
    "color": TEXT_SECONDARY_COLOR,
    "fontStyle": "italic",
}
STATUS_BLOCK_STYLE = {
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "8px",
    "padding": "1rem 1.125rem",
    "backgroundColor": SUBTLE_SURFACE_BACKGROUND_COLOR,
}

SECTION_STYLE = {
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "8px",
    "padding": "1.375rem",
    "backgroundColor": SURFACE_BACKGROUND_COLOR,
    "marginBottom": "1rem",
}
DASHBOARD_WIDGET_SECTION_STYLE = {
    key: value for key, value in SECTION_STYLE.items() if key != "marginBottom"
}
SCENARIO_B_EDITOR_VISIBLE_STYLE = {
    "display": "block",
}
SCENARIO_B_EDITOR_HIDDEN_STYLE = {
    "display": "none",
}
SCENARIO_B_TEMPLATE_VISIBLE_STYLE = {
    "display": "block",
}
SCENARIO_B_TEMPLATE_HIDDEN_STYLE = {
    "display": "none",
}
COMPARISON_BUILDER_ACTION_VISIBLE_STYLE = {
    "display": "flex",
    "alignItems": "center",
    "flexWrap": "wrap",
    "gap": "0.75rem",
}
COMPARISON_BUILDER_ACTION_HIDDEN_STYLE = {
    "display": "none",
}
COMPARISON_LEAD_TEXT_STYLE = {
    "color": TEXT_SECONDARY_COLOR,
    "maxWidth": "60rem",
    "marginTop": "0.25rem",
    "marginBottom": "0",
    "fontSize": "0.875rem",
    "lineHeight": "1.55",
}
COMPARISON_EYEBROW_STYLE = {
    "color": ACCENT_BLUE,
    "fontSize": "0.75rem",
    "fontWeight": "600",
    "letterSpacing": "0.04em",
    "marginBottom": "0.45rem",
    "textTransform": "uppercase",
}
COMPARISON_CALLOUT_STYLE = {
    "backgroundColor": STATUS_BLUE_BACKGROUND,
    "border": f"1px solid {BORDER_COLOR}",
    "borderLeft": f"3px solid {ACCENT_BLUE}",
    "borderRadius": "8px",
    "padding": "1rem 1.125rem",
}

GRAPH_STYLE = {
    "height": "420px",
    "width": "100%",
    "minWidth": "0",
}
SMART_CHARGING_HERO_GRAPH_STYLE = {
    "height": "420px",
    "width": "100%",
    "minWidth": "0",
}
SMART_CHARGING_SUPPORTING_GRAPH_STYLE = {
    "height": "420px",
    "width": "100%",
    "minWidth": "0",
}
SMART_CHARGING_SECTION_STACK_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "1.125rem",
}
SMART_CHARGING_HERO_SECTION_STYLE = {
    **SECTION_STYLE,
    "padding": "1.5rem",
}
SMART_CHARGING_HERO_GRID_STYLE = {
    "marginBottom": "1rem",
}
SMART_CHARGING_HERO_BLOCK_STYLE = {
    "minWidth": "0",
}
SMART_CHARGING_ANALYSIS_SECTION_STYLE = {
    **SECTION_STYLE,
    "padding": "1.25rem 1.375rem",
}
SMART_CHARGING_SUBSECTION_STYLE = {
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "8px",
    "padding": "1.125rem 1.25rem",
    "backgroundColor": SURFACE_BACKGROUND_COLOR,
    "minWidth": "0",
    "overflow": "visible",
}
COMPACT_STATUS_MESSAGE_STYLE = {
    **STATUS_BLOCK_STYLE,
    "color": TEXT_SECONDARY_COLOR,
}
COMPACT_SUMMARY_CHIP_STYLE = {
    "display": "inline-flex",
    "alignItems": "center",
    "padding": "0.3rem 0.65rem",
    "borderRadius": "999px",
    "border": f"1px solid {BORDER_COLOR}",
    "backgroundColor": SURFACE_BACKGROUND_COLOR,
    "color": TEXT_SECONDARY_COLOR,
    "fontSize": "0.8rem",
    "fontWeight": "600",
}
COMPACT_SUMMARY_CHIP_ROW_STYLE = {
    "display": "flex",
    "flexWrap": "wrap",
    "gap": "0.5rem",
}
DISCLOSURE_SUMMARY_STYLE = {
    "cursor": "pointer",
    "color": ACCENT_BLUE,
    "fontWeight": "600",
}
SMART_CHARGING_SECTION_LEAD_STYLE = {
    "marginTop": SECTION_LEAD_TEXT_STYLE["marginTop"],
    "marginBottom": SECTION_LEAD_TEXT_STYLE["marginBottom"],
    "color": SECTION_LEAD_TEXT_STYLE["color"],
    "fontSize": SECTION_LEAD_TEXT_STYLE["fontSize"],
    "lineHeight": SECTION_LEAD_TEXT_STYLE["lineHeight"],
    "maxWidth": "60rem",
}
KPI_CARD_STYLE = {
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "8px",
    "padding": "1.125rem 1.25rem",
    "backgroundColor": SURFACE_BACKGROUND_COLOR,
    "display": "flex",
    "flexDirection": "column",
    "gap": "0.35rem",
    "minWidth": "0",
}
KPI_CARD_GRID_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "repeat(auto-fit, minmax(210px, 1fr))",
    "gap": "1rem",
}
DEFAULT_SCENARIO_COMPARISON_STATUS = (
    "Scenario B is ready. Changes here affect only the comparison scenario."
)
DEFAULT_SCENARIO_AB_SIMULATION_STATUS = (
    "Not run yet."
)
DEFAULT_SCENARIO_STATUS_MESSAGE = (
    "Run the simulation to generate an executive scenario summary."
)
DEFAULT_DETAILED_COMPARISON_MESSAGE = (
    "Run the simulation to review additional technical comparison details."
)
DEFAULT_CHARGING_PERFORMANCE_COMPARISON_TEXT = (
    "Run the simulation to compare charger occupancy, queueing, and waiting "
    "outcomes across charging strategies."
)
DEFAULT_POWER_QUALITY_COMPARISON_TEXT = (
    "Run the simulation to compare planner-facing power-quality indicators "
    "across charging strategies."
)
DEFAULT_SMART_CHARGING_TECHNICAL_DETAILS_TEXT = (
    "Run the simulation to review lower-priority diagnostic comparison metrics."
)
DEFAULT_CAPACITY_SENSITIVITY_MESSAGE = (
    "Run the simulation to explore connection-capacity alternatives."
)
DEFAULT_CAPACITY_SENSITIVITY_LOADING_MESSAGE = (
    "Loading connection-capacity alternatives..."
)
DEFAULT_GRID_LOADING_MESSAGE = (
    "Run the simulation to review modeled transformer and feeder loading "
    "against configured asset ratings and connection-capacity pressure."
)
DEFAULT_POWER_QUALITY_MESSAGE = (
    "Run the simulation to review modeled power quality indicators."
)
DEFAULT_GRID_ASSET_STATUS_MESSAGE = (
    "Run the simulation to review transformer and feeder asset status."
)
DEFAULT_SIMULATION_INSIGHTS_MESSAGE = (
    "Run the simulation to generate key findings."
)
LOADING_OVERLAY_STYLE = {
    "visibility": "visible",
    "backgroundColor": "rgba(244, 246, 248, 0.62)",
    "backdropFilter": "blur(1px)",
}
LOADING_INDICATOR_CONTAINER_STYLE = {
    "display": "inline-flex",
    "alignItems": "center",
    "gap": "0.75rem",
    "padding": "0.75rem 0.95rem",
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "999px",
    "backgroundColor": "rgba(255, 255, 255, 0.96)",
    "boxShadow": "0 10px 24px rgba(23, 33, 43, 0.08)",
    "color": TEXT_PRIMARY_COLOR,
}
LOADING_INDICATOR_MESSAGE_STYLE = {
    "fontSize": "0.9rem",
    "fontWeight": "600",
    "lineHeight": "1.4",
}
LOADING_WRAPPER_PARENT_STYLE = {
    "position": "relative",
    "width": "100%",
}


def _scenario_row(label: str, value: Any) -> Any:
    return html.Div(
        [
            html.Strong(label),
            html.Span(value),
        ],
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "gap": "1rem",
            "padding": "0.25rem 0",
        },
    )


def _placeholder_kpi_card(title: str, subtitle: str = "") -> Any:
    children = [html.Strong(title)]
    if subtitle:
        children.append(html.Span(subtitle, style=KPI_LABEL_TEXT_STYLE))
    children.append(html.Span("Not run yet", style=KPI_VALUE_TEXT_STYLE))

    return html.Div(children, style=KPI_CARD_STYLE)


def _compact_summary_chip(label: str) -> Any:
    return html.Span(label, style=COMPACT_SUMMARY_CHIP_STYLE)


def create_default_comparison_table_placeholder(
    message: str,
    *,
    delta_label: str = "Delta / Status",
) -> Any:
    """Return a compact placeholder table for comparison sections."""

    return html.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Metric", style=TABLE_HEADER_CELL_STYLE),
                        html.Th("Uncontrolled", style=TABLE_HEADER_CELL_STYLE),
                        html.Th("Smart", style=TABLE_HEADER_CELL_STYLE),
                        html.Th(delta_label, style=TABLE_HEADER_CELL_STYLE),
                    ]
                )
            ),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td(
                                message,
                                colSpan=4,
                                style={
                                    **TABLE_EMPTY_CELL_STYLE,
                                    "paddingLeft": "0",
                                    "paddingRight": "0",
                                },
                            )
                        ]
                    )
                ]
            ),
        ],
        style=TABLE_STYLE,
    )


def create_compact_status_message(message: str) -> Any:
    """Return a compact informational status message for disclosure states."""

    return html.Div(
        html.P(message, style={"margin": "0"}),
        style=COMPACT_STATUS_MESSAGE_STYLE,
    )


def build_loading_wrapper(
    child: Any,
    *,
    message: str,
    target_components: dict[str, Any],
    component_id: str | None = None,
    parent_style: dict[str, Any] | None = None,
) -> Any:
    """Wrap one dashboard output in a consistent loading overlay."""

    return dcc.Loading(
        child,
        id=component_id,
        delay_hide=150,
        delay_show=150,
        show_initially=False,
        overlay_style=LOADING_OVERLAY_STYLE,
        parent_style={
            **LOADING_WRAPPER_PARENT_STYLE,
            **(parent_style or {}),
        },
        custom_spinner=html.Div(
            [
                html.Span(className="dashboard-loading-indicator__spinner"),
                html.Span(message, style=LOADING_INDICATOR_MESSAGE_STYLE),
            ],
            className="dashboard-loading-indicator",
            style=LOADING_INDICATOR_CONTAINER_STYLE,
        ),
        target_components=target_components,
    )


def build_tab_panel(children: list[Any]) -> Any:
    """Wrap one dashboard tab's sections in a consistent panel container."""

    return html.Div(children, className="dashboard-tab-panel")


def build_dashboard_header() -> Any:
    """Return the shared dashboard header shown above the tab container."""

    return html.Section(
        [
            html.H1("EV Charging Demonstrator", className="dashboard-title"),
            html.P(
                "A scenario-based decision support demonstrator for "
                "exploring EV charging infrastructure and smart charging "
                "strategies.",
                className="dashboard-subtitle",
            ),
        ],
        className="dashboard-header",
        style={
            "marginBottom": "1.5rem",
        },
    )


def build_scenario_preset_overview(preset) -> Any:
    """Return a compact preset summary without parameter duplication."""

    overview_sentences = [preset.purpose]
    if preset.key_assumptions:
        overview_sentences.append(preset.key_assumptions[0])
    overview_text = " ".join(overview_sentences[:2])

    return [
        html.P(
            overview_text,
            style={
                "marginTop": "0.5rem",
                "marginBottom": "0",
                **SECTION_LEAD_TEXT_STYLE,
            },
        ),
    ]


def build_compact_scenario_preset_details(preset) -> Any:
    """Return compact, disclosure-first content for one comparison template."""

    return [
        html.P(
            preset.purpose,
            style={
                **SECTION_LEAD_TEXT_STYLE,
                "marginBottom": "0.6rem",
            },
        ),
        html.Div(
            [
                _compact_summary_chip(
                    f"{len(preset.key_assumptions)} key assumptions"
                ),
                _compact_summary_chip(
                    f"{len(preset.default_parameters)} default parameters"
                ),
            ],
            style=COMPACT_SUMMARY_CHIP_ROW_STYLE,
        ),
        html.Details(
            [
                html.Summary("View details", style=DISCLOSURE_SUMMARY_STYLE),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Strong("Key assumptions"),
                                html.Ul(
                                    [
                                        html.Li(assumption)
                                        for assumption in preset.key_assumptions
                                    ],
                                    style={
                                        "marginTop": "0.5rem",
                                        "marginBottom": "0",
                                        "paddingLeft": "1.1rem",
                                    },
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Strong("Default parameters"),
                                html.Div(
                                    [
                                        _scenario_row(label, value)
                                        for label, value in preset.default_parameters
                                    ],
                                    style={"marginTop": "0.5rem"},
                                ),
                            ],
                            style={"marginTop": "0.85rem"},
                        ),
                    ],
                    style={"marginTop": "0.6rem"},
                ),
            ],
            style={"marginTop": "0.6rem"},
        ),
    ]


def build_initial_active_scenario_store_data() -> dict[str, Any]:
    """Return the initial single-source-of-truth active scenario state."""

    return create_active_scenario_state(
        default_scenario_preset.preset_id,
        default_scenario,
    )


def build_initial_scenario_builder_store_data() -> dict[str, Any]:
    """Return the initial editable scenario-builder draft state."""

    return build_initial_active_scenario_store_data()


def build_initial_scenario_comparison_store_data() -> dict[str, Any]:
    """Return the initial Scenario A/B comparison state for Modified copy."""

    return create_scenario_comparison_snapshot(default_scenario)


def create_default_capacity_planning_cards() -> list[Any]:
    """Return the initial placeholder capacity-planning KPI cards."""

    return [
        _placeholder_kpi_card("Simulated Peak Load"),
        _placeholder_kpi_card("Required Connection Capacity"),
        _placeholder_kpi_card("Recommended Connection Capacity"),
        _placeholder_kpi_card("Peak Capacity Margin"),
    ]


def create_default_charger_availability_cards() -> list[Any]:
    """Return the initial placeholder charger-availability KPI cards."""

    return [
        _placeholder_kpi_card("Peak Charger Utilization"),
        _placeholder_kpi_card("Peak Occupied Chargers"),
        _placeholder_kpi_card("Maximum Queue Length"),
        _placeholder_kpi_card("Vehicles Not Started"),
    ]


def create_default_comparison_summary_cards() -> list[Any]:
    """Return the initial placeholder uncontrolled-vs-smart summary cards."""

    return [
        _placeholder_kpi_card(
            "Peak Load",
            "Uncontrolled - Smart",
        ),
        _placeholder_kpi_card(
            "Required Connection Capacity",
            "Uncontrolled - Smart",
        ),
        _placeholder_kpi_card(
            "Peak Transformer Loading",
            "Uncontrolled - Smart",
        ),
        _placeholder_kpi_card(
            "Service Impact",
            "Prepared planner-facing summary",
        ),
        _placeholder_kpi_card(
            "Power Quality Impact",
            "Prepared planner-facing summary",
        ),
        _placeholder_kpi_card(
            "Grid / Infrastructure Status",
            "Prepared planner-facing summary",
        ),
    ]


def create_default_grid_loading_cards() -> list[Any]:
    """Return the initial placeholder grid-loading KPI cards."""

    return [
        _placeholder_kpi_card(
            "Peak Transformer Loading",
            "Highest modeled loading",
        ),
        _placeholder_kpi_card(
            "Transformer Overload Duration",
            "Timesteps above transformer rating",
        ),
        _placeholder_kpi_card(
            "Maximum Transformer Overload",
            "Peak amount above transformer rating",
        ),
        _placeholder_kpi_card(
            "Maximum Feeder Loading",
            "Highest modeled feeder peak",
        ),
        _placeholder_kpi_card(
            "Overloaded Feeders",
            "Count of feeders above rating",
        ),
    ]


def create_default_power_quality_cards() -> list[Any]:
    """Return the initial placeholder power-quality KPI cards."""

    return [
        _placeholder_kpi_card(
            "Overall PQ Risk",
            "",
        ),
        _placeholder_kpi_card(
            "PQ Warnings",
            "",
        ),
        _placeholder_kpi_card(
            "Peak Harmonic Risk",
            "",
        ),
        _placeholder_kpi_card(
            "Harmonic Risk Duration",
            "",
        ),
        _placeholder_kpi_card(
            "Peak Current Imbalance",
            "",
        ),
        _placeholder_kpi_card(
            "Current Imbalance Duration",
            "",
        ),
    ]


def create_default_charger_planning_status_children() -> list[Any]:
    """Return the initial charger-planning placeholder content."""

    return [
        html.Strong("Run the simulation to generate a charger-planning recommendation."),
        html.P(
            "This summary explains whether current chargers are sufficient, "
            "whether brief waiting remains acceptable for sizing, or whether "
            "a different infrastructure constraint should be reviewed."
        ),
    ]


def create_default_power_quality_status_children() -> list[Any]:
    """Return the initial compact power-quality supplemental status content."""

    return []


def create_default_grid_asset_status_children() -> list[Any]:
    """Return the initial placeholder grid-asset status content."""

    return [
        html.Strong("Run the simulation to generate a grid caution summary."),
        html.P(
            "Only the high-level planning signal stays on Infrastructure. "
            "Use Grid & Capacity for transformer, feeder, and PQ detail."
        ),
    ]


def create_default_infrastructure_summary_children() -> list[Any]:
    """Return the initial infrastructure-summary placeholder content."""

    return [
        html.Strong("Run the simulation to generate an infrastructure status."),
        html.Ul(
            [
                html.Li(
                    "Decision Summary: the infrastructure decision outcome "
                    "for the modeled service rule."
                ),
                html.Li(
                    "Constraint Diagnosis: the dominant modeled planning "
                    "constraint."
                ),
                html.Li(
                    "Planning Impact: what the result means for planning "
                    "pressure or service risk."
                ),
                html.Li(
                    "Recommended Planning Focus: the next planning area to "
                    "review."
                ),
            ],
            style={"marginBottom": "0"},
        ),
    ]


def create_default_simulation_insights_list() -> list[Any]:
    """Return the initial placeholder insights list content."""

    return [html.Li(DEFAULT_SIMULATION_INSIGHTS_MESSAGE)]


def create_default_changed_assumptions_children() -> list[Any]:
    """Return the initial changed-assumptions placeholder content."""

    return [
        html.Div(
            [
                html.Strong("No comparison changes yet."),
                html.Span(
                    "Update Scenario B to preview the key differences.",
                    style={
                        "color": TEXT_SECONDARY_COLOR,
                    },
                ),
            ],
            className="scenario-comparison-assumptions-inline",
        )
    ]


def create_default_scenario_ab_executive_summary_cards(
    scenario_a_label: str = "Current scenario",
    scenario_b_label: str = "Comparison scenario",
) -> list[Any]:
    """Return the initial Scenario A/B executive-summary placeholder cards."""

    return [
        _placeholder_kpi_card(
            "Peak Load",
            "Shows how much connection-capacity and infrastructure pressure the scenario creates.",
        ),
        _placeholder_kpi_card(
            "Capacity Utilization",
            "Shows how intensely the configured charging capacity is used at the modeled peak.",
        ),
        _placeholder_kpi_card(
            "Unmet Energy",
            "Shows how much charging demand the modeled infrastructure still fails to serve.",
        ),
        _placeholder_kpi_card(
            "Maximum Queue Length",
            "Indicates how much user waiting pressure builds up at the busiest point.",
        ),
        _placeholder_kpi_card(
            "Peak Transformer Loading",
            "Highlights how close the site comes to stressing the transformer rating.",
        ),
        _placeholder_kpi_card(
            "Overall PQ Risk",
            "Summarizes the modeled power-quality risk level across the charging profile.",
        ),
    ]


def create_default_scenario_comparison_empty_state_children() -> list[Any]:
    """Return the initial comparison-tab empty-state guidance."""

    return [
        html.P(
            "Results appear below after you run the comparison.",
            style={
                "margin": "0",
                **SECTION_LEAD_TEXT_STYLE,
            },
        ),
    ]
