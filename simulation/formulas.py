"""Formula helpers for raw simulation calculations."""

from scenarios import Scenario

PERCENT_MULTIPLIER = 100.0


def calculate_daily_energy_demand(scenario: Scenario) -> float:
    """Return total daily charging energy demand in kWh."""
    return scenario.vehicles * scenario.daily_energy_per_vehicle


def calculate_installed_charger_capacity(scenario: Scenario) -> float:
    """Return installed charger capacity in kW."""
    return scenario.charger_count * scenario.charger_power


def calculate_available_site_capacity(scenario: Scenario) -> float:
    """Return available charging capacity limited by chargers and grid in kW."""
    installed_charger_capacity = calculate_installed_charger_capacity(scenario)
    return min(installed_charger_capacity, scenario.grid_capacity)


def calculate_transformer_total_load(
    ev_charging_load_kw: float,
    transformer_other_load_kw: float,
) -> float:
    """Return total transformer load from EV charging and other load in kW."""
    return ev_charging_load_kw + transformer_other_load_kw


def calculate_transformer_loading_percent(
    total_transformer_load_kw: float,
    transformer_capacity_kw: float,
) -> float:
    """Return transformer loading as a percentage of transformer capacity."""
    return (
        total_transformer_load_kw
        / transformer_capacity_kw
        * PERCENT_MULTIPLIER
    )


def calculate_transformer_overload_kw(
    total_transformer_load_kw: float,
    transformer_capacity_kw: float,
) -> float:
    """Return transformer overload amount in kW above the rated capacity."""
    return max(total_transformer_load_kw - transformer_capacity_kw, 0.0)
