import unittest
from pathlib import Path
import tempfile
from interval_engine import solve_max_net_payout, export_schedule_report


class TestIntervalEngine(unittest.TestCase):
    def test_solve_max_net_payout_empty(self):
        self.assertEqual(solve_max_net_payout([], 100), "0.00")

    def test_solve_max_net_payout_basic(self):
        # (start, end, gross)
        intervals = [
            (0, 5, "100.00"),
            (3, 7, "200.00"),
            (5, 9, "150.00"),
        ]
        # fee_bps = 100 (1%)
        # 100 -> net 99.00
        # 200 -> net 198.00
        # 150 -> net 148.50
        # Non-overlapping: interval 0 (0-5, net 99.00) and interval 2 (5-9, net 148.50) => 99.00 + 148.50 = 247.50
        result = solve_max_net_payout(intervals, 100)
        self.assertEqual(result, "247.50")

    def test_solve_max_net_payout_single(self):
        intervals = [(1, 3, "50.50")]
        # 100 bps = 1%
        # 50.50 * 0.99 = 49.995 -> ROUND_HALF_UP to 50.00? Wait: 50.50 * 0.01 = 0.505 -> 0.51 fee -> 49.99 net
        result = solve_max_net_payout(intervals, 100)
        self.assertEqual(result, "49.99")

    def test_export_schedule_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.txt"
            summary = "Test summary report with Unicode: 🚀"
            export_schedule_report(path, summary)
            self.assertTrue(path.exists())
            content = path.read_text(encoding="utf-8")
            self.assertEqual(content, summary)


if __name__ == "__main__":
    unittest.main()
