"""Mapping knowledge: object graph mapping rules (F/P1-3).

Parent resolution, device target resolution, and identity-aggregate classification.
These are used by semantic_compiler.expand_graph to build the typed object graph
without embedding rule logic inline.
"""

from __future__ import annotations

from typing import Any

from experiments.v3.knowledge.ontology import IDENTITY_TYPES  # type: ignore
from experiments.v3.knowledge.constraint import AGGREGATABLE_TYPES  # type: ignore


def is_identity_type(nt: str) -> bool:
    """Return True if object type carries per-instance identity (must not be count-folded)."""
    return nt in IDENTITY_TYPES


def is_aggregatable(nt: str) -> bool:
    """Return True if the type may use count=N (background grouping)."""
    return nt in AGGREGATABLE_TYPES


def resolve_parent_hint(hint: str, default: str) -> str:
    """Resolve a parent hint string (e.g. 'root', '', or an explicit id) to a resolved parent."""
    if hint and hint.lower() == "root":
        return default
    return hint or default


def find_child(nodes: list[dict[str, Any]], parent_id: str, child_type: str) -> str | None:
    """Return the id of the first node of `child_type` under `parent_id`, else None."""
    for n in nodes:
        if n.get("type") == child_type and str(n.get("parent") or "") == parent_id:
            return str(n.get("id") or "")
    return None


def find_any(nodes: list[dict[str, Any]], typ: str) -> dict[str, Any] | None:
    """Return the first node dict whose type matches `typ`, else None."""
    for n in nodes:
        if n.get("type") == typ:
            return n
    return None


def find_contained_plant(nodes: list[dict[str, Any]], relations: list[dict[str, Any]],
                         parent_id: str) -> str | None:
    """Return a Plant object id contained under `parent_id`, else None."""
    contained = {r.get("object") for r in relations if r.get("subject") == parent_id}
    for n in nodes:
        if n.get("type") == "Plant" and str(n.get("id")) in contained:
            return str(n.get("id") or "")
    return None