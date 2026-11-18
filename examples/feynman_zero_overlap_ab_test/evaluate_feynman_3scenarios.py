"""
Independent Adversarial Evaluation across 3 Zero-Overlap Domains:
1. Compiler / Expression Evaluator (`expr_eval.py`)
2. Distributed Consistent Hash Ring (`hash_ring.py`)
3. Stateful TCP Stream Frame Codec (`stream_codec.py`)

Compares Weak Model (`flash_lite`) Control (No EVLOP) vs. Weak Model (`flash_lite`) Treatment (Feynman-EVLOP).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _score_suite(folder: Path, prefix: str) -> dict:
    expr_mod = _load_mod(f"{prefix}_expr", folder / "expr_eval.py")
    ring_mod = _load_mod(f"{prefix}_ring", folder / "hash_ring.py")
    codec_mod = _load_mod(f"{prefix}_codec", folder / "stream_codec.py")

    results: dict[str, bool] = {}
    details: dict[str, str] = {}

    # --- Scenario 1: Expression Evaluator ---
    # 1.1 Right-associative exponentiation: 2 ^ 3 ^ 2 == 2 ^ 9 == 512 (NOT 64 and NOT bitwise XOR 3!)
    try:
        v_exp = expr_mod.eval_expr("2 ^ 3 ^ 2")
        results["s1_right_assoc_exp"] = (v_exp == 512)
        details["s1_right_assoc_exp"] = f"got {v_exp!r} (expected 512)"
    except Exception as exc:
        results["s1_right_assoc_exp"] = False
        details["s1_right_assoc_exp"] = f"raised {type(exc).__name__}: {exc}"

    # 1.2 Short-circuit boolean evaluation: dead branch `10 / 0` must NOT be evaluated
    try:
        v_or = expr_mod.eval_expr("1 == 1 or 10 / 0 == 1")
        v_and = expr_mod.eval_expr("1 == 2 and 10 / 0 == 1")
        results["s1_short_circuit_guard"] = (v_or is True and v_and is False)
        details["s1_short_circuit_guard"] = f"got or={v_or!r}, and={v_and!r}"
    except Exception as exc:
        results["s1_short_circuit_guard"] = False
        details["s1_short_circuit_guard"] = f"raised {type(exc).__name__}: {exc}"

    # 1.3 Equality of comparison & unary precedence: `1 < 2 == True` and `-2 ^ 2 == -4`
    try:
        v_comp = expr_mod.eval_expr("1 < 2 == True")
        v_unary = expr_mod.eval_expr("-2 ^ 2")
        results["s1_comparison_equality_and_unary"] = (v_comp is True and v_unary == -4)
        details["s1_comparison_equality_and_unary"] = f"got comp={v_comp!r}, unary={v_unary!r}"
    except Exception as exc:
        results["s1_comparison_equality_and_unary"] = False
        details["s1_comparison_equality_and_unary"] = f"raised {type(exc).__name__}: {exc}"

    # --- Scenario 2: Consistent Hash Ring ---
    # 2.1 Distinct physical node replica deduplication
    try:
        ring = ring_mod.ConsistentHashRing(virtual_nodes=50)
        ring.add_node("node-A")
        ring.add_node("node-B")
        reps = ring.get_replicas("customer-key-42", 2)
        results["s2_distinct_physical_replicas"] = (len(reps) == 2 and len(set(reps)) == 2)
        details["s2_distinct_physical_replicas"] = f"got {reps!r}"
    except Exception as exc:
        results["s2_distinct_physical_replicas"] = False
        details["s2_distinct_physical_replicas"] = f"raised {type(exc).__name__}: {exc}"

    # 2.2 Requesting count > num_physical_nodes must clamp to distinct physical nodes without hanging
    try:
        ring2 = ring_mod.ConsistentHashRing(virtual_nodes=50)
        ring2.add_node("node-1")
        ring2.add_node("node-2")
        reps_clamped = ring2.get_replicas("any-key", 5)
        results["s2_clamp_when_count_exceeds_cluster"] = (
            len(reps_clamped) == 2 and set(reps_clamped) == {"node-1", "node-2"}
        )
        details["s2_clamp_when_count_exceeds_cluster"] = f"got {reps_clamped!r}"
    except Exception as exc:
        results["s2_clamp_when_count_exceeds_cluster"] = False
        details["s2_clamp_when_count_exceeds_cluster"] = f"raised {type(exc).__name__}: {exc}"

    # 2.3 Degenerate boundary: count=0 on non-empty ring and empty ring safety
    try:
        ring_deg = ring_mod.ConsistentHashRing(virtual_nodes=10)
        reps_empty = ring_deg.get_replicas("k", 3)
        ring_deg.add_node("node-1")
        ring_deg.add_node("node-2")
        reps_zero = ring_deg.get_replicas("k", 0)
        results["s2_degenerate_zero_and_empty_boundary"] = (reps_empty == [] and reps_zero == [])
        details["s2_degenerate_zero_and_empty_boundary"] = f"empty={reps_empty!r}, count0={reps_zero!r}"
    except Exception as exc:
        results["s2_degenerate_zero_and_empty_boundary"] = False
        details["s2_degenerate_zero_and_empty_boundary"] = f"raised {type(exc).__name__}: {exc}"

    # --- Scenario 3: Stateful TCP Stream Frame Codec ---
    # 3.1 1-byte-at-a-time extreme fragmentation
    try:
        codec = codec_mod.StreamFrameCodec()
        raw = b"feynman-stream-payload"
        encoded = codec.encode_frame(raw)
        collected = []
        for b in encoded:
            collected.extend(codec.feed_chunk(bytes([b])))
        results["s3_single_byte_fragmentation"] = (collected == [raw])
        details["s3_single_byte_fragmentation"] = f"got {collected!r}"
    except Exception as exc:
        results["s3_single_byte_fragmentation"] = False
        details["s3_single_byte_fragmentation"] = f"raised {type(exc).__name__}: {exc}"

    # 3.2 Coalesced multi-frame + split boundary in a single chunk
    try:
        codec2 = codec_mod.StreamFrameCodec()
        f1 = codec2.encode_frame(b"frame-1")
        f2 = codec2.encode_frame(b"frame-2")
        f3 = codec2.encode_frame(b"frame-3-tail")
        part1 = codec2.feed_chunk(f1 + f2 + f3[:5])
        part2 = codec2.feed_chunk(f3[5:])
        results["s3_coalesced_and_split_boundary"] = (
            part1 == [b"frame-1", b"frame-2"] and part2 == [b"frame-3-tail"]
        )
        details["s3_coalesced_and_split_boundary"] = f"part1={part1!r}, part2={part2!r}"
    except Exception as exc:
        results["s3_coalesced_and_split_boundary"] = False
        details["s3_coalesced_and_split_boundary"] = f"raised {type(exc).__name__}: {exc}"

    # 3.3 Zero-length payload frame
    try:
        codec3 = codec_mod.StreamFrameCodec()
        ef = codec3.encode_frame(b"")
        out = codec3.feed_chunk(ef)
        results["s3_empty_frame_payload"] = (out == [b""])
        details["s3_empty_frame_payload"] = f"got {out!r}"
    except Exception as exc:
        results["s3_empty_frame_payload"] = False
        details["s3_empty_frame_payload"] = f"raised {type(exc).__name__}: {exc}"

    # 4. Self-Generated Counter-Example Test Coverage (Did the agent test 2^3^2, 1/0 short-circuit, and 1-byte stream chunks?)
    test_src = (folder / "test_all_three.py").read_text(encoding="utf-8")
    has_feynman_tests = (
        ("512" in test_src)
        and ("1 / 0" in test_src or "1/0" in test_src)
        and ("bytes([b])" in test_src)
    )
    results["s4_adversarial_counter_example_test_coverage"] = has_feynman_tests
    details["s4_adversarial_counter_example_test_coverage"] = f"has_all_3_feynman_counter_examples={has_feynman_tests}"

    passed_cnt = sum(1 for v in results.values() if v)
    total_cnt = len(results)
    return {
        "score_pct": round((passed_cnt / total_cnt) * 100.0, 2),
        "passed": passed_cnt,
        "total": total_cnt,
        "results": results,
        "details": details,
    }


def main() -> None:
    base = Path(__file__).resolve().parent
    ctrl_res = _score_suite(base / "control_no_evlop", "ctrl")
    treat_res = _score_suite(base / "treatment_feynman_evlop", "treat")
    summary = {
        "weak_model": "flash_lite",
        "domain_overlap_with_prior_genes": "0% (Zero-Overlap Unseen Domains)",
        "control_no_evlop": ctrl_res,
        "treatment_feynman_evlop": treat_res,
        "net_gain_pct": round(treat_res["score_pct"] - ctrl_res["score_pct"], 2),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
