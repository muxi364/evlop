import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from evlop.models import EvlopConfig, Gene, Episode, VerifyRecord
from evlop.fitness import compute_fitness, jaccard_similarity, govern_genes
from evlop.store import EvlopStore


class TestEvlopCore(unittest.TestCase):
    def test_fitness_formula_and_unverified_gate(self):
        cfg = EvlopConfig()
        now = datetime(2026, 11, 18, tzinfo=timezone.utc)
        g_verified = Gene(
            id="gene-1", title="Run pytest with PYTHONPATH", category="testing",
            trigger="ModuleNotFoundError in pytest", strategy="Use python -m pytest",
            anti_pattern="Running bare pytest", success_count=2, failure_count=0,
            verified_gate=True, created_at=now.isoformat(), last_used_at=now.isoformat()
        )
        g_unverified = Gene(
            id="gene-2", title="Unverified rule", category="testing",
            trigger="Some error", strategy="Guess fix",
            anti_pattern="None", success_count=5, failure_count=0,
            verified_gate=False, created_at=now.isoformat(), last_used_at=now.isoformat()
        )
        f_ver = compute_fitness(g_verified, cfg, now=now)
        f_unver = compute_fitness(g_unverified, cfg, now=now)
        # S=2, F=0 -> (3/4) * (1 + 0.5*ln(3)) * 1.5 * 1.0 = 0.75 * 1.5493 * 1.5 = 1.743
        self.assertAlmostEqual(f_ver, 0.75 * (1 + 0.5 * 1.0986122886681098) * 1.5, places=3)
        self.assertLess(f_unver, f_ver)
        governed = govern_genes([g_verified, g_unverified], cfg, now=now)
        by_id = {g.id: g for g in governed}
        self.assertEqual(by_id["gene-1"].status, "promoted")
        self.assertNotEqual(by_id["gene-2"].status, "promoted")  # Review Focus #1: unverified never promoted

    def test_future_timestamp_clamped_and_decay_works(self):
        cfg = EvlopConfig(half_life_days=30.0)
        now = datetime(2026, 11, 18, tzinfo=timezone.utc)
        future = (now + timedelta(days=5)).isoformat()
        old = (now - timedelta(days=90)).isoformat()
        g_future = Gene(
            id="g-fut", title="Future rule", category="workflow",
            trigger="clock skew", strategy="clamp delta", anti_pattern="crash",
            success_count=1, failure_count=0, verified_gate=True,
            created_at=future, last_used_at=future
        )
        g_old = Gene(
            id="g-old", title="Stale rule", category="workflow",
            trigger="ancient error", strategy="old fix", anti_pattern="none",
            success_count=1, failure_count=2, verified_gate=False,
            created_at=old, last_used_at=old
        )
        f_fut = compute_fitness(g_future, cfg, now=now)
        self.assertGreater(f_fut, 1.0)  # Review Focus #5: future timestamp clamped cleanly
        governed = govern_genes([g_old], cfg, now=now)
        self.assertEqual(governed[0].status, "archived")

    def test_duplicate_gene_merge(self):
        cfg = EvlopConfig()
        now = datetime(2026, 11, 18, tzinfo=timezone.utc)
        g1 = Gene(
            id="g-1", title="Fix pytest import path error", category="testing",
            trigger="pytest ModuleNotFoundError src import path",
            strategy="Run python -m pytest", anti_pattern="bare pytest",
            success_count=1, failure_count=0, verified_gate=False,
            created_at=now.isoformat(), last_used_at=now.isoformat()
        )
        g2 = Gene(
            id="g-2", title="Fix pytest import path issue", category="testing",
            trigger="pytest ModuleNotFoundError src import path error",
            strategy="Always run python -m pytest", anti_pattern="bare pytest",
            success_count=2, failure_count=0, verified_gate=True,
            created_at=now.isoformat(), last_used_at=now.isoformat()
        )
        governed = govern_genes([g1, g2], cfg, now=now)
        self.assertEqual(len(governed), 1)  # Review Focus #3: near-duplicates merged
        self.assertEqual(governed[0].success_count, 3)
        self.assertTrue(governed[0].verified_gate)
        self.assertEqual(governed[0].status, "promoted")

    def test_store_roundtrip_and_recall(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvlopStore(Path(tmp))
            store.init_store()
            g = Gene(
                id="gene-sqlite-lock", title="SQLite WAL mode for concurrent reads",
                category="architecture", trigger="sqlite3.OperationalError database is locked",
                strategy="Enable PRAGMA journal_mode=WAL;", anti_pattern="Default rollback journal",
                success_count=3, failure_count=0, verified_gate=True, fitness=2.1, status="promoted"
            )
            store.save_genes([g])
            hits = store.recall_genes("sqlite3 database locked")
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0].id, "gene-sqlite-lock")


if __name__ == "__main__":
    unittest.main()
