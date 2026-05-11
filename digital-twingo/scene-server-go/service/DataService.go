package service

import (
	"math/rand"
	"scene-server-go/mapper"
	"scene-server-go/vo"
	"strconv"
	"time"
)

// DataService handles data entity queries and simulation.
type DataService struct {
	dao *mapper.DataIndexMapper
}

func NewDataService() *DataService {
	return &DataService{
		dao: mapper.NewDataIndexMapper(),
	}
}

func (s *DataService) GetData(dataId string) vo.ResultVo {
	v, err := s.dao.SelectByPrimaryKey(dataId)

	dataMap := make(map[string]interface{})
	dataMap["dataId"] = dataId

	if err != nil || v == nil {
		dataMap["name"] = "未知对象"
	} else {
		dataMap["name"] = v.Name
	}

	s.simulateData(dataId, dataMap)

	return vo.ResultVo{Code: 200, Data: dataMap}
}

func (s *DataService) simulateData(dataId string, dataMap map[string]interface{}) {
	dataMap["loadcurve"] = s.createCurveData()
	dataMap["carbon"] = 30 + rand.Float64()*20
	dataMap["intensity"] = 25 - rand.Float64()*20
}

func (s *DataService) createCurveData() []vo.CurveData {
	rng := rand.New(rand.NewSource(time.Now().UnixNano()))
	curveData := make([]vo.CurveData, 0)

	for h := 0; h < 24; h++ {
		for m := 0; m < 60; m += 30 {
			d := vo.CurveData{
				Time:  formatTime(h, m),
				Value: 20 + float64(int(rng.Float64()*20000))/1000.0,
			}
			curveData = append(curveData, d)
		}
	}
	return curveData
}

func formatTime(h, m int) string {
	return strconv.Itoa(h) + ":" + strconv.Itoa(m)
}
