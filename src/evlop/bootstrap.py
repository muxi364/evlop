"""Turnkey cross-project bootstrapper so any Agent can adopt EVLOP in one command."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

from evlop.compiler import inject_markdown_file
from evlop.models import Gene


_AGENT_PROTOCOL_HEADER = """# {title} — EVLOP Self-Evolving Agent Protocol

This project is equipped with the **EVLOP Self-Evolving Agent Engine** (`.evlop/evlop_runner.py`).
Follow the 5-stage loop on every coding or debugging task:

1. **[E] Explore & Recall:** Before acting or when hitting an error, run:
   `python .evlop/evlop_runner.py recall "<error or keyword>"`
2. **[V] Verify Deterministically:** Run your test/build command through the gate:
   `python .evlop/evlop_runner.py verify "<test-command>"`
   *(If verification fails, EVLOP automatically diagnoses the stack trace and recalls matching fixes!)*
3. **[L] Learn & Log:** After fixing a failure and passing `verify`, log the lesson automatically:
   `python .evlop/evlop_runner.py log --from-last-failure --title "<Rule Title>" --task "<Task>" --root-cause "<Why>" --fix "<How fixed>"`
4. **[O & P] Evolve & Promote:** Compile verified high-fitness genes into project instructions:
   `python .evlop/evlop_runner.py evolve --target AGENTS.md,CLAUDE.md,.cursorrules`
"""


def bootstrap_workspace(
    target_dir: Path,
    genes: list[Gene],
    max_genes: int = 15,
    with_hooks: bool = False,
) -> list[Path]:
    """
    Vendor a zero-dependency standalone EVLOP runner into `target_dir/.evlop/`
    and initialize `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, and optional `.claude/settings.json`.
    """
    target_dir = Path(target_dir).resolve()
    evlop_dir = target_dir / ".evlop"
    vendor_pkg_dir = evlop_dir / "vendor" / "evlop"
    vendor_pkg_dir.mkdir(parents=True, exist_ok=True)

    # Copy all current evlop package modules into .evlop/vendor/evlop/ so the target project is 100% standalone
    src_pkg_dir = Path(__file__).resolve().parent
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
