"""State matching for repair tasks.

A repair task succeeds only if:
  - the final scene state matches the goal_state (or an allowed variant), AND
  - every critical_object was ACTUALLY modified relative to initial_state.

Merely regenerating a new scene while leaving the specified object unchanged is
a repair failure. Merely preserving initial_state unchanged is also a failure.
"""

from __future__ import annotations

from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from node_match import match_nodes, _norm  # noqa: E402


def _objects_of(state: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not state:
        return []
    return state.get("objects") or []


def _binding_of(state: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not state:
        return []
    return state.get("bindings") or []


def _traits_of(state: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return trait entries (T23 models phenotype traits in a traits[] array)."""
    if not state:
        return []
    return state.get("traits") or []


def _find(nodes: list[dict[str, Any]], oid: str) -> dict[str, Any] | None:
    for n in nodes:
        if str(n.get("id") or "") == oid:
            return n
    return None


def _get(key: str, obj: dict[str, Any]):
    """Read a semantic field from top-level or key_attrs (either representation).

    Prefers key_attrs (canonical home after layout-solve / typed-repair), so a
    repaired key_attrs.location is not shadowed by a stale top-level location.
    """
    ka = obj.get("key_attrs") or {}
    if key in ka:
        return ka.get(key)
    if key in obj:
        return obj.get(key)
    return None


def _meaningful_change(init: dict[str, Any], final: dict[str, Any]) -> bool:
    """True if the final object differs from the initial object on key semantics."""
    keys = ("monitoring_target", "belongs_to", "observes", "pose", "fov", "asset_key", "asset_policy", "location")
    diffs = 0
    for k in keys:
        if _norm(str(_get(k, init))) != _norm(str(_get(k, final))):
            diffs += 1
    # also compare via serialized equality on non-location attrs
    if _norm(str(init.get("type"))) != _norm(str(final.get("type"))):
        diffs += 1
    return diffs > 0


def repair_match(*, task: dict[str, Any], initial_state: dict[str, Any],
                 goal_state: dict[str, Any], final_state: dict[str, Any]) -> dict[str, Any]:
    """Score a repair task's final state against goal_state + critical-object modification.

    final_state: the method's produced scene state (nodes + bindings).
    Returns:
      success: bool
      goal_match: matched/required counts against goal_state nodes
      critical_unmodified: list of critical_objects that were NOT actually modified
      reasons: list[str]
    """
    goal_nodes = _objects_of(goal_state)
    final_nodes = _objects_of(final_state)
    init_nodes = _objects_of(initial_state)
    critical = task.get("critical_objects") or []

    # 1. All required goal nodes present (counts as node matching).
    node_match = match_nodes(required=goal_nodes, generated=final_nodes)
    all_goal_nodes = node_match["all_matched"]

    # 2. Critical objects actually modified. Critical objects may be scene nodes OR
    #    data-backed objects (sensor/trait represented as a binding subject, e.g. T23
    #    models trait_h_42 as a trait_bind, not a scene node). Detect either change.
    final_binds = _binding_of(final_state)

    # Map of initial trait entries by id (T23 keeps traits in initial_state.traits[])
    init_traits = _traits_of(initial_state)
    final_traits = _traits_of(final_state)

    def _init_obj(cid) -> dict | None:
        return _find(init_nodes, cid) or _find(init_traits, cid)

    def _final_obj(cid) -> dict | None:
        return _find(final_nodes, cid) or _find(final_traits, cid)

    def _trait_bound(cid) -> bool:
        # a trait is genuinely repaired if it has unit+timestamp and is bound
        return any(str(b.get("subject") or "") == cid
                   and (b.get("target") is not None) for b in final_binds)

    critical_unmodified: list[str] = []
    for cid in critical:
        init_o = _init_obj(cid)
        final_o = _final_obj(cid)
        if init_o is None:
            continue  # not present initially -> cannot be repaired-from
        if final_o is None:
            critical_unmodified.append(cid)
        elif _norm(str(cid)) in {str(b.get("subject") or "") for b in final_binds}:
            # critical object is data-backed (sensor/trait bind subject): it is
            # 'modified' once it is bound with unit/timestamp (its error was missing
            # these). Do not require a node-level field change it never had.
            if not _trait_bound(cid):
                # still count as modified if it gained unit/timestamp somewhere
                has_unit = bool(_get("unit", final_o) or final_o.get("unit")
                                or _get("timestamp", final_o) or final_o.get("timestamp"))
                if not has_unit:
                    critical_unmodified.append(cid)
        elif not _meaningful_change(init_o, final_o):
            critical_unmodified.append(cid)

    # 3. Initial error state no longer present: final must not equal initial (no-op).
    noop = _noop_repair(initial_state, final_state)

    reasons: list[str] = []
    if not all_goal_nodes:
        reasons.append(f"goal state not fully reached: {node_match['matched']}/{len(goal_nodes)} nodes")
    if critical_unmodified:
        reasons.append(f"critical objects not actually modified: {sorted(critical_unmodified)}")
    if noop:
        reasons.append("final state equals initial state (no-op repair)")

    success = all_goal_nodes and not critical_unmodified and not noop
    return {
        "success": success,
        "goal_nodes_matched": node_match["matched"],
        "goal_nodes_required": len(goal_nodes),
        "critical_unmodified": sorted(critical_unmodified),
        "noop_repair": noop,
        "reasons": reasons,
    }


def _noop_repair(initial: dict[str, Any], final: dict[str, Any]) -> bool:
    """Return True if the final state is structurally identical to the initial (no repair).

    Compares the same semantic fields `_meaningful_change` uses, on every object.
    `_meaningful_change` and `_noop_repair` must agree on what counts as "changed":
    T20's repair changes `location`; T23's repair changes a trait's unit/bound_to
    (modeled in traits[]/bindings, not the scene nodes). A repair that only changes
    a trait/binding (nodes identical) is NOT a no-op.
    """
    _CHANGE_KEYS = ("monitoring_target", "belongs_to", "observes", "pose", "fov",
                    "asset_key", "asset_policy", "location", "type")
    init_nodes = _objects_of(initial)
    final_nodes = _objects_of(final)
    if len(init_nodes) != len(final_nodes):
        return False
    for n in init_nodes:
        fn = _find(final_nodes, str(n.get("id") or ""))
        if fn is None:
            return False
        for k in _CHANGE_KEYS:
            if _norm(str(_get(k, n))) != _norm(str(_get(k, fn))):
                return False
    # if nodes are identical, check whether traits/bindings changed (T23 repair)
    if _binding_of(initial) != _binding_of(final):
        return False
    if _traits_of(initial) != _traits_of(final):
        return False
    return True
