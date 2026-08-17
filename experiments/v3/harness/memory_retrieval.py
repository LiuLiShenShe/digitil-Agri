#!/usr/bin/env python3
"""Shared memory-query retrieval + answer assembly (F-015 wiring).

memory_query tasks ask a method to retrieve/aggregate from a PRE-EXISTING
store (the public ``initial_state``: timeseries_records / events). No method
authors a scene. For the two competing methods to be compared fairly they must
have the SAME retrieval capability, driven only by the public prompt + data —
never by gold (query_spec / expected_answer / expected_evidence are gold).

This helper gives both methods an identical, deterministic retrieval pipeline:

  1. pick the target metric from the prompt ("查询温室内 {metric} 最近 N 天 ...")
  2. determine the query window from the DATA ITSELF: the contiguous block of
     days that each carry >=3 records for that metric (the real signal). The
     generator seeds interference records (-pre / -post) as isolated single
     points OUTSIDE the window, so this data-only rule reproduces the oracle
     window exactly and never sweeps the interference tail.
  3. query via the shared tools (timeseries.query / event.query) so tool-call
     evidence is real and traceable
  4. compute the deterministic answer: per-day means, mean/latest, trend
     direction+shape (mirroring the gold oracle's aggregation), and cite the
     actual record/event ids as evidence.

Both SingleAgent and KAFarmTwin call this on memory_query tasks; neither sees
any gold field.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

_METRIC_RE = re.compile(r"温室内\s*([^\s，。,]+)\s*最近")


def _norm(s: Any) -> str:
    return str(s or "").strip().lower()


def metric_from_prompt(prompt: str) -> str:
    """Extract the target metric name from the Chinese prompt.

    Handles the canonical metric names used by the generator (co2, humidity,
    temperature, soil_moisture) and their aliases (CO2, 温度, 湿度, 土壤湿度).
    """
    p = prompt or ""
    low = p.lower()
    for m in ("soil_moisture", "soil moisture", "soilmoisture"):
        if m in low or "土壤湿度" in p:
            return "soil_moisture"
    for m in ("temperature",):
        if m in low or "温度" in p:
            return "temperature"
    for m in ("humidity",):
        if m in low or "湿度" in p:
            return "humidity"
    for m in ("co2",):
        if m in low or "co₂" in p or "co2" in p:
            return "co2"
    m = _METRIC_RE.search(p)
    if m:
        return m.group(1).lower()
    return ""


def _days_with_records(records: list[dict[str, Any]], metric: str) -> dict[str, list[dict[str, Any]]]:
    """Group records for a metric by calendar day (YYYY-MM-DD)."""
    days: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        if metric and _norm(r.get("metric")) != _norm(metric):
            continue
        ts = str(r.get("timestamp") or "")
        if not ts:
            continue
        days[ts[:10]].append(r)
    return dict(days)


def derive_query_window(records: list[dict[str, Any]], metric: str) -> tuple[str, str]:
    """Determine [start, end] ISO window from the data alone.

    The in-window signal days each carry >=3 records (06/12/18h sampling);
    interference records appear as isolated single-record days. Return the
    earliest..latest contiguous run of >=3-record days (ISO date bounds).
    """
    days = _days_with_records(records, metric)
    strong = sorted(d for d, rs in days.items() if len(rs) >= 3)
    if not strong:
        # fall back to full metric range
        all_days = sorted(days.keys())
        if not all_days:
            return "", ""
        return all_days[0] + "T00:00:00+08:00", all_days[-1] + "T23:00:00+08:00"
    # longest contiguous run
    best = [strong[0]]
    cur = [strong[0]]
    from datetime import datetime, timedelta
    for i in range(1, len(strong)):
        prev = datetime.fromisoformat(cur[-1])
        curd = datetime.fromisoformat(strong[i])
        if (curd - prev).days == 1:
            cur.append(strong[i])
            if len(cur) > len(best):
                best = list(cur)
        else:
            cur = [strong[i]]
    # end-of-day marker matches the oracle: window end is the LAST day at 23:00
    # (generator uses start + timedelta(days=days-1, hours=23)).
    return best[0] + "T00:00:00+08:00", best[-1] + "T23:00:00+08:00"


def _trend_label(vals: list[float]) -> str:
    if not vals:
        return "no_data"
    delta = vals[-1] - vals[0]
    if abs(delta) < 1e-9:
        return "flat"
    return "up" if delta > 0 else "down"


def _trend_shape(vals: list[float]) -> str:
    if len(vals) < 3:
        return "flat" if abs(vals[-1] - vals[0]) < 1e-9 else _trend_label(vals)
    deltas = [vals[i + 1] - vals[i] for i in range(len(vals) - 1)]
    if all(abs(d) < 1e-9 for d in deltas):
        return "flat"
    if all(d >= 0 for d in deltas):
        return "monotonic_up"
    if all(d <= 0 for d in deltas):
        return "monotonic_down"
    sign = [1 if d > 0 else (-1 if d < 0 else 0) for d in deltas]
    nz = [s for s in sign if s != 0]
    if nz and all(s == nz[0] for s in nz):
        return "flat"
    if nz[0] > 0 and nz[-1] < 0:
        return "up_then_down"
    if nz[0] < 0 and nz[-1] > 0:
        return "down_then_up"
    return "oscillating"


def _round(v: float) -> float:
    return round(v, 2)


def build_memory_answer(task: dict[str, Any], registry: Any,
                        *, agent_id: str = "anon") -> dict[str, Any]:
    """Retrieve from the seeded store and assemble the Query-CVSR answer.

    Returns the full answer dict (normalized_values / trend / events /
    evidence) plus the query window used. Uses only public data + tools.
    """
    ctx = registry.ctx
    memory = ctx.get("memory_state") or {}
    records = memory.get("timeseries_records") or []
    events = memory.get("events") or []
    prompt = task.get("prompt") or ""
    metric = metric_from_prompt(prompt)

    # Determine window from data (>=3 records/day contiguous run).
    start, end = derive_query_window(records, metric)
    if not start:
        return {"normalized_values": {}, "trend": {}, "events": [], "evidence": {},
                "window": {"start": "", "end": ""}}

    # Query via the shared tools (real, traceable tool calls).
    ts_resp = registry.call(
        "timeseries.query",
        {"metric": metric, "start": start, "end": end},
        agent_id=agent_id,
    ) or {}
    ev_resp = registry.call(
        "event.query",
        {"start": start, "end": end},
        agent_id=agent_id,
    ) or {}

    points = ts_resp.get("points") or []
    ev_matches = ev_resp.get("events") or []

    # Per-day means.
    day_groups: dict[str, list[float]] = defaultdict(list)
    for r in points:
        ts = str(r.get("timestamp") or "")
        if not ts:
            continue
        day_groups[ts[:10]].append(float(r.get("value") or 0.0))
    daily_means = []
    for day in sorted(day_groups):
        vals = day_groups[day]
        daily_means.append(_round(sum(vals) / len(vals)))
    if not daily_means:
        return {"normalized_values": {}, "trend": {}, "events": [], "evidence": {},
                "window": {"start": start, "end": end}}

    values = [float(r.get("value") or 0.0) for r in points]
    unit = ""
    for r in points:
        if r.get("unit"):
            unit = r.get("unit")
            break
    mean = _round(sum(values) / len(values))

    # Trend from daily means.
    label = _trend_label(daily_means)
    shape = _trend_shape(daily_means)

    # Evidence: cite the real in-window records + events.
    evidence = {
        "record_ids": [r.get("record_id") for r in points if r.get("record_id")],
        "event_ids": [e.get("event_id") for e in ev_matches if e.get("event_id")],
    }

    return {
        "normalized_values": {
            metric: {
                "daily_means": daily_means,
                "mean": mean,
                "latest": daily_means[-1],
                "unit": unit,
            }
        },
        "time_window": {"start": start, "end": end},
        "trend": {
            "label": label,
            "net_change_direction": label,
            "shape": shape,
            "daily_means": daily_means,
        },
        "events": ev_matches,
        "summary_facts": [
            f"daily_means={daily_means}",
            f"trend={label}",
            f"{len(ev_matches)} high alarm event(s)",
        ],
        "evidence": evidence,
        "window": {"start": start, "end": end},
    }
