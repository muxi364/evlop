"""Deterministic execution gate and automatic failure stack-trace extractor."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import time

from evlop.models import FailureDiagnosis, VerifyRecord, utc_now_iso

_ERROR_TYPE_RE = re.compile(
    r"\b([A-Z][A-Za-z0-9_]*(?:Error|Exception|Warning|Failure|Fault)|FAIL|ERROR|panic)\b"
)


def extract_failure_diagnosis(record: VerifyRecord) -> FailureDiagnosis:
    """Extract structured error_type and concise symptom line from a failing VerifyRecord."""
    lines = [ln.strip() for ln in record.output_snippet.splitlines() if ln.strip()]
    error_type = "ExecutionFailure"
    symptom_summary = f"Command `{record.command}` exited with code {record.exit_code}"

    for line in reversed(lines):
        m = _ERROR_TYPE_RE.search(line)
        if m:
            error_type = m.group(1)
            symptom_summary = line[:200]
            break
    else:
        if lines:
            symptom_summary = lines[-1][:200]

    return FailureDiagnosis(
        command=record.command,
        exit_code=record.exit_code,
        timestamp=record.timestamp,
        error_type=error_type,
        symptom_summary=symptom_summary,
        output_snippet=record.output_snippet,
    )


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
