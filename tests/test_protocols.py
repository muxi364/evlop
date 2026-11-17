import json
import unittest
from pathlib import Path


class TestProtocolsAndTemplates(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent

    def test_skill_md_has_frontmatter_and_five_stages(self):
        skill_text = (self.repo_root / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill_text.startswith("---\n"))
        for keyword in [
            "name: evlop",
            "evlop recall",
            "evlop verify",
            "evlop log",
            "evlop evolve",
            "evlop export-skill",
        ]:
            self.assertIn(keyword, skill_text)

    def test_agents_and_claude_md_contain_evlop_markers(self):
        for fname in [
            "AGENTS.md",
            "CLAUDE.md",
            "templates/AGENTS.template.md",
            "templates/CLAUDE.template.md",
        ]:
            content = (self.repo_root / fname).read_text(encoding="utf-8")
            self.assertIn("<!-- EVLOP:START -->", content)
            self.assertIn("<!-- EVLOP:END -->", content)

    def test_claude_hooks_template_is_valid_json(self):
        hooks_path = self.repo_root / "templates" / "claude-settings-hooks.json"
        data = json.loads(hooks_path.read_text(encoding="utf-8"))
        self.assertIn("hooks", data)


if __name__ == "__main__":
    unittest.main()
