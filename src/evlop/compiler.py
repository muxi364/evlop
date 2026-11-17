"""Markdown marker injection (AGENTS.md / CLAUDE.md) and SKILL.md compiler for EVLOP Stage P."""

from __future__ import annotations

from pathlib import Path

from evlop.models import Gene

MARKER_START = "<!-- EVLOP:START -->"
MARKER_END = "<!-- EVLOP:END -->"


def render_genes_markdown(genes: list[Gene], max_genes: int = 15) -> str:
    """Render top promoted genes into a bounded, structured Markdown block."""
    promoted = [g for g in genes if g.status == "promoted"]
    promoted.sort(key=lambda g: (g.fitness, g.success_count), reverse=True)
    selected = promoted[:max_genes]

    lines = [
        MARKER_START,
        "## EVLOP Evolved Genome (Auto-Compiled High-Fitness Rules)",
        "",
        "> Managed automatically by `evlop evolve`. Only verified rules (`verified_gate=True`) with high Darwinian fitness are promoted here (capped at top "
        f"{max_genes} genes to prevent Context Rot).",
        "",
    ]

    if not selected:
        lines.append("_No promoted genes yet. Run `evlop verify` -> `evlop log` -> `evlop evolve` to evolve rules._")
    else:
        for idx, g in enumerate(selected, start=1):
            lines.extend(
                [
                    f"### {idx}. [{g.category.upper()}] {g.title} (`{g.id}` | Fitness: `{g.fitness:.2f}` | S/F: `{g.success_count}/{g.failure_count}`)",
                    f"- **Trigger (When):** {g.trigger}",
                    f"- **Strategy (Do):** {g.strategy}",
                    f"- **Anti-Pattern (Avoid):** {g.anti_pattern}",
                    "",
                ]
            )

    lines.append(MARKER_END)
    return "\n".join(lines)


def inject_markdown_file(file_path: Path, genes: list[Gene], max_genes: int = 15) -> None:
    """Inject or update the EVLOP genome block inside a Markdown file."""
    block = render_genes_markdown(genes, max_genes=max_genes)
    if not file_path.exists():
        header = f"# {file_path.stem} — Agent Instructions\n\n"
        file_path.write_text(header + block + "\n", encoding="utf-8")
        return

    existing = file_path.read_text(encoding="utf-8")
    start_idx = existing.find(MARKER_START)
    end_idx = existing.find(MARKER_END)

    if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
        updated = (
            existing[:start_idx]
            + block
            + existing[end_idx + len(MARKER_END) :]
        )
    else:
        cleaned = existing.replace(MARKER_START, "").replace(MARKER_END, "").rstrip()
        updated = f"{cleaned}\n\n{block}\n" if cleaned else f"{block}\n"

    file_path.write_text(updated, encoding="utf-8")


def export_gene_to_skill(gene: Gene, skills_root: Path) -> Path:
    """Promote a high-fitness Gene into a standalone SKILL.md directory."""
    skill_name = f"auto-{gene.id}"
    skill_dir = Path(skills_root) / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"

    content = f"""---
name: {skill_name}
description: "Auto-evolved EVLOP skill for [{gene.category}] {gene.title}. Activate when encountering: {gene.trigger}"
---

# {gene.title}

> **EVLOP Auto-Evolved Skill** (`{gene.id}`)
> - **Category:** `{gene.category}`
> - **Darwinian Fitness:** `{gene.fitness:.4f}`
> - **Empirical Track Record:** `{gene.success_count}` verified successes / `{gene.failure_count}` failures

## When to Trigger

Activate this skill whenever you encounter the following symptom, file pattern, or task context:

- {gene.trigger}

## Verified Strategy (What to Do)

{gene.strategy}

## Anti-Pattern (What to Avoid)

- {gene.anti_pattern}

## Evolution Lifecycle

If applying this skill resolves the task and passes `evlop verify`, reinforce it via:
```bash
python -m evlop log --title "{gene.title}" --task "Applied {skill_name}" --symptom "{gene.trigger}" --root-cause "Known pattern" --fix "{gene.strategy}"
```
"""
    skill_file.write_text(content, encoding="utf-8")
    return skill_file
