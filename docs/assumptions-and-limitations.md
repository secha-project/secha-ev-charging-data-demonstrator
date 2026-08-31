# Assumptions and Limitations

## What the Demonstrator Models

The current implementation models:

- one charging site over one representative day
- deterministic vehicle arrivals within a configured vehicle-arrival window
- deterministic charging requests derived from fleet demand assumptions
- charger-count and charger-power constraints
- site connection-capacity constraints
- transformer and feeder loading with fixed non-EV background load assumptions
- simplified phase allocation and simplified power-quality risk indicators
- planner-facing comparison between uncontrolled charging and a deterministic smart-charging heuristic

## Deliberate Simplifications

- Time is represented in fixed 15-minute steps.
- Each vehicle generates one charging request for the modeled day.
- Request-energy variability is deterministic and reproducible.
- Random arrival mode is seeded from scenario inputs, so repeated runs are identical for the same scenario.
- Feeder allocation is simplified and based on configured shares or charger-count-derived shares.
- Power quality is represented through bounded heuristic indicators rather than electrical standards calculations.

## What the Demonstrator Does Not Model

The current codebase does not model:

- real traffic networks or route choice
- stochastic multi-day uncertainty
- driver behavior adaptation
- charger outages or maintenance failures
- vehicle battery chemistry or degradation
- battery state-of-charge trajectories outside the simplified request-energy abstraction
- direct charging-cost modeling, dynamic electricity prices, demand charges, or tariff optimization
- detailed AC power flow, voltage quality, protection studies, or grid-code compliance
- formal optimization with guaranteed optimality

## Smart Charging Caveat

The `Smart Charging` strategy is a deterministic heuristic. It reacts to flexibility and queue pressure, but it is not:

- a mixed-integer optimization model
- a linear program
- a nonlinear optimizer
- a proof of optimal peak shaving

It can improve some metrics while leaving others unchanged, and in edge cases it may trade one objective against another.

## Appropriate Uses

The demonstrator is appropriate for:

- explaining infrastructure trade-offs
- comparing scenario assumptions
- illustrating how concentrated arrivals affect peaks and queueing
- showing how a heuristic charging strategy changes planner-facing outcomes
- supporting research discussion, stakeholder workshops, and early-stage scoping

## Inappropriate Uses

The demonstrator should not be used as the sole basis for:

- electrical design sign-off
- regulatory compliance statements
- protective-device settings
- harmonic compliance assessment
- investment decisions that require detailed operational or market modeling
- claims of mathematically optimal charging schedules

## Interpretation Guidance

- Treat results as directional and comparative rather than exact forecasts.
- Use the built-in scenarios to understand modeled phenomena, not as universal benchmarks.
- Check which constraint is primary before acting on a single KPI.
- Read grid and power-quality outputs as screening indicators that may justify deeper engineering analysis.

## Reproducibility

One strength of the current implementation is reproducibility:

- same inputs produce the same simulation result
- pseudo-random arrivals remain deterministic for a given scenario
- KPI derivation is formula-based and test-covered

That reproducibility is valuable for research communication, even though the model remains simplified.
