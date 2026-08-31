from dataclasses import replace
from datetime import time

import pytest

import metrics.planning as planning_module
import simulation.engine as simulation_engine_module
from metrics import (
    Metrics,
    calculate_metrics,
    evaluate_charger_count_service_rule,
    search_minimum_feasible_charger_count,
)
from scenarios import (
    WORKPLACE_CHARGING_PRESET_ID,
    create_internal_scenario,
    default_scenario,
    get_scenario_preset,
)
from simulation import (
    SimulationResult,
    TIMESTEPS_PER_DAY,
    get_timestep_hours,
    simulate,
    simulate_planner_candidate,
)


def _strip_evaluation_trace(search_result):
    return replace(
        search_result,
        evaluated_candidate_charger_counts=(),
    )


def _linear_reference_search_result(
    scenario,
    simulation_result,
    metrics,
):
    base_evaluation = evaluate_charger_count_service_rule(
        scenario,
        simulation_result,
        metrics,
    )
    evaluated_candidate_charger_counts = (scenario.charger_count,)

    if scenario.vehicles == 0:
        return planning_module.ChargerCountSearchResult(
            service_rule_already_met=True,
            failed_conditions=base_evaluation.failed_conditions,
            charger_count_resolvable=False,
            feasible_candidate_found=True,
            first_feasible_candidate_charger_count=0,
            no_solution_reason=None,
            required_evidence_available=base_evaluation.required_evidence_available,
            evaluated_candidate_charger_counts=evaluated_candidate_charger_counts,
        )

    if (
        simulation_result.daily_energy_demand
        <= planning_module.FLOATING_POINT_TOLERANCE
        and base_evaluation.service_rule_met
    ):
        return planning_module.ChargerCountSearchResult(
            service_rule_already_met=True,
            failed_conditions=base_evaluation.failed_conditions,
            charger_count_resolvable=False,
            feasible_candidate_found=True,
            first_feasible_candidate_charger_count=0,
            no_solution_reason=None,
            required_evidence_available=base_evaluation.required_evidence_available,
            evaluated_candidate_charger_counts=evaluated_candidate_charger_counts,
        )

    if base_evaluation.service_rule_met:
        return planning_module.ChargerCountSearchResult(
            service_rule_already_met=True,
            failed_conditions=base_evaluation.failed_conditions,
            charger_count_resolvable=False,
            feasible_candidate_found=True,
            first_feasible_candidate_charger_count=scenario.charger_count,
            no_solution_reason=None,
            required_evidence_available=base_evaluation.required_evidence_available,
            evaluated_candidate_charger_counts=evaluated_candidate_charger_counts,
        )

    if not base_evaluation.required_evidence_available:
        return planning_module.ChargerCountSearchResult(
            service_rule_already_met=False,
            failed_conditions=base_evaluation.failed_conditions,
            charger_count_resolvable=False,
            feasible_candidate_found=False,
            first_feasible_candidate_charger_count=None,
            no_solution_reason=planning_module.NO_SOLUTION_INSUFFICIENT_EVIDENCE,
            required_evidence_available=False,
            evaluated_candidate_charger_counts=evaluated_candidate_charger_counts,
        )

    if not base_evaluation.potentially_resolvable_by_adding_chargers:
        return planning_module.ChargerCountSearchResult(
            service_rule_already_met=False,
            failed_conditions=base_evaluation.failed_conditions,
            charger_count_resolvable=False,
            feasible_candidate_found=False,
            first_feasible_candidate_charger_count=None,
            no_solution_reason=(
                planning_module.NO_SOLUTION_NOT_CHARGER_COUNT_RESOLVABLE
            ),
            required_evidence_available=True,
            evaluated_candidate_charger_counts=evaluated_candidate_charger_counts,
        )

    return planning_module._search_minimum_feasible_charger_count_linear(
        scenario,
        simulation_result,
        metrics,
        base_evaluation=base_evaluation,
    )


def test_feasible_scenario_satisfies_first_charger_planning_rule():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)

    evaluation = evaluate_charger_count_service_rule(
        scenario,
        simulation_result,
        metrics,
    )

    assert evaluation.service_rule_met is True
    assert evaluation.failed_conditions == ()
    assert evaluation.potentially_resolvable_by_adding_chargers is False
    assert evaluation.required_evidence_available is True


def test_brief_queue_alone_can_still_satisfy_charger_planning_rule():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)

    evaluation = evaluate_charger_count_service_rule(
        scenario,
        simulation_result,
        metrics,
    )

    assert metrics.queue_present_indicator is True
    assert metrics.vehicles_not_started_count == 0
    assert metrics.vehicles_with_unmet_energy_count == 0
    assert metrics.maximum_waiting_time_hours == pytest.approx(0.5)
    assert evaluation.service_rule_met is True
    assert evaluation.failed_conditions == ()
    assert evaluation.potentially_resolvable_by_adding_chargers is False


def test_waiting_above_turnover_tolerance_fails_charger_planning_rule():
    scenario = create_internal_scenario(
        vehicles=4,
        daily_energy_per_vehicle=10.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)

    evaluation = evaluate_charger_count_service_rule(
        scenario,
        simulation_result,
        metrics,
    )

    assert metrics.queue_present_indicator is True
    assert metrics.vehicles_not_started_count == 0
    assert metrics.vehicles_with_unmet_energy_count == 0
    assert metrics.maximum_waiting_time_hours is not None
    assert metrics.maximum_waiting_time_hours > 2 * get_timestep_hours()
    assert evaluation.service_rule_met is False
    assert evaluation.failed_conditions == ("maximum_waiting_time_hours",)
    assert evaluation.potentially_resolvable_by_adding_chargers is True


def test_scenario_specific_waiting_tolerance_changes_required_charger_count():
    base_scenario = create_internal_scenario(
        vehicles=8,
        daily_energy_per_vehicle=12.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 30),
    )

    heavy_duty_scenario = replace(
        base_scenario,
        charger_service_max_waiting_time_minutes=120,
    )
    workplace_scenario = replace(
        base_scenario,
        charger_service_max_waiting_time_minutes=60,
    )
    public_fast_scenario = replace(
        base_scenario,
        charger_service_max_waiting_time_minutes=15,
    )

    heavy_duty_metrics = calculate_metrics(
        simulate(heavy_duty_scenario),
        heavy_duty_scenario,
    )
    workplace_metrics = calculate_metrics(
        simulate(workplace_scenario),
        workplace_scenario,
    )
    public_fast_metrics = calculate_metrics(
        simulate(public_fast_scenario),
        public_fast_scenario,
    )

    assert heavy_duty_metrics.maximum_waiting_time_hours == pytest.approx(1.75)
    assert workplace_metrics.maximum_waiting_time_hours == pytest.approx(1.75)
    assert public_fast_metrics.maximum_waiting_time_hours == pytest.approx(1.75)

    assert heavy_duty_metrics.required_charger_count == 1
    assert workplace_metrics.required_charger_count == 2
    assert public_fast_metrics.required_charger_count == 4


@pytest.mark.parametrize(
    ("scenario"),
    [
        create_internal_scenario(
            vehicles=2,
            daily_energy_per_vehicle=20.0,
            charger_count=0,
            charger_power=50.0,
            grid_capacity=100.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(9, 0),
        ),
        create_internal_scenario(
            vehicles=4,
            daily_energy_per_vehicle=10.0,
            charger_count=1,
            charger_power=50.0,
            grid_capacity=200.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(9, 0),
        ),
        create_internal_scenario(
            vehicles=8,
            daily_energy_per_vehicle=12.0,
            charger_count=1,
            charger_power=50.0,
            grid_capacity=400.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(10, 0),
            arrival_window_start=time(8, 0),
            arrival_window_end=time(8, 30),
            charger_service_max_waiting_time_minutes=15,
        ),
    ],
    ids=[
        "zero-to-one-availability",
        "queue-pressure-threshold-without-grid-limit",
        "public-fast-threshold-without-grid-limit",
    ],
)
def test_charger_count_feasibility_is_monotonic_when_grid_capacity_cannot_become_the_bottleneck(
    scenario,
):
    base_result = simulate(scenario)
    base_metrics = calculate_metrics(base_result, scenario)
    base_evaluation = evaluate_charger_count_service_rule(
        scenario,
        base_result,
        base_metrics,
    )

    assert base_evaluation.service_rule_met is False
    assert base_evaluation.potentially_resolvable_by_adding_chargers is True

    seen_feasible = False
    for candidate_charger_count in range(
        scenario.charger_count,
        scenario.vehicles + 1,
    ):
        candidate_scenario = planning_module.copy_scenario_with_updates(
            scenario,
            charger_count=candidate_charger_count,
        )
        candidate_result = simulate(candidate_scenario)
        candidate_metrics = calculate_metrics(
            candidate_result,
            candidate_scenario,
        )
        candidate_evaluation = evaluate_charger_count_service_rule(
            candidate_scenario,
            candidate_result,
            candidate_metrics,
        )
        if candidate_evaluation.service_rule_met:
            seen_feasible = True
            continue
        assert seen_feasible is False


def test_charger_count_feasibility_is_not_globally_monotonic_when_extra_chargers_can_hit_grid_capacity():
    scenario = create_internal_scenario(
        vehicles=8,
        daily_energy_per_vehicle=12.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 30),
        charger_service_max_waiting_time_minutes=15,
    )

    feasibility_by_charger_count = []
    for candidate_charger_count in range(
        scenario.charger_count,
        scenario.vehicles + 1,
    ):
        candidate_scenario = planning_module.copy_scenario_with_updates(
            scenario,
            charger_count=candidate_charger_count,
        )
        candidate_result = simulate(candidate_scenario)
        candidate_metrics = calculate_metrics(
            candidate_result,
            candidate_scenario,
        )
        candidate_evaluation = evaluate_charger_count_service_rule(
            candidate_scenario,
            candidate_result,
            candidate_metrics,
        )
        feasibility_by_charger_count.append(candidate_evaluation.service_rule_met)

    assert feasibility_by_charger_count == [
        False,
        False,
        False,
        True,
        False,
        False,
        False,
        True,
    ]


def test_charger_count_feasibility_is_piecewise_monotonic_on_each_side_of_grid_saturation_boundary():
    scenario = create_internal_scenario(
        vehicles=8,
        daily_energy_per_vehicle=12.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 30),
        charger_service_max_waiting_time_minutes=15,
    )

    lower_region_feasibility = []
    for candidate_charger_count in range(1, 5):
        candidate_scenario = planning_module.copy_scenario_with_updates(
            scenario,
            charger_count=candidate_charger_count,
        )
        candidate_result = simulate(candidate_scenario)
        candidate_metrics = calculate_metrics(
            candidate_result,
            candidate_scenario,
        )
        lower_region_feasibility.append(
            evaluate_charger_count_service_rule(
                candidate_scenario,
                candidate_result,
                candidate_metrics,
            ).service_rule_met
        )

    upper_region_feasibility = []
    for candidate_charger_count in range(5, 9):
        candidate_scenario = planning_module.copy_scenario_with_updates(
            scenario,
            charger_count=candidate_charger_count,
        )
        candidate_result = simulate(candidate_scenario)
        candidate_metrics = calculate_metrics(
            candidate_result,
            candidate_scenario,
        )
        upper_region_feasibility.append(
            evaluate_charger_count_service_rule(
                candidate_scenario,
                candidate_result,
                candidate_metrics,
            ).service_rule_met
        )

    assert lower_region_feasibility == [False, False, False, True]
    assert upper_region_feasibility == [False, False, False, True]


def test_resolve_safe_monotonic_charger_count_ranges_splits_around_grid_saturation_boundary():
    scenario = create_internal_scenario(
        vehicles=8,
        daily_energy_per_vehicle=12.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=200.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(10, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 30),
        charger_service_max_waiting_time_minutes=15,
    )

    assert planning_module._resolve_safe_monotonic_charger_count_ranges(
        scenario
    ) == ((1, 4), (4, 8))


def test_unstarted_vehicles_alone_fail_first_charger_planning_rule():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = simulate(scenario)
    metrics = Metrics(
        total_daily_energy=simulation_result.daily_energy_demand,
        available_capacity=simulation_result.available_site_charging_capacity_kw,
        energy_delivery_sufficient=False,
        vehicles_not_started_count=1,
        primary_constraint_reason="charging_window",
    )

    evaluation = evaluate_charger_count_service_rule(
        scenario,
        simulation_result,
        metrics,
    )

    assert evaluation.service_rule_met is False
    assert evaluation.failed_conditions == ("vehicles_not_started_count",)
    assert evaluation.potentially_resolvable_by_adding_chargers is False


def test_unmet_energy_alone_fails_first_charger_planning_rule():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = simulate(scenario)
    metrics = Metrics(
        total_daily_energy=simulation_result.daily_energy_demand,
        available_capacity=simulation_result.available_site_charging_capacity_kw,
        energy_delivery_sufficient=False,
        vehicles_with_unmet_energy_count=1,
        primary_constraint_reason="charger_power",
    )

    evaluation = evaluate_charger_count_service_rule(
        scenario,
        simulation_result,
        metrics,
    )

    assert evaluation.service_rule_met is False
    assert evaluation.failed_conditions == (
        "vehicles_with_unmet_energy_count",
    )
    assert evaluation.potentially_resolvable_by_adding_chargers is False


@pytest.mark.parametrize(
    ("scenario"),
    [
        pytest.param(default_scenario, id="heavy-duty"),
        pytest.param(
            get_scenario_preset(WORKPLACE_CHARGING_PRESET_ID).scenario,
            id="workplace",
        ),
        pytest.param(
            create_internal_scenario(
                vehicles=2,
                daily_energy_per_vehicle=20.0,
                charger_count=0,
                charger_power=50.0,
                grid_capacity=100.0,
                charging_window_start=time(8, 0),
                charging_window_end=time(9, 0),
            ),
            id="zero-chargers",
        ),
        pytest.param(
            create_internal_scenario(
                vehicles=0,
                daily_energy_per_vehicle=20.0,
                charger_count=0,
                charger_power=50.0,
                grid_capacity=100.0,
                charging_window_start=time(8, 0),
                charging_window_end=time(9, 0),
            ),
            id="zero-vehicles",
        ),
    ],
)
def test_planner_candidate_metrics_match_full_metrics_for_service_rule_fields(
    scenario,
):
    assert scenario is not None

    full_result = simulate(scenario)
    full_metrics = calculate_metrics(
        full_result,
        scenario,
        include_primary_constraint_reason=False,
        include_charger_count_recommendation=False,
    )
    planner_candidate_result = simulate_planner_candidate(scenario)
    planner_candidate_metrics = (
        planning_module._build_planner_candidate_service_rule_metrics(
            planner_candidate_result,
            scenario,
        )
    )

    assert planner_candidate_metrics.queue_present_indicator == (
        full_metrics.queue_present_indicator
    )
    assert planner_candidate_metrics.average_waiting_time_hours == pytest.approx(
        full_metrics.average_waiting_time_hours
    )
    assert planner_candidate_metrics.maximum_waiting_time_hours == pytest.approx(
        full_metrics.maximum_waiting_time_hours
    )
    assert planner_candidate_metrics.charger_service_waiting_tolerance_hours == (
        full_metrics.charger_service_waiting_tolerance_hours
    )
    assert planner_candidate_metrics.vehicles_waiting_count == (
        full_metrics.vehicles_waiting_count
    )
    assert planner_candidate_metrics.vehicles_not_started_count == (
        full_metrics.vehicles_not_started_count
    )
    assert planner_candidate_metrics.vehicles_with_unmet_energy_count == (
        full_metrics.vehicles_with_unmet_energy_count
    )
    assert planner_candidate_metrics.waiting_vehicle_count_by_timestep == (
        full_metrics.waiting_vehicle_count_by_timestep
    )


@pytest.mark.parametrize(
    ("scenario", "candidate_charger_count"),
    [
        pytest.param(default_scenario, 30, id="heavy-duty-mid"),
        pytest.param(default_scenario, 50, id="heavy-duty-feasible"),
        pytest.param(
            get_scenario_preset(WORKPLACE_CHARGING_PRESET_ID).scenario,
            100,
            id="workplace-mid",
        ),
        pytest.param(
            get_scenario_preset(WORKPLACE_CHARGING_PRESET_ID).scenario,
            120,
            id="workplace-feasible",
        ),
        pytest.param(
            create_internal_scenario(
                vehicles=8,
                daily_energy_per_vehicle=12.0,
                charger_count=1,
                charger_power=50.0,
                grid_capacity=200.0,
                charging_window_start=time(8, 0),
                charging_window_end=time(10, 0),
                arrival_window_start=time(8, 0),
                arrival_window_end=time(8, 30),
                charger_service_max_waiting_time_minutes=15,
            ),
            4,
            id="non-monotonic-lower-feasible",
        ),
        pytest.param(
            create_internal_scenario(
                vehicles=8,
                daily_energy_per_vehicle=12.0,
                charger_count=1,
                charger_power=50.0,
                grid_capacity=200.0,
                charging_window_start=time(8, 0),
                charging_window_end=time(10, 0),
                arrival_window_start=time(8, 0),
                arrival_window_end=time(8, 30),
                charger_service_max_waiting_time_minutes=15,
            ),
            5,
            id="non-monotonic-upper-infeasible",
        ),
    ],
)
def test_lightweight_candidate_evaluation_matches_full_candidate_evaluation(
    scenario,
    candidate_charger_count,
):
    assert scenario is not None

    candidate_scenario = planning_module.copy_scenario_with_updates(
        scenario,
        charger_count=candidate_charger_count,
    )
    full_candidate_result = simulate(candidate_scenario)
    full_candidate_metrics = calculate_metrics(
        full_candidate_result,
        candidate_scenario,
        include_primary_constraint_reason=False,
        include_charger_count_recommendation=False,
    )
    full_candidate_evaluation = evaluate_charger_count_service_rule(
        candidate_scenario,
        full_candidate_result,
        full_candidate_metrics,
    )

    lightweight_candidate_result = simulate_planner_candidate(candidate_scenario)
    lightweight_candidate_metrics = (
        planning_module._build_planner_candidate_service_rule_metrics(
            lightweight_candidate_result,
            candidate_scenario,
        )
    )
    lightweight_candidate_evaluation = evaluate_charger_count_service_rule(
        candidate_scenario,
        lightweight_candidate_result,
        lightweight_candidate_metrics,
    )

    assert lightweight_candidate_evaluation.service_rule_met == (
        full_candidate_evaluation.service_rule_met
    )
    assert lightweight_candidate_evaluation.failed_conditions == (
        full_candidate_evaluation.failed_conditions
    )
    assert lightweight_candidate_evaluation.required_evidence_available == (
        full_candidate_evaluation.required_evidence_available
    )


def test_zero_vehicle_scenario_satisfies_first_charger_planning_rule():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)

    evaluation = evaluate_charger_count_service_rule(
        scenario,
        simulation_result,
        metrics,
    )

    assert evaluation.service_rule_met is True
    assert evaluation.failed_conditions == ()
    assert evaluation.potentially_resolvable_by_adding_chargers is False


def test_zero_chargers_with_positive_demand_fail_first_charger_planning_rule():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)

    evaluation = evaluate_charger_count_service_rule(
        scenario,
        simulation_result,
        metrics,
    )

    assert evaluation.service_rule_met is False
    assert evaluation.potentially_resolvable_by_adding_chargers is True


def test_charger_availability_cases_are_marked_potentially_resolvable_by_adding_chargers():
    scenario = create_internal_scenario(
        vehicles=4,
        daily_energy_per_vehicle=10.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)

    evaluation = evaluate_charger_count_service_rule(
        scenario,
        simulation_result,
        metrics,
    )

    assert metrics.primary_constraint_reason == "charger_availability"
    assert evaluation.failed_conditions == ("maximum_waiting_time_hours",)
    assert evaluation.potentially_resolvable_by_adding_chargers is True


def test_non_availability_constraints_are_not_marked_charger_count_resolvable():
    scenarios = [
        create_internal_scenario(
            vehicles=1,
            daily_energy_per_vehicle=20.0,
            charger_count=1,
            charger_power=10.0,
            grid_capacity=100.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(9, 0),
        ),
        create_internal_scenario(
            vehicles=2,
            daily_energy_per_vehicle=20.0,
            charger_count=2,
            charger_power=50.0,
            grid_capacity=20.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(9, 0),
        ),
        create_internal_scenario(
            vehicles=1,
            daily_energy_per_vehicle=20.0,
            charger_count=1,
            charger_power=50.0,
            grid_capacity=100.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(8, 15),
            arrival_window_start=time(8, 15),
            arrival_window_end=time(8, 15),
        ),
        create_internal_scenario(
            vehicles=2,
            daily_energy_per_vehicle=20.0,
            charger_count=1,
            charger_power=10.0,
            grid_capacity=100.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(9, 0),
        ),
    ]

    for scenario in scenarios:
        simulation_result = simulate(scenario)
        metrics = calculate_metrics(simulation_result, scenario)

        evaluation = evaluate_charger_count_service_rule(
            scenario,
            simulation_result,
            metrics,
        )

        assert evaluation.service_rule_met is False
        assert evaluation.potentially_resolvable_by_adding_chargers is False


def test_incomplete_legacy_queueing_outputs_remain_safe_and_do_not_report_false_success():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
    )
    simulation_result = SimulationResult(
        daily_energy_demand=40.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=50.0,
        available_site_charging_capacity_kw=50.0,
        requested_load_profile_kw=[50.0, 50.0],
        delivered_load_profile_kw=[50.0, 50.0],
        charging_requests=[],
        waiting_vehicle_count_by_timestep=[],
    )
    metrics = calculate_metrics(simulation_result, scenario)

    evaluation = evaluate_charger_count_service_rule(
        scenario,
        simulation_result,
        metrics,
    )

    assert evaluation.service_rule_met is False
    assert evaluation.failed_conditions == ()
    assert evaluation.potentially_resolvable_by_adding_chargers is False
    assert evaluation.required_evidence_available is False


def test_zero_demand_without_unresolved_outcomes_satisfies_first_charger_planning_rule():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
    )
    simulation_result = SimulationResult(
        daily_energy_demand=0.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=50.0,
        available_site_charging_capacity_kw=50.0,
        requested_load_profile_kw=[0.0] * TIMESTEPS_PER_DAY,
        delivered_load_profile_kw=[0.0] * TIMESTEPS_PER_DAY,
        charging_requests=[],
        waiting_vehicle_count_by_timestep=[],
    )
    metrics = calculate_metrics(simulation_result, scenario)

    evaluation = evaluate_charger_count_service_rule(
        scenario,
        simulation_result,
        metrics,
    )

    assert evaluation.service_rule_met is True
    assert evaluation.required_evidence_available is True


def test_charger_count_search_finds_first_feasible_candidate_for_availability_constraint():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)

    result = search_minimum_feasible_charger_count(
        scenario,
        simulation_result,
        metrics,
    )

    assert result.service_rule_already_met is False
    assert result.charger_count_resolvable is True
    assert result.feasible_candidate_found is True
    assert result.first_feasible_candidate_charger_count == 1
    assert result.no_solution_reason is None
    assert result.evaluated_candidate_charger_counts == (0, 1)


def test_charger_count_search_starts_at_configured_count_and_never_tests_lower_values():
    scenario = create_internal_scenario(
        vehicles=3,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)

    result = search_minimum_feasible_charger_count(
        scenario,
        simulation_result,
        metrics,
    )

    assert result.evaluated_candidate_charger_counts[0] == scenario.charger_count
    assert all(
        candidate_count >= scenario.charger_count
        for candidate_count in result.evaluated_candidate_charger_counts
    )


def test_charger_count_search_stops_at_first_feasible_integer_candidate():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)

    result = search_minimum_feasible_charger_count(
        scenario,
        simulation_result,
        metrics,
    )

    assert result.first_feasible_candidate_charger_count == 1
    assert result.evaluated_candidate_charger_counts == (0, 1)


@pytest.mark.parametrize(
    ("scenario"),
    [
        create_internal_scenario(
            vehicles=2,
            daily_energy_per_vehicle=20.0,
            charger_count=2,
            charger_power=50.0,
            grid_capacity=100.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(9, 0),
        ),
        create_internal_scenario(
            vehicles=0,
            daily_energy_per_vehicle=20.0,
            charger_count=0,
            charger_power=50.0,
            grid_capacity=100.0,
        ),
        create_internal_scenario(
            vehicles=2,
            daily_energy_per_vehicle=20.0,
            charger_count=0,
            charger_power=50.0,
            grid_capacity=100.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(9, 0),
        ),
        create_internal_scenario(
            vehicles=8,
            daily_energy_per_vehicle=12.0,
            charger_count=1,
            charger_power=50.0,
            grid_capacity=200.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(10, 0),
            arrival_window_start=time(8, 0),
            arrival_window_end=time(8, 30),
            charger_service_max_waiting_time_minutes=15,
        ),
        create_internal_scenario(
            vehicles=1,
            daily_energy_per_vehicle=20.0,
            charger_count=1,
            charger_power=10.0,
            grid_capacity=100.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(9, 0),
        ),
        create_internal_scenario(
            vehicles=2,
            daily_energy_per_vehicle=20.0,
            charger_count=2,
            charger_power=50.0,
            grid_capacity=20.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(9, 0),
        ),
        create_internal_scenario(
            vehicles=1,
            daily_energy_per_vehicle=20.0,
            charger_count=1,
            charger_power=50.0,
            grid_capacity=100.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(8, 15),
            arrival_window_start=time(8, 15),
            arrival_window_end=time(8, 15),
        ),
    ],
    ids=[
        "already-feasible",
        "zero-vehicles",
        "availability-threshold-one",
        "public-fast-threshold-four",
        "charger-power-not-resolvable",
        "grid-capacity-not-resolvable",
        "window-not-resolvable",
    ],
)
def test_optimized_charger_count_search_matches_linear_reference_result(
    scenario,
):
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)

    optimized_result = search_minimum_feasible_charger_count(
        scenario,
        simulation_result,
        metrics,
    )
    linear_result = _linear_reference_search_result(
        scenario,
        simulation_result,
        metrics,
    )

    assert _strip_evaluation_trace(optimized_result) == _strip_evaluation_trace(
        linear_result
    )


def test_zero_demand_search_matches_linear_reference_result():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = SimulationResult(
        daily_energy_demand=0.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=50.0,
        available_site_charging_capacity_kw=50.0,
        requested_load_profile_kw=[0.0] * TIMESTEPS_PER_DAY,
        delivered_load_profile_kw=[0.0] * TIMESTEPS_PER_DAY,
        charging_requests=[],
        waiting_vehicle_count_by_timestep=[0] * TIMESTEPS_PER_DAY,
    )
    metrics = calculate_metrics(simulation_result, scenario)

    optimized_result = search_minimum_feasible_charger_count(
        scenario,
        simulation_result,
        metrics,
    )
    linear_result = _linear_reference_search_result(
        scenario,
        simulation_result,
        metrics,
    )

    assert _strip_evaluation_trace(optimized_result) == _strip_evaluation_trace(
        linear_result
    )


def test_optimized_charger_count_search_reduces_reruns_for_large_monotonic_span(
    monkeypatch,
):
    scenario = create_internal_scenario(
        vehicles=16,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=800.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(12, 0),
    )
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)
    original_evaluator = planning_module.evaluate_charger_count_service_rule
    threshold = 13

    def monotonic_evaluator(candidate_scenario, candidate_result, candidate_metrics):
        evaluation = original_evaluator(
            candidate_scenario,
            candidate_result,
            candidate_metrics,
        )
        if candidate_scenario.charger_count >= threshold:
            return replace(
                evaluation,
                service_rule_met=True,
                potentially_resolvable_by_adding_chargers=False,
            )

        return replace(
            evaluation,
            service_rule_met=False,
            failed_conditions=("maximum_waiting_time_hours",),
            potentially_resolvable_by_adding_chargers=True,
            required_evidence_available=True,
        )

    monkeypatch.setattr(
        planning_module,
        "evaluate_charger_count_service_rule",
        monotonic_evaluator,
    )

    optimized_result = search_minimum_feasible_charger_count(
        scenario,
        simulation_result,
        metrics,
    )
    linear_result = _linear_reference_search_result(
        scenario,
        simulation_result,
        metrics,
    )

    assert optimized_result.first_feasible_candidate_charger_count == threshold
    assert optimized_result.first_feasible_candidate_charger_count == (
        linear_result.first_feasible_candidate_charger_count
    )
    assert len(optimized_result.evaluated_candidate_charger_counts) < len(
        linear_result.evaluated_candidate_charger_counts
    )


@pytest.mark.parametrize(
    ("scenario"),
    [
        pytest.param(default_scenario, id="heavy-duty"),
        pytest.param(
            get_scenario_preset(WORKPLACE_CHARGING_PRESET_ID).scenario,
            id="workplace",
        ),
    ],
)
def test_optimized_charger_count_search_substantially_reduces_reference_preset_reruns(
    scenario,
):
    assert scenario is not None

    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)

    optimized_result = search_minimum_feasible_charger_count(
        scenario,
        simulation_result,
        metrics,
    )
    linear_result = _linear_reference_search_result(
        scenario,
        simulation_result,
        metrics,
    )

    assert optimized_result.first_feasible_candidate_charger_count == (
        linear_result.first_feasible_candidate_charger_count
    )
    assert len(optimized_result.evaluated_candidate_charger_counts) < (
        len(linear_result.evaluated_candidate_charger_counts) / 2
    )


@pytest.mark.parametrize(
    ("scenario"),
    [
        pytest.param(default_scenario, id="heavy-duty"),
        pytest.param(
            get_scenario_preset(WORKPLACE_CHARGING_PRESET_ID).scenario,
            id="workplace",
        ),
    ],
)
def test_required_charger_count_matches_linear_reference_for_reference_presets(
    scenario,
):
    assert scenario is not None

    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)
    linear_result = _linear_reference_search_result(
        scenario,
        simulation_result,
        metrics,
    )

    assert metrics.required_charger_count == (
        linear_result.first_feasible_candidate_charger_count
    )


def test_charger_count_search_returns_current_count_without_reruns_when_rule_is_already_met(
    monkeypatch,
):
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)
    rerun_calls: list[int] = []

    def _record_simulate_planner_candidate(candidate_scenario, **_kwargs):
        rerun_calls.append(candidate_scenario.charger_count)
        return simulate_planner_candidate(candidate_scenario)

    monkeypatch.setattr(
        planning_module,
        "simulate_planner_candidate",
        _record_simulate_planner_candidate,
    )

    result = search_minimum_feasible_charger_count(
        scenario,
        simulation_result,
        metrics,
    )

    assert result.service_rule_already_met is True
    assert result.first_feasible_candidate_charger_count == scenario.charger_count
    assert rerun_calls == []


def test_zero_vehicle_search_returns_zero_without_reruns(monkeypatch):
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=100.0,
    )
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)
    rerun_calls: list[int] = []

    def _record_simulate_planner_candidate(candidate_scenario, **_kwargs):
        rerun_calls.append(candidate_scenario.charger_count)
        return simulate_planner_candidate(candidate_scenario)

    monkeypatch.setattr(
        planning_module,
        "simulate_planner_candidate",
        _record_simulate_planner_candidate,
    )

    result = search_minimum_feasible_charger_count(
        scenario,
        simulation_result,
        metrics,
    )

    assert result.service_rule_already_met is True
    assert result.first_feasible_candidate_charger_count == 0
    assert rerun_calls == []


def test_non_availability_constraints_return_no_solution_without_misleading_searches(
    monkeypatch,
):
    scenarios = [
        create_internal_scenario(
            vehicles=1,
            daily_energy_per_vehicle=20.0,
            charger_count=1,
            charger_power=10.0,
            grid_capacity=100.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(9, 0),
        ),
        create_internal_scenario(
            vehicles=2,
            daily_energy_per_vehicle=20.0,
            charger_count=2,
            charger_power=50.0,
            grid_capacity=20.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(9, 0),
        ),
        create_internal_scenario(
            vehicles=1,
            daily_energy_per_vehicle=20.0,
            charger_count=1,
            charger_power=50.0,
            grid_capacity=100.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(8, 15),
            arrival_window_start=time(8, 15),
            arrival_window_end=time(8, 15),
        ),
        create_internal_scenario(
            vehicles=2,
            daily_energy_per_vehicle=20.0,
            charger_count=1,
            charger_power=10.0,
            grid_capacity=100.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(9, 0),
        ),
    ]
    rerun_calls: list[int] = []

    def _record_simulate_planner_candidate(candidate_scenario, **_kwargs):
        rerun_calls.append(candidate_scenario.charger_count)
        return simulate_planner_candidate(candidate_scenario)

    monkeypatch.setattr(
        planning_module,
        "simulate_planner_candidate",
        _record_simulate_planner_candidate,
    )

    for scenario in scenarios:
        simulation_result = simulate(scenario)
        metrics = calculate_metrics(simulation_result, scenario)
        result = search_minimum_feasible_charger_count(
            scenario,
            simulation_result,
            metrics,
        )

        assert result.charger_count_resolvable is False
        assert result.feasible_candidate_found is False
        assert result.no_solution_reason == "not_charger_count_resolvable"

    assert rerun_calls == []


def test_incomplete_service_rule_evidence_returns_no_solution_without_candidate_reruns(
    monkeypatch,
):
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
    )
    simulation_result = SimulationResult(
        daily_energy_demand=40.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=50.0,
        available_site_charging_capacity_kw=50.0,
        requested_load_profile_kw=[50.0, 50.0],
        delivered_load_profile_kw=[50.0, 50.0],
        charging_requests=[],
        waiting_vehicle_count_by_timestep=[],
    )
    metrics = calculate_metrics(simulation_result, scenario)
    rerun_calls: list[int] = []

    def _record_simulate_planner_candidate(candidate_scenario, **_kwargs):
        rerun_calls.append(candidate_scenario.charger_count)
        return simulate_planner_candidate(candidate_scenario)

    monkeypatch.setattr(
        planning_module,
        "simulate_planner_candidate",
        _record_simulate_planner_candidate,
    )

    result = search_minimum_feasible_charger_count(
        scenario,
        simulation_result,
        metrics,
    )

    assert result.charger_count_resolvable is False
    assert result.feasible_candidate_found is False
    assert result.no_solution_reason == "insufficient_service_rule_evidence"
    assert result.required_evidence_available is False
    assert rerun_calls == []


def test_unresolved_availability_search_returns_deterministic_no_solution_within_bound(
    monkeypatch,
):
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)

    original_evaluator = planning_module.evaluate_charger_count_service_rule

    def _never_feasible(candidate_scenario, candidate_result, candidate_metrics):
        evaluation = original_evaluator(
            candidate_scenario,
            candidate_result,
            candidate_metrics,
        )
        if candidate_scenario.charger_count == scenario.charger_count:
            return evaluation
        return replace(
            evaluation,
            service_rule_met=False,
            potentially_resolvable_by_adding_chargers=False,
        )

    monkeypatch.setattr(
        planning_module,
        "evaluate_charger_count_service_rule",
        _never_feasible,
    )

    result = search_minimum_feasible_charger_count(
        scenario,
        simulation_result,
        metrics,
    )

    assert result.charger_count_resolvable is True
    assert result.feasible_candidate_found is False
    assert (
        result.no_solution_reason
        == "no_feasible_candidate_within_vehicle_count_bound"
    )
    assert result.evaluated_candidate_charger_counts == (0, 1, 2)


def test_candidate_reruns_preserve_all_non_charger_count_inputs(monkeypatch):
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(8, 0),
    )
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)
    captured_scenarios = []
    original_simulate_planner_candidate = planning_module.simulate_planner_candidate

    def _record_simulate_planner_candidate(candidate_scenario, **kwargs):
        captured_scenarios.append(candidate_scenario)
        return original_simulate_planner_candidate(
            candidate_scenario,
            **kwargs,
        )

    monkeypatch.setattr(
        planning_module,
        "simulate_planner_candidate",
        _record_simulate_planner_candidate,
    )

    search_minimum_feasible_charger_count(
        scenario,
        simulation_result,
        metrics,
    )

    assert captured_scenarios
    for candidate_scenario in captured_scenarios:
        assert candidate_scenario.vehicles == scenario.vehicles
        assert (
            candidate_scenario.daily_energy_per_vehicle
            == scenario.daily_energy_per_vehicle
        )
        assert candidate_scenario.charger_power == scenario.charger_power
        assert candidate_scenario.grid_capacity == scenario.grid_capacity
        assert (
            candidate_scenario.charging_window_start
            == scenario.charging_window_start
        )
        assert candidate_scenario.charging_window_end == scenario.charging_window_end
        assert candidate_scenario.arrival_window_start == scenario.arrival_window_start
        assert candidate_scenario.arrival_window_end == scenario.arrival_window_end
        assert (
            candidate_scenario.arrival_profile_shape
            == scenario.arrival_profile_shape
        )
        assert (
            candidate_scenario.charging_strategy
            == scenario.charging_strategy
        )


@pytest.mark.parametrize(
    ("scenario"),
    [
        pytest.param(default_scenario, id="heavy-duty"),
        pytest.param(
            get_scenario_preset(WORKPLACE_CHARGING_PRESET_ID).scenario,
            id="workplace",
        ),
    ],
)
def test_charger_count_search_reuses_invariant_planner_generation_within_one_search(
    scenario,
    monkeypatch,
):
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)
    call_counts = {
        "daily_energy_demand": 0,
        "arrivals": 0,
        "requests": 0,
        "assignment": 0,
    }

    original_calculate_daily_energy_demand = (
        simulation_engine_module.calculate_daily_energy_demand
    )
    original_generate_arrivals_count_by_timestep = (
        simulation_engine_module.generate_arrivals_count_by_timestep
    )
    original_generate_charging_requests = (
        simulation_engine_module.generate_charging_requests
    )
    original_simulate_charging_requests = (
        simulation_engine_module.simulate_charging_requests
    )

    monkeypatch.setattr(
        simulation_engine_module,
        "calculate_daily_energy_demand",
        lambda candidate_scenario: (
            call_counts.__setitem__(
                "daily_energy_demand",
                call_counts["daily_energy_demand"] + 1,
            )
            or original_calculate_daily_energy_demand(candidate_scenario)
        ),
    )
    monkeypatch.setattr(
        simulation_engine_module,
        "generate_arrivals_count_by_timestep",
        lambda candidate_scenario: (
            call_counts.__setitem__(
                "arrivals",
                call_counts["arrivals"] + 1,
            )
            or original_generate_arrivals_count_by_timestep(candidate_scenario)
        ),
    )
    monkeypatch.setattr(
        simulation_engine_module,
        "generate_charging_requests",
        lambda candidate_scenario, arrivals_count_by_timestep=None: (
            call_counts.__setitem__(
                "requests",
                call_counts["requests"] + 1,
            )
            or original_generate_charging_requests(
                candidate_scenario,
                arrivals_count_by_timestep,
            )
        ),
    )
    monkeypatch.setattr(
        simulation_engine_module,
        "simulate_charging_requests",
        lambda *args, **kwargs: (
            call_counts.__setitem__(
                "assignment",
                call_counts["assignment"] + 1,
            )
            or original_simulate_charging_requests(*args, **kwargs)
        ),
    )

    result = search_minimum_feasible_charger_count(
        scenario,
        simulation_result,
        metrics,
    )

    assert len(result.evaluated_candidate_charger_counts) > 2
    assert call_counts["daily_energy_demand"] == 1
    assert call_counts["arrivals"] == 1
    assert call_counts["requests"] == 1
    assert call_counts["assignment"] == (
        len(result.evaluated_candidate_charger_counts) - 1
    )


def test_charger_count_search_does_not_mutate_original_scenario_result_or_metrics():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)
    original_scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    original_result = simulate(scenario)
    original_metrics = calculate_metrics(simulation_result, scenario)

    search_minimum_feasible_charger_count(
        scenario,
        simulation_result,
        metrics,
    )

    assert scenario == original_scenario
    assert simulation_result == original_result
    assert metrics == original_metrics


def test_repeated_charger_count_searches_are_deterministic():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    simulation_result = simulate(scenario)
    metrics = calculate_metrics(simulation_result, scenario)

    first_result = search_minimum_feasible_charger_count(
        scenario,
        simulation_result,
        metrics,
    )
    second_result = search_minimum_feasible_charger_count(
        scenario,
        simulation_result,
        metrics,
    )

    assert first_result == second_result
