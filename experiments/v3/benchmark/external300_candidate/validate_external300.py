#!/usr/bin/env python3
"""Static integrity checks for the External300 candidate benchmark.

The validator performs data/schema/provenance checks only.  It does not import or
execute KAFarmTwin, SingleAgent, an LLM client, or the formal experiment runner.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
PUBLIC = ROOT / "external300_public_inputs.jsonl"
GOLD = ROOT / "external300_gold_draft.jsonl"
CATALOG = ROOT / "external300_catalog.csv"
REVIEW = ROOT / "external300_review_queue.csv"
MANIFEST = ROOT / "external300_manifest_draft.json"
SCHEMA = ROOT / "external300_schema.json"
LEGACY_PUBLIC = REPO_ROOT / "experiments/v3/benchmark/test_v2/test_v2_public_inputs.jsonl"
LEGACY_GOLD = REPO_ROOT / "experiments/v3/benchmark/test_v2/test_v2_gold.jsonl"

TASK_TYPES = {
    "scene_construction": "SC",
    "asset_routing": "AR",
    "data_binding": "DB",
    "rule_repair": "RR",
    "memory_query": "MQ",
}
EXPECTED_PUBLIC_KEYS = {
    "task_id", "task_type", "difficulty", "prompt", "policy_ref", "initial_state",
}
GOLD_ONLY_TOP_LEVEL = {
    "required_nodes", "required_edges", "required_bindings", "critical_objects",
    "equivalence_groups", "fatal_constraints", "forbidden_side_effects",
    "allowed_side_effects", "allowed_variants", "expected_outcome", "graph_outcome",
    "expected_answer", "expected_evidence", "query_spec", "goal_state", "review_status",
    "annotation_version",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name}:{number}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path.name}:{number}: expected object")
        rows.append(value)
    return rows


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm_prompt(value: str) -> str:
    value = value.lower()
    value = re.sub(r"\d+(?:\.\d+)?", "#", value)
    value = re.sub(r"[\s，。；、,:：;()（）=_\-]", "", value)
    return value


def object_map(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("id")): item
        for item in (state.get("objects") or [])
        if isinstance(item, dict) and item.get("id")
    }


def _schema_type_matches(value: Any, expected: str) -> bool:
    checks = {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
        "boolean": lambda item: isinstance(item, bool),
        "null": lambda item: item is None,
    }
    return checks.get(expected, lambda _item: True)(value)


def _resolve_schema_ref(root_schema: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise ValueError(f"unsupported external schema ref: {reference}")
    node: Any = root_schema
    for part in reference[2:].split("/"):
        node = node[part.replace("~1", "/").replace("~0", "~")]
    if not isinstance(node, dict):
        raise ValueError(f"schema ref does not resolve to an object: {reference}")
    return node


def _validate_schema_subset(
    value: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
) -> list[str]:
    """Validate the Draft-07 keywords used by external300_schema.json.

    This dependency-free fallback intentionally supports only the schema keywords
    present in this repository artifact: $ref, type, required, properties, enum,
    const, pattern, minLength, minimum, min/maxItems, items, allOf and if/then/else.
    """
    issues: list[str] = []
    if "$ref" in schema:
        return _validate_schema_subset(value, _resolve_schema_ref(root_schema, schema["$ref"]), root_schema, path)

    expected_types = schema.get("type")
    if expected_types is not None:
        options = expected_types if isinstance(expected_types, list) else [expected_types]
        if not any(_schema_type_matches(value, option) for option in options):
            return [f"{path}: expected type {options}, got {type(value).__name__}"]

    if "enum" in schema and value not in schema["enum"]:
        issues.append(f"{path}: value {value!r} not in enum {schema['enum']!r}")
    if "const" in schema and value != schema["const"]:
        issues.append(f"{path}: value {value!r} != const {schema['const']!r}")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < int(schema["minLength"]):
            issues.append(f"{path}: string shorter than minLength={schema['minLength']}")
        if "pattern" in schema and re.search(str(schema["pattern"]), value) is None:
            issues.append(f"{path}: string does not match pattern {schema['pattern']!r}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            issues.append(f"{path}: number below minimum={schema['minimum']}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < int(schema["minItems"]):
            issues.append(f"{path}: array shorter than minItems={schema['minItems']}")
        if "maxItems" in schema and len(value) > int(schema["maxItems"]):
            issues.append(f"{path}: array longer than maxItems={schema['maxItems']}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                issues.extend(_validate_schema_subset(item, item_schema, root_schema, f"{path}/{index}"))
    if isinstance(value, dict):
        for required_key in schema.get("required") or []:
            if required_key not in value:
                issues.append(f"{path}: missing required property {required_key!r}")
        for key, child_schema in (schema.get("properties") or {}).items():
            if key in value and isinstance(child_schema, dict):
                issues.extend(_validate_schema_subset(value[key], child_schema, root_schema, f"{path}/{key}"))

    for child_schema in schema.get("allOf") or []:
        issues.extend(_validate_schema_subset(value, child_schema, root_schema, path))
    if "if" in schema:
        condition_issues = _validate_schema_subset(value, schema["if"], root_schema, path)
        branch = schema.get("then") if not condition_issues else schema.get("else")
        if isinstance(branch, dict):
            issues.extend(_validate_schema_subset(value, branch, root_schema, path))
    return issues


def validate_schema(tasks: list[dict[str, Any]], errors: list[str]) -> str:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    try:
        from jsonschema import Draft7Validator
    except ImportError:
        for task in tasks:
            for issue in _validate_schema_subset(task, schema, schema, "<root>"):
                errors.append(f"{task.get('task_id')}: schema {issue}")
        return "builtin_draft07_subset"
    validator = Draft7Validator(schema)
    for task in tasks:
        for issue in validator.iter_errors(task):
            path = "/".join(str(part) for part in issue.path) or "<root>"
            errors.append(f"{task.get('task_id')}: schema {path}: {issue.message}")
    return "jsonschema.Draft7Validator"


def validate_graph_refs(task: dict[str, Any], errors: list[str]) -> None:
    task_id = task["task_id"]
    nodes = task.get("required_nodes") or []
    ids = {str(node.get("id")) for node in nodes}
    if len(ids) != len(nodes):
        errors.append(f"{task_id}: duplicate required node ids")
    for edge in task.get("required_edges") or []:
        if edge.get("subject") not in ids:
            errors.append(f"{task_id}: edge subject not in required_nodes: {edge.get('subject')}")
        if edge.get("object") not in ids:
            errors.append(f"{task_id}: edge object not in required_nodes: {edge.get('object')}")
    for binding in task.get("required_bindings") or []:
        if binding.get("subject") not in ids:
            errors.append(f"{task_id}: binding subject not in required_nodes: {binding.get('subject')}")
        if binding.get("type") in {"sensor_bind", "trait_bind"} and binding.get("target") not in ids:
            errors.append(f"{task_id}: semantic binding target not in required_nodes: {binding.get('target')}")


def validate_binding_task(task: dict[str, Any], errors: list[str]) -> None:
    task_id = task["task_id"]
    initial_ids = set(object_map(task.get("initial_state") or {}))
    timestamp_values = set()
    sensor_bind_count = 0
    trait_bind_count = 0
    for binding in task.get("required_bindings") or []:
        metadata = binding.get("metadata") or {}
        if binding.get("subject") not in initial_ids or binding.get("target") not in initial_ids:
            errors.append(f"{task_id}: binding does not use public initial-state ids")
        if not metadata.get("unit"):
            errors.append(f"{task_id}: binding missing unit")
        timestamp = metadata.get("timestamp")
        if not timestamp:
            errors.append(f"{task_id}: binding missing timestamp")
        else:
            timestamp_values.add(str(timestamp))
        if binding.get("type") == "sensor_bind":
            sensor_bind_count += 1
            if not metadata.get("metrics"):
                errors.append(f"{task_id}: sensor_bind missing metrics")
        elif binding.get("type") == "trait_bind":
            trait_bind_count += 1
            if not metadata.get("trait"):
                errors.append(f"{task_id}: trait_bind missing trait")
    if sensor_bind_count < 1 or trait_bind_count < 1:
        errors.append(f"{task_id}: expected both sensor_bind and trait_bind")
    if len(timestamp_values) != 1:
        errors.append(f"{task_id}: expected one public timestamp contract, got {sorted(timestamp_values)}")
    elif next(iter(timestamp_values)) not in task.get("prompt", ""):
        errors.append(f"{task_id}: gold timestamp is not declared in the public prompt")


def validate_repair_task(task: dict[str, Any], errors: list[str]) -> None:
    task_id = task["task_id"]
    initial = object_map(task.get("initial_state") or {})
    goal = object_map(task.get("goal_state") or {})
    critical = task.get("critical_objects") or []
    if len(critical) != 1:
        errors.append(f"{task_id}: evaluator_v2.3 repair contract requires exactly one critical object")
        return
    cid = critical[0]
    if set(initial) != set(goal):
        errors.append(f"{task_id}: repair goal must preserve the input object-id set")
    changed = {oid for oid in set(initial) & set(goal) if initial[oid] != goal[oid]}
    if changed != {cid}:
        errors.append(f"{task_id}: only the critical object may change, got {sorted(changed)}")
    if cid not in initial or cid not in goal:
        errors.append(f"{task_id}: critical object missing from initial or goal state")
        return
    target = str(goal[cid].get("asset_key") or "")
    source = str(initial[cid].get("asset_key") or "")
    if not target or target == source:
        errors.append(f"{task_id}: repair does not change asset_key")
    if source not in task.get("prompt", "") or target not in task.get("prompt", ""):
        errors.append(f"{task_id}: source/target asset classes must both be public in the prompt")
    bindings = task.get("required_bindings") or []
    if len(bindings) != 1 or (bindings[0].get("metadata") or {}).get("asset_key") != target:
        errors.append(f"{task_id}: required repair binding does not match goal asset_key")
    if task.get("allowed_variants") != [{
        "path": "replace_asset",
        "detail": "set critical object asset_key to the declared device asset",
    }]:
        errors.append(f"{task_id}: candidate repair must use the unambiguous direct-replacement contract")


def validate_memory_task(task: dict[str, Any], errors: list[str]) -> None:
    task_id = task["task_id"]
    query = task.get("query_spec") or {}
    metrics = query.get("metrics") or []
    if len(metrics) != 1:
        errors.append(f"{task_id}: evaluator_v2.3 answer shape requires one primary metric")
        return
    metric = metrics[0]
    start = datetime.fromisoformat(query.get("start_time"))
    end = datetime.fromisoformat(query.get("end_time"))
    state = task.get("initial_state") or {}
    records = [
        row for row in (state.get("timeseries_records") or [])
        if row.get("metric") == metric
        and start <= datetime.fromisoformat(str(row.get("timestamp"))) <= end
    ]
    if not records:
        errors.append(f"{task_id}: memory query has no in-window records")
        return
    days: dict[str, list[float]] = defaultdict(list)
    for row in records:
        days[str(row["timestamp"])[:10]].append(float(row["value"]))
    daily_means = [round(sum(days[day]) / len(days[day]), 2) for day in sorted(days)]
    expected_metric = ((task.get("expected_answer") or {}).get("normalized_values") or {}).get(metric) or {}
    if expected_metric.get("daily_means") != daily_means:
        errors.append(f"{task_id}: expected daily_means do not match the public records")
    expected_mean = round(sum(daily_means) / len(daily_means), 2)
    if float(expected_metric.get("mean", float("nan"))) != expected_mean:
        errors.append(f"{task_id}: expected mean does not match the public records")
    if float(expected_metric.get("latest", float("nan"))) != daily_means[-1]:
        errors.append(f"{task_id}: expected latest does not match the last daily mean")
    evidence = task.get("expected_evidence") or {}
    if set(evidence.get("record_ids") or []) != {str(row.get("record_id")) for row in records}:
        errors.append(f"{task_id}: record evidence is not exactly the in-window record set")
    window_events = [
        event for event in (state.get("events") or [])
        if start <= datetime.fromisoformat(str(event.get("timestamp"))) <= end
    ]
    if set(evidence.get("event_ids") or []) != {str(event.get("event_id")) for event in window_events}:
        errors.append(f"{task_id}: event evidence is not exactly the in-window event set")
    expected_events = (task.get("expected_answer") or {}).get("events") or []
    if expected_events != window_events:
        errors.append(f"{task_id}: expected events do not match public initial_state events")
    if task.get("required_nodes") or task.get("required_edges") or task.get("required_bindings"):
        errors.append(f"{task_id}: memory_query must not carry graph-construction gold")


def validate_manifest(errors: list[str]) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("status") != "CANDIDATE_NOT_FROZEN_NOT_EVALUATED":
        errors.append("manifest status must remain CANDIDATE_NOT_FROZEN_NOT_EVALUATED")
    if manifest.get("method_execution_status") != "NOT_RUN":
        errors.append("manifest must record method_execution_status=NOT_RUN")
    for filename, metadata in (manifest.get("files") or {}).items():
        path = ROOT / filename
        if not path.exists():
            errors.append(f"manifest file missing: {filename}")
            continue
        if metadata.get("sha256") != file_sha256(path):
            errors.append(f"manifest hash mismatch: {filename}")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    for path in (PUBLIC, GOLD, CATALOG, REVIEW, MANIFEST, SCHEMA):
        if not path.exists():
            errors.append(f"missing required artifact: {path.name}")
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        return 1

    try:
        public_rows = load_jsonl(PUBLIC)
        gold_rows = load_jsonl(GOLD)
        legacy_public = load_jsonl(LEGACY_PUBLIC)
        legacy_gold = load_jsonl(LEGACY_GOLD)
    except ValueError as exc:
        print(f"ERROR {exc}")
        return 1

    if len(public_rows) != 300 or len(gold_rows) != 300:
        errors.append(f"expected 300 public and 300 gold rows, got {len(public_rows)} and {len(gold_rows)}")
    public_ids = [row.get("task_id") for row in public_rows]
    gold_ids = [row.get("task_id") for row in gold_rows]
    if len(set(public_ids)) != len(public_ids) or len(set(gold_ids)) != len(gold_ids):
        errors.append("task ids must be unique")
    if public_ids != gold_ids:
        errors.append("public/gold task order or ids differ")

    gold_by_id = {row["task_id"]: row for row in gold_rows}
    for public in public_rows:
        task_id = str(public.get("task_id"))
        gold = gold_by_id.get(task_id)
        if set(public) != EXPECTED_PUBLIC_KEYS:
            errors.append(f"{task_id}: public keys differ from whitelist: {sorted(public)}")
        leaked = set(public) & GOLD_ONLY_TOP_LEVEL
        if leaked:
            errors.append(f"{task_id}: public top-level gold leakage: {sorted(leaked)}")
        if gold and public.get("initial_state") != gold.get("initial_state"):
            errors.append(f"{task_id}: public initial_state differs from gold input state")
        if gold and public.get("prompt") != gold.get("prompt"):
            errors.append(f"{task_id}: public/gold prompt differs")

    counts = Counter(row.get("task_type") for row in gold_rows)
    for task_type in TASK_TYPES:
        if counts[task_type] != 60:
            errors.append(f"{task_type}: expected 60 rows, got {counts[task_type]}")
        split = Counter(row.get("difficulty") for row in gold_rows if row.get("task_type") == task_type)
        if split != Counter({"easy": 15, "medium": 30, "hard": 15}):
            errors.append(f"{task_type}: wrong difficulty split {dict(split)}")

    prompts = [str(row.get("prompt") or "").strip() for row in gold_rows]
    if len(set(prompts)) != len(prompts):
        duplicates = [prompt for prompt, count in Counter(prompts).items() if count > 1]
        errors.append(f"duplicate prompts found: {duplicates[:3]}")
    legacy_prompts = [str(row.get("prompt") or "").strip() for row in legacy_public]
    exact_overlap = set(prompts) & set(legacy_prompts)
    if exact_overlap:
        errors.append(f"exact prompt overlap with frozen test_v2: {sorted(exact_overlap)}")
    for prompt in prompts:
        normalized = norm_prompt(prompt)
        for old_prompt in legacy_prompts:
            ratio = SequenceMatcher(None, normalized, norm_prompt(old_prompt)).ratio()
            if ratio >= 0.92:
                errors.append(f"near-copy of test_v2 wording (ratio={ratio:.3f}): {prompt[:80]}")
                break

    legacy_ids: set[str] = set()
    for row in legacy_gold:
        for key in ("required_nodes",):
            legacy_ids.update(str(item.get("id")) for item in (row.get(key) or []) if item.get("id"))
        legacy_ids.update(object_map(row.get("initial_state") or {}))
    candidate_id_owners: dict[str, set[str]] = defaultdict(set)
    for row in gold_rows:
        task_id = str(row.get("task_id"))
        for item in row.get("required_nodes") or []:
            if item.get("id"):
                candidate_id_owners[str(item["id"])].add(task_id)
        for object_id in object_map(row.get("initial_state") or {}):
            candidate_id_owners[object_id].add(task_id)
    cross_task_collisions = {
        object_id: owners for object_id, owners in candidate_id_owners.items() if len(owners) > 1
    }
    if cross_task_collisions:
        errors.append(f"object ids collide across External300 tasks: {list(cross_task_collisions)[:10]}")
    collision = set(candidate_id_owners) & legacy_ids
    if collision:
        errors.append(f"object-id overlap with test_v2: {sorted(collision)[:10]}")

    schema_mode = validate_schema(gold_rows, errors)
    for task in gold_rows:
        task_id = task["task_id"]
        expected_code = TASK_TYPES.get(task.get("task_type"))
        if not task_id.startswith(f"EXT-{expected_code}-"):
            errors.append(f"{task_id}: id prefix does not match task_type")
        if task.get("review_status") not in ("pending", "approved"):
            errors.append(f"{task_id}: review_status must be pending (draft) or approved (post unified directive 2026-08-24)")
        if task.get("annotation_version") != "v2":
            errors.append(f"{task_id}: annotation_version must remain v2 for evaluator compatibility")
        if task.get("task_type") != "memory_query":
            validate_graph_refs(task, errors)
        if task.get("task_type") == "data_binding":
            validate_binding_task(task, errors)
        elif task.get("task_type") == "rule_repair":
            validate_repair_task(task, errors)
        elif task.get("task_type") == "memory_query":
            validate_memory_task(task, errors)

    with CATALOG.open(encoding="utf-8", newline="") as handle:
        catalog_rows = list(csv.DictReader(handle))
    with REVIEW.open(encoding="utf-8", newline="") as handle:
        review_rows = list(csv.DictReader(handle))
    if len(catalog_rows) != 300 or [row["task_id"] for row in catalog_rows] != gold_ids:
        errors.append("catalog must contain the same 300 ordered task ids")
    if len(review_rows) != 300 or [row["task_id"] for row in review_rows] != gold_ids:
        errors.append("review queue must contain the same 300 ordered task ids")
    _post_directive = all(row.get("final_status") == "approved" and row.get("freeze_eligible") == "true"
                          and row.get("disagreement") == "false" for row in review_rows)
    if not _post_directive and any(row.get("final_status") != "pending" or row.get("freeze_eligible") != "false" for row in review_rows):
        errors.append("review queue must start pending and freeze_eligible=false")

    validate_manifest(errors)

    record_ids: list[str] = []
    for task in gold_rows:
        record_ids.extend(
            str(row.get("record_id"))
            for row in ((task.get("initial_state") or {}).get("timeseries_records") or [])
            if row.get("record_id")
        )
    if len(record_ids) != len(set(record_ids)):
        errors.append("memory record ids collide across tasks")

    summary = {
        "public_rows": len(public_rows),
        "gold_rows": len(gold_rows),
        "counts_by_type": dict(sorted(counts.items())),
        "exact_test_v2_prompt_overlap": len(exact_overlap),
        "schema_checked": True,
        "schema_mode": schema_mode,
        "errors": len(errors),
        "warnings": len(warnings),
        "freeze_ready": False,
        "reason": "review closed by author unified execution directive 2026-08-24 (author-reviewed only; NOT independent double-blind)",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    for warning in warnings:
        print(f"WARNING {warning}")
    for error in errors:
        print(f"ERROR {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
