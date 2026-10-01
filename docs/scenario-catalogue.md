# Scenario Catalogue

This document describes the built-in scenario presets currently registered in [scenarios/presets.py](../scenarios/presets.py).

## Heavy-duty

- Preset id: `heavy_duty`
- Purpose: baseline overnight depot-style heavy-duty charging scenario
- Demonstrates: concentrated depot return behavior, high per-vehicle energy demand, and overnight infrastructure sizing pressure
- Typical defaults: `50` vehicles, `150 kWh` per vehicle, `10` chargers at `150 kW`, `1000 kW` site capacity

## Public Fast Charging

- Preset id: `public_fast_charging`
- Purpose: short-stay public charging hub scenario
- Demonstrates: higher turnover, dwell-limited charging, and daytime variability in public fast charging demand
- Typical defaults: `48` charging sessions, `50 kWh` per session, `6` chargers at `300 kW`, `1200 kW` site capacity, `15` minute modeled dwell

## Workplace Charging

- Preset id: `workplace_charging`
- Purpose: daytime workplace charging scenario
- Demonstrates: lower per-vehicle energy demand, daytime charging-allowed windows, and broader charger deployment at lower power
- Typical defaults: `120` vehicles, `20 kWh` per vehicle, `40` chargers at `22 kW`, `500 kW` site capacity

## Constrained Heavy-Duty Peak Shaving

- Preset id: `constrained_heavy_duty_peak_shaving`
- Purpose: heavy-duty showcase tuned to create a pronounced evening peak
- Demonstrates: a case where smart charging can visibly reduce peak load and connection-capacity pressure
- Typical defaults: `60` vehicles, `180 kWh` per vehicle, `12` chargers at `150 kW`, `1200 kW` site capacity

## Charger-Limited Depot

- Preset id: `charger_limited_depot`
- Purpose: depot case with intentionally tight charger availability
- Demonstrates: queue pressure, charger-service constraints, and situations where charger count is a more important issue than raw grid headroom
- Typical defaults: `32` vehicles, `90 kWh` per vehicle, `8` chargers at `150 kW`, `700 kW` site capacity

## Concentrated-Arrival Workplace Charging

- Preset id: `concentrated_arrival_workplace_charging`
- Purpose: workplace case with synchronized morning arrivals
- Demonstrates: how arrival concentration can create daytime peaks even in lower-power workplace charging
- Typical defaults: `120` vehicles, `20 kWh` per vehicle, `40` chargers at `22 kW`, `500 kW` site capacity, `08:00-08:30` vehicle-arrival window

## PQ-Sensitive AC Charging

- Preset id: `pq_sensitive_ac_charging`
- Purpose: AC charging case with non-neutral power-quality assumptions
- Demonstrates: modeled harmonic and phase-imbalance sensitivity, especially under a high single-phase share
- Typical defaults: `72` vehicles, `14 kWh` per vehicle, `30` chargers at `11 kW`, `280 kW` site capacity, `60%` single-phase charger share

## How to Use the Catalogue

- Use `Heavy-duty` as the baseline depot-style reference case.
- Use `Public Fast Charging` when short dwell and turnover matter.
- Use `Workplace Charging` for daytime employee parking behavior.
- Use `Constrained Heavy-Duty Peak Shaving` when demonstrating load shifting and connection relief.
- Use `Charger-Limited Depot` when discussing service bottlenecks and charger-count planning.
- Use `Concentrated-Arrival Workplace Charging` when discussing the effect of synchronized arrival peaks.
- Use `PQ-Sensitive AC Charging` when discussing simplified power-quality indicators.

## Important Note

These presets are illustrative research scenarios, not calibrated field cases. They are designed to surface distinct modeled phenomena clearly in the dashboard and tests.
