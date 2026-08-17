"""test_v2 candidate task generator (F-014).

Builds a frozen test set with per-type coverage and non-colliding object names
relative to train/dev. test_v2 is emitted as a CANDIDATE set (review_status
pending/full) — it is frozen (SHA-256 sealed) only after it passes the Gold
audit and (for the final gate) human approval.

Coverage targets (per spec):
  total >= 20
  per class >= 4 (scene_construction, asset_routing, data_binding, rule_repair, memory_query)
  memory_query >= 4
  rule_repair >= 4

Object-name policy: every test_v2 object id is prefixed with the task id to
guarantee no collision with train/dev ids (e.g. 'N01_pepper_gh_root').
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from memory_fixtures import build_memory_task, TZ
from datetime import datetime, timedelta

BASE = Path(__file__).resolve().parents[1] / "benchmark"
OUT = BASE / "test_v2"


# --------------------------------------------------------------------------- #
# Per-type task builders (all use distinct N0x object prefixes).
# --------------------------------------------------------------------------- #

def _scene_task(n: str) -> dict[str, Any]:
    # A different greenhouse crop per task to vary gold.
    crops = {
        "N01": {"crop": "Lettuce", "rows": 2, "plants": 12},
        "N02": {"crop": "Strawberry", "rows": 3, "plants": 24},
        "N03": {"crop": "Bell-Pepper", "rows": 3, "plants": 21},
        "N04": {"crop": "Eggplant", "rows": 2, "plants": 10},
    }[n]
    name = crops["crop"].replace("-", "_").lower()
    root = f"{n}_{name}_gh"
    row = f"{n}_{name}_row"
    plant = f"{n}_{name}_plant"
    ws = f"{n}_{name}_ws"
    cam1 = f"{n}_{name}_cam1"
    cam2 = f"{n}_{name}_cam2"
    return {
        "task_id": f"T{n}-v2-scene",
        "task_type": "scene_construction",
        "difficulty": "medium",
        "prompt": (f"构建一个 {name} 温室，包含 {crops['rows']} 行作物、{crops['plants']} 株{name}、"
                   f"1 个气象站和 2 个摄像头，气象站和摄像头必须位于温室内部。"),
        "annotation_version": "v2",
        "review_status": "pending",
        "initial_state": {},
        "query_spec": None,
        "expected_answer": None,
        "expected_evidence": None,
        # REQUIRED_NODES = full set: Greenhouse + rows + plants + WS + 2 cameras.
        # Rows/plants are repeated instances -> equivalence groups make them
        # semantically matchable (count/type based), not exact-ID matched.
        "expected_outcome": {"graph": {"required_nodes": [
            {"id": root, "type": "Greenhouse", "role": "root", "count": 1,
             "key_attrs": {"size": "20x6m", "location": {"x": 0, "z": 0}}},
            {"id": row, "type": "CropRow", "role": "entity", "count": crops["rows"],
             "parent": root, "key_attrs": {"location": {"x": 2, "z": 1}}},
            {"id": plant, "type": "Plant", "role": "entity", "count": crops["plants"],
             "parent": row, "key_attrs": {"belongs_to": row, "location": {"x": 3, "z": 2}}},
            {"id": ws, "type": "WeatherStation", "role": "entity", "count": 1,
             "parent": root, "key_attrs": {"location": {"x": 1, "z": 1}}},
            {"id": cam1, "type": "Camera", "role": "entity", "count": 1,
             "parent": root, "key_attrs": {"observes": row, "location": {"x": 1, "z": 2}}},
            {"id": cam2, "type": "Camera", "role": "entity", "count": 1,
             "parent": root, "key_attrs": {"observes": row, "location": {"x": 5, "z": 2}}},
        ]}},
        "graph_outcome": {"required_nodes": [
            {"id": root, "type": "Greenhouse", "role": "root", "count": 1},
            {"id": row, "type": "CropRow", "role": "entity", "count": crops["rows"], "parent": root},
            {"id": plant, "type": "Plant", "role": "entity", "count": crops["plants"], "parent": row},
            {"id": ws, "type": "WeatherStation", "role": "entity", "count": 1, "parent": root},
            {"id": cam1, "type": "Camera", "role": "entity", "count": 1, "parent": root,
             "key_attrs": {"observes": row}},
            {"id": cam2, "type": "Camera", "role": "entity", "count": 1, "parent": root,
             "key_attrs": {"observes": row}},
        ]},
        "required_nodes": [
            {"id": root, "type": "Greenhouse", "role": "root", "count": 1},
            {"id": row, "type": "CropRow", "role": "entity", "count": crops["rows"], "parent": root},
            {"id": plant, "type": "Plant", "role": "entity", "count": crops["plants"], "parent": row},
            {"id": ws, "type": "WeatherStation", "role": "entity", "count": 1, "parent": root},
            {"id": cam1, "type": "Camera", "role": "entity", "count": 1, "parent": root,
             "key_attrs": {"observes": row}},
            {"id": cam2, "type": "Camera", "role": "entity", "count": 1, "parent": root,
             "key_attrs": {"observes": row}},
        ],
        "required_edges": [
            {"subject": root, "predicate": "contains", "object": row},
            {"subject": row, "predicate": "contains", "object": plant},
            {"subject": root, "predicate": "contains", "object": ws},
            {"subject": root, "predicate": "contains", "object": cam1},
            {"subject": root, "predicate": "contains", "object": cam2},
        ],
        "required_bindings": [],
        "critical_objects": [],
        "forbidden_side_effects": ["omit_required_plant", "wrong_parent",
                                   "omit_weather_station", "omit_camera"],
        "fatal_constraints": [
            "weather_station_and_cameras_must_be_present",
            "camera_must_have_observes_target",
        ],
        "allowed_side_effects": [],
        "equivalence_groups": [
            {"group_id": f"{n}_rows", "match_on": "type", "members_pattern": f"^{row}",
             "members": [row], "expected_count": crops["rows"]},
            {"group_id": f"{n}_plants", "match_on": "type", "members_pattern": f"^{plant}",
             "members": [plant], "expected_count": crops["plants"]},
            {"group_id": f"{n}_cameras", "match_on": "role", "members": [cam1, cam2],
             "expected_count": 2},
        ],
        "allowed_variants": [],
    }


def _asset_task(n: str) -> dict[str, Any]:
    crops = {"N11": ("Mango", 4, 16), "N12": ("Guava", 5, 15), "N13": ("Lychee", 6, 18), "N14": ("Papaya", 3, 12)}[n]
    crop, focus, bg = crops
    name = crop.lower()
    root = f"{n}_{name}_gh"
    row = f"{n}_{name}_row"
    focus_p = f"{n}_{name}_focus"
    bg_p = f"{n}_{name}_bg"
    light_dev = f"{n}_{name}_light"
    place_asset = f"{n}_{name}_light_placeholder"
    place_job = f"{n}_{name}_light_job"
    return {
        "task_id": f"T{n}-v2-asset",
        "task_type": "asset_routing",
        "difficulty": "medium",
        "prompt": (f"构建{name}温室，{focus} 株重点植株使用高保真资产，{bg} 株背景植株使用轻量 GLB。"
                   f"温室缺少补光设备，需生成一个占位任务用于后续补光设备资产。"),
        "annotation_version": "v2",
        "review_status": "pending",
        "initial_state": {},
        "query_spec": None, "expected_answer": None, "expected_evidence": None,
        # REQUIRED: greenhouse + row + focus(hif-fi) + bg(lightweight) + light device
        # placeholder + asset-generation job. Missing light -> placeholder is gradable.
        "expected_outcome": {"graph": {"required_nodes": [
            {"id": root, "type": "Greenhouse", "role": "root", "count": 1},
            {"id": row, "type": "CropRow", "role": "entity", "count": 1, "parent": root},
            {"id": focus_p, "type": "Plant", "role": "entity", "count": focus,
             "parent": row, "key_attrs": {"asset_policy": "high_fidelity"}},
            {"id": bg_p, "type": "Plant", "role": "entity", "count": bg,
             "parent": row, "key_attrs": {"asset_policy": "lightweight_glb"}},
            {"id": light_dev, "type": "Device", "role": "entity", "count": 1,
             "parent": root, "key_attrs": {"device_type": "supplemental_light",
                                            "asset_state": "placeholder"}},
        ]}},
        "graph_outcome": {"required_nodes": [
            {"id": root, "type": "Greenhouse", "role": "root", "count": 1},
            {"id": row, "type": "CropRow", "role": "entity", "count": 1, "parent": root},
            {"id": focus_p, "type": "Plant", "role": "entity", "count": focus,
             "parent": row, "key_attrs": {"asset_policy": "high_fidelity"}},
            {"id": bg_p, "type": "Plant", "role": "entity", "count": bg,
             "parent": row, "key_attrs": {"asset_policy": "lightweight_glb"}},
            {"id": light_dev, "type": "Device", "role": "entity", "count": 1,
             "parent": root, "key_attrs": {"device_type": "supplemental_light",
                                            "asset_state": "placeholder"}},
        ]},
        "required_nodes": [
            {"id": root, "type": "Greenhouse", "role": "root", "count": 1},
            {"id": row, "type": "CropRow", "role": "entity", "count": 1, "parent": root},
            {"id": focus_p, "type": "Plant", "role": "entity", "count": focus,
             "parent": row, "key_attrs": {"asset_policy": "high_fidelity"}},
            {"id": bg_p, "type": "Plant", "role": "entity", "count": bg,
             "parent": row, "key_attrs": {"asset_policy": "lightweight_glb"}},
            {"id": light_dev, "type": "Device", "role": "entity", "count": 1,
             "parent": root, "key_attrs": {"device_type": "supplemental_light",
                                            "asset_state": "placeholder"}},
        ],
        "required_edges": [
            {"subject": root, "predicate": "contains", "object": row},
            {"subject": row, "predicate": "contains", "object": focus_p},
            {"subject": row, "predicate": "contains", "object": bg_p},
            {"subject": root, "predicate": "contains", "object": light_dev},
        ],
        "required_bindings": [
            {"subject": focus_p, "target": f"{n}_{name}_focus_asset", "type": "asset",
             "metadata": {"asset_key": f"{name}_focus", "policy": "high_fidelity"}},
            {"subject": bg_p, "target": f"{n}_{name}_bg_asset", "type": "asset",
             "metadata": {"asset_key": f"{name}_bg", "policy": "lightweight_glb"}},
            {"subject": light_dev, "target": place_asset, "type": "asset_job",
             "metadata": {"job_type": "placeholder", "policy": "procedural_model",
                          "reason": "missing_supplemental_light"}},
        ],
        "critical_objects": [light_dev],
        "forbidden_side_effects": ["all_low_fidelity",
                                   "skip_placeholder_for_missing_light",
                                   "silent_omit_supplemental_light"],
        "fatal_constraints": [
            "missing_supplemental_light_must_generate_placeholder",
            "focus_plants_must_be_high_fidelity",
            "background_plants_must_be_lightweight_glb",
        ],
        "allowed_side_effects": ["set_placeholder", "create_asset_job"],
        "equivalence_groups": [
            {"group_id": f"{n}_focus", "match_on": "key_attrs",
             "members": [focus_p], "expected_count": focus},
            {"group_id": f"{n}_bg", "match_on": "key_attrs",
             "members": [bg_p], "expected_count": bg},
        ],
        "allowed_variants": [],
    }


def _bind_task(n: str) -> dict[str, Any]:
    specs = {
        "N21": ("Kiwi", "humidity", "%", 2),
        "N22": ("Fig", "temperature", "°C", 3),
        "N23": ("Plum", "light", "klux", 2),
        "N24": ("Pear", "co2", "ppm", 3),
    }[n]
    crop, metric, unit, n_sensors = specs
    name = crop.lower()
    root = f"{n}_{name}_gh"
    row = f"{n}_{name}_row"
    sensors = [f"{n}_{name}_sen{i}" for i in range(1, n_sensors + 1)]
    plant = f"{n}_{name}_plant"
    # Explicit prompt so the gold's trait/timestamp are observable, not arbitrary:
    # one key plant, trait=growth_stage, timestamp is part of the task's fixed clock.
    trait = "growth_stage"
    ts = "2026-09-01T00:00:00+08:00"
    return {
        "task_id": f"T{n}-v2-bind",
        "task_type": "data_binding",
        "difficulty": "medium",
        "prompt": (f"将温室内 {n_sensors} 个{metric}传感器绑定到对应作物行。"
                   f"为 1 株关键{name}植株绑定特征属性 {trait}（单位 text，时间戳 {ts}）。"),
        "annotation_version": "v2",
        "review_status": "pending",
        "initial_state": {
            "objects": [
                {"id": root, "type": "Greenhouse"},
                {"id": row, "type": "CropRow"},
                *[{"id": s, "type": "Sensor", "metric": metric, "unit": unit} for s in sensors],
                {"id": plant, "type": "Plant", "key_attrs": {"is_key": True}},
            ],
            "relations": [
                {"subject": root, "predicate": "contains", "object": row},
                {"subject": row, "predicate": "contains", "object": plant},
                *[{"subject": row, "predicate": "contains", "object": s} for s in sensors],
            ],
        },
        "query_spec": None, "expected_answer": None, "expected_evidence": None,
        "expected_outcome": {"graph": {"required_nodes": [
            {"id": root, "type": "Greenhouse", "role": "root", "count": 1},
            {"id": row, "type": "CropRow", "role": "entity", "count": 1, "parent": root},
            *[{"id": s, "type": "Sensor", "role": "entity", "count": 1, "parent": row,
               "key_attrs": {"monitoring_target": row}} for s in sensors],
            {"id": plant, "type": "Plant", "role": "entity", "count": 1, "parent": row},
        ]}},
        "required_nodes": [
            {"id": root, "type": "Greenhouse", "role": "root", "count": 1},
            {"id": row, "type": "CropRow", "role": "entity", "count": 1, "parent": root},
            *[{"id": s, "type": "Sensor", "role": "entity", "count": 1, "parent": row} for s in sensors],
            {"id": plant, "type": "Plant", "role": "entity", "count": 1, "parent": row},
        ],
        "required_edges": [
            {"subject": root, "predicate": "contains", "object": row},
            {"subject": row, "predicate": "contains", "object": plant},
            *[{"subject": row, "predicate": "contains", "object": s} for s in sensors],
        ],
        "required_bindings": [
            *[{"subject": s, "target": row, "type": "sensor_bind",
               "metadata": {"metrics": [metric], "unit": unit,
                            "timestamp": ts}} for s in sensors],
            {"subject": plant, "target": plant, "type": "trait_bind",
             "metadata": {"trait": trait, "unit": "text", "timestamp": ts}},
        ],
        "critical_objects": [plant],
        "forbidden_side_effects": ["missing_unit", "missing_timestamp",
                                   "wrong_monitoring_target", "invent_trait"],
        "fatal_constraints": [
            "sensor_bind_must_have_unit_and_timestamp",
            "key_plant_trait_must_be_growth_stage",
        ],
        "allowed_side_effects": [],
        "equivalence_groups": [
            {"group_id": f"{n}_sensors", "match_on": "type", "members": [*sensors],
             "expected_count": n_sensors},
            {"group_id": f"{n}_plants", "match_on": "id", "members": [plant],
             "expected_count": 1},
            {"group_id": f"{n}_rows", "match_on": "id", "members": [row],
             "expected_count": 1},
        ],
        "allowed_variants": [],
    }


def _repair_task(n: str) -> dict[str, Any]:
    specs = {
        "N31": ("Pump", "lemongrass"),
        "N32": ("Camera", "soy"),
        "N33": ("Irrigation", "alfalfa"),
        "N34": ("Pump", "oregano"),
    }[n]
    obj_type, wrong_tie = specs
    obj = f"{n}_WaterPump_B" if obj_type == "Pump" else f"{n}_Asset_B"
    root = f"{n}_gh_root"
    row = f"{n}_row"
    # Target asset class is device-type-derived, NOT crop-derived: a Pump /
    # Irrigation object repairs to irrigation asset; a Camera repairs to a
    # camera asset. Crop name is only context in the prompt, not the target.
    device_asset = {
        "Pump": "irrigation",
        "Irrigation": "irrigation",
        "Camera": "camera",
    }[obj_type]
    return {
        "task_id": f"T{n}-v2-repair",
        "task_type": "rule_repair",
        "difficulty": "hard",
        "prompt": (f"输入一个{obj_type} {obj} 错误关联到{wrong_tie}植物的场景。"
                   f"识别资产类型不匹配并修复：{obj} 的资产应为 {device_asset} 类"
                   f"（若无法直接替换则生成占位任务）。作物类别不影响目标资产类别。"),
        "annotation_version": "v2",
        "review_status": "pending",
        # Concrete erroneous binding: the object carries asset_key = the wrong
        # crop tie; goal_state requires asset_key corrected to the device asset.
        "initial_state": {"objects": [
            {"id": root, "type": "Greenhouse"},
            {"id": obj, "type": obj_type,
             "asset_key": wrong_tie,
             "asset_binding": {"type": "asset", "asset_key": wrong_tie}},
            {"id": row, "type": "CropRow"},
        ]},
        "goal_state": {"objects": [
            {"id": root, "type": "Greenhouse"},
            {"id": obj, "type": obj_type,
             "asset_key": device_asset,
             "asset_binding": {"type": "asset", "asset_key": device_asset}},
            {"id": row, "type": "CropRow"},
        ]},
        "query_spec": None, "expected_answer": None, "expected_evidence": None,
        "expected_outcome": {"graph": {
            "required_nodes": [
                {"id": root, "type": "Greenhouse", "role": "root", "count": 1},
                {"id": obj, "type": obj_type, "role": "entity", "count": 1, "parent": root,
                 "key_attrs": {"asset_key": device_asset}},
                {"id": row, "type": "CropRow", "role": "entity", "count": 1, "parent": root},
            ],
            "required_bindings": [
                {"subject": obj, "target": obj, "type": "asset",
                 "metadata": {"asset_key": device_asset, "fixed": True}},
            ],
        }},
        "required_nodes": [
            {"id": root, "type": "Greenhouse", "role": "root", "count": 1},
            {"id": obj, "type": obj_type, "role": "entity", "count": 1, "parent": root,
             "key_attrs": {"asset_key": device_asset}},
            {"id": row, "type": "CropRow", "role": "entity", "count": 1, "parent": root},
        ],
        "required_edges": [
            {"subject": root, "predicate": "contains", "object": row},
            {"subject": root, "predicate": "contains", "object": obj},
        ],
        "required_bindings": [
            {"subject": obj, "target": obj, "type": "asset",
             "metadata": {"asset_key": device_asset, "fixed": True}},
        ],
        "critical_objects": [obj],
        "forbidden_side_effects": ["noop_repair", "keep_asset_mismatch",
                                   "regenerate_whole_scene"],
        "fatal_constraints": [
            "asset_type_mismatch_must_be_fixed",
            "critical_object_must_be_actually_modified",
        ],
        "allowed_side_effects": ["replace_asset", "set_placeholder"],
        "equivalence_groups": [],
        "allowed_variants": [            {"path": "replace_asset", "detail": "set obj.asset_key to device_asset"},
            {"path": "set_placeholder", "detail": "keep asset mismatch + create placeholder asset_job"},
        ],
    }


def _memory_task(n: str, metric: str, days: int, unit: str) -> dict[str, Any]:
    # metric is the SINGLE canonical metric name (e.g. 'temperature'); no alias.
    # Per-day baseline values; each day is recorded 3x (morning/noon/evening) so
    # a daily_mean is a genuine aggregation, not a single sample.
    start = datetime(2026, 8, 1, 0, 0, tzinfo=TZ) - timedelta(days=days - 1)
    values = {"co2": [410.0, 405.0, 420.0, 415.0], "humidity": [70.0, 68.0, 72.0, 66.0],
              "temperature": [24.0, 25.0, 26.0, 23.0], "soil_moisture": [55.0, 56.0, 54.0, 57.0]}
    days_vals = values.get(metric, [420.0] * days)[:days]
    while len(days_vals) < days:
        days_vals.append(days_vals[-1])
    # daily intraday offsets (morning/noon/evening) — deterministic, small enough
    # that the daily mean rounds to the baseline value.
    intraday = (-0.5, 0.0, 0.5)
    gh_id = f"{n}_gh"
    sen_id = f"{n}_sen"
    row_id = f"{n}_crop"
    objects = [
        {"id": gh_id, "type": "Greenhouse"},
        {"id": sen_id, "type": "Sensor", "monitoring_target": gh_id,
         "metric": metric, "unit": unit},
        {"id": row_id, "type": "CropRow", "label": f"Row {n[-1]}"},
    ]
    # Explicit relation so any 'associated_row' claim is grounded: greenhouse
    # contains the crop row, sensor monitors the greenhouse.
    relations = [
        {"subject": gh_id, "predicate": "contains", "object": row_id},
        {"subject": sen_id, "predicate": "monitors", "object": gh_id},
    ]
    # 3 records per day at 06:00/12:00/18:00 (deterministic intraday offsets).
    timeseries = []
    for i, base in enumerate(days_vals):
        d = start + timedelta(days=i)
        for hour, off in zip((6, 12, 18), intraday):
            timeseries.append({
                "record_id": f"rec-{n}-{metric}-{d.strftime('%Y%m%d')}-{hour:02d}",
                "sensor_id": sen_id, "metric": metric, "unit": unit,
                "timestamp": (start + timedelta(days=i, hours=hour)).isoformat(),
                "value": round(base + off, 2),
            })
    # Interference records: same sensor/metric OUTSIDE the query window — the
    # agent must bound its aggregation to [start, end], not sweep the whole store.
    interference = [
        {"record_id": f"rec-{n}-{metric}-pre", "sensor_id": sen_id, "metric": metric,
         "unit": unit, "timestamp": (start - timedelta(days=2, hours=8)).isoformat(),
         "value": 999.0},
        {"record_id": f"rec-{n}-{metric}-post", "sensor_id": sen_id, "metric": metric,
         "unit": unit, "timestamp": (start + timedelta(days=days + 1, hours=10)).isoformat(),
         "value": 0.5},
    ]
    # Event thresholds are metric-specific and observably stated in the prompt
    # (e.g. TN43: temperature threshold=35°C, value=38°C).
    event_cfg = {
        "co2": {"value": 900.0, "threshold": 800.0},
        "humidity": {"value": 92.0, "threshold": 80.0},
        "temperature": {"value": 38.0, "threshold": 35.0},
        "soil_moisture": {"value": 5.0, "threshold": 20.0},
    }.get(metric, {"value": 90.0, "threshold": 80.0})
    events = [{"event_id": f"evt-{n}-high", "object_id": gh_id,
               "event_type": f"{metric}_high",
               "timestamp": (start + timedelta(days=1, hours=3)).isoformat(),
               "payload": {"metric": metric, "value": event_cfg["value"],
                           "threshold": event_cfg["threshold"]}}]
    initial_state = {"objects": objects, "relations": relations,
                     "timeseries_records": timeseries + interference,
                     "events": events, "daily_reports": []}
    q = {
        "target_object_ids": [gh_id, sen_id],
        "metrics": [metric],
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(days=days - 1, hours=23)).isoformat(),
        "aggregations": ["mean", "latest", "trend"],
        "required_units": {metric: unit},
    }
    # Explicit trend: net_change_direction (up/down/flat) + a shape descriptor,
    # deterministic and part of the canonical answer.
    trend_label = _trend_label(days_vals)
    trend_shape = _trend_shape(days_vals)
    expected_answer = {
        "normalized_values": {metric: {"daily_means": days_vals,
                                       "latest": days_vals[-1],
                                       "mean": round(sum(days_vals) / len(days_vals), 2),
                                       "unit": unit}},
        "trend": {"label": trend_label, "net_change_direction": trend_label,
                  "shape": trend_shape, "daily_means": days_vals},
        "events": events,
        "summary_facts": [f"sensor={sen_id}", f"associated_row={row_id}",
                          f"daily_means={days_vals}",
                          f"trend={trend_label}",
                          f"{len(events)} high alarm event(s)"],
    }
    # expected_evidence must reference ONLY in-window records (interference
    # records are NOT part of the correct evidence).
    expected_evidence = {"record_ids": [r["record_id"] for r in timeseries],
                         "event_ids": [e["event_id"] for e in events]}
    # SINGLE canonical Oracle: expected_outcome is one dict holding the answer
    # and evidence; expected_answer/expected_evidence are views of it (not two
    # independent shapes).
    canonical = {"answer": expected_answer, "evidence": expected_evidence}
    t = build_memory_task(
        task_id=f"T{n}-v2-mem", prompt=f"查询温室内 {metric} 最近 {days} 天的浓度/状态趋势，返回日均值与异常事件（阈值 {event_cfg['threshold']}{unit}）。",
        initial_state=initial_state, query_spec=q, difficulty="easy",
    )
    t["expected_answer"] = expected_answer
    t["expected_evidence"] = expected_evidence
    t["expected_outcome"] = canonical
    t["review_status"] = "pending"
    return t


def _trend_label(vals: list[float]) -> str:
    """Deterministic trend label from a daily-values sequence.

    Uses the NET change (last - first) for the direction, plus a shape keyword
    for monotonic vs up_then_down / down_then_up sequences. Values that merely
    oscillate but end above the start are still 'up' (net change direction).
    """
    if not vals:
        return "no_data"
    first, last = vals[0], vals[-1]
    delta = last - first
    if abs(delta) < 1e-9:
        return "flat"
    if delta > 0:
        return "up"
    return "down"


def _trend_shape(vals: list[float]) -> str:
    """Shape descriptor: monotonic / up_then_down / down_then_up / flat.

    Used as an additional, non-directional guard on the trend claim so a method
    cannot satisfy 'trend' by only reporting the net direction while ignoring
    an intra-window reversal.
    """
    if len(vals) < 3:
        return "flat" if abs(vals[-1] - vals[0]) < 1e-9 else _trend_label(vals)
    deltas = [vals[i + 1] - vals[i] for i in range(len(vals) - 1)]
    if all(abs(d) < 1e-9 for d in deltas):
        return "flat"
    if all(d >= 0 for d in deltas):
        return "monotonic_up"
    if all(d <= 0 for d in deltas):
        return "monotonic_down"
    # at least one reversal
    sign = [1 if d > 0 else (-1 if d < 0 else 0) for d in deltas]
    nz = [s for s in sign if s != 0]
    if nz and all(s == nz[0] for s in nz):
        return "flat"
    if nz[0] > 0 and nz[-1] < 0:
        return "up_then_down"
    if nz[0] < 0 and nz[-1] > 0:
        return "down_then_up"
    return "oscillating"


def build_test_v2() -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    # scene_construction x4
    for n in ("N01", "N02", "N03", "N04"):
        tasks.append(_scene_task(n))
    # asset_routing x4
    for n in ("N11", "N12", "N13", "N14"):
        tasks.append(_asset_task(n))
    # data_binding x4
    for n in ("N21", "N22", "N23", "N24"):
        tasks.append(_bind_task(n))
    # rule_repair x4
    for n in ("N31", "N32", "N33", "N34"):
        tasks.append(_repair_task(n))
    # memory_query x4
    mem = [("N41", "co2", 4, "ppm"), ("N42", "humidity", 5, "%"),
           ("N43", "temperature", 3, "°C"), ("N44", "soil_moisture", 4, "%")]
    for n, metric, days, unit in mem:
        tasks.append(_memory_task(n, metric, days, unit))
    return tasks


# Gold-only keys that must NEVER appear in public inputs. Anything else that
# describes the *answer* is also excluded via the whitelist below.
_GOLD_KEYS = {
    "required_nodes", "required_edges", "required_bindings", "critical_objects",
    "equivalence_groups", "fatal_constraints", "forbidden_side_effects",
    "allowed_side_effects", "allowed_variants", "expected_outcome",
    "graph_outcome", "expected_answer", "expected_evidence", "good_oracle",
    "query_spec", "goal_state", "trait", "unit", "asset_key", "asset_policy",
    "key_attrs", "observes", "monitoring_target", "required_events", "event_bind",
    "target_object_ids", "metrics", "aggregations", "required_units",
}


def _public_fields(t: dict[str, Any]) -> dict[str, Any]:
    """Whitelisted public fields a method may see — NO gold/answer leakage.

    The method sees only the task description it must act on: identity,
    prompt, task type, difficulty, a reference to the (referenced, not
    inlined) shared knowledge policy, and any initial state it must operate
    on. Every grading target is excluded.
    """
    return {
        "task_id": t.get("task_id"),
        "task_type": t.get("task_type"),
        "difficulty": t.get("difficulty"),
        "prompt": t.get("prompt"),
        "policy_ref": t.get("policy_ref", "shared_knowledge:asset_policy/v2"),
        # initial_state is part of the public input for repair/binding/memory
        # (it is the *input* the method transforms/queries), NEVER the gold.
        "initial_state": t.get("initial_state", {}),
    }


def write_test_v2() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = build_test_v2()
    # write public inputs (no gold) and sealed gold (gold only)
    public = [{} for _ in tasks]
    gold_lines = []
    public_lines = []
    for t in tasks:
        # public: whitelist only — never an exclusion list (refuses future gold
        # keys instead of silently leaking new additions).
        pub = _public_fields(t)
        public_lines.append(json.dumps(pub, ensure_ascii=False, sort_keys=True))
        gold_lines.append(json.dumps(t, ensure_ascii=False, sort_keys=True))
    (OUT / "test_v2_public_inputs.jsonl").write_text(
        "\n".join(public_lines) + "\n", encoding="utf-8")
    (OUT / "test_v2_gold.jsonl").write_text(
        "\n".join(gold_lines) + "\n", encoding="utf-8")
    return {
        "tasks": len(tasks),
        "by_type": {tt: sum(1 for t in tasks if t["task_type"] == tt)
                    for tt in ("scene_construction", "asset_routing", "data_binding",
                               "rule_repair", "memory_query")},
        "public_sha256": _sha(OUT / "test_v2_public_inputs.jsonl"),
        "gold_sha256": _sha(OUT / "test_v2_gold.jsonl"),
    }


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


if __name__ == "__main__":
    print(json.dumps(write_test_v2(), ensure_ascii=False, indent=2))
