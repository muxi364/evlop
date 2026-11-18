from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from evlop.cli import main
from evlop.models import VerifyRecord
from evlop.store import EvlopStore


class TestEngineeringHardening(unittest.TestCase):
    def test_full_bootstrap_and_standalone_runner_in_external_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            ext_proj = Path(tmp) / "external_agent_project"
            ext_proj.mkdir(parents=True, exist_ok=True)

            rc = main(["init", "--bootstrap", "--with-hooks"], root_dir=ext_proj)
            self.assertEqual(rc, 0)

            for expected_file in [
                ".evlop/config.json",
                ".evlop/evlop_runner.py",
                "AGENTS.md",
                "CLAUDE.md",
                ".cursorrules",
                ".claude/settings.json",
            ]:
                self.assertTrue(
                    (ext_proj / expected_file).exists(),
                    f"Bootstrap missing {expected_file}",
                )

            # Verify another Agent can run `.evlop/evlop_runner.py` in `ext_proj` WITHOUT PYTHONPATH or pip install
            env_clean = {"PATH": subprocess.os.environ.get("PATH", ""), "SYSTEMROOT": subprocess.os.environ.get("SYSTEMROOT", "")}
            proc = subprocess.run(
                [sys.executable, str(ext_proj / ".evlop" / "evlop_runner.py"), "status", "--json"],
                cwd=str(ext_proj),
                env=env_clean,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            status_data = json.loads(proc.stdout)
            self.assertIn("total_genes", status_data)

    def test_verify_failure_auto_diagnosis_auto_recall_and_from_last_failure_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["init"], root_dir=root)

            # Seed a verified gene for KeyError
            main(["verify", f"\"{sys.executable}\" -c \"print('ok')\""], root_dir=root)
            main([
                "log",
                "--title", "Safe Dict Lookup for Config Keys",
                "--category", "debugging",
                "--task", "Handle missing config keys",
                "--symptom", "KeyError: 'api_token'",
                "--root-cause", "Direct dict indexing on optional config key",
                "--fix", "Use config.get('api_token', '')",
                "--trigger", "KeyError api_token config dict",
                "--strategy", "Use dict.get('api_token') with fallback default",
            ], root_dir=root)

            # Now simulate another Agent hitting a failing verify with KeyError: 'api_token'
            buf = io.StringIO()
            old_stdout = sys.stdout
            try:
                sys.stdout = buf
                rc_fail = main(
                    ["verify", f"\"{sys.executable}\" -c \"d={{}}; print(d['api_token'])\""],
                    root_dir=root,
                )
            finally:
                sys.stdout = old_stdout

            self.assertNotEqual(rc_fail, 0)
            output = buf.getvalue()
            # Must auto-recall the matching gene right in the verify failure output!
            self.assertIn("[EVLOP Auto-Recall Hint]", output)
            self.assertIn("Safe Dict Lookup for Config Keys", output)

            # Check `.evlop/last_failure.json` was written with extracted error_type
            last_fail = json.loads((root / ".evlop" / "last_failure.json").read_text(encoding="utf-8"))
            self.assertEqual(last_fail["error_type"], "KeyError")

            # Now Agent fixes the code, passes verify, and logs with `--from-last-failure`
            main(["verify", f"\"{sys.executable}\" -c \"d={{}}; print(d.get('api_token', 'ok'))\""], root_dir=root)
            rc_log = main([
                "log",
                "--from-last-failure",
                "--title", "Safe Dict Lookup for Config Keys",
                "--task", "Fix api_token lookup crash",
                "--root-cause", "Direct indexing d['api_token']",
                "--fix", "Replaced with d.get('api_token', 'ok')",
            ], root_dir=root)
            self.assertEqual(rc_log, 0)
            genes = json.loads((root / ".evlop" / "genes.json").read_text(encoding="utf-8"))
            self.assertEqual(genes[0]["success_count"], 2)

    def test_stale_verification_ttl_expiration_blocks_reward_hacking(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["init"], root_dir=root)
            store = EvlopStore(root)
            expired_ts = (datetime.now(timezone.utc) - timedelta(minutes=120)).isoformat()
            store.save_verify(
                VerifyRecord(
                    command="pytest",
                    exit_code=0,
                    passed=True,
                    timestamp=expired_ts,
                    output_snippet="ok",
                    duration_ms=12.0,
                )
            )
            # Logging with a 2-hour-old verification record (TTL default 30m) must treat verified=False
            main([
                "log",
                "--title", "Stale Verify Rule",
                "--task", "Attempt stale verify reuse",
                "--symptom", "Some bug",
                "--root-cause", "Some cause",
                "--fix", "Some fix",
            ], root_dir=root)
            genes = json.loads((root / ".evlop" / "genes.json").read_text(encoding="utf-8"))
            self.assertFalse(genes[0]["verified_gate"])
            self.assertEqual(genes[0]["success_count"], 0)

    def test_concurrent_swarm_agent_logging_is_lock_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["init"], root_dir=root)
            main(["verify", f"\"{sys.executable}\" -c \"print('ok')\""], root_dir=root)

            def _worker(idx: int) -> int:
                return main([
                    "log",
                    "--title", f"Swarm Worker Rule {idx}",
                    "--category", "workflow",
                    "--task", f"Parallel task {idx}",
                    "--symptom", f"Distinct symptom {idx} alpha_{idx*17}",
                    "--root-cause", f"Cause {idx}",
                    "--fix", f"Fix {idx}",
                    "--agent-id", f"swarm-agent-{idx}",
                ], root_dir=root)

            with ThreadPoolExecutor(max_workers=6) as pool:
                results = list(pool.map(_worker, range(6)))

            self.assertEqual(results, [0, 0, 0, 0, 0, 0])
            store = EvlopStore(root)
            episodes = store.load_episodes()
            genes = store.load_genes()
            self.assertEqual(len(episodes), 6)
            self.assertEqual(len(genes), 6)

    def test_mcp_stdio_jsonrpc_server_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["init"], root_dir=root)

            from evlop.mcp_server import handle_mcp_request

            init_resp = handle_mcp_request(
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                workspace=root,
            )
            self.assertEqual(init_resp["result"]["serverInfo"]["name"], "evlop-mcp")

            tools_resp = handle_mcp_request(
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
                workspace=root,
            )
            tool_names = {t["name"] for t in tools_resp["result"]["tools"]}
            for expected_tool in ["evlop_verify", "evlop_log", "evlop_recall", "evlop_evolve", "evlop_status"]:
                self.assertIn(expected_tool, tool_names)

            # Call evlop_verify -> evlop_log -> evlop_evolve -> evlop_recall via MCP
            v_resp = handle_mcp_request(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "evlop_verify",
                        "arguments": {"command": f"\"{sys.executable}\" -c \"print('mcp-verify-ok')\""},
                    },
                },
                workspace=root,
            )
            self.assertFalse(v_resp["result"]["isError"])

            l_resp = handle_mcp_request(
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {
                        "name": "evlop_log",
                        "arguments": {
                            "title": "MCP JSON-RPC Stdio Protocol Rule",
                            "category": "tooling",
                            "task": "Expose EVLOP over MCP",
                            "symptom": "External agents need native tool calls",
                            "root_cause": "CLI requires shell escaping",
                            "fix": "Use evlop_log and evlop_recall MCP tools",
                            "agent_id": "mcp-client-agent",
                        },
                    },
                },
                workspace=root,
            )
            self.assertFalse(l_resp["result"]["isError"])

            r_resp = handle_mcp_request(
                {
                    "jsonrpc": "2.0",
                    "id": 5,
                    "method": "tools/call",
                    "params": {
                        "name": "evlop_recall",
                        "arguments": {"query": "MCP JSON-RPC Stdio"},
                    },
                },
                workspace=root,
            )
            self.assertIn("MCP JSON-RPC Stdio Protocol Rule", r_resp["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
