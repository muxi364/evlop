import unittest
from pathlib import Path
import tempfile
from interval_engine import solve_max_net_payout, export_schedule_report

class TestIntervalEngine(unittest.TestCase):

    def test_solve_max_net_payout_empty(self):
        self.assertEqual(solve_max_net_payout([], 100), "0.00")

    def test_solve_max_net_payout_single(self):
        # 100.00 gross, 100 bps (1%) fee -> net 99.00
        intervals = [(0, 10, "100.00")]
        self.assertEqual(solve_max_net_payout(intervals, 100), "99.00")

    def test_solve_max_net_payout_non_overlapping(self):
        intervals = [
            (0, 5, "50.00"),
            (5, 10, "60.00"),
            (10, 15, "70.00")
        ]
        # fee = 0 bps -> 50 + 60 + 70 = 180.00
        self.assertEqual(solve_max_net_payout(intervals, 0), "180.00")

    def test_solve_max_net_payout_overlapping(self):
        intervals = [
            (1, 4, "100.00"),
            (3, 5, "200.00"),
            (0, 9, "50.00")
        ]
        # 1-4 (net 90) and 3-5 overlap. Best single or non-overlapping.
        # If we pick (1, 4) and no other, or (3, 5). 
        # Let's test with fee_bps = 1000 (10%)
        # (1, 4): 100 -> 90
        # (3, 5): 200 -> 180
        # (0, 9): 50 -> 45
        # Max is 180.00
        self.assertEqual(solve_max_net_payout(intervals, 1000), "180.00")

    def test_export_schedule_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "report.txt"
            export_schedule_report(p, "Test summary text.")
            self.assertTrue(p.exists())
            self.assertEqual(p.read_text(encoding='utf-8'), "Test summary text.")

if __name__ == '__main__':
    unittest.main()
