"""Tests for the static Gold audit (F-013).

The audit must catch the test_v1 defect class (memory_query carrying scene-build
gold) and must NOT falsely flag a correct v2 memory_query.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # experiments/v3/
sys.path.insert(0, str(ROOT / "evaluators"))
sys.path.insert(0, str(ROOT / "benchmark"))

from gold_audit import audit_task  # noqa: E402


def _good_memory_task() -> dict:
    return {
        "task_id": "T", "task_type": "memory_query", "prompt": "查询最近 7 天温度趋势，返回日均值。",
        "annotation_version": "v2", "review_status": "approved",
        "query_spec": {"metrics": ["temperature"]},
        "expected_answer": {"normalized_values": {"temperature": {"mean": 22.0}}},
        "expected_evidence": {"record_ids": ["rec-1"]},
        "required_nodes": [], "required_edges": [], "required_bindings": [],
    }


def _testv1_style_bad_memory_task() -> dict:
    """A memory_query that (wrongly) demands scene construction — the test_v1 defect."""
    t = _good_memory_task()
    t["required_nodes"] = [{"id": "p1", "type": "Plant", "count": 20}]
    del t["query_spec"], t["expected_answer"], t["expected_evidence"]
    return t


def _good_graph_task() -> dict:
    return {
        "task_id": "T", "task_type": "scene_construction", "prompt": "构建温室，包含 3 行作物。",
        "annotation_version": "v2", "review_status": "approved",
        "required_nodes": [{"id": "row1", "type": "CropRow", "count": 3}],
        "required_edges": [], "required_bindings": [],
    }


def test_good_memory_task_clean():
    errs = [c for lvl, c, _ in audit_task(_good_memory_task())["issues"] if lvl == "error"]
    assert errs == []


def test_testv1_defect_caught():
    r = audit_task(_testv1_style_bad_memory_task())
    codes = [c for _, c, _ in r["issues"]]
    assert "memory_query_scene_gold" in codes
    assert "memory_query_missing_query_gold" in codes


def test_good_graph_task_clean():
    errs = [c for lvl, c, _ in audit_task(_good_graph_task())["issues"] if lvl == "error"]
    assert errs == []


def test_bad_version_flagged():
    t = _good_memory_task()
    t["annotation_version"] = "v1"
    codes = [c for _, c, _ in audit_task(t)["issues"]]
    assert "bad_annotation_version" in codes


def test_not_approved_blocks_freeze():
    t = _good_memory_task()
    t["review_status"] = "pending"
    codes = [c for _, c, _ in audit_task(t)["issues"]]
    assert "not_approved" in codes  # warning level, blocks freeze


def test_memory_missing_query_flagged():
    t = _good_memory_task()
    del t["query_spec"], t["expected_answer"], t["expected_evidence"]
    codes = [c for _, c, _ in audit_task(t)["issues"]]
    assert "memory_query_missing_query_gold" in codes