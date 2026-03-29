import random
import math
from typing import Callable


class PoissonGenerator:
    """
    Truck arrival generator using Poisson process.

    Internally works with callable lambda(t) -> float (trucks/hour).
    Three factory methods for different input types.
    """

    def __init__(self, lambda_func: Callable[[float], float]):
        """
        Primary constructor — accepts a callable.
        Users should prefer the factory methods below.

        Args:
            lambda_func: function (t_seconds) -> arrival rate in trucks/hour
        """
        self._lambda_func = lambda_func

    @classmethod
    def from_constant(cls, rate: float) -> "PoissonGenerator":
        """
        Constant lambda — homogeneous Poisson process.

        Args:
            rate: trucks per hour (e.g. 10)

        Usage:
            gen = PoissonGenerator.from_constant(10)
        """
        return cls(lambda_func=lambda t: rate)

    @classmethod
    def from_blocks(cls, blocks: list[tuple[float, float, float]]) -> "PoissonGenerator":
        """
        Block-wise lambda — non-homogeneous process with time intervals.

        Args:
            blocks: list of (start_hour, end_hour, rate)
                    e.g. [(0, 6, 3), (6, 9, 15), (9, 14, 5), (14, 18, 12), (18, 24, 3)]

        Usage:
            gen = PoissonGenerator.from_blocks([(6, 9, 15), (9, 18, 5)])
        """

        def block_lambda(t_seconds: float) -> float:
            t_hours = (t_seconds / 3600) % 24
            for start, end, rate in blocks:
                if start <= t_hours < end:
                    return rate
            return 0.0

        return cls(lambda_func=block_lambda)

    @classmethod
    def from_function(cls, func: Callable[[float], float]) -> "PoissonGenerator":
        """
        Continuous lambda — arbitrary function of time.

        Args:
            func: (t_seconds) -> arrival rate in trucks/hour

        Usage:
            gen = PoissonGenerator.from_function(lambda t: 10 + 8 * math.sin(t / 3600 * math.pi / 12))
        """
        return cls(lambda_func=func)

    def get_lambda(self, t_seconds: float) -> float:
        """Returns current lambda (trucks/hour) at time t."""
        return self._lambda_func(t_seconds)

    def next_arrival(self, t_seconds: float) -> float:
        """
        Generates inter-arrival interval (in seconds) using inverse transform.


        Args:
            t_seconds: current simulation time in seconds

        Returns:
            interval in seconds until next truck arrival
        """
        current_lambda = self.get_lambda(t_seconds)

        if current_lambda <= 0:
            return float('inf')

        lambda_per_second = current_lambda / 3600
        interval = -math.log(1-random.random()) / lambda_per_second

        return interval


# if __name__ == "__main__":
#     # --- Demo: constant lambda ---
#     gen_const = PoissonGenerator.from_constant(rate=10)
#     print("=== Constant λ = 10 trucks/hour ===")
#     t = 0.0
#     for i in range(10):
#         interval = gen_const.next_arrival(t)
#         t += interval
#         print(f"  Truck {i + 1}: arrival at t = {t:.0f}s ({t / 60:.1f} min)")
#
#     # --- Demo: block profile ---
#     blocks = [
#         (0, 6, 3),
#         (6, 9, 15),
#         (9, 14, 5),
#         (14, 18, 12),
#         (18, 24, 3),
#     ]
#     gen_blocks = PoissonGenerator.from_blocks(blocks)
#     print("\n=== Block profile ===")
#     for hour in [3, 7, 11, 16, 22]:
#         t_sec = hour * 3600
#         lam = gen_blocks.get_lambda(t_sec)
#         interval = gen_blocks.next_arrival(t_sec)
#         print(f"  {hour}:00 -> λ = {lam} trucks/hour, next arrival in {interval:.0f}s ({interval / 60:.1f} min)")