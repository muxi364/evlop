import json
import tempfile
import unittest
from pathlib import Path

from evlop.cli import main


class TestCliAndCompiler(unittest.TestCase):
    def test_verify_pass_and_fail_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(main(["init"], root_dir=root), 0)
            # Review Focus #4: failing command records passed=False cleanly and returns non-zero
            rc_fail = main(["verify", "python -c \"import sys; sys.exit(2)\""], root_dir=root)
            self.assertNotEqual(rc_fail, 0)
            last_v = json.loads((root / ".evlop" / "last_verify.json").read_text(encoding="utf-8"))
            self.assertFalse(last_v["passed"])

            rc_pass = main(["verify", "python -c \"print('ok')\""], root_dir=root)
            self.assertEqual(rc_pass, 0)
            last_v2 = json.loads((root / ".evlop" / "last_verify.json").read_text(encoding="utf-8"))
            self.assertTrue(last_v2["passed"])

    def test_end_to_end_evlop_loop_and_markdown_injection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Review Focus #2: file without existing markers gets clean marker block appended
            agents_md = root / "AGENTS.md"
            agents_md.write_text("# Existing Project Rules\n\nKeep code clean.\n", encoding="utf-8")

            main(["init"], root_dir=root)
            main(["verify", "python -c \"print('tests passed')\""], root_dir=root)
            for _ in range(2):
                main([
                    "log",
                    "--task", "Fix Windows encoding issue",
                    "--symptom", "UnicodeDecodeError cp936 when reading files",
                    "--root-cause", "Path.read_text called without encoding='utf-8'",
                    "--fix", "Always pass encoding='utf-8' to read_text/write_text",
                    "--category", "debugging",
                    "--trigger", "UnicodeDecodeError cp936 gbk file read_text",
                    "--strategy", "Specify encoding='utf-8' explicitly in all Path and open calls",
                    "--anti-pattern", "Relying on OS default locale encoding"
                ], root_dir=root)

            rc_evolve = main(["evolve", "--target", "AGENTS.md"], root_dir=root)
            self.assertEqual(rc_evolve, 0)
            updated = agents_md.read_text(encoding="utf-8")
            self.assertIn("# Existing Project Rules", updated)
            self.assertIn("<!-- EVLOP:START -->", updated)
            self.assertIn("Specify encoding='utf-8' explicitly", updated)

            genes = json.loads((root / ".evlop" / "genes.json").read_text(encoding="utf-8"))
            gene_id = genes[0]["id"]
            rc_skill = main(["export-skill", "--gene-id", gene_id, "--out-dir", "skills"], root_dir=root)
            self.assertEqual(rc_skill, 0)
            skill_file = root / "skills" / f"auto-{gene_id}" / "SKILL.md"
            self.assertTrue(skill_file.exists())
            self.assertIn("name: auto-", skill_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
