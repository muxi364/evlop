"""Deterministic execution gate for EVLOP Stage V (Verify & Validate) with AlphaEvolve latency profiling."""

from __future__ import annotations

from pathlib import Path
import subprocess
import time

from evlop.models import VerifyRecord, utc_now_iso


def run_verification(command: str, cwd: Path, timeout_sec: int = 120) -> VerifyRecord:
    """Execute a verification shell command and capture its exit code, latency (ms), and output."""
    t0 = time.perf_counter()
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
        duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        combined = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
        snippet = combined[-1200:] if len(combined) > 1200 else combined
        return VerifyRecord(
            command=command,
            exit_code=proc.returncode,
            passed=(proc.returncode == 0),
            timestamp=utc_now_iso(),
            output_snippet=snippet,
            duration_ms=duration_ms,
        )
    except subprocess.TimeoutExpired as exc:
        duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return VerifyRecord(
            command=command,
            exit_code=124,
            passed=False,
            timestamp=utc_now_iso(),
            output_snippet=f"TimeoutExpired after {timeout_sec}s: {exc}",
            duration_ms=duration_ms,
        )
    except Exception as exc:  # pragma: no cover - defensive fallback
        duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return VerifyRecord(
            command=command,
            exit_code=1,
            passed=False,
            timestamp=utc_now_iso(),
            output_snippet=f"Execution error: {exc}",
            duration_ms=duration_ms,
        )
