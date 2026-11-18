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

### 5. [ARCHITECTURE] [Feynman Mental Model] Stateful Accumulator Buffer with Atomic Frame-Boundary Commit (`gene-feynman-mental-model-stateful-accumulator` | Fitness: `1.83` | S/F: `2/0` | Gen `1`)
- **Trigger (When):** Cross-domain structural problem (network-protocols, log-collectors, rpc-framing, binary-parsers): Implement stateful TCP byte-stream frame codec across fragmented and coalesced chunks
- **Strategy (Do):** Invariant: Byte-Stream Continuity Invariant: Transport chunk boundaries are completely arbitrary and independent of logical message boundaries. A decoder MUST append incoming bytes to a persistent unread buffer and loop to extract 0, 1, or N complete frames only when their full payload is present, leaving partial trailing bytes in the buffer for future calls. | Counter-examples to test: Feed a 20-byte encoded frame 1 byte at a time (`for b in frame: feed(bytes([b]))`) -> first 19 calls return `[]`, 20th call returns `[payload]`.; Feed 3 concatenated frames in a single `feed_chunk(f1 + f2 + f3)` call -> must return all 3 decoded payloads in one list.; Payload containing literal delimiter/escape bytes -> must round-trip identically (`decode(encode(raw)) == raw`).
- **Anti-Pattern (Avoid):** Assuming 1 `feed_chunk()` call equals 1 logical frame (failing when a frame is split 1 byte at a time or when 3 frames arrive in 1 chunk).; Consuming or discarding buffer bytes before verifying the full frame length is available in the buffer.; Replacing escaped sequences in-place with naive `.replace()` where double-escapes (`\\`) get corrupted.

### 6. [ARCHITECTURE] [Feynman Mental Model] Cyclic Coordinate Ring with Distinct-Entity Projection & Bounded Wrap-Around Traversal (`gene-feynman-mental-model-cyclic-coordinate-rin` | Fitness: `1.83` | S/F: `2/0` | Gen `1`)
- **Trigger (When):** Cross-domain structural problem (distributed-storage, load-balancing, sharded-caches, quorum-routing): Implement consistent hash ring with virtual nodes and replica placement
- **Strategy (Do):** Invariant: Many-to-One Virtual-to-Physical Mapping Invariant: Virtual tokens on a cyclic ring (`0 .. 2^32-1`) map many positions to a smaller set of distinct physical entities. Walking clockwise (wrapping around index 0 when past the end) must deduplicate physical entities so `K` requested replicas sit on `min(K, N_physical)` DISTINCT physical hosts. | Counter-examples to test: 2 physical nodes each with 100 virtual nodes, requesting `replicas=2` -> must return 2 distinct physical nodes (never `[nodeA, nodeA]`).; Requesting `replicas=5` when only 3 physical nodes exist in the cluster -> must return all 3 distinct physical nodes without hanging.; Key hash larger than the maximum token on the ring -> must wrap around to index `0`.
- **Anti-Pattern (Avoid):** Returning the next `K` virtual tokens on the ring without checking if two virtual tokens belong to the SAME physical node.; Forgetting wrap-around (`idx = (start_idx + offset) % len(ring)`) when `bisect` reaches the end of the sorted ring.; Infinite looping when requested `replicas > len(distinct_physical_nodes)`.

### 7. [ARCHITECTURE] [Feynman Mental Model] Lazy AST / Recursive-Descent Evaluation with Explicit Associativity & Short-Circuit Thunks (`gene-feynman-mental-model-lazy-ast-recursive-de` | Fitness: `1.83` | S/F: `2/0` | Gen `1`)
- **Trigger (When):** Cross-domain structural problem (compilers, query-engines, rule-evaluators, formula-parsers): Build expression parser and evaluator with operator precedence, associativity, unary minus, and shor
- **Strategy (Do):** Invariant: Grammar hierarchy determines binding tightness and evaluation order: higher-precedence operators bind first, right-associative operators (like exponentiation `^`) recurse on the right operand (`a ^ (b ^ c)`), unary operators bind tighter than binary `+`/`-` but looser than `^`, and short-circuit boolean operators (`and`/`or`) MUST NOT evaluate their right-hand AST branch if the left-hand value already decides the outcome. | Counter-examples to test: `2 ^ 3 ^ 2` -> must equal `512` (not `64`).; `True or (1 / 0)` and `False and (1 / 0)` -> must return `True` / `False` without raising `ZeroDivisionError`.; `-2 ^ 2` vs `(-2) ^ 2` -> unary precedence handling.
- **Anti-Pattern (Avoid):** Treating exponentiation `^` as left-associative (`(2^3)^2 = 64` instead of `2^(3^2) = 512`).; Evaluating both left and right operands eagerly before applying `and`/`or`, causing crashes (e.g. `1/0`) on dead branches.; Confusing unary minus with binary subtraction after an operator or open parenthesis (`-3^2` vs `(-3)^2`).

### 8. [DEBUGGING] Resolve AssertionError in verification gate (`gene-resolve-assertionerror-in-verification-gat` | Fitness: `1.39` | S/F: `1/0` | Gen `1`)
- **Trigger (When):** AssertionError AssertionError: 4 != -4
- **Strategy (Do):** Guard against `AssertionError` (AssertionError: 4 != -4) and verify with `python -m unittest discover -s . -p test_all_three.py -v`
- **Anti-Pattern (Avoid):** Unchecked condition causing AssertionError

<!-- EVLOP:END -->
