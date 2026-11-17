"""Deterministic execution gate for EVLOP Stage V (Verify & Validate)."""

from __future__ import annotations

from pathlib import Path
import subprocess

from evlop.models import VerifyRecord, utc_now_iso


def run_verification(command: str, cwd: Path, timeout_sec: int = 120) -> VerifyRecord:
    """Execute a verification shell command and capture its exit code and output."""
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
        )
        combined = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
        snippet = combined[-1200:] if len(combined) > 1200 else combined
        return VerifyRecord(
            command=command,
            exit_code=proc.returncode,
            passed=(proc.returncode == 0),
            timestamp=utc_now_iso(),
            output_snippet=snippet,
        )
    except subprocess.TimeoutExpired as exc:
        return VerifyRecord(
            command=command,
            exit_code=124,
            passed=False,
            timestamp=utc_now_iso(),
            output_snippet=f"TimeoutExpired after {timeout_sec}s: {exc}",
        )
    except Exception as exc:  # pragma: no cover - defensive fallback
        return VerifyRecord(
            command=command,
            exit_code=1,
            passed=False,
            timestamp=utc_now_iso(),
            output_snippet=f"Execution error: {exc}",
        )
