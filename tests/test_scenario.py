from dataclasses import FrozenInstanceError, fields, replace
from datetime import time
import json

import pytest

from scenarios import (
    ACTIVE_SCENARIO_STATE_SCHEMA_VERSION,
    ArrivalMode,
    ArrivalProfileShape,
    ChargingStrategy,
    COMPARISON_SOURCE_MODIFIED_COPY,
    COMPARISON_SOURCE_TEMPLATE,
    DEFAULT_SCENARIO_PRESET_ID,
    DepartureMode,
    FeederEVAllocationMethod,
    PowerQualityPhaseAllocationMethod,
    PUBLIC_FAST_CHARGING_PRESET_ID,
    SCENARIO_B_EDITABLE_FIELDS,
    SCENARIO_STATE_FIELD_NAMES,
    Scenario,
    active_scenario_from_state,
    apply_preset_defaults_to_active_scenario_state,
    comparison_scenarios_from_state,
    coerce_scenario_field_value,
    copy_scenario_with_updates,
    create_active_scenario_state,
    create_scenario_comparison_state,
    create_scenario_comparison_snapshot,
    create_internal_scenario,
    create_strategy_variants,
    duplicate_scenario,
    get_active_scenario_is_modified,
    get_active_scenario_metadata,
    get_active_scenario_parameters,
    get_active_scenario_preset_id,
    get_normalized_scenario_b_snapshot,
    get_scenario_preset,
    is_scenario_modified_from_preset,
    list_scenario_field_definitions,
    normalize_scenario_comparison_data,
    reset_active_scenario_to_preset_defaults,
    scenario_b_editable_values_from_state,
    scenario_field_values_from_state,
    scenario_parameters_from_input_values,
    scenario_from_dict,
    scenario_to_dict,
    summarize_scenario_assumption_change_overview,
    summarize_scenario_assumption_differences,
    update_active_scenario_parameters,
    update_scenario_a_in_comparison_data,
    update_scenario_b,
    update_scenario_b_in_comparison_data,
    update_scenario_b_in_comparison_state,
    WORKPLACE_CHARGING_PRESET_ID,
)


def test_scenario_contains_required_mvp_fields():
    assert [field.name for field in fields(Scenario)] == [
        "vehicles",
        "daily_energy_per_vehicle",
        "charger_count",
        "charger_power",
        "grid_capacity",
        "request_energy_variability_percent",
        "transformer_capacity_kw",
        "transformer_other_load_kw",
        "feeder_count",
        "feeder_capacity_kw",
        "feeder_base_load_kw",
        "feeder_ev_allocation_method",
        "feeder_allocation_shares",
        "single_phase_charger_share_percent",
        "charger_harmonic_factor",
        "power_quality_phase_allocation_method",
        "planning_margin_percent",
        "charging_window_start",
        "charging_window_end",
        "arrival_window_start",
        "arrival_window_end",
        "arrival_mode",
        "arrival_profile_shape",
        "departure_mode",
        "session_dwell_minutes",
        "departure_time_spread_minutes",
        "charger_service_max_waiting_time_minutes",
        "charging_strategy",
    ]


def test_scenario_field_schema_covers_all_editable_scenario_fields():
    assert [field.field_name for field in list_scenario_field_definitions()] == [
        field.name for field in fields(Scenario)
    ]


def test_charging_strategy_contains_supported_mvp_values():
    assert ChargingStrategy.UNCONTROLLED.value == "Uncontrolled"
    assert ChargingStrategy.SMART.value == "Smart Charging"


def test_arrival_profile_shape_contains_supported_values():
    assert ArrivalProfileShape.FRONT_LOADED.value == "front_loaded"
    assert ArrivalProfileShape.FRONT_WEIGHTED.value == "front_weighted"
    assert ArrivalProfileShape.MID_PEAK.value == "mid_peak"
    assert ArrivalProfileShape.EVEN.value == "even"


def test_active_scenario_state_separates_preset_metadata_and_parameters():
    preset = get_scenario_preset(WORKPLACE_CHARGING_PRESET_ID)
    assert preset.scenario is not None

    active_state = create_active_scenario_state(
        preset.preset_id,
        preset.scenario,
    )

    assert active_state["schema_version"] == ACTIVE_SCENARIO_STATE_SCHEMA_VERSION
    assert active_state["preset"] == {
        "preset_id": WORKPLACE_CHARGING_PRESET_ID,
        "is_modified": False,
    }
    assert active_state["metadata"] == {
        "name": "Workplace Charging",
        "description": preset.purpose,
        "assumptions": list(preset.key_assumptions),
    }
    assert active_state["parameters"] == scenario_to_dict(preset.scenario)
    assert get_active_scenario_preset_id(active_state) == WORKPLACE_CHARGING_PRESET_ID
    assert get_active_scenario_metadata(active_state)["name"] == "Workplace Charging"
    assert get_active_scenario_parameters(active_state)["vehicles"] == 120
    assert active_scenario_from_state(active_state) == preset.scenario


def test_active_scenario_state_marks_non_default_strategy_as_modified():
    modified_state = apply_preset_defaults_to_active_scenario_state(
        WORKPLACE_CHARGING_PRESET_ID,
        charging_strategy_value=ChargingStrategy.SMART.value,
    )

    assert modified_state["preset"] == {
        "preset_id": WORKPLACE_CHARGING_PRESET_ID,
        "is_modified": True,
    }
    assert get_active_scenario_is_modified(modified_state) is True
    assert (
        modified_state["parameters"]["charging_strategy"]
        == ChargingStrategy.SMART.value
    )


def test_active_scenario_state_supports_legacy_store_shape_for_transition():
    preset = get_scenario_preset(WORKPLACE_CHARGING_PRESET_ID)
    assert preset.scenario is not None
    legacy_state = {
        "preset_id": WORKPLACE_CHARGING_PRESET_ID,
        "scenario": scenario_to_dict(preset.scenario),
    }

    assert get_active_scenario_preset_id(legacy_state) == WORKPLACE_CHARGING_PRESET_ID
    assert get_active_scenario_metadata(legacy_state)["name"] == "Workplace Charging"
    assert get_active_scenario_parameters(legacy_state)["vehicles"] == 120
    assert active_scenario_from_state(legacy_state).vehicles == 120
    assert get_active_scenario_is_modified(legacy_state) is False


def test_is_scenario_modified_from_preset_detects_parameter_edits():
    preset = get_scenario_preset(WORKPLACE_CHARGING_PRESET_ID)
    assert preset.scenario is not None

    edited_parameters = scenario_to_dict(
        replace(
            preset.scenario,
            vehicles=150,
        )
    )

    assert is_scenario_modified_from_preset(
        WORKPLACE_CHARGING_PRESET_ID,
        preset.scenario,
    ) is False
    assert is_scenario_modified_from_preset(
        WORKPLACE_CHARGING_PRESET_ID,
        edited_parameters,
    ) is True


def test_update_active_scenario_parameters_preserves_existing_edits():
    preset = get_scenario_preset(WORKPLACE_CHARGING_PRESET_ID)
    assert preset.scenario is not None
    active_state = create_active_scenario_state(
        WORKPLACE_CHARGING_PRESET_ID,
        replace(
            preset.scenario,
            vehicles=150,
        ),
    )

    updated_state = update_active_scenario_parameters(
        active_state,
        parameter_updates={
            "charging_strategy": ChargingStrategy.SMART.value,
        },
    )

    assert updated_state["parameters"]["vehicles"] == 150
    assert (
        updated_state["parameters"]["charging_strategy"]
        == ChargingStrategy.SMART.value
    )
    assert get_active_scenario_is_modified(updated_state) is True


def test_reset_active_scenario_to_preset_defaults_restores_seed_values():
    preset = get_scenario_preset(WORKPLACE_CHARGING_PRESET_ID)
    assert preset.scenario is not None
    active_state = create_active_scenario_state(
        WORKPLACE_CHARGING_PRESET_ID,
        replace(
            preset.scenario,
            vehicles=150,
            charging_strategy=ChargingStrategy.SMART,
        ),
    )

    reset_state = reset_active_scenario_to_preset_defaults(active_state)

    assert reset_state["preset"] == {
        "preset_id": WORKPLACE_CHARGING_PRESET_ID,
        "is_modified": False,
    }
    assert reset_state["parameters"] == scenario_to_dict(preset.scenario)
    assert active_scenario_from_state(reset_state) == preset.scenario


def test_apply_preset_defaults_to_active_scenario_state_overwrites_existing_edits():
    edited_state = update_active_scenario_parameters(
        apply_preset_defaults_to_active_scenario_state(
            WORKPLACE_CHARGING_PRESET_ID
        ),
        parameter_updates={
            "vehicles": 144,
            "grid_capacity": 640.0,
            "charging_strategy": ChargingStrategy.SMART.value,
        },
    )
    public_fast_preset = get_scenario_preset(PUBLIC_FAST_CHARGING_PRESET_ID)
    assert public_fast_preset.scenario is not None

    reseeded_state = apply_preset_defaults_to_active_scenario_state(
        PUBLIC_FAST_CHARGING_PRESET_ID
    )

    assert get_active_scenario_is_modified(edited_state) is True
    assert reseeded_state["preset"] == {
        "preset_id": PUBLIC_FAST_CHARGING_PRESET_ID,
        "is_modified": False,
    }
    assert reseeded_state["metadata"]["name"] == "Public Fast Charging"
    assert reseeded_state["parameters"] == scenario_to_dict(
        public_fast_preset.scenario
    )
    assert active_scenario_from_state(reseeded_state) == public_fast_preset.scenario


def test_edited_active_scenario_state_round_trips_through_json_serialization():
    edited_state = update_active_scenario_parameters(
        apply_preset_defaults_to_active_scenario_state(
            WORKPLACE_CHARGING_PRESET_ID
        ),
        parameter_updates={
            "vehicles": 144,
            "grid_capacity": 640.0,
            "request_energy_variability_percent": 18.0,
            "charging_strategy": ChargingStrategy.SMART.value,
        },
    )

    restored_state = json.loads(json.dumps(edited_state))

    assert restored_state == edited_state
    assert restored_state["preset"] == {
        "preset_id": WORKPLACE_CHARGING_PRESET_ID,
        "is_modified": True,
    }
    assert restored_state["metadata"]["name"] == "Workplace Charging"
    assert restored_state["parameters"]["vehicles"] == 144
    assert restored_state["parameters"]["grid_capacity"] == 640.0
    assert restored_state["parameters"]["charging_strategy"] == (
        ChargingStrategy.SMART.value
    )
    assert active_scenario_from_state(restored_state) == active_scenario_from_state(
        edited_state
    )


def test_scenario_field_values_from_state_preserve_store_shape_for_sidebar_inputs():
    active_state = update_active_scenario_parameters(
        apply_preset_defaults_to_active_scenario_state(
            DEFAULT_SCENARIO_PRESET_ID
        ),
        parameter_updates={
            "feeder_count": 3,
            "feeder_ev_allocation_method": (
                FeederEVAllocationMethod.BY_CONFIGURED_SHARE.value
            ),
            "feeder_allocation_shares": [0.5, 0.3, 0.2],
        },
    )

    field_values = scenario_field_values_from_state(active_state)
    field_value_map = dict(zip(SCENARIO_STATE_FIELD_NAMES, field_values, strict=True))

    assert field_value_map["vehicles"] == 50
    assert field_value_map["charging_strategy"] == ChargingStrategy.UNCONTROLLED.value
    assert field_value_map["feeder_allocation_shares"] == "0.5, 0.3, 0.2"


def test_scenario_parameters_from_input_values_apply_existing_dependent_defaults():
    active_state = apply_preset_defaults_to_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID
    )
    field_value_map = dict(
        zip(
            SCENARIO_STATE_FIELD_NAMES,
            scenario_field_values_from_state(active_state),
            strict=True,
        )
    )
    field_value_map["departure_mode"] = DepartureMode.SESSION_DWELL.value
    field_value_map["session_dwell_minutes"] = None
    field_value_map["feeder_count"] = 3
    field_value_map["feeder_ev_allocation_method"] = (
        FeederEVAllocationMethod.BY_CONFIGURED_SHARE.value
    )
    field_value_map["feeder_allocation_shares"] = ""

    next_parameters = scenario_parameters_from_input_values(
        active_state,
        field_value_map,
    )

    assert next_parameters["session_dwell_minutes"] == 60
    assert next_parameters["feeder_allocation_shares"] == pytest.approx(
        [1 / 3, 1 / 3, 1 / 3]
    )


def test_scenario_parameters_from_input_values_keep_default_arrival_window_linked_to_charging_start():
    active_state = apply_preset_defaults_to_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID
    )
    field_value_map = dict(
        zip(
            SCENARIO_STATE_FIELD_NAMES,
            scenario_field_values_from_state(active_state),
            strict=True,
        )
    )
    field_value_map["charging_window_start"] = "18:00"

    next_parameters = scenario_parameters_from_input_values(
        active_state,
        field_value_map,
    )

    assert next_parameters["charging_window_start"] == "18:00"
    assert next_parameters["arrival_window_start"] == "18:00"
    assert next_parameters["arrival_window_end"] == "18:00"


def test_scenario_parameters_from_input_values_preserve_explicit_arrival_window_overrides():
    active_state = apply_preset_defaults_to_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID
    )
    field_value_map = dict(
        zip(
            SCENARIO_STATE_FIELD_NAMES,
            scenario_field_values_from_state(active_state),
            strict=True,
        )
    )
    field_value_map["charging_window_start"] = "18:00"
    field_value_map["arrival_window_start"] = "19:00"
    field_value_map["arrival_window_end"] = "20:00"

    next_parameters = scenario_parameters_from_input_values(
        active_state,
        field_value_map,
    )

    assert next_parameters["charging_window_start"] == "18:00"
    assert next_parameters["arrival_window_start"] == "19:00"
    assert next_parameters["arrival_window_end"] == "20:00"


def test_coerce_scenario_field_value_preserves_sidebar_whole_number_rules():
    assert coerce_scenario_field_value("vehicles", 500.0) == 500
    assert coerce_scenario_field_value("charger_count", 12.0) == 12
    assert coerce_scenario_field_value("departure_time_spread_minutes", 45.0) == 45

    with pytest.raises(ValueError, match="Number of vehicles must be a whole number."):
        coerce_scenario_field_value("vehicles", 499.5)


def test_create_scenario_comparison_state_from_active_state_preserves_existing_store_contract():
    active_state = apply_preset_defaults_to_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        charging_strategy_value=ChargingStrategy.SMART.value,
    )

    comparison_state = create_scenario_comparison_state(active_state)

    assert comparison_state["comparison_source"] == COMPARISON_SOURCE_MODIFIED_COPY
    assert comparison_state["selected_template"] is None
    assert comparison_state["scenario_a"] == comparison_state["scenario_b"]
    assert comparison_state["normalized_scenario_b"] == comparison_state["scenario_b"]
    assert comparison_state["scenario_a"]["charging_strategy"] == (
        ChargingStrategy.SMART.value
    )


def test_comparison_scenarios_from_state_uses_normalized_template_scenario_b():
    active_state = apply_preset_defaults_to_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        charging_strategy_value=ChargingStrategy.SMART.value,
    )
    comparison_state = create_scenario_comparison_state(
        active_state,
        comparison_source=COMPARISON_SOURCE_TEMPLATE,
        selected_template=WORKPLACE_CHARGING_PRESET_ID,
    )
    comparison_state["scenario_b"]["vehicles"] = 75

    scenario_a, scenario_b = comparison_scenarios_from_state(comparison_state)

    assert scenario_a.vehicles == 50
    assert scenario_b.vehicles == 120
    assert scenario_b.charger_count == 40
    assert scenario_b.charging_strategy == ChargingStrategy.SMART


def test_scenario_b_state_helpers_round_trip_editable_values_and_coercion():
    comparison_state = create_scenario_comparison_state(
        apply_preset_defaults_to_active_scenario_state(
            DEFAULT_SCENARIO_PRESET_ID,
            charging_strategy_value=ChargingStrategy.UNCONTROLLED.value,
        )
    )

    assert scenario_b_editable_values_from_state(comparison_state) == (
        50,
        10,
        150.0,
        1000.0,
    )

    updated_state = update_scenario_b_in_comparison_state(
        comparison_state,
        vehicles=75.0,
        charger_count=12.0,
        charger_power=180.0,
        grid_capacity=1200.0,
    )

    assert updated_state["scenario_b"]["vehicles"] == 75
    assert updated_state["scenario_b"]["charger_count"] == 12
    assert updated_state["scenario_b"]["charger_power"] == 180.0
    assert updated_state["scenario_b"]["grid_capacity"] == 1200.0


def test_arrival_mode_contains_supported_values():
    assert ArrivalMode.PROFILE.value == "profile"
    assert ArrivalMode.RANDOM.value == "random"


def test_departure_mode_contains_supported_values():
    assert DepartureMode.WINDOW_END.value == "window_end"
    assert DepartureMode.SESSION_DWELL.value == "session_dwell"


def test_feeder_ev_allocation_method_contains_supported_mvp_values():
    assert (
        FeederEVAllocationMethod.BY_CHARGER_COUNT.value
        == "by_charger_count"
    )
    assert (
        FeederEVAllocationMethod.BY_CONFIGURED_SHARE.value
        == "by_configured_share"
    )


def test_power_quality_phase_allocation_method_contains_supported_values():
    assert (
        PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN.value
        == "balanced_round_robin"
    )
    assert (
        PowerQualityPhaseAllocationMethod.FRONT_LOADED_PHASE_A.value
        == "front_loaded_phase_a"
    )


def test_scenario_accepts_positive_values():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        charging_window_start=time(17, 0),
        charging_window_end=time(6, 0),
    )

    assert scenario.vehicles == 50
    assert scenario.daily_energy_per_vehicle == 150.0
    assert scenario.charger_count == 10
    assert scenario.charger_power == 150.0
    assert scenario.grid_capacity == 1000.0
    assert scenario.request_energy_variability_percent == 0.0
    assert scenario.transformer_capacity_kw == 1000.0
    assert scenario.transformer_other_load_kw == 0.0
    assert scenario.feeder_count == 1
    assert scenario.feeder_capacity_kw == 1000.0
    assert scenario.feeder_base_load_kw == 0.0
    assert (
        scenario.feeder_ev_allocation_method
        == FeederEVAllocationMethod.BY_CHARGER_COUNT
    )
    assert scenario.feeder_allocation_shares is None
    assert scenario.single_phase_charger_share_percent == 0.0
    assert scenario.charger_harmonic_factor == 1.0
    assert (
        scenario.power_quality_phase_allocation_method
        == PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
    )
    assert scenario.planning_margin_percent == 10.0
    assert scenario.charging_window_start == time(17, 0)
    assert scenario.charging_window_end == time(6, 0)
    assert scenario.arrival_window_start == time(17, 0)
    assert scenario.arrival_window_end == time(17, 0)
    assert scenario.arrival_mode == ArrivalMode.PROFILE
    assert scenario.arrival_profile_shape == ArrivalProfileShape.FRONT_LOADED
    assert scenario.departure_mode == DepartureMode.WINDOW_END
    assert scenario.session_dwell_minutes is None
    assert scenario.departure_time_spread_minutes == 0
    assert scenario.charger_service_max_waiting_time_minutes == 30
    assert scenario.charging_strategy == ChargingStrategy.UNCONTROLLED


def test_scenario_normalizes_whole_number_count_fields_from_numeric_inputs():
    scenario = Scenario(
        vehicles=50.0,
        daily_energy_per_vehicle=150.0,
        charger_count=10.0,
        charger_power=150.0,
        grid_capacity=1000.0,
        feeder_count=2.0,
    )

    assert scenario.vehicles == 50
    assert isinstance(scenario.vehicles, int)
    assert scenario.charger_count == 10
    assert isinstance(scenario.charger_count, int)
    assert scenario.feeder_count == 2
    assert isinstance(scenario.feeder_count, int)


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("vehicles", 49.5),
        ("charger_count", 9.5),
        ("feeder_count", 1.5),
    ],
)
def test_scenario_rejects_fractional_count_fields(field_name, field_value):
    scenario_kwargs = {
        "vehicles": 50,
        "daily_energy_per_vehicle": 150.0,
        "charger_count": 10,
        "charger_power": 150.0,
        "grid_capacity": 1000.0,
    }
    scenario_kwargs[field_name] = field_value

    with pytest.raises(ValueError, match=f"{field_name} must be a whole number."):
        Scenario(**scenario_kwargs)


def test_scenario_accepts_request_behavior_inputs():
    scenario = Scenario(
        vehicles=24,
        daily_energy_per_vehicle=80.0,
        charger_count=6,
        charger_power=300.0,
        grid_capacity=1200.0,
        request_energy_variability_percent=25.0,
        departure_mode=DepartureMode.SESSION_DWELL,
        session_dwell_minutes=30,
        departure_time_spread_minutes=15,
        charger_service_max_waiting_time_minutes=45,
    )

    assert scenario.request_energy_variability_percent == 25.0
    assert scenario.departure_time_spread_minutes == 15
    assert scenario.charger_service_max_waiting_time_minutes == 45


def test_scenario_accepts_non_negative_planning_margin_percent():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        planning_margin_percent=0.0,
    )

    assert scenario.planning_margin_percent == 0.0


def test_scenario_accepts_zero_request_energy_variability_percent():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        request_energy_variability_percent=0.0,
    )

    assert scenario.request_energy_variability_percent == 0.0


def test_scenario_accepts_explicit_grid_asset_inputs():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        transformer_capacity_kw=1250.0,
        transformer_other_load_kw=150.0,
        feeder_count=3,
        feeder_capacity_kw=400.0,
        feeder_base_load_kw=25.0,
        feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CHARGER_COUNT,
    )

    assert scenario.transformer_capacity_kw == 1250.0
    assert scenario.transformer_other_load_kw == 150.0
    assert scenario.feeder_count == 3
    assert scenario.feeder_capacity_kw == 400.0
    assert scenario.feeder_base_load_kw == 25.0
    assert (
        scenario.feeder_ev_allocation_method
        == FeederEVAllocationMethod.BY_CHARGER_COUNT
    )
    assert scenario.feeder_allocation_shares is None


def test_scenario_accepts_configured_feeder_allocation_shares():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        feeder_count=3,
        feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CONFIGURED_SHARE,
        feeder_allocation_shares=[0.5, 0.3, 0.2],
    )

    assert (
        scenario.feeder_ev_allocation_method
        == FeederEVAllocationMethod.BY_CONFIGURED_SHARE
    )
    assert scenario.feeder_allocation_shares == (0.5, 0.3, 0.2)


def test_scenario_serializes_and_deserializes_configured_feeder_allocation_inputs():
    scenario = Scenario(
        vehicles=24,
        daily_energy_per_vehicle=80.0,
        charger_count=6,
        charger_power=300.0,
        grid_capacity=1200.0,
        feeder_count=2,
        feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CONFIGURED_SHARE,
        feeder_allocation_shares=[0.7, 0.3],
    )

    data = scenario_to_dict(scenario)
    restored_scenario = scenario_from_dict(data)

    assert data["feeder_ev_allocation_method"] == "by_configured_share"
    assert data["feeder_allocation_shares"] == [0.7, 0.3]
    assert restored_scenario == scenario


def test_scenario_accepts_explicit_power_quality_inputs():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        single_phase_charger_share_percent=40.0,
        charger_harmonic_factor=1.25,
        power_quality_phase_allocation_method=(
            PowerQualityPhaseAllocationMethod.FRONT_LOADED_PHASE_A
        ),
    )

    assert scenario.single_phase_charger_share_percent == 40.0
    assert scenario.charger_harmonic_factor == 1.25
    assert (
        scenario.power_quality_phase_allocation_method
        == PowerQualityPhaseAllocationMethod.FRONT_LOADED_PHASE_A
    )


def test_scenario_defaults_grid_asset_inputs_deterministically_from_grid_capacity():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
    )

    assert scenario.transformer_capacity_kw == scenario.grid_capacity
    assert scenario.transformer_other_load_kw == 0.0
    assert scenario.feeder_count == 1
    assert scenario.feeder_capacity_kw == scenario.transformer_capacity_kw
    assert scenario.feeder_base_load_kw == 0.0
    assert (
        scenario.feeder_ev_allocation_method
        == FeederEVAllocationMethod.BY_CHARGER_COUNT
    )
    assert scenario.feeder_allocation_shares is None
    assert scenario.single_phase_charger_share_percent == 0.0
    assert scenario.charger_harmonic_factor == 1.0
    assert (
        scenario.power_quality_phase_allocation_method
        == PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
    )


def test_scenario_accepts_decimal_planning_margin_percent():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        planning_margin_percent=15.0,
    )

    assert scenario.planning_margin_percent == 15.0


def test_scenario_accepts_decimal_request_energy_variability_percent():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        request_energy_variability_percent=12.5,
    )

    assert scenario.request_energy_variability_percent == 12.5


def test_scenario_accepts_charging_strategy_selection():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        charging_strategy=ChargingStrategy.SMART,
    )

    assert scenario.charging_strategy == ChargingStrategy.SMART


@pytest.mark.parametrize("arrival_profile_shape", list(ArrivalProfileShape))
def test_scenario_accepts_supported_arrival_profile_shapes(arrival_profile_shape):
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        charging_window_start=time(17, 0),
        charging_window_end=time(6, 0),
        arrival_window_start=time(17, 0),
        arrival_window_end=time(20, 0),
        arrival_profile_shape=arrival_profile_shape,
    )

    assert scenario.arrival_profile_shape == arrival_profile_shape


@pytest.mark.parametrize("arrival_mode", list(ArrivalMode))
def test_scenario_accepts_supported_arrival_modes(arrival_mode):
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        charging_window_start=time(17, 0),
        charging_window_end=time(6, 0),
        arrival_window_start=time(17, 0),
        arrival_window_end=time(20, 0),
        arrival_mode=arrival_mode,
    )

    assert scenario.arrival_mode == arrival_mode


@pytest.mark.parametrize("departure_mode", list(DepartureMode))
def test_scenario_accepts_supported_departure_modes(departure_mode):
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        departure_mode=departure_mode,
        session_dwell_minutes=30 if departure_mode is DepartureMode.SESSION_DWELL else None,
    )

    assert scenario.departure_mode == departure_mode


@pytest.mark.parametrize(
    "power_quality_phase_allocation_method",
    list(PowerQualityPhaseAllocationMethod),
)
def test_scenario_accepts_supported_power_quality_phase_allocation_methods(
    power_quality_phase_allocation_method,
):
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        power_quality_phase_allocation_method=power_quality_phase_allocation_method,
    )

    assert (
        scenario.power_quality_phase_allocation_method
        == power_quality_phase_allocation_method
    )


def test_scenario_defaults_arrival_window_to_charging_window_start():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        charging_window_start=time(17, 0),
        charging_window_end=time(6, 0),
    )

    assert scenario.arrival_window_start == time(17, 0)
    assert scenario.arrival_window_end == time(17, 0)
    assert scenario.arrival_mode == ArrivalMode.PROFILE
    assert scenario.arrival_profile_shape == ArrivalProfileShape.FRONT_LOADED
    assert scenario.departure_mode == DepartureMode.WINDOW_END
    assert scenario.session_dwell_minutes is None
    assert scenario.departure_time_spread_minutes == 0


def test_scenario_accepts_session_dwell_minutes_for_dwell_departures():
    scenario = Scenario(
        vehicles=12,
        daily_energy_per_vehicle=80.0,
        charger_count=6,
        charger_power=300.0,
        grid_capacity=1200.0,
        arrival_window_start=time(8, 0),
        arrival_window_end=time(12, 0),
        arrival_mode=ArrivalMode.RANDOM,
        departure_mode=DepartureMode.SESSION_DWELL,
        session_dwell_minutes=30,
    )

    assert scenario.arrival_mode == ArrivalMode.RANDOM
    assert scenario.departure_mode == DepartureMode.SESSION_DWELL
    assert scenario.session_dwell_minutes == 30


def test_scenario_accepts_aligned_departure_time_spread_minutes():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        departure_time_spread_minutes=45,
    )

    assert scenario.departure_time_spread_minutes == 45


def test_scenario_accepts_aligned_charger_service_waiting_tolerance_minutes():
    scenario = Scenario(
        vehicles=24,
        daily_energy_per_vehicle=80.0,
        charger_count=6,
        charger_power=300.0,
        grid_capacity=1200.0,
        charger_service_max_waiting_time_minutes=60,
    )

    assert scenario.charger_service_max_waiting_time_minutes == 60


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("vehicles", -1),
        ("daily_energy_per_vehicle", 0.0),
        ("daily_energy_per_vehicle", -1.0),
        ("charger_count", -1),
        ("charger_power", 0.0),
        ("charger_power", -1.0),
        ("grid_capacity", 0.0),
        ("grid_capacity", -1.0),
        ("transformer_capacity_kw", 0.0),
        ("transformer_capacity_kw", -1.0),
        ("feeder_count", 0),
        ("feeder_count", -1),
        ("feeder_capacity_kw", 0.0),
        ("feeder_capacity_kw", -1.0),
    ],
)
def test_scenario_rejects_non_positive_values(field_name, value):
    params = {
        "vehicles": 50,
        "daily_energy_per_vehicle": 150.0,
        "charger_count": 10,
        "charger_power": 150.0,
        "grid_capacity": 1000.0,
    }
    params[field_name] = value

    with pytest.raises(ValueError, match=f"{field_name} must be greater than zero"):
        Scenario(**params)


@pytest.mark.parametrize("field_name", ["vehicles", "charger_count"])
def test_scenario_rejects_zero_values_for_user_facing_construction(field_name):
    params = {
        "vehicles": 50,
        "daily_energy_per_vehicle": 150.0,
        "charger_count": 10,
        "charger_power": 150.0,
        "grid_capacity": 1000.0,
    }
    params[field_name] = 0

    with pytest.raises(ValueError, match=f"{field_name} must be greater than zero"):
        Scenario(**params)


def test_create_internal_scenario_allows_zero_vehicles():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
    )

    assert scenario.vehicles == 0
    assert scenario.charger_count == 10


def test_create_internal_scenario_allows_zero_vehicles_with_explicit_grid_asset_inputs():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        transformer_capacity_kw=1250.0,
        transformer_other_load_kw=120.0,
        feeder_count=2,
        feeder_capacity_kw=700.0,
        feeder_base_load_kw=30.0,
        feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CHARGER_COUNT,
    )

    assert scenario.vehicles == 0
    assert scenario.transformer_capacity_kw == 1250.0
    assert scenario.transformer_other_load_kw == 120.0
    assert scenario.feeder_count == 2
    assert scenario.feeder_capacity_kw == 700.0
    assert scenario.feeder_base_load_kw == 30.0
    assert (
        scenario.feeder_ev_allocation_method
        == FeederEVAllocationMethod.BY_CHARGER_COUNT
    )


def test_create_internal_scenario_allows_zero_chargers():
    scenario = create_internal_scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=0,
        charger_power=150.0,
        grid_capacity=1000.0,
    )

    assert scenario.vehicles == 50
    assert scenario.charger_count == 0


def test_create_internal_scenario_allows_zero_chargers_with_explicit_grid_asset_inputs():
    scenario = create_internal_scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=0,
        charger_power=150.0,
        grid_capacity=1000.0,
        transformer_capacity_kw=1250.0,
        transformer_other_load_kw=120.0,
        feeder_count=2,
        feeder_capacity_kw=700.0,
        feeder_base_load_kw=30.0,
        feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CHARGER_COUNT,
    )

    assert scenario.charger_count == 0
    assert scenario.transformer_capacity_kw == 1250.0
    assert scenario.transformer_other_load_kw == 120.0
    assert scenario.feeder_count == 2
    assert scenario.feeder_capacity_kw == 700.0
    assert scenario.feeder_base_load_kw == 30.0
    assert (
        scenario.feeder_ev_allocation_method
        == FeederEVAllocationMethod.BY_CHARGER_COUNT
    )


def test_create_internal_scenario_allows_zero_vehicles_and_zero_chargers():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=150.0,
        charger_count=0,
        charger_power=150.0,
        grid_capacity=1000.0,
    )

    assert scenario.vehicles == 0
    assert scenario.charger_count == 0


@pytest.mark.parametrize(
    ("field_name", "value"),
    [("vehicles", -1), ("charger_count", -1)],
)
def test_create_internal_scenario_rejects_negative_zero_supported_values(
    field_name,
    value,
):
    params = {
        "vehicles": 50,
        "daily_energy_per_vehicle": 150.0,
        "charger_count": 10,
        "charger_power": 150.0,
        "grid_capacity": 1000.0,
    }
    params[field_name] = value

    with pytest.raises(ValueError, match=f"{field_name} must be zero or greater"):
        create_internal_scenario(**params)


@pytest.mark.parametrize("feeder_count", [0, -1])
def test_create_internal_scenario_still_rejects_invalid_feeder_counts(feeder_count):
    with pytest.raises(ValueError, match="feeder_count must be greater than zero"):
        create_internal_scenario(
            vehicles=0,
            daily_energy_per_vehicle=150.0,
            charger_count=0,
            charger_power=150.0,
            grid_capacity=1000.0,
            feeder_count=feeder_count,
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("transformer_other_load_kw", -0.01),
        ("feeder_base_load_kw", -0.01),
    ],
)
def test_scenario_rejects_negative_grid_asset_background_loads(field_name, value):
    params = {
        "vehicles": 50,
        "daily_energy_per_vehicle": 150.0,
        "charger_count": 10,
        "charger_power": 150.0,
        "grid_capacity": 1000.0,
    }
    params[field_name] = value

    with pytest.raises(ValueError, match=f"{field_name} must be non-negative"):
        Scenario(**params)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("single_phase_charger_share_percent", -0.01),
        ("charger_harmonic_factor", -0.01),
    ],
)
def test_scenario_rejects_negative_power_quality_numeric_inputs(field_name, value):
    params = {
        "vehicles": 50,
        "daily_energy_per_vehicle": 150.0,
        "charger_count": 10,
        "charger_power": 150.0,
        "grid_capacity": 1000.0,
    }
    params[field_name] = value

    with pytest.raises(ValueError, match=f"{field_name} must be non-negative"):
        Scenario(**params)


def test_scenario_rejects_single_phase_charger_share_percent_above_100():
    with pytest.raises(
        ValueError,
        match="single_phase_charger_share_percent must be 100 or less",
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            single_phase_charger_share_percent=100.1,
        )


def test_scenario_rejects_negative_planning_margin_percent():
    with pytest.raises(
        ValueError, match="planning_margin_percent must be non-negative"
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            planning_margin_percent=-0.01,
        )


def test_scenario_rejects_negative_request_energy_variability_percent():
    with pytest.raises(
        ValueError,
        match="request_energy_variability_percent must be non-negative",
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            request_energy_variability_percent=-0.1,
        )


def test_scenario_rejects_request_energy_variability_percent_above_100():
    with pytest.raises(
        ValueError,
        match="request_energy_variability_percent must be 100 or less",
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            request_energy_variability_percent=100.1,
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "transformer_other_load_kw",
        "feeder_count",
        "feeder_base_load_kw",
    ],
)
def test_scenario_rejects_missing_required_grid_asset_numeric_values(field_name):
    params = {
        "vehicles": 50,
        "daily_energy_per_vehicle": 150.0,
        "charger_count": 10,
        "charger_power": 150.0,
        "grid_capacity": 1000.0,
    }
    params[field_name] = None

    with pytest.raises(ValueError, match=f"{field_name} is required"):
        Scenario(**params)


def test_scenario_rejects_missing_planning_margin_percent():
    with pytest.raises(ValueError, match="planning_margin_percent is required"):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            planning_margin_percent=None,
        )


def test_scenario_rejects_missing_request_energy_variability_percent():
    with pytest.raises(
        ValueError,
        match="request_energy_variability_percent is required",
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            request_energy_variability_percent=None,
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "single_phase_charger_share_percent",
        "charger_harmonic_factor",
    ],
)
def test_scenario_rejects_missing_power_quality_numeric_values(field_name):
    params = {
        "vehicles": 50,
        "daily_energy_per_vehicle": 150.0,
        "charger_count": 10,
        "charger_power": 150.0,
        "grid_capacity": 1000.0,
    }
    params[field_name] = None

    with pytest.raises(ValueError, match=f"{field_name} is required"):
        Scenario(**params)


@pytest.mark.parametrize(
    "field_name",
    [
        "single_phase_charger_share_percent",
        "charger_harmonic_factor",
    ],
)
def test_scenario_rejects_non_numeric_power_quality_values(field_name):
    params = {
        "vehicles": 50,
        "daily_energy_per_vehicle": 150.0,
        "charger_count": 10,
        "charger_power": 150.0,
        "grid_capacity": 1000.0,
    }
    params[field_name] = "invalid"

    with pytest.raises(TypeError, match=f"{field_name} must be numeric"):
        Scenario(**params)


def test_scenario_rejects_non_numeric_planning_margin_percent():
    with pytest.raises(
        TypeError, match="planning_margin_percent must be numeric"
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            planning_margin_percent="10.0",
        )


def test_scenario_rejects_non_numeric_request_energy_variability_percent():
    with pytest.raises(
        TypeError,
        match="request_energy_variability_percent must be numeric",
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            request_energy_variability_percent="10.0",
        )


def test_scenario_rejects_missing_feeder_ev_allocation_method():
    with pytest.raises(
        TypeError,
        match=(
            "feeder_ev_allocation_method must be a "
            "FeederEVAllocationMethod"
        ),
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            feeder_ev_allocation_method=None,
        )


def test_scenario_rejects_missing_configured_feeder_allocation_shares():
    with pytest.raises(
        ValueError,
        match=(
            "feeder_allocation_shares is required when "
            "feeder_ev_allocation_method is by_configured_share"
        ),
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            feeder_count=2,
            feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CONFIGURED_SHARE,
        )


def test_scenario_rejects_configured_feeder_allocation_shares_with_wrong_length():
    with pytest.raises(
        ValueError,
        match="feeder_allocation_shares length must match feeder_count",
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            feeder_count=3,
            feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CONFIGURED_SHARE,
            feeder_allocation_shares=[0.7, 0.3],
        )


def test_scenario_rejects_negative_configured_feeder_allocation_shares():
    with pytest.raises(
        ValueError,
        match="feeder_allocation_shares must be non-negative",
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            feeder_count=2,
            feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CONFIGURED_SHARE,
            feeder_allocation_shares=[0.7, -0.3],
        )


def test_scenario_rejects_zero_total_configured_feeder_allocation_shares():
    with pytest.raises(
        ValueError,
        match="feeder_allocation_shares total must be greater than zero",
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            feeder_count=2,
            feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CONFIGURED_SHARE,
            feeder_allocation_shares=[0.0, 0.0],
        )


def test_scenario_accepts_charging_windows_that_cross_midnight():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        charging_window_start=time(17, 0),
        charging_window_end=time(6, 0),
    )

    assert scenario.charging_window_start == time(17, 0)
    assert scenario.charging_window_end == time(6, 0)


def test_scenario_accepts_front_loaded_arrival_window_at_charging_window_start():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        charging_window_start=time(17, 0),
        charging_window_end=time(6, 0),
        arrival_window_start=time(17, 0),
        arrival_window_end=time(17, 0),
        arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
    )

    assert scenario.arrival_window_start == time(17, 0)
    assert scenario.arrival_window_end == time(17, 0)


def test_scenario_accepts_even_arrival_window_within_cross_midnight_charging_window():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        charging_window_start=time(17, 0),
        charging_window_end=time(6, 0),
        arrival_window_start=time(17, 0),
        arrival_window_end=time(20, 0),
        arrival_profile_shape=ArrivalProfileShape.EVEN,
    )

    assert scenario.arrival_window_start == time(17, 0)
    assert scenario.arrival_window_end == time(20, 0)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("charging_window_start", "17:00"),
        ("charging_window_end", "06:00"),
        ("arrival_window_start", "17:00"),
        ("arrival_window_end", "06:00"),
    ],
)
def test_scenario_rejects_non_time_charging_window_values(field_name, value):
    params = {
        "vehicles": 50,
        "daily_energy_per_vehicle": 150.0,
        "charger_count": 10,
        "charger_power": 150.0,
        "grid_capacity": 1000.0,
        "charging_window_start": time(17, 0),
        "charging_window_end": time(6, 0),
        "arrival_window_start": time(17, 0),
        "arrival_window_end": time(17, 0),
    }
    params[field_name] = value

    with pytest.raises(TypeError, match=f"{field_name} must be a datetime.time object"):
        Scenario(**params)


def test_scenario_rejects_partial_arrival_window_configuration():
    with pytest.raises(
        ValueError,
        match=(
            "arrival_window_start and arrival_window_end must both be provided "
            "when either is set"
        ),
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            charging_window_start=time(17, 0),
            charging_window_end=time(6, 0),
            arrival_window_start=time(17, 0),
        )


@pytest.mark.parametrize("field_name", ["arrival_window_start", "arrival_window_end"])
def test_scenario_rejects_arrival_window_values_not_on_15_minute_boundaries(
    field_name,
):
    params = {
        "vehicles": 50,
        "daily_energy_per_vehicle": 150.0,
        "charger_count": 10,
        "charger_power": 150.0,
        "grid_capacity": 1000.0,
        "charging_window_start": time(17, 0),
        "charging_window_end": time(6, 0),
        "arrival_window_start": time(17, 0),
        "arrival_window_end": time(20, 0),
    }
    params[field_name] = time(17, 10)

    with pytest.raises(
        ValueError,
        match=f"{field_name} must align to 15-minute timesteps",
    ):
        Scenario(**params)


def test_scenario_rejects_arrival_window_outside_charging_window():
    with pytest.raises(
        ValueError,
        match="vehicle-arrival window must fall within the configured charging-allowed window",
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            charging_window_start=time(17, 0),
            charging_window_end=time(6, 0),
            arrival_window_start=time(16, 0),
            arrival_window_end=time(18, 0),
            arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
        )


def test_scenario_rejects_arrival_window_with_invalid_order_inside_charging_window():
    with pytest.raises(
        ValueError,
        match="vehicle-arrival window must fall within the configured charging-allowed window",
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            charging_window_start=time(17, 0),
            charging_window_end=time(6, 0),
            arrival_window_start=time(5, 0),
            arrival_window_end=time(4, 0),
            arrival_profile_shape=ArrivalProfileShape.EVEN,
        )


def test_scenario_rejects_arrival_window_when_non_cross_midnight_window_is_incompatible():
    with pytest.raises(
        ValueError,
        match="vehicle-arrival window must fall within the configured charging-allowed window",
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(17, 0),
            arrival_window_start=time(16, 0),
            arrival_window_end=time(7, 0),
            arrival_profile_shape=ArrivalProfileShape.EVEN,
        )


def test_scenario_rejects_unsupported_arrival_profile_shape():
    with pytest.raises(
        TypeError,
        match="arrival_profile_shape must be an ArrivalProfileShape",
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            arrival_profile_shape="clustered",
        )


def test_scenario_rejects_unsupported_arrival_mode():
    with pytest.raises(
        TypeError,
        match="arrival_mode must be an ArrivalMode",
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            arrival_mode="random",
        )


def test_scenario_rejects_unsupported_departure_mode():
    with pytest.raises(
        TypeError,
        match="departure_mode must be a DepartureMode",
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            departure_mode="session_dwell",
        )


def test_scenario_rejects_unsupported_feeder_ev_allocation_method():
    with pytest.raises(
        TypeError,
        match=(
            "feeder_ev_allocation_method must be a "
            "FeederEVAllocationMethod"
        ),
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            feeder_ev_allocation_method="equal_share",
        )


def test_scenario_rejects_unsupported_power_quality_phase_allocation_method():
    with pytest.raises(
        TypeError,
        match=(
            "power_quality_phase_allocation_method must be a "
            "PowerQualityPhaseAllocationMethod"
        ),
    ):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            power_quality_phase_allocation_method="phase_a_heavy",
        )


def test_scenario_rejects_missing_session_dwell_minutes_for_dwell_departures():
    with pytest.raises(
        ValueError,
        match="session_dwell_minutes is required when departure_mode uses session dwell",
    ):
        Scenario(
            vehicles=12,
            daily_energy_per_vehicle=80.0,
            charger_count=6,
            charger_power=300.0,
            grid_capacity=1200.0,
            departure_mode=DepartureMode.SESSION_DWELL,
        )


@pytest.mark.parametrize("session_dwell_minutes", [0, -15, 22.5, 20])
def test_scenario_rejects_invalid_session_dwell_minutes(session_dwell_minutes):
    with pytest.raises(
        ValueError,
        match=(
            "session_dwell_minutes must be greater than zero|"
            "session_dwell_minutes must be a whole number of minutes|"
            "session_dwell_minutes must align to 15-minute timesteps"
        ),
    ):
        Scenario(
            vehicles=12,
            daily_energy_per_vehicle=80.0,
            charger_count=6,
            charger_power=300.0,
            grid_capacity=1200.0,
            departure_mode=DepartureMode.SESSION_DWELL,
            session_dwell_minutes=session_dwell_minutes,
        )


@pytest.mark.parametrize("departure_time_spread_minutes", [-15, 22.5, 20])
def test_scenario_rejects_invalid_departure_time_spread_minutes(
    departure_time_spread_minutes,
):
    with pytest.raises(
        ValueError,
        match=(
            "departure_time_spread_minutes must be non-negative|"
            "departure_time_spread_minutes must be a whole number of minutes|"
            "departure_time_spread_minutes must align to 15-minute timesteps"
        ),
    ):
        Scenario(
            vehicles=12,
            daily_energy_per_vehicle=80.0,
            charger_count=6,
            charger_power=300.0,
            grid_capacity=1200.0,
            departure_time_spread_minutes=departure_time_spread_minutes,
        )


@pytest.mark.parametrize(
    "charger_service_max_waiting_time_minutes",
    [-15, 22.5, 20],
)
def test_scenario_rejects_invalid_charger_service_waiting_tolerance_minutes(
    charger_service_max_waiting_time_minutes,
):
    with pytest.raises(
        ValueError,
        match=(
            "charger_service_max_waiting_time_minutes must be non-negative|"
            "charger_service_max_waiting_time_minutes must be a whole number of minutes|"
            "charger_service_max_waiting_time_minutes must align to 15-minute timesteps"
        ),
    ):
        Scenario(
            vehicles=24,
            daily_energy_per_vehicle=80.0,
            charger_count=6,
            charger_power=300.0,
            grid_capacity=1200.0,
            charger_service_max_waiting_time_minutes=(
                charger_service_max_waiting_time_minutes
            ),
        )


def test_scenario_rejects_non_enum_charging_strategy():
    with pytest.raises(TypeError, match="charging_strategy must be a ChargingStrategy"):
        Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            charging_strategy="Smart Charging",
        )


def test_scenario_is_immutable():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
    )

    with pytest.raises(FrozenInstanceError):
        scenario.vehicles = 60


def test_create_strategy_variants_returns_uncontrolled_and_smart_scenarios():
    base_scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        charging_window_start=time(17, 0),
        charging_window_end=time(6, 0),
        charging_strategy=ChargingStrategy.SMART,
    )

    uncontrolled, smart = create_strategy_variants(base_scenario)

    assert uncontrolled.charging_strategy == ChargingStrategy.UNCONTROLLED
    assert smart.charging_strategy == ChargingStrategy.SMART


def test_create_strategy_variants_preserves_all_other_scenario_inputs():
    base_scenario = Scenario(
        vehicles=120,
        daily_energy_per_vehicle=20.0,
        charger_count=40,
        charger_power=22.0,
        grid_capacity=500.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(17, 0),
    )

    uncontrolled, smart = create_strategy_variants(base_scenario)

    for field in fields(Scenario):
        if field.name == "charging_strategy":
            continue

        assert getattr(uncontrolled, field.name) == getattr(base_scenario, field.name)
        assert getattr(smart, field.name) == getattr(base_scenario, field.name)


def test_create_strategy_variants_returns_independent_scenario_objects():
    base_scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
    )

    uncontrolled, smart = create_strategy_variants(base_scenario)

    assert uncontrolled is not base_scenario
    assert smart is not base_scenario
    assert uncontrolled is not smart
    assert base_scenario.charging_strategy == ChargingStrategy.UNCONTROLLED


def test_replacing_one_strategy_variant_does_not_change_the_other_or_base():
    base_scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
    )
    uncontrolled, smart = create_strategy_variants(base_scenario)

    changed_uncontrolled = replace(uncontrolled, vehicles=60)

    assert changed_uncontrolled.vehicles == 60
    assert uncontrolled.vehicles == 50
    assert smart.vehicles == 50
    assert base_scenario.vehicles == 50


def test_duplicate_scenario_returns_independent_copy_with_same_values():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        charging_window_start=time(17, 0),
        charging_window_end=time(6, 0),
        charging_strategy=ChargingStrategy.SMART,
    )

    duplicate = duplicate_scenario(scenario)

    assert duplicate == scenario
    assert duplicate is not scenario


def test_duplicate_scenario_preserves_internal_zero_value_boundaries():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=150.0,
        charger_count=0,
        charger_power=150.0,
        grid_capacity=1000.0,
    )

    duplicate = duplicate_scenario(scenario)

    assert duplicate == scenario
    assert duplicate is not scenario


def test_replacing_duplicate_does_not_change_original_scenario():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
    )
    duplicate = duplicate_scenario(scenario)

    changed_duplicate = replace(duplicate, vehicles=60)

    assert changed_duplicate.vehicles == 60
    assert duplicate.vehicles == 50
    assert scenario.vehicles == 50


def test_scenario_serialization_round_trip_preserves_values():
    scenario = Scenario(
        vehicles=120,
        daily_energy_per_vehicle=20.0,
        charger_count=40,
        charger_power=22.0,
        grid_capacity=500.0,
        request_energy_variability_percent=12.5,
        transformer_capacity_kw=600.0,
        transformer_other_load_kw=100.0,
        feeder_count=2,
        feeder_capacity_kw=300.0,
        feeder_base_load_kw=40.0,
        feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CONFIGURED_SHARE,
        feeder_allocation_shares=[0.6, 0.4],
        single_phase_charger_share_percent=60.0,
        charger_harmonic_factor=1.4,
        power_quality_phase_allocation_method=(
            PowerQualityPhaseAllocationMethod.FRONT_LOADED_PHASE_A
        ),
        planning_margin_percent=15.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(17, 0),
        arrival_window_start=time(8, 0),
        arrival_window_end=time(9, 0),
        arrival_mode=ArrivalMode.RANDOM,
        arrival_profile_shape=ArrivalProfileShape.EVEN,
        departure_mode=DepartureMode.SESSION_DWELL,
        session_dwell_minutes=30,
        departure_time_spread_minutes=45,
        charger_service_max_waiting_time_minutes=60,
        charging_strategy=ChargingStrategy.SMART,
    )

    data = scenario_to_dict(scenario)
    restored_scenario = scenario_from_dict(data)

    assert data == {
        "vehicles": 120,
        "daily_energy_per_vehicle": 20.0,
        "charger_count": 40,
        "charger_power": 22.0,
        "grid_capacity": 500.0,
        "request_energy_variability_percent": 12.5,
        "transformer_capacity_kw": 600.0,
        "transformer_other_load_kw": 100.0,
        "feeder_count": 2,
        "feeder_capacity_kw": 300.0,
        "feeder_base_load_kw": 40.0,
        "feeder_ev_allocation_method": "by_configured_share",
        "feeder_allocation_shares": [0.6, 0.4],
        "single_phase_charger_share_percent": 60.0,
        "charger_harmonic_factor": 1.4,
        "power_quality_phase_allocation_method": "front_loaded_phase_a",
        "planning_margin_percent": 15.0,
        "charging_window_start": "08:00",
        "charging_window_end": "17:00",
        "arrival_window_start": "08:00",
        "arrival_window_end": "09:00",
        "arrival_mode": "random",
        "arrival_profile_shape": "even",
        "departure_mode": "session_dwell",
        "session_dwell_minutes": 30,
        "departure_time_spread_minutes": 45,
        "charger_service_max_waiting_time_minutes": 60,
        "charging_strategy": "Smart Charging",
    }
    assert restored_scenario == scenario


def test_scenario_deserialization_adds_backward_compatible_arrival_defaults():
    restored_scenario = scenario_from_dict(
        {
            "vehicles": 120,
            "daily_energy_per_vehicle": 20.0,
            "charger_count": 40,
            "charger_power": 22.0,
            "grid_capacity": 500.0,
            "planning_margin_percent": 15.0,
            "charging_window_start": "08:00",
            "charging_window_end": "17:00",
            "charging_strategy": "Smart Charging",
        }
    )

    assert restored_scenario.arrival_window_start == time(8, 0)
    assert restored_scenario.arrival_window_end == time(8, 0)
    assert restored_scenario.arrival_mode == ArrivalMode.PROFILE
    assert restored_scenario.arrival_profile_shape == ArrivalProfileShape.FRONT_LOADED
    assert restored_scenario.departure_mode == DepartureMode.WINDOW_END
    assert restored_scenario.session_dwell_minutes is None
    assert restored_scenario.request_energy_variability_percent == 0.0
    assert restored_scenario.departure_time_spread_minutes == 0
    assert restored_scenario.charger_service_max_waiting_time_minutes == 30
    assert restored_scenario.transformer_capacity_kw == 500.0
    assert restored_scenario.transformer_other_load_kw == 0.0
    assert restored_scenario.feeder_count == 1
    assert restored_scenario.feeder_capacity_kw == 500.0
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


def test_scenario_comparison_snapshot_stores_independent_scenario_data():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
    )

    snapshot = create_scenario_comparison_snapshot(scenario)

    assert snapshot["scenario_a"] == snapshot["scenario_b"]
    assert snapshot["scenario_a"] is not snapshot["scenario_b"]
    assert snapshot["scenario_a"]["planning_margin_percent"] == 10.0
    assert snapshot["scenario_b"]["planning_margin_percent"] == 10.0

    snapshot["scenario_b"]["vehicles"] = 60

    assert snapshot["scenario_a"]["vehicles"] == 50
    assert snapshot["scenario_b"]["vehicles"] == 60


def test_scenario_comparison_snapshot_defaults_builder_state_to_modified_copy():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
    )

    snapshot = create_scenario_comparison_snapshot(scenario)

    assert snapshot["comparison_source"] == COMPARISON_SOURCE_MODIFIED_COPY
    assert snapshot["selected_template"] is None
    assert snapshot["normalized_scenario_b"] == snapshot["scenario_b"]
    assert snapshot["normalized_scenario_b"] is not snapshot["scenario_b"]


def test_normalize_scenario_comparison_data_adds_legacy_builder_defaults():
    scenario_a = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
    )
    scenario_b = replace(
        scenario_a,
        vehicles=75,
        grid_capacity=1200.0,
    )

    normalized_data = normalize_scenario_comparison_data(
        {
            "scenario_a": scenario_to_dict(scenario_a),
            "scenario_b": scenario_to_dict(scenario_b),
        }
    )

    assert normalized_data["comparison_source"] == COMPARISON_SOURCE_MODIFIED_COPY
    assert normalized_data["selected_template"] is None
    assert normalized_data["normalized_scenario_b"] == normalized_data["scenario_b"]
    assert get_normalized_scenario_b_snapshot(normalized_data)["vehicles"] == 75


def test_template_comparison_source_uses_selected_template_for_normalized_scenario_b():
    scenario_a = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        planning_margin_percent=15.0,
        charging_strategy=ChargingStrategy.SMART,
    )
    workplace_preset = get_scenario_preset(WORKPLACE_CHARGING_PRESET_ID)

    normalized_data = normalize_scenario_comparison_data(
        {
            "scenario_a": scenario_to_dict(scenario_a),
            "scenario_b": scenario_to_dict(replace(scenario_a, vehicles=75)),
            "comparison_source": COMPARISON_SOURCE_TEMPLATE,
            "selected_template": WORKPLACE_CHARGING_PRESET_ID,
        }
    )

    assert normalized_data["scenario_b"]["vehicles"] == 75
    assert normalized_data["normalized_scenario_b"]["vehicles"] == 120
    assert normalized_data["normalized_scenario_b"]["charger_count"] == (
        workplace_preset.scenario.charger_count
    )
    assert normalized_data["normalized_scenario_b"]["charging_strategy"] == (
        ChargingStrategy.SMART.value
    )
    assert normalized_data["normalized_scenario_b"]["planning_margin_percent"] == 15.0
    assert get_normalized_scenario_b_snapshot(normalized_data)["vehicles"] == 120


def test_scenario_b_editable_fields_are_limited_to_phase_6_parameters():
    assert SCENARIO_B_EDITABLE_FIELDS == frozenset(
        {
            "vehicles",
            "charger_count",
            "charger_power",
            "grid_capacity",
        }
    )


def test_update_scenario_b_changes_only_explicitly_provided_fields():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        charging_window_start=time(17, 0),
        charging_window_end=time(6, 0),
        charging_strategy=ChargingStrategy.SMART,
    )

    updated_scenario = update_scenario_b(
        scenario,
        vehicles=75,
        grid_capacity=1200.0,
    )

    assert updated_scenario is not scenario
    assert updated_scenario.vehicles == 75
    assert updated_scenario.grid_capacity == 1200.0
    assert updated_scenario.charger_count == scenario.charger_count
    assert updated_scenario.charger_power == scenario.charger_power
    assert (
        updated_scenario.daily_energy_per_vehicle
        == scenario.daily_energy_per_vehicle
    )
    assert (
        updated_scenario.planning_margin_percent
        == scenario.planning_margin_percent
    )
    assert updated_scenario.charging_window_start == scenario.charging_window_start
    assert updated_scenario.charging_window_end == scenario.charging_window_end
    assert updated_scenario.arrival_window_start == scenario.arrival_window_start
    assert updated_scenario.arrival_window_end == scenario.arrival_window_end
    assert updated_scenario.arrival_profile_shape == scenario.arrival_profile_shape
    assert updated_scenario.charging_strategy == scenario.charging_strategy


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("vehicles", 0),
        ("charger_count", 0),
        ("charger_power", 0.0),
        ("grid_capacity", 0.0),
    ],
)
def test_update_scenario_b_reuses_scenario_validation(field_name, field_value):
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
    )

    with pytest.raises(ValueError, match=f"{field_name} must be greater than zero"):
        update_scenario_b(scenario, **{field_name: field_value})


def test_copy_scenario_with_updates_preserves_internal_zero_value_support():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=150.0,
        charger_count=0,
        charger_power=150.0,
        grid_capacity=1000.0,
    )

    copied = copy_scenario_with_updates(scenario, charging_strategy=ChargingStrategy.SMART)

    assert copied.vehicles == 0
    assert copied.charger_count == 0
    assert copied.charging_strategy == ChargingStrategy.SMART


def test_copy_scenario_with_updates_preserves_new_grid_asset_inputs():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=150.0,
        charger_count=0,
        charger_power=150.0,
        grid_capacity=1000.0,
        transformer_capacity_kw=1250.0,
        transformer_other_load_kw=100.0,
        feeder_count=2,
        feeder_capacity_kw=700.0,
        feeder_base_load_kw=30.0,
        feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CONFIGURED_SHARE,
        feeder_allocation_shares=[0.7, 0.3],
    )

    copied = copy_scenario_with_updates(
        scenario,
        charging_strategy=ChargingStrategy.SMART,
    )

    assert copied.transformer_capacity_kw == 1250.0
    assert copied.transformer_other_load_kw == 100.0
    assert copied.feeder_count == 2
    assert copied.feeder_capacity_kw == 700.0
    assert copied.feeder_base_load_kw == 30.0
    assert (
        copied.feeder_ev_allocation_method
        == FeederEVAllocationMethod.BY_CONFIGURED_SHARE
    )
    assert copied.feeder_allocation_shares == (0.7, 0.3)


def test_update_scenario_b_validates_explicitly_cleared_values():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
    )

    with pytest.raises(ValueError, match="vehicles is required"):
        update_scenario_b(scenario, vehicles=None)


def test_update_scenario_b_in_comparison_data_preserves_scenario_a_snapshot():
    scenario_a = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        charging_window_start=time(17, 0),
        charging_window_end=time(6, 0),
        charging_strategy=ChargingStrategy.SMART,
    )
    comparison_data = create_scenario_comparison_snapshot(scenario_a)

    updated_data = update_scenario_b_in_comparison_data(
        comparison_data,
        vehicles=75,
        charger_count=12,
        charger_power=180.0,
        grid_capacity=1200.0,
    )

    assert updated_data["scenario_a"] == comparison_data["scenario_a"]
    assert updated_data["scenario_a"] is not comparison_data["scenario_a"]
    assert updated_data["scenario_b"]["vehicles"] == 75
    assert updated_data["scenario_b"]["charger_count"] == 12
    assert updated_data["scenario_b"]["charger_power"] == 180.0
    assert updated_data["scenario_b"]["grid_capacity"] == 1200.0
    assert updated_data["scenario_b"]["planning_margin_percent"] == 10.0
    assert updated_data["scenario_b"]["charging_window_start"] == "17:00"
    assert updated_data["scenario_b"]["charging_window_end"] == "06:00"
    assert updated_data["scenario_b"]["arrival_window_start"] == "17:00"
    assert updated_data["scenario_b"]["arrival_window_end"] == "17:00"
    assert updated_data["scenario_b"]["arrival_mode"] == "profile"
    assert updated_data["scenario_b"]["arrival_profile_shape"] == "front_loaded"
    assert updated_data["scenario_b"]["departure_mode"] == "window_end"
    assert updated_data["scenario_b"]["session_dwell_minutes"] is None
    assert updated_data["scenario_b"]["request_energy_variability_percent"] == 0.0
    assert updated_data["scenario_b"]["departure_time_spread_minutes"] == 0
    assert (
        updated_data["scenario_b"]["charger_service_max_waiting_time_minutes"]
        == 30
    )
    assert updated_data["scenario_b"]["single_phase_charger_share_percent"] == 0.0
    assert updated_data["scenario_b"]["charger_harmonic_factor"] == 1.0
    assert (
        updated_data["scenario_b"]["power_quality_phase_allocation_method"]
        == "balanced_round_robin"
    )
    assert updated_data["scenario_b"]["charging_strategy"] == "Smart Charging"
    assert updated_data["comparison_source"] == COMPARISON_SOURCE_MODIFIED_COPY
    assert updated_data["selected_template"] is None
    assert updated_data["normalized_scenario_b"] == updated_data["scenario_b"]


def test_update_scenario_a_in_comparison_data_rebases_comparison_on_current_scenario_a():
    original_scenario_a = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
        charging_strategy=ChargingStrategy.SMART,
    )
    rebased_scenario_a = replace(
        original_scenario_a,
        charging_strategy=ChargingStrategy.UNCONTROLLED,
    )
    comparison_data = update_scenario_b_in_comparison_data(
        create_scenario_comparison_snapshot(original_scenario_a),
        vehicles=75,
        grid_capacity=1200.0,
    )

    rebased_data = update_scenario_a_in_comparison_data(
        comparison_data,
        rebased_scenario_a,
    )

    assert rebased_data["scenario_a"]["charging_strategy"] == "Uncontrolled"
    assert rebased_data["scenario_b"]["vehicles"] == 75
    assert rebased_data["scenario_b"]["grid_capacity"] == 1200.0


def test_summarize_scenario_assumption_differences_reports_changed_fields():
    scenario_a = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
    )
    comparison_data = update_scenario_b_in_comparison_data(
        create_scenario_comparison_snapshot(scenario_a),
        vehicles=75,
        grid_capacity=1200.0,
    )

    summaries = summarize_scenario_assumption_differences(comparison_data)

    assert summaries == (
        "Number of vehicles: 50 -> 75",
        "Grid connection capacity: 1,000.0 kW -> 1,200.0 kW",
    )


def test_summarize_scenario_assumption_differences_reports_matching_scenarios():
    scenario = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
    )

    summaries = summarize_scenario_assumption_differences(
        create_scenario_comparison_snapshot(scenario)
    )

    assert summaries == ("Comparison scenario matches the current scenario.",)


def test_summarize_scenario_assumption_change_overview_groups_changes():
    scenario_a = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
    )
    comparison_data = update_scenario_b_in_comparison_data(
        create_scenario_comparison_snapshot(scenario_a),
        vehicles=75,
        charger_count=12,
        grid_capacity=1200.0,
    )

    overview = summarize_scenario_assumption_change_overview(comparison_data)

    assert overview["change_count"] == 3
    assert overview["category_counts"] == (
        ("Fleet & Demand", 1),
        ("Charging Infrastructure", 1),
        ("Grid & Capacity", 1),
    )
    assert overview["highlights"] == (
        "Number of vehicles: 50 -> 75",
        "Number of chargers: 10 -> 12",
        "Grid connection capacity: 1,000.0 kW -> 1,200.0 kW",
    )
    assert overview["all_summaries"] == overview["highlights"]


def test_summarize_scenario_assumption_differences_hides_electricity_price():
    scenario_a = Scenario(
        vehicles=50,
        daily_energy_per_vehicle=150.0,
        charger_count=10,
        charger_power=150.0,
        grid_capacity=1000.0,
    )
    comparison_data = create_scenario_comparison_snapshot(scenario_a)
    comparison_data["scenario_b"]["electricity_price"] = 0.23

    summaries = summarize_scenario_assumption_differences(comparison_data)

    assert summaries == ("Comparison scenario matches the current scenario.",)
