/**
 *   semantic mock API
 */

const semanticSamples = [
  { title: '智慧农业示范园区', message: '搭一个智慧农业示范园区，左侧六块玉米地，右侧三个温室，中间一条道路，中央放气象站和灌溉设备。' },
  { title: '标准温室场景', message: '创建标准温室场景，两个大棚纵向排列，每个大棚旁边放灌溉设备，入口放摄像头。' },
  { title: '农田 + 气象站组合', message: '生成农田和气象站组合，四块小麦田做网格，中间放气象站，南侧放水塔。' },
  { title: '现有场景补设备', message: '在现有场景补齐摄像头、气象站、水塔和灌溉系统，设备沿道路布置。' },
  { title: '综合园区模板', message: '做一个综合农业园区，西侧农田，东侧温室，北侧仓库和管理楼，中央道路贯穿。' },
  { title: '温室语义同义词', message: '帮我搭一个玻璃房园区，左边放 3 个大棚，右边放 2 个温室，中央放监测站。' },
  { title: '补全当前场景', message: '继续补几个摄像头和环境传感器，优先放在道路两侧。' },
  { title: '方位与数量', message: '左侧放 4 块小麦田，右侧放 2 个水塔，北侧补一个仓库。' },
  { title: '模板变体', message: '生成一个智慧农业园区模板，南侧道路贯穿，中间放气象站，东侧摆温室。' },
  { title: '模糊补充', message: '把当前场景再完善一下，增加巡检车、无人机和灌溉装置。' },
  { title: '温室阵列', message: '在右边做一排温室，按纵向排列，旁边加传感器。' },
  { title: '田块阵列', message: '西边做 6 块玉米地，按网格摆放，留出中间通道。' },
  { title: '中心设备', message: '中心放一个气象站，周围配摄像头和喷灌设备。' },
  { title: '仓储补齐', message: '北侧补仓库和管理楼，南侧放水塔。' },
  { title: '道路导向', message: '沿道路两侧布置摄像头和灌溉设备。' },
  { title: '补全温室', message: '在现有温室旁边继续补 2 个大棚和 2 个传感器。' },
  { title: '温室 + 道路', message: '做一个温室园区，中央道路贯穿，东侧三个温室，西侧四块小麦田。' },
  { title: '示范园区简版', message: '帮我搭一个农业示范园区，左边农田，右边温室，中间道路。' },
  { title: '设备补齐', message: '在场景里补齐气象站、摄像头、水塔和农机。' },
  { title: '复杂组合', message: '左边 3 块玉米地，右边 3 个玻璃房，北边仓库和管理楼，中间放气象站和灌溉系统。' }
]

function buildSemanticPlan(req: any) {
  const message = String(req?.message || '')
  const sceneName = req?.sceneName || 'AI搭建草稿'
  const appendMode = req?.context?.appendMode || /继续|补|补齐|补充|增加|加几个|现有|当前/.test(message)
  const useLLM = /LLM|llm|语义/.test(message) && !/规则回退/.test(message)
  const greenhouse = {
    id: 'greenhouse_group',
    label: '温室大棚',
    category: 'facility',
    assetKey: 'greenhouse',
    url: '/scene-assets/models/Silo_House.glb',
    count: 3,
    layout: 'column',
    area: 'east',
    scale: 0.9,
    size: { width: 140, depth: 90 },
    aliases: ['温室', '大棚', '玻璃温室', '暖棚']
  }
  const plan = {
    scenePlan: {
      sceneName,
      intent: message,
      units: 'platform',
      mode: appendMode ? 'append' : 'preview',
      ground: { width: 1500, height: 1300, color: '#88aa66', terrain: 'field' },
      objects: [greenhouse],
      relations: [{ subject: 'weather_station', predicate: 'near', object: 'field_center' }]
    },
    models: [
      {
        url: '/scene-assets/models/Silo_House.glb',
        options: { offset: { x: 250, y: 0, z: 0 }, scale: 0.9, angle: 90 },
        meta: { id: 'greenhouse_01', label: '温室大棚 1', assetKey: 'greenhouse', category: 'facility', area: 'east', layout: 'column' }
      }
    ],
    warnings: useLLM ? [] : ['LLM 未启用，已使用规则版解析。'],
    missingAssets: [
      { assetKey: 'camera', name: '摄像头', reason: '当前模型库没有可用 GLB。' }
    ],
    samples: semanticSamples,
    planSource: {
      mode: useLLM ? 'llm' : 'rule',
      model: useLLM ? 'mock-llm' : '',
      provider: useLLM ? 'openai-compatible' : 'disabled',
      attempt: useLLM ? 1 : 0,
      reason: useLLM ? 'mock semantic plan' : 'llm disabled'
    },
    context: req?.context || {
      sceneName,
      appendMode,
      sceneSummary: { objectCount: 1, modelCount: 1 },
      existingObjects: [greenhouse]
    },
    rawLlmPlan: useLLM ? JSON.stringify({ scenePlan: { sceneName, intent: message } }, null, 2) : ''
  }
  return { code: 200, data: plan }
}

export const semanticMock = [
  {
    url: '/semantic/build/plan',
    type: 'post',
    response: (options: any, reqUrl: string, reqBody: any) => {
      let payload = reqBody
      if (!payload && options?.body) {
        try {
          payload = JSON.parse(options.body)
        } catch {
          payload = {}
        }
      }
      return buildSemanticPlan(payload)
    }
  },
  {
    url: '/semantic/assets',
    type: 'get',
    response: () => {
      return {
        code: 200,
        data: [
          { assetKey: 'greenhouse', name: '温室大棚', aliases: ['温室', '大棚', '玻璃温室'], category: 'facility', url: '/scene-assets/models/Silo_House.glb', defaultScale: 0.9, footprint: { width: 140, depth: 90 }, layoutRules: ['row', 'column', 'grid'] },
          { assetKey: 'corn', name: '玉米地', aliases: ['玉米', '玉米田'], category: 'crop', url: '/scene-assets/models/Corn_Crop.glb', defaultScale: 1.1, footprint: { width: 90, depth: 90 }, layoutRules: ['grid', 'row'] },
          { assetKey: 'weather_station', name: '气象站', aliases: ['气象站', '监测站'], category: 'device', url: '/scene-assets/models/TowerWindmill.glb', defaultScale: 0.7, footprint: { width: 60, depth: 60 }, layoutRules: ['single'] }
        ]
      }
    }
  },
  {
    url: '/semantic/samples',
    type: 'get',
    response: () => {
      return { code: 200, data: semanticSamples }
    }
  }
]
