import json
import sys
import tempfile
import unittest
from pathlib import Path

from evlop.cli import main


class TestQualityGateAndSeedGenome(unittest.TestCase):
    def test_bootstrap_preseeds_foundational_sota_genome(self):
        """Verify `evlop init --bootstrap` pre-seeds foundational SOTA engineering genes so external agents start at top-tier quality from Task 1."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rc = main(["init", "--bootstrap"], root_dir=root)
            self.assertEqual(rc, 0)

            genes = json.loads((root / ".evlop" / "genes.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(genes), 4)
            promoted = [g for g in genes if g["status"] == "promoted"]
            self.assertGreaterEqual(len(promoted), 4)

            agents_md = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertNotIn("_No promoted genes yet", agents_md)
            self.assertIn("Algorithmic Complexity", agents_md)

    def test_ast_quality_gate_catches_mediocre_code_and_passes_top_tier_code(self):
        """Verify `evlop audit` deterministically rejects mediocre code (bare except, missing encoding, re.compile in loop) and scores clean code 100/100."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["init", "--bootstrap"], root_dir=root)

            bad_code = root / "mediocre_module.py"
            bad_code.write_text(
                """import re
from pathlib import Path

def process_items(items):
    results = []
    for item in items:
        for other in items:
            pat = re.compile(r"\\d+")
            text = Path("data.txt").read_text()
            if pat.search(text):
                results.append(item)
    try:
        return results[0]
    except:
        pass
""",
                encoding="utf-8",
            )

            rc_bad = main(["audit", str(bad_code), "--min-score", "90"], root_dir=root)
            self.assertNotEqual(rc_bad, 0)

            good_code = root / "top_tier_module.py"
            good_code.write_text(
                '''"""High-efficiency item processor with pre-compiled regex and O(1) lookup."""

from __future__ import annotations

from pathlib import Path
import re

_DIGIT_RE = re.compile(r"\\d+")


def process_items(items: list[str], data_path: Path) -> list[str]:
    """Process items in O(N) time with explicit UTF-8 I/O and pre-compiled regex."""
    text = data_path.read_text(encoding="utf-8")
    if not _DIGIT_RE.search(text):
        return []
    seen: set[str] = set(items)
    return [item for item in items if item in seen]
''',
                encoding="utf-8",
            )

            rc_good = main(["audit", str(good_code), "--min-score", "95"], root_dir=root)
            self.assertEqual(rc_good, 0)

    def test_verify_with_quality_gate_flag(self):
        """Verify `evlop verify --quality-gate` enforces both unit test exit code AND AST quality score >= 90."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["init", "--bootstrap"], root_dir=root)

            src_file = root / "service.py"
            src_file.write_text(
                '''"""Clean service module."""

def compute_sum(values: list[int]) -> int:
    """Return sum of integers."""
    return sum(values)
''',
                encoding="utf-8",
            )
            rc = main(
                [
                    "verify",
                    f"\"{sys.executable}\" -c \"import service; assert service.compute_sum([1,2,3]) == 6\"",
                    "--quality-gate",
                    str(src_file),
                ],
                root_dir=root,
            )
            self.assertEqual(rc, 0)

    def test_zero_friction_red_to_green_auto_evolve(self):
        """Verify `evlop verify --auto-evolve` automatically distills and promotes a gene on a RED -> GREEN transition with 0 manual log/evolve calls."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["init", "--bootstrap"], root_dir=root)

            calc_py = root / "calc.py"
            # Step 1 (RED): Buggy division without zero guard
            calc_py.write_text(
                "def safe_divide(a: float, b: float) -> float:\n    return a / b\n",
                encoding="utf-8",
            )
            rc_red = main(
                [
                    "verify",
                    f"\"{sys.executable}\" -c \"import calc; assert calc.safe_divide(10, 0) == 0.0\"",
                    "--auto-evolve",
                ],
                root_dir=root,
            )
            self.assertNotEqual(rc_red, 0)
            self.assertTrue((root / ".evlop" / "last_failure.json").exists())

            # Step 2 (GREEN): Agent fixes calc.py and re-runs `verify --auto-evolve` (NO manual `log` or `evolve` call!)
            calc_py.write_text(
                "def safe_divide(a: float, b: float) -> float:\n    return 0.0 if b == 0 else a / b\n",
                encoding="utf-8",
            )
            rc_green = main(
                [
                    "verify",
                    f"\"{sys.executable}\" -c \"import calc; assert calc.safe_divide(10, 0) == 0.0\"",
                    "--auto-evolve",
                ],
                root_dir=root,
            )
            self.assertEqual(rc_green, 0)

            # Verify a new ZeroDivisionError gene was automatically logged, promoted, and compiled into AGENTS.md!
            genes = json.loads((root / ".evlop" / "genes.json").read_text(encoding="utf-8"))
            zdiv_genes = [g for g in genes if "ZeroDivisionError" in g["title"] or "ZeroDivisionError" in g["trigger"]]
            self.assertEqual(len(zdiv_genes), 1)
            self.assertEqual(zdiv_genes[0]["status"], "promoted")
            agents_md = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("ZeroDivisionError", agents_md)


if __name__ == "__main__":
    unittest.main()
