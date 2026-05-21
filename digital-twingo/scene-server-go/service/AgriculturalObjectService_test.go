package service

import "testing"

func TestAgriculturalObjectRejectsUnknownType(t *testing.T) {
	store := NewMemoryAgriculturalObjectStore()
	svc := NewAgriculturalObjectServiceWithStore(store)

	obj := TomatoGreenhouseSeedObjects()[0]
	obj.Type = "UnknownThing"

	if err := svc.ValidateObject(obj); err == nil {
		t.Fatalf("expected unknown agricultural object type to be rejected")
	}
}

func TestAgriculturalObjectSeedIncludesMVPObjects(t *testing.T) {
	store := NewMemoryAgriculturalObjectStore()
	svc := NewAgriculturalObjectServiceWithStore(store)
	if err := svc.SeedTomatoGreenhouseMVP(); err != nil {
		t.Fatalf("seed failed: %v", err)
	}

	requiredTypes := []AgriculturalObjectType{
		ObjectTypeGreenhouse,
		ObjectTypeParcel,
		ObjectTypeCropRow,
		ObjectTypePlant,
		ObjectTypeSensor,
		ObjectTypeDevice,
		ObjectTypeCamera,
	}
	for _, objectType := range requiredTypes {
		result := svc.Lookup(ObjectLookupRequest{Type: string(objectType)})
		if result.Code != 200 {
			t.Fatalf("lookup type %s failed with code %d: %#v", objectType, result.Code, result.Error)
		}
		if len(result.Objects) == 0 {
			t.Fatalf("seed did not include object type %s", objectType)
		}
	}

	plants := svc.Lookup(ObjectLookupRequest{Type: string(ObjectTypePlant)})
	if len(plants.Objects) != 20 {
		t.Fatalf("plant count = %d, want 20", len(plants.Objects))
	}
}

func TestGreenhouseRelationsIncludeMVPContext(t *testing.T) {
	store := NewMemoryAgriculturalObjectStore()
	svc := NewAgriculturalObjectServiceWithStore(store)
	if err := svc.SeedTomatoGreenhouseMVP(); err != nil {
		t.Fatalf("seed failed: %v", err)
	}

	result := svc.Relations(ObjectRelationsRequest{ObjectID: "gh-tomato-001"})
	if result.Code != 200 {
		t.Fatalf("relations failed with code %d: %#v", result.Code, result.Error)
	}

	requiredGroups := []string{
		"parcels",
		"cropRows",
		"cropBatches",
		"sensors",
		"devices",
		"cameras",
		"keyPlants",
	}
	for _, group := range requiredGroups {
		if len(result.Relations[group]) == 0 {
			t.Fatalf("greenhouse relation group %s is empty: %#v", group, result.Relations)
		}
	}
}

func TestAgriculturalObjectDataQualityStatuses(t *testing.T) {
	store := NewMemoryAgriculturalObjectStore()
	svc := NewAgriculturalObjectServiceWithStore(store)
	if err := svc.SeedTomatoGreenhouseMVP(); err != nil {
		t.Fatalf("seed failed: %v", err)
	}

	seen := map[string]bool{}
	result := svc.Lookup(ObjectLookupRequest{})
	if result.Code != 200 {
		t.Fatalf("lookup all failed with code %d", result.Code)
	}
	for _, obj := range result.Objects {
		seen[obj.DataQuality] = true
	}

	for _, status := range []DataQualityStatus{DataQualityReal, DataQualitySimulated, DataQualityStale, DataQualityMissing} {
		if !seen[string(status)] {
			t.Fatalf("data quality status %s not represented in seed: %#v", status, seen)
		}
	}
}

func TestObjectLookupContractReturnsNormalizedDetails(t *testing.T) {
	store := NewMemoryAgriculturalObjectStore()
	svc := NewAgriculturalObjectServiceWithStore(store)
	if err := svc.SeedTomatoGreenhouseMVP(); err != nil {
		t.Fatalf("seed failed: %v", err)
	}

	result := svc.Lookup(ObjectLookupRequest{ObjectID: "gh-tomato-001"})
	if result.Code != 200 {
		t.Fatalf("lookup failed with code %d: %#v", result.Code, result.Error)
	}
	if result.Object == nil {
		t.Fatalf("lookup result object is nil")
	}
	if result.Object.ID != "gh-tomato-001" || result.Object.Type != string(ObjectTypeGreenhouse) {
		t.Fatalf("unexpected lookup object: %#v", result.Object)
	}
	if result.Object.Name == "" || result.Object.Status == "" || result.Object.UpdatedAt == "" || result.Object.DataQuality == "" {
		t.Fatalf("lookup object lacks normalized required fields: %#v", result.Object)
	}
	if result.Object.Spatial == nil || result.Object.Metadata == nil {
		t.Fatalf("lookup object lacks spatial or metadata maps: %#v", result.Object)
	}
}

func TestObjectRelationsContractRejectsUnsupportedQuery(t *testing.T) {
	store := NewMemoryAgriculturalObjectStore()
	svc := NewAgriculturalObjectServiceWithStore(store)
	if err := svc.SeedTomatoGreenhouseMVP(); err != nil {
		t.Fatalf("seed failed: %v", err)
	}

	result := svc.Relations(ObjectRelationsRequest{ObjectID: "gh-tomato-001", RelationTypes: []string{"DROP TABLE"}})
	if result.Code == 200 {
		t.Fatalf("unsupported relation type should not be accepted: %#v", result)
	}
}
