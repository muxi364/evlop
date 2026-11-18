"""Unit and performance tests for Scenario 2: DoubleEntryLedger."""

from __future__ import annotations

from decimal import Decimal
import time
import unittest

from scenario_ledger import DoubleEntryLedger


class TestDoubleEntryLedger(unittest.TestCase):
    """Test suite for exact Decimal clearing, idempotency, and throughput."""

    def test_exact_basis_point_fee_rounding_half_up(self) -> None:
        """Verify ROUND_HALF_UP on half-cent boundary fees."""
        ledger = DoubleEntryLedger({"alice": "1000.00"})
        # 10.00 * 25 bps (0.25%) = 0.025 -> rounds half-up to 0.03
        receipt = ledger.post_transfer(
            tx_id="tx-half-up-1",
            sender="alice",
            receiver="bob",
            amount_str="10.00",
            fee_bps=25,
        )
        self.assertEqual(receipt["amount"], Decimal("10.00"))
        self.assertEqual(receipt["fee"], Decimal("0.03"))
        self.assertEqual(receipt["net_amount"], Decimal("9.97"))
        self.assertEqual(ledger.get_balance("alice"), Decimal("990.00"))
        self.assertEqual(ledger.get_balance("bob"), Decimal("9.97"))
        self.assertEqual(ledger.get_balance("platform_fee"), Decimal("0.03"))
        self.assertTrue(ledger.verify_zero_sum_invariant())

    def test_idempotent_replay_protection(self) -> None:
        """Verify re-submitting the same tx_id returns original receipt without double-charging."""
        ledger = DoubleEntryLedger({"alice": "500.00"})
        first = ledger.post_transfer(
            tx_id="tx-idem-001",
            sender="alice",
            receiver="bob",
            amount_str="100.00",
            fee_bps=150,
        )
        for _ in range(50):
            replay = ledger.post_transfer(
                tx_id="tx-idem-001",
                sender="alice",
                receiver="bob",
                amount_str="100.00",
                fee_bps=150,
            )
            self.assertIs(replay, first)

        self.assertEqual(ledger.get_balance("alice"), Decimal("400.00"))
        self.assertEqual(ledger.get_balance("bob"), Decimal("98.50"))
        self.assertEqual(ledger.get_balance("platform_fee"), Decimal("1.50"))
        self.assertTrue(ledger.verify_zero_sum_invariant())

    def test_overdraft_and_invalid_amount_rejection(self) -> None:
        """Verify negative, zero, malformed, and overdraft transfers are cleanly rejected."""
        ledger = DoubleEntryLedger({"alice": "50.00"})

        with self.assertRaises(ValueError):
            ledger.post_transfer("tx-neg", "alice", "bob", "-10.00", 100)

        with self.assertRaises(ValueError):
            ledger.post_transfer("tx-zero", "alice", "bob", "0.00", 100)

        with self.assertRaises(ValueError):
            ledger.post_transfer("tx-overdraft", "alice", "bob", "50.01", 100)

        with self.assertRaises(ValueError):
            ledger.post_transfer("tx-bad-bps", "alice", "bob", "10.00", -5)

        with self.assertRaises(ValueError):
            ledger.post_transfer("tx-self", "alice", "alice", "10.00", 10)

        self.assertEqual(ledger.get_balance("alice"), Decimal("50.00"))
        self.assertEqual(ledger.get_balance("bob"), Decimal("0.00"))
        self.assertTrue(ledger.verify_zero_sum_invariant())

    def test_ten_thousand_transfers_zero_sum_and_throughput(self) -> None:
        """Verify 10,000 transfers conserve zero-sum invariant in < 200ms."""
        ledger = DoubleEntryLedger(
            {
                "acct_0": "1000000.00",
                "acct_1": "1000000.00",
                "acct_2": "1000000.00",
                "acct_3": "1000000.00",
            }
        )
        accounts = ["acct_0", "acct_1", "acct_2", "acct_3"]
        total_transfers = 10_000

        start_ns = time.perf_counter_ns()
        for i in range(total_transfers):
            sender = accounts[i & 3]
            receiver = accounts[(i + 1) & 3]
            ledger.post_transfer(
                tx_id=f"tx-{i}",
                sender=sender,
                receiver=receiver,
                amount_str="13.37",
                fee_bps=35,
            )
        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000.0
        throughput = total_transfers / (elapsed_ms / 1000.0)

        print(
            f"\n[BENCHMARK] 10,000 transfers completed in {elapsed_ms:.2f} ms "
            f"({throughput:,.0f} transfers/sec)"
        )
        self.assertTrue(ledger.verify_zero_sum_invariant())
        total_user_and_fee = (
            sum(ledger.get_balance(acct) for acct in accounts)
            + ledger.get_balance("platform_fee")
        )
        self.assertEqual(total_user_and_fee, Decimal("4000000.00"))
        self.assertLess(
            elapsed_ms,
            200.0,
            f"Expected 10,000 transfers in < 200ms, got {elapsed_ms:.2f}ms",
        )


if __name__ == "__main__":
    unittest.main()
