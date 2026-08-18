"""Shared external Trace proxy.

All methods record their tool calls through this proxy. It captures real
agent IDs, messages, and tool calls (request + response). Evidence IDs minted
here are the ONLY verifiable evidence: an evidenceId is real only if it matches
a call recorded by this proxy.

This replaces the old behavior of auto-fabricating evidence IDs in the scorer.
"""

from __future__ import annotations

import itertools
import uuid
from typing import Any


class TraceProxy:
    def __init__(self, *, task_id: str = "", method: str = "") -> None:
        self.task_id = task_id
        self.method = method
        self._calls: list[dict[str, Any]] = []
        self._counter = itertools.count(1)

    def record(self, *, agent_id: str, tool: str, request: dict[str, Any],
               response: dict[str, Any], caller_method: str = "",
               ctx_snapshot: dict[str, Any] | None = None) -> str:
        call_id = f"call-{next(self._counter):04d}"
        # deep-copy request/response: the trace must faithfully reflect the state AT
        # CALL TIME. In-place mutation of shared state later (e.g. add_edge setting
        # node.parent, merge_layout_into_nodes) must not retroactively rewrite a
        # recorded request, or replay would mismatch the recorded output.
        import copy
        rec = {
            "call_id": call_id,
            "task_id": self.task_id,
            "method": self.method or caller_method,
            "agent_id": agent_id,
            "tool": tool,
            "request": copy.deepcopy(request),
            "response": copy.deepcopy(response),
            "status": "ok" if "error" not in response else "error",
            "fallback": False,
        }
        # A2 (P0-5): context-dependent memory tools (timeseries.query / event.query)
        # read ctx["memory_state"]; an empty-context replay returns zero points. Record
        # the exact memory_state snapshot the call was made against so replay can
        # reproduce the real store instead of an empty one. This is recorded evidence
        # (the public initial_state/seed given to the method), not re-derived gold.
        if ctx_snapshot is not None:
            rec["ctx_snapshot"] = copy.deepcopy(ctx_snapshot)
        self._calls.append(rec)
        return call_id

    def mark_fallback(self, call_id: str) -> None:
        for c in self._calls:
            if c["call_id"] == call_id:
                c["fallback"] = True
                return

    def calls(self) -> list[dict[str, Any]]:
        return list(self._calls)

    def steps_for_trace(self) -> list[dict[str, Any]]:
        """Convert recorded calls into trace steps (all executed with real evidence)."""
        steps = []
        for c in self._calls:
            steps.append({
                "traceType": "executed",
                "evidenceId": c["call_id"],
                "agent": c["agent_id"],
                "tool": c["tool"],
                "inputSummary": str(c.get("request") or "")[:120],
                "outputSummary": str(c.get("response") or "")[:120],
                "status": c["status"],
                "fallback": c["fallback"],
            })
        return steps
