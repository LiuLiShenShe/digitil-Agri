import type {
  EventQueryResponse,
  FarmLatestResponse,
  FarmMetricDefinition,
  FarmSyncPolicy,
  GreenhouseReportSource,
  TimeSeriesResponse
} from '@/services/farmMemoryService'

const now = new Date('2026-05-21T10:00:00Z')
const iso = (hoursAgo: number) => new Date(now.getTime() - hoursAgo * 60 * 60 * 1000).toISOString()

const metrics: Record<string, FarmMetricDefinition> = {
  temperature: { key: 'temperature', label: '温度', unit: '°C', category: 'environment', defaultFrequency: 'realtime' },
  humidity: { key: 'humidity', label: '湿度', unit: '%', category: 'environment', defaultFrequency: 'realtime' },
  soilMoisture: { key: 'soilMoisture', label: '土壤水分', unit: '%', category: 'soil', defaultFrequency: 'hourly' },
  co2: { key: 'co2', label: 'CO2', unit: 'ppm', category: 'environment', defaultFrequency: 'realtime' },
  lightIntensity: { key: 'lightIntensity', label: '光照', unit: 'lux', category: 'environment', defaultFrequency: 'realtime' },
  ph: { key: 'ph', label: 'pH', unit: 'pH', category: 'soil', defaultFrequency: 'daily' },
  ec: { key: 'ec', label: 'EC', unit: 'mS/cm', category: 'water_quality', defaultFrequency: 'daily' },
  waterPressure: { key: 'waterPressure', label: '水压', unit: 'kPa', category: 'irrigation', defaultFrequency: 'realtime' },
  flow: { key: 'flow', label: '流量', unit: 'L/min', category: 'irrigation', defaultFrequency: 'realtime', aliases: ['waterFlow'] },
  switchState: { key: 'switchState', label: '设备开关状态', unit: '', category: 'device', defaultFrequency: 'realtime', aliases: ['status'] }
}

function policy(objectId: string): FarmSyncPolicy {
  const isPlant = objectId.startsWith('plant-')
  const isDevice = objectId.includes('device-irrigation')
  const isCamera = objectId.includes('camera')
  return {
    objectId,
    objectType: isPlant ? 'Plant' : isDevice ? 'Device' : isCamera ? 'Camera' : 'Greenhouse',
    syncFrequency: isPlant ? 'daily' : 'realtime',
    geometryFrequency: isPlant ? 'milestone' : undefined,
    metricKeys: isDevice ? ['waterPressure', 'flow', 'switchState'] : isCamera ? ['switchState'] : ['temperature', 'humidity', 'soilMoisture', 'co2', 'lightIntensity', 'ph'],
    sourceDeviceIds: isDevice ? ['iot-irrigation-01'] : isCamera ? ['iot-camera-01'] : ['iot-greenhouse-01', 'iot-irrigation-01'],
    dataQuality: 'simulated'
  }
}

function latest(objectId: string): FarmLatestResponse {
  const base: FarmLatestResponse = {
    objectId,
    values: {
      temperature: { metricKey: 'temperature', label: '温度', value: 25.8, unit: '°C', timestamp: iso(0.5), dataQuality: 'simulated', sourceDeviceId: 'iot-greenhouse-01' },
      humidity: { metricKey: 'humidity', label: '湿度', value: 66.2, unit: '%', timestamp: iso(0.5), dataQuality: 'simulated', sourceDeviceId: 'iot-greenhouse-01' },
      soilMoisture: { metricKey: 'soilMoisture', label: '土壤水分', value: 54.6, unit: '%', timestamp: iso(1), dataQuality: 'simulated', sourceDeviceId: 'iot-greenhouse-01' },
      co2: { metricKey: 'co2', label: 'CO2', value: 820, unit: 'ppm', timestamp: iso(0.5), dataQuality: 'simulated', sourceDeviceId: 'iot-greenhouse-01' },
      waterPressure: { metricKey: 'waterPressure', label: '水压', value: 246, unit: 'kPa', timestamp: iso(0.25), dataQuality: 'simulated', sourceDeviceId: 'iot-irrigation-01' },
      flow: { metricKey: 'flow', label: '流量', value: 32, unit: 'L/min', timestamp: iso(0.25), dataQuality: 'simulated', sourceDeviceId: 'iot-irrigation-01' }
    },
    missing: []
  }
  return base
}

function series(objectId: string, range: '24h' | '7d'): TimeSeriesResponse {
  const hours = range === '24h' ? 24 : 7 * 24
  const points = Array.from({ length: range === '24h' ? 8 : 7 }, (_, idx) => {
    const offset = hours - idx * (range === '24h' ? 3 : 24)
    return {
      id: idx + 1,
      objectId,
      sourceDeviceId: 'iot-greenhouse-01',
      metricKey: 'temperature',
      value: Math.round((24 + Math.sin(idx) * 2) * 10) / 10,
      unit: '°C',
      timestamp: iso(offset),
      dataQuality: 'simulated' as const
    }
  })
  return {
    objectId,
    range,
    startAt: iso(hours),
    endAt: now.toISOString(),
    series: {
      temperature: {
        metricKey: 'temperature',
        label: '温度',
        unit: '°C',
        points,
        aggregate: { min: 22.8, max: 26.1, avg: 24.4, count: points.length },
        dataQuality: 'simulated'
      }
    },
    missing: []
  }
}

function events(objectId: string): EventQueryResponse {
  return {
    objectId,
    range: '24h',
    startAt: iso(24),
    endAt: now.toISOString(),
    events: [
      { id: 1, eventId: 'evt-irrigation-1', objectId, relatedObjectId: 'device-irrigation-001', eventType: 'irrigation', severity: 'info', summary: 'A区灌溉18分钟', timestamp: iso(3), dataQuality: 'real', metadata: { durationMin: 18 } },
      { id: 2, eventId: 'evt-alert-1', objectId: 'device-irrigation-001', relatedObjectId: objectId, eventType: 'alert', severity: 'warning', summary: '水压波动，建议复核过滤器', timestamp: iso(2), dataQuality: 'simulated', metadata: {} },
      { id: 3, eventId: 'evt-agent-1', objectId, relatedObjectId: '', eventType: 'agent_analysis', severity: 'info', summary: 'ReportAgent 建议午后保持通风', timestamp: iso(1), dataQuality: 'simulated', metadata: {} }
    ],
    missing: []
  }
}

function report(objectId: string): GreenhouseReportSource {
  const ev = events(objectId).events
  return {
    objectId,
    objectName: '番茄一号温室',
    date: '2026-05-21',
    dataQuality: 'simulated',
    environment: { dataQuality: 'simulated', summary: '环境摘要包含 4 项指标', items: Object.values(latest(objectId).values).slice(0, 4), missing: [] },
    deviceStatus: { dataQuality: 'simulated', summary: '设备状态包含水压与流量', items: [latest(objectId).values.waterPressure, latest(objectId).values.flow], missing: [] },
    alerts: ev.filter(item => item.eventType === 'alert'),
    irrigationEvents: ev.filter(item => item.eventType === 'irrigation'),
    recommendations: ['午后维持通风策略。', '灌溉设备只读监测，控制动作进入后续受控流程。'],
    missingCategories: []
  }
}

export const farmMemoryMock = [
  { url: '/memory/metrics', type: 'get', response: () => ({ code: 200, data: metrics }) },
  { url: '/memory/sync-policies', type: 'get', response: () => ({ code: 200, data: {} }) },
  {
    url: '/objects/[^/]+/memory/sync-policy',
    type: 'get',
    response: (_options: unknown, reqUrl: string) => ({ code: 200, data: policy(decodeURIComponent(reqUrl.match(/\/objects\/([^/]+)\//)?.[1] || 'gh-tomato-001')) })
  },
  {
    url: '/objects/[^/]+/memory/latest.*',
    type: 'get',
    response: (_options: unknown, reqUrl: string) => ({ code: 200, data: latest(decodeURIComponent(reqUrl.match(/\/objects\/([^/]+)\//)?.[1] || 'gh-tomato-001')) })
  },
  {
    url: '/objects/[^/]+/memory/timeseries.*',
    type: 'get',
    response: (_options: unknown, reqUrl: string) => {
      const objectId = decodeURIComponent(reqUrl.match(/\/objects\/([^/]+)\//)?.[1] || 'gh-tomato-001')
      const range = reqUrl.includes('range=7d') ? '7d' : '24h'
      return { code: 200, data: series(objectId, range) }
    }
  },
  {
    url: '/objects/[^/]+/memory/events.*',
    type: 'get',
    response: (_options: unknown, reqUrl: string) => ({ code: 200, data: events(decodeURIComponent(reqUrl.match(/\/objects\/([^/]+)\//)?.[1] || 'gh-tomato-001')) })
  },
  {
    url: '/objects/[^/]+/memory/report-source.*',
    type: 'get',
    response: (_options: unknown, reqUrl: string) => ({ code: 200, data: report(decodeURIComponent(reqUrl.match(/\/objects\/([^/]+)\//)?.[1] || 'gh-tomato-001')) })
  }
]
