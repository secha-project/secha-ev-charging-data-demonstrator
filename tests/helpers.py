from dataclasses import replace
import json
from datetime import time
from types import SimpleNamespace

from dash import no_update
import pytest

from app import create_app
import dashboard.callbacks as dashboard_callbacks_module
import dashboard.callback_registration as dashboard_callback_registration_module
from insights import generate_insights
from dashboard.callbacks import (
    ADDITIONAL_CHARGERS_NOT_APPLICABLE_HELPER,
    CHARGER_UTILIZATION_UNAVAILABLE_HELPER,
    GRAPH_HEIGHT_PX,
    GRID_CAPACITY_TAB_VALUE,
    OVERVIEW_TAB_VALUE,
    SCENARIO_COMPARISON_TAB_VALUE,
    REQUIRED_CHARGER_COUNT_NOT_APPLICABLE_HELPER,
    WAITING_TIME_UNAVAILABLE_HELPER,
    active_scenario_from_state,
    build_scenario_ab_comparison_rows,
    build_scenario_ab_charger_availability_rows,
    build_connection_capacity_comparison_rows,
    build_connection_capacity_sensitivity_rows,
    create_capacity_vs_load_figure,
    create_active_scenario,
    create_active_scenario_state,
    create_charger_occupancy_figure,
    create_comparison_occupancy_figure,
    create_comparison_power_quality_figure,
    create_comparison_queue_figure,
    create_comparison_load_profile_figure,
    create_connection_capacity_sensitivity_state,
    create_current_imbalance_figure,
    create_harmonic_risk_figure,
    create_load_profile_figure,
    create_phase_load_figure,
    create_power_capacity_over_time_figure,
    create_queue_length_figure,
    create_service_pressure_figure,
    create_scenario_ab_power_quality_figure,
    create_transformer_loading_figure,
    create_scenario_ab_occupancy_figure,
    create_scenario_ab_queue_figure,
    create_scenario_ab_transformer_loading_figure,
    create_scenario_ab_comparison_run_state,
    create_scenario_ab_simulation_results_state,
    create_scenario_comparison_state,
    create_single_scenario_run_state,
    format_annual_energy_kwh,
    format_energy_delivery_status,
    format_capacity_status,
    format_connection_capacity_exceeded_status,
    format_energy_kwh,
    format_percent,
    format_planner_status_message,
    format_percentage_points,
    format_power_kw,
    format_signed_hours,
    format_signed_power_kw,
    format_signed_percentage_points,
    format_signed_score_points,
    format_scenario_status,
    render_capacity_planning_kpi_cards,
    render_charger_availability_kpi_cards,
    render_charging_performance_comparison_table,
    render_charger_planning_status,
    render_comparison_kpi_cards,
    render_connection_capacity_sensitivity_table,
    render_detailed_comparison_table,
    render_feeder_summary_section,
    render_grid_asset_planning_status,
    render_grid_loading_kpi_cards,
    render_grid_loading_status,
    render_infrastructure_summary,
    render_insights,
    render_power_quality_comparison_table,
    render_power_quality_kpi_cards,
    render_power_quality_status,
    render_scenario_preset_details,
    render_scenario_ab_charger_availability_table,
    render_scenario_ab_detailed_sections,
    render_scenario_ab_executive_summary_cards,
    render_scenario_ab_comparison_table,
    _smart_charging_power_quality_status_state,
    _smart_charging_queue_evidence_state,
    _normalize_single_scenario_run_status_state,
    _coerce_sidebar_field_value,
    _resolve_scenario_ab_display_labels,
    _scenario_builder_status_message_state,
    _sidebar_field_values_from_active_state,
    update_scenario_comparison_state_for_b_edits,
)
from dashboard.sidebar import (
    SCENARIO_SIDEBAR_CATEGORY_ORDER,
    SCENARIO_SIDEBAR_FIELD_DEFINITIONS,
    SCENARIO_SIDEBAR_VISIBLE_FIELD_NAMES,
    get_sidebar_advanced_field_definitions,
    get_sidebar_primary_field_definitions,
    get_sidebar_visible_field_definitions,
)
from metrics import (
    CapacityAlternativeMetrics,
    calculate_comparison_metrics,
    ComparisonMetrics,
    FeederSummaryMetrics,
    Metrics,
    ScenarioComparisonMetrics,
    capacity_alternative_metrics_from_dict,
    calculate_metrics,
    metrics_from_dict,
    metrics_to_dict,
    run_connection_capacity_sensitivity,
    scenario_comparison_metrics_from_dict,
)
from metrics.scenario_comparison_display import (
    SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT,
    SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL,
    SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF,
    ScenarioComparisonDisplayMetric,
    prepare_scenario_comparison_display_data,
)
from scenarios import (
    ACTIVE_SCENARIO_STATE_SCHEMA_VERSION,
    ArrivalMode,
    ChargingStrategy,
    COMPARISON_SOURCE_MODIFIED_COPY,
    COMPARISON_SOURCE_TEMPLATE,
    DEFAULT_SCENARIO_PRESET_ID,
    DepartureMode,
    PUBLIC_FAST_CHARGING_PRESET_ID,
    Scenario,
    WORKPLACE_CHARGING_PRESET_ID,
    apply_preset_defaults_to_active_scenario_state,
    create_internal_scenario,
    default_scenario,
    get_scenario_preset,
    scenario_to_dict,
    update_scenario_b_in_comparison_data,
    update_active_scenario_parameters,
    update_scenario_a_in_comparison_data,
)
from scenarios.presets import (
    CHARGER_LIMITED_DEPOT_PRESET_ID,
    CONCENTRATED_ARRIVAL_WORKPLACE_CHARGING_PRESET_ID,
    CONSTRAINED_HEAVY_DUTY_PEAK_SHAVING_PRESET_ID,
    PQ_SENSITIVE_AC_CHARGING_PRESET_ID,
)
from simulation import (
    SimulationResult,
    get_time_labels,
    simulate,
    simulate_strategy_comparison,
    simulation_result_from_dict,
    simulation_result_to_dict,
)


def _collect_text(component):
    if isinstance(component, str):
        return [component]

    if isinstance(component, (list, tuple)):
        text = []
        for child in component:
            text.extend(_collect_text(child))
        return text

    if hasattr(component, "children"):
        return _collect_text(component.children)

    return []


def _collect_immediate_child_text(component):
    children = getattr(component, "children", None)
    if children is None:
        return []

    if not isinstance(children, (list, tuple)):
        children = [children]

    return [" ".join(_collect_text(child)) for child in children]


def _find_component_by_id(component, component_id):
    if getattr(component, "id", None) == component_id:
        return component

    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            result = _find_component_by_id(child, component_id)
            if result is not None:
                return result
    elif children is not None:
        return _find_component_by_id(children, component_id)

    return None


def _unwrap_loading_child(component):
    if component.__class__.__name__ != "Loading":
        return component

    return component.children


def _find_component_by_title(component, title):
    if isinstance(component, (list, tuple)):
        for child in component:
            result = _find_component_by_title(child, title)
            if result is not None:
                return result
        return None

    if getattr(component, "title", None) == title:
        return component

    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            result = _find_component_by_title(child, title)
            if result is not None:
                return result
    elif children is not None:
        return _find_component_by_title(children, title)

    return None


def _find_component_by_class_name(component, class_name):
    if isinstance(component, (list, tuple)):
        for child in component:
            result = _find_component_by_class_name(child, class_name)
            if result is not None:
                return result
        return None

    if getattr(component, "className", None) == class_name:
        return component

    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            result = _find_component_by_class_name(child, class_name)
            if result is not None:
                return result
    elif children is not None:
        return _find_component_by_class_name(children, class_name)

    return None


def _find_components_by_class_name(component, class_name):
    matches = []

    if isinstance(component, (list, tuple)):
        for child in component:
            matches.extend(_find_components_by_class_name(child, class_name))
        return matches

    component_class_name = getattr(component, "className", None)
    if isinstance(component_class_name, str):
        component_class_names = component_class_name.split()
        if class_name in component_class_names:
            matches.append(component)

    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            matches.extend(_find_components_by_class_name(child, class_name))
    elif children is not None:
        matches.extend(_find_components_by_class_name(children, class_name))

    return matches


def _component_contains_descendant_with_id(component, component_id):
    return _find_component_by_id(component, component_id) is not None


def _find_tab_by_value(tabs, value):
    return next(tab for tab in tabs.children if tab.value == value)


def _callback_output_nodes(callback_key):
    return [
        output_fragment.strip(".")
        for output_fragment in callback_key.split("...")
        if output_fragment.strip(".")
    ]


def _callback_input_nodes(callback_entry):
    return [
        f"{item['id']}.{item['property']}"
        for item in callback_entry["inputs"]
    ]


def _find_callback_function(app, output_fragment):
    callback_key = next(
        key for key in app.callback_map if output_fragment in key
    )
    callback = app.callback_map[callback_key]["callback"]
    return getattr(callback, "__wrapped__", callback)


def _normalize_dashboard_output(value):
    if hasattr(value, "to_plotly_json"):
        return _normalize_dashboard_output(value.to_plotly_json())

    if isinstance(value, dict):
        return {
            key: _normalize_dashboard_output(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _normalize_dashboard_output(item)
            for item in value
        ]

    return value


def _create_legacy_single_scenario_run_state(active_scenario_state):
    active_scenario = active_scenario_from_state(active_scenario_state)
    uncontrolled_result, smart_result = simulate_strategy_comparison(
        active_scenario
    )
    uncontrolled_metrics = calculate_metrics(
        uncontrolled_result,
        active_scenario,
    )
    smart_metrics = calculate_metrics(
        smart_result,
        active_scenario,
    )
    if active_scenario.charging_strategy == ChargingStrategy.UNCONTROLLED:
        simulation_result = uncontrolled_result
        metrics = uncontrolled_metrics
    else:
        simulation_result = smart_result
        metrics = smart_metrics
    comparison_metrics = calculate_comparison_metrics(
        uncontrolled_metrics,
        smart_metrics,
    )
    insights = generate_insights(
        metrics,
        active_scenario.charging_strategy,
        comparison_metrics,
    )

    return (
        {
            "active": simulation_result_to_dict(simulation_result),
            "uncontrolled": simulation_result_to_dict(uncontrolled_result),
            "smart": simulation_result_to_dict(smart_result),
        },
        {
            "active": metrics_to_dict(metrics),
            "uncontrolled": metrics_to_dict(uncontrolled_metrics),
            "smart": metrics_to_dict(smart_metrics),
            "comparison": dashboard_callbacks_module._comparison_metrics_to_dict(
                comparison_metrics
            ),
            "insights": list(insights),
        },
    )


def _create_legacy_single_scenario_render_sections(active_scenario_state):
    simulation_results_state, metrics_state = _create_legacy_single_scenario_run_state(
        active_scenario_state
    )
    active_scenario = active_scenario_from_state(active_scenario_state)
    simulation_result = simulation_result_from_dict(
        simulation_results_state["active"]
    )
    uncontrolled_result = simulation_result_from_dict(
        simulation_results_state["uncontrolled"]
    )
    smart_result = simulation_result_from_dict(
        simulation_results_state["smart"]
    )
    metrics = metrics_from_dict(metrics_state["active"])
    uncontrolled_metrics = metrics_from_dict(metrics_state["uncontrolled"])
    smart_metrics = metrics_from_dict(metrics_state["smart"])
    comparison_metrics = dashboard_callbacks_module._comparison_metrics_from_dict(
        metrics_state["comparison"]
    )
    (
        queue_chart_container_style,
        queue_status_children,
        queue_status_style,
    ) = dashboard_callbacks_module._smart_charging_queue_evidence_state(
        comparison_metrics
    )
    (
        power_quality_status_children,
        power_quality_status_style,
    ) = dashboard_callbacks_module._smart_charging_power_quality_status_state(
        comparison_metrics
    )

    return {
        "summary": (
            format_energy_kwh(metrics.total_daily_energy),
            format_power_kw(metrics.available_capacity),
            format_power_kw(metrics.peak_load),
            format_percent(metrics.capacity_utilization),
            format_energy_kwh(metrics.delivered_energy),
            format_energy_kwh(metrics.unmet_energy),
            format_energy_kwh(metrics.total_daily_energy),
            format_annual_energy_kwh(metrics.annual_energy),
            format_scenario_status(metrics),
            render_insights(list(metrics_state["insights"])),
        ),
        "overview": create_capacity_vs_load_figure(
            simulation_result,
            metrics,
        ),
        "infrastructure": (
            render_infrastructure_summary(metrics, active_scenario),
            render_capacity_planning_kpi_cards(metrics, simulation_result),
            render_charger_availability_kpi_cards(metrics),
            create_service_pressure_figure(metrics, active_scenario),
        ),
        "grid_capacity": (
            render_grid_loading_kpi_cards(metrics),
            render_grid_loading_status(metrics),
            create_transformer_loading_figure(metrics),
            render_feeder_summary_section(metrics),
            create_power_capacity_over_time_figure(simulation_result),
        ),
        "power_quality": (
            render_power_quality_kpi_cards(metrics),
            render_power_quality_status(metrics),
            create_harmonic_risk_figure(metrics),
            create_current_imbalance_figure(metrics),
            create_phase_load_figure(metrics),
        ),
        "smart_charging": (
            create_comparison_load_profile_figure(uncontrolled_result, smart_result),
            render_comparison_kpi_cards(
                comparison_metrics,
                uncontrolled_metrics,
                smart_metrics,
            ),
            create_comparison_occupancy_figure(comparison_metrics),
            create_comparison_queue_figure(comparison_metrics),
            queue_chart_container_style,
            queue_status_children,
            queue_status_style,
            render_charging_performance_comparison_table(comparison_metrics),
            create_comparison_power_quality_figure(comparison_metrics),
            power_quality_status_children,
            power_quality_status_style,
            render_power_quality_comparison_table(comparison_metrics),
            render_detailed_comparison_table(
                uncontrolled_metrics,
                smart_metrics,
            ),
        ),
    }


def _extract_section_titles(tab_panel):
    titles = []
    for section in _extract_dashboard_widget_sections(tab_panel):
        children = getattr(section, "children", None)
        if not isinstance(children, (list, tuple)) or not children:
            continue
        heading = children[0]
        if getattr(heading, "children", None) is None:
            continue
        titles.append(heading.children)
    return titles


def _extract_dashboard_widget_sections(tab_panel):
    sections = []
    for child in tab_panel.children:
        class_name = getattr(child, "className", "")
        if isinstance(class_name, str) and "dashboard-region" in class_name:
            region_children = getattr(child, "children", None)
            if isinstance(region_children, (list, tuple)):
                sections.extend(region_children)
            elif region_children is not None:
                sections.append(region_children)
            continue

        sections.append(child)

    return sections


def _build_single_scenario_dashboard_slice(
    scenario: Scenario,
) -> tuple[
    SimulationResult,
    Metrics,
    list[str],
    list[str],
    list[str],
    list[str],
    object,
    object,
]:
    """Run the single-scenario workflow through simulation, metrics, and views."""
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)
    cards_text = _collect_text(
        render_capacity_planning_kpi_cards(metrics, simulation_result)
    )
    charger_availability_cards_text = _collect_text(
        render_charger_availability_kpi_cards(metrics)
    )
    status_text = _collect_text(format_scenario_status(metrics))
    charger_planning_status_text = _collect_text(
        render_charger_planning_status(metrics, scenario)
    )
    capacity_vs_load_figure = create_capacity_vs_load_figure(
        simulation_result,
        metrics,
    )
    load_profile_figure = create_load_profile_figure(simulation_result.load_profile)
    return (
        simulation_result,
        metrics,
        cards_text,
        charger_availability_cards_text,
        status_text,
        charger_planning_status_text,
        capacity_vs_load_figure,
        load_profile_figure,
    )


def _build_reference_grid_loading_scenario(
    *,
    vehicles: int = 1,
    charger_count: int = 1,
    charger_power: float = 100.0,
    grid_capacity: float = 100.0,
    transformer_capacity_kw: float = 150.0,
    transformer_other_load_kw: float = 20.0,
    feeder_count: int = 1,
    feeder_capacity_kw: float = 140.0,
    feeder_base_load_kw: float = 10.0,
    charging_window_end: time = time(8, 15),
    charging_strategy: ChargingStrategy = ChargingStrategy.UNCONTROLLED,
) -> Scenario:
    """Return a compact deterministic scenario for dashboard regressions."""
    return create_internal_scenario(
        vehicles=vehicles,
        daily_energy_per_vehicle=25.0,
        charger_count=charger_count,
        charger_power=charger_power,
        grid_capacity=grid_capacity,
        transformer_capacity_kw=transformer_capacity_kw,
        transformer_other_load_kw=transformer_other_load_kw,
        feeder_count=feeder_count,
        feeder_capacity_kw=feeder_capacity_kw,
        feeder_base_load_kw=feeder_base_load_kw,
        charging_window_start=time(8, 0),
        charging_window_end=charging_window_end,
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        charging_strategy=charging_strategy,
    )



__all__ = [name for name in globals() if not name.startswith('__')]

