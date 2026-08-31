"""State helpers for preset-backed editable scenario configuration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
import math
from typing import Any

from scenarios.comparison import (
    COMPARISON_SOURCE_MODIFIED_COPY,
    ScenarioComparisonData,
    create_scenario_comparison_snapshot,
    get_normalized_scenario_b_snapshot,
    normalize_scenario_comparison_data,
    scenario_from_dict,
    scenario_to_dict,
    update_scenario_b_in_comparison_data,
)
from scenarios.field_schema import (
    get_scenario_field_definition,
    list_scenario_field_definitions,
)
from scenarios.presets import get_scenario_preset
from scenarios.scenario import (
    ChargingStrategy,
    DepartureMode,
    FeederEVAllocationMethod,
    Scenario,
)


ACTIVE_SCENARIO_STATE_SCHEMA_VERSION = 3
SESSION_DWELL_DEFAULT_MINUTES = 60
SCENARIO_STATE_FIELD_NAMES = tuple(
    field.field_name for field in list_scenario_field_definitions()
)


def build_scenario_metadata_from_preset_id(preset_id: str) -> dict[str, Any]:
    """Return stable scenario metadata derived from one preset."""

    preset = get_scenario_preset(preset_id)
    return {
        "name": preset.label,
        "description": preset.purpose,
        "assumptions": list(preset.key_assumptions),
    }


def create_preset_initialized_scenario(
    preset_id: str,
    *,
    charging_strategy_value: str | None = None,
) -> Scenario:
    """Return a preset-seeded validated scenario for the editable state layer."""

    preset = get_scenario_preset(preset_id)
    if preset.scenario is None:
        raise ValueError(
            f"Scenario preset {preset_id!r} does not define simulation inputs."
        )

    if charging_strategy_value is None:
        return preset.scenario

    return replace(
        preset.scenario,
        charging_strategy=ChargingStrategy(charging_strategy_value),
    )


def _normalize_active_scenario_parameters(
    parameters: Scenario | dict[str, Any],
) -> dict[str, Any]:
    if isinstance(parameters, Scenario):
        return scenario_to_dict(parameters)

    return scenario_to_dict(scenario_from_dict(dict(parameters)))


def is_scenario_modified_from_preset(
    preset_id: str,
    parameters: Scenario | dict[str, Any],
) -> bool:
    """Return whether parameters differ from the selected preset defaults."""

    preset_defaults = scenario_to_dict(create_preset_initialized_scenario(preset_id))
    normalized_parameters = _normalize_active_scenario_parameters(parameters)
    return normalized_parameters != preset_defaults


def create_active_scenario_state(
    preset_id: str,
    parameters: Scenario | dict[str, Any],
    *,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the canonical active-scenario store payload."""

    parameter_data = _normalize_active_scenario_parameters(parameters)
    return {
        "schema_version": ACTIVE_SCENARIO_STATE_SCHEMA_VERSION,
        "preset": {
            "preset_id": preset_id,
            "is_modified": is_scenario_modified_from_preset(
                preset_id,
                parameter_data,
            ),
        },
        "metadata": (
            dict(metadata)
            if metadata is not None
            else build_scenario_metadata_from_preset_id(preset_id)
        ),
        "parameters": parameter_data,
    }


def apply_preset_defaults_to_active_scenario_state(
    preset_id: str,
    *,
    charging_strategy_value: str | None = None,
) -> dict[str, Any]:
    """Return active state reseeded from the selected preset template."""

    return create_active_scenario_state(
        preset_id,
        create_preset_initialized_scenario(
            preset_id,
            charging_strategy_value=charging_strategy_value,
        ),
    )


def get_active_scenario_preset_id(active_scenario_state: dict[str, Any]) -> str | None:
    """Return the selected preset id from new or legacy active state."""

    preset = active_scenario_state.get("preset")
    if isinstance(preset, dict):
        preset_id = preset.get("preset_id")
        if isinstance(preset_id, str):
            return preset_id

    legacy_preset_id = active_scenario_state.get("preset_id")
    if isinstance(legacy_preset_id, str):
        return legacy_preset_id

    return None


def get_active_scenario_is_modified(active_scenario_state: dict[str, Any]) -> bool:
    """Return whether the active scenario differs from its preset defaults."""

    preset = active_scenario_state.get("preset")
    if isinstance(preset, dict):
        is_modified = preset.get("is_modified")
        if isinstance(is_modified, bool):
            return is_modified

    preset_id = get_active_scenario_preset_id(active_scenario_state)
    if preset_id is None:
        return False

    try:
        return is_scenario_modified_from_preset(
            preset_id,
            get_active_scenario_parameters(active_scenario_state),
        )
    except KeyError:
        return False


def get_active_scenario_metadata(
    active_scenario_state: dict[str, Any],
) -> dict[str, Any]:
    """Return scenario metadata from state, deriving it from the preset if needed."""

    metadata = active_scenario_state.get("metadata")
    if isinstance(metadata, dict):
        return dict(metadata)

    preset_id = get_active_scenario_preset_id(active_scenario_state)
    if preset_id is None:
        return {}

    try:
        return build_scenario_metadata_from_preset_id(preset_id)
    except KeyError:
        return {}


def get_active_scenario_parameters(
    active_scenario_state: dict[str, Any],
) -> dict[str, Any]:
    """Return canonical editable parameter values from new or legacy state."""

    parameters = active_scenario_state.get("parameters")
    if isinstance(parameters, dict):
        return dict(parameters)

    legacy_parameters = active_scenario_state.get("scenario")
    if isinstance(legacy_parameters, dict):
        return dict(legacy_parameters)

    raise KeyError("Active scenario state does not contain scenario parameters.")


def active_scenario_from_state(active_scenario_state: dict[str, Any]) -> Scenario:
    """Rebuild a validated Scenario from active state parameters."""

    return scenario_from_dict(get_active_scenario_parameters(active_scenario_state))


def create_scenario_comparison_state(
    active_scenario_state: dict[str, Any],
    *,
    comparison_source: str = COMPARISON_SOURCE_MODIFIED_COPY,
    selected_template: str | None = None,
) -> ScenarioComparisonData:
    """Return canonical Scenario A/B comparison state from active state."""

    return create_scenario_comparison_snapshot(
        active_scenario_from_state(active_scenario_state),
        comparison_source=comparison_source,
        selected_template=selected_template,
    )


def comparison_scenarios_from_state(
    comparison_state: ScenarioComparisonData,
) -> tuple[Scenario, Scenario]:
    """Return validated Scenario A and normalized Scenario B from comparison state."""

    normalized_comparison_state = normalize_scenario_comparison_data(comparison_state)
    return (
        scenario_from_dict(normalized_comparison_state["scenario_a"]),
        scenario_from_dict(
            get_normalized_scenario_b_snapshot(normalized_comparison_state)
        ),
    )


def scenario_b_editable_values_from_state(
    comparison_state: ScenarioComparisonData,
) -> tuple[Any, Any, Any, Any]:
    """Return raw Scenario B edit values from comparison state."""

    normalized_comparison_state = normalize_scenario_comparison_data(comparison_state)
    scenario_b = scenario_from_dict(normalized_comparison_state["scenario_b"])
    return (
        scenario_b.vehicles,
        scenario_b.charger_count,
        scenario_b.charger_power,
        scenario_b.grid_capacity,
    )


def scenario_field_values_from_state(
    active_scenario_state: dict[str, Any],
    *,
    field_names: Sequence[str] = SCENARIO_STATE_FIELD_NAMES,
) -> tuple[Any, ...]:
    """Return store-compatible field values for the requested scenario fields."""

    parameters = get_active_scenario_parameters(active_scenario_state)
    return tuple(
        _scenario_field_value_from_parameters(field_name, parameters)
        for field_name in field_names
    )


def coerce_scenario_field_value(field_name: str, value: Any) -> Any:
    """Return one store value coerced to the canonical scenario-field form."""

    field_definition = get_scenario_field_definition(field_name)

    if field_definition.input_kind == "sequence":
        return _parse_sequence_value(value)

    if field_definition.value_type == "int":
        if value is None:
            raise ValueError(f"{field_definition.label} is required.")
        return _coerce_whole_number_value(value, label=field_definition.label)

    if field_definition.value_type == "optional_int":
        if value in (None, ""):
            return None
        return _coerce_whole_number_value(value, label=field_definition.label)

    if field_definition.value_type == "float":
        if value is None:
            raise ValueError(f"{field_definition.label} is required.")
        return float(value)

    return value


def scenario_parameters_from_input_values(
    active_scenario_state: dict[str, Any],
    field_values: Mapping[str, Any],
) -> dict[str, Any]:
    """Return canonical scenario parameters rebuilt from store/input values."""

    existing_parameters = get_active_scenario_parameters(active_scenario_state)
    normalized_parameters = dict(existing_parameters)
    for field_name, value in field_values.items():
        normalized_parameters[field_name] = coerce_scenario_field_value(
            field_name,
            value,
        )

    return _ensure_dependent_defaults(
        normalized_parameters,
        existing_parameters,
    )


def update_scenario_b_in_comparison_state(
    comparison_state: ScenarioComparisonData,
    *,
    vehicles: Any,
    charger_count: Any,
    charger_power: Any,
    grid_capacity: Any,
) -> ScenarioComparisonData:
    """Return comparison state with Scenario B edits coerced from store values."""

    return update_scenario_b_in_comparison_data(
        comparison_state,
        vehicles=_coerce_whole_number_value(
            vehicles,
            label="Scenario B number of vehicles",
        ),
        charger_count=_coerce_whole_number_value(
            charger_count,
            label="Scenario B number of chargers",
        ),
        charger_power=float(charger_power),
        grid_capacity=float(grid_capacity),
    )


def update_active_scenario_parameters(
    active_scenario_state: dict[str, Any],
    *,
    parameter_updates: dict[str, Any],
) -> dict[str, Any]:
    """Return active state with only the supplied parameter edits applied."""

    preset_id = get_active_scenario_preset_id(active_scenario_state)
    if preset_id is None:
        raise KeyError("Active scenario state does not contain a selected preset.")

    next_parameters = get_active_scenario_parameters(active_scenario_state)
    next_parameters.update(parameter_updates)
    return create_active_scenario_state(
        preset_id,
        next_parameters,
        metadata=get_active_scenario_metadata(active_scenario_state),
    )


def reset_active_scenario_to_preset_defaults(
    active_scenario_state: dict[str, Any],
    *,
    charging_strategy_value: str | None = None,
) -> dict[str, Any]:
    """Return active state reset to the selected preset defaults."""

    preset_id = get_active_scenario_preset_id(active_scenario_state)
    if preset_id is None:
        raise KeyError("Active scenario state does not contain a selected preset.")

    return apply_preset_defaults_to_active_scenario_state(
        preset_id,
        charging_strategy_value=charging_strategy_value,
    )


def _format_sequence_value(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, (list, tuple)):
        return ", ".join(
            (
                str(int(item))
                if float(item).is_integer()
                else f"{float(item):.2f}".rstrip("0").rstrip(".")
            )
            for item in value
        )

    return str(value)


def _scenario_field_value_from_parameters(
    field_name: str,
    parameters: dict[str, Any],
) -> Any:
    value = parameters[field_name]
    if field_name == "feeder_allocation_shares":
        return _format_sequence_value(value)

    return value


def _parse_sequence_value(value: Any) -> list[float] | None:
    if value is None:
        return None

    if isinstance(value, str):
        stripped_value = value.strip()
        if not stripped_value:
            return None

        try:
            return [
                float(item.strip())
                for item in stripped_value.split(",")
                if item.strip()
            ]
        except ValueError as exc:
            raise ValueError(
                "Feeder allocation shares must be comma-separated numeric values."
            ) from exc

    if isinstance(value, (list, tuple)):
        return [float(item) for item in value]

    raise TypeError("Feeder allocation shares must be provided as text.")


def _coerce_whole_number_value(value: Any, *, label: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{label} must be numeric.")

    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{label} must be numeric.") from exc

    if not math.isfinite(numeric_value):
        raise ValueError(f"{label} must be finite.")

    rounded_value = round(numeric_value)
    if not math.isclose(numeric_value, rounded_value, abs_tol=1e-9):
        raise ValueError(f"{label} must be a whole number.")

    return int(rounded_value)


def _ensure_dependent_defaults(
    parameters: dict[str, Any],
    existing_parameters: dict[str, Any],
) -> dict[str, Any]:
    normalized_parameters = dict(parameters)
    existing_charging_window_start = existing_parameters.get(
        "charging_window_start"
    )
    next_charging_window_start = normalized_parameters["charging_window_start"]

    if next_charging_window_start != existing_charging_window_start:
        if (
            normalized_parameters["arrival_window_start"]
            == existing_parameters.get("arrival_window_start")
            and existing_parameters.get("arrival_window_start")
            == existing_charging_window_start
        ):
            normalized_parameters["arrival_window_start"] = (
                next_charging_window_start
            )

        if (
            normalized_parameters["arrival_window_end"]
            == existing_parameters.get("arrival_window_end")
            and existing_parameters.get("arrival_window_end")
            == existing_charging_window_start
        ):
            normalized_parameters["arrival_window_end"] = (
                next_charging_window_start
            )

    departure_mode = normalized_parameters["departure_mode"]
    if departure_mode == DepartureMode.SESSION_DWELL.value:
        if normalized_parameters["session_dwell_minutes"] is None:
            normalized_parameters["session_dwell_minutes"] = (
                existing_parameters.get("session_dwell_minutes")
                or SESSION_DWELL_DEFAULT_MINUTES
            )

    feeder_method = normalized_parameters["feeder_ev_allocation_method"]
    if feeder_method == FeederEVAllocationMethod.BY_CONFIGURED_SHARE.value:
        feeder_count = int(normalized_parameters["feeder_count"])
        shares = normalized_parameters["feeder_allocation_shares"]
        if shares is None or len(shares) != feeder_count:
            equal_share = 1.0 / feeder_count
            normalized_parameters["feeder_allocation_shares"] = [
                equal_share for _ in range(feeder_count)
            ]
    elif normalized_parameters["feeder_allocation_shares"] is None:
        normalized_parameters["feeder_allocation_shares"] = existing_parameters.get(
            "feeder_allocation_shares"
        )

    return normalized_parameters


__all__ = [
    "ACTIVE_SCENARIO_STATE_SCHEMA_VERSION",
    "SCENARIO_STATE_FIELD_NAMES",
    "SESSION_DWELL_DEFAULT_MINUTES",
    "active_scenario_from_state",
    "apply_preset_defaults_to_active_scenario_state",
    "build_scenario_metadata_from_preset_id",
    "comparison_scenarios_from_state",
    "coerce_scenario_field_value",
    "create_active_scenario_state",
    "create_preset_initialized_scenario",
    "create_scenario_comparison_state",
    "get_active_scenario_is_modified",
    "get_active_scenario_metadata",
    "get_active_scenario_parameters",
    "get_active_scenario_preset_id",
    "is_scenario_modified_from_preset",
    "reset_active_scenario_to_preset_defaults",
    "scenario_b_editable_values_from_state",
    "scenario_field_values_from_state",
    "scenario_parameters_from_input_values",
    "update_scenario_b_in_comparison_state",
    "update_active_scenario_parameters",
]
