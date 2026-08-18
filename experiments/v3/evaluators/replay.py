"""Replay support for the semantic evaluator.

Replay replays the recorded tool calls (from the shared trace proxy) through the
same tool functions to verify the trace is reproducible. A method's Replay
Success is the fraction of recorded real calls that can be deterministically
replayed to the same outcome.
"""

from __future__ import annotations

from typing import Any, Callable

# Tools whose output depends ONLY on the request (pure), replayable against an
# empty context. Deterministic replay verifies the recorded trace reproduces the
# same outcome — evidence that the trace is real and not fabricated.
# layout.solve / scene.plan / object.bind are NOT pure: their output depends on the
# run's full context state (seeded initial_state), so an empty-context replay cannot
# reproduce them; they are excluded from the replayable base (not penalized).
_PURE_REPLAYABLE = {"model.search", "model.metadata", "layout.validate",
                    "rule.check", "scene.current", "timeseries.query", "event.query",
                    "object.lookup", "object.relations", "asset.job.create"}


def replay_trace(*, proxy_calls: list[dict[str, Any]],
                 tool_fn: dict[str, Callable[..., Any]] | None = None) -> dict[str, Any]:
    """Replay the trace proxy's recorded calls through deterministic tool functions.

    tool_fn: map from tool name to a pure-ish callable (tool, request) -> response.
      If a tool_fn is missing for a tool, that call is marked 'not_replayable'.
    Returns replay success stats.
    """
    tool_fn = tool_fn or {}
    replayable = 0
    not_replayable = 0
    matched = 0
    mismatched = 0
    for c in proxy_calls or []:
        tool = str(c.get("tool") or c.get("toolName") or "")
        request = c.get("request") or c.get("input") or {}
        expected_response = c.get("response") or c.get("output")
        fn = tool_fn.get(tool)
        if fn is None:
            not_replayable += 1
            continue
        replayable += 1
        try:
            actual = fn(tool, request, c.get("ctx_snapshot"))
        except Exception as e:  # pragma: no cover
            mismatched += 1
            continue
        # `_call_id` is minted per-call by the trace proxy and would differ on every
        # replay; it is evidence plumbing, not tool output, so ignore it when comparing.
        actual_cmp = dict(actual or {})
        expected_cmp = dict(expected_response or {}) if isinstance(expected_response, dict) else expected_response
        if isinstance(actual_cmp, dict):
            actual_cmp.pop("_call_id", None)
        if isinstance(expected_cmp, dict):
            expected_cmp.pop("_call_id", None)
        if actual_cmp == expected_cmp or (expected_response is None):
            matched += 1
        else:
            mismatched += 1

    total = len(proxy_calls or [])
    # Replay Success only counts tools that are deterministically replayable; if a
    # trace recorded only pure tools, it should replay 100%. Calls whose tool we have
    # no pure implementation for are 'not_replayable' and excluded from the rate base.
    rate_base = replayable if replayable > 0 else 1
    return {
        "total_calls": total,
        "replayable": replayable,
        "not_replayable": not_replayable,
        "matched": matched,
        "mismatched": mismatched,
        "replay_success": round(matched / rate_base, 4),
    }


def make_replay_tool_fn() -> dict[str, Callable[..., Any]]:
    """Build a replay tool_fn from DEFAULT_TOOLS, bound to an empty ctx.

    Returns (tool, request) -> response, matching the replay_trace contract. Tools
    whose real execution mutates a shared ctx (e.g. scene.plan, object.bind) are NOT
    included, since their replay would need the exact prior ctx state; they are
    'not_replayable' (excluded from the replay-success rate, not penalized).
    """
    try:
        from experiments.v3.harness.tools import DEFAULT_TOOLS  # type: ignore
    except ImportError:
        DEFAULT_TOOLS = {}
    empty_ctx: dict[str, Any] = {"scene_plan": [], "scene_objects": [], "scene_bindings": [],
                                 "generation_jobs": [], "catalog": {}}

    def _make(tool_name: str):
        fn = DEFAULT_TOOLS.get(tool_name)

        def _replay(tool: str, request: dict[str, Any],
                    ctx_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
            ctx = dict(empty_ctx)
            ctx["scene_objects"] = list(empty_ctx["scene_objects"])
            ctx["scene_plan"] = list(empty_ctx["scene_plan"])
            ctx["scene_bindings"] = list(empty_ctx["scene_bindings"])
            # A2 (P0-5): restore the recorded memory_state snapshot so the memory
            # queries (timeseries.query / event.query) replay against the real store,
            # not an empty one. The snapshot is recorded evidence, not re-derived gold.
            mem = (ctx_snapshot or {}).get("memory_state")
            if mem:
                import copy
                ctx["memory_state"] = copy.deepcopy(mem)
            return fn(ctx, request)
        return _replay

    result: dict[str, Callable[..., Any]] = {}
    for name in _PURE_REPLAYABLE:
        if name in DEFAULT_TOOLS:
            result[name] = _make(name)
    return result
