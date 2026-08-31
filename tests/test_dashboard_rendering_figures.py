from tests.helpers import *  # noqa: F401,F403

def test_load_profile_figure_uses_shared_timestep_labels():
    load_profile = [float(index) for index in range(len(get_time_labels()))]

    figure = create_load_profile_figure(load_profile)

    assert list(figure.data[0].x) == get_time_labels()
    assert list(figure.data[0].y) == load_profile
    assert figure.data[0].mode == "lines"
    assert figure.layout.title.text == "Charging Load Profile"
    assert figure.layout.yaxis.title.text == "Charging Power (kW)"
    assert figure.layout.height == GRAPH_HEIGHT_PX
    assert figure.layout.autosize is False

def test_capacity_vs_load_figure_contains_requested_and_delivered_traces():
    simulation_result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=80.0,
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=80.0,
        requested_load_profile_kw=[100.0, 0.0] + [0.0] * (len(get_time_labels()) - 2),
        delivered_load_profile_kw=[80.0, 0.0] + [0.0] * (len(get_time_labels()) - 2),
    )
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=80.0,
        energy_delivery_sufficient=False,
        peak_load=80.0,
        connection_capacity_exceeded=True,
    )

    figure = create_capacity_vs_load_figure(simulation_result, metrics)

    visible_trace_names = [trace.name for trace in figure.data if trace.name is not None]
    assert visible_trace_names == [
        "Delivered Charging Load",
        "Requested Charging Demand",
        "Configured Connection Capacity",
    ]
    delivered_trace = next(
        trace for trace in figure.data if trace.name == "Delivered Charging Load"
    )
    requested_trace = next(
        trace for trace in figure.data if trace.name == "Requested Charging Demand"
    )
    assert list(delivered_trace.y) == simulation_result.delivered_load_profile_kw
    assert list(requested_trace.y) == simulation_result.requested_load_profile_kw
    assert figure.layout.title.text is None
    assert figure.layout.yaxis.title.text == "Charging Power (kW)"
    assert figure.layout.height == 400
    assert figure.layout.xaxis.tickmode == "array"
    assert list(figure.layout.xaxis.tickvals) == get_time_labels()[::8]
    assert (
        delivered_trace.hovertemplate
        == "%{y:,.1f} kW<extra>%{fullData.name}</extra>"
    )

def test_capacity_vs_load_figure_contains_configured_capacity_reference_line():
    simulation_result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=80.0,
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=80.0,
        requested_load_profile_kw=[100.0] + [0.0] * (len(get_time_labels()) - 1),
        delivered_load_profile_kw=[80.0] + [0.0] * (len(get_time_labels()) - 1),
    )
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=80.0,
        energy_delivery_sufficient=False,
        peak_load=80.0,
        connection_capacity_exceeded=True,
    )

    figure = create_capacity_vs_load_figure(simulation_result, metrics)

    configured_capacity_trace = next(
        trace
        for trace in figure.data
        if trace.name == "Configured Connection Capacity"
    )
    assert list(configured_capacity_trace.y) == [80.0] * len(get_time_labels())

def test_capacity_vs_load_figure_adds_exceedance_highlighting_when_capacity_is_exceeded():
    simulation_result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=80.0,
        installed_charger_capacity_kw=120.0,
        available_site_charging_capacity_kw=80.0,
        requested_load_profile_kw=[70.0, 100.0, 90.0, 60.0]
        + [0.0] * (len(get_time_labels()) - 4),
        delivered_load_profile_kw=[70.0, 80.0, 80.0, 60.0]
        + [0.0] * (len(get_time_labels()) - 4),
    )
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=80.0,
        energy_delivery_sufficient=True,
        peak_load=80.0,
        connection_capacity_exceeded=True,
    )

    figure = create_capacity_vs_load_figure(simulation_result, metrics)

    assert len(figure.data) == 3
    assert figure.data[2].name == "Configured Connection Capacity"

def test_capacity_vs_load_figure_omits_exceedance_highlighting_when_capacity_not_exceeded():
    simulation_result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=80.0,
        installed_charger_capacity_kw=80.0,
        available_site_charging_capacity_kw=80.0,
        requested_load_profile_kw=[70.0, 80.0, 60.0]
        + [0.0] * (len(get_time_labels()) - 3),
        delivered_load_profile_kw=[70.0, 80.0, 60.0]
        + [0.0] * (len(get_time_labels()) - 3),
    )
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=80.0,
        energy_delivery_sufficient=True,
        peak_load=80.0,
        connection_capacity_exceeded=False,
    )

    figure = create_capacity_vs_load_figure(simulation_result, metrics)

    assert len(figure.data) == 3
    assert all(trace.name != "Requested Load Exceedance" for trace in figure.data)

def test_capacity_vs_load_figure_aligns_requested_and_delivered_time_axes():
    simulation_result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=80.0,
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=80.0,
        requested_load_profile_kw=[100.0] + [0.0] * 23,
        delivered_load_profile_kw=[80.0] + [0.0] * 23,
    )
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=80.0,
        energy_delivery_sufficient=False,
        peak_load=80.0,
        connection_capacity_exceeded=True,
    )

    figure = create_capacity_vs_load_figure(simulation_result, metrics)

    assert list(figure.data[0].x) == list(figure.data[1].x)
    assert list(figure.data[1].x) == list(figure.data[2].x)

def test_capacity_vs_load_figure_renders_identical_profiles_safely():
    simulation_result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[25.0, 25.0, 25.0, 25.0] + [0.0] * 20,
        delivered_load_profile_kw=[25.0, 25.0, 25.0, 25.0] + [0.0] * 20,
    )
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=100.0,
        energy_delivery_sufficient=True,
        peak_load=25.0,
        connection_capacity_exceeded=False,
    )

    figure = create_capacity_vs_load_figure(simulation_result, metrics)

    assert len(figure.data) == 3
    assert list(figure.data[0].y) == list(figure.data[1].y)

def test_charger_occupancy_figure_uses_metrics_series_and_scenario_charger_count():
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=80.0,
        energy_delivery_sufficient=True,
        occupied_charger_count_by_timestep=[1.0, 2.0] + [0.0] * 94,
    )
    scenario = Scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=3,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )

    figure = create_charger_occupancy_figure(metrics, scenario)

    assert [trace.name for trace in figure.data] == [
        "Occupied Chargers",
        "Available Chargers",
    ]
    assert list(figure.data[0].x) == get_time_labels()
    assert list(figure.data[0].y[:4]) == [1.0, 2.0, 0.0, 0.0]
    assert list(figure.data[1].y) == [3] * len(get_time_labels())
    assert figure.layout.title.text == "Charger Occupancy Over Time"
    assert figure.layout.yaxis.title.text == "Chargers"

def test_queue_length_figure_uses_metrics_series_without_recalculation():
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=80.0,
        energy_delivery_sufficient=True,
        waiting_vehicle_count_by_timestep=[0, 2, 1] + [0] * 93,
        maximum_queue_length=99,
    )

    figure = create_queue_length_figure(metrics)

    assert [trace.name for trace in figure.data] == ["Waiting Vehicles"]
    assert list(figure.data[0].x) == get_time_labels()
    assert list(figure.data[0].y[:4]) == [0, 2, 1, 0]
    assert figure.layout.title.text == "Queue Length Over Time"
    assert figure.layout.yaxis.title.text == "Vehicles"
    assert 99 not in list(figure.data[0].y)

def test_service_pressure_figure_includes_queue_trace_when_queue_is_present():
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=80.0,
        energy_delivery_sufficient=True,
        occupied_charger_count_by_timestep=[1.0, 2.0] + [0.0] * 94,
        waiting_vehicle_count_by_timestep=[0, 2, 1] + [0] * 93,
    )
    scenario = Scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=3,
        charger_power=50.0,
        grid_capacity=100.0,
        charging_window_start=time(8, 0),
        charging_window_end=time(9, 0),
    )

    figure = create_service_pressure_figure(metrics, scenario)

    assert [trace.name for trace in figure.data] == [
        "Occupied Chargers",
        "Charger Capacity",
        "Waiting Vehicles",
    ]
    assert list(figure.data[0].x) == get_time_labels()
    assert list(figure.data[0].y[:4]) == [1.0, 2.0, 0.0, 0.0]
    assert list(figure.data[1].y) == [3] * len(get_time_labels())
    assert list(figure.data[2].y[:4]) == [0, 2, 1, 0]
    assert figure.layout.title.text is None
    assert figure.layout.yaxis.title.text == "Chargers"
    assert figure.layout.yaxis2.title.text == "Waiting Vehicles"
    assert figure.layout.height == 360
    assert figure.layout.autosize is True
    assert figure.layout.legend.y == 1.08
    assert figure.layout.margin.t == 38
    assert figure.layout.margin.b == 58
    assert figure.layout.xaxis.ticklabelstandoff == 6
    assert figure.layout.xaxis.tickmode == "array"
    assert list(figure.layout.xaxis.tickvals) == get_time_labels()[::8]
    assert (
        figure.data[0].hovertemplate
        == "%{y:,.0f} chargers<extra>%{fullData.name}</extra>"
    )
    assert (
        figure.data[2].hovertemplate
        == "%{y:,.0f} vehicles<extra>%{fullData.name}</extra>"
    )

def test_power_capacity_over_time_figure_uses_delivered_load_installed_and_grid_capacity():
    simulation_result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=80.0,
        installed_charger_capacity_kw=120.0,
        available_site_charging_capacity_kw=80.0,
        delivered_load_profile_kw=[70.0, 80.0, 0.0] + [0.0] * 93,
    )

    figure = create_power_capacity_over_time_figure(simulation_result)

    assert [trace.name for trace in figure.data] == [
        "Delivered Charging Power",
        "Installed Charger Capacity",
        "Grid Connection Capacity",
    ]
    assert list(figure.data[0].y[:4]) == [70.0, 80.0, 0.0, 0.0]
    assert list(figure.data[1].y) == [120.0] * len(get_time_labels())
    assert list(figure.data[2].y) == [80.0] * len(get_time_labels())
    assert figure.layout.title.text is None
    assert figure.layout.yaxis.title.text == "Charging Power (kW)"
    assert figure.layout.autosize is True
    assert figure.layout.legend.y == 1.08
    assert figure.layout.xaxis.tickmode == "array"
    assert list(figure.layout.xaxis.tickvals) == get_time_labels()[::8]
    assert (
        figure.data[0].hovertemplate
        == "%{y:,.1f} kW<extra>%{fullData.name}</extra>"
    )

def test_new_infrastructure_charts_render_zero_value_series_normally():
    metrics = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        occupied_charger_count_by_timestep=[0] * len(get_time_labels()),
        waiting_vehicle_count_by_timestep=[0] * len(get_time_labels()),
    )
    scenario = create_internal_scenario(
        vehicles=0,
        daily_energy_per_vehicle=20.0,
        charger_count=0,
        charger_power=50.0,
        grid_capacity=1.0,
    )
    simulation_result = SimulationResult(
        daily_energy_demand=0.0,
        configured_connection_capacity_kw=0.0,
        installed_charger_capacity_kw=0.0,
        available_site_charging_capacity_kw=0.0,
        delivered_load_profile_kw=[0.0] * len(get_time_labels()),
    )

    service_pressure_figure = create_service_pressure_figure(metrics, scenario)
    power_figure = create_power_capacity_over_time_figure(simulation_result)

    assert [trace.name for trace in service_pressure_figure.data] == [
        "Occupied Chargers",
        "Charger Capacity",
    ]
    assert service_pressure_figure.layout.title.text is None
    assert list(service_pressure_figure.data[0].y) == [0] * len(get_time_labels())
    assert list(service_pressure_figure.data[1].y) == [0] * len(get_time_labels())
    assert list(power_figure.data[0].y) == [0.0] * len(get_time_labels())
    assert list(power_figure.data[1].y) == [0.0] * len(get_time_labels())
    assert list(power_figure.data[2].y) == [0.0] * len(get_time_labels())

def test_new_infrastructure_charts_render_unavailable_state_for_legacy_or_incomplete_series():
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=80.0,
        energy_delivery_sufficient=True,
        occupied_charger_count_by_timestep=[1],
        waiting_vehicle_count_by_timestep=[],
    )
    scenario = Scenario(
        vehicles=2,
        daily_energy_per_vehicle=20.0,
        charger_count=2,
        charger_power=50.0,
        grid_capacity=100.0,
    )
    simulation_result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=80.0,
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=80.0,
        delivered_load_profile_kw=[80.0],
    )

    service_pressure_figure = create_service_pressure_figure(metrics, scenario)
    power_figure = create_power_capacity_over_time_figure(simulation_result)

    assert len(service_pressure_figure.data) == 0
    assert service_pressure_figure.layout.annotations[0].text == (
        "Service-pressure series unavailable for this result."
    )
    assert len(power_figure.data) == 0
    assert power_figure.layout.annotations[0].text == (
        "Charging power series unavailable for this result."
    )

def test_comparison_load_profile_figure_uses_strategy_result_profiles():
    uncontrolled_result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[100.0] + [0.0] * 23,
        delivered_load_profile_kw=[100.0] + [0.0] * 23,
        delivered_energy=100.0,
        unmet_energy=0.0,
    )
    smart_result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=100.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[25.0, 25.0, 25.0, 25.0] + [0.0] * 20,
        delivered_load_profile_kw=[25.0, 25.0, 25.0, 25.0] + [0.0] * 20,
        delivered_energy=100.0,
        unmet_energy=0.0,
    )

    figure = create_comparison_load_profile_figure(
        uncontrolled_result,
        smart_result,
    )

    assert [trace.name for trace in figure.data] == [
        "Uncontrolled Charging",
        "Smart Charging",
    ]
    assert list(figure.data[0].y) == uncontrolled_result.load_profile
    assert list(figure.data[1].y) == smart_result.load_profile
    assert list(figure.data[0].x) == list(figure.data[1].x)
    assert figure.layout.title.text is None
    assert figure.layout.height == GRAPH_HEIGHT_PX
    assert figure.layout.autosize is True
    assert figure.layout.xaxis.tickmode == "array"
    assert list(figure.layout.xaxis.tickvals) == get_time_labels()[::4][::2]
    assert (
        figure.data[0].hovertemplate
        == "%{y:,.1f} kW<extra>%{fullData.name}</extra>"
    )

def test_comparison_load_profile_figure_uses_delivered_profile_not_requested_profile():
    uncontrolled_result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=150.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[150.0] + [0.0] * 23,
        delivered_load_profile_kw=[100.0] + [0.0] * 23,
        delivered_energy=100.0,
        unmet_energy=0.0,
    )
    smart_result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=100.0,
        installed_charger_capacity_kw=150.0,
        available_site_charging_capacity_kw=100.0,
        requested_load_profile_kw=[75.0, 75.0] + [0.0] * 22,
        delivered_load_profile_kw=[50.0, 50.0] + [0.0] * 22,
        delivered_energy=100.0,
        unmet_energy=0.0,
    )

    figure = create_comparison_load_profile_figure(
        uncontrolled_result,
        smart_result,
    )

    assert list(figure.data[0].y) == uncontrolled_result.delivered_load_profile_kw
    assert list(figure.data[1].y) == smart_result.delivered_load_profile_kw

def test_dashboard_comparison_occupancy_chart_uses_prepared_strategy_series():
    comparison_metrics = ComparisonMetrics(
        peak_reduction=0.0,
        relative_peak_reduction=0.0,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
        uncontrolled_occupied_charger_count_by_timestep=[1, 2, 0]
        + [0] * (len(get_time_labels()) - 3),
        smart_occupied_charger_count_by_timestep=[1, 1, 1]
        + [0] * (len(get_time_labels()) - 3),
    )

    figure = create_comparison_occupancy_figure(comparison_metrics)

    assert [trace.name for trace in figure.data] == [
        "Uncontrolled Charging",
        "Smart Charging",
    ]
    assert list(figure.data[0].x) == get_time_labels()
    assert list(figure.data[0].y[:4]) == [1, 2, 0, 0]
    assert list(figure.data[1].y[:4]) == [1, 1, 1, 0]
    assert figure.layout.title.text is None
    assert figure.layout.autosize is True
    assert figure.layout.yaxis.title.text == "Chargers"

def test_dashboard_comparison_queue_chart_uses_prepared_strategy_series():
    comparison_metrics = ComparisonMetrics(
        peak_reduction=0.0,
        relative_peak_reduction=0.0,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
        uncontrolled_waiting_vehicle_count_by_timestep=[0, 2, 1]
        + [0] * (len(get_time_labels()) - 3),
        smart_waiting_vehicle_count_by_timestep=[0, 1, 0]
        + [0] * (len(get_time_labels()) - 3),
        maximum_queue_length_difference=99,
    )

    figure = create_comparison_queue_figure(comparison_metrics)

    assert [trace.name for trace in figure.data] == [
        "Uncontrolled Charging",
        "Smart Charging",
    ]
    assert list(figure.data[0].x) == get_time_labels()
    assert list(figure.data[0].y[:4]) == [0, 2, 1, 0]
    assert list(figure.data[1].y[:4]) == [0, 1, 0, 0]
    assert figure.layout.title.text is None
    assert figure.layout.autosize is True
    assert figure.layout.yaxis.title.text == "Vehicles"
    assert 99 not in list(figure.data[0].y)

def test_dashboard_comparison_power_quality_chart_uses_prepared_strategy_series():
    comparison_metrics = ComparisonMetrics(
        peak_reduction=0.0,
        relative_peak_reduction=0.0,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
        uncontrolled_overall_pq_risk_score_by_timestep=[40.0, 55.0, 35.0]
        + [0.0] * (len(get_time_labels()) - 3),
        smart_overall_pq_risk_score_by_timestep=[25.0, 32.0, 22.0]
        + [0.0] * (len(get_time_labels()) - 3),
    )

    figure = create_comparison_power_quality_figure(comparison_metrics)

    assert [trace.name for trace in figure.data] == [
        "Uncontrolled Charging",
        "Smart Charging",
    ]
    assert list(figure.data[0].x) == get_time_labels()
    assert list(figure.data[0].y[:4]) == [40.0, 55.0, 35.0, 0.0]
    assert list(figure.data[1].y[:4]) == [25.0, 32.0, 22.0, 0.0]
    assert figure.layout.title.text is None
    assert figure.layout.autosize is True
    assert figure.layout.yaxis.title.text == "Overall PQ Risk Score (0-100)"

def test_dashboard_transformer_loading_figure_uses_metrics_series_only():
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=80.0,
        energy_delivery_sufficient=True,
        transformer_loading_percent_by_timestep=[95.0, 105.0, 90.0]
        + [0.0] * (len(get_time_labels()) - 3),
    )

    figure = create_transformer_loading_figure(metrics)

    assert [trace.name for trace in figure.data] == [
        "Transformer Loading",
        "Transformer Rating",
        "Overload Range",
    ]
    assert list(figure.data[0].x) == get_time_labels()
    assert list(figure.data[0].y[:4]) == [95.0, 105.0, 90.0, 0.0]
    assert list(figure.data[1].y[:4]) == [100.0, 100.0, 100.0, 100.0]
    assert list(figure.data[2].y[:4]) == [None, 105.0, None, None]
    assert figure.layout.title.text is None
    assert figure.layout.yaxis.title.text == "Transformer Loading (%)"
    assert figure.layout.autosize is True
    assert figure.layout.xaxis.tickmode == "array"
    assert list(figure.layout.xaxis.tickvals) == get_time_labels()[::8]
    assert (
        figure.data[0].hovertemplate
        == "%{y:,.1f} %<extra>%{fullData.name}</extra>"
    )

def test_dashboard_transformer_loading_figure_renders_safe_empty_state():
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=80.0,
        energy_delivery_sufficient=True,
        transformer_loading_percent_by_timestep=[],
    )

    figure = create_transformer_loading_figure(metrics)

    assert len(figure.data) == 0
    assert figure.layout.title.text is None
    assert figure.layout.autosize is True
    assert figure.layout.annotations[0].text == (
        "Transformer loading series unavailable for this result."
    )

def test_dashboard_harmonic_risk_figure_uses_metrics_series_only():
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=80.0,
        energy_delivery_sufficient=True,
        harmonic_risk_score_by_timestep=[35.0, 55.0, 45.0]
        + [0.0] * (len(get_time_labels()) - 3),
    )

    figure = create_harmonic_risk_figure(metrics)

    assert [trace.name for trace in figure.data] == ["Harmonic Risk"]
    assert list(figure.data[0].x) == get_time_labels()
    assert list(figure.data[0].y[:4]) == [35.0, 55.0, 45.0, 0.0]
    assert figure.layout.title.text is None
    assert figure.layout.yaxis.title.text == "Harmonic Risk Score (0-100)"
    assert figure.layout.xaxis.tickmode == "array"
    assert list(figure.layout.xaxis.tickvals) == get_time_labels()[::8]
    assert figure.layout.autosize is True

def test_dashboard_current_imbalance_figure_uses_metrics_series_only():
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=80.0,
        energy_delivery_sufficient=True,
        current_imbalance_percent_by_timestep=[6.0, 14.0, 10.0]
        + [0.0] * (len(get_time_labels()) - 3),
    )

    figure = create_current_imbalance_figure(metrics)

    assert [trace.name for trace in figure.data] == ["Current Imbalance"]
    assert list(figure.data[0].x) == get_time_labels()
    assert list(figure.data[0].y[:4]) == [6.0, 14.0, 10.0, 0.0]
    assert figure.layout.title.text is None
    assert figure.layout.yaxis.title.text == "Current Imbalance (%)"
    assert figure.layout.xaxis.tickmode == "array"
    assert list(figure.layout.xaxis.tickvals) == get_time_labels()[::8]
    assert figure.layout.autosize is True

def test_dashboard_phase_load_figure_uses_metrics_series_only():
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=80.0,
        energy_delivery_sufficient=True,
        phase_a_load_kw_by_timestep=[30.0, 35.0, 25.0]
        + [0.0] * (len(get_time_labels()) - 3),
        phase_b_load_kw_by_timestep=[20.0, 25.0, 22.0]
        + [0.0] * (len(get_time_labels()) - 3),
        phase_c_load_kw_by_timestep=[18.0, 24.0, 20.0]
        + [0.0] * (len(get_time_labels()) - 3),
    )

    figure = create_phase_load_figure(metrics)

    assert [trace.name for trace in figure.data] == [
        "Phase A",
        "Phase B",
        "Phase C",
    ]
    assert list(figure.data[0].x) == get_time_labels()
    assert list(figure.data[0].y[:4]) == [30.0, 35.0, 25.0, 0.0]
    assert list(figure.data[1].y[:4]) == [20.0, 25.0, 22.0, 0.0]
    assert list(figure.data[2].y[:4]) == [18.0, 24.0, 20.0, 0.0]
    assert figure.layout.title.text is None
    assert figure.layout.yaxis.title.text == "Phase Load (kW)"
    assert figure.layout.xaxis.tickmode == "array"
    assert list(figure.layout.xaxis.tickvals) == get_time_labels()[::8]
    assert figure.layout.autosize is True

def test_dashboard_power_quality_figures_render_safe_empty_states():
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=80.0,
        energy_delivery_sufficient=True,
        harmonic_risk_score_by_timestep=[],
        current_imbalance_percent_by_timestep=[],
        phase_a_load_kw_by_timestep=[],
        phase_b_load_kw_by_timestep=[],
        phase_c_load_kw_by_timestep=[],
    )

    harmonic_figure = create_harmonic_risk_figure(metrics)
    imbalance_figure = create_current_imbalance_figure(metrics)
    phase_load_figure = create_phase_load_figure(metrics)

    assert len(harmonic_figure.data) == 0
    assert harmonic_figure.layout.title.text is None
    assert harmonic_figure.layout.autosize is True
    assert harmonic_figure.layout.annotations[0].text == (
        "Harmonic-risk series unavailable for this result."
    )
    assert len(imbalance_figure.data) == 0
    assert imbalance_figure.layout.title.text is None
    assert imbalance_figure.layout.autosize is True
    assert imbalance_figure.layout.annotations[0].text == (
        "Current-imbalance series unavailable for this result."
    )
    assert len(phase_load_figure.data) == 0
    assert phase_load_figure.layout.title.text is None
    assert phase_load_figure.layout.autosize is True
    assert phase_load_figure.layout.annotations[0].text == (
        "Phase-load series unavailable for this result."
    )

def test_scenario_ab_evidence_figures_add_extra_spacing_below_chart_titles():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        occupied_charger_count_by_timestep=[1, 2, 3, 2],
        waiting_vehicle_count_by_timestep=[0, 1, 1, 0],
        overall_pq_risk_score_by_timestep=[8.0, 10.0, 12.0, 9.0],
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        occupied_charger_count_by_timestep=[1, 1, 2, 2],
        waiting_vehicle_count_by_timestep=[0, 0, 1, 0],
        overall_pq_risk_score_by_timestep=[7.0, 9.0, 10.0, 8.0],
    )

    occupancy_figure = create_scenario_ab_occupancy_figure(metrics_a, metrics_b)
    queue_figure = create_scenario_ab_queue_figure(metrics_a, metrics_b)
    pq_figure = create_scenario_ab_power_quality_figure(metrics_a, metrics_b)

    assert occupancy_figure.layout.title.pad.b == 20
    assert queue_figure.layout.title.pad.b == 20
    assert pq_figure.layout.title.pad.b == 20

def test_scenario_ab_evidence_panel_renders_external_chart_titles_with_full_width_graphs():
    metrics_a = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        average_occupied_charger_count=2.0,
        peak_occupied_charger_count=4,
        occupied_charger_count_by_timestep=[1, 2, 3, 4],
        queue_present_indicator=True,
        maximum_queue_length=3,
        average_queue_length=1.5,
        queue_duration_hours=2.0,
        waiting_vehicle_count_by_timestep=[0, 1, 2, 1],
        overall_pq_risk_level="moderate",
        overall_pq_risk_score=34.0,
        power_quality_warning_count=2,
        overall_pq_risk_score_by_timestep=[20.0, 30.0, 40.0, 35.0],
    )
    metrics_b = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        average_occupied_charger_count=1.0,
        peak_occupied_charger_count=2,
        occupied_charger_count_by_timestep=[1, 1, 2, 2],
        queue_present_indicator=False,
        maximum_queue_length=1,
        average_queue_length=0.5,
        queue_duration_hours=0.5,
        average_waiting_time_hours=0.25,
        maximum_waiting_time_hours=0.5,
        waiting_vehicle_count_by_timestep=[0, 0, 1, 0],
        overall_pq_risk_level="low",
        overall_pq_risk_score=18.0,
        power_quality_warning_count=0,
        overall_pq_risk_score_by_timestep=[12.0, 16.0, 18.0, 15.0],
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=0.0,
        peak_load_change_percent=None,
        capacity_utilization_difference_percentage_points=0.0,
        capacity_utilization_change_percent=None,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=None,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=None,
        average_transformer_loading_percent_difference=0.0,
        peak_transformer_loading_percent_difference=0.0,
        transformer_overload_duration_hours_difference=0.0,
        transformer_maximum_overload_kw_difference=0.0,
        maximum_feeder_loading_percent_difference=0.0,
        overloaded_feeder_count_difference=0,
        peak_harmonic_risk_score_difference=0.0,
        harmonic_risk_duration_hours_difference=0.0,
        peak_current_imbalance_percent_difference=0.0,
        imbalance_duration_hours_difference=0.0,
        average_occupied_charger_count_difference=-1.0,
        peak_occupied_charger_count_difference=-2,
        maximum_queue_length_difference=-2,
        average_queue_length_difference=-1.0,
        queue_duration_hours_difference=-1.5,
        average_waiting_time_hours_difference=None,
        maximum_waiting_time_hours_difference=None,
        overall_pq_risk_score_difference=-16.0,
        power_quality_warning_count_difference=-2,
        vehicles_waiting_count_difference=0,
        vehicles_not_started_count_difference=0,
        vehicles_with_unmet_energy_count_difference=0,
        charger_capacity_vs_demand_balance_difference=0,
        required_charger_count_difference=None,
        additional_chargers_required_difference=None,
    )

    queueing_sections = render_scenario_ab_detailed_sections(
        metrics_a,
        metrics_b,
        comparison_metrics,
        selected_section_id="queueing",
    )
    queueing_content = _find_component_by_id(
        queueing_sections,
        "scenario-ab-section-content-queueing",
    )
    assert queueing_content is not None
    queueing_chart_content = queueing_content.children[1].children[0]
    assert queueing_chart_content.children[0].children == "Queue Length Over Time"
    queueing_chart_shell = queueing_chart_content.children[1]
    assert queueing_chart_shell.style["width"] == "100%"
    queueing_chart = queueing_chart_shell.children
    assert queueing_chart.id == "scenario-ab-queue-chart"
    assert queueing_chart.figure.layout.title.text is None

    infrastructure_sections = render_scenario_ab_detailed_sections(
        metrics_a,
        metrics_b,
        comparison_metrics,
        selected_section_id="infrastructure",
    )
    infrastructure_content = _find_component_by_id(
        infrastructure_sections,
        "scenario-ab-section-content-infrastructure",
    )
    assert infrastructure_content is not None
    infrastructure_chart_content = infrastructure_content.children[1].children[0]
    assert infrastructure_chart_content.children[0].children == "Occupied Chargers Over Time"
    infrastructure_chart_shell = infrastructure_chart_content.children[1]
    assert infrastructure_chart_shell.style["width"] == "100%"
    infrastructure_chart = infrastructure_chart_shell.children
    assert infrastructure_chart.id == "scenario-ab-occupancy-chart"
    assert infrastructure_chart.figure.layout.title.text is None

    power_quality_sections = render_scenario_ab_detailed_sections(
        metrics_a,
        metrics_b,
        comparison_metrics,
        selected_section_id="power_quality",
    )
    power_quality_content = _find_component_by_id(
        power_quality_sections,
        "scenario-ab-section-content-power_quality",
    )
    assert power_quality_content is not None
    power_quality_chart_content = power_quality_content.children[1].children[0]
    assert power_quality_chart_content.children[0].children == "Overall PQ Risk Over Time"
    power_quality_chart_shell = power_quality_chart_content.children[1]
    assert power_quality_chart_shell.style["width"] == "100%"
    power_quality_chart = power_quality_chart_shell.children
    assert power_quality_chart.id == "scenario-ab-pq-risk-chart"
    assert power_quality_chart.figure.layout.title.text is None

    grid_metrics_a = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        average_transformer_loading_percent=92.0,
        peak_transformer_loading_percent=110.0,
        transformer_overload_indicator=True,
        transformer_overload_duration_hours=1.5,
        transformer_maximum_overload_kw=18.0,
        transformer_thermal_risk_level="high",
        maximum_feeder_loading_percent=104.0,
        feeder_overload_indicator=True,
        overloaded_feeder_count=2,
        highest_feeder_thermal_risk_level="high",
        transformer_loading_percent_by_timestep=[88.0, 95.0, 108.0, 110.0],
    )
    grid_metrics_b = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        average_transformer_loading_percent=68.0,
        peak_transformer_loading_percent=84.0,
        transformer_overload_indicator=False,
        transformer_overload_duration_hours=0.0,
        transformer_maximum_overload_kw=0.0,
        transformer_thermal_risk_level="low",
        maximum_feeder_loading_percent=79.0,
        feeder_overload_indicator=False,
        overloaded_feeder_count=0,
        highest_feeder_thermal_risk_level="low",
        transformer_loading_percent_by_timestep=[58.0, 63.0, 80.0, 84.0],
    )
    grid_comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=0.0,
        peak_load_change_percent=None,
        capacity_utilization_difference_percentage_points=0.0,
        capacity_utilization_change_percent=None,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=None,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=None,
        average_transformer_loading_percent_difference=-24.0,
        peak_transformer_loading_percent_difference=-26.0,
        transformer_overload_duration_hours_difference=-1.5,
        transformer_maximum_overload_kw_difference=-18.0,
        maximum_feeder_loading_percent_difference=-25.0,
        overloaded_feeder_count_difference=-2,
        peak_harmonic_risk_score_difference=0.0,
        harmonic_risk_duration_hours_difference=0.0,
        peak_current_imbalance_percent_difference=0.0,
        imbalance_duration_hours_difference=0.0,
        overall_pq_risk_score_difference=0.0,
        power_quality_warning_count_difference=0,
        average_occupied_charger_count_difference=0.0,
        peak_occupied_charger_count_difference=0,
        maximum_queue_length_difference=0,
        average_queue_length_difference=0.0,
        queue_duration_hours_difference=0.0,
        average_waiting_time_hours_difference=None,
        maximum_waiting_time_hours_difference=None,
        vehicles_waiting_count_difference=0,
        vehicles_not_started_count_difference=0,
        vehicles_with_unmet_energy_count_difference=0,
        charger_capacity_vs_demand_balance_difference=0,
        required_charger_count_difference=None,
        additional_chargers_required_difference=None,
    )

    grid_sections = render_scenario_ab_detailed_sections(
        grid_metrics_a,
        grid_metrics_b,
        grid_comparison_metrics,
        selected_section_id="grid",
    )
    grid_text = " ".join(_collect_text(grid_sections))
    assert "Peak transformer loading (%)" in grid_text
    assert "Maximum feeder loading (%)" in grid_text
    assert "Transformer overload duration (h)" in grid_text
    grid_content = _find_component_by_id(
        grid_sections,
        "scenario-ab-section-content-grid",
    )
    assert grid_content is not None
    grid_chart_block = grid_content.children[1].children[0]
    assert "scenario-ab-evidence-chart-block" in grid_chart_block.className
    assert grid_chart_block.children[0].children == "Transformer Loading Over Time"
    grid_chart_shell = grid_chart_block.children[1]
    assert "scenario-ab-evidence-chart-shell" in grid_chart_shell.className
    assert grid_chart_shell.style["width"] == "100%"
    grid_chart = grid_chart_shell.children
    assert grid_chart.id == "scenario-ab-transformer-loading-chart"
    assert grid_chart.figure.layout.title.text is None

def test_dashboard_scenario_ab_occupancy_chart_preserves_scenario_specific_series_lengths():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        occupied_charger_count_by_timestep=[0, 1, 1],
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        occupied_charger_count_by_timestep=[1, 1],
    )

    figure = create_scenario_ab_occupancy_figure(
        metrics_a,
        metrics_b,
        scenario_a_label="Heavy-duty",
        scenario_b_label="Workplace Charging",
    )

    assert [trace.name for trace in figure.data] == [
        "Heavy-duty",
        "Workplace Charging",
    ]
    assert list(figure.data[0].x) == ["T1", "T2", "T3"]
    assert list(figure.data[1].x) == ["T1", "T2"]
    assert list(figure.data[0].y) == [0, 1, 1]
    assert list(figure.data[1].y) == [1, 1]
    assert figure.layout.title.text == "Occupied Chargers Over Time"
    assert figure.layout.yaxis.title.text == "Chargers"
    assert figure.layout.autosize is True

def test_dashboard_scenario_ab_queue_chart_uses_prepared_series_without_recalculation():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        waiting_vehicle_count_by_timestep=[0, 2, 1] + [0] * 93,
        maximum_queue_length=99,
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        waiting_vehicle_count_by_timestep=[0, 1, 0] + [0] * 93,
    )

    figure = create_scenario_ab_queue_figure(
        metrics_a,
        metrics_b,
        scenario_a_label="Heavy-duty",
        scenario_b_label="Workplace Charging",
    )

    assert [trace.name for trace in figure.data] == [
        "Heavy-duty",
        "Workplace Charging",
    ]
    assert list(figure.data[0].x) == get_time_labels()
    assert list(figure.data[1].x) == get_time_labels()
    assert list(figure.data[0].y[:4]) == [0, 2, 1, 0]
    assert list(figure.data[1].y[:4]) == [0, 1, 0, 0]
    assert figure.layout.title.text == "Queue Length Over Time"
    assert figure.layout.yaxis.title.text == "Vehicles"
    assert figure.layout.autosize is True
    assert figure.layout.xaxis.tickmode == "array"
    assert list(figure.layout.xaxis.tickvals) == get_time_labels()[::8]
    assert (
        figure.data[0].hovertemplate
        == "%{y:,.0f} vehicles<extra>%{fullData.name}</extra>"
    )
    assert 99 not in list(figure.data[0].y)

def test_dashboard_scenario_ab_power_quality_chart_preserves_series_lengths():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        overall_pq_risk_score_by_timestep=[30.0, 45.0, 25.0],
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        overall_pq_risk_score_by_timestep=[18.0, 24.0],
    )

    figure = create_scenario_ab_power_quality_figure(
        metrics_a,
        metrics_b,
        scenario_a_label="Heavy-duty",
        scenario_b_label="Workplace Charging",
    )

    assert [trace.name for trace in figure.data] == [
        "Heavy-duty",
        "Workplace Charging",
    ]
    assert list(figure.data[0].x) == ["T1", "T2", "T3"]
    assert list(figure.data[1].x) == ["T1", "T2"]
    assert list(figure.data[0].y) == [30.0, 45.0, 25.0]
    assert list(figure.data[1].y) == [18.0, 24.0]
    assert figure.layout.title.text == "Overall PQ Risk Over Time"
    assert figure.layout.yaxis.title.text == "Overall PQ Risk Score (0-100)"
    assert figure.layout.autosize is True
    assert (
        figure.data[0].hovertemplate
        == "%{y:,.1f} / 100<extra>%{fullData.name}</extra>"
    )

def test_dashboard_scenario_ab_transformer_loading_chart_preserves_series_lengths():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        transformer_loading_percent_by_timestep=[88.0, 95.0, 108.0],
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        transformer_loading_percent_by_timestep=[58.0, 63.0],
    )

    figure = create_scenario_ab_transformer_loading_figure(
        metrics_a,
        metrics_b,
        scenario_a_label="Heavy-duty",
        scenario_b_label="Workplace Charging",
    )

    assert [trace.name for trace in figure.data] == [
        "Heavy-duty",
        "Workplace Charging",
    ]
    assert list(figure.data[0].x) == ["T1", "T2", "T3"]
    assert list(figure.data[1].x) == ["T1", "T2"]
    assert list(figure.data[0].y) == [88.0, 95.0, 108.0]
    assert list(figure.data[1].y) == [58.0, 63.0]
    assert figure.layout.title.text == "Transformer Loading Over Time"
    assert figure.layout.yaxis.title.text == "Transformer Loading (%)"
    assert figure.layout.autosize is True
    assert (
        figure.data[0].hovertemplate
        == "%{y:,.1f} %<extra>%{fullData.name}</extra>"
    )

def test_dashboard_capacity_vs_load_chart_uses_completed_exceedance_status_without_recalculation():
    simulation_result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=120.0,
        installed_charger_capacity_kw=210.0,
        available_site_charging_capacity_kw=120.0,
        requested_load_profile_kw=[210.0, 0.0] + [0.0] * 22,
        delivered_load_profile_kw=[120.0, 0.0] + [0.0] * 22,
    )
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=120.0,
        energy_delivery_sufficient=True,
        peak_load=120.0,
        connection_capacity_exceeded=False,
    )

    figure = create_capacity_vs_load_figure(simulation_result, metrics)

    assert len(figure.data) == 3
    assert all(trace.name != "Requested Load Exceedance" for trace in figure.data)

