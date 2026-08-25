#!/usr/bin/env python3
"""Generate the External300 candidate benchmark deterministically.

This generator creates a *candidate pool*, not a frozen external test set.  The
draft gold is intentionally marked ``pending`` and must be blind-reviewed by two
human annotators who were not involved in method development before any result is
reported as external-test evidence.

The generator never imports or calls a scored method.  Its only inputs are the
constants in this file and the public-source provenance recorded in ``SOURCES.md``.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


OUT = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
LEGACY_PUBLIC = REPO_ROOT / "experiments/v3/benchmark/test_v2/test_v2_public_inputs.jsonl"

ANNOTATION_VERSION = "v2"
POLICY_REF = "shared_knowledge:asset_policy/v2"
TZ = timezone(timedelta(hours=8))

CROPS = (
    "tomato", "cucumber", "lettuce", "strawberry", "bell_pepper",
    "eggplant", "basil", "spinach", "pak_choi", "melon",
    "green_bean", "radish", "cherry_tomato", "dwarf_tomato", "arugula",
    "kale", "celery", "parsley", "mint", "coriander",
)

METRICS = (
    ("temperature", "celsius", 24.0, 0.4),
    ("humidity", "percent", 68.0, 1.0),
    ("co2", "ppm", 430.0, 8.0),
    ("soil_moisture", "percent", 55.0, 1.0),
    ("light", "klux", 32.0, 2.0),
)

SOURCE_REGISTRY = {
    "semantic_core": ["SAREF4AGRI-v2.1.1", "W3C-SOSA-SSN-2017"],
    "greenhouse_schema": ["FIWARE-SmartDataModels-AgriGreenhouse"],
    "scenario_basis": [
        "WUR-AGC-2018-cucumber",
        "WUR-AGC-2019-cherry-tomato",
        "WUR-AGC-2022-lettuce",
        "WUR-AGC-2024-dwarf-tomato",
    ],
}


def difficulty(index: int) -> str:
    if index <= 15:
        return "easy"
    if index <= 45:
        return "medium"
    return "hard"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def public_view(task: dict[str, Any]) -> dict[str, Any]:
    """Whitelist the only fields a method is allowed to see."""
    return {
        "task_id": task["task_id"],
        "task_type": task["task_type"],
        "difficulty": task["difficulty"],
        "prompt": task["prompt"],
        "policy_ref": POLICY_REF,
        "initial_state": deepcopy(task.get("initial_state") or {}),
    }


def base_gold(
    *, task_id: str, task_type: str, diff: str, prompt: str,
    initial_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "task_type": task_type,
        "difficulty": diff,
        "prompt": prompt,
        "annotation_version": ANNOTATION_VERSION,
        "review_status": "pending",
        "initial_state": initial_state or {},
        "query_spec": None,
        "expected_answer": None,
        "expected_evidence": None,
        "expected_outcome": {},
        "required_nodes": [],
        "required_edges": [],
        "required_bindings": [],
        "critical_objects": [],
        "forbidden_side_effects": [],
        "fatal_constraints": [],
        "allowed_side_effects": [],
        "equivalence_groups": [],
        "allowed_variants": [],
    }


def scene_task(index: int) -> tuple[dict[str, Any], dict[str, str]]:
    diff = difficulty(index)
    crop = CROPS[(index - 1) % len(CROPS)]
    tag = f"ESC{index:03d}"
    task_id = f"EXT-SC-{index:03d}"
    root = f"{tag}_greenhouse"
    plot = f"{tag}_plot"
    row = f"{tag}_row"
    plant = f"{tag}_{crop}_plant"
    station = f"{tag}_weather_station"

    if diff == "easy":
        rows = 1 + (index % 2)
        plants = rows * (6 + index % 5)
        cameras = 0 if index <= 5 else 1
        use_plot = False
    elif diff == "medium":
        rows = 2 + (index % 3)
        plants = rows * (7 + index % 5)
        cameras = 2
        use_plot = False
    else:
        rows = 4 + (index % 2)
        plants = rows * (8 + index % 5)
        cameras = 2
        use_plot = True

    camera_ids = [f"{tag}_camera_{i}" for i in range(1, cameras + 1)]
    parent_for_rows = plot if use_plot else root
    camera_clause = ""
    if cameras:
        camera_clause = (
            f"、{cameras} 个摄像头；摄像头必须位于温室内并配置观察目标、位姿与视场角"
        )
    plot_clause = "1 个种植分区内设置" if use_plot else "设置"
    prompt_templates = (
        "新建 {crop} 温室：{plot_clause}{rows} 行作物，共 {plants} 株，配 1 个气象站{camera_clause}。",
        "请搭建一座 {crop} 生产温室，{plot_clause}{rows} 个作物行和 {plants} 株植株，并放置 1 个气象站{camera_clause}。",
        "生成 {crop} 温室场景；场景需含 {rows} 行、{plants} 株作物和 1 个气象站{camera_clause}，所有设备均在温室内部。",
        "按照生产清单构建 {crop} 温室：作物行 {rows}、植株 {plants}、气象站 1{camera_clause}。",
        "建立 {crop} 数字孪生温室，{plot_clause}{rows} 行栽培单元与 {plants} 株植株，另含 1 个气象站{camera_clause}。",
        "为 {crop} 种植任务创建温室对象图，包含 {rows} 个 CropRow、{plants} 个 Plant、1 个 WeatherStation{camera_clause}。",
    )
    prompt = prompt_templates[(index - 1) % len(prompt_templates)].format(
        crop=crop,
        plot_clause=plot_clause,
        rows=rows,
        plants=plants,
        camera_clause=camera_clause,
    )

    nodes: list[dict[str, Any]] = [
        {"id": root, "type": "Greenhouse", "role": "root", "count": 1},
    ]
    edges: list[dict[str, Any]] = []
    if use_plot:
        nodes.append({"id": plot, "type": "Plot", "role": "entity", "count": 1, "parent": root})
        edges.append({"subject": root, "predicate": "contains", "object": plot})
    nodes.extend([
        {"id": row, "type": "CropRow", "role": "entity", "count": rows, "parent": parent_for_rows},
        {"id": plant, "type": "Plant", "role": "entity", "count": plants, "parent": row},
        {"id": station, "type": "WeatherStation", "role": "entity", "count": 1, "parent": root},
    ])
    edges.extend([
        {"subject": parent_for_rows, "predicate": "contains", "object": row},
        {"subject": row, "predicate": "contains", "object": plant},
        {"subject": root, "predicate": "contains", "object": station},
    ])
    for cid in camera_ids:
        nodes.append({
            "id": cid,
            "type": "Camera",
            "role": "entity",
            "count": 1,
            "parent": root,
            "key_attrs": {"observes": row},
        })
        edges.append({"subject": root, "predicate": "contains", "object": cid})

    task = base_gold(task_id=task_id, task_type="scene_construction", diff=diff, prompt=prompt)
    task.update({
        "expected_outcome": {"graph": {"required_nodes": deepcopy(nodes)}},
        "graph_outcome": {"required_nodes": deepcopy(nodes)},
        "required_nodes": nodes,
        "required_edges": edges,
        "forbidden_side_effects": ["omit_required_plant", "wrong_parent", "omit_weather_station"],
        "fatal_constraints": ["hierarchy_must_be_valid", "weather_station_must_be_present"],
        "equivalence_groups": [
            {"group_id": f"{tag}_rows", "match_on": "type", "members": [row], "expected_count": rows},
            {"group_id": f"{tag}_plants", "match_on": "type", "members": [plant], "expected_count": plants},
        ],
    })
    if cameras:
        task["forbidden_side_effects"].append("omit_camera")
        task["fatal_constraints"].append("camera_must_have_observes_target")
        task["equivalence_groups"].append({
            "group_id": f"{tag}_cameras",
            "match_on": "role",
            "members": camera_ids,
            "expected_count": cameras,
        })
    return task, {
        "crop": crop,
        "scenario_family": "hierarchy_with_plot" if use_plot else "greenhouse_hierarchy",
        "source_basis": "SAREF4AGRI+FIWARE",
    }


def asset_task(index: int) -> tuple[dict[str, Any], dict[str, str]]:
    diff = difficulty(index)
    crop = CROPS[(index + 4) % len(CROPS)]
    tag = f"EAR{index:03d}"
    task_id = f"EXT-AR-{index:03d}"
    root = f"{tag}_greenhouse"
    row = f"{tag}_row"
    focus_id = f"{tag}_{crop}_focus"
    background_id = f"{tag}_{crop}_background"
    focus = 2 + (index % 6)
    background = 10 + (index * 3 % 21)
    if diff == "easy":
        missing_types: list[str] = []
    elif diff == "medium":
        missing_types = [("supplemental_light", "fogger", "circulation_fan")[index % 3]]
    else:
        pairs = (
            ("supplemental_light", "fogger"),
            ("circulation_fan", "nutrient_doser"),
            ("shading_screen", "thermal_camera"),
        )
        missing_types = list(pairs[index % len(pairs)])

    missing_clause = ""
    if missing_types:
        joined = "、".join(missing_types)
        missing_clause = f"；当前缺少 {joined} 资产，必须保留设备占位对象并创建资产生成任务"
    prompt_templates = (
        "构建 {crop} 温室资产方案：{focus} 株重点植株采用 high_fidelity，{background} 株背景植株采用 lightweight_glb{missing_clause}。",
        "为 {crop} 场景路由资产，前景 {focus} 株使用高保真模型，背景 {background} 株使用轻量 GLB{missing_clause}。",
        "创建 {crop} 温室并区分资产质量：重点植株 {focus} 株为 high_fidelity，普通背景 {background} 株为 lightweight_glb{missing_clause}。",
        "按性能预算配置 {crop} 数字孪生：{focus} 株关键作物使用高保真资产，其余 {background} 株使用轻量资产{missing_clause}。",
        "生成 {crop} 温室的分级资产绑定，focus={focus}、background={background}；两组分别采用 high_fidelity 与 lightweight_glb{missing_clause}。",
    )
    prompt = prompt_templates[(index - 1) % len(prompt_templates)].format(
        crop=crop, focus=focus, background=background, missing_clause=missing_clause,
    )

    nodes: list[dict[str, Any]] = [
        {"id": root, "type": "Greenhouse", "role": "root", "count": 1},
        {"id": row, "type": "CropRow", "role": "entity", "count": 1, "parent": root},
        {
            "id": focus_id, "type": "Plant", "role": "focus", "count": focus,
            "parent": row, "key_attrs": {"asset_policy": "high_fidelity"},
        },
        {
            "id": background_id, "type": "Plant", "role": "background", "count": background,
            "parent": row, "key_attrs": {"asset_policy": "lightweight_glb"},
        },
    ]
    edges = [
        {"subject": root, "predicate": "contains", "object": row},
        {"subject": row, "predicate": "contains", "object": focus_id},
        {"subject": row, "predicate": "contains", "object": background_id},
    ]
    bindings: list[dict[str, Any]] = [
        {
            "subject": focus_id,
            "target": f"{focus_id}_asset",
            "type": "asset",
            "metadata": {"asset_key": f"{crop}_focus", "policy": "high_fidelity"},
        },
        {
            "subject": background_id,
            "target": f"{background_id}_asset",
            "type": "asset",
            "metadata": {"asset_key": f"{crop}_bg", "policy": "lightweight_glb"},
        },
    ]
    critical: list[str] = []
    for ordinal, device_type in enumerate(missing_types, start=1):
        did = f"{tag}_missing_{ordinal}"
        nodes.append({
            "id": did,
            "type": "Device",
            "role": "entity",
            "count": 1,
            "parent": root,
            "key_attrs": {"device_type": device_type, "asset_state": "placeholder"},
        })
        edges.append({"subject": root, "predicate": "contains", "object": did})
        bindings.append({
            "subject": did,
            "target": f"{did}_placeholder",
            "type": "asset_job",
            "metadata": {
                "job_type": "placeholder",
                "policy": "procedural_model",
                "reason": f"missing_{device_type}",
            },
        })
        critical.append(did)

    task = base_gold(task_id=task_id, task_type="asset_routing", diff=diff, prompt=prompt)
    task.update({
        "expected_outcome": {"graph": {"required_nodes": deepcopy(nodes)}},
        "graph_outcome": {"required_nodes": deepcopy(nodes)},
        "required_nodes": nodes,
        "required_edges": edges,
        "required_bindings": bindings,
        "critical_objects": critical,
        "forbidden_side_effects": ["all_low_fidelity", "swap_focus_background_policy", "silent_asset_omission"],
        "fatal_constraints": ["focus_must_be_high_fidelity", "background_must_be_lightweight_glb"],
        "allowed_side_effects": ["set_placeholder", "create_asset_job"] if missing_types else [],
        "equivalence_groups": [
            {"group_id": f"{tag}_focus", "match_on": "key_attrs", "members": [focus_id], "expected_count": focus},
            {"group_id": f"{tag}_background", "match_on": "key_attrs", "members": [background_id], "expected_count": background},
        ],
    })
    if missing_types:
        task["fatal_constraints"].append("missing_asset_must_generate_placeholder_job")
    return task, {
        "crop": crop,
        "scenario_family": "tiered_asset_with_placeholder" if missing_types else "tiered_plant_asset",
        "source_basis": "FIWARE+project-asset-policy",
    }


def data_binding_task(index: int) -> tuple[dict[str, Any], dict[str, str]]:
    diff = difficulty(index)
    crop = CROPS[(index + 9) % len(CROPS)]
    tag = f"EDB{index:03d}"
    task_id = f"EXT-DB-{index:03d}"
    root = f"{tag}_greenhouse"
    row_count = 2 if diff == "hard" else 1
    rows = [f"{tag}_row_{i}" for i in range(1, row_count + 1)]
    if diff == "easy":
        sensor_count = 1
        trait, trait_unit = "growth_stage", "text"
    elif diff == "medium":
        sensor_count = 2 + (index % 2)
        trait, trait_unit = (("growth_stage", "text"), ("canopy_height", "cm"))[index % 2]
    else:
        sensor_count = 4
        trait, trait_unit = (
            ("leaf_area_index", "index"),
            ("fruit_load", "count"),
            ("growth_stage", "text"),
        )[index % 3]

    metric_specs = [METRICS[(index + j - 1) % len(METRICS)] for j in range(sensor_count)]
    timestamp = datetime(2026, 10, 1, 8, 0, tzinfo=TZ) + timedelta(days=index, hours=index % 6)
    timestamp_iso = timestamp.isoformat()

    objects: list[dict[str, Any]] = [{"id": root, "type": "Greenhouse"}]
    relations: list[dict[str, Any]] = []
    for rid in rows:
        objects.append({"id": rid, "type": "CropRow", "parent": root})
        relations.append({"subject": root, "predicate": "contains", "object": rid})

    sensors: list[tuple[str, str, str, str]] = []
    for j, (metric, unit, _base, _offset) in enumerate(metric_specs, start=1):
        sid = f"{tag}_sensor_{j}"
        rid = rows[(j - 1) % len(rows)]
        sensors.append((sid, rid, metric, unit))
        objects.append({
            "id": sid,
            "type": "Sensor",
            "parent": rid,
            "metric": metric,
            "unit": unit,
        })
        relations.append({"subject": rid, "predicate": "contains", "object": sid})

    plants: list[tuple[str, str]] = []
    plants_needed = 2 if diff == "hard" else 1
    for j in range(1, plants_needed + 1):
        pid = f"{tag}_{crop}_key_plant_{j}"
        rid = rows[(j - 1) % len(rows)]
        plants.append((pid, rid))
        objects.append({"id": pid, "type": "Plant", "parent": rid, "key_attrs": {"is_key": True}})
        relations.append({"subject": rid, "predicate": "contains", "object": pid})

    mapping_text = "；".join(
        f"{sid} 的 {metric}（{unit}）绑定到 {rid}" for sid, rid, metric, unit in sensors
    )
    plant_text = "、".join(pid for pid, _ in plants)
    prompt_templates = (
        "在既有温室对象图上建立数据绑定：{mapping_text}。为关键植株 {plant_text} 绑定 {trait}（单位 {trait_unit}）。所有绑定时间戳统一为 {timestamp}。",
        "请保持对象 ID 不变并完成绑定。{mapping_text}；关键植株 {plant_text} 的特征为 {trait}，单位 {trait_unit}，timestamp {timestamp}。",
        "将传感器绑定到指定作物行：{mapping_text}。同时给 {plant_text} 增加 {trait} 特征绑定（{trait_unit}），录制时间 {timestamp}。",
        "根据现有层级生成 sensor_bind 与 trait_bind：{mapping_text}；{plant_text}→{trait}/{trait_unit}。时间戳 {timestamp}。",
    )
    prompt = prompt_templates[(index - 1) % len(prompt_templates)].format(
        mapping_text=mapping_text,
        plant_text=plant_text,
        trait=trait,
        trait_unit=trait_unit,
        timestamp=timestamp_iso,
    )

    required_nodes = [{"id": root, "type": "Greenhouse", "role": "root", "count": 1}]
    required_nodes.extend(
        {"id": rid, "type": "CropRow", "role": "entity", "count": 1, "parent": root}
        for rid in rows
    )
    required_nodes.extend(
        {"id": sid, "type": "Sensor", "role": "entity", "count": 1, "parent": rid}
        for sid, rid, _metric, _unit in sensors
    )
    required_nodes.extend(
        {"id": pid, "type": "Plant", "role": "entity", "count": 1, "parent": rid}
        for pid, rid in plants
    )
    bindings = [
        {
            "subject": sid,
            "target": rid,
            "type": "sensor_bind",
            "metadata": {"metrics": [metric], "unit": unit, "timestamp": timestamp_iso},
        }
        for sid, rid, metric, unit in sensors
    ]
    bindings.extend(
        {
            "subject": pid,
            "target": pid,
            "type": "trait_bind",
            "metadata": {"trait": trait, "unit": trait_unit, "timestamp": timestamp_iso},
        }
        for pid, _rid in plants
    )

    task = base_gold(
        task_id=task_id,
        task_type="data_binding",
        diff=diff,
        prompt=prompt,
        initial_state={"objects": objects, "relations": relations},
    )
    task.update({
        "expected_outcome": {"graph": {"required_nodes": deepcopy(required_nodes)}},
        "required_nodes": required_nodes,
        "required_edges": deepcopy(relations),
        "required_bindings": bindings,
        "critical_objects": [pid for pid, _ in plants],
        "forbidden_side_effects": ["rename_object", "wrong_monitoring_target", "missing_unit", "missing_timestamp", "invent_trait"],
        "fatal_constraints": ["every_sensor_must_bind_to_declared_row", "binding_metadata_must_match_public_contract"],
        "equivalence_groups": [
            {"group_id": f"{tag}_sensors", "match_on": "id", "members": [s[0] for s in sensors], "expected_count": len(sensors)},
            {"group_id": f"{tag}_key_plants", "match_on": "id", "members": [p[0] for p in plants], "expected_count": len(plants)},
        ],
    })
    return task, {
        "crop": crop,
        "scenario_family": "multirow_multimetric_binding" if diff == "hard" else "typed_sensor_trait_binding",
        "source_basis": "SAREF4AGRI+W3C-SOSA-SSN",
    }


def repair_task(index: int) -> tuple[dict[str, Any], dict[str, str]]:
    diff = difficulty(index)
    tag = f"ERR{index:03d}"
    task_id = f"EXT-RR-{index:03d}"
    root = f"{tag}_greenhouse"
    row = f"{tag}_row"
    device_type, target_asset = (
        ("Pump", "irrigation"),
        ("Irrigation", "irrigation"),
        ("Camera", "camera"),
        ("Sensor", "sensor"),
    )[(index - 1) % 4]
    wrong_assets = ("tomato", "lettuce", "strawberry", "corn", "lemongrass", "basil", "oregano", "soy", "alfalfa", "plant")
    wrong_asset = wrong_assets[(index * 3) % len(wrong_assets)]
    critical = f"{tag}_{device_type.lower()}"

    support_attrs: dict[str, Any] = {}
    if device_type == "Camera":
        support_attrs = {
            "observes": row,
            "pose": {"position": [1.0, 2.5, 3.0]},
            "fov": {"degrees": 55.0},
        }
    elif device_type == "Sensor":
        support_attrs = {
            "monitoring_target": row,
            "unit": "celsius",
            "timestamp": "2026-10-01T08:00:00+08:00",
        }

    objects: list[dict[str, Any]] = [
        {"id": root, "type": "Greenhouse"},
        {"id": row, "type": "CropRow", "parent": root},
        {
            "id": critical,
            "type": device_type,
            "parent": root,
            "asset_key": wrong_asset,
            "asset_binding": {"type": "asset", "asset_key": wrong_asset},
            "key_attrs": deepcopy(support_attrs),
        },
    ]
    relations = [
        {"subject": root, "predicate": "contains", "object": row},
        {"subject": root, "predicate": "contains", "object": critical},
    ]
    distractor_count = 0 if diff == "easy" else (1 if diff == "medium" else 2)
    distractor_ids: list[str] = []
    for j in range(1, distractor_count + 1):
        did = f"{tag}_preserve_plant_{j}"
        distractor_ids.append(did)
        objects.append({
            "id": did,
            "type": "Plant",
            "parent": row,
            "asset_key": CROPS[(index + j) % len(CROPS)],
        })
        relations.append({"subject": row, "predicate": "contains", "object": did})

    preserve_clause = ""
    if distractor_ids:
        preserve_clause = f" 不得修改或删除非目标对象：{', '.join(distractor_ids)}。"
    prompt_templates = (
        "修复既有场景中的资产类型错误：{critical} 是 {device_type}，却绑定了 {wrong_asset} 植物资产。仅将其 asset_key 修正为 {target_asset}。{preserve_clause}",
        "对象 {critical}（类型 {device_type}）存在错绑，当前 asset_key={wrong_asset}。执行最小修复，使 asset_key={target_asset}；禁止重建整座温室。{preserve_clause}",
        "检查并修复 {critical} 的设备资产：{device_type} 不应使用 {wrong_asset}，目标资产类别为 {target_asset}。保留对象 ID 和层级。{preserve_clause}",
        "对输入场景做类型化修复。目标对象 {critical}/{device_type} 错用了 {wrong_asset} 资产，必须直接替换为 {target_asset}，其余对象保持不变。{preserve_clause}",
    )
    prompt = prompt_templates[(index - 1) % len(prompt_templates)].format(
        critical=critical,
        device_type=device_type,
        wrong_asset=wrong_asset,
        target_asset=target_asset,
        preserve_clause=preserve_clause,
    )

    goal_objects = deepcopy(objects)
    for obj in goal_objects:
        if obj["id"] == critical:
            obj["asset_key"] = target_asset
            obj["asset_binding"] = {"type": "asset", "asset_key": target_asset}

    required_nodes = [
        {"id": root, "type": "Greenhouse", "role": "root", "count": 1},
        {"id": row, "type": "CropRow", "role": "entity", "count": 1, "parent": root},
        {
            "id": critical,
            "type": device_type,
            "role": "entity",
            "count": 1,
            "parent": root,
            "key_attrs": {"asset_key": target_asset, **deepcopy(support_attrs)},
        },
    ]
    required_nodes.extend(
        {
            "id": did,
            "type": "Plant",
            "role": "entity",
            "count": 1,
            "parent": row,
            "key_attrs": {"asset_key": next(o["asset_key"] for o in objects if o["id"] == did)},
        }
        for did in distractor_ids
    )
    required_binding = {
        "subject": critical,
        "target": critical,
        "type": "asset",
        "metadata": {"asset_key": target_asset, "fixed": True},
    }
    task = base_gold(
        task_id=task_id,
        task_type="rule_repair",
        diff=diff,
        prompt=prompt,
        initial_state={"objects": objects, "relations": relations},
    )
    task.update({
        "goal_state": {"objects": goal_objects, "relations": deepcopy(relations)},
        "expected_outcome": {
            "graph": {
                "required_nodes": deepcopy(required_nodes),
                "required_bindings": [deepcopy(required_binding)],
            }
        },
        "required_nodes": required_nodes,
        "required_edges": deepcopy(relations),
        "required_bindings": [required_binding],
        "critical_objects": [critical],
        "forbidden_side_effects": ["noop_repair", "keep_asset_mismatch", "regenerate_whole_scene", "modify_noncritical_object"],
        "fatal_constraints": ["asset_type_mismatch_must_be_fixed", "critical_object_must_be_actually_modified"],
        "allowed_side_effects": ["replace_asset"],
        "allowed_variants": [{"path": "replace_asset", "detail": "set critical object asset_key to the declared device asset"}],
    })
    return task, {
        "crop": "n/a",
        "scenario_family": f"typed_asset_mismatch_{device_type.lower()}",
        "source_basis": "SAREF4AGRI+project-repair-contract",
    }


def trend_label(values: list[float]) -> str:
    if not values:
        return "no_data"
    delta = values[-1] - values[0]
    if abs(delta) < 1e-9:
        return "flat"
    return "up" if delta > 0 else "down"


def trend_shape(values: list[float]) -> str:
    if len(values) < 3:
        return "flat" if abs(values[-1] - values[0]) < 1e-9 else trend_label(values)
    deltas = [values[i + 1] - values[i] for i in range(len(values) - 1)]
    if all(abs(d) < 1e-9 for d in deltas):
        return "flat"
    if all(d >= 0 for d in deltas):
        return "monotonic_up"
    if all(d <= 0 for d in deltas):
        return "monotonic_down"
    signs = [1 if d > 0 else -1 if d < 0 else 0 for d in deltas]
    nonzero = [s for s in signs if s]
    if nonzero[0] > 0 and nonzero[-1] < 0:
        return "up_then_down"
    if nonzero[0] < 0 and nonzero[-1] > 0:
        return "down_then_up"
    return "oscillating"


def pattern_values(index: int, days: int, base: float) -> list[float]:
    mode = (index - 1) % 6
    if mode == 0:
        offsets = list(range(days))
    elif mode == 1:
        offsets = list(reversed(range(days)))
    elif mode == 2:
        offsets = [0, 2, 4, 3, 2, 1, 0][:days]
    elif mode == 3:
        offsets = [4, 2, 0, 1, 2, 3, 4][:days]
    elif mode == 4:
        offsets = [0, 2, -1, 3, 1, 4, 2][:days]
    else:
        offsets = [0] * days
    if len(offsets) < days:
        offsets.extend([offsets[-1]] * (days - len(offsets)))
    return [round(base + value, 2) for value in offsets]


def memory_task(index: int) -> tuple[dict[str, Any], dict[str, str]]:
    diff = difficulty(index)
    crop = ("cucumber", "cherry_tomato", "lettuce", "dwarf_tomato")[(index - 1) % 4]
    metric, unit, metric_base, intraday_offset = METRICS[(index - 1) % len(METRICS)]
    tag = f"EMQ{index:03d}"
    task_id = f"EXT-MQ-{index:03d}"
    root = f"{tag}_greenhouse"
    row = f"{tag}_{crop}_row"
    sensor = f"{tag}_{metric}_sensor"
    days = 3 + (index % 2) if diff == "easy" else (5 + index % 2 if diff == "medium" else 7)
    start = datetime(2025, 1, 1, 0, 0, tzinfo=TZ) + timedelta(days=index * 9)
    daily_means = pattern_values(index, days, metric_base + (index % 5))

    records: list[dict[str, Any]] = []
    for day_offset, day_mean in enumerate(daily_means):
        day_start = start + timedelta(days=day_offset)
        for hour, offset in ((6, -intraday_offset), (12, 0.0), (18, intraday_offset)):
            timestamp = day_start + timedelta(hours=hour)
            records.append({
                "record_id": f"rec-{tag}-{metric}-{timestamp.strftime('%Y%m%d-%H')}",
                "sensor_id": sensor,
                "object_id": root,
                "metric": metric,
                "unit": unit,
                "timestamp": timestamp.isoformat(),
                "value": round(day_mean + offset, 2),
            })
    records.extend([
        {
            "record_id": f"rec-{tag}-{metric}-pre",
            "sensor_id": sensor,
            "object_id": root,
            "metric": metric,
            "unit": unit,
            "timestamp": (start - timedelta(days=2, hours=8)).isoformat(),
            "value": round(metric_base * 2.0, 2),
        },
        {
            "record_id": f"rec-{tag}-{metric}-post",
            "sensor_id": sensor,
            "object_id": root,
            "metric": metric,
            "unit": unit,
            "timestamp": (start + timedelta(days=days + 1, hours=10)).isoformat(),
            "value": round(metric_base * 0.25, 2),
        },
    ])

    event_count = 0 if diff == "easy" and index % 3 == 0 else (2 if diff == "hard" and index % 2 == 0 else 1)
    events: list[dict[str, Any]] = []
    threshold = {
        "temperature": 32.0,
        "humidity": 85.0,
        "co2": 900.0,
        "soil_moisture": 35.0,
        "light": 55.0,
    }[metric]
    for event_index in range(event_count):
        event_time = start + timedelta(days=min(1 + event_index * 2, days - 1), hours=3)
        direction = "low" if metric == "soil_moisture" else "high"
        value = threshold - 8 if direction == "low" else threshold + 8
        events.append({
            "event_id": f"evt-{tag}-{metric}-{event_index + 1}",
            "object_id": root,
            "event_type": f"{metric}_{direction}",
            "timestamp": event_time.isoformat(),
            "payload": {"metric": metric, "threshold": threshold, "value": value},
        })

    end = start + timedelta(days=days - 1, hours=23)
    prompt_templates = (
        "针对传感器 {sensor}，查询温室内 {metric} 最近 {days} 天的状态趋势，返回每日均值、窗口均值、最新日均值和异常事件，并给出记录证据。",
        "从传感器 {sensor} 的现有记忆中汇总温室内 {metric} 最近 {days} 天的数据；报告日均序列、总体均值、趋势形态及异常事件，禁止改写历史记录。",
        "检索传感器 {sensor} 对温室内 {metric} 最近 {days} 天的时间序列，过滤窗口外干扰记录，返回日均值、趋势和可核验 evidence IDs。",
        "针对传感器 {sensor}，查询温室内 {metric} 最近 {days} 天的观测，输出每日均值、最新值、趋势与异常事件证据。",
    )
    prompt = prompt_templates[(index - 1) % len(prompt_templates)].format(
        metric=metric, days=days, sensor=sensor,
    )
    initial_state = {
        "objects": [
            {"id": root, "type": "Greenhouse"},
            {"id": row, "type": "CropRow", "parent": root, "label": f"{crop} row"},
            {
                "id": sensor,
                "type": "Sensor",
                "parent": root,
                "monitoring_target": root,
                "metric": metric,
                "unit": unit,
            },
        ],
        "relations": [
            {"subject": root, "predicate": "contains", "object": row},
            {"subject": sensor, "predicate": "monitors", "object": root},
        ],
        "timeseries_records": records,
        "events": events,
        "daily_reports": [],
    }
    in_window_records = [r for r in records if start <= datetime.fromisoformat(r["timestamp"]) <= end]
    direction = trend_label(daily_means)
    shape = trend_shape(daily_means)
    expected_answer = {
        "normalized_values": {
            metric: {
                "daily_means": daily_means,
                "mean": round(sum(daily_means) / len(daily_means), 2),
                "latest": daily_means[-1],
                "unit": unit,
            }
        },
        "trend": {
            "label": direction,
            "net_change_direction": direction,
            "shape": shape,
            "daily_means": daily_means,
        },
        "events": events,
        "summary_facts": [
            f"sensor={sensor}",
            f"crop={crop}",
            f"daily_means={daily_means}",
            f"trend={direction}",
            f"event_count={len(events)}",
        ],
    }
    expected_evidence = {
        "record_ids": [r["record_id"] for r in in_window_records],
        "event_ids": [e["event_id"] for e in events],
    }
    query_spec = {
        "target_object_ids": [root, sensor],
        "metrics": [metric],
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "aggregations": ["mean", "latest", "trend", "daily_mean"],
        "required_units": {metric: unit},
    }
    task = base_gold(
        task_id=task_id,
        task_type="memory_query",
        diff=diff,
        prompt=prompt,
        initial_state=initial_state,
    )
    task.update({
        "query_spec": query_spec,
        "expected_answer": expected_answer,
        "expected_evidence": expected_evidence,
        "expected_outcome": {"answer": deepcopy(expected_answer), "evidence": deepcopy(expected_evidence)},
        "forbidden_side_effects": ["create_scene", "add_object", "delete_object", "modify_timeseries", "invent_record"],
    })
    return task, {
        "crop": crop,
        "scenario_family": "bounded_timeseries_with_interference",
        "source_basis": "WUR-AGC-scenario-informed-synthetic",
    }


BUILDERS = (
    ("scene_construction", scene_task),
    ("asset_routing", asset_task),
    ("data_binding", data_binding_task),
    ("rule_repair", repair_task),
    ("memory_query", memory_task),
)


def build_all() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    tasks: list[dict[str, Any]] = []
    catalog: list[dict[str, str]] = []
    review_order = 0
    for task_type, builder in BUILDERS:
        for index in range(1, 61):
            task, metadata = builder(index)
            tasks.append(task)
            review_order += 1
            catalog.append({
                "review_order": str(review_order),
                "task_id": task["task_id"],
                "task_type": task_type,
                "difficulty": task["difficulty"],
                "crop": metadata["crop"],
                "scenario_family": metadata["scenario_family"],
                "source_basis": metadata["source_basis"],
                "draft_status": "pending_double_blind_review",
            })
    return tasks, catalog


def write_catalog(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "review_order", "task_id", "task_type", "difficulty", "crop",
        "scenario_family", "source_basis", "draft_status",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_review_queue(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "review_order", "task_id", "task_type", "difficulty",
        "reviewer_a_decision", "reviewer_a_comments",
        "reviewer_b_decision", "reviewer_b_comments",
        "disagreement", "adjudicator_decision", "adjudicator_comments",
        "final_status", "freeze_eligible",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "review_order": row["review_order"],
                "task_id": row["task_id"],
                "task_type": row["task_type"],
                "difficulty": row["difficulty"],
                "reviewer_a_decision": "",
                "reviewer_a_comments": "",
                "reviewer_b_decision": "",
                "reviewer_b_comments": "",
                "disagreement": "",
                "adjudicator_decision": "",
                "adjudicator_comments": "",
                "final_status": "pending",
                "freeze_eligible": "false",
            })


def legacy_prompt_hashes() -> set[str]:
    if not LEGACY_PUBLIC.exists():
        return set()
    hashes = set()
    for line in LEGACY_PUBLIC.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        prompt = json.loads(line).get("prompt", "").strip()
        hashes.add(hashlib.sha256(prompt.encode("utf-8")).hexdigest())
    return hashes


def main() -> None:
    tasks, catalog = build_all()
    public = [public_view(task) for task in tasks]

    public_path = OUT / "external300_public_inputs.jsonl"
    gold_path = OUT / "external300_gold_draft.jsonl"
    catalog_path = OUT / "external300_catalog.csv"
    review_path = OUT / "external300_review_queue.csv"
    write_jsonl(public_path, public)
    write_jsonl(gold_path, tasks)
    write_catalog(catalog_path, catalog)
    write_review_queue(review_path, catalog)

    by_type = Counter(task["task_type"] for task in tasks)
    by_difficulty = {
        task_type: Counter(task["difficulty"] for task in tasks if task["task_type"] == task_type)
        for task_type, _builder in BUILDERS
    }
    current_prompt_hashes = {
        hashlib.sha256(task["prompt"].strip().encode("utf-8")).hexdigest() for task in tasks
    }
    overlap = sorted(current_prompt_hashes & legacy_prompt_hashes())
    files = {}
    support_paths = [
        OUT / "external300_schema.json",
        OUT / "validate_external300.py",
        OUT / "audit_gold_satisfiability.py",
        OUT / "README.md",
        OUT / "SOURCES.md",
        OUT / "ANNOTATION_GUIDELINE.md",
        OUT / "PREREGISTRATION_DRAFT.md",
        OUT / "PUBLIC_DATA_IMPORT_PLAN.md",
        OUT / "PHASE5_EXECUTION_PROMPT.md",
        OUT / "public_data_registry.csv",
    ]
    for path in (public_path, gold_path, catalog_path, review_path, *support_paths):
        if not path.exists():
            continue
        files[path.name] = {"sha256": sha256(path), "bytes": path.stat().st_size}

    manifest = {
        "benchmark_name": "External300 candidate",
        "benchmark_version": "external300-candidate-v0.1",
        "status": "CANDIDATE_NOT_FROZEN_NOT_EVALUATED",
        "generated_at": datetime.now(TZ).isoformat(),
        "generator": "generate_external300.py",
        "generator_sha256": sha256(Path(__file__)),
        "task_count": len(tasks),
        "counts_by_type": dict(sorted(by_type.items())),
        "difficulty_by_type": {
            task_type: dict(sorted(counts.items())) for task_type, counts in by_difficulty.items()
        },
        "annotation_version": ANNOTATION_VERSION,
        "review_status": "pending_double_blind_human_review",
        "method_execution_status": "NOT_RUN",
        "legacy_test_v2_exact_prompt_overlap_count": len(overlap),
        "legacy_test_v2_exact_prompt_overlap_hashes": overlap,
        "record_provenance": {
            "memory_timeseries": "deterministic synthetic; public-dataset scenario informed; not copied raw WUR observations",
            "semantic_sources": SOURCE_REGISTRY,
        },
        "files": files,
        "freeze_requirements": [
            "two independent reviewers complete every row",
            "disagreements adjudicated by a third person",
            "all accepted gold rows set to approved",
            "public and gold files regenerated and sealed with SHA-256",
            "methods, prompts, model/provider, budget and evaluator frozen before first run",
            "no method output inspected during annotation",
        ],
    }
    manifest_path = OUT / "external300_manifest_draft.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "tasks": len(tasks),
        "counts_by_type": manifest["counts_by_type"],
        "difficulty_by_type": manifest["difficulty_by_type"],
        "exact_prompt_overlap": len(overlap),
        "public_sha256": files[public_path.name]["sha256"],
        "gold_sha256": files[gold_path.name]["sha256"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
