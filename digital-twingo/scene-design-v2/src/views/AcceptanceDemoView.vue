<template>
  <main class="acceptance-page" v-loading="loading && !acceptance">
    <header class="acceptance-header">
      <div class="brand-block">
        <div class="brand-mark">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div>
          <h1>Phase 6 综合验收</h1>
          <p>{{ acceptance?.sceneName || '番茄温室 MVP' }}</p>
        </div>
      </div>
      <div class="header-actions">
        <span v-if="acceptance" class="status-pill" :class="{ failed: !acceptance.overallPassed }">
          {{ acceptance.overallPassed ? '验收通过' : '存在缺口' }}
        </span>
        <span>{{ runTimeText }}</span>
        <el-button :icon="Refresh" size="small" plain :loading="loading" @click="loadAcceptance">重新验收</el-button>
        <el-button :icon="Back" size="small" plain @click="router.push('/')">返回场景</el-button>
      </div>
    </header>

    <section v-if="acceptance" class="hero-band">
      <div class="prompt-box">
        <span>固定验收提示词</span>
        <strong>{{ acceptance.prompt }}</strong>
      </div>
      <div class="archive-box" :class="{ ready: acceptance.archiveReadiness.ready }">
        <span>归档准备</span>
        <strong>{{ acceptance.archiveReadiness.ready ? 'Ready' : 'Blocked' }}</strong>
        <small>{{ acceptance.archiveReadiness.nextAction }}</small>
      </div>
    </section>

    <section v-if="acceptance" class="count-grid">
      <article v-for="item in countItems" :key="item.key" class="count-card" :class="{ failed: !item.passed }">
        <span>{{ item.label }}</span>
        <strong>{{ item.actual }} / {{ item.expected }}</strong>
        <small>{{ item.passed ? '匹配' : '需修正' }}</small>
      </article>
    </section>

    <section v-if="acceptance" class="main-grid">
      <section class="panel steps-panel">
        <div class="panel-title">
          <span>端到端演示步骤</span>
          <strong>{{ passedStepCount }}/{{ acceptance.steps.length }}</strong>
        </div>
        <div class="step-list">
          <article v-for="step in acceptance.steps" :key="step.key" class="step-item" :class="{ failed: !step.passed }">
            <div>
              <span>{{ step.title }}</span>
              <strong>{{ step.actual }}</strong>
            </div>
            <p>{{ step.target }}</p>
            <small v-if="step.evidence">{{ step.evidence }}</small>
          </article>
        </div>
      </section>

      <section class="panel metrics-panel">
        <div class="panel-title">
          <span>成功指标矩阵</span>
          <strong>{{ passedMetricCount }}/{{ acceptance.successMetrics.length }}</strong>
        </div>
        <div class="metric-list">
          <article v-for="metric in acceptance.successMetrics" :key="metric.key" class="metric-row" :class="{ failed: !metric.passed }">
            <div>
              <span>{{ metric.label }}</span>
              <small>{{ metric.source }}</small>
            </div>
            <strong>{{ metric.actual }}</strong>
            <p>{{ metric.target }}</p>
          </article>
        </div>
      </section>

      <section class="panel trace-panel">
        <div class="panel-title">
          <span>Agent Trace</span>
          <strong>{{ traceSteps.length }} steps</strong>
        </div>
        <div class="trace-list">
          <article v-for="step in traceSteps" :key="step.stepId" class="trace-item" :class="step.status">
            <div>
              <span>{{ step.agent }}</span>
              <strong>{{ step.tool }}</strong>
            </div>
            <small>{{ flowLabel(step.flow) }} / {{ categoryLabel(step.toolCategory) }} / {{ step.durationMs }} ms</small>
            <p v-if="step.outputSummary">{{ step.outputSummary }}</p>
          </article>
        </div>
      </section>

      <section class="panel routing-panel">
        <div class="panel-title">
          <span>资产路由与补资产任务</span>
          <strong>{{ acceptance.semanticBuild.missingAssets.length }}</strong>
        </div>
        <div class="asset-list">
          <article v-for="asset in acceptance.semanticBuild.missingAssets" :key="asset.assetKey" class="asset-item">
            <div>
              <span>{{ asset.name }}</span>
              <strong>{{ asset.routing?.strategy || 'placeholder' }}</strong>
            </div>
            <p>{{ asset.routing?.routingReason || asset.reason }}</p>
            <small>任务 {{ asset.generation?.taskId || '未创建' }} / {{ asset.generation?.status || 'unknown' }}</small>
          </article>
        </div>
      </section>

      <section class="panel object-panel">
        <div class="panel-title">
          <span>点选对象上下文</span>
          <strong>{{ acceptance.greenhouseObject?.name || '温室对象' }}</strong>
        </div>
        <div class="object-grid">
          <div>
            <span>传感器</span>
            <strong>{{ relationCount('sensors') }}</strong>
          </div>
          <div>
            <span>设备</span>
            <strong>{{ relationCount('devices') }}</strong>
          </div>
          <div>
            <span>摄像头</span>
            <strong>{{ relationCount('cameras') }}</strong>
          </div>
          <div>
            <span>事件</span>
            <strong>{{ relationCount('events') }}</strong>
          </div>
        </div>
        <div class="device-context">
          <strong>{{ acceptance.abnormalDevice?.name || '异常设备' }}</strong>
          <p>{{ acceptance.abnormalContext.recommendation }}</p>
          <div class="latest-grid">
            <span v-for="item in latestValues" :key="item.metricKey">
              {{ item.label }} <strong>{{ formatValue(item.value, item.unit) }}</strong>
            </span>
          </div>
        </div>
      </section>

      <section class="panel validation-panel">
        <div class="panel-title">
          <span>场景校验问题</span>
          <strong>{{ acceptance.bindingValidation.summary.bindingRate.toFixed(1) }}%</strong>
        </div>
        <div class="issue-list">
          <article v-for="issue in acceptance.issues" :key="`${issue.category}-${issue.source}-${issue.message}`" class="issue-item" :class="issue.severity">
            <span>{{ issue.category }}</span>
            <p>{{ issue.message }}</p>
            <small>{{ issue.source }}</small>
          </article>
        </div>
      </section>

      <section class="panel report-panel">
        <div class="panel-title">
          <span>温室日报摘要</span>
          <strong>{{ acceptance.reportSource.date }}</strong>
        </div>
        <div class="report-section">
          <span>环境摘要</span>
          <p>{{ acceptance.reportSource.environment.summary }}</p>
        </div>
        <div class="report-section">
          <span>设备状态</span>
          <p>{{ acceptance.reportSource.deviceStatus.summary }}</p>
        </div>
        <div class="report-stats">
          <div>
            <span>告警</span>
            <strong>{{ acceptance.reportSource.alerts.length }}</strong>
          </div>
          <div>
            <span>灌溉</span>
            <strong>{{ acceptance.reportSource.irrigationEvents.length }}</strong>
          </div>
        </div>
        <ul class="recommend-list">
          <li v-for="item in acceptance.reportSource.recommendations" :key="item">{{ item }}</li>
        </ul>
      </section>
    </section>

    <section v-else-if="!loading" class="empty-state">
      <el-icon><Warning /></el-icon>
      <p>综合验收数据暂不可用</p>
      <el-button :icon="Refresh" plain @click="loadAcceptance">重新加载</el-button>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back, CircleCheck, Refresh, Warning } from '@element-plus/icons-vue'
import {
  fetchTomatoGreenhouseAcceptance,
  type AcceptanceCount,
  type TomatoGreenhouseAcceptance
} from '@/services/acceptanceService'
import type { FarmMetricLatestValue } from '@/services/farmMemoryService'

const router = useRouter()
const acceptance = ref<TomatoGreenhouseAcceptance | null>(null)
const loading = ref(false)

const countItems = computed(() => {
  const counts = acceptance.value?.modelCounts || {}
  const order = ['tomato', 'greenhouse', 'weather_station', 'irrigation', 'camera', 'sensor']
  return order
    .filter(key => counts[key])
    .map(key => ({ key, ...counts[key] as AcceptanceCount }))
})

const traceSteps = computed(() => acceptance.value?.semanticBuild.agentTrace?.steps || [])
const passedStepCount = computed(() => acceptance.value?.steps.filter(item => item.passed).length || 0)
const passedMetricCount = computed(() => acceptance.value?.successMetrics.filter(item => item.passed).length || 0)
const latestValues = computed<FarmMetricLatestValue[]>(() => Object.values(acceptance.value?.abnormalContext.latest.values || {}))
const runTimeText = computed(() => {
  if (!acceptance.value?.runAt) return '等待验收'
  return `更新 ${new Date(acceptance.value.runAt).toLocaleString('zh-CN')}`
})

async function loadAcceptance() {
  loading.value = true
  try {
    acceptance.value = await fetchTomatoGreenhouseAcceptance()
  } catch (err: any) {
    ElMessage.error(err?.message || '综合验收数据加载失败')
  } finally {
    loading.value = false
  }
}

function relationCount(group: string): number {
  return acceptance.value?.greenhouseContext.relations[group]?.length || 0
}

function formatValue(value: number, unit: string): string {
  return `${Number(value).toFixed(Number.isInteger(value) ? 0 : 1)}${unit || ''}`
}

function flowLabel(flow = ''): string {
  const labels: Record<string, string> = {
    semantic_construction: '语义搭建',
    asset_routing: '资产路由',
    object_binding: '对象绑定',
    validation: '校验'
  }
  return labels[flow] || flow || '调度'
}

function categoryLabel(category = ''): string {
  const labels: Record<string, string> = {
    'read-only': '只读',
    'controlled-write': '受控写',
    prohibited: '禁止'
  }
  return labels[category] || category
}

onMounted(loadAcceptance)
</script>

<style scoped>
.acceptance-page {
  width: 100%;
  min-height: 100vh;
  padding: 18px;
  color: #d7e1ea;
  background:
    linear-gradient(180deg, rgba(8, 18, 30, 0.98), rgba(4, 10, 16, 1)),
    repeating-linear-gradient(90deg, rgba(255,255,255,0.03) 0, rgba(255,255,255,0.03) 1px, transparent 1px, transparent 80px);
}

.acceptance-header,
.brand-block,
.header-actions,
.hero-band,
.panel-title,
.step-item > div,
.asset-item > div,
.trace-item > div,
.report-stats,
.metric-row {
  display: flex;
  align-items: center;
}

.acceptance-header {
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
  border: 1px solid rgba(57, 217, 138, 0.32);
  border-radius: 8px;
  color: #39d98a;
  background: rgba(57, 217, 138, 0.1);
}

.brand-block h1 {
  margin: 0;
  color: #f1f6fa;
  font-size: 22px;
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: 0;
}

.brand-block p,
.header-actions {
  color: #8fa1b2;
  font-size: 13px;
}

.brand-block p {
  margin: 5px 0 0;
}

.header-actions {
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.header-actions :deep(.el-button) {
  --el-button-bg-color: rgba(255,255,255,0.05);
  --el-button-border-color: rgba(255,255,255,0.14);
  --el-button-text-color: #d7e1ea;
  --el-button-hover-bg-color: rgba(77,163,255,0.14);
}

.status-pill {
  padding: 5px 10px;
  border: 1px solid rgba(57,217,138,0.42);
  border-radius: 999px;
  color: #39d98a;
  background: rgba(57,217,138,0.12);
}

.status-pill.failed {
  border-color: rgba(255,176,32,0.42);
  color: #ffb020;
  background: rgba(255,176,32,0.12);
}

.hero-band {
  gap: 12px;
  margin-bottom: 12px;
}

.prompt-box,
.archive-box,
.count-card,
.panel {
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 8px;
  background: rgba(8, 20, 32, 0.78);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.24);
}

.prompt-box,
.archive-box {
  min-height: 88px;
  padding: 16px;
}

.prompt-box {
  flex: 1;
}

.archive-box {
  width: min(420px, 38vw);
}

.prompt-box span,
.archive-box span,
.count-card span,
.report-section span,
.report-stats span {
  color: #93a6b8;
  font-size: 12px;
}

.prompt-box strong,
.archive-box strong {
  display: block;
  margin-top: 8px;
  color: #f1f6fa;
  font-size: 18px;
  line-height: 1.35;
}

.archive-box.ready strong {
  color: #39d98a;
}

.archive-box small {
  display: block;
  margin-top: 6px;
  color: #8fa1b2;
  line-height: 1.35;
}

.count-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(120px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.count-card {
  min-height: 98px;
  padding: 14px;
  border-left: 3px solid #39d98a;
}

.count-card.failed {
  border-left-color: #ffb020;
}

.count-card strong {
  display: block;
  margin-top: 10px;
  color: #f1f6fa;
  font-size: 26px;
  line-height: 1;
}

.count-card small {
  display: block;
  margin-top: 10px;
  color: #39d98a;
}

.count-card.failed small {
  color: #ffb020;
}

.main-grid {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) minmax(360px, 1.2fr) minmax(320px, 1fr);
  grid-template-areas:
    "steps metrics trace"
    "routing object validation"
    "report report validation";
  gap: 12px;
}

.panel {
  min-width: 0;
  padding: 14px;
}

.steps-panel { grid-area: steps; }
.metrics-panel { grid-area: metrics; }
.trace-panel { grid-area: trace; }
.routing-panel { grid-area: routing; }
.object-panel { grid-area: object; }
.validation-panel { grid-area: validation; }
.report-panel { grid-area: report; }

.panel-title {
  justify-content: space-between;
  gap: 10px;
  min-height: 28px;
  margin-bottom: 10px;
  color: #f1f6fa;
  font-size: 15px;
  font-weight: 650;
}

.panel-title strong {
  color: #39d98a;
  font-size: 13px;
}

.step-list,
.metric-list,
.trace-list,
.asset-list,
.issue-list {
  display: grid;
  gap: 8px;
}

.step-item,
.metric-row,
.trace-item,
.asset-item,
.issue-item,
.device-context,
.report-section {
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  background: rgba(255,255,255,0.035);
}

.step-item,
.trace-item,
.asset-item,
.issue-item,
.device-context,
.report-section {
  padding: 10px;
}

.step-item {
  border-left: 3px solid #39d98a;
}

.step-item.failed {
  border-left-color: #ffb020;
}

.step-item > div,
.asset-item > div,
.trace-item > div {
  justify-content: space-between;
  gap: 10px;
}

.step-item span,
.asset-item span,
.trace-item span,
.metric-row span,
.issue-item span {
  color: #f1f6fa;
  font-size: 13px;
  font-weight: 650;
}

.step-item strong,
.asset-item strong,
.trace-item strong,
.metric-row strong {
  color: #39d98a;
  font-size: 12px;
}

.step-item p,
.asset-item p,
.trace-item p,
.metric-row p,
.issue-item p,
.device-context p,
.report-section p {
  margin: 7px 0 0;
  color: #9aa8b7;
  font-size: 12px;
  line-height: 1.45;
}

.step-item small,
.asset-item small,
.trace-item small,
.metric-row small,
.issue-item small {
  display: block;
  margin-top: 6px;
  color: #708294;
  font-size: 11px;
  line-height: 1.35;
}

.metric-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 6px 12px;
  padding: 10px;
  align-items: start;
}

.metric-row p {
  grid-column: 1 / -1;
}

.metric-row.failed strong {
  color: #ffb020;
}

.trace-list,
.issue-list {
  max-height: 520px;
  overflow: auto;
}

.trace-item p {
  max-height: 58px;
  overflow: hidden;
}

.object-grid,
.latest-grid,
.report-stats {
  display: grid;
  gap: 8px;
}

.object-grid {
  grid-template-columns: repeat(4, 1fr);
  margin-bottom: 10px;
}

.object-grid div,
.report-stats div {
  padding: 10px;
  border-radius: 8px;
  background: rgba(255,255,255,0.045);
}

.object-grid span,
.object-grid strong,
.report-stats span,
.report-stats strong {
  display: block;
}

.object-grid strong,
.report-stats strong {
  margin-top: 5px;
  color: #f1f6fa;
  font-size: 21px;
}

.device-context strong {
  color: #f1f6fa;
}

.latest-grid {
  grid-template-columns: repeat(3, 1fr);
  margin-top: 10px;
}

.latest-grid span {
  padding: 8px;
  border-radius: 8px;
  color: #93a6b8;
  font-size: 12px;
  background: rgba(255,255,255,0.045);
}

.latest-grid strong {
  display: block;
  margin-top: 4px;
  color: #39d98a;
}

.issue-item.warning {
  border-color: rgba(255,176,32,0.22);
}

.issue-item.error {
  border-color: rgba(255,77,79,0.28);
}

.report-stats {
  grid-template-columns: repeat(2, 1fr);
  margin: 10px 0;
}

.recommend-list {
  display: grid;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.recommend-list li {
  padding: 9px 10px;
  border-radius: 8px;
  color: #d7e1ea;
  font-size: 12px;
  background: rgba(57,217,138,0.08);
}

.empty-state {
  display: grid;
  place-items: center;
  gap: 12px;
  min-height: 60vh;
  color: #8fa1b2;
}

@media (max-width: 1180px) {
  .count-grid {
    grid-template-columns: repeat(3, minmax(120px, 1fr));
  }

  .main-grid {
    grid-template-columns: 1fr;
    grid-template-areas:
      "steps"
      "metrics"
      "trace"
      "routing"
      "object"
      "validation"
      "report";
  }
}

@media (max-width: 760px) {
  .acceptance-page {
    padding: 12px;
  }

  .acceptance-header,
  .hero-band {
    align-items: stretch;
    flex-direction: column;
  }

  .archive-box {
    width: 100%;
  }

  .count-grid,
  .object-grid,
  .latest-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
