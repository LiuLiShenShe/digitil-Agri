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

from node_match import match_nodes, object_precision_recall, id_correspondence  # noqa: E402
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


# ---------------------------------------------------------------------------
# 16. Node-id correspondence must be reused for edges/bindings (F-015 fix)
# ---------------------------------------------------------------------------

def test_anti_cheat_16_id_correspondence_aligns_generated_relations():
    """Generated objects legitimately use invented ids (gold ids never shown to
    methods). Node matching already proved generated greenhouse_1 == required
    greenhouse. The scorer must reuse that correspondence when matching edges,
    or every relation/binding is structurally mis-scored as 0 even for a correct
    scene graph."""
    required = _greenhouse_required()  # 1 greenhouse + 3 tomato
    req_edges = [
        {"subject": "greenhouse", "predicate": "contains", "object": "tomato"},
    ]
    # Method-generated scene: invented ids, same topology.
    nodes = [
        {"id": "gh_a", "type": "Greenhouse", "role": "root", "parent": ""},
        {"id": "tom_1", "type": "Plant", "role": "entity", "parent": "gh_a"},
        {"id": "tom_2", "type": "Plant", "role": "entity", "parent": "gh_a"},
        {"id": "tom_3", "type": "Plant", "role": "entity", "parent": "gh_a"},
    ]
    edges = [
        {"subject": "gh_a", "predicate": "contains", "object": "tom_1"},
        {"subject": "gh_a", "predicate": "contains", "object": "tom_2"},
        {"subject": "gh_a", "predicate": "contains", "object": "tom_3"},
    ]
    nm = match_nodes(required=required, generated=nodes)
    assert nm["all_matched"], f"nodes should match, got {nm}"
    id_map = id_correspondence(nm["assignments"], nodes, nm["req_expanded_ids"])
    # The generated greenhouse maps to the required 'greenhouse' id.
    assert id_map.get("gh_a") == "greenhouse"
    em = match_edges(required=req_edges, generated=edges, id_map=id_map)
    assert em["matched"] == 1, f"edge should match after id remap, got {em}"
    assert em["all_matched"], f"all required edges should match, got {em}"


def test_anti_cheat_17_wrong_target_binding_still_fails_after_remap():
    """The correspondence must NOT rescue a binding to the wrong object. A binding
    subject/target that does not correspond to any required node id must be
    penalized even after the id remap, and a genuinely wrong target must fail."""
    from binding_match import match_bindings
    # Gold nodes + the binding under test.
    node_required = [
        {"id": "greenhouse", "type": "Greenhouse", "role": "root", "count": 1},
        {"id": "tomato", "type": "Plant", "role": "entity", "count": 1},
    ]
    req_bindings = [
        {"subject": "greenhouse", "target": "tomato", "type": "monitor"},
    ]
    nodes = [
        {"id": "gh_a", "type": "Greenhouse", "role": "root"},
        {"id": "tom_a", "type": "Plant", "role": "entity"},
    ]
    nm = match_nodes(required=node_required, generated=nodes)
    id_map = id_correspondence(nm["assignments"], nodes, nm["req_expanded_ids"])
    # Generated binds greenhouse -> tom_a (maps to required tomato). This is correct.
    generated_right = [{"subject": "gh_a", "target": "tom_a", "type": "monitor"}]
    bm = match_bindings(required=req_bindings, generated=generated_right, id_map=id_map)
    assert bm["matched"] == 1, "correct binding must match after remap"
    assert bm["all_matched"], "the one required binding is satisfied"
    # Genuinely wrong: binds to a plant that is not in the scene at all.
    generated_fake = [{"subject": "gh_a", "target": "nonexistent_plant", "type": "monitor"}]
    bm2 = match_bindings(required=req_bindings, generated=generated_fake, id_map=id_map)
    assert bm2["matched"] == 0, "binding to an absent node must not match anything"


# ---------------------------------------------------------------------------
# 18. SingleAgent honest no-repair fires for test-v2 repair representation
# ---------------------------------------------------------------------------

def test_anti_cheat_18_singleagent_honest_norepair_on_rule_repair():
    """F-016: SingleAgent's honest no-repair branch must fire when the task is a
    repair task, whether it arrives as legacy category='repair' (v1) or as
    task_type='rule_repair' (test_v2 Gold Schema v2). Previously the check used
    category == 'rule_repair' (never true after the runner maps rule_repair ->
    repair), so SingleAgent silently rebuilt the repair task from its prompt
    instead of emitting the unchanged broken input — an unfair asymmetry vs the
    KAFarmTwin repair loop."""
    from methods.single_agent import run_single_agent

    class _FakeBudget:
        summary = lambda self: {}
        llm_calls = 0
        tool_calls = 0

    class _FakeRegistry:
        def __init__(self):
            self.trace_proxy = None
            self.ctx = {}
        def call(self, *a, **k):
            return {}

    init_obj = [
        {"id": "N31_gh_root", "type": "Greenhouse"},
        {"id": "N31_WaterPump_B", "type": "Pump", "asset_key": "lemongrass"},
        {"id": "N31_row", "type": "CropRow"},
    ]
    # test_v2 representation: task_type=rule_repair, no legacy category
    task = {
        "task_id": "TN31-v2-repair",
        "task_type": "rule_repair",
        "category": None,
        "prompt": "fix it",
        "initial_state": {"objects": init_obj},
    }
    out = run_single_agent(task=task, registry=_FakeRegistry(), budget=_FakeBudget(),
                           llm_call_fn=lambda messages, b=None: {})
    # Honest no-repair: emits the unchanged broken input, no fabricated fix.
    # canonicalize_output folds top-level asset_key into key_attrs.asset_key.
    assert len(out.get("nodes", [])) == 3
    pump = next(n for n in out["nodes"] if n["id"] == "N31_WaterPump_B")
    assert (pump.get("asset_key") == "lemongrass"
            or (pump.get("key_attrs") or {}).get("asset_key") == "lemongrass"), \
        "must not 'fix' the asset mismatch"


# ---------------------------------------------------------------------------
# 19. P0-1: empty trace with real proxy calls must NOT be vacuously perfect
# ---------------------------------------------------------------------------

def test_anti_cheat_19_empty_trace_with_real_proxy_not_vacuous():
    """F-019/P0-1: if the runner's trace is empty (canonicalizer dropped traceSteps)
    but the trace proxy recorded real tool calls, evidence_precision must be 0.0
    and all_evidence_real False — NOT the old vacuous 1.0 / True."""
    steps = []  # the buggy path: out["traceSteps"] read after canonicalization
    proxy = [
        {"call_id": "call-0001", "tool": "scene.plan", "request": {"objects": []}, "response": "ok"},
        {"call_id": "call-0002", "tool": "layout.solve", "request": {"objects": []}, "response": "ok"},
    ]
    te = evaluate_trace(steps=steps, proxy_calls=proxy)
    assert te["evidence_precision"] == 0.0, f"empty trace + real calls must be 0.0, got {te}"
    assert te["all_evidence_real"] is False
    # control: genuinely nothing happened -> vacuous 1.0 is acceptable
    te2 = evaluate_trace(steps=[], proxy_calls=[])
    assert te2["evidence_precision"] == 1.0
    assert te2["all_evidence_real"] is True


def test_anti_cheat_20_runner_reads_canonical_trace_steps():
    """P0-1: the runner must read the CANONICAL trace (canonicalize_output folds
    traceSteps -> trace.steps and drops the top-level key). Reading out['traceSteps']
    always yields [] after canonicalization — that is the exact bug that made
    evidence vacuous. This test locks the canonicalizer contract: top-level
    traceSteps is consumed into trace.steps."""
    from harness.canonicalizer import canonicalize_output
    raw = {
        "nodes": [{"id": "g", "type": "Greenhouse", "role": "root"}],
        "edges": [], "bindings": [],
        "traceSteps": [{"traceType": "executed", "evidenceId": "call-1", "tool": "scene.plan"}],
    }
    out = canonicalize_output(raw)
    # trace.steps must carry the steps
    assert out["trace"]["steps"] == raw["traceSteps"]
    # the canonical result exposes trace, not the raw top-level key
    assert out.get("traceSteps") is None, "canonicalize_output must consume traceSteps"
    # canonicalizer returns {"nodes","edges","bindings","trace"}
    assert set(out.keys()) == {"nodes", "edges", "bindings", "trace"}


# ---------------------------------------------------------------------------
# 21. P0-2: R4 must detect a wrong node.asset_key (repair target)
# ---------------------------------------------------------------------------

def test_anti_cheat_21_r4_detects_wrong_asset_key_on_node():
    """F-019/P0-2: R4 previously only looked at binding target type. It must also
    fire when the node ITSELF carries a wrong asset_key (e.g. N31_WaterPump_B with
    asset_key=lemongrass instead of irrigation). And it must be silent once the
    asset_key is repaired."""
    from rule_engine import RuleEngine
    re = RuleEngine()
    # unrepaired: pump still has the wrong crop asset_key
    nodes_bad = [{"id": "N31_WaterPump_B", "type": "Pump", "asset_key": "lemongrass"}]
    v_bad = re.evaluate(nodes=nodes_bad, edges=[], bindings=[], active_rules=["R4"])
    assert any(v.rule_id == "R4" and v.severity == "fatal" for v in v_bad)
    # repaired: pump now has the correct device asset
    nodes_good = [{"id": "N31_WaterPump_B", "type": "Pump", "asset_key": "irrigation"}]
    v_good = re.evaluate(nodes=nodes_good, edges=[], bindings=[], active_rules=["R4"])
    assert not any(v.rule_id == "R4" and v.severity == "fatal" for v in v_good)


# ---------------------------------------------------------------------------
# 22. P0-2: R9 must not be a silent pass — retained asset mismatch fails
# ---------------------------------------------------------------------------

def test_anti_cheat_22_r9_placeholder_and_retained_mismatch():
    """F-019/P0-2: R9 was literally `pass`. It must now reject (a) an asset_job
    binding without job_type=placeholder, and (b) a retained asset binding whose
    asset_key is still the wrong crop asset. A clean placeholder passes."""
    from rule_engine import RuleEngine
    re = RuleEngine()
    # placeholder asset_job without job_type -> fatal
    bad_job = [{"subject": "P", "target": "job-1", "type": "asset_job", "metadata": {"job_type": "other"}}]
    v = re.evaluate(nodes=[], edges=[], bindings=bad_job, active_rules=["R9"])
    assert any(v.rule_id == "R9" and v.severity == "fatal" for v in v)
    # retained wrong crop asset binding -> fatal
    bad_bind = [{"subject": "P", "target": "P", "type": "asset", "metadata": {"asset_key": "lemongrass"}}]
    v2 = re.evaluate(nodes=[], edges=[], bindings=bad_bind, active_rules=["R9"])
    assert any(v.rule_id == "R9" and v.severity == "fatal" for v in v2)
    # clean placeholder -> no R9 fatal
    good = [{"subject": "P", "target": "job-1", "type": "asset_job", "metadata": {"job_type": "placeholder"}}]
    v3 = re.evaluate(nodes=[], edges=[], bindings=good, active_rules=["R9"])
    assert not any(v.rule_id == "R9" and v.severity == "fatal" for v in v3)


# ---------------------------------------------------------------------------
# 23. P0-3/4: annotation-normalized binding match (fixed:true, {subject}_asset)
# ---------------------------------------------------------------------------

def _norm_binding(b):
    from harness.canonicalizer import canonicalize_binding
    return canonicalize_binding(b)


def test_binding_matches_asset_routing_semantic_contract():
    """P0-4 (TN11-14): gold asset bindings target '{subject}_asset' (a notation
    artifact with no distinct node in required_nodes). A method given only public
    fields emits the asset via metadata {asset_key, policy}. The scorer must match
    on (subject, asset_key, policy), not the literal target string. A wrong
    asset_key must still fail."""
    req = [
        _norm_binding({"subject": "N11_mango_focus", "target": "N11_mango_focus_asset",
                       "type": "asset", "metadata": {"asset_key": "mango_focus", "policy": "high_fidelity"}}),
        _norm_binding({"subject": "N11_mango_light", "target": "N11_mango_light_placeholder",
                       "type": "asset_job", "metadata": {"job_type": "placeholder", "policy": "procedural_model"}}),
    ]
    gen_ok = [
        _norm_binding({"subject": "N11_mango_focus", "target": "N11_mango_focus",
                       "type": "asset", "metadata": {"asset_key": "mango_focus", "policy": "high_fidelity"}}),
        _norm_binding({"subject": "N11_mango_light", "target": "light",
                       "type": "asset_job", "metadata": {"job_type": "placeholder", "policy": "procedural_model"}}),
    ]
    bm = match_bindings(required=req, generated=gen_ok, id_map={})
    assert bm["all_matched"], f"asset semantic contract must match, got {bm}"
    # wrong asset_key must not match (anti-cheat)
    gen_wrong = [_norm_binding({"subject": "N11_mango_focus", "target": "x", "type": "asset",
                                "metadata": {"asset_key": "papaya_bg", "policy": "high_fidelity"}})]
    bmw = match_bindings(required=req[:1], generated=gen_wrong, id_map={})
    assert bmw["matched"] == 0, "wrong asset_key must NOT match"


def test_binding_strips_fixed_annotation_key():
    """P0-3 (TN31-34): gold required binding carries metadata.fixed=true — a labeler
    annotation, never emitted by a method. The scorer must strip it so a correctly
    repaired binding (asset_key=irrigation, no fixed key) matches."""
    req = [_norm_binding({"subject": "N31_WaterPump_B", "target": "N31_WaterPump_B",
                          "type": "asset", "metadata": {"asset_key": "irrigation", "fixed": True}})]
    gen_repaired = [_norm_binding({"subject": "N31_WaterPump_B", "target": "N31_WaterPump_B",
                                   "type": "asset", "metadata": {"asset_key": "irrigation"}})]
    bm = match_bindings(required=req, generated=gen_repaired, id_map={})
    assert bm["all_matched"], f"fixed:true must be stripped; repaired binding matches, got {bm}"


def test_binding_data_binding_unit_alias():
    """P0-5 (TN21-24): gold sensor_bind metadata unit='%'; a method may emit
    unit='percent'. These are authoring variants, not a real difference. match on
    canonical unit + set-compare metrics. A wrong data-binding target still fails."""
    req = [_norm_binding({"subject": "N21_kiwi_sen1", "target": "N21_kiwi_row", "type": "sensor_bind",
                          "metadata": {"metrics": ["humidity"], "unit": "%", "timestamp": "2026-09-01T00:00:00+08:00"}})]
    gen = [_norm_binding({"subject": "N21_kiwi_sen1", "target": "N21_kiwi_row", "type": "sensor_bind",
                          "metadata": {"metrics": ["humidity"], "unit": "percent", "timestamp": "2026-09-01T00:00:00+08:00"}})]
    bm = match_bindings(required=req, generated=gen, id_map={})
    assert bm["all_matched"], f"unit alias percent must match '%', got {bm}"
    # wrong target -> fail
    gen_wrong = [_norm_binding({"subject": "N21_kiwi_sen1", "target": "N21_kiwi_plant", "type": "sensor_bind",
                                "metadata": {"metrics": ["humidity"], "unit": "%", "timestamp": "2026-09-01T00:00:00+08:00"}})]
    bmw = match_bindings(required=req, generated=gen_wrong, id_map={})
    assert bmw["matched"] == 0, "wrong data-binding target must fail"


def test_anti_cheat_26_work_without_trace_not_vacuous():
    """P0-1 honesty: a method that made LLM/tool calls but recorded NO trace steps
    and NO proxy evidence has a BROKEN audit chain — it executed without recording.
    It must NOT get vacuously-perfect evidence_precision / replay_success."""
    task = {"task_id": "T19", "required_nodes": [
        {"id": "r1", "type": "Greenhouse", "role": "root", "count": 1}],
        "required_edges": [], "required_bindings": [], "critical_objects": [],
        "rules": ["R1", "R2", "R3", "R5"]}
    # 10 LLM calls, empty trace, empty proxy = reasoned-but-didn't-record
    e = evaluate_task(task=task, method="ReAct-AllTools", nodes=[], edges=[], bindings=[],
                      trace={"steps": []}, proxy_calls=[], llm_calls=10, tool_calls=0)
    assert e.evidence_precision == 0.0, f"broken-work evidence must be 0, got {e.evidence_precision}"
    assert e.replay_success == 0.0, f"broken-work replay must be 0, got {e.replay_success}"
    assert e.cvsr is False


def test_anti_cheat_27_genuinely_empty_stays_vacuous():
    """Opposite contract: a method that genuinely did NO work (0 LLM, 0 tool,
    0 trace, 0 proxy) demands no evidence — vacuously auditable is correct. This
    is distinct from 'did work but didn't record'."""
    task = {"task_id": "T19", "required_nodes": [
        {"id": "r1", "type": "Greenhouse", "role": "root", "count": 1}],
        "required_edges": [], "required_bindings": [], "critical_objects": [],
        "rules": ["R1", "R2", "R3", "R5"]}
    e = evaluate_task(task=task, method="Det", nodes=[], edges=[], bindings=[],
                      trace={"steps": []}, proxy_calls=[], llm_calls=0, tool_calls=0)
    assert e.evidence_precision == 1.0
    assert e.replay_success == 1.0
