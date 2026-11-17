import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evlop.cli import main
from evlop.compiler import export_gene_to_skill, inject_markdown_file
from evlop.models import Gene


class TestCliAndCompiler(unittest.TestCase):
    def test_verify_pass_fail_timeout_and_gbk_stdout_safety(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(main(["init"], root_dir=root), 0)
            rc_fail = main(["verify", "python -c \"import sys; sys.exit(2)\""], root_dir=root)
            self.assertNotEqual(rc_fail, 0)
            last_v = json.loads((root / ".evlop" / "last_verify.json").read_text(encoding="utf-8"))
            self.assertFalse(last_v["passed"])

            # Timeout verification (Review Focus #4)
            rc_timeout = main(
                ["verify", "--timeout", "1", "python -c \"import time; time.sleep(3)\""],
                root_dir=root,
            )
            self.assertEqual(rc_timeout, 124)
            last_timeout = json.loads((root / ".evlop" / "last_verify.json").read_text(encoding="utf-8"))
            self.assertFalse(last_timeout["passed"])

            # Important #1: non-UTF-8 bytes in subprocess output when host stdout is strict gbk
            raw_buf = io.BytesIO()
            gbk_stdout = io.TextIOWrapper(raw_buf, encoding="gbk", errors="strict")
            with patch.object(sys, "stdout", gbk_stdout):
                rc_non_utf8 = main(
                    ["verify", "python -c \"import sys; sys.stderr.buffer.write(b'\\xff\\xfe error'); sys.exit(3)\""],
                    root_dir=root,
                )
            self.assertEqual(rc_non_utf8, 3)

            rc_pass = main(["verify", "python -c \"print('ok')\""], root_dir=root)
            self.assertEqual(rc_pass, 0)

    def test_unverified_log_blocked_from_promotion_reinforcement_and_skill_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["init"], root_dir=root)
            # Log without prior verify -> must stay unverified and not promote
            main([
                "log",
                "--title", "Unverified Rule",
                "--task", "Task A",
                "--symptom", "Error A",
                "--root-cause", "Cause A",
                "--fix", "Fix A",
            ], root_dir=root)
            main(["evolve", "--target", "AGENTS.md"], root_dir=root)
            genes = json.loads((root / ".evlop" / "genes.json").read_text(encoding="utf-8"))
            self.assertFalse(genes[0]["verified_gate"])
            self.assertNotEqual(genes[0]["status"], "promoted")
            self.assertEqual(genes[0]["success_count"], 0)

            # Important #5: export-skill must reject unverified gene
            rc_export_unver = main(
                ["export-skill", "--gene-id", genes[0]["id"], "--out-dir", "skills"],
                root_dir=root,
            )
            self.assertNotEqual(rc_export_unver, 0)

            # Now pass verify and log a verified gene, then fail verify and try to inflate its success_count
            main(["verify", "python -c \"print('ok')\""], root_dir=root)
            main([
                "log",
                "--title", "Verified Rule",
                "--task", "Task B",
                "--symptom", "Symptom B",
                "--root-cause", "Cause B",
                "--fix", "Fix B",
            ], root_dir=root)
            # Fail verify
            main(["verify", "python -c \"import sys; sys.exit(1)\""], root_dir=root)
            # Unverified log of same gene must NOT increment success_count
            main([
                "log",
                "--title", "Verified Rule",
                "--task", "Task B2",
                "--symptom", "Symptom B",
                "--root-cause", "Cause B",
                "--fix", "Fix B",
            ], root_dir=root)
            genes2 = {g["title"]: g for g in json.loads((root / ".evlop" / "genes.json").read_text(encoding="utf-8"))}
            self.assertEqual(genes2["Verified Rule"]["success_count"], 1)

    def test_markdown_marker_edge_cases_and_prose_mention_safety(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            md_file = root / "AGENTS.md"
            # Important #4: inline prose mention of markers must not be clobbered
            prose = (
                "# Rules\n\n"
                "Note: EVLOP uses `<!-- EVLOP:START -->` and `<!-- EVLOP:END -->` on their own lines.\n"
                "Important paragraph that must survive!\n"
            )
            md_file.write_text(prose, encoding="utf-8")
            inject_markdown_file(md_file, [], max_genes=15)
            after_first = md_file.read_text(encoding="utf-8")
            self.assertIn("Important paragraph that must survive!", after_first)

            # Second idempotent injection
            inject_markdown_file(md_file, [], max_genes=15)
            after_second = md_file.read_text(encoding="utf-8")
            self.assertIn("Important paragraph that must survive!", after_second)
            self.assertEqual(after_first, after_second)

    def test_export_skill_escapes_quotes_and_newlines_in_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            g = Gene(
                id="gene-quote-test",
                title='Fix "KeyError" in parser',
                category="debugging",
                trigger='Traceback:\nFile "main.py", line 10\nKeyError: "id"',
                strategy="Use dict.get('id')",
                anti_pattern="Direct indexing",
                success_count=2,
                verified_gate=True,
                status="promoted",
                fitness=1.6,
            )
            skill_path = export_gene_to_skill(g, Path(tmp))
            text = skill_path.read_text(encoding="utf-8")
            frontmatter = text.split("---\n")[1]
            desc_lines = [line for line in frontmatter.splitlines() if line.startswith("description:")]
            self.assertEqual(len(desc_lines), 1)
            # Value after `description: ` must be valid JSON string (which is valid YAML double-quoted scalar)
            raw_val = desc_lines[0][len("description:"):].strip()
            parsed = json.loads(raw_val)
            self.assertIn('Fix "KeyError" in parser', parsed)

    def test_end_to_end_evlop_loop_and_markdown_injection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
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
