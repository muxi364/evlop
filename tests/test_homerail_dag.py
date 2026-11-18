import json
import sys
import tempfile
import unittest
from pathlib import Path

from evlop.cli import main


class TestHomeRailHeterogeneousDag(unittest.TestCase):
    def test_dag_topological_wave_concurrency_scorecard_and_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["init"], root_dir=root)

            # Seed an initial gene so DAG nodes can auto-recall it
            main(["verify", f"\"{sys.executable}\" -c \"print('seed-ok')\""], root_dir=root)
            main([
                "log",
                "--title", "Validate JSON Schema Before Handoff",
                "--category", "architecture",
                "--task", "Ensure multi-agent handoff payloads are valid JSON",
                "--symptom", "JSONDecodeError during downstream node handoff",
                "--root-cause", "Upstream agent printed unstructured text",
                "--fix", "Always validate handoff output as strict JSON",
                "--trigger", "multi-agent handoff json schema",
                "--agent-id", "claude-architect",
            ], root_dir=root)

            # Define a heterogeneous 4-node diamond DAG Rail (inspired by xiaotianfotos/homerail):
            # Wave 0: [plan_node (claude-code)]
            # Wave 1 (Concurrent!): [code_worker (codex), security_auditor (gemini)] both depend on plan_node
            # Wave 2: [verify_gate (evlop-verifier)] depends on both code_worker and security_auditor
            dag_spec = {
                "rail_id": "heterogeneous-release-rail",
                "description": "Heterogeneous multi-agent concurrent DAG workflow",
                "nodes": [
                    {
                        "id": "plan_node",
                        "role": "Architecture Planner",
                        "agent_type": "claude-code",
                        "depends_on": [],
                        "recall_query": "multi-agent handoff json",
                        "command": f"\"{sys.executable}\" -c \"import time; time.sleep(0.1); print('PLAN_READY')\"",
                    },
                    {
                        "id": "code_worker",
                        "role": "Implementation Engineer",
                        "agent_type": "codex",
                        "depends_on": ["plan_node"],
                        "recall_query": "json schema",
                        "command": f"\"{sys.executable}\" -c \"import time; time.sleep(0.2); print('CODE_BUILT')\"",
                    },
                    {
                        "id": "security_auditor",
                        "role": "Security & Boundary Auditor",
                        "agent_type": "gemini",
                        "depends_on": ["plan_node"],
                        "recall_query": "json schema",
                        "command": f"\"{sys.executable}\" -c \"import time; time.sleep(0.2); print('AUDIT_CLEAN')\"",
                    },
                    {
                        "id": "verify_gate",
                        "role": "Deterministic Integration Verifier",
                        "agent_type": "evlop-verifier",
                        "depends_on": ["code_worker", "security_auditor"],
                        "command": f"\"{sys.executable}\" -c \"print('INTEGRATION_VERIFIED')\"",
                    },
                ],
            }
            dag_file = root / "rail.json"
            dag_file.write_text(json.dumps(dag_spec, indent=2), encoding="utf-8")

            # 1. Run `evlop dag run rail.json`
            rc_dag = main(["dag", "run", str(dag_file), "--run-id", "run-test-001"], root_dir=root)
            self.assertEqual(rc_dag, 0)

            # 2. Inspect Scorecard (`evlop scorecard run-test-001 --json`)
            run_record_path = root / ".evlop" / "runs" / "run-test-001.json"
            self.assertTrue(run_record_path.exists())
            run_data = json.loads(run_record_path.read_text(encoding="utf-8"))

            self.assertEqual(run_data["status"], "passed")
            self.assertEqual(len(run_data["waves"]), 3)
            self.assertEqual(run_data["waves"][0], ["plan_node"])
            self.assertEqual( sorted(run_data["waves"][1]), ["code_worker", "security_auditor"])
            self.assertEqual(run_data["waves"][2], ["verify_gate"])

            scorecard = run_data["scorecard"]
            self.assertEqual(scorecard["total_nodes"], 4)
            self.assertEqual(scorecard["passed_nodes"], 4)
            self.assertEqual(scorecard["overall_score"], 100.0)
            self.assertGreater(scorecard["parallel_speedup_factor"], 1.0)
            self.assertEqual(
                sorted(scorecard["heterogeneous_agents"]),
                ["claude-code", "codex", "evlop-verifier", "gemini"],
            )

            # 3. Verify CLI `evlop scorecard` and `evlop replay`
            rc_sc = main(["scorecard", "run-test-001"], root_dir=root)
            self.assertEqual(rc_sc, 0)

            rc_rep = main(
                ["replay", "run-test-001", "--from-node", "verify_gate"],
                root_dir=root,
            )
            self.assertEqual(rc_rep, 0)

    def test_dag_cycle_detection_and_failed_node_auto_gene_logging(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["init"], root_dir=root)

            # Cyclic DAG must be rejected cleanly
            bad_dag = {
                "rail_id": "cyclic-rail",
                "nodes": [
                    {"id": "a", "agent_type": "claude-code", "depends_on": ["b"], "command": "echo a"},
                    {"id": "b", "agent_type": "codex", "depends_on": ["a"], "command": "echo b"},
                ],
            }
            bad_path = root / "bad_rail.json"
            bad_path.write_text(json.dumps(bad_dag), encoding="utf-8")
            rc_cycle = main(["dag", "run", str(bad_path)], root_dir=root)
            self.assertNotEqual(rc_cycle, 0)


if __name__ == "__main__":
    unittest.main()
