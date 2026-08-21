"""Phase 3.3 focused live validation: TN21-24 bind tasks only.

Confirms the `timestamp` prompt fix in `bindings_only_scene` changes BindF1.
Writes to v3_runs_bind_validate.jsonl (separate from frozen v3_runs.jsonl).
"""
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, str(ROOT))

from experiments.v3.scripts.run_fair_baselines import (  # type: ignore
    load_split, run_one_method, make_llm_call_fn, LLMClient,
)
from experiments.v3.evaluators.version import stamp_record as _stamp  # type: ignore

RESULTS_DIR = ROOT / "experiments" / "v3" / "results"
OUT = RESULTS_DIR / "v3_runs_bind_validate.jsonl"
OUT = RESULTS_DIR / "v3_runs_bind_validate.jsonl"


def main():
    client = LLMClient()
    if not client.is_configured():
        print("[validate] ERROR: no AGNES_API_KEY set")
        return 2
    llm_call_fn = make_llm_call_fn(client)

    tasks = load_split("test", None)
    bind_tasks = [t for t in tasks if "bind" in t.get("task_id", "").lower()]
    print(f"[validate] bind tasks = {[t['task_id'] for t in bind_tasks]}")

    methods = ["KAFarmTwin-TypedRepair", "SingleAgent-AllTools"]
    runs = int(os.getenv("VALIDATE_RUNS", "3"))
    records = []
    t0 = time.time()
    for task in bind_tasks:
        for method in methods:
            for run_i in range(runs):
                rec = run_one_method(method, task, llm_call_fn)
                rec["run_id"] = run_i + 1
                rec = _stamp(rec)
                records.append(rec)
                with OUT.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
                print(f"  {task['task_id']} {method} #{run_i+1}: "
                      f"cvsr={rec.get('cvsr')} bindF1={rec.get('binding_f1')} "
                      f"cost={rec.get('cost')} rounds={rec.get('repair_rounds')}")
    print(f"[validate] done in {time.time()-t0:.1f}s -> {OUT}")


if __name__ == "__main__":
    raise SystemExit(main())
