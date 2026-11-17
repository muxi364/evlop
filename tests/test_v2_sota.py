import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from evlop.cli import main


class TestEvlopV2Sota(unittest.TestCase):
    def test_alphaevolve_verify_captures_duration_ms(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["init"], root_dir=root)
            rc = main(["verify", "python -c \"print('fast check')\""], root_dir=root)
            self.assertEqual(rc, 0)
            last_v = json.loads((root / ".evlop" / "last_verify.json").read_text(encoding="utf-8"))
            self.assertIn("duration_ms", last_v)
            self.assertGreaterEqual(last_v["duration_ms"], 0.0)

    def test_dgm_lineage_mutation_and_phylogenetic_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["init"], root_dir=root)
            main(["verify", "python -c \"print('ok')\""], root_dir=root)

            # Generation 1 ancestor gene
            main([
                "log",
                "--title", "Optimize Matrix Kernel",
                "--category", "architecture",
                "--task", "Speed up 4x4 matrix multiply",
                "--symptom", "Naive 64-multiplication kernel is slow",
                "--root-cause", "Unoptimized nested loops",
                "--fix", "Use Strassen 49-multiplication decomposition",
                "--agent-id", "alpha-worker-1",
            ], root_dir=root)

            genes_gen1 = json.loads((root / ".evlop" / "genes.json").read_text(encoding="utf-8"))
            ancestor_id = genes_gen1[0]["id"]
            self.assertEqual(genes_gen1[0]["generation"], 1)
            self.assertIn("alpha-worker-1", genes_gen1[0]["contributors"])

            # Generation 2 mutation via `evlop mutate` (DGM style scaffold/strategy mutation)
            rc_mut = main([
                "mutate",
                "--parent-id", ancestor_id,
                "--title", "Optimize Matrix Kernel 48-Mul",
                "--strategy", "Use AlphaEvolve 48-multiplication complex decomposition",
                "--reason", "Discovered lower scalar multiplication count in benchmark",
                "--agent-id", "alpha-worker-2",
            ], root_dir=root)
            self.assertEqual(rc_mut, 0)

            genes_all = {g["id"]: g for g in json.loads((root / ".evlop" / "genes.json").read_text(encoding="utf-8"))}
            child_genes = [g for g in genes_all.values() if g["parent_id"] == ancestor_id]
            self.assertEqual(len(child_genes), 1)
            child = child_genes[0]
            self.assertEqual(child["generation"], 2)
            self.assertIn("alpha-worker-2", child["contributors"])

            # Verify `evlop lineage --mermaid` outputs a valid Mermaid graph connecting parent -> child
            rc_lin = main(["lineage", "--mermaid", "--out", "LINEAGE.md"], root_dir=root)
            self.assertEqual(rc_lin, 0)
            lineage_md = (root / "LINEAGE.md").read_text(encoding="utf-8")
            self.assertIn("flowchart TD", lineage_md)
            self.assertIn(ancestor_id, lineage_md)
            self.assertIn(child["id"], lineage_md)

    def test_voyager_executable_tool_synthesis_on_export_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["init"], root_dir=root)
            main(["verify", "python -c \"print('ok')\""], root_dir=root)
            main([
                "log",
                "--title", "Run Unit Tests Safely",
                "--category", "testing",
                "--task", "Execute unit tests",
                "--symptom", "Tests skipped",
                "--root-cause", "No runner script",
                "--fix", "python -m unittest discover -s tests -v",
                "--strategy", "Run command: `python -c \"print('voyager-tool-ok')\"`",
            ], root_dir=root)
            genes = json.loads((root / ".evlop" / "genes.json").read_text(encoding="utf-8"))
            gid = genes[0]["id"]

            rc_exp = main(
                ["export-skill", "--gene-id", gid, "--out-dir", "skills", "--synthesize-script"],
                root_dir=root,
            )
            self.assertEqual(rc_exp, 0)
            script_path = root / "skills" / f"auto-{gid}" / "scripts" / "run_strategy.py"
            self.assertTrue(script_path.exists())

            # Execute the synthesized Voyager tool script in dry-run / inspect mode
            proc = subprocess.run(
                [sys.executable, str(script_path), "--info"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            self.assertIn(gid, proc.stdout)


if __name__ == "__main__":
    unittest.main()
