"""Generate T031-T035 annotation review packets (F-012).

Produces DRAFT gold for the 5 held-out tasks. Per the research-integrity rules
the agent (implementer) may generate a draft but must NOT mark it as final gold
— these stay PENDING_HUMAN_REVIEW until the user (annotator 2) reviews.
T034 is a memory_query and uses the new Query-Gold Schema.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from memory_fixtures import build_memory_task, TZ
from datetime import datetime, timedelta

BASE = Path(__file__).resolve().parents[1] / "benchmark" / "annotation_packets"
OUT = BASE / "T031-T035"


def _co2_fixture() -> dict[str, Any]:
    """Last-3-days CO2 concentration fixture (for T034, memory_query).

    3 records per day (06/12/18) so the daily mean is a real aggregation.
    Daily baselines [418.0, 432.0, 425.0]; intraday ±0.5 offsets round back to
    the baseline. Includes an interference record outside the query window.
    """
    start = datetime(2026, 7, 5, 0, 0, tzinfo=TZ)
    rows = [{"id": "cropRow_01", "type": "CropRow", "label": "Row 1"},
            {"id": "cropRow_02", "type": "CropRow", "label": "Row 2"},
            {"id": "cropRow_03", "type": "CropRow", "label": "Row 3"}]
    objects = [
        {"id": "greenhouse_01", "type": "Greenhouse"},
        {"id": "co2_sensor_01", "type": "Sensor", "monitoring_target": "greenhouse_01",
         "metric": "co2", "unit": "ppm"},
        *rows,
    ]
    timeseries = []
    # daily CO2 average values for 3 days (7/5, 7/6, 7/7)
    daily = [418.0, 432.0, 425.0]
    for day in range(3):
        d = start + timedelta(days=day)
        for hour, off in zip((6, 12, 18), (-0.5, 0.0, 0.5)):
            timeseries.append({
                "record_id": f"rec-co2-{d.strftime('%Y%m%d')}-{hour:02d}",
                "sensor_id": "co2_sensor_01", "metric": "co2", "unit": "ppm",
                "timestamp": (start + timedelta(days=day, hours=hour)).isoformat(),
                "value": round(daily[day] + off, 2),
            })
    # interference record OUTSIDE the query window — must not be cited as evidence
    timeseries.append({
        "record_id": "rec-co2-pre", "sensor_id": "co2_sensor_01", "metric": "co2",
        "unit": "ppm", "timestamp": (start - timedelta(days=1, hours=8)).isoformat(),
        "value": 999.0,
    })
    events = [
        {"event_id": "evt-co2-high-1", "object_id": "greenhouse_01",
         "event_type": "co2_high", "timestamp": (start + timedelta(days=2, hours=3)).isoformat(),
         "payload": {"metric": "co2", "value": 880, "threshold": 800}},
    ]
    return {"objects": objects, "timeseries_records": timeseries,
            "events": events, "daily_reports": [],
            "_daily_means": daily}


def _graph_gold(nodes, edges=None, bindings=None, critical=None,
                initial_state=None, goal_state=None, event_bind=None) -> dict[str, Any]:
    return {
        "required_nodes": nodes,
        "required_edges": edges or [],
        "required_bindings": bindings or [],
        "critical_objects": critical or [],
        "initial_state": initial_state or {},
        "goal_state": goal_state or {},
        "event_bind": event_bind or [],
    }


def _packet(task_id, task_type, difficulty, prompt, gold: dict[str, Any],
            rationale: str, review_items: list[str],
            forbidden_side_effects: list[str] | None = None) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "task_type": task_type,
        "difficulty": difficulty,
        "annotation_version": "v2",
        "review_status": "pending",
        "prompt": prompt,
        "gold": gold,
        "rationale": rationale,
        "review_items": review_items,
        "forbidden_side_effects": forbidden_side_effects or [],
    }


def build_packets() -> list[dict[str, Any]]:
    packets = []

    # ---- T031: scene_build — cucumber greenhouse ----
    # Reviewer: add camera observes/pose/coverage gold + irrigation controls.
    t031 = _packet(
        "T031", "scene_construction", "medium",
        "构建一个 20m x 6m 的黄瓜温室，包含 3 行作物、18 株黄瓜、1 个气象站、1 套滴灌设备和 1 个摄像头。",
        _graph_gold(
            nodes=[
                {"id": "cucumber_greenhouse_root", "type": "Greenhouse", "role": "root",
                 "count": 1, "key_attrs": {"location": {"x": 0, "z": 0}, "size": "20x6m"}},
                {"id": "crop_row_01", "type": "CropRow", "role": "entity", "count": 3,
                 "parent": "cucumber_greenhouse_root"},
                {"id": "cucumber_01", "type": "Plant", "role": "entity", "count": 18,
                 "parent": "crop_row_01", "key_attrs": {"belongs_to": "crop_row_01"}},
                {"id": "ws_01", "type": "WeatherStation", "role": "entity", "count": 1,
                 "parent": "cucumber_greenhouse_root"},
                {"id": "drip_01", "type": "Irrigation", "role": "entity", "count": 1,
                 "parent": "cucumber_greenhouse_root"},
                {"id": "cam_01", "type": "Camera", "role": "entity", "count": 1,
                 "parent": "cucumber_greenhouse_root",
                 "key_attrs": {"observes": "crop_row_01", "pose": {"position": [1.0, 2.5, 3.0]},
                               "fov": {"degrees": 45}}},
            ],
            edges=[
                {"subject": "cucumber_greenhouse_root", "predicate": "contains", "object": "crop_row_01"},
                {"subject": "crop_row_01", "predicate": "contains", "object": "cucumber_01"},
                {"subject": "cucumber_greenhouse_root", "predicate": "contains", "object": "ws_01"},
                {"subject": "cucumber_greenhouse_root", "predicate": "contains", "object": "drip_01"},
                {"subject": "cucumber_greenhouse_root", "predicate": "contains", "object": "cam_01"},
                # irrigation controls/service-area
                {"subject": "drip_01", "predicate": "controls", "object": "crop_row_01"},
            ],
            bindings=[
                # controls: irrigation device serves the crop row (control_bind),
                # NOT a meaningless 'asset' binding. WeatherStation carries no
                # asset/control binding — it is an entity with containment only.
                {"subject": "drip_01", "target": "crop_row_01", "type": "control_bind",
                 "metadata": {"service_area": "crop_row_01", "controls": ["crop_row_01"]}},
            ],
        ),
        rationale="scene_construction: complete cucumber greenhouse; camera carries observes/pose/fov; drip irrigation controls crop row (control_bind, gradable); WS entity only (no asset binding).",
        review_items=[
            "Confirm 18 plants as Plant.type with belongs_to crop row",
            "Confirm WeatherStation/Drip/Camera presence and parent containment",
            "Confirm camera has observes/pose/fov",
            "Confirm drip irrigation controls crop_row_01",
        ],
        forbidden_side_effects=["omit_required_plant", "wrong_parent",
                                "omit_camera", "omit_weather_station"],
    )
    t031["equivalence_groups"] = [
        {"group_id": "crop_rows", "match_on": "role", "members": ["crop_row_01"],
         "expected_count": 3},
        {"group_id": "plants", "match_on": "type", "members": ["cucumber_01"],
         "expected_count": 18},
    ]
    packets.append(t031)

    # ---- T032: data_bind — light sensors + tomato traits ----
    # Reviewer: specify key-plant count, consistent trait term, harvest_date as
    # a distinct event binding, timestamp from task input.
    ts = "2026-09-01T00:00:00+08:00"
    t032 = _packet(
        "T032", "data_binding", "medium",
        f"将温室内 2 个光照传感器绑定到对应作物行，并为 1 株关键番茄绑定叶面积指数(LI=leaf_area_index, 单位 m2/m2)与采收日期事件（时间戳 {ts}）。",
        _graph_gold(
            nodes=[
                {"id": "gh_bind_root", "type": "Greenhouse", "role": "root", "count": 1},
                {"id": "crop_row_a", "type": "CropRow", "role": "entity", "count": 1, "parent": "gh_bind_root"},
                {"id": "crop_row_b", "type": "CropRow", "role": "entity", "count": 1, "parent": "gh_bind_root"},
                {"id": "light_sensor_1", "type": "Sensor", "role": "entity", "count": 1,
                 "parent": "crop_row_a", "key_attrs": {"monitoring_target": "crop_row_a"}},
                {"id": "light_sensor_2", "type": "Sensor", "role": "entity", "count": 1,
                 "parent": "crop_row_b", "key_attrs": {"monitoring_target": "crop_row_b"}},
                {"id": "tomato_k1", "type": "Plant", "role": "entity", "count": 1,
                 "parent": "crop_row_a", "key_attrs": {"belongs_to": "crop_row_a"}},
            ],
            edges=[
                {"subject": "gh_bind_root", "predicate": "contains", "object": "crop_row_a"},
                {"subject": "gh_bind_root", "predicate": "contains", "object": "crop_row_b"},
                {"subject": "crop_row_a", "predicate": "contains", "object": "light_sensor_1"},
                {"subject": "crop_row_b", "predicate": "contains", "object": "light_sensor_2"},
                {"subject": "crop_row_a", "predicate": "contains", "object": "tomato_k1"},
            ],
            bindings=[
                {"subject": "light_sensor_1", "target": "crop_row_a", "type": "sensor_bind",
                 "metadata": {"metrics": ["light"], "unit": "klux", "timestamp": ts}},
                {"subject": "light_sensor_2", "target": "crop_row_b", "type": "sensor_bind",
                 "metadata": {"metrics": ["light"], "unit": "klux", "timestamp": ts}},
                {"subject": "tomato_k1", "target": "tomato_k1", "type": "trait_bind",
                 "metadata": {"trait": "leaf_area_index", "unit": "m2/m2", "timestamp": ts}},
            ],
            goal_state={
                "objects": [],
                "events": [
                    {"event_id": "evt-tomato_k1-harvest", "object_id": "tomato_k1",
                     "event_type": "harvest_date", "timestamp": ts},
                ],
            },
            # harvest_date is a first-class scoring target (event_bind), not a
            # nested trait metadata field.
            event_bind=[
                {"event_id": "evt-tomato_k1-harvest", "object_id": "tomato_k1",
                 "event_type": "harvest_date", "timestamp": ts},
            ],
        ),
        rationale="data_binding: 2 light sensors -> rows (sensor_bind, unit klux, timestamp); 1 key tomato binds LI trait + a distinct harvest_date event (timestamp from task).",
        review_items=[
            "Confirm 1 key tomato (explicit in prompt), not arbitrary count",
            "Confirm LI = leaf_area_index (consistent term), unit m2/m2",
            "Confirm harvest_date is a distinct event binding, not nested in trait metadata",
            "Confirm timestamp {ts} in prompt/input",
        ],
        forbidden_side_effects=["missing_unit", "missing_timestamp", "wrong_monitoring_target",
                                "invent_trait", "harvest_not_separate_event"],
    )
    t032["equivalence_groups"] = [
        {"group_id": "light_sensors", "match_on": "type", "members": ["light_sensor_1", "light_sensor_2"],
         "expected_count": 2},
        {"group_id": "keys", "match_on": "id", "members": ["tomato_k1", "gh_bind_root"],
         "expected_count": 1},
    ]
    packets.append(t032)

    # ---- T033: repair — pump asset-type mismatch ----
    # Reviewer: required_nodes must encode the CORRECTED asset_key; add
    # replace_asset + set_placeholder variants; require actual modification.
    t033 = _packet(
        "T033", "rule_repair", "hard",
        "输入一个水泵 WaterPump_B 错误关联到生菜植物的场景，系统需要识别资产类型不匹配并改为灌溉设备资产或占位任务。",
        _graph_gold(
            nodes=[
                {"id": "lettuce_gh_root", "type": "Greenhouse", "role": "root", "count": 1},
                {"id": "WaterPump_B", "type": "Pump", "role": "entity", "count": 1,
                 "parent": "lettuce_gh_root", "key_attrs": {"asset_key": "irrigation"}},  # CORRECTED
                {"id": "lettuce_row", "type": "CropRow", "role": "entity", "count": 1,
                 "parent": "lettuce_gh_root"},
            ],
            edges=[
                {"subject": "lettuce_gh_root", "predicate": "contains", "object": "lettuce_row"},
                {"subject": "lettuce_gh_root", "predicate": "contains", "object": "WaterPump_B"},
            ],
            bindings=[
                {"subject": "WaterPump_B", "target": "WaterPump_B", "type": "asset",
                 "metadata": {"asset_key": "irrigation", "fixed": True}},
            ],
            critical=["WaterPump_B"],
            initial_state={
                "objects": [
                    {"id": "lettuce_gh_root", "type": "Greenhouse"},
                    {"id": "WaterPump_B", "type": "Pump", "asset_key": "lettuce",
                     "asset_binding": {"type": "asset", "asset_key": "lettuce"}},
                    {"id": "lettuce_row", "type": "CropRow"},
                ]
            },
            goal_state={
                "objects": [
                    {"id": "lettuce_gh_root", "type": "Greenhouse"},
                    {"id": "WaterPump_B", "type": "Pump", "asset_key": "irrigation",
                     "asset_binding": {"type": "asset", "asset_key": "irrigation"}},
                    {"id": "lettuce_row", "type": "CropRow"},
                ]
            },
        ),
        rationale="rule_repair: WaterPump_B.asset_key lettuce->irrigation (device asset, crop-independent); required_nodes encode the CORRECTED state; required_bindings distinguish success from no-op.",
        review_items=[
            "Confirm required_nodes now carry asset_key=irrigation (corrected), NOT lettuce",
            "Confirm replace_asset AND set_placeholder both valid variants",
            "Confirm critical WaterPump_B must be actually modified (evidence)",
        ],
        forbidden_side_effects=["noop_repair", "keep_asset_mismatch", "regenerate_whole_scene"],
    )
    t033["allowed_side_effects"] = ["replace_asset", "set_placeholder"]
    t033["allowed_variants"] = [
        {"path": "replace_asset", "detail": "set WaterPump_B.asset_key to irrigation"},
        {"path": "set_placeholder", "detail": "keep mismatch + create placeholder asset_job"},
    ]
    packets.append(t033)

    # ---- T034: memory_query — CO2 3-day trend (Query-Gold) ----
    # Reviewer: add explicit row relation (or remove associated_rows), unify
    # Oracle structure (expected_answer == expected_outcome.answer).
    co2 = _co2_fixture()
    means = list(co2.pop("_daily_means"))  # [418.0, 432.0, 425.0]
    # explicit relations so associated_rows is grounded
    co2["relations"] = [
        {"subject": "greenhouse_01", "predicate": "contains", "object": "cropRow_01"},
        {"subject": "greenhouse_01", "predicate": "contains", "object": "cropRow_02"},
        {"subject": "greenhouse_01", "predicate": "contains", "object": "cropRow_03"},
        {"subject": "co2_sensor_01", "predicate": "monitors", "object": "greenhouse_01"},
    ]
    t034 = build_memory_task(
        task_id="T034", prompt=(
            "查询番茄温室最近 3 天 CO2 浓度趋势，返回传感器、日均值、异常事件与关联作物行。"),
        initial_state=co2,
        query_spec={
            "target_object_ids": ["greenhouse_01", "co2_sensor_01"],
            "metrics": ["co2"],
            "start_time": "2026-07-05T00:00:00+08:00",
            "end_time": "2026-07-07T23:59:59+08:00",
            "aggregations": ["mean", "latest", "trend"],
            "required_units": {"co2": "ppm"},
        },
        difficulty="medium",
    )
    trend_label = "up" if means[-1] > means[0] else ("down" if means[-1] < means[0] else "flat")
    trend_shape = "up_then_down" if means[0] < means[1] > means[2] else (
        "down_then_up" if means[0] > means[1] < means[2] else (
            "monotonic_up" if all(b >= a for a, b in zip(means, means[1:])) else
            ("monotonic_down" if all(b <= a for a, b in zip(means, means[1:])) else "flat")))
    # in-window records only (exclude the 'rec-co2-pre' interference record)
    win_records = [r for r in co2["timeseries_records"]
                   if not r["record_id"].endswith("-pre")]
    expected_answer = {
        "normalized_values": {
            "co2": {"daily_means": means, "latest": means[-1],
                    "mean": round(sum(means) / len(means), 2), "unit": "ppm"},
        },
        "trend": {"label": trend_label, "net_change_direction": trend_label,
                  "shape": trend_shape, "daily_means": means},
        "events": co2["events"],
        "summary_facts": [
            "sensor=co2_sensor_01",
            "associated_rows=Row1,Row2,Row3",
            f"daily_means={means}",
            f"trend={trend_label}",
            f"{len(co2['events'])} high alarm events",
        ],
    }
    expected_evidence = {
        "record_ids": [r["record_id"] for r in win_records],
        "event_ids": [e["event_id"] for e in co2["events"]],
    }
    t034["expected_answer"] = expected_answer
    t034["expected_evidence"] = expected_evidence
    t034["expected_outcome"] = {"answer": expected_answer, "evidence": expected_evidence}
    t034["review_status"] = "pending"
    t034["rationale"] = (
        "memory_query: agent retrieves/aggregates CO2 trend from pre-existing "
        "timeseries; NO scene building. Explicit trend + grounded row relations.")
    t034["review_items"] = [
        "Confirm daily_means (418/432/425) derived from fixture records",
        "Confirm explicit trend field + CO2 high alarm event present",
        "Confirm associated_rows grounded by greenhouse-contains-row relations",
        "Confirm expected_answer and expected_outcome are one canonical Oracle (same shape)",
    ]
    packets.append(t034)

    # ---- T035: asset_route — pepper greenhouse hi-fi vs lightweight ----
    # Reviewer: add missing lighting device + placeholder/asset_job; silent
    # omission must be fatal; clarify asset binding targets.
    t035 = _packet(
        "T035", "asset_routing", "medium",
        "构建辣椒温室，6 株重点辣椒使用高保真资产，14 株背景辣椒使用轻量 GLB，缺失补光设备生成占位任务。",
        _graph_gold(
            nodes=[
                {"id": "pepper_gh_root", "type": "Greenhouse", "role": "root", "count": 1},
                {"id": "pepper_row", "type": "CropRow", "role": "entity", "count": 1,
                 "parent": "pepper_gh_root"},
                {"id": "pepper_focus_01", "type": "Plant", "role": "entity", "count": 6,
                 "parent": "pepper_row", "key_attrs": {"asset_policy": "high_fidelity"}},
                {"id": "pepper_bg_01", "type": "Plant", "role": "entity", "count": 14,
                 "parent": "pepper_row", "key_attrs": {"asset_policy": "lightweight_glb"}},
                {"id": "pepper_light_dev", "type": "Device", "role": "entity", "count": 1,
                 "parent": "pepper_gh_root", "key_attrs": {"device_type": "supplemental_light",
                                                           "asset_state": "placeholder"}},
            ],
            edges=[
                {"subject": "pepper_gh_root", "predicate": "contains", "object": "pepper_row"},
                {"subject": "pepper_row", "predicate": "contains", "object": "pepper_focus_01"},
                {"subject": "pepper_row", "predicate": "contains", "object": "pepper_bg_01"},
                {"subject": "pepper_gh_root", "predicate": "contains", "object": "pepper_light_dev"},
            ],
            bindings=[
                {"subject": "pepper_focus_01", "target": "pepper_focus_asset", "type": "asset",
                 "metadata": {"asset_key": "pepper_focus", "policy": "high_fidelity"}},
                {"subject": "pepper_bg_01", "target": "pepper_bg_asset", "type": "asset",
                 "metadata": {"asset_key": "pepper_bg", "policy": "lightweight_glb"}},
                {"subject": "pepper_light_dev", "target": "pepper_light_job", "type": "asset_job",
                 "metadata": {"job_type": "placeholder", "policy": "procedural_model",
                              "reason": "missing_supplemental_light"}},
            ],
            critical=["pepper_light_dev"],
        ),
        rationale="asset_routing: 6 hi-fi focus peppers + 14 lightweight bg peppers; missing supplemental-light generates a placeholder asset_job (gradable).",
        review_items=[
            "Confirm 6 hi-fi vs 14 lightweight split",
            "Confirm missing light-fill spawns asset.job.create placeholder (not silent skip)",
            "Confirm asset_key/policy on each asset bind; placeholder job on light device",
        ],
        forbidden_side_effects=["all_low_fidelity", "skip_placeholder_for_missing_light",
                                "silent_omit_supplemental_light"],
    )
    t035["fatal_constraints"] = ["missing_supplemental_light_must_generate_placeholder"]
    t035["allowed_side_effects"] = ["set_placeholder", "create_asset_job"]
    packets.append(t035)

    return packets


def write_packets() -> list[str]:
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for p in build_packets():
        fn = OUT / f"{p['task_id']}_annotation_packet.json"
        fn.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(str(fn))
    # also a consolidated review index
    idx = {"note": "T031-T035 draft annotation packets. review_status=PENDING_HUMAN_REVIEW.",
           "total": len(written)}
    (OUT / "INDEX.md").write_text(
        "## By Chen T031-T035 — PENDING_HUMAN_REVIEW\n\n"
        "Agent produced DRAFT gold only. User (annotator 2) must review each "
        "task_id gold before it can be used as final test-set gold.\n\n"
        "| task | task_type | difficulty | status |\n"
        "|------|-----------|-----------|--------|\n" +
        "\n".join(f"| {p['task_id']} | {p['task_type']} | {p['difficulty']} | PENDING_HUMAN_REVIEW |"
                  for p in build_packets()) + "\n",
        encoding="utf-8")
    return written


if __name__ == "__main__":
    for w in write_packets():
        print("wrote", w)
