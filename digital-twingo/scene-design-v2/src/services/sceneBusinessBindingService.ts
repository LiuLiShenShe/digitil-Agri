import axios from 'axios'
import type { AgriculturalObject, ObjectRelationsResponse } from './agriculturalObjectService'

export interface SceneBusinessBinding {
  sceneName: string
  modelId: number
  sceneObjectId: string
  businessObjectId: string
  assetKey: string
  isDefaultBinding: boolean
  url: string
}

export interface SceneBindingLookupResponse {
  code: number
  binding?: SceneBusinessBinding
  bindings?: SceneBusinessBinding[]
  object?: AgriculturalObject
}

export interface SceneBindingValidationIssue {
  category: 'missing_business_binding' | 'missing_data_binding' | 'missing_asset_metadata'
  sceneName: string
  sceneObjectId: string
  modelId: number
  businessObjectId?: string
  businessType?: string
  message: string
}

export interface SceneBindingValidationSummary {
  sceneName: string
  totalSceneObjects: number
  boundSceneObjects: number
  bindingRate: number
  verifiedObjectTypes: string[]
  missingObjectTypes: string[]
  issues: SceneBindingValidationIssue[]
}

export interface BoundBusinessDetail {
  binding?: SceneBusinessBinding
  object?: AgriculturalObject | null
  relations?: ObjectRelationsResponse | null
}

export async function fetchSceneObjectBinding(sceneName: string, sceneObjectId: string): Promise<SceneBindingLookupResponse | null> {
  if (!sceneName || !sceneObjectId) return null
  const res = await axios.get('/scene/bindings/by-scene-object', {
    params: { scene: sceneName, sceneObjectId }
  })
  if (res.data?.code === 200) {
    return res.data.data as SceneBindingLookupResponse
  }
  return null
}

export async function fetchBusinessObjectSceneBindings(sceneName: string, businessObjectId: string): Promise<SceneBusinessBinding[]> {
  if (!sceneName || !businessObjectId) return []
  const res = await axios.get('/scene/bindings/by-business-object', {
    params: { scene: sceneName, businessObjectId }
  })
  if (res.data?.code === 200) {
    const data = res.data.data as SceneBindingLookupResponse
    return data.bindings || []
  }
  return []
}

export async function updateSceneBusinessBinding(payload: {
  sceneName: string
  sceneObjectId: string
  businessObjectId: string
  assetKey: string
  isDefaultBinding?: boolean
}): Promise<SceneBindingLookupResponse | null> {
  const res = await axios.put('/scene/bindings', payload)
  if (res.data?.code === 200) {
    return res.data.data as SceneBindingLookupResponse
  }
  return null
}

export async function validateSceneBindings(sceneName: string): Promise<SceneBindingValidationSummary | null> {
  if (!sceneName) return null
  const res = await axios.get('/scene/bindings/validate', { params: { scene: sceneName } })
  if (res.data?.code === 200) {
    return res.data.data as SceneBindingValidationSummary
  }
  return null
}
