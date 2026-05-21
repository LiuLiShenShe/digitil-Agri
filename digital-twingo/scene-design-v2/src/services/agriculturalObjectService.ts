import axios from 'axios'

export type AgriculturalObjectType =
  | 'Farm'
  | 'Greenhouse'
  | 'Parcel'
  | 'CropRow'
  | 'Plant'
  | 'CropBatch'
  | 'Sensor'
  | 'Device'
  | 'Camera'
  | 'Operation'
  | 'Observation'

export type DataQualityStatus = 'real' | 'simulated' | 'stale' | 'missing'

export interface AgriculturalObject {
  id: string
  type: AgriculturalObjectType
  name: string
  parentId: string
  containingArea: string
  spatial: Record<string, unknown>
  status: string
  updatedAt: string
  dataQuality: DataQualityStatus
  metadata: Record<string, unknown>
}

export interface RelatedObject {
  relationType: string
  targetId: string
  targetType: string
  targetLabel: string
  object?: AgriculturalObject
  metadata: Record<string, unknown>
}

export interface ObjectRelationsResponse {
  code: number
  objectId: string
  object?: AgriculturalObject
  parent?: AgriculturalObject
  relations: Record<string, RelatedObject[]>
}

const AGRICULTURAL_OBJECT_API = '/objects'

export async function fetchAgriculturalObjects(type?: AgriculturalObjectType): Promise<AgriculturalObject[]> {
  const res = await axios.get(AGRICULTURAL_OBJECT_API, { params: type ? { type } : undefined })
  if (res.data?.code === 200 && Array.isArray(res.data.data)) {
    return res.data.data as AgriculturalObject[]
  }
  return []
}

export async function fetchAgriculturalObject(id: string): Promise<AgriculturalObject | null> {
  const res = await axios.get(`${AGRICULTURAL_OBJECT_API}/${encodeURIComponent(id)}`)
  if (res.data?.code === 200) {
    return res.data.data as AgriculturalObject
  }
  return null
}

export async function fetchAgriculturalObjectRelations(id: string): Promise<ObjectRelationsResponse | null> {
  const res = await axios.get(`${AGRICULTURAL_OBJECT_API}/${encodeURIComponent(id)}/relations`)
  if (res.data?.code === 200) {
    return res.data.data as ObjectRelationsResponse
  }
  return null
}
