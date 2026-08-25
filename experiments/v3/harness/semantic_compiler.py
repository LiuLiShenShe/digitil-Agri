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
    id assignment. For asset_routing tasks the groups carry an explicit asset_policy
    (high_fidelity / lightweight) and role (focus / background), plus any missing-device
    placeholders the user requested.
    """
    resp = llm_call_fn({
        "system": (
            "Extract INTENT only (not a full scene). Output JSON {\"scene_type\", \"crop\", "
            "\"groups\":[{object_type, role, count, asset_policy(optional), key_attrs(optional)}, ...], "
            "\"devices\":[{device_type, role, count, asset_type(optional)}, ...], "
            "\"missing_devices\":[{device_type, fallback}]}. "
            "asset_policy: 'high_fidelity' for focus plants needing strong assets, "
            "'lightweight' for background group; 'placeholder' fallback marks an object "
            "the user explicitly notes is absent and must be recorded as a pending asset job. "
            "Collapse Plant/CropRow into count groups; list each Camera/Sensor/Device individually. "
            "Do NOT assign object ids — the compiler owns them."
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

    def _policy_for_group(grp: dict[str, Any]) -> str:
        pol = str((grp.get("key_attrs") or {}).get("asset_policy") or grp.get("asset_policy") or "")
        return pol or "TRELLIS.2"

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
        asset_policy = _policy_for_group(grp)
        parent_hint = str(grp.get("parent") or "")
        is_identity = is_identity_type(nt)
        n_to_emit = 1 if not is_identity else count  # identity: individual; aggregate: one group node
        # resolve parent: declared -> greenhouse root
        parent = resolve_parent_hint(parent_hint, gh_id)
        # Plants attach under a CropRow child of the greenhouse (per hierarchy GH->CropRow->Plant).
        if nt in ("Plant", "plant") and (parent_hint in ("", "root") or parent == gh_id):
            row = find_child(g.objects, gh_id, "CropRow")
            if not row:
                rid = _nid("croprow")
                g.objects.append({"id": rid, "type": "CropRow", "role": "entity",
                                  "key_attrs": {}, "count": 1, "parent": gh_id})
                g.relations.append({"subject": gh_id, "predicate": "contains", "object": rid})
                row = rid
            parent = row
        if not is_identity and count > 1:
            # aggregate background group: one node with count
            oid = _nid(nt.lower())
            node = {"id": oid, "type": nt, "role": role, "asset_policy": asset_policy,
                    "key_attrs": dict(grp.get("key_attrs") or {}), "count": count, "parent": parent}
            g.relations.append({"subject": parent, "predicate": "contains", "object": oid})
            g.objects.append(node)
            # Plant belongs_to CropRow (already set as parent above)
            if nt in ("Plant", "plant"):
                node["key_attrs"]["belongs_to"] = parent
        else:
            # identity: emit each instance individually
            for i in range(n_to_emit):
                oid = _nid(nt.lower())
                node = {"id": oid, "type": nt, "role": role, "asset_policy": asset_policy,
                        "key_attrs": dict(grp.get("key_attrs") or {}), "count": 1, "parent": parent}
                g.relations.append({"subject": parent, "predicate": "contains", "object": oid})
                g.objects.append(node)

    # Ensure there's at least one CropRow under the GH for plants (in case no Plant group
    # declared but CropRow is still expected by the hierarchy).
    if not any(o["type"] == "CropRow" for o in g.objects):
        rid = _nid("croprow")
        g.objects.append({"id": rid, "type": "CropRow", "role": "entity",
                          "key_attrs": {}, "count": 1, "parent": gh_id})
        g.relations.append({"subject": gh_id, "predicate": "contains", "object": rid})

    # Device expansion: each listed device is an identity object with correct asset
    _plot = find_any(g.objects, "Plot")
    _row = find_any(g.objects, "CropRow")
    device_parent_default = (_plot.get("id") if _plot else _row.get("id") if _row else gh_id)
    declared_types = {str(d.get("device_type") or "").strip().lower() for d in ir.devices}
    missing_types = {str(d.get("device_type") or "").strip().lower() for d in ir.missing_devices}
    for dev in ir.devices:
        dt = str(dev.get("device_type") or "").strip()
        if not dt or (dt not in ASSET_BY_TYPE and dt.lower() not in declared_types):
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
    # Missing devices (user noted absent) still get a Device/placeholder node so the
    # scene honestly represents the pending asset job, with a placeholder binding later.
    # Default parent is the greenhouse root (devices mount at greenhouse level unless declared).
    for md in ir.missing_devices:
        dt = str(md.get("device_type") or "").strip()
        if not dt or dt.lower() in declared_types:
            continue
        parent_hint = str(md.get("parent") or "")
        parent = resolve_parent_hint(parent_hint, gh_id)
        oid = _nid(dt.lower())
        # Normalize to a generic Device node when the subtype is not a known asset
        # class — the placeholder job is represented as Device, not a hallucinated asset.
        node_type = dt if dt in ASSET_BY_TYPE else "Device"
        # A missing-device placeholder honestly records WHICH device the user noted
        # absent (device_type) and that it is not yet resolved (asset_state: placeholder).
        # General placeholder semantics, derived from the user's missing-device note —
        # not task/gold specific.
        ka = dict(md.get("key_attrs") or {})
        ka.setdefault("device_type", dt)
        ka.setdefault("asset_state", "placeholder")
        node = {"id": oid, "type": node_type, "role": "entity",
                "key_attrs": ka, "count": 1, "parent": parent}
        g.relations.append({"subject": parent, "predicate": "contains", "object": oid})
        g.objects.append(node)
    return g


def compile_asset_routes(graph: TypedObjectGraph, catalog: dict[str, Any] | None = None,
                         ir: IntentIR | None = None) -> list[dict[str, Any]]:
    """Compile asset routing for Plant + device objects (Task 5 / AssetCompiler).

    Drives routing by GENERAL policy (role / asset_policy / device type / availability),
    NOT by task_id or gold ids.

    Case A focus plant  -> high_fidelity asset policy
    Case B background    -> lightweight asset policy
    Case C device type   -> asset family from ASSET_BY_TYPE
    Case D missing device -> placeholder / unresolved asset_job
    """
    from experiments.v3.knowledge.binding_vocab import make_asset_bind, make_asset_job_placeholder  # type: ignore
    asset_routes: list[dict[str, Any]] = []
    catalog = catalog or {}
    ir_devices = (ir.devices if ir else []) or []
    ir_missing = (ir.missing_devices if ir else []) or []

    missing_types = {str(d.get("device_type")).strip().lower() for d in ir_missing}
    declared_device_types = {str(d.get("device_type")).strip().lower() for d in ir_devices}

    # Device asset keys (Case C + Case D).
    for n in graph.objects:
        nt = str(n.get("type") or "").strip()
        oid = str(n.get("id") or "")
        oid_prefix = oid.lower()
        known_device = nt in ASSET_BY_TYPE
        declared_device = nt.lower() in declared_device_types \
            or any(oid_prefix.startswith(t + "_") or oid_prefix == t for t in declared_device_types)
        # A Device node whose id prefix matches a declared missing type is that
        # placeholder slot (expand_graph emits the missing-device node with the
        # subtype as its id prefix: light_5 for a missing Light).
        is_missing_slot = any(oid_prefix.startswith(t + "_") or oid_prefix == t for t in missing_types)
        if not known_device and not declared_device and not is_missing_slot and nt.lower() not in missing_types:
            continue
        # Case D: user explicitly noted this device type is absent → placeholder asset job.
        if nt.lower() in missing_types or is_missing_slot:
            asset_routes.append(make_asset_job_placeholder(oid))
            continue
        ak = asset_key_for(n) if known_device else nt.lower()
        if ak:
            asset_routes.append(make_asset_bind(oid, ak, policy_for(n)))

    # Plant asset routing (Case A / B) — driven by role + crop semantics.
    # The asset_key is derived from (crop, role): focus plants use a focus asset,
    # background plants use a lightweight/background asset. This is a GENERAL rule
    # (role/crop driven), NOT a task-id or gold-id dependency — it works for any crop.
    crop = (ir.crop or "").strip().lower() if ir else ""
    if not crop:
        crop = "crop"
    for n in graph.objects:
        nt = str(n.get("type") or "").strip()
        if nt not in ("Plant", "plant"):
            continue
        oid = str(n.get("id") or "")
        role = str(n.get("role") or "entity")
        policy = str(n.get("asset_policy") or policy_for(n))
        # Infer focus vs background from asset_policy when the LLM did not emit an
        # explicit role. high_fidelity => focus, lightweight => background. This is
        # a general, crop-agnostic policy rule — not a task-specific check.
        if role == "entity":
            pol_low = policy.lower()
            if "high" in pol_low or "focus" in pol_low:
                role = "focus"
            elif "light" in pol_low or "bg" in pol_low:
                role = "background"
        if role == "focus":
            asset_key = f"{crop}_focus"
            pol = policy if policy != "TRELLIS.2" else "high_fidelity"
        else:
            asset_key = f"{crop}_bg"
            pol = policy if policy != "TRELLIS.2" else "lightweight_glb"
        asset_routes.append(make_asset_bind(oid, asset_key, pol))

    return asset_routes


def bind_scene(graph: TypedObjectGraph, ir: IntentIR,
               binding_vocab=None, unit_reg=None, asset_policy=None,
               catalog: dict[str, Any] | None = None) -> TypedObjectGraph:
    """Author gold-aligned bindings by construction.

    - Sensor/Camera/Device get a binding to a contained/served plant (or their declared
      target) with the canonical unit for their metric.
    - Devices get their correct asset_key via asset_policy (R4 satisfied at authoring).
    - Plants get asset bindings driven by their role/asset_policy (focus=high-fidelity,
      background=lightweight), so asset routing is identity-aware and general.
    """
    # Asset routes from the AssetCompiler (Plants + devices + missing-device placeholders).
    graph.bindings.extend(compile_asset_routes(graph, ir=ir))

    for n in graph.objects:
        nt = str(n.get("type") or "")
        if nt not in DEVICE_ASSET_CLASSES:
            continue
        oid = str(n.get("id") or "")
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
        # correct asset (R4 at authoring) — already emitted via compile_asset_routes.
    return graph


def build_scene_from_intent(prompt: str, llm_call_fn, budget, registry, agent_id: str,
                            catalog: dict[str, Any] | None = None) -> TypedObjectGraph:
    """End-to-end knowledge-compiled pipeline: IntentIR -> expand -> asset route -> bind.

    This is the KAFarmTwin-specific path (Task 2) that replaces the shared
    stepwise_build_scene for asset_routing tasks: the LLM only captures intent (one
    compact call), and the compiler + domain knowledge instantiate the typed object
    graph, route assets, and author bindings — no id/hierarchy/asset reinvention
    reaches the scorer.
    """
    ir = emit_intent(prompt, llm_call_fn, budget)
    graph = expand_graph(ir)
    bind_scene(graph, ir, catalog=catalog)
    if graph.objects:
        registry.call("scene.plan", {"objects": graph.objects}, agent_id=agent_id)
        registry.call("layout.solve", {"objects": graph.objects}, agent_id=agent_id)
        registry.call("layout.validate", {"layout": list(graph.objects)}, agent_id=agent_id)
    for b in graph.bindings:
        registry.call("object.bind", b, agent_id=agent_id)
    return graph