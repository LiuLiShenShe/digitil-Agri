#!/usr/bin/env python3
"""Run the v3 fair-baseline experiment.

For each (task x method) tuple, runs the method >= N independent times through the
shared ToolRegistry / ValidatorAPI / TraceProxy / Budget / canonicalizer, evaluates
each run with the v3 semantic evaluator, and writes per-run JSONL logs + aggregated
reports under experiments/v3/results/.

Methods (all same capabilities/budget, structural differences only):
  SingleAgent-AllTools, ReAct-AllTools, GenericMultiAgent-AllTools,
  GenericRepair-AllTools, KAFarmTwin-TypedRepair, DeterministicFallback(separate)

Usage:
  python3 experiments/v3/scripts/run_fair_baselines.py [--split dev|test] [--max-tasks N]
      [--runs N] [--methods m1,m2,...] [--smoke] [--mock] [--seed N] [--model NAME]
Exit 0 on success.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # repo root
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "v3"))
sys.path.insert(0, str(ROOT / "experiments" / "v3" / "harness"))
sys.path.insert(0, str(ROOT / "experiments" / "v3" / "methods"))
sys.path.insert(0, str(ROOT / "experiments" / "v3" / "evaluators"))

from experiments.v3.harness.tools import ToolRegistry  # type: ignore
from experiments.v3.harness.budget import BudgetConfig, BudgetEnforcer  # type: ignore
from experiments.v3.harness.trace_proxy import TraceProxy  # type: ignore
from experiments.v3.harness.validator_api import ValidatorAPI  # type: ignore
from experiments.v3.harness.canonicalizer import canonicalize_output  # type: ignore
from experiments.v3.harness.llm import LLMClient, make_llm_call_fn, LLMError  # type: ignore
from experiments.v3.evaluators.metrics import evaluate_task, aggregate  # type: ignore

from experiments.v3.methods.single_agent import run_single_agent  # type: ignore
from experiments.v3.methods.react import run_react  # type: ignore
from experiments.v3.methods.generic_multia_agent import run_generic_multi_agent  # type: ignore
from experiments.v3.methods.generic_repair import run_generic_repair  # type: ignore
from experiments.v3.methods.kafarmtwin_typed_repair import run_kafarmtwin_typed_repair  # type: ignore
from experiments.v3.methods.deterministic_fallback import run_deterministic_fallback  # type: ignore


METHODS = {
    "SingleAgent-AllTools": run_single_agent,
    "ReAct-AllTools": run_react,
    "GenericMultiAgent-AllTools": run_generic_multi_agent,
    "GenericRepair-AllTools": run_generic_repair,
    "KAFarmTwin-TypedRepair": run_kafarmtwin_typed_repair,
    "DeterministicFallback": run_deterministic_fallback,
}

# Public fields that methods may see; gold fields (required_nodes, goal_state, etc.)
# are NEVER exposed to any method. initial_state is included because repair tasks
# require it as input.
_PUBLIC_FIELDS = {"task_id", "category", "task_type", "difficulty", "prompt", "initial_state"}


def load_split(split: str, max_tasks: int | None = None) -> list[dict]:
    """Load benchmark split; return task dicts stripped to public fields.

    Gold-bearing fields (required_nodes, goal_state, critical_objects, etc.) are
    NEVER included in the returned dicts.  For dev/test, the gold fields are kept in
    a parallel mapping so the evaluator/scorer can access them.
    """
    bench = ROOT / "experiments" / "v3" / "benchmark"
    # Public inputs for the methods.
    if split == "test":
        path = bench / "test_public_inputs.jsonl"
    else:
        path = bench / f"{split}.jsonl"
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    if max_tasks:
        rows = rows[:max_tasks]
    # Gold answer key for the scorer (kept separate; methods never see it).
    gold_path = bench / (f"{split}_gold.sealed.jsonl" if split == "test" else f"{split}.jsonl")
    gold_map = {}
    if gold_path.exists():
        for l in gold_path.read_text(encoding="utf-8").splitlines():
            l = l.strip()
            if not l:
                continue
            r = json.loads(l)
            if "task_id" in r:
                gold_map[r["task_id"]] = r
    # Strip tasks to public fields only, but keep gold alongside
    out = []
    for row in rows:
        tid = row.get("task_id")
        public = {k: v for k, v in row.items() if k in _PUBLIC_FIELDS}
        gold = gold_map.get(tid, {})
        # Tasks whose gold is not yet human-adjudicated (T031-T035 carry
        # TODO_ANNOTATION in the sealed gold) MUST NOT be scored — running them
        # against placeholder gold would fabricate test-set evidence. They are
        # excluded from the run entirely until the annotator seals them.
        if "TODO_ANNOTATION" in json.dumps(gold):
            continue
        public["_gold"] = gold  # evaluated by scorer; never passed to methods
        out.append(public)
    return out


def make_ctx_for_task(task: dict) -> dict:
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
        "scene_state": None,
        "scene_plan": [],
        "scene_objects": [],
        "scene_relations": [],
        "scene_bindings": [],
        "generation_jobs": [],
    }


def _strip_public(task: dict) -> dict:
    """Return a copy of the task containing ONLY public fields (never gold)."""
    return {k: v for k, v in task.items() if k in _PUBLIC_FIELDS}


def run_one_method(method: str, task: dict, llm_call_fn, *, mock: bool = False) -> dict:
    """Run one method on one task through the shared harness; return the record.

    `task` is the PUBLIC task dict (no gold fields). Evaluation uses `gold` (the
    frozen answer key) held separately; methods never see it.
    """
    gold = task.get("_gold") or task  # fall back to task only if no gold attached
    public = _strip_public(task)       # methods only ever see public fields
    budget = BudgetEnforcer(BudgetConfig(max_llm_calls=30, max_tool_calls=100, max_repair_rounds=3))
    proxy = TraceProxy(task_id=public.get("task_id", ""), method=method)
    ctx = make_ctx_for_task(public)
    registry = ToolRegistry(ctx=ctx, trace_proxy=proxy, budget=budget)
    validator = ValidatorAPI()

    # seed the initial state if repair (public field)
    if public.get("initial_state"):
        ctx["scene_state"] = public["initial_state"]

    # DeterministicFallback uses no LLM
    fn = METHODS[method]
    if method == "DeterministicFallback":
        out = run_deterministic_fallback(task=public, registry=registry, budget=budget)
    else:
        if llm_call_fn is None:
            # mock LLM: deterministic content-free plan -> will produce low score (honest mock)
            out = fn(task=public, registry=registry, budget=budget,
                     llm_call_fn=_mock_llm_call_fn(public))
        else:
            out = fn(task=public, registry=registry, budget=budget, llm_call_fn=llm_call_fn)

    proxy_calls = proxy.calls()
    eval_result = evaluate_task(
        task=gold, method=method,
        nodes=out.get("nodes") or [], edges=out.get("edges") or [],
        bindings=out.get("bindings") or [],
        trace={"steps": out.get("traceSteps") or []},
        proxy_calls=proxy_calls,
        final_state={"objects": out.get("nodes") or []},
        llm_calls=budget.llm_calls, tool_calls=budget.tool_calls,
        repair_rounds=budget.repair_rounds,
        tokens=budget.tokens, cost=budget.cost,
        latency_ms=out.get("_latency_ms", 0.0),
    )
    return {
        "task_id": task.get("task_id"),
        "method": method,
        **{k: getattr(eval_result, k) for k in (
            "cvsr", "object_p", "object_r", "object_f1", "critical_recall", "exact_quantity",
            "relation_f1", "binding_f1", "fatal_violations", "nonfatal_violations",
            "repair_success", "evidence_precision", "replay_success", "new_conflicts",
            "llm_calls", "tool_calls", "repair_rounds", "tokens", "cost", "latency_ms")},
        "budget": budget.summary(),
        "conflicts": out.get("conflicts") or [],
        "trace_steps": out.get("traceSteps") or [],
        "proxy_calls": proxy_calls,
        "fallback": out.get("fallback", False),
    }


def _mock_llm_call_fn(task: dict):
    """A deterministic mock LLM for offline pipeline testing (produces honest low scores)."""
    def call_fn(messages, budget=None):
        return {"content": "{}", "content_json": {}, "finish_reason": "stop", "usage": {"total_tokens": 10}}
    return call_fn


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="dev", choices=["dev", "test"])
    parser.add_argument("--max-tasks", type=int, default=None)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--methods", default=",".join(METHODS.keys()))
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--mock", action="store_true", help="use mock LLM (offline pipeline test)")
    parser.add_argument("--seed", type=int, default=20260804)
    parser.add_argument("--model", default=None)
    args = parser.parse_args(argv)

    random.seed(args.seed)
    methods = [m.strip() for m in args.methods.split(",") if m.strip() in METHODS]

    # LLM client
    client = LLMClient()
    llm_call_fn = None
    if not args.mock:
        if not client.is_configured():
            print("[run_fair_baselines] ERROR: no AGNES_API_KEY set; use --mock for offline or set .env")
            return 2
        llm_call_fn = make_llm_call_fn(client)
        if args.model:
            os.environ["AGNES_MODEL"] = args.model
            client.model = args.model

    tasks = load_split(args.split, args.max_tasks)
    results_dir = ROOT / "experiments" / "v3" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    records = []
    t_start = time.time()
    for task in tasks:
        for method in methods:
            for run_i in range(args.runs):
                r0 = time.time()
                try:
                    rec = run_one_method(method, task, llm_call_fn, mock=args.mock)
                    rec["_latency_ms"] = round((time.time() - r0) * 1000, 1)
                    rec["run_id"] = run_i + 1
                except LLMError as e:
                    rec = {
                        "task_id": task.get("task_id"), "method": method, "run_id": run_i + 1,
                        "cvsr": False, "error": f"LLMError: {e}", "object_p": 0, "object_r": 0,
                        "object_f1": 0, "critical_recall": 0, "exact_quantity": False,
                        "relation_f1": 0, "binding_f1": 0, "fatal_violations": ["R7"],
                        "nonfatal_violations": [], "repair_success": None,
                        "evidence_precision": 0, "replay_success": 0, "new_conflicts": 0,
                        "llm_calls": 0, "tool_calls": 0, "repair_rounds": 0, "tokens": 0,
                        "cost": 0, "latency_ms": round((time.time() - r0) * 1000, 1),
                        "fallback": False,
                    }
                records.append(rec)
                # write per-run JSONL immediately (interrupt-safe)
                with (results_dir / "v3_runs.jsonl").open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
                if args.smoke:
                    print(f"  smoke run {task['task_id']} {method} #{run_i+1}: cvsr={rec.get('cvsr')}")
            if args.smoke:
                break

    # aggregate per method
    summary = {}
    for method in methods:
        recs = [r for r in records if r.get("method") == method]
        if recs:
            summary[method] = aggregate([_rec_to_taskeval(r) for r in recs])

    # write summary csv + json
    with (results_dir / "v3_summary.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["method", "n_runs", "mean_cvsr", "pass1", "pass3", "pass5",
                                                "object_f1", "critical_recall", "relation_f1", "binding_f1",
                                                "fatal_violation_rate", "evidence_precision", "replay_success",
                                                "llm_calls_mean", "cost_mean"])
        writer.writeheader()
        for method, agg in summary.items():
            row = {k: agg.get(k, "") for k in ("method", "n_runs", "mean_cvsr", "pass1", "pass3", "pass5",
                                                "object_f1", "critical_recall", "relation_f1", "binding_f1",
                                                "fatal_violation_rate", "evidence_precision", "replay_success",
                                                "llm_calls_mean", "cost_mean")}
            row["method"] = method
            writer.writerow(row)
    (results_dir / "v3_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    elapsed = time.time() - t_start
    print(f"[run_fair_baselines] split={args.split} tasks={len(tasks)} methods={methods} runs={args.runs}")
    for method, agg in summary.items():
        print(f"  {method}: CVSR={agg.get('mean_cvsr')} pass5={agg.get('pass5')} objF1={agg.get('object_f1')} "
              f"critR={agg.get('critical_recall')} relF1={agg.get('relation_f1')} bindF1={agg.get('binding_f1')} "
              f"fatal={agg.get('fatal_violation_rate')}")
    print(f"  total runs: {len(records)} in {elapsed:.1f}s -> {results_dir}")
    return 0


def _rec_to_taskeval(r: dict):
    from experiments.v3.evaluators.metrics import TaskEval  # type: ignore
    return TaskEval(
        task_id=r.get("task_id") or "", method=r.get("method") or "", category="",
        cvsr=bool(r.get("cvsr")), object_p=float(r.get("object_p") or 0),
        object_r=float(r.get("object_r") or 0), object_f1=float(r.get("object_f1") or 0),
        critical_recall=float(r.get("critical_recall") or 0),
        exact_quantity=bool(r.get("exact_quantity")), relation_f1=float(r.get("relation_f1") or 0),
        binding_f1=float(r.get("binding_f1") or 0),
        fatal_violations=list(r.get("fatal_violations") or []),
        nonfatal_violations=list(r.get("nonfatal_violations") or []),
        repair_success=r.get("repair_success"), evidence_precision=float(r.get("evidence_precision") or 0),
        replay_success=float(r.get("replay_success") or 0), new_conflicts=int(r.get("new_conflicts") or 0),
        llm_calls=int(r.get("llm_calls") or 0), tool_calls=int(r.get("tool_calls") or 0),
        repair_rounds=int(r.get("repair_rounds") or 0), tokens=int(r.get("tokens") or 0),
        cost=float(r.get("cost") or 0), latency_ms=float(r.get("latency_ms") or 0),
    )


if __name__ == "__main__":
    raise SystemExit(main())
