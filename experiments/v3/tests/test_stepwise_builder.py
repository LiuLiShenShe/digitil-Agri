"""Tests for the shared stepwise scene builder (F-016).

Locks the F-018 fix: the stepwise builder splits scene authoring into
objects -> relations -> bindings, each a separate LLM call under the output cap.
Here the mock LLM returns ONLY its own per-step array (simulating capped, partial
single responses) and the builder must assemble the full scene across calls.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # repo root (has experiments/package)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
HARNESS = Path(__file__).resolve().parents[1] / "harness"
EVAL = Path(__file__).resolve().parents[1] / "evaluators"
for p in (HARNESS, EVAL, Path(__file__).resolve().parents[1]):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from stepwise_builder import stepwise_build_scene  # noqa: E402


class _FakeBudget:
    def __init__(self):
        self.calls = 0
        self.tokens = 0
    def assert_llm_budget(self):
        self.calls += 1
    def add_tokens(self, n):
        self.tokens += (n or 0)
    def summary(self):
        return {"llm_calls": self.calls, "tokens": self.tokens}


class _FakeRegistry:
    def __init__(self):
        self.calls = []
    def call(self, name, payload, agent_id=None, caller_method=None):
        self.calls.append((name, agent_id))
        return {"_call_id": f"{name}#{len(self.calls)}"}


def _stepwise_mock():
    """Mimic a capped model: each call returns ONLY its own array.

    Mirrors make_llm_call_fn's normalization: caller may pass a flat dict like
    {'system':..., 'user':...}; the mock reads the system prompt from it.
    """
    def _sysmsg(messages):
        if isinstance(messages, list):
            return messages[0]["content"] if messages else ""
        if isinstance(messages, dict):
            return messages.get("system") or ""
        return ""
    def call(messages, b=None):
        sysmsg = _sysmsg(messages)
        if "list ALL scene objects" in sysmsg:
            return {"content_json": {"objects": [
                {"id": "gh", "type": "Greenhouse", "role": "root", "key_attrs": {}, "count": 1},
                {"id": "row", "type": "CropRow", "role": "entity", "parent": "gh", "count": 1},
                {"id": "pl", "type": "Plant", "role": "entity", "parent": "row", "count": 4},
            ]}, "content": "", "finish_reason": "stop"}
        if "output relations" in sysmsg:
            return {"content_json": {"edges": [
                {"subject": "gh", "predicate": "contains", "object": "row"},
                {"subject": "row", "predicate": "contains", "object": "pl"},
            ]}, "content": "", "finish_reason": "stop"}
        if "output bindings" in sysmsg:
            return {"content_json": {"bindings": [
                {"subject": "pl", "target": "pl_asset", "type": "asset",
                 "metadata": {"asset_key": "tomato", "policy": "high_fidelity"}},
            ]}, "content": "", "finish_reason": "stop"}
        return {"content_json": {}, "content": "", "finish_reason": "stop"}
    return call


def test_stepwise_assembles_complex_scene():
    budget = _FakeBudget()
    reg = _FakeRegistry()
    out = stepwise_build_scene(
        prompt="build a greenhouse with 4 plants",
        ontology_hint="Types: Greenhouse CropRow Plant",
        llm_call_fn=_stepwise_mock(), budget=budget, registry=reg, agent_id="T")
    assert len(out["nodes"]) == 3, out["nodes"]
    assert any(n["type"] == "Greenhouse" for n in out["nodes"])
    assert len(out["edges"]) == 2, out["edges"]
    assert len(out["bindings"]) == 1, out["bindings"]


def test_stepwise_charges_each_step_and_calls_scene_plan():
    budget = _FakeBudget()
    reg = _FakeRegistry()
    stepwise_build_scene(
        prompt="x", ontology_hint="T", llm_call_fn=_stepwise_mock(),
        budget=budget, registry=reg, agent_id="T")
    # 3 LLM steps, each charged
    assert budget.calls >= 3, budget.calls
    # scene.plan called once objects exist (real tool evidence)
    assert "scene.plan" in [c[0] for c in reg.calls]
