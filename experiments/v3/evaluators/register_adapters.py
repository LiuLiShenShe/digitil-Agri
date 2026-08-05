"""Register task_type adapters (F-010).

memory_query -> Query-CVSR (query_cvsr.py)
graph types  -> graph CVSR (wired from metrics.py's object-graph evaluation)

Call register_adapters() at import time from the evaluator package.
"""

from __future__ import annotations

from typing import Any

from task_types import register_adapter


def _memory_query_adapter(task: dict[str, Any], run_state: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    from query_cvsr import evaluate_query_cvsr
    answer = run_state.get("answer")
    state_delta = run_state.get("state_delta")
    res = evaluate_query_cvsr(task=task, answer=answer, state_delta=state_delta)
    return res["success"], res["diagnostics"]


def _graph_adapter(task: dict[str, Any], run_state: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """Graph types delegate to the object-graph evaluation in metrics.py.

    run_state must carry the graph evaluation result already computed by
    metrics.evaluate_task (nodes/edges/bindings matched, no fatal, evidence).
    """
    gr = run_state.get("graph_result") or {}
    ok = bool(gr.get("graph_cvsr"))
    diag = {k: gr.get(k) for k in
            ("object_f1", "critical_recall", "relation_f1", "binding_f1",
             "fatal_violation_rate")}
    diag["graph_cvsr"] = ok
    return ok, diag


def register_adapters() -> None:
    register_adapter("memory_query", _memory_query_adapter)
    for tt in ("scene_construction", "asset_routing", "data_binding", "rule_repair"):
        register_adapter(tt, _graph_adapter)
