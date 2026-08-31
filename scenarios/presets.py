"""Central registry of scenario presets."""

from dataclasses import dataclass
from datetime import time

from scenarios.field_schema import (
    format_scenario_summary_value,
    get_scenario_summary_label,
)
from scenarios.scenario import (
    ArrivalMode,
    ArrivalProfileShape,
    DepartureMode,
    FeederEVAllocationMethod,
    PowerQualityPhaseAllocationMethod,
    Scenario,
)


DEFAULT_SCENARIO_PRESET_ID = "heavy_duty"
PUBLIC_FAST_CHARGING_PRESET_ID = "public_fast_charging"
WORKPLACE_CHARGING_PRESET_ID = "workplace_charging"
CONSTRAINED_HEAVY_DUTY_PEAK_SHAVING_PRESET_ID = (
    "constrained_heavy_duty_peak_shaving"
)
CHARGER_LIMITED_DEPOT_PRESET_ID = "charger_limited_depot"
CONCENTRATED_ARRIVAL_WORKPLACE_CHARGING_PRESET_ID = (
    "concentrated_arrival_workplace_charging"
)
PQ_SENSITIVE_AC_CHARGING_PRESET_ID = "pq_sensitive_ac_charging"


@dataclass(frozen=True)
class ScenarioPresetParameterSummary:
    """One display summary row for preset default values."""

    summary_id: str
    label: str | None = None


def _summary(summary_id: str, *, label: str | None = None) -> ScenarioPresetParameterSummary:
    return ScenarioPresetParameterSummary(summary_id=summary_id, label=label)


@dataclass(frozen=True)
class ScenarioPreset:
    """A reusable named scenario preset independent of any UI."""

    preset_id: str
    label: str
    purpose: str
    key_assumptions: tuple[str, ...]
    parameter_summaries: tuple[ScenarioPresetParameterSummary, ...]
    scenario: Scenario | None = None

    @property
    def default_parameters(self) -> tuple[tuple[str, str], ...]:
        """Return display-ready default parameter rows derived from scenario defaults."""

        if self.scenario is None:
            return ()

        return tuple(
            (
                summary.label or get_scenario_summary_label(summary.summary_id),
                format_scenario_summary_value(summary.summary_id, self.scenario),
            )
            for summary in self.parameter_summaries
        )


_SCENARIO_PRESETS = (
    ScenarioPreset(
        preset_id=DEFAULT_SCENARIO_PRESET_ID,
        label="Heavy-duty",
        purpose=(
            "Depot-style heavy-duty charging scenario used as the MVP "
            "reference configuration."
        ),
        key_assumptions=(
            "Fleet vehicles begin arriving near the start of the charging-allowed window.",
            "Energy demand is modeled per vehicle per day.",
            "Charging is evaluated across an overnight depot window.",
        ),
        parameter_summaries=(
            _summary("vehicles"),
            _summary("daily_energy_per_vehicle"),
            _summary("charger_count", label="Charger count"),
            _summary("charger_power", label="Charger power"),
            _summary("grid_capacity", label="Grid capacity"),
            _summary("charging_window"),
        ),
        scenario=Scenario(
            vehicles=50,
            daily_energy_per_vehicle=150.0,
            charger_count=10,
            charger_power=150.0,
            grid_capacity=1000.0,
            request_energy_variability_percent=10.0,
            transformer_capacity_kw=1250.0,
            transformer_other_load_kw=50.0,
            feeder_count=2,
            feeder_capacity_kw=700.0,
            feeder_base_load_kw=25.0,
            feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CHARGER_COUNT,
            single_phase_charger_share_percent=0.0,
            charger_harmonic_factor=1.0,
            power_quality_phase_allocation_method=(
                PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
            ),
            planning_margin_percent=10.0,
            charging_window_start=time(17, 0),
            charging_window_end=time(6, 0),
            departure_time_spread_minutes=60,
            charger_service_max_waiting_time_minutes=120,
        ),
    ),
    ScenarioPreset(
        preset_id=PUBLIC_FAST_CHARGING_PRESET_ID,
        label="Public Fast Charging",
        purpose=(
            "High-power public charging hub scenario for short-stay customer "
            "charging sessions."
        ),
        key_assumptions=(
            "Higher-turnover charging sessions than depot or workplace charging.",
            "Pseudo-random arrivals are concentrated around the busier part of the day.",
            "Requested energy scales with the modeled short-stay session dwell time.",
        ),
        parameter_summaries=(
            _summary("vehicles", label="Charging sessions"),
            _summary("daily_energy_per_vehicle", label="Energy demand per session"),
            _summary("session_dwell_minutes", label="Typical dwell time"),
            _summary("charger_count", label="Charger count"),
            _summary("charger_power", label="Charger power"),
            _summary("grid_capacity", label="Grid capacity"),
        ),
        scenario=Scenario(
            vehicles=48,
            daily_energy_per_vehicle=50.0,
            charger_count=6,
            charger_power=300.0,
            grid_capacity=1200.0,
            request_energy_variability_percent=25.0,
            transformer_capacity_kw=1500.0,
            transformer_other_load_kw=75.0,
            feeder_count=2,
            feeder_capacity_kw=750.0,
            feeder_base_load_kw=37.5,
            feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CHARGER_COUNT,
            single_phase_charger_share_percent=0.0,
            charger_harmonic_factor=1.0,
            power_quality_phase_allocation_method=(
                PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
            ),
            planning_margin_percent=10.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(20, 0),
            arrival_window_start=time(8, 0),
            arrival_window_end=time(20, 0),
            arrival_mode=ArrivalMode.RANDOM,
            arrival_profile_shape=ArrivalProfileShape.MID_PEAK,
            departure_mode=DepartureMode.SESSION_DWELL,
            session_dwell_minutes=15,
            departure_time_spread_minutes=30,
            charger_service_max_waiting_time_minutes=15,
        ),
    ),
    ScenarioPreset(
        preset_id=WORKPLACE_CHARGING_PRESET_ID,
        label="Workplace Charging",
        purpose=(
            "Daytime workplace charging scenario for employee vehicles parked "
            "during working hours."
        ),
        key_assumptions=(
            "Passenger vehicles arrive around the start of the workday.",
            "Charging demand is lower per vehicle than heavy-duty charging.",
            "Charging is spread across a daytime availability window.",
        ),
        parameter_summaries=(
            _summary("vehicles"),
            _summary("daily_energy_per_vehicle"),
            _summary("charger_count", label="Charger count"),
            _summary("charger_power", label="Charger power"),
            _summary("grid_capacity", label="Grid capacity"),
            _summary("arrival_window", label="Illustrative vehicle arrival window"),
        ),
        scenario=Scenario(
            vehicles=120,
            daily_energy_per_vehicle=20.0,
            charger_count=40,
            charger_power=22.0,
            grid_capacity=500.0,
            request_energy_variability_percent=15.0,
            transformer_capacity_kw=630.0,
            transformer_other_load_kw=60.0,
            feeder_count=4,
            feeder_capacity_kw=160.0,
            feeder_base_load_kw=15.0,
            feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CHARGER_COUNT,
            single_phase_charger_share_percent=0.0,
            charger_harmonic_factor=1.0,
            power_quality_phase_allocation_method=(
                PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
            ),
            planning_margin_percent=10.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(17, 0),
            arrival_window_start=time(8, 0),
            arrival_window_end=time(9, 0),
            arrival_mode=ArrivalMode.PROFILE,
            arrival_profile_shape=ArrivalProfileShape.EVEN,
            departure_mode=DepartureMode.WINDOW_END,
            session_dwell_minutes=None,
            departure_time_spread_minutes=120,
            charger_service_max_waiting_time_minutes=60,
        ),
    ),
    ScenarioPreset(
        preset_id=CONSTRAINED_HEAVY_DUTY_PEAK_SHAVING_PRESET_ID,
        label="Constrained Heavy-Duty Peak Shaving",
        purpose=(
            "Heavy-duty depot showcase tuned to create a pronounced evening peak "
            "so Smart Charging can demonstrate peak-load and connection-capacity "
            "reduction."
        ),
        key_assumptions=(
            "A larger heavy-duty fleet returns during a concentrated evening window.",
            "Non-EV depot load leaves less connection headroom than the baseline preset.",
            "Charging still uses an overnight depot window with end-of-window departures.",
        ),
        parameter_summaries=(
            _summary("vehicles"),
            _summary("daily_energy_per_vehicle"),
            _summary("charger_count", label="Charger count"),
            _summary("charger_power", label="Charger power"),
            _summary("grid_capacity", label="Grid capacity"),
            _summary("arrival_window", label="Illustrative vehicle arrival window"),
        ),
        scenario=Scenario(
            vehicles=60,
            daily_energy_per_vehicle=180.0,
            charger_count=12,
            charger_power=150.0,
            grid_capacity=1200.0,
            request_energy_variability_percent=10.0,
            transformer_capacity_kw=1500.0,
            transformer_other_load_kw=120.0,
            feeder_count=2,
            feeder_capacity_kw=850.0,
            feeder_base_load_kw=60.0,
            feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CHARGER_COUNT,
            single_phase_charger_share_percent=0.0,
            charger_harmonic_factor=1.0,
            power_quality_phase_allocation_method=(
                PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
            ),
            planning_margin_percent=10.0,
            charging_window_start=time(17, 0),
            charging_window_end=time(6, 0),
            arrival_window_start=time(17, 0),
            arrival_window_end=time(20, 0),
            arrival_mode=ArrivalMode.PROFILE,
            arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
            departure_mode=DepartureMode.WINDOW_END,
            departure_time_spread_minutes=30,
            charger_service_max_waiting_time_minutes=120,
        ),
    ),
    ScenarioPreset(
        preset_id=CHARGER_LIMITED_DEPOT_PRESET_ID,
        label="Charger-Limited Depot",
        purpose=(
            "Depot showcase with concentrated evening returns and limited charger "
            "availability to surface charger-service pressure alongside the usual "
            "load-management comparison."
        ),
        key_assumptions=(
            "Depot arrivals are concentrated near the start of the overnight window.",
            "Installed charger count is intentionally tighter than the baseline heavy-duty preset.",
            "Grid capacity is available, but charger availability remains the primary stress point.",
        ),
        parameter_summaries=(
            _summary("vehicles"),
            _summary("daily_energy_per_vehicle"),
            _summary("charger_count", label="Charger count"),
            _summary("charger_power", label="Charger power"),
            _summary("grid_capacity", label="Grid capacity"),
            _summary("arrival_window", label="Illustrative vehicle arrival window"),
        ),
        scenario=Scenario(
            vehicles=32,
            daily_energy_per_vehicle=90.0,
            charger_count=8,
            charger_power=150.0,
            grid_capacity=700.0,
            request_energy_variability_percent=10.0,
            transformer_capacity_kw=900.0,
            transformer_other_load_kw=50.0,
            feeder_count=2,
            feeder_capacity_kw=450.0,
            feeder_base_load_kw=25.0,
            feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CHARGER_COUNT,
            single_phase_charger_share_percent=0.0,
            charger_harmonic_factor=1.0,
            power_quality_phase_allocation_method=(
                PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
            ),
            planning_margin_percent=10.0,
            charging_window_start=time(17, 0),
            charging_window_end=time(7, 0),
            arrival_window_start=time(17, 0),
            arrival_window_end=time(20, 0),
            arrival_mode=ArrivalMode.PROFILE,
            arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
            departure_mode=DepartureMode.WINDOW_END,
            departure_time_spread_minutes=30,
            charger_service_max_waiting_time_minutes=120,
        ),
    ),
    ScenarioPreset(
        preset_id=CONCENTRATED_ARRIVAL_WORKPLACE_CHARGING_PRESET_ID,
        label="Concentrated-Arrival Workplace Charging",
        purpose=(
            "Workplace showcase with synchronized morning arrivals to highlight "
            "how Smart Charging shifts daytime load when many drivers plug in at once."
        ),
        key_assumptions=(
            "Most drivers arrive within the first 30 minutes of the workday.",
            "Vehicles remain parked through the working day rather than session-dwell charging.",
            "Charging demand remains realistic for AC workplace charging rather than public fast charging.",
        ),
        parameter_summaries=(
            _summary("vehicles"),
            _summary("daily_energy_per_vehicle"),
            _summary("charger_count", label="Charger count"),
            _summary("charger_power", label="Charger power"),
            _summary("grid_capacity", label="Grid capacity"),
            _summary("arrival_window", label="Illustrative vehicle arrival window"),
        ),
        scenario=Scenario(
            vehicles=120,
            daily_energy_per_vehicle=20.0,
            charger_count=40,
            charger_power=22.0,
            grid_capacity=500.0,
            request_energy_variability_percent=15.0,
            transformer_capacity_kw=630.0,
            transformer_other_load_kw=60.0,
            feeder_count=4,
            feeder_capacity_kw=160.0,
            feeder_base_load_kw=15.0,
            feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CHARGER_COUNT,
            single_phase_charger_share_percent=0.0,
            charger_harmonic_factor=1.0,
            power_quality_phase_allocation_method=(
                PowerQualityPhaseAllocationMethod.BALANCED_ROUND_ROBIN
            ),
            planning_margin_percent=10.0,
            charging_window_start=time(8, 0),
            charging_window_end=time(17, 0),
            arrival_window_start=time(8, 0),
            arrival_window_end=time(8, 30),
            arrival_mode=ArrivalMode.PROFILE,
            arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
            departure_mode=DepartureMode.WINDOW_END,
            session_dwell_minutes=None,
            departure_time_spread_minutes=90,
            charger_service_max_waiting_time_minutes=60,
        ),
    ),
    ScenarioPreset(
        preset_id=PQ_SENSITIVE_AC_CHARGING_PRESET_ID,
        label="PQ-Sensitive AC Charging",
        purpose=(
            "AC charging showcase with non-neutral power-quality assumptions so "
            "Smart Charging can demonstrate lower modeled harmonic and phase-imbalance risk."
        ),
        key_assumptions=(
            "A material share of chargers are modeled as single-phase AC loads.",
            "Phase allocation is intentionally front-loaded to create a realistic imbalance stress case.",
            "Harmonic severity is above the neutral baseline but remains within plausible AC charger behavior.",
        ),
        parameter_summaries=(
            _summary("vehicles"),
            _summary("daily_energy_per_vehicle"),
            _summary("charger_count", label="Charger count"),
            _summary("single_phase_charger_share_percent"),
            _summary("charger_harmonic_factor", label="Harmonic factor"),
            _summary("grid_capacity", label="Grid capacity"),
        ),
        scenario=Scenario(
            vehicles=72,
            daily_energy_per_vehicle=14.0,
            charger_count=30,
            charger_power=11.0,
            grid_capacity=280.0,
            request_energy_variability_percent=10.0,
            transformer_capacity_kw=420.0,
            transformer_other_load_kw=40.0,
            feeder_count=3,
            feeder_capacity_kw=110.0,
            feeder_base_load_kw=10.0,
            feeder_ev_allocation_method=FeederEVAllocationMethod.BY_CHARGER_COUNT,
            single_phase_charger_share_percent=60.0,
            charger_harmonic_factor=1.25,
            power_quality_phase_allocation_method=(
                PowerQualityPhaseAllocationMethod.FRONT_LOADED_PHASE_A
            ),
            planning_margin_percent=10.0,
            charging_window_start=time(17, 0),
            charging_window_end=time(7, 0),
            arrival_window_start=time(17, 0),
            arrival_window_end=time(20, 0),
            arrival_mode=ArrivalMode.PROFILE,
            arrival_profile_shape=ArrivalProfileShape.FRONT_LOADED,
            departure_mode=DepartureMode.WINDOW_END,
            departure_time_spread_minutes=60,
            charger_service_max_waiting_time_minutes=120,
        ),
    ),
)

_SCENARIO_PRESETS_BY_ID = {
    preset.preset_id: preset for preset in _SCENARIO_PRESETS
}


def list_scenario_presets() -> tuple[ScenarioPreset, ...]:
    """Return the built-in scenario presets in stable display order."""

    return _SCENARIO_PRESETS


def get_scenario_preset(preset_id: str) -> ScenarioPreset:
    """Return one registered scenario preset by its stable identifier."""

    try:
        return _SCENARIO_PRESETS_BY_ID[preset_id]
    except KeyError as exc:
        raise KeyError(f"Unknown scenario preset: {preset_id!r}.") from exc


def get_default_scenario_preset() -> ScenarioPreset:
    """Return the default registered scenario preset."""

    return get_scenario_preset(DEFAULT_SCENARIO_PRESET_ID)


default_scenario_preset = get_default_scenario_preset()
