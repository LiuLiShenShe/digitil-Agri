## ADDED Requirements

### Requirement: Agricultural object registry
The system SHALL maintain a registry of agricultural digital twin objects covering Farm, Greenhouse, Parcel, CropRow, Plant, CropBatch, Sensor, Device, Camera, Operation, and Observation.

#### Scenario: Create tomato greenhouse object set
- **WHEN** the platform prepares the tomato greenhouse MVP data
- **THEN** it SHALL include at least one Greenhouse, one Parcel, one CropBatch, one CropRow, one Plant, one Sensor, one Device, and one Camera object in the registry

#### Scenario: Reject unknown object type
- **WHEN** an object is created with a type outside the supported registry
- **THEN** the system SHALL reject the object or mark it invalid with a validation error

### Requirement: Object identity and metadata
Each agricultural object SHALL expose a globally unique ID, object type, display name, parent relation, spatial location or containing area, current status, updated timestamp, data quality status, and extensible metadata.

#### Scenario: Query object detail
- **WHEN** a client requests an agricultural object by ID
- **THEN** the response SHALL include identity, type, name, parent relation, spatial anchor, current status, updated timestamp, data quality status, and metadata

#### Scenario: Missing required metadata
- **WHEN** an object lacks a required identity, type, name, parent relation, status, updated timestamp, or data quality field
- **THEN** the system SHALL report the object as incomplete for twin validation

### Requirement: Object relationship queries
The system SHALL support relationship queries across parent-child hierarchy, associated devices, sensors, cameras, crop batches, plants, metrics, events, analysis records, and asset versions.

#### Scenario: Query greenhouse relationships
- **WHEN** a user or Agent queries relationships for a Greenhouse object
- **THEN** the system SHALL return its Parcels, CropRows, CropBatches, Sensors, Devices, Cameras, key Plants, events, metrics, and related assets when available

#### Scenario: Query device parent context
- **WHEN** a user or Agent queries relationships for a Device object
- **THEN** the system SHALL return the containing Greenhouse or Parcel and any related Sensor, metric, event, and alert context when available

### Requirement: Object lookup tool contract
The system SHALL provide a stable object lookup contract that can be used by UI flows and Agent tools to resolve object details and relationships.

#### Scenario: Agent requests object lookup
- **WHEN** an Agent calls `object.lookup` with a valid object ID
- **THEN** the system SHALL return the object's normalized details without requiring direct database access

#### Scenario: Agent requests object relationships
- **WHEN** an Agent calls `object.relations` with a valid object ID
- **THEN** the system SHALL return normalized relationships without exposing arbitrary query execution

