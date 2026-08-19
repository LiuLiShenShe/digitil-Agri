"""Shared external Trace proxy.

All methods record their tool calls through this proxy. It captures real
agent IDs, messages, and tool calls (request + response). Evidence IDs minted
here are the ONLY verifiable evidence: an evidenceId is real only if it matches
a call recorded by this proxy.

This replaces the old behavior of auto-fabricating evidence IDs in the scorer.
"""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
import uuid
from typing import Any

# A2 (review 2026-08-18): context-dependent memory tools (timeseries.query /
# event.query) read ctx["memory_state"]; an empty-context replay returns zero.
# The fix records the memory_state the call was made against. Per the review we
# do NOT store the full snapshot in the run record (a reviewer could claim
# test-environment leakage from the run log): the trace records only
#   ctx_snapshot_id / ctx_snapshot_version / ctx_snapshot_hash,
# and the snapshot CONTENT is kept in a separate, process-local FIXTURE store
# keyed by that hash. Replay loads the fixture by hash. The content is the PUBLIC
# seeded memory_state (never gold), so no gold ever leaves the method boundary.
_FIXTURE_VERSION = "v1"
_FIXTURES: dict[str, dict[str, Any]] = {}  # snapshot sha256 -> deepcopied snapshot


def store_snapshot(snapshot: dict[str, Any]) -> tuple[str, str, str]:
    """Persist a ctx snapshot into the fixture store; return (id, version, hash).

    The run record carries only these three fields; the full content lives in the
    process-local fixture store so the trace is lean (no test-environment leakage).
    """
    try:
        s = json.dumps(snapshot, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    except Exception:
        s = repr(snapshot).encode("utf-8", "replace")
    h = hashlib.sha256(s).hexdigest()
    if h not in _FIXTURES:
        _FIXTURES[h] = copy.deepcopy(snapshot)
    return f"mem-snap-{h[:12]}", _FIXTURE_VERSION, h


def load_snapshot(snapshot_hash: str) -> dict[str, Any] | None:
    """Return the deepcopied fixture for a snapshot hash, else None."""
    snap = _FIXTURES.get(snapshot_hash)
    return copy.deepcopy(snap) if snap is not None else None


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
        # A2 (review): store ONLY the hash + version of the memory-state snapshot,
        # not the full content (trace stays lean; the fixture store holds content).
        if ctx_snapshot is not None:
            snap_id, snap_version, snap_hash = store_snapshot(ctx_snapshot)
            rec["ctx_snapshot_id"] = snap_id
            rec["ctx_snapshot_version"] = snap_version
            rec["ctx_snapshot_hash"] = snap_hash
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
