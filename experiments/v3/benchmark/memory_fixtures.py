"""Deterministic state fixtures and Oracle for memory_query tasks (F-009).

A memory_query task supplies a *pre-existing* state (objects, timeseries,
events, daily_reports). The agent must RETRIEVE/AGGREGATE from that state and
return a grounded answer — it must NOT build the scene (that is the test_v1
defect this module fixes).

The Oracle computes `expected_answer` and `expected_evidence` deterministically
from the fixture's initial_state, so gold is derived from data, never from a
hand-picked scene-count.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

TZ = timezone(timedelta(hours=8))  # +08:00 (greenhouse locale)


# --------------------------------------------------------------------------- #
# Fixtures — each returns a full memory_query task draft (public + gold).
# The oracle-computed fields are filled by build_memory_task below.
# --------------------------------------------------------------------------- #

def _ts(iso: str) -> datetime:
    return datetime.fromisoformat(iso)


def _plant(pid: str, row: str, variety: str = "Tomato-Gin", height_cm: float = 120.0):
    return {
        "id": pid, "type": "Plant", "row": row, "variety": variety,
        "stage": "flowering", "height_cm": height_cm,
        "f2dmas_version": "v2.1.3", "created": "2026-06-01T08:00:00+08:00",
    }


def _sensor(sid: str, target: str, metric: str, unit: str):
    return {
        "id": sid, "type": "Sensor", "monitoring_target": target,
        "metric": metric, "unit": unit,
    }


def _camera(cid: str, observes: list[str], fov_deg: float = 45.0):
    return {
        "id": cid, "type": "Camera", "observes": observes, "fov": {"degrees": fov_deg},
        "pose": {"position": [1.0, 2.5, 3.0]},
    }


def _ts_record(sensor_id: str, metric: str, unit: str, t: str, value: float):
    return {"record_id": f"rec-{sensor_id}-{t[:10]}-{t[11:13]}",
            "sensor_id": sensor_id, "metric": metric, "unit": unit,
            "timestamp": t, "value": value}


def _event(event_id: str, object_id: str, event_type: str, t: str, payload: dict | None = None):
    return {"event_id": event_id, "object_id": object_id, "event_type": event_type,
            "timestamp": t, "payload": payload or {}}


def _report(report_id: str, date: str, summary: str, alerts: int = 0, water_ml: float = 0.0):
    return {"report_id": report_id, "date": date, "summary": summary,
            "alerts": alerts, "water_ml": water_ml}


# Environment telemetry for "last 7 days" style queries. Deterministic, no RNG.
def _week_environment() -> dict[str, Any]:
    start = datetime(2026, 7, 1, 0, 0, tzinfo=TZ)
    objects = [
        {"id": "greenhouse_01", "type": "Greenhouse", "location": {"x": 0, "z": 0},
         "area_m2": 1200},
        _sensor("env_sensor_01", "greenhouse_01", "temperature", "°C"),
        _sensor("env_sensor_02", "greenhouse_01", "humidity", "%"),
        _sensor("env_sensor_03", "greenhouse_01", "co2", "ppm"),
        _sensor("env_sensor_04", "greenhouse_01", "light", "klux"),
        _sensor("env_sensor_05", "greenhouse_01", "soil_moisture", "%"),
    ]
    timeseries: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    # 6 metrics x 7 days x 24 hours — keep to a daily aggregate fixture to stay
    # deterministic and compact: one record per metric per day (representative).
    metric_base = {"temperature": [22, 23, 21, 24, 22, 20, 23],
                   "humidity": [65, 66, 63, 67, 64, 62, 66],
                   "co2": [420, 415, 430, 425, 418, 432, 428],
                   "light": [38, 41, 35, 44, 39, 33, 42],
                   "soil_moisture": [58, 57, 60, 55, 59, 61, 56]}
    sensors = {"temperature": "env_sensor_01", "humidity": "env_sensor_02",
               "co2": "env_sensor_03", "light": "env_sensor_04",
               "soil_moisture": "env_sensor_05"}
    for day in range(7):
        d = start + timedelta(days=day)
        for metric, vals in metric_base.items():
            rid = f"rec-env-{metric}-{d.strftime('%Y%m%d')}"
            timeseries.append({"record_id": rid, "sensor_id": sensors[metric],
                               "metric": metric, "unit": _unit_for(metric),
                               "timestamp": d.isoformat(), "value": float(vals[day])})
    # 2 alert events over the week
    events.append(_event("evt-alert-01", "greenhouse_01", "temp_high",
                         (start + timedelta(days=2, hours=14)).isoformat(),
                         {"metric": "temperature", "value": 33.5, "threshold": 30}))
    events.append(_event("evt-alert-02", "greenhouse_01", "co2_high",
                         (start + timedelta(days=5, hours=3)).isoformat(),
                         {"metric": "co2", "value": 902, "threshold": 800}))
    return {"objects": objects, "timeseries_records": timeseries,
            "events": events, "daily_reports": []}


def _unit_for(metric: str) -> str:
    return {"temperature": "°C", "humidity": "%", "co2": "ppm",
            "light": "klux", "soil_moisture": "%"}.get(metric, "")


# --------------------------------------------------------------------------- #
# Oracle — deterministic answer computation from an initial_state.
# --------------------------------------------------------------------------- #

def oracle_environment_summary(initial_state: dict[str, Any],
                               start_iso: str, end_iso: str,
                               metrics: list[str]) -> dict[str, Any]:
    """Compute the expected answer for a 'last-N-days environment summary'.

    Returns {normalized_values, events, summary_facts, evidence} — all derived
    deterministically from initial_state.
    """
    ts = initial_state.get("timeseries_records") or []
    evs = initial_state.get("events") or []
    start = datetime.fromisoformat(start_iso)
    end = datetime.fromisoformat(end_iso)

    in_window = [r for r in ts
                 if start <= datetime.fromisoformat(str(r["timestamp"])) <= end
                 and r.get("metric") in metrics]
    by_metric: dict[str, list[float]] = {}
    unit_by_metric: dict[str, str] = {}
    for r in in_window:
        m = r["metric"]
        by_metric.setdefault(m, []).append(float(r["value"]))
        unit_by_metric[m] = r.get("unit", "")

    normalized: dict[str, dict[str, float | str]] = {}
    for m in metrics:
        vals = by_metric.get(m, [])
        if not vals:
            normalized[m] = {"count": 0}
            continue
        normalized[m] = {
            "mean": round(sum(vals) / len(vals), 2),
            "min": round(min(vals), 2),
            "max": round(max(vals), 2),
            "latest": round(vals[-1], 2),
            "unit": unit_by_metric.get(m, ""),
        }

    window_events = [e for e in evs
                     if start <= datetime.fromisoformat(str(e["timestamp"])) <= end]
    fact = (f"{len(window_events)} alert events in window "
            f"[{start_iso}, {end_iso}]")

    return {
        "normalized_values": normalized,
        "events": window_events,
        "summary_facts": [fact],
        "evidence": {
            "record_ids": [r["record_id"] for r in in_window],
            "event_ids": [e["event_id"] for e in window_events],
        },
    }


# --------------------------------------------------------------------------- #
# Task builder — assemble a full memory_query task (public + gold).
# --------------------------------------------------------------------------- #

def build_memory_task(*, task_id: str, prompt: str, initial_state: dict[str, Any],
                      query_spec: dict[str, Any],
                      forbidden_side_effects: list[str] | None = None,
                      difficulty: str = "easy",
                      annotation_version: str = "v2") -> dict[str, Any]:
    """Build a memory_query task with oracle-filled gold.

    The oracle runs over the same initial_state the agent will query, so gold is
    a deterministic function of data (not a hand-picked scene count).
    """
    metrics = query_spec.get("metrics") or []
    start_iso = query_spec.get("start_time") or ""
    end_iso = query_spec.get("end_time") or ""
    oracle = oracle_environment_summary(initial_state, start_iso, end_iso, metrics)

    expected_answer = {
        "normalized_values": oracle["normalized_values"],
        "events": oracle["events"],
        "summary_facts": oracle["summary_facts"],
    }
    expected_evidence = oracle["evidence"]

    return {
        "task_id": task_id,
        "task_type": "memory_query",
        "difficulty": difficulty,
        "prompt": prompt,
        "annotation_version": annotation_version,
        "review_status": "pending",
        "initial_state": initial_state,
        "query_spec": query_spec,
        "expected_answer": expected_answer,
        "expected_evidence": expected_evidence,
        "expected_outcome": {"answer": expected_answer, "evidence": expected_evidence},
        "fatal_constraints": [],
        "allowed_side_effects": [],
        "forbidden_side_effects": forbidden_side_effects or [
            "create_scene", "add_object", "delete_object",
            "modify_timeseries", "invent_record",
        ],
        "critical_objects": [],
        "required_nodes": [],
        "required_edges": [],
        "required_bindings": [],
        "equivalence_groups": [],
        "allowed_variants": [],
    }
