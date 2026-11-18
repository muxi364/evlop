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

### 5. [ARCHITECTURE] O(V+E) Topological Wave and Critical-Path DP Scheduler (`gene-o-v-e-topological-wave-and-critical-path-d` | Fitness: `1.38` | S/F: `1/0` | Gen `1`)
- **Trigger (When):** Recursive DFS critical-path search hits RecursionError or exponential blowup on dense DAGs
- **Strategy (Do):** Run Kahn O(V+E) wave sort followed by single-pass forward DP for critical path
- **Anti-Pattern (Avoid):** Blindly guessing without verification

### 6. [DEBUGGING] Idempotent Double-Entry Decimal Ledger with 10000-bps Fee Conservation (`gene-idempotent-double-entry-decimal-ledger-wit` | Fitness: `1.38` | S/F: `1/0` | Gen `1`)
- **Trigger (When):** Duplicate transaction replay and float rounding drift corrupt account balances
- **Strategy (Do):** Cache receipts by tx_id and compute fee via Decimal(fee_bps)/Decimal(10000) with ROUND_HALF_UP
- **Anti-Pattern (Avoid):** Blindly guessing without verification

### 7. [TOOLING] Single-Pass Alternation Regex Redactor and Canonical Path Guard (`gene-single-pass-alternation-regex-redactor-and` | Fitness: `1.38` | S/F: `1/0` | Gen `1`)
- **Trigger (When):** Sequential regex substitutions and string-prefix path checks are slow and bypassable
- **Strategy (Do):** Pre-compile a single combined named-group regex at module load and enforce Path.resolve().is_relative_to()
- **Anti-Pattern (Avoid):** Blindly guessing without verification

### 8. [ARCHITECTURE] O(1) Amortized Monotonic Deque Sliding Window (`gene-o-1-amortized-monotonic-deque-sliding-wind` | Fitness: `1.38` | S/F: `1/0` | Gen `1`)
- **Trigger (When):** O(N) min/max/sum recalculation over sliding window degrades streaming throughput
- **Strategy (Do):** Maintain monotonic min/max deques and running sum for O(1) amortized updates
- **Anti-Pattern (Avoid):** Blindly guessing without verification

<!-- EVLOP:END -->
