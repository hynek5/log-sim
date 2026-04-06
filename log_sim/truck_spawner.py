import simpy
from simpy import Timeout
from simpy.events import NORMAL

from log_sim.arrivals.arrival_source import ArrivalSource
from log_sim.center.dockyard import DockYard


class TruckSpawner:
    """
    Spawns trucks into SimPy environment based on an arrival generator.

    The arrival generator can be any object with next_arrival(t_seconds) -> float.
    PoissonGenerator satisfies this, but so would any custom generator.
    """

    def __init__(self, env: simpy.Environment, generator: ArrivalSource, dockyard: DockYard):
        self.env = env
        self.generator = generator
        self.arrived_truck_count = 0
        self.dockyard = dockyard
        self._active = env.event()
        self._active.succeed()

    def spawn(self, truck_process):

        """
        Returns a SimPy generator that spawns trucks over time.

        Args:
            truck_process: a callable(env, name, **kwargs) that returns
                           a SimPy generator (the truck lifecycle)

        Usage:
            def truck(env, name):
                yield env.timeout(100)

            spawner = TruckSpawner(env, poisson_gen)
            env.process(spawner.spawn(truck))
        """
        while True :
            yield self._active
            interval = self.generator.next_arrival(self.env.now)
            yield self.env.timeout(interval)
            self.arrived_truck_count += 1
            name = f"Truck-{self.arrived_truck_count:03d}"
            #print(f"T:{self.env.now} spawning {name}")
            self.env.process(truck_process(self.env, self.dockyard, name))

    def pause(self):
        self._active = self.env.event()  # new unfired event

    def resume(self):
        if not self._active.triggered:
            self._active.succeed()