# AGENTS.md — EVLOP Self-Evolving Agent Protocol

This project is equipped with the **EVLOP Self-Evolving Agent Engine** (`.evlop/evlop_runner.py`).

## ⚡ Zero-Friction 2-Step Autopilot (Recommended for All Agents)
1. **Before coding (`preflight`):** Deconstruct the task into Feynman First-Principles invariants + recall top matching genes:
   `python .evlop/evlop_runner.py preflight "<your task description>"`
2. **After coding (`ship`):** Run unit tests + 100-point AST Quality Gate + auto-log/evolve/promote gene into `AGENTS.md`:
   `python .evlop/evlop_runner.py ship "<test-command>" --code <file_or_dir>`

---

## Granular 5-Stage Commands (Advanced Control)
1. **[E] Explore & Recall:** `python .evlop/evlop_runner.py recall "<error or keyword>"`
2. **[V] Verify & Audit:** `python .evlop/evlop_runner.py verify "<test-command>" --quality-gate . --auto-evolve`
3. **[L] Learn & Log:** `python .evlop/evlop_runner.py log --from-last-failure --title "<Rule Title>" --task "<Task>" --root-cause "<Why>" --fix "<How fixed>"`
4. **[O & P] Evolve & Promote:** `python .evlop/evlop_runner.py evolve --target AGENTS.md,CLAUDE.md,.cursorrules`

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

### 5. [ARCHITECTURE] [Feynman Mental Model] Stateful Accumulator Buffer with Atomic Frame-Boundary Commit (`gene-feynman-mental-model-stateful-accumulator` | Fitness: `1.79` | S/F: `2/0` | Gen `1`)
- **Trigger (When):** Cross-domain structural problem (network-protocols, log-collectors, rpc-framing, binary-parsers): Implement a stateful TCP byte-stream frame codec with 4-byte big-endian length prefix and arbitrary 
- **Strategy (Do):** Invariant: Byte-Stream Continuity Invariant: Transport chunk boundaries are completely arbitrary and independent of logical message boundaries. A decoder MUST append incoming bytes to a persistent unread buffer and loop to extract 0, 1, or N complete frames only when their full payload is present, leaving partial trailing bytes in the buffer for future calls. | Counter-examples to test: Feed a 20-byte encoded frame 1 byte at a time (`for b in frame: feed(bytes([b]))`) -> first 19 calls return `[]`, 20th call returns `[payload]`.; Feed 3 concatenated frames in a single `feed_chunk(f1 + f2 + f3)` call -> must return all 3 decoded payloads in one list.; Payload containing literal delimiter/escape bytes -> must round-trip identically (`decode(encode(raw)) == raw`).
- **Anti-Pattern (Avoid):** Assuming 1 `feed_chunk()` call equals 1 logical frame (failing when a frame is split 1 byte at a time or when 3 frames arrive in 1 chunk).; Consuming or discarding buffer bytes before verifying the full frame length is available in the buffer.; Replacing escaped sequences in-place with naive `.replace()` where double-escapes (`\\`) get corrupted.

<!-- EVLOP:END -->
