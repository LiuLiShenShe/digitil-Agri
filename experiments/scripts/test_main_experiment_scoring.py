#!/usr/bin/env python3
"""Focused tests for main-experiment scoring helpers."""

import unittest
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_main_experiment as exp
import run_ablation_experiment as ablation


class MainExperimentScoringTest(unittest.TestCase):
    def test_llm_call_repairs_malformed_json_once(self) -> None:
        class FakeResponse:
            status_code = 200

            def __init__(self, content: str) -> None:
                self._content = content

            def json(self):
                return {
                    "choices": [{"message": {"content": self._content}}],
                    "usage": {"total_tokens": 1},
                }

        responses = [
            FakeResponse('{"taskId":"TXX","method":"Direct-LLM","success":true "objects":[]}'),
            FakeResponse('{"taskId":"TXX","method":"Direct-LLM","success":true,"objects":[]}'),
        ]

        def fake_post(*args, **kwargs):
            return responses.pop(0)

        config = exp.LLMConfig(
            enabled=True,
            base_url="https://api.stepfun.com/v1",
            api_key="secret",
            model="step-3.5-flash",
            timeout_seconds=5,
        )
        task = {
            "task_id": "TXX",
            "category": "unit",
            "prompt": "构建测试温室",
            "required_objects": 1,
            "required_relations": 1,
            "required_bindings": 1,
            "rules": ["R1"],
        }

        with patch.object(exp.requests, "post", side_effect=fake_post) as post:
            parsed = exp.call_llm_json("Direct-LLM + Schema", task, config)

        self.assertEqual(post.call_count, 2)
        self.assertTrue(parsed["success"])

    def test_failure_output_is_scoreable(self) -> None:
        task = {
            "task_id": "TXX",
            "category": "unit",
            "prompt": "构建测试温室",
            "required_objects": 1,
            "required_relations": 1,
            "required_bindings": 1,
            "rules": ["R1", "R7"],
        }

        record = exp.failure_output("Direct-LLM + Schema", task, RuntimeError("bad json"), 99)
        scored = exp.score_record(task, record)

        self.assertFalse(record["success"])
        self.assertEqual(record["violatedRules"], ["R1", "R7"])
        self.assertEqual(scored["success"], 0)
        self.assertEqual(scored["generated_objects"], 0)

    def test_score_caps_objects_relations_and_bindings(self) -> None:
        """[SUPERSEDED by experiments/v3/tests/test_anti_cheat.py]

        This test documents the old legacy scoring behavior where correct_objects =
        min(generated_objects, required_objects). The v3 evaluator does NOT use this
        formula — it uses Hungarian-optimal matching and never rewards mere count. This
        test is kept for backward-compatibility documentation only; it does not apply
        to the v3 experiment suite and must not be cited as evidence of fairness.
        """
        task = {
            "task_id": "TXX",
            "category": "unit",
            "required_objects": 2,
            "required_relations": 3,
            "required_bindings": 1,
            "rules": ["R1", "R7"],
        }
        record = {
            "method": "Single-Agent",
            "success": True,
            "objects": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
            "relations": [{}, {}, {}, {}],
            "bindings": [{}, {}],
            "checkedRules": ["R1", "R7"],
            "violatedRules": [],
            "manualCorrections": 0,
            "traceSteps": [
                {"traceType": "declared", "tool": "scene.plan"},
                {"traceType": "declared", "tool": "layout.solve"},
                {"traceType": "declared", "tool": "asset.job.create"},
                {"traceType": "declared", "tool": "object.bind"},
                {"traceType": "declared", "tool": "layout.validate"},
            ],
            "elapsedMs": 123,
        }

        scored = exp.score_record(task, record)

        self.assertEqual(scored["success"], 1)
        self.assertEqual(scored["generated_objects"], 3)
        self.assertEqual(scored["correct_relations"], 3)
        self.assertEqual(scored["correct_bindings"], 1)
        self.assertEqual(scored["traceable_steps"], 5)

    def test_fatal_rule_violation_marks_failure(self) -> None:
        task = {
            "task_id": "TXX",
            "category": "unit",
            "required_objects": 1,
            "required_relations": 1,
            "required_bindings": 1,
            "rules": ["R1", "R7"],
        }
        record = {
            "method": "Direct-LLM",
            "success": True,
            "objects": [{"id": "a"}],
            "relations": [{}],
            "bindings": [{}],
            "checkedRules": ["R1", "R7"],
            "violatedRules": [{"rule": "R1"}],
            "manualCorrections": 1,
            "traceSteps": [{}],
            "elapsedMs": 10,
        }

        scored = exp.score_record(task, record)

        self.assertEqual(scored["success"], 0)
        self.assertEqual(scored["violated_rules"], 1)

    def test_summary_averages_metrics(self) -> None:
        rows = [
            {
                "method": "Direct-LLM + Schema",
                "success": 1,
                "generated_objects": 2,
                "required_objects": 4,
                "correct_relations": 1,
                "required_relations": 2,
                "correct_bindings": 1,
                "required_bindings": 2,
                "violated_rules": 1,
                "checked_rules": 4,
                "manual_corrections": 2,
                "traceable_steps": 1,
                "expected_trace_steps": 1,
            },
            {
                "method": "Direct-LLM",
                "success": 0,
                "generated_objects": 4,
                "required_objects": 4,
                "correct_relations": 2,
                "required_relations": 2,
                "correct_bindings": 0,
                "required_bindings": 2,
                "violated_rules": 2,
                "checked_rules": 4,
                "manual_corrections": 0,
                "traceable_steps": 0,
                "expected_trace_steps": 1,
            },
        ]

        summary = exp.summarize(rows)[0]

        self.assertEqual(summary["method"], "Direct-LLM + Schema")
        self.assertEqual(summary["SR"], 0.5)
        self.assertEqual(summary["OC"], 0.75)
        self.assertEqual(summary["RA"], 0.75)
        self.assertEqual(summary["BA"], 0.25)
        self.assertEqual(summary["VR"], 0.375)
        self.assertEqual(summary["MR"], 1.0)
        self.assertEqual(summary["TC"], 0.5)
        self.assertEqual(summary["OF1"], 0.8571)
        self.assertEqual(summary["RF1"], 0.8571)
        self.assertEqual(summary["BF1"], 0.3333)

    def test_precision_recall_f1_helpers_handle_normal_over_and_empty_cases(self) -> None:
        self.assertEqual(exp.precision(2, 4), 0.5)
        self.assertEqual(exp.recall(2, 4), 0.5)
        self.assertEqual(exp.precision(4, 2), 1.0)
        self.assertEqual(exp.recall(0, 0), 1.0)
        self.assertEqual(exp.precision(0, 0), 0.0)
        self.assertEqual(exp.f1_score(0.5, 0.5), 0.5)
        self.assertEqual(exp.f1_score(0.0, 0.0), 0.0)

    def test_declared_trace_counts_field_completeness_but_not_executed_faithfulness(self) -> None:
        record = {
            "traceSteps": [
                {"traceType": "declared", "agent": "ScenePlannerAgent", "tool": "scene.plan"},
                {"traceType": "declared", "agent": "LayoutAgent", "tool": "layout.solve"},
                {"traceType": "declared", "agent": "AssetFidelityAgent", "tool": "asset.job.create"},
                {"traceType": "declared", "agent": "DataBindingAgent", "tool": "object.bind"},
                {"traceType": "declared", "agent": "ValidatorAgent", "tool": "layout.validate"},
            ]
        }

        scores = exp.trace_quality(record)

        self.assertEqual(scores["component_count"], 5)
        self.assertEqual(scores["executed_component_count"], 0)
        self.assertEqual(scores["declared_steps"], 5)
        self.assertEqual(scores["executed_steps"], 0)

    def test_executed_trace_without_evidence_is_downgraded_for_faithfulness(self) -> None:
        record = {
            "traceSteps": [
                {"traceType": "executed", "agent": "ScenePlannerAgent", "tool": "scene.plan", "evidenceId": "e1"},
                {"traceType": "executed", "agent": "LayoutAgent", "tool": "layout.solve"},
            ]
        }

        scores = exp.trace_quality(record)

        self.assertEqual(scores["component_count"], 2)
        self.assertEqual(scores["executed_component_count"], 1)
        self.assertEqual(scores["executed_steps"], 2)
        self.assertEqual(scores["evidence_steps"], 1)

    def test_progress_cache_keeps_latest_successful_record_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "progress.jsonl"
            exp.append_progress_record(path, {"taskId": "T01", "method": "Direct-LLM + Schema", "success": True, "objects": []})
            exp.append_progress_record(path, {"taskId": "T01", "method": "Direct-LLM + Schema", "success": True, "objects": [{"id": "new"}]})
            exp.append_progress_record(path, {"taskId": "T02", "method": "Direct-LLM + Schema", "success": False})

            cache = exp.load_progress_cache(path)

            self.assertEqual(set(cache.keys()), {"T01::Direct-LLM + Schema"})
            self.assertEqual(cache["T01::Direct-LLM + Schema"]["objects"], [{"id": "new"}])

    def test_error_analysis_counts_common_structural_failures(self) -> None:
        task = {
            "task_id": "TXX",
            "category": "历史查询",
            "prompt": "查询番茄温室最近 7 天环境状态",
            "required_objects": 4,
            "required_relations": 3,
            "required_bindings": 2,
            "rules": ["R1", "R2", "R8"],
        }
        record = {
            "method": "Direct-LLM + Schema",
            "objects": [{"id": "plant1", "type": "Plant", "name": "番茄"}],
            "relations": [{"subject": "plant1", "predicate": "contains", "object": ""}],
            "bindings": [{"subject": "plant1"}],
            "checkedRules": ["R1", "R2", "R8"],
            "violatedRules": ["R8"],
            "traceSteps": [{"traceType": "declared", "agent": "Agent", "tool": "scene.plan"}],
        }

        errors = exp.analyze_errors(task, record)

        self.assertEqual(errors["missing_objects"], 3)
        self.assertEqual(errors["missing_relations"], 2)
        self.assertEqual(errors["missing_bindings"], 1)
        self.assertEqual(errors["binding_missing_fields"], 1)
        self.assertEqual(errors["relation_direction_errors"], 1)
        self.assertEqual(errors["memory_range_errors"], 1)
        self.assertEqual(errors["trace_not_auditable"], 1)

    def test_without_ontology_adds_hierarchy_violation_and_removes_hierarchy_edges(self) -> None:
        task = {
            "task_id": "T01",
            "category": "场景构建",
            "required_objects": 4,
            "required_relations": 4,
            "required_bindings": 2,
            "rules": ["R1", "R2", "R7"],
        }
        record = {
            "taskId": "T01",
            "method": "Ours",
            "success": True,
            "objects": [{"id": "gh"}, {"id": "row"}, {"id": "plant"}],
            "relations": [
                {"subject": "gh", "predicate": "contains", "object": "row"},
                {"subject": "plant", "predicate": "belongs_to", "object": "row"},
                {"subject": "sensor", "predicate": "monitors", "object": "gh"},
            ],
            "bindings": [{"type": "asset"}, {"type": "business"}],
            "checkedRules": ["R1", "R2", "R7"],
            "violatedRules": [],
            "traceSteps": [{"tool": "scene.plan"}, {"tool": "layout.solve"}, {"tool": "layout.validate"}],
            "elapsedMs": 1,
        }

        variant = ablation.apply_variant(record, task, {"method": "Ours w/o Ontology", "useOntology": False})

        self.assertEqual(variant["method"], "Ours w/o Ontology")
        self.assertIn("R1", variant["violatedRules"])
        self.assertEqual([item["predicate"] for item in variant["relations"]], ["monitors"])

    def test_without_asset_router_zeroes_asset_route_score(self) -> None:
        task = {
            "task_id": "T07",
            "category": "资产路由",
            "required_objects": 4,
            "required_relations": 4,
            "required_bindings": 4,
            "rules": ["R1", "R4", "R7", "R9"],
        }
        record = {
            "taskId": "T07",
            "method": "Ours",
            "success": True,
            "objects": [{"id": "gh"}, {"id": "plant"}],
            "relations": [{"subject": "plant", "predicate": "has_asset", "object": "tomato"}],
            "bindings": [
                {"subject": "plant", "target": "tomato", "type": "asset"},
                {"subject": "camera", "target": "TRELLIS.2-task", "type": "placeholder"},
            ],
            "checkedRules": ["R1", "R4", "R7", "R9"],
            "violatedRules": [],
            "traceSteps": [{"agent": "AssetFidelityAgent", "tool": "asset.job.create"}],
            "elapsedMs": 1,
        }

        variant = ablation.apply_variant(record, task, {"method": "Ours w/o Asset Router", "useAssetRouter": False})
        scored = ablation.score_ablation_record(task, variant)

        self.assertEqual(scored["required_asset_routes"], 4)
        self.assertEqual(scored["correct_asset_routes"], 0)
        self.assertIn("R4", variant["violatedRules"])
        self.assertIn("R9", variant["violatedRules"])

    def test_without_validator_records_rule_conflicts_and_trace_gap(self) -> None:
        task = {
            "task_id": "T20",
            "category": "规则修正",
            "required_objects": 4,
            "required_relations": 4,
            "required_bindings": 2,
            "rules": ["R1", "R3", "R7", "R10"],
        }
        record = {
            "taskId": "T20",
            "method": "Ours",
            "success": True,
            "objects": [{"id": "row"}],
            "relations": [{"subject": "gh", "predicate": "contains", "object": "row"}],
            "bindings": [{"type": "asset"}],
            "checkedRules": ["R1", "R3", "R7", "R10"],
            "violatedRules": [],
            "traceSteps": [
                {"tool": "scene.plan"},
                {"tool": "layout.solve"},
                {"tool": "layout.validate"},
                {"tool": "asset.job.create"},
                {"tool": "object.bind"},
            ],
            "elapsedMs": 1,
        }

        variant = ablation.apply_variant(record, task, {"method": "Ours w/o Validator", "useValidator": False})
        scored = ablation.score_ablation_record(task, variant)

        self.assertIn("R10", variant["violatedRules"])
        self.assertGreater(scored["violated_rules"], 0)
        self.assertLess(scored["traceable_steps"], scored["expected_trace_steps"])

    def test_ablation_trace_components_require_distinct_pipeline_evidence(self) -> None:
        full_record = {
            "traceSteps": [
                {"agent": "ScenePlannerAgent", "tool": "scene.plan"},
                {"agent": "LayoutAgent", "tool": "layout.solve"},
                {"agent": "AssetFidelityAgent", "tool": "asset.job.create"},
                {"agent": "DataBindingAgent", "tool": "object.relations"},
                {"agent": "ValidatorAgent", "tool": "layout.validate"},
                {"agent": "ScenePlannerAgent", "tool": "scene.plan"},
            ]
        }
        partial_record = {
            "traceSteps": [
                {"agent": "ScenePlannerAgent", "tool": "scene.plan"},
                {"agent": "ScenePlannerAgent", "tool": "scene.plan"},
                {"agent": "ScenePlannerAgent", "tool": "scene.plan"},
            ]
        }

        self.assertEqual(ablation.count_trace_components(full_record), 5)
        self.assertEqual(ablation.count_trace_components(partial_record), 1)

    def test_ablation_report_explains_counterfactual_and_metric_caveats(self) -> None:
        summary_rows = [
            {
                "method": "Ours",
                "SR": 1.0,
                "OC": 0.5236,
                "RA": 0.8153,
                "AR": 0.5971,
                "VR": 0.0067,
                "TC": 0.9933,
                "hierarchy_error_rate": 0.0,
                "validator_conflict_rate": 0.0083,
            }
        ]
        variants = [{"method": "Ours", "description": "full"}]
        original_results_dir = ablation.RESULTS_DIR

        with tempfile.TemporaryDirectory() as tmpdir:
            ablation.RESULTS_DIR = Path(tmpdir)
            try:
                ablation.write_markdown_report(summary_rows, variants)
                report = (Path(tmpdir) / "ablation_experiment_report.md").read_text(encoding="utf-8")
            finally:
                ablation.RESULTS_DIR = original_results_dir

        self.assertIn("反事实模块消融实验", report)
        self.assertIn("OC 主要反映对象实例展开程度", report)
        self.assertIn("AR 仅在资产路由相关任务上统计", report)
        self.assertIn("VR 反映最终场景结果中的规则冲突比例", report)
        self.assertIn("Validator 冲突率反映规则校验模块内部检查项", report)


if __name__ == "__main__":
    unittest.main()
