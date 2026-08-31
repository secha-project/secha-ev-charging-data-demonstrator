"""Helpers for deriving comparable scenario variants."""

from scenarios.scenario import (
    ChargingStrategy,
    Scenario,
    copy_scenario_with_updates,
)


def create_strategy_variants(base_scenario: Scenario) -> tuple[Scenario, Scenario]:
    """Return uncontrolled and smart variants of one base scenario."""
    return (
        _with_charging_strategy(base_scenario, ChargingStrategy.UNCONTROLLED),
        _with_charging_strategy(base_scenario, ChargingStrategy.SMART),
    )


def _with_charging_strategy(
    scenario: Scenario,
    charging_strategy: ChargingStrategy,
) -> Scenario:
    """Return a scenario copy with the selected charging strategy."""
    return copy_scenario_with_updates(
        scenario,
        charging_strategy=charging_strategy,
    )
