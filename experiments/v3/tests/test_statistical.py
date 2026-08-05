"""Tests for statistical_tests.py — bootstrap CI, sign test, Pareto."""

from __future__ import annotations

import sys
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1] / "evaluators"
sys.path.insert(0, str(EVAL))

from statistical_tests import paired_bootstrap_cvsr, sign_test, wilcoxon_paired, pareto_dominates  # noqa: E402


def test_paired_bootstrap_ci_lower_bound_gt0_when_clearly_better():
    # Method passes 10/10, baseline 0/10 -> CI lower bound should be > 0
    method = [1.0] * 10
    baseline = [0.0] * 10
    res = paired_bootstrap_cvsr(method, baseline, n_boot=2000, seed=42)
    assert res["mean_diff"] == 1.0
    assert res["ci_lower_gt_0"] is True
    assert res["ci_low"] > 0


def test_paired_bootstrap_ci_not_gt0_when_tied():
    method = [1.0, 0.0, 1.0, 0.0, 1.0]
    baseline = [1.0, 0.0, 1.0, 0.0, 1.0]
    res = paired_bootstrap_cvsr(method, baseline, n_boot=2000, seed=42)
    assert res["mean_diff"] == 0.0
    assert res["ci_lower_gt_0"] is False


def test_sign_test():
    method = [True, True, True, True, True]
    baseline = [False, False, False, False, True]
    res = sign_test(method, baseline)
    assert res["better"] == 4
    assert res["method_superior"] is True


def test_wilcoxon_paired():
    a = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    b = [x - 2.0 for x in a]  # consistently better -> low p
    res = wilcoxon_paired(a, b)
    assert res["p_value"] < 0.1


def test_pareto_dominates():
    assert pareto_dominates({"cvsr": 0.9, "cost": 1.0, "latency_p95": 100.0},
                            {"cvsr": 0.8, "cost": 1.2, "latency_p95": 200.0})
    assert not pareto_dominates({"cvsr": 0.9, "cost": 2.0, "latency_p95": 100.0},
                                {"cvsr": 0.8, "cost": 1.2, "latency_p95": 200.0})  # cost worse
