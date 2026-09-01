"""SingleAgent-DirectRepair: unconstrained LLM repair without typed operators.

For rule_repair tasks, receives the broken scene and asks the LLM to directly
output the corrected scene. No Knowledge Compiler, no typed RepairTicket,
no candidate_actions_for(), no deterministic repair executor.

This is a fair-repair baseline: same LLM, same budget, same task, but the
LLM must fix violations using its own judgment rather than selecting from
a constrained operator set.
"""

from __future__ import annotations

from typing import Any
from experiments.v3.harness.tools import ToolRegistry  # type: ignore
from experiments.v3.harness.budget import BudgetEnforcer  # type: ignore
from experiments.v3.harness.canonicalizer import canonicalize_output  # type: ignore


def run_single_agent_direct_repair(
    *, task: dict[str, Any], registry: ToolRegistry,
    budget: BudgetEnforcer, llm_call_fn, agent_id: str = "DirectRepair",
) -> dict[str, Any]:
    """One-shot LLM repair: send broken scene + instruction, get corrected scene."""
    prompt = task["prompt"]

    # Only handles rule_repair tasks; other types delegate to standard SA behavior
    task_type = task.get("task_type") or task.get("category") or ""
    if task_type not in ("rule_repair", "repair"):
        # Fallback: standard single-agent construction (no repair)
        from experiments.v3.methods.single_agent import run_single_agent
        return run_single_agent(
            task=task, registry=registry, budget=budget,
            llm_call_fn=llm_call_fn, agent_id=agent_id,
        )

    # Extract the broken scene from initial_state
    init_state = task.get("initial_state") or {}
    broken_objects = init_state.get("objects") or init_state.get("nodes") or []
    broken_edges = init_state.get("edges") or init_state.get("relations") or []
    broken_bindings = init_state.get("bindings") or []

    # Compose the direct-repair prompt
    system_msg = (
        "You are a digital-twin scene repair assistant. You will receive a broken "
        "scene with one or more rule violations. Your task is to fix ALL violations "
        "and output the corrected scene.\n\n"
        "Available repair rules:\n"
        "- R1: Object hierarchy (Greenhouse contains Plot contains CropRow contains Plant)\n"
        "- R2: Data bindings must reference existing objects with valid units/timestamps\n"
        "- R3: Spatial layout validity\n"
        "- R4: Asset type consistency — each object must have a matching asset_key\n"
        "  (e.g., Pump→irrigation, Camera→camera, Sensor→sensor)\n"
        "- R5: Camera must have pose, observation target, FOV\n"
        "- R6: Device coverage — devices must bind control zones\n"
        "- R7: Execution trace completeness\n\n"
        "Output a JSON object with: {\"objects\": [...], \"relations\": [...], \"bindings\": [...]}\n"
        "Fix the violations directly. Do NOT explain your reasoning. Return ONLY the JSON."
    )

    user_msg = (
        f"Task: {prompt}\n\n"
        f"Current (broken) scene:\n"
        f"Objects: {broken_objects}\n"
        f"Relations: {broken_edges}\n"
        f"Bindings: {broken_bindings}\n\n"
        "Fix ALL violations and return the corrected scene as JSON."
    )

    # Make one LLM call
    resp = llm_call_fn({
        "system": system_msg,
        "user": user_msg,
    }, budget)

    # Parse the response
    content_json = resp.get("content_json") or {}
    fixed_objects = content_json.get("objects") or content_json.get("nodes") or broken_objects
    fixed_edges = content_json.get("relations") or content_json.get("edges") or broken_edges
    fixed_bindings = content_json.get("bindings") or broken_bindings

    raw = {
        "nodes": fixed_objects,
        "edges": fixed_edges,
        "bindings": fixed_bindings,
        "traceSteps": registry.trace_proxy.steps_for_trace() if registry.trace_proxy else [],
        "budget": budget.summary(),
        "construction_path": "direct_repair_llm",
        "success": bool(fixed_objects),
    }
    return canonicalize_output(raw)
