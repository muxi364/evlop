"""Unit and throughput benchmark suite for TokenBucketRateLimiter."""

from __future__ import annotations

import math
import threading
import time
import unittest
from typing import List

from rate_limiter import RateLimitDecision, TokenBucketRateLimiter


class FakeMonotonicClock:
    """Deterministic fake monotonic clock for exact unit testing."""

    def __init__(self, initial: float = 1000.0) -> None:
        """Initialize the fake clock at `initial` seconds."""
        self.current: float = initial

    def __call__(self) -> float:
        """Return the current simulated monotonic timestamp."""
        return self.current

    def advance(self, seconds: float) -> None:
        """Advance the simulated clock by `seconds`."""
        self.current += seconds


class TestTokenBucketRateLimiter(unittest.TestCase):
    """Comprehensive unit and performance tests for TokenBucketRateLimiter."""

    def test_burst_allowance_and_exhaustion(self) -> None:
        """Verify full burst capacity is allowed immediately and excess is rejected."""
        clock = FakeMonotonicClock()
        limiter = TokenBucketRateLimiter(capacity=5.0, refill_rate=2.0, clock_fn=clock)

        for expected_remaining in (4.0, 3.0, 2.0, 1.0, 0.0):
            self.assertTrue(limiter.allow_request(1.0))
            self.assertAlmostEqual(limiter.remaining_tokens, expected_remaining, places=9)
            self.assertEqual(limiter.last_retry_after_sec, 0.0)

        self.assertFalse(limiter.allow_request(1.0))
        self.assertAlmostEqual(limiter.remaining_tokens, 0.0, places=9)
        self.assertAlmostEqual(limiter.last_retry_after_sec, 0.5, places=9)
        self.assertAlmostEqual(limiter.retry_after_sec(1.0), 0.5, places=9)

    def test_exact_lazy_refill_and_cap(self) -> None:
        """Verify lazy O(1) refill calculation and capacity clamping over time."""
        clock = FakeMonotonicClock()
        limiter = TokenBucketRateLimiter(capacity=10.0, refill_rate=4.0, clock_fn=clock)

        self.assertTrue(limiter.allow_request(10.0))
        self.assertAlmostEqual(limiter.remaining_tokens, 0.0, places=9)

        clock.advance(0.75)  # +3.0 tokens
        self.assertAlmostEqual(limiter.remaining_tokens, 3.0, places=9)
        self.assertAlmostEqual(limiter.retry_after_sec(5.0), 0.5, places=9)

        decision: RateLimitDecision = limiter.evaluate(2.5)
        self.assertTrue(decision.allowed)
        self.assertAlmostEqual(decision.remaining_tokens, 0.5, places=9)
        self.assertEqual(decision.retry_after_sec, 0.0)

        # Advance far beyond capacity and verify clamping at capacity=10.0
        clock.advance(100.0)
        self.assertAlmostEqual(limiter.remaining_tokens, 10.0, places=9)

    def test_boundary_and_invalid_inputs(self) -> None:
        """Verify strict boundary guards against zero, negative, NaN, Inf, and bool inputs."""
        clock = FakeMonotonicClock()
        for invalid_val in (0, -1, -0.0001, math.nan, math.inf, -math.inf, True, False):
            with self.assertRaises(ValueError):
                TokenBucketRateLimiter(
                    capacity=invalid_val,  # type: ignore[arg-type]
                    refill_rate=10.0,
                    clock_fn=clock,
                )
            with self.assertRaises(ValueError):
                TokenBucketRateLimiter(
                    capacity=10.0,
                    refill_rate=invalid_val,  # type: ignore[arg-type]
                    clock_fn=clock,
                )

        limiter = TokenBucketRateLimiter(capacity=5.0, refill_rate=1.0, clock_fn=clock)
        for invalid_cost in (0, -1.0, math.nan, math.inf, -math.inf, True, False):
            with self.assertRaises(ValueError):
                limiter.allow_request(invalid_cost)  # type: ignore[arg-type]
            with self.assertRaises(ValueError):
                limiter.evaluate(invalid_cost)  # type: ignore[arg-type]

        # Cost exceeding burst capacity is rejected with infinite retry_after_sec
        self.assertFalse(limiter.allow_request(10.0))
        self.assertTrue(math.isinf(limiter.last_retry_after_sec))
        self.assertTrue(math.isinf(limiter.retry_after_sec(10.0)))

    def test_thread_safety_under_concurrent_burst(self) -> None:
        """Verify exact token accounting under multi-threaded contention."""
        clock = FakeMonotonicClock()
        limiter = TokenBucketRateLimiter(
            capacity=200.0,
            refill_rate=1.0,
            clock_fn=clock,
            thread_safe=True,
        )
        results: List[bool] = [False] * 400

        def worker(start_idx: int, count: int) -> None:
            """Attempt `count` requests and record outcomes."""
            for idx in range(start_idx, start_idx + count):
                results[idx] = limiter.allow_request(1.0)

        threads = [
            threading.Thread(target=worker, args=(i * 50, 50)) for i in range(8)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(sum(1 for allowed in results if allowed), 200)
        self.assertAlmostEqual(limiter.remaining_tokens, 0.0, places=9)

    def test_throughput_benchmark_50k_requests(self) -> None:
        """Verify 50,000 allow_request() calls complete in < 200ms (> 250,000 ops/sec)."""
        limiter = TokenBucketRateLimiter(
            capacity=100_000.0,
            refill_rate=10_000.0,
            clock_fn=time.monotonic,
            thread_safe=True,
        )
        iterations = 50_000
        start_ns = time.perf_counter_ns()
        allowed_count = 0
        for _ in range(iterations):
            if limiter.allow_request():
                allowed_count += 1
        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000.0
        ops_per_sec = iterations / (elapsed_ms / 1000.0)

        print(
            f"\n[BENCHMARK] 50,000 allow_request() calls: "
            f"{elapsed_ms:.2f} ms ({ops_per_sec:,.0f} ops/sec)"
        )
        self.assertEqual(allowed_count, iterations)
        self.assertLess(
            elapsed_ms,
            200.0,
            f"Expected < 200ms for 50,000 requests, took {elapsed_ms:.2f}ms",
        )
        self.assertGreater(
            ops_per_sec,
            250_000.0,
            f"Expected > 250,000 ops/sec, got {ops_per_sec:,.0f} ops/sec",
        )


if __name__ == "__main__":
    unittest.main()
