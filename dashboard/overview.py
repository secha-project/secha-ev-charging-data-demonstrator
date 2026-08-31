from typing import Any

from dash import dcc, html

from .common import (
    ACCENT_BLUE,
    DASHBOARD_WIDGET_SECTION_STYLE,
    DEFAULT_SCENARIO_STATUS_MESSAGE,
    GRAPH_STYLE,
    KPI_LABEL_TEXT_STYLE,
    KPI_VALUE_TEXT_STYLE,
    KPI_CARD_GRID_STYLE,
    KPI_CARD_STYLE,
    build_tab_panel,
    build_loading_wrapper,
    create_default_simulation_insights_list,
)
from .layout_components import DashboardWidgetPlacement, build_dashboard_region_grid
from .layout_contract import (
    DashboardRegionColumns,
    DashboardRegionSpec,
    DashboardWidgetHeightHint,
    DashboardWidgetMode,
    DashboardWidgetSpec,
    DashboardWidgetSpan,
)


OVERVIEW_GRAPH_STYLE = {
    **GRAPH_STYLE,
    "height": "400px",
}

OVERVIEW_PRIMARY_REGION_SPEC = DashboardRegionSpec(
    region_id="overview_primary",
    columns=DashboardRegionColumns(mobile=1, tablet=1, desktop=1),
)
OVERVIEW_SECONDARY_REGION_SPEC = DashboardRegionSpec(
    region_id="overview_secondary",
    columns=DashboardRegionColumns(mobile=1, tablet=1, desktop=2),
)

OVERVIEW_KPI_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="overview-kpi-summary-section",
    region=OVERVIEW_PRIMARY_REGION_SPEC.region_id,
    priority=10,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=12),
    height_hint=DashboardWidgetHeightHint.STANDARD,
    mode_hint=DashboardWidgetMode.SUMMARY,
)
OVERVIEW_SMART_CHARGING_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="overview-smart-charging-impact-section",
    region=OVERVIEW_SECONDARY_REGION_SPEC.region_id,
    priority=10,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=5),
    height_hint=DashboardWidgetHeightHint.STANDARD,
    mode_hint=DashboardWidgetMode.SUMMARY,
)
OVERVIEW_CHART_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="overview-capacity-vs-load-section",
    region=OVERVIEW_SECONDARY_REGION_SPEC.region_id,
    priority=20,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=7),
    height_hint=DashboardWidgetHeightHint.TALL,
    mode_hint=DashboardWidgetMode.CHART,
)
OVERVIEW_SMART_CHARGING_PREVIEW_GRID_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "1.4rem",
    "width": "100%",
    "minWidth": "0",
}
OVERVIEW_SMART_CHARGING_ROW_STYLE = {
    "display": "grid",
    "gap": "0.5rem",
    "minWidth": "0",
}
OVERVIEW_SMART_CHARGING_BAR_TRACK_STYLE = {
    "width": "100%",
    "height": "0.7rem",
    "backgroundColor": "#dbe6ef",
    "borderRadius": "999px",
    "overflow": "hidden",
}
OVERVIEW_SMART_CHARGING_BAR_BASE_STYLE = {
    "height": "100%",
    "borderRadius": "999px",
}
OVERVIEW_SMART_CHARGING_BASELINE_BAR_STYLE = {
    **OVERVIEW_SMART_CHARGING_BAR_BASE_STYLE,
    "width": "100%",
    "backgroundColor": "#5d7287",
}
OVERVIEW_SMART_CHARGING_COMPARISON_BAR_STYLE = {
    **OVERVIEW_SMART_CHARGING_BAR_BASE_STYLE,
    "width": "72%",
    "backgroundColor": ACCENT_BLUE,
}


def _build_smart_charging_preview_row(
    label: str,
    value_text: str,
    bar_style: dict[str, Any],
) -> Any:
    """Return one compact Smart Charging preview row for the Overview tab."""

    return html.Div(
        [
            html.Strong(label, style={"lineHeight": "1.3"}),
            html.Span(
                value_text,
                style={
                    **KPI_LABEL_TEXT_STYLE,
                    "fontWeight": "600",
                    "color": "#17212b",
                },
            ),
            html.Div(
                html.Div(style=bar_style),
                style=OVERVIEW_SMART_CHARGING_BAR_TRACK_STYLE,
            ),
        ],
        style=OVERVIEW_SMART_CHARGING_ROW_STYLE,
    )


def _build_overview_placeholder_kpi_cards() -> list[Any]:
    """Return the initial four-card Overview KPI placeholder set."""

    return [
        _overview_kpi_card(
            "Scenario Outcome",
            "Not run yet",
            "Overall modeled scenario status",
        ),
        _overview_kpi_card(
            "Peak Load",
            "Not run yet",
            "Maximum charging demand",
        ),
        _overview_kpi_card(
            "Grid Connection Need",
            "Not run yet",
            "Planner-facing connection recommendation",
        ),
        _overview_kpi_card(
            "Charger Expansion Need",
            "Not run yet",
            "Required charger-count change",
        ),
    ]


def _overview_kpi_card(title: str, value_component: Any, subtitle: str) -> Any:
    """Return a compact KPI card for the executive overview row."""

    return html.Div(
        [
            html.Strong(title),
            html.Span(subtitle, style=KPI_LABEL_TEXT_STYLE),
            html.Span(value_component, style=KPI_VALUE_TEXT_STYLE),
        ],
        style=KPI_CARD_STYLE,
    )


def _build_overview_primary_region() -> Any:
    """Return the primary Overview region using shared widget shells."""

    return build_dashboard_region_grid(
        OVERVIEW_PRIMARY_REGION_SPEC,
        [
            DashboardWidgetPlacement(
                spec=OVERVIEW_KPI_WIDGET_SPEC,
                component_id="overview-kpi-summary-section",
                style=DASHBOARD_WIDGET_SECTION_STYLE,
                children=[
                    html.H2("Executive KPI Summary"),
                    build_loading_wrapper(
                        html.Div(
                            _build_overview_placeholder_kpi_cards(),
                            id="overview-kpi-cards",
                            className="overview-kpi-grid",
                            style=KPI_CARD_GRID_STYLE,
                        ),
                        component_id="overview-kpi-cards-loading",
                        message="Running simulation...",
                        target_components={
                            "overview-kpi-cards": "children",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
            ),
        ],
        component_id="overview-primary-region",
        style={"marginBottom": "1rem"},
    )


def _build_overview_secondary_region() -> Any:
    """Return the Overview evidence region with the two main visuals."""

    return build_dashboard_region_grid(
        OVERVIEW_SECONDARY_REGION_SPEC,
        [
            DashboardWidgetPlacement(
                spec=OVERVIEW_SMART_CHARGING_WIDGET_SPEC,
                component_id="overview-smart-charging-impact-section",
                style=DASHBOARD_WIDGET_SECTION_STYLE,
                children=[
                    html.H2("Smart Charging Impact"),
                    build_loading_wrapper(
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Span(
                                            "Peak Reduction",
                                            style=KPI_LABEL_TEXT_STYLE,
                                        ),
                                        html.Strong(
                                            "Not run yet",
                                            style={
                                                **KPI_VALUE_TEXT_STYLE,
                                                "fontSize": "1.65rem",
                                            },
                                        ),
                                    ],
                                    style={
                                        "display": "grid",
                                        "gap": "0.25rem",
                                    },
                                ),
                                html.Hr(
                                    style={
                                        "border": "0",
                                        "borderTop": "1px solid #d8e0e8",
                                        "margin": "0",
                                    }
                                ),
                                _build_smart_charging_preview_row(
                                    "Uncontrolled peak load",
                                    "Not run yet",
                                    OVERVIEW_SMART_CHARGING_BASELINE_BAR_STYLE,
                                ),
                                _build_smart_charging_preview_row(
                                    "Smart Charging peak load",
                                    "Not run yet",
                                    OVERVIEW_SMART_CHARGING_COMPARISON_BAR_STYLE,
                                ),
                            ],
                            id="overview-smart-charging-preview",
                            style=OVERVIEW_SMART_CHARGING_PREVIEW_GRID_STYLE,
                        ),
                        component_id="overview-smart-charging-preview-loading",
                        message="Loading results...",
                        target_components={
                            "overview-smart-charging-preview": "children",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
            ),
            DashboardWidgetPlacement(
                spec=OVERVIEW_CHART_WIDGET_SPEC,
                component_id="overview-capacity-vs-load-section",
                style=DASHBOARD_WIDGET_SECTION_STYLE,
                children=[
                    html.H2("Capacity vs Load"),
                    build_loading_wrapper(
                        dcc.Graph(
                            id="capacity-vs-load-chart",
                            figure={},
                            config={"responsive": True, "displayModeBar": False},
                            style=OVERVIEW_GRAPH_STYLE,
                        ),
                        component_id="capacity-vs-load-chart-loading",
                        message="Preparing visualizations...",
                        target_components={
                            "capacity-vs-load-chart": "figure",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
            ),
        ],
        component_id="overview-secondary-region",
        style={"marginBottom": "1rem"},
    )


def build_overview_tab() -> Any:
    """Return the summary-focused Overview tab layout."""

    return build_tab_panel(
        [
            _build_overview_primary_region(),
            _build_overview_secondary_region(),
            html.Div(
                [
                    html.Span("Not run yet", id="available-capacity-value"),
                    html.Span("Not run yet", id="peak-load-value"),
                    html.Span("Not run yet", id="capacity-utilization-value"),
                    html.Span("Not run yet", id="unmet-energy-value"),
                    html.Span("", id="total-daily-energy-value"),
                    html.Span("", id="delivered-energy-value"),
                    html.Span("", id="daily-charging-energy-value"),
                    html.Span("", id="annual-energy-value"),
                    html.Div(
                        DEFAULT_SCENARIO_STATUS_MESSAGE,
                        id="scenario-status-message",
                    ),
                    html.Ul(
                        create_default_simulation_insights_list(),
                        id="simulation-insights-list",
                    ),
                ],
                style={"display": "none"},
            ),
        ]
    )
