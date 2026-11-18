from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

def solve_max_net_payout(intervals: list[tuple[int, int, str]], fee_bps: int) -> str:
    """
    Finds the maximum total net amount achievable by selecting a subset of mutually non-overlapping intervals.
    Each interval is (start_time, end_time, gross_amount_str).
    fee_bps: basis points of gross_amount (10000 bps = 100%).
    Returns the maximum net amount formatted to 2 decimal places as a string.
    """
    if not intervals:
        return "0.00"

    parsed_intervals = []
    for start, end, gross_str in intervals:
        gross = Decimal(gross_str)
        # fee = gross * fee_bps / 10000
        fee = (gross * Decimal(fee_bps)) / Decimal(10000)
        net = gross - fee
        parsed_intervals.append((start, end, net))

    # Sort intervals by end time
    parsed_intervals.sort(key=lambda x: x[1])

    n = len(parsed_intervals)
    # DP array or table to store max net payout up to interval i
    # Since n can be small or moderate, let's use binary search for previous non-overlapping interval.
    
    # We can use an array of end times for binary search
    end_times = [iv[1] for iv in parsed_intervals]

    import bisect

    # dp[i] = max net amount using a subset of the first i intervals
    # Alternatively, let's compute dp iteratively.
    # To find the latest interval that finishes before or at start time of current interval i:
    # bisect_right on end_times for current_start gives index where end <= current_start.
    
    dp = [Decimal('0.00')] * n
    for i in range(n):
        start, end, net = parsed_intervals[i]
        inclusion_net = net
        
        # Find latest interval ending <= start
        # bisect_left with a tuple or custom search
        # Since end_times is sorted, we can search in end_times up to i
        idx = bisect.bisect_right(end_times, start, 0, i)
        if idx > 0:
            inclusion_net += dp[idx - 1]
        
        if i > 0:
            dp[i] = max(dp[i - 1], inclusion_net)
        else:
            dp[i] = inclusion_net

    max_net = dp[-1] if n > 0 else Decimal('0.00')
    
    # Format to 2 decimal places using ROUND_HALF_UP or standard quantize
    quantized = max_net.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return f"{quantized:.2f}"

def export_schedule_report(report_path: Path, summary_text: str) -> None:
    """
    Writes summary_text to report_path.
    """
    report_path.write_text(summary_text, encoding='utf-8')
