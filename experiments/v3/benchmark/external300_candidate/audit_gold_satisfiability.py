#!/usr/bin/env python3
"""Check that every draft Gold contract has at least one evaluator-v2.3 solution.

This is a Gold-oracle self-check, not a method run.  It constructs the declared
required graph (adding only rule-mandated camera pose/FOV defaults) or the declared
memory answer and asks the frozen evaluator whether that oracle passes.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
EVALUATORS = REPO_ROOT / "experiments/v3/evaluators"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(EVALUATORS))

from metrics import evaluate_task  # noqa: E402


def load_gold() -> list[dict[str, Any]]:
    path = ROOT / "external300_gold_draft.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def graph_oracle(task: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = deepcopy(task.get("required_nodes") or [])
    for node in nodes:
        if node.get("type") != "Camera":
            continue
        attrs = node.setdefault("key_attrs", {})
        attrs.setdefault("observes", next((n.get("id") for n in nodes if n.get("type") == "CropRow"), "crop_row"))
        attrs.setdefault("pose", {"position": [1.0, 2.5, 3.0]})
        attrs.setdefault("fov", {"degrees": 55.0})
    return nodes, deepcopy(task.get("required_edges") or []), deepcopy(task.get("required_bindings") or [])


def main() -> int:
    failures: list[dict[str, Any]] = []
    passes = Counter()
    for task in load_gold():
        task_type = task["task_type"]
        if task_type == "memory_query":
            answer = deepcopy(task.get("expected_answer") or {})
            answer["evidence"] = deepcopy(task.get("expected_evidence") or {})
            query = task.get("query_spec") or {}
            answer["time_window"] = {
                "start": query.get("start_time"),
                "end": query.get("end_time"),
            }
            result = evaluate_task(
                task=task,
                method="DECLARED_GOLD_ORACLE",
                nodes=[],
                edges=[],
                bindings=[],
                answer=answer,
                final_state={},
                trace={"steps": []},
                proxy_calls=[],
            )
        else:
            nodes, edges, bindings = graph_oracle(task)
            final_state = {"objects": deepcopy(nodes), "relations": deepcopy(edges), "bindings": deepcopy(bindings)}
            result = evaluate_task(
                task=task,
                method="DECLARED_GOLD_ORACLE",
                nodes=nodes,
                edges=edges,
                bindings=bindings,
                final_state=final_state,
                trace={"steps": []},
                proxy_calls=[],
            )
        if result.cvsr:
            passes[task_type] += 1
        else:
            failures.append({
                "task_id": task["task_id"],
                "task_type": task_type,
                "first_failed": result.first_failed_cvsr_clause,
                "fatal": result.fatal_violations,
                "object_f1": result.object_f1,
                "relation_f1": result.relation_f1,
                "binding_f1": result.binding_f1,
            })

    summary = {
        "oracle": "declared Gold contract; no scored method executed",
        "tasks": sum(passes.values()) + len(failures),
        "passes_by_type": dict(sorted(passes.items())),
        "failures": len(failures),
        "failure_examples": failures[:20],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
