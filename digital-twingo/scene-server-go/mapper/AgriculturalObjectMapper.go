package mapper

import (
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"time"

	"scene-server-go/vo"
)

type AgriculturalObjectRecord struct {
	ObjectID       string `db:"objectId"`
	ObjectType     string `db:"objectType"`
	Name           string `db:"name"`
	ParentID       string `db:"parentId"`
	ContainingArea string `db:"containingArea"`
	Spatial        string `db:"spatial"`
	Status         string `db:"status"`
	UpdatedAt      string `db:"updatedAt"`
	DataQuality    string `db:"dataQuality"`
	Metadata       string `db:"metadata"`
}

type AgriculturalRelationRecord struct {
	ID             int64  `db:"id"`
	SourceObjectID string `db:"sourceObjectId"`
	RelationType   string `db:"relationType"`
	TargetObjectID string `db:"targetObjectId"`
	TargetType     string `db:"targetType"`
	TargetLabel    string `db:"targetLabel"`
	Metadata       string `db:"metadata"`
}

type AgriculturalObjectMapper struct{}

func NewAgriculturalObjectMapper() *AgriculturalObjectMapper {
	return &AgriculturalObjectMapper{}
}

func (m *AgriculturalObjectMapper) EnsureSchema() error {
	if db == nil {
		return fmt.Errorf("database is not initialized")
	}
	statements := []string{
		`CREATE TABLE IF NOT EXISTS agricultural_object (
			objectId varchar(64) NOT NULL,
			objectType varchar(32) NOT NULL,
			name varchar(128) NOT NULL,
			parentId varchar(64) DEFAULT '',
			containingArea varchar(128) DEFAULT '',
			` + "`spatial`" + ` json DEFAULT NULL,
			status varchar(32) NOT NULL DEFAULT 'normal',
			updatedAt datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
			dataQuality varchar(16) NOT NULL DEFAULT 'simulated',
			metadata json DEFAULT NULL,
			PRIMARY KEY (objectId),
			INDEX idx_object_type (objectType),
			INDEX idx_parent_id (parentId),
			INDEX idx_data_quality (dataQuality)
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`,
		`CREATE TABLE IF NOT EXISTS agricultural_object_relation (
			id bigint NOT NULL AUTO_INCREMENT,
			sourceObjectId varchar(64) NOT NULL,
			relationType varchar(32) NOT NULL,
			targetObjectId varchar(64) DEFAULT '',
			targetType varchar(32) DEFAULT '',
			targetLabel varchar(128) DEFAULT '',
			metadata json DEFAULT NULL,
			PRIMARY KEY (id),
			UNIQUE KEY uk_source_relation_target (sourceObjectId, relationType, targetObjectId, targetLabel),
			INDEX idx_source_relation (sourceObjectId, relationType),
			INDEX idx_target_object (targetObjectId)
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`,
	}
	for _, statement := range statements {
		if _, err := db.Exec(statement); err != nil {
			return err
		}
	}
	return nil
}

func (m *AgriculturalObjectMapper) UpsertObject(obj vo.AgriculturalObjectVo) error {
	if db == nil {
		return fmt.Errorf("database is not initialized")
	}
	spatial, err := marshalJSONMap(obj.Spatial)
	if err != nil {
		return err
	}
	metadata, err := marshalJSONMap(obj.Metadata)
	if err != nil {
		return err
	}
	_, err = db.Exec(`INSERT INTO agricultural_object
		(objectId, objectType, name, parentId, containingArea, `+"`spatial`"+`, status, updatedAt, dataQuality, metadata)
		VALUES (?, ?, ?, ?, ?, CAST(? AS JSON), ?, ?, ?, CAST(? AS JSON))
		ON DUPLICATE KEY UPDATE
			objectType = VALUES(objectType),
			name = VALUES(name),
			parentId = VALUES(parentId),
			containingArea = VALUES(containingArea),
			`+"`spatial`"+` = VALUES(`+"`spatial`"+`),
			status = VALUES(status),
			updatedAt = VALUES(updatedAt),
			dataQuality = VALUES(dataQuality),
			metadata = VALUES(metadata)`,
		obj.ID, obj.Type, obj.Name, obj.ParentID, obj.ContainingArea, spatial, obj.Status, normalizeDatetimeForMySQL(obj.UpdatedAt), obj.DataQuality, metadata)
	return err
}

func (m *AgriculturalObjectMapper) UpsertRelation(rel vo.AgriculturalObjectRelationVo) error {
	if db == nil {
		return fmt.Errorf("database is not initialized")
	}
	metadata, err := marshalJSONMap(rel.Metadata)
	if err != nil {
		return err
	}
	_, err = db.Exec(`INSERT INTO agricultural_object_relation
		(sourceObjectId, relationType, targetObjectId, targetType, targetLabel, metadata)
		VALUES (?, ?, ?, ?, ?, CAST(? AS JSON))
		ON DUPLICATE KEY UPDATE
			targetType = VALUES(targetType),
			targetLabel = VALUES(targetLabel),
			metadata = VALUES(metadata)`,
		rel.SourceObjectID, rel.RelationType, rel.TargetObjectID, rel.TargetType, rel.TargetLabel, metadata)
	return err
}

func (m *AgriculturalObjectMapper) FindByID(objectID string) (*vo.AgriculturalObjectVo, error) {
	if db == nil {
		return nil, fmt.Errorf("database is not initialized")
	}
	var record AgriculturalObjectRecord
	err := db.Get(&record, `SELECT `+agriculturalObjectSelectColumns()+`
		FROM agricultural_object WHERE objectId = ?`, objectID)
	if err != nil {
		return nil, err
	}
	obj, err := objectRecordToVO(record)
	if err != nil {
		return nil, err
	}
	return &obj, nil
}

func (m *AgriculturalObjectMapper) FindByType(objectType string) ([]vo.AgriculturalObjectVo, error) {
	if db == nil {
		return nil, fmt.Errorf("database is not initialized")
	}
	var records []AgriculturalObjectRecord
	err := db.Select(&records, `SELECT `+agriculturalObjectSelectColumns()+`
		FROM agricultural_object WHERE objectType = ? ORDER BY objectId`, objectType)
	if err != nil {
		return nil, err
	}
	return objectRecordsToVO(records)
}

func (m *AgriculturalObjectMapper) ListObjects() ([]vo.AgriculturalObjectVo, error) {
	if db == nil {
		return nil, fmt.Errorf("database is not initialized")
	}
	var records []AgriculturalObjectRecord
	err := db.Select(&records, `SELECT `+agriculturalObjectSelectColumns()+`
		FROM agricultural_object ORDER BY objectType, objectId`)
	if err != nil {
		return nil, err
	}
	return objectRecordsToVO(records)
}

func (m *AgriculturalObjectMapper) FindRelations(objectID string, relationTypes []string) ([]vo.AgriculturalObjectRelationVo, error) {
	if db == nil {
		return nil, fmt.Errorf("database is not initialized")
	}
	args := []interface{}{objectID}
	query := `SELECT id, sourceObjectId, relationType, targetObjectId, targetType, targetLabel,
		COALESCE(CAST(metadata AS CHAR), '{}') AS metadata
		FROM agricultural_object_relation WHERE sourceObjectId = ?`
	if len(relationTypes) > 0 {
		query += " AND relationType IN ("
		for i, relationType := range relationTypes {
			if i > 0 {
				query += ","
			}
			query += "?"
			args = append(args, relationType)
		}
		query += ")"
	}
	query += " ORDER BY relationType, targetObjectId, targetLabel"

	var records []AgriculturalRelationRecord
	if err := db.Select(&records, query, args...); err != nil {
		return nil, err
	}
	return relationRecordsToVO(records)
}

func (m *AgriculturalObjectMapper) FindChildren(parentID string) ([]vo.AgriculturalObjectVo, error) {
	if db == nil {
		return nil, fmt.Errorf("database is not initialized")
	}
	var records []AgriculturalObjectRecord
	err := db.Select(&records, `SELECT `+agriculturalObjectSelectColumns()+`
		FROM agricultural_object WHERE parentId = ? ORDER BY objectType, objectId`, parentID)
	if err != nil {
		return nil, err
	}
	return objectRecordsToVO(records)
}

func (m *AgriculturalObjectMapper) CountObjects() (int, error) {
	if db == nil {
		return 0, fmt.Errorf("database is not initialized")
	}
	var count int
	if err := db.Get(&count, "SELECT COUNT(*) FROM agricultural_object"); err != nil {
		return 0, err
	}
	return count, nil
}

func IsNotFound(err error) bool {
	return errors.Is(err, sql.ErrNoRows)
}

func agriculturalObjectSelectColumns() string {
	return "objectId, objectType, name, parentId, containingArea, " +
		"COALESCE(CAST(`spatial` AS CHAR), '{}') AS `spatial`, " +
		"status, DATE_FORMAT(updatedAt, '%Y-%m-%dT%H:%i:%sZ') AS updatedAt, " +
		"dataQuality, COALESCE(CAST(metadata AS CHAR), '{}') AS metadata"
}

func normalizeDatetimeForMySQL(value string) string {
	if parsed, err := time.Parse(time.RFC3339, value); err == nil {
		return parsed.UTC().Format("2006-01-02 15:04:05")
	}
	return value
}

func marshalJSONMap(value map[string]interface{}) (string, error) {
	if value == nil {
		return "{}", nil
	}
	data, err := json.Marshal(value)
	if err != nil {
		return "", err
	}
	return string(data), nil
}

func parseJSONMap(raw string) (map[string]interface{}, error) {
	if raw == "" {
		return map[string]interface{}{}, nil
	}
	var value map[string]interface{}
	if err := json.Unmarshal([]byte(raw), &value); err != nil {
		return nil, err
	}
	if value == nil {
		value = map[string]interface{}{}
	}
	return value, nil
}

func objectRecordToVO(record AgriculturalObjectRecord) (vo.AgriculturalObjectVo, error) {
	spatial, err := parseJSONMap(record.Spatial)
	if err != nil {
		return vo.AgriculturalObjectVo{}, err
	}
	metadata, err := parseJSONMap(record.Metadata)
	if err != nil {
		return vo.AgriculturalObjectVo{}, err
	}
	updatedAt := record.UpdatedAt
	if _, err := time.Parse(time.RFC3339, updatedAt); err != nil {
		updatedAt = record.UpdatedAt
	}
	return vo.AgriculturalObjectVo{
		ID:             record.ObjectID,
		Type:           record.ObjectType,
		Name:           record.Name,
		ParentID:       record.ParentID,
		ContainingArea: record.ContainingArea,
		Spatial:        spatial,
		Status:         record.Status,
		UpdatedAt:      updatedAt,
		DataQuality:    record.DataQuality,
		Metadata:       metadata,
	}, nil
}

func objectRecordsToVO(records []AgriculturalObjectRecord) ([]vo.AgriculturalObjectVo, error) {
	objects := make([]vo.AgriculturalObjectVo, 0, len(records))
	for _, record := range records {
		obj, err := objectRecordToVO(record)
		if err != nil {
			return nil, err
		}
		objects = append(objects, obj)
	}
	return objects, nil
}

func relationRecordsToVO(records []AgriculturalRelationRecord) ([]vo.AgriculturalObjectRelationVo, error) {
	relations := make([]vo.AgriculturalObjectRelationVo, 0, len(records))
	for _, record := range records {
		metadata, err := parseJSONMap(record.Metadata)
		if err != nil {
			return nil, err
		}
		relations = append(relations, vo.AgriculturalObjectRelationVo{
			ID:             record.ID,
			SourceObjectID: record.SourceObjectID,
			RelationType:   record.RelationType,
			TargetObjectID: record.TargetObjectID,
			TargetType:     record.TargetType,
			TargetLabel:    record.TargetLabel,
			Metadata:       metadata,
		})
	}
	return relations, nil
}
