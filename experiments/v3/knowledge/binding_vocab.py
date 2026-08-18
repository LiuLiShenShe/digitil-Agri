"""Canonical binding vocabulary (F, P1-3).

Defines the exact binding types and target-id conventions a method compiles so the
scorer's binding_match recognizes them. Mirrors the evaluator's binding contract
(types asset / sensor_bind / trait_bind / asset_job, target notation for assets).
"""

from __future__ import annotations

from typing import Iterable

BINDING_TYPES = ("asset", "sensor_bind", "trait_bind", "asset_job")

# sensor_bind / trait_bind target a real monitored object id (a node).
# asset / asset_job bindings carry the object's current asset in metadata.asset_key
# (and job_type=placeholder for asset_job); their `target` is a notation placeholder
# the scorer normalizes by metadata, so the exact target string does not need to be a
# scene node — but the metadata must carry the asset_key.

# metric aliases -> canonical metric (mirrors how gold authors metric lists)
_METRIC_CANONICAL = {
    "temperature": "temperature",
    "temp": "temperature",
    "humidity": "humidity",
    "moisture": "moisture",
    "soil_moisture": "soil_moisture",
    "co2": "co2_ppm",
    "co2ppm": "co2_ppm",
}


def canonical_metric(m) -> str:
    if m is None:
        return ""
    return _METRIC_CANONICAL.get(str(m).strip().lower(), str(m).strip().lower())


def canonical_metrics(metrics: Iterable) -> list[str]:
    return [canonical_metric(m) for m in (metrics or []) if m]


def make_sensor_bind(subject: str, target: str, metrics, unit: str) -> dict:
    """Compile a sensor_bind the evaluator will match against gold sensor bindings."""
    return {
        "subject": subject,
        "target": target,
        "type": "sensor_bind",
        "metadata": {"metrics": canonical_metrics(metrics), "unit": unit},
    }


def make_asset_bind(subject: str, asset_key: str, policy: str = "TRELLIS.2") -> dict:
    """Compile an asset binding carrying the object's current asset via metadata."""
    return {
        "subject": subject,
        "target": f"{subject}_asset",
        "type": "asset",
        # asset bindings normally do NOT carry the object's asset_key as a target id;
        # they carry metadata describing the assets routed to this object (policy) and
        # the asset key so the evaluator's semantic asset path can match.
        "metadata": {"asset_key": asset_key, "policy": policy},
    }


def make_asset_job_placeholder(subject: str) -> dict:
    """Compile an asset_job placeholder (job_type=placeholder), matching the disjunctive
    repair contract where a replacement is pending for a device asset."""
    return {
        "subject": subject,
        "target": f"{subject}_placeholder",
        "type": "asset_job",
        "metadata": {"job_type": "placeholder"},
    }