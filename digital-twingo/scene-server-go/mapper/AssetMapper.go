package mapper

import (
	"fmt"
	"time"
)

// AssetJobRecord is a row in the asset_jobs table.
type AssetJobRecord struct {
	JobID                string    `db:"jobId"`
	OwnerKey             string    `db:"ownerKey"`
	AssetKey             string    `db:"assetKey"`
	AssetName            string    `db:"assetName"`
	Prompt               string    `db:"prompt"`
	ReferenceImageSource string    `db:"referenceImageSource"`
	Status               string    `db:"status"`
	Progress             int       `db:"progress"`
	Resolution           int       `db:"resolution"`
	DecimationTarget     int       `db:"decimationTarget"`
	TextureSize          int       `db:"textureSize"`
	ModelName            string    `db:"modelName"`
	ModelURL             string    `db:"modelUrl"`
	ThumbURL             string    `db:"thumbUrl"`
	SourceImageURL       string    `db:"sourceImageUrl"`
	FileSize             int64     `db:"fileSize"`
	ErrorMsg             string    `db:"errorMsg"`
	CreatedAt            time.Time `db:"createdAt"`
	UpdatedAt            time.Time `db:"updatedAt"`
}

// AssetMapper provides database operations for the asset_jobs table.
type AssetMapper struct{}

const assetJobSelectColumns = `
	jobId,
	COALESCE(ownerKey, '') AS ownerKey,
	COALESCE(assetKey, '') AS assetKey,
	COALESCE(assetName, '') AS assetName,
	COALESCE(prompt, '') AS prompt,
	COALESCE(referenceImageSource, '') AS referenceImageSource,
	COALESCE(status, '') AS status,
	COALESCE(progress, 0) AS progress,
	COALESCE(resolution, 512) AS resolution,
	COALESCE(decimationTarget, 300000) AS decimationTarget,
	COALESCE(textureSize, 2048) AS textureSize,
	COALESCE(modelName, '') AS modelName,
	COALESCE(modelUrl, '') AS modelUrl,
	COALESCE(thumbUrl, '') AS thumbUrl,
	COALESCE(sourceImageUrl, '') AS sourceImageUrl,
	COALESCE(fileSize, 0) AS fileSize,
	COALESCE(errorMsg, '') AS errorMsg,
	createdAt,
	updatedAt`

func NewAssetMapper() *AssetMapper {
	return &AssetMapper{}
}

func (m *AssetMapper) CreateTable() error {
	if db == nil {
		return fmt.Errorf("database is not initialized")
	}
	_, err := db.Exec(`CREATE TABLE IF NOT EXISTS asset_jobs (
		jobId VARCHAR(32) NOT NULL,
		ownerKey VARCHAR(64) DEFAULT '',
		assetKey VARCHAR(128) DEFAULT '',
		assetName VARCHAR(128) DEFAULT '',
		prompt TEXT,
		referenceImageSource VARCHAR(32) DEFAULT '',
		status VARCHAR(16) DEFAULT 'queued',
		progress INT DEFAULT 0,
		resolution INT DEFAULT 512,
		decimationTarget INT DEFAULT 300000,
		textureSize INT DEFAULT 2048,
		modelName VARCHAR(128) DEFAULT '',
		modelUrl VARCHAR(512) DEFAULT '',
		thumbUrl VARCHAR(512) DEFAULT '',
		sourceImageUrl VARCHAR(512) DEFAULT '',
		fileSize BIGINT DEFAULT 0,
		errorMsg TEXT,
		createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
		updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
		PRIMARY KEY (jobId),
		INDEX idx_ownerKey (ownerKey),
		INDEX idx_assetKey (assetKey),
		INDEX idx_status (status)
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`)
	if err != nil {
		return err
	}
	migrations := []struct {
		name string
		ddl  string
	}{
		{name: "assetKey", ddl: "ALTER TABLE asset_jobs ADD COLUMN assetKey VARCHAR(128) DEFAULT '' AFTER ownerKey"},
		{name: "assetName", ddl: "ALTER TABLE asset_jobs ADD COLUMN assetName VARCHAR(128) DEFAULT '' AFTER assetKey"},
		{name: "prompt", ddl: "ALTER TABLE asset_jobs ADD COLUMN prompt TEXT AFTER assetName"},
		{name: "referenceImageSource", ddl: "ALTER TABLE asset_jobs ADD COLUMN referenceImageSource VARCHAR(32) DEFAULT '' AFTER prompt"},
	}
	for _, migration := range migrations {
		if err := m.ensureColumn(migration.name, migration.ddl); err != nil {
			return err
		}
	}
	if err := m.ensureIndex("idx_assetKey", "ALTER TABLE asset_jobs ADD INDEX idx_assetKey (assetKey)"); err != nil {
		return err
	}
	return nil
}

func (m *AssetMapper) ensureColumn(name string, ddl string) error {
	var count int
	err := db.Get(&count, `SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
		WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'asset_jobs' AND COLUMN_NAME = ?`, name)
	if err != nil {
		return err
	}
	if count > 0 {
		return nil
	}
	_, err = db.Exec(ddl)
	return err
}

func (m *AssetMapper) ensureIndex(name string, ddl string) error {
	var count int
	err := db.Get(&count, `SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
		WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'asset_jobs' AND INDEX_NAME = ?`, name)
	if err != nil {
		return err
	}
	if count > 0 {
		return nil
	}
	_, err = db.Exec(ddl)
	return err
}

func (m *AssetMapper) Insert(job *AssetJobRecord) error {
	if db == nil {
		return fmt.Errorf("database is not initialized")
	}
	_, err := db.Exec(`INSERT INTO asset_jobs
		(jobId, ownerKey, assetKey, assetName, prompt, referenceImageSource, status, progress, resolution, decimationTarget, textureSize,
		 modelName, modelUrl, thumbUrl, sourceImageUrl, fileSize, errorMsg)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		job.JobID, job.OwnerKey, job.AssetKey, job.AssetName, job.Prompt, job.ReferenceImageSource, job.Status, job.Progress, job.Resolution,
		job.DecimationTarget, job.TextureSize, job.ModelName, job.ModelURL,
		job.ThumbURL, job.SourceImageURL, job.FileSize, job.ErrorMsg)
	return err
}

func (m *AssetMapper) UpdateStatus(jobID, status string, progress int, modelURL, thumbURL string, fileSize int64, errorMsg string) error {
	if db == nil {
		return fmt.Errorf("database is not initialized")
	}
	_, err := db.Exec(`UPDATE asset_jobs SET status=?, progress=?, modelUrl=?, thumbUrl=?, fileSize=?, errorMsg=?, updatedAt=NOW()
		WHERE jobId=?`,
		status, progress, modelURL, thumbURL, fileSize, errorMsg, jobID)
	return err
}

func (m *AssetMapper) ApproveJob(jobID, modelName string) error {
	if db == nil {
		return fmt.Errorf("database is not initialized")
	}
	_, err := db.Exec(`UPDATE asset_jobs SET status='approved', modelName=?, updatedAt=NOW() WHERE jobId=?`,
		modelName, jobID)
	return err
}

func (m *AssetMapper) RejectJob(jobID string) error {
	if db == nil {
		return fmt.Errorf("database is not initialized")
	}
	_, err := db.Exec(`UPDATE asset_jobs SET status='rejected', updatedAt=NOW() WHERE jobId=?`, jobID)
	return err
}

func (m *AssetMapper) GetByID(jobID string) (*AssetJobRecord, error) {
	if db == nil {
		return nil, fmt.Errorf("database is not initialized")
	}
	var job AssetJobRecord
	err := db.Get(&job, "SELECT "+assetJobSelectColumns+" FROM asset_jobs WHERE jobId=?", jobID)
	if err != nil {
		return nil, err
	}
	return &job, nil
}

func (m *AssetMapper) ListByOwner(ownerKey string) ([]AssetJobRecord, error) {
	if db == nil {
		return nil, fmt.Errorf("database is not initialized")
	}
	var jobs []AssetJobRecord
	err := db.Select(&jobs, "SELECT "+assetJobSelectColumns+" FROM asset_jobs WHERE ownerKey=? ORDER BY createdAt DESC", ownerKey)
	if err != nil {
		return nil, err
	}
	return jobs, nil
}

func (m *AssetMapper) ListApproved() ([]AssetJobRecord, error) {
	if db == nil {
		return nil, fmt.Errorf("database is not initialized")
	}
	var jobs []AssetJobRecord
	err := db.Select(&jobs, "SELECT "+assetJobSelectColumns+" FROM asset_jobs WHERE status='approved' ORDER BY createdAt DESC")
	if err != nil {
		return nil, err
	}
	return jobs, nil
}

// ListForModelTree returns approved jobs + jobs owned by the given user.
func (m *AssetMapper) ListForModelTree(ownerKey string) ([]AssetJobRecord, error) {
	if db == nil {
		return nil, fmt.Errorf("database is not initialized")
	}
	var jobs []AssetJobRecord
	err := db.Select(&jobs,
		"SELECT "+assetJobSelectColumns+" FROM asset_jobs WHERE status IN ('completed','approved') AND (status='approved' OR ownerKey=?) ORDER BY createdAt DESC",
		ownerKey)
	if err != nil {
		return nil, err
	}
	return jobs, nil
}
