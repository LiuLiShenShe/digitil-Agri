"""Ontology knowledge: type definitions and identity classification (F/P1-3).

Defines which object types carry per-instance identity (must NOT be count-folded),
the hierarchy constraints (Greenhouse → Plot/CropRow → Plant), and the device
identity classification used by the semantic compiler to expand the object graph
without collapsing critical instance IDs.
"""

from __future__ import annotations


# Object types that carry per-instance identity (must NOT be count-folded).
# Identity types get distinct ids, explicit edges, and per-instance bindings.
# Non-identity types (Plant, CropRow) may carry count=N for grouping.
# C (review 2026-08-18): abstracted into IDENTITY_CRITICAL.
IDENTITY_CRITICAL = frozenset({
    "Camera", "Sensor", "Pump", "Valve", "Light", "WeatherStation",
    "Device", "Irrigation",
})

# Alias used by semantic_compiler; same set, different name for backwards compat.
IDENTITY_TYPES = IDENTITY_CRITICAL


# Hierarchy: the types that must have an explicit parent in the scene graph.
# An object without a parent in this set triggers R1 (illegal parent).
HIERARCHY_WITHOUT_PARENT = {"Camera", "Sensor", "Pump", "Irrigation", "WeatherStation"}


# Root greenhouse id used as the default root in expand_graph.
ROOT_ID = "greenhouse_1"
