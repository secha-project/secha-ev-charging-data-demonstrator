from dataclasses import replace
from datetime import time

import pytest

from metrics import (
    calculate_comparison_metrics,
    calculate_metrics,
    evaluate_charger_count_service_rule,
    search_minimum_feasible_charger_count,
)
from scenarios import (
    ArrivalMode,
    ArrivalProfileShape,
    ChargingStrategy,
    DEFAULT_SCENARIO_PRESET_ID,
    DepartureMode,
    PUBLIC_FAST_CHARGING_PRESET_ID,
    Scenario,
    WORKPLACE_CHARGING_PRESET_ID,
    create_internal_scenario,
    get_scenario_preset,
)
from simulation import simulate
from simulation.time import get_timestep_hours


def _calculate_reference_metrics(scenario: Scenario):
    result = simulate(scenario)
    metrics = calculate_metrics(result, scenario)
    return result, metrics


def _calculate_reference_strategy_comparison(base_scenario: Scenario):
    uncontrolled_scenario = replace(
        base_scenario,
        charging_strategy=ChargingStrategy.UNCONTROLLED,
    )
    smart_scenario = replace(
        base_scenario,
        charging_strategy=ChargingStrategy.SMART,
    )
    uncontrolled_result, uncontrolled_metrics = _calculate_reference_metrics(
        uncontrolled_scenario
    )
    smart_result, smart_metrics = _calculate_reference_metrics(smart_scenario)
    comparison_metrics = calculate_comparison_metrics(
        uncontrolled_metrics,
        smart_metrics,
    )
    return (
        uncontrolled_scenario,
        uncontrolled_result,
        uncontrolled_metrics,
        smart_scenario,
        smart_result,
        smart_metrics,
        comparison_metrics,
    )


def _build_reference_low_concurrency_scenario() -> Scenario:
    return create_internal_scenario(
        vehicles=4,
        daily_energy_per_vehicle=10.0,
        charger_count=4,
        charger_power=22.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(16, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(12, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
        departure_mode=DepartureMode.WINDOW_END,
    )


def _build_reference_concentrated_arrival_scenario(
    *,
    arrival_profile_shape: ArrivalProfileShape,
) -> Scenario:
    return create_internal_scenario(
        vehicles=8,
        daily_energy_per_vehicle=12.0,
        charger_count=3,
        charger_power=22.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(18, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(10, 0),
        arrival_profile_shape=arrival_profile_shape,
        departure_mode=DepartureMode.WINDOW_END,
    )


def _build_reference_constrained_capacity_scenario() -> Scenario:
    return create_internal_scenario(
        vehicles=4,
        daily_energy_per_vehicle=30.0,
        charger_count=4,
        charger_power=60.0,
        grid_capacity=60.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
        departure_mode=DepartureMode.WINDOW_END,
    )


def _build_reference_flexible_smart_scenario() -> Scenario:
    return create_internal_scenario(
        vehicles=4,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=20.0,
        grid_capacity=80.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
        departure_mode=DepartureMode.WINDOW_END,
        departure_time_spread_minutes=120,
    )


def _build_reference_inflexible_smart_scenario() -> Scenario:
    return create_internal_scenario(
        vehicles=4,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=20.0,
        grid_capacity=80.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
        departure_mode=DepartureMode.WINDOW_END,
        departure_time_spread_minutes=0,
    )


def _build_reference_high_turnover_scenario() -> Scenario:
    return create_internal_scenario(
        vehicles=6,
        daily_energy_per_vehicle=8.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
        departure_mode=DepartureMode.SESSION_DWELL,
        session_dwell_minutes=45,
    )


def _build_reference_high_queue_scenario() -> Scenario:
    return create_internal_scenario(
        vehicles=8,
        daily_energy_per_vehicle=12.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 30),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
        departure_mode=DepartureMode.WINDOW_END,
    )


def _build_reference_public_fast_turnover_scenario() -> Scenario:
    return create_internal_scenario(
        vehicles=48,
        daily_energy_per_vehicle=50.0,
        charger_count=6,
        charger_power=300.0,
        grid_capacity=1200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(20, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(20, 0),
        arrival_mode=ArrivalMode.RANDOM,
        arrival_profile_shape=ArrivalProfileShape.MID_PEAK,
        departure_mode=DepartureMode.SESSION_DWELL,
        session_dwell_minutes=15,
        departure_time_spread_minutes=30,
        charger_service_max_waiting_time_minutes=15,
    )


def test_reference_low_concurrency_case_remains_queue_free_and_feasible():
    scenario = _build_reference_low_concurrency_scenario()
    result, metrics = _calculate_reference_metrics(scenario)

    evaluation = evaluate_charger_count_service_rule(
        scenario,
        result,
        metrics,
    )
    search = search_minimum_feasible_charger_count(
        scenario,
        result,
        metrics,
    )

    assert metrics.queue_present_indicator is False
    assert metrics.maximum_queue_length == 0
    assert metrics.average_waiting_time_hours == 0.0
    assert metrics.vehicles_not_started_count == 0
    assert metrics.vehicles_with_unmet_energy_count == 0
    assert metrics.peak_occupied_charger_count < scenario.charger_count
    assert metrics.primary_constraint_reason == "none"
    assert evaluation.service_rule_met is True
    assert search.service_rule_already_met is True
    assert search.first_feasible_candidate_charger_count == scenario.charger_count


def test_reference_concentrated_arrival_case_creates_more_concurrency_than_even_arrivals():
    even_scenario = _build_reference_concentrated_arrival_scenario(
        arrival_profile_shape=ArrivalProfileShape.EVEN,
    )
    concentrated_scenario = _build_reference_concentrated_arrival_scenario(
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    _, even_metrics = _calculate_reference_metrics(even_scenario)
    _, concentrated_metrics = _calculate_reference_metrics(concentrated_scenario)

    assert even_metrics.queue_present_indicator is False
    assert even_metrics.maximum_queue_length == 0
    assert even_metrics.primary_constraint_reason == "none"
    assert concentrated_metrics.queue_present_indicator is True
    assert concentrated_metrics.maximum_queue_length > even_metrics.maximum_queue_length
    assert concentrated_metrics.average_waiting_time_hours > even_metrics.average_waiting_time_hours
    assert concentrated_metrics.maximum_waiting_time_hours > even_metrics.maximum_waiting_time_hours
    assert concentrated_metrics.peak_load > even_metrics.peak_load
    assert concentrated_metrics.primary_constraint_reason == "charger_availability"


def test_reference_constrained_capacity_case_is_not_resolvable_by_adding_chargers():
    scenario = _build_reference_constrained_capacity_scenario()
    result, metrics = _calculate_reference_metrics(scenario)

    evaluation = evaluate_charger_count_service_rule(
        scenario,
        result,
        metrics,
    )
    search = search_minimum_feasible_charger_count(
        scenario,
        result,
        metrics,
    )

    assert metrics.primary_constraint_reason == "grid_connection_capacity"
    assert metrics.queue_present_indicator is False
    assert metrics.vehicles_not_started_count == 0
    assert metrics.vehicles_with_unmet_energy_count == scenario.vehicles
    assert metrics.required_charger_count is None
    assert metrics.additional_chargers_required is None
    assert evaluation.service_rule_met is False
    assert evaluation.failed_conditions == ("vehicles_with_unmet_energy_count",)
    assert evaluation.potentially_resolvable_by_adding_chargers is False
    assert search.charger_count_resolvable is False
    assert search.no_solution_reason == "not_charger_count_resolvable"
    assert search.evaluated_candidate_charger_counts == (scenario.charger_count,)


def test_reference_flexible_smart_case_reduces_peak_without_service_tradeoff():
    (
        _uncontrolled_scenario,
        _uncontrolled_result,
        uncontrolled_metrics,
        _smart_scenario,
        _smart_result,
        smart_metrics,
        comparison_metrics,
    ) = _calculate_reference_strategy_comparison(
        _build_reference_flexible_smart_scenario()
    )

    assert uncontrolled_metrics.queue_present_indicator is False
    assert smart_metrics.queue_present_indicator is False
    assert uncontrolled_metrics.vehicles_with_unmet_energy_count == 0
    assert smart_metrics.vehicles_with_unmet_energy_count == 0
    assert smart_metrics.peak_load < uncontrolled_metrics.peak_load
    assert smart_metrics.required_connection_capacity_kw < (
        uncontrolled_metrics.required_connection_capacity_kw
    )
    assert comparison_metrics.peak_reduction > 0.0
    assert comparison_metrics.service_impact_summary == "No modeled service pressure."
    assert comparison_metrics.infrastructure_recommendation_changed_by_smart is False


def test_reference_inflexible_smart_case_keeps_peak_unchanged_when_flexibility_is_absent():
    (
        _uncontrolled_scenario,
        _uncontrolled_result,
        uncontrolled_metrics,
        _smart_scenario,
        _smart_result,
        smart_metrics,
        comparison_metrics,
    ) = _calculate_reference_strategy_comparison(
        _build_reference_inflexible_smart_scenario()
    )

    assert uncontrolled_metrics.queue_present_indicator is False
    assert smart_metrics.queue_present_indicator is False
    assert uncontrolled_metrics.vehicles_with_unmet_energy_count == 0
    assert smart_metrics.vehicles_with_unmet_energy_count == 0
    assert smart_metrics.peak_load == pytest.approx(uncontrolled_metrics.peak_load)
    assert comparison_metrics.peak_reduction == pytest.approx(0.0)
    assert comparison_metrics.service_impact_summary == "No modeled service pressure."
    assert comparison_metrics.infrastructure_recommendation_changed_by_smart is False
    assert (
        comparison_metrics.infrastructure_impact_summary
        == "Both strategies satisfy the modeled service rule and lead to the same infrastructure recommendation."
    )


def test_reference_high_turnover_case_no_longer_trades_service_for_peak_reduction():
    (
        uncontrolled_scenario,
        uncontrolled_result,
        uncontrolled_metrics,
        smart_scenario,
        smart_result,
        smart_metrics,
        comparison_metrics,
    ) = _calculate_reference_strategy_comparison(
        _build_reference_high_turnover_scenario()
    )

    uncontrolled_evaluation = evaluate_charger_count_service_rule(
        uncontrolled_scenario,
        uncontrolled_result,
        uncontrolled_metrics,
    )
    smart_evaluation = evaluate_charger_count_service_rule(
        smart_scenario,
        smart_result,
        smart_metrics,
    )

    assert uncontrolled_metrics.queue_present_indicator is True
    assert uncontrolled_metrics.maximum_waiting_time_hours == pytest.approx(0.5)
    assert uncontrolled_evaluation.service_rule_met is True
    assert smart_metrics.vehicles_not_started_count == (
        uncontrolled_metrics.vehicles_not_started_count
    )
    assert smart_metrics.vehicles_with_unmet_energy_count == (
        uncontrolled_metrics.vehicles_with_unmet_energy_count
    )
    assert smart_metrics.unmet_energy == pytest.approx(uncontrolled_metrics.unmet_energy)
    assert smart_evaluation.service_rule_met is True
    assert smart_evaluation.failed_conditions == ()
    assert comparison_metrics.peak_reduction == pytest.approx(0.0)
    assert comparison_metrics.service_rule_worsened_by_smart is False
    assert comparison_metrics.service_impact_summary == "Service pressure unchanged."
    assert comparison_metrics.infrastructure_impact_summary == (
        "Both strategies satisfy the modeled service rule and lead to the same infrastructure recommendation."
    )


def test_reference_high_queue_case_requires_more_chargers_to_limit_waiting():
    scenario = _build_reference_high_queue_scenario()
    result, metrics = _calculate_reference_metrics(scenario)

    evaluation = evaluate_charger_count_service_rule(
        scenario,
        result,
        metrics,
    )
    search = search_minimum_feasible_charger_count(
        scenario,
        result,
        metrics,
    )

    (
        _uncontrolled_scenario,
        _uncontrolled_result,
        uncontrolled_metrics,
        _smart_scenario,
        _smart_result,
        smart_metrics,
        comparison_metrics,
    ) = _calculate_reference_strategy_comparison(scenario)

    assert metrics.queue_present_indicator is True
    assert metrics.maximum_queue_length >= 6
    assert metrics.maximum_waiting_time_hours is not None
    assert metrics.maximum_waiting_time_hours > 0.5
    assert metrics.vehicles_not_started_count == 0
    assert metrics.vehicles_with_unmet_energy_count == 0
    assert evaluation.service_rule_met is False
    assert evaluation.failed_conditions == ("maximum_waiting_time_hours",)
    assert evaluation.potentially_resolvable_by_adding_chargers is True
    assert search.feasible_candidate_found is True
    assert search.first_feasible_candidate_charger_count == 3
    assert search.evaluated_candidate_charger_counts[0] == scenario.charger_count
    assert 3 in search.evaluated_candidate_charger_counts
    assert smart_metrics.peak_load == pytest.approx(uncontrolled_metrics.peak_load)
    assert smart_metrics.maximum_queue_length == uncontrolled_metrics.maximum_queue_length
    assert comparison_metrics.peak_reduction == pytest.approx(0.0)
    assert comparison_metrics.service_impact_summary == "Service pressure unchanged."


def test_reference_public_fast_case_exhibits_higher_turnover_under_shared_model():
    scenario = _build_reference_public_fast_turnover_scenario()
    result, metrics = _calculate_reference_metrics(scenario)

    evaluation = evaluate_charger_count_service_rule(
        scenario,
        result,
        metrics,
    )

    assert metrics.queue_present_indicator is True
    assert metrics.maximum_queue_length >= 1
    assert metrics.maximum_waiting_time_hours == pytest.approx(0.25)
    assert metrics.vehicles_not_started_count == 0
    assert metrics.vehicles_with_unmet_energy_count == 0
    assert metrics.peak_occupied_charger_count == scenario.charger_count
    assert metrics.primary_constraint_reason == "charger_availability"
    assert evaluation.service_rule_met is True


def test_reference_heavy_duty_preset_smart_charging_now_shows_a_waiting_tradeoff_without_extra_service_failure():
    base_scenario = get_scenario_preset(DEFAULT_SCENARIO_PRESET_ID).scenario
    (
        _uncontrolled_scenario,
        _uncontrolled_result,
        uncontrolled_metrics,
        _smart_scenario,
        _smart_result,
        smart_metrics,
        comparison_metrics,
    ) = _calculate_reference_strategy_comparison(base_scenario)

    assert smart_metrics.vehicles_not_started_count == uncontrolled_metrics.vehicles_not_started_count
    assert smart_metrics.vehicles_with_unmet_energy_count == (
        uncontrolled_metrics.vehicles_with_unmet_energy_count
    )
    assert smart_metrics.average_waiting_time_hours < (
        uncontrolled_metrics.average_waiting_time_hours
    )
    assert smart_metrics.maximum_waiting_time_hours <= (
        uncontrolled_metrics.maximum_waiting_time_hours
        + get_timestep_hours()
        + 1e-9
    )
    assert smart_metrics.peak_load <= uncontrolled_metrics.peak_load + 1e-9
    assert comparison_metrics.service_impact_summary == "Service trade-off changed."


def test_reference_workplace_preset_smart_charging_now_shows_a_waiting_tradeoff_without_extra_service_failure():
    base_scenario = get_scenario_preset(WORKPLACE_CHARGING_PRESET_ID).scenario
    (
        _uncontrolled_scenario,
        _uncontrolled_result,
        uncontrolled_metrics,
        _smart_scenario,
        _smart_result,
        smart_metrics,
        comparison_metrics,
    ) = _calculate_reference_strategy_comparison(base_scenario)

    assert smart_metrics.vehicles_not_started_count == uncontrolled_metrics.vehicles_not_started_count
    assert smart_metrics.vehicles_with_unmet_energy_count == (
        uncontrolled_metrics.vehicles_with_unmet_energy_count
    )
    assert smart_metrics.average_waiting_time_hours < (
        uncontrolled_metrics.average_waiting_time_hours
    )
    assert smart_metrics.maximum_waiting_time_hours <= (
        uncontrolled_metrics.maximum_waiting_time_hours
        + get_timestep_hours()
        + 1e-9
    )
    assert smart_metrics.peak_load <= uncontrolled_metrics.peak_load + 1e-9
    assert comparison_metrics.service_impact_summary == "Service trade-off changed."


def test_reference_public_fast_preset_keeps_queue_outcomes_while_reducing_peak():
    base_scenario = get_scenario_preset(PUBLIC_FAST_CHARGING_PRESET_ID).scenario
    (
        _uncontrolled_scenario,
        _uncontrolled_result,
        uncontrolled_metrics,
        _smart_scenario,
        _smart_result,
        smart_metrics,
        comparison_metrics,
    ) = _calculate_reference_strategy_comparison(base_scenario)

    assert smart_metrics.maximum_queue_length == uncontrolled_metrics.maximum_queue_length
    assert smart_metrics.average_waiting_time_hours == pytest.approx(
        uncontrolled_metrics.average_waiting_time_hours
    )
    assert smart_metrics.maximum_waiting_time_hours == pytest.approx(
        uncontrolled_metrics.maximum_waiting_time_hours
    )
    assert smart_metrics.vehicles_not_started_count == uncontrolled_metrics.vehicles_not_started_count
    assert smart_metrics.vehicles_with_unmet_energy_count == (
        uncontrolled_metrics.vehicles_with_unmet_energy_count
    )
    assert smart_metrics.peak_load < uncontrolled_metrics.peak_load
    assert comparison_metrics.service_impact_summary == "Service pressure unchanged."
