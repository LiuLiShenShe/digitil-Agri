package vo

// AssetJobRequest is the request to create a new asset generation job.
type AssetJobRequest struct {
	ImageBase64       string `json:"imageBase64"`
	ImageFileName     string `json:"imageFileName"`
	OwnerKey          string `json:"ownerKey"`
	Resolution        int    `json:"resolution"`        // 512 or 1024
	DecimationTarget  int    `json:"decimationTarget"`  // e.g. 300000
	TextureSize       int    `json:"textureSize"`       // e.g. 2048
}

// AssetJobResponse is returned when querying a job.
type AssetJobResponse struct {
	JobID             string `json:"jobId"`
	OwnerKey          string `json:"ownerKey"`
	Status            string `json:"status"`            // queued, running, completed, failed
	Progress          int    `json:"progress"`
	Resolution        int    `json:"resolution"`
	DecimationTarget  int    `json:"decimationTarget"`
	TextureSize       int    `json:"textureSize"`
	ModelName         string `json:"modelName"`
	ModelURL          string `json:"modelUrl"`
	ThumbURL          string `json:"thumbUrl"`
	SourceImageURL    string `json:"sourceImageUrl"`
	FileSize          int64  `json:"fileSize"`
	ErrorMsg          string `json:"errorMsg"`
	CreatedAt         string `json:"createdAt"`
	UpdatedAt         string `json:"updatedAt"`
}

// AssetApproveRequest approves or rejects a generated asset.
type AssetApproveRequest struct {
	JobID    string `json:"jobId"`
	Action   string `json:"action"`   // "approve" or "reject"
	ModelName string `json:"modelName"` // optional new name for approved model
	ParentID int    `json:"parentId"`  // parent category id in model tree
}
