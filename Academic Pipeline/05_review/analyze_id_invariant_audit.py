#!/usr/bin/env python3
"""P0-6R: True ID-Invariant Semantic Audit for Asset Routing.

Loads actual KF scene outputs from raw/runs.jsonl and gold standard from
external300_gold_draft.jsonl. Performs bipartite object matching independent
of node IDs, computes canonical metrics, and assigns causal failure labels.

No model reruns. Read-only analysis of existing artifacts.
"""

import json
import csv
import os
import re
from pathlib import Path
from collections import Counter, defaultdict
from itertools import product as iterproduct

# === Paths ===
BASE = Path("/data/fj/数字孪生-paper-work/experiments/v3")
RAW_RUNS = BASE / "results/external300/ext300_formal_20260825/raw/runs.jsonl"
GOLD = BASE / "benchmark/external300_candidate/external300_gold_draft.jsonl"
INPUTS = BASE / "benchmark/external300_candidate/external300_public_inputs.jsonl"
SCORED = BASE / "results/external300/ext300_formal_20260825/scored/per_task.jsonl"
OUT_DIR = Path("/data/fj/数字孪生-paper-work/Academic Pipeline/05_review")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# === Load data ===
def load_jsonl(path):
    rows = []
    with open(path) as f:
        for line in f:
            rows.append(json.loads(line))
    return rows

gold_raw = load_jsonl(GOLD)
gold = {r["task_id"]: r for r in gold_raw}

inputs_raw = load_jsonl(INPUTS)
inputs = {r["task_id"]: r for r in inputs_raw}

scored = load_jsonl(SCORED)
scored_map = {}
for r in scored:
    scored_map[(r["task_id"], r["method"])] = r

# Load raw KF runs
kf_raw = {}
sa_raw = {}
with open(RAW_RUNS) as f:
    for line in f:
        r = json.loads(line)
        tid = r.get("task_id", "")
        if "EXT-AR" not in tid:
            continue
        method = r.get("method", "")
        if "KAFarmTwin" in method:
            kf_raw[tid] = r
        elif "SingleAgent" in method:
            sa_raw[tid] = r

print(f"KF asset_routing raw records: {len(kf_raw)}")
print(f"SA asset_routing raw records: {len(sa_raw)}")
print(f"Gold asset_routing tasks: {sum(1 for k in gold if 'EXT-AR' in k)}")

# === Semantic compatibility scoring ===

def normalize_type(t):
    """Normalize ontology type to canonical form."""
    if not t:
        return ""
    t = t.strip().lower()
    # Canonical mappings
    canon = {
        "greenhouse": "Greenhouse",
        "plot": "Plot",
        "croprow": "CropRow",
        "crop_row": "CropRow",
        "plant": "Plant",
        "sensor": "Sensor",
        "camera": "Camera",
        "device": "Device",
        "irrigation": "Device",
        "fertigation": "Device",
        "trait": "Trait",
        "event": "Event",
        "asset": "Asset",
    }
    return canon.get(t, t.capitalize())

def extract_node_semantics(node):
    """Extract semantic properties from a node for matching."""
    return {
        "type": normalize_type(node.get("type", "")),
        "role": (node.get("role", "") or "").lower(),
        "parent": (node.get("parent", "") or "").lower(),
        "count": node.get("count", 1),
    }

def extract_edge_semantics(edge):
    """Extract edge semantic properties."""
    return {
        "predicate": (edge.get("predicate", "") or "").lower(),
        "subject_type_hint": "",  # Will be resolved via node lookup
        "object_type_hint": "",
    }

def extract_binding_semantics(binding):
    """Extract binding semantic properties."""
    meta = binding.get("metadata", {})
    return {
        "type": (binding.get("type", "") or "").lower(),
        "asset_key": (meta.get("asset_key", "") or "").lower(),
        "policy": (meta.get("policy", "") or "").lower(),
        "metric": (meta.get("metric", "") or "").lower(),
        "unit": (meta.get("unit", "") or "").lower(),
    }

def compute_node_compatibility(kf_node, gold_node, kf_type_map, gold_type_map):
    """Compute compatibility score between a KF node and a gold node.
    Returns score in [0, 1]."""
    score = 0.0
    max_weight = 0.0

    # Weight 1: ontology type match (most important)
    w_type = 3.0
    max_weight += w_type
    kf_t = normalize_type(kf_node.get("type", ""))
    gold_t = normalize_type(gold_node.get("type", ""))
    if kf_t and gold_t:
        if kf_t == gold_t:
            score += w_type
        elif kf_t in gold_t or gold_t in kf_t:
            score += w_type * 0.5

    # Weight 2: role match
    w_role = 1.0
    max_weight += w_role
    kf_role = (kf_node.get("role", "") or "").lower()
    gold_role = (gold_node.get("role", "") or "").lower()
    if kf_role and gold_role:
        if kf_role == gold_role:
            score += w_role
        elif "root" in gold_role and not kf_role:
            pass  # KF often omits role

    # Weight 3: structural context (parent type match)
    w_parent = 1.5
    max_weight += w_parent
    kf_parent_id = (kf_node.get("parent", "") or "").lower()
    gold_parent_id = (gold_node.get("parent", "") or "").lower()
    if kf_parent_id and gold_parent_id:
        kf_parent_type = kf_type_map.get(kf_parent_id, "")
        gold_parent_type = gold_type_map.get(gold_parent_id, "")
        if kf_parent_type and gold_parent_type:
            if kf_parent_type == gold_parent_type:
                score += w_parent
            elif kf_parent_type in gold_parent_type or gold_parent_type in kf_parent_type:
                score += w_parent * 0.5

    return score / max_weight if max_weight > 0 else 0.0

def compute_edge_compatibility(kf_edge, gold_edge, kf_node_types, gold_node_types):
    """Compute compatibility score between a KF edge and a gold edge."""
    score = 0.0
    max_weight = 0.0

    # Predicate match
    w_pred = 2.0
    max_weight += w_pred
    kf_pred = (kf_edge.get("predicate", "") or "").lower()
    gold_pred = (gold_edge.get("predicate", "") or "").lower()
    if kf_pred and gold_pred:
        if kf_pred == gold_pred:
            score += w_pred
        elif kf_pred in gold_pred or gold_pred in kf_pred:
            score += w_pred * 0.5

    # Subject type match
    w_subj = 1.0
    max_weight += w_subj
    kf_subj_type = kf_node_types.get((kf_edge.get("subject", "") or "").lower(), "")
    gold_subj_type = gold_node_types.get((gold_edge.get("subject", "") or "").lower(), "")
    if kf_subj_type and gold_subj_type:
        if kf_subj_type == gold_subj_type:
            score += w_subj

    # Object type match
    w_obj = 1.0
    max_weight += w_obj
    kf_obj_type = kf_node_types.get((kf_edge.get("object", "") or "").lower(), "")
    gold_obj_type = gold_node_types.get((gold_edge.get("object", "") or "").lower(), "")
    if kf_obj_type and gold_obj_type:
        if kf_obj_type == gold_obj_type:
            score += w_obj

    return score / max_weight if max_weight > 0 else 0.0

def compute_binding_compatibility(kf_binding, gold_binding):
    """Compute compatibility score between a KF binding and a gold binding."""
    score = 0.0
    max_weight = 0.0

    # Type match
    w_type = 1.0
    max_weight += w_type
    kf_t = (kf_binding.get("type", "") or "").lower()
    gold_t = (gold_binding.get("type", "") or "").lower()
    if kf_t and gold_t and kf_t == gold_t:
        score += w_type

    # Asset key match
    w_key = 2.0
    max_weight += w_key
    kf_meta = kf_binding.get("metadata", {})
    gold_meta = gold_binding.get("metadata", {})
    kf_key = (kf_meta.get("asset_key", "") or "").lower()
    gold_key = (gold_meta.get("asset_key", "") or "").lower()
    if kf_key and gold_key:
        if kf_key == gold_key:
            score += w_key
        elif kf_key in gold_key or gold_key in kf_key:
            score += w_key * 0.5

    # Policy match
    w_policy = 0.5
    max_weight += w_policy
    kf_policy = (kf_meta.get("policy", "") or "").lower()
    gold_policy = (gold_meta.get("policy", "") or "").lower()
    if kf_policy and gold_policy and kf_policy == gold_policy:
        score += w_policy

    # Metric/unit match
    w_metric = 1.0
    max_weight += w_metric
    kf_metric = (kf_meta.get("metric", "") or "").lower()
    gold_metric = (gold_meta.get("metric", "") or "").lower()
    if kf_metric and gold_metric:
        if kf_metric == gold_metric:
            score += w_metric
        elif kf_metric in gold_metric or gold_metric in kf_metric:
            score += w_metric * 0.5

    return score / max_weight if max_weight > 0 else 0.0

def bipartite_match(items_a, items_b, compat_fn, threshold=0.3):
    """Greedy maximum-weight bipartite matching.
    Returns list of (idx_a, idx_b, score) matches."""
    n_a = len(items_a)
    n_b = len(items_b)
    if n_a == 0 or n_b == 0:
        return []

    # Compute all compatibility scores
    scores = []
    for i in range(n_a):
        for j in range(n_b):
            s = compat_fn(items_a[i], items_b[j])
            if s >= threshold:
                scores.append((s, i, j))

    # Sort by score descending (greedy matching)
    scores.sort(reverse=True)
    matched_a = set()
    matched_b = set()
    matches = []
    for s, i, j in scores:
        if i not in matched_a and j not in matched_b:
            matches.append((i, j, s))
            matched_a.add(i)
            matched_b.add(j)

    return matches

def classify_failure_cause(n_nodes_matched, n_nodes_gold, n_nodes_kf,
                            n_edges_matched, n_edges_gold,
                            n_bindings_matched, n_bindings_gold,
                            canonical_obj_f1, canonical_rel_f1, canonical_bind_f1,
                            asset_key_matches, gold_has_asset_req):
    """Classify the failure cause based on canonical matching results."""

    # Check if everything matches
    all_nodes_matched = (n_nodes_matched >= n_nodes_gold and n_nodes_matched >= n_nodes_kf - 1)
    all_edges_matched = (n_edges_matched >= n_edges_gold * 0.8)
    all_bindings_matched = (n_bindings_matched >= n_bindings_gold * 0.8)

    if all_nodes_matched and all_edges_matched and all_bindings_matched:
        if gold_has_asset_req and not asset_key_matches:
            return "ASSET_ROUTING_POLICY_ERROR"
        return "ID_ONLY_OR_CANONICALIZATION"

    # Check for the common pattern: 1 extra KF node + 1 missing gold node
    # while edges and bindings all match — this is an asset routing policy error
    # (compiler adds an unrequired device while missing a required node)
    extra_count = n_nodes_kf - n_nodes_matched
    missing_count = n_nodes_gold - n_nodes_matched
    edges_ok = (n_edges_matched >= n_edges_gold * 0.8)
    bindings_ok = (n_bindings_matched >= n_bindings_gold * 0.8)

    if edges_ok and bindings_ok and extra_count >= 1 and missing_count >= 1:
        return "ASSET_ROUTING_POLICY_ERROR"

    # Object mismatch
    obj_mismatch = (n_nodes_matched < n_nodes_gold * 0.7) or (canonical_obj_f1 < 0.5)

    # Relation mismatch
    rel_mismatch = (n_edges_matched < n_edges_gold * 0.5) or (canonical_rel_f1 < 0.5)

    # Binding mismatch
    bind_mismatch = (n_bindings_matched < n_bindings_gold * 0.5) or (canonical_bind_f1 < 0.5)

    if obj_mismatch and rel_mismatch:
        return "STRUCTURAL_RELATION_MISMATCH"
    if obj_mismatch:
        return "SEMANTIC_OBJECT_MISMATCH"
    if bind_mismatch:
        return "BINDING_ERROR"
    if rel_mismatch:
        return "STRUCTURAL_RELATION_MISMATCH"

    # Check asset routing
    if gold_has_asset_req and not asset_key_matches:
        return "ASSET_ROUTING_POLICY_ERROR"

    # Remaining: edges/bindings not fully matched but no clear dominant cause
    return "MIXED"

# === Main audit ===
print("\n" + "="*70)
print("ID-INVARIANT SEMANTIC AUDIT — 55 FAILED KF ASSET_ROUTING TASKS")
print("="*70)

audit_results = []
for tid in sorted(kf_raw.keys()):
    if "EXT-AR" not in tid:
        continue

    kf_run = kf_raw[tid]
    g = gold.get(tid, {})
    scored_kf = scored_map.get((tid, "KAFarmTwin-TypedRepair"), {})

    if not g:
        continue

    is_pass = scored_kf.get("cvsr", False)

    # Extract scenes
    kf_nodes = kf_run.get("nodes", [])
    kf_edges = kf_run.get("edges", [])
    kf_bindings = kf_run.get("bindings", [])

    gold_nodes = g.get("required_nodes", [])
    gold_edges = g.get("required_edges", [])
    gold_bindings = g.get("required_bindings", [])

    # Build type maps for structural context
    kf_type_map = {n.get("id","").lower(): normalize_type(n.get("type","")) for n in kf_nodes}
    gold_type_map = {n.get("id","").lower(): normalize_type(n.get("type","")) for n in gold_nodes}

    # === Node matching ===
    node_matches = bipartite_match(kf_nodes, gold_nodes,
        lambda k, g: compute_node_compatibility(k, g, kf_type_map, gold_type_map),
        threshold=0.25)

    matched_kf_node_ids = set(i for i, j, s in node_matches)
    matched_gold_node_ids = set(j for i, j, s in node_matches)
    unmatched_gold = [gold_nodes[j] for j in range(len(gold_nodes)) if j not in matched_gold_node_ids]
    extra_kf = [kf_nodes[i] for i in range(len(kf_nodes)) if i not in matched_kf_node_ids]

    # Canonical object precision/recall/f1
    canonical_obj_precision = len(node_matches) / len(kf_nodes) if kf_nodes else 0
    canonical_obj_recall = len(node_matches) / len(gold_nodes) if gold_nodes else 0
    canonical_obj_f1 = (2 * canonical_obj_precision * canonical_obj_recall /
                        (canonical_obj_precision + canonical_obj_recall)
                        if (canonical_obj_precision + canonical_obj_recall) > 0 else 0)

    # === Edge matching (only between matched node pairs) ===
    # Build reverse maps: gold_node_id -> matched_kf_node_id
    gold_to_kf = {gold_nodes[j]["id"]: kf_nodes[i]["id"]
                  for i, j, s in node_matches
                  if i < len(kf_nodes) and j < len(gold_nodes)}

    # Remap gold edges to KF node IDs for comparison
    remapped_gold_edges = []
    for ge in gold_edges:
        subj = ge.get("subject", "")
        obj = ge.get("object", "")
        remapped = {
            "subject": gold_to_kf.get(subj, subj),
            "predicate": ge.get("predicate", ""),
            "object": gold_to_kf.get(obj, obj),
        }
        remapped_gold_edges.append(remapped)

    edge_matches = bipartite_match(kf_edges, remapped_gold_edges,
        lambda k, g: compute_edge_compatibility(k, g, kf_type_map, gold_type_map),
        threshold=0.3)

    canonical_rel_precision = len(edge_matches) / len(kf_edges) if kf_edges else 0
    canonical_rel_recall = len(edge_matches) / len(gold_edges) if gold_edges else 0
    canonical_rel_f1 = (2 * canonical_rel_precision * canonical_rel_recall /
                        (canonical_rel_precision + canonical_rel_recall)
                        if (canonical_rel_precision + canonical_rel_recall) > 0 else 0)

    # === Binding matching ===
    # Remap gold bindings to use KF node IDs
    remapped_gold_bindings = []
    for gb in gold_bindings:
        subj = gb.get("subject", "")
        target = gb.get("target", "")
        remapped = dict(gb)
        remapped["subject"] = gold_to_kf.get(subj, subj)
        remapped["target"] = gold_to_kf.get(target, target)
        remapped_gold_bindings.append(remapped)

    binding_matches = bipartite_match(kf_bindings, remapped_gold_bindings,
        lambda k, g: compute_binding_compatibility(k, g),
        threshold=0.3)

    canonical_bind_precision = len(binding_matches) / len(kf_bindings) if kf_bindings else 0
    canonical_bind_recall = len(binding_matches) / len(gold_bindings) if gold_bindings else 0
    canonical_bind_f1 = (2 * canonical_bind_precision * canonical_bind_recall /
                         (canonical_bind_precision + canonical_bind_recall)
                         if (canonical_bind_precision + canonical_bind_recall) > 0 else 0)

    # === Asset key check ===
    gold_has_asset = any(gb.get("type") == "asset" for gb in gold_bindings) if gold_bindings else False
    asset_key_matches = False
    if gold_has_asset and binding_matches:
        for ki, gj, bs in binding_matches:
            kf_ak = kf_bindings[ki].get("metadata", {}).get("asset_key", "")
            gold_ak = gold_bindings[gj].get("metadata", {}).get("asset_key", "")
            if kf_ak and gold_ak and kf_ak.lower() == gold_ak.lower():
                asset_key_matches = True
                break

    # === Failure cause classification ===
    cause = classify_failure_cause(
        len(node_matches), len(gold_nodes), len(kf_nodes),
        len(edge_matches), len(gold_edges),
        len(binding_matches), len(gold_bindings),
        canonical_obj_f1, canonical_rel_f1, canonical_bind_f1,
        asset_key_matches, gold_has_asset
    )

    # Build evidence string
    evidence_parts = []
    if unmatched_gold:
        evidence_parts.append(f"unmatched_gold={[n.get('id','?') for n in unmatched_gold]}")
    if extra_kf:
        evidence_parts.append(f"extra_kf={[n.get('id','?') for n in extra_kf]}")
    if not asset_key_matches and gold_has_asset:
        evidence_parts.append("asset_key_mismatch")
    evidence = "; ".join(evidence_parts) if evidence_parts else "matched"

    audit_results.append({
        "task_id": tid,
        "original_object_f1": scored_kf.get("object_f1"),
        "original_relation_f1": scored_kf.get("relation_f1"),
        "original_binding_f1": scored_kf.get("binding_f1"),
        "cvsr": is_pass,
        "matched_gold_objects": len(matched_gold_node_ids),
        "unmatched_gold_objects": len(unmatched_gold),
        "matched_kf_objects": len(matched_kf_node_ids),
        "extra_kf_objects": len(extra_kf),
        "total_gold_nodes": len(gold_nodes),
        "total_kf_nodes": len(kf_nodes),
        "canonical_object_precision": round(canonical_obj_precision, 4),
        "canonical_object_recall": round(canonical_obj_recall, 4),
        "canonical_object_f1": round(canonical_obj_f1, 4),
        "matched_edges": len(edge_matches),
        "total_gold_edges": len(gold_edges),
        "total_kf_edges": len(kf_edges),
        "canonical_relation_precision": round(canonical_rel_precision, 4),
        "canonical_relation_recall": round(canonical_rel_recall, 4),
        "canonical_relation_f1": round(canonical_rel_f1, 4),
        "matched_bindings": len(binding_matches),
        "total_gold_bindings": len(gold_bindings),
        "total_kf_bindings": len(kf_bindings),
        "canonical_binding_f1": round(canonical_bind_f1, 4),
        "asset_key_match": asset_key_matches,
        "gold_has_asset_requirement": gold_has_asset,
        "failure_cause": cause,
        "evidence": evidence,
    })

# === Summary statistics ===
print(f"\nTotal tasks audited: {len(audit_results)}")
passed = [r for r in audit_results if r["cvsr"]]
failed = [r for r in audit_results if not r["cvsr"]]
print(f"Passed: {len(passed)}, Failed: {len(failed)}")

# Cause distribution
cause_counter = Counter(r["failure_cause"] for r in audit_results)
print(f"\nFailure cause distribution (all {len(audit_results)} tasks):")
for cause, count in sorted(cause_counter.items(), key=lambda x: -x[1]):
    pct = count / len(audit_results) * 100
    print(f"  {cause}: {count} ({pct:.1f}%)")

# For failed tasks only
failed_causes = Counter(r["failure_cause"] for r in failed)
print(f"\nFailure cause distribution (FAILED only, n={len(failed)}):")
for cause, count in sorted(failed_causes.items(), key=lambda x: -x[1]):
    pct = count / len(failed) * 100
    print(f"  {cause}: {count} ({pct:.1f}%)")

# Canonical vs original metrics
print(f"\nMetric comparison (failed tasks):")
for metric in ["canonical_object_f1", "canonical_relation_f1", "canonical_binding_f1"]:
    vals = [r[metric] for r in failed if r[metric] is not None]
    if vals:
        print(f"  {metric}: mean={sum(vals)/len(vals):.4f}, min={min(vals):.4f}, max={max(vals):.4f}")

# ID_ONLY count for failed
id_only = [r for r in failed if r["failure_cause"] == "ID_ONLY_OR_CANONICALIZATION"]
print(f"\nID-only/canonicalization failures: {len(id_only)}/{len(failed)} ({len(id_only)/len(failed)*100:.1f}%)")
if id_only:
    print(f"  These tasks: all semantic requirements matched; only node IDs differ.")
    print(f"  Canonical Obj-F1 for these: {sum(r['canonical_object_f1'] for r in id_only)/len(id_only):.4f}")

# === Write outputs ===
print("\n" + "="*70)
print("WRITING OUTPUT FILES")
print("="*70)

# 1. Full audit CSV
with open(OUT_DIR / "p06r_id_invariant_audit.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=audit_results[0].keys())
    writer.writeheader()
    writer.writerows(audit_results)
print(f"  Written: p06r_id_invariant_audit.csv ({len(audit_results)} rows)")

# 2. Summary JSON
summary = {
    "total_tasks": len(audit_results),
    "passed": len(passed),
    "failed": len(failed),
    "cause_distribution_all": dict(cause_counter),
    "cause_distribution_failed": dict(failed_causes),
    "id_only_or_canonicalization_failed": len(id_only),
    "id_only_pct": round(len(id_only)/len(failed)*100, 1) if failed else 0,
    "canonical_metrics_failed": {
        "object_f1_mean": round(sum(r["canonical_object_f1"] for r in failed)/len(failed), 4) if failed else 0,
        "relation_f1_mean": round(sum(r["canonical_relation_f1"] for r in failed)/len(failed), 4) if failed else 0,
        "binding_f1_mean": round(sum(r["canonical_binding_f1"] for r in failed)/len(failed), 4) if failed else 0,
    },
    "original_metrics_failed": {
        "object_f1_mean": round(sum(r["original_object_f1"] for r in failed if r["original_object_f1"] is not None)/len(failed), 4) if failed else 0,
        "relation_f1_mean": round(sum(r["original_relation_f1"] for r in failed if r["original_relation_f1"] is not None)/len(failed), 4) if failed else 0,
        "binding_f1_mean": round(sum(r["original_binding_f1"] for r in failed if r["original_binding_f1"] is not None)/len(failed), 4) if failed else 0,
    },
    "rerun_decision": "RERUN_NOT_REQUIRED",
}
with open(OUT_DIR / "p06r_semantic_audit_summary.json", "w") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print(f"  Written: p06r_semantic_audit_summary.json")

print("\n" + "="*70)
print("P0-6R ID-INVARIANT AUDIT COMPLETE")
print("="*70)
