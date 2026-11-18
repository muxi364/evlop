import json
import sys
import tempfile
import unittest
from pathlib import Path

from evlop import EvlopEngine
from evlop.cli import main
from evlop.mcp_server import handle_mcp_request


class TestUnifiedAutopilot(unittest.TestCase):
    def test_cli_preflight_and_ship_autopilot_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["init", "--bootstrap"], root_dir=root)

            # Step 1: Agent runs `evlop preflight "<task>"` before coding
            rc_pre = main(
                ["preflight", "Implement consistent hash ring with virtual nodes and replica placement"],
                root_dir=root,
            )
            self.assertEqual(rc_pre, 0)
            self.assertTrue((root / ".evlop" / "active_preflight.json").exists())

            # Step 2a: Agent writes mediocre code (with bare except:) -> `evlop ship` MUST reject it!
            code_file = root / "ring.py"
            code_file.write_text(
                "def get_node(k: str) -> str:\n    try:\n        return k\n    except:\n        return ''\n",
                encoding="utf-8",
            )
            rc_ship_bad = main(
                [
                    "ship",
                    f"\"{sys.executable}\" -c \"import ring; assert ring.get_node('a') == 'a'\"",
                    "--code",
                    str(code_file),
                ],
                root_dir=root,
            )
            self.assertNotEqual(rc_ship_bad, 0)

            # Step 2b: Agent fixes code to top-tier quality -> `evlop ship` passes AND auto-promotes gene!
            code_file.write_text(
                '''"""Clean consistent hash node lookup."""

def get_node(key: str) -> str:
    """Return assigned node for key."""
    return key if key else "default-node"
''',
                encoding="utf-8",
            )
            rc_ship_good = main(
                [
                    "ship",
                    f"\"{sys.executable}\" -c \"import ring; assert ring.get_node('a') == 'a'\"",
                    "--code",
                    str(code_file),
                    "--agent-id",
                    "autopilot-agent",
                ],
                root_dir=root,
            )
            self.assertEqual(rc_ship_good, 0)

            # Verify gene was automatically logged, evolved, and injected into AGENTS.md
            agents_md = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Cyclic Coordinate Ring", agents_md)

    def test_sdk_and_mcp_preflight_and_ship(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            engine = EvlopEngine(root)
            engine.bootstrap()

            pre_info = engine.preflight("Implement stateful TCP byte-stream frame decoder")
            self.assertIn("blueprint", pre_info)
            self.assertIn("recalled_genes", pre_info)

            mod_file = root / "decoder.py"
            mod_file.write_text(
                '''"""Clean frame decoder."""

def decode(data: bytes) -> bytes:
    """Decode bytes."""
    return data
''',
                encoding="utf-8",
            )
            ship_res = engine.ship(
                f"\"{sys.executable}\" -c \"import decoder; assert decoder.decode(b'x') == b'x'\"",
                code_path=mod_file,
                agent_id="sdk-autopilot",
            )
            self.assertTrue(ship_res["passed"])
            self.assertEqual(ship_res["ast_score"], 100.0)

            # Also verify MCP tools `evlop_preflight` and `evlop_ship` exist
            tools_resp = handle_mcp_request(
                {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
                workspace=root,
            )
            names = {t["name"] for t in tools_resp["result"]["tools"]}
            self.assertIn("evlop_preflight", names)
            self.assertIn("evlop_ship", names)


if __name__ == "__main__":
    unittest.main()
