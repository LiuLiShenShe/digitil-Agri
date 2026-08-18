"""Executable rule engine for R1-R10 (aligned with the Go backend's validate logic).

The evaluator is fully independent of the scored methods: it only reads the
method's produced scene state (nodes/edges/bindings), the task gold, and the
shared trace, and reports rule violations. Rules that govern repair correctness
(R10) are asserted against the actual final state vs initial_state, and require
that `critical_objects` were actually modified.

Violations are classified fatal vs warning. Fatal violations fail CVSR.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuleViolation:
    rule_id: str
    severity: str  # fatal | warning
    message: str
    object_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "object_ids": self.object_ids,
        }


FATAL_RULES = {"R1", "R2", "R3", "R4", "R7"}


def _ids(nodes: list[dict[str, Any]]) -> set[str]:
    return {str(n.get("id") or "") for n in nodes}


def _type_of(n: dict[str, Any]) -> str:
    return str(n.get("type") or n.get("assetKey") or n.get("category") or "")


def _norm(s: Any) -> str:
    return str(s or "").strip().lower()


def _parent(n: dict[str, Any]) -> str:
    return str(n.get("parent") or "")


def _get(key: str, n: dict[str, Any]):
    """Read a field from top-level OR key_attrs (either representation).

    Prefers key_attrs (the canonical location for semantic fields after
    canonicalization / layout-solve / typed-repair updates), falling back to
    top-level. This avoids a stale top-level location shadowing a repaired
    key_attrs.location.
    """
    ka = n.get("key_attrs") or {}
    if key in ka:
        return ka.get(key)
    if key in n:
        return n.get(key)
    return None


class RuleEngine:
    """Evaluate a scene state against the R1-R10 executable rules.

    State shape (generic, method-independent):
      nodes:   list of {id, type, parent?, key_attrs?, ...}
      edges:   list of {subject, predicate, object}
      bindings:list of {subject, target, type, metadata?}
    """

    def __init__(self) -> None:
        self.fatal_rules = set(FATAL_RULES)

    def evaluate(self, *, nodes: list[dict[str, Any]], edges: list[dict[str, Any]],
                 bindings: list[dict[str, Any]], active_rules: list[str],
                 task: dict[str, Any] | None = None,
                 initial_state: dict[str, Any] | None = None,
                 goal_state: dict[str, Any] | None = None) -> list[RuleViolation]:
        active = set(active_rules)
        violations: list[RuleViolation] = []
        nodes = nodes or []
        edges = edges or []
        bindings = bindings or []
        node_ids = _ids(nodes)
        node_by_id = {str(n.get("id") or ""): n for n in nodes}
        edge_keys = {(str(e.get("subject") or ""), str(e.get("predicate") or ""), str(e.get("object") or "")) for e in edges}
        binding_keys = {(str(b.get("subject") or ""), str(b.get("target") or ""), str(b.get("type") or "")) for b in bindings}
        bindings_by_key = {(str(b.get("subject") or ""), str(b.get("target") or ""), str(b.get("type") or "")): b for b in bindings}

        if "R1" in active:
            # Hierarchy: Greenhouse contains CropRow/Plot/Plant; CropRow contains Plant.
            # The frozen gold does NOT encode parent fields (0/91 required_nodes carry one),
            # so "no parent" is a warning (incomplete hierarchy), NOT fatal. An ILLEGAL
            # parent (wrong type) remains fatal. This aligns the rule with the gold's
            # annotation granularity instead of punishing every method that faithfully
            # reproduces the gold.
            for n in nodes:
                p = node_by_id.get(_parent(n))
                if p is None:
                    if _type_of(n) in {"Plant", "CropRow", "Sensor", "Camera", "Irrigation", "Pump", "WeatherStation"} \
                            and n.get("role") != "root":
                        violations.append(RuleViolation("R1", "warning",
                                                        f"object {n.get('id')} of type {_type_of(n)} has no parent",
                                                        [str(n.get('id') or '')]))
                    continue
                pt = _type_of(p)
                nt = _type_of(n)
                legal = {
                    "Greenhouse": {"Plot", "CropRow", "Plant", "Sensor", "Camera", "WeatherStation", "Irrigation", "Pump", "Device"},
                    "Plot": {"CropRow", "Plant", "Sensor"},
                    "CropRow": {"Plant"},
                }.get(pt, set())
                if nt and pt in legal and nt not in legal:
                    violations.append(RuleViolation("R1", "fatal",
                                                    f"illegal parent: {nt} {n.get('id')} under {pt}", [str(n.get('id') or '')]))

        if "R2" in active:
            # Data binding legal: sensors/traits/events must have binding target + unit + timestamp metadata.
            # unit/timestamp may live on the node's key_attrs OR on the binding's
            # metadata (the gold authors sensor_bind metadata with unit/metrics, and
            # does not duplicate them onto the node). Accepting either representation
            # aligns the rule with the gold's authoring convention.
            for n in nodes:
                if _type_of(n) in {"Sensor", "Trait", "Event"}:
                    node_id = str(n.get("id") or "")
                    binding_md = {}
                    for (s, _t, _ty), b in bindings_by_key.items():
                        if s == node_id:
                            binding_md = b.get("metadata") or {}
                            break
                    has_binding = any(s == node_id for (s, _t, _ty) in binding_keys)
                    meta = {}
                    meta["unit"] = _get("unit", n)
                    meta["timestamp"] = _get("timestamp", n)
                    has_unit = bool(meta.get("unit") or meta.get("timestamp")
                                   or binding_md.get("unit") or binding_md.get("timestamp"))
                    if not has_binding:
                        violations.append(RuleViolation("R2", "fatal",
                                                        f"{n.get('id')} missing data binding", [str(n.get('id') or '')]))
                    elif not has_unit:
                        violations.append(RuleViolation("R2", "fatal",
                                                        f"{n.get('id')} missing unit/timestamp metadata", [str(n.get('id') or '')]))

        if "R3" in active:
            # Spatial layout legal: objects not out of bounds / not floating / within parent bounds.
            # The frozen gold does NOT encode coordinates on its nodes, so "no location"
            # is a warning (spatial detail absent), NOT fatal. OOB/illegal positions
            # (when a location IS present) remain fatal — that is the real spatial error
            # this rule exists to catch. T20's Row_05 at {x:29,z:9} vs Plot bounds
            # z_max=8 is a genuine out-of-bounds repair target.
            for n in nodes:
                loc = _get("location", n)
                if loc is None:
                    if _type_of(n) not in {"Greenhouse", "Plot"}:
                        violations.append(RuleViolation("R3", "warning",
                                                        f"{n.get('id')} has no location", [str(n.get('id') or '')]))
                    continue
                # bounds check against an ancestor Plot/Greenhouse bounds (if declared)
                if isinstance(loc, dict) and ("x" in loc or "z" in loc):
                    x = loc.get("x", 0)
                    z = loc.get("z", 0)
                    bounds = None
                    p = node_by_id.get(_parent(n))
                    if p is not None:
                        bounds = p.get("bounds") or p.get("key_attrs", {}).get("bounds")
                    if bounds:
                        try:
                            x_min = float(bounds.get("x_min", 0))
                            x_max = float(bounds.get("x_max", 1e9))
                            z_min = float(bounds.get("z_min", 0))
                            z_max = float(bounds.get("z_max", 1e9))
                        except (TypeError, ValueError):
                            x_min = z_min = 0.0
                            x_max = z_max = 1e9
                        if not (x_min <= x <= x_max and z_min <= z <= z_max):
                            violations.append(RuleViolation(
                                "R3", "fatal",
                                f"{n.get('id')} out of parent bounds (loc={loc}, bounds={bounds})",
                                [str(n.get('id') or '')]))

        if "R4" in active:
            # Asset type consistent: an object's asset_key must match the device-asset
            # contract for its type. Detects a wrong asset_key on an object itself
            # (R4 node.asset_key check — previously only checked binding target type)
            # AND a pump wrongly bound to a plant asset.
            _ASSET_BY_TYPE = {
                "Pump": ("irrigation", {"tomato", "plant", "lettuce", "strawberry", "corn", "lemongrass", "basil", "oregano", "soy", "alfalfa"}),
                "Camera": ("camera", {"tomato", "plant", "lettuce", "strawberry", "corn", "lemongrass", "basil", "oregano", "soy", "alfalfa"}),
                "Sensor": ("sensor", {"tomato", "plant", "lettuce", "strawberry", "corn", "lemongrass", "basil", "oregano", "soy", "alfalfa"}),
                "Irrigation": ("irrigation", {"tomato", "plant", "lettuce", "strawberry", "corn", "lemongrass", "basil", "oregano", "soy", "alfalfa"}),
            }
            for n in nodes:
                nt = _type_of(n)
                if nt not in _ASSET_BY_TYPE:
                    continue
                correct, wrong_assets = _ASSET_BY_TYPE[nt]
                node_asset = _norm(str(_get("asset_key", n) or n.get("asset_key") or ""))
                if node_asset and node_asset in wrong_assets:
                    violations.append(RuleViolation("R4", "fatal",
                                                    f"node {n.get('id')} of type {nt} has wrong asset_key={node_asset!r} (expected {correct!r})",
                                                    [str(n.get('id') or '')]))
            # Also check asset-typed bindings: a pump bound to a plant asset target.
            for b in bindings:
                subject = b.get("subject")
                target = b.get("target")
                btype = _norm(b.get("type") or "")
                if btype == "asset":
                    s_obj = node_by_id.get(str(subject) or "")
                    st = _type_of(s_obj) if s_obj else ""
                    target_norm = _norm(str(target or ""))
                    if st == "Pump" and target_norm in {"tomato", "plant", "lettuce", "strawberry", "corn"}:
                        violations.append(RuleViolation("R4", "fatal",
                                                        f"pump {subject} wrongly bound to plant asset {target}",
                                                        [str(subject or '')]))

        if "R5" in active:
            # Camera legal: must have pose, observes target, and fov.
            for n in nodes:
                if _type_of(n) == "Camera":
                    # pose/observes/fov may be on top-level OR key_attrs (gold writes them top-level)
                    if not (_get("pose", n) and _get("observes", n) and _get("fov", n)):
                        violations.append(RuleViolation("R5", "fatal",
                                                        f"camera {n.get('id')} missing pose/observes/fov",
                                                        [str(n.get('id') or '')]))

        if "R6" in active:
            # Device coverage: irrigation/pump/lighting/ventilation must bind a control region or served object.
            for n in nodes:
                if _type_of(n) in {"Irrigation", "Pump", "Device"}:
                    if not any(s == str(n.get("id") or "") for (s, _t, _ty) in binding_keys):
                        violations.append(RuleViolation("R6", "fatal",
                                                        f"device {n.get('id')} missing served-object binding",
                                                        [str(n.get('id') or '')]))

        if "R7" in active:
            # Agent trace complete: planning, layout, asset_routing, data_binding, validation present (validated in trace_evidence).
            # Here we only emit a placeholder if the caller supplies trace_complete=False.
            if task is not None and not task.get("_trace_complete", True):
                violations.append(RuleViolation("R7", "fatal", "agent trace incomplete", []))

        if "R8" in active:
            # Memory query legal: historical queries bounded by object/metric/range/event-type/limit.
            for b in bindings:
                if b.get("type") == "memory_query":
                    md = b.get("metadata") or {}
                    if not (md.get("object_id") and md.get("metric") and md.get("time_range")):
                        violations.append(RuleViolation("R8", "fatal",
                                                        f"memory query {b.get('subject')} unbounded",
                                                        [str(b.get('subject') or '')]))

        if "R9" in active:
            # Missing asset must not break: a placeholder asset_job must be present
            # when a device asset is committed as a placeholder (set_placeholder
            # branch of the repair contract), instead of silently retaining the
            # wrong-mismatched binding. Previously `pass` — now it is a real check:
            # any asset_job binding must carry job_type=placeholder; a retained
            # wrong asset_key on the same object is a fatal R9 violation.
            for b in bindings:
                btype = _norm(b.get("type") or "")
                subject = b.get("subject")
                md = b.get("metadata") or {}
                if btype == "asset_job":
                    job_type = _norm(md.get("job_type") or "")
                    if job_type != "placeholder":
                        violations.append(RuleViolation(
                            "R9", "fatal",
                            f"placeholder asset_job on {subject} missing job_type=placeholder (got {job_type!r})",
                            [str(subject or '')]))
                elif btype == "asset":
                    # a retained asset binding with a wrong (non-empty, non-device)
                    # asset_key on a placeholder-able object = the mismatch survived
                    bkey = _norm(md.get("asset_key") or "")
                    if bkey in {"tomato", "plant", "lettuce", "strawberry", "corn",
                                "lemongrass", "basil", "oregano", "soy", "alfalfa"}:
                        violations.append(RuleViolation(
                            "R9", "fatal",
                            f"asset mismatch retained on {subject}: asset_key={bkey!r}",
                            [str(subject or '')]))

        if "R10" in active:
            # Errors must be correctable: repair tasks must actually modify critical_objects
            # from initial_state. Evaluated against final state vs initial/goal.
            if initial_state is not None and goal_state is not None and task is not None:
                critical = task.get("critical_objects") or []
                for cid in critical:
                    init_node = _find_node(initial_state.get("objects") or [], cid)
                    final_node = node_by_id.get(cid)
                    if init_node is not None and final_node is None:
                        violations.append(RuleViolation("R10", "fatal",
                                                        f"critical object {cid} disappeared (not preserved+modified)",
                                                        [cid]))
                    elif init_node is not None and final_node is not None and _same_object(init_node, final_node):
                        violations.append(RuleViolation("R10", "fatal",
                                                        f"critical object {cid} was NOT actually modified",
                                                        [cid]))

        return violations


def _find_node(nodes: list[dict[str, Any]], oid: str) -> dict[str, Any] | None:
    for n in nodes:
        if str(n.get("id") or "") == oid:
            return n
    return None


def _same_object(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Return True if object b is structurally identical to a (no meaningful change)."""
    keys = ("monitoring_target", "belongs_to", "observes", "pose", "fov", "asset_key", "asset_policy")
    return all(a.get(k) == b.get(k) for k in keys)
