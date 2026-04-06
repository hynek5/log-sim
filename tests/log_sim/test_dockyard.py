import pytest
import simpy

from log_sim.center.dock import Dock
from log_sim.center.dockyard import DockYard, ClassicDockYard, FlowThroughDockYard


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_env_and_yard(cls, num_docks=5):
    env = simpy.Environment()
    yard = cls(env, num_docks)
    return env, yard


def run_get(env, store):
    """Run a single store.get() and return the item synchronously."""
    result = []

    def proc():
        item = yield store.get()
        result.append(item)

    env.process(proc())
    env.run()
    return result[0]


def run_put(env, store, item):
    """Run a single store.put() synchronously."""
    def proc():
        yield store.put(item)

    env.process(proc())
    env.run()


def run_release(env, yard, dock):
    """Call yard.release_dock() inside a SimPy process."""
    def proc():
        yield yard.release_dock(dock)

    env.process(proc())
    env.run()


# ---------------------------------------------------------------------------
# DockYard — init
# ---------------------------------------------------------------------------

class TestDockYardInit:
    def test_creates_correct_number_of_docks(self):
        _, yard = make_env_and_yard(DockYard, num_docks=4)
        assert len(yard.docks) == 4

    def test_store_starts_full(self):
        _, yard = make_env_and_yard(DockYard, num_docks=4)
        assert len(yard.store.items) == 4

    def test_docks_start_unoccupied(self):
        _, yard = make_env_and_yard(DockYard, num_docks=4)
        assert all(not d.occupied for d in yard.docks)

    def test_dock_indices_are_sequential(self):
        _, yard = make_env_and_yard(DockYard, num_docks=4)
        assert [d.index for d in yard.docks] == [0, 1, 2, 3]


# ---------------------------------------------------------------------------
# DockYard — get_neighbors
# ---------------------------------------------------------------------------

class TestGetNeighbors:
    def setup_method(self):
        _, self.yard = make_env_and_yard(DockYard, num_docks=5)

    def test_middle_dock_has_two_neighbors(self):
        neighbors = self.yard.get_neighbors(self.yard.docks[2])
        assert len(neighbors) == 2
        assert self.yard.docks[1] in neighbors
        assert self.yard.docks[3] in neighbors

    def test_first_dock_has_one_neighbor(self):
        neighbors = self.yard.get_neighbors(self.yard.docks[0])
        assert neighbors == [self.yard.docks[1]]

    def test_last_dock_has_one_neighbor(self):
        neighbors = self.yard.get_neighbors(self.yard.docks[4])
        assert neighbors == [self.yard.docks[3]]

    def test_single_dock_yard_has_no_neighbors(self):
        _, yard = make_env_and_yard(DockYard, num_docks=1)
        assert yard.get_neighbors(yard.docks[0]) == []


# ---------------------------------------------------------------------------
# DockYard — get_occupied_neighbors / occupied_neighbor_count
# ---------------------------------------------------------------------------

class TestOccupiedNeighbors:
    def setup_method(self):
        _, self.yard = make_env_and_yard(DockYard, num_docks=5)

    def test_no_occupied_neighbors_when_all_free(self):
        assert self.yard.get_occupied_neighbors(self.yard.docks[2]) == []

    def test_detects_one_occupied_neighbor(self):
        self.yard.docks[1].occupied = True
        result = self.yard.get_occupied_neighbors(self.yard.docks[2])
        assert result == [self.yard.docks[1]]

    def test_detects_two_occupied_neighbors(self):
        self.yard.docks[1].occupied = True
        self.yard.docks[3].occupied = True
        result = self.yard.get_occupied_neighbors(self.yard.docks[2])
        assert len(result) == 2

    def test_occupied_neighbor_count_zero(self):
        assert self.yard.occupied_neighbor_count(self.yard.docks[2]) == 0

    def test_occupied_neighbor_count_one(self):
        self.yard.docks[1].occupied = True
        assert self.yard.occupied_neighbor_count(self.yard.docks[2]) == 1

    def test_occupied_neighbor_count_two(self):
        self.yard.docks[1].occupied = True
        self.yard.docks[3].occupied = True
        assert self.yard.occupied_neighbor_count(self.yard.docks[2]) == 2


# ---------------------------------------------------------------------------
# DockYard — is_edge_dock
# ---------------------------------------------------------------------------

class TestIsEdgeDock:
    def setup_method(self):
        _, self.yard = make_env_and_yard(DockYard, num_docks=5)

    def test_first_dock_is_edge(self):
        assert self.yard.is_edge_dock(self.yard.docks[0])

    def test_last_dock_is_edge(self):
        assert self.yard.is_edge_dock(self.yard.docks[4])

    def test_middle_docks_are_not_edge(self):
        for i in [1, 2, 3]:
            assert not self.yard.is_edge_dock(self.yard.docks[i])


# ---------------------------------------------------------------------------
# DockYard — request_dock / release_dock
# ---------------------------------------------------------------------------

class TestRequestReleaseDock:
    def test_request_dock_returns_a_dock(self):
        env, yard = make_env_and_yard(DockYard, num_docks=3)
        dock = run_get(env, yard.store)
        assert isinstance(dock, Dock)

    def test_request_dock_reduces_store_size(self):
        env, yard = make_env_and_yard(DockYard, num_docks=3)
        run_get(env, yard.store)
        assert len(yard.store.items) == 2

    def test_release_dock_marks_unoccupied(self):
        env, yard = make_env_and_yard(DockYard, num_docks=3)
        dock = run_get(env, yard.store)
        dock.occupied = True
        run_release(env, yard, dock)
        assert not dock.occupied

    def test_release_dock_returns_to_store(self):
        env, yard = make_env_and_yard(DockYard, num_docks=3)
        dock = run_get(env, yard.store)
        assert len(yard.store.items) == 2
        run_put(env, yard.store, dock)
        assert len(yard.store.items) == 3

    def test_all_docks_can_be_requested(self):
        env, yard = make_env_and_yard(DockYard, num_docks=3)
        docks = [run_get(env, yard.store) for _ in range(3)]
        assert len(docks) == 3
        assert len(yard.store.items) == 0


# ---------------------------------------------------------------------------
# DockYard — status_summary
# ---------------------------------------------------------------------------

class TestStatusSummary:
    def test_summary_all_free(self):
        _, yard = make_env_and_yard(DockYard, num_docks=4)
        assert yard.status_summary() == "Docks: 0/4 occupied, 4 in store"

    def test_summary_some_occupied(self):
        env, yard = make_env_and_yard(DockYard, num_docks=4)
        dock = run_get(env, yard.store)
        dock.occupied = True
        assert yard.status_summary() == "Docks: 1/4 occupied, 3 in store"


# ---------------------------------------------------------------------------
# DockYard — calc_maneuver_time (base)
# ---------------------------------------------------------------------------

class TestDockYardCalcManeuverTime:
    def test_raises_not_implemented(self):
        _, yard = make_env_and_yard(DockYard, num_docks=3)
        with pytest.raises(NotImplementedError):
            yard.calc_maneuver_time(yard.docks[0])


# ---------------------------------------------------------------------------
# ClassicDockYard — calc_maneuver_time
# ---------------------------------------------------------------------------

class TestClassicDockYard:
    def setup_method(self):
        _, self.yard = make_env_and_yard(ClassicDockYard, num_docks=5)

    def test_edge_dock_no_occupied_neighbors(self):
        dock = self.yard.docks[0]  # edge
        # occ_count=0 but is_edge_dock → ONE_NEIGHBOR_PENALTY
        expected = ClassicDockYard.BASE_TIME + ClassicDockYard.ONE_NEIGHBOR_PENALTY
        assert self.yard.calc_maneuver_time(dock) == expected

    def test_non_edge_one_occupied_neighbor(self):
        dock = self.yard.docks[2]  # middle
        self.yard.docks[1].occupied = True
        expected = ClassicDockYard.BASE_TIME + ClassicDockYard.ONE_NEIGHBOR_PENALTY
        assert self.yard.calc_maneuver_time(dock) == expected

    def test_non_edge_two_occupied_neighbors(self):
        dock = self.yard.docks[2]  # middle
        self.yard.docks[1].occupied = True
        self.yard.docks[3].occupied = True
        expected = ClassicDockYard.BASE_TIME + ClassicDockYard.TWO_NEIGHBOR_PENALTY
        assert self.yard.calc_maneuver_time(dock) == expected

    def test_non_edge_no_occupied_neighbors_raises(self):
        dock = self.yard.docks[2]  # middle, no neighbors occupied
        expected = ClassicDockYard.BASE_TIME
        assert self.yard.calc_maneuver_time((dock)) == expected


# ---------------------------------------------------------------------------
# FlowThroughDockYard — calc_maneuver_time
# ---------------------------------------------------------------------------

class TestFlowThroughDockYard:
    def setup_method(self):
        _, self.yard = make_env_and_yard(FlowThroughDockYard, num_docks=5)

    def test_always_returns_base_time(self):
        for dock in self.yard.docks:
            assert self.yard.calc_maneuver_time(dock) == FlowThroughDockYard.BASE_TIME

    def test_unaffected_by_occupied_neighbors(self):
        self.yard.docks[1].occupied = True
        self.yard.docks[3].occupied = True
        assert self.yard.calc_maneuver_time(self.yard.docks[2]) == FlowThroughDockYard.BASE_TIME