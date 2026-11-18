# CLAUDE.md — Claude Code Self-Evolving Harness Configuration

This project integrates the **EVLOP Self-Evolving Framework** inspired by Claude 5.2/5.5's execution-guided RL and harness co-design.

## Quick Commands

- **Run Test Suite via EVLOP Gate:** `PYTHONPATH=src python -m evlop verify "python -m unittest discover -s tests -v"`
- **Recall Relevant Genes:** `PYTHONPATH=src python -m evlop recall "<symptom or keyword>"`
- **Log New Experience Gene:** `PYTHONPATH=src python -m evlop log --title "..." --task "..." --symptom "..." --root-cause "..." --fix "..."`
- **Evolve & Recompile Rules:** `PYTHONPATH=src python -m evlop evolve --target AGENTS.md,CLAUDE.md`
- **Check Genome Status:** `PYTHONPATH=src python -m evlop status`

## Architectural Rules

- Zero external runtime dependencies: `src/evlop/` uses Python 3.10+ standard library only.
- Never promote unverified rules: `verified_gate` requires a passing `evlop verify` execution.
- Prevent Context Rot: Keep active promoted genes capped at `max_active_genes = 15`.

<!-- EVLOP:START -->
## EVLOP Evolved Genome (Auto-Compiled High-Fitness Rules)

> Managed automatically by `evlop evolve`. Only verified rules (`verified_gate=True`) with high Darwinian fitness are promoted here (capped at top 15 genes to prevent Context Rot).

### 1. [ARCHITECTURE] BM25 Corpus IDF + CJK Bigrams + 3x Field Weighting for Recall (`gene-bm25-corpus-idf-cjk-bigrams-3x-field-weigh` | Fitness: `1.35` | S/F: `1/0` | Gen `1`)
- **Trigger (When):** Recall@1 dropped to 40% when high-fitness distractor genes contained common stop-words
- **Strategy (Do):** Implement Robertson-Sparck Jones IDF, CJK bigrams, stop-word filtering, and 3x trigger/title field weighting
- **Anti-Pattern (Avoid):** Blindly guessing without verification

### 2. [TESTING] Self-Healing DAG Node Retry with Critical Path Scorecard (`gene-self-healing-dag-node-retry-with-critical` | Fitness: `1.35` | S/F: `1/0` | Gen `3` from `gene-latency-profiled-execution-verification-ga`)
- **Trigger (When):** Any code modification, bug fix, or refactoring task
- **Strategy (Do):** On DAG node failure, extract FailureDiagnosis, inject recalled recovery genes into EVLOP_RECOVERY_GENES_JSON, auto-retry up to max_retries, and compute critical_path_nodes
- **Anti-Pattern (Avoid):** Self-reporting success based solely on reading the code diff

### 3. [ARCHITECTURE] Subagent Context Isolation for Deep Exploration (`gene-subagent-context-isolation-for-deep-explor` | Fitness: `1.34` | S/F: `1/0` | Gen `1`)
- **Trigger (When):** Exploring unfamiliar modules, tracing cross-repo references, or reading >5 files
- **Strategy (Do):** Dispatch an Explore/research subagent and only ingest its structured summary into the main loop
- **Anti-Pattern (Avoid):** Dumping thousands of lines of raw file contents into the primary conversation context

### 4. [DEBUGGING] Explicit UTF-8 Encoding on Cross-Platform File I/O (`gene-explicit-utf-8-encoding-on-cross-platform` | Fitness: `1.34` | S/F: `1/0` | Gen `1`)
- **Trigger (When):** Reading/writing files or capturing subprocess stdout/stderr across Windows/Linux
- **Strategy (Do):** Always specify encoding='utf-8' in Path.read_text, Path.write_text, open(), and subprocess.run()
- **Anti-Pattern (Avoid):** Calling Path.read_text() or subprocess.run(text=True) without explicit encoding

<!-- EVLOP:END -->
