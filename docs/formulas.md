# Formula Reference

This document lists the core formulas and algorithmic KPI rules implemented in the current codebase. It documents actual behavior only.

## Scope

The demonstrator combines explicit formulas with deterministic rule-based procedures. Some outputs are algebraic. Others, especially charger-planning outputs, are produced by repeated simulation runs rather than a single closed-form equation.

## Time Base

- Timestep length: `15 minutes`
- Timestep hours: `0.25 h`
- Timesteps per day: `96`

Energy from any power profile is therefore integrated as:

`energy_kwh = sum(power_kw_by_timestep) * 0.25`

## Core Demand and Capacity Formulas

### Daily Energy Demand

Implemented in [simulation/formulas.py](../simulation/formulas.py):

`daily_energy_demand_kwh = vehicles * daily_energy_per_vehicle_kwh`

### Installed Charger Capacity

`installed_charger_capacity_kw = charger_count * charger_power_kw`

### Available Site Charging Capacity

`available_site_charging_capacity_kw = min(installed_charger_capacity_kw, grid_capacity_kw)`

This is the maximum EV charging power available at the site before the simulation starts distributing power.

## Request-Energy Formulas

The request generator preserves total site energy demand:

`sum(request_energy_kwh) = vehicles * daily_energy_per_vehicle_kwh`

When `request_energy_variability_percent > 0`, the code applies a deterministic spread around the base request size and adjusts the final request to preserve the exact total after rounding.

When departure mode is `SESSION_DWELL`, request energy is weighted by modeled dwell duration before being normalized back to the same total site energy.

## Load and Energy Formulas

### Requested Connection Capacity

In the current implementation, required connection capacity is based on the peak of the requested load profile:

`required_connection_capacity_kw = max(requested_load_profile_kw)`

This is intentionally different from delivered peak load. It represents the connection capacity the modeled charging requests would ask for before the site limit constrains them.

### Delivered Peak Load

`peak_load_kw = max(delivered_load_profile_kw)`

### Delivered Energy

Implemented in [simulation/load_profiles.py](../simulation/load_profiles.py):

`delivered_energy_kwh = sum(delivered_load_profile_kw) * 0.25`

### Unmet Energy

`unmet_energy_kwh = max(0, daily_energy_demand_kwh - delivered_energy_kwh)`

### Annual Energy

`annual_energy_kwh = daily_energy_kwh * 365`

## Capacity-Margin and Exceedance Formulas

### Peak Capacity Margin

`peak_capacity_margin_kw = configured_connection_capacity_kw - required_connection_capacity_kw`

### Peak Capacity Margin Percent

When configured capacity is positive:

`peak_capacity_margin_percent = (peak_capacity_margin_kw / configured_connection_capacity_kw) * 100`

If configured capacity is zero, the percentage metric is treated as undefined.

### Capacity Exceedance by Timestep

For each timestep:

`capacity_exceedance_kw = max(requested_load_kw - configured_connection_capacity_kw, 0)`

### Maximum Capacity Exceedance

`maximum_capacity_exceedance_kw = max(capacity_exceedance_kw_by_timestep)`

### Exceedance Duration

`capacity_exceedance_duration_hours = exceeded_timestep_count * 0.25`

The metrics layer treats exceedance as persistent when the exceedance count reaches the current persistence threshold used in [metrics/constraint_analysis.py](../metrics/constraint_analysis.py).

## Charger Utilization and Queue Formulas

### Average Charger Utilization

When installed charger capacity is positive:

`average_charger_utilization_percent = (average(delivered_window_load_kw) / installed_charger_capacity_kw) * 100`

### Peak Charger Utilization

`peak_charger_utilization_percent = (max(delivered_window_load_kw) / installed_charger_capacity_kw) * 100`

Both utilization metrics are bounded to `0..100`.

### Average Queue Length

`average_queue_length = mean(waiting_vehicle_count_by_timestep_within_window)`

### Maximum Queue Length

`maximum_queue_length = max(waiting_vehicle_count_by_timestep_within_window)`

### Queue Duration

`queue_duration_hours = count(timesteps where waiting_vehicle_count > 0) * 0.25`

### Waiting Times

For each started request:

`waiting_time_hours = ((charging_start_timestep - arrival_timestep) mod 96) * 0.25`

The dashboard metrics expose the average and maximum over started requests only.

## Transformer Formulas

Implemented in [simulation/formulas.py](../simulation/formulas.py):

### Transformer Total Load

For each timestep:

`transformer_total_load_kw = ev_load_kw + transformer_other_load_kw`

### Transformer Loading Percent

When transformer capacity is positive:

`transformer_loading_percent = (transformer_total_load_kw / transformer_capacity_kw) * 100`

### Transformer Overload

`transformer_overload_kw = max(transformer_total_load_kw - transformer_capacity_kw, 0)`

### Transformer Overload Duration

`transformer_overload_duration_hours = count(timesteps where transformer_overload_kw > 0) * 0.25`

## Feeder Formulas

Implemented in [simulation/grid_loading.py](../simulation/grid_loading.py).

### Feeder EV Allocation

At each timestep, site EV load is allocated across feeders using normalized feeder shares. Under the default method, those shares are derived from charger counts; an alternative scenario mode allows configured shares.

`feeder_ev_load_kw[i] = site_ev_load_kw * feeder_allocation_share[i]`

The last feeder receives any residual so the allocated feeder totals exactly match site EV load.

### Feeder Total Load

`feeder_total_load_kw = feeder_ev_load_kw + feeder_base_load_kw`

### Feeder Loading Percent

`feeder_loading_percent = (feeder_total_load_kw / feeder_capacity_kw) * 100`

### Feeder Overload

`feeder_overload_kw = max(feeder_total_load_kw - feeder_capacity_kw, 0)`

## Simplified Power-Quality Formulas

These are demonstrator indicators, not compliance calculations.

### Harmonic Risk Score

Implemented in [simulation/power_quality.py](../simulation/power_quality.py):

`harmonic_risk_score = 100 * load_factor * source_mix_factor * concentration_factor`

The result is rounded and bounded by the implementation logic. The score increases when more charging load is present, when a larger share of chargers is modeled as single-phase, and when the load is more concentrated.

### Current Imbalance Percent

The current imbalance indicator is derived from the spread between modeled phase loads and is bounded to `0..200`. It is a simplified percentage-style imbalance signal rather than a standards-based electrical calculation.

### Overall PQ Risk Score

Implemented in [metrics/power_quality.py](../metrics/power_quality.py):

`overall_pq_risk_score = 0.6 * harmonic_risk_score + 0.4 * normalized_current_imbalance`

where:

`normalized_current_imbalance = min(max(current_imbalance_percent, 0), 100)`

The blended score is then bounded to `0..100`.

## Recommended Connection Capacity Rule

Recommended capacity is not a simple copy of peak requested load. The implementation applies decision logic from [metrics/constraint_analysis.py](../metrics/constraint_analysis.py):

- If required capacity is effectively zero, recommend `0`
- If the current configured capacity is judged adequate, recommend the configured capacity
- Otherwise recommend the greater of:
  - the current configured capacity
  - `required_connection_capacity_kw * (1 + planning_margin_percent / 100)`

In compact form:

`recommended_connection_capacity_kw = max(configured_capacity_kw, required_capacity_kw * (1 + planning_margin))`

This only applies when adequacy checks fail.

## Charger-Planning Outputs

The following metrics are produced by deterministic planner reruns, not by one direct formula:

- `required_charger_count`
- `additional_chargers_required`
- `charger_count_sufficient_indicator`

The planner searches for the minimum charger count that satisfies the current service rule:

- no vehicles fail to start charging
- no vehicles finish with unmet energy
- maximum waiting time stays within the scenario waiting-tolerance threshold

If the constraint is not charger-count-resolvable, the planner reports that instead of forcing a charger recommendation.

## Constraint Diagnosis

The primary constraint reason is also algorithmic rather than algebraic. The metrics layer runs counterfactual checks with relaxed charger count, charger power, and grid capacity assumptions to classify the dominant modeled bottleneck as one of:

- `charger_availability`
- `charger_power`
- `grid_connection_capacity`
- `charging_window`
- `mixed`
- `none`

In the user interface, `charging_window` is presented as the charging-allowed window, while `arrival_window` is presented as the vehicle-arrival window.

## Not Included

The current implementation does not include:

- AC power flow equations
- voltage-drop calculations
- battery state-of-health models
- tariff optimisation formulas
- probabilistic Monte Carlo formulas
- route or duty-cycle optimization formulas

Those are outside the scope of the implemented demonstrator.
