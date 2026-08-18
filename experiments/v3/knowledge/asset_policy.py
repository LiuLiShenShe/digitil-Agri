"""Asset-policy knowledge (F, P1-3).

Maps each device object type to its correct asset key (the R4 asset_type contract)
and encodes the crop->policy routing the compiler applies when authoring asset
bindings. Mirrors rule_engine.R4's _ASSET_BY_TYPE so the compiler never authors a
wrong device asset to begin with.
"""

from __future__ import annotations

from typing import Any

# device type -> correct asset key (unambiguous R4 contract)
ASSET_BY_TYPE = {
    "Pump": "irrigation",
    "Irrigation": "irrigation",
    "Camera": "camera",
    "Sensor": "sensor",
}

# crop/plant object heuristic -> generation policy
CROP_POLICY = {
    "lettuce": "TRELLIS.2",
    "tomato": "TRELLIS.2",
    "strawberry": "TRELLIS.2",
    "plant": "TRELLIS.2",
}

# fallback names used to detect a plant's crop kind from its id (crop-in-id heuristic)
CROP_HINTS = ("lettuce", "tomato", "strawberry", "corn", "kiwi", "soy", "alfalfa")


def asset_key_for(node: dict[str, Any]) -> str | None:
    """Return the correct asset_key for a device node, else None (not a device)."""
    nt = str(node.get("type") or "")
    return ASSET_BY_TYPE.get(nt)


def policy_for(node: dict[str, Any]) -> str:
    """Return the encoding policy for an object from its type/id (crop-aware)."""
    oid = str(node.get("id") or "").lower()
    nt = str(node.get("type") or "").lower()
    # crop rows / plants: pick policy by crop hint in id
    if nt in ("plant", "crop", "croprow"):
        for hint in CROP_HINTS:
            if hint in oid:
                return CROP_POLICY.get(hint, "TRELLIS.2")
        return "TRELLIS.2"
    return "TRELLIS.2"


def catalog_for(asset_key: str) -> dict[str, Any]:
    """Stub catalog metadata for an asset key (kept minimal; the evaluator only needs
    asset_key/policy, which are authoring-time, not a model library lookup)."""
    return {"policy": "TRELLIS.2", "assetKey": asset_key}