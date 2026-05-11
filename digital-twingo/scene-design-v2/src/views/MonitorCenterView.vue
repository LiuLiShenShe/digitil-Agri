<template>
  <main class="monitor-page" v-loading="loading && !dashboard">
    <header class="monitor-header">
      <div class="brand-block">
        <div class="brand-mark">
          <el-icon><Monitor /></el-icon>
        </div>
        <div>
          <h1>{{ dashboard?.overview.parkName || '智慧农业示范园区' }}</h1>
          <p>监控中心大屏</p>
        </div>
      </div>
      <div class="header-status">
        <span class="live-dot"></span>
        <span>{{ lastUpdateText }}</span>
        <el-tooltip content="刷新" placement="bottom">
          <el-button :icon="Refresh" circle size="small" plain :loading="loading" @click="loadDashboard" />
        </el-tooltip>
        <el-tooltip content="全屏" placement="bottom">
          <el-button :icon="FullScreen" circle size="small" plain @click="toggleFullscreen" />
        </el-tooltip>
        <el-button :icon="DataBoard" size="small" plain @click="router.push('/business')">业务中心</el-button>
        <el-button :icon="Back" size="small" plain @click="router.push('/')">返回</el-button>
      </div>
    </header>

    <section class="metrics-row" v-if="dashboard">
      <article
        v-for="metric in dashboard.keyMetrics"
        :key="metric.key"
        class="metric-card"
        :class="metric.status"
      >
        <div class="metric-top">
          <span>{{ metric.label }}</span>
          <el-icon><DataAnalysis /></el-icon>
        </div>
        <div class="metric-value">
          {{ formatNumber(metric.value) }}
          <small>{{ metric.unit }}</small>
        </div>
        <div class="metric-foot" :class="{ down: metric.delta < 0 }">
          {{ metric.delta >= 0 ? '+' : '' }}{{ metric.delta.toFixed(1) }}%
        </div>
      </article>
    </section>

    <section class="dashboard-grid" v-if="dashboard">
      <div class="scene-panel">
        <div class="panel-title">
          <span>园区总览</span>
          <strong>{{ dashboard.overview.onlineRate.toFixed(1) }}% 在线</strong>
        </div>
        <MonitorScenePreview
          class="scene-preview"
          :devices="dashboard.deviceStatus"
          :heatmap="dashboard.yieldAnalysis.heatmap"
        />
        <div class="overview-strip">
          <div>
            <span>设备</span>
            <strong>{{ dashboard.overview.deviceTotal }}</strong>
          </div>
          <div>
            <span>在线</span>
            <strong>{{ dashboard.overview.onlineCount }}</strong>
          </div>
          <div>
            <span>未确认告警</span>
            <strong>{{ dashboard.overview.unackedAlerts }}</strong>
          </div>
          <div>
            <span>环境评分</span>
            <strong>{{ dashboard.environment.score.toFixed(1) }}</strong>
          </div>
        </div>
      </div>

      <aside class="device-panel">
        <div class="panel-title">
          <span>设备状态矩阵</span>
          <el-icon><Connection /></el-icon>
        </div>
        <div class="device-matrix">
          <button
            v-for="device in dashboard.deviceStatus"
            :key="device.deviceId"
            class="device-tile"
            :class="device.status"
            @click="selectedDeviceId = device.deviceId"
          >
            <span class="device-indicator"></span>
            <span class="device-name">{{ device.deviceName }}</span>
            <span class="device-type">{{ deviceTypeLabel(device.deviceType) }}</span>
          </button>
        </div>
        <div class="device-detail">
          <div class="detail-name">{{ selectedDevice?.deviceName || '选择设备' }}</div>
          <div class="detail-grid" v-if="selectedDevice">
            <span v-for="(value, key) in selectedDevice.metrics" :key="key">
              {{ metricLabel(key) }} <strong>{{ value.toFixed(1) }}</strong>
            </span>
          </div>
        </div>
      </aside>

      <aside class="alert-panel">
        <div class="panel-title">
          <span>告警列表</span>
          <el-icon><Warning /></el-icon>
        </div>
        <div class="alert-list">
          <article
            v-for="alert in dashboard.recentAlerts"
            :key="alert.id"
            class="alert-item"
            :class="[alert.severity, { acknowledged: alert.acknowledged }]"
          >
            <span class="alert-level">{{ severityLabel(alert.severity) }}</span>
            <div>
              <strong>{{ alert.deviceId }}</strong>
              <p>{{ alert.message }}</p>
              <time>{{ formatTime(alert.createdAt) }}</time>
            </div>
          </article>
          <div v-if="dashboard.recentAlerts.length === 0" class="empty-state">暂无告警</div>
        </div>
      </aside>

      <section class="chart-panel energy-panel">
        <div class="panel-title">
          <span>能耗管理</span>
          <strong>{{ dashboard.energy.todayTotal.toFixed(1) }}</strong>
        </div>
        <div ref="energyChartRef" class="chart-box"></div>
      </section>

      <section class="chart-panel yield-panel">
        <div class="panel-title">
          <span>产量分析</span>
          <strong>{{ dashboard.yieldAnalysis.total.toFixed(1) }} {{ dashboard.yieldAnalysis.unit }}</strong>
        </div>
        <div class="yield-content">
          <div ref="yieldChartRef" class="chart-box heat-chart"></div>
          <div class="yield-list">
            <div v-for="area in dashboard.yieldAnalysis.areas" :key="area.name" class="yield-row">
              <span>{{ area.name }}</span>
              <strong>{{ area.yield.toFixed(1) }}</strong>
              <el-progress :percentage="Math.round(area.rate * 100)" :show-text="false" />
            </div>
          </div>
        </div>
      </section>

      <section class="report-panel">
        <div class="panel-title">
          <span>环境日报</span>
          <el-icon><Document /></el-icon>
        </div>
        <div class="report-score">
          <div>
            <strong>{{ dashboard.environment.score.toFixed(1) }}</strong>
            <span>{{ dashboard.environment.level }}</span>
          </div>
          <p>{{ dashboard.environment.summary }}</p>
        </div>
        <div ref="envChartRef" class="chart-box report-chart"></div>
        <ul class="recommend-list">
          <li v-for="item in dashboard.environment.recommendations" :key="item">{{ item }}</li>
        </ul>
      </section>
    </section>

    <section class="empty-dashboard" v-else-if="!loading">
      <el-icon><Monitor /></el-icon>
      <p>监控数据暂不可用</p>
      <el-button :icon="Refresh" plain @click="loadDashboard">重新加载</el-button>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Back,
  Connection,
  DataBoard,
  DataAnalysis,
  Document,
  FullScreen,
  Monitor,
  Refresh,
  Warning
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import MonitorScenePreview from '@/components/MonitorScenePreview.vue'
import { fetchMonitorDashboard, type MonitorDashboard } from '@/services/monitorService'

const router = useRouter()
const dashboard = ref<MonitorDashboard | null>(null)
const loading = ref(false)
const selectedDeviceId = ref<string | null>(null)
const energyChartRef = ref<HTMLElement>()
const yieldChartRef = ref<HTMLElement>()
const envChartRef = ref<HTMLElement>()
let energyChart: echarts.ECharts | null = null
let yieldChart: echarts.ECharts | null = null
let envChart: echarts.ECharts | null = null
let refreshTimer: ReturnType<typeof setInterval> | null = null

const selectedDevice = computed(() => {
  const list = dashboard.value?.deviceStatus || []
  return list.find((device) => device.deviceId === selectedDeviceId.value) || list[0] || null
})

const lastUpdateText = computed(() => {
  if (!dashboard.value?.updatedAt) return '等待数据'
  return `更新 ${new Date(dashboard.value.updatedAt).toLocaleTimeString('zh-CN')}`
})

async function loadDashboard() {
  loading.value = true
  try {
    const data = await fetchMonitorDashboard()
    if (data) {
      dashboard.value = data
      if (!selectedDeviceId.value && data.deviceStatus.length > 0) {
        selectedDeviceId.value = data.deviceStatus[0].deviceId
      }
      await nextTick()
      renderCharts()
    } else {
      ElMessage.warning('监控数据返回为空')
    }
  } catch {
    ElMessage.error('监控中心数据加载失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}

function renderCharts() {
  renderEnergyChart()
  renderYieldChart()
  renderEnvironmentChart()
}

function renderEnergyChart() {
  if (!energyChartRef.value || !dashboard.value) return
  if (!energyChart) {
    energyChart = echarts.init(energyChartRef.value, 'dark')
  }
  const bars = dashboard.value.energy.bars
  const totals = bars.map((item) => item.water + item.electricity + item.gas)
  energyChart.setOption({
    backgroundColor: 'transparent',
    color: ['#39d98a', '#4da3ff', '#ffb020', '#f97066'],
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(6,16,26,0.96)', borderColor: 'rgba(255,255,255,0.12)' },
    legend: { top: 0, right: 0, textStyle: { color: '#9aa8b7' } },
    grid: { top: 38, left: 42, right: 24, bottom: 34 },
    xAxis: {
      type: 'category',
      data: bars.map((item) => item.name),
      axisLabel: { color: '#8a99a8', fontSize: 11 },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.12)' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#8a99a8', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.07)', type: 'dashed' } }
    },
    series: [
      { name: '水', type: 'bar', stack: 'total', barWidth: 16, data: bars.map((item) => item.water) },
      { name: '电', type: 'bar', stack: 'total', data: bars.map((item) => item.electricity) },
      { name: '气', type: 'bar', stack: 'total', data: bars.map((item) => item.gas) },
      { name: '趋势', type: 'line', smooth: true, symbolSize: 6, data: totals }
    ]
  })
}

function renderYieldChart() {
  if (!yieldChartRef.value || !dashboard.value) return
  if (!yieldChart) {
    yieldChart = echarts.init(yieldChartRef.value, 'dark')
  }
  const heatmap = dashboard.value.yieldAnalysis.heatmap
  yieldChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: 'rgba(6,16,26,0.96)',
      borderColor: 'rgba(255,255,255,0.12)',
      formatter: (params: any) => {
        const item = heatmap[params.dataIndex]
        return `${item.area}<br/>产量指数 ${item.value.toFixed(1)}`
      }
    },
    grid: { top: 12, left: 24, right: 58, bottom: 24 },
    xAxis: {
      type: 'category',
      data: ['1', '2', '3', '4', '5', '6'],
      axisLabel: { color: '#8a99a8' },
      splitArea: { show: true }
    },
    yAxis: {
      type: 'category',
      data: ['A', 'B', 'C', 'D', 'E', 'F'],
      axisLabel: { color: '#8a99a8' },
      splitArea: { show: true }
    },
    visualMap: {
      min: 40,
      max: 100,
      calculable: true,
      right: 0,
      top: 'middle',
      itemWidth: 10,
      itemHeight: 120,
      textStyle: { color: '#8a99a8' },
      inRange: { color: ['#244331', '#4d8d4a', '#c5a940', '#f07a3f'] }
    },
    series: [{
      type: 'heatmap',
      data: heatmap.map((item) => [item.x, item.y, item.value]),
      emphasis: { itemStyle: { shadowBlur: 12, shadowColor: 'rgba(57,217,138,0.45)' } }
    }]
  })
}

function renderEnvironmentChart() {
  if (!envChartRef.value || !dashboard.value) return
  if (!envChart) {
    envChart = echarts.init(envChartRef.value, 'dark')
  }
  const hourly = dashboard.value.environment.hourly
  envChart.setOption({
    backgroundColor: 'transparent',
    color: ['#39d98a'],
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(6,16,26,0.96)', borderColor: 'rgba(255,255,255,0.12)' },
    grid: { top: 16, left: 34, right: 18, bottom: 26 },
    xAxis: {
      type: 'category',
      data: hourly.map((item) => item.time),
      axisLabel: { color: '#8a99a8', fontSize: 10 },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.12)' } }
    },
    yAxis: {
      type: 'value',
      min: 40,
      max: 100,
      axisLabel: { color: '#8a99a8', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.07)', type: 'dashed' } }
    },
    series: [{
      type: 'line',
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 3 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(57,217,138,0.32)' },
          { offset: 1, color: 'rgba(57,217,138,0.02)' }
        ])
      },
      data: hourly.map((item) => item.value)
    }]
  })
}

function resizeCharts() {
  energyChart?.resize()
  yieldChart?.resize()
  envChart?.resize()
}

function toggleFullscreen() {
  const root = document.documentElement
  if (!document.fullscreenElement) {
    root.requestFullscreen?.()
  } else {
    document.exitFullscreen?.()
  }
}

function formatNumber(value: number): string {
  if (value >= 1000) return value.toLocaleString('zh-CN', { maximumFractionDigits: 0 })
  return value.toFixed(value >= 100 ? 0 : 1)
}

function formatTime(value: string): string {
  return new Date(value).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function deviceTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    sensor: '传感器',
    camera: '摄像头',
    controller: '控制器',
    weather_station: '气象站'
  }
  return labels[type] || type
}

function severityLabel(severity: string): string {
  const labels: Record<string, string> = {
    info: '提示',
    warning: '预警',
    critical: '严重'
  }
  return labels[severity] || severity
}

function metricLabel(key: string): string {
  const labels: Record<string, string> = {
    temperature: '温度',
    humidity: '湿度',
    soilMoisture: '墒情',
    co2: 'CO2',
    lightIntensity: '光照',
    ph: 'pH',
    windSpeed: '风速',
    rainfall: '降雨',
    waterFlow: '流量',
    waterPressure: '压力',
    powerOutput: '功率',
    status: '状态'
  }
  return labels[key] || key
}

watch(dashboard, () => {
  nextTick(renderCharts)
})

onMounted(() => {
  loadDashboard()
  refreshTimer = setInterval(loadDashboard, 15000)
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  window.removeEventListener('resize', resizeCharts)
  energyChart?.dispose()
  yieldChart?.dispose()
  envChart?.dispose()
})
</script>

<style scoped>
.monitor-page {
  width: 100%;
  height: 100vh;
  overflow: auto;
  padding: 18px;
  color: #d7e1ea;
  background:
    linear-gradient(180deg, rgba(8, 18, 30, 0.98), rgba(4, 10, 16, 1)),
    repeating-linear-gradient(90deg, rgba(255,255,255,0.03) 0, rgba(255,255,255,0.03) 1px, transparent 1px, transparent 80px);
}

.monitor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  min-height: 58px;
  margin-bottom: 14px;
}

.brand-block,
.header-status,
.metric-top,
.panel-title,
.overview-strip,
.device-tile,
.alert-item,
.yield-row,
.report-score {
  display: flex;
  align-items: center;
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

.header-status {
  gap: 10px;
  color: #9aa8b7;
  font-size: 13px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.header-status :deep(.el-button) {
  --el-button-bg-color: rgba(255,255,255,0.05);
  --el-button-border-color: rgba(255,255,255,0.14);
  --el-button-text-color: #d7e1ea;
  --el-button-hover-bg-color: rgba(77,163,255,0.14);
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #39d98a;
  box-shadow: 0 0 12px rgba(57, 217, 138, 0.8);
}

.metrics-row {
  display: grid;
  grid-template-columns: repeat(6, minmax(128px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.metric-card,
.scene-panel,
.device-panel,
.alert-panel,
.chart-panel,
.report-panel {
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 8px;
  background: rgba(8, 20, 32, 0.78);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.25);
}

.metric-card {
  min-height: 104px;
  padding: 14px;
  border-left: 3px solid #39d98a;
}

.metric-card.warning {
  border-left-color: #ffb020;
}

.metric-card.critical {
  border-left-color: #ff4d4f;
}

.metric-top {
  justify-content: space-between;
  color: #93a6b8;
  font-size: 13px;
}

.metric-value {
  margin-top: 12px;
  color: #f1f6fa;
  font-size: 28px;
  line-height: 1;
  font-weight: 700;
}

.metric-value small {
  margin-left: 4px;
  color: #8fa1b2;
  font-size: 12px;
  font-weight: 500;
}

.metric-foot {
  margin-top: 10px;
  color: #39d98a;
  font-size: 12px;
}

.metric-foot.down {
  color: #ffb020;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(260px, 1fr) minmax(420px, 1.5fr) minmax(280px, 1fr);
  grid-template-rows: 390px 300px 330px;
  grid-template-areas:
    "device scene alert"
    "energy energy report"
    "yield yield report";
  gap: 12px;
  min-height: calc(100vh - 180px);
}

.scene-panel {
  grid-area: scene;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.device-panel {
  grid-area: device;
}

.alert-panel {
  grid-area: alert;
}

.energy-panel {
  grid-area: energy;
}

.yield-panel {
  grid-area: yield;
}

.report-panel {
  grid-area: report;
}

.device-panel,
.alert-panel,
.chart-panel,
.report-panel {
  min-width: 0;
  padding: 14px;
  overflow: hidden;
}

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
  font-weight: 700;
}

.scene-panel .panel-title {
  padding: 14px 16px 0;
}

.scene-preview {
  flex: 1;
  min-height: 0;
}

.overview-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  background: rgba(255,255,255,0.08);
}

.overview-strip div {
  padding: 12px;
  background: rgba(8, 20, 32, 0.96);
}

.overview-strip span,
.overview-strip strong {
  display: block;
}

.overview-strip span {
  color: #8fa1b2;
  font-size: 12px;
}

.overview-strip strong {
  margin-top: 4px;
  color: #f1f6fa;
  font-size: 21px;
}

.device-matrix {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.device-tile {
  align-items: flex-start;
  flex-direction: column;
  gap: 5px;
  min-height: 78px;
  padding: 10px;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  color: #d7e1ea;
  background: rgba(255,255,255,0.035);
  cursor: pointer;
  text-align: left;
  font-family: inherit;
}

.device-tile:hover {
  border-color: rgba(77, 163, 255, 0.45);
  background: rgba(77, 163, 255, 0.08);
}

.device-indicator {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #667085;
}

.device-tile.online .device-indicator {
  background: #39d98a;
  box-shadow: 0 0 8px rgba(57,217,138,0.8);
}

.device-tile.warning .device-indicator {
  background: #ffb020;
  box-shadow: 0 0 8px rgba(255,176,32,0.8);
}

.device-tile.critical .device-indicator {
  background: #ff4d4f;
  box-shadow: 0 0 8px rgba(255,77,79,0.8);
}

.device-name {
  width: 100%;
  color: #f1f6fa;
  font-size: 13px;
  font-weight: 650;
  line-height: 1.25;
}

.device-type {
  color: #8fa1b2;
  font-size: 11px;
}

.device-detail {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255,255,255,0.08);
}

.detail-name {
  color: #f1f6fa;
  font-size: 13px;
  font-weight: 650;
  margin-bottom: 8px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 7px;
}

.detail-grid span {
  padding: 6px 8px;
  border-radius: 6px;
  color: #8fa1b2;
  background: rgba(255,255,255,0.04);
  font-size: 12px;
}

.detail-grid strong {
  display: block;
  margin-top: 3px;
  color: #39d98a;
  font-size: 14px;
}

.alert-list {
  height: calc(100% - 38px);
  overflow: auto;
  padding-right: 3px;
}

.alert-item {
  align-items: flex-start;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255,255,255,0.07);
}

.alert-item.acknowledged {
  opacity: 0.58;
}

.alert-level {
  min-width: 36px;
  padding: 3px 6px;
  border-radius: 6px;
  color: #06101a;
  background: #8fa1b2;
  font-size: 11px;
  font-weight: 700;
  text-align: center;
}

.alert-item.warning .alert-level {
  background: #ffb020;
}

.alert-item.critical .alert-level {
  color: #fff;
  background: #ff4d4f;
}

.alert-item strong {
  color: #f1f6fa;
  font-size: 12px;
}

.alert-item p {
  margin: 4px 0;
  color: #c8d3dd;
  font-size: 12px;
  line-height: 1.45;
}

.alert-item time {
  color: #748392;
  font-size: 11px;
}

.chart-box {
  width: 100%;
  height: calc(100% - 38px);
  min-height: 220px;
}

.yield-content {
  display: grid;
  grid-template-columns: minmax(240px, 1fr) 260px;
  gap: 12px;
  height: calc(100% - 38px);
}

.heat-chart {
  min-height: 250px;
  height: 100%;
}

.yield-list {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 10px;
}

.yield-row {
  display: grid;
  grid-template-columns: 1fr 54px;
  gap: 7px;
  padding: 10px;
  border-radius: 8px;
  background: rgba(255,255,255,0.04);
}

.yield-row span {
  color: #c8d3dd;
  font-size: 13px;
}

.yield-row strong {
  color: #39d98a;
  font-size: 14px;
  text-align: right;
}

.yield-row :deep(.el-progress) {
  grid-column: 1 / -1;
}

.yield-row :deep(.el-progress-bar__outer) {
  height: 5px !important;
}

.report-panel {
  display: flex;
  flex-direction: column;
}

.report-score {
  align-items: flex-start;
  gap: 14px;
  padding: 12px;
  border-radius: 8px;
  background: rgba(57, 217, 138, 0.08);
}

.report-score strong {
  display: block;
  color: #39d98a;
  font-size: 32px;
  line-height: 1;
}

.report-score span {
  display: block;
  margin-top: 4px;
  color: #c8d3dd;
  font-size: 12px;
  text-align: center;
}

.report-score p {
  margin: 0;
  color: #c8d3dd;
  font-size: 13px;
  line-height: 1.6;
}

.report-chart {
  height: 210px;
  min-height: 180px;
  margin-top: 12px;
}

.recommend-list {
  margin: 8px 0 0;
  padding: 0 0 0 16px;
  color: #b9c6d2;
  font-size: 12px;
  line-height: 1.7;
}

.empty-state,
.empty-dashboard {
  color: #8fa1b2;
  text-align: center;
}

.empty-dashboard {
  display: grid;
  place-items: center;
  gap: 12px;
  height: calc(100vh - 120px);
}

.empty-dashboard .el-icon {
  color: #4da3ff;
  font-size: 42px;
}

@media (max-width: 1280px) {
  .metrics-row {
    grid-template-columns: repeat(3, minmax(160px, 1fr));
  }

  .dashboard-grid {
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 420px 360px 320px 360px;
    grid-template-areas:
      "scene scene"
      "device alert"
      "energy energy"
      "yield report";
  }
}

@media (max-width: 820px) {
  .monitor-page {
    padding: 12px;
  }

  .monitor-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .header-status {
    justify-content: flex-start;
  }

  .brand-block h1 {
    font-size: 19px;
  }

  .metrics-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .dashboard-grid {
    display: flex;
    flex-direction: column;
  }

  .scene-panel {
    min-height: 420px;
  }

  .device-panel,
  .alert-panel,
  .chart-panel,
  .report-panel {
    min-height: 320px;
  }

  .overview-strip {
    grid-template-columns: repeat(2, 1fr);
  }

  .yield-content {
    display: flex;
    flex-direction: column;
    height: auto;
  }

  .yield-list {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 520px) {
  .metrics-row,
  .device-matrix,
  .detail-grid,
  .yield-list {
    grid-template-columns: 1fr;
  }

  .metric-value {
    font-size: 24px;
  }

  .scene-panel {
    min-height: 360px;
  }
}
</style>
