"""Scenario helpers for lightweight A/B comparison setup."""

from dataclasses import fields, replace
from datetime import time
from enum import Enum
from typing import Any

from scenarios.field_schema import (
    get_scenario_field_categories,
    get_scenario_field_labels,
)
from scenarios.presets import get_scenario_preset
from scenarios.scenario import (
    ArrivalMode,
    ArrivalProfileShape,
    ChargingStrategy,
    DepartureMode,
    FeederEVAllocationMethod,
    PowerQualityPhaseAllocationMethod,
    Scenario,
    copy_scenario_with_updates,
    create_internal_scenario,
)


ScenarioData = dict[str, Any]
ScenarioComparisonData = dict[str, Any]
COMPARISON_SOURCE_MODIFIED_COPY = "modified_copy"
COMPARISON_SOURCE_TEMPLATE = "template"
COMPARISON_SOURCES = frozenset(
    (
        COMPARISON_SOURCE_MODIFIED_COPY,
        COMPARISON_SOURCE_TEMPLATE,
    )
)


class _UnsetValue:
    """Sentinel type for omitted Scenario B update values."""


_UNSET = _UnsetValue()
ScenarioBIntUpdate = int | None | _UnsetValue
ScenarioBFloatUpdate = float | None | _UnsetValue

SCENARIO_B_EDITABLE_FIELDS = frozenset(
    (
        "vehicles",
        "charger_count",
        "charger_power",
        "grid_capacity",
    )
)
SCENARIO_B_TEMPLATE_SHARED_FIELDS = frozenset(
    (
        "planning_margin_percent",
        "charging_strategy",
    )
)
SCENARIO_ASSUMPTION_LABELS = get_scenario_field_labels()
SCENARIO_ASSUMPTION_CATEGORY_LABELS = get_scenario_field_categories()
_KW_FIELDS = frozenset(
    (
        "charger_power",
        "grid_capacity",
        "transformer_capacity_kw",
        "transformer_other_load_kw",
        "feeder_capacity_kw",
        "feeder_base_load_kw",
    )
)
_PERCENT_FIELDS = frozenset(
    (
        "single_phase_charger_share_percent",
        "planning_margin_percent",
        "request_energy_variability_percent",
    )
)
_ENUM_STYLE_FIELDS = frozenset(
    (
        "arrival_mode",
        "arrival_profile_shape",
        "departure_mode",
        "feeder_ev_allocation_method",
        "power_quality_phase_allocation_method",
    )
)


def duplicate_scenario(scenario: Scenario) -> Scenario:
    """Return an independent scenario copy with the same assumptions."""
    return copy_scenario_with_updates(scenario)


def scenario_to_dict(scenario: Scenario) -> ScenarioData:
    """Return a Dash-store-safe dictionary representation of a scenario."""
    data: ScenarioData = {}
    for field in fields(Scenario):
        value = getattr(scenario, field.name)
        if isinstance(value, time):
            data[field.name] = _time_to_string(value)
        elif field.name == "feeder_allocation_shares" and value is not None:
            data[field.name] = list(value)
        elif isinstance(value, Enum):
            data[field.name] = value.value
        else:
            data[field.name] = value

    return data


def scenario_from_dict(data: ScenarioData) -> Scenario:
    """Rebuild and validate a scenario from serialized scenario data."""
    scenario_params = {
        "vehicles": data["vehicles"],
        "daily_energy_per_vehicle": data["daily_energy_per_vehicle"],
        "request_energy_variability_percent": data.get(
            "request_energy_variability_percent",
            0.0,
        ),
        "charger_count": data["charger_count"],
        "charger_power": data["charger_power"],
        "grid_capacity": data["grid_capacity"],
        "transformer_capacity_kw": data.get("transformer_capacity_kw"),
        "transformer_other_load_kw": data.get("transformer_other_load_kw", 0.0),
        "feeder_count": data.get("feeder_count", 1),
        "feeder_capacity_kw": data.get("feeder_capacity_kw"),
        "feeder_base_load_kw": data.get("feeder_base_load_kw", 0.0),
        "feeder_ev_allocation_method": FeederEVAllocationMethod(
            data.get(
                "feeder_ev_allocation_method",
                FeederEVAllocationMethod.BY_CHARGER_COUNT.value,
            )
        ),
        "feeder_allocation_shares": data.get("feeder_allocation_shares"),
        "single_phase_charger_share_percent": data.get(
            "single_phase_charger_share_percent",
            0.0,
        ),
        "charger_harmonic_factor": data.get("charger_harmonic_factor", 1.0),
        "power_quality_phase_allocation_method": PowerQualityPhaseAllocationMethod(
            data.get(
                "power_quality_phase_allocation_method",
                PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN.value,
            )
        ),
        "planning_margin_percent": data["planning_margin_percent"],
        "charging_window_start": _time_from_string(data["charging_window_start"]),
        "charging_window_end": _time_from_string(data["charging_window_end"]),
        "arrival_window_start": _time_from_string(
            data.get("arrival_window_start", data["charging_window_start"])
        ),
        "arrival_window_end": _time_from_string(
            data.get("arrival_window_end", data["charging_window_start"])
        ),
        "arrival_mode": ArrivalMode(
            data.get("arrival_mode", ArrivalMode.PROFILE.value)
        ),
        "arrival_profile_shape": ArrivalProfileShape(
            data.get("arrival_profile_shape", ArrivalProfileShape.FRONT_LOADED.value)
        ),
        "departure_mode": DepartureMode(
            data.get("departure_mode", DepartureMode.WINDOW_END.value)
        ),
        "session_dwell_minutes": data.get("session_dwell_minutes"),
        "departure_time_spread_minutes": data.get(
            "departure_time_spread_minutes",
            0,
        ),
        "charger_service_max_waiting_time_minutes": data.get(
            "charger_service_max_waiting_time_minutes",
            30,
        ),
        "charging_strategy": ChargingStrategy(data["charging_strategy"]),
    }

    if (
        scenario_params["vehicles"] == 0
        or scenario_params["charger_count"] == 0
    ):
        return create_internal_scenario(**scenario_params)

    return Scenario(
        **scenario_params,
    )


def create_scenario_comparison_snapshot(
    scenario_a: Scenario,
    *,
    comparison_source: str = COMPARISON_SOURCE_MODIFIED_COPY,
    selected_template: str | None = None,
) -> ScenarioComparisonData:
    """Return serializable Scenario A and Scenario B snapshot data."""
    scenario_a_data = scenario_to_dict(scenario_a)
    comparison_source = _validate_comparison_source(comparison_source)

    if (
        comparison_source == COMPARISON_SOURCE_TEMPLATE
        and selected_template is not None
    ):
        scenario_b_data = _scenario_data_from_template(selected_template)
    else:
        scenario_b_data = scenario_to_dict(duplicate_scenario(scenario_a))

    return normalize_scenario_comparison_data(
        {
            "scenario_a": scenario_a_data,
            "scenario_b": scenario_b_data,
            "comparison_source": comparison_source,
            "selected_template": selected_template,
        }
    )


def update_scenario_b(
    scenario_b: Scenario,
    *,
    vehicles: ScenarioBIntUpdate = _UNSET,
    charger_count: ScenarioBIntUpdate = _UNSET,
    charger_power: ScenarioBFloatUpdate = _UNSET,
    grid_capacity: ScenarioBFloatUpdate = _UNSET,
) -> Scenario:
    """Return Scenario B with only Phase 6 editable fields changed."""
    updates = {
        field_name: value
        for field_name, value in (
            ("vehicles", vehicles),
            ("charger_count", charger_count),
            ("charger_power", charger_power),
            ("grid_capacity", grid_capacity),
        )
        if not isinstance(value, _UnsetValue)
    }
    return replace(scenario_b, **updates)


def update_scenario_b_in_comparison_data(
    comparison_data: ScenarioComparisonData,
    *,
    vehicles: ScenarioBIntUpdate = _UNSET,
    charger_count: ScenarioBIntUpdate = _UNSET,
    charger_power: ScenarioBFloatUpdate = _UNSET,
    grid_capacity: ScenarioBFloatUpdate = _UNSET,
) -> ScenarioComparisonData:
    """Return stored comparison data with an updated Scenario B snapshot."""
    normalized_data = normalize_scenario_comparison_data(comparison_data)
    scenario_b = scenario_from_dict(normalized_data["scenario_b"])
    updated_scenario_b = update_scenario_b(
        scenario_b,
        vehicles=vehicles,
        charger_count=charger_count,
        charger_power=charger_power,
        grid_capacity=grid_capacity,
    )
    return normalize_scenario_comparison_data(
        {
            "scenario_a": dict(normalized_data["scenario_a"]),
            "scenario_b": scenario_to_dict(updated_scenario_b),
            "comparison_source": normalized_data["comparison_source"],
            "selected_template": normalized_data["selected_template"],
        }
    )


def update_scenario_a_in_comparison_data(
    comparison_data: ScenarioComparisonData,
    scenario_a: Scenario,
) -> ScenarioComparisonData:
    """Return comparison data rebased onto the current Scenario A."""
    normalized_data = normalize_scenario_comparison_data(comparison_data)
    comparison_source = normalized_data["comparison_source"]
    selected_template = normalized_data["selected_template"]
    if (
        comparison_source == COMPARISON_SOURCE_TEMPLATE
        and selected_template is not None
    ):
        return create_scenario_comparison_snapshot(
            scenario_a,
            comparison_source=COMPARISON_SOURCE_TEMPLATE,
            selected_template=selected_template,
        )

    return normalize_scenario_comparison_data(
        {
            "scenario_a": scenario_to_dict(scenario_a),
            "scenario_b": dict(normalized_data["scenario_b"]),
            "comparison_source": comparison_source,
            "selected_template": selected_template,
        }
    )


def normalize_scenario_comparison_data(
    comparison_data: ScenarioComparisonData,
) -> ScenarioComparisonData:
    """Return comparison data with stable defaults and a normalized Scenario B."""
    scenario_a_data = _normalize_scenario_snapshot(comparison_data["scenario_a"])
    scenario_b_data = _normalize_scenario_snapshot(
        comparison_data.get("scenario_b", scenario_a_data)
    )
    comparison_source = _validate_comparison_source(
        comparison_data.get(
            "comparison_source",
            COMPARISON_SOURCE_MODIFIED_COPY,
        )
    )
    selected_template = comparison_data.get("selected_template")
    normalized_scenario_b = _build_normalized_scenario_b_snapshot(
        scenario_a_data,
        scenario_b_data,
        comparison_source=comparison_source,
        selected_template=selected_template,
    )
    return {
        "scenario_a": scenario_a_data,
        "scenario_b": scenario_b_data,
        "comparison_source": comparison_source,
        "selected_template": selected_template,
        "normalized_scenario_b": normalized_scenario_b,
    }


def get_normalized_scenario_b_snapshot(
    comparison_data: ScenarioComparisonData,
) -> ScenarioData:
    """Return the canonical Scenario B snapshot for comparison execution."""
    return dict(normalize_scenario_comparison_data(comparison_data)["normalized_scenario_b"])


def summarize_scenario_assumption_differences(
    comparison_data: ScenarioComparisonData,
) -> tuple[str, ...]:
    """Return human-readable Scenario A vs Scenario B assumption differences."""
    normalized_data = normalize_scenario_comparison_data(comparison_data)
    scenario_a_data = normalized_data["scenario_a"]
    scenario_b_data = normalized_data["normalized_scenario_b"]
    summaries: list[str] = []

    for field in fields(Scenario):
        scenario_a_value = scenario_a_data[field.name]
        scenario_b_value = scenario_b_data[field.name]
        if scenario_a_value == scenario_b_value:
            continue

        label = SCENARIO_ASSUMPTION_LABELS.get(
            field.name,
            field.name.replace("_", " ").title(),
        )
        summaries.append(
            (
                f"{label}: "
                f"{_format_assumption_value(field.name, scenario_a_value)} -> "
                f"{_format_assumption_value(field.name, scenario_b_value)}"
            )
        )

    if not summaries:
        return ("Comparison scenario matches the current scenario.",)

    return tuple(summaries)


def summarize_scenario_assumption_change_overview(
    comparison_data: ScenarioComparisonData,
) -> dict[str, Any]:
    """Return compact Scenario A vs B change metadata for disclosure-first UI."""

    normalized_data = normalize_scenario_comparison_data(comparison_data)
    scenario_a_data = normalized_data["scenario_a"]
    scenario_b_data = normalized_data["normalized_scenario_b"]
    change_items: list[dict[str, str]] = []

    for field in fields(Scenario):
        scenario_a_value = scenario_a_data[field.name]
        scenario_b_value = scenario_b_data[field.name]
        if scenario_a_value == scenario_b_value:
            continue

        label = SCENARIO_ASSUMPTION_LABELS.get(
            field.name,
            field.name.replace("_", " ").title(),
        )
        change_items.append(
            {
                "category": SCENARIO_ASSUMPTION_CATEGORY_LABELS.get(
                    field.name,
                    "Other",
                ),
                "summary": (
                    f"{label}: "
                    f"{_format_assumption_value(field.name, scenario_a_value)} -> "
                    f"{_format_assumption_value(field.name, scenario_b_value)}"
                ),
            }
        )

    if not change_items:
        return {
            "change_count": 0,
            "category_counts": (),
            "highlights": (),
            "all_summaries": ("Comparison scenario matches the current scenario.",),
        }

    category_counts: dict[str, int] = {}
    for item in change_items:
        category = item["category"]
        category_counts[category] = category_counts.get(category, 0) + 1

    all_summaries = tuple(item["summary"] for item in change_items)
    return {
        "change_count": len(change_items),
        "category_counts": tuple(category_counts.items()),
        "highlights": all_summaries[:3],
        "all_summaries": all_summaries,
    }


def _build_normalized_scenario_b_snapshot(
    scenario_a_data: ScenarioData,
    scenario_b_data: ScenarioData,
    *,
    comparison_source: str,
    selected_template: str | None,
) -> ScenarioData:
    """Return the canonical Scenario B snapshot for one comparison setup."""
    if (
        comparison_source == COMPARISON_SOURCE_TEMPLATE
        and selected_template is not None
    ):
        template_data = _scenario_data_from_template(selected_template)
        return _apply_template_shared_overrides(template_data, scenario_a_data)

    return dict(scenario_b_data)


def _scenario_data_from_template(template_id: str) -> ScenarioData:
    """Return serialized scenario data for one registered template."""
    preset = get_scenario_preset(template_id)
    if preset.scenario is None:
        raise ValueError(
            f"Scenario template {template_id!r} does not define simulation inputs."
        )

    return scenario_to_dict(preset.scenario)


def _validate_comparison_source(comparison_source: Any) -> str:
    """Return one supported comparison source identifier."""
    if comparison_source not in COMPARISON_SOURCES:
        raise ValueError(
            "comparison_source must be one of "
            f"{sorted(COMPARISON_SOURCES)!r}."
        )

    return str(comparison_source)


def _apply_template_shared_overrides(
    template_data: ScenarioData,
    scenario_a_data: ScenarioData,
) -> ScenarioData:
    """Keep comparison-wide settings aligned when Scenario B uses a template."""
    normalized_data = dict(template_data)
    for field_name in SCENARIO_B_TEMPLATE_SHARED_FIELDS:
        normalized_data[field_name] = scenario_a_data[field_name]

    return normalized_data


def _normalize_scenario_snapshot(data: ScenarioData) -> ScenarioData:
    """Return one canonical scenario snapshot while tolerating legacy keys."""
    return scenario_to_dict(scenario_from_dict(dict(data)))


def _format_assumption_value(field_name: str, value: Any) -> str:
    """Format one scenario assumption value for a human-readable summary."""
    if value is None:
        return "None"

    if field_name == "daily_energy_per_vehicle" and isinstance(value, (int, float)):
        return f"{value:,.1f} kWh"
    if field_name == "session_dwell_minutes" and isinstance(value, (int, float)):
        return f"{int(value)} minutes"
    if (
        field_name == "departure_time_spread_minutes"
        and isinstance(value, (int, float))
    ):
        return f"{int(value)} minutes"
    if field_name in _KW_FIELDS and isinstance(value, (int, float)):
        return f"{value:,.1f} kW"
    if field_name in _PERCENT_FIELDS and isinstance(value, (int, float)):
        return f"{value:,.1f}%"
    if field_name == "charger_harmonic_factor" and isinstance(value, (int, float)):
        return f"{value:,.2f}"
    if field_name in _ENUM_STYLE_FIELDS and isinstance(value, str):
        return value.replace("_", " ").title()
    if isinstance(value, float):
        return f"{value:,.1f}"

    return str(value)


def _time_to_string(value: time) -> str:
    """Return a stable HH:MM representation for Dash storage."""
    return value.strftime("%H:%M")


def _time_from_string(value: Any) -> time:
    """Parse a stored HH:MM time value."""
    if not isinstance(value, str):
        raise TypeError("Stored scenario time values must be strings.")

    try:
        hour_text, minute_text = value.split(":")
        return time(int(hour_text), int(minute_text))
    except (TypeError, ValueError) as exc:
        raise ValueError("Stored scenario time values must use HH:MM format.") from exc
