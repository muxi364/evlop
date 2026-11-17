"""CLI entrypoint for EVLOP v2.0: init, recall, verify, log, mutate, lineage, evolve, export-skill, status."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

from evlop.compiler import export_gene_to_skill, inject_markdown_file, render_lineage_mermaid
from evlop.fitness import govern_genes
from evlop.models import Episode, Gene, slugify_gene_id, utc_now_iso
from evlop.store import EvlopStore
from evlop.verifier import run_verification


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
        description="EVLOP v2.0: Self-Evolving Agent Framework & DGM/AlphaEvolve Lineage Engine",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p_init = sub.add_parser("init", help="Initialize .evlop/ workspace store")
    p_init.add_argument("--target-dir", default=".", help="Workspace directory")

    p_recall = sub.add_parser("recall", help="[Stage E] Recall relevant evolved genes before acting")
    p_recall.add_argument("query", help="Search keywords, error message, or '*' for top genes")
    p_recall.add_argument("--top", type=int, default=5, help="Max genes to return")

    p_verify = sub.add_parser("verify", help="[Stage V] Run deterministic verification command gate")
    p_verify.add_argument("command", help="Shell command to execute (e.g. pytest, npm test)")
    p_verify.add_argument("--timeout", type=int, default=120, help="Timeout in seconds")

    p_log = sub.add_parser("log", help="[Stage L] Record an episode and create/reinforce a gene")
    p_log.add_argument("--title", default="", help="Short imperative rule title")
    p_log.add_argument("--task", required=True, help="Summary of the task being solved")
    p_log.add_argument("--symptom", required=True, help="Failure symptom or problem encountered")
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

    p_status = sub.add_parser("status", help="Inspect EVLOP genome health, swarm contributors, and lineage depth")
    p_status.add_argument("--json", action="store_true", help="Output status as JSON")

    return parser


def main(argv: list[str] | None = None, root_dir: Path | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    workspace = Path(root_dir).resolve() if root_dir else Path.cwd().resolve()

    if args.subcommand == "init":
        target = (workspace / args.target_dir).resolve() if not root_dir else workspace
        store = EvlopStore(target)
        evlop_path = store.init_store()
        _safe_print(f"[EVLOP] Initialized self-evolution store at {evlop_path}")
        return 0

    store = EvlopStore(workspace)
    store.init_store()
    cfg = store.load_config()

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

    if args.subcommand == "verify":
        record = run_verification(args.command, cwd=workspace, timeout_sec=args.timeout)
        store.save_verify(record)
        status_str = "PASSED" if record.passed else f"FAILED (exit={record.exit_code})"
        _safe_print(f"[EVLOP Verify] {status_str} ({record.duration_ms:.1f}ms) -> {record.command}")
        if record.output_snippet:
            _safe_print(record.output_snippet)
        return 0 if record.passed else (record.exit_code or 1)

    if args.subcommand == "log":
        last_v = store.load_last_verify()
        is_verified = bool(last_v and last_v.passed and not args.failed)
        verify_cmd = last_v.command if last_v else ""
        agent_id = args.agent_id.strip() or os.environ.get("EVLOP_AGENT_ID", "default-agent")

        title = args.title.strip() or args.fix.strip()[:60]
        gene_id = slugify_gene_id(title)
        now_iso = utc_now_iso()
        ep_hash = hashlib.sha1(f"{now_iso}:{args.task}:{gene_id}:{agent_id}".encode("utf-8")).hexdigest()[:10]

        episode = Episode(
            episode_id=f"ep-{ep_hash}",
            timestamp=now_iso,
            task_summary=args.task,
            failure_symptom=args.symptom,
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
            trigger=args.trigger.strip() or args.symptom.strip(),
            strategy=args.strategy.strip() or args.fix.strip(),
            anti_pattern=args.anti_pattern.strip(),
            success_count=1 if is_verified else 0,
            failure_count=1 if args.failed else 0,
            verified_gate=is_verified,
            created_at=now_iso,
            last_used_at=now_iso,
            contributors=[agent_id],
        )
        genes.append(new_gene)
        governed = govern_genes(genes, cfg)
        store.save_genes(governed)
        _safe_print(
            f"[EVLOP Log] Recorded episode {episode.episode_id} (agent={agent_id}) -> gene {gene_id} (verified={is_verified})"
        )
        return 0

    if args.subcommand == "mutate":
        genes = store.load_genes()
        by_id = {g.id: g for g in genes}
        if args.parent_id not in by_id:
            _safe_print(f"[EVLOP Error] Parent gene '{args.parent_id}' not found.", file=sys.stderr)
            return 1
        parent = by_id[args.parent_id]
        last_v = store.load_last_verify()
        is_verified = bool(last_v and last_v.passed)
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
