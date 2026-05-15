<template>
  <transition name="semantic-slide">
    <div
      ref="panelRef"
      class="semantic-builder"
      :class="{ dragging }"
      :style="panelStyle"
      v-show="dialogStore.semanticBuilderPanel"
      @pointerdown="bringToFront"
    >
      <div class="semantic-head" title="拖动移动面板，双击回到默认位置" @pointerdown="startDrag" @dblclick="resetPosition">
        <div class="semantic-head-left">
          <span class="semantic-dot"></span>
          <span class="semantic-title">AI 搭建</span>
          <span class="semantic-badge">{{ sourceLabel }}</span>
        </div>
        <el-button type="danger" :icon="Close" circle size="small" plain @click="dialogStore.showSemanticBuilderPanel(false)" />
      </div>

      <div class="semantic-body">
        <el-input
          v-model="message"
          type="textarea"
          :rows="5"
          resize="none"
          maxlength="260"
          show-word-limit
          placeholder="描述你想搭建的农业场景"
        />

        <div class="sample-strip">
          <button
            v-for="sample in samples"
            :key="sample.title"
            type="button"
            class="sample-chip"
            @click="useSample(sample.message)"
          >
            {{ sample.title }}
          </button>
        </div>

        <div class="semantic-actions">
          <el-button type="primary" :loading="loading || applying" @click="generatePlan">
            生成并搭建
          </el-button>
          <el-button plain :disabled="!result || applying || loading" :loading="applying" @click="applyPlan(false)">
            重新应用
          </el-button>
          <el-button plain :disabled="(!result && !message.trim()) || applying || loading" :loading="loading || applying" @click="applyLatestPlan(true)">
            清空后应用
          </el-button>
        </div>

        <div v-if="result" class="plan-summary">
          <div class="summary-row">
            <span>场景</span>
            <strong>{{ result.scenePlan.sceneName }}</strong>
          </div>
          <div class="summary-row source-row">
            <span>来源</span>
            <strong>{{ sourceDetail }}</strong>
          </div>
          <div class="summary-grid">
            <div>
              <strong>{{ result.scenePlan.objects.length }}</strong>
              <span>对象组</span>
            </div>
            <div>
              <strong>{{ result.models.length }}</strong>
              <span>可加载模型</span>
            </div>
            <div>
              <strong>{{ result.missingAssets.length }}</strong>
              <span>缺失资产</span>
            </div>
          </div>
        </div>

        <div v-if="result" class="context-box">
          <div class="section-title">上下文</div>
          <div class="context-row">
            <span>当前场景</span>
            <strong>{{ result.context.sceneName || '新建场景' }}</strong>
          </div>
          <div class="context-row">
            <span>已有对象</span>
            <strong>{{ result.context.sceneSummary?.modelCount || 0 }}</strong>
          </div>
          <div v-if="result.context.selectedObject" class="context-row">
            <span>选中对象</span>
            <strong>{{ result.context.selectedObject.label }}</strong>
          </div>
        </div>

        <div v-if="result?.warnings.length" class="notice-list warning-list">
          <div v-for="item in result.warnings" :key="item" class="notice-item">{{ item }}</div>
        </div>

        <div v-if="result?.missingAssets.length" class="missing-box">
          <div class="section-title">缺失资产</div>
          <div v-for="asset in result.missingAssets" :key="asset.assetKey" class="missing-item">
            <span>{{ asset.name }}</span>
            <small>{{ asset.reason }}</small>
          </div>
        </div>

        <div v-if="result?.scenePlan.objects.length" class="object-list">
          <div class="section-title">对象清单</div>
          <div v-for="obj in result.scenePlan.objects" :key="obj.id" class="object-item">
            <div class="object-main">
              <span>{{ obj.label }}</span>
              <strong>x{{ obj.count }}</strong>
            </div>
            <div class="object-meta">
              {{ areaLabel(obj.area) }} / {{ layoutLabel(obj.layout) }} / {{ obj.assetKey }}
            </div>
            <div class="asset-source" :class="{ missing: !obj.url }">
              {{ obj.url ? `模型库：${obj.url}` : '模型库：缺失 GLB' }}
            </div>
          </div>
        </div>

        <div v-if="result?.models.length" class="model-list">
          <div class="section-title">加载队列</div>
          <div v-for="model in result.models" :key="model.meta.id" class="model-item">
            <span>{{ model.meta.label }}</span>
            <small>{{ formatOffset(model.options.offset) }}</small>
          </div>
        </div>

        <details v-if="result?.rawLlmPlan" class="raw-plan">
          <summary>LLM JSON</summary>
          <pre>{{ formattedRawPlan }}</pre>
        </details>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { Scene } from '@/lib/scene'
import { useDialogStore } from '@/stores/dialog'
import { useModelStore } from '@/stores/model'
import { useSceneStore } from '@/stores/scene'
import { useDraggablePanel } from '@/composables/useDraggablePanel'
import {
  buildSemanticPlan,
  fetchSemanticSamples,
  type BuildModel,
  type BuildSample,
  type SemanticBuildContext,
  type SemanticBuildResponse,
  type SemanticObjectSummary
} from '@/services/semanticService'

const dialogStore = useDialogStore()
const sceneStore = useSceneStore()
const modelStore = useModelStore()
const { panelRef, panelStyle, dragging, startDrag, resetPosition, bringToFront } = useDraggablePanel({
  storageKey: 'scene-design:panel:semantic-builder',
  initialTop: 82,
  initialLeft: 18,
  width: 420,
  zIndex: 760
})

const defaultPrompt = '搭一个智慧农业示范园区，左侧六块玉米地，右侧三个温室，中间一条道路，中央放气象站和灌溉设备。'
const message = ref(defaultPrompt)
const loading = ref(false)
const applying = ref(false)
const result = ref<SemanticBuildResponse | null>(null)
const resultPrompt = ref('')
const samples = ref<BuildSample[]>([])
const sourceLabel = computed(() => {
  if (!result.value) return 'LLM 版'
  return result.value.planSource?.mode === 'llm' ? 'LLM 版' : '规则回退'
})
const sourceDetail = computed(() => {
  const source = result.value?.planSource
  if (!source) return '待生成'
  if (source.mode === 'llm') {
    return `${source.model || 'LLM'} / 第 ${source.attempt || 1} 次`
  }
  return source.reason || '规则版解析'
})
const formattedRawPlan = computed(() => {
  const raw = result.value?.rawLlmPlan
  if (!raw) return ''
  try {
    return JSON.stringify(JSON.parse(raw), null, 2)
  } catch {
    return raw
  }
})

onMounted(async () => {
  try {
    samples.value = await fetchSemanticSamples()
  } catch {
    samples.value = [
      { title: '智慧农业示范园区', message: defaultPrompt },
      { title: '标准温室场景', message: '创建标准温室场景，两个大棚纵向排列，每个大棚旁边放灌溉设备。' }
    ]
  }
})

function useSample(text: string) {
  message.value = text
}

async function generatePlan() {
  const text = message.value.trim()
  if (!text) {
    ElMessage.warning('请输入场景描述')
    return
  }
  loading.value = true
  try {
    const { plan, context } = await buildPlanForCurrentMessage(text)
    await applyPlan(!context.appendMode, plan)
  } catch (err: any) {
    ElMessage.error(err?.message || '语义搭建方案生成失败')
  } finally {
    loading.value = false
  }
}

async function applyLatestPlan(clearFirst: boolean) {
  const text = message.value.trim()
  if (!text) {
    ElMessage.warning('请输入场景描述')
    return
  }

  let plan = result.value
  if (!plan || resultPrompt.value !== text) {
    loading.value = true
    try {
      plan = (await buildPlanForCurrentMessage(text)).plan
    } catch (err: any) {
      ElMessage.error(err?.message || '语义搭建方案生成失败')
      return
    } finally {
      loading.value = false
    }
  }
  await applyPlan(clearFirst, plan)
}

async function buildPlanForCurrentMessage(text: string) {
  const context = buildContext(text)
  const plan = await buildSemanticPlan({
    message: text,
    sceneName: sceneStore.sceneName || undefined,
    mode: context.appendMode ? 'append' : 'preview',
    context
  })
  result.value = plan
  resultPrompt.value = text
  return { plan, context }
}

function buildContext(text = message.value): SemanticBuildContext {
  const scene = Scene.getInstance()
  const objects = summarizeSceneObjects()
  const selected = modelStore.activeModel ? summarizeModel(modelStore.activeModel.getModelId, modelStore.activeModel) : undefined
  const appendMode = /继续|补|补齐|补充|增加|加几个|现有|当前/.test(text)
  return {
    sceneName: scene.sceneName || sceneStore.sceneName || '新建场景',
    appendMode,
    sceneSummary: {
      objectCount: objects.length,
      modelCount: objects.length
    },
    selectedObject: selected,
    selectedObjects: modelStore.selectedModels.map(model => summarizeModel(model.getModelId, model)).filter(Boolean),
    existingObjects: objects
  }
}

function summarizeSceneObjects(): SemanticObjectSummary[] {
  const scene = Scene.getInstance()
  return Object.entries(scene.getSceneModels)
    .slice(0, 24)
    .map(([id, model]) => summarizeModel(id, model))
    .filter(Boolean)
}

function summarizeModel(id: string, model: any): SemanticObjectSummary {
  const saved = model.saveModel()
  const meta = saved.options?.meta || saved.options?.data || {}
  const label = meta.label || model.name || saved.url?.split('/').pop() || '场景对象'
  return {
    id,
    label,
    assetKey: meta.assetKey || guessAssetKey(saved.url),
    category: meta.category || '',
    url: saved.url,
    scale: Number(saved.options?.scale || 1),
    offset: saved.options?.offset
  }
}

function guessAssetKey(url = '') {
  if (url.includes('Silo_House')) return 'greenhouse'
  if (url.includes('Corn_Crop')) return 'corn'
  if (url.includes('Wheat_Crop')) return 'wheat'
  if (url.includes('Rice_Crop')) return 'rice'
  if (url.includes('TowerWindmill')) return 'weather_station'
  if (url.includes('Well')) return 'irrigation'
  if (url.includes('WaterTower')) return 'water_tower'
  if (url.includes('BigBarn')) return 'warehouse'
  if (url.includes('building-type-i')) return 'admin_building'
  if (url.includes('path-long')) return 'road'
  return ''
}

async function applyPlan(clearFirst: boolean, plan = result.value) {
  if (!plan) return
  const scene = Scene.getInstance()
  applying.value = true
  try {
    if (plan.models.length === 0) {
      ElMessage.warning('当前方案没有可加载模型')
      return
    }
    if (clearFirst) {
      scene.clear()
    }
    const ground = plan.scenePlan.ground
    scene.enableRoomEnvironment()
    scene.setAmbientLight({ color: '#ffffff', intensity: 1.15 })
    scene.setDirectionalLight({ color: '#fff2d0', intensity: 1.6, position: { x: 260, y: 520, z: 320 } })
    if (clearFirst || scene.isEmpty()) {
      scene.setSceneName(plan.scenePlan.sceneName)
      scene.setGroundPane({ color: ground.color || '#88aa66', width: ground.width, height: ground.height })
      scene.setGrid({ size: Math.max(ground.width, ground.height), division: 24 })
      scene.setView('origin')
    }

    const settled = await Promise.allSettled(
      plan.models.map(item => scene.loadModel(item.url, semanticModelOptions(item)))
    )
    const failed = settled.filter(item => item.status === 'rejected').length
    if (failed > 0) {
      ElMessage.warning(`已应用 ${settled.length - failed} 个模型，${failed} 个模型加载失败`)
    } else {
      ElMessage.success(`已应用 ${settled.length} 个模型到当前场景`)
    }
  } catch (err: any) {
    ElMessage.error(err?.message || '应用搭建方案失败')
  } finally {
    applying.value = false
  }
}

function semanticModelOptions(item: BuildModel) {
  return {
    offset: item.options.offset,
    angle: item.options.angle,
    semanticScale: item.options.scale,
    meta: item.meta
  }
}

function areaLabel(area: string) {
  const labels: Record<string, string> = {
    west: '左侧',
    east: '右侧',
    north: '北侧',
    south: '南侧',
    center: '中心'
  }
  return labels[area] || area || '默认区域'
}

function layoutLabel(layout: string) {
  const labels: Record<string, string> = {
    single: '单个',
    row: '行列',
    column: '纵列',
    grid: '网格',
    along_path: '沿道路'
  }
  return labels[layout] || layout || '自动'
}

function formatOffset(offset: { x: number; y: number; z: number }) {
  return `x ${Math.round(offset.x)}, z ${Math.round(offset.z)}`
}
</script>

<style scoped>
.semantic-builder {
  position: fixed;
  width: 420px;
  max-height: calc(100vh - 110px);
  display: flex;
  flex-direction: column;
  color: #c8d0da;
  background: rgba(12, 20, 34, 0.94);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  box-shadow: 0 18px 50px rgba(0,0,0,0.38);
  backdrop-filter: blur(14px);
  overflow: hidden;
}

.semantic-builder.dragging {
  cursor: grabbing;
}

.semantic-head {
  height: 48px;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px 0 16px;
  border-bottom: 1px solid rgba(255,255,255,0.07);
  background: rgba(255,255,255,0.03);
}

.semantic-head-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.semantic-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #00d4ff;
  box-shadow: 0 0 10px rgba(0,212,255,0.8);
}

.semantic-title {
  font-size: 15px;
  font-weight: 600;
  color: #e6f7ff;
}

.semantic-badge {
  height: 20px;
  display: inline-flex;
  align-items: center;
  padding: 0 7px;
  border-radius: 4px;
  font-size: 11px;
  color: #8be7ff;
  background: rgba(0,212,255,0.12);
  border: 1px solid rgba(0,212,255,0.2);
}

.semantic-body {
  padding: 14px;
  overflow: auto;
}

.sample-strip {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin: 10px 0 12px;
}

.sample-chip {
  min-height: 26px;
  padding: 0 8px;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 4px;
  background: rgba(255,255,255,0.04);
  color: #9fb2c6;
  font-size: 12px;
  cursor: pointer;
}

.sample-chip:hover {
  color: #00d4ff;
  border-color: rgba(0,212,255,0.32);
}

.semantic-actions {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
}

.semantic-actions :deep(.el-button) {
  margin-left: 0;
}

.plan-summary {
  margin-top: 14px;
  padding: 12px;
  border-radius: 8px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
}

.summary-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  color: #8899aa;
}

.summary-row strong {
  color: #e6f7ff;
  font-size: 13px;
  text-align: right;
}

.source-row {
  margin-top: 8px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 10px;
}

.summary-grid div {
  min-height: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: rgba(0,0,0,0.16);
}

.summary-grid strong {
  color: #00d4ff;
  font-size: 20px;
  line-height: 22px;
}

.summary-grid span {
  margin-top: 4px;
  font-size: 11px;
  color: #8899aa;
}

.notice-list,
.missing-box,
.context-box,
.object-list,
.model-list,
.raw-plan {
  margin-top: 12px;
}

.notice-item {
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 18px;
  color: #ffd89b;
  background: rgba(255,166,77,0.1);
  border: 1px solid rgba(255,166,77,0.18);
}

.notice-item + .notice-item {
  margin-top: 6px;
}

.section-title {
  margin-bottom: 8px;
  font-size: 12px;
  color: #8899aa;
}

.context-box {
  padding: 10px;
  border-radius: 8px;
  background: rgba(255,255,255,0.035);
  border: 1px solid rgba(255,255,255,0.07);
}

.context-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  min-height: 22px;
  font-size: 12px;
  color: #8899aa;
}

.context-row strong {
  color: #d9e8f6;
  font-weight: 500;
  text-align: right;
}

.missing-item,
.object-item,
.model-item {
  padding: 9px 10px;
  border-radius: 6px;
  background: rgba(255,255,255,0.035);
  border: 1px solid rgba(255,255,255,0.07);
}

.missing-item + .missing-item,
.object-item + .object-item,
.model-item + .model-item {
  margin-top: 6px;
}

.missing-item span,
.model-item span {
  display: block;
  color: #e5edf6;
  font-size: 13px;
}

.missing-item small,
.model-item small {
  display: block;
  margin-top: 4px;
  color: #7f91a5;
  font-size: 11px;
  line-height: 16px;
}

.object-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.object-main span {
  color: #e5edf6;
  font-size: 13px;
}

.object-main strong {
  color: #00d4ff;
  font-size: 12px;
}

.object-meta {
  margin-top: 4px;
  color: #7f91a5;
  font-size: 11px;
}

.asset-source {
  margin-top: 5px;
  color: #7ed9ff;
  font-size: 11px;
  overflow-wrap: anywhere;
}

.asset-source.missing {
  color: #ffbd7a;
}

.raw-plan {
  border-radius: 8px;
  background: rgba(0,0,0,0.18);
  border: 1px solid rgba(255,255,255,0.07);
}

.raw-plan summary {
  padding: 9px 10px;
  cursor: pointer;
  color: #9fb2c6;
  font-size: 12px;
}

.raw-plan pre {
  max-height: 220px;
  margin: 0;
  padding: 0 10px 10px;
  overflow: auto;
  color: #c8d0da;
  font-size: 11px;
  line-height: 16px;
  white-space: pre-wrap;
}

.semantic-slide-enter-active,
.semantic-slide-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.semantic-slide-enter-from,
.semantic-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
