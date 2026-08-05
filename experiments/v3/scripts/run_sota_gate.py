#!/usr/bin/env python3
"""SOTA Gate — the single allowed exit point for the experiment rebuild.

Reads experiments/v3/results/ and checks all conditions from specs/sota-gate/spec.md.
Exits non-zero until all conditions pass; prints full evidence on PASS.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "experiments" / "v3" / "evaluators"))
sys.path.insert(0, str(ROOT / "experiments" / "v3"))

RESULTS_DIR = ROOT / "experiments" / "v3" / "results"
BENCH_DIR = ROOT / "experiments" / "v3" / "benchmark"

KAFARMTWIN = "KAFarmTwin-TypedRepair"
KAFARMTWIN_CVSR_MIN_DELTA_PP = 0.03    # +3pp over strongest baseline
KAFARMTWIN_PASS5_IMPROVE = 0           # pass^5 strictly greater than strongest baseline
CRITICAL_RECALL_MIN = 0.95
FATAL_RATE_MAX = 0.01
COST_RATIO_MAX = 1.5
EVIDENCE_PRECISION_MIN = 0.95
REPLAY_SUCCESS_MIN = 0.95
REPEATS_MIN = 5


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


# Test-split tasks as defined by test_public_inputs.jsonl. The SOTA gate is defined
# on the FROZEN TEST SET (specs/sota-gate/spec.md line 15), never the dev split.
# Runs that only cover dev tasks (T19-T26) do not constitute gate evidence.
def test_split_task_ids() -> set[str]:
    p = BENCH_DIR / "test_public_inputs.jsonl"
    if not p.exists():
        return set()
    tids = set()
    for l in p.read_text(encoding="utf-8").splitlines():
        l = l.strip()
        if not l:
            continue
        tids.add(json.loads(l).get("task_id", ""))
    return tids


def check_conditions(summary: dict[str, dict], runs: list[dict]) -> list[dict[str, str]]:
    """Return list of {condition, status, detail} — FAILED entries block the gate."""
    violations: list[dict[str, str]] = []

    if not summary:
        violations.append({"condition": "data_exists", "status": "FAIL",
                           "detail": "no v3_summary.json found; run make run-test first"})
        return violations

    # 0. Split provenance: the gate is defined on the test split. If the runs only
    #    cover dev tasks, this is not gate evidence — refuse to PASS.
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
    baselines = {m: s for m, s in summary.items() if m != KAFARMTWIN and m != "DeterministicFallback"}
    if not baselines:
        violations.append({"condition": "baselines_exist", "status": "FAIL",
                           "detail": "no non-fallback baselines found"})
        return violations

    # 2. Test gold frozen
    manifest_path = BENCH_DIR / "benchmark_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        sealed_hash = manifest.get("splits", {}).get("test_gold_sealed", {}).get("sha256")
        actual_hash = sha256_of(BENCH_DIR / "test_gold.sealed.jsonl") if (BENCH_DIR / "test_gold.sealed.jsonl").exists() else None
        if sealed_hash and actual_hash and sealed_hash != actual_hash:
            violations.append({"condition": "gold_hash_match", "status": "FAIL",
                               "detail": f"manifest sha256 {sealed_hash} != actual {actual_hash}"})
    else:
        violations.append({"condition": "gold_hash_match", "status": "FAIL",
                           "detail": "benchmark_manifest.json missing"})

    # 5. Repeats >= 5
    runs_by_method = {}
    for r in runs:
        runs_by_method.setdefault(r.get("method", ""), []).append(r)
    for m in methods:
        n = len(runs_by_method.get(m, []))
        if n < REPEATS_MIN:
            violations.append({"condition": f"repeats_{m}", "status": "FAIL",
                               "detail": f"{m}: {n} runs < {REPEATS_MIN}"})

    # 6. CVSR delta >= 3pp
    best_baseline = max(baselines.items(), key=lambda x: x[1].get("mean_cvsr", 0))
    best_name, best_agg = best_baseline
    delta = ours.get("mean_cvsr", 0) - best_agg.get("mean_cvsr", 0)
    if delta < KAFARMTWIN_CVSR_MIN_DELTA_PP:
        violations.append({"condition": "cvsr_delta", "status": "FAIL",
                           "detail": f"delta={delta:+.4f} < {KAFARMTWIN_CVSR_MIN_DELTA_PP} "
                                     f"(ours={ours.get('mean_cvsr',0):.4f} vs {best_name}={best_agg.get('mean_cvsr',0):.4f})"})

    # 8. pass^5 higher
    if ours.get("pass5", 0) <= best_agg.get("pass5", 0):
        violations.append({"condition": "pass5_improve", "status": "FAIL",
                           "detail": f"ours pass5={ours.get('pass5',0):.4f} <= {best_name} pass5={best_agg.get('pass5',0):.4f}"})

    # 9. Critical Object Recall >= baseline
    if ours.get("critical_recall", 0) < best_agg.get("critical_recall", 0):
        violations.append({"condition": "critical_recall", "status": "FAIL",
                           "detail": f"ours {ours.get('critical_recall',0):.4f} < {best_name} {best_agg.get('critical_recall',0):.4f}"})

    # 10. Fatal Violation Rate <= baseline
    if ours.get("fatal_violation_rate", 0) > best_agg.get("fatal_violation_rate", 0):
        violations.append({"condition": "fatal_rate", "status": "FAIL",
                           "detail": f"ours {ours.get('fatal_violation_rate',0):.4f} > {best_name} {best_agg.get('fatal_violation_rate',0):.4f}"})

    # 11. Evidence Precision / Replay Success
    if ours.get("evidence_precision", 0) < EVIDENCE_PRECISION_MIN:
        violations.append({"condition": "evidence_precision", "status": "FAIL",
                           "detail": f"ours {ours.get('evidence_precision',0):.4f} < {EVIDENCE_PRECISION_MIN}"})
    if ours.get("replay_success", 0) < REPLAY_SUCCESS_MIN:
        violations.append({"condition": "replay_success", "status": "FAIL",
                           "detail": f"ours {ours.get('replay_success',0):.4f} < {REPLAY_SUCCESS_MIN} "
                                     f"(see FAILURES.md F-005: replay substrate gap)"})

    # 12. Cost <= 1.5x
    if ours.get("cost_mean", 0) > 0 and best_agg.get("cost_mean", 0) > 0:
        ratio = ours["cost_mean"] / best_agg["cost_mean"]
        if ratio > COST_RATIO_MAX:
            violations.append({"condition": "cost_ratio", "status": "FAIL",
                               "detail": f"ours/baseline cost ratio = {ratio:.2f} > {COST_RATIO_MAX}"})

    return violations


def main() -> int:
    summary = load_summary()
    runs = load_runs()
    violations = check_conditions(summary, runs)
    if violations:
        print("SOTA_GATE=FAIL", end="")
        fails = [v for v in violations if v["status"] == "FAIL"]
        print(f" ({len(fails)} conditions failed):")
        for v in violations:
            print(f"  [{v['status']}] {v['condition']}: {v['detail']}")
        return 1

    # All pass
    ours = summary[KAFARMTWIN]
    best_baseline = max(
        {m: s for m, s in summary.items() if m != KAFARMTWIN and m != "DeterministicFallback"}.items(),
        key=lambda x: x[1].get("mean_cvsr", 0)
    )
    delta = ours.get("mean_cvsr", 0) - best_baseline[1].get("mean_cvsr", 0)
    manifest_hash = ""
    manifest_path = BENCH_DIR / "benchmark_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_hash = manifest.get("splits", {}).get("test_gold_sealed", {}).get("sha256", "")
    print("SOTA_GATE=PASS")
    print(f"baseline={best_baseline[0]}")
    print(f"delta_cvsr={delta:+.4f}")
    print(f"pass5_delta={ours.get('pass5',0) - best_baseline[1].get('pass5',0):+.4f}")
    print(f"manifest_sha256={manifest_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
