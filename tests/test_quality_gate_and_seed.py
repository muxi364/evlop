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


if __name__ == "__main__":
    unittest.main()
