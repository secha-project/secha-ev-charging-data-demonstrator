from app import create_app
from dashboard.callbacks import (
    create_active_scenario_state,
    create_scenario_ab_comparison_run_state,
    create_scenario_comparison_state,
)
from scenarios import ChargingStrategy, DEFAULT_SCENARIO_PRESET_ID
from scenarios import update_scenario_b_in_comparison_data


def _collect_text(component):
    if isinstance(component, str):
        return [component]

    if isinstance(component, (list, tuple)):
        text = []
        for child in component:
            text.extend(_collect_text(child))
        return text

    if hasattr(component, "children"):
        return _collect_text(component.children)

    return []


def _find_component_by_id(component, component_id):
    if getattr(component, "id", None) == component_id:
        return component

    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            result = _find_component_by_id(child, component_id)
            if result is not None:
                return result
    elif children is not None:
        return _find_component_by_id(children, component_id)

    return None


def _find_tab_by_value(tabs, value):
    return next(tab for tab in tabs.children if tab.value == value)


def _find_callback_function(app, output_fragment):
    callback_key = next(
        key for key in app.callback_map if output_fragment in key
    )
    callback = app.callback_map[callback_key]["callback"]
    return getattr(callback, "__wrapped__", callback)


def _extract_dashboard_widget_sections(tab_panel):
    sections = []
    for child in tab_panel.children:
        class_name = getattr(child, "className", "")
        if isinstance(class_name, str) and "dashboard-region" in class_name:
            region_children = getattr(child, "children", None)
            if isinstance(region_children, (list, tuple)):
                sections.extend(region_children)
            elif region_children is not None:
                sections.append(region_children)
            continue

        sections.append(child)

    return sections


def test_scenario_comparison_uses_shared_regions_and_widget_shells():
    app = create_app()
    tabs = _find_component_by_id(app.layout, "dashboard-tabs")
    comparison_panel = _find_tab_by_value(tabs, "scenario-comparison").children
    selected_section_store = _find_component_by_id(
        comparison_panel,
        "scenario-ab-selected-section-store",
    )

    builder_region = _find_component_by_id(
        comparison_panel,
        "scenario-comparison-builder-region",
    )
    results_region = _find_component_by_id(
        comparison_panel,
        "scenario-comparison-results-region",
    )

    assert builder_region is not None
    assert selected_section_store is not None
    assert selected_section_store.data is None
    assert "dashboard-region" in builder_region.className
    assert len(builder_region.children) == 1
    assert results_region is not None
    assert "dashboard-region" in results_region.className
    assert len(results_region.children) == 2

    assert [
        getattr(section, "id", None)
        for section in _extract_dashboard_widget_sections(comparison_panel)
    ] == [
        "scenario-ab-selected-section-store",
        "scenario-comparison-builder-section",
        "scenario-ab-executive-summary-section",
        "scenario-ab-comparison-table-section",
    ]

    builder_section = _find_component_by_id(
        comparison_panel,
        "scenario-comparison-builder-section",
    )
    assert builder_section is not None
    expanded_content = _find_component_by_id(
        builder_section,
        "scenario-comparison-builder-expanded-content",
    )
    assert expanded_content is not None
    builder_stack = next(
        child
        for child in expanded_content.children
        if getattr(child, "className", None) == "scenario-comparison-builder-stack"
    )
    assert [
        getattr(child, "id", None)
        for child in builder_stack.children
        if getattr(child, "id", None) is not None
    ] == [
        "scenario-b-source-section",
        "scenario-b-configuration-section",
        "scenario-ab-assumptions-section",
        "scenario-comparison-empty-state-section",
    ]
    assert _find_component_by_id(builder_section, "scenario-b-source-section") is not None
    assert _find_component_by_id(builder_section, "scenario-b-configuration-section") is not None
    assert _find_component_by_id(builder_section, "scenario-ab-assumptions-section") is not None
    assert _find_component_by_id(
        builder_section,
        "scenario-comparison-empty-state-section",
    ) is not None


def test_scenario_comparison_preserves_widget_shells_for_run_and_results_states():
    app = create_app()

    builder_section = _find_component_by_id(
        app.layout,
        "scenario-comparison-builder-section",
    )
    empty_state_section = _find_component_by_id(
        app.layout,
        "scenario-comparison-empty-state-section",
    )
    detailed_section = _find_component_by_id(
        app.layout,
        "scenario-ab-comparison-table-section",
    )
    executive_summary_section = _find_component_by_id(
        app.layout,
        "scenario-ab-executive-summary-section",
    )

    assert builder_section is not None
    assert "dashboard-widget" in builder_section.className
    assert builder_section.style["--dashboard-widget-span-desktop"] == "12"
    assert empty_state_section is not None
    assert empty_state_section.style.get("display") is None
    assert detailed_section is not None
    assert "dashboard-widget" in detailed_section.className
    assert detailed_section.style["--dashboard-widget-span-desktop"] == "12"
    assert detailed_section.style["display"] == "none"
    assert executive_summary_section is not None
    assert "dashboard-widget" in executive_summary_section.className
    assert executive_summary_section.style["--dashboard-widget-span-desktop"] == "12"
    assert executive_summary_section.style["display"] == "none"


def test_scenario_comparison_render_callback_collapses_and_reveals_results_widgets():
    app = create_app()
    callback = _find_callback_function(
        app,
        "scenario-ab-comparison-table.children",
    )
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = create_scenario_comparison_state(active_scenario_state)

    prerun_outputs = callback(
        active_scenario_state,
        comparison_state,
        None,
        None,
        {"collapsed": False, "has_run": False},
        None,
    )

    assert prerun_outputs[0].get("display") is None
    assert prerun_outputs[2]["--dashboard-widget-span-desktop"] == "12"
    assert prerun_outputs[2]["display"] == "none"
    assert prerun_outputs[4]["--dashboard-widget-span-desktop"] == "12"
    assert prerun_outputs[4]["display"] == "none"
    assert prerun_outputs[1] == []
    assert prerun_outputs[5] == ""

    _results_state, metrics_state, difference_metrics_state = (
        create_scenario_ab_comparison_run_state(comparison_state)
    )
    postrun_outputs = callback(
        active_scenario_state,
        comparison_state,
        metrics_state,
        difference_metrics_state,
        {"collapsed": True, "has_run": True},
        None,
    )

    assert postrun_outputs[0]["display"] == "none"
    assert postrun_outputs[2]["--dashboard-widget-span-desktop"] == "12"
    assert postrun_outputs[2].get("display") is None
    assert postrun_outputs[4]["--dashboard-widget-span-desktop"] == "12"
    assert postrun_outputs[4].get("display") is None
    assert len(postrun_outputs[3]) == 6
    postrun_card_text = " ".join(_collect_text(postrun_outputs[3]))
    assert "Peak Load" in postrun_card_text
    assert "Capacity Utilization" in postrun_card_text
    assert "Unmet Energy" in postrun_card_text
    assert "Maximum Queue Length" in postrun_card_text
    assert "Peak Transformer Loading" in postrun_card_text
    assert "Overall PQ Risk" in postrun_card_text
    assert "Benefits:" not in postrun_card_text
    assert "Trade-offs:" not in postrun_card_text
    assert "Unchanged areas:" not in postrun_card_text
    assert "Decision Summary" in " ".join(_collect_text(postrun_outputs[5]))
    assert "Energy & Performance" in " ".join(_collect_text(postrun_outputs[5]))


def test_scenario_comparison_assumption_summary_uses_progressive_disclosure():
    app = create_app()
    callback = _find_callback_function(
        app,
        "scenario-ab-assumptions-summary.children",
    )
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = create_scenario_comparison_state(active_scenario_state)
    updated_comparison_state = update_scenario_b_in_comparison_data(
        comparison_state,
        vehicles=75,
        grid_capacity=1200.0,
    )

    summary_children = callback(updated_comparison_state)
    summary_text = " ".join(_collect_text(summary_children))

    assert "2 assumption changes" in summary_text
    assert "2 areas" in summary_text
    assert "Number of vehicles: 50 -> 75" in summary_text
    assert "Grid connection capacity: 1,000.0 kW -> 1,200.0 kW" in summary_text
    assert "View changes" in summary_text


def test_scenario_comparison_render_callback_keeps_results_visible_when_builder_is_expanded_after_run():
    app = create_app()
    callback = _find_callback_function(
        app,
        "scenario-ab-comparison-table.children",
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

    outputs = callback(
        active_scenario_state,
        comparison_state,
        metrics_state,
        difference_metrics_state,
        {"collapsed": False, "has_run": True},
        None,
    )

    assert outputs[0].get("display") is None
    assert outputs[1] == []
    assert outputs[2].get("display") is None
    assert outputs[4].get("display") is None
    assert "Energy & Performance" in " ".join(_collect_text(outputs[5]))


def test_scenario_comparison_render_callback_hides_summary_again_when_results_are_invalidated():
    app = create_app()
    callback = _find_callback_function(
        app,
        "scenario-ab-comparison-table.children",
    )
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = update_scenario_b_in_comparison_data(
        create_scenario_comparison_state(active_scenario_state),
        vehicles=75,
    )

    outputs = callback(
        active_scenario_state,
        comparison_state,
        None,
        None,
        {"collapsed": False, "has_run": True},
        None,
    )

    assert outputs[0].get("display") is None
    assert outputs[2]["display"] == "none"
    assert len(outputs[3]) == 6
    assert outputs[4]["display"] == "none"
    assert outputs[5] == ""


def test_scenario_comparison_collapsed_bar_renders_post_run_context():
    app = create_app()
    callback = _find_callback_function(
        app,
        "scenario-comparison-collapsed-title.children",
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

    outputs = callback(
        active_scenario_state,
        comparison_state,
        {"status": "up_to_date"},
        {"collapsed": True, "has_run": True},
    )

    assert outputs[0]["display"] == "none"
    assert outputs[1]["display"] == "grid"
    assert "Scenario A:" in outputs[2]
    assert "Scenario B:" in outputs[2]
    assert "->" in outputs[2]
    assert "1 assumption change selected." in outputs[3]
    assert outputs[4] == "Up to date"


def test_scenario_comparison_collapsed_bar_renders_out_of_date_status_after_edit():
    app = create_app()
    callback = _find_callback_function(
        app,
        "scenario-comparison-collapsed-title.children",
    )
    active_scenario_state = create_active_scenario_state(
        DEFAULT_SCENARIO_PRESET_ID,
        ChargingStrategy.SMART.value,
    )
    comparison_state = update_scenario_b_in_comparison_data(
        create_scenario_comparison_state(active_scenario_state),
        vehicles=75,
    )

    outputs = callback(
        active_scenario_state,
        comparison_state,
        {"status": "stale"},
        {"collapsed": True, "has_run": True},
    )

    assert outputs[0]["display"] == "none"
    assert outputs[1]["display"] == "grid"
    assert outputs[4] == "Out of date"
    assert "1 assumption change selected." in outputs[3]
