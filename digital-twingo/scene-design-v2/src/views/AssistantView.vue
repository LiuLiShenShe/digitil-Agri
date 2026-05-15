<template>
  <main class="assistant-page">
    <header class="assistant-header">
      <div class="brand-block">
        <div class="brand-mark">
          <el-icon><DataAnalysis /></el-icon>
        </div>
        <div>
          <h1>AI 助手</h1>
          <p>只读调用项目数据，辅助审计、运维和方案补齐</p>
        </div>
      </div>
      <div class="header-actions">
        <span>{{ contextText }}</span>
        <el-button :icon="Refresh" circle size="small" plain :loading="contextLoading" @click="loadContext" />
        <el-button :icon="Monitor" size="small" plain @click="router.push('/monitor')">大屏</el-button>
        <el-button :icon="DataBoard" size="small" plain @click="router.push('/business')">业务</el-button>
        <el-button :icon="Back" size="small" plain @click="router.push('/')">返回</el-button>
      </div>
    </header>

    <section class="assistant-shell">
      <section class="chat-panel">
        <div class="quick-row">
          <button
            v-for="item in quickPrompts"
            :key="item"
            class="quick-chip"
            type="button"
            @click="askQuick(item)"
          >
            {{ item }}
          </button>
        </div>

        <div ref="messageListRef" class="message-list">
          <article
            v-for="message in messages"
            :key="message.id"
            class="message-card"
            :class="message.role"
          >
            <div class="message-avatar">
              <el-icon v-if="message.role === 'assistant'"><Connection /></el-icon>
              <span v-else>我</span>
            </div>
            <div class="message-body">
              <div class="message-meta">
                <strong>{{ message.role === 'assistant' ? '平台助手' : '用户' }}</strong>
                <span>{{ formatTime(message.createdAt) }}</span>
              </div>
              <p class="message-content">{{ message.content }}</p>

              <div v-if="message.loading" class="thinking-line">
                <span class="pulse-dot"></span>
                正在读取项目数据并生成回答...
              </div>

              <div v-if="message.toolCalls?.length" class="tool-call-list">
                <div
                  v-for="tool in message.toolCalls"
                  :key="tool.name + tool.durationMs"
                  class="tool-call"
                  :class="tool.status"
                >
                  <span>{{ tool.label }}</span>
                  <strong>{{ tool.status === 'success' ? tool.summary : tool.error || '调用失败' }}</strong>
                  <em>{{ tool.durationMs }}ms</em>
                </div>
              </div>

              <div v-if="message.citations?.length" class="citation-list">
                <span v-for="citation in message.citations" :key="citation.source" class="citation-pill">
                  {{ citation.source }}
                </span>
              </div>
            </div>
          </article>
        </div>

        <form class="composer" @submit.prevent="sendMessage">
          <el-input
            v-model="input"
            type="textarea"
            :rows="3"
            resize="none"
            placeholder="问我当前平台缺什么、模型库风险、IoT 告警、业务子系统完成度..."
            @keydown.enter.exact.prevent="sendMessage"
          />
          <el-button type="primary" :icon="DataAnalysis" :loading="sending" native-type="submit">
            发送
          </el-button>
        </form>
      </section>

      <aside class="context-panel">
        <section class="context-card">
          <div class="card-title">
            <el-icon><Document /></el-icon>
            项目上下文
          </div>
          <div class="summary-grid">
            <div class="summary-item">
              <span>场景</span>
              <strong>{{ contextSummary?.sceneCount ?? '--' }}</strong>
            </div>
            <div class="summary-item">
              <span>设备</span>
              <strong>{{ deviceCount }}</strong>
            </div>
            <div class="summary-item warning">
              <span>未确认告警</span>
              <strong>{{ unackedAlerts }}</strong>
            </div>
            <div class="summary-item">
              <span>模型节点</span>
              <strong>{{ modelTotal }}</strong>
            </div>
          </div>
        </section>

        <section class="context-card">
          <div class="card-title">
            <el-icon><Connection /></el-icon>
            只读工具
          </div>
          <div class="tool-list">
            <div v-for="tool in tools" :key="tool.name" class="tool-item">
              <div>
                <strong>{{ tool.label }}</strong>
                <span>{{ tool.name }}</span>
              </div>
              <el-tag size="small" type="success" effect="dark">只读</el-tag>
            </div>
          </div>
        </section>

        <section class="context-card">
          <div class="card-title">
            <el-icon><Warning /></el-icon>
            RAG 状态
          </div>
          <p class="rag-message">{{ ragStatus?.message || '等待 RAG 状态' }}</p>
          <div class="doc-types">
            <span v-for="item in ragStatus?.documentTypes || []" :key="item">{{ item }}</span>
          </div>
        </section>
      </aside>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Back,
  Connection,
  DataAnalysis,
  DataBoard,
  Document,
  Monitor,
  Refresh,
  Warning
} from '@element-plus/icons-vue'
import {
  fetchAssistantContextSummary,
  fetchAssistantRagStatus,
  fetchAssistantTools,
  sendAssistantMessage,
  type AssistantChatResponse,
  type AssistantCitation,
  type AssistantContextSummary,
  type AssistantRagStatus,
  type AssistantTool,
  type AssistantToolCall
} from '@/services/assistantService'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: number
  loading?: boolean
  toolCalls?: AssistantToolCall[]
  citations?: AssistantCitation[]
}

const router = useRouter()
const input = ref('')
const sending = ref(false)
const contextLoading = ref(false)
const sessionId = ref('')
const tools = ref<AssistantTool[]>([])
const contextSummary = ref<AssistantContextSummary | null>(null)
const ragStatus = ref<AssistantRagStatus | null>(null)
const messageListRef = ref<HTMLElement | null>(null)

const quickPrompts = [
  '当前平台还缺什么？',
  '模型库有哪些风险？',
  '当前未确认告警有哪些？',
  '帮我总结业务子系统完成度',
  '分析 IoT 设备在线情况'
]

const messages = ref<ChatMessage[]>([
  {
    id: 'welcome',
    role: 'assistant',
    content: '我是数字孪生平台 AI 助手。当前版本只读调用项目数据，可以帮你审计模型、场景、IoT、告警、监控和业务完成度；RAG 已预留，暂未启用。',
    createdAt: Date.now()
  }
])

const contextText = computed(() => {
  if (!contextSummary.value?.updatedAt) return '等待上下文'
  return `上下文 ${new Date(contextSummary.value.updatedAt).toLocaleTimeString('zh-CN')}`
})

const modelTotal = computed(() => {
  const stats = contextSummary.value?.modelStats as { total?: number } | undefined
  return stats?.total ?? '--'
})

const deviceCount = computed(() => {
  const summary = contextSummary.value?.deviceSummary as { count?: number } | undefined
  return summary?.count ?? '--'
})

const unackedAlerts = computed(() => {
  const summary = contextSummary.value?.alertSummary as { unacked?: number } | undefined
  return summary?.unacked ?? '--'
})

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

async function loadContext() {
  contextLoading.value = true
  try {
    const [toolList, summary, rag] = await Promise.all([
      fetchAssistantTools(),
      fetchAssistantContextSummary(),
      fetchAssistantRagStatus()
    ])
    tools.value = toolList
    contextSummary.value = summary
    ragStatus.value = rag
  } catch {
    ElMessage.error('AI 助手上下文加载失败，请检查后端服务')
  } finally {
    contextLoading.value = false
  }
}

function askQuick(text: string) {
  input.value = text
  sendMessage()
}

async function sendMessage() {
  const text = input.value.trim()
  if (!text || sending.value) return

  input.value = ''
  messages.value.push({
    id: `user-${Date.now()}`,
    role: 'user',
    content: text,
    createdAt: Date.now()
  })

  const assistantMessage: ChatMessage = {
    id: `assistant-${Date.now()}`,
    role: 'assistant',
    content: '',
    createdAt: Date.now(),
    loading: true
  }
  messages.value.push(assistantMessage)
  sending.value = true
  await scrollToBottom()

  try {
    const response = await sendAssistantMessage({
      message: text,
      sessionId: sessionId.value || undefined
    })
    applyAssistantResponse(assistantMessage, response)
  } catch (error) {
    assistantMessage.content = error instanceof Error ? error.message : 'AI 助手请求失败'
    assistantMessage.toolCalls = []
    assistantMessage.citations = []
    ElMessage.error('AI 助手请求失败')
  } finally {
    assistantMessage.loading = false
    sending.value = false
    await scrollToBottom()
  }
}

function applyAssistantResponse(message: ChatMessage, response: AssistantChatResponse) {
  sessionId.value = response.sessionId
  message.content = response.answer
  message.toolCalls = response.toolCalls || []
  message.citations = response.citations || []
}

async function scrollToBottom() {
  await nextTick()
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

onMounted(() => {
  loadContext()
})
</script>

<style scoped>
.assistant-page {
  width: 100%;
  height: 100vh;
  overflow: hidden;
  padding: 18px;
  color: #dbe6ee;
  background:
    linear-gradient(180deg, rgba(8, 16, 28, 0.98), rgba(4, 8, 12, 1)),
    repeating-linear-gradient(90deg, rgba(255,255,255,0.024) 0, rgba(255,255,255,0.024) 1px, transparent 1px, transparent 74px);
}

.assistant-header,
.brand-block,
.header-actions,
.assistant-shell,
.message-card,
.message-meta,
.composer,
.card-title,
.tool-item {
  display: flex;
  align-items: center;
}

.assistant-header {
  justify-content: space-between;
  gap: 18px;
  min-height: 58px;
  margin-bottom: 14px;
}

.brand-block {
  gap: 12px;
}

.brand-mark {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(0, 212, 255, 0.28);
  border-radius: 8px;
  color: #00d4ff;
  background: rgba(0, 212, 255, 0.1);
}

h1,
p {
  margin: 0;
}

h1 {
  font-size: 20px;
  color: #f2f7fb;
}

.brand-block p,
.header-actions,
.message-meta span,
.tool-item span,
.rag-message {
  color: #7f91a2;
  font-size: 12px;
}

.header-actions {
  gap: 8px;
}

.assistant-shell {
  align-items: stretch;
  gap: 14px;
  height: calc(100vh - 90px);
}

.chat-panel,
.context-panel,
.context-card,
.message-card,
.composer {
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(12, 20, 34, 0.78);
  backdrop-filter: blur(14px);
}

.chat-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  border-radius: 8px;
  overflow: hidden;
}

.quick-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.quick-chip {
  border: 1px solid rgba(0, 212, 255, 0.18);
  border-radius: 8px;
  padding: 7px 10px;
  color: #bcd3e5;
  background: rgba(0, 212, 255, 0.06);
  cursor: pointer;
  font-size: 12px;
}

.quick-chip:hover {
  color: #00d4ff;
  border-color: rgba(0, 212, 255, 0.36);
}

.message-list {
  flex: 1;
  overflow: auto;
  padding: 14px;
}

.message-card {
  align-items: flex-start;
  gap: 10px;
  max-width: 980px;
  margin-bottom: 12px;
  padding: 12px;
  border-radius: 8px;
}

.message-card.user {
  margin-left: auto;
  background: rgba(0, 120, 255, 0.14);
}

.message-avatar {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 8px;
  color: #00d4ff;
  background: rgba(0, 212, 255, 0.1);
}

.message-card.user .message-avatar {
  color: #fff;
  background: rgba(64, 144, 255, 0.28);
}

.message-body {
  min-width: 0;
  flex: 1;
}

.message-meta {
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.message-content {
  white-space: pre-wrap;
  line-height: 1.7;
  color: #dce8f0;
  font-size: 14px;
}

.thinking-line {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #8fb6d8;
  font-size: 13px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #00d4ff;
  animation: pulse 1.1s ease-in-out infinite;
}

@keyframes pulse {
  50% { opacity: 0.35; transform: scale(1.5); }
}

.tool-call-list,
.citation-list,
.doc-types {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.tool-call {
  display: grid;
  grid-template-columns: auto minmax(160px, 1fr) auto;
  gap: 8px;
  width: 100%;
  padding: 7px 9px;
  border-radius: 7px;
  color: #a9bac8;
  background: rgba(255, 255, 255, 0.04);
  font-size: 12px;
}

.tool-call.success span {
  color: #52d273;
}

.tool-call.error span {
  color: #ff6b6b;
}

.tool-call strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.tool-call em {
  color: #667788;
  font-style: normal;
}

.citation-pill,
.doc-types span {
  border-radius: 999px;
  padding: 3px 8px;
  color: #8ecbff;
  background: rgba(0, 212, 255, 0.09);
  font-size: 11px;
}

.composer {
  gap: 10px;
  padding: 12px;
  border-width: 1px 0 0 0;
  border-radius: 0;
}

.composer :deep(.el-textarea__inner) {
  color: #dce8f0;
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.1);
  box-shadow: none;
}

.context-panel {
  width: 360px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: auto;
}

.context-card {
  border-radius: 8px;
  padding: 14px;
}

.card-title {
  gap: 8px;
  color: #edf6fb;
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 12px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.summary-item {
  padding: 10px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
}

.summary-item span {
  display: block;
  color: #7f91a2;
  font-size: 11px;
  margin-bottom: 5px;
}

.summary-item strong {
  color: #f2f7fb;
  font-size: 22px;
}

.summary-item.warning strong {
  color: #ffaa00;
}

.tool-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tool-item {
  justify-content: space-between;
  gap: 8px;
  padding: 9px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
}

.tool-item div {
  min-width: 0;
}

.tool-item strong,
.tool-item span {
  display: block;
}

.tool-item strong {
  color: #dce8f0;
  font-size: 13px;
}

.tool-item span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-top: 3px;
}

.rag-message {
  line-height: 1.7;
}

@media (max-width: 980px) {
  .assistant-page {
    overflow: auto;
  }

  .assistant-header,
  .assistant-shell {
    flex-direction: column;
  }

  .assistant-shell {
    height: auto;
  }

  .context-panel {
    width: 100%;
  }

  .header-actions {
    flex-wrap: wrap;
  }
}
</style>
