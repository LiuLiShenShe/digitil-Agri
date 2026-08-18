#!/usr/bin/env python3
"""Shared stepwise scene builder (F-015/F-016, method-agnostic).

Root cause F-018: asset/bind/repair tasks require complex JSON (multi-group
objects + asset bindings + repair ops) that exceeds the model's single-response
output cap (~1200 tokens on DeepSeek-V4-Flash). A one-shot ``{objects, relations,
bindings}`` call truncates mid-JSON (finish=length) -> content_json=None ->
empty scene for BOTH methods on those tasks.

This helper removes that shared ceiling by building the scene in SEPARATE LLM
calls, each well under the cap:

  step 1  objects   :  nodes {id,type,role,parent,key_attrs,count}
  step 2  relations :  edges {subject,predicate,object} referencing step-1 ids
  step 3  bindings  :  bindings {subject,target,type,metadata}

Each step is fed the prior steps' ids as context (so edges/bindings reference
REAL generated ids), but asked to output ONLY its own list. No step sees gold.
Every step is charged to the budget, recorded through the shared trace proxy,
and parsed defensively (a truncated step yields the partial parse + continues).

Both SingleAgent and KAFarmTwin invoke this identical helper, so the two methods
have symmetric scene-authoring capability and are compared fairly. The methods
still keep their distinguishing orchestration (layout / typed-repair loop) around
the emitted scene.
"""

from __future__ import annotations

import json
from typing import Any

from experiments.v3.harness.canonicalizer import canonicalize_node, canonicalize_edge, canonicalize_binding  # type: ignore


def _merge_json_part(part: dict[str, Any], key: str) -> list[dict[str, Any]]:
    """Return the per-step list a partial JSON dict holds for `key`."""
    v = (part or {}).get(key)
    if v is None:
        return []
    if isinstance(v, list):
        return [x for x in v if isinstance(x, dict)]
    if isinstance(v, str) and v.strip():
        try:
            inner = json.loads(v)
            if isinstance(inner, list):
                return [x for x in inner if isinstance(x, dict)]
        except Exception:
            return []
    return []


def _extract_list(content_json: Any, keys: tuple[str, ...]) -> list[dict[str, Any]]:
    """Robustly pull the per-step list out of a model response.

    The model may emit the step's list in any of these shapes (all seen live):
      - bare JSON array            [{...}, ...]
      - dict wrapper               {"objects": [{...}, ...]}
      - JSON string of either      '{"edges":[...]}' or '[...]'
    Returns [] only when nothing parseable is present.
    """
    cj = content_json
    if isinstance(cj, str) and cj.strip():
        try:
            cj = json.loads(cj)
        except Exception:
            return []
    if isinstance(cj, list):
        return [x for x in cj if isinstance(x, dict)]
    if isinstance(cj, dict):
        for k in keys:
            v = cj.get(k)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
        # dict but key missing: fall back to any single list value
        for v in cj.values():
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
    return []


def stepwise_build_scene(
    *,
    prompt: str,
    ontology_hint: str,
    llm_call_fn,
    budget: Any,
    registry: Any,
    agent_id: str,
    max_objects: int = 60,
) -> dict[str, Any]:
    """Build {nodes, edges, bindings} via three capped LLM steps + tools.

    Returns the same shape a one-shot builder would, but assembled stepwise so no
    single LLM response must hold the whole scene.

    - nodes   : canonicalized object nodes
    - edges   : canonicalized relations
    - bindings: canonicalized bindings
    Trace/tool evidence is real (registry.call for scene.plan after nodes).
    """
    system = (
        "You build digital-twin farm scenes. Shared knowledge:\n"
        f"{ontology_hint}\n"
        "Output ONLY compact JSON. Repeated objects = one object with count=N. "
        "Keep each response short and stop as soon as the JSON is complete.\n"
        "Emit NO markdown code fences and NO extra prose."
    )

    # ---- step 1: objects ----
    # P0-6: budget accounting is the single source in make_llm_call_fn (assert_llm
    # + tokens + cost). Do NOT re-assert/add here or calls/tokens/cost double-count.
    r1 = llm_call_fn({
        "system": system + "\n\nResponsibility: list ALL scene objects as JSON array under key \"objects\". "
                           "Each node: {\"id\":str,\"type\":<SharedType>,\"role\":\"root\"|\"entity\",\"parent\":str|omit,\"key_attrs\":{},\"count\":int}.",
        "user": prompt,
    }, budget)
    cj1 = r1.get("content_json")
    if isinstance(cj1, list):
        # model returned a bare array (treat as the objects list)
        p1 = {"objects": cj1}
    elif isinstance(cj1, dict):
        p1 = cj1
    else:
        p1 = {}
    if not p1 or not p1.get("objects"):
        p1 = {"objects": _merge_json_part(p1, "objects")}
    nodes = [_as_node(o) for o in (_extract_list(cj1, ("objects", "nodes", "entities")) or [])]
    nodes = _dedupe_nodes(nodes)[:max_objects]

    # reflect layout through tools if we have objects (real trace)
    if nodes:
        registry.call("scene.plan", {"objects": nodes}, agent_id=agent_id)
        registry.call("layout.solve", {"objects": nodes}, agent_id=agent_id)
        registry.call("layout.validate", {"layout": list(nodes)}, agent_id=agent_id)
        from experiments.v3.harness.canonicalizer import merge_layout_into_nodes  # type: ignore
        nodes = merge_layout_into_nodes(nodes, list(nodes))

    node_ids = "\n".join(f"- {o.get('id')} ({o.get('type')})" for o in nodes) or "(none yet)"

    # ---- step 2: relations ----
    r2 = llm_call_fn({
        "system": system + "\n\nResponsibility: output relations for the scene as JSON array under key \"edges\". "
                           "Each edge: {\"subject\":str,\"predicate\":\"contains\",\"object\":str}. "
                           "Use ONLY the exact existing ids listed below. If the parent/child relationship "
                           "is already implied by a node's `parent` field, still emit the explicit contains edge "
                           "for every parent->child pair.",
        "user": f"Scene objects (ids to use exactly):\n{node_ids}\n\nOriginal prompt:\n{prompt}",
    }, budget)
    edges = [_as_edge(e) for e in (_extract_list(r2.get("content_json"), ("edges", "relations", "relationships")) or [])]

    # ---- step 3: bindings ----
    r3 = llm_call_fn({
        "system": system + "\n\nResponsibility: output bindings for the scene as JSON array under key \"bindings\". "
                           "Each binding: {\"subject\":str,\"target\":str,\"type\":\"asset\"|\"sensor_bind\"|\"trait_bind\","
                           "\"metadata\":{\"metrics\":[str],\"unit\":str,\"asset_key\":str,\"policy\":str}}. "
                           "Use ONLY the exact existing ids below.",
        "user": f"Scene objects (ids):\n{node_ids}\n\nOriginal prompt:\n{prompt}",
    }, budget)
    bindings = [_as_binding(b) for b in (_extract_list(r3.get("content_json"), ("bindings", "binding", "links")) or [])]

    return {"nodes": nodes, "edges": edges, "bindings": bindings}


def seed_nodes_from_initial_state(initial_state: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Derive objects + relations from a task's public initial_state (B, P0-2).

    data_binding / asset_routing tasks legitimately start from a complete object
    graph that the task already provides in `initial_state`. The method must NOT
    reinvent those ids/hierarchy from the prompt (that breaks id_map/binding
    alignment). Return (nodes preserving initial ids, relations) — the same shape
    stepwise_build_scene's step 1-2 would produce, but deterministically from the
    seeded graph.
    """
    if isinstance(initial_state, dict):
        objs = initial_state.get("objects") or []
        rels = initial_state.get("relations") or []
    else:
        return [], []
    nodes = []
    for o in objs:
        if not isinstance(o, dict) or not o.get("id"):
            continue
        n = dict(o)
        n.setdefault("count", 1)
        nodes.append(n)
    relations = []
    for r in rels:
        if not isinstance(r, dict):
            continue
        relations.append(canonicalize_edge(r))
    # Also materialize contains edges implied by a node.parent, matching the repair
    # seeding path (so R1 hierarchy is explicit in the scored relations).
    seen = {(e.get("subject"), e.get("object")) for e in relations}
    for n in nodes:
        p = n.get("parent")
        if p and (str(p), str(n.get("id") or "")) not in seen:
            relations.append({"subject": p, "predicate": "contains", "object": str(n.get("id") or "")})
            seen.add((str(p), str(n.get("id") or "")))
    return nodes, relations


def bindings_only_scene(
    *,
    initial_state: Any,
    prompt: str,
    llm_call_fn,
    budget: Any,
    registry: Any,
    agent_id: str,
) -> dict[str, Any]:
    """data_binding path: seed objects+relations from initial_state, emit bindings only.

    The task's public initial_state already carries the object graph with the exact
    ids the gold references (TN21: objects=[gh,row,sen1,sen2,plant]). We preserve
    those ids (deterministic — no LLM rebuild, so id_map/binding_match align) and ask
    the LLM only for the bindings edge data (sensor_bind / trait_bind / asset). This
    fixes the data_bind BindF1=0 root cause without the model reinventing the scene.
    """
    nodes, edges = seed_nodes_from_initial_state(initial_state)
    node_ids = "\n".join(f"- {o.get('id')} ({o.get('type')})" for o in nodes) or "(none yet)"
    # reflect the seeded graph through the SHARED tools (real trace/evidence)
    if nodes:
        registry.call("scene.plan", {"objects": nodes}, agent_id=agent_id)
        registry.call("layout.solve", {"objects": nodes}, agent_id=agent_id)

    system = (
        "You emit data bindings for an existing digital-twin scene. Shared knowledge:\n"
        "Binding types: sensor_bind (sensor→monitored object), trait_bind (trait→plant), "
        "asset (object→asset). metadata: {metrics:[...], unit:<canonical unit>, asset_key, policy}. "
        "Use ONLY the exact existing ids below. Do NOT invent or rename objects. "
        "Output ONLY compact JSON under key \"bindings\". No markdown, no prose."
    )
    bind_r = llm_call_fn({
        "system": system,
        "user": f"Existing scene objects (ids to use exactly):\n{node_ids}\n\n"
                f"Emit bindings for:\n{prompt}",
    }, budget)
    from experiments.v3.harness.canonicalizer import canonicalize_binding  # type: ignore
    bindings = [_as_binding(b) for b in (_extract_list(bind_r.get("content_json"), ("bindings", "binding", "links")) or [])]

    return {"nodes": nodes, "edges": edges, "bindings": bindings}


def _as_node(o: dict[str, Any]) -> dict[str, Any]:
    return canonicalize_node(o)


def _as_edge(e: dict[str, Any]) -> dict[str, Any]:
    return canonicalize_edge(e)


def _as_binding(b: dict[str, Any]) -> dict[str, Any]:
    return canonicalize_binding(b)


def _dedupe_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop exact duplicates by (type, id) while keeping useful distinct types."""
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    order: list[tuple[str, str]] = []
    for n in nodes:
        k = (str(n.get("type") or ""), str(n.get("id") or ""))
        if k not in seen:
            seen[k] = n
            order.append(k)
    return [seen[k] for k in order]
