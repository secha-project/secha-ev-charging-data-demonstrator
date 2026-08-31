from dataclasses import dataclass, field
from typing import Any


SimulationResultData = dict[str, Any]
ChargingRequestResultData = dict[str, Any]
TransformerLoadingResultData = dict[str, Any]
FeederLoadingResultData = dict[str, Any]
GridLoadingResultData = dict[str, Any]
FeederPowerQualityResultData = dict[str, Any]
PowerQualityResultData = dict[str, Any]


@dataclass(frozen=True)
class ChargingRequestResult:
    """Raw request-level charging outcome for one modeled vehicle request."""

    request_id: str
    vehicle_index: int
    arrival_timestep: int
    departure_timestep: int
    charging_start_timestep: int | None
    charging_completion_timestep: int | None
    energy_requested_kwh: float
    energy_delivered_kwh: float
    unmet_energy_kwh: float
    waiting_time_hours: float | None
    not_started_within_window: bool
    delayed_start_reason: str | None
    unmet_energy_reason: str | None
    strategy_extended_occupancy: bool | None = None


@dataclass(frozen=True)
class TransformerLoadingResult:
    """Raw transformer loading series for one simulation run."""

    total_load_kw_by_timestep: list[float] = field(default_factory=list)
    loading_percent_by_timestep: list[float] = field(default_factory=list)
    overload_kw_by_timestep: list[float] = field(default_factory=list)


@dataclass(frozen=True)
class FeederLoadingResult:
    """Raw feeder loading series for one modeled feeder."""

    feeder_id: str
    charger_count: int
    total_load_kw_by_timestep: list[float] = field(default_factory=list)
    loading_percent_by_timestep: list[float] = field(default_factory=list)
    overload_kw_by_timestep: list[float] = field(default_factory=list)


@dataclass(frozen=True)
class FeederPowerQualityResult:
    """Raw feeder-level PQ series for one modeled feeder."""

    feeder_id: str
    harmonic_risk_score_by_timestep: list[float] = field(default_factory=list)
    current_imbalance_percent_by_timestep: list[float] = field(default_factory=list)


@dataclass(frozen=True)
class PowerQualityResult:
    """Grouped raw PQ outputs for the current harmonic and imbalance model.

    `feeder_power_quality_results` is an ordered raw contract. The list order
    should follow the deterministic feeder expansion order used by the
    Simulation Engine so later metrics and dashboard layers can consume
    feeder-level PQ series without re-sorting or inferring feeder identity.
    """

    harmonic_risk_score_by_timestep: list[float] = field(default_factory=list)
    current_imbalance_percent_by_timestep: list[float] = field(default_factory=list)
    overall_pq_risk_score_by_timestep: list[float] = field(default_factory=list)
    phase_a_load_kw_by_timestep: list[float] = field(default_factory=list)
    phase_b_load_kw_by_timestep: list[float] = field(default_factory=list)
    phase_c_load_kw_by_timestep: list[float] = field(default_factory=list)
    feeder_power_quality_results: list[FeederPowerQualityResult] = field(
        default_factory=list
    )


@dataclass(frozen=True)
class GridLoadingResult:
    """Grouped raw grid-loading outputs for the current transformer and feeder model.

    `feeder_loading_results` is an ordered raw contract. The list order follows
    the deterministic feeder expansion order used by the Simulation Engine so
    later metrics and dashboard layers can consume per-feeder series without
    re-sorting or inferring feeder identity.
    """

    transformer_loading: TransformerLoadingResult = field(
        default_factory=TransformerLoadingResult
    )
    feeder_loading_results: list[FeederLoadingResult] = field(default_factory=list)


@dataclass(frozen=True)
class SimulationResult:
    """Raw simulation outputs produced from a scenario."""

    daily_energy_demand: float
    configured_connection_capacity_kw: float
    installed_charger_capacity_kw: float
    available_site_charging_capacity_kw: float
    requested_load_profile_kw: list[float] = field(default_factory=list)
    delivered_load_profile_kw: list[float] = field(default_factory=list)
    delivered_energy: float = 0.0
    unmet_energy: float = 0.0
    charging_requests: list[ChargingRequestResult] = field(default_factory=list)
    arrivals_count_by_timestep: list[int] = field(default_factory=list)
    charging_start_count_by_timestep: list[int] = field(default_factory=list)
    charging_completion_count_by_timestep: list[int] = field(default_factory=list)
    requested_charger_slots_by_timestep: list[int] = field(default_factory=list)
    occupied_charger_count_by_timestep: list[int] = field(default_factory=list)
    waiting_vehicle_count_by_timestep: list[int] = field(default_factory=list)
    grid_loading: GridLoadingResult = field(default_factory=GridLoadingResult)
    power_quality: PowerQualityResult = field(default_factory=PowerQualityResult)

    def __post_init__(self) -> None:
        if not self.requested_load_profile_kw and self.delivered_load_profile_kw:
            object.__setattr__(
                self,
                "requested_load_profile_kw",
                list(self.delivered_load_profile_kw),
            )

        if len(self.requested_load_profile_kw) != len(self.delivered_load_profile_kw):
            raise ValueError(
                "requested_load_profile_kw and delivered_load_profile_kw must have "
                "matching timestep lengths."
            )

    @property
    def load_profile(self) -> list[float]:
        """Return the delivered charging load profile for compatibility."""
        return self.delivered_load_profile_kw

    @property
    def configured_connection_capacity(self) -> float:
        """Return configured connection capacity using a legacy-style name."""
        return self.configured_connection_capacity_kw

    @property
    def installed_charger_capacity(self) -> float:
        """Return installed charger capacity using a legacy-style name."""
        return self.installed_charger_capacity_kw

    @property
    def available_site_capacity(self) -> float:
        """Return available site charging capacity using a legacy-style name."""
        return self.available_site_charging_capacity_kw

    @property
    def uncontrolled_load_profile(self) -> list[float]:
        """Return the delivered profile using the legacy result field name."""
        return self.delivered_load_profile_kw


@dataclass(frozen=True)
class PlannerCandidateSimulationResult:
    """Minimal raw simulation contract for charger-planning candidate reruns.

    This lightweight contract keeps planner candidate evaluation inside the
    Simulation layer while avoiding transformer, feeder, and power-quality
    calculations that are irrelevant to the service rule.
    """

    daily_energy_demand: float
    request_count: int = 0
    started_request_waiting_times_hours: list[float] = field(default_factory=list)
    vehicles_waiting_count: int = 0
    vehicles_not_started_count: int = 0
    vehicles_with_unmet_energy_count: int = 0
    waiting_vehicle_count_by_timestep: list[int] = field(default_factory=list)


def charging_request_result_to_dict(
    result: ChargingRequestResult,
) -> ChargingRequestResultData:
    """Return a Dash-store-safe dictionary representation of one request result."""
    return {
        "request_id": result.request_id,
        "vehicle_index": result.vehicle_index,
        "arrival_timestep": result.arrival_timestep,
        "departure_timestep": result.departure_timestep,
        "charging_start_timestep": result.charging_start_timestep,
        "charging_completion_timestep": result.charging_completion_timestep,
        "energy_requested_kwh": result.energy_requested_kwh,
        "energy_delivered_kwh": result.energy_delivered_kwh,
        "unmet_energy_kwh": result.unmet_energy_kwh,
        "waiting_time_hours": result.waiting_time_hours,
        "not_started_within_window": result.not_started_within_window,
        "delayed_start_reason": result.delayed_start_reason,
        "unmet_energy_reason": result.unmet_energy_reason,
        "strategy_extended_occupancy": result.strategy_extended_occupancy,
    }


def charging_request_result_from_dict(
    data: ChargingRequestResultData,
) -> ChargingRequestResult:
    """Rebuild one request-level charging result from serialized data."""
    return ChargingRequestResult(
        request_id=data["request_id"],
        vehicle_index=data["vehicle_index"],
        arrival_timestep=data["arrival_timestep"],
        departure_timestep=data["departure_timestep"],
        charging_start_timestep=data["charging_start_timestep"],
        charging_completion_timestep=data["charging_completion_timestep"],
        energy_requested_kwh=data["energy_requested_kwh"],
        energy_delivered_kwh=data["energy_delivered_kwh"],
        unmet_energy_kwh=data["unmet_energy_kwh"],
        waiting_time_hours=data["waiting_time_hours"],
        not_started_within_window=data["not_started_within_window"],
        delayed_start_reason=data["delayed_start_reason"],
        unmet_energy_reason=data["unmet_energy_reason"],
        strategy_extended_occupancy=data.get("strategy_extended_occupancy"),
    )


def transformer_loading_result_to_dict(
    result: TransformerLoadingResult,
) -> TransformerLoadingResultData:
    """Return a Dash-store-safe dictionary representation of transformer loading."""
    return {
        "total_load_kw_by_timestep": list(result.total_load_kw_by_timestep),
        "loading_percent_by_timestep": list(result.loading_percent_by_timestep),
        "overload_kw_by_timestep": list(result.overload_kw_by_timestep),
    }


def transformer_loading_result_from_dict(
    data: TransformerLoadingResultData | None,
) -> TransformerLoadingResult:
    """Rebuild transformer loading outputs from serialized data."""
    resolved_data = data or {}
    return TransformerLoadingResult(
        total_load_kw_by_timestep=list(
            resolved_data.get("total_load_kw_by_timestep") or []
        ),
        loading_percent_by_timestep=list(
            resolved_data.get("loading_percent_by_timestep") or []
        ),
        overload_kw_by_timestep=list(
            resolved_data.get("overload_kw_by_timestep") or []
        ),
    )


def feeder_loading_result_to_dict(
    result: FeederLoadingResult,
) -> FeederLoadingResultData:
    """Return a Dash-store-safe dictionary representation of feeder loading."""
    return {
        "feeder_id": result.feeder_id,
        "charger_count": result.charger_count,
        "total_load_kw_by_timestep": list(result.total_load_kw_by_timestep),
        "loading_percent_by_timestep": list(result.loading_percent_by_timestep),
        "overload_kw_by_timestep": list(result.overload_kw_by_timestep),
    }


def feeder_loading_result_from_dict(
    data: FeederLoadingResultData,
) -> FeederLoadingResult:
    """Rebuild feeder loading outputs from serialized data."""
    return FeederLoadingResult(
        feeder_id=data["feeder_id"],
        charger_count=data["charger_count"],
        total_load_kw_by_timestep=list(data.get("total_load_kw_by_timestep") or []),
        loading_percent_by_timestep=list(data.get("loading_percent_by_timestep") or []),
        overload_kw_by_timestep=list(data.get("overload_kw_by_timestep") or []),
    )


def feeder_power_quality_result_to_dict(
    result: FeederPowerQualityResult,
) -> FeederPowerQualityResultData:
    """Return a Dash-store-safe dictionary representation of feeder PQ output."""
    return {
        "feeder_id": result.feeder_id,
        "harmonic_risk_score_by_timestep": list(
            result.harmonic_risk_score_by_timestep
        ),
        "current_imbalance_percent_by_timestep": list(
            result.current_imbalance_percent_by_timestep
        ),
    }


def feeder_power_quality_result_from_dict(
    data: FeederPowerQualityResultData,
) -> FeederPowerQualityResult:
    """Rebuild feeder PQ outputs from serialized data."""
    return FeederPowerQualityResult(
        feeder_id=data["feeder_id"],
        harmonic_risk_score_by_timestep=list(
            data.get("harmonic_risk_score_by_timestep") or []
        ),
        current_imbalance_percent_by_timestep=list(
            data.get("current_imbalance_percent_by_timestep") or []
        ),
    )


def grid_loading_result_to_dict(result: GridLoadingResult) -> GridLoadingResultData:
    """Return a Dash-store-safe dictionary representation of grid loading."""
    return {
        "transformer_loading": transformer_loading_result_to_dict(
            result.transformer_loading
        ),
        "feeder_loading_results": [
            feeder_loading_result_to_dict(feeder_result)
            for feeder_result in result.feeder_loading_results
        ],
    }


def power_quality_result_to_dict(
    result: PowerQualityResult,
) -> PowerQualityResultData:
    """Return a Dash-store-safe dictionary representation of PQ output."""
    return {
        "harmonic_risk_score_by_timestep": list(
            result.harmonic_risk_score_by_timestep
        ),
        "current_imbalance_percent_by_timestep": list(
            result.current_imbalance_percent_by_timestep
        ),
        "overall_pq_risk_score_by_timestep": list(
            result.overall_pq_risk_score_by_timestep
        ),
        "phase_a_load_kw_by_timestep": list(result.phase_a_load_kw_by_timestep),
        "phase_b_load_kw_by_timestep": list(result.phase_b_load_kw_by_timestep),
        "phase_c_load_kw_by_timestep": list(result.phase_c_load_kw_by_timestep),
        "feeder_power_quality_results": [
            feeder_power_quality_result_to_dict(feeder_result)
            for feeder_result in result.feeder_power_quality_results
        ],
    }


def power_quality_result_from_dict(
    data: PowerQualityResultData | None,
) -> PowerQualityResult:
    """Rebuild grouped PQ outputs from serialized data."""
    resolved_data = data or {}
    return PowerQualityResult(
        harmonic_risk_score_by_timestep=list(
            resolved_data.get("harmonic_risk_score_by_timestep") or []
        ),
        current_imbalance_percent_by_timestep=list(
            resolved_data.get("current_imbalance_percent_by_timestep") or []
        ),
        overall_pq_risk_score_by_timestep=list(
            resolved_data.get("overall_pq_risk_score_by_timestep") or []
        ),
        phase_a_load_kw_by_timestep=list(
            resolved_data.get("phase_a_load_kw_by_timestep") or []
        ),
        phase_b_load_kw_by_timestep=list(
            resolved_data.get("phase_b_load_kw_by_timestep") or []
        ),
        phase_c_load_kw_by_timestep=list(
            resolved_data.get("phase_c_load_kw_by_timestep") or []
        ),
        feeder_power_quality_results=[
            feeder_power_quality_result_from_dict(feeder_result_data)
            for feeder_result_data in (
                resolved_data.get("feeder_power_quality_results") or []
            )
        ],
    )


def grid_loading_result_from_dict(
    data: GridLoadingResultData | None,
) -> GridLoadingResult:
    """Rebuild grouped grid-loading outputs from serialized data."""
    resolved_data = data or {}
    return GridLoadingResult(
        transformer_loading=transformer_loading_result_from_dict(
            resolved_data.get("transformer_loading", {})
        ),
        feeder_loading_results=[
            feeder_loading_result_from_dict(feeder_result_data)
            for feeder_result_data in (
                resolved_data.get("feeder_loading_results") or []
            )
        ],
    )


def simulation_result_to_dict(result: SimulationResult) -> SimulationResultData:
    """Return a Dash-store-safe dictionary representation of simulation output."""
    delivered_load_profile = list(result.delivered_load_profile_kw)
    return {
        "daily_energy_demand": result.daily_energy_demand,
        "configured_connection_capacity_kw": (
            result.configured_connection_capacity_kw
        ),
        "installed_charger_capacity_kw": result.installed_charger_capacity_kw,
        "available_site_charging_capacity_kw": (
            result.available_site_charging_capacity_kw
        ),
        "requested_load_profile_kw": list(result.requested_load_profile_kw),
        "delivered_load_profile_kw": delivered_load_profile,
        "load_profile": delivered_load_profile,
        "uncontrolled_load_profile": delivered_load_profile,
        "delivered_energy": result.delivered_energy,
        "unmet_energy": result.unmet_energy,
        "charging_requests": [
            charging_request_result_to_dict(request_result)
            for request_result in result.charging_requests
        ],
        "arrivals_count_by_timestep": list(result.arrivals_count_by_timestep),
        "charging_start_count_by_timestep": list(
            result.charging_start_count_by_timestep
        ),
        "charging_completion_count_by_timestep": list(
            result.charging_completion_count_by_timestep
        ),
        "requested_charger_slots_by_timestep": list(
            result.requested_charger_slots_by_timestep
        ),
        "occupied_charger_count_by_timestep": list(
            result.occupied_charger_count_by_timestep
        ),
        "waiting_vehicle_count_by_timestep": list(
            result.waiting_vehicle_count_by_timestep
        ),
        "grid_loading": grid_loading_result_to_dict(result.grid_loading),
        "power_quality": power_quality_result_to_dict(result.power_quality),
    }


def simulation_result_from_dict(data: SimulationResultData) -> SimulationResult:
    """Rebuild a raw simulation result from serialized result data."""
    delivered_load_profile_kw = list(
        data.get(
            "delivered_load_profile_kw",
            data.get("uncontrolled_load_profile", data.get("load_profile", [])),
        )
    )
    return SimulationResult(
        daily_energy_demand=data["daily_energy_demand"],
        configured_connection_capacity_kw=data.get(
            "configured_connection_capacity_kw",
            data.get("available_site_capacity", 0.0),
        ),
        installed_charger_capacity_kw=data.get(
            "installed_charger_capacity_kw",
            data.get("installed_charger_capacity", 0.0),
        ),
        available_site_charging_capacity_kw=data.get(
            "available_site_charging_capacity_kw",
            data.get("available_site_capacity", 0.0),
        ),
        requested_load_profile_kw=list(
            data.get("requested_load_profile_kw", delivered_load_profile_kw)
        ),
        delivered_load_profile_kw=delivered_load_profile_kw,
        delivered_energy=data["delivered_energy"],
        unmet_energy=data["unmet_energy"],
        charging_requests=[
            charging_request_result_from_dict(request_data)
            for request_data in data.get("charging_requests", [])
        ],
        arrivals_count_by_timestep=list(data.get("arrivals_count_by_timestep", [])),
        charging_start_count_by_timestep=list(
            data.get("charging_start_count_by_timestep", [])
        ),
        charging_completion_count_by_timestep=list(
            data.get("charging_completion_count_by_timestep", [])
        ),
        requested_charger_slots_by_timestep=list(
            data.get("requested_charger_slots_by_timestep", [])
        ),
        occupied_charger_count_by_timestep=list(
            data.get("occupied_charger_count_by_timestep", [])
        ),
        waiting_vehicle_count_by_timestep=list(
            data.get("waiting_vehicle_count_by_timestep", [])
        ),
        grid_loading=grid_loading_result_from_dict(data.get("grid_loading", {})),
        power_quality=power_quality_result_from_dict(data.get("power_quality", {})),
    )
