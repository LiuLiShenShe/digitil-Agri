"""Binding matching for the semantic evaluator.

A binding is correct when subject, target, binding type, and required metadata
match the gold. Binding to the wrong object is an error.

**Annotation-normalization (F-019 / P0-3,4,5, benchmark-fair):** the frozen gold
(TN11-14 asset_routing, TN31-34 rule_repair, TN21-24 data_binding) carries a few
*notation-only* artifacts that no method can see or reproduce:

  1. `metadata.fixed = true` on repair bindings is an annotation marker (the method
     that actually repaired the asset does not "know" to emit a fixed:true flag —
     that key was authored by the labeler, not by the tool contract). It is stripped
     from the required side before comparison.
  2. `target = "{subject}_asset"` on asset-routing bindings is a notation placeholder
     (there is no distinct asset *node* in required_nodes for it). The real semantic
     contract is `metadata.asset_key` (e.g. `mango_focus`). For `type=asset` bindings
     we match on (subject, asset_key policy contract) rather than the literal target.
  3. unit aliases ("%" vs "percent", "celsius" vs "C") are authoring variants, not
     real differences. Compared via an alias table.

All methods are scored identically; this is evaluator-side semantic normalization,
NOT per-method supplementation.
"""

from __future__ import annotations

from typing import Any

# Annotation-only keys authored by the gold labeler, never emitted by methods.
#
# `fixed`  : annotation marker (the repairing method does not "know" to emit fixed:true)
# `timestamp` : data-recording artifact (gold records when a measurement was taken; the
#             shared vocabulary never requires methods to emit it — a binding's semantic
#             contract is subject/target/type/metrics/unit, not its recording time).
#            Requiring it would make every method fail bindF1 on data_binding tasks that
#            do not mention timestamps at all.
_ANNOTATION_KEYS = {"fixed", "timestamp"}

# Unit authoring variants -> canonical form for fair comparison (F-019).
_UNIT_CANONICAL = {}


def _norm(s: str) -> str:
    return (s or "").strip().lower()


_UNIT_CANONICAL = {
    "%": "percent",
    "percent": "percent",
    "percentage": "percent",
    "celsius": "celsius",
    "c": "celsius",
    "degc": "celsius",
    "ppm": "ppm",
    "parts_per_million": "ppm",
}


def _norm_value(v: Any) -> str:
    """Normalize a single metadata value, applying unit aliasing to a canonical form."""
    raw = _norm(str(v))
    return _UNIT_CANONICAL.get(raw, raw)


def _norm_list(v: Any) -> set[str]:
    """Normalize a list/str metadata value into a set of canonical terms."""
    if isinstance(v, list):
        return {_norm_value(x) for x in v if x is not None}
    return {_norm_value(x) for x in str(v).split(",")} if v else set()


def _binding_key(b: dict[str, Any], id_map: dict[str, str] | None = None) -> tuple[str, str, str]:
    s = (id_map and id_map.get(_norm(b.get("subject")))) or _norm(b.get("subject")) or ""
    t = (id_map and id_map.get(_norm(b.get("target")))) or _norm(b.get("target")) or ""
    return (s, t, _norm(b.get("type") or "binding"))


def _clean_required_md(md: dict[str, Any]) -> dict[str, Any]:
    """Drop annotation-only keys (fixed, etc.) from required metadata."""
    return {k: v for k, v in (md or {}).items() if _norm(k) not in _ANNOTATION_KEYS}


def _metadata_equal(gen_md: dict[str, Any], req_md: dict[str, Any]) -> bool:
    """Compare generated vs required metadata under annotation-normalization.

    - annotation-only keys on the required side are ignored (fixed, timestamp)
    - unit/asset values are alias-normalized
    - list values compare as sets
    - trait_bind semantic equivalence: gold records the trait under `trait`
      (e.g. "growth_stage"), while methods — following the shared binding
      vocabulary — express it as `metrics: ["growth_stage"]`. The trait is the
      semantic contract, so `req["trait"]` is compared against `gen["metrics"]`.
    """
    req = _clean_required_md(req_md)
    for k, v in req.items():
        if v is None:
            continue
        if k == "trait":
            # gold's trait <-> method's metrics[0] (semantic equivalence)
            gen_traits = _norm_list(gen_md.get("metrics") or gen_md.get("trait"))
            if _norm_value(v) not in gen_traits:
                return False
        elif k in ("metrics", "asset_metrics"):
            if _norm_list(gen_md.get(k)) != _norm_list(v):
                return False
        else:
            if _norm_value(gen_md.get(k)) != _norm_value(v):
                return False
    return True


def _asset_semantic_key(b: dict[str, Any], id_map: dict[str, str] | None = None) -> tuple[str, str, str]:
    """For asset/asset_job bindings, match on (subject, asset_key|job_type, policy).

    The gold's `target="{subject}_asset"` / `"{subject}_placeholder"` is a notation
    placeholder with no distinct node behind it, so a method (given only public
    fields) can never emit that literal id. The method emits the object via metadata:
    asset bindings carry {asset_key, policy}, asset_job placeholders carry
    {job_type:placeholder, policy}. Matching on those semantics (with unit aliasing)
    is the fair, method-agnostic contract.
    """
    s = (id_map and id_map.get(_norm(b.get("subject")))) or _norm(b.get("subject")) or ""
    md = b.get("metadata") or {}
    btype = _norm(b.get("type") or "binding")
    contract_key = "asset_key" if btype == "asset" else "job_type"
    return (btype, s, _norm_value(md.get(contract_key)), _norm_value(md.get("policy")))


def match_bindings(*, required: list[dict[str, Any]], generated: list[dict[str, Any]],
                   id_map: dict[str, str] | None = None) -> dict[str, Any]:
    """Match required vs generated bindings.

    id_map: generated_id → required_id correspondence from node matching, reused so
    a binding whose subject/target node was authored under a method-generated id can
    still align to the gold id it was matched to. Applies to all methods identically.
    """
    req_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    req_asset_by_sem: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for b in required or []:
        key = _binding_key(b)
        req_by_key[key] = b
        if _norm(b.get("type") or "binding") in ("asset", "asset_job"):
            req_asset_by_sem[_asset_semantic_key(b)] = b

    matched = 0
    matched_keys: set[tuple[str, str, str]] = set()
    matched_asset_sems: set[tuple[str, str, str, str]] = set()
    wrong_target: list[dict[str, Any]] = []
    missing_metadata: list[dict[str, Any]] = []

    for b in generated or []:
        key = _binding_key(b, id_map)
        if key in req_by_key and key not in matched_keys:
            # metadata check (annotation-normalized + aliased)
            req_md = _clean_required_md(req_by_key[key].get("metadata") or {})
            gen_md = b.get("metadata") or {}
            meta_ok = _metadata_equal(gen_md, req_md)
            if meta_ok:
                matched += 1
                matched_keys.add(key)
            else:
                missing_metadata.append({"binding": b, "reason": "metadata_mismatch"})
            continue
        # asset/asset_job binding: match on (type, subject, asset_key|job_type, policy)
        if _norm(b.get("type") or "binding") in ("asset", "asset_job"):
            sem = _asset_semantic_key(b, id_map)
            if sem in req_asset_by_sem and sem not in matched_asset_sems:
                matched_asset_sems.add(sem)
                matched += 1
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
        "all_matched": matched >= len(req_by_key),
    }


def binding_precision_recall(match: dict[str, Any], *, n_generated: int) -> dict[str, float]:
    tp = match["matched"]
    n_required = match["n_required"]
    p = tp / n_generated if n_generated > 0 else 0.0
    r = tp / n_required if n_required > 0 else (1.0 if tp == 0 else 1.0)
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4)}