"""Shared ToolRegistry + budget-shared tool calls for all methods.

Every method in the fair-baseline experiment uses this same ToolRegistry, so the
tools, knowledge, and budget are identical. The registry goes through the shared
TraceProxy (so every real call is recorded) and is gated by the BudgetEnforcer.
"""

from __future__ import annotations

from typing import Any, Callable


def tool_scene_current(ctx: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Read-only: return the current scene state."""
    return {"scene_id": ctx.get("scene_id"), "state": ctx.get("scene_state")}


def _as_dict(o: Any) -> dict[str, Any]:
    """Coerce an object into a dict (handle LLM returning a bare string/scalar)."""
    if isinstance(o, dict):
        return o
    return {"id": str(o), "type": str(o)}


def tool_scene_plan(ctx: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Controlled-write: set the scene plan."""
    plan = request.get("plan") or request.get("objects")
    plan = [_as_dict(o) for o in plan] if isinstance(plan, list) else plan
    ctx["scene_plan"] = plan
    return {"plan": plan, "count": len(plan) if isinstance(plan, list) else 0}


def tool_layout_solve(ctx: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Controlled-write: solve layout for the plan."""
    objects = request.get("objects") or ctx.get("scene_plan") or []
    layout = []
    for i, o in enumerate(objects):
        oid = _as_dict(o).get("id")
        layout.append({"id": oid, "location": {"x": i, "z": i % 4}})
    ctx["scene_objects"] = layout
    return {"layout": layout}


def tool_layout_validate(ctx: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Read/validate: check layout bounds."""
    layout = request.get("layout") or ctx.get("scene_objects") or []
    issues = []
    for o in layout:
        loc = o.get("location") or {}
        if loc.get("z", 0) > 8:
            issues.append({"object": o.get("id"), "issue": "out_of_bounds"})
    return {"valid": not issues, "issues": issues}


def tool_model_search(ctx: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Read-only: search asset models by query."""
    q = (request.get("query") or "").lower()
    catalog = ctx.get("catalog") or {}
    results = [v for k, v in catalog.items() if q in k.lower() or q in str(v).lower()]
    return {"results": results[:5]}


def tool_model_metadata(ctx: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    return {"assetKey": request.get("assetKey"), "metadata": ctx.get("catalog", {}).get(request.get("assetKey"), {})}


def tool_asset_job_create(ctx: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    job = {"jobId": f"job-{len(ctx.get('generation_jobs', [])) + 1}", "assetKey": request.get("assetKey"),
           "policy": request.get("policy", "TRELLIS.2")}
    ctx.setdefault("generation_jobs", []).append(job)
    return {"job": job}


def tool_object_lookup(ctx: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    oid = request.get("objectId") or request.get("id")
    objs = ctx.get("scene_objects") or []
    for o in objs:
        if o.get("id") == oid:
            return {"object": o}
    return {"object": None}


def tool_object_relations(ctx: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    oid = request.get("objectId")
    return {"relations": [r for r in ctx.get("scene_relations", []) if r.get("subject") == oid]}


def tool_object_bind(ctx: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    binding = {"subject": request.get("subject"), "target": request.get("target"),
               "type": request.get("type", "binding")}
    ctx.setdefault("scene_bindings", []).append(binding)
    return {"binding": binding}


def tool_timeseries_query(ctx: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    return {"objectId": request.get("objectId"), "metric": request.get("metric"),
            "range": request.get("range"), "points": []}


def tool_event_query(ctx: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    return {"objectId": request.get("objectId"), "eventType": request.get("eventType"),
            "range": request.get("range"), "events": []}


def tool_rule_check(ctx: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """External Validator API wrapper (aligned with rule_engine.py)."""
    from experiments.v3.evaluators.rule_engine import RuleEngine  # type: ignore
    engine = RuleEngine()
    violations = engine.evaluate(
        nodes=request.get("nodes") or [], edges=request.get("edges") or [],
        bindings=request.get("bindings") or [], active_rules=request.get("rules") or ["R1", "R2", "R3", "R4", "R5", "R6", "R7"],
    )
    return {"violations": [v.to_dict() for v in violations]}


DEFAULT_TOOLS: dict[str, Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]] = {
    "scene.current": tool_scene_current,
    "scene.plan": tool_scene_plan,
    "layout.solve": tool_layout_solve,
    "layout.validate": tool_layout_validate,
    "model.search": tool_model_search,
    "model.metadata": tool_model_metadata,
    "asset.job.create": tool_asset_job_create,
    "object.lookup": tool_object_lookup,
    "object.relations": tool_object_relations,
    "object.bind": tool_object_bind,
    "timeseries.query": tool_timeseries_query,
    "event.query": tool_event_query,
    "rule.check": tool_rule_check,
}


class ToolRegistry:
    """Shared tool registry. All methods call through this, wrapped by trace + budget."""

    def __init__(self, ctx: dict[str, Any], tools: dict[str, Callable] | None = None,
                 trace_proxy: Any = None, budget: Any = None) -> None:
        self.ctx = ctx
        self.tools = dict(DEFAULT_TOOLS)
        if tools:
            self.tools.update(tools)
        self.trace_proxy = trace_proxy
        self.budget = budget

    def list_tools(self) -> list[str]:
        return sorted(self.tools)

    def call(self, tool: str, request: dict[str, Any], *, agent_id: str = "anon", caller_method: str = "") -> dict[str, Any]:
        """Run a tool through trace + budget. Returns the response and records the call."""
        if tool not in self.tools:
            return {"error": f"unknown tool {tool}"}
        if self.budget is not None:
            self.budget.assert_tool_budget(tool)
        # execute (this is the real tool implementation)
        response = self.tools[tool](self.ctx, request)
        # record through the shared trace proxy
        if self.trace_proxy is not None:
            call_id = self.trace_proxy.record(agent_id=agent_id, tool=tool, request=request, response=response,
                                              caller_method=caller_method)
            response["_call_id"] = call_id
        return response