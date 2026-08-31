from dataclasses import dataclass
from math import floor

from scenarios import PowerQualityPhaseAllocationMethod, Scenario

from simulation.feeders import expand_feeder_assets
from simulation.formulas import calculate_available_site_capacity
from simulation.grid_loading import allocate_site_ev_load_to_feeders
from simulation.result import FeederPowerQualityResult, PowerQualityResult


PHASE_COUNT = 3
MAX_HARMONIC_FACTOR_FOR_SCORING = 2.0
MAX_CURRENT_IMBALANCE_PERCENT = 200.0


@dataclass(frozen=True)
class FeederPhaseAllocation:
    """Deterministic feeder-level phase-allocation inputs for PQ helpers."""

    feeder_id: str
    charger_count: int
    single_phase_charger_count: int
    three_phase_charger_count: int
    phase_a_equivalent_charger_count: float
    phase_b_equivalent_charger_count: float
    phase_c_equivalent_charger_count: float


def build_feeder_phase_allocations(
    scenario: Scenario,
) -> list[FeederPhaseAllocation]:
    """Return deterministic feeder-level phase allocations for PQ modeling."""
    modeled_feeders = expand_feeder_assets(scenario)
    total_single_phase_charger_count = _calculate_total_single_phase_charger_count(
        scenario.charger_count,
        scenario.single_phase_charger_share_percent,
    )
    single_phase_counts_by_feeder = _allocate_single_phase_chargers_to_feeders(
        scenario,
        total_single_phase_charger_count=total_single_phase_charger_count,
    )

    feeder_phase_allocations: list[FeederPhaseAllocation] = []
    for feeder, single_phase_charger_count in zip(
        modeled_feeders,
        single_phase_counts_by_feeder,
        strict=True,
    ):
        three_phase_charger_count = max(
            feeder.charger_count - single_phase_charger_count,
            0,
        )
        (
            phase_a_single_phase_count,
            phase_b_single_phase_count,
            phase_c_single_phase_count,
        ) = _allocate_single_phase_chargers_to_phases(
            single_phase_charger_count,
            scenario.power_quality_phase_allocation_method,
            feeder_index=feeder.feeder_index,
        )
        three_phase_equivalent_count_per_phase = (
            three_phase_charger_count / PHASE_COUNT
        )

        feeder_phase_allocations.append(
            FeederPhaseAllocation(
                feeder_id=feeder.feeder_id,
                charger_count=feeder.charger_count,
                single_phase_charger_count=single_phase_charger_count,
                three_phase_charger_count=three_phase_charger_count,
                phase_a_equivalent_charger_count=(
                    phase_a_single_phase_count
                    + three_phase_equivalent_count_per_phase
                ),
                phase_b_equivalent_charger_count=(
                    phase_b_single_phase_count
                    + three_phase_equivalent_count_per_phase
                ),
                phase_c_equivalent_charger_count=(
                    phase_c_single_phase_count
                    + three_phase_equivalent_count_per_phase
                ),
            )
        )

    return feeder_phase_allocations


def allocate_feeder_ev_load_to_phases(
    feeder_ev_load_kw: float,
    feeder_phase_allocation: FeederPhaseAllocation,
) -> tuple[float, float, float]:
    """Return one feeder EV load split deterministically across phases."""
    if feeder_ev_load_kw <= 0.0 or feeder_phase_allocation.charger_count <= 0:
        return (0.0, 0.0, 0.0)

    phase_a_load_kw = (
        feeder_ev_load_kw
        * feeder_phase_allocation.phase_a_equivalent_charger_count
        / feeder_phase_allocation.charger_count
    )
    phase_b_load_kw = (
        feeder_ev_load_kw
        * feeder_phase_allocation.phase_b_equivalent_charger_count
        / feeder_phase_allocation.charger_count
    )
    phase_c_load_kw = max(
        feeder_ev_load_kw - phase_a_load_kw - phase_b_load_kw,
        0.0,
    )
    return (
        phase_a_load_kw,
        phase_b_load_kw,
        phase_c_load_kw,
    )


def build_site_phase_load_series(
    scenario: Scenario,
    delivered_load_profile_kw: list[float],
) -> tuple[list[float], list[float], list[float]]:
    """Return aligned site-level phase A/B/C load series for PQ modeling."""
    modeled_feeders = expand_feeder_assets(scenario)
    feeder_phase_allocations = build_feeder_phase_allocations(scenario)
    phase_a_load_kw_by_timestep: list[float] = []
    phase_b_load_kw_by_timestep: list[float] = []
    phase_c_load_kw_by_timestep: list[float] = []

    for site_ev_load_kw in delivered_load_profile_kw:
        feeder_ev_loads_kw = allocate_site_ev_load_to_feeders(
            site_ev_load_kw,
            modeled_feeders,
        )
        phase_a_total_load_kw = 0.0
        phase_b_total_load_kw = 0.0
        phase_c_total_load_kw = 0.0

        for feeder_phase_allocation, feeder_ev_load_kw in zip(
            feeder_phase_allocations,
            feeder_ev_loads_kw,
            strict=True,
        ):
            (
                feeder_phase_a_load_kw,
                feeder_phase_b_load_kw,
                feeder_phase_c_load_kw,
            ) = allocate_feeder_ev_load_to_phases(
                feeder_ev_load_kw,
                feeder_phase_allocation,
            )
            phase_a_total_load_kw += feeder_phase_a_load_kw
            phase_b_total_load_kw += feeder_phase_b_load_kw
            phase_c_total_load_kw += feeder_phase_c_load_kw

        phase_a_load_kw_by_timestep.append(phase_a_total_load_kw)
        phase_b_load_kw_by_timestep.append(phase_b_total_load_kw)
        phase_c_load_kw_by_timestep.append(phase_c_total_load_kw)

    return (
        phase_a_load_kw_by_timestep,
        phase_b_load_kw_by_timestep,
        phase_c_load_kw_by_timestep,
    )


def build_power_quality_result(
    scenario: Scenario,
    delivered_load_profile_kw: list[float],
) -> PowerQualityResult:
    """Return deterministic raw PQ outputs for one simulation run."""
    modeled_feeders = expand_feeder_assets(scenario)
    feeder_phase_allocations = build_feeder_phase_allocations(scenario)
    (
        phase_a_load_kw_by_timestep,
        phase_b_load_kw_by_timestep,
        phase_c_load_kw_by_timestep,
    ) = build_site_phase_load_series(
        scenario,
        delivered_load_profile_kw,
    )
    available_site_capacity_kw = max(
        calculate_available_site_capacity(scenario),
        0.0,
    )
    harmonic_risk_score_by_timestep: list[float] = []
    current_imbalance_percent_by_timestep: list[float] = []
    feeder_harmonic_scores_by_timestep: list[list[float]] = [
        [] for _ in modeled_feeders
    ]
    feeder_current_imbalance_percents_by_timestep: list[list[float]] = [
        [] for _ in modeled_feeders
    ]

    for timestep_index, site_ev_load_kw in enumerate(delivered_load_profile_kw):
        feeder_ev_loads_kw = allocate_site_ev_load_to_feeders(
            site_ev_load_kw,
            modeled_feeders,
        )
        phase_loads_kw = (
            phase_a_load_kw_by_timestep[timestep_index],
            phase_b_load_kw_by_timestep[timestep_index],
            phase_c_load_kw_by_timestep[timestep_index],
        )
        harmonic_risk_score_by_timestep.append(
            calculate_harmonic_risk_score(
                ev_load_kw=site_ev_load_kw,
                capacity_reference_kw=available_site_capacity_kw,
                single_phase_charger_share_percent=(
                    scenario.single_phase_charger_share_percent
                ),
                charger_harmonic_factor=scenario.charger_harmonic_factor,
                phase_loads_kw=phase_loads_kw,
                feeder_ev_loads_kw=feeder_ev_loads_kw,
            )
        )
        current_imbalance_percent_by_timestep.append(
            calculate_current_imbalance_percent(phase_loads_kw)
        )

        for feeder_index, (
            feeder_phase_allocation,
            feeder_ev_load_kw,
        ) in enumerate(
            zip(
                feeder_phase_allocations,
                feeder_ev_loads_kw,
                strict=True,
            )
        ):
            feeder_phase_loads_kw = allocate_feeder_ev_load_to_phases(
                feeder_ev_load_kw,
                feeder_phase_allocation,
            )
            feeder_capacity_reference_kw = (
                feeder_phase_allocation.charger_count * scenario.charger_power
            )
            feeder_harmonic_scores_by_timestep[feeder_index].append(
                calculate_harmonic_risk_score(
                    ev_load_kw=feeder_ev_load_kw,
                    capacity_reference_kw=feeder_capacity_reference_kw,
                    single_phase_charger_share_percent=(
                        scenario.single_phase_charger_share_percent
                    ),
                    charger_harmonic_factor=scenario.charger_harmonic_factor,
                    phase_loads_kw=feeder_phase_loads_kw,
                    feeder_ev_loads_kw=[feeder_ev_load_kw],
                )
            )
            feeder_current_imbalance_percents_by_timestep[feeder_index].append(
                calculate_current_imbalance_percent(feeder_phase_loads_kw)
            )

    return PowerQualityResult(
        harmonic_risk_score_by_timestep=harmonic_risk_score_by_timestep,
        current_imbalance_percent_by_timestep=current_imbalance_percent_by_timestep,
        phase_a_load_kw_by_timestep=phase_a_load_kw_by_timestep,
        phase_b_load_kw_by_timestep=phase_b_load_kw_by_timestep,
        phase_c_load_kw_by_timestep=phase_c_load_kw_by_timestep,
        feeder_power_quality_results=[
            FeederPowerQualityResult(
                feeder_id=feeder_phase_allocation.feeder_id,
                harmonic_risk_score_by_timestep=feeder_harmonic_scores_by_timestep[
                    feeder_index
                ],
                current_imbalance_percent_by_timestep=(
                    feeder_current_imbalance_percents_by_timestep[feeder_index]
                ),
            )
            for feeder_index, feeder_phase_allocation in enumerate(
                feeder_phase_allocations
            )
        ],
    )


def calculate_harmonic_risk_score(
    *,
    ev_load_kw: float,
    capacity_reference_kw: float,
    single_phase_charger_share_percent: float,
    charger_harmonic_factor: float,
    phase_loads_kw: tuple[float, float, float],
    feeder_ev_loads_kw: list[float],
) -> float:
    """Return a bounded planner-facing harmonic-risk score."""
    if ev_load_kw <= 0.0 or capacity_reference_kw <= 0.0:
        return 0.0

    load_factor = _clamp(
        ev_load_kw / capacity_reference_kw,
        minimum=0.0,
        maximum=1.0,
    )
    source_mix_factor = _calculate_harmonic_source_mix_factor(
        single_phase_charger_share_percent=single_phase_charger_share_percent,
        charger_harmonic_factor=charger_harmonic_factor,
    )
    concentration_factor = _calculate_harmonic_concentration_factor(
        phase_loads_kw=phase_loads_kw,
        feeder_ev_loads_kw=feeder_ev_loads_kw,
    )
    return round(
        100.0 * load_factor * source_mix_factor * concentration_factor,
        4,
    )


def calculate_current_imbalance_percent(
    phase_loads_kw: tuple[float, float, float],
) -> float:
    """Return simplified phase current imbalance on a bounded 0-200 scale."""
    average_phase_load_kw = sum(phase_loads_kw) / PHASE_COUNT
    if average_phase_load_kw <= 0.0:
        return 0.0

    highest_phase_load_kw = max(phase_loads_kw)
    imbalance_percent = (
        (highest_phase_load_kw - average_phase_load_kw)
        / average_phase_load_kw
        * 100.0
    )
    return round(
        _clamp(
            imbalance_percent,
            minimum=0.0,
            maximum=MAX_CURRENT_IMBALANCE_PERCENT,
        ),
        4,
    )


def _calculate_total_single_phase_charger_count(
    charger_count: int,
    single_phase_charger_share_percent: float,
) -> int:
    if charger_count <= 0 or single_phase_charger_share_percent <= 0.0:
        return 0

    rounded_single_phase_charger_count = floor(
        charger_count * single_phase_charger_share_percent / 100.0 + 0.5
    )
    return min(max(rounded_single_phase_charger_count, 0), charger_count)


def _allocate_single_phase_chargers_to_feeders(
    scenario: Scenario,
    *,
    total_single_phase_charger_count: int,
) -> list[int]:
    modeled_feeders = expand_feeder_assets(scenario)
    if not modeled_feeders:
        return []

    base_single_phase_counts: list[int] = []
    remainder_candidates: list[tuple[float, int]] = []
    allocated_single_phase_count = 0

    for feeder in modeled_feeders:
        proportional_single_phase_count = (
            feeder.charger_count * scenario.single_phase_charger_share_percent / 100.0
        )
        base_single_phase_count = min(
            floor(proportional_single_phase_count),
            feeder.charger_count,
        )
        base_single_phase_counts.append(base_single_phase_count)
        allocated_single_phase_count += base_single_phase_count
        remainder_candidates.append(
            (
                proportional_single_phase_count - base_single_phase_count,
                feeder.feeder_index,
            )
        )

    remaining_single_phase_count = max(
        total_single_phase_charger_count - allocated_single_phase_count,
        0,
    )
    for _, feeder_index in sorted(
        remainder_candidates,
        key=lambda candidate: (-candidate[0], candidate[1]),
    ):
        if remaining_single_phase_count <= 0:
            break
        if (
            base_single_phase_counts[feeder_index]
            >= modeled_feeders[feeder_index].charger_count
        ):
            continue
        base_single_phase_counts[feeder_index] += 1
        remaining_single_phase_count -= 1

    return base_single_phase_counts


def _allocate_single_phase_chargers_to_phases(
    single_phase_charger_count: int,
    allocation_method: PowerQualityPhaseAllocationMethod,
    *,
    feeder_index: int,
) -> tuple[int, int, int]:
    if single_phase_charger_count <= 0:
        return (0, 0, 0)

    if allocation_method is PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN:
        phase_counts = [0, 0, 0]
        for single_phase_index in range(single_phase_charger_count):
            phase_counts[(feeder_index + single_phase_index) % PHASE_COUNT] += 1
        return (
            phase_counts[0],
            phase_counts[1],
            phase_counts[2],
        )

    if allocation_method is PowerQualityPhaseAllocationMethod.FRONT_LOADED_PHASE_A:
        return (
            single_phase_charger_count,
            0,
            0,
        )

    raise ValueError(
        "Unsupported power-quality phase allocation method: "
        f"{allocation_method!r}."
    )


def _calculate_harmonic_source_mix_factor(
    *,
    single_phase_charger_share_percent: float,
    charger_harmonic_factor: float,
) -> float:
    single_phase_share = _clamp(
        single_phase_charger_share_percent / 100.0,
        minimum=0.0,
        maximum=1.0,
    )
    harmonic_factor_component = _clamp(
        charger_harmonic_factor / MAX_HARMONIC_FACTOR_FOR_SCORING,
        minimum=0.0,
        maximum=1.0,
    )
    return 0.35 + (0.40 * single_phase_share) + (0.25 * harmonic_factor_component)


def _calculate_harmonic_concentration_factor(
    *,
    phase_loads_kw: tuple[float, float, float],
    feeder_ev_loads_kw: list[float],
) -> float:
    phase_concentration = _calculate_normalized_load_concentration(list(phase_loads_kw))
    feeder_concentration = _calculate_normalized_load_concentration(
        feeder_ev_loads_kw
    )
    return 0.70 + (0.30 * max(phase_concentration, feeder_concentration))


def _calculate_normalized_load_concentration(loads_kw: list[float]) -> float:
    if len(loads_kw) <= 1:
        return 0.0

    total_load_kw = sum(loads_kw)
    if total_load_kw <= 0.0:
        return 0.0

    balanced_share = 1.0 / len(loads_kw)
    maximum_share = max(loads_kw) / total_load_kw
    return _clamp(
        (maximum_share - balanced_share) / (1.0 - balanced_share),
        minimum=0.0,
        maximum=1.0,
    )


def _clamp(value: float, *, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)
