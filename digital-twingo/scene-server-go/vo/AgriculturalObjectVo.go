package vo

type AgriculturalObjectType string

const (
	ObjectTypeFarm        AgriculturalObjectType = "Farm"
	ObjectTypeGreenhouse  AgriculturalObjectType = "Greenhouse"
	ObjectTypeParcel      AgriculturalObjectType = "Parcel"
	ObjectTypeCropRow     AgriculturalObjectType = "CropRow"
	ObjectTypePlant       AgriculturalObjectType = "Plant"
	ObjectTypeCropBatch   AgriculturalObjectType = "CropBatch"
	ObjectTypeSensor      AgriculturalObjectType = "Sensor"
	ObjectTypeDevice      AgriculturalObjectType = "Device"
	ObjectTypeCamera      AgriculturalObjectType = "Camera"
	ObjectTypeOperation   AgriculturalObjectType = "Operation"
	ObjectTypeObservation AgriculturalObjectType = "Observation"
)

type DataQualityStatus string

const (
	DataQualityReal      DataQualityStatus = "real"
	DataQualitySimulated DataQualityStatus = "simulated"
	DataQualityStale     DataQualityStatus = "stale"
	DataQualityMissing   DataQualityStatus = "missing"
)

type AgriculturalRelationType string

const (
	RelationTypeParent      AgriculturalRelationType = "parent"
	RelationTypeContains    AgriculturalRelationType = "contains"
	RelationTypeDevice      AgriculturalRelationType = "device"
	RelationTypeSensor      AgriculturalRelationType = "sensor"
	RelationTypeCamera      AgriculturalRelationType = "camera"
	RelationTypeCropBatch   AgriculturalRelationType = "crop_batch"
	RelationTypeKeyPlant    AgriculturalRelationType = "key_plant"
	RelationTypeMetric      AgriculturalRelationType = "metric"
	RelationTypeEvent       AgriculturalRelationType = "event"
	RelationTypeAsset       AgriculturalRelationType = "asset"
	RelationTypeObservation AgriculturalRelationType = "observation"
)

type AgriculturalObjectVo struct {
	ID             string                 `json:"id" db:"objectId"`
	Type           string                 `json:"type" db:"objectType"`
	Name           string                 `json:"name" db:"name"`
	ParentID       string                 `json:"parentId" db:"parentId"`
	ContainingArea string                 `json:"containingArea" db:"containingArea"`
	Spatial        map[string]interface{} `json:"spatial" db:"-"`
	Status         string                 `json:"status" db:"status"`
	UpdatedAt      string                 `json:"updatedAt" db:"updatedAt"`
	DataQuality    string                 `json:"dataQuality" db:"dataQuality"`
	Metadata       map[string]interface{} `json:"metadata" db:"-"`
}

type AgriculturalObjectRelationVo struct {
	ID             int64                  `json:"id" db:"id"`
	SourceObjectID string                 `json:"sourceObjectId" db:"sourceObjectId"`
	RelationType   string                 `json:"relationType" db:"relationType"`
	TargetObjectID string                 `json:"targetObjectId" db:"targetObjectId"`
	TargetType     string                 `json:"targetType" db:"targetType"`
	TargetLabel    string                 `json:"targetLabel" db:"targetLabel"`
	Metadata       map[string]interface{} `json:"metadata" db:"-"`
}

type ObjectLookupRequest struct {
	ObjectID string `json:"objectId"`
	Type     string `json:"type"`
}

type ObjectLookupResponse struct {
	Code    int                    `json:"code"`
	Error   string                 `json:"error,omitempty"`
	Object  *AgriculturalObjectVo  `json:"object,omitempty"`
	Objects []AgriculturalObjectVo `json:"objects,omitempty"`
}

type ObjectRelationsRequest struct {
	ObjectID      string   `json:"objectId"`
	RelationTypes []string `json:"relationTypes,omitempty"`
}

type RelatedObjectVo struct {
	RelationType string                 `json:"relationType"`
	TargetID     string                 `json:"targetId"`
	TargetType   string                 `json:"targetType"`
	TargetLabel  string                 `json:"targetLabel"`
	Object       *AgriculturalObjectVo  `json:"object,omitempty"`
	Metadata     map[string]interface{} `json:"metadata"`
}

type ObjectRelationsResponse struct {
	Code      int                          `json:"code"`
	Error     string                       `json:"error,omitempty"`
	ObjectID  string                       `json:"objectId"`
	Object    *AgriculturalObjectVo        `json:"object,omitempty"`
	Parent    *AgriculturalObjectVo        `json:"parent,omitempty"`
	Relations map[string][]RelatedObjectVo `json:"relations"`
}
