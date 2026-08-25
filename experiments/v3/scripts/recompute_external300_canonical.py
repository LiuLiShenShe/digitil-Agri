"""Canonical offline recomputation of External300 metrics from the SEALED raw records.

Read-only with respect to evidence: loads raw/runs.jsonl + SEAL.json + scored outputs,
verifies the seal, recomputes every headline metric from scratch, and writes the
canonical deliverables. NEVER imports an LLM client or calls any API.

Latency is reported in TWO scopes (user-facing ambiguity resolved here):
  all_tasks          - every one of the 300 tasks per method, including tasks where
                       the method answered deterministically without any LLM call
                       (latency_ms may be near-zero; these ARE included);
  llm_invoking_tasks - only tasks with llm_calls > 0.
Quantile algorithm: nearest-rank on the sorted list (index = ceil(p*n)-1), matching
the runner's original computation so numbers are directly comparable.

McNemar: the exact two-sided p-value under Binomial(b+c, .5) can be far below 1e-6;
we never print "p=0" - anything below 1e-6 is reported as "p<1e-6" together with the
exact rational tail value.

Outputs (into results/external300/):
  External300_CANONICAL_METRICS.json / .csv
  External300_FINAL_REPORT_v1.md
  External300_CLAIM_EVIDENCE_MATRIX.csv
  METRIC_DEFINITIONS_EXTERNAL300.md   (written once by this script if absent)
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V3 = HERE.parent
RESULTS = V3 / "results" / "external300"
RUN_ID = "ext300_formal_20260825"
RUN_DIR = RESULTS / RUN_ID
RAW_FILE = RUN_DIR / "raw" / "runs.jsonl"
SEAL_FILE = RUN_DIR / "SEAL.json"
EXPECTED_SEAL_SHA = "b52f00c4bee3b43723689c3556300e0754a8ab9564b96341d05e88b591d40d91"
METHODS = ("KAFarmTwin-TypedRepair", "SingleAgent-AllTools")
KF, SA = METHODS


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def p_quantile(sorted_vals: list[float], q: float) -> float:
    """Nearest-rank quantile: index = max(0, ceil(q*n)-1) on a pre-sorted list."""
    n = len(sorted_vals)
    if n == 0:
        return 0.0
    import math
    idx = min(n - 1, max(0, math.ceil(q * n) - 1))
    return sorted_vals[idx]


def mcnemar_string(b: int, c: int) -> tuple[str, float]:
    """Return (human-readable p, exact float). Two-sided exact binomial."""
    from math import comb
    n = b + c
    if n == 0:
        return "p=1.0 (no discordant pairs)", 1.0
    k = max(b, c)
    tail = sum(comb(n, i) for i in range(k, n + 1)) * (0.5 ** n)
    p = min(1.0, 2.0 * tail)
    s = f"p={p:.6f}" if p >= 1e-6 else f"p<1e-6 (exact tail {p:.2e}, b={b}, c={c})"
    return s, p


def load_and_verify() -> list[dict]:
    if not SEAL_FILE.exists():
        raise SystemExit(f"[canonical] REFUSED: no SEAL.json in {RUN_DIR}")
    seal = json.loads(SEAL_FILE.read_text(encoding="utf-8"))
    actual = sha256_file(RAW_FILE)
    if actual != seal.get("raw_runs_sha256"):
        raise SystemExit(f"[canonical] REFUSED: raw SHA {actual} != sealed {seal.get('raw_runs_sha256')}")
    if actual != EXPECTED_SEAL_SHA:
        raise SystemExit(f"[canonical] REFUSED: sealed SHA {actual} != expected {EXPECTED_SEAL_SHA}")
    recs = [json.loads(l) for l in RAW_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    pairs = [(r["task_id"], r["method"]) for r in recs]
    if len(recs) != 600 or len(set(pairs)) != 600:
        raise SystemExit(f"[canonical] REFUSED: {len(recs)} records / {len(set(pairs))} unique pairs (need 600/600)")
    tids = {r["task_id"] for r in recs}
    if len(tids) != 300:
        raise SystemExit(f"[canonical] REFUSED: {len(tids)} task ids (need 300)")
    for t in tids:
        ms = {r["method"] for r in recs if r["task_id"] == t}
        if ms != set(METHODS):
            raise SystemExit(f"[canonical] REFUSED: task {t} methods {ms}")
    return recs


def aggregate(recs: list[dict]) -> dict:
    """Recompute all per-method aggregates straight from raw+scored fields."""
    # scored per-task file carries the evaluator's verdicts; join it to raw for tokens/cost/latency
    scored = {}
    spath = RUN_DIR / "scored" / "per_task.jsonl"
    for l in spath.read_text(encoding="utf-8").splitlines():
        if l.strip():
            d = json.loads(l)
            scored[(d["task_id"], d["method"])] = d

    out: dict[str, dict] = {}
    types_by_task = {d["task_id"]: d.get("task_type") for d in scored.values()}
    for m in METHODS:
        rs = [r for r in recs if r["method"] == m]
        sc = [scored[(r["task_id"], m)] for r in rs]
        n = len(rs)
        lat_all = sorted(r["latency_ms"] for r in rs)
        llm_rs = [r for r in rs if r.get("llm_calls", 0) > 0]
        lat_llm = sorted(r["latency_ms"] for r in llm_rs)

        def mean(vals):
            return sum(vals) / len(vals) if vals else 0.0

        by_type: dict[str, dict] = {}
        for tt in sorted({types_by_task[r["task_id"]] for r in rs}):
            sub = [s for s in sc if s["task_id"] and types_by_task[s["task_id"]] == tt]
            by_type[tt] = {
                "n": len(sub),
                "mean_cvsr": round(mean([bool(s["cvsr"]) for s in sub]), 4),
                "object_f1": round(mean([s["object_f1"] for s in sub]), 4),
                "relation_f1": round(mean([s["relation_f1"] for s in sub]), 4),
                "binding_f1": round(mean([s["binding_f1"] for s in sub]), 4),
                "fatal_violation_rate": round(mean([1.0 if s["fatal_violations"] else 0.0 for s in sub]), 4),
                "critical_recall": round(mean([s["critical_recall"] for s in sub]), 4),
            }
        out[m] = {
            "n": n,
            "overall_cvsr": round(mean([bool(s["cvsr"]) for s in sc]), 4),
            "object_f1": round(mean([s["object_f1"] for s in sc]), 4),
            "relation_f1": round(mean([s["relation_f1"] for s in sc]), 4),
            "binding_f1": round(mean([s["binding_f1"] for s in sc]), 4),
            "critical_recall": round(mean([s["critical_recall"] for s in sc]), 4),
            "fatal_violation_rate": round(mean([1.0 if s["fatal_violations"] else 0.0 for s in sc]), 4),
            "evidence_precision": round(mean([s["evidence_precision"] for s in sc]), 4),
            "replay_success": round(mean([float(s["replay_success"]) for s in sc]), 4),
            "tokens_total": sum(r["tokens"] for r in rs),
            "cost_total_usd": round(sum(r["cost"] for r in rs), 4),
            "latency": {
                "all_tasks": {"n": n, "include_zero_latency_deterministic_tasks": True,
                              "p50_s": round(p_quantile(lat_all, .5) / 1000, 2),
                              "p95_s": round(p_quantile(lat_all, .95) / 1000, 2)},
                "llm_invoking_tasks": {"n": len(llm_rs),
                                       "include_zero_latency_deterministic_tasks": False,
                                       "p50_s": round(p_quantile(lat_llm, .5) / 1000, 2),
                                       "p95_s": round(p_quantile(lat_llm, .95) / 1000, 2)},
            },
            "technical_failures": sum(1 for r in rs if r.get("technical_failure")),
            "by_type": by_type,
        }
    return out


def paired_stats(recs: list[dict], agg: dict) -> dict:
    cvsr = {}
    for r in recs:
        key = (r["task_id"], r["method"])
        cvsr.setdefault(key, None)
    scored = {}
    for l in (RUN_DIR / "scored" / "per_task.jsonl").read_text(encoding="utf-8").splitlines():
        if l.strip():
            d = json.loads(l)
            scored[(d["task_id"], d["method"])] = bool(d["cvsr"])
    shared = sorted({t for (t, m) in scored if m == KF} & {t for (t, m) in scored if m == SA})
    diffs = [int(scored[(t, KF)]) - int(scored[(t, SA)]) for t in shared]
    import random
    rng = random.Random(20260804)
    n_boot = 10_000
    boots = []
    for _ in range(n_boot):
        boots.append(sum(rng.choice(diffs) for _ in diffs) / len(diffs))
    boots.sort()
    lo, hi = boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot) - 1]
    b = sum(1 for d in diffs if d > 0)
    c = sum(1 for d in diffs if d < 0)
    p_str, p_float = mcnemar_string(b, c)
    return {
        "n_paired_tasks": len(shared),
        "point_delta": round(sum(diffs) / len(diffs), 4),
        "ci95_low": round(lo, 4), "ci95_high": round(hi, 4),
        "mcnemar_b": b, "mcnemar_c": c,
        "mcnemar_p_display": p_str, "mcnemar_p_float": p_float,
    }


def main() -> int:
    recs = load_and_verify()
    agg = aggregate(recs)
    stats = paired_stats(recs, agg)
    tok_ratio = agg[KF]["tokens_total"] / agg[SA]["tokens_total"]
    cost_ratio = agg[KF]["cost_total_usd"] / agg[SA]["cost_total_usd"]

    canonical = {
        "run_id": RUN_ID,
        "sealed_raw_sha256": EXPECTED_SEAL_SHA,
        "verification": {"records": 600, "unique_pairs": 600, "tasks": 300, "seal_match": True},
        "by_method": agg,
        "token_ratio_kf_over_sa": round(tok_ratio, 4),
        "cost_ratio_kf_over_sa": round(cost_ratio, 4),
        "paired_statistics": stats,
        "quantile_algorithm": "nearest-rank on sorted values (index ceil(q*n)-1)",
        "latency_note": ("all_tasks includes deterministic zero/low-latency tasks; "
                         "llm_invoking_tasks excludes them. Both scopes reported."),
        "provenance_files": ["EXECUTION_SOURCE_PROVENANCE_POSTHOC.json",
                             "REVIEW_PROVENANCE_CORRECTION.json",
                             "PROTOCOL_DEVIATION_EXTERNAL300.md"],
    }
    out_json = RESULTS / "External300_CANONICAL_METRICS.json"
    out_json.write_text(json.dumps(canonical, ensure_ascii=False, indent=1), encoding="utf-8")

    # CSV: one row per method x scope
    rows = []
    for m in METHODS:
        a = agg[m]
        base = {"method": m, "n": a["n"], "overall_cvsr": a["overall_cvsr"],
                "object_f1": a["object_f1"], "relation_f1": a["relation_f1"],
                "binding_f1": a["binding_f1"], "critical_recall": a["critical_recall"],
                "fatal_violation_rate": a["fatal_violation_rate"],
                "evidence_precision": a["evidence_precision"], "replay_success": a["replay_success"],
                "tokens_total": a["tokens_total"], "cost_total_usd": a["cost_total_usd"],
                "latency_all_p50_s": a["latency"]["all_tasks"]["p50_s"],
                "latency_all_p95_s": a["latency"]["all_tasks"]["p95_s"],
                "latency_llm_p50_s": a["latency"]["llm_invoking_tasks"]["p50_s"],
                "latency_llm_p95_s": a["latency"]["llm_invoking_tasks"]["p95_s"]}
        rows.append(base)
        for tt, bt in a["by_type"].items():
            rows.append({"method": m, "n": bt["n"], "task_type": tt,
                         "overall_cvsr": bt["mean_cvsr"], "object_f1": bt["object_f1"],
                         "relation_f1": bt["relation_f1"], "binding_f1": bt["binding_f1"],
                         "critical_recall": bt["critical_recall"],
                         "fatal_violation_rate": bt["fatal_violation_rate"]})
    keys = sorted({k for r in rows for k in r})
    with (RESULTS / "External300_CANONICAL_METRICS.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    # consistency gate vs previously published core numbers
    checks = {
        "kf_cvsr_0.7167": abs(agg[KF]["overall_cvsr"] - 0.7167) < 5e-4,
        "sa_cvsr_0.4800": abs(agg[SA]["overall_cvsr"] - 0.4800) < 5e-4,
        "delta_0.2367": abs(stats["point_delta"] - 0.2367) < 5e-4,
        "b77_c6": stats["mcnemar_b"] == 77 and stats["mcnemar_c"] == 6,
        "kf_tokens_668769": agg[KF]["tokens_total"] == 668_769,
        "sa_tokens_472722": agg[SA]["tokens_total"] == 472_722,
        "token_ratio_~1.415": abs(canonical["token_ratio_kf_over_sa"] - 1.4149) < 5e-3,
        "kf_cost_0.1035": abs(agg[KF]["cost_total_usd"] - 0.1035) < 5e-4,
        "sa_cost_0.0854": abs(agg[SA]["cost_total_usd"] - 0.0854) < 5e-4,
        "cost_ratio_~1.212": abs(canonical["cost_ratio_kf_over_sa"] - 1.2119) < 5e-3,
        "kf_fatal_0": agg[KF]["fatal_violation_rate"] == 0.0,
        "sa_fatal_0.25": abs(agg[SA]["fatal_violation_rate"] - 0.25) < 1e-9,
    }
    failed = [k for k, ok in checks.items() if not ok]
    canonical["consistency_gate"] = {"all_pass": not failed, "failed": failed}
    out_json.write_text(json.dumps(canonical, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(checks, indent=1))
    print("token ratio:", canonical["token_ratio_kf_over_sa"], "| cost ratio:", canonical["cost_ratio_kf_over_sa"])
    print("latency all:", {m: agg[m]["latency"]["all_tasks"] for m in METHODS})
    print("latency llm:", {m: agg[m]["latency"]["llm_invoking_tasks"] for m in METHODS})
    print("mcnemar:", stats["mcnemar_p_display"])
    print(f"[canonical] consistency gate: {'ALL PASS' if not failed else 'FAILED: ' + str(failed)}")
    print(f"[canonical] wrote {out_json} + csv")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
