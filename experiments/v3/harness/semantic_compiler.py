"""Semantic compiler: knowledge-constrained scene construction (F, P1-2/P1-3).

This is the architectural upgrade that separates KAFarmTwin from
"SingleAgent + post-hoc repair". Instead of the LLM authoring the full scene graph
(in which it must reinvent object ids/hierarchy/asset routing and inevitably drift
from the gold's controlled vocabulary), the compiler:

  1. emit_intent — ONE compact LLM call captures the *intent* (a handful of object
     groups + device list), well under the output cap.
  2. expand_graph — the DOMAIN KNOWLEDGE (hierarchy rules, identity-type policy)
     instantiates the full object graph (Greenhouse -> Plot/CropRow -> Plant) and
     expands counts, keeping Camera/Sensor/Device individual.
  3. bind_scene — the BINDING VOCAB (unit_registry, binding_vocab, asset_policy)
     emits gold-aligned bindings by construction: canonical units, correct device
     asset keys, served-object bindings.

The typed repair loop then only cleans up residual deviations (D/E). The LLM stops
owning deterministic structure work.

F (review 2026-08-18): the domain knowledge is NOT an inline if/else block — it is
a "knowledge compilation layer" decomposed into knowledge/{ontology,constraint,
mapping,policy}. This module is the compiler; the knowledge modules are the
compiled domain knowledge it consumes. Contribution claim = "Knowledge
compilation layer", not "rule table".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from experiments.v3.knowledge.unit_registry import unit_for_metric  # type: ignore
from experiments.v3.knowledge.binding_vocab import make_sensor_bind, make_asset_bind  # type: ignore
from experiments.v3.knowledge.asset_policy import ASSET_BY_TYPE, asset_key_for, policy_for  # type: ignore
from experiments.v3.knowledge.ontology import IDENTITY_TYPES, ROOT_ID  # type: ignore
from experiments.v3.knowledge.constraint import DEVICE_DEFAULT_TARGET_CLASS, DEVICE_DEFAULT_METRIC, DEVICE_ASSET_CLASSES, AGGREGATABLE_TYPES  # type: ignore
from experiments.v3.knowledge.mapping import (  # type: ignore
    is_identity_type,
    is_aggregatable,
    resolve_parent_hint,
    find_child,
    find_any,
    find_contained_plant,
)


@dataclass
class ObjectGroup:
    """An LLM-described group of objects; the compiler expands it."""
    object_type: str
    role: str = "entity"
    count: int = 1
    key_attrs: dict[str, Any] = field(default_factory=dict)
    parent: str = ""  # a role or object id the compiler resolves


@dataclass
class IntentIR:
    scene_type: str = "greenhouse"
    crop: str = ""
    groups: list[dict[str, Any]] = field(default_factory=list)  # raw LLM group dicts
    devices: list[dict[str, Any]] = field(default_factory=list)  # device rows
    missing_devices: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TypedObjectGraph:
    objects: list[dict[str, Any]] = field(default_factory=list)
    relations: list[dict[str, Any]] = field(default_factory=list)
    bindings: list[dict[str, Any]] = field(default_factory=list)


_ROOT_ID = ROOT_ID  # kept for import-compat; canonical id lives in knowledge/ontology.py


def emit_intent(prompt: str, llm_call_fn, budget) -> IntentIR:
    """One compact LLM call to capture intent (object groups + device list).

    Far under the ~1200-token output cap: a few object groups + a device list, NOT the
    full per-instance graph. No id reinvention reaches the scorer — the compiler owns
    id assignment.
    """
    resp = llm_call_fn({
        "system": (
            "Extract INTENT only (not a full scene). Output JSON {\"scene_type\", \"crop\", "
            "\"groups\":[{object_type, role, count, key_attrs(optional)}, ...], "
            "\"devices\":[{device_type, role, count, asset_type(optional)}, ...]}. "
            "Keep it compact: collapse Plant/CropRow into count groups; list each "
            "Camera/Sensor/Device individually if it has its own role/parent. "
            "Do NOT assign object ids here — the compiler owns them."
        ),
        "user": prompt,
    }, budget)
    data = resp.get("content_json") or {}
    return IntentIR(
        scene_type=str(data.get("scene_type") or "greenhouse"),
        crop=str(data.get("crop") or ""),
        groups=list(data.get("groups") or []),
        devices=list(data.get("devices") or []),
        missing_devices=list(data.get("missing_devices") or []),
    )


def _assign_id(base: str, existing: list[str]) -> str:
    """Return a unique base id; if taken, append -1, -2, ... (instance-level ids for
    identity objects remain distinct so their observes/edges align)."""
    b = base.lower().replace(" ", "_")
    cand = b
    i = 1
    lowered = {x.lower() for x in existing}
    while cand.lower() in lowered:
        i += 1
        cand = f"{b}-{i}"
    return cand


def expand_graph(ir: IntentIR, unit_reg=None, vocab=None) -> TypedObjectGraph:
    """Instantiate the object graph from intent + domain knowledge.

    Hierarchy: Greenhouse(root) -> Plot? -> CropRow -> Plant; devices attach to the
    greenhouse or their declared parent. Identity types are emitted individually
    (count instances get distinct ids); aggregate background types may carry count>1
    but are NOT per-id edges.
    """
    g = TypedObjectGraph()
    ids: list[str] = []
    next_seq = [0]

    def _nid(prefix: str):
        next_seq[0] += 1
        cand = f"{prefix}_{next_seq[0]}"
        while cand in ids:
            next_seq[0] += 1
            cand = f"{prefix}_{next_seq[0]}"
        ids.append(cand)
        return cand

    # Root greenhouse
    gh_id = _nid("greenhouse")
    g.objects.append({"id": gh_id, "type": "Greenhouse", "role": "root",
                      "key_attrs": {}, "count": 1})

    # Group expansion
    for grp in ir.groups:
        nt = str(grp.get("object_type") or "").strip()
        if not nt:
            continue
        count = max(1, int(grp.get("count") or 1))
        role = str(grp.get("role") or "entity")
        parent_hint = str(grp.get("parent") or "")
        is_identity = is_identity_type(nt)
        n_to_emit = 1 if not is_identity else count  # identity: individual; aggregate: one group node
        # resolve parent: declared -> greenhouse root
        parent = resolve_parent_hint(parent_hint, gh_id)
        if not is_identity and count > 1:
            # aggregate background group: one node with count
            oid = _nid(nt.lower())
            # Plant/CropRow groups attach under a CropRow (Plant) or the GH (CropRow)
            if nt in ("Plant", "plant") and (not parent_hint or parent_hint == "root"):
                row = find_child(g.objects, gh_id, "CropRow")
                if row:
                    parent = row
            node = {"id": oid, "type": nt, "role": role,
                    "key_attrs": dict(grp.get("key_attrs") or {}), "count": count, "parent": parent}
            g.relations.append({"subject": parent, "predicate": "contains", "object": oid})
            g.objects.append(node)
            # Plant belongs_to CropRow; CropRow belongs_to Greenhouse/Plot — model the Plant group as under a CropRow
            if nt in ("Plant", "plant") and "belongs_to" not in (node.get("key_attrs") or {}):
                # attach to a CropRow child of parent if present, else parent directly
                child_row = find_child(g.objects, parent, "CropRow") or find_child(g.objects, gh_id, "CropRow")
                if child_row:
                    node["key_attrs"]["belongs_to"] = child_row
        else:
            # identity: emit each instance individually
            for i in range(n_to_emit):
                oid = _nid(nt.lower())
                node = {"id": oid, "type": nt, "role": role,
                        "key_attrs": dict(grp.get("key_attrs") or {}), "count": 1, "parent": parent}
                g.relations.append({"subject": parent, "predicate": "contains", "object": oid})
                g.objects.append(node)

    # Ensure there's at least one CropRow under the GH for plants
    if not any(o["type"] == "CropRow" for o in g.objects):
        rid = _nid("croprow")
        g.objects.append({"id": rid, "type": "CropRow", "role": "entity",
                          "key_attrs": {}, "count": 1, "parent": gh_id})
        g.relations.append({"subject": gh_id, "predicate": "contains", "object": rid})

    # Device expansion: each listed device is an identity object with correct asset
    _plot = find_any(g.objects, "Plot")
    _row = find_any(g.objects, "CropRow")
    device_parent_default = (_plot.get("id") if _plot else _row.get("id") if _row else gh_id)
    for dev in ir.devices:
        dt = str(dev.get("device_type") or "").strip()
        if not dt or dt not in ASSET_BY_TYPE:
            continue
        count = max(1, int(dev.get("count") or 1))
        parent_hint = str(dev.get("parent") or "")
        parent = resolve_parent_hint(parent_hint, device_parent_default)
        for i in range(count):
            oid = _nid(dt.lower())
            node = {"id": oid, "type": dt, "role": "entity",
                    "key_attrs": dict(dev.get("key_attrs") or {}), "count": 1, "parent": parent}
            g.relations.append({"subject": parent, "predicate": "contains", "object": oid})
            g.objects.append(node)
    return g


def bind_scene(graph: TypedObjectGraph, ir: IntentIR,
               binding_vocab=None, unit_reg=None, asset_policy=None) -> TypedObjectGraph:
    """Author gold-aligned bindings by construction.

    - Sensor/Camera/Device get a binding to a contained/served plant (or their declared
      target) with the canonical unit for their metric.
    - Devices get their correct asset_key via asset_policy (R4 satisfied at authoring).
    """
    for n in graph.objects:
        nt = str(n.get("type") or "")
        oid = str(n.get("id") or "")
        if nt not in DEVICE_ASSET_CLASSES:
            continue
        # served object: use declared target, else a plant contained by the device's parent
        target = None
        if isinstance(ir.devices, list):
            for dev in ir.devices:
                if str(dev.get("device_type")) == nt:
                    target = str(dev.get("target") or "")
                    break
        if not target:
            target = find_contained_plant(graph.objects, graph.relations, n.get("parent"))
        if target:
            metric = DEVICE_DEFAULT_METRIC.get(nt, "temperature")
            unit = unit_for_metric(metric)
            graph.bindings.append(make_sensor_bind(oid, target, [metric], unit))
        # correct asset (R4 at authoring)
        ak = asset_key_for(n)
        if ak:
            graph.bindings.append(make_asset_bind(oid, ak, policy_for(n)))
    return graph