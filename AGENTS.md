# AGENTS.md — Universal Self-Evolving Agent Instructions

This repository is governed by the **EVLOP Self-Evolving Agent Protocol** (`Execute -> Verify -> Learn -> Orchestrate -> Promote`). Any AI coding agent (Claude Code, Antigravity, Cursor, Codex, OpenHands, SWE-agent) operating in this workspace MUST follow the workflow below.

## Core Operational Protocol

1. **[E] Explore & Recall:** Before starting work or debugging an error, run `python -m evlop recall "<keywords>"` (or read the evolved genome block below) to apply proven project strategies.
2. **[V] Verify Deterministically:** Always validate changes via `python -m evlop verify "<test-command>"` before claiming completion or logging a lesson.
3. **[L] Log Distilled Lessons:** After fixing a bug or discovering a non-obvious pattern, record the trajectory with `python -m evlop log ...`.
4. **[O & P] Evolve & Promote:** Run `python -m evlop evolve --target AGENTS.md,CLAUDE.md` to deduplicate, fitness-score, prune, and promote verified genes into the block below.

<!-- EVLOP:START -->
## EVLOP Evolved Genome (Auto-Compiled High-Fitness Rules)

> Managed automatically by `evlop evolve`. Only verified rules (`verified_gate=True`) with high Darwinian fitness are promoted here (capped at top 15 genes to prevent Context Rot).

### 1. [ARCHITECTURE] [Pareto-HEAVY] Gen-3 GEPA Hybrid Scaffold (rsi-gen2-utopia x rsi-gen2-fast) (`gene-pareto-rsi-heavy-rsi-gen3-fast` | Fitness: `2.72` | S/F: `6/0` | Gen `4` from `rsi-gen2-utopia`)
- **Trigger (When):** Complex multi-objective coding, reasoning, or agentic workflow optimization (mode=heavy)
- **Strategy (Do):** [Pareto-Optimal RSI Gen-3] Fuse accuracy invariants of 'Gen-2 GEPA Hybrid Scaffold (rsi-gen1-utopia x rsi-gen1-fast)' with O(1)/O(N) fast-path execution of 'Gen-2 GEPA Hybrid Scaffold (rsi-gen1-fast x rsi-gen0-lite)' (Quality=100.0%, Latency=8.69ms, Cost=67 tokens).
- **Anti-Pattern (Avoid):** Using dominated O(N^2) or unverified single-objective scaffolds

### 2. [ARCHITECTURE] [Pareto-BALANCED-KNEE] Gen-3 GEPA Hybrid Scaffold (rsi-gen2-utopia x rsi-gen2-fast) (`gene-pareto-rsi-balanced-knee-rsi-gen3-fast` | Fitness: `2.72` | S/F: `6/0` | Gen `4` from `rsi-gen2-utopia`)
- **Trigger (When):** Complex multi-objective coding, reasoning, or agentic workflow optimization (mode=balanced-knee)
- **Strategy (Do):** [Pareto-Optimal RSI Gen-3] Fuse accuracy invariants of 'Gen-2 GEPA Hybrid Scaffold (rsi-gen1-utopia x rsi-gen1-fast)' with O(1)/O(N) fast-path execution of 'Gen-2 GEPA Hybrid Scaffold (rsi-gen1-fast x rsi-gen0-lite)' (Quality=100.0%, Latency=8.69ms, Cost=67 tokens).
- **Anti-Pattern (Avoid):** Using dominated O(N^2) or unverified single-objective scaffolds

### 3. [ARCHITECTURE] [Pareto-LITE] Gen-3 GEPA Hybrid Scaffold (rsi-gen2-utopia x rsi-gen2-fast) (`gene-pareto-rsi-lite-rsi-gen3-fast` | Fitness: `2.72` | S/F: `6/0` | Gen `4` from `rsi-gen2-utopia`)
- **Trigger (When):** Complex multi-objective coding, reasoning, or agentic workflow optimization (mode=lite)
- **Strategy (Do):** [Pareto-Optimal RSI Gen-3] Fuse accuracy invariants of 'Gen-2 GEPA Hybrid Scaffold (rsi-gen1-utopia x rsi-gen1-fast)' with O(1)/O(N) fast-path execution of 'Gen-2 GEPA Hybrid Scaffold (rsi-gen1-fast x rsi-gen0-lite)' (Quality=100.0%, Latency=8.69ms, Cost=67 tokens).
- **Anti-Pattern (Avoid):** Using dominated O(N^2) or unverified single-objective scaffolds

### 4. [ARCHITECTURE] BM25 Corpus IDF + CJK Bigrams + 3x Field Weighting for Recall (`gene-bm25-corpus-idf-cjk-bigrams-3x-field-weigh` | Fitness: `1.34` | S/F: `1/0` | Gen `1`)
- **Trigger (When):** Recall@1 dropped to 40% when high-fitness distractor genes contained common stop-words
- **Strategy (Do):** Implement Robertson-Sparck Jones IDF, CJK bigrams, stop-word filtering, and 3x trigger/title field weighting
- **Anti-Pattern (Avoid):** Blindly guessing without verification

### 5. [TESTING] Self-Healing DAG Node Retry with Critical Path Scorecard (`gene-self-healing-dag-node-retry-with-critical` | Fitness: `1.34` | S/F: `1/0` | Gen `3` from `gene-latency-profiled-execution-verification-ga`)
- **Trigger (When):** Any code modification, bug fix, or refactoring task
- **Strategy (Do):** On DAG node failure, extract FailureDiagnosis, inject recalled recovery genes into EVLOP_RECOVERY_GENES_JSON, auto-retry up to max_retries, and compute critical_path_nodes
- **Anti-Pattern (Avoid):** Self-reporting success based solely on reading the code diff

### 6. [ARCHITECTURE] Subagent Context Isolation for Deep Exploration (`gene-subagent-context-isolation-for-deep-explor` | Fitness: `1.34` | S/F: `1/0` | Gen `1`)
- **Trigger (When):** Exploring unfamiliar modules, tracing cross-repo references, or reading >5 files
- **Strategy (Do):** Dispatch an Explore/research subagent and only ingest its structured summary into the main loop
- **Anti-Pattern (Avoid):** Dumping thousands of lines of raw file contents into the primary conversation context

### 7. [DEBUGGING] Explicit UTF-8 Encoding on Cross-Platform File I/O (`gene-explicit-utf-8-encoding-on-cross-platform` | Fitness: `1.34` | S/F: `1/0` | Gen `1`)
- **Trigger (When):** Reading/writing files or capturing subprocess stdout/stderr across Windows/Linux
- **Strategy (Do):** Always specify encoding='utf-8' in Path.read_text, Path.write_text, open(), and subprocess.run()
- **Anti-Pattern (Avoid):** Calling Path.read_text() or subprocess.run(text=True) without explicit encoding

<!-- EVLOP:END -->
