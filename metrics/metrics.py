"""Public Metrics facade with stable dataclasses, constants, and APIs."""

import sys
from dataclasses import dataclass, field
from typing import Any

from metrics.constraint_analysis import (
    CHARGER_AVAILABILITY_CONSTRAINT_REASON,
    CHARGER_POWER_CONSTRAINT_REASON,
    CHARGING_WINDOW_CONSTRAINT_REASON,
    CONFIGURED_CONNECTION_CAPACITY_ADEQUATE_REASON,
    CONNECTION_CAPACITY_EXCEEDANCE_PERSISTENCE_TIMESTEP_THRESHOLD,
    GRID_CONNECTION_CAPACITY_CONSTRAINT_REASON,
    GRID_CONNECTION_SERVICE_PRESSURE_REASON,
    MIXED_CONSTRAINT_REASON,
    NO_PRIMARY_CONSTRAINT_REASON,
    PERSISTENT_CONNECTION_CAPACITY_EXCEEDANCE_REASON,
    PRIMARY_CONSTRAINT_REASON_LABELS,
    calculate_exceedance_values,
    calculate_peak_capacity_margin_percent,
    calculate_recommended_connection_capacity_kw,
    classify_primary_constraint_reason,
    connection_capacity_is_adequate,
    count_exceeded_timesteps,
    format_primary_constraint_reason_label,
    has_persistent_connection_capacity_exceedance,
    resolve_connection_capacity_recommendation_reason,
)
from metrics.grid_risk import THERMAL_RISK_LOW
from metrics.power_quality import POWER_QUALITY_RISK_LOW
from metrics.shared import (
    DAYS_PER_YEAR,
    FLOATING_POINT_TOLERANCE,
    PERCENT_MULTIPLIER,
    calculate_annual_energy,
    calculate_average_charger_utilization_percent,
    calculate_average_count,
    calculate_average_waiting_time_hours,
    calculate_maximum_waiting_time_hours,
    calculate_peak_charger_utilization_percent,
    calculate_peak_load,
    collect_started_request_waiting_times,
    copy_full_day_count_series,
    copy_full_day_float_series,
    extract_window_count_values,
    extract_window_values,
)
from scenarios import Scenario
from simulation.result import SimulationResult


FEEDER_LOADING_BALANCED_SPREAD_THRESHOLD_PERCENTAGE_POINTS = 5.0
FEEDER_LOADING_CONCENTRATED_SPREAD_THRESHOLD_PERCENTAGE_POINTS = 20.0
FEEDER_LOADING_DISTRIBUTION_NO_FEEDERS = "No feeders modeled"
FEEDER_LOADING_DISTRIBUTION_SINGLE_FEEDER = "Single feeder"
FEEDER_LOADING_DISTRIBUTION_BALANCED = "Balanced"
FEEDER_LOADING_DISTRIBUTION_UNEVEN = "Uneven"
FEEDER_LOADING_DISTRIBUTION_CONCENTRATED = "Concentrated"

MetricsData = dict[str, Any]
FeederSummaryMetricsData = dict[str, Any]

_SEQUENCE_METRIC_FIELD_NAMES = (
    "feeder_summary_rows",
    "transformer_total_load_kw_by_timestep",
    "transformer_loading_percent_by_timestep",
    "transformer_overload_kw_by_timestep",
    "occupied_charger_count_by_timestep",
    "waiting_vehicle_count_by_timestep",
    "harmonic_risk_score_by_timestep",
    "current_imbalance_percent_by_timestep",
    "overall_pq_risk_score_by_timestep",
    "phase_a_load_kw_by_timestep",
    "phase_b_load_kw_by_timestep",
    "phase_c_load_kw_by_timestep",
)


@dataclass(frozen=True)
class FeederSummaryMetrics:
    """Planner-facing feeder summary row derived from raw feeder series."""

    feeder_id: str
    charger_count: int
    peak_loading_percent: float = 0.0
    overload_indicator: bool = False
    overload_duration_hours: float = 0.0
    maximum_overload_kw: float = 0.0
    thermal_risk_level: str = THERMAL_RISK_LOW


@dataclass(frozen=True, init=False)
class Metrics:
    """Reusable metrics derived from raw simulation outputs."""

    total_daily_energy: float
    available_capacity: float
    energy_delivery_sufficient: bool
    peak_load: float = 0.0
    capacity_utilization: float = 0.0
    delivered_energy: float = 0.0
    unmet_energy: float = 0.0
    annual_energy: float = 0.0
    configured_connection_capacity_kw: float = 0.0
    required_connection_capacity_kw: float = 0.0
    recommended_connection_capacity_kw: float = 0.0
    planning_margin_percent: float = 0.0
    peak_capacity_margin_kw: float = 0.0
    peak_capacity_margin_percent: float | None = 0.0
    connection_capacity_exceeded: bool = False
    maximum_capacity_exceedance_kw: float = 0.0
    exceeded_timestep_count: int = 0
    capacity_exceedance_duration_hours: float = 0.0
    persistent_capacity_exceedance_indicator: bool = False
    connection_capacity_adequate_indicator: bool = True
    connection_capacity_recommendation_reason: str = (
        CONFIGURED_CONNECTION_CAPACITY_ADEQUATE_REASON
    )
    average_transformer_loading_percent: float = 0.0
    peak_transformer_loading_percent: float = 0.0
    transformer_overload_indicator: bool = False
    transformer_overload_duration_hours: float = 0.0
    transformer_maximum_overload_kw: float = 0.0
    transformer_thermal_risk_level: str = THERMAL_RISK_LOW
    maximum_feeder_loading_percent: float = 0.0
    feeder_overload_indicator: bool = False
    overloaded_feeder_count: int = 0
    highest_feeder_thermal_risk_level: str = THERMAL_RISK_LOW
    most_loaded_feeder_id: str | None = None
    peak_feeder_loading_spread_percentage_points: float = 0.0
    feeder_loading_distribution_label: str = FEEDER_LOADING_DISTRIBUTION_NO_FEEDERS
    feeder_status_message: str = "No feeder-level load was modeled."
    show_feeder_detail_indicator: bool = False
    peak_harmonic_risk_score: float = 0.0
    average_harmonic_risk_score: float = 0.0
    harmonic_risk_duration_hours: float = 0.0
    harmonic_risk_level: str = POWER_QUALITY_RISK_LOW
    harmonic_warning_indicator: bool = False
    peak_current_imbalance_percent: float = 0.0
    average_current_imbalance_percent: float = 0.0
    imbalance_duration_hours: float = 0.0
    current_imbalance_risk_level: str = POWER_QUALITY_RISK_LOW
    imbalance_warning_indicator: bool = False
    overall_pq_risk_score: float = 0.0
    overall_pq_risk_level: str = POWER_QUALITY_RISK_LOW
    overall_pq_warning_indicator: bool = False
    power_quality_warning_count: int = 0
    power_quality_message: str = ""
    average_charger_utilization_percent: float | None = 0.0
    peak_charger_utilization_percent: float | None = 0.0
    average_occupied_charger_count: float = 0.0
    peak_occupied_charger_count: int = 0
    charger_shortage_indicator: bool = False
    queue_present_indicator: bool = False
    maximum_queue_length: int = 0
    average_queue_length: float = 0.0
    queue_duration_hours: float = 0.0
    average_waiting_time_hours: float | None = 0.0
    maximum_waiting_time_hours: float | None = 0.0
    charger_service_waiting_tolerance_hours: float = 0.5
    vehicles_waiting_count: int = 0
    vehicles_not_started_count: int = 0
    vehicles_with_unmet_energy_count: int = 0
    charger_capacity_vs_demand_balance: int = 0
    required_charger_count: int | None = 0
    additional_chargers_required: int | None = 0
    charger_count_sufficient_indicator: bool = True
    primary_constraint_reason: str = NO_PRIMARY_CONSTRAINT_REASON
    feeder_summary_rows: list[FeederSummaryMetrics] = field(default_factory=list)
    transformer_total_load_kw_by_timestep: list[float] = field(default_factory=list)
    transformer_loading_percent_by_timestep: list[float] = field(
        default_factory=list
    )
    transformer_overload_kw_by_timestep: list[float] = field(default_factory=list)
    occupied_charger_count_by_timestep: list[int] = field(default_factory=list)
    waiting_vehicle_count_by_timestep: list[int] = field(default_factory=list)
    harmonic_risk_score_by_timestep: list[float] = field(default_factory=list)
    current_imbalance_percent_by_timestep: list[float] = field(default_factory=list)
    overall_pq_risk_score_by_timestep: list[float] = field(default_factory=list)
    phase_a_load_kw_by_timestep: list[float] = field(default_factory=list)
    phase_b_load_kw_by_timestep: list[float] = field(default_factory=list)
    phase_c_load_kw_by_timestep: list[float] = field(default_factory=list)

    def __init__(
        self,
        total_daily_energy: float,
        available_capacity: float,
        energy_delivery_sufficient: bool | None = None,
        peak_load: float = 0.0,
        capacity_utilization: float = 0.0,
        delivered_energy: float = 0.0,
        unmet_energy: float = 0.0,
        annual_energy: float = 0.0,
        configured_connection_capacity_kw: float = 0.0,
        required_connection_capacity_kw: float = 0.0,
        recommended_connection_capacity_kw: float = 0.0,
        planning_margin_percent: float = 0.0,
        peak_capacity_margin_kw: float = 0.0,
        peak_capacity_margin_percent: float | None = 0.0,
        connection_capacity_exceeded: bool = False,
        maximum_capacity_exceedance_kw: float = 0.0,
        exceeded_timestep_count: int = 0,
        capacity_exceedance_duration_hours: float = 0.0,
        persistent_capacity_exceedance_indicator: bool = False,
        connection_capacity_adequate_indicator: bool = True,
        connection_capacity_recommendation_reason: str = (
            CONFIGURED_CONNECTION_CAPACITY_ADEQUATE_REASON
        ),
        average_transformer_loading_percent: float = 0.0,
        peak_transformer_loading_percent: float = 0.0,
        transformer_overload_indicator: bool = False,
        transformer_overload_duration_hours: float = 0.0,
        transformer_maximum_overload_kw: float = 0.0,
        transformer_thermal_risk_level: str = THERMAL_RISK_LOW,
        maximum_feeder_loading_percent: float = 0.0,
        feeder_overload_indicator: bool = False,
        overloaded_feeder_count: int = 0,
        highest_feeder_thermal_risk_level: str = THERMAL_RISK_LOW,
        most_loaded_feeder_id: str | None = None,
        peak_feeder_loading_spread_percentage_points: float = 0.0,
        feeder_loading_distribution_label: str = (
            FEEDER_LOADING_DISTRIBUTION_NO_FEEDERS
        ),
        feeder_status_message: str = "No feeder-level load was modeled.",
        show_feeder_detail_indicator: bool = False,
        peak_harmonic_risk_score: float = 0.0,
        average_harmonic_risk_score: float = 0.0,
        harmonic_risk_duration_hours: float = 0.0,
        harmonic_risk_level: str = POWER_QUALITY_RISK_LOW,
        harmonic_warning_indicator: bool = False,
        peak_current_imbalance_percent: float = 0.0,
        average_current_imbalance_percent: float = 0.0,
        imbalance_duration_hours: float = 0.0,
        current_imbalance_risk_level: str = POWER_QUALITY_RISK_LOW,
        imbalance_warning_indicator: bool = False,
        overall_pq_risk_score: float = 0.0,
        overall_pq_risk_level: str = POWER_QUALITY_RISK_LOW,
        overall_pq_warning_indicator: bool = False,
        power_quality_warning_count: int = 0,
        power_quality_message: str = "",
        average_charger_utilization_percent: float | None = 0.0,
        peak_charger_utilization_percent: float | None = 0.0,
        average_occupied_charger_count: float = 0.0,
        peak_occupied_charger_count: int = 0,
        charger_shortage_indicator: bool = False,
        queue_present_indicator: bool = False,
        maximum_queue_length: int = 0,
        average_queue_length: float = 0.0,
        queue_duration_hours: float = 0.0,
        average_waiting_time_hours: float | None = 0.0,
        maximum_waiting_time_hours: float | None = 0.0,
        charger_service_waiting_tolerance_hours: float = 0.5,
        vehicles_waiting_count: int = 0,
        vehicles_not_started_count: int = 0,
        vehicles_with_unmet_energy_count: int = 0,
        charger_capacity_vs_demand_balance: int = 0,
        required_charger_count: int | None = 0,
        additional_chargers_required: int | None = 0,
        charger_count_sufficient_indicator: bool = True,
        primary_constraint_reason: str = NO_PRIMARY_CONSTRAINT_REASON,
        feeder_summary_rows: list[FeederSummaryMetrics] | None = None,
        transformer_total_load_kw_by_timestep: list[float] | None = None,
        transformer_loading_percent_by_timestep: list[float] | None = None,
        transformer_overload_kw_by_timestep: list[float] | None = None,
        occupied_charger_count_by_timestep: list[int] | None = None,
        waiting_vehicle_count_by_timestep: list[int] | None = None,
        harmonic_risk_score_by_timestep: list[float] | None = None,
        current_imbalance_percent_by_timestep: list[float] | None = None,
        overall_pq_risk_score_by_timestep: list[float] | None = None,
        phase_a_load_kw_by_timestep: list[float] | None = None,
        phase_b_load_kw_by_timestep: list[float] | None = None,
        phase_c_load_kw_by_timestep: list[float] | None = None,
        *,
        capacity_sufficiency: bool | None = None,
    ) -> None:
        """Build metrics with compatibility for legacy sufficiency naming."""
        resolved_energy_delivery_sufficient = _resolve_energy_delivery_sufficiency(
            energy_delivery_sufficient,
            capacity_sufficiency,
        )
        values = locals().copy()
        values.pop("self")
        values.pop("capacity_sufficiency")
        values.pop("resolved_energy_delivery_sufficient")
        values["energy_delivery_sufficient"] = (
            resolved_energy_delivery_sufficient
        )
        for field_name in _SEQUENCE_METRIC_FIELD_NAMES:
            values[field_name] = list(values[field_name] or [])
        for field_name, value in values.items():
            object.__setattr__(self, field_name, value)

    @property
    def capacity_sufficiency(self) -> bool:
        """Return the legacy sufficiency flag name for compatibility."""
        return self.energy_delivery_sufficient


def _resolve_energy_delivery_sufficiency(
    energy_delivery_sufficient: bool | None,
    capacity_sufficiency: bool | None,
) -> bool:
    """Resolve the canonical sufficiency flag from old and new names."""
    if (
        energy_delivery_sufficient is not None
        and capacity_sufficiency is not None
        and energy_delivery_sufficient != capacity_sufficiency
    ):
        raise ValueError(
            "energy_delivery_sufficient and capacity_sufficiency must match "
            "when both are provided."
        )

    if energy_delivery_sufficient is not None:
        return energy_delivery_sufficient

    if capacity_sufficiency is not None:
        return capacity_sufficiency

    raise TypeError(
        "Metrics requires energy_delivery_sufficient or capacity_sufficiency."
    )


from metrics.core_metrics import (  # noqa: E402
    _DirectMetricsComputation,
    _PlannerDiagnosticsInputs,
    _calculate_direct_metrics_values,
)
from metrics.planner_diagnostics import (  # noqa: E402
    _build_planner_context_metrics,
    _calculate_planner_diagnostic_values,
)
from metrics.serialization import (  # noqa: E402
    feeder_summary_metrics_from_dict,
    feeder_summary_metrics_to_dict,
    metrics_from_dict,
    metrics_to_dict,
)

_calculate_average_waiting_time_hours = calculate_average_waiting_time_hours
_calculate_exceedance_values = calculate_exceedance_values
_calculate_maximum_waiting_time_hours = calculate_maximum_waiting_time_hours
_calculate_peak_capacity_margin_percent = calculate_peak_capacity_margin_percent
_calculate_peak_load = calculate_peak_load
_classify_primary_constraint_reason = classify_primary_constraint_reason
_collect_started_request_waiting_times = collect_started_request_waiting_times
_connection_capacity_is_adequate = connection_capacity_is_adequate
_copy_full_day_count_series = copy_full_day_count_series
_copy_full_day_float_series = copy_full_day_float_series
_count_exceeded_timesteps = count_exceeded_timesteps
_extract_window_count_values = extract_window_count_values
_extract_window_values = extract_window_values
_has_persistent_connection_capacity_exceedance = (
    has_persistent_connection_capacity_exceedance
)
_resolve_connection_capacity_recommendation_reason = (
    resolve_connection_capacity_recommendation_reason
)


def calculate_metrics(
    simulation_result: SimulationResult,
    scenario: Scenario,
    *,
    include_primary_constraint_reason: bool = True,
    include_charger_count_recommendation: bool = True,
) -> Metrics:
    """Calculate reusable metrics from one completed simulation result."""
    metrics_module = sys.modules[__name__]
    direct_metrics = metrics_module._calculate_direct_metrics_values(
        simulation_result,
        scenario,
    )
    planner_diagnostics = metrics_module._calculate_planner_diagnostic_values(
        simulation_result,
        scenario,
        direct_metrics.planner_diagnostics_inputs,
        include_primary_constraint_reason=(
            include_primary_constraint_reason
        ),
        include_charger_count_recommendation=(
            include_charger_count_recommendation
        ),
    )
    return Metrics(
        **direct_metrics.metrics_kwargs,
        **planner_diagnostics,
    )
