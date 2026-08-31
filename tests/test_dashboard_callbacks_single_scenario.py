from tests.helpers import *  # noqa: F401,F403

def test_dashboard_registers_scenario_builder_callbacks():
    app = create_app()
    callback_keys = " ".join(app.callback_map)

    assert "active-scenario-store.data" in callback_keys
    assert "scenario-builder-store.data" in callback_keys
    assert "scenario-builder-feedback-store.data" in callback_keys

    builder_callback_key = next(
        key
        for key in app.callback_map
        if "scenario-builder-store.data" in key
        and "scenario-builder-feedback-store.data" in key
    )
    builder_inputs = app.callback_map[builder_callback_key]["inputs"]
    builder_state = app.callback_map[builder_callback_key]["state"]

    assert {
        "id": "scenario-preset-selector",
        "property": "value",
    } in builder_inputs
    assert {
        "id": "reset-scenario-preset-button",
        "property": "n_clicks",
    } in builder_inputs
    assert {
        "id": "charging-strategy-selector",
        "property": "value",
    } in builder_inputs
    assert {
        "id": "scenario-field-vehicles-input",
        "property": "value",
    } in builder_inputs
    assert {
        "id": "scenario-field-grid_capacity-input",
        "property": "value",
    } in builder_inputs
    assert builder_state == [
        {
            "id": "scenario-builder-store",
            "property": "data",
        }
    ]

    active_sync_callback_key = next(
        key
        for key in app.callback_map
        if key.startswith("active-scenario-store.data")
    )
    callback_inputs = app.callback_map[active_sync_callback_key]["inputs"]
    callback_state = app.callback_map[active_sync_callback_key]["state"]

    assert {
        "id": "scenario-builder-store",
        "property": "data",
    } in callback_inputs
    assert callback_state == [
        {
            "id": "active-scenario-store",
            "property": "data",
        }
    ]

    message_callback_key = next(
        key
        for key in app.callback_map
        if "scenario-input-validation-message.children" in key
        and "scenario-builder-status-message.children" in key
    )
    message_callback_inputs = app.callback_map[message_callback_key]["inputs"]

    assert {
        "id": "scenario-builder-feedback-store",
        "property": "data",
    } in message_callback_inputs
    assert {
        "id": "single-scenario-run-status-store",
        "property": "data",
    } in message_callback_inputs

def test_dashboard_single_scenario_builder_flow_has_no_cycles_and_no_advanced_ui_dependencies():
    app = create_app()
    relevant_nodes = {
        "scenario-builder-store.data",
        "scenario-builder-feedback-store.data",
        "active-scenario-store.data",
        "active-simulation-results-store.data",
        "active-metrics-store.data",
        "single-scenario-run-status-store.data",
    }
    adjacency = {output_node: set() for output_node in relevant_nodes}

    for callback_key, callback_entry in app.callback_map.items():
        callback_output_nodes = [
            output_node
            for output_node in _callback_output_nodes(callback_key)
            if output_node in relevant_nodes
        ]
        if not callback_output_nodes:
            continue

        callback_inputs = _callback_input_nodes(callback_entry)
        for output_node in callback_output_nodes:
            adjacency[output_node].update(
                input_node for input_node in callback_inputs if input_node in relevant_nodes
            )

    visiting = set()
    visited = set()

    def _visit(node):
        if node in visited:
            return
        if node in visiting:
            raise AssertionError(f"Cycle detected at {node}.")

        visiting.add(node)
        for next_node in adjacency[node]:
            _visit(next_node)
        visiting.remove(node)
        visited.add(node)

    for node in relevant_nodes:
        _visit(node)

    assert not any("scenario-sidebar-advanced" in node for node in relevant_nodes)
    assert not any(
        "scenario-sidebar-advanced" in input_node
        for callback_entry in app.callback_map.values()
        for input_node in _callback_input_nodes(callback_entry)
    )

def test_dashboard_preset_request_callback_flags_overwrite_for_modified_scenario(
    monkeypatch,
):
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "scenario-builder-store.data",
    )
    modified_builder_state = update_active_scenario_parameters(
        create_active_scenario_state(
            DEFAULT_SCENARIO_PRESET_ID,
            ChargingStrategy.UNCONTROLLED.value,
        ),
        parameter_updates={"vehicles": 72},
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="scenario-preset-selector"),
    )

    next_state, feedback_state = callback_function(
        PUBLIC_FAST_CHARGING_PRESET_ID,
        0,
        *(_sidebar_field_values_from_active_state(modified_builder_state)),
        modified_builder_state,
    )

    assert next_state["preset"] == {
        "preset_id": PUBLIC_FAST_CHARGING_PRESET_ID,
        "is_modified": False,
    }
    assert next_state["parameters"]["vehicles"] == 48
    assert feedback_state["action"] == "apply_preset"
    assert feedback_state["overwrote_modified_values"] is True

def test_dashboard_preset_request_callback_keeps_overwrite_false_for_clean_scenario(
    monkeypatch,
):
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "scenario-builder-store.data",
    )
    clean_builder_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.UNCONTROLLED.value,
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="scenario-preset-selector"),
    )

    next_state, feedback_state = callback_function(
        PUBLIC_FAST_CHARGING_PRESET_ID,
        0,
        *(_sidebar_field_values_from_active_state(clean_builder_state)),
        clean_builder_state,
    )

    assert next_state["preset"]["preset_id"] == PUBLIC_FAST_CHARGING_PRESET_ID
    assert feedback_state["action"] == "apply_preset"
    assert feedback_state["overwrote_modified_values"] is False

def test_dashboard_reset_preset_request_callback_uses_active_preset_and_dirty_state(
    monkeypatch,
):
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "scenario-builder-store.data",
    )
    modified_builder_state = update_active_scenario_parameters(
        create_active_scenario_state(
            WORKPLACE_CHARGING_PRESET_ID,
            ChargingStrategy.UNCONTROLLED.value,
        ),
        parameter_updates={"vehicles": 144},
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="reset-scenario-preset-button"),
    )

    next_state, feedback_state = callback_function(
        WORKPLACE_CHARGING_PRESET_ID,
        1,
        *(_sidebar_field_values_from_active_state(modified_builder_state)),
        modified_builder_state,
    )

    assert next_state["preset"] == {
        "preset_id": WORKPLACE_CHARGING_PRESET_ID,
        "is_modified": False,
    }
    assert next_state["parameters"]["vehicles"] == 120
    assert feedback_state["action"] == "reset_preset"
    assert feedback_state["overwrote_modified_values"] is True

def test_dashboard_preset_reducer_overwrites_modified_state_with_selected_preset_defaults(
    monkeypatch,
):
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "scenario-builder-feedback-store.data",
    )
    modified_active_state = update_active_scenario_parameters(
        create_active_scenario_state(
            DEFAULT_SCENARIO_PRESET_ID,
            ChargingStrategy.UNCONTROLLED.value,
        ),
        parameter_updates={
            "vehicles": 72,
            "grid_capacity": 1350.0,
        },
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="scenario-preset-selector"),
    )

    next_state, feedback_state = callback_function(
        PUBLIC_FAST_CHARGING_PRESET_ID,
        0,
        *(_sidebar_field_values_from_active_state(modified_active_state)),
        modified_active_state,
    )

    assert next_state["preset"] == {
        "preset_id": PUBLIC_FAST_CHARGING_PRESET_ID,
        "is_modified": False,
    }
    assert next_state["parameters"]["vehicles"] == 48
    assert next_state["parameters"]["grid_capacity"] == 1200.0
    assert feedback_state == {
        "action": "apply_preset",
        "overwrote_modified_values": True,
        "validation_message": "",
    }

def test_dashboard_field_edit_callback_ignores_unchanged_values(monkeypatch):
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "scenario-builder-store.data",
    )
    builder_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.UNCONTROLLED.value,
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="scenario-field-vehicles-input"),
    )

    next_state, feedback_state = callback_function(
        DEFAULT_SCENARIO_PRESET_ID,
        0,
        *(_sidebar_field_values_from_active_state(builder_state)),
        builder_state,
    )

    assert next_state is dashboard_callbacks_module.no_update
    assert feedback_state == {
        "action": "idle",
        "overwrote_modified_values": False,
        "validation_message": "",
    }

def test_dashboard_charging_window_start_edit_regenerates_shifted_overview_profile(
    monkeypatch,
):
    app = create_app()
    builder_callback = _find_callback_function(
        app,
        "scenario-builder-store.data",
    )
    active_state_callback = _find_callback_function(
        app,
        "active-scenario-store.data",
    )
    run_callback = _find_callback_function(
        app,
        "active-simulation-results-store.data",
    )
    overview_callback = _find_callback_function(
        app,
        "capacity-vs-load-chart.figure",
    )
    base_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.UNCONTROLLED.value,
    )
    field_names = list(SCENARIO_SIDEBAR_VISIBLE_FIELD_NAMES)
    edited_field_values = list(_sidebar_field_values_from_active_state(base_state))
    edited_field_values[field_names.index("charging_window_start")] = "18:00"
    base_results_state, _ = create_single_scenario_run_state(base_state)
    base_result = simulation_result_from_dict(base_results_state["active"])

    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(
            triggered_id="scenario-field-charging_window_start-input"
        ),
    )
    builder_state, feedback_state = builder_callback(
        DEFAULT_SCENARIO_PRESET_ID,
        0,
        *edited_field_values,
        base_state,
    )

    assert builder_state["parameters"]["charging_window_start"] == "18:00"
    assert builder_state["parameters"]["arrival_window_start"] == "18:00"
    assert builder_state["parameters"]["arrival_window_end"] == "18:00"
    assert feedback_state["action"] == "field_edit"

    active_state = active_state_callback(builder_state, base_state)

    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="run-simulation-button"),
    )
    results_state, metrics_state, run_status_state = run_callback(
        1,
        active_state,
        {"status": "stale"},
        feedback_state,
    )
    active_result = simulation_result_from_dict(results_state["active"])
    figure, _overview_cards, _smart_preview = overview_callback(
        results_state,
        metrics_state,
        OVERVIEW_TAB_VALUE,
        active_state,
    )

    assert run_status_state == {"status": "up_to_date"}
    assert active_result.delivered_load_profile_kw != base_result.delivered_load_profile_kw
    assert base_result.delivered_load_profile_kw[get_time_labels().index("17:00")] > 0.0
    assert active_result.delivered_load_profile_kw[get_time_labels().index("17:00")] == 0.0
    assert active_result.delivered_load_profile_kw[get_time_labels().index("18:00")] > 0.0
    assert list(figure.data[0].y) == active_result.delivered_load_profile_kw
    assert list(figure.data[1].y) == active_result.requested_load_profile_kw

def test_dashboard_registers_strategy_selector_visibility_callback():
    app = create_app()
    callback_keys = " ".join(app.callback_map)

    assert "charging-strategy-selector-container.style" in callback_keys
    assert "smart-charging-comparison-mode-container.style" in callback_keys

    callback_key = next(
        key
        for key in app.callback_map
        if "charging-strategy-selector-container.style" in key
    )
    callback_inputs = app.callback_map[callback_key]["inputs"]

    assert {
        "id": "dashboard-tabs",
        "property": "value",
    } in callback_inputs

def test_dashboard_registers_single_scenario_run_state_callbacks():
    app = create_app()
    callback_keys = " ".join(app.callback_map)
    callback_outputs = [
        output.strip(".")
        for callback_key in app.callback_map
        for output in callback_key.split("...")
        if output.strip(".")
    ]

    assert "active-simulation-results-store.data" in callback_keys
    assert "active-metrics-store.data" in callback_keys
    assert "active-capacity-sensitivity-store.data" in callback_keys
    assert "single-scenario-run-status-store.data" in callback_keys
    assert "smart-charging-comparison-summary-cards.children" in callback_keys
    assert "charger-availability-comparison-table.children" not in callback_keys
    assert "charging-performance-comparison-table.children" in callback_keys
    assert "power-quality-comparison-table.children" in callback_keys
    assert "capacity-planning-comparison-table.children" not in callback_keys
    assert "detailed-comparison-table.children" in callback_keys
    assert "dashboard-graph-resize-effect.children" in callback_keys
    assert "strategy-comparison-queue-chart-container.style" in callback_keys
    assert "strategy-comparison-queue-status.children" in callback_keys
    assert "power-quality-comparison-status.children" in callback_keys
    assert "capacity-planning-comparison-status.children" not in callback_keys
    assert "power-capacity-chart.figure" in callback_keys
    assert "load-profile-chart.figure" not in callback_outputs
    assert "strategy-comparison-load-profile-chart.figure" in callback_outputs
    assert "strategy-comparison-occupancy-chart.figure" in callback_keys
    assert "strategy-comparison-queue-chart.figure" in callback_keys
    assert "strategy-comparison-pq-risk-chart.figure" in callback_keys

    run_state_callback_key = next(
        key
        for key in app.callback_map
        if "active-simulation-results-store.data" in key
        and "total-daily-energy-value.children" not in key
    )
    run_state_callback_inputs = app.callback_map[run_state_callback_key]["inputs"]

    assert {
        "id": "run-simulation-button",
        "property": "n_clicks",
    } in run_state_callback_inputs
    assert {
        "id": "active-scenario-store",
        "property": "data",
    } in run_state_callback_inputs
    run_state_callback_state = app.callback_map[run_state_callback_key]["state"]
    assert {
        "id": "single-scenario-run-status-store",
        "property": "data",
    } in run_state_callback_state
    assert {
        "id": "scenario-builder-feedback-store",
        "property": "data",
    } in run_state_callback_state

    sensitivity_callback_key = next(
        key
        for key in app.callback_map
        if "active-capacity-sensitivity-store.data" in key
    )
    sensitivity_callback_inputs = app.callback_map[sensitivity_callback_key]["inputs"]
    sensitivity_callback_state = app.callback_map[sensitivity_callback_key]["state"]

    assert {
        "id": "active-scenario-store",
        "property": "data",
    } in sensitivity_callback_inputs
    assert {
        "id": "active-metrics-store",
        "property": "data",
    } in sensitivity_callback_inputs
    assert {
        "id": "dashboard-tabs",
        "property": "value",
    } in sensitivity_callback_inputs
    assert sensitivity_callback_state == [
        {
            "id": "active-capacity-sensitivity-store",
            "property": "data",
        },
        {
            "id": "single-scenario-run-status-store",
            "property": "data",
        },
    ]

    summary_callback_key = next(
        key
        for key in app.callback_map
        if "total-daily-energy-value.children" in key
    )
    summary_callback_inputs = app.callback_map[summary_callback_key]["inputs"]
    summary_callback_state = app.callback_map[summary_callback_key]["state"]

    assert summary_callback_inputs == [
        {
            "id": "active-metrics-store",
            "property": "data",
        },
        {
            "id": "single-scenario-run-status-store",
            "property": "data",
        }
    ]
    assert summary_callback_state == []

    overview_callback_key = next(
        key
        for key in app.callback_map
        if "capacity-vs-load-chart.figure" in key
    )
    overview_callback_inputs = app.callback_map[overview_callback_key]["inputs"]
    overview_callback_state = app.callback_map[overview_callback_key]["state"]

    assert {
        "id": "active-simulation-results-store",
        "property": "data",
    } in overview_callback_inputs
    assert {
        "id": "active-metrics-store",
        "property": "data",
    } in overview_callback_inputs
    assert {
        "id": "dashboard-tabs",
        "property": "value",
    } in overview_callback_inputs
    assert overview_callback_state == [
        {
            "id": "active-scenario-store",
            "property": "data",
        }
    ]

    graph_resize_callback_key = next(
        key
        for key in app.callback_map
        if key.startswith("dashboard-graph-resize-effect.children")
    )
    graph_resize_callback_inputs = app.callback_map[graph_resize_callback_key]["inputs"]

    assert graph_resize_callback_inputs == [
        {
            "id": "dashboard-tabs",
            "property": "value",
        },
        {
            "id": "active-simulation-results-store",
            "property": "data",
        },
        {
            "id": "active-metrics-store",
            "property": "data",
        },
        {
            "id": "single-scenario-run-status-store",
            "property": "data",
        },
        {
            "id": "scenario-ab-simulation-results-store",
            "property": "data",
        },
        {
            "id": "scenario-ab-metrics-store",
            "property": "data",
        },
        {
            "id": "scenario-ab-difference-metrics-store",
            "property": "data",
        },
    ]

    smart_charging_callback_key = next(
        key
        for key in app.callback_map
        if "strategy-comparison-load-profile-chart.figure" in key
    )
    smart_charging_callback_inputs = app.callback_map[
        smart_charging_callback_key
    ]["inputs"]

    assert {
        "id": "dashboard-tabs",
        "property": "value",
    } in smart_charging_callback_inputs

    sensitivity_render_callback_key = next(
        key
        for key in app.callback_map
        if key.startswith("capacity-sensitivity-table.children")
    )
    sensitivity_render_inputs = app.callback_map[
        sensitivity_render_callback_key
    ]["inputs"]

    assert sensitivity_render_inputs == [
        {
            "id": "active-capacity-sensitivity-store",
            "property": "data",
        },
        {
            "id": "active-simulation-results-store",
            "property": "data",
        },
        {
            "id": "active-metrics-store",
            "property": "data",
        },
        {
            "id": "single-scenario-run-status-store",
            "property": "data",
        },
        {
            "id": "dashboard-tabs",
            "property": "value",
        },
    ]

def test_dashboard_run_state_callback_marks_results_stale_only_after_actual_scenario_change(
    monkeypatch,
):
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "active-simulation-results-store.data",
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="active-scenario-store"),
    )

    results_state, metrics_state, run_status_state = callback_function(
        0,
        create_active_scenario_state(
            DEFAULT_SCENARIO_PRESET_ID,
            ChargingStrategy.UNCONTROLLED.value,
        ),
        {"status": "up_to_date"},
        {"action": "idle", "overwrote_modified_values": False, "validation_message": ""},
    )

    assert results_state is no_update
    assert metrics_state is no_update
    assert run_status_state == {"status": "stale"}

def test_dashboard_single_scenario_summary_surfaces_stale_warning_without_clearing_results():
    app = create_app()
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    _simulation_results_state, metrics_state = create_single_scenario_run_state(
        active_scenario_state
    )
    callback_function = _find_callback_function(
        app,
        "total-daily-energy-value.children",
    )

    up_to_date_result = callback_function(
        metrics_state,
        {"status": "up_to_date"},
    )
    stale_result = callback_function(
        metrics_state,
        {"status": "stale"},
    )

    assert stale_result[:8] == up_to_date_result[:8]
    assert _collect_text(stale_result[9]) == _collect_text(up_to_date_result[9])
    assert "out of date" in " ".join(_collect_text(stale_result[8])).lower()

def test_dashboard_overview_smart_charging_preview_renders_compact_comparison_visual():
    app = create_app()
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    simulation_results_state, metrics_state = create_single_scenario_run_state(
        active_scenario_state
    )
    overview_callback = _find_callback_function(
        app,
        "capacity-vs-load-chart.figure",
    )

    preview_children = overview_callback(
        simulation_results_state,
        metrics_state,
        OVERVIEW_TAB_VALUE,
        active_scenario_state,
    )[2]
    preview_text = " ".join(_collect_text(preview_children))

    assert "Peak Reduction" in preview_text or "Peak Increase" in preview_text
    assert "Uncontrolled peak load" in preview_text
    assert "Smart Charging peak load" in preview_text
    assert "Before vs after" not in preview_text
    assert "Shared peak scale" not in preview_text

def test_dashboard_overview_scenario_outcome_card_uses_responsive_wrapping_style():
    app = create_app()
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.UNCONTROLLED.value,
    )
    simulation_results_state, metrics_state = create_single_scenario_run_state(
        active_scenario_state
    )
    overview_callback = _find_callback_function(
        app,
        "capacity-vs-load-chart.figure",
    )

    _figure, overview_cards, _smart_preview = overview_callback(
        simulation_results_state,
        metrics_state,
        OVERVIEW_TAB_VALUE,
        active_scenario_state,
    )

    scenario_outcome_card = overview_cards[0]
    scenario_outcome_value = scenario_outcome_card.children[1]

    assert scenario_outcome_card.style["minWidth"] == "0"
    assert (
        scenario_outcome_value.style["fontSize"]
        == "clamp(1.7rem, 1.5rem + 0.7vw, 2.15rem)"
    )
    assert scenario_outcome_value.style["lineHeight"] == "1.15"
    assert scenario_outcome_value.style["maxWidth"] == "100%"
    assert scenario_outcome_value.style["whiteSpace"] == "normal"
    assert scenario_outcome_value.style["overflowWrap"] == "break-word"

def test_dashboard_connection_capacity_sensitivity_callback_clears_state_when_scenario_changes(
    monkeypatch,
):
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "active-capacity-sensitivity-store.data",
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="active-scenario-store"),
    )

    next_state = callback_function(
        create_active_scenario_state(
            DEFAULT_SCENARIO_PRESET_ID,
            ChargingStrategy.UNCONTROLLED.value,
        ),
        None,
        OVERVIEW_TAB_VALUE,
        [{"capacity_option_kw": 800.0}],
        {"status": "up_to_date"},
    )

    assert next_state is None

def test_dashboard_connection_capacity_sensitivity_callback_does_not_run_when_grid_tab_is_inactive(
    monkeypatch,
):
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "active-capacity-sensitivity-store.data",
    )
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.UNCONTROLLED.value,
    )
    expected_state = [{"capacity_option_kw": 800.0}]
    metrics_state = {"active": {"label": "active"}}
    sensitivity_calls = []

    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="active-metrics-store"),
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "create_connection_capacity_sensitivity_state",
        lambda scenario_state, next_metrics_state: sensitivity_calls.append(
            (scenario_state, next_metrics_state)
        )
        or expected_state,
    )

    next_state = callback_function(
        active_scenario_state,
        metrics_state,
        OVERVIEW_TAB_VALUE,
        [{"capacity_option_kw": 600.0}],
        {"status": "up_to_date"},
    )

    assert sensitivity_calls == []
    assert next_state is None

def test_dashboard_connection_capacity_sensitivity_callback_runs_when_grid_tab_is_first_opened(
    monkeypatch,
):
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "active-capacity-sensitivity-store.data",
    )
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.UNCONTROLLED.value,
    )
    expected_state = [{"capacity_option_kw": 800.0}]
    metrics_state = {"active": {"label": "active"}}
    sensitivity_calls = []

    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="dashboard-tabs"),
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "create_connection_capacity_sensitivity_state",
        lambda scenario_state, next_metrics_state: sensitivity_calls.append(
            (scenario_state, next_metrics_state)
        )
        or expected_state,
    )

    next_state = callback_function(
        active_scenario_state,
        metrics_state,
        GRID_CAPACITY_TAB_VALUE,
        None,
        {"status": "up_to_date"},
    )

    assert sensitivity_calls == [(active_scenario_state, metrics_state)]
    assert next_state == expected_state

def test_dashboard_connection_capacity_sensitivity_callback_reuses_cached_rows_on_tab_revisit(
    monkeypatch,
):
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "active-capacity-sensitivity-store.data",
    )
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.UNCONTROLLED.value,
    )
    metrics_state = {"active": {"label": "active"}}
    current_sensitivity_state = [{"capacity_option_kw": 800.0}]

    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="dashboard-tabs"),
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "create_connection_capacity_sensitivity_state",
        lambda *_args: pytest.fail(
            "sensitivity should not recompute when cached rows already exist"
        ),
    )

    next_state = callback_function(
        active_scenario_state,
        metrics_state,
        GRID_CAPACITY_TAB_VALUE,
        current_sensitivity_state,
        {"status": "up_to_date"},
    )

    assert next_state is no_update

def test_dashboard_connection_capacity_sensitivity_callback_invalidates_cached_rows_on_new_run(
    monkeypatch,
):
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "active-capacity-sensitivity-store.data",
    )
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.UNCONTROLLED.value,
    )
    metrics_state = {"active": {"label": "active"}}
    previous_state = [{"capacity_option_kw": 600.0}]

    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="active-metrics-store"),
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "create_connection_capacity_sensitivity_state",
        lambda *_args: pytest.fail(
            "sensitivity should be invalidated, not recomputed, when a new run finishes off the Grid & Capacity tab"
        ),
    )

    next_state = callback_function(
        active_scenario_state,
        metrics_state,
        OVERVIEW_TAB_VALUE,
        previous_state,
        {"status": "up_to_date"},
    )

    assert next_state is None

def test_dashboard_connection_capacity_sensitivity_callback_computes_on_completed_grid_tab_run(
    monkeypatch,
):
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "active-capacity-sensitivity-store.data",
    )
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.UNCONTROLLED.value,
    )
    expected_state = [{"capacity_option_kw": 800.0}]
    metrics_state = {"active": {"label": "active"}}
    sensitivity_calls = []

    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="active-metrics-store"),
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "create_connection_capacity_sensitivity_state",
        lambda scenario_state, next_metrics_state: sensitivity_calls.append(
            (scenario_state, next_metrics_state)
        )
        or expected_state,
    )

    next_state = callback_function(
        active_scenario_state,
        metrics_state,
        GRID_CAPACITY_TAB_VALUE,
        [{"capacity_option_kw": 600.0}],
        {"status": "up_to_date"},
    )

    assert sensitivity_calls == [(active_scenario_state, metrics_state)]
    assert next_state == expected_state

def test_dashboard_connection_capacity_sensitivity_render_callback_shows_loading_until_rows_arrive():
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "capacity-sensitivity-table.children",
    )

    content = callback_function(
        None,
        {"active": {"label": "active"}},
        {"active": {"label": "active"}},
        {"status": "up_to_date"},
        GRID_CAPACITY_TAB_VALUE,
    )

    assert content == "Loading connection-capacity alternatives..."

def test_dashboard_connection_capacity_sensitivity_render_callback_keeps_placeholder_until_grid_tab_is_opened():
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "capacity-sensitivity-table.children",
    )

    content = callback_function(
        None,
        {"active": {"label": "active"}},
        {"active": {"label": "active"}},
        {"status": "up_to_date"},
        OVERVIEW_TAB_VALUE,
    )

    assert content is no_update

def test_dashboard_render_selected_simulation_callback_returns_exact_declared_output_count():
    app = create_app()
    callback_specs = [
        ("total-daily-energy-value.children", (None, None), 10),
        (
            "capacity-vs-load-chart.figure",
            (None, None, "overview", None),
            3,
        ),
        (
            "infrastructure-summary.children",
            (None, None, "infrastructure", None),
            4,
        ),
        (
            "strategy-comparison-load-profile-chart.figure",
            (None, None, "smart-charging", None),
            13,
        ),
        (
            "grid-loading-kpi-cards.children",
            (None, None, "grid-capacity", None),
            5,
        ),
        (
            "power-quality-kpi-cards.children",
            (None, None, "power-quality", None),
            5,
        ),
    ]

    for output_fragment, placeholder_args, expected_output_count in callback_specs:
        callback_key = next(
            key
            for key in app.callback_map
            if output_fragment in key
        )
        callback_function = _find_callback_function(
            app,
            output_fragment,
        )
        declared_output_count = len(callback_key.split("..."))
        assert declared_output_count == expected_output_count

        placeholder_result = callback_function(*placeholder_args)
        if expected_output_count == 1:
            assert placeholder_result == {}
        else:
            assert len(placeholder_result) == declared_output_count

    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    simulation_results_state, metrics_state = create_single_scenario_run_state(
        active_scenario_state
    )
    rendered_result = _find_callback_function(
        app,
        "strategy-comparison-load-profile-chart.figure",
    )(
        simulation_results_state,
        metrics_state,
        "smart-charging",
        active_scenario_state,
    )

    assert len(rendered_result) == 13

def test_dashboard_registers_scenario_preset_details_callback():
    app = create_app()
    callback_keys = " ".join(app.callback_map)

    assert "scenario-preset-details.children" in callback_keys

    details_callback_key = next(
        key
        for key in app.callback_map
        if "scenario-preset-details.children" in key
    )
    callback_inputs = app.callback_map[details_callback_key]["inputs"]

    assert {
        "id": "scenario-builder-store",
        "property": "data",
    } in callback_inputs

def test_dashboard_scenario_preset_details_callback_hides_conditional_advanced_fields_by_default():
    app = create_app()
    callback = _find_callback_function(app, "scenario-preset-details.children")

    (
        _details,
        _modified_indicator_style,
        _reset_button_style,
        session_dwell_style,
    ) = callback(
        create_active_scenario_state(
            DEFAULT_SCENARIO_PRESET_ID,
            ChargingStrategy.UNCONTROLLED.value,
        )
    )

    assert session_dwell_style == {"display": "none"}

def test_dashboard_scenario_preset_details_callback_shows_session_dwell_when_departure_mode_uses_it():
    app = create_app()
    callback = _find_callback_function(app, "scenario-preset-details.children")
    builder_state = update_active_scenario_parameters(
        create_active_scenario_state(
            DEFAULT_SCENARIO_PRESET_ID,
            ChargingStrategy.UNCONTROLLED.value,
        ),
        parameter_updates={
            "departure_mode": DepartureMode.SESSION_DWELL.value,
            "session_dwell_minutes": 45,
        },
    )

    (
        _details,
        _modified_indicator_style,
        _reset_button_style,
        session_dwell_style,
    ) = callback(builder_state)

    assert session_dwell_style == {}

def test_dashboard_scenario_builder_status_message_state_shows_stale_rerun_copy():
    message, style = _scenario_builder_status_message_state(
        {"validation_message": "", "action": "field_edit"},
        {"status": "stale"},
    )

    assert message == "Inputs changed — rerun simulation."
    assert style == {"display": "block"}

def test_dashboard_scenario_builder_status_message_state_hides_when_validation_is_present():
    message, style = _scenario_builder_status_message_state(
        {"validation_message": "Grid capacity must be positive."},
        {"status": "stale"},
    )

    assert message == ""
    assert style == {"display": "none"}

def test_dashboard_normalizes_single_scenario_run_status_state():
    assert _normalize_single_scenario_run_status_state(None) == {
        "status": "not_run"
    }
    assert _normalize_single_scenario_run_status_state(
        {"status": "up_to_date"}
    ) == {"status": "up_to_date"}
    assert _normalize_single_scenario_run_status_state(
        {"status": "unexpected"}
    ) == {"status": "not_run"}

def test_dashboard_sidebar_whole_number_coercion_preserves_exact_integer_values():
    assert _coerce_sidebar_field_value("vehicles", 500.0) == 500
    assert _coerce_sidebar_field_value("charger_count", 12.0) == 12
    assert _coerce_sidebar_field_value("departure_time_spread_minutes", 45.0) == 45

def test_dashboard_sidebar_whole_number_coercion_rejects_fractional_integer_fields():
    with pytest.raises(ValueError, match="Number of vehicles must be a whole number."):
        _coerce_sidebar_field_value("vehicles", 499.5)

def test_dashboard_scenario_b_edits_coerce_whole_number_inputs_without_truncation():
    comparison_state = create_scenario_comparison_state(
        create_active_scenario_state(
            DEFAULT_SCENARIO_PRESET_ID,
            ChargingStrategy.UNCONTROLLED.value,
        )
    )

    next_state = update_scenario_comparison_state_for_b_edits(
        comparison_state,
        vehicles=75.0,
        charger_count=12.0,
        charger_power=180.0,
        grid_capacity=1200.0,
    )

    assert next_state["scenario_b"]["vehicles"] == 75
    assert next_state["scenario_b"]["charger_count"] == 12

def test_dashboard_running_simulation_does_not_mutate_active_scenario_state():
    active_state = update_active_scenario_parameters(
        create_active_scenario_state(
            DEFAULT_SCENARIO_PRESET_ID,
            ChargingStrategy.UNCONTROLLED.value,
        ),
        parameter_updates={
            "vehicles": 500,
            "grid_capacity": 1500.0,
            "charger_count": 15,
        },
    )
    original_state = json.loads(json.dumps(active_state))

    create_single_scenario_run_state(active_state)

    assert active_state == original_state

def test_dashboard_sync_sidebar_callback_reflects_modified_state_and_visible_dependent_inputs():
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "scenario-preset-modified-indicator.style",
    )
    edited_state = update_active_scenario_parameters(
        create_active_scenario_state(
            DEFAULT_SCENARIO_PRESET_ID,
            ChargingStrategy.UNCONTROLLED.value,
        ),
        parameter_updates={
            "departure_mode": DepartureMode.SESSION_DWELL.value,
            "session_dwell_minutes": 45,
        },
    )

    result = callback_function(edited_state)

    details_text = " ".join(_collect_text(result[0]))
    assert "Depot-style heavy-duty charging scenario used as the MVP reference configuration." in details_text
    assert result[1] == {}
    assert result[2].get("display") != "none"
    assert result[3] == {}

def test_dashboard_sync_sidebar_callback_hides_modified_and_dependent_inputs_for_clean_defaults():
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "scenario-preset-modified-indicator.style",
    )
    clean_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.UNCONTROLLED.value,
    )

    result = callback_function(clean_state)

    assert result[1] == {"display": "none"}
    assert result[2]["display"] == "none"
    assert result[3] == {"display": "none"}

def test_dashboard_sync_sidebar_field_groups_callback_rebuilds_inputs_for_preset_apply():
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "scenario-sidebar-field-groups.children",
    )
    public_fast_state = apply_preset_defaults_to_active_scenario_state(
        PUBLIC_FAST_CHARGING_PRESET_ID
    )

    result = callback_function(
        public_fast_state,
        {
            "action": "apply_preset",
            "overwrote_modified_values": True,
            "validation_message": "",
        },
    )

    visible_text = " ".join(_collect_text(result))
    assert "Number of vehicles" in visible_text
    assert "Number of chargers" in visible_text

def test_dashboard_layout_removes_static_model_assumptions_price_note():
    app = create_app()
    note = _find_component_by_id(app.layout, "model-assumptions-price-note")

    assert note is None

