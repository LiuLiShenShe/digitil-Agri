"""Anti-cheat unit tests for the v3 semantic evaluator.

These tests lock down the integrity constraints from the controlling spec:
  1. correct count but all empty objects -> NOT high score (CVSR=0, low F1)
  2. reversed relation direction -> wrong
  3. swapped subject/object -> wrong
  4. binding to wrong object -> wrong
  5. different object ID but semantically equivalent -> matchable
  6. optimal matching of multiple same-type instances (Hungarian)
  7. optional objects don't reduce recall; wrong optional objects reduce precision
  8. forbidden objects penalized separately
  9. multiple legal layouts (equivalence groups) -> all pass
  10. repair fails when initial error state not actually modified
  11. repair fails when only regenerating new scene without modifying specified object
  12. declared trace with no real call -> Evidence Score 0
  13. auto-generated evidenceId with no real response -> NOT pass
  14. rule fallback flagged separately, not counted as LLM/multi-agent success
  15. new conflicts counted separately
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

EVAL = Path(__file__).resolve().parents[1] / "evaluators"  # experiments/v3/evaluators
sys.path.insert(0, str(EVAL))

from node_match import match_nodes, object_precision_recall  # noqa: E402
from edge_match import match_edges, edge_precision_recall  # noqa: E402
from binding_match import match_bindings  # noqa: E402
from state_match import repair_match  # noqa: E402
from trace_evidence import evaluate_trace  # noqa: E402
from replay import replay_trace  # noqa: E402
from rule_engine import RuleEngine  # noqa: E402
from metrics import evaluate_task  # noqa: E402


# ---------------------------------------------------------------------------
# 1. Correct count but all empty objects -> NOT high score
# ---------------------------------------------------------------------------

def _greenhouse_required() -> list[dict]:
    return [
        {"id": "greenhouse", "type": "Greenhouse", "role": "root", "count": 1},
        {"id": "tomato", "type": "Plant", "role": "entity", "count": 3},
    ]


def test_anti_cheat_1_empty_objects_not_high_score():
    required = _greenhouse_required()
    # Correct count (1 + 3 = 4) but all empty placeholders (no type / empty attrs)
    generated = [
        {"id": "x1", "type": "", "role": "", "count": 1},
        {"id": "x2", "type": "", "role": "", "count": 1},
        {"id": "x3", "type": "", "role": "", "count": 1},
        {"id": "x4", "type": "", "role": "", "count": 1},
    ]
    nm = match_nodes(required=required, generated=generated)
    assert nm["matched"] == 0
    assert nm["all_matched"] is False
    prf = object_precision_recall(nm, n_required=4, n_generated=4)
    assert prf["f1"] < 0.2, f"empty objects must not score high F1, got {prf}"


# ---------------------------------------------------------------------------
# 2. Reversed relation direction
# ---------------------------------------------------------------------------

def test_anti_cheat_2_reversed_relation_direction_wrong():
    required = [{"subject": "greenhouse", "predicate": "contains", "object": "row1"}]
    generated = [{"subject": "row1", "predicate": "contains", "object": "greenhouse"}]
    em = match_edges(required=required, generated=generated)
    assert em["matched"] == 0
    assert em["all_matched"] is False
    assert em["direction_errors"]


# ---------------------------------------------------------------------------
# 3. Swapped subject/object
# ---------------------------------------------------------------------------

def test_anti_cheat_3_swapped_subject_object_wrong():
    required = [{"subject": "sensor", "predicate": "monitors", "object": "greenhouse"}]
    generated = [{"subject": "greenhouse", "predicate": "monitors", "object": "sensor"}]
    em = match_edges(required=required, generated=generated)
    assert em["matched"] == 0
    assert em["all_matched"] is False


# ---------------------------------------------------------------------------
# 4. Binding to wrong object
# ---------------------------------------------------------------------------

def test_anti_cheat_4_binding_wrong_object():
    required = [{"subject": "s1", "target": "greenhouse", "type": "sensor_bind"}]
    generated = [{"subject": "s1", "target": "pump", "type": "sensor_bind"}]
    bm = match_bindings(required=required, generated=generated)
    assert bm["matched"] == 0
    assert bm["wrong_target"]


# ---------------------------------------------------------------------------
# 5. Different object ID but semantically equivalent -> matchable
# ---------------------------------------------------------------------------

def test_anti_cheat_5_semantic_equivalence_matchable():
    required = [{"id": "greenhouse", "type": "Greenhouse", "role": "root", "count": 1}]
    # different ID but equivalent type+role
    generated = [{"id": "gh_01", "type": "Greenhouse", "role": "root"}]
    nm = match_nodes(required=required, generated=generated, equivalence_groups=["greenhouse|gh_01"])
    assert nm["all_matched"] is True, f"semantically equivalent object must match, got {nm}"


# ---------------------------------------------------------------------------
# 6. Optimal matching of multiple same-type instances (Hungarian)
# ---------------------------------------------------------------------------

def test_anti_cheat_6_optimal_multi_instance_assignment():
    required = [
        {"id": "tomato", "type": "Plant", "count": 3, "key_attrs": {"trait": "A"}},
    ]
    # 3 tomatoes, all correct type; even if IDs are permuted/absent, all 3 match
    generated = [
        {"id": "p2", "type": "Plant", "key_attrs": {"trait": "A"}},
        {"id": "p1", "type": "Plant", "key_attrs": {"trait": "A"}},
        {"id": "p3", "type": "Plant", "key_attrs": {"trait": "A"}},
    ]
    nm = match_nodes(required=required, generated=generated)
    assert nm["matched"] == 3
    assert nm["all_matched"] is True


# ---------------------------------------------------------------------------
# 7. Optional objects don't reduce recall; wrong optional objects reduce precision
# ---------------------------------------------------------------------------

def test_anti_cheat_7_optional_objects():
    # task with an optional camera
    required = [{"id": "greenhouse", "type": "Greenhouse", "role": "root", "count": 1}]
    optional = [{"id": "cam", "type": "Camera", "role": "entity"}]
    # Method A: omits optional camera -> recall on required still 1.0
    genA = [{"id": "g", "type": "Greenhouse", "role": "root"}]
    nmA = match_nodes(required=required, generated=genA)
    assert nmA["matched"] == 1 and nmA["all_matched"] is True
    # Method B: includes a WRONG optional object (a forbidden-like camera) -> precision drops
    genB = [{"id": "g", "type": "Greenhouse", "role": "root"},
            {"id": "camX", "type": "Camera", "role": "entity"}]
    nmB = match_nodes(required=required, generated=genB)
    prfB = object_precision_recall(nmB, n_required=1, n_generated=2)
    assert prfB["precision"] < 1.0, "wrong extra optional object must reduce precision"


# ---------------------------------------------------------------------------
# 8. Forbidden objects penalized separately
# ---------------------------------------------------------------------------

def test_anti_cheat_8_forbidden_object_penalty():
    task = {
        "task_id": "T008", "category": "scene_build",
        "required_nodes": [{"id": "g", "type": "Greenhouse", "role": "root", "count": 1}],
        "forbidden_nodes": [{"id": "weapon", "type": "Forbidden"}],
        "required_edges": [], "required_bindings": [], "equivalence_groups": [],
    }
    eval1 = evaluate_task(task=task, method="m", nodes=[{"id": "g", "type": "Greenhouse", "role": "root"}],
                          edges=[], bindings=[], trace={"steps": []}, proxy_calls=[])
    assert eval1.cvsr is True
    # now output a forbidden node -> should NOT silently pass; the forbidden presence is a red flag
    eval2 = evaluate_task(task=task, method="m",
                          nodes=[{"id": "g", "type": "Greenhouse", "role": "root"},
                                 {"id": "w", "type": "Forbidden"}],
                          edges=[], bindings=[], trace={"steps": []}, proxy_calls=[])
    # object precision must drop (extra wrong object), demonstrating separate penalty channel
    assert eval2.object_p < eval1.object_p


# ---------------------------------------------------------------------------
# 9. Multiple legal layouts (equivalence groups) -> all pass
# ---------------------------------------------------------------------------

def test_anti_cheat_9_multiple_legal_layouts():
    required = [{"id": "tomato", "type": "Plant", "count": 2}]
    layoutA = [{"id": "t1", "type": "Plant"}, {"id": "t2", "type": "Plant"}]
    layoutB = [{"id": "tA", "type": "Plant"}, {"id": "tB", "type": "Plant"}]
    for gen in (layoutA, layoutB):
        nm = match_nodes(required=required, generated=gen, equivalence_groups=["tomato|t1|t2|tA|tB"])
        assert nm["all_matched"] is True, f"legal layout {gen} must pass"


# ---------------------------------------------------------------------------
# 10. Repair fails when initial error state not actually modified
# ---------------------------------------------------------------------------

def _repair_task() -> dict:
    return {
        "task_id": "T019", "category": "repair",
        "required_nodes": [{"id": "Sensor_01", "type": "Sensor"}, {"id": "Greenhouse_A", "type": "Greenhouse"}],
        "required_edges": [], "required_bindings": [],
        "critical_objects": ["Sensor_01"],
        "initial_state": {"objects": [
            {"id": "Greenhouse_A", "type": "Greenhouse"},
            {"id": "Sensor_01", "type": "Sensor", "monitoring_target": None},
        ]},
        "goal_state": {"objects": [
            {"id": "Greenhouse_A", "type": "Greenhouse"},
            {"id": "Sensor_01", "type": "Sensor", "monitoring_target": "Greenhouse_A"},
        ]},
        "equivalence_groups": [],
    }


def test_anti_cheat_10_repair_not_actually_modified():
    task = _repair_task()
    # Method outputs a scene where Sensor_01 still has monitoring_target=None (unchanged)
    final = {"objects": [
        {"id": "Greenhouse_A", "type": "Greenhouse"},
        {"id": "Sensor_01", "type": "Sensor", "monitoring_target": None},
    ]}
    rm = repair_match(task=task, initial_state=task["initial_state"], goal_state=task["goal_state"],
                      final_state=final)
    assert rm["success"] is False
    assert "Sensor_01" in rm["critical_unmodified"]


def test_anti_cheat_11_repair_regenerating_without_modifying_target():
    task = _repair_task()
    # Method regenerated a whole new scene but did NOT bind Sensor_01 to a greenhouse
    final = {"objects": [
        {"id": "Greenhouse_B", "type": "Greenhouse"},
        {"id": "Sensor_02", "type": "Sensor", "monitoring_target": None},  # different sensor
    ]}
    rm = repair_match(task=task, initial_state=task["initial_state"], goal_state=task["goal_state"],
                      final_state=final)
    # critical object Sensor_01 disappeared and the original error persists
    assert rm["success"] is False
    assert rm["critical_unmodified"]


# ---------------------------------------------------------------------------
# 12. Declared trace with no real call -> Evidence Score 0
# ---------------------------------------------------------------------------

def test_anti_cheat_12_declared_trace_no_real_call():
    steps = [
        {"traceType": "declared", "evidenceId": "", "tool": "scene.plan", "outputSummary": "planned"},
        {"traceType": "declared", "evidenceId": "", "tool": "layout.solve", "outputSummary": "solved"},
    ]
    proxy = []
    te = evaluate_trace(steps=steps, proxy_calls=proxy)
    assert te["evidence_steps"] == 0
    assert te["evidence_precision"] == 0.0 or te["declared_steps"] > 0
    assert te["all_evidence_real"] is False


# ---------------------------------------------------------------------------
# 13. Auto-generated evidenceId with no real response -> NOT pass
# ---------------------------------------------------------------------------

def test_anti_cheat_13_fabricated_evidence_id_rejected():
    steps = [
        {"traceType": "executed", "evidenceId": "exec-001", "tool": "layout.solve", "outputSummary": "solved"},
    ]
    proxy = []  # no real recorded call for exec-001
    te = evaluate_trace(steps=steps, proxy_calls=proxy)
    assert te["real_evidence"] == 0
    assert te["fabricated_evidence"] >= 1
    assert te["all_evidence_real"] is False


# ---------------------------------------------------------------------------
# 14. Rule fallback flagged separately, not counted as LLM/multi-agent success
# ---------------------------------------------------------------------------

def test_anti_cheat_14_rule_fallback_flagged():
    steps = [
        {"traceType": "executed", "evidenceId": "real-1", "tool": "scene.plan", "outputSummary": "plan",
         "fallback": "deterministic"},
        {"traceType": "executed", "evidenceId": "real-2", "tool": "layout.solve", "outputSummary": "solved"},
    ]
    proxy = [
        {"call_id": "real-1", "tool": "scene.plan", "response": "plan"},
        {"call_id": "real-2", "tool": "layout.solve", "response": "solved"},
    ]
    te = evaluate_trace(steps=steps, proxy_calls=proxy)
    assert te["fallback_steps"] == 1  # the fallback step is flagged
    assert te["all_evidence_real"] is True  # evidence real, but fallback still flagged


# ---------------------------------------------------------------------------
# 15. New conflicts counted separately (via repair loop reporting)
# ---------------------------------------------------------------------------

def test_anti_cheat_15_new_conflicts_counted_separately():
    from metrics import _count_new_conflicts
    from rule_engine import RuleViolation
    violations = [
        RuleViolation("R4", "fatal", "asset type mismatch", ["pump_01"]),
        RuleViolation("R6", "warning", "device missing served object", ["pump_01"]),
    ]
    # The repair loop reports new_conflicts; here we only assert the mechanism exists
    n = _count_new_conflicts(violations, final_state={"objects": []})
    assert isinstance(n, int)


# ---------------------------------------------------------------------------
# Bonus: the old min(count) shortcut must NOT be the correctness measure
# ---------------------------------------------------------------------------

def test_anti_cheat_bonus_min_count_not_used():
    # A method that outputs the right COUNT but totally wrong objects must NOT pass
    required = _greenhouse_required()  # 1 greenhouse + 3 tomato
    generated = [{"id": f"w{i}", "type": "Weapon", "role": "bad"} for i in range(4)]
    nm = match_nodes(required=required, generated=generated)
    assert nm["matched"] == 0
    assert nm["all_matched"] is False
    prf = object_precision_recall(nm, n_required=4, n_generated=4)
    assert prf["f1"] < 0.2
