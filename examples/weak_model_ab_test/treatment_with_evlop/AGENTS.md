# AGENTS.md — EVLOP Self-Evolving Agent Protocol

This project is equipped with the **EVLOP Self-Evolving Agent Engine** (`.evlop/evlop_runner.py`).
Follow the 5-stage loop on every coding or debugging task:

1. **[E] Explore & Recall:** Before acting or when hitting an error, run:
   `python .evlop/evlop_runner.py recall "<error or keyword>"`
2. **[V] Verify Deterministically:** Run your test/build command through the gate:
   `python .evlop/evlop_runner.py verify "<test-command>"`
   *(If verification fails, EVLOP automatically diagnoses the stack trace and recalls matching fixes!)*
3. **[L] Learn & Log:** After fixing a failure and passing `verify`, log the lesson automatically:
   `python .evlop/evlop_runner.py log --from-last-failure --title "<Rule Title>" --task "<Task>" --root-cause "<Why>" --fix "<How fixed>"`
4. **[O & P] Evolve & Promote:** Compile verified high-fitness genes into project instructions:
   `python .evlop/evlop_runner.py evolve --target AGENTS.md,CLAUDE.md,.cursorrules`

<!-- EVLOP:START -->
## EVLOP Evolved Genome (Auto-Compiled High-Fitness Rules)

> Managed automatically by `evlop evolve`. Only verified rules (`verified_gate=True`) with high Darwinian fitness are promoted here (capped at top 15 genes to prevent Context Rot).

### 1. [ARCHITECTURE] Enforce O(N) / O(1) Algorithmic Complexity and Pre-Compiled Invariants (`gene-seed-algorithmic-complexity` | Fitness: `2.13` | S/F: `3/0` | Gen `1`)
- **Trigger (When):** Implementing loops, search, reconciliation, rate limiting, or data processing
- **Strategy (Do):** Use hash/dict/set indexes or monotonic deques for O(1)/O(N) lookup; hoist re.compile() and file I/O outside loops; benchmark throughput.
- **Anti-Pattern (Avoid):** Writing O(N^2) nested scans, calling re.compile() or Path.read_text() inside loops.

### 2. [DEBUGGING] Enforce Exact Numerical Precision, Explicit UTF-8 I/O, and Boundary Guards (`gene-seed-numerical-and-boundary-safety` | Fitness: `2.13` | S/F: `3/0` | Gen `1`)
- **Trigger (When):** Financial/rate math, file I/O, or handling empty/None/concurrent inputs
- **Strategy (Do):** Use decimal.Decimal with ROUND_HALF_UP for exact rates/money, pass encoding='utf-8' to all file/subprocess I/O, and guard empty/boundary inputs.
- **Anti-Pattern (Avoid):** Using binary float for exact decimals, omitting encoding='utf-8', or writing bare except: pass blocks.

### 3. [TESTING] Enforce Deterministic Test Verification and AST Quality Gate Before Completion (`gene-seed-deterministic-verification-and-ast-audit` | Fitness: `2.13` | S/F: `3/0` | Gen `1`)
- **Trigger (When):** Completing any feature, bugfix, or refactoring task
- **Strategy (Do):** Write adversarial unit tests (boundary, concurrency, scale), run `evlop verify --quality-gate <path>`, and require 0 test failures and AST quality score >= 90.
- **Anti-Pattern (Avoid):** Claiming completion based on reading diffs without running `evlop verify` and `evlop audit`.

### 4. [WORKFLOW] Enforce Subagent Context Isolation and Topological DAG Wave Concurrency (`gene-seed-subagent-isolation-and-dag-waves` | Fitness: `2.13` | S/F: `3/0` | Gen `1`)
- **Trigger (When):** Exploring >5 unfamiliar files or orchestrating multi-module agent workflows
- **Strategy (Do):** Isolate broad file exploration inside read-only subagents and execute independent multi-agent tasks in topological parallel waves via `evlop dag run`.
- **Anti-Pattern (Avoid):** Dumping raw multi-file search outputs into the primary context window or running independent agents sequentially.

### 5. [ARCHITECTURE] O(N log N) Bisect DP for Weighted Interval Scheduling (`gene-o-n-log-n-bisect-dp-for-weighted-interval` | Fitness: `1.40` | S/F: `1/0` | Gen `1`)
- **Trigger (When):** Nested loop DP over intervals triggers AST-PERF-NESTED-LOOP and is slow on N=5000
- **Strategy (Do):** Sort intervals by end time, extract end_times list, and use bisect.bisect_right(end_times, start_time) in a single O(N log N) loop
- **Anti-Pattern (Avoid):** Blindly guessing without verification

### 6. [DEBUGGING] Resolve IndentationError in verification gate (`gene-resolve-indentationerror-in-verification-g` | Fitness: `1.38` | S/F: `1/0` | Gen `1`)
- **Trigger (When):** IndentationError IndentationError: unexpected indent
- **Strategy (Do):** Guard against `IndentationError` (IndentationError: unexpected indent) and verify with `python -m unittest discover -s . -p test_interval_engine.py -v`
- **Anti-Pattern (Avoid):** Unchecked condition causing IndentationError

<!-- EVLOP:END -->
