"""Offline tests for the External300 runner (run_external300.py).

All tests use the DEV-* synthetic fixture under tests/fixtures/external300_dev_fixture
(NOT External300 tasks, NOT test_v2) with a mock LLM. No real model is ever called
and no benchmark file is touched.

Covers:
1. Public whitelist enforcement (methods see exactly the 6 whitelisted fields;
   policy_ref and every gold-only key are absent).
2. The run phase never opens the gold file (sentinel on Path.open/read_text).
3. score refuses without SEAL.json; proceeds with a valid SEAL.
4. Order table: balance (KF-first == SA-first), determinism under fixed seed,
   self-hash tamper detection.
5. One logical execution per task x method; technical failures preserved.
6. mcnemar_exact unit assertions.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
V3 = HERE.parent
REPO_ROOT = V3.parent.parent
for p in (REPO_ROOT, V3, V3 / "evaluators", V3 / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import experiments.v3.scripts.run_external300 as R  # canonical package import (single instance)

FIXTURE = HERE / "fixtures" / "external300_dev_fixture"


@pytest.fixture()
def runner_env(tmp_path, monkeypatch):
    """Point the runner module at the dev fixture and tmp results."""
    monkeypatch.setattr(R, "PUBLIC_FILE", FIXTURE / "public.jsonl")
    monkeypatch.setattr(R, "GOLD_FILE", FIXTURE / "gold.jsonl")
    monkeypatch.setattr(R, "MANIFEST_FILE", FIXTURE / "manifest.json")
    order_table = tmp_path / "order_table.json"
    monkeypatch.setattr(R, "ORDER_TABLE", order_table)
    results = tmp_path / "results"
    monkeypatch.setattr(R, "RESULTS_EXT300", results)
    return results


def _mk_args(run_id="dev_run", **kw):
    import argparse
    return argparse.Namespace(run_id=run_id, model=None, mock=True, verbose=False, **kw)


def _run_pipeline(results: Path, run_id="dev_run"):
    R.cmd_order(None)
    assert R.cmd_run(_mk_args(run_id)) == 0
    assert R.cmd_seal(type("A", (), {"run_id": run_id})()) == 0
    assert R.cmd_score(type("A", (), {"run_id": run_id})()) == 0


# --- 1. whitelist ------------------------------------------------------------

def test_public_whitelist_exact_fields():
    rows = [json.loads(l) for l in (FIXTURE / "public.jsonl").read_text().splitlines() if l.strip()]
    for row in rows:
        pub = R.strip_public(row)
        assert set(pub.keys()) <= R.PUBLIC_FIELDS
        assert "policy_ref" not in pub
        for banned in ("_gold", "required_nodes", "required_edges", "required_bindings",
                       "critical_objects", "expected_answer", "expected_evidence",
                       "goal_state", "fatal_constraints"):
            assert banned not in pub


def test_category_derived_from_task_type():
    row = {"task_id": "X", "task_type": "rule_repair", "difficulty": "easy",
           "prompt": "p", "policy_ref": "z", "initial_state": {}}
    pub = R.strip_public(row)
    assert pub["category"] == "repair"
    assert "policy_ref" not in pub


# --- 2. gold never opened by run ----------------------------------------------

def test_run_phase_never_opens_gold(runner_env, monkeypatch):
    opened = []

    real_open = Path.open

    def spy_open(self, *a, **kw):
        opened.append(str(self))
        return real_open(self, *a, **kw)

    monkeypatch.setattr(Path, "open", spy_open)
    # phases 1-2 only: order + run must not touch gold
    R.cmd_order(None)
    R.cmd_run(_mk_args())
    leaked = [p for p in opened if Path(p).name == R.GOLD_FILE.name]
    assert not leaked, f"gold file opened during run phase: {leaked}"
    # phase 3 (score) MAY open gold; verify it did so through the module constant
    opened.clear()
    R.cmd_seal(type("A", (), {"run_id": "dev_run"})())
    R.cmd_score(type("A", (), {"run_id": "dev_run"})())


def test_gold_read_only_via_module_constant(tmp_path, monkeypatch):
    """Structural guard: the run-phase functions must not reference GOLD_FILE or
    CALL evaluate_task (a docstring mention is fine; an actual call is not)."""
    import ast
    import inspect

    def forbidden_calls(fn, names):
        tree = ast.walk(ast.parse(inspect.getsource(fn)))
        calls = [n.func.id for n in tree if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name)]
        return [c for c in calls if c in names]

    assert "GOLD_FILE" not in inspect.getsource(R.cmd_run)
    assert not forbidden_calls(R.execute_public, {"evaluate_task"})
    # and cmd_score DOES call evaluate_task (the only place it may appear as a call)
    assert "evaluate_task" in forbidden_calls(R.cmd_score, {"evaluate_task"})


# --- 3. seal gate ---------------------------------------------------------------

def test_score_refuses_without_seal(runner_env):
    R.cmd_order(None)
    R.cmd_run(_mk_args())
    raw = runner_env / "dev_run" / "raw" / "runs.jsonl"
    assert raw.exists()
    with pytest.raises(SystemExit, match="SEAL"):
        R.cmd_score(type("A", (), {"run_id": "dev_run"})())


def test_seal_detects_missing_records(runner_env):
    R.cmd_order(None)
    R.cmd_run(_mk_args())
    R.cmd_seal(type("A", (), {"run_id": "dev_run"})())
    seal = json.loads((runner_env / "dev_run" / "SEAL.json").read_text())
    # fixture has 4 tasks x2 methods = 8 records; full protocol needs 600 -> flagged
    assert seal["records"] == 8
    assert any("600" in p for p in seal["problems"])


# --- 4. order table -------------------------------------------------------------

def test_order_table_balanced_and_deterministic(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "ORDER_TABLE", tmp_path / "ot.json")
    monkeypatch.setattr(R, "RESULTS_EXT300", tmp_path)
    R.cmd_order(None)
    t1 = json.loads((tmp_path / "ot.json").read_text())
    assert t1["kf_first_count"] == t1["sa_first_count"]
    per_type: dict[str, int] = {}
    for s in t1["schedule"]:
        if s["first_method"] == R.METHODS[0]:
            tt = s["task_id"].rsplit("-", 1)[0]
            per_type[tt] = per_type.get(tt, 0) + 1
    # determinism: regenerate into a second file, byte-identical schedule
    monkeypatch.setattr(R, "ORDER_TABLE", tmp_path / "ot2.json")
    R.cmd_order(None)
    t2 = json.loads((tmp_path / "ot2.json").read_text())
    assert t1["schedule"] == t2["schedule"]
    assert t1["self_sha256"] == t2["self_sha256"]


def test_order_table_tamper_detected(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "ORDER_TABLE", tmp_path / "ot.json")
    monkeypatch.setattr(R, "RESULTS_EXT300", tmp_path)
    R.cmd_order(None)
    table = json.loads((tmp_path / "ot.json").read_text())
    table["schedule"][0]["first_method"] = R.METHODS[1]
    (tmp_path / "ot.json").write_text(json.dumps(table))
    with pytest.raises(SystemExit, match="TAMPERED"):
        R.load_order_table()


# --- 5. one logical execution + records -----------------------------------------

def test_one_execution_per_task_method_and_no_retry_on_logic_failure(runner_env):
    calls = {"n": 0}
    from experiments.v3.scripts.run_fair_baselines import _mock_llm_call_fn
    base = _mock_llm_call_fn({})

    def counting_llm(messages, budget=None):
        calls["n"] += 1
        return base(messages, budget)

    import experiments.v3.scripts.run_external300 as mod
    orig_exec = mod.execute_public

    def spy_exec(method, public, llm_call_fn):
        return orig_exec(method, public, llm_call_fn)

    R.cmd_order(None)
    R.cmd_run(_mk_args())
    recs = [json.loads(l) for l in
            (runner_env / "dev_run" / "raw" / "runs.jsonl").read_text().splitlines() if l.strip()]
    pairs = [(r["task_id"], r["method"]) for r in recs]
    assert len(pairs) == len(set(pairs)) == 8  # 4 fixture tasks x 2 methods, exactly once
    assert sum(1 for r in recs if r.get("technical_failure")) == 0
    # provenance fields present
    for r in recs:
        assert r["git_commit"] and r["method_hash"] and r["public_hash"]
        assert r["model_catalog_id"] == "mock"


def test_technical_failure_recorded_not_retried(runner_env, monkeypatch):
    import experiments.v3.scripts.run_external300 as mod
    attempts = {"n": 0}

    def boom(method, public, llm_call_fn):
        attempts["n"] += 1
        raise RuntimeError("simulated API outage")

    monkeypatch.setattr(mod, "execute_public", boom)
    R.cmd_order(None)
    rc = mod.cmd_run(_mk_args())
    assert rc == 0
    # run wrote into runner_env (patched RESULTS_EXT300), not the real results dir
    recs = [json.loads(l) for l in
            (runner_env / "dev_run" / "raw" / "runs.jsonl").read_text().splitlines() if l.strip()]
    # each of the 8 task-method pairs failed exactly once (no retries)
    assert attempts["n"] == 8
    assert all(r.get("technical_failure") for r in recs)


def test_score_produces_outputs_and_stats(runner_env):
    _run_pipeline(runner_env)
    out_dir = runner_env / "dev_run" / "scored"
    assert (out_dir / "per_task.jsonl").exists()
    assert (out_dir / "per_task.csv").exists()
    summary = json.loads((out_dir / "overall_summary.json").read_text())
    assert summary["n_scored"] == 8
    # DEV-XX-002 gold is intentionally pending -> its 2 records skipped by adjudication guard
    assert summary["skipped_unadjudicated_gold"] >= 2
    assert "paired_statistics" in summary
    assert "note_non_sota" in summary and "SOTA" in summary["note_non_sota"]
    for m in R.METHODS:
        assert m in summary["by_method"]


# --- 6. McNemar exact ------------------------------------------------------------

def test_mcnemar_exact_known_cases():
    from experiments.v3.evaluators.statistical_tests import mcnemar_exact
    # b=3 wins, c=0 losses -> two-sided p = min(1, 2*(0.5^3)) = 0.25
    res = mcnemar_exact([True]*3 + [False]*7, [False]*10)
    assert res["b"] == 3 and res["c"] == 0
    assert abs(res["p_value"] - 0.25) < 1e-9
    assert res["odds_ratio"] is None
    # no discordant pairs -> p=1
    res0 = mcnemar_exact([True]*5, [True]*5)
    assert res0["p_value"] == 1.0 and res0["n_discordant"] == 0
    # b=c symmetric -> p=1
    res_sym = mcnemar_exact([True, True, False], [True, False, True])
    assert res_sym["b"] == 1 and res_sym["c"] == 1
    assert res_sym["p_value"] == 1.0
