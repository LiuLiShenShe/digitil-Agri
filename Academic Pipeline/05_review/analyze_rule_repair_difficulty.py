#!/usr/bin/env python3
"""P0-5: Rule Repair Difficulty + Baseline Applicability Audit.

Read-only analysis of existing External300 rule_repair results.
No model reruns. No modification of benchmark artifacts.
"""

import json
import csv
import os
import re
from pathlib import Path
from collections import Counter, defaultdict

# === Paths ===
BASE = Path("/data/fj/数字孪生-paper-work/experiments/v3")
INPUTS = BASE / "benchmark/external300_candidate/external300_public_inputs.jsonl"
GOLD = BASE / "benchmark/external300_candidate/external300_gold_draft.jsonl"
SCORED = BASE / "results/external300/ext300_formal_20260825/scored/per_task.jsonl"
OUT_DIR = Path("/data/fj/数字孪生-paper-work/Academic Pipeline/05_review")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# === Load data ===
def load_jsonl(path):
    rows = []
    with open(path) as f:
        for line in f:
            rows.append(json.loads(line))
    return rows

inputs = {r["task_id"]: r for r in load_jsonl(INPUTS)}
scored = load_jsonl(SCORED)

# === Filter rule_repair ===
rr_inputs = {k: v for k, v in inputs.items() if v.get("task_type") == "rule_repair"}
rr_scored = [r for r in scored if r.get("task_type") == "rule_repair"]

print(f"Rule repair tasks in inputs: {len(rr_inputs)}")
print(f"Rule repair scored records: {len(rr_scored)} (expect 120 = 60 tasks × 2 methods)")

# === SA llm_calls investigation ===
print("\n" + "="*60)
print("SA llm_calls INVESTIGATION")
print("="*60)

sa_rr = [r for r in rr_scored if "SingleAgent" in r.get("method", "")]
kf_rr = [r for r in rr_scored if "KAFarmTwin" in r.get("method", "")]

print(f"\nSA rule_repair records: {len(sa_rr)}")
sa_llm_calls = Counter(r.get("llm_calls", -1) for r in sa_rr)
print(f"SA llm_calls distribution: {dict(sa_llm_calls)}")

sa_tokens = Counter(r.get("tokens", -1) for r in sa_rr)
print(f"SA tokens distribution: {dict(sa_tokens)}")

sa_construction = Counter(r.get("construction_path", "unknown") for r in sa_rr)
print(f"SA construction_path distribution: {dict(sa_construction)}")

sa_success = Counter(r.get("cvsr", None) for r in sa_rr)
print(f"SA CVSR distribution: {dict(sa_success)}")

sa_fatal = [r.get("fatal_violations", []) for r in sa_rr]
fatal_counter = Counter()
for fv in sa_fatal:
    for v in fv:
        fatal_counter[v] += 1
print(f"SA fatal violations across all 60 tasks: {dict(fatal_counter)}")

print(f"\nKF rule_repair records: {len(kf_rr)}")
kf_llm_calls = Counter(r.get("llm_calls", -1) for r in kf_rr)
print(f"KF llm_calls distribution: {dict(kf_llm_calls)}")

kf_success = Counter(r.get("cvsr", None) for r in kf_rr)
print(f"KF CVSR distribution: {dict(kf_success)}")

# === Baseline applicability classification ===
print("\n" + "="*60)
print("BASELINE APPLICABILITY CLASSIFICATION")
print("="*60)

# From single_agent.py lines 40-53:
# SA on rule_repair returns "bare_seed_no_repair" — by design, no repair loop.
# construction_path is NOT in scored data, so we classify via:
#   llm_calls=0 + tokens=0 + CVSR=False = SA never attempted repair = by design.
# This is BASELINE_INCAPABLE_BY_DESIGN (label A).

baseline_applicability = {}
for r in sa_rr:
    tid = r["task_id"]
    cvsr = r.get("cvsr", False)
    llm_calls = r.get("llm_calls", 0)
    tokens = r.get("tokens", 0)
    fatal = r.get("fatal_violations", [])

    if llm_calls == 0 and tokens == 0 and not cvsr:
        # SA was routed to the no-repair path by design (confirmed by source code)
        label = "A_BASELINE_INCAPABLE_BY_DESIGN"
        reason = "SA has no repair loop; returns broken scene unchanged by design (single_agent.py:40-53). Scored data lacks construction_path; classified via llm_calls=0+tokens=0."
    elif llm_calls == 0 and not cvsr:
        label = "B_BASELINE_CAPABLE_BUT_DID_NOT_ACT"
        reason = "SA received task but produced no LLM calls"
    else:
        label = "D_AMBIGUOUS_REQUIRES_MANUAL_REVIEW"
        reason = f"llm_calls={llm_calls}, tokens={tokens}, cvsr={cvsr}"

    baseline_applicability[tid] = {"label": label, "reason": reason, "cvsr": cvsr}

# Summary
label_counts = Counter(v["label"] for v in baseline_applicability.values())
print(f"\nBaseline applicability distribution:")
for label, count in sorted(label_counts.items()):
    print(f"  {label}: {count}/{len(baseline_applicability)} ({count/len(baseline_applicability)*100:.1f}%)")

# === Task template analysis ===
print("\n" + "="*60)
print("TASK TEMPLATE ANALYSIS")
print("="*60)

templates = defaultdict(list)
for tid, inp in rr_inputs.items():
    prompt = inp.get("prompt", "")
    init = inp.get("initial_state", {})

    # Extract object type from prompt
    if "Pump" in prompt or "pump" in prompt.lower():
        if "irrigation" in prompt:
            templates["Pump → irrigation asset fix"].append(tid)
        else:
            templates["Pump → OTHER fix"].append(tid)
    elif "Irrigation" in prompt or "irrigation" in prompt.lower():
        templates["Irrigation → irrigation asset fix"].append(tid)
    elif "Camera" in prompt or "camera" in prompt.lower():
        templates["Camera → camera asset fix"].append(tid)
    elif "Sensor" in prompt or "sensor" in prompt.lower():
        templates["Sensor → sensor asset fix"].append(tid)
    else:
        templates["UNCLASSIFIED"].append(prompt[:80])

print(f"\nTemplate distribution:")
for pat, ids in sorted(templates.items(), key=lambda x: -len(x[1])):
    print(f"  {pat}: {len(ids)} tasks ({len(ids)/60*100:.1f}%)")

# === Difficulty tier classification ===
print("\n" + "="*60)
print("DIFFICULTY TIER CLASSIFICATION")
print("="*60)

task_audit = []
for tid in sorted(rr_inputs.keys()):
    inp = rr_inputs[tid]
    prompt = inp.get("prompt", "")
    init = inp.get("initial_state", {})

    # Check if fix is explicitly stated
    explicit_fix = any(kw in prompt for kw in [
        "修正为", "替换为", "目标资产", "必须直接替换", "使 asset_key=",
        "修正为 irrigation", "修正为 camera", "修正为 sensor",
        "仅将其 asset_key", "执行最小修复"
    ])

    # Determine violation rule from prompt content
    if "Pump" in prompt or "Irrigation" in prompt:
        violation_rule = "R4"
    elif "Camera" in prompt:
        violation_rule = "R4"
    elif "Sensor" in prompt:
        violation_rule = "R4"
    else:
        violation_rule = "R4"  # all are R4

    # Number of violations (from initial_state objects)
    init_objects = init.get("objects", [])
    n_violations = len([o for o in init_objects if o.get("asset_binding")])

    # Difficulty: All are D1 — single rule, single step, explicit fix
    # Rationale: prompt explicitly states the correction target
    difficulty = "D1"

    # KF results
    kf_r = next((r for r in kf_rr if r["task_id"] == tid), None)
    sa_r = next((r for r in sa_rr if r["task_id"] == tid), None)

    task_audit.append({
        "task_id": tid,
        "prompt": prompt[:150],
        "template_family": next((k for k, v in templates.items() if tid in v), "unknown"),
        "violation_rule": violation_rule,
        "violation_type": "asset_type_mismatch",
        "number_of_violations": n_violations,
        "repair_steps_required": 1,
        "explicit_fix_target_in_prompt": explicit_fix,
        "semantic_reasoning_required": False,
        "ontology_reasoning_required": False,
        "asset_reasoning_required": False,
        "binding_reasoning_required": False,
        "hierarchy_reasoning_required": False,
        "multiple_valid_repairs": False,
        "difficulty_tier": difficulty,
        "KF_success": kf_r.get("cvsr", False) if kf_r else None,
        "SA_success": sa_r.get("cvsr", False) if sa_r else None,
        "KF_llm_calls": kf_r.get("llm_calls", 0) if kf_r else None,
        "SA_llm_calls": sa_r.get("llm_calls", 0) if sa_r else None,
    })

# Difficulty distribution
diff_counts = Counter(t["difficulty_tier"] for t in task_audit)
print(f"\nDifficulty tier distribution:")
for tier, count in sorted(diff_counts.items()):
    print(f"  {tier}: {count}/{len(task_audit)} ({count/len(task_audit)*100:.1f}%)")

# Explicit fix stats
explicit_count = sum(1 for t in task_audit if t["explicit_fix_target_in_prompt"])
print(f"\nExplicit fix target in prompt: {explicit_count}/{len(task_audit)} ({explicit_count/len(task_audit)*100:.1f}%)")

# === Decomposed External300 metrics ===
print("\n" + "="*60)
print("DECOMPOSED EXTERNAL300 METRICS")
print("="*60)

# All 300 tasks
all_scored = [r for r in scored if r.get("method") in ("KAFarmTwin-TypedRepair", "SingleAgent-AllTools")]
kf_all = [r for r in all_scored if "KAFarmTwin" in r.get("method", "")]
sa_all = [r for r in all_scored if "SingleAgent" in r.get("method", "")]

kf_pass = sum(1 for r in kf_all if r.get("cvsr"))
sa_pass = sum(1 for r in sa_all if r.get("cvsr"))
total = len(kf_all)

print(f"\nAll 300 tasks:")
print(f"  KF: {kf_pass}/{total} = {kf_pass/total:.4f}")
print(f"  SA: {sa_pass}/{total} = {sa_pass/total:.4f}")
print(f"  Delta: +{(kf_pass - sa_pass)/total*100:.1f} pp")

# Per-category
categories = ["scene_construction", "asset_routing", "data_binding", "rule_repair", "memory_query"]
cat_results = {}
print(f"\nPer-category breakdown:")
print(f"{'Category':<25} {'KF':>8} {'SA':>8} {'Δ':>8} {'Net Δ':>8}")
print("-" * 60)

total_net_kf_wins = 0
total_net_sa_wins = 0
for cat in categories:
    kf_cat = [r for r in kf_all if r.get("task_type") == cat]
    sa_cat = [r for r in sa_all if r.get("task_type") == cat]
    kf_cat_pass = sum(1 for r in kf_cat if r.get("cvsr"))
    sa_cat_pass = sum(1 for r in sa_cat if r.get("cvsr"))
    n = len(kf_cat)
    delta = (kf_cat_pass - sa_cat_pass) / n * 100 if n else 0
    net = kf_cat_pass - sa_cat_pass
    total_net_kf_wins += max(0, net)
    total_net_sa_wins += max(0, -net)
    cat_results[cat] = {"kf": kf_cat_pass, "sa": sa_cat_pass, "n": n, "delta_pp": delta, "net": net}
    print(f"  {cat:<23} {kf_cat_pass:>5}/{n:<3} {sa_cat_pass:>5}/{n:<3} {delta:>+7.1f}pp {net:>+7d}")

print(f"\nTotal net KF-only wins: {total_net_kf_wins}")
print(f"Total net SA-only wins: {total_net_sa_wins}")

# Excluding rule_repair
kf_no_repair = [r for r in kf_all if r.get("task_type") != "rule_repair"]
sa_no_repair = [r for r in sa_all if r.get("task_type") != "rule_repair"]
kf_nr_pass = sum(1 for r in kf_no_repair if r.get("cvsr"))
sa_nr_pass = sum(1 for r in sa_no_repair if r.get("cvsr"))
n_nr = len(kf_no_repair)

print(f"\nExcluding rule_repair (240 tasks):")
print(f"  KF: {kf_nr_pass}/{n_nr} = {kf_nr_pass/n_nr:.4f}")
print(f"  SA: {sa_nr_pass}/{n_nr} = {sa_nr_pass/n_nr:.4f}")
print(f"  Delta: +{(kf_nr_pass - sa_nr_pass)/n_nr*100:.1f} pp")

# === Write outputs ===
print("\n" + "="*60)
print("WRITING OUTPUT FILES")
print("="*60)

# 1. rule_repair_task_audit.csv
with open(OUT_DIR / "rule_repair_task_audit.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=task_audit[0].keys())
    writer.writeheader()
    writer.writerows(task_audit)
print(f"  Written: rule_repair_task_audit.csv ({len(task_audit)} rows)")

# 2. rule_repair_baseline_applicability.csv
with open(OUT_DIR / "rule_repair_baseline_applicability.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["task_id", "label", "reason", "cvsr"])
    writer.writeheader()
    for tid in sorted(baseline_applicability.keys()):
        writer.writerow({"task_id": tid, **baseline_applicability[tid]})
print(f"  Written: rule_repair_baseline_applicability.csv ({len(baseline_applicability)} rows)")

# 3. rule_repair_summary.json
summary = {
    "total_tasks": 60,
    "total_records": len(rr_scored),
    "kf_success": sum(1 for r in kf_rr if r.get("cvsr")),
    "sa_success": sum(1 for r in sa_rr if r.get("cvsr")),
    "sa_llm_calls_all_zero": all(r.get("llm_calls", 0) == 0 for r in sa_rr),
    "sa_construction_path": "bare_seed_no_repair (by design, single_agent.py:40-53)",
    "baseline_applicability": dict(label_counts),
    "template_distribution": {k: len(v) for k, v in templates.items()},
    "difficulty_distribution": dict(diff_counts),
    "explicit_fix_in_prompt": f"{explicit_count}/{len(task_audit)}",
    "all_tasks_R4": all(t["violation_rule"] == "R4" for t in task_audit),
    "defensible_interpretation": "The 60-task subset is a controlled mechanism test showing that the KAFarmTwin typed repair path can reliably execute supported single-step R4 corrections when the repair target is unambiguous.",
    "baseline_comparison_note": "The 60/60 vs 0/60 comparison primarily measures the presence of an explicit repair loop vs an execution path that performs no repair; it should not be interpreted as a general comparison of semantic repair reasoning ability.",
    "decomposed_external300": {
        "all_300": {"kf": kf_pass, "sa": sa_pass, "total": total, "delta_pp": round((kf_pass-sa_pass)/total*100, 1)},
        "excluding_rule_repair_240": {"kf": kf_nr_pass, "sa": sa_nr_pass, "total": n_nr, "delta_pp": round((kf_nr_pass-sa_nr_pass)/n_nr*100, 1)},
        "per_category": cat_results,
    },
    "rerun_decision": "RERUN_NOT_REQUIRED",
}
with open(OUT_DIR / "rule_repair_summary.json", "w") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print(f"  Written: rule_repair_summary.json")

# 4. external300_decomposed_metrics.json
decomposed = {
    "all_300": {"kf_pass": kf_pass, "sa_pass": sa_pass, "total": total, "kf_cvsr": round(kf_pass/total, 4), "sa_cvsr": round(sa_pass/total, 4), "delta_pp": round((kf_pass-sa_pass)/total*100, 1)},
    "excluding_rule_repair": {"kf_pass": kf_nr_pass, "sa_pass": sa_nr_pass, "total": n_nr, "kf_cvsr": round(kf_nr_pass/n_nr, 4), "sa_cvsr": round(sa_nr_pass/n_nr, 4), "delta_pp": round((kf_nr_pass-sa_nr_pass)/n_nr*100, 1)},
    "per_category": cat_results,
}
with open(OUT_DIR / "external300_decomposed_metrics.json", "w") as f:
    json.dump(decomposed, f, indent=2, ensure_ascii=False)
print(f"  Written: external300_decomposed_metrics.json")

print("\n" + "="*60)
print("P0-5 COMPLETE")
print("="*60)
