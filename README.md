# SECHA EV Charging Data Demonstrator

Formula-based EV charging decision-support demonstrator for research and planning discussions about EV charging infrastructure, service quality, grid capacity, and simplified power-quality risk.

## Purpose

This repository implements a transparent demonstrator that turns a charging scenario into:

1. A deterministic charging simulation
2. A derived KPI set for planning interpretation
3. An interactive Dash dashboard for scenario review and comparison

The project is intended for explainable research, workshop, and decision-support use. It is not an engineering-grade power-system simulator and it is not a dispatch optimisation tool.

## Research Context

The demonstrator is built to help users explore how charger count, charger power, arrival concentration, charging-allowed windows, grid capacity, and simplified infrastructure assumptions affect:

- Peak charging load
- Required connection capacity
- Queueing and charger-service pressure
- Transformer and feeder loading
- Simplified power-quality risk indicators
- The difference between uncontrolled charging and a deterministic smart-charging heuristic

## Key Capabilities

- Built-in reference scenarios for depot, workplace, public fast charging, constrained peak-shaving, charger-limited, and power-quality-sensitive cases
- Deterministic 15-minute timestep simulation over a 24-hour day
- Two charging strategies: `Uncontrolled` and `Smart Charging`
- KPI views for overview, infrastructure, grid/capacity, power quality, and strategy comparison
- Scenario A/B comparison for planner-facing trade-off review
- Extensive automated test coverage, including reference-scenario checks

## Quick Start

### Requirements

- Python 3.11 or newer
- The repository contents, including the tracked `assets/` directory

### Install

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Run

```bash
python app.py
```

Then open [http://127.0.0.1:8050/](http://127.0.0.1:8050/).

## Runtime Requirements

- No environment variables are required for the current application.
- No external database, API connection, or local secrets file is required.
- No external data files are required beyond the repository contents.
- Dash automatically loads files from `assets/`, so that directory must remain present after cloning.

## Technology Stack

- Python
- Dash
- Plotly

## Documentation Map

- [docs/architecture.md](/C:/Users/valko/SECHA-EV-charging-data-demonstrator/docs/architecture.md)
- [docs/simulation-and-modelling.md](/C:/Users/valko/SECHA-EV-charging-data-demonstrator/docs/simulation-and-modelling.md)
- [docs/formulas.md](/C:/Users/valko/SECHA-EV-charging-data-demonstrator/docs/formulas.md)
- [docs/kpi-reference.md](/C:/Users/valko/SECHA-EV-charging-data-demonstrator/docs/kpi-reference.md)
- [docs/assumptions-and-limitations.md](/C:/Users/valko/SECHA-EV-charging-data-demonstrator/docs/assumptions-and-limitations.md)
- [docs/scenario-catalogue.md](/C:/Users/valko/SECHA-EV-charging-data-demonstrator/docs/scenario-catalogue.md)
- [docs/testing-and-validation.md](/C:/Users/valko/SECHA-EV-charging-data-demonstrator/docs/testing-and-validation.md)

## Main Limitations

- The model is deterministic, even when using the `RANDOM` arrival mode, because the random generator is seeded from scenario inputs for reproducibility.
- Smart Charging is a deterministic heuristic. It is not a mathematical optimisation algorithm and it does not guarantee a globally optimal solution.
- The simulation uses a single-day, 15-minute timestep representation rather than continuous-time vehicle behaviour.
- Grid and power-quality outputs are simplified planning indicators, not compliance calculations or detailed electrical studies.
- The demonstrator does not produce direct charging-cost KPIs or detailed business-case calculations.

## Optional Test Run

`pytest` is not required to run the application itself, but it is used for validation.

```bash
pip install pytest
pytest
```
