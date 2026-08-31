from tests.helpers import *  # noqa: F401,F403

def test_dashboard_app_initializes_layout_and_callbacks():
    app = create_app()

    assert app.layout is not None
    assert len(app.callback_map) > 0
    assert _find_component_by_id(app.layout, "dashboard-tabs") is not None
    assert _find_component_by_class_name(app.layout, "app-sidebar") is not None
    assert _find_component_by_id(app.layout, "dashboard-graph-resize-effect") is not None

def test_dashboard_layout_displays_default_scenario_values():
    app = create_app()

    visible_text = " ".join(_collect_text(app.layout))
    scenario_details = _find_component_by_id(app.layout, "scenario-preset-details")
    scenario_details_text = " ".join(_collect_text(scenario_details))
    overview_kpi_cards = _find_component_by_id(app.layout, "overview-kpi-cards")
    overview_smart_charging_preview = _find_component_by_id(
        app.layout,
        "overview-smart-charging-preview",
    )

    assert "EV Charging Demonstrator" in visible_text
    assert "Scenario Type" in visible_text
    assert "Scenario Details" not in visible_text
    assert "Heavy-duty preset" not in scenario_details_text
    assert (
        "Depot-style heavy-duty charging scenario used as the MVP reference configuration."
        in scenario_details_text
    )
    assert (
        "Fleet vehicles begin arriving near the start of the charging-allowed window."
        in scenario_details_text
    )
    assert "About this scenario" not in scenario_details_text
    assert "Key Assumptions" not in scenario_details_text
    assert "Number of vehicles: 50" not in scenario_details_text
    assert "Daily energy per vehicle: 150 kWh" not in scenario_details_text
    assert "Charger count: 10" not in scenario_details_text
    assert "Electricity price (\u20ac/kWh)" not in visible_text
    assert "Flat electricity price assumption: EUR 0.15/kWh." not in visible_text
    assert "17:00 - 06:00" in visible_text
    assert "Executive Recommendation" not in visible_text
    assert _find_component_by_id(app.layout, "overview-scenario-status-section") is None
    assert _find_component_by_id(app.layout, "overview-decision-messages-section") is None
    assert overview_kpi_cards is not None
    assert len(overview_kpi_cards.children) == 4
    assert "Scenario Outcome" in visible_text
    assert "Peak Load" in visible_text
    assert "Grid Connection Need" in visible_text
    assert "Smart Charging Impact" in visible_text
    assert "Charger Expansion Need" in visible_text
    assert " ".join(_collect_text(overview_kpi_cards)).count("Not run yet") == 4
    assert "Infrastructure Status" in visible_text
    assert "Run the simulation to generate an infrastructure status." in (
        visible_text
    )
    assert "Decision Summary:" in visible_text
    assert "Constraint Diagnosis:" in visible_text
    assert "Planning Impact:" in visible_text
    assert "Recommended Planning Focus:" in visible_text
    assert "Connection Capacity Planning" in visible_text
    assert "Charger Availability" in visible_text
    assert "Simulated Peak Load" in visible_text
    assert "Required Connection Capacity" in visible_text
    assert "Recommended Connection Capacity" in visible_text
    assert "Peak Capacity Margin" in visible_text
    assert "Peak Charger Utilization" in visible_text
    assert "Peak Occupied Chargers" in visible_text
    assert "Maximum Queue Length" in visible_text
    assert "Vehicles Not Started" in visible_text
    assert "Charger Planning Recommendation" not in visible_text
    assert "Grid Asset Summary" not in visible_text
    assert "Charger Pressure During Charging Window" in visible_text
    assert "Connection Capacity Exceeded" not in visible_text
    assert "Average Charger Utilization" not in visible_text
    assert "Average Occupied Chargers" not in visible_text
    assert "Required Charger Count" not in visible_text
    assert "Waiting target:" not in visible_text
    assert "Current:" not in visible_text
    assert "Required:" not in visible_text
    assert "Charging Strategy Comparison" in visible_text
    assert "Executive KPI Summary" in visible_text
    assert "Smart Charging Executive KPIs" in visible_text
    assert "Peak Load" in visible_text
    assert "Required Connection Capacity" in visible_text
    assert "Peak Transformer Loading" in visible_text
    assert "Service Impact" in visible_text
    assert "Power Quality Impact" in visible_text
    assert "Grid / Infrastructure Status" in visible_text
    assert "Peak Load Reduction" not in visible_text
    assert "Required Connection Capacity Reduction" not in visible_text
    assert "Peak Transformer Loading Reduction" not in visible_text
    assert "Capacity & Grid" not in visible_text
    assert "Charging Performance" in visible_text
    assert "Power Quality" in visible_text
    assert "Infrastructure recommendation unchanged" not in visible_text
    assert "Technical Details" in visible_text
    assert "No queues formed during the simulation." in visible_text
    assert "Overall PQ Risk Over Time" in visible_text
    assert "Run the simulation to review additional technical comparison details." in (
        visible_text
    )
    assert "Overall PQ Risk Over Time" in visible_text
    assert "Scenario Comparison" in visible_text
    assert "Compare" in visible_text
    assert "Edit Comparison" in visible_text
    assert "Scenario A vs Scenario B" in visible_text
    assert "Reset from Scenario A" in visible_text
    assert (
        "Scenario B is ready."
        in visible_text
    )
    assert "No comparison changes yet." in visible_text
    assert "Run comparison" in visible_text
    assert "View details" in visible_text
    assert (
        "Results appear below after you run the comparison."
        in visible_text
    )
    assert "Load Profile" not in visible_text
    assert "Capacity vs Load" in visible_text
    assert "Connection Capacity Planning" in visible_text
    assert "Run the simulation to explore connection-capacity alternatives." in visible_text
    assert (
        "Run the simulation to review modeled transformer and feeder loading "
        "against configured asset ratings and connection-capacity pressure."
        in visible_text
    )
    assert "Grid Loading Indicators" in visible_text
    assert "Power Quality Indicators" in visible_text
    assert "Transformer Loading Over Time" in visible_text
    assert "Harmonic Risk Over Time" in visible_text
    assert "Current Imbalance Over Time" in visible_text
    assert "Phase Load Over Time" in visible_text
    assert "Feeder Loading" in visible_text
    assert "PQ indicators are simplified scenario-based risk estimates" in visible_text
    assert "not engineering-grade measurements or compliance results" in (
        visible_text
    )
    assert "Key Findings" not in visible_text
    assert (
        "Run the simulation to compare peak load under uncontrolled and Smart Charging."
        not in visible_text
    )
    assert overview_smart_charging_preview is not None
    overview_smart_charging_text = " ".join(
        _collect_text(overview_smart_charging_preview)
    )
    assert "Peak Reduction" in overview_smart_charging_text
    assert "Uncontrolled" in overview_smart_charging_text
    assert "Smart Charging" in overview_smart_charging_text
    assert overview_smart_charging_text.count("Not run yet") == 3
    assert "Flat electricity price assumption: EUR 0.15/kWh." not in visible_text
    assert (
        "A compact view of delivered load, requested demand, and configured "
        "capacity to highlight headroom or exceedances." not in visible_text
    )
    assert "Energy and Cost Summary" not in visible_text
    assert "Cost Assumption" not in visible_text
    assert "Comparison Summary" not in visible_text
    assert "Simulation Insights" not in visible_text
    assert "Delivered Energy" not in visible_text
    assert "Run the simulation to evaluate the flat-price cost rule." not in visible_text

    active_scenario_store = _find_component_by_id(
        app.layout,
        "active-scenario-store",
    )
    assert active_scenario_store is not None
    assert active_scenario_store.data["schema_version"] == (
        ACTIVE_SCENARIO_STATE_SCHEMA_VERSION
    )
    assert active_scenario_store.data["preset"]["preset_id"] == (
        DEFAULT_SCENARIO_PRESET_ID
    )
    assert active_scenario_store.data["preset"]["is_modified"] is False
    assert active_scenario_store.data["metadata"]["name"] == "Heavy-duty"
    assert active_scenario_store.data["parameters"]["charging_strategy"] == (
        ChargingStrategy.UNCONTROLLED.value
    )
    scenario_builder_store = _find_component_by_id(
        app.layout,
        "scenario-builder-store",
    )
    assert scenario_builder_store is not None
    assert scenario_builder_store.data == active_scenario_store.data
    scenario_builder_feedback_store = _find_component_by_id(
        app.layout,
        "scenario-builder-feedback-store",
    )
    assert scenario_builder_feedback_store is not None
    assert scenario_builder_feedback_store.data == {
        "action": "idle",
        "overwrote_modified_values": False,
        "validation_message": "",
    }
    active_simulation_results_store = _find_component_by_id(
        app.layout,
        "active-simulation-results-store",
    )
    assert active_simulation_results_store is not None
    assert active_simulation_results_store.data is None
    active_metrics_store = _find_component_by_id(
        app.layout,
        "active-metrics-store",
    )
    assert active_metrics_store is not None
    assert active_metrics_store.data is None
    active_capacity_sensitivity_store = _find_component_by_id(
        app.layout,
        "active-capacity-sensitivity-store",
    )
    assert active_capacity_sensitivity_store is not None
    assert active_capacity_sensitivity_store.data is None
    single_scenario_run_status_store = _find_component_by_id(
        app.layout,
        "single-scenario-run-status-store",
    )
    assert single_scenario_run_status_store is not None
    assert single_scenario_run_status_store.data == {"status": "not_run"}
    scenario_comparison_store = _find_component_by_id(
        app.layout,
        "scenario-comparison-store",
    )
    assert scenario_comparison_store is not None
    assert scenario_comparison_store.data["comparison_source"] == (
        COMPARISON_SOURCE_MODIFIED_COPY
    )
    assert scenario_comparison_store.data["selected_template"] is None
    assert (
        scenario_comparison_store.data["scenario_a"]
        == scenario_comparison_store.data["scenario_b"]
    )
    scenario_ab_results_store = _find_component_by_id(
        app.layout,
        "scenario-ab-simulation-results-store",
    )
    assert scenario_ab_results_store is not None
    assert scenario_ab_results_store.data is None
    scenario_ab_metrics_store = _find_component_by_id(
        app.layout,
        "scenario-ab-metrics-store",
    )
    assert scenario_ab_metrics_store is not None
    assert scenario_ab_metrics_store.data is None
    scenario_ab_difference_metrics_store = _find_component_by_id(
        app.layout,
        "scenario-ab-difference-metrics-store",
    )
    assert scenario_ab_difference_metrics_store is not None
    assert scenario_ab_difference_metrics_store.data is None
    scenario_comparison_run_status_store = _find_component_by_id(
        app.layout,
        "scenario-comparison-run-status-store",
    )
    assert scenario_comparison_run_status_store is not None
    assert scenario_comparison_run_status_store.data == {"status": "not_run"}
    scenario_comparison_builder_ui_store = _find_component_by_id(
        app.layout,
        "scenario-comparison-builder-ui-store",
    )
    assert scenario_comparison_builder_ui_store is not None
    assert scenario_comparison_builder_ui_store.data == {
        "collapsed": False,
        "has_run": False,
    }
    scenario_comparison_edit_scroll_trigger = _find_component_by_id(
        app.layout,
        "scenario-comparison-edit-scroll-trigger",
    )
    assert scenario_comparison_edit_scroll_trigger is not None
    assert scenario_comparison_edit_scroll_trigger.data == 0
    assert (
        _find_component_by_id(
            app.layout,
            "scenario-comparison-edit-scroll-effect",
        )
        is not None
    )
    duplicate_button = _find_component_by_id(
        app.layout,
        "duplicate-scenario-b-button",
    )
    assert duplicate_button is not None
    assert duplicate_button.children == "Reset from Scenario A"
    comparison_source_selector = _find_component_by_id(
        app.layout,
        "comparison-source-selector",
    )
    assert comparison_source_selector is not None
    assert comparison_source_selector.value == COMPARISON_SOURCE_MODIFIED_COPY
    assert [option["value"] for option in comparison_source_selector.options] == [
        COMPARISON_SOURCE_MODIFIED_COPY,
        COMPARISON_SOURCE_TEMPLATE,
    ]
    assert (
        " ".join(_collect_text(comparison_source_selector.options[0]["label"]))
        == "Modify current scenario"
    )
    assert (
        " ".join(_collect_text(comparison_source_selector.options[1]["label"]))
        == "Predefined template"
    )
    scenario_b_template_selector = _find_component_by_id(
        app.layout,
        "scenario-b-template-selector",
    )
    assert scenario_b_template_selector is not None
    assert scenario_b_template_selector.value == DEFAULT_SCENARIO_PRESET_ID
    assert [option["label"] for option in scenario_b_template_selector.options] == [
        "Heavy-duty",
        "Public Fast Charging",
        "Workplace Charging",
        "Constrained Heavy-Duty Peak Shaving",
        "Charger-Limited Depot",
        "Concentrated-Arrival Workplace Charging",
        "PQ-Sensitive AC Charging",
    ]
    comparison_status = _find_component_by_id(
        app.layout,
        "scenario-comparison-status",
    )
    assert comparison_status is not None
    assumptions_section = _find_component_by_id(
        app.layout,
        "scenario-ab-assumptions-section",
    )
    assert assumptions_section is not None
    assumptions_summary = _find_component_by_id(
        app.layout,
        "scenario-ab-assumptions-summary",
    )
    assert assumptions_summary is not None
    scenario_ab_executive_summary_section = _find_component_by_id(
        app.layout,
        "scenario-ab-executive-summary-section",
    )
    assert scenario_ab_executive_summary_section is not None
    assert scenario_ab_executive_summary_section.style["display"] == "none"
    assert scenario_ab_executive_summary_section.style["--dashboard-widget-span-desktop"] == "12"
    scenario_ab_executive_summary_text = " ".join(
        _collect_text(scenario_ab_executive_summary_section)
    )
    assert "Headline Comparison KPIs" in scenario_ab_executive_summary_text
    scenario_ab_executive_summary_cards = _find_component_by_id(
        app.layout,
        "scenario-ab-executive-summary-cards",
    )
    assert scenario_ab_executive_summary_cards is not None
    assert len(scenario_ab_executive_summary_cards.children) == 6
    executive_summary_text = " ".join(
        _collect_text(scenario_ab_executive_summary_cards)
    )
    assert "Peak Load" in executive_summary_text
    assert "Capacity Utilization" in executive_summary_text
    assert "Overall PQ Risk" in executive_summary_text
    comparison_empty_state_section = _find_component_by_id(
        app.layout,
        "scenario-comparison-empty-state-section",
    )
    assert comparison_empty_state_section is not None
    collapsed_bar = _find_component_by_id(
        app.layout,
        "scenario-comparison-builder-collapsed-bar",
    )
    assert collapsed_bar is not None
    assert collapsed_bar.style["position"] == "sticky"
    assert collapsed_bar.style["top"] == "0.5rem"
    assert (
        collapsed_bar.style["gridTemplateColumns"] == "minmax(0, 1fr) auto"
    )
    assert collapsed_bar.style["display"] == "none"
    assert collapsed_bar.style["display"] == "none"
    comparison_empty_state = _find_component_by_id(
        app.layout,
        "scenario-comparison-empty-state",
    )
    assert comparison_empty_state is not None
    scenario_b_editor = _find_component_by_id(
        app.layout,
        "scenario-b-editor-section",
    )
    assert scenario_b_editor is not None
    assert scenario_b_editor.style["display"] == "block"
    scenario_b_validation_message = _find_component_by_id(
        app.layout,
        "scenario-b-validation-message",
    )
    assert scenario_b_validation_message is not None
    scenario_b_template_section = _find_component_by_id(
        app.layout,
        "scenario-b-template-section",
    )
    assert scenario_b_template_section is not None
    assert scenario_b_template_section.style["display"] == "none"
    scenario_b_template_details = _find_component_by_id(
        app.layout,
        "scenario-b-template-details",
    )
    assert scenario_b_template_details is not None
    template_details_text = " ".join(_collect_text(scenario_b_template_details))
    assert "View details" in template_details_text
    assert "3 key assumptions" in template_details_text
    assert "6 default parameters" in template_details_text
    assumptions_summary_text = " ".join(_collect_text(assumptions_summary))
    assert "No comparison changes yet." in assumptions_summary_text
    scenario_ab_run_button = _find_component_by_id(
        app.layout,
        "run-scenario-ab-comparison-button",
    )
    assert scenario_ab_run_button is not None
    assert scenario_ab_run_button.children == "Run comparison"
    scenario_ab_status = _find_component_by_id(
        app.layout,
        "scenario-ab-simulation-status",
    )
    assert scenario_ab_status is not None
    assert (
        "Not run yet."
        in " ".join(_collect_text(scenario_ab_status))
    )
    scenario_ab_table_section = _find_component_by_id(
        app.layout,
        "scenario-ab-comparison-table-section",
    )
    assert scenario_ab_table_section is not None
    assert scenario_ab_table_section.style["display"] == "none"
    scenario_ab_table = _find_component_by_id(
        app.layout,
        "scenario-ab-comparison-table",
    )
    assert scenario_ab_table is not None
    comparison_chart = _find_component_by_id(
        app.layout,
        "strategy-comparison-load-profile-chart",
    )
    assert comparison_chart is not None
    assert comparison_chart.style == {
        "height": "420px",
        "width": "100%",
        "minWidth": "0",
    }
    smart_charging_comparison_cards = _find_component_by_id(
        app.layout,
        "smart-charging-comparison-summary-cards",
    )
    assert smart_charging_comparison_cards is not None
    assert len(smart_charging_comparison_cards.children) == 6
    comparison_cards = _find_component_by_id(app.layout, "comparison-summary-cards")
    assert comparison_cards is None
    charger_availability_comparison_table = _find_component_by_id(
        app.layout,
        "charger-availability-comparison-table",
    )
    assert charger_availability_comparison_table is None
    charging_performance_comparison_table = _find_component_by_id(
        app.layout,
        "charging-performance-comparison-table",
    )
    assert charging_performance_comparison_table is not None
    strategy_comparison_occupancy_chart = _find_component_by_id(
        app.layout,
        "strategy-comparison-occupancy-chart",
    )
    assert strategy_comparison_occupancy_chart is not None
    assert strategy_comparison_occupancy_chart.style == {
        "height": "420px",
        "width": "100%",
        "minWidth": "0",
    }
    strategy_comparison_queue_chart = _find_component_by_id(
        app.layout,
        "strategy-comparison-queue-chart",
    )
    assert strategy_comparison_queue_chart is not None
    assert strategy_comparison_queue_chart.style == {
        "height": "420px",
        "width": "100%",
        "minWidth": "0",
    }
    strategy_comparison_pq_chart = _find_component_by_id(
        app.layout,
        "strategy-comparison-pq-risk-chart",
    )
    assert strategy_comparison_pq_chart is not None
    assert strategy_comparison_pq_chart.style == {
        "height": "420px",
        "width": "100%",
        "minWidth": "0",
    }
    power_quality_comparison_table = _find_component_by_id(
        app.layout,
        "power-quality-comparison-table",
    )
    assert power_quality_comparison_table is not None
    capacity_planning_comparison_table = _find_component_by_id(
        app.layout,
        "capacity-planning-comparison-table",
    )
    assert capacity_planning_comparison_table is None
    capacity_planning_cards = _find_component_by_id(
        app.layout,
        "capacity-planning-kpi-cards",
    )
    assert capacity_planning_cards is not None
    assert len(capacity_planning_cards.children) == 4
    charger_availability_cards = _find_component_by_id(
        app.layout,
        "charger-availability-kpi-cards",
    )
    assert charger_availability_cards is not None
    assert len(charger_availability_cards.children) == 4
    charger_availability_text = " ".join(_collect_text(charger_availability_cards))
    assert "Peak Charger Utilization" in charger_availability_text
    assert "Peak Occupied Chargers" in charger_availability_text
    assert "Maximum Queue Length" in charger_availability_text
    assert "Vehicles Not Started" in charger_availability_text
    assert "Average Charger Utilization" not in charger_availability_text
    assert "Average Occupied Chargers" not in charger_availability_text
    assert "Average Waiting Time" not in charger_availability_text
    assert "Required Charger Count" not in charger_availability_text
    infrastructure_summary = _find_component_by_id(
        app.layout,
        "infrastructure-summary",
    )
    assert infrastructure_summary is not None
    grid_loading_cards = _find_component_by_id(
        app.layout,
        "grid-loading-kpi-cards",
    )
    assert grid_loading_cards is not None
    assert len(grid_loading_cards.children) == 5
    grid_loading_status = _find_component_by_id(
        app.layout,
        "grid-loading-status",
    )
    assert grid_loading_status is not None
    power_quality_cards = _find_component_by_id(
        app.layout,
        "power-quality-kpi-cards",
    )
    assert power_quality_cards is not None
    assert len(power_quality_cards.children) == 6
    power_quality_status = _find_component_by_id(
        app.layout,
        "power-quality-status",
    )
    assert power_quality_status is not None
    harmonic_risk_chart = _find_component_by_id(
        app.layout,
        "harmonic-risk-chart",
    )
    assert harmonic_risk_chart is not None
    assert harmonic_risk_chart.style == {
        "height": "420px",
        "width": "100%",
        "minWidth": "0",
    }
    current_imbalance_chart = _find_component_by_id(
        app.layout,
        "current-imbalance-chart",
    )
    assert current_imbalance_chart is not None
    assert current_imbalance_chart.style == {
        "height": "420px",
        "width": "100%",
        "minWidth": "0",
    }
    phase_load_chart = _find_component_by_id(
        app.layout,
        "phase-load-chart",
    )
    assert phase_load_chart is not None
    assert phase_load_chart.style == {
        "height": "420px",
        "width": "100%",
        "minWidth": "0",
    }
    assert _find_component_by_id(app.layout, "grid-asset-planning-status") is None
    assert _find_component_by_id(app.layout, "charger-planning-status") is None
    service_pressure_chart = _find_component_by_id(
        app.layout,
        "service-pressure-chart",
    )
    assert service_pressure_chart is not None
    assert service_pressure_chart.style == {
        "height": "360px",
        "width": "100%",
        "minWidth": "0",
    }
    transformer_loading_chart = _find_component_by_id(
        app.layout,
        "transformer-loading-chart",
    )
    assert transformer_loading_chart is not None
    assert transformer_loading_chart.style == {
        "height": "420px",
        "width": "100%",
        "minWidth": "0",
    }
    power_capacity_chart = _find_component_by_id(
        app.layout,
        "power-capacity-chart",
    )
    assert power_capacity_chart is not None
    assert power_capacity_chart.style == {
        "height": "420px",
        "width": "100%",
        "minWidth": "0",
    }
    comparison_table = _find_component_by_id(app.layout, "detailed-comparison-table")
    assert comparison_table is not None
    capacity_sensitivity_table = _find_component_by_id(
        app.layout,
        "capacity-sensitivity-table",
    )
    assert capacity_sensitivity_table is not None
    feeder_summary_section = _find_component_by_id(
        app.layout,
        "feeder-summary-section",
    )
    assert feeder_summary_section is not None
    capacity_vs_load_chart = _find_component_by_id(
        app.layout,
        "capacity-vs-load-chart",
    )
    assert capacity_vs_load_chart is not None
    assert capacity_vs_load_chart.style == {
        "height": "400px",
        "width": "100%",
        "minWidth": "0",
    }

def test_dashboard_layout_places_scenario_builder_in_sidebar():
    app = create_app()

    shell = _find_component_by_class_name(app.layout, "app-shell")
    sidebar = _find_component_by_class_name(app.layout, "app-sidebar")
    sidebar_frame = _find_component_by_class_name(app.layout, "scenario-sidebar-frame")
    sidebar_content = _find_component_by_class_name(
        app.layout,
        "scenario-sidebar-content",
    )
    sidebar_action_area = _find_component_by_class_name(
        app.layout,
        "scenario-sidebar-action-area",
    )
    main_content = _find_component_by_class_name(app.layout, "app-main-content")

    assert shell is not None
    assert sidebar is not None
    assert sidebar_frame is not None
    assert sidebar_content is not None
    assert sidebar_action_area is not None
    assert main_content is not None
    assert getattr(shell, "style", None) is None
    assert getattr(sidebar, "style", None) is None
    assert getattr(main_content, "style", None) is None

    sidebar_text = " ".join(_collect_text(sidebar))
    main_content_text = " ".join(_collect_text(main_content))

    assert "Scenario Inputs" in sidebar_text
    assert "Scenario Comparison" not in sidebar_text
    assert "Scenario B: Alternative Configuration" not in sidebar_text
    assert "Scenario A / B Simulation" not in sidebar_text
    assert "Use the Scenario Comparison tab to configure the comparison scenario " not in sidebar_text
    assert "Run Simulation" in sidebar_text
    assert "Scenario Inputs" not in main_content_text
    assert "Run Simulation" not in main_content_text
    assert "EV Charging Demonstrator" in main_content_text
    assert "Executive KPI Summary" in main_content_text
    assert "Scenario Outcome" in main_content_text
    assert "Grid Connection Need" in main_content_text
    assert "Charger Expansion Need" in main_content_text
    assert "Executive Recommendation" not in main_content_text
    assert "Smart Charging Impact" in main_content_text
    assert "Key Findings" not in main_content_text
    assert "Connection Capacity Planning" in main_content_text
    assert "Charging Strategy Comparison" in main_content_text
    assert "Power Quality Indicators" in main_content_text
    assert "Compare" in main_content_text
    assert "Edit Comparison" in main_content_text
    assert "Scenario A vs Scenario B" in main_content_text
    assert "Scenario B" in main_content_text
    assert "Run comparison" in main_content_text

def test_dashboard_layout_wraps_results_area_in_tabs():
    app = create_app()

    tabs = _find_component_by_id(app.layout, "dashboard-tabs")

    assert tabs is not None
    assert tabs.value == "overview"
    assert len(tabs.children) == 6
    assert [tab.label for tab in tabs.children] == [
        "Overview",
        "Infrastructure",
        "Smart Charging",
        "Grid & Capacity",
        "Power Quality",
        "Scenario Comparison",
    ]

    overview_text = " ".join(
        _collect_text(_find_tab_by_value(tabs, "overview").children)
    )
    infrastructure_text = " ".join(
        _collect_text(_find_tab_by_value(tabs, "infrastructure").children)
    )
    smart_charging_text = " ".join(
        _collect_text(_find_tab_by_value(tabs, "smart-charging").children)
    )
    grid_capacity_text = " ".join(
        _collect_text(_find_tab_by_value(tabs, "grid-capacity").children)
    )
    power_quality_text = " ".join(
        _collect_text(_find_tab_by_value(tabs, "power-quality").children)
    )
    scenario_comparison_text = " ".join(
        _collect_text(_find_tab_by_value(tabs, "scenario-comparison").children)
    )

    assert "Executive KPI Summary" in overview_text
    assert "Scenario Outcome" in overview_text
    assert "Grid Connection Need" in overview_text
    assert "Charger Expansion Need" in overview_text
    assert "Executive Recommendation" not in overview_text
    assert "Key Findings" not in overview_text
    assert "Smart Charging Impact" in overview_text
    assert "Capacity vs Load" in overview_text
    assert "Uncontrolled" in overview_text
    assert "Smart Charging" in overview_text
    assert "Model Assumptions" not in overview_text
    assert "Flat electricity price assumption: EUR 0.15/kWh." not in overview_text
    assert "Energy and Cost Summary" not in overview_text
    assert "Cost Assumption" not in overview_text
    assert "Comparison Summary" not in overview_text
    assert "Simulation Insights" not in overview_text
    assert "Run the simulation to evaluate the flat-price cost rule." not in overview_text
    assert "Charging Strategy Comparison" not in overview_text
    assert "Load Profile" not in overview_text
    assert "Charging Power and Capacity Over Time" not in overview_text
    assert "Scenario A / B Comparison" not in overview_text

    assert "Connection Capacity Planning" in infrastructure_text
    assert "Charger Availability" in infrastructure_text
    assert "Infrastructure Status" in infrastructure_text
    assert "Charger Pressure During Charging Window" in infrastructure_text
    assert "Charger Planning Recommendation" not in infrastructure_text
    assert "Grid Asset Summary" not in infrastructure_text
    assert "Service Pressure Over Time" not in infrastructure_text
    assert "Charger Occupancy Over Time" not in infrastructure_text
    assert "Queue Length Over Time" not in infrastructure_text
    assert "Charger Planning Status" not in infrastructure_text
    assert "Grid Asset Status" not in infrastructure_text
    assert "Load Profile" not in infrastructure_text
    assert "Detailed Comparison" not in infrastructure_text

    assert "Smart Charging Executive KPIs" in smart_charging_text
    assert "Baseline: Uncontrolled Charging. Comparison: Smart Charging." in smart_charging_text
    assert "Charging Strategy Comparison" in smart_charging_text
    assert "Capacity & Grid" not in smart_charging_text
    assert "Charging Performance" in smart_charging_text
    assert "Power Quality" in smart_charging_text
    assert "Infrastructure recommendation unchanged" not in smart_charging_text
    assert "Occupied Chargers Over Time" in smart_charging_text
    assert "Queue Length Over Time" in smart_charging_text
    assert "Technical Details" in smart_charging_text

    assert "Charging Power and Capacity Over Time" in grid_capacity_text
    assert "Load Profile" not in grid_capacity_text
    assert "Capacity vs Load" not in grid_capacity_text
    assert "Connection Capacity Planning" in grid_capacity_text
    assert "Grid Loading Indicators" in grid_capacity_text
    assert "Transformer Loading Over Time" in grid_capacity_text
    assert "Feeder Loading" in grid_capacity_text
    assert "Power Quality Indicators" not in grid_capacity_text
    assert "Harmonic Risk Over Time" not in grid_capacity_text
    assert "Current Imbalance Over Time" not in grid_capacity_text
    assert "Phase Load Over Time" not in grid_capacity_text
    assert "Scenario A / B Comparison" not in grid_capacity_text

    assert "Power Quality Indicators" in power_quality_text
    assert "PQ indicators are simplified scenario-based risk estimates" in power_quality_text
    assert "Harmonic Risk Over Time" in power_quality_text
    assert "Current Imbalance Over Time" in power_quality_text
    assert "Power Quality Summary" not in power_quality_text
    assert "Power Quality Evidence" not in power_quality_text
    assert "Phase Load Context" not in power_quality_text
    assert "Phase Load Over Time" in power_quality_text
    assert "Grid Loading Indicators" not in power_quality_text
    assert "Transformer Loading Over Time" not in power_quality_text
    assert "Feeder Loading" not in power_quality_text
    assert "Charging Power and Capacity Over Time" not in power_quality_text
    assert "Connection Capacity Planning" not in power_quality_text

    assert "Scenario A vs Scenario B" in scenario_comparison_text
    assert "Edit Comparison" in scenario_comparison_text
    assert "Compare" in scenario_comparison_text
    assert "Modify current scenario" not in scenario_comparison_text
    assert "Predefined template" not in scenario_comparison_text
    assert "Scenario B" in scenario_comparison_text
    assert "Run comparison" in scenario_comparison_text
    assert "Reset from Scenario A" in scenario_comparison_text
    assert (
        "Scenario B is ready."
        in scenario_comparison_text
    )
    assert "Difference Overview" not in scenario_comparison_text
    assert "Occupied Chargers Over Time" not in scenario_comparison_text
    assert "Queue Length Over Time" not in scenario_comparison_text
    assert "Overall PQ Risk Over Time" not in scenario_comparison_text
    assert "Executive KPI Summary" not in scenario_comparison_text
    scenario_comparison_panel = _find_tab_by_value(tabs, "scenario-comparison").children
    scenario_comparison_sections = _extract_dashboard_widget_sections(
        scenario_comparison_panel
    )
    assert [
        getattr(section, "id", None)
        for section in scenario_comparison_sections
        if getattr(section, "id", None) != "scenario-ab-selected-section-store"
    ] == [
        "scenario-comparison-builder-section",
        "scenario-ab-executive-summary-section",
        "scenario-ab-comparison-table-section",
    ]

def test_dashboard_grid_and_power_quality_tabs_match_phase_four_contract():
    app = create_app()

    tabs = _find_component_by_id(app.layout, "dashboard-tabs")
    grid_panel = _find_tab_by_value(tabs, "grid-capacity").children
    power_quality_panel = _find_tab_by_value(tabs, "power-quality").children

    assert _extract_section_titles(grid_panel) == [
        "Grid Loading Indicators",
        "Connection Capacity Planning",
        "Feeder Loading",
        "Transformer Loading Over Time",
        "Charging Power and Capacity Over Time",
    ]
    assert _extract_section_titles(power_quality_panel) == [
        "Power Quality Indicators",
        "Harmonic Risk Over Time",
        "Current Imbalance Over Time",
        "Phase Load Over Time",
    ]

def test_dashboard_smart_charging_tab_uses_hero_then_analysis_section_order():
    app = create_app()

    tabs = _find_component_by_id(app.layout, "dashboard-tabs")
    smart_charging_panel = _find_tab_by_value(tabs, "smart-charging").children

    assert [
        getattr(section, "id", None)
        for section in smart_charging_panel.children
        if getattr(section, "id", None) is not None
    ] == [
        "smart-charging-hero-section",
        "smart-charging-main-analysis-section",
        "smart-charging-performance-section",
        "smart-charging-technical-details-section",
    ]

    hero_section = smart_charging_panel.children[0]
    hero_text = " ".join(_collect_text(hero_section))

    assert getattr(hero_section, "className", None) == "smart-charging-hero-section"
    assert "Smart Charging Executive KPIs" in hero_text
    assert "Baseline: Uncontrolled Charging. Comparison: Smart Charging." in hero_text
    assert _find_component_by_id(hero_section, "smart-charging-hero-summary") is not None
    assert _find_component_by_id(
        hero_section,
        "smart-charging-comparison-summary-cards",
    ) is not None

    strategy_section = smart_charging_panel.children[1]
    strategy_text = " ".join(_collect_text(strategy_section))

    assert "Charging Strategy Comparison" in strategy_text
    assert _find_component_by_id(strategy_section, "smart-charging-hero-chart") is not None
    assert _find_component_by_id(
        strategy_section,
        "strategy-comparison-load-profile-chart",
    ) is not None

    for section in smart_charging_panel.children[2:-1]:
        assert "smart-charging-analysis-section" in getattr(
            section,
            "className",
            "",
        )

def test_dashboard_smart_charging_tab_switches_to_comparison_mode_indicator():
    app = create_app()

    callback = _find_callback_function(
        app,
        "charging-strategy-selector-container.style",
    )

    smart_selector_style, smart_mode_style = callback("smart-charging")
    overview_selector_style, overview_mode_style = callback("overview")

    assert smart_selector_style == {"display": "none"}
    assert smart_mode_style == {"display": "block"}
    assert overview_selector_style == {}
    assert overview_mode_style == {"display": "none"}

def test_dashboard_grid_capacity_tab_matches_final_planning_layout_snapshot():
    app = create_app()

    tabs = _find_component_by_id(app.layout, "dashboard-tabs")
    grid_panel = _find_tab_by_value(tabs, "grid-capacity").children
    sections = _extract_dashboard_widget_sections(grid_panel)

    grid_snapshot = [
        {
            "title": sections[0].children[0].children,
            "cards_id": _unwrap_loading_child(sections[0].children[1]).children[0].id,
            "cards_class": _unwrap_loading_child(sections[0].children[1]).children[0].className,
            "card_titles": [
                card.children[0].children
                for card in _unwrap_loading_child(sections[0].children[1]).children[0].children
            ],
            "status_id": _unwrap_loading_child(sections[0].children[1]).children[1].id,
        },
        {
            "title": sections[1].children[0].children,
            "content_id": _unwrap_loading_child(sections[1].children[1]).id,
            "content_text": " ".join(_collect_text(_unwrap_loading_child(sections[1].children[1]))),
        },
        {
            "title": sections[2].children[0].children,
            "content_id": _unwrap_loading_child(sections[2].children[1]).id,
            "content_text": " ".join(_collect_text(_unwrap_loading_child(sections[2].children[1]))),
        },
        {
            "title": sections[3].children[0].children,
            "chart_id": _unwrap_loading_child(sections[3].children[1]).id,
        },
        {
            "title": sections[4].children[0].children,
            "chart_id": _unwrap_loading_child(sections[4].children[1]).id,
        },
    ]

    assert grid_snapshot == [
        {
            "title": "Grid Loading Indicators",
            "cards_id": "grid-loading-kpi-cards",
            "cards_class": "grid-capacity-kpi-grid",
            "card_titles": [
                "Peak Transformer Loading",
                "Transformer Overload Duration",
                "Maximum Transformer Overload",
                "Maximum Feeder Loading",
                "Overloaded Feeders",
            ],
            "status_id": "grid-loading-status",
        },
        {
            "title": "Connection Capacity Planning",
            "content_id": "capacity-sensitivity-table",
            "content_text": (
                "Run the simulation to explore connection-capacity alternatives."
            ),
        },
        {
            "title": "Feeder Loading",
            "content_id": "feeder-summary-section",
            "content_text": (
                "Run the simulation to review modeled transformer and feeder "
                "loading against configured asset ratings and connection-capacity pressure."
            ),
        },
        {
            "title": "Transformer Loading Over Time",
            "chart_id": "transformer-loading-chart",
        },
        {
            "title": "Charging Power and Capacity Over Time",
            "chart_id": "power-capacity-chart",
        },
    ]

def test_dashboard_power_quality_tab_matches_final_planning_layout_snapshot():
    app = create_app()

    tabs = _find_component_by_id(app.layout, "dashboard-tabs")
    power_quality_panel = _find_tab_by_value(tabs, "power-quality").children
    sections = _extract_dashboard_widget_sections(power_quality_panel)

    power_quality_snapshot = [
        {
            "title": sections[0].children[0].children,
            "cards_id": _unwrap_loading_child(sections[0].children[1]).children[0].id,
            "cards_class": _unwrap_loading_child(sections[0].children[1]).children[0].className,
            "card_titles": [
                card.children[0].children
                for card in _unwrap_loading_child(sections[0].children[1]).children[0].children
            ],
            "disclaimer_text": " ".join(_collect_text(_unwrap_loading_child(sections[0].children[1]).children[1])),
            "status_id": _unwrap_loading_child(sections[0].children[1]).children[1].children[1].id,
        },
        {
            "title": sections[1].children[0].children,
            "chart_id": _unwrap_loading_child(sections[1].children[1]).id,
            "desktop_span": sections[1].style["--dashboard-widget-span-desktop"],
        },
        {
            "title": sections[2].children[0].children,
            "chart_id": _unwrap_loading_child(sections[2].children[1]).id,
            "desktop_span": sections[2].style["--dashboard-widget-span-desktop"],
        },
        {
            "title": sections[3].children[0].children,
            "chart_id": _unwrap_loading_child(sections[3].children[1]).id,
            "desktop_span": sections[3].style["--dashboard-widget-span-desktop"],
        },
    ]

    assert power_quality_snapshot == [
        {
            "title": "Power Quality Indicators",
            "cards_id": "power-quality-kpi-cards",
            "cards_class": "power-quality-kpi-grid",
            "card_titles": [
                "Overall PQ Risk",
                "PQ Warnings",
                "Peak Harmonic Risk",
                "Harmonic Risk Duration",
                "Peak Current Imbalance",
                "Current Imbalance Duration",
            ],
            "disclaimer_text": (
                "PQ indicators are simplified scenario-based risk estimates, "
                "not engineering-grade measurements or compliance results. "
                "\u24d8"
            ),
            "status_id": "power-quality-status",
        },
        {
            "title": "Harmonic Risk Over Time",
            "chart_id": "harmonic-risk-chart",
            "desktop_span": "8",
        },
        {
            "title": "Current Imbalance Over Time",
            "chart_id": "current-imbalance-chart",
            "desktop_span": "4",
        },
        {
            "title": "Phase Load Over Time",
            "chart_id": "phase-load-chart",
            "desktop_span": "12",
        },
    ]

def test_dashboard_infrastructure_tab_matches_final_planning_layout_snapshot():
    app = create_app()

    tabs = _find_component_by_id(app.layout, "dashboard-tabs")
    infrastructure_panel = _find_tab_by_value(tabs, "infrastructure").children

    assert _extract_section_titles(infrastructure_panel) == [
        "Connection Capacity Planning",
        "Charger Availability",
        "Infrastructure Status",
        "Charger Pressure During Charging Window",
    ]

    sections = _extract_dashboard_widget_sections(infrastructure_panel)
    infrastructure_snapshot = [
        {
            "title": sections[0].children[0].children,
            "content_id": _unwrap_loading_child(sections[0].children[1]).id,
            "content_class": _unwrap_loading_child(sections[0].children[1]).className,
            "grid_columns": _unwrap_loading_child(sections[0].children[1]).style["gridTemplateColumns"],
            "content_text": " ".join(_collect_text(_unwrap_loading_child(sections[0].children[1]))),
        },
        {
            "title": sections[1].children[0].children,
            "content_id": _unwrap_loading_child(sections[1].children[1]).id,
            "content_class": _unwrap_loading_child(sections[1].children[1]).className,
            "grid_columns": _unwrap_loading_child(sections[1].children[1]).style["gridTemplateColumns"],
            "content_text": " ".join(_collect_text(_unwrap_loading_child(sections[1].children[1]))),
        },
        {
            "title": sections[2].children[0].children,
            "content_id": _unwrap_loading_child(sections[2].children[1]).id,
            "content_text": " ".join(_collect_text(_unwrap_loading_child(sections[2].children[1]))),
        },
        {
            "title": sections[3].children[0].children,
            "content_id": _unwrap_loading_child(sections[3].children[1]).id,
        },
    ]

    assert infrastructure_snapshot == [
        {
            "title": "Connection Capacity Planning",
            "content_id": "capacity-planning-kpi-cards",
            "content_class": "infrastructure-kpi-grid",
            "grid_columns": "repeat(2, minmax(0, 1fr))",
            "content_text": (
                "Simulated Peak Load Not run yet Required Connection Capacity "
                "Not run yet Recommended Connection Capacity Not run yet Peak "
                "Capacity Margin Not run yet"
            ),
        },
        {
            "title": "Charger Availability",
            "content_id": "charger-availability-kpi-cards",
            "content_class": "infrastructure-kpi-grid",
            "grid_columns": "repeat(2, minmax(0, 1fr))",
            "content_text": (
                "Peak Charger Utilization Not run yet Peak Occupied Chargers "
                "Not run yet Maximum Queue Length Not run yet Vehicles Not "
                "Started Not run yet"
            ),
        },
        {
            "title": "Infrastructure Status",
            "content_id": "infrastructure-summary",
            "content_text": (
                "Run the simulation to generate an infrastructure status. "
                "Decision Summary: the infrastructure decision outcome "
                "for the modeled service rule. "
                "Constraint Diagnosis: the dominant modeled planning "
                "constraint. Planning Impact: what the result means for "
                "planning pressure or service risk. Recommended Planning "
                "Focus: the next planning area to review."
            ),
        },
        {
            "title": "Charger Pressure During Charging Window",
            "content_id": "service-pressure-chart",
        },
    ]
    assert sections[2].style["--dashboard-widget-span-desktop"] == "5"
    assert sections[3].style["--dashboard-widget-span-desktop"] == "7"

def test_dashboard_layout_displays_scenario_preset_selector():
    app = create_app()

    selector = _find_component_by_id(app.layout, "scenario-preset-selector")

    assert selector is not None
    assert selector.options == [
        {
            "label": "Heavy-duty",
            "value": DEFAULT_SCENARIO_PRESET_ID,
        },
        {
            "label": "Public Fast Charging",
            "value": PUBLIC_FAST_CHARGING_PRESET_ID,
        },
        {
            "label": "Workplace Charging",
            "value": WORKPLACE_CHARGING_PRESET_ID,
        },
        {
            "label": "Constrained Heavy-Duty Peak Shaving",
            "value": CONSTRAINED_HEAVY_DUTY_PEAK_SHAVING_PRESET_ID,
        },
        {
            "label": "Charger-Limited Depot",
            "value": CHARGER_LIMITED_DEPOT_PRESET_ID,
        },
        {
            "label": "Concentrated-Arrival Workplace Charging",
            "value": CONCENTRATED_ARRIVAL_WORKPLACE_CHARGING_PRESET_ID,
        },
        {
            "label": "PQ-Sensitive AC Charging",
            "value": PQ_SENSITIVE_AC_CHARGING_PRESET_ID,
        },
    ]
    assert selector.value == DEFAULT_SCENARIO_PRESET_ID
    assert selector.clearable is False

def test_dashboard_layout_displays_default_scenario_preset_details():
    app = create_app()

    details = _find_component_by_id(app.layout, "scenario-preset-details")

    assert details is not None
    visible_text = " ".join(_collect_text(details))
    assert "Heavy-duty preset" not in visible_text
    assert "Depot-style heavy-duty charging scenario used as the MVP reference configuration." in visible_text
    assert (
        "Fleet vehicles begin arriving near the start of the charging-allowed window."
        in visible_text
    )
    assert "About this scenario" not in visible_text
    assert "Key Assumptions" not in visible_text
    assert "Number of vehicles: 50" not in visible_text
    assert "Default Parameters" not in visible_text
    assert "Charging window" not in visible_text

def test_sidebar_presentation_configuration_covers_each_group_in_schema_order():
    grouped_field_names = {
        category: [
            field.field_name
            for field in get_sidebar_visible_field_definitions(category)
        ]
        for category in SCENARIO_SIDEBAR_CATEGORY_ORDER
    }

    for category in SCENARIO_SIDEBAR_CATEGORY_ORDER:
        primary_field_names = [
            field.field_name
            for field in get_sidebar_primary_field_definitions(category)
        ]
        advanced_field_names = [
            field.field_name
            for field in get_sidebar_advanced_field_definitions(category)
        ]
        visible_field_names = [
            field.field_name
            for field in get_sidebar_visible_field_definitions(category)
        ]

        assert set(primary_field_names).isdisjoint(advanced_field_names)
        assert visible_field_names == grouped_field_names[category]
        assert set(visible_field_names) == set(primary_field_names + advanced_field_names)

def test_sidebar_presentation_configuration_keeps_power_quality_advanced_only():
    assert get_sidebar_primary_field_definitions("Power Quality") == ()
    assert [
        field.field_name
        for field in get_sidebar_advanced_field_definitions("Power Quality")
    ] == [
        "single_phase_charger_share_percent",
    ]

def test_dashboard_layout_displays_editable_sidebar_parameter_groups():
    app = create_app()

    sidebar = _find_component_by_class_name(app.layout, "app-sidebar")
    action_area = _find_component_by_class_name(
        app.layout,
        "scenario-sidebar-action-area",
    )
    vehicles_input = _find_component_by_id(app.layout, "scenario-field-vehicles-input")
    daily_energy_input = _find_component_by_id(
        app.layout,
        "scenario-field-daily_energy_per_vehicle-input",
    )
    grid_capacity_input = _find_component_by_id(
        app.layout,
        "scenario-field-grid_capacity-input",
    )
    arrival_window_start_input = _find_component_by_id(
        app.layout,
        "scenario-field-arrival_window_start-input",
    )
    arrival_window_end_input = _find_component_by_id(
        app.layout,
        "scenario-field-arrival_window_end-input",
    )
    validation_message = _find_component_by_id(
        app.layout,
        "scenario-input-validation-message",
    )
    status_message = _find_component_by_id(
        app.layout,
        "scenario-builder-status-message",
    )

    assert sidebar is not None
    visible_text = " ".join(_collect_text(sidebar))
    assert "Editable Parameters" in visible_text
    assert "Fleet & Demand" in visible_text
    assert "Charging Infrastructure" in visible_text
    assert "Grid & Capacity" in visible_text
    assert "Operating Pattern" in visible_text
    assert "Power Quality" in visible_text
    assert "Daily energy per vehicle (kWh)" in visible_text
    assert "Request energy variability (%)" in visible_text
    assert "Charger power (kW)" in visible_text
    assert "Grid connection capacity (kW)" in visible_text
    assert "Vehicle arrivals begin" in visible_text
    assert "Vehicle arrivals end" in visible_text
    assert "Number of vehicles (" not in visible_text
    assert "Number of chargers (" not in visible_text
    assert "Feeder count (" not in visible_text
    assert "Planning margin (%)" not in visible_text
    assert "Charger harmonic factor" not in visible_text
    assert "Power-quality phase allocation" not in visible_text
    assert "Feeder allocation shares" not in visible_text
    assert "Arrival mode" not in visible_text

    assert vehicles_input is not None
    assert vehicles_input.type == "number"
    assert vehicles_input.debounce is False
    assert vehicles_input.value == default_scenario.vehicles

    assert daily_energy_input is not None
    assert daily_energy_input.type == "number"
    assert daily_energy_input.value == default_scenario.daily_energy_per_vehicle

    assert grid_capacity_input is not None
    assert grid_capacity_input.type == "number"
    assert grid_capacity_input.value == default_scenario.grid_capacity

    assert arrival_window_start_input is not None
    assert arrival_window_start_input.value == "17:00"
    assert arrival_window_end_input is not None
    assert arrival_window_end_input.value == "17:00"

    assert validation_message is not None
    assert validation_message.style == {"display": "none"}
    assert status_message is not None
    assert status_message.style == {"display": "none"}
    assert action_area is not None
    action_text = " ".join(_collect_text(action_area))
    assert "Run Simulation" in action_text

def test_dashboard_layout_adds_tooltip_icons_only_to_selected_sidebar_fields():
    app = create_app()

    tooltip_triggers = _find_components_by_class_name(
        app.layout,
        "scenario-sidebar-tooltip-trigger",
    )

    tooltip_copy = {
        trigger.to_plotly_json()["props"]["data-tooltip"]
        for trigger in tooltip_triggers
    }
    tooltip_props = [
        trigger.to_plotly_json()["props"]
        for trigger in tooltip_triggers
    ]

    assert len(tooltip_triggers) == 9
    assert {
        "When the site begins allowing vehicles to charge.",
        "When the site stops allowing charging in this scenario.",
        "When vehicles begin arriving and joining the charging queue.",
        "When the modeled arrival period finishes.",
        (
            "Spreads per-request energy across a deterministic low-to-high band "
            "while preserving the same total daily site energy."
        ),
        (
            "Maximum waiting time allowed by the charger-planning service rule. "
            "Higher tolerance allows more modeled queueing before extra chargers "
            "are indicated."
        ),
        (
            "Deterministically spreads per-request deadlines. With window-end "
            "departures some requests leave earlier than the shared end time; "
            "with session dwell, dwell durations vary around the baseline."
        ),
        (
            "Share of chargers modeled as single-phase power-quality sources. "
            "Higher values increase modeled harmonic risk and can concentrate "
            "phase loading depending on phase allocation."
        ),
        (
            "Fixed non-EV load added to EV charging on the transformer at every "
            "timestep. Higher values increase total transformer loading and "
            "overload risk."
        ),
    } == tooltip_copy
    assert all("title" not in props for props in tooltip_props)
    assert all(props["role"] == "button" for props in tooltip_props)

    visible_text = " ".join(_collect_text(app.layout))
    assert "Number of vehicles ⓘ" not in visible_text
    assert "Charger power (kW) ⓘ" not in visible_text

def test_dashboard_layout_uses_per_group_advanced_disclosures():
    app = create_app()

    sidebar_groups = _find_components_by_class_name(
        app.layout,
        "scenario-sidebar-group",
    )
    primary_grids = _find_components_by_class_name(
        app.layout,
        "scenario-sidebar-primary-grid",
    )
    advanced_disclosures = _find_components_by_class_name(
        app.layout,
        "scenario-sidebar-advanced-disclosure",
    )
    advanced_grids = _find_components_by_class_name(
        app.layout,
        "scenario-sidebar-advanced-grid",
    )
    advanced_summaries = _find_components_by_class_name(
        app.layout,
        "scenario-sidebar-advanced-summary",
    )

    assert len(sidebar_groups) == 5
    assert len(primary_grids) == 4
    assert len(advanced_disclosures) == 5
    assert len(advanced_grids) == 5
    assert len(advanced_summaries) == 5
    assert all(summary.children == "Advanced settings" for summary in advanced_summaries)

    power_quality_group = next(
        group
        for group in sidebar_groups
        if group.children[0].children == "Power Quality"
    )
    power_quality_primary_grids = [
        child
        for child in power_quality_group.children[1:]
        if "scenario-sidebar-primary-grid"
        in str(getattr(child, "className", "")).split()
    ]
    power_quality_advanced_disclosures = [
        child
        for child in power_quality_group.children[1:]
        if "scenario-sidebar-advanced-disclosure"
        in str(getattr(child, "className", "")).split()
    ]

    assert power_quality_primary_grids == []
    assert len(power_quality_advanced_disclosures) == 1

def test_dashboard_layout_keeps_advanced_disclosures_ui_only():
    app = create_app()

    advanced_disclosures = _find_components_by_class_name(
        app.layout,
        "scenario-sidebar-advanced-disclosure",
    )
    advanced_summaries = _find_components_by_class_name(
        app.layout,
        "scenario-sidebar-advanced-summary",
    )

    assert all(getattr(disclosure, "id", None) is None for disclosure in advanced_disclosures)
    assert all(getattr(summary, "id", None) is None for summary in advanced_summaries)

def test_dashboard_layout_places_conditional_fields_inside_advanced_sections():
    app = create_app()

    sidebar_groups = _find_components_by_class_name(
        app.layout,
        "scenario-sidebar-group",
    )
    grid_capacity_group = next(
        group
        for group in sidebar_groups
        if group.children[0].children == "Grid & Capacity"
    )
    operating_pattern_group = next(
        group
        for group in sidebar_groups
        if group.children[0].children == "Operating Pattern"
    )
    grid_capacity_advanced_disclosure = next(
        child
        for child in grid_capacity_group.children[1:]
        if "scenario-sidebar-advanced-disclosure"
        in str(getattr(child, "className", "")).split()
    )
    operating_pattern_advanced_disclosure = next(
        child
        for child in operating_pattern_group.children[1:]
        if "scenario-sidebar-advanced-disclosure"
        in str(getattr(child, "className", "")).split()
    )

    assert not _component_contains_descendant_with_id(
        grid_capacity_advanced_disclosure,
        "scenario-field-feeder_allocation_shares-input",
    )
    assert _component_contains_descendant_with_id(
        operating_pattern_advanced_disclosure,
        "scenario-field-session_dwell_minutes-input",
    )

def test_dashboard_layout_displays_hidden_modified_indicator_and_reset_button():
    app = create_app()

    modified_indicator = _find_component_by_id(
        app.layout,
        "scenario-preset-modified-indicator",
    )
    reset_button = _find_component_by_id(app.layout, "reset-scenario-preset-button")

    assert modified_indicator is not None
    assert modified_indicator.style == {"display": "none"}
    assert reset_button is not None
    assert reset_button.n_clicks == 0
    assert reset_button.style["display"] == "none"

def test_dashboard_layout_marks_operating_pattern_grid_for_stable_medium_width_reflow():
    app = create_app()

    sidebar_groups = _find_components_by_class_name(
        app.layout,
        "scenario-sidebar-group",
    )
    operating_pattern_group = next(
        group
        for group in sidebar_groups
        if group.children[0].children == "Operating Pattern"
    )
    primary_grid = next(
        child
        for child in operating_pattern_group.children[1:]
        if "scenario-sidebar-primary-grid"
        in str(getattr(child, "className", "")).split()
    )

    assert "scenario-sidebar-group--operating-pattern" in str(
        getattr(operating_pattern_group, "className", "")
    ).split()
    assert "scenario-sidebar-primary-grid--operating-pattern" in str(
        getattr(primary_grid, "className", "")
    ).split()

def test_dashboard_layout_displays_charging_strategy_selector():
    app = create_app()

    selector_container = _find_component_by_id(
        app.layout,
        "charging-strategy-selector-container",
    )
    selector = _find_component_by_id(app.layout, "charging-strategy-selector")
    comparison_mode_container = _find_component_by_id(
        app.layout,
        "smart-charging-comparison-mode-container",
    )
    comparison_mode_indicator = _find_component_by_id(
        app.layout,
        "smart-charging-comparison-mode-indicator",
    )

    assert selector_container is not None
    assert selector is not None
    assert selector.options == [
        {
            "label": "Uncontrolled Charging",
            "value": ChargingStrategy.UNCONTROLLED.value,
        },
        {
            "label": "Smart Charging",
            "value": ChargingStrategy.SMART.value,
        },
    ]
    assert selector.value == ChargingStrategy.UNCONTROLLED.value
    assert selector.clearable is False
    assert comparison_mode_container is not None
    assert comparison_mode_container.style == {"display": "none"}
    assert comparison_mode_indicator is not None
    visible_text = " ".join(_collect_text(comparison_mode_container))
    assert "Comparison Mode" in visible_text
    assert "Uncontrolled Charging vs Smart Charging" in visible_text
    assert "selected charging strategy remains stored for the single-scenario tabs" in (
        visible_text
    )

def test_dashboard_layout_includes_hidden_scenario_b_edit_controls():
    app = create_app()

    comparison_source_selector = _find_component_by_id(
        app.layout,
        "comparison-source-selector",
    )
    template_selector = _find_component_by_id(
        app.layout,
        "scenario-b-template-selector",
    )
    vehicles_input = _find_component_by_id(app.layout, "scenario-b-vehicles-input")
    charger_count_input = _find_component_by_id(
        app.layout,
        "scenario-b-charger-count-input",
    )
    charger_power_input = _find_component_by_id(
        app.layout,
        "scenario-b-charger-power-input",
    )
    grid_capacity_input = _find_component_by_id(
        app.layout,
        "scenario-b-grid-capacity-input",
    )

    assert comparison_source_selector is not None
    assert comparison_source_selector.value == COMPARISON_SOURCE_MODIFIED_COPY
    assert template_selector is not None
    assert template_selector.value == DEFAULT_SCENARIO_PRESET_ID

    for scenario_b_input in (
        vehicles_input,
        charger_count_input,
        charger_power_input,
        grid_capacity_input,
    ):
        assert scenario_b_input is not None
        assert scenario_b_input.type == "number"
        assert scenario_b_input.debounce is False

    assert vehicles_input.value == default_scenario.vehicles
    assert charger_count_input.value == default_scenario.charger_count
    assert charger_power_input.value == default_scenario.charger_power
    assert grid_capacity_input.value == default_scenario.grid_capacity

    assert vehicles_input.min == 1
    assert vehicles_input.step == 1
    assert charger_count_input.min == 1
    assert charger_count_input.step == 1
    assert charger_power_input.min == 0.1
    assert charger_power_input.step == 0.1
    assert grid_capacity_input.min == 0.1
    assert grid_capacity_input.step == 0.1

def test_dashboard_scenario_comparison_layout_exposes_responsive_builder_hooks():
    app = create_app()
    source_selector = _find_component_by_id(
        app.layout,
        "comparison-source-selector",
    )
    assert source_selector is not None
    assert source_selector.className == "scenario-comparison-source-options"

    run_row = _find_component_by_class_name(
        app.layout,
        "scenario-comparison-run-row",
    )
    assert run_row is not None

    run_actions = _find_component_by_class_name(
        app.layout,
        "scenario-comparison-run-actions",
    )
    assert run_actions is not None

    collapsed_bar = _find_component_by_id(
        app.layout,
        "scenario-comparison-builder-collapsed-bar",
    )
    assert collapsed_bar is not None
    assert "scenario-comparison-builder-collapsed-bar" in collapsed_bar.className

def test_dashboard_comparison_capacity_kpi_placeholders_exist_in_layout():
    app = create_app()

    comparison_cards = _find_component_by_id(
        app.layout,
        "smart-charging-comparison-summary-cards",
    )
    visible_text = " ".join(_collect_text(comparison_cards))

    assert "Peak Load" in visible_text
    assert "Required Connection Capacity" in visible_text
    assert "Peak Transformer Loading" in visible_text
    assert "Service Impact" in visible_text
    assert "Power Quality Impact" in visible_text
    assert "Grid / Infrastructure Status" in visible_text
    assert "Peak Load Reduction" not in visible_text
    assert "Required Connection Capacity Reduction" not in visible_text
    assert "Peak Transformer Loading Reduction" not in visible_text

def test_dashboard_smart_charging_layout_uses_section_specific_placeholder_copy():
    app = create_app()
    smart_charging_tab = _find_tab_by_value(
        _find_component_by_id(app.layout, "dashboard-tabs"),
        "smart-charging",
    )
    visible_text = " ".join(_collect_text(smart_charging_tab.children))

    assert "Baseline: Uncontrolled Charging. Comparison: Smart Charging." in visible_text
    assert "Charging Strategy Comparison" in visible_text
    assert "Charging Performance" in visible_text
    assert "Occupied Chargers Over Time" in visible_text
    assert "Queue Length Over Time" in visible_text
    assert "Overall PQ Risk Over Time" in visible_text
    assert "Detailed overload, queueing, capacity, and PQ diagnostics" in visible_text
    assert "Run the simulation to review additional technical comparison details." in (
        visible_text
    )

def test_dashboard_grid_capacity_tab_does_not_render_optional_feeder_chart_by_default():
    app = create_app()

    tabs = _find_component_by_id(app.layout, "dashboard-tabs")
    grid_panel = _find_tab_by_value(tabs, "grid-capacity").children
    grid_text = " ".join(_collect_text(grid_panel))

    assert _find_component_by_id(grid_panel, "feeder-peak-loading-chart") is None
    assert "Peak Loading by Feeder" not in grid_text

