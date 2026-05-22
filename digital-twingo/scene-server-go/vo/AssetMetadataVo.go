package vo

type AssetMetadataVo struct {
	AssetKey              string             `json:"assetKey"`
	Name                  string             `json:"name"`
	Aliases               []string           `json:"aliases,omitempty"`
	Category              string             `json:"category"`
	Source                string             `json:"source"`
	License               string             `json:"license"`
	FidelityLevel         string             `json:"fidelityLevel"`
	ThumbnailURL          string             `json:"thumbnailUrl"`
	GLBURL                string             `json:"glbUrl"`
	ApplicableObjectTypes []string           `json:"applicableObjectTypes"`
	Quality               AssetQualityInfoVo `json:"quality"`
	Version               AssetVersionInfoVo `json:"version"`
	MetadataComplete      bool               `json:"metadataComplete"`
	DefaultScale          float64            `json:"defaultScale,omitempty"`
	Footprint             FootprintVo        `json:"footprint,omitempty"`
	LayoutRules           []string           `json:"layoutRules,omitempty"`
}

type AssetQualityInfoVo struct {
	Loadable      bool     `json:"loadable"`
	Axis          string   `json:"axis"`
	UnitScale     float64  `json:"unitScale"`
	Center        OffsetVo `json:"center"`
	PolygonCount  int      `json:"polygonCount"`
	TextureCount  int      `json:"textureCount"`
	VolumeM3      float64  `json:"volumeM3"`
	HasThumbnail  bool     `json:"hasThumbnail"`
	HasSource     bool     `json:"hasSource"`
	HasLicense    bool     `json:"hasLicense"`
	LOD           string   `json:"lod,omitempty"`
	QualityStatus string   `json:"qualityStatus"`
	Issues        []string `json:"issues,omitempty"`
}

type AssetVersionInfoVo struct {
	Version   string `json:"version"`
	Revision  string `json:"revision,omitempty"`
	UpdatedAt string `json:"updatedAt"`
	Stage     string `json:"stage,omitempty"`
}

type AssetQualityAuditIssueVo struct {
	Code     string `json:"code"`
	Severity string `json:"severity"`
	Message  string `json:"message"`
}

type AssetQualityAuditReportVo struct {
	AssetKey string                     `json:"assetKey"`
	Complete bool                       `json:"complete"`
	Accepted bool                       `json:"accepted"`
	Metadata AssetMetadataVo            `json:"metadata"`
	Issues   []AssetQualityAuditIssueVo `json:"issues"`
}

type AssetFidelityRoutingRequest struct {
	AssetKey         string `json:"assetKey"`
	ObjectType       string `json:"objectType"`
	BusinessValue    string `json:"businessValue,omitempty"`
	RequiredFidelity string `json:"requiredFidelity,omitempty"`
	IsKeyPlant       bool   `json:"isKeyPlant,omitempty"`
	IsAbnormalPlant  bool   `json:"isAbnormalPlant,omitempty"`
	IsResearchSample bool   `json:"isResearchSample,omitempty"`
	MaxWaitMinutes   int    `json:"maxWaitMinutes,omitempty"`
}

type AssetFidelityRoutingDecisionVo struct {
	AssetKey               string `json:"assetKey"`
	ObjectType             string `json:"objectType"`
	Strategy               string `json:"strategy"`
	SelectedAssetKey       string `json:"selectedAssetKey,omitempty"`
	SelectedURL            string `json:"selectedUrl,omitempty"`
	FidelityLevel          string `json:"fidelityLevel"`
	RoutingReason          string `json:"routingReason"`
	RequiresGenerationTask bool   `json:"requiresGenerationTask"`
	PlaceholderAssetKey    string `json:"placeholderAssetKey,omitempty"`
	GenerationMode         string `json:"generationMode,omitempty"`
	ReferenceImageRequired bool   `json:"referenceImageRequired,omitempty"`
}

type PlantGeometryVersionVo struct {
	ObjectID         string                  `json:"objectId"`
	Stage            string                  `json:"stage"`
	StageLabel       string                  `json:"stageLabel"`
	AssetKey         string                  `json:"assetKey"`
	GLBURL           string                  `json:"glbUrl"`
	ThumbnailURL     string                  `json:"thumbnailUrl,omitempty"`
	FidelityLevel    string                  `json:"fidelityLevel"`
	Version          string                  `json:"version"`
	CreatedAt        string                  `json:"createdAt"`
	PhenotypeBinding PlantPhenotypeBindingVo `json:"phenotypeBinding"`
}

type PlantPhenotypeBindingVo struct {
	ObjectID  string `json:"objectId"`
	MetricKey string `json:"metricKey"`
	Source    string `json:"source"`
}
