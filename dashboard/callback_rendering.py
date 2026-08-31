"""Compatibility facade for dashboard rendering helpers and callback outputs."""

from .rendering import (
    _shared as _shared,
    figures as _figures,
    formatters as _formatters,
    infrastructure as _infrastructure,
    overview as _overview,
    scenario_comparison as _scenario_comparison,
    smart_charging as _smart_charging,
)
from .rendering._shared import *
from .rendering.figures import *
from .rendering.formatters import *
from .rendering.infrastructure import *
from .rendering.overview import *
from .rendering.scenario_comparison import *
from .rendering.smart_charging import *
from . import state as _state
from .state import *

def _input_validation_status(validation_message: str) -> Any:
    """Render a concise validation message in the scenario status area."""
    return html.Div(
        [
            html.Strong("Input required"),
            html.P(validation_message),
        ]
    )

def _simulation_input_error_response(validation_message: str) -> tuple[Any, ...]:
    """Return callback outputs for a blocked simulation run."""
    return (
        (no_update,) * 18
        + (_input_validation_status(validation_message),)
        + (no_update,) * 19
    )

def _single_scenario_summary_placeholder_response() -> tuple[Any, ...]:
    """Return placeholder outputs for the small always-on summary callback."""

    return (
        "",
        "Not run yet",
        "Not run yet",
        "Not run yet",
        "",
        "Not run yet",
        "",
        "",
        DEFAULT_SCENARIO_STATUS_MESSAGE,
        create_default_simulation_insights_list(),
    )

def _single_scenario_summary_response(
    metrics: Metrics,
    insights: tuple[str, ...],
    *,
    run_status_state: dict[str, Any] | None = None,
) -> tuple[Any, ...]:
    """Return the lightweight single-scenario summary outputs."""

    normalized_run_status = _normalize_single_scenario_run_status_state(
        run_status_state
    )
    scenario_status = format_scenario_status(metrics)
    if normalized_run_status["status"] == "stale":
        scenario_status = html.Div(
            [
                create_compact_status_message(
                    "Results shown below are out of date. Inputs changed - rerun simulation to refresh them."
                ),
                scenario_status,
            ],
            style={"display": "grid", "gap": "0.75rem"},
        )

    return (
        format_energy_kwh(metrics.total_daily_energy),
        format_power_kw(metrics.available_capacity),
        format_power_kw(metrics.peak_load),
        format_percent(metrics.capacity_utilization),
        format_energy_kwh(metrics.delivered_energy),
        format_energy_kwh(metrics.unmet_energy),
        format_energy_kwh(metrics.total_daily_energy),
        format_annual_energy_kwh(metrics.annual_energy),
        scenario_status,
        render_insights(list(insights)),
    )

def _single_scenario_overview_placeholder_response() -> tuple[Any, ...]:
    """Return the Overview placeholder state when no run is available."""

    return (
        {},
        _default_overview_kpi_cards(),
        _default_overview_smart_charging_preview_children(),
    )

def _single_scenario_overview_response(
    context: _SingleScenarioRenderContext,
) -> tuple[Any, ...]:
    """Return the Overview executive-summary outputs for one completed run."""

    display_data = prepare_overview_display_data(
        context.active_scenario,
        context.metrics,
        context.uncontrolled_metrics,
        context.smart_metrics,
        context.comparison_metrics,
    )
    return (
        create_capacity_vs_load_figure(
            context.simulation_result,
            context.metrics,
        ),
        render_overview_kpi_cards(display_data),
        render_overview_smart_charging_preview(display_data.smart_charging_preview),
    )

def _single_scenario_infrastructure_placeholder_response() -> tuple[Any, ...]:
    """Return Infrastructure placeholders when no run is available."""

    return (
        create_default_infrastructure_summary_children(),
        create_default_capacity_planning_cards(),
        create_default_charger_availability_cards(),
        {},
    )

def _single_scenario_infrastructure_response(
    context: _SingleScenarioRenderContext,
) -> tuple[Any, ...]:
    """Return Infrastructure outputs for one completed run."""

    return (
        render_infrastructure_summary(context.metrics, context.active_scenario),
        render_capacity_planning_kpi_cards(
            context.metrics,
            context.simulation_result,
        ),
        render_charger_availability_kpi_cards(context.metrics),
        create_service_pressure_figure(
            context.metrics,
            context.active_scenario,
        ),
    )

def _single_scenario_grid_capacity_placeholder_response() -> tuple[Any, ...]:
    """Return Grid & Capacity placeholders when no run is available."""

    return (
        create_default_grid_loading_cards(),
        DEFAULT_GRID_LOADING_MESSAGE,
        {},
        DEFAULT_GRID_LOADING_MESSAGE,
        {},
    )

def _single_scenario_grid_capacity_response(
    context: _SingleScenarioRenderContext,
) -> tuple[Any, ...]:
    """Return Grid & Capacity outputs for one completed run."""

    return (
        render_grid_loading_kpi_cards(context.metrics),
        render_grid_loading_status(context.metrics),
        create_transformer_loading_figure(context.metrics),
        render_feeder_summary_section(context.metrics),
        create_power_capacity_over_time_figure(context.simulation_result),
    )

def _single_scenario_power_quality_placeholder_response() -> tuple[Any, ...]:
    """Return Power Quality placeholders when no run is available."""

    return (
        create_default_power_quality_cards(),
        create_default_power_quality_status_children(),
        {},
        {},
        {},
    )

def _single_scenario_power_quality_response(
    context: _SingleScenarioRenderContext,
) -> tuple[Any, ...]:
    """Return Power Quality outputs for one completed run."""

    return (
        render_power_quality_kpi_cards(context.metrics),
        render_power_quality_status(context.metrics),
        create_harmonic_risk_figure(context.metrics),
        create_current_imbalance_figure(context.metrics),
        create_phase_load_figure(context.metrics),
    )

def _single_scenario_smart_charging_placeholder_response() -> tuple[Any, ...]:
    """Return Smart Charging placeholders when no run is available."""

    return (
        {},
        create_default_comparison_summary_cards(),
        {},
        {},
        {},
        "",
        {"display": "none"},
        create_default_comparison_table_placeholder(
            DEFAULT_CHARGING_PERFORMANCE_COMPARISON_TEXT
        ),
        {},
        "",
        {"display": "none"},
        create_default_comparison_table_placeholder(
            DEFAULT_POWER_QUALITY_COMPARISON_TEXT
        ),
        create_default_comparison_table_placeholder(
            DEFAULT_DETAILED_COMPARISON_MESSAGE
        ),
    )

def _single_scenario_smart_charging_response(
    context: _SingleScenarioRenderContext,
) -> tuple[Any, ...]:
    """Return Smart Charging outputs for one completed run."""

    (
        queue_chart_container_style,
        queue_status_children,
        queue_status_style,
    ) = _smart_charging_queue_evidence_state(
        context.comparison_metrics
    )
    (
        power_quality_status_children,
        power_quality_status_style,
    ) = _smart_charging_power_quality_status_state(
        context.comparison_metrics
    )

    return (
        create_comparison_load_profile_figure(
            context.uncontrolled_result,
            context.smart_result,
        ),
        render_comparison_kpi_cards(
            context.comparison_metrics,
            context.uncontrolled_metrics,
            context.smart_metrics,
        ),
        create_comparison_occupancy_figure(context.comparison_metrics),
        create_comparison_queue_figure(context.comparison_metrics),
        queue_chart_container_style,
        queue_status_children,
        queue_status_style,
        render_charging_performance_comparison_table(
            context.comparison_metrics
        ),
        create_comparison_power_quality_figure(
            context.comparison_metrics
        ),
        power_quality_status_children,
        power_quality_status_style,
        render_power_quality_comparison_table(
            context.comparison_metrics
        ),
        render_detailed_comparison_table(
            context.uncontrolled_metrics,
            context.smart_metrics,
        ),
    )

def _single_scenario_placeholder_response() -> tuple[Any, ...]:
    """Return the placeholder dashboard state when no active run is available."""

    return (
        "",
        "Not run yet",
        "Not run yet",
        "Not run yet",
        "",
        "Not run yet",
        "",
        "",
        create_default_infrastructure_summary_children(),
        create_default_capacity_planning_cards(),
        create_default_charger_availability_cards(),
        create_default_grid_loading_cards(),
        DEFAULT_GRID_LOADING_MESSAGE,
        create_default_power_quality_cards(),
        create_default_power_quality_status_children(),
        DEFAULT_SCENARIO_STATUS_MESSAGE,
        create_default_charger_planning_status_children(),
        create_default_grid_asset_status_children(),
        {},
        {},
        {},
        {},
        {},
        DEFAULT_GRID_LOADING_MESSAGE,
        {},
        {},
        {},
        create_default_comparison_summary_cards(),
        {},
        {},
        {},
        "",
        {"display": "none"},
        create_default_comparison_table_placeholder(
            DEFAULT_CHARGING_PERFORMANCE_COMPARISON_TEXT
        ),
        {},
        "",
        {"display": "none"},
        create_default_comparison_table_placeholder(
            DEFAULT_POWER_QUALITY_COMPARISON_TEXT
        ),
        create_default_comparison_table_placeholder(
            DEFAULT_DETAILED_COMPARISON_MESSAGE
        ),
        create_default_simulation_insights_list(),
    )

__all__ = [
    *_shared.__all__,
    *_formatters.__all__,
    *_figures.__all__,
    *_overview.__all__,
    *_infrastructure.__all__,
    *_smart_charging.__all__,
    *_scenario_comparison.__all__,
    *_state.__all__,
    '_input_validation_status',
    '_simulation_input_error_response',
    '_single_scenario_summary_placeholder_response',
    '_single_scenario_summary_response',
    '_single_scenario_overview_placeholder_response',
    '_single_scenario_overview_response',
    '_single_scenario_infrastructure_placeholder_response',
    '_single_scenario_infrastructure_response',
    '_single_scenario_grid_capacity_placeholder_response',
    '_single_scenario_grid_capacity_response',
    '_single_scenario_power_quality_placeholder_response',
    '_single_scenario_power_quality_response',
    '_single_scenario_smart_charging_placeholder_response',
    '_single_scenario_smart_charging_response',
    '_single_scenario_placeholder_response',
]

