from typing import Any

from dash import dcc, html

from .common import build_dashboard_header
from .grid_capacity import build_grid_capacity_tab
from .infrastructure import build_infrastructure_tab
from .overview import build_overview_tab
from .power_quality import build_power_quality_tab
from .scenario_comparison import build_scenario_comparison_tab
from .smart_charging import build_smart_charging_tab


TAB_STYLE = {
    "padding": "0.8rem 1rem",
    "fontSize": "0.9rem",
    "fontWeight": "600",
    "color": "#5f6f82",
    "backgroundColor": "#f8fafc",
    "border": "1px solid #d8e0e8",
    "borderBottom": "none",
}
TAB_SELECTED_STYLE = {
    **TAB_STYLE,
    "color": "#17212b",
    "backgroundColor": "#ffffff",
    "boxShadow": "inset 0 -2px 0 #1f6fb2",
}


def build_dashboard_tabs() -> Any:
    """Return the primary tab navigation for the dashboard area."""

    return dcc.Tabs(
        [
            dcc.Tab(
                label="Overview",
                value="overview",
                children=build_overview_tab(),
                className="dashboard-tab-label",
                selected_className="dashboard-tab-label--selected",
                style=TAB_STYLE,
                selected_style=TAB_SELECTED_STYLE,
            ),
            dcc.Tab(
                label="Infrastructure",
                value="infrastructure",
                children=build_infrastructure_tab(),
                className="dashboard-tab-label",
                selected_className="dashboard-tab-label--selected",
                style=TAB_STYLE,
                selected_style=TAB_SELECTED_STYLE,
            ),
            dcc.Tab(
                label="Smart Charging",
                value="smart-charging",
                children=build_smart_charging_tab(),
                className="dashboard-tab-label",
                selected_className="dashboard-tab-label--selected",
                style=TAB_STYLE,
                selected_style=TAB_SELECTED_STYLE,
            ),
            dcc.Tab(
                label="Grid & Capacity",
                value="grid-capacity",
                children=build_grid_capacity_tab(),
                className="dashboard-tab-label",
                selected_className="dashboard-tab-label--selected",
                style=TAB_STYLE,
                selected_style=TAB_SELECTED_STYLE,
            ),
            dcc.Tab(
                label="Power Quality",
                value="power-quality",
                children=build_power_quality_tab(),
                className="dashboard-tab-label",
                selected_className="dashboard-tab-label--selected",
                style=TAB_STYLE,
                selected_style=TAB_SELECTED_STYLE,
            ),
            dcc.Tab(
                label="Scenario Comparison",
                value="scenario-comparison",
                children=build_scenario_comparison_tab(),
                className="dashboard-tab-label",
                selected_className="dashboard-tab-label--selected",
                style=TAB_STYLE,
                selected_style=TAB_SELECTED_STYLE,
            ),
        ],
        id="dashboard-tabs",
        value="overview",
        className="dashboard-tabs",
        parent_className="dashboard-tabs-parent",
    )


def build_dashboard_content() -> Any:
    """Return the main dashboard content area shown beside the sidebar."""

    return html.Div(
        [
            build_dashboard_header(),
            build_dashboard_tabs(),
        ],
        className="app-main-content",
    )
