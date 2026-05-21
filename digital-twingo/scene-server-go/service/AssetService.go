package service

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"scene-server-go/config"
	"scene-server-go/mapper"
	"scene-server-go/vo"
)

const (
	pythonServiceURL = "http://127.0.0.1:9020"
	sceneAssetsDir   = "scene-assets"
)

type AssetService struct {
	assetMapper *mapper.AssetMapper
}

func NewAssetService() *AssetService {
	return &AssetService{
		assetMapper: mapper.NewAssetMapper(),
	}
}

// InitDB ensures the asset_jobs table exists.
func (s *AssetService) InitDB() error {
	return s.assetMapper.CreateTable()
}

// CreateJob saves the uploaded image, calls Python service, and stores the job.
func (s *AssetService) CreateJob(req *vo.AssetJobRequest) (*vo.AssetJobResponse, error) {
	// Decode image
	imgData, err := base64.StdEncoding.DecodeString(req.ImageBase64)
	if err != nil {
		return nil, fmt.Errorf("invalid image base64: %w", err)
	}

	// Set defaults
	if req.Resolution == 0 {
		req.Resolution = 512
	}
	if req.DecimationTarget == 0 {
		req.DecimationTarget = 300000
	}
	if req.TextureSize == 0 {
		req.TextureSize = 2048
	}

	// Forward to Python service (it generates its own job_id)
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)
	part, _ := writer.CreateFormFile("image", req.ImageFileName)
	part.Write(imgData)
	writer.WriteField("resolution", fmt.Sprintf("%d", req.Resolution))
	writer.WriteField("decimation_target", fmt.Sprintf("%d", req.DecimationTarget))
	writer.WriteField("texture_size", fmt.Sprintf("%d", req.TextureSize))
	writer.Close()

	resp, err := http.Post(pythonServiceURL+"/generate", writer.FormDataContentType(), body)
	if err != nil {
		return nil, fmt.Errorf("python service unreachable: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		errBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("python service error %d: %s", resp.StatusCode, string(errBody))
	}

	var pyResp struct {
		JobID  string `json:"job_id"`
		Status string `json:"status"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&pyResp); err != nil {
		return nil, fmt.Errorf("failed to parse python response: %w", err)
	}

	// Save uploaded image using python's job_id as filename
	sourceDir := filepath.Join(sceneAssetsDir, "sources")
	os.MkdirAll(sourceDir, 0755)

	imgExt := ".png"
	if strings.HasSuffix(strings.ToLower(req.ImageFileName), ".jpg") ||
		strings.HasSuffix(strings.ToLower(req.ImageFileName), ".jpeg") {
		imgExt = ".jpg"
	}
	sourceImagePath := filepath.Join(sourceDir, pyResp.JobID+imgExt)
	os.WriteFile(sourceImagePath, imgData, 0644)

	// Store job in DB using Python's job_id
	record := &mapper.AssetJobRecord{
		JobID:                pyResp.JobID,
		OwnerKey:             req.OwnerKey,
		AssetKey:             req.AssetKey,
		AssetName:            req.AssetName,
		Prompt:               req.Prompt,
		ReferenceImageSource: req.ReferenceImageSource,
		Status:               "queued",
		Progress:             0,
		Resolution:           req.Resolution,
		DecimationTarget:     req.DecimationTarget,
		TextureSize:          req.TextureSize,
		SourceImageURL:       "/" + sourceImagePath,
	}
	s.assetMapper.Insert(record)
	config.Log("INFO", "[Asset] Job %s created by %s (resolution=%d, size=%d bytes)",
		pyResp.JobID, req.OwnerKey, req.Resolution, len(imgData))

	return &vo.AssetJobResponse{
		JobID:                pyResp.JobID,
		OwnerKey:             req.OwnerKey,
		AssetKey:             req.AssetKey,
		AssetName:            req.AssetName,
		Prompt:               req.Prompt,
		ReferenceImageSource: req.ReferenceImageSource,
		Status:               "queued",
	}, nil
}

// GetJob fetches job status, polling Python service if still running.
func (s *AssetService) GetJob(jobID string) (*vo.AssetJobResponse, error) {
	job, err := s.assetMapper.GetByID(jobID)
	if err != nil {
		return nil, fmt.Errorf("job not found: %s", jobID)
	}

	// If job is still queued or running, check Python service for updates
	if job.Status == "queued" || job.Status == "running" {
		pyStatus, err := s.pollPythonStatus(jobID)
		if err == nil {
			if pyStatus.Status == "completed" {
				s.assetMapper.UpdateStatus(jobID, "completed", 100,
					pyStatus.Result.GlbURL, pyStatus.Result.ThumbURL, pyStatus.Result.FileSize, "")
				job.Status = "completed"
				job.ModelURL = pyStatus.Result.GlbURL
				job.ThumbURL = pyStatus.Result.ThumbURL
				job.FileSize = pyStatus.Result.FileSize
				job.Progress = 100
			} else if pyStatus.Status == "failed" {
				s.assetMapper.UpdateStatus(jobID, "failed", 0, "", "", 0, pyStatus.Error)
				job.Status = "failed"
				job.ErrorMsg = pyStatus.Error
			} else {
				job.Status = pyStatus.Status
				job.Progress = pyStatus.Progress
			}
		}
	}

	return jobToResponse(job), nil
}

// ListJobs returns all jobs for a given owner.
func (s *AssetService) ListJobs(ownerKey string) ([]vo.AssetJobResponse, error) {
	jobs, err := s.assetMapper.ListByOwner(ownerKey)
	if err != nil {
		return nil, err
	}
	result := make([]vo.AssetJobResponse, len(jobs))
	for i, j := range jobs {
		result[i] = *jobToResponse(&j)
	}
	return result, nil
}

// ApproveJob approves an asset and optionally renames it.
func (s *AssetService) ApproveJob(jobID, modelName string) error {
	if modelName == "" {
		modelName = "AI Generated Asset"
	}
	return s.assetMapper.ApproveJob(jobID, modelName)
}

// RejectJob rejects an asset.
func (s *AssetService) RejectJob(jobID string) error {
	return s.assetMapper.RejectJob(jobID)
}

type pyStatusResp struct {
	JobID    string `json:"job_id"`
	Status   string `json:"status"`
	Progress int    `json:"progress"`
	Error    string `json:"error"`
	Result   *struct {
		GlbURL   string `json:"glb_url"`
		ThumbURL string `json:"thumb_url"`
		FileSize int64  `json:"file_size"`
	} `json:"result,omitempty"`
}

func (s *AssetService) pollPythonStatus(jobID string) (*pyStatusResp, error) {
	resp, err := http.Get(pythonServiceURL + "/status/" + jobID)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var status pyStatusResp
	if err := json.NewDecoder(resp.Body).Decode(&status); err != nil {
		return nil, err
	}
	return &status, nil
}

func jobToResponse(job *mapper.AssetJobRecord) *vo.AssetJobResponse {
	return &vo.AssetJobResponse{
		JobID:                job.JobID,
		OwnerKey:             job.OwnerKey,
		AssetKey:             job.AssetKey,
		AssetName:            job.AssetName,
		Prompt:               job.Prompt,
		ReferenceImageSource: job.ReferenceImageSource,
		Status:               job.Status,
		Progress:             job.Progress,
		Resolution:           job.Resolution,
		DecimationTarget:     job.DecimationTarget,
		TextureSize:          job.TextureSize,
		ModelName:            job.ModelName,
		ModelURL:             job.ModelURL,
		ThumbURL:             job.ThumbURL,
		SourceImageURL:       job.SourceImageURL,
		FileSize:             job.FileSize,
		ErrorMsg:             job.ErrorMsg,
		CreatedAt:            job.CreatedAt.Format("2006-01-02 15:04:05"),
		UpdatedAt:            job.UpdatedAt.Format("2006-01-02 15:04:05"),
	}
}
