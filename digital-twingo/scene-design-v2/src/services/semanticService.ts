import axios from 'axios'

export interface SemanticBuildRequest {
  message: string
  sceneName?: string
  mode?: 'preview' | 'append'
  ownerKey?: string
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
    scaleMode?: string
    templateKey?: string
    placeholder?: boolean
    missingAssetKey?: string
    generationTaskId?: string
  }
}

export interface SemanticVisualTemplate {
  templateKey: string
  label: string
  renderingMode: string
  greenhouse: {
    center: { x: number; y: number; z: number }
    width: number
    depth: number
    height: number
  }
  plantGrid: {
    rows: number
    columns: number
    spacingX: number
    spacingZ: number
    bedCount: number
    insideOnly: boolean
  }
  irrigation: {
    bedCount: number
    dripLineCount: number
    mainPipeLength: number
    pumpPosition: { x: number; y: number; z: number }
    valvePositions?: Array<{ x: number; y: number; z: number }>
  }
  lighting: {
    skyColor: string
    groundColor: string
    ambientIntensity: number
    directionalIntensity: number
    minimumScreenshotLuma: number
  }
  scaleCalibrations?: Record<string, {
    assetKey: string
    scaleMode: string
    realWidth: number
    realDepth: number
    realHeight: number
    anchorDescription?: string
  }>
  acceptance: {
    expectedTomatoesInsideGreenhouse: number
    minimumScreenshotLuma: number
    maximumTomatoScale: number
    requiresContinuousIrrigation: boolean
  }
}

export interface MissingAsset {
  assetKey: string
  name: string
  category?: string
  reason: string
  prompt?: string
  fallbackModelKey?: string
  placementRefs?: string[]
  routing?: AssetFidelityRoutingDecision
  referenceImage?: MissingAssetReferenceImage
  generation?: MissingAssetGeneration
}

export interface AssetFidelityRoutingDecision {
  assetKey: string
  objectType: string
  strategy: 'existing_asset' | 'F2DMAS' | 'high_fidelity_reconstruction' | 'TRELLIS.2' | 'procedural' | 'placeholder' | string
  selectedAssetKey?: string
  selectedUrl?: string
  fidelityLevel: string
  routingReason: string
  requiresGenerationTask: boolean
  placeholderAssetKey?: string
  generationMode?: string
  referenceImageRequired?: boolean
}

export interface AssetQualityInfo {
  loadable: boolean
  axis: string
  unitScale: number
  center: { x: number; y: number; z: number }
  polygonCount: number
  textureCount: number
  volumeM3: number
  hasThumbnail: boolean
  hasSource: boolean
  hasLicense: boolean
  lod?: string
  qualityStatus: string
  issues?: string[]
}

export interface AssetVersionInfo {
  version: string
  revision?: string
  updatedAt: string
  stage?: string
}

export interface MissingAssetReferenceImage {
  status: 'missing' | 'resolved' | 'uploaded' | 'generated' | 'rejected' | string
  source?: string
  url?: string
  candidates?: ReferenceImageCandidate[]
}

export interface ReferenceImageCandidate {
  id: string
  source: string
  url: string
  score: number
}

export interface MissingAssetGeneration {
  enabled: boolean
  taskId?: string
  status: 'not_created' | 'waiting_image' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | string
  progress?: number
  resultUrl?: string
  thumbnailUrl?: string
  errorMessage?: string
  reviewStatus?: string
  pipeline?: AssetGenerationPipelineStep[]
}

export interface AssetGenerationPipelineStep {
  stage: string
  label: string
  status: string
  localModel?: string
  input?: string
  output?: string
  description?: string
}

export interface AssetJobResponse {
  jobId: string
  ownerKey: string
  assetKey?: string
  assetName?: string
  prompt?: string
  referenceImageSource?: string
  status: string
  progress: number
  modelName?: string
  modelUrl?: string
  thumbUrl?: string
  sourceImageUrl?: string
  fileSize?: number
  errorMsg?: string
  createdAt?: string
  updatedAt?: string
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
  source?: string
  license?: string
  fidelityLevel?: string
  thumbnailUrl?: string
  glbUrl?: string
  applicableObjectTypes?: string[]
  quality?: AssetQualityInfo
  version?: AssetVersionInfo
  metadataComplete?: boolean
  routingReason?: string
}

export interface SemanticBuildResponse {
  scenePlan: ScenePlan
  models: BuildModel[]
  warnings: string[]
  missingAssets: MissingAsset[]
  samples: BuildSample[]
  planSource: SemanticPlanSource
  context: SemanticBuildContext
  visualTemplate?: SemanticVisualTemplate
  rawLlmPlan?: string
  agentTrace?: SceneAgentTrace
}

export interface SceneAgentTrace {
  invocationId: string
  taskId?: string
  agentName: string
  legacyAgentName?: string
  framework: string
  mode: string
  startedAt: string
  finishedAt: string
  durationMs: number
  userInput?: string
  userGoal?: string
  tools: SceneAgentToolCall[]
  steps?: SceneAgentStep[]
  fallback?: SceneAgentFallback
  finalSummary: string
  error?: string
}

export interface SceneAgentToolCall {
  name: string
  agent?: string
  toolCategory?: string
  status: string
  durationMs: number
  inputSummary?: string
  outputSummary?: string
  failureReason?: string
  error?: string
  fallback?: SceneAgentFallback
  flow?: string
}

export interface SceneAgentStep {
  stepId: string
  agent: string
  tool: string
  toolCategory: 'read-only' | 'controlled-write' | 'prohibited' | string
  status: string
  durationMs: number
  inputSummary?: string
  outputSummary?: string
  failureReason?: string
  fallback?: SceneAgentFallback
  flow?: string
}

export interface SceneAgentFallback {
  used: boolean
  reason?: string
  path?: string
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

export async function createAssetGenerationJob(request: {
  imageBase64: string
  imageFileName: string
  ownerKey: string
  assetKey?: string
  assetName?: string
  prompt?: string
  referenceImageSource?: string
  resolution?: number
  decimationTarget?: number
  textureSize?: number
}): Promise<AssetJobResponse> {
  const res = await axios.post('/asset/jobs', request)
  if (res.data?.code === 200) {
    return res.data.data as AssetJobResponse
  }
  throw new Error(res.data?.data || '资产生成任务提交失败')
}

export async function fetchAssetGenerationJob(jobId: string): Promise<AssetJobResponse> {
  const res = await axios.get(`/asset/jobs/${jobId}`)
  if (res.data?.code === 200) {
    return res.data.data as AssetJobResponse
  }
  throw new Error(res.data?.data || '资产生成任务查询失败')
}
