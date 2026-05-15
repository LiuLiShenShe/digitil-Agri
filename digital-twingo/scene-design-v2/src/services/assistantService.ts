import axios from 'axios'

export interface AssistantChatRequest {
  message: string
  sessionId?: string
  context?: Record<string, unknown>
}

export interface AssistantChatResponse {
  sessionId: string
  answer: string
  toolCalls: AssistantToolCall[]
  citations: AssistantCitation[]
  ragUsed: boolean
}

export interface AssistantTool {
  name: string
  label: string
  description: string
  readOnly: boolean
}

export interface AssistantToolCall {
  name: string
  label: string
  status: 'success' | 'error'
  durationMs: number
  summary: string
  data?: unknown
  error?: string
}

export interface AssistantCitation {
  source: string
  title: string
  excerpt: string
}

export interface AssistantRagStatus {
  enabled: boolean
  status: string
  message: string
  documentTypes: string[]
  chunks: AssistantRagChunk[]
}

export interface AssistantRagChunk {
  source: string
  score: number
  title: string
  excerpt: string
}

export interface AssistantContextSummary {
  updatedAt: string
  modelStats: unknown
  sceneCount: number
  deviceSummary: Record<string, unknown>
  alertSummary: Record<string, unknown>
  businessSummary: unknown
  rag: AssistantRagStatus
}

export async function fetchAssistantTools(): Promise<AssistantTool[]> {
  const res = await axios.get('/assistant/tools')
  if (res.data?.code === 200) {
    return res.data.data as AssistantTool[]
  }
  return []
}

export async function fetchAssistantContextSummary(): Promise<AssistantContextSummary | null> {
  const res = await axios.get('/assistant/context/summary')
  if (res.data?.code === 200) {
    return res.data.data as AssistantContextSummary
  }
  return null
}

export async function fetchAssistantRagStatus(): Promise<AssistantRagStatus | null> {
  const res = await axios.get('/assistant/rag/status')
  if (res.data?.code === 200) {
    return res.data.data as AssistantRagStatus
  }
  return null
}

export async function sendAssistantMessage(request: AssistantChatRequest): Promise<AssistantChatResponse> {
  const res = await axios.post('/assistant/chat', request)
  if (res.data?.code === 200) {
    return res.data.data as AssistantChatResponse
  }
  throw new Error(res.data?.data || 'AI 助手响应失败')
}
