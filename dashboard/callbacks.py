"""Compatibility module for dashboard callback helpers and registration."""

from dash import ctx, no_update
from insights import generate_insights
from metrics import (
    calculate_comparison_metrics,
    calculate_metrics,
    run_connection_capacity_sensitivity,
)
from simulation import simulate, simulate_strategy_comparison

from . import callback_rendering as _callback_rendering
from . import callback_state as _callback_state
from .callback_registration import register_callbacks


def _rendering_exports() -> dict[str, object]:
    exported: dict[str, object] = {}
    for name in getattr(_callback_rendering, "__all__", ()):
        exported[name] = getattr(_callback_rendering, name)
    return exported


globals().update(_rendering_exports())
globals().update(
    {name: getattr(_callback_state, name) for name in _callback_state.__all__}
)

__all__ = [
    "ctx",
    "generate_insights",
    "no_update",
    "register_callbacks",
    "run_connection_capacity_sensitivity",
    "simulate",
    "simulate_strategy_comparison",
    "calculate_metrics",
    "calculate_comparison_metrics",
    *_rendering_exports().keys(),
    *_callback_state.__all__,
]
