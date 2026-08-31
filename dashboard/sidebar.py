from typing import Any

from dash import dcc, html

from scenarios import (
    ScenarioFieldDefinition,
    default_scenario,
    default_scenario_preset,
    format_scenario_field_value,
    list_scenario_field_definitions,
    list_scenario_presets,
    scenario_to_dict,
)

from .common import (
    BORDER_COLOR,
    SECTION_LEAD_TEXT_STYLE,
    SECTION_STYLE,
    SUBTLE_SURFACE_BACKGROUND_COLOR,
    TEXT_PRIMARY_COLOR,
    build_scenario_preset_overview,
)
from .scenario_comparison import (
    COMPARISON_CONFIGURATION_PANEL_STYLE,
    COMPARISON_SECONDARY_BUTTON_STYLE,
)


SCENARIO_SIDEBAR_CATEGORY_ORDER = (
    "Fleet & Demand",
    "Charging Infrastructure",
    "Grid & Capacity",
    "Operating Pattern",
    "Power Quality",
)
SCENARIO_SIDEBAR_FIELD_DEFINITIONS = tuple(list_scenario_field_definitions())
_SCENARIO_SIDEBAR_FIELD_DEFINITIONS_BY_NAME = {
    field.field_name: field for field in SCENARIO_SIDEBAR_FIELD_DEFINITIONS
}
_SCENARIO_SIDEBAR_PRIMARY_FIELDS_BY_CATEGORY = {
    "Fleet & Demand": (
        "vehicles",
        "daily_energy_per_vehicle",
    ),
    "Charging Infrastructure": (
        "charger_count",
        "charger_power",
    ),
    "Grid & Capacity": (
        "grid_capacity",
        "transformer_capacity_kw",
    ),
    "Operating Pattern": (
        "charging_window_start",
        "charging_window_end",
        "arrival_window_start",
        "arrival_window_end",
        "departure_mode",
        "charging_strategy",
    ),
    "Power Quality": (),
}
_SCENARIO_SIDEBAR_ADVANCED_FIELDS_BY_CATEGORY = {
    "Fleet & Demand": (
        "request_energy_variability_percent",
    ),
    "Charging Infrastructure": (
        "charger_service_max_waiting_time_minutes",
    ),
    "Grid & Capacity": (
        "transformer_other_load_kw",
        "feeder_count",
        "feeder_capacity_kw",
        "feeder_base_load_kw",
    ),
    "Operating Pattern": (
        "arrival_profile_shape",
        "session_dwell_minutes",
        "departure_time_spread_minutes",
    ),
    "Power Quality": (
        "single_phase_charger_share_percent",
    ),
}
_SCENARIO_SIDEBAR_HIDDEN_FIELDS_BY_CATEGORY = {
    "Fleet & Demand": (),
    "Charging Infrastructure": (),
    # These modeling controls stay internal to preserve existing scenario and
    # preset behavior without exposing implementation detail in the sidebar UI.
    "Grid & Capacity": (
        "feeder_ev_allocation_method",
        "feeder_allocation_shares",
        "planning_margin_percent",
    ),
    "Operating Pattern": (
        "arrival_mode",
    ),
    "Power Quality": (
        "charger_harmonic_factor",
        "power_quality_phase_allocation_method",
    ),
}
_TIME_OPTIONS = [
    {
        "label": f"{hour:02d}:{minute:02d}",
        "value": f"{hour:02d}:{minute:02d}",
    }
    for hour in range(24)
    for minute in range(0, 60, 15)
]
_SIDEBAR_LABEL_TOOLTIPS = {
    "charging_window_start": (
        "When the site begins allowing vehicles to charge."
    ),
    "charging_window_end": (
        "When the site stops allowing charging in this scenario."
    ),
    "arrival_window_start": (
        "When vehicles begin arriving and joining the charging queue."
    ),
    "arrival_window_end": (
        "When the modeled arrival period finishes."
    ),
    "request_energy_variability_percent": (
        "Spreads per-request energy across a deterministic low-to-high band "
        "while preserving the same total daily site energy."
    ),
    "charger_service_max_waiting_time_minutes": (
        "Maximum waiting time allowed by the charger-planning service rule. "
        "Higher tolerance allows more modeled queueing before extra chargers "
        "are indicated."
    ),
    "departure_time_spread_minutes": (
        "Deterministically spreads per-request deadlines. With window-end "
        "departures some requests leave earlier than the shared end time; "
        "with session dwell, dwell durations vary around the baseline."
    ),
    "single_phase_charger_share_percent": (
        "Share of chargers modeled as single-phase power-quality sources. "
        "Higher values increase modeled harmonic risk and can concentrate "
        "phase loading depending on phase allocation."
    ),
    "transformer_other_load_kw": (
        "Fixed non-EV load added to EV charging on the transformer at every "
        "timestep. Higher values increase total transformer loading and "
        "overload risk."
    ),
}
_SIDEBAR_SECTION_STYLE = {
    **SECTION_STYLE,
    "padding": "1.05rem 1.05rem 0.9rem",
    "marginBottom": "0.75rem",
}
_SIDEBAR_SECTION_TITLE_STYLE = {
    "marginTop": "0",
    "marginBottom": "0.85rem",
}
_SIDEBAR_PRESET_DETAILS_STYLE = {
    "marginTop": "0.75rem",
}
_SIDEBAR_FIELD_GROUP_STYLE = {
    **COMPARISON_CONFIGURATION_PANEL_STYLE,
    "padding": "0.9rem 1rem",
    "marginTop": "0.65rem",
}


def get_sidebar_field_input_id(field_name: str) -> str:
    """Return the stable input id for one sidebar field."""

    if field_name == "charging_strategy":
        return "charging-strategy-selector"

    return f"scenario-field-{field_name}-input"


def get_sidebar_field_container_id(field_name: str) -> str:
    """Return the stable wrapper id for one sidebar field."""

    if field_name == "charging_strategy":
        return "charging-strategy-selector-container"

    return f"scenario-field-{field_name}-container"


def _field_definitions_from_field_names(
    field_names: tuple[str, ...],
) -> tuple[ScenarioFieldDefinition, ...]:
    return tuple(
        _SCENARIO_SIDEBAR_FIELD_DEFINITIONS_BY_NAME[field_name]
        for field_name in field_names
    )


def _validate_sidebar_presentation_configuration() -> None:
    for category in SCENARIO_SIDEBAR_CATEGORY_ORDER:
        category_field_names = tuple(
            field.field_name
            for field in SCENARIO_SIDEBAR_FIELD_DEFINITIONS
            if field.category == category
        )
        primary_field_names = _SCENARIO_SIDEBAR_PRIMARY_FIELDS_BY_CATEGORY[category]
        advanced_field_names = _SCENARIO_SIDEBAR_ADVANCED_FIELDS_BY_CATEGORY[category]
        hidden_field_names = _SCENARIO_SIDEBAR_HIDDEN_FIELDS_BY_CATEGORY[category]

        if set(primary_field_names) & set(advanced_field_names):
            raise ValueError(
                f"Sidebar presentation config for {category!r} duplicates fields "
                "between primary and advanced sections."
            )

        if set(primary_field_names + advanced_field_names) & set(hidden_field_names):
            raise ValueError(
                f"Sidebar presentation config for {category!r} duplicates fields "
                "between visible and hidden sections."
            )

        classified_field_names = set(
            primary_field_names + advanced_field_names + hidden_field_names
        )
        if classified_field_names != set(category_field_names):
            raise ValueError(
                f"Sidebar presentation config for {category!r} must classify each "
                "category field exactly once across visible and hidden sections."
            )


_validate_sidebar_presentation_configuration()


def get_sidebar_primary_field_definitions(
    category: str,
) -> tuple[ScenarioFieldDefinition, ...]:
    """Return the primary fields for one sidebar group."""

    return _field_definitions_from_field_names(
        _SCENARIO_SIDEBAR_PRIMARY_FIELDS_BY_CATEGORY[category]
    )


def get_sidebar_advanced_field_definitions(
    category: str,
) -> tuple[ScenarioFieldDefinition, ...]:
    """Return the advanced fields for one sidebar group."""

    return _field_definitions_from_field_names(
        _SCENARIO_SIDEBAR_ADVANCED_FIELDS_BY_CATEGORY[category]
    )


def get_sidebar_visible_field_definitions(
    category: str,
) -> tuple[ScenarioFieldDefinition, ...]:
    """Return all visible fields for one sidebar group in schema order."""

    visible_field_names = set(
        _SCENARIO_SIDEBAR_PRIMARY_FIELDS_BY_CATEGORY[category]
        + _SCENARIO_SIDEBAR_ADVANCED_FIELDS_BY_CATEGORY[category]
    )
    return tuple(
        field
        for field in SCENARIO_SIDEBAR_FIELD_DEFINITIONS
        if field.category == category and field.field_name in visible_field_names
    )


def _sidebar_category_class_suffix(category: str) -> str:
    """Return a CSS-safe class suffix for one sidebar category."""

    return category.lower().replace("&", "and").replace("/", " ").replace(" ", "-")


SCENARIO_SIDEBAR_VISIBLE_FIELD_NAMES = tuple(
    field.field_name
    for category in SCENARIO_SIDEBAR_CATEGORY_ORDER
    for field in get_sidebar_visible_field_definitions(category)
)


def _format_sidebar_field_label(field_definition: ScenarioFieldDefinition) -> str:
    if field_definition.unit is None:
        return field_definition.label

    return f"{field_definition.label} ({field_definition.unit})"


def _build_field_label(field_definition, input_id: str) -> Any:
    tooltip_text = _SIDEBAR_LABEL_TOOLTIPS.get(field_definition.field_name)

    return html.Div(
        [
            html.Label(
                _format_sidebar_field_label(field_definition),
                htmlFor=input_id,
                style={
                    "display": "block",
                    "fontWeight": "600",
                    "marginBottom": "0",
                    "color": TEXT_PRIMARY_COLOR,
                },
            ),
            (
                html.Span(
                    "\u24d8",
                    className="scenario-sidebar-tooltip-trigger",
                    tabIndex=0,
                    **{
                        "aria-label": tooltip_text,
                        "data-tooltip": tooltip_text,
                        "role": "button",
                    },
                )
                if tooltip_text is not None
                else None
            ),
        ],
        className="scenario-sidebar-label-row",
    )


def _build_field_input(field_definition, value: Any) -> Any:
    input_id = get_sidebar_field_input_id(field_definition.field_name)

    if field_definition.input_kind == "select":
        options = [
            {
                "label": option.label,
                "value": option.value,
            }
            for option in field_definition.options
        ]
        if field_definition.field_name == "charging_strategy":
            options = [
                {
                    "label": "Uncontrolled Charging",
                    "value": "Uncontrolled",
                },
                {
                    "label": "Smart Charging",
                    "value": "Smart Charging",
                },
            ]
        return dcc.Dropdown(
            id=input_id,
            options=options,
            value=value,
            clearable=False,
        )

    if field_definition.input_kind == "time":
        return dcc.Dropdown(
            id=input_id,
            options=_TIME_OPTIONS,
            value=value,
            clearable=False,
        )

    if field_definition.input_kind == "sequence":
        return dcc.Input(
            id=input_id,
            type="text",
            value=value,
            debounce=True,
            placeholder="e.g. 0.4, 0.35, 0.25",
            style={
                "width": "100%",
                "boxSizing": "border-box",
            },
        )

    return dcc.Input(
        id=input_id,
        type="number",
        min=field_definition.min_value,
        step=field_definition.step,
        value=value,
        debounce=False,
        style={
            "width": "100%",
            "boxSizing": "border-box",
        },
    )


def _build_sidebar_field(field_definition, value: Any) -> Any:
    input_id = get_sidebar_field_input_id(field_definition.field_name)
    helper_children: list[Any] = []
    if field_definition.input_kind == "sequence":
        helper_children.append(
            html.P(
                "Comma-separated shares. The total must be greater than zero.",
                className="scenario-sidebar-field-helper",
            )
        )

    return html.Div(
        [
            _build_field_label(field_definition, input_id),
            _build_field_input(field_definition, value),
            *helper_children,
        ],
        id=get_sidebar_field_container_id(field_definition.field_name),
        className="scenario-sidebar-field",
    )


def _build_sidebar_field_grid(
    field_definitions: tuple[ScenarioFieldDefinition, ...],
    parameters: dict[str, Any],
    *,
    class_name: str,
) -> Any:
    if not field_definitions:
        return None

    return html.Div(
        [
            _build_sidebar_field(
                field_definition,
                parameters[field_definition.field_name],
            )
            for field_definition in field_definitions
        ],
        className=class_name,
    )


def _build_sidebar_advanced_disclosure(
    category: str,
    parameters: dict[str, Any],
) -> Any:
    advanced_field_definitions = get_sidebar_advanced_field_definitions(category)
    if not advanced_field_definitions:
        return None

    return html.Details(
        [
            html.Summary(
                "Advanced settings",
                className="scenario-sidebar-advanced-summary",
            ),
            _build_sidebar_field_grid(
                advanced_field_definitions,
                parameters,
                class_name=(
                    "scenario-sidebar-field-grid scenario-sidebar-advanced-grid"
                ),
            ),
        ],
        className="scenario-sidebar-advanced-disclosure",
    )


def _build_sidebar_field_group(
    category: str,
    parameters: dict[str, Any],
) -> Any:
    primary_field_definitions = get_sidebar_primary_field_definitions(category)
    category_class_suffix = _sidebar_category_class_suffix(category)
    return html.Div(
        [
            html.H4(category, className="scenario-sidebar-group-title"),
            _build_sidebar_field_grid(
                primary_field_definitions,
                parameters,
                class_name=(
                    "scenario-sidebar-field-grid "
                    "scenario-sidebar-primary-grid "
                    f"scenario-sidebar-primary-grid--{category_class_suffix}"
                ),
            ),
            _build_sidebar_advanced_disclosure(category, parameters),
        ],
        className=(
            "scenario-sidebar-group "
            f"scenario-sidebar-group--{category_class_suffix}"
        ),
        style=_SIDEBAR_FIELD_GROUP_STYLE,
    )


def _initial_sidebar_parameters() -> dict[str, Any]:
    initial_parameters = scenario_to_dict(default_scenario)
    for time_field_name in (
        "charging_window_start",
        "charging_window_end",
        "arrival_window_start",
        "arrival_window_end",
    ):
        initial_parameters[time_field_name] = format_scenario_field_value(
            time_field_name,
            initial_parameters[time_field_name],
        )

    return initial_parameters


def build_sidebar_field_groups(parameters: dict[str, Any]) -> list[Any]:
    """Return grouped editable scenario controls for the sidebar."""

    return [
        _build_sidebar_field_group(category, parameters)
        for category in SCENARIO_SIDEBAR_CATEGORY_ORDER
    ]


def _build_modified_indicator(*, is_modified: bool) -> Any:
    return html.Div(
        [
            html.Span(
                "Modified",
                id="scenario-preset-modified-indicator",
                className="scenario-sidebar-modified-chip",
                style={} if is_modified else {"display": "none"},
            ),
            html.Button(
                "Reset Defaults",
                id="reset-scenario-preset-button",
                n_clicks=0,
                type="button",
                style=(
                    COMPARISON_SECONDARY_BUTTON_STYLE
                    if is_modified
                    else {**COMPARISON_SECONDARY_BUTTON_STYLE, "display": "none"}
                ),
            ),
        ],
        className="scenario-sidebar-status-row",
    )


def build_sidebar() -> Any:
    """Return the persistent scenario-builder sidebar."""

    initial_parameters = _initial_sidebar_parameters()

    return html.Aside(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Section(
                                [
                                    html.H2(
                                        "Scenario Inputs",
                                        style=_SIDEBAR_SECTION_TITLE_STYLE,
                                    ),
                                    html.Div(
                                        [
                                            html.Label(
                                                "Scenario Type",
                                                htmlFor="scenario-preset-selector",
                                                style={
                                                    "display": "block",
                                                    "fontWeight": "bold",
                                                    "marginBottom": "0.25rem",
                                                },
                                            ),
                                            _build_modified_indicator(
                                                is_modified=False,
                                            ),
                                        ],
                                        className="scenario-sidebar-selector-row",
                                    ),
                                    dcc.Dropdown(
                                        id="scenario-preset-selector",
                                        options=[
                                            {
                                                "label": preset.label,
                                                "value": preset.preset_id,
                                            }
                                            for preset in list_scenario_presets()
                                        ],
                                        value=default_scenario_preset.preset_id,
                                        clearable=False,
                                    ),
                                    html.Div(
                                        [
                                            html.Div(
                                                build_scenario_preset_overview(
                                                    default_scenario_preset
                                                ),
                                                id="scenario-preset-details",
                                            ),
                                        ],
                                        style=_SIDEBAR_PRESET_DETAILS_STYLE,
                                    ),
                                    html.Div(
                                        [
                                            html.H3(
                                                "Editable Parameters",
                                                style={
                                                    "marginTop": "0.9rem",
                                                    "marginBottom": "0.45rem",
                                                },
                                            ),
                                            html.P(
                                                "",
                                                id="scenario-input-validation-message",
                                                className="scenario-sidebar-validation",
                                                style={"display": "none"},
                                            ),
                                            html.Div(
                                                build_sidebar_field_groups(
                                                    initial_parameters
                                                ),
                                                id="scenario-sidebar-field-groups",
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        [
                                            html.P(
                                                "Comparison Mode",
                                                style={
                                                    "fontWeight": "bold",
                                                    "marginTop": "1rem",
                                                    "marginBottom": "0.25rem",
                                                    "color": TEXT_PRIMARY_COLOR,
                                                },
                                            ),
                                            html.Div(
                                                "Uncontrolled Charging vs Smart Charging",
                                                id="smart-charging-comparison-mode-indicator",
                                                style={
                                                    "border": f"1px solid {BORDER_COLOR}",
                                                    "borderRadius": "8px",
                                                    "padding": "0.75rem 0.9rem",
                                                    "backgroundColor": SUBTLE_SURFACE_BACKGROUND_COLOR,
                                                    "fontWeight": "600",
                                                },
                                            ),
                                            html.P(
                                                (
                                                    "This tab always compares both strategies. "
                                                    "Your selected charging strategy remains "
                                                    "stored for the single-scenario tabs."
                                                ),
                                                id="smart-charging-comparison-mode-helper",
                                                style={
                                                    **SECTION_LEAD_TEXT_STYLE,
                                                    "marginTop": "0.5rem",
                                                    "marginBottom": "0",
                                                },
                                            ),
                                        ],
                                        id="smart-charging-comparison-mode-container",
                                        style={"display": "none"},
                                    ),
                                ],
                                style=_SIDEBAR_SECTION_STYLE,
                            ),
                        ],
                        className="scenario-sidebar-content",
                    ),
                    html.Section(
                        [
                            html.Button(
                                "Run Simulation",
                                id="run-simulation-button",
                                n_clicks=0,
                                type="button",
                                className="scenario-sidebar-primary-action",
                                style={
                                    "width": "100%",
                                },
                            ),
                            html.P(
                                "",
                                id="scenario-builder-status-message",
                                className="scenario-sidebar-status-message",
                                style={"display": "none"},
                            ),
                        ],
                        className="scenario-sidebar-action-area",
                    ),
                ],
                className="scenario-sidebar-frame",
            ),
        ],
        className="app-sidebar",
    )


__all__ = [
    "SCENARIO_SIDEBAR_CATEGORY_ORDER",
    "SCENARIO_SIDEBAR_FIELD_DEFINITIONS",
    "SCENARIO_SIDEBAR_VISIBLE_FIELD_NAMES",
    "build_sidebar",
    "build_sidebar_field_groups",
    "get_sidebar_advanced_field_definitions",
    "get_sidebar_field_container_id",
    "get_sidebar_field_input_id",
    "get_sidebar_primary_field_definitions",
    "get_sidebar_visible_field_definitions",
]
