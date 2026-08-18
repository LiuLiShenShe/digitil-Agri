#!/usr/bin/env python3
"""SOTA Gate — the single allowed exit point for the experiment rebuild.

Reads experiments/v3/results/ and checks all conditions from specs/sota-gate/spec.md.
Exits non-zero until all conditions pass; prints full evidence on PASS.

P0-8 additions (paired bootstrap CI, per-task repeats, absolute guardrails):
  - Paired bootstrap 95% CI: KAFarmTwin CVSR vs strongest baseline, lower bound > 0
  - Per-task 5× repeat: each method must have ≥5 independent runs on every test task
  - Absolute guardrails (not just vs baseline):
      critical_recall ≥ 0.95, fatal_violation_rate ≤ 0.01, evidence_precision ≥ 0.95
  - Cost/latency reporting
"""

from __future__ import annotations

import hashlib
import json
import random
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "experiments" / "v3" / "evaluators"))
sys.path.insert(0, str(ROOT / "experiments" / "v3"))

RESULTS_DIR = ROOT / "experiments" / "v3" / "results"
BENCH_DIR = ROOT / "experiments" / "v3" / "benchmark"

KAFARMTWIN = "KAFarmTwin-TypedRepair"

# ─── P0-8: all guardrails ─────────────────────────────────────────────────────
KAFARMTWIN_CVSR_MIN_DELTA_PP = 0.03    # +3pp over strongest baseline (paired bootstrap)
CRITICAL_RECALL_MIN = 0.95              # absolute, not just vs baseline
FATAL_RATE_MAX = 0.01                   # absolute
EVIDENCE_PRECISION_MIN = 0.95           # absolute
REPLAY_SUCCESS_MIN = 0.95               # absolute
COST_RATIO_MAX = 1.5                   # ours ≤ 1.5× best baseline
REPEATS_PER_TASK_MIN = 5               # per (method × task)
BOOTSTRAP_N = 10_000                    # paired bootstrap samples
BOOTSTRAP_CI_ALPHA = 0.05              # 95% CI
RANDOM_SEED = 20260817


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_summary() -> dict[str, dict]:
    p = RESULTS_DIR / "v3_summary.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def load_runs() -> list[dict]:
    p = RESULTS_DIR / "v3_runs.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def test_split_task_ids() -> set[str]:
    p = BENCH_DIR / "test_v2" / "test_v2_public_inputs.jsonl"
    if not p.exists():
        return set()
    tids = set()
    for l in p.read_text(encoding="utf-8").splitlines():
        l = l.strip()
        if not l:
            continue
        tids.add(json.loads(l).get("task_id", ""))
    return tids


def _per_task_cvsr(runs: list[dict], method: str, test_ids: set[str]) -> dict[str, list[bool]]:
    """Return {task_id: [cvsr_per_run]} for a method on the frozen test split."""
    out: dict[str, list[bool]] = {}
    for r in runs:
        if r.get("method") != method:
            continue
        tid = r.get("task_id", "")
        if tid not in test_ids:
            continue
        out.setdefault(tid, []).append(bool(r.get("cvsr")))
    return out


def paired_bootstrap_ci(
    ours_per_task: dict[str, list[bool]],
    theirs_per_task: dict[str, list[bool]],
    n_boot: int = BOOTSTRAP_N,
    ci_alpha: float = BOOTSTRAP_CI_ALPHA,
    rng_seed: int = RANDOM_SEED,
) -> dict:
    """Paired bootstrap 95% CI for mean CVSR delta (ours − theirs).

    For each bootstrap sample: resample tasks with replacement, take the mean CVSR
    of each method on that resampled set, compute delta. The 95% CI lower bound
    must be > 0 to pass.

    If a task is missing from one method's runs, that task is excluded entirely
    (paired design — both methods must have data for the task).
    """
    shared_tasks = sorted(set(ours_per_task.keys()) & set(theirs_per_task.keys()))
    if not shared_tasks:
        return {"ci_lower": -1.0, "ci_upper": -1.0, "point_est": 0.0,
                "n_tasks": 0, "status": "NO_DATA", "detail": "no shared tasks"}

    # point estimate: mean per-task delta (averaged across shared tasks)
    deltas = []
    for t in shared_tasks:
        o_mean = statistics.mean(ours_per_task[t]) if ours_per_task[t] else 0.0
        t_mean = statistics.mean(theirs_per_task[t]) if theirs_per_task[t] else 0.0
        deltas.append(o_mean - t_mean)
    point_est = statistics.mean(deltas)

    # bootstrap
    rng = random.Random(rng_seed)
    boot_deltas = []
    for _ in range(n_boot):
        sample = rng.choices(shared_tasks, k=len(shared_tasks))
        boot_deltas.append(statistics.mean([
            (statistics.mean(ours_per_task[t]) - statistics.mean(theirs_per_task[t]))
            for t in sample
        ]))
    boot_deltas.sort()
    lo_idx = int(ci_alpha / 2 * n_boot)
    hi_idx = int((1 - ci_alpha / 2) * n_boot) - 1
    ci_lower = boot_deltas[lo_idx]
    ci_upper = boot_deltas[min(hi_idx, n_boot - 1)]

    # Frozen A+ protocol: the gate PASS requires BOTH
    #   (a) Mean CVSR delta ≥ 3pp (point estimate over shared tasks), AND
    #   (b) paired-bootstrap 95% CI lower bound > 0.
    # A CI lower bound > 0 alone is not enough (a 1pp advantage with a tiny CI
    # would satisfy CI>0 but not the frozen +3pp bar). Fail if either fails.
    point_ok = point_est >= KAFARMTWIN_CVSR_MIN_DELTA_PP
    ci_ok = ci_lower > 0
    status = "OK" if (point_ok and ci_ok) else "FAIL"
    return {
        "ci_lower": round(ci_lower, 6),
        "ci_upper": round(ci_upper, 6),
        "point_est": round(point_est, 6),
        "n_tasks": len(shared_tasks),
        "status": status,
        "detail": (f"95% CI [{ci_lower:+.4f}, {ci_upper:+.4f}], "
                   f"point Δ={point_est:+.4f} {'≥3pp' if point_ok else '<3pp!'}, "
                   f"CI lower {'>0' if ci_ok else '≤0!'} → {status}"
                   f" ({len(shared_tasks)} tasks, {n_boot} bootstraps)"),
    }


def check_conditions(summary: dict[str, dict], runs: list[dict]) -> list[dict]:
    """Return list of {condition, status, detail} — FAILED entries block the gate."""
    violations: list[dict[str, str]] = []

    if not summary:
        violations.append({"condition": "data_exists", "status": "FAIL",
                           "detail": "no v3_summary.json found; run make run-test first"})
        return violations

    # 0. Split provenance
    test_ids = test_split_task_ids()
    if test_ids:
        covered = {r.get("task_id") for r in runs if r.get("method") == KAFARMTWIN}
        if not covered & test_ids:
            violations.append({"condition": "split_is_test", "status": "FAIL",
                               "detail": "runs cover only dev tasks; "
                                         "SOTA gate requires the frozen test split"})
        else:
            missing = sorted(test_ids - covered)
            if missing:
                violations.append({"condition": "test_coverage", "status": "FAIL",
                                   "detail": f"test tasks not run: {missing}"})

    methods = sorted(summary.keys())
    if KAFARMTWIN not in summary:
        violations.append({"condition": "ours_method_exists", "status": "FAIL",
                           "detail": f"{KAFARMTWIN} not in summary"})
        return violations

    ours = summary[KAFARMTWIN]
    baselines = {m: s for m, s in summary.items()
                 if m != KAFARMTWIN and m != "DeterministicFallback"}
    if not baselines:
        violations.append({"condition": "baselines_exist", "status": "FAIL",
                           "detail": "no non-fallback baselines found"})
        return violations

    # 1. Gold hash frozen
    manifest_path = BENCH_DIR / "benchmark_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        sealed_hash = manifest.get("splits", {}).get("test_v2_gold", {}).get("sha256")
        actual_hash = (sha256_of(BENCH_DIR / "test_v2" / "test_v2_gold.jsonl")
                       if (BENCH_DIR / "test_v2" / "test_v2_gold.jsonl").exists()
                       else None)
        if sealed_hash and actual_hash and sealed_hash != actual_hash:
            violations.append({"condition": "gold_hash_match", "status": "FAIL",
                               "detail": f"manifest sha256 {sealed_hash} != actual {actual_hash}"})
    else:
        violations.append({"condition": "gold_hash_match", "status": "FAIL",
                           "detail": "benchmark_manifest.json missing"})

    # 2. Per-task 5× repeat (P0-8)
    runs_by_method: dict[str, list[dict]] = {}
    for r in runs:
        runs_by_method.setdefault(r.get("method", ""), []).append(r)

    for m in [KAFARMTWIN] + sorted(baselines.keys()):
        per_task = _per_task_cvsr(runs, m, test_ids)
        for tid in sorted(test_ids):
            n = len(per_task.get(tid, []))
            if n < REPEATS_PER_TASK_MIN:
                violations.append({
                    "condition": f"repeats_{m}_{tid}",
                    "status": "FAIL",
                    "detail": f"{m} on {tid}: {n} runs < {REPEATS_PER_TASK_MIN}",
                })

    # 3. CVSR delta via paired bootstrap CI (P0-8: replaces simple delta check)
    best_baseline_name = max(baselines.items(),
                             key=lambda x: x[1].get("mean_cvsr", 0))[0]
    ours_per_task = _per_task_cvsr(runs, KAFARMTWIN, test_ids)
    best_per_task = _per_task_cvsr(runs, best_baseline_name, test_ids)
    ci_result = paired_bootstrap_ci(ours_per_task, best_per_task)
    if ci_result["status"] != "OK":
        violations.append({
            "condition": "cvsr_paired_bootstrap_ci",
            "status": "FAIL",
            "detail": ci_result["detail"],
        })

    # 4. pass^5 higher
    best_agg = baselines[best_baseline_name]
    if ours.get("pass5", 0) <= best_agg.get("pass5", 0):
        violations.append({"condition": "pass5_improve", "status": "FAIL",
                           "detail": (f"ours pass5={ours.get('pass5',0):.4f} <= "
                                      f"{best_baseline_name} pass5={best_agg.get('pass5',0):.4f}")})

    # 5. Critical recall (absolute ≥ 0.95 AND ≥ best baseline)
    if ours.get("critical_recall", 0) < CRITICAL_RECALL_MIN:
        violations.append({"condition": "critical_recall_absolute", "status": "FAIL",
                           "detail": (f"ours {ours.get('critical_recall',0):.4f} < "
                                      f"absolute minimum {CRITICAL_RECALL_MIN}")})
    elif ours.get("critical_recall", 0) < best_agg.get("critical_recall", 0):
        violations.append({"condition": "critical_recall_vs_baseline", "status": "FAIL",
                           "detail": (f"ours {ours.get('critical_recall',0):.4f} < "
                                      f"{best_baseline_name} {best_agg.get('critical_recall',0):.4f}")})

    # 6. Fatal violation rate (absolute ≤ 0.01 AND ≤ best baseline)
    if ours.get("fatal_violation_rate", 0) > FATAL_RATE_MAX:
        violations.append({"condition": "fatal_rate_absolute", "status": "FAIL",
                           "detail": (f"ours {ours.get('fatal_violation_rate',0):.4f} > "
                                      f"absolute maximum {FATAL_RATE_MAX}")})
    elif ours.get("fatal_violation_rate", 0) > best_agg.get("fatal_violation_rate", 0):
        violations.append({"condition": "fatal_rate_vs_baseline", "status": "FAIL",
                           "detail": (f"ours {ours.get('fatal_violation_rate',0):.4f} > "
                                      f"{best_baseline_name} {best_agg.get('fatal_violation_rate',0):.4f}")})

    # 7. Evidence precision (absolute ≥ 0.95)
    if ours.get("evidence_precision", 0) < EVIDENCE_PRECISION_MIN:
        violations.append({"condition": "evidence_precision_absolute", "status": "FAIL",
                           "detail": (f"ours {ours.get('evidence_precision',0):.4f} < "
                                      f"absolute minimum {EVIDENCE_PRECISION_MIN}")})

    # 8. Replay success (absolute ≥ 0.95)
    if ours.get("replay_success", 0) < REPLAY_SUCCESS_MIN:
        violations.append({"condition": "replay_success", "status": "FAIL",
                           "detail": (f"ours {ours.get('replay_success',0):.4f} < "
                                      f"{REPLAY_SUCCESS_MIN} (see FAILURES.md F-005)")})

    # 9. Cost ratio ≤ 1.5×
    if ours.get("cost_mean", 0) > 0 and best_agg.get("cost_mean", 0) > 0:
        ratio = ours["cost_mean"] / best_agg["cost_mean"]
        if ratio > COST_RATIO_MAX:
            violations.append({"condition": "cost_ratio", "status": "FAIL",
                               "detail": f"ours/baseline cost ratio = {ratio:.2f} > {COST_RATIO_MAX}"})

    return violations


def _build_evidence_table(summary: dict[str, dict]) -> str:
    """Pretty-print the method comparison table."""
    rows = []
    for m in sorted(summary.keys()):
        s = summary[m]
        rows.append({
            "method": m,
            "n_runs": str(s.get("n_runs", 0)),
            "CVSR": f"{s.get('mean_cvsr', 0):.3f}",
            "pass5": f"{s.get('pass5', 0):.3f}",
            "ObjF1": f"{s.get('object_f1', 0):.3f}",
            "CritR": f"{s.get('critical_recall', 0):.3f}",
            "RelF1": f"{s.get('relation_f1', 0):.3f}",
            "BindF1": f"{s.get('binding_f1', 0):.3f}",
            "Fatal": f"{s.get('fatal_violation_rate', 0):.3f}",
            "EvidP": f"{s.get('evidence_precision', 0):.3f}",
            "Cost": f"${s.get('cost_mean', 0):.4f}",
        })
    if not rows:
        return "  (no data)"
    header = "  ".join(f"{k:>8s}" for k in rows[0])
    lines = [header, "-" * len(header)]
    for r in rows:
        lines.append("  ".join(f"{v:>8s}" for v in r.values()))
    return "\n".join(lines)


def main() -> int:
    summary = load_summary()
    runs = load_runs()
    violations = check_conditions(summary, runs)

    # Separate FAIL from WARN (currently all are FAIL)
    fails = [v for v in violations if v["status"] == "FAIL"]

    if fails:
        print(f"SOTA_GATE=FAIL ({len(fails)} conditions failed):")
        for v in fails:
            print(f"  [FAIL] {v['condition']}: {v['detail']}")
        print()
        print("Evidence table:")
        print(_build_evidence_table(summary))
        return 1

    # ─── PASS ──────────────────────────────────────────────────────────────
    baselines = {m: s for m, s in summary.items()
                 if m != KAFARMTWIN and m != "DeterministicFallback"}
    best_name = max(baselines.items(), key=lambda x: x[1].get("mean_cvsr", 0))[0]
    best_agg = baselines[best_name]
    ours = summary[KAFARMTWIN]
    delta = ours.get("mean_cvsr", 0) - best_agg.get("mean_cvsr", 0)

    test_ids = test_split_task_ids()
    ours_per_task = _per_task_cvsr(runs, KAFARMTWIN, test_ids)
    best_per_task = _per_task_cvsr(runs, best_name, test_ids)
    ci = paired_bootstrap_ci(ours_per_task, best_per_task)

    manifest_hash = ""
    manifest_path = BENCH_DIR / "benchmark_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_hash = manifest.get("splits", {}).get("test_v2_gold", {}).get("sha256", "")

    print("=" * 72)
    print("SOTA_GATE=PASS")
    print("=" * 72)
    print(f"  Method:          {KAFARMTWIN}")
    print(f"  vs Baseline:     {best_name}")
    print(f"  CVSR (ours):     {ours.get('mean_cvsr', 0):.4f}")
    print(f"  CVSR (baseline): {best_agg.get('mean_cvsr', 0):.4f}")
    print(f"  Delta:           {delta:+.4f} ({delta*100:+.2f}pp)")
    print(f"  Paired bootstrap 95% CI: {ci['detail']}")
    print(f"  pass5 (ours):    {ours.get('pass5', 0):.4f}")
    print(f"  pass5 (baseline):{best_agg.get('pass5', 0):.4f}")
    print(f"  Critical Recall: {ours.get('critical_recall', 0):.4f} (≥{CRITICAL_RECALL_MIN})")
    print(f"  Fatal Rate:      {ours.get('fatal_violation_rate', 0):.4f} (≤{FATAL_RATE_MAX})")
    print(f"  Evidence Prec:   {ours.get('evidence_precision', 0):.4f} (≥{EVIDENCE_PRECISION_MIN})")
    print(f"  Replay Success:  {ours.get('replay_success', 0):.4f}")
    print(f"  Cost (ours):     ${ours.get('cost_mean', 0):.4f}")
    print(f"  Cost (baseline): ${best_agg.get('cost_mean', 0):.4f}")
    print(f"  Gold hash:       {manifest_hash}")
    print()
    print("Evidence table:")
    print(_build_evidence_table(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
