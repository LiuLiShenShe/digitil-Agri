package service

import (
	"strings"

	"scene-server-go/vo"
)

type AssetQualityAuditService struct {
	registry *AssetRegistryService
}

func NewAssetQualityAuditService(registry *AssetRegistryService) *AssetQualityAuditService {
	if registry == nil {
		registry = NewAssetRegistryService()
	}
	return &AssetQualityAuditService{registry: registry}
}

func (s *AssetQualityAuditService) AuditAsset(assetKey string) vo.AssetQualityAuditReportVo {
	assetKey = strings.TrimSpace(assetKey)
	meta, ok := s.registry.Get(assetKey)
	if !ok {
		meta = vo.AssetMetadataVo{AssetKey: assetKey}
	}
	issues := qualityAuditIssues(meta)
	return vo.AssetQualityAuditReportVo{
		AssetKey: assetKey,
		Complete: len(issues) == 0 && meta.MetadataComplete,
		Accepted: len(issues) == 0 && meta.MetadataComplete,
		Metadata: meta,
		Issues:   issues,
	}
}

func (s *AssetQualityAuditService) AuditAll() []vo.AssetQualityAuditReportVo {
	assets := s.registry.List()
	reports := make([]vo.AssetQualityAuditReportVo, 0, len(assets))
	for _, asset := range assets {
		reports = append(reports, s.AuditAsset(asset.AssetKey))
	}
	return reports
}

func qualityAuditIssues(meta vo.AssetMetadataVo) []vo.AssetQualityAuditIssueVo {
	issues := make([]vo.AssetQualityAuditIssueVo, 0)
	if strings.TrimSpace(meta.GLBURL) == "" || !meta.Quality.Loadable {
		issues = append(issues, auditIssue("not_threejs_loadable", "error", "GLB 为空或未通过 Three.js 可加载检查"))
	}
	if strings.TrimSpace(meta.Quality.Axis) == "" {
		issues = append(issues, auditIssue("invalid_axis", "warning", "资产缺少 Y-up 坐标轴检查结果"))
	}
	if meta.Quality.UnitScale <= 0 {
		issues = append(issues, auditIssue("invalid_unit_scale", "warning", "资产缺少单位比例检查结果"))
	}
	if meta.Quality.PolygonCount <= 0 {
		issues = append(issues, auditIssue("missing_quality", "warning", "资产缺少面数、贴图或体积质量信息"))
	}
	if meta.Quality.TextureCount < 0 {
		issues = append(issues, auditIssue("invalid_texture_count", "warning", "资产贴图数量检查结果异常"))
	}
	if meta.Quality.VolumeM3 <= 0 {
		issues = append(issues, auditIssue("missing_quality", "warning", "资产缺少体积质量信息"))
	}
	if strings.TrimSpace(meta.ThumbnailURL) == "" || !meta.Quality.HasThumbnail {
		issues = append(issues, auditIssue("missing_thumbnail", "warning", "资产缺少缩略图"))
	}
	if strings.TrimSpace(meta.Source) == "" || !meta.Quality.HasSource {
		issues = append(issues, auditIssue("missing_source", "warning", "资产缺少来源"))
	}
	if strings.TrimSpace(meta.License) == "" || !meta.Quality.HasLicense {
		issues = append(issues, auditIssue("missing_license", "warning", "资产缺少许可信息"))
	}
	return uniqueAuditIssues(issues)
}

func auditIssue(code string, severity string, message string) vo.AssetQualityAuditIssueVo {
	return vo.AssetQualityAuditIssueVo{Code: code, Severity: severity, Message: message}
}

func uniqueAuditIssues(items []vo.AssetQualityAuditIssueVo) []vo.AssetQualityAuditIssueVo {
	seen := map[string]bool{}
	result := make([]vo.AssetQualityAuditIssueVo, 0, len(items))
	for _, item := range items {
		if seen[item.Code] {
			continue
		}
		seen[item.Code] = true
		result = append(result, item)
	}
	return result
}
