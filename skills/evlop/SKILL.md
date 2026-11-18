---
name: evlop
description: "Universal Self-Evolving Agent Framework, Darwinian Memory & HomeRail Heterogeneous DAG Engine. Mounts via CLI (`evlop_standalone.py`), MCP (`evlop_*` tools), or Python SDK (`from evlop import EvlopEngine`)."
---

# EVLOP Whole-System Mounted Skill

Use EVLOP to recall evolved genes before coding, enforce deterministic verification gates (`verify`), distill failure-to-fix lessons (`log --from-last-failure`), mutate and supersede rules (`mutate` / `evolve`), and orchestrate heterogeneous multi-agent workflows along a self-healing DAG (`dag run` / `scorecard` / `replay`).

## Quick Invocation (Zero-Dependency Single-File or MCP)

- **Bootstrap any external project:** `python evlop_standalone.py init --target-dir <path> --bootstrap --with-hooks`
- **Recall prior genes:** `python evlop_standalone.py recall "<query>"` (or MCP tool `evlop_recall`)
- **Verify with auto-diagnosis & recall:** `python evlop_standalone.py verify "<test-cmd>"` (or MCP tool `evlop_verify`)
- **Log & Evolve:** `python evlop_standalone.py log --from-last-failure ...` then `python evlop_standalone.py evolve` (or MCP tools `evlop_log` + `evlop_evolve`)
- **Run HomeRail Heterogeneous DAG:** `python evlop_standalone.py dag run <spec.json>` (or MCP tool `evlop_dag_run`)
