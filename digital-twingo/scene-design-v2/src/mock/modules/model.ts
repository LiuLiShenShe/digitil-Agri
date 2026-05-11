/**
 *   model mock API
 */
import modelList from '../resdata/model-list.json'

export const modelMock = [
  {
    url: '/model/list',
    type: 'get',
    response: () => {
      return { code: 200, data: modelList }
    }
  }
]
