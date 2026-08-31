from typing import Any

from dash import dcc, html

from .common import (
    DASHBOARD_WIDGET_SECTION_STYLE,
    DEFAULT_CAPACITY_SENSITIVITY_MESSAGE,
    DEFAULT_GRID_LOADING_MESSAGE,
    GRAPH_STYLE,
    KPI_CARD_GRID_STYLE,
    build_tab_panel,
    build_loading_wrapper,
    create_default_grid_loading_cards,
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


GRID_CAPACITY_PRIMARY_REGION_SPEC = DashboardRegionSpec(
    region_id="grid_capacity_primary",
    columns=DashboardRegionColumns(mobile=1, tablet=1, desktop=1),
)
GRID_CAPACITY_SECONDARY_REGION_SPEC = DashboardRegionSpec(
    region_id="grid_capacity_secondary",
    columns=DashboardRegionColumns(mobile=1, tablet=1, desktop=2),
    allow_mixed_heights=False,
)
GRID_CAPACITY_TERTIARY_REGION_SPEC = DashboardRegionSpec(
    region_id="grid_capacity_tertiary",
    columns=DashboardRegionColumns(mobile=1, tablet=1, desktop=2),
)

GRID_CAPACITY_SUMMARY_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="grid-capacity-summary-section",
    region=GRID_CAPACITY_PRIMARY_REGION_SPEC.region_id,
    priority=10,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=12),
    height_hint=DashboardWidgetHeightHint.COMPACT,
    mode_hint=DashboardWidgetMode.SUMMARY,
)
GRID_CAPACITY_SENSITIVITY_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="grid-capacity-sensitivity-section",
    region=GRID_CAPACITY_SECONDARY_REGION_SPEC.region_id,
    priority=10,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=8),
    height_hint=DashboardWidgetHeightHint.STANDARD,
    mode_hint=DashboardWidgetMode.TABLE,
)
GRID_CAPACITY_TRANSFORMER_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="grid-capacity-transformer-section",
    region=GRID_CAPACITY_TERTIARY_REGION_SPEC.region_id,
    priority=10,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=6),
    height_hint=DashboardWidgetHeightHint.TALL,
    mode_hint=DashboardWidgetMode.CHART,
)
GRID_CAPACITY_POWER_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="grid-capacity-power-capacity-section",
    region=GRID_CAPACITY_TERTIARY_REGION_SPEC.region_id,
    priority=20,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=6),
    height_hint=DashboardWidgetHeightHint.TALL,
    mode_hint=DashboardWidgetMode.CHART,
)
GRID_CAPACITY_FEEDER_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="grid-capacity-feeder-section",
    region=GRID_CAPACITY_SECONDARY_REGION_SPEC.region_id,
    priority=20,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=4),
    height_hint=DashboardWidgetHeightHint.STANDARD,
    mode_hint=DashboardWidgetMode.DETAIL,
)


def _build_grid_capacity_primary_region() -> Any:
    """Return the KPI-first Grid & Capacity region."""

    return build_dashboard_region_grid(
        GRID_CAPACITY_PRIMARY_REGION_SPEC,
        [
            DashboardWidgetPlacement(
                spec=GRID_CAPACITY_SUMMARY_WIDGET_SPEC,
                component_id="grid-capacity-summary-section",
                style=DASHBOARD_WIDGET_SECTION_STYLE,
                children=[
                    html.H2("Grid Loading Indicators"),
                    build_loading_wrapper(
                        html.Div(
                            [
                                html.Div(
                                    create_default_grid_loading_cards(),
                                    id="grid-loading-kpi-cards",
                                    className="grid-capacity-kpi-grid",
                                    style=KPI_CARD_GRID_STYLE,
                                ),
                                html.Div(
                                    id="grid-loading-status",
                                    style={"display": "none"},
                                ),
                            ]
                        ),
                        component_id="grid-loading-summary-loading",
                        message="Loading results...",
                        target_components={
                            "grid-loading-kpi-cards": "children",
                            "grid-loading-status": "children",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
            ),
        ],
        component_id="grid-capacity-primary-region",
        style={"marginBottom": "1rem"},
    )


def _build_grid_capacity_secondary_region() -> Any:
    """Return the planning-and-feeder Grid & Capacity region."""

    return build_dashboard_region_grid(
        GRID_CAPACITY_SECONDARY_REGION_SPEC,
        [
            DashboardWidgetPlacement(
                spec=GRID_CAPACITY_SENSITIVITY_WIDGET_SPEC,
                component_id="grid-capacity-sensitivity-region-section",
                style=DASHBOARD_WIDGET_SECTION_STYLE,
                children=[
                    html.H2("Connection Capacity Planning"),
                    build_loading_wrapper(
                        html.Div(
                            DEFAULT_CAPACITY_SENSITIVITY_MESSAGE,
                            id="capacity-sensitivity-table",
                            className="grid-capacity-sensitivity-table-shell",
                        ),
                        component_id="capacity-sensitivity-table-loading",
                        message="Loading results...",
                        target_components={
                            "capacity-sensitivity-table": "children",
                            "active-capacity-sensitivity-store": "data",
                        },
                    ),
                ],
            ),
            DashboardWidgetPlacement(
                spec=GRID_CAPACITY_FEEDER_WIDGET_SPEC,
                component_id="grid-capacity-feeder-loading-section",
                style=DASHBOARD_WIDGET_SECTION_STYLE,
                children=[
                    html.H2("Feeder Loading"),
                    build_loading_wrapper(
                        html.Div(
                            DEFAULT_GRID_LOADING_MESSAGE,
                            id="feeder-summary-section",
                            className="grid-capacity-feeder-summary-shell",
                        ),
                        component_id="feeder-summary-section-loading",
                        message="Loading results...",
                        target_components={
                            "feeder-summary-section": "children",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
            ),
        ],
        component_id="grid-capacity-secondary-region",
        style={"marginBottom": "1rem"},
    )


def _build_grid_capacity_tertiary_region() -> Any:
    """Return the paired transformer and power evidence region."""

    return build_dashboard_region_grid(
        GRID_CAPACITY_TERTIARY_REGION_SPEC,
        [
            DashboardWidgetPlacement(
                spec=GRID_CAPACITY_TRANSFORMER_WIDGET_SPEC,
                component_id="grid-capacity-transformer-loading-section",
                style=DASHBOARD_WIDGET_SECTION_STYLE,
                children=[
                    html.H2("Transformer Loading Over Time"),
                    build_loading_wrapper(
                        dcc.Graph(
                            id="transformer-loading-chart",
                            figure={},
                            config={"responsive": True},
                            style=GRAPH_STYLE,
                        ),
                        component_id="transformer-loading-chart-loading",
                        message="Preparing visualizations...",
                        target_components={
                            "transformer-loading-chart": "figure",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
            ),
            DashboardWidgetPlacement(
                spec=GRID_CAPACITY_POWER_WIDGET_SPEC,
                component_id="grid-capacity-power-capacity-over-time-section",
                style=DASHBOARD_WIDGET_SECTION_STYLE,
                children=[
                    html.H2("Charging Power and Capacity Over Time"),
                    build_loading_wrapper(
                        dcc.Graph(
                            id="power-capacity-chart",
                            figure={},
                            config={"responsive": True},
                            style=GRAPH_STYLE,
                        ),
                        component_id="power-capacity-chart-loading",
                        message="Preparing visualizations...",
                        target_components={
                            "power-capacity-chart": "figure",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
            ),
        ],
        component_id="grid-capacity-tertiary-region",
        style={"marginBottom": "1rem"},
    )


def build_grid_capacity_tab() -> Any:
    """Return the Grid & Capacity tab layout."""

    return build_tab_panel(
        [
            _build_grid_capacity_primary_region(),
            _build_grid_capacity_secondary_region(),
            _build_grid_capacity_tertiary_region(),
        ]
    )
