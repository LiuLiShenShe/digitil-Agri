package service

import (
	"fmt"
	"sort"

	"scene-server-go/vo"
)

type MemoryAgriculturalObjectStore struct {
	objects   map[string]vo.AgriculturalObjectVo
	relations []vo.AgriculturalObjectRelationVo
	nextID    int64
}

func NewMemoryAgriculturalObjectStore() *MemoryAgriculturalObjectStore {
	return &MemoryAgriculturalObjectStore{
		objects:   map[string]vo.AgriculturalObjectVo{},
		relations: []vo.AgriculturalObjectRelationVo{},
		nextID:    1,
	}
}

func (s *MemoryAgriculturalObjectStore) EnsureSchema() error {
	return nil
}

func (s *MemoryAgriculturalObjectStore) UpsertObject(obj vo.AgriculturalObjectVo) error {
	copied := copyObject(obj)
	s.objects[obj.ID] = copied
	return nil
}

func (s *MemoryAgriculturalObjectStore) UpsertRelation(rel vo.AgriculturalObjectRelationVo) error {
	for i := range s.relations {
		existing := s.relations[i]
		if existing.SourceObjectID == rel.SourceObjectID &&
			existing.RelationType == rel.RelationType &&
			existing.TargetObjectID == rel.TargetObjectID &&
			existing.TargetLabel == rel.TargetLabel {
			rel.ID = existing.ID
			s.relations[i] = copyRelation(rel)
			return nil
		}
	}
	rel.ID = s.nextID
	s.nextID++
	s.relations = append(s.relations, copyRelation(rel))
	return nil
}

func (s *MemoryAgriculturalObjectStore) FindByID(objectID string) (*vo.AgriculturalObjectVo, error) {
	obj, ok := s.objects[objectID]
	if !ok {
		return nil, fmt.Errorf("agricultural object not found: %s", objectID)
	}
	copied := copyObject(obj)
	return &copied, nil
}

func (s *MemoryAgriculturalObjectStore) FindByType(objectType string) ([]vo.AgriculturalObjectVo, error) {
	objects := make([]vo.AgriculturalObjectVo, 0)
	for _, obj := range s.objects {
		if obj.Type == objectType {
			objects = append(objects, copyObject(obj))
		}
	}
	sortObjects(objects)
	return objects, nil
}

func (s *MemoryAgriculturalObjectStore) ListObjects() ([]vo.AgriculturalObjectVo, error) {
	objects := make([]vo.AgriculturalObjectVo, 0, len(s.objects))
	for _, obj := range s.objects {
		objects = append(objects, copyObject(obj))
	}
	sortObjects(objects)
	return objects, nil
}

func (s *MemoryAgriculturalObjectStore) FindRelations(objectID string, relationTypes []string) ([]vo.AgriculturalObjectRelationVo, error) {
	allowed := map[string]bool{}
	for _, relationType := range relationTypes {
		allowed[relationType] = true
	}
	relations := make([]vo.AgriculturalObjectRelationVo, 0)
	for _, rel := range s.relations {
		if rel.SourceObjectID != objectID {
			continue
		}
		if len(allowed) > 0 && !allowed[rel.RelationType] {
			continue
		}
		relations = append(relations, copyRelation(rel))
	}
	sort.SliceStable(relations, func(i, j int) bool {
		if relations[i].RelationType != relations[j].RelationType {
			return relations[i].RelationType < relations[j].RelationType
		}
		return relations[i].TargetObjectID < relations[j].TargetObjectID
	})
	return relations, nil
}

func (s *MemoryAgriculturalObjectStore) FindChildren(parentID string) ([]vo.AgriculturalObjectVo, error) {
	objects := make([]vo.AgriculturalObjectVo, 0)
	for _, obj := range s.objects {
		if obj.ParentID == parentID {
			objects = append(objects, copyObject(obj))
		}
	}
	sortObjects(objects)
	return objects, nil
}

func (s *MemoryAgriculturalObjectStore) CountObjects() (int, error) {
	return len(s.objects), nil
}

func copyObject(obj vo.AgriculturalObjectVo) vo.AgriculturalObjectVo {
	obj.Spatial = copyMap(obj.Spatial)
	obj.Metadata = copyMap(obj.Metadata)
	return obj
}

func copyRelation(rel vo.AgriculturalObjectRelationVo) vo.AgriculturalObjectRelationVo {
	rel.Metadata = copyMap(rel.Metadata)
	return rel
}

func copyMap(input map[string]interface{}) map[string]interface{} {
	if input == nil {
		return map[string]interface{}{}
	}
	output := make(map[string]interface{}, len(input))
	for key, value := range input {
		output[key] = value
	}
	return output
}

func sortObjects(objects []vo.AgriculturalObjectVo) {
	sort.SliceStable(objects, func(i, j int) bool {
		if objects[i].Type != objects[j].Type {
			return objects[i].Type < objects[j].Type
		}
		return objects[i].ID < objects[j].ID
	})
}
