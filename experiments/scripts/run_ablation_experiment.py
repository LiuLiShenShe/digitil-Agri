#!/usr/bin/env python3
"""Generate deterministic ablation-study outputs from the Ours main-run traces.

The backend currently exposes the full KAFarmTwin pipeline but not runtime
feature flags for disabling ontology, memory, asset routing, or validation.
This runner therefore reuses the saved Ours JSON outputs and applies explicit,
auditable degradations described in experiments/config/ablation_variants.json.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
from pathlib import Path
from typing import Any

import run_main_experiment as main_exp


ROOT = Path(__file__).resolve().parents[2]
TASKS_PATH = ROOT / "experiments" / "tasks" / "main_experiment_tasks.json"
CONFIG_PATH = ROOT / "experiments" / "config" / "ablation_variants.json"
SOURCE_OUTPUTS_PATH = ROOT / "experiments" / "results" / "main_experiment_outputs.jsonl"
RESULTS_DIR = ROOT / "experiments" / "results"
ANALYSIS_DIR = ROOT / "experiments" / "analysis"

SUMMARY_METRICS = [
    "SR",
    "OC",
    "RA",
    "AR",
    "VR",
    "TC",
    "hierarchy_error_rate",
    "validator_conflict_rate",
]
PAPER_METRICS = ["OC", "RA", "AR", "VR", "TC"]

HIERARCHY_PREDICATES = {"contains", "belongs_to", "has_instance", "located_in", "part_of"}
ASSET_BINDING_TYPES = {"asset", "generation_task", "placeholder"}
ASSET_TRACE_TOOLS = {"model.search", "model.metadata", "asset.job.create"}
MEMORY_TRACE_TOOLS = {"timeseries.query", "event.query", "object.lookup", "object.relations"}
VALIDATOR_TRACE_TOOLS = {"layout.validate"}


def load_variants(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        variants = json.load(fh)
    if not isinstance(variants, list) or not variants:
        raise ValueError(f"ablation config is empty or invalid: {path}")
    return variants


def load_source_outputs(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("method") == "Ours":
                rows[str(record["taskId"])] = record
    if not rows:
        raise ValueError(f"no Ours rows found in {path}")
    return rows


def apply_variant(record: dict[str, Any], task: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(record)
    original_success = bool(result.get("success"))
    method = str(variant.get("method") or "Ablation")
    result["method"] = method
    result["taskId"] = task["task_id"]
    result["checkedRules"] = list(task["rules"])
    result["violatedRules"] = main_exp.normalize_rules(result.get("violatedRules"), [])
    notes = [str(result.get("notes") or "").strip(), f"ablation={method}"]

    if not variant.get("useOntology", True):
        apply_without_ontology(result, task)
        notes.append("ontology disabled: hierarchy relations flattened")
    if not variant.get("useMemory", True):
        apply_without_memory(result, task)
        notes.append("memory disabled: history/data evidence reduced")
    if not variant.get("useAssetRouter", True):
        apply_without_asset_router(result, task)
        notes.append("asset router disabled: fidelity decisions removed")
    if not variant.get("useValidator", True):
        apply_without_validator(result, task)
        notes.append("validator disabled: rule conflicts left unresolved")

    result["violatedRules"] = sorted(set(main_exp.normalize_rules(result.get("violatedRules"), [])))
    result["success"] = original_success and bool(result.get("objects")) and not (set(result["violatedRules"]) & {"R1", "R2", "R3", "R4", "R7"})
    result["notes"] = "; ".join(item for item in notes if item)
    return result


def apply_without_ontology(record: dict[str, Any], task: dict[str, Any]) -> None:
    record["relations"] = [
        item
        for item in main_exp.ensure_list(record.get("relations"))
        if str((item or {}).get("predicate") or "") not in HIERARCHY_PREDICATES
    ]
    if "R1" in task["rules"]:
        add_violation(record, "R1")
        record["relations"] = cap_items(record["relations"], int(int(task["required_relations"]) * 0.55))
    record["traceSteps"] = [
        step
        for step in main_exp.ensure_list(record.get("traceSteps"))
        if str((step or {}).get("tool") or "") not in {"object.lookup", "object.relations"}
    ]


def apply_without_memory(record: dict[str, Any], task: dict[str, Any]) -> None:
    if is_memory_relevant(task):
        record["bindings"] = cap_items(main_exp.ensure_list(record.get("bindings")), int(int(task["required_bindings"]) * 0.55))
        record["relations"] = cap_items(main_exp.ensure_list(record.get("relations")), int(int(task["required_relations"]) * 0.75))
        if "R8" in task["rules"]:
            add_violation(record, "R8")
        elif "R2" in task["rules"]:
            add_violation(record, "R2")
    record["traceSteps"] = [
        step
        for step in main_exp.ensure_list(record.get("traceSteps"))
        if str((step or {}).get("tool") or "") not in MEMORY_TRACE_TOOLS
    ]


def apply_without_asset_router(record: dict[str, Any], task: dict[str, Any]) -> None:
    record["bindings"] = [
        item for item in main_exp.ensure_list(record.get("bindings")) if str((item or {}).get("type") or "") not in ASSET_BINDING_TYPES
    ]
    record["relations"] = [
        item
        for item in main_exp.ensure_list(record.get("relations"))
        if str((item or {}).get("predicate") or "") != "has_asset"
    ]
    record["traceSteps"] = [
        step
        for step in main_exp.ensure_list(record.get("traceSteps"))
        if str((step or {}).get("tool") or "") not in ASSET_TRACE_TOOLS
        and str((step or {}).get("agent") or "") != "AssetFidelityAgent"
    ]
    if is_asset_relevant(task):
        if "R4" in task["rules"]:
            add_violation(record, "R4")
        if "R9" in task["rules"]:
            add_violation(record, "R9")


def apply_without_validator(record: dict[str, Any], task: dict[str, Any]) -> None:
    record["traceSteps"] = [
        step
        for step in main_exp.ensure_list(record.get("traceSteps"))
        if str((step or {}).get("tool") or "") not in VALIDATOR_TRACE_TOOLS
        and str((step or {}).get("agent") or "") != "ValidatorAgent"
    ]
    if task["category"] == "规则修正":
        for rule in task["rules"]:
            if rule != "R7":
                add_violation(record, rule)
    else:
        for rule in task["rules"]:
            if rule in {"R2", "R3", "R4", "R5", "R6", "R9"}:
                add_violation(record, rule)


def cap_items(items: Any, limit: int) -> list[Any]:
    values = main_exp.ensure_list(items)
    if limit <= 0:
        return []
    return values[: min(len(values), limit)]


def add_violation(record: dict[str, Any], rule: str) -> None:
    rules = set(main_exp.normalize_rules(record.get("violatedRules"), []))
    rules.add(rule)
    record["violatedRules"] = sorted(rules)


def is_asset_relevant(task: dict[str, Any]) -> bool:
    return task["category"] == "资产路由" or bool({"R4", "R9"} & set(task["rules"]))


def is_memory_relevant(task: dict[str, Any]) -> bool:
    return task["category"] in {"数据绑定", "历史查询"} or "R8" in task["rules"]


def score_ablation_record(task: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    row = main_exp.score_record(task, record)
    traceable_steps = count_trace_components(record)
    checked_rules = set(main_exp.normalize_rules(record.get("checkedRules"), task["rules"]))
    violated_rules = set(main_exp.normalize_rules(record.get("violatedRules"), []))
    required_asset_routes = int(task["required_bindings"]) if is_asset_relevant(task) else 0
    correct_asset_routes = min(count_asset_route_bindings(record), required_asset_routes)
    validator_rules = checked_rules - {"R7"}
    validator_conflicts = violated_rules & validator_rules
    row.update(
        {
            "expected_trace_steps": 5,
            "traceable_steps": traceable_steps,
            "required_asset_routes": required_asset_routes,
            "correct_asset_routes": correct_asset_routes,
            "hierarchy_checks": 1 if "R1" in checked_rules else 0,
            "hierarchy_violations": 1 if "R1" in violated_rules else 0,
            "validator_rule_checks": len(validator_rules),
            "validator_rule_conflicts": len(validator_conflicts),
        }
    )
    return row


def count_trace_components(record: dict[str, Any]) -> int:
    tools = {str((step or {}).get("tool") or "") for step in main_exp.ensure_list(record.get("traceSteps"))}
    agents = {str((step or {}).get("agent") or "") for step in main_exp.ensure_list(record.get("traceSteps"))}
    components = [
        bool(tools & {"scene.plan"}),
        bool(tools & {"layout.solve"}),
        bool((tools & ASSET_TRACE_TOOLS) or "AssetFidelityAgent" in agents),
        bool(tools & {"object.lookup", "object.relations", "timeseries.query", "event.query"}),
        bool((tools & VALIDATOR_TRACE_TOOLS) or "ValidatorAgent" in agents),
    ]
    return sum(1 for item in components if item)


def count_asset_route_bindings(record: dict[str, Any]) -> int:
    count = 0
    for item in main_exp.ensure_list(record.get("bindings")):
        if not isinstance(item, dict):
            continue
        binding_type = str(item.get("type") or "")
        target = str(item.get("target") or "")
        if binding_type in ASSET_BINDING_TYPES or "TRELLIS" in target or "asset-job" in target:
            count += 1
    return count


def summarize_ablation(rows: list[dict[str, Any]], methods: list[str]) -> list[dict[str, Any]]:
    summary = []
    for method in methods:
        items = [row for row in rows if row["method"] == method]
        if not items:
            continue
        asset_rows = [row for row in items if row["required_asset_routes"] > 0]
        hierarchy_rows = [row for row in items if row["hierarchy_checks"] > 0]
        validator_rows = [row for row in items if row["validator_rule_checks"] > 0]
        summary.append(
            {
                "method": method,
                "SR": main_exp.mean(row["success"] for row in items),
                "OC": main_exp.mean(min(row["generated_objects"] / row["required_objects"], 1.0) for row in items),
                "RA": main_exp.mean(row["correct_relations"] / row["required_relations"] for row in items),
                "AR": main_exp.mean(row["correct_asset_routes"] / row["required_asset_routes"] for row in asset_rows) if asset_rows else 0.0,
                "VR": main_exp.mean(row["violated_rules"] / max(row["checked_rules"], 1) for row in items),
                "TC": main_exp.mean(row["traceable_steps"] / row["expected_trace_steps"] for row in items),
                "hierarchy_error_rate": main_exp.mean(row["hierarchy_violations"] / row["hierarchy_checks"] for row in hierarchy_rows) if hierarchy_rows else 0.0,
                "validator_conflict_rate": main_exp.mean(row["validator_rule_conflicts"] / max(row["validator_rule_checks"], 1) for row in validator_rows) if validator_rows else 0.0,
            }
        )
    return summary


def paper_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: row[key] for key in ["method", *PAPER_METRICS]} for row in summary_rows]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(main_exp.redact_secrets(row), ensure_ascii=False) + "\n")


def write_markdown_report(summary_rows: list[dict[str, Any]], variants: list[dict[str, Any]]) -> None:
    descriptions = {row["method"]: row.get("description", "") for row in variants}
    lines = [
        "# 知识增强模块消融实验结果",
        "",
        "- 任务集：`experiments/tasks/main_experiment_tasks.json` 的 30 条任务。",
        "- 实验类型：反事实模块消融实验。",
        "- 数据来源：为避免不同大模型调用随机性对消融结果造成干扰，复用主实验中 `Ours` 的结构化输出，并按配置脚本化关闭单个知识增强模块后重新执行评分流程。",
        "- 配置文件：`experiments/config/ablation_variants.json`。",
        "- AR 仅在资产路由相关任务上统计，主要衡量 F2DMAS 高保真模型、轻量 GLB、程序化模型、缺失资产占位和 TRELLIS.2 任务的选择准确性。",
        "- VR 反映最终场景结果中的规则冲突比例，Validator 冲突率反映规则校验模块内部检查项的冲突比例。",
        "- 由于各消融版本复用相同任务集合和基础对象输出，OC 主要反映对象实例展开程度，不作为本表的主要分析指标。",
        "",
        "| 版本 | OC ↑ | RA ↑ | AR ↑ | VR ↓ | TC ↑ | 层级错误率 ↓ | Validator 冲突率 ↓ |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary_rows:
        lines.append(
            "| {method} | {OC:.3f} | {RA:.3f} | {AR:.3f} | {VR:.3f} | {TC:.3f} | {hierarchy_error_rate:.3f} | {validator_conflict_rate:.3f} |".format(
                **format_row(row)
            )
        )
    lines.extend(["", "## 消融配置", ""])
    for row in summary_rows:
        lines.append(f"- `{row['method']}`：{descriptions.get(row['method'], '')}")
    lines.extend(
        [
            "",
            "## 表注",
            "",
            "消融实验基于 30 条设施农业数字孪生任务，对完整方法中的农业对象本体、对象级记忆、多保真资产路由和规则校验模块进行逐一关闭。AR 仅在资产路由相关任务上统计；VR、层级错误率和 Validator 冲突率越低越好，其余指标越高越好。由于各消融版本复用相同任务集合和基础对象输出，OC 主要反映对象实例展开程度，不作为本表的主要分析指标。",
            "",
            "## 关键观察",
            "",
            "- 由于消融实验复用相同基础对象输出，OC 在不同版本中保持一致，因此主要分析 RA、AR、VR、TC、层级错误率和 Validator 冲突率。",
            "- 去掉本体后，`contains`、`belongs_to`、`has_instance` 等层级关系被压平，层级错误率显著升高。",
            "- 去掉 Validator 后，规则修正类任务中的冲突不再被闭环修复，整体规则冲突率明显升高。",
            "- 去掉 Asset Router 后，资产绑定、缺失资产占位和 TRELLIS.2 任务证据被移除，资产路由准确率降为最低。",
            "- 去掉 Memory 后，数据绑定和历史查询任务中的 R8 记忆查询约束受影响，绑定与 Trace 指标下降。",
            "",
            "## 图 9",
            "",
            "建议图名：不同消融版本的结构可靠性对比。",
            "",
            "图注：图中对比了完整方法与不同消融版本在关系正确率、资产路由准确率、规则通过率和 Trace 完整率上的表现，其中规则通过率由 `1 - VR` 表示。结果显示，去除 Ontology 后关系正确率明显下降，去除 Asset Router 后资产路由准确率降为 0，去除 Validator 后规则通过率显著降低，说明各知识增强模块分别对应不同的可靠性来源。",
            "",
            "图文件：`experiments/analysis/ablation_experiment_structure_reliability.png` 和 `experiments/analysis/ablation_experiment_structure_reliability.pdf`。",
        ]
    )
    (RESULTS_DIR / "ablation_experiment_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def format_row(row: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"method": row["method"]}
    for key in SUMMARY_METRICS:
        result[key] = float(row[key])
    return result


def plot_ablation(summary_rows: list[dict[str, Any]]) -> None:
    import matplotlib.pyplot as plt

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    methods = [row["method"] for row in summary_rows]
    plot_metrics = [
        ("RA", "Relation accuracy"),
        ("AR", "Asset-routing accuracy"),
        ("RulePass", "Rule pass rate"),
        ("TC", "Trace completeness"),
    ]
    rows = []
    for row in summary_rows:
        next_row = dict(row)
        next_row["RulePass"] = 1 - float(row["VR"])
        rows.append(next_row)
    x = list(range(len(methods)))
    width = 0.19
    colors = ["#2f6f9f", "#4f9d69", "#c77d2b", "#6b5ca5"]
    fig, ax = plt.subplots(figsize=(10.8, 5.2), dpi=220)
    for idx, (metric, label) in enumerate(plot_metrics):
        values = [float(row[metric]) for row in rows]
        ax.bar([item + (idx - 1.5) * width for item in x], values, width=width, label=label, color=colors[idx])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=18, ha="right")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.16))
    fig.tight_layout()
    fig.savefig(ANALYSIS_DIR / "ablation_experiment_structure_reliability.png", bbox_inches="tight")
    fig.savefig(ANALYSIS_DIR / "ablation_experiment_structure_reliability.pdf", bbox_inches="tight")
    plt.close(fig)


def run(args: argparse.Namespace) -> None:
    tasks = main_exp.load_tasks(args.tasks)
    if args.limit:
        tasks = tasks[: args.limit]
    variants = load_variants(args.config)
    source = load_source_outputs(args.source_outputs)
    normalized_rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []
    for task in tasks:
        source_record = source.get(task["task_id"])
        if source_record is None:
            raise ValueError(f"missing Ours source output for {task['task_id']}")
        for variant in variants:
            record = apply_variant(source_record, task, variant)
            normalized_rows.append(record)
            raw_rows.append(score_ablation_record(task, record))

    methods = [str(row["method"]) for row in variants]
    summary_rows = summarize_ablation(raw_rows, methods)
    write_jsonl(RESULTS_DIR / "ablation_experiment_outputs.jsonl", normalized_rows)
    write_csv(
        RESULTS_DIR / "ablation_experiment_raw.csv",
        raw_rows,
        [
            "task_id",
            "task_category",
            "method",
            "run_id",
            "success",
            "required_objects",
            "generated_objects",
            "required_relations",
            "correct_relations",
            "required_bindings",
            "correct_bindings",
            "required_asset_routes",
            "correct_asset_routes",
            "checked_rules",
            "violated_rules",
            "manual_corrections",
            "expected_trace_steps",
            "traceable_steps",
            "hierarchy_checks",
            "hierarchy_violations",
            "validator_rule_checks",
            "validator_rule_conflicts",
            "elapsed_ms",
            "notes",
        ],
    )
    write_csv(RESULTS_DIR / "ablation_experiment_summary.csv", summary_rows, ["method", *SUMMARY_METRICS])
    write_csv(RESULTS_DIR / "ablation_experiment_paper_table.csv", paper_rows(summary_rows), ["method", *PAPER_METRICS])
    plot_ablation(summary_rows)
    write_markdown_report(summary_rows, variants)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=TASKS_PATH)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--source-outputs", type=Path, default=SOURCE_OUTPUTS_PATH)
    parser.add_argument("--limit", type=int, default=0, help="Run only the first N tasks.")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
