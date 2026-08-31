import pytest

from dashboard.layout_contract import (
    DASHBOARD_GRID_COLUMNS,
    DashboardBreakpoint,
    DashboardEmptyStatePolicy,
    DashboardRegionColumns,
    DashboardRegionSpec,
    DashboardWidgetHeightHint,
    DashboardWidgetMode,
    DashboardWidgetRenderState,
    DashboardWidgetSpan,
    DashboardWidgetSpec,
    resolve_widget_render_state,
    resolve_widget_visibility,
)


def test_widget_span_defaults_to_full_width():
    span = DashboardWidgetSpan.normalize(None)

    assert span == DashboardWidgetSpan(
        mobile=DASHBOARD_GRID_COLUMNS,
        tablet=DASHBOARD_GRID_COLUMNS,
        desktop=DASHBOARD_GRID_COLUMNS,
    )
    assert span.as_dict() == {
        "mobile": DASHBOARD_GRID_COLUMNS,
        "tablet": DASHBOARD_GRID_COLUMNS,
        "desktop": DASHBOARD_GRID_COLUMNS,
    }


def test_widget_span_normalization_cascades_missing_breakpoints():
    span = DashboardWidgetSpan.normalize(
        {
            DashboardBreakpoint.MOBILE: 12,
            DashboardBreakpoint.TABLET: 6,
        }
    )

    assert span.mobile == 12
    assert span.tablet == 6
    assert span.desktop == 6


def test_widget_span_normalization_accepts_scalar_values():
    span = DashboardWidgetSpan.normalize(4)

    assert span.mobile == 4
    assert span.tablet == 4
    assert span.desktop == 4


@pytest.mark.parametrize("invalid_value", [0, 13])
def test_widget_span_rejects_out_of_range_values(invalid_value: int):
    with pytest.raises(ValueError, match="span must stay within 1..12"):
        DashboardWidgetSpan(mobile=invalid_value)


def test_region_columns_normalization_cascades_missing_breakpoints():
    columns = DashboardRegionColumns.normalize({"tablet": 2, "desktop": 4})

    assert columns.mobile == 1
    assert columns.tablet == 2
    assert columns.desktop == 4


def test_region_spec_rejects_blank_region_ids():
    with pytest.raises(ValueError, match="region_id must not be blank"):
        DashboardRegionSpec(region_id=" ")


def test_widget_spec_uses_minimal_layout_metadata_defaults():
    widget = DashboardWidgetSpec(
        widget_id="overview-peak-load",
        region="summary",
    )

    assert widget.priority == 100
    assert widget.span == DashboardWidgetSpan()
    assert widget.height_hint == DashboardWidgetHeightHint.STANDARD
    assert widget.empty_state_policy == DashboardEmptyStatePolicy.SHOW_PLACEHOLDER
    assert widget.default_visible is True
    assert widget.visibility_rule is None
    assert widget.mode_hint is None
    assert widget.group_hint is None


def test_widget_spec_accepts_symbolic_visibility_rule_but_not_callable_logic():
    widget = DashboardWidgetSpec(
        widget_id="queue-status",
        region="evidence",
        visibility_rule="comparison_has_queue_pressure",
        mode_hint=DashboardWidgetMode.STATUS,
    )

    assert widget.visibility_rule == "comparison_has_queue_pressure"

    with pytest.raises(TypeError, match="visibility_rule must be a string label or None"):
        DashboardWidgetSpec(
            widget_id="queue-status",
            region="evidence",
            visibility_rule=lambda: True,
        )


def test_resolve_widget_visibility_uses_override_when_provided():
    widget = DashboardWidgetSpec(
        widget_id="pq-summary",
        region="summary",
        default_visible=False,
    )

    assert resolve_widget_visibility(widget) is False
    assert resolve_widget_visibility(widget, rule_result=True) is True


def test_render_state_hides_invisible_widgets_without_reserving_space():
    widget = DashboardWidgetSpec(
        widget_id="feeder-detail",
        region="details",
        empty_state_policy=DashboardEmptyStatePolicy.REPLACE_WITH_MESSAGE,
    )

    render_state = resolve_widget_render_state(
        widget,
        has_meaningful_content=True,
        rule_result=False,
    )

    assert render_state == DashboardWidgetRenderState.HIDDEN


@pytest.mark.parametrize(
    ("policy", "expected_state"),
    [
        (DashboardEmptyStatePolicy.HIDE, DashboardWidgetRenderState.HIDDEN),
        (
            DashboardEmptyStatePolicy.REPLACE_WITH_MESSAGE,
            DashboardWidgetRenderState.MESSAGE,
        ),
        (
            DashboardEmptyStatePolicy.SHOW_PLACEHOLDER,
            DashboardWidgetRenderState.PLACEHOLDER,
        ),
        (
            DashboardEmptyStatePolicy.ALWAYS_SHOW,
            DashboardWidgetRenderState.CONTENT,
        ),
    ],
)
def test_render_state_respects_empty_state_policy_when_content_is_not_meaningful(
    policy: DashboardEmptyStatePolicy,
    expected_state: DashboardWidgetRenderState,
):
    widget = DashboardWidgetSpec(
        widget_id="grid-summary",
        region="summary",
        empty_state_policy=policy,
    )

    render_state = resolve_widget_render_state(
        widget,
        has_meaningful_content=False,
    )

    assert render_state == expected_state
