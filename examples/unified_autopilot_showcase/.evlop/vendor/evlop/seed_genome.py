"""Foundational SOTA Seed Genome pre-loaded when bootstrapping external agent workspaces."""

from __future__ import annotations

from evlop.models import Gene, utc_now_iso


def get_default_seed_genes() -> list[Gene]:
    """Return 4 foundational SOTA engineering genes distilled from Claude 5.2/5.5, AlphaEvolve, and SWE-agent."""
    now = utc_now_iso()
    return [
        Gene(
            id="gene-seed-algorithmic-complexity",
            title="Enforce O(N) / O(1) Algorithmic Complexity and Pre-Compiled Invariants",
            category="architecture",
            trigger="Implementing loops, search, reconciliation, rate limiting, or data processing",
            strategy="Use hash/dict/set indexes or monotonic deques for O(1)/O(N) lookup; hoist re.compile() and file I/O outside loops; benchmark throughput.",
            anti_pattern="Writing O(N^2) nested scans, calling re.compile() or Path.read_text() inside loops.",
            success_count=3,
            failure_count=0,
            verified_gate=True,
            created_at=now,
            last_used_at=now,
            status="promoted",
            fitness=2.15,
            contributors=["evlop-seed-genome"],
            best_duration_ms=5.0,
        ),
        Gene(
            id="gene-seed-numerical-and-boundary-safety",
            title="Enforce Exact Numerical Precision, Explicit UTF-8 I/O, and Boundary Guards",
            category="debugging",
            trigger="Financial/rate math, file I/O, or handling empty/None/concurrent inputs",
            strategy="Use decimal.Decimal with ROUND_HALF_UP for exact rates/money, pass encoding='utf-8' to all file/subprocess I/O, and guard empty/boundary inputs.",
            anti_pattern="Using binary float for exact decimals, omitting encoding='utf-8', or writing bare except: pass blocks.",
            success_count=3,
            failure_count=0,
            verified_gate=True,
            created_at=now,
            last_used_at=now,
            status="promoted",
            fitness=2.10,
            contributors=["evlop-seed-genome"],
            best_duration_ms=8.0,
        ),
        Gene(
            id="gene-seed-deterministic-verification-and-ast-audit",
            title="Enforce Deterministic Test Verification and AST Quality Gate Before Completion",
            category="testing",
            trigger="Completing any feature, bugfix, or refactoring task",
            strategy="Write adversarial unit tests (boundary, concurrency, scale), run `evlop verify --quality-gate <path>`, and require 0 test failures and AST quality score >= 90.",
            anti_pattern="Claiming completion based on reading diffs without running `evlop verify` and `evlop audit`.",
            success_count=3,
            failure_count=0,
            verified_gate=True,
            created_at=now,
            last_used_at=now,
            status="promoted",
            fitness=2.05,
            contributors=["evlop-seed-genome"],
            best_duration_ms=10.0,
        ),
        Gene(
            id="gene-seed-subagent-isolation-and-dag-waves",
            title="Enforce Subagent Context Isolation and Topological DAG Wave Concurrency",
            category="workflow",
            trigger="Exploring >5 unfamiliar files or orchestrating multi-module agent workflows",
            strategy="Isolate broad file exploration inside read-only subagents and execute independent multi-agent tasks in topological parallel waves via `evlop dag run`.",
            anti_pattern="Dumping raw multi-file search outputs into the primary context window or running independent agents sequentially.",
            success_count=3,
            failure_count=0,
            verified_gate=True,
            created_at=now,
            last_used_at=now,
            status="promoted",
            fitness=2.00,
            contributors=["evlop-seed-genome"],
            best_duration_ms=12.0,
        ),
    ]
