from datetime import time

from scenarios import (
    ArrivalMode,
    ArrivalProfileShape,
    ChargingStrategy,
    DepartureMode,
    FeederEVAllocationMethod,
    PowerQualityPhaseAllocationMethod,
    Scenario,
    default_scenario,
    default_scenario_preset,
)


def test_default_scenario_uses_heavy_duty_reference_values():
    assert default_scenario == Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        request_energy_variability_percent=10.0,
        transformer_capacity_kw=1250.0,
        transformer_other_load_kw=50.0,
        feeder_count=2,
        feeder_capacity_kw=700.0,
        feeder_base_load_kw=25.0,
        feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CHARGER_COUNT,
        feeder_allocation_shares=None,
        single_phase_charger_share_percent=0.0,
        charger_harmonic_factor=1.0,
        power_quality_phase_allocation_method=(
            PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
        ),
        planning_margin_percent=10.0,
        charging_window_start=time(17, 0),
        charging_window_end=time(6, 0),
        arrival_window_start=time(17, 0),
        arrival_window_end=time(17, 0),
        arrival_mode=ArrivalMode.PROFILE,
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
        departure_mode=DepartureMode.WINDOW_END,
        session_dwell_minutes=None,
        departure_time_spread_minutes=60,
        charger_service_max_waiting_time_minutes=120,
        charging_strategy=ChargingStrategy.UNCONTROLLED,
    )


def test_default_scenario_remains_the_default_preset_scenario():
    assert default_scenario_preset.preset_id == "heavy_duty"
    assert default_scenario_preset.scenario is default_scenario


def test_default_scenario_grid_asset_inputs_remain_boundary_safe():
    assert default_scenario.transformer_capacity_kw > 0
    assert default_scenario.transformer_other_load_kw >= 0
    assert default_scenario.feeder_count > 0
    assert default_scenario.feeder_capacity_kw > 0
    assert default_scenario.feeder_base_load_kw >= 0
    assert (
        default_scenario.feeder_ev_allocation_method
        == FeederEVAllocationMethod.BY_CHARGER_COUNT
    )
    assert default_scenario.feeder_allocation_shares is None
    assert default_scenario.single_phase_charger_share_percent == 0.0
    assert default_scenario.charger_harmonic_factor == 1.0
    assert (
        default_scenario.power_quality_phase_allocation_method
        == PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
    )
