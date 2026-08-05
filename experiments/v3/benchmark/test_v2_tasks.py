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
        "N01": {"crop": "Lettuce", "rows": 2, "plants": 12, "giant": False},
        "N02": {"crop": "Strawberry", "rows": 3, "plants": 24, "giant": False},
        "N03": {"crop": "Bell-Pepper", "rows": 3, "plants": 21, "giant": False},
        "N04": {"crop": "Eggplant", "rows": 2, "plants": 10, "giant": False},
    }[n]
    name = crops["crop"].replace("-", "_").lower()
    root = f"{n}_{name}_gh"
    row = f"{n}_{name}_row"
    plant = f"{n}_{name}_plant"
    return {
        "task_id": f"T{n}-v2-scene",
        "task_type": "scene_construction",
        "difficulty": "medium",
        "prompt": f"构建一个 {name} 温室，包含 {crops['rows']} 行作物、{crops['plants']} 株{name}、1 个气象站和 2 个摄像头。",
        "annotation_version": "v2",
        "review_status": "PENDING_HUMAN_REVIEW",
        "initial_state": {},
        "query_spec": None,
        "expected_answer": None,
        "expected_evidence": None,
        "expected_outcome": {"graph": {"required_nodes": [
            {"id": root, "type": "Greenhouse", "role": "root", "count": 1,
             "key_attrs": {"size": "20x6m", "location": {"x": 0, "z": 0}}},
            {"id": row, "type": "CropRow", "role": "entity", "count": crops["rows"],
             "parent": root, "key_attrs": {"location": {"x": 2, "z": 1}}},
            {"id": plant, "type": "Plant", "role": "entity", "count": crops["plants"],
             "parent": row, "key_attrs": {"belongs_to": row, "location": {"x": 3, "z": 2}}},
        ]}},
        "graph_outcome": {"required_nodes": [
            {"id": root, "type": "Greenhouse", "role": "root", "count": 1},
            {"id": row, "type": "CropRow", "role": "entity", "count": crops["rows"], "parent": root},
            {"id": plant, "type": "Plant", "role": "entity", "count": crops["plants"], "parent": row},
        ]},
        "required_nodes": [
            {"id": root, "type": "Greenhouse", "role": "root", "count": 1},
            {"id": row, "type": "CropRow", "role": "entity", "count": crops["rows"], "parent": root},
            {"id": plant, "type": "Plant", "role": "entity", "count": crops["plants"], "parent": row},
        ],
        "required_edges": [
            {"subject": root, "predicate": "contains", "object": row},
            {"subject": row, "predicate": "contains", "object": plant},
        ],
        "required_bindings": [],
        "critical_objects": [],
        "forbidden_side_effects": ["omit_required_plant", "wrong_parent"],
        "fatal_constraints": [],
        "allowed_side_effects": [],
        "equivalence_groups": [],
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
    return {
        "task_id": f"T{n}-v2-asset",
        "task_type": "asset_routing",
        "difficulty": "medium",
        "prompt": f"构建{name}温室，{focus} 株重点{focus}使用高保真资产，{bg} 株背景使用轻量 GLB，缺失补光设备生成占位任务。",
        "annotation_version": "v2",
        "review_status": "PENDING_HUMAN_REVIEW",
        "initial_state": {},
        "query_spec": None, "expected_answer": None, "expected_evidence": None,
        "expected_outcome": {"graph": {"required_nodes": [
            {"id": root, "type": "Greenhouse", "role": "root", "count": 1},
            {"id": row, "type": "CropRow", "role": "entity", "count": 1, "parent": root},
            {"id": focus_p, "type": "Plant", "role": "entity", "count": focus,
             "parent": row, "key_attrs": {"asset_policy": "high_fidelity"}},
            {"id": bg_p, "type": "Plant", "role": "entity", "count": bg,
             "parent": row, "key_attrs": {"asset_policy": "lightweight_glb"}},
        ]}},
        "graph_outcome": {"required_nodes": [
            {"id": root, "type": "Greenhouse", "role": "root", "count": 1},
            {"id": row, "type": "CropRow", "role": "entity", "count": 1, "parent": root},
            {"id": focus_p, "type": "Plant", "role": "entity", "count": focus,
             "parent": row, "key_attrs": {"asset_policy": "high_fidelity"}},
            {"id": bg_p, "type": "Plant", "role": "entity", "count": bg,
             "parent": row, "key_attrs": {"asset_policy": "lightweight_glb"}},
        ]},
        "required_nodes": [
            {"id": root, "type": "Greenhouse", "role": "root", "count": 1},
            {"id": row, "type": "CropRow", "role": "entity", "count": 1, "parent": root},
            {"id": focus_p, "type": "Plant", "role": "entity", "count": focus,
             "parent": row, "key_attrs": {"asset_policy": "high_fidelity"}},
            {"id": bg_p, "type": "Plant", "role": "entity", "count": bg,
             "parent": row, "key_attrs": {"asset_policy": "lightweight_glb"}},
        ],
        "required_edges": [
            {"subject": root, "predicate": "contains", "object": row},
            {"subject": row, "predicate": "contains", "object": focus_p},
            {"subject": row, "predicate": "contains", "object": bg_p},
        ],
        "required_bindings": [
            {"subject": focus_p, "target": root, "type": "asset",
             "metadata": {"asset_key": f"{name}_focus", "policy": "high_fidelity"}},
            {"subject": bg_p, "target": root, "type": "asset",
             "metadata": {"asset_key": f"{name}_bg", "policy": "lightweight_glb"}},
        ],
        "critical_objects": [],
        "forbidden_side_effects": ["all_low_fidelity", "skip_placeholder_for_missing_light"],
        "fatal_constraints": [], "allowed_side_effects": [],
        "equivalence_groups": [], "allowed_variants": [],
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
    return {
        "task_id": f"T{n}-v2-bind",
        "task_type": "data_binding",
        "difficulty": "medium",
        "prompt": f"将温室内 {n_sensors} 个{metric}传感器绑定到对应作物行，并为关键植物绑定特征属性（含单位与时间戳）。",
        "annotation_version": "v2",
        "review_status": "PENDING_HUMAN_REVIEW",
        "initial_state": {}, "query_spec": None, "expected_answer": None, "expected_evidence": None,
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
               "metadata": {"metrics": [metric], "unit": unit}} for s in sensors],
            {"subject": plant, "target": plant, "type": "trait_bind",
             "metadata": {"trait": "growth_stage", "unit": "text",
                          "timestamp": "2026-09-01T00:00:00+08:00"}},
        ],
        "critical_objects": [],
        "forbidden_side_effects": ["missing_unit", "missing_timestamp", "wrong_monitoring_target"],
        "fatal_constraints": [], "allowed_side_effects": [],
        "equivalence_groups": [], "allowed_variants": [],
    }


def _repair_task(n: str) -> dict[str, Any]:
    specs = {
        "N31": ("Pump", "lemongrass", "tree"),
        "N32": ("Camera", "soy", "crop"),
        "N33": ("Irrigation", "alfalfa", "grass"),
        "N34": ("Pump", "oregano", "herb"),
    }[n]
    obj_type, wrong_tie, good_tie = specs
    obj = f"{n}_WaterPump_B" if obj_type == "Pump" else f"{n}_Asset_B"
    root = f"{n}_gh_root"
    row = f"{n}_row"
    return {
        "task_id": f"T{n}-v2-repair",
        "task_type": "rule_repair",
        "difficulty": "hard",
        "prompt": f"输入一个{obj_type} {obj} 错误关联到{wrong_tie}植物的场景，识别资产类型不匹配并改为正确的 {good_tie} 灌溉设备资产或占位任务。",
        "annotation_version": "v2",
        "review_status": "PENDING_HUMAN_REVIEW",
        "initial_state": {"objects": [
            {"id": root, "type": "Greenhouse"},
            {"id": obj, "type": obj_type, "asset_key": wrong_tie},
            {"id": row, "type": "CropRow"},
        ]},
        "goal_state": {"objects": [
            {"id": root, "type": "Greenhouse"},
            {"id": obj, "type": obj_type, "asset_key": good_tie},
            {"id": row, "type": "CropRow"},
        ]},
        "query_spec": None, "expected_answer": None, "expected_evidence": None,
        "expected_outcome": {"graph": {"required_nodes": [
            {"id": root, "type": "Greenhouse", "role": "root", "count": 1},
            {"id": obj, "type": obj_type, "role": "entity", "count": 1, "parent": root},
            {"id": row, "type": "CropRow", "role": "entity", "count": 1, "parent": root},
        ]}},
        "required_nodes": [
            {"id": root, "type": "Greenhouse", "role": "root", "count": 1},
            {"id": obj, "type": obj_type, "role": "entity", "count": 1, "parent": root},
            {"id": row, "type": "CropRow", "role": "entity", "count": 1, "parent": root},
        ],
        "required_edges": [
            {"subject": root, "predicate": "contains", "object": row},
            {"subject": root, "predicate": "contains", "object": obj},
        ],
        "required_bindings": [],
        "critical_objects": [obj],
        "forbidden_side_effects": ["noop_repair", "keep_asset_mismatch"],
        "fatal_constraints": ["asset_type_mismatch_must_be_fixed"],
        "allowed_side_effects": ["set_placeholder"], "equivalence_groups": [],
        "allowed_variants": [],
    }


def _memory_task(n: str, metric: str, days: int, unit: str) -> dict[str, Any]:
    start = datetime(2026, 8, 1, 0, 0, tzinfo=TZ) - timedelta(days=days - 1)
    values = {"co2": [410.0, 405.0, 420.0, 415.0], "humidity": [70.0, 68.0, 72.0, 66.0],
              "thermo": [24.0, 25.0, 26.0, 23.0], "soil_moisture": [55.0, 56.0, 54.0, 57.0]}
    days_vals = values.get(metric, [420.0] * days)[:days]
    while len(days_vals) < days:
        days_vals.append(days_vals[-1])
    objects = [
        {"id": f"{n}_gh", "type": "Greenhouse"},
        {"id": f"{n}_sen", "type": "Sensor", "monitoring_target": f"{n}_gh",
         "metric": metric, "unit": unit},
        {"id": f"{n}_crop", "type": "CropRow", "label": f"Row {n[-1]}"},
    ]
    timeseries = [
        {"record_id": f"rec-{n}-{metric}-{(start+timedelta(days=i)).strftime('%Y%m%d')}",
         "sensor_id": f"{n}_sen", "metric": metric, "unit": unit,
         "timestamp": (start + timedelta(days=i)).isoformat(), "value": float(v)}
        for i, v in enumerate(days_vals)
    ]
    events = [{"event_id": f"evt-{n}-high", "object_id": f"{n}_gh",
               "event_type": f"{metric}_high",
               "timestamp": (start + timedelta(days=1, hours=3)).isoformat(),
               "payload": {"metric": metric, "value": 900 if metric == "co2" else 90,
                           "threshold": 800 if metric == "co2" else 80}}]
    initial_state = {"objects": objects, "timeseries_records": timeseries,
                     "events": events, "daily_reports": []}
    q = {
        "target_object_ids": [f"{n}_gh", f"{n}_sen"],
        "metrics": [metric] if metric not in ("thermo",) else ["temperature"],
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(days=days - 1, hours=23)).isoformat(),
        "aggregations": ["mean", "latest", "trend"],
        "required_units": {("temperature" if metric == "thermo" else metric): unit},
    }
    metric_key = "temperature" if metric == "thermo" else metric
    t = build_memory_task(
        task_id=f"T{n}-v2-mem", prompt=f"查询温室内 {metric_key} 最近 {days} 天的浓度/状态趋势，返回日均值与异常事件。",
        initial_state=initial_state, query_spec=q, difficulty="easy",
    )
    t["expected_answer"] = {
        "normalized_values": {metric_key: {"daily_means": days_vals,
                                           "latest": days_vals[-1],
                                           "mean": round(sum(days_vals) / len(days_vals), 2),
                                           "unit": unit}},
        "events": events,
        "summary_facts": [f"sensor={n}_sen", f"associated_row={n}_crop",
                          f"daily_means={days_vals}",
                          f"{len(events)} high alarm event(s)"],
    }
    t["expected_evidence"] = {"record_ids": [r["record_id"] for r in timeseries],
                              "event_ids": [e["event_id"] for e in events]}
    t["review_status"] = "PENDING_HUMAN_REVIEW"
    return t


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
           ("N43", "thermo", 3, "°C"), ("N44", "soil_moisture", 4, "%")]
    for n, metric, days, unit in mem:
        tasks.append(_memory_task(n, metric, days, unit))
    return tasks


def write_test_v2() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = build_test_v2()
    # write public inputs (no gold) and sealed gold (gold only)
    public = [{} for _ in tasks]
    gold_lines = []
    public_lines = []
    for t in tasks:
        # public: strip gold
        pub = {k: v for k, v in t.items() if k not in
               ("expected_answer", "expected_evidence", "graph_outcome",
                "expected_outcome", "goal_state", "initial_state")}
        pub["initial_state"] = t.get("initial_state", {})
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
