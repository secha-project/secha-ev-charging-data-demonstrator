"""Dashboard rendering and presentation helpers for callback outputs."""

from dataclasses import asdict, dataclass
import math
import sys
from typing import Any

from dash import dcc, html, no_update
import plotly.graph_objects as go

from metrics import (
    CapacityAlternativeMetrics,
    ComparisonMetrics,
    Metrics,
    OVERVIEW_VALUE_FORMAT_TEXT,
    SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT,
    SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL,
    SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF,
    SCENARIO_SECTION_IMPACT_NONE,
    SCENARIO_SECTION_VISUALIZATION_SUPPORTING_WHEN_USEFUL,
    SCENARIO_SECTION_SUMMARY_MAJOR_CHANGES,
    SCENARIO_SECTION_SUMMARY_TRADE_OFFS,
    SCENARIO_CHANGE_NONE,
    SCENARIO_CHANGE_NOT_APPLICABLE,
    SCENARIO_CHANGE_OPTIONAL_DELTA,
    SCENARIO_VALUE_OPTIONAL_NOT_APPLICABLE,
    SCENARIO_VALUE_OPTIONAL_UNAVAILABLE,
    ScenarioComparisonDisplayData,
    ScenarioComparisonDisplaySection,
    ScenarioComparisonExecutiveMetric,
    ScenarioComparisonHighlightItem,
    ScenarioComparisonMetrics,
    ScenarioComparisonDisplayMetric,
    ScenarioComparisonOverviewItem,
    OverviewDisplayData,
    OverviewDisplayField,
    OverviewKpiDescriptor,
    OverviewSmartChargingPreview,
    capacity_alternative_metrics_from_dict,
    capacity_alternative_metrics_to_dict,
    calculate_comparison_metrics,
    calculate_scenario_difference_metrics,
    calculate_scenario_comparison_metrics,
    metrics_from_dict,
    metrics_to_dict,
    prepare_overview_display_data,
    prepare_scenario_comparison_display_data,
    prepare_smart_charging_card_descriptors,
    scenario_comparison_metrics_from_dict,
    scenario_comparison_metrics_to_dict,
)
from scenarios import (
    ChargingStrategy,
    COMPARISON_SOURCE_MODIFIED_COPY,
    COMPARISON_SOURCE_TEMPLATE,
    Scenario,
    active_scenario_from_state as scenario_from_active_state,
    apply_preset_defaults_to_active_scenario_state,
    comparison_scenarios_from_state,
    coerce_scenario_field_value,
    default_scenario_preset,
    DepartureMode,
    create_scenario_comparison_state as create_scenario_comparison_state_from_active_state,
    get_active_scenario_is_modified,
    get_active_scenario_metadata,
    get_active_scenario_parameters,
    get_active_scenario_preset_id,
    get_scenario_preset,
    create_preset_initialized_scenario,
    scenario_b_editable_values_from_state,
    scenario_field_values_from_state,
    scenario_parameters_from_input_values,
    summarize_scenario_assumption_change_overview,
    update_scenario_b_in_comparison_state,
)
from simulation import (
    SimulationResult,
    get_time_labels,
    simulate_scenario_comparison,
    simulation_result_from_dict,
    simulation_result_to_dict,
)
from dashboard.common import (
    ACCENT_BLUE,
    BORDER_COLOR,
    CHART_GRID_COLOR,
    COMPARISON_BUILDER_ACTION_HIDDEN_STYLE,
    COMPARISON_BUILDER_ACTION_VISIBLE_STYLE,
    COMPARISON_EYEBROW_STYLE,
    DASHBOARD_WIDGET_SECTION_STYLE,
    KPI_LABEL_TEXT_STYLE,
    KPI_CARD_STYLE,
    KPI_VALUE_TEXT_STYLE,
    SCENARIO_B_EDITOR_HIDDEN_STYLE,
    SCENARIO_B_EDITOR_VISIBLE_STYLE,
    SCENARIO_B_TEMPLATE_HIDDEN_STYLE,
    SCENARIO_B_TEMPLATE_VISIBLE_STYLE,
    DEFAULT_CHARGING_PERFORMANCE_COMPARISON_TEXT,
    DEFAULT_DETAILED_COMPARISON_MESSAGE,
    GRAPH_STYLE,
    DEFAULT_GRID_LOADING_MESSAGE,
    DEFAULT_POWER_QUALITY_COMPARISON_TEXT,
    DEFAULT_SCENARIO_COMPARISON_STATUS,
    DEFAULT_SCENARIO_STATUS_MESSAGE,
    SECTION_LEAD_TEXT_STYLE,
    SECTION_TITLE_STYLE,
    SECTION_STYLE,
    SMART_CHARGING_SECTION_LEAD_STYLE,
    STATUS_AMBER,
    STATUS_AMBER_BACKGROUND,
    STATUS_BLOCK_STYLE,
    STATUS_BLUE_BACKGROUND,
    STATUS_GREEN,
    STATUS_GREEN_BACKGROUND,
    STATUS_RED,
    STATUS_RED_BACKGROUND,
    SUBSECTION_TITLE_STYLE,
    SUBTLE_SURFACE_BACKGROUND_COLOR,
    SURFACE_BACKGROUND_COLOR,
    SUPPORTING_TEXT_STYLE,
    TABLE_CELL_STYLE,
    TABLE_HEADER_CELL_STYLE,
    TABLE_STYLE,
    TEXT_PRIMARY_COLOR,
    TEXT_SECONDARY_COLOR,
    build_compact_scenario_preset_details,
    build_scenario_preset_overview,
    create_default_changed_assumptions_children,
    create_default_capacity_planning_cards,
    create_default_charger_availability_cards,
    create_default_charger_planning_status_children,
    create_compact_status_message,
    create_default_comparison_summary_cards,
    create_default_scenario_ab_executive_summary_cards,
    create_default_scenario_comparison_empty_state_children,
    create_default_comparison_table_placeholder,
    create_default_grid_asset_status_children,
    create_default_grid_loading_cards,
    create_default_infrastructure_summary_children,
    create_default_power_quality_cards,
    create_default_power_quality_status_children,
    create_default_simulation_insights_list,
)
from dashboard.layout_components import build_dashboard_widget_style
from dashboard.scenario_comparison import (
    COMPARISON_BUILDER_COLLAPSED_BAR_HIDDEN_STYLE,
    COMPARISON_BUILDER_COLLAPSED_BAR_ROW_STYLE,
    COMPARISON_BUILDER_COLLAPSED_BAR_VISIBLE_STYLE,
    COMPARISON_BUILDER_EXPANDED_HIDDEN_STYLE,
    COMPARISON_BUILDER_EXPANDED_VISIBLE_STYLE,
    COMPARISON_SECONDARY_BUTTON_STYLE,
    SCENARIO_AB_COMPARISON_TABLE_WIDGET_SPEC,
    SCENARIO_COMPARISON_EXECUTIVE_SUMMARY_WIDGET_SPEC,
    COMPARISON_BUILDER_RUN_SECTION_HIDDEN_STYLE,
    COMPARISON_BUILDER_RUN_SECTION_VISIBLE_STYLE,
    COMPARISON_BUILDER_STATUS_CHIP_BASE_STYLE,
)
from dashboard.sidebar import SCENARIO_SIDEBAR_VISIBLE_FIELD_NAMES
from metrics.comparison_semantics import classify_directional_outcome
from metrics.metrics import (
    CONFIGURED_CONNECTION_CAPACITY_ADEQUATE_REASON,
    GRID_CONNECTION_SERVICE_PRESSURE_REASON,
    PERSISTENT_CONNECTION_CAPACITY_EXCEEDANCE_REASON,
)
from metrics.planning import (
    service_rule_is_met as charger_planning_service_rule_is_met,
)

GRAPH_HEIGHT_PX = 420
OVERVIEW_CAPACITY_SUMMARY_HEIGHT_PX = 400
CHART_LEGEND_FONT_SIZE_PX = 14
CHART_AXIS_FONT_SIZE_PX = 14
CHART_TITLE_FONT_SIZE_PX = 19
OVERVIEW_TAB_VALUE = "overview"
INFRASTRUCTURE_TAB_VALUE = "infrastructure"
SMART_CHARGING_TAB_VALUE = "smart-charging"
GRID_CAPACITY_TAB_VALUE = "grid-capacity"
POWER_QUALITY_TAB_VALUE = "power-quality"
SCENARIO_COMPARISON_TAB_VALUE = "scenario-comparison"
SCENARIO_AB_SECTION_SELECT_ID_TYPE = "scenario-ab-section-select"
SCENARIO_B_INPUT_IDS = {
    "scenario-b-vehicles-input",
    "scenario-b-charger-count-input",
    "scenario-b-charger-power-input",
    "scenario-b-grid-capacity-input",
}
SCENARIO_SIDEBAR_FIELD_NAMES = SCENARIO_SIDEBAR_VISIBLE_FIELD_NAMES
DEFAULT_SCENARIO_B_TEMPLATE_ID = default_scenario_preset.preset_id
CHARGER_PLANNING_REASON_LABELS = {
    "none": "no primary charger-planning constraint identified",
    "charger_availability": "physical charger availability is limiting",
    "charger_power": "charger power is limiting",
    "grid_connection_capacity": "grid connection capacity is limiting",
    "charging_window": "available charging time is limiting",
    "mixed": "multiple modeled constraints are limiting",
}
CONNECTION_CAPACITY_RECOMMENDATION_REASON_LABELS = {
    CONFIGURED_CONNECTION_CAPACITY_ADEQUATE_REASON: (
        "Configured capacity remains adequate"
    ),
    PERSISTENT_CONNECTION_CAPACITY_EXCEEDANCE_REASON: (
        "Persistent requested peak exceedance"
    ),
    GRID_CONNECTION_SERVICE_PRESSURE_REASON: "Grid-capacity service pressure",
}
UNAVAILABLE_METRIC_TEXT = "Not available"
NOT_APPLICABLE_METRIC_TEXT = "Not applicable"
WAITING_TIME_UNAVAILABLE_HELPER = (
    "This waiting-time metric is undefined because no vehicles started charging."
)
REQUIRED_CHARGER_COUNT_NOT_APPLICABLE_HELPER = (
    "This charger recommendation is undefined because adding chargers alone "
    "does not resolve the modeled limitation."
)
ADDITIONAL_CHARGERS_NOT_APPLICABLE_HELPER = (
    "Additional chargers are undefined because charger-count expansion alone "
    "does not satisfy the modeled service rule."
)
CHARGER_UTILIZATION_UNAVAILABLE_HELPER = (
    "This utilization metric is undefined because installed charger capacity "
    "is zero while charging demand exists."
)
DIFFERENCE_UNAVAILABLE_HELPER = (
    "This difference is undefined because at least one compared value is undefined."
)
NON_NUMERIC_DIFFERENCE_NOT_APPLICABLE_HELPER = (
    "A numeric difference is not applicable for this categorical comparison."
)
SCENARIO_AB_DETAIL_SECTION_STYLE = {
    **SECTION_STYLE,
    "backgroundColor": SUBTLE_SURFACE_BACKGROUND_COLOR,
    "padding": "1.25rem",
}
SCENARIO_AB_WORKSPACE_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(280px, 360px) minmax(0, 1fr)",
    "gap": "1rem",
    "alignItems": "start",
    "marginTop": "1rem",
}
SCENARIO_AB_DETAIL_GRID_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(0, 1fr)",
    "gap": "0.875rem",
    "alignItems": "start",
}
SCENARIO_AB_DETAIL_TABLE_STYLE = TABLE_STYLE
SCENARIO_AB_DETAIL_HEADER_CELL_STYLE = TABLE_HEADER_CELL_STYLE
SCENARIO_AB_DETAIL_CELL_STYLE = TABLE_CELL_STYLE
SCENARIO_AB_VALUE_CHIP_BASE_STYLE = {
    "backgroundColor": SURFACE_BACKGROUND_COLOR,
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "999px",
    "display": "inline-flex",
    "padding": "0.25rem 0.65rem",
    "color": TEXT_PRIMARY_COLOR,
}
SCENARIO_AB_CHANGE_BADGE_BASE_STYLE = {
    "borderRadius": "999px",
    "display": "inline-flex",
    "fontSize": "0.8rem",
    "fontWeight": "600",
    "padding": "0.25rem 0.65rem",
}
SCENARIO_AB_SECTION_SUMMARY_STYLE = {
    "alignItems": "center",
    "cursor": "pointer",
    "display": "flex",
    "gap": "0.75rem",
    "justifyContent": "space-between",
    "listStyle": "none",
}
SCENARIO_AB_SECTION_SUMMARY_CONTENT_STYLE = {
    "display": "flex",
    "alignItems": "center",
    "gap": "0.75rem",
    "flexWrap": "wrap",
}
SCENARIO_AB_SECTION_CONTENT_STYLE = {
    "marginTop": "0.75rem",
}
SCENARIO_AB_SECTION_SUMMARY_STACK_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "0.85rem",
    "listStyle": "none",
}
SCENARIO_AB_SECTION_HEADER_ROW_STYLE = {
    "display": "flex",
    "justifyContent": "space-between",
    "gap": "0.75rem",
    "alignItems": "flex-start",
}
SCENARIO_AB_EVIDENCE_PANEL_TITLE_STYLE = {
    **SECTION_TITLE_STYLE,
    "margin": "0",
    "fontSize": "1.35rem",
    "fontWeight": "700",
    "lineHeight": "1.25",
}
SCENARIO_AB_EVIDENCE_BLOCK_TITLE_STYLE = {
    **SUBSECTION_TITLE_STYLE,
    "margin": "0",
    "fontWeight": "700",
}
SCENARIO_AB_EVIDENCE_DRIVER_GRID_STYLE = {
    "width": "100%",
    "gap": "0.75rem",
}
SCENARIO_AB_EVIDENCE_DRIVER_CARD_STYLE = {
    **KPI_CARD_STYLE,
    "padding": "0.95rem 1rem",
    "gap": "0.3rem",
}
SCENARIO_AB_EVIDENCE_FACT_GRID_STYLE = {
    "width": "100%",
    "gap": "0.65rem",
}
SCENARIO_AB_EVIDENCE_FACT_CARD_STYLE = {
    **KPI_CARD_STYLE,
    "padding": "0.95rem 1rem",
    "gap": "0.3rem",
}
SCENARIO_AB_EVIDENCE_BLOCK_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "0.55rem",
    "width": "100%",
}
SCENARIO_AB_EVIDENCE_MAX_SUPPORTING_METRICS = 6
SCENARIO_AB_EVIDENCE_PRIORITY = {
    "energy_performance": (
        "unmet_energy",
        "peak_load",
        "delivered_energy",
        "capacity_utilization",
    ),
    "infrastructure": (
        "charger_capacity_vs_demand_balance",
        "required_charger_count",
        "additional_chargers_required",
        "peak_occupied_chargers",
        "average_occupied_chargers",
        "peak_charger_utilization",
        "average_charger_utilization",
        "primary_constraint_reason",
    ),
    "queueing": (
        "maximum_queue_length",
        "average_waiting_time_hours",
        "average_queue_length",
        "maximum_waiting_time_hours",
        "queue_duration_hours",
        "vehicles_waiting",
        "queue_present",
        "vehicles_not_started",
        "vehicles_with_unmet_energy",
    ),
    "grid": (
        "peak_transformer_loading",
        "maximum_feeder_loading",
        "transformer_overload_duration",
        "average_transformer_loading",
        "transformer_overload",
        "feeder_overload",
        "overloaded_feeders",
        "highest_feeder_thermal_risk",
        "transformer_thermal_risk",
        "maximum_transformer_overload",
    ),
    "power_quality": (
        "overall_pq_risk_score",
        "pq_warning_count",
        "peak_harmonic_risk_score",
        "peak_current_imbalance",
        "harmonic_risk_duration",
        "current_imbalance_duration",
        "overall_pq_risk_level",
        "harmonic_risk_level",
        "current_imbalance_risk_level",
    ),
}
SCENARIO_AB_SECTION_PRIMARY_GRID_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "repeat(auto-fit, minmax(220px, 1fr))",
    "gap": "0.75rem",
}
SCENARIO_AB_SECTION_PRIMARY_CARD_STYLE = {
    "backgroundColor": SURFACE_BACKGROUND_COLOR,
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "8px",
    "padding": "1rem 1.125rem",
    "display": "flex",
    "flexDirection": "column",
    "gap": "0.4rem",
}
SCENARIO_AB_SECTION_SUPPORTING_BLOCK_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "1rem",
}
SCENARIO_AB_SECTION_SUBBLOCK_STYLE = {
    "backgroundColor": SURFACE_BACKGROUND_COLOR,
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "8px",
    "padding": "1rem 1.125rem",
}
SCENARIO_AB_SECTION_EVIDENCE_DETAILS_STYLE = {
    "marginTop": "0.25rem",
}
SCENARIO_AB_SECTION_EVIDENCE_SUMMARY_STYLE = {
    "cursor": "pointer",
    "color": TEXT_SECONDARY_COLOR,
    "fontSize": "0.85rem",
    "fontWeight": "600",
}
SCENARIO_AB_SECTION_EVIDENCE_CONTENT_STYLE = {
    "marginTop": "0.75rem",
    "display": "flex",
    "flexDirection": "column",
    "gap": "0.75rem",
}
SCENARIO_AB_COMPACT_SECTION_CARD_STYLE = {
    **SECTION_STYLE,
    "backgroundColor": SURFACE_BACKGROUND_COLOR,
    "border": f"1px solid {BORDER_COLOR}",
    "padding": "0.8rem 0.95rem",
    "display": "flex",
    "flexDirection": "column",
    "gap": "0.45rem",
}
SCENARIO_AB_DETAIL_CARD_STYLE = {
    **SCENARIO_AB_COMPACT_SECTION_CARD_STYLE,
    "gap": "0.75rem",
    "padding": "0.95rem 1rem",
}
SCENARIO_AB_SECTION_SELECT_SURFACE_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "0.65rem",
    "cursor": "pointer",
}
SCENARIO_AB_DECISION_SUMMARY_GRID_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "repeat(auto-fit, minmax(240px, 1fr))",
    "gap": "0.75rem",
}
SCENARIO_AB_DECISION_CARD_STYLE = {
    "backgroundColor": SURFACE_BACKGROUND_COLOR,
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "8px",
    "padding": "0.85rem 1rem",
    "display": "flex",
    "flexDirection": "column",
    "gap": "0.35rem",
}
SCENARIO_AB_DECISION_AREA_STRIP_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))",
    "gap": "0.75rem",
    "marginTop": "1rem",
}
SCENARIO_AB_DECISION_AREA_CARD_STYLE = {
    "backgroundColor": SURFACE_BACKGROUND_COLOR,
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "8px",
    "padding": "1rem 1.125rem",
    "display": "flex",
    "flexDirection": "column",
    "gap": "0.35rem",
}
SCENARIO_AB_EVIDENCE_PANEL_STYLE = {
    **SECTION_STYLE,
    "backgroundColor": SURFACE_BACKGROUND_COLOR,
    "border": f"1px solid {BORDER_COLOR}",
    "padding": "1rem 1.125rem",
    "display": "flex",
    "flexDirection": "column",
    "gap": "0.8rem",
    "position": "sticky",
    "top": "4.5rem",
}
SCENARIO_AB_EVIDENCE_EMPTY_STATE_STYLE = {
    "border": f"1px dashed {BORDER_COLOR}",
    "borderRadius": "8px",
    "padding": "0.9rem 1rem",
    "backgroundColor": SUBTLE_SURFACE_BACKGROUND_COLOR,
    "display": "flex",
    "flexDirection": "column",
    "gap": "0.35rem",
}
SCENARIO_AB_EVIDENCE_BODY_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "1rem",
}
CHART_MARGIN_DEFAULT = {"l": 60, "r": 24, "t": 72, "b": 50}
CHART_MARGIN_COMPACT = {"l": 56, "r": 20, "t": 68, "b": 44}
CHART_MARGIN_TITLELESS = {"l": 60, "r": 24, "t": 24, "b": 50}
CHART_LINE_COLORS = {
    "Charging power": TEXT_PRIMARY_COLOR,
    "Delivered Charging Load": TEXT_PRIMARY_COLOR,
    "Delivered Charging Power": TEXT_PRIMARY_COLOR,
    "Requested Charging Demand": TEXT_SECONDARY_COLOR,
    "Configured Connection Capacity": ACCENT_BLUE,
    "Installed Charger Capacity": TEXT_SECONDARY_COLOR,
    "Grid Connection Capacity": ACCENT_BLUE,
    "Occupied Chargers": TEXT_PRIMARY_COLOR,
    "Available Chargers": ACCENT_BLUE,
    "Charger Capacity": ACCENT_BLUE,
    "Waiting Vehicles": STATUS_AMBER,
    "Uncontrolled Charging": TEXT_PRIMARY_COLOR,
    "Smart Charging": ACCENT_BLUE,
    "Transformer Loading": TEXT_PRIMARY_COLOR,
    "Transformer Rating": ACCENT_BLUE,
    "Overload Range": STATUS_RED,
    "Harmonic Risk": TEXT_PRIMARY_COLOR,
    "Current Imbalance": TEXT_PRIMARY_COLOR,
    "Phase A": TEXT_PRIMARY_COLOR,
    "Phase B": ACCENT_BLUE,
    "Phase C": TEXT_SECONDARY_COLOR,
}
INFRASTRUCTURE_STATUS_BADGE_BASE_STYLE = {
    "display": "inline-flex",
    "alignItems": "center",
    "alignSelf": "flex-start",
    "borderRadius": "999px",
    "fontSize": "0.8rem",
    "fontWeight": "700",
    "letterSpacing": "0.04em",
    "padding": "0.3rem 0.7rem",
    "textTransform": "uppercase",
}
INFRASTRUCTURE_STATUS_PANEL_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "1rem",
    "minHeight": "300px",
    "padding": "0",
    "backgroundColor": "transparent",
    "border": "0",
    "borderRadius": "0",
}
INFRASTRUCTURE_STATUS_ROW_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "0.35rem",
    "padding": "0.15rem 0 0.45rem 0",
}
INFRASTRUCTURE_STATUS_ROW_LABEL_STYLE = {
    "color": TEXT_PRIMARY_COLOR,
    "fontSize": "1rem",
    "fontWeight": "700",
    "lineHeight": "1.35",
}
INFRASTRUCTURE_STATUS_ROW_VALUE_STYLE = {
    "color": TEXT_PRIMARY_COLOR,
    "fontSize": "1rem",
    "fontWeight": "500",
    "lineHeight": "1.55",
}
INFRASTRUCTURE_KPI_EMPHASIS_STYLE = {
    "borderColor": "#b9c9d8",
    "boxShadow": "0 4px 12px rgba(23, 33, 43, 0.05)",
}
INFRASTRUCTURE_KPI_VALUE_EMPHASIS_STYLE = {
    **KPI_VALUE_TEXT_STYLE,
    "fontSize": "1.95rem",
}

def _callbacks_module() -> Any:
    """Return the compatibility callbacks module for monkeypatch-friendly lookups."""

    return sys.modules["dashboard.callbacks"]

__all__ = [
    name
    for name in globals()
    if name != "__all__" and not name.startswith("__")
]

