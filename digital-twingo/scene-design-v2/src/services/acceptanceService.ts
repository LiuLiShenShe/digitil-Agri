import axios from 'axios'
import type { AgriculturalObject, ObjectRelationsResponse } from './agriculturalObjectService'
import type { EventQueryResponse, FarmLatestResponse, GreenhouseReportSource } from './farmMemoryService'
import type { MissingAsset, SceneAgentTrace, ScenePlan, BuildModel, SemanticPlanSource } from './semanticService'
import type { SceneBindingValidationSummary } from './sceneBusinessBindingService'

export interface AcceptanceCount {
  label: string
  expected: number
  actual: number
  passed: boolean
}

export interface AcceptanceStep {
  key: string
  title: string
  target: string
  actual: string
  passed: boolean
  evidence?: string
}

export interface AcceptanceMetric {
  key: string
  label: string
  target: string
  actual: string
  value: number
  passed: boolean
  source: string
  evidence?: string
}

export interface AcceptanceIssue {
  severity: 'info' | 'warning' | 'error' | string
  category: string
  message: string
  source?: string
}

export interface AcceptanceSemanticBuild {
  scenePlan: ScenePlan
  models: BuildModel[]
  warnings: string[]
  missingAssets: MissingAsset[]
  planSource: SemanticPlanSource
  agentTrace?: SceneAgentTrace
}

export interface AcceptanceObjectMemory {
  objectId: string
  latest: FarmLatestResponse
  events: EventQueryResponse
  recommendation: string
}

export interface AcceptanceArchiveReadiness {
  ready: boolean
  changes: string[]
  nextAction: string
}

export interface AcceptanceBindingValidation {
  code: number
  error?: string
  summary: SceneBindingValidationSummary
}

export interface TomatoGreenhouseAcceptance {
  prompt: string
  sceneName: string
  runAt: string
  overallPassed: boolean
  modelCounts: Record<string, AcceptanceCount>
  steps: AcceptanceStep[]
  successMetrics: AcceptanceMetric[]
  issues: AcceptanceIssue[]
  semanticBuild: AcceptanceSemanticBuild
  bindingValidation: AcceptanceBindingValidation
  greenhouseObject?: AgriculturalObject
  greenhouseContext: ObjectRelationsResponse
  abnormalDevice?: AgriculturalObject
  abnormalContext: AcceptanceObjectMemory
  reportSource: GreenhouseReportSource
  archiveReadiness: AcceptanceArchiveReadiness
}

export async function fetchTomatoGreenhouseAcceptance(): Promise<TomatoGreenhouseAcceptance> {
  const res = await axios.get('/acceptance/tomato-greenhouse')
  if (res.data?.code === 200) {
    return res.data.data as TomatoGreenhouseAcceptance
  }
  throw new Error(res.data?.data || '番茄温室综合验收加载失败')
}
