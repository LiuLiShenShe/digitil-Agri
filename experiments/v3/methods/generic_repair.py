"""GenericRepair + All Tools: multi-agent with a generic (non-typed) repair loop.

Repairs are generic: on any violation, it re-prompts a generic agent to fix and
re-validates, up to max repair rounds. It does NOT use structured conflict types.
"""

from __future__ import annotations

from typing import Any
from experiments.v3.harness.tools import ToolRegistry  # type: ignore
from experiments.v3.harness.budget import BudgetEnforcer  # type: ignore
from experiments.v3.harness.validator_api import ValidatorAPI  # type: ignore
from experiments.v3.harness.canonicalizer import canonicalize_output  # type: ignore


def run_generic_repair(*, task: dict[str, Any], registry: ToolRegistry,
                       budget: BudgetEnforcer, llm_call_fn,
                       validator: ValidatorAPI | None = None) -> dict[str, Any]:
    validator = validator or ValidatorAPI()
    prompt = task["prompt"]
    ctx = registry.ctx
    plan_objects: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []
    bindings: list[dict[str, Any]] = []

    # initial plan
    budget.assert_llm_budget()
    resp = llm_call_fn({
        "system": "You are a scene-builder. Return JSON {objects:[], relations:[], bindings:[]}",
        "user": prompt,
    }, budget)
    budget.add_tokens(resp.get("usage", {}).get("total_tokens", 0))
    try:
        plan_objects = (resp.get("content_json") or {}).get("objects") or []
        relations = (resp.get("content_json") or {}).get("relations") or []
        bindings = (resp.get("content_json") or {}).get("bindings") or []
    except Exception:
        pass

    # generic repair loop
    for round_i in range(budget.config.max_repair_rounds):
        verdict = validator.validate(nodes=plan_objects, edges=relations, bindings=bindings, task=task)
        if verdict["valid"]:
            break
        if not budget.assert_repair_budget():
            break
        budget.assert_llm_budget()
        fix = llm_call_fn({
            "system": "You are a repairer. Fix the violations. Return JSON {objects:[], relations:[], bindings:[]}",
            "user": f"Fix:\n{verdict['violations']}\nCurrent objects: {plan_objects}",
        }, budget)
        budget.add_tokens(fix.get("usage", {}).get("total_tokens", 0))
        try:
            c = fix.get("content_json") or {}
            if c.get("objects") is not None:
                plan_objects = c["objects"]
            if c.get("relations") is not None:
                relations = c["relations"]
            if c.get("bindings") is not None:
                bindings = c["bindings"]
        except Exception:
            pass

    # emit through tools so trace reflects real calls, not just description
    if plan_objects:
        registry.call("scene.plan", {"objects": plan_objects}, agent_id="GenericRepair")
        registry.call("layout.solve", {"objects": plan_objects}, agent_id="GenericRepair")
        from experiments.v3.harness.canonicalizer import merge_layout_into_nodes  # type: ignore
        plan_objects = merge_layout_into_nodes(plan_objects, ctx.get("scene_objects") or [])
    registry.call("rule.check", {"nodes": plan_objects, "edges": relations, "bindings": bindings},
                  agent_id="GenericRepair")

    raw = {
        "nodes": plan_objects,
        "edges": relations,
        "bindings": bindings,
        "traceSteps": registry.trace_proxy.steps_for_trace() if registry.trace_proxy else [],
        "budget": budget.summary(),
        "success": bool(plan_objects),
    }
    return canonicalize_output(raw)
