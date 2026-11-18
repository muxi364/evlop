"""Scenario 2: Double-Entry Financial Ledger & Idempotent Basis-Point Clearing."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

ZERO = Decimal("0.00")
CENT = Decimal("0.01")
BPS_DIVISOR = Decimal(10000)


class DoubleEntryLedger:
    """Zero-sum double-entry financial ledger with O(1) idempotent clearing."""

    def __init__(
        self, initial_balances: dict[str, str | Decimal] | None = None
    ) -> None:
        """Initialize the ledger with optional funded account balances."""
        self._balances: dict[str, Decimal] = {}
        self._treasury_offset: Decimal = ZERO
        self._receipts: dict[str, dict[str, Any]] = {}
        if initial_balances:
            for account, raw_amount in initial_balances.items():
                self.fund_account(account, str(raw_amount))

    @staticmethod
    def _parse_positive_amount(amount_str: str) -> Decimal:
        """Parse and quantize a positive monetary amount using ROUND_HALF_UP."""
        if not isinstance(amount_str, (str, Decimal)) or str(amount_str).strip() == "":
            raise ValueError("Amount must be a non-empty string or Decimal.")
        try:
            raw = Decimal(str(amount_str))
        except InvalidOperation as exc:
            raise ValueError(f"Invalid decimal amount: {amount_str!r}") from exc
        if not raw.is_finite():
            raise ValueError("Amount must be finite.")
        quantized = raw.quantize(CENT, rounding=ROUND_HALF_UP)
        if quantized <= ZERO:
            raise ValueError("Amount must be strictly positive.")
        return quantized

    def fund_account(self, account: str, amount_str: str) -> Decimal:
        """Credit an account and debit the offsetting treasury account."""
        if not account or not account.strip():
            raise ValueError("Account identifier must be non-empty.")
        amount = self._parse_positive_amount(amount_str)
        self._balances[account] = self._balances.get(account, ZERO) + amount
        self._treasury_offset -= amount
        return self._balances[account]

    def get_balance(self, account: str) -> Decimal:
        """Return the current quantized balance of an account."""
        return self._balances.get(account, ZERO)

    def get_receipt(self, tx_id: str) -> dict[str, Any] | None:
        """Return a previously posted transaction receipt in O(1) time."""
        return self._receipts.get(tx_id)

    def post_transfer(
        self,
        tx_id: str,
        sender: str,
        receiver: str,
        amount_str: str,
        fee_bps: int,
        fee_account: str = "platform_fee",
    ) -> dict[str, Any]:
        """Post an idempotent double-entry transfer with basis-point fee clearing."""
        if not tx_id or not tx_id.strip():
            raise ValueError("Transaction ID must be non-empty.")

        existing = self._receipts.get(tx_id)
        if existing is not None:
            return existing

        if not sender or not receiver or not fee_account:
            raise ValueError("Sender, receiver, and fee_account must be non-empty.")
        if sender == receiver:
            raise ValueError("Sender and receiver must be distinct accounts.")
        if isinstance(fee_bps, bool) or not isinstance(fee_bps, int):
            raise ValueError("fee_bps must be an integer.")
        if fee_bps < 0 or fee_bps > 10000:
            raise ValueError("fee_bps must be between 0 and 10000 inclusive.")

        amount = self._parse_positive_amount(amount_str)
        sender_balance = self._balances.get(sender, ZERO)
        if sender_balance < amount:
            raise ValueError(
                f"Insufficient balance for {sender}: has {sender_balance}, needs {amount}."
            )

        fee = (amount * Decimal(fee_bps) / BPS_DIVISOR).quantize(
            CENT, rounding=ROUND_HALF_UP
        )
        net_amount = amount - fee

        self._balances[sender] = sender_balance - amount
        self._balances[receiver] = self._balances.get(receiver, ZERO) + net_amount
        self._balances[fee_account] = self._balances.get(fee_account, ZERO) + fee

        receipt: dict[str, Any] = {
            "tx_id": tx_id,
            "sender": sender,
            "receiver": receiver,
            "fee_account": fee_account,
            "amount": amount,
            "fee": fee,
            "net_amount": net_amount,
            "fee_bps": fee_bps,
            "status": "POSTED",
        }
        self._receipts[tx_id] = receipt
        return receipt

    def verify_zero_sum_invariant(self) -> bool:
        """Verify that all balances and treasury offsets sum to exactly 0.00."""
        if any(balance < ZERO for balance in self._balances.values()):
            return False
        total_assets = sum(self._balances.values(), ZERO)
        return (total_assets + self._treasury_offset) == ZERO
