#!/usr/bin/env python3
"""Build single-file zero-dependency `evlop_standalone.py` distribution from `src/evlop/*.py`."""

from __future__ import annotations

import json
from pathlib import Path


def build_standalone() -> Path:
    repo_root = Path(__file__).resolve().parent.parent
    pkg_dir = repo_root / "src" / "evlop"
    modules: dict[str, str] = {}
    for py_file in sorted(pkg_dir.glob("*.py")):
        modules[py_file.name] = py_file.read_text(encoding="utf-8")

    payload_json = json.dumps(modules, indent=2, ensure_ascii=False)
    standalone_path = repo_root / "evlop_standalone.py"

    code = f'''#!/usr/bin/env python3
"""
EVLOP Single-File Standalone Distribution (`evlop_standalone.py`).
Drop this single file into ANY repository, container, or agent sandbox and run:
    python evlop_standalone.py init --bootstrap --with-hooks
    python evlop_standalone.py verify "<test-cmd>"
    python evlop_standalone.py mcp
Zero external pip dependencies required (Python 3.10+ standard library only).
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

_EMBEDDED_MODULES: dict[str, str] = json.loads({json.dumps(payload_json)})


def _ensure_embedded_package() -> Path:
    cwd_vendor = Path.cwd().resolve() / ".evlop" / "vendor"
    target_root = cwd_vendor if (Path.cwd().resolve() / ".evlop").exists() else Path(tempfile.gettempdir()) / "evlop_standalone_runtime"
    pkg_dir = target_root / "evlop"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in _EMBEDDED_MODULES.items():
        dest = pkg_dir / filename
        if not dest.exists() or dest.read_text(encoding="utf-8") != content:
            dest.write_text(content, encoding="utf-8")
    return target_root


def main() -> int:
    runtime_root = _ensure_embedded_package()
    if str(runtime_root) not in sys.path:
        sys.path.insert(0, str(runtime_root))
    from evlop.cli import main as cli_main

    return cli_main()


if __name__ == "__main__":
    sys.exit(main())
'''
    standalone_path.write_text(code, encoding="utf-8")
    print(f"[EVLOP Build] Generated single-file standalone executable: {standalone_path} ({len(modules)} modules)")
    return standalone_path


if __name__ == "__main__":
    build_standalone()
