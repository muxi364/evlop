"""High-frequency streaming sliding-window analytics using O(1) monotonic deques."""

from __future__ import annotations

from collections import deque


class SlidingWindowStats:
    """Compute O(1) amortized sliding-window statistics over a time-ordered stream.

    Maintains a primary timestamp-value deque alongside monotonic minimum and
    maximum deques and a running sum so that both event ingestion and window
    queries execute in O(1) amortized time without scanning the window.
    """

    def __init__(self, window_size_sec: float) -> None:
        """Initialize the sliding window with a positive duration in seconds."""
        if window_size_sec <= 0.0:
            raise ValueError("window_size_sec must be strictly positive")
        self.window_size_sec: float = float(window_size_sec)
        self._events: deque[tuple[float, float]] = deque()
        self._min_deque: deque[tuple[float, float]] = deque()
        self._max_deque: deque[tuple[float, float]] = deque()
        self._running_sum: float = 0.0

    def _evict_expired(self, cutoff: float) -> None:
        """Evict all events with timestamps at or before the expiration cutoff."""
        events = self._events
        while events and events[0][0] <= cutoff:
            _, expired_val = events.popleft()
            self._running_sum -= expired_val

        min_deque = self._min_deque
        while min_deque and min_deque[0][0] <= cutoff:
            min_deque.popleft()

        max_deque = self._max_deque
        while max_deque and max_deque[0][0] <= cutoff:
            max_deque.popleft()

        if not events:
            self._running_sum = 0.0

    def add_event(self, timestamp: float, value: float) -> None:
        """Record a streaming event and evict expired entries in O(1) amortized time."""
        entry = ( timestamp, value )
        self._events.append(entry)
        self._running_sum += value

        min_deque = self._min_deque
        while min_deque and min_deque[-1][1] >= value:
            min_deque.pop()
        min_deque.append(entry)

        max_deque = self._max_deque
        while max_deque and max_deque[-1][1] <= value:
            max_deque.pop()
        max_deque.append(entry)

        self._evict_expired(timestamp - self.window_size_sec)

    def get_stats(self, now: float) -> dict[str, float]:
        """Return count, sum, mean, min, and max for the active window at `now`."""
        self._evict_expired(now - self.window_size_sec)
        count = len(self._events)
        if count == 0:
            return {
                "count": 0.0,
                "sum": 0.0,
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
            }
        total = self._running_sum
        return {
            "count": float(count),
            "sum": total,
            "mean": total / count,
            "min": self._min_deque[0][1],
            "max": self._max_deque[0][1],
        }
