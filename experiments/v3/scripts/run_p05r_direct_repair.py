#!/usr/bin/env python3
"""P0-5R: Run SingleAgent-DirectRepair on 60 External300 rule_repair tasks.

This is a NEW baseline experiment. Does NOT modify existing canonical results.
Produces per-task scored records compatible with the existing evaluation pipeline.

Usage:
    python3 experiments/v3/scripts/run_p05r_direct_repair.py [--dry-run] [--max-tasks N]
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
from experiments.v3.harness.canonicalizer import canonicalize_output
from experiments.v3.harness.llm import LLMClient, make_llm_call_fn
from experiments.v3.evaluators.metrics import evaluate_task
from experiments.v3.scripts.run_fair_baselines import make_ctx_for_task

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
TEMPERATURE = 0.2
BUDGET_POLICY = {"max_llm_calls": 30, "max_tool_calls": 100, "max_repair_rounds": 3}


def load_rule_repair_tasks(max_tasks: int | None = None) -> list[dict]:
    """Load rule_repair tasks from public inputs, stripped to public fields."""
    tasks = []
    with open(PUBLIC_FILE) as f:
        for line in f:
            r = json.loads(line)
            if r.get("task_type") != "rule_repair":
                continue
            # Strip to public fields (same as other methods see)
            public = {k: v for k, v in r.items() if k in PUBLIC_FIELDS}
            # Derive legacy 'category' field
            public["category"] = LEGACY_LOOKUP.get(public.get("task_type", ""), public.get("task_type", ""))
            tasks.append(public)
            if max_tasks and len(tasks) >= max_tasks:
                break
    return tasks


def load_gold() -> dict:
    gold = {}
    with open(GOLD_FILE) as f:
        for line in f:
            r = json.loads(line)
            gold[r["task_id"]] = r
    return gold


def main():
    parser = argparse.ArgumentParser(description="P0-5R DirectRepair baseline")
    parser.add_argument("--dry-run", action="store_true", help="Load tasks but don't run LLM")
    parser.add_argument("--max-tasks", type=int, default=None, help="Limit number of tasks")
    args = parser.parse_args()

    tasks = load_rule_repair_tasks(args.max_tasks)
    gold = load_gold()
    print(f"Loaded {len(tasks)} rule_repair tasks")

    # Setup
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    llm_client = LLMClient()
    llm_call_fn = make_llm_call_fn(llm_client)

    results = []
    for i, task in enumerate(tasks):
        tid = task["task_id"]
        print(f"[{i+1}/{len(tasks)}] {tid} ...", end=" ", flush=True)

        if args.dry_run:
            print("DRY RUN — skipped")
            continue

        # Fresh harness per task
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

            # Score with the frozen evaluator
            # CRITICAL: pass the GOLD record as 'task' so evaluate_task can
            # access required_nodes/required_edges/required_bindings. The public
            # task dict is stripped of gold fields and would cause empty matching.
            g = gold.get(tid, {})
            budget_summary = budget.summary()
            score = evaluate_task(
                task=g,
                method="SingleAgent-DirectRepair",
                nodes=raw.get("nodes", []),
                edges=raw.get("edges", []),
                bindings=raw.get("bindings", []),
                trace={"steps": raw.get("traceSteps", [])},
                llm_calls=budget_summary.get("llm_calls", 0),
                tool_calls=budget_summary.get("tool_calls", 0),
                repair_rounds=0,
                tokens=budget_summary.get("tokens", 0),
                cost=budget_summary.get("cost", 0.0),
                latency_ms=latency_ms,
            )
            # Convert TaskEval to dict for JSONL output
            import dataclasses
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
            print(f"CVSR={cvsr}, obj={score_dict.get('object_f1',0):.3f}, "
                  f"fatal={len(score_dict.get('fatal_violations',[]))}")

        except Exception as e:
            latency_ms = (time.time() - t0) * 1000
            print(f"ERROR: {e}")
            results.append({
                "task_id": tid,
                "method": "SingleAgent-DirectRepair",
                "cvsr": False,
                "technical_failure": True,
                "error": str(e),
                "latency_ms": round(latency_ms, 1),
            })

    # Write per-task results
    out_file = OUT_DIR / "p05r_direct_repair_results.jsonl"
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
    print(f"Fatal violations total: {fatal_count}")

    # Write summary JSON
    summary = {
        "method": "SingleAgent-DirectRepair",
        "total_tasks": len(results),
        "pass": pass_count,
        "fail": fail_count,
        "cvsr": round(pass_count / len(results), 4) if results else 0,
        "fatal_violations_total": fatal_count,
        "benchmark": "External300 rule_repair (60 tasks)",
        "temperature": TEMPERATURE,
        "budget": BUDGET_POLICY,
    }
    summary_file = OUT_DIR / "p05r_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Written: {summary_file}")


if __name__ == "__main__":
    main()
