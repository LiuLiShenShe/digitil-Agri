"""Query-CVSR — memory_query success evaluation (F-010).

A memory_query run succeeds only when the agent's *retrieved answer* satisfies
all conditions; it does NOT build a scene. Query-CVSR is the binary success
flag; we also report continuous diagnostics.

Conditions (all must hold for success):
  1. target objects correct
  2. time window correct
  3. all required metrics returned
  4. no wrong / invented metrics
  5. aggregation correct
  6. values within pre-registered tolerance
  7. units correct
  8. evidence maps to real records
  9. evidence_precision == 1.0
 10. no forbidden state mutation
"""

from __future__ import annotations

from typing import Any

# Tolerance for numeric comparison (relative). Pre-registered in the spec.
NUMERIC_REL_TOL = 0.02  # 2%


def _norm_key(x: Any) -> str:
    return str(x).strip().lower().replace(" ", "").replace("_", "")


def _values_close(a: float, b: float, rel_tol: float = NUMERIC_REL_TOL) -> bool:
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if abs(b) <= 1e-12:
        return abs(a) <= 1e-9
    return abs(a - b) / max(abs(b), 1e-9) <= rel_tol


def evaluate_query_cvsr(*, task: dict[str, Any], answer: dict[str, Any] | None,
                        state_delta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Evaluate a memory_query run.

    answer: the structured answer produced by the agent
      {normalized_values: {metric: {mean,min,max,latest,unit}},
       events: [...], summary_facts: [...]}
    state_delta: records of state mutations the agent performed during the run
      (e.g. tool calls that mutate). Absence means no mutation evidence.

    Returns {success, diagnostics}.
    """
    q = task.get("query_spec") or {}
    expected_answer = task.get("expected_answer") or {}
    expected_evidence = task.get("expected_evidence") or {}
    forbidden = task.get("forbidden_side_effects") or []
    metrics = q.get("metrics") or []
    start_iso = q.get("start_time") or ""
    end_iso = q.get("end_time") or ""
    required_units = q.get("required_units") or {}

    diag: dict[str, Any] = {}
    answer = answer or {}

    # 1. target objects correct
    expected_targets = {_norm_key(t) for t in (q.get("target_object_ids") or [])}
    answer_targets = {_norm_key(t) for t in (answer.get("target_object_ids") or
                                             answer.get("targets") or [])}
    # If the agent did not report targets, we cannot confirm — but the query
    # spec is about the retrieval, so absence of a target list is not fatal
    # when values/evidence already reference the right object. We require the
    # *reported* targets, if any, to be within expected set.
    target_ok = True
    if answer_targets and expected_targets:
        target_ok = answer_targets <= expected_targets
    diag["target_accuracy"] = 1.0 if target_ok else 0.0

    # 2. time window correct
    win = answer.get("time_window") or answer.get("window")
    win_ok = True
    if win:
        a_s = _norm_key(win.get("start")) if isinstance(win, dict) else None
        a_e = _norm_key(win.get("end")) if isinstance(win, dict) else None
        if a_s and a_s != _norm_key(start_iso):
            win_ok = False
        if a_e and a_e != _norm_key(end_iso):
            win_ok = False
    # absence of reported window is not fatal (window implied by values)
    diag["time_window_accuracy"] = 1.0 if win_ok else 0.0

    # 3. all required metrics returned
    ans_norm = answer.get("normalized_values") or answer.get("metrics") or {}
    ans_metrics = {_norm_key(k) for k in ans_norm.keys()}
    req_metrics = {_norm_key(m) for m in metrics}
    metric_recall = (len(ans_metrics & req_metrics) / len(req_metrics)
                     if req_metrics else 1.0)
    metric_precision = (len(ans_metrics & req_metrics) / len(ans_metrics)
                        if ans_metrics else 0.0)
    all_metrics_returned = metric_recall >= 1.0
    diag["metric_recall"] = round(metric_recall, 4)
    diag["metric_precision"] = round(metric_precision, 4)

    # 4. no wrong / invented metrics (precision must be 1.0)
    no_invented = metric_precision >= 1.0 or (not ans_metrics and not req_metrics)
    diag["unsupported_claim_rate"] = round(1.0 - metric_precision, 4)

    # 5. aggregation correct: mean/min/max/latest must match oracle (if agent
    #    reported these keys)
    exp_norm = expected_answer.get("normalized_values") or {}
    agg_ok = True
    for m in metrics:
        mk = next((k for k in ans_norm if _norm_key(k) == _norm_key(m)), None)
        if mk is None:
            continue  # missing handled by metric_recall
        ek = next((k for k in exp_norm if _norm_key(k) == _norm_key(m)), None)
        if ek is None:
            continue
        a_v, e_v = ans_norm[mk], exp_norm[ek]
        for agg in ("mean", "min", "max", "latest"):
            if agg in e_v and agg in a_v:
                if not _values_close(a_v[agg], e_v[agg]):
                    agg_ok = False
    diag["aggregation_correct"] = 1.0 if agg_ok else 0.0

    # 6. numeric accuracy (across mean/min/max/latest)
    numeric_ok = agg_ok
    diag["numeric_accuracy"] = 1.0 if numeric_ok else 0.0

    # 7. units correct
    units_ok = True
    for m in metrics:
        mk = next((k for k in ans_norm if _norm_key(k) == _norm_key(m)), None)
        if mk is None:
            continue
        ek = next((k for k in exp_norm if _norm_key(k) == _norm_key(m)), None)
        if ek is None:
            continue
        a_u = str((ans_norm[mk] or {}).get("unit", ""))
        e_u = str((exp_norm[ek] or {}).get("unit", ""))
        ru = required_units.get(m)
        ref = e_u or str(ru or "")
        if a_u and ref and _norm_key(a_u) != _norm_key(ref):
            units_ok = False
    diag["unit_accuracy"] = 1.0 if units_ok else 0.0

    # 8. evidence maps to real records
    exp_records = {_norm_key(r) for r in (expected_evidence.get("record_ids") or [])}
    exp_events = {_norm_key(e) for e in (expected_evidence.get("event_ids") or [])}
    ans_evidence = answer.get("evidence") or answer.get("evidence_ids") or {}
    if isinstance(ans_evidence, dict):
        ans_records = {_norm_key(r) for r in (ans_evidence.get("record_ids") or [])}
        ans_events = {_norm_key(e) for e in (ans_evidence.get("event_ids") or [])}
    else:
        ans_records = {_norm_key(r) for r in ans_evidence}
        ans_events = set()
    ev_cited = ans_records | ans_events
    if ev_cited:
        ev_real = ev_cited <= (exp_records | exp_events)
        ev_recall = len(ev_cited & (exp_records | exp_events)) / len(ev_cited)
        diag["evidence_precision"] = 1.0 if ev_real else 0.0
    else:
        # no evidence cited — un-grounded answer: evidence precision 0 (not
        # vacuously 1.0, which would reward fabricating a bare answer)
        ev_real = False
        ev_recall = 0.0
        diag["evidence_precision"] = 0.0
    diag["evidence_recall"] = round(ev_recall, 4)
    evidence_ok = bool(ev_cited) and ev_real

    # 9. evidence_precision == 1.0 (explicit, even if empty)
    diag["evidence_precision_explicit"] = 1.0 if diag["evidence_precision"] == 1.0 else 0.0

    # 10. no forbidden state mutation
    state_delta = state_delta or {}
    mutations = state_delta.get("mutations") or state_delta.get("side_effects") or []
    forbidden_mutation = False
    for m in mutations:
        m_norm = _norm_key(str(m))
        if any(_norm_key(f) in m_norm or m_norm in _norm_key(f) for f in forbidden):
            forbidden_mutation = True
    diag["unauthorized_mutation_rate"] = 1.0 if forbidden_mutation else 0.0
    no_mutation = not forbidden_mutation

    # ---- binary Query-CVSR ----
    conditions = {
        "target_ok": target_ok,
        "window_ok": win_ok,
        "metrics_returned": all_metrics_returned,
        "no_invented": no_invented,
        "aggregation_ok": agg_ok,
        "numeric_ok": numeric_ok,
        "units_ok": units_ok,
        "evidence_ok": evidence_ok,
        "evidence_precision_ok": diag["evidence_precision"] == 1.0,
        "no_forbidden_mutation": no_mutation,
    }
    success = all(conditions.values())
    diag["success"] = success
    diag["conditions"] = conditions
    return {"success": success, "diagnostics": diag}
