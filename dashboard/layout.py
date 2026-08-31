from typing import Any

from dash import dcc, html

from .common import (
    FONT_FAMILY_STACK,
    PAGE_BACKGROUND_COLOR,
    TEXT_PRIMARY_COLOR,
    build_initial_active_scenario_store_data,
    build_initial_scenario_builder_store_data,
    build_initial_scenario_comparison_store_data,
)
from .sidebar import build_sidebar
from .tabs import build_dashboard_content


def build_main_layout() -> Any:
    """Return the composed application layout."""

    return html.Main(
        [
            dcc.Store(
                id="active-scenario-store",
                data=build_initial_active_scenario_store_data(),
            ),
            dcc.Store(
                id="scenario-builder-store",
                data=build_initial_scenario_builder_store_data(),
            ),
            dcc.Store(
                id="scenario-builder-feedback-store",
                data={
                    "action": "idle",
                    "overwrote_modified_values": False,
                    "validation_message": "",
                },
            ),
            dcc.Store(id="active-simulation-results-store", data=None),
            dcc.Store(id="active-metrics-store", data=None),
            dcc.Store(id="active-capacity-sensitivity-store", data=None),
            dcc.Store(
                id="single-scenario-run-status-store",
                data={"status": "not_run"},
            ),
            dcc.Store(
                id="scenario-comparison-store",
                data=build_initial_scenario_comparison_store_data(),
            ),
            dcc.Store(id="scenario-ab-simulation-results-store", data=None),
            dcc.Store(id="scenario-ab-metrics-store", data=None),
            dcc.Store(id="scenario-ab-difference-metrics-store", data=None),
            dcc.Store(
                id="scenario-comparison-run-status-store",
                data={"status": "not_run"},
            ),
            dcc.Store(
                id="scenario-comparison-builder-ui-store",
                data={"collapsed": False, "has_run": False},
            ),
            html.Div(
                id="dashboard-graph-resize-effect",
                style={"display": "none"},
            ),
            html.Div(
                [
                    build_sidebar(),
                    build_dashboard_content(),
                ],
                className="app-shell",
            ),
        ],
        style={
            "fontFamily": FONT_FAMILY_STACK,
            "lineHeight": "1.5",
            "backgroundColor": PAGE_BACKGROUND_COLOR,
            "color": TEXT_PRIMARY_COLOR,
            "minHeight": "100vh",
        },
    )


def create_layout() -> Any:
    """Backward-compatible layout factory for the Dash app."""

    return build_main_layout()
