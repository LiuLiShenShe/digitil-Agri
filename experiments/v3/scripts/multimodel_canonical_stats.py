"""Canonical multimodel statistics — per-model metrics + preregistered generalization verdict.

Reads ONLY sealed runs (SEAL.json verified) + scored outputs for the four new model
blocks plus the frozen DeepSeek baseline. Offline; no API calls.

McNemar display: never "p=0"; below 1e-6 -> "p<1e-6 (exact tail …)".
Cross-model aggregation: cluster bootstrap by task_id (300 reused tasks are NOT
1500 independent samples); also emitted as exploratory-labeled.
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import sys
from math import comb, ceil
from pathlib import Path

HERE = Path(__file__).resolve().parent
V3 = HERE.parent
RES = V3 / "results" / "external300"
MM = RES / "multimodel"

KF, SA = "KAFarmTwin-TypedRepair", "SingleAgent-AllTools"
BLOCKS = {
    "DeepSeek-V4-Flash (frozen baseline)": {
        "run_id": "ext300_formal_20260825",
        "seal": "b52f00c4bee3b43723689c3556300e0754a8ab9564b96341d05e88b591d40d91",
    },
    "Pro/moonshotai/Kimi-K2.6":  {"run_id": "ext300_mm1_kimi_20260825"},
    "MiniMaxAI/MiniMax-M2.5":    {"run_id": "ext300_mm2_minimax_20260825"},
    "Qwen/Qwen3.6-27B":          {"run_id": "ext300_mm3_qwen_20260825"},
    "zai-org/GLM-5.2":           {"run_id": "ext300_mm4_glm_20260825"},
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def mcnemar(b: int, c: int) -> tuple[str, float]:
    n = b + c
    if n == 0:
        return "p=1.0 (no discordant pairs)", 1.0
    k = max(b, c)
    tail = sum(comb(n, i) for i in range(k, n + 1)) * 0.5 ** n
    p = min(1.0, 2 * tail)
    s = f"p={p:.6f}" if p >= 1e-6 else f"p<1e-6 (exact tail {p:.2e}, b={b}, c={c})"
    return s, p


def q(sorted_vals, qq):
    if not sorted_vals:
        return 0.0
    return sorted_vals[min(len(sorted_vals) - 1, max(0, ceil(qq * len(sorted_vals)) - 1))]


def load_block(name: str, info: dict) -> dict:
    rd = RES / info["run_id"]
    seal = json.loads((rd / "SEAL.json").read_text())
    actual = sha(rd / "raw" / "runs.jsonl")
    assert actual == seal.get("raw_runs_sha256"), f"seal mismatch {info['run_id']}"
    if "seal" in info:
        assert actual == info["seal"], f"frozen baseline SHA changed! {actual}"
    recs = [json.loads(l) for l in (rd / "raw" / "runs.jsonl").read_text().splitlines() if l.strip()]
    scored = {}
    for l in (rd / "scored" / "per_task.jsonl").read_text().splitlines():
        if l.strip():
            d = json.loads(l)
            scored[(d["task_id"], d["method"])] = d
    assert len(recs) == 600 and len(scored) == 600, f"{info['run_id']}: {len(recs)}/{len(scored)}"
    return {"run_id": info["run_id"], "raw_sha": actual, "recs": recs, "scored": scored,
            "name": name}


def stats_for(block: dict) -> dict:
    sc = block["scored"]
    types = {k[0]: v["task_type"] for k, v in sc.items()}
    out = {"run_id": block["run_id"], "sealed_raw_sha256": block["raw_sha"], "n": 300}
    for m in (KF, SA):
        rows = [v for (t, mm), v in sc.items() if mm == m]
        rs = [r for r in block["recs"] if r["method"] == m]
        # the single technical_failure record (read timeout) has no latency — excluded
        lat_all = sorted(r["latency_ms"] for r in rs if "latency_ms" in r)
        lat_llm = sorted(r["latency_ms"] for r in rs
                         if r.get("llm_calls", 0) > 0 and "latency_ms" in r)
        by_type = {}
        for tt in sorted(set(types.values())):
            sub = [v for (t, mm), v in sc.items() if mm == m and types[t] == tt]
            by_type[tt] = round(sum(bool(v["cvsr"]) for v in sub) / len(sub), 4)
        out[m] = {
            "cvsr": round(sum(bool(v["cvsr"]) for v in rows) / len(rows), 4),
            "object_f1": round(sum(v["object_f1"] for v in rows) / len(rows), 4),
            "relation_f1": round(sum(v["relation_f1"] for v in rows) / len(rows), 4),
            "binding_f1": round(sum(v["binding_f1"] for v in rows) / len(rows), 4),
            "critical_recall": round(sum(v["critical_recall"] for v in rows) / len(rows), 4),
            "fatal_rate": round(sum(1.0 if v["fatal_violations"] else 0.0 for v in rows) / len(rows), 4),
            "evidence_precision": round(sum(v["evidence_precision"] for v in rows) / len(rows), 4),
            "replay_success": round(sum(float(v["replay_success"]) for v in rows) / len(rows), 4),
            "tokens_total": sum(r["tokens"] for r in rs),
            "cost_usd_total": round(sum(r["cost"] for r in rs), 4),
            "latency_p50_s_all": round(q(lat_all, .5) / 1000, 2),
            "latency_p95_s_all": round(q(lat_all, .95) / 1000, 2),
            "llm_invoking_n": len(lat_llm),
            "latency_p50_s_llm": round(q(lat_llm, .5) / 1000, 2),
            "latency_p95_s_llm": round(q(lat_llm, .95) / 1000, 2),
            "technical_failures": sum(1 for r in rs if r.get("technical_failure")),
            "pass5_note": "single execution per task-method on External300; pass@5 not defined in this protocol",
            "by_type_cvsr": by_type,
        }
    shared = sorted({t for (t, mm) in sc if mm == KF} & {t for (t, mm) in sc if mm == SA})
    diffs = [int(bool(sc[(t, KF)]["cvsr"])) - int(bool(sc[(t, SA)]["cvsr"])) for t in shared]
    rng = random.Random(20260804)
    boots = []
    n_boot = 10_000
    for _ in range(n_boot):
        boots.append(sum(rng.choice(diffs) for _ in diffs) / len(diffs))
    boots.sort()
    b = sum(1 for d in diffs if d > 0)
    c = sum(1 for d in diffs if d < 0)
    p_str, p_f = mcnemar(b, c)
    out["paired"] = {
        "delta": round(sum(diffs) / len(diffs), 4),
        "ci95_low": round(boots[int(.025 * n_boot)], 4),
        "ci95_high": round(boots[int(.975 * n_boot) - 1], 4),
        "mcnemar_b": b, "mcnemar_c": c,
        "mcnemar_display": p_str,
    }
    # cluster bootstrap over tasks (exploratory cross-model aggregate input):
    out["_diffs_by_task"] = dict(zip(shared, diffs))
    return out


def main() -> int:
    prices = json.loads((MM / "price_snapshot.json").read_text())["models"]
    fx = json.loads((MM / "price_snapshot.json").read_text())["cny_to_usd_rate_at_capture"]
    results = {"artifact": "MULTIMODEL_CANONICAL_STATISTICS_v2", "blocks": {}}
    diff_table = {}
    for name, info in BLOCKS.items():
        blk = load_block(name, info)
        st = stats_for(blk)
        diff_table[name] = st.pop("_diffs_by_task")
        # CNY cost at this model's real price split (in/out ratio from raw usage is not
        # stored; use harness USD cost converted + report tokens)
        for m in (KF, SA):
            st[m]["cost_cny_total_harness"] = round(st[m]["cost_usd_total"] / fx, 4) if fx else None
        results["blocks"][name] = st
        print(f"[{name}] KF {st[KF]['cvsr']} vs SA {st[SA]['cvsr']} | "
              f"Δ={st['paired']['delta']} CI=[{st['paired']['ci95_low']},{st['paired']['ci95_high']}] "
              f"{st['paired']['mcnemar_display']}")

    # ---- preregistered generalization verdict over the FOUR NEW models ----
    new_names = [n for n in BLOCKS if "frozen" not in n]
    deltas = {n: results["blocks"][n]["paired"]["delta"] for n in new_names}
    ci_pos = {n: results["blocks"][n]["paired"]["ci95_low"] > 0 for n in new_names}
    all_pos = all(d > 0 for d in deltas.values())
    ge3_pos = sum(d > 0 for d in deltas.values()) >= 3
    ge3_ci = sum(ci_pos.values()) >= 3
    if all_pos and ge3_ci:
        verdict = "MODEL_GENERALIZATION_PASS"
    elif ge3_pos:
        verdict = "MODEL_GENERALIZATION_PARTIAL"
    else:
        verdict = "MODEL_GENERALIZATION_FAIL"
    results["generalization_verdict"] = {
        "rule_source": "preregistered in MULTIMODEL_PREREGISTRATION_v2.md §6",
        "per_model_delta": deltas, "per_model_ci_lower_positive": ci_pos,
        "verdict": verdict,
    }

    # ---- exploratory cross-model aggregate: cluster bootstrap by task_id ----
    tasks = sorted({t for d in diff_table.values() for t in d})
    rng = random.Random(20260804)

    def agg(sample_tasks):
        return sum(sum(diff_table[n][t] for t in sample_tasks) / len(sample_tasks)
                   for n in new_names) / len(new_names)

    boots = [agg(rng.choices(tasks, k=len(tasks))) for _ in range(2000)]
    boots.sort()
    results["cross_model_aggregate_exploratory"] = {
        "note": ("the same 300 tasks are reused across models; values are NOT 1200 "
                 "independent pairs. Cluster bootstrap by task_id, 2000 resamples, "
                 "mean of the four new models' per-task KF-SA differences."),
        "point": round(agg(tasks), 4),
        "ci95_low": round(boots[int(.025 * 2000)], 4),
        "ci95_high": round(boots[int(.975 * 2000) - 1], 4),
    }

    (MM / "MULTIMODEL_CANONICAL_STATISTICS_v2.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")

    # summary CSV: one row per model x method
    with (MM / "MULTIMODEL_SUMMARY_v2.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "method", "cvsr", "object_f1", "relation_f1", "binding_f1",
                    "critical_recall", "fatal_rate", "evidence_precision", "replay",
                    "tokens_total", "cost_usd", "lat_p50_all_s", "lat_p95_all_s",
                    "tech_failures"])
        for name, st in results["blocks"].items():
            for m in (KF, SA):
                d = st[m]
                w.writerow([name, m, d["cvsr"], d["object_f1"], d["relation_f1"],
                            d["binding_f1"], d["critical_recall"], d["fatal_rate"],
                            d["evidence_precision"], d["replay_success"],
                            d["tokens_total"], d["cost_usd_total"],
                            d["latency_p50_s_all"], d["latency_p95_s_all"],
                            d["technical_failures"]])

    print("\nVERDICT:", verdict)
    print("exploratory cluster-bootstrap aggregate:",
          results["cross_model_aggregate_exploratory"])
    print("[canonical] wrote MULTIMODEL_CANONICAL_STATISTICS_v2.json + MULTIMODEL_SUMMARY_v2.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
