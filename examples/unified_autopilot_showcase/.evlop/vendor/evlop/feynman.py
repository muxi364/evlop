"""
Feynman Technique First-Principles Deconstruction & Anti-Overfitting Engine (`evlop feynman`).

Prevents rote memorization ("over-overlapping" / overfitting to surface-level keywords) by forcing
any AI Agent (especially lightweight weak models like `flash_lite`) to execute the 4-Step Feynman Loop:
1. [Concept Deconstruction]: Explain the core mechanism in plain, domain-independent terms.
2. [Naive Intuition Counter-Example]: Construct the minimal input where a naive implementation breaks.
3. [Boundary & Conservation Invariant]: Check degenerate boundaries (0, 1, ties, fragmentation, wrap-around).
4. [Universal Mental Model Distillation]: Abstract the solution into a cross-domain transferable gene.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any

from evlop.models import Gene, slugify_gene_id, utc_now_iso


@dataclass
class FeynmanBlueprint:
    task_description: str
    first_principles_invariant: str
    naive_intuition_traps: list[str]
    minimal_counter_examples: list[str]
    boundary_checklist: list[str]
    universal_mental_model: str
    transferable_domains: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        lines = [
            "## Feynman 4-Step First-Principles Blueprint (Anti-Overfitting Protocol)",
            "",
            f"**Target Task:** {self.task_description}",
            "",
            "### Step 1: Plain-Language First-Principles Invariant (What Must Always Hold?)",
            f"- {self.first_principles_invariant}",
            "",
            "### Step 2: Why Naive Intuition Fails (Cognitive Traps to Avoid)",
        ]
        for trap in self.naive_intuition_traps:
            lines.append(f"- **Trap:** {trap}")
        lines.append("")
        lines.append("### Step 3: Minimal Counter-Examples You MUST Write Tests For")
        for ce in self.minimal_counter_examples:
            lines.append(f"- **Counter-Example Test:** {ce}")
        lines.append("")
        lines.append("### Step 4: Degenerate Boundary Checklist & Universal Mental Model")
        for b in self.boundary_checklist:
            lines.append(f"- [ ] {b}")
        lines.append(f"- **Universal Mental Model:** {self.universal_mental_model}")
        return "\n".join(lines)


# Domain-agnostic structural archetypes detected from first-principles problem structure
_ARCHETYPES: list[dict[str, Any]] = [
    {
        "pattern": re.compile(r"expression|parser|eval|operator|precedence|associativ|short[- ]?circuit|ast|compiler", re.I),
        "invariant": "Grammar hierarchy determines binding tightness and evaluation order: higher-precedence operators bind first, right-associative operators (like exponentiation `^`) recurse on the right operand (`a ^ (b ^ c)`), unary operators bind tighter than binary `+`/`-` but looser than `^`, and short-circuit boolean operators (`and`/`or`) MUST NOT evaluate their right-hand AST branch if the left-hand value already decides the outcome.",
        "traps": [
            "Treating exponentiation `^` as left-associative (`(2^3)^2 = 64` instead of `2^(3^2) = 512`).",
            "Evaluating both left and right operands eagerly before applying `and`/`or`, causing crashes (e.g. `1/0`) on dead branches.",
            "Confusing unary minus with binary subtraction after an operator or open parenthesis (`-3^2` vs `(-3)^2`).",
        ],
        "counter_examples": [
            "`2 ^ 3 ^ 2` -> must equal `512` (not `64`).",
            "`True or (1 / 0)` and `False and (1 / 0)` -> must return `True` / `False` without raising `ZeroDivisionError`.",
            "`-2 ^ 2` vs `(-2) ^ 2` -> unary precedence handling.",
        ],
        "mental_model": "Lazy AST / Recursive-Descent Evaluation with Explicit Associativity & Short-Circuit Thunks",
        "domains": ["compilers", "query-engines", "rule-evaluators", "formula-parsers"],
    },
    {
        "pattern": re.compile(r"ring|hash|replica|virtual|node|cluster|partition|shard|consistent", re.I),
        "invariant": "Many-to-One Virtual-to-Physical Mapping Invariant: Virtual tokens on a cyclic ring (`0 .. 2^32-1`) map many positions to a smaller set of distinct physical entities. Walking clockwise (wrapping around index 0 when past the end) must deduplicate physical entities so `K` requested replicas sit on `min(K, N_physical)` DISTINCT physical hosts.",
        "traps": [
            "Returning the next `K` virtual tokens on the ring without checking if two virtual tokens belong to the SAME physical node.",
            "Forgetting wrap-around (`idx = (start_idx + offset) % len(ring)`) when `bisect` reaches the end of the sorted ring.",
            "Infinite looping when requested `replicas > len(distinct_physical_nodes)`.",
        ],
        "counter_examples": [
            "2 physical nodes each with 100 virtual nodes, requesting `replicas=2` -> must return 2 distinct physical nodes (never `[nodeA, nodeA]`).",
            "Requesting `replicas=5` when only 3 physical nodes exist in the cluster -> must return all 3 distinct physical nodes without hanging.",
            "Key hash larger than the maximum token on the ring -> must wrap around to index `0`.",
        ],
        "mental_model": "Cyclic Coordinate Ring with Distinct-Entity Projection & Bounded Wrap-Around Traversal",
        "domains": ["distributed-storage", "load-balancing", "sharded-caches", "quorum-routing"],
    },
    {
        "pattern": re.compile(r"stream|chunk|frame|packet|buffer|tcp|codec|escape|delimiter|reassembl", re.I),
        "invariant": "Byte-Stream Continuity Invariant: Transport chunk boundaries are completely arbitrary and independent of logical message boundaries. A decoder MUST append incoming bytes to a persistent unread buffer and loop to extract 0, 1, or N complete frames only when their full payload is present, leaving partial trailing bytes in the buffer for future calls.",
        "traps": [
            "Assuming 1 `feed_chunk()` call equals 1 logical frame (failing when a frame is split 1 byte at a time or when 3 frames arrive in 1 chunk).",
            "Consuming or discarding buffer bytes before verifying the full frame length is available in the buffer.",
            "Replacing escaped sequences in-place with naive `.replace()` where double-escapes (`\\\\`) get corrupted.",
        ],
        "counter_examples": [
            "Feed a 20-byte encoded frame 1 byte at a time (`for b in frame: feed(bytes([b]))`) -> first 19 calls return `[]`, 20th call returns `[payload]`.",
            "Feed 3 concatenated frames in a single `feed_chunk(f1 + f2 + f3)` call -> must return all 3 decoded payloads in one list.",
            "Payload containing literal delimiter/escape bytes -> must round-trip identically (`decode(encode(raw)) == raw`).",
        ],
        "mental_model": "Stateful Accumulator Buffer with Atomic Frame-Boundary Commit",
        "domains": ["network-protocols", "log-collectors", "rpc-framing", "binary-parsers"],
    },
]


def generate_feynman_blueprint(task_description: str) -> FeynmanBlueprint:
    """
    Deconstruct any engineering task using the 4-Step Feynman Technique so a model
    understands the underlying structural invariant and counter-examples before coding.
    """
    matched_arch = None
    for arch in _ARCHETYPES:
        if arch["pattern"].search(task_description):
            matched_arch = arch
            break

    if matched_arch is not None:
        return FeynmanBlueprint(
            task_description=task_description,
            first_principles_invariant=matched_arch["invariant"],
            naive_intuition_traps=list(matched_arch["traps"]),
            minimal_counter_examples=list(matched_arch["counter_examples"]),
            boundary_checklist=[
                "Empty / zero-element input handled without crash",
                "Single-element and tie-breaking / wrap-around boundary tested",
                "All 3 Feynman minimal counter-examples encoded as unit tests",
                "AST Quality Gate (`evlop audit --min-score 100`) passes with 0 findings",
            ],
            universal_mental_model=matched_arch["mental_model"],
            transferable_domains=list(matched_arch["domains"]),
        )

    return FeynmanBlueprint(
        task_description=task_description,
        first_principles_invariant=(
            "Identify the conserved quantity or structural state invariant before writing code: "
            "separate state representation from transition rules, and ensure every operation preserves the invariant."
        ),
        naive_intuition_traps=[
            "Conflating surface input chunks/order with logical domain boundaries.",
            "Using O(N^2) nested scans instead of pre-indexing or monotonic structures.",
            "Eagerly evaluating or mutating state before preconditions are verified.",
        ],
        minimal_counter_examples=[
            "Degenerate empty/zero input (`N=0`) and single-element boundary (`N=1`).",
            "Duplicate / colliding keys or asymmetric tie-breaking values.",
            "Adversarial scale input (`N >= 2,000`) verifying O(N) or O(N log N) latency.",
        ],
        boundary_checklist=[
            "State invariant holds before and after every public method call",
            "All 3 Feynman counter-examples verified by deterministic unit tests",
            "AST Quality Gate (`evlop audit --min-score 100`) passes with 0 findings",
        ],
        universal_mental_model="First-Principles Invariant Decomposition & Counter-Example Driven Design",
        transferable_domains=["algorithms", "systems-engineering", "data-pipelines"],
    )


def distill_feynman_gene(
    blueprint: FeynmanBlueprint,
    verified: bool = True,
    agent_id: str = "feynman-agent",
    duration_ms: float = 10.0,
) -> Gene:
    """Convert a FeynmanBlueprint into a domain-agnostic, cross-domain transferable Gene."""
    now_iso = utc_now_iso()
    title = f"[Feynman Mental Model] {blueprint.universal_mental_model}"
    gid = slugify_gene_id(title)
    domains_str = ", ".join(blueprint.transferable_domains) if blueprint.transferable_domains else "cross-domain"
    return Gene(
        id=gid,
        title=title,
        category="architecture",
        trigger=f"Cross-domain structural problem ({domains_str}): {blueprint.task_description[:100]}",
        strategy=f"Invariant: {blueprint.first_principles_invariant} | Counter-examples to test: {'; '.join(blueprint.minimal_counter_examples)}",
        anti_pattern="; ".join(blueprint.naive_intuition_traps),
        success_count=2 if verified else 0,
        failure_count=0,
        verified_gate=verified,
        created_at=now_iso,
        last_used_at=now_iso,
        status="promoted" if verified else "candidate",
        fitness=1.85 if verified else 0.5,
        contributors=[agent_id],
        best_duration_ms=duration_ms,
    )
