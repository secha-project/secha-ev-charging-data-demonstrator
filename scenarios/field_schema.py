"""Reusable schema and formatting helpers for editable scenario parameters."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import time
from enum import Enum
from typing import Any

from scenarios.scenario import (
    ArrivalMode,
    ArrivalProfileShape,
    ChargingStrategy,
    DepartureMode,
    FeederEVAllocationMethod,
    PowerQualityPhaseAllocationMethod,
    Scenario,
)


@dataclass(frozen=True)
class ScenarioFieldOption:
    """One allowed option for an enum-style scenario field."""

    value: str
    label: str


@dataclass(frozen=True)
class ScenarioFieldDefinition:
    """Schema metadata for one editable scenario field."""

    field_name: str
    label: str
    category: str
    description: str
    input_kind: str
    value_type: str
    unit: str | None = None
    min_value: int | float | None = None
    step: int | float | None = None
    options: tuple[ScenarioFieldOption, ...] = ()


@dataclass(frozen=True)
class ScenarioSummaryDefinition:
    """Display-oriented summary mapping backed by scenario fields."""

    summary_id: str
    label: str
    source_fields: tuple[str, ...]


def _titleize_enum_value(value: str) -> str:
    return value.replace("_", " ").title()


def _enum_options(enum_type: type[Enum]) -> tuple[ScenarioFieldOption, ...]:
    return tuple(
        ScenarioFieldOption(
            value=str(member.value),
            label=_titleize_enum_value(str(member.value)),
        )
        for member in enum_type
    )


_SCENARIO_FIELDS = (
    ScenarioFieldDefinition(
        field_name="vehicles",
        label="Number of vehicles",
        category="Fleet & Demand",
        description="Number of vehicles or charging sessions represented by the scenario.",
        input_kind="number",
        value_type="int",
        min_value=1,
        step=1,
    ),
    ScenarioFieldDefinition(
        field_name="daily_energy_per_vehicle",
        label="Daily energy per vehicle",
        category="Fleet & Demand",
        description="Average daily charging demand assigned to each vehicle.",
        input_kind="number",
        value_type="float",
        unit="kWh",
        min_value=0.1,
        step=0.1,
    ),
    ScenarioFieldDefinition(
        field_name="charger_count",
        label="Number of chargers",
        category="Charging Infrastructure",
        description="Installed charger count available to the modeled fleet.",
        input_kind="number",
        value_type="int",
        min_value=1,
        step=1,
    ),
    ScenarioFieldDefinition(
        field_name="charger_power",
        label="Charger power",
        category="Charging Infrastructure",
        description="Rated power per charger.",
        input_kind="number",
        value_type="float",
        unit="kW",
        min_value=0.1,
        step=0.1,
    ),
    ScenarioFieldDefinition(
        field_name="grid_capacity",
        label="Grid connection capacity",
        category="Grid & Capacity",
        description="Available EV charging connection capacity.",
        input_kind="number",
        value_type="float",
        unit="kW",
        min_value=0.1,
        step=0.1,
    ),
    ScenarioFieldDefinition(
        field_name="request_energy_variability_percent",
        label="Request energy variability",
        category="Fleet & Demand",
        description="Deterministic per-request energy variability around the average demand.",
        input_kind="number",
        value_type="float",
        unit="%",
        min_value=0.0,
        step=0.1,
    ),
    ScenarioFieldDefinition(
        field_name="transformer_capacity_kw",
        label="Transformer capacity",
        category="Grid & Capacity",
        description="Rated transformer capacity assigned to the scenario.",
        input_kind="number",
        value_type="float",
        unit="kW",
        min_value=0.1,
        step=0.1,
    ),
    ScenarioFieldDefinition(
        field_name="transformer_other_load_kw",
        label="Transformer other load",
        category="Grid & Capacity",
        description="Deterministic non-EV transformer background load.",
        input_kind="number",
        value_type="float",
        unit="kW",
        min_value=0.0,
        step=0.1,
    ),
    ScenarioFieldDefinition(
        field_name="feeder_count",
        label="Feeder count",
        category="Grid & Capacity",
        description="Number of modeled feeders sharing the EV load.",
        input_kind="number",
        value_type="int",
        min_value=1,
        step=1,
    ),
    ScenarioFieldDefinition(
        field_name="feeder_capacity_kw",
        label="Feeder capacity",
        category="Grid & Capacity",
        description="Rated capacity per feeder.",
        input_kind="number",
        value_type="float",
        unit="kW",
        min_value=0.1,
        step=0.1,
    ),
    ScenarioFieldDefinition(
        field_name="feeder_base_load_kw",
        label="Feeder base load",
        category="Grid & Capacity",
        description="Deterministic non-EV base load per feeder.",
        input_kind="number",
        value_type="float",
        unit="kW",
        min_value=0.0,
        step=0.1,
    ),
    ScenarioFieldDefinition(
        field_name="feeder_ev_allocation_method",
        label="Feeder EV allocation method",
        category="Grid & Capacity",
        description="Rule for allocating EV load across feeders.",
        input_kind="select",
        value_type="enum",
        options=_enum_options(FeederEVAllocationMethod),
    ),
    ScenarioFieldDefinition(
        field_name="feeder_allocation_shares",
        label="Feeder allocation shares",
        category="Grid & Capacity",
        description="Optional configured feeder shares used for explicit EV-load allocation.",
        input_kind="sequence",
        value_type="float_sequence",
    ),
    ScenarioFieldDefinition(
        field_name="single_phase_charger_share_percent",
        label="Single-phase charger share",
        category="Power Quality",
        description="Share of chargers modeled as single-phase power-quality sources.",
        input_kind="number",
        value_type="float",
        unit="%",
        min_value=0.0,
        step=0.1,
    ),
    ScenarioFieldDefinition(
        field_name="charger_harmonic_factor",
        label="Charger harmonic factor",
        category="Power Quality",
        description="Relative harmonic-severity factor used by the simplified PQ model.",
        input_kind="number",
        value_type="float",
        min_value=0.0,
        step=0.01,
    ),
    ScenarioFieldDefinition(
        field_name="power_quality_phase_allocation_method",
        label="Power-quality phase allocation",
        category="Power Quality",
        description="Deterministic phase-allocation rule for PQ modeling.",
        input_kind="select",
        value_type="enum",
        options=_enum_options(PowerQualityPhaseAllocationMethod),
    ),
    ScenarioFieldDefinition(
        field_name="planning_margin_percent",
        label="Planning margin",
        category="Grid & Capacity",
        description="Additional planning headroom applied to capacity sizing.",
        input_kind="number",
        value_type="float",
        unit="%",
        min_value=0.0,
        step=0.1,
    ),
    ScenarioFieldDefinition(
        field_name="charging_window_start",
        label="Charging allowed from",
        category="Operating Pattern",
        description="Time when the site begins allowing vehicles to charge.",
        input_kind="time",
        value_type="time",
    ),
    ScenarioFieldDefinition(
        field_name="charging_window_end",
        label="Charging allowed until",
        category="Operating Pattern",
        description="Time when the site stops allowing charging in this scenario.",
        input_kind="time",
        value_type="time",
    ),
    ScenarioFieldDefinition(
        field_name="arrival_window_start",
        label="Vehicle arrivals begin",
        category="Operating Pattern",
        description="Time when vehicles begin arriving and joining the charging queue.",
        input_kind="time",
        value_type="time",
    ),
    ScenarioFieldDefinition(
        field_name="arrival_window_end",
        label="Vehicle arrivals end",
        category="Operating Pattern",
        description="Time when the modeled arrival period finishes.",
        input_kind="time",
        value_type="time",
    ),
    ScenarioFieldDefinition(
        field_name="arrival_mode",
        label="Arrival mode",
        category="Operating Pattern",
        description="Arrival-generation mode for the vehicle-arrival window.",
        input_kind="select",
        value_type="enum",
        options=_enum_options(ArrivalMode),
    ),
    ScenarioFieldDefinition(
        field_name="arrival_profile_shape",
        label="Arrival profile shape",
        category="Operating Pattern",
        description="Deterministic arrival distribution shape.",
        input_kind="select",
        value_type="enum",
        options=_enum_options(ArrivalProfileShape),
    ),
    ScenarioFieldDefinition(
        field_name="departure_mode",
        label="Departure mode",
        category="Operating Pattern",
        description="How departure or deadline timing is interpreted.",
        input_kind="select",
        value_type="enum",
        options=_enum_options(DepartureMode),
    ),
    ScenarioFieldDefinition(
        field_name="session_dwell_minutes",
        label="Session dwell time",
        category="Operating Pattern",
        description="Typical session dwell time when departure mode uses dwell.",
        input_kind="number",
        value_type="optional_int",
        unit="minutes",
        min_value=15,
        step=15,
    ),
    ScenarioFieldDefinition(
        field_name="departure_time_spread_minutes",
        label="Departure time spread",
        category="Operating Pattern",
        description="Deterministic departure/deadline spread around the baseline.",
        input_kind="number",
        value_type="int",
        unit="minutes",
        min_value=0,
        step=15,
    ),
    ScenarioFieldDefinition(
        field_name="charger_service_max_waiting_time_minutes",
        label="Service waiting tolerance",
        category="Charging Infrastructure",
        description="Maximum acceptable waiting time used by the charger-planning rule.",
        input_kind="number",
        value_type="int",
        unit="minutes",
        min_value=0,
        step=15,
    ),
    ScenarioFieldDefinition(
        field_name="charging_strategy",
        label="Charging strategy",
        category="Operating Pattern",
        description="Single-scenario charging strategy used for the simulation run.",
        input_kind="select",
        value_type="enum",
        options=_enum_options(ChargingStrategy),
    ),
)

_SCENARIO_FIELDS_BY_NAME = {
    field.field_name: field for field in _SCENARIO_FIELDS
}

_SCENARIO_SUMMARIES = (
    ScenarioSummaryDefinition(
        summary_id="vehicles",
        label="Number of vehicles",
        source_fields=("vehicles",),
    ),
    ScenarioSummaryDefinition(
        summary_id="daily_energy_per_vehicle",
        label="Daily energy per vehicle",
        source_fields=("daily_energy_per_vehicle",),
    ),
    ScenarioSummaryDefinition(
        summary_id="charger_count",
        label="Number of chargers",
        source_fields=("charger_count",),
    ),
    ScenarioSummaryDefinition(
        summary_id="charger_power",
        label="Charger power",
        source_fields=("charger_power",),
    ),
    ScenarioSummaryDefinition(
        summary_id="grid_capacity",
        label="Grid connection capacity",
        source_fields=("grid_capacity",),
    ),
    ScenarioSummaryDefinition(
        summary_id="session_dwell_minutes",
        label="Session dwell time",
        source_fields=("session_dwell_minutes",),
    ),
    ScenarioSummaryDefinition(
        summary_id="single_phase_charger_share_percent",
        label="Single-phase charger share",
        source_fields=("single_phase_charger_share_percent",),
    ),
    ScenarioSummaryDefinition(
        summary_id="charger_harmonic_factor",
        label="Charger harmonic factor",
        source_fields=("charger_harmonic_factor",),
    ),
    ScenarioSummaryDefinition(
        summary_id="charging_window",
        label="Charging allowed window",
        source_fields=("charging_window_start", "charging_window_end"),
    ),
    ScenarioSummaryDefinition(
        summary_id="arrival_window",
        label="Vehicle arrival window",
        source_fields=("arrival_window_start", "arrival_window_end"),
    ),
)

_SCENARIO_SUMMARIES_BY_ID = {
    summary.summary_id: summary for summary in _SCENARIO_SUMMARIES
}


def list_scenario_field_definitions() -> tuple[ScenarioFieldDefinition, ...]:
    """Return all editable scenario field definitions in stable UI order."""

    return _SCENARIO_FIELDS


def get_scenario_field_definition(field_name: str) -> ScenarioFieldDefinition:
    """Return one field definition by scenario field name."""

    try:
        return _SCENARIO_FIELDS_BY_NAME[field_name]
    except KeyError as exc:
        raise KeyError(f"Unknown scenario field: {field_name!r}.") from exc


def list_scenario_summary_definitions() -> tuple[ScenarioSummaryDefinition, ...]:
    """Return stable display summaries backed by scenario fields."""

    return _SCENARIO_SUMMARIES


def get_scenario_summary_definition(summary_id: str) -> ScenarioSummaryDefinition:
    """Return one scenario summary definition by identifier."""

    try:
        return _SCENARIO_SUMMARIES_BY_ID[summary_id]
    except KeyError as exc:
        raise KeyError(f"Unknown scenario summary: {summary_id!r}.") from exc


def _format_time_value(value: Any) -> str:
    if isinstance(value, time):
        return value.strftime("%H:%M")
    if isinstance(value, str):
        return value
    raise TypeError("Scenario time values must be datetime.time or HH:MM strings.")


def _format_decimal_value(value: int | float, *, precision: int) -> str:
    numeric_value = float(value)
    if numeric_value.is_integer():
        return str(int(numeric_value))

    return f"{numeric_value:.{precision}f}".rstrip("0").rstrip(".")


def format_scenario_field_value(field_name: str, value: Any) -> str:
    """Return one planner-facing display value for a scenario field."""

    definition = get_scenario_field_definition(field_name)

    if value is None:
        return "None"

    if definition.input_kind == "time":
        return _format_time_value(value)

    if field_name == "charger_harmonic_factor" and isinstance(value, (int, float)):
        return _format_decimal_value(value, precision=2)

    if definition.value_type in {"int", "optional_int"} and isinstance(value, (int, float)):
        if definition.unit is not None:
            return f"{int(value)} {definition.unit}"
        return str(int(value))

    if definition.value_type == "float" and isinstance(value, (int, float)):
        formatted_value = _format_decimal_value(value, precision=1)
        if definition.unit == "%":
            return f"{formatted_value}%"
        if definition.unit is not None:
            return f"{formatted_value} {definition.unit}"
        return formatted_value

    if definition.value_type == "float_sequence" and isinstance(value, (list, tuple)):
        return ", ".join(
            _format_decimal_value(item, precision=2)
            for item in value
        )

    if definition.value_type == "enum":
        if isinstance(value, Enum):
            return _titleize_enum_value(str(value.value))
        if isinstance(value, str):
            return _titleize_enum_value(value)

    return str(value)


def _value_from_scenario_source(source: Scenario | dict[str, Any], field_name: str) -> Any:
    if isinstance(source, Scenario):
        return getattr(source, field_name)
    return source[field_name]


def get_scenario_summary_label(summary_id: str) -> str:
    """Return the default label for one display summary."""

    return get_scenario_summary_definition(summary_id).label


def format_scenario_summary_value(
    summary_id: str,
    source: Scenario | dict[str, Any],
) -> str:
    """Return one display-ready summary value from scenario-backed data."""

    summary = get_scenario_summary_definition(summary_id)

    if summary_id == "charging_window":
        start = _format_time_value(
            _value_from_scenario_source(source, "charging_window_start")
        )
        end = _format_time_value(
            _value_from_scenario_source(source, "charging_window_end")
        )
        return f"{start} - {end}"

    if summary_id == "arrival_window":
        start = _format_time_value(
            _value_from_scenario_source(source, "arrival_window_start")
        )
        end = _format_time_value(
            _value_from_scenario_source(source, "arrival_window_end")
        )
        return f"{start} - {end}"

    field_name = summary.source_fields[0]
    return format_scenario_field_value(
        field_name,
        _value_from_scenario_source(source, field_name),
    )


def get_scenario_field_labels() -> dict[str, str]:
    """Return a field-name to label map derived from the shared schema."""

    return {
        field.field_name: field.label
        for field in list_scenario_field_definitions()
    }


def get_scenario_field_categories() -> dict[str, str]:
    """Return a field-name to category map derived from the shared schema."""

    return {
        field.field_name: field.category
        for field in list_scenario_field_definitions()
    }


def validate_scenario_field_schema() -> None:
    """Raise if the schema does not cover every Scenario dataclass field."""

    scenario_field_names = {field.name for field in fields(Scenario)}
    schema_field_names = {
        field.field_name for field in list_scenario_field_definitions()
    }
    if scenario_field_names != schema_field_names:
        missing_fields = sorted(scenario_field_names - schema_field_names)
        extra_fields = sorted(schema_field_names - scenario_field_names)
        raise ValueError(
            "Scenario field schema must match Scenario fields exactly. "
            f"Missing: {missing_fields!r}. Extra: {extra_fields!r}."
        )


validate_scenario_field_schema()


__all__ = [
    "ScenarioFieldDefinition",
    "ScenarioFieldOption",
    "ScenarioSummaryDefinition",
    "format_scenario_field_value",
    "format_scenario_summary_value",
    "get_scenario_field_categories",
    "get_scenario_field_definition",
    "get_scenario_field_labels",
    "get_scenario_summary_definition",
    "get_scenario_summary_label",
    "list_scenario_field_definitions",
    "list_scenario_summary_definitions",
    "validate_scenario_field_schema",
]
