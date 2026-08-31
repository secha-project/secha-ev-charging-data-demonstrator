"""Shared service-rule primitives used by planning search and summaries."""

from metrics.metrics import Metrics
from metrics.shared import FLOATING_POINT_TOLERANCE
from simulation import get_timestep_hours


MAXIMUM_WAITING_TIME_CONDITION = "maximum_waiting_time_hours"
VEHICLES_NOT_STARTED_CONDITION = "vehicles_not_started_count"
VEHICLES_WITH_UNMET_ENERGY_CONDITION = "vehicles_with_unmet_energy_count"
DEFAULT_CHARGER_SERVICE_RULE_WAITING_TOLERANCE_HOURS = (
    2 * get_timestep_hours()
)


def collect_failed_conditions(metrics: Metrics) -> tuple[str, ...]:
    """Return the service-rule conditions violated by prepared metrics."""
    failed_conditions: list[str] = []

    if metrics.vehicles_not_started_count > 0:
        failed_conditions.append(VEHICLES_NOT_STARTED_CONDITION)
    if metrics.vehicles_with_unmet_energy_count > 0:
        failed_conditions.append(VEHICLES_WITH_UNMET_ENERGY_CONDITION)
    if maximum_waiting_time_exceeds_service_rule_tolerance(metrics):
        failed_conditions.append(MAXIMUM_WAITING_TIME_CONDITION)

    return tuple(failed_conditions)


def maximum_waiting_time_exceeds_service_rule_tolerance(
    metrics: Metrics,
) -> bool:
    """Return whether prepared waiting time exceeds the service-rule limit."""
    maximum_waiting_time_hours = metrics.maximum_waiting_time_hours
    if maximum_waiting_time_hours is None:
        return False

    return maximum_waiting_time_hours > (
        resolve_charger_service_waiting_tolerance_hours(metrics)
        + FLOATING_POINT_TOLERANCE
    )


def resolve_charger_service_waiting_tolerance_hours(metrics: Metrics) -> float:
    """Return the prepared waiting tolerance used by charger planning."""
    waiting_tolerance_hours = metrics.charger_service_waiting_tolerance_hours
    if waiting_tolerance_hours < 0:
        return DEFAULT_CHARGER_SERVICE_RULE_WAITING_TOLERANCE_HOURS
    return waiting_tolerance_hours
