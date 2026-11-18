"""
Scenario 3: O(V+E) Priority DAG Scheduler & Critical-Path Analyzer.

Provides `DagTaskScheduler` to partition tasks into topological execution waves
ordered by `(-priority, id)`, detect cycles or missing dependencies, and compute
the exact critical path (`critical_path_ids` and `critical_path_ms`) in O(V+E)
time via single-pass topological dynamic programming.
"""

from __future__ import annotations

from typing import Any


def _register_task_edges(
    tid: str,
    raw_deps: list[str],
    known_ids: set[str],
    in_degree: dict[str, int],
    dependents: dict[str, list[str]],
    deps_map: dict[str, list[str]],
) -> None:
    """Register dependency edges for a single task and validate upstream targets."""
    seen_local: set[str] = set()
    clean_deps: list[str] = []
    for dep_raw in raw_deps:
        dep = str(dep_raw)
        if dep not in known_ids:
            raise ValueError(f"Task '{tid}' depends on unknown task '{dep}'.")
        if dep == tid:
            raise ValueError(f"Cycle detected: task '{tid}' depends on itself.")
        if dep not in seen_local:
            seen_local.add(dep)
            clean_deps.append(dep)
            in_degree[tid] += 1
            dependents[dep].append(tid)
    deps_map[tid] = clean_deps


def _advance_wave_frontier(
    current_wave: list[str],
    dependents: dict[str, list[str]],
    in_degree: dict[str, int],
    priority_map: dict[str, int],
) -> list[str]:
    """Decrement in-degrees for downstream dependents and return next sorted wave."""
    next_ready: list[str] = []
    for uid in current_wave:
        for vid in dependents[uid]:
            in_degree[vid] -= 1
            if in_degree[vid] == 0:
                next_ready.append(vid)
    next_ready.sort(key=lambda tid: (-priority_map[tid], tid))
    return next_ready


def _select_critical_predecessor(
    deps: list[str],
    earliest_finish: dict[str, float],
    path_len: dict[str, int],
    priority_map: dict[str, int],
) -> str:
    """Pick the upstream dependency that maximizes earliest finish time."""
    return max(
        deps,
        key=lambda dep: (
            earliest_finish[dep],
            path_len[dep],
            priority_map[dep],
            dep,
        ),
    )


def _reconstruct_critical_path(
    end_tid: str,
    predecessor: dict[str, str | None],
) -> list[str]:
    """Walk predecessor links backward from the terminal critical task in O(V)."""
    chain: list[str] = []
    cursor: str | None = end_tid
    while cursor is not None:
        chain.append(cursor)
        cursor = predecessor[cursor]
    chain.reverse()
    return chain


class DagTaskScheduler:
    """O(V+E) Kahn topological wave scheduler and forward-DP critical-path analyzer."""

    def schedule_waves_and_critical_path(
        self,
        tasks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Compute priority-ordered topological execution waves and exact critical path.

        Each task dict must contain:
          - `id` (str)
          - `duration_ms` (int | float, non-negative)
          - `priority` (int, higher runs earlier within a wave)
          - `depends_on` (list[str])

        Raises ValueError on duplicate IDs, negative durations, missing dependencies,
        or dependency cycles.
        """
        if not tasks:
            return {
                "waves": [],
                "wave_count": 0,
                "total_tasks": 0,
                "critical_path_ids": [],
                "critical_path_ms": 0.0,
                "earliest_start_ms": {},
                "earliest_finish_ms": {},
            }

        duration_map: dict[str, float] = {}
        priority_map: dict[str, int] = {}
        raw_deps_by_id: dict[str, list[str]] = {}
        in_degree: dict[str, int] = {}
        dependents: dict[str, list[str]] = {}
        deps_map: dict[str, list[str]] = {}

        for item in tasks:
            tid = str(item["id"])
            if tid in duration_map:
                raise ValueError(f"Duplicate task ID '{tid}' in task specification.")
            dur = float(item.get("duration_ms", 0.0))
            if dur < 0.0:
                raise ValueError(f"Task '{tid}' has negative duration_ms ({dur}).")
            prio = int(item.get("priority", 0))
            raw_deps = list(item.get("depends_on", []))

            duration_map[tid] = dur
            priority_map[tid] = prio
            raw_deps_by_id[tid] = raw_deps
            in_degree[tid] = 0
            dependents[tid] = []

        known_ids = set(duration_map.keys())
        for tid, raw_deps in raw_deps_by_id.items():
            _register_task_edges(
                tid=tid,
                raw_deps=raw_deps,
                known_ids=known_ids,
                in_degree=in_degree,
                dependents=dependents,
                deps_map=deps_map,
            )

        ready = [tid for tid, deg in in_degree.items() if deg == 0]
        ready.sort(key=lambda tid: (-priority_map[tid], tid))

        waves: list[list[str]] = []
        earliest_start: dict[str, float] = {}
        earliest_finish: dict[str, float] = {}
        predecessor: dict[str, str | None] = {}
        path_len: dict[str, int] = {}
        visited_count = 0

        while ready:
            waves.append(ready)
            visited_count += len(ready)
            for uid in ready:
                deps = deps_map[uid]
                dur = duration_map[uid]
                if not deps:
                    earliest_start[uid] = 0.0
                    earliest_finish[uid] = dur
                    predecessor[uid] = None
                    path_len[uid] = 1
                else:
                    best_dep = _select_critical_predecessor(
                        deps, earliest_finish, path_len, priority_map
                    )
                    start_ms = earliest_finish[best_dep]
                    earliest_start[uid] = start_ms
                    earliest_finish[uid] = start_ms + dur
                    predecessor[uid] = best_dep
                    path_len[uid] = path_len[best_dep] + 1

            ready = _advance_wave_frontier(ready, dependents, in_degree, priority_map)

        if visited_count != len(duration_map):
            raise ValueError("Cycle detected in task dependency graph.")

        crit_end = max(
            known_ids,
            key=lambda tid: (
                earliest_finish[tid],
                path_len[tid],
                priority_map[tid],
                tid,
            ),
        )
        critical_path_ids = _reconstruct_critical_path(crit_end, predecessor)
        critical_path_ms = round(earliest_finish[crit_end], 4)

        return {
            "waves": waves,
            "wave_count": len(waves),
            "total_tasks": len(duration_map),
            "critical_path_ids": critical_path_ids,
            "critical_path_ms": critical_path_ms,
            "earliest_start_ms": earliest_start,
            "earliest_finish_ms": earliest_finish,
        }


def schedule_waves_and_critical_path(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Module-level convenience wrapper around `DagTaskScheduler`."""
    return DagTaskScheduler().schedule_waves_and_critical_path(tasks)
