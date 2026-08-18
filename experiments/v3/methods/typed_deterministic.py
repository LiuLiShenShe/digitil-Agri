"""Deterministic (no-LLM) patch operators for the KAFarmTwin typed repair loop.

D2 (P1-4): many rules have an unambiguous mechanical fix. Routing those through an
LLM round wastes budget (cost_ratio 1.75), risks a malformed patch, and is exactly
the kind of deterministic structure work the LLM should not own. For these, we
compute the patch directly from the rule + the current scene state and apply it.
The LLM is retained only for genuinely ambiguous choices (e.g. R2: which sensor
→ which crop row when several crop rows exist).

Gated by `use_deterministic_ops` (default True) so the same code is auditable and
the ablation can disable this path.
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


def build_deterministic_patch(*, rule_id: str, violation: dict[str, Any],
                              nodes: list[dict[str, Any]], edges: list[dict[str, Any]],
                              bindings: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return a concrete patch {patch_op, target, changes} if rule_id has a
    deterministic mechanical fix, else None (fall back to the LLM).
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

    if rule_id == "R4":
        # R4: replace_asset to the correct type (unambiguous mechanical fix).
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
    if rule_id == "R1":
        # R1: attach a legal parent — the root Greenhouse. If the child has no
        # parent, set it under the greenhouse (the only root object present).
        root = next((n for n in nodes if n.get("role") == "root"), None)
        node = _node(oid)
        if not root or (node and node.get("parent")):
            return None  # ambiguous / already has a parent → leave to LLM
        return {"patch_op": "update_transform", "target": oid,
                "changes": {"parent": str(root.get("id"))}}
    if rule_id == "R3":
        # R3: init an in-bounds location within parent bounds. If we can find the
        # parent's bounds, place the object inside them; else in-bounds default.
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
    if rule_id == "R5":
        # R5: camera missing pose/observes/fov → fill observes from a contained child.
        node = _node(oid)
        observes = None
        for e in edges:
            if str(e.get("subject") or "") == oid and str(e.get("predicate") or "") == "contains":
                observes = e.get("object")
                break
        if node and (node.get("observes") is not None or node.get("key_attrs", {}).get("observes")):
            return None  # partial observed already — leave to LLM to fill the rest
        return {"patch_op": "set_attr", "target": oid,
                "changes": {"pose": {"position": [0, 0, 0]},
                            "observes": observes or oid,
                            "fov": 90.0}}
    if rule_id == "R6":
        # R6: device missing served-object binding → bind to a contained crop object.
        contained = None
        # find objects this device contains, else any crop under the same parent
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
    return None  # R2 and others: genuinely ambiguous → LLM