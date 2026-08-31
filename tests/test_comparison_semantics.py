import pytest

from metrics.comparison_semantics import (
    COMPARISON_OUTCOME_IMPROVEMENT,
    COMPARISON_OUTCOME_NEUTRAL,
    COMPARISON_OUTCOME_TRADE_OFF,
    classify_directional_outcome,
    default_materiality_threshold,
    is_numeric_change_material,
    relative_shift_percent,
)


def test_default_materiality_threshold_matches_existing_display_rounding_rules():
    assert default_materiality_threshold("power_kw_signed") == pytest.approx(0.05)
    assert default_materiality_threshold("score_points_signed") == pytest.approx(0.05)
    assert default_materiality_threshold("vehicle_count_0_signed") == pytest.approx(0.5)
    assert default_materiality_threshold("warning_count_signed") == pytest.approx(0.5)
    assert default_materiality_threshold("unknown_format") == pytest.approx(0.0)


def test_classify_directional_outcome_preserves_lower_and_higher_semantics():
    assert (
        classify_directional_outcome(-10.0, "lower")
        == COMPARISON_OUTCOME_IMPROVEMENT
    )
    assert (
        classify_directional_outcome(10.0, "lower")
        == COMPARISON_OUTCOME_TRADE_OFF
    )
    assert (
        classify_directional_outcome(10.0, "higher")
        == COMPARISON_OUTCOME_IMPROVEMENT
    )
    assert (
        classify_directional_outcome(-10.0, "higher")
        == COMPARISON_OUTCOME_TRADE_OFF
    )
    assert classify_directional_outcome(0.0, "lower") == COMPARISON_OUTCOME_NEUTRAL
    assert classify_directional_outcome(None, "higher") == COMPARISON_OUTCOME_NEUTRAL


def test_relative_shift_percent_preserves_zero_and_zero_baseline_behavior():
    assert relative_shift_percent(None, 100.0) == pytest.approx(0.0)
    assert relative_shift_percent(0.0, 100.0) == pytest.approx(0.0)
    assert relative_shift_percent(5.0, 0.0) == pytest.approx(100.0)
    assert relative_shift_percent(-5.0, 20.0) == pytest.approx(25.0)


def test_is_numeric_change_material_preserves_absolute_and_relative_threshold_logic():
    assert not is_numeric_change_material(
        0.04,
        absolute_materiality_threshold=0.05,
    )
    assert is_numeric_change_material(
        0.05,
        absolute_materiality_threshold=0.05,
    )
    assert not is_numeric_change_material(
        5.0,
        absolute_materiality_threshold=0.05,
        relative_materiality_threshold=10.0,
        relative_change_percent=5.0,
        baseline_value=100.0,
    )
    assert is_numeric_change_material(
        5.0,
        absolute_materiality_threshold=0.05,
        relative_materiality_threshold=5.0,
        relative_change_percent=5.0,
        baseline_value=100.0,
    )
    assert is_numeric_change_material(
        5.0,
        absolute_materiality_threshold=0.05,
        relative_materiality_threshold=20.0,
        relative_change_percent=None,
        baseline_value=20.0,
    )
