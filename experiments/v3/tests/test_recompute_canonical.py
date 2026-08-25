"""Tests for the canonical External300 recomputation outputs.

Enforces that External300_CANONICAL_METRICS.json matches the sealed-run blob
values, dual-scope latency exists, and McNemar is never displayed as "p=0".
"""
from __future__ import annotations

import json
from pathlib import Path

V3 = Path(__file__).resolve().parents[1]
RESULTS_EXT300 = V3 / "results" / "external300"
KF = "KAFarmTwin-TypedRepair"
SA = "SingleAgent-AllTools"


def _canonical() -> dict:
    p = RESULTS_EXT300 / "External300_CANONICAL_METRICS.json"
    assert p.exists(), f"missing {p}"
    return json.loads(p.read_text(encoding="utf-8"))


def test_canonical_metrics_exist_and_consistency_gate_passes():
    c = _canonical()
    gate = c.get("consistency_gate", {})
    assert gate.get("all_pass") is True, f"consistency gate failed: {gate.get('failed')}"
    assert c["verification"]["records"] == 600
    assert c["verification"]["tasks"] == 300
    assert c["sealed_raw_sha256"] == (
        "b52f00c4bee3b43723689c3556300e0754a8ab9564b96341d05e88b591d40d91")


def test_core_headline_numbers_match_sealed_blob():
    c = _canonical()
    kf, sa = c["by_method"][KF], c["by_method"][SA]
    assert abs(kf["overall_cvsr"] - 0.7167) < 5e-4
    assert abs(sa["overall_cvsr"] - 0.4800) < 5e-4
    assert abs(kf["fatal_violation_rate"] - 0.0) < 1e-9
    assert abs(sa["fatal_violation_rate"] - 0.25) < 1e-9
    # token/cost must not be conflated
    assert kf["tokens_total"] == 668_769
    assert sa["tokens_total"] == 472_722
    assert abs(kf["cost_total_usd"] - 0.1035) < 5e-4
    assert abs(sa["cost_total_usd"] - 0.0854) < 5e-4


def test_token_and_cost_ratios():
    c = _canonical()
    assert abs(c["token_ratio_kf_over_sa"] - 1.4147) < 5e-3
    assert abs(c["cost_ratio_kf_over_sa"] - 1.2119) < 5e-3


def test_paired_statistics():
    s = _canonical()["paired_statistics"]
    assert s["n_paired_tasks"] == 300
    assert abs(s["point_delta"] - 0.2367) < 5e-4
    assert abs(s["ci95_low"] - 0.1833) < 5e-4 and abs(s["ci95_high"] - 0.29) < 5e-4
    assert (s["mcnemar_b"], s["mcnemar_c"]) == (77, 6)


def test_mcnemar_never_displayed_as_p_zero():
    disp = _canonical()["paired_statistics"]["mcnemar_p_display"]
    assert not disp.startswith("p=0"), f"McNemar displayed as p=0: {disp!r}"
    if float(_canonical()["paired_statistics"]["mcnemar_p_float"]) < 1e-6:
        assert disp.startswith("p<1e-6"), disp
        assert "exact tail" in disp, disp


def test_dual_scope_latency_present_for_both_methods():
    c = _canonical()
    for m in (KF, SA):
        lat = c["by_method"][m]["latency"]
        assert set(lat) >= {"all_tasks", "llm_invoking_tasks"}, lat.keys()
        assert lat["all_tasks"]["n"] == 300
        assert lat["all_tasks"]["include_zero_latency_deterministic_tasks"] is True
        assert lat["llm_invoking_tasks"]["include_zero_latency_deterministic_tasks"] is False
    # llm-only scope: KF 240 LLM tasks vs SA 180
    assert c["by_method"][KF]["latency"]["llm_invoking_tasks"]["n"] == 240
    assert c["by_method"][SA]["latency"]["llm_invoking_tasks"]["n"] == 180
    # canonical llm-scope values from sealed rerun
    assert abs(c["by_method"][SA]["latency"]["llm_invoking_tasks"]["p50_s"] - 6.72) < 5e-3
    assert abs(c["by_method"][KF]["latency"]["llm_invoking_tasks"]["p50_s"] - 2.82) < 5e-3


def test_quantile_algorithm_disclosed():
    assert "nearest-rank" in _canonical()["quantile_algorithm"]
