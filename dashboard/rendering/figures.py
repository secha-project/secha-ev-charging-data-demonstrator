"""Dashboard Plotly figure builders and chart helpers."""

from ._shared import *
from .formatters import *

def _standard_legend_layout() -> dict[str, Any]:
    """Return the shared legend configuration for dashboard charts."""

    return {
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "left",
        "x": 0,
        "font": {
            "size": CHART_LEGEND_FONT_SIZE_PX,
            "color": TEXT_SECONDARY_COLOR,
        },
    }

def _apply_standard_figure_layout(
    figure: go.Figure,
    *,
    title: str | None,
    yaxis_title: str,
    xaxis_title: str = "Hour",
    height: int = GRAPH_HEIGHT_PX,
    margin: dict[str, int] | None = None,
    show_legend: bool = True,
    autosize: bool = False,
    extra_layout: dict[str, Any] | None = None,
    title_pad_bottom: int = 0,
    **layout_overrides: Any,
) -> go.Figure:
    """Apply one restrained, shared dashboard chart layout."""

    figure.update_layout(
        title=(
            {
                "text": title,
                "x": 0,
                "xanchor": "left",
                "font": {
                    "size": CHART_TITLE_FONT_SIZE_PX,
                    "color": TEXT_PRIMARY_COLOR,
                },
                "pad": {"b": title_pad_bottom},
            }
            if title
            else None
        ),
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        margin=margin or (CHART_MARGIN_DEFAULT if title else CHART_MARGIN_TITLELESS),
        legend=_standard_legend_layout(),
        hovermode="x unified",
        height=height,
        autosize=autosize,
        paper_bgcolor=SURFACE_BACKGROUND_COLOR,
        plot_bgcolor=SURFACE_BACKGROUND_COLOR,
        font={"family": "Segoe UI, Arial, sans-serif", "color": TEXT_PRIMARY_COLOR},
        showlegend=show_legend,
    )
    figure.update_xaxes(
        showgrid=False,
        zeroline=False,
        color=TEXT_SECONDARY_COLOR,
        tickfont={"size": CHART_AXIS_FONT_SIZE_PX},
        title_font={
            "size": CHART_AXIS_FONT_SIZE_PX,
            "color": TEXT_SECONDARY_COLOR,
        },
    )
    figure.update_yaxes(
        showgrid=True,
        gridcolor=CHART_GRID_COLOR,
        zeroline=False,
        color=TEXT_SECONDARY_COLOR,
        tickfont={"size": CHART_AXIS_FONT_SIZE_PX},
        title_font={
            "size": CHART_AXIS_FONT_SIZE_PX,
            "color": TEXT_SECONDARY_COLOR,
        },
    )
    if extra_layout is not None:
        figure.update_layout(**extra_layout)
    if layout_overrides:
        figure.update_layout(**layout_overrides)

    return figure

def _apply_sparse_time_ticks(
    figure: go.Figure,
    time_labels: list[str],
    *,
    tick_step: int | None,
) -> go.Figure:
    """Reduce displayed categorical time ticks while preserving trace points."""

    resolved_tick_step = tick_step
    if resolved_tick_step is None:
        resolved_tick_step = _standard_time_tick_step(time_labels)

    if resolved_tick_step is None or resolved_tick_step <= 1:
        return figure

    tick_values = time_labels[::resolved_tick_step]
    figure.update_xaxes(
        tickmode="array",
        tickvals=tick_values,
        ticktext=tick_values,
    )
    return figure

def _standard_time_tick_step(time_labels: list[str]) -> int | None:
    """Return the shared tick-label step for supported time-of-day labels."""

    full_day_labels = get_time_labels()
    if time_labels == full_day_labels:
        return 8

    if time_labels == full_day_labels[::4]:
        return 2

    return None

def _hover_value_format_parts(yaxis_title: str) -> tuple[str, str]:
    """Return the shared numeric format and suffix for one chart axis."""

    normalized_title = yaxis_title.strip().lower()

    if "(kw)" in normalized_title:
        return ",.1f", " kW"
    if "(kwh)" in normalized_title:
        return ",.1f", " kWh"
    if "(%)" in normalized_title:
        return ",.1f", " %"
    if normalized_title == "chargers":
        return ",.0f", " chargers"
    if normalized_title == "vehicles":
        return ",.0f", " vehicles"
    if "risk score (0-100)" in normalized_title:
        return ",.1f", " / 100"

    return ",.1f", ""

def _standard_hovertemplate(
    yaxis_title: str,
    *,
    trace_name_placeholder: str = "%{fullData.name}",
    axis_token: str = "y",
) -> str:
    """Return the shared hover template for one numeric chart trace."""

    value_format, value_suffix = _hover_value_format_parts(yaxis_title)
    return (
        f"%{{{axis_token}:{value_format}}}{value_suffix}"
        f"<extra>{trace_name_placeholder}</extra>"
    )

def _trace_line_style(trace_name: str, dash: str | None = None) -> dict[str, Any]:
    """Return one restrained line style for a named chart trace."""

    style: dict[str, Any] = {"width": 2.5}
    color = CHART_LINE_COLORS.get(trace_name)
    if color is not None:
        style["color"] = color
    if dash is not None:
        style["dash"] = dash

    return style

def create_load_profile_figure(load_profile: list[float]) -> go.Figure:
    """Create a Plotly figure for one timestep-based charging load profile."""
    return _create_load_profile_figure(
        [("Charging power", load_profile)],
        "Charging Load Profile",
    )

def create_capacity_vs_load_figure(
    simulation_result: SimulationResult,
    metrics: Metrics,
) -> go.Figure:
    """Create a single-scenario chart comparing requested and delivered load."""
    time_labels = get_time_labels()
    configured_capacity = simulation_result.configured_connection_capacity_kw
    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=time_labels,
            y=simulation_result.delivered_load_profile_kw,
            mode="lines",
            name="Delivered Charging Load",
            line=_trace_line_style("Delivered Charging Load"),
            hovertemplate=_standard_hovertemplate("Charging Power (kW)"),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=time_labels,
            y=simulation_result.requested_load_profile_kw,
            mode="lines",
            name="Requested Charging Demand",
            line=_trace_line_style("Requested Charging Demand", "dash"),
            hovertemplate=_standard_hovertemplate("Charging Power (kW)"),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=time_labels,
            y=[configured_capacity] * len(time_labels),
            mode="lines",
            name="Configured Connection Capacity",
            line=_trace_line_style("Configured Connection Capacity", "dot"),
            hovertemplate=_standard_hovertemplate("Charging Power (kW)"),
        )
    )

    _apply_standard_figure_layout(
        figure,
        title=None,
        yaxis_title="Charging Power (kW)",
        height=OVERVIEW_CAPACITY_SUMMARY_HEIGHT_PX,
        margin=CHART_MARGIN_COMPACT,
    )
    _apply_sparse_time_ticks(figure, time_labels, tick_step=None)

    return figure

def create_charger_occupancy_figure(
    metrics: Metrics,
    scenario: Scenario,
) -> go.Figure:
    """Create a chart of occupied chargers against configured charger count."""
    return _create_count_vs_reference_figure(
        title="Charger Occupancy Over Time",
        yaxis_title="Chargers",
        series_name="Occupied Chargers",
        series=metrics.occupied_charger_count_by_timestep,
        reference_name="Available Chargers",
        reference_value=scenario.charger_count,
        unavailable_message=(
            "Charger occupancy series unavailable for this result."
        ),
    )

def create_service_pressure_figure(
    metrics: Metrics,
    scenario: Scenario,
) -> go.Figure:
    """Create one Infrastructure chart combining occupancy and queue pressure."""
    occupied_series = metrics.occupied_charger_count_by_timestep
    time_labels = get_time_labels()
    if len(occupied_series) != len(time_labels):
        return _create_unavailable_time_series_figure(
            title="Charger Pressure During Charging Window",
            yaxis_title="Chargers",
            message="Service-pressure series unavailable for this result.",
            show_figure_title=False,
            autosize=True,
        )

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=time_labels,
            y=occupied_series,
            mode="lines",
            name="Occupied Chargers",
            line=_trace_line_style("Occupied Chargers"),
            hovertemplate=_standard_hovertemplate("Chargers"),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=time_labels,
            y=[scenario.charger_count] * len(time_labels),
            mode="lines",
            name="Charger Capacity",
            line=_trace_line_style("Charger Capacity", "dash"),
            hovertemplate=_standard_hovertemplate("Chargers"),
        )
    )

    queue_series = metrics.waiting_vehicle_count_by_timestep
    queue_trace_present = (
        len(queue_series) == len(time_labels)
        and any(queue_count > 0 for queue_count in queue_series)
    )
    if queue_trace_present:
        figure.add_trace(
            go.Scatter(
                x=time_labels,
                y=queue_series,
                mode="lines",
                name="Waiting Vehicles",
                yaxis="y2",
                line=_trace_line_style("Waiting Vehicles"),
                hovertemplate=_standard_hovertemplate("Vehicles"),
            )
        )

    layout: dict[str, Any] = {
        "legend": {
            **_standard_legend_layout(),
            "y": 1.08,
        },
        "margin": {"l": 54, "r": 60 if queue_trace_present else 24, "t": 38, "b": 58},
        "xaxis": {"ticklabelstandoff": 6},
        "yaxis": {"rangemode": "tozero"},
    }
    if queue_trace_present:
        layout["yaxis2"] = {
            "title": "Waiting Vehicles",
            "overlaying": "y",
            "side": "right",
            "rangemode": "tozero",
            "showgrid": False,
            "zeroline": False,
            "color": TEXT_SECONDARY_COLOR,
            "tickfont": {"size": CHART_AXIS_FONT_SIZE_PX},
            "title_font": {
                "size": CHART_AXIS_FONT_SIZE_PX,
                "color": TEXT_SECONDARY_COLOR,
            },
        }

    _apply_standard_figure_layout(
        figure,
        title=None,
        yaxis_title="Chargers",
        height=360,
        autosize=True,
        extra_layout=layout,
    )
    _apply_sparse_time_ticks(figure, time_labels, tick_step=None)
    return figure

def create_queue_length_figure(metrics: Metrics) -> go.Figure:
    """Create a chart of waiting vehicles over time."""
    return _create_count_series_figure(
        title="Queue Length Over Time",
        yaxis_title="Vehicles",
        series_name="Waiting Vehicles",
        series=metrics.waiting_vehicle_count_by_timestep,
        unavailable_message="Queue-length series unavailable for this result.",
    )

def create_power_capacity_over_time_figure(
    simulation_result: SimulationResult,
) -> go.Figure:
    """Create a chart of delivered load against installed and grid capacity."""
    delivered_series = simulation_result.delivered_load_profile_kw
    time_labels = get_time_labels()
    if len(delivered_series) != len(time_labels):
        return _create_unavailable_time_series_figure(
            title="Charging Power and Capacity Over Time",
            yaxis_title="Charging Power (kW)",
            message="Charging power series unavailable for this result.",
            show_figure_title=False,
            autosize=True,
        )

    figure = _create_time_series_figure(
        traces=[
            ("Delivered Charging Power", delivered_series, None),
            (
                "Installed Charger Capacity",
                [simulation_result.installed_charger_capacity_kw]
                * len(time_labels),
                "dash",
            ),
            (
                "Grid Connection Capacity",
                [simulation_result.configured_connection_capacity_kw]
                * len(time_labels),
                "dot",
            ),
        ],
        title="Charging Power and Capacity Over Time",
        yaxis_title="Charging Power (kW)",
        show_figure_title=False,
        autosize=True,
    )
    figure.update_layout(
        legend={
            **_standard_legend_layout(),
            "y": 1.08,
        }
    )
    return figure

def create_comparison_load_profile_figure(
    uncontrolled_result: SimulationResult,
    smart_result: SimulationResult,
) -> go.Figure:
    """Create a Plotly figure comparing charging strategy load profiles."""
    return _create_load_profile_figure(
        [
            (
                "Uncontrolled Charging",
                uncontrolled_result.delivered_load_profile_kw,
            ),
            ("Smart Charging", smart_result.delivered_load_profile_kw),
        ],
        "Before / After Load Profile",
        show_figure_title=False,
        autosize=True,
    )

def create_comparison_occupancy_figure(
    comparison_metrics: ComparisonMetrics,
) -> go.Figure:
    """Create a chart comparing occupied chargers across strategies."""
    return _create_strategy_comparison_series_figure(
        title="Occupied Chargers Over Time",
        yaxis_title="Chargers",
        uncontrolled_series=(
            comparison_metrics.uncontrolled_occupied_charger_count_by_timestep
        ),
        smart_series=comparison_metrics.smart_occupied_charger_count_by_timestep,
        unavailable_message=(
            "Occupied-charger comparison series unavailable for this result."
        ),
        show_figure_title=False,
        autosize=True,
    )

def create_comparison_queue_figure(
    comparison_metrics: ComparisonMetrics,
) -> go.Figure:
    """Create a chart comparing queue length across strategies."""
    return _create_strategy_comparison_series_figure(
        title="Queue Length Over Time",
        yaxis_title="Vehicles",
        uncontrolled_series=(
            comparison_metrics.uncontrolled_waiting_vehicle_count_by_timestep
        ),
        smart_series=comparison_metrics.smart_waiting_vehicle_count_by_timestep,
        unavailable_message=(
            "Queue-length comparison series unavailable for this result."
        ),
        show_figure_title=False,
        autosize=True,
    )

def create_comparison_power_quality_figure(
    comparison_metrics: ComparisonMetrics,
) -> go.Figure:
    """Create a chart comparing overall PQ risk across strategies."""
    return _create_strategy_comparison_float_series_figure(
        title="Overall PQ Risk Over Time",
        yaxis_title="Overall PQ Risk Score (0-100)",
        uncontrolled_series=(
            comparison_metrics.uncontrolled_overall_pq_risk_score_by_timestep
        ),
        smart_series=comparison_metrics.smart_overall_pq_risk_score_by_timestep,
        unavailable_message=(
            "Overall PQ risk comparison series unavailable for this result."
        ),
        show_figure_title=False,
        autosize=True,
    )

def create_transformer_loading_figure(metrics: Metrics) -> go.Figure:
    """Create a chart of transformer loading percent against the rating line."""
    loading_series = metrics.transformer_loading_percent_by_timestep
    time_labels = get_time_labels()
    if len(loading_series) != len(time_labels):
        return _create_unavailable_time_series_figure(
            title="Transformer Loading Over Time",
            yaxis_title="Transformer Loading (%)",
            message="Transformer loading series unavailable for this result.",
            show_figure_title=False,
            autosize=True,
        )

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=time_labels,
            y=loading_series,
            mode="lines",
            name="Transformer Loading",
            line=_trace_line_style("Transformer Loading"),
            hovertemplate=_standard_hovertemplate("Transformer Loading (%)"),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=time_labels,
            y=[100.0] * len(time_labels),
            mode="lines",
            name="Transformer Rating",
            line=_trace_line_style("Transformer Rating", "dot"),
            hovertemplate=_standard_hovertemplate("Transformer Loading (%)"),
        )
    )

    if any(loading_percent > 100.0 for loading_percent in loading_series):
        figure.add_trace(
            go.Scatter(
                x=time_labels,
                y=[
                    loading_percent if loading_percent > 100.0 else None
                    for loading_percent in loading_series
                ],
                mode="lines",
                name="Overload Range",
                line={**_trace_line_style("Overload Range"), "width": 3.25},
                hovertemplate=_standard_hovertemplate("Transformer Loading (%)"),
            )
        )

    _apply_standard_figure_layout(
        figure,
        title=None,
        yaxis_title="Transformer Loading (%)",
        autosize=True,
    )
    _apply_sparse_time_ticks(figure, time_labels, tick_step=None)

    return figure

def create_harmonic_risk_figure(metrics: Metrics) -> go.Figure:
    """Create a chart of the modeled harmonic-risk score over time."""
    return _create_float_series_figure(
        title="Harmonic Risk Over Time",
        yaxis_title="Harmonic Risk Score (0-100)",
        series_name="Harmonic Risk",
        series=metrics.harmonic_risk_score_by_timestep,
        unavailable_message="Harmonic-risk series unavailable for this result.",
        show_figure_title=False,
        autosize=True,
    )

def create_current_imbalance_figure(metrics: Metrics) -> go.Figure:
    """Create a chart of the modeled current-imbalance percent over time."""
    return _create_float_series_figure(
        title="Current Imbalance Over Time",
        yaxis_title="Current Imbalance (%)",
        series_name="Current Imbalance",
        series=metrics.current_imbalance_percent_by_timestep,
        unavailable_message=(
            "Current-imbalance series unavailable for this result."
        ),
        show_figure_title=False,
        autosize=True,
    )

def create_phase_load_figure(metrics: Metrics) -> go.Figure:
    """Create a chart of modeled phase A/B/C load over time."""
    phase_a_series = metrics.phase_a_load_kw_by_timestep
    phase_b_series = metrics.phase_b_load_kw_by_timestep
    phase_c_series = metrics.phase_c_load_kw_by_timestep
    time_labels = get_time_labels()

    if any(
        len(series) != len(time_labels)
        for series in (phase_a_series, phase_b_series, phase_c_series)
    ):
        return _create_unavailable_time_series_figure(
            title="Phase Load Over Time",
            yaxis_title="Phase Load (kW)",
            message="Phase-load series unavailable for this result.",
            show_figure_title=False,
            autosize=True,
        )

    return _create_time_series_figure(
        traces=[
            ("Phase A", phase_a_series, None),
            ("Phase B", phase_b_series, "dash"),
            ("Phase C", phase_c_series, "dot"),
        ],
        title="Phase Load Over Time",
        yaxis_title="Phase Load (kW)",
        show_figure_title=False,
        autosize=True,
    )

def _create_load_profile_figure(
    traces: list[tuple[str, list[float]]],
    title: str,
    *,
    show_figure_title: bool = True,
    autosize: bool = False,
    x_tick_step: int | None = None,
) -> go.Figure:
    """Create a Plotly figure from one or more charging load profiles."""
    if not traces:
        return _create_unavailable_time_series_figure(
            title=title,
            yaxis_title="Charging Power (kW)",
            message="Charging power series unavailable for this result.",
            show_figure_title=show_figure_title,
            autosize=autosize,
        )

    time_labels = _get_time_labels_for_series_length(
        len(traces[0][1]),
        allow_hourly_legacy=True,
    )
    if time_labels is None or any(
        len(load_profile) != len(time_labels)
        for _trace_name, load_profile in traces
    ):
        return _create_unavailable_time_series_figure(
            title=title,
            yaxis_title="Charging Power (kW)",
            message="Charging power series unavailable for this result.",
            show_figure_title=show_figure_title,
            autosize=autosize,
        )

    figure = go.Figure()
    for trace_name, load_profile in traces:
        figure.add_trace(
            go.Scatter(
                x=time_labels,
                y=load_profile,
                mode="lines",
                name=trace_name,
                line=_trace_line_style(trace_name),
                hovertemplate=_standard_hovertemplate("Charging Power (kW)"),
            )
        )

    _apply_standard_figure_layout(
        figure,
        title=title if show_figure_title else None,
        yaxis_title="Charging Power (kW)",
        autosize=autosize,
    )
    _apply_sparse_time_ticks(
        figure,
        time_labels,
        tick_step=x_tick_step,
    )

    return figure

def _create_strategy_comparison_series_figure(
    *,
    title: str,
    yaxis_title: str,
    uncontrolled_series: list[int],
    smart_series: list[int],
    unavailable_message: str,
    show_figure_title: bool = True,
    autosize: bool = False,
    x_tick_step: int | None = None,
) -> go.Figure:
    """Create a strategy-comparison chart from two aligned timestep series."""
    if (
        len(uncontrolled_series) != len(get_time_labels())
        or len(smart_series) != len(get_time_labels())
    ):
        return _create_unavailable_time_series_figure(
            title=title,
            yaxis_title=yaxis_title,
            message=unavailable_message,
            show_figure_title=show_figure_title,
            autosize=autosize,
        )

    return _create_time_series_figure(
        traces=[
            ("Uncontrolled Charging", uncontrolled_series, None),
            ("Smart Charging", smart_series, "dash"),
        ],
        title=title,
        yaxis_title=yaxis_title,
        x_tick_step=x_tick_step,
        show_figure_title=show_figure_title,
        autosize=autosize,
    )

def _create_strategy_comparison_float_series_figure(
    *,
    title: str,
    yaxis_title: str,
    uncontrolled_series: list[float],
    smart_series: list[float],
    unavailable_message: str,
    show_figure_title: bool = True,
    autosize: bool = False,
    x_tick_step: int | None = None,
) -> go.Figure:
    """Create a strategy-comparison chart from two aligned float series."""
    if (
        len(uncontrolled_series) != len(get_time_labels())
        or len(smart_series) != len(get_time_labels())
    ):
        return _create_unavailable_time_series_figure(
            title=title,
            yaxis_title=yaxis_title,
            message=unavailable_message,
            show_figure_title=show_figure_title,
            autosize=autosize,
        )

    return _create_time_series_figure(
        traces=[
            ("Uncontrolled Charging", uncontrolled_series, None),
            ("Smart Charging", smart_series, "dash"),
        ],
        title=title,
        yaxis_title=yaxis_title,
        x_tick_step=x_tick_step,
        show_figure_title=show_figure_title,
        autosize=autosize,
    )

def _create_scenario_ab_series_figure(
    *,
    title: str,
    yaxis_title: str,
    scenario_a_series: list[int],
    scenario_b_series: list[int],
    scenario_a_label: str,
    scenario_b_label: str,
    unavailable_message: str,
    show_figure_title: bool = True,
) -> go.Figure:
    """Create a Scenario A/B chart while preserving each series length."""
    if not scenario_a_series or not scenario_b_series:
        return _create_unavailable_time_series_figure(
            title=title,
            yaxis_title=yaxis_title,
            message=unavailable_message,
            show_figure_title=show_figure_title,
            autosize=True,
        )

    series_specs = [
        (scenario_a_label, scenario_a_series, None),
        (scenario_b_label, scenario_b_series, "dash"),
    ]
    if any(_get_comparison_time_labels(len(series)) is None for _name, series, _dash in series_specs):
        return _create_unavailable_time_series_figure(
            title=title,
            yaxis_title=yaxis_title,
            message=unavailable_message,
            show_figure_title=show_figure_title,
            autosize=True,
        )

    figure = go.Figure()
    for trace_name, series, dash in series_specs:
        figure.add_trace(
            go.Scatter(
                x=_get_comparison_time_labels(len(series)),
                y=series,
                mode="lines",
                name=trace_name,
                line=_trace_line_style(trace_name, dash),
                hovertemplate=_standard_hovertemplate(yaxis_title),
            )
        )

    _apply_standard_figure_layout(
        figure,
        title=title if show_figure_title else None,
        xaxis_title="Time",
        yaxis_title=yaxis_title,
        autosize=True,
        title_pad_bottom=20,
    )
    time_labels = _get_comparison_time_labels(len(scenario_a_series))
    if time_labels is not None:
        _apply_sparse_time_ticks(
            figure,
            time_labels,
            tick_step=_comparison_time_tick_step(time_labels),
        )

    return figure

def _create_time_series_figure(
    traces: list[tuple[str, list[float], str | None]],
    title: str,
    yaxis_title: str,
    *,
    x_tick_step: int | None = None,
    show_figure_title: bool = True,
    autosize: bool = False,
) -> go.Figure:
    """Create a Plotly figure from aligned timestep series."""
    time_labels = get_time_labels()

    if any(len(series) != len(time_labels) for _name, series, _dash in traces):
        return _create_unavailable_time_series_figure(
            title=title,
            yaxis_title=yaxis_title,
            message="Time-series data unavailable for this result.",
            show_figure_title=show_figure_title,
            autosize=autosize,
        )

    figure = go.Figure()
    for trace_name, series, dash in traces:
        figure.add_trace(
            go.Scatter(
                x=time_labels,
                y=series,
                mode="lines",
                name=trace_name,
                line=_trace_line_style(trace_name, dash),
                hovertemplate=_standard_hovertemplate(yaxis_title),
            )
        )

    _apply_standard_figure_layout(
        figure,
        title=title if show_figure_title else None,
        yaxis_title=yaxis_title,
        autosize=autosize,
    )
    _apply_sparse_time_ticks(
        figure,
        time_labels,
        tick_step=x_tick_step,
    )

    return figure

def _create_count_vs_reference_figure(
    *,
    title: str,
    yaxis_title: str,
    series_name: str,
    series: list[int],
    reference_name: str,
    reference_value: int,
    unavailable_message: str,
) -> go.Figure:
    """Create a count-based chart with a constant reference line."""
    time_labels = get_time_labels()
    if len(series) != len(time_labels):
        return _create_unavailable_time_series_figure(
            title=title,
            yaxis_title=yaxis_title,
            message=unavailable_message,
        )

    return _create_time_series_figure(
        traces=[
            (series_name, series, None),
            (reference_name, [reference_value] * len(time_labels), "dash"),
        ],
        title=title,
        yaxis_title=yaxis_title,
    )

def _create_count_series_figure(
    *,
    title: str,
    yaxis_title: str,
    series_name: str,
    series: list[int],
    unavailable_message: str,
) -> go.Figure:
    """Create a chart from one count-based timestep series."""
    if len(series) != len(get_time_labels()):
        return _create_unavailable_time_series_figure(
            title=title,
            yaxis_title=yaxis_title,
            message=unavailable_message,
        )

    return _create_time_series_figure(
        traces=[(series_name, series, None)],
        title=title,
        yaxis_title=yaxis_title,
    )

def _create_float_series_figure(
    *,
    title: str,
    yaxis_title: str,
    series_name: str,
    series: list[float],
    unavailable_message: str,
    x_tick_step: int | None = None,
    show_figure_title: bool = True,
    autosize: bool = False,
) -> go.Figure:
    """Create a chart from one float-based timestep series."""
    if len(series) != len(get_time_labels()):
        return _create_unavailable_time_series_figure(
            title=title,
            yaxis_title=yaxis_title,
            message=unavailable_message,
            show_figure_title=show_figure_title,
            autosize=autosize,
        )

    return _create_time_series_figure(
        traces=[(series_name, series, None)],
        title=title,
        yaxis_title=yaxis_title,
        x_tick_step=x_tick_step,
        show_figure_title=show_figure_title,
        autosize=autosize,
    )

def _create_unavailable_time_series_figure(
    *,
    title: str,
    yaxis_title: str,
    message: str,
    show_figure_title: bool = True,
    autosize: bool = False,
) -> go.Figure:
    """Create a safe empty-state figure for unavailable time-series data."""
    figure = go.Figure()
    _apply_standard_figure_layout(
        figure,
        title=title if show_figure_title else None,
        yaxis_title=yaxis_title,
        show_legend=False,
        autosize=autosize,
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 13, "color": TEXT_SECONDARY_COLOR},
            }
        ],
    )
    figure.update_xaxes(visible=False)
    return figure

def _get_time_labels_for_series_length(
    series_length: int,
    *,
    allow_hourly_legacy: bool = False,
) -> list[str] | None:
    """Return display labels matching a supported series length."""
    full_day_labels = get_time_labels()
    if series_length == len(full_day_labels):
        return full_day_labels

    if allow_hourly_legacy and series_length == 24:
        return full_day_labels[::4]

    return None

def _get_comparison_time_labels(series_length: int) -> list[str] | None:
    """Return time labels for comparison charts, preserving differing lengths."""
    if series_length <= 0:
        return None

    standard_labels = _get_time_labels_for_series_length(
        series_length,
        allow_hourly_legacy=True,
    )
    if standard_labels is not None:
        return standard_labels

    return [f"T{index}" for index in range(1, series_length + 1)]

def _comparison_time_tick_step(time_labels: list[str]) -> int | None:
    """Return the shared sparse tick step for time-based comparison charts."""

    return _standard_time_tick_step(time_labels)

def create_scenario_ab_difference_overview_figure(
    overview_items: tuple[ScenarioComparisonOverviewItem, ...]
    | list[ScenarioComparisonOverviewItem],
    *,
    scenario_a_label: str = "Scenario A",
    scenario_b_label: str = "Scenario B",
) -> go.Figure:
    """Create a high-level overview chart of the largest Scenario A/B changes."""

    visible_candidates = list(overview_items)

    if not visible_candidates:
        return _create_scenario_ab_empty_overview_figure(
            f"{scenario_a_label} and {scenario_b_label} have no material change across the "
            "headline overview metrics."
        )

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=[candidate.relative_shift_percent for candidate in visible_candidates],
            y=[
                f"{candidate.theme}: {candidate.label}"
                for candidate in visible_candidates
            ],
            orientation="h",
            marker_color=[
                ACCENT_BLUE if candidate.raw_change > 0 else TEXT_SECONDARY_COLOR
                for candidate in visible_candidates
            ],
            text=[
                _format_scenario_ab_scalar_value(
                    candidate.change_format,
                    candidate.raw_change,
                )
                for candidate in visible_candidates
            ],
            textposition="outside",
            customdata=[
                [
                    candidate.direction_label,
                    _format_scenario_ab_scalar_value(
                        candidate.change_format,
                        candidate.raw_change,
                    ),
                ]
                for candidate in visible_candidates
            ],
            hovertemplate=(
                "%{y}<br>%{customdata[0]}: %{customdata[1]}"
                "<br>Relative shift: %{x:.1f}%<extra></extra>"
            ),
        )
    )
    _apply_standard_figure_layout(
        figure,
        title="Difference Overview",
        xaxis_title=f"Relative shift versus {scenario_a_label} (%)",
        yaxis_title="",
        margin={"l": 80, "r": 24, "t": 72, "b": 48},
    )
    figure.update_yaxes(autorange="reversed")

    return figure

def _create_scenario_ab_empty_overview_figure(message: str) -> go.Figure:
    """Return an empty overview figure with an explanatory message."""

    figure = go.Figure()
    _apply_standard_figure_layout(
        figure,
        title="Difference Overview",
        yaxis_title="",
        margin={"l": 24, "r": 24, "t": 72, "b": 48},
        show_legend=False,
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 13, "color": TEXT_SECONDARY_COLOR},
            }
        ],
    )
    return figure

def create_scenario_ab_occupancy_figure(
    metrics_a: Metrics,
    metrics_b: Metrics,
    *,
    scenario_a_label: str = "Scenario A",
    scenario_b_label: str = "Scenario B",
    show_figure_title: bool = True,
) -> go.Figure:
    """Create a chart comparing occupied chargers for Scenario A and B."""
    return _create_scenario_ab_series_figure(
        title="Occupied Chargers Over Time",
        yaxis_title="Chargers",
        scenario_a_series=metrics_a.occupied_charger_count_by_timestep,
        scenario_b_series=metrics_b.occupied_charger_count_by_timestep,
        scenario_a_label=scenario_a_label,
        scenario_b_label=scenario_b_label,
        unavailable_message=(
            f"{scenario_a_label}/{scenario_b_label} occupied-charger series unavailable for this result."
        ),
        show_figure_title=show_figure_title,
    )

def create_scenario_ab_queue_figure(
    metrics_a: Metrics,
    metrics_b: Metrics,
    *,
    scenario_a_label: str = "Scenario A",
    scenario_b_label: str = "Scenario B",
    show_figure_title: bool = True,
) -> go.Figure:
    """Create a chart comparing queue length for Scenario A and B."""
    return _create_scenario_ab_series_figure(
        title="Queue Length Over Time",
        yaxis_title="Vehicles",
        scenario_a_series=metrics_a.waiting_vehicle_count_by_timestep,
        scenario_b_series=metrics_b.waiting_vehicle_count_by_timestep,
        scenario_a_label=scenario_a_label,
        scenario_b_label=scenario_b_label,
        unavailable_message=(
            f"{scenario_a_label}/{scenario_b_label} queue-length series unavailable for this result."
        ),
        show_figure_title=show_figure_title,
    )

def create_scenario_ab_transformer_loading_figure(
    metrics_a: Metrics,
    metrics_b: Metrics,
    *,
    scenario_a_label: str = "Scenario A",
    scenario_b_label: str = "Scenario B",
    show_figure_title: bool = True,
) -> go.Figure:
    """Create a chart comparing transformer loading for Scenario A and B."""

    return _create_scenario_ab_float_series_figure(
        title="Transformer Loading Over Time",
        yaxis_title="Transformer Loading (%)",
        scenario_a_series=metrics_a.transformer_loading_percent_by_timestep,
        scenario_b_series=metrics_b.transformer_loading_percent_by_timestep,
        scenario_a_label=scenario_a_label,
        scenario_b_label=scenario_b_label,
        unavailable_message=(
            f"{scenario_a_label}/{scenario_b_label} transformer-loading series unavailable for this result."
        ),
        show_figure_title=show_figure_title,
    )

def create_scenario_ab_power_quality_figure(
    metrics_a: Metrics,
    metrics_b: Metrics,
    *,
    scenario_a_label: str = "Scenario A",
    scenario_b_label: str = "Scenario B",
    show_figure_title: bool = True,
) -> go.Figure:
    """Create a chart comparing overall PQ risk for Scenario A and B."""
    return _create_scenario_ab_float_series_figure(
        title="Overall PQ Risk Over Time",
        yaxis_title="Overall PQ Risk Score (0-100)",
        scenario_a_series=metrics_a.overall_pq_risk_score_by_timestep,
        scenario_b_series=metrics_b.overall_pq_risk_score_by_timestep,
        scenario_a_label=scenario_a_label,
        scenario_b_label=scenario_b_label,
        unavailable_message=(
            f"{scenario_a_label}/{scenario_b_label} overall PQ risk series unavailable for this result."
        ),
        show_figure_title=show_figure_title,
    )

def _create_scenario_ab_float_series_figure(
    *,
    title: str,
    yaxis_title: str,
    scenario_a_series: list[float],
    scenario_b_series: list[float],
    scenario_a_label: str,
    scenario_b_label: str,
    unavailable_message: str,
    show_figure_title: bool = True,
) -> go.Figure:
    """Create a Scenario A/B chart while preserving each float-series length."""
    if not scenario_a_series or not scenario_b_series:
        return _create_unavailable_time_series_figure(
            title=title,
            yaxis_title=yaxis_title,
            message=unavailable_message,
            show_figure_title=show_figure_title,
            autosize=True,
        )

    series_specs = [
        (scenario_a_label, scenario_a_series, None),
        (scenario_b_label, scenario_b_series, "dash"),
    ]
    if any(
        _get_comparison_time_labels(len(series)) is None
        for _name, series, _dash in series_specs
    ):
        return _create_unavailable_time_series_figure(
            title=title,
            yaxis_title=yaxis_title,
            message=unavailable_message,
            show_figure_title=show_figure_title,
            autosize=True,
        )

    figure = go.Figure()
    for trace_name, series, dash in series_specs:
        figure.add_trace(
            go.Scatter(
                x=_get_comparison_time_labels(len(series)),
                y=series,
                mode="lines",
                name=trace_name,
                line=_trace_line_style(trace_name, dash),
                hovertemplate=_standard_hovertemplate(yaxis_title),
            )
        )

    _apply_standard_figure_layout(
        figure,
        title=title if show_figure_title else None,
        xaxis_title="Time",
        yaxis_title=yaxis_title,
        autosize=True,
        title_pad_bottom=20,
    )
    time_labels = _get_comparison_time_labels(len(scenario_a_series))
    if time_labels is not None:
        _apply_sparse_time_ticks(
            figure,
            time_labels,
            tick_step=_comparison_time_tick_step(time_labels),
        )

    return figure

__all__ = [

    '_standard_legend_layout',

    '_apply_standard_figure_layout',

    '_apply_sparse_time_ticks',

    '_standard_time_tick_step',

    '_hover_value_format_parts',

    '_standard_hovertemplate',

    '_trace_line_style',

    'create_load_profile_figure',

    'create_capacity_vs_load_figure',

    'create_charger_occupancy_figure',

    'create_service_pressure_figure',

    'create_queue_length_figure',

    'create_power_capacity_over_time_figure',

    'create_comparison_load_profile_figure',

    'create_comparison_occupancy_figure',

    'create_comparison_queue_figure',

    'create_comparison_power_quality_figure',

    'create_transformer_loading_figure',

    'create_harmonic_risk_figure',

    'create_current_imbalance_figure',

    'create_phase_load_figure',

    '_create_load_profile_figure',

    '_create_strategy_comparison_series_figure',

    '_create_strategy_comparison_float_series_figure',

    '_create_scenario_ab_series_figure',

    '_create_time_series_figure',

    '_create_count_vs_reference_figure',

    '_create_count_series_figure',

    '_create_float_series_figure',

    '_create_unavailable_time_series_figure',

    '_get_time_labels_for_series_length',

    '_get_comparison_time_labels',

    '_comparison_time_tick_step',

    'create_scenario_ab_difference_overview_figure',

    '_create_scenario_ab_empty_overview_figure',

    'create_scenario_ab_occupancy_figure',

    'create_scenario_ab_queue_figure',

    'create_scenario_ab_transformer_loading_figure',

    'create_scenario_ab_power_quality_figure',

    '_create_scenario_ab_float_series_figure',

]

