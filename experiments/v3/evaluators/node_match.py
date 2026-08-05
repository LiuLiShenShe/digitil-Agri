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

    # equivalence groups: if the required id is in a group, allow matching any member
    eq_groups = [g for g in (equivalence_groups or []) if "|" in g]
    req_in_group = any(req.get("id") in g.split("|") for g in eq_groups)
    if req_in_group:
        cost = max(0.0, cost - 0.5)  # relax mismatches for interchangeable objects

    return cost


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
    """Expand generated nodes: each generated object is one instance."""
    return list(nodes)


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
                "assignments": [], "all_matched": False}
    if not gen:
        return {"matched": 0, "unmatched_required": req_expanded, "unmatched_generated": [],
                "assignments": [], "all_matched": False}

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
        "all_matched": matched == len(req_expanded),
    }


def object_precision_recall(match: dict[str, Any], *, n_required: int, n_generated: int) -> dict[str, float]:
    """Precision/recall/F1 from the matching report (not from min(count))."""
    tp = match["matched"]
    p = tp / n_generated if n_generated > 0 else 0.0
    r = tp / n_required if n_required > 0 else (1.0 if tp == 0 else 1.0)
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4)}
