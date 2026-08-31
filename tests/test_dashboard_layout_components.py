from dash import html

from dashboard.layout_components import (
    DashboardWidgetPlacement,
    build_dashboard_widget_style,
    build_dashboard_region_class_name,
    build_dashboard_region_grid,
    build_dashboard_region_grid_style,
    build_dashboard_widget_shell,
    build_dashboard_widget_shell_class_name,
    build_dashboard_widget_shell_style,
    build_dashboard_widget_surface_style,
    create_dashboard_widget_placement,
)
from dashboard.layout_contract import (
    DashboardEmptyStatePolicy,
    DashboardRegionColumns,
    DashboardRegionSpec,
    DashboardWidgetHeightHint,
    DashboardWidgetMode,
    DashboardWidgetRenderState,
    DashboardWidgetSpan,
    DashboardWidgetSpec,
)


def test_dashboard_widget_shell_returns_none_for_hidden_state():
    placement = DashboardWidgetPlacement(
        spec=DashboardWidgetSpec(
            widget_id="queue-status",
            region="evidence",
        ),
        children=html.Div("Should not render"),
        render_state=DashboardWidgetRenderState.HIDDEN,
    )

    assert build_dashboard_widget_shell(placement) is None


def test_dashboard_widget_shell_renders_responsive_span_and_state_classes():
    placement = DashboardWidgetPlacement(
        spec=DashboardWidgetSpec(
            widget_id="peak-load-card",
            region="summary",
            span=DashboardWidgetSpan(mobile=12, tablet=6, desktop=3),
            height_hint=DashboardWidgetHeightHint.COMPACT,
            mode_hint=DashboardWidgetMode.SUMMARY,
        ),
        children=html.Div("Peak load"),
        render_state=DashboardWidgetRenderState.CONTENT,
        class_name="custom-widget",
        style={"backgroundColor": "#ffffff"},
        component_id="peak-load-widget",
    )

    widget = build_dashboard_widget_shell(placement)

    assert widget.id == "peak-load-widget"
    assert "dashboard-widget" in widget.className
    assert "dashboard-widget--state-content" in widget.className
    assert "dashboard-widget--mode-summary" in widget.className
    assert "dashboard-widget--height-compact" in widget.className
    assert "custom-widget" in widget.className
    assert widget.style["--dashboard-widget-span-mobile"] == "12"
    assert widget.style["--dashboard-widget-span-tablet"] == "6"
    assert widget.style["--dashboard-widget-span-desktop"] == "3"
    assert widget.style["backgroundColor"] == "#ffffff"


def test_dashboard_widget_shell_uses_message_children_for_message_state():
    placement = DashboardWidgetPlacement(
        spec=DashboardWidgetSpec(
            widget_id="queue-status",
            region="evidence",
            empty_state_policy=DashboardEmptyStatePolicy.REPLACE_WITH_MESSAGE,
        ),
        render_state=DashboardWidgetRenderState.MESSAGE,
        message_children=html.P("No queues formed during the simulation."),
    )

    widget = build_dashboard_widget_shell(placement)

    assert widget.children.children == "No queues formed during the simulation."


def test_dashboard_region_grid_sorts_widgets_by_priority_and_omits_hidden_items():
    region = DashboardRegionSpec(
        region_id="summary",
        columns=DashboardRegionColumns(mobile=1, tablet=2, desktop=4),
    )
    placements = [
        DashboardWidgetPlacement(
            spec=DashboardWidgetSpec(
                widget_id="later-widget",
                region="summary",
                priority=30,
            ),
            children=html.Div("Later"),
        ),
        DashboardWidgetPlacement(
            spec=DashboardWidgetSpec(
                widget_id="hidden-widget",
                region="summary",
                priority=10,
            ),
            children=html.Div("Hidden"),
            render_state=DashboardWidgetRenderState.HIDDEN,
        ),
        DashboardWidgetPlacement(
            spec=DashboardWidgetSpec(
                widget_id="first-widget",
                region="summary",
                priority=10,
            ),
            children=html.Div("First"),
        ),
    ]

    region_grid = build_dashboard_region_grid(
        region,
        placements,
        component_id="summary-region",
    )

    assert region_grid.id == "summary-region"
    assert len(region_grid.children) == 2
    assert region_grid.children[0].children.children == "First"
    assert region_grid.children[1].children.children == "Later"


def test_dashboard_region_grid_style_exposes_responsive_column_variables():
    region = DashboardRegionSpec(
        region_id="hero",
        columns=DashboardRegionColumns(mobile=1, tablet=2, desktop=3),
        prefer_full_width_children=True,
    )

    style = build_dashboard_region_grid_style(
        region,
        style={"marginBottom": "1rem"},
    )
    class_name = build_dashboard_region_class_name(
        region,
        extra_class_name="hero-region",
    )

    assert style["--dashboard-region-columns-mobile"] == "1"
    assert style["--dashboard-region-columns-tablet"] == "2"
    assert style["--dashboard-region-columns-desktop"] == "3"
    assert style["marginBottom"] == "1rem"
    assert "dashboard-region" in class_name
    assert "dashboard-region--hero" in class_name
    assert "dashboard-region--prefer-full-width" in class_name
    assert "hero-region" in class_name


def test_widget_and_region_class_name_helpers_are_stable():
    widget_spec = DashboardWidgetSpec(
        widget_id="pq-chart",
        region="evidence",
        height_hint=DashboardWidgetHeightHint.TALL,
        mode_hint=DashboardWidgetMode.CHART,
    )
    region_spec = DashboardRegionSpec(
        region_id="evidence",
        allow_mixed_heights=False,
    )

    widget_class_name = build_dashboard_widget_shell_class_name(
        widget_spec,
        DashboardWidgetRenderState.PLACEHOLDER,
    )
    widget_style = build_dashboard_widget_shell_style(widget_spec)
    region_class_name = build_dashboard_region_class_name(region_spec)

    assert "dashboard-widget--state-placeholder" in widget_class_name
    assert "dashboard-widget--mode-chart" in widget_class_name
    assert "dashboard-widget--height-tall" in widget_class_name
    assert widget_style["--dashboard-widget-span-mobile"] == "12"
    assert "dashboard-region--uniform-heights" in region_class_name


def test_dashboard_widget_authoring_template_builds_widget_from_metadata_and_render_logic():
    spec = DashboardWidgetSpec(
        widget_id="new-widget",
        region="future_region",
        span=DashboardWidgetSpan(mobile=12, tablet=6, desktop=4),
        height_hint=DashboardWidgetHeightHint.STANDARD,
        mode_hint=DashboardWidgetMode.DETAIL,
    )
    placement = create_dashboard_widget_placement(
        spec,
        component_id="new-widget-section",
        base_style={"padding": "1rem"},
        children=[
            html.H2("New Widget"),
            html.Div("Render logic stays local to the widget."),
        ],
    )
    widget = build_dashboard_widget_shell(placement)

    assert widget.id == "new-widget-section"
    assert widget.children[0].children == "New Widget"
    assert widget.children[1].children == "Render logic stays local to the widget."
    assert widget.style["padding"] == "1rem"
    assert widget.style["--dashboard-widget-span-desktop"] == "4"


def test_dashboard_widget_style_helpers_share_one_visibility_path():
    spec = DashboardWidgetSpec(
        widget_id="status-widget",
        region="summary",
        span=DashboardWidgetSpan(mobile=12, tablet=12, desktop=5),
    )

    surface_style = build_dashboard_widget_surface_style(
        base_style={"padding": "1rem"},
        hidden=True,
    )
    widget_style = build_dashboard_widget_style(
        spec,
        base_style={"padding": "1rem"},
        hidden=True,
    )

    assert surface_style == {
        "padding": "1rem",
        "display": "none",
    }
    assert widget_style["padding"] == "1rem"
    assert widget_style["display"] == "none"
    assert widget_style["--dashboard-widget-span-desktop"] == "5"
