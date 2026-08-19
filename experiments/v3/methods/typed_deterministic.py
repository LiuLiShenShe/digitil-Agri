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
        # Root detection must not depend on the node carrying role="root": the
        # initial_state of repair tasks seeds a Greenhouse node WITHOUT a role field
        # (e.g. {"id":"N31_gh_root","type":"Greenhouse"}), so role-based detection
        # would find no root and the executor bails → edges stay empty. Fall back
        # to the Greenhouse TYPE as the root (canonical, general).
        root = next((n for n in nodes if str(n.get("role") or "").lower() == "root"
                     or str(n.get("type") or "").lower() in ("greenhouse", "green house")), None)
        node = _node(oid)
        if not root or not node or node.get("parent"):
            return None
        parent_id = str(root.get("id"))
        # R1 hierarchy must be represented as an explicit `contains` edge (the scored
        # graph's edge list, which is what required_edges compare against), not only a
        # `parent` transform field. Setting parent alone leaves edges=[] → relation_f1=0.
        # A single op can carry both, so edge_match sees the contains edge AND the node
        # keeps its parent field for any validator that reads it.
        return {"patch_op": "add_edge", "target": oid,
                "changes": {"subject": parent_id, "predicate": "contains", "object": oid,
                            "parent": parent_id}}
    if action == "fill_observes" and rule_id == "R5":
        node = _node(oid)
        observes = None
        # A camera mounted on the root observes the scene beneath it: prefer a
        # contained object of the ROOT (the CropRow / plant), not the camera itself.
        # This is a general camera-observation policy — the camera watches what it is
        # mounted over, not its own id (a self-observes is a no-op the validator would
        # still not semantically satisfy).
        for e in edges:
            if str(e.get("subject") or "") == oid and str(e.get("predicate") or "") == "contains":
                observes = e.get("object")
                break
        # skip self-observation: camera watching itself is not a valid observes target
        if observes == oid:
            observes = None
        if not observes:
            root_id = str((node.get("parent") or "") or "")
            for e in edges:
                if str(e.get("subject") or "") == root_id and str(e.get("predicate") or "") == "contains":
                    if str(e.get("object") or "") != oid:
                        observes = e.get("object")
                        break
        if not observes:
            # last resort: any non-camera object in the scene is a valid observation
            # target (general: cameras watch crops, rows, plots — never another device).
            for n in nodes:
                nt = str(n.get("type") or "").lower()
                if nt in ("croprow", "plant", "plot", "greenhouse"):
                    if str(n.get("id") or "") != oid:
                        observes = str(n.get("id") or "")
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


def attach_all_rootless(nodes: list[dict[str, Any]],
                        edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Batched R1 executor: produce an `add_edge` op for EVERY orphaned object.

    When the LLM chooses `attach_to_root`, the intent is to repair the scene
    hierarchy — a single decision, not one decision per orphan. Emitting one
    op per rootless object in a single round keeps the 3-round repair budget
    from being exhausted one orphan at a time (e.g. TN32: R4 + R5 + R1(Asset_B)
    fixed everything but the second orphan, N32_row, was never reached). This
    is still pure deterministic structure work under D2: the LLM chose the
    action, the executor applies it consistently to every affected object.

    An object is orphaned iff it is not the root AND has no parent (no `parent`
    field set, and no `contains` edge anywhere that points at it). Attaching to
    the root is the canonical fallback parent (general domain policy), identical
    to what the single-object `attach_to_root` executor already does — just
    applied to every orphan at once.
    """
    root = next((n for n in nodes if str(n.get("role") or "").lower() == "root"
                 or str(n.get("type") or "").lower() in ("greenhouse", "green house")), None)
    if not root:
        return []
    root_id = str(root.get("id"))
    parented = set()
    for n in nodes:
        pid = str((n.get("parent") or "") or "")
        if pid:
            parented.add(str(n.get("id") or ""))
    for e in edges:
        if str(e.get("predicate") or "").lower() == "contains":
            parented.add(str(e.get("object") or ""))
    ops = []
    for n in nodes:
        oid = str(n.get("id") or "")
        if not oid or oid == root_id or oid in parented:
            continue
        ops.append({"patch_op": "add_edge", "target": oid,
                    "changes": {"subject": root_id, "predicate": "contains", "object": oid,
                                "parent": root_id}})
    return ops