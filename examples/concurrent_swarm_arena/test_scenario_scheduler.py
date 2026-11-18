"""
Unit and benchmark test suite for Scenario 3 (`scenario_scheduler.py`):
O(V+E) Priority DAG Scheduler & Critical-Path Analyzer.
"""

from __future__ import annotations

import time
import unittest
from typing import Any

from scenario_scheduler import DagTaskScheduler, schedule_waves_and_critical_path


def _build_layered_2000_node_dag(
    num_layers: int = 50,
    width: int = 40,
) -> list[dict[str, Any]]:
    """Construct a 2,000-node (50x40) layered diamond mesh DAG with deterministic weights."""
    tasks: list[dict[str, Any]] = []
    total_nodes = num_layers * width
    for idx in range(total_nodes):
        layer = idx // width
        col = idx % width
        tid = f"n_{layer:03d}_{col:03d}"
        is_spine = col == 0
        duration_ms = 25.0 if is_spine else float(5 + (col % 7))
        priority = 100 if is_spine else (col * 3) % 50
        if layer == 0:
            deps: list[str] = []
        else:
            prev_layer = layer - 1
            dep_a = f"n_{prev_layer:03d}_{col:03d}"
            dep_b = f"n_{prev_layer:03d}_{(col - 1) % width:03d}"
            dep_c = f"n_{prev_layer:03d}_{0:03d}"
            deps = [dep_a, dep_b, dep_c]
        tasks.append(
            {
                "id": tid,
                "duration_ms": duration_ms,
                "priority": priority,
                "depends_on": deps,
            }
        )
    return tasks


class TestScenarioScheduler(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = DagTaskScheduler()

    def test_empty_dag(self) -> None:
        res = self.scheduler.schedule_waves_and_critical_path([])
        self.assertEqual(res["waves"], [])
        self.assertEqual(res["wave_count"], 0)
        self.assertEqual(res["critical_path_ids"], [])
        self.assertEqual(res["critical_path_ms"], 0.0)

    def test_diamond_dag_waves_and_critical_path(self) -> None:
        tasks = [
            {"id": "ingest", "duration_ms": 10.0, "priority": 5, "depends_on": []},
            {"id": "fast_branch", "duration_ms": 15.0, "priority": 20, "depends_on": ["ingest"]},
            {"id": "heavy_branch", "duration_ms": 45.0, "priority": 10, "depends_on": ["ingest"]},
            {"id": "mid_branch", "duration_ms": 30.0, "priority": 20, "depends_on": ["ingest"]},
            {
                "id": "join_sink",
                "duration_ms": 12.0,
                "priority": 1,
                "depends_on": ["fast_branch", "heavy_branch", "mid_branch"],
            },
        ]
        res = self.scheduler.schedule_waves_and_critical_path(tasks)
        self.assertEqual(
            res["waves"],
            [
                ["ingest"],
                ["fast_branch", "mid_branch", "heavy_branch"],
                ["join_sink"],
            ],
        )
        self.assertEqual(res["critical_path_ids"], ["ingest", "heavy_branch", "join_sink"])
        self.assertAlmostEqual(res["critical_path_ms"], 67.0)
        self.assertAlmostEqual(res["earliest_start_ms"]["join_sink"], 55.0)
        self.assertAlmostEqual(res["earliest_finish_ms"]["join_sink"], 67.0)

    def test_priority_ordering_and_lexicographical_tie_break(self) -> None:
        tasks = [
            {"id": "task_c", "duration_ms": 5, "priority": 10, "depends_on": []},
            {"id": "task_a", "duration_ms": 5, "priority": 10, "depends_on": []},
            {"id": "task_b", "duration_ms": 5, "priority": 50, "depends_on": []},
            {"id": "task_d", "duration_ms": 5, "priority": 1, "depends_on": []},
        ]
        res = schedule_waves_and_critical_path(tasks)
        self.assertEqual(res["waves"], [["task_b", "task_a", "task_c", "task_d"]])

    def test_cycle_and_missing_dependency_detection(self) -> None:
        cycle_tasks = [
            {"id": "a", "duration_ms": 10, "priority": 1, "depends_on": ["c"]},
            {"id": "b", "duration_ms": 10, "priority": 1, "depends_on": ["a"]},
            {"id": "c", "duration_ms": 10, "priority": 1, "depends_on": ["b"]},
        ]
        with self.assertRaises(ValueError):
            self.scheduler.schedule_waves_and_critical_path(cycle_tasks)

        self_loop = [
            {"id": "self_node", "duration_ms": 5, "priority": 1, "depends_on": ["self_node"]},
        ]
        with self.assertRaises(ValueError):
            self.scheduler.schedule_waves_and_critical_path(self_loop)

        missing_dep = [
            {"id": "node_1", "duration_ms": 5, "priority": 1, "depends_on": ["non_existent"]},
        ]
        with self.assertRaises(ValueError):
            self.scheduler.schedule_waves_and_critical_path(missing_dep)

        duplicate_id = [
            {"id": "dup", "duration_ms": 5, "priority": 1, "depends_on": []},
            {"id": "dup", "duration_ms": 8, "priority": 2, "depends_on": []},
        ]
        with self.assertRaises(ValueError):
            self.scheduler.schedule_waves_and_critical_path(duplicate_id)

    def test_2000_node_dag_sub_100ms_benchmark(self) -> None:
        tasks = _build_layered_2000_node_dag(num_layers=50, width=40)
        self.assertEqual(len(tasks), 2000)

        t0 = time.perf_counter()
        res = self.scheduler.schedule_waves_and_critical_path(tasks)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        print(f"\n[Benchmark] 2,000-node DAG scheduled in {elapsed_ms:.2f} ms")
        self.assertLess(
            elapsed_ms,
            100.0,
            f"Expected 2,000-node DAG scheduling < 100ms, got {elapsed_ms:.2f}ms",
        )
        self.assertEqual(res["total_tasks"], 2000)
        self.assertEqual(res["wave_count"], 50)
        self.assertEqual(len(res["critical_path_ids"]), 50)
        self.assertAlmostEqual(res["critical_path_ms"], 50 * 25.0)
        self.assertEqual(res["waves"][0][0], "n_000_000")


if __name__ == "__main__":
    unittest.main()
