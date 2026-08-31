"""Orchestration helpers for running comparable simulations."""

from scenarios import Scenario, create_strategy_variants
from simulation.engine import simulate
from simulation.result import SimulationResult


def simulate_strategy_comparison(
    base_scenario: Scenario,
) -> tuple[SimulationResult, SimulationResult]:
    """Run uncontrolled and smart simulations from one base scenario."""
    uncontrolled_scenario, smart_scenario = create_strategy_variants(base_scenario)

    return (
        simulate(uncontrolled_scenario),
        simulate(smart_scenario),
    )


def simulate_scenario_comparison(
    scenario_a: Scenario,
    scenario_b: Scenario,
) -> tuple[SimulationResult, SimulationResult]:
    """Run independent simulations for Scenario A and Scenario B."""
    return (
        simulate(scenario_a),
        simulate(scenario_b),
    )
