from dataclasses import dataclass

from math import floor

from scenarios import FeederEVAllocationMethod, Scenario


@dataclass(frozen=True)
class ModeledFeeder:
    """Internal deterministic feeder asset derived from scenario inputs."""

    feeder_id: str
    feeder_index: int
    charger_count: int
    allocation_share: float
    capacity_kw: float
    base_load_kw: float


def expand_feeder_assets(scenario: Scenario) -> list[ModeledFeeder]:
    """Expand scalar feeder inputs into deterministic per-feeder assets."""
    allocation_shares = _build_feeder_allocation_shares(scenario)
    charger_counts = _build_feeder_charger_counts(scenario, allocation_shares)

    modeled_feeders = []
    for feeder_index in range(scenario.feeder_count):
        modeled_feeders.append(
            ModeledFeeder(
                feeder_id=f"feeder-{feeder_index + 1}",
                feeder_index=feeder_index,
                charger_count=charger_counts[feeder_index],
                allocation_share=allocation_shares[feeder_index],
                capacity_kw=scenario.feeder_capacity_kw,
                base_load_kw=scenario.feeder_base_load_kw,
            )
        )

    return modeled_feeders


def _build_feeder_allocation_shares(scenario: Scenario) -> list[float]:
    if (
        scenario.feeder_ev_allocation_method
        is FeederEVAllocationMethod.BY_CONFIGURED_SHARE
    ):
        assert scenario.feeder_allocation_shares is not None
        total_share = sum(scenario.feeder_allocation_shares)
        return [
            feeder_share / total_share
            for feeder_share in scenario.feeder_allocation_shares
        ]

    if scenario.charger_count <= 0:
        return [0.0 for _ in range(scenario.feeder_count)]

    charger_counts = _build_even_feeder_charger_counts(scenario)
    total_charger_count = sum(charger_counts)
    return [
        charger_count / total_charger_count
        for charger_count in charger_counts
    ]


def _build_feeder_charger_counts(
    scenario: Scenario,
    allocation_shares: list[float],
) -> list[int]:
    if (
        scenario.feeder_ev_allocation_method
        is FeederEVAllocationMethod.BY_CONFIGURED_SHARE
    ):
        return _build_configured_share_feeder_charger_counts(
            scenario.charger_count,
            allocation_shares,
        )

    return _build_even_feeder_charger_counts(scenario)


def _build_even_feeder_charger_counts(scenario: Scenario) -> list[int]:
    base_charger_count = scenario.charger_count // scenario.feeder_count
    remainder_charger_count = scenario.charger_count % scenario.feeder_count

    charger_counts = [base_charger_count for _ in range(scenario.feeder_count)]
    for feeder_index in range(remainder_charger_count):
        charger_counts[feeder_index] += 1

    return charger_counts


def _build_configured_share_feeder_charger_counts(
    total_charger_count: int,
    allocation_shares: list[float],
) -> list[int]:
    if total_charger_count <= 0:
        return [0 for _ in allocation_shares]

    raw_charger_counts = [
        total_charger_count * allocation_share
        for allocation_share in allocation_shares
    ]
    charger_counts = [
        floor(raw_charger_count)
        for raw_charger_count in raw_charger_counts
    ]
    remaining_chargers = total_charger_count - sum(charger_counts)

    ranked_remainders = sorted(
        (
            (raw_charger_counts[feeder_index] - charger_counts[feeder_index], feeder_index)
            for feeder_index in range(len(allocation_shares))
        ),
        key=lambda item: (-item[0], item[1]),
    )

    for _, feeder_index in ranked_remainders[:remaining_chargers]:
        charger_counts[feeder_index] += 1

    return charger_counts
