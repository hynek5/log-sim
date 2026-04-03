from log_sim.arrivals.arrival_source import ArrivalSource


class TestSource(ArrivalSource):

    def next_arrival(self, t_seconds: float) -> float:
        return 1

