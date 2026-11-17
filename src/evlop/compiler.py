"""Markdown marker injection (AGENTS.md / CLAUDE.md) and SKILL.md compiler for EVLOP Stage P."""

from __future__ import annotations

import json
from pathlib import Path
import re

from evlop.models import Gene

MARKER_START = "<!-- EVLOP:START -->"
MARKER_END = "<!-- EVLOP:END -->"
_START_LINE_RE = re.compile(r"^[ \t]*<!-- EVLOP:START -->[ \t]*$", re.MULTILINE)
_END_LINE_RE = re.compile(r"^[ \t]*<!-- EVLOP:END -->[ \t]*$", re.MULTILINE)


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
    """Inject or update the EVLOP genome block inside a Markdown file matching standalone marker lines only."""
    block = render_genes_markdown(genes, max_genes=max_genes)
    if not file_path.exists():
        header = f"# {file_path.stem} — Agent Instructions\n\n"
        file_path.write_text(header + block + "\n", encoding="utf-8")
        return

    existing = file_path.read_text(encoding="utf-8")
    m_start = _START_LINE_RE.search(existing)
    m_end = _END_LINE_RE.search(existing)

    if m_start and m_end and m_start.start() < m_end.start():
        updated = existing[: m_start.start()] + block + existing[m_end.end() :]
    else:
        cleaned = _START_LINE_RE.sub("", existing)
        cleaned = _END_LINE_RE.sub("", cleaned).rstrip()
        updated = f"{cleaned}\n\n{block}\n" if cleaned else f"{block}\n"

    file_path.write_text(updated, encoding="utf-8")


def export_gene_to_skill(gene: Gene, skills_root: Path) -> Path:
    """Promote a high-fitness Gene into a standalone SKILL.md directory with safely escaped YAML frontmatter."""
    skill_name = f"auto-{gene.id}"
    skill_dir = Path(skills_root) / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"

    one_line_title = " ".join(gene.title.splitlines()).strip()
    one_line_trigger = " ".join(gene.trigger.splitlines()).strip()
    raw_desc = f"Auto-evolved EVLOP skill for [{gene.category}] {one_line_title}. Activate when encountering: {one_line_trigger}"
    safe_yaml_desc = json.dumps(raw_desc, ensure_ascii=False)

    content = f"""---
name: {skill_name}
description: {safe_yaml_desc}
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
python -m evlop log --title "{one_line_title}" --task "Applied {skill_name}" --symptom "{one_line_trigger}" --root-cause "Known pattern" --fix "{gene.strategy}"
```
"""
    skill_file.write_text(content, encoding="utf-8")
    return skill_file
