import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestWholeSystemMountingAndAblation(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent

    def test_mode1_python_sdk_evlop_engine_mount(self):
        """Verify external Python agent frameworks (LangGraph/AutoGen/CrewAI) can mount EVLOP via `from evlop import EvlopEngine`."""
        from evlop import EvlopEngine

        with tempfile.TemporaryDirectory() as tmp:
            engine = EvlopEngine(Path(tmp))
            engine.bootstrap(with_hooks=True)
            v_rec = engine.verify(f"\"{sys.executable}\" -c \"print('sdk-ok')\"")
            self.assertTrue(v_rec.passed)
            gene = engine.log_experience(
                title="Use EvlopEngine SDK in Python Agents",
                category="architecture",
                task="Mount EVLOP programmatically",
                symptom="Subprocess CLI overhead in Python loops",
                root_cause="No direct Python class API",
                fix="Import EvlopEngine from evlop",
                agent_id="langgraph-worker",
            )
            self.assertTrue(gene.verified_gate)
            engine.evolve()
            hits = engine.recall("EvlopEngine SDK")
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0].id, gene.id)

    def test_mode2_global_mcp_server_multi_workspace_and_all_9_tools(self):
        """Verify a single globally mounted MCP server can operate on arbitrary external `workspace_dir` paths and exposes all 9 tools."""
        from evlop.mcp_server import handle_mcp_request

        with tempfile.TemporaryDirectory() as server_cwd, tempfile.TemporaryDirectory() as external_proj:
            ext_path = str(Path(external_proj).resolve())

            tools_resp = handle_mcp_request(
                {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
                workspace=Path(server_cwd),
            )
            tool_names = {t["name"] for t in tools_resp["result"]["tools"]}
            expected_9 = {
                "evlop_init_bootstrap",
                "evlop_recall",
                "evlop_verify",
                "evlop_log",
                "evlop_mutate",
                "evlop_lineage",
                "evlop_evolve",
                "evlop_dag_run",
                "evlop_status",
            }
            self.assertTrue(expected_9.issubset(tool_names), f"Missing MCP tools: {expected_9 - tool_names}")

            # Call evlop_init_bootstrap targeting `external_proj` from a server running in `server_cwd`
            b_resp = handle_mcp_request(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "evlop_init_bootstrap",
                        "arguments": {"workspace_dir": ext_path, "with_hooks": True},
                    },
                },
                workspace=Path(server_cwd),
            )
            self.assertFalse(b_resp["result"]["isError"])
            self.assertTrue((Path(external_proj) / "AGENTS.md").exists())
            self.assertTrue((Path(external_proj) / ".mcp.json").exists())

    def test_mode3_single_file_standalone_drop_in_executable(self):
        """Verify `evlop_standalone.py` works as a 1-file zero-dependency drop-in executable in an isolated temp folder."""
        standalone_src = self.repo_root / "evlop_standalone.py"
        self.assertTrue(standalone_src.exists(), "Missing root evlop_standalone.py single-file distribution")

        with tempfile.TemporaryDirectory() as isolated_dir:
            iso_path = Path(isolated_dir)
            target_script = iso_path / "evlop_standalone.py"
            target_script.write_text(standalone_src.read_text(encoding="utf-8"), encoding="utf-8")

            env_clean = {
                "PATH": subprocess.os.environ.get("PATH", ""),
                "SYSTEMROOT": subprocess.os.environ.get("SYSTEMROOT", ""),
            }
            proc_init = subprocess.run(
                [sys.executable, str(target_script), "init"],
                cwd=str(iso_path),
                env=env_clean,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            self.assertIn("[EVLOP]", proc_init.stdout)

            proc_status = subprocess.run(
                [sys.executable, str(target_script), "status", "--json"],
                cwd=str(iso_path),
                env=env_clean,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            status_obj = json.loads(proc_status.stdout)
            self.assertIn("total_genes", status_obj)

    def test_mode4_plugin_and_mcp_manifests_valid(self):
        """Verify whole-repository plugin and MCP discovery manifests exist and are valid JSON."""
        for rel_path in [
            "plugin.json",
            ".claude-plugin/plugin.json",
            ".mcp.json",
            "skills/evlop/SKILL.md",
        ]:
            full = self.repo_root / rel_path
            self.assertTrue(full.exists(), f"Missing whole-mount manifest: {rel_path}")
            if rel_path.endswith(".json"):
                data = json.loads(full.read_text(encoding="utf-8"))
                self.assertIsInstance(data, dict)

    def test_scientific_ablation_study_proves_statistically_significant_gains(self):
        """Run the controlled A/B ablation experiment and verify Treatment (Mounted EVLOP) strictly outperforms Control."""
        sys.path.insert(0, str(self.repo_root))
        from benchmarks.scientific_ablation_study import run_ablation_study

        study = run_ablation_study()
        self.assertGreater(
            study["treatment_evlop_mounted"]["first_pass_success_rate_pct"],
            study["control_unmounted"]["first_pass_success_rate_pct"],
        )
        self.assertLess(
            study["treatment_evlop_mounted"]["total_verification_attempts"],
            study["control_unmounted"]["total_verification_attempts"],
        )
        self.assertGreaterEqual(
            study["improvements"]["post_evolution_code_speedup_x"],
            15.0,
        )
        self.assertGreaterEqual(
            study["improvements"]["cumulative_amdahl_speedup_x"],
            2.5,
        )
        self.assertEqual(study["mounting_modes_verified"], 6)


if __name__ == "__main__":
    unittest.main()
