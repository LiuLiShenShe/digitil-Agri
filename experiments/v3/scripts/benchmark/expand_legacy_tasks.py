#!/usr/bin/env python3
"""Expand the 30 legacy benchmark tasks into typed gold for experiments/v3.

Reads `experiments/tasks/main_experiment_tasks.json` (30 seeds) and produces
typed, versioned benchmark files under `experiments/v3/benchmark/`:

  schema.json               (already present; validated here)
  train.jsonl               legacy T01-T18 -> typed gold   (18 tasks)
  dev.jsonl                 legacy T19-T26 -> typed gold   (8 tasks)
  test_public_inputs.jsonl  legacy T27-T30 + new blind tasks (prompt only, NO gold)
  test_gold.sealed.jsonl    gold for the test split (frozen, sha256 recorded in manifest)

Objective: every task carries REAL typed gold (nodes/edges/bindings/constraints/
equivalence_groups/critical_objects/allowed_variants). Repair tasks (legacy
T19-T24) receive a real `initial_state` describing the faulty scene, plus a
`goal_state` and `critical_objects` that must actually be modified.

The test gold is sealed: `test_gold.sealed.jsonl` is written once and its SHA-256
is recorded in `benchmark_manifest.json`. Agents executing test tasks see only
`test_public_inputs.jsonl` (prompt + public fields), never the gold.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
LEGACY_TASKS = ROOT / "experiments" / "tasks" / "main_experiment_tasks.json"
SHARED_KNOWLEDGE = ROOT / "experiments" / "config" / "shared_knowledge.json"
OUT_DIR = ROOT / "experiments" / "v3" / "benchmark"

CATEGORY_MAP = {
    "场景构建": "scene_build",
    "资产路由": "asset_route",
    "数据绑定": "data_bind",
    "规则修正": "repair",
    "历史查询": "memory_query",
}

OBJECT_TYPE_FROM_ASSET = {
    "greenhouse": "Greenhouse",
    "plot": "Plot",
    "croprow": "CropRow",
    "row": "CropRow",
    "tomato": "Plant",
    "strawberry": "Plant",
    "corn": "Plant",
    "wheat": "Plant",
    "rice": "Plant",
    "lettuce": "Plant",
    "pumpkin": "Plant",
    "seedling": "Plant",
    "sensor": "Sensor",
    "weather_station": "WeatherStation",
    "camera": "Camera",
    "irrigation": "Irrigation",
    "pump": "Pump",
    "water_tower": "Pump",
    "device": "Device",
    "trait": "Trait",
    "event": "Event",
    "asset": "Asset",
    "report_source": "ReportSource",
    "monitoring_point": "Plot",
    "sensor_group": "Sensor",
}

# asset_key -- the object type used in the system's shared knowledge
ASSET_KEYS = {
    "Greenhouse": "greenhouse",
    "Plot": "plot",
    "CropRow": "cropRow",
    "Plant": "plant",
    "Sensor": "sensor",
    "Camera": "camera",
    "WeatherStation": "weather_station",
    "Irrigation": "irrigation",
    "Pump": "pump",
    "Device": "device",
    "Trait": "trait",
    "Event": "event",
    "Asset": "asset",
    "ReportSource": "report_source",
}


def node(oid: str, otype: str, *, role: str = "entity", parent: str | None = None,
         count: int = 1, key_attrs: dict[str, Any] | None = None, asset_policy: str | None = None) -> dict[str, Any]:
    n = {"id": oid, "type": otype, "role": role, "count": count}
    if parent:
        n["parent"] = parent
    if key_attrs:
        n["key_attrs"] = key_attrs
    if asset_policy:
        n["asset_policy"] = asset_policy
    return n


def edge(subject: str, predicate: str, obj: str) -> dict[str, str]:
    return {"subject": subject, "predicate": predicate, "object": obj}


def binding(subject: str, target: str, btype: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    b = {"subject": subject, "target": target, "type": btype}
    if metadata:
        b["metadata"] = metadata
    return b


def difficulty_for(task: dict[str, Any]) -> str:
    rules = set(task.get("rules", []))
    if "R10" in rules:
        return "hard"
    if "R9" in rules or "R4" in rules:
        return "medium"
    return "easy"


def parse_count(prompt: str, label: str) -> int | None:
    """Extract an integer immediately before/with a label in the Chinese prompt."""
    import re
    m = re.search(r"(\d+)\s*[株组个套台例行项区].*?" + re.escape(label), prompt)
    if m:
        return int(m.group(1))
    return None


# ---------------------------------------------------------------------------
# Repair tasks: real faulty initial_state, goal_state, critical_objects.
# These are hand-authored (decidable) faulty scenes. category -> repair.
# ---------------------------------------------------------------------------

def build_repair_initial(legacy: dict[str, Any]) -> dict[str, Any]:
    """Return (initial_state, goal_state, critical_objects) for repair tasks."""
    tid = legacy["task_id"]
    prompt = legacy["prompt"]
    if tid in {"T19", "T20", "T21", "T22", "T23", "T24"}:
        pass  # handled below

    if tid == "T19":  # Sensor_01 no monitoring target -> bind to Greenhouse_A
        initial = {
            "id": "scene_T19",
            "objects": [
                {"id": "Greenhouse_A", "type": "Greenhouse", "location": {"x": 0, "y": 0, "z": 0}, "area": 240.0},
                {"id": "Sensor_01", "type": "Sensor", "monitoring_target": None, "location": "Greenhouse_A",
                 "metrics": ["temperature", "humidity", "co2", "light"]},
            ],
            "bindings": [],
        }
        goal = {
            "id": "scene_T19",
            "objects": [
                {"id": "Greenhouse_A", "type": "Greenhouse", "location": {"x": 0, "y": 0, "z": 0}, "area": 240.0},
                {"id": "Sensor_01", "type": "Sensor", "monitoring_target": "Greenhouse_A", "location": "Greenhouse_A",
                 "metrics": ["temperature", "humidity", "co2", "light"]},
            ],
            "bindings": [binding("Sensor_01", "Greenhouse_A", "sensor_bind",
                                 {"metrics": ["temperature", "humidity", "co2", "light"], "unit": "celsius"})],
        }
        critical = ["Sensor_01"]
        constraints = [
            "Sensor_01 must gain a monitoring_target equal to a present Greenhouse object",
            "No new fatal rule conflict shall be introduced (R2 data binding legal)",
        ]
        allowed_variants = [
            "Sensor_01 may be bound to any Greenhouse present in the scene",
            "The monitoring_target SHALL be a Greenhouse; binding type is sensor_bind",
        ]
        return initial, goal, critical, constraints, allowed_variants

    if tid == "T20":  # crop row Row_05 out of bounds -> recompute layout
        # Each Row_xx is ONE concrete CropRow instance (count=1). The earlier
        # `count: 5` was a copy/paste error from the required_nodes pattern (where
        # it means 5 plants per row); on a concrete scene object it inflated the
        # goal-state expansion to 25 and broke even gold-self evaluation.
        initial = {
            "id": "scene_T20",
            "objects": [
                {"id": "Plot_A", "type": "Plot", "bounds": {"x_min": 0, "x_max": 30, "z_min": 0, "z_max": 8}},
                {"id": "Row_01", "type": "CropRow", "location": {"x": 5, "z": 1}, "count": 1},
                {"id": "Row_02", "type": "CropRow", "location": {"x": 10, "z": 2}, "count": 1},
                {"id": "Row_03", "type": "CropRow", "location": {"x": 15, "z": 3}, "count": 1},
                {"id": "Row_04", "type": "CropRow", "location": {"x": 20, "z": 4}, "count": 1},
                {"id": "Row_05", "type": "CropRow", "location": {"x": 29, "z": 9}, "count": 1},  # z=9 > z_max=8
            ],
            "bindings": [],
        }
        goal = {
            "id": "scene_T20",
            "objects": [
                {"id": "Plot_A", "type": "Plot", "bounds": {"x_min": 0, "x_max": 30, "z_min": 0, "z_max": 8}},
                {"id": "Row_01", "type": "CropRow", "location": {"x": 5, "z": 1}, "count": 1},
                {"id": "Row_02", "type": "CropRow", "location": {"x": 10, "z": 2}, "count": 1},
                {"id": "Row_03", "type": "CropRow", "location": {"x": 15, "z": 3}, "count": 1},
                {"id": "Row_04", "type": "CropRow", "location": {"x": 20, "z": 4}, "count": 1},
                {"id": "Row_05", "type": "CropRow", "location": {"x": 24, "z": 6}, "count": 1},
            ],
            "bindings": [],
        }
        critical = ["Row_05"]
        constraints = [
            "Row_05's new location MUST lie strictly within Plot_A bounds (0<=x<=30, 0<=z<=8)",
            "No row may overlap another row's location",
        ]
        allowed_variants = [
            "Row_05 may be placed at any in-bounds, non-overlapping location",
        ]
        return initial, goal, critical, constraints, allowed_variants

    if tid == "T21":  # 6 tomato plants no belongs_to -> assign to nearest row
        initial = {
            "id": "scene_T21",
            "objects": [
                {"id": "Greenhouse_A", "type": "Greenhouse", "location": {"x": 0, "y": 0, "z": 0}},
                {"id": "Row_01", "type": "CropRow", "location": {"x": 5, "z": 1}},
                {"id": "Row_02", "type": "CropRow", "location": {"x": 10, "z": 2}},
                {"id": "tomato_01", "type": "Plant", "belongs_to": None, "location": {"x": 5.5, "z": 1.2}},
                {"id": "tomato_02", "type": "Plant", "belongs_to": None, "location": {"x": 5.5, "z": 1.2}},
                {"id": "tomato_03", "type": "Plant", "belongs_to": None, "location": {"x": 5.5, "z": 1.2}},
                {"id": "tomato_04", "type": "Plant", "belongs_to": None, "location": {"x": 10.5, "z": 2.2}},
                {"id": "tomato_05", "type": "Plant", "belongs_to": None, "location": {"x": 10.5, "z": 2.2}},
                {"id": "tomato_06", "type": "Plant", "belongs_to": None, "location": {"x": 10.5, "z": 2.2}},
            ],
            "bindings": [],
        }
        goal = {
            "id": "scene_T21",
            "objects": [
                {"id": "Greenhouse_A", "type": "Greenhouse", "location": {"x": 0, "y": 0, "z": 0}},
                {"id": "Row_01", "type": "CropRow", "location": {"x": 5, "z": 1}},
                {"id": "Row_02", "type": "CropRow", "location": {"x": 10, "z": 2}},
                {"id": "tomato_01", "type": "Plant", "belongs_to": "Row_01", "location": {"x": 5.5, "z": 1.2}},
                {"id": "tomato_02", "type": "Plant", "belongs_to": "Row_01", "location": {"x": 5.5, "z": 1.2}},
                {"id": "tomato_03", "type": "Plant", "belongs_to": "Row_01", "location": {"x": 5.5, "z": 1.2}},
                {"id": "tomato_04", "type": "Plant", "belongs_to": "Row_02", "location": {"x": 10.5, "z": 2.2}},
                {"id": "tomato_05", "type": "Plant", "belongs_to": "Row_02", "location": {"x": 10.5, "z": 2.2}},
                {"id": "tomato_06", "type": "Plant", "belongs_to": "Row_02", "location": {"x": 10.5, "z": 2.2}},
            ],
            "bindings": [],
        }
        critical = ["tomato_01", "tomato_02", "tomato_03", "tomato_04", "tomato_05", "tomato_06"]
        constraints = [
            "Every unbound tomato SHALL receive a belongs_to pointing to the nearest crop row",
            "R1 hierarchy (crop row contains plant) must be legal and not duplicated",
        ]
        allowed_variants = [
            "tomato_01..03 belong to Row_01; tomato_04..06 belong to Row_02 (nearest by location)",
        ]
        return initial, goal, critical, constraints, allowed_variants

    if tid == "T22":  # Camera_02 no pose/observe target -> add target/location/FOV
        initial = {
            "id": "scene_T22",
            "objects": [
                {"id": "Greenhouse_A", "type": "Greenhouse", "location": {"x": 0, "y": 0, "z": 0}},
                {"id": "Camera_02", "type": "Camera", "pose": None, "observes": None, "fov": None},
            ],
            "bindings": [],
        }
        goal = {
            "id": "scene_T22",
            "objects": [
                {"id": "Greenhouse_A", "type": "Greenhouse", "location": {"x": 0, "y": 0, "z": 0}},
                {"id": "Camera_02", "type": "Camera", "pose": {"position": [1, 3, 1], "orientation": [0, 90, 0]},
                 "observes": "Greenhouse_A", "fov": 60},
            ],
            "bindings": [],
        }
        critical = ["Camera_02"]
        constraints = [
            "Camera_02 SHALL gain a pose, an observes target (a present Greenhouse/CropRow), and an fov",
        ]
        allowed_variants = [
            "Camera_02 may observe Greenhouse_A or any present CropRow",
        ]
        return initial, goal, critical, constraints, allowed_variants

    if tid == "T23":  # trait height=42.3 missing unit/timestamp/binding object
        initial = {
            "id": "scene_T23",
            "objects": [
                {"id": "tomato_10", "type": "Plant", "location": {"x": 5, "z": 1}},
            ],
            "traits": [{"id": "trait_h_42", "metric": "height", "value": 42.3, "unit": None, "timestamp": None,
                        "bound_to": None}],
        }
        goal = {
            "id": "scene_T23",
            "objects": [
                {"id": "tomato_10", "type": "Plant", "location": {"x": 5, "z": 1}},
            ],
            "traits": [{"id": "trait_h_42", "metric": "height", "value": 42.3, "unit": "cm", "timestamp": "sample_time",
                        "bound_to": "tomato_10"}],
            "bindings": [binding("trait_h_42", "tomato_10", "trait_bind", {"metric": "height", "unit": "cm"})],
        }
        critical = ["trait_h_42"]
        constraints = [
            "trait_h_42 SHALL gain unit=cm, a sampling timestamp, and a binding to a present target plant",
        ]
        allowed_variants = [
            "trait_h_42 must bind to a Plant that exists in the scene",
        ]
        return initial, goal, critical, constraints, allowed_variants

    if tid == "T24":  # pump wrongly bound to tomato asset -> use irrigation asset or placeholder
        initial = {
            "id": "scene_T24",
            "objects": [
                {"id": "Greenhouse_A", "type": "Greenhouse", "location": {"x": 0, "y": 0, "z": 0}},
                {"id": "pump_01", "type": "Pump", "asset_key": "tomato", "asset_policy": None},
            ],
            "bindings": [{"subject": "pump_01", "target": "tomato", "type": "asset",
                          "metadata": {"policy": "wrong_asset"}}],
        }
        goal = {
            "id": "scene_T24",
            "objects": [
                {"id": "Greenhouse_A", "type": "Greenhouse", "location": {"x": 0, "y": 0, "z": 0}},
                {"id": "pump_01", "type": "Pump", "asset_key": "irrigation", "asset_policy": "existing_asset"},
            ],
            "bindings": [binding("pump_01", "irrigation", "asset", {"policy": "existing_asset"})],
        }
        critical = ["pump_01"]
        constraints = [
            "pump_01 SHALL no longer use a plant asset; it SHALL use an irrigation/compatible asset or a placeholder task",
            "R4 asset type consistency must hold; R9 missing-asset rule must be respected if placing a placeholder",
        ]
        allowed_variants = [
            "pump_01 may bind to an irrigation asset OR a placeholder + generation task",
        ]
        return initial, goal, critical, constraints, allowed_variants

    # Fallback for unexpected repair task (should not occur for legacy 30)
    raise ValueError(f"no hand-authored repair initial_state for {tid}")


# ---------------------------------------------------------------------------
# Generic expansion for non-repair tasks
# ---------------------------------------------------------------------------

def scene_objects_from_prompt(prompt: str, legacy: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive typed required_nodes from the (Chinese) building-prompt text."""
    nodes: list[dict[str, Any]] = []
    greenhouse = {"id": "greenhouse_root", "type": "Greenhouse", "role": "root", "count": 1}
    # Only add greenhouse root if the prompt mentions a greenhouse/温/棚.
    if any(k in prompt for k in ["温室", "大棚", "棚", "Greenhouse"]):
        nodes.append(greenhouse)

    known = [
        ("番茄", "tomato", "Plant", 20), ("草莓", "strawberry", "Plant", 6),
        ("玉米", "corn", "Plant", 40), ("生菜", "lettuce", "Plant", 32),
        ("果树", "tree", "Plant", 5), ("食用菌", "mushroom", "Plant", 24),
        ("气象站", "weather_station", "WeatherStation", 1), ("水泵", "pump", "Pump", 1),
        ("滴灌", "irrigation", "Irrigation", 1), ("微喷", "irrigation", "Irrigation", 1),
        ("摄像头", "camera", "Camera", 1), ("传感器", "sensor", "Sensor", 1),
        ("苗床", "seedbed", "CropRow", 6), ("栽培架", "shelf", "CropRow", 4),
        ("培养架", "shelf", "CropRow", 4), ("作物行", "cropRow", "CropRow", 4),
        ("行", "cropRow", "CropRow", 1),
    ]
    seen = set()
    for label, asset, otype, default_count in known:
        if label in prompt and otype not in seen:
            count = parse_count(prompt, label) or default_count
            oid = f"{asset}_01" if count <= 1 else f"{asset}_01"
            # For many-instance objects we keep count>1 and append suffixed nodes.
            nodes.append(node(oid, otype, role="entity", count=count))
            seen.add(otype)
    return nodes


def expand_task(legacy: dict[str, Any]) -> dict[str, Any]:
    """Convert one legacy task record into typed gold."""
    category = CATEGORY_MAP[legacy["category"]]
    tid = legacy["task_id"]
    difficulty = difficulty_for(legacy)
    out: dict[str, Any] = {
        "task_id": tid,
        "category": category,
        "difficulty": difficulty,
        "prompt": legacy["prompt"],
        "required_nodes": [],
        "optional_nodes": [],
        "forbidden_nodes": [],
        "required_edges": [],
        "required_bindings": [],
        "constraints": [],
        "equivalence_groups": [],
        "goal_state": {},
        "critical_objects": [],
        "allowed_variants": [],
    }

    if category == "repair":
        initial, goal, critical, constraints, variants = build_repair_initial(legacy)
        out["initial_state"] = initial
        out["goal_state"] = goal
        out["critical_objects"] = critical
        out["constraints"] = constraints
        out["allowed_variants"] = variants
        # Derive required_nodes/edges from initial objects for the gold graph.
        for obj in initial.get("objects", []):
            out["required_nodes"].append(node(obj["id"], obj["type"], role="entity", count=1))
        return out

    # Non-repair: derive from prompt.
    nodes = scene_objects_from_prompt(legacy["prompt"], legacy)
    out["required_nodes"] = nodes

    # Relations: use the legacy required_relations count as an expected edge budget,
    # but we emit concrete typed edges for the greenhouse contains relationships.
    if any(n["type"] == "Greenhouse" for n in nodes):
        for n in nodes:
            if n["id"] != "greenhouse_root" and n["type"] not in {"CropRow", "Plot"}:
                out["required_edges"].append(edge("greenhouse_root", "contains", n["id"]))
    for n in nodes:
        if n["type"] == "CropRow":
            out["required_edges"].append(edge("greenhouse_root", "contains", n["id"]))
    # Equivalence groups: plants of the same type are interchangeable.
    plant_ids = [n["id"] for n in nodes if n["type"] == "Plant"]
    if len(plant_ids) > 0:
        out["equivalence_groups"].append("|".join(plant_ids))

    return out


def load_shared() -> dict[str, Any]:
    with SHARED_KNOWLEDGE.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with LEGACY_TASKS.open("r", encoding="utf-8") as fh:
        legacy_rows = json.load(fh)
    if not isinstance(legacy_rows, list) or len(legacy_rows) != 30:
        print(f"[error] expected 30 legacy tasks, got {len(legacy_rows)}", file=sys.stderr)
        return 1

    all_tasks = [expand_task(t) for t in legacy_rows]
    train = [t for t in all_tasks if t["task_id"] in {f"T{i:02d}" for i in range(1, 19)}]
    dev = [t for t in all_tasks if t["task_id"] in {f"T{i:02d}" for i in range(19, 27)}]
    test_ids = {f"T{i:02d}" for i in range(27, 31)}
    test = [t for t in all_tasks if t["task_id"] in test_ids]

    # Fresh blind test tasks (prompt only; gold authoring deferred to annotation).
    blind_prompts = [
        {
            "task_id": "T031", "category": "scene_build", "difficulty": "medium",
            "prompt": "构建一个 20m x 6m 的黄瓜温室，包含 3 行作物、18 株黄瓜、1 个气象站、1 套滴灌设备和 1 个摄像头。",
        },
        {
            "task_id": "T032", "category": "data_bind", "difficulty": "medium",
            "prompt": "将温室内 2 个光照传感器绑定到对应作物行，并为每株关键番茄绑定叶面积指数(LI)与采收日期事件，含单位与时间戳。",
        },
        {
            "task_id": "T033", "category": "repair", "difficulty": "hard",
            "prompt": "输入一个水泵 WaterPump_B 错误关联到生菜植物的场景，系统需要识别资产类型不匹配并改为灌溉设备资产或占位任务。",
        },
        {
            "task_id": "T034", "category": "memory_query", "difficulty": "medium",
            "prompt": "查询番茄温室最近 3 天 CO2 浓度趋势，返回传感器、日均值、异常事件与关联作物行。",
        },
        {
            "task_id": "T035", "category": "asset_route", "difficulty": "medium",
            "prompt": "构建辣椒温室，6 株重点辣椒使用高保真资产，14 株背景辣椒使用轻量 GLB，缺失补光设备生成占位任务。",
        },
    ]
    # public test inputs = legacy test tasks + blind tasks (NO gold)
    PUBLIC_FIELDS = {"task_id", "category", "difficulty", "prompt"}
    public_test = []
    for t in test:
        public_test.append({k: v for k, v in t.items() if k in PUBLIC_FIELDS})
    for bp in blind_prompts:
        public_test.append({k: v for k, v in bp.items() if k in PUBLIC_FIELDS})

    write_jsonl(OUT_DIR / "train.jsonl", train)
    write_jsonl(OUT_DIR / "dev.jsonl", dev)
    write_jsonl(OUT_DIR / "test_public_inputs.jsonl", public_test)
    # test gold: legacy test gold (typed) + blind gold endpoints stubbed (annotation TODO)
    gold = []
    for t in test:
        gold.append({k: v for k, v in t.items() if k != "initial_state"})  # keep gold fields
    for bp in blind_prompts:
        gold.append({**bp, "goald_basis": "TODO_ANNOTATION",
                     "note": "blind test gold authored during annotation (T033 is repair; needs real initial_state)"})
    write_jsonl(OUT_DIR / "test_gold.sealed.jsonl", gold)

    # Write / refresh manifest with SHA-256.
    manifest_path = OUT_DIR / "benchmark_manifest.json"
    manifest = {
        "benchmark_version": "v1",
        "created": "2026-08-04",
        "splits": {
            "train": {"file": "train.jsonl", "tasks": len(train), "sha256": sha256_of(OUT_DIR / "train.jsonl")},
            "dev": {"file": "dev.jsonl", "tasks": len(dev), "sha256": sha256_of(OUT_DIR / "dev.jsonl")},
            "test_public_inputs": {"file": "test_public_inputs.jsonl", "tasks": len(public_test),
                                   "sha256": sha256_of(OUT_DIR / "test_public_inputs.jsonl")},
            "test_gold_sealed": {"file": "test_gold.sealed.jsonl", "tasks": len(gold),
                                 "sha256": sha256_of(OUT_DIR / "test_gold.sealed.jsonl")},
        },
        "note": "Test gold is sealed+frozen after annotation adepts final decision. Rebuild bumps benchmark_version and full rerun.",
    }
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    print(f"train={len(train)} dev={len(dev)} test_public={len(public_test)} test_gold={len(gold)}")
    print(f"manifest sha256s updated; version={manifest['benchmark_version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
