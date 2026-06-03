
# log-sim

Discrete-event simulation of a logistics dockyard, built on [SimPy](https://simpy.readthedocs.io/).  
Compares **Classic** (90° reverse-in) vs **Flow-through** (drive-forward) dock layouts under stochastic truck arrivals.

# Flow-through logistic portfolio
For more information about a concept using this simulation for operational validation see [portofolio](https://heyzine.com/flip-book/80f43af6e9.html)


## Key Concepts

| Component | Role |
|-----------|------|
| **ArrivalSource** | Protocol defining `next_arrival(t) -> float` (inter-arrival interval in seconds) |
| **PoissonSource** | Implements ArrivalSource via Poisson process. Factory methods: `from_constant`, `from_blocks`, `from_function` |
| **TruckSpawner** | SimPy process that yields arrival intervals and kicks off `truck_process` for each truck. Supports `pause()`/`resume()` |
| **DockYard** | Base class managing a `simpy.Store` of `Dock` objects. Handles request/release, neighbor queries, occupancy tracking |
| **ClassicDockYard** | 90° reversing layout — maneuver time increases with occupied neighbors (base 120s + penalties) |
| **FlowThroughDockYard** | Drive-through layout — constant 75s maneuver time regardless of neighbors |
| **truck_process** | SimPy generator: request dock → maneuver delay → loading time → release dock |

## Simulation Flow

1. `PoissonSource` generates stochastic inter-arrival times
2. `TruckSpawner` waits each interval, then spawns a `truck_process`
3. Each truck requests a dock from the `DockYard` (queues if none free)
4. Truck maneuvers in (time depends on layout), loads for `SimConfig.loading_time`, then releases the dock

## Running

```bash
pip install -r requirements.txt
python -m log_sim.simulation        # Runs 1000 Monte Carlo iterations, outputs comparison.png
```

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

## Dependencies

- `simpy >= 4.1` — discrete-event simulation engine
- `matplotlib >= 3.10.8` — histogram plotting
- `pytest >= 8.0` — testing (dev)

## Output
See histogram comparison of the classic and flow-trough docks created in project folder.
