package mapper

import (
	"time"
)

// AssetJobRecord is a row in the asset_jobs table.
type AssetJobRecord struct {
	JobID            string    `db:"jobId"`
	OwnerKey         string    `db:"ownerKey"`
	Status           string    `db:"status"`
	Progress         int       `db:"progress"`
	Resolution       int       `db:"resolution"`
	DecimationTarget int       `db:"decimationTarget"`
	TextureSize      int       `db:"textureSize"`
	ModelName        string    `db:"modelName"`
	ModelURL         string    `db:"modelUrl"`
	ThumbURL         string    `db:"thumbUrl"`
	SourceImageURL   string    `db:"sourceImageUrl"`
	FileSize         int64     `db:"fileSize"`
	ErrorMsg         string    `db:"errorMsg"`
	CreatedAt        time.Time `db:"createdAt"`
	UpdatedAt        time.Time `db:"updatedAt"`
}

// AssetMapper provides database operations for the asset_jobs table.
type AssetMapper struct{}

func NewAssetMapper() *AssetMapper {
	return &AssetMapper{}
}

func (m *AssetMapper) CreateTable() error {
	_, err := db.Exec(`CREATE TABLE IF NOT EXISTS asset_jobs (
		jobId VARCHAR(32) NOT NULL,
		ownerKey VARCHAR(64) DEFAULT '',
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
		INDEX idx_status (status)
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`)
	return err
}

func (m *AssetMapper) Insert(job *AssetJobRecord) error {
	_, err := db.Exec(`INSERT INTO asset_jobs
		(jobId, ownerKey, status, progress, resolution, decimationTarget, textureSize,
		 modelName, modelUrl, thumbUrl, sourceImageUrl, fileSize, errorMsg)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		job.JobID, job.OwnerKey, job.Status, job.Progress, job.Resolution,
		job.DecimationTarget, job.TextureSize, job.ModelName, job.ModelURL,
		job.ThumbURL, job.SourceImageURL, job.FileSize, job.ErrorMsg)
	return err
}

func (m *AssetMapper) UpdateStatus(jobID, status string, progress int, modelURL, thumbURL string, fileSize int64, errorMsg string) error {
	_, err := db.Exec(`UPDATE asset_jobs SET status=?, progress=?, modelUrl=?, thumbUrl=?, fileSize=?, errorMsg=?, updatedAt=NOW()
		WHERE jobId=?`,
		status, progress, modelURL, thumbURL, fileSize, errorMsg, jobID)
	return err
}

func (m *AssetMapper) ApproveJob(jobID, modelName string) error {
	_, err := db.Exec(`UPDATE asset_jobs SET status='approved', modelName=?, updatedAt=NOW() WHERE jobId=?`,
		modelName, jobID)
	return err
}

func (m *AssetMapper) RejectJob(jobID string) error {
	_, err := db.Exec(`UPDATE asset_jobs SET status='rejected', updatedAt=NOW() WHERE jobId=?`, jobID)
	return err
}

func (m *AssetMapper) GetByID(jobID string) (*AssetJobRecord, error) {
	var job AssetJobRecord
	err := db.Get(&job, "SELECT * FROM asset_jobs WHERE jobId=?", jobID)
	if err != nil {
		return nil, err
	}
	return &job, nil
}

func (m *AssetMapper) ListByOwner(ownerKey string) ([]AssetJobRecord, error) {
	var jobs []AssetJobRecord
	err := db.Select(&jobs, "SELECT * FROM asset_jobs WHERE ownerKey=? ORDER BY createdAt DESC", ownerKey)
	if err != nil {
		return nil, err
	}
	return jobs, nil
}

func (m *AssetMapper) ListApproved() ([]AssetJobRecord, error) {
	var jobs []AssetJobRecord
	err := db.Select(&jobs, "SELECT * FROM asset_jobs WHERE status='approved' ORDER BY createdAt DESC")
	if err != nil {
		return nil, err
	}
	return jobs, nil
}

// ListForModelTree returns approved jobs + jobs owned by the given user.
func (m *AssetMapper) ListForModelTree(ownerKey string) ([]AssetJobRecord, error) {
	var jobs []AssetJobRecord
	err := db.Select(&jobs,
		"SELECT * FROM asset_jobs WHERE status IN ('completed','approved') AND (status='approved' OR ownerKey=?) ORDER BY createdAt DESC",
		ownerKey)
	if err != nil {
		return nil, err
	}
	return jobs, nil
}
