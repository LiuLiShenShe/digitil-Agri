#!/usr/bin/env python3
"""Diagnostic matrix: 20 tasks × {KAFarmTwin, SingleAgent} × 1 repeat (real LLM).

Runs only 1 repeat per task to diagnose direction before committing to the full
500-run formal Gate. Writes results to a SEPARATE file (not v3_runs.jsonl) so
v3.0 and v3.1 results are preserved independently.

Per-category targets:
  scene  → CVSR 0.4–0.7 / 0.3–0.5 (KF/SA)
  asset  → CVSR 0.3–0.6 / 0.2–0.4
  bind   → CVSR 0.6–0.8 / 0.2–0.4
  repair → CVSR 0.8–1.0 / 0
  mem    → CVSR 1.0 / 1.0

Usage:
  python3 experiments/v3/scripts/run_diagnostic_matrix.py [--runs 1] [--split test]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "v3"))
sys.path.insert(0, str(ROOT / "experiments" / "v3" / "harness"))
sys.path.insert(0, str(ROOT / "experiments" / "v3" / "methods"))
sys.path.insert(0, str(ROOT / "experiments" / "v3" / "evaluators"))

from experiments.v3.harness.tools import ToolRegistry
from experiments.v3.harness.budget import BudgetConfig, BudgetEnforcer
from experiments.v3.harness.trace_proxy import TraceProxy
from experiments.v3.harness.validator_api import ValidatorAPI
from experiments.v3.harness.canonicalizer import canonicalize_output
from experiments.v3.harness.llm import LLMClient, make_llm_call_fn
from experiments.v3.evaluators.metrics import evaluate_task, aggregate, TaskEval
from experiments.v3.evaluators.version import stamp_record

from experiments.v3.methods.single_agent import run_single_agent
from experiments.v3.methods.kafarmtwin_typed_repair import run_kafarmtwin_typed_repair

METHODS = {
    "SingleAgent-AllTools": run_single_agent,
    "KAFarmTwin-TypedRepair": run_kafarmtwin_typed_repair,
}

PUBLIC_FIELDS = {"task_id", "category", "task_type", "difficulty", "prompt", "initial_state"}


def load_split(split: str, max_tasks: int | None = None) -> list[dict]:
    bench = ROOT / "experiments" / "v3" / "benchmark"
    if split == "test":
        path = bench / "test_v2" / "test_v2_public_inputs.jsonl"
        gold_path = bench / "test_v2" / "test_v2_gold.jsonl"
    else:
        path = bench / f"{split}.jsonl"
        gold_path = bench / f"{split}.jsonl"
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    if max_tasks:
        rows = rows[:max_tasks]
    gold_map = {}
    if gold_path.exists():
        for l in gold_path.read_text(encoding="utf-8").splitlines():
            l = l.strip()
            if not l:
                continue
            r = json.loads(l)
            if "task_id" in r:
                gold_map[r["task_id"]] = r
    out = []
    for row in rows:
        tid = row.get("task_id")
        public = {k: v for k, v in row.items() if k in PUBLIC_FIELDS}
        gold = gold_map.get(tid, {})
        if "TODO_ANNOTATION" in json.dumps(gold):
            continue
        public["_gold"] = gold
        out.append(public)
    return out


def make_ctx_for_task(task):
    return {
        "task_id": task.get("task_id"),
        "catalog": {
            "greenhouse": {"assetKey": "greenhouse", "policy": "existing_asset"},
            "tomato": {"assetKey": "tomato", "policy": "lightweight_glb"},
            "sensor": {"assetKey": "sensor", "policy": "placeholder"},
            "camera": {"assetKey": "camera", "policy": "TRELLIS.2"},
            "irrigation": {"assetKey": "irrigation", "policy": "procedural_model"},
            "weather_station": {"assetKey": "weather_station", "policy": "existing_asset"},
        },
        "scene_state": None, "scene_plan": [], "scene_objects": [],
        "scene_relations": [], "scene_bindings": [], "generation_jobs": [],
    }


def _strip_public(task):
    out = {k: v for k, v in task.items() if k in PUBLIC_FIELDS}
    tt = out.get("task_type") or out.get("category") or ""
    LEGACY = {"scene_construction": "scene", "asset_routing": "asset",
              "data_binding": "bind", "rule_repair": "repair", "memory_query": "mem"}
    if not out.get("category"):
        out["category"] = LEGACY.get(tt, tt)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="test", choices=["dev", "test"])
    parser.add_argument("--max-tasks", type=int, default=None)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260818)
    args = parser.parse_args()

    client = LLMClient()
    if not client.is_configured():
        print("[diagnostic] ERROR: no AGNES_API_KEY; export or set .env")
        return 2
    llm_call_fn = make_llm_call_fn(client)

    tasks = load_split(args.split, args.max_tasks)
    results_dir = ROOT / "experiments" / "v3" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Write to a SEPARATE file so v3_runs.jsonl is untouched
    diag_file = results_dir / "v3_diagnostic_runs.jsonl"
    records = []
    t_start = time.time()

    for task in tasks:
        for method_name, method_fn in METHODS.items():
            for run_i in range(args.runs):
                r0 = time.time()
                gold = task.get("_gold") or task
                public = _strip_public(task)
                budget = BudgetEnforcer(BudgetConfig(max_llm_calls=30, max_tool_calls=100,
                                                     max_repair_rounds=3))
                proxy = TraceProxy(task_id=public.get("task_id", ""), method=method_name)
                ctx = make_ctx_for_task(public)
                registry = ToolRegistry(ctx=ctx, trace_proxy=proxy, budget=budget)
                validator = ValidatorAPI()
                if public.get("initial_state"):
                    ctx["scene_state"] = public["initial_state"]
                if public.get("category") in ("memory_query", "mem") and public.get("initial_state"):
                    ctx["memory_state"] = public["initial_state"]
                try:
                    out = method_fn(task=public, registry=registry, budget=budget,
                                    llm_call_fn=llm_call_fn)
                except Exception as e:
                    out = {"nodes": [], "edges": [], "bindings": [], "traceSteps": [],
                           "budget": budget.summary(), "conflicts": [], "error": str(e)}
                latency_ms = round((time.time() - r0) * 1000, 1)
                proxy_calls = proxy.calls()
                final_state = {"objects": out.get("nodes") or []}
                if out.get("bindings"):
                    final_state["bindings"] = out.get("bindings")
                eval_result = evaluate_task(
                    task=gold, method=method_name,
                    nodes=out.get("nodes") or [], edges=out.get("edges") or [],
                    bindings=out.get("bindings") or [],
                    trace=out.get("trace") or {"steps": out.get("traceSteps") or []},
                    proxy_calls=proxy_calls, final_state=final_state,
                    answer=out.get("answer"),
                    llm_calls=budget.llm_calls, tool_calls=budget.tool_calls,
                    repair_rounds=budget.repair_rounds,
                    tokens=budget.tokens, cost=budget.cost,
                    latency_ms=latency_ms,
                )
                rec = {
                    "task_id": task.get("task_id"), "method": method_name,
                    **{k: getattr(eval_result, k) for k in (
                        "cvsr", "object_p", "object_r", "object_f1", "critical_recall", "exact_quantity",
                        "relation_f1", "binding_f1", "fatal_violations", "nonfatal_violations",
                        "repair_success", "evidence_precision", "replay_success", "new_conflicts",
                        "llm_calls", "tool_calls", "repair_rounds", "tokens", "cost", "latency_ms")},
                    "budget": budget.summary(),
                    "run_id": run_i + 1,
                }
                rec = stamp_record(rec)
                records.append(rec)
                with diag_file.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
                cat = task.get("category", "?")
                cvsr_s = "T" if rec.get("cvsr") else "F"
                critr = rec.get("critical_recall", 0)
                bindf1 = rec.get("binding_f1", 0)
                print(f"  {task.get('task_id'):20s} {method_name:30s} "
                      f"CVSR={cvsr_s}  critR={critr:.2f}  bindF1={bindf1:.2f}  "
                      f"cat={cat}")

    elapsed = time.time() - t_start
    print(f"\n[diagnostic] {len(records)} runs in {elapsed:.1f}s -> {diag_file}")

    # Per-category summary
    from collections import defaultdict
    cat_method = defaultdict(lambda: {"cvsr_true": 0, "cvsr_total": 0, "critR": [], "bindF1": [], "repOK": []})
    task_type_map = {}
    LEGACY = {"scene_construction": "scene", "asset_routing": "asset", "data_binding": "bind",
              "rule_repair": "repair", "memory_query": "mem"}
    for task in tasks:
        tt = task.get("task_type") or task.get("category") or "?"
        task_type_map[task.get("task_id")] = LEGACY.get(tt, tt)
    for r in records:
        cat = task_type_map.get(r["task_id"], "?")
        method = r["method"]
        key = (cat, method)
        d = cat_method[key]
        d["cvsr_total"] += 1
        if r.get("cvsr"):
            d["cvsr_true"] += 1
        d["critR"].append(r.get("critical_recall", 0))
        d["bindF1"].append(r.get("binding_f1", 0))
        d["repOK"].append(1 if r.get("repair_success") else 0)

    print(f"\n{'Category':>12s}  {'Method':>30s}  CVSR    CritR   BindF1  Repair")
    print("-" * 90)
    for (cat, method), d in sorted(cat_method.items()):
        cvsr = d["cvsr_true"] / d["cvsr_total"] if d["cvsr_total"] else 0
        critR = sum(d["critR"]) / len(d["critR"]) if d["critR"] else 0
        bindF1 = sum(d["bindF1"]) / len(d["bindF1"]) if d["bindF1"] else 0
        repOK = sum(d["repOK"]) / len(d["repOK"]) if d["repOK"] else 0
        print(f"{cat:>12s}  {method:>30s}  {cvsr:.3f}  {critR:.3f}  {bindF1:.3f}  {repOK:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
