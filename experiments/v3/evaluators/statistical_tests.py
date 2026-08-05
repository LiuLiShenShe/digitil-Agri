"""Statistical tests for the v3 evaluator.

Paired per-task bootstrap for the CVSR difference, sign test / McNemar,
Wilcoxon signed-rank, and budget-normalized / Pareto checks.
"""

from __future__ import annotations

import math
import random
from statistics import median
from typing import Any, Sequence


def paired_bootstrap_cvsr(method_flags: Sequence[float], baseline_flags: Sequence[float],
                          n_boot: int = 5000, seed: int = 20260804, alpha: float = 0.05) -> dict[str, Any]:
    """Paired per-task bootstrap 95% CI for mean(CVSR_method - CVSR_baseline).

    method_flags / baseline_flags: per-task per-run CVSR 0/1 flags, PAIRED by index.
    Returns {mean_diff, ci_low, ci_high, ci_lower_gt_0: bool, p_value}.
    """
    assert len(method_flags) == len(baseline_flags), "flags must be paired per task/run"
    diffs = [m - b for m, b in zip(method_flags, baseline_flags)]
    n = len(diffs)
    if n == 0:
        return {"mean_diff": 0.0, "ci_low": 0.0, "ci_high": 0.0, "ci_lower_gt_0": False, "p_value": 1.0}
    rng = random.Random(seed)
    mean_diff = sum(diffs) / n
    boot = []
    for _ in range(n_boot):
        sample = [rng.choice(diffs) for _ in range(n)]
        boot.append(sum(sample) / n)
    boot.sort()
    lo = int(round((alpha / 2) * n_boot))
    hi = int(round((1 - alpha / 2) * n_boot))
    ci_low = boot[max(0, lo - 1)]
    ci_high = boot[min(n_boot - 1, hi - 1)]
    # p-value: fraction of bootstrap means <= 0 (one-sided H0: diff <= 0)
    p_value = sum(1 for b in boot if b <= 0) / n_boot
    return {
        "mean_diff": round(mean_diff, 4),
        "ci_low": round(ci_low, 4),
        "ci_high": round(ci_high, 4),
        "ci_lower_gt_0": bool(ci_low > 0),
        "p_value": round(p_value, 4),
        "n_boot": n_boot,
        "n": n,
    }


def sign_test(method_flags: Sequence[bool], baseline_flags: Sequence[bool]) -> dict[str, Any]:
    """Sign test on paired CVSR flags (method strictly better / worse / tie)."""
    better = 0
    worse = 0
    tie = 0
    for m, b in zip(method_flags, baseline_flags):
        if m and not b:
            better += 1
        elif b and not m:
            worse += 1
        else:
            tie += 1
    n = better + worse
    p_value = _binom_tail(better, n) if n > 0 else 1.0
    return {"better": better, "worse": worse, "tie": tie, "p_value": round(p_value, 4),
            "method_superior": better > worse}


def _binom_tail(k: int, n: int) -> float:
    """P(X >= k) under Binomial(n, 0.5) — one-sided for the sign test."""
    from math import comb
    if n <= 0:
        return 1.0
    return sum(comb(n, i) * 0.5 ** n for i in range(k, n + 1))


def wilcoxon_paired(a: Sequence[float], b: Sequence[float]) -> dict[str, Any]:
    """Wilcoxon signed-rank test on paired continuous values (approximate)."""
    diffs = [x - y for x, y in zip(a, b)]
    nonzero = [d for d in diffs if d != 0]
    n = len(nonzero)
    if n < 3:
        return {"n": n, "w_stat": 0.0, "p_value": 1.0}
    ranks = {abs(d): (i + 1) for i, d in enumerate(sorted(nonzero, key=abs))}
    # handle ties approximately
    w_plus = sum(ranks[abs(d)] for d in nonzero if d > 0)
    mu = n * (n + 1) / 4
    var = n * (n + 1) * (2 * n + 1) / 24
    z = (w_plus - mu) / math.sqrt(var) if var > 0 else 0.0
    p = 2 * (1 - _normal_cdf(abs(z)))
    return {"n": n, "w_plus": w_plus, "z": round(z, 4), "p_value": round(p, 4)}


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def pareto_dominates(metric_a: dict[str, float], metric_b: dict[str, float]) -> bool:
    """True if A Pareto-dominates B on (cvsr, cost, latency): >= all, > at least one."""
    return (metric_a["cvsr"] >= metric_b["cvsr"] and
            metric_a["cost"] <= metric_b["cost"] and
            metric_a["latency_p95"] <= metric_b["latency_p95"] and
            (metric_a["cvsr"] > metric_b["cvsr"] or metric_a["cost"] < metric_b["cost"] or
             metric_a["latency_p95"] < metric_b["latency_p95"]))
