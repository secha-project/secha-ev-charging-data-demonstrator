from tests.helpers import *  # noqa: F401,F403

def test_dashboard_creates_active_scenario_from_strategy_selection():
    scenario = create_active_scenario(ChargingStrategy.SMART.value)

    assert scenario.charging_strategy == ChargingStrategy.SMART

def test_dashboard_creates_active_scenario_state_from_selected_preset():
    active_scenario_state = create_active_scenario_state(
        PUBLIC_FAST_CHARGING_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    active_scenario = active_scenario_from_state(active_scenario_state)

    assert active_scenario_state["schema_version"] == (
        ACTIVE_SCENARIO_STATE_SCHEMA_VERSION
    )
    assert active_scenario_state["preset"]["preset_id"] == (
        PUBLIC_FAST_CHARGING_PRESET_ID
    )
    assert active_scenario_state["preset"]["is_modified"] is True
    assert active_scenario_state["metadata"]["name"] == "Public Fast Charging"
    assert active_scenario.charging_strategy == ChargingStrategy.SMART
    assert active_scenario.vehicles == 48
    assert active_scenario.daily_energy_per_vehicle == 50.0
    assert active_scenario.charger_count == 6
    assert active_scenario.charger_power == 300.0
    assert active_scenario.grid_capacity == 1200.0
    assert active_scenario.arrival_mode == ArrivalMode.RANDOM
    assert active_scenario.departure_mode == DepartureMode.SESSION_DWELL
    assert active_scenario.session_dwell_minutes == 15
    assert active_scenario_state["parameters"]["single_phase_charger_share_percent"] == 0.0
    assert active_scenario_state["parameters"]["charger_harmonic_factor"] == 1.0
    assert (
        active_scenario_state["parameters"]["power_quality_phase_allocation_method"]
        == "balanced_round_robin"
    )

def test_dashboard_active_scenario_state_switching_updates_selected_preset():
    heavy_duty_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.UNCONTROLLED.value,
    )
    public_fast_charging_state = create_active_scenario_state(
        PUBLIC_FAST_CHARGING_PRESET_ID,
        ChargingStrategy.UNCONTROLLED.value,
    )

    assert heavy_duty_state["preset"]["preset_id"] == DEFAULT_SCENARIO_PRESET_ID
    assert heavy_duty_state["preset"]["is_modified"] is False
    assert (
        public_fast_charging_state["preset"]["preset_id"]
        == PUBLIC_FAST_CHARGING_PRESET_ID
    )
    assert public_fast_charging_state["preset"]["is_modified"] is False
    assert heavy_duty_state != public_fast_charging_state

def test_dashboard_creates_workplace_active_scenario_from_selected_preset():
    active_scenario_state = create_active_scenario_state(
        WORKPLACE_CHARGING_PRESET_ID,
        ChargingStrategy.UNCONTROLLED.value,
    )
    active_scenario = active_scenario_from_state(active_scenario_state)

    assert active_scenario_state["preset"]["preset_id"] == WORKPLACE_CHARGING_PRESET_ID
    assert active_scenario_state["preset"]["is_modified"] is False
    assert active_scenario.vehicles == 120
    assert active_scenario.daily_energy_per_vehicle == 20.0
    assert active_scenario.charger_count == 40
    assert active_scenario.charger_power == 22.0
    assert active_scenario.grid_capacity == 500.0
    assert active_scenario.arrival_mode == ArrivalMode.PROFILE

def test_dashboard_public_fast_charging_selection_changes_simulation_inputs():
    heavy_duty_scenario = create_active_scenario(
        ChargingStrategy.UNCONTROLLED.value,
        preset_id=DEFAULT_SCENARIO_PRESET_ID,
    )
    public_fast_charging_scenario = create_active_scenario(
        ChargingStrategy.UNCONTROLLED.value,
        preset_id=PUBLIC_FAST_CHARGING_PRESET_ID,
    )

    assert public_fast_charging_scenario.vehicles != heavy_duty_scenario.vehicles
    assert (
        public_fast_charging_scenario.daily_energy_per_vehicle
        != heavy_duty_scenario.daily_energy_per_vehicle
    )
    assert (
        public_fast_charging_scenario.charger_power
        != heavy_duty_scenario.charger_power
    )
    assert public_fast_charging_scenario.arrival_mode == ArrivalMode.RANDOM
    assert (
        public_fast_charging_scenario.departure_mode
        == DepartureMode.SESSION_DWELL
    )

def test_dashboard_single_scenario_run_state_uses_selected_public_fast_charging_preset():
    active_scenario_state = create_active_scenario_state(
        PUBLIC_FAST_CHARGING_PRESET_ID,
        ChargingStrategy.UNCONTROLLED.value,
    )

    simulation_results_state, metrics_state = create_single_scenario_run_state(
        active_scenario_state
    )

    active_result = simulation_result_from_dict(simulation_results_state["active"])
    active_metrics = metrics_from_dict(metrics_state["active"])

    assert active_result.daily_energy_demand == 2400.0
    assert active_result.configured_connection_capacity_kw == 1200.0
    assert len(active_result.delivered_load_profile_kw) == len(get_time_labels())
    assert active_result.charging_requests == []
    assert active_metrics.total_daily_energy == 2400.0
    assert active_metrics.total_daily_energy == active_result.daily_energy_demand

def test_dashboard_single_scenario_run_state_changes_when_selected_preset_changes():
    heavy_duty_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.UNCONTROLLED.value,
    )
    public_fast_charging_state = create_active_scenario_state(
        PUBLIC_FAST_CHARGING_PRESET_ID,
        ChargingStrategy.UNCONTROLLED.value,
    )

    heavy_duty_results_state, heavy_duty_metrics_state = create_single_scenario_run_state(
        heavy_duty_state
    )
    public_fast_results_state, public_fast_metrics_state = create_single_scenario_run_state(
        public_fast_charging_state
    )

    heavy_duty_result = simulation_result_from_dict(heavy_duty_results_state["active"])
    public_fast_result = simulation_result_from_dict(public_fast_results_state["active"])
    heavy_duty_metrics = metrics_from_dict(heavy_duty_metrics_state["active"])
    public_fast_metrics = metrics_from_dict(public_fast_metrics_state["active"])

    assert heavy_duty_result.daily_energy_demand == 7500.0
    assert public_fast_result.daily_energy_demand == 2400.0
    assert heavy_duty_metrics.total_daily_energy == 7500.0
    assert public_fast_metrics.total_daily_energy == 2400.0
    assert (
        heavy_duty_result.configured_connection_capacity_kw
        != public_fast_result.configured_connection_capacity_kw
    )
    assert (
        heavy_duty_result.delivered_load_profile_kw
        != public_fast_result.delivered_load_profile_kw
    )

def test_dashboard_single_scenario_run_state_keeps_charger_recommendation_available_for_default_preset():
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.UNCONTROLLED.value,
    )
    active_scenario = active_scenario_from_state(active_scenario_state)

    _simulation_results_state, metrics_state = create_single_scenario_run_state(
        active_scenario_state
    )
    active_metrics = metrics_from_dict(metrics_state["active"])

    visible_text = " ".join(
        _collect_text(render_charger_planning_status(active_metrics, active_scenario))
    )

    assert "Recommendation unavailable" not in visible_text
    assert "Add chargers" in visible_text

def test_dashboard_renders_heavy_duty_scenario_preset_details():
    visible_text = " ".join(
        _collect_text(render_scenario_preset_details(DEFAULT_SCENARIO_PRESET_ID))
    )

    assert "Heavy-duty preset" not in visible_text
    assert "Depot-style heavy-duty charging scenario used as the MVP reference configuration." in visible_text
    assert (
        "Fleet vehicles begin arriving near the start of the charging-allowed window."
        in visible_text
    )
    assert "About this scenario" not in visible_text
    assert "Key Assumptions" not in visible_text
    assert "Number of vehicles: 50" not in visible_text

def test_dashboard_switches_scenario_preset_details_when_selection_changes():
    heavy_duty_text = " ".join(
        _collect_text(render_scenario_preset_details(DEFAULT_SCENARIO_PRESET_ID))
    )
    public_fast_charging_text = " ".join(
        _collect_text(render_scenario_preset_details(PUBLIC_FAST_CHARGING_PRESET_ID))
    )

    assert "Depot-style heavy-duty charging scenario used as the MVP reference configuration." in heavy_duty_text
    assert "High-power public charging hub scenario for short-stay customer charging sessions." in public_fast_charging_text
    assert "Higher-turnover charging sessions than depot or workplace charging." in public_fast_charging_text
    assert "Energy demand per session: 50 kWh" not in public_fast_charging_text
    assert "Typical dwell time: 15 minutes" not in public_fast_charging_text
    assert "17:00 - 06:00" not in public_fast_charging_text

def test_dashboard_shared_single_scenario_views_use_scenario_neutral_wording():
    for preset_id in (
        DEFAULT_SCENARIO_PRESET_ID,
        PUBLIC_FAST_CHARGING_PRESET_ID,
        WORKPLACE_CHARGING_PRESET_ID,
    ):
        scenario = get_scenario_preset(preset_id).scenario
        assert scenario is not None

        (
            _simulation_result,
            _metrics,
            cards_text,
            charger_availability_cards_text,
            status_text,
            charger_planning_status_text,
            capacity_vs_load_figure,
            load_profile_figure,
        ) = _build_single_scenario_dashboard_slice(scenario)
        visible_text = " ".join(
            cards_text
            + charger_availability_cards_text
            + status_text
            + charger_planning_status_text
        )

        assert "Simulated Peak Load" in visible_text
        assert "Peak Charger Utilization" in visible_text
        assert "Planner-facing rule" not in visible_text
        assert "Depot-style heavy-duty charging scenario" not in visible_text
        assert "High-power public charging hub scenario" not in visible_text
        assert "Daytime workplace charging scenario" not in visible_text
        assert "17:00 - 06:00" not in visible_text
        assert "30-minute dwell time" not in visible_text
        assert capacity_vs_load_figure.layout.title.text is None
        assert load_profile_figure.layout.title.text == "Charging Load Profile"

def test_dashboard_shared_scenario_ab_views_use_scenario_neutral_wording():
    active_scenario_state = create_active_scenario_state(
        PUBLIC_FAST_CHARGING_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = create_scenario_comparison_state(active_scenario_state)
    comparison_state = update_scenario_comparison_state_for_b_edits(
        comparison_state,
        vehicles=30,
        charger_count=8,
        charger_power=300.0,
        grid_capacity=1500.0,
    )
    _results_state, metrics_state, difference_state = (
        create_scenario_ab_comparison_run_state(comparison_state)
    )

    metrics_a = metrics_from_dict(metrics_state["scenario_a"])
    metrics_b = metrics_from_dict(metrics_state["scenario_b"])
    difference_metrics = scenario_comparison_metrics_from_dict(difference_state)

    comparison_text = " ".join(
        _collect_text(
            render_scenario_ab_comparison_table(
                metrics_a,
                metrics_b,
                difference_metrics,
            )
        )
    )
    availability_text = " ".join(
        _collect_text(
            render_scenario_ab_charger_availability_table(
                metrics_a,
                metrics_b,
                difference_metrics,
            )
        )
    )
    visible_text = f"{comparison_text} {availability_text}"

    assert "Scenario A" in visible_text
    assert "Scenario B" in visible_text
    assert "Peak load (kW)" in visible_text
    assert "Average charger utilization (%)" in visible_text
    assert "Primary constraint reason" in visible_text
    assert "Depot-style heavy-duty charging scenario" not in visible_text
    assert "High-power public charging hub scenario" not in visible_text
    assert "Daytime workplace charging scenario" not in visible_text

def test_dashboard_creates_serializable_comparison_state_from_current_inputs():
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = create_scenario_comparison_state(active_scenario_state)

    assert comparison_state["comparison_source"] == COMPARISON_SOURCE_MODIFIED_COPY
    assert comparison_state["selected_template"] is None
    assert comparison_state["scenario_a"] == comparison_state["scenario_b"]
    assert comparison_state["scenario_a"] is not comparison_state["scenario_b"]
    assert comparison_state["normalized_scenario_b"] == comparison_state["scenario_b"]
    assert comparison_state["scenario_a"]["charging_strategy"] == "Smart Charging"
    assert "electricity_price" not in comparison_state["scenario_a"]

def test_dashboard_comparison_state_uses_selected_public_fast_charging_preset():
    active_scenario_state = create_active_scenario_state(
        PUBLIC_FAST_CHARGING_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = create_scenario_comparison_state(active_scenario_state)

    assert comparison_state["scenario_a"]["vehicles"] == 48
    assert comparison_state["scenario_a"]["daily_energy_per_vehicle"] == 50.0
    assert comparison_state["scenario_a"]["charger_count"] == 6
    assert comparison_state["scenario_a"]["arrival_mode"] == "random"
    assert comparison_state["scenario_a"]["arrival_profile_shape"] == "mid_peak"
    assert comparison_state["scenario_a"]["departure_mode"] == "session_dwell"
    assert comparison_state["scenario_a"]["session_dwell_minutes"] == 15
    assert comparison_state["comparison_source"] == COMPARISON_SOURCE_MODIFIED_COPY
    assert comparison_state["scenario_b"] == comparison_state["scenario_a"]
    assert comparison_state["normalized_scenario_b"] == comparison_state["scenario_b"]

def test_dashboard_updates_only_scenario_b_comparison_state_from_edit_values():
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = create_scenario_comparison_state(active_scenario_state)

    updated_state = update_scenario_comparison_state_for_b_edits(
        comparison_state,
        vehicles=75,
        charger_count=12,
        charger_power=180.0,
        grid_capacity=1200.0,
    )

    assert updated_state["scenario_a"] == comparison_state["scenario_a"]
    assert updated_state["scenario_b"]["vehicles"] == 75
    assert updated_state["scenario_b"]["charger_count"] == 12
    assert updated_state["scenario_b"]["charger_power"] == 180.0
    assert updated_state["scenario_b"]["grid_capacity"] == 1200.0
    assert updated_state["scenario_b"]["charging_strategy"] == "Smart Charging"
    assert updated_state["comparison_source"] == COMPARISON_SOURCE_MODIFIED_COPY
    assert updated_state["selected_template"] is None
    assert updated_state["normalized_scenario_b"] == updated_state["scenario_b"]

def test_dashboard_creates_template_comparison_state_with_shared_settings_from_scenario_a():
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )

    comparison_state = create_scenario_comparison_state(
        active_scenario_state,
        comparison_source=COMPARISON_SOURCE_TEMPLATE,
        selected_template=WORKPLACE_CHARGING_PRESET_ID,
    )

    assert comparison_state["comparison_source"] == COMPARISON_SOURCE_TEMPLATE
    assert comparison_state["selected_template"] == WORKPLACE_CHARGING_PRESET_ID
    assert comparison_state["normalized_scenario_b"]["vehicles"] == 120
    assert comparison_state["normalized_scenario_b"]["charger_count"] == 40
    assert comparison_state["normalized_scenario_b"]["charging_strategy"] == (
        ChargingStrategy.SMART.value
    )

def test_dashboard_creates_modified_copy_comparison_state_from_fully_edited_active_scenario():
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.UNCONTROLLED.value,
    )
    edited_active_scenario_state = update_active_scenario_parameters(
        active_scenario_state,
        parameter_updates={
            "vehicles": 72,
            "grid_capacity": 1350.0,
            "request_energy_variability_percent": 12.0,
            "feeder_count": 3,
        },
    )

    comparison_state = create_scenario_comparison_state(edited_active_scenario_state)

    assert comparison_state["scenario_a"]["vehicles"] == 72
    assert comparison_state["scenario_a"]["grid_capacity"] == 1350.0
    assert comparison_state["scenario_a"]["request_energy_variability_percent"] == 12.0
    assert comparison_state["scenario_a"]["feeder_count"] == 3
    assert comparison_state["scenario_b"] == comparison_state["scenario_a"]
    assert comparison_state["normalized_scenario_b"] == comparison_state["scenario_a"]

def test_dashboard_rebases_modified_copy_comparison_state_onto_current_edited_scenario_a():
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    initial_comparison_state = create_scenario_comparison_state(active_scenario_state)
    edited_comparison_state = update_scenario_comparison_state_for_b_edits(
        initial_comparison_state,
        vehicles=75,
        charger_count=12,
        charger_power=180.0,
        grid_capacity=1200.0,
    )
    rebased_active_scenario_state = update_active_scenario_parameters(
        active_scenario_state,
        parameter_updates={
            "vehicles": 58,
            "daily_energy_per_vehicle": 165.0,
            "grid_capacity": 1100.0,
        },
    )

    rebased_comparison_state = update_scenario_a_in_comparison_data(
        edited_comparison_state,
        active_scenario_from_state(rebased_active_scenario_state),
    )

    assert rebased_comparison_state["scenario_a"]["vehicles"] == 58
    assert rebased_comparison_state["scenario_a"]["daily_energy_per_vehicle"] == 165.0
    assert rebased_comparison_state["scenario_a"]["grid_capacity"] == 1100.0
    assert rebased_comparison_state["scenario_b"]["vehicles"] == 75
    assert rebased_comparison_state["scenario_b"]["charger_count"] == 12
    assert rebased_comparison_state["scenario_b"]["charger_power"] == 180.0
    assert rebased_comparison_state["scenario_b"]["grid_capacity"] == 1200.0

def test_dashboard_rebases_template_comparison_state_onto_current_edited_scenario_a():
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    template_comparison_state = create_scenario_comparison_state(
        active_scenario_state,
        comparison_source=COMPARISON_SOURCE_TEMPLATE,
        selected_template=WORKPLACE_CHARGING_PRESET_ID,
    )
    rebased_active_scenario_state = update_active_scenario_parameters(
        active_scenario_state,
        parameter_updates={
            "vehicles": 58,
            "planning_margin_percent": 18.0,
            "charging_strategy": ChargingStrategy.UNCONTROLLED.value,
        },
    )

    rebased_comparison_state = update_scenario_a_in_comparison_data(
        template_comparison_state,
        active_scenario_from_state(rebased_active_scenario_state),
    )

    assert rebased_comparison_state["scenario_a"]["vehicles"] == 58
    assert rebased_comparison_state["comparison_source"] == COMPARISON_SOURCE_TEMPLATE
    assert rebased_comparison_state["selected_template"] == WORKPLACE_CHARGING_PRESET_ID
    assert rebased_comparison_state["scenario_b"]["vehicles"] == 120
    assert rebased_comparison_state["normalized_scenario_b"]["vehicles"] == 120
    assert rebased_comparison_state["normalized_scenario_b"]["planning_margin_percent"] == 18.0
    assert rebased_comparison_state["normalized_scenario_b"]["charging_strategy"] == (
        ChargingStrategy.UNCONTROLLED.value
    )

def test_dashboard_resolves_scenario_ab_labels_for_modified_copy_results():
    active_scenario_state = create_active_scenario_state(
        WORKPLACE_CHARGING_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = create_scenario_comparison_state(active_scenario_state)

    assert _resolve_scenario_ab_display_labels(
        active_scenario_state,
        comparison_state,
    ) == ("Workplace Charging", "Workplace Charging (Modified)")

def test_dashboard_resolves_scenario_ab_labels_for_modified_active_template_results():
    active_scenario_state = create_active_scenario_state(
        WORKPLACE_CHARGING_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    edited_active_scenario_state = update_active_scenario_parameters(
        active_scenario_state,
        parameter_updates={"vehicles": 144},
    )
    comparison_state = create_scenario_comparison_state(
        edited_active_scenario_state,
        comparison_source=COMPARISON_SOURCE_TEMPLATE,
        selected_template=PUBLIC_FAST_CHARGING_PRESET_ID,
    )

    assert _resolve_scenario_ab_display_labels(
        edited_active_scenario_state,
        comparison_state,
    ) == ("Workplace Charging (Modified)", "Public Fast Charging")

def test_dashboard_resolves_scenario_ab_labels_for_template_results():
    active_scenario_state = create_active_scenario_state(
        WORKPLACE_CHARGING_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = create_scenario_comparison_state(
        active_scenario_state,
        comparison_source=COMPARISON_SOURCE_TEMPLATE,
        selected_template=PUBLIC_FAST_CHARGING_PRESET_ID,
    )

    assert _resolve_scenario_ab_display_labels(
        active_scenario_state,
        comparison_state,
    ) == ("Workplace Charging (Modified)", "Public Fast Charging")

def test_dashboard_resolves_scenario_ab_labels_for_unknown_preset_fallback():
    active_scenario_state = {
        "preset_id": "unknown-preset",
    }

    assert _resolve_scenario_ab_display_labels(
        active_scenario_state,
        None,
    ) == ("Current Scenario", "Comparison Scenario")

def test_dashboard_ab_results_state_supports_legacy_comparison_store_shape():
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = create_scenario_comparison_state(active_scenario_state)
    legacy_comparison_state = {
        "scenario_a": comparison_state["scenario_a"],
        "scenario_b": {
            **comparison_state["scenario_b"],
            "vehicles": 75,
        },
    }

    results_state = create_scenario_ab_simulation_results_state(legacy_comparison_state)

    result_b = simulation_result_from_dict(results_state["scenario_b"])

    assert len(result_b.charging_requests) == 75

def test_dashboard_ab_run_state_uses_normalized_template_scenario_b():
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = create_scenario_comparison_state(active_scenario_state)
    comparison_state["comparison_source"] = COMPARISON_SOURCE_TEMPLATE
    comparison_state["selected_template"] = WORKPLACE_CHARGING_PRESET_ID
    comparison_state["scenario_b"]["vehicles"] = 75

    results_state, metrics_state, _difference_metrics_state = (
        create_scenario_ab_comparison_run_state(comparison_state)
    )

    result_b = simulation_result_from_dict(results_state["scenario_b"])
    metrics_b = metrics_from_dict(metrics_state["scenario_b"])

    assert result_b.daily_energy_demand == 2400.0
    assert metrics_b.total_daily_energy == 2400.0

def test_dashboard_creates_serializable_ab_simulation_results_from_stored_scenarios():
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = create_scenario_comparison_state(active_scenario_state)
    comparison_state["scenario_b"]["vehicles"] = 75

    results_state = create_scenario_ab_simulation_results_state(comparison_state)

    result_a = simulation_result_from_dict(results_state["scenario_a"])
    result_b = simulation_result_from_dict(results_state["scenario_b"])

    assert isinstance(result_a, SimulationResult)
    assert isinstance(result_b, SimulationResult)
    assert result_a is not result_b
    assert result_a.daily_energy_demand != result_b.daily_energy_demand
    assert len(result_a.charging_requests) == 50
    assert len(result_b.charging_requests) == 75
    assert sum(result_a.arrivals_count_by_timestep) == 50
    assert sum(result_b.arrivals_count_by_timestep) == 75
    assert len(result_a.waiting_vehicle_count_by_timestep) == len(
        result_a.delivered_load_profile_kw
    )
    assert len(result_b.waiting_vehicle_count_by_timestep) == len(
        result_b.delivered_load_profile_kw
    )
    assert set(results_state) == {"scenario_a", "scenario_b"}

def test_dashboard_creates_serializable_ab_results_for_selected_public_fast_charging_preset():
    active_scenario_state = create_active_scenario_state(
        PUBLIC_FAST_CHARGING_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = create_scenario_comparison_state(active_scenario_state)
    comparison_state["scenario_b"]["vehicles"] = 30

    results_state = create_scenario_ab_simulation_results_state(comparison_state)

    result_a = simulation_result_from_dict(results_state["scenario_a"])
    result_b = simulation_result_from_dict(results_state["scenario_b"])

    assert result_a.daily_energy_demand == 2400.0
    assert result_b.daily_energy_demand == 1500.0
    assert len(result_a.charging_requests) == 48
    assert len(result_b.charging_requests) == 30
    assert {
        (request.departure_timestep - request.arrival_timestep) % 96
        for request in result_a.charging_requests
    } == {1, 2, 3}

def test_dashboard_creates_serializable_ab_results_and_metrics_from_stored_scenarios():
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = create_scenario_comparison_state(active_scenario_state)
    comparison_state["scenario_b"]["vehicles"] = 75

    (
        results_state,
        metrics_state,
        difference_metrics_state,
    ) = create_scenario_ab_comparison_run_state(comparison_state)

    result_a = simulation_result_from_dict(results_state["scenario_a"])
    result_b = simulation_result_from_dict(results_state["scenario_b"])
    metrics_a = metrics_from_dict(metrics_state["scenario_a"])
    metrics_b = metrics_from_dict(metrics_state["scenario_b"])
    difference_metrics = scenario_comparison_metrics_from_dict(
        difference_metrics_state
    )

    assert isinstance(result_a, SimulationResult)
    assert isinstance(result_b, SimulationResult)
    assert isinstance(metrics_a, Metrics)
    assert isinstance(metrics_b, Metrics)
    assert isinstance(difference_metrics, ScenarioComparisonMetrics)
    assert metrics_a.total_daily_energy == result_a.daily_energy_demand
    assert metrics_b.total_daily_energy == result_b.daily_energy_demand
    assert metrics_a is not metrics_b
    assert metrics_a.total_daily_energy != metrics_b.total_daily_energy
    assert difference_metrics.peak_load_difference_kw == (
        metrics_b.peak_load - metrics_a.peak_load
    )
    assert metrics_state["scenario_a"]["average_charger_utilization_percent"] == (
        metrics_a.average_charger_utilization_percent
    )
    assert metrics_state["scenario_b"]["peak_occupied_charger_count"] == (
        metrics_b.peak_occupied_charger_count
    )
    assert metrics_state["scenario_a"]["queue_present_indicator"] == (
        metrics_a.queue_present_indicator
    )
    assert metrics_state["scenario_b"]["vehicles_not_started_count"] == (
        metrics_b.vehicles_not_started_count
    )
    assert metrics_state["scenario_a"]["required_charger_count"] == (
        metrics_a.required_charger_count
    )
    assert metrics_state["scenario_b"]["additional_chargers_required"] == (
        metrics_b.additional_chargers_required
    )
    assert metrics_state["scenario_a"]["primary_constraint_reason"] == (
        metrics_a.primary_constraint_reason
    )
    assert metrics_state["scenario_b"]["occupied_charger_count_by_timestep"] == (
        metrics_b.occupied_charger_count_by_timestep
    )
    assert metrics_state["scenario_a"]["waiting_vehicle_count_by_timestep"] == (
        metrics_a.waiting_vehicle_count_by_timestep
    )
    assert difference_metrics.average_occupied_charger_count_difference == pytest.approx(
        metrics_b.average_occupied_charger_count
        - metrics_a.average_occupied_charger_count
    )
    assert difference_metrics.maximum_queue_length_difference == (
        metrics_b.maximum_queue_length - metrics_a.maximum_queue_length
    )
    assert set(metrics_state) == {"scenario_a", "scenario_b"}

def test_dashboard_creates_public_fast_charging_ab_results_and_metrics_from_stored_scenarios():
    active_scenario_state = create_active_scenario_state(
        PUBLIC_FAST_CHARGING_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = create_scenario_comparison_state(active_scenario_state)
    comparison_state["scenario_b"]["vehicles"] = 30

    (
        results_state,
        metrics_state,
        difference_metrics_state,
    ) = create_scenario_ab_comparison_run_state(comparison_state)

    result_a = simulation_result_from_dict(results_state["scenario_a"])
    result_b = simulation_result_from_dict(results_state["scenario_b"])
    metrics_a = metrics_from_dict(metrics_state["scenario_a"])
    metrics_b = metrics_from_dict(metrics_state["scenario_b"])
    difference_metrics = scenario_comparison_metrics_from_dict(
        difference_metrics_state
    )

    assert result_a.daily_energy_demand == 2400.0
    assert result_b.daily_energy_demand == 1500.0
    assert metrics_a.total_daily_energy == 2400.0
    assert metrics_b.total_daily_energy == 1500.0
    assert difference_metrics.delivered_energy_difference_kwh == pytest.approx(
        metrics_b.delivered_energy - metrics_a.delivered_energy
    )

def test_dashboard_creates_single_scenario_run_state_from_active_scenario_store():
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )

    simulation_results_state, metrics_state = create_single_scenario_run_state(
        active_scenario_state
    )

    active_result = simulation_result_from_dict(simulation_results_state["active"])
    uncontrolled_result = simulation_result_from_dict(
        simulation_results_state["uncontrolled"]
    )
    smart_result = simulation_result_from_dict(simulation_results_state["smart"])
    active_metrics = metrics_from_dict(metrics_state["active"])

    assert isinstance(active_result, SimulationResult)
    assert isinstance(uncontrolled_result, SimulationResult)
    assert isinstance(smart_result, SimulationResult)
    assert isinstance(active_metrics, Metrics)
    assert active_metrics.total_daily_energy == active_result.daily_energy_demand
    assert metrics_state["insights"]
    assert set(simulation_results_state) == {"active", "uncontrolled", "smart"}
    assert set(metrics_state) == {
        "active",
        "uncontrolled",
        "smart",
        "comparison",
        "insights",
    }
    assert active_result == smart_result
    smart_metrics = metrics_from_dict(metrics_state["smart"])
    assert smart_metrics.peak_load == active_metrics.peak_load
    assert (
        smart_metrics.required_connection_capacity_kw
        == active_metrics.required_connection_capacity_kw
    )
    assert (
        smart_metrics.required_charger_count
        == active_metrics.required_charger_count
    )
    assert smart_metrics.occupied_charger_count_by_timestep == []
    assert smart_metrics.waiting_vehicle_count_by_timestep == []
    assert "charging_requests" not in simulation_results_state["active"]
    assert "charging_requests" not in simulation_results_state["smart"]


@pytest.mark.parametrize(
    ("active_strategy", "expected_active_label"),
    [
        (ChargingStrategy.UNCONTROLLED.value, "uncontrolled"),
        (ChargingStrategy.SMART.value, "smart"),
    ],
)

def test_dashboard_single_scenario_run_state_reuses_matching_strategy_result_and_metrics(
    monkeypatch,
    active_strategy,
    expected_active_label,
):
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        active_strategy,
    )
    uncontrolled_result = object()
    smart_result = object()
    result_labels = {
        uncontrolled_result: "uncontrolled",
        smart_result: "smart",
    }
    strategy_calls = []
    metrics_calls = []

    def fail_if_direct_simulate_called(*_args, **_kwargs):
        raise AssertionError(
            "create_single_scenario_run_state should reuse strategy results "
            "instead of directly simulating the active scenario."
        )

    def fake_simulate_strategy_comparison(base_scenario):
        strategy_calls.append(base_scenario.charging_strategy)
        return uncontrolled_result, smart_result

    def fake_calculate_metrics(result, scenario):
        metrics_calls.append((result_labels[result], scenario.charging_strategy))
        return {"label": result_labels[result]}

    monkeypatch.setattr(
        dashboard_callbacks_module,
        "simulate",
        fail_if_direct_simulate_called,
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "simulate_strategy_comparison",
        fake_simulate_strategy_comparison,
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "calculate_metrics",
        fake_calculate_metrics,
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "calculate_comparison_metrics",
        lambda uncontrolled, smart: {
            "uncontrolled": uncontrolled["label"],
            "smart": smart["label"],
        },
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "_comparison_metrics_to_dict",
        lambda comparison_metrics: dict(comparison_metrics),
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "run_connection_capacity_sensitivity",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError(
                "create_single_scenario_run_state should not calculate "
                "connection-capacity sensitivity."
            )
        ),
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "generate_insights",
        lambda metrics, strategy, comparison_metrics: (
            f"{metrics['label']}:{strategy.value}:{comparison_metrics['smart']}",
        ),
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "_single_scenario_simulation_result_to_dict",
        lambda result: {"label": result_labels[result]},
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "_single_scenario_active_metrics_to_dict",
        lambda metrics: {"label": metrics["label"]},
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "_single_scenario_comparison_metrics_to_dict",
        lambda metrics: {"label": metrics["label"]},
    )

    simulation_results_state, metrics_state = create_single_scenario_run_state(
        active_scenario_state
    )

    expected_strategy = ChargingStrategy(active_strategy)
    assert strategy_calls == [expected_strategy]
    assert metrics_calls == [
        ("uncontrolled", expected_strategy),
        ("smart", expected_strategy),
    ]
    assert simulation_results_state["active"] == {"label": expected_active_label}
    assert metrics_state["active"] == {"label": expected_active_label}
    assert simulation_results_state[expected_active_label] == {"label": expected_active_label}
    assert metrics_state[expected_active_label] == {"label": expected_active_label}
    assert metrics_state["comparison"] == {
        "uncontrolled": "uncontrolled",
        "smart": "smart",
    }
    assert metrics_state["insights"] == [
        f"{expected_active_label}:{expected_strategy.value}:smart"
    ]

def test_dashboard_creates_connection_capacity_sensitivity_state_from_active_scenario_store():
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    active_scenario = active_scenario_from_state(active_scenario_state)
    _simulation_results_state, metrics_state = create_single_scenario_run_state(
        active_scenario_state
    )
    active_metrics = metrics_from_dict(metrics_state["active"])

    sensitivity_state = create_connection_capacity_sensitivity_state(
        active_scenario_state,
        metrics_state,
    )
    restored_rows = [
        capacity_alternative_metrics_from_dict(row)
        for row in sensitivity_state
    ]

    assert restored_rows == run_connection_capacity_sensitivity(
        active_scenario,
        base_metrics=active_metrics,
    )

def test_dashboard_single_scenario_results_state_is_json_safe_with_compact_payload():
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )

    simulation_results_state, _ = create_single_scenario_run_state(
        active_scenario_state
    )
    restored_state = json.loads(json.dumps(simulation_results_state))

    active_result = simulation_result_from_dict(restored_state["active"])
    uncontrolled_result = simulation_result_from_dict(
        restored_state["uncontrolled"]
    )
    smart_result = simulation_result_from_dict(restored_state["smart"])

    assert active_result.delivered_load_profile_kw
    assert uncontrolled_result.delivered_load_profile_kw
    assert smart_result.delivered_load_profile_kw
    assert active_result.charging_requests == []
    assert uncontrolled_result.charging_requests == []
    assert smart_result.charging_requests == []
    assert (
        active_result.grid_loading.transformer_loading.total_load_kw_by_timestep
        == []
    )
    assert (
        uncontrolled_result.grid_loading.transformer_loading.total_load_kw_by_timestep
        == []
    )
    assert (
        smart_result.grid_loading.transformer_loading.total_load_kw_by_timestep
        == []
    )


@pytest.mark.parametrize(
    ("preset_id", "strategy"),
    [
        (DEFAULT_SCENARIO_PRESET_ID, ChargingStrategy.SMART.value),
        (WORKPLACE_CHARGING_PRESET_ID, ChargingStrategy.UNCONTROLLED.value),
    ],
)

def test_dashboard_split_single_scenario_render_callbacks_match_legacy_render_behavior(
    preset_id,
    strategy,
):
    app = create_app()
    active_scenario_state = create_active_scenario_state(
        preset_id,
        strategy,
    )
    compact_simulation_results_state, compact_metrics_state = (
        create_single_scenario_run_state(active_scenario_state)
    )
    legacy_simulation_results_state, legacy_metrics_state = (
        _create_legacy_single_scenario_run_state(active_scenario_state)
    )
    legacy_sections = _create_legacy_single_scenario_render_sections(
        active_scenario_state
    )

    summary_callback = _find_callback_function(
        app,
        "total-daily-energy-value.children",
    )
    overview_callback = _find_callback_function(
        app,
        "capacity-vs-load-chart.figure",
    )
    infrastructure_callback = _find_callback_function(
        app,
        "infrastructure-summary.children",
    )
    smart_charging_callback = _find_callback_function(
        app,
        "strategy-comparison-load-profile-chart.figure",
    )
    grid_capacity_callback = _find_callback_function(
        app,
        "grid-loading-kpi-cards.children",
    )
    power_quality_callback = _find_callback_function(
        app,
        "power-quality-kpi-cards.children",
    )

    assert _normalize_dashboard_output(
        summary_callback(compact_metrics_state, {"status": "up_to_date"})
    ) == _normalize_dashboard_output(legacy_sections["summary"])
    assert _normalize_dashboard_output(
        overview_callback(
            compact_simulation_results_state,
            compact_metrics_state,
            "overview",
            active_scenario_state,
        )
    )[0] == _normalize_dashboard_output(legacy_sections["overview"])
    assert _normalize_dashboard_output(
        infrastructure_callback(
            compact_simulation_results_state,
            compact_metrics_state,
            "infrastructure",
            active_scenario_state,
        )
    ) == _normalize_dashboard_output(legacy_sections["infrastructure"])
    assert _normalize_dashboard_output(
        smart_charging_callback(
            compact_simulation_results_state,
            compact_metrics_state,
            "smart-charging",
            active_scenario_state,
        )
    ) == _normalize_dashboard_output(legacy_sections["smart_charging"])
    assert _normalize_dashboard_output(
        grid_capacity_callback(
            compact_simulation_results_state,
            compact_metrics_state,
            "grid-capacity",
            active_scenario_state,
        )
    ) == _normalize_dashboard_output(legacy_sections["grid_capacity"])
    assert _normalize_dashboard_output(
        power_quality_callback(
            compact_simulation_results_state,
            compact_metrics_state,
            "power-quality",
            active_scenario_state,
        )
    ) == _normalize_dashboard_output(legacy_sections["power_quality"])

def test_dashboard_tab_callbacks_render_completed_results_on_tab_switch_without_rerun():
    app = create_app()
    active_scenario_state = create_active_scenario_state(
        WORKPLACE_CHARGING_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    simulation_results_state, metrics_state = create_single_scenario_run_state(
        active_scenario_state
    )
    legacy_sections = _create_legacy_single_scenario_render_sections(
        active_scenario_state
    )

    overview_callback = _find_callback_function(
        app,
        "capacity-vs-load-chart.figure",
    )
    smart_charging_callback = _find_callback_function(
        app,
        "strategy-comparison-load-profile-chart.figure",
    )
    grid_capacity_callback = _find_callback_function(
        app,
        "grid-loading-kpi-cards.children",
    )

    assert overview_callback(
        simulation_results_state,
        metrics_state,
        "infrastructure",
        active_scenario_state,
    ) == (no_update,) * 3
    assert smart_charging_callback(
        simulation_results_state,
        metrics_state,
        "overview",
        active_scenario_state,
    ) == (no_update,) * 13
    assert grid_capacity_callback(
        simulation_results_state,
        metrics_state,
        "overview",
        active_scenario_state,
    ) == (no_update,) * 5

    assert _normalize_dashboard_output(
        overview_callback(
            simulation_results_state,
            metrics_state,
            "overview",
            active_scenario_state,
        )
    )[0] == _normalize_dashboard_output(legacy_sections["overview"])
    assert _normalize_dashboard_output(
        smart_charging_callback(
            simulation_results_state,
            metrics_state,
            "smart-charging",
            active_scenario_state,
        )
    ) == _normalize_dashboard_output(legacy_sections["smart_charging"])
    assert _normalize_dashboard_output(
        grid_capacity_callback(
            simulation_results_state,
            metrics_state,
            "grid-capacity",
            active_scenario_state,
        )
    ) == _normalize_dashboard_output(legacy_sections["grid_capacity"])


@pytest.mark.parametrize(
    "preset_id",
    [
        DEFAULT_SCENARIO_PRESET_ID,
        WORKPLACE_CHARGING_PRESET_ID,
    ],
)

def test_dashboard_single_scenario_store_payload_is_smaller_than_legacy_payload(
    preset_id,
):
    active_scenario_state = create_active_scenario_state(
        preset_id,
        ChargingStrategy.SMART.value,
    )
    compact_simulation_results_state, compact_metrics_state = (
        create_single_scenario_run_state(active_scenario_state)
    )
    legacy_simulation_results_state, legacy_metrics_state = (
        _create_legacy_single_scenario_run_state(active_scenario_state)
    )

    compact_results_size = len(
        json.dumps(compact_simulation_results_state, separators=(",", ":"))
    )
    legacy_results_size = len(
        json.dumps(legacy_simulation_results_state, separators=(",", ":"))
    )
    compact_metrics_size = len(
        json.dumps(compact_metrics_state, separators=(",", ":"))
    )
    legacy_metrics_size = len(
        json.dumps(legacy_metrics_state, separators=(",", ":"))
    )

    assert compact_results_size < legacy_results_size
    assert compact_metrics_size < legacy_metrics_size

def test_dashboard_ab_results_state_is_json_safe_with_transformer_loading():
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = create_scenario_comparison_state(active_scenario_state)
    comparison_state["scenario_b"]["vehicles"] = 75

    results_state = create_scenario_ab_simulation_results_state(comparison_state)
    restored_state = json.loads(json.dumps(results_state))

    result_a = simulation_result_from_dict(restored_state["scenario_a"])
    result_b = simulation_result_from_dict(restored_state["scenario_b"])

    assert len(
        result_a.grid_loading.transformer_loading.total_load_kw_by_timestep
    ) == len(result_a.delivered_load_profile_kw)
    assert len(
        result_b.grid_loading.transformer_loading.total_load_kw_by_timestep
    ) == len(result_b.delivered_load_profile_kw)

def test_dashboard_store_results_load_legacy_payload_without_transformer_loading():
    result = simulate(default_scenario)
    legacy_payload = simulation_result_to_dict(result)
    legacy_payload["grid_loading"] = {}

    restored_result = simulation_result_from_dict(
        json.loads(json.dumps(legacy_payload))
    )

    assert restored_result.delivered_load_profile_kw == result.delivered_load_profile_kw
    assert (
        restored_result.grid_loading.transformer_loading.total_load_kw_by_timestep
        == []
    )
    assert (
        restored_result.grid_loading.transformer_loading.loading_percent_by_timestep
        == []
    )
    assert (
        restored_result.grid_loading.transformer_loading.overload_kw_by_timestep
        == []
    )

def test_dashboard_ab_metrics_state_preserves_separate_series_lengths_when_scenarios_differ():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        occupied_charger_count_by_timestep=[0, 1, 1],
        waiting_vehicle_count_by_timestep=[0, 0, 1],
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        occupied_charger_count_by_timestep=[1, 1],
        waiting_vehicle_count_by_timestep=[0, 1],
    )

    metrics_state = {
        "scenario_a": metrics_to_dict(metrics_a),
        "scenario_b": metrics_to_dict(metrics_b),
    }

    restored_metrics_a = metrics_from_dict(metrics_state["scenario_a"])
    restored_metrics_b = metrics_from_dict(metrics_state["scenario_b"])

    assert restored_metrics_a.occupied_charger_count_by_timestep == [0, 1, 1]
    assert restored_metrics_b.occupied_charger_count_by_timestep == [1, 1]
    assert restored_metrics_a.waiting_vehicle_count_by_timestep == [0, 0, 1]
    assert restored_metrics_b.waiting_vehicle_count_by_timestep == [0, 1]
    assert len(restored_metrics_a.occupied_charger_count_by_timestep) == 3
    assert len(restored_metrics_b.occupied_charger_count_by_timestep) == 2

def test_dashboard_formatters_are_presentation_only():
    metrics = Metrics(
        total_daily_energy=7500.0,
        available_capacity=1000.0,
        energy_delivery_sufficient=True,
    )

    assert format_energy_kwh(metrics.total_daily_energy) == "7,500.0 kWh"
    assert format_annual_energy_kwh(2737500.0) == "2,737,500.0 kWh/year"
    assert format_power_kw(metrics.available_capacity) == "1,000.0 kW"
    assert format_percent(62.5) == "62.5%"
    assert format_percentage_points(30.0) == "30.0 percentage points"
    assert format_energy_delivery_status(metrics) == "Energy delivery is sufficient"
    assert format_capacity_status(metrics) == "Energy delivery is sufficient"

def test_dashboard_capacity_status_uses_metric_boolean():
    metrics = Metrics(
        total_daily_energy=7500.0,
        available_capacity=100.0,
        energy_delivery_sufficient=False,
    )

    assert format_energy_delivery_status(metrics) == "Energy delivery is insufficient"
    assert format_capacity_status(metrics) == "Energy delivery is insufficient"

def test_dashboard_scenario_status_for_energy_sufficient_and_capacity_not_exceeded():
    metrics = Metrics(
        total_daily_energy=7500.0,
        available_capacity=1000.0,
        energy_delivery_sufficient=True,
        connection_capacity_exceeded=False,
        unmet_energy=0.0,
    )

    visible_text = " ".join(_collect_text(format_scenario_status(metrics)))

    assert "Overall outcome: Feasible" in visible_text
    assert (
        "Configured connection capacity is adequate and daily energy demand "
        "can be delivered."
    ) in visible_text
    assert "Primary limiting factor:" in visible_text
    assert "No primary limiting factor indicated." in visible_text
    assert "Charger planning outcome:" in visible_text
    assert "Service rule met." in visible_text
    assert "Grid / PQ caution:" in visible_text
    assert "No additional grid or PQ caution indicated." in visible_text

def test_dashboard_scenario_status_treats_brief_waiting_as_service_rule_met():
    metrics = Metrics(
        total_daily_energy=40.0,
        available_capacity=50.0,
        energy_delivery_sufficient=True,
        connection_capacity_exceeded=False,
        queue_present_indicator=True,
        maximum_waiting_time_hours=0.5,
        vehicles_waiting_count=1,
        vehicles_not_started_count=0,
        vehicles_with_unmet_energy_count=0,
        primary_constraint_reason="charger_availability",
        required_charger_count=1,
        additional_chargers_required=0,
        unmet_energy=0.0,
    )

    visible_text = " ".join(_collect_text(format_scenario_status(metrics)))

    assert "Overall outcome: Feasible" in visible_text
    assert "Service rule met." in visible_text
    assert "Charger expansion indicated" not in visible_text
    assert "Charger expansion alone is insufficient." not in visible_text

def test_dashboard_scenario_status_for_energy_sufficient_and_capacity_exceeded():
    metrics = Metrics(
        total_daily_energy=7500.0,
        available_capacity=1000.0,
        energy_delivery_sufficient=True,
        connection_capacity_exceeded=True,
        connection_capacity_adequate_indicator=False,
        connection_capacity_recommendation_reason=(
            "persistent_requested_exceedance"
        ),
    )

    visible_text = " ".join(_collect_text(format_scenario_status(metrics)))

    assert "Overall outcome: Constrained" in visible_text
    assert (
        "A connection-capacity upgrade is indicated, although daily energy "
        "demand can still be delivered."
    ) in visible_text
    assert (
        "Persistent requested peak demand indicates connection-capacity "
        "review."
        in visible_text
    )

def test_dashboard_scenario_status_for_energy_insufficient_and_capacity_not_exceeded():
    metrics = Metrics(
        total_daily_energy=7500.0,
        available_capacity=100.0,
        energy_delivery_sufficient=False,
        connection_capacity_exceeded=False,
        unmet_energy=1600.0,
    )

    visible_text = " ".join(_collect_text(format_scenario_status(metrics)))

    assert "Overall outcome: Constrained" in visible_text
    assert (
        "Configured connection capacity remains adequate, but daily energy "
        "demand cannot be fully delivered within the scenario constraints."
    ) in visible_text
    assert (
        "Daily energy demand cannot be fully delivered within the scenario "
        "constraints." in visible_text
    )

def test_dashboard_scenario_status_for_energy_insufficient_and_capacity_exceeded():
    metrics = Metrics(
        total_daily_energy=7500.0,
        available_capacity=100.0,
        energy_delivery_sufficient=False,
        connection_capacity_exceeded=True,
        unmet_energy=1600.0,
        connection_capacity_adequate_indicator=False,
        connection_capacity_recommendation_reason=(
            "persistent_requested_exceedance"
        ),
    )

    visible_text = " ".join(_collect_text(format_scenario_status(metrics)))

    assert "Overall outcome: Constrained" in visible_text
    assert (
        "A connection-capacity upgrade is indicated and daily energy demand "
        "cannot be fully delivered."
    ) in visible_text

def test_dashboard_scenario_status_uses_metric_booleans_not_other_metric_values():
    metrics = Metrics(
        total_daily_energy=7500.0,
        available_capacity=100.0,
        energy_delivery_sufficient=True,
        connection_capacity_exceeded=False,
        unmet_energy=1600.0,
        peak_capacity_margin_kw=-500.0,
    )

    visible_text = " ".join(_collect_text(format_scenario_status(metrics)))

    assert "Overall outcome: Feasible" in visible_text
    assert (
        "Configured connection capacity is adequate and daily energy demand "
        "can be delivered."
    ) in visible_text

def test_dashboard_planner_status_formatter_uses_explicit_status_booleans():
    metrics = Metrics(
        total_daily_energy=7500.0,
        available_capacity=1000.0,
        energy_delivery_sufficient=True,
        connection_capacity_exceeded=True,
        unmet_energy=9999.0,
        connection_capacity_adequate_indicator=False,
        connection_capacity_recommendation_reason=(
            "persistent_requested_exceedance"
        ),
    )

    assert format_planner_status_message(metrics) == (
        "A connection-capacity upgrade is indicated, although daily energy "
        "demand can still be delivered."
    )

def test_dashboard_active_status_no_longer_uses_legacy_single_sufficiency_message():
    metrics = Metrics(
        total_daily_energy=7500.0,
        available_capacity=1000.0,
        energy_delivery_sufficient=True,
        connection_capacity_exceeded=False,
    )

    visible_text = " ".join(_collect_text(format_scenario_status(metrics)))

    assert "Overall outcome: Feasible" in visible_text
    assert "Warning" not in visible_text

def test_dashboard_scenario_status_surfaces_existing_charger_planning_outcome():
    metrics = Metrics(
        total_daily_energy=7500.0,
        available_capacity=100.0,
        energy_delivery_sufficient=False,
        connection_capacity_exceeded=False,
        queue_present_indicator=True,
        vehicles_not_started_count=2,
        vehicles_with_unmet_energy_count=2,
        primary_constraint_reason="charger_availability",
        additional_chargers_required=3,
    )

    visible_text = " ".join(_collect_text(format_scenario_status(metrics)))

    assert "Physical charger availability is the primary limiting factor." in visible_text
    assert "Charger expansion indicated (3 chargers)." in visible_text

def test_dashboard_scenario_status_surfaces_existing_grid_and_pq_caution():
    metrics = Metrics(
        total_daily_energy=7500.0,
        available_capacity=1000.0,
        energy_delivery_sufficient=True,
        connection_capacity_exceeded=False,
        transformer_overload_indicator=True,
        transformer_thermal_risk_level="moderate",
        overall_pq_risk_level="moderate",
        power_quality_warning_count=2,
    )

    visible_text = " ".join(_collect_text(format_scenario_status(metrics)))

    assert "Grid / PQ caution:" in visible_text
    assert "Modeled grid stress and PQ warnings should be reviewed together." in visible_text

def test_dashboard_capacity_status_alias_remains_compatible():
    metrics = Metrics(
        total_daily_energy=7500.0,
        available_capacity=100.0,
        capacity_sufficiency=False,
    )

    assert metrics.capacity_sufficiency == metrics.energy_delivery_sufficient
    assert format_capacity_status(metrics) == "Energy delivery is insufficient"

def test_dashboard_charger_planning_status_renders_service_rule_met_state():
    scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=50.0,
        charger_count=4,
        charger_power=100.0,
        grid_capacity=400.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(6, 0),
    )
    metrics = Metrics(
        total_daily_energy=500.0,
        available_capacity=400.0,
        energy_delivery_sufficient=True,
        queue_present_indicator=False,
        vehicles_not_started_count=0,
        vehicles_with_unmet_energy_count=0,
        primary_constraint_reason="none",
        required_charger_count=4,
        additional_chargers_required=0,
    )

    visible_text = " ".join(
        _collect_text(render_charger_planning_status(metrics, scenario))
    )

    assert "No charger expansion indicated" in visible_text
    assert "Current charger count satisfies the modeled service rule." in visible_text
    assert "Applied waiting tolerance:" in visible_text
    assert "0.5 h" in visible_text
    assert "Required charger count:" in visible_text
    assert "4 chargers" in visible_text
    assert "Current charger count:" not in visible_text
    assert "Additional chargers required:" not in visible_text

def test_dashboard_charger_planning_status_treats_brief_waiting_as_acceptable():
    scenario = Scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    metrics = Metrics(
        total_daily_energy=40.0,
        available_capacity=50.0,
        energy_delivery_sufficient=True,
        queue_present_indicator=True,
        maximum_waiting_time_hours=0.5,
        vehicles_waiting_count=1,
        vehicles_not_started_count=0,
        vehicles_with_unmet_energy_count=0,
        primary_constraint_reason="charger_availability",
        required_charger_count=1,
        additional_chargers_required=0,
    )

    visible_text = " ".join(
        _collect_text(render_charger_planning_status(metrics, scenario))
    )

    assert "No charger expansion indicated" in visible_text
    assert "Current charger count satisfies the modeled service rule." in visible_text
    assert "Applied waiting tolerance:" in visible_text
    assert (
        "Waiting is present but remains within the 0.5 h service expectation for this scenario"
        in visible_text
    )
    assert "Required charger count:" in visible_text
    assert "1 chargers" in visible_text
    assert "Recommendation unavailable" not in visible_text
    assert "Add chargers" not in visible_text

def test_dashboard_charger_planning_status_renders_numeric_expansion_message():
    scenario = Scenario(
        vehicles=12,
        daily_energy_per_vehicle=50.0,
        charger_count=2,
        charger_power=100.0,
        grid_capacity=400.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(6, 0),
    )
    metrics = Metrics(
        total_daily_energy=600.0,
        available_capacity=400.0,
        energy_delivery_sufficient=False,
        queue_present_indicator=True,
        vehicles_not_started_count=1,
        vehicles_with_unmet_energy_count=1,
        primary_constraint_reason="charger_availability",
        required_charger_count=4,
        additional_chargers_required=2,
        charger_capacity_vs_demand_balance=-2,
    )

    visible_text = " ".join(
        _collect_text(render_charger_planning_status(metrics, scenario))
    )

    assert "Add chargers" in visible_text
    assert "physical charger availability is the primary planning constraint" in (
        visible_text.lower()
    )
    assert "Add 2 chargers (4 chargers total) under current assumptions." in visible_text
    assert "Current charger count:" in visible_text
    assert "2 chargers" in visible_text
    assert "Required charger count:" in visible_text
    assert "4 chargers" in visible_text
    assert "Additional chargers required:" not in visible_text
    assert "Peak charger-slot balance:" not in visible_text

def test_dashboard_charger_planning_status_explains_waiting_driven_expansion():
    scenario = Scenario(
        vehicles=4,
        daily_energy_per_vehicle=10.0,
        charger_count=1,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )
    metrics = Metrics(
        total_daily_energy=40.0,
        available_capacity=50.0,
        energy_delivery_sufficient=True,
        queue_present_indicator=True,
        maximum_waiting_time_hours=0.75,
        vehicles_waiting_count=3,
        vehicles_not_started_count=0,
        vehicles_with_unmet_energy_count=0,
        primary_constraint_reason="charger_availability",
        required_charger_count=2,
        additional_chargers_required=1,
    )

    visible_text = " ".join(
        _collect_text(render_charger_planning_status(metrics, scenario))
    )

    assert "Add chargers" in visible_text
    assert (
        "to keep waiting within the 0.5 h service expectation for this scenario."
        in visible_text
    )
    assert "Applied waiting tolerance:" in visible_text
    assert "Current charger count:" in visible_text
    assert "1 chargers" in visible_text
    assert "Required charger count:" in visible_text
    assert "2 chargers" in visible_text


@pytest.mark.parametrize(
    ("primary_constraint_reason", "expected_reason_text"),
    [
        ("charger_power", "charger power is limiting"),
        (
            "grid_connection_capacity",
            "grid connection capacity is limiting",
        ),
        ("charging_window", "available charging time is limiting"),
        ("mixed", "multiple modeled constraints are limiting"),
    ],
)

def test_dashboard_charger_planning_status_renders_non_expansion_reasons(
    primary_constraint_reason,
    expected_reason_text,
):
    scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=50.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=80.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    )
    metrics = Metrics(
        total_daily_energy=500.0,
        available_capacity=80.0,
        energy_delivery_sufficient=False,
        queue_present_indicator=False,
        vehicles_not_started_count=0,
        vehicles_with_unmet_energy_count=4,
        primary_constraint_reason=primary_constraint_reason,
        required_charger_count=None,
        additional_chargers_required=None,
    )

    visible_text = " ".join(
        _collect_text(render_charger_planning_status(metrics, scenario))
    )

    assert "Review non-charger constraint" in visible_text
    assert expected_reason_text in visible_text
    assert "Adding chargers alone is not the primary recommendation" in visible_text
    assert "Required charger count: 0 chargers" not in visible_text

def test_dashboard_charger_planning_status_renders_zero_vehicle_state_safely():
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=1.0,
    )
    metrics = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        queue_present_indicator=False,
        vehicles_not_started_count=0,
        vehicles_with_unmet_energy_count=0,
        primary_constraint_reason="none",
        required_charger_count=0,
        additional_chargers_required=0,
    )

    visible_text = " ".join(
        _collect_text(render_charger_planning_status(metrics, scenario))
    )

    assert "No charger expansion indicated" in visible_text
    assert "no modeled vehicle charging demand" in visible_text.lower()
    assert "Required charger count:" in visible_text
    assert "0 chargers" in visible_text

def test_dashboard_charger_planning_status_renders_zero_demand_state_safely():
    scenario = Scenario(
        vehicles=5,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(6, 0),
    )
    metrics = Metrics(
        total_daily_energy=0.0,
        available_capacity=100.0,
        energy_delivery_sufficient=True,
        queue_present_indicator=False,
        vehicles_not_started_count=0,
        vehicles_with_unmet_energy_count=0,
        primary_constraint_reason="none",
        required_charger_count=2,
        additional_chargers_required=0,
    )

    visible_text = " ".join(
        _collect_text(render_charger_planning_status(metrics, scenario))
    )

    assert "No charger expansion indicated" in visible_text
    assert "Current charger count:" not in visible_text
    assert "Required charger count:" in visible_text
    assert "2 chargers" in visible_text

def test_dashboard_charger_planning_status_renders_unavailable_for_legacy_metrics():
    scenario = Scenario(
        vehicles=10,
        daily_energy_per_vehicle=50.0,
        charger_count=4,
        charger_power=100.0,
        grid_capacity=400.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(6, 0),
    )
    legacy_metrics = metrics_from_dict(
        {
            "total_daily_energy": 500.0,
            "available_capacity": 400.0,
            "energy_delivery_sufficient": True,
            "peak_load": 0.0,
            "capacity_utilization": 0.0,
            "delivered_energy": 500.0,
            "unmet_energy": 0.0,
            "annual_energy": 182500.0,
        }
    )

    visible_text = " ".join(
        _collect_text(render_charger_planning_status(legacy_metrics, scenario))
    )

    assert "Recommendation unavailable" in visible_text
    assert "cannot produce a charger recommendation" in visible_text

def test_dashboard_grid_asset_planning_status_renders_no_overload_state():
    metrics = Metrics(
        total_daily_energy=500.0,
        available_capacity=400.0,
        energy_delivery_sufficient=True,
        transformer_overload_indicator=False,
        transformer_thermal_risk_level="low",
        peak_transformer_loading_percent=82.0,
        feeder_overload_indicator=False,
        highest_feeder_thermal_risk_level="low",
        maximum_feeder_loading_percent=76.0,
    )

    visible_text = " ".join(_collect_text(render_grid_asset_planning_status(metrics)))

    assert "No grid caution" in visible_text
    assert "No modeled transformer or feeder caution is indicated" in visible_text
    assert "Grid & Capacity" in visible_text
    assert "Transformer overload:" not in visible_text
    assert "82.0%" not in visible_text
    assert "76.0%" not in visible_text

def test_dashboard_grid_asset_planning_status_renders_overload_state():
    metrics = Metrics(
        total_daily_energy=500.0,
        available_capacity=400.0,
        energy_delivery_sufficient=True,
        transformer_overload_indicator=True,
        transformer_thermal_risk_level="moderate",
        peak_transformer_loading_percent=104.0,
        feeder_overload_indicator=False,
        highest_feeder_thermal_risk_level="moderate",
        maximum_feeder_loading_percent=98.0,
    )

    visible_text = " ".join(_collect_text(render_grid_asset_planning_status(metrics)))

    assert "Grid stress indicated" in visible_text
    assert "Modeled transformer or feeder stress is indicated" in visible_text
    assert "Grid & Capacity" in visible_text
    assert "Transformer overload:" not in visible_text
    assert "104.0%" not in visible_text

def test_dashboard_grid_asset_planning_status_renders_high_risk_state():
    metrics = Metrics(
        total_daily_energy=500.0,
        available_capacity=400.0,
        energy_delivery_sufficient=True,
        transformer_overload_indicator=True,
        transformer_thermal_risk_level="high",
        peak_transformer_loading_percent=118.0,
        feeder_overload_indicator=True,
        highest_feeder_thermal_risk_level="high",
        maximum_feeder_loading_percent=111.0,
    )

    visible_text = " ".join(_collect_text(render_grid_asset_planning_status(metrics)))

    assert "Grid stress indicated" in visible_text
    assert "Modeled transformer or feeder stress is indicated" in visible_text
    assert "Grid & Capacity" in visible_text
    assert "Transformer thermal risk:" not in visible_text
    assert "Feeder overload:" not in visible_text

def test_dashboard_grid_asset_planning_status_keeps_grid_terms_separate_from_charger_terms():
    metrics = Metrics(
        total_daily_energy=500.0,
        available_capacity=400.0,
        energy_delivery_sufficient=False,
        transformer_overload_indicator=True,
        transformer_thermal_risk_level="high",
        peak_transformer_loading_percent=120.0,
        feeder_overload_indicator=True,
        highest_feeder_thermal_risk_level="high",
        maximum_feeder_loading_percent=115.0,
    )

    visible_text = " ".join(_collect_text(render_grid_asset_planning_status(metrics)))

    assert "charger expansion" not in visible_text.lower()
    assert "service rule" not in visible_text.lower()
    assert "required charger count" not in visible_text.lower()
    assert "grid" in visible_text.lower()


