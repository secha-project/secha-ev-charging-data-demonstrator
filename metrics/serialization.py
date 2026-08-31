"""Explicit serialization helpers for Metrics payloads and feeder summaries."""

from metrics.constraint_analysis import (
    CONFIGURED_CONNECTION_CAPACITY_ADEQUATE_REASON,
    NO_PRIMARY_CONSTRAINT_REASON,
)
from metrics.grid_risk import THERMAL_RISK_LOW
from metrics.power_quality import POWER_QUALITY_RISK_LOW
from metrics.metrics import (
    FEEDER_LOADING_DISTRIBUTION_NO_FEEDERS,
    FeederSummaryMetrics,
    FeederSummaryMetricsData,
    Metrics,
    MetricsData,
)


def metrics_to_dict(metrics: Metrics) -> MetricsData:
    """Return a Dash-store-safe dictionary representation of metrics."""

    return {
        "total_daily_energy": metrics.total_daily_energy,
        "available_capacity": metrics.available_capacity,
        "energy_delivery_sufficient": metrics.energy_delivery_sufficient,
        "capacity_sufficiency": metrics.capacity_sufficiency,
        "peak_load": metrics.peak_load,
        "capacity_utilization": metrics.capacity_utilization,
        "delivered_energy": metrics.delivered_energy,
        "unmet_energy": metrics.unmet_energy,
        "annual_energy": metrics.annual_energy,
        "configured_connection_capacity_kw": (
            metrics.configured_connection_capacity_kw
        ),
        "required_connection_capacity_kw": (
            metrics.required_connection_capacity_kw
        ),
        "recommended_connection_capacity_kw": (
            metrics.recommended_connection_capacity_kw
        ),
        "planning_margin_percent": metrics.planning_margin_percent,
        "peak_capacity_margin_kw": metrics.peak_capacity_margin_kw,
        "peak_capacity_margin_percent": (
            metrics.peak_capacity_margin_percent
        ),
        "connection_capacity_exceeded": (
            metrics.connection_capacity_exceeded
        ),
        "maximum_capacity_exceedance_kw": (
            metrics.maximum_capacity_exceedance_kw
        ),
        "exceeded_timestep_count": metrics.exceeded_timestep_count,
        "capacity_exceedance_duration_hours": (
            metrics.capacity_exceedance_duration_hours
        ),
        "persistent_capacity_exceedance_indicator": (
            metrics.persistent_capacity_exceedance_indicator
        ),
        "connection_capacity_adequate_indicator": (
            metrics.connection_capacity_adequate_indicator
        ),
        "connection_capacity_recommendation_reason": (
            metrics.connection_capacity_recommendation_reason
        ),
        "average_transformer_loading_percent": (
            metrics.average_transformer_loading_percent
        ),
        "peak_transformer_loading_percent": (
            metrics.peak_transformer_loading_percent
        ),
        "transformer_overload_indicator": (
            metrics.transformer_overload_indicator
        ),
        "transformer_overload_duration_hours": (
            metrics.transformer_overload_duration_hours
        ),
        "transformer_maximum_overload_kw": (
            metrics.transformer_maximum_overload_kw
        ),
        "transformer_thermal_risk_level": (
            metrics.transformer_thermal_risk_level
        ),
        "maximum_feeder_loading_percent": (
            metrics.maximum_feeder_loading_percent
        ),
        "feeder_overload_indicator": metrics.feeder_overload_indicator,
        "overloaded_feeder_count": metrics.overloaded_feeder_count,
        "highest_feeder_thermal_risk_level": (
            metrics.highest_feeder_thermal_risk_level
        ),
        "most_loaded_feeder_id": metrics.most_loaded_feeder_id,
        "peak_feeder_loading_spread_percentage_points": (
            metrics.peak_feeder_loading_spread_percentage_points
        ),
        "feeder_loading_distribution_label": (
            metrics.feeder_loading_distribution_label
        ),
        "feeder_status_message": metrics.feeder_status_message,
        "show_feeder_detail_indicator": (
            metrics.show_feeder_detail_indicator
        ),
        "peak_harmonic_risk_score": metrics.peak_harmonic_risk_score,
        "average_harmonic_risk_score": metrics.average_harmonic_risk_score,
        "harmonic_risk_duration_hours": metrics.harmonic_risk_duration_hours,
        "harmonic_risk_level": metrics.harmonic_risk_level,
        "harmonic_warning_indicator": metrics.harmonic_warning_indicator,
        "peak_current_imbalance_percent": (
            metrics.peak_current_imbalance_percent
        ),
        "average_current_imbalance_percent": (
            metrics.average_current_imbalance_percent
        ),
        "imbalance_duration_hours": metrics.imbalance_duration_hours,
        "current_imbalance_risk_level": (
            metrics.current_imbalance_risk_level
        ),
        "imbalance_warning_indicator": metrics.imbalance_warning_indicator,
        "overall_pq_risk_score": metrics.overall_pq_risk_score,
        "overall_pq_risk_level": metrics.overall_pq_risk_level,
        "overall_pq_warning_indicator": metrics.overall_pq_warning_indicator,
        "power_quality_warning_count": metrics.power_quality_warning_count,
        "power_quality_message": metrics.power_quality_message,
        "average_charger_utilization_percent": (
            metrics.average_charger_utilization_percent
        ),
        "peak_charger_utilization_percent": (
            metrics.peak_charger_utilization_percent
        ),
        "average_occupied_charger_count": (
            metrics.average_occupied_charger_count
        ),
        "peak_occupied_charger_count": metrics.peak_occupied_charger_count,
        "charger_shortage_indicator": metrics.charger_shortage_indicator,
        "queue_present_indicator": metrics.queue_present_indicator,
        "maximum_queue_length": metrics.maximum_queue_length,
        "average_queue_length": metrics.average_queue_length,
        "queue_duration_hours": metrics.queue_duration_hours,
        "average_waiting_time_hours": metrics.average_waiting_time_hours,
        "maximum_waiting_time_hours": metrics.maximum_waiting_time_hours,
        "charger_service_waiting_tolerance_hours": (
            metrics.charger_service_waiting_tolerance_hours
        ),
        "vehicles_waiting_count": metrics.vehicles_waiting_count,
        "vehicles_not_started_count": metrics.vehicles_not_started_count,
        "vehicles_with_unmet_energy_count": (
            metrics.vehicles_with_unmet_energy_count
        ),
        "charger_capacity_vs_demand_balance": (
            metrics.charger_capacity_vs_demand_balance
        ),
        "required_charger_count": metrics.required_charger_count,
        "additional_chargers_required": (
            metrics.additional_chargers_required
        ),
        "charger_count_sufficient_indicator": (
            metrics.charger_count_sufficient_indicator
        ),
        "primary_constraint_reason": metrics.primary_constraint_reason,
        "feeder_summary_rows": [
            feeder_summary_metrics_to_dict(feeder_summary)
            for feeder_summary in metrics.feeder_summary_rows
        ],
        "transformer_total_load_kw_by_timestep": list(
            metrics.transformer_total_load_kw_by_timestep
        ),
        "transformer_loading_percent_by_timestep": list(
            metrics.transformer_loading_percent_by_timestep
        ),
        "transformer_overload_kw_by_timestep": list(
            metrics.transformer_overload_kw_by_timestep
        ),
        "occupied_charger_count_by_timestep": list(
            metrics.occupied_charger_count_by_timestep
        ),
        "waiting_vehicle_count_by_timestep": list(
            metrics.waiting_vehicle_count_by_timestep
        ),
        "harmonic_risk_score_by_timestep": list(
            metrics.harmonic_risk_score_by_timestep
        ),
        "current_imbalance_percent_by_timestep": list(
            metrics.current_imbalance_percent_by_timestep
        ),
        "overall_pq_risk_score_by_timestep": list(
            metrics.overall_pq_risk_score_by_timestep
        ),
        "phase_a_load_kw_by_timestep": list(metrics.phase_a_load_kw_by_timestep),
        "phase_b_load_kw_by_timestep": list(metrics.phase_b_load_kw_by_timestep),
        "phase_c_load_kw_by_timestep": list(metrics.phase_c_load_kw_by_timestep),
    }


def metrics_from_dict(data: MetricsData) -> Metrics:
    """Rebuild metrics from serialized metric data."""

    return Metrics(
        total_daily_energy=data["total_daily_energy"],
        available_capacity=data["available_capacity"],
        energy_delivery_sufficient=data.get(
            "energy_delivery_sufficient"
        ),
        capacity_sufficiency=data.get("capacity_sufficiency"),
        peak_load=data["peak_load"],
        capacity_utilization=data["capacity_utilization"],
        delivered_energy=data["delivered_energy"],
        unmet_energy=data["unmet_energy"],
        annual_energy=data["annual_energy"],
        configured_connection_capacity_kw=data.get(
            "configured_connection_capacity_kw",
            0.0,
        ),
        required_connection_capacity_kw=data.get(
            "required_connection_capacity_kw",
            0.0,
        ),
        recommended_connection_capacity_kw=data.get(
            "recommended_connection_capacity_kw",
            0.0,
        ),
        planning_margin_percent=data.get("planning_margin_percent", 0.0),
        peak_capacity_margin_kw=data.get("peak_capacity_margin_kw", 0.0),
        peak_capacity_margin_percent=data.get(
            "peak_capacity_margin_percent",
            0.0,
        ),
        connection_capacity_exceeded=data.get(
            "connection_capacity_exceeded",
            False,
        ),
        maximum_capacity_exceedance_kw=data.get(
            "maximum_capacity_exceedance_kw",
            0.0,
        ),
        exceeded_timestep_count=data.get("exceeded_timestep_count", 0),
        capacity_exceedance_duration_hours=data.get(
            "capacity_exceedance_duration_hours",
            0.0,
        ),
        persistent_capacity_exceedance_indicator=data.get(
            "persistent_capacity_exceedance_indicator",
            False,
        ),
        connection_capacity_adequate_indicator=data.get(
            "connection_capacity_adequate_indicator",
            True,
        ),
        connection_capacity_recommendation_reason=data.get(
            "connection_capacity_recommendation_reason",
            CONFIGURED_CONNECTION_CAPACITY_ADEQUATE_REASON,
        ),
        average_transformer_loading_percent=data.get(
            "average_transformer_loading_percent",
            0.0,
        ),
        peak_transformer_loading_percent=data.get(
            "peak_transformer_loading_percent",
            0.0,
        ),
        transformer_overload_indicator=data.get(
            "transformer_overload_indicator",
            False,
        ),
        transformer_overload_duration_hours=data.get(
            "transformer_overload_duration_hours",
            0.0,
        ),
        transformer_maximum_overload_kw=data.get(
            "transformer_maximum_overload_kw",
            0.0,
        ),
        transformer_thermal_risk_level=data.get(
            "transformer_thermal_risk_level",
            THERMAL_RISK_LOW,
        )
        or THERMAL_RISK_LOW,
        maximum_feeder_loading_percent=data.get(
            "maximum_feeder_loading_percent",
            0.0,
        ),
        feeder_overload_indicator=data.get(
            "feeder_overload_indicator",
            False,
        ),
        overloaded_feeder_count=data.get("overloaded_feeder_count", 0),
        highest_feeder_thermal_risk_level=data.get(
            "highest_feeder_thermal_risk_level",
            THERMAL_RISK_LOW,
        )
        or THERMAL_RISK_LOW,
        most_loaded_feeder_id=data.get("most_loaded_feeder_id"),
        peak_feeder_loading_spread_percentage_points=data.get(
            "peak_feeder_loading_spread_percentage_points",
            0.0,
        )
        or 0.0,
        feeder_loading_distribution_label=data.get(
            "feeder_loading_distribution_label",
            FEEDER_LOADING_DISTRIBUTION_NO_FEEDERS,
        )
        or FEEDER_LOADING_DISTRIBUTION_NO_FEEDERS,
        feeder_status_message=data.get(
            "feeder_status_message",
            "No feeder-level load was modeled.",
        )
        or "No feeder-level load was modeled.",
        show_feeder_detail_indicator=data.get(
            "show_feeder_detail_indicator",
            False,
        )
        or False,
        peak_harmonic_risk_score=data.get("peak_harmonic_risk_score", 0.0) or 0.0,
        average_harmonic_risk_score=(
            data.get("average_harmonic_risk_score", 0.0) or 0.0
        ),
        harmonic_risk_duration_hours=(
            data.get("harmonic_risk_duration_hours", 0.0) or 0.0
        ),
        harmonic_risk_level=data.get(
            "harmonic_risk_level",
            POWER_QUALITY_RISK_LOW,
        )
        or POWER_QUALITY_RISK_LOW,
        harmonic_warning_indicator=data.get("harmonic_warning_indicator", False)
        or False,
        peak_current_imbalance_percent=data.get(
            "peak_current_imbalance_percent",
            0.0,
        )
        or 0.0,
        average_current_imbalance_percent=data.get(
            "average_current_imbalance_percent",
            0.0,
        )
        or 0.0,
        imbalance_duration_hours=data.get("imbalance_duration_hours", 0.0) or 0.0,
        current_imbalance_risk_level=data.get(
            "current_imbalance_risk_level",
            POWER_QUALITY_RISK_LOW,
        )
        or POWER_QUALITY_RISK_LOW,
        imbalance_warning_indicator=data.get("imbalance_warning_indicator", False)
        or False,
        overall_pq_risk_score=data.get("overall_pq_risk_score", 0.0) or 0.0,
        overall_pq_risk_level=data.get(
            "overall_pq_risk_level",
            POWER_QUALITY_RISK_LOW,
        )
        or POWER_QUALITY_RISK_LOW,
        overall_pq_warning_indicator=data.get(
            "overall_pq_warning_indicator",
            False,
        )
        or False,
        power_quality_warning_count=data.get("power_quality_warning_count", 0) or 0,
        power_quality_message=data.get("power_quality_message", "") or "",
        average_charger_utilization_percent=data.get(
            "average_charger_utilization_percent",
            0.0,
        ),
        peak_charger_utilization_percent=data.get(
            "peak_charger_utilization_percent",
            0.0,
        ),
        average_occupied_charger_count=data.get(
            "average_occupied_charger_count",
            0.0,
        ),
        peak_occupied_charger_count=data.get("peak_occupied_charger_count", 0),
        charger_shortage_indicator=data.get("charger_shortage_indicator", False),
        queue_present_indicator=data.get("queue_present_indicator", False),
        maximum_queue_length=data.get("maximum_queue_length", 0),
        average_queue_length=data.get("average_queue_length", 0.0),
        queue_duration_hours=data.get("queue_duration_hours", 0.0),
        average_waiting_time_hours=data.get("average_waiting_time_hours", 0.0),
        maximum_waiting_time_hours=data.get("maximum_waiting_time_hours", 0.0),
        charger_service_waiting_tolerance_hours=data.get(
            "charger_service_waiting_tolerance_hours",
            0.5,
        ),
        vehicles_waiting_count=data.get("vehicles_waiting_count", 0),
        vehicles_not_started_count=data.get("vehicles_not_started_count", 0),
        vehicles_with_unmet_energy_count=data.get(
            "vehicles_with_unmet_energy_count",
            0,
        ),
        charger_capacity_vs_demand_balance=data.get(
            "charger_capacity_vs_demand_balance",
            0,
        ),
        required_charger_count=data.get("required_charger_count", 0),
        additional_chargers_required=data.get(
            "additional_chargers_required",
            0,
        ),
        charger_count_sufficient_indicator=data.get(
            "charger_count_sufficient_indicator",
            True,
        ),
        primary_constraint_reason=data.get(
            "primary_constraint_reason",
            NO_PRIMARY_CONSTRAINT_REASON,
        )
        or NO_PRIMARY_CONSTRAINT_REASON,
        feeder_summary_rows=[
            feeder_summary_metrics_from_dict(summary_data)
            for summary_data in (data.get("feeder_summary_rows") or [])
        ],
        transformer_total_load_kw_by_timestep=list(
            data.get("transformer_total_load_kw_by_timestep") or []
        ),
        transformer_loading_percent_by_timestep=list(
            data.get("transformer_loading_percent_by_timestep") or []
        ),
        transformer_overload_kw_by_timestep=list(
            data.get("transformer_overload_kw_by_timestep") or []
        ),
        occupied_charger_count_by_timestep=list(
            data.get("occupied_charger_count_by_timestep") or []
        ),
        waiting_vehicle_count_by_timestep=list(
            data.get("waiting_vehicle_count_by_timestep") or []
        ),
        harmonic_risk_score_by_timestep=list(
            data.get("harmonic_risk_score_by_timestep") or []
        ),
        current_imbalance_percent_by_timestep=list(
            data.get("current_imbalance_percent_by_timestep") or []
        ),
        overall_pq_risk_score_by_timestep=list(
            data.get("overall_pq_risk_score_by_timestep") or []
        ),
        phase_a_load_kw_by_timestep=list(
            data.get("phase_a_load_kw_by_timestep") or []
        ),
        phase_b_load_kw_by_timestep=list(
            data.get("phase_b_load_kw_by_timestep") or []
        ),
        phase_c_load_kw_by_timestep=list(
            data.get("phase_c_load_kw_by_timestep") or []
        ),
    )


def feeder_summary_metrics_to_dict(
    feeder_summary: FeederSummaryMetrics,
) -> FeederSummaryMetricsData:
    """Return a Dash-store-safe dictionary representation of a feeder summary."""

    return {
        "feeder_id": feeder_summary.feeder_id,
        "charger_count": feeder_summary.charger_count,
        "peak_loading_percent": feeder_summary.peak_loading_percent,
        "overload_indicator": feeder_summary.overload_indicator,
        "overload_duration_hours": feeder_summary.overload_duration_hours,
        "maximum_overload_kw": feeder_summary.maximum_overload_kw,
        "thermal_risk_level": feeder_summary.thermal_risk_level,
    }


def feeder_summary_metrics_from_dict(
    data: FeederSummaryMetricsData,
) -> FeederSummaryMetrics:
    """Rebuild one feeder summary row from serialized data."""

    return FeederSummaryMetrics(
        feeder_id=data["feeder_id"],
        charger_count=data["charger_count"],
        peak_loading_percent=data.get("peak_loading_percent", 0.0),
        overload_indicator=data.get("overload_indicator", False),
        overload_duration_hours=data.get("overload_duration_hours", 0.0),
        maximum_overload_kw=data.get("maximum_overload_kw", 0.0),
        thermal_risk_level=data.get("thermal_risk_level", THERMAL_RISK_LOW),
    )
