from insights import generate_insights
from metrics import ComparisonMetrics, Metrics
from scenarios import ChargingStrategy


def test_insights_return_at_most_three_messages():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=100.0,
        energy_delivery_sufficient=True,
        capacity_utilization=95.0,
    )
    comparison_metrics = ComparisonMetrics(
        peak_reduction=150.0,
        relative_peak_reduction=37.5,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
        connection_capacity_avoided_by_smart_kw=120.0,
        exceedance_duration_reduction_hours=2.0,
    )

    insights = generate_insights(
        metrics,
        ChargingStrategy.SMART,
        comparison_metrics,
    )

    assert len(insights) == 3


def test_insights_cover_service_sufficiency_when_demand_is_met():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=100.0,
        energy_delivery_sufficient=True,
    )

    insights = generate_insights(metrics)

    assert insights[0] == "Daily charging demand can be served."


def test_insights_cover_service_sufficiency_when_demand_is_not_met():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=100.0,
        energy_delivery_sufficient=False,
    )

    insights = generate_insights(metrics)

    assert insights[0] == (
        "Daily charging demand cannot be fully served."
    )


def test_insights_summarize_positive_smart_charging_benefit():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=100.0,
        energy_delivery_sufficient=True,
    )
    comparison_metrics = ComparisonMetrics(
        peak_reduction=150.0,
        relative_peak_reduction=37.5,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
        connection_capacity_avoided_by_smart_kw=120.0,
        required_connection_capacity_difference_kw=120.0,
        recommended_connection_capacity_difference_kw=132.0,
        exceedance_duration_reduction_hours=2.0,
    )

    insights = generate_insights(
        metrics,
        ChargingStrategy.SMART,
        comparison_metrics,
    )

    assert insights[1] == (
        "Smart Charging improves the scenario versus uncontrolled charging."
    )


def test_insights_summarize_negative_smart_charging_tradeoff():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=100.0,
        energy_delivery_sufficient=True,
    )
    comparison_metrics = ComparisonMetrics(
        peak_reduction=-20.0,
        relative_peak_reduction=-5.0,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
        required_connection_capacity_difference_kw=-40.0,
        recommended_connection_capacity_difference_kw=-44.0,
        exceedance_duration_reduction_hours=-1.5,
    )

    insights = generate_insights(
        metrics,
        ChargingStrategy.SMART,
        comparison_metrics,
    )

    assert insights[1] == (
        "Smart Charging adds trade-offs in this scenario."
    )


def test_insights_summarize_limited_smart_charging_benefit():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=100.0,
        energy_delivery_sufficient=True,
    )
    comparison_metrics = ComparisonMetrics(
        peak_reduction=0.0,
        relative_peak_reduction=0.0,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
    )

    insights = generate_insights(
        metrics,
        ChargingStrategy.SMART,
        comparison_metrics,
    )

    assert insights[1] == (
        "Smart Charging adds limited planning value in this scenario."
    )


def test_insights_report_missing_smart_charging_comparison():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=100.0,
        energy_delivery_sufficient=True,
    )

    insights = generate_insights(metrics, ChargingStrategy.UNCONTROLLED)

    assert insights[1] == "Smart Charging comparison is not available for this scenario."


def test_insights_prioritize_combined_grid_and_pq_caution():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=100.0,
        energy_delivery_sufficient=True,
        transformer_overload_indicator=True,
        transformer_thermal_risk_level="moderate",
        overall_pq_risk_level="moderate",
        power_quality_warning_count=2,
    )

    insights = generate_insights(metrics)

    assert insights[2] == (
        "PQ warnings overlap with transformer or feeder stress."
    )


def test_insights_report_power_quality_caution_without_grid_overlap():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=100.0,
        energy_delivery_sufficient=True,
        overall_pq_risk_level="moderate",
        power_quality_warning_count=1,
    )

    insights = generate_insights(metrics)

    assert insights[2] == "Power-quality caution is indicated."


def test_insights_report_connection_capacity_caution_when_no_other_risk_is_present():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=100.0,
        energy_delivery_sufficient=True,
        connection_capacity_exceeded=True,
    )

    insights = generate_insights(metrics)

    assert insights[2] == (
        "Requested peak exceeds configured connection capacity."
    )


def test_insights_report_headroom_caution_when_utilization_is_high():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=100.0,
        energy_delivery_sufficient=True,
        capacity_utilization=95.0,
    )

    insights = generate_insights(metrics)

    assert insights[2] == "Spare charging headroom is limited."


def test_insights_report_no_additional_caution_when_results_are_clean():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=100.0,
        energy_delivery_sufficient=True,
        capacity_utilization=75.0,
    )

    insights = generate_insights(metrics)

    assert insights[2] == "No additional material cautions are indicated."


def test_insights_avoid_old_mechanism_descriptions_and_numeric_repetition():
    metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=100.0,
        energy_delivery_sufficient=True,
    )
    comparison_metrics = ComparisonMetrics(
        peak_reduction=150.0,
        relative_peak_reduction=37.5,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
        connection_capacity_avoided_by_smart_kw=120.0,
        exceedance_duration_reduction_hours=2.0,
    )

    insights = generate_insights(
        metrics,
        ChargingStrategy.SMART,
        comparison_metrics,
    )

    assert not any("distributes charging evenly" in insight for insight in insights)
    assert not any("Uncontrolled Charging begins immediately" in insight for insight in insights)
    assert not any("120.0 kW" in insight for insight in insights)
