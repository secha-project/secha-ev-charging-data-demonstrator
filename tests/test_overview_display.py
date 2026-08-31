from metrics import (
    ComparisonMetrics,
    Metrics,
    OVERVIEW_OUTCOME_CHARGER_EXPANSION_RECOMMENDED,
    OVERVIEW_OUTCOME_CONSTRAINED,
    OVERVIEW_OUTCOME_FEASIBLE,
    OVERVIEW_OUTCOME_MULTIPLE_CONSTRAINTS,
    OVERVIEW_OUTCOME_UPGRADE_RECOMMENDED,
    prepare_overview_display_data,
)
from metrics.comparison_semantics import (
    COMPARISON_OUTCOME_IMPROVEMENT,
    COMPARISON_OUTCOME_NEUTRAL,
    COMPARISON_OUTCOME_TRADE_OFF,
)
from scenarios import ChargingStrategy, copy_scenario_with_updates, default_scenario


def test_prepare_overview_display_data_prepares_executive_summary_for_smart_relief():
    active_scenario = copy_scenario_with_updates(
        default_scenario,
        charging_strategy=ChargingStrategy.SMART,
        charger_count=40,
        grid_capacity=500.0,
    )
    active_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=420.0,
        capacity_utilization=84.0,
        configured_connection_capacity_kw=500.0,
        required_connection_capacity_kw=500.0,
        recommended_connection_capacity_kw=500.0,
        connection_capacity_adequate_indicator=True,
        peak_transformer_loading_percent=82.0,
        maximum_feeder_loading_percent=78.0,
        required_charger_count=40,
        additional_chargers_required=0,
        primary_constraint_reason="none",
    )
    uncontrolled_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=600.0,
        configured_connection_capacity_kw=500.0,
        required_connection_capacity_kw=620.0,
        recommended_connection_capacity_kw=660.0,
        connection_capacity_adequate_indicator=False,
        peak_transformer_loading_percent=101.0,
        maximum_feeder_loading_percent=92.0,
    )
    smart_metrics = active_metrics
    comparison_metrics = ComparisonMetrics(
        peak_reduction=180.0,
        relative_peak_reduction=30.0,
        capacity_utilization_difference=36.0,
        unmet_energy_difference=0.0,
        uncontrolled_required_connection_capacity_kw=620.0,
        smart_required_connection_capacity_kw=500.0,
        required_connection_capacity_difference_kw=120.0,
        uncontrolled_recommended_connection_capacity_kw=660.0,
        smart_recommended_connection_capacity_kw=500.0,
        recommended_connection_capacity_difference_kw=160.0,
        recommended_connection_capacity_avoided_by_smart_kw=160.0,
        connection_upgrade_avoided_by_smart=True,
        grid_capacity_status="Constraint resolved",
        infrastructure_impact_summary=(
            "Smart Charging avoids the modeled connection-capacity upgrade "
            "recommendation for this scenario."
        ),
    )

    display_data = prepare_overview_display_data(
        active_scenario,
        active_metrics,
        uncontrolled_metrics,
        smart_metrics,
        comparison_metrics,
    )

    assert [kpi.title for kpi in display_data.kpis] == [
        "Scenario Outcome",
        "Peak Load",
        "Grid Connection Need",
        "Charger Expansion Need",
    ]
    assert display_data.kpis[0].headline.value == OVERVIEW_OUTCOME_FEASIBLE
    assert display_data.kpis[0].outcome == COMPARISON_OUTCOME_IMPROVEMENT
    assert display_data.kpis[2].headline.value == 500.0
    assert display_data.kpis[3].headline.value == 0
    assert display_data.kpis[2].supporting_fields[0].label == "Current capacity"
    assert display_data.kpis[2].supporting_fields[0].value == 500.0
    assert display_data.kpis[2].supporting_fields[1].label == "Required increase"
    assert display_data.kpis[2].supporting_fields[1].value == 0.0
    assert display_data.kpis[3].supporting_text is None
    assert display_data.smart_charging_preview.summary_title == "Peak Reduction"
    assert display_data.smart_charging_preview.summary_value == "180.0 kW (30.0%)"
    assert (
        display_data.smart_charging_preview.summary
        == "Smart Charging reduces peak demand by 180.0 kW (30.0%)."
    )


def test_prepare_overview_display_data_prepares_upgrade_recommendation():
    active_scenario = copy_scenario_with_updates(
        default_scenario,
        charging_strategy=ChargingStrategy.UNCONTROLLED,
        charger_count=40,
        grid_capacity=500.0,
    )
    active_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=620.0,
        capacity_utilization=124.0,
        configured_connection_capacity_kw=500.0,
        required_connection_capacity_kw=620.0,
        recommended_connection_capacity_kw=660.0,
        connection_capacity_adequate_indicator=False,
        peak_transformer_loading_percent=96.0,
        maximum_feeder_loading_percent=87.0,
        required_charger_count=40,
        additional_chargers_required=0,
        primary_constraint_reason="grid_connection_capacity",
    )
    comparison_metrics = ComparisonMetrics(
        peak_reduction=40.0,
        relative_peak_reduction=6.5,
        capacity_utilization_difference=8.0,
        unmet_energy_difference=0.0,
        uncontrolled_required_connection_capacity_kw=620.0,
        smart_required_connection_capacity_kw=580.0,
        required_connection_capacity_difference_kw=40.0,
        uncontrolled_recommended_connection_capacity_kw=660.0,
        smart_recommended_connection_capacity_kw=620.0,
        recommended_connection_capacity_difference_kw=40.0,
        recommended_connection_capacity_avoided_by_smart_kw=40.0,
        connection_upgrade_avoided_by_smart=False,
        grid_capacity_status="Constraint reduced",
    )

    display_data = prepare_overview_display_data(
        active_scenario,
        active_metrics,
        active_metrics,
        active_metrics,
        comparison_metrics,
    )

    assert display_data.kpis[0].headline.value == OVERVIEW_OUTCOME_UPGRADE_RECOMMENDED
    assert display_data.kpis[0].outcome == COMPARISON_OUTCOME_TRADE_OFF
    assert display_data.kpis[2].headline.value == 660.0
    assert display_data.kpis[2].supporting_fields[0].label == "Current capacity"
    assert display_data.kpis[2].supporting_fields[0].value == 500.0
    assert display_data.kpis[2].supporting_fields[1].value == 160.0
    assert display_data.kpis[2].outcome == COMPARISON_OUTCOME_TRADE_OFF
    assert display_data.kpis[2].supporting_text is None


def test_prepare_overview_display_data_keeps_grid_card_recommendation_led_for_brief_spike():
    active_scenario = copy_scenario_with_updates(
        default_scenario,
        charging_strategy=ChargingStrategy.UNCONTROLLED,
        charger_count=40,
        grid_capacity=500.0,
    )
    active_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=520.0,
        capacity_utilization=104.0,
        configured_connection_capacity_kw=500.0,
        required_connection_capacity_kw=520.0,
        recommended_connection_capacity_kw=500.0,
        connection_capacity_adequate_indicator=True,
        peak_transformer_loading_percent=82.0,
        maximum_feeder_loading_percent=78.0,
        required_charger_count=40,
        additional_chargers_required=0,
        primary_constraint_reason="none",
    )
    comparison_metrics = ComparisonMetrics(
        peak_reduction=20.0,
        relative_peak_reduction=3.7,
        capacity_utilization_difference=4.0,
        unmet_energy_difference=0.0,
        uncontrolled_required_connection_capacity_kw=520.0,
        smart_required_connection_capacity_kw=500.0,
        required_connection_capacity_difference_kw=20.0,
        uncontrolled_recommended_connection_capacity_kw=500.0,
        smart_recommended_connection_capacity_kw=500.0,
        recommended_connection_capacity_difference_kw=0.0,
        recommended_connection_capacity_avoided_by_smart_kw=0.0,
        connection_upgrade_avoided_by_smart=False,
        grid_capacity_status="No modeled constraint",
    )

    display_data = prepare_overview_display_data(
        active_scenario,
        active_metrics,
        active_metrics,
        active_metrics,
        comparison_metrics,
    )

    grid_card = display_data.kpis[2]
    assert grid_card.title == "Grid Connection Need"
    assert grid_card.headline.label == "Planner recommendation"
    assert grid_card.headline.value == 500.0
    assert grid_card.supporting_fields[0].label == "Current capacity"
    assert grid_card.supporting_fields[0].value == 500.0
    assert grid_card.supporting_fields[1].label == "Required increase"
    assert grid_card.supporting_fields[1].value == 0.0
    assert grid_card.outcome == COMPARISON_OUTCOME_NEUTRAL
    assert grid_card.supporting_text is None


def test_prepare_overview_display_data_prepares_charger_expansion_recommendation():
    active_scenario = copy_scenario_with_updates(
        default_scenario,
        charger_count=40,
        grid_capacity=500.0,
    )
    active_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=420.0,
        capacity_utilization=84.0,
        configured_connection_capacity_kw=500.0,
        required_connection_capacity_kw=420.0,
        recommended_connection_capacity_kw=500.0,
        connection_capacity_adequate_indicator=True,
        peak_transformer_loading_percent=82.0,
        maximum_feeder_loading_percent=78.0,
        required_charger_count=60,
        additional_chargers_required=20,
        primary_constraint_reason="charger_availability",
        maximum_waiting_time_hours=1.0,
        charger_service_waiting_tolerance_hours=0.5,
    )
    comparison_metrics = ComparisonMetrics(
        peak_reduction=0.0,
        relative_peak_reduction=0.0,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
    )

    display_data = prepare_overview_display_data(
        active_scenario,
        active_metrics,
        active_metrics,
        active_metrics,
        comparison_metrics,
    )

    assert (
        display_data.kpis[0].headline.value
        == OVERVIEW_OUTCOME_CHARGER_EXPANSION_RECOMMENDED
    )
    assert display_data.kpis[3].headline.value == 20
    assert display_data.kpis[3].supporting_fields[0].value == 40
    assert display_data.kpis[3].supporting_fields[1].value == 60
    assert display_data.kpis[3].outcome == COMPARISON_OUTCOME_TRADE_OFF
    assert display_data.kpis[3].supporting_text is None


def test_prepare_overview_display_data_prepares_multiple_constraint_outcome():
    active_scenario = copy_scenario_with_updates(
        default_scenario,
        charger_count=40,
        grid_capacity=500.0,
    )
    active_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        peak_load=700.0,
        capacity_utilization=140.0,
        configured_connection_capacity_kw=500.0,
        required_connection_capacity_kw=700.0,
        recommended_connection_capacity_kw=760.0,
        connection_capacity_adequate_indicator=False,
        peak_transformer_loading_percent=112.0,
        transformer_overload_indicator=True,
        maximum_feeder_loading_percent=104.0,
        feeder_overload_indicator=True,
        primary_constraint_reason="mixed",
        maximum_waiting_time_hours=1.0,
        charger_service_waiting_tolerance_hours=0.5,
        required_charger_count=None,
        additional_chargers_required=None,
    )
    comparison_metrics = ComparisonMetrics(
        peak_reduction=-30.0,
        relative_peak_reduction=-4.3,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=50.0,
        grid_capacity_status="Constraint worsened",
    )

    display_data = prepare_overview_display_data(
        active_scenario,
        active_metrics,
        active_metrics,
        active_metrics,
        comparison_metrics,
    )

    assert (
        display_data.kpis[0].headline.value
        == OVERVIEW_OUTCOME_MULTIPLE_CONSTRAINTS
    )
    assert display_data.kpis[3].headline.value == "Not the primary constraint"
    assert display_data.kpis[3].outcome == COMPARISON_OUTCOME_NEUTRAL
    assert display_data.smart_charging_preview.outcome == COMPARISON_OUTCOME_TRADE_OFF
    assert display_data.smart_charging_preview.summary_title == "Peak Increase"
    assert display_data.smart_charging_preview.summary_value == "30.0 kW (4.3%)"


def test_prepare_overview_display_data_uses_multiple_constraints_label_when_service_and_grid_both_fail():
    active_scenario = copy_scenario_with_updates(
        default_scenario,
        charger_count=40,
        grid_capacity=500.0,
    )
    active_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        peak_load=640.0,
        capacity_utilization=128.0,
        configured_connection_capacity_kw=500.0,
        required_connection_capacity_kw=640.0,
        recommended_connection_capacity_kw=700.0,
        connection_capacity_adequate_indicator=False,
        peak_transformer_loading_percent=92.0,
        maximum_feeder_loading_percent=84.0,
        primary_constraint_reason="charger_availability",
        required_charger_count=52,
        additional_chargers_required=12,
        maximum_waiting_time_hours=1.0,
        charger_service_waiting_tolerance_hours=0.5,
    )
    comparison_metrics = ComparisonMetrics(
        peak_reduction=60.0,
        relative_peak_reduction=9.4,
        capacity_utilization_difference=12.0,
        unmet_energy_difference=40.0,
    )

    display_data = prepare_overview_display_data(
        active_scenario,
        active_metrics,
        active_metrics,
        active_metrics,
        comparison_metrics,
    )

    assert (
        display_data.kpis[0].headline.value
        == OVERVIEW_OUTCOME_MULTIPLE_CONSTRAINTS
    )
    assert display_data.kpis[0].supporting_text == (
        "More than one modeled bottleneck should be addressed."
    )


def test_prepare_overview_display_data_uses_review_bottleneck_wording_for_non_expansion_constraint():
    active_scenario = copy_scenario_with_updates(
        default_scenario,
        charger_count=40,
        grid_capacity=500.0,
    )
    active_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=False,
        peak_load=420.0,
        capacity_utilization=84.0,
        configured_connection_capacity_kw=500.0,
        required_connection_capacity_kw=420.0,
        recommended_connection_capacity_kw=500.0,
        connection_capacity_adequate_indicator=True,
        peak_transformer_loading_percent=78.0,
        maximum_feeder_loading_percent=74.0,
        primary_constraint_reason="charging_window",
        required_charger_count=None,
        additional_chargers_required=None,
        maximum_waiting_time_hours=1.0,
        charger_service_waiting_tolerance_hours=0.5,
    )
    comparison_metrics = ComparisonMetrics(
        peak_reduction=0.0,
        relative_peak_reduction=0.0,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=20.0,
        grid_capacity_status="No modeled constraint",
    )

    display_data = prepare_overview_display_data(
        active_scenario,
        active_metrics,
        active_metrics,
        active_metrics,
        comparison_metrics,
    )

    assert display_data.kpis[0].headline.value == OVERVIEW_OUTCOME_CONSTRAINED
    assert display_data.kpis[0].supporting_fields[0].value == "Charging allowed window"
    assert display_data.kpis[3].headline.value == "Not the primary constraint"
    assert display_data.kpis[3].supporting_text is None
