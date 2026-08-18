"""Canonical unit registry (F, P1-3).

Mirrors the evaluator's binding_match._UNIT_CANONICAL so the semantic compiler emits
gold-aligned units by construction (no aliasing surprises at scoring time). A unit
pair (raw -> canonical) is stored here for every alias the scorer accepts.
"""

from __future__ import annotations

# raw authoring alias -> canonical unit
_UNIT_CANONICAL = {
    "%": "percent",
    "percent": "percent",
    "percentage": "percent",
    "celsius": "celsius",
    "c": "celsius",
    "degc": "celsius",
    "ppm": "ppm",
    "parts_per_million": "ppm",
}


def canonical_unit(unit) -> str:
    """Return the canonical form of a unit (as the scorer would normalize it)."""
    if unit is None:
        return ""
    return _UNIT_CANONICAL.get(str(unit).strip().lower(), str(unit).strip().lower())


# Common metric -> canonical unit the gold authors for that metric.
METRIC_UNIT = {
    "temperature": "celsius",
    "humidity": "percent",
    "moisture": "percent",
    "co2": "ppm",
    "co2_ppm": "ppm",
    "light": "klux",
    "soil_moisture": "percent",
}


def unit_for_metric(metric) -> str:
    """Canonical unit used for a given metric (fallback 'percent')."""
    from experiments.v3.knowledge.binding_vocab import canonical_metric  # type: ignore
    return METRIC_UNIT.get(canonical_metric(metric), "percent")