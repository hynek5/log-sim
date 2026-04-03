import simpy

from log_sim.arrivals.test_source import TestSource
from log_sim.center.dockyard import TestDockYard
from log_sim.truck_spawner import TruckSpawner
from log_sim.simulation import truck_process


def run_simulation(num_docks, sim_duration):
    """Helper: run a full simulation and return (env, dockyard, spawner)."""
    env = simpy.Environment()
    dockyard = TestDockYard(env, num_docks)
    spawner = TruckSpawner(env, TestSource(), dockyard)
    env.process(spawner.spawn(truck_process))
    env.run(sim_duration)
    return env, dockyard, spawner


class TestSimulationBasic:
    def test_trucks_are_spawned(self):
        """TestSource returns interval=1, so in 10s we should spawn ~10 trucks."""
        _, _, spawner = run_simulation(num_docks=5, sim_duration=11)
        assert spawner.arrived_truck_count == 10

    def test_docks_released_after_use(self):
        """With enough docks and time, all docks should be free at the end."""
        # TestDockYard.BASE_TIME=1, SimConfig.loading_time=1, interval=1
        # truck uses dock for 1 (maneuver) + 1 (loading) = 2s
        # interval = 1s, 3 docks → plenty of capacity
        env, dockyard, spawner = run_simulation(num_docks=3, sim_duration=100)
        spawner.pause()
        env.run(110)
        assert all(not d.occupied for d in dockyard.docks)

    def test_all_docks_return_to_store(self):
        """After simulation, all docks should be back in the store."""
        env, dockyard, spawner = run_simulation(num_docks=3, sim_duration=100)
        spawner.pause()
        env.run(110)
        assert len(dockyard.store.items) == 3

    def test_simulation_advances_time(self):
        """Env.now should reach the sim_duration."""
        env, _, _ = run_simulation(num_docks=3, sim_duration=50)
        assert env.now == 50


class TestSimulationQueueing:
    def test_trucks_queue_when_docks_full(self):
        """With 1 dock, trucks must wait — but simulation still completes."""
        env, dockyard, spawner = run_simulation(num_docks=1, sim_duration=21)
        assert spawner.arrived_truck_count == 20
        # all trucks eventually processed, dock back in store
        spawner.pause()
        env.run(60)
        assert len(dockyard.store.items) == 1

    #def test_many_docks_no_queueing(self):
    #    """With many docks, no truck should ever wait."""
    #    _, dockyard, spawner = run_simulation(num_docks=50, sim_duration=10)
    #    assert spawner.truck_count == 10
    #    assert len(dockyard.store.items) == 50