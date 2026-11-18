"""Unit tests and throughput benchmarks for O(1) monotonic deque sliding window."""

from __future__ import annotations

import time
import unittest

from scenario_streaming import SlidingWindowStats


class TestSlidingWindowStats(unittest.TestCase):
    """Verify accuracy, eviction semantics, edge cases, and O(1) throughput."""

    def test_invalid_window_size_raises(self) -> None:
        """Ensure non-positive window sizes are rejected."""
        with self.assertRaises(ValueError):
            SlidingWindowStats(0.0)
        with self.assertRaises(ValueError):
            SlidingWindowStats(-5.0)

    def test_empty_window_safety(self) -> None:
        """Verify safe zeroed stats before any events and after full expiration."""
        window = SlidingWindowStats(window_size_sec=10.0)
        initial_stats = window.get_stats(now=0.0)
        self.assertEqual(
            initial_stats,
            {"count": 0.0, "sum": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0},
        )

        window.add_event(1.0, 42.5)
        window.add_event(2.0, 17.5)
        expired_stats = window.get_stats(now=25.0)
        self.assertEqual(
            expired_stats,
            {"count": 0.0, "sum": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0},
        )

    def test_exact_window_eviction_and_monotonic_extrema(self) -> None:
        """Verify exact boundary eviction and min/max transitions as extrema expire."""
        window = SlidingWindowStats(window_size_sec=5.0)
        window.add_event(1.0, 100.0)  # Early peak
        window.add_event(2.0, -50.0)  # Early trough
        window.add_event(3.0, 20.0)
        window.add_event(4.0, 40.0)
        window.add_event(5.0, 30.0)

        stats_at_5 = window.get_stats(now=5.0)
        self.assertEqual(stats_at_5["count"], 5.0)
        self.assertAlmostEqual(stats_at_5["sum"], 140.0)
        self.assertAlmostEqual(stats_at_5["mean"], 28.0)
        self.assertAlmostEqual(stats_at_5["min"], -50.0)
        self.assertAlmostEqual(stats_at_5["max"], 100.0)

        # At now=6.0, cutoff is 1.0 -> t=1.0 (value 100.0) is evicted
        stats_at_6 = window.get_stats(now=6.0)
        self.assertEqual(stats_at_6["count"], 4.0)
        self.assertAlmostEqual(stats_at_6["sum"], 40.0)
        self.assertAlmostEqual(stats_at_6["mean"], 10.0)
        self.assertAlmostEqual(stats_at_6["min"], -50.0)
        self.assertAlmostEqual(stats_at_6["max"], 40.0)

        # At now=7.0, cutoff is 2.0 -> t=2.0 (value -50.0) is evicted
        stats_at_7 = window.get_stats(now=7.0)
        self.assertEqual(stats_at_7["count"], 3.0)
        self.assertAlmostEqual(stats_at_7["sum"], 90.0)
        self.assertAlmostEqual(stats_at_7["mean"], 30.0)
        self.assertAlmostEqual(stats_at_7["min"], 20.0)
        self.assertAlmostEqual(stats_at_7["max"], 40.0)

    def test_duplicate_extrema_values(self) -> None:
        """Verify duplicate min/max values survive until the latest instance expires."""
        window = SlidingWindowStats(window_size_sec=3.0)
        window.add_event(1.0, 5.0)
        window.add_event(2.0, 5.0)
        window.add_event(3.0, 10.0)

        # At now=4.5, t=1.0 is evicted, but t=2.0 (also 5.0) remains
        stats = window.get_stats(now=4.5)
        self.assertEqual(stats["count"], 2.0)
        self.assertAlmostEqual(stats["min"], 5.0)
        self.assertAlmostEqual(stats["max"], 10.0)

    def test_throughput_benchmark_50k_events(self) -> None:
        """Assert 50,000 events are processed and queried in < 250ms (> 200k events/sec)."""
        window = SlidingWindowStats(window_size_sec=100.0)
        num_events = 50_000

        start_ns = time.perf_counter_ns()
        for i in range(num_events):
            ts = i * 0.01
            val = float((i * 73) % 997) - 500.0
            window.add_event(ts, val)
            if i % 1000 == 999:
                window.get_stats(ts)
        final_stats = window.get_stats((num_events - 1) * 0.01)
        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000.0
        throughput = num_events / (elapsed_ms / 1000.0)

        self.assertEqual(final_stats["count"], 10_000.0)
        self.assertLess(
            elapsed_ms,
            250.0,
            f"Expected < 250ms for 50k events, got {elapsed_ms:.2f}ms ({throughput:,.0f} events/sec)",
        )


if __name__ == "__main__":
    unittest.main()
