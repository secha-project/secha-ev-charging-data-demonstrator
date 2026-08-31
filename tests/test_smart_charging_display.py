from metrics import (
    ComparisonMetrics,
    Metrics,
    prepare_smart_charging_card_descriptors,
)
from metrics.comparison_semantics import (
    COMPARISON_OUTCOME_IMPROVEMENT,
    COMPARISON_OUTCOME_NEUTRAL,
    COMPARISON_OUTCOME_TRADE_OFF,
    normalize_numeric_delta_for_display,
)
from metrics.planning import WAITING_REDUCED_SUMMARY, WAITING_WORSENED_SUMMARY


def test_prepare_smart_charging_card_descriptors_returns_six_prepared_cards():
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
        service_impact_summary=WAITING_REDUCED_SUMMARY,
        grid_capacity_status="Constraint reduced",
        infrastructure_impact_summary="Prepared infrastructure summary.",
    )

    cards = prepare_smart_charging_card_descriptors(
        uncontrolled_metrics,
        smart_metrics,
        comparison_metrics,
    )

    assert [card.card_id for card in cards] == [
        "peak_load",
        "required_connection_capacity",
        "peak_transformer_loading",
        "service_impact",
        "power_quality_impact",
        "grid_infrastructure_status",
    ]
    assert [card.title for card in cards] == [
        "Peak Load",
        "Required Connection Capacity",
        "Peak Transformer Loading",
        "Service Impact",
        "Power Quality Impact",
        "Grid / Infrastructure Status",
    ]
    assert [
        (card.delta.label, card.before.label, card.after.label)
        for card in cards
    ] == [
        ("Uncontrolled - Smart", "Uncontrolled", "Smart Charging"),
        ("Uncontrolled - Smart", "Uncontrolled", "Smart Charging"),
        ("Uncontrolled - Smart", "Uncontrolled", "Smart Charging"),
        ("Uncontrolled - Smart waiting", "Uncontrolled", "Smart Charging"),
        ("Uncontrolled - Smart PQ score", "Uncontrolled", "Smart Charging"),
        ("Prepared planner-facing summary", "Uncontrolled", "Smart Charging"),
    ]
    assert cards[0].outcome == COMPARISON_OUTCOME_IMPROVEMENT
    assert cards[0].delta.value == 150.0
    assert cards[0].before.value == 420.0
    assert cards[0].after.value == 270.0
    assert cards[1].outcome == COMPARISON_OUTCOME_IMPROVEMENT
    assert cards[1].delta.value == 240.0
    assert cards[1].before.value == 1200.0
    assert cards[1].after.value == 960.0
    assert cards[2].outcome == COMPARISON_OUTCOME_IMPROVEMENT
    assert cards[2].delta.value == 24.0
    assert cards[2].before.value == 110.0
    assert cards[2].after.value == 86.0
    assert cards[3].outcome == COMPARISON_OUTCOME_IMPROVEMENT
    assert cards[3].delta.value == 3.0
    assert cards[3].before.value == "Queue present: Yes; Max queue: 2; Avg wait: 4.0"
    assert cards[3].after.value == "Queue present: No; Max queue: 0; Avg wait: 1.0"
    assert "Not started 1 -> 0" in cards[3].supporting_text
    assert cards[4].outcome == COMPARISON_OUTCOME_IMPROVEMENT
    assert cards[4].delta.value == 18.0
    assert cards[4].before.value == "Level: moderate; Warnings: 2; Score: 48.0"
    assert cards[4].after.value == "Level: low; Warnings: 1; Score: 30.0"
    assert cards[5].outcome == COMPARISON_OUTCOME_IMPROVEMENT
    assert cards[5].delta.value == "Constraint reduced"
    assert (
        cards[5].before.value
        == "Adequacy: Adequate; Transformer: 110.0; Feeder: 104.0"
    )
    assert (
        cards[5].after.value
        == "Adequacy: Adequate; Transformer: 86.0; Feeder: 79.0"
    )
    assert cards[5].supporting_text == "Prepared infrastructure summary."


def test_prepare_smart_charging_card_descriptors_normalizes_zero_and_marks_minimal_change():
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

    cards = prepare_smart_charging_card_descriptors(
        uncontrolled_metrics,
        smart_metrics,
        comparison_metrics,
    )

    assert cards[0].outcome == COMPARISON_OUTCOME_NEUTRAL
    assert cards[0].delta.value == 0.0
    assert cards[1].outcome == COMPARISON_OUTCOME_NEUTRAL
    assert cards[1].delta.value == 0.0
    assert cards[2].outcome == COMPARISON_OUTCOME_NEUTRAL
    assert cards[2].delta.value == 0.0
    assert cards[3].outcome == COMPARISON_OUTCOME_NEUTRAL
    assert cards[3].delta.value == "Service unchanged"
    assert cards[4].outcome == COMPARISON_OUTCOME_NEUTRAL
    assert cards[4].delta.value == "Low risk in both"
    assert cards[5].outcome == COMPARISON_OUTCOME_NEUTRAL
    assert cards[5].delta.value == "No modeled constraint"
    assert normalize_numeric_delta_for_display(-0.0, "score_points_signed") == 0.0


def test_prepare_smart_charging_card_descriptors_classifies_trade_offs():
    uncontrolled_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=420.0,
        required_connection_capacity_kw=840.0,
        peak_transformer_loading_percent=88.0,
        maximum_feeder_loading_percent=77.0,
    )
    smart_metrics = Metrics(
        total_daily_energy=1000.0,
        available_capacity=500.0,
        energy_delivery_sufficient=True,
        peak_load=460.0,
        required_connection_capacity_kw=880.0,
        peak_transformer_loading_percent=92.0,
        maximum_feeder_loading_percent=79.0,
    )
    comparison_metrics = ComparisonMetrics(
        peak_reduction=-40.0,
        relative_peak_reduction=-9.5238095238,
        capacity_utilization_difference=0.0,
        unmet_energy_difference=0.0,
        required_connection_capacity_difference_kw=-40.0,
        average_waiting_time_difference_hours=-1.5,
        uncontrolled_average_waiting_time_hours=2.0,
        smart_average_waiting_time_hours=3.5,
        uncontrolled_queue_present_indicator=False,
        smart_queue_present_indicator=True,
        uncontrolled_maximum_queue_length=0,
        smart_maximum_queue_length=2,
        uncontrolled_vehicles_not_started_count=0,
        smart_vehicles_not_started_count=1,
        uncontrolled_vehicles_with_unmet_energy_count=0,
        smart_vehicles_with_unmet_energy_count=1,
        peak_transformer_loading_percent_difference=-4.0,
        overall_pq_risk_score_difference=-18.0,
        uncontrolled_overall_pq_risk_score=18.0,
        smart_overall_pq_risk_score=36.0,
        uncontrolled_overall_pq_risk_level="low",
        smart_overall_pq_risk_level="moderate",
        uncontrolled_power_quality_warning_count=0,
        smart_power_quality_warning_count=1,
        service_impact_summary=WAITING_WORSENED_SUMMARY,
        grid_capacity_status="Constraint worsened",
    )

    cards = prepare_smart_charging_card_descriptors(
        uncontrolled_metrics,
        smart_metrics,
        comparison_metrics,
    )

    assert all(card.outcome == COMPARISON_OUTCOME_TRADE_OFF for card in cards)
    assert cards[0].delta.value == -40.0
    assert cards[1].delta.value == -40.0
    assert cards[2].delta.value == -4.0
    assert cards[3].delta.value == -1.5
    assert cards[4].delta.value == -18.0
    assert cards[5].delta.value == "Constraint worsened"


def test_prepare_smart_charging_service_outcome_uses_uncontrolled_minus_smart_waiting_sign():
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

    improvement_cards = prepare_smart_charging_card_descriptors(
        uncontrolled_metrics,
        smart_metrics,
        ComparisonMetrics(
            peak_reduction=0.0,
            relative_peak_reduction=0.0,
            capacity_utilization_difference=0.0,
            unmet_energy_difference=0.0,
            average_waiting_time_difference_hours=1.5,
            uncontrolled_average_waiting_time_hours=2.0,
            smart_average_waiting_time_hours=0.5,
            uncontrolled_queue_present_indicator=True,
            smart_queue_present_indicator=False,
            uncontrolled_maximum_queue_length=2,
            smart_maximum_queue_length=0,
        ),
    )
    trade_off_cards = prepare_smart_charging_card_descriptors(
        uncontrolled_metrics,
        smart_metrics,
        ComparisonMetrics(
            peak_reduction=0.0,
            relative_peak_reduction=0.0,
            capacity_utilization_difference=0.0,
            unmet_energy_difference=0.0,
            average_waiting_time_difference_hours=-1.5,
            uncontrolled_average_waiting_time_hours=0.5,
            smart_average_waiting_time_hours=2.0,
            uncontrolled_queue_present_indicator=False,
            smart_queue_present_indicator=True,
            uncontrolled_maximum_queue_length=0,
            smart_maximum_queue_length=2,
        ),
    )
    neutral_cards = prepare_smart_charging_card_descriptors(
        uncontrolled_metrics,
        smart_metrics,
        ComparisonMetrics(
            peak_reduction=0.0,
            relative_peak_reduction=0.0,
            capacity_utilization_difference=0.0,
            unmet_energy_difference=0.0,
            average_waiting_time_difference_hours=-0.0,
            uncontrolled_average_waiting_time_hours=1.0,
            smart_average_waiting_time_hours=1.0,
            uncontrolled_queue_present_indicator=False,
            smart_queue_present_indicator=False,
            uncontrolled_maximum_queue_length=0,
            smart_maximum_queue_length=0,
        ),
    )

    assert improvement_cards[3].delta.value == 1.5
    assert improvement_cards[3].outcome == COMPARISON_OUTCOME_IMPROVEMENT
    assert trade_off_cards[3].delta.value == -1.5
    assert trade_off_cards[3].outcome == COMPARISON_OUTCOME_TRADE_OFF
    assert neutral_cards[3].outcome == COMPARISON_OUTCOME_NEUTRAL


def test_prepare_smart_charging_service_card_keeps_missing_waiting_delta_summary_driven():
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

    cards = prepare_smart_charging_card_descriptors(
        uncontrolled_metrics,
        smart_metrics,
        ComparisonMetrics(
            peak_reduction=0.0,
            relative_peak_reduction=0.0,
            capacity_utilization_difference=0.0,
            unmet_energy_difference=0.0,
            average_waiting_time_difference_hours=None,
            uncontrolled_average_waiting_time_hours=None,
            smart_average_waiting_time_hours=None,
            uncontrolled_queue_present_indicator=False,
            smart_queue_present_indicator=False,
            uncontrolled_maximum_queue_length=0,
            smart_maximum_queue_length=0,
            maximum_queue_length_difference=0,
            vehicles_not_started_count_difference=0,
            vehicles_with_unmet_energy_count_difference=0,
        ),
    )

    assert cards[3].outcome == COMPARISON_OUTCOME_NEUTRAL
    assert cards[3].delta.label == "Prepared planner-facing summary"
    assert cards[3].delta.value == "Service unchanged"
    assert cards[3].delta.value != 0.0
    assert cards[3].before.value == "Queue present: No; Max queue: 0; Avg wait: None"
    assert cards[3].after.value == "Queue present: No; Max queue: 0; Avg wait: None"


def test_prepare_smart_charging_service_card_classifies_summary_trade_off_when_waiting_delta_missing():
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

    cards = prepare_smart_charging_card_descriptors(
        uncontrolled_metrics,
        smart_metrics,
        ComparisonMetrics(
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
        ),
    )

    assert cards[3].outcome == COMPARISON_OUTCOME_TRADE_OFF
    assert cards[3].delta.label == "Prepared planner-facing summary"
    assert cards[3].delta.value == "Queue introduced"
    assert cards[3].delta.value != 0.0


def test_prepare_smart_charging_power_quality_outcome_uses_uncontrolled_minus_smart_score_sign():
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

    improvement_cards = prepare_smart_charging_card_descriptors(
        uncontrolled_metrics,
        smart_metrics,
        ComparisonMetrics(
            peak_reduction=0.0,
            relative_peak_reduction=0.0,
            capacity_utilization_difference=0.0,
            unmet_energy_difference=0.0,
            overall_pq_risk_score_difference=12.0,
            uncontrolled_overall_pq_risk_score=32.0,
            smart_overall_pq_risk_score=20.0,
            uncontrolled_overall_pq_risk_level="moderate",
            smart_overall_pq_risk_level="low",
            uncontrolled_power_quality_warning_count=2,
            smart_power_quality_warning_count=1,
        ),
    )
    trade_off_cards = prepare_smart_charging_card_descriptors(
        uncontrolled_metrics,
        smart_metrics,
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
    )
    neutral_cards = prepare_smart_charging_card_descriptors(
        uncontrolled_metrics,
        smart_metrics,
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
    )

    assert improvement_cards[4].delta.value == 12.0
    assert improvement_cards[4].outcome == COMPARISON_OUTCOME_IMPROVEMENT
    assert trade_off_cards[4].delta.value == -12.0
    assert trade_off_cards[4].outcome == COMPARISON_OUTCOME_TRADE_OFF
    assert neutral_cards[4].delta.value == "PQ impact unchanged"
    assert neutral_cards[4].outcome == COMPARISON_OUTCOME_NEUTRAL


def test_prepare_smart_charging_grid_status_outcome_matches_existing_direction_convention():
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

    statuses = {
        "Constraint resolved": COMPARISON_OUTCOME_IMPROVEMENT,
        "Constraint reduced": COMPARISON_OUTCOME_IMPROVEMENT,
        "Constraint worsened": COMPARISON_OUTCOME_TRADE_OFF,
        "Constraint unchanged": COMPARISON_OUTCOME_NEUTRAL,
        "No modeled constraint": COMPARISON_OUTCOME_NEUTRAL,
    }

    for status, expected_outcome in statuses.items():
        cards = prepare_smart_charging_card_descriptors(
            uncontrolled_metrics,
            smart_metrics,
            ComparisonMetrics(
                peak_reduction=0.0,
                relative_peak_reduction=0.0,
                capacity_utilization_difference=0.0,
                unmet_energy_difference=0.0,
                grid_capacity_status=status,
            ),
        )
        assert cards[5].delta.value == status
        assert cards[5].outcome == expected_outcome

