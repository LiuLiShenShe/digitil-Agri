## ADDED Requirements

### Requirement: Scene object primary business binding
Each 3D scene object SHALL be able to bind zero or one primary agricultural business object.

Each persisted scene object SHALL expose a stable `sceneObjectId` and MAY expose `businessObjectId`, `assetKey`, and `isDefaultBinding` metadata.

#### Scenario: Bind greenhouse mesh to business object
- **WHEN** an operator binds a greenhouse scene object to a Greenhouse business object
- **THEN** the scene object SHALL persist the Greenhouse object ID as its primary business binding

#### Scenario: Prevent ambiguous primary binding
- **WHEN** an operator attempts to assign multiple primary business objects to one scene object
- **THEN** the system SHALL reject the ambiguous binding or require one primary object to be selected

### Requirement: Business object multi-scene binding
Each agricultural business object SHALL be able to bind zero or more 3D scene objects for multi-view, multi-LOD, internal, external, or component-level representation.

When multiple scene objects bind to one business object, the system SHALL return all bindings and SHOULD sort the default binding first when `isDefaultBinding` is available.

#### Scenario: Locate all visual representations
- **WHEN** a user requests scene representations for a business object
- **THEN** the system SHALL return all scene object IDs bound to that business object

#### Scenario: Business object without scene object
- **WHEN** a business object has no scene object binding
- **THEN** the system SHALL keep the business object queryable and SHALL report that no visual representation is available

### Requirement: 3D selection business detail
The system SHALL allow users to select a bound 3D scene object and view the associated business object details, current status, recent metrics, alerts, historical trend entry points, and related events.

#### Scenario: Select bound greenhouse
- **WHEN** a user selects a greenhouse scene object with a valid business binding
- **THEN** the system SHALL show the Greenhouse details, related sensors, devices, metrics, alerts, and events

#### Scenario: Select unbound object
- **WHEN** a user selects a scene object without a business binding
- **THEN** the system SHALL show the scene object details and indicate that no business object is bound

### Requirement: Business-to-scene location
The system SHALL allow users to locate a business object in the 3D scene when one or more scene object bindings exist.

#### Scenario: Locate device from business list
- **WHEN** a user selects a Device object in a business object list and requests scene location
- **THEN** the system SHALL focus or highlight the bound scene object when available

#### Scenario: Multiple scene bindings
- **WHEN** a business object has multiple scene object bindings
- **THEN** the system SHALL present or choose a default visual representation and preserve access to the remaining representations

### Requirement: Binding validation
The system SHALL validate scene objects for missing business bindings, missing data bindings, and missing asset metadata.

The validation result SHALL include total scene objects, bound scene objects, binding rate, verified core object types, missing core object types, and issue entries categorized as `missing_business_binding`, `missing_data_binding`, or `missing_asset_metadata`.

#### Scenario: Validate core observable objects
- **WHEN** the system validates a complete greenhouse scene
- **THEN** it SHALL report missing business bindings for Greenhouse, Parcel, Plant, Sensor, Device, and Camera scene objects

#### Scenario: Validator finds data or asset gaps
- **WHEN** a bound scene object lacks related metrics or required asset metadata
- **THEN** the validation result SHALL identify the object and the missing data or metadata category
