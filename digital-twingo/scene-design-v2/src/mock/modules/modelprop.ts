/**
 *   model property mock API — simulates data with random values + load curve
 */

function createCurveData() {
  const curve = []
  for (let h = 0; h < 24; h++) {
    for (let m = 0; m < 60; m += 30) {
      curve.push({
        time: h + ':' + m,
        value: 20 + Math.round(Math.random() * 20000) / 1000
      })
    }
  }
  return curve
}

export const modelPropMock = [
  {
    url: '/datasvr/getData',
    type: 'get',
    response: (_options: any, reqUrl: string) => {
      // Extract dataId from query string
      const match = reqUrl.match(/dataId=([^&]*)/)
      const dataId = match ? match[1] : 'unknown'

      return {
        code: 200,
        data: {
          dataId: dataId,
          name: '模拟数据#' + dataId,
          loadcurve: createCurveData(),
          carbon: 30 + Math.round(Math.random() * 20000) / 1000,
          intensity: 25 - Math.round(Math.random() * 20000) / 1000
        }
      }
    }
  }
]
