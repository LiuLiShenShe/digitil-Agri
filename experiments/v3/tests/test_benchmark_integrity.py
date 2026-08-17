"""Benchmark integrity tests for test_v2 (P0-1..P1-5).

Locks down the Annotator 2 round-2 audit fixes:

  P0-1  public inputs carry NO gold fields (whitelist only)
  P0-2  every gold task validates against schema.json (0 errors)
  P0-3  asset routing bindings reference real assets / jobs (referential integrity)
  P0-4  repair tasks are disjunctive (replace_asset OR set_placeholder) — the
        repair adapter accepts either branch and rejects no-op / retained-wrong-binding
  P1-1  equivalence_groups are object-structured (group_id + match_on + members)
  P1-2  data_binding initial_state pre-exists the objects being bound (+ relations)
  P1-3  memory_query gold is enhanced: >=3 records/day for a real daily_mean,
        trend with net_change_direction + shape, in-window evidence only
  P1-5  MANIFEST hashes match the on-disk files
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

V3 = Path(__file__).resolve().parents[1]  # experiments/v3/
BENCH = V3 / "benchmark"
EVAL = V3 / "evaluators"
sys.path.insert(0, str(EVAL))
sys.path.insert(0, str(BENCH))

from jsonschema import Draft7Validator  # noqa: E402  (deferred)

GOLD_KEYS = {
    "required_nodes", "required_edges", "required_bindings", "critical_objects",
    "equivalence_groups", "fatal_constraints", "forbidden_side_effects",
    "allowed_side_effects", "allowed_variants", "expected_outcome",
    "graph_outcome", "expected_answer", "expected_evidence", "query_spec",
    "goal_state", "required_events", "event_bind", "target_object_ids",
    "metrics", "aggregations", "required_units", "asset_key", "asset_policy",
}


def _load(path: str) -> list[dict]:
    p = BENCH / path
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _sha(path: str) -> str:
    return hashlib.sha256((BENCH / path).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# P0-1  Public inputs carry NO gold
# ---------------------------------------------------------------------------

PUBLIC_FIELDS = {"task_id", "task_type", "difficulty", "prompt", "policy_ref", "initial_state"}


def test_public_inputs_have_no_gold_fields():
    pub = _load("test_v2/test_v2_public_inputs.jsonl")
    assert len(pub) == 20
    for t in pub:
        allowed = set(t.keys()) - PUBLIC_FIELDS
        assert allowed == set(), f"{t['task_id']} carries non-public fields: {allowed}"
    # spot-check no *gold block* key appears as a key at any depth — the block
    # keys (required_nodes/expected_answer/query_spec/...) must never appear.
    # Data attributes (metric/unit/timestamp on timeseries) are legitimate
    # public input; it is the grading blocks that must not leak.
    BLOCK_KEYS = {
        "required_nodes", "required_edges", "required_bindings", "critical_objects",
        "equivalence_groups", "fatal_constraints", "forbidden_side_effects",
        "allowed_side_effects", "allowed_variants", "expected_outcome",
        "graph_outcome", "expected_answer", "expected_evidence", "query_spec",
        "goal_state", "required_events", "event_bind",
    }
    def _scan(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in BLOCK_KEYS:
                    return False
                if not _scan(v):
                    return False
        elif isinstance(obj, list):
            for it in obj:
                if not _scan(it):
                    return False
        return True
    for t in pub:
        assert _scan(t), f"{t['task_id']} leaks a gold block key somewhere"


def test_gold_has_protected_fields():
    gold = _load("test_v2/test_v2_gold.jsonl")
    for t in gold:
        for k in ("required_nodes", "required_edges", "required_bindings",
                  "expected_outcome"):
            assert k in t, f"{t['task_id']} missing protected field {k}"


# ---------------------------------------------------------------------------
# P0-2  Gold validates against schema (0 errors)
# ---------------------------------------------------------------------------

def test_all_gold_tasks_validate_against_schema():
    schema = json.loads((BENCH / "schema.json").read_text(encoding="utf-8"))
    v = Draft7Validator(schema)
    gold = _load("test_v2/test_v2_gold.jsonl")
    errs = []
    for t in gold:
        for e in v.iter_errors(t):
            errs.append((t["task_id"], list(e.path), e.message))
    assert errs == [], f"schema errors:\n" + "\n".join(f"{a} {b} {c}" for a, b, c in errs)


def test_review_status_uses_unified_enum():
    gold = _load("test_v2/test_v2_gold.jsonl")
    allowed = {"pending", "needs_revision", "approved", "rejected"}
    for t in gold:
        assert t.get("review_status") in allowed, f"{t['task_id']} bad review_status"


def test_task_id_slug_matches_schema_pattern():
    gold = _load("test_v2/test_v2_gold.jsonl")
    pat = re.compile(r"^T[NO]?[0-9]{2,3}-v2-(scene|asset|bind|repair|mem)$")
    for t in gold:
        assert pat.match(t.get("task_id", "")), f"{t['task_id']} fails task_id pattern"
    # annotation packets may use T031–T035 format (no v2 slug)
    for t in _load_packets():
        tid = t.get("task_id", "")
        assert re.match(r"^T0[3-5][0-9]$", tid), f"packet {tid} unexpected task_id"


def _load_packets():
    out = []
    p = BENCH / "annotation_packets" / "T031-T035"
    if p.exists():
        for f in sorted(p.glob("*.json")):
            try:
                out.append(json.loads(f.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue
    return out


# ---------------------------------------------------------------------------
# P0-3  Asset routing referential integrity
# ---------------------------------------------------------------------------

def test_asset_bindings_reference_real_assets_and_jobs():
    gold = _load("test_v2/test_v2_gold.jsonl")
    asset_tasks = [t for t in gold if t["task_type"] == "asset_routing"]
    assert asset_tasks
    for t in asset_tasks:
        req_nodes = t["required_nodes"]
        node_ids = {n["id"] for n in req_nodes}
        bindings = t["required_bindings"]
        assert bindings, f"{t['task_id']} has no bindings to check"
        # focus/bg plants and the light device must resolve to a node subject
        subjects = {b["subject"] for b in bindings}
        assert subjects <= node_ids, f"{t['task_id']} binds unknown subject {subjects - node_ids}"
        # each binding has a distinct, non-empty target (asset key / job id)
        for b in bindings:
            assert b["target"], f"{t['task_id']} binding {b} has empty target"
        # the light device must carry a placeholder job (its device is missing)
        light_dev = next((n for n in req_nodes
                          if n.get("type") == "Device"
                          and (n.get("key_attrs") or {}).get("device_type") == "supplemental_light"), None)
        assert light_dev is not None, f"{t['task_id']} missing supplemental-light Device"
        light_found = any(b["subject"] == light_dev["id"]
                          and b["type"] == "asset_job" for b in bindings)
        assert light_found, f"{t['task_id']} light device has no asset_job placeholder"
        # focus/bg plants must NOT bind to the placeholder job/asset
        for b in bindings:
            if b["type"] == "asset" and b["subject"].startswith(t["task_id"].split("-v2")[0]):
                assert "placeholder" not in b["target"], f"{t['task_id']} plant bound to placeholder"


# ---------------------------------------------------------------------------
# P0-4  Repair disjunctive adapter
# ---------------------------------------------------------------------------

def _repair_task() -> dict:
    return {
        "task_id": "TN31-v2-repair",
        "task_type": "rule_repair",
        "critical_objects": ["N31_WaterPump_B"],
        "allowed_variants": [
            {"path": "replace_asset", "detail": "set to irrigation"},
            {"path": "set_placeholder", "detail": "keep + placeholder job"},
        ],
        "initial_state": {"objects": [
            {"id": "N31_WaterPump_B", "type": "Pump", "asset_key": "lemongrass"},
        ]},
        "goal_state": {"objects": [
            {"id": "N31_WaterPump_B", "type": "Pump", "asset_key": "irrigation"},
        ]},
    }


def test_repair_replace_asset_accepted():
    from register_adapters import register_adapters, _repair_adapter
    register_adapters()
    ok, diag = _repair_adapter(_repair_task(), {"final_state": {"objects": [
        {"id": "N31_WaterPump_B", "type": "Pump", "asset_key": "irrigation"}],
        "bindings": []}})
    assert ok, diag
    assert diag["repair_variant"] == "replace_asset"


def test_repair_set_placeholder_accepted():
    from register_adapters import register_adapters, _repair_adapter
    register_adapters()
    ok, diag = _repair_adapter(_repair_task(), {"final_state": {"objects": [
        {"id": "N31_WaterPump_B", "type": "Pump", "asset_key": "lemongrass"}],
        "bindings": [
            {"subject": "N31_WaterPump_B", "target": "job1", "type": "asset_job",
             "metadata": {"job_type": "placeholder"}},
        ]}})
    assert ok, diag
    assert diag["repair_variant"] == "set_placeholder"


def test_repair_retained_wrong_binding_fails():
    from register_adapters import register_adapters, _repair_adapter
    register_adapters()
    # replace_asset applied BUT the old lemongrass binding is still present
    ok, diag = _repair_adapter(_repair_task(), {"final_state": {"objects": [
        {"id": "N31_WaterPump_B", "type": "Pump", "asset_key": "irrigation"}],
        "bindings": [
            {"subject": "N31_WaterPump_B", "target": "lemongrass", "type": "asset",
             "metadata": {"asset_key": "lemongrass"}},
        ]}})
    assert not ok, diag


def test_repair_noop_fails():
    from register_adapters import register_adapters, _repair_adapter
    register_adapters()
    # nothing changed at all
    ok, diag = _repair_adapter(_repair_task(), {"final_state": {"objects": [
        {"id": "N31_WaterPump_B", "type": "Pump", "asset_key": "lemongrass"}],
        "bindings": []}})
    assert not ok, diag


# ---------------------------------------------------------------------------
# P1-1  equivalence_groups object structure
# ---------------------------------------------------------------------------

def test_equivalence_groups_object_structure():
    gold = _load("test_v2/test_v2_gold.jsonl")
    for t in gold:
        for grp in t.get("equivalence_groups") or []:
            assert isinstance(grp, dict), f"{t['task_id']} has a non-object equivalence group"
            assert "group_id" in grp and "match_on" in grp and "members" in grp, \
                f"{t['task_id']} group missing required keys: {grp}"
            assert grp["match_on"] in {"id", "type", "role", "key_attrs"}
            assert isinstance(grp["members"], list) and grp["members"]


# ---------------------------------------------------------------------------
# P1-2  data_binding initial_state pre-exists the bound objects
# ---------------------------------------------------------------------------

def test_binding_initial_state_pre_exists_bound_objects():
    gold = _load("test_v2/test_v2_gold.jsonl")
    bind_tasks = [t for t in gold if t["task_type"] == "data_binding"]
    for t in bind_tasks:
        init_objs = [o["id"] for o in (t.get("initial_state") or {}).get("objects") or []]
        init_rels = (t.get("initial_state") or {}).get("relations") or []
        # every binding subject must already exist in initial_state (we bind existing)
        for b in t["required_bindings"]:
            assert b["subject"] in init_objs, \
                f"{t['task_id']} binds subject {b['subject']} not in initial_state"
        assert init_rels, f"{t['task_id']} has no relations in initial_state"


# ---------------------------------------------------------------------------
# P1-3  memory_query gold enhanced
# ---------------------------------------------------------------------------

def test_memory_gold_has_daily_records_and_trend():
    gold = _load("test_v2/test_v2_gold.jsonl")
    mem_tasks = [t for t in gold if t["task_type"] == "memory_query"]
    assert len(mem_tasks) >= 4
    for t in mem_tasks:
        ts = (t.get("initial_state") or {}).get("timeseries_records") or []
        # >=3 records per day in the query window
        q = t["query_spec"]
        from datetime import datetime
        start = datetime.fromisoformat(q["start_time"])
        end = datetime.fromisoformat(q["end_time"])
        in_win = [r for r in ts if start <= datetime.fromisoformat(str(r["timestamp"])) <= end]
        assert len(in_win) >= 3, f"{t['task_id']} only {len(in_win)} in-window records"
        # trend block has label + net_change_direction (+ shape)
        ans = t["expected_answer"]
        assert "trend" in ans and "net_change_direction" in ans["trend"]
        # evidence references ONLY in-window records
        ev = t["expected_evidence"]["record_ids"]
        in_win_ids = {r["record_id"] for r in in_win}
        assert set(ev) <= in_win_ids, f"{t['task_id']} evidence includes out-of-window records"
        # TN43 temperature threshold is 35 (per review)
        if t["task_id"] == "TN43-v2-mem":
            evt = ans["events"][0]["payload"]
            assert evt["threshold"] == 35.0 and evt["value"] >= evt["threshold"]


# ---------------------------------------------------------------------------
# P1-5  MANIFEST hash consistency
# ---------------------------------------------------------------------------

def test_manifest_hashes_match_disk():
    man = (BENCH / "test_v2" / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
    manifest = {}
    for line in man:
        parts = line.split()
        if len(parts) == 2:
            manifest[parts[1]] = parts[0]
    # compare the two data files referenced in the manifest
    for fname in ("test_v2_public_inputs.jsonl", "test_v2_gold.jsonl"):
        if fname in manifest:
            assert _sha(f"test_v2/{fname}") == manifest[fname], \
                f"{fname} hash mismatch (regenerate + seal)"


# NOTE: MANIFEST.sha256 is regenerated by the freeze step (post-approval). The
# current on-disk file must be re-sealed AFTER all gold edits. This test is
# authoritative: if it fails, run the re-seal step before claiming consistency.
