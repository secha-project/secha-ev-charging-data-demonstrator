"""Core KPI derivation from simulation outputs without planner rerun orchestration."""

from dataclasses import dataclass

from metrics.grid_risk import (
    THERMAL_RISK_LOW,
    classify_thermal_risk,
    highest_thermal_risk_level,
)
from metrics.power_quality import (
    CURRENT_IMBALANCE_HIGH_PERCENT_THRESHOLD,
    CURRENT_IMBALANCE_MODERATE_PERCENT_THRESHOLD,
    HARMONIC_RISK_HIGH_SCORE_THRESHOLD,
    HARMONIC_RISK_MODERATE_SCORE_THRESHOLD,
    POWER_QUALITY_RISK_LOW,
    build_overall_pq_risk_score_series,
    build_power_quality_message,
    calculate_threshold_duration_hours,
    classify_power_quality_risk,
    derive_overall_power_quality_risk_level,
    identify_primary_power_quality_issue,
)
from metrics.shared import (
    FLOATING_POINT_TOLERANCE,
    calculate_annual_energy,
    calculate_average_charger_utilization_percent,
    calculate_average_count,
    calculate_maximum_waiting_time_hours,
    calculate_peak_charger_utilization_percent,
    calculate_peak_load,
    calculate_average_waiting_time_hours,
    collect_started_request_waiting_times,
    copy_full_day_count_series,
    copy_full_day_float_series,
    extract_window_count_values,
    extract_window_values,
)
from metrics.constraint_analysis import (
    calculate_exceedance_values,
    calculate_peak_capacity_margin_percent,
    has_persistent_connection_capacity_exceedance,
    count_exceeded_timesteps,
)
from metrics.metrics import (
    FEEDER_LOADING_BALANCED_SPREAD_THRESHOLD_PERCENTAGE_POINTS,
    FEEDER_LOADING_CONCENTRATED_SPREAD_THRESHOLD_PERCENTAGE_POINTS,
    FEEDER_LOADING_DISTRIBUTION_BALANCED,
    FEEDER_LOADING_DISTRIBUTION_CONCENTRATED,
    FEEDER_LOADING_DISTRIBUTION_NO_FEEDERS,
    FEEDER_LOADING_DISTRIBUTION_SINGLE_FEEDER,
    FEEDER_LOADING_DISTRIBUTION_UNEVEN,
    FeederSummaryMetrics,
    MetricsData,
)
from scenarios import Scenario
from simulation.load_profiles import calculate_delivered_energy, calculate_unmet_energy
from simulation.result import FeederLoadingResult, SimulationResult
from simulation.time import get_timestep_hours


@dataclass(frozen=True)
class _PlannerDiagnosticsInputs:
    """Planner-diagnostic inputs derived from the direct KPI pass."""

    total_daily_energy: float
    available_capacity: float
    energy_delivery_sufficient: bool
    peak_load: float
    capacity_utilization: float
    delivered_energy: float
    unmet_energy: float
    configured_connection_capacity_kw: float
    required_connection_capacity_kw: float
    persistent_capacity_exceedance_indicator: bool
    queue_present_indicator: bool
    maximum_waiting_time_hours: float | None
    charger_service_waiting_tolerance_hours: float
    vehicles_not_started_count: int
    vehicles_with_unmet_energy_count: int


@dataclass(frozen=True)
class _DirectMetricsComputation:
    """Direct KPI outputs plus the planner-diagnostic inputs they expose."""

    metrics_kwargs: MetricsData
    planner_diagnostics_inputs: _PlannerDiagnosticsInputs


def _calculate_direct_metrics_values(
    simulation_result: SimulationResult,
    scenario: Scenario,
) -> _DirectMetricsComputation:
    """Return direct KPI values without planner rerun diagnostics."""

    total_daily_energy = simulation_result.daily_energy_demand
    annual_energy = calculate_annual_energy(total_daily_energy)
    peak_load = calculate_peak_load(simulation_result.delivered_load_profile_kw)
    delivered_energy = calculate_delivered_energy(
        simulation_result.delivered_load_profile_kw
    )
    unmet_energy = calculate_unmet_energy(total_daily_energy, delivered_energy)
    energy_delivery_sufficient = delivered_energy >= total_daily_energy
    configured_connection_capacity = (
        simulation_result.configured_connection_capacity_kw
    )
    requested_peak_load = calculate_peak_load(
        simulation_result.requested_load_profile_kw
    )
    available_capacity = simulation_result.available_site_charging_capacity_kw
    capacity_utilization = _calculate_capacity_utilization(
        peak_load,
        available_capacity,
    )
    transformer_total_load_kw_by_timestep = copy_full_day_float_series(
        simulation_result.grid_loading.transformer_loading.total_load_kw_by_timestep
    )
    transformer_loading_percent_by_timestep = copy_full_day_float_series(
        simulation_result.grid_loading.transformer_loading.loading_percent_by_timestep
    )
    transformer_overload_kw_by_timestep = copy_full_day_float_series(
        simulation_result.grid_loading.transformer_loading.overload_kw_by_timestep
    )
    feeder_summary_rows = _build_feeder_summary_rows(
        simulation_result.grid_loading.feeder_loading_results
    )
    transformer_thermal_risk_level = classify_thermal_risk(
        transformer_loading_percent_by_timestep,
        transformer_overload_kw_by_timestep,
    )
    delivered_window_load_profile_kw = extract_window_values(
        simulation_result.delivered_load_profile_kw,
        scenario,
    )
    occupied_charger_count_window = extract_window_count_values(
        simulation_result.occupied_charger_count_by_timestep,
        scenario,
    )
    requested_charger_slots_window = extract_window_count_values(
        simulation_result.requested_charger_slots_by_timestep,
        scenario,
    )
    waiting_vehicle_count_window = extract_window_count_values(
        simulation_result.waiting_vehicle_count_by_timestep,
        scenario,
    )
    harmonic_risk_score_by_timestep = copy_full_day_float_series(
        simulation_result.power_quality.harmonic_risk_score_by_timestep
    )
    current_imbalance_percent_by_timestep = copy_full_day_float_series(
        simulation_result.power_quality.current_imbalance_percent_by_timestep
    )
    overall_pq_risk_score_by_timestep = copy_full_day_float_series(
        simulation_result.power_quality.overall_pq_risk_score_by_timestep
    ) or copy_full_day_float_series(
        build_overall_pq_risk_score_series(
            harmonic_risk_score_by_timestep,
            current_imbalance_percent_by_timestep,
        )
    )
    phase_a_load_kw_by_timestep = copy_full_day_float_series(
        simulation_result.power_quality.phase_a_load_kw_by_timestep
    )
    phase_b_load_kw_by_timestep = copy_full_day_float_series(
        simulation_result.power_quality.phase_b_load_kw_by_timestep
    )
    phase_c_load_kw_by_timestep = copy_full_day_float_series(
        simulation_result.power_quality.phase_c_load_kw_by_timestep
    )
    started_request_waiting_times_hours = collect_started_request_waiting_times(
        simulation_result
    )
    average_waiting_time_hours = calculate_average_waiting_time_hours(
        started_request_waiting_times_hours,
        request_count=len(simulation_result.charging_requests),
    )
    maximum_waiting_time_hours = calculate_maximum_waiting_time_hours(
        started_request_waiting_times_hours,
        request_count=len(simulation_result.charging_requests),
    )
    charger_service_waiting_tolerance_hours = (
        scenario.charger_service_max_waiting_time_minutes / 60
    )
    exceedance_values = calculate_exceedance_values(
        simulation_result.requested_load_profile_kw,
        configured_connection_capacity,
    )
    exceeded_timestep_count = count_exceeded_timesteps(exceedance_values)
    persistent_capacity_exceedance_indicator = (
        has_persistent_connection_capacity_exceedance(
            exceeded_timestep_count
        )
    )
    peak_requested_charger_slots = int(
        max(requested_charger_slots_window, default=0)
    )
    queue_present_indicator = any(
        waiting_count > 0 for waiting_count in waiting_vehicle_count_window
    )
    vehicles_not_started_count = sum(
        request.charging_start_timestep is None
        for request in simulation_result.charging_requests
    )
    vehicles_with_unmet_energy_count = sum(
        request.unmet_energy_kwh > FLOATING_POINT_TOLERANCE
        for request in simulation_result.charging_requests
    )
    harmonic_risk_duration_hours = calculate_threshold_duration_hours(
        harmonic_risk_score_by_timestep,
        threshold=HARMONIC_RISK_MODERATE_SCORE_THRESHOLD,
    )
    peak_harmonic_risk_score = max(harmonic_risk_score_by_timestep, default=0.0)
    harmonic_risk_level = classify_power_quality_risk(
        harmonic_risk_score_by_timestep,
        moderate_threshold=HARMONIC_RISK_MODERATE_SCORE_THRESHOLD,
        high_threshold=HARMONIC_RISK_HIGH_SCORE_THRESHOLD,
    )
    harmonic_warning_indicator = harmonic_risk_level != POWER_QUALITY_RISK_LOW
    imbalance_duration_hours = calculate_threshold_duration_hours(
        current_imbalance_percent_by_timestep,
        threshold=CURRENT_IMBALANCE_MODERATE_PERCENT_THRESHOLD,
    )
    peak_current_imbalance_percent = max(
        current_imbalance_percent_by_timestep,
        default=0.0,
    )
    current_imbalance_risk_level = classify_power_quality_risk(
        current_imbalance_percent_by_timestep,
        moderate_threshold=CURRENT_IMBALANCE_MODERATE_PERCENT_THRESHOLD,
        high_threshold=CURRENT_IMBALANCE_HIGH_PERCENT_THRESHOLD,
    )
    imbalance_warning_indicator = (
        current_imbalance_risk_level != POWER_QUALITY_RISK_LOW
    )
    primary_power_quality_issue = identify_primary_power_quality_issue(
        peak_harmonic_risk_score=peak_harmonic_risk_score,
        peak_current_imbalance_percent=peak_current_imbalance_percent,
    )
    overall_pq_risk_level = derive_overall_power_quality_risk_level(
        overall_pq_risk_score_by_timestep=overall_pq_risk_score_by_timestep,
        harmonic_risk_level=harmonic_risk_level,
        current_imbalance_risk_level=current_imbalance_risk_level,
        primary_issue=primary_power_quality_issue,
    )
    overall_pq_warning_indicator = overall_pq_risk_level != POWER_QUALITY_RISK_LOW
    power_quality_warning_count = sum(
        (
            harmonic_warning_indicator,
            imbalance_warning_indicator,
            overall_pq_warning_indicator,
        )
    )
    power_quality_message = build_power_quality_message(
        overall_pq_risk_level=overall_pq_risk_level,
        harmonic_risk_level=harmonic_risk_level,
        current_imbalance_risk_level=current_imbalance_risk_level,
        primary_issue=primary_power_quality_issue,
    )

    return _DirectMetricsComputation(
        metrics_kwargs={
            "total_daily_energy": total_daily_energy,
            "available_capacity": available_capacity,
            "energy_delivery_sufficient": energy_delivery_sufficient,
            "peak_load": peak_load,
            "capacity_utilization": capacity_utilization,
            "delivered_energy": delivered_energy,
            "unmet_energy": unmet_energy,
            "annual_energy": annual_energy,
            "configured_connection_capacity_kw": configured_connection_capacity,
            "required_connection_capacity_kw": requested_peak_load,
            "planning_margin_percent": scenario.planning_margin_percent,
            "peak_capacity_margin_kw": (
                configured_connection_capacity - requested_peak_load
            ),
            "peak_capacity_margin_percent": calculate_peak_capacity_margin_percent(
                configured_connection_capacity,
                requested_peak_load,
            ),
            "connection_capacity_exceeded": any(
                exceedance_kw > 0.0 for exceedance_kw in exceedance_values
            ),
            "maximum_capacity_exceedance_kw": max(
                exceedance_values,
                default=0.0,
            ),
            "exceeded_timestep_count": exceeded_timestep_count,
            "capacity_exceedance_duration_hours": (
                exceeded_timestep_count * get_timestep_hours()
            ),
            "persistent_capacity_exceedance_indicator": (
                persistent_capacity_exceedance_indicator
            ),
            "average_transformer_loading_percent": calculate_average_count(
                transformer_loading_percent_by_timestep
            ),
            "peak_transformer_loading_percent": max(
                transformer_loading_percent_by_timestep,
                default=0.0,
            ),
            "transformer_overload_indicator": any(
                overload_kw > 0.0
                for overload_kw in transformer_overload_kw_by_timestep
            ),
            "transformer_overload_duration_hours": (
                sum(
                    overload_kw > 0.0
                    for overload_kw in transformer_overload_kw_by_timestep
                )
                * get_timestep_hours()
            ),
            "transformer_maximum_overload_kw": max(
                transformer_overload_kw_by_timestep,
                default=0.0,
            ),
            "transformer_thermal_risk_level": transformer_thermal_risk_level,
            "maximum_feeder_loading_percent": max(
                (
                    feeder_summary.peak_loading_percent
                    for feeder_summary in feeder_summary_rows
                ),
                default=0.0,
            ),
            "feeder_overload_indicator": any(
                feeder_summary.overload_indicator
                for feeder_summary in feeder_summary_rows
            ),
            "overloaded_feeder_count": sum(
                feeder_summary.overload_indicator
                for feeder_summary in feeder_summary_rows
            ),
            "highest_feeder_thermal_risk_level": highest_thermal_risk_level(
                [
                    feeder_summary.thermal_risk_level
                    for feeder_summary in feeder_summary_rows
                ]
            ),
            "most_loaded_feeder_id": _most_loaded_feeder_id(
                feeder_summary_rows
            ),
            "peak_feeder_loading_spread_percentage_points": (
                _calculate_peak_feeder_loading_spread_percentage_points(
                    feeder_summary_rows
                )
            ),
            "feeder_loading_distribution_label": (
                _classify_feeder_loading_distribution(feeder_summary_rows)
            ),
            "feeder_status_message": _build_feeder_status_message(
                feeder_summary_rows
            ),
            "show_feeder_detail_indicator": _should_show_feeder_detail(
                feeder_summary_rows
            ),
            "peak_harmonic_risk_score": peak_harmonic_risk_score,
            "average_harmonic_risk_score": calculate_average_count(
                harmonic_risk_score_by_timestep
            ),
            "harmonic_risk_duration_hours": harmonic_risk_duration_hours,
            "harmonic_risk_level": harmonic_risk_level,
            "harmonic_warning_indicator": harmonic_warning_indicator,
            "peak_current_imbalance_percent": peak_current_imbalance_percent,
            "average_current_imbalance_percent": calculate_average_count(
                current_imbalance_percent_by_timestep
            ),
            "imbalance_duration_hours": imbalance_duration_hours,
            "current_imbalance_risk_level": current_imbalance_risk_level,
            "imbalance_warning_indicator": imbalance_warning_indicator,
            "overall_pq_risk_score": max(
                overall_pq_risk_score_by_timestep,
                default=0.0,
            ),
            "overall_pq_risk_level": overall_pq_risk_level,
            "overall_pq_warning_indicator": overall_pq_warning_indicator,
            "power_quality_warning_count": power_quality_warning_count,
            "power_quality_message": power_quality_message,
            "average_charger_utilization_percent": (
                calculate_average_charger_utilization_percent(
                    delivered_window_load_profile_kw,
                    simulation_result.installed_charger_capacity_kw,
                    simulation_result.daily_energy_demand,
                )
            ),
            "peak_charger_utilization_percent": (
                calculate_peak_charger_utilization_percent(
                    delivered_window_load_profile_kw,
                    simulation_result.installed_charger_capacity_kw,
                    simulation_result.daily_energy_demand,
                )
            ),
            "average_occupied_charger_count": calculate_average_count(
                occupied_charger_count_window
            ),
            "peak_occupied_charger_count": int(
                max(occupied_charger_count_window, default=0)
            ),
            "charger_shortage_indicator": any(
                requested_count > scenario.charger_count
                for requested_count in requested_charger_slots_window
            ),
            "queue_present_indicator": queue_present_indicator,
            "maximum_queue_length": int(
                max(waiting_vehicle_count_window, default=0)
            ),
            "average_queue_length": calculate_average_count(
                waiting_vehicle_count_window
            ),
            "queue_duration_hours": (
                sum(
                    waiting_count > 0
                    for waiting_count in waiting_vehicle_count_window
                )
                * get_timestep_hours()
            ),
            "average_waiting_time_hours": average_waiting_time_hours,
            "maximum_waiting_time_hours": maximum_waiting_time_hours,
            "charger_service_waiting_tolerance_hours": (
                charger_service_waiting_tolerance_hours
            ),
            "vehicles_waiting_count": sum(
                waiting_time_hours > 0.0
                for waiting_time_hours in started_request_waiting_times_hours
            ),
            "vehicles_not_started_count": vehicles_not_started_count,
            "vehicles_with_unmet_energy_count": (
                vehicles_with_unmet_energy_count
            ),
            "charger_capacity_vs_demand_balance": (
                scenario.charger_count - peak_requested_charger_slots
            ),
            "feeder_summary_rows": feeder_summary_rows,
            "transformer_total_load_kw_by_timestep": (
                transformer_total_load_kw_by_timestep
            ),
            "transformer_loading_percent_by_timestep": (
                transformer_loading_percent_by_timestep
            ),
            "transformer_overload_kw_by_timestep": (
                transformer_overload_kw_by_timestep
            ),
            "occupied_charger_count_by_timestep": copy_full_day_count_series(
                simulation_result.occupied_charger_count_by_timestep
            ),
            "waiting_vehicle_count_by_timestep": copy_full_day_count_series(
                simulation_result.waiting_vehicle_count_by_timestep
            ),
            "harmonic_risk_score_by_timestep": harmonic_risk_score_by_timestep,
            "current_imbalance_percent_by_timestep": (
                current_imbalance_percent_by_timestep
            ),
            "overall_pq_risk_score_by_timestep": (
                overall_pq_risk_score_by_timestep
            ),
            "phase_a_load_kw_by_timestep": phase_a_load_kw_by_timestep,
            "phase_b_load_kw_by_timestep": phase_b_load_kw_by_timestep,
            "phase_c_load_kw_by_timestep": phase_c_load_kw_by_timestep,
        },
        planner_diagnostics_inputs=_PlannerDiagnosticsInputs(
            total_daily_energy=total_daily_energy,
            available_capacity=available_capacity,
            energy_delivery_sufficient=energy_delivery_sufficient,
            peak_load=peak_load,
            capacity_utilization=capacity_utilization,
            delivered_energy=delivered_energy,
            unmet_energy=unmet_energy,
            configured_connection_capacity_kw=configured_connection_capacity,
            required_connection_capacity_kw=requested_peak_load,
            persistent_capacity_exceedance_indicator=(
                persistent_capacity_exceedance_indicator
            ),
            queue_present_indicator=queue_present_indicator,
            maximum_waiting_time_hours=maximum_waiting_time_hours,
            charger_service_waiting_tolerance_hours=(
                charger_service_waiting_tolerance_hours
            ),
            vehicles_not_started_count=vehicles_not_started_count,
            vehicles_with_unmet_energy_count=(
                vehicles_with_unmet_energy_count
            ),
        ),
    )


def _calculate_capacity_utilization(
    peak_load: float,
    available_capacity: float,
) -> float:
    if available_capacity <= 0:
        return 0.0

    utilization = peak_load / available_capacity * 100.0
    return min(max(utilization, 0.0), 100.0)


def _build_feeder_summary_rows(
    feeder_loading_results: list[FeederLoadingResult],
) -> list[FeederSummaryMetrics]:
    """Return planner-facing feeder summary rows from raw feeder series."""

    feeder_summary_rows: list[FeederSummaryMetrics] = []
    for feeder_result in feeder_loading_results:
        feeder_summary_rows.append(
            FeederSummaryMetrics(
                feeder_id=feeder_result.feeder_id,
                charger_count=feeder_result.charger_count,
                peak_loading_percent=max(
                    feeder_result.loading_percent_by_timestep,
                    default=0.0,
                ),
                overload_indicator=any(
                    overload_kw > 0.0
                    for overload_kw in feeder_result.overload_kw_by_timestep
                ),
                overload_duration_hours=(
                    sum(
                        overload_kw > 0.0
                        for overload_kw in feeder_result.overload_kw_by_timestep
                    )
                    * get_timestep_hours()
                ),
                maximum_overload_kw=max(
                    feeder_result.overload_kw_by_timestep,
                    default=0.0,
                ),
                thermal_risk_level=classify_thermal_risk(
                    feeder_result.loading_percent_by_timestep,
                    feeder_result.overload_kw_by_timestep,
                ),
            )
        )
    return feeder_summary_rows


def _select_most_loaded_feeder(
    feeder_summary_rows: list[FeederSummaryMetrics],
) -> FeederSummaryMetrics | None:
    if not feeder_summary_rows:
        return None

    return max(
        feeder_summary_rows,
        key=lambda feeder_summary: feeder_summary.peak_loading_percent,
    )


def _most_loaded_feeder_id(
    feeder_summary_rows: list[FeederSummaryMetrics],
) -> str | None:
    most_loaded_feeder = _select_most_loaded_feeder(feeder_summary_rows)
    if most_loaded_feeder is None:
        return None
    return most_loaded_feeder.feeder_id


def _calculate_peak_feeder_loading_spread_percentage_points(
    feeder_summary_rows: list[FeederSummaryMetrics],
) -> float:
    if not feeder_summary_rows:
        return 0.0

    peak_loading_percent_values = [
        feeder_summary.peak_loading_percent
        for feeder_summary in feeder_summary_rows
    ]
    return max(peak_loading_percent_values) - min(peak_loading_percent_values)


def _classify_feeder_loading_distribution(
    feeder_summary_rows: list[FeederSummaryMetrics],
) -> str:
    if not feeder_summary_rows:
        return FEEDER_LOADING_DISTRIBUTION_NO_FEEDERS

    if len(feeder_summary_rows) == 1:
        return FEEDER_LOADING_DISTRIBUTION_SINGLE_FEEDER

    peak_loading_spread = _calculate_peak_feeder_loading_spread_percentage_points(
        feeder_summary_rows
    )

    if (
        peak_loading_spread
        <= FEEDER_LOADING_BALANCED_SPREAD_THRESHOLD_PERCENTAGE_POINTS
    ):
        return FEEDER_LOADING_DISTRIBUTION_BALANCED

    if (
        peak_loading_spread
        <= FEEDER_LOADING_CONCENTRATED_SPREAD_THRESHOLD_PERCENTAGE_POINTS
    ):
        return FEEDER_LOADING_DISTRIBUTION_UNEVEN

    return FEEDER_LOADING_DISTRIBUTION_CONCENTRATED


def _build_feeder_status_message(
    feeder_summary_rows: list[FeederSummaryMetrics],
) -> str:
    if not feeder_summary_rows:
        return "No feeder-level load was modeled."

    most_loaded_feeder = _select_most_loaded_feeder(feeder_summary_rows)
    assert most_loaded_feeder is not None

    overloaded_feeder_count = sum(
        feeder_summary.overload_indicator
        for feeder_summary in feeder_summary_rows
    )
    highest_feeder_risk_level = highest_thermal_risk_level(
        [
            feeder_summary.thermal_risk_level
            for feeder_summary in feeder_summary_rows
        ]
    )
    distribution_label = _classify_feeder_loading_distribution(
        feeder_summary_rows
    )

    if overloaded_feeder_count > 0:
        if overloaded_feeder_count == 1:
            return (
                "1 feeder is overloaded. "
                f"{most_loaded_feeder.feeder_id} is the most loaded feeder."
            )
        return (
            f"{overloaded_feeder_count} feeders are overloaded. "
            f"{most_loaded_feeder.feeder_id} is the most loaded feeder."
        )

    if highest_feeder_risk_level != THERMAL_RISK_LOW:
        return (
            "No feeder overload is indicated, but "
            f"{most_loaded_feeder.feeder_id} is the most loaded feeder and "
            "modeled feeder stress is elevated."
        )

    if distribution_label == FEEDER_LOADING_DISTRIBUTION_BALANCED:
        return "All feeders are evenly loaded. No local feeder bottleneck detected."

    if distribution_label == FEEDER_LOADING_DISTRIBUTION_SINGLE_FEEDER:
        return (
            f"{most_loaded_feeder.feeder_id} is the only modeled feeder. "
            "No feeder overload is indicated."
        )

    if distribution_label == FEEDER_LOADING_DISTRIBUTION_CONCENTRATED:
        return (
            "Feeder loading is concentrated on "
            f"{most_loaded_feeder.feeder_id}. Review local feeder balance."
        )

    return (
        "Feeder loading is uneven. "
        f"{most_loaded_feeder.feeder_id} is the most loaded feeder."
    )


def _should_show_feeder_detail(
    feeder_summary_rows: list[FeederSummaryMetrics],
) -> bool:
    if not feeder_summary_rows:
        return False

    if any(
        feeder_summary.overload_indicator
        for feeder_summary in feeder_summary_rows
    ):
        return True

    if highest_thermal_risk_level(
        [
            feeder_summary.thermal_risk_level
            for feeder_summary in feeder_summary_rows
        ]
    ) != THERMAL_RISK_LOW:
        return True

    if len(feeder_summary_rows) <= 1:
        return False

    return (
        _calculate_peak_feeder_loading_spread_percentage_points(
            feeder_summary_rows
        )
        > FEEDER_LOADING_BALANCED_SPREAD_THRESHOLD_PERCENTAGE_POINTS
    )
