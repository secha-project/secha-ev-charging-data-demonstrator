from scenarios import Scenario

from simulation.feeders import ModeledFeeder, expand_feeder_assets
from simulation.formulas import (
    calculate_transformer_loading_percent,
    calculate_transformer_overload_kw,
)
from simulation.result import FeederLoadingResult


def calculate_feeder_charger_shares(
    modeled_feeders: list[ModeledFeeder],
) -> list[float]:
    """Return deterministic EV-load shares for each feeder."""
    return calculate_feeder_allocation_shares(modeled_feeders)


def calculate_feeder_allocation_shares(
    modeled_feeders: list[ModeledFeeder],
) -> list[float]:
    """Return deterministic EV-load shares for each feeder."""
    return [feeder.allocation_share for feeder in modeled_feeders]


def allocate_site_ev_load_to_feeders(
    site_ev_load_kw: float,
    modeled_feeders: list[ModeledFeeder],
) -> list[float]:
    """Allocate one timestep of site EV load across feeders by charger share."""
    if not modeled_feeders:
        return []

    feeder_allocation_shares = calculate_feeder_allocation_shares(modeled_feeders)
    feeder_ev_loads_kw: list[float] = []
    allocated_load_kw = 0.0

    for feeder_index, allocation_share in enumerate(feeder_allocation_shares):
        if feeder_index == len(feeder_allocation_shares) - 1:
            feeder_ev_load_kw = max(site_ev_load_kw - allocated_load_kw, 0.0)
        else:
            feeder_ev_load_kw = site_ev_load_kw * allocation_share
            allocated_load_kw += feeder_ev_load_kw

        feeder_ev_loads_kw.append(feeder_ev_load_kw)

    return feeder_ev_loads_kw


def build_feeder_loading_results(
    scenario: Scenario,
    delivered_load_profile_kw: list[float],
) -> list[FeederLoadingResult]:
    """Return deterministic per-feeder loading outputs from the site EV load."""
    modeled_feeders = expand_feeder_assets(scenario)
    feeder_total_load_series: list[list[float]] = [[] for _ in modeled_feeders]
    feeder_loading_percent_series: list[list[float]] = [[] for _ in modeled_feeders]
    feeder_overload_series: list[list[float]] = [[] for _ in modeled_feeders]

    for site_ev_load_kw in delivered_load_profile_kw:
        feeder_ev_loads_kw = allocate_site_ev_load_to_feeders(
            site_ev_load_kw,
            modeled_feeders,
        )
        for feeder_index, feeder in enumerate(modeled_feeders):
            total_load_kw = (
                feeder_ev_loads_kw[feeder_index]
                + feeder.base_load_kw
            )
            feeder_total_load_series[feeder_index].append(total_load_kw)
            feeder_loading_percent_series[feeder_index].append(
                calculate_transformer_loading_percent(
                    total_load_kw,
                    feeder.capacity_kw,
                )
            )
            feeder_overload_series[feeder_index].append(
                calculate_transformer_overload_kw(
                    total_load_kw,
                    feeder.capacity_kw,
                )
            )

    return [
        FeederLoadingResult(
            feeder_id=feeder.feeder_id,
            charger_count=feeder.charger_count,
            total_load_kw_by_timestep=feeder_total_load_series[feeder_index],
            loading_percent_by_timestep=feeder_loading_percent_series[feeder_index],
            overload_kw_by_timestep=feeder_overload_series[feeder_index],
        )
        for feeder_index, feeder in enumerate(modeled_feeders)
    ]
