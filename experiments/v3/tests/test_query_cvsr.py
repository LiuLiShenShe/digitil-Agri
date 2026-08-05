"""Unit tests for Query-CVSR (F-010) and memory fixtures/Oracle (F-009).

Anti-cheat focused: a memory_query must NOT pass by building a scene or by
returning empty/invented data. It passes only via a correct, evidence-grounded
retrieval answer.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # experiments/v3/
sys.path.insert(0, str(ROOT / "evaluators"))
sys.path.insert(0, str(ROOT / "benchmark"))

from query_cvsr import evaluate_query_cvsr, _values_close  # noqa: E402
from memory_fixtures import (  # noqa: E402
    build_memory_task, _week_environment, oracle_environment_summary,
)


def _make_task() -> dict:
    is_ = _week_environment()
    q = {
        "target_object_ids": ["greenhouse_01"],
        "metrics": ["temperature", "humidity", "co2"],
        "start_time": "2026-07-01T00:00:00+08:00",
        "end_time": "2026-07-07T23:59:59+08:00",
        "aggregations": ["mean", "min", "max", "latest"],
        "required_units": {"temperature": "°C", "humidity": "%", "co2": "ppm"},
    }
    oracle = oracle_environment_summary(is_, q["start_time"], q["end_time"], q["metrics"])
    return {
        "task_type": "memory_query",
        "query_spec": q,
        "expected_answer": oracle,
        "expected_evidence": oracle["evidence"],
        "forbidden_side_effects": ["create_scene", "add_object", "delete_object",
                                   "modify_timeseries", "invent_record"],
    }


def _perfect_answer(task: dict) -> dict:
    import copy
    return copy.deepcopy(task["expected_answer"])


def _run(task, answer, state_delta=None):
    res = evaluate_query_cvsr(task=task, answer=answer, state_delta=state_delta)
    return res["success"], res["diagnostics"]


def test_perfect_answer_passes():
    task = _make_task()
    ok, diag = _run(task, _perfect_answer(task))
    assert ok
    assert diag["metric_recall"] == 1.0
    assert diag["evidence_precision"] == 1.0
    assert diag["aggregation_correct"] == 1.0
    assert diag["unauthorized_mutation_rate"] == 0.0


def test_empty_answer_fails_not_vacuous():
    task = _make_task()
    ok, diag = _run(task, {})
    assert not ok
    assert diag["metric_recall"] == 0.0
    # empty evidence must NOT be scored as 1.0 precision
    assert diag["evidence_precision"] == 0.0


def test_missing_metric_fails():
    task = _make_task()
    ans = _perfect_answer(task)
    del ans["normalized_values"]["co2"]  # drop one metric
    ok, diag = _run(task, ans)
    assert not ok
    assert diag["metric_recall"] < 1.0


def test_invented_metric_fails():
    task = _make_task()
    ans = _perfect_answer(task)
    ans["normalized_values"]["phantom_metric"] = {"mean": 999.0, "unit": "N/A"}
    ok, diag = _run(task, ans)
    assert not ok
    assert diag["unsupported_claim_rate"] > 0.0


def test_wrong_value_fails():
    task = _make_task()
    ans = _perfect_answer(task)
    ans["normalized_values"]["temperature"]["mean"] = 99.0  # way off
    ok, diag = _run(task, ans)
    assert not ok
    assert diag["numeric_accuracy"] == 0.0


def test_wrong_unit_fails():
    task = _make_task()
    ans = _perfect_answer(task)
    ans["normalized_values"]["temperature"]["unit"] = "°F"
    ok, diag = _run(task, ans)
    assert not ok
    assert diag["unit_accuracy"] == 0.0


def test_invented_evidence_fails():
    task = _make_task()
    ans = _perfect_answer(task)
    ans["evidence"] = {"record_ids": ["rec-NOT-REAL-1"]}
    ok, diag = _run(task, ans)
    assert not ok
    assert diag["evidence_precision"] == 0.0


def test_forbidden_mutation_fails():
    task = _make_task()
    ok, diag = _run(task, _perfect_answer(task),
                    state_delta={"mutations": ["add_object Plant p99"]})
    assert not ok
    assert diag["unauthorized_mutation_rate"] == 1.0


def test_tolerance_within_2pct():
    task = _make_task()
    ans = _perfect_answer(task)
    orig = ans["normalized_values"]["temperature"]["mean"]
    ans["normalized_values"]["temperature"]["mean"] = orig * 1.008  # 0.8% within
    ok, diag = _run(task, ans)
    assert ok
    assert diag["numeric_accuracy"] == 1.0


def test_oracle_deterministic():
    is1, is2 = _week_environment(), _week_environment()
    q = {"metrics": ["temperature", "co2"],
         "start_time": "2026-07-01T00:00:00+08:00",
         "end_time": "2026-07-07T23:59:59+08:00"}
    a1 = oracle_environment_summary(is1, q["start_time"], q["end_time"], q["metrics"])
    a2 = oracle_environment_summary(is2, q["start_time"], q["end_time"], q["metrics"])
    assert a1 == a2


def test_build_task_no_scene_gold():
    t = build_memory_task(task_id="T", prompt="q", initial_state=_week_environment(),
                          query_spec={"metrics": ["temperature"],
                                      "start_time": "2026-07-01T00:00:00+08:00",
                                      "end_time": "2026-07-07T23:59:59+08:00"})
    # memory_query must NOT demand scene construction
    assert t["required_nodes"] == []
    assert t["required_edges"] == []
    assert t["task_type"] == "memory_query"
    assert "create_scene" in t["forbidden_side_effects"]


def test_values_close():
    assert _values_close(1.0, 1.005)
    assert _values_close(100.0, 101.0)      # 1%
    assert not _values_close(100.0, 105.0)  # 5%
    assert not _values_close("a", "b")
