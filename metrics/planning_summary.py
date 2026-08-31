"""Planner-facing summary and status helpers for strategy comparisons."""

import math

from metrics.constraint_analysis import (
    GRID_CONNECTION_CAPACITY_CONSTRAINT_REASON,
    format_primary_constraint_reason_label,
)
from metrics.metrics import Metrics
from metrics.planning_rules import collect_failed_conditions
from metrics.shared import FLOATING_POINT_TOLERANCE


NO_MODELED_SERVICE_PRESSURE_SUMMARY = "No modeled service pressure."
SERVICE_PRESSURE_UNCHANGED_SUMMARY = "Service pressure unchanged."
SERVICE_TRADEOFF_CHANGED_SUMMARY = "Service trade-off changed."
SERVICE_PRESSURE_REDUCED_SUMMARY = "Service pressure reduced."
SERVICE_PRESSURE_WORSENED_SUMMARY = "Service pressure worsened."
SERVICE_SHORTFALL_REDUCED_SUMMARY = "Service shortfall reduced."
SERVICE_SHORTFALL_WORSENED_SUMMARY = "Service shortfall worsened."
WAITING_REDUCED_SUMMARY = "Waiting reduced."
WAITING_WORSENED_SUMMARY = "Waiting worsened."
QUEUE_PRESSURE_REDUCED_SUMMARY = "Queue pressure reduced."
QUEUE_PRESSURE_WORSENED_SUMMARY = "Queue pressure worsened."
SERVICE_RULE_RESOLVED_SUMMARY = "Service-rule violation resolved."
SERVICE_RULE_WORSENED_SUMMARY = "Service-rule violation introduced."
NO_PRIMARY_CONSTRAINT_SHIFT_SUMMARY = "No primary constraint shift."
NO_PLANNING_CHANGE_SUMMARY = (
    "Smart Charging reduces operational load but does not change "
    "infrastructure recommendations for this scenario."
)
NO_PLANNING_CHANGE_WHEN_FEASIBLE_SUMMARY = (
    "Both strategies satisfy the modeled service rule and lead to the same "
    "infrastructure recommendation."
)


def service_rule_is_met(metrics: Metrics) -> bool:
    """Return whether the prepared planning outputs satisfy the service rule."""
    return len(collect_failed_conditions(metrics)) == 0


def connection_upgrade_required(metrics: Metrics) -> bool:
    """Return whether the planner recommendation exceeds configured capacity."""
    return (
        metrics.recommended_connection_capacity_kw
        > metrics.configured_connection_capacity_kw + FLOATING_POINT_TOLERANCE
    )


def connection_upgrade_avoided_by_smart(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> bool:
    """Return whether Smart Charging removes the need for a connection upgrade."""
    return connection_upgrade_required(
        uncontrolled_metrics
    ) and not connection_upgrade_required(smart_metrics)


def charger_expansion_avoided_by_smart(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> bool:
    """Return whether Smart Charging removes the need for extra chargers."""
    uncontrolled_additional = uncontrolled_metrics.additional_chargers_required
    smart_additional = smart_metrics.additional_chargers_required

    return (
        uncontrolled_additional is not None
        and uncontrolled_additional > 0
        and smart_additional == 0
        and smart_metrics.required_charger_count is not None
    )


def service_rule_resolved_by_smart(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> bool:
    """Return whether Smart Charging resolves a modeled service-rule failure."""
    return (
        not service_rule_is_met(uncontrolled_metrics)
        and service_rule_is_met(smart_metrics)
    )


def service_rule_worsened_by_smart(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> bool:
    """Return whether Smart Charging introduces a modeled service-rule failure."""
    return (
        service_rule_is_met(uncontrolled_metrics)
        and not service_rule_is_met(smart_metrics)
    )


def primary_constraint_shifted_by_smart(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> bool:
    """Return whether the dominant modeled bottleneck changes by strategy."""
    return (
        uncontrolled_metrics.primary_constraint_reason
        != smart_metrics.primary_constraint_reason
    )


def primary_constraint_shift_summary(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> str:
    """Return a planner-facing summary of any primary-constraint shift."""
    if not primary_constraint_shifted_by_smart(
        uncontrolled_metrics,
        smart_metrics,
    ):
        return NO_PRIMARY_CONSTRAINT_SHIFT_SUMMARY

    return (
        "Primary modeled bottleneck shifts from "
        f"{format_primary_constraint_reason_label(uncontrolled_metrics.primary_constraint_reason)} "
        f"to {format_primary_constraint_reason_label(smart_metrics.primary_constraint_reason)}."
    )


def infrastructure_recommendation_changed_by_smart(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> bool:
    """Return whether Smart Charging changes planner-facing outcomes."""
    uncontrolled_has_defined_charger_plan = (
        uncontrolled_metrics.required_charger_count is not None
        and uncontrolled_metrics.additional_chargers_required is not None
    )
    smart_has_defined_charger_plan = (
        smart_metrics.required_charger_count is not None
        and smart_metrics.additional_chargers_required is not None
    )
    required_charger_count_changed = (
        uncontrolled_has_defined_charger_plan
        and smart_has_defined_charger_plan
        and uncontrolled_metrics.required_charger_count
        != smart_metrics.required_charger_count
    )
    additional_chargers_required_changed = (
        uncontrolled_has_defined_charger_plan
        and smart_has_defined_charger_plan
        and uncontrolled_metrics.additional_chargers_required
        != smart_metrics.additional_chargers_required
    )
    recommended_connection_capacity_changed = (
        uncontrolled_has_defined_charger_plan
        and smart_has_defined_charger_plan
        and not math.isclose(
            uncontrolled_metrics.recommended_connection_capacity_kw,
            smart_metrics.recommended_connection_capacity_kw,
            abs_tol=FLOATING_POINT_TOLERANCE,
        )
    )
    service_rule_changed = (
        uncontrolled_has_defined_charger_plan
        and smart_has_defined_charger_plan
        and service_rule_is_met(uncontrolled_metrics)
        != service_rule_is_met(smart_metrics)
    )

    return (
        recommended_connection_capacity_changed
        or required_charger_count_changed
        or additional_chargers_required_changed
        or service_rule_changed
        or primary_constraint_shifted_by_smart(
            uncontrolled_metrics,
            smart_metrics,
        )
    )


def service_impact_summary(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> str:
    """Return a prepared operational service-pressure summary by strategy."""
    if (
        not _has_modeled_service_pressure(uncontrolled_metrics)
        and not _has_modeled_service_pressure(smart_metrics)
    ):
        return NO_MODELED_SERVICE_PRESSURE_SUMMARY

    if service_rule_resolved_by_smart(uncontrolled_metrics, smart_metrics):
        return SERVICE_RULE_RESOLVED_SUMMARY

    if service_rule_worsened_by_smart(uncontrolled_metrics, smart_metrics):
        return SERVICE_RULE_WORSENED_SUMMARY

    shortfall_reduced = _service_shortfall_reduced_by_smart(
        uncontrolled_metrics,
        smart_metrics,
    )
    shortfall_worsened = _service_shortfall_worsened_by_smart(
        uncontrolled_metrics,
        smart_metrics,
    )
    queue_pressure_reduced = _queue_pressure_reduced_by_smart(
        uncontrolled_metrics,
        smart_metrics,
    )
    queue_pressure_worsened = _queue_pressure_worsened_by_smart(
        uncontrolled_metrics,
        smart_metrics,
    )
    waiting_improved = _waiting_improved_by_smart(
        uncontrolled_metrics,
        smart_metrics,
    )
    waiting_worsened = _waiting_worsened_by_smart(
        uncontrolled_metrics,
        smart_metrics,
    )

    if (
        (shortfall_reduced or queue_pressure_reduced or waiting_improved)
        and (shortfall_worsened or queue_pressure_worsened or waiting_worsened)
    ):
        return SERVICE_TRADEOFF_CHANGED_SUMMARY

    if shortfall_reduced:
        return SERVICE_SHORTFALL_REDUCED_SUMMARY

    if shortfall_worsened:
        return SERVICE_SHORTFALL_WORSENED_SUMMARY

    if waiting_improved:
        return WAITING_REDUCED_SUMMARY

    if waiting_worsened:
        return WAITING_WORSENED_SUMMARY

    if queue_pressure_reduced:
        return QUEUE_PRESSURE_REDUCED_SUMMARY

    if queue_pressure_worsened:
        return QUEUE_PRESSURE_WORSENED_SUMMARY

    return SERVICE_PRESSURE_UNCHANGED_SUMMARY


def infrastructure_impact_summary(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
    *,
    connection_capacity_avoided_by_smart_kw: float,
    recommended_connection_capacity_avoided_by_smart_kw: float = 0.0,
    connection_upgrade_avoided_by_smart: bool = False,
    infrastructure_recommendation_changed_by_smart: bool = False,
) -> str:
    """Return the prepared high-level planning impact summary for Smart Charging."""
    if charger_expansion_avoided_by_smart(uncontrolled_metrics, smart_metrics):
        return (
            "Smart Charging avoids the additional charger expansion indicated "
            "under uncontrolled charging."
        )

    if connection_upgrade_avoided_by_smart:
        return (
            "Smart Charging avoids the modeled connection-capacity upgrade "
            "recommendation for this scenario."
        )

    if (
        uncontrolled_metrics.primary_constraint_reason
        == GRID_CONNECTION_CAPACITY_CONSTRAINT_REASON
        and smart_metrics.primary_constraint_reason
        != GRID_CONNECTION_CAPACITY_CONSTRAINT_REASON
        and connection_capacity_avoided_by_smart_kw > 0.0
    ):
        return (
            "Smart Charging resolves the modeled grid connection-capacity "
            "constraint under current infrastructure."
        )

    if service_rule_resolved_by_smart(uncontrolled_metrics, smart_metrics):
        if primary_constraint_shifted_by_smart(
            uncontrolled_metrics,
            smart_metrics,
        ):
            return (
                "Smart Charging resolves the modeled service-rule violation "
                "and changes the dominant planning bottleneck."
            )

        return (
            "Smart Charging resolves the modeled service-rule violation under "
            "current infrastructure."
        )

    uncontrolled_additional = uncontrolled_metrics.additional_chargers_required
    smart_additional = smart_metrics.additional_chargers_required
    if (
        uncontrolled_additional is not None
        and smart_additional is not None
        and uncontrolled_additional > smart_additional
        and smart_additional > 0
    ):
        return (
            "Smart Charging reduces the modeled charger expansion "
            "requirement but does not eliminate it."
        )

    if primary_constraint_shifted_by_smart(
        uncontrolled_metrics,
        smart_metrics,
    ):
        return primary_constraint_shift_summary(
            uncontrolled_metrics,
            smart_metrics,
        )

    if service_rule_worsened_by_smart(uncontrolled_metrics, smart_metrics):
        return "Smart Charging worsens the modeled service outcome for this scenario."

    if (
        uncontrolled_additional is not None
        and smart_additional is not None
        and uncontrolled_additional < smart_additional
    ):
        return (
            "Smart Charging increases the modeled charger expansion "
            "requirement for this scenario."
        )

    if (
        recommended_connection_capacity_avoided_by_smart_kw > 0.0
        and infrastructure_recommendation_changed_by_smart
    ):
        if connection_upgrade_required(smart_metrics):
            return (
                "Smart Charging reduces the modeled connection-capacity "
                "upgrade recommendation but does not eliminate it."
            )

        return (
            "Smart Charging lowers the modeled connection-capacity "
            "recommendation for this scenario."
        )

    recommended_connection_capacity_difference_kw = (
        uncontrolled_metrics.recommended_connection_capacity_kw
        - smart_metrics.recommended_connection_capacity_kw
    )
    if (
        recommended_connection_capacity_difference_kw
        < -FLOATING_POINT_TOLERANCE
        and infrastructure_recommendation_changed_by_smart
    ):
        return (
            "Smart Charging increases the modeled connection-capacity "
            "recommendation for this scenario."
        )

    if (
        connection_capacity_avoided_by_smart_kw > 0.0
        and not infrastructure_recommendation_changed_by_smart
    ):
        return (
            "Smart Charging reduces required connection capacity but does not "
            "change the modeled infrastructure recommendation."
        )

    if service_rule_is_met(uncontrolled_metrics) and service_rule_is_met(
        smart_metrics
    ):
        return NO_PLANNING_CHANGE_WHEN_FEASIBLE_SUMMARY

    return NO_PLANNING_CHANGE_SUMMARY



def _has_modeled_service_pressure(metrics: Metrics) -> bool:
    return (
        metrics.queue_present_indicator
        or metrics.maximum_queue_length > 0
        or metrics.vehicles_waiting_count > 0
        or metrics.vehicles_not_started_count > 0
        or metrics.vehicles_with_unmet_energy_count > 0
        or metrics.unmet_energy > FLOATING_POINT_TOLERANCE
        or (
            metrics.average_waiting_time_hours is not None
            and metrics.average_waiting_time_hours > FLOATING_POINT_TOLERANCE
        )
    )


def _service_shortfall_reduced_by_smart(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> bool:
    return (
        smart_metrics.vehicles_not_started_count
        < uncontrolled_metrics.vehicles_not_started_count
        or smart_metrics.vehicles_with_unmet_energy_count
        < uncontrolled_metrics.vehicles_with_unmet_energy_count
        or smart_metrics.unmet_energy
        < uncontrolled_metrics.unmet_energy - FLOATING_POINT_TOLERANCE
    )


def _service_shortfall_worsened_by_smart(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> bool:
    return (
        smart_metrics.vehicles_not_started_count
        > uncontrolled_metrics.vehicles_not_started_count
        or smart_metrics.vehicles_with_unmet_energy_count
        > uncontrolled_metrics.vehicles_with_unmet_energy_count
        or smart_metrics.unmet_energy
        > uncontrolled_metrics.unmet_energy + FLOATING_POINT_TOLERANCE
    )


def _queue_pressure_reduced_by_smart(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> bool:
    return (
        (
            uncontrolled_metrics.queue_present_indicator
            and not smart_metrics.queue_present_indicator
        )
        or smart_metrics.maximum_queue_length
        < uncontrolled_metrics.maximum_queue_length
        or smart_metrics.queue_duration_hours
        < uncontrolled_metrics.queue_duration_hours - FLOATING_POINT_TOLERANCE
        or smart_metrics.vehicles_waiting_count
        < uncontrolled_metrics.vehicles_waiting_count
    )


def _queue_pressure_worsened_by_smart(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> bool:
    return (
        (
            not uncontrolled_metrics.queue_present_indicator
            and smart_metrics.queue_present_indicator
        )
        or smart_metrics.maximum_queue_length
        > uncontrolled_metrics.maximum_queue_length
        or smart_metrics.queue_duration_hours
        > uncontrolled_metrics.queue_duration_hours + FLOATING_POINT_TOLERANCE
        or smart_metrics.vehicles_waiting_count
        > uncontrolled_metrics.vehicles_waiting_count
    )


def _waiting_improved_by_smart(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> bool:
    return _average_waiting_improved_by_smart(
        uncontrolled_metrics,
        smart_metrics,
    ) or _maximum_waiting_improved_by_smart(
        uncontrolled_metrics,
        smart_metrics,
    )


def _average_waiting_improved_by_smart(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> bool:
    if (
        uncontrolled_metrics.average_waiting_time_hours is None
        or smart_metrics.average_waiting_time_hours is None
    ):
        return False

    return smart_metrics.average_waiting_time_hours < (
        uncontrolled_metrics.average_waiting_time_hours - 0.05
    )


def _waiting_worsened_by_smart(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> bool:
    return _average_waiting_worsened_by_smart(
        uncontrolled_metrics,
        smart_metrics,
    ) or _maximum_waiting_worsened_by_smart(
        uncontrolled_metrics,
        smart_metrics,
    )


def _average_waiting_worsened_by_smart(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> bool:
    if (
        uncontrolled_metrics.average_waiting_time_hours is None
        or smart_metrics.average_waiting_time_hours is None
    ):
        return False

    return smart_metrics.average_waiting_time_hours > (
        uncontrolled_metrics.average_waiting_time_hours + 0.05
    )


def _maximum_waiting_improved_by_smart(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> bool:
    if (
        uncontrolled_metrics.maximum_waiting_time_hours is None
        or smart_metrics.maximum_waiting_time_hours is None
    ):
        return False

    return smart_metrics.maximum_waiting_time_hours < (
        uncontrolled_metrics.maximum_waiting_time_hours - 0.05
    )


def _maximum_waiting_worsened_by_smart(
    uncontrolled_metrics: Metrics,
    smart_metrics: Metrics,
) -> bool:
    if (
        uncontrolled_metrics.maximum_waiting_time_hours is None
        or smart_metrics.maximum_waiting_time_hours is None
    ):
        return False

    return smart_metrics.maximum_waiting_time_hours > (
        uncontrolled_metrics.maximum_waiting_time_hours + 0.05
    )
