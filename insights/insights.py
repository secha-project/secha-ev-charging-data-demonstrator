"""Rule-based decision-support messages derived from calculated metrics."""

from metrics import ComparisonMetrics, Metrics
from scenarios import ChargingStrategy


HIGH_UTILIZATION_THRESHOLD = 90.0


def generate_insights(
    metrics: Metrics,
    charging_strategy: ChargingStrategy | None = None,
    comparison_metrics: ComparisonMetrics | None = None,
) -> list[str]:
    """Return up to three concise decision-support messages."""
    del charging_strategy

    return [
        _service_sufficiency_insight(metrics),
        _smart_charging_benefit_insight(comparison_metrics),
        _risk_or_caution_insight(metrics),
    ]


def _service_sufficiency_insight(metrics: Metrics) -> str:
    """Summarize whether the scenario can satisfy modeled charging demand."""
    if metrics.energy_delivery_sufficient:
        return "Daily charging demand can be served."

    return "Daily charging demand cannot be fully served."


def _smart_charging_benefit_insight(
    comparison_metrics: ComparisonMetrics | None,
) -> str:
    """Summarize whether Smart Charging appears beneficial in planning terms."""
    if comparison_metrics is None:
        return "Smart Charging comparison is not available for this scenario."

    if (
        comparison_metrics.peak_reduction > 0.0
        or comparison_metrics.connection_capacity_avoided_by_smart_kw > 0.0
        or comparison_metrics.exceedance_duration_reduction_hours > 0.0
    ):
        return "Smart Charging improves the scenario versus uncontrolled charging."

    if (
        comparison_metrics.peak_reduction < 0.0
        or comparison_metrics.required_connection_capacity_difference_kw < 0.0
        or comparison_metrics.recommended_connection_capacity_difference_kw < 0.0
        or comparison_metrics.exceedance_duration_reduction_hours < 0.0
    ):
        return "Smart Charging adds trade-offs in this scenario."

    return "Smart Charging adds limited planning value in this scenario."


def _risk_or_caution_insight(metrics: Metrics) -> str:
    """Summarize the main modeled risk or caution that still deserves review."""
    if _power_quality_overlaps_with_grid_stress(metrics):
        return "PQ warnings overlap with transformer or feeder stress."

    if metrics.power_quality_warning_count > 0:
        return "Power-quality caution is indicated."

    if (
        metrics.transformer_thermal_risk_level == "high"
        or metrics.highest_feeder_thermal_risk_level == "high"
    ):
        return "High modeled transformer or feeder stress is indicated."

    if metrics.transformer_overload_indicator or metrics.feeder_overload_indicator:
        return "Modeled transformer or feeder overload is indicated."

    if metrics.connection_capacity_exceeded:
        return "Requested peak exceeds configured connection capacity."

    if metrics.capacity_utilization > HIGH_UTILIZATION_THRESHOLD:
        return "Spare charging headroom is limited."

    return "No additional material cautions are indicated."


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
