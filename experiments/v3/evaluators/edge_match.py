"""Edge (relation) matching for the semantic evaluator.

Relations must match on subject, predicate, object, and DIRECTION.
  - reversed direction (subject/object swapped) -> wrong
  - swapped subject/object -> wrong
  - semantic equivalence groups allow matched equivalent IDs
"""

from __future__ import annotations

from typing import Any


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def remap_ids(ref: str, id_map: dict[str, str] | None) -> str:
    """Map a generated object id to the required id it was matched to, if any.

    `id_map` is the node-matching correspondence (generated_id → required_id). When
    present, a generated relation endpoint is rewritten to its matched required id
    before literal matching, so relations can align even though methods legitimately
    invent their own ids (gold ids are never shown to them). If the id is unmapped
    (a fabricated/extra node), it is left as-is and won't match anything — no
    over-credit. Applies uniformly to every method.
    """
    n = _norm(ref)
    return id_map.get(n, n) if id_map else n


def match_edges(*, required: list[dict[str, Any]], generated: list[dict[str, Any]],
                equivalence_groups: list[str] | None = None,
                id_map: dict[str, str] | None = None) -> dict[str, Any]:
    """Return matching report for required vs generated edges.

    id_map: generated_id → required_id correspondence from node matching. When given,
    generated edge endpoints are first rewritten through it so a generated node id
    (e.g. greenhouse_1) is compared using the required id it was matched to
    (e.g. N02_strawberry_gh). Applied to ALL methods identically.
    """
    # Build a lookup: (subject, predicate, object) normalized -> edge
    req_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for e in required or []:
        key = (_norm(e.get("subject")), _norm(e.get("predicate")), _norm(e.get("object")))
        req_by_key[key] = e

    matched = 0
    matched_req_keys: set[tuple[str, str, str]] = set()
    direction_errors: list[dict[str, Any]] = []
    swapped_errors: list[dict[str, Any]] = []

    for e in generated or []:
        s = remap_ids(e.get("subject"), id_map)
        p, o = _norm(e.get("predicate")), remap_ids(e.get("object"), id_map)
        key = (s, p, o)
        if key in req_by_key and key not in matched_req_keys:
            matched += 1
            matched_req_keys.add(key)
            continue
        # Try semantic equivalence on subject/object
        alt = _equiv_substitute(s, o, p, req_by_key, equivalence_groups, matched_req_keys)
        if alt is not None:
            matched += 1
            matched_req_keys.add(alt)
            continue
        # reversed direction? (s,p,o) vs (o,p,s)
        rev = (o, p, s)
        if rev in req_by_key:
            direction_errors.append({"edge": e, "expected": req_by_key[rev], "reason": "direction_reversed"})
        # swapped subject/object with different predicate? treat as swapped error
        elif (o, p, s) in req_by_key or (s, p, o) not in req_by_key:
            swapped_errors.append({"edge": e, "reason": "subject_object_mismatch"})

    return {
        "matched": matched,
        "n_required": len(req_by_key),
        "matched_required_keys": sorted(matched_req_keys),
        "direction_errors": direction_errors,
        "swapped_errors": swapped_errors,
        "all_matched": matched == len(req_by_key),
    }


def _equiv_substitute(s: str, o: str, p: str, req_by_key: dict[tuple[str, str, str], dict[str, Any]],
                      equivalence_groups: list[str] | None, matched: set[tuple[str, str, str]]) -> tuple[str, str, str] | None:
    """Try to match using an equivalence group member for s and/or o."""
    if not equivalence_groups:
        return None
    groups: list[list[str]] = []
    for g in equivalence_groups:
        if "|" in g:
            groups.append([_norm(x) for x in g.split("|")])
    for grp in groups:
        if s in grp:
            for alt_s in grp:
                key = (alt_s, p, o)
                if key in req_by_key and key not in matched:
                    return key
        if o in grp:
            for alt_o in grp:
                key = (s, p, alt_o)
                if key in req_by_key and key not in matched:
                    return key
    return None


def edge_precision_recall(match: dict[str, Any], *, n_generated: int) -> dict[str, float]:
    tp = match["matched"]
    n_required = match["n_required"]
    p = tp / n_generated if n_generated > 0 else 0.0
    r = tp / n_required if n_required > 0 else (1.0 if tp == 0 else 1.0)
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4)}
