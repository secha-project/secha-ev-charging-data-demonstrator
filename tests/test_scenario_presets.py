from scenarios import (
    ArrivalMode,
    ArrivalProfileShape,
    DEFAULT_SCENARIO_PRESET_ID,
    DepartureMode,
    FeederEVAllocationMethod,
    PowerQualityPhaseAllocationMethod,
    PUBLIC_FAST_CHARGING_PRESET_ID,
    WORKPLACE_CHARGING_PRESET_ID,
    create_scenario_comparison_snapshot,
    default_scenario,
    default_scenario_preset,
    get_default_scenario_preset,
    get_scenario_preset,
    list_scenario_presets,
    scenario_from_dict,
    scenario_to_dict,
)
from scenarios.presets import (
    CHARGER_LIMITED_DEPOT_PRESET_ID,
    CONCENTRATED_ARRIVAL_WORKPLACE_CHARGING_PRESET_ID,
    CONSTRAINED_HEAVY_DUTY_PEAK_SHAVING_PRESET_ID,
    PQ_SENSITIVE_AC_CHARGING_PRESET_ID,
)


def test_list_scenario_presets_returns_registered_presets_in_stable_order():
    presets = list_scenario_presets()

    assert isinstance(presets, tuple)
    assert [preset.preset_id for preset in presets] == [
        DEFAULT_SCENARIO_PRESET_ID,
        PUBLIC_FAST_CHARGING_PRESET_ID,
        WORKPLACE_CHARGING_PRESET_ID,
        CONSTRAINED_HEAVY_DUTY_PEAK_SHAVING_PRESET_ID,
        CHARGER_LIMITED_DEPOT_PRESET_ID,
        CONCENTRATED_ARRIVAL_WORKPLACE_CHARGING_PRESET_ID,
        PQ_SENSITIVE_AC_CHARGING_PRESET_ID,
    ]


def test_get_scenario_preset_returns_heavy_duty_default_preset():
    preset = get_scenario_preset(DEFAULT_SCENARIO_PRESET_ID)

    assert preset is default_scenario_preset
    assert preset.label == "Heavy-duty"
    assert preset.scenario is default_scenario
    assert preset.scenario.request_energy_variability_percent == 10.0
    assert preset.scenario.transformer_capacity_kw == 1250.0
    assert preset.scenario.transformer_other_load_kw == 50.0
    assert preset.scenario.feeder_count == 2
    assert preset.scenario.feeder_capacity_kw == 700.0
    assert preset.scenario.feeder_base_load_kw == 25.0
    assert (
        preset.scenario.feeder_ev_allocation_method
        == FeederEVAllocationMethod.BY_CHARGER_COUNT
    )
    assert preset.scenario.feeder_allocation_shares is None
    assert preset.scenario.single_phase_charger_share_percent == 0.0
    assert preset.scenario.charger_harmonic_factor == 1.0
    assert (
        preset.scenario.power_quality_phase_allocation_method
        == PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
    )
    assert preset.scenario.departure_time_spread_minutes == 60
    assert preset.scenario.charger_service_max_waiting_time_minutes == 120


def test_public_fast_charging_preset_exposes_a_simulation_ready_scenario():
    public_fast_charging = get_scenario_preset(PUBLIC_FAST_CHARGING_PRESET_ID)

    assert public_fast_charging.scenario is not None
    assert public_fast_charging.scenario.vehicles == 48
    assert public_fast_charging.scenario.daily_energy_per_vehicle == 50.0
    assert public_fast_charging.scenario.charger_count == 6
    assert public_fast_charging.scenario.charger_power == 300.0
    assert public_fast_charging.scenario.grid_capacity == 1200.0
    assert public_fast_charging.scenario.request_energy_variability_percent == 25.0
    assert public_fast_charging.scenario.transformer_capacity_kw == 1500.0
    assert public_fast_charging.scenario.transformer_other_load_kw == 75.0
    assert public_fast_charging.scenario.feeder_count == 2
    assert public_fast_charging.scenario.feeder_capacity_kw == 750.0
    assert public_fast_charging.scenario.feeder_base_load_kw == 37.5
    assert (
        public_fast_charging.scenario.feeder_ev_allocation_method
        == FeederEVAllocationMethod.BY_CHARGER_COUNT
    )
    assert public_fast_charging.scenario.feeder_allocation_shares is None
    assert public_fast_charging.scenario.single_phase_charger_share_percent == 0.0
    assert public_fast_charging.scenario.charger_harmonic_factor == 1.0
    assert (
        public_fast_charging.scenario.power_quality_phase_allocation_method
        == PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
    )
    assert public_fast_charging.scenario.arrival_mode == ArrivalMode.RANDOM
    assert (
        public_fast_charging.scenario.arrival_profile_shape
        == ArrivalProfileShape.MID_PEAK
    )
    assert public_fast_charging.scenario.departure_mode == DepartureMode.SESSION_DWELL
    assert public_fast_charging.scenario.session_dwell_minutes == 15
    assert public_fast_charging.scenario.departure_time_spread_minutes == 30
    assert public_fast_charging.scenario.charger_service_max_waiting_time_minutes == 15
    assert public_fast_charging.key_assumptions
    assert public_fast_charging.default_parameters


def test_workplace_charging_preset_exposes_a_simulation_ready_scenario():
    workplace_charging = get_scenario_preset(WORKPLACE_CHARGING_PRESET_ID)

    assert workplace_charging.scenario is not None
    assert workplace_charging.scenario.vehicles == 120
    assert workplace_charging.scenario.daily_energy_per_vehicle == 20.0
    assert workplace_charging.scenario.charger_count == 40
    assert workplace_charging.scenario.charger_power == 22.0
    assert workplace_charging.scenario.grid_capacity == 500.0
    assert workplace_charging.scenario.request_energy_variability_percent == 15.0
    assert workplace_charging.scenario.transformer_capacity_kw == 630.0
    assert workplace_charging.scenario.transformer_other_load_kw == 60.0
    assert workplace_charging.scenario.feeder_count == 4
    assert workplace_charging.scenario.feeder_capacity_kw == 160.0
    assert workplace_charging.scenario.feeder_base_load_kw == 15.0
    assert (
        workplace_charging.scenario.feeder_ev_allocation_method
        == FeederEVAllocationMethod.BY_CHARGER_COUNT
    )
    assert workplace_charging.scenario.feeder_allocation_shares is None
    assert workplace_charging.scenario.single_phase_charger_share_percent == 0.0
    assert workplace_charging.scenario.charger_harmonic_factor == 1.0
    assert (
        workplace_charging.scenario.power_quality_phase_allocation_method
        == PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
    )
    assert workplace_charging.scenario.arrival_mode == ArrivalMode.PROFILE
    assert workplace_charging.scenario.arrival_profile_shape == ArrivalProfileShape.EVEN
    assert workplace_charging.scenario.departure_mode == DepartureMode.WINDOW_END
    assert workplace_charging.scenario.session_dwell_minutes is None
    assert workplace_charging.scenario.departure_time_spread_minutes == 120
    assert workplace_charging.scenario.charger_service_max_waiting_time_minutes == 60
    assert workplace_charging.key_assumptions
    assert workplace_charging.default_parameters


def test_constrained_heavy_duty_peak_shaving_preset_exposes_a_showcase_scenario():
    constrained_peak = get_scenario_preset(
        CONSTRAINED_HEAVY_DUTY_PEAK_SHAVING_PRESET_ID
    )

    assert constrained_peak.label == "Constrained Heavy-Duty Peak Shaving"
    assert constrained_peak.scenario is not None
    assert constrained_peak.scenario.vehicles == 60
    assert constrained_peak.scenario.daily_energy_per_vehicle == 180.0
    assert constrained_peak.scenario.charger_count == 12
    assert constrained_peak.scenario.charger_power == 150.0
    assert constrained_peak.scenario.grid_capacity == 1200.0
    assert constrained_peak.scenario.request_energy_variability_percent == 10.0
    assert constrained_peak.scenario.transformer_capacity_kw == 1500.0
    assert constrained_peak.scenario.transformer_other_load_kw == 120.0
    assert constrained_peak.scenario.feeder_count == 2
    assert constrained_peak.scenario.feeder_capacity_kw == 850.0
    assert constrained_peak.scenario.feeder_base_load_kw == 60.0
    assert constrained_peak.scenario.arrival_mode == ArrivalMode.PROFILE
    assert (
        constrained_peak.scenario.arrival_profile_shape
        == ArrivalProfileShape.FRONT_LOADED
    )
    assert constrained_peak.scenario.departure_mode == DepartureMode.WINDOW_END
    assert constrained_peak.scenario.departure_time_spread_minutes == 30
    assert constrained_peak.scenario.charger_service_max_waiting_time_minutes == 120
    assert constrained_peak.key_assumptions
    assert constrained_peak.default_parameters


def test_charger_limited_depot_preset_exposes_service_pressure_inputs():
    charger_limited_depot = get_scenario_preset(CHARGER_LIMITED_DEPOT_PRESET_ID)

    assert charger_limited_depot.label == "Charger-Limited Depot"
    assert charger_limited_depot.scenario is not None
    assert charger_limited_depot.scenario.vehicles == 32
    assert charger_limited_depot.scenario.daily_energy_per_vehicle == 90.0
    assert charger_limited_depot.scenario.charger_count == 8
    assert charger_limited_depot.scenario.charger_power == 150.0
    assert charger_limited_depot.scenario.grid_capacity == 700.0
    assert charger_limited_depot.scenario.request_energy_variability_percent == 10.0
    assert charger_limited_depot.scenario.transformer_capacity_kw == 900.0
    assert charger_limited_depot.scenario.transformer_other_load_kw == 50.0
    assert charger_limited_depot.scenario.feeder_count == 2
    assert charger_limited_depot.scenario.feeder_capacity_kw == 450.0
    assert charger_limited_depot.scenario.feeder_base_load_kw == 25.0
    assert charger_limited_depot.scenario.arrival_mode == ArrivalMode.PROFILE
    assert (
        charger_limited_depot.scenario.arrival_profile_shape
        == ArrivalProfileShape.FRONT_LOADED
    )
    assert charger_limited_depot.scenario.departure_mode == DepartureMode.WINDOW_END
    assert charger_limited_depot.scenario.departure_time_spread_minutes == 30
    assert charger_limited_depot.scenario.charger_service_max_waiting_time_minutes == 120
    assert charger_limited_depot.key_assumptions
    assert charger_limited_depot.default_parameters


def test_concentrated_arrival_workplace_preset_exposes_load_shifting_inputs():
    concentrated_workplace = get_scenario_preset(
        CONCENTRATED_ARRIVAL_WORKPLACE_CHARGING_PRESET_ID
    )

    assert concentrated_workplace.label == "Concentrated-Arrival Workplace Charging"
    assert concentrated_workplace.scenario is not None
    assert concentrated_workplace.scenario.vehicles == 120
    assert concentrated_workplace.scenario.daily_energy_per_vehicle == 20.0
    assert concentrated_workplace.scenario.charger_count == 40
    assert concentrated_workplace.scenario.charger_power == 22.0
    assert concentrated_workplace.scenario.grid_capacity == 500.0
    assert concentrated_workplace.scenario.request_energy_variability_percent == 15.0
    assert concentrated_workplace.scenario.transformer_capacity_kw == 630.0
    assert concentrated_workplace.scenario.transformer_other_load_kw == 60.0
    assert concentrated_workplace.scenario.feeder_count == 4
    assert concentrated_workplace.scenario.feeder_capacity_kw == 160.0
    assert concentrated_workplace.scenario.feeder_base_load_kw == 15.0
    assert concentrated_workplace.scenario.arrival_mode == ArrivalMode.PROFILE
    assert (
        concentrated_workplace.scenario.arrival_profile_shape
        == ArrivalProfileShape.FRONT_LOADED
    )
    assert concentrated_workplace.scenario.departure_mode == DepartureMode.WINDOW_END
    assert concentrated_workplace.scenario.departure_time_spread_minutes == 90
    assert concentrated_workplace.scenario.charger_service_max_waiting_time_minutes == 60
    assert concentrated_workplace.key_assumptions
    assert concentrated_workplace.default_parameters


def test_pq_sensitive_ac_charging_preset_exposes_non_neutral_pq_inputs():
    pq_sensitive_ac = get_scenario_preset(PQ_SENSITIVE_AC_CHARGING_PRESET_ID)

    assert pq_sensitive_ac.label == "PQ-Sensitive AC Charging"
    assert pq_sensitive_ac.scenario is not None
    assert pq_sensitive_ac.scenario.vehicles == 72
    assert pq_sensitive_ac.scenario.daily_energy_per_vehicle == 14.0
    assert pq_sensitive_ac.scenario.charger_count == 30
    assert pq_sensitive_ac.scenario.charger_power == 11.0
    assert pq_sensitive_ac.scenario.grid_capacity == 280.0
    assert pq_sensitive_ac.scenario.request_energy_variability_percent == 10.0
    assert pq_sensitive_ac.scenario.transformer_capacity_kw == 420.0
    assert pq_sensitive_ac.scenario.transformer_other_load_kw == 40.0
    assert pq_sensitive_ac.scenario.feeder_count == 3
    assert pq_sensitive_ac.scenario.feeder_capacity_kw == 110.0
    assert pq_sensitive_ac.scenario.feeder_base_load_kw == 10.0
    assert pq_sensitive_ac.scenario.single_phase_charger_share_percent == 60.0
    assert pq_sensitive_ac.scenario.charger_harmonic_factor == 1.25
    assert (
        pq_sensitive_ac.scenario.power_quality_phase_allocation_method
        == PowerQualityPhaseAllocationMethod.FRONT_LOADED_PHASE_A
    )
    assert pq_sensitive_ac.scenario.departure_time_spread_minutes == 60
    assert pq_sensitive_ac.scenario.charger_service_max_waiting_time_minutes == 120
    assert pq_sensitive_ac.key_assumptions
    assert pq_sensitive_ac.default_parameters


def test_get_default_scenario_preset_returns_heavy_duty_preset():
    assert get_default_scenario_preset() is default_scenario_preset
    assert get_default_scenario_preset().preset_id == DEFAULT_SCENARIO_PRESET_ID


def test_preset_default_parameters_are_derived_from_seed_scenario_values():
    public_fast_charging = get_scenario_preset(PUBLIC_FAST_CHARGING_PRESET_ID)

    assert public_fast_charging.default_parameters == (
        ("Charging sessions", "48"),
        ("Energy demand per session", "50 kWh"),
        ("Typical dwell time", "15 minutes"),
        ("Charger count", "6"),
        ("Charger power", "300 kW"),
        ("Grid capacity", "1200 kW"),
    )


def test_preset_scenarios_round_trip_through_scenario_serialization():
    for preset in list_scenario_presets():
        assert preset.scenario is not None

        data = scenario_to_dict(preset.scenario)
        assert (
            data["single_phase_charger_share_percent"]
            == preset.scenario.single_phase_charger_share_percent
        )
        assert (
            data["request_energy_variability_percent"]
            == preset.scenario.request_energy_variability_percent
        )
        assert data["charger_harmonic_factor"] == preset.scenario.charger_harmonic_factor
        assert data["power_quality_phase_allocation_method"] == (
            preset.scenario.power_quality_phase_allocation_method.value
        )
        assert (
            data["departure_time_spread_minutes"]
            == preset.scenario.departure_time_spread_minutes
        )
        assert (
            data["charger_service_max_waiting_time_minutes"]
            == preset.scenario.charger_service_max_waiting_time_minutes
        )
        restored_scenario = scenario_from_dict(data)

        assert restored_scenario == preset.scenario


def test_preset_scenarios_create_comparison_snapshots_with_grid_asset_fields():
    for preset in list_scenario_presets():
        assert preset.scenario is not None

        snapshot = create_scenario_comparison_snapshot(preset.scenario)

        assert snapshot["scenario_a"] == snapshot["scenario_b"]
        assert "transformer_capacity_kw" in snapshot["scenario_a"]
        assert "transformer_other_load_kw" in snapshot["scenario_a"]
        assert "feeder_count" in snapshot["scenario_a"]
        assert "feeder_capacity_kw" in snapshot["scenario_a"]
        assert "feeder_base_load_kw" in snapshot["scenario_a"]
        assert "feeder_ev_allocation_method" in snapshot["scenario_a"]
        assert "feeder_allocation_shares" in snapshot["scenario_a"]
        assert "single_phase_charger_share_percent" in snapshot["scenario_a"]
        assert "request_energy_variability_percent" in snapshot["scenario_a"]
        assert "charger_harmonic_factor" in snapshot["scenario_a"]
        assert "power_quality_phase_allocation_method" in snapshot["scenario_a"]
        assert "departure_time_spread_minutes" in snapshot["scenario_a"]
        assert "charger_service_max_waiting_time_minutes" in snapshot["scenario_a"]
        assert (
            snapshot["scenario_a"]["single_phase_charger_share_percent"]
            == preset.scenario.single_phase_charger_share_percent
        )
        assert (
            snapshot["scenario_a"]["request_energy_variability_percent"]
            == preset.scenario.request_energy_variability_percent
        )
        assert (
            snapshot["scenario_a"]["charger_harmonic_factor"]
            == preset.scenario.charger_harmonic_factor
        )
        assert (
            snapshot["scenario_a"]["power_quality_phase_allocation_method"]
            == preset.scenario.power_quality_phase_allocation_method.value
        )
        assert (
            snapshot["scenario_a"]["departure_time_spread_minutes"]
            == preset.scenario.departure_time_spread_minutes
        )
        assert (
            snapshot["scenario_a"]["charger_service_max_waiting_time_minutes"]
            == preset.scenario.charger_service_max_waiting_time_minutes
        )


def test_preset_scenarios_ignore_legacy_electricity_price_in_snapshot_payloads():
    restored_scenario = scenario_from_dict(
        {
            "vehicles": 50,
            "daily_energy_per_vehicle": 150.0,
            "charger_count": 10,
            "charger_power": 150.0,
            "grid_capacity": 1000.0,
            "planning_margin_percent": 10.0,
            "electricity_price": 0.15,
            "charging_window_start": "17:00",
            "charging_window_end": "06:00",
            "charging_strategy": "Uncontrolled",
        }
    )

    assert restored_scenario.transformer_capacity_kw == 1000.0
    assert restored_scenario.transformer_other_load_kw == 0.0
    assert restored_scenario.feeder_count == 1
    assert restored_scenario.feeder_capacity_kw == 1000.0
    assert restored_scenario.feeder_base_load_kw == 0.0
    assert (
        restored_scenario.feeder_ev_allocation_method
        == FeederEVAllocationMethod.BY_CHARGER_COUNT
    )
    assert restored_scenario.feeder_allocation_shares is None
    assert restored_scenario.single_phase_charger_share_percent == 0.0
    assert restored_scenario.charger_harmonic_factor == 1.0
    assert (
        restored_scenario.power_quality_phase_allocation_method
        == PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
    )
    assert restored_scenario.request_energy_variability_percent == 0.0
    assert restored_scenario.departure_time_spread_minutes == 0
    assert "electricity_price" not in scenario_to_dict(restored_scenario)


def test_get_scenario_preset_rejects_unknown_preset_id():
    try:
        get_scenario_preset("unknown_scenario")
    except KeyError as exc:
        assert str(exc) == '"Unknown scenario preset: \'unknown_scenario\'."'
    else:
        raise AssertionError("Expected KeyError for an unknown scenario preset.")
