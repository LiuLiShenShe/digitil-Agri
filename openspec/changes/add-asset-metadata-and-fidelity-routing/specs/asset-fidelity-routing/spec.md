## ADDED Requirements

### Requirement: Asset metadata registry
Every managed GLB asset SHALL have assetKey, category, source, license, fidelity level, thumbnail, GLB URL, applicable object types, quality information, and version information.

#### Scenario: Query asset metadata
- **WHEN** a user or Agent queries metadata for a managed asset
- **THEN** the system SHALL return assetKey, category, source, license, fidelity level, thumbnail, GLB URL, applicable object types, quality information, and version information

#### Scenario: Incomplete public asset metadata
- **WHEN** a public GLB asset lacks thumbnail, source, license, fidelity, or quality information
- **THEN** the system SHALL mark the asset metadata incomplete for asset validation

### Requirement: Asset ingestion validation
The system SHALL validate asset ingestion for Three.js loadability, axis, unit scale, center point, polygon count, textures, volume thresholds, thumbnail, source, and license.

#### Scenario: Accept valid GLB asset
- **WHEN** a GLB asset loads in Three.js and passes axis, unit, center, polygon, texture, volume, thumbnail, source, and license checks
- **THEN** the system SHALL allow the asset to be used as a validated managed asset

#### Scenario: Reject or flag invalid GLB asset
- **WHEN** a GLB asset fails loadability, geometry, texture, thumbnail, source, or license checks
- **THEN** the system SHALL reject the asset or flag it with quality issues before use in validated scenes

### Requirement: Fidelity routing strategy
The system SHALL route asset selection among existing assets, F2DMAS or high-fidelity reconstruction, TRELLIS.2 generation, procedural generation, and placeholder models based on object type, business value, fidelity need, availability, and waiting time.

#### Scenario: Route key plant asset
- **WHEN** a Plant object is marked as a key plant, abnormal plant, or research sample requiring trustworthy geometry
- **THEN** the system SHALL route it to F2DMAS or another high-fidelity reconstruction path when available

#### Scenario: Route ordinary missing equipment asset
- **WHEN** an ordinary equipment or decoration asset is missing from the asset library
- **THEN** the system SHALL create a TRELLIS.2 generation task or use a placeholder model while preserving the missing asset task

#### Scenario: Route procedural geometry
- **WHEN** an object represents a parcel, road, fence, ditch, or pipeline with rule-based geometry
- **THEN** the system SHALL prefer procedural generation when it satisfies the required fidelity

### Requirement: Placeholder continuity
Missing assets SHALL NOT block supported scene construction when a placeholder model and asset generation task can be created.

#### Scenario: Continue scene generation with placeholder
- **WHEN** semantic scene construction requests an unavailable GLB asset
- **THEN** the system SHALL insert a placeholder scene object and create an asset generation task linked to that object

#### Scenario: Track placeholder replacement
- **WHEN** a generated or approved asset becomes available for a placeholder object
- **THEN** the system SHALL preserve the scene object binding and allow replacing the placeholder asset with the final asset

### Requirement: Plant geometry versions
Key Plant objects SHALL support milestone geometry versions for seedling, vegetative, flowering, fruiting, and mature stages while maintaining phenotype data bindings.

#### Scenario: View plant stage geometry
- **WHEN** a user opens a key Plant object with multiple geometry versions
- **THEN** the system SHALL allow viewing the current milestone GLB version and related phenotype data

#### Scenario: Preserve historical plant geometry
- **WHEN** a key Plant object receives a new milestone GLB version
- **THEN** the system SHALL retain previous geometry version metadata for historical comparison

