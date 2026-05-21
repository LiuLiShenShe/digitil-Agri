import type { AgriculturalObject, ObjectRelationsResponse, RelatedObject } from '@/services/agriculturalObjectService'

const updatedAt = '2026-05-21T08:00:00Z'

function object(
  id: string,
  type: AgriculturalObject['type'],
  name: string,
  parentId: string,
  dataQuality: AgriculturalObject['dataQuality'],
  metadata: Record<string, unknown> = {}
): AgriculturalObject {
  return {
    id,
    type,
    name,
    parentId,
    containingArea: parentId ? '番茄一号温室' : '园区',
    spatial: { anchor: id, position: { x: 0, y: 0, z: 0 } },
    status: type === 'Camera' ? 'offline' : 'normal',
    updatedAt,
    dataQuality,
    metadata
  }
}

const objects: AgriculturalObject[] = [
  object('farm-yupont-demo', 'Farm', '智慧农业示范园区', '', 'real', { mvp: true }),
  object('gh-tomato-001', 'Greenhouse', '番茄一号温室', 'farm-yupont-demo', 'simulated', { areaSqm: 480 }),
  object('parcel-tomato-a', 'Parcel', '番茄温室 A 区地块', 'gh-tomato-001', 'real'),
  object('row-tomato-a01', 'CropRow', 'A01 番茄种植行', 'parcel-tomato-a', 'simulated', { plantCount: 20 }),
  object('batch-tomato-2026-spring', 'CropBatch', '2026 春茬番茄批次', 'gh-tomato-001', 'stale'),
  object('sensor-greenhouse-001', 'Sensor', '温室环境传感器组', 'gh-tomato-001', 'simulated'),
  object('device-irrigation-001', 'Device', '水肥一体化水泵', 'gh-tomato-001', 'real'),
  object('camera-greenhouse-001', 'Camera', '温室入口摄像头', 'gh-tomato-001', 'missing')
]

for (let i = 1; i <= 20; i++) {
  objects.push(object(
    `plant-tomato-${String(i).padStart(3, '0')}`,
    'Plant',
    `番茄植株 ${String(i).padStart(2, '0')}`,
    'row-tomato-a01',
    i === 20 ? 'missing' : 'simulated',
    { keyPlant: i === 1 || i === 10 || i === 20 }
  ))
}

function related(relationType: string, targetId: string): RelatedObject {
  const target = objects.find(item => item.id === targetId)
  return {
    relationType,
    targetId,
    targetType: target?.type || '',
    targetLabel: target?.name || targetId,
    object: target,
    metadata: {}
  }
}

function relationsFor(id: string): ObjectRelationsResponse {
  const current = objects.find(item => item.id === id)
  if (id !== 'gh-tomato-001' || !current) {
    return {
      code: 200,
      objectId: id,
      object: current,
      relations: {
        children: objects.filter(item => item.parentId === id).map(item => related('contains', item.id))
      }
    }
  }
  return {
    code: 200,
    objectId: id,
    object: current,
    parent: objects.find(item => item.id === current.parentId),
    relations: {
      parcels: [related('contains', 'parcel-tomato-a')],
      cropRows: [related('contains', 'row-tomato-a01')],
      cropBatches: [related('crop_batch', 'batch-tomato-2026-spring')],
      sensors: [related('sensor', 'sensor-greenhouse-001')],
      devices: [related('device', 'device-irrigation-001')],
      cameras: [related('camera', 'camera-greenhouse-001')],
      keyPlants: ['plant-tomato-001', 'plant-tomato-010', 'plant-tomato-020'].map(id => related('key_plant', id)),
      metrics: [{ relationType: 'metric', targetId: '', targetType: '', targetLabel: 'temperature', metadata: { unit: 'C' } }],
      events: [{ relationType: 'event', targetId: 'operation-irrigation-001', targetType: 'Operation', targetLabel: '最近一次灌溉', metadata: {} }]
    }
  }
}

export const agriculturalObjectMock = [
  {
    url: '/objects\\?.*',
    type: 'get',
    response: (_options: unknown, reqUrl: string) => {
      const typeMatch = reqUrl.match(/[?&]type=([^&]+)/)
      const idMatch = reqUrl.match(/[?&]id=([^&]+)/)
      if (idMatch) {
        return { code: 200, data: objects.find(item => item.id === decodeURIComponent(idMatch[1])) || null }
      }
      if (typeMatch) {
        const type = decodeURIComponent(typeMatch[1])
        return { code: 200, data: objects.filter(item => item.type === type) }
      }
      return { code: 200, data: objects }
    }
  },
  {
    url: '/objects$',
    type: 'get',
    response: () => ({ code: 200, data: objects })
  },
  {
    url: '/objects/[^/]+/relations',
    type: 'get',
    response: (_options: unknown, reqUrl: string) => {
      const match = reqUrl.match(/\/objects\/([^/]+)\/relations/)
      return { code: 200, data: relationsFor(match ? decodeURIComponent(match[1]) : '') }
    }
  },
  {
    url: '/objects/[^/]+$',
    type: 'get',
    response: (_options: unknown, reqUrl: string) => {
      const match = reqUrl.match(/\/objects\/([^/?]+)/)
      return { code: 200, data: objects.find(item => item.id === (match ? decodeURIComponent(match[1]) : '')) || null }
    }
  }
]
