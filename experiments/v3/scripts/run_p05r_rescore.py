#!/usr/bin/env python3
"""Re-score DirectRepair with gold fields merged into task dict.

The original runner bug: evaluate_task received task=public (no required_nodes),
causing object_p=0.0, object_r=1.0 for all 60 tasks. This script re-runs
DirectRepair + re-scores with the correct gold-injected task.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import dataclasses
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
from experiments.v3.harness.llm import LLMClient, make_llm_call_fn
from experiments.v3.evaluators.metrics import evaluate_task
from experiments.v3.methods.single_agent_direct_repair import run_single_agent_direct_repair

BENCH_DIR = ROOT / "experiments" / "v3" / "benchmark" / "external300_candidate"
PUBLIC_FILE = BENCH_DIR / "external300_public_inputs.jsonl"
GOLD_FILE = BENCH_DIR / "external300_gold_draft.jsonl"
OUT_DIR = ROOT / "experiments" / "v3" / "results" / "external300" / "p05r_direct_repair"

PUBLIC_FIELDS = {"task_id", "category", "task_type", "difficulty", "prompt", "initial_state"}
LEGACY_LOOKUP = {
    "scene_construction": "scene_build",
    "asset_routing": "asset_route",
    "data_binding": "data_bind",
    "rule_repair": "repair",
    "memory_query": "memory_query",
}
BUDGET_POLICY = {"max_llm_calls": 30, "max_tool_calls": 100, "max_repair_rounds": 3}

# For budget tracking since BudgetEnforcer.summary() may return None
_CALL_COUNTER = {"llm_calls": 0, "tokens": 0}


def track_call(fn):
    """Wrap llm_call_fn to count calls and tokens."""
    def wrapper(messages, budget):
        result = fn(messages, budget)
        _CALL_COUNTER["llm_calls"] += 1
        _CALL_COUNTER["tokens"] += len(json.dumps(result.get("content", "")) or "")
        return result
    return wrapper


def make_ctx_for_task(task):
    """Build context dict from task (same as run_fair_baselines.py)."""
    ctx = {}
    ctx["task_id"] = task.get("task_id", "")
    ctx["task_type"] = task.get("task_type") or task.get("category", "")
    ctx["prompt"] = task.get("prompt", "")
    if task.get("initial_state"):
        ctx["scene_state"] = task["initial_state"]
    return ctx


def load_tasks(max_tasks=None):
    tasks = []
    with open(PUBLIC_FILE) as f:
        for line in f:
            r = json.loads(line)
            if r.get("task_type") != "rule_repair":
                continue
            public = {k: v for k, v in r.items() if k in PUBLIC_FIELDS}
            public["category"] = LEGACY_LOOKUP.get(public.get("task_type", ""), public.get("task_type", ""))
            tasks.append(public)
            if max_tasks and len(tasks) >= max_tasks:
                break
    return tasks


def load_gold():
    gold = {}
    with open(GOLD_FILE) as f:
        for line in f:
            r = json.loads(line)
            gold[r["task_id"]] = r
    return gold


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-tasks", type=int, default=None)
    parser.add_argument("--score-only", action="store_true", help="Re-score with saved results (needs raw nodes/edges/bindings)")
    args = parser.parse_args()

    tasks = load_tasks(args.max_tasks)
    gold = load_gold()
    print(f"Loaded {len(tasks)} rule_repair tasks, {len(gold)} gold records")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    llm_client = LLMClient()
    _raw_fn = make_llm_call_fn(llm_client)
    llm_call_fn = track_call(_raw_fn)

    results = []
    for i, task in enumerate(tasks):
        tid = task["task_id"]
        g = gold.get(tid, {})
        print(f"[{i+1}/{len(tasks)}] {tid} ...", end=" ", flush=True)

        _CALL_COUNTER["llm_calls"] = 0
        _CALL_COUNTER["tokens"] = 0

        budget = BudgetEnforcer(BudgetConfig(**BUDGET_POLICY))
        proxy = TraceProxy(task_id=tid, method="SingleAgent-DirectRepair")
        ctx = make_ctx_for_task(task)
        if task.get("initial_state"):
            ctx["scene_state"] = task["initial_state"]
        registry = ToolRegistry(ctx=ctx, trace_proxy=proxy, budget=budget)

        t0 = time.time()
        try:
            raw = run_single_agent_direct_repair(
                task=task, registry=registry, budget=budget,
                llm_call_fn=llm_call_fn, agent_id="DirectRepair",
            )
            latency_ms = (time.time() - t0) * 1000

            # FIX: pass gold record 'g' as task, so evaluator sees required_nodes
            score = evaluate_task(
                task=g,
                method="SingleAgent-DirectRepair",
                nodes=raw.get("nodes", []),
                edges=raw.get("edges", []),
                bindings=raw.get("bindings", []),
                trace={"steps": raw.get("traceSteps", [])},
                llm_calls=_CALL_COUNTER["llm_calls"],
                tool_calls=0,
                repair_rounds=0,
                tokens=_CALL_COUNTER["tokens"],
                cost=0.0,
                latency_ms=latency_ms,
            )

            if dataclasses.is_dataclass(score) and not isinstance(score, dict):
                score_dict = dataclasses.asdict(score)
            elif isinstance(score, dict):
                score_dict = score
            else:
                score_dict = {"cvsr": getattr(score, "cvsr", False), "raw": str(score)}
            score_dict["method"] = "SingleAgent-DirectRepair"
            score_dict["task_id"] = tid
            results.append(score_dict)

            cvsr = score_dict.get("cvsr", False)
            print(f"CVSR={cvsr}, obj_p={score_dict.get('object_p',0):.3f}, "
                  f"obj_r={score_dict.get('object_r',0):.3f}, obj_f1={score_dict.get('object_f1',0):.3f}, "
                  f"fatal={len(score_dict.get('fatal_violations',[]))}")

        except Exception as e:
            latency_ms = (time.time() - t0) * 1000
            print(f"ERROR: {e}")
            import traceback; traceback.print_exc()
            results.append({
                "task_id": tid,
                "method": "SingleAgent-DirectRepair",
                "cvsr": False,
                "technical_failure": True,
                "error": str(e),
                "latency_ms": round(latency_ms, 1),
            })

    # Write per-task results
    out_file = OUT_DIR / "p05r_direct_repair_results_v2.jsonl"
    with open(out_file, "w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nWritten: {out_file} ({len(results)} records)")

    # Summary
    pass_count = sum(1 for r in results if r.get("cvsr"))
    fail_count = len(results) - pass_count
    fatal_count = sum(len(r.get("fatal_violations", [])) for r in results)
    print(f"\n=== SUMMARY ===")
    print(f"Total: {len(results)}, Pass: {pass_count}, Fail: {fail_count}")
    print(f"CVSR: {pass_count/len(results):.4f}" if results else "No results")

    # Per-task stats
    obj_p_vals = [r.get("object_p", 0) for r in results if not r.get("technical_failure")]
    obj_r_vals = [r.get("object_r", 0) for r in results if not r.get("technical_failure")]
    obj_f1_vals = [r.get("object_f1", 0) for r in results if not r.get("technical_failure")]
    rel_f1_vals = [r.get("relation_f1", 0) for r in results if not r.get("technical_failure")]
    bind_f1_vals = [r.get("binding_f1", 0) for r in results if not r.get("technical_failure")]
    if obj_p_vals:
        print(f"\nObject  P: mean={sum(obj_p_vals)/len(obj_p_vals):.3f}")
        print(f"Object  R: mean={sum(obj_r_vals)/len(obj_r_vals):.3f}")
        print(f"Object F1: mean={sum(obj_f1_vals)/len(obj_f1_vals):.3f}")
        print(f"Rel.   F1: mean={sum(rel_f1_vals)/len(rel_f1_vals):.3f}")
        print(f"Bind.  F1: mean={sum(bind_f1_vals)/len(bind_f1_vals):.3f}")

    summary = {
        "method": "SingleAgent-DirectRepair",
        "total_tasks": len(results),
        "pass": pass_count,
        "fail": fail_count,
        "cvsr": round(pass_count / len(results), 4) if results else 0,
        "fatal_violations_total": fatal_count,
        "mean_object_p": round(sum(obj_p_vals)/len(obj_p_vals), 4) if obj_p_vals else 0,
        "mean_object_r": round(sum(obj_r_vals)/len(obj_r_vals), 4) if obj_r_vals else 0,
        "mean_object_f1": round(sum(obj_f1_vals)/len(obj_f1_vals), 4) if obj_f1_vals else 0,
        "mean_relation_f1": round(sum(rel_f1_vals)/len(rel_f1_vals), 4) if rel_f1_vals else 0,
        "mean_binding_f1": round(sum(bind_f1_vals)/len(bind_f1_vals), 4) if bind_f1_vals else 0,
        "note": "Re-scored with gold-injected task dict (v1 had runner bug: public dict lacked required_nodes)",
        "benchmark": "External300 rule_repair (60 tasks)",
    }
    summary_file = OUT_DIR / "p05r_summary_v2.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWritten: {summary_file}")


if __name__ == "__main__":
    main()
