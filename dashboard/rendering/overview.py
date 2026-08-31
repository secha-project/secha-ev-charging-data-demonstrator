"""Overview-tab rendering helpers."""

from ._shared import *
from .formatters import *

def render_insights(insights: list[str]) -> list[Any]:
    """Render generated insight messages as dashboard list items."""
    return [html.Li(insight) for insight in insights]

def render_overview_kpi_cards(display_data: OverviewDisplayData) -> list[Any]:
    """Render Overview KPI cards from prepared executive-summary data."""

    return [_render_overview_kpi_card(descriptor) for descriptor in display_data.kpis]

def render_overview_smart_charging_preview(
    preview: OverviewSmartChargingPreview,
) -> list[Any]:
    """Render the compact Overview Smart Charging preview from prepared data."""

    baseline_value = _overview_numeric_field_value(preview.baseline)
    comparison_value = _overview_numeric_field_value(preview.comparison)
    scale_max = max(baseline_value, comparison_value, 1.0)
    baseline_ratio = baseline_value / scale_max
    comparison_ratio = comparison_value / scale_max
    change_direction = _overview_smart_charging_change_direction(
        baseline_value,
        comparison_value,
    )
    return [
        html.Div(
            [
                html.Div(
                    [
                        html.Span(
                            preview.summary_title,
                            style=KPI_LABEL_TEXT_STYLE,
                        ),
                        html.Strong(
                            preview.summary_value,
                            style={
                                **KPI_VALUE_TEXT_STYLE,
                                "fontSize": "1.65rem",
                            },
                        ),
                    ],
                    style={
                        "display": "grid",
                        "gap": "0.25rem",
                    },
                ),
                html.Hr(
                    style={
                        "border": "0",
                        "borderTop": f"1px solid {BORDER_COLOR}",
                        "margin": "0",
                    }
                ),
                _render_overview_smart_charging_row(
                    preview.baseline.label,
                    _format_overview_display_field_value(preview.baseline),
                    baseline_ratio,
                    "#5d7287",
                ),
                _render_overview_smart_charging_row(
                    preview.comparison.label,
                    _format_overview_display_field_value(preview.comparison),
                    comparison_ratio,
                    ACCENT_BLUE,
                    reference_ratio=baseline_ratio,
                    change_direction=change_direction,
                ),
            ],
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": "1.4rem",
                "width": "100%",
                "minWidth": "0",
            },
        ),
    ]

def _default_overview_kpi_cards() -> list[Any]:
    """Return placeholder Overview KPI cards before a run is available."""

    return [
        _render_overview_placeholder_card(
            "Scenario Outcome",
            "Overall modeled scenario status",
        ),
        _render_overview_placeholder_card(
            "Peak Load",
            "Maximum charging demand",
        ),
        _render_overview_placeholder_card(
            "Grid Connection Need",
            "Planner-facing connection recommendation",
        ),
        _render_overview_placeholder_card(
            "Charger Expansion Need",
            "Required charger-count change",
        ),
    ]

def _default_overview_smart_charging_preview_children() -> list[Any]:
    """Return placeholder Smart Charging preview content for the Overview tab."""

    return [
        html.Div(
            [
                html.Div(
                    [
                        html.Span(
                            "Peak Reduction",
                            style=KPI_LABEL_TEXT_STYLE,
                        ),
                        html.Strong(
                            "Not run yet",
                            style={
                                **KPI_VALUE_TEXT_STYLE,
                                "fontSize": "1.65rem",
                            },
                        ),
                    ],
                    style={
                        "display": "grid",
                        "gap": "0.25rem",
                    },
                ),
                html.Hr(
                    style={
                        "border": "0",
                        "borderTop": f"1px solid {BORDER_COLOR}",
                        "margin": "0",
                    }
                ),
                _render_overview_smart_charging_row(
                    "Uncontrolled peak load",
                    "Not run yet",
                    1.0,
                    "#5d7287",
                ),
                _render_overview_smart_charging_row(
                    "Smart Charging peak load",
                    "Not run yet",
                    0.72,
                    ACCENT_BLUE,
                    reference_ratio=1.0,
                    change_direction="reduction",
                ),
            ],
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": "1.4rem",
                "width": "100%",
                "minWidth": "0",
            },
        ),
    ]

def _render_overview_placeholder_card(title: str, subtitle: str) -> Any:
    """Return one placeholder KPI card for the Overview tab."""

    return html.Div(
        [
            html.Strong(title),
            html.Span(subtitle, style=KPI_LABEL_TEXT_STYLE),
            html.Span("Not run yet", style=KPI_VALUE_TEXT_STYLE),
        ],
        style=KPI_CARD_STYLE,
    )

def _render_overview_kpi_card(descriptor: OverviewKpiDescriptor) -> Any:
    """Render one prepared Overview KPI card."""

    children: list[Any] = [
        html.Strong(descriptor.title),
        html.Span(
            _format_overview_display_field_value(descriptor.headline),
            style=KPI_VALUE_TEXT_STYLE,
        ),
        html.Span(
            descriptor.headline.label,
            style=KPI_LABEL_TEXT_STYLE,
        ),
    ]
    children.extend(
        html.Span(
            (
                f"{field.label}: "
                f"{_format_overview_display_field_value(field)}"
            ),
            style=KPI_LABEL_TEXT_STYLE,
        )
        for field in descriptor.supporting_fields
    )
    if descriptor.supporting_text:
        children.append(
            html.Span(
                descriptor.supporting_text,
                style=SUPPORTING_TEXT_STYLE,
            )
        )

    return html.Div(
        children,
        style=_scenario_ab_executive_card_style(descriptor.outcome),
    )

def _format_overview_display_field_value(field: OverviewDisplayField) -> str:
    """Format one prepared Overview display field."""

    if field.value_format == OVERVIEW_VALUE_FORMAT_TEXT:
        return str(field.value)

    return _format_scenario_ab_scalar_value(field.value_format, field.value)

def _overview_numeric_field_value(field: OverviewDisplayField) -> float:
    """Return a numeric Overview field value for compact preview scaling."""

    try:
        return max(float(field.value), 0.0)
    except (TypeError, ValueError):
        return 0.0

def _render_overview_smart_charging_row(
    label: str,
    value_text: str,
    width_ratio: float,
    bar_color: str,
    *,
    reference_ratio: float | None = None,
    change_direction: str | None = None,
) -> Any:
    """Render one compact bar row for the Overview Smart Charging preview."""

    clamped_width = min(max(width_ratio, 0.0), 1.0) * 100.0
    track_children = [
        html.Div(
            style={
                "width": f"{clamped_width:.1f}%",
                "height": "100%",
                "borderRadius": "999px",
                "backgroundColor": bar_color,
                "flex": f"0 0 {clamped_width:.1f}%",
            }
        )
    ]
    if reference_ratio is not None and change_direction is not None:
        reference_width = min(max(reference_ratio, 0.0), 1.0) * 100.0
        delta_width = abs(reference_width - clamped_width)
        if delta_width > 0.0:
            delta_color = _overview_smart_charging_delta_color(change_direction)
            if clamped_width < reference_width:
                track_children.append(
                    html.Div(
                        style={
                            "width": f"{delta_width:.1f}%",
                            "height": "100%",
                            "borderRadius": "999px",
                            "backgroundColor": delta_color,
                            "flex": f"0 0 {delta_width:.1f}%",
                        }
                    )
                )
            else:
                track_children = [
                    html.Div(
                        style={
                            "width": f"{reference_width:.1f}%",
                            "height": "100%",
                            "borderRadius": "999px",
                            "backgroundColor": ACCENT_BLUE,
                            "flex": f"0 0 {reference_width:.1f}%",
                        }
                    ),
                    html.Div(
                        style={
                            "width": f"{delta_width:.1f}%",
                            "height": "100%",
                            "borderRadius": "999px",
                            "backgroundColor": delta_color,
                            "flex": f"0 0 {delta_width:.1f}%",
                        }
                    ),
                ]

    return html.Div(
        [
            html.Strong(label, style={"lineHeight": "1.3"}),
            html.Span(
                value_text,
                style={
                    **KPI_LABEL_TEXT_STYLE,
                    "color": TEXT_PRIMARY_COLOR,
                    "fontWeight": "600",
                },
            ),
            html.Div(track_children, style=_overview_smart_charging_track_style()),
        ],
        style={
            "display": "grid",
            "gap": "0.5rem",
            "minWidth": "0",
        },
    )

def _overview_smart_charging_track_style() -> dict[str, Any]:
    """Return the shared track styling for Overview smart-charging rows."""

    return {
        "display": "flex",
        "width": "100%",
        "height": "0.8rem",
        "backgroundColor": "#dbe6ef",
        "borderRadius": "999px",
        "overflow": "hidden",
    }

def _overview_smart_charging_change_direction(
    baseline_value: float,
    comparison_value: float,
) -> str:
    """Return whether Smart Charging reduces, increases, or preserves peak."""

    if math.isclose(baseline_value, comparison_value, abs_tol=0.05):
        return "neutral"
    if comparison_value < baseline_value:
        return "reduction"
    return "increase"

def _overview_smart_charging_delta_color(change_direction: str) -> str:
    """Return the highlighted delta color for the smart-charging preview."""

    if change_direction == "reduction":
        return STATUS_GREEN
    if change_direction == "increase":
        return STATUS_RED
    return STATUS_AMBER

__all__ = [

    'render_insights',

    'render_overview_kpi_cards',

    'render_overview_smart_charging_preview',

    '_default_overview_kpi_cards',

    '_default_overview_smart_charging_preview_children',

    '_render_overview_placeholder_card',

    '_render_overview_kpi_card',

    '_format_overview_display_field_value',

    '_overview_numeric_field_value',

    '_render_overview_smart_charging_row',

    '_overview_smart_charging_track_style',

    '_overview_smart_charging_change_direction',

    '_overview_smart_charging_delta_color',

]

