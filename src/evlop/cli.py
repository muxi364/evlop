"""CLI entrypoint for EVLOP v3.0: init, recall, verify, log, mutate, lineage, evolve, export-skill, dag, scorecard, replay, status, mcp."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

from evlop.bootstrap import bootstrap_workspace
from evlop.compiler import export_gene_to_skill, inject_markdown_file, render_lineage_mermaid
from evlop.dag_rail import DagCycleError, execute_dag_rail
from evlop.fitness import govern_genes
from evlop.models import Episode, Gene, slugify_gene_id, utc_now_iso
from evlop.quality_gate import audit_python_path
from evlop.rsi_pareto import run_rsi_scaffold_evolution
from evlop.store import EvlopStore
from evlop.verifier import extract_failure_diagnosis, run_verification


def _safe_print(text: str, file=None) -> None:
    """Print text safely even if the target console stream uses strict legacy encoding (e.g. Windows gbk)."""
    stream = file if file is not None else sys.stdout
    try:
        print(text, file=stream)
    except UnicodeEncodeError:
        enc = getattr(stream, "encoding", None) or "utf-8"
        safe_text = text.encode(enc, errors="replace").decode(enc, errors="replace")
        print(safe_text, file=stream)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evlop",
        description="EVLOP v3.0: Heterogeneous Multi-Agent DAG Rail & Darwinian Self-Evolution Engine",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p_init = sub.add_parser("init", help="Initialize .evlop/ workspace store and optional full agent bootstrap")
    p_init.add_argument("--target-dir", default=".", help="Workspace directory")
    p_init.add_argument(
        "--bootstrap",
        action="store_true",
        help="Vendor standalone .evlop/evlop_runner.py and create AGENTS.md, CLAUDE.md, and .cursorrules",
    )
    p_init.add_argument(
        "--with-hooks",
        action="store_true",
        help="Also generate .claude/settings.json automatic SessionStart and Stop evolution hooks",
    )

    p_recall = sub.add_parser("recall", help="[Stage E] Recall relevant evolved genes before acting")
    p_recall.add_argument("query", help="Search keywords, error message, or '*' for top genes")
    p_recall.add_argument("--top", type=int, default=5, help="Max genes to return")

    p_verify = sub.add_parser("verify", help="[Stage V] Run deterministic verification command gate")
    p_verify.add_argument("command", help="Shell command to execute (e.g. pytest, npm test)")
    p_verify.add_argument("--timeout", type=int, default=120, help="Timeout in seconds")
    p_verify.add_argument(
        "--quality-gate",
        default="",
        help="Optional Python file or directory path to enforce AST code quality & complexity gate (>= min-quality-score)",
    )
    p_verify.add_argument(
        "--min-quality-score",
        type=float,
        default=90.0,
        help="Minimum AST quality score required when --quality-gate is enabled (default 90.0)",
    )
    p_verify.add_argument(
        "--auto-evolve",
        action="store_true",
        help="Automatically distill and promote a gene into AGENTS.md/CLAUDE.md when transitioning from FAILED to PASSED",
    )
    p_verify.add_argument(
        "--agent-id",
        default="",
        help="Swarm agent identifier for isolated per-agent verification state",
    )

    p_audit = sub.add_parser(
        "audit",
        help="[Stage V+] Run deterministic AST code quality & O(N^2) complexity auditor on Python files",
    )
    p_audit.add_argument("path", default=".", nargs="?", help="Python file or directory to audit")
    p_audit.add_argument("--min-score", type=float, default=90.0, help="Minimum passing score (0..100)")
    p_audit.add_argument("--json", action="store_true", help="Output audit report as JSON")

    p_log = sub.add_parser("log", help="[Stage L] Record an episode and create/reinforce a gene")
    p_log.add_argument("--title", default="", help="Short imperative rule title")
    p_log.add_argument("--task", required=True, help="Summary of the task being solved")
    p_log.add_argument("--symptom", default="", help="Failure symptom or problem encountered")
    p_log.add_argument(
        "--from-last-failure",
        action="store_true",
        help="Auto-populate symptom and trigger from .evlop/last_failure.json",
    )
    p_log.add_argument("--root-cause", required=True, help="Diagnosed root cause")
    p_log.add_argument("--fix", required=True, help="Fix applied")
    p_log.add_argument(
        "--category",
        default="debugging",
        choices=["debugging", "architecture", "testing", "tooling", "workflow"],
        help="Gene category",
    )
    p_log.add_argument("--trigger", default="", help="Trigger condition for activating the gene")
    p_log.add_argument("--strategy", default="", help="Reusable actionable strategy")
    p_log.add_argument("--anti-pattern", default="Blindly guessing without verification", help="What to avoid")
    p_log.add_argument("--agent-id", default="", help="Swarm agent identifier (or EVLOP_AGENT_ID env)")
    p_log.add_argument("--failed", action="store_true", help="Mark that applying this strategy failed")

    p_mutate = sub.add_parser(
        "mutate",
        help="[Stage O - DGM Mode] Evolve a child gene mutation from an existing parent gene",
    )
    p_mutate.add_argument("--parent-id", required=True, help="Parent gene ID to mutate from")
    p_mutate.add_argument("--title", required=True, help="New mutated gene title")
    p_mutate.add_argument("--strategy", required=True, help="Mutated strategy")
    p_mutate.add_argument("--reason", default="Empirical refinement", help="Reason for mutation")
    p_mutate.add_argument("--trigger", default="", help="Optional updated trigger (defaults to parent trigger)")
    p_mutate.add_argument("--agent-id", default="", help="Swarm agent identifier")

    p_lineage = sub.add_parser(
        "lineage",
        help="[Stage O - DGM Archive] Inspect or export the phylogenetic evolution tree of genes",
    )
    p_lineage.add_argument("--mermaid", action="store_true", help="Render as Mermaid flowchart")
    p_lineage.add_argument("--out", default="", help="Optional file path to write lineage output")

    p_evolve = sub.add_parser(
        "evolve",
        help="[Stages O & P] Govern genome (merge/score/prune) and compile top genes into AGENTS.md/CLAUDE.md",
    )
    p_evolve.add_argument(
        "--target",
        default="AGENTS.md,CLAUDE.md",
        help="Comma-separated markdown files to update with promoted genes",
    )

    p_skill = sub.add_parser(
        "export-skill",
        help="[Stage P - Voyager Mode] Export a verified gene into a standalone SKILL.md directory",
    )
    p_skill.add_argument("--gene-id", required=True, help="ID of the gene to export")
    p_skill.add_argument("--out-dir", default="skills", help="Output skills directory")
    p_skill.add_argument(
        "--synthesize-script",
        action="store_true",
        help="Also synthesize an executable Python tool script under scripts/run_strategy.py",
    )

    # HomeRail Heterogeneous Multi-Agent DAG Rail Commands
    p_dag = sub.add_parser(
        "dag",
        help="[HomeRail Mode] Run or supervise a heterogeneous multi-agent DAG workflow in parallel waves",
    )
    p_dag.add_argument("action", choices=["run", "supervise"], help="DAG action")
    p_dag.add_argument("spec", help="Path to DAG specification JSON file")
    p_dag.add_argument("--run-id", default="", help="Optional explicit run identifier")

    p_scorecard = sub.add_parser(
        "scorecard",
        help="[HomeRail Mode] Inspect evaluation scorecard for a completed DAG run",
    )
    p_scorecard.add_argument("run_id", help="DAG run ID")
    p_scorecard.add_argument("--json", action="store_true", help="Output scorecard as JSON")

    p_replay = sub.add_parser(
        "replay",
        help="[HomeRail Mode] Replay or audit a previous DAG run (optionally starting from a specific node)",
    )
    p_replay.add_argument("run_id", help="DAG run ID to replay")
    p_replay.add_argument("--from-node", default="", help="Node ID to resume execution from")

    p_status = sub.add_parser("status", help="Inspect EVLOP genome health, swarm contributors, and lineage depth")
    p_status.add_argument("--json", action="store_true", help="Output status as JSON")

    p_rsi = sub.add_parser(
        "rsi",
        help="[RSI + Pareto Mode] Run Recursive Scaffold Self-Improvement to evolve the 3D Pareto Frontier (Quality x Latency x Cost)",
    )
    p_rsi.add_argument("--generations", type=int, default=3, help="Number of RSI generations to evolve")
    p_rsi.add_argument(
        "--mode",
        default="balanced",
        choices=["heavy", "balanced", "lite"],
        help="HarnessPro operating mode selection on the Pareto Frontier",
    )
    p_rsi.add_argument("--out", default="", help="Optional path to write JSON Pareto report")

    sub.add_parser("mcp", help="Run zero-dependency MCP JSON-RPC 2.0 server over stdio")

    return parser


def main(argv: list[str] | None = None, root_dir: Path | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    workspace = Path(root_dir).resolve() if root_dir else Path.cwd().resolve()

    if args.subcommand == "init":
        target = (workspace / args.target_dir).resolve() if not root_dir else workspace
        store = EvlopStore(target)
        evlop_path = store.init_store()
        cfg = store.load_config()
        if args.bootstrap or args.with_hooks:
            created = bootstrap_workspace(
                target,
                store.load_genes(),
                max_genes=cfg.max_active_genes,
                with_hooks=args.with_hooks,
            )
            _safe_print(
                f"[EVLOP Bootstrap] Initialized {evlop_path} and bootstrapped {len(created)} agent protocol files."
            )
        else:
            _safe_print(f"[EVLOP] Initialized self-evolution store at {evlop_path}")
        return 0

    store = EvlopStore(workspace)
    store.init_store()
    cfg = store.load_config()

    if args.subcommand == "mcp":
        from evlop.mcp_server import run_stdio_server

        return run_stdio_server(workspace)

    if args.subcommand == "rsi":
        report = run_rsi_scaffold_evolution(
            workspace=workspace,
            generations=args.generations,
            mode=args.mode,
        )
        if args.out:
            out_p = Path(args.out)
            if not out_p.is_absolute():
                out_p = (workspace / out_p).resolve()
            out_p.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        sel = report["selected_pareto_optimal"]
        hv_hist = report["hypervolume_history"]
        _safe_print(
            f"[EVLOP RSI Pareto-Optimal] Generations: {args.generations} | "
            f"Hypervolume: {hv_hist[0]:.2f} -> {hv_hist[-1]:.2f} (+{report['hypervolume_gain_pct']}%) | "
            f"Selected ({args.mode.upper()}): {sel['title']} "
            f"[Quality={sel['quality']}%, Latency={sel['latency_ms']}ms, Cost={sel['cost_tokens']} tok]"
        )
        return 0

    if args.subcommand == "dag":
        spec_path = Path(args.spec)
        if not spec_path.is_absolute():
            spec_path = (workspace / spec_path).resolve()
        try:
            record = execute_dag_rail(spec_path, workspace=workspace, store=store, run_id=args.run_id)
        except (DagCycleError, FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
            _safe_print(f"[EVLOP DAG Error] {exc}", file=sys.stderr)
            return 1

        sc = record.scorecard
        _safe_print(
            f"[EVLOP DAG {record.status.upper()}] Run: {record.run_id} | Rail: {record.rail_id} | "
            f"Waves: {len(record.waves)} | Score: {sc['overall_score']}% | "
            f"Speedup: {sc['parallel_speedup_factor']}x | Agents: {', '.join(sc['heterogeneous_agents'])}"
        )
        return 0 if record.status == "passed" else 1

    if args.subcommand == "scorecard":
        run_file = store.evlop_dir / "runs" / f"{args.run_id}.json"
        if not run_file.exists():
            _safe_print(f"[EVLOP Error] Run '{args.run_id}' not found.", file=sys.stderr)
            return 1
        data = json.loads(run_file.read_text(encoding="utf-8"))
        sc = data.get("scorecard", {})
        if args.json:
            _safe_print(json.dumps(sc, indent=2, ensure_ascii=False))
        else:
            _safe_print(
                f"[EVLOP Scorecard] Run: {args.run_id} ({data.get('rail_id')})\n"
                f"  Overall Score : {sc.get('overall_score')}% ({sc.get('passed_nodes')}/{sc.get('total_nodes')} nodes passed)\n"
                f"  Speedup Factor: {sc.get('parallel_speedup_factor')}x (Wall: {sc.get('wall_clock_ms')}ms)\n"
                f"  Agent Mix     : {', '.join(sc.get('heterogeneous_agents', []))}\n"
                f"  Genes Recalled: {sc.get('total_genes_recalled', 0)}"
            )
        return 0

    if args.subcommand == "replay":
        run_file = store.evlop_dir / "runs" / f"{args.run_id}.json"
        if not run_file.exists():
            _safe_print(f"[EVLOP Error] Run '{args.run_id}' not found.", file=sys.stderr)
            return 1
        prior_data = json.loads(run_file.read_text(encoding="utf-8"))
        spec_path = Path(prior_data["spec_path"])
        record = execute_dag_rail(
            spec_path,
            workspace=workspace,
            store=store,
            run_id=f"{args.run_id}-replay",
            start_from_node=args.from_node,
            prior_results=prior_data.get("node_results", {}),
        )
        _safe_print(
            f"[EVLOP Replay {record.status.upper()}] Replayed '{args.run_id}' -> '{record.run_id}' "
            f"(Score: {record.scorecard['overall_score']}%)"
        )
        return 0 if record.status == "passed" else 1

    if args.subcommand == "recall":
        matches = store.recall_genes(args.query, top_k=args.top)
        if not matches:
            _safe_print(f"[EVLOP Recall] No matching genes found for '{args.query}'.")
            return 0
        _safe_print(f"[EVLOP Recall] Top {len(matches)} matching gene(s):")
        for g in matches:
            _safe_print(
                f"  - [{g.status.upper()}] {g.id} (gen={g.generation}, fitness={g.fitness:.2f}): {g.title}\n"
                f"    Trigger : {g.trigger}\n"
                f"    Strategy: {g.strategy}"
            )
        return 0

    if args.subcommand == "audit":
        target_p = Path(args.path)
        if not target_p.is_absolute():
            target_p = (workspace / target_p).resolve()
        q_report = audit_python_path(target_p, min_score=args.min_score)
        if args.json:
            _safe_print(json.dumps(q_report.to_dict(), indent=2, ensure_ascii=False))
        else:
            status_tag = "PASSED" if q_report.passed else "FAILED"
            _safe_print(
                f"[EVLOP AST Audit {status_tag}] Score: {q_report.score}/100.0 "
                f"(Min: {q_report.min_score} | Scanned: {q_report.files_scanned} file(s) | Findings: {len(q_report.findings)})"
            )
            for f in q_report.findings:
                _safe_print(f"  - [{f.severity.upper()}] {f.file}:{f.line} ({f.rule_id}, -{f.penalty}): {f.message}")
        return 0 if q_report.passed else 1

    if args.subcommand == "verify":
        record = run_verification(args.command, cwd=workspace, timeout_sec=args.timeout)
        if record.passed and args.quality_gate:
            qg_path = Path(args.quality_gate)
            if not qg_path.is_absolute():
                qg_path = (workspace / qg_path).resolve()
            q_rep = audit_python_path(qg_path, min_score=args.min_quality_score)
            if not q_rep.passed:
                record.passed = False
                record.exit_code = 2
                findings_txt = "; ".join(f"{f.file}:{f.line} {f.rule_id}" for f in q_rep.findings)
                record.output_snippet = (
                    f"{record.output_snippet}\n[EVLOP Quality Gate FAILED] AST Score {q_rep.score} < {q_rep.min_score}: {findings_txt}"
                ).strip()
        v_agent_id = args.agent_id.strip() or os.environ.get("EVLOP_AGENT_ID", "default-agent")
        with store.lock():
            store.save_verify(record, agent_id=v_agent_id)
            status_str = "PASSED" if record.passed else f"FAILED (exit={record.exit_code})"
            _safe_print(f"[EVLOP Verify] {status_str} ({record.duration_ms:.1f}ms) -> {record.command}")
            if record.output_snippet:
                _safe_print(record.output_snippet)
            if not record.passed:
                diag = extract_failure_diagnosis(record)
                store.save_failure(diag, agent_id=v_agent_id)
                hints = store.recall_genes(f"{diag.error_type} {diag.symptom_summary}", top_k=3)
                if hints:
                    _safe_print(f"\n[EVLOP Auto-Recall Hint] Found {len(hints)} matching gene(s) for {diag.error_type}:")
                    for h in hints:
                        _safe_print(f"  * {h.title} ({h.id}): {h.strategy}")
            elif args.auto_evolve:
                prior_fail = store.load_last_failure(agent_id=v_agent_id)
                if prior_fail is not None:
                    now_iso = utc_now_iso()
                    agent_id = os.environ.get("EVLOP_AGENT_ID", "auto-evolve-agent")
                    auto_title = f"Resolve {prior_fail.error_type} in verification gate"
                    gene_id = slugify_gene_id(auto_title)
                    ep_hash = hashlib.sha1(f"{now_iso}:{gene_id}".encode("utf-8")).hexdigest()[:10]
                    ep = Episode(
                        episode_id=f"ep-{ep_hash}",
                        timestamp=now_iso,
                        task_summary=f"Auto-evolved RED->GREEN fix for {prior_fail.error_type}",
                        failure_symptom=f"{prior_fail.error_type}: {prior_fail.symptom_summary}",
                        root_cause=prior_fail.symptom_summary,
                        fix_applied=f"Verified passing command: {record.command}",
                        verified=True,
                        verify_cmd=record.command,
                        gene_id=gene_id,
                        agent_id=agent_id,
                    )
                    store.append_episode(ep)
                    genes = store.load_genes()
                    genes.append(
                        Gene(
                            id=gene_id,
                            title=auto_title,
                            category="debugging",
                            trigger=f"{prior_fail.error_type} {prior_fail.symptom_summary}",
                            strategy=f"Guard against `{prior_fail.error_type}` ({prior_fail.symptom_summary}) and verify with `{record.command}`",
                            anti_pattern=f"Unchecked condition causing {prior_fail.error_type}",
                            success_count=1,
                            failure_count=0,
                            verified_gate=True,
                            created_at=now_iso,
                            last_used_at=now_iso,
                            contributors=[agent_id],
                            best_duration_ms=record.duration_ms,
                        )
                    )
                    governed = govern_genes(genes, cfg)
                    store.save_genes(governed)
                    for target_doc in ("AGENTS.md", "CLAUDE.md"):
                        inject_markdown_file(workspace / target_doc, governed, max_genes=cfg.max_active_genes)
                    try:
                        store.failure_file.unlink()
                    except OSError:
                        pass
                    _safe_print(
                        f"[EVLOP Auto-Evolve] RED->GREEN transition detected! Automatically promoted gene '{gene_id}' into AGENTS.md & CLAUDE.md."
                    )
        return 0 if record.passed else (record.exit_code or 1)

    if args.subcommand == "log":
        with store.lock():
            agent_id = args.agent_id.strip() or os.environ.get("EVLOP_AGENT_ID", "default-agent")
            last_v = store.load_last_verify(agent_id=agent_id)
            is_verified = bool(
                store.is_verify_fresh(last_v, ttl_minutes=cfg.verify_ttl_minutes)
                and not args.failed
            )
            verify_cmd = last_v.command if last_v else ""

            symptom = args.symptom.strip()
            trigger = args.trigger.strip()
            if args.from_last_failure:
                last_fail = store.load_last_failure(agent_id=agent_id)
                if last_fail:
                    if not symptom:
                        symptom = f"{last_fail.error_type}: {last_fail.symptom_summary}"
                    if not trigger:
                        trigger = f"{last_fail.error_type} {last_fail.symptom_summary}"
            if not symptom:
                symptom = args.task.strip()

            title = args.title.strip() or args.fix.strip()[:60]
            gene_id = slugify_gene_id(title)
            now_iso = utc_now_iso()
            ep_hash = hashlib.sha1(f"{now_iso}:{args.task}:{gene_id}:{agent_id}".encode("utf-8")).hexdigest()[:10]

            episode = Episode(
                episode_id=f"ep-{ep_hash}",
                timestamp=now_iso,
                task_summary=args.task,
                failure_symptom=symptom,
                root_cause=args.root_cause,
                fix_applied=args.fix,
                verified=is_verified,
                verify_cmd=verify_cmd,
                gene_id=gene_id,
                agent_id=agent_id,
            )
            store.append_episode(episode)

            genes = store.load_genes()
            new_gene = Gene(
                id=gene_id,
                title=title,
                category=args.category,
                trigger=trigger or symptom,
                strategy=args.strategy.strip() or args.fix.strip(),
                anti_pattern=args.anti_pattern.strip(),
                success_count=1 if is_verified else 0,
                failure_count=1 if args.failed else 0,
                verified_gate=is_verified,
                created_at=now_iso,
                last_used_at=now_iso,
                contributors=[agent_id],
                best_duration_ms=last_v.duration_ms if (is_verified and last_v) else 0.0,
            )
            genes.append(new_gene)
            governed = govern_genes(genes, cfg)
            store.save_genes(governed)
        _safe_print(
            f"[EVLOP Log] Recorded episode {episode.episode_id} (agent={agent_id}) -> gene {gene_id} (verified={is_verified})"
        )
        return 0

    if args.subcommand == "mutate":
        with store.lock():
            genes = store.load_genes()
            by_id = {g.id: g for g in genes}
            if args.parent_id not in by_id:
                _safe_print(f"[EVLOP Error] Parent gene '{args.parent_id}' not found.", file=sys.stderr)
                return 1
            parent = by_id[args.parent_id]
            last_v = store.load_last_verify()
            is_verified = store.is_verify_fresh(last_v, ttl_minutes=cfg.verify_ttl_minutes)
            agent_id = args.agent_id.strip() or os.environ.get("EVLOP_AGENT_ID", "default-agent")
            now_iso = utc_now_iso()
            child_id = slugify_gene_id(args.title.strip())
            if child_id == parent.id:
                suffix = hashlib.sha1(f"{args.title}:{args.strategy}".encode("utf-8")).hexdigest()[:6]
                child_id = f"{child_id}-gen{parent.generation + 1}-{suffix}"

            child_gene = Gene(
                id=child_id,
                title=args.title.strip(),
                category=parent.category,
                trigger=args.trigger.strip() or parent.trigger,
                strategy=args.strategy.strip(),
                anti_pattern=parent.anti_pattern,
                success_count=1 if is_verified else 0,
                failure_count=0,
                verified_gate=is_verified,
                created_at=now_iso,
                last_used_at=now_iso,
                parent_id=parent.id,
                generation=parent.generation + 1,
                mutation_reason=args.reason.strip(),
                contributors=sorted(set(parent.contributors) | {agent_id}),
                best_duration_ms=last_v.duration_ms if (is_verified and last_v) else 0.0,
            )
            genes.append(child_gene)
            governed = govern_genes(genes, cfg)
            store.save_genes(governed)
        _safe_print(
            f"[EVLOP Mutate] Evolved Gen-{child_gene.generation} gene '{child_gene.id}' from '{parent.id}'"
        )
        return 0

    if args.subcommand == "lineage":
        genes = govern_genes(store.load_genes(), cfg)
        output = render_lineage_mermaid(genes)
        if args.out:
            out_path = workspace / args.out
            out_path.write_text(output, encoding="utf-8")
            _safe_print(f"[EVLOP Lineage] Wrote phylogenetic tree to {out_path}")
        else:
            _safe_print(output)
        return 0

    if args.subcommand == "evolve":
        with store.lock():
            genes = store.load_genes()
            governed = govern_genes(genes, cfg)
            store.save_genes(governed)

            targets = [t.strip() for t in args.target.split(",") if t.strip()]
            for rel_target in targets:
                target_path = workspace / rel_target
                inject_markdown_file(target_path, governed, max_genes=cfg.max_active_genes)

        promoted_cnt = sum(1 for g in governed if g.status == "promoted")
        archived_cnt = sum(1 for g in governed if g.status == "archived")
        _safe_print(
            f"[EVLOP Evolve] Governed {len(governed)} genes "
            f"(promoted={promoted_cnt}, archived={archived_cnt}) -> updated {', '.join(targets)}"
        )
        return 0

    if args.subcommand == "export-skill":
        genes = {g.id: g for g in store.load_genes()}
        if args.gene_id not in genes:
            _safe_print(f"[EVLOP Error] Gene '{args.gene_id}' not found.", file=sys.stderr)
            return 1
        target_gene = genes[args.gene_id]
        if not target_gene.verified_gate or target_gene.status == "archived":
            _safe_print(
                f"[EVLOP Error] Refusing to export unverified or archived gene '{args.gene_id}'.",
                file=sys.stderr,
            )
            return 1
        out_root = workspace / args.out_dir
        skill_path = export_gene_to_skill(
            target_gene,
            out_root,
            synthesize_script=args.synthesize_script,
        )
        _safe_print(f"[EVLOP Export-Skill] Created {skill_path}")
        return 0

    if args.subcommand == "status":
        genes = govern_genes(store.load_genes(), cfg)
        episodes = store.load_episodes()
        last_v = store.load_last_verify()
        all_agents = sorted({c for g in genes for c in g.contributors})
        max_gen = max((g.generation for g in genes), default=0)
        summary = {
            "total_episodes": len(episodes),
            "total_genes": len(genes),
            "promoted_genes": sum(1 for g in genes if g.status == "promoted"),
            "candidate_genes": sum(1 for g in genes if g.status == "candidate"),
            "archived_genes": sum(1 for g in genes if g.status == "archived"),
            "max_generation": max_gen,
            "swarm_contributors": all_agents,
            "last_verify": last_v.to_dict() if last_v else None,
            "top_genes": [g.to_dict() for g in genes[:5]],
        }
        if args.json:
            _safe_print(json.dumps(summary, indent=2, ensure_ascii=False))
        else:
            _safe_print(
                f"[EVLOP Status] Episodes: {summary['total_episodes']} | "
                f"Genes: {summary['total_genes']} "
                f"(Promoted: {summary['promoted_genes']}, "
                f"Candidate: {summary['candidate_genes']}, "
                f"Archived: {summary['archived_genes']}, "
                f"MaxGen: {summary['max_generation']})"
            )
        return 0

    return 1


def entry_point() -> None:
    sys.exit(main())
