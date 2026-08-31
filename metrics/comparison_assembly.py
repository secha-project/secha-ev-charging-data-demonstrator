"""Small declarative helpers for repeated metrics comparison assembly."""

from dataclasses import dataclass
from typing import Any, Callable

from metrics.serialization import feeder_summary_metrics_to_dict


CopyTransform = Callable[[Any], Any]


@dataclass(frozen=True)
class StrategyMetricFieldSpec:
    """Describe one repeated uncontrolled/smart comparison field mapping."""

    attribute_name: str
    difference_field: str | None = None
    difference_kind: str = "subtract"
    copy_transform: CopyTransform | None = None


@dataclass(frozen=True)
class ScenarioDifferenceFieldSpec:
    """Describe one repeated Scenario A/B difference field mapping."""

    attribute_name: str
    difference_field: str
    percent_change_field: str | None = None
    difference_kind: str = "subtract"


def calculate_defined_difference(
    minuend: int | float | None,
    subtrahend: int | float | None,
) -> int | float | None:
    """Return a numeric difference only when both values are defined."""
    if minuend is None or subtrahend is None:
        return None

    return minuend - subtrahend


def build_strategy_metric_fields(
    uncontrolled_metrics,
    smart_metrics,
    specs: tuple[StrategyMetricFieldSpec, ...],
) -> dict[str, Any]:
    """Return repeated uncontrolled/smart value fields from explicit specs."""
    values: dict[str, Any] = {}

    for spec in specs:
        uncontrolled_value = getattr(
            uncontrolled_metrics,
            spec.attribute_name,
        )
        smart_value = getattr(smart_metrics, spec.attribute_name)

        if spec.copy_transform is not None:
            uncontrolled_value = spec.copy_transform(uncontrolled_value)
            smart_value = spec.copy_transform(smart_value)

        values[f"uncontrolled_{spec.attribute_name}"] = uncontrolled_value
        values[f"smart_{spec.attribute_name}"] = smart_value

        if spec.difference_field is None:
            continue

        if spec.difference_kind == "defined":
            values[spec.difference_field] = calculate_defined_difference(
                uncontrolled_value,
                smart_value,
            )
            continue

        values[spec.difference_field] = uncontrolled_value - smart_value

    return values


def build_scenario_difference_fields(
    metrics_a,
    metrics_b,
    specs: tuple[ScenarioDifferenceFieldSpec, ...],
    *,
    calculate_percent_change: Callable[[float, float], float | None],
) -> dict[str, Any]:
    """Return repeated Scenario B minus Scenario A fields from explicit specs."""
    values: dict[str, Any] = {}

    for spec in specs:
        value_a = getattr(metrics_a, spec.attribute_name)
        value_b = getattr(metrics_b, spec.attribute_name)

        if spec.difference_kind == "defined":
            difference = calculate_defined_difference(value_b, value_a)
        else:
            difference = value_b - value_a

        values[spec.difference_field] = difference

        if spec.percent_change_field is None:
            continue

        if difference is None:
            values[spec.percent_change_field] = None
            continue

        values[spec.percent_change_field] = calculate_percent_change(
            difference,
            value_a,
        )

    return values


def copy_metric_sequence(values: list[int] | list[float]) -> list[int] | list[float]:
    """Return a copied chart-ready metric sequence."""
    return list(values)


def copy_summary_rows_for_comparison(
    summary_rows,
) -> list[dict[str, Any]]:
    """Return feeder summary rows serialized for comparison payloads."""
    return [
        feeder_summary_metrics_to_dict(summary_row)
        for summary_row in summary_rows
    ]
