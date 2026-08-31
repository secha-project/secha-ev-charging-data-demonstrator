"""Shared dashboard layout infrastructure.

These helpers render reusable widget shells and responsive region grids without
changing existing dashboard views yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dash import html

from .layout_contract import (
    DashboardRegionSpec,
    DashboardWidgetHeightHint,
    DashboardWidgetMode,
    DashboardWidgetRenderState,
    DashboardWidgetSpec,
)


def _join_class_names(*values: str | None) -> str:
    """Return one normalized CSS class string."""

    return " ".join(value for value in values if value)


def build_dashboard_region_grid_style(
    region_spec: DashboardRegionSpec,
    *,
    style: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return CSS custom properties for one shared dashboard region grid."""

    region_style = {
        "--dashboard-region-columns-mobile": str(region_spec.columns.mobile),
        "--dashboard-region-columns-tablet": str(region_spec.columns.tablet),
        "--dashboard-region-columns-desktop": str(region_spec.columns.desktop),
    }
    if style is not None:
        region_style.update(style)

    return region_style


def build_dashboard_widget_shell_style(
    widget_spec: DashboardWidgetSpec,
    *,
    style: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return CSS custom properties for one widget shell."""

    widget_style = {
        "--dashboard-widget-span-mobile": str(widget_spec.span.mobile),
        "--dashboard-widget-span-tablet": str(widget_spec.span.tablet),
        "--dashboard-widget-span-desktop": str(widget_spec.span.desktop),
    }
    if style is not None:
        widget_style.update(style)

    return widget_style


def build_dashboard_widget_surface_style(
    *,
    base_style: dict[str, Any] | None = None,
    style: dict[str, Any] | None = None,
    hidden: bool = False,
) -> dict[str, Any]:
    """Return one normalized widget surface style before grid vars are applied."""

    widget_style = {}
    if base_style is not None:
        widget_style.update(base_style)
    if style is not None:
        widget_style.update(style)
    if hidden:
        widget_style["display"] = "none"

    return widget_style


def build_dashboard_widget_style(
    widget_spec: DashboardWidgetSpec,
    *,
    base_style: dict[str, Any] | None = None,
    style: dict[str, Any] | None = None,
    hidden: bool = False,
) -> dict[str, Any]:
    """Return a full widget shell style with shared grid vars and visibility."""

    return build_dashboard_widget_shell_style(
        widget_spec,
        style=build_dashboard_widget_surface_style(
            base_style=base_style,
            style=style,
            hidden=hidden,
        ),
    )


def build_dashboard_region_class_name(
    region_spec: DashboardRegionSpec,
    *,
    extra_class_name: str | None = None,
) -> str:
    """Return the composed CSS class name for one dashboard region."""

    mixed_height_class = (
        "dashboard-region--mixed-heights"
        if region_spec.allow_mixed_heights
        else "dashboard-region--uniform-heights"
    )
    width_preference_class = (
        "dashboard-region--prefer-full-width"
        if region_spec.prefer_full_width_children
        else "dashboard-region--flow"
    )
    return _join_class_names(
        "dashboard-region",
        f"dashboard-region--{region_spec.region_id}",
        mixed_height_class,
        width_preference_class,
        extra_class_name,
    )


def build_dashboard_widget_shell_class_name(
    widget_spec: DashboardWidgetSpec,
    render_state: DashboardWidgetRenderState,
    *,
    extra_class_name: str | None = None,
) -> str:
    """Return the composed CSS class name for one dashboard widget shell."""

    mode_class = (
        f"dashboard-widget--mode-{widget_spec.mode_hint.value}"
        if isinstance(widget_spec.mode_hint, DashboardWidgetMode)
        else None
    )
    height_class = (
        f"dashboard-widget--height-{widget_spec.height_hint.value}"
        if isinstance(widget_spec.height_hint, DashboardWidgetHeightHint)
        else None
    )
    return _join_class_names(
        "dashboard-widget",
        f"dashboard-widget--state-{render_state.value}",
        mode_class,
        height_class,
        extra_class_name,
    )


@dataclass(frozen=True)
class DashboardWidgetPlacement:
    """Concrete widget content prepared for shared region rendering."""

    spec: DashboardWidgetSpec
    children: Any = None
    render_state: DashboardWidgetRenderState = DashboardWidgetRenderState.CONTENT
    message_children: Any = None
    placeholder_children: Any = None
    class_name: str | None = None
    style: dict[str, Any] = field(default_factory=dict)
    component_id: str | None = None


def create_dashboard_widget_placement(
    spec: DashboardWidgetSpec,
    *,
    children: Any = None,
    render_state: DashboardWidgetRenderState = DashboardWidgetRenderState.CONTENT,
    message_children: Any = None,
    placeholder_children: Any = None,
    class_name: str | None = None,
    base_style: dict[str, Any] | None = None,
    style: dict[str, Any] | None = None,
    hidden: bool = False,
    component_id: str | None = None,
) -> DashboardWidgetPlacement:
    """Return a standard widget placement from metadata and render content only."""

    return DashboardWidgetPlacement(
        spec=spec,
        children=children,
        render_state=render_state,
        message_children=message_children,
        placeholder_children=placeholder_children,
        class_name=class_name,
        style=build_dashboard_widget_surface_style(
            base_style=base_style,
            style=style,
            hidden=hidden,
        ),
        component_id=component_id,
    )


def _resolve_widget_children(placement: DashboardWidgetPlacement) -> Any:
    """Return the active children for one placement."""

    if placement.render_state == DashboardWidgetRenderState.CONTENT:
        return placement.children

    if placement.render_state == DashboardWidgetRenderState.MESSAGE:
        return placement.message_children

    if placement.render_state == DashboardWidgetRenderState.PLACEHOLDER:
        return placement.placeholder_children

    return None


def build_dashboard_widget_shell(
    placement: DashboardWidgetPlacement,
) -> Any | None:
    """Render one reusable widget shell or omit it if hidden."""

    if placement.render_state == DashboardWidgetRenderState.HIDDEN:
        return None

    component_kwargs = {
        "className": build_dashboard_widget_shell_class_name(
            placement.spec,
            placement.render_state,
            extra_class_name=placement.class_name,
        ),
        "style": build_dashboard_widget_shell_style(
            placement.spec,
            style=placement.style,
        ),
    }
    if placement.component_id is not None:
        component_kwargs["id"] = placement.component_id

    return html.Section(
        _resolve_widget_children(placement),
        **component_kwargs,
    )


def build_dashboard_region_grid(
    region_spec: DashboardRegionSpec,
    placements: list[DashboardWidgetPlacement],
    *,
    component_id: str | None = None,
    class_name: str | None = None,
    style: dict[str, Any] | None = None,
) -> Any:
    """Render one responsive dashboard region grid from prepared placements."""

    rendered_widgets = [
        widget
        for widget in (
            build_dashboard_widget_shell(placement)
            for placement in sorted(
                placements,
                key=lambda placement: (placement.spec.priority, placement.spec.widget_id),
            )
        )
        if widget is not None
    ]
    return html.Div(
        rendered_widgets,
        id=component_id,
        className=build_dashboard_region_class_name(
            region_spec,
            extra_class_name=class_name,
        ),
        style=build_dashboard_region_grid_style(
            region_spec,
            style=style,
        ),
    )


__all__ = [
    "DashboardWidgetPlacement",
    "build_dashboard_widget_style",
    "build_dashboard_widget_surface_style",
    "build_dashboard_region_class_name",
    "build_dashboard_region_grid",
    "build_dashboard_region_grid_style",
    "build_dashboard_widget_shell",
    "build_dashboard_widget_shell_class_name",
    "build_dashboard_widget_shell_style",
    "create_dashboard_widget_placement",
]
