/**
 *   background mock API
 */
import skyboxList from '../resdata/skybox-list.json'

export const backgroundMock = [
  {
    url: '/background/list',
    type: 'get',
    response: () => {
      return { code: 200, data: skyboxList }
    }
  },
  {
    url: 'background/gdTextures',
    type: 'get',
    response: () => {
      return {
        code: 200,
        data: [
          { name: '草地', pic: './textures/grass.jpg' },
          { name: '混凝土', pic: './textures/concrete.jpg' },
          { name: '大理石', pic: './textures/marble.jpg' }
        ]
      }
    }
  }
]
