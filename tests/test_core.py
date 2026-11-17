import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from evlop.models import EvlopConfig, Gene
from evlop.fitness import compute_fitness, govern_genes
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
        self.assertAlmostEqual(f_ver, 0.75 * (1 + 0.5 * 1.0986122886681098) * 1.5, places=3)
        self.assertLess(f_unver, f_ver)
        governed = govern_genes([g_verified, g_unverified], cfg, now=now)
        by_id = {g.id: g for g in governed}
        self.assertEqual(by_id["gene-1"].status, "promoted")
        self.assertNotEqual(by_id["gene-2"].status, "promoted")

    def test_future_and_malformed_timestamps_clamped_and_decay_works(self):
        cfg = EvlopConfig(half_life_days=30.0)
        now = datetime(2026, 11, 18, tzinfo=timezone.utc)
        future = (now + timedelta(days=5)).isoformat()
        old = (now - timedelta(days=90)).isoformat()
        g_now = Gene(
            id="g-now", title="Now rule", category="workflow",
            trigger="now", strategy="clamp delta", anti_pattern="crash",
            success_count=1, failure_count=0, verified_gate=True,
            created_at=now.isoformat(), last_used_at=now.isoformat()
        )
        g_future = Gene(
            id="g-fut", title="Future rule", category="workflow",
            trigger="clock skew", strategy="clamp delta", anti_pattern="crash",
            success_count=1, failure_count=0, verified_gate=True,
            created_at=future, last_used_at=future
        )
        g_malformed = Gene(
            id="g-mal", title="Malformed timestamp rule", category="workflow",
            trigger="bad date", strategy="clamp delta", anti_pattern="crash",
            success_count=1, failure_count=0, verified_gate=True,
            created_at="not-a-valid-date", last_used_at="not-a-valid-date"
        )
        g_old = Gene(
            id="g-old", title="Stale rule", category="workflow",
            trigger="ancient error", strategy="old fix", anti_pattern="none",
            success_count=1, failure_count=2, verified_gate=False,
            created_at=old, last_used_at=old
        )
        f_now = compute_fitness(g_now, cfg, now=now)
        f_fut = compute_fitness(g_future, cfg, now=now)
        f_mal = compute_fitness(g_malformed, cfg, now=now)
        self.assertEqual(f_fut, f_now)  # Exact decay == 1.0 clamp check
        self.assertEqual(f_mal, f_now)  # Malformed timestamp safely defaults to delta_t == 0
        governed = govern_genes([g_old], cfg, now=now)
        self.assertEqual(governed[0].status, "archived")

    def test_duplicate_gene_merge_english_and_cjk(self):
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
        self.assertEqual(len(governed), 1)
        self.assertEqual(governed[0].success_count, 3)
        self.assertTrue(governed[0].verified_gate)
        self.assertEqual(governed[0].status, "promoted")

        # Important #2: CJK near-duplicate merge
        cjk1 = Gene(
            id="cjk-1", title="显式指定UTF8编码避免报错", category="debugging",
            trigger="Windows文件读取出现编码错误", strategy="使用encoding='utf-8'", anti_pattern="默认编码",
            success_count=1, failure_count=0, verified_gate=True,
            created_at=now.isoformat(), last_used_at=now.isoformat()
        )
        cjk2 = Gene(
            id="cjk-2", title="显式指定UTF8编码避免异常", category="debugging",
            trigger="Windows文件读取出现编码报错", strategy="始终使用encoding='utf-8'", anti_pattern="默认编码",
            success_count=1, failure_count=0, verified_gate=True,
            created_at=now.isoformat(), last_used_at=now.isoformat()
        )
        gov_cjk = govern_genes([cjk1, cjk2], cfg, now=now)
        self.assertEqual(len(gov_cjk), 1)
        self.assertEqual(gov_cjk[0].success_count, 2)

    def test_store_roundtrip_and_cjk_recall(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvlopStore(Path(tmp))
            store.init_store()
            g_en = Gene(
                id="gene-sqlite-lock", title="SQLite WAL mode for concurrent reads",
                category="architecture", trigger="sqlite3.OperationalError database is locked",
                strategy="Enable PRAGMA journal_mode=WAL;", anti_pattern="Default rollback journal",
                success_count=3, failure_count=0, verified_gate=True, fitness=2.1, status="promoted"
            )
            g_zh = Gene(
                id="gene-win-utf8", title="Windows文件读取必须显式指定UTF8编码",
                category="debugging", trigger="Windows环境读取文件乱码",
                strategy="使用encoding='utf-8'", anti_pattern="省略encoding参数",
                success_count=2, failure_count=0, verified_gate=True, fitness=1.8, status="promoted"
            )
            store.save_genes([g_en, g_zh])
            hits = store.recall_genes("sqlite3 database locked")
            self.assertEqual(hits[0].id, "gene-sqlite-lock")

            zh_hits = store.recall_genes("Windows 编码")
            self.assertTrue(any(h.id == "gene-win-utf8" for h in zh_hits))


if __name__ == "__main__":
    unittest.main()
