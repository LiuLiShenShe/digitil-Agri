#!/usr/bin/env python3
"""Phase 3.4 ablation study for KAFarmTwin-TypedRepair.

Three ablations (each = 20 tasks x 5 repeats = 100 runs, same frozen benchmark/
evaluator/model/budget as Phase 2). Each disables ONE component via the env hooks
added to kafarmtwin_typed_repair.py. Default (no env) is the full method.

  A1 (no knowledge compiler): KAFARMTWIN_ABLATE_COMPILER=1  -> asset tasks use the
      shared stepwise builder instead of the knowledge_compiler path.
  A2 (no typed repair):       KAFARMTWIN_ABLATE_REPAIR=1   -> skip the repair loop,
      emit the as-built scene (like a non-repairing method).
  A3 (no ontology constraints):KAFARMTWIN_ABLATE_ONTOLOGY=1 -> LLM produces patches
      directly, no knowledge-constrained executor.

Writes one file per variant (distinct from frozen v3_runs.jsonl):
  experiments/v3/results/v3_runs_ablation_A1.jsonl
  experiments/v3/results/v3_runs_ablation_A2.jsonl
  experiments/v3/results/v3_runs_ablation_A3.jsonl
"""
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "experiments" / "v3"))

from experiments.v3.scripts.run_fair_baselines import (  # type: ignore
    load_split, make_llm_call_fn, LLMClient, _rec_to_taskeval, make_ctx_for_task,
)
from experiments.v3.evaluators.metrics import aggregate  # type: ignore
from experiments.v3.evaluators.version import stamp_record  # type: ignore
import experiments.v3.scripts.run_ablation_v3 as RA  # type: ignore

# We re-implement the runner here (not via run_ablation_v3.main) because that script
# does not actually pass flags into the method. Here we set env vars that the method
# reads, giving true component ablation.
from experiments.v3.harness.tools import ToolRegistry  # type: ignore
from experiments.v3.harness.budget import BudgetConfig, BudgetEnforcer  # type: ignore
from experiments.v3.harness.trace_proxy import TraceProxy  # type: ignore
from experiments.v3.harness.validator_api import ValidatorAPI  # type: ignore
from experiments.v3.evaluators.metrics import evaluate_task  # type: ignore


ABLATIONS = {
    "A1_no_compiler": "KAFARMTWIN_ABLATE_COMPILER",
    "A2_no_typed_repair": "KAFARMTWIN_ABLATE_REPAIR",
    "A3_no_ontology": "KAFARMTWIN_ABLATE_ONTOLOGY",
}


def _eval_dict(task, out, proxy_calls, budget):
    """Mirror run_ablation_v3._eval_dict behavior (scored output)."""
    te = evaluate_task(
        predicted=out, task=task, proxy_calls=proxy_calls, budget=budget,
        trace_steps=out.get("traceSteps", []),
    )
    return {
        "cvsr": bool(te.cvsr), "object_p": te.object_p, "object_r": te.object_r,
        "object_f1": te.object_f1, "critical_recall": te.critical_recall,
        "exact_quantity": bool(te.exact_quantity), "relation_f1": te.relation_f1,
        "binding_f1": te.binding_f1, "fatal_violations": te.fatal_violations,
        "nonfatal_violations": te.nonfatal_violations,
        "repair_success": te.repair_success, "evidence_precision": te.evidence_precision,
        "replay_success": te.replay_success, "new_conflicts": te.new_conflicts,
        "llm_calls": te.llm_calls, "tool_calls": te.tool_calls,
        "repair_rounds": te.repair_rounds, "tokens": te.tokens, "cost": te.cost,
        "latency_ms": te.latency_ms, "fallback": bool(out.get("fallback")),
    }


def run_variant(name, env_var, tasks, llm, runs):
    from experiments.v3.scripts.run_fair_baselines import make_ctx_for_task  # type: ignore
    # Clear any other ablation env, set this one.
    for ev in ABLATIONS.values():
        os.environ.pop(ev, None)
    os.environ[env_var] = "1"
    records = []
    for task in tasks:
        for run_i in range(runs):
            budget = BudgetEnforcer(BudgetConfig())
            proxy = TraceProxy(task_id=task.get("task_id", ""), method=f"KAFarmTwin-{name}")
            ctx = make_ctx_for_task(task)
            registry = ToolRegistry(ctx=ctx, trace_proxy=proxy, budget=budget)
            r0 = time.time()
            try:
                out = RA.run_kafarmtwin_typed_repair(
                    task=task, registry=registry, budget=budget, llm_call_fn=llm)
                out = RA.canonicalize_output(out)
            except Exception as e:  # noqa
                out = {"nodes": [], "edges": [], "bindings": [], "traceSteps": [],
                       "fallback": True, "success": False}
            rec = {
                "task_id": task.get("task_id"), "method": f"KAFarmTwin-{name}",
                "variant": name, "run_id": run_i + 1,
                "latency_ms": round((time.time() - r0) * 1000, 1),
                "construction_path": out.get("construction_path"),
                **_eval_dict(task, out, proxy.calls(), budget),
            }
            rec = stamp_record(rec)
            records.append(rec)
    return records


def main():
    client = LLMClient()
    if not client.is_configured():
        print("[ablation] ERROR: no AGNES_API_KEY")
        return 2
    llm = make_llm_call_fn(client)
    tasks = load_split("test", None)
    runs = 5
    results_dir = ROOT / "experiments" / "v3" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    summary = {}
    for name, env_var in ABLATIONS.items():
        print(f"[ablation] running {name} ({env_var}) ...")
        recs = run_variant(name, env_var, tasks, llm, runs)
        out_path = results_dir / f"v3_runs_ablation_{name}.jsonl"
        with out_path.open("w", encoding="utf-8") as fh:
            for r in recs:
                fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
        agg = aggregate([_rec_to_taskeval(r) for r in recs])
        summary[name] = agg
        print(f"  {name}: CVSR={agg.get('mean_cvsr',0):.4f} "
              f"objF1={agg.get('object_f1',0):.4f} critR={agg.get('critical_recall',0):.4f} "
              f"bindF1={agg.get('binding_f1',0):.4f} cost={agg.get('cost_mean',0):.6f}")
    # Also run full (no env) for comparison.
    print("[ablation] running full (no ablation) ...")
    recs = run_variant("full", "KAFARMTWIN_UNUSED", tasks, llm, runs)
    out_path = results_dir / "v3_runs_ablation_full.jsonl"
    with out_path.open("w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    agg = aggregate([_rec_to_taskeval(r) for r in recs])
    summary["full"] = agg
    print(f"  full: CVSR={agg.get('mean_cvsr',0):.4f} objF1={agg.get('object_f1',0):.4f} "
          f"critR={agg.get('critical_recall',0):.4f} bindF1={agg.get('binding_f1',0):.4f} "
          f"cost={agg.get('cost_mean',0):.6f}")
    with (results_dir / "v3_ablation_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print(f"[ablation] done -> {results_dir}")


if __name__ == "__main__":
    raise SystemExit(main())
