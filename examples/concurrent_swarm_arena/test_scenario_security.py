"""Unit and throughput benchmark tests for Scenario 4: SecuritySanitizer."""

from __future__ import annotations

from pathlib import Path
import tempfile
import time
import unittest

from scenario_security import SecuritySanitizer


class TestSecuritySanitizer(unittest.TestCase):
    """Test suite for single-pass PII/secret redaction and canonical path guard."""

    def setUp(self) -> None:
        self.sanitizer = SecuritySanitizer()

    def test_redact_bearer_jwt_and_api_tokens(self) -> None:
        line = (
            "GET /v1/profile Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
            ".eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )
        redacted = self.sanitizer.redact_log_line(line)
        self.assertEqual(
            redacted,
            "GET /v1/profile Authorization: [REDACTED_TOKEN]",
        )

    def test_redact_secret_keys(self) -> None:
        line = "Using API key sk-AbCdEfGhIjKlMnOpQrStUvWxYz012345 for request"
        redacted = self.sanitizer.redact_log_line(line)
        self.assertEqual(
            redacted,
            "Using API key [REDACTED_KEY] for request",
        )
        # Keys shorter than 16 alphanumeric characters after 'sk-' should not match
        short_key_line = " Benign token sk-short12345 in text"
        self.assertEqual(self.sanitizer.redact_log_line(short_key_line), short_key_line)

    def test_redact_email_addresses(self) -> None:
        line = "Password reset requested for alice.sec+tag_01@sub.example-corp.io from 10.0.0.1"
        redacted = self.sanitizer.redact_log_line(line)
        self.assertEqual(
            redacted,
            "Password reset requested for [REDACTED_EMAIL] from 10.0.0.1",
        )

    def test_redact_combined_single_pass(self) -> None:
        line = (
            "User admin@corp.internal authenticated via Bearer tok_998877-aa.bb "
            "and provisioned secret sk-1234567890abcdefABCDEF"
        )
        redacted = self.sanitizer.redact_log_line(line)
        self.assertEqual(
            redacted,
            "User [REDACTED_EMAIL] authenticated via [REDACTED_TOKEN] "
            "and provisioned secret [REDACTED_KEY]",
        )
        self.assertEqual(self.sanitizer.redact_log_line(""), "")

    def test_safe_resolve_path_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            nested_file = base / "logs" / "2026" / "audit.log"
            nested_file.parent.mkdir(parents=True, exist_ok=True)
            nested_file.write_text("ok", encoding="utf-8")

            resolved = self.sanitizer.safe_resolve_path(base, "logs/2026/audit.log")
            self.assertEqual(resolved, nested_file.resolve())

    def test_safe_resolve_path_blocks_traversal_and_prefix_tricks(self) -> None:
        with tempfile.TemporaryDirectory() as parent_tmp:
            parent = Path(parent_tmp)
            base = parent / "app_data"
            sibling_evil = parent / "app_data_compromised"
            base.mkdir(parents=True, exist_ok=True)
            sibling_evil.mkdir(parents=True, exist_ok=True)
            (sibling_evil / "secret.txt").write_text("top-secret", encoding="utf-8")

            traversal_vectors = [
                "../../etc/passwd",
                "../../../Windows/System32/drivers/etc/hosts",
                "../app_data_compromised/secret.txt",
                "logs/../../app_data_compromised/secret.txt",
                "/etc/passwd",
                "\\Windows\\win.ini",
                "safe/file.txt\x00.jpg",
            ]
            for vector in traversal_vectors:
                with self.subTest(vector=vector):
                    with self.assertRaises(PermissionError):
                        self.sanitizer.safe_resolve_path(base, vector)

    def test_throughput_20000_lines_under_150ms(self) -> None:
        sample_lines = [
            "2026-11-18T02:00:00Z INFO user=ops.lead@enterprise.io auth=Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig key=sk-9876543210abcdefABCDEF12",
            "2026-11-18T02:00:01Z WARN retry for dev_user@sub.domain.org token=Bearer api_tok_12345_xyz",
            "2026-11-18T02:00:02Z DEBUG rotated secret sk-abcdefghijklmnop12345678 for billing@company.com",
            "2026-11-18T02:00:03Z INFO healthcheck passed status=200 latency_ms=1.4",
        ] * 5000  # 20,000 log lines

        redact = self.sanitizer.redact_log_line
        start = time.perf_counter()
        outputs = [redact(line) for line in sample_lines]
        elapsed_sec = time.perf_counter() - start
        elapsed_ms = elapsed_sec * 1000.0
        lines_per_sec = len(sample_lines) / max(elapsed_sec, 1e-9)

        self.assertEqual(len(outputs), 20000)
        self.assertIn("[REDACTED_EMAIL]", outputs[0])
        self.assertIn("[REDACTED_TOKEN]", outputs[0])
        self.assertIn("[REDACTED_KEY]", outputs[0])
        self.assertLess(
            elapsed_ms,
            150.0,
            f"Expected < 150ms for 20,000 lines, got {elapsed_ms:.2f}ms ({lines_per_sec:,.0f} lines/sec)",
        )
        self.assertGreater(
            lines_per_sec,
            130000.0,
            f"Expected > 130,000 lines/sec, got {lines_per_sec:,.0f} lines/sec ({elapsed_ms:.2f}ms)",
        )
        print(
            f"\n[BENCHMARK] Redacted {len(sample_lines):,} lines in {elapsed_ms:.2f}ms "
            f"({lines_per_sec:,.0f} lines/sec)"
        )


if __name__ == "__main__":
    unittest.main()
