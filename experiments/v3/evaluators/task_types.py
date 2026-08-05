"""Task-type dispatch for the v2 benchmark.

Every task declares a ``task_type`` (F-008 Gold Schema). Evaluation is routed
through a per-type success adapter — NOT a single object-graph CVSR shared by
all types (the root defect in test_v1, see INVALIDATION_REPORT.md).

Task types:
  - scene_construction : agent authors a complete, valid object graph
  - asset_routing      : agent routes asset/GLB policies onto objects
  - data_binding       : agent binds sensors/traits to monitored objects
  - rule_repair        : agent fixes violations in an initial_state
  - memory_query       : agent retrieves/aggregates from existing state (no scene build)
"""

from __future__ import annotations

from typing import Any, Callable

TASK_TYPES = ("scene_construction", "asset_routing", "data_binding",
              "rule_repair", "memory_query")

# Names used by the v1 codebase for the same underlying intents.
LEGACY_CATEGORY_TO_TASK_TYPE = {
    "scene_build": "scene_construction",
    "asset_route": "asset_routing",
    "data_bind": "data_binding",
    "repair": "rule_repair",
    "memory_query": "memory_query",
}


def task_type_of(task: dict[str, Any]) -> str:
    """Resolve a task's task_type from the new field or legacy category."""
    tt = task.get("task_type")
    if tt in TASK_TYPES:
        return tt
    legacy = task.get("category") or ""
    return LEGACY_CATEGORY_TO_TASK_TYPE.get(legacy, "scene_construction")


def requires_graph_gold(task_type: str) -> bool:
    """Graph-gold (required_nodes/edges/bindings) applies to these types."""
    return task_type in {"scene_construction", "asset_routing", "data_binding", "rule_repair"}


def requires_query_gold(task_type: str) -> bool:
    """Query-gold (query_spec/expected_answer/expected_evidence) applies to memory_query."""
    return task_type == "memory_query"


# Type-specific success adapter: (task, run_state) -> (success: bool, diagnostics: dict)
TaskAdapter = Callable[[dict[str, Any], dict[str, Any]], tuple[bool, dict[str, Any]]]

_ADAPTERS: dict[str, TaskAdapter] = {}


def register_adapter(task_type: str, fn: TaskAdapter) -> None:
    if task_type not in TASK_TYPES:
        raise ValueError(f"unknown task_type {task_type!r}")
    _ADAPTERS[task_type] = fn


def get_adapter(task_type: str) -> TaskAdapter | None:
    return _ADAPTERS.get(task_type)


def evaluate_task_success(task: dict[str, Any], run_state: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """Route to the task_type adapter. Unknown/None adapter -> (False, {error})."""
    tt = task_type_of(task)
    adapter = get_adapter(tt)
    if adapter is None:
        return False, {"task_type": tt, "error": f"no adapter registered for {tt}"}
    ok, diag = adapter(task, run_state)
    diag.setdefault("task_type", tt)
    return bool(ok), diag
