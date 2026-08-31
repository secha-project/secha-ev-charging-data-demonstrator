"""Dashboard store serialization and state helper utilities."""

from .rendering._shared import *

def create_active_scenario(
    charging_strategy_value: str,
    *,
    preset_id: str = default_scenario_preset.preset_id,
) -> Scenario:
    """Return the selected preset scenario with run-specific overrides."""
    return create_preset_initialized_scenario(
        preset_id,
        charging_strategy_value=charging_strategy_value,
    )

def create_active_scenario_state(
    preset_id: str,
    charging_strategy_value: str,
) -> dict[str, Any]:
    """Create serializable single-source-of-truth active scenario state."""
    return apply_preset_defaults_to_active_scenario_state(
        preset_id,
        charging_strategy_value=charging_strategy_value,
    )

def active_scenario_from_state(active_scenario_state: dict[str, Any]) -> Scenario:
    """Rebuild the validated active scenario from stored dashboard state."""

    return scenario_from_active_state(active_scenario_state)

def _coerce_sidebar_field_value(field_name: str, value: Any) -> Any:
    return coerce_scenario_field_value(field_name, value)

def _sidebar_parameters_from_input_values(
    active_scenario_state: dict[str, Any],
    field_values: dict[str, Any],
) -> dict[str, Any]:
    return scenario_parameters_from_input_values(
        active_scenario_state,
        {
            field_name: field_values[field_name]
            for field_name in SCENARIO_SIDEBAR_FIELD_NAMES
        },
    )

def _sidebar_field_values_from_active_state(
    active_scenario_state: dict[str, Any],
) -> tuple[Any, ...]:
    return scenario_field_values_from_state(
        active_scenario_state,
        field_names=SCENARIO_SIDEBAR_FIELD_NAMES,
    )

def _sidebar_session_dwell_field_style(
    active_scenario_state: dict[str, Any],
) -> dict[str, Any]:
    parameters = get_active_scenario_parameters(active_scenario_state)
    if parameters["departure_mode"] == DepartureMode.SESSION_DWELL.value:
        return {}

    return {"display": "none"}

def _comparison_metrics_to_dict(
    comparison_metrics: ComparisonMetrics,
) -> dict[str, Any]:
    """Return a Dash-store-safe dictionary for strategy comparison metrics."""

    return asdict(comparison_metrics)

def _comparison_metrics_from_dict(data: dict[str, Any]) -> ComparisonMetrics:
    """Rebuild strategy comparison metrics from stored dashboard state."""

    return ComparisonMetrics(**data)

def _single_scenario_simulation_result_to_dict(
    result: SimulationResult,
) -> dict[str, Any]:
    """Return the compact single-scenario store payload for one result."""

    return {
        "daily_energy_demand": result.daily_energy_demand,
        "configured_connection_capacity_kw": (
            result.configured_connection_capacity_kw
        ),
        "installed_charger_capacity_kw": result.installed_charger_capacity_kw,
        "available_site_charging_capacity_kw": (
            result.available_site_charging_capacity_kw
        ),
        "requested_load_profile_kw": list(result.requested_load_profile_kw),
        "delivered_load_profile_kw": list(result.delivered_load_profile_kw),
        "delivered_energy": result.delivered_energy,
        "unmet_energy": result.unmet_energy,
    }

def _single_scenario_active_metrics_to_dict(metrics: Metrics) -> dict[str, Any]:
    """Return the active-strategy metrics store payload for one run."""

    data = metrics_to_dict(metrics)
    data.pop("capacity_sufficiency", None)
    return data

def _single_scenario_comparison_metrics_to_dict(
    metrics: Metrics,
) -> dict[str, Any]:
    """Return the compact comparison-strategy metrics payload for one run."""

    data = metrics_to_dict(metrics)
    data.pop("capacity_sufficiency", None)
    return {
        key: value
        for key, value in data.items()
        if not isinstance(value, list)
    }

def create_single_scenario_run_state(
    active_scenario_state: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Create serializable raw results and metrics for one active scenario."""

    callbacks_module = _callbacks_module()
    active_scenario = active_scenario_from_state(active_scenario_state)
    uncontrolled_result, smart_result = callbacks_module.simulate_strategy_comparison(
        active_scenario
    )
    uncontrolled_metrics = callbacks_module.calculate_metrics(
        uncontrolled_result,
        active_scenario,
    )
    smart_metrics = callbacks_module.calculate_metrics(
        smart_result,
        active_scenario,
    )
    if active_scenario.charging_strategy == ChargingStrategy.UNCONTROLLED:
        simulation_result = uncontrolled_result
        metrics = uncontrolled_metrics
    else:
        simulation_result = smart_result
        metrics = smart_metrics
    comparison_metrics = callbacks_module.calculate_comparison_metrics(
        uncontrolled_metrics,
        smart_metrics,
    )
    insights = callbacks_module.generate_insights(
        metrics,
        active_scenario.charging_strategy,
        comparison_metrics,
    )

    return (
        {
            "active": callbacks_module._single_scenario_simulation_result_to_dict(
                simulation_result
            ),
            "uncontrolled": callbacks_module._single_scenario_simulation_result_to_dict(
                uncontrolled_result
            ),
            "smart": callbacks_module._single_scenario_simulation_result_to_dict(
                smart_result
            ),
        },
        {
            "active": callbacks_module._single_scenario_active_metrics_to_dict(metrics),
            "uncontrolled": callbacks_module._single_scenario_comparison_metrics_to_dict(
                uncontrolled_metrics
            ),
            "smart": callbacks_module._single_scenario_comparison_metrics_to_dict(
                smart_metrics
            ),
            "comparison": callbacks_module._comparison_metrics_to_dict(
                comparison_metrics
            ),
            "insights": list(insights),
        },
    )

def create_connection_capacity_sensitivity_state(
    active_scenario_state: dict[str, Any],
    metrics_state: dict[str, Any],
) -> list[dict[str, Any]]:
    """Create serializable connection-capacity sensitivity rows."""

    callbacks_module = _callbacks_module()
    active_scenario = active_scenario_from_state(active_scenario_state)
    active_metrics = metrics_from_dict(metrics_state["active"])
    sensitivity_rows = callbacks_module.run_connection_capacity_sensitivity(
        active_scenario,
        base_metrics=active_metrics,
    )
    return [
        capacity_alternative_metrics_to_dict(row)
        for row in sensitivity_rows
    ]

def create_scenario_comparison_state(
    active_scenario_state: dict[str, Any],
    *,
    comparison_source: str = COMPARISON_SOURCE_MODIFIED_COPY,
    selected_template: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Create serializable Scenario A and Scenario B snapshot state."""
    return create_scenario_comparison_state_from_active_state(
        active_scenario_state,
        comparison_source=comparison_source,
        selected_template=selected_template,
    )

def update_scenario_comparison_state_for_b_edits(
    comparison_state: dict[str, dict[str, Any]],
    *,
    vehicles: int,
    charger_count: int,
    charger_power: float,
    grid_capacity: float,
) -> dict[str, dict[str, Any]]:
    """Return comparison state with edited Scenario B planning values."""
    return update_scenario_b_in_comparison_state(
        comparison_state,
        vehicles=vehicles,
        charger_count=charger_count,
        charger_power=charger_power,
        grid_capacity=grid_capacity,
    )

def create_scenario_ab_simulation_results_state(
    comparison_state: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Create serializable raw simulation results for Scenario A and B."""
    scenario_a, scenario_b = comparison_scenarios_from_state(comparison_state)
    result_a, result_b = simulate_scenario_comparison(scenario_a, scenario_b)
    return {
        "scenario_a": simulation_result_to_dict(result_a),
        "scenario_b": simulation_result_to_dict(result_b),
    }

def create_scenario_ab_comparison_run_state(
    comparison_state: dict[str, dict[str, Any]],
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, Any],
]:
    """Create serializable raw results, metrics, and differences for A/B."""
    scenario_a, scenario_b = comparison_scenarios_from_state(comparison_state)
    result_a, result_b = simulate_scenario_comparison(scenario_a, scenario_b)
    metrics_a, metrics_b = calculate_scenario_comparison_metrics(
        scenario_a,
        result_a,
        scenario_b,
        result_b,
    )
    difference_metrics = calculate_scenario_difference_metrics(metrics_a, metrics_b)
    return (
        {
            "scenario_a": simulation_result_to_dict(result_a),
            "scenario_b": simulation_result_to_dict(result_b),
        },
        {
            "scenario_a": metrics_to_dict(metrics_a),
            "scenario_b": metrics_to_dict(metrics_b),
        },
        scenario_comparison_metrics_to_dict(difference_metrics),
    )

def _scenario_b_editor_values(
    comparison_state: dict[str, dict[str, Any]],
) -> tuple[Any, Any, Any, Any]:
    """Return Scenario B values for the editable dashboard controls."""
    return scenario_b_editable_values_from_state(comparison_state)

def _resolved_template_id(template_id: str | None) -> str:
    """Return a valid Scenario B template identifier."""
    if template_id is not None:
        return template_id

    return DEFAULT_SCENARIO_B_TEMPLATE_ID

def _scenario_label_from_preset_id(preset_id: Any) -> str | None:
    """Return one human-friendly scenario label from a preset id when possible."""

    if not isinstance(preset_id, str):
        return None

    try:
        return get_scenario_preset(preset_id).label
    except KeyError:
        return None

def _scenario_label_with_modified_suffix(
    scenario_label: str,
    *,
    is_modified: bool,
) -> str:
    """Return one display label with a compact modified suffix when needed."""

    if not is_modified or scenario_label == "Current Scenario":
        return scenario_label

    if scenario_label.endswith(" (Modified)"):
        return scenario_label

    return f"{scenario_label} (Modified)"

def _resolve_scenario_ab_display_labels(
    active_scenario_state: dict[str, Any] | None,
    comparison_state: dict[str, dict[str, Any]] | None,
) -> tuple[str, str]:
    """Return display labels for Scenario A and Scenario B results."""

    active_scenario_metadata = (
        get_active_scenario_metadata(active_scenario_state or {})
        if active_scenario_state is not None
        else {}
    )
    scenario_a_label = (
        active_scenario_metadata.get("name")
        or _scenario_label_from_preset_id(
            get_active_scenario_preset_id(active_scenario_state or {})
        )
        or "Current Scenario"
    )
    scenario_a_is_modified = (
        get_active_scenario_is_modified(active_scenario_state or {})
        if active_scenario_state is not None
        else False
    )

    if comparison_state is None:
        return (
            _scenario_label_with_modified_suffix(
                scenario_a_label,
                is_modified=scenario_a_is_modified,
            ),
            "Comparison Scenario",
        )

    comparison_source = comparison_state.get(
        "comparison_source",
        COMPARISON_SOURCE_MODIFIED_COPY,
    )
    if comparison_source == COMPARISON_SOURCE_TEMPLATE:
        scenario_a_label = _scenario_label_with_modified_suffix(
            scenario_a_label,
            is_modified=scenario_a_is_modified,
        )
        scenario_b_label = _scenario_label_from_preset_id(
            comparison_state.get("selected_template")
        ) or "Template Scenario"
        return scenario_a_label, scenario_b_label

    if scenario_a_label == "Current Scenario":
        return scenario_a_label, "Comparison Scenario"

    return scenario_a_label, f"{scenario_a_label} (Modified)"

def _template_comparison_status(template_id: str) -> str:
    """Return a user-facing status line for template-backed Scenario B."""
    del template_id
    return DEFAULT_SCENARIO_COMPARISON_STATUS

def _stale_comparison_status(comparison_source: str) -> str:
    """Return a stale-state builder message after Scenario A changes."""
    if comparison_source == COMPARISON_SOURCE_TEMPLATE:
        return (
            "Scenario A changed. Scenario B was refreshed from the selected "
            "template."
        )

    return (
        "Scenario A changed. Scenario B kept its own edits."
    )

def _comparison_builder_styles(
    comparison_source: str,
    *,
    show_editor: bool,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Return styles for the comparison-builder subsections."""
    duplicate_action_style = (
        COMPARISON_BUILDER_ACTION_VISIBLE_STYLE
        if comparison_source == COMPARISON_SOURCE_MODIFIED_COPY
        else COMPARISON_BUILDER_ACTION_HIDDEN_STYLE
    )
    template_section_style = (
        SCENARIO_B_TEMPLATE_VISIBLE_STYLE
        if comparison_source == COMPARISON_SOURCE_TEMPLATE
        else SCENARIO_B_TEMPLATE_HIDDEN_STYLE
    )
    editor_section_style = (
        SCENARIO_B_EDITOR_VISIBLE_STYLE
        if comparison_source == COMPARISON_SOURCE_MODIFIED_COPY and show_editor
        else SCENARIO_B_EDITOR_HIDDEN_STYLE
    )
    return (
        duplicate_action_style,
        template_section_style,
        editor_section_style,
    )

def _normalize_scenario_comparison_builder_ui_state(
    builder_ui_state: dict[str, Any] | None,
) -> dict[str, bool]:
    """Return stable builder compaction state for Scenario Comparison."""

    if not isinstance(builder_ui_state, dict):
        return {"collapsed": False, "has_run": False}

    return {
        "collapsed": bool(builder_ui_state.get("collapsed", False)),
        "has_run": bool(builder_ui_state.get("has_run", False)),
    }

def _normalize_scenario_comparison_run_status_state(
    run_status_state: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return the normalized Scenario Comparison run lifecycle state."""

    if isinstance(run_status_state, dict):
        status = run_status_state.get("status")
        if status in {"not_run", "stale", "up_to_date", "error"}:
            stale_reason = run_status_state.get("stale_reason")
            if stale_reason not in {"scenario_a_changed", "scenario_b_changed"}:
                stale_reason = None
            baseline_active_scenario_state = run_status_state.get(
                "baseline_active_scenario_state"
            )
            return {
                "status": status,
                "stale_reason": stale_reason,
                "baseline_active_scenario_state": (
                    baseline_active_scenario_state
                    if isinstance(baseline_active_scenario_state, dict)
                    else None
                ),
            }

    return {
        "status": "not_run",
        "stale_reason": None,
        "baseline_active_scenario_state": None,
    }

def _scenario_comparison_builder_is_collapsed(
    builder_ui_state: dict[str, Any] | None,
) -> bool:
    """Return whether the compact post-run builder bar should be visible."""

    normalized_state = _normalize_scenario_comparison_builder_ui_state(builder_ui_state)
    return normalized_state["has_run"] and normalized_state["collapsed"]

def _scenario_comparison_collapsed_status_summary(
    run_status_state: dict[str, Any] | None,
    builder_ui_state: dict[str, Any] | None,
) -> tuple[str, dict[str, str]]:
    """Return collapsed-bar status wording and badge styling."""

    normalized_state = _normalize_scenario_comparison_builder_ui_state(builder_ui_state)
    normalized_run_status = _normalize_scenario_comparison_run_status_state(
        run_status_state
    )

    if normalized_run_status["status"] == "up_to_date":
        return (
            "Up to date",
            {
                "backgroundColor": STATUS_GREEN_BACKGROUND,
                "border": f"1px solid {STATUS_GREEN}",
                "color": STATUS_GREEN,
            },
        )

    if normalized_run_status["status"] == "error":
        return (
            "Update failed",
            {
                "backgroundColor": STATUS_RED_BACKGROUND,
                "border": f"1px solid {STATUS_RED}",
                "color": STATUS_RED,
            },
        )

    if normalized_run_status["status"] == "stale" or normalized_state["has_run"]:
        return (
            "Out of date",
            {
                "backgroundColor": STATUS_AMBER_BACKGROUND,
                "border": f"1px solid {STATUS_AMBER}",
                "color": STATUS_AMBER,
            },
        )

    return (
        "Not run yet",
        {
            "backgroundColor": SUBTLE_SURFACE_BACKGROUND_COLOR,
            "border": f"1px solid {BORDER_COLOR}",
            "color": TEXT_SECONDARY_COLOR,
        },
    )

def _create_scenario_builder_feedback_state(
    *,
    action: str = "idle",
    overwrote_modified_values: bool = False,
    validation_message: str = "",
) -> dict[str, Any]:
    """Return the normalized sidebar builder feedback payload."""

    return {
        "action": action,
        "overwrote_modified_values": overwrote_modified_values,
        "validation_message": validation_message,
    }

def _normalize_scenario_builder_feedback_state(
    feedback_state: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return a safe builder feedback state for sidebar status rendering."""

    if not isinstance(feedback_state, dict):
        return _create_scenario_builder_feedback_state()

    validation_message = feedback_state.get("validation_message", "")
    action = feedback_state.get("action", "idle")
    overwrote_modified_values = feedback_state.get(
        "overwrote_modified_values",
        False,
    )
    return _create_scenario_builder_feedback_state(
        action=action if isinstance(action, str) else "idle",
        overwrote_modified_values=bool(overwrote_modified_values),
        validation_message=(
            validation_message if isinstance(validation_message, str) else ""
        ),
    )

def _normalize_single_scenario_run_status_state(
    run_status_state: dict[str, Any] | None,
) -> dict[str, str]:
    """Return the normalized single-scenario run lifecycle state."""

    if isinstance(run_status_state, dict):
        status = run_status_state.get("status")
        if status in {"not_run", "stale", "up_to_date"}:
            return {"status": status}

    return {"status": "not_run"}

def _scenario_builder_status_message_state(
    feedback_state: dict[str, Any] | None,
    run_status_state: dict[str, Any] | None,
) -> tuple[str, dict[str, str]]:
    """Return the planner-facing sidebar status copy for the run button area."""

    feedback = _normalize_scenario_builder_feedback_state(feedback_state)
    if feedback["validation_message"]:
        return "", {"display": "none"}

    run_status = _normalize_single_scenario_run_status_state(run_status_state)
    if run_status["status"] == "stale":
        return "Inputs changed — rerun simulation.", {"display": "block"}

    if run_status["status"] == "up_to_date":
        return "Simulation results are up to date.", {"display": "block"}

    return "", {"display": "none"}

@dataclass(frozen=True)
class _SingleScenarioRenderContext:
    """Prepared dashboard render context rebuilt from one completed run."""

    active_scenario: Scenario
    simulation_result: SimulationResult
    uncontrolled_result: SimulationResult
    smart_result: SimulationResult
    metrics: Metrics
    uncontrolled_metrics: Metrics
    smart_metrics: Metrics
    comparison_metrics: ComparisonMetrics
    insights: tuple[str, ...]

def _single_scenario_render_context_from_states(
    simulation_results_state: dict[str, dict[str, Any]] | None,
    metrics_state: dict[str, Any] | None,
    active_scenario_state: dict[str, Any] | None,
) -> _SingleScenarioRenderContext | None:
    """Return the prepared render context for one completed single run."""

    if (
        simulation_results_state is None
        or metrics_state is None
        or active_scenario_state is None
    ):
        return None

    return _SingleScenarioRenderContext(
        active_scenario=active_scenario_from_state(active_scenario_state),
        simulation_result=simulation_result_from_dict(
            simulation_results_state["active"]
        ),
        uncontrolled_result=simulation_result_from_dict(
            simulation_results_state["uncontrolled"]
        ),
        smart_result=simulation_result_from_dict(
            simulation_results_state["smart"]
        ),
        metrics=metrics_from_dict(metrics_state["active"]),
        uncontrolled_metrics=metrics_from_dict(metrics_state["uncontrolled"]),
        smart_metrics=metrics_from_dict(metrics_state["smart"]),
        comparison_metrics=_comparison_metrics_from_dict(
            metrics_state["comparison"]
        ),
        insights=tuple(metrics_state["insights"]),
    )

__all__ = [

    'create_active_scenario',

    'create_active_scenario_state',

    'active_scenario_from_state',

    '_coerce_sidebar_field_value',

    '_sidebar_parameters_from_input_values',

    '_sidebar_field_values_from_active_state',

    '_sidebar_session_dwell_field_style',

    '_comparison_metrics_to_dict',

    '_comparison_metrics_from_dict',

    '_single_scenario_simulation_result_to_dict',

    '_single_scenario_active_metrics_to_dict',

    '_single_scenario_comparison_metrics_to_dict',

    'create_single_scenario_run_state',

    'create_connection_capacity_sensitivity_state',

    'create_scenario_comparison_state',

    'update_scenario_comparison_state_for_b_edits',

    'create_scenario_ab_simulation_results_state',

    'create_scenario_ab_comparison_run_state',

    '_scenario_b_editor_values',

    '_resolved_template_id',

    '_scenario_label_from_preset_id',

    '_scenario_label_with_modified_suffix',

    '_resolve_scenario_ab_display_labels',

    '_template_comparison_status',

    '_stale_comparison_status',

    '_comparison_builder_styles',

    '_normalize_scenario_comparison_builder_ui_state',

    '_normalize_scenario_comparison_run_status_state',

    '_scenario_comparison_builder_is_collapsed',

    '_scenario_comparison_collapsed_status_summary',

    '_create_scenario_builder_feedback_state',

    '_normalize_scenario_builder_feedback_state',

    '_normalize_single_scenario_run_status_state',

    '_scenario_builder_status_message_state',

    '_SingleScenarioRenderContext',

    '_single_scenario_render_context_from_states',

]

