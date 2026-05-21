import axios from 'axios'

export type SyncFrequency = 'realtime' | 'hourly' | 'daily' | 'milestone' | 'static'
export type FarmDataQuality = 'real' | 'simulated' | 'stale' | 'missing'

export interface FarmMetricDefinition {
  key: string
  label: string
  unit: string
  category: string
  defaultFrequency: SyncFrequency
  aliases?: string[]
}

export interface FarmSyncPolicy {
  objectId?: string
  objectType: string
  syncFrequency: SyncFrequency
  geometryFrequency?: SyncFrequency
  metricKeys: string[]
  sourceDeviceIds: string[]
  dataQuality: FarmDataQuality
}

export interface FarmMetricLatestValue {
  metricKey: string
  label: string
  value: number
  unit: string
  timestamp: string
  dataQuality: FarmDataQuality
  sourceDeviceId?: string
}

export interface FarmLatestResponse {
  objectId: string
  values: Record<string, FarmMetricLatestValue>
  missing: string[]
}

export interface FarmMetricPoint {
  id: number
  objectId: string
  sourceDeviceId: string
  metricKey: string
  value: number
  unit: string
  timestamp: string
  dataQuality: FarmDataQuality
}

export interface FarmMetricAggregate {
  min: number
  max: number
  avg: number
  count: number
}

export interface FarmMetricSeries {
  metricKey: string
  label: string
  unit: string
  points: FarmMetricPoint[]
  aggregate: FarmMetricAggregate
  dataQuality: FarmDataQuality
}

export interface TimeSeriesResponse {
  objectId: string
  range: '24h' | '7d'
  startAt: string
  endAt: string
  series: Record<string, FarmMetricSeries>
  missing: string[]
}

export interface FarmEvent {
  id: number
  eventId: string
  objectId: string
  relatedObjectId: string
  eventType: string
  severity: string
  summary: string
  timestamp: string
  dataQuality: FarmDataQuality
  metadata: Record<string, unknown>
}

export interface EventQueryResponse {
  objectId: string
  range: '24h' | '7d'
  startAt: string
  endAt: string
  events: FarmEvent[]
  missing: string[]
}

export interface FarmReportSection {
  dataQuality: FarmDataQuality
  summary: string
  items: unknown[]
  missing: string[]
}

export interface GreenhouseReportSource {
  objectId: string
  objectName: string
  date: string
  dataQuality: FarmDataQuality
  environment: FarmReportSection
  deviceStatus: FarmReportSection
  alerts: FarmEvent[]
  irrigationEvents: FarmEvent[]
  recommendations: string[]
  missingCategories: string[]
}

export async function fetchMetricDictionary(): Promise<Record<string, FarmMetricDefinition>> {
  const res = await axios.get('/memory/metrics')
  if (res.data?.code === 200) {
    return res.data.data || {}
  }
  return {}
}

export async function fetchObjectSyncPolicy(objectId: string): Promise<FarmSyncPolicy | null> {
  const res = await axios.get(`/objects/${encodeURIComponent(objectId)}/memory/sync-policy`)
  if (res.data?.code === 200) {
    return res.data.data as FarmSyncPolicy
  }
  return null
}

export async function fetchObjectLatestValues(objectId: string, metrics: string[] = []): Promise<FarmLatestResponse | null> {
  const res = await axios.get(`/objects/${encodeURIComponent(objectId)}/memory/latest`, {
    params: metrics.length ? { metric: metrics } : undefined
  })
  if (res.data?.code === 200) {
    return res.data.data as FarmLatestResponse
  }
  return null
}

export async function fetchObjectTimeSeries(objectId: string, range: '24h' | '7d', metrics: string[] = [], limit?: number): Promise<TimeSeriesResponse | null> {
  const res = await axios.get(`/objects/${encodeURIComponent(objectId)}/memory/timeseries`, {
    params: {
      range,
      ...(metrics.length ? { metric: metrics } : {}),
      ...(limit ? { limit } : {})
    }
  })
  if (res.data?.code === 200) {
    return res.data.data as TimeSeriesResponse
  }
  return null
}

export async function fetchObjectEvents(objectId: string, range: '24h' | '7d' = '24h'): Promise<EventQueryResponse | null> {
  const res = await axios.get(`/objects/${encodeURIComponent(objectId)}/memory/events`, { params: { range } })
  if (res.data?.code === 200) {
    return res.data.data as EventQueryResponse
  }
  return null
}

export async function fetchGreenhouseReportSource(objectId: string, date?: string): Promise<GreenhouseReportSource | null> {
  const res = await axios.get(`/objects/${encodeURIComponent(objectId)}/memory/report-source`, {
    params: date ? { date } : undefined
  })
  if (res.data?.code === 200) {
    return res.data.data as GreenhouseReportSource
  }
  return null
}
