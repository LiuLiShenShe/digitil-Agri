"""Generic Multi-Agent + Shared State / Blackboard: multiple agent roles sharing one context."""

from __future__ import annotations

from typing import Any
from experiments.v3.harness.tools import ToolRegistry  # type: ignore
from experiments.v3.harness.budget import BudgetEnforcer  # type: ignore
from experiments.v3.harness.canonicalizer import canonicalize_output  # type: ignore


AGENT_ROLES = [
    ("PlannerAgent", "You are a planner. Return JSON {objects:[], relations:[], bindings:[], next_role}"),
    ("LayoutAgent",  "You are a layout planner. Return JSON {layout:[], next_role}"),
    ("AssetAgent",   "You are an asset router. Return JSON {asset_plan:[], next_role}"),
    ("BindingAgent", "You are a binding agent. Return JSON {bindings:[], next_role}"),
    ("ValidatorAgent", "You are a validator. Return JSON {valid, violations:[], done}"),
]


def run_generic_multi_agent(*, task: dict[str, Any], registry: ToolRegistry,
                            budget: BudgetEnforcer, llm_call_fn,
                            shared_state: dict[str, Any] | None = None) -> dict[str, Any]:
    """Each agent role takes one LLM call, reads/writes shared blackboard state."""
    prompt = task["prompt"]
    blackboard = shared_state if shared_state is not None else {}
    plan_objects: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []
    bindings: list[dict[str, Any]] = []

    for role, sys_prompt in AGENT_ROLES:
        if budget.llm_calls >= budget.config.max_llm_calls:
            break
        budget.assert_llm_budget()
        resp = llm_call_fn({
            "system": sys_prompt,
            "user": f"{prompt}\nBlackboard: {list(blackboard.keys())}",
        }, budget)
        budget.add_tokens(resp.get("usage", {}).get("total_tokens", 0))
        try:
            out = resp.get("content_json") or {}
        except Exception:
            out = {}
        blackboard[role] = out
        if role == "PlannerAgent":
            plan_objects = out.get("objects") or []
            plan_objects = [o if isinstance(o, dict) else {"id": str(o), "type": str(o)} for o in plan_objects]
            relations = out.get("relations") or []
        elif role == "BindingAgent":
            bindings = out.get("bindings") or []
            bindings = [b if isinstance(b, dict) else {"subject": str(b), "target": str(b)} for b in bindings]
        elif role == "LayoutAgent":
            for o in plan_objects:
                registry.call("layout.solve", {"objects": [o]}, agent_id=role)
        elif role == "ValidatorAgent":
            if out.get("done") or out.get("valid"):
                break

    # reflect solved layout onto emitted nodes (real layout, must be scored)
    from experiments.v3.harness.canonicalizer import merge_layout_into_nodes  # type: ignore
    plan_objects = merge_layout_into_nodes(plan_objects, registry.ctx.get("scene_objects") or [])

    raw = {
        "nodes": plan_objects,
        "edges": relations,
        "bindings": bindings,
        "traceSteps": registry.trace_proxy.steps_for_trace() if registry.trace_proxy else [],
        "budget": budget.summary(),
        "success": bool(plan_objects),
    }
    return canonicalize_output(raw)
