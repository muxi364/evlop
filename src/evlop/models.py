"""Core data structures for EVLOP episodes, genes, verification records, and configuration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import re
from typing import Any


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def slugify_gene_id(title: str) -> str:
    """Generate a deterministic human-readable slug ID for a gene."""
    ascii_part = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if len(ascii_part) >= 6:
        return f"gene-{ascii_part[:42].strip('-')}"
    digest = hashlib.sha1(title.encode("utf-8")).hexdigest()[:8]
    prefix = f"{ascii_part}-" if ascii_part else ""
    return f"gene-{prefix}{digest}"


@dataclass
class EvlopConfig:
    max_active_genes: int = 15
    promote_threshold: float = 1.15
    prune_threshold: float = 0.35
    half_life_days: float = 30.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvlopConfig:
        return cls(
            max_active_genes=int(data.get("max_active_genes", 15)),
            promote_threshold=float(data.get("promote_threshold", 1.15)),
            prune_threshold=float(data.get("prune_threshold", 0.35)),
            half_life_days=float(data.get("half_life_days", 30.0)),
        )


@dataclass
class VerifyRecord:
    command: str
    exit_code: int
    passed: bool
    timestamp: str
    output_snippet: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VerifyRecord:
        return cls(
            command=str(data.get("command", "")),
            exit_code=int(data.get("exit_code", -1)),
            passed=bool(data.get("passed", False)),
            timestamp=str(data.get("timestamp", "")),
            output_snippet=str(data.get("output_snippet", "")),
        )


@dataclass
class Episode:
    episode_id: str
    timestamp: str
    task_summary: str
    failure_symptom: str
    root_cause: str
    fix_applied: str
    verified: bool
    verify_cmd: str
    gene_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Episode:
        return cls(
            episode_id=str(data.get("episode_id", "")),
            timestamp=str(data.get("timestamp", "")),
            task_summary=str(data.get("task_summary", "")),
            failure_symptom=str(data.get("failure_symptom", "")),
            root_cause=str(data.get("root_cause", "")),
            fix_applied=str(data.get("fix_applied", "")),
            verified=bool(data.get("verified", False)),
            verify_cmd=str(data.get("verify_cmd", "")),
            gene_id=str(data.get("gene_id", "")),
        )


@dataclass
class Gene:
    id: str
    title: str
    category: str
    trigger: str
    strategy: str
    anti_pattern: str
    success_count: int = 1
    failure_count: int = 0
    verified_gate: bool = False
    created_at: str = ""
    last_used_at: str = ""
    status: str = "candidate"
    fitness: float = 0.0

    def __post_init__(self) -> None:
        now = utc_now_iso()
        if not self.created_at:
            self.created_at = now
        if not self.last_used_at:
            self.last_used_at = self.created_at

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Gene:
        return cls(
            id=str(data.get("id", "")),
            title=str(data.get("title", "")),
            category=str(data.get("category", "workflow")),
            trigger=str(data.get("trigger", "")),
            strategy=str(data.get("strategy", "")),
            anti_pattern=str(data.get("anti_pattern", "")),
            success_count=int(data.get("success_count", 1)),
            failure_count=int(data.get("failure_count", 0)),
            verified_gate=bool(data.get("verified_gate", False)),
            created_at=str(data.get("created_at", "")),
            last_used_at=str(data.get("last_used_at", "")),
            status=str(data.get("status", "candidate")),
            fitness=float(data.get("fitness", 0.0)),
        )
