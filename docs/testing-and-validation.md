# Testing and Validation

## Validation Philosophy

The demonstrator is validated as a deterministic research tool:

- identical inputs should produce identical outputs
- scenario validation should reject invalid modeling inputs early
- simulation traces should remain internally consistent
- metrics should be derived from simulation outputs, not duplicated in the dashboard
- dashboard rendering should reflect the prepared metrics correctly

The goal is reproducibility and interpretability, not empirical proof that every result matches a real charging site exactly.

## Current Test Coverage

The repository includes an extensive `pytest` suite covering:

- scenario validation rules
- scenario preset registration
- time-window behavior
- arrival generation
- request generation
- charging assignment behavior
- simulation engine outputs
- KPI derivation
- charger-planning search behavior
- scenario and strategy comparison logic
- dashboard layout and rendering contracts


## Reference Scenarios

The suite includes dedicated reference-scenario tests in [tests/test_reference_scenarios.py](../tests/test_reference_scenarios.py).

These tests are especially important because they verify behavioral intent rather than only isolated helper functions. They cover cases such as:

- queue-free feasible charging
- concentrated versus even arrivals
- charger-limited behavior
- public fast charging turnover
- connection-capacity-limited behavior
- smart-charging flexibility effects

## What the Tests Validate Well

- deterministic reproducibility
- layer separation
- KPI consistency
- queueing and service logic
- infrastructure and connection-capacity signals
- simplified transformer, feeder, and power-quality calculations
- dashboard text and visualization contracts

## Known Validation Limits

Even with broad automated coverage, the tests do not turn the demonstrator into a full engineering simulator. In particular, the current validation does not establish:

- real-world calibration against measured charging data
- standards-grade transformer aging analysis
- harmonic compliance accuracy
- detailed network power-flow fidelity
- optimality of the smart-charging strategy

## How to Run the Tests

`pytest` is intentionally kept out of runtime requirements, so install it separately when needed:

```bash
pip install pytest
pytest
```

## Interpreting Passing Tests

A passing suite means the implemented contracts are currently consistent with the codebase and expected demonstrator behavior. It does not mean the model is exhaustive or suitable for design certification.
