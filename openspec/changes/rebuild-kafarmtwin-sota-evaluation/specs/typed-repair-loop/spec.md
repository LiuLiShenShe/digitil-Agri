## ADDED Requirements

### Requirement: Structured conflict representation
The repair loop SHALL represent each conflict with a structured record containing `conflict_id`, `rule_id`, `severity` (fatal|warning), `conflict_type`, `object_ids`, `observed`, `expected`, `evidence_ids`, `owner_agent`, `allowed_patch_ops`, and `status` (detected|patched|verified|rolled_back|unresolved).

#### Scenario: Detect a fatal rule conflict
- **WHEN** the validator finds an asset type mismatch (R4) on `pump_01`
- **THEN** the loop SHALL create a conflict with `rule_id=R4`, `severity=fatal`, `conflict_type=asset_type_mismatch`, `object_ids=[pump_01]`, and `status=detected`

### Requirement: Typed patch operations
The loop SHALL support at least these patch operations: `add_node`, `remove_node`, `replace_type`, `add_edge`, `remove_edge`, `replace_binding`, `update_transform`, `replace_asset`, `set_placeholder`. Each conflict SHALL declare its allowed patch operations.

#### Scenario: Replace a wrongly bound asset
- **WHEN** a pump is bound to a tomato asset
- **THEN** the loop SHALL be able to `replace_binding` on the pump to the irrigation asset or `set_placeholder` as allowed by the conflict's `allowed_patch_ops`

### Requirement: Full repair lifecycle with rollback
The repair flow SHALL be: detect → classify → route → propose patch → precheck → transactional apply → local revalidate → global fatal revalidate → commit/rollback. Patches SHALL be applied transactionally with a state snapshot before and after; a patch that fails local or global fatal revalidation SHALL be rolled back. Ranked conflict priority and a configurable maximum repair round count SHALL be respected.

#### Scenario: Commit on global success
- **WHEN** a proposed patch passes local revalidate and global fatal revalidate
- **THEN** the loop SHALL commit the patch and mark the conflict `status=patched` then `verified`

#### Scenario: Rollback on global fatal failure
- **WHEN** a patch introduces a new fatal conflict that the global revalidate rejects
- **THEN** the loop SHALL roll back to the pre-patch snapshot and mark the patch rolled back

### Requirement: Repair is verified, unresolved is not success
New conflicts introduced by a patch SHALL be counted separately. An unresolved conflict SHALL NOT be reported as success. Repair tasks T19–T24 SHALL verify that the specified `critical_objects` were actually modified from the real `initial_state`; merely regenerating a new scene without modifying the target object SHALL count as repair failure.

#### Scenario: Target object not actually modified
- **WHEN** a repair task's `critical_objects` are unchanged in the final state compared to `initial_state`
- **THEN** the repair SHALL be scored as failed even if a valid new scene was produced