import json
import tempfile
import unittest
from pathlib import Path

from evlop.cli import main


class TestRsiAndParetoOptimality(unittest.TestCase):
    def test_multi_objective_pareto_frontier_hypervolume_and_knee_point(self):
        from evlop.rsi_pareto import (
            ParetoCandidate,
            compute_pareto_frontier,
            compute_hypervolume_3d,
            select_by_operating_mode,
        )

        candidates = [
            # Dominated candidate (worse quality, slower, higher cost than c_balanced)
            ParetoCandidate(id="c_dominated", title="Naive Loop", quality=70.0, latency_ms=400.0, cost_tokens=600),
            # Pareto Front Member 1: Heavy (Max quality, higher latency/cost)
            ParetoCandidate(id="c_heavy", title="Deep Verification Scaffold", quality=100.0, latency_ms=250.0, cost_tokens=500),
            # Pareto Front Member 2: Balanced Knee-Point (High quality, low latency, moderate cost)
            ParetoCandidate(id="c_balanced", title="Indexed Hybrid Scaffold", quality=98.0, latency_ms=25.0, cost_tokens=180),
            # Pareto Front Member 3: Lite (Fastest & cheapest, acceptable quality)
            ParetoCandidate(id="c_lite", title="Zero-Alloc Fast Path", quality=90.0, latency_ms=4.0, cost_tokens=80),
        ]

        front = compute_pareto_frontier(candidates)
        front_ids = {c.id for c in front}
        self.assertEqual(front_ids, {"c_heavy", "c_balanced", "c_lite"})
        self.assertNotIn("c_dominated", front_ids)

        hv_initial = compute_hypervolume_3d(front)
        self.assertGreater(hv_initial, 0.0)

        # HarnessPro Mode Selection (arXiv:2610.26770)
        self.assertEqual(select_by_operating_mode(front, mode="heavy").id, "c_heavy")
        self.assertEqual(select_by_operating_mode(front, mode="lite").id, "c_lite")
        self.assertEqual(select_by_operating_mode(front, mode="balanced").id, "c_balanced")

        # Add a GEPA Pareto-superior offspring that dominates c_heavy and c_balanced -> Hypervolume MUST strictly increase
        offspring = ParetoCandidate(
            id="c_utopia_child", title="GEPA Crossover Offspring", quality=100.0, latency_ms=10.0, cost_tokens=120
        )
        new_front = compute_pareto_frontier(candidates + [offspring])
        hv_after = compute_hypervolume_3d(new_front)
        self.assertGreater(hv_after, hv_initial)

    def test_gepa_pareto_crossover_and_cli_rsi_evolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["init", "--bootstrap"], root_dir=root)

            # Run 3-generation RSI Scaffold Evolution via CLI `evlop rsi --generations 3`
            rc = main(
                ["rsi", "--generations", "3", "--mode", "balanced", "--out", "RSI_REPORT.json"],
                root_dir=root,
            )
            self.assertEqual(rc, 0)

            report_file = root / "RSI_REPORT.json"
            self.assertTrue(report_file.exists())
            report = json.loads(report_file.read_text(encoding="utf-8"))

            # Verify monotonic Hypervolume expansion across RSI generations (Gen 0 -> Gen 3)
            hv_history = report["hypervolume_history"]
            self.assertEqual(len(hv_history), 4)  # Gen 0, 1, 2, 3
            self.assertGreater(hv_history[-1], hv_history[0])
            for i in range(len(hv_history) - 1):
                self.assertGreaterEqual(hv_history[i + 1], hv_history[i])

            # Verify effective model+scaffold capability reached 100% quality at the Pareto knee point
            best = report["selected_pareto_optimal"]
            self.assertEqual(best["quality"], 100.0)
            self.assertLess(best["latency_ms"], 50.0)

            # Verify Pareto-optimal genes were promoted into AGENTS.md
            agents_md = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Pareto", agents_md)


if __name__ == "__main__":
    unittest.main()
