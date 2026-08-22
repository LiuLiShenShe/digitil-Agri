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

Writes one file per variant (distinct from frozen v3_runs.jsonl), APPENDING per-run
so progress is observable and a crash loses at most the in-flight run:
  experiments/v3/results/v3_runs_ablation_A1.jsonl
  experiments/v3/results/v3_runs_ablation_A2.jsonl
  experiments/v3/results/v3_runs_ablation_A3.jsonl
  experiments/v3/results/v3_runs_ablation_full.jsonl
"""
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from experiments.v3.scripts.run_fair_baselines import (  # type: ignore
    load_split, make_llm_call_fn, LLMClient, _rec_to_taskeval, run_one_method,
)
from experiments.v3.evaluators.metrics import aggregate  # type: ignore


ABLATIONS = {
    "A1_no_compiler": "KAFARMTWIN_ABLATE_COMPILER",
    "A2_no_typed_repair": "KAFARMTWIN_ABLATE_REPAIR",
    "A3_no_ontology": "KAFARMTWIN_ABLATE_ONTOLOGY",
}


def run_variant(name, env_var, tasks, llm, runs, results_dir):
    """Run one ablation variant via the SAME run_one_method path as the gate
    (so memory_state seeding, canonical evaluation, gold handling are identical).
    Only the env hook differs between variants. Writes per-run, prints progress."""
    # Clear any other ablation env, set this one.
    for ev in ABLATIONS.values():
        os.environ.pop(ev, None)
    if env_var != "KAFARMTWIN_UNUSED":
        os.environ[env_var] = "1"

    out_path = results_dir / f"v3_runs_ablation_{name}.jsonl"
    with out_path.open("w", encoding="utf-8") as fh:
        pass

    recs = []
    t_start = time.time()
    total = len(tasks) * runs
    done = 0
    for task in tasks:
        for run_i in range(runs):
            try:
                rec = run_one_method(
                    method="KAFarmTwin-TypedRepair", task=task,
                    llm_call_fn=llm, mock=False)
            except Exception as e:  # noqa
                rec = {"task_id": task.get("task_id"), "method": "KAFarmTwin-TypedRepair",
                       "cvsr": False, "binding_f1": 0.0, "cost": 0.0,
                       "repair_rounds": 0, "fatal_violations": 1,
                       "object_f1": 0.0, "relation_f1": 0.0, "critical_recall": 0.0,
                       "error": str(e)}
            rec["variant"] = name
            rec["run_id"] = run_i + 1
            recs.append(rec)
            with out_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
            done += 1
            print(f"  [{name}] {done}/{total} {task.get('task_id')} #{run_i+1}: "
                  f"cvsr={rec.get('cvsr')} bindF1={rec.get('binding_f1')} "
                  f"cost={rec.get('cost')} rounds={rec.get('repair_rounds')}", flush=True)
    agg = aggregate([_rec_to_taskeval(r) for r in recs])
    print(f"  [{name}] DONE in {time.time()-t_start:.1f}s: "
          f"CVSR={agg.get('mean_cvsr',0):.4f} objF1={agg.get('object_f1',0):.4f} "
          f"critR={agg.get('critical_recall',0):.4f} bindF1={agg.get('binding_f1',0):.4f} "
          f"cost={agg.get('cost_mean',0):.6f}", flush=True)
    return agg


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
    print(f"[ablation] {len(tasks)} tasks x {runs} runs, variants: "
          f"{list(ABLATIONS.keys())} + full", flush=True)

    summary = {}
    for name, env_var in ABLATIONS.items():
        print(f"[ablation] >>> {name} ({env_var})", flush=True)
        summary[name] = run_variant(name, env_var, tasks, llm, runs, results_dir)
    print("[ablation] >>> full (no ablation)", flush=True)
    summary["full"] = run_variant("full", "KAFARMTWIN_UNUSED", tasks, llm, runs, results_dir)

    with (results_dir / "v3_ablation_summary.json").open("w", encoding="utf-8") as fh:
        json.dump({k: {kk: vv for kk, vv in v.items()} for k, v in summary.items()}, fh, indent=2)
    print(f"[ablation] ALL DONE -> {results_dir}", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
