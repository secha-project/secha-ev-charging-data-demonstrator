import pytest

from scenarios import (
    FeederEVAllocationMethod,
    Scenario,
    create_internal_scenario,
    default_scenario,
)
from simulation import (
    allocate_site_ev_load_to_feeders,
    build_feeder_loading_results,
    calculate_available_site_capacity,
    calculate_feeder_allocation_shares,
    calculate_daily_energy_demand,
    calculate_installed_charger_capacity,
    calculate_transformer_loading_percent,
    calculate_transformer_overload_kw,
    calculate_transformer_total_load,
    expand_feeder_assets,
)


def test_calculate_daily_energy_demand_uses_documented_formula():
    assert calculate_daily_energy_demand(default_scenario) == 7500.0


def test_calculate_installed_charger_capacity_uses_documented_formula():
    assert calculate_installed_charger_capacity(default_scenario) == 1500.0


def test_calculate_available_site_capacity_uses_grid_limit_when_lower():
    assert calculate_available_site_capacity(default_scenario) == 1000.0


def test_calculate_available_site_capacity_uses_charger_limit_when_lower():
    scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=500.0,
    )

    assert calculate_available_site_capacity(scenario) == 100.0


def test_formulas_handle_zero_vehicles_internal_scenario():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=150.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=500.0,
    )

    assert calculate_daily_energy_demand(scenario) == 0.0
    assert calculate_installed_charger_capacity(scenario) == 100.0
    assert calculate_available_site_capacity(scenario) == 100.0


def test_formulas_handle_zero_chargers_internal_scenario():
    scenario = create_internal_scenario(
        vehicles=10,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=500.0,
    )

    assert calculate_daily_energy_demand(scenario) == 200.0
    assert calculate_installed_charger_capacity(scenario) == 0.0
    assert calculate_available_site_capacity(scenario) == 0.0


def test_calculate_transformer_total_load_uses_ev_and_background_load():
    assert calculate_transformer_total_load(800.0, 50.0) == 850.0


def test_calculate_transformer_loading_percent_returns_nominal_loading():
    total_load_kw = calculate_transformer_total_load(800.0, 50.0)

    assert calculate_transformer_loading_percent(total_load_kw, 1250.0) == 68.0


def test_calculate_transformer_loading_percent_returns_exact_limit_loading():
    total_load_kw = calculate_transformer_total_load(950.0, 50.0)

    assert calculate_transformer_loading_percent(total_load_kw, 1000.0) == 100.0


def test_calculate_transformer_loading_percent_returns_overloaded_loading():
    total_load_kw = calculate_transformer_total_load(1100.0, 50.0)

    assert calculate_transformer_loading_percent(
        total_load_kw,
        1000.0,
    ) == pytest.approx(115.0)


def test_calculate_transformer_overload_kw_returns_zero_below_limit():
    total_load_kw = calculate_transformer_total_load(800.0, 50.0)

    assert calculate_transformer_overload_kw(total_load_kw, 1250.0) == 0.0


def test_calculate_transformer_overload_kw_returns_zero_at_exact_limit():
    total_load_kw = calculate_transformer_total_load(950.0, 50.0)

    assert calculate_transformer_overload_kw(total_load_kw, 1000.0) == 0.0


def test_calculate_transformer_overload_kw_returns_positive_amount_above_limit():
    total_load_kw = calculate_transformer_total_load(1100.0, 50.0)

    assert calculate_transformer_overload_kw(total_load_kw, 1000.0) == 150.0


def test_transformer_formulas_handle_zero_ev_load_with_non_zero_background_load():
    total_load_kw = calculate_transformer_total_load(0.0, 60.0)

    assert total_load_kw == 60.0
    assert calculate_transformer_loading_percent(total_load_kw, 120.0) == 50.0
    assert calculate_transformer_overload_kw(total_load_kw, 120.0) == 0.0


def test_calculate_feeder_allocation_shares_returns_balanced_shares():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        feeder_count=2,
        feeder_capacity_kw=120.0,
        feeder_base_load_kw=10.0,
    )

    modeled_feeders = expand_feeder_assets(scenario)

    assert calculate_feeder_allocation_shares(modeled_feeders) == [0.5, 0.5]


def test_allocate_site_ev_load_to_feeders_sums_exactly_in_balanced_case():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        feeder_count=2,
        feeder_capacity_kw=120.0,
        feeder_base_load_kw=10.0,
    )

    modeled_feeders = expand_feeder_assets(scenario)
    feeder_ev_loads_kw = allocate_site_ev_load_to_feeders(120.0, modeled_feeders)

    assert feeder_ev_loads_kw == [60.0, 60.0]
    assert sum(feeder_ev_loads_kw) == 120.0


def test_allocate_site_ev_load_to_feeders_supports_single_feeder_configured_share():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=100.0,
        feeder_count=1,
        feeder_capacity_kw=120.0,
        feeder_base_load_kw=10.0,
        feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CONFIGURED_SHARE,
        feeder_allocation_shares=[1.0],
    )

    modeled_feeders = expand_feeder_assets(scenario)
    feeder_ev_loads_kw = allocate_site_ev_load_to_feeders(80.0, modeled_feeders)

    assert [feeder.charger_count for feeder in modeled_feeders] == [2]
    assert calculate_feeder_allocation_shares(modeled_feeders) == [1.0]
    assert feeder_ev_loads_kw == [80.0]


def test_allocate_site_ev_load_to_feeders_returns_zeroes_for_zero_chargers_with_configured_shares():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=100.0,
        feeder_count=2,
        feeder_capacity_kw=120.0,
        feeder_base_load_kw=10.0,
        feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CONFIGURED_SHARE,
        feeder_allocation_shares=[0.8, 0.2],
    )

    modeled_feeders = expand_feeder_assets(scenario)
    feeder_ev_loads_kw = allocate_site_ev_load_to_feeders(0.0, modeled_feeders)

    assert [feeder.charger_count for feeder in modeled_feeders] == [0, 0]
    assert calculate_feeder_allocation_shares(modeled_feeders) == [
        pytest.approx(0.8),
        pytest.approx(0.2),
    ]
    assert feeder_ev_loads_kw == [0.0, 0.0]


def test_allocate_site_ev_load_to_feeders_supports_balanced_configured_shares():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=4,
        charger_power=50.0,
        grid_capacity=200.0,
        feeder_count=2,
        feeder_capacity_kw=120.0,
        feeder_base_load_kw=10.0,
        feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CONFIGURED_SHARE,
        feeder_allocation_shares=[0.5, 0.5],
    )

    modeled_feeders = expand_feeder_assets(scenario)
    feeder_ev_loads_kw = allocate_site_ev_load_to_feeders(120.0, modeled_feeders)

    assert [feeder.charger_count for feeder in modeled_feeders] == [2, 2]
    assert calculate_feeder_allocation_shares(modeled_feeders) == [0.5, 0.5]
    assert feeder_ev_loads_kw == [60.0, 60.0]
    assert sum(feeder_ev_loads_kw) == 120.0


def test_allocate_site_ev_load_to_feeders_handles_unbalanced_default_shares():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=22.5,
        charger_count=3,
        charger_power=100.0,
        grid_capacity=100.0,
        feeder_count=2,
        feeder_capacity_kw=80.0,
        feeder_base_load_kw=10.0,
    )

    modeled_feeders = expand_feeder_assets(scenario)
    feeder_ev_loads_kw = allocate_site_ev_load_to_feeders(90.0, modeled_feeders)
    feeder_loading_results = build_feeder_loading_results(scenario, [90.0])

    assert calculate_feeder_allocation_shares(modeled_feeders) == [
        pytest.approx(2.0 / 3.0),
        pytest.approx(1.0 / 3.0),
    ]
    assert feeder_ev_loads_kw == [60.0, 30.0]
    assert sum(feeder_ev_loads_kw) == 90.0
    assert [
        feeder_result.total_load_kw_by_timestep
        for feeder_result in feeder_loading_results
    ] == [[70.0], [40.0]]


def test_allocate_site_ev_load_to_feeders_uses_configured_shares_exactly():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=22.5,
        charger_count=5,
        charger_power=100.0,
        grid_capacity=100.0,
        feeder_count=2,
        feeder_capacity_kw=80.0,
        feeder_base_load_kw=10.0,
        feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CONFIGURED_SHARE,
        feeder_allocation_shares=[0.7, 0.3],
    )

    modeled_feeders = expand_feeder_assets(scenario)
    feeder_ev_loads_kw = allocate_site_ev_load_to_feeders(90.0, modeled_feeders)
    feeder_loading_results = build_feeder_loading_results(scenario, [90.0])

    assert [feeder.charger_count for feeder in modeled_feeders] == [4, 1]
    assert calculate_feeder_allocation_shares(modeled_feeders) == [
        pytest.approx(0.7),
        pytest.approx(0.3),
    ]
    assert feeder_ev_loads_kw == pytest.approx([63.0, 27.0])
    assert sum(feeder_ev_loads_kw) == 90.0
    feeder_total_loads = [
        feeder_result.total_load_kw_by_timestep
        for feeder_result in feeder_loading_results
    ]

    assert feeder_total_loads[0] == pytest.approx([73.0])
    assert feeder_total_loads[1] == pytest.approx([37.0])


def test_allocate_site_ev_load_to_feeders_supports_configured_shares_80_20():
    scenario = create_internal_scenario(
        vehicles=1,
        daily_energy_per_vehicle=22.5,
        charger_count=5,
        charger_power=100.0,
        grid_capacity=100.0,
        feeder_count=2,
        feeder_capacity_kw=80.0,
        feeder_base_load_kw=10.0,
        feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CONFIGURED_SHARE,
        feeder_allocation_shares=[0.8, 0.2],
    )

    modeled_feeders = expand_feeder_assets(scenario)
    feeder_ev_loads_kw = allocate_site_ev_load_to_feeders(90.0, modeled_feeders)

    assert [feeder.charger_count for feeder in modeled_feeders] == [4, 1]
    assert calculate_feeder_allocation_shares(modeled_feeders) == [
        pytest.approx(0.8),
        pytest.approx(0.2),
    ]
    assert feeder_ev_loads_kw == pytest.approx([72.0, 18.0])
    assert sum(feeder_ev_loads_kw) == 90.0


def test_allocate_site_ev_load_to_feeders_supports_three_feeder_uneven_allocation():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=25.0,
        charger_count=10,
        charger_power=100.0,
        grid_capacity=300.0,
        feeder_count=3,
        feeder_capacity_kw=140.0,
        feeder_base_load_kw=5.0,
        feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CONFIGURED_SHARE,
        feeder_allocation_shares=[0.5, 0.3, 0.2],
    )

    modeled_feeders = expand_feeder_assets(scenario)
    feeder_ev_loads_kw = allocate_site_ev_load_to_feeders(210.0, modeled_feeders)

    assert [feeder.charger_count for feeder in modeled_feeders] == [5, 3, 2]
    assert calculate_feeder_allocation_shares(modeled_feeders) == [
        pytest.approx(0.5),
        pytest.approx(0.3),
        pytest.approx(0.2),
    ]
    assert feeder_ev_loads_kw == pytest.approx([105.0, 63.0, 42.0])
    assert sum(feeder_ev_loads_kw) == 210.0


def test_allocate_site_ev_load_to_feeders_preserves_exact_sum_for_three_feeder_configured_shares():
    scenario = create_internal_scenario(
        vehicles=2,
        daily_energy_per_vehicle=25.0,
        charger_count=6,
        charger_power=100.0,
        grid_capacity=300.0,
        feeder_count=3,
        feeder_capacity_kw=140.0,
        feeder_base_load_kw=5.0,
        feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CONFIGURED_SHARE,
        feeder_allocation_shares=[0.5, 0.3, 0.2],
    )

    modeled_feeders = expand_feeder_assets(scenario)
    site_ev_load_kw = 100.0
    feeder_ev_loads_kw = allocate_site_ev_load_to_feeders(
        site_ev_load_kw,
        modeled_feeders,
    )

    assert feeder_ev_loads_kw == pytest.approx([50.0, 30.0, 20.0])
    assert sum(feeder_ev_loads_kw) == pytest.approx(site_ev_load_kw)


def test_build_feeder_loading_results_handles_zero_ev_load_with_base_load_only():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=22.5,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=100.0,
        feeder_count=2,
        feeder_capacity_kw=100.0,
        feeder_base_load_kw=15.0,
    )

    feeder_loading_results = build_feeder_loading_results(scenario, [0.0, 0.0])

    assert [
        feeder_result.total_load_kw_by_timestep
        for feeder_result in feeder_loading_results
    ] == [[15.0, 15.0], [15.0, 15.0]]
    assert [
        feeder_result.loading_percent_by_timestep
        for feeder_result in feeder_loading_results
    ] == [[15.0, 15.0], [15.0, 15.0]]
    assert [
        feeder_result.overload_kw_by_timestep
        for feeder_result in feeder_loading_results
    ] == [[0.0, 0.0], [0.0, 0.0]]
