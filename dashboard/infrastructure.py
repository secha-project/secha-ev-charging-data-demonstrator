from typing import Any

from dash import dcc, html

from .common import (
    DASHBOARD_WIDGET_SECTION_STYLE,
    KPI_CARD_GRID_STYLE,
    build_loading_wrapper,
    create_default_capacity_planning_cards,
    create_default_charger_availability_cards,
    create_default_infrastructure_summary_children,
    build_tab_panel,
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


INFRASTRUCTURE_PRIMARY_REGION_SPEC = DashboardRegionSpec(
    region_id="infrastructure_primary",
    columns=DashboardRegionColumns(mobile=1, tablet=1, desktop=2),
)
INFRASTRUCTURE_SECONDARY_REGION_SPEC = DashboardRegionSpec(
    region_id="infrastructure_secondary",
    columns=DashboardRegionColumns(mobile=1, tablet=1, desktop=2),
)

INFRASTRUCTURE_SUMMARY_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="infrastructure-summary-section",
    region=INFRASTRUCTURE_SECONDARY_REGION_SPEC.region_id,
    priority=10,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=5),
    height_hint=DashboardWidgetHeightHint.STANDARD,
    mode_hint=DashboardWidgetMode.STATUS,
)
INFRASTRUCTURE_CAPACITY_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="infrastructure-capacity-planning-section",
    region=INFRASTRUCTURE_PRIMARY_REGION_SPEC.region_id,
    priority=20,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=6),
    height_hint=DashboardWidgetHeightHint.STANDARD,
    mode_hint=DashboardWidgetMode.SUMMARY,
)
INFRASTRUCTURE_CHARGER_AVAILABILITY_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="infrastructure-charger-availability-section",
    region=INFRASTRUCTURE_PRIMARY_REGION_SPEC.region_id,
    priority=30,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=6),
    height_hint=DashboardWidgetHeightHint.STANDARD,
    mode_hint=DashboardWidgetMode.SUMMARY,
)
INFRASTRUCTURE_SERVICE_PRESSURE_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="infrastructure-service-pressure-section",
    region=INFRASTRUCTURE_SECONDARY_REGION_SPEC.region_id,
    priority=20,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=7),
    height_hint=DashboardWidgetHeightHint.STANDARD,
    mode_hint=DashboardWidgetMode.CHART,
)
INFRASTRUCTURE_KPI_GRID_STYLE = {
    **KPI_CARD_GRID_STYLE,
    "gridTemplateColumns": "repeat(2, minmax(0, 1fr))",
    "gridAutoRows": "1fr",
    "gap": "0.75rem",
}
INFRASTRUCTURE_SERVICE_PRESSURE_GRAPH_STYLE = {
    "height": "360px",
    "width": "100%",
    "minWidth": "0",
}


def _build_infrastructure_primary_region() -> Any:
    """Return the primary Infrastructure region using shared widget shells."""

    return build_dashboard_region_grid(
        INFRASTRUCTURE_PRIMARY_REGION_SPEC,
        [
            DashboardWidgetPlacement(
                spec=INFRASTRUCTURE_CAPACITY_WIDGET_SPEC,
                component_id="infrastructure-capacity-planning-section",
                style=DASHBOARD_WIDGET_SECTION_STYLE,
                children=[
                    html.H2("Connection Capacity Planning"),
                    build_loading_wrapper(
                        html.Div(
                            create_default_capacity_planning_cards(),
                            id="capacity-planning-kpi-cards",
                            className="infrastructure-kpi-grid",
                            style=INFRASTRUCTURE_KPI_GRID_STYLE,
                        ),
                        component_id="capacity-planning-kpi-cards-loading",
                        message="Loading results...",
                        target_components={
                            "capacity-planning-kpi-cards": "children",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
            ),
            DashboardWidgetPlacement(
                spec=INFRASTRUCTURE_CHARGER_AVAILABILITY_WIDGET_SPEC,
                component_id="infrastructure-charger-availability-section",
                style=DASHBOARD_WIDGET_SECTION_STYLE,
                children=[
                    html.H2("Charger Availability"),
                    build_loading_wrapper(
                        html.Div(
                            create_default_charger_availability_cards(),
                            id="charger-availability-kpi-cards",
                            className="infrastructure-kpi-grid",
                            style=INFRASTRUCTURE_KPI_GRID_STYLE,
                        ),
                        component_id="charger-availability-kpi-cards-loading",
                        message="Loading results...",
                        target_components={
                            "charger-availability-kpi-cards": "children",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
            ),
        ],
        component_id="infrastructure-primary-region",
        style={"marginBottom": "1rem"},
    )


def _build_infrastructure_secondary_region() -> Any:
    """Return the secondary Infrastructure region using shared widget shells."""

    return build_dashboard_region_grid(
        INFRASTRUCTURE_SECONDARY_REGION_SPEC,
        [
            DashboardWidgetPlacement(
                spec=INFRASTRUCTURE_SUMMARY_WIDGET_SPEC,
                component_id="infrastructure-summary-section",
                style=DASHBOARD_WIDGET_SECTION_STYLE,
                children=[
                    html.H2("Infrastructure Status"),
                    build_loading_wrapper(
                        html.Div(
                            create_default_infrastructure_summary_children(),
                            id="infrastructure-summary",
                        ),
                        component_id="infrastructure-summary-loading",
                        message="Loading results...",
                        target_components={
                            "infrastructure-summary": "children",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
            ),
            DashboardWidgetPlacement(
                spec=INFRASTRUCTURE_SERVICE_PRESSURE_WIDGET_SPEC,
                component_id="infrastructure-service-pressure-section",
                style=DASHBOARD_WIDGET_SECTION_STYLE,
                children=[
                    html.H2("Charger Pressure During Charging Window"),
                    build_loading_wrapper(
                        dcc.Graph(
                            id="service-pressure-chart",
                            figure={},
                            config={"responsive": True},
                            style=INFRASTRUCTURE_SERVICE_PRESSURE_GRAPH_STYLE,
                        ),
                        component_id="service-pressure-chart-loading",
                        message="Preparing visualizations...",
                        target_components={
                            "service-pressure-chart": "figure",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
            )
        ],
        component_id="infrastructure-secondary-region",
        style={"marginBottom": "1rem"},
    )


def build_infrastructure_tab() -> Any:
    """Return the Infrastructure tab layout."""

    return build_tab_panel(
        [
            _build_infrastructure_primary_region(),
            _build_infrastructure_secondary_region(),
        ]
    )
