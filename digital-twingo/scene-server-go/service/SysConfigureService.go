package service

import (
	"scene-server-go/mapper"
	"scene-server-go/vo"
)

// SysConfigureService handles system configuration key-value operations.
type SysConfigureService struct {
	dao *mapper.SysconfigMapper
}

func NewSysConfigureService() *SysConfigureService {
	return &SysConfigureService{
		dao: mapper.NewSysconfigMapper(),
	}
}

func (s *SysConfigureService) GetConfig(key string) string {
	vo, err := s.dao.SelectByPrimaryKey(key)
	if err != nil || vo == nil {
		return ""
	}
	return vo.Value
}

func (s *SysConfigureService) SetConfig(key, value string) bool {
	existing, err := s.dao.SelectByPrimaryKey(key)
	if err != nil {
		return false
	}

	if existing == nil {
		record := &vo.SysconfigVo{Key: key, Value: value}
		_, err = s.dao.Insert(record)
	} else {
		existing.Value = value
		_, err = s.dao.UpdateByPrimaryKey(existing)
	}

	return err == nil
}
