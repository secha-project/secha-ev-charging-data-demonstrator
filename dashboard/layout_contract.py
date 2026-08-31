"""Shared dashboard region and widget layout contract.

This module defines the responsive region, widget, visibility, and render-state
vocabulary used by the dashboard views so tabs can share one consistent layout
model without embedding layout rules directly in each view.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Self
from collections.abc import Mapping


DASHBOARD_GRID_COLUMNS = 12


class DashboardBreakpoint(str, Enum):
    """Responsive breakpoints supported by the dashboard contract."""

    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"


class DashboardWidgetHeightHint(str, Enum):
    """Relative vertical size hint for one dashboard widget."""

    COMPACT = "compact"
    STANDARD = "standard"
    TALL = "tall"


class DashboardWidgetMode(str, Enum):
    """High-level presentation mode for one dashboard widget."""

    HERO = "hero"
    SUMMARY = "summary"
    EVIDENCE = "evidence"
    DETAIL = "detail"
    STATUS = "status"
    CHART = "chart"
    TABLE = "table"


class DashboardEmptyStatePolicy(str, Enum):
    """How a widget should behave when it has no meaningful content."""

    HIDE = "hide"
    REPLACE_WITH_MESSAGE = "replace_with_message"
    SHOW_PLACEHOLDER = "show_placeholder"
    ALWAYS_SHOW = "always_show"


class DashboardWidgetRenderState(str, Enum):
    """The presentation state selected for one widget instance."""

    HIDDEN = "hidden"
    CONTENT = "content"
    MESSAGE = "message"
    PLACEHOLDER = "placeholder"


def _coerce_breakpoint_key(
    value: DashboardBreakpoint | str,
) -> DashboardBreakpoint:
    """Return one normalized breakpoint key."""

    if isinstance(value, DashboardBreakpoint):
        return value

    return DashboardBreakpoint(value)


@dataclass(frozen=True)
class DashboardWidgetSpan:
    """Responsive column span for one widget within the shared 12-column grid."""

    mobile: int = DASHBOARD_GRID_COLUMNS
    tablet: int = DASHBOARD_GRID_COLUMNS
    desktop: int = DASHBOARD_GRID_COLUMNS

    def __post_init__(self) -> None:
        for label, value in (
            ("mobile", self.mobile),
            ("tablet", self.tablet),
            ("desktop", self.desktop),
        ):
            if not 1 <= value <= DASHBOARD_GRID_COLUMNS:
                raise ValueError(
                    f"{label} span must stay within 1..{DASHBOARD_GRID_COLUMNS}."
                )

    @classmethod
    def normalize(
        cls,
        value: Self | int | Mapping[DashboardBreakpoint | str, int] | None,
    ) -> Self:
        """Return a normalized responsive span definition.

        Missing breakpoints inherit from the next smaller breakpoint.
        `mobile` defaults to full width when omitted.
        """

        if value is None:
            return cls()

        if isinstance(value, cls):
            return value

        if isinstance(value, int):
            return cls(mobile=value, tablet=value, desktop=value)

        raw_values = {
            _coerce_breakpoint_key(key): raw_value for key, raw_value in value.items()
        }
        mobile = raw_values.get(DashboardBreakpoint.MOBILE, DASHBOARD_GRID_COLUMNS)
        tablet = raw_values.get(DashboardBreakpoint.TABLET, mobile)
        desktop = raw_values.get(DashboardBreakpoint.DESKTOP, tablet)
        return cls(mobile=mobile, tablet=tablet, desktop=desktop)

    def as_dict(self) -> dict[str, int]:
        """Return a JSON-safe span mapping."""

        return {
            DashboardBreakpoint.MOBILE.value: self.mobile,
            DashboardBreakpoint.TABLET.value: self.tablet,
            DashboardBreakpoint.DESKTOP.value: self.desktop,
        }


@dataclass(frozen=True)
class DashboardRegionColumns:
    """Responsive maximum column counts for one view region."""

    mobile: int = 1
    tablet: int = 2
    desktop: int = 3

    def __post_init__(self) -> None:
        for label, value in (
            ("mobile", self.mobile),
            ("tablet", self.tablet),
            ("desktop", self.desktop),
        ):
            if value < 1:
                raise ValueError(f"{label} region columns must be at least 1.")

    @classmethod
    def normalize(
        cls,
        value: Self | int | Mapping[DashboardBreakpoint | str, int] | None,
    ) -> Self:
        """Return normalized region-column counts across breakpoints."""

        if value is None:
            return cls()

        if isinstance(value, cls):
            return value

        if isinstance(value, int):
            return cls(mobile=value, tablet=value, desktop=value)

        raw_values = {
            _coerce_breakpoint_key(key): raw_value for key, raw_value in value.items()
        }
        mobile = raw_values.get(DashboardBreakpoint.MOBILE, 1)
        tablet = raw_values.get(DashboardBreakpoint.TABLET, mobile)
        desktop = raw_values.get(DashboardBreakpoint.DESKTOP, tablet)
        return cls(mobile=mobile, tablet=tablet, desktop=desktop)

    def as_dict(self) -> dict[str, int]:
        """Return a JSON-safe region-column mapping."""

        return {
            DashboardBreakpoint.MOBILE.value: self.mobile,
            DashboardBreakpoint.TABLET.value: self.tablet,
            DashboardBreakpoint.DESKTOP.value: self.desktop,
        }


@dataclass(frozen=True)
class DashboardRegionSpec:
    """Declarative contract for one named layout region within a view."""

    region_id: str
    priority: int = 100
    columns: DashboardRegionColumns = field(default_factory=DashboardRegionColumns)
    allow_mixed_heights: bool = True
    prefer_full_width_children: bool = False

    def __post_init__(self) -> None:
        if not self.region_id.strip():
            raise ValueError("region_id must not be blank.")


@dataclass(frozen=True)
class DashboardWidgetSpec:
    """Declarative contract for one independently placeable dashboard widget."""

    widget_id: str
    region: str
    priority: int = 100
    span: DashboardWidgetSpan = field(default_factory=DashboardWidgetSpan)
    height_hint: DashboardWidgetHeightHint = DashboardWidgetHeightHint.STANDARD
    empty_state_policy: DashboardEmptyStatePolicy = (
        DashboardEmptyStatePolicy.SHOW_PLACEHOLDER
    )
    default_visible: bool = True
    visibility_rule: str | None = None
    mode_hint: DashboardWidgetMode | None = None
    group_hint: str | None = None

    def __post_init__(self) -> None:
        if not self.widget_id.strip():
            raise ValueError("widget_id must not be blank.")

        if not self.region.strip():
            raise ValueError("region must not be blank.")

        if self.visibility_rule is not None and not isinstance(self.visibility_rule, str):
            raise TypeError("visibility_rule must be a string label or None.")

        if self.group_hint is not None and not isinstance(self.group_hint, str):
            raise TypeError("group_hint must be a string label or None.")


def resolve_widget_visibility(
    widget: DashboardWidgetSpec,
    *,
    rule_result: bool | None = None,
) -> bool:
    """Return one resolved visibility state for a widget spec."""

    if rule_result is None:
        return widget.default_visible

    return rule_result


def resolve_widget_render_state(
    widget: DashboardWidgetSpec,
    *,
    has_meaningful_content: bool,
    rule_result: bool | None = None,
) -> DashboardWidgetRenderState:
    """Return the selected presentation state for one widget.

    Hidden widgets resolve to ``HIDDEN`` and should not reserve layout space.
    """

    if not resolve_widget_visibility(widget, rule_result=rule_result):
        return DashboardWidgetRenderState.HIDDEN

    if has_meaningful_content:
        return DashboardWidgetRenderState.CONTENT

    if widget.empty_state_policy == DashboardEmptyStatePolicy.HIDE:
        return DashboardWidgetRenderState.HIDDEN

    if widget.empty_state_policy == DashboardEmptyStatePolicy.REPLACE_WITH_MESSAGE:
        return DashboardWidgetRenderState.MESSAGE

    if widget.empty_state_policy == DashboardEmptyStatePolicy.SHOW_PLACEHOLDER:
        return DashboardWidgetRenderState.PLACEHOLDER

    return DashboardWidgetRenderState.CONTENT


__all__ = [
    "DASHBOARD_GRID_COLUMNS",
    "DashboardBreakpoint",
    "DashboardEmptyStatePolicy",
    "DashboardRegionColumns",
    "DashboardRegionSpec",
    "DashboardWidgetHeightHint",
    "DashboardWidgetMode",
    "DashboardWidgetRenderState",
    "DashboardWidgetSpan",
    "DashboardWidgetSpec",
    "resolve_widget_render_state",
    "resolve_widget_visibility",
]
