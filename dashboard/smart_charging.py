from typing import Any

from dash import dcc, html

from .common import (
    DEFAULT_DETAILED_COMPARISON_MESSAGE,
    DEFAULT_SMART_CHARGING_TECHNICAL_DETAILS_TEXT,
    KPI_CARD_GRID_STYLE,
    SMART_CHARGING_ANALYSIS_SECTION_STYLE,
    SMART_CHARGING_HERO_BLOCK_STYLE,
    SMART_CHARGING_HERO_GRAPH_STYLE,
    SMART_CHARGING_HERO_GRID_STYLE,
    SMART_CHARGING_HERO_SECTION_STYLE,
    SMART_CHARGING_SECTION_LEAD_STYLE,
    SMART_CHARGING_SECTION_STACK_STYLE,
    SMART_CHARGING_SUBSECTION_STYLE,
    SMART_CHARGING_SUPPORTING_GRAPH_STYLE,
    build_tab_panel,
    build_loading_wrapper,
    create_compact_status_message,
    create_default_comparison_summary_cards,
    create_default_comparison_table_placeholder,
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


SMART_CHARGING_HERO_REGION_SPEC = DashboardRegionSpec(
    region_id="smart_charging_hero",
    columns=DashboardRegionColumns(mobile=1, tablet=1, desktop=1),
)
SMART_CHARGING_MAIN_ANALYSIS_REGION_SPEC = DashboardRegionSpec(
    region_id="smart_charging_main_analysis",
    columns=DashboardRegionColumns(mobile=1, tablet=1, desktop=2),
)
SMART_CHARGING_PERFORMANCE_REGION_SPEC = DashboardRegionSpec(
    region_id="smart_charging_performance",
    columns=DashboardRegionColumns(mobile=1, tablet=1, desktop=2),
)
SMART_CHARGING_TECHNICAL_DETAILS_REGION_SPEC = DashboardRegionSpec(
    region_id="smart_charging_technical_details",
    columns=DashboardRegionColumns(mobile=1, tablet=1, desktop=1),
)

SMART_CHARGING_HERO_SUMMARY_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="smart-charging-hero-summary",
    region=SMART_CHARGING_HERO_REGION_SPEC.region_id,
    priority=10,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=12),
    height_hint=DashboardWidgetHeightHint.COMPACT,
    mode_hint=DashboardWidgetMode.SUMMARY,
)
SMART_CHARGING_HERO_CHART_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="smart-charging-hero-chart",
    region=SMART_CHARGING_MAIN_ANALYSIS_REGION_SPEC.region_id,
    priority=10,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=8),
    height_hint=DashboardWidgetHeightHint.TALL,
    mode_hint=DashboardWidgetMode.HERO,
)
SMART_CHARGING_POWER_QUALITY_CHART_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="strategy-comparison-pq-risk-block",
    region=SMART_CHARGING_MAIN_ANALYSIS_REGION_SPEC.region_id,
    priority=20,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=4),
    mode_hint=DashboardWidgetMode.CHART,
    height_hint=DashboardWidgetHeightHint.TALL,
)
SMART_CHARGING_OCCUPANCY_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="strategy-comparison-occupancy-block",
    region=SMART_CHARGING_PERFORMANCE_REGION_SPEC.region_id,
    priority=10,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=6),
    height_hint=DashboardWidgetHeightHint.TALL,
    mode_hint=DashboardWidgetMode.CHART,
)
SMART_CHARGING_QUEUE_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="strategy-comparison-queue-block",
    region=SMART_CHARGING_PERFORMANCE_REGION_SPEC.region_id,
    priority=20,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=6),
    height_hint=DashboardWidgetHeightHint.TALL,
    mode_hint=DashboardWidgetMode.CHART,
)
SMART_CHARGING_TECHNICAL_DETAILS_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="detailed-comparison-table",
    region=SMART_CHARGING_TECHNICAL_DETAILS_REGION_SPEC.region_id,
    priority=10,
    mode_hint=DashboardWidgetMode.DETAIL,
)


def _render_smart_charging_region(
    region_spec: DashboardRegionSpec,
    placements: list[DashboardWidgetPlacement],
    *,
    class_name: str | None = None,
    style: dict[str, Any] | None = None,
    component_id: str | None = None,
) -> Any:
    """Render one Smart Charging widget region from descriptor placements."""

    return build_dashboard_region_grid(
        region_spec,
        placements,
        component_id=component_id,
        class_name=class_name,
        style=style,
    )


def _build_hero_region() -> Any:
    """Return the Smart Charging executive KPI row."""

    return _render_smart_charging_region(
        SMART_CHARGING_HERO_REGION_SPEC,
        [
            DashboardWidgetPlacement(
                spec=SMART_CHARGING_HERO_SUMMARY_WIDGET_SPEC,
                component_id="smart-charging-hero-summary",
                class_name="smart-charging-hero-block",
                style=SMART_CHARGING_HERO_BLOCK_STYLE,
                children=[
                    html.H2("Smart Charging Executive KPIs"),
                    html.P(
                        (
                            "Baseline: Uncontrolled Charging. Comparison: "
                            "Smart Charging."
                        ),
                        className="smart-charging-section-lead",
                        style=SMART_CHARGING_SECTION_LEAD_STYLE,
                    ),
                    build_loading_wrapper(
                        html.Div(
                            create_default_comparison_summary_cards(),
                            id="smart-charging-comparison-summary-cards",
                            style=KPI_CARD_GRID_STYLE,
                        ),
                        component_id="smart-charging-summary-cards-loading",
                        message="Loading results...",
                        target_components={
                            "smart-charging-comparison-summary-cards": "children",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
            ),
        ],
        class_name="smart-charging-hero-grid",
        style=SMART_CHARGING_HERO_GRID_STYLE,
        component_id="smart-charging-hero-region",
    )


def _build_main_analysis_region() -> Any:
    """Return the top Smart Charging analysis row."""

    return _render_smart_charging_region(
        SMART_CHARGING_MAIN_ANALYSIS_REGION_SPEC,
        [
            DashboardWidgetPlacement(
                spec=SMART_CHARGING_HERO_CHART_WIDGET_SPEC,
                component_id="smart-charging-hero-chart",
                class_name="smart-charging-hero-block",
                style={
                    **SMART_CHARGING_SUBSECTION_STYLE,
                    **SMART_CHARGING_HERO_BLOCK_STYLE,
                    **SMART_CHARGING_SECTION_STACK_STYLE,
                },
                children=[
                    html.H2("Charging Strategy Comparison"),
                    build_loading_wrapper(
                        dcc.Graph(
                            id="strategy-comparison-load-profile-chart",
                            figure={},
                            config={"responsive": True},
                            style=SMART_CHARGING_HERO_GRAPH_STYLE,
                        ),
                        component_id="strategy-comparison-load-profile-chart-loading",
                        message="Preparing visualizations...",
                        target_components={
                            "strategy-comparison-load-profile-chart": "figure",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
            ),
            DashboardWidgetPlacement(
                spec=SMART_CHARGING_POWER_QUALITY_CHART_WIDGET_SPEC,
                component_id="strategy-comparison-pq-risk-block",
                children=[
                    html.H2("Overall PQ Risk Over Time"),
                    build_loading_wrapper(
                        dcc.Graph(
                            id="strategy-comparison-pq-risk-chart",
                            figure={},
                            config={"responsive": True},
                            style=SMART_CHARGING_SUPPORTING_GRAPH_STYLE,
                        ),
                        component_id="strategy-comparison-pq-risk-chart-loading",
                        message="Preparing visualizations...",
                        target_components={
                            "strategy-comparison-pq-risk-chart": "figure",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
                style={
                    **SMART_CHARGING_SUBSECTION_STYLE,
                    **SMART_CHARGING_SECTION_STACK_STYLE,
                },
            ),
        ],
        component_id="smart-charging-main-analysis-region",
    )


def _build_charging_performance_region() -> Any:
    """Return the shared region for Charging Performance content."""

    return _render_smart_charging_region(
        SMART_CHARGING_PERFORMANCE_REGION_SPEC,
        [
            DashboardWidgetPlacement(
                spec=SMART_CHARGING_OCCUPANCY_WIDGET_SPEC,
                component_id="strategy-comparison-occupancy-block",
                children=[
                    html.H3("Occupied Chargers Over Time"),
                    build_loading_wrapper(
                        dcc.Graph(
                            id="strategy-comparison-occupancy-chart",
                            figure={},
                            config={"responsive": True},
                            style=SMART_CHARGING_SUPPORTING_GRAPH_STYLE,
                        ),
                        component_id="strategy-comparison-occupancy-chart-loading",
                        message="Preparing visualizations...",
                        target_components={
                            "strategy-comparison-occupancy-chart": "figure",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
                style={
                    **SMART_CHARGING_SUBSECTION_STYLE,
                    **SMART_CHARGING_SECTION_STACK_STYLE,
                },
            ),
            DashboardWidgetPlacement(
                spec=SMART_CHARGING_QUEUE_WIDGET_SPEC,
                component_id="strategy-comparison-queue-block",
                children=[
                    html.H3("Queue Length Over Time"),
                    build_loading_wrapper(
                        html.Div(
                            [
                                html.Div(
                                    dcc.Graph(
                                        id="strategy-comparison-queue-chart",
                                        figure={},
                                        config={"responsive": True},
                                        style=SMART_CHARGING_SUPPORTING_GRAPH_STYLE,
                                    ),
                                    id="strategy-comparison-queue-chart-container",
                                ),
                                html.Div(
                                    id="strategy-comparison-queue-status",
                                    children=create_compact_status_message(
                                        "No queues formed during the simulation."
                                    ),
                                    style={"display": "none"},
                                ),
                            ]
                        ),
                        component_id="strategy-comparison-queue-section-loading",
                        message="Preparing visualizations...",
                        target_components={
                            "strategy-comparison-queue-chart": "figure",
                            "strategy-comparison-queue-chart-container": "style",
                            "strategy-comparison-queue-status": "children",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
                style={
                    **SMART_CHARGING_SUBSECTION_STYLE,
                    **SMART_CHARGING_SECTION_STACK_STYLE,
                },
            ),
        ],
        component_id="smart-charging-performance-region",
    )


def _build_technical_details_region() -> Any:
    """Return the shared region for Technical Details content."""

    return _render_smart_charging_region(
        SMART_CHARGING_TECHNICAL_DETAILS_REGION_SPEC,
        [
            DashboardWidgetPlacement(
                spec=SMART_CHARGING_TECHNICAL_DETAILS_WIDGET_SPEC,
                component_id="detailed-comparison-table-section",
                children=[
                    build_loading_wrapper(
                        html.Div(
                            create_default_comparison_table_placeholder(
                                DEFAULT_DETAILED_COMPARISON_MESSAGE
                            ),
                            id="detailed-comparison-table",
                        ),
                        component_id="detailed-comparison-table-loading",
                        message="Loading results...",
                        target_components={
                            "detailed-comparison-table": "children",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
                style=SMART_CHARGING_SUBSECTION_STYLE,
            )
        ],
        component_id="smart-charging-technical-details-region",
    )


def _build_hidden_smart_charging_callback_targets() -> Any:
    """Keep presentation-removed callback outputs mounted but invisible."""

    return html.Div(
        [
            html.Div(id="charging-performance-comparison-table"),
            html.Div(
                id="power-quality-comparison-status",
                className="dashboard-widget",
                style={"display": "none"},
            ),
            html.Div(id="power-quality-comparison-table"),
        ],
        style={"display": "none"},
    )


def build_smart_charging_tab() -> Any:
    """Return the Smart Charging tab layout."""

    return build_tab_panel(
        [
            html.Section(
                [
                    _build_hero_region(),
                ],
                id="smart-charging-hero-section",
                className="smart-charging-hero-section",
                style=SMART_CHARGING_HERO_SECTION_STYLE,
            ),
            html.Section(
                [
                    _build_main_analysis_region(),
                ],
                id="smart-charging-main-analysis-section",
                className="smart-charging-analysis-section",
                style={
                    "marginBottom": "1rem",
                    "padding": "0",
                    "border": "none",
                    "background": "transparent",
                },
            ),
            html.Section(
                [
                    html.H2("Charging Performance"),
                    _build_charging_performance_region(),
                ],
                id="smart-charging-performance-section",
                className="smart-charging-analysis-section",
                style=SMART_CHARGING_ANALYSIS_SECTION_STYLE,
            ),
            html.Section(
                [
                    html.Details(
                        [
                            html.Summary(
                                "Technical Details",
                                style={
                                    "cursor": "pointer",
                                    "fontWeight": "bold",
                                },
                            ),
                            html.Div(
                                [
                                    html.P(
                                        (
                                            f"{DEFAULT_SMART_CHARGING_TECHNICAL_DETAILS_TEXT} "
                                            "Detailed overload, queueing, capacity, "
                                            "and PQ diagnostics remain available here."
                                        ),
                                        className="smart-charging-section-lead",
                                        style={
                                            **SMART_CHARGING_SECTION_LEAD_STYLE,
                                            "marginTop": "0.75rem",
                                        },
                                    ),
                                    _build_technical_details_region(),
                                ],
                                style={"marginTop": "0.5rem"},
                            ),
                        ]
                    ),
                ],
                id="smart-charging-technical-details-section",
                className="smart-charging-analysis-section smart-charging-technical-section",
                style=SMART_CHARGING_ANALYSIS_SECTION_STYLE,
            ),
            _build_hidden_smart_charging_callback_targets(),
        ]
    )
