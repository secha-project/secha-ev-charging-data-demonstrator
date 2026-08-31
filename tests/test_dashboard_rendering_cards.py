from tests.helpers import *  # noqa: F401,F403
from dashboard.common import KPI_CARD_STYLE

def test_dashboard_renders_generated_insights_as_list_items():
    rendered_items = render_insights(["First insight", "Second insight"])

    visible_text = " ".join(_collect_text(rendered_items))

    assert visible_text == "First insight Second insight"

def test_dashboard_renders_comparison_metrics_as_kpi_cards():
    uncontrolled_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=420.0,
        required_connection_capacity_kw=1200.0,
        peak_transformer_loading_percent=110.0,
        maximum_feeder_loading_percent=104.0,
    )
    smart_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=270.0,
        required_connection_capacity_kw=960.0,
        peak_transformer_loading_percent=86.0,
        maximum_feeder_loading_percent=79.0,
    )
    comparison_metrics = ComparisonMetrics(
        peak_reduction=150.0,
        relative_peak_reduction=37.5,
        capacity_utilization_difference=30.0,
        unmet_energy_difference=0.0,
        required_connection_capacity_difference_kw=240.0,
        average_waiting_time_difference_hours=3.0,
        uncontrolled_average_waiting_time_hours=4.0,
        smart_average_waiting_time_hours=1.0,
        uncontrolled_queue_present_indicator=True,
        smart_queue_present_indicator=False,
        uncontrolled_maximum_queue_length=2,
        smart_maximum_queue_length=0,
        uncontrolled_vehicles_not_started_count=1,
        smart_vehicles_not_started_count=0,
        uncontrolled_vehicles_with_unmet_energy_count=2,
        smart_vehicles_with_unmet_energy_count=0,
        peak_transformer_loading_percent_difference=24.0,
        overall_pq_risk_score_difference=18.0,
        uncontrolled_overall_pq_risk_score=48.0,
        smart_overall_pq_risk_score=30.0,
        uncontrolled_overall_pq_risk_level="moderate",
        smart_overall_pq_risk_level="low",
        uncontrolled_power_quality_warning_count=2,
        smart_power_quality_warning_count=1,
        grid_capacity_status="Constraint reduced",
    )

    rendered_cards = render_comparison_kpi_cards(
        comparison_metrics,
        uncontrolled_metrics,
        smart_metrics,
    )
    visible_text = " ".join(_collect_text(rendered_cards))
    card_rows = [_collect_immediate_child_text(card) for card in rendered_cards]

    assert len(rendered_cards) == 6
    assert card_rows == [
        [
            "Peak Load",
            "↓ 150.0 kW",
            "Uncontrolled - Smart",
            "420.0 kW -> 270.0 kW",
        ],
        [
            "Required Connection Capacity",
            "↓ 240.0 kW",
            "Uncontrolled - Smart",
            "1,200.0 kW -> 960.0 kW",
        ],
        [
            "Peak Transformer Loading",
            "↓ 24.0 percentage points",
            "Uncontrolled - Smart",
            "110.0% -> 86.0%",
        ],
        [
            "Service Impact",
            "Avg. wait ↓ 3.0 h",
            "Average waiting time change",
            "4.0 h -> 1.0 h",
        ],
        [
            "Power Quality Impact",
            "Low risk · 30.0 / 100",
            "Smart Charging overall PQ risk",
            "48.0 -> 30.0",
        ],
        [
            "Grid / Infrastructure Status",
            "Constraint reduced",
            "Planner-facing grid status",
            "86.0% transformer · 79.0% feeder",
        ],
    ]

    assert "Peak Load" in visible_text
    assert "Improvement" not in visible_text
    assert "↓ 150.0 kW" in visible_text
    assert "420.0 kW -> 270.0 kW" in visible_text
    assert "Required Connection Capacity" in visible_text
    assert "↓ 240.0 kW" in visible_text
    assert "1,200.0 kW -> 960.0 kW" in visible_text
    assert "Peak Transformer Loading" in visible_text
    assert "↓ 24.0 percentage points" in visible_text
    assert "110.0% -> 86.0%" in visible_text
    assert "Service Impact" in visible_text
    assert "Avg. wait ↓ 3.0 h" in visible_text
    assert "4.0 h -> 1.0 h" in visible_text
    assert "Power Quality Impact" in visible_text
    assert "Low risk · 30.0 / 100" in visible_text
    assert "48.0 -> 30.0" in visible_text
    assert "Grid / Infrastructure Status" in visible_text
    assert "Constraint reduced" in visible_text
    assert "86.0% transformer · 79.0% feeder" in visible_text
    assert all(card.style.get("boxShadow") for card in rendered_cards)

def test_dashboard_comparison_capacity_kpi_cards_use_completed_metrics_only():
    uncontrolled_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=999.0,
        required_connection_capacity_kw=840.0,
        peak_transformer_loading_percent=88.0,
        maximum_feeder_loading_percent=77.0,
    )
    smart_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=800.0,
        required_connection_capacity_kw=880.0,
        peak_transformer_loading_percent=92.0,
        maximum_feeder_loading_percent=79.0,
    )
    comparison_metrics = ComparisonMetrics(
        peak_reduction=999.0,
        relative_peak_reduction=99.0,
        capacity_utilization_difference=88.0,
        unmet_energy_difference=77.0,
        required_connection_capacity_difference_kw=-40.0,
        peak_transformer_loading_percent_difference=-4.0,
        average_waiting_time_difference_hours=-1.5,
        uncontrolled_average_waiting_time_hours=2.0,
        smart_average_waiting_time_hours=3.5,
        overall_pq_risk_score_difference=0.0,
        uncontrolled_overall_pq_risk_score=18.0,
        smart_overall_pq_risk_score=18.0,
        uncontrolled_overall_pq_risk_level="low",
        smart_overall_pq_risk_level="low",
        uncontrolled_power_quality_warning_count=0,
        smart_power_quality_warning_count=0,
        grid_capacity_status="Constraint worsened",
    )

    rendered_cards = render_comparison_kpi_cards(
        comparison_metrics,
        uncontrolled_metrics,
        smart_metrics,
    )
    visible_text = " ".join(_collect_text(rendered_cards))

    assert "Deterioration" not in visible_text
    assert "↑ 4.0 percentage points" in visible_text
    assert "↑ 40.0 kW" in visible_text
    assert "Avg. wait ↑ 1.5 h" in visible_text
    assert "Low risk · 18.0 / 100" in visible_text
    assert "Constraint worsened" in visible_text
    assert "+40.0 kW" not in visible_text
    assert rendered_cards[1].style.get("boxShadow")

def test_dashboard_renders_charging_performance_comparison_table_from_comparison_metrics():
    comparison_metrics = ComparisonMetrics(
        peak_reduction=0.0,
        relative_peak_reduction=0.0,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
        uncontrolled_peak_occupied_charger_count=5,
        smart_peak_occupied_charger_count=3,
        peak_occupied_charger_count_difference=2,
        uncontrolled_queue_present_indicator=True,
        smart_queue_present_indicator=False,
        uncontrolled_maximum_queue_length=4,
        smart_maximum_queue_length=1,
        maximum_queue_length_difference=3,
        uncontrolled_average_waiting_time_hours=None,
        smart_average_waiting_time_hours=0.25,
        average_waiting_time_difference_hours=None,
    )

    table = render_charging_performance_comparison_table(comparison_metrics)
    visible_text = " ".join(_collect_text(table))

    assert "Peak occupied chargers" in visible_text
    assert "Queue present" in visible_text
    assert "Maximum queue length" in visible_text
    assert "Average waiting time (h)" in visible_text
    assert "Present" in visible_text
    assert "Not present" in visible_text
    assert visible_text.count("Not available") >= 2

def test_dashboard_hides_queue_rows_without_modeled_queue_pressure():
    comparison_metrics = ComparisonMetrics(
        peak_reduction=0.0,
        relative_peak_reduction=0.0,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
        uncontrolled_peak_occupied_charger_count=5,
        smart_peak_occupied_charger_count=4,
        peak_occupied_charger_count_difference=1,
        uncontrolled_queue_present_indicator=False,
        smart_queue_present_indicator=False,
        uncontrolled_maximum_queue_length=0,
        smart_maximum_queue_length=0,
        maximum_queue_length_difference=0,
        uncontrolled_average_waiting_time_hours=None,
        smart_average_waiting_time_hours=None,
        average_waiting_time_difference_hours=None,
    )

    table = render_charging_performance_comparison_table(comparison_metrics)
    visible_text = " ".join(_collect_text(table))

    assert "Peak occupied chargers" in visible_text
    assert "Queue present" not in visible_text
    assert "Maximum queue length" not in visible_text
    assert "Average waiting time (h)" not in visible_text

def test_dashboard_replaces_queue_chart_with_status_message_without_modeled_queue_pressure():
    comparison_metrics = ComparisonMetrics(
        peak_reduction=0.0,
        relative_peak_reduction=0.0,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
        uncontrolled_peak_occupied_charger_count=5,
        smart_peak_occupied_charger_count=4,
        peak_occupied_charger_count_difference=1,
        uncontrolled_queue_present_indicator=False,
        smart_queue_present_indicator=False,
        uncontrolled_maximum_queue_length=0,
        smart_maximum_queue_length=0,
        maximum_queue_length_difference=0,
        uncontrolled_average_waiting_time_hours=None,
        smart_average_waiting_time_hours=None,
        average_waiting_time_difference_hours=None,
    )

    chart_style, status_children, status_style = _smart_charging_queue_evidence_state(
        comparison_metrics
    )
    visible_text = " ".join(_collect_text(status_children))

    assert chart_style == {"display": "none"}
    assert status_style == {}
    assert "No queues formed during the simulation." in visible_text

def test_dashboard_keeps_queue_chart_visible_when_modeled_queue_pressure_exists():
    comparison_metrics = ComparisonMetrics(
        peak_reduction=0.0,
        relative_peak_reduction=0.0,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
        uncontrolled_peak_occupied_charger_count=5,
        smart_peak_occupied_charger_count=4,
        peak_occupied_charger_count_difference=1,
        uncontrolled_queue_present_indicator=True,
        smart_queue_present_indicator=False,
        uncontrolled_maximum_queue_length=3,
        smart_maximum_queue_length=0,
        maximum_queue_length_difference=3,
        uncontrolled_average_waiting_time_hours=1.0,
        smart_average_waiting_time_hours=0.25,
        average_waiting_time_difference_hours=0.75,
    )

    chart_style, status_children, status_style = _smart_charging_queue_evidence_state(
        comparison_metrics
    )

    assert chart_style == {}
    assert status_children == ""
    assert status_style == {"display": "none"}

def test_dashboard_renders_power_quality_comparison_table_from_comparison_metrics():
    comparison_metrics = ComparisonMetrics(
        peak_reduction=0.0,
        relative_peak_reduction=0.0,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
        uncontrolled_overall_pq_risk_score=58.0,
        smart_overall_pq_risk_score=26.0,
        overall_pq_risk_score_difference=32.0,
        uncontrolled_overall_pq_risk_level="high",
        smart_overall_pq_risk_level="low",
        uncontrolled_power_quality_warning_count=3,
        smart_power_quality_warning_count=1,
        power_quality_warning_count_difference=2,
    )

    table = render_power_quality_comparison_table(comparison_metrics)
    visible_text = " ".join(_collect_text(table))
    status_children, status_style = _smart_charging_power_quality_status_state(
        comparison_metrics
    )

    assert "Overall PQ risk score" in visible_text
    assert "Overall PQ risk level" in visible_text
    assert "PQ warning count" in visible_text
    assert "+32.0 points" in visible_text
    assert "+2 warnings" in visible_text
    assert "Not applicable" in visible_text
    assert status_children == ""
    assert status_style == {"display": "none"}

def test_dashboard_hides_unchanged_power_quality_level_row_and_shows_status_message():
    comparison_metrics = ComparisonMetrics(
        peak_reduction=0.0,
        relative_peak_reduction=0.0,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
        uncontrolled_overall_pq_risk_score=12.0,
        smart_overall_pq_risk_score=8.0,
        overall_pq_risk_score_difference=4.0,
        uncontrolled_overall_pq_risk_level="low",
        smart_overall_pq_risk_level="low",
        uncontrolled_power_quality_warning_count=0,
        smart_power_quality_warning_count=0,
        power_quality_warning_count_difference=0,
    )

    table = render_power_quality_comparison_table(comparison_metrics)
    visible_text = " ".join(_collect_text(table))
    status_children, status_style = _smart_charging_power_quality_status_state(
        comparison_metrics
    )
    status_text = " ".join(_collect_text(status_children))

    assert "Overall PQ risk score" in visible_text
    assert "PQ warning count" in visible_text
    assert "Overall PQ risk level" not in visible_text
    assert status_style == {}
    assert "Modeled PQ risk remains low for both strategies." in status_text

def test_dashboard_reference_smart_charging_outputs_keep_grid_values_available():
    scenario = _build_reference_grid_loading_scenario(
        vehicles=4,
        charger_count=4,
        grid_capacity=400.0,
        transformer_capacity_kw=250.0,
        transformer_other_load_kw=20.0,
        feeder_count=2,
        feeder_capacity_kw=120.0,
        feeder_base_load_kw=10.0,
        charging_window_end=time(9, 0),
    )

    uncontrolled_result, smart_result = simulate_strategy_comparison(scenario)
    uncontrolled_metrics = calculate_metrics(uncontrolled_result, scenario)
    smart_metrics = calculate_metrics(smart_result, scenario)
    comparison_metrics = calculate_comparison_metrics(
        uncontrolled_metrics,
        smart_metrics,
    )

    cards = render_comparison_kpi_cards(
        comparison_metrics,
        uncontrolled_metrics,
        smart_metrics,
    )
    details_table = render_detailed_comparison_table(
        uncontrolled_metrics,
        smart_metrics,
    )
    card_text = " ".join(_collect_text(cards))
    detail_text = " ".join(_collect_text(details_table))

    assert "Peak Load" in card_text
    assert "↓ 300.0 kW" in card_text
    assert "400.0 kW -> 100.0 kW" in card_text
    assert "Required Connection Capacity" in card_text
    assert "Peak Transformer Loading" in card_text
    assert "↓ 120.0 percentage points" in card_text
    assert "168.0% -> 48.0%" in card_text
    assert "Grid / Infrastructure Status" in card_text
    assert "50.0% feeder" in card_text
    assert "Recommended connection capacity (kW)" in detail_text
    assert "Connection capacity adequacy" in detail_text
    assert "Capacity recommendation basis" in detail_text
    assert "Transformer overload" in detail_text
    assert "Feeder overload" in detail_text

def test_dashboard_comparison_availability_outputs_render_safe_legacy_state():
    comparison_metrics = ComparisonMetrics(
        peak_reduction=0.0,
        relative_peak_reduction=0.0,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
        uncontrolled_required_charger_count=None,
        smart_required_charger_count=None,
        required_charger_count_difference=None,
        uncontrolled_additional_chargers_required=None,
        smart_additional_chargers_required=None,
        additional_chargers_required_difference=None,
        uncontrolled_average_waiting_time_hours=None,
        smart_average_waiting_time_hours=None,
        average_waiting_time_difference_hours=None,
        uncontrolled_maximum_waiting_time_hours=None,
        smart_maximum_waiting_time_hours=None,
        maximum_waiting_time_difference_hours=None,
        uncontrolled_occupied_charger_count_by_timestep=[],
        smart_occupied_charger_count_by_timestep=[],
        uncontrolled_waiting_vehicle_count_by_timestep=[],
        smart_waiting_vehicle_count_by_timestep=[],
    )
    uncontrolled_metrics = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
    )
    smart_metrics = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
    )

    charging_performance_table = render_charging_performance_comparison_table(
        comparison_metrics
    )
    technical_details_table = render_detailed_comparison_table(
        uncontrolled_metrics,
        smart_metrics,
    )
    occupancy_figure = create_comparison_occupancy_figure(comparison_metrics)
    queue_figure = create_comparison_queue_figure(comparison_metrics)
    pq_figure = create_comparison_power_quality_figure(comparison_metrics)
    visible_text = " ".join(
        _collect_text(charging_performance_table)
        + _collect_text(technical_details_table)
    )

    assert "Peak occupied chargers" in visible_text
    assert "Primary bottleneck" not in visible_text
    assert "Infrastructure recommendation unchanged" not in visible_text
    assert "Required charger count" not in visible_text
    assert len(occupancy_figure.data) == 0
    assert occupancy_figure.layout.annotations[0].text == (
        "Occupied-charger comparison series unavailable for this result."
    )
    assert len(queue_figure.data) == 0
    assert queue_figure.layout.annotations[0].text == (
        "Queue-length comparison series unavailable for this result."
    )
    assert len(pq_figure.data) == 0
    assert pq_figure.layout.annotations[0].text == (
        "Overall PQ risk comparison series unavailable for this result."
    )


@pytest.mark.parametrize(
    (
        "peak_transformer_loading_percent_difference",
        "required_connection_capacity_difference_kw",
        "average_waiting_time_difference_hours",
        "overall_pq_risk_score_difference",
        "expected_transformer_difference",
        "expected_capacity_change",
        "expected_service_value",
        "expected_pq_score",
    ),
    [
        pytest.param(
            24.0,
            120.0,
            3.0,
            18.0,
            "↓ 24.0 percentage points",
            "↓ 120.0 kW",
            "Avg. wait ↓ 3.0 h",
            "Low risk · 4.0 / 100",
            id="positive-values",
        ),
        pytest.param(
            -4.0,
            -40.0,
            -1.5,
            -6.0,
            "↑ 4.0 percentage points",
            "↑ 40.0 kW",
            "Avg. wait ↑ 1.5 h",
            "Low risk · 28.0 / 100",
            id="negative-differences",
        ),
        pytest.param(
            0.0,
            0.0,
            0.0,
            0.0,
            "No change",
            "No change",
            "Service unchanged",
            "Low risk · 22.0 / 100",
            id="zero-values",
        ),
    ],
)

def test_dashboard_comparison_capacity_kpi_cards_format_signed_values(
    peak_transformer_loading_percent_difference,
    required_connection_capacity_difference_kw,
    average_waiting_time_difference_hours,
    overall_pq_risk_score_difference,
    expected_transformer_difference,
    expected_capacity_change,
    expected_service_value,
    expected_pq_score,
):
    uncontrolled_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=450.0,
        required_connection_capacity_kw=900.0,
        peak_transformer_loading_percent=90.0,
        maximum_feeder_loading_percent=82.0,
    )
    smart_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=300.0,
        required_connection_capacity_kw=(
            uncontrolled_metrics.required_connection_capacity_kw
            - required_connection_capacity_difference_kw
        ),
        peak_transformer_loading_percent=(
            uncontrolled_metrics.peak_transformer_loading_percent
            - peak_transformer_loading_percent_difference
        ),
        maximum_feeder_loading_percent=70.0,
    )
    comparison_metrics = ComparisonMetrics(
        peak_reduction=150.0,
        relative_peak_reduction=37.5,
        capacity_utilization_difference=30.0,
        unmet_energy_difference=0.0,
        required_connection_capacity_difference_kw=(
            required_connection_capacity_difference_kw
        ),
        peak_transformer_loading_percent_difference=(
            peak_transformer_loading_percent_difference
        ),
        average_waiting_time_difference_hours=(
            average_waiting_time_difference_hours
        ),
        uncontrolled_average_waiting_time_hours=2.0,
        smart_average_waiting_time_hours=(
            2.0 - average_waiting_time_difference_hours
        ),
        overall_pq_risk_score_difference=overall_pq_risk_score_difference,
        uncontrolled_overall_pq_risk_score=22.0,
        smart_overall_pq_risk_score=22.0 - overall_pq_risk_score_difference,
        uncontrolled_overall_pq_risk_level="moderate",
        smart_overall_pq_risk_level="low",
        uncontrolled_power_quality_warning_count=1,
        smart_power_quality_warning_count=0,
        grid_capacity_status="Constraint unchanged",
    )

    visible_text = " ".join(
        _collect_text(
            render_comparison_kpi_cards(
                comparison_metrics,
                uncontrolled_metrics,
                smart_metrics,
            )
        )
    )

    assert expected_transformer_difference in visible_text
    assert expected_capacity_change in visible_text
    assert expected_service_value in visible_text
    assert expected_pq_score in visible_text

def test_dashboard_service_impact_card_prefers_prepared_service_summary_when_available():
    uncontrolled_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        peak_load=450.0,
        required_connection_capacity_kw=900.0,
        peak_transformer_loading_percent=90.0,
        maximum_feeder_loading_percent=82.0,
    )
    smart_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        peak_load=300.0,
        required_connection_capacity_kw=780.0,
        peak_transformer_loading_percent=66.0,
        maximum_feeder_loading_percent=70.0,
    )
    comparison_metrics = ComparisonMetrics(
        peak_reduction=150.0,
        relative_peak_reduction=37.5,
        capacity_utilization_difference=30.0,
        unmet_energy_difference=0.0,
        required_connection_capacity_difference_kw=120.0,
        peak_transformer_loading_percent_difference=24.0,
        overall_pq_risk_score_difference=18.0,
        uncontrolled_overall_pq_risk_score=22.0,
        smart_overall_pq_risk_score=4.0,
        uncontrolled_overall_pq_risk_level="moderate",
        smart_overall_pq_risk_level="low",
        uncontrolled_power_quality_warning_count=1,
        smart_power_quality_warning_count=0,
        grid_capacity_status="Constraint unchanged",
        service_impact_summary="Service trade-off changed.",
        uncontrolled_queue_present_indicator=True,
        smart_queue_present_indicator=False,
        uncontrolled_average_waiting_time_hours=1.0,
        smart_average_waiting_time_hours=0.25,
        uncontrolled_vehicles_not_started_count=0,
        smart_vehicles_not_started_count=1,
        uncontrolled_vehicles_with_unmet_energy_count=1,
        smart_vehicles_with_unmet_energy_count=1,
    )

    visible_text = " ".join(
        _collect_text(
            render_comparison_kpi_cards(
                comparison_metrics,
                uncontrolled_metrics,
                smart_metrics,
            )
        )
    )

    assert "Service trade-off changed." in visible_text
    assert "1.0 h -> 0.2 h" in visible_text
    assert "Deterioration" not in visible_text
    assert "Not started 0 -> 1; Unmet vehicles 1 -> 1" not in visible_text

def test_dashboard_service_impact_card_renders_summary_trade_off_without_fabricating_zero():
    uncontrolled_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        required_connection_capacity_kw=200.0,
        peak_transformer_loading_percent=75.0,
        maximum_feeder_loading_percent=60.0,
    )
    smart_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        required_connection_capacity_kw=200.0,
        peak_transformer_loading_percent=75.0,
        maximum_feeder_loading_percent=60.0,
    )
    comparison_metrics = ComparisonMetrics(
        peak_reduction=0.0,
        relative_peak_reduction=0.0,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
        average_waiting_time_difference_hours=None,
        uncontrolled_average_waiting_time_hours=None,
        smart_average_waiting_time_hours=None,
        uncontrolled_queue_present_indicator=False,
        smart_queue_present_indicator=True,
        uncontrolled_maximum_queue_length=0,
        smart_maximum_queue_length=2,
        maximum_queue_length_difference=-2,
        uncontrolled_vehicles_not_started_count=0,
        smart_vehicles_not_started_count=1,
        vehicles_not_started_count_difference=-1,
        uncontrolled_vehicles_with_unmet_energy_count=0,
        smart_vehicles_with_unmet_energy_count=0,
        vehicles_with_unmet_energy_count_difference=0,
        overall_pq_risk_score_difference=0.0,
        uncontrolled_overall_pq_risk_score=18.0,
        smart_overall_pq_risk_score=18.0,
        uncontrolled_overall_pq_risk_level="low",
        smart_overall_pq_risk_level="low",
        uncontrolled_power_quality_warning_count=0,
        smart_power_quality_warning_count=0,
        grid_capacity_status="Constraint unchanged",
    )

    rendered_cards = render_comparison_kpi_cards(
        comparison_metrics,
        uncontrolled_metrics,
        smart_metrics,
    )
    service_card_rows = _collect_immediate_child_text(rendered_cards[3])

    assert service_card_rows == [
        "Service Impact",
        "Queue introduced",
        "Planner-facing service outcome",
        "N/A -> N/A",
    ]
    assert "0.0 h" not in " ".join(service_card_rows)


@pytest.mark.parametrize(
    ("comparison_metrics", "expected_outcome", "expected_main", "expected_context"),
    [
        pytest.param(
            ComparisonMetrics(
                peak_reduction=0.0,
                relative_peak_reduction=0.0,
                capacity_utilization_difference=0.0,
                unmet_energy_difference=0.0,
                overall_pq_risk_score_difference=-0.0,
                uncontrolled_overall_pq_risk_score=20.0,
                smart_overall_pq_risk_score=20.0,
                uncontrolled_overall_pq_risk_level="moderate",
                smart_overall_pq_risk_level="moderate",
                uncontrolled_power_quality_warning_count=1,
                smart_power_quality_warning_count=1,
            ),
            "No change",
            "Moderate risk · 20.0 / 100",
            "20.0 -> 20.0",
            id="unchanged",
        ),
        pytest.param(
            ComparisonMetrics(
                peak_reduction=0.0,
                relative_peak_reduction=0.0,
                capacity_utilization_difference=0.0,
                unmet_energy_difference=0.0,
                overall_pq_risk_score_difference=-12.0,
                uncontrolled_overall_pq_risk_score=20.0,
                smart_overall_pq_risk_score=32.0,
                uncontrolled_overall_pq_risk_level="low",
                smart_overall_pq_risk_level="moderate",
                uncontrolled_power_quality_warning_count=1,
                smart_power_quality_warning_count=2,
            ),
            "Deterioration",
            "Moderate risk · 32.0 / 100",
            "20.0 -> 32.0",
            id="worsening",
        ),
    ],
)

def test_dashboard_power_quality_card_renders_expected_semantics(
    comparison_metrics,
    expected_outcome,
    expected_main,
    expected_context,
):
    uncontrolled_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        required_connection_capacity_kw=200.0,
        peak_transformer_loading_percent=75.0,
        maximum_feeder_loading_percent=60.0,
    )
    smart_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        required_connection_capacity_kw=200.0,
        peak_transformer_loading_percent=75.0,
        maximum_feeder_loading_percent=60.0,
    )

    rendered_cards = render_comparison_kpi_cards(
        comparison_metrics,
        uncontrolled_metrics,
        smart_metrics,
    )
    power_quality_card_rows = _collect_immediate_child_text(rendered_cards[4])

    assert power_quality_card_rows[0] == "Power Quality Impact"
    assert power_quality_card_rows[1] == expected_main
    assert power_quality_card_rows[2] == "Smart Charging overall PQ risk"
    assert power_quality_card_rows[3] == expected_context
    if expected_outcome == "No change":
        assert "0.0 points" not in " ".join(power_quality_card_rows)
        assert "boxShadow" not in rendered_cards[4].style
    else:
        assert rendered_cards[4].style.get("boxShadow")


@pytest.mark.parametrize(
        ("grid_capacity_status", "expected_outcome"),
        [
            pytest.param("Constraint resolved", "Improvement", id="resolved"),
            pytest.param("Constraint unchanged", "No change", id="unchanged"),
            pytest.param("Constraint worsened", "Deterioration", id="worsened"),
        ],
    )

def test_dashboard_grid_status_card_renders_expected_outcome_label(
    grid_capacity_status,
    expected_outcome,
):
    uncontrolled_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        required_connection_capacity_kw=200.0,
        peak_transformer_loading_percent=75.0,
        maximum_feeder_loading_percent=60.0,
    )
    smart_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        required_connection_capacity_kw=200.0,
        peak_transformer_loading_percent=75.0,
        maximum_feeder_loading_percent=60.0,
    )
    comparison_metrics = ComparisonMetrics(
        peak_reduction=0.0,
        relative_peak_reduction=0.0,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
        overall_pq_risk_score_difference=0.0,
        uncontrolled_overall_pq_risk_score=18.0,
        smart_overall_pq_risk_score=18.0,
        uncontrolled_overall_pq_risk_level="low",
        smart_overall_pq_risk_level="low",
        uncontrolled_power_quality_warning_count=0,
        smart_power_quality_warning_count=0,
        grid_capacity_status=grid_capacity_status,
    )

    rendered_cards = render_comparison_kpi_cards(
        comparison_metrics,
        uncontrolled_metrics,
        smart_metrics,
    )
    grid_card_rows = _collect_immediate_child_text(rendered_cards[5])

    assert grid_card_rows[0] == "Grid / Infrastructure Status"
    assert grid_card_rows[1] == grid_capacity_status
    assert grid_card_rows[2] == "Planner-facing grid status"
    assert grid_card_rows[3] == "Adequate · 75.0% transformer · 60.0% feeder"
    if expected_outcome == "No change":
        assert "boxShadow" not in rendered_cards[5].style
    else:
        assert rendered_cards[5].style.get("boxShadow")

def test_dashboard_renders_capacity_planning_kpi_cards_from_metrics_and_result():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=321.0,
        required_connection_capacity_kw=654.0,
        recommended_connection_capacity_kw=777.0,
        planning_margin_percent=15.0,
        peak_capacity_margin_kw=-80.0,
        peak_capacity_margin_percent=-8.0,
        connection_capacity_exceeded=True,
    )
    simulation_result = SimulationResult(
        daily_energy_demand=1000.0,
        configured_connection_capacity_kw=900.0,
        installed_charger_capacity_kw=1000.0,
        available_site_charging_capacity_kw=500.0,
        requested_load_profile_kw=[1000.0],
        delivered_load_profile_kw=[50.0],
    )

    rendered_cards = render_capacity_planning_kpi_cards(metrics, simulation_result)
    visible_text = " ".join(_collect_text(rendered_cards))

    assert "Simulated Peak Load" in visible_text
    assert "321.0 kW" in visible_text
    assert "Required Connection Capacity" in visible_text
    assert "654.0 kW" in visible_text
    assert "Recommended Connection Capacity" in visible_text
    assert "777.0 kW" in visible_text
    assert "Capacity Shortfall" in visible_text
    assert "80.0 kW" in visible_text
    assert "Planning margin" not in visible_text
    assert "Peak capacity margin:" not in visible_text
    assert "Margin percent:" not in visible_text
    assert "Configured Connection Capacity" not in visible_text
    assert "Connection Capacity Exceeded" not in visible_text
    assert "Exceeded" not in visible_text

def test_dashboard_renders_charger_availability_kpi_cards_from_metrics():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        average_charger_utilization_percent=42.5,
        peak_charger_utilization_percent=88.0,
        average_occupied_charger_count=3.5,
        peak_occupied_charger_count=5,
        maximum_queue_length=2,
        average_waiting_time_hours=0.75,
        vehicles_not_started_count=1,
        required_charger_count=6,
    )

    visible_text = " ".join(
        _collect_text(render_charger_availability_kpi_cards(metrics))
    )

    assert "Peak Charger Utilization" in visible_text
    assert "88.0%" in visible_text
    assert "Peak Occupied Chargers" in visible_text
    assert "5 chargers" in visible_text
    assert "Maximum Queue Length" in visible_text
    assert "2 vehicles" in visible_text
    assert "Vehicles Not Started" in visible_text
    assert "1 vehicles" in visible_text
    assert "Highest modeled power saturation" not in visible_text
    assert "Highest modeled charger-slot use" not in visible_text
    assert "Strongest modeled waiting-pressure signal" not in visible_text
    assert "Demand left unserved by charger availability" not in visible_text
    assert "Average Charger Utilization" not in visible_text
    assert "42.5%" not in visible_text
    assert "Average Occupied Chargers" not in visible_text
    assert "3.5 chargers" not in visible_text
    assert "Average Waiting Time" not in visible_text
    assert "0.8 h" not in visible_text
    assert "Required Charger Count" not in visible_text

def test_dashboard_infrastructure_kpi_cards_share_standard_card_styling():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=321.0,
        required_connection_capacity_kw=654.0,
        recommended_connection_capacity_kw=777.0,
        peak_capacity_margin_kw=-80.0,
        peak_charger_utilization_percent=88.0,
        peak_occupied_charger_count=5,
        maximum_queue_length=2,
        vehicles_not_started_count=1,
    )
    simulation_result = SimulationResult(
        daily_energy_demand=1000.0,
        configured_connection_capacity_kw=900.0,
        installed_charger_capacity_kw=1000.0,
        available_site_charging_capacity_kw=500.0,
        requested_load_profile_kw=[1000.0],
        delivered_load_profile_kw=[50.0],
    )

    cards = [
        *render_capacity_planning_kpi_cards(metrics, simulation_result),
        *render_charger_availability_kpi_cards(metrics),
    ]

    for card in cards:
        assert card.style["border"] == KPI_CARD_STYLE["border"]
        assert card.style["backgroundColor"] == KPI_CARD_STYLE["backgroundColor"]
        assert "borderColor" not in card.style
        assert "boxShadow" not in card.style

def test_dashboard_infrastructure_summary_renders_feasible_scenario():
    metrics = Metrics(
        total_daily_energy=500.0,
        available_capacity=400.0,
        energy_delivery_sufficient=True,
        connection_capacity_exceeded=False,
        primary_constraint_reason="none",
        required_charger_count=4,
        additional_chargers_required=0,
        power_quality_warning_count=0,
        transformer_overload_indicator=False,
        feeder_overload_indicator=False,
        transformer_thermal_risk_level="low",
        highest_feeder_thermal_risk_level="low",
        overall_pq_risk_level="low",
    )

    visible_text = " ".join(
        _collect_text(render_infrastructure_summary(metrics, default_scenario))
    )

    assert "ADEQUATE" in visible_text
    assert "Decision Summary:" in visible_text
    assert "Infrastructure is adequate for the modeled service rule." in visible_text
    assert "Constraint Diagnosis:" in visible_text
    assert (
        "No dominant infrastructure bottleneck is indicated under current assumptions."
        in visible_text
    )
    assert "Planning Impact:" in visible_text
    assert (
        "The scenario does not currently create clear infrastructure expansion pressure."
        in visible_text
    )
    assert "Recommended Planning Focus:" in visible_text
    assert (
        "Maintain the baseline and test sensitivity to higher demand or tighter service expectations."
        in visible_text
    )
    assert "Primary bottleneck:" not in visible_text
    assert "Recommended action:" not in visible_text
    assert "Chargers:" not in visible_text
    assert "Waiting target:" not in visible_text

def test_dashboard_infrastructure_summary_renders_charger_limited_scenario():
    metrics = Metrics(
        total_daily_energy=600.0,
        available_capacity=300.0,
        energy_delivery_sufficient=False,
        connection_capacity_exceeded=False,
        vehicles_not_started_count=1,
        vehicles_with_unmet_energy_count=1,
        primary_constraint_reason="charger_availability",
        required_charger_count=6,
        additional_chargers_required=2,
        power_quality_warning_count=0,
        transformer_overload_indicator=False,
        feeder_overload_indicator=False,
        transformer_thermal_risk_level="low",
        highest_feeder_thermal_risk_level="low",
        overall_pq_risk_level="low",
    )

    visible_text = " ".join(
        _collect_text(render_infrastructure_summary(metrics, default_scenario))
    )

    assert "CONSTRAINED" in visible_text
    assert (
        "Infrastructure is constrained under the current scenario." in visible_text
    )
    assert (
        "Charger availability is the dominant modeled bottleneck." in visible_text
    )
    assert (
        "Queueing pressure is likely to affect service performance during the charging-allowed window."
        in visible_text
    )
    assert (
        "Prioritize charger provision before reviewing larger connection-capacity changes."
        in visible_text
    )
    assert "Required:" not in visible_text
    assert "6 chargers" not in visible_text

def test_dashboard_infrastructure_summary_treats_brief_waiting_as_sufficient():
    metrics = Metrics(
        total_daily_energy=40.0,
        available_capacity=50.0,
        energy_delivery_sufficient=True,
        connection_capacity_exceeded=False,
        queue_present_indicator=True,
        maximum_waiting_time_hours=0.5,
        vehicles_waiting_count=1,
        vehicles_not_started_count=0,
        vehicles_with_unmet_energy_count=0,
        primary_constraint_reason="charger_availability",
        required_charger_count=1,
        additional_chargers_required=0,
        power_quality_warning_count=0,
        transformer_overload_indicator=False,
        feeder_overload_indicator=False,
        transformer_thermal_risk_level="low",
        highest_feeder_thermal_risk_level="low",
        overall_pq_risk_level="low",
    )

    visible_text = " ".join(
        _collect_text(render_infrastructure_summary(metrics, default_scenario))
    )

    assert "ADEQUATE" in visible_text
    assert (
        "Infrastructure is adequate for the modeled service rule."
        in visible_text
    )
    assert (
        "No dominant infrastructure bottleneck is indicated under current assumptions."
        in visible_text
    )
    assert (
        "The scenario does not currently create clear infrastructure expansion pressure."
        in visible_text
    )
    assert (
        "Maintain the baseline and test sensitivity to higher demand or tighter service expectations."
        in visible_text
    )

def test_dashboard_infrastructure_summary_renders_charger_power_limited_scenario():
    metrics = Metrics(
        total_daily_energy=600.0,
        available_capacity=300.0,
        energy_delivery_sufficient=False,
        connection_capacity_exceeded=False,
        vehicles_with_unmet_energy_count=1,
        primary_constraint_reason="charger_power",
        required_charger_count=None,
        additional_chargers_required=None,
        power_quality_warning_count=0,
        transformer_overload_indicator=False,
        feeder_overload_indicator=False,
        transformer_thermal_risk_level="low",
        highest_feeder_thermal_risk_level="low",
        overall_pq_risk_level="low",
    )

    visible_text = " ".join(
        _collect_text(render_infrastructure_summary(metrics, default_scenario))
    )

    assert "CONSTRAINED" in visible_text
    assert (
        "Infrastructure is constrained by charger-power limits." in visible_text
    )
    assert "Charger power is the dominant modeled bottleneck." in visible_text
    assert (
        "Increasing charger count alone is unlikely to resolve the modeled service limitation."
        in visible_text
    )
    assert "Review charger power sizing before expanding charger count." in (
        visible_text
    )

def test_dashboard_infrastructure_summary_renders_grid_capacity_limited_scenario():
    metrics = Metrics(
        total_daily_energy=600.0,
        available_capacity=250.0,
        energy_delivery_sufficient=False,
        connection_capacity_exceeded=True,
        vehicles_with_unmet_energy_count=1,
        primary_constraint_reason="grid_connection_capacity",
        required_charger_count=None,
        additional_chargers_required=None,
        power_quality_warning_count=0,
        transformer_overload_indicator=False,
        feeder_overload_indicator=False,
        transformer_thermal_risk_level="moderate",
        highest_feeder_thermal_risk_level="low",
        overall_pq_risk_level="low",
    )

    visible_text = " ".join(
        _collect_text(render_infrastructure_summary(metrics, default_scenario))
    )

    assert "CONSTRAINED" in visible_text
    assert (
        "Infrastructure is constrained by connection-capacity pressure."
        in visible_text
    )
    assert (
        "Grid connection capacity is the dominant modeled bottleneck."
        in visible_text
    )
    assert (
        "Additional chargers alone are unlikely to resolve the modeled service limitation."
        in visible_text
    )
    assert (
        "Review connection-capacity sizing before expanding charger count."
        in visible_text
    )

def test_dashboard_infrastructure_summary_renders_mixed_constraint_scenario():
    metrics = Metrics(
        total_daily_energy=700.0,
        available_capacity=250.0,
        energy_delivery_sufficient=False,
        connection_capacity_exceeded=True,
        vehicles_not_started_count=1,
        vehicles_with_unmet_energy_count=2,
        primary_constraint_reason="mixed",
        required_charger_count=None,
        additional_chargers_required=None,
        power_quality_warning_count=2,
        transformer_overload_indicator=True,
        feeder_overload_indicator=False,
        transformer_thermal_risk_level="high",
        highest_feeder_thermal_risk_level="moderate",
        overall_pq_risk_level="high",
    )

    visible_text = " ".join(
        _collect_text(render_infrastructure_summary(metrics, default_scenario))
    )

    assert "CONSTRAINED" in visible_text
    assert (
        "Infrastructure is constrained by multiple interacting limits."
        in visible_text
    )
    assert (
        "No single infrastructure change resolves the dominant modeled pressure."
        in visible_text
    )
    assert (
        "Incremental investment in only one area may leave the scenario materially constrained."
        in visible_text
    )
    assert (
        "Review charger count, charger power, and connection-capacity assumptions together."
        in visible_text
    )

def test_dashboard_renders_grid_loading_kpi_cards_from_metrics():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        average_transformer_loading_percent=72.5,
        peak_transformer_loading_percent=108.0,
        transformer_overload_duration_hours=1.5,
        transformer_maximum_overload_kw=18.0,
        maximum_feeder_loading_percent=96.0,
        overloaded_feeder_count=2,
    )

    visible_text = " ".join(_collect_text(render_grid_loading_kpi_cards(metrics)))

    assert "Average Transformer Loading" not in visible_text
    assert "Peak Transformer Loading" in visible_text
    assert "108.0%" in visible_text
    assert "Transformer Overload Duration" in visible_text
    assert "1.5 h" in visible_text
    assert "Maximum Transformer Overload" in visible_text
    assert "18.0 kW" in visible_text
    assert "Maximum Feeder Loading" in visible_text
    assert "96.0%" in visible_text
    assert "Overloaded Feeders" in visible_text
    assert "2 feeders" in visible_text

def test_dashboard_renders_grid_loading_status_from_metrics():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        transformer_overload_indicator=True,
        transformer_thermal_risk_level="high",
        feeder_overload_indicator=False,
        highest_feeder_thermal_risk_level="moderate",
    )

    visible_text = " ".join(_collect_text(render_grid_loading_status(metrics)))

    assert "Grid stress indicated" in visible_text
    assert "Modeled transformer or feeder stress is indicated" in visible_text
    assert "transformer chart" in visible_text
    assert "feeder loading section" in visible_text
    assert "Transformer overload:" not in visible_text
    assert "Highest feeder thermal risk:" not in visible_text
    assert "500.0 kW" not in visible_text
    assert "1000.0 kWh" not in visible_text

def test_dashboard_renders_power_quality_kpi_cards_from_metrics():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_harmonic_risk_score=68.5,
        harmonic_risk_duration_hours=2.5,
        peak_current_imbalance_percent=18.0,
        imbalance_duration_hours=0.5,
        overall_pq_risk_level="moderate",
        power_quality_warning_count=2,
    )

    visible_text = " ".join(_collect_text(render_power_quality_kpi_cards(metrics)))

    assert "Overall PQ Risk" in visible_text
    assert "Moderate" in visible_text
    assert "PQ Warnings" in visible_text
    assert "2 warnings" in visible_text
    assert "Peak Harmonic Risk" in visible_text
    assert "68.5 / 100" in visible_text
    assert "Harmonic Risk Duration" in visible_text
    assert "2.5 h" in visible_text
    assert "Peak Current Imbalance" in visible_text
    assert "18.0%" in visible_text
    assert "Current Imbalance Duration" in visible_text
    assert "0.5 h" in visible_text

def test_dashboard_power_quality_kpi_cards_use_metrics_values_without_recalculation():
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=80.0,
        energy_delivery_sufficient=False,
        peak_harmonic_risk_score=44.4,
        harmonic_risk_duration_hours=1.25,
        peak_current_imbalance_percent=27.5,
        imbalance_duration_hours=0.75,
        overall_pq_risk_level="high",
        power_quality_warning_count=3,
    )

    visible_text = " ".join(_collect_text(render_power_quality_kpi_cards(metrics)))

    assert "44.4 / 100" in visible_text
    assert "1.2 h" in visible_text
    assert "27.5%" in visible_text
    assert "3 warnings" in visible_text
    assert "80.0 kW" not in visible_text
    assert "100.0 kWh" not in visible_text

def test_dashboard_renders_power_quality_status_from_metrics_only():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        harmonic_risk_level="high",
        current_imbalance_risk_level="moderate",
        overall_pq_risk_level="high",
        overall_pq_risk_score=66.0,
        overall_pq_warning_indicator=True,
        power_quality_warning_count=3,
        harmonic_risk_score_by_timestep=[55.0, 66.0, 40.0]
        + [0.0] * (len(get_time_labels()) - 3),
        current_imbalance_percent_by_timestep=[18.0, 28.0, 12.0]
        + [0.0] * (len(get_time_labels()) - 3),
        overall_pq_risk_score_by_timestep=[42.0, 66.0, 33.0]
        + [0.0] * (len(get_time_labels()) - 3),
        power_quality_message=(
            "Modeled overall PQ risk is high because harmonic risk is high "
            "and dominates the weighted demonstrator score."
        ),
    )

    visible_text = " ".join(_collect_text(render_power_quality_status(metrics)))

    assert (
        "Modeled overall PQ risk is high because harmonic risk is high "
        "and dominates the weighted demonstrator score." in visible_text
    )
    assert "Overall PQ risk:" not in visible_text
    assert "Overall PQ score:" not in visible_text
    assert "Current imbalance risk:" not in visible_text
    assert "Overall warning state:" not in visible_text

def test_dashboard_power_quality_status_mentions_overlap_with_grid_stress_when_relevant():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        harmonic_risk_level="high",
        current_imbalance_risk_level="moderate",
        overall_pq_risk_level="high",
        overall_pq_risk_score=72.0,
        overall_pq_warning_indicator=True,
        power_quality_warning_count=3,
        transformer_overload_indicator=True,
        highest_feeder_thermal_risk_level="moderate",
        harmonic_risk_score_by_timestep=[60.0, 72.0, 48.0]
        + [0.0] * (len(get_time_labels()) - 3),
        current_imbalance_percent_by_timestep=[20.0, 30.0, 14.0]
        + [0.0] * (len(get_time_labels()) - 3),
        overall_pq_risk_score_by_timestep=[45.0, 72.0, 37.0]
        + [0.0] * (len(get_time_labels()) - 3),
        power_quality_message="Modeled overall PQ risk is high in this scenario.",
    )

    visible_text = " ".join(_collect_text(render_power_quality_status(metrics)))

    assert "PQ warnings also overlap with modeled transformer or feeder stress" in (
        visible_text
    )
    assert "Grid-stress overlap:" not in visible_text

def test_dashboard_power_quality_status_renders_unavailable_for_missing_series():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        harmonic_risk_level="low",
        current_imbalance_risk_level="low",
        overall_pq_risk_level="low",
        overall_pq_risk_score=0.0,
        overall_pq_warning_indicator=False,
        power_quality_warning_count=0,
        harmonic_risk_score_by_timestep=[],
        current_imbalance_percent_by_timestep=[],
        overall_pq_risk_score_by_timestep=[],
    )

    visible_text = " ".join(_collect_text(render_power_quality_status(metrics)))

    assert "PQ status unavailable" in visible_text
    assert "completed PQ series are needed" in visible_text
    assert "Not available" not in visible_text

def test_dashboard_charger_availability_cards_render_zero_and_none_values_distinctly():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=0.0,
        energy_delivery_sufficient=False,
        average_charger_utilization_percent=None,
        peak_charger_utilization_percent=None,
        average_occupied_charger_count=0.0,
        peak_occupied_charger_count=0,
        maximum_queue_length=0,
        average_waiting_time_hours=None,
        vehicles_not_started_count=0,
        required_charger_count=None,
    )

    visible_text = " ".join(
        _collect_text(render_charger_availability_kpi_cards(metrics))
    )

    assert "Not available" in visible_text
    assert "0 chargers" in visible_text
    assert "0 vehicles" in visible_text
    assert "0.0 h" not in visible_text
    cards = render_charger_availability_kpi_cards(metrics)
    assert (
        _find_component_by_title(cards, CHARGER_UTILIZATION_UNAVAILABLE_HELPER)
        is not None
    )
    assert _find_component_by_title(cards, WAITING_TIME_UNAVAILABLE_HELPER) is None
    assert _find_component_by_title(
        cards,
        REQUIRED_CHARGER_COUNT_NOT_APPLICABLE_HELPER,
    ) is None

def test_dashboard_grid_loading_cards_use_completed_values_without_recalculation():
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=80.0,
        energy_delivery_sufficient=False,
        average_transformer_loading_percent=12.3,
        peak_transformer_loading_percent=145.6,
        transformer_overload_duration_hours=2.25,
        transformer_maximum_overload_kw=33.0,
        maximum_feeder_loading_percent=88.8,
        overloaded_feeder_count=1,
    )

    visible_text = " ".join(_collect_text(render_grid_loading_kpi_cards(metrics)))

    assert "Average Transformer Loading" not in visible_text
    assert "12.3%" not in visible_text
    assert "145.6%" in visible_text
    assert "2.2 h" in visible_text
    assert "33.0 kW" in visible_text
    assert "88.8%" in visible_text
    assert "1 feeders" in visible_text
    assert "80.0 kW" not in visible_text
    assert "100.0 kWh" not in visible_text

def test_dashboard_charger_availability_cards_render_zero_vehicle_values_safely():
    metrics = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        average_charger_utilization_percent=0.0,
        peak_charger_utilization_percent=0.0,
        average_occupied_charger_count=0.0,
        peak_occupied_charger_count=0,
        maximum_queue_length=0,
        average_waiting_time_hours=0.0,
        vehicles_not_started_count=0,
        required_charger_count=0,
    )

    visible_text = " ".join(
        _collect_text(render_charger_availability_kpi_cards(metrics))
    )

    assert "0.0%" in visible_text
    assert "0 chargers" in visible_text
    assert "0 vehicles" in visible_text
    assert "0.0 h" not in visible_text

def test_dashboard_renders_feeder_summary_section_from_metrics():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        maximum_feeder_loading_percent=108.0,
        overloaded_feeder_count=1,
        highest_feeder_thermal_risk_level="high",
        most_loaded_feeder_id="feeder-2",
        peak_feeder_loading_spread_percentage_points=16.0,
        feeder_loading_distribution_label="Uneven",
        feeder_status_message=(
            "1 feeder is overloaded. feeder-2 is the most loaded feeder."
        ),
        show_feeder_detail_indicator=True,
        feeder_summary_rows=[
            FeederSummaryMetrics(
                feeder_id="feeder-1",
                charger_count=3,
                peak_loading_percent=92.0,
                overload_indicator=False,
                overload_duration_hours=0.0,
                maximum_overload_kw=0.0,
                thermal_risk_level="moderate",
            ),
            FeederSummaryMetrics(
                feeder_id="feeder-2",
                charger_count=2,
                peak_loading_percent=108.0,
                overload_indicator=True,
                overload_duration_hours=1.0,
                maximum_overload_kw=12.0,
                thermal_risk_level="high",
            ),
        ],
    )

    visible_text = " ".join(_collect_text(render_feeder_summary_section(metrics)))

    assert "Feeder bottleneck indicated" in visible_text
    assert "Most loaded feeder:" in visible_text
    assert "feeder-2" in visible_text
    assert "Loading spread:" in visible_text
    assert "16.0 percentage points" in visible_text
    assert "Loading distribution:" in visible_text
    assert "Uneven" in visible_text
    assert "Thermal risk:" in visible_text
    assert "High" in visible_text
    assert "Maximum feeder loading:" not in visible_text
    assert "Overloaded feeders:" not in visible_text
    assert "Feeder detail" not in visible_text
    assert "3 chargers" not in visible_text

def test_dashboard_hides_feeder_detail_table_when_metrics_mark_it_low_value():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        maximum_feeder_loading_percent=47.7,
        overloaded_feeder_count=0,
        highest_feeder_thermal_risk_level="low",
        most_loaded_feeder_id="feeder-1",
        peak_feeder_loading_spread_percentage_points=0.0,
        feeder_loading_distribution_label="Balanced",
        feeder_status_message=(
            "All feeders are evenly loaded. No local feeder bottleneck detected."
        ),
        show_feeder_detail_indicator=False,
        feeder_summary_rows=[
            FeederSummaryMetrics(
                feeder_id="feeder-1",
                charger_count=3,
                peak_loading_percent=47.7,
                overload_indicator=False,
                overload_duration_hours=0.0,
                maximum_overload_kw=0.0,
                thermal_risk_level="low",
            ),
            FeederSummaryMetrics(
                feeder_id="feeder-2",
                charger_count=3,
                peak_loading_percent=47.7,
                overload_indicator=False,
                overload_duration_hours=0.0,
                maximum_overload_kw=0.0,
                thermal_risk_level="low",
            ),
        ],
    )

    visible_text = " ".join(_collect_text(render_feeder_summary_section(metrics)))

    assert "Balanced feeder loading" in visible_text
    assert "All feeders are evenly loaded. No local feeder bottleneck detected." in (
        visible_text
    )
    assert "Feeder detail" not in visible_text
    assert "3 chargers" not in visible_text

def test_dashboard_shows_feeder_detail_table_for_uneven_non_overloaded_state():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        maximum_feeder_loading_percent=75.0,
        overloaded_feeder_count=0,
        highest_feeder_thermal_risk_level="low",
        most_loaded_feeder_id="feeder-2",
        peak_feeder_loading_spread_percentage_points=15.0,
        feeder_loading_distribution_label="Uneven",
        feeder_status_message=(
            "Feeder loading is uneven. feeder-2 is the most loaded feeder."
        ),
        show_feeder_detail_indicator=True,
        feeder_summary_rows=[
            FeederSummaryMetrics(
                feeder_id="feeder-1",
                charger_count=3,
                peak_loading_percent=60.0,
                overload_indicator=False,
                overload_duration_hours=0.0,
                maximum_overload_kw=0.0,
                thermal_risk_level="low",
            ),
            FeederSummaryMetrics(
                feeder_id="feeder-2",
                charger_count=3,
                peak_loading_percent=75.0,
                overload_indicator=False,
                overload_duration_hours=0.0,
                maximum_overload_kw=0.0,
                thermal_risk_level="low",
            ),
        ],
    )

    visible_text = " ".join(_collect_text(render_feeder_summary_section(metrics)))

    assert "Uneven feeder loading" in visible_text
    assert "feeder-2" in visible_text
    assert "Loading spread:" in visible_text
    assert "15.0 percentage points" in visible_text
    assert "Feeder detail" not in visible_text
    assert "Not overloaded" not in visible_text

def test_dashboard_renders_feeder_summary_section_empty_state_safely():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        feeder_summary_rows=[],
    )

    feeder_summary = render_feeder_summary_section(metrics)

    assert (
        feeder_summary
        == "Run the simulation to review modeled transformer and feeder loading "
        "against configured asset ratings and connection-capacity pressure."
    )

def test_dashboard_capacity_planning_cards_render_positive_margin():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=300.0,
        required_connection_capacity_kw=400.0,
        recommended_connection_capacity_kw=440.0,
        planning_margin_percent=10.0,
        peak_capacity_margin_kw=120.0,
        peak_capacity_margin_percent=12.0,
        connection_capacity_exceeded=False,
    )
    simulation_result = SimulationResult(
        daily_energy_demand=1000.0,
        configured_connection_capacity_kw=520.0,
        installed_charger_capacity_kw=600.0,
        available_site_charging_capacity_kw=500.0,
    )

    rendered_cards = render_capacity_planning_kpi_cards(metrics, simulation_result)
    visible_text = " ".join(_collect_text(rendered_cards))

    assert "Peak Capacity Margin" in visible_text
    assert "+120.0 kW" in visible_text
    assert "Margin percent:" not in visible_text

def test_dashboard_capacity_planning_cards_render_undefined_margin_percent_safely():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=0.0,
        energy_delivery_sufficient=False,
        peak_load=0.0,
        required_connection_capacity_kw=150.0,
        recommended_connection_capacity_kw=165.0,
        planning_margin_percent=10.0,
        peak_capacity_margin_kw=-150.0,
        peak_capacity_margin_percent=None,
        connection_capacity_exceeded=True,
    )
    simulation_result = SimulationResult(
        daily_energy_demand=1000.0,
        configured_connection_capacity_kw=0.0,
        installed_charger_capacity_kw=150.0,
        available_site_charging_capacity_kw=0.0,
    )

    rendered_cards = render_capacity_planning_kpi_cards(metrics, simulation_result)
    visible_text = " ".join(_collect_text(rendered_cards))

    assert "Capacity Shortfall" in visible_text
    assert "150.0 kW" in visible_text
    assert "Margin percent:" not in visible_text

def test_dashboard_connection_capacity_exceeded_status_formats_both_states():
    exceeded_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        connection_capacity_exceeded=True,
    )
    not_exceeded_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        connection_capacity_exceeded=False,
    )

    assert format_connection_capacity_exceeded_status(exceeded_metrics) == "Exceeded"
    assert (
        format_connection_capacity_exceeded_status(not_exceeded_metrics)
        == "Not exceeded"
    )

def test_dashboard_charger_availability_cards_use_completed_values_without_recalculation():
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=80.0,
        energy_delivery_sufficient=False,
        average_charger_utilization_percent=12.3,
        peak_charger_utilization_percent=45.6,
        average_occupied_charger_count=1.7,
        peak_occupied_charger_count=4,
        maximum_queue_length=9,
        average_waiting_time_hours=1.25,
        vehicles_not_started_count=3,
        required_charger_count=None,
    )

    visible_text = " ".join(
        _collect_text(render_charger_availability_kpi_cards(metrics))
    )

    assert "45.6%" in visible_text
    assert "4 chargers" in visible_text
    assert "9 vehicles" in visible_text
    assert "3 vehicles" in visible_text
    assert "12.3%" not in visible_text
    assert "1.7 chargers" not in visible_text
    assert "1.2 h" not in visible_text
    assert "Not applicable" not in visible_text
    assert "80.0 kW" not in visible_text
    assert "100.0 kWh" not in visible_text

def test_dashboard_charger_availability_cards_update_with_strategy_metrics():
    base_scenario = get_scenario_preset(PUBLIC_FAST_CHARGING_PRESET_ID).scenario

    uncontrolled_metrics = calculate_metrics(
        simulate(
            replace(
                base_scenario,
                charging_strategy=ChargingStrategy.UNCONTROLLED,
            )
        ),
        replace(
            base_scenario,
            charging_strategy=ChargingStrategy.UNCONTROLLED,
        ),
    )
    smart_metrics = calculate_metrics(
        simulate(
            replace(
                base_scenario,
                charging_strategy=ChargingStrategy.SMART,
            )
        ),
        replace(
            base_scenario,
            charging_strategy=ChargingStrategy.SMART,
        ),
    )

    uncontrolled_visible = " ".join(
        _collect_text(render_charger_availability_kpi_cards(uncontrolled_metrics))
    )
    smart_visible = " ".join(
        _collect_text(render_charger_availability_kpi_cards(smart_metrics))
    )

    assert uncontrolled_visible != smart_visible

def test_dashboard_charger_availability_cards_render_legacy_metrics_payload_safely():
    legacy_metrics = metrics_from_dict(
        {
            "total_daily_energy": 1000.0,
            "available_capacity": 500.0,
            "energy_delivery_sufficient": True,
            "peak_load": 321.0,
            "capacity_utilization": 64.2,
            "delivered_energy": 1000.0,
            "unmet_energy": 0.0,
            "annual_energy": 365000.0,
        }
    )

    visible_text = " ".join(
        _collect_text(render_charger_availability_kpi_cards(legacy_metrics))
    )

    assert "Peak Charger Utilization" in visible_text
    assert "0.0%" in visible_text
    assert "Peak Occupied Chargers" in visible_text
    assert "0 chargers" in visible_text
    assert "0 vehicles" in visible_text
    assert "Average Charger Utilization" not in visible_text
    assert "Average Occupied Chargers" not in visible_text
    assert "Average Waiting Time" not in visible_text
    assert "Required Charger Count" not in visible_text

def test_dashboard_builds_connection_capacity_comparison_rows_from_metrics():
    uncontrolled_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        capacity_utilization=80.0,
        recommended_connection_capacity_kw=1260.0,
        connection_capacity_exceeded=True,
        maximum_capacity_exceedance_kw=200.0,
        capacity_exceedance_duration_hours=3.0,
        average_transformer_loading_percent=82.5,
        transformer_overload_indicator=True,
        transformer_overload_duration_hours=2.0,
        transformer_maximum_overload_kw=25.0,
        transformer_thermal_risk_level="high",
        feeder_overload_indicator=True,
        overloaded_feeder_count=2,
        highest_feeder_thermal_risk_level="high",
        peak_harmonic_risk_score=64.0,
        harmonic_risk_duration_hours=2.0,
        peak_current_imbalance_percent=24.0,
        imbalance_duration_hours=1.0,
        average_charger_utilization_percent=88.0,
        peak_charger_utilization_percent=100.0,
        average_occupied_charger_count=3.5,
        average_queue_length=1.5,
        queue_duration_hours=2.0,
        maximum_waiting_time_hours=1.5,
        vehicles_waiting_count=4,
    )
    smart_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        capacity_utilization=50.0,
        recommended_connection_capacity_kw=980.0,
        connection_capacity_exceeded=False,
        maximum_capacity_exceedance_kw=0.0,
        capacity_exceedance_duration_hours=0.0,
        average_transformer_loading_percent=60.0,
        transformer_overload_indicator=False,
        transformer_overload_duration_hours=0.0,
        transformer_maximum_overload_kw=0.0,
        transformer_thermal_risk_level="low",
        feeder_overload_indicator=False,
        overloaded_feeder_count=0,
        highest_feeder_thermal_risk_level="low",
        peak_harmonic_risk_score=32.0,
        harmonic_risk_duration_hours=0.5,
        peak_current_imbalance_percent=14.0,
        imbalance_duration_hours=0.0,
        average_charger_utilization_percent=66.0,
        peak_charger_utilization_percent=82.0,
        average_occupied_charger_count=2.0,
        average_queue_length=0.5,
        queue_duration_hours=0.5,
        maximum_waiting_time_hours=0.75,
        vehicles_waiting_count=1,
    )
    rows = build_connection_capacity_comparison_rows(
        uncontrolled_metrics,
        smart_metrics,
    )

    rendered_rows = [
        tuple(" ".join(_collect_text(cell)) for cell in row)
        for row in rows
    ]

    assert (
        "Capacity utilization (%)",
        "80.0%",
        "50.0%",
        "+30.0 pp",
    ) in rendered_rows
    assert (
        "Recommended connection capacity (kW)",
        "1,260.0 kW",
        "980.0 kW",
        "+280.0 kW",
    ) in rendered_rows
    assert (
        "Connection capacity exceeded",
        "Exceeded",
        "Not exceeded",
        "Improved",
    ) in rendered_rows
    assert (
        "Connection capacity adequacy",
        "Not adequate",
        "Not adequate",
        "No change",
    ) in rendered_rows
    assert (
        "Peak harmonic risk score",
        "64.0 / 100",
        "32.0 / 100",
        "+32.0 points",
    ) in rendered_rows
    assert (
        "Vehicles waiting",
        "4 vehicles",
        "1 vehicles",
        "+3 vehicles",
    ) in rendered_rows

def test_dashboard_renders_detailed_comparison_table_from_metrics():
    uncontrolled_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        capacity_utilization=80.0,
        recommended_connection_capacity_kw=1260.0,
        connection_capacity_exceeded=True,
        maximum_capacity_exceedance_kw=200.0,
        capacity_exceedance_duration_hours=3.0,
        average_transformer_loading_percent=82.5,
        transformer_overload_indicator=True,
        transformer_overload_duration_hours=2.0,
        transformer_maximum_overload_kw=25.0,
        transformer_thermal_risk_level="high",
        feeder_overload_indicator=True,
        overloaded_feeder_count=2,
        highest_feeder_thermal_risk_level="high",
        peak_harmonic_risk_score=64.0,
        harmonic_risk_duration_hours=2.0,
        peak_current_imbalance_percent=24.0,
        imbalance_duration_hours=1.0,
        average_charger_utilization_percent=88.0,
        peak_charger_utilization_percent=100.0,
        average_occupied_charger_count=3.5,
        average_queue_length=1.5,
        queue_duration_hours=2.0,
        maximum_waiting_time_hours=1.5,
        vehicles_waiting_count=4,
    )
    smart_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        capacity_utilization=50.0,
        recommended_connection_capacity_kw=980.0,
        connection_capacity_exceeded=False,
        maximum_capacity_exceedance_kw=0.0,
        capacity_exceedance_duration_hours=0.0,
        average_transformer_loading_percent=60.0,
        transformer_overload_indicator=False,
        transformer_overload_duration_hours=0.0,
        transformer_maximum_overload_kw=0.0,
        transformer_thermal_risk_level="low",
        feeder_overload_indicator=False,
        overloaded_feeder_count=0,
        highest_feeder_thermal_risk_level="low",
        peak_harmonic_risk_score=32.0,
        harmonic_risk_duration_hours=0.5,
        peak_current_imbalance_percent=14.0,
        imbalance_duration_hours=0.0,
        average_charger_utilization_percent=66.0,
        peak_charger_utilization_percent=82.0,
        average_occupied_charger_count=2.0,
        average_queue_length=0.5,
        queue_duration_hours=0.5,
        maximum_waiting_time_hours=0.75,
        vehicles_waiting_count=1,
    )

    table = render_detailed_comparison_table(
        uncontrolled_metrics,
        smart_metrics,
    )
    visible_text = " ".join(_collect_text(table))

    assert "Metric" in visible_text
    assert "Uncontrolled charging" in visible_text
    assert "Smart charging" in visible_text
    assert "Delta / Status" in visible_text
    assert "Numeric delta = Uncontrolled - Smart" in visible_text
    assert "Relative peak reduction (%)" not in visible_text
    assert "Recommended connection capacity (kW)" in visible_text
    assert "1,260.0 kW" in visible_text
    assert "980.0 kW" in visible_text
    assert "Capacity utilization (%)" in visible_text
    assert "80.0%" in visible_text
    assert "50.0%" in visible_text
    assert "Connection capacity exceeded" in visible_text
    assert "Exceeded" in visible_text
    assert "Not exceeded" in visible_text
    assert "Improved" in visible_text
    assert "Maximum capacity exceedance (kW)" in visible_text
    assert "200.0 kW" in visible_text
    assert "0.0 kW" in visible_text
    assert "Capacity exceedance duration (h)" in visible_text
    assert "3.0 h" in visible_text
    assert "0.0 h" in visible_text
    assert "Peak harmonic risk score" in visible_text
    assert "64.0 / 100" in visible_text
    assert "32.0 / 100" in visible_text
    assert "Peak current imbalance (%)" in visible_text
    assert "24.0%" in visible_text
    assert "14.0%" in visible_text
    assert "Transformer thermal risk" in visible_text
    assert "High" in visible_text
    assert "Low" in visible_text
    assert "Peak charger utilization (%)" in visible_text
    assert "100.0%" in visible_text
    assert "82.0%" in visible_text
    assert "+18.0 pp" in visible_text
    assert "Average charger utilization (%)" not in visible_text

def test_dashboard_detailed_comparison_table_uses_completed_metrics_only():
    uncontrolled_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        capacity_utilization=82.0,
        recommended_connection_capacity_kw=950.0,
        maximum_capacity_exceedance_kw=50.0,
        capacity_exceedance_duration_hours=2.0,
        peak_harmonic_risk_score=18.0,
    )
    smart_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        capacity_utilization=41.0,
        recommended_connection_capacity_kw=700.0,
        maximum_capacity_exceedance_kw=0.0,
        capacity_exceedance_duration_hours=0.0,
        peak_harmonic_risk_score=6.0,
    )

    visible_text = " ".join(
        _collect_text(
            render_detailed_comparison_table(
                uncontrolled_metrics,
                smart_metrics,
            )
        )
    )

    assert "82.0%" in visible_text
    assert "41.0%" in visible_text
    assert "950.0 kW" in visible_text
    assert "700.0 kW" in visible_text
    assert "2.0 h" in visible_text
    assert "18.0 / 100" in visible_text
    assert "6.0 / 100" in visible_text
    assert "Difference" not in visible_text

def test_dashboard_builds_connection_capacity_sensitivity_rows_in_ascending_order():
    sensitivity_rows = [
        CapacityAlternativeMetrics(
            capacity_option_kw=1200.0,
            required_connection_capacity_kw=400.0,
            headroom_kw=800.0,
            headroom_percent=66.7,
            capacity_exceeded=False,
            time_above_capacity_hours=0.0,
        ),
        CapacityAlternativeMetrics(
            capacity_option_kw=800.0,
            required_connection_capacity_kw=400.0,
            headroom_kw=400.0,
            headroom_percent=50.0,
            capacity_exceeded=False,
            time_above_capacity_hours=0.0,
        ),
        CapacityAlternativeMetrics(
            capacity_option_kw=1000.0,
            required_connection_capacity_kw=450.0,
            headroom_kw=550.0,
            headroom_percent=55.0,
            capacity_exceeded=False,
            time_above_capacity_hours=0.0,
        ),
    ]

    rows = build_connection_capacity_sensitivity_rows(sensitivity_rows)

    assert rows == [
        ("800.0 kW", "400.0 kW", "+400.0 kW", "Adequate", "0.0 h"),
        ("1,000.0 kW", "450.0 kW", "+550.0 kW", "Adequate", "0.0 h"),
        ("1,200.0 kW", "400.0 kW", "+800.0 kW", "Adequate", "0.0 h"),
    ]

def test_dashboard_renders_connection_capacity_sensitivity_table_from_completed_rows():
    sensitivity_rows = [
        CapacityAlternativeMetrics(
            capacity_option_kw=800.0,
            required_connection_capacity_kw=880.0,
            headroom_kw=-80.0,
            headroom_percent=-10.0,
            capacity_exceeded=True,
            time_above_capacity_hours=3.0,
            capacity_adequate_indicator=False,
            capacity_recommendation_reason="persistent_requested_exceedance",
        ),
        CapacityAlternativeMetrics(
            capacity_option_kw=1200.0,
            required_connection_capacity_kw=400.0,
            headroom_kw=800.0,
            headroom_percent=66.7,
            capacity_exceeded=False,
            time_above_capacity_hours=0.0,
        ),
    ]

    table = render_connection_capacity_sensitivity_table(
        sensitivity_rows,
        configured_capacity_kw=800.0,
        recommended_capacity_kw=1200.0,
    )
    visible_text = " ".join(_collect_text(table))

    assert "Connection capacity" in visible_text
    assert "Required peak demand" in visible_text
    assert "Headroom" in visible_text
    assert "Status" in visible_text
    assert "Time above capacity" in visible_text
    assert "800.0 kW" in visible_text
    assert "1,200.0 kW" in visible_text
    assert "880.0 kW" in visible_text
    assert "400.0 kW" in visible_text
    assert "-80.0 kW" in visible_text
    assert "+800.0 kW" in visible_text
    assert "Not adequate" in visible_text
    assert "3.0 h" in visible_text
    assert "0.0 h" in visible_text
    assert "Adequate" in visible_text
    assert "Configured" in visible_text
    assert "Recommended" in visible_text
    assert "Simulated peak load" not in visible_text
    assert "Maximum exceedance" not in visible_text
    assert "Energy delivery sufficient" not in visible_text
    assert "Unmet energy" not in visible_text

def test_dashboard_connection_capacity_sensitivity_table_handles_duplicate_equivalent_generated_alternatives_safely():
    sensitivity_rows = [
        CapacityAlternativeMetrics(
            capacity_option_kw=1000.0,
            required_connection_capacity_kw=400.0,
            headroom_kw=600.0,
            headroom_percent=60.0,
            capacity_exceeded=False,
            time_above_capacity_hours=0.0,
        ),
        CapacityAlternativeMetrics(
            capacity_option_kw=1200.0,
            required_connection_capacity_kw=400.0,
            headroom_kw=800.0,
            headroom_percent=66.7,
            capacity_exceeded=False,
            time_above_capacity_hours=0.0,
        ),
    ]

    table = render_connection_capacity_sensitivity_table(
        sensitivity_rows,
        configured_capacity_kw=1000.0,
        recommended_capacity_kw=1200.0,
    )
    visible_text = " ".join(_collect_text(table))

    assert "1,000.0 kW" in visible_text
    assert "1,200.0 kW" in visible_text
    assert visible_text.count("Adequate") == 2

def test_dashboard_connection_capacity_sensitivity_table_uses_completed_rows_only():
    sensitivity_rows = [
        CapacityAlternativeMetrics(
            capacity_option_kw=910.0,
            required_connection_capacity_kw=1135.0,
            headroom_kw=-225.0,
            headroom_percent=None,
            capacity_exceeded=True,
            time_above_capacity_hours=7.5,
            capacity_adequate_indicator=False,
            capacity_recommendation_reason="persistent_requested_exceedance",
        ),
    ]

    visible_text = " ".join(
        _collect_text(
            render_connection_capacity_sensitivity_table(
                sensitivity_rows,
                configured_capacity_kw=910.0,
                recommended_capacity_kw=1135.0,
            )
        )
    )

    assert "910.0 kW" in visible_text
    assert "1,135.0 kW" in visible_text
    assert "-225.0 kW" in visible_text
    assert "Not adequate" in visible_text
    assert "7.5 h" in visible_text
    assert "+225.0 kW" not in visible_text

def test_dashboard_renders_real_connection_capacity_sensitivity_flow_in_ascending_order():
    scenario = Scenario(
        vehicles=20,
        daily_energy_per_vehicle=100.0,
        charger_count=4,
        charger_power=100.0,
        grid_capacity=100.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    )

    sensitivity_rows = run_connection_capacity_sensitivity(scenario)
    table = render_connection_capacity_sensitivity_table(
        sensitivity_rows,
        configured_capacity_kw=100.0,
        recommended_capacity_kw=440.0,
    )
    visible_text = " ".join(_collect_text(table))

    assert [row.capacity_option_kw for row in sensitivity_rows] == pytest.approx(
        [80.0, 100.0, 120.0, 400.0, 440.0]
    )
    assert "80.0 kW" in visible_text
    assert "100.0 kW" in visible_text
    assert "120.0 kW" in visible_text
    assert "400.0 kW" in visible_text
    assert "440.0 kW" in visible_text
    assert "-320.0 kW" in visible_text
    assert "-300.0 kW" in visible_text
    assert "-280.0 kW" in visible_text
    assert "+40.0 kW" in visible_text
    assert "0.0 kW" in visible_text
    assert "Not adequate" in visible_text
    assert "Adequate" in visible_text

def test_dashboard_builds_scenario_ab_difference_rows_from_metrics():
    metrics_a = Metrics(
        total_daily_energy=7500.0,
        available_capacity=1000.0,
        energy_delivery_sufficient=True,
        peak_load=1000.0,
        capacity_utilization=100.0,
        delivered_energy=7500.0,
        unmet_energy=0.0,
        annual_energy=2737500.0,
    )
    metrics_b = Metrics(
        total_daily_energy=11250.0,
        available_capacity=1200.0,
        energy_delivery_sufficient=True,
        peak_load=1200.0,
        capacity_utilization=100.0,
        delivered_energy=11250.0,
        unmet_energy=0.0,
        annual_energy=4106250.0,
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=200.0,
        peak_load_change_percent=20.0,
        capacity_utilization_difference_percentage_points=0.0,
        capacity_utilization_change_percent=0.0,
        delivered_energy_difference_kwh=3750.0,
        delivered_energy_change_percent=50.0,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=None,
        peak_harmonic_risk_score_difference=24.0,
        harmonic_risk_duration_hours_difference=1.5,
        peak_current_imbalance_percent_difference=8.0,
        imbalance_duration_hours_difference=0.5,
        overall_pq_risk_score_difference=20.0,
        power_quality_warning_count_difference=2,
    )

    rows = build_scenario_ab_comparison_rows(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )

    assert rows[0] == (
        "Peak load (kW)",
        "1,000.0 kW",
        "1,200.0 kW",
        "+200.0 kW",
        "+20.0%",
    )
    assert rows[1] == (
        "Capacity utilization (%)",
        "100.0%",
        "100.0%",
        "0.0 pp",
        "0.0%",
    )
    assert rows[2] == (
        "Delivered energy (kWh)",
        "7,500.0 kWh",
        "11,250.0 kWh",
        "+3,750.0 kWh",
        "+50.0%",
    )
    assert rows[3] == ("Unmet energy (kWh)", "0.0 kWh", "0.0 kWh", "0.0 kWh", "N/A")
    assert rows[4] == (
        "Peak harmonic risk score",
        "0.0 / 100",
        "0.0 / 100",
        "+24.0 points",
        "Not applicable",
    )
    assert rows[5] == (
        "Harmonic risk duration (h)",
        "0.0 h",
        "0.0 h",
        "+1.5 h",
        "Not applicable",
    )
    assert rows[6] == (
        "Peak current imbalance (%)",
        "0.0%",
        "0.0%",
        "+8.0 pp",
        "Not applicable",
    )
    assert rows[7] == (
        "Current imbalance duration (h)",
        "0.0 h",
        "0.0 h",
        "+0.5 h",
        "Not applicable",
    )
    assert rows[8] == (
        "Overall PQ risk score",
        "0.0 / 100",
        "0.0 / 100",
        "+20.0 points",
        "Not applicable",
    )
    assert rows[9] == (
        "PQ warning count",
        "0 warnings",
        "0 warnings",
        "+2 warnings",
        "Not applicable",
    )

def test_dashboard_renders_scenario_ab_difference_table_from_metrics():
    metrics_a = Metrics(
        total_daily_energy=7500.0,
        available_capacity=1000.0,
        energy_delivery_sufficient=True,
        peak_load=1000.0,
        capacity_utilization=100.0,
        delivered_energy=7500.0,
        unmet_energy=0.0,
        annual_energy=2737500.0,
    )
    metrics_b = Metrics(
        total_daily_energy=11250.0,
        available_capacity=1200.0,
        energy_delivery_sufficient=True,
        peak_load=1200.0,
        capacity_utilization=100.0,
        delivered_energy=11250.0,
        unmet_energy=0.0,
        annual_energy=4106250.0,
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=200.0,
        peak_load_change_percent=20.0,
        capacity_utilization_difference_percentage_points=0.0,
        capacity_utilization_change_percent=0.0,
        delivered_energy_difference_kwh=3750.0,
        delivered_energy_change_percent=50.0,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=None,
    )

    table = render_scenario_ab_comparison_table(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )
    visible_text = " ".join(_collect_text(table))

    assert "Metric" in visible_text
    assert "Scenario A" in visible_text
    assert "Scenario B" in visible_text
    assert "Difference" in visible_text
    assert "Change" in visible_text
    assert "Peak load (kW)" in visible_text
    assert "Capacity utilization (%)" in visible_text
    assert "Delivered energy (kWh)" in visible_text
    assert "Unmet energy (kWh)" in visible_text
    assert "Daily charging cost" not in visible_text
    assert "Annual charging cost" not in visible_text
    assert "+200.0 kW" in visible_text
    assert "+20.0%" in visible_text
    assert "0.0 pp" in visible_text
    assert "N/A" in visible_text

def test_dashboard_renders_scenario_ab_executive_summary_cards_from_metrics():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=420.0,
        unmet_energy=120.0,
        maximum_queue_length=6,
        peak_transformer_loading_percent=88.0,
        overall_pq_risk_score=34.0,
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=360.0,
        unmet_energy=40.0,
        maximum_queue_length=2,
        peak_transformer_loading_percent=76.0,
        overall_pq_risk_score=18.0,
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=-60.0,
        peak_load_change_percent=-14.2857142857,
        capacity_utilization_difference_percentage_points=0.0,
        capacity_utilization_change_percent=None,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=None,
        unmet_energy_difference_kwh=-80.0,
        unmet_energy_change_percent=-66.6666666667,
        peak_transformer_loading_percent_difference=-12.0,
        overall_pq_risk_score_difference=-16.0,
        maximum_queue_length_difference=-4,
    )

    cards = render_scenario_ab_executive_summary_cards(
        metrics_a,
        metrics_b,
        comparison_metrics,
        scenario_a_label="Heavy-duty",
        scenario_b_label="Workplace Charging",
    )
    visible_text = " ".join(_collect_text(cards))

    assert len(cards) == 6
    assert "Peak Load" in visible_text
    assert "Capacity Utilization" in visible_text
    assert "Unmet Energy" in visible_text
    assert "Maximum Queue Length" in visible_text
    assert "Peak Transformer Loading" in visible_text
    assert "Overall PQ Risk" in visible_text
    assert "Improvement" not in visible_text
    assert "Relative change:" not in visible_text
    assert "A 420.0 kW -> B 360.0 kW" in visible_text
    assert "↓ 60.0 kW" in visible_text
    assert "0.0 pp" in visible_text
    assert "A 34.0 / 100 -> B 18.0 / 100" in visible_text

def _scenario_ab_peak_load_display_outcome(
    *,
    scenario_b_peak_load: float,
    peak_load_difference_kw: float,
    peak_load_change_percent: float | None,
) -> str:
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=420.0,
        capacity_utilization=80.0,
        unmet_energy=120.0,
        maximum_queue_length=6,
        peak_transformer_loading_percent=88.0,
        overall_pq_risk_score=34.0,
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=scenario_b_peak_load,
        capacity_utilization=80.0,
        unmet_energy=120.0,
        maximum_queue_length=6,
        peak_transformer_loading_percent=88.0,
        overall_pq_risk_score=34.0,
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=peak_load_difference_kw,
        peak_load_change_percent=peak_load_change_percent,
        capacity_utilization_difference_percentage_points=0.0,
        capacity_utilization_change_percent=0.0,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=0.0,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=0.0,
        peak_transformer_loading_percent_difference=0.0,
        overall_pq_risk_score_difference=0.0,
        maximum_queue_length_difference=0,
    )

    display_data = prepare_scenario_comparison_display_data(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )
    return next(
        metric.display_outcome
        for metric in display_data.executive_metrics
        if metric.metric_id == "peak_load"
    )

def test_scenario_ab_executive_metric_display_outcome_is_minimal_for_zero_change():
    assert (
        _scenario_ab_peak_load_display_outcome(
            scenario_b_peak_load=420.0,
            peak_load_difference_kw=0.0,
            peak_load_change_percent=0.0,
        )
        == SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL
    )

def test_scenario_ab_executive_metric_display_outcome_is_minimal_for_negligible_change():
    assert (
        _scenario_ab_peak_load_display_outcome(
            scenario_b_peak_load=420.04,
            peak_load_difference_kw=0.04,
            peak_load_change_percent=0.0095238095,
        )
        == SCENARIO_EXECUTIVE_OUTCOME_NEUTRAL
    )

def test_scenario_ab_executive_metric_display_outcome_is_improvement_for_material_benefit():
    assert (
        _scenario_ab_peak_load_display_outcome(
            scenario_b_peak_load=360.0,
            peak_load_difference_kw=-60.0,
            peak_load_change_percent=-14.2857142857,
        )
        == SCENARIO_EXECUTIVE_OUTCOME_IMPROVEMENT
    )

def test_scenario_ab_executive_metric_display_outcome_is_trade_off_for_material_worsening():
    assert (
        _scenario_ab_peak_load_display_outcome(
            scenario_b_peak_load=480.0,
            peak_load_difference_kw=60.0,
            peak_load_change_percent=14.2857142857,
        )
        == SCENARIO_EXECUTIVE_OUTCOME_TRADE_OFF
    )

def test_dashboard_renders_materiality_aware_scenario_ab_kpi_badges():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=420.0,
        capacity_utilization=80.0,
        unmet_energy=120.0,
        maximum_queue_length=6,
        peak_transformer_loading_percent=88.0,
        overall_pq_risk_score=34.0,
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        peak_load=420.04,
        capacity_utilization=80.0,
        unmet_energy=120.0,
        maximum_queue_length=6,
        peak_transformer_loading_percent=88.0,
        overall_pq_risk_score=34.0,
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=0.04,
        peak_load_change_percent=0.0095238095,
        capacity_utilization_difference_percentage_points=0.0,
        capacity_utilization_change_percent=0.0,
        delivered_energy_difference_kwh=0.0,
        delivered_energy_change_percent=0.0,
        unmet_energy_difference_kwh=0.0,
        unmet_energy_change_percent=0.0,
        peak_transformer_loading_percent_difference=0.0,
        overall_pq_risk_score_difference=0.0,
        maximum_queue_length_difference=0,
    )

    cards = render_scenario_ab_executive_summary_cards(
        metrics_a,
        metrics_b,
        comparison_metrics,
        scenario_a_label="Heavy-duty",
        scenario_b_label="Workplace Charging",
    )
    visible_text = " ".join(_collect_text(cards))

    assert "0.0 kW" in visible_text
    assert "Minimal change" not in visible_text
    assert "Trade-off 0.0 kW" not in visible_text
    assert "+0.0 kW" not in visible_text
    assert "-0.0 kW" not in visible_text

def test_signed_delta_formatters_normalize_rounded_zero_centrally():
    assert format_signed_power_kw(0.0) == "0.0 kW"
    assert format_signed_power_kw(0.04) == "0.0 kW"
    assert format_signed_power_kw(-0.04) == "0.0 kW"
    assert format_signed_power_kw(0.05) == "+0.1 kW"
    assert format_signed_power_kw(-0.05) == "-0.1 kW"

    assert format_signed_percentage_points(0.04) == "0.0 pp"
    assert format_signed_percentage_points(-0.04) == "0.0 pp"
    assert format_signed_percentage_points(0.06) == "+0.1 pp"
    assert format_signed_percentage_points(-0.06) == "-0.1 pp"

    assert format_signed_hours(0.04) == "0.0 h"
    assert format_signed_hours(-0.04) == "0.0 h"
    assert format_signed_hours(0.06) == "+0.1 h"
    assert format_signed_hours(-0.06) == "-0.1 h"

    assert format_signed_score_points(0.04) == "0.0 points"
    assert format_signed_score_points(-0.04) == "0.0 points"
    assert format_signed_score_points(0.06) == "+0.1 points"
    assert format_signed_score_points(-0.06) == "-0.1 points"

def test_dashboard_renders_smart_charging_zero_deltas_without_signed_zero():
    uncontrolled_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=100.0,
        required_connection_capacity_kw=200.0,
        peak_transformer_loading_percent=75.0,
        maximum_feeder_loading_percent=60.0,
    )
    smart_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=100.04,
        required_connection_capacity_kw=200.04,
        peak_transformer_loading_percent=75.04,
        maximum_feeder_loading_percent=60.0,
    )
    comparison_metrics = ComparisonMetrics(
        peak_reduction=-0.04,
        relative_peak_reduction=-0.04,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
        required_connection_capacity_difference_kw=-0.04,
        average_waiting_time_difference_hours=-0.04,
        uncontrolled_average_waiting_time_hours=1.0,
        smart_average_waiting_time_hours=1.04,
        uncontrolled_queue_present_indicator=False,
        smart_queue_present_indicator=False,
        uncontrolled_maximum_queue_length=0,
        smart_maximum_queue_length=0,
        peak_transformer_loading_percent_difference=-0.04,
        overall_pq_risk_score_difference=-0.0,
        uncontrolled_overall_pq_risk_score=18.0,
        smart_overall_pq_risk_score=18.0,
        uncontrolled_overall_pq_risk_level="low",
        smart_overall_pq_risk_level="low",
        uncontrolled_power_quality_warning_count=0,
        smart_power_quality_warning_count=0,
        grid_capacity_status="No modeled constraint",
    )

    visible_text = " ".join(
        _collect_text(
            render_comparison_kpi_cards(
                comparison_metrics,
                uncontrolled_metrics,
                smart_metrics,
            )
        )
    )

    assert visible_text.count("No change") == 3
    assert "100.0 kW -> 100.0 kW" in visible_text
    assert "200.0 kW -> 200.0 kW" in visible_text
    assert "75.0% -> 75.0%" in visible_text
    assert "+0.0 kW" not in visible_text
    assert "-0.0 kW" not in visible_text
    assert "+0.0 pp" not in visible_text
    assert "-0.0 pp" not in visible_text

def test_dashboard_renders_scenario_ab_detailed_sections_by_theme():
    metrics_a = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=1000.0,
        capacity_utilization=80.0,
        delivered_energy=750.0,
        unmet_energy=250.0,
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
        harmonic_risk_level="high",
        current_imbalance_risk_level="moderate",
        overall_pq_risk_level="high",
        peak_harmonic_risk_score=64.0,
        harmonic_risk_duration_hours=2.0,
        peak_current_imbalance_percent=24.0,
        imbalance_duration_hours=1.0,
        overall_pq_risk_score=58.0,
        power_quality_warning_count=3,
        average_charger_utilization_percent=75.0,
        peak_charger_utilization_percent=100.0,
        average_occupied_charger_count=3.5,
        peak_occupied_charger_count=5,
        queue_present_indicator=True,
        maximum_queue_length=3,
        average_queue_length=1.5,
        queue_duration_hours=2.0,
        average_waiting_time_hours=None,
        maximum_waiting_time_hours=None,
        vehicles_waiting_count=4,
        vehicles_not_started_count=2,
        vehicles_with_unmet_energy_count=3,
        charger_capacity_vs_demand_balance=-2,
        required_charger_count=None,
        additional_chargers_required=None,
        primary_constraint_reason="mixed",
    )
    metrics_b = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=1200.0,
        capacity_utilization=100.0,
        delivered_energy=1125.0,
        unmet_energy=0.0,
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
        harmonic_risk_level="low",
        current_imbalance_risk_level="low",
        overall_pq_risk_level="low",
        peak_harmonic_risk_score=32.0,
        harmonic_risk_duration_hours=0.5,
        peak_current_imbalance_percent=14.0,
        imbalance_duration_hours=0.0,
        overall_pq_risk_score=26.0,
        power_quality_warning_count=1,
        average_charger_utilization_percent=50.0,
        peak_charger_utilization_percent=80.0,
        average_occupied_charger_count=2.0,
        peak_occupied_charger_count=3,
        queue_present_indicator=False,
        maximum_queue_length=1,
        average_queue_length=0.5,
        queue_duration_hours=0.5,
        average_waiting_time_hours=0.25,
        maximum_waiting_time_hours=0.5,
        vehicles_waiting_count=1,
        vehicles_not_started_count=0,
        vehicles_with_unmet_energy_count=1,
        charger_capacity_vs_demand_balance=0,
        required_charger_count=4,
        additional_chargers_required=1,
        primary_constraint_reason="charger_availability",
    )
    comparison_metrics = ScenarioComparisonMetrics(
        peak_load_difference_kw=200.0,
        peak_load_change_percent=20.0,
        capacity_utilization_difference_percentage_points=20.0,
        capacity_utilization_change_percent=25.0,
        delivered_energy_difference_kwh=375.0,
        delivered_energy_change_percent=50.0,
        unmet_energy_difference_kwh=-250.0,
        unmet_energy_change_percent=-100.0,
        average_transformer_loading_percent_difference=-24.0,
        peak_transformer_loading_percent_difference=-26.0,
        transformer_overload_duration_hours_difference=-1.5,
        transformer_maximum_overload_kw_difference=-18.0,
        maximum_feeder_loading_percent_difference=-25.0,
        overloaded_feeder_count_difference=-2,
        peak_harmonic_risk_score_difference=-32.0,
        harmonic_risk_duration_hours_difference=-1.5,
        peak_current_imbalance_percent_difference=-10.0,
        imbalance_duration_hours_difference=-1.0,
        overall_pq_risk_score_difference=-32.0,
        power_quality_warning_count_difference=-2,
        average_occupied_charger_count_difference=-1.5,
        peak_occupied_charger_count_difference=-2,
        maximum_queue_length_difference=-2,
        average_queue_length_difference=-1.0,
        queue_duration_hours_difference=-1.5,
        average_waiting_time_hours_difference=None,
        maximum_waiting_time_hours_difference=None,
        vehicles_waiting_count_difference=-3,
        vehicles_not_started_count_difference=-2,
        vehicles_with_unmet_energy_count_difference=-2,
        charger_capacity_vs_demand_balance_difference=2,
        required_charger_count_difference=None,
        additional_chargers_required_difference=None,
    )

    detailed_sections = render_scenario_ab_detailed_sections(
        metrics_a,
        metrics_b,
        comparison_metrics,
        scenario_a_label="Heavy-duty",
        scenario_b_label="Workplace Charging",
    )
    visible_text = " ".join(_collect_text(detailed_sections))

    assert "Energy & Performance" in visible_text
    assert "Infrastructure" in visible_text
    assert "Queueing" in visible_text
    assert "Grid" in visible_text
    assert "Power Quality" in visible_text
    assert "Decision Summary" in visible_text
    assert "Biggest Improvements" in visible_text
    assert "Key Trade-offs" in visible_text
    assert "Unmet energy (kWh) -250.0 kWh" in visible_text
    assert "A 250.0 kWh -> B 0.0 kWh" in visible_text
    assert "Peak load (kW) +200.0 kW" in visible_text
    assert "A 1,000.0 kW -> B 1,200.0 kW" in visible_text
    assert "Focus:" not in visible_text
    assert "Select a decision area to view detailed evidence." in visible_text
    assert (
        _find_component_by_id(
            detailed_sections,
            "scenario-ab-decision-summary",
        )
        is not None
    )
    decision_summary = _find_component_by_id(
        detailed_sections,
        "scenario-ab-decision-summary",
    )
    decision_summary_text = " ".join(_collect_text(decision_summary))
    assert "Higher:" not in decision_summary_text
    assert "Lower:" not in decision_summary_text
    assert "Relative change:" not in decision_summary_text
    assert _find_component_by_id(
        detailed_sections,
        "scenario-ab-biggest-improvements",
    ) is not None
    assert _find_component_by_id(
        detailed_sections,
        "scenario-ab-key-trade-offs",
    ) is not None
    assert (
        _find_component_by_id(
            detailed_sections,
            "scenario-ab-decision-area-summary",
        )
        is None
    )
    assert _find_component_by_id(
        detailed_sections,
        "scenario-ab-difference-overview-chart",
    ) is None
    assert _find_component_by_id(detailed_sections, "scenario-ab-occupancy-chart") is None
    assert _find_component_by_id(detailed_sections, "scenario-ab-queue-chart") is None
    assert _find_component_by_id(detailed_sections, "scenario-ab-pq-risk-chart") is None

    energy_section = _find_component_by_id(
        detailed_sections,
        "scenario-ab-detail-section-energy_performance",
    )
    infrastructure_section = _find_component_by_id(
        detailed_sections,
        "scenario-ab-detail-section-infrastructure",
    )
    queueing_section = _find_component_by_id(
        detailed_sections,
        "scenario-ab-detail-section-queueing",
    )
    grid_section = _find_component_by_id(
        detailed_sections,
        "scenario-ab-detail-section-grid",
    )
    power_quality_section = _find_component_by_id(
        detailed_sections,
        "scenario-ab-detail-section-power_quality",
    )
    assert energy_section is not None
    assert infrastructure_section is not None
    assert queueing_section is not None
    assert grid_section is not None
    assert power_quality_section is not None
    assert (
        _find_component_by_id(
            detailed_sections,
            "scenario-ab-detail-card-grid",
        )
        is not None
    )
    assert _find_component_by_id(detailed_sections, "scenario-ab-comparison-workspace") is not None
    assert _find_component_by_id(detailed_sections, "scenario-ab-evidence-panel") is not None
    assert (
        _find_component_by_id(
            detailed_sections,
            "scenario-ab-evidence-panel-empty-state",
        )
        is not None
    )
    assert (
        _find_component_by_id(
            detailed_sections,
            "scenario-ab-section-badge-energy_performance",
        ).children
        == "Mixed"
    )
    assert (
        _find_component_by_id(
            detailed_sections,
            "scenario-ab-section-badge-grid",
        ).children
        == "Improvement"
    )
    assert (
        "Scenario B improves some energy & performance outcomes but introduces "
        "trade-offs, led by Unmet energy (kWh)." in visible_text
    )
    assert (
        "Scenario B shows a strong improvement signal in grid, led by Peak "
        "transformer loading (%)." in visible_text
    )
    assert "Select to open supporting evidence." not in visible_text

    assert (
        _find_component_by_id(
            detailed_sections,
            "scenario-ab-section-content-infrastructure",
        )
        is None
    )

    selected_infrastructure_sections = render_scenario_ab_detailed_sections(
        metrics_a,
        metrics_b,
        comparison_metrics,
        selected_section_id="infrastructure",
        scenario_a_label="Heavy-duty",
        scenario_b_label="Workplace Charging",
    )
    selected_text = " ".join(_collect_text(selected_infrastructure_sections))
    assert "Evidence shown in the panel." not in selected_text
    assert "Focus:" not in selected_text
    assert "Charger capacity vs demand balance" in selected_text
    assert "↑ 2 chargers" in selected_text
    assert "A -2 chargers -> B 0 chargers" in selected_text
    assert "Required charger count" not in selected_text
    assert "Additional chargers required" not in selected_text
    assert "Top Drivers" in selected_text
    assert "Supporting Facts" in selected_text
    assert "Main Evidence Chart" not in selected_text
    assert "Primary constraint reason" in selected_text
    assert "Physical charger availability is limiting" in selected_text
    assert "Occupied-charger traces are unavailable" in selected_text
    assert "Not available" not in selected_text

    evidence_panel = _find_component_by_id(
        selected_infrastructure_sections,
        "scenario-ab-evidence-panel",
    )
    assert evidence_panel is not None
    evidence_panel_text = " ".join(_collect_text(evidence_panel))
    assert "Scenario B" not in evidence_panel_text
    evidence_panel_header = evidence_panel.children[1]
    evidence_panel_title = evidence_panel_header.children[0]
    assert evidence_panel_title.children == "Infrastructure"
    assert evidence_panel_title.style["fontSize"] == "1.35rem"
    assert evidence_panel_title.style["fontWeight"] == "700"

    infrastructure_content = _find_component_by_id(
        selected_infrastructure_sections,
        "scenario-ab-section-content-infrastructure",
    )
    assert infrastructure_content is not None
    infrastructure_text = " ".join(_collect_text(infrastructure_content))
    assert "Top Drivers" in infrastructure_text
    assert "Supporting Facts" in infrastructure_text
    top_drivers_block = infrastructure_content.children[0]
    assert "scenario-ab-evidence-block--drivers" in top_drivers_block.className
    top_drivers_heading = top_drivers_block.children[0]
    assert top_drivers_heading.children == "Top Drivers"
    assert top_drivers_heading.style["fontSize"] == "1.05rem"
    assert top_drivers_heading.style["fontWeight"] == "700"
    top_drivers_grid = top_drivers_block.children[1]
    assert "scenario-ab-evidence-grid--drivers" in top_drivers_grid.className
    assert "scenario-ab-evidence-card--driver" in top_drivers_grid.children[0].className

    chart_block = infrastructure_content.children[1]
    assert "scenario-ab-evidence-block--chart" in chart_block.className
    chart_content = chart_block.children[0]
    assert "scenario-ab-evidence-chart-block" in chart_content.className
    assert chart_content.children[0].children == "Occupied Chargers Over Time"
    assert "scenario-ab-evidence-chart-title" in chart_content.children[0].className
    chart_shell = chart_content.children[1]
    assert "scenario-ab-evidence-chart-shell" in chart_shell.className
    assert chart_shell.style["width"] == "100%"

    supporting_facts_block = infrastructure_content.children[2]
    assert "scenario-ab-evidence-block--facts" in supporting_facts_block.className
    supporting_facts_heading = supporting_facts_block.children[0]
    assert supporting_facts_heading.children == "Supporting Facts"
    assert supporting_facts_heading.style["fontSize"] == "1.05rem"
    assert supporting_facts_heading.style["fontWeight"] == "700"
    supporting_facts_grid = supporting_facts_block.children[1]
    assert "scenario-ab-evidence-grid--facts" in supporting_facts_grid.className
    assert (
        "scenario-ab-evidence-card--fact"
        in supporting_facts_grid.children[0].className
    )

    selected_queueing_sections = render_scenario_ab_detailed_sections(
        metrics_a,
        metrics_b,
        comparison_metrics,
        selected_section_id="queueing",
        scenario_a_label="Heavy-duty",
        scenario_b_label="Workplace Charging",
    )
    queueing_content = _find_component_by_id(
        selected_queueing_sections,
        "scenario-ab-section-content-queueing",
    )
    assert queueing_content is not None
    queueing_chart_block = queueing_content.children[1].children[0]
    assert "scenario-ab-evidence-chart-block" in queueing_chart_block.className
    assert queueing_chart_block.children[0].children == "Queue Length Over Time"
    assert (
        "scenario-ab-evidence-chart-title"
        in queueing_chart_block.children[0].className
    )
    queueing_chart_shell = queueing_chart_block.children[1]
    assert "scenario-ab-evidence-chart-shell" in queueing_chart_shell.className
    assert queueing_chart_shell.style["width"] == "100%"

    selected_power_quality_sections = render_scenario_ab_detailed_sections(
        metrics_a,
        metrics_b,
        comparison_metrics,
        selected_section_id="power_quality",
        scenario_a_label="Heavy-duty",
        scenario_b_label="Workplace Charging",
    )
    power_quality_content = _find_component_by_id(
        selected_power_quality_sections,
        "scenario-ab-section-content-power_quality",
    )
    assert power_quality_content is not None
    power_quality_chart_block = power_quality_content.children[1].children[0]
    assert "scenario-ab-evidence-chart-block" in power_quality_chart_block.className
    assert power_quality_chart_block.children[0].children == "Overall PQ Risk Over Time"
    power_quality_chart_shell = power_quality_chart_block.children[1]
    assert "scenario-ab-evidence-chart-shell" in power_quality_chart_shell.className
    assert power_quality_chart_shell.style["width"] == "100%"

def test_dashboard_scenario_ab_evidence_metric_cards_match_kpi_hierarchy():
    metric = ScenarioComparisonDisplayMetric(
        metric_id="charger_capacity_vs_demand_balance",
        label="Charger capacity vs demand balance",
        value_format="charger_count_0",
        scenario_a_value=-2,
        scenario_b_value=0,
        change_format="charger_count_0_signed",
        change_value=2,
        preferred_direction="higher",
    )

    card = dashboard_callbacks_module._render_scenario_ab_evidence_metric_card(
        metric,
        scenario_a_label="Heavy-duty",
        scenario_b_label="Workplace Charging",
        card_style=dashboard_callbacks_module.SCENARIO_AB_EVIDENCE_DRIVER_CARD_STYLE,
        card_class_name="scenario-ab-evidence-card scenario-ab-evidence-card--driver",
    )

    assert "scenario-ab-evidence-card--driver" in card.className
    assert card.style["padding"] == "0.95rem 1rem"
    assert card.style["minHeight"] == "8.75rem"
    assert card.style["backgroundColor"] == dashboard_callbacks_module.STATUS_GREEN_BACKGROUND
    assert (
        card.style["boxShadow"]
        == f"inset 3px 0 0 {dashboard_callbacks_module.STATUS_GREEN}"
    )

    label, primary_value, baseline_context = card.children
    assert label.children == "Charger capacity vs demand balance"
    assert label.className == "scenario-ab-evidence-card-label"
    assert label.style["fontSize"] == "0.8rem"
    assert primary_value.children == "↑ 2 chargers"
    assert primary_value.className == "scenario-ab-evidence-card-value"
    assert primary_value.style["fontWeight"] == "700"
    assert primary_value.style["lineHeight"] == "1.15"
    assert primary_value.style["fontSize"] == "clamp(1.45rem, 1.2rem + 0.55vw, 1.95rem)"
    assert baseline_context.className == "scenario-ab-evidence-card-context"
    assert " ".join(" ".join(_collect_text(baseline_context)).split()) == (
        "A -2 chargers -> B 0 chargers"
    )

def test_dashboard_scenario_ab_evidence_keeps_near_zero_deltas_neutral_and_out_of_top_drivers():
    metrics_a = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        average_transformer_loading_percent=70.0,
        peak_transformer_loading_percent=96.0,
        transformer_overload_indicator=False,
        transformer_overload_duration_hours=0.0,
        transformer_maximum_overload_kw=0.0,
        transformer_thermal_risk_level="low",
        maximum_feeder_loading_percent=84.0,
        feeder_overload_indicator=False,
        overloaded_feeder_count=0,
        highest_feeder_thermal_risk_level="low",
    )
    metrics_b = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        average_transformer_loading_percent=64.0,
        peak_transformer_loading_percent=84.0,
        transformer_overload_indicator=False,
        transformer_overload_duration_hours=0.0,
        transformer_maximum_overload_kw=0.0,
        transformer_thermal_risk_level="low",
        maximum_feeder_loading_percent=84.04,
        feeder_overload_indicator=False,
        overloaded_feeder_count=0,
        highest_feeder_thermal_risk_level="low",
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
        average_transformer_loading_percent_difference=-6.0,
        peak_transformer_loading_percent_difference=-12.0,
        transformer_overload_duration_hours_difference=0.0,
        transformer_maximum_overload_kw_difference=0.0,
        maximum_feeder_loading_percent_difference=0.04,
        overloaded_feeder_count_difference=0,
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

    selected_sections = render_scenario_ab_detailed_sections(
        metrics_a,
        metrics_b,
        comparison_metrics,
        selected_section_id="grid",
        scenario_a_label="Scenario A",
        scenario_b_label="Scenario B",
    )

    grid_content = _find_component_by_id(
        selected_sections,
        "scenario-ab-section-content-grid",
    )
    assert grid_content is not None

    top_drivers_grid = grid_content.children[0].children[1]
    assert len(top_drivers_grid.children) == 2
    top_driver_text = " ".join(" ".join(_collect_text(top_drivers_grid)).split())
    assert "Peak transformer loading (%)" in top_driver_text
    assert "Average transformer loading (%)" in top_driver_text
    assert "Maximum feeder loading (%)" not in top_driver_text

    supporting_facts_grid = grid_content.children[-1].children[1]
    supporting_cards = list(supporting_facts_grid.children)
    feeder_loading_card = next(
        card
        for card in supporting_cards
        if "Maximum feeder loading (%)" in " ".join(_collect_text(card))
    )
    feeder_loading_text = " ".join(" ".join(_collect_text(feeder_loading_card)).split())
    assert "0.0 pp" in feeder_loading_text
    assert "↑ 0.0 pp" not in feeder_loading_text
    assert "↓ 0.0 pp" not in feeder_loading_text
    assert "A 84.0% -> B 84.0%" in feeder_loading_text

def test_dashboard_collapses_low_signal_scenario_ab_sections_by_default():
    metrics_a = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=400.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        average_transformer_loading_percent=60.0,
        peak_transformer_loading_percent=80.0,
        transformer_overload_indicator=False,
        transformer_overload_duration_hours=0.0,
        transformer_maximum_overload_kw=0.0,
        transformer_thermal_risk_level="low",
        maximum_feeder_loading_percent=55.0,
        feeder_overload_indicator=False,
        overloaded_feeder_count=0,
        highest_feeder_thermal_risk_level="low",
        harmonic_risk_level="low",
        current_imbalance_risk_level="low",
        overall_pq_risk_level="low",
        peak_harmonic_risk_score=10.0,
        harmonic_risk_duration_hours=0.0,
        peak_current_imbalance_percent=5.0,
        imbalance_duration_hours=0.0,
        overall_pq_risk_score=12.0,
        power_quality_warning_count=0,
        average_charger_utilization_percent=50.0,
        peak_charger_utilization_percent=70.0,
        average_occupied_charger_count=2.0,
        peak_occupied_charger_count=3,
        queue_present_indicator=False,
        maximum_queue_length=0,
        average_queue_length=0.0,
        queue_duration_hours=0.0,
        average_waiting_time_hours=None,
        maximum_waiting_time_hours=None,
        vehicles_waiting_count=0,
        vehicles_not_started_count=0,
        vehicles_with_unmet_energy_count=0,
        charger_capacity_vs_demand_balance=1,
        required_charger_count=None,
        additional_chargers_required=None,
        primary_constraint_reason="none",
    )
    metrics_b = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=400.0,
        capacity_utilization=80.0,
        delivered_energy=1000.0,
        unmet_energy=0.0,
        average_transformer_loading_percent=60.0,
        peak_transformer_loading_percent=80.0,
        transformer_overload_indicator=False,
        transformer_overload_duration_hours=0.0,
        transformer_maximum_overload_kw=0.0,
        transformer_thermal_risk_level="low",
        maximum_feeder_loading_percent=55.0,
        feeder_overload_indicator=False,
        overloaded_feeder_count=0,
        highest_feeder_thermal_risk_level="low",
        harmonic_risk_level="low",
        current_imbalance_risk_level="low",
        overall_pq_risk_level="low",
        peak_harmonic_risk_score=10.0,
        harmonic_risk_duration_hours=0.0,
        peak_current_imbalance_percent=5.0,
        imbalance_duration_hours=0.0,
        overall_pq_risk_score=12.0,
        power_quality_warning_count=0,
        average_charger_utilization_percent=50.0,
        peak_charger_utilization_percent=70.0,
        average_occupied_charger_count=2.0,
        peak_occupied_charger_count=3,
        queue_present_indicator=False,
        maximum_queue_length=0,
        average_queue_length=0.0,
        queue_duration_hours=0.0,
        average_waiting_time_hours=None,
        maximum_waiting_time_hours=None,
        vehicles_waiting_count=0,
        vehicles_not_started_count=0,
        vehicles_with_unmet_energy_count=0,
        charger_capacity_vs_demand_balance=1,
        required_charger_count=None,
        additional_chargers_required=None,
        primary_constraint_reason="none",
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

    detailed_sections = render_scenario_ab_detailed_sections(
        metrics_a,
        metrics_b,
        comparison_metrics,
        scenario_a_label="Scenario A",
        scenario_b_label="Scenario B",
    )

    assert (
        _find_component_by_id(
            detailed_sections,
            "scenario-ab-detail-section-grid",
        )
        is not None
    )
    assert (
        _find_component_by_id(
            detailed_sections,
            "scenario-ab-section-badge-grid",
        ).children
        == "Minimal change"
    )
    visible_text = " ".join(_collect_text(detailed_sections))
    assert "Minimal change" in visible_text
    assert "Select to verify unchanged metrics." not in visible_text
    assert "Select a decision area to view detailed evidence." in visible_text
    assert (
        _find_component_by_id(
            detailed_sections,
            "scenario-ab-evidence-panel-empty-state",
        )
        is not None
    )

    selected_sections = render_scenario_ab_detailed_sections(
        metrics_a,
        metrics_b,
        comparison_metrics,
        selected_section_id="grid",
        scenario_a_label="Scenario A",
        scenario_b_label="Scenario B",
    )
    selected_text = " ".join(_collect_text(selected_sections))
    assert "This decision area stayed materially aligned" not in selected_text
    assert "Verification shown in the panel." not in selected_text
    assert "Supporting Facts" in selected_text
    assert "Transformer Loading Over Time" not in selected_text
    assert (
        _find_component_by_id(
            selected_sections,
            "scenario-ab-section-content-grid",
        )
        is not None
    )
    assert (
        _find_component_by_id(
            selected_sections,
            "scenario-ab-transformer-loading-chart",
        )
        is None
    )
    evidence_panel = _find_component_by_id(
        selected_sections,
        "scenario-ab-evidence-panel",
    )
    assert evidence_panel is not None
    evidence_panel_title = evidence_panel.children[1].children[0]
    assert evidence_panel_title.children == "Grid"
    assert evidence_panel_title.style["fontSize"] == "1.35rem"
    supporting_facts_block = _find_component_by_id(
        selected_sections,
        "scenario-ab-section-content-grid",
    ).children[0]
    assert supporting_facts_block.children[0].children == "Supporting Facts"
    assert supporting_facts_block.children[0].style["fontSize"] == "1.05rem"

def test_dashboard_scenario_ab_infrastructure_evidence_hides_non_comparable_charger_recommendations():
    metrics_a = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        average_occupied_charger_count=6.0,
        peak_occupied_charger_count=8,
        charger_capacity_vs_demand_balance=-40,
        required_charger_count=50,
        additional_chargers_required=40,
        primary_constraint_reason="charger_availability",
    )
    metrics_b = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        average_occupied_charger_count=5.0,
        peak_occupied_charger_count=7,
        charger_capacity_vs_demand_balance=-20,
        required_charger_count=None,
        additional_chargers_required=None,
        primary_constraint_reason="charging_window",
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
        average_occupied_charger_count_difference=-1.0,
        peak_occupied_charger_count_difference=-1,
        charger_capacity_vs_demand_balance_difference=20,
        required_charger_count_difference=None,
        additional_chargers_required_difference=None,
    )

    detailed_sections = render_scenario_ab_detailed_sections(
        metrics_a,
        metrics_b,
        comparison_metrics,
        selected_section_id="infrastructure",
        scenario_a_label="Scenario A",
        scenario_b_label="Scenario B",
    )
    visible_text = " ".join(" ".join(_collect_text(detailed_sections)).split())

    assert "State changed" not in visible_text
    assert "Required charger count" not in visible_text
    assert "Additional chargers required" not in visible_text
    assert "Charger capacity vs demand balance" in visible_text
    assert "Primary constraint reason" in visible_text

def test_dashboard_scenario_ab_infrastructure_evidence_shows_numeric_recommendation_deltas_when_defined():
    metrics_a = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        average_occupied_charger_count=6.0,
        peak_occupied_charger_count=8,
        charger_capacity_vs_demand_balance=-40,
        required_charger_count=50,
        additional_chargers_required=40,
        primary_constraint_reason="charger_availability",
    )
    metrics_b = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        average_occupied_charger_count=7.0,
        peak_occupied_charger_count=9,
        charger_capacity_vs_demand_balance=-80,
        required_charger_count=90,
        additional_chargers_required=80,
        primary_constraint_reason="charger_availability",
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
        average_occupied_charger_count_difference=1.0,
        peak_occupied_charger_count_difference=1,
        charger_capacity_vs_demand_balance_difference=-40,
        required_charger_count_difference=None,
        additional_chargers_required_difference=None,
    )

    detailed_sections = render_scenario_ab_detailed_sections(
        metrics_a,
        metrics_b,
        comparison_metrics,
        selected_section_id="infrastructure",
        scenario_a_label="Scenario A",
        scenario_b_label="Scenario B",
    )
    visible_text = " ".join(" ".join(_collect_text(detailed_sections)).split())

    assert "Required charger count" in visible_text
    assert "↑ 40 chargers" in visible_text
    assert "A 50 chargers -> B 90 chargers" in visible_text
    assert "Additional chargers required" in visible_text
    assert "A 40 chargers -> B 80 chargers" in visible_text
    assert "State changed" not in visible_text

def test_dashboard_builds_scenario_ab_charger_availability_rows_from_metrics():
    metrics_a = Metrics(
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
        average_charger_utilization_percent=75.0,
        peak_charger_utilization_percent=100.0,
        average_occupied_charger_count=3.5,
        peak_occupied_charger_count=5,
        queue_present_indicator=True,
        maximum_queue_length=3,
        average_queue_length=1.5,
        queue_duration_hours=2.0,
        average_waiting_time_hours=None,
        maximum_waiting_time_hours=None,
        vehicles_waiting_count=4,
        vehicles_not_started_count=2,
        vehicles_with_unmet_energy_count=3,
        charger_capacity_vs_demand_balance=-2,
        required_charger_count=None,
        additional_chargers_required=None,
        primary_constraint_reason="mixed",
    )
    metrics_b = Metrics(
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
        average_charger_utilization_percent=50.0,
        peak_charger_utilization_percent=80.0,
        average_occupied_charger_count=2.0,
        peak_occupied_charger_count=3,
        queue_present_indicator=False,
        maximum_queue_length=1,
        average_queue_length=0.5,
        queue_duration_hours=0.5,
        average_waiting_time_hours=0.25,
        maximum_waiting_time_hours=0.5,
        vehicles_waiting_count=1,
        vehicles_not_started_count=0,
        vehicles_with_unmet_energy_count=1,
        charger_capacity_vs_demand_balance=0,
        required_charger_count=4,
        additional_chargers_required=1,
        primary_constraint_reason="charger_availability",
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
        average_transformer_loading_percent_difference=-24.0,
        peak_transformer_loading_percent_difference=-26.0,
        transformer_overload_duration_hours_difference=-1.5,
        transformer_maximum_overload_kw_difference=-18.0,
        maximum_feeder_loading_percent_difference=-25.0,
        overloaded_feeder_count_difference=-2,
        average_occupied_charger_count_difference=-1.5,
        peak_occupied_charger_count_difference=-2,
        maximum_queue_length_difference=-2,
        average_queue_length_difference=-1.0,
        queue_duration_hours_difference=-1.5,
        average_waiting_time_hours_difference=None,
        maximum_waiting_time_hours_difference=None,
        vehicles_waiting_count_difference=-3,
        vehicles_not_started_count_difference=-2,
        vehicles_with_unmet_energy_count_difference=-2,
        charger_capacity_vs_demand_balance_difference=2,
        required_charger_count_difference=None,
        additional_chargers_required_difference=None,
    )

    rows = build_scenario_ab_charger_availability_rows(
        metrics_a,
        metrics_b,
        comparison_metrics,
    )
    rendered_rows = [
        tuple(" ".join(_collect_text(cell)) for cell in row)
        for row in rows
    ]

    assert (
        "Average transformer loading (%)",
        "92.0%",
        "68.0%",
        "-24.0 pp",
    ) in rendered_rows
    assert (
        "Transformer overload",
        "Overloaded",
        "Not overloaded",
        "Not applicable",
    ) in rendered_rows
    assert (
        "Maximum transformer overload (kW)",
        "18.0 kW",
        "0.0 kW",
        "-18.0 kW",
    ) in rendered_rows
    assert (
        "Maximum feeder loading (%)",
        "104.0%",
        "79.0%",
        "-25.0 pp",
    ) in rendered_rows
    assert (
        "Highest feeder thermal risk",
        "High",
        "Low",
        "Not applicable",
    ) in rendered_rows
    assert (
        "Average charger utilization (%)",
        "75.0%",
        "50.0%",
        "Not applicable",
    ) in rendered_rows
    assert (
        "Average occupied chargers",
        "3.5 chargers",
        "2.0 chargers",
        "-1.5 chargers",
    ) in rendered_rows
    assert (
        "Queue present",
        "Present",
        "Not present",
        "Not applicable",
    ) in rendered_rows
    assert (
        "Average waiting time (h)",
        "Not available",
        "0.2 h",
        "Not available",
    ) in rendered_rows
    assert (
        "Required charger count",
        "Not applicable",
        "4 chargers",
        "Not available",
    ) in rendered_rows
    assert (
        "Primary constraint reason",
        "Multiple modeled constraints are limiting",
        "Physical charger availability is limiting",
        "Not applicable",
    ) in rendered_rows

def test_dashboard_hides_pq_chart_when_scenario_ab_traces_are_nearly_identical():
    metrics_a = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        overall_pq_risk_level="low",
        overall_pq_risk_score=24.0,
        overall_pq_risk_score_by_timestep=[24.0, 25.0, 24.0],
    )
    metrics_b = Metrics(
        total_daily_energy=0.0,
        available_capacity=0.0,
        energy_delivery_sufficient=True,
        overall_pq_risk_level="low",
        overall_pq_risk_score=24.5,
        overall_pq_risk_score_by_timestep=[24.5, 25.0, 24.0],
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
        overall_pq_risk_score_difference=0.5,
        power_quality_warning_count_difference=0,
    )

    detailed_sections = render_scenario_ab_detailed_sections(
        metrics_a,
        metrics_b,
        comparison_metrics,
        selected_section_id="power_quality",
    )
    visible_text = " ".join(_collect_text(detailed_sections))

    assert _find_component_by_id(detailed_sections, "scenario-ab-pq-risk-chart") is None
    assert "nearly identical overall PQ risk traces" in visible_text

def test_dashboard_renders_scenario_ab_charger_availability_table_from_metrics():
    metrics_a = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        average_transformer_loading_percent=75.0,
        peak_transformer_loading_percent=95.0,
        transformer_overload_indicator=True,
        transformer_overload_duration_hours=1.0,
        transformer_maximum_overload_kw=12.0,
        transformer_thermal_risk_level="moderate",
        maximum_feeder_loading_percent=90.0,
        feeder_overload_indicator=True,
        overloaded_feeder_count=1,
        highest_feeder_thermal_risk_level="moderate",
        harmonic_risk_level="high",
        current_imbalance_risk_level="moderate",
        overall_pq_risk_level="high",
        average_charger_utilization_percent=60.0,
        average_occupied_charger_count=3.0,
        queue_present_indicator=True,
        maximum_queue_length=2,
        average_waiting_time_hours=0.5,
        vehicles_not_started_count=1,
        required_charger_count=5,
        additional_chargers_required=2,
        primary_constraint_reason="charger_availability",
    )
    metrics_b = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        average_transformer_loading_percent=60.0,
        peak_transformer_loading_percent=77.0,
        transformer_overload_indicator=False,
        transformer_overload_duration_hours=0.0,
        transformer_maximum_overload_kw=0.0,
        transformer_thermal_risk_level="low",
        maximum_feeder_loading_percent=70.0,
        feeder_overload_indicator=False,
        overloaded_feeder_count=0,
        highest_feeder_thermal_risk_level="low",
        harmonic_risk_level="low",
        current_imbalance_risk_level="low",
        overall_pq_risk_level="low",
        average_charger_utilization_percent=45.0,
        average_occupied_charger_count=2.0,
        queue_present_indicator=False,
        maximum_queue_length=0,
        average_waiting_time_hours=None,
        vehicles_not_started_count=0,
        required_charger_count=None,
        additional_chargers_required=None,
        primary_constraint_reason="charging_window",
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
        average_transformer_loading_percent_difference=-15.0,
        peak_transformer_loading_percent_difference=-18.0,
        transformer_overload_duration_hours_difference=-1.0,
        transformer_maximum_overload_kw_difference=-12.0,
        maximum_feeder_loading_percent_difference=-20.0,
        overloaded_feeder_count_difference=-1,
        average_occupied_charger_count_difference=-1.0,
        peak_occupied_charger_count_difference=0,
        maximum_queue_length_difference=-2,
        average_queue_length_difference=0.0,
        queue_duration_hours_difference=0.0,
        average_waiting_time_hours_difference=None,
        maximum_waiting_time_hours_difference=None,
        vehicles_waiting_count_difference=0,
        vehicles_not_started_count_difference=-1,
        vehicles_with_unmet_energy_count_difference=0,
        charger_capacity_vs_demand_balance_difference=0,
        required_charger_count_difference=None,
        additional_chargers_required_difference=None,
    )

    table = render_scenario_ab_charger_availability_table(
        metrics_a,
        metrics_b,
        comparison_metrics,
        scenario_a_label="Heavy-duty",
        scenario_b_label="Workplace Charging",
    )
    visible_text = " ".join(_collect_text(table))

    assert "Metric" in visible_text
    assert "Heavy-duty" in visible_text
    assert "Workplace Charging" in visible_text
    assert "Difference" in visible_text
    assert "Average transformer loading (%)" in visible_text
    assert "-15.0 pp" in visible_text
    assert "Transformer overload" in visible_text
    assert "Overloaded" in visible_text
    assert "Not overloaded" in visible_text
    assert "Highest feeder thermal risk" in visible_text
    assert "Harmonic risk level" in visible_text
    assert "Current imbalance risk level" in visible_text
    assert "Overall PQ risk level" in visible_text
    assert "Average charger utilization (%)" in visible_text
    assert "60.0%" in visible_text
    assert "45.0%" in visible_text
    assert "Average occupied chargers" in visible_text
    assert "-1.0 chargers" in visible_text
    assert "Queue present" in visible_text
    assert "Present" in visible_text
    assert "Not present" in visible_text
    assert "Average waiting time (h)" in visible_text
    assert visible_text.count("Not available") >= 2
    assert visible_text.count("Not applicable") >= 6
    assert "Primary constraint reason" in visible_text
    assert "Physical charger availability is limiting" in visible_text
    assert "Available charging time is limiting" in visible_text
    assert (
        _find_component_by_title(
            table,
            ADDITIONAL_CHARGERS_NOT_APPLICABLE_HELPER,
        )
        is not None
    )

def test_dashboard_scenario_ab_charger_availability_outputs_render_safe_legacy_state():
    metrics_a = metrics_from_dict(
        {
            "total_daily_energy": 1000.0,
            "available_capacity": 500.0,
            "energy_delivery_sufficient": True,
            "peak_load": 321.0,
            "capacity_utilization": 64.2,
            "delivered_energy": 1000.0,
            "unmet_energy": 0.0,
            "annual_energy": 365000.0,
        }
    )
    metrics_b = metrics_from_dict(
        {
            "total_daily_energy": 1200.0,
            "available_capacity": 600.0,
            "energy_delivery_sufficient": True,
            "peak_load": 400.0,
            "capacity_utilization": 66.7,
            "delivered_energy": 1200.0,
            "unmet_energy": 0.0,
            "annual_energy": 438000.0,
        }
    )
    comparison_metrics = scenario_comparison_metrics_from_dict(
        {
            "peak_load_difference_kw": 79.0,
            "peak_load_change_percent": 24.6,
            "capacity_utilization_difference_percentage_points": 2.5,
            "capacity_utilization_change_percent": 3.9,
            "delivered_energy_difference_kwh": 200.0,
            "delivered_energy_change_percent": 20.0,
            "unmet_energy_difference_kwh": 0.0,
            "unmet_energy_change_percent": None,
        }
    )

    table = render_scenario_ab_charger_availability_table(
        metrics_a,
        metrics_b,
        comparison_metrics,
        scenario_a_label="Current Scenario",
        scenario_b_label="Comparison Scenario",
    )
    occupancy_figure = create_scenario_ab_occupancy_figure(
        metrics_a,
        metrics_b,
        scenario_a_label="Current Scenario",
        scenario_b_label="Comparison Scenario",
    )
    queue_figure = create_scenario_ab_queue_figure(
        metrics_a,
        metrics_b,
        scenario_a_label="Current Scenario",
        scenario_b_label="Comparison Scenario",
    )
    pq_figure = create_scenario_ab_power_quality_figure(
        metrics_a,
        metrics_b,
        scenario_a_label="Current Scenario",
        scenario_b_label="Comparison Scenario",
    )
    visible_text = " ".join(_collect_text(table))

    assert "0.0%" in visible_text
    assert "0.0 chargers" in visible_text
    assert "No primary charger-planning constraint identified" in visible_text
    assert len(occupancy_figure.data) == 0
    assert occupancy_figure.layout.autosize is True
    assert occupancy_figure.layout.annotations[0].text == (
        "Current Scenario/Comparison Scenario occupied-charger series unavailable for this result."
    )
    assert len(queue_figure.data) == 0
    assert queue_figure.layout.autosize is True
    assert queue_figure.layout.annotations[0].text == (
        "Current Scenario/Comparison Scenario queue-length series unavailable for this result."
    )
    assert len(pq_figure.data) == 0
    assert pq_figure.layout.autosize is True
    assert pq_figure.layout.annotations[0].text == (
        "Current Scenario/Comparison Scenario overall PQ risk series unavailable for this result."
    )

@pytest.mark.parametrize(
    (
        "scenario",
        "expected_energy_delivery_sufficient",
        "expected_connection_capacity_exceeded",
        "expected_status_message",
        "expected_identical_profiles",
    ),
    [
        pytest.param(
            Scenario(
                vehicles=10,
                daily_energy_per_vehicle=50.0,
                charger_count=2,
                charger_power=100.0,
                grid_capacity=200.0,
                charging_window_start=time(22, 0),
                charging_window_end=time(4, 0),
                charging_strategy=ChargingStrategy.SMART,
            ),
            True,
            False,
            "Configured connection capacity is adequate and daily energy "
            "demand can be delivered.",
            True,
            id="energy-sufficient-capacity-not-exceeded",
        ),
        pytest.param(
            default_scenario,
            True,
            True,
            "A connection-capacity upgrade is indicated, although daily "
            "energy demand can still be delivered.",
            False,
            id="energy-sufficient-capacity-exceeded",
        ),
        pytest.param(
            Scenario(
                vehicles=20,
                daily_energy_per_vehicle=100.0,
                charger_count=1,
                charger_power=100.0,
                grid_capacity=100.0,
                charging_window_start=time(22, 0),
                charging_window_end=time(2, 0),
            ),
            False,
            False,
            "Configured connection capacity remains adequate, but daily "
            "energy demand cannot be fully delivered within the scenario "
            "constraints.",
            True,
            id="energy-insufficient-capacity-not-exceeded",
        ),
        pytest.param(
            Scenario(
                vehicles=20,
                daily_energy_per_vehicle=100.0,
                charger_count=4,
                charger_power=100.0,
                grid_capacity=150.0,
                charging_window_start=time(22, 0),
                charging_window_end=time(2, 0),
            ),
            False,
            True,
            "A connection-capacity upgrade is indicated and daily energy "
            "demand cannot be fully delivered.",
            False,
            id="energy-insufficient-capacity-exceeded",
        ),
    ],
)
def test_dashboard_single_scenario_capacity_planning_vertical_slice_end_to_end(
    scenario,
    expected_energy_delivery_sufficient,
    expected_connection_capacity_exceeded,
    expected_status_message,
    expected_identical_profiles,
):
    (
        simulation_result,
        metrics,
        cards_text,
        charger_availability_cards_text,
        status_text,
        charger_planning_status_text,
        capacity_vs_load_figure,
        load_profile_figure,
    ) = _build_single_scenario_dashboard_slice(scenario)

    visible_cards = " ".join(cards_text)
    visible_charger_availability_cards = " ".join(
        charger_availability_cards_text
    )
    visible_status = " ".join(status_text)
    visible_charger_planning_status = " ".join(
        charger_planning_status_text
    )

    assert (
        metrics.energy_delivery_sufficient
        is expected_energy_delivery_sufficient
    )
    assert (
        metrics.connection_capacity_exceeded
        is expected_connection_capacity_exceeded
    )
    assert expected_status_message in visible_status

    assert "Simulated Peak Load" in visible_cards
    assert "Required Connection Capacity" in visible_cards
    assert "Recommended Connection Capacity" in visible_cards
    if metrics.peak_capacity_margin_kw < 0.0:
        assert "Capacity Shortfall" in visible_cards
        assert format_power_kw(abs(metrics.peak_capacity_margin_kw)) in visible_cards
    else:
        assert "Peak Capacity Margin" in visible_cards
        assert format_signed_power_kw(metrics.peak_capacity_margin_kw) in visible_cards
    assert format_power_kw(metrics.peak_load) in visible_cards
    assert (
        format_power_kw(metrics.required_connection_capacity_kw)
        in visible_cards
    )
    assert (
        format_power_kw(metrics.recommended_connection_capacity_kw)
        in visible_cards
    )
    assert "Peak capacity margin:" not in visible_cards
    assert "Configured Connection Capacity" not in visible_cards
    assert "Connection Capacity Exceeded" not in visible_cards
    assert format_connection_capacity_exceeded_status(metrics) not in visible_cards
    assert "Peak Charger Utilization" in visible_charger_availability_cards
    assert "Peak Occupied Chargers" in visible_charger_availability_cards
    assert "Maximum Queue Length" in visible_charger_availability_cards
    assert "Vehicles Not Started" in visible_charger_availability_cards
    assert "Average Charger Utilization" not in visible_charger_availability_cards
    assert "Average Occupied Chargers" not in visible_charger_availability_cards
    assert "Average Waiting Time" not in visible_charger_availability_cards
    assert "Required Charger Count" not in visible_charger_availability_cards
    assert "Planner-facing rule:" not in visible_charger_planning_status

    visible_trace_names = [
        trace.name for trace in capacity_vs_load_figure.data if trace.name is not None
    ]
    assert visible_trace_names == [
        "Delivered Charging Load",
        "Requested Charging Demand",
        "Configured Connection Capacity",
    ]
    delivered_trace = next(
        trace for trace in capacity_vs_load_figure.data if trace.name == "Delivered Charging Load"
    )
    requested_trace = next(
        trace for trace in capacity_vs_load_figure.data if trace.name == "Requested Charging Demand"
    )
    configured_capacity_trace = next(
        trace
        for trace in capacity_vs_load_figure.data
        if trace.name == "Configured Connection Capacity"
    )
    assert list(delivered_trace.y) == (
        simulation_result.delivered_load_profile_kw
    )
    assert list(requested_trace.y) == (
        simulation_result.requested_load_profile_kw
    )
    assert list(configured_capacity_trace.y) == [
        simulation_result.configured_connection_capacity_kw
    ] * len(simulation_result.delivered_load_profile_kw)
    assert list(load_profile_figure.data[0].y) == (
        simulation_result.delivered_load_profile_kw
    )

    assert len(capacity_vs_load_figure.data) == 3
    assert all(
        trace.name != "Requested Load Exceedance"
        for trace in capacity_vs_load_figure.data
    )

    assert (
        simulation_result.requested_load_profile_kw
        == simulation_result.delivered_load_profile_kw
    ) is expected_identical_profiles

def test_dashboard_capacity_planning_cards_use_completed_values_without_recalculation():
    metrics = Metrics(
        total_daily_energy=100.0,
        available_capacity=80.0,
        energy_delivery_sufficient=True,
        peak_load=12.5,
        required_connection_capacity_kw=345.0,
        recommended_connection_capacity_kw=380.0,
        planning_margin_percent=10.0,
        peak_capacity_margin_kw=-225.0,
        peak_capacity_margin_percent=-65.2,
        connection_capacity_exceeded=False,
    )
    simulation_result = SimulationResult(
        daily_energy_demand=100.0,
        configured_connection_capacity_kw=120.0,
        installed_charger_capacity_kw=210.0,
        available_site_charging_capacity_kw=80.0,
        requested_load_profile_kw=[210.0, 0.0] + [0.0] * 22,
        delivered_load_profile_kw=[80.0, 0.0] + [0.0] * 22,
    )

    visible_text = " ".join(
        _collect_text(render_capacity_planning_kpi_cards(metrics, simulation_result))
    )

    assert format_power_kw(12.5) in visible_text
    assert format_power_kw(345.0) in visible_text
    assert format_power_kw(380.0) in visible_text
    assert "Capacity Shortfall" in visible_text
    assert format_power_kw(225.0) in visible_text
    assert format_signed_power_kw(-225.0) not in visible_text
    assert format_power_kw(120.0) not in visible_text
    assert "Not exceeded" not in visible_text
    assert format_power_kw(210.0) not in visible_text

