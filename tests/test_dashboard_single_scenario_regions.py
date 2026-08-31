from app import create_app


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


def test_single_scenario_tabs_use_shared_dashboard_regions():
    app = create_app()
    tabs = _find_component_by_id(app.layout, "dashboard-tabs")

    overview_panel = _find_tab_by_value(tabs, "overview").children
    infrastructure_panel = _find_tab_by_value(tabs, "infrastructure").children
    grid_panel = _find_tab_by_value(tabs, "grid-capacity").children
    power_quality_panel = _find_tab_by_value(tabs, "power-quality").children

    overview_primary_region = _find_component_by_id(
        overview_panel,
        "overview-primary-region",
    )
    overview_secondary_region = _find_component_by_id(
        overview_panel,
        "overview-secondary-region",
    )
    infrastructure_primary_region = _find_component_by_id(
        infrastructure_panel,
        "infrastructure-primary-region",
    )
    grid_primary_region = _find_component_by_id(
        grid_panel,
        "grid-capacity-primary-region",
    )
    power_quality_primary_region = _find_component_by_id(
        power_quality_panel,
        "power-quality-primary-region",
    )

    assert overview_primary_region is not None
    assert "dashboard-region" in overview_primary_region.className
    assert len(overview_primary_region.children) == 1
    assert overview_secondary_region is not None
    assert "dashboard-region" in overview_secondary_region.className
    assert len(overview_secondary_region.children) == 2
    assert infrastructure_primary_region is not None
    assert "dashboard-region" in infrastructure_primary_region.className
    assert len(infrastructure_primary_region.children) == 2
    assert grid_primary_region is not None
    assert "dashboard-region" in grid_primary_region.className
    assert len(grid_primary_region.children) == 1
    assert power_quality_primary_region is not None
    assert "dashboard-region" in power_quality_primary_region.className
    assert len(power_quality_primary_region.children) == 1


def test_single_scenario_tabs_preserve_placeholder_surfaces_inside_widget_shells():
    app = create_app()

    overview_kpi_section = _find_component_by_id(
        app.layout,
        "overview-kpi-summary-section",
    )
    overview_kpi_cards = _find_component_by_id(
        app.layout,
        "overview-kpi-cards",
    )
    overview_smart_charging_section = _find_component_by_id(
        app.layout,
        "overview-smart-charging-impact-section",
    )
    overview_capacity_section = _find_component_by_id(
        app.layout,
        "overview-capacity-vs-load-section",
    )
    infrastructure_summary_section = _find_component_by_id(
        app.layout,
        "infrastructure-summary-section",
    )
    grid_summary_section = _find_component_by_id(
        app.layout,
        "grid-capacity-summary-section",
    )
    power_quality_summary_section = _find_component_by_id(
        app.layout,
        "power-quality-kpi-section",
    )

    assert overview_kpi_section is not None
    assert "dashboard-widget" in overview_kpi_section.className
    assert "Executive KPI Summary" in str(overview_kpi_section.children)
    assert overview_kpi_cards is not None
    assert len(overview_kpi_cards.children) == 4
    overview_kpi_text = " ".join(_collect_text(overview_kpi_cards))
    assert "Scenario Outcome" in overview_kpi_text
    assert "Peak Load" in overview_kpi_text
    assert "Grid Connection Need" in overview_kpi_text
    assert "Charger Expansion Need" in overview_kpi_text
    assert overview_kpi_text.count("Not run yet") == 4
    assert overview_smart_charging_section is not None
    assert "dashboard-widget" in overview_smart_charging_section.className
    overview_smart_charging_text = " ".join(
        _collect_text(overview_smart_charging_section)
    )
    assert "Smart Charging Impact" in overview_smart_charging_text
    assert "Peak Reduction" in overview_smart_charging_text
    assert "Uncontrolled" in overview_smart_charging_text
    assert "Smart Charging" in overview_smart_charging_text
    assert overview_smart_charging_text.count("Not run yet") == 3
    assert overview_capacity_section is not None
    assert "dashboard-widget" in overview_capacity_section.className
    assert "Capacity vs Load" in str(overview_capacity_section.children)
    assert infrastructure_summary_section is not None
    assert "dashboard-widget" in infrastructure_summary_section.className
    assert "Run the simulation to generate an infrastructure status." in str(
        infrastructure_summary_section.children
    )
    assert grid_summary_section is not None
    assert "dashboard-widget" in grid_summary_section.className
    assert "Grid Loading Indicators" in str(
        grid_summary_section.children
    )
    assert power_quality_summary_section is not None
    assert "dashboard-widget" in power_quality_summary_section.className
    assert "PQ indicators are simplified scenario-based risk estimates" in str(
        power_quality_summary_section.children
    )
