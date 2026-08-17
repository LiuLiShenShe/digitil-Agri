"""Static Gold integrity audit (F-013).

Checks each task for the class of defect that invalidated test_v1: a task whose
prompt task-type contradicts its gold evaluation target. Runs as the pre-freeze
gate for test_v2, and on any candidate split/task set.

Checks (per task):
  1. task_type is a known type
  2. memory_query MUST NOT carry scene-building gold (required_nodes/edges with
     non-empty counts) and MUST have query_spec/expected_answer/expected_evidence
  3. graph types MUST NOT be evaluated purely as retrieval (must have a graph
     gold block when there are required nodes)
  4. annotation_version == 'v2' and review_status in the allowed set
  5. if review_status != 'approved', flag as not-ready (blocks freeze)
  6. prompt keyword consistency: e.g. a prompt asking to 'query/return/report'
     telemetry is a retrieval signal, conflicting with scene-build required_nodes
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from task_types import TASK_TYPES, task_type_of, requires_graph_gold, requires_query_gold

RETRIEVAL_HINTS = ("查询", "返回", "汇总", "最近", "趋势", "现状", "状态", "日报", "报告",
                   "query", "return", "summarize", "trend", "report", "coverage", "history")

_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "benchmark" / "schema.json"


def validate_task_schema(task: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Validate one task against schema.json (the independent schema check).

    The static audit checks *intent* (Prompt-Gold consistency); the JSON Schema
    check enforces the *shape* contract. Both must pass (Annotator 2 round-2
    requirement P0-2). Returns issues in the same (level, code, message) shape.
    """
    try:
        import json as _json
        from jsonschema import Draft7Validator
        schema = _json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
        v = Draft7Validator(schema)
        errs = list(v.iter_errors(task))
        if not errs:
            return []
        issues = []
        for e in errs[:20]:
            path = "/".join(str(p) for p in e.path) or "<root>"
            issues.append(("error", "schema_violation",
                           f"schema {path}: {e.message}"))
        return issues
    except FileNotFoundError:
        return [("error", "schema_missing", "schema.json not found")]
    except Exception as exc:  # pragma: no cover
        return [("error", "schema_error", f"schema validation failed: {exc}")]


def audit_task(task: dict[str, Any]) -> dict[str, Any]:
    """Return {task_id, issues: [ (level, code, message) ]}. issue level in
    {error, warning}."""
    issues = []
    tid = task.get("task_id", "?")

    # 0. JSON Schema shape contract (independent of the intent audit)
    issues.extend(validate_task_schema(task))

    # 1. known task_type
    tt = task_type_of(task)
    if tt not in TASK_TYPES:
        issues.append(("error", "unknown_task_type", f"resolved task_type {tt!r} not in {TASK_TYPES}"))

    # 4. version / review_status
    ver = task.get("annotation_version")
    if ver != "v2":
        issues.append(("error", "bad_annotation_version",
                       f"annotation_version={ver!r}, expected 'v2'"))
    rs = task.get("review_status")
    _allowed_rs = {"pending", "needs_revision", "reviewed", "approved", "rejected"}
    if rs not in _allowed_rs:
        issues.append(("error", "bad_review_status", f"review_status={rs!r}"))
    if rs != "approved":
        issues.append(("warning", "not_approved",
                       f"review_status={rs!r}; must be 'approved' before freeze"))

    # 2. memory_query must not demand scene building
    if requires_query_gold(tt):
        req_nodes = task.get("graph_outcome", {}).get("required_nodes") or task.get("required_nodes") or []
        has_query = bool(task.get("query_spec") or task.get("expected_answer") or
                         task.get("expected_evidence") or
                         (task.get("expected_outcome") or {}).get("answer"))
        if req_nodes:
            issues.append(("error", "memory_query_scene_gold",
                           f"memory_query carries {len(req_nodes)} required_nodes "
                           "(should be empty; target objects live in initial_state)"))
        if not has_query:
            issues.append(("error", "memory_query_missing_query_gold",
                           "memory_query lacks query_spec/expected_answer/expected_evidence"))
        # prompt must be retrieval-flavored
        prompt = str(task.get("prompt") or "")
        if not any(h in prompt for h in RETRIEVAL_HINTS):
            issues.append(("warning", "prompt_not_retrieval",
                           "memory_query prompt has no retrieval keywords"))

    # 3. graph types: if they carry required_nodes, ensure they aren't pure retrieval
    if requires_graph_gold(tt):
        graph = task.get("graph_outcome") or task
        req_nodes = graph.get("required_nodes") or []
        prompt = str(task.get("prompt") or "")
        has_scene_keywords = any(h in prompt for h in RETRIEVAL_HINTS)
        # retrieval prompt + graph gold is the test_v1 defect ONLY when there are
        # no scene-construction keywords; if the prompt asks to build something,
        # having graph gold is fine.
        build_hints = ("构建", "创建", "包含", "绑定", "覆盖", "温室", "安装",
                       "build", "create", "plant", "greenhouse", "asset")
        if not req_nodes and not has_query_spec(task):
            issues.append(("error", "graph_missing_graph_gold",
                           f"{tt} has no required_nodes and no query_spec (nothing to grade)"))
        elif req_nodes and has_scene_keywords and not any(b in prompt for b in build_hints):
            issues.append(("warning", "retrieval_prompt_graph_gold",
                           "prompt reads as retrieval but gold requires scene nodes — check intent"))

    return {"task_id": tid, "task_type": tt, "issues": issues}


def has_query_spec(task: dict[str, Any]) -> bool:
    return bool(task.get("query_spec") or task.get("expected_answer") or
                task.get("expected_evidence") or (task.get("expected_outcome") or {}).get("answer"))


def audit_file(path: Path) -> list[dict[str, Any]]:
    """Audit every task in a JSONL/JSON task file."""
    text = path.read_text(encoding="utf-8")
    tasks = []
    try:
        if text.lstrip().startswith("["):
            tasks = json.loads(text)
        else:
            tasks = [json.loads(l) for l in text.splitlines() if l.strip()]
    except (json.JSONDecodeError, ValueError):
        # single JSON object
        tasks = [json.loads(text)]
    reports = []
    for t in tasks:
        if isinstance(t, dict) and "task_id" in t:
            reports.append(audit_task(t))
    return reports


def audit_summary(reports: list[dict[str, Any]]) -> dict[str, Any]:
    errors = [r for r in reports if any(lvl == "error" for lvl, _, _ in r["issues"])]
    warnings = [r for r in reports if any(lvl == "warning" for lvl, _, _ in r["issues"])]
    return {
        "total": len(reports),
        "errors": len(errors),
        "warnings": len(warnings),
        "clean": len(reports) - len(errors),
        "error_tasks": [r["task_id"] for r in errors],
        "warning_tasks": [r["task_id"] for r in warnings],
    }


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        reports = audit_file(Path(p))
        s = audit_summary(reports)
        print(f"{p}: {s}")
        for r in reports:
            for lvl, code, msg in r["issues"]:
                print(f"  [{lvl}] {r['task_id']} {code}: {msg}")
