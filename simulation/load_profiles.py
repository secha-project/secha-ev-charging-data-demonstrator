"""Load profile generators for formula-based simulations."""

from scenarios import ChargingStrategy, Scenario
from simulation.assignment import simulate_charging_requests
from simulation.time import get_timestep_hours


def generate_uncontrolled_load_profile(
    scenario: Scenario,
    *,
    capacity_limit_kw: float,
) -> list[float]:
    """Generate an uncontrolled charging load profile from the shared request run."""
    return simulate_charging_requests(
        scenario,
        charging_strategy=ChargingStrategy.UNCONTROLLED,
        power_limit_kw=capacity_limit_kw,
    ).load_profile_kw


def generate_smart_load_profile(
    scenario: Scenario,
    *,
    capacity_limit_kw: float,
) -> list[float]:
    """Generate a smart charging load profile from the shared request run."""
    return simulate_charging_requests(
        scenario,
        charging_strategy=ChargingStrategy.SMART,
        power_limit_kw=capacity_limit_kw,
    ).load_profile_kw


def calculate_delivered_energy(load_profile: list[float]) -> float:
    """Return delivered charging energy from a load profile in kWh."""
    return sum(load_profile) * get_timestep_hours()


def calculate_unmet_energy(
    daily_energy_demand: float, delivered_energy: float
) -> float:
    """Return undelivered charging energy in kWh."""
    return max(0.0, daily_energy_demand - delivered_energy)
