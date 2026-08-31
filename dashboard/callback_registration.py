"""Dash callback registration for the dashboard UI."""

import sys
from typing import Any

from dash import ALL, Input, Output, State, ctx, no_update

from metrics import capacity_alternative_metrics_from_dict, metrics_from_dict
from scenarios import (
    ChargingStrategy,
    COMPARISON_SOURCE_MODIFIED_COPY,
    COMPARISON_SOURCE_TEMPLATE,
    active_scenario_from_state,
    apply_preset_defaults_to_active_scenario_state,
    default_scenario_preset,
    get_active_scenario_is_modified,
    get_active_scenario_parameters,
    get_active_scenario_preset_id,
    reset_active_scenario_to_preset_defaults,
    update_active_scenario_parameters,
    update_scenario_a_in_comparison_data,
)

from dashboard.common import (
    DEFAULT_CAPACITY_SENSITIVITY_LOADING_MESSAGE,
    DEFAULT_CAPACITY_SENSITIVITY_MESSAGE,
    DEFAULT_SCENARIO_AB_SIMULATION_STATUS,
    DEFAULT_SCENARIO_COMPARISON_STATUS,
)
from dashboard.scenario_comparison import (
    COMPARISON_BUILDER_COLLAPSED_BAR_HIDDEN_STYLE,
    COMPARISON_BUILDER_COLLAPSED_BAR_ROW_STYLE,
    COMPARISON_BUILDER_COLLAPSED_BAR_VISIBLE_STYLE,
    COMPARISON_BUILDER_EXPANDED_HIDDEN_STYLE,
    COMPARISON_BUILDER_EXPANDED_VISIBLE_STYLE,
    COMPARISON_BUILDER_STATUS_CHIP_BASE_STYLE,
    COMPARISON_SECONDARY_BUTTON_STYLE,
)
from dashboard.sidebar import (
    build_sidebar_field_groups,
    get_sidebar_field_container_id,
    get_sidebar_field_input_id,
)

from .callback_rendering import (
    GRID_CAPACITY_TAB_VALUE,
    INFRASTRUCTURE_TAB_VALUE,
    OVERVIEW_TAB_VALUE,
    POWER_QUALITY_TAB_VALUE,
    SCENARIO_AB_SECTION_SELECT_ID_TYPE,
    SCENARIO_COMPARISON_TAB_VALUE,
    SMART_CHARGING_TAB_VALUE,
    _single_scenario_grid_capacity_placeholder_response,
    _single_scenario_grid_capacity_response,
    _single_scenario_infrastructure_placeholder_response,
    _single_scenario_infrastructure_response,
    _single_scenario_overview_placeholder_response,
    _single_scenario_overview_response,
    _single_scenario_power_quality_placeholder_response,
    _single_scenario_power_quality_response,
    _single_scenario_render_context_from_states,
    _single_scenario_smart_charging_placeholder_response,
    _single_scenario_smart_charging_response,
    _single_scenario_summary_placeholder_response,
    _single_scenario_summary_response,
    render_comparison_scenario_preset_details,
    render_connection_capacity_sensitivity_table,
    render_scenario_preset_details,
)
from .callback_state import (
    SCENARIO_SIDEBAR_FIELD_NAMES,
    _build_scenario_ab_results_render_state,
    _comparison_builder_styles,
    _create_scenario_builder_feedback_state,
    _normalize_scenario_builder_feedback_state,
    _normalize_scenario_comparison_builder_ui_state,
    _normalize_scenario_comparison_run_status_state,
    _normalize_single_scenario_run_status_state,
    _render_changed_assumptions_summary,
    _render_scenario_comparison_collapsed_bar,
    _resolved_template_id,
    _scenario_b_editor_values,
    _scenario_builder_status_message_state,
    _scenario_comparison_builder_is_collapsed,
    _sidebar_field_values_from_active_state,
    _sidebar_parameters_from_input_values,
    _sidebar_session_dwell_field_style,
    _stale_comparison_status,
    _template_comparison_status,
    create_active_scenario_state,
)

SCENARIO_B_INPUT_IDS = {
    "scenario-b-vehicles-input",
    "scenario-b-charger-count-input",
    "scenario-b-charger-power-input",
    "scenario-b-grid-capacity-input",
}


def _callbacks_module() -> Any:
    """Return the compatibility callbacks module for monkeypatch-friendly lookups."""

    return sys.modules["dashboard.callbacks"]


def register_callbacks(app: Any) -> None:
    """Register dashboard callbacks for the Dash application."""

    app.clientside_callback(
        """
        function(editScrollTrigger) {
            if (!editScrollTrigger) {
                return window.dash_clientside.no_update;
            }

            const maxAttempts = 12;
            const scrollToBuilder = (attempt) => {
                const expandedContent = document.getElementById(
                    "scenario-comparison-builder-expanded-content"
                );
                const collapsedBar = document.getElementById(
                    "scenario-comparison-builder-collapsed-bar"
                );
                const builderSection = document.getElementById(
                    "scenario-comparison-builder-section"
                );
                const target = expandedContent || builderSection;

                if (!expandedContent || !target) {
                    return;
                }

                const expandedVisible =
                    window.getComputedStyle(expandedContent).display !== "none";
                const collapsedHidden =
                    !collapsedBar
                    || window.getComputedStyle(collapsedBar).display === "none";

                if (!expandedVisible || !collapsedHidden) {
                    if (attempt < maxAttempts) {
                        window.setTimeout(() => scrollToBuilder(attempt + 1), 50);
                    }
                    return;
                }

                const targetTop =
                    window.scrollY + target.getBoundingClientRect().top - 16;
                window.scrollTo({
                    top: Math.max(0, targetTop),
                    behavior: "smooth",
                });
            };

            window.requestAnimationFrame(() => scrollToBuilder(0));
            return window.dash_clientside.no_update;
        }
        """,
        Output("scenario-comparison-edit-scroll-effect", "children"),
        Input("scenario-comparison-edit-scroll-trigger", "data"),
        prevent_initial_call=True,
    )

    app.clientside_callback(
        """
        function(
            activeTab,
            singleScenarioResults,
            singleScenarioMetrics,
            singleScenarioRunStatus,
            comparisonResults,
            comparisonMetrics,
            comparisonDifferenceMetrics
        ) {
            const resizeVisiblePlots = () => {
                window.dispatchEvent(new Event("resize"));

                if (!window.Plotly || !window.Plotly.Plots) {
                    return;
                }

                document
                    .querySelectorAll(".js-plotly-plot")
                    .forEach((plot) => {
                        if (
                            !(plot instanceof HTMLElement)
                            || plot.offsetParent === null
                        ) {
                            return;
                        }

                        try {
                            window.Plotly.Plots.resize(plot);
                        } catch (error) {
                            // Ignore transient resize timing races; later retries still run.
                        }
                    });
            };

            window.requestAnimationFrame(() => {
                window.requestAnimationFrame(() => {
                    [0, 80, 180, 320].forEach((delayMs) => {
                        window.setTimeout(resizeVisiblePlots, delayMs);
                    });
                });
            });

            return window.dash_clientside.no_update;
        }
        """,
        Output("dashboard-graph-resize-effect", "children"),
        Input("dashboard-tabs", "value"),
        Input("active-simulation-results-store", "data"),
        Input("active-metrics-store", "data"),
        Input("single-scenario-run-status-store", "data"),
        Input("scenario-ab-simulation-results-store", "data"),
        Input("scenario-ab-metrics-store", "data"),
        Input("scenario-ab-difference-metrics-store", "data"),
        prevent_initial_call=True,
    )

    @app.callback(
        Output("charging-strategy-selector-container", "style"),
        Output("smart-charging-comparison-mode-container", "style"),
        Input("dashboard-tabs", "value"),
    )
    def update_strategy_selector_visibility(active_tab: str) -> tuple[dict[str, Any], dict[str, Any]]:
        """Toggle between the live selector and read-only comparison-mode copy."""
        if active_tab == SMART_CHARGING_TAB_VALUE:
            return {"display": "none"}, {"display": "block"}

        return {}, {"display": "none"}

    @app.callback(
        Output("scenario-preset-details", "children"),
        Output("scenario-preset-modified-indicator", "style"),
        Output("reset-scenario-preset-button", "style"),
        Output(
            get_sidebar_field_container_id("session_dwell_minutes"),
            "style",
        ),
        Input("scenario-builder-store", "data"),
    )
    def sync_sidebar_builder_ui(
        builder_state: dict[str, Any] | None,
    ):
        if builder_state is None:
            builder_state = create_active_scenario_state(
                default_scenario_preset.preset_id,
                ChargingStrategy.UNCONTROLLED.value,
            )

        is_modified = get_active_scenario_is_modified(builder_state)
        preset_id = (
            get_active_scenario_preset_id(builder_state)
            or default_scenario_preset.preset_id
        )
        return (
            render_scenario_preset_details(preset_id),
            {} if is_modified else {"display": "none"},
            (
                COMPARISON_SECONDARY_BUTTON_STYLE
                if is_modified
                else {**COMPARISON_SECONDARY_BUTTON_STYLE, "display": "none"}
            ),
            _sidebar_session_dwell_field_style(builder_state),
        )

    @app.callback(
        Output("scenario-builder-store", "data"),
        Output("scenario-builder-feedback-store", "data"),
        Input("scenario-preset-selector", "value"),
        Input("reset-scenario-preset-button", "n_clicks"),
        *[
            Input(get_sidebar_field_input_id(field_name), "value")
            for field_name in SCENARIO_SIDEBAR_FIELD_NAMES
        ],
        State("scenario-builder-store", "data"),
        prevent_initial_call=True,
    )
    def update_scenario_builder_state(
        preset_id: str,
        _reset_n_clicks: int,
        *field_values_and_builder_state: Any,
    ):
        *field_values, builder_state = field_values_and_builder_state
        resolved_builder_state = builder_state
        if resolved_builder_state is None:
            resolved_builder_state = create_active_scenario_state(
                default_scenario_preset.preset_id,
                ChargingStrategy.UNCONTROLLED.value,
            )

        resolved_preset_id = preset_id or default_scenario_preset.preset_id
        overwrote_modified_values = get_active_scenario_is_modified(
            resolved_builder_state
        )

        if _callbacks_module().ctx.triggered_id == "scenario-preset-selector":
            next_state = apply_preset_defaults_to_active_scenario_state(
                resolved_preset_id
            )
            if next_state == resolved_builder_state:
                return no_update, _create_scenario_builder_feedback_state()

            return (
                next_state,
                _create_scenario_builder_feedback_state(
                    action="apply_preset",
                    overwrote_modified_values=overwrote_modified_values,
                ),
            )

        if _callbacks_module().ctx.triggered_id == "reset-scenario-preset-button":
            next_state = reset_active_scenario_to_preset_defaults(
                resolved_builder_state
            )
            if next_state == resolved_builder_state:
                return no_update, _create_scenario_builder_feedback_state()

            return (
                next_state,
                _create_scenario_builder_feedback_state(
                    action="reset_preset",
                    overwrote_modified_values=overwrote_modified_values,
                ),
            )

        field_value_map = dict(zip(SCENARIO_SIDEBAR_FIELD_NAMES, field_values))
        try:
            next_parameters = _sidebar_parameters_from_input_values(
                resolved_builder_state,
                field_value_map,
            )
        except (TypeError, ValueError) as exc:
            return (
                no_update,
                _create_scenario_builder_feedback_state(
                    action="validation_error",
                    validation_message=str(exc),
                ),
            )

        try:
            next_state = update_active_scenario_parameters(
                resolved_builder_state,
                parameter_updates=next_parameters,
            )
        except (TypeError, ValueError) as exc:
            return (
                no_update,
                _create_scenario_builder_feedback_state(
                    action="validation_error",
                    validation_message=str(exc),
                ),
            )

        if next_parameters == get_active_scenario_parameters(resolved_builder_state):
            return no_update, _create_scenario_builder_feedback_state()

        return (
            next_state,
            _create_scenario_builder_feedback_state(action="field_edit"),
        )

    @app.callback(
        Output("scenario-sidebar-field-groups", "children"),
        Input("scenario-builder-store", "data"),
        Input("scenario-builder-feedback-store", "data"),
        prevent_initial_call=True,
    )
    def sync_sidebar_inputs_from_builder_state(
        builder_state: dict[str, Any] | None,
        feedback_state: dict[str, Any] | None,
    ):
        normalized_feedback = _normalize_scenario_builder_feedback_state(feedback_state)
        if normalized_feedback["action"] not in {"apply_preset", "reset_preset"}:
            return no_update

        if builder_state is None:
            builder_state = create_active_scenario_state(
                default_scenario_preset.preset_id,
                ChargingStrategy.UNCONTROLLED.value,
            )

        return build_sidebar_field_groups(
            {
                field_name: field_value
                for field_name, field_value in zip(
                    SCENARIO_SIDEBAR_FIELD_NAMES,
                    _sidebar_field_values_from_active_state(builder_state),
                )
            }
        )

    @app.callback(
        Output("active-scenario-store", "data"),
        Input("scenario-builder-store", "data"),
        State("active-scenario-store", "data"),
        prevent_initial_call=True,
    )
    def sync_active_scenario_from_builder_state(
        builder_state: dict[str, Any] | None,
        active_scenario_state: dict[str, Any] | None,
    ):
        if builder_state is None or builder_state == active_scenario_state:
            return no_update

        return builder_state

    @app.callback(
        Output("scenario-input-validation-message", "children"),
        Output("scenario-input-validation-message", "style"),
        Output("scenario-builder-status-message", "children"),
        Output("scenario-builder-status-message", "style"),
        Input("scenario-builder-feedback-store", "data"),
        Input("single-scenario-run-status-store", "data"),
    )
    def update_scenario_builder_messages(
        feedback_state: dict[str, Any] | None,
        run_status_state: dict[str, Any] | None,
    ):
        normalized_feedback = _normalize_scenario_builder_feedback_state(
            feedback_state
        )
        validation_message = normalized_feedback["validation_message"]
        status_message, status_style = _scenario_builder_status_message_state(
            normalized_feedback,
            run_status_state,
        )
        return (
            validation_message,
            {"display": "block"} if validation_message else {"display": "none"},
            status_message,
            status_style,
        )

    @app.callback(
        Output("active-simulation-results-store", "data"),
        Output("active-metrics-store", "data"),
        Output("single-scenario-run-status-store", "data"),
        Input("run-simulation-button", "n_clicks"),
        Input("active-scenario-store", "data"),
        State("single-scenario-run-status-store", "data"),
        State("scenario-builder-feedback-store", "data"),
        running=[
            (Output("run-simulation-button", "disabled"), True, False),
        ],
        prevent_initial_call=True,
    )
    def manage_single_scenario_run_state(
        _n_clicks: int,
        active_scenario_state: dict[str, Any] | None,
        run_status_state: dict[str, Any] | None,
        feedback_state: dict[str, Any] | None,
    ):
        normalized_run_status = _normalize_single_scenario_run_status_state(
            run_status_state
        )
        if _callbacks_module().ctx.triggered_id == "active-scenario-store":
            if active_scenario_state is None:
                return None, None, {"status": "not_run"}

            if normalized_run_status["status"] == "up_to_date":
                return no_update, no_update, {"status": "stale"}

            return no_update, no_update, normalized_run_status

        if active_scenario_state is None:
            return None, None, {"status": "not_run"}

        normalized_feedback = _normalize_scenario_builder_feedback_state(
            feedback_state
        )
        if normalized_feedback["validation_message"]:
            return no_update, no_update, normalized_run_status

        results_state, metrics_state = _callbacks_module().create_single_scenario_run_state(
            active_scenario_state
        )
        return results_state, metrics_state, {"status": "up_to_date"}

    @app.callback(
        Output("active-capacity-sensitivity-store", "data"),
        Input("active-scenario-store", "data"),
        Input("active-metrics-store", "data"),
        Input("dashboard-tabs", "value"),
        State("active-capacity-sensitivity-store", "data"),
        State("single-scenario-run-status-store", "data"),
        prevent_initial_call=True,
    )
    def manage_connection_capacity_sensitivity_state(
        active_scenario_state: dict[str, Any] | None,
        metrics_state: dict[str, Any] | None,
        active_tab: str,
        current_sensitivity_state: list[dict[str, Any]] | None,
        run_status_state: dict[str, Any] | None,
    ):
        if _callbacks_module().ctx.triggered_id == "active-scenario-store":
            return None

        if _callbacks_module().ctx.triggered_id == "dashboard-tabs":
            if active_tab != GRID_CAPACITY_TAB_VALUE:
                return no_update

            normalized_run_status = _normalize_single_scenario_run_status_state(
                run_status_state
            )
            if (
                active_scenario_state is None
                or metrics_state is None
                or normalized_run_status["status"] != "up_to_date"
                or current_sensitivity_state is not None
            ):
                return no_update

            return _callbacks_module().create_connection_capacity_sensitivity_state(
                active_scenario_state,
                metrics_state,
            )

        if active_scenario_state is None or metrics_state is None:
            return None

        if active_tab != GRID_CAPACITY_TAB_VALUE:
            return None

        return _callbacks_module().create_connection_capacity_sensitivity_state(
            active_scenario_state,
            metrics_state,
        )

    @app.callback(
        Output("capacity-vs-load-chart", "figure"),
        Output("overview-kpi-cards", "children"),
        Output("overview-smart-charging-preview", "children"),
        Input("active-simulation-results-store", "data"),
        Input("active-metrics-store", "data"),
        Input("dashboard-tabs", "value"),
        State("active-scenario-store", "data"),
    )
    def render_overview_tab(
        simulation_results_state: dict[str, dict[str, Any]] | None,
        metrics_state: dict[str, Any] | None,
        active_tab: str,
        active_scenario_state: dict[str, Any] | None,
    ):
        if active_tab != OVERVIEW_TAB_VALUE:
            return (no_update,) * 3

        context = _single_scenario_render_context_from_states(
            simulation_results_state,
            metrics_state,
            active_scenario_state,
        )
        if context is None:
            return _single_scenario_overview_placeholder_response()

        return _single_scenario_overview_response(
            context,
        )

    @app.callback(
        Output("total-daily-energy-value", "children"),
        Output("available-capacity-value", "children"),
        Output("peak-load-value", "children"),
        Output("capacity-utilization-value", "children"),
        Output("delivered-energy-value", "children"),
        Output("unmet-energy-value", "children"),
        Output("daily-charging-energy-value", "children"),
        Output("annual-energy-value", "children"),
        Output("scenario-status-message", "children"),
        Output("simulation-insights-list", "children"),
        Input("active-metrics-store", "data"),
        Input("single-scenario-run-status-store", "data"),
    )
    def render_single_scenario_summary(
        metrics_state: dict[str, Any] | None,
        run_status_state: dict[str, Any] | None,
    ):
        if metrics_state is None:
            return _single_scenario_summary_placeholder_response()

        return _single_scenario_summary_response(
            metrics_from_dict(metrics_state["active"]),
            tuple(metrics_state["insights"]),
            run_status_state=run_status_state,
        )

    @app.callback(
        Output("infrastructure-summary", "children"),
        Output("capacity-planning-kpi-cards", "children"),
        Output("charger-availability-kpi-cards", "children"),
        Output("service-pressure-chart", "figure"),
        Input("active-simulation-results-store", "data"),
        Input("active-metrics-store", "data"),
        Input("dashboard-tabs", "value"),
        State("active-scenario-store", "data"),
    )
    def render_infrastructure_tab(
        simulation_results_state: dict[str, dict[str, Any]] | None,
        metrics_state: dict[str, Any] | None,
        active_tab: str,
        active_scenario_state: dict[str, Any] | None,
    ):
        if active_tab != INFRASTRUCTURE_TAB_VALUE:
            return (no_update,) * 4

        context = _single_scenario_render_context_from_states(
            simulation_results_state,
            metrics_state,
            active_scenario_state,
        )
        if context is None:
            return _single_scenario_infrastructure_placeholder_response()

        return _single_scenario_infrastructure_response(context)

    @app.callback(
        Output("strategy-comparison-load-profile-chart", "figure"),
        Output("smart-charging-comparison-summary-cards", "children"),
        Output("strategy-comparison-occupancy-chart", "figure"),
        Output("strategy-comparison-queue-chart", "figure"),
        Output("strategy-comparison-queue-chart-container", "style"),
        Output("strategy-comparison-queue-status", "children"),
        Output("strategy-comparison-queue-status", "style"),
        Output("charging-performance-comparison-table", "children"),
        Output("strategy-comparison-pq-risk-chart", "figure"),
        Output("power-quality-comparison-status", "children"),
        Output("power-quality-comparison-status", "style"),
        Output("power-quality-comparison-table", "children"),
        Output("detailed-comparison-table", "children"),
        Input("active-simulation-results-store", "data"),
        Input("active-metrics-store", "data"),
        Input("dashboard-tabs", "value"),
        State("active-scenario-store", "data"),
    )
    def render_smart_charging_tab(
        simulation_results_state: dict[str, dict[str, Any]] | None,
        metrics_state: dict[str, Any] | None,
        active_tab: str,
        active_scenario_state: dict[str, Any] | None,
    ):
        if active_tab != SMART_CHARGING_TAB_VALUE:
            return (no_update,) * 13

        context = _single_scenario_render_context_from_states(
            simulation_results_state,
            metrics_state,
            active_scenario_state,
        )
        if context is None:
            return _single_scenario_smart_charging_placeholder_response()

        return _single_scenario_smart_charging_response(context)

    @app.callback(
        Output("grid-loading-kpi-cards", "children"),
        Output("grid-loading-status", "children"),
        Output("transformer-loading-chart", "figure"),
        Output("feeder-summary-section", "children"),
        Output("power-capacity-chart", "figure"),
        Input("active-simulation-results-store", "data"),
        Input("active-metrics-store", "data"),
        Input("dashboard-tabs", "value"),
        State("active-scenario-store", "data"),
    )
    def render_grid_capacity_tab(
        simulation_results_state: dict[str, dict[str, Any]] | None,
        metrics_state: dict[str, Any] | None,
        active_tab: str,
        active_scenario_state: dict[str, Any] | None,
    ):
        if active_tab != GRID_CAPACITY_TAB_VALUE:
            return (no_update,) * 5

        context = _single_scenario_render_context_from_states(
            simulation_results_state,
            metrics_state,
            active_scenario_state,
        )
        if context is None:
            return _single_scenario_grid_capacity_placeholder_response()

        return _single_scenario_grid_capacity_response(context)

    @app.callback(
        Output("power-quality-kpi-cards", "children"),
        Output("power-quality-status", "children"),
        Output("harmonic-risk-chart", "figure"),
        Output("current-imbalance-chart", "figure"),
        Output("phase-load-chart", "figure"),
        Input("active-simulation-results-store", "data"),
        Input("active-metrics-store", "data"),
        Input("dashboard-tabs", "value"),
        State("active-scenario-store", "data"),
    )
    def render_power_quality_tab(
        simulation_results_state: dict[str, dict[str, Any]] | None,
        metrics_state: dict[str, Any] | None,
        active_tab: str,
        active_scenario_state: dict[str, Any] | None,
    ):
        if active_tab != POWER_QUALITY_TAB_VALUE:
            return (no_update,) * 5

        context = _single_scenario_render_context_from_states(
            simulation_results_state,
            metrics_state,
            active_scenario_state,
        )
        if context is None:
            return _single_scenario_power_quality_placeholder_response()

        return _single_scenario_power_quality_response(context)

    @app.callback(
        Output("capacity-sensitivity-table", "children"),
        Input("active-capacity-sensitivity-store", "data"),
        Input("active-simulation-results-store", "data"),
        Input("active-metrics-store", "data"),
        Input("single-scenario-run-status-store", "data"),
        Input("dashboard-tabs", "value"),
    )
    def render_connection_capacity_sensitivity(
        sensitivity_state: list[dict[str, Any]] | None,
        simulation_results_state: dict[str, dict[str, Any]] | None,
        metrics_state: dict[str, Any] | None,
        run_status_state: dict[str, Any] | None,
        active_tab: str,
    ):
        if active_tab != GRID_CAPACITY_TAB_VALUE:
            return no_update

        if sensitivity_state is not None:
            sensitivity_rows = [
                capacity_alternative_metrics_from_dict(row)
                for row in sensitivity_state
            ]
            active_metrics = (
                metrics_from_dict(metrics_state["active"])
                if metrics_state is not None and metrics_state.get("active") is not None
                else None
            )
            return render_connection_capacity_sensitivity_table(
                sensitivity_rows,
                configured_capacity_kw=(
                    active_metrics.configured_connection_capacity_kw
                    if active_metrics is not None
                    else None
                ),
                recommended_capacity_kw=(
                    active_metrics.recommended_connection_capacity_kw
                    if active_metrics is not None
                    else None
                ),
            )

        normalized_run_status = _normalize_single_scenario_run_status_state(
            run_status_state
        )
        if (
            simulation_results_state is not None
            and metrics_state is not None
            and active_tab == GRID_CAPACITY_TAB_VALUE
            and normalized_run_status["status"] == "up_to_date"
        ):
            return DEFAULT_CAPACITY_SENSITIVITY_LOADING_MESSAGE

        return DEFAULT_CAPACITY_SENSITIVITY_MESSAGE

    @app.callback(
        Output("scenario-comparison-store", "data"),
        Output("scenario-comparison-status", "children"),
        Output("modified-copy-builder-action", "style"),
        Output("scenario-b-template-section", "style"),
        Output("scenario-b-editor-section", "style"),
        Output("scenario-b-vehicles-input", "value"),
        Output("scenario-b-charger-count-input", "value"),
        Output("scenario-b-charger-power-input", "value"),
        Output("scenario-b-grid-capacity-input", "value"),
        Output("scenario-b-validation-message", "children"),
        Input("active-scenario-store", "data"),
        Input("comparison-source-selector", "value"),
        Input("duplicate-scenario-b-button", "n_clicks"),
        Input("scenario-b-template-selector", "value"),
        Input("scenario-b-vehicles-input", "value"),
        Input("scenario-b-charger-count-input", "value"),
        Input("scenario-b-charger-power-input", "value"),
        Input("scenario-b-grid-capacity-input", "value"),
        State("scenario-comparison-store", "data"),
        prevent_initial_call=True,
    )
    def manage_scenario_b_state(
        active_scenario_state: dict[str, Any] | None,
        comparison_source: str,
        _n_clicks: int,
        scenario_b_template_id: str | None,
        scenario_b_vehicles: Any,
        scenario_b_charger_count: Any,
        scenario_b_charger_power: Any,
        scenario_b_grid_capacity: Any,
        comparison_state: dict[str, dict[str, Any]] | None,
    ):
        triggered_id = _callbacks_module().ctx.triggered_id
        resolved_comparison_source = comparison_source or COMPARISON_SOURCE_MODIFIED_COPY
        resolved_template_id = _resolved_template_id(scenario_b_template_id)
        (
            duplicate_action_style,
            template_section_style,
            hidden_editor_style,
        ) = _comparison_builder_styles(
            resolved_comparison_source,
            show_editor=False,
        )
        (
            visible_duplicate_action_style,
            hidden_template_style,
            visible_editor_style,
        ) = _comparison_builder_styles(
            COMPARISON_SOURCE_MODIFIED_COPY,
            show_editor=True,
        )
        if triggered_id == "active-scenario-store":
            if active_scenario_state is None:
                return (
                    None,
                    DEFAULT_SCENARIO_COMPARISON_STATUS,
                    duplicate_action_style,
                    template_section_style,
                    hidden_editor_style,
                    None,
                    None,
                    None,
                    None,
                    "",
                )

            if comparison_state is not None:
                next_state = update_scenario_a_in_comparison_data(
                    comparison_state,
                    active_scenario_from_state(active_scenario_state),
                )
            else:
                next_state = _callbacks_module().create_scenario_comparison_state(
                    active_scenario_state,
                    comparison_source=resolved_comparison_source,
                    selected_template=(
                        resolved_template_id
                        if resolved_comparison_source == COMPARISON_SOURCE_TEMPLATE
                        else None
                    ),
                )

            if resolved_comparison_source == COMPARISON_SOURCE_TEMPLATE:
                status_message = (
                    _template_comparison_status(resolved_template_id)
                    if comparison_state is None
                    else _stale_comparison_status(COMPARISON_SOURCE_TEMPLATE)
                )
                return (
                    next_state,
                    status_message,
                    duplicate_action_style,
                    template_section_style,
                    hidden_editor_style,
                    None,
                    None,
                    None,
                    None,
                    "",
                )

            return (
                next_state,
                (
                    DEFAULT_SCENARIO_COMPARISON_STATUS
                    if comparison_state is None
                    else _stale_comparison_status(COMPARISON_SOURCE_MODIFIED_COPY)
                ),
                visible_duplicate_action_style,
                hidden_template_style,
                visible_editor_style,
                *(_scenario_b_editor_values(next_state)),
                "",
            )

        if triggered_id == "comparison-source-selector":
            if active_scenario_state is None:
                return (
                    None,
                    DEFAULT_SCENARIO_COMPARISON_STATUS,
                    duplicate_action_style,
                    template_section_style,
                    hidden_editor_style,
                    None,
                    None,
                    None,
                    None,
                    "",
                )

            if resolved_comparison_source == COMPARISON_SOURCE_TEMPLATE:
                next_state = _callbacks_module().create_scenario_comparison_state(
                    active_scenario_state,
                    comparison_source=COMPARISON_SOURCE_TEMPLATE,
                    selected_template=resolved_template_id,
                )
                return (
                    next_state,
                    _template_comparison_status(resolved_template_id),
                    duplicate_action_style,
                    template_section_style,
                    hidden_editor_style,
                    None,
                    None,
                    None,
                    None,
                    "",
                )

            next_state = _callbacks_module().create_scenario_comparison_state(
                active_scenario_state,
                comparison_source=COMPARISON_SOURCE_MODIFIED_COPY,
            )
            return (
                next_state,
                DEFAULT_SCENARIO_COMPARISON_STATUS,
                visible_duplicate_action_style,
                hidden_template_style,
                visible_editor_style,
                *(_scenario_b_editor_values(next_state)),
                "",
            )

        if triggered_id == "duplicate-scenario-b-button":
            if active_scenario_state is None:
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    "",
                )

            next_state = _callbacks_module().create_scenario_comparison_state(
                active_scenario_state,
                comparison_source=COMPARISON_SOURCE_MODIFIED_COPY,
            )
            return (
                next_state,
                DEFAULT_SCENARIO_COMPARISON_STATUS,
                visible_duplicate_action_style,
                hidden_template_style,
                visible_editor_style,
                *(_scenario_b_editor_values(next_state)),
                "",
            )

        if triggered_id == "scenario-b-template-selector":
            if (
                active_scenario_state is None
                or resolved_comparison_source != COMPARISON_SOURCE_TEMPLATE
            ):
                return (
                    no_update,
                    no_update,
                    duplicate_action_style,
                    template_section_style,
                    hidden_editor_style,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    "",
                )

            next_state = _callbacks_module().create_scenario_comparison_state(
                active_scenario_state,
                comparison_source=COMPARISON_SOURCE_TEMPLATE,
                selected_template=resolved_template_id,
            )
            return (
                next_state,
                _template_comparison_status(resolved_template_id),
                duplicate_action_style,
                template_section_style,
                hidden_editor_style,
                None,
                None,
                None,
                None,
                "",
            )

        if triggered_id not in SCENARIO_B_INPUT_IDS or comparison_state is None:
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        try:
            next_state = _callbacks_module().update_scenario_comparison_state_for_b_edits(
                comparison_state,
                vehicles=scenario_b_vehicles,
                charger_count=scenario_b_charger_count,
                charger_power=scenario_b_charger_power,
                grid_capacity=scenario_b_grid_capacity,
            )
        except (TypeError, ValueError) as exc:
            return (
                no_update,
                no_update,
                visible_duplicate_action_style,
                hidden_template_style,
                visible_editor_style,
                no_update,
                no_update,
                no_update,
                no_update,
                str(exc),
            )

        if next_state == comparison_state:
            return (
                no_update,
                no_update,
                visible_duplicate_action_style,
                hidden_template_style,
                visible_editor_style,
                no_update,
                no_update,
                no_update,
                no_update,
                "",
            )

        return (
            next_state,
            DEFAULT_SCENARIO_COMPARISON_STATUS,
            visible_duplicate_action_style,
            hidden_template_style,
            visible_editor_style,
            no_update,
            no_update,
            no_update,
            no_update,
            "",
        )

    @app.callback(
        Output("scenario-comparison-builder-ui-store", "data"),
        Output("scenario-comparison-edit-scroll-trigger", "data"),
        Input("run-scenario-ab-comparison-button", "n_clicks"),
        Input("rerun-scenario-ab-comparison-button", "n_clicks"),
        Input("edit-scenario-comparison-button", "n_clicks"),
        Input("scenario-comparison-run-status-store", "data"),
        State("scenario-comparison-builder-ui-store", "data"),
        State("scenario-comparison-edit-scroll-trigger", "data"),
        State("scenario-comparison-store", "data"),
        prevent_initial_call=True,
    )
    def update_scenario_comparison_builder_ui_state(
        _run_clicks: int,
        _rerun_clicks: int,
        _edit_clicks: int,
        run_status_state: dict[str, Any] | None,
        builder_ui_state: dict[str, Any] | None,
        edit_scroll_trigger: int | None,
        comparison_state: dict[str, dict[str, Any]] | None,
    ):
        normalized_state = _normalize_scenario_comparison_builder_ui_state(
            builder_ui_state
        )
        normalized_run_status = _normalize_scenario_comparison_run_status_state(
            run_status_state
        )
        next_scroll_trigger = int(edit_scroll_trigger or 0)
        if _callbacks_module().ctx.triggered_id == "edit-scenario-comparison-button":
            return (
                {
                    "collapsed": False,
                    "has_run": normalized_state["has_run"],
                },
                next_scroll_trigger + 1,
            )

        if _callbacks_module().ctx.triggered_id in {
            "run-scenario-ab-comparison-button",
            "rerun-scenario-ab-comparison-button",
        }:
            if comparison_state is None:
                return no_update, no_update

            return (
                {
                    "collapsed": True,
                    "has_run": True,
                },
                no_update,
            )

        if _callbacks_module().ctx.triggered_id == "scenario-comparison-run-status-store":
            if normalized_run_status["status"] == "not_run" and normalized_state["has_run"]:
                return (
                    {
                        "collapsed": False,
                        "has_run": False,
                    },
                    no_update,
                )

            if normalized_run_status["status"] == "error":
                return (
                    {
                        "collapsed": False,
                        "has_run": normalized_state["has_run"],
                    },
                    no_update,
                )

            if normalized_run_status["status"] != "up_to_date":
                return no_update, no_update

            return (
                {
                    "collapsed": True,
                    "has_run": True,
                },
                no_update,
            )

        return no_update, no_update

    @app.callback(
        Output("scenario-ab-simulation-results-store", "data"),
        Output("scenario-ab-metrics-store", "data"),
        Output("scenario-ab-difference-metrics-store", "data"),
        Output("scenario-comparison-run-status-store", "data"),
        Output("scenario-ab-simulation-status", "children"),
        Input("run-scenario-ab-comparison-button", "n_clicks"),
        Input("rerun-scenario-ab-comparison-button", "n_clicks"),
        Input("active-scenario-store", "data"),
        Input("scenario-comparison-store", "data"),
        Input("active-metrics-store", "data"),
        Input("single-scenario-run-status-store", "data"),
        State("scenario-comparison-run-status-store", "data"),
        State("scenario-ab-metrics-store", "data"),
        State("scenario-ab-difference-metrics-store", "data"),
        running=[
            (Output("run-scenario-ab-comparison-button", "disabled"), True, False),
            (Output("rerun-scenario-ab-comparison-button", "disabled"), True, False),
        ],
        prevent_initial_call=True,
    )
    def run_scenario_ab_comparison(
        _n_clicks: int,
        _rerun_clicks: int,
        active_scenario_state: dict[str, Any] | None,
        comparison_state: dict[str, dict[str, Any]] | None,
        _active_metrics_state: dict[str, Any] | None,
        single_scenario_run_status_state: dict[str, Any] | None,
        run_status_state: dict[str, Any] | None,
        current_metrics_state: dict[str, dict[str, Any]] | None,
        current_difference_metrics_state: dict[str, Any] | None,
    ):
        has_previous_results = (
            current_metrics_state is not None
            and current_difference_metrics_state is not None
        )
        normalized_run_status = _normalize_scenario_comparison_run_status_state(
            run_status_state
        )
        normalized_single_scenario_run_status = (
            _normalize_single_scenario_run_status_state(single_scenario_run_status_state)
        )
        current_baseline_snapshot = normalized_run_status[
            "baseline_active_scenario_state"
        ]

        if _callbacks_module().ctx.triggered_id in {
            "active-metrics-store",
            "single-scenario-run-status-store",
        }:
            if (
                not has_previous_results
                or normalized_single_scenario_run_status["status"] != "up_to_date"
                or normalized_run_status["stale_reason"] != "scenario_a_changed"
                or current_baseline_snapshot is None
                or active_scenario_state is None
                or current_baseline_snapshot == active_scenario_state
            ):
                return (
                    no_update,
                    no_update,
                    no_update,
                    normalized_run_status,
                    no_update,
                )

            return (
                None,
                None,
                None,
                {
                    "status": "not_run",
                    "stale_reason": None,
                    "baseline_active_scenario_state": None,
                },
                DEFAULT_SCENARIO_AB_SIMULATION_STATUS,
            )

        if _callbacks_module().ctx.triggered_id == "active-scenario-store":
            if comparison_state is None or not has_previous_results:
                return (
                    no_update,
                    no_update,
                    no_update,
                    {
                        "status": "not_run",
                        "stale_reason": None,
                        "baseline_active_scenario_state": None,
                    },
                    DEFAULT_SCENARIO_AB_SIMULATION_STATUS,
                )
            return (
                no_update,
                no_update,
                no_update,
                {
                    "status": "stale",
                    "stale_reason": "scenario_a_changed",
                    "baseline_active_scenario_state": current_baseline_snapshot,
                },
                "Results out of date. Scenario A changed. Previous results remain visible until you rerun.",
            )

        if _callbacks_module().ctx.triggered_id == "scenario-comparison-store":
            if comparison_state is None or not has_previous_results:
                return (
                    no_update,
                    no_update,
                    no_update,
                    {
                        "status": "not_run",
                        "stale_reason": None,
                        "baseline_active_scenario_state": None,
                    },
                    DEFAULT_SCENARIO_AB_SIMULATION_STATUS,
                )
            return (
                no_update,
                no_update,
                no_update,
                {
                    "status": "stale",
                    "stale_reason": "scenario_b_changed",
                    "baseline_active_scenario_state": current_baseline_snapshot,
                },
                "Results out of date. Scenario B changed. Previous results remain visible until you rerun.",
            )

        if comparison_state is None:
            return (
                no_update,
                no_update,
                no_update,
                normalized_run_status,
                "Comparison not ready yet.",
            )

        try:
            (
                results_state,
                metrics_state,
                difference_metrics_state,
            ) = _callbacks_module().create_scenario_ab_comparison_run_state(
                comparison_state
            )
        except Exception:
            failure_message = (
                "Updated results could not be generated. Previous valid results are still shown."
                if has_previous_results
                else "The comparison could not be generated. Check the inputs and try again."
            )
            return (
                no_update,
                no_update,
                no_update,
                {
                    "status": "error",
                    "stale_reason": normalized_run_status["stale_reason"],
                    "baseline_active_scenario_state": current_baseline_snapshot,
                },
                failure_message,
            )

        return (
            results_state,
            metrics_state,
            difference_metrics_state,
            {
                "status": "up_to_date",
                "stale_reason": None,
                "baseline_active_scenario_state": active_scenario_state,
            },
            "Up to date.",
        )

    @app.callback(
        Output("scenario-ab-assumptions-summary", "children"),
        Input("scenario-comparison-store", "data"),
        Input("dashboard-tabs", "value"),
    )
    def render_scenario_ab_assumptions_summary(
        comparison_state: dict[str, dict[str, Any]] | None,
        active_tab: str = SCENARIO_COMPARISON_TAB_VALUE,
    ):
        if active_tab != SCENARIO_COMPARISON_TAB_VALUE:
            return no_update

        return _render_changed_assumptions_summary(comparison_state)

    @app.callback(
        Output("scenario-ab-selected-section-store", "data"),
        Input(
            {
                "type": SCENARIO_AB_SECTION_SELECT_ID_TYPE,
                "section_id": ALL,
            },
            "n_clicks",
        ),
        Input("active-scenario-store", "data"),
        Input("scenario-comparison-store", "data"),
        Input("scenario-ab-metrics-store", "data"),
        Input("scenario-ab-difference-metrics-store", "data"),
        State("scenario-ab-selected-section-store", "data"),
        State("dashboard-tabs", "value"),
        prevent_initial_call=True,
    )
    def update_scenario_ab_selected_section(
        _section_clicks: list[int],
        _active_scenario_state: dict[str, Any] | None,
        _comparison_state: dict[str, dict[str, Any]] | None,
        metrics_state: dict[str, dict[str, Any]] | None,
        difference_metrics_state: dict[str, Any] | None,
        selected_section_id: str | None,
        active_tab: str = SCENARIO_COMPARISON_TAB_VALUE,
    ):
        if active_tab != SCENARIO_COMPARISON_TAB_VALUE:
            return no_update

        triggered_id = ctx.triggered_id
        if isinstance(triggered_id, str) and triggered_id in {
            "active-scenario-store",
            "scenario-comparison-store",
        }:
            if metrics_state is None or difference_metrics_state is None:
                return None

            return selected_section_id

        if metrics_state is None or difference_metrics_state is None:
            return None

        if (
            isinstance(triggered_id, dict)
            and triggered_id.get("type") == SCENARIO_AB_SECTION_SELECT_ID_TYPE
        ):
            return triggered_id.get("section_id")

        return selected_section_id

    @app.callback(
        Output("scenario-comparison-empty-state-section", "style"),
        Output("scenario-comparison-empty-state", "children"),
        Output("scenario-ab-executive-summary-section", "style"),
        Output("scenario-ab-executive-summary-cards", "children"),
        Output("scenario-ab-comparison-table-section", "style"),
        Output("scenario-ab-comparison-table", "children"),
        Input("active-scenario-store", "data"),
        Input("scenario-comparison-store", "data"),
        Input("scenario-ab-metrics-store", "data"),
        Input("scenario-ab-difference-metrics-store", "data"),
        Input("scenario-comparison-builder-ui-store", "data"),
        Input("scenario-ab-selected-section-store", "data"),
        Input("dashboard-tabs", "value"),
    )
    def render_scenario_ab_comparison(
        active_scenario_state: dict[str, Any] | None,
        comparison_state: dict[str, dict[str, Any]] | None,
        metrics_state: dict[str, dict[str, Any]] | None,
        difference_metrics_state: dict[str, Any] | None,
        builder_ui_state: dict[str, Any] | None,
        selected_section_id: str | None,
        active_tab: str = SCENARIO_COMPARISON_TAB_VALUE,
    ):
        if active_tab != SCENARIO_COMPARISON_TAB_VALUE:
            return (no_update,) * 6

        return _build_scenario_ab_results_render_state(
            active_scenario_state,
            comparison_state,
            metrics_state,
            difference_metrics_state,
            builder_ui_state,
            selected_section_id,
        )

    @app.callback(
        Output("scenario-comparison-builder-expanded-content", "style"),
        Output("scenario-comparison-builder-collapsed-bar", "style"),
        Output("scenario-comparison-collapsed-title", "children"),
        Output("scenario-comparison-collapsed-summary", "children"),
        Output("scenario-comparison-collapsed-status", "children"),
        Output("scenario-comparison-collapsed-status", "style"),
        Input("active-scenario-store", "data"),
        Input("scenario-comparison-store", "data"),
        Input("scenario-comparison-run-status-store", "data"),
        Input("scenario-comparison-builder-ui-store", "data"),
        Input("dashboard-tabs", "value"),
    )
    def render_scenario_comparison_builder_compaction(
        active_scenario_state: dict[str, Any] | None,
        comparison_state: dict[str, dict[str, Any]] | None,
        run_status_state: dict[str, Any] | None,
        builder_ui_state: dict[str, Any] | None,
        active_tab: str = SCENARIO_COMPARISON_TAB_VALUE,
    ):
        if active_tab != SCENARIO_COMPARISON_TAB_VALUE:
            return (no_update,) * 6

        if not _scenario_comparison_builder_is_collapsed(builder_ui_state):
            return (
                dict(COMPARISON_BUILDER_EXPANDED_VISIBLE_STYLE),
                {
                    **COMPARISON_BUILDER_COLLAPSED_BAR_ROW_STYLE,
                    **COMPARISON_BUILDER_COLLAPSED_BAR_HIDDEN_STYLE,
                },
                "",
                "",
                "",
                dict(COMPARISON_BUILDER_STATUS_CHIP_BASE_STYLE, display="none"),
            )

        title, summary, status_label, status_style = (
            _render_scenario_comparison_collapsed_bar(
                active_scenario_state,
                comparison_state,
                run_status_state,
                builder_ui_state,
            )
        )
        return (
            dict(COMPARISON_BUILDER_EXPANDED_HIDDEN_STYLE),
            {
                **COMPARISON_BUILDER_COLLAPSED_BAR_ROW_STYLE,
                **COMPARISON_BUILDER_COLLAPSED_BAR_VISIBLE_STYLE,
            },
            title,
            summary,
            status_label,
            {
                **COMPARISON_BUILDER_STATUS_CHIP_BASE_STYLE,
                **status_style,
            },
        )

    @app.callback(
        Output("scenario-b-template-details", "children"),
        Input("scenario-b-template-selector", "value"),
        Input("dashboard-tabs", "value"),
    )
    def update_scenario_b_template_details(
        preset_id: str | None,
        active_tab: str = SCENARIO_COMPARISON_TAB_VALUE,
    ):
        if active_tab != SCENARIO_COMPARISON_TAB_VALUE:
            return no_update

        return render_comparison_scenario_preset_details(
            _resolved_template_id(preset_id)
        )
