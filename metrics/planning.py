"""Deterministic charger-planning service-rule helpers."""

import math
from dataclasses import dataclass

from metrics.constraint_analysis import CHARGER_AVAILABILITY_CONSTRAINT_REASON
from metrics.metrics import Metrics
from metrics.planning_rules import (
    DEFAULT_CHARGER_SERVICE_RULE_WAITING_TOLERANCE_HOURS,
    MAXIMUM_WAITING_TIME_CONDITION,
    VEHICLES_NOT_STARTED_CONDITION,
    VEHICLES_WITH_UNMET_ENERGY_CONDITION,
    collect_failed_conditions,
    maximum_waiting_time_exceeds_service_rule_tolerance,
)
from metrics.planning_summary import (
    NO_MODELED_SERVICE_PRESSURE_SUMMARY,
    NO_PLANNING_CHANGE_SUMMARY,
    NO_PLANNING_CHANGE_WHEN_FEASIBLE_SUMMARY,
    NO_PRIMARY_CONSTRAINT_SHIFT_SUMMARY,
    QUEUE_PRESSURE_REDUCED_SUMMARY,
    QUEUE_PRESSURE_WORSENED_SUMMARY,
    SERVICE_PRESSURE_REDUCED_SUMMARY,
    SERVICE_PRESSURE_UNCHANGED_SUMMARY,
    SERVICE_PRESSURE_WORSENED_SUMMARY,
    SERVICE_RULE_RESOLVED_SUMMARY,
    SERVICE_RULE_WORSENED_SUMMARY,
    SERVICE_SHORTFALL_REDUCED_SUMMARY,
    SERVICE_SHORTFALL_WORSENED_SUMMARY,
    SERVICE_TRADEOFF_CHANGED_SUMMARY,
    WAITING_REDUCED_SUMMARY,
    WAITING_WORSENED_SUMMARY,
    charger_expansion_avoided_by_smart,
    connection_upgrade_avoided_by_smart,
    connection_upgrade_required,
    infrastructure_impact_summary,
    infrastructure_recommendation_changed_by_smart,
    primary_constraint_shift_summary,
    primary_constraint_shifted_by_smart,
    service_impact_summary,
    service_rule_is_met,
    service_rule_resolved_by_smart,
    service_rule_worsened_by_smart,
)
from metrics.shared import (
    FLOATING_POINT_TOLERANCE,
    calculate_average_waiting_time_hours,
    calculate_maximum_waiting_time_hours,
)
from scenarios import Scenario, copy_scenario_with_updates
from simulation import (
    PlannerCandidateSimulationContext,
    PlannerCandidateSimulationResult,
    SimulationResult,
    TIMESTEPS_PER_DAY,
    build_planner_candidate_simulation_context,
    simulate_planner_candidate,
)


NO_SOLUTION_NOT_CHARGER_COUNT_RESOLVABLE = "not_charger_count_resolvable"
NO_SOLUTION_INSUFFICIENT_EVIDENCE = "insufficient_service_rule_evidence"
NO_SOLUTION_WITHIN_VEHICLE_COUNT_BOUND = (
    "no_feasible_candidate_within_vehicle_count_bound"
)
@dataclass(frozen=True)
class ChargerPlanningRuleEvaluation:
    """Planner-facing evaluation of the initial charger-count service rule."""

    service_rule_met: bool
    failed_conditions: tuple[str, ...]
    potentially_resolvable_by_adding_chargers: bool
    required_evidence_available: bool


@dataclass(frozen=True)
class ChargerCountSearchResult:
    """Internal-facing result for deterministic charger-count search."""

    service_rule_already_met: bool
    failed_conditions: tuple[str, ...]
    charger_count_resolvable: bool
    feasible_candidate_found: bool
    first_feasible_candidate_charger_count: int | None
    no_solution_reason: str | None
    required_evidence_available: bool
    evaluated_candidate_charger_counts: tuple[int, ...]



def evaluate_charger_count_service_rule(
    scenario: Scenario,
    simulation_result: SimulationResult,
    metrics: Metrics,
) -> ChargerPlanningRuleEvaluation:
    """Evaluate the first deterministic charger-planning service rule.

    The planner-facing success rule is met only when:

    * ``vehicles_not_started_count == 0``
    * ``vehicles_with_unmet_energy_count == 0``
    * ``maximum_waiting_time_hours`` stays within the scenario-specific waiting
      tolerance used for charger sizing

    The helper uses already-calculated metrics plus raw-result completeness
    checks so legacy or incomplete queueing outputs do not create false
    planning success.
    """
    required_evidence_available = _has_complete_service_rule_evidence(
        scenario,
        simulation_result,
    )
    failed_conditions = collect_failed_conditions(metrics)

    if not required_evidence_available:
        return ChargerPlanningRuleEvaluation(
            service_rule_met=False,
            failed_conditions=failed_conditions,
            potentially_resolvable_by_adding_chargers=False,
            required_evidence_available=False,
        )

    service_rule_met = len(failed_conditions) == 0
    return ChargerPlanningRuleEvaluation(
        service_rule_met=service_rule_met,
        failed_conditions=failed_conditions,
        potentially_resolvable_by_adding_chargers=(
            not service_rule_met
            and metrics.primary_constraint_reason
            == CHARGER_AVAILABILITY_CONSTRAINT_REASON
        ),
        required_evidence_available=True,
    )


def search_minimum_feasible_charger_count(
    scenario: Scenario,
    simulation_result: SimulationResult,
    metrics: Metrics,
) -> ChargerCountSearchResult:
    """Return the first charger count that satisfies the Phase 5 rule.

    The helper reuses the normal scenario -> simulation -> metrics flow for
    candidate reruns, but disables primary-constraint classification inside
    those reruns because search success depends only on the service rule.
    """
    base_evaluation = evaluate_charger_count_service_rule(
        scenario,
        simulation_result,
        metrics,
    )
    evaluated_candidate_charger_counts = (scenario.charger_count,)

    if scenario.vehicles == 0:
        return ChargerCountSearchResult(
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
        simulation_result.daily_energy_demand <= FLOATING_POINT_TOLERANCE
        and base_evaluation.service_rule_met
    ):
        return ChargerCountSearchResult(
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
        return ChargerCountSearchResult(
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
        return ChargerCountSearchResult(
            service_rule_already_met=False,
            failed_conditions=base_evaluation.failed_conditions,
            charger_count_resolvable=False,
            feasible_candidate_found=False,
            first_feasible_candidate_charger_count=None,
            no_solution_reason=NO_SOLUTION_INSUFFICIENT_EVIDENCE,
            required_evidence_available=False,
            evaluated_candidate_charger_counts=evaluated_candidate_charger_counts,
        )

    if not base_evaluation.potentially_resolvable_by_adding_chargers:
        return ChargerCountSearchResult(
            service_rule_already_met=False,
            failed_conditions=base_evaluation.failed_conditions,
            charger_count_resolvable=False,
            feasible_candidate_found=False,
            first_feasible_candidate_charger_count=None,
            no_solution_reason=NO_SOLUTION_NOT_CHARGER_COUNT_RESOLVABLE,
            required_evidence_available=True,
            evaluated_candidate_charger_counts=evaluated_candidate_charger_counts,
        )

    planner_candidate_simulation_context = (
        build_planner_candidate_simulation_context(scenario)
    )

    # For the current service rule, feasibility is monotonic with charger count
    # only inside charger-count ranges that do not cross the point where
    # installed charger capacity first hits the site connection limit.
    # Below that breakpoint, adding one charger adds one more full-power slot.
    # Above it, total site power stays fixed and extra chargers only relax
    # queueing/occupancy pressure. Crossing the breakpoint can be globally
    # non-monotonic, so the search treats the lower and upper ranges
    # separately and falls back to the legacy linear scan only when no safe
    # monotonic partition can be established.
    monotonic_ranges = _resolve_safe_monotonic_charger_count_ranges(
        scenario
    )
    if monotonic_ranges is None:
        return _search_minimum_feasible_charger_count_linear(
            scenario,
            simulation_result,
            metrics,
            base_evaluation=base_evaluation,
            planner_candidate_simulation_context=(
                planner_candidate_simulation_context
            ),
        )

    return _search_minimum_feasible_charger_count_monotonic(
        scenario,
        simulation_result,
        metrics,
        base_evaluation=base_evaluation,
        monotonic_ranges=monotonic_ranges,
        planner_candidate_simulation_context=(
            planner_candidate_simulation_context
        ),
    )


def _search_minimum_feasible_charger_count_linear(
    scenario: Scenario,
    simulation_result: SimulationResult,
    metrics: Metrics,
    *,
    base_evaluation: ChargerPlanningRuleEvaluation | None = None,
    planner_candidate_simulation_context: (
        PlannerCandidateSimulationContext | None
    ) = None,
) -> ChargerCountSearchResult:
    """Return the first feasible charger count using the legacy linear scan."""

    if base_evaluation is None:
        base_evaluation = evaluate_charger_count_service_rule(
            scenario,
            simulation_result,
            metrics,
        )

    evaluated_candidate_counts = [scenario.charger_count]
    for candidate_charger_count in range(
        scenario.charger_count + 1,
        scenario.vehicles + 1,
    ):
        evaluated_candidate_counts.append(candidate_charger_count)
        candidate_evaluation = _evaluate_candidate_charger_count_service_rule(
            scenario,
            candidate_charger_count,
            planner_candidate_simulation_context=(
                planner_candidate_simulation_context
            ),
        )
        if candidate_evaluation.service_rule_met:
            return ChargerCountSearchResult(
                service_rule_already_met=False,
                failed_conditions=base_evaluation.failed_conditions,
                charger_count_resolvable=True,
                feasible_candidate_found=True,
                first_feasible_candidate_charger_count=candidate_charger_count,
                no_solution_reason=None,
                required_evidence_available=True,
                evaluated_candidate_charger_counts=tuple(
                    evaluated_candidate_counts
                ),
            )

    return ChargerCountSearchResult(
        service_rule_already_met=False,
        failed_conditions=base_evaluation.failed_conditions,
        charger_count_resolvable=True,
        feasible_candidate_found=False,
        first_feasible_candidate_charger_count=None,
        no_solution_reason=NO_SOLUTION_WITHIN_VEHICLE_COUNT_BOUND,
        required_evidence_available=True,
        evaluated_candidate_charger_counts=tuple(evaluated_candidate_counts),
    )


def _search_minimum_feasible_charger_count_monotonic(
    scenario: Scenario,
    simulation_result: SimulationResult,
    metrics: Metrics,
    *,
    base_evaluation: ChargerPlanningRuleEvaluation | None = None,
    monotonic_ranges: tuple[tuple[int, int], ...] | None = None,
    planner_candidate_simulation_context: (
        PlannerCandidateSimulationContext | None
    ) = None,
) -> ChargerCountSearchResult:
    """Return the first feasible charger count using bounded monotonic ranges."""

    if base_evaluation is None:
        base_evaluation = evaluate_charger_count_service_rule(
            scenario,
            simulation_result,
            metrics,
        )

    evaluated_candidate_counts = [scenario.charger_count]
    resolved_ranges = (
        monotonic_ranges
        if monotonic_ranges is not None
        else _resolve_safe_monotonic_charger_count_ranges(scenario)
    )
    if resolved_ranges is None:
        return _search_minimum_feasible_charger_count_linear(
            scenario,
            simulation_result,
            metrics,
            base_evaluation=base_evaluation,
            planner_candidate_simulation_context=(
                planner_candidate_simulation_context
            ),
        )

    for lower_infeasible, highest_candidate_charger_count in resolved_ranges:
        feasible_candidate = _search_first_feasible_candidate_in_monotonic_range(
            scenario,
            lower_infeasible=lower_infeasible,
            highest_candidate_charger_count=highest_candidate_charger_count,
            evaluated_candidate_counts=evaluated_candidate_counts,
            planner_candidate_simulation_context=(
                planner_candidate_simulation_context
            ),
        )
        if feasible_candidate is None:
            continue

        return ChargerCountSearchResult(
            service_rule_already_met=False,
            failed_conditions=base_evaluation.failed_conditions,
            charger_count_resolvable=True,
            feasible_candidate_found=True,
            first_feasible_candidate_charger_count=feasible_candidate,
            no_solution_reason=None,
            required_evidence_available=True,
            evaluated_candidate_charger_counts=tuple(evaluated_candidate_counts),
        )

    return ChargerCountSearchResult(
        service_rule_already_met=False,
        failed_conditions=base_evaluation.failed_conditions,
        charger_count_resolvable=True,
        feasible_candidate_found=False,
        first_feasible_candidate_charger_count=None,
        no_solution_reason=NO_SOLUTION_WITHIN_VEHICLE_COUNT_BOUND,
        required_evidence_available=True,
        evaluated_candidate_charger_counts=tuple(evaluated_candidate_counts),
    )


def _search_first_feasible_candidate_in_monotonic_range(
    scenario: Scenario,
    *,
    lower_infeasible: int,
    highest_candidate_charger_count: int,
    evaluated_candidate_counts: list[int],
    planner_candidate_simulation_context: (
        PlannerCandidateSimulationContext | None
    ) = None,
) -> int | None:
    """Return the first feasible candidate in one safely monotonic range."""

    if highest_candidate_charger_count <= lower_infeasible:
        return None

    if highest_candidate_charger_count - lower_infeasible <= 2:
        for candidate_charger_count in range(
            lower_infeasible + 1,
            highest_candidate_charger_count + 1,
        ):
            evaluated_candidate_counts.append(candidate_charger_count)
            candidate_evaluation = _evaluate_candidate_charger_count_service_rule(
                scenario,
                candidate_charger_count,
                planner_candidate_simulation_context=(
                    planner_candidate_simulation_context
                ),
            )
            if candidate_evaluation.service_rule_met:
                return candidate_charger_count
        return None

    candidate_cache: dict[int, ChargerPlanningRuleEvaluation] = {}

    def evaluate_candidate(
        candidate_charger_count: int,
    ) -> ChargerPlanningRuleEvaluation:
        if candidate_charger_count in candidate_cache:
            return candidate_cache[candidate_charger_count]

        evaluated_candidate_counts.append(candidate_charger_count)
        candidate_evaluation = _evaluate_candidate_charger_count_service_rule(
            scenario,
            candidate_charger_count,
            planner_candidate_simulation_context=(
                planner_candidate_simulation_context
            ),
        )
        candidate_cache[candidate_charger_count] = candidate_evaluation
        return candidate_evaluation

    highest_candidate_evaluation = evaluate_candidate(
        highest_candidate_charger_count
    )
    if not highest_candidate_evaluation.service_rule_met:
        return None

    upper_feasible = highest_candidate_charger_count
    while lower_infeasible + 1 < upper_feasible:
        candidate_charger_count = (lower_infeasible + upper_feasible) // 2
        candidate_evaluation = evaluate_candidate(candidate_charger_count)
        if candidate_evaluation.service_rule_met:
            upper_feasible = candidate_charger_count
            continue
        lower_infeasible = candidate_charger_count

    return upper_feasible


def _evaluate_candidate_charger_count_service_rule(
    scenario: Scenario,
    candidate_charger_count: int,
    *,
    planner_candidate_simulation_context: (
        PlannerCandidateSimulationContext | None
    ) = None,
) -> ChargerPlanningRuleEvaluation:
    """Return the service-rule evaluation for one charger-count rerun."""

    candidate_scenario = copy_scenario_with_updates(
        scenario,
        charger_count=candidate_charger_count,
    )
    candidate_result = simulate_planner_candidate(
        candidate_scenario,
        simulation_context=planner_candidate_simulation_context,
    )
    candidate_metrics = _build_planner_candidate_service_rule_metrics(
        candidate_result,
        candidate_scenario,
    )
    return evaluate_charger_count_service_rule(
        candidate_scenario,
        candidate_result,
        candidate_metrics,
    )


def _build_planner_candidate_service_rule_metrics(
    simulation_result: PlannerCandidateSimulationResult,
    scenario: Scenario,
) -> Metrics:
    """Return the minimal Metrics context needed for the service rule."""

    return Metrics(
        total_daily_energy=simulation_result.daily_energy_demand,
        available_capacity=0.0,
        energy_delivery_sufficient=(
            simulation_result.vehicles_with_unmet_energy_count == 0
        ),
        queue_present_indicator=any(
            waiting_count > 0
            for waiting_count in simulation_result.waiting_vehicle_count_by_timestep
        ),
        average_waiting_time_hours=calculate_average_waiting_time_hours(
            simulation_result.started_request_waiting_times_hours,
            request_count=simulation_result.request_count,
        ),
        maximum_waiting_time_hours=calculate_maximum_waiting_time_hours(
            simulation_result.started_request_waiting_times_hours,
            request_count=simulation_result.request_count,
        ),
        charger_service_waiting_tolerance_hours=(
            scenario.charger_service_max_waiting_time_minutes / 60
        ),
        vehicles_waiting_count=simulation_result.vehicles_waiting_count,
        vehicles_not_started_count=simulation_result.vehicles_not_started_count,
        vehicles_with_unmet_energy_count=(
            simulation_result.vehicles_with_unmet_energy_count
        ),
        waiting_vehicle_count_by_timestep=list(
            simulation_result.waiting_vehicle_count_by_timestep
        ),
    )


def _resolve_safe_monotonic_charger_count_ranges(
    scenario: Scenario,
) -> tuple[tuple[int, int], ...] | None:
    """Return charger-count ranges where the service rule is safely monotonic.

    The service-rule outcome can change non-monotonically only when candidate
    charger counts cross the point where installed charger capacity first
    exceeds the site connection limit. The search therefore treats counts on
    each side of that breakpoint as separate monotonic ranges.
    """

    if scenario.charger_power <= FLOATING_POINT_TOLERANCE:
        return None

    highest_non_grid_limited_count = min(
        scenario.vehicles,
        max(
            int(
                math.floor(
                    (
                        scenario.grid_capacity
                        + FLOATING_POINT_TOLERANCE
                    )
                    / scenario.charger_power
                )
            ),
            0,
        ),
    )

    monotonic_ranges: list[tuple[int, int]] = []
    if scenario.charger_count < highest_non_grid_limited_count:
        monotonic_ranges.append(
            (scenario.charger_count, highest_non_grid_limited_count)
        )

    first_grid_limited_count = max(
        highest_non_grid_limited_count + 1,
        scenario.charger_count + 1,
    )
    if first_grid_limited_count <= scenario.vehicles:
        monotonic_ranges.append(
            (first_grid_limited_count - 1, scenario.vehicles)
        )

    return tuple(monotonic_ranges)


def _has_complete_service_rule_evidence(
    scenario: Scenario,
    simulation_result: SimulationResult,
) -> bool:
    """Return whether the required raw evidence exists to trust service success."""
    if scenario.vehicles == 0:
        return True

    if simulation_result.daily_energy_demand <= FLOATING_POINT_TOLERANCE:
        return True

    return (
        _resolve_service_rule_request_count(simulation_result) == scenario.vehicles
        and len(simulation_result.waiting_vehicle_count_by_timestep)
        == TIMESTEPS_PER_DAY
    )


def _resolve_service_rule_request_count(
    simulation_result: SimulationResult | PlannerCandidateSimulationResult,
) -> int:
    request_count = getattr(simulation_result, "request_count", None)
    if request_count is not None:
        return request_count

    return len(simulation_result.charging_requests)
