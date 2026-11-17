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

### 1. [TESTING] Execution-Verified Patching Gate (`gene-execution-verified-patching-gate` | Fitness: `1.35` | S/F: `1/0`)
- **Trigger (When):** Any code modification, bug fix, or refactoring task
- **Strategy (Do):** Run python -m evlop verify '<test-cmd>' and confirm exit_code == 0 before concluding
- **Anti-Pattern (Avoid):** Self-reporting success based solely on reading the code diff

### 2. [ARCHITECTURE] Subagent Context Isolation for Deep Exploration (`gene-subagent-context-isolation-for-deep-explor` | Fitness: `1.35` | S/F: `1/0`)
- **Trigger (When):** Exploring unfamiliar modules, tracing cross-repo references, or reading >5 files
- **Strategy (Do):** Dispatch an Explore/research subagent and only ingest its structured summary into the main loop
- **Anti-Pattern (Avoid):** Dumping thousands of lines of raw file contents into the primary conversation context

### 3. [DEBUGGING] Explicit UTF-8 Encoding on Cross-Platform File I/O (`gene-explicit-utf-8-encoding-on-cross-platform` | Fitness: `1.35` | S/F: `1/0`)
- **Trigger (When):** Reading/writing files or capturing subprocess stdout/stderr across Windows/Linux
- **Strategy (Do):** Always specify encoding='utf-8' in Path.read_text, Path.write_text, open(), and subprocess.run()
- **Anti-Pattern (Avoid):** Calling Path.read_text() or subprocess.run(text=True) without explicit encoding

<!-- EVLOP:END -->
