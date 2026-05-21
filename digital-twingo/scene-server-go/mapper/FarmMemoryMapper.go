package mapper

import (
	"encoding/json"
	"fmt"
	"sort"
	"strings"
	"time"

	"scene-server-go/vo"
)

type FarmMemoryMapper struct{}

type farmEventRecord struct {
	ID              int64     `db:"id"`
	EventID         string    `db:"eventId"`
	ObjectID        string    `db:"objectId"`
	RelatedObjectID string    `db:"relatedObjectId"`
	EventType       string    `db:"eventType"`
	Severity        string    `db:"severity"`
	Summary         string    `db:"summary"`
	Timestamp       time.Time `db:"timestamp"`
	DataQuality     string    `db:"dataQuality"`
	Metadata        string    `db:"metadata"`
}

type farmDailyArchiveRecord struct {
	ID              int64     `db:"id"`
	ObjectID        string    `db:"objectId"`
	ArchiveDate     string    `db:"archiveDate"`
	MetricSummaries string    `db:"metricSummaries"`
	EventCounts     string    `db:"eventCounts"`
	DataQuality     string    `db:"dataQuality"`
	CreatedAt       time.Time `db:"createdAt"`
}

func NewFarmMemoryMapper() *FarmMemoryMapper {
	return &FarmMemoryMapper{}
}

func (m *FarmMemoryMapper) EnsureSchema() error {
	if db == nil {
		return fmt.Errorf("database is not initialized")
	}
	statements := []string{
		`CREATE TABLE IF NOT EXISTS farm_event_memory (
			id bigint NOT NULL AUTO_INCREMENT,
			eventId varchar(96) NOT NULL,
			objectId varchar(64) NOT NULL,
			relatedObjectId varchar(64) DEFAULT '',
			eventType varchar(32) NOT NULL,
			severity varchar(16) DEFAULT 'info',
			summary text,
			timestamp datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
			dataQuality varchar(16) NOT NULL DEFAULT 'simulated',
			metadata json DEFAULT NULL,
			PRIMARY KEY (id),
			UNIQUE KEY uk_event_id (eventId),
			INDEX idx_object_time (objectId, timestamp),
			INDEX idx_related_time (relatedObjectId, timestamp),
			INDEX idx_event_type (eventType)
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`,
		`CREATE TABLE IF NOT EXISTS farm_daily_archive (
			id bigint NOT NULL AUTO_INCREMENT,
			objectId varchar(64) NOT NULL,
			archiveDate date NOT NULL,
			metricSummaries json DEFAULT NULL,
			eventCounts json DEFAULT NULL,
			dataQuality varchar(16) NOT NULL DEFAULT 'simulated',
			createdAt datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
			PRIMARY KEY (id),
			UNIQUE KEY uk_object_date (objectId, archiveDate),
			INDEX idx_archive_date (archiveDate)
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`,
	}
	for _, statement := range statements {
		if _, err := db.Exec(statement); err != nil {
			return err
		}
	}
	if err := m.ensureIndex("iot_data", "idx_iot_data_device_metric_time", "ALTER TABLE iot_data ADD INDEX idx_iot_data_device_metric_time (deviceId, metricKey, timestamp)"); err != nil {
		return err
	}
	return nil
}

func (m *FarmMemoryMapper) ensureIndex(tableName string, indexName string, ddl string) error {
	var count int
	err := db.Get(&count, `SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
		WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ? AND INDEX_NAME = ?`, tableName, indexName)
	if err != nil {
		return err
	}
	if count > 0 {
		return nil
	}
	_, err = db.Exec(ddl)
	return err
}

func (m *FarmMemoryMapper) InsertMetricPoint(point vo.FarmMetricPointVo) error {
	if db == nil {
		return fmt.Errorf("database is not initialized")
	}
	_, err := db.Exec(`INSERT INTO iot_data (deviceId, metricKey, metricValue, unit, timestamp)
		VALUES (?, ?, ?, ?, ?)`,
		firstNonEmptyString(point.SourceDeviceID, point.ObjectID), point.MetricKey, point.Value, point.Unit, point.Timestamp)
	return err
}

func (m *FarmMemoryMapper) FindMetricPoints(objectIDs []string, metricKeys []string, start, end time.Time, limit int) ([]vo.FarmMetricPointVo, error) {
	if db == nil {
		return nil, fmt.Errorf("database is not initialized")
	}
	deviceIDs := objectIDsToDeviceIDs(objectIDs)
	if len(deviceIDs) == 0 {
		return []vo.FarmMetricPointVo{}, nil
	}
	query := `SELECT id, deviceId AS sourceDeviceId, deviceId AS objectId, metricKey, metricValue, unit, timestamp,
		'simulated' AS dataQuality FROM iot_data WHERE `
	args := []interface{}{}
	query += inClause("deviceId", deviceIDs, &args)
	if len(metricKeys) > 0 {
		query += " AND " + inClause("metricKey", metricKeys, &args)
	}
	if !start.IsZero() {
		query += " AND timestamp >= ?"
		args = append(args, start)
	}
	if !end.IsZero() {
		query += " AND timestamp <= ?"
		args = append(args, end)
	}
	query += " ORDER BY timestamp ASC"
	if limit > 0 {
		query += " LIMIT ?"
		args = append(args, limit)
	}
	var points []vo.FarmMetricPointVo
	if err := db.Select(&points, query, args...); err != nil {
		return nil, err
	}
	for i := range points {
		points[i].ObjectID = deviceIDToObjectID(points[i].SourceDeviceID, objectIDs)
	}
	return points, nil
}

func (m *FarmMemoryMapper) FindLatestMetricPoints(objectIDs []string, metricKeys []string) ([]vo.FarmMetricPointVo, error) {
	if db == nil {
		return nil, fmt.Errorf("database is not initialized")
	}
	deviceIDs := objectIDsToDeviceIDs(objectIDs)
	if len(deviceIDs) == 0 {
		return []vo.FarmMetricPointVo{}, nil
	}
	args := []interface{}{}
	query := buildLatestMetricPointsQuery(deviceIDs, metricKeys, &args)
	var result []vo.FarmMetricPointVo
	if err := db.Select(&result, query, args...); err != nil {
		return nil, err
	}
	for i := range result {
		result[i].ObjectID = deviceIDToObjectID(result[i].SourceDeviceID, objectIDs)
	}
	sort.SliceStable(result, func(i, j int) bool {
		if result[i].MetricKey == result[j].MetricKey {
			return result[i].SourceDeviceID < result[j].SourceDeviceID
		}
		return result[i].MetricKey < result[j].MetricKey
	})
	return result, nil
}

func buildLatestMetricPointsQuery(deviceIDs []string, metricKeys []string, args *[]interface{}) string {
	filterArgs := []interface{}{}
	filter := inClause("deviceId", deviceIDs, &filterArgs)
	if len(metricKeys) > 0 {
		filter += " AND " + inClause("metricKey", metricKeys, &filterArgs)
	}
	*args = append(*args, filterArgs...)
	*args = append(*args, filterArgs...)
	return `SELECT data.id, data.deviceId AS sourceDeviceId, data.deviceId AS objectId, data.metricKey,
		data.metricValue, data.unit, data.timestamp, 'simulated' AS dataQuality
		FROM iot_data data
		INNER JOIN (
			SELECT deviceId, metricKey, MAX(timestamp) AS timestamp
			FROM iot_data
			WHERE ` + filter + `
			GROUP BY deviceId, metricKey
		) latest ON latest.deviceId = data.deviceId
			AND latest.metricKey = data.metricKey
			AND latest.timestamp = data.timestamp
		WHERE ` + qualifyIotDataFilter(filter) + `
		ORDER BY data.metricKey ASC, data.deviceId ASC`
}

func qualifyIotDataFilter(filter string) string {
	filter = strings.ReplaceAll(filter, "deviceId", "data.deviceId")
	filter = strings.ReplaceAll(filter, "metricKey", "data.metricKey")
	return filter
}

func (m *FarmMemoryMapper) UpsertEvent(event vo.FarmEventVo) error {
	if db == nil {
		return fmt.Errorf("database is not initialized")
	}
	metadata, err := json.Marshal(event.Metadata)
	if err != nil {
		return err
	}
	_, err = db.Exec(`INSERT INTO farm_event_memory
		(eventId, objectId, relatedObjectId, eventType, severity, summary, timestamp, dataQuality, metadata)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, CAST(? AS JSON))
		ON DUPLICATE KEY UPDATE
			objectId = VALUES(objectId),
			relatedObjectId = VALUES(relatedObjectId),
			eventType = VALUES(eventType),
			severity = VALUES(severity),
			summary = VALUES(summary),
			timestamp = VALUES(timestamp),
			dataQuality = VALUES(dataQuality),
			metadata = VALUES(metadata)`,
		event.EventID, event.ObjectID, event.RelatedObjectID, event.EventType, event.Severity, event.Summary, event.Timestamp, event.DataQuality, string(metadata))
	return err
}

func (m *FarmMemoryMapper) FindEvents(objectIDs []string, eventTypes []string, start, end time.Time, limit int) ([]vo.FarmEventVo, error) {
	if db == nil {
		return nil, fmt.Errorf("database is not initialized")
	}
	args := []interface{}{}
	query := `SELECT id, eventId, objectId, relatedObjectId, eventType, severity, summary, timestamp, dataQuality,
		COALESCE(CAST(metadata AS CHAR), '{}') AS metadata
		FROM farm_event_memory WHERE (` + inClause("objectId", objectIDs, &args) + " OR " + inClause("relatedObjectId", objectIDs, &args) + ")"
	if len(eventTypes) > 0 {
		query += " AND " + inClause("eventType", eventTypes, &args)
	}
	if !start.IsZero() {
		query += " AND timestamp >= ?"
		args = append(args, start)
	}
	if !end.IsZero() {
		query += " AND timestamp <= ?"
		args = append(args, end)
	}
	query += " ORDER BY timestamp DESC"
	if limit > 0 {
		query += " LIMIT ?"
		args = append(args, limit)
	}
	var records []farmEventRecord
	if err := db.Select(&records, query, args...); err != nil {
		return nil, err
	}
	events := make([]vo.FarmEventVo, 0, len(records))
	for _, record := range records {
		metadata, err := parseJSONMap(record.Metadata)
		if err != nil {
			return nil, err
		}
		events = append(events, vo.FarmEventVo{
			ID: record.ID, EventID: record.EventID, ObjectID: record.ObjectID, RelatedObjectID: record.RelatedObjectID,
			EventType: record.EventType, Severity: record.Severity, Summary: record.Summary, Timestamp: record.Timestamp,
			DataQuality: record.DataQuality, Metadata: metadata,
		})
	}
	return events, nil
}

func (m *FarmMemoryMapper) UpsertDailyArchive(archive vo.FarmDailyArchiveVo) error {
	if db == nil {
		return fmt.Errorf("database is not initialized")
	}
	metricSummaries, err := json.Marshal(archive.MetricSummaries)
	if err != nil {
		return err
	}
	eventCounts, err := json.Marshal(archive.EventCounts)
	if err != nil {
		return err
	}
	createdAt := archive.CreatedAt
	if createdAt.IsZero() {
		createdAt = time.Now()
	}
	_, err = db.Exec(`INSERT INTO farm_daily_archive
		(objectId, archiveDate, metricSummaries, eventCounts, dataQuality, createdAt)
		VALUES (?, ?, CAST(? AS JSON), CAST(? AS JSON), ?, ?)
		ON DUPLICATE KEY UPDATE
			metricSummaries = VALUES(metricSummaries),
			eventCounts = VALUES(eventCounts),
			dataQuality = VALUES(dataQuality),
			createdAt = VALUES(createdAt)`,
		archive.ObjectID, archive.ArchiveDate, string(metricSummaries), string(eventCounts), archive.DataQuality, createdAt)
	return err
}

func (m *FarmMemoryMapper) FindDailyArchives(objectID string, days int, endDate string) ([]vo.FarmDailyArchiveVo, error) {
	if db == nil {
		return nil, fmt.Errorf("database is not initialized")
	}
	if days <= 0 {
		days = 7
	}
	query := `SELECT id, objectId, DATE_FORMAT(archiveDate, '%Y-%m-%d') AS archiveDate,
		COALESCE(CAST(metricSummaries AS CHAR), '{}') AS metricSummaries,
		COALESCE(CAST(eventCounts AS CHAR), '{}') AS eventCounts,
		dataQuality, createdAt FROM farm_daily_archive WHERE objectId = ?`
	args := []interface{}{objectID}
	if endDate != "" {
		query += " AND archiveDate <= ?"
		args = append(args, endDate)
	}
	query += " ORDER BY archiveDate DESC LIMIT ?"
	args = append(args, days)
	var records []farmDailyArchiveRecord
	if err := db.Select(&records, query, args...); err != nil {
		return nil, err
	}
	archives := make([]vo.FarmDailyArchiveVo, 0, len(records))
	for _, record := range records {
		metricSummaries := map[string]vo.FarmMetricAggregateVo{}
		eventCounts := map[string]int{}
		if err := json.Unmarshal([]byte(record.MetricSummaries), &metricSummaries); err != nil {
			return nil, err
		}
		if err := json.Unmarshal([]byte(record.EventCounts), &eventCounts); err != nil {
			return nil, err
		}
		archives = append(archives, vo.FarmDailyArchiveVo{
			ID: record.ID, ObjectID: record.ObjectID, ArchiveDate: record.ArchiveDate,
			MetricSummaries: metricSummaries, EventCounts: eventCounts, DataQuality: record.DataQuality, CreatedAt: record.CreatedAt,
		})
	}
	return archives, nil
}

func inClause(column string, values []string, args *[]interface{}) string {
	if len(values) == 0 {
		return "1=0"
	}
	placeholders := make([]string, 0, len(values))
	for _, value := range values {
		placeholders = append(placeholders, "?")
		*args = append(*args, value)
	}
	return column + " IN (" + strings.Join(placeholders, ",") + ")"
}

func objectIDsToDeviceIDs(objectIDs []string) []string {
	bindings := map[string][]string{
		"gh-tomato-001":         {"iot-greenhouse-01", "iot-irrigation-01", "iot-camera-01"},
		"parcel-tomato-a":       {"iot-field-01", "iot-greenhouse-01"},
		"sensor-greenhouse-001": {"iot-greenhouse-01"},
		"device-irrigation-001": {"iot-irrigation-01"},
		"camera-greenhouse-001": {"iot-camera-01"},
		"farm-yupont-demo":      {"iot-greenhouse-01", "iot-field-01", "iot-weather-01", "iot-irrigation-01", "iot-camera-01"},
	}
	result := []string{}
	for _, objectID := range objectIDs {
		if devices, ok := bindings[objectID]; ok {
			result = append(result, devices...)
		}
		if strings.HasPrefix(objectID, "iot-") {
			result = append(result, objectID)
		}
	}
	return uniqueMapperStrings(result)
}

func deviceIDToObjectID(deviceID string, objectIDs []string) string {
	for _, objectID := range objectIDs {
		for _, candidate := range objectIDsToDeviceIDs([]string{objectID}) {
			if candidate == deviceID {
				return objectID
			}
		}
	}
	return deviceID
}

func uniqueMapperStrings(values []string) []string {
	seen := map[string]bool{}
	result := []string{}
	for _, value := range values {
		if value == "" || seen[value] {
			continue
		}
		seen[value] = true
		result = append(result, value)
	}
	sort.Strings(result)
	return result
}

func firstNonEmptyString(values ...string) string {
	for _, value := range values {
		if value != "" {
			return value
		}
	}
	return ""
}
