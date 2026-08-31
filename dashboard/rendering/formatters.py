"""Dashboard formatter and display helper functions."""

from ._shared import *

def format_energy_kwh(value: float) -> str:
    """Format an energy value for display."""
    return f"{value:,.1f} kWh"

def format_annual_energy_kwh(value: float) -> str:
    """Format an annual energy value for display."""
    return f"{value:,.1f} kWh/year"

def format_power_kw(value: float) -> str:
    """Format a power value for display."""
    return f"{value:,.1f} kW"

def format_hours(value: float) -> str:
    """Format a duration in hours for display."""
    return f"{value:,.1f} h"

def format_optional_hours(value: float | None) -> str:
    """Format a duration in hours or an unavailable placeholder."""
    if value is None:
        return "N/A"

    return format_hours(value)

def format_percent(value: float) -> str:
    """Format a percentage value for display."""
    return f"{value:,.1f}%"

def format_optional_percent(value: float | None) -> str:
    """Format a percentage or an unavailable placeholder."""
    if value is None:
        return "N/A"

    return format_percent(value)

def format_percentage_points(value: float) -> str:
    """Format a percentage-point difference for display."""
    return f"{value:,.1f} percentage points"

def format_signed_energy_kwh(value: float) -> str:
    """Format a signed energy difference for display."""
    return f"{_format_signed_number(value, 1)} kWh"

def format_signed_power_kw(value: float) -> str:
    """Format a signed power difference for display."""
    return f"{_format_signed_number(value, 1)} kW"

def format_signed_hours(value: float) -> str:
    """Format a signed duration in hours for display."""
    return f"{_format_signed_number(value, 1)} h"

def format_optional_signed_hours(value: float | None) -> str:
    """Format a signed duration or an unavailable placeholder."""
    if value is None:
        return "N/A"

    return format_signed_hours(value)

def format_signed_percentage_points(value: float) -> str:
    """Format a signed percentage-point difference for display."""
    return f"{_format_signed_number(value, 1)} pp"

def format_change_percent(value: float | None) -> str:
    """Format a relative percentage change or neutral placeholder."""
    if value is None:
        return "N/A"

    return f"{_format_signed_number(value, 1)}%"

def format_charger_count(value: int | float, *, decimals: int = 0) -> str:
    """Format a charger count with the requested precision."""
    return f"{value:,.{decimals}f} chargers"

def format_vehicle_count(value: int | float, *, decimals: int = 0) -> str:
    """Format a vehicle count with the requested precision."""
    return f"{value:,.{decimals}f} vehicles"

def format_optional_charger_count(
    value: int | float | None,
    *,
    decimals: int = 0,
) -> str:
    """Format a charger count or an unavailable placeholder."""
    if value is None:
        return "N/A"

    return format_charger_count(value, decimals=decimals)

def format_service_waiting_tolerance_minutes(waiting_time_minutes: int) -> str:
    """Format a scenario-specific charger-planning waiting tolerance."""
    return format_hours(waiting_time_minutes / 60)

def format_signed_charger_count(value: int | float, *, decimals: int = 0) -> str:
    """Format a signed charger-count difference for display."""
    return f"{_format_signed_number(value, decimals)} chargers"

def format_optional_signed_charger_count(
    value: int | float | None,
    *,
    decimals: int = 0,
) -> str:
    """Format a signed charger-count difference or an unavailable placeholder."""
    if value is None:
        return "N/A"

    return format_signed_charger_count(value, decimals=decimals)

def format_signed_vehicle_count(value: int | float, *, decimals: int = 0) -> str:
    """Format a signed vehicle-count difference for display."""
    return f"{_format_signed_number(value, decimals)} vehicles"

def format_feeder_count(value: int | float, *, decimals: int = 0) -> str:
    """Format a feeder count for display."""
    return f"{value:,.{decimals}f} feeders"

def format_signed_feeder_count(value: int | float, *, decimals: int = 0) -> str:
    """Format a signed feeder-count difference for display."""
    return f"{_format_signed_number(value, decimals)} feeders"

def format_risk_score(value: float) -> str:
    """Format a bounded planner-facing risk score."""
    return f"{value:,.1f} / 100"

def format_warning_count(value: int) -> str:
    """Format a warning count for dashboard display."""
    if value == 1:
        return "1 warning"

    return f"{value:,d} warnings"

def format_signed_score_points(value: float) -> str:
    """Format a signed score-point difference for display."""
    return f"{_format_signed_number(value, 1)} points"

def format_signed_warning_count(value: int) -> str:
    """Format a signed warning-count difference for display."""
    if value == 0:
        return "0 warnings"
    if abs(value) == 1:
        return f"{value:+d} warning"

    return f"{value:+d} warnings"

def format_primary_constraint_reason(reason: str) -> str:
    """Format a raw constraint-reason label for planner-facing display."""
    return CHARGER_PLANNING_REASON_LABELS.get(reason, "unavailable").capitalize()

def _undefined_metric_value(
    label: str,
    explanation: str,
    *,
    text: str,
) -> Any:
    """Return a styled undefined-metric value with concise helper text."""
    return html.Span(
        text,
        title=explanation,
        **{"aria-label": f"{label}: {text}. {explanation}"},
        style={
            "color": TEXT_SECONDARY_COLOR,
            "textDecoration": "underline dotted",
            "textUnderlineOffset": "0.15em",
        },
    )

def _optional_metric_value(
    value: Any | None,
    formatter: Any,
    *,
    label: str,
    explanation: str,
    text: str = UNAVAILABLE_METRIC_TEXT,
) -> Any:
    """Return a formatted metric value or an explicit undefined-state marker."""
    if value is None:
        return _undefined_metric_value(label, explanation, text=text)

    return formatter(value)

def _format_queue_present_value(queue_present: bool) -> str:
    """Format the queue-presence indicator for comparison display."""
    if queue_present:
        return "Present"

    return "Not present"

def _format_overload_indicator_value(overload_indicator: bool) -> str:
    """Format a grid-asset overload indicator for comparison display."""
    if overload_indicator:
        return "Overloaded"

    return "Not overloaded"

def format_thermal_risk_level(risk_level: str) -> str:
    """Format a raw thermal-risk label for planner-facing display."""
    return risk_level.replace("_", " ").capitalize()

def format_power_quality_risk_level(risk_level: str) -> str:
    """Format a raw PQ-risk label for planner-facing display."""
    return risk_level.replace("_", " ").capitalize()

def _format_signed_number(value: float, decimals: int) -> str:
    """Format positive and negative numbers with signs, zero without one."""
    rounded_value = round(value, decimals)
    if rounded_value == 0.0:
        return f"{0:,.{decimals}f}"

    return f"{rounded_value:+,.{decimals}f}"

def format_energy_delivery_status(metrics: Metrics) -> str:
    """Return a display status from the energy-delivery feasibility metric."""
    if metrics.energy_delivery_sufficient:
        return "Energy delivery is sufficient"
    return "Energy delivery is insufficient"

def format_energy_delivery_sufficient_value(
    energy_delivery_sufficient: bool,
) -> str:
    """Return a compact label for energy-delivery sufficiency."""
    if energy_delivery_sufficient:
        return "Sufficient"
    return "Insufficient"

def format_connection_capacity_exceeded_value(
    connection_capacity_exceeded: bool,
) -> str:
    """Return a compact label for requested-load exceedance."""
    if connection_capacity_exceeded:
        return "Exceeded"
    return "Not exceeded"

def format_connection_capacity_adequacy_value(
    capacity_adequate_indicator: bool,
) -> str:
    """Return the planner-facing adequacy label for connection capacity."""
    if capacity_adequate_indicator:
        return "Adequate"
    return "Not adequate"

def format_connection_capacity_recommendation_reason(reason: str) -> str:
    """Return a compact planner-facing label for the recommendation basis."""
    return CONNECTION_CAPACITY_RECOMMENDATION_REASON_LABELS.get(
        reason,
        CONNECTION_CAPACITY_RECOMMENDATION_REASON_LABELS[
            CONFIGURED_CONNECTION_CAPACITY_ADEQUATE_REASON
        ],
    )

def format_connection_sizing_status(capacity_adequate_indicator: bool) -> str:
    """Return a compact planner-facing status for connection sizing."""
    return format_connection_capacity_adequacy_value(
        capacity_adequate_indicator
    )

def format_connection_capacity_exceeded_status(metrics: Metrics) -> str:
    """Return a neutral status label for requested-load exceedance."""
    return format_connection_capacity_exceeded_value(
        metrics.connection_capacity_exceeded
    )

def _format_worse_when_true_change(
    uncontrolled_value: bool,
    smart_value: bool,
) -> str:
    """Return one semantic comparison for boolean issue indicators."""

    if uncontrolled_value == smart_value:
        return "No change"
    if uncontrolled_value and not smart_value:
        return "Improved"
    return "Worsened"

def _format_status_transition_change(
    uncontrolled_value: str,
    smart_value: str,
) -> str:
    """Return one compact textual change for categorical status values."""

    if uncontrolled_value == smart_value:
        return "No change"
    return f"{uncontrolled_value} -> {smart_value}"

def _comparison_has_queue_pressure(
    comparison_metrics: ComparisonMetrics,
) -> bool:
    """Return whether queue or waiting outcomes deserve main-table visibility."""
    return any(
        (
            comparison_metrics.uncontrolled_queue_present_indicator,
            comparison_metrics.smart_queue_present_indicator,
            comparison_metrics.uncontrolled_maximum_queue_length > 0,
            comparison_metrics.smart_maximum_queue_length > 0,
            (comparison_metrics.uncontrolled_average_waiting_time_hours or 0.0) > 0,
            (comparison_metrics.smart_average_waiting_time_hours or 0.0) > 0,
        )
    )

def _comparison_has_changed_power_quality_level(
    comparison_metrics: ComparisonMetrics,
) -> bool:
    """Return whether the strategy comparison changes qualitative PQ level."""
    return (
        comparison_metrics.uncontrolled_overall_pq_risk_level
        != comparison_metrics.smart_overall_pq_risk_level
    )

def _power_quality_status_message(
    comparison_metrics: ComparisonMetrics,
) -> str | None:
    """Return a section-level PQ status message for low-information states."""
    if _comparison_has_changed_power_quality_level(comparison_metrics):
        return None

    shared_level = format_power_quality_risk_level(
        comparison_metrics.uncontrolled_overall_pq_risk_level
    ).lower()
    return f"Modeled PQ risk remains {shared_level} for both strategies."

def format_capacity_status(metrics: Metrics) -> str:
    """Return the legacy status label from the energy-delivery metric."""
    return format_energy_delivery_status(metrics)

def format_planner_status_message(metrics: Metrics) -> str:
    """Return the planner-facing scenario status from explicit metric booleans."""
    if (
        metrics.energy_delivery_sufficient
        and metrics.connection_capacity_adequate_indicator
    ):
        return (
            "Configured connection capacity is adequate and daily energy "
            "demand can be delivered."
        )

    if (
        metrics.energy_delivery_sufficient
        and not metrics.connection_capacity_adequate_indicator
    ):
        return (
            "A connection-capacity upgrade is indicated, although daily "
            "energy demand can still be delivered."
        )

    if (
        not metrics.energy_delivery_sufficient
        and metrics.connection_capacity_adequate_indicator
    ):
        return (
            "Configured connection capacity remains adequate, but daily "
            "energy demand cannot be fully delivered within the scenario "
            "constraints."
        )

    return (
        "A connection-capacity upgrade is indicated and daily energy demand "
        "cannot be fully delivered."
    )

def format_scenario_status(metrics: Metrics) -> Any:
    """Return the active single-scenario executive summary block."""
    return html.Div(
        [
            html.P(
                html.Strong(
                    f"Overall outcome: {_format_scenario_outcome_label(metrics)}"
                ),
                style={"margin": "0 0 0.5rem 0"},
            ),
            html.P(
                format_planner_status_message(metrics),
                style={"margin": "0 0 0.5rem 0"},
            ),
            _status_metric_rows(
                [
                    (
                        "Primary limiting factor",
                        _format_primary_limiting_factor(metrics),
                    ),
                    (
                        "Charger planning outcome",
                        _format_overview_charger_planning_outcome(metrics),
                    ),
                    (
                        "Grid / PQ caution",
                        _format_overview_grid_pq_caution(metrics),
                    ),
                ]
            ),
        ],
    )

def _format_scenario_outcome_label(metrics: Metrics) -> str:
    """Return the executive overall outcome from existing status booleans."""
    if (
        metrics.energy_delivery_sufficient
        and metrics.connection_capacity_adequate_indicator
    ):
        return "Feasible"

    return "Constrained"

def _format_primary_limiting_factor(metrics: Metrics) -> str:
    """Return the primary limiting factor from existing Metrics fields only."""
    if (
        _charger_planning_rule_is_met(metrics)
        and metrics.connection_capacity_adequate_indicator
    ):
        return "No primary limiting factor indicated."

    if metrics.primary_constraint_reason == "charger_availability":
        return "Physical charger availability is the primary limiting factor."

    if metrics.primary_constraint_reason == "charger_power":
        return "Charger power is the primary limiting factor."

    if metrics.primary_constraint_reason == "grid_connection_capacity":
        return "Grid connection capacity is the primary limiting factor."

    if metrics.primary_constraint_reason == "charging_window":
        return "Available charging time is the primary limiting factor."

    if metrics.primary_constraint_reason == "mixed":
        return "Multiple modeled constraints are limiting."

    if not metrics.connection_capacity_adequate_indicator:
        return (
            "Persistent requested peak demand indicates connection-capacity "
            "review."
        )

    if not metrics.energy_delivery_sufficient:
        return (
            "Daily energy demand cannot be fully delivered within the scenario "
            "constraints."
        )

    return "No primary limiting factor indicated."

def _format_overview_charger_planning_outcome(metrics: Metrics) -> str:
    """Return a compact charger-planning outcome for the overview status block."""
    if _charger_planning_rule_is_met(metrics):
        return "Service rule met."

    if (
        metrics.primary_constraint_reason == "charger_availability"
        and metrics.additional_chargers_required is not None
        and metrics.additional_chargers_required > 0
    ):
        return (
            "Charger expansion indicated "
            f"({format_charger_count(metrics.additional_chargers_required)})."
        )

    return "Charger expansion alone is insufficient."

def _format_overview_grid_pq_caution(metrics: Metrics) -> str:
    """Return a compact grid and PQ caution summary from existing Metrics fields."""
    if _power_quality_overlaps_with_grid_stress(metrics):
        return "Modeled grid stress and PQ warnings should be reviewed together."

    if metrics.power_quality_warning_count > 0:
        return (
            "Modeled PQ caution indicated "
            f"({format_power_quality_risk_level(metrics.overall_pq_risk_level)} risk)."
        )

    if (
        metrics.transformer_thermal_risk_level == "high"
        or metrics.highest_feeder_thermal_risk_level == "high"
    ):
        return "High modeled transformer or feeder thermal risk is indicated."

    if metrics.transformer_overload_indicator or metrics.feeder_overload_indicator:
        return "Modeled transformer or feeder overload should be reviewed."

    if (
        metrics.transformer_thermal_risk_level != "low"
        or metrics.highest_feeder_thermal_risk_level != "low"
    ):
        return "Modeled transformer or feeder loading should be reviewed."

    return "No additional grid or PQ caution indicated."

def _format_scenario_ab_scalar_value(format_id: str, value: Any) -> str:
    """Format one prepared comparison value using presentation-only rules."""

    if format_id == "power_kw":
        return format_power_kw(value)
    if format_id == "power_kw_signed":
        return format_signed_power_kw(value)
    if format_id == "percent":
        return format_percent(value)
    if format_id == "percentage_points_signed":
        return format_signed_percentage_points(value)
    if format_id == "energy_kwh":
        return format_energy_kwh(value)
    if format_id == "energy_kwh_signed":
        return format_signed_energy_kwh(value)
    if format_id == "risk_score":
        return format_risk_score(value)
    if format_id == "score_points_signed":
        return format_signed_score_points(value)
    if format_id == "warning_count":
        return format_warning_count(value)
    if format_id == "warning_count_signed":
        return format_signed_warning_count(value)
    if format_id == "charger_count_0":
        return format_charger_count(value)
    if format_id == "charger_count_0_signed":
        return format_signed_charger_count(value)
    if format_id == "charger_count_1":
        return format_charger_count(value, decimals=1)
    if format_id == "charger_count_1_signed":
        return format_signed_charger_count(value, decimals=1)
    if format_id == "vehicle_count_0":
        return format_vehicle_count(value)
    if format_id == "vehicle_count_0_signed":
        return format_signed_vehicle_count(value)
    if format_id == "vehicle_count_1":
        return format_vehicle_count(value, decimals=1)
    if format_id == "vehicle_count_1_signed":
        return format_signed_vehicle_count(value, decimals=1)
    if format_id == "hours":
        return format_hours(value)
    if format_id == "hours_signed":
        return format_signed_hours(value)
    if format_id == "feeder_count":
        return format_feeder_count(value)
    if format_id == "feeder_count_signed":
        return format_signed_feeder_count(value)
    if format_id == "queue_present":
        return _format_queue_present_value(value)
    if format_id == "overload_indicator":
        return _format_overload_indicator_value(value)
    if format_id == "thermal_risk_level":
        return format_thermal_risk_level(value)
    if format_id == "power_quality_risk_level":
        return format_power_quality_risk_level(value)
    if format_id == "primary_constraint_reason":
        return format_primary_constraint_reason(value)

    raise ValueError(f"Unsupported Scenario A/B display format: {format_id}")

def _format_scenario_ab_absolute_change_value(
    change_format: str | None,
    change_value: Any,
) -> str:
    """Return an unsigned narrative-friendly change magnitude for one value."""

    absolute_change = abs(float(change_value))

    if change_format == "power_kw_signed":
        return format_power_kw(absolute_change)
    if change_format == "percentage_points_signed":
        return format_percentage_points(absolute_change)
    if change_format == "energy_kwh_signed":
        return format_energy_kwh(absolute_change)
    if change_format == "score_points_signed":
        return f"{absolute_change:,.1f} pts"
    if change_format == "vehicle_count_0_signed":
        return format_vehicle_count(absolute_change)
    if change_format == "vehicle_count_1_signed":
        return format_vehicle_count(absolute_change, decimals=1)
    if change_format == "charger_count_0_signed":
        return format_charger_count(absolute_change)
    if change_format == "charger_count_1_signed":
        return format_charger_count(absolute_change, decimals=1)
    if change_format == "warning_count_signed":
        return format_warning_count(int(absolute_change))
    if change_format == "hours_signed":
        return format_hours(absolute_change)
    if change_format == "feeder_count_signed":
        return format_feeder_count(int(absolute_change))

    return _format_scenario_ab_scalar_value(change_format, change_value)

def _scenario_ab_executive_change_style(outcome: str) -> dict[str, str]:
    """Return compact value styling for one Scenario A/B executive KPI."""

    style = {
        **KPI_VALUE_TEXT_STYLE,
        "fontSize": "1.35rem",
        "lineHeight": "1.2",
    }
    if outcome == SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT:
        return {
            **style,
            "color": STATUS_GREEN,
        }
    if outcome == SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF:
        return {
            **style,
            "color": STATUS_RED,
        }
    return {
        **style,
        "color": TEXT_SECONDARY_COLOR,
    }

def _scenario_ab_executive_card_style(outcome: str) -> dict[str, str]:
    """Return compact card styling for one Scenario A/B executive KPI."""

    style = {
        **KPI_CARD_STYLE,
        "padding": "0.95rem 1rem",
        "gap": "0.28rem",
    }
    if outcome == SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT:
        return {
            **style,
            "backgroundColor": STATUS_GREEN_BACKGROUND,
            "boxShadow": f"inset 3px 0 0 {STATUS_GREEN}",
        }
    if outcome == SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF:
        return {
            **style,
            "backgroundColor": STATUS_RED_BACKGROUND,
            "boxShadow": f"inset 3px 0 0 {STATUS_RED}",
        }
    return {
        **style,
        "backgroundColor": SUBTLE_SURFACE_BACKGROUND_COLOR,
    }

def _status_metric_rows(metric_rows: list[tuple[str, str]]) -> Any:
    """Return a compact list of label-value status rows."""

    return html.Div(
        [
            html.Div(
                [
                    html.Strong(f"{label}: "),
                    html.Span(value),
                ],
                style={"padding": "0.15rem 0"},
            )
            for label, value in metric_rows
        ],
        style={"marginTop": "0.75rem"},
    )

def _charger_planning_rule_is_met(metrics: Metrics) -> bool:
    """Return whether the completed charger-planning service rule is met."""

    return (
        metrics.energy_delivery_sufficient
        and charger_planning_service_rule_is_met(metrics)
    )

def _power_quality_overlaps_with_grid_stress(metrics: Metrics) -> bool:
    """Return whether active PQ warnings coincide with modeled grid stress."""

    if metrics.power_quality_warning_count <= 0:
        return False

    return (
        metrics.transformer_overload_indicator
        or metrics.feeder_overload_indicator
        or metrics.transformer_thermal_risk_level != "low"
        or metrics.highest_feeder_thermal_risk_level != "low"
    )

__all__ = [

    'format_energy_kwh',

    'format_annual_energy_kwh',

    'format_power_kw',

    'format_hours',

    'format_optional_hours',

    'format_percent',

    'format_optional_percent',

    'format_percentage_points',

    'format_signed_energy_kwh',

    'format_signed_power_kw',

    'format_signed_hours',

    'format_optional_signed_hours',

    'format_signed_percentage_points',

    'format_change_percent',

    'format_charger_count',

    'format_vehicle_count',

    'format_optional_charger_count',

    'format_service_waiting_tolerance_minutes',

    'format_signed_charger_count',

    'format_optional_signed_charger_count',

    'format_signed_vehicle_count',

    'format_feeder_count',

    'format_signed_feeder_count',

    'format_risk_score',

    'format_warning_count',

    'format_signed_score_points',

    'format_signed_warning_count',

    'format_primary_constraint_reason',

    '_undefined_metric_value',

    '_optional_metric_value',

    '_format_queue_present_value',

    '_format_overload_indicator_value',

    'format_thermal_risk_level',

    'format_power_quality_risk_level',

    '_format_signed_number',

    'format_energy_delivery_status',

    'format_energy_delivery_sufficient_value',

    'format_connection_capacity_exceeded_value',

    'format_connection_capacity_adequacy_value',

    'format_connection_capacity_recommendation_reason',

    'format_connection_sizing_status',

    'format_connection_capacity_exceeded_status',

    '_format_worse_when_true_change',

    '_format_status_transition_change',

    '_comparison_has_queue_pressure',

    '_comparison_has_changed_power_quality_level',

    '_power_quality_status_message',

    'format_capacity_status',

    'format_planner_status_message',

    'format_scenario_status',

    '_format_scenario_outcome_label',

    '_format_primary_limiting_factor',

    '_format_overview_charger_planning_outcome',

    '_format_overview_grid_pq_caution',

    '_format_scenario_ab_scalar_value',

    '_format_scenario_ab_absolute_change_value',

    '_scenario_ab_executive_change_style',

    '_scenario_ab_executive_card_style',

    '_status_metric_rows',

    '_charger_planning_rule_is_met',

    '_power_quality_overlaps_with_grid_stress',

]

