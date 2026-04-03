import random

import simpy
from matplotlib import pyplot as plt

from config.sim_config import SimConfig
from log_sim.arrivals.poisson_source import PoissonSource
from log_sim.center.dockyard import DockYard, ClassicDockYard, FlowThroughDockYard
from log_sim.truck_spawner import TruckSpawner


def timeout_generator(seconds: int, env: simpy.Environment):
    yield env.timeout(seconds)

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

def run_scenario(dockyard_class, num_docks, arrival_rate, duration, seed):
    random.seed(seed)
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

    return {
        "seed": seed,
        "arrived": truck_spawner.arrived_truck_count,
        "handled": dockyard.trucks_handled,
        #"max_queue": yard.max_queue,  # if you track this
    }

results = []
if __name__ == "__main__":
    classic_results = []
    flow_results = []

    for i in range(1000):
        classic_results.append(
            run_scenario(
                ClassicDockYard,
                60,
                50,
                3600,
                seed=i
            )
        )

        flow_results.append(
            run_scenario(
                FlowThroughDockYard,
                45,
                50,
                3600,
                seed = i
            )
        )
        print(f"Running iteration {i}")



    #handled = [r["handled"] for r in results]
    #print(f"Mean: {sum(handled) / len(handled):.0f}")
    #print(f"Min:  {min(handled)}")
    #print(f"Max:  {max(handled)}")


    classic = [r["handled"] for r in classic_results]
    flow = [r["handled"] for r in flow_results]

    plt.hist(classic, bins=30, alpha=0.5, label="Classic")
    plt.hist(flow, bins=30, alpha=0.5, label="Flow-through")
    plt.xlabel("Trucks handled")
    plt.ylabel("Frequency")
    plt.legend()
    plt.savefig("comparison.png")

#if __name__ == "__main__":

     #env = simpy.Environment()
     #source = PoissonSource.from_constant(rate=300)


     ### test scenario ###
     #truck_spawner = TruckSpawner(env,
     #                             TestSource(),
     #                             TestDockYard(env,2))


     ### classic dock yard ###
     #dockyard = ClassicDockYard(env, 60)
     #truck_spawner = TruckSpawner(env,
     #                             source,
     #                             dockyard)


     ### flow trough yard ###
     #dockyard = FlowThroughDockYard(env, 50)
     #truck_spawner = TruckSpawner(env,
      #                           source,
       #                          dockyard)

     #kicks in spawner and implement truck process
     #env.process(
     #    truck_spawner.spawn(truck_process))
     #env.process(timeout_generator(10, env))
     #env.run(7200)
     #print(env.now)
     #print(f"Total trucks arrived: {truck_spawner.arrived_truck_count}")
     #print(f"Total trucks handled: {dockyard.trucks_handled}")






