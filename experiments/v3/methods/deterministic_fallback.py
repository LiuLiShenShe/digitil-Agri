"""DeterministicFallback: pure rule/ontology planning (the only allowed rule-fallback method).

This is run SEPARATELY and reported separately. KAFarmTwin main results must NOT
mix in this fallback path. It mirrors the Go backend's buildRulePlan behavior.
"""

from __future__ import annotations

from typing import Any
from experiments.v3.harness.tools import ToolRegistry  # type: ignore
from experiments.v3.harness.budget import BudgetEnforcer  # type: ignore
from experiments.v3.harness.canonicalizer import canonicalize_output  # type: ignore


def run_deterministic_fallback(*, task: dict[str, Any], registry: ToolRegistry,
                               budget: BudgetEnforcer) -> dict[str, Any]:
    """Deterministically expand the task prompt's object requirements using shared knowledge."""
    prompt = task["prompt"]
    nodes: list[dict[str, Any]] = []
    # Parse known object counts from the prompt (deterministic).
    known = [
        ("番茄", "Plant"), ("草莓", "Plant"), ("玉米", "Plant"), ("生菜", "Plant"),
        ("气象站", "WeatherStation"), ("水泵", "Pump"), ("滴灌", "Irrigation"), ("微喷", "Irrigation"),
        ("摄像头", "Camera"), ("传感器", "Sensor"),
    ]
    import re
    for label, otype in known:
        m = re.search(r"(\d+)\s*[株组个套台]\s*" + label, prompt)
        count = int(m.group(1)) if m else (1 if label in prompt else 0)
        if count > 0:
            nodes.append({"id": f"{label}_{count}", "type": otype, "role": "entity", "count": count})

    # no LLM calls; pure deterministic tool pass, recorded as fallback
    if nodes:
        out = registry.call("scene.plan", {"objects": nodes}, agent_id="DeterministicFallback")
        if registry.trace_proxy is not None and out.get("_call_id"):
            registry.trace_proxy.mark_fallback(out["_call_id"])
        registry.call("layout.solve", {"objects": nodes}, agent_id="DeterministicFallback")

    raw = {
        "nodes": nodes,
        "edges": [],
        "bindings": [],
        "traceSteps": registry.trace_proxy.steps_for_trace() if registry.trace_proxy else [],
        "budget": budget.summary(),
        "fallback": "deterministic",
        "success": bool(nodes),
    }
    return canonicalize_output(raw)
