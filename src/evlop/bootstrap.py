"""Turnkey cross-project bootstrapper so any Agent or IDE can mount EVLOP in one command."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

from evlop.compiler import inject_markdown_file
from evlop.models import Gene
from evlop.seed_genome import get_default_seed_genes
from evlop.store import EvlopStore


_AGENT_PROTOCOL_HEADER = """# {title} — EVLOP Self-Evolving Agent Protocol

This project is equipped with the **EVLOP Self-Evolving Agent Engine** (`.evlop/evlop_runner.py`).

## ⚡ Zero-Friction 2-Step Autopilot (Recommended for All Agents)
1. **Before coding (`preflight`):** Deconstruct the task into Feynman First-Principles invariants + recall top matching genes:
   `python .evlop/evlop_runner.py preflight "<your task description>"`
2. **After coding (`ship`):** Run unit tests + 100-point AST Quality Gate + auto-log/evolve/promote gene into `AGENTS.md`:
   `python .evlop/evlop_runner.py ship "<test-command>" --code <file_or_dir>`

---

## Granular 5-Stage Commands (Advanced Control)
1. **[E] Explore & Recall:** `python .evlop/evlop_runner.py recall "<error or keyword>"`
2. **[V] Verify & Audit:** `python .evlop/evlop_runner.py verify "<test-command>" --quality-gate . --auto-evolve`
3. **[L] Learn & Log:** `python .evlop/evlop_runner.py log --from-last-failure --title "<Rule Title>" --task "<Task>" --root-cause "<Why>" --fix "<How fixed>"`
4. **[O & P] Evolve & Promote:** `python .evlop/evlop_runner.py evolve --target AGENTS.md,CLAUDE.md,.cursorrules`
"""


def bootstrap_workspace(
    target_dir: Path,
    genes: list[Gene],
    max_genes: int = 15,
    with_hooks: bool = False,
) -> list[Path]:
    """
    Vendor a zero-dependency standalone EVLOP runner into `target_dir/.evlop/`
    and initialize `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.mcp.json`, and optional `.claude/settings.json`.
    """
    target_dir = Path(target_dir).resolve()
    if not genes:
        genes = get_default_seed_genes()
        EvlopStore(target_dir).save_genes(genes)
    evlop_dir = target_dir / ".evlop"
    vendor_pkg_dir = evlop_dir / "vendor" / "evlop"
    vendor_pkg_dir.mkdir(parents=True, exist_ok=True)

    src_pkg_dir = Path(__file__).resolve().parent
    if src_pkg_dir.name == "evlop" and (src_pkg_dir / "cli.py").exists():
        for py_file in src_pkg_dir.glob("*.py"):
            shutil.copy2(py_file, vendor_pkg_dir / py_file.name)

    runner_path = evlop_dir / "evlop_runner.py"
    runner_code = '''#!/usr/bin/env python3
"""Standalone zero-install EVLOP runner for external agent workspaces."""

from __future__ import annotations

from pathlib import Path
import sys

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "vendor"))

from evlop.cli import entry_point  # noqa: E402

if __name__ == "__main__":
    entry_point()
'''
    runner_path.write_text(runner_code, encoding="utf-8")

    created: list[Path] = [runner_path]
    for doc_name in ["AGENTS.md", "CLAUDE.md", ".cursorrules"]:
        doc_path = target_dir / doc_name
        if not doc_path.exists():
            doc_path.write_text(
                _AGENT_PROTOCOL_HEADER.format(title=doc_name),
                encoding="utf-8",
            )
        inject_markdown_file(doc_path, genes, max_genes=max_genes)
        created.append(doc_path)

    mcp_json_path = target_dir / ".mcp.json"
    mcp_payload = {
        "mcpServers": {
            "evlop": {
                "command": "python",
                "args": [".evlop/evlop_runner.py", "mcp"],
            }
        }
    }
    mcp_json_path.write_text(
        json.dumps(mcp_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    created.append(mcp_json_path)

    if with_hooks:
        claude_dir = target_dir / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        settings_path = claude_dir / "settings.json"
        hooks_payload = {
            "hooks": {
                "SessionStart": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python .evlop/evlop_runner.py status",
                            }
                        ]
                    }
                ],
                "Stop": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python .evlop/evlop_runner.py evolve --target AGENTS.md,CLAUDE.md,.cursorrules",
                            }
                        ]
                    }
                ],
            }
        }
        settings_path.write_text(
            json.dumps(hooks_payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        created.append(settings_path)

    return created
