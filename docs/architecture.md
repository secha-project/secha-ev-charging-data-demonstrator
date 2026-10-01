# Architecture

## System Overview

The demonstrator is organized as a one-way pipeline:

`Scenario -> Simulation -> Metrics -> Dashboard`

Each layer has a distinct responsibility:

- `scenarios/`: validates scenario inputs, defines enums and defaults, and provides built-in presets
- `simulation/`: runs the deterministic timestep model and produces raw operational traces
- `metrics/`: derives planner-facing KPIs and comparison summaries from simulation outputs
- `dashboard/`: renders the user interface from prepared metrics and raw traces without recalculating KPIs
- `assets/`: supplies tracked Dash CSS and front-end assets
- `tests/`: verifies scenario validation, simulation behavior, metric derivation, and dashboard rendering

This separation is intentional. The dashboard is a presentation layer, not a calculation layer.

## High-Level Flow

1. A `Scenario` object is created from a built-in preset or user-edited values.
2. The simulation layer converts that scenario into a 96-step daily model using fixed 15-minute timesteps.
3. The simulation engine produces raw outputs such as arrivals, charging requests, requested and delivered load, queue counts, charger occupancy, transformer loading, feeder loading, and simplified power-quality traces.
4. The metrics layer converts those raw traces into KPIs, status indicators, and comparison summaries.
5. The Dash application renders the results in tabs for overview, infrastructure, smart charging, grid/capacity, power quality, and scenario comparison.

## Main Modules

### Scenario Layer

The scenario layer is the input contract for the entire demonstrator. It owns:

- Site demand assumptions such as `vehicles` and `daily_energy_per_vehicle`
- Charging infrastructure assumptions such as `charger_count` and `charger_power`
- Grid assumptions such as `grid_capacity`, transformer capacity, and feeder capacity
- Arrival and departure modeling controls
- Charging-strategy selection
- Planning settings such as waiting-tolerance and planning-margin values

The built-in catalogue lives in [scenarios/presets.py](../scenarios/presets.py).

### Simulation Layer

The simulation layer owns all modeled operational behavior:

- Time discretization
- Arrival generation
- Request generation
- Departure deadlines
- FIFO queueing
- Charger assignment
- Uncontrolled and smart-charging power allocation
- Transformer loading
- Feeder loading
- Simplified phase and harmonic risk signals

It returns raw simulation outputs in typed dataclasses defined in [simulation/result.py](../simulation/result.py).

### Metrics Layer

The metrics layer translates raw traces into decision-support outputs. It owns:

- Energy and utilization KPIs
- Connection-capacity KPIs
- Charger-service KPIs
- Transformer and feeder KPIs
- Simplified power-quality KPIs
- Constraint diagnosis
- Charger-count planning search
- Strategy comparison summaries
- Scenario A/B comparison summaries

This layer is the only place where dashboard KPIs should be derived.

### Dashboard Layer

The dashboard layer owns:

- Layout structure
- User controls
- Prepared card rendering
- Charts and tab organization
- Comparison presentation
- Empty states and explanatory text

The application entry point in [app.py](../app.py) wires the layout and callbacks together. The dashboard currently exposes these top-level tabs:

- `Overview`
- `Infrastructure`
- `Smart Charging`
- `Grid & Capacity`
- `Power Quality`
- `Scenario Comparison`

## Data Flow Responsibilities

### Scenario -> Simulation

The simulation receives validated scenario inputs and does not depend on dashboard-specific formatting. This keeps the model reusable for tests and future non-Dash interfaces.

### Simulation -> Metrics

The metrics layer consumes simulation traces and calculates planner-facing outputs such as peak load, unmet energy, queue durations, required connection capacity, transformer overload duration, and overall PQ risk.

### Metrics -> Dashboard

The dashboard renders cards, summaries, and figures from metrics outputs and raw series. It may format values for display, but it should not introduce new KPI logic.

## Comparison Modes

The codebase currently supports two comparison patterns:

- Strategy comparison: `Uncontrolled` versus `Smart Charging` for one scenario
- Scenario comparison: Scenario A versus Scenario B using the prepared comparison display model

These comparison surfaces still follow the same layered flow. The dashboard renders prepared comparison outputs; it does not compute them.

## Extension Points

The demonstrator is designed to be extendable without breaking the layer boundaries:

- New scenario sources can feed the existing `Scenario` contract.
- Additional simulation assumptions can be added inside `simulation/` while preserving raw-output contracts.
- New KPIs or planning summaries can be added in `metrics/` without embedding logic in the dashboard.
- Alternative front ends can reuse the scenario, simulation, and metrics layers.

The current codebase does not yet implement external data ingestion, persistent storage, or real-time integrations, but the layer split is intended to make those additions possible later.

## What Is Deliberately Not Mixed

- Dashboard code does not calculate KPIs.
- Metrics code does not own low-level charging formulas.
- Simulation code does not depend on dashboard layout concerns.
- Scenario validation is centralized instead of being spread across callbacks.

That separation is one of the main reasons the demonstrator remains testable and explainable.
