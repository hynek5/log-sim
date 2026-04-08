import statistics

import simpy
from matplotlib import pyplot as plt

from config.sim_config import SimConfig
from log_sim.arrivals.poisson_source import PoissonSource
from log_sim.center.dockyard import DockYard, ClassicDockYard, FlowThroughDockYard
from log_sim.truck_spawner import TruckSpawner


def truck_process(env: simpy.Environment, dockyard: DockYard, truck_id):
    dock = yield dockyard.request_dock()

    if dock.index is None:
        raise ValueError("dock not initialized")

    #print(f"[T:{env.now}:{truck_id} has entered the dock {dock.index}])")
    dock.occupied = True
    maneuvering_delay = dockyard.calc_maneuver_time(dock)
    yield env.timeout(maneuvering_delay)

    yield env.timeout(SimConfig.loading_time)

    yield dockyard.release_dock(dock)
    #print(f"[T:{env.now}:{truck_id} has left the dock {dock.index}])")


class Simulation:

    TIME_BUFFER = 1000

    def run_scenario(self, dockyard_class, num_docks, arrival_rate, duration, seed=None):
        #random.seed(seed)
        env = simpy.Environment()
        source = PoissonSource.from_constant(rate=arrival_rate)

        dockyard = dockyard_class(env, num_docks)
        truck_spawner = TruckSpawner(env,
                                     source,
                                     dockyard)
        env.process(
            truck_spawner.spawn(
                truck_process
            )
        )

        env.run(until=duration)
        truck_spawner.pause()
        #drain dockyard
        env.run(until=duration + SimConfig.loading_time + self.TIME_BUFFER)

        return {
            "seed": seed,
            "arrived": truck_spawner.arrived_truck_count,
            "handled": dockyard.trucks_handled,
        }

if __name__ == "__main__":
    classic_results = []
    flow_results = []
    simulation = Simulation()

    for i in range(1000):
        classic_results.append(
            simulation.run_scenario(
                ClassicDockYard,
                60,
                SimConfig.arrival_rate,
                SimConfig.simulation_duration
            )
        )

        flow_results.append(
            simulation.run_scenario(
                FlowThroughDockYard,
                45,
                SimConfig.arrival_rate,
                SimConfig.simulation_duration
            )
        )
        print(f"Running iteration {i}")

    classic = [r["handled"] for r in classic_results]
    flow = [r["handled"] for r in flow_results]

    print(f"Classic - arrived: {statistics.mean(r['arrived'] for r in classic_results):.1f}, handled: {statistics.mean(classic):.1f}")
    print(f"Flow    - arrived: {statistics.mean(r['arrived'] for r in flow_results):.1f}, handled: {statistics.mean(flow):.1f}")

    plt.hist(classic, bins=30, alpha=0.5, label="Classic")
    plt.hist(flow, bins=30, alpha=0.5, label="Flow-through")
    plt.xlabel("Trucks handled")
    plt.ylabel("Frequency")
    plt.legend()
    plt.savefig("comparison.png")