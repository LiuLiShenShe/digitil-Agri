"""Single-Agent + All Tools: one agent has all tools, one planning pass, no repair loop."""

from __future__ import annotations

from typing import Any
from experiments.v3.harness.tools import ToolRegistry  # type: ignore
from experiments.v3.harness.budget import BudgetEnforcer  # type: ignore
from experiments.v3.harness.canonicalizer import canonicalize_output  # type: ignore
from experiments.v3.harness.memory_retrieval import build_memory_answer  # type: ignore


def run_single_agent(*, task: dict[str, Any], registry: ToolRegistry,
                     budget: BudgetEnforcer, llm_call_fn, agent_id: str = "SingleAgent") -> dict[str, Any]:
    """Single-agent pass: plan -> layout -> validate, one shot. No repair loop."""
    prompt = task["prompt"]

    # memory_query tasks: retrieve/aggregate from the pre-existing store. This
    # uses the identical shared helper the KAFarmTwin method calls, so the two
    # methods have symmetric retrieval capability. Token/tool budget is charged
    # the same way; no scene is authored.
    if task.get("category") == "memory_query" or task.get("task_type") == "memory_query":
        # P0-6: build_memory_answer is deterministic (no LLM call); must NOT charge
        # an LLM call. Tool calls (timeseries.query/event.query) are real trace.
        answer = build_memory_answer(task, registry, agent_id=agent_id)
        raw = {
            "nodes": [],
            "edges": [],
            "bindings": [],
            "answer": answer,
            "traceSteps": registry.trace_proxy.steps_for_trace() if registry.trace_proxy else [],
            "budget": budget.summary(),
            "success": True,
        }
        return canonicalize_output(raw)

    ctx = registry.ctx
    # _strip_public derives the legacy category from task_type (rule_repair -> repair).
    # Accept both so the honesty check fires for either representation.
    if task.get("category") == "repair" or task.get("task_type") == "rule_repair":
        # Repair tasks seed from initial_state (the broken input) and expect the
        # SingleAgent to fix it; but a plain agent has no typed repair loop, so it
        # emits the (unchanged) input scene. This is honest: no repair capability.
        init_obj = ((task.get("initial_state") or {}).get("objects")) or []
        return canonicalize_output({
            "nodes": init_obj,
            "edges": [],
            "bindings": ((task.get("initial_state") or {}).get("bindings")) or [],
            "traceSteps": [],
            "budget": budget.summary(),
            "success": bool(init_obj),
        })

    # Non-repair scene/asset/bind: build the scene via the SHARED stepwise builder.
    # This splits the once-overflowing single JSON into objects/relations/bindings
    # steps, each well under the model's output cap, so asset/bind tasks are no
    # longer truncated to empty scenes. Same mechanism for both methods (fair). A
    # compact ontology hint keeps the model on controlled vocabulary without an
    # oversized system message stealing output budget.
    from experiments.v3.harness.stepwise_builder import stepwise_build_scene  # type: ignore
    from experiments.v3.harness.llm import ONTOLOGY_NOTE  # type: ignore
    built = stepwise_build_scene(
        prompt=prompt, ontology_hint=ONTOLOGY_NOTE, llm_call_fn=llm_call_fn,
        budget=budget, registry=registry, agent_id=agent_id,
    )
    plan_objects, relations, bindings = built["nodes"], built["edges"], built["bindings"]

    # route to Validator for asset binding (real tool evidence)
    for obj in plan_objects:
        ak = obj.get("assetKey") or obj.get("type") or ""
        if ak:
            registry.call("model.search", {"query": ak}, agent_id=agent_id)
    for b in bindings:
        registry.call("object.bind", b, agent_id=agent_id)

    raw = {
        "nodes": plan_objects,
        "edges": relations,
        "bindings": bindings,
        "traceSteps": registry.trace_proxy.steps_for_trace() if registry.trace_proxy else [],
        "budget": budget.summary(),
        "success": bool(plan_objects),
    }
    return canonicalize_output(raw)
