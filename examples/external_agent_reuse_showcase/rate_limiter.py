"""High-throughput O(1) Lazy-Refill Token Bucket Rate Limiter.

Engineered under the EVLOP Self-Evolving Agent Protocol:
- Gene `gene-seed-algorithmic-complexity`: Strictly O(1) time and O(1) space per
  request using lazy monotonic timestamp arithmetic (zero loops, zero per-request
  timestamp log allocations).
- Gene `gene-seed-numerical-and-boundary-safety`: Strict boundary guards against
  NaN, Inf, non-positive capacity/refill rates, negative token costs, and clock
  skew, with exact retry-after and remaining-token computation.
"""

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class RateLimitDecision:
    """Immutable decision snapshot returned by detailed rate limit checks."""

    allowed: bool
    remaining_tokens: float
    retry_after_sec: float
    capacity: float
    refill_rate: float


class TokenBucketRateLimiter:
    """Production-grade O(1) lazy-refill token bucket rate limiter.

    Instead of storing sliding-window request timestamps (which degrades to O(N)
    pruning under burst traffic), this implementation stores only the current
    token balance and last monotonic update timestamp, computing token replenishment
    lazily in O(1) arithmetic on each request.
    """

    __slots__ = (
        "_capacity",
        "_refill_rate",
        "_inv_refill_rate",
        "_clock_fn",
        "_lock",
        "_tokens",
        "_last_timestamp",
        "_last_retry_after_sec",
    )

    def __init__(
        self,
        capacity: float,
        refill_rate: float,
        clock_fn: Callable[[], float] = time.monotonic,
        thread_safe: bool = True,
        initial_tokens: Optional[float] = None,
    ) -> None:
        """Initialize the token bucket rate limiter with strict boundary validation.

        Args:
            capacity: Maximum burst capacity (must be finite and > 0).
            refill_rate: Steady token refill rate per second (must be finite and > 0).
            clock_fn: Monotonic clock callable returning seconds as float.
            thread_safe: If True, guards state mutations with a threading.Lock.
            initial_tokens: Optional starting token balance (defaults to full capacity).
        """
        if (
            isinstance(capacity, bool)
            or not isinstance(capacity, (int, float))
            or math.isnan(capacity)
            or math.isinf(capacity)
            or capacity <= 0.0
        ):
            raise ValueError(f"capacity must be a finite number > 0, got {capacity!r}")

        if (
            isinstance(refill_rate, bool)
            or not isinstance(refill_rate, (int, float))
            or math.isnan(refill_rate)
            or math.isinf(refill_rate)
            or refill_rate <= 0.0
        ):
            raise ValueError(f"refill_rate must be a finite number > 0, got {refill_rate!r}")

        if not callable(clock_fn):
            raise TypeError("clock_fn must be callable")

        cap = float(capacity)
        rate = float(refill_rate)

        if initial_tokens is None:
            start_tokens = cap
        else:
            if (
                isinstance(initial_tokens, bool)
                or not isinstance(initial_tokens, (int, float))
                or math.isnan(initial_tokens)
                or math.isinf(initial_tokens)
                or initial_tokens < 0.0
                or initial_tokens > cap
            ):
                raise ValueError(
                    f"initial_tokens must be between 0 and capacity ({cap}), got {initial_tokens!r}"
                )
            start_tokens = float(initial_tokens)

        self._capacity: float = cap
        self._refill_rate: float = rate
        self._inv_refill_rate: float = 1.0 / rate
        self._clock_fn: Callable[[], float] = clock_fn
        self._lock: Optional[threading.Lock] = threading.Lock() if thread_safe else None
        self._tokens: float = start_tokens
        self._last_timestamp: float = float(clock_fn())
        self._last_retry_after_sec: float = 0.0

    @property
    def capacity(self) -> float:
        """Return the maximum burst token capacity."""
        return self._capacity

    @property
    def refill_rate(self) -> float:
        """Return the steady token refill rate (tokens per second)."""
        return self._refill_rate

    @property
    def remaining_tokens(self) -> float:
        """Return the exact current remaining tokens after lazy refill."""
        if self._lock is not None:
            with self._lock:
                self._refill_unlocked(self._clock_fn())
                return self._tokens
        self._refill_unlocked(self._clock_fn())
        return self._tokens

    @property
    def last_retry_after_sec(self) -> float:
        """Return the retry_after_sec computed on the most recent request check."""
        return self._last_retry_after_sec

    def _refill_unlocked(self, now: float) -> None:
        """Replenish tokens lazily in O(1) arithmetic using elapsed monotonic time."""
        elapsed = now - self._last_timestamp
        if elapsed > 0.0:
            new_tokens = self._tokens + elapsed * self._refill_rate
            self._tokens = self._capacity if new_tokens >= self._capacity else new_tokens
            self._last_timestamp = now
        elif elapsed < 0.0:
            # Guard against non-monotonic clock regression without losing tokens
            self._last_timestamp = now

    @staticmethod
    def _validate_cost(tokens: float) -> float:
        """Validate requested token cost against numerical boundary errors."""
        if (
            isinstance(tokens, bool)
            or not isinstance(tokens, (int, float))
            or math.isnan(tokens)
            or math.isinf(tokens)
            or tokens <= 0.0
        ):
            raise ValueError(f"Requested tokens must be a finite number > 0, got {tokens!r}")
        return float(tokens)

    def allow_request(self, tokens: float = 1.0) -> bool:
        """Attempt to consume `tokens` in O(1) time.

        Updates `last_retry_after_sec` to 0.0 if allowed, or the exact wait time
        in seconds until `tokens` become available if rejected.
        """
        cost = (
            1.0
            if tokens == 1.0 and type(tokens) is float
            else self._validate_cost(tokens)
        )
        lock = self._lock
        if lock is not None:
            with lock:
                now = self._clock_fn()
                elapsed = now - self._last_timestamp
                if elapsed > 0.0:
                    replenished = self._tokens + elapsed * self._refill_rate
                    self._tokens = (
                        self._capacity if replenished >= self._capacity else replenished
                    )
                    self._last_timestamp = now
                elif elapsed < 0.0:
                    self._last_timestamp = now

                if self._tokens >= cost:
                    self._tokens -= cost
                    self._last_retry_after_sec = 0.0
                    return True

                if cost > self._capacity:
                    self._last_retry_after_sec = math.inf
                else:
                    deficit = cost - self._tokens
                    self._last_retry_after_sec = deficit * self._inv_refill_rate
                return False

        now = self._clock_fn()
        elapsed = now - self._last_timestamp
        if elapsed > 0.0:
            replenished = self._tokens + elapsed * self._refill_rate
            self._tokens = (
                self._capacity if replenished >= self._capacity else replenished
            )
            self._last_timestamp = now
        elif elapsed < 0.0:
            self._last_timestamp = now

        if self._tokens >= cost:
            self._tokens -= cost
            self._last_retry_after_sec = 0.0
            return True

        if cost > self._capacity:
            self._last_retry_after_sec = math.inf
        else:
            deficit = cost - self._tokens
            self._last_retry_after_sec = deficit * self._inv_refill_rate
        return False

    def evaluate(self, tokens: float = 1.0) -> RateLimitDecision:
        """Consume `tokens` if available and return a detailed RateLimitDecision."""
        cost = self._validate_cost(tokens)
        if self._lock is not None:
            with self._lock:
                return self._evaluate_unlocked(cost)
        return self._evaluate_unlocked(cost)

    def _evaluate_unlocked(self, cost: float) -> RateLimitDecision:
        """Internal O(1) evaluation returning a full RateLimitDecision."""
        self._refill_unlocked(self._clock_fn())
        if self._tokens >= cost:
            self._tokens -= cost
            self._last_retry_after_sec = 0.0
            return RateLimitDecision(
                allowed=True,
                remaining_tokens=self._tokens,
                retry_after_sec=0.0,
                capacity=self._capacity,
                refill_rate=self._refill_rate,
            )

        retry_after = (
            math.inf
            if cost > self._capacity
            else (cost - self._tokens) * self._inv_refill_rate
        )
        self._last_retry_after_sec = retry_after
        return RateLimitDecision(
            allowed=False,
            remaining_tokens=self._tokens,
            retry_after_sec=retry_after,
            capacity=self._capacity,
            refill_rate=self._refill_rate,
        )

    def retry_after_sec(self, tokens: float = 1.0) -> float:
        """Calculate exact wait time in seconds until `tokens` will be available."""
        cost = self._validate_cost(tokens)
        if self._lock is not None:
            with self._lock:
                self._refill_unlocked(self._clock_fn())
                if cost > self._capacity:
                    return math.inf
                if self._tokens >= cost:
                    return 0.0
                return (cost - self._tokens) * self._inv_refill_rate

        self._refill_unlocked(self._clock_fn())
        if cost > self._capacity:
            return math.inf
        if self._tokens >= cost:
            return 0.0
        return (cost - self._tokens) * self._inv_refill_rate
