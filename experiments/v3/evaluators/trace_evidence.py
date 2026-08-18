"""Trace evidence evaluation for the semantic evaluator.

Evidence must point to REAL tool calls recorded through the shared trace proxy.
Rules:
  - declared trace steps with no real backing call -> evidence score 0
  - auto-generated evidence IDs with no real response -> NOT counted (rejected)
  - rule fallback (DeterministicFallback) is flagged separately, never counted as
    LLM / multi-agent success
  - Evidence Coverage / Precision computed over the steps

The trace proxy records entries like:
  {call_id, agent_id, tool, request, response, status, fallback?}
"""

from __future__ import annotations

from typing import Any


def evaluate_trace(*, steps: list[dict[str, Any]], proxy_calls: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Score a method's trace steps against the real recorded proxy calls.

    steps: the method's emitted trace steps (traceType declared|executed, evidenceId, tool)
    proxy_calls: the shared trace proxy's real recorded calls (call_id, tool, response)
    """
    proxy = proxy_calls or []
    proxy_by_id: dict[str, dict[str, Any]] = {}
    for c in proxy:
        cid = str(c.get("call_id") or c.get("id") or "")
        if cid:
            proxy_by_id[cid] = c

    evidence_steps = 0
    real_evidence = 0
    fabricated = 0
    declared_steps = 0
    executed_steps = 0
    fallback_steps = 0
    evidence_ids: list[str] = []

    for s in steps:
        trace_type = str(s.get("traceType") or s.get("trace_type") or "declared").lower()
        evidence_id = str(s.get("evidenceId") or s.get("evidence_id") or s.get("callId") or "").strip()
        if s.get("fallback") or str(s.get("fallbackReason") or "").strip() or str(s.get("fallback") or "").lower() in {"true", "deterministic"}:
            fallback_steps += 1
        if trace_type == "executed":
            executed_steps += 1
            if not evidence_id:
                # executed with no evidenceId -> auto-generated / unverifiable
                fabricated += 1
                continue
            if evidence_id in proxy_by_id:
                real_evidence += 1
                evidence_ids.append(evidence_id)
            else:
                fabricated += 1  # evidenceId present but no real backing response
        else:
            declared_steps += 1

    evidence_steps = real_evidence  # only real, verifiable evidence counts

    total_evidence_claims = len([s for s in steps if (s.get("evidenceId") or s.get("evidence_id"))])
    # P0-1: forbid vacuous 1.0. Before this fix, empty steps (trace chain broken)
    # returned 1.0 via the "no claims, no executed" branch — a fake perfect score.
    # If the trace is empty, evidence_precision must be 0 (no evidence provided),
    # UNLESS the task genuinely made no tool calls at all (proxy_calls also empty),
    # in which case we stay vacuously 1.0 (no evidence demanded = no penalty).
    if total_evidence_claims > 0:
        evidence_precision = real_evidence / total_evidence_claims
    elif executed_steps > 0:
        # executed steps exist but none have evidenceIds — all fabricated
        evidence_precision = 0.0
    else:
        # truly empty trace: no declared/executed steps at all
        # vacuously true only if proxy also has no calls (nothing to prove)
        evidence_precision = 1.0 if not proxy else 0.0
    evidence_coverage = executed_steps / len(steps) if steps else 0.0

    return {
        "declared_steps": declared_steps,
        "executed_steps": executed_steps,
        "evidence_steps": evidence_steps,
        "real_evidence": real_evidence,
        "fabricated_evidence": fabricated,
        "fallback_steps": fallback_steps,
        "evidence_ids": evidence_ids,
        "evidence_precision": round(evidence_precision, 4),
        "evidence_coverage": round(evidence_coverage, 4),
        # P0-1: all_evidence_real must NOT be vacuously true on an empty trace.
        # - genuinely nothing happened (empty trace + empty proxy): vacuously fine
        # - real proxy calls but empty trace (broken chain): NOT fine
        # - declared steps with no backing call: NOT fine (red flag)
        # - fabricated evidenceIds: NOT fine
        "all_evidence_real": bool(
            fabricated == 0
            and declared_steps == 0
            and (real_evidence > 0 or (not steps and not proxy))
        ),
    }


def evidence_is_real(evidence_id: str, proxy_calls: list[dict[str, Any]]) -> bool:
    proxy_by_id = {str(c.get("call_id") or c.get("id") or ""): c for c in proxy_calls}
    return evidence_id in proxy_by_id
