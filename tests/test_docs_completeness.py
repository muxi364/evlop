import unittest
from pathlib import Path


class TestDocsCompleteness(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent.parent

    def test_required_docs_and_citations_exist(self):
        required_files = [
            "README.md",
            "README_EN.md",
            "LICENSE",
            ".gitignore",
            "docs/why-claude-is-strong.md",
            "docs/evlop-methodology.md",
            "docs/papers-and-ecosystem.md",
        ]
        for rel in required_files:
            self.assertTrue((self.root / rel).exists(), f"Missing {rel}")

        papers_doc = (self.root / "docs/papers-and-ecosystem.md").read_text(encoding="utf-8")
        for citation in [
            "2507.21046",  # Gao et al. TMLR 2026 Survey
            "2508.07407",  # Fang et al. Survey
            "2607.13104",  # Ren et al. 2026 Survey
            "Reflexion",
            "Voyager",
            "TextGrad",
            "ADAS",
            "SWE-agent",
            "Dive-into-Claude-Code",
            "claude-evolve",
            "Self-Evolving-Skill",
        ]:
            self.assertIn(citation, papers_doc)


if __name__ == "__main__":
    unittest.main()
