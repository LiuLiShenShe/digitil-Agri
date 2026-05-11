package service

import (
	"scene-server-go/mapper"
	"scene-server-go/vo"
)

// SkyboxService handles skybox-related business logic.
type SkyboxService struct {
	dao *mapper.SkyboxMapper
}

func NewSkyboxService() *SkyboxService {
	return &SkyboxService{
		dao: mapper.NewSkyboxMapper(),
	}
}

func (s *SkyboxService) QueryAll() vo.ResultVo {
	list, err := s.dao.SelectAll()
	if err != nil {
		return vo.ResultVo{Code: 999, Data: err.Error()}
	}
	return vo.ResultVo{Code: 200, Data: list}
}
