"""ReAct + All Tools: thought/act interleaved, still a single agent."""

from __future__ import annotations

from typing import Any
from experiments.v3.harness.tools import ToolRegistry  # type: ignore
from experiments.v3.harness.budget import BudgetEnforcer  # type: ignore
from experiments.v3.harness.canonicalizer import canonicalize_output  # type: ignore


def run_react(*, task: dict[str, Any], registry: ToolRegistry,
              budget: BudgetEnforcer, llm_call_fn, agent_id: str = "ReActAgent") -> dict[str, Any]:
    """ReAct loop: repeat {think -> act (call a tool) -> observe} until done or budget."""
    prompt = task["prompt"]
    ctx = registry.ctx
    steps: list[str] = []
    plan_objects: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []
    bindings: list[dict[str, Any]] = []
    max_react = budget.config.max_llm_calls // 3

    for i in range(max_react):
        # P0-6: accounting (assert_llm/tokens/cost) is in make_llm_call_fn; not here.
        resp = llm_call_fn({
            "system": "You are a ReAct agent. Return JSON {thought, action: {name, args}, done}",
            "user": f"{prompt}\nSo far: {steps[-2:] if steps else 'nothing'}",
        }, budget)
        try:
            act = resp.get("content_json") or {}
        except Exception:
            act = {"done": True}
        if act.get("done"):
            break
        action = act.get("action") or {}
        tool = action.get("name")
        args = action.get("args") or {}
        if tool and tool in registry.list_tools():
            out = registry.call(tool, args, agent_id=agent_id)
            steps.append(f"{tool}:{out}")
            # accumulate plan/bindings from tool outputs
            if tool == "scene.plan" and args.get("objects"):
                plan_objects = args["objects"]
            if tool == "object.bind":
                bindings.append(args)
        elif tool:
            # unknown tool -> just note
            steps.append(f"{tool}:noop")
        # derive relations from plan
    # build relations from plan objects
    for o in plan_objects:
        relations.append({"subject": "root", "predicate": "contains", "object": o.get("id", "")})

    # ensure a real layout.solve ran and is reflected in the emitted nodes (R3 honesty)
    if plan_objects:
        registry.call("layout.solve", {"objects": plan_objects}, agent_id=agent_id)
        from experiments.v3.harness.canonicalizer import merge_layout_into_nodes  # type: ignore
        plan_objects = merge_layout_into_nodes(plan_objects, ctx.get("scene_objects") or [])

    raw = {
        "nodes": plan_objects,
        "edges": relations,
        "bindings": bindings,
        "traceSteps": registry.trace_proxy.steps_for_trace() if registry.trace_proxy else [],
        "budget": budget.summary(),
        "success": bool(plan_objects),
    }
    return canonicalize_output(raw)
