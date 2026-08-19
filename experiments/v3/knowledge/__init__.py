"""Knowledge modules for the KAFarmTwin semantic compiler.

Modules:
  ontology  - type definitions, identity classification (IDENTITY_CRITICAL)
  constraint - scene/binding constraints for the compiler
  mapping   - object graph mapping rules (parent resolution, find_child, etc.)
  policy    - (see asset_policy, binding_vocab, unit_registry for existing modules)
  asset_policy - correct device asset routing (R4 satisfied at authoring)
  binding_vocab - canonical binding types and compilation helpers
  unit_registry - canonical units for metric/unit pairs
"""