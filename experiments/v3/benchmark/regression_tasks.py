"""Regression-set fixtures for re-annotated T27-T30 (F-011).

These tasks use the new memory_query Query-Gold Schema: target objects live in
initial_state (NOT re-built by the agent), expected_answer is oracle-derived,
expected_evidence points to real record IDs. They are regression / case-study
tasks, NOT hidden test-set (test_v2 supersedes them).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from memory_fixtures import (  # noqa: F401
    _plant, _sensor, _camera, _ts_record, _event, _report, _week_environment,
    build_memory_task, oracle_environment_summary, TZ,
)


def _plant_telemetry_fixture() -> dict[str, Any]:
    """P15 plant-state fixture: plant + growth timeseries + phenology records."""
    plants = [
        {"id": "P15", "type": "Plant", "row": "Row3", "variety": "Tomato-Gin",
         "stage": "fruit_setting", "height_cm": 138.5,
         "f2dmas_version": "v2.1.3", "created": "2026-06-01T08:00:00+08:00"},
    ]
    timeseries = [
        {"record_id": "rec-P15-h-20260701", "object_id": "P15", "metric": "height_cm",
         "timestamp": "2026-07-01T08:00:00+08:00", "value": 131.2},
        {"record_id": "rec-P15-h-20260704", "object_id": "P15", "metric": "height_cm",
         "timestamp": "2026-07-04T08:00:00+08:00", "value": 135.0},
        {"record_id": "rec-P15-h-20260707", "object_id": "P15", "metric": "height_cm",
         "timestamp": "2026-07-07T08:00:00+08:00", "value": 138.5},
        {"record_id": "rec-P15-stem-20260707", "object_id": "P15", "metric": "stem_diam_mm",
         "timestamp": "2026-07-07T08:00:00+08:00", "value": 12.4},
    ]
    events = [
        {"event_id": "evt-P15-pheno-001", "object_id": "P15", "event_type": "stage_change",
         "timestamp": "2026-07-05T09:00:00+08:00",
         "payload": {"from": "flowering", "to": "fruit_setting"}},
    ]
    traits = [
        {"trait_id": "trait-P15-01", "object_id": "P15", "trait": "fruit_brix",
         "value": 4.8, "unit": "brix", "measured_at": "2026-07-06T10:00:00+08:00"},
        {"trait_id": "trait-P15-02", "object_id": "P15", "trait": "leaf_count",
         "value": 17, "unit": "count", "measured_at": "2026-07-06T10:00:00+08:00"},
    ]
    return {"objects": plants, "timeseries_records": timeseries,
            "events": events, "traits": traits, "daily_reports": []}


def _camera_coverage_fixture() -> dict[str, Any]:
    """C02 camera-coverage fixture: camera + row objects + inspection events."""
    objects = [
        _camera("C02", observes=["Row3", "Row4"], fov_deg=45.0),
        {"id": "cropRow_03", "type": "CropRow", "label": "Row 3",
         "tomato_variety": "Tomato-Gin", "plant_count": 3},
        {"id": "cropRow_04", "type": "CropRow", "label": "Row 4",
         "tomato_variety": "Tomato-Gin", "plant_count": 3},
    ]
    events = [
        {"event_id": "evt-C02-inspect-07", "object_id": "C02", "event_type": "inspection",
         "timestamp": "2026-07-06T11:00:00+08:00",
         "payload": {"coverage": ["Row3", "Row4"], "plants_detected": 6}},
    ]
    return {"objects": objects, "events": events,
            "timeseries_records": [], "daily_reports": []}


def _daily_report_fixture() -> dict[str, Any]:
    """Today's production daily report fixture: env + device + irrigation + alerts."""
    objects = [
        {"id": "greenhouse_01", "type": "Greenhouse"},
        {"id": "irrigation_01", "type": "Irrigation", "status": "active"},
        {"id": "pump_01", "type": "Pump", "status": "normal"},
    ]
    daily_reports = [
        {"report_id": "rep-2026-07-07", "date": "2026-07-07",
         "environment_summary": "temp 22-24C, humidity 65%, co2 425ppm",
         "device_status": {"irrigation_01": "active", "pump_01": "normal"},
         "irrigation_records": [{"time": "06:00", "volume_ml": 2500},
                                 {"time": "18:00", "volume_ml": 2500}],
         "alerts": 0,
         "agent_advice": "maintain watering; watch co2 overnight"},
    ]
    return {"objects": objects, "daily_reports": daily_reports,
            "timeseries_records": [], "events": []}


def build_regression_tasks() -> dict[str, dict[str, Any]]:
    """Build re-annotated T27-T30 as regression memory_query tasks (v2 gold)."""
    tasks: dict[str, dict[str, Any]] = {}

    # T27: last-7-days environment summary
    env = _week_environment()
    t27 = build_memory_task(
        task_id="T27-reg", prompt="查询番茄温室最近 7 天环境状态，汇总温度、湿度、CO2、光照、土壤水分和告警次数。",
        initial_state=env,
        query_spec={
            "target_object_ids": ["greenhouse_01"],
            "metrics": ["temperature", "humidity", "co2", "light", "soil_moisture"],
            "start_time": "2026-07-01T00:00:00+08:00",
            "end_time": "2026-07-07T23:59:59+08:00",
            "aggregations": ["mean", "min", "max", "latest"],
            "required_units": {"temperature": "°C", "humidity": "%", "co2": "ppm",
                               "light": "klux", "soil_moisture": "%"},
        },
        difficulty="easy",
    )
    t27["review_status"] = "pending"
    tasks["T27"] = t27

    # T28: plant P15 state (stage, F2DMAS version, height change, traits)
    p15 = _plant_telemetry_fixture()
    ts = p15["timeseries_records"]
    h0 = next(r["value"] for r in ts if r["metric"] == "height_cm" and "0701" in r["record_id"])
    h1 = next(r["value"] for r in ts if r["metric"] == "height_cm" and "0707" in r["record_id"])
    stage = next(o["stage"] for o in p15["objects"] if o["id"] == "P15")
    f2 = next(o["f2dmas_version"] for o in p15["objects"] if o["id"] == "P15")
    traits = p15.get("traits") or []
    t28 = build_memory_task(
        task_id="T28-reg",
        prompt="查询重点植株 P15 当前生育阶段、最近一次 F2DMAS 几何版本、株高变化和关联表型记录。",
        initial_state={k: v for k, v in p15.items() if k in
                       ("objects", "timeseries_records", "events", "traits", "daily_reports")},
        query_spec={
            "target_object_ids": ["P15"],
            "metrics": ["height_cm", "stem_diam_mm"],
            "start_time": "2026-07-01T00:00:00+08:00",
            "end_time": "2026-07-07T23:59:59+08:00",
            "aggregations": ["latest", "change"],
            "required_units": {"height_cm": "cm", "stem_diam_mm": "mm"},
        },
        difficulty="medium",
    )
    t28["expected_answer"] = {
        "normalized_values": {"height_cm": {"latest": h1, "change": round(h1 - h0, 2), "unit": "cm"},
                              "stem_diam_mm": {"latest": 12.4, "unit": "mm"}},
        "events": p15["events"],
        "summary_facts": [f"stage={stage}", f"f2dmas={f2}",
                          f"traits: {len(traits)} recorded"],
    }
    t28["expected_evidence"] = {"record_ids": [r["record_id"] for r in ts],
                                "event_ids": [e["event_id"] for e in p15["events"]]}
    t28["review_status"] = "pending"
    tasks["T28"] = t28

    # T29: camera C02 coverage + last inspection + Row-3 coverage
    cam = _camera_coverage_fixture()
    c02 = next(o for o in cam["objects"] if o["id"] == "C02")
    insp = [e for e in cam["events"] if e["event_type"] == "inspection"]
    t29 = build_memory_task(
        task_id="T29-reg",
        prompt="查询摄像头 C02 的观测覆盖对象、最近一次巡检事件和是否覆盖第 3 行番茄。",
        initial_state=cam,
        query_spec={
            "target_object_ids": ["C02"],
            "metrics": [],
            "start_time": "2026-07-01T00:00:00+08:00",
            "end_time": "2026-07-07T23:59:59+08:00",
            "aggregations": ["latest"],
            "required_units": {},
        },
        difficulty="medium",
    )
    t29["expected_answer"] = {
        "normalized_values": {},
        "events": insp,
        "summary_facts": ["observes=Row3,Row4", "covers_row3=true",
                          "covers_row4=true",
                          f"last_inspection={insp[-1]['event_id'] if insp else 'none'}"],
    }
    t29["expected_evidence"] = {"record_ids": [], "event_ids": [e["event_id"] for e in insp]}
    t29["review_status"] = "pending"
    tasks["T29"] = t29

    # T30: today's production daily report
    rep = _daily_report_fixture()
    t30 = build_memory_task(
        task_id="T30-reg",
        prompt="查询番茄温室今日生产日报，返回环境摘要、设备状态、灌溉记录、告警记录和 Agent 管理建议。",
        initial_state=rep,
        query_spec={
            "target_object_ids": ["greenhouse_01"],
            "metrics": [],
            "start_time": "2026-07-07T00:00:00+08:00",
            "end_time": "2026-07-07T23:59:59+08:00",
            "aggregations": ["latest"],
            "required_units": {},
        },
        difficulty="easy",
    )
    rep0 = rep["daily_reports"][0]
    t30["expected_answer"] = {
        "normalized_values": {},
        "events": [],
        "summary_facts": [f"env={rep0['environment_summary']}",
                          f"irrigation_01={rep0['device_status']['irrigation_01']}",
                          f"pump_01={rep0['device_status']['pump_01']}",
                          f"irrigations={len(rep0['irrigation_records'])}",
                          f"alerts={rep0['alerts']}",
                          f"advice={rep0['agent_advice']}"],
    }
    t30["expected_evidence"] = {"record_ids": [rep0["report_id"]],
                                "event_ids": []}
    t30["review_status"] = "pending"
    tasks["T30"] = t30

    return tasks


def write_regression_set(out_dir: str = "benchmark/regression") -> list[str]:
    """Write the 4 re-annotated regression tasks to benchmark/regression/."""
    from pathlib import Path
    import json
    base = Path(__file__).resolve().parents[1] / out_dir
    base.mkdir(parents=True, exist_ok=True)
    written = []
    for task in build_regression_tasks().values():
        p = base / f"{task['task_id']}.json"
        p.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(str(p))
    return written


if __name__ == "__main__":
    for p in write_regression_set():
        print("wrote", p)
