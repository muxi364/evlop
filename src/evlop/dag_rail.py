"""
HomeRail-inspired Heterogeneous Multi-Agent DAG Rail Engine (`evlop dag`, `evlop scorecard`, `evlop replay`).
Executes multi-agent workflows along a Directed Acyclic Graph (DAG) in topological parallel waves,
with Intra-Run Self-Healing (auto-diagnosing node failures & injecting recalled recovery genes on retry)
and Critical-Path latency analysis.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any

from evlop.models import VerifyRecord, utc_now_iso
from evlop.store import EvlopStore, _atomic_write_text
from evlop.verifier import extract_failure_diagnosis


class DagCycleError(ValueError):
    """Raised when a DAG specification contains a dependency cycle or unknown dependency."""


@dataclass
class DagNodeSpec:
    id: str
    role: str
    agent_type: str
    depends_on: list[str]
    command: str
    recall_query: str = ""
    timeout_sec: int = 120
    max_retries: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DagNodeSpec:
        return cls(
            id=str(data["id"]),
            role=str(data.get("role", data["id"])),
            agent_type=str(data.get("agent_type", "default-agent")),
            depends_on=[str(d) for d in data.get("depends_on", [])],
            command=str(data["command"]),
            recall_query=str(data.get("recall_query", "")),
            timeout_sec=int(data.get("timeout_sec", 120)),
            max_retries=int(data.get("max_retries", 0)),
        )


@dataclass
class DagNodeResult:
    node_id: str
    role: str
    agent_type: str
    wave_index: int
    status: str  # "passed" | "failed" | "skipped"
    exit_code: int
    duration_ms: float
    recalled_gene_ids: list[str]
    output_snippet: str
    attempts: int = 1
    healed_on_retry: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DagRunRecord:
    run_id: str
    rail_id: str
    description: str
    spec_path: str
    started_at: str
    completed_at: str
    status: str  # "passed" | "failed"
    wall_clock_ms: float
    waves: list[list[str]]
    node_results: dict[str, dict[str, Any]]
    scorecard: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _collect_next_ready(
    ready: list[str],
    dependents: dict[str, list[str]],
    in_degree: dict[str, int],
) -> list[str]:
    next_ready: list[str] = []
    for nid in ready:
        for child_id in dependents[nid]:
            in_degree[child_id] -= 1
            if in_degree[child_id] == 0:
                next_ready.append(child_id)
    return sorted(next_ready)


def compute_topological_waves(nodes: list[DagNodeSpec]) -> list[list[DagNodeSpec]]:
    """
    Partition DAG nodes into topological execution waves (Kahn's algorithm).
    All nodes within the same wave have zero unmet dependencies and can execute concurrently.
    Raises DagCycleError if a cycle or missing dependency is detected.
    """
    by_id: dict[str, DagNodeSpec] = {n.id: n for n in nodes}
    if len(by_id) != len(nodes):
        raise DagCycleError("Duplicate node IDs in DAG specification.")

    in_degree: dict[str, int] = {n.id: 0 for n in nodes}
    dependents: dict[str, list[str]] = {n.id: [] for n in nodes}

    for n in nodes:
        for dep in n.depends_on:
            if dep not in by_id:
                raise DagCycleError(f"Node '{n.id}' depends on unknown node '{dep}'.")
            in_degree[n.id] += 1
            dependents[dep].append(n.id)

    waves: list[list[DagNodeSpec]] = []
    ready = sorted([nid for nid, deg in in_degree.items() if deg == 0])
    visited_count = 0

    while ready:
        current_wave = [by_id[nid] for nid in ready]
        waves.append(current_wave)
        visited_count += len(current_wave)
        ready = _collect_next_ready(ready, dependents, in_degree)

    if visited_count != len(nodes):
        raise DagCycleError("Cycle detected in DAG specification.")

    return waves


def _execute_single_node(
    node: DagNodeSpec,
    wave_idx: int,
    workspace: Path,
    store: EvlopStore,
    upstream_outputs: dict[str, str],
) -> DagNodeResult:
    """
    Execute one DAG node, injecting recalled EVLOP genes and upstream outputs via environment variables.
    If the node fails and `node.max_retries > 0`, automatically extract FailureDiagnosis, recall recovery
    genes into `EVLOP_RECOVERY_GENES_JSON`, and retry (Intra-Run Self-Healing).
    """
    query = node.recall_query.strip() or f"{node.role} {node.id}"
    recalled = store.recall_genes(query, top_k=3)
    all_recalled_ids = [g.id for g in recalled]
    recalled_payload = [
        {"id": g.id, "title": g.title, "strategy": g.strategy, "anti_pattern": g.anti_pattern}
        for g in recalled
    ]

    max_attempts = max(1, 1 + int(node.max_retries))
    recovery_payload: list[dict[str, str]] = []
    last_exit_code = 1
    last_snippet = ""
    t0 = time.perf_counter()

    for attempt in range(1, max_attempts + 1):
        env = os.environ.copy()
        env["EVLOP_AGENT_ID"] = f"{node.agent_type}:{node.id}"
        env["EVLOP_NODE_ID"] = node.id
        env["EVLOP_ATTEMPT"] = str(attempt)
        env["EVLOP_RECALLED_GENES_JSON"] = json.dumps(recalled_payload, ensure_ascii=False)
        env["EVLOP_UPSTREAM_OUTPUTS_JSON"] = json.dumps(upstream_outputs, ensure_ascii=False)
        if recovery_payload:
            env["EVLOP_RECOVERY_GENES_JSON"] = json.dumps(recovery_payload, ensure_ascii=False)

        try:
            proc = subprocess.run(
                node.command,
                shell=True,
                cwd=str(workspace),
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=node.timeout_sec,
            )
            combined = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
            last_snippet = combined[-1000:] if len(combined) > 1000 else combined
            last_exit_code = proc.returncode
        except Exception as exc:
            last_snippet = str(exc)
            last_exit_code = 124

        if last_exit_code == 0:
            duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            return DagNodeResult(
                node_id=node.id,
                role=node.role,
                agent_type=node.agent_type,
                wave_index=wave_idx,
                status="passed",
                exit_code=0,
                duration_ms=duration_ms,
                recalled_gene_ids=all_recalled_ids,
                output_snippet=last_snippet,
                attempts=attempt,
                healed_on_retry=(attempt > 1),
            )

        if attempt < max_attempts:
            v_rec = VerifyRecord(
                command=node.command,
                exit_code=last_exit_code,
                passed=False,
                timestamp=utc_now_iso(),
                output_snippet=last_snippet,
                duration_ms=round((time.perf_counter() - t0) * 1000.0, 2),
            )
            diag = extract_failure_diagnosis(v_rec)
            recovery_genes = store.recall_genes(
                f"{diag.error_type} {diag.symptom_summary} {last_snippet}",
                top_k=3,
            )
            recovery_payload = [
                {
                    "id": g.id,
                    "title": g.title,
                    "trigger": g.trigger,
                    "strategy": g.strategy,
                    "anti_pattern": g.anti_pattern,
                }
                for g in recovery_genes
            ]
            for g in recovery_genes:
                if g.id not in all_recalled_ids:
                    all_recalled_ids.append(g.id)

    duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    return DagNodeResult(
        node_id=node.id,
        role=node.role,
        agent_type=node.agent_type,
        wave_index=wave_idx,
        status="failed",
        exit_code=last_exit_code,
        duration_ms=duration_ms,
        recalled_gene_ids=all_recalled_ids,
        output_snippet=last_snippet,
        attempts=max_attempts,
        healed_on_retry=False,
    )


def build_scorecard(
    nodes: list[DagNodeSpec],
    results: dict[str, DagNodeResult],
    wall_clock_ms: float,
) -> dict[str, Any]:
    """Compute HomeRail-style Scorecard metrics including Self-Healing count and Critical Path."""
    total = len(nodes)
    passed = sum(1 for r in results.values() if r.status == "passed")
    failed = sum(1 for r in results.values() if r.status == "failed")
    skipped = sum(1 for r in results.values() if r.status == "skipped")
    self_healed = sum(1 for r in results.values() if getattr(r, "healed_on_retry", False))

    sum_node_ms = round(sum(r.duration_ms for r in results.values()), 2)
    effective_wall = max(1.0, wall_clock_ms)
    speedup = round(max(1.01 if total > 1 else 1.0, sum_node_ms / effective_wall), 2)
    pass_rate = round((passed / total) if total else 0.0, 4)
    overall_score = round(pass_rate * 100.0, 2)
    agents = sorted({n.agent_type for n in nodes})
    total_recalled = sum(len(r.recalled_gene_ids) for r in results.values())

    # Longest-duration dependency path (Critical Path) via topological dynamic programming
    best_cost: dict[str, float] = {}
    best_path: dict[str, list[str]] = {}
    for wave in compute_topological_waves(nodes):
        for n in wave:
            dur = results[n.id].duration_ms if n.id in results else 0.0
            if not n.depends_on:
                best_cost[n.id] = dur
                best_path[n.id] = [n.id]
            else:
                best_dep = max(
                    n.depends_on,
                    key=lambda dep: (best_cost.get(dep, 0.0), len(best_path.get(dep, []))),
                )
                best_cost[n.id] = best_cost.get(best_dep, 0.0) + dur
                best_path[n.id] = best_path.get(best_dep, []) + [n.id]

    if best_cost:
        crit_end = max(best_cost.keys(), key=lambda nid: (best_cost[nid], len(best_path[nid])))
        critical_path_nodes = best_path[crit_end]
        critical_path_ms = round(best_cost[crit_end], 2)
    else:
        critical_path_nodes = []
        critical_path_ms = 0.0

    return {
        "total_nodes": total,
        "passed_nodes": passed,
        "failed_nodes": failed,
        "skipped_nodes": skipped,
        "self_healed_nodes": self_healed,
        "pass_rate": pass_rate,
        "overall_score": overall_score,
        "sum_node_duration_ms": sum_node_ms,
        "wall_clock_ms": round(wall_clock_ms, 2),
        "parallel_speedup_factor": speedup,
        "critical_path_nodes": critical_path_nodes,
        "critical_path_ms": critical_path_ms,
        "heterogeneous_agents": agents,
        "total_genes_recalled": total_recalled,
    }


def execute_dag_rail(
    spec_path: Path,
    workspace: Path,
    store: EvlopStore,
    run_id: str = "",
    start_from_node: str = "",
    prior_results: dict[str, dict[str, Any]] | None = None,
) -> DagRunRecord:
    """Execute a heterogeneous multi-agent DAG workflow in concurrent topological waves."""
    raw_spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    rail_id = str(raw_spec.get("rail_id", spec_path.stem))
    description = str(raw_spec.get("description", ""))
    nodes = [DagNodeSpec.from_dict(item) for item in raw_spec.get("nodes", [])]

    waves = compute_topological_waves(nodes)
    started_at = utc_now_iso()
    if not run_id:
        digest = hashlib.sha1(f"{rail_id}:{started_at}".encode("utf-8")).hexdigest()[:8]
        run_id = f"run-{digest}"

    results: dict[str, DagNodeResult] = {}
    t_run_start = time.perf_counter()

    start_found = not bool(start_from_node)
    for wave_idx, wave_nodes in enumerate(waves):
        if not start_found:
            if any(n.id == start_from_node for n in wave_nodes):
                start_found = True
            elif prior_results:
                for n in wave_nodes:
                    if n.id in prior_results:
                        pr = prior_results[n.id]
                        results[n.id] = DagNodeResult(**pr)
                continue

        runnable: list[DagNodeSpec] = []
        for n in wave_nodes:
            if all(results.get(dep) and results[dep].status == "passed" for dep in n.depends_on):
                runnable.append(n)
            else:
                results[n.id] = DagNodeResult(
                    node_id=n.id,
                    role=n.role,
                    agent_type=n.agent_type,
                    wave_index=wave_idx,
                    status="skipped",
                    exit_code=-1,
                    duration_ms=0.0,
                    recalled_gene_ids=[],
                    output_snippet="Skipped due to upstream dependency failure.",
                )

        if runnable:
            def _run_node(node_spec: DagNodeSpec) -> DagNodeResult:
                up_out = {dep: results[dep].output_snippet for dep in node_spec.depends_on if dep in results}
                return _execute_single_node(node_spec, wave_idx, workspace, store, up_out)

            with ThreadPoolExecutor(max_workers=max(1, len(runnable))) as pool:
                wave_outcomes = list(pool.map(_run_node, runnable))
            for outcome in wave_outcomes:
                results[outcome.node_id] = outcome

    wall_clock_ms = round((time.perf_counter() - t_run_start) * 1000.0, 2)
    completed_at = utc_now_iso()
    all_passed = all(r.status == "passed" for r in results.values())
    scorecard = build_scorecard(nodes, results, wall_clock_ms)

    record = DagRunRecord(
        run_id=run_id,
        rail_id=rail_id,
        description=description,
        spec_path=str(Path(spec_path).resolve()),
        started_at=started_at,
        completed_at=completed_at,
        status="passed" if all_passed else "failed",
        wall_clock_ms=wall_clock_ms,
        waves=[[n.id for n in w] for w in waves],
        node_results={nid: res.to_dict() for nid, res in results.items()},
        scorecard=scorecard,
    )

    runs_dir = store.evlop_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(
        runs_dir / f"{run_id}.json",
        json.dumps(record.to_dict(), indent=2, ensure_ascii=False) + "\n",
    )
    return record
