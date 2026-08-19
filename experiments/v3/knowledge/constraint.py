"""Constraint knowledge: scene / binding constraints for the compiler (F/P1-3).

Encodes the invariants the compiled scene must satisfy by construction — device
default target classes, hierarchy parent resolution, device classes — so the
compiler never authors a scene that would violate R1/R3/R5/R6 at authoring time.
"""

from __future__ import annotations


# device -> the object class its sensor observes (semantic default for R6
# served-object bindings when the task does not declare an explicit target).
DEVICE_DEFAULT_TARGET_CLASS = {
    "Sensor": "plant",
    "Camera": "plant",
    "Irrigation": "plant",
    "Pump": "plot",
    "Device": "plot",
}

# metric the compiler authors for a device when none is declared (semantic default)
DEVICE_DEFAULT_METRIC = {
    "Pump": "moisture",
    "Irrigation": "moisture",
    "Sensor": "temperature",
    "Camera": "temperature",
    "WeatherStation": "temperature",
    "Device": "temperature",
}

# Device classes the compiler emits asset bindings for (R4 satisfied at authoring).
DEVICE_ASSET_CLASSES = ("Sensor", "Camera", "Device", "Irrigation", "Pump", "WeatherStation")

# Types that may carry count=N (aggregate background grouping); everything else is
# emitted as per-instance identity objects.
AGGREGATABLE_TYPES = ("Plant", "CropRow", "plant", "croprow")