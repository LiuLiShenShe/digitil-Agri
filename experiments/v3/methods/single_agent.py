"""Single-Agent + All Tools: one agent has all tools, one planning pass, no repair loop."""

from __future__ import annotations

from typing import Any
from experiments.v3.harness.tools import ToolRegistry  # type: ignore
from experiments.v3.harness.budget import BudgetEnforcer  # type: ignore
from experiments.v3.harness.canonicalizer import canonicalize_output  # type: ignore


def run_single_agent(*, task: dict[str, Any], registry: ToolRegistry,
                     budget: BudgetEnforcer, llm_call_fn, agent_id: str = "SingleAgent") -> dict[str, Any]:
    """Single-agent pass: plan -> layout -> validate, one shot. No repair loop."""
    prompt = task["prompt"]
    ctx = registry.ctx
    budget.assert_llm_budget()
    # ask LLM for a scene plan
    plan_response = llm_call_fn({
        "system": "You are a scene planner. Return a JSON object with {objects: [...], relations: [...], bindings: [...]}",
        "user": prompt,
    }, budget)
    budget.add_tokens(plan_response.get("usage", {}).get("total_tokens", 0))
    try:
        plan = plan_response.get("content_json") or {}
    except Exception:
        plan = {"objects": [], "relations": [], "bindings": []}

    # feed plan into tools (coerce objects to dicts; LLM may return bare strings)
    def _as_dict(o):
        if isinstance(o, dict):
            return o
        return {"id": str(o), "type": str(o), "assetKey": str(o)}

    plan["objects"] = [_as_dict(o) for o in (plan.get("objects") or [])]
    plan["bindings"] = [_as_dict(b) for b in (plan.get("bindings") or [])]
    plan["relations"] = [_as_dict(r) for r in (plan.get("relations") or [])]

    if plan.get("objects"):
        registry.call("scene.plan", {"objects": plan["objects"]}, agent_id=agent_id)
        registry.call("layout.solve", {"objects": plan["objects"]}, agent_id=agent_id)
        registry.call("layout.validate", {"layout": ctx.get("scene_objects")}, agent_id=agent_id)

    # route to Validator for asset binding
    for obj in (plan.get("objects") or []):
        ak = obj.get("assetKey") or obj.get("type") or ""
        if ak:
            registry.call("model.search", {"query": ak}, agent_id=agent_id)
        for b in (plan.get("bindings") or []):
            if b.get("subject") == obj.get("id"):
                registry.call("object.bind", b, agent_id=agent_id)

    # reflect the real solved layout in the emitted nodes (so R3 does not falsely fire)
    from experiments.v3.harness.canonicalizer import merge_layout_into_nodes  # type: ignore
    merged_nodes = merge_layout_into_nodes(plan.get("objects") or [], ctx.get("scene_objects") or [])

    raw = {
        "nodes": merged_nodes,
        "edges": plan.get("relations") or [],
        "bindings": plan.get("bindings") or [],
        "traceSteps": registry.trace_proxy.steps_for_trace() if registry.trace_proxy else [],
        "budget": budget.summary(),
        "success": True,
    }
    return canonicalize_output(raw)
