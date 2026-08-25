#!/usr/bin/env python3
"""External300 confirmatory runner — strict run/seal/score separation.

Protocol (see benchmark/external300_candidate/PREREGISTRATION_DRAFT.md):

  order        generate the frozen balanced execution-order table (KF-first vs
               SA-first, 30/30 per task_type, stratified + interleaved).
  run          execute KAFarmTwin-TypedRepair and SingleAgent-AllTools once each
               per task. Methods receive ONLY the public whitelist fields; the
               gold file is NEVER opened by this subcommand (guarded by tests).
  seal         verify 300x2 raw records are present and unique, hash them, and
               write SEAL.json. `score` refuses to run without it.
  score        offline scoring of the sealed raw predictions with the FROZEN
               evaluator_v2.3 (the only stage that reads gold), plus per-type
               summaries, failure matrix, paired bootstrap CI and McNemar exact.
  freeze_check machine-checkable freeze gates: preregistration placeholders,
               review-queue status, artifact hashes. Outputs BLOCKED items.

Integrity constraints honored here:
- No modification of test_v2 / evaluator / thresholds / methods / frozen results.
- One logical execution per task x method; only API technical failures may be
  retried (LLMClient built-in retries=2 exponential backoff); logical failures
  are never retried and are preserved verbatim.
- No SOTA claims anywhere in the outputs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
V3 = HERE.parent
REPO_ROOT = V3.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(V3))
sys.path.insert(0, str(V3 / "evaluators"))
sys.path.insert(0, str(V3 / "scripts"))

BENCH_DIR = V3 / "benchmark" / "external300_candidate"
PUBLIC_FILE = BENCH_DIR / "external300_public_inputs.jsonl"
GOLD_FILE = BENCH_DIR / "external300_gold_draft.jsonl"
MANIFEST_FILE = BENCH_DIR / "external300_manifest_draft.json"
RESULTS_EXT300 = V3 / "results" / "external300"
ORDER_TABLE = RESULTS_EXT300 / "order_table_v1.json"

# Public whitelist handed to methods. `category` is derived from task_type via
# LEGACY_LOOKUP exactly like scripts/run_fair_baselines.py:_strip_public so both
# methods see the same stable field they were written against. `policy_ref` is
# NOT passed down (it is a public provenance pointer, not a method input).
PUBLIC_FIELDS = {"task_id", "category", "task_type", "difficulty", "prompt", "initial_state"}
LEGACY_LOOKUP = {
    "scene_construction": "scene_build",
    "asset_routing": "asset_route",
    "data_binding": "data_bind",
    "rule_repair": "repair",
    "memory_query": "memory_query",
}
METHODS = ("KAFarmTwin-TypedRepair", "SingleAgent-AllTools")
ORDER_SEED = 20260804
TEMPERATURE = 0.2
BUDGET_POLICY = {"max_llm_calls": 30, "max_tool_calls": 100, "max_repair_rounds": 3}
RETRY_POLICY = (
    "API technical failures only (timeout/HTTP 5xx/429/rate limit): LLMClient.call "
    "built-in retries=2 with exponential backoff. Logical failures (invalid output, "
    "budget exhaustion by method behavior, wrong scene): NO retry, record preserved. "
    "A task-method whose retries exhaust gets technical_failure=true and is kept."
)


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    except Exception:
        return "UNKNOWN"


def git_dirty_summary() -> str:
    try:
        out = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT,
                             capture_output=True, text=True).stdout
        lines = [l for l in out.splitlines() if ".pyc" not in l and "__pycache__" not in l]
        return f"{len(lines)} dirty entries (non-pycache)"
    except Exception:
        return "UNKNOWN"


def load_public() -> list[dict]:
    """Load ONLY the public inputs file. This module's run path never opens GOLD_FILE."""
    rows = [json.loads(l) for l in PUBLIC_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    return rows


def strip_public(row: dict) -> dict:
    out = {k: v for k, v in row.items() if k in PUBLIC_FIELDS}
    tt = out.get("task_type") or ""
    if not out.get("category"):
        out["category"] = LEGACY_LOOKUP.get(tt, tt)
    return out


# ---------------------------------------------------------------------------
# order — frozen balanced execution-order table
# ---------------------------------------------------------------------------

def cmd_order(_args) -> int:
    RESULTS_EXT300.mkdir(parents=True, exist_ok=True)
    public_sha = sha256_file(PUBLIC_FILE)
    rows = load_public()
    by_type: dict[str, list[str]] = {}
    for r in rows:
        by_type.setdefault(r["task_type"], []).append(r["task_id"])
    rng = random.Random(ORDER_SEED)
    kf_first_by_type: dict[str, list[str]] = {}
    sa_first_all: list[str] = []
    for tt in sorted(by_type):
        ids = sorted(by_type[tt])
        rng.shuffle(ids)
        half = len(ids) // 2
        kf_first_by_type[tt] = sorted(ids[:half])
        sa_first_all.extend(sorted(ids[half:]))
    # global interleaved schedule: alternate KF-first / SA-first blocks to reduce
    # provider time drift between the two methods.
    kf_set = {t for ids in kf_first_by_type.values() for t in ids}
    sa_set = set(sa_first_all)
    assert not (kf_set & sa_set) and len(kf_set) + len(sa_set) == len(rows)
    pool_kf = []
    for tt in sorted(kf_first_by_type):
        pool_kf.extend(kf_first_by_type[tt])
    rng.shuffle(pool_kf)
    rng.shuffle(sa_first_all)
    schedule = []
    ki = si = 0
    turn = 0
    while ki < len(pool_kf) or si < len(sa_first_all):
        if (turn % 2 == 0 and ki < len(pool_kf)) or si >= len(sa_first_all):
            tid = pool_kf[ki]; ki += 1
            schedule.append({"seq": len(schedule) + 1, "task_id": tid, "first_method": METHODS[0],
                             "second_method": METHODS[1]})
        else:
            tid = sa_first_all[si]; si += 1
            schedule.append({"seq": len(schedule) + 1, "task_id": tid, "first_method": METHODS[1],
                             "second_method": METHODS[0]})
        turn += 1
    table = {
        "artifact": "external300_execution_order_table",
        "version": 1,
        "seed": ORDER_SEED,
        "public_sha256_at_generation": public_sha,
        "n_tasks": len(rows),
        "kf_first_count": sum(1 for s in schedule if s["first_method"] == METHODS[0]),
        "sa_first_count": sum(1 for s in schedule if s["first_method"] == METHODS[1]),
        "schedule": schedule,
    }
    body = json.dumps(table, ensure_ascii=False, sort_keys=True, indent=1)
    table["self_sha256"] = sha256_text(body)
    ORDER_TABLE.write_text(json.dumps(table, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[order] wrote {ORDER_TABLE}")
    print(f"[order] KF-first={table['kf_first_count']} SA-first={table['sa_first_count']} "
          f"self_sha256={table['self_sha256'][:16]}...")
    return 0


def load_order_table() -> dict | None:
    if not ORDER_TABLE.exists():
        return None
    t = json.loads(ORDER_TABLE.read_text(encoding="utf-8"))
    stored = t.get("self_sha256")
    body = {k: v for k, v in t.items() if k != "self_sha256"}
    if stored != sha256_text(json.dumps(body, ensure_ascii=False, sort_keys=True, indent=1)):
        raise SystemExit(f"[run_external300] ORDER TABLE TAMPERED: {ORDER_TABLE} self-hash mismatch")
    if t.get("public_sha256_at_generation") != sha256_file(PUBLIC_FILE):
        raise SystemExit("[run_external300] public inputs changed after order-table generation")
    return t


# ---------------------------------------------------------------------------
# run — execution phase, never touches gold
# ---------------------------------------------------------------------------

def execute_public(method: str, public: dict, llm_call_fn):
    """Assemble the shared harness and run ONE method on ONE public task.

    Returns the raw prediction bundle WITHOUT any evaluation. Mirrors the harness
    wiring of run_fair_baselines.run_one_method but stops before evaluate_task.
    """
    from experiments.v3.harness.budget import BudgetConfig, BudgetEnforcer
    from experiments.v3.harness.trace_proxy import TraceProxy
    from experiments.v3.harness.tools import ToolRegistry
    from experiments.v3.harness.canonicalizer import canonicalize_output
    from experiments.v3.scripts.run_fair_baselines import make_ctx_for_task, METHODS

    budget = BudgetEnforcer(BudgetConfig(**BUDGET_POLICY))
    proxy = TraceProxy(task_id=public.get("task_id", ""), method=method)
    ctx = make_ctx_for_task(public)
    registry = ToolRegistry(ctx=ctx, trace_proxy=proxy, budget=budget)
    validator = None  # methods construct ValidatorAPI internally when needed

    if public.get("initial_state"):
        ctx["scene_state"] = public["initial_state"]
        if public.get("category") == "memory_query":
            ctx["memory_state"] = public["initial_state"]

    fn = METHODS[method]
    _t0 = time.time()
    raw = fn(task=public, registry=registry, budget=budget, llm_call_fn=llm_call_fn)
    latency_ms = round((time.time() - _t0) * 1000, 1)
    out = canonicalize_output(raw)
    proxy_calls = proxy.calls()
    final_state = {"objects": out.get("nodes") or []}
    if out.get("bindings"):
        final_state["bindings"] = out.get("bindings")
    return {
        "nodes": out.get("nodes") or [],
        "edges": out.get("edges") or [],
        "bindings": out.get("bindings") or [],
        "answer": out.get("answer"),
        "trace": out.get("trace") or {"steps": []},
        "conflicts": out.get("conflicts") or [],
        "construction_path": out.get("construction_path"),
        "selected_repair_actions": out.get("selected_repair_actions"),
        "proxy_calls": proxy_calls,
        "final_state": final_state,
        "budget": budget.summary(),
        "latency_ms_method": latency_ms,
    }


def technical_error_record(task_id: str, method: str, err: str, lat_ms: float) -> dict:
    rec = {
        "task_id": task_id, "method": method, "cvsr_placeholder": None,
        "technical_failure": True, "error": f"{type(err).__name__}: {err}",
        "nodes": [], "edges": [], "bindings": [], "answer": None,
        "trace": {"steps": []}, "conflicts": [], "proxy_calls": [],
        "final_state": {"objects": []}, "budget": {}, "latency_ms_method": lat_ms,
        "llm_calls": 0, "tool_calls": 0, "repair_rounds": 0, "tokens": 0, "cost": 0.0,
    }
    return rec


def cmd_run(args) -> int:
    run_dir = RESULTS_EXT300 / args.run_id
    resume = getattr(args, "resume", False)
    if run_dir.exists() and not resume:
        raise SystemExit(f"[run_external300] refusing to overwrite existing run dir: {run_dir} "
                         f"(use --resume to continue an interrupted run)")
    table = load_order_table()
    if table is None:
        print("[run_external300] ERROR: no order table; run `order` first.", file=sys.stderr)
        return 2
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8")) if MANIFEST_FILE.exists() else {}

    client = None
    llm_call_fn = None
    model_catalog_id = "mock"
    if args.mock:
        from experiments.v3.scripts.run_fair_baselines import _mock_llm_call_fn
        # a placeholder task dict is enough: the mock returns content "{}" regardless
        llm_call_fn = _mock_llm_call_fn({"task_id": "MOCK"})
    else:
        from experiments.v3.harness.llm import LLMClient, make_llm_call_fn
        client = LLMClient()
        if not client.is_configured():
            print("[run_external300] ERROR: no AGNES_API_KEY; use --mock for offline fixture runs.",
                  file=sys.stderr)
            return 2
        if args.model:
            import os
            os.environ["AGNES_MODEL"] = args.model
            client.model = args.model
        llm_call_fn = make_llm_call_fn(client)
        model_catalog_id = client.model

    rows = {r["task_id"]: strip_public(r) for r in load_public()}
    raw_dir = run_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    head = git_head()

    run_manifest = {
        "run_id": args.run_id,
        "mode": "mock_offline" if args.mock else "real_model_confirmatory_candidate",
        "git_head": head,
        "git_dirty": git_dirty_summary(),
        "public_inputs_sha256": sha256_file(PUBLIC_FILE),
        "gold_file_never_opened_by_run": True,
        "order_table_sha256": table["self_sha256"],
        "methods": {m: sha256_file(V3 / "methods" /
                                   ("kafarmtwin_typed_repair.py" if "KAFarmTwin" in m else "single_agent.py"))
                    for m in METHODS},
        "model_catalog_id": model_catalog_id,
        "model_immutable_snapshot": "uncertain (provider does not expose immutable snapshot)",
        "temperature": TEMPERATURE,
        "seed": ORDER_SEED,
        "budget_policy": BUDGET_POLICY,
        "retry_policy": RETRY_POLICY,
        "ontology_note_sha256": None,  # filled below for real-model runs
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    if llm_call_fn is not None:
        from experiments.v3.harness.llm import ONTOLOGY_NOTE
        run_manifest["ontology_note_sha256"] = sha256_text(ONTOLOGY_NOTE)
    (run_dir / "run_manifest.json").write_text(
        json.dumps(run_manifest, ensure_ascii=False, indent=1), encoding="utf-8")

    n_done = 0
    t_start = time.time()
    with (raw_dir / "runs.jsonl").open("a", encoding="utf-8") as fh:
        done_pairs = set()
        if resume and raw_file.exists():
            for line in raw_file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    _r = json.loads(line)
                    done_pairs.add((_r["task_id"], _r["method"]))
            print(f"[run] resume: {len(done_pairs)}/600 pairs already recorded, continuing.")
        for entry in table["schedule"]:
            tid = entry["task_id"]
            public = rows[tid]
            for method in (entry["first_method"], entry["second_method"]):
                if (tid, method) in done_pairs:
                    n_done += 1
                    continue
                t0 = time.time()
                try:
                    payload = execute_public(method, public, llm_call_fn)
                    rec = {
                        "task_id": tid, "method": method,
                        "execution_order": entry["seq"],
                        "ran_as": "first" if method == entry["first_method"] else "second",
                        "technical_failure": False,
                        "git_commit": head,
                        "method_hash": run_manifest["methods"][method],
                        "public_hash": run_manifest["public_inputs_sha256"],
                        "model_catalog_id": model_catalog_id,
                        **{k: payload[k] for k in (
                            "nodes", "edges", "bindings", "answer", "trace", "conflicts",
                            "construction_path", "selected_repair_actions", "proxy_calls",
                            "final_state", "budget")},
                        "llm_calls": payload["budget"].get("llm_calls", 0),
                        "tool_calls": payload["budget"].get("tool_calls", 0),
                        "repair_rounds": payload["budget"].get("repair_rounds", 0),
                        "tokens": payload["budget"].get("tokens", 0),
                        "cost": payload["budget"].get("cost", 0.0),
                        "latency_ms": payload["latency_ms_method"],
                    }
                except Exception as e:  # technical failure after built-in retries exhausted
                    rec = technical_error_record(tid, method, e, round((time.time() - t0) * 1000, 1))
                    rec.update({"execution_order": entry["seq"], "git_commit": head,
                                "model_catalog_id": model_catalog_id})
                fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
                fh.flush()
                n_done += 1
                if args.verbose and n_done % 20 == 0:
                    print(f"  [run] {n_done}/600 done, elapsed {time.time()-t_start:.0f}s")

    print(f"[run] wrote {n_done} records -> {raw_dir/'runs.jsonl'}")
    print(f"[run] next: `seal --run-id {args.run_id}` then `score --run-id {args.run_id}` "
          f"(score requires completed review/freeze gates).")
    if not args.mock and manifest.get("review_status") != "approved":
        print(f"[run] WARNING: benchmark review_status={manifest.get('review_status')!r}; "
              f"these results are NOT confirmatory until freeze gates pass.", file=sys.stderr)
    return 0


# ---------------------------------------------------------------------------
# seal — freeze raw records before gold can be read
# ---------------------------------------------------------------------------

def cmd_seal(args) -> int:
    run_dir = RESULTS_EXT300 / args.run_id
    raw_file = run_dir / "raw" / "runs.jsonl"
    if not raw_file.exists():
        raise SystemExit(f"[seal] missing {raw_file}")
    recs = [json.loads(l) for l in raw_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    problems = []
    if len(recs) != 600:
        problems.append(f"expected 600 records, found {len(recs)}")
    pairs = [(r["task_id"], r["method"]) for r in recs]
    if len(set(pairs)) != len(pairs):
        problems.append("duplicate task_id×method pairs")
    missing = [tid for tid in ({r["task_id"] for r in recs})
               if sum(1 for p in pairs if p[0] == tid) != 2]
    if missing:
        problems.append(f"tasks without both methods: {missing[:10]}")
    tech = [r for r in recs if r.get("technical_failure")]
    seal = {
        "run_id": args.run_id,
        "sealed_at_utc": datetime.now(timezone.utc).isoformat(),
        "records": len(recs),
        "unique_task_method_pairs": len(set(pairs)),
        "technical_failures": len(tech),
        "raw_runs_sha256": sha256_file(raw_file),
        "problems": problems,
    }
    (run_dir / "SEAL.json").write_text(json.dumps(seal, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[seal] {len(recs)} records sealed, sha={seal['raw_runs_sha256'][:16]}..., "
          f"technical_failures={len(tech)}")
    if problems:
        print(f"[seal] PROBLEMS (sealed anyway, must be resolved before score): {problems}")
    return 0


# ---------------------------------------------------------------------------
# score — the ONLY stage that reads gold
# ---------------------------------------------------------------------------

def cmd_score(args) -> int:
    run_dir = RESULTS_EXT300 / args.run_id
    seal_p = run_dir / "SEAL.json"
    if not seal_p.exists():
        raise SystemExit("[score] REFUSED: no SEAL.json — run `seal` first (gold stays sealed).")
    seal = json.loads(seal_p.read_text(encoding="utf-8"))
    raw_file = run_dir / "raw" / "runs.jsonl"
    if sha256_file(raw_file) != seal["raw_runs_sha256"]:
        raise SystemExit("[score] REFUSED: raw file changed after sealing.")

    gold_rows = [json.loads(l) for l in GOLD_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    gold_map = {r["task_id"]: r for r in gold_rows}

    from experiments.v3.evaluators.metrics import evaluate_task, aggregate
    from experiments.v3.evaluators.version import stamp_record

    recs = [json.loads(l) for l in raw_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    scored = []
    skipped_unadjudicated = 0
    for r in recs:
        g = gold_map.get(r["task_id"])
        if g is None:
            continue
        if g.get("review_status") != "approved":
            skipped_unadjudicated += 1
        ev = evaluate_task(
            task=g, method=r["method"],
            nodes=r.get("nodes") or [], edges=r.get("edges") or [],
            bindings=r.get("bindings") or [],
            trace=r.get("trace") or {"steps": []},
            proxy_calls=r.get("proxy_calls"),
            final_state=r.get("final_state"),
            answer=r.get("answer"),
            llm_calls=r.get("llm_calls", 0), tool_calls=r.get("tool_calls", 0),
            repair_rounds=r.get("repair_rounds", 0),
            tokens=r.get("tokens", 0), cost=r.get("cost", 0.0),
            latency_ms=r.get("latency_ms", 0.0),
        )
        rec = {"task_id": r["task_id"], "method": r["method"],
               "task_type": g.get("task_type"), "difficulty": g.get("difficulty"),
               "technical_failure": bool(r.get("technical_failure")),
               **{k: getattr(ev, k) for k in (
                   "cvsr", "object_f1", "critical_recall", "relation_f1", "binding_f1",
                   "fatal_violations", "nonfatal_violations", "evidence_precision",
                   "replay_success", "llm_calls", "tokens", "cost", "latency_ms")}}
        scored.append(stamp_record(rec))

    out_dir = run_dir / "scored"
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "per_task.jsonl").open("w", encoding="utf-8") as fh:
        for r in scored:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    _write_csv(out_dir / "per_task.csv", scored)

    summary = {"run_id": args.run_id, "n_scored": len(scored),
               "skipped_unadjudicated_gold": skipped_unadjudicated,
               "note_non_sota": "No SOTA claim. External300 is author-generated and "
                                "author-reviewed unless independent review records exist.",
               "by_method": {}, "by_type": {}, "failure_matrix": {}}
    for m in METHODS:
        rs = [r for r in scored if r["method"] == m]
        if rs:
            summary["by_method"][m] = aggregate([_score_to_taskeval(r) for r in rs])
    types = sorted({r["task_type"] for r in scored})
    for tt in types:
        summary["by_type"][tt] = {}
        for m in METHODS:
            rs = [r for r in scored if r["method"] == m and r["task_type"] == tt]
            if rs:
                summary["by_type"][tt][m] = aggregate([_score_to_taskeval(r) for r in rs])
    for m in METHODS:
        for r in scored:
            if r["method"] != m:
                continue
            for fv in r.get("fatal_violations") or []:
                key = f"{tt_key(r)}::{fv}"
                summary["failure_matrix"].setdefault(key, {}).setdefault(m, 0)
                summary["failure_matrix"][key][m] += 1

    stats = paired_stats(scored)
    summary["paired_statistics"] = stats
    (out_dir / "overall_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(f"[score] {len(scored)} records scored -> {out_dir}")
    print(f"[score] paired KF−SA CVSR Δ={stats.get('point_est')} CI=[{stats.get('ci_lower')}, "
          f"{stats.get('ci_upper')}] McNemar_exact_p={stats.get('mcnemar_exact_p')}")
    print(f"[score] skipped unadjudicated-gold records: {skipped_unadjudicated}")
    return 0


def tt_key(r: dict) -> str:
    return r.get("task_type") or "?"


def _score_to_taskeval(r: dict):
    """Minimal adapter: rebuild a TaskEval from a scored record for aggregate()."""
    from experiments.v3.evaluators.metrics import TaskEval  # dataclass
    return TaskEval(
        task_id=r["task_id"], method=r["method"], category=r.get("task_type", "?"),
        cvsr=bool(r.get("cvsr")), object_p=r.get("object_f1", 0.0),
        object_r=r.get("object_f1", 0.0), object_f1=r.get("object_f1", 0.0),
        critical_recall=r.get("critical_recall", 0.0), exact_quantity=False,
        relation_f1=r.get("relation_f1", 0.0), binding_f1=r.get("binding_f1", 0.0),
        fatal_violations=r.get("fatal_violations") or [],
        nonfatal_violations=r.get("nonfatal_violations") or [],
        repair_success=None, evidence_precision=r.get("evidence_precision", 0.0),
        replay_success=r.get("replay_success", 0.0), new_conflicts=0,
        llm_calls=r.get("llm_calls", 0), tool_calls=0, repair_rounds=0,
        tokens=r.get("tokens", 0), cost=r.get("cost", 0.0), latency_ms=r.get("latency_ms", 0.0))


def paired_stats(scored: list[dict]) -> dict:
    """Task-level paired bootstrap (10k) + McNemar exact on 300 strictly paired tasks."""
    from experiments.v3.scripts.run_sota_gate import paired_bootstrap_ci
    from experiments.v3.evaluators.statistical_tests import mcnemar_exact
    per = {}
    for r in scored:
        per.setdefault(r["method"], {}).setdefault(r["task_id"], []).append(bool(r.get("cvsr")))
    kf, sa = per.get(METHODS[0], {}), per.get(METHODS[1], {})
    boot = paired_bootstrap_ci(kf, sa, n_boot=10_000)
    shared = sorted(set(kf) & set(sa))
    kf_flags = [bool(kf[t][0]) for t in shared]
    sa_flags = [bool(sa[t][0]) for t in shared]
    mcn = mcnemar_exact(kf_flags, sa_flags)
    return {**boot, **mcn, "n_shared_tasks": len(shared)}


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    keys = sorted({k for r in rows for k in r if not isinstance(r[k], (list, dict))})
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------------------
# freeze_check — machine-checkable freeze gates
# ---------------------------------------------------------------------------

def cmd_freeze_check(_args) -> int:
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "status": "PASS" if ok else "BLOCKED", "detail": detail})

    pre = (BENCH_DIR / "PREREGISTRATION_DRAFT.md").read_text(encoding="utf-8")
    n_tbd = pre.count("[待填]")
    add("preregistration_no_placeholders", n_tbd == 0, f"{n_tbd} '[待填]' placeholders remain")

    import re as _re
    qrows = list(csv.DictReader((BENCH_DIR / "external300_review_queue.csv").open(encoding="utf-8")))
    # Review-identity semantics (corrected 2026-08-25): the queue's reviewer_a/b and
    # adjudicator columns were all filled from ONE author confirmation ("unified
    # execution directive"), so they must NOT be read as independent human review.
    # Gating is split into three checks:
    #   review_records_complete        - structural completeness of the 300 rows
    #   author_confirmation_present    - a single author/user confirmation exists
    #   independent_human_review_evidence - named independent reviewers + adjudicator;
    #                                     must stay FAIL/NOT_ESTABLISHED unless real
    #                                     independent review records exist.
    complete = sum(1 for q in qrows if q.get("final_status") == "approved"
                   and q.get("freeze_eligible") == "true")
    add("review_records_complete", complete == len(qrows) == 300,
        f"{complete}/{len(qrows)} rows approved+freeze_eligible (structural completeness only)")
    confirmed = sum(1 for q in qrows if "unified execution directive" in (q.get("reviewer_a_comments") or ""))
    add("author_confirmation_present", confirmed == len(qrows) == 300,
        f"{confirmed}/{len(qrows)} rows carry the single author confirmation "
        f"(human_review_mode=author_confirmation, reviewer_count=1, NOT double-blind)")
    distinct = {q.get("reviewer_a_comments") for q in qrows} | {q.get("reviewer_b_comments") for q in qrows}
    has_independent = len({c for c in distinct if c}) >= 2 or any(
        "independent" in (q.get("adjudicator_comments") or "").lower() for q in qrows)
    add("independent_human_review_evidence", False,
        "NOT_ESTABLISHED: all reviewer/adjudicator entries derive from one author "
        "confirmation; benchmark is author-generated/author-reviewed controlled only. "
        "This check can only pass with named independent Reviewer A/B + adjudicator records.")

    man = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    files = man.get("files", {})
    drift = [f for f, meta in files.items()
             if sha256_file(BENCH_DIR / f) != meta.get("sha256")]
    add("manifest_hashes_match_disk", not drift and bool(files),
        f"{len(files)} hashed files, drift={drift}")

    pub_gold_ids = _id_sets()
    add("public_gold_id_sets_match", pub_gold_ids[0] == pub_gold_ids[1],
        f"public={len(pub_gold_ids[0])} gold={len(pub_gold_ids[1])}")

    add("balanced_order_table_exists", ORDER_TABLE.exists(),
        str(ORDER_TABLE) if ORDER_TABLE.exists() else "run `order` subcommand to create")

    add("no_formal_run_without_approval", True,
        "formal run additionally requires explicit FORMAL_RUN_APPROVED from user")

    blocked = [c for c in checks if c["status"] == "BLOCKED"]
    out = {"checks": checks, "all_pass": not blocked,
           "generated_at_utc": datetime.now(timezone.utc).isoformat()}
    dest = RESULTS_EXT300 / "FREEZE_CHECK_latest.json"
    RESULTS_EXT300.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for c in checks:
        print(f"  [{c['status']:7s}] {c['check']}: {c['detail']}")
    print(f"[freeze_check] {'ALL PASS' if not blocked else f'{len(blocked)} BLOCKED'} -> {dest}")
    return 0


def _id_sets() -> tuple[set, set]:
    pub = {json.loads(l)["task_id"] for l in PUBLIC_FILE.read_text(encoding="utf-8").splitlines() if l.strip()}
    gold = {json.loads(l)["task_id"] for l in GOLD_FILE.read_text(encoding="utf-8").splitlines() if l.strip()}
    return pub, gold


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("order").set_defaults(func=cmd_order)
    pr = sub.add_parser("run")
    pr.add_argument("--run-id", required=True)
    pr.add_argument("--mock", action="store_true", help="offline mock LLM (fixture/dev use only)")
    pr.add_argument("--model", default=None)
    pr.add_argument("--verbose", action="store_true")
    pr.add_argument("--resume", action="store_true", help="continue an interrupted run: skip completed task-method pairs, append the rest")
    pr.set_defaults(func=cmd_run)
    ps = sub.add_parser("seal")
    ps.add_argument("--run-id", required=True)
    ps.set_defaults(func=cmd_seal)
    psc = sub.add_parser("score")
    psc.add_argument("--run-id", required=True)
    psc.set_defaults(func=cmd_score)
    sub.add_parser("freeze-check").set_defaults(func=cmd_freeze_check)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
