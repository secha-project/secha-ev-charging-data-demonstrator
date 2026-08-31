from collections.abc import Sequence
from dataclasses import dataclass, fields
from datetime import time
from enum import Enum
import math
from numbers import Real
from typing import Any


class ChargingStrategy(Enum):
    """Supported charging strategy selections for a scenario."""

    UNCONTROLLED = "Uncontrolled"
    SMART = "Smart Charging"


class ArrivalProfileShape(Enum):
    """Supported deterministic arrival profile selections for a scenario."""

    FRONT_LOADED = "front_loaded"
    FRONT_WEIGHTED = "front_weighted"
    MID_PEAK = "mid_peak"
    EVEN = "even"


class ArrivalMode(Enum):
    """Supported arrival-generation modes for a scenario."""

    PROFILE = "profile"
    RANDOM = "random"


class DepartureMode(Enum):
    """Supported departure-deadline modes for a scenario."""

    WINDOW_END = "window_end"
    SESSION_DWELL = "session_dwell"


class FeederEVAllocationMethod(Enum):
    """Supported EV-load allocation methods for feeder loading."""

    BY_CHARGER_COUNT = "by_charger_count"
    BY_CONFIGURED_SHARE = "by_configured_share"


class PowerQualityPhaseAllocationMethod(Enum):
    """Supported deterministic phase-allocation methods for PQ modeling."""

    BALANCED_ROUND_ROBIN = "balanced_round_robin"
    FRONT_LOADED_PHASE_A = "front_loaded_phase_a"


@dataclass(frozen=True)
class Scenario:
    """Validated input data for the simulation layer.

    The scenario layer stores charging system assumptions only. It does not
    calculate charging durations or perform simulations.

    Standard ``Scenario(...)`` construction is intentionally strict for
    user-facing and dashboard-driven workflows. Internal model-only boundary
    cases that need ``0`` vehicles or ``0`` chargers should use
    ``create_internal_scenario(...)`` instead.

    Attributes:
        vehicles: Number of vehicles requiring charging.
        daily_energy_per_vehicle: Average daily charging demand per vehicle in kWh.
        charger_count: Number of available chargers.
        charger_power: Rated power per charger in kW.
        grid_capacity: Available grid connection capacity in kW.
        request_energy_variability_percent: Deterministic per-request energy
            spread around the daily energy assumption, expressed as a percent.
        transformer_capacity_kw: Rated transformer loading limit in kW.
        transformer_other_load_kw: Deterministic non-EV transformer load in kW.
        feeder_count: Number of modeled feeders.
        feeder_capacity_kw: Rated loading limit per feeder in kW.
        feeder_base_load_kw: Deterministic non-EV load per feeder in kW.
        feeder_ev_allocation_method: Deterministic feeder EV-load allocation rule.
        feeder_allocation_shares: Optional deterministic feeder load shares used
            when ``feeder_ev_allocation_method`` is ``by_configured_share``.
        single_phase_charger_share_percent: Share of chargers modeled as
            single-phase PQ sources in percent.
        charger_harmonic_factor: Simplified relative harmonic-severity factor
            for the modeled charger mix.
        power_quality_phase_allocation_method: Deterministic phase-allocation
            rule for simplified current-imbalance modeling.
        planning_margin_percent: Extra planning headroom for future capacity sizing.
        charging_window_start: Time of day when charging is allowed to start.
        charging_window_end: Time of day when charging is allowed to end.
        arrival_window_start: Time of day when vehicle arrivals begin.
        arrival_window_end: Time of day when vehicle arrivals finish.
        arrival_mode: Arrival-generation mode for the vehicle-arrival window.
        arrival_profile_shape: Deterministic arrival distribution selection.
        departure_mode: Departure-deadline mode for charging requests.
        session_dwell_minutes: Optional session dwell time in minutes.
        departure_time_spread_minutes: Deterministic departure/deadline spread
            around the scenario baseline, in minutes.
        charger_service_max_waiting_time_minutes: Maximum waiting time the
            charger-planning service rule tolerates for this scenario, in
            minutes.
        charging_strategy: User-selected charging strategy.
    """

    vehicles: int
    daily_energy_per_vehicle: float
    charger_count: int
    charger_power: float
    grid_capacity: float
    request_energy_variability_percent: float = 0.0
    transformer_capacity_kw: float | None = None
    transformer_other_load_kw: float = 0.0
    feeder_count: int = 1
    feeder_capacity_kw: float | None = None
    feeder_base_load_kw: float = 0.0
    feeder_ev_allocation_method: FeederEVAllocationMethod = (
        FeederEVAllocationMethod.BY_CHARGER_COUNT
    )
    feeder_allocation_shares: tuple[float, ...] | None = None
    single_phase_charger_share_percent: float = 0.0
    charger_harmonic_factor: float = 1.0
    power_quality_phase_allocation_method: PowerQualityPhaseAllocationMethod = (
        PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
    )
    planning_margin_percent: float = 10.0
    charging_window_start: time = time(0, 0)
    charging_window_end: time = time(0, 0)
    arrival_window_start: time | None = None
    arrival_window_end: time | None = None
    arrival_mode: ArrivalMode = ArrivalMode.PROFILE
    arrival_profile_shape: ArrivalProfileShape = ArrivalProfileShape.FRONT_LOADED
    departure_mode: DepartureMode = DepartureMode.WINDOW_END
    session_dwell_minutes: int | None = None
    departure_time_spread_minutes: int = 0
    charger_service_max_waiting_time_minutes: int = 30
    charging_strategy: ChargingStrategy = ChargingStrategy.UNCONTROLLED

    def __post_init__(self) -> None:
        _validate_scenario_values(self)


def create_internal_scenario(
    *,
    vehicles: int,
    daily_energy_per_vehicle: float,
    charger_count: int,
    charger_power: float,
    grid_capacity: float,
    request_energy_variability_percent: float = 0.0,
    transformer_capacity_kw: float | None = None,
    transformer_other_load_kw: float = 0.0,
    feeder_count: int = 1,
    feeder_capacity_kw: float | None = None,
    feeder_base_load_kw: float = 0.0,
    feeder_ev_allocation_method: FeederEVAllocationMethod = (
        FeederEVAllocationMethod.BY_CHARGER_COUNT
    ),
    feeder_allocation_shares: Sequence[float] | None = None,
    single_phase_charger_share_percent: float = 0.0,
    charger_harmonic_factor: float = 1.0,
    power_quality_phase_allocation_method: PowerQualityPhaseAllocationMethod = (
        PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
    ),
    planning_margin_percent: float = 10.0,
    charging_window_start: time = time(0, 0),
    charging_window_end: time = time(0, 0),
    arrival_window_start: time | None = None,
    arrival_window_end: time | None = None,
    arrival_mode: ArrivalMode = ArrivalMode.PROFILE,
    arrival_profile_shape: ArrivalProfileShape = ArrivalProfileShape.FRONT_LOADED,
    departure_mode: DepartureMode = DepartureMode.WINDOW_END,
    session_dwell_minutes: int | None = None,
    departure_time_spread_minutes: int = 0,
    charger_service_max_waiting_time_minutes: int = 30,
    charging_strategy: ChargingStrategy = ChargingStrategy.UNCONTROLLED,
) -> Scenario:
    """Return an internal-only scenario that supports zero-value boundaries.

    This helper exists for deterministic simulation/model boundary cases such as:

    * zero vehicles with available chargers
    * zero chargers with charging demand
    * zero vehicles and zero chargers

    The standard ``Scenario(...)`` constructor remains strict for user-facing
    workflows and still rejects ``0`` vehicles and ``0`` chargers.
    """

    scenario = object.__new__(Scenario)
    for field_name, value in (
        ("vehicles", vehicles),
        ("daily_energy_per_vehicle", daily_energy_per_vehicle),
        (
            "request_energy_variability_percent",
            request_energy_variability_percent,
        ),
        ("charger_count", charger_count),
        ("charger_power", charger_power),
        ("grid_capacity", grid_capacity),
        ("transformer_capacity_kw", transformer_capacity_kw),
        ("transformer_other_load_kw", transformer_other_load_kw),
        ("feeder_count", feeder_count),
        ("feeder_capacity_kw", feeder_capacity_kw),
        ("feeder_base_load_kw", feeder_base_load_kw),
        ("feeder_ev_allocation_method", feeder_ev_allocation_method),
        ("feeder_allocation_shares", feeder_allocation_shares),
        ("single_phase_charger_share_percent", single_phase_charger_share_percent),
        ("charger_harmonic_factor", charger_harmonic_factor),
        (
            "power_quality_phase_allocation_method",
            power_quality_phase_allocation_method,
        ),
        ("planning_margin_percent", planning_margin_percent),
        ("charging_window_start", charging_window_start),
        ("charging_window_end", charging_window_end),
        ("arrival_window_start", arrival_window_start),
        ("arrival_window_end", arrival_window_end),
        ("arrival_mode", arrival_mode),
        ("arrival_profile_shape", arrival_profile_shape),
        ("departure_mode", departure_mode),
        ("session_dwell_minutes", session_dwell_minutes),
        ("departure_time_spread_minutes", departure_time_spread_minutes),
        (
            "charger_service_max_waiting_time_minutes",
            charger_service_max_waiting_time_minutes,
        ),
        ("charging_strategy", charging_strategy),
    ):
        object.__setattr__(scenario, field_name, value)

    _validate_scenario_values(
        scenario,
        allow_zero_vehicles=True,
        allow_zero_charger_count=True,
    )
    return scenario


def copy_scenario_with_updates(
    scenario: Scenario,
    **updates: Any,
) -> Scenario:
    """Return a copied scenario while preserving internal zero-value support."""

    values = {
        field.name: getattr(scenario, field.name)
        for field in fields(Scenario)
    }
    values.update(updates)

    if values["vehicles"] == 0 or values["charger_count"] == 0:
        return create_internal_scenario(**values)

    return Scenario(**values)


def _validate_scenario_values(
    scenario: Scenario,
    *,
    allow_zero_vehicles: bool = False,
    allow_zero_charger_count: bool = False,
) -> None:
    _apply_grid_asset_defaults(scenario)

    for field_name, value in (
        ("vehicles", scenario.vehicles),
        ("daily_energy_per_vehicle", scenario.daily_energy_per_vehicle),
        (
            "request_energy_variability_percent",
            scenario.request_energy_variability_percent,
        ),
        ("charger_count", scenario.charger_count),
        ("charger_power", scenario.charger_power),
        ("grid_capacity", scenario.grid_capacity),
        ("transformer_capacity_kw", scenario.transformer_capacity_kw),
        ("transformer_other_load_kw", scenario.transformer_other_load_kw),
        ("feeder_count", scenario.feeder_count),
        ("feeder_capacity_kw", scenario.feeder_capacity_kw),
        ("feeder_base_load_kw", scenario.feeder_base_load_kw),
        (
            "charger_service_max_waiting_time_minutes",
            scenario.charger_service_max_waiting_time_minutes,
        ),
        (
            "single_phase_charger_share_percent",
            scenario.single_phase_charger_share_percent,
        ),
        ("charger_harmonic_factor", scenario.charger_harmonic_factor),
    ):
        _validate_numeric_value(field_name, value)

    _normalize_whole_number_field(scenario, "vehicles")
    _normalize_whole_number_field(scenario, "charger_count")
    _normalize_whole_number_field(scenario, "feeder_count")

    _validate_non_negative_or_positive(
        "vehicles",
        scenario.vehicles,
        allow_zero=allow_zero_vehicles,
    )
    _validate_non_negative_or_positive(
        "charger_count",
        scenario.charger_count,
        allow_zero=allow_zero_charger_count,
    )
    _validate_non_negative_or_positive(
        "feeder_count",
        scenario.feeder_count,
        allow_zero=False,
    )

    for field_name, value in (
        ("daily_energy_per_vehicle", scenario.daily_energy_per_vehicle),
        ("charger_power", scenario.charger_power),
        ("grid_capacity", scenario.grid_capacity),
        ("transformer_capacity_kw", scenario.transformer_capacity_kw),
        ("feeder_capacity_kw", scenario.feeder_capacity_kw),
    ):
        if value <= 0:
            raise ValueError(f"{field_name} must be greater than zero.")

    for field_name, value in (
        ("transformer_other_load_kw", scenario.transformer_other_load_kw),
        ("feeder_base_load_kw", scenario.feeder_base_load_kw),
        (
            "single_phase_charger_share_percent",
            scenario.single_phase_charger_share_percent,
        ),
        ("charger_harmonic_factor", scenario.charger_harmonic_factor),
        ("planning_margin_percent", scenario.planning_margin_percent),
        (
            "request_energy_variability_percent",
            scenario.request_energy_variability_percent,
        ),
    ):
        _validate_numeric_value(field_name, value)
        if value < 0:
            raise ValueError(f"{field_name} must be non-negative.")

    _validate_percentage_range(
        "single_phase_charger_share_percent",
        scenario.single_phase_charger_share_percent,
    )
    _validate_percentage_range(
        "request_energy_variability_percent",
        scenario.request_energy_variability_percent,
    )

    _apply_arrival_window_defaults(scenario)

    for field_name, value in (
        ("charging_window_start", scenario.charging_window_start),
        ("charging_window_end", scenario.charging_window_end),
        ("arrival_window_start", scenario.arrival_window_start),
        ("arrival_window_end", scenario.arrival_window_end),
    ):
        if not isinstance(value, time):
            raise TypeError(f"{field_name} must be a datetime.time object.")

    _validate_arrival_window_alignment(scenario)
    _validate_arrival_window_compatibility(scenario)

    if not isinstance(scenario.arrival_mode, ArrivalMode):
        raise TypeError("arrival_mode must be an ArrivalMode.")

    if not isinstance(scenario.arrival_profile_shape, ArrivalProfileShape):
        raise TypeError("arrival_profile_shape must be an ArrivalProfileShape.")

    if not isinstance(scenario.departure_mode, DepartureMode):
        raise TypeError("departure_mode must be a DepartureMode.")

    if not isinstance(
        scenario.feeder_ev_allocation_method,
        FeederEVAllocationMethod,
    ):
        raise TypeError(
            "feeder_ev_allocation_method must be a FeederEVAllocationMethod."
        )

    _validate_feeder_allocation_shares(scenario)

    if not isinstance(
        scenario.power_quality_phase_allocation_method,
        PowerQualityPhaseAllocationMethod,
    ):
        raise TypeError(
            "power_quality_phase_allocation_method must be a "
            "PowerQualityPhaseAllocationMethod."
        )

    _validate_session_dwell_minutes(scenario)
    _validate_departure_time_spread_minutes(scenario)
    _validate_charger_service_max_waiting_time_minutes(scenario)

    if not isinstance(scenario.charging_strategy, ChargingStrategy):
        raise TypeError("charging_strategy must be a ChargingStrategy.")


def _validate_non_negative_or_positive(
    field_name: str,
    value: Any,
    *,
    allow_zero: bool,
) -> None:
    if value < 0:
        if allow_zero:
            raise ValueError(f"{field_name} must be zero or greater.")
        raise ValueError(f"{field_name} must be greater than zero.")

    if value == 0 and not allow_zero:
        raise ValueError(f"{field_name} must be greater than zero.")


def _validate_numeric_value(field_name: str, value: Any) -> None:
    """Raise a clear error for missing or non-numeric scenario values."""
    if value is None:
        raise ValueError(f"{field_name} is required.")

    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field_name} must be numeric.")


def _normalize_whole_number_field(scenario: Scenario, field_name: str) -> None:
    numeric_value = getattr(scenario, field_name)
    rounded_value = round(float(numeric_value))
    if not math.isclose(float(numeric_value), rounded_value, abs_tol=1e-9):
        raise ValueError(f"{field_name} must be a whole number.")

    object.__setattr__(scenario, field_name, int(rounded_value))


def _validate_percentage_range(field_name: str, value: float) -> None:
    if value > 100:
        raise ValueError(f"{field_name} must be 100 or less.")


def _validate_feeder_allocation_shares(scenario: Scenario) -> None:
    shares = scenario.feeder_allocation_shares

    if shares is None:
        if (
            scenario.feeder_ev_allocation_method
            is FeederEVAllocationMethod.BY_CONFIGURED_SHARE
        ):
            raise ValueError(
                "feeder_allocation_shares is required when "
                "feeder_ev_allocation_method is by_configured_share."
            )
        return

    if isinstance(shares, (str, bytes)) or not isinstance(shares, Sequence):
        raise TypeError(
            "feeder_allocation_shares must be a sequence of numeric values."
        )

    normalized_shares: list[float] = []
    for share in shares:
        _validate_numeric_value("feeder_allocation_shares", share)
        if share < 0:
            raise ValueError("feeder_allocation_shares must be non-negative.")
        normalized_shares.append(float(share))

    if len(normalized_shares) != scenario.feeder_count:
        raise ValueError(
            "feeder_allocation_shares length must match feeder_count."
        )

    if sum(normalized_shares) <= 0:
        raise ValueError(
            "feeder_allocation_shares total must be greater than zero."
        )

    object.__setattr__(
        scenario,
        "feeder_allocation_shares",
        tuple(normalized_shares),
    )


def _apply_arrival_window_defaults(scenario: Scenario) -> None:
    start = scenario.arrival_window_start
    end = scenario.arrival_window_end

    if start is None and end is None:
        object.__setattr__(
            scenario,
            "arrival_window_start",
            scenario.charging_window_start,
        )
        object.__setattr__(
            scenario,
            "arrival_window_end",
            scenario.charging_window_start,
        )
        return

    if start is None or end is None:
        raise ValueError(
            "arrival_window_start and arrival_window_end must both be provided "
            "when either is set."
        )


def _apply_grid_asset_defaults(scenario: Scenario) -> None:
    if scenario.transformer_capacity_kw is None:
        object.__setattr__(
            scenario,
            "transformer_capacity_kw",
            scenario.grid_capacity,
        )

    if scenario.feeder_capacity_kw is None:
        object.__setattr__(
            scenario,
            "feeder_capacity_kw",
            scenario.transformer_capacity_kw,
        )


def _validate_arrival_window_alignment(scenario: Scenario) -> None:
    for field_name, value in (
        ("arrival_window_start", scenario.arrival_window_start),
        ("arrival_window_end", scenario.arrival_window_end),
    ):
        if not _is_fifteen_minute_aligned(value):
            raise ValueError(f"{field_name} must align to 15-minute timesteps.")


def _validate_arrival_window_compatibility(scenario: Scenario) -> None:
    charging_duration_minutes = _window_duration_minutes(
        scenario.charging_window_start,
        scenario.charging_window_end,
    )
    arrival_start_offset = _offset_from_window_start_minutes(
        scenario.charging_window_start,
        scenario.arrival_window_start,
    )
    arrival_end_offset = _offset_from_window_start_minutes(
        scenario.charging_window_start,
        scenario.arrival_window_end,
    )

    if scenario.arrival_window_start == scenario.arrival_window_end:
        if arrival_start_offset > charging_duration_minutes:
            raise ValueError(
                "vehicle-arrival window must fall within the configured charging-allowed window."
            )
        return

    normalized_arrival_end_offset = arrival_end_offset
    if normalized_arrival_end_offset <= arrival_start_offset:
        normalized_arrival_end_offset += MINUTES_PER_DAY

    if normalized_arrival_end_offset > charging_duration_minutes:
        raise ValueError(
            "vehicle-arrival window must fall within the configured charging-allowed window."
        )


def _is_fifteen_minute_aligned(value: time) -> bool:
    return (
        value.minute % 15 == 0
        and value.second == 0
        and value.microsecond == 0
    )


def _validate_session_dwell_minutes(scenario: Scenario) -> None:
    if scenario.session_dwell_minutes is None:
        if scenario.departure_mode is DepartureMode.SESSION_DWELL:
            raise ValueError(
                "session_dwell_minutes is required when departure_mode uses "
                "session dwell."
            )
        return

    _validate_numeric_value("session_dwell_minutes", scenario.session_dwell_minutes)

    if scenario.session_dwell_minutes <= 0:
        raise ValueError("session_dwell_minutes must be greater than zero.")

    if int(scenario.session_dwell_minutes) != scenario.session_dwell_minutes:
        raise ValueError("session_dwell_minutes must be a whole number of minutes.")

    normalized_session_dwell_minutes = int(scenario.session_dwell_minutes)
    if normalized_session_dwell_minutes % 15 != 0:
        raise ValueError("session_dwell_minutes must align to 15-minute timesteps.")

    object.__setattr__(
        scenario,
        "session_dwell_minutes",
        normalized_session_dwell_minutes,
    )


def _validate_departure_time_spread_minutes(scenario: Scenario) -> None:
    _validate_numeric_value(
        "departure_time_spread_minutes",
        scenario.departure_time_spread_minutes,
    )

    if scenario.departure_time_spread_minutes < 0:
        raise ValueError("departure_time_spread_minutes must be non-negative.")

    if int(scenario.departure_time_spread_minutes) != scenario.departure_time_spread_minutes:
        raise ValueError(
            "departure_time_spread_minutes must be a whole number of minutes."
        )

    normalized_departure_time_spread_minutes = int(
        scenario.departure_time_spread_minutes
    )
    if normalized_departure_time_spread_minutes % 15 != 0:
        raise ValueError(
            "departure_time_spread_minutes must align to 15-minute timesteps."
        )

    object.__setattr__(
        scenario,
        "departure_time_spread_minutes",
        normalized_departure_time_spread_minutes,
    )


def _validate_charger_service_max_waiting_time_minutes(
    scenario: Scenario,
) -> None:
    _validate_numeric_value(
        "charger_service_max_waiting_time_minutes",
        scenario.charger_service_max_waiting_time_minutes,
    )

    if scenario.charger_service_max_waiting_time_minutes < 0:
        raise ValueError(
            "charger_service_max_waiting_time_minutes must be non-negative."
        )

    if (
        int(scenario.charger_service_max_waiting_time_minutes)
        != scenario.charger_service_max_waiting_time_minutes
    ):
        raise ValueError(
            "charger_service_max_waiting_time_minutes must be a whole number of minutes."
        )

    normalized_waiting_time_minutes = int(
        scenario.charger_service_max_waiting_time_minutes
    )
    if normalized_waiting_time_minutes % 15 != 0:
        raise ValueError(
            "charger_service_max_waiting_time_minutes must align to 15-minute timesteps."
        )

    object.__setattr__(
        scenario,
        "charger_service_max_waiting_time_minutes",
        normalized_waiting_time_minutes,
    )


MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
MINUTES_PER_DAY = HOURS_PER_DAY * MINUTES_PER_HOUR


def _window_duration_minutes(start: time, end: time) -> int:
    start_minutes = _time_to_minutes(start)
    end_minutes = _time_to_minutes(end)
    duration_minutes = end_minutes - start_minutes
    if duration_minutes <= 0:
        duration_minutes += MINUTES_PER_DAY
    return duration_minutes


def _offset_from_window_start_minutes(window_start: time, value: time) -> int:
    return (_time_to_minutes(value) - _time_to_minutes(window_start)) % MINUTES_PER_DAY


def _time_to_minutes(value: time) -> int:
    return value.hour * MINUTES_PER_HOUR + value.minute
