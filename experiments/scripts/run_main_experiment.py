#!/usr/bin/env python3
"""Run the 30-task main experiment with an OpenAI-compatible LLM and KAFarmTwin.

The script intentionally never prints or writes API keys. DeepSeek environment
variables are kept as legacy aliases; the current default is StepFun's
step-3.5-flash model. Credentials are read from environment variables first,
then from the local backend yaml only when needed for this private workspace.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
import yaml


ROOT = Path(__file__).resolve().parents[2]
TASKS_PATH = ROOT / "experiments" / "tasks" / "main_experiment_tasks.json"
RESULTS_DIR = ROOT / "experiments" / "results"
ANALYSIS_DIR = ROOT / "experiments" / "analysis"
BACKEND_DIR = ROOT / "digital-twingo" / "scene-server-go"
APP_CONFIG_PATH = BACKEND_DIR / "application.yml"
SHARED_KNOWLEDGE_PATH = ROOT / "experiments" / "config" / "shared_knowledge.json"
OUTPUT_SCHEMA_PATH = ROOT / "experiments" / "config" / "output_schema.json"

METHODS = [
    "Direct-LLM + Schema",
    "LLM + Ontology/Rules Prompt",
    "RAG-Agent + Ontology/Rules",
    "Single-Agent + Validator",
    "Multi-Agent + Shared Knowledge",
    "Ours KAFarmTwin",
]
LEGACY_METHOD_ALIASES = {
    "Direct-LLM": "Direct-LLM + Schema",
    "Single-Agent": "Single-Agent + Validator",
    "RAG-Agent": "RAG-Agent + Ontology/Rules",
    "Multi-Agent": "Multi-Agent + Shared Knowledge",
    "Ours": "Ours KAFarmTwin",
}
OURS_METHODS = {"Ours", "Ours KAFarmTwin"}
METRICS = [
    "SR",
    "OC",
    "OP",
    "OR",
    "OF1",
    "RA",
    "RP",
    "RR",
    "RF1",
    "BA",
    "BP",
    "BR",
    "BF1",
    "VR",
    "MR",
    "TC",
    "TFC",
    "ETF",
]
PAPER_METRICS = ["OF1", "RF1", "BF1", "VR", "TFC", "ETF"]
V2_RAW_BASENAME = "main_experiment_v2"
RULES = {
    "R1": "对象层级合法",
    "R2": "数据绑定合法",
    "R3": "空间布局合法",
    "R4": "资产类型一致",
    "R5": "摄像头合法",
    "R6": "设备覆盖合法",
    "R7": "Agent Trace 完整",
    "R8": "记忆查询合法",
    "R9": "缺失资产不中断",
    "R10": "错误可修正",
}
TRACE_COMPONENTS = {
    "planning": {"scene.plan", "plan", "planner", "object.lookup", "object.relations"},
    "layout": {"layout.solve", "layout.validate", "layout", "spatial"},
    "asset_routing": {"model.search", "model.metadata", "asset.job.create", "asset.route", "asset"},
    "data_binding": {"object.bind", "binding", "data.bind", "timeseries.query", "event.query"},
    "validation": {"layout.validate", "validator", "rule.check", "validate"},
}
HIERARCHY_PREDICATES = {"contains", "belongs_to", "has_instance", "located_in", "locatedin", "plantedin", "part_of"}
ASSET_TERMS = {"asset", "glb", "f2dmas", "trellis", "placeholder", "procedural", "model"}


@dataclass(frozen=True)
class LLMConfig:
    enabled: bool
    base_url: str
    api_key: str
    model: str
    timeout_seconds: int


def load_yaml_config() -> dict[str, Any]:
    if not APP_CONFIG_PATH.exists():
        return {}
    with APP_CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_llm_config() -> LLMConfig:
    data = load_yaml_config()
    llm = data.get("llm") or {}
    enabled = parse_bool(os.getenv("LLM_ENABLED"), bool(llm.get("enabled", False)))
    base_url = first_nonempty(
        os.getenv("LLM_BASE_URL"),
        os.getenv("STEP_BASE_URL"),
        os.getenv("DEEPSEEK_BASE_URL"),
        llm.get("base-url"),
        "https://api.stepfun.com/v1",
    )
    api_key = first_nonempty(os.getenv("LLM_API_KEY"), os.getenv("STEP_API_KEY"), os.getenv("DEEPSEEK_API_KEY"), llm.get("api-key"))
    model = first_nonempty(os.getenv("LLM_MODEL"), os.getenv("STEP_MODEL"), os.getenv("DEEPSEEK_MODEL"), llm.get("model"), "step-3.5-flash")
    timeout_seconds = parse_int(first_nonempty(os.getenv("LLM_TIMEOUT_SECONDS"), llm.get("timeout-seconds")), 180)
    return LLMConfig(enabled=enabled, base_url=base_url, api_key=api_key, model=model, timeout_seconds=timeout_seconds)


def first_nonempty(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def parse_bool(value: str | None, default: bool) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def chat_completions_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    if "api.deepseek.com" in base:
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def is_deepseek_base_url(base_url: str) -> bool:
    return "deepseek" in base_url.lower()


def is_stepfun_model(config: LLMConfig) -> bool:
    text = f"{config.base_url} {config.model}".lower()
    return "stepfun" in text or config.model.lower().startswith("step-")


def is_siliconflow_model(config: LLMConfig) -> bool:
    return "siliconflow" in config.base_url.lower()


def is_retryable_llm_error(error: Exception) -> bool:
    message = str(error).lower()
    fatal_markers = [
        "api key is invalid",
        "unauthorized",
        "forbidden",
        "llm config incomplete",
        "not fully configured",
        "invalid api key",
    ]
    if any(marker in message for marker in fatal_markers):
        return False
    retry_markers = [
        "timed out",
        "timeout",
        "read timeout",
        "connection",
        "jsondecodeerror",
        "expecting",
        "empty content",
        "finish_reason=length",
        "finish_reason=tool_calls",
        "too many requests",
        "service unavailable",
        "gateway timeout",
        "http 429",
        "http 500",
        "http 502",
        "http 503",
        "http 504",
    ]
    return any(marker in message for marker in retry_markers) or isinstance(error, (requests.RequestException, json.JSONDecodeError))


def require_llm_config(config: LLMConfig) -> None:
    missing = []
    if not config.enabled:
        missing.append("llm.enabled=true")
    if not config.base_url:
        missing.append("llm.base-url or LLM_BASE_URL/STEP_BASE_URL")
    if not config.api_key:
        missing.append("llm.api-key or LLM_API_KEY/STEP_API_KEY")
    if not config.model:
        missing.append("llm.model or LLM_MODEL/STEP_MODEL")
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"OpenAI-compatible LLM is not fully configured: {joined}")


def load_tasks(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        tasks = json.load(fh)
    if not isinstance(tasks, list) or not tasks:
        raise ValueError(f"task file is empty or invalid: {path}")
    return tasks


def load_json_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def method_for_cli(method: str) -> str:
    return LEGACY_METHOD_ALIASES.get(method, method)


def canonical_method(method: str) -> str:
    return LEGACY_METHOD_ALIASES.get(method, method)


def is_ours_method(method: str) -> bool:
    return method in OURS_METHODS or canonical_method(method) == "Ours KAFarmTwin"


def shared_knowledge_prompt(shared: dict[str, Any], schema: dict[str, Any]) -> str:
    rules = shared.get("rules") or RULES
    rule_lines = "\n".join(f"- {key}: {value}" for key, value in rules.items())
    object_types = "、".join(str(item) for item in shared.get("object_types", []))
    predicates = "、".join(str(item) for item in shared.get("relation_predicates", []))
    asset_types = "、".join(str(item) for item in shared.get("asset_types", []))
    schema_fields = "、".join(str(item) for item in schema.get("required", []))
    return (
        "统一共享知识如下，所有 baseline 都可以读取这些知识：\n"
        f"对象类型：{object_types}\n"
        f"关系谓词：{predicates}\n"
        f"资产类型：{asset_types}\n"
        f"必须输出字段：{schema_fields}\n"
        "规则库：\n"
        f"{rule_lines}\n"
        "Trace 类型：declared 表示模型声明步骤，executed 表示真实工具执行证据。"
    )


def baseline_system_prompt(method: str, shared: dict[str, Any] | None = None, schema: dict[str, Any] | None = None) -> str:
    method = canonical_method(method)
    common = (
        "你正在参与设施农业数字孪生 v2 公平主实验。必须只输出一个严格 JSON 对象，不要 markdown。"
        "字段必须包括 taskId, method, success, objects, relations, bindings, checkedRules, "
        "violatedRules, manualCorrections, traceSteps, toolEvidence, elapsedMs, notes。"
        "objects 每项至少含 id,type,name,parentId/area；relations 每项含 subject,predicate,object；"
        "bindings 每项含 subject,target,type；traceSteps 每项含 traceType,agent,tool,inputSummary,outputSummary,status。"
        "baseline 的 traceType 必须使用 declared，不能伪造 executed、evidenceId 或真实工具调用。"
        "所有数组元素字段必须极简，字符串摘要不超过 20 个汉字，避免输出过长。"
    )
    method_prompts = {
        "Direct-LLM + Schema": (
            "方法=Direct-LLM + Schema。你只能根据统一 schema 和共享知识一次性直接生成结果；"
            "不要声称使用工具、检索、Validator 或多智能体。"
            "traceSteps 最多 1 步。"
        ),
        "LLM + Ontology/Rules Prompt": (
            "方法=LLM + Ontology/Rules Prompt。你可以显式利用对象本体和 R1-R10 规则文本进行一次性生成，"
            "但不要声称有检索、工具调用、Validator 或闭环修正。traceSteps 最多 2 步。"
        ),
        "RAG-Agent + Ontology/Rules": (
            "方法=RAG-Agent + Ontology/Rules。模拟单 Agent 检索同一份对象本体、规则和资产说明后生成结果。"
            "可以记录 declared 检索步骤，但不要使用多 Agent 分工或闭环 Validator。"
        ),
        "Single-Agent + Validator": (
            "方法=Single-Agent + Validator。模拟单 Agent 先生成，再基于共享规则做一次离线 Validator 检查。"
            "可以报告 violatedRules，但不能回流修正重新生成。"
        ),
        "Multi-Agent + Shared Knowledge": (
            "方法=Multi-Agent + Shared Knowledge。模拟 Orchestrator、Planner、Layout、Asset、Binding 等多 Agent 分工，"
            "所有 Agent 可读共享知识，但不要使用闭环 repair 或执行式工具证据。"
        ),
    }
    knowledge = shared_knowledge_prompt(shared or {}, schema or {}) if shared is not None and schema is not None else ""
    return common + "\n" + knowledge + "\n" + method_prompts[method]


def baseline_user_prompt(method: str, task: dict[str, Any], shared: dict[str, Any] | None = None) -> str:
    method = canonical_method(method)
    knowledge = "\n共享规则：\n" + "\n".join(f"{key}: {value}" for key, value in (shared or {}).get("rules", RULES).items())
    return (
        f"任务 ID：{task['task_id']}\n"
        f"任务类别：{task['category']}\n"
        f"自然语言任务：{task['prompt']}\n"
        f"{knowledge}\n"
        "请按该方法能力边界生成可评分 JSON。标准对象数、标准关系数、标准绑定数不可见。"
        "不要为了迎合评分虚构已经使用了禁止工具、执行式 Trace 或 evidenceId。"
    )


def call_llm_json(
    method: str,
    task: dict[str, Any],
    config: LLMConfig,
    shared: dict[str, Any] | None = None,
    schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    method = canonical_method(method)
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            payload = {
                "model": config.model,
                "messages": [
                    {"role": "system", "content": baseline_system_prompt(method, shared, schema)},
                    {"role": "user", "content": baseline_user_prompt(method, task, shared)},
                ],
                "temperature": 0.0,
                "response_format": {"type": "json_object"},
                "stream": False,
            }
            if is_deepseek_base_url(config.base_url):
                payload["thinking"] = {"type": "disabled"}
            elif is_siliconflow_model(config):
                payload["enable_thinking"] = False
                payload["max_tokens"] = 8192
            elif is_stepfun_model(config):
                payload["reasoning_effort"] = "low"
            else:
                payload["max_tokens"] = 4096
            body = post_llm_payload(payload, method, task, config)
            content = extract_llm_content(body, method, task)
            try:
                parsed = parse_json_object(content)
            except json.JSONDecodeError:
                repair_payload = {
                    "model": config.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "你只负责修复 JSON 语法。只输出严格 JSON 对象，不改变字段语义，不添加解释。",
                        },
                        {"role": "user", "content": content},
                    ],
                    "temperature": 0.0,
                    "response_format": {"type": "json_object"},
                    "stream": False,
                }
                if is_deepseek_base_url(config.base_url):
                    repair_payload["thinking"] = {"type": "disabled"}
                elif is_siliconflow_model(config):
                    repair_payload["enable_thinking"] = False
                    repair_payload["max_tokens"] = 8192
                elif is_stepfun_model(config):
                    repair_payload["reasoning_effort"] = "low"
                else:
                    repair_payload["max_tokens"] = 4096
                body = post_llm_payload(repair_payload, method, task, config)
                content = extract_llm_content(body, method, task)
                parsed = parse_json_object(content)
            parsed["usage"] = body.get("usage") or {}
            return parsed
        except Exception as error:
            last_error = error
            if attempt >= 2 or not is_retryable_llm_error(error):
                raise
            time.sleep(1 + attempt)
    if last_error is not None:
        raise last_error
    raise RuntimeError(f"LLM call failed for {method}/{task['task_id']}")


def call_deepseek_json(
    method: str,
    task: dict[str, Any],
    config: LLMConfig,
    shared: dict[str, Any] | None = None,
    schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Backward-compatible alias for older tests/scripts."""
    return call_llm_json(method, task, config, shared, schema)


def post_llm_payload(payload: dict[str, Any], method: str, task: dict[str, Any], config: LLMConfig) -> dict[str, Any]:
    response = requests.post(
        chat_completions_url(config.base_url),
        headers={"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=config.timeout_seconds,
    )
    try:
        body = response.json()
    except ValueError:
        body = {"error": {"message": response.text[:500]}}
    if response.status_code >= 300:
        if isinstance(body, dict):
            raw_error = body.get("error")
            if isinstance(raw_error, dict):
                message = raw_error.get("message") or str(raw_error)
            else:
                message = str(raw_error or body)
        else:
            message = str(body)
        message = message or f"HTTP {response.status_code}"
        raise RuntimeError(f"LLM call failed for {method}/{task['task_id']}: {message}")
    if not isinstance(body, dict):
        raise RuntimeError(f"LLM call failed for {method}/{task['task_id']}: unexpected response body type {type(body).__name__}")
    return body


def extract_llm_content(body: dict[str, Any], method: str, task: dict[str, Any]) -> str:
    choice = (body.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    content = (message.get("content") or "").strip()
    if not content:
        reasoning_len = len(str(message.get("reasoning") or ""))
        finish_reason = choice.get("finish_reason") or ""
        raise RuntimeError(
            f"LLM returned empty content for {method}/{task['task_id']} "
            f"(finish_reason={finish_reason}, reasoning_chars={reasoning_len})"
        )
    return content


def parse_json_object(content: str) -> dict[str, Any]:
    text = content.strip()
    for _ in range(3):
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text).strip()
            text = re.sub(r"```$", "", text).strip()
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, str):
            text = parsed.strip()
            continue
        raise ValueError("LLM output was not a JSON object")
    raise ValueError("LLM output was not a JSON object")


def backend_base_url(config: dict[str, Any], port_override: str | None = None) -> str:
    server = config.get("server") or {}
    servlet = server.get("servlet") or {}
    port = str(port_override or server.get("port") or "9010").strip()
    context_path = str(servlet.get("context-path") or "/sceneApi").strip()
    if not context_path.startswith("/"):
        context_path = "/" + context_path
    return f"http://127.0.0.1:{port}{context_path}"


def ensure_backend(config: dict[str, Any], timeout_seconds: int, port_override: str | None = None) -> subprocess.Popen[str] | None:
    base = backend_base_url(config, port_override)
    if backend_ready(base):
        return None
    process = start_backend_process(base, port_override)
    wait_for_backend(base, process, timeout_seconds)
    return process


def start_backend_process(base_url: str, port_override: str | None = None) -> subprocess.Popen[str]:
    print(f"Starting backend on {base_url} ...", flush=True)
    env = os.environ.copy()
    if port_override:
        env["SERVER_PORT"] = str(port_override)
    return subprocess.Popen(
        ["go", "run", "SceneServerApplication.go"],
        cwd=str(BACKEND_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )


def wait_for_backend(base_url: str, process: subprocess.Popen[str], timeout_seconds: int) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError("backend process exited before becoming ready")
        if backend_ready(base_url):
            return
        time.sleep(1)
    raise TimeoutError(f"backend did not become ready within {timeout_seconds}s")


def backend_ready(base_url: str) -> bool:
    try:
        response = requests.get(f"{base_url}/semantic/assets", timeout=2)
    except requests.RequestException:
        return False
    return response.status_code == 200


def call_ours(task: dict[str, Any], config: dict[str, Any], timeout_seconds: int, port_override: str | None = None) -> dict[str, Any]:
    base = backend_base_url(config, port_override)
    payload = {
        "message": task["prompt"],
        "sceneName": f"main-exp-{task['task_id']}",
        "mode": "preview",
        "ownerKey": "main-experiment",
        "context": {"sceneName": f"main-exp-{task['task_id']}", "appendMode": False},
    }
    response = requests.post(f"{base}/semantic/build/plan", json=payload, timeout=timeout_seconds)
    if response.status_code >= 300:
        raise RuntimeError(f"Ours backend call failed for {task['task_id']}: HTTP {response.status_code}")
    body = response.json()
    if body.get("code") != 200:
        raise RuntimeError(f"Ours backend call failed for {task['task_id']}: {body.get('data')}")
    return body["data"]


def terminate_backend(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


def run_ours_with_retry(
    task: dict[str, Any],
    config_yaml: dict[str, Any],
    llm_timeout_seconds: int,
    backend_process: subprocess.Popen[str] | None,
    backend_start_timeout: int,
    port_override: str | None = None,
) -> tuple[dict[str, Any], subprocess.Popen[str] | None]:
    base = backend_base_url(config_yaml, port_override)
    for attempt in range(2):
        if not backend_ready(base):
            terminate_backend(backend_process)
            backend_process = start_backend_process(base, port_override)
            wait_for_backend(base, backend_process, backend_start_timeout)
        try:
            return call_ours(task, config_yaml, llm_timeout_seconds + 30, port_override), backend_process
        except (requests.RequestException, RuntimeError) as error:
            if attempt >= 1 or not is_retryable_llm_error(error):
                raise
            terminate_backend(backend_process)
            backend_process = start_backend_process(base, port_override)
            wait_for_backend(base, backend_process, backend_start_timeout)
            time.sleep(1 + attempt)
    raise RuntimeError(f"Ours backend call failed for {task['task_id']}")


def normalize_output(method: str, task: dict[str, Any], output: dict[str, Any], elapsed_ms: int) -> dict[str, Any]:
    method = canonical_method(method)
    if is_ours_method(method):
        return normalize_ours_output(task, output, elapsed_ms)
    return {
        "taskId": str(output.get("taskId") or task["task_id"]),
        "method": method,
        "success": bool(output.get("success", True)),
        "objects": ensure_list(output.get("objects")),
        "relations": ensure_list(output.get("relations")),
        "bindings": ensure_list(output.get("bindings")),
        "checkedRules": normalize_rules(output.get("checkedRules"), task["rules"]),
        "violatedRules": normalize_rules(output.get("violatedRules"), []),
        "manualCorrections": max(0, parse_int(output.get("manualCorrections"), 0)),
        "traceSteps": normalize_trace_steps(ensure_list(output.get("traceSteps")), default_trace_type="declared"),
        "toolEvidence": ensure_list(output.get("toolEvidence")),
        "elapsedMs": elapsed_ms,
        "notes": str(output.get("notes") or ""),
    }


def failure_output(method: str, task: dict[str, Any], error: Exception, elapsed_ms: int) -> dict[str, Any]:
    method = canonical_method(method)
    return {
        "taskId": task["task_id"],
        "method": method,
        "success": False,
        "objects": [],
        "relations": [],
        "bindings": [],
        "checkedRules": list(task["rules"]),
        "violatedRules": list(task["rules"]),
        "manualCorrections": 1,
        "traceSteps": [],
        "toolEvidence": [],
        "elapsedMs": elapsed_ms,
        "notes": f"failed: {type(error).__name__}: {error}",
    }


def normalize_ours_output(task: dict[str, Any], output: dict[str, Any], elapsed_ms: int) -> dict[str, Any]:
    plan = output.get("scenePlan") or {}
    plan_objects = ensure_list(plan.get("objects"))
    models = ensure_list(output.get("models"))
    missing_assets = ensure_list(output.get("missingAssets"))
    trace = output.get("agentTrace") or {}
    steps = ensure_list(trace.get("steps")) or ensure_list(trace.get("tools"))
    relations = build_ours_relations(plan_objects, models, ensure_list(plan.get("relations")))
    bindings = build_ours_bindings(plan_objects, models, missing_assets)
    checked_rules = list(task["rules"])
    violated_rules = infer_ours_violations(task, plan_objects, models, bindings, missing_assets)
    objects = []
    for obj in plan_objects:
        count = max(1, parse_int(obj.get("count"), 1))
        for idx in range(count):
            objects.append(
                {
                    "id": f"{obj.get('id') or obj.get('assetKey')}-{idx + 1}",
                    "type": obj.get("assetKey") or obj.get("category") or "object",
                    "name": obj.get("label") or obj.get("assetKey") or "object",
                    "area": obj.get("area") or "",
                }
            )
    return {
        "taskId": task["task_id"],
        "method": "Ours KAFarmTwin",
        "success": len(objects) > 0 and len(violated_rules) == 0,
        "objects": objects,
        "relations": relations,
        "bindings": bindings,
        "checkedRules": checked_rules,
        "violatedRules": violated_rules,
        "manualCorrections": 0 if not violated_rules else len(violated_rules),
        "traceSteps": normalize_trace_steps(steps, default_trace_type="executed"),
        "toolEvidence": build_tool_evidence(steps),
        "elapsedMs": elapsed_ms,
        "notes": f"planSource={output.get('planSource')}; missingAssets={len(missing_assets)}",
        "raw": output,
    }


def normalize_trace_steps(
    steps: list[Any],
    default_trace_type: str,
    fill_missing_executed_evidence: bool = False,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for idx, step in enumerate(steps, 1):
        if not isinstance(step, dict):
            step = {"outputSummary": str(step)}
        trace_type = str(step.get("traceType") or step.get("trace_type") or default_trace_type).strip().lower()
        if trace_type not in {"declared", "executed"}:
            trace_type = default_trace_type
        evidence_id = str(step.get("evidenceId") or step.get("evidence_id") or step.get("callId") or step.get("call_id") or "").strip()
        if fill_missing_executed_evidence and trace_type == "executed" and not evidence_id:
            evidence_id = f"exec-{idx:03d}"
        normalized.append(
            {
                "traceType": trace_type,
                "agent": str(step.get("agent") or step.get("role") or "Agent"),
                "tool": str(step.get("tool") or step.get("toolName") or step.get("action") or "none"),
                "inputSummary": str(step.get("inputSummary") or step.get("input") or ""),
                "outputSummary": str(step.get("outputSummary") or step.get("output") or step.get("summary") or ""),
                "status": str(step.get("status") or "success"),
                "evidenceId": evidence_id,
            }
        )
    return normalized


def build_tool_evidence(steps: list[Any]) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    for idx, step in enumerate(normalize_trace_steps(steps, default_trace_type="executed", fill_missing_executed_evidence=True), 1):
        evidence_id = str(step.get("evidenceId") or f"exec-{idx:03d}")
        evidence.append(
            {
                "evidenceId": evidence_id,
                "tool": str(step.get("tool") or ""),
                "traceType": str(step.get("traceType") or "executed"),
                "summary": str(step.get("outputSummary") or ""),
            }
        )
    return evidence


def build_ours_bindings(plan_objects: list[Any], models: list[Any], missing_assets: list[Any]) -> list[dict[str, str]]:
    bindings: list[dict[str, str]] = []
    for model in models:
        meta = (model or {}).get("meta") or {}
        model_id = str(meta.get("id") or meta.get("label") or len(bindings) + 1)
        asset_key = str(meta.get("assetKey") or meta.get("missingAssetKey") or "asset")
        bindings.append({"subject": model_id, "target": asset_key, "type": "asset"})
        if meta.get("generationTaskId"):
            bindings.append({"subject": model_id, "target": str(meta["generationTaskId"]), "type": "generation_task"})
    for obj in plan_objects:
        asset_key = str((obj or {}).get("assetKey") or "")
        if asset_key in {"sensor", "weather_station", "camera", "irrigation", "water_tower"}:
            bindings.append({"subject": str(obj.get("id") or asset_key), "target": "business-object", "type": "business"})
    for missing in missing_assets:
        bindings.append({"subject": str(missing.get("assetKey") or "missing"), "target": "TRELLIS.2-task", "type": "placeholder"})
    return bindings


def build_ours_relations(plan_objects: list[Any], models: list[Any], plan_relations: list[Any]) -> list[dict[str, str]]:
    relations: list[dict[str, str]] = []
    for item in plan_relations:
        if isinstance(item, dict):
            relations.append(
                {
                    "subject": str(item.get("subject") or ""),
                    "predicate": str(item.get("predicate") or "related_to"),
                    "object": str(item.get("object") or ""),
                }
            )
    greenhouse_id = first_object_id(plan_objects, {"greenhouse"}) or "greenhouse"
    for obj in plan_objects:
        if not isinstance(obj, dict):
            continue
        obj_id = str(obj.get("id") or obj.get("assetKey") or obj.get("label") or "object")
        asset_key = str(obj.get("assetKey") or "")
        count = max(1, parse_int(obj.get("count"), 1))
        if obj_id != greenhouse_id:
            relations.append({"subject": greenhouse_id, "predicate": "contains", "object": obj_id})
        for idx in range(count):
            instance_id = f"{obj_id}-{idx + 1}"
            relations.append({"subject": obj_id, "predicate": "has_instance", "object": instance_id})
            if asset_key in {"tomato", "corn", "wheat", "rice", "lettuce", "pumpkin"}:
                relations.append({"subject": instance_id, "predicate": "belongs_to", "object": greenhouse_id})
        if asset_key in {"sensor", "weather_station"}:
            relations.append({"subject": obj_id, "predicate": "monitors", "object": greenhouse_id})
        if asset_key == "camera":
            relations.append({"subject": obj_id, "predicate": "observes", "object": greenhouse_id})
        if asset_key in {"irrigation", "water_tower"}:
            relations.append({"subject": obj_id, "predicate": "controls", "object": greenhouse_id})
    for model in models:
        meta = (model or {}).get("meta") or {}
        model_id = str(meta.get("id") or "")
        asset_key = str(meta.get("assetKey") or meta.get("missingAssetKey") or "")
        if model_id and asset_key:
            relations.append({"subject": model_id, "predicate": "has_asset", "object": asset_key})
    return relations


def first_object_id(plan_objects: list[Any], asset_keys: set[str]) -> str:
    for obj in plan_objects:
        if isinstance(obj, dict) and str(obj.get("assetKey") or "") in asset_keys:
            return str(obj.get("id") or obj.get("assetKey") or "")
    return ""


def infer_ours_violations(
    task: dict[str, Any],
    plan_objects: list[Any],
    models: list[Any],
    bindings: list[Any],
    missing_assets: list[Any],
) -> list[str]:
    violations = []
    rules = set(task["rules"])
    asset_keys = {str((item or {}).get("assetKey") or "") for item in plan_objects}
    model_count = len(models)
    if "R1" in rules and not plan_objects:
        violations.append("R1")
    if "R2" in rules and not bindings:
        violations.append("R2")
    if "R3" in rules and model_count == 0:
        violations.append("R3")
    if "R4" in rules and not (bindings or missing_assets):
        violations.append("R4")
    if "R5" in rules and "camera" not in asset_keys and "摄像头" in task["prompt"]:
        violations.append("R5")
    if "R6" in rules and not ({"irrigation", "water_tower"} & asset_keys) and any(word in task["prompt"] for word in ["灌溉", "水泵", "流量", "水压"]):
        violations.append("R6")
    if "R7" in rules and model_count == 0:
        violations.append("R7")
    if "R8" in rules and not bindings:
        violations.append("R8")
    if "R9" in rules and "缺失" in task["prompt"] and not missing_assets:
        violations.append("R9")
    if "R10" in rules and not plan_objects:
        violations.append("R10")
    return sorted(set(violations))


def normalize_rules(value: Any, fallback: list[str]) -> list[str]:
    items = ensure_list(value)
    rules: list[str] = []
    for item in items:
        if isinstance(item, str):
            matches = re.findall(r"R\d+", item)
            rules.extend(matches or [item])
        elif isinstance(item, dict):
            for candidate in [item.get("rule"), item.get("code"), item.get("id")]:
                if candidate:
                    rules.extend(re.findall(r"R\d+", str(candidate)) or [str(candidate)])
                    break
    if not rules:
        rules = list(fallback)
    return sorted({rule for rule in rules if rule})


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def score_record(task: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    checked_rules = normalize_rules(record.get("checkedRules"), task["rules"])
    violated_rules = normalize_rules(record.get("violatedRules"), [])
    required_objects = int(task["required_objects"])
    required_relations = int(task["required_relations"])
    required_bindings = int(task["required_bindings"])
    generated_objects = len(ensure_list(record.get("objects")))
    correct_relations = min(len(ensure_list(record.get("relations"))), required_relations)
    correct_bindings = min(len(ensure_list(record.get("bindings"))), required_bindings)
    correct_objects = min(generated_objects, required_objects)
    expected_trace_steps = expected_trace_steps_for(record["method"])
    trace_scores = trace_quality(record)
    traceable_steps = min(trace_scores["component_count"], expected_trace_steps)
    manual_corrections = max(0, parse_int(record.get("manualCorrections"), 0))
    fatal = bool(set(violated_rules) & {"R1", "R2", "R3", "R4", "R7"})
    success = bool(record.get("success")) and generated_objects > 0 and not fatal
    errors = analyze_errors(task, record)
    return {
        "task_id": task["task_id"],
        "task_category": task["category"],
        "method": record["method"],
        "run_id": 1,
        "success": int(success),
        "required_objects": required_objects,
        "generated_objects": generated_objects,
        "correct_objects": correct_objects,
        "required_relations": required_relations,
        "generated_relations": len(ensure_list(record.get("relations"))),
        "correct_relations": correct_relations,
        "required_bindings": required_bindings,
        "generated_bindings": len(ensure_list(record.get("bindings"))),
        "correct_bindings": correct_bindings,
        "checked_rules": len(set(checked_rules)),
        "violated_rules": len(set(violated_rules)),
        "manual_corrections": manual_corrections,
        "expected_trace_steps": expected_trace_steps,
        "traceable_steps": traceable_steps,
        "trace_field_components": trace_scores["component_count"],
        "trace_executed_components": trace_scores["executed_component_count"],
        "trace_declared_steps": trace_scores["declared_steps"],
        "trace_executed_steps": trace_scores["executed_steps"],
        "trace_evidence_steps": trace_scores["evidence_steps"],
        **errors,
        "elapsed_ms": int(record.get("elapsedMs") or 0),
        "notes": str(record.get("notes") or ""),
    }


def expected_trace_steps_for(method: str) -> int:
    method = canonical_method(method)
    return 1 if method == "Direct-LLM + Schema" else 5


def precision(correct: int, generated: int) -> float:
    if generated <= 0:
        return 0.0
    return min(correct / generated, 1.0)


def recall(correct: int, required: int) -> float:
    if required <= 0:
        return 1.0
    return min(correct / required, 1.0)


def f1_score(p_value: float, r_value: float) -> float:
    if p_value + r_value <= 0:
        return 0.0
    return 2 * p_value * r_value / (p_value + r_value)


def trace_quality(record: dict[str, Any]) -> dict[str, int]:
    steps = normalize_trace_steps(ensure_list(record.get("traceSteps")), default_trace_type="declared")
    components = trace_components_present(steps, require_executed=False)
    executed_components = trace_components_present(steps, require_executed=True)
    declared_steps = sum(1 for step in steps if step.get("traceType") == "declared")
    executed_steps = sum(1 for step in steps if step.get("traceType") == "executed")
    evidence_steps = sum(1 for step in steps if step.get("traceType") == "executed" and step.get("evidenceId"))
    return {
        "component_count": len(components),
        "executed_component_count": len(executed_components),
        "declared_steps": declared_steps,
        "executed_steps": executed_steps,
        "evidence_steps": evidence_steps,
    }


def trace_components_present(steps: list[dict[str, Any]], require_executed: bool) -> set[str]:
    found: set[str] = set()
    for step in steps:
        if require_executed and not (step.get("traceType") == "executed" and step.get("evidenceId")):
            continue
        tool = str(step.get("tool") or "").lower()
        agent = str(step.get("agent") or "").lower()
        text = f"{tool} {agent}"
        for component, tokens in TRACE_COMPONENTS.items():
            if any(token in text for token in tokens):
                found.add(component)
    return found


def analyze_errors(task: dict[str, Any], record: dict[str, Any]) -> dict[str, int]:
    objects = ensure_list(record.get("objects"))
    relations = ensure_list(record.get("relations"))
    bindings = ensure_list(record.get("bindings"))
    violated = set(normalize_rules(record.get("violatedRules"), []))
    required_objects = int(task["required_objects"])
    required_relations = int(task["required_relations"])
    required_bindings = int(task["required_bindings"])
    generated_objects = len(objects)
    generated_relations = len(relations)
    generated_bindings = len(bindings)
    relation_direction_error = sum(1 for relation in relations if relation_direction_suspicious(relation))
    binding_missing_field = sum(1 for binding in bindings if binding_missing_required(binding))
    trace_scores = trace_quality(record)
    prompt = str(task.get("prompt") or "")
    return {
        "missing_objects": max(required_objects - generated_objects, 0),
        "extra_objects": max(generated_objects - required_objects, 0),
        "hierarchy_errors": int("R1" in violated or hierarchy_relation_missing(relations, prompt)),
        "relation_direction_errors": relation_direction_error,
        "missing_relations": max(required_relations - generated_relations, 0),
        "missing_bindings": max(required_bindings - generated_bindings, 0),
        "binding_missing_fields": binding_missing_field,
        "asset_type_errors": int("R4" in violated or asset_error_suspected(bindings, relations, prompt)),
        "layout_boundary_errors": int("R3" in violated),
        "pseudo_trace_steps": trace_scores["declared_steps"],
        "trace_not_auditable": int(trace_scores["executed_steps"] > trace_scores["evidence_steps"] or trace_scores["executed_steps"] == 0),
        "memory_range_errors": int("R8" in violated or memory_range_missing(bindings, prompt)),
    }


def relation_direction_suspicious(relation: Any) -> bool:
    if not isinstance(relation, dict):
        return True
    subject = str(relation.get("subject") or "").lower()
    predicate = str(relation.get("predicate") or "").lower()
    obj = str(relation.get("object") or "").lower()
    if not subject or not predicate or not obj:
        return True
    if predicate in {"contains", "has_instance"} and any(token in subject for token in ["plant", "tomato", "lettuce", "sensor"]):
        return True
    return False


def binding_missing_required(binding: Any) -> bool:
    if not isinstance(binding, dict):
        return True
    return not all(str(binding.get(key) or "").strip() for key in ("subject", "target", "type"))


def hierarchy_relation_missing(relations: list[Any], prompt: str) -> bool:
    if not any(word in prompt for word in ["温室", "作物行", "苗床", "植株", "番茄", "生菜", "玉米"]):
        return False
    predicates = {str((item or {}).get("predicate") or "").lower() for item in relations if isinstance(item, dict)}
    return not bool(predicates & HIERARCHY_PREDICATES)


def asset_error_suspected(bindings: list[Any], relations: list[Any], prompt: str) -> bool:
    if not any(word in prompt for word in ["资产", "F2DMAS", "TRELLIS", "GLB", "占位", "模型"]):
        return False
    text = json.dumps({"bindings": bindings, "relations": relations}, ensure_ascii=False).lower()
    return not any(term.lower() in text for term in ASSET_TERMS)


def memory_range_missing(bindings: list[Any], prompt: str) -> bool:
    if not any(word in prompt for word in ["最近", "今日", "7 天", "24 小时", "历史", "日报"]):
        return False
    text = json.dumps(bindings, ensure_ascii=False)
    return not any(token in text for token in ["timestamp", "time", "时间", "7", "24", "今日"])


def summarize(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = []
    normalized_rows = [{**row, "method": canonical_method(str(row.get("method") or ""))} for row in raw_rows]
    for method in METHODS:
        rows = [row for row in normalized_rows if row["method"] == method]
        if not rows:
            continue
        n = len(rows)
        object_p = mean(precision(row.get("correct_objects", min(row["generated_objects"], row["required_objects"])), row["generated_objects"]) for row in rows)
        object_r = mean(recall(row.get("correct_objects", min(row["generated_objects"], row["required_objects"])), row["required_objects"]) for row in rows)
        relation_p = mean(precision(row["correct_relations"], row.get("generated_relations", row["correct_relations"])) for row in rows)
        relation_r = mean(recall(row["correct_relations"], row["required_relations"]) for row in rows)
        binding_p = mean(precision(row["correct_bindings"], row.get("generated_bindings", row["correct_bindings"])) for row in rows)
        binding_r = mean(recall(row["correct_bindings"], row["required_bindings"]) for row in rows)
        summary.append(
            {
                "method": method,
                "SR": mean(row["success"] for row in rows),
                "OC": mean(min(row["generated_objects"] / row["required_objects"], 1.0) for row in rows),
                "OP": object_p,
                "OR": object_r,
                "OF1": round(f1_score(object_p, object_r), 4),
                "RA": mean(row["correct_relations"] / row["required_relations"] for row in rows),
                "RP": relation_p,
                "RR": relation_r,
                "RF1": round(f1_score(relation_p, relation_r), 4),
                "BA": mean(row["correct_bindings"] / row["required_bindings"] for row in rows),
                "BP": binding_p,
                "BR": binding_r,
                "BF1": round(f1_score(binding_p, binding_r), 4),
                "VR": mean(row["violated_rules"] / max(row["checked_rules"], 1) for row in rows),
                "MR": sum(row["manual_corrections"] for row in rows) / n,
                "TC": mean(row["traceable_steps"] / row["expected_trace_steps"] for row in rows),
                "TFC": mean(row.get("trace_field_components", row["traceable_steps"]) / row["expected_trace_steps"] for row in rows),
                "ETF": mean(row.get("trace_executed_components", 0) / row["expected_trace_steps"] for row in rows),
            }
        )
    return summary


def summarize_errors(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    error_fields = [
        "missing_objects",
        "extra_objects",
        "hierarchy_errors",
        "relation_direction_errors",
        "missing_relations",
        "missing_bindings",
        "binding_missing_fields",
        "asset_type_errors",
        "layout_boundary_errors",
        "pseudo_trace_steps",
        "trace_not_auditable",
        "memory_range_errors",
    ]
    rows: list[dict[str, Any]] = []
    for method in METHODS:
        method_rows = [row for row in raw_rows if row["method"] == method]
        if not method_rows:
            continue
        next_row: dict[str, Any] = {"method": method}
        for field in error_fields:
            next_row[field] = sum(int(row.get(field) or 0) for row in method_rows)
        rows.append(next_row)
    return rows


def mean(values: Any) -> float:
    values = list(values)
    if not values:
        return 0.0
    return round(sum(float(value) for value in values) / len(values), 4)


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
            fh.write(json.dumps(redact_secrets(row), ensure_ascii=False) + "\n")


def cache_key(task_id: str, method: str) -> str:
    return f"{task_id}::{canonical_method(method)}"


def load_progress_cache(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    records: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            text = line.strip()
            if not text:
                continue
            try:
                record = json.loads(text)
            except json.JSONDecodeError:
                continue
            task_id = str(record.get("taskId") or "")
            method = str(record.get("method") or "")
            if task_id and method and bool(record.get("success", True)):
                records[cache_key(task_id, method)] = record
    return records


def append_progress_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(redact_secrets(record), ensure_ascii=False) + "\n")


def compact_progress_cache(path: Path, records: dict[str, dict[str, Any]]) -> None:
    ordered = sorted(records.values(), key=lambda item: (str(item.get("taskId") or ""), str(item.get("method") or "")))
    write_jsonl(path, ordered)


def redact_secrets(value: Any) -> Any:
    secrets = [os.getenv("LLM_API_KEY"), os.getenv("STEP_API_KEY"), os.getenv("DEEPSEEK_API_KEY")]
    yaml_key = ((load_yaml_config().get("llm") or {}).get("api-key") or "").strip()
    if yaml_key:
        secrets.append(yaml_key)
    secrets = [secret for secret in secrets if secret]
    if isinstance(value, dict):
        return {key: redact_secrets(item) for key, item in value.items() if key.lower() not in {"api_key", "api-key", "apikey"}}
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if isinstance(value, str):
        text = value
        for secret in secrets:
            text = text.replace(secret, "<redacted>")
        text = re.sub(r"sk-[A-Za-z0-9]{12,}", "sk-<redacted>", text)
        text = re.sub(r"\b[A-Za-z0-9]{48,}\b", "<redacted-token>", text)
        return text
    return value


def plot_summary(summary_rows: list[dict[str, Any]], basename: str) -> None:
    import matplotlib.pyplot as plt

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    methods = [row["method"] for row in summary_rows]
    metric_names = ["OF1", "RF1", "BF1", "TFC", "ETF"]
    inverse_names = ["VR"]
    x = list(range(len(methods)))
    width = 0.14
    fig, ax = plt.subplots(figsize=(11, 5.8))
    for idx, metric in enumerate(metric_names + inverse_names):
        offset = (idx - 2.5) * width
        values = [float(row[metric]) for row in summary_rows]
        ax.bar([item + offset for item in x], values, width=width, label=metric)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=15, ha="right")
    ax.legend(ncol=6, fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(ANALYSIS_DIR / f"{basename}_bar.png", dpi=220)
    fig.savefig(ANALYSIS_DIR / f"{basename}_bar.pdf")
    plt.close(fig)


def paper_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: row[key] for key in ["method", *PAPER_METRICS]} for row in summary_rows]


def plot_structure_reliability(summary_rows: list[dict[str, Any]], basename: str) -> None:
    import matplotlib.pyplot as plt

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    methods = [row["method"] for row in summary_rows]
    metrics = [
        ("RF1", "Relation F1"),
        ("BF1", "Binding F1"),
        ("RulePass", "Rule pass rate"),
        ("ETF", "Trace faithfulness"),
    ]
    colors = ["#2f6f9f", "#4f9d69", "#c77d2b", "#756bb1"]
    rows = []
    for row in summary_rows:
        next_row = dict(row)
        next_row["RulePass"] = 1 - float(row["VR"])
        rows.append(next_row)
    x = list(range(len(methods)))
    width = 0.18
    fig, ax = plt.subplots(figsize=(10.6, 4.8), dpi=220)
    for idx, (metric, label) in enumerate(metrics):
        values = [float(row[metric]) for row in rows]
        ax.bar([item + (idx - 1.5) * width for item in x], values, width=width, label=label, color=colors[idx])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=15, ha="right")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.12))
    fig.tight_layout()
    fig.savefig(ANALYSIS_DIR / f"{basename}_structure_reliability.png", bbox_inches="tight")
    fig.savefig(ANALYSIS_DIR / f"{basename}_structure_reliability.pdf", bbox_inches="tight")
    plt.close(fig)


def write_markdown_report(summary_rows: list[dict[str, Any]], config: LLMConfig, basename: str) -> None:
    lines = [
        "# 主实验结果",
        "",
        f"- 模型：`{config.model}`",
        "- 运行模式：v2 公平基线均使用同一 schema、对象本体、规则和资产知识；Ours 使用本地 `/sceneApi/semantic/build/plan` 执行工具化闭环。",
        "- 密钥处理：脚本只在内存中读取 API key，不写入结果文件。",
        "",
        "| 方法 | Object-F1 | Relation-F1 | Binding-F1 | VR↓ | TFC | ETF |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in paper_rows(summary_rows):
        lines.append(
            "| {method} | {OF1:.3f} | {RF1:.3f} | {BF1:.3f} | {VR:.3f} | {TFC:.3f} | {ETF:.3f} |".format(
                **{key: (float(value) if key in PAPER_METRICS else value) for key, value in row.items()}
            )
        )
    lines.extend(
        [
            "",
            f"图文件：`experiments/analysis/{basename}_structure_reliability.png` 和 `experiments/analysis/{basename}_structure_reliability.pdf`。",
        ]
    )
    (RESULTS_DIR / f"{basename}_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_blocked_report(failures: list[dict[str, Any]], config: LLMConfig, basename: str) -> None:
    lines = [
        f"# {basename} 阻塞记录",
        "",
        f"- 模型：`{config.model}`",
        "- 状态：至少一个方法调用失败，脚本未写入正式 `main_experiment_v2_*` 结果表。",
        "- 处理原则：不沿用 v1 结果冒充 v2 公平基线实验。",
        "",
        "| 任务 | 方法 | 错误 |",
        "| --- | --- | --- |",
    ]
    for item in failures:
        lines.append(f"| {item['task_id']} | {item['method']} | {item['error']} |")
    (RESULTS_DIR / f"{basename}_BLOCKED.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def remove_stale_outputs(basename: str) -> None:
    for name in [
        f"{basename}_outputs.jsonl",
        f"{basename}_raw.csv",
        f"{basename}_summary.csv",
        f"{basename}_paper_table.csv",
        f"{basename}_report.md",
        f"{basename}_error_analysis.csv",
        f"{basename}_error_analysis_summary.csv",
    ]:
        path = RESULTS_DIR / name
        if path.exists():
            path.unlink()


def remove_blocked_report(basename: str) -> None:
    path = RESULTS_DIR / f"{basename}_BLOCKED.md"
    if path.exists():
        path.unlink()


def run(args: argparse.Namespace) -> None:
    config_yaml = load_yaml_config()
    llm_config = load_llm_config()
    require_llm_config(llm_config)
    run_prefix = str(args.run_prefix or V2_RAW_BASENAME).strip() or V2_RAW_BASENAME
    progress_path = Path(args.progress) if args.progress else RESULTS_DIR / f"{run_prefix}_progress.jsonl"
    tasks = load_tasks(args.tasks)
    shared = load_json_file(args.shared_knowledge)
    schema = load_json_file(args.output_schema)
    if args.limit:
        tasks = tasks[: args.limit]
    if args.methods:
        methods = [method_for_cli(item.strip()) for item in args.methods.split(",") if item.strip()]
    else:
        methods = [method_for_cli(args.method)] if args.method else METHODS
    if any(method not in METHODS for method in methods):
        raise ValueError(f"unknown method in {methods}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    backend_process: subprocess.Popen[str] | None = None
    try:
        if any(is_ours_method(method) for method in methods):
            backend_process = ensure_backend(config_yaml, args.backend_start_timeout, args.backend_port)

        progress_cache = {} if args.no_cache else load_progress_cache(progress_path)
        normalized_rows: list[dict[str, Any]] = []
        raw_score_rows: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        total = len(tasks) * len(methods)
        index = 0
        for task in tasks:
            for method in methods:
                index += 1
                key = cache_key(str(task["task_id"]), method)
                if key in progress_cache:
                    normalized = progress_cache[key]
                    print(f"[{index}/{total}] cached {method} {task['task_id']}", flush=True)
                    normalized_rows.append(normalized)
                    raw_score_rows.append(score_record(task, normalized))
                    continue
                print(f"[{index}/{total}] {method} {task['task_id']}", flush=True)
                start = time.time()
                elapsed_ms = int((time.time() - start) * 1000)
                try:
                    if is_ours_method(method):
                        raw_output, backend_process = run_ours_with_retry(
                            task,
                            config_yaml,
                            llm_config.timeout_seconds,
                            backend_process,
                            args.backend_start_timeout,
                            args.backend_port,
                        )
                    else:
                        raw_output = call_llm_json(method, task, llm_config, shared, schema)
                    elapsed_ms = int((time.time() - start) * 1000)
                    normalized = normalize_output(method, task, raw_output, elapsed_ms)
                    if not args.no_cache:
                        progress_cache[key] = normalized
                        append_progress_record(progress_path, normalized)
                except Exception as error:
                    elapsed_ms = int((time.time() - start) * 1000)
                    print(f"  ! {method} {task['task_id']} failed: {type(error).__name__}: {error}", flush=True)
                    failures.append(
                        {
                            "task_id": task["task_id"],
                            "method": method,
                            "error": f"{type(error).__name__}: {error}",
                        }
                    )
                    normalized = failure_output(method, task, error, elapsed_ms)
                normalized_rows.append(normalized)
                raw_score_rows.append(score_record(task, normalized))

        if failures and not args.allow_partial:
            remove_stale_outputs(run_prefix)
            write_blocked_report(failures, llm_config, run_prefix)
            if not args.no_cache:
                compact_progress_cache(progress_path, progress_cache)
            raise RuntimeError(
                f"experiment blocked by {len(failures)} failed call(s); see experiments/results/{run_prefix}_BLOCKED.md"
            )

        if not args.no_cache:
            compact_progress_cache(progress_path, progress_cache)
        summary_rows = summarize(raw_score_rows)
        error_rows = summarize_errors(raw_score_rows)
        write_jsonl(RESULTS_DIR / f"{run_prefix}_outputs.jsonl", normalized_rows)
        write_csv(
            RESULTS_DIR / f"{run_prefix}_raw.csv",
            raw_score_rows,
            [
                "task_id",
                "task_category",
                "method",
                "run_id",
                "success",
                "required_objects",
                "generated_objects",
                "correct_objects",
                "required_relations",
                "generated_relations",
                "correct_relations",
                "required_bindings",
                "generated_bindings",
                "correct_bindings",
                "checked_rules",
                "violated_rules",
                "manual_corrections",
                "expected_trace_steps",
                "traceable_steps",
                "trace_field_components",
                "trace_executed_components",
                "trace_declared_steps",
                "trace_executed_steps",
                "trace_evidence_steps",
                "missing_objects",
                "extra_objects",
                "hierarchy_errors",
                "relation_direction_errors",
                "missing_relations",
                "missing_bindings",
                "binding_missing_fields",
                "asset_type_errors",
                "layout_boundary_errors",
                "pseudo_trace_steps",
                "trace_not_auditable",
                "memory_range_errors",
                "elapsed_ms",
                "notes",
            ],
        )
        write_csv(RESULTS_DIR / f"{run_prefix}_summary.csv", summary_rows, ["method", *METRICS])
        write_csv(RESULTS_DIR / f"{run_prefix}_paper_table.csv", paper_rows(summary_rows), ["method", *PAPER_METRICS])
        error_fields = [key for key in error_rows[0].keys()] if error_rows else ["method"]
        write_csv(RESULTS_DIR / f"{run_prefix}_error_analysis_summary.csv", error_rows, error_fields)
        write_csv(
            RESULTS_DIR / f"{run_prefix}_error_analysis.csv",
            raw_score_rows,
            [
                "task_id",
                "task_category",
                "method",
                "missing_objects",
                "extra_objects",
                "hierarchy_errors",
                "relation_direction_errors",
                "missing_relations",
                "missing_bindings",
                "binding_missing_fields",
                "asset_type_errors",
                "layout_boundary_errors",
                "pseudo_trace_steps",
                "trace_not_auditable",
                "memory_range_errors",
            ],
        )
        plot_summary(summary_rows, run_prefix)
        plot_structure_reliability(summary_rows, run_prefix)
        write_markdown_report(summary_rows, llm_config, run_prefix)
        remove_blocked_report(run_prefix)
    finally:
        terminate_backend(backend_process)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=TASKS_PATH)
    parser.add_argument("--shared-knowledge", type=Path, default=SHARED_KNOWLEDGE_PATH)
    parser.add_argument("--output-schema", type=Path, default=OUTPUT_SCHEMA_PATH)
    parser.add_argument("--run-prefix", default=V2_RAW_BASENAME, help="Prefix for generated result files.")
    parser.add_argument("--limit", type=int, default=0, help="Run only the first N tasks.")
    parser.add_argument("--method", choices=[*METHODS, *LEGACY_METHOD_ALIASES.keys()], help="Run only one method.")
    parser.add_argument("--methods", help="Run a comma-separated method subset, for example 'Direct-LLM + Schema,Ours KAFarmTwin'.")
    parser.add_argument("--backend-start-timeout", type=int, default=60)
    parser.add_argument(
        "--backend-port",
        default=os.getenv("EXPERIMENT_BACKEND_PORT"),
        help="Start/call the Ours backend on this port instead of application.yml; useful to isolate experiments from a running dev server.",
    )
    parser.add_argument("--allow-partial", action="store_true", help="Write v2 result files even if some calls fail.")
    parser.add_argument("--progress", type=Path, default=None, help="JSONL cache for successful task-method outputs. Defaults to <run-prefix>_progress.jsonl.")
    parser.add_argument("--no-cache", action="store_true", help="Disable progress cache and rerun every selected task-method.")
    return parser.parse_args()


if __name__ == "__main__":
    try:
        run(parse_args())
    except KeyboardInterrupt:
        sys.exit(130)
