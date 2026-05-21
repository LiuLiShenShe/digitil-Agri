<template>
  <main class="object-page" v-loading="loading && objects.length === 0">
    <header class="object-header">
      <div class="brand-block">
        <div class="brand-mark">
          <el-icon><Connection /></el-icon>
        </div>
        <div>
          <h1>农业对象底座</h1>
          <p>番茄温室 MVP 对象注册表</p>
        </div>
      </div>
      <div class="header-actions">
        <el-select v-model="selectedType" size="small" class="type-select" @change="loadObjects">
          <el-option label="全部类型" value="" />
          <el-option v-for="type in objectTypes" :key="type" :label="type" :value="type" />
        </el-select>
        <el-button :icon="Refresh" circle size="small" plain :loading="loading" @click="loadObjects" />
        <el-button :icon="Back" size="small" plain @click="router.push('/')">返回</el-button>
      </div>
    </header>

    <section class="content-grid">
      <aside class="object-list">
        <button
          v-for="item in objects"
          :key="item.id"
          class="object-row"
          :class="{ active: selectedObject?.id === item.id }"
          @click="selectObject(item.id)"
        >
          <span>
            <strong>{{ item.name }}</strong>
            <small>{{ item.id }}</small>
          </span>
          <el-tag size="small" effect="dark">{{ item.type }}</el-tag>
        </button>
      </aside>

      <section class="detail-panel" v-if="selectedObject">
        <div class="detail-head">
          <div>
            <h2>{{ selectedObject.name }}</h2>
            <p>{{ selectedObject.id }}</p>
          </div>
          <div class="detail-actions">
            <el-tag :type="qualityTagType(selectedObject.dataQuality)" effect="dark">
              {{ qualityLabel(selectedObject.dataQuality) }}
            </el-tag>
            <el-button size="small" plain @click="locateSelectedObject">定位到场景</el-button>
          </div>
        </div>

        <div class="scene-binding-panel">
          <div class="group-title">
            <span>3D 场景绑定</span>
            <strong>{{ sceneBindings.length }}</strong>
          </div>
          <div v-if="bindingLoading" class="scene-binding-empty">查询中</div>
          <div v-else-if="sceneBindings.length === 0" class="scene-binding-empty">无可定位场景对象</div>
          <div v-else class="scene-binding-list">
            <button
              v-for="binding in sceneBindings"
              :key="binding.sceneObjectId"
              class="scene-binding-chip"
              @click="locateBinding(binding.sceneObjectId)"
            >
              <span>{{ binding.sceneObjectId }}</span>
              <small>{{ binding.assetKey || '未设置资产类型' }}{{ binding.isDefaultBinding ? ' / 默认' : '' }}</small>
            </button>
          </div>
        </div>

        <div class="field-grid">
          <div class="field-item">
            <span>类型</span>
            <strong>{{ selectedObject.type }}</strong>
          </div>
          <div class="field-item">
            <span>状态</span>
            <strong>{{ selectedObject.status }}</strong>
          </div>
          <div class="field-item">
            <span>父级</span>
            <strong>{{ selectedObject.parentId || '无' }}</strong>
          </div>
          <div class="field-item">
            <span>区域</span>
            <strong>{{ selectedObject.containingArea || '未设置' }}</strong>
          </div>
          <div class="field-item wide">
            <span>更新时间</span>
            <strong>{{ formatTime(selectedObject.updatedAt) }}</strong>
          </div>
        </div>

        <div class="relation-section" v-if="relationGroups.length > 0">
          <div v-for="group in relationGroups" :key="group.key" class="relation-group">
            <div class="group-title">
              <span>{{ groupLabel(group.key) }}</span>
              <strong>{{ group.items.length }}</strong>
            </div>
            <div class="relation-list">
              <button
                v-for="item in group.items"
                :key="group.key + item.relationType + item.targetId + item.targetLabel"
                class="relation-chip"
                :disabled="!item.targetId"
                @click="item.targetId && selectObject(item.targetId)"
              >
                <span>{{ item.targetLabel || item.targetId }}</span>
                <small>{{ item.targetType || item.relationType }}</small>
              </button>
            </div>
          </div>
        </div>

        <div class="json-block">
          <div class="group-title">
            <span>扩展属性</span>
          </div>
          <pre>{{ JSON.stringify(selectedObject.metadata, null, 2) }}</pre>
        </div>
      </section>

      <section class="empty-panel" v-else>
        <el-icon><Connection /></el-icon>
        <p>请选择一个农业对象</p>
      </section>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back, Connection, Refresh } from '@element-plus/icons-vue'
import {
  fetchAgriculturalObject,
  fetchAgriculturalObjectRelations,
  fetchAgriculturalObjects,
  type AgriculturalObject,
  type AgriculturalObjectType,
  type DataQualityStatus,
  type ObjectRelationsResponse,
  type RelatedObject
} from '@/services/agriculturalObjectService'
import { fetchBusinessObjectSceneBindings, type SceneBusinessBinding } from '@/services/sceneBusinessBindingService'

const router = useRouter()
const loading = ref(false)
const bindingLoading = ref(false)
const objects = ref<AgriculturalObject[]>([])
const selectedType = ref<AgriculturalObjectType | ''>('')
const selectedObject = ref<AgriculturalObject | null>(null)
const relations = ref<ObjectRelationsResponse | null>(null)
const sceneBindings = ref<SceneBusinessBinding[]>([])
const defaultSceneName = '番茄温室 MVP'

const objectTypes: AgriculturalObjectType[] = [
  'Farm',
  'Greenhouse',
  'Parcel',
  'CropRow',
  'Plant',
  'CropBatch',
  'Sensor',
  'Device',
  'Camera',
  'Operation',
  'Observation'
]

const relationGroups = computed(() => {
  if (!relations.value?.relations) return []
  return Object.entries(relations.value.relations)
    .filter(([, items]) => items.length > 0)
    .map(([key, items]) => ({ key, items }))
})

async function loadObjects() {
  loading.value = true
  try {
    objects.value = await fetchAgriculturalObjects(selectedType.value || undefined)
    if (objects.value.length > 0) {
      await selectObject(selectedObject.value?.id && objects.value.some(item => item.id === selectedObject.value?.id)
        ? selectedObject.value.id
        : objects.value[0].id)
    } else {
      selectedObject.value = null
      relations.value = null
    }
  } catch {
    ElMessage.error('农业对象加载失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}

async function selectObject(id: string) {
  loading.value = true
  try {
    const [object, objectRelations] = await Promise.all([
      fetchAgriculturalObject(id),
      fetchAgriculturalObjectRelations(id)
    ])
    selectedObject.value = object
    relations.value = objectRelations
    await loadSceneBindings(id)
  } catch {
    ElMessage.error('农业对象详情加载失败')
  } finally {
    loading.value = false
  }
}

async function loadSceneBindings(objectId: string) {
  bindingLoading.value = true
  try {
    const bindings = await fetchBusinessObjectSceneBindings(defaultSceneName, objectId)
    sceneBindings.value = bindings.sort((a, b) => Number(b.isDefaultBinding) - Number(a.isDefaultBinding))
  } catch {
    sceneBindings.value = []
  } finally {
    bindingLoading.value = false
  }
}

function locateSelectedObject() {
  const target = sceneBindings.value[0]
  if (!target) {
    ElMessage.warning('当前对象没有可定位的场景对象')
    return
  }
  locateBinding(target.sceneObjectId)
}

function locateBinding(sceneObjectId: string) {
  router.push({
    path: '/',
    query: {
      scene: defaultSceneName,
      sceneObjectId
    }
  })
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

function qualityTagType(status: DataQualityStatus): 'success' | 'warning' | 'danger' | 'info' {
  if (status === 'real') return 'success'
  if (status === 'simulated') return 'info'
  if (status === 'stale') return 'warning'
  return 'danger'
}

function groupLabel(key: string): string {
  const labels: Record<string, string> = {
    parents: '父级对象',
    parcels: '地块',
    cropRows: '作物行',
    cropBatches: '作物批次',
    sensors: '传感器',
    devices: '设备',
    cameras: '摄像头',
    keyPlants: '关键植株',
    plants: '植株',
    metrics: '关联指标',
    events: '关联事件',
    assets: '关联资产',
    observations: '观测记录',
    children: '子对象'
  }
  return labels[key] || key
}

function formatTime(value: string): string {
  if (!value) return '未更新'
  return new Date(value).toLocaleString('zh-CN')
}

onMounted(loadObjects)
</script>

<style scoped>
.object-page {
  width: 100%;
  height: 100vh;
  overflow: hidden;
  padding: 18px;
  color: #d7e1ea;
  background:
    linear-gradient(180deg, rgba(8, 18, 30, 0.98), rgba(5, 9, 14, 1)),
    repeating-linear-gradient(90deg, rgba(255,255,255,0.025) 0, rgba(255,255,255,0.025) 1px, transparent 1px, transparent 76px);
}

.object-header,
.brand-block,
.header-actions,
.detail-actions,
.detail-head,
.group-title {
  display: flex;
  align-items: center;
}

.object-header {
  justify-content: space-between;
  gap: 18px;
  min-height: 58px;
  margin-bottom: 14px;
}

.brand-block,
.header-actions {
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

.brand-block h1,
.detail-head h2 {
  margin: 0;
  color: #f1f6fa;
  letter-spacing: 0;
}

.brand-block h1 {
  font-size: 22px;
}

.brand-block p,
.detail-head p {
  margin: 5px 0 0;
  color: #8fa1b2;
  font-size: 13px;
}

.type-select {
  width: 142px;
}

.header-actions :deep(.el-button),
.header-actions :deep(.el-select__wrapper) {
  --el-button-bg-color: rgba(255,255,255,0.05);
  --el-button-border-color: rgba(255,255,255,0.14);
  --el-button-text-color: #d7e1ea;
  background: rgba(255,255,255,0.05);
  box-shadow: none;
}

.content-grid {
  height: calc(100vh - 90px);
  display: grid;
  grid-template-columns: minmax(260px, 360px) 1fr;
  gap: 12px;
}

.object-list,
.detail-panel,
.empty-panel {
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  background: rgba(12, 24, 42, 0.78);
  backdrop-filter: blur(12px);
}

.object-list {
  padding: 10px;
  overflow: auto;
}

.object-row {
  width: 100%;
  min-height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
  padding: 10px;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 6px;
  color: #d7e1ea;
  background: rgba(255,255,255,0.04);
  cursor: pointer;
  text-align: left;
}

.object-row.active,
.object-row:hover {
  border-color: rgba(77, 163, 255, 0.45);
  background: rgba(77, 163, 255, 0.13);
}

.object-row strong,
.object-row small {
  display: block;
}

.object-row small {
  margin-top: 5px;
  color: #8fa1b2;
}

.detail-panel {
  padding: 16px;
  overflow: auto;
}

.detail-head {
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.detail-actions {
  gap: 8px;
}

.detail-head h2 {
  font-size: 20px;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(150px, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.field-item,
.relation-group,
.scene-binding-panel,
.json-block {
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  background: rgba(255,255,255,0.045);
}

.field-item {
  min-height: 72px;
  padding: 12px;
}

.field-item.wide {
  grid-column: span 2;
}

.field-item span,
.group-title span {
  color: #8fa1b2;
  font-size: 12px;
}

.field-item strong {
  display: block;
  margin-top: 8px;
  color: #f1f6fa;
  font-size: 15px;
  word-break: break-word;
}

.relation-section {
  display: grid;
  grid-template-columns: repeat(2, minmax(220px, 1fr));
  gap: 10px;
}

.relation-group,
.scene-binding-panel,
.json-block {
  padding: 12px;
}

.group-title {
  justify-content: space-between;
  margin-bottom: 10px;
}

.group-title strong {
  color: #4da3ff;
}

.relation-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.scene-binding-panel {
  margin-bottom: 14px;
}

.scene-binding-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.scene-binding-chip {
  min-width: 190px;
  max-width: 320px;
  padding: 8px 10px;
  border: 1px solid rgba(77, 163, 255, 0.28);
  border-radius: 6px;
  color: #d7e1ea;
  background: rgba(77, 163, 255, 0.1);
  cursor: pointer;
  text-align: left;
}

.scene-binding-chip span,
.scene-binding-chip small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scene-binding-chip small,
.scene-binding-empty {
  margin-top: 3px;
  color: #8fa1b2;
  font-size: 12px;
}

.relation-chip {
  min-width: 122px;
  max-width: 220px;
  padding: 8px 10px;
  border: 1px solid rgba(77, 163, 255, 0.28);
  border-radius: 6px;
  color: #d7e1ea;
  background: rgba(77, 163, 255, 0.1);
  cursor: pointer;
  text-align: left;
}

.relation-chip:disabled {
  cursor: default;
  opacity: 0.75;
}

.relation-chip span,
.relation-chip small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.relation-chip small {
  margin-top: 3px;
  color: #8fa1b2;
}

.json-block {
  margin-top: 10px;
}

.json-block pre {
  margin: 0;
  color: #b9cad8;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-word;
}

.empty-panel {
  display: grid;
  place-items: center;
  color: #8fa1b2;
}

.empty-panel .el-icon {
  font-size: 42px;
  color: #4da3ff;
}

@media (max-width: 900px) {
  .object-page {
    overflow: auto;
  }

  .object-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .content-grid {
    height: auto;
    grid-template-columns: 1fr;
  }

  .object-list,
  .detail-panel {
    max-height: none;
  }

  .field-grid,
  .relation-section {
    grid-template-columns: 1fr;
  }

  .field-item.wide {
    grid-column: span 1;
  }
}
</style>
