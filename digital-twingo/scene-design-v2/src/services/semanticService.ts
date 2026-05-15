import axios from 'axios'

export interface SemanticBuildRequest {
  message: string
  sceneName?: string
  mode?: 'preview' | 'append'
  context?: SemanticBuildContext
}

export interface ScenePlan {
  sceneName: string
  intent: string
  units: string
  mode: string
  ground: {
    width: number
    height: number
    color?: string
    terrain?: string
  }
  objects: ScenePlanObject[]
  relations: SceneRelation[]
}

export interface ScenePlanObject {
  id: string
  label: string
  category: string
  assetKey: string
  url?: string
  count: number
  layout: string
  area: string
  scale: number
  size: {
    width: number
    depth: number
  }
  aliases?: string[]
}

export interface SceneRelation {
  subject: string
  predicate: string
  object: string
}

export interface BuildModel {
  url: string
  options: {
    offset: { x: number; y: number; z: number }
    scale: number
    angle: number
  }
  meta: {
    id: string
    label: string
    assetKey: string
    category: string
    area: string
    layout: string
  }
}

export interface MissingAsset {
  assetKey: string
  name: string
  reason: string
}

export interface BuildSample {
  title: string
  message: string
}

export interface SemanticPlanSource {
  mode: 'llm' | 'rule' | string
  model: string
  provider?: string
  attempt: number
  reason?: string
}

export interface SemanticBuildContext {
  sceneName: string
  appendMode: boolean
  sceneSummary: {
    objectCount: number
    modelCount: number
  }
  selectedObject?: SemanticObjectSummary
  selectedObjects?: SemanticObjectSummary[]
  existingObjects?: SemanticObjectSummary[]
}

export interface SemanticObjectSummary {
  id?: string
  label: string
  assetKey?: string
  category?: string
  url?: string
  count?: number
  area?: string
  layout?: string
  scale?: number
  offset?: { x: number; y: number; z: number }
}

export interface AssetSemantic {
  assetKey: string
  name: string
  aliases: string[]
  category: string
  url: string
  defaultScale: number
  footprint: {
    width: number
    depth: number
  }
  layoutRules: string[]
}

export interface SemanticBuildResponse {
  scenePlan: ScenePlan
  models: BuildModel[]
  warnings: string[]
  missingAssets: MissingAsset[]
  samples: BuildSample[]
  planSource: SemanticPlanSource
  context: SemanticBuildContext
  rawLlmPlan?: string
}

export async function buildSemanticPlan(request: SemanticBuildRequest): Promise<SemanticBuildResponse> {
  const res = await axios.post('/semantic/build/plan', request)
  if (res.data?.code === 200) {
    return res.data.data as SemanticBuildResponse
  }
  throw new Error(res.data?.data || '语义搭建方案生成失败')
}

export async function fetchSemanticSamples(): Promise<BuildSample[]> {
  const res = await axios.get('/semantic/samples')
  if (res.data?.code === 200) {
    return res.data.data as BuildSample[]
  }
  return []
}

export async function fetchAssetSemantics(): Promise<AssetSemantic[]> {
  const res = await axios.get('/semantic/assets')
  if (res.data?.code === 200) {
    return res.data.data as AssetSemantic[]
  }
  return []
}
