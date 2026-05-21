#!/usr/bin/env python3
"""Phase 0 baseline guard for the agri digital twin OpenSpec workspace."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class CommandResult:
    command: str
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class GateResult:
    ok: bool
    failed_commands: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class ActiveChange:
    name: str
    completed_tasks: int
    total_tasks: int
    status: str

    @property
    def is_implemented(self) -> bool:
        return self.total_tasks > 0 and self.completed_tasks >= self.total_tasks


@dataclass(frozen=True)
class AssetCounts:
    backend_glb: int
    backend_thumbnails: int
    frontend_glb: int
    frontend_images: int


@dataclass(frozen=True)
class DataSourceStatus:
    name: str
    status: str
    evidence: str


SECRET_LINE = re.compile(r"(?i)^(\s*(?:api[-_]?key|password|authorization)\s*[:=]\s*).*$")


def redact(text: str) -> str:
    return "\n".join(SECRET_LINE.sub(r"\1[REDACTED]", line) for line in text.splitlines())


def run_command(command: Sequence[str], cwd: Path) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return CommandResult(" ".join(command), completed.returncode, completed.stdout, completed.stderr)


def run_shell_command(command: str, cwd: Path) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return CommandResult(command, completed.returncode, completed.stdout, completed.stderr)


def count_files(root: Path, pattern: str) -> int:
    return sum(1 for path in root.glob(pattern) if path.is_file())


def count_assets(root: Path) -> AssetCounts:
    return AssetCounts(
        backend_glb=count_files(root, "digital-twingo/scene-server-go/scene-assets/**/*.glb")
        + count_files(root, "digital-twingo/scene-server-go/scene-assets/**/*.GLB"),
        backend_thumbnails=count_files(root, "digital-twingo/scene-server-go/scene-assets/thumbs/*"),
        frontend_glb=count_files(root, "digital-twingo/scene-design-v2/public/**/*.glb")
        + count_files(root, "digital-twingo/scene-design-v2/public/**/*.GLB"),
        frontend_images=sum(
            count_files(root, pattern)
            for pattern in (
                "digital-twingo/scene-design-v2/public/**/*.png",
                "digital-twingo/scene-design-v2/public/**/*.jpg",
                "digital-twingo/scene-design-v2/public/**/*.jpeg",
                "digital-twingo/scene-design-v2/public/**/*.PNG",
                "digital-twingo/scene-design-v2/public/**/*.JPG",
                "digital-twingo/scene-design-v2/public/**/*.JPEG",
            )
        ),
    )


def parse_active_changes(payload: Mapping[str, object]) -> list[ActiveChange]:
    raw_changes = payload.get("changes", [])
    if not isinstance(raw_changes, list):
        return []

    changes: list[ActiveChange] = []
    for item in raw_changes:
        if not isinstance(item, Mapping):
            continue
        changes.append(
            ActiveChange(
                name=str(item.get("name", "")),
                completed_tasks=int(item.get("completedTasks", 0)),
                total_tasks=int(item.get("totalTasks", 0)),
                status=str(item.get("status", "")),
            )
        )
    return changes


def default_data_sources() -> list[DataSourceStatus]:
    return [
        DataSourceStatus("IoT 设备与指标", "模拟", "`iot.simulator-enabled: true`，当前以模拟器和 mock 数据链路为主"),
        DataSourceStatus("真实设备接入", "缺失", "未发现 Phase 0 真实设备联调记录，本阶段不做真实设备控制"),
        DataSourceStatus("LLM Agent", "缺失", "`llm.enabled: false`，语义搭建保留确定性回退路径"),
        DataSourceStatus("RAG 知识库", "缺失", "`rag.enabled: false`，不可误标为已完成文档 RAG"),
        DataSourceStatus("资产元数据", "缺失", "GLB 数量多于缩略图和元数据治理结果，待 Phase 5 收敛"),
        DataSourceStatus("前端业务展示", "模拟", "业务中心、监控大屏、图表主要面向演示和模拟数据聚合"),
        DataSourceStatus("过期数据", "过期", "Phase 0 仅定义状态标签，后续对象/记忆层实现具体判定规则"),
    ]


def evaluate_hard_gates(results: Iterable[CommandResult]) -> GateResult:
    failed: list[str] = []
    warnings: list[str] = []
    for result in results:
        if result.returncode != 0:
            failed.append(result.command)
        if result.command == "npm run build":
            combined = f"{result.stdout}\n{result.stderr}".strip()
            warning_lines = [
                line.strip()
                for line in combined.splitlines()
                if "warning" in line.lower() or "(!)" in line or "larger than 500 kb" in line.lower()
            ]
            if warning_lines:
                warnings.append(f"{result.command}: {'; '.join(warning_lines[:3])}")
        elif result.stderr.strip() and result.returncode == 0 and result.command != "openspec validate --all --strict":
            warnings.append(f"{result.command}: {result.stderr.strip().splitlines()[0]}")
    return GateResult(ok=not failed, failed_commands=failed, warnings=warnings)


def render_report(
    generated_on: str,
    command_results: Sequence[CommandResult],
    active_changes: Sequence[ActiveChange],
    asset_counts: AssetCounts,
    data_sources: Sequence[DataSourceStatus],
    gate_result: GateResult,
) -> str:
    gate_text = "PASS" if gate_result.ok else "FAIL"
    lines = [
        "# Phase 0 基线收敛与开发护栏报告",
        "",
        f"生成日期：{generated_on}",
        "",
        "## 结论",
        "",
        f"- 护栏状态：{gate_text}",
        "- Phase 0 只确认基线，不实现 5 个 active changes 的业务能力。",
        "- 首个 MVP 固定为番茄温室：1 个温室、20 株番茄、1 个气象站、1 个水泵/灌溉设备、1 个摄像头、1 个传感器组。",
        "- 后续扩展锚点保留 Parcel、CropRow、CropBatch，不在 Phase 0 落库实现。",
        "- 本阶段非目标：不做真实设备控制、不做每日 GLB 重建、不做完整 RBAC。",
        "",
        "## 命令基线",
        "",
        "| 命令 | 退出码 | 状态 |",
        "| --- | ---: | --- |",
    ]
    for result in command_results:
        status = "PASS" if result.returncode == 0 else "FAIL"
        lines.append(f"| `{result.command}` | {result.returncode} | {status} |")

    if gate_result.warnings:
        lines.extend(["", "## 警告", ""])
        lines.extend(f"- {warning}" for warning in gate_result.warnings)

    if gate_result.failed_commands:
        lines.extend(["", "## 失败命令", ""])
        lines.extend(f"- `{command}`" for command in gate_result.failed_commands)

    lines.extend(
        [
            "",
            "## OpenSpec Active Changes",
            "",
            "| Change | Tasks | Status | Phase 0 判定 |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for change in active_changes:
        implementation_state = "已实现" if change.is_implemented else "未实现"
        lines.append(f"| {change.name} | {change.completed_tasks}/{change.total_tasks} | {change.status} | {implementation_state} |")

    lines.extend(
        [
            "",
            "## 资产盘点",
            "",
            "| 口径 | 数量 |",
            "| --- | ---: |",
            f"| backend scene-assets GLB | {asset_counts.backend_glb} |",
            f"| backend scene-assets/thumbs files | {asset_counts.backend_thumbnails} |",
            f"| frontend public GLB | {asset_counts.frontend_glb} |",
            f"| frontend public images | {asset_counts.frontend_images} |",
            "",
            "## 数据来源状态",
            "",
            "| 数据源 | 状态 | 证据 |",
            "| --- | --- | --- |",
        ]
    )
    for source in data_sources:
        lines.append(f"| {source.name} | {source.status} | {source.evidence} |")

    lines.extend(["", "## 命令输出摘要", ""])
    for result in command_results:
        output = redact((result.stdout + "\n" + result.stderr).strip())
        if len(output) > 2400:
            output = output[:2400] + "\n...[truncated]"
        lines.extend([f"### `{result.command}`", "", "```text", output or "(no output)", "```", ""])

    return "\n".join(lines).rstrip() + "\n"


def collect_active_changes(root: Path) -> list[ActiveChange]:
    result = run_command(["openspec", "list", "--json"], root)
    if result.returncode != 0:
        return []
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    return parse_active_changes(payload)


def run_baseline(root: Path) -> tuple[list[CommandResult], list[ActiveChange], AssetCounts, list[DataSourceStatus], GateResult]:
    command_results = [
        run_command(["openspec", "validate", "--all", "--strict"], root),
        run_shell_command("go test ./...", root / "digital-twingo" / "scene-server-go"),
        run_shell_command("npm run build", root / "digital-twingo" / "scene-design-v2"),
    ]
    active_changes = collect_active_changes(root)
    asset_counts = count_assets(root)
    data_sources = default_data_sources()
    gate_result = evaluate_hard_gates(command_results)
    return command_results, active_changes, asset_counts, data_sources, gate_result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Phase 0 baseline guard and optionally write a markdown report.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--write-report", help="Markdown report path to write.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    command_results, active_changes, asset_counts, data_sources, gate_result = run_baseline(root)
    report = render_report(
        generated_on=date.today().isoformat(),
        command_results=command_results,
        active_changes=active_changes,
        asset_counts=asset_counts,
        data_sources=data_sources,
        gate_result=gate_result,
    )

    if args.write_report:
        report_path = Path(args.write_report)
        if not report_path.is_absolute():
            report_path = root / report_path
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")
    else:
        sys.stdout.write(report)

    return 0 if gate_result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
