"""LLM client for the v3 experiment harness.

Reads the endpoint/model/key from environment (AGNES_BASE_URL / AGNES_API_KEY /
AGNES_MODEL), never prints the key. Compatible with the SiliconFlow OpenAI-compatible
/chat/completions API used by the experiment (deepseek-ai/DeepSeek-V4-Flash).

The model returns `content` + `reasoning_content`; we parse finish_reason and tool_calls
robustly (the reasoning model may emit reasoning_content alongside content).
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

import requests


class LLMError(Exception):
    pass


def _load_env() -> tuple[str, str, str]:
    base_url = os.getenv("AGNES_BASE_URL") or os.getenv("LLM_BASE_URL") or "https://api.siliconflow.cn/v1"
    api_key = os.getenv("AGNES_API_KEY") or os.getenv("LLM_API_KEY") or ""
    model = os.getenv("AGNES_MODEL") or os.getenv("LLM_MODEL") or "deepseek-ai/DeepSeek-V4-Flash"
    return base_url.rstrip("/"), api_key, model


def chat_completions_url(base_url: str) -> str:
    if base_url.endswith("/chat/completions"):
        return base_url
    if base_url.endswith("/v1"):
        return base_url + "/chat/completions"
    return base_url + "/v1/chat/completions"


def _extract_json_object(text: str) -> Any | None:
    """Extract the first balanced JSON object/array embedded in prose."""
    start = text.find("{")
    if start == -1 and "[" in text:
        return _extract_json_array(text)
    if start == -1:
        return None
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except Exception:
                    return None
    return None


def _extract_json_array(text: str) -> Any | None:
    start = text.find("[")
    if start == -1:
        return None
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except Exception:
                    return None
    return None


class LLMClient:
    def __init__(self) -> None:
        self.base_url, self.api_key, self.model = _load_env()
        self.url = chat_completions_url(self.base_url)

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def call(self, messages: list[dict[str, Any]], *, max_tokens: int = 1200,
             temperature: float = 0.2, retries: int = 2, timeout: int = 180) -> dict[str, Any]:
        """Call /chat/completions, return {content_json?, content, finish_reason, usage}.

        Raises LLMError on final failure. Parses JSON from content if present.
        """
        if not self.api_key:
            raise LLMError("AGNES_API_KEY not set")
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            # Disable the reasoning chain on SiliconFlow DeepSeek-V4-Flash. Without
            # this the model emits thousands of reasoning tokens per call (3+ min
            # latency); with it, identical output at ~1-2s. Same model, same
            # temperature — only chain-of-thought is suppressed, keeping the
            # experiment runnable at the required scale. SiliconFlow honors the
            # top-level enable_thinking (a nested chat_template_kwargs is NOT
            # honored on this gateway — verified by the 40s+ timeout above).
            "enable_thinking": False,
        }
        last_err: Exception | None = None
        for attempt in range(retries + 1):
            try:
                resp = requests.post(self.url, headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }, json=payload, timeout=timeout)
                if resp.status_code != 200:
                    last_err = LLMError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                    continue
                data = resp.json()
                choice = (data.get("choices") or [{}])[0]
                message = choice.get("message") or {}
                content = message.get("content") or ""
                finish_reason = choice.get("finish_reason") or ""
                usage = data.get("usage") or {}
                # parse JSON from content if it looks like JSON (strip markdown fences)
                content_json = None
                text = content.strip()
                if text.startswith("```"):
                    text = text.strip("`")
                    if text.startswith("json"):
                        text = text[4:].strip()
                try:
                    content_json = json.loads(text)
                except Exception:
                    content_json = _extract_json_object(text)
                return {
                    "content": content,
                    "content_json": content_json,
                    "finish_reason": finish_reason,
                    "usage": usage,
                    "model": data.get("model", self.model),
                }
            except requests.RequestException as e:
                last_err = e
                time.sleep(2 ** attempt)
        raise LLMError(f"LLM call failed after retries: {last_err}")


ONTOLOGY_NOTE = (
    "【共享场景知识 / Shared knowledge】\n"
    "可用对象类型（必须严格使用下列精确类型名，不要发明新类型）: "
    "Greenhouse, Plot, CropRow, Plant, Sensor, Camera, Device, Trait, Event, Asset, "
    "WeatherStation, Irrigation, Pump, ReportSource\n"
    "可用关系谓词: contains（父场景包含子对象）\n"
    "可用绑定类型: asset（对象挂接资产）, sensor_bind（传感器监测目标）, "
    "trait_bind（对象关联特征属性）\n"
    "节点字段格式: {\"id\": str, \"type\": <上述类型>, \"role\": \"root\"|\"entity\", "
    "\"parent\": str(可选), \"key_attrs\": {可选}, \"count\": int}\n"
    "关系字段格式: {\"subject\": str, \"predicate\": \"contains\", \"object\": str}\n"
    "绑定字段格式: {\"subject\": str, \"target\": str, \"type\": <上述绑定类型>, "
    "\"metadata\": {\"metrics\": [str], \"unit\": str}}\n"
    "关键字段规范（缺失会导致违规）：\n"
    "  Sensor/传感器节点需有 monitoring_target 字段指向其监测的对象id；绑定类型用 "
    "sensor_bind，metadata 需含 metrics 与 unit（如 \"unit\": \"celsius\"）\n"
    "  Camera 节点需有 observes（指向观察对象）、pose（含 position）、fov 字段\n"
    "  Plant 节点需有 belongs_to（指向所属 CropRow 或 Plot）\n"
    "  Irrigations/Pump 资产类节点需有 asset_key（指向正确资产类型）\n"
    "约束：\n"
    "  只有 role=\"root\" 的对象可以无父级；Greenhouse 可包含 Plot/CropRow/Plant/Sensor/"
    "Camera/WeatherStation/Irrigation/Pump/Device\n"
    "  每个 Sensor/Trait/Event 必须被绑定且 metadata 含 unit 或 timestamp\n"
    "  所有对象必须有 key_attrs.location（排除 Greenhouse/Plot）否则视为空间越界\n"
    "必须原样输出上述受控词汇与字段，不要改写为同义词或自由命名。"
)


def make_llm_call_fn(client: LLMClient):
    """Return a callable (messages, budget) -> response that respects LLM budget.

    `messages` may be a list of {role, content} OR a flat dict like
    {"system": "...", "user": "..."} (normalized here) OR a single {role, content}.

    The shared ONTOLOGY_NOTE (controlled vocabulary used to author the frozen gold)
    is injected into the system message of EVERY call, identically for all methods,
    so all methods see the same domain knowledge the gold was typed from.
    """

    def _normalize_messages(messages) -> list[dict[str, Any]]:
        if isinstance(messages, list):
            # each item must be {role, content}
            out = []
            for m in messages:
                if "role" in m:
                    out.append({"role": m["role"], "content": m.get("content", "")})
                elif "system" in m or "user" in m:
                    out.extend(_normalize_messages(m))
                else:
                    out.append({"role": "user", "content": str(m)})
            return out
        if isinstance(messages, dict):
            if "role" in messages:
                return [{"role": messages["role"], "content": messages.get("content", "")}]
            out = []
            for role in ("system", "user", "assistant"):
                if messages.get(role):
                    out.append({"role": role, "content": messages[role]})
            return out
        return [{"role": "user", "content": str(messages)}]

    def call_fn(messages, budget=None) -> dict[str, Any]:
        if budget is not None:
            budget.assert_llm_budget()
        normalized = _normalize_messages(messages)
        # inject shared ontology knowledge into the system message (uniform across methods)
        sys_idx = next((i for i, m in enumerate(normalized) if m["role"] == "system"), None)
        if sys_idx is not None:
            if ONTOLOGY_NOTE not in normalized[sys_idx]["content"]:
                normalized[sys_idx]["content"] = ONTOLOGY_NOTE + "\n\n" + normalized[sys_idx]["content"]
        else:
            normalized.insert(0, {"role": "system", "content": ONTOLOGY_NOTE})
        resp = client.call(normalized)
        if budget is not None:
            budget.add_tokens(resp.get("usage", {}).get("total_tokens", 0))
        return resp
    return call_fn
