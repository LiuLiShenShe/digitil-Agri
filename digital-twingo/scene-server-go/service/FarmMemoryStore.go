package service

import (
	"fmt"
	"sort"
	"time"

	"scene-server-go/vo"
)

type FarmMemoryStore interface {
	EnsureSchema() error
	FindMetricPoints(objectIDs []string, metricKeys []string, start, end time.Time, limit int) ([]vo.FarmMetricPointVo, error)
	FindLatestMetricPoints(objectIDs []string, metricKeys []string) ([]vo.FarmMetricPointVo, error)
	InsertMetricPoint(vo.FarmMetricPointVo) error
	UpsertEvent(vo.FarmEventVo) error
	FindEvents(objectIDs []string, eventTypes []string, start, end time.Time, limit int) ([]vo.FarmEventVo, error)
	UpsertDailyArchive(vo.FarmDailyArchiveVo) error
	FindDailyArchives(objectID string, days int, endDate string) ([]vo.FarmDailyArchiveVo, error)
}

type MemoryFarmMemoryStore struct {
	points   []vo.FarmMetricPointVo
	events   []vo.FarmEventVo
	archives []vo.FarmDailyArchiveVo
	nextID   int64
}

func NewMemoryFarmMemoryStore() *MemoryFarmMemoryStore {
	return &MemoryFarmMemoryStore{nextID: 1}
}

func (s *MemoryFarmMemoryStore) EnsureSchema() error {
	return nil
}

func (s *MemoryFarmMemoryStore) InsertMetricPoint(point vo.FarmMetricPointVo) error {
	if point.ID == 0 {
		point.ID = s.nextID
		s.nextID++
	}
	s.points = append(s.points, point)
	return nil
}

func (s *MemoryFarmMemoryStore) FindMetricPoints(objectIDs []string, metricKeys []string, start, end time.Time, limit int) ([]vo.FarmMetricPointVo, error) {
	objectSet := stringSet(objectIDs)
	metricSet := stringSet(metricKeys)
	points := make([]vo.FarmMetricPointVo, 0)
	for _, point := range s.points {
		if len(objectSet) > 0 && !objectSet[point.ObjectID] {
			continue
		}
		if len(metricSet) > 0 && !metricSet[point.MetricKey] {
			continue
		}
		if !start.IsZero() && point.Timestamp.Before(start) {
			continue
		}
		if !end.IsZero() && point.Timestamp.After(end) {
			continue
		}
		points = append(points, point)
	}
	sort.SliceStable(points, func(i, j int) bool {
		return points[i].Timestamp.Before(points[j].Timestamp)
	})
	if limit > 0 && len(points) > limit {
		points = points[len(points)-limit:]
	}
	return points, nil
}

func (s *MemoryFarmMemoryStore) FindLatestMetricPoints(objectIDs []string, metricKeys []string) ([]vo.FarmMetricPointVo, error) {
	points, err := s.FindMetricPoints(objectIDs, metricKeys, time.Time{}, time.Time{}, 0)
	if err != nil {
		return nil, err
	}
	latest := map[string]vo.FarmMetricPointVo{}
	for _, point := range points {
		key := point.ObjectID + "|" + point.MetricKey
		if current, ok := latest[key]; !ok || point.Timestamp.After(current.Timestamp) {
			latest[key] = point
		}
	}
	result := make([]vo.FarmMetricPointVo, 0, len(latest))
	for _, point := range latest {
		result = append(result, point)
	}
	sort.SliceStable(result, func(i, j int) bool {
		if result[i].MetricKey == result[j].MetricKey {
			return result[i].ObjectID < result[j].ObjectID
		}
		return result[i].MetricKey < result[j].MetricKey
	})
	return result, nil
}

func (s *MemoryFarmMemoryStore) UpsertEvent(event vo.FarmEventVo) error {
	if event.EventID == "" {
		return fmt.Errorf("eventId is required")
	}
	for i := range s.events {
		if s.events[i].EventID == event.EventID {
			if event.ID == 0 {
				event.ID = s.events[i].ID
			}
			s.events[i] = copyFarmEvent(event)
			return nil
		}
	}
	if event.ID == 0 {
		event.ID = s.nextID
		s.nextID++
	}
	s.events = append(s.events, copyFarmEvent(event))
	return nil
}

func (s *MemoryFarmMemoryStore) FindEvents(objectIDs []string, eventTypes []string, start, end time.Time, limit int) ([]vo.FarmEventVo, error) {
	objectSet := stringSet(objectIDs)
	eventSet := stringSet(eventTypes)
	events := make([]vo.FarmEventVo, 0)
	for _, event := range s.events {
		if len(objectSet) > 0 && !objectSet[event.ObjectID] && !objectSet[event.RelatedObjectID] {
			continue
		}
		if len(eventSet) > 0 && !eventSet[event.EventType] {
			continue
		}
		if !start.IsZero() && event.Timestamp.Before(start) {
			continue
		}
		if !end.IsZero() && event.Timestamp.After(end) {
			continue
		}
		events = append(events, copyFarmEvent(event))
	}
	sort.SliceStable(events, func(i, j int) bool {
		return events[i].Timestamp.After(events[j].Timestamp)
	})
	if limit > 0 && len(events) > limit {
		events = events[:limit]
	}
	return events, nil
}

func (s *MemoryFarmMemoryStore) UpsertDailyArchive(archive vo.FarmDailyArchiveVo) error {
	for i := range s.archives {
		if s.archives[i].ObjectID == archive.ObjectID && s.archives[i].ArchiveDate == archive.ArchiveDate {
			if archive.ID == 0 {
				archive.ID = s.archives[i].ID
			}
			s.archives[i] = copyArchive(archive)
			return nil
		}
	}
	if archive.ID == 0 {
		archive.ID = s.nextID
		s.nextID++
	}
	s.archives = append(s.archives, copyArchive(archive))
	return nil
}

func (s *MemoryFarmMemoryStore) FindDailyArchives(objectID string, days int, endDate string) ([]vo.FarmDailyArchiveVo, error) {
	if days <= 0 {
		days = 7
	}
	archives := make([]vo.FarmDailyArchiveVo, 0)
	for _, archive := range s.archives {
		if archive.ObjectID != objectID {
			continue
		}
		if endDate != "" && archive.ArchiveDate > endDate {
			continue
		}
		archives = append(archives, copyArchive(archive))
	}
	sort.SliceStable(archives, func(i, j int) bool {
		return archives[i].ArchiveDate > archives[j].ArchiveDate
	})
	if len(archives) > days {
		archives = archives[:days]
	}
	return archives, nil
}

func copyFarmEvent(event vo.FarmEventVo) vo.FarmEventVo {
	event.Metadata = copyMap(event.Metadata)
	return event
}

func copyArchive(archive vo.FarmDailyArchiveVo) vo.FarmDailyArchiveVo {
	archive.MetricSummaries = copyMetricSummaries(archive.MetricSummaries)
	archive.EventCounts = copyIntMap(archive.EventCounts)
	return archive
}

func copyMetricSummaries(input map[string]vo.FarmMetricAggregateVo) map[string]vo.FarmMetricAggregateVo {
	if input == nil {
		return map[string]vo.FarmMetricAggregateVo{}
	}
	output := make(map[string]vo.FarmMetricAggregateVo, len(input))
	for key, value := range input {
		output[key] = value
	}
	return output
}

func copyIntMap(input map[string]int) map[string]int {
	if input == nil {
		return map[string]int{}
	}
	output := make(map[string]int, len(input))
	for key, value := range input {
		output[key] = value
	}
	return output
}

func stringSet(values []string) map[string]bool {
	result := map[string]bool{}
	for _, value := range values {
		if value != "" {
			result[value] = true
		}
	}
	return result
}
