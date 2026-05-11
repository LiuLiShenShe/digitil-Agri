/**
 *   scene mock API
 */

// Import scene JSON files using glob
const sceneModules = import.meta.glob('../resdata/scenes/*.json', { eager: true }) as Record<string, any>

function getSceneList(): string[] {
  return Object.keys(sceneModules)
    .map(k => {
      const parts = k.replace(/\\/g, '/').split('/')
      const name = parts[parts.length - 1].replace('.json', '')
      return name
    })
}

function loadSceneData(sceneName: string): any {
  for (const [path, data] of Object.entries(sceneModules)) {
    const parts = path.replace(/\\/g, '/').split('/')
    const name = parts[parts.length - 1].replace('.json', '')
    if (name === sceneName) {
      return data
    }
  }
  return null
}

export const sceneMock = [
  {
    url: '/scene/saveScene',
    type: 'post',
    response: () => {
      return { code: 200 }
    }
  },
  {
    url: '/scene/sceneList',
    type: 'get',
    response: () => {
      return { code: 200, data: getSceneList() }
    }
  },
  {
    url: '/scene/loadScene',
    type: 'get',
    response: (_options: any, reqUrl: string) => {
      const match = reqUrl.match(/scene=([^&]*)/)
      const sceneName = match ? decodeURIComponent(match[1]) : ''

      const sceneData = loadSceneData(sceneName)
      if (sceneData) {
        return { code: 200, data: sceneData }
      }
      return { code: 999, data: '场景未找到: ' + sceneName }
    }
  },
  {
    url: '/scene/defaultScene',
    type: 'get',
    response: () => {
      return { code: 200, data: 'scene001' }
    }
  }
]
