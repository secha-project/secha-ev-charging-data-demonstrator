from typing import Any

from dash import dcc, html

from scenarios import (
    COMPARISON_SOURCE_MODIFIED_COPY,
    COMPARISON_SOURCE_TEMPLATE,
    default_scenario,
    default_scenario_preset,
    list_scenario_presets,
)

from .common import (
    ACCENT_BLUE,
    BORDER_COLOR,
    COMPARISON_BUILDER_ACTION_VISIBLE_STYLE,
    COMPARISON_EYEBROW_STYLE,
    COMPARISON_LEAD_TEXT_STYLE,
    DASHBOARD_WIDGET_SECTION_STYLE,
    SECTION_LEAD_TEXT_STYLE,
    SUBTLE_SURFACE_BACKGROUND_COLOR,
    SURFACE_BACKGROUND_COLOR,
    TEXT_PRIMARY_COLOR,
    TEXT_SECONDARY_COLOR,
    build_compact_scenario_preset_details,
    create_default_changed_assumptions_children,
    create_default_scenario_ab_executive_summary_cards,
    create_default_scenario_comparison_empty_state_children,
    build_loading_wrapper,
    DEFAULT_SCENARIO_AB_SIMULATION_STATUS,
    DEFAULT_SCENARIO_COMPARISON_STATUS,
    KPI_CARD_GRID_STYLE,
    SCENARIO_B_EDITOR_VISIBLE_STYLE,
    SCENARIO_B_TEMPLATE_HIDDEN_STYLE,
    build_tab_panel,
)
from .layout_components import (
    build_dashboard_region_grid,
    create_dashboard_widget_placement,
)
from .layout_contract import (
    DashboardRegionColumns,
    DashboardRegionSpec,
    DashboardWidgetHeightHint,
    DashboardWidgetMode,
    DashboardWidgetSpec,
    DashboardWidgetSpan,
)

COMPARISON_OPTION_LABEL_STYLE = {
    "display": "inline-flex",
    "alignItems": "center",
    "gap": "0.5rem",
    "marginBottom": "0",
    "padding": "0.55rem 0.85rem",
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "999px",
    "backgroundColor": SUBTLE_SURFACE_BACKGROUND_COLOR,
}
COMPARISON_CONFIGURATION_PANEL_STYLE = {
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "8px",
    "padding": "1rem 1.125rem",
    "backgroundColor": SUBTLE_SURFACE_BACKGROUND_COLOR,
    "marginTop": "0.75rem",
}
COMPARISON_BUILDER_SECTION_STYLE = {
    "padding": "0.85rem 0 0.35rem",
    "borderTop": f"1px solid {BORDER_COLOR}",
}
COMPARISON_BUILDER_STACK_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "0.1rem",
    "width": "100%",
}
COMPARISON_BUILDER_RUN_SECTION_VISIBLE_STYLE = dict(
    COMPARISON_BUILDER_SECTION_STYLE,
)
COMPARISON_BUILDER_RUN_SECTION_HIDDEN_STYLE = {
    "display": "none",
}
COMPARISON_BUILDER_EXPANDED_VISIBLE_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "0.5rem",
}
COMPARISON_BUILDER_EXPANDED_HIDDEN_STYLE = {
    "display": "none",
}
COMPARISON_BUILDER_COLLAPSED_BAR_VISIBLE_STYLE = {
    "position": "sticky",
    "top": "0.5rem",
    "zIndex": "40",
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "12px",
    "padding": "0.65rem 0.85rem",
    "backgroundColor": "rgba(255, 255, 255, 0.94)",
    "boxShadow": "0 10px 24px rgba(23, 33, 43, 0.08)",
}
COMPARISON_BUILDER_COLLAPSED_BAR_HIDDEN_STYLE = {
    **COMPARISON_BUILDER_COLLAPSED_BAR_VISIBLE_STYLE,
    "display": "none",
}
COMPARISON_BUILDER_COLLAPSED_BAR_ROW_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(0, 1fr) auto",
    "gap": "0.85rem",
    "alignItems": "center",
}
COMPARISON_BUILDER_COLLAPSED_BAR_TEXT_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "0.15rem",
    "minWidth": "0",
}
COMPARISON_BUILDER_COLLAPSED_BAR_ACTIONS_STYLE = {
    "display": "flex",
    "alignItems": "center",
    "gap": "0.6rem",
    "justifyContent": "flex-end",
    "flexWrap": "wrap",
    "minWidth": "0",
}
COMPARISON_BUILDER_STATUS_CHIP_BASE_STYLE = {
    "display": "inline-flex",
    "alignItems": "center",
    "padding": "0.3rem 0.65rem",
    "borderRadius": "999px",
    "fontSize": "0.8rem",
    "fontWeight": "600",
}
COMPARISON_PRIMARY_BUTTON_STYLE = {
    "backgroundColor": ACCENT_BLUE,
    "color": "#ffffff",
    "border": f"1px solid {ACCENT_BLUE}",
    "borderRadius": "8px",
    "padding": "0.8rem 1rem",
    "fontSize": "0.95rem",
    "fontWeight": "600",
    "width": "auto",
    "whiteSpace": "nowrap",
}
COMPARISON_SECONDARY_BUTTON_STYLE = {
    "backgroundColor": SURFACE_BACKGROUND_COLOR,
    "color": TEXT_PRIMARY_COLOR,
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "8px",
    "padding": "0.55rem 0.85rem",
    "fontWeight": "600",
}
COMPARISON_INLINE_STATUS_STYLE = {
    "marginBottom": "0",
    "marginTop": "0",
    "padding": "0",
    "fontSize": "0.85rem",
    "fontWeight": "600",
    "color": TEXT_SECONDARY_COLOR,
    "lineHeight": "1.4",
}
COMPARISON_BUILDER_RUN_ROW_STYLE = {
    "display": "flex",
    "justifyContent": "flex-start",
    "alignItems": "flex-end",
    "gap": "0.85rem",
    "flexWrap": "wrap",
}
COMPARISON_BUILDER_RUN_CONTENT_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "0.35rem",
    "flex": "0 1 auto",
    "minWidth": "0",
}
COMPARISON_BUILDER_RUN_ACTION_STYLE = {
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "flex-start",
    "flex": "0 0 auto",
    "minWidth": "0",
}
COMPARISON_INLINE_LABEL_STYLE = {
    "color": TEXT_PRIMARY_COLOR,
    "fontSize": "0.88rem",
    "fontWeight": "600",
    "flex": "0 0 auto",
}
COMPARISON_INLINE_ROW_STYLE = {
    "display": "flex",
    "alignItems": "center",
    "gap": "0.75rem",
    "flexWrap": "wrap",
}
COMPARISON_PARAMETER_ROW_STYLE = {
    "display": "flex",
    "alignItems": "flex-end",
    "gap": "0.75rem",
    "flexWrap": "wrap",
}
COMPARISON_PARAMETER_FIELD_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "0.25rem",
    "flex": "0 1 10.5rem",
    "minWidth": "9.75rem",
}
COMPARISON_TEMPLATE_SELECTOR_SHELL_STYLE = {
    "flex": "0 1 16rem",
    "minWidth": "12rem",
    "maxWidth": "18rem",
}

SCENARIO_COMPARISON_BUILDER_REGION_SPEC = DashboardRegionSpec(
    region_id="scenario_comparison_builder",
    columns=DashboardRegionColumns(mobile=1, tablet=1, desktop=1),
)
SCENARIO_COMPARISON_RESULTS_REGION_SPEC = DashboardRegionSpec(
    region_id="scenario_comparison_results",
    columns=DashboardRegionColumns(mobile=1, tablet=1, desktop=1),
)
SCENARIO_COMPARISON_EXECUTIVE_GRID_STYLE = {
    **KPI_CARD_GRID_STYLE,
    "gridTemplateColumns": "repeat(auto-fit, minmax(190px, 1fr))",
    "gap": "0.75rem",
}

SCENARIO_COMPARISON_BUILDER_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="scenario-comparison-builder-section",
    region=SCENARIO_COMPARISON_BUILDER_REGION_SPEC.region_id,
    priority=10,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=12),
    height_hint=DashboardWidgetHeightHint.STANDARD,
    mode_hint=DashboardWidgetMode.DETAIL,
)
SCENARIO_COMPARISON_EXECUTIVE_SUMMARY_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="scenario-ab-executive-summary-section",
    region=SCENARIO_COMPARISON_RESULTS_REGION_SPEC.region_id,
    priority=10,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=12),
    height_hint=DashboardWidgetHeightHint.COMPACT,
    mode_hint=DashboardWidgetMode.SUMMARY,
)
SCENARIO_AB_COMPARISON_TABLE_WIDGET_SPEC = DashboardWidgetSpec(
    widget_id="scenario-ab-comparison-table-section",
    region=SCENARIO_COMPARISON_RESULTS_REGION_SPEC.region_id,
    priority=20,
    span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=12),
    height_hint=DashboardWidgetHeightHint.TALL,
    mode_hint=DashboardWidgetMode.DETAIL,
)


def _build_scenario_b_number_input(
    label: str,
    input_id: str,
    *,
    min_value: int | float,
    step: int | float,
    value: int | float | None = None,
) -> Any:
    return html.Div(
        [
            html.Label(
                label,
                htmlFor=input_id,
                style={
                    "display": "block",
                    "fontWeight": "bold",
                    "marginBottom": "0.25rem",
                    "whiteSpace": "nowrap",
                },
            ),
            dcc.Input(
                id=input_id,
                type="number",
                min=min_value,
                step=step,
                value=value,
                debounce=False,
                style={
                    "width": "100%",
                    "boxSizing": "border-box",
                },
            ),
        ],
        className="scenario-comparison-parameter-field",
        style=COMPARISON_PARAMETER_FIELD_STYLE,
    )


def _build_comparison_source_option_label(
    title: str,
    helper_text: str | None = None,
) -> Any:
    children: list[Any] = [html.Span(title, style={"fontWeight": "600"})]
    if helper_text:
        children.append(
            html.Span(
                helper_text,
                style={
                    **SECTION_LEAD_TEXT_STYLE,
                    "marginBottom": "0",
                    "marginTop": "0",
                },
            )
        )

    return html.Div(
        children,
        className="scenario-comparison-source-option-content",
    )


def _build_setup_region() -> Any:
    """Return the compact Comparison Builder region for Scenario Comparison."""

    return build_dashboard_region_grid(
        SCENARIO_COMPARISON_BUILDER_REGION_SPEC,
        [
            create_dashboard_widget_placement(
                spec=SCENARIO_COMPARISON_BUILDER_WIDGET_SPEC,
                component_id="scenario-comparison-builder-section",
                base_style=DASHBOARD_WIDGET_SECTION_STYLE,
                class_name="scenario-comparison-builder-widget",
                children=[
                    dcc.Store(
                        id="scenario-comparison-edit-scroll-trigger",
                        data=0,
                    ),
                    html.Div(
                        id="scenario-comparison-edit-scroll-effect",
                        style={"display": "none"},
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        "Scenario Comparison",
                                        style=COMPARISON_EYEBROW_STYLE,
                                    ),
                                    html.Strong(
                                        "Scenario A vs Scenario B",
                                        id="scenario-comparison-collapsed-title",
                                        style={"fontSize": "1rem"},
                                    ),
                                    html.Span(
                                        "",
                                        id="scenario-comparison-collapsed-summary",
                                        style={
                                            "color": TEXT_SECONDARY_COLOR,
                                            "fontSize": "0.85rem",
                                        },
                                    ),
                                ],
                                style=COMPARISON_BUILDER_COLLAPSED_BAR_TEXT_STYLE,
                            ),
                            html.Div(
                                [
                                    html.Span(
                                        "",
                                        id="scenario-comparison-collapsed-status",
                                        style=COMPARISON_BUILDER_STATUS_CHIP_BASE_STYLE,
                                    ),
                                    html.Button(
                                        "Edit Comparison",
                                        id="edit-scenario-comparison-button",
                                        n_clicks=0,
                                        type="button",
                                        style=COMPARISON_SECONDARY_BUTTON_STYLE,
                                    ),
                                    html.Button(
                                        "Run Again",
                                        id="rerun-scenario-ab-comparison-button",
                                        n_clicks=0,
                                        type="button",
                                        style=COMPARISON_SECONDARY_BUTTON_STYLE,
                                    ),
                                ],
                                style=COMPARISON_BUILDER_COLLAPSED_BAR_ACTIONS_STYLE,
                            ),
                        ],
                        id="scenario-comparison-builder-collapsed-bar",
                        className="scenario-comparison-builder-collapsed-bar",
                        style={
                            **COMPARISON_BUILDER_COLLAPSED_BAR_ROW_STYLE,
                            **COMPARISON_BUILDER_COLLAPSED_BAR_HIDDEN_STYLE,
                        },
                    ),
                    html.Div(
                        [
                            html.Div("Compare", style=COMPARISON_EYEBROW_STYLE),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Span(
                                                        "Compare",
                                                        style=COMPARISON_INLINE_LABEL_STYLE,
                                                    ),
                                                    dcc.RadioItems(
                                                        id="comparison-source-selector",
                                                        options=[
                                                            {
                                                                "label": _build_comparison_source_option_label(
                                                                    "Modify current scenario"
                                                                ),
                                                                "value": COMPARISON_SOURCE_MODIFIED_COPY,
                                                            },
                                                            {
                                                                "label": _build_comparison_source_option_label(
                                                                    "Predefined template"
                                                                ),
                                                                "value": COMPARISON_SOURCE_TEMPLATE,
                                                            },
                                                        ],
                                                        value=COMPARISON_SOURCE_MODIFIED_COPY,
                                                        className="scenario-comparison-source-options",
                                                        labelStyle=COMPARISON_OPTION_LABEL_STYLE,
                                                        inputStyle={"marginRight": "0.45rem"},
                                                    ),
                                                ],
                                                className="scenario-comparison-inline-row",
                                                style=COMPARISON_INLINE_ROW_STYLE,
                                            ),
                                        ],
                                        id="scenario-b-source-section",
                                        className="scenario-comparison-builder-pane scenario-comparison-builder-pane--source",
                                        style={
                                            **COMPARISON_BUILDER_SECTION_STYLE,
                                            "borderTop": "none",
                                            "paddingTop": "0",
                                        },
                                    ),
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(
                                                        [
                                                            html.Span(
                                                                "Scenario B",
                                                                style=COMPARISON_INLINE_LABEL_STYLE,
                                                            ),
                                                            html.Button(
                                                                "Reset from Scenario A",
                                                                id="duplicate-scenario-b-button",
                                                                n_clicks=0,
                                                                type="button",
                                                                style=COMPARISON_SECONDARY_BUTTON_STYLE,
                                                            ),
                                                        ],
                                                        id="modified-copy-builder-action",
                                                        className="scenario-comparison-builder-reset-row",
                                                        style=COMPARISON_BUILDER_ACTION_VISIBLE_STYLE,
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                [
                                                                    _build_scenario_b_number_input(
                                                                        "Vehicles",
                                                                        "scenario-b-vehicles-input",
                                                                        min_value=1,
                                                                        step=1,
                                                                        value=default_scenario.vehicles,
                                                                    ),
                                                                    _build_scenario_b_number_input(
                                                                        "Chargers",
                                                                        "scenario-b-charger-count-input",
                                                                        min_value=1,
                                                                        step=1,
                                                                        value=default_scenario.charger_count,
                                                                    ),
                                                                    _build_scenario_b_number_input(
                                                                        "Charger power (kW)",
                                                                        "scenario-b-charger-power-input",
                                                                        min_value=0.1,
                                                                        step=0.1,
                                                                        value=default_scenario.charger_power,
                                                                    ),
                                                                    _build_scenario_b_number_input(
                                                                        "Grid (kW)",
                                                                        "scenario-b-grid-capacity-input",
                                                                        min_value=0.1,
                                                                        step=0.1,
                                                                        value=default_scenario.grid_capacity,
                                                                    ),
                                                                ],
                                                                className="scenario-comparison-parameter-row",
                                                                style=COMPARISON_PARAMETER_ROW_STYLE,
                                                            ),
                                                            html.Div(
                                                                "",
                                                                id="scenario-b-validation-message",
                                                                style={
                                                                    "color": "#b63a3a",
                                                                    "fontSize": "0.85rem",
                                                                    "marginTop": "0.25rem",
                                                                },
                                                            ),
                                                        ],
                                                        id="scenario-b-editor-section",
                                                        className="scenario-comparison-builder-editor",
                                                        style=SCENARIO_B_EDITOR_VISIBLE_STYLE,
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                [
                                                                    html.Span(
                                                                        "Scenario B",
                                                                        style=COMPARISON_INLINE_LABEL_STYLE,
                                                                    ),
                                                                    html.Div(
                                                                        [
                                                                            dcc.Dropdown(
                                                                                id="scenario-b-template-selector",
                                                                                options=[
                                                                                    {
                                                                                        "label": preset.label,
                                                                                        "value": preset.preset_id,
                                                                                    }
                                                                                    for preset in list_scenario_presets()
                                                                                ],
                                                                                value=default_scenario_preset.preset_id,
                                                                                clearable=False,
                                                                            ),
                                                                        ],
                                                                        className="scenario-comparison-template-select-shell",
                                                                        style=COMPARISON_TEMPLATE_SELECTOR_SHELL_STYLE,
                                                                    ),
                                                                    html.Div(
                                                                        build_compact_scenario_preset_details(
                                                                            default_scenario_preset
                                                                        ),
                                                                        id="scenario-b-template-details",
                                                                        className="scenario-comparison-template-details",
                                                                    ),
                                                                ],
                                                                className="scenario-comparison-template-row",
                                                                style=COMPARISON_INLINE_ROW_STYLE,
                                                            ),
                                                        ],
                                                        id="scenario-b-template-section",
                                                        className="scenario-comparison-builder-template-block",
                                                        style=SCENARIO_B_TEMPLATE_HIDDEN_STYLE,
                                                    ),
                                                    html.P(
                                                        DEFAULT_SCENARIO_COMPARISON_STATUS,
                                                        id="scenario-comparison-status",
                                                        style=COMPARISON_INLINE_STATUS_STYLE,
                                                    ),
                                                ],
                                                className="scenario-comparison-builder-config-stack",
                                            ),
                                        ],
                                        id="scenario-b-configuration-section",
                                        className="scenario-comparison-builder-pane scenario-comparison-builder-pane--configuration",
                                        style=COMPARISON_BUILDER_SECTION_STYLE,
                                    ),
                                    html.Div(
                                        [
                                            html.Div(
                                                create_default_changed_assumptions_children(),
                                                id="scenario-ab-assumptions-summary",
                                            ),
                                        ],
                                        id="scenario-ab-assumptions-section",
                                        className="scenario-comparison-builder-pane scenario-comparison-builder-pane--assumptions",
                                        style=COMPARISON_BUILDER_SECTION_STYLE,
                                    ),
                                    html.Div(
                                        build_loading_wrapper(
                                            html.Div(
                                                [
                                                    html.Div(
                                                        [
                                                            html.P(
                                                                DEFAULT_SCENARIO_AB_SIMULATION_STATUS,
                                                                id="scenario-ab-simulation-status",
                                                                style=COMPARISON_INLINE_STATUS_STYLE,
                                                            ),
                                                            html.Div(
                                                                create_default_scenario_comparison_empty_state_children(),
                                                                id="scenario-comparison-empty-state",
                                                            ),
                                                        ],
                                                        className="scenario-comparison-run-content",
                                                        style=COMPARISON_BUILDER_RUN_CONTENT_STYLE,
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Button(
                                                                "Run comparison",
                                                                id="run-scenario-ab-comparison-button",
                                                                n_clicks=0,
                                                                type="button",
                                                                className="scenario-comparison-primary-action",
                                                                style=COMPARISON_PRIMARY_BUTTON_STYLE,
                                                            ),
                                                        ],
                                                        className="scenario-comparison-run-actions",
                                                        style=COMPARISON_BUILDER_RUN_ACTION_STYLE,
                                                    ),
                                                ],
                                                className="scenario-comparison-run-row",
                                                style=COMPARISON_BUILDER_RUN_ROW_STYLE,
                                            ),
                                            component_id="scenario-comparison-run-state-loading",
                                            message="Running simulation...",
                                            target_components={
                                                "scenario-ab-metrics-store": "data",
                                                "scenario-ab-difference-metrics-store": "data",
                                                "scenario-ab-simulation-status": "children",
                                            },
                                        ),
                                        id="scenario-comparison-empty-state-section",
                                        className="scenario-comparison-builder-pane scenario-comparison-run-section",
                                        style=COMPARISON_BUILDER_RUN_SECTION_VISIBLE_STYLE,
                                    ),
                                ],
                                className="scenario-comparison-builder-stack",
                                style=COMPARISON_BUILDER_STACK_STYLE,
                            ),
                        ],
                        id="scenario-comparison-builder-expanded-content",
                        className="scenario-comparison-builder-expanded",
                        style=COMPARISON_BUILDER_EXPANDED_VISIBLE_STYLE,
                    ),
                ],
            ),
        ],
        component_id="scenario-comparison-builder-region",
        style={"marginBottom": "1rem"},
    )


def _build_results_region() -> Any:
    """Return the shared results region for Scenario Comparison."""

    return build_dashboard_region_grid(
        SCENARIO_COMPARISON_RESULTS_REGION_SPEC,
        [
            create_dashboard_widget_placement(
                spec=SCENARIO_COMPARISON_EXECUTIVE_SUMMARY_WIDGET_SPEC,
                component_id="scenario-ab-executive-summary-section",
                base_style=DASHBOARD_WIDGET_SECTION_STYLE,
                hidden=True,
                children=[
                    html.H2("Headline Comparison KPIs"),
                    build_loading_wrapper(
                        html.Div(
                            create_default_scenario_ab_executive_summary_cards(
                                default_scenario_preset.label,
                                f"{default_scenario_preset.label} (Modified)",
                            ),
                            id="scenario-ab-executive-summary-cards",
                            style=SCENARIO_COMPARISON_EXECUTIVE_GRID_STYLE,
                        ),
                        component_id="scenario-ab-executive-summary-loading",
                        message="Loading results...",
                        target_components={
                            "scenario-ab-executive-summary-cards": "children",
                            "scenario-ab-metrics-store": "data",
                        },
                    ),
                ],
            ),
            create_dashboard_widget_placement(
                spec=SCENARIO_AB_COMPARISON_TABLE_WIDGET_SPEC,
                component_id="scenario-ab-comparison-table-section",
                base_style=DASHBOARD_WIDGET_SECTION_STYLE,
                hidden=True,
                children=[
                    html.H2("Detailed Decision Evidence"),
                    html.P(
                        "Select a decision area to review supporting metrics, "
                        "status comparisons, charts, and technical findings "
                        "in the evidence panel.",
                        style=COMPARISON_LEAD_TEXT_STYLE,
                    ),
                    build_loading_wrapper(
                        html.Div(
                            "",
                            id="scenario-ab-comparison-table",
                        ),
                        component_id="scenario-ab-comparison-table-loading",
                        message="Preparing visualizations...",
                        target_components={
                            "scenario-ab-comparison-table": "children",
                            "scenario-ab-metrics-store": "data",
                            "scenario-ab-difference-metrics-store": "data",
                        },
                    ),
                ],
            ),
        ],
        component_id="scenario-comparison-results-region",
        style={"marginBottom": "1rem"},
    )


def build_scenario_comparison_tab() -> Any:
    """Return the Scenario Comparison tab layout."""

    return build_tab_panel(
        [
            dcc.Store(id="scenario-ab-selected-section-store", data=None),
            _build_setup_region(),
            _build_results_region(),
        ]
    )
