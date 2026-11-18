from decimal import Decimal, ROUND_HALF_UP
import bisect
from pathlib import Path


def solve_max_net_payout(intervals: list[tuple[int, int, str]], fee_bps: int) -> str:
    """
    Compute the maximum total net amount of non-overlapping intervals using
    O(N log N) bisect DP.
    
    Args:
        intervals: List of tuples (start_time, end_time, gross_amount_str)
        fee_bps: Basis points fee (10000 bps = 100%)
        
    Returns:
        String representation of the maximum net payout rounded to 2 decimal places.
    """
    if not intervals:
        return "0.00"

    fee_divisor = Decimal("10000")
    fee_rate = Decimal(fee_bps) / fee_divisor

    # Pre-calculate net amounts and sort intervals by end time
    processed = []
    for start, end, gross_str in intervals:
        gross = Decimal(gross_str)
        fee = (gross * fee_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        net = (gross - fee).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        processed.append((start, end, net))

    # Sort by end time
    sorted_intervals = sorted(processed, key=lambda x: x[1])
    ends = [iv[1] for iv in sorted_intervals]

    n = len(sorted_intervals)
    dp = [Decimal("0.00")] * (n + 1)

    for i in range(1, n + 1):
        start, end, net = sorted_intervals[i - 1]
        
        # Find latest non-overlapping interval using bisect_right
        # bisect_right returns count of intervals with end <= start
        p = bisect.bisect_right(ends, start)
        
        include_val = net + dp[p]
        exclude_val = dp[i - 1]
        
        dp[i] = max(include_val, exclude_val)

    max_payout = dp[n].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{max_payout:.2f}"


def export_schedule_report(report_path: Path, summary_text: str) -> None:
    """
    Export schedule report summary text to file with explicit UTF-8 encoding.
    """
    report_path.write_text(summary_text, encoding="utf-8")
