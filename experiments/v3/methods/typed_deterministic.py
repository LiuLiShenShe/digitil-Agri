"""Deterministic (no-LLM) patch executor for the KAFarmTwin typed repair loop.

D2 (review 2026-08-18, max risk): the design must NOT become a pure rule system.
The LLM is the DECISION-MAKER; this module is the deterministic EXECUTOR only.

Flow per conflict:
  1. The detector/validator emits a RepairTicket with `candidate_actions`
     (the bounded decision space the LLM may choose from, e.g.
     R4 -> [replace_asset, create_placeholder, ask_user]).
  2. The LLM picks ONE action from candidate_actions (it may refuse / request
     more — that is real reasoning, not a rule skip).
  3. This module (executor) applies the chosen action deterministically,
     turning it into a concrete `patch_op` + `changes` given the current scene.

`candidate_actions_for(rule_id)` returns the *legal actions* for a rule, and
`apply_action(action, ...)` produces the *concrete patch* for a LLM-chosen
action — pure execution, no judgment call. There is deliberately NO function
that maps a rule directly to a patch: every repair decision passes through the
LLM's action choice (D2 invariant).

Gated by `use_deterministic_ops` (default True) so the ablation can force the LLM
to produce the whole patch itself (no executor help) for a fair comparison.
"""

from __future__ import annotations

import re as _re
from typing import Any

# Correct device asset per object type — must mirror rule_engine.R4's contract.
_ASSET_BY_TYPE = {
    "Pump": "irrigation",
    "Camera": "camera",
    "Sensor": "sensor",
    "Irrigation": "irrigation",
}


# D2 (review): per-rule candidate ACTIONS the LLM may choose. This is the
# decision space; the LLM reasons over it, the executor (below) only applies.
CANDIDATE_ACTIONS_BY_RULE: dict[str, list[str]] = {
    "R1": ["attach_to_root", "ask_user"],            # parent hierarchy
    "R2": ["add_binding", "ask_user"],                # ambiguous target → LLM decides
    "R3": ["init_location", "ask_user"],              # bounds
    "R4": ["replace_asset", "create_placeholder", "ask_user"],
    "R5": ["fill_observes", "ask_user"],             # camera pose/observes/fov
    "R6": ["served_binding", "ask_user"],            # device binding
    "R9": ["set_placeholder", "replace_asset", "ask_user"],
    "R10": ["replace_binding", "ask_user"],
}


def candidate_actions_for(rule_id: str) -> list[str]:
    """Return the bounded set of patch actions the LLM may choose for a rule.

    Always includes "ask_user" so the LLM can defer genuinely ambiguous repairs;
    the executor never fabricates context it doesn't have. If the rule has no
    enumerated actions (unknown rule), fall back to the open "ask_user" so the
    LLM is never locked out of deciding.
    """
    return list(CANDIDATE_ACTIONS_BY_RULE.get(rule_id, ["ask_user"]))


def apply_action(*, action: str, rule_id: str, violation: dict[str, Any],
                 nodes: list[dict[str, Any]], edges: list[dict[str, Any]],
                 bindings: list[dict[str, Any]]) -> dict[str, Any] | None:
    """EXECUTOR ONLY: return the concrete patch for an LLM-chosen `action` under
    a rule, or None if this action cannot be executed deterministically.

    The LLM already chose `action`; this function only translates that decision
    into structured changes. It does NOT choose between actions — that judgment
    belongs to the LLM (D2 invariant).
    """
    message = str(violation.get("message") or "")
    oids = list(violation.get("object_ids") or [])

    def _oid():
        if oids:
            return oids[0]
        m = _re.search(r"([A-Za-z0-9_#-]+)", message)
        return m.group(1) if m else None

    def _node(oid):
        for n in nodes:
            if str(n.get("id") or "") == oid:
                return n
        return None

    oid = _oid()
    if not oid:
        return None

    if action == "replace_asset" and rule_id == "R4":
        node = _node(oid)
        nt = (node.get("type") if node else "") or (
            "Pump" if "pump" in message.lower() else
            "Camera" if "camera" in message.lower() else
            "Sensor")
        correct = _ASSET_BY_TYPE.get(nt)
        if not correct:
            return None
        return {"patch_op": "replace_asset", "target": oid,
                "changes": {"target": correct}}
    if action == "create_placeholder" and rule_id in ("R4", "R9"):
        return {"patch_op": "set_placeholder", "target": oid, "changes": {}}
    if action == "init_location" and rule_id == "R3":
        node = _node(oid)
        if not node:
            return None
        parent_id = str((node.get("parent") or "") or "")
        bounds = None
        for n in nodes:
            if str(n.get("id") or "") == parent_id:
                bounds = n.get("bounds") or (n.get("key_attrs") or {}).get("bounds")
                break
        zb = None
        if bounds:
            try:
                zb = float(bounds.get("z_max", 8))
            except (TypeError, ValueError):
                zb = None
        x_ = 1.0
        z_ = min(zb, 4.0) if zb is not None else 4.0
        return {"patch_op": "update_transform", "target": oid,
                "changes": {"key_attrs": {"location": {"x": x_, "z": z_}}}}
    if action == "attach_to_root" and rule_id == "R1":
        root = next((n for n in nodes if n.get("role") == "root"), None)
        node = _node(oid)
        if not root or (node and node.get("parent")):
            return None
        return {"patch_op": "update_transform", "target": oid,
                "changes": {"parent": str(root.get("id"))}}
    if action == "fill_observes" and rule_id == "R5":
        node = _node(oid)
        observes = None
        for e in edges:
            if str(e.get("subject") or "") == oid and str(e.get("predicate") or "") == "contains":
                observes = e.get("object")
                break
        if node and (node.get("observes") is not None or node.get("key_attrs", {}).get("observes")):
            return None
        return {"patch_op": "set_attr", "target": oid,
                "changes": {"pose": {"position": [0, 0, 0]},
                            "observes": observes or oid,
                            "fov": 90.0}}
    if action == "served_binding" and rule_id == "R6":
        contained = None
        for e in edges:
            if str(e.get("subject") or "") == oid and str(e.get("predicate") or "") == "contains":
                contained = e.get("object")
                break
        if not contained:
            node = _node(oid)
            pid = str((node.get("parent") or "") or "") if node else ""
            for e in edges:
                if str(e.get("subject") or "") == pid and str(e.get("predicate") or "") == "contains":
                    contained = e.get("object")
                    break
        if not contained:
            return None
        return {"patch_op": "add_binding", "target": oid,
                "changes": {"binding": {"subject": oid, "target": contained,
                                        "type": "sensor_bind",
                                        "metadata": {"metrics": ["moisture"], "unit": "percent"}}}}
    if action == "replace_binding" and rule_id in ("R2", "R10"):
        # R2/R10 target selection is genuinely ambiguous when the violation message
        # does not name the monitored object. The executor must NOT guess (that
        # would fabricate a binding); return None so the LLM reasons over the full
        # patch instead (D2: executor never fabricates judgment).
        m_target = _re.search(r"target['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9_#-]+)", message)
        if not m_target:
            return None
        target = m_target.group(1)
        m_unit = _re.search(r"unit['\"]?\s*[:=]\s*['\"]?([a-zA-Z_]+)", message)
        unit = m_unit.group(1) if m_unit else "celsius"
        m_metric = _re.search(r"metric(?:s)?['\"]?\s*[:=]\s*['\"]?([a-zA-Z_]+)", message)
        metric = m_metric.group(1) if m_metric else "temperature"
        return {"patch_op": "add_binding", "target": oid,
                "changes": {"binding": {"subject": oid, "target": target,
                                        "type": "sensor_bind",
                                        "metadata": {"metrics": [metric], "unit": unit}}}}
    if action == "add_binding" and rule_id == "R2":
        # generic binding add (used when the LLM picked "add_binding")
        return apply_action(action="replace_binding", rule_id="R2",
                            violation=violation, nodes=nodes, edges=edges,
                            bindings=bindings)
    # "ask_user" and anything unmapped: executor cannot act deterministically
    return None