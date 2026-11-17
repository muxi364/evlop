#!/usr/bin/env python3
"""Auto-synthesized Voyager executable skill tool for EVLOP gene `gene-execution-verified-patching-gate`."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

GENE_METADATA = json.loads("{\n  \"gene_id\": \"gene-execution-verified-patching-gate\",\n  \"title\": \"Execution-Verified Patching Gate\",\n  \"category\": \"testing\",\n  \"generation\": 1,\n  \"parent_id\": \"\",\n  \"strategy\": \"Run python -m evlop verify '<test-cmd>' and confirm exit_code == 0 before concluding\",\n  \"extracted_command\": \"\"\n}")


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
        print(f"[Voyager Tool] Declarative strategy: {GENE_METADATA['strategy']}")
        return 0

    proc = subprocess.run(cmd, shell=True)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
