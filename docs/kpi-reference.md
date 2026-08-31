# KPI Reference

This document describes the KPIs and summary outputs currently surfaced by the dashboard. Definitions follow the current implementation.

## Overview Tab

### Scenario Outcome

- Definition: planner-facing summary of the modeled infrastructure outcome, primary bottleneck, and next-action hint
- Unit: categorical summary
- Interpretation: answers whether the current setup appears adequate, constrained, or in need of further review
- Caveat: this is a prepared summary derived from multiple underlying metrics rather than a single formula

### Peak Load

- Definition: maximum delivered charging load in the simulated day
- Unit: `kW`
- Interpretation: indicates the highest realized charging demand at the site
- Caveat: this is delivered peak load, not requested peak load

### Grid Connection Need

- Definition: recommended connection capacity together with current capacity and required increase
- Unit: `kW`
- Interpretation: summarizes whether the modeled site connection appears adequate and what connection headroom may be required
- Caveat: the recommendation includes adequacy logic and planning margin rules, not just raw peak demand

### Charger Expansion Need

- Definition: planner-facing charger-count recommendation summary
- Unit: charger count
- Interpretation: shows whether charger expansion is the primary issue and, if so, how many additional chargers are indicated by the current service rule
- Caveat: if charger count is not the primary modeled constraint, the card intentionally does not force a charger recommendation

### Smart Charging Impact

- Definition: compact preview of one selected improvement signal between uncontrolled and smart charging
- Unit: varies by displayed metric
- Interpretation: gives a quick before/after strategy comparison from the overview page
- Caveat: the selected preview is a summary surface, not a full optimization proof

## Infrastructure Tab

### Capacity Planning Cards

#### Simulated Peak Load

- Definition: delivered peak charging load for the active scenario
- Unit: `kW`
- Interpretation: highest realized site charging demand

#### Required Connection Capacity

- Definition: peak of the requested load profile
- Unit: `kW`
- Interpretation: connection capacity that would be needed to avoid curtailing requested charging demand
- Caveat: this can be higher than delivered peak load because delivered load is capped by site limits

#### Recommended Connection Capacity

- Definition: adequacy-aware recommended site connection size
- Unit: `kW`
- Interpretation: planner-facing recommended capacity after applying adequacy checks and planning margin logic

#### Peak Capacity Margin

- Definition: configured connection capacity minus required connection capacity
- Unit: `kW` and `%`
- Interpretation: positive values indicate headroom; negative values indicate shortfall

### Charger Availability Cards

#### Peak Charger Utilization

- Definition: maximum delivered charging load divided by installed charger capacity within the charging-allowed window
- Unit: `%`
- Interpretation: how hard the installed charger power is used at the modeled peak

#### Peak Occupied Chargers

- Definition: highest number of simultaneously occupied chargers during the charging-allowed window
- Unit: charger count
- Interpretation: indicates occupancy pressure on the installed charger fleet

#### Maximum Queue Length

- Definition: largest waiting-vehicle count observed during the charging-allowed window
- Unit: vehicle count
- Interpretation: shows the worst instantaneous charger-service queue pressure

#### Vehicles Not Started

- Definition: count of requests that never began charging before departure
- Unit: vehicle count
- Interpretation: direct signal of service failure under the current modeled assumptions

### Infrastructure Status Summary

The Infrastructure tab also shows a prepared narrative summary with these fields:

- `Decision Summary`
- `Constraint Diagnosis`
- `Planning Impact`
- `Recommended Planning Focus`

These are not standalone formulas. They are planner-facing interpretations derived from the metric set.

## Smart Charging Tab

### Peak Load

- Definition: change in peak delivered load between uncontrolled and smart charging
- Unit: `kW`
- Interpretation: indicates whether the heuristic reduces or increases the highest realized load

### Required Connection Capacity

- Definition: change in required connection capacity between uncontrolled and smart charging
- Unit: `kW`
- Interpretation: indicates whether the heuristic reduces modeled connection need

### Peak Transformer Loading

- Definition: change in peak transformer loading between uncontrolled and smart charging
- Unit: `%`
- Interpretation: indicates whether the heuristic relieves or worsens transformer stress

### Service Impact

- Definition: prepared summary of charger-service effects such as waiting pressure or completion behavior
- Unit: categorical summary
- Interpretation: indicates whether smart charging improves, preserves, or worsens service outcomes
- Caveat: the summary is intentionally planner-facing rather than a raw single-number KPI

### Power Quality Impact

- Definition: prepared summary of the strategy effect on modeled PQ signals
- Unit: categorical summary
- Interpretation: indicates whether the heuristic appears to improve, preserve, or worsen simplified PQ risk

### Grid / Infrastructure Status

- Definition: prepared summary of whether strategy change resolves, leaves unchanged, or worsens the infrastructure situation
- Unit: categorical summary
- Interpretation: combines grid and infrastructure implications into one executive signal

Important note:

The Smart Charging tab documents a deterministic heuristic comparison. It does not imply that the smart strategy has found an optimal charging schedule.

## Grid & Capacity Tab

### Peak Transformer Loading

- Definition: highest transformer loading percentage across the simulated day
- Unit: `%`
- Interpretation: how close the transformer comes to its rating

### Transformer Overload Duration

- Definition: total modeled time above transformer rating
- Unit: hours
- Interpretation: duration of transformer overload exposure

### Maximum Transformer Overload

- Definition: largest amount by which transformer load exceeds transformer capacity
- Unit: `kW`
- Interpretation: severity of the worst overload event

### Maximum Feeder Loading

- Definition: highest peak loading percentage among feeders
- Unit: `%`
- Interpretation: identifies the worst feeder thermal stress level

### Overloaded Feeders

- Definition: number of feeders with any timestep above rated capacity
- Unit: feeder count
- Interpretation: breadth of feeder overload exposure

## Power Quality Tab

### Overall PQ Risk

- Definition: highest blended power-quality risk score derived from harmonic risk and normalized current imbalance
- Unit: bounded score `0..100`
- Interpretation: compact summary of overall modeled PQ concern
- Caveat: this is a simplified planning indicator, not a compliance metric

### PQ Warnings

- Definition: count of active warning categories among harmonic risk, current imbalance, and overall PQ risk
- Unit: warning count
- Interpretation: broader warning activity across simplified PQ signals

### Peak Harmonic Risk

- Definition: highest modeled harmonic-risk score
- Unit: bounded score `0..100`
- Interpretation: worst modeled harmonic-risk condition

### Harmonic Risk Duration

- Definition: total duration at or above the current moderate harmonic-risk threshold
- Unit: hours
- Interpretation: persistence of modeled harmonic concern

### Peak Current Imbalance

- Definition: highest modeled current-imbalance indicator
- Unit: `%`
- Interpretation: worst phase-imbalance stress condition in the simplified model

### Current Imbalance Duration

- Definition: total duration at or above the current moderate imbalance threshold
- Unit: hours
- Interpretation: persistence of modeled imbalance concern

## Scenario Comparison Tab

### Executive Comparison Cards

The Scenario Comparison page currently exposes these executive comparison KPIs:

#### Peak Load

- Definition: scenario A versus scenario B delivered peak load
- Unit: `kW`
- Interpretation: compares site peak demand pressure

#### Capacity Utilization

- Definition: scenario A versus scenario B peak delivered load as a share of available charging capacity
- Unit: `%`
- Interpretation: compares how intensely the available charging capacity is used

#### Unmet Energy

- Definition: scenario A versus scenario B undelivered charging energy
- Unit: `kWh`
- Interpretation: compares service sufficiency

#### Maximum Queue Length

- Definition: scenario A versus scenario B largest waiting queue
- Unit: vehicle count
- Interpretation: compares worst-case queue pressure

#### Peak Transformer Loading

- Definition: scenario A versus scenario B peak transformer loading
- Unit: `%`
- Interpretation: compares transformer stress

#### Overall PQ Risk

- Definition: scenario A versus scenario B overall simplified PQ risk
- Unit: bounded score `0..100`
- Interpretation: compares aggregate PQ concern

### Section-Level Comparison Families

Beyond the executive cards, the comparison page groups prepared metrics into current decision themes covering:

- infrastructure and charger pressure
- queueing and service effects
- grid and connection-capacity effects
- power-quality effects

Those sections are driven by prepared comparison display data rather than by a fixed hand-written text layer.

## Interpretation Guidance

- Lower is generally better for unmet energy, queueing, overload, and risk metrics.
- Higher is not always better or worse; for example, higher delivered energy can be desirable while higher capacity utilization may indicate tighter operating headroom.
- Narrative cards such as `Scenario Outcome`, `Service Impact`, and `Grid / Infrastructure Status` should be read alongside the underlying numeric KPIs.

For implementation formulas behind these KPIs, see [formulas.md](/C:/Users/valko/SECHA-EV-charging-data-demonstrator/docs/formulas.md).
