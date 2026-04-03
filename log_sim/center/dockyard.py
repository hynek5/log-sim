from logging import raiseExceptions

import simpy

from log_sim.center.dock import Dock


class DockYard:
    """
    Base class for dock yard layouts.

    Handles dock storage, assignment, release and neighbor lookup.
    Subclasses implement calc_maneuver_time for their specific layout.
    """

    def __init__(self, env, num_docks):
        self.env = env
        self.num_docks = num_docks
        self.store = simpy.Store(env, capacity=num_docks)
        self.docks = []
        self.trucks_handled = 0

        for i in range(num_docks):
            dock = Dock(i)
            self.docks.append(dock)
            self.store.put(dock)

    def get_neighbors(self, dock):
        """Returns list of neighboring docks (left and right)."""
        neighbors = []
        if dock.index > 0:
            neighbors.append(self.docks[dock.index - 1])
        if dock.index < self.num_docks - 1:
            neighbors.append(self.docks[dock.index + 1])
        return neighbors

    def get_occupied_neighbors(self, dock):
        """Returns list of occupied neighboring docks."""
        return [n for n in self.get_neighbors(dock) if n.occupied]

    def occupied_neighbor_count(self, dock):
        """How many neighbors are currently occupied."""
        return len(self.get_occupied_neighbors(dock))

    def is_edge_dock(self, dock):
        """Edge docks have more space on one side."""
        return dock.index == 0 or dock.index == self.num_docks - 1

    def request_dock(self):
        """
        Request any free dock from the store.
        Returns a SimPy get event — yield this in a process.
        """
        return self.store.get()

    def release_dock(self, dock):
        """
        Return dock to the store after use.
        Returns a SimPy put event — yield this in a process.
        """
        dock.occupied = False
        self.trucks_handled = self.trucks_handled + 1
        return self.store.put(dock)

    def status_summary(self):
        """Quick overview of yard state."""
        occupied = sum(1 for d in self.docks if d.occupied)
        return f"Docks: {occupied}/{self.num_docks} occupied, {len(self.store.items)} in store"

    def calc_maneuver_time(self, dock):
        """Subclasses must implement this."""
        raise NotImplementedError


class ClassicDockYard(DockYard):
    """
    Classic layout — 90 degree reversing to dock.

    Maneuver time depends on:
    - base reversing time (slow, complex)
    - number of occupied neighbors (tighter space = harder reversing)
    - edge position (one side always open = easier approach)
    """

    BASE_TIME = 120  # 5 min base reversing time
    ONE_NEIGHBOR_PENALTY = 45 # +1.5 min per occupied neighbor
    TWO_NEIGHBOR_PENALTY = 90

    def calc_maneuver_time(self, dock):
        time = self.BASE_TIME
        occ_count = self.occupied_neighbor_count(dock)
        if (occ_count == 0):
            return time
        elif occ_count == 1 or self.is_edge_dock(dock):
            time = time + self.ONE_NEIGHBOR_PENALTY
        elif occ_count == 2:
            time = time + self.TWO_NEIGHBOR_PENALTY
        else:
            raise ValueError(f"Dock {self.index} has more than two neighbors")
        return time




class FlowThroughDockYard(DockYard):
    """
    Flow-through layout — truck drives forward into dock lane.

    Maneuver time is short and nearly constant.
    Neighbors have minimal impact because no reversing is needed.
    """

    BASE_TIME = 75  # 1 min simple lane switch
    def calc_maneuver_time(self, dock):
        return self.BASE_TIME

class TestDockYard(DockYard):

    BASE_TIME = 1

    def calc_maneuver_time(self, dock):
        return self.BASE_TIME
