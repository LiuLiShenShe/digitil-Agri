#!/usr/bin/env python3
"""Asset 16-run diagnostic + repair failure decomposition (Tasks 8 + 15).

16 runs: 4 asset tasks (TN11-14) x {KF, SA} x 2 repeats.
Plus: TN31-34 repair failure decomposition (first_failed_cvSR_clause etc.).

Writes to results/v3_asset_diagnostic_runs.jsonl (separate from formal runs).
"""
from __future__ import annotations

import json, os, sys, time
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
from experiments.v3.harness.llm import LLMClient, make_llm_call_fn
from experiments.v3.evaluators.metrics import evaluate_task
from experiments.v3.evaluators.version import stamp_record

from experiments.v3.methods.single_agent import run_single_agent
from experiments.v3.methods.kafarmtwin_typed_repair import run_kafarmtwin_typed_repair

METHODS = {
    "SingleAgent-AllTools": run_single_agent,
    "KAFarmTwin-TypedRepair": run_kafarmtwin_typed_repair,
}
PUBLIC_FIELDS = {"task_id", "category", "task_type", "difficulty", "prompt", "initial_state"}
LEGACY = {"scene_construction": "scene", "asset_routing": "asset",
          "data_binding": "bind", "rule_repair": "repair", "memory_query": "mem"}


def _strip_public(task: dict) -> dict:
    """Return a copy with only public fields — methods must never see gold."""
    out = {k: v for k, v in task.items() if k in PUBLIC_FIELDS}
    tt = out.get("task_type") or out.get("category") or ""
    if not out.get("category"):
        out["category"] = LEGACY.get(tt, tt)
    return out


def load_split():
    bench = ROOT / "experiments" / "v3" / "benchmark" / "test_v2"
    gold_map = {}
    for l in (bench / "test_v2_gold.jsonl").read_text().splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        gold_map[r["task_id"]] = r
    out = []
    for l in (bench / "test_v2_public_inputs.jsonl").read_text().splitlines():
        if not l.strip():
            continue
        row = json.loads(l)
        public = {k: v for k, v in row.items() if k in PUBLIC_FIELDS}
        tt = public.get("task_type") or public.get("category") or ""
        if not public.get("category"):
            public["category"] = LEGACY.get(tt, tt)
        public["_gold"] = gold_map.get(public.get("task_id"), {})
        out.append(public)
    return out


def make_ctx(task):
    return {"task_id": task.get("task_id"),
        "catalog": {
            "greenhouse": {"assetKey": "greenhouse", "policy": "existing_asset"},
            "tomato": {"assetKey": "tomato", "policy": "lightweight_glb"},
            "sensor": {"assetKey": "sensor", "policy": "placeholder"},
            "camera": {"assetKey": "camera", "policy": "TRELLIS.2"},
            "irrigation": {"assetKey": "irrigation", "policy": "procedural_model"},
            "weather_station": {"assetKey": "weather_station", "policy": "existing_asset"},
        },
        "scene_state": None, "scene_plan": [], "scene_objects": [],
        "scene_relations": [], "scene_bindings": [], "generation_jobs": []}


def run_one(public, method_name, method_fn, llm, repeats, out_fh, task_filter=None):
    for run_i in range(repeats):
        t0 = time.time()
        gold = public["_gold"]
        method_task = _strip_public(public)  # methods see ONLY public fields; gold stays with scorer
        budget = BudgetEnforcer(BudgetConfig(max_llm_calls=30, max_tool_calls=100, max_repair_rounds=3))
        proxy = TraceProxy(task_id=public.get("task_id", ""), method=method_name)
        ctx = make_ctx(method_task)
        registry = ToolRegistry(ctx=ctx, trace_proxy=proxy, budget=budget)
        validator = ValidatorAPI()
        if method_task.get("initial_state"):
            ctx["scene_state"] = method_task["initial_state"]
        if method_task.get("category") == "mem" and method_task.get("initial_state"):
            ctx["memory_state"] = method_task["initial_state"]
        try:
            out = method_fn(task=method_task, registry=registry, budget=budget, llm_call_fn=llm)
        except Exception as e:
            out = {"nodes": [], "edges": [], "bindings": [], "traceSteps": [],
                   "budget": budget.summary(), "conflicts": [], "error": str(e)}
        latency_ms = round((time.time() - t0) * 1000, 1)
        proxy_calls = proxy.calls()
        final_state = {"objects": out.get("nodes") or []}
        if out.get("bindings"):
            final_state["bindings"] = out.get("bindings")
        te = evaluate_task(
            task=gold, method=method_name,
            nodes=out.get("nodes") or [], edges=out.get("edges") or [],
            bindings=out.get("bindings") or [],
            trace=out.get("trace") or {"steps": out.get("traceSteps") or []},
            proxy_calls=proxy_calls, final_state=final_state,
            answer=out.get("answer"),
            llm_calls=budget.llm_calls, tool_calls=budget.tool_calls,
            repair_rounds=budget.repair_rounds, tokens=budget.tokens, cost=budget.cost,
            latency_ms=latency_ms,
        )
        rec = {
            "task_id": public.get("task_id"), "method": method_name,
            "run_id": run_i + 1,
            "cvsr": te.cvsr,
            "object_f1": te.object_f1, "relation_f1": te.relation_f1,
            "binding_f1": te.binding_f1, "critical_recall": te.critical_recall,
            "fatal_violations": te.fatal_violations,
            "nonfatal_violations": te.nonfatal_violations,
            "repair_success": te.repair_success, "evidence_precision": te.evidence_precision,
            "replay_success": te.replay_success,
            "first_failed_cvsr_clause": te.first_failed_cvsr_clause,
            "llm_calls": budget.llm_calls, "tool_calls": budget.tool_calls,
            "repair_rounds": budget.repair_rounds, "tokens": budget.tokens, "cost": budget.cost,
            "latency_ms": latency_ms,
            "n_nodes": len(out.get("nodes") or []),
            "n_edges": len(out.get("edges") or []),
            "n_bindings": len(out.get("bindings") or []),
            "conflict_count": len(out.get("conflicts") or []),
            "n_asset_bindings": sum(1 for b in (out.get("bindings") or []) if b.get("type") in ("asset", "asset_job")),
        }
        rec = stamp_record(rec)
        out_fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
        out_fh.flush()
        c = "T" if te.cvsr else "F"
        print(f"  {rec['task_id']:16s} {method_name:30s} CVSR={c} "
              f"objF1={te.object_f1:.3f} relF1={te.relation_f1:.3f} bindF1={te.binding_f1:.3f} "
              f"critR={te.critical_recall:.3f} nodes={rec['n_nodes']} bindings={rec['n_bindings']} "
              f"failclause={te.first_failed_cvsr_clause or '-'}")


def main():
    tasks = load_split()
    client = LLMClient()
    if not client.is_configured():
        print("ERROR: no AGNES_API_KEY")
        return 2
    llm = make_llm_call_fn(client)

    results_dir = ROOT / "experiments" / "v3" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    asset_file = results_dir / "v3_asset_diagnostic_runs.jsonl"
    repair_file = results_dir / "v3_repair_decomposition.jsonl"

    print("=" * 30, "ASSET 16-run diagnostic", "=" * 30)
    with asset_file.open("w", encoding="utf-8") as fh:
        for task in tasks:
            tid = task.get("task_id") or ""
            if not tid.startswith("TN1"):
                continue
            for mname, mfn in METHODS.items():
                for _ in range(2):
                    run_one(task, mname, mfn, llm, 1, fh)
    print(f"\n[asset] done -> {asset_file}")

    print("=" * 30, "REPAIR failure decomposition (TN31-34)", "=" * 30)
    with repair_file.open("w", encoding="utf-8") as fh:
        for task in tasks:
            tid = task.get("task_id") or ""
            if not tid.startswith("TN3"):
                continue
            for mname, mfn in METHODS.items():
                run_one(task, mname, mfn, llm, 1, fh)
    print(f"\n[repair] done -> {repair_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
