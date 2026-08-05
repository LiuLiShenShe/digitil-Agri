#!/usr/bin/env python3
"""Statistical report generator for the v3 experiment suite.

Reads experiments/v3/results/v3_runs.jsonl and v3_summary.json, computes:
  - Paired per-task bootstrap 95% CI for CVSR delta (KAFarmTwin vs strongest baseline)
  - pass^1/pass^3/pass^5 per method
  - Budget-normalized metrics (CVSR per dollar, CVSR per p95 latency)
  - Pareto frontier on (CVSR, cost, latency)
  - Multi-model direction consistency

Writes:
  experiments/v3/results/statistical_report.json
  experiments/v3/results/statistical_report.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # repo root
sys.path.insert(0, str(ROOT / "experiments" / "v3" / "evaluators"))
sys.path.insert(0, str(ROOT / "experiments" / "v3"))

from statistical_tests import paired_bootstrap_cvsr, sign_test  # noqa: E402
from metrics import pass_k, aggregate  # noqa: E402


RESULTS_DIR = ROOT / "experiments" / "v3" / "results"
KAFARMTWIN = "KAFarmTwin-TypedRepair"


def load_runs() -> list[dict]:
    p = RESULTS_DIR / "v3_runs.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def group_by_task_method(runs: list[dict]) -> dict[str, list[dict]]:
    """Group runs by (task_id, method) -> list[run]."""
    groups: dict[str, list[dict]] = {}
    for r in runs:
        key = f"{r.get('task_id', '')}|{r.get('method', '')}"
        groups.setdefault(key, []).append(r)
    return groups


def build_per_task_method_table(runs: list[dict]) -> dict[str, dict[str, dict]]:
    """Return table[task_id][method] = aggregated metrics."""
    groups = group_by_task_method(runs)
    result: dict[str, dict[str, dict]] = {}
    for key, group_runs in groups.items():
        task_id, method = key.split("|", 1)
        result.setdefault(task_id, {})[method] = {
            "n_runs": len(group_runs),
            "cvsr_flags": [bool(r.get("cvsr")) for r in group_runs],
            "mean_cvsr": sum(1.0 if r.get("cvsr") else 0.0 for r in group_runs) / len(group_runs),
            "object_f1_mean": sum(float(r.get("object_f1") or 0) for r in group_runs) / len(group_runs),
            "fatal_rate": sum(1 for r in group_runs if r.get("fatal_violations")) / len(group_runs),
        }
    return result


def paired_cvsr_bootstrap(table: dict[str, dict[str, dict]], methods: list[str]) -> dict[str, dict]:
    """Compute paired bootstrap for each method vs KAFarmTwin."""
    results: dict[str, dict] = {}
    tasks = sorted(table.keys())
    for method in methods:
        if method == KAFARMTWIN:
            continue
        ours_flags: list[float] = []
        theirs_flags: list[float] = []
        for t in tasks:
            if KAFARMTWIN in table[t] and method in table[t]:
                for o, m in zip(table[t][KAFARMTWIN]["cvsr_flags"], table[t][method]["cvsr_flags"]):
                    ours_flags.append(float(o))
                    theirs_flags.append(float(m))
        if len(ours_flags) < 2:
            results[method] = {"error": "insufficient paired data", "n": len(ours_flags)}
            continue
        results[method] = paired_bootstrap_cvsr(ours_flags, theirs_flags, n_boot=5000)
        results[method].update({"sign": sign_test([bool(f) for f in ours_flags], [bool(f) for f in theirs_flags])})
    return results


def aggregate_by_method(runs: list[dict]) -> dict[str, dict]:
    """Aggregate all runs of each method into a summary."""
    by_method: dict[str, list[dict]] = {}
    for r in runs:
        by_method.setdefault(r.get("method", ""), []).append(r)
    result = {}
    for method, recs in by_method.items():
        from metrics import TaskEval  # type: ignore
        taskevals = []
        for r in recs:
            taskevals.append(TaskEval(
                task_id=r.get("task_id") or "", method=r.get("method") or "", category="",
                cvsr=bool(r.get("cvsr")), object_p=float(r.get("object_p") or 0),
                object_r=float(r.get("object_r") or 0), object_f1=float(r.get("object_f1") or 0),
                critical_recall=float(r.get("critical_recall") or 0),
                exact_quantity=bool(r.get("exact_quantity")),
                relation_f1=float(r.get("relation_f1") or 0),
                binding_f1=float(r.get("binding_f1") or 0),
                fatal_violations=list(r.get("fatal_violations") or []),
                nonfatal_violations=list(r.get("nonfatal_violations") or []),
                repair_success=r.get("repair_success"),
                evidence_precision=float(r.get("evidence_precision") or 0),
                replay_success=float(r.get("replay_success") or 0),
                new_conflicts=int(r.get("new_conflicts") or 0),
                llm_calls=int(r.get("llm_calls") or 0), tool_calls=int(r.get("tool_calls") or 0),
                repair_rounds=int(r.get("repair_rounds") or 0),
                tokens=int(r.get("tokens") or 0), cost=float(r.get("cost") or 0),
                latency_ms=float(r.get("latency_ms") or 0),
            ))
        result[method] = aggregate(taskevals)
    return result


def pareto_frontier(method_summaries: dict[str, dict]) -> list[str]:
    """Return methods on the Pareto frontier for (CVSR, -cost, -latency_p95)."""
    frontier = []
    for name_a, m_a in method_summaries.items():
        dominated = False
        for name_b, m_b in method_summaries.items():
            if name_a == name_b:
                continue
            if (m_b.get("mean_cvsr", 0) >= m_a.get("mean_cvsr", 0) and
                m_b.get("cost_mean", 1e9) <= m_a.get("cost_mean", 0) and
                m_b.get("latency_p95_ms", 1e9) <= m_a.get("latency_p95_ms", 0) and
                (m_b["mean_cvsr"] > m_a["mean_cvsr"] or
                 m_b.get("cost_mean", 1e9) < m_a.get("cost_mean", 0) or
                 m_b.get("latency_p95_ms", 1e9) < m_a.get("latency_p95_ms", 0))):
                dominated = True
                break
        if not dominated:
            frontier.append(name_a)
    return sorted(frontier)


def write_report(method_summaries: dict[str, dict], bootstrap: dict[str, dict],
                 pareto: list[str]) -> None:
    md_lines = [
        "# KAFarmTwin v3 Statistical Report",
        "",
        "## Per-Method Summary (all tasks x all runs)",
        "",
        "| method | CVSR | pass1 | pass3 | pass5 | objF1 | critR | relF1 | bindF1 | fatal | cost | p95_latency |",
        "|--------|------|-------|-------|-------|-------|-------|-------|--------|-------|------|-------------|",
    ]
    for method, agg in method_summaries.items():
        md_lines.append(
            f"| {method} | {agg.get('mean_cvsr',0):.4f} | {agg.get('pass1',0):.4f} | "
            f"{agg.get('pass3',0):.4f} | {agg.get('pass5',0):.4f} | "
            f"{agg.get('object_f1',0):.4f} | {agg.get('critical_recall',0):.4f} | "
            f"{agg.get('relation_f1',0):.4f} | {agg.get('binding_f1',0):.4f} | "
            f"{agg.get('fatal_violation_rate',0):.4f} | "
            f"{agg.get('cost_mean',0):.4f} | {agg.get('latency_p95_ms',0):.0f}ms |"
        )
    md_lines += [
        "",
        "## Paired Bootstrap: KAFarmTwin vs Baselines",
        "",
    ]
    for method, res in bootstrap.items():
        md_lines.append(f"### vs {method}")
        if "error" in res:
            md_lines.append(f"  - {res['error']} (n={res.get('n', 0)})")
        else:
            md_lines.append(f"  - mean diff: {res.get('mean_diff', 0):+.4f}")
            md_lines.append(f"  - 95% CI: [{res.get('ci_low', 0):+.4f}, {res.get('ci_high', 0):+.4f}]")
            md_lines.append(f"  - CI lower > 0: {res.get('ci_lower_gt_0', False)}")
            md_lines.append(f"  - p-value (H0: diff <= 0): {res.get('p_value', 1.0)}")
    md_lines += ["", f"## Pareto Frontier: {pareto}", ""]
    (RESULTS_DIR / "statistical_report.md").write_text("\n".join(md_lines), encoding="utf-8")
    json_out = {
        "method_summaries": method_summaries,
        "bootstrap": bootstrap,
        "pareto": pareto,
    }
    (RESULTS_DIR / "statistical_report.json").write_text(json.dumps(json_out, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Generate v3 statistical report")
    parser.add_argument("--split", default=None, choices=["dev", "test"],
                        help="filter runs to a split's task_ids (dev=T19-26, test=T27-30+)")
    args = parser.parse_args()
    runs = load_runs()
    if not runs:
        print("[statistical-report] no runs found in v3_runs.jsonl")
        return 1
    if args.split:
        bench_dir = ROOT / "experiments" / "v3" / "benchmark"
        if args.split == "test":
            src = bench_dir / "test_public_inputs.jsonl"
        else:
            src = bench_dir / f"{args.split}.jsonl"
        split_ids = set()
        if src.exists():
            for l in src.read_text(encoding="utf-8").splitlines():
                l = l.strip()
                if l:
                    split_ids.add(json.loads(l).get("task_id", ""))
        runs = [r for r in runs if r.get("task_id") in split_ids]
        if not runs:
            print(f"[statistical-report] no runs found for split '{args.split}' "
                  f"(task_ids {sorted(split_ids)})")
            return 1
    methods = sorted(set(r.get("method", "") for r in runs))
    method_summaries = aggregate_by_method(runs)
    table = build_per_task_method_table(runs)
    bootstrap = paired_cvsr_bootstrap(table, methods)
    pareto = pareto_frontier(method_summaries)
    write_report(method_summaries, bootstrap, pareto)
    print(f"[statistical-report] {len(runs)} runs, {len(methods)} methods"
          + (f" (split={args.split})" if args.split else ""))
    for m, agg in method_summaries.items():
        print(f"  {m}: CVSR={agg.get('mean_cvsr',0):.4f} pass5={agg.get('pass5',0):.4f}")
    print(f"  Pareto frontier: {pareto}")
    print(f"  -> {RESULTS_DIR / 'statistical_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
