"""Register task_type adapters (F-010).

memory_query -> Query-CVSR (query_cvsr.py)
graph types  -> graph CVSR (wired from metrics.py's object-graph evaluation)
rule_repair  -> disjunctive repair adapter (replace_asset OR set_placeholder)

Call register_adapters() at import time from the evaluator package.
"""

from __future__ import annotations

from typing import Any

from task_types import register_adapter


def _norm(s: Any) -> str:
    return str(s or "").strip().lower()


def _memory_query_adapter(task: dict[str, Any], run_state: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    from query_cvsr import evaluate_query_cvsr
    answer = run_state.get("answer")
    state_delta = run_state.get("state_delta")
    res = evaluate_query_cvsr(task=task, answer=answer, state_delta=state_delta)
    return res["success"], res["diagnostics"]


def _repair_adapter(task: dict[str, Any], run_state: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """Disjunctive rule_repair success: replace_asset OR set_placeholder.

    A repair task is a *typed*-repair: given an asset(type,crop) mismatch, the
    agent must EITHER
      (A) replace_asset — correct the object's asset_key to the device asset
          (e.g. WaterPump_B.asset_key: lettuce -> irrigation), OR
      (B) set_placeholder — keep the object but attach a placeholder asset_job
          that records the pending replacement, and REMOVE the wrong binding
          (must not silently retain the mismatched lettuce binding).

    Either branch is success; a no-op (unchanged initial_state) and an unchanged
    mismatched binding are both failures. Every legal variant is declared in the
    task's `allowed_variants` so a method may not invent a third route.
    """
    diag: dict[str, Any] = {}

    # The object to repair and its correct device asset — read from the gold.
    crit = task.get("critical_objects") or []
    if not crit:
        return False, {**diag, "reason": "no critical_objects declared"}
    crit_str = _norm(crit[0])

    # device asset to repair TO: read from goal/required gold.
    goal_objs = ((task.get("goal_state") or {}).get("objects") or []) or []
    device_asset = None
    for g in goal_objs:
        if _norm(str(g.get("id") or "")) == crit_str:
            device_asset = _norm(g.get("asset_key") or
                                 (g.get("key_attrs") or {}).get("asset_key"))

    final_state = run_state.get("final_state") or {}
    nodes = final_state.get("objects") or []
    binds = final_state.get("bindings") or []

    node_by_id = {_norm(str(n.get("id") or "")): n for n in nodes}
    me = node_by_id.get(crit_str)

    # ---- Branch A (replace_asset): the object's asset_key is corrected ----
    cur_key = ""
    if me is not None:
        cur_key = _norm(me.get("asset_key") or (me.get("key_attrs") or {}).get("asset_key"))
    replaced = bool(device_asset) and cur_key == _norm(device_asset)

    # ---- Branch B (set_placeholder): a placeholder asset_job attached to crit ----
    placeholder = any(
        _norm(b.get("subject")) == crit_str
        and _norm(b.get("type")) == "asset_job"
        and _norm((b.get("metadata") or {}).get("job_type")) == "placeholder"
        for b in binds
    )

    # ---- Wrong binding must NOT be retained on either branch ----
    # A retained asset binding whose asset_key is neither the corrected device
    # asset nor empty means the conflicting (wrong, crop-tied) binding survived.
    wrong_binding_kept = any(
        _norm(b.get("subject")) == crit_str
        and _norm(b.get("type")) == "asset"
        and _norm((b.get("metadata") or {}).get("asset_key")) not in (_norm(device_asset), "")
        for b in binds
    )
    # object disappearing entirely is also a failure (not preserved+modified)
    if me is None:
        wrong_binding_kept = True

    # No-op detection: final == initial.
    from state_match import _noop_repair
    init = task.get("initial_state") or {}
    noop = _noop_repair(init, final_state)

    both = replaced or placeholder
    success = both and not wrong_binding_kept and not noop and device_asset is not None

    diag.update({
        "repair_variant": "replace_asset" if replaced else ("set_placeholder" if placeholder else "none"),
        "critical_object": crit_str,
        "device_asset": device_asset,
        "noop_repair": noop,
        "wrong_binding_kept": wrong_binding_kept,
        "success": success,
    })
    return success, diag


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
    for tt in ("scene_construction", "asset_routing", "data_binding"):
        register_adapter(tt, _graph_adapter)
    register_adapter("rule_repair", _repair_adapter)