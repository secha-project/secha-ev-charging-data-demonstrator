"""Metric orchestration for independent Scenario A/B comparisons."""

from metrics.metrics import Metrics, calculate_metrics
from scenarios import Scenario
from simulation import SimulationResult


def calculate_scenario_comparison_metrics(
    scenario_a: Scenario,
    result_a: SimulationResult,
    scenario_b: Scenario,
    result_b: SimulationResult,
) -> tuple[Metrics, Metrics]:
    """Calculate standard metrics for Scenario A and Scenario B results."""
    return (
        calculate_metrics(result_a, scenario_a),
        calculate_metrics(result_b, scenario_b),
    )
