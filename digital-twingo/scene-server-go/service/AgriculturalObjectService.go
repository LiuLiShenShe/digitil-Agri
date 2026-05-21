package service

import (
	"fmt"
	"sort"
	"strings"

	"scene-server-go/mapper"
	"scene-server-go/vo"
)

type AgriculturalObjectType = vo.AgriculturalObjectType

const (
	ObjectTypeFarm        = vo.ObjectTypeFarm
	ObjectTypeGreenhouse  = vo.ObjectTypeGreenhouse
	ObjectTypeParcel      = vo.ObjectTypeParcel
	ObjectTypeCropRow     = vo.ObjectTypeCropRow
	ObjectTypePlant       = vo.ObjectTypePlant
	ObjectTypeCropBatch   = vo.ObjectTypeCropBatch
	ObjectTypeSensor      = vo.ObjectTypeSensor
	ObjectTypeDevice      = vo.ObjectTypeDevice
	ObjectTypeCamera      = vo.ObjectTypeCamera
	ObjectTypeOperation   = vo.ObjectTypeOperation
	ObjectTypeObservation = vo.ObjectTypeObservation
)

type DataQualityStatus = vo.DataQualityStatus

const (
	DataQualityReal      = vo.DataQualityReal
	DataQualitySimulated = vo.DataQualitySimulated
	DataQualityStale     = vo.DataQualityStale
	DataQualityMissing   = vo.DataQualityMissing
)

type AgriculturalObjectVo = vo.AgriculturalObjectVo
type AgriculturalObjectRelationVo = vo.AgriculturalObjectRelationVo
type ObjectLookupRequest = vo.ObjectLookupRequest
type ObjectLookupResponse = vo.ObjectLookupResponse
type ObjectRelationsRequest = vo.ObjectRelationsRequest
type ObjectRelationsResponse = vo.ObjectRelationsResponse
type RelatedObjectVo = vo.RelatedObjectVo

type AgriculturalObjectStore interface {
	EnsureSchema() error
	UpsertObject(vo.AgriculturalObjectVo) error
	UpsertRelation(vo.AgriculturalObjectRelationVo) error
	FindByID(string) (*vo.AgriculturalObjectVo, error)
	FindByType(string) ([]vo.AgriculturalObjectVo, error)
	ListObjects() ([]vo.AgriculturalObjectVo, error)
	FindRelations(string, []string) ([]vo.AgriculturalObjectRelationVo, error)
	FindChildren(string) ([]vo.AgriculturalObjectVo, error)
	CountObjects() (int, error)
}

type AgriculturalObjectService struct {
	store AgriculturalObjectStore
}

func NewAgriculturalObjectService() *AgriculturalObjectService {
	return NewAgriculturalObjectServiceWithStore(mapper.NewAgriculturalObjectMapper())
}

func NewAgriculturalObjectServiceWithStore(store AgriculturalObjectStore) *AgriculturalObjectService {
	return &AgriculturalObjectService{store: store}
}

func (s *AgriculturalObjectService) InitDB() error {
	if err := s.store.EnsureSchema(); err != nil {
		return err
	}
	count, err := s.store.CountObjects()
	if err != nil {
		return err
	}
	if count == 0 {
		return s.SeedTomatoGreenhouseMVP()
	}
	return nil
}

func (s *AgriculturalObjectService) SeedTomatoGreenhouseMVP() error {
	for _, obj := range TomatoGreenhouseSeedObjects() {
		if err := s.ValidateObject(obj); err != nil {
			return err
		}
		if err := s.store.UpsertObject(obj); err != nil {
			return err
		}
	}
	for _, rel := range TomatoGreenhouseSeedRelations() {
		if !validRelationTypes[rel.RelationType] {
			return fmt.Errorf("unsupported agricultural relation type: %s", rel.RelationType)
		}
		if err := s.store.UpsertRelation(rel); err != nil {
			return err
		}
	}
	return nil
}

func (s *AgriculturalObjectService) ValidateObject(obj vo.AgriculturalObjectVo) error {
	if obj.ID == "" {
		return fmt.Errorf("agricultural object id is required")
	}
	if !validObjectTypes[obj.Type] {
		return fmt.Errorf("unsupported agricultural object type: %s", obj.Type)
	}
	if obj.Name == "" {
		return fmt.Errorf("agricultural object name is required")
	}
	if obj.Status == "" {
		return fmt.Errorf("agricultural object status is required")
	}
	if obj.UpdatedAt == "" {
		return fmt.Errorf("agricultural object updatedAt is required")
	}
	if !validDataQualityStatuses[obj.DataQuality] {
		return fmt.Errorf("unsupported agricultural object data quality: %s", obj.DataQuality)
	}
	if obj.Metadata == nil {
		return fmt.Errorf("agricultural object metadata is required")
	}
	if obj.Spatial == nil {
		return fmt.Errorf("agricultural object spatial anchor is required")
	}
	return nil
}

func (s *AgriculturalObjectService) Lookup(req vo.ObjectLookupRequest) vo.ObjectLookupResponse {
	if req.ObjectID != "" {
		obj, err := s.store.FindByID(req.ObjectID)
		if err != nil {
			return vo.ObjectLookupResponse{Code: 404, Error: err.Error()}
		}
		normalizeObject(obj)
		return vo.ObjectLookupResponse{Code: 200, Object: obj}
	}

	var (
		objects []vo.AgriculturalObjectVo
		err     error
	)
	if req.Type != "" {
		if !validObjectTypes[req.Type] {
			return vo.ObjectLookupResponse{Code: 400, Error: "unsupported agricultural object type: " + req.Type}
		}
		objects, err = s.store.FindByType(req.Type)
	} else {
		objects, err = s.store.ListObjects()
	}
	if err != nil {
		return vo.ObjectLookupResponse{Code: 999, Error: err.Error()}
	}
	for i := range objects {
		normalizeObject(&objects[i])
	}
	return vo.ObjectLookupResponse{Code: 200, Objects: objects}
}

func (s *AgriculturalObjectService) Relations(req vo.ObjectRelationsRequest) vo.ObjectRelationsResponse {
	if req.ObjectID == "" {
		return vo.ObjectRelationsResponse{Code: 400, Error: "objectId is required", Relations: map[string][]vo.RelatedObjectVo{}}
	}
	if err := validateRequestedRelationTypes(req.RelationTypes); err != nil {
		return vo.ObjectRelationsResponse{Code: 400, Error: err.Error(), ObjectID: req.ObjectID, Relations: map[string][]vo.RelatedObjectVo{}}
	}

	obj, err := s.store.FindByID(req.ObjectID)
	if err != nil {
		return vo.ObjectRelationsResponse{Code: 404, Error: err.Error(), ObjectID: req.ObjectID, Relations: map[string][]vo.RelatedObjectVo{}}
	}
	normalizeObject(obj)

	result := vo.ObjectRelationsResponse{
		Code:      200,
		ObjectID:  req.ObjectID,
		Object:    obj,
		Relations: map[string][]vo.RelatedObjectVo{},
	}

	if obj.ParentID != "" {
		if parent, err := s.store.FindByID(obj.ParentID); err == nil {
			normalizeObject(parent)
			result.Parent = parent
			result.Relations["parents"] = append(result.Relations["parents"], relatedFromObject("parent", parent, nil))
		}
	}

	children, err := s.store.FindChildren(req.ObjectID)
	if err != nil {
		return vo.ObjectRelationsResponse{Code: 999, Error: err.Error(), ObjectID: req.ObjectID, Relations: map[string][]vo.RelatedObjectVo{}}
	}
	for i := range children {
		normalizeObject(&children[i])
		group := relationGroupForObjectType(children[i].Type)
		result.Relations[group] = append(result.Relations[group], relatedFromObject("contains", &children[i], nil))
	}

	relations, err := s.store.FindRelations(req.ObjectID, req.RelationTypes)
	if err != nil {
		return vo.ObjectRelationsResponse{Code: 999, Error: err.Error(), ObjectID: req.ObjectID, Relations: map[string][]vo.RelatedObjectVo{}}
	}
	for _, rel := range relations {
		group := relationGroupForRelation(rel)
		related := vo.RelatedObjectVo{
			RelationType: rel.RelationType,
			TargetID:     rel.TargetObjectID,
			TargetType:   rel.TargetType,
			TargetLabel:  rel.TargetLabel,
			Metadata:     rel.Metadata,
		}
		if rel.TargetObjectID != "" {
			if target, err := s.store.FindByID(rel.TargetObjectID); err == nil {
				normalizeObject(target)
				related.Object = target
				if related.TargetType == "" {
					related.TargetType = target.Type
				}
				if related.TargetLabel == "" {
					related.TargetLabel = target.Name
				}
			}
		}
		result.Relations[group] = append(result.Relations[group], related)
	}

	sortRelationGroups(result.Relations)
	return result
}

func TomatoGreenhouseSeedObjects() []vo.AgriculturalObjectVo {
	updatedAt := "2026-05-21T08:00:00Z"
	objects := []vo.AgriculturalObjectVo{
		seedObject("farm-yupont-demo", ObjectTypeFarm, "智慧农业示范园区", "", "园区", "normal", DataQualityReal, updatedAt, spatial("area", "demo-farm", 0, 0, 0), map[string]interface{}{"mvp": true, "crop": "tomato"}),
		seedObject("gh-tomato-001", ObjectTypeGreenhouse, "番茄一号温室", "farm-yupont-demo", "北区温室", "normal", DataQualitySimulated, updatedAt, spatial("greenhouse", "north-greenhouse", 0, 0, 0), map[string]interface{}{"areaSqm": 480, "structure": "glass", "mvpCore": true}),
		seedObject("parcel-tomato-a", ObjectTypeParcel, "番茄温室 A 区地块", "gh-tomato-001", "番茄一号温室", "normal", DataQualityReal, updatedAt, spatial("parcel", "row-zone-a", -6, 0, 0), map[string]interface{}{"soil": "loam", "beds": 1}),
		seedObject("row-tomato-a01", ObjectTypeCropRow, "A01 番茄种植行", "parcel-tomato-a", "A 区地块", "normal", DataQualitySimulated, updatedAt, spatial("crop_row", "A01", -6, 0, 0), map[string]interface{}{"plantCount": 20, "spacingCm": 45}),
		seedObject("batch-tomato-2026-spring", ObjectTypeCropBatch, "2026 春茬番茄批次", "gh-tomato-001", "番茄一号温室", "growing", DataQualityStale, updatedAt, spatial("batch", "A01", -6, 0, 0), map[string]interface{}{"cultivar": "粉果番茄", "stage": "flowering"}),
		seedObject("sensor-greenhouse-001", ObjectTypeSensor, "温室环境传感器组", "gh-tomato-001", "温室中部", "online", DataQualitySimulated, updatedAt, spatial("sensor", "center", 0, 2.4, 0), map[string]interface{}{"metrics": []string{"temperature", "humidity", "co2", "lightIntensity", "soilMoisture", "ph"}}),
		seedObject("device-irrigation-001", ObjectTypeDevice, "水肥一体化水泵", "gh-tomato-001", "温室东侧设备区", "online", DataQualityReal, updatedAt, spatial("device", "east-service", 8, 0, 3), map[string]interface{}{"deviceClass": "irrigation_pump", "controlAllowed": false}),
		seedObject("camera-greenhouse-001", ObjectTypeCamera, "温室入口摄像头", "gh-tomato-001", "温室入口", "offline", DataQualityMissing, updatedAt, spatial("camera", "entrance", 0, 3, -8), map[string]interface{}{"stream": "", "coverage": "entrance"}),
		seedObject("operation-irrigation-001", ObjectTypeOperation, "最近一次灌溉", "gh-tomato-001", "A 区地块", "completed", DataQualityReal, updatedAt, spatial("operation", "A01", -6, 0, 0), map[string]interface{}{"operationType": "irrigation", "durationMin": 18}),
		seedObject("observation-growth-001", ObjectTypeObservation, "关键植株长势观测", "plant-tomato-001", "A01 行", "recorded", DataQualityStale, updatedAt, spatial("observation", "A01-P01", -10.5, 0, -2), map[string]interface{}{"heightCm": 86, "leafColor": "normal"}),
	}
	for i := 1; i <= 20; i++ {
		id := fmt.Sprintf("plant-tomato-%03d", i)
		parentID := "row-tomato-a01"
		x := -10.5 + float64((i-1)%10)
		z := -2.0 + float64((i-1)/10)*4
		metadata := map[string]interface{}{"batchId": "batch-tomato-2026-spring", "index": i}
		if i == 1 || i == 10 || i == 20 {
			metadata["keyPlant"] = true
		}
		quality := DataQualitySimulated
		if i == 20 {
			quality = DataQualityMissing
		}
		objects = append(objects, seedObject(id, ObjectTypePlant, fmt.Sprintf("番茄植株 %02d", i), parentID, "A01 行", "normal", quality, updatedAt, spatial("plant", fmt.Sprintf("A01-P%02d", i), x, 0, z), metadata))
	}
	return objects
}

func TomatoGreenhouseSeedRelations() []vo.AgriculturalObjectRelationVo {
	relations := []vo.AgriculturalObjectRelationVo{
		seedRelation("farm-yupont-demo", "contains", "gh-tomato-001", ObjectTypeGreenhouse, "番茄一号温室", nil),
		seedRelation("gh-tomato-001", "contains", "parcel-tomato-a", ObjectTypeParcel, "番茄温室 A 区地块", nil),
		seedRelation("gh-tomato-001", "contains", "row-tomato-a01", ObjectTypeCropRow, "A01 番茄种植行", nil),
		seedRelation("gh-tomato-001", "crop_batch", "batch-tomato-2026-spring", ObjectTypeCropBatch, "2026 春茬番茄批次", nil),
		seedRelation("gh-tomato-001", "sensor", "sensor-greenhouse-001", ObjectTypeSensor, "温室环境传感器组", nil),
		seedRelation("gh-tomato-001", "device", "device-irrigation-001", ObjectTypeDevice, "水肥一体化水泵", nil),
		seedRelation("gh-tomato-001", "camera", "camera-greenhouse-001", ObjectTypeCamera, "温室入口摄像头", nil),
		seedRelation("gh-tomato-001", "event", "operation-irrigation-001", ObjectTypeOperation, "最近一次灌溉", map[string]interface{}{"eventType": "irrigation"}),
		seedRelation("gh-tomato-001", "observation", "observation-growth-001", ObjectTypeObservation, "关键植株长势观测", nil),
		seedRelation("gh-tomato-001", "metric", "", "", "temperature", map[string]interface{}{"unit": "C", "sourceObjectId": "sensor-greenhouse-001"}),
		seedRelation("gh-tomato-001", "asset", "", "", "greenhouse.glb", map[string]interface{}{"assetKey": "greenhouse", "status": "placeholder"}),
	}
	for _, plantID := range []string{"plant-tomato-001", "plant-tomato-010", "plant-tomato-020"} {
		relations = append(relations, seedRelation("gh-tomato-001", "key_plant", plantID, ObjectTypePlant, plantID, map[string]interface{}{"reason": "mvp_observation"}))
	}
	for i := 1; i <= 20; i++ {
		plantID := fmt.Sprintf("plant-tomato-%03d", i)
		relations = append(relations, seedRelation("row-tomato-a01", "contains", plantID, ObjectTypePlant, fmt.Sprintf("番茄植株 %02d", i), nil))
	}
	return relations
}

var validObjectTypes = map[string]bool{
	string(ObjectTypeFarm):        true,
	string(ObjectTypeGreenhouse):  true,
	string(ObjectTypeParcel):      true,
	string(ObjectTypeCropRow):     true,
	string(ObjectTypePlant):       true,
	string(ObjectTypeCropBatch):   true,
	string(ObjectTypeSensor):      true,
	string(ObjectTypeDevice):      true,
	string(ObjectTypeCamera):      true,
	string(ObjectTypeOperation):   true,
	string(ObjectTypeObservation): true,
}

var validDataQualityStatuses = map[string]bool{
	string(DataQualityReal):      true,
	string(DataQualitySimulated): true,
	string(DataQualityStale):     true,
	string(DataQualityMissing):   true,
}

var validRelationTypes = map[string]bool{
	"parent":      true,
	"contains":    true,
	"device":      true,
	"sensor":      true,
	"camera":      true,
	"crop_batch":  true,
	"key_plant":   true,
	"metric":      true,
	"event":       true,
	"asset":       true,
	"observation": true,
}

func seedObject(id string, objectType vo.AgriculturalObjectType, name, parentID, area, status string, quality vo.DataQualityStatus, updatedAt string, spatial map[string]interface{}, metadata map[string]interface{}) vo.AgriculturalObjectVo {
	return vo.AgriculturalObjectVo{
		ID:             id,
		Type:           string(objectType),
		Name:           name,
		ParentID:       parentID,
		ContainingArea: area,
		Spatial:        spatial,
		Status:         status,
		UpdatedAt:      updatedAt,
		DataQuality:    string(quality),
		Metadata:       metadata,
	}
}

func seedRelation(sourceID, relationType, targetID string, targetType vo.AgriculturalObjectType, label string, metadata map[string]interface{}) vo.AgriculturalObjectRelationVo {
	if metadata == nil {
		metadata = map[string]interface{}{}
	}
	return vo.AgriculturalObjectRelationVo{
		SourceObjectID: sourceID,
		RelationType:   relationType,
		TargetObjectID: targetID,
		TargetType:     string(targetType),
		TargetLabel:    label,
		Metadata:       metadata,
	}
}

func spatial(kind, anchor string, x, y, z float64) map[string]interface{} {
	return map[string]interface{}{
		"kind":   kind,
		"anchor": anchor,
		"position": map[string]interface{}{
			"x": x,
			"y": y,
			"z": z,
		},
	}
}

func normalizeObject(obj *vo.AgriculturalObjectVo) {
	if obj == nil {
		return
	}
	if obj.Spatial == nil {
		obj.Spatial = map[string]interface{}{}
	}
	if obj.Metadata == nil {
		obj.Metadata = map[string]interface{}{}
	}
}

func validateRequestedRelationTypes(relationTypes []string) error {
	for _, relationType := range relationTypes {
		if !validRelationTypes[relationType] {
			return fmt.Errorf("unsupported agricultural relation type: %s", relationType)
		}
	}
	return nil
}

func relationGroupForObjectType(objectType string) string {
	switch objectType {
	case string(ObjectTypeParcel):
		return "parcels"
	case string(ObjectTypeCropRow):
		return "cropRows"
	case string(ObjectTypePlant):
		return "plants"
	case string(ObjectTypeCropBatch):
		return "cropBatches"
	case string(ObjectTypeSensor):
		return "sensors"
	case string(ObjectTypeDevice):
		return "devices"
	case string(ObjectTypeCamera):
		return "cameras"
	case string(ObjectTypeOperation):
		return "events"
	case string(ObjectTypeObservation):
		return "observations"
	default:
		return "children"
	}
}

func relationGroupForRelationType(relationType string) string {
	switch relationType {
	case "parent":
		return "parents"
	case "contains":
		return "children"
	case "device":
		return "devices"
	case "sensor":
		return "sensors"
	case "camera":
		return "cameras"
	case "crop_batch":
		return "cropBatches"
	case "key_plant":
		return "keyPlants"
	case "metric":
		return "metrics"
	case "event":
		return "events"
	case "asset":
		return "assets"
	case "observation":
		return "observations"
	default:
		return "relations"
	}
}

func relationGroupForRelation(rel vo.AgriculturalObjectRelationVo) string {
	if rel.RelationType == "contains" && rel.TargetType != "" {
		return relationGroupForObjectType(rel.TargetType)
	}
	return relationGroupForRelationType(rel.RelationType)
}

func relatedFromObject(relationType string, obj *vo.AgriculturalObjectVo, metadata map[string]interface{}) vo.RelatedObjectVo {
	if metadata == nil {
		metadata = map[string]interface{}{}
	}
	return vo.RelatedObjectVo{
		RelationType: relationType,
		TargetID:     obj.ID,
		TargetType:   obj.Type,
		TargetLabel:  obj.Name,
		Object:       obj,
		Metadata:     metadata,
	}
}

func sortRelationGroups(groups map[string][]vo.RelatedObjectVo) {
	for key := range groups {
		sort.SliceStable(groups[key], func(i, j int) bool {
			left := strings.Join([]string{groups[key][i].TargetType, groups[key][i].TargetID, groups[key][i].TargetLabel}, "|")
			right := strings.Join([]string{groups[key][j].TargetType, groups[key][j].TargetID, groups[key][j].TargetLabel}, "|")
			return left < right
		})
	}
}
