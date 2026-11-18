"""
Head-to-Head Evaluation of Weak Model (`flash_lite`) Control (No EVLOP)
vs. Weak Model (`flash_lite`) Treatment (With EVLOP Scaffold).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import time


def _load_module(mod_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(mod_name, str(file_path))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def evaluate_both() -> dict:
    base = Path(__file__).resolve().parent
    ctrl_path = base / "control_no_evlop" / "interval_engine.py"
    treat_path = base / "treatment_with_evlop" / "interval_engine.py"

    ctrl_mod = _load_module("ctrl_interval", ctrl_path)
    treat_mod = _load_module("treat_interval", treat_path)

    # 1. Per-Interval Half-Cent Penny-Rounding Compliance Test:
    # Two non-overlapping intervals of "10.00" with 25 bps (0.25%) fee:
    # Each interval fee = 10.00 * 25 / 10000 = 0.025 -> quantized ROUND_HALF_UP = 0.03 -> net = 9.97.
    # Total across 2 intervals MUST be 9.97 + 9.97 = "19.94" (NOT "19.95" from unquantized float/Decimal accumulation!).
    penny_intervals = [(0, 10, "10.00"), (10, 20, "10.00")]
    ctrl_penny = ctrl_mod.solve_max_net_payout(penny_intervals, 25)
    treat_penny = treat_mod.solve_max_net_payout(penny_intervals, 25)

    # 2. Multi-Interval Weighted DP Optimality Test:
    dp_intervals = [
        (1, 4, "100.00"),
        (3, 5, "50.00"),
        (0, 6, "120.00"),
        (4, 7, "100.00"),
        (3, 8, "200.00"),
        (5, 9, "150.00"),
        (6, 10, "100.00"),
        (8, 11, "180.00"),
    ]
    ctrl_dp = ctrl_mod.solve_max_net_payout(dp_intervals, 1000)   # 10% fee
    treat_dp = treat_mod.solve_max_net_payout(dp_intervals, 1000)

    # 3. Code Structure & Top-Level Import Cleanliness Check:
    ctrl_src = ctrl_path.read_text(encoding="utf-8")
    treat_src = treat_path.read_text(encoding="utf-8")
    ctrl_clean_imports = "    import " not in ctrl_src
    treat_clean_imports = "    import " not in treat_src

    # 4. 5,000-Interval Scale Throughput Benchmark:
    scale_intervals = [(i * 2, i * 2 + 5, "19.95") for i in range(5000)]
    t0 = time.perf_counter()
    ctrl_mod.solve_max_net_payout(scale_intervals, 125)
    ctrl_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    t1 = time.perf_counter()
    treat_mod.solve_max_net_payout(scale_intervals, 125)
    treat_ms = round((time.perf_counter() - t1) * 1000.0, 2)

    ctrl_checks = [
        ctrl_penny == "19.94",
        ctrl_dp == "342.00",
        ctrl_clean_imports,
        ctrl_ms < 100.0,
    ]
    treat_checks = [
        treat_penny == "19.94",
        treat_dp == "342.00",
        treat_clean_imports,
        treat_ms < 100.0,
    ]

    report = {
        "weak_model_tier": "flash_lite",
        "control_no_evlop": {
            "adversarial_rubric_score_pct": round((sum(ctrl_checks) / len(ctrl_checks)) * 100.0, 2),
            "per_interval_penny_rounding_output": ctrl_penny,
            "per_interval_penny_rounding_passed": (ctrl_penny == "19.94"),
            "dp_optimality_passed": (ctrl_dp == "342.00"),
            "clean_top_level_imports": ctrl_clean_imports,
            "scale_5000_intervals_ms": ctrl_ms,
        },
        "treatment_with_evlop": {
            "adversarial_rubric_score_pct": round((sum(treat_checks) / len(treat_checks)) * 100.0, 2),
            "per_interval_penny_rounding_output": treat_penny,
            "per_interval_penny_rounding_passed": (treat_penny == "19.94"),
            "dp_optimality_passed": (treat_dp == "342.00"),
            "clean_top_level_imports": treat_clean_imports,
            "scale_5000_intervals_ms": treat_ms,
        },
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


if __name__ == "__main__":
    evaluate_both()
