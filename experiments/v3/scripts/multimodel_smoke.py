"""Multimodel SMOKE test — 4 models x 2 DEV tasks x 2 methods = 16 method-runs max.

Gate: requires MULTIMODEL_SMOKE_APPROVED (recorded by the user 2026-08-25).
Uses ONLY the DEV fixture (tests/fixtures/external300_dev_fixture/, status
DEV_FIXTURE_NOT_A_BENCHMARK) — never External300 tasks. Results are compatibility
diagnostics only: they NEVER enter paper main results and are NOT used to tune
formal prompts. No gold evaluation here; no key ever printed or written.

Checks per model: HTTP/API compat, structured-output parsing, content /
reasoning_content / tool_calls presence, usage token fields, finish_reason,
returned model id, cache fields, latency, per-request cost (from price_snapshot).
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

V3 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(V3.parents[1]))  # repo root on sys.path

MM = V3 / "results" / "external300" / "multimodel"
FIXTURE = V3 / "tests" / "fixtures" / "external300_dev_fixture"
SMOKE_GATE = "MULTIMODEL_SMOKE_APPROVED"  # granted by user 2026-08-25 ("同意")

MODELS = [  # preregistered block order (seed 20260825)
    "Pro/moonshotai/Kimi-K2.6",
    "MiniMaxAI/MiniMax-M2.5",
    "Qwen/Qwen3.6-27B",
    "zai-org/GLM-5.2",
]
DEV_TASKS = ["DEV-XX-001", "DEV-XX-003"]  # structured output + repair path
METHODS = ["KAFarmTwin-TypedRepair", "SingleAgent-AllTools"]


def main() -> int:
    cfg = json.loads((MM / "model_matrix_config_v2.json").read_text(encoding="utf-8"))
    assert cfg["status"].startswith("PREREGISTERED"), "config v2 must be frozen first"
    print(f"[smoke] gate={SMOKE_GATE} (user approval recorded 2026-08-25)")

    from experiments.v3.harness.llm import LLMClient, make_llm_call_fn
    from experiments.v3.scripts.run_external300 import execute_public

    # load DEV public tasks (fixture only)
    publics = {}
    for line in (FIXTURE / "public.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            d = json.loads(line)
            publics[d["task_id"]] = d
    for t in DEV_TASKS:
        assert t in publics, f"missing DEV task {t}"

    prices = json.loads((MM / "price_snapshot.json").read_text(encoding="utf-8"))["models"]

    import experiments.v3.harness.llm as llmmod
    results = {"artifact": "multimodel_smoke_v2", "gate": SMOKE_GATE,
               "started_at_cst": datetime.now(timezone(timedelta(hours=8))).isoformat(),
               "dev_tasks": DEV_TASKS, "models": {}}

    for model in MODELS:
        print(f"\n=== {model} ===")
        os.environ["AGNES_MODEL"] = model
        client = LLMClient()
        client.model = model
        assert client.is_configured(), "AGNES_API_KEY missing"

        # passively capture RAW provider responses for field-level diagnostics
        captured: list[dict] = []
        orig_post = llmmod.requests.post

        def spying_post(url, **kw):
            resp = orig_post(url, **kw)
            try:
                captured.append({"status": resp.status_code, "body": resp.json()})
            except Exception:
                captured.append({"status": resp.status_code, "body": None})
            return resp
        llmmod.requests.post = spying_post

        mres = {"runs": [], "errors": []}
        try:
            for tid in DEV_TASKS:
                public = publics[tid]
                for method in METHODS:
                    t0 = time.time()
                    rec = execute_public(method, public, make_llm_call_fn(client))
                    wall = round(time.time() - t0, 1)
                    mres["runs"].append({
                        "task": tid, "method": method, "wall_s": wall,
                        "technical_failure": bool(rec.get("technical_failure")),
                        "error": rec.get("error"),
                        "llm_calls": len([c for c in rec.get("proxy_calls", []) if c.get("tool") in (None, "llm")]) or None,
                        "tokens": rec.get("budget", {}).get("tokens"),
                        "cost_usd_harness": rec.get("budget", {}).get("cost"),
                        "nodes": len(rec.get("nodes") or []),
                        "bindings": len(rec.get("bindings") or []),
                    })
                    r = mres["runs"][-1]
                    print(f"  {tid} {method:26s} wall={wall}s fail={r['technical_failure']} "
                          f"tokens={r['tokens']} nodes={r['nodes']}")
                    if r["technical_failure"]:
                        mres["errors"].append(r["error"])
        except Exception as e:  # keep other models running
            mres["errors"].append(f"{type(e).__name__}: {e}")
            print("  RUN-LEVEL ERROR:", e)
        finally:
            llmmod.requests.post = orig_post

        # field-level diagnostics over captured raw responses
        diag = {"n_requests": len(captured), "http_200": sum(1 for c in captured if c["status"] == 200),
                "http_errors": sorted({c["status"] for c in captured if c["status"] != 200}),
                "with_usage": 0, "prompt_tokens": 0, "completion_tokens": 0,
                "cached_tokens": 0, "reasoning_tokens": 0,
                "has_content": 0, "has_reasoning_content": 0, "has_tool_calls": 0,
                "finish_reasons": [], "returned_model_ids": set(),
                "parse_failures": 0}
        for c in captured:
            b = c.get("body")
            if c["status"] != 200 or not isinstance(b, dict):
                continue
            u = b.get("usage") or {}
            if u:
                diag["with_usage"] += 1
                diag["prompt_tokens"] += int(u.get("prompt_tokens") or 0)
                diag["completion_tokens"] += int(u.get("completion_tokens") or u.get("output_tokens") or 0)
                pdet = u.get("prompt_tokens_details") or {}
                diag["cached_tokens"] += int(pdet.get("cached_tokens") or 0)
                cdet = u.get("completion_tokens_details") or {}
                diag["reasoning_tokens"] += int(cdet.get("reasoning_tokens") or 0)
            msg = ((b.get("choices") or [{}])[0].get("message") or {})
            if msg.get("content"):
                diag["has_content"] += 1
            if msg.get("reasoning_content"):
                diag["has_reasoning_content"] += 1
            if msg.get("tool_calls"):
                diag["has_tool_calls"] += 1
            fr = ((b.get("choices") or [{}])[0].get("finish_reason"))
            if fr:
                diag["finish_reasons"].append(fr)
            if b.get("model"):
                diag["returned_model_ids"].add(b["model"])
        diag["returned_model_ids"] = sorted(diag["returned_model_ids"])
        diag["finish_reasons"] = sorted(set(diag["finish_reasons"]))
        p = prices.get(model, {})
        pin, pout = p.get("input", 0), p.get("output", 0)
        diag["cost_cny_smoke"] = round(
            (diag["prompt_tokens"] * pin + diag["completion_tokens"] * pout) / 1e6, 4)
        mres["diagnostics"] = diag
        results["models"][model] = mres
        print(f"  diag: req={diag['n_requests']} http200={diag['http_200']} "
              f"http_err={diag['http_errors']} usage={diag['with_usage']} "
              f"in/out/cached={diag['prompt_tokens']}/{diag['completion_tokens']}/{diag['cached_tokens']} "
              f"reasoning={diag['reasoning_tokens']} finish={diag['finish_reasons']} "
              f"model_ids={diag['returned_model_ids']} cost=¥{diag['cost_cny_smoke']}")

    results["finished_at_cst"] = datetime.now(timezone(timedelta(hours=8))).isoformat()
    out = MM / "smoke_results_v2.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    total_cost = sum(m["diagnostics"]["cost_cny_smoke"] for m in results["models"].values())
    print(f"\n[smoke] wrote {out}")
    print(f"[smoke] TOTAL smoke cost ≈ ¥{total_cost:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
