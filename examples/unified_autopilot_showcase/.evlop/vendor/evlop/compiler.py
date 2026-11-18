"""Markdown marker injection, DGM phylogenetic lineage rendering, and Voyager skill/tool synthesis."""

from __future__ import annotations

import json
from pathlib import Path
import re

from evlop.models import Gene

MARKER_START = "<!-- EVLOP:START -->"
MARKER_END = "<!-- EVLOP:END -->"
_START_LINE_RE = re.compile(r"^[ \t]*<!-- EVLOP:START -->[ \t]*$", re.MULTILINE)
_END_LINE_RE = re.compile(r"^[ \t]*<!-- EVLOP:END -->[ \t]*$", re.MULTILINE)
_BACKTICK_CMD_RE = re.compile(r"`([^`]+)`")


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
            lineage_tag = f" | Gen `{g.generation}`" + (f" from `{g.parent_id}`" if g.parent_id else "")
            lines.extend(
                [
                    f"### {idx}. [{g.category.upper()}] {g.title} (`{g.id}` | Fitness: `{g.fitness:.2f}` | S/F: `{g.success_count}/{g.failure_count}`{lineage_tag})",
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


def render_lineage_mermaid(genes: list[Gene]) -> str:
    """Render a Darwin Gödel Machine (DGM) style phylogenetic evolution tree in Mermaid format."""
    lines = [
        "# EVLOP Phylogenetic Lineage Tree (DGM Evolution Archive)",
        "",
        "```mermaid",
        "flowchart TD",
    ]
    if not genes:
        lines.append('    empty["No genes in archive yet"]')
    else:
        for g in genes:
            clean_title = g.title.replace('"', "'")
            label = f"{g.id}<br/>Gen {g.generation}: {clean_title}<br/>Fitness: {g.fitness:.2f} ({g.status})"
            lines.append(f'    {g.id}["{label}"]')
        for g in genes:
            if g.parent_id:
                reason = g.mutation_reason.replace('"', "'")[:36] if g.mutation_reason else "mutated"
                lines.append(f'    {g.parent_id} -->|"{reason}"| {g.id}')
    lines.append("```")
    return "\n".join(lines) + "\n"


def _synthesize_voyager_script(gene: Gene, scripts_dir: Path) -> Path:
    """Synthesize a Voyager-style executable Python helper tool from a Gene's strategy."""
    scripts_dir.mkdir(parents=True, exist_ok=True)
    script_path = scripts_dir / "run_strategy.py"

    cmd_match = _BACKTICK_CMD_RE.search(gene.strategy)
    extracted_cmd = cmd_match.group(1) if cmd_match else ""

    meta = {
        "gene_id": gene.id,
        "title": gene.title,
        "category": gene.category,
        "generation": gene.generation,
        "parent_id": gene.parent_id,
        "strategy": gene.strategy,
        "extracted_command": extracted_cmd,
    }
    meta_json = json.dumps(meta, indent=2, ensure_ascii=False)

    script_code = f'''#!/usr/bin/env python3
"""Auto-synthesized Voyager executable skill tool for EVLOP gene `{gene.id}`."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

GENE_METADATA = json.loads({json.dumps(meta_json)})


def main() -> int:
    parser = argparse.ArgumentParser(description=GENE_METADATA["title"])
    parser.add_argument("--info", action="store_true", help="Print gene metadata and strategy")
    parser.add_argument("--execute", action="store_true", help="Execute extracted strategy command")
    args = parser.parse_args()

    if args.info or not args.execute:
        print(json.dumps(GENE_METADATA, indent=2, ensure_ascii=False))
        return 0

    cmd = GENE_METADATA.get("extracted_command", "").strip()
    if not cmd:
        print(f"[Voyager Tool] Declarative strategy: {{GENE_METADATA['strategy']}}")
        return 0

    proc = subprocess.run(cmd, shell=True)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
'''
    script_path.write_text(script_code, encoding="utf-8")
    return script_path


def export_gene_to_skill(
    gene: Gene,
    skills_root: Path,
    synthesize_script: bool = False,
) -> Path:
    """Promote a high-fitness Gene into a standalone SKILL.md directory (and optional Voyager script)."""
    skill_name = f"auto-{gene.id}"
    skill_dir = Path(skills_root) / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"

    one_line_title = " ".join(gene.title.splitlines()).strip()
    one_line_trigger = " ".join(gene.trigger.splitlines()).strip()
    raw_desc = f"Auto-evolved EVLOP skill for [{gene.category}] {one_line_title}. Activate when encountering: {one_line_trigger}"
    safe_yaml_desc = json.dumps(raw_desc, ensure_ascii=False)

    script_section = ""
    if synthesize_script:
        _synthesize_voyager_script(gene, skill_dir / "scripts")
        script_section = f"""
## Synthesized Executable Tool (Voyager Mode)

This skill includes an auto-synthesized executable script:
- Inspect metadata: `python skills/{skill_name}/scripts/run_strategy.py --info`
- Execute strategy command: `python skills/{skill_name}/scripts/run_strategy.py --execute`
"""

    content = f"""---
name: {skill_name}
description: {safe_yaml_desc}
---

# {gene.title}

> **EVLOP Auto-Evolved Skill** (`{gene.id}`)
> - **Category:** `{gene.category}`
> - **Generation:** `{gene.generation}` {f"(Parent: `{gene.parent_id}`)" if gene.parent_id else "(Root Ancestor)"}
> - **Darwinian Fitness:** `{gene.fitness:.4f}`
> - **Empirical Track Record:** `{gene.success_count}` verified successes / `{gene.failure_count}` failures

## When to Trigger

Activate this skill whenever you encounter the following symptom, file pattern, or task context:

- {gene.trigger}

## Verified Strategy (What to Do)

{gene.strategy}

## Anti-Pattern (What to Avoid)

- {gene.anti_pattern}
{script_section}
## Evolution Lifecycle

If applying this skill resolves the task and passes `evlop verify`, reinforce it via:
```bash
python -m evlop log --title "{one_line_title}" --task "Applied {skill_name}" --symptom "{one_line_trigger}" --root-cause "Known pattern" --fix "{gene.strategy}"
```
"""
    skill_file.write_text(content, encoding="utf-8")
    return skill_file
