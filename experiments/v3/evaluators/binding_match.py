"""Binding matching for the semantic evaluator.

A binding is correct when subject, target, binding type, and required metadata
match the gold. Binding to the wrong object is an error.
"""

from __future__ import annotations

from typing import Any


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def _binding_key(b: dict[str, Any]) -> tuple[str, str, str]:
    return (_norm(b.get("subject")), _norm(b.get("target")), _norm(b.get("type") or "binding"))


def match_bindings(*, required: list[dict[str, Any]], generated: list[dict[str, Any]]) -> dict[str, Any]:
    req_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for b in required or []:
        req_by_key[_binding_key(b)] = b

    matched = 0
    matched_keys: set[tuple[str, str, str]] = set()
    wrong_target: list[dict[str, Any]] = []
    missing_metadata: list[dict[str, Any]] = []

    for b in generated or []:
        key = _binding_key(b)
        if key in req_by_key and key not in matched_keys:
            # metadata check
            req_md = req_by_key[key].get("metadata") or {}
            gen_md = b.get("metadata") or {}
            meta_ok = all(_norm(str(gen_md.get(k))) == _norm(str(v)) for k, v in req_md.items() if v is not None)
            if meta_ok:
                matched += 1
                matched_keys.add(key)
            else:
                missing_metadata.append({"binding": b, "reason": "metadata_mismatch"})
            continue
        # wrong target: same subject+type but different target
        s, t, ty = key
        alt = None
        for (rs, rt, rty), rb in req_by_key.items():
            if rs == s and rty == ty and rt != t:
                alt = rb
                break
        if alt is not None:
            wrong_target.append({"binding": b, "expected_target": alt.get("target"), "reason": "wrong_target"})
        else:
            missing_metadata.append({"binding": b, "reason": "unmatched_binding"})

    return {
        "matched": matched,
        "n_required": len(req_by_key),
        "matched_keys": sorted(matched_keys),
        "wrong_target": wrong_target,
        "missing_metadata": missing_metadata,
        "all_matched": matched == len(req_by_key),
    }


def binding_precision_recall(match: dict[str, Any], *, n_generated: int) -> dict[str, float]:
    tp = match["matched"]
    n_required = match["n_required"]
    p = tp / n_generated if n_generated > 0 else 0.0
    r = tp / n_required if n_required > 0 else (1.0 if tp == 0 else 1.0)
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4)}
