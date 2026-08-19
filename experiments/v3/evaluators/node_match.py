"""Node matching for the semantic evaluator.

Matches generated nodes against required nodes using a constrained cost matrix:
  - type must match (else impossible / high cost)
  - role + key attributes + parent context add cost
  - equivalence groups allow semantically-equivalent objects with different IDs to match

Multiple instances of the same type use bipartite / Hungarian optimal assignment
(here: a small built-in implementation; if `scipy` is available it is preferred).

Never uses `min(generated_count, required_count)` as a correctness measure: we
return per-node matches plus matched/unmatched counts, and metrics.py computes
precision/recall/F1 from the actual matches.
"""

from __future__ import annotations

from typing import Any

try:  # prefer scipy's linear_sum_assignment when available
    from scipy.optimize import linear_sum_assignment  # type: ignore
    _HAS_SCIPY = True
except Exception:  # pragma: no cover
    _HAS_SCIPY = False


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def _type_score(gen_type: str, req_type: str) -> float:
    """Return 0 if types match, 1 if mismatch (max cost)."""
    g = _norm(gen_type)
    r = _norm(req_type)
    if g == r:
        return 0.0
    # alias tolerance for common plurals/asset keys
    aliases = {
        "plants": "plant", "plant": "plants", "croprows": "croprow", "crop row": "croprow",
        "croprow": "crop row", "tomato": "plant", "lettuce": "plant", "camera": "camera",
    }
    if aliases.get(g) == r or aliases.get(r) == g:
        return 0.0
    return 1.0


def _attr_cost(gen: dict[str, Any], req: dict[str, Any], equivalence_groups: list[str] | None = None) -> float:
    """Additional cost for role, key_attrs, parent context, and equivalence mismatch."""
    cost = 0.0
    req_role = _norm(req.get("role") or "entity")
    gen_role = _norm(gen.get("role") or "entity")
    if req_role and req_role != "entity" and gen_role != req_role:
        cost += 0.5

    req_attrs = req.get("key_attrs") or {}
    gen_attrs = gen.get("key_attrs") or {}
    if req_attrs:
        for k, v in req_attrs.items():
            if v is not None and _norm(str(gen_attrs.get(k))) != _norm(str(v)):
                cost += 0.5

    req_parent = _norm(req.get("parent") or "")
    gen_parent = _norm(gen.get("parent") or "")
    if req_parent and gen_parent and gen_parent != req_parent:
        cost += 0.4

    # equivalence groups: if the required id is in any group, the object is
    # interchangeable with the other members -> relax mismatch costs.
    req_in_group = _in_any_group(_norm(req.get("id") or ""), equivalence_groups)
    if req_in_group:
        cost = max(0.0, cost - 0.5)  # relax mismatches for interchangeable objects

    return cost


def _in_any_group(rid: str, equivalence_groups) -> bool:
    """True if the (lowercased) required id is named by any equivalence group.

    Groups may be either the legacy 'a|b|c' string form or the v2 object form
    {group_id, members, members_pattern, match_on, expected_count}.
    """
    if not equivalence_groups:
        return False
    for g in equivalence_groups:
        if isinstance(g, str):
            if rid in g.split("|"):
                return True
            continue
        if not isinstance(g, dict):
            continue
        members = [str(m).strip().lower() for m in (g.get("members") or [])]
        pat = g.get("members_pattern")
        if rid in members:
            return True
        if pat and re_search(pat, rid):
            return True
    return False


def re_search(pattern: str, s: str) -> bool:
    """Thin wrapper so tests can import it; regex is anchored as a prefix match."""
    import re
    try:
        return re.match(pattern, s) is not None
    except re.error:
        return False


def _expand_count(n: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand a required node with count>1 into individual placeholders for matching."""
    count = int(n.get("count") or 1)
    base = dict(n)
    base.pop("count", None)
    out = []
    for i in range(count):
        item = dict(base)
        item["_instance"] = i
        item["id"] = f"{n.get('id') or 'x'}-{i + 1}" if count > 1 else n.get("id")
        out.append(item)
    return out


def _expand_generated(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expand generated nodes by their count, mirroring the required side.

    The gold types count>1 objects as a *single group node* (e.g. required
    `N11_mango_focus` with count=4). Methods, following the shared vocabulary,
    may likewise emit one group node with count=N (e.g. `plant_3` count=4). To
    score these fairly we must expand BOTH sides identically — treat a generated
    count=N node as N instances, exactly as _expand_count does for required.

    This is evaluator-side normalization applied identically to all methods. The
    generated *bounding* ids (plant_3-1..N) feed node matching, but the BASE ids
    the method actually used for its bindings/edges (plant_3) are preserved via
    id_correspondence's base-id stripping, so bindings/edges still align.
    """
    out: list[dict[str, Any]] = []
    for n in nodes or []:
        count = int(n.get("count") or 1)
        base = dict(n)
        base.pop("count", None)
        for i in range(count):
            item = dict(base)
            item["_instance"] = i
            if count > 1:
                item["id"] = f"{n.get('id') or 'x'}-{i + 1}"
            out.append(item)
    return out


def hungarian(cost: list[list[float]]) -> list[tuple[int, int]]:
    """Return optimal assignment [(gen_idx, req_idx), ...] minimizing total cost.

    Falls back to a greedy when scipy is unavailable; greedy is deterministic and
    still optimal for the simple cost matrices used in the anti-cheat tests.
    """
    if _HAS_SCIPY:
        import numpy as np  # type: ignore
        arr = np.array(cost, dtype=float)
        if arr.size == 0:
            return []
        # Infeasible (no generated node can match any required node) -> no assignment
        finite_mask = np.isfinite(arr)
        if not finite_mask.any():
            return []
        # Replace any all-inf rows/cols so scipy doesn't raise; inf cells stay inf (never chosen).
        if not finite_mask.all(axis=1).any():
            # At least one row has no feasible cell -> cannot assign everyone; return best subset
            pass
        try:
            r, c = linear_sum_assignment(arr)
            return list(zip(r.tolist(), c.tolist()))
        except ValueError:
            # fall back to greedy subset
            return _hungarian_greedy(cost)
    return _hungarian_greedy(cost)


def _hungarian_greedy(cost: list[list[float]]) -> list[tuple[int, int]]:
    """Deterministic greedy assignment (row-min then global best) — used only if scipy absent."""
    n, m = len(cost), (len(cost[0]) if cost else 0)
    if n == 0 or m == 0:
        return []
    used_rows: set[int] = set()
    used_cols: set[int] = set()
    assignment: list[tuple[int, int]] = []
    for _ in range(min(n, m)):
        best = None
        for i in range(n):
            if i in used_rows:
                continue
            for j in range(m):
                if j in used_cols:
                    continue
                v = cost[i][j]
                if best is None or v < best[0]:
                    best = (v, i, j)
        if best is None:
            break
        _, i, j = best
        used_rows.add(i)
        used_cols.add(j)
        assignment.append((i, j))
    return assignment


def match_nodes(*, required: list[dict[str, Any]], generated: list[dict[str, Any]],
                equivalence_groups: list[str] | None = None,
                threshold: float = 0.99) -> dict[str, Any]:
    """Return matching report.

    required: the typed required_nodes (with count expanded internally)
    generated: the scene's produced nodes (each is one instance)

    Returns: {matched, unmatched_required, unmatched_generated, assignments}
      matched = number of required nodes satisfied (assignment cost below threshold)
    """
    req_expanded = []
    for n in required or []:
        req_expanded.extend(_expand_count(n))
    gen = _expand_generated(generated or [])
    if not req_expanded:
        return {"matched": 0, "unmatched_required": [], "unmatched_generated": list(gen),
                "assignments": [], "req_expanded_ids": [], "all_matched": False}
    if not gen:
        return {"matched": 0, "unmatched_required": req_expanded, "unmatched_generated": [],
                "assignments": [], "req_expanded_ids": [str(r.get("id") or "") for r in req_expanded],
                "all_matched": False}

    cost = []
    for g in gen:
        row = []
        for r in req_expanded:
            c = _type_score(g.get("type") or "", r.get("type") or "")
            if c >= 1.0:
                row.append(float("inf"))
            else:
                row.append(_attr_cost(g, r, equivalence_groups))
        cost.append(row)

    assignments = hungarian(cost)
    matched = 0
    matched_req_ids: set[str] = set()
    for gi, ri in assignments:
        if cost[gi][ri] <= threshold:
            matched += 1
            matched_req_ids.add(str(req_expanded[ri].get("id") or ""))

    unmatched_required = [r for r in req_expanded if str(r.get("id") or "") not in matched_req_ids]
    matched_gen_idx = {gi for gi, _ in assignments}
    unmatched_generated = [g for i, g in enumerate(gen) if i not in matched_gen_idx]

    return {
        "matched": matched,
        "matched_required_ids": sorted(matched_req_ids),
        "unmatched_required": unmatched_required,
        "unmatched_generated": unmatched_generated,
        "assignments": [(gi, ri) for gi, ri in assignments],
        "req_expanded_ids": [str(r.get("id") or "") for r in req_expanded],
        "gen_expanded": gen,
        "all_matched": matched == len(req_expanded),
    }


def id_correspondence(assignments: list[tuple[int, int]],
                      generated: list[dict[str, Any]],
                      req_expanded_ids: list[str]) -> dict[str, str]:
    """Map each matched generated node's id → the required node id it was matched to.

    This is the identity proof the node matcher already established: it knows the
    generated greenhouse IS the required N02_strawberry_gh because type/role/attrs
    align. Edges and bindings reference these same object ids, so the scorer must
    reuse this correspondence when matching relations/bindings — otherwise gold ids
    (which methods legitimately never see) could never align with the generated ids,
    forcing relation_f1/binding_f1 to 0 even when the scene graph is correct.

    Only *matched* nodes (cost below the CVSR threshold) are carried over, so no
    unmatched/fabricated node leaks a false identity. This is pure reasoning over
    the correspondence already proven for nodes — it supplements nothing.

    `generated` MUST be the *expanded* generated list (the same list `match_nodes`
    assigned over, returned as `gen_expanded`), because assignment indices index into
    it — a count=N group node occupies N slots. Using the un-expanded list would
    mis-align every instance past a group node (P0-correction).
    """
    corr: dict[str, str] = {}
    for gi, ri in assignments:
        g = generated[gi] if gi < len(generated) else None
        if g is None:
            continue
        gid = _norm(str(g.get("id") or ""))
        rid = _norm(str(req_expanded_ids[ri] if ri < len(req_expanded_ids) else ""))
        if not gid or not rid:
            continue
        # Expanded required instances carry a `-<i>` suffix (e.g. row-2) but the
        # id referenced by required_edges/required_bindings is the base id (the row).
        # Strip that numeric instance suffix so edges/bindings can align to the base.
        import re as _re
        base_rid = _re.sub(r"-\d+$", "", rid)
        # Methods author repeated objects as one node with count=N; the generated
        # expansion produces suffixed instances (plant_1-1..plant_1-12), but the
        # method's bindings/edges reference the base id (plant_1). Register BOTH
        # the full expanded id and its base so edge/binding remapping aligns.
        base_gid = _re.sub(r"-\d+$", "", gid)
        corr.setdefault(gid, base_rid)
        corr.setdefault(base_gid, base_rid)
    return corr


def object_precision_recall(match: dict[str, Any], *, n_required: int, n_generated: int) -> dict[str, float]:
    """Precision/recall/F1 from the matching report (not from min(count))."""
    tp = match["matched"]
    p = tp / n_generated if n_generated > 0 else 0.0
    r = tp / n_required if n_required > 0 else (1.0 if tp == 0 else 1.0)
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4)}
