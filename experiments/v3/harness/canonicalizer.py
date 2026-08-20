"""Single public deterministic canonicalizer.

Applied identically to ALL methods before scoring. It only normalizes field
names / trivial formatting; it does NOT add or fabricate relations, bindings, or
nodes on any method's behalf (that would be method-specific supplementation).
"""

from __future__ import annotations

from typing import Any


def canonicalize_node(n: dict[str, Any]) -> dict[str, Any]:
    """Normalize a node to a canonical shape: id, type, role, key_attrs, parent.

    A top-level `location` field (used by layout.solve and by initial_state scenes)
    is folded into `key_attrs.location`, since the R3/R6 spatial rules read it there.
    Semantic fields carried by the initial_state (monitoring_target, belongs_to,
    observes, pose, fov, asset_key, asset_policy, metrics, unit) are merged into
    key_attrs so that the repair_match evaluator can detect whether they were actually
    changed from the initial state.
    """
    key_attrs = dict(n.get("key_attrs") or n.get("attributes") or {})
    # top-level location → key_attrs.location
    loc = n.get("location")
    if loc is not None and "location" not in key_attrs:
        key_attrs["location"] = loc
    # semantic fields carried on the top level by initial_state / goal_state scenes
    _SEMANTIC_TOP_KEYS = (
        "monitoring_target", "belongs_to", "observes", "pose", "fov",
        "asset_key", "asset_policy", "metrics", "unit", "timestamp",
    )
    for k in _SEMANTIC_TOP_KEYS:
        if k in n and k not in key_attrs:
            key_attrs[k] = n[k]
    return {
        "id": str(n.get("id") or n.get("objectId") or n.get("name") or ""),
        "type": str(n.get("type") or n.get("assetKey") or n.get("category") or ""),
        "role": str(n.get("role") or "entity"),
        "parent": str(n.get("parent") or n.get("parentId") or ""),
        "key_attrs": key_attrs,
        "count": int(n.get("count") or 1),
    }


def canonicalize_edge(e: dict[str, Any]) -> dict[str, Any]:
    return {
        "subject": str(e.get("subject") or e.get("source") or e.get("from") or ""),
        "predicate": str(e.get("predicate") or e.get("relation") or "related_to"),
        "object": str(e.get("object") or e.get("target") or e.get("to") or ""),
    }


def canonicalize_binding(b: dict[str, Any]) -> dict[str, Any]:
    return {
        "subject": str(b.get("subject") or ""),
        "target": str(b.get("target") or ""),
        "type": str(b.get("type") or "binding"),
        "metadata": dict(b.get("metadata") or b.get("meta") or {}),
    }


def canonicalize_output(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize a method's raw output into {nodes, edges, bindings, trace}."""
    nodes_raw = raw.get("nodes") or raw.get("objects") or raw.get("required_nodes") or []
    edges_raw = raw.get("edges") or raw.get("relations") or raw.get("required_edges") or []
    bindings_raw = raw.get("bindings") or raw.get("required_bindings") or []
    trace = raw.get("trace") or {"steps": raw.get("traceSteps") or raw.get("steps") or []}

    # nodes: canonicalize each node, preserving count on the node itself (the
    # evaluator's node_match._expand_count handles count→instances for matching,
    # and expanding here would break binding/edge subject ids which reference the
    # group id, not per-instance ids).
    nodes: list[dict[str, Any]] = []
    for n in nodes_raw:
        canonical = canonicalize_node(n)
        nodes.append(canonical)

    edges = [canonicalize_edge(e) for e in edges_raw]
    bindings = [canonicalize_binding(b) for b in bindings_raw]
    result = {"nodes": nodes, "edges": edges, "bindings": bindings, "trace": trace}
    # Provenance (NOT scored): preserve conflict/repair bookkeeping so runners can
    # report conflict_count / repair_rounds truthfully. These never feed the
    # evaluator's CVSR — they are diagnostic records only.
    if "conflicts" in raw:
        result["conflicts"] = raw["conflicts"]
    if "new_conflict_count" in raw:
        result["new_conflict_count"] = raw["new_conflict_count"]
    if "repair_ticket_count" in raw:
        result["repair_ticket_count"] = raw["repair_ticket_count"]
    if "applied_patch_count" in raw:
        result["applied_patch_count"] = raw["applied_patch_count"]
    if "rollback_count" in raw:
        result["rollback_count"] = raw["rollback_count"]
    # memory_query tasks produce a structured retrieval `answer`; preserve it so
    # the runner threads it into Query-CVSR. Not a graph artifact.
    if "answer" in raw:
        result["answer"] = raw["answer"]
    return result


def merge_layout_into_nodes(nodes: list[dict[str, Any]], layout: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge solved layout locations onto nodes so the scored state reflects the real layout.

    Shared by all methods that invoke layout.solve: the layout IS real (recorded in the
    trace proxy), so it must be reflected in the scored node state or R3 falsely fires.
    """
    loc_by_id = {str(l.get("id") or ""): l.get("location") for l in layout if isinstance(l, dict)}
    merged = []
    for o in nodes:
        if not isinstance(o, dict):
            merged.append({"id": str(o), "type": str(o), "location": loc_by_id.get(str(o), {"x": 0, "z": 0})})
            continue
        oid = str(o.get("id") or "")
        if oid in loc_by_id and "location" not in o and "location" not in (o.get("key_attrs") or {}):
            o = dict(o)
            o["key_attrs"] = dict(o.get("key_attrs") or {})
            o["key_attrs"]["location"] = loc_by_id[oid]
            o["location"] = loc_by_id[oid]
        merged.append(o)
    return merged
