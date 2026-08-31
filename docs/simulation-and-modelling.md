# Simulation and Modelling

## Scope

The demonstrator models a single site over one representative day using deterministic scenario inputs. It is designed to explain charging-system behavior clearly, not to replicate every detail of real-world fleet operations or electrical networks.

## Time Representation

- Horizon: `24 hours`
- Resolution: `15 minutes`
- Total timesteps: `96`

Charging-allowed windows and vehicle-arrival windows can cross midnight. If a window end time is earlier than or equal to the start time, the implementation treats the end as falling on the next day.

## Arrival Modelling

Arrival generation is implemented in [simulation/arrivals.py](/C:/Users/valko/SECHA-EV-charging-data-demonstrator/simulation/arrivals.py).

The simulation creates an arrival-count series that always sums exactly to `scenario.vehicles`.

Supported arrival modes:

- `PROFILE`: uses a deterministic shape across the vehicle-arrival window
- `RANDOM`: uses a seeded pseudo-random generator so the same scenario always reproduces the same arrivals

Implemented profile shapes:

- `front_loaded`: all arrivals occur in the first arrival timestep
- `front_weighted`: arrivals are weighted toward the start of the window
- `mid_peak`: arrivals follow a triangular middle-heavy pattern
- `even`: arrivals are spread as evenly as possible across the window

If `arrival_window_start == arrival_window_end`, the current implementation treats that as a point-arrival event rather than a full-day vehicle-arrival window.

## Request Generation

Charging requests are generated in [simulation/requests.py](/C:/Users/valko/SECHA-EV-charging-data-demonstrator/simulation/requests.py).

Each modeled vehicle becomes one charging request with:

- an arrival timestep
- an energy request in kWh
- a departure deadline or dwell-based departure
- empty outcome fields that are later populated by the charging simulation

Important current behaviors:

- Total requested site energy is preserved exactly
- Request-energy variability is deterministic rather than stochastic
- Requests are ordered by arrival timestep and then vehicle index
- The final request is adjusted after rounding so the full-day total remains correct

## Departure Modelling

The code supports two departure modes:

### Window-End Departure

Vehicles are expected to remain available until the charging-window end, optionally with earlier departures introduced through `departure_time_spread_minutes`.

### Session-Dwell Departure

Each request departs after a modeled dwell duration starting from its arrival. The dwell can also be spread by `departure_time_spread_minutes`.

This mode is used to represent shorter-turnover charging behavior such as public fast charging.

## Queue Modelling

The charging simulation uses a deterministic FIFO waiting queue.

At each timestep, the shared lifecycle is:

1. Release completed chargers
2. Add newly arrived requests to the waiting queue
3. Resolve zero-energy requests
4. Assign available chargers in FIFO order
5. Allocate charging power to connected requests based on the selected strategy

There is no probabilistic reneging or abandonment model. A waiting-tolerance parameter exists, but in the current implementation it is used as:

- a planner-facing service-rule threshold
- a queue-pressure input for the smart-charging heuristic

It is not a hard rule that automatically removes a waiting vehicle from the simulation.

## Capacity Constraints

The simulation models several interacting limits:

- charger count
- charger power
- site connection capacity
- charging-window time availability
- transformer capacity and background load
- feeder capacity and background load

The available site charging capacity is the smaller of:

- installed charger capacity
- configured site connection capacity

This limit affects how much charging power can actually be delivered even when more charging is requested.

## Charging Process Lifecycle

Each request can move through these states:

- arrived but waiting
- connected and charging
- completed
- not started before departure
- started but left with unmet energy

The simulation records request-level outcomes as well as aggregate time-series outputs such as:

- requested load
- delivered load
- occupied chargers
- waiting vehicles
- arrivals and completions

## Charging Strategies

### Uncontrolled Charging

`Uncontrolled` charging assigns available chargers in FIFO order and then charges connected vehicles without intentional peak shaping beyond the hard site and charger limits already present in the scenario.

This provides the baseline behavior used for comparison.

### Smart Charging

`Smart Charging` uses a deterministic heuristic implemented in [simulation/assignment.py](/C:/Users/valko/SECHA-EV-charging-data-demonstrator/simulation/assignment.py).

Its current behavior is:

1. Allocate the minimum pace required for the least-flexible connected requests to remain on track for their deadlines.
2. If vehicles are waiting, add queue-pressure logic based on queue length, waiting time, and the head-of-queue deadline signal.
3. Use any remaining headroom to smooth load toward a shared fleet planning floor without exceeding charger or site limits.

Important interpretation note:

`Smart Charging` is a deterministic heuristic, not an optimisation algorithm. It does not solve a global objective function and it does not guarantee the mathematically best achievable schedule.

It can improve peak load, required connection capacity, service outcomes, or simplified PQ indicators in many scenarios, but it does not guarantee improvement on every metric in every case.

## Grid and Power-Quality Modelling

The simulation extends the delivered EV load into simplified grid indicators:

- transformer total load and overload
- feeder load allocation and overload
- phase load allocation
- harmonic-risk score
- current-imbalance indicator

These outputs are intended for planner-facing interpretation. They are deliberately simpler than detailed electrical-network studies.

## Built-In Scenario Types

The current preset catalogue covers several distinct behaviors:

- overnight heavy-duty depot charging
- public fast charging with short dwell
- daytime workplace charging
- constrained heavy-duty peak shaving
- charger-limited depot operations
- concentrated-arrival workplace charging
- power-quality-sensitive AC charging

See [scenario-catalogue.md](/C:/Users/valko/SECHA-EV-charging-data-demonstrator/docs/scenario-catalogue.md) for the current built-in set.
