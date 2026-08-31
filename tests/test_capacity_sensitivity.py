from dataclasses import replace
from datetime import time

import pytest

from metrics import (
    CapacityAlternativeMetrics,
    calculate_metrics,
    capacity_alternative_metrics_from_dict,
    capacity_alternative_metrics_to_dict,
    create_capacity_alternative_metrics,
    generate_connection_capacity_alternatives,
    run_connection_capacity_sensitivity,
)
from scenarios import Scenario, default_scenario
from simulation import simulate


def _run_connection_capacity_sensitivity_reference(
    scenario: Scenario,
    capacity_alternatives_kw: list[float] | None = None,
    *,
    base_metrics=None,
) -> list[CapacityAlternativeMetrics]:
    """Return the legacy sensitivity result using full reruns per row."""

    alternative_values = list(capacity_alternatives_kw or [])
    if not alternative_values or base_metrics is None:
        base_result = simulate(scenario)
        base_metrics = calculate_metrics(base_result, scenario)
        alternative_values = generate_connection_capacity_alternatives(
            scenario.grid_capacity,
            base_metrics.required_connection_capacity_kw,
            base_metrics.recommended_connection_capacity_kw,
        )
    alternative_values = sorted(alternative_values)

    sensitivity_results: list[CapacityAlternativeMetrics] = []
    for configured_connection_capacity_kw in alternative_values:
        alternative_scenario = replace(
            scenario,
            grid_capacity=configured_connection_capacity_kw,
        )
        rerun_result = simulate(alternative_scenario)
        rerun_metrics = calculate_metrics(rerun_result, alternative_scenario)
        sensitivity_results.append(
            create_capacity_alternative_metrics(
                configured_connection_capacity_kw,
                rerun_metrics,
            )
        )

    return sensitivity_results


def _build_capacity_limited_scenario(
    *,
    grid_capacity: float,
    planning_margin_percent: float = 10.0,
) -> Scenario:
    return Scenario(
        vehicles=20,
        daily_energy_per_vehicle=100.0,
        charger_count=4,
        charger_power=100.0,
        grid_capacity=grid_capacity,
        planning_margin_percent=planning_margin_percent,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    )


def test_generate_connection_capacity_alternatives_considers_all_five_source_values():
    alternatives = generate_connection_capacity_alternatives(
        configured_connection_capacity_kw=1000.0,
        required_connection_capacity_kw=1500.0,
        recommended_connection_capacity_kw=1650.0,
    )

    assert alternatives == [800.0, 1000.0, 1200.0, 1500.0, 1650.0]


def test_generate_connection_capacity_alternatives_returns_sorted_values():
    alternatives = generate_connection_capacity_alternatives(
        configured_connection_capacity_kw=1000.0,
        required_connection_capacity_kw=700.0,
        recommended_connection_capacity_kw=1300.0,
    )

    assert alternatives == [700.0, 800.0, 1000.0, 1200.0, 1300.0]


def test_generate_connection_capacity_alternatives_removes_duplicates():
    alternatives = generate_connection_capacity_alternatives(
        configured_connection_capacity_kw=1000.0,
        required_connection_capacity_kw=1000.0,
        recommended_connection_capacity_kw=1200.0,
    )

    assert alternatives == [800.0, 1000.0, 1200.0]


def test_generate_connection_capacity_alternatives_includes_configured_required_and_recommended_capacities():
    alternatives = generate_connection_capacity_alternatives(
        configured_connection_capacity_kw=950.0,
        required_connection_capacity_kw=1100.0,
        recommended_connection_capacity_kw=1210.0,
    )

    assert 950.0 in alternatives
    assert 1100.0 in alternatives
    assert 1210.0 in alternatives


def test_equal_configured_required_and_recommended_capacities_produce_one_value_where_appropriate():
    alternatives = generate_connection_capacity_alternatives(
        configured_connection_capacity_kw=0.0,
        required_connection_capacity_kw=0.0,
        recommended_connection_capacity_kw=0.0,
    )

    assert alternatives == [0.0]


def test_generate_connection_capacity_alternatives_handles_zero_values_safely():
    alternatives = generate_connection_capacity_alternatives(
        configured_connection_capacity_kw=0.0,
        required_connection_capacity_kw=10.0,
        recommended_connection_capacity_kw=12.0,
    )

    assert alternatives == [0.0, 10.0, 12.0]


def test_create_capacity_alternative_metrics_maps_completed_metrics_without_recalculation():
    metrics = calculate_metrics(
        simulate(default_scenario),
        default_scenario,
    )
    custom_metrics = replace(
        metrics,
        required_connection_capacity_kw=980.0,
        peak_capacity_margin_kw=-80.0,
        peak_capacity_margin_percent=-8.0,
        connection_capacity_exceeded=True,
        capacity_exceedance_duration_hours=2.5,
    )

    row = create_capacity_alternative_metrics(900.0, custom_metrics)

    assert row == CapacityAlternativeMetrics(
        capacity_option_kw=900.0,
        required_connection_capacity_kw=980.0,
        headroom_kw=-80.0,
        headroom_percent=-8.0,
        capacity_exceeded=True,
        time_above_capacity_hours=2.5,
        capacity_adequate_indicator=False,
        capacity_recommendation_reason="persistent_requested_exceedance",
    )


def test_create_capacity_alternative_metrics_preserves_undefined_margin_percent():
    metrics = replace(
        calculate_metrics(simulate(default_scenario), default_scenario),
        peak_capacity_margin_percent=None,
    )

    row = create_capacity_alternative_metrics(0.0, metrics)

    assert row.headroom_percent is None


def test_capacity_alternative_metrics_serialization_round_trip_preserves_values():
    row = CapacityAlternativeMetrics(
        capacity_option_kw=900.0,
        required_connection_capacity_kw=980.0,
        headroom_kw=-80.0,
        headroom_percent=None,
        capacity_exceeded=True,
        time_above_capacity_hours=2.5,
        capacity_adequate_indicator=False,
        capacity_recommendation_reason="persistent_requested_exceedance",
    )

    data = capacity_alternative_metrics_to_dict(row)
    restored_row = capacity_alternative_metrics_from_dict(data)

    assert data == {
        "capacity_option_kw": 900.0,
        "required_connection_capacity_kw": 980.0,
        "headroom_kw": -80.0,
        "headroom_percent": None,
        "capacity_exceeded": True,
        "time_above_capacity_hours": 2.5,
        "capacity_adequate_indicator": False,
        "capacity_recommendation_reason": "persistent_requested_exceedance",
    }
    assert restored_row == row


def test_capacity_alternative_metrics_from_dict_supports_legacy_mixed_table_fields():
    restored_row = capacity_alternative_metrics_from_dict(
        {
            "capacity_option_kw": 900.0,
            "peak_capacity_margin_kw": -80.0,
            "peak_capacity_margin_percent": None,
            "connection_capacity_exceeded": True,
            "capacity_exceedance_duration_hours": 2.5,
        }
    )

    assert restored_row == CapacityAlternativeMetrics(
        capacity_option_kw=900.0,
        required_connection_capacity_kw=980.0,
        headroom_kw=-80.0,
        headroom_percent=None,
        capacity_exceeded=True,
        time_above_capacity_hours=2.5,
        capacity_adequate_indicator=False,
        capacity_recommendation_reason="persistent_requested_exceedance",
    )


def test_run_connection_capacity_sensitivity_changes_only_configured_connection_capacity():
    scenario = replace(
        default_scenario,
        vehicles=20,
        daily_energy_per_vehicle=100.0,
        charger_count=4,
        charger_power=100.0,
        grid_capacity=150.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
        arrival_window_start=time(22, 0),
        arrival_window_end=time(22, 0),
    )

    sensitivity_results = run_connection_capacity_sensitivity(
        scenario,
        capacity_alternatives_kw=[120.0, 150.0, 180.0],
    )

    assert scenario.grid_capacity == 150.0
    assert [row.capacity_option_kw for row in sensitivity_results] == [
        120.0,
        150.0,
        180.0,
    ]

    for capacity_option_kw, row in zip(
        [120.0, 150.0, 180.0],
        sensitivity_results,
        strict=True,
    ):
        rerun_scenario = replace(scenario, grid_capacity=capacity_option_kw)
        rerun_metrics = calculate_metrics(simulate(rerun_scenario), rerun_scenario)
        assert row == create_capacity_alternative_metrics(
            capacity_option_kw,
            rerun_metrics,
        )


@pytest.mark.parametrize(
    ("scenario"),
    [
        default_scenario,
        _build_capacity_limited_scenario(grid_capacity=100.0),
        _build_capacity_limited_scenario(grid_capacity=400.0),
        _build_capacity_limited_scenario(grid_capacity=600.0),
    ],
    ids=[
        "default",
        "capacity-limited",
        "required-capacity-match",
        "no-exceedance",
    ],
)
def test_run_connection_capacity_sensitivity_matches_legacy_reference_output(
    scenario,
):
    assert run_connection_capacity_sensitivity(scenario) == (
        _run_connection_capacity_sensitivity_reference(scenario)
    )


def test_run_connection_capacity_sensitivity_returns_rows_ordered_by_capacity_option():
    sensitivity_results = run_connection_capacity_sensitivity(
        default_scenario,
        capacity_alternatives_kw=[1200.0, 800.0, 1000.0],
    )

    assert [row.capacity_option_kw for row in sensitivity_results] == [
        800.0,
        1000.0,
        1200.0,
    ]


def test_run_connection_capacity_sensitivity_returns_one_row_per_generated_alternative():
    scenario = Scenario(
        vehicles=20,
        daily_energy_per_vehicle=100.0,
        charger_count=4,
        charger_power=100.0,
        grid_capacity=100.0,
        charging_window_start=time(22, 0),
        charging_window_end=time(2, 0),
    )
    base_result = simulate(scenario)
    base_metrics = calculate_metrics(base_result, scenario)
    expected_alternatives = generate_connection_capacity_alternatives(
        scenario.grid_capacity,
        base_metrics.required_connection_capacity_kw,
        base_metrics.recommended_connection_capacity_kw,
    )

    sensitivity_results = run_connection_capacity_sensitivity(scenario)

    assert len(sensitivity_results) == len(expected_alternatives)
    assert [row.capacity_option_kw for row in sensitivity_results] == pytest.approx(
        expected_alternatives
    )


def test_run_connection_capacity_sensitivity_is_deterministic():
    first_run = run_connection_capacity_sensitivity(default_scenario)
    second_run = run_connection_capacity_sensitivity(default_scenario)

    assert first_run == second_run


def test_connection_capacity_sensitivity_reuses_base_row_and_skips_full_metrics_reruns(
    monkeypatch,
):
    import metrics.capacity_sensitivity as capacity_sensitivity_module

    scenario = _build_capacity_limited_scenario(grid_capacity=100.0)
    base_metrics = calculate_metrics(simulate(scenario), scenario)
    alternatives = [80.0, 100.0, 120.0, 400.0, 440.0]
    simulate_calls: list[float] = []
    original_simulate = capacity_sensitivity_module.simulate

    def record_simulate(candidate_scenario):
        simulate_calls.append(candidate_scenario.grid_capacity)
        return original_simulate(candidate_scenario)

    monkeypatch.setattr(
        capacity_sensitivity_module,
        "simulate",
        record_simulate,
    )
    monkeypatch.setattr(
        capacity_sensitivity_module,
        "calculate_metrics",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError(
                "run_connection_capacity_sensitivity should not use full "
                "calculate_metrics reruns when base metrics are supplied."
            )
        ),
    )

    rows = run_connection_capacity_sensitivity(
        scenario,
        capacity_alternatives_kw=alternatives,
        base_metrics=base_metrics,
    )

    assert [row.capacity_option_kw for row in rows] == alternatives
    assert simulate_calls == [80.0, 120.0, 400.0, 440.0]


def test_connection_capacity_sensitivity_uses_supplied_base_metrics_for_generated_alternatives(
    monkeypatch,
):
    import metrics.capacity_sensitivity as capacity_sensitivity_module

    scenario = _build_capacity_limited_scenario(grid_capacity=100.0)
    base_metrics = calculate_metrics(simulate(scenario), scenario)
    simulate_calls: list[float] = []
    original_simulate = capacity_sensitivity_module.simulate

    def record_simulate(candidate_scenario):
        simulate_calls.append(candidate_scenario.grid_capacity)
        return original_simulate(candidate_scenario)

    monkeypatch.setattr(
        capacity_sensitivity_module,
        "simulate",
        record_simulate,
    )
    monkeypatch.setattr(
        capacity_sensitivity_module,
        "calculate_metrics",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError(
                "run_connection_capacity_sensitivity should not rerun "
                "base calculate_metrics when base metrics are supplied."
            )
        ),
    )

    rows = run_connection_capacity_sensitivity(
        scenario,
        base_metrics=base_metrics,
    )

    assert [row.capacity_option_kw for row in rows] == pytest.approx(
        [80.0, 100.0, 120.0, 400.0, 440.0]
    )
    assert simulate_calls == pytest.approx([80.0, 120.0, 400.0, 440.0])


def test_connection_capacity_sensitivity_with_base_metrics_matches_legacy_reference_output():
    scenario = _build_capacity_limited_scenario(grid_capacity=100.0)
    base_metrics = calculate_metrics(simulate(scenario), scenario)

    assert run_connection_capacity_sensitivity(
        scenario,
        base_metrics=base_metrics,
    ) == _run_connection_capacity_sensitivity_reference(
        scenario,
        base_metrics=base_metrics,
    )


def test_connection_capacity_sensitivity_full_flow_reuses_independent_reruns_per_alternative():
    scenario = _build_capacity_limited_scenario(grid_capacity=100.0)
    base_result = simulate(scenario)
    base_metrics = calculate_metrics(base_result, scenario)
    alternatives = generate_connection_capacity_alternatives(
        scenario.grid_capacity,
        base_metrics.required_connection_capacity_kw,
        base_metrics.recommended_connection_capacity_kw,
    )

    rerun_results = [
        simulate(replace(scenario, grid_capacity=capacity_option_kw))
        for capacity_option_kw in alternatives
    ]
    rerun_metrics = [
        calculate_metrics(result, replace(scenario, grid_capacity=capacity_option_kw))
        for capacity_option_kw, result in zip(
            alternatives,
            rerun_results,
            strict=True,
        )
    ]
    expected_rows = [
        create_capacity_alternative_metrics(capacity_option_kw, metrics)
        for capacity_option_kw, metrics in zip(
            alternatives,
            rerun_metrics,
            strict=True,
        )
    ]

    actual_rows = run_connection_capacity_sensitivity(scenario)

    assert len({id(result) for result in rerun_results}) == len(rerun_results)
    assert len({id(metrics) for metrics in rerun_metrics}) == len(rerun_metrics)
    assert actual_rows == expected_rows
    assert scenario.grid_capacity == 100.0


def test_required_connection_capacity_remains_constant_across_sweep_when_strategy_is_unchanged():
    scenario = _build_capacity_limited_scenario(grid_capacity=100.0)
    base_metrics = calculate_metrics(simulate(scenario), scenario)
    sensitivity_rows = run_connection_capacity_sensitivity(scenario)

    required_capacities = [
        calculate_metrics(
            simulate(replace(scenario, grid_capacity=row.capacity_option_kw)),
            replace(scenario, grid_capacity=row.capacity_option_kw),
        ).required_connection_capacity_kw
        for row in sensitivity_rows
    ]

    assert required_capacities == [base_metrics.required_connection_capacity_kw] * len(
        sensitivity_rows
    )


@pytest.mark.parametrize(
    ("scenario", "expected_alternatives"),
    [
        pytest.param(
            _build_capacity_limited_scenario(grid_capacity=100.0),
            [80.0, 100.0, 120.0, 400.0, 440.0],
            id="configured-below-required-capacity",
        ),
        pytest.param(
            _build_capacity_limited_scenario(grid_capacity=400.0),
            [320.0, 400.0, 480.0],
            id="configured-equals-required-capacity",
        ),
        pytest.param(
            _build_capacity_limited_scenario(grid_capacity=500.0),
            [400.0, 500.0, 600.0],
            id="configured-above-recommended-capacity",
        ),
        pytest.param(
            _build_capacity_limited_scenario(
                grid_capacity=400.0,
                planning_margin_percent=0.0,
            ),
            [320.0, 400.0, 480.0],
            id="configured-required-and-recommended-equal",
        ),
    ],
)
def test_generated_alternatives_cover_representative_capacity_relationships(
    scenario,
    expected_alternatives,
):
    base_metrics = calculate_metrics(simulate(scenario), scenario)

    alternatives = generate_connection_capacity_alternatives(
        scenario.grid_capacity,
        base_metrics.required_connection_capacity_kw,
        base_metrics.recommended_connection_capacity_kw,
    )

    assert alternatives == pytest.approx(expected_alternatives)


def test_sensitivity_sweep_handles_scenario_with_no_connection_capacity_exceedance():
    scenario = _build_capacity_limited_scenario(grid_capacity=600.0)

    sensitivity_rows = run_connection_capacity_sensitivity(scenario)

    assert [row.capacity_option_kw for row in sensitivity_rows] == pytest.approx(
        [400.0, 480.0, 600.0, 720.0]
    )
    assert all(not row.capacity_exceeded for row in sensitivity_rows)


def test_sensitivity_sweep_shows_lower_capacity_causing_less_headroom_and_longer_overload():
    scenario = _build_capacity_limited_scenario(grid_capacity=100.0)

    sensitivity_rows = run_connection_capacity_sensitivity(scenario)

    assert sensitivity_rows[0].capacity_option_kw == pytest.approx(80.0)
    assert sensitivity_rows[-1].capacity_option_kw == pytest.approx(440.0)
    assert sensitivity_rows[0].headroom_kw < sensitivity_rows[-1].headroom_kw
    assert (
        sensitivity_rows[0].time_above_capacity_hours
        >= sensitivity_rows[-1].time_above_capacity_hours
    )


def test_run_connection_capacity_sensitivity_updates_row_values_consistently_when_capacity_changes():
    scenario = _build_capacity_limited_scenario(grid_capacity=100.0)

    sensitivity_results = run_connection_capacity_sensitivity(scenario)

    assert [row.capacity_option_kw for row in sensitivity_results] == pytest.approx(
        [80.0, 100.0, 120.0, 400.0, 440.0]
    )
    assert [row.required_connection_capacity_kw for row in sensitivity_results] == [
        400.0,
        400.0,
        400.0,
        400.0,
        400.0,
    ]
    assert [row.headroom_kw for row in sensitivity_results] == pytest.approx(
        [
        -320.0,
        -300.0,
        -280.0,
        0.0,
        40.0,
        ]
    )
    assert [row.time_above_capacity_hours for row in sensitivity_results] == [
        4.0,
        4.0,
        4.0,
        0.0,
        0.0,
    ]
    assert [row.capacity_exceeded for row in sensitivity_results] == [
        True,
        True,
        True,
        False,
        False,
    ]
