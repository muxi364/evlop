"""High-speed single-pass PII/secret log redactor and canonical path traversal guard."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Final

_TOKEN_BRANCH: Final[str] = r"(?P<token>Bearer [A-Za-z0-9\-_\.]++)"
_KEY_BRANCH: Final[str] = r"(?P<key>sk-[A-Za-z0-9]{16,}+)"
_EMAIL_BRANCH: Final[str] = (
    r"(?P<email>[A-Za-z0-9][A-Za-z0-9._%+\-]*+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})"
)

MASTER_REDACT_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"\b(?:{_TOKEN_BRANCH}|{_KEY_BRANCH}|{_EMAIL_BRANCH})"
)

_REPLACEMENTS: Final[dict[str | None, str]] = {
    "token": "[REDACTED_TOKEN]",
    "key": "[REDACTED_KEY]",
    "email": "[REDACTED_EMAIL]",
}


def _replace_match(
    match: re.Match[str],
    lookup: dict[str | None, str] = _REPLACEMENTS,
) -> str:
    """Map a named alternation match group to its constant redaction placeholder."""
    return lookup[match.lastgroup]


class SecuritySanitizer:
    """High-throughput O(N) log sanitizer and canonical path traversal guard."""

    MASTER_PATTERN: Final[re.Pattern[str]] = MASTER_REDACT_PATTERN

    @staticmethod
    def redact_log_line(
        text: str,
        _sub=MASTER_REDACT_PATTERN.sub,
    ) -> str:
        """Redact Bearer tokens, sk-* secret keys, and emails in a single regex pass."""
        if not text:
            if isinstance(text, str):
                return ""
            raise TypeError("Log line must be a string.")
        if "@" not in text and "Bearer " not in text and "sk-" not in text:
            return text
        return _sub(_replace_match, text)

    @staticmethod
    def safe_resolve_path(base_dir: Path, untrusted_rel_path: str) -> Path:
        """Resolve an untrusted relative path inside base_dir or raise PermissionError."""
        if not isinstance(untrusted_rel_path, str):
            raise PermissionError("Untrusted relative path must be a string.")
        if "\x00" in untrusted_rel_path or "\x00" in str(base_dir):
            raise PermissionError("Null byte injection detected in path.")

        if untrusted_rel_path.startswith(("/", "\\")):
            raise PermissionError(f"Absolute path not permitted: {untrusted_rel_path!r}")

        rel_path = Path(untrusted_rel_path)
        if rel_path.is_absolute() or rel_path.drive or rel_path.root:
            raise PermissionError(f"Anchored or drive path not permitted: {untrusted_rel_path!r}")

        try:
            canonical_base = Path(base_dir).resolve()
            resolved_target = (canonical_base / rel_path).resolve()
        except (OSError, RuntimeError, ValueError) as exc:
            raise PermissionError(f"Invalid path resolution for {untrusted_rel_path!r}") from exc

        if not resolved_target.is_relative_to(canonical_base):
            raise PermissionError(
                f"Path traversal blocked: {untrusted_rel_path!r} escapes {canonical_base}"
            )
        return resolved_target


redact_log_line = SecuritySanitizer.redact_log_line
safe_resolve_path = SecuritySanitizer.safe_resolve_path
