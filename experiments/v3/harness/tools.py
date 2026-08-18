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


def _memory_records(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    """Timeseries records from the seeded memory state (memory_query tasks)."""
    return ctx.get("memory_state") and (ctx.get("memory_state").get("timeseries_records") or []) or []


def _memory_events(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    return ctx.get("memory_state") and (ctx.get("memory_state").get("events") or []) or []


def _iso_in_range(ts_iso: str, start_iso: str | None, end_iso: str | None) -> bool:
    if start_iso and ts_iso < start_iso:
        return False
    if end_iso and ts_iso > end_iso:
        return False
    return True


def tool_timeseries_query(ctx: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Read-only retrieval over the seeded memory timeseries.

    Filters by metric / objectId / (start,end) range and returns the matching
    points plus deterministic aggregates (mean/min/max/latest) over that window.
    The aggregation mirrors the memory Oracle so a method that retrieves the
    correct window reproduces the gold's expected_answer exactly.
    """
    metric = request.get("metric")
    obj = request.get("objectId") or request.get("object_id")
    start = request.get("start") or request.get("start_time")
    end = request.get("end") or request.get("end_time")
    records = _memory_records(ctx)
    matches = []
    for r in records:
        if metric and r.get("metric") != metric:
            continue
        if obj and not (r.get("object_id") == obj or r.get("sensor_id") == obj or r.get("target_id") == obj):
            continue
        ts = str(r.get("timestamp") or "")
        if not _iso_in_range(ts, start, end):
            continue
        matches.append(r)
    matches.sort(key=lambda r: str(r.get("timestamp") or ""))
    values = [float(r["value"]) for r in matches if r.get("value") is not None]
    aggs: dict[str, float | str] = {}
    if values:
        aggs = {
            "mean": round(sum(values) / len(values), 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "latest": round(values[-1], 2),
        }
    unit = ""
    if matches:
        unit = matches[-1].get("unit") or ""
    return {
        "objectId": request.get("objectId"),
        "metric": metric,
        "range": {"start": start, "end": end},
        "points": matches,
        "count": len(matches),
        "aggregates": aggs,
        "unit": unit,
    }


def tool_event_query(ctx: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Read-only retrieval over the seeded memory events (memory_query tasks)."""
    etype = request.get("eventType") or request.get("event_type")
    obj = request.get("objectId") or request.get("object_id")
    start = request.get("start") or request.get("start_time")
    end = request.get("end") or request.get("end_time")
    events = _memory_events(ctx)
    matches = []
    for e in events:
        if etype and e.get("event_type") != etype:
            continue
        if obj and not (e.get("object_id") == obj or e.get("target_id") == obj):
            continue
        ts = str(e.get("timestamp") or "")
        if not _iso_in_range(ts, start, end):
            continue
        matches.append(e)
    matches.sort(key=lambda e: str(e.get("timestamp") or ""))
    return {
        "objectId": request.get("objectId"),
        "eventType": etype,
        "range": {"start": start, "end": end},
        "events": matches,
        "count": len(matches),
    }


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
            # A2 (P0-5): memory tools are context-dependent (they read ctx["memory_state"]).
            # Capture a snapshot so replay reproduces the real store, not an empty one.
            import copy
            ctx_snapshot = None
            if tool in ("timeseries.query", "event.query") and self.ctx.get("memory_state"):
                ctx_snapshot = {"memory_state": copy.deepcopy(self.ctx.get("memory_state"))}
            call_id = self.trace_proxy.record(agent_id=agent_id, tool=tool, request=request, response=response,
                                              caller_method=caller_method, ctx_snapshot=ctx_snapshot)
            response["_call_id"] = call_id
        return response