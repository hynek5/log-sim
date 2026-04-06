import math
import random
import pytest
from log_sim.arrivals.poisson_source import PoissonSource


# ---------------------------------------------------------------------------
# from_constant
# ---------------------------------------------------------------------------

class TestFromConstant:
    def test_get_lambda_returns_rate(self):
        gen = PoissonSource.from_constant(rate=10)
        assert gen.get_lambda(0) == 10
        assert gen.get_lambda(3600) == 10
        assert gen.get_lambda(86400) == 10

    def test_next_arrival_returns_positive_interval(self):
        gen = PoissonSource.from_constant(rate=10)
        interval = gen.next_arrival(0)
        assert interval > 0

    def test_next_arrival_zero_rate_returns_inf(self):
        gen = PoissonSource.from_constant(rate=0)
        assert gen.next_arrival(0) == float("inf")

    def test_next_arrival_negative_rate_returns_inf(self):
        gen = PoissonSource.from_constant(rate=-5)
        assert gen.next_arrival(0) == float("inf")

    def test_mean_interval_matches_rate(self):
        """Mean inter-arrival time should be ≈ 3600 / rate seconds."""
        random.seed(42)
        rate = 10
        gen = PoissonSource.from_constant(rate=rate)
        samples = [gen.next_arrival(0) for _ in range(10_000)]
        expected_mean = 3600 / rate
        actual_mean = sum(samples) / len(samples)
        # within 5 % of the theoretical mean
        assert abs(actual_mean - expected_mean) / expected_mean < 0.05

    def test_simulated_arrivals_accumulate(self):
        """Replicate the demo loop: 10 sequential arrivals on a constant process."""
        random.seed(0)
        gen = PoissonSource.from_constant(rate=10)
        t = 0.0
        arrivals = []
        for _ in range(10):
            interval = gen.next_arrival(t)
            t += interval
            arrivals.append(t)
        assert len(arrivals) == 10
        assert arrivals[-1] > arrivals[0]          # times are strictly increasing
        assert all(a > 0 for a in arrivals)


# ---------------------------------------------------------------------------
# from_blocks
# ---------------------------------------------------------------------------

BLOCKS = [
    (0, 6, 3),
    (6, 9, 15),
    (9, 14, 5),
    (14, 18, 12),
    (18, 24, 3),
]


class TestFromBlocks:
    @pytest.mark.parametrize("hour, expected_rate", [
        (3,  3),   # night: 0–6
        (7,  15),  # morning peak: 6–9
        (11, 5),   # mid-day: 9–14
        (16, 12),  # afternoon peak: 14–18
        (22, 3),   # evening: 18–24
    ])
    def test_get_lambda_at_each_block(self, hour, expected_rate):
        gen = PoissonSource.from_blocks(BLOCKS)
        assert gen.get_lambda(hour * 3600) == expected_rate

    def test_get_lambda_outside_all_blocks_returns_zero(self):
        # blocks that don't cover all 24 h
        sparse_blocks = [(6, 9, 15)]
        gen = PoissonSource.from_blocks(sparse_blocks)
        assert gen.get_lambda(0) == 0.0      # before 6 h
        assert gen.get_lambda(10 * 3600) == 0.0  # after 9 h

    def test_next_arrival_positive_in_active_block(self):
        gen = PoissonSource.from_blocks(BLOCKS)
        interval = gen.next_arrival(7 * 3600)
        assert interval > 0

    def test_next_arrival_inf_outside_blocks(self):
        sparse_blocks = [(6, 9, 15)]
        gen = PoissonSource.from_blocks(sparse_blocks)
        assert gen.next_arrival(0) == float("inf")

    def test_block_lambda_wraps_around_24h(self):
        """t > 24 h should wrap via modulo and still hit the right block."""
        gen = PoissonSource.from_blocks(BLOCKS)
        # 25 h ≡ 1 h → night block, rate 3
        assert gen.get_lambda(25 * 3600) == 3

    def test_simulated_arrivals_at_each_block_hour(self):
        """Replicate the demo loop across representative hours."""
        random.seed(1)
        gen = PoissonSource.from_blocks(BLOCKS)
        for hour in [3, 7, 11, 16, 22]:
            t_sec = hour * 3600
            lam = gen.get_lambda(t_sec)
            interval = gen.next_arrival(t_sec)
            assert lam > 0
            assert interval > 0


# ---------------------------------------------------------------------------
# from_function
# ---------------------------------------------------------------------------

class TestFromFunction:
    def test_get_lambda_matches_func_output(self):
        func = lambda t: 10 + 8 * math.sin(t / 3600 * math.pi / 12)
        gen = PoissonSource.from_function(func)
        for t in [0, 3600, 7200, 43200]:
            assert gen.get_lambda(t) == pytest.approx(func(t))

    def test_next_arrival_positive_when_lambda_positive(self):
        gen = PoissonSource.from_function(lambda t: 5.0)
        assert gen.next_arrival(0) > 0

    def test_next_arrival_inf_when_lambda_zero(self):
        gen = PoissonSource.from_function(lambda t: 0.0)
        assert gen.next_arrival(0) == float("inf")