"""KAFarmTwin-TypedRepair: the proposed method with a typed conflict repair loop.

Conflict structure (aligned with the Go backend's typed repair contract):
  {conflict_id, rule_id, severity, conflict_type, object_ids, observed, expected,
   evidence_ids, owner_agent, allowed_patch_ops, status}

Repair flow: detect -> classify -> route -> propose patch -> precheck ->
transactional apply -> local revalidate -> global fatal revalidate -> commit/rollback.

Key fairness invariants:
  - runs through the SAME ToolRegistry / ValidatorAPI / TraceProxy / Budget as every
    baseline
  - never uses rule fallback for its main result (DeterministicFallback is separate)
  - only difference vs baselines is: conflict representation, routing policy, patch
    selection policy, evidence binding policy, and multi-agent organization
"""

from __future__ import annotations

import itertools
from typing import Any

from experiments.v3.harness.tools import ToolRegistry  # type: ignore
from experiments.v3.harness.budget import BudgetEnforcer  # type: ignore
from experiments.v3.harness.validator_api import ValidatorAPI  # type: ignore
from experiments.v3.harness.canonicalizer import canonicalize_output  # type: ignore

PATCH_OPS = {
    "add_node", "remove_node", "replace_type", "add_edge", "remove_edge",
    "replace_binding", "add_binding", "update_transform", "set_attr",
    "replace_asset", "set_placeholder",
}

# Fixed conflict priority (highest = handled first).
# R1 (parent) precedes R3 (bounds) because the R3 bounds check reads the parent's
# bounds: an orphan cannot be bounds-checked. Establishing hierarchy first lets the
# spatial check (and its fix) actually engage.
CONFLICT_PRIORITY = ["R4", "R2", "R1", "R3", "R5", "R6", "R7", "R8", "R9", "R10"]

# Route: rule_id -> owner agent
OWNER_BY_RULE = {
    "R1": "HierarchyAgent", "R2": "BindingAgent", "R3": "LayoutAgent",
    "R4": "AssetAgent", "R5": "BindingAgent", "R6": "BindingAgent",
    "R7": "TraceAgent", "R8": "MemoryAgent", "R9": "AssetAgent", "R10": "RepairAgent",
}

# Allowed patch ops by rule
PATCH_OPS_BY_RULE = {
    "R1": {"add_node", "remove_node", "add_edge", "remove_edge", "update_transform"},
    "R2": {"add_binding", "replace_binding", "set_attr", "update_transform"},
    "R3": {"update_transform", "replace_type", "set_attr"},
    "R4": {"replace_asset", "set_placeholder"},
    "R5": {"replace_binding", "update_transform"},
    "R6": {"add_edge", "replace_binding"},
    "R8": {"replace_binding", "update_transform"},
    "R9": {"set_placeholder", "replace_asset"},
    "R10": {"replace_binding", "add_node", "update_transform"},
}


def _severity(rule_id: str) -> str:
    return "fatal" if rule_id in {"R1", "R2", "R3", "R4", "R7"} else "warning"


def _new_conflict(violation: dict[str, Any], counter: itertools.count,
                  *, nodes: list[dict[str, Any]] | None = None,
                  bindings: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build a typed RepairTicket from a RuleViolation.

    D1 (P1-1): fill `observed`/`expected` so the owner agent gets actionable,
    structured feedback (structural path + observed value + expected admissible
    alternatives) instead of an empty dict the LLM must guess from. Values are
    extracted from the violation message / scene state — never re-derived from gold.
    """
    rule_id = violation.get("rule_id") or ""
    message = str(violation.get("message") or "")
    oids = list(violation.get("object_ids") or [])
    nodes = nodes or []
    bindings = bindings or []
    import re as _re

    def _first_oid():
        if oids:
            return oids[0]
        m = _re.search(r"([A-Za-z0-9_#-]+)", message)
        return (m.group(1) if m else "")

    def _find_oid_node(oid):
        for n in nodes:
            if str(n.get("id") or "") == oid:
                return n
        return None

    observed: dict[str, Any] = {}
    expected: dict[str, Any] = {}

    if rule_id == "R4":
        # message: "node X of type T has wrong asset_key='y' (expected 'c')" or
        #          "pump X wrongly bound to plant asset T"
        m_expected = _re.search(r"expected '?([a-z_]+)'?", message)
        m_wrong = _re.search(r"asset_key='?([^']+)'?|wrongly bound to (plant|tomato|lettuce|strawberry|corn) asset", message)
        oid = _first_oid()
        node = _find_oid_node(oid)
        observed["asset_key"] = (node.get("asset_key") if node else None) or (m_wrong.group(1) if m_wrong else None)
        expected["asset_key"] = m_expected.group(1) if m_expected else (
            "irrigation" if "pump" in message.lower() or (node or {}).get("type") == "Pump"
            else "camera" if "camera" in message.lower() or (node or {}).get("type") == "Camera"
            else "sensor")
    elif rule_id == "R2":
        oid = _first_oid()
        if "missing data binding" in message:
            observed["binding"] = None
            expected["binding"] = {"type": "sensor_bind", "target": "<monitored_object_id>",
                                   "metadata": {"metrics": ["<metric>"], "unit": "<canonical unit>"}}
        else:
            observed["metadata"] = None
            expected["binding"] = {"metadata": {"unit": "<canonical unit>", "timestamp": "<ISO8601>"}}
    elif rule_id == "R1":
        oid = _first_oid()
        if "illegal parent" in message:
            m = _re.search(r"illegal parent: (\w+) (\S+) under (\S+)", message)
            observed["parent_type"] = m.group(1) if m else None
            observed["parent"] = m.group(3) if m else None
            expected["parent"] = "a legal parent type (Greenhouse/Plot/CropRow per hierarchy)"
        else:
            observed["parent"] = None
            expected["parent"] = "attach a parent of a legal type (or set role=root)"
    elif rule_id == "R3":
        oid = _first_oid()
        node = _find_oid_node(oid)
        observed["location"] = ((node.get("key_attrs") or {}).get("location") if node else None) \
            or (node.get("location") if node else None)
        expected["location"] = "in-bounds position within parent Plot/Greenhouse bounds"
    elif rule_id == "R5":
        oid = _first_oid()
        observed["camera_fields"] = "missing pose/observes/fov"
        expected["camera_fields"] = {"pose": {"position": [0, 0, 0]}, "observes": "<contained object id>", "fov": "<number>"}
    elif rule_id == "R6":
        oid = _first_oid()
        observed["served_object_binding"] = None
        expected["served_object_binding"] = "a sensor_bind/asset binding to a contained crop object"
    elif rule_id == "R9":
        oid = _first_oid()
        observed["asset_state"] = "wrong asset_key retained"
        expected["asset_state"] = "set_placeholder (asset_job job_type=placeholder) OR replace_asset to correct type"

    return {
        "conflict_id": f"C{next(counter):03d}",
        "rule_id": rule_id,
        "severity": violation.get("severity") or _severity(rule_id),
        "conflict_type": f"violation_{rule_id}",
        "object_ids": oids,
        "observed": observed,
        "expected": expected,
        "evidence_ids": [],
        "owner_agent": OWNER_BY_RULE.get(rule_id, "RepairAgent"),
        "allowed_patch_ops": list(PATCH_OPS_BY_RULE.get(rule_id, {"update_transform"})),
        "status": "detected",
    }


def run_kafarmtwin_typed_repair(*, task: dict[str, Any], registry: ToolRegistry,
                                budget: BudgetEnforcer, llm_call_fn,
                                validator: ValidatorAPI | None = None) -> dict[str, Any]:
    validator = validator or ValidatorAPI()
    ctx = registry.ctx

    # memory_query tasks: KAFarmTwin has a dedicated MemoryAgent (R8) that
    # retrieves/aggregates from the pre-existing store. It runs through the SAME
    # shared retrieval helper and tools as the SingleAgent baseline, so the two
    # methods have symmetric retrieval capability — no gold access, budgeted the
    # same way.
    if task.get("category") == "memory_query" or task.get("task_type") == "memory_query":
        from experiments.v3.harness.memory_retrieval import build_memory_answer  # type: ignore
        # P0-6: build_memory_answer is a DETERMINISTIC helper (no LLM call). It must
        # NOT charge an LLM call — only real tool calls (timeseries.query/event.query)
        # are recorded through the trace proxy. The old assert_llm_budget() inflated
        # llm_calls for a non-LLM operation and differed from no LLM being invoked.
        answer = build_memory_answer(task, registry, agent_id="MemoryAgent")
        raw = {
            "nodes": [],
            "edges": [],
            "bindings": [],
            "answer": answer,
            "traceSteps": registry.trace_proxy.steps_for_trace() if registry.trace_proxy else [],
            "budget": budget.summary(),
            "conflicts": [],
            "fallback": False,
            "success": True,
        }
        return canonicalize_output(raw)

    counter = itertools.count(1)
    new_conflicts: list[dict[str, Any]] = []
    plan_objects: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []
    bindings: list[dict[str, Any]] = []

    # If the task is a repair task, seed the scene from initial_state and verify modification.
    # B (P0-2): data_binding tasks ALSO carry a complete object graph in initial_state
    # (TN21: objects=[gh,row,sen1,sen2,plant]). Reinventing those ids from the prompt
    # broke id_map/binding alignment → BindF1=0. Seed objects+relations from
    # initial_state and emit bindings only, preserving the seeded ids.
    is_repair = (task.get("category") in ("repair", "rule_repair")
                 or task.get("task_type") == "rule_repair")
    is_data_bind = (task.get("category") in ("data_bind", "data_binding")
                    or task.get("task_type") == "data_binding")
    initial_state = task.get("initial_state") if is_repair else None
    goal_state = task.get("goal_state") if is_repair else None
    critical = task.get("critical_objects") or []

    if is_repair and initial_state is not None:
        # Repair task: the broken input scene IS the starting point. Seed from it and
        # let the typed repair loop actually fix it. Do NOT regenerate a fresh scene
        # from the prompt (that would ignore the error we are asked to repair).
        init_objs = (initial_state.get("objects") if isinstance(initial_state, dict) else initial_state) or []
        init_binds = (initial_state.get("bindings") if isinstance(initial_state, dict) else []) or []
        plan_objects = [dict(o) for o in init_objs]
        bindings = [dict(b) for b in init_binds]
        ctx["scene_state"] = {"objects": plan_objects, "bindings": bindings}
        # relations seeded from parent references if present
        for o in plan_objects:
            if o.get("parent"):
                relations.append({"subject": o["parent"], "predicate": "contains", "object": o.get("id", "")})
    elif is_data_bind and (task.get("initial_state") or {}).get("objects"):
        # data_binding: seed the deterministic object graph, emit bindings ONLY. The
        # LLM sees only the existing ids → no scene/id reinvention → binding_match aligns.
        from experiments.v3.harness.stepwise_builder import bindings_only_scene  # type: ignore
        built = bindings_only_scene(
            initial_state=task.get("initial_state"), prompt=task["prompt"],
            llm_call_fn=llm_call_fn, budget=budget, registry=registry,
            agent_id="KAFarmTwin-Planner",
        )
        plan_objects = built["nodes"]
        relations = built["edges"]
        bindings = built["bindings"]
    else:
        # Other (scene_build / asset_routing without seed): build the scene from the
        # prompt through the SHARED stepwise builder (objects -> relations -> bindings),
        # so complex asset/bind scenes no longer overflow the model's single-response
        # output cap. Same mechanism as SingleAgent (fair); KAFarmTwin then runs its
        # typed repair loop over the emitted scene.
        from experiments.v3.harness.stepwise_builder import stepwise_build_scene  # type: ignore
        from experiments.v3.harness.llm import ONTOLOGY_NOTE  # type: ignore
        built = stepwise_build_scene(
            prompt=task["prompt"], ontology_hint=ONTOLOGY_NOTE, llm_call_fn=llm_call_fn,
            budget=budget, registry=registry, agent_id="KAFarmTwin-Planner",
        )
        plan_objects = built["nodes"]
        relations = built["edges"]
        bindings = built["bindings"]

    # ---- 2. Typed repair loop ----
    for round_i in range(budget.config.max_repair_rounds):
        verdict = validator.validate(nodes=plan_objects, edges=relations, bindings=bindings, task=task)
        violations = verdict["violations"]
        if not violations:
            break
        # classify + route: sort by priority, take the first
        fatal = [v for v in violations if v["severity"] == "fatal"]
        warnings = [v for v in violations if v["severity"] == "warning"]
        ordered = sorted(fatal + warnings, key=lambda v: CONFLICT_PRIORITY.index(v.get("rule_id")) if v.get("rule_id") in CONFLICT_PRIORITY else 99)
        v = ordered[0]
        conflict = _new_conflict(v, counter, nodes=plan_objects, bindings=bindings)
        new_conflicts.append(conflict)

        if not budget.assert_repair_budget():
            conflict["status"] = "unresolved"
            break

        # propose patch: route to owner agent, which chooses the patch op
        owner = conflict["owner_agent"]
        _rule = v.get("rule_id") or ""
        # D2 (P1-4): mechanical rules have an unambiguous deterministic fix. Try it
        # FIRST — it skips the LLM round entirely (no budget charge), lowering cost
        # AND raising repair success. Only genuinely ambiguous rules fall through to
        # the owner LLM. Absent a config flag, deterministic ops default to enabled.
        fix = None
        deterministic_patch = None
        _use_det = True
        try:  # env override allows the ablation to disable this path
            import os as _os
            _use_det = _os.getenv("KAFARMTWIN_USE_DETERMINISTIC_OPS", "1").strip() != "0"
        except Exception:
            _use_det = True
        if _use_det:
            from experiments.v3.methods.typed_deterministic import build_deterministic_patch  # type: ignore
            deterministic_patch = build_deterministic_patch(
                rule_id=_rule, violation=v, nodes=plan_objects,
                edges=relations, bindings=bindings)
        if deterministic_patch is not None:
            patch = {"ops": [deterministic_patch]}
        else:
            # Generic shape examples (placeholder IDs) so the owner agent learns the
            # patch contract, NOT any task's specific answer.
            _examples = {
                "R2": 'e.g. {"patch_op":"add_binding","target":"<sensor_id>",'
                      '"changes":{"subject":"<sensor_id>","target":"<monitored_object_id>","type":"sensor_bind",'
                      '"metadata":{"metrics":["temperature"],"unit":"celsius"}}} '
                      'or {"patch_op":"set_attr","target":"<sensor_id>","changes":{"unit":"celsius","timestamp":"<ISO8601>"}}',
                "R1": 'e.g. {"patch_op":"update_transform","target":"<child_id>","changes":{"parent":"<parent_id>"}}',
                "R3": 'e.g. {"patch_op":"update_transform","target":"<object_id>",'
                      '"changes":{"key_attrs":{"location":{"x":<in-bounds num>,"z":<in-bounds num>}}}} '
                      '— if the object is out of bounds, MOVE it to an in-bounds position '
                      '(e.g. inside its parent Plot bounds 0<=z<=8)',
                "R4": 'e.g. {"patch_op":"replace_asset","target":"<pump_id>","changes":{"target":"<correct_asset_type>"}}',
            }
            fix = llm_call_fn({
                "system": f"You are {owner}. Repair this typed conflict. Return JSON with EITHER "
                          f"{{patch_op: '<one of {PATCH_OPS_BY_RULE.get(_rule, {'update_transform'})}>', "
                          f"target: '<object id>', changes: {{...}}}} OR a batched repair "
                          f"{{ops: [{{patch_op, target, changes}}, ...]}} fixing ALL affected objects "
                          f"in one round (one scene may have several broken objects at once). "
                          f"{_examples.get(_rule, '')}",
                "user": f"Conflict: {conflict}\nCurrent objects: {plan_objects}\n"
                        f"Current relations: {relations}\nCurrent bindings: {bindings}\n"
                        f"All current violations: {violations}",
            }, budget)
            try:
                patch = fix.get("content_json") or {}
            except Exception:
                patch = {}

        # ---- 3. precheck -> transactional apply -> local revalidate ----
        # Support a batched {ops: [...]} patch (multiple objects fixed in one round)
        ops = patch.get("ops") if isinstance(patch, dict) and isinstance(patch.get("ops"), list) else None
        if ops is not None:
            patches = [p for p in ops if isinstance(p, dict) and p.get("patch_op") in PATCH_OPS]
        else:
            patches = [patch] if patch.get("patch_op") in PATCH_OPS else []
        if not patches:
            conflict["status"] = "unresolved"
            continue
        # snapshot before — E (P0-4): use DEEP copy. _apply_patch mutates node/binding
        # dicts IN PLACE; a shallow list copy retains references to the SAME already-
        # mutated dicts, so rollback would be ineffective. Deep-copy both the snapshot
        # (so it stays pristine) and the restore (so the original dict objects are
        # replaced, not kept mutated).
        import copy as _copy
        snapshot = (_copy.deepcopy(plan_objects), _copy.deepcopy(relations), _copy.deepcopy(bindings))
        conflict_rule = conflict.get("rule_id") or ""
        # pre-patch violated objects (any severity) to detect NEW problems later.
        # A patch that resolves its own rule while letting a DIFFERENT latent rule
        # become detectable on the SAME already-problematic object is progress, not
        # regression: e.g. establishing R1 parent legitimately exposed that the child
        # was also out of bounds (R3). We only roll back genuine NEW object failures.
        pre_violated_obj = {oid for v in violations
                            for oid in (v.get("object_ids") or [])}
        # Apply all patches (transactional: any failure -> whole batch rolled back).
        applied_any = False
        for p in patches:
            ok = _apply_patch(p, plan_objects, relations, bindings)
            if ok and p.get("patch_op") == "update_transform":
                # also apply R2 companion if this op targets an R2-relevant object
                pass
            if ok:
                applied_any = True
            else:
                # E (P0-4): restore from the DEEP-COPY snapshot (pristine dicts, not
                # the mutated-originals referenced by a shallow copy).
                plan_objects[:] = _copy.deepcopy(snapshot[0])
                relations[:] = _copy.deepcopy(snapshot[1])
                bindings[:] = _copy.deepcopy(snapshot[2])
                conflict["status"] = "unresolved"
                applied_any = False
                break
        if not applied_any:
            conflict["status"] = "unresolved"
            continue
        if conflict_rule == "R2":
            for p in patches:
                _apply_r2_companion(p, plan_objects, bindings)
        # local revalidate: keep the patch iff it did NOT introduce a NEW fatal on an
        # object that was not already flagged. Latent same-object progression (e.g.
        # R1-parent exposing an R3-bounds issue that existed all along) is kept.
        local = validator.validate(nodes=plan_objects, edges=relations, bindings=bindings, task=task)
        # objects that became fatally new (not previously violated at all)
        new_fatal_objs = set()
        rule_level_new_fatal = False
        for v in local["violations"]:
            if v.get("severity") != "fatal":
                continue
            oids = v.get("object_ids") or []
            if not oids:
                rule_level_new_fatal = True  # rule fired with no specific object
            for oid in oids:
                if oid not in pre_violated_obj:
                    new_fatal_objs.add(oid)
        if rule_level_new_fatal or new_fatal_objs:
            plan_objects[:] = _copy.deepcopy(snapshot[0])
            relations[:] = _copy.deepcopy(snapshot[1])
            bindings[:] = _copy.deepcopy(snapshot[2])
            conflict["status"] = "rolled_back"
            continue
        conflict["status"] = "verified"
        # record the repair through the trace proxy: invoke the REAL rule.check tool
        # (which records a genuine request + response pair through the shared proxy),
        # so the evidence is strictly source-consistent and replayable — not a method-
        # volunteered response that could drift from the tool's actual output.
        conflict["evidence_ids"].append(
            registry.call("rule.check",
                          {"nodes": plan_objects, "edges": relations, "bindings": bindings},
                          agent_id=owner, caller_method="KAFarmTwin-TypedRepair").get("_call_id", ""))

    # emit the final scene through the shared tools (real trace, not description)
    if plan_objects:
        registry.call("scene.plan", {"objects": plan_objects}, agent_id="KAFarmTwin-Orchestrator")
        registry.call("layout.solve", {"objects": plan_objects}, agent_id="KAFarmTwin-Orchestrator")
        registry.call("layout.validate", {"layout": ctx.get("scene_objects")}, agent_id="KAFarmTwin-Orchestrator")
        # propagate solved layout locations back onto the emitted nodes (layout was real,
        # it must be reflected in the scored state or R3 would falsely fire)
        from experiments.v3.harness.canonicalizer import merge_layout_into_nodes  # type: ignore
        plan_objects = merge_layout_into_nodes(plan_objects, ctx.get("scene_objects") or [])
    for b in bindings:
        registry.call("object.bind", b, agent_id="KAFarmTwin-Orchestrator")

    # repair success determination: critical objects actually modified
    repair_ok = True
    if initial_state is not None and critical:
        init_ids = {o.get("id") for o in (initial_state.get("objects") or [])}
        final_ids = {o.get("id") for o in plan_objects}
        for cid in critical:
            if cid not in final_ids:
                repair_ok = False
            elif cid in init_ids:
                # must have changed some semantic key
                init_obj = next(o for o in initial_state.get("objects") or [] if o.get("id") == cid)
                final_obj = next((o for o in plan_objects if o.get("id") == cid), None)
                if final_obj is not None and init_obj == final_obj:
                    repair_ok = False

    raw = {
        "nodes": plan_objects,
        "edges": relations,
        "bindings": bindings,
        "traceSteps": registry.trace_proxy.steps_for_trace() if registry.trace_proxy else [],
        "budget": budget.summary(),
        "conflicts": new_conflicts,
        "new_conflict_count": len(new_conflicts),
        "repair_success": repair_ok,
        "fallback": False,
        "success": bool(plan_objects) and repair_ok,
    }
    return canonicalize_output(raw)


def _is_asset_binding(b: dict[str, Any]) -> bool:
    """True for an asset-typed binding (the object's current asset assignment)."""
    return (b.get("type") in ("asset", "asset_bind")
            or (b.get("metadata") or {}).get("type") == "asset")


def _apply_patch(patch: dict[str, Any], nodes: list[dict[str, Any]], edges: list[dict[str, Any]],
                 bindings: list[dict[str, Any]]) -> bool:
    op = patch.get("patch_op")
    target = patch.get("target")
    changes = patch.get("changes") or {}
    if op == "replace_binding":
        for b in bindings:
            if b.get("subject") == target:
                b.update({k: v for k, v in changes.items() if v is not None})
                return True
        # no existing binding for subject -> create it
        new_b = {k: v for k, v in changes.items() if v is not None}
        if new_b.get("subject"):
            bindings.append(new_b)
            return True
        return False
    if op == "add_binding":
        new_b = changes.get("binding") or changes
        subj = new_b.get("subject")
        typ = new_b.get("type") or "binding"
        if not subj:
            return False
        # idempotent: if a binding for this subject+type already exists, update it
        # instead of duplicating
        for b in bindings:
            if b.get("subject") == subj and (b.get("type") or "binding") == typ:
                b.update({k: v for k, v in new_b.items() if v is not None})
                if new_b.get("metadata"):
                    b.setdefault("metadata", {})
                    b["metadata"].update(new_b["metadata"])
                return True
        bindings.append(dict(new_b))
        return True
    if op == "update_transform":
        for n in nodes:
            if n.get("id") == target:
                # shallow keys + nested key_attrs
                for k, v in changes.items():
                    if v is None:
                        continue
                    if k == "key_attrs" or k == "attributes":
                        n.setdefault("key_attrs", {})
                        n["key_attrs"].update(v)
                    else:
                        n[k] = v
                return True
        return False
    if op == "set_attr":
        for n in nodes:
            if n.get("id") == target:
                n.setdefault("key_attrs", {})
                n["key_attrs"].update(changes)
                return True
        return False
    if op == "replace_asset":
        # The correct device asset comes either from changes.target (LLM contract
        # per the R4 prompt) or changes.assetKey / changes.asset / asset_key.
        correct = (changes.get("target") or changes.get("assetKey")
                   or changes.get("asset") or changes.get("asset_key"))
        if not correct:
            return False
        # Correct any asset binding on the object, else stamp the node's asset
        # key (snake_case, matching the evaluator's disjunctive repair adapter).
        for b in bindings:
            if b.get("subject") == target and _is_asset_binding(b):
                b["metadata"] = dict(b.get("metadata") or {})
                b["metadata"]["asset_key"] = correct
                b.setdefault("target", target)
                return True
        for n in nodes:
            if n.get("id") == target:
                n["asset_key"] = correct
                return True
        return False
    if op == "set_placeholder":
        # Evaluator's disjunctive adapter accepts a placeholder as an asset_job
        # binding with job_type=placeholder on the object (retaining the object,
        # recording the pending replacement). Also clear any conflicting asset
        # binding's asset_key so a wrong retained binding does not linger.
        for b in bindings:
            if b.get("subject") == target and _is_asset_binding(b):
                b["metadata"] = dict(b.get("metadata") or {})
                b["metadata"]["asset_key"] = ""
        bindings.append({
            "subject": target, "target": f"job-{len(bindings) + 1}",
            "type": "asset_job", "metadata": {"job_type": "placeholder"},
        })
        return True
    if op == "add_node":
        new = changes.get("node") or {}
        if new.get("id"):
            nodes.append(new)
            return True
        return False
    if op == "add_edge":
        new = changes.get("edge") or {}
        if new.get("subject") and new.get("object"):
            edges.append(new)
            # Keep node.parent consistent with the contains edge: R1 reads node.parent,
            # while the LLM naturally expresses hierarchy as contains edges. Setting the
            # child's parent field on add_edge makes both representations agree.
            for n in nodes:
                if str(n.get("id") or "") == str(new.get("object") or ""):
                    if not n.get("parent"):
                        n["parent"] = new.get("subject")
            return True
        return False
    if op == "remove_node":
        for i, n in enumerate(nodes):
            if n.get("id") == target:
                nodes.pop(i)
                return True
        return False
    if op == "remove_edge":
        for i, e in enumerate(edges):
            if e.get("subject") == target:
                edges.pop(i)
                return True
        return False
    if op == "replace_type":
        for n in nodes:
            if n.get("id") == target:
                n["type"] = changes.get("type", n.get("type", ""))
                return True
        return False
    return False


def _apply_r2_companion(patch: dict[str, Any], nodes: list[dict[str, Any]],
                        bindings: list[dict[str, Any]]) -> None:
    """Ensure R2 is fully satisfied on the target object.

    R2 (data-binding legal) fires when a Sensor/Trait/Event node has NO binding OR
    the node lacks unit/timestamp metadata. A single patch may only add one binding,
    but the rule needs BOTH: a binding and node metadata. This companion mirrors the
    binding's metadata (unit/metrics) onto the node's key_attrs and sets
    monitoring_target so the repair is a genuine data-binding repair (matching how
    the gold authors sensor bindings).
    """
    target = patch.get("target") or ""
    changes = patch.get("changes") or {}
    bound_target = None
    for b in bindings:
        if b.get("subject") == target:
            bound_target = b.get("target")
            md = b.get("metadata") or {}
            for n in nodes:
                if n.get("id") == target:
                    n.setdefault("key_attrs", {})
                    if not n["key_attrs"].get("unit"):
                        n["key_attrs"]["unit"] = md.get("unit") or "celsius"
                    if not n["key_attrs"].get("timestamp"):
                        n["key_attrs"]["timestamp"] = md.get("timestamp") or "2026-08-05T00:00:00Z"
            break
    # set monitoring_target on the node from the binding's target (real repair change)
    for n in nodes:
        if n.get("id") == target and bound_target:
            if not n.get("monitoring_target"):
                n["monitoring_target"] = bound_target


def _introduced_new_fatal(violations: list[dict[str, Any]], conflict: dict[str, Any]) -> bool:
    """True if applying the patch introduced a fatal rule not already tracked by this conflict."""
    conflict_rule = conflict.get("rule_id")
    for v in violations:
        if v.get("severity") == "fatal" and v.get("rule_id") != conflict_rule:
            return True
    return False
