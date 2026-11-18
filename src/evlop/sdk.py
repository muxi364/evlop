"""High-level programmatic Python SDK (`from evlop import EvlopEngine`) for LangGraph, CrewAI, AutoGen, and custom agents."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from evlop.bootstrap import bootstrap_workspace
from evlop.compiler import export_gene_to_skill, inject_markdown_file, render_lineage_mermaid
from evlop.dag_rail import DagRunRecord, execute_dag_rail
from evlop.feynman import distill_feynman_gene, generate_feynman_blueprint
from evlop.fitness import govern_genes
from evlop.models import Episode, Gene, VerifyRecord, slugify_gene_id, utc_now_iso
from evlop.quality_gate import audit_python_path
from evlop.store import EvlopStore
from evlop.verifier import extract_failure_diagnosis, run_verification


class EvlopEngine:
    """Programmatic SDK facade for mounting EVLOP inside any Python agent runtime."""

    def __init__(self, workspace: Path | str = ".") -> None:
        self.workspace = Path(workspace).resolve()
        self.store = EvlopStore(self.workspace)
        self.store.init_store()

    def bootstrap(self, with_hooks: bool = False) -> list[Path]:
        cfg = self.store.load_config()
        return bootstrap_workspace(
            self.workspace,
            self.store.load_genes(),
            max_genes=cfg.max_active_genes,
            with_hooks=with_hooks,
        )

    def recall(self, query: str = "*", top_k: int = 5) -> list[Gene]:
        return self.store.recall_genes(query, top_k=top_k)

    def preflight(self, task: str, top_k: int = 5) -> dict[str, Any]:
        """
        Unified Step-1 Autopilot (`evlop preflight`):
        Deconstructs the task via Feynman First-Principles and recalls top matching genes in one call.
        """
        bp = generate_feynman_blueprint(task)
        recalled = self.store.recall_genes(task, top_k=top_k)
        payload: dict[str, Any] = {
            "task": task,
            "timestamp": utc_now_iso(),
            "blueprint": bp.to_dict(),
            "recalled_genes": [g.to_dict() for g in recalled],
        }
        active_file = self.store.evlop_dir / "active_preflight.json"
        with self.store.lock():
            active_file.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        return payload

    def ship(
        self,
        command: str,
        code_path: Path | str = ".",
        min_quality_score: float = 95.0,
        agent_id: str = "sdk-agent",
        timeout_sec: int = 120,
    ) -> dict[str, Any]:
        """
        Unified Step-2 Autopilot (`evlop ship`):
        Runs verification command + AST Quality Gate, and on pass automatically distills, logs,
        evolves, and promotes the active Feynman/verified gene into AGENTS.md & CLAUDE.md.
        """
        target_code = Path(code_path)
        if not target_code.is_absolute():
            target_code = (self.workspace / target_code).resolve()

        record = run_verification(command, cwd=self.workspace, timeout_sec=timeout_sec)
        q_rep = audit_python_path(target_code, min_score=min_quality_score)
        if not q_rep.passed:
            record.passed = False
            if record.exit_code == 0:
                record.exit_code = 2
            findings_txt = "; ".join(f"{f.file}:{f.line} {f.rule_id}" for f in q_rep.findings)
            record.output_snippet = (
                f"{record.output_snippet}\n[EVLOP Quality Gate FAILED] AST Score {q_rep.score} < {q_rep.min_score}: {findings_txt}"
            ).strip()

        with self.store.lock():
            cfg = self.store.load_config()
            self.store.save_verify(record, agent_id=agent_id)
            if not record.passed:
                diag = extract_failure_diagnosis(record)
                self.store.save_failure(diag, agent_id=agent_id)
                hints = self.store.recall_genes(f"{diag.error_type} {diag.symptom_summary}", top_k=3)
                return {
                    "passed": False,
                    "exit_code": record.exit_code or 1,
                    "ast_score": q_rep.score,
                    "ast_findings": [f.to_dict() for f in q_rep.findings],
                    "duration_ms": record.duration_ms,
                    "output_snippet": record.output_snippet,
                    "diagnosis": diag.to_dict(),
                    "hints": [h.to_dict() for h in hints],
                    "promoted_gene_id": "",
                    "promoted_gene_title": "",
                }

            active_file = self.store.evlop_dir / "active_preflight.json"
            task_text = f"Verified delivery: {command}"
            if active_file.exists():
                try:
                    pre_data = json.loads(active_file.read_text(encoding="utf-8"))
                    task_text = str(pre_data.get("task") or task_text)
                except (OSError, json.JSONDecodeError):
                    pass

            bp = generate_feynman_blueprint(task_text)
            new_gene = distill_feynman_gene(bp, verified=True)
            new_gene.contributors = [agent_id]
            new_gene.best_duration_ms = record.duration_ms

            now_iso = utc_now_iso()
            prior_fail = self.store.load_last_failure(agent_id=agent_id)
            symptom_txt = (
                f"{prior_fail.error_type}: {prior_fail.symptom_summary}"
                if prior_fail
                else bp.first_principles_invariant
            )
            ep_hash = hashlib.sha1(f"{now_iso}:{new_gene.id}:{agent_id}".encode("utf-8")).hexdigest()[:10]
            ep = Episode(
                episode_id=f"ep-{ep_hash}",
                timestamp=now_iso,
                task_summary=task_text,
                failure_symptom=symptom_txt,
                root_cause=bp.first_principles_invariant,
                fix_applied=f"Passed unit tests ({record.duration_ms:.1f}ms) and AST audit ({q_rep.score}/100.0)",
                verified=True,
                verify_cmd=command,
                gene_id=new_gene.id,
                agent_id=agent_id,
            )
            self.store.append_episode(ep)
            genes = self.store.load_genes()
            genes.append(new_gene)
            governed = govern_genes(genes, cfg)
            self.store.save_genes(governed)
            for doc_name in ("AGENTS.md", "CLAUDE.md", ".cursorrules"):
                doc_p = self.workspace / doc_name
                if doc_name in ("AGENTS.md", "CLAUDE.md") or doc_p.exists():
                    inject_markdown_file(doc_p, governed, max_genes=cfg.max_active_genes)

            return {
                "passed": True,
                "exit_code": 0,
                "ast_score": q_rep.score,
                "ast_findings": [f.to_dict() for f in q_rep.findings],
                "duration_ms": record.duration_ms,
                "output_snippet": record.output_snippet,
                "diagnosis": None,
                "hints": [],
                "promoted_gene_id": new_gene.id,
                "promoted_gene_title": new_gene.title,
            }

    def verify(self, command: str, timeout_sec: int = 120) -> VerifyRecord:
        record = run_verification(command, cwd=self.workspace, timeout_sec=timeout_sec)
        with self.store.lock():
            self.store.save_verify(record)
            if not record.passed:
                diag = extract_failure_diagnosis(record)
                self.store.save_failure(diag)
        return record

    def log_experience(
        self,
        *,
        title: str,
        task: str,
        root_cause: str,
        fix: str,
        symptom: str = "",
        category: str = "debugging",
        trigger: str = "",
        strategy: str = "",
        anti_pattern: str = "Blindly guessing without verification",
        agent_id: str = "sdk-agent",
        from_last_failure: bool = False,
        failed: bool = False,
    ) -> Gene:
        with self.store.lock():
            cfg = self.store.load_config()
            last_v = self.store.load_last_verify()
            is_verified = bool(
                self.store.is_verify_fresh(last_v, ttl_minutes=cfg.verify_ttl_minutes)
                and not failed
            )
            verify_cmd = last_v.command if last_v else ""

            eff_symptom = symptom.strip()
            eff_trigger = trigger.strip()
            if from_last_failure:
                last_fail = self.store.load_last_failure()
                if last_fail:
                    if not eff_symptom:
                        eff_symptom = f"{last_fail.error_type}: {last_fail.symptom_summary}"
                    if not eff_trigger:
                        eff_trigger = f"{last_fail.error_type} {last_fail.symptom_summary}"
            if not eff_symptom:
                eff_symptom = task.strip()

            clean_title = title.strip() or fix.strip()[:60]
            gene_id = slugify_gene_id(clean_title)
            now_iso = utc_now_iso()
            ep_hash = hashlib.sha1(f"{now_iso}:{task}:{gene_id}:{agent_id}".encode("utf-8")).hexdigest()[:10]

            ep = Episode(
                episode_id=f"ep-{ep_hash}",
                timestamp=now_iso,
                task_summary=task,
                failure_symptom=eff_symptom,
                root_cause=root_cause,
                fix_applied=fix,
                verified=is_verified,
                verify_cmd=verify_cmd,
                gene_id=gene_id,
                agent_id=agent_id,
            )
            self.store.append_episode(ep)

            genes = self.store.load_genes()
            new_gene = Gene(
                id=gene_id,
                title=clean_title,
                category=category,
                trigger=eff_trigger or eff_symptom,
                strategy=strategy.strip() or fix.strip(),
                anti_pattern=anti_pattern.strip(),
                success_count=1 if is_verified else 0,
                failure_count=1 if failed else 0,
                verified_gate=is_verified,
                created_at=now_iso,
                last_used_at=now_iso,
                contributors=[agent_id],
                best_duration_ms=last_v.duration_ms if (is_verified and last_v) else 0.0,
            )
            genes.append(new_gene)
            governed = govern_genes(genes, cfg)
            self.store.save_genes(governed)
            by_id = {g.id: g for g in governed}
            return by_id.get(gene_id, governed[0])

    def evolve(self, targets: Sequence[str] = ("AGENTS.md", "CLAUDE.md")) -> list[Gene]:
        with self.store.lock():
            cfg = self.store.load_config()
            governed = govern_genes(self.store.load_genes(), cfg)
            self.store.save_genes(governed)
            for rel in targets:
                inject_markdown_file(self.workspace / rel, governed, max_genes=cfg.max_active_genes)
            return governed

    def export_skill(self, gene_id: str, out_dir: str = "skills", synthesize_script: bool = True) -> Path:
        genes = {g.id: g for g in self.store.load_genes()}
        if gene_id not in genes:
            raise KeyError(f"Gene '{gene_id}' not found.")
        target_gene = genes[gene_id]
        if not target_gene.verified_gate or target_gene.status == "archived":
            raise ValueError(f"Gene '{gene_id}' is unverified or archived.")
        return export_gene_to_skill(
            target_gene,
            self.workspace / out_dir,
            synthesize_script=synthesize_script,
        )

    def run_dag(self, spec_path: Path | str, run_id: str = "") -> DagRunRecord:
        p = Path(spec_path)
        if not p.is_absolute():
            p = (self.workspace / p).resolve()
        return execute_dag_rail(p, workspace=self.workspace, store=self.store, run_id=run_id)

    def lineage_mermaid(self) -> str:
        cfg = self.store.load_config()
        return render_lineage_mermaid(govern_genes(self.store.load_genes(), cfg))

    def status(self) -> dict[str, Any]:
        cfg = self.store.load_config()
        genes = govern_genes(self.store.load_genes(), cfg)
        episodes = self.store.load_episodes()
        return {
            "total_episodes": len(episodes),
            "total_genes": len(genes),
            "promoted_genes": sum(1 for g in genes if g.status == "promoted"),
            "superseded_genes": sum(1 for g in genes if g.status == "superseded"),
            "archived_genes": sum(1 for g in genes if g.status == "archived"),
            "max_generation": max((g.generation for g in genes), default=0),
            "swarm_contributors": sorted({c for g in genes for c in g.contributors}),
        }
