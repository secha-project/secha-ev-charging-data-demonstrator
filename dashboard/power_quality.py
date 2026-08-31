from typing import Any

from dash import dcc, html

from .common import (
    BORDER_COLOR,
    DASHBOARD_WIDGET_SECTION_STYLE,
    GRAPH_STYLE,
    KPI_CARD_GRID_STYLE,
    SECTION_LEAD_TEXT_STYLE,
    SUBTLE_SURFACE_BACKGROUND_COLOR,
    build_tab_panel,
    build_loading_wrapper,
    create_default_power_quality_cards,
    create_default_power_quality_status_children,
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


POWER_QUALITY_PRIMARY_REGION_SPEC = DashboardRegionSpec(
    region_id="power_quality_primary",
    columns=DashboardRegionColumns(mobile=1, tablet=1, desktop=1),
)
POWER_QUALITY_EVIDENCE_REGION_SPEC = DashboardRegionSpec(
    region_id="power_quality_evidence",
    columns=DashboardRegionColumns(mobile=1, tablet=1, desktop=1),
)
POWER_QUALITY_SECONDARY_REGION_SPEC = DashboardRegionSpec(
    region_id="power_quality_secondary",
    columns=DashboardRegionColumns(mobile=1, tablet=1, desktop=1),
)

POWER_QUALITY_KPI_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="power-quality-kpi-section",
    region=POWER_QUALITY_PRIMARY_REGION_SPEC.region_id,
    priority=10,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=12),
    height_hint=DashboardWidgetHeightHint.COMPACT,
    mode_hint=DashboardWidgetMode.SUMMARY,
)
POWER_QUALITY_HARMONIC_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="power-quality-harmonic-risk-section",
    region=POWER_QUALITY_EVIDENCE_REGION_SPEC.region_id,
    priority=10,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=8),
    height_hint=DashboardWidgetHeightHint.TALL,
    mode_hint=DashboardWidgetMode.CHART,
)
POWER_QUALITY_IMBALANCE_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="power-quality-current-imbalance-section",
    region=POWER_QUALITY_EVIDENCE_REGION_SPEC.region_id,
    priority=20,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=4),
    height_hint=DashboardWidgetHeightHint.TALL,
    mode_hint=DashboardWidgetMode.CHART,
)
POWER_QUALITY_PHASE_LOAD_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="power-quality-phase-load-section",
    region=POWER_QUALITY_SECONDARY_REGION_SPEC.region_id,
    priority=10,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=12),
    height_hint=DashboardWidgetHeightHint.TALL,
    mode_hint=DashboardWidgetMode.CHART,
)


POWER_QUALITY_COMPACT_SECTION_STYLE = {
    **DASHBOARD_WIDGET_SECTION_STYLE,
    "padding": "1rem 1.125rem",
}
POWER_QUALITY_DISCLAIMER_STYLE = {
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "8px",
    "padding": "0.65rem 0.85rem",
    "backgroundColor": SUBTLE_SURFACE_BACKGROUND_COLOR,
    "marginTop": "0.85rem",
}
POWER_QUALITY_STATUS_STYLE = {
    **SECTION_LEAD_TEXT_STYLE,
    "marginTop": "0.35rem",
    "marginBottom": "0",
}
POWER_QUALITY_DISCLAIMER_TOOLTIP = (
    "Harmonic risk is a simplified bounded indicator. Current imbalance uses "
    "simplified phase-loading assumptions. Outputs are scenario-based model "
    "estimates, not standards-compliance measurements."
)


def _build_power_quality_disclaimer() -> Any:
    """Return the compact Power Quality modeling disclaimer row."""

    return html.Div(
        [
            html.Div(
                [
                    html.Span(
                        "PQ indicators are simplified scenario-based risk "
                        "estimates, not engineering-grade measurements or "
                        "compliance results."
                    ),
                    html.Span(
                        "\u24d8",
                        className="power-quality-tooltip-trigger",
                        tabIndex=0,
                        **{
                            "aria-label": POWER_QUALITY_DISCLAIMER_TOOLTIP,
                            "data-tooltip": POWER_QUALITY_DISCLAIMER_TOOLTIP,
                            "role": "button",
                        },
                    ),
                ],
                className="power-quality-disclaimer-row",
            ),
            html.Div(
                create_default_power_quality_status_children(),
                id="power-quality-status",
                style=POWER_QUALITY_STATUS_STYLE,
            ),
        ],
        style=POWER_QUALITY_DISCLAIMER_STYLE,
    )


def _build_power_quality_primary_region() -> Any:
    """Return the compact Power Quality summary region."""

    return build_dashboard_region_grid(
        POWER_QUALITY_PRIMARY_REGION_SPEC,
        [
            DashboardWidgetPlacement(
                spec=POWER_QUALITY_KPI_WIDGET_SPEC,
                component_id="power-quality-kpi-section",
                style=POWER_QUALITY_COMPACT_SECTION_STYLE,
                children=[
                    html.H2("Power Quality Indicators"),
                    build_loading_wrapper(
                        html.Div(
                            [
                                html.Div(
                                    create_default_power_quality_cards(),
                                    id="power-quality-kpi-cards",
                                    className="power-quality-kpi-grid",
                                    style=KPI_CARD_GRID_STYLE,
                                ),
                                _build_power_quality_disclaimer(),
                            ]
                        ),
                        component_id="power-quality-kpi-loading",
                        message="Loading results...",
                        target_components={
                            "power-quality-kpi-cards": "children",
                            "power-quality-status": "children",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
            ),
        ],
        component_id="power-quality-primary-region",
    )


def _build_power_quality_evidence_region() -> Any:
    """Return the asymmetric Power Quality evidence chart region."""

    return build_dashboard_region_grid(
        POWER_QUALITY_EVIDENCE_REGION_SPEC,
        [
            DashboardWidgetPlacement(
                spec=POWER_QUALITY_HARMONIC_WIDGET_SPEC,
                component_id="power-quality-harmonic-risk-section",
                style=DASHBOARD_WIDGET_SECTION_STYLE,
                children=[
                    html.H2("Harmonic Risk Over Time"),
                    build_loading_wrapper(
                        dcc.Graph(
                            id="harmonic-risk-chart",
                            figure={},
                            config={"responsive": True},
                            style=GRAPH_STYLE,
                        ),
                        component_id="harmonic-risk-chart-loading",
                        message="Preparing visualizations...",
                        target_components={
                            "harmonic-risk-chart": "figure",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
            ),
            DashboardWidgetPlacement(
                spec=POWER_QUALITY_IMBALANCE_WIDGET_SPEC,
                component_id="power-quality-current-imbalance-section",
                style=DASHBOARD_WIDGET_SECTION_STYLE,
                children=[
                    html.H2("Current Imbalance Over Time"),
                    build_loading_wrapper(
                        dcc.Graph(
                            id="current-imbalance-chart",
                            figure={},
                            config={"responsive": True},
                            style=GRAPH_STYLE,
                        ),
                        component_id="current-imbalance-chart-loading",
                        message="Preparing visualizations...",
                        target_components={
                            "current-imbalance-chart": "figure",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
            ),
        ],
        component_id="power-quality-evidence-region",
    )


def _build_power_quality_secondary_region() -> Any:
    """Return the secondary Power Quality region using shared widget shells."""

    return build_dashboard_region_grid(
        POWER_QUALITY_SECONDARY_REGION_SPEC,
        [
            DashboardWidgetPlacement(
                spec=POWER_QUALITY_PHASE_LOAD_WIDGET_SPEC,
                component_id="power-quality-phase-load-context-section",
                style=DASHBOARD_WIDGET_SECTION_STYLE,
                children=[
                    html.H2("Phase Load Over Time"),
                    build_loading_wrapper(
                        dcc.Graph(
                            id="phase-load-chart",
                            figure={},
                            config={"responsive": True},
                            style=GRAPH_STYLE,
                        ),
                        component_id="phase-load-chart-loading",
                        message="Preparing visualizations...",
                        target_components={
                            "phase-load-chart": "figure",
                            "active-simulation-results-store": "data",
                            "active-metrics-store": "data",
                        },
                    ),
                ],
            )
        ],
        component_id="power-quality-secondary-region",
        style={"marginBottom": "1rem"},
    )


def build_power_quality_tab() -> Any:
    """Return the Power Quality tab layout."""

    return build_tab_panel(
        [
            _build_power_quality_primary_region(),
            _build_power_quality_evidence_region(),
            _build_power_quality_secondary_region(),
        ]
    )
