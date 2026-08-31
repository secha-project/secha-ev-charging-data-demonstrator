from tests.helpers import *  # noqa: F401,F403

def test_dashboard_registers_duplicate_scenario_callback():
    app = create_app()
    callback_keys = " ".join(app.callback_map)

    assert "scenario-comparison-store.data" in callback_keys
    assert "scenario-comparison-status.children" in callback_keys
    assert "modified-copy-builder-action.style" in callback_keys
    assert "scenario-b-template-section.style" in callback_keys
    assert "scenario-b-editor-section.style" in callback_keys
    assert "scenario-b-validation-message.children" in callback_keys

    duplicate_callback_key = next(
        key for key in app.callback_map if "scenario-comparison-store.data" in key
    )
    callback_inputs = app.callback_map[duplicate_callback_key]["inputs"]
    callback_state = app.callback_map[duplicate_callback_key]["state"]

    assert {
        "id": "active-scenario-store",
        "property": "data",
    } in callback_inputs
    assert {
        "id": "comparison-source-selector",
        "property": "value",
    } in callback_inputs
    assert {
        "id": "duplicate-scenario-b-button",
        "property": "n_clicks",
    } in callback_inputs
    assert {
        "id": "scenario-b-template-selector",
        "property": "value",
    } in callback_inputs
    assert {
        "id": "scenario-b-vehicles-input",
        "property": "value",
    } in callback_inputs
    assert {
        "id": "scenario-b-charger-count-input",
        "property": "value",
    } in callback_inputs
    assert {
        "id": "scenario-b-charger-power-input",
        "property": "value",
    } in callback_inputs
    assert {
        "id": "scenario-b-grid-capacity-input",
        "property": "value",
    } in callback_inputs
    assert {
        "id": "scenario-comparison-store",
        "property": "data",
    } in callback_state

def test_dashboard_duplicate_scenario_callback_uses_fully_edited_active_scenario(
    monkeypatch,
):
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "scenario-comparison-store.data",
    )
    edited_active_scenario_state = update_active_scenario_parameters(
        create_active_scenario_state(
            DEFAULT_SCENARIO_PRESET_ID,
            ChargingStrategy.UNCONTROLLED.value,
        ),
        parameter_updates={
            "vehicles": 72,
            "grid_capacity": 1350.0,
            "request_energy_variability_percent": 12.0,
        },
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="duplicate-scenario-b-button"),
    )

    next_state, status_message, *_rest = callback_function(
        edited_active_scenario_state,
        COMPARISON_SOURCE_MODIFIED_COPY,
        1,
        DEFAULT_SCENARIO_PRESET_ID,
        None,
        None,
        None,
        None,
        None,
    )

    assert next_state["scenario_a"]["vehicles"] == 72
    assert next_state["scenario_a"]["grid_capacity"] == 1350.0
    assert next_state["scenario_a"]["request_energy_variability_percent"] == 12.0
    assert next_state["scenario_b"] == next_state["scenario_a"]
    assert status_message == (
        "Scenario B is ready. Changes here affect only the comparison scenario."
    )

def test_dashboard_scenario_comparison_results_invalidate_when_scenario_b_changes(
    monkeypatch,
):
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "scenario-ab-simulation-results-store.data",
    )
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = update_scenario_b_in_comparison_data(
        create_scenario_comparison_state(active_scenario_state),
        vehicles=75,
    )
    _results_state, current_metrics_state, current_difference_metrics_state = (
        create_scenario_ab_comparison_run_state(comparison_state)
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="scenario-comparison-store"),
    )

    (
        results_state,
        metrics_state,
        difference_metrics_state,
        run_status_state,
        status_message,
    ) = (
        callback_function(
            1,
            0,
            active_scenario_state,
            comparison_state,
            current_metrics_state,
            {"status": "up_to_date"},
            {
                "status": "up_to_date",
                "stale_reason": None,
                "baseline_active_scenario_state": active_scenario_state,
            },
            current_metrics_state,
            current_difference_metrics_state,
        )
    )

    assert results_state is no_update
    assert metrics_state is no_update
    assert difference_metrics_state is no_update
    assert run_status_state == {
        "status": "stale",
        "stale_reason": "scenario_b_changed",
        "baseline_active_scenario_state": active_scenario_state,
    }
    assert "Previous results remain visible" in status_message

def test_dashboard_scenario_comparison_results_reset_after_successful_new_baseline_run(
    monkeypatch,
):
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "scenario-ab-simulation-results-store.data",
    )
    original_active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    updated_active_scenario_state = update_active_scenario_parameters(
        original_active_scenario_state,
        parameter_updates={"vehicles": 72},
    )
    comparison_state = update_scenario_a_in_comparison_data(
        update_scenario_b_in_comparison_data(
            create_scenario_comparison_state(original_active_scenario_state),
            vehicles=75,
        ),
        active_scenario_from_state(updated_active_scenario_state),
    )
    (
        _results_state,
        current_metrics_state,
        current_difference_metrics_state,
    ) = create_scenario_ab_comparison_run_state(
        create_scenario_comparison_state(original_active_scenario_state)
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="single-scenario-run-status-store"),
    )

    (
        results_state,
        metrics_state,
        difference_metrics_state,
        run_status_state,
        status_message,
    ) = callback_function(
        0,
        0,
        updated_active_scenario_state,
        comparison_state,
        current_metrics_state,
        {"status": "up_to_date"},
        {
            "status": "stale",
            "stale_reason": "scenario_a_changed",
            "baseline_active_scenario_state": original_active_scenario_state,
        },
        current_metrics_state,
        current_difference_metrics_state,
    )

    assert results_state is None
    assert metrics_state is None
    assert difference_metrics_state is None
    assert run_status_state == {
        "status": "not_run",
        "stale_reason": None,
        "baseline_active_scenario_state": None,
    }
    assert status_message == "Not run yet."

def test_dashboard_scenario_comparison_visual_callbacks_defer_when_tab_is_inactive():
    app = create_app()
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = create_scenario_comparison_state(active_scenario_state)
    assumptions_callback = _find_callback_function(
        app,
        "scenario-ab-assumptions-summary.children",
    )
    render_callback = _find_callback_function(
        app,
        "scenario-comparison-empty-state-section.style",
    )
    builder_callback = _find_callback_function(
        app,
        "scenario-comparison-builder-expanded-content.style",
    )

    assert (
        assumptions_callback(
            comparison_state,
            OVERVIEW_TAB_VALUE,
        )
        is no_update
    )
    assert (
        render_callback(
            active_scenario_state,
            comparison_state,
            None,
            None,
            {"collapsed": False, "has_run": False},
            None,
            OVERVIEW_TAB_VALUE,
        )
        == (no_update,) * 6
    )
    assert (
        builder_callback(
            active_scenario_state,
            comparison_state,
            {"status": "up_to_date"},
            {"collapsed": True, "has_run": True},
            OVERVIEW_TAB_VALUE,
        )
        == (no_update,) * 6
    )

def test_dashboard_scenario_comparison_state_stays_synchronized_while_visuals_are_deferred(
    monkeypatch,
):
    app = create_app()
    state_callback = _find_callback_function(
        app,
        "scenario-comparison-store.data",
    )
    assumptions_callback = _find_callback_function(
        app,
        "scenario-ab-assumptions-summary.children",
    )
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.UNCONTROLLED.value,
    )
    comparison_state = create_scenario_comparison_state(active_scenario_state)

    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="scenario-b-vehicles-input"),
    )

    next_state, *_rest = state_callback(
        active_scenario_state,
        COMPARISON_SOURCE_MODIFIED_COPY,
        0,
        DEFAULT_SCENARIO_PRESET_ID,
        75,
        comparison_state["scenario_b"]["charger_count"],
        comparison_state["scenario_b"]["charger_power"],
        comparison_state["scenario_b"]["grid_capacity"],
        comparison_state,
    )

    assert next_state["scenario_b"]["vehicles"] == 75
    assert (
        assumptions_callback(next_state, OVERVIEW_TAB_VALUE)
        is no_update
    )
    visible_text = " ".join(
        _collect_text(
            assumptions_callback(
                next_state,
                SCENARIO_COMPARISON_TAB_VALUE,
            )
        )
    )
    assert "Number of vehicles" in visible_text

def test_dashboard_scenario_ab_selected_section_updates_on_card_click(
    monkeypatch,
):
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "scenario-ab-selected-section-store.data",
    )
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = update_scenario_b_in_comparison_data(
        create_scenario_comparison_state(active_scenario_state),
        vehicles=75,
    )
    _results_state, metrics_state, difference_metrics_state = (
        create_scenario_ab_comparison_run_state(comparison_state)
    )
    monkeypatch.setattr(
        dashboard_callback_registration_module,
        "ctx",
        SimpleNamespace(
            triggered_id={
                "type": "scenario-ab-section-select",
                "section_id": "queueing",
            }
        ),
    )

    selected_section_id = callback_function(
        [0, 0, 1, 0, 0],
        active_scenario_state,
        comparison_state,
        metrics_state,
        difference_metrics_state,
        None,
        SCENARIO_COMPARISON_TAB_VALUE,
    )

    assert selected_section_id == "queueing"

def test_dashboard_scenario_ab_selected_section_preserves_selection_when_results_turn_stale(
    monkeypatch,
):
    app = create_app()
    callback_function = _find_callback_function(
        app,
        "scenario-ab-selected-section-store.data",
    )
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = update_scenario_b_in_comparison_data(
        create_scenario_comparison_state(active_scenario_state),
        vehicles=75,
    )
    _results_state, metrics_state, difference_metrics_state = (
        create_scenario_ab_comparison_run_state(comparison_state)
    )
    monkeypatch.setattr(
        dashboard_callback_registration_module,
        "ctx",
        SimpleNamespace(triggered_id="scenario-comparison-store"),
    )

    selected_section_id = callback_function(
        [0, 0, 0, 0, 0],
        active_scenario_state,
        comparison_state,
        metrics_state,
        difference_metrics_state,
        "grid",
        SCENARIO_COMPARISON_TAB_VALUE,
    )

    assert selected_section_id == "grid"

def test_dashboard_registers_scenario_ab_simulation_callbacks():
    app = create_app()
    callback_keys = " ".join(app.callback_map)

    assert "scenario-ab-assumptions-summary.children" in callback_keys
    assert "scenario-ab-selected-section-store.data" in callback_keys
    assert "scenario-comparison-empty-state-section.style" in callback_keys
    assert "scenario-comparison-empty-state.children" in callback_keys
    assert "scenario-ab-executive-summary-section.style" in callback_keys
    assert "scenario-ab-simulation-results-store.data" in callback_keys
    assert "scenario-ab-metrics-store.data" in callback_keys
    assert "scenario-ab-difference-metrics-store.data" in callback_keys
    assert "scenario-comparison-builder-ui-store.data" in callback_keys
    assert "scenario-comparison-edit-scroll-trigger.data" in callback_keys
    assert "scenario-ab-simulation-status.children" in callback_keys
    assert "scenario-ab-executive-summary-cards.children" in callback_keys
    assert "scenario-ab-comparison-table-section.style" in callback_keys
    assert "scenario-ab-comparison-table.children" in callback_keys
    assert "scenario-b-template-details.children" in callback_keys
    assert "scenario-comparison-builder-expanded-content.style" in callback_keys
    assert "scenario-comparison-builder-collapsed-bar.style" in callback_keys
    assert "scenario-comparison-collapsed-title.children" in callback_keys
    assert "scenario-comparison-edit-scroll-effect.children" in callback_keys

    run_callback_key = next(
        key
        for key in app.callback_map
        if "scenario-ab-simulation-results-store.data" in key
    )
    callback_inputs = app.callback_map[run_callback_key]["inputs"]
    callback_state = app.callback_map[run_callback_key]["state"]

    assert {
        "id": "run-scenario-ab-comparison-button",
        "property": "n_clicks",
    } in callback_inputs
    assert {
        "id": "rerun-scenario-ab-comparison-button",
        "property": "n_clicks",
    } in callback_inputs
    assert {
        "id": "active-scenario-store",
        "property": "data",
    } in callback_inputs
    assert {
        "id": "scenario-comparison-store",
        "property": "data",
    } in callback_inputs
    assert {
        "id": "active-metrics-store",
        "property": "data",
    } in callback_inputs
    assert {
        "id": "single-scenario-run-status-store",
        "property": "data",
    } in callback_inputs

    render_callback_key = next(
        key
        for key in app.callback_map
        if "scenario-ab-comparison-table.children" in key
    )
    render_callback_inputs = app.callback_map[render_callback_key]["inputs"]

    assert {
        "id": "active-scenario-store",
        "property": "data",
    } in render_callback_inputs
    assert {
        "id": "scenario-comparison-store",
        "property": "data",
    } in render_callback_inputs
    assert {
        "id": "scenario-ab-metrics-store",
        "property": "data",
    } in render_callback_inputs
    assert {
        "id": "scenario-ab-difference-metrics-store",
        "property": "data",
    } in render_callback_inputs
    assert {
        "id": "scenario-comparison-builder-ui-store",
        "property": "data",
    } in render_callback_inputs
    assert {
        "id": "scenario-ab-selected-section-store",
        "property": "data",
    } in render_callback_inputs
    assert {
        "id": "dashboard-tabs",
        "property": "value",
    } in render_callback_inputs

    builder_ui_callback_key = next(
        key
        for key in app.callback_map
        if "scenario-comparison-builder-expanded-content.style" in key
    )
    builder_ui_callback_inputs = app.callback_map[builder_ui_callback_key]["inputs"]
    assert {
        "id": "scenario-comparison-builder-ui-store",
        "property": "data",
    } in builder_ui_callback_inputs
    assert {
        "id": "dashboard-tabs",
        "property": "value",
    } in builder_ui_callback_inputs

    builder_state_callback_key = next(
        key
        for key in app.callback_map
        if "scenario-comparison-builder-ui-store.data" in key
        and "scenario-comparison-edit-scroll-trigger.data" in key
    )
    builder_state_callback_state = app.callback_map[builder_state_callback_key][
        "state"
    ]
    assert {
        "id": "scenario-comparison-edit-scroll-trigger",
        "property": "data",
    } in builder_state_callback_state

    template_details_callback_key = next(
        key
        for key in app.callback_map
        if "scenario-b-template-details.children" in key
    )
    template_details_callback_inputs = app.callback_map[template_details_callback_key][
        "inputs"
    ]

    assert {
        "id": "scenario-b-template-selector",
        "property": "value",
    } in template_details_callback_inputs
    assert {
        "id": "dashboard-tabs",
        "property": "value",
    } in template_details_callback_inputs

    assumptions_callback_key = next(
        key
        for key in app.callback_map
        if "scenario-ab-assumptions-summary.children" in key
    )
    assumptions_callback_inputs = app.callback_map[assumptions_callback_key]["inputs"]

    assert {
        "id": "scenario-comparison-store",
        "property": "data",
    } in assumptions_callback_inputs
    assert {
        "id": "dashboard-tabs",
        "property": "value",
    } in assumptions_callback_inputs

def test_dashboard_scenario_comparison_edit_mode_raises_scroll_trigger(
    monkeypatch,
):
    app = create_app()
    callback = _find_callback_function(
        app,
        "scenario-comparison-builder-ui-store.data",
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="edit-scenario-comparison-button"),
    )

    builder_ui_state, scroll_trigger = callback(
        0,
        0,
        1,
        {"status": "up_to_date"},
        {"collapsed": True, "has_run": True},
        2,
        {"scenario_a": {}, "scenario_b": {}},
    )

    assert builder_ui_state == {
        "collapsed": False,
        "has_run": True,
    }
    assert scroll_trigger == 3

def test_dashboard_scenario_comparison_run_request_collapses_builder(
    monkeypatch,
):
    app = create_app()
    callback = _find_callback_function(
        app,
        "scenario-comparison-builder-ui-store.data",
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="run-scenario-ab-comparison-button"),
    )

    builder_ui_state, scroll_trigger = callback(
        1,
        0,
        0,
        {"status": "stale"},
        {"collapsed": False, "has_run": False},
        2,
        {"scenario_a": {}, "scenario_b": {}},
    )

    assert builder_ui_state == {
        "collapsed": True,
        "has_run": True,
    }
    assert scroll_trigger is no_update

def test_dashboard_scenario_comparison_error_reopens_builder_after_failed_run(
    monkeypatch,
):
    app = create_app()
    callback = _find_callback_function(
        app,
        "scenario-comparison-builder-ui-store.data",
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="scenario-comparison-run-status-store"),
    )

    builder_ui_state, scroll_trigger = callback(
        1,
        0,
        0,
        {"status": "error"},
        {"collapsed": True, "has_run": True},
        2,
        {"scenario_a": {}, "scenario_b": {}},
    )

    assert builder_ui_state == {
        "collapsed": False,
        "has_run": True,
    }
    assert scroll_trigger is no_update

def test_dashboard_scenario_comparison_reset_reopens_builder_after_new_baseline_run(
    monkeypatch,
):
    app = create_app()
    callback = _find_callback_function(
        app,
        "scenario-comparison-builder-ui-store.data",
    )
    monkeypatch.setattr(
        dashboard_callbacks_module,
        "ctx",
        SimpleNamespace(triggered_id="scenario-comparison-run-status-store"),
    )

    builder_ui_state, scroll_trigger = callback(
        1,
        0,
        0,
        {"status": "not_run"},
        {"collapsed": True, "has_run": True},
        2,
        {"scenario_a": {}, "scenario_b": {}},
    )

    assert builder_ui_state == {
        "collapsed": False,
        "has_run": False,
    }
    assert scroll_trigger is no_update

