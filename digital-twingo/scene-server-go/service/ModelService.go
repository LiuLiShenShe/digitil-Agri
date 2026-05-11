package service

import (
	"scene-server-go/mapper"
	"scene-server-go/vo"
)

// ModelService handles model-related business logic.
type ModelService struct {
	dao        *mapper.ModelMapper
	assetMapper *mapper.AssetMapper
}

func NewModelService() *ModelService {
	return &ModelService{
		dao:         mapper.NewModelMapper(),
		assetMapper: mapper.NewAssetMapper(),
	}
}

func (s *ModelService) QueryAll() vo.ResultVo {
	list, err := s.dao.SelectAll()
	if err != nil {
		return vo.ResultVo{Code: 999, Data: err.Error()}
	}
	return vo.ResultVo{Code: 200, Data: list}
}

// QueryAllWithAI returns public models + AI-generated models owned by the user.
func (s *ModelService) QueryAllWithAI(ownerKey string) vo.ResultVo {
	// Get public models from model table
	publicList, err := s.dao.SelectAll()
	if err != nil {
		return vo.ResultVo{Code: 999, Data: err.Error()}
	}

	// Get AI-generated models (approved + user's own)
	aiJobs, err := s.assetMapper.ListForModelTree(ownerKey)
	if err != nil {
		return vo.ResultVo{Code: 999, Data: err.Error()}
	}

	// Merge: public models first, then AI-generated under a "我的AI生成" category
	result := make([]vo.ModelVo, len(publicList))
	for i, m := range publicList {
		result[i] = vo.ModelVo{
			Id:        m.Id,
			ParentId:  m.ParentId,
			Name:      m.Name,
			URL:       m.URL,
			Leaf:      m.Leaf,
			Category:  m.Category,
			Tags:      m.Tags,
			Thumbnail: m.Thumbnail,
		}
	}

	// Add AI category if user has AI jobs
	if len(aiJobs) > 0 {
		aiCategoryID := 9999
		result = append(result, vo.ModelVo{
			Id:       aiCategoryID,
			ParentId: 0,
			Name:     "AI 生成",
			URL:      nil,
			Leaf:     false,
		})
		for _, job := range aiJobs {
			modelName := job.ModelName
			if modelName == "" {
				modelName = job.JobID
			}
			url := job.ModelURL
			result = append(result, vo.ModelVo{
				Id:       aiCategoryID*100 + len(result),
				ParentId: aiCategoryID,
				Name:     modelName,
				URL:      &url,
				Leaf:     true,
			})
		}
	}

	return vo.ResultVo{Code: 200, Data: result}
}
