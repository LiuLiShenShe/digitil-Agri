package service

import (
	"scene-server-go/mapper"
	"scene-server-go/vo"
)

// GdTextureService handles ground texture-related business logic.
type GdTextureService struct {
	dao *mapper.GdtextureMapper
}

func NewGdTextureService() *GdTextureService {
	return &GdTextureService{
		dao: mapper.NewGdtextureMapper(),
	}
}

func (s *GdTextureService) QueryAll() vo.ResultVo {
	list, err := s.dao.SelectAll()
	if err != nil {
		return vo.ResultVo{Code: 999, Data: err.Error()}
	}
	return vo.ResultVo{Code: 200, Data: list}
}
