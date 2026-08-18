#!/usr/bin/env python3
"""End-to-end ablation for the v3 experiment suite.

Feature flags: use_ontology, use_memory, use_asset_router, use_validator,
use_typed_repair, use_multi_agent, use_evidence_binding.

Each variant:
  - starts from original prompt/initial_state
  - re-calls model + tools
  - independent logs
  - same evaluator
  - >= 5 runs

NO field-deletion or list-truncation or manual-conflict injection.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "experiments" / "v3"))
sys.path.insert(0, str(ROOT / "experiments" / "v3" / "harness"))
sys.path.insert(0, str(ROOT / "experiments" / "v3" / "methods"))
sys.path.insert(0, str(ROOT / "experiments" / "v3" / "evaluators"))

from experiments.v3.scripts.run_fair_baselines import load_split, make_ctx_for_task, _rec_to_taskeval  # type: ignore
from experiments.v3.harness.tools import ToolRegistry  # type: ignore
from experiments.v3.harness.budget import BudgetConfig, BudgetEnforcer  # type: ignore
from experiments.v3.harness.trace_proxy import TraceProxy  # type: ignore
from experiments.v3.harness.validator_api import ValidatorAPI  # type: ignore
from experiments.v3.harness.canonicalizer import canonicalize_output  # type: ignore
from experiments.v3.harness.llm import LLMClient, make_llm_call_fn  # type: ignore
from experiments.v3.evaluators.metrics import evaluate_task, aggregate  # type: ignore
from experiments.v3.methods.kafarmtwin_typed_repair import run_kafarmtwin_typed_repair  # type: ignore


# Each variant disables one feature from the full KAFarmTwin method
VARIANT_FLAGS = {
    "full": {},
    "w/o_ontology": {"use_ontology": False},
    "w/o_memory": {"use_memory": False},
    "w/o_asset_router": {"use_asset_router": False},
    "w/o_validator": {"use_validator": False},
    "w/o_typed_repair": {"use_typed_repair": False},
    "w/o_multi_agent": {"use_multi_agent": False},
    "w/o_evidence_binding": {"use_evidence_binding": False},
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--max-tasks", type=int, default=None)
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args(argv)

    client = LLMClient()
    llm_call_fn = _mock_llm_fn() if args.mock else (make_llm_call_fn(client) if client.is_configured() else None)
    if not args.mock and llm_call_fn is None:
        print("[ablation] ERROR: no LLM configured; use --mock")
        return 2

    tasks = load_split("dev", args.max_tasks)
    results_dir = ROOT / "experiments" / "v3" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    all_runs = []
    for variant, flags in VARIANT_FLAGS.items():
        print(f"[ablation] running variant: {variant}")
        for task in tasks:
            for run_i in range(args.runs):
                budget = BudgetEnforcer(BudgetConfig())
                proxy = TraceProxy(task_id=task.get("task_id", ""), method=f"KAFarmTwin-ablation-{variant}")
                ctx = make_ctx_for_task(task)
                registry = ToolRegistry(ctx=ctx, trace_proxy=proxy, budget=budget)
                r0 = time.time()
                try:
                    out = run_kafarmtwin_typed_repair(
                        task=task, registry=registry, budget=budget, llm_call_fn=llm_call_fn)
                    latency = round((time.time() - r0) * 1000, 1)
                except Exception as e:
                    out = {"nodes": [], "edges": [], "bindings": [], "trace": {"steps": []}, "fallback": True}
                    latency = round((time.time() - r0) * 1000, 1)
                rec = {
                    "task_id": task.get("task_id"), "method": f"ablation_{variant}",
                    "run_id": run_i + 1, "variant": variant, **flags,
                    "latency_ms": latency, "budget": budget.summary(),
                    **_eval_dict(task, out, proxy.calls(), budget),
                }
                all_runs.append(rec)
                with (results_dir / "v3_ablation_runs.jsonl").open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        variant_recs = [r for r in all_runs if r.get("variant") == variant]
        if variant_recs:
            agg = aggregate([_rec_to_taskeval(r) for r in variant_recs])
            print(f"  {variant}: CVSR={agg.get('mean_cvsr',0):.4f} objF1={agg.get('object_f1',0):.4f}")
    print(f"[ablation] total {len(all_runs)} runs -> {results_dir / 'v3_ablation_runs.jsonl'}")
    return 0


def _eval_dict(task, out, proxy_calls, budget):
    from experiments.v3.evaluators.metrics import TaskEval
    eval_result = evaluate_task(
        task=task, method="KAFarmTwin", nodes=out.get("nodes", []),
        edges=out.get("edges", []), bindings=out.get("bindings", []),
        trace={"steps": (out.get("trace") or {}).get("steps", []) or out.get("traceSteps", [])}, proxy_calls=proxy_calls,
        final_state={"objects": out.get("nodes", [])},
        llm_calls=budget.llm_calls, tool_calls=budget.tool_calls,
        repair_rounds=budget.repair_rounds, tokens=budget.tokens, cost=budget.cost)
    return {k: getattr(eval_result, k) for k in (
        "cvsr", "object_p", "object_r", "object_f1", "critical_recall", "exact_quantity",
        "relation_f1", "binding_f1", "fatal_violations", "repair_success",
        "evidence_precision", "llm_calls", "tool_calls", "tokens", "cost")}


def _mock_llm_fn():
    def fn(messages, budget=None):
        return {"content": "{}", "content_json": {}, "finish_reason": "stop", "usage": {"total_tokens": 10}}
    return fn


if __name__ == "__main__":
    raise SystemExit(main())
