<!--
 *   三维数字孪生设计平台
 *    模型属性面板
 *
 *  @author Sparcle
 *  @version 2.1
 -->

<template>
  <transition name="pane-slide">
    <div class="prop" v-show="dialogStore.propPane">
      <div class="prop-head">
        <div class="prop-head-left">
          <span class="prop-dot"></span>
          <span class="prop-title">{{ activeName }}</span>
        </div>
        <el-button type="danger" :icon="Close" circle size="small" plain @click="closePropPane" />
      </div>

      <el-collapse v-model="activeNames" class="prop-collapse">
        <el-collapse-item title="模型信息" name="0">
          <el-descriptions :column="1" border size="small" class="prop-desc">
            <el-descriptions-item label="模型名称">{{ activeModelInfo.label }}</el-descriptions-item>
            <el-descriptions-item label="资产类型">{{ activeModelInfo.assetKey }}</el-descriptions-item>
            <el-descriptions-item label="分类">{{ activeModelInfo.category }}</el-descriptions-item>
            <el-descriptions-item label="区域/布局">{{ activeModelInfo.placement }}</el-descriptions-item>
            <el-descriptions-item label="数据ID">{{ activeModelInfo.dataId }}</el-descriptions-item>
            <el-descriptions-item label="场景对象">{{ activeModelInfo.sceneObjectId }}</el-descriptions-item>
            <el-descriptions-item label="业务绑定">{{ businessStatusText }}</el-descriptions-item>
            <el-descriptions-item label="模型URL">{{ activeModelInfo.url }}</el-descriptions-item>
          </el-descriptions>
        </el-collapse-item>

        <el-collapse-item title="业务对象详情" name="business">
          <div v-if="businessLoading" class="business-empty">加载中</div>
          <div v-else-if="boundObject" class="business-card">
            <div class="business-title">
              <span>{{ boundObject.name }}</span>
              <el-tag size="small" effect="dark">{{ boundObject.type }}</el-tag>
            </div>
            <el-descriptions :column="1" border size="small" class="prop-desc">
              <el-descriptions-item label="对象ID">{{ boundObject.id }}</el-descriptions-item>
              <el-descriptions-item label="状态">{{ boundObject.status }}</el-descriptions-item>
              <el-descriptions-item label="数据质量">{{ qualityLabel(boundObject.dataQuality) }}</el-descriptions-item>
              <el-descriptions-item label="指标摘要">{{ metricSummary }}</el-descriptions-item>
              <el-descriptions-item label="历史趋势入口">{{ trendEntryText }}</el-descriptions-item>
              <el-descriptions-item label="告警入口">{{ alertEntryText }}</el-descriptions-item>
              <el-descriptions-item label="关联事件入口">{{ eventEntryText }}</el-descriptions-item>
              <el-descriptions-item label="同步频率">{{ memorySummary.syncFrequency }}</el-descriptions-item>
              <el-descriptions-item label="最新状态">{{ memorySummary.latest }}</el-descriptions-item>
              <el-descriptions-item label="24h趋势">{{ memorySummary.trend }}</el-descriptions-item>
              <el-descriptions-item label="事件记忆">{{ memorySummary.events }}</el-descriptions-item>
            </el-descriptions>
          </div>
          <div v-else class="business-empty">未绑定业务对象</div>
        </el-collapse-item>

        <el-collapse-item title="模型调整" name="1" v-if="$envCfg.editMode">
          <el-form label-width="72px" size="small" class="prop-form">
            <el-form-item label="数据关联">
              <el-input v-model="formDataId" placeholder="输入数据ID" @change="bandDataId" />
            </el-form-item>
            <el-form-item label="缩放">
              <el-slider v-model="scale" :min="1" :max="30000" :format-tooltip="formatSliderValue" @change="modelPropChange" />
            </el-form-item>
            <el-form-item label="南北位置">
              <el-slider v-model="formData.offset.x" :min="-500" :max="500" @change="modelPropChange" />
            </el-form-item>
            <el-form-item label="东西位置">
              <el-slider v-model="formData.offset.z" :min="-500" :max="500" @change="modelPropChange" />
            </el-form-item>
            <el-form-item label="高度">
              <el-slider v-model="formData.offset.y" :min="-500" :max="500" @change="modelPropChange" />
            </el-form-item>
            <el-form-item label="朝向">
              <el-radio-group v-model="formData.angle" @change="modelPropChange" size="small">
                <el-radio-button :value="0">北</el-radio-button>
                <el-radio-button :value="90">东</el-radio-button>
                <el-radio-button :value="180">南</el-radio-button>
                <el-radio-button :value="270">西</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-form>
        </el-collapse-item>

        <el-collapse-item title="碳排放数据" name="2">
          <div class="data-rows">
            <el-descriptions :column="1" border size="small" class="prop-desc">
              <el-descriptions-item label="月碳排放">{{ activeData.carbon || '--' }}</el-descriptions-item>
              <el-descriptions-item label="碳排放强度">{{ activeData.intensity || '--' }}</el-descriptions-item>
              <el-descriptions-item label="单位名称">{{ activeData.name || '--' }}</el-descriptions-item>
            </el-descriptions>
          </div>
          <div ref="chart" class="prop-chart"></div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Close } from '@element-plus/icons-vue'
import { useModelStore } from '@/stores/model'
import { useDialogStore } from '@/stores/dialog'
import { useGlobals } from '@/composables/useGlobals'
import { today, nextDay } from '@/lib/utils'
import type { Model } from '@/lib/model'
import type { AgriculturalObject, ObjectRelationsResponse, DataQualityStatus } from '@/services/agriculturalObjectService'
import { fetchAgriculturalObjectRelations } from '@/services/agriculturalObjectService'
import { fetchSceneObjectBinding } from '@/services/sceneBusinessBindingService'
import {
  fetchObjectEvents,
  fetchObjectLatestValues,
  fetchObjectSyncPolicy,
  fetchObjectTimeSeries,
  type EventQueryResponse,
  type FarmLatestResponse,
  type FarmSyncPolicy,
  type TimeSeriesResponse
} from '@/services/farmMemoryService'
import { Scene } from '@/lib/scene'

const { $envCfg } = useGlobals()
const modelStore = useModelStore()
const dialogStore = useDialogStore()

const activeNames = ref(['0', 'business', '2'])
const scale = ref(1)
const formDataId = ref('')
const businessLoading = ref(false)
const boundObject = ref<AgriculturalObject | null>(null)
const boundRelations = ref<ObjectRelationsResponse | null>(null)
const memoryPolicy = ref<FarmSyncPolicy | null>(null)
const memoryLatest = ref<FarmLatestResponse | null>(null)
const memorySeries = ref<TimeSeriesResponse | null>(null)
const memoryEvents = ref<EventQueryResponse | null>(null)
const formData = reactive({
  offset: { x: 0, y: 0, z: 0 },
  angle: 0
})
let businessRequestId = 0

const chart = ref<HTMLElement>()
let myChart: any = null

type BusinessBindableModel = Pick<Model, 'getSceneObjectId' | 'setBusinessBinding'>

const activeObject = computed(() => modelStore.activeModel)
const activeName = computed(() => activeObject.value?.name || '未选择')
const activeData = computed(() => activeObject.value?.getData || {})
const activeOptions = computed(() => activeObject.value?.getOptions || {})
const activeMeta = computed(() => activeOptions.value?.meta || {})
const activeModelInfo = computed(() => {
  const saved = activeObject.value?.saveModel()
  const meta = activeMeta.value
  return {
    label: meta.label || activeObject.value?.name || '--',
    assetKey: meta.assetKey || guessAssetKey(saved?.url) || '--',
    category: categoryLabel(meta.category),
    placement: [areaLabel(meta.area), layoutLabel(meta.layout)].filter(item => item !== '--').join(' / ') || '--',
    dataId: activeOptions.value?.dataId || '未绑定',
    sceneObjectId: activeObject.value?.getSceneObjectId || '--',
    url: saved?.url || '--'
  }
})
const businessStatusText = computed(() => {
  if (businessLoading.value) return '查询中'
  return boundObject.value ? `${boundObject.value.name} (${boundObject.value.id})` : '未绑定业务对象'
})
const metricSummary = computed(() => {
  const metrics = boundRelations.value?.relations?.metrics || []
  if (metrics.length > 0) {
    return metrics.map(item => item.targetLabel || item.targetId).filter(Boolean).join('、') || '已关联指标'
  }
  const metadataMetrics = boundObject.value?.metadata?.metrics
  if (Array.isArray(metadataMetrics)) {
    return metadataMetrics.join('、')
  }
  return boundObject.value?.dataQuality === 'missing' ? '缺数据绑定' : '暂无指标'
})
const trendEntryText = computed(() => metricSummary.value === '暂无指标' || metricSummary.value === '缺数据绑定' ? '暂无趋势入口' : '可查看历史趋势')
const alertEntryText = computed(() => (boundRelations.value?.relations?.events || []).length > 0 ? '可查看关联告警/事件' : '暂无告警')
const eventEntryText = computed(() => {
  const events = boundRelations.value?.relations?.events || []
  return events.length > 0 ? `${events.length} 条关联事件` : '暂无事件'
})
const memorySummary = computed(() => {
  const latest = memoryLatest.value ? Object.values(memoryLatest.value.values) : []
  const firstSeries = memorySeries.value ? Object.values(memorySeries.value.series)[0] : null
  return {
    syncFrequency: memoryPolicy.value?.syncFrequency || '未配置',
    latest: latest.length > 0 ? latest.slice(0, 3).map(item => `${item.label}${item.value}${item.unit}`).join('、') : '暂无最新值',
    trend: firstSeries && firstSeries.aggregate.count > 0 ? `${firstSeries.label}均值${firstSeries.aggregate.avg}${firstSeries.unit}` : '暂无24h趋势',
    events: memoryEvents.value?.events.length ? `${memoryEvents.value.events.length} 条事件` : '暂无事件'
  }
})

watch(() => modelStore.offset, (val) => {
  formData.offset.x = val.x
  formData.offset.y = val.y
  formData.offset.z = val.z
}, { deep: true })

watch(activeObject, (val) => {
  boundObject.value = null
  boundRelations.value = null
  resetMemory()
  if (!val) return
  const options = val.getOptions
  formDataId.value = options.dataId || ''
  formData.offset.x = options.offset.x
  formData.offset.y = options.offset.y
  formData.offset.z = options.offset.z
  scale.value = Math.min(30000, options.scale * 100)
  formData.angle = options.angle || 0

  nextTick(() => {
    if (val.getData && val.getData.loadcurve) {
      buildChart()
    }
  })
  loadBusinessBinding(val as BusinessBindableModel)
}, { immediate: true })

function closePropPane() {
  dialogStore.showPropPane(false)
}

function bandDataId() {
  const model = activeObject.value
  if (model) {
    (modelStore.setActiveDataId as any)({ model, dataId: formDataId.value })
  }
}

async function loadBusinessBinding(model: BusinessBindableModel) {
  const requestId = ++businessRequestId
  const sceneName = Scene.getInstance().getSceneName()
  businessLoading.value = true
  resetMemory()
  try {
    const binding = await fetchSceneObjectBinding(sceneName, model.getSceneObjectId)
    if (requestId !== businessRequestId || activeObject.value?.getSceneObjectId !== model.getSceneObjectId) return
    const object = binding?.object || null
    boundObject.value = object
    if (binding?.binding) {
      model.setBusinessBinding({
        businessObjectId: binding.binding.businessObjectId,
        assetKey: binding.binding.assetKey,
        isDefaultBinding: binding.binding.isDefaultBinding
      })
    }
    if (object?.id) {
      const [relations, policy, latest, series, events] = await Promise.all([
        fetchAgriculturalObjectRelations(object.id),
        fetchObjectSyncPolicy(object.id),
        fetchObjectLatestValues(object.id),
        fetchObjectTimeSeries(object.id, '24h', [], 720),
        fetchObjectEvents(object.id, '24h')
      ])
      if (requestId !== businessRequestId || boundObject.value?.id !== object.id) return
      boundRelations.value = relations
      memoryPolicy.value = policy
      memoryLatest.value = latest
      memorySeries.value = series
      memoryEvents.value = events
    }
  } catch {
    boundObject.value = null
    boundRelations.value = null
    resetMemory()
  } finally {
    if (requestId === businessRequestId) {
      businessLoading.value = false
    }
  }
}

function resetMemory() {
  memoryPolicy.value = null
  memoryLatest.value = null
  memorySeries.value = null
  memoryEvents.value = null
}

function modelPropChange() {
  if (activeObject.value) {
    activeObject.value.setProp({
      scale: scale.value / 100,
      offset: formData.offset,
      angle: formData.angle
    })
  }
}

function formatSliderValue(val: number) {
  return val / 100
}

function qualityLabel(status: DataQualityStatus): string {
  const labels: Record<DataQualityStatus, string> = {
    real: '真实',
    simulated: '模拟',
    stale: '过期',
    missing: '缺失'
  }
  return labels[status] || status
}

function guessAssetKey(url = '') {
  if (url.includes('Silo_House')) return 'greenhouse'
  if (url.includes('Corn_Crop')) return 'corn'
  if (url.includes('Wheat_Crop')) return 'wheat'
  if (url.includes('Rice_Crop')) return 'rice'
  if (url.includes('Tomato_Crop')) return 'tomato'
  if (url.includes('Lettuce_Crop')) return 'lettuce'
  if (url.includes('Pumpkin_Crop')) return 'pumpkin'
  if (url.includes('TowerWindmill')) return 'weather_station'
  if (url.includes('Well')) return 'irrigation'
  if (url.includes('WaterTower')) return 'water_tower'
  if (url.includes('BigBarn')) return 'warehouse'
  if (url.includes('building-type-i')) return 'admin_building'
  if (url.includes('path-long')) return 'road'
  if (url.includes('fence')) return 'fence'
  if (url.includes('Windmill')) return 'windmill'
  if (url.includes('solar')) return 'solar'
  return ''
}

function categoryLabel(category = '') {
  const labels: Record<string, string> = {
    facility: '设施',
    crop: '作物',
    device: '设备',
    building: '建筑',
    infrastructure: '基础设施',
    energy: '能源',
    vehicle: '车辆'
  }
  return labels[category] || category || '--'
}

function areaLabel(area = '') {
  const labels: Record<string, string> = {
    west: '左侧',
    east: '右侧',
    north: '北侧',
    south: '南侧',
    center: '中心',
    left: '左侧',
    right: '右侧',
    northwest: '西北',
    northeast: '东北',
    southwest: '西南',
    southeast: '东南'
  }
  return labels[area] || area || '--'
}

function layoutLabel(layout = '') {
  const labels: Record<string, string> = {
    single: '单个',
    row: '横排',
    column: '纵列',
    grid: '网格',
    along_path: '沿路'
  }
  return labels[layout] || layout || '--'
}

function buildChart() {
  if (!chart.value || !activeObject.value) return
  const loadcurve = activeObject.value.getData.loadcurve
  if (!loadcurve) return

  if (myChart) {
    myChart.dispose()
  }
  myChart = echarts.init(chart.value, 'dark')
  const t = today()
  const n = nextDay()
  const data = loadcurve.map((d: any) => [`${t} ${d.time}`, d.value])
  data.push([`${n} 0:0`, data[data.length - 1]?.[1] || 0])

  myChart.setOption({
    grid: { top: 40, left: 50, right: 30, bottom: 50 },
    xAxis: { type: 'time', name: '时刻' },
    yAxis: { type: 'value', name: '负荷(KW)' },
    series: [{ data: data, type: 'line', smooth: true, areaStyle: {} }]
  })
}
</script>

<style scoped>
.prop {
  display: flex;
  flex-direction: column;
  position: absolute;
  left: 16px;
  top: 80px;
  width: 320px;
  max-height: calc(100% - 100px);
  background: rgba(12, 20, 36, 0.9);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  color: #c8d0da;
  text-align: left;
  z-index: 500;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}

.pane-slide-enter-active { transition: all 0.3s ease-out; }
.pane-slide-leave-active { transition: all 0.2s ease-in; }
.pane-slide-enter-from { transform: translateX(-20px); opacity: 0; }
.pane-slide-leave-to { transform: translateX(-20px); opacity: 0; }

.prop-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.prop-head-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.prop-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #00d4ff;
  box-shadow: 0 0 8px rgba(0,212,255,0.5);
}

.prop-title {
  color: #e8ecf1;
  font-size: 15px;
  font-weight: 600;
}

.prop-collapse {
  padding: 0 4px;
}

.prop-collapse :deep(.el-collapse-item__header) {
  color: #bcc8d4;
  font-size: 13px;
  padding: 0 12px;
  border-color: rgba(255,255,255,0.06);
  background: transparent;
}

.prop-collapse :deep(.el-collapse-item__wrap) {
  background: transparent;
  border-color: rgba(255,255,255,0.06);
}

.prop-collapse :deep(.el-collapse-item__content) {
  color: #c8d0da;
  padding: 8px 12px;
}

.prop-form :deep(.el-form-item__label) {
  color: #8899aa;
  font-size: 12px;
}

.prop-desc :deep(.el-descriptions__label) {
  background: rgba(255,255,255,0.03);
  color: #8899aa;
}

.prop-desc :deep(.el-descriptions__content) {
  background: rgba(255,255,255,0.02);
  color: #c8d0da;
  word-break: break-all;
}

.prop-chart {
  width: 100%;
  height: 200px;
  margin-top: 8px;
}

.data-rows {
  margin-bottom: 6px;
}

.business-card,
.business-empty {
  padding: 8px 0;
}

.business-empty {
  color: #8fa1b2;
  font-size: 13px;
}

.business-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
  color: #e8ecf1;
  font-size: 14px;
  font-weight: 600;
}
</style>
