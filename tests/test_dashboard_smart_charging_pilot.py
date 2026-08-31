from app import create_app


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


def test_smart_charging_pilot_uses_shared_region_and_widget_shells():
    app = create_app()
    tabs = _find_component_by_id(app.layout, "dashboard-tabs")
    smart_charging_panel = _find_tab_by_value(tabs, "smart-charging").children

    hero_region = _find_component_by_id(
        smart_charging_panel,
        "smart-charging-hero-region",
    )
    performance_region = _find_component_by_id(
        smart_charging_panel,
        "smart-charging-performance-region",
    )
    main_analysis_region = _find_component_by_id(
        smart_charging_panel,
        "smart-charging-main-analysis-region",
    )
    hero_summary = _find_component_by_id(
        smart_charging_panel,
        "smart-charging-hero-summary",
    )
    hero_chart = _find_component_by_id(
        smart_charging_panel,
        "smart-charging-hero-chart",
    )
    pq_chart_block = _find_component_by_id(
        smart_charging_panel,
        "strategy-comparison-pq-risk-block",
    )

    assert hero_region is not None
    assert "dashboard-region" in hero_region.className
    assert "smart-charging-hero-grid" in hero_region.className
    assert main_analysis_region is not None
    assert "dashboard-region" in main_analysis_region.className
    assert performance_region is not None
    assert "dashboard-region" in performance_region.className
    assert hero_summary is not None
    assert "dashboard-widget" in hero_summary.className
    assert "smart-charging-hero-block" in hero_summary.className
    assert hero_chart is not None
    assert "dashboard-widget" in hero_chart.className
    assert "smart-charging-hero-block" in hero_chart.className
    assert pq_chart_block is not None
    assert "dashboard-widget" in pq_chart_block.className
    assert [child.id for child in main_analysis_region.children] == [
        "smart-charging-hero-chart",
        "strategy-comparison-pq-risk-block",
    ]
    assert _find_component_by_id(hero_chart, "strategy-comparison-pq-risk-block") is None


def test_smart_charging_pilot_preserves_conditional_status_targets():
    app = create_app()

    queue_status = _find_component_by_id(
        app.layout,
        "strategy-comparison-queue-status",
    )
    power_quality_status = _find_component_by_id(
        app.layout,
        "power-quality-comparison-status",
    )

    assert queue_status is not None
    assert queue_status.style == {"display": "none"}
    assert power_quality_status is not None
    assert "dashboard-widget" in power_quality_status.className
    assert power_quality_status.style["display"] == "none"
