<template>
  <main class="business-page" v-loading="loading && !overview">
    <header class="business-header">
      <div class="brand-block">
        <div class="brand-mark">
          <el-icon><DataBoard /></el-icon>
        </div>
        <div>
          <h1>{{ overview?.parkName || '智慧农业示范园区' }}</h1>
          <p>业务子系统验收视图</p>
        </div>
      </div>
      <div class="header-actions">
        <span>{{ updateText }}</span>
        <el-button :icon="Refresh" circle size="small" plain :loading="loading" @click="loadOverview" />
        <el-button :icon="Monitor" size="small" plain @click="router.push('/monitor')">大屏</el-button>
        <el-button :icon="Back" size="small" plain @click="router.push('/')">返回</el-button>
      </div>
    </header>

    <section class="summary-grid" v-if="overview">
      <article class="summary-card">
        <span>总体完成度</span>
        <strong>{{ overview.summary.completionRate.toFixed(1) }}%</strong>
      </article>
      <article class="summary-card">
        <span>验收评分</span>
        <strong>{{ overview.summary.overallScore.toFixed(1) }}</strong>
      </article>
      <article class="summary-card">
        <span>部分完成</span>
        <strong>{{ overview.summary.partialCount }}/{{ overview.summary.systemTotal }}</strong>
      </article>
      <article class="summary-card warning">
        <span>未确认告警</span>
        <strong>{{ overview.summary.unackedAlerts }}</strong>
      </article>
    </section>

    <section class="system-grid" v-if="overview">
      <article
        v-for="system in overview.subsystems"
        :key="system.key"
        class="system-panel"
        :class="[system.status, system.implementationLevel]"
      >
        <div class="system-head">
          <div>
            <h2>{{ system.name }}</h2>
            <p>{{ system.objective }}</p>
          </div>
          <el-tag :type="levelTagType(system.implementationLevel)" effect="dark" round>
            {{ levelLabel(system.implementationLevel) }}
          </el-tag>
        </div>

        <div class="progress-row">
          <span>完成度</span>
          <el-progress
            :percentage="Math.round(system.completionRate)"
            :status="progressStatus(system.status)"
            :stroke-width="8"
          />
        </div>

        <div class="metric-grid">
          <div v-for="metric in system.metrics" :key="metric.label + metric.key" class="metric-pill" :class="metric.status">
            <span>{{ metric.label }}</span>
            <strong>{{ metricValue(metric) }}</strong>
          </div>
        </div>

        <div class="workflow-list">
          <div v-for="item in system.workflows" :key="item.name" class="workflow-item">
            <span class="state-dot" :class="item.state"></span>
            <div>
              <strong>{{ item.name }}</strong>
              <p>{{ item.description }}</p>
            </div>
          </div>
        </div>

        <div class="risk-block">
          <div class="block-title">未完成项</div>
          <ul>
            <li v-for="gap in system.gaps" :key="gap">{{ gap }}</li>
          </ul>
        </div>

        <div class="alert-strip" v-if="system.alerts.length > 0">
          <span>告警</span>
          <strong>{{ system.alerts[0].message }}</strong>
        </div>
      </article>
    </section>

    <section class="empty-state" v-else-if="!loading">
      <el-icon><DataBoard /></el-icon>
      <p>业务子系统数据暂不可用</p>
      <el-button :icon="Refresh" plain @click="loadOverview">重新加载</el-button>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back, DataBoard, Monitor, Refresh } from '@element-plus/icons-vue'
import { fetchBusinessOverview, type BusinessMetric, type BusinessOverview } from '@/services/businessService'

const router = useRouter()
const overview = ref<BusinessOverview | null>(null)
const loading = ref(false)
let refreshTimer: ReturnType<typeof setInterval> | null = null

const updateText = computed(() => {
  if (!overview.value?.updatedAt) return '等待数据'
  return `更新 ${new Date(overview.value.updatedAt).toLocaleTimeString('zh-CN')}`
})

async function loadOverview() {
  loading.value = true
  try {
    const data = await fetchBusinessOverview()
    if (data) {
      overview.value = data
    } else {
      ElMessage.warning('业务中心数据返回为空')
    }
  } catch {
    ElMessage.error('业务中心数据加载失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}

function metricValue(metric: BusinessMetric): string {
  if (metric.status === 'missing') return '未接入'
  if (metric.key === 'status') return metric.value >= 1 ? '在线' : '离线'
  const digits = Math.abs(metric.value) >= 100 ? 0 : 1
  return `${metric.value.toFixed(digits)}${metric.unit ? ' ' + metric.unit : ''}`
}

function levelLabel(level: string): string {
  const labels: Record<string, string> = {
    ready: '可演示',
    partial: '部分完成',
    missing: '缺失'
  }
  return labels[level] || level
}

function levelTagType(level: string): 'success' | 'warning' | 'danger' | 'info' {
  if (level === 'ready') return 'success'
  if (level === 'partial') return 'warning'
  if (level === 'missing') return 'danger'
  return 'info'
}

function progressStatus(status: string): 'success' | 'warning' | 'exception' | undefined {
  if (status === 'normal') return 'success'
  if (status === 'warning') return 'warning'
  if (status === 'critical') return 'exception'
  return undefined
}

onMounted(() => {
  loadOverview()
  refreshTimer = setInterval(loadOverview, 15000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.business-page {
  width: 100%;
  height: 100vh;
  overflow: auto;
  padding: 18px;
  color: #d7e1ea;
  background:
    linear-gradient(180deg, rgba(8, 18, 30, 0.98), rgba(5, 9, 14, 1)),
    repeating-linear-gradient(90deg, rgba(255,255,255,0.025) 0, rgba(255,255,255,0.025) 1px, transparent 1px, transparent 76px);
}

.business-header,
.brand-block,
.header-actions,
.system-head,
.progress-row,
.alert-strip,
.workflow-item {
  display: flex;
  align-items: center;
}

.business-header {
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
  border: 1px solid rgba(77, 163, 255, 0.28);
  border-radius: 8px;
  color: #4da3ff;
  background: rgba(77, 163, 255, 0.1);
}

.brand-block h1 {
  margin: 0;
  color: #f1f6fa;
  font-size: 22px;
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: 0;
}

.brand-block p {
  margin: 5px 0 0;
  color: #8fa1b2;
  font-size: 13px;
}

.header-actions {
  gap: 10px;
  color: #9aa8b7;
  font-size: 13px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.header-actions :deep(.el-button) {
  --el-button-bg-color: rgba(255,255,255,0.05);
  --el-button-border-color: rgba(255,255,255,0.14);
  --el-button-text-color: #d7e1ea;
  --el-button-hover-bg-color: rgba(77,163,255,0.14);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(160px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.summary-card,
.system-panel {
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 8px;
  background: rgba(8, 20, 32, 0.78);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.25);
}

.summary-card {
  min-height: 96px;
  padding: 16px;
  border-left: 3px solid #39d98a;
}

.summary-card.warning {
  border-left-color: #ffb020;
}

.summary-card span {
  display: block;
  color: #93a6b8;
  font-size: 13px;
}

.summary-card strong {
  display: block;
  margin-top: 12px;
  color: #f1f6fa;
  font-size: 30px;
  line-height: 1;
}

.system-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(280px, 1fr));
  gap: 12px;
}

.system-panel {
  min-height: 420px;
  padding: 16px;
  border-left: 3px solid #39d98a;
}

.system-panel.warning {
  border-left-color: #ffb020;
}

.system-panel.critical {
  border-left-color: #ff4d4f;
}

.system-head {
  justify-content: space-between;
  gap: 12px;
}

.system-head h2 {
  margin: 0;
  color: #f1f6fa;
  font-size: 17px;
  line-height: 1.25;
  letter-spacing: 0;
}

.system-head p {
  margin: 8px 0 0;
  color: #8fa1b2;
  font-size: 12px;
  line-height: 1.55;
}

.progress-row {
  gap: 10px;
  margin-top: 14px;
  color: #93a6b8;
  font-size: 12px;
}

.progress-row :deep(.el-progress) {
  flex: 1;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 14px;
}

.metric-pill {
  min-height: 66px;
  padding: 10px;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  background: rgba(255,255,255,0.035);
}

.metric-pill span {
  display: block;
  color: #90a1b2;
  font-size: 12px;
}

.metric-pill strong {
  display: block;
  margin-top: 8px;
  color: #f1f6fa;
  font-size: 18px;
  line-height: 1.1;
  word-break: break-word;
}

.metric-pill.warning strong,
.metric-pill.missing strong {
  color: #ffb020;
}

.metric-pill.critical strong {
  color: #ff6b6b;
}

.workflow-list {
  margin-top: 14px;
}

.workflow-item {
  align-items: flex-start;
  gap: 9px;
  padding: 9px 0;
  border-top: 1px solid rgba(255,255,255,0.06);
}

.state-dot {
  width: 9px;
  height: 9px;
  margin-top: 5px;
  border-radius: 50%;
  background: #39d98a;
  flex-shrink: 0;
}

.state-dot.partial {
  background: #ffb020;
}

.state-dot.missing {
  background: #ff4d4f;
}

.workflow-item strong {
  color: #dce6ef;
  font-size: 13px;
}

.workflow-item p {
  margin: 4px 0 0;
  color: #8797a7;
  font-size: 12px;
  line-height: 1.45;
}

.risk-block {
  margin-top: 10px;
  padding: 10px;
  border-radius: 8px;
  background: rgba(255, 176, 32, 0.08);
}

.block-title {
  color: #ffcf7a;
  font-size: 12px;
  font-weight: 700;
}

.risk-block ul {
  margin: 8px 0 0 16px;
  color: #c4d0dc;
  font-size: 12px;
  line-height: 1.6;
}

.alert-strip {
  gap: 8px;
  margin-top: 12px;
  padding: 10px;
  border: 1px solid rgba(255, 77, 79, 0.24);
  border-radius: 8px;
  color: #ffb4b4;
  background: rgba(255, 77, 79, 0.08);
}

.alert-strip span {
  font-size: 12px;
  color: #ff6b6b;
  font-weight: 700;
}

.alert-strip strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
}

.empty-state {
  min-height: 320px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 14px;
  color: #93a6b8;
}

.empty-state .el-icon {
  color: #4da3ff;
  font-size: 42px;
}

@media (max-width: 1280px) {
  .summary-grid,
  .system-grid {
    grid-template-columns: repeat(2, minmax(260px, 1fr));
  }
}

@media (max-width: 760px) {
  .business-page {
    padding: 12px;
  }

  .business-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .summary-grid,
  .system-grid,
  .metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>
