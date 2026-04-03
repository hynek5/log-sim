from dataclasses import dataclass

@dataclass(frozen=True)
class SimConfig:
    loading_time: int = 600
    simulation_duration: int = 86400
    arrival_rate: float = 10.0