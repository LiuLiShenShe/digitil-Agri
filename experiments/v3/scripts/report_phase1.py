#!/usr/bin/env python3
"""Phase 1 (80-run) per-category aggregation + report.

Reads results/v3_diagnostic_80_<FREEZE_ID>.jsonl and prints the five-category
result table plus the integrity/health checks the Phase-1 decision requires:
  scene/asset/bind/repair/memory per-method CVSR, CritR, BindF1, RelF1, RepairOK
  Fatal rate, Repair Success, Replay Success, Cost ratio, Token ratio,
  API-error rate, empty-node rate.

This is a REPORT-ONLY script. It never modifies frozen code, benchmark, or scorer.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "experiments" / "v3" / "results"


def load(fname: str) -> list[dict]:
    out = []
    for l in (RESULTS / fname).read_text(encoding="utf-8").splitlines():
        if l.strip():
            out.append(json.loads(l))
    return out


def cat_of(task_id: str) -> str:
    # TNxx-v2-<cat> where cat in {scene,asset,bind,repair,mem}
    for c in ("scene", "asset", "bind", "repair", "mem"):
        if task_id.endswith(f"-{c}") or f"-{c}-" in task_id:
            return c
    return "other"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", default="freeze-2026-08-20-e3e8351")
    ap.add_argument("--max", type=int, default=None)
    args = ap.parse_args()
    fname = f"v3_diagnostic_80_{args.freeze}.jsonl"
    recs = load(fname)
    if args.max:
        recs = recs[: args.max]
    if not recs:
        print(f"no records in {fname}")
        return 1

    # sanity: provenance fields present?
    missing = [k for k in ("run_uuid", "git_commit", "evaluator_version", "freeze_id",
                           "construction_path", "repeat") if k not in recs[0]]
    if missing:
        print(f"WARNING: first record missing provenance fields: {missing}")
    print(f"records: {len(recs)}  freeze={args.freeze}")

    # ---- per-category x method table ----
    groups: dict[tuple, dict] = defaultdict(lambda: {
        "n": 0, "cvsr": 0, "critR": [], "bindF1": [], "relF1": [], "repair_ok": 0,
        "fatal": 0, "replay": [], "empty": 0, "api_err": 0,
        "tokens": 0, "cost": 0.0, "objF1": [],
    })
    api_errors = 0
    total = 0
    for r in recs:
        total += 1
        cat = cat_of(r.get("task_id", ""))
        m = r.get("method", "?")
        g = groups[(cat, m)]
        g["n"] += 1
        if r.get("cvsr"):
            g["cvsr"] += 1
        g["critR"].append(r.get("critical_recall") or 0)
        g["bindF1"].append(r.get("binding_f1") or 0)
        g["relF1"].append(r.get("relation_f1") or 0)
        g["objF1"].append(r.get("object_f1") or 0)
        if r.get("repair_success") is True:
            g["repair_ok"] += 1
        if r.get("fatal_violations"):
            g["fatal"] += 1
        g["replay"].append(r.get("replay_success") or 0)
        if r.get("error"):
            api_errors += 1
            g["api_err"] += 1
        g["tokens"] += r.get("tokens") or 0
        g["cost"] += r.get("cost") or 0
        if not r.get("n_nodes", 0):
            g["empty"] += 1

    print(f"\n{'Cat':>6s}  {'Method':>30s}  {'n':>3s}  {'CVSR':>6s}  {'CritR':>6s}  "
          f"{'ObjF1':>6s}  {'RelF1':>6s}  {'BindF1':>6s}  {'Repair':>6s}  "
          f"{'Fatal':>5s}  {'Replay':>6s}  {'Empty':>5s}  {'Tok':>7s}  {'Cost':>7s}")
    print("-" * 120)
    for (cat, m), g in sorted(groups.items()):
        n = g["n"]
        cv = g["cvsr"] / n if n else 0
        crit = sum(g["critR"]) / len(g["critR"]) if g["critR"] else 0
        obj = sum(g["objF1"]) / len(g["objF1"]) if g["objF1"] else 0
        rel = sum(g["relF1"]) / len(g["relF1"]) if g["relF1"] else 0
        bind = sum(g["bindF1"]) / len(g["bindF1"]) if g["bindF1"] else 0
        rep = g["repair_ok"] / n if n else 0
        fat = g["fatal"] / n if n else 0
        reply = sum(g["replay"]) / len(g["replay"]) if g["replay"] else 0
        empty = g["empty"] / n if n else 0
        print(f"{cat:>6s}  {m:>30s}  {n:>3d}  {cv:>6.3f}  {crit:>6.3f}  {obj:>6.3f}  "
              f"{rel:>6.3f}  {bind:>6.3f}  {rep:>6.3f}  {fat:>5.3f}  {reply:>6.3f}  "
              f"{empty:>5.3f}  {g['tokens']:>7d}  {g['cost']:>7.5f}")

    # ---- overall integrity / health ----
    methods = sorted({r.get("method") for r in recs})
    print("\n--- Integrity / health (per method) ---")
    for m in methods:
        sub = [r for r in recs if r.get("method") == m]
        n = len(sub)
        api = sum(1 for r in sub if r.get("error"))
        empty = sum(1 for r in sub if not r.get("n_nodes", 0))
        print(f"  {m:30s} n={n:3d} api_errors={api:2d} empty_nodes={empty:2d} "
              f"eval_hash_ok={sum(1 for r in sub if (r.get('evaluator_hash') or '').startswith('8b7d4695'))}/{n}")
    print(f"\nTotal: {total} runs. API/error records: {api_errors}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
