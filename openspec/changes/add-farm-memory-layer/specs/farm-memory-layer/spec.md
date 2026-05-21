## ADDED Requirements

### Requirement: Object synchronization frequency
The system SHALL define synchronization frequency for agricultural objects using realtime, hourly, daily, milestone, or static.

#### Scenario: Query object sync policy
- **WHEN** a client requests details for an agricultural object
- **THEN** the system SHALL expose the object's synchronization frequency or inherited object-type synchronization policy

#### Scenario: Critical plant geometry update
- **WHEN** a Plant object represents a key plant with stage-based geometry
- **THEN** the system SHALL allow milestone geometry updates while preserving higher-frequency status or observation updates

### Requirement: Metric dictionary
The system SHALL maintain a metric dictionary for temperature, humidity, soil moisture, CO2, light, pH, EC, water pressure, flow, and device switch state.

#### Scenario: Bind metric to sensor
- **WHEN** a Sensor object reports temperature or humidity
- **THEN** the metric SHALL be represented using the metric dictionary with a normalized key, unit, timestamp, value, and data quality status

#### Scenario: Unknown metric
- **WHEN** incoming data references a metric outside the dictionary
- **THEN** the system SHALL reject it or mark it as unmapped until the dictionary is extended

### Requirement: Object time-series query
The system SHALL support object-scoped queries for latest values, historical curves, aggregate statistics, and daily archives.

#### Scenario: Query 24 hour greenhouse environment
- **WHEN** a user queries a Greenhouse object's environment metrics for the last 24 hours
- **THEN** the system SHALL return time-series values or aggregates for the requested metrics within that object context

#### Scenario: Query seven day parcel moisture
- **WHEN** a user queries a Parcel object's soil moisture for the last 7 days
- **THEN** the system SHALL return historical values, aggregate statistics, or daily archive records for that Parcel

### Requirement: Object event memory
The system SHALL store and query object-scoped events for irrigation, fertilization, alerts, inspection, maintenance, and Agent analysis records.

#### Scenario: Query recent greenhouse events
- **WHEN** a user or Agent queries recent events for a Greenhouse object
- **THEN** the system SHALL return irrigation, fertilization, alert, inspection, maintenance, and Agent analysis events linked to the Greenhouse or its descendants

#### Scenario: Link alert event to device
- **WHEN** an alert is raised for a Device object
- **THEN** the event memory SHALL preserve the Device ID, timestamp, severity, summary, and related object context

### Requirement: Greenhouse report data source
The system SHALL provide a report data source that aggregates environment, device, alert, irrigation, and event data for a Greenhouse object.

#### Scenario: Generate greenhouse daily report
- **WHEN** ReportAgent or a report workflow requests a daily report data source for a Greenhouse
- **THEN** the system SHALL return environment summaries, device status summaries, alerts, irrigation events, and relevant recommendations context for that Greenhouse

#### Scenario: Missing report data
- **WHEN** required report data is missing or stale
- **THEN** the report data source SHALL expose the missing category and data quality status instead of silently omitting it

