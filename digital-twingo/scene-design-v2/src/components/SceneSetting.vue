<!--
 *   三维数字孪生设计平台
 *    场景设置面板
 *    Phase 2: 增加吸附开关、地形工具入口、场景模板、批量操作
 *
 *  @author Sparcle
 *  @version 2.1
 -->

<template>
  <transition name="pane-slide">
    <div class="scene-setting" v-show="dialogStore.sceneSettingPane">
      <div class="setting-head">
        <div class="setting-head-left">
          <span class="setting-dot"></span>
          <span>场景设置</span>
        </div>
        <el-button type="danger" :icon="Close" circle size="small" plain @click="close" />
      </div>

      <el-collapse v-model="activeNames" class="setting-collapse">
        <el-collapse-item title="视图切换" name="view">
          <div class="view-buttons">
            <el-button v-for="v in views" :key="v.key" size="small" round @click="toggleView(v.key)">{{ v.label }}</el-button>
          </div>
        </el-collapse-item>

        <el-collapse-item title="灯光" name="light">
          <el-form label-width="70px" size="small" class="setting-form">
            <el-form-item label="环境光">
              <el-color-picker v-model="ambColor" @change="setAmbLight" size="small" />
              <el-slider v-model="ambIntensity" :min="0.1" :max="2.0" :step="0.1" @change="setAmbLight" class="light-slider" />
              <el-switch v-model="ambOn" @change="setAmbLight" size="small" />
            </el-form-item>
            <el-form-item label="平行光">
              <el-color-picker v-model="dirColor" @change="setDireLight" size="small" />
              <el-slider v-model="dirIntensity" :min="0.1" :max="2.0" :step="0.1" @change="setDireLight" class="light-slider" />
              <el-switch v-model="dirOn" @change="setDireLight" size="small" />
            </el-form-item>
            <el-form-item label="点光源">
              <el-color-picker v-model="spotColor" @change="setSpotLight" size="small" />
              <el-slider v-model="spotIntensity" :min="0.1" :max="2.0" :step="0.1" @change="setSpotLight" class="light-slider" />
              <el-switch v-model="spotOn" @change="setSpotLight" size="small" />
            </el-form-item>
            <el-form-item label="角度">
              <el-slider v-model="spotAngle" :min="-180" :max="180" @change="setSpotLight" />
            </el-form-item>
            <el-form-item label="高度">
              <el-slider v-model="spotHight" :min="50" :max="600" @change="setSpotLight" />
            </el-form-item>
            <el-form-item label="距离">
              <el-slider v-model="spotDistance" :min="100" :max="800" @change="setSpotLight" />
            </el-form-item>
          </el-form>
        </el-collapse-item>

        <el-collapse-item title="背景" name="background">
          <el-form label-width="70px" size="small" class="setting-form">
            <el-form-item label="天空盒">
              <el-select v-model="curSkybox" @change="setSkybox" placeholder="选择天空盒" size="small">
                <el-option v-for="s in skyboxes" :key="s.alias" :label="s.alias" :value="JSON.stringify(s)" />
              </el-select>
              <el-switch v-model="skyboxOn" @change="setSkybox" size="small" style="margin-left:8px" />
            </el-form-item>
            <el-form-item label="地面">
              <el-select v-model="curGround" @change="setGround" placeholder="选择地面纹理" size="small">
                <el-option v-for="g in grounds" :key="g.name" :label="g.name" :value="g.pic" />
              </el-select>
              <el-color-picker v-model="groundColor" @change="setGround" size="small" style="margin-left:4px" />
              <el-switch v-model="groundOn" @change="setGround" size="small" style="margin-left:8px" />
            </el-form-item>
            <el-form-item label="辅助网格">
              <el-switch v-model="gridOn" @change="setGrid" size="small" />
            </el-form-item>
          </el-form>
        </el-collapse-item>

        <!-- Phase 2: 吸附设置 -->
        <el-collapse-item title="对齐吸附" name="snap">
          <el-form label-width="80px" size="small" class="setting-form">
            <el-form-item label="启用吸附">
              <el-switch v-model="snapOn" @change="setSnap" size="small" />
            </el-form-item>
            <el-form-item label="网格大小">
              <el-slider v-model="snapGridSize" :min="5" :max="50" :step="5" @change="setSnap" show-input size="small" />
            </el-form-item>
          </el-form>
        </el-collapse-item>

        <!-- Phase 2: 批量操作 -->
        <el-collapse-item title="批量操作" name="batch" v-if="$envCfg.editMode">
          <div class="batch-section">
            <div class="batch-buttons">
              <el-button size="small" @click="batchMoveX(-20)">-X</el-button>
              <el-button size="small" @click="batchMoveX(20)">+X</el-button>
              <el-button size="small" @click="batchMoveZ(-20)">-Z</el-button>
              <el-button size="small" @click="batchMoveZ(20)">+Z</el-button>
            </div>
            <div class="batch-buttons" style="margin-top:6px">
              <el-button size="small" @click="batchRotate(-15)">-15</el-button>
              <el-button size="small" @click="batchRotate(15)">+15</el-button>
              <el-button size="small" @click="batchScale(1.1)">放大</el-button>
              <el-button size="small" @click="batchScale(0.9)">缩小</el-button>
            </div>
            <el-button size="small" @click="toggleBoxSelect" style="margin-top:6px;width:100%"
              :type="sceneStore.boxSelectActive ? 'warning' : 'info'">
              {{ sceneStore.boxSelectActive ? '退出框选模式' : '框选模式 (拖拽选择多个模型)' }}
            </el-button>
            <div class="batch-message" v-if="!hasSelection" style="margin-top:6px;color:#667788;font-size:11px">
              点击模型选中后可用批量操作，或使用框选模式选择多个
            </div>
          </div>
        </el-collapse-item>

        <el-collapse-item title="测试" name="test" v-if="$envCfg.showTest">
          <el-form label-width="70px" size="small" class="setting-form">
            <el-form-item label="房间环境">
              <el-switch v-model="roomEnvOn" @change="toggleRoomEnv" size="small" />
            </el-form-item>
            <el-form-item label="加载场景">
              <el-select v-model="loadSceneName" placeholder="选择场景" size="small" style="width:120px">
                <el-option v-for="sn in sceneNameList" :key="sn" :label="sn" :value="sn" />
              </el-select>
              <el-button size="small" @click="loadScene" style="margin-left:8px">加载</el-button>
            </el-form-item>
            <el-form-item label="保存场景">
              <el-input v-model="saveSceneName" placeholder="场景名称" size="small" style="width:140px" />
              <el-button size="small" @click="saveScene" style="margin-left:8px">保存</el-button>
            </el-form-item>
            <el-form-item label="加载模型">
              <el-select v-model="loadModelUrl" placeholder="选择模型" size="small" style="width:200px">
                <el-option v-for="m in modelList" :key="m.id" :label="m.name" :value="m.url" />
              </el-select>
              <el-button size="small" @click="loadModel" style="margin-left:8px">加载</el-button>
            </el-form-item>
          </el-form>
        </el-collapse-item>
      </el-collapse>

      <div class="setting-actions">
        <el-button v-if="$envCfg.editMode" type="primary" @click="loadModelTree" class="action-btn">
          <el-icon><FolderOpened /></el-icon>
          模型加载
        </el-button>
        <el-button v-if="$envCfg.editMode" type="success" plain @click="openLayerPanel" class="action-btn">
          <el-icon><Grid /></el-icon>
          图层管理
        </el-button>
        <el-button v-if="$envCfg.editMode" type="warning" plain @click="openTerrainTools" class="action-btn">
          <el-icon><PictureFilled /></el-icon>
          地形工具
        </el-button>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Scene } from '@/lib/scene'
import { useDialogStore } from '@/stores/dialog'
import { useSceneStore } from '@/stores/scene'
import { useModelStore } from '@/stores/model'
import { useGlobals } from '@/composables/useGlobals'
import { Close, FolderOpened, Grid, PictureFilled } from '@element-plus/icons-vue'

const { $http, $envCfg, $bus } = useGlobals()
const dialogStore = useDialogStore()
const sceneStore = useSceneStore()
const modelStore = useModelStore()
const scene = Scene.getInstance()

const activeNames = ref('')

const views = [
  { key: 'origin', label: '全景' },
  { key: 'top', label: '顶' },
  { key: 'left', label: '左' },
  { key: 'right', label: '右' },
  { key: 'front', label: '前' },
  { key: 'back', label: '后' }
]

// Light state
const ambColor = ref('#ffffff')
const ambIntensity = ref(0.6)
const ambOn = ref(false)
const dirColor = ref('#ffffff')
const dirIntensity = ref(1.0)
const dirOn = ref(false)
const spotColor = ref('#ffffff')
const spotIntensity = ref(1.0)
const spotOn = ref(false)
const spotAngle = ref(0)
const spotHight = ref(300)
const spotDistance = ref(500)

// Background state
const skyboxes = ref<any[]>([])
const curSkybox = ref('')
const skyboxOn = ref(false)
const grounds = ref<any[]>([])
const curGround = ref('')
const groundColor = ref('#88cc88')
const groundOn = ref(false)
const gridOn = ref(false)

// Snap state
const snapOn = ref(sceneStore.snap.enabled)
const snapGridSize = ref(sceneStore.snap.gridSize)

// Test state
const roomEnvOn = ref(false)
const sceneNameList = ref<string[]>([])
const loadSceneName = ref('')
const saveSceneName = ref('')
const modelList = ref<any[]>([])
const loadModelUrl = ref('')

onMounted(() => {
  $http.get('/background/list').then(res => { skyboxes.value = res.data.data })
  $http.get('/background/gdTextures').then(res => { grounds.value = res.data.data })
  $http.get('/model/list').then(res => {
    modelList.value = (res.data.data || []).filter((m: any) => m.leaf && m.url)
  })
  $http.get('/scene/sceneList').then(res => { sceneNameList.value = res.data.data })
})

function close() { dialogStore.showSceneSettingPane(false) }
function toggleView(key: string) { scene.setView(key) }

function setAmbLight() {
  scene.setAmbientLight({ color: ambColor.value, intensity: ambIntensity.value, turnOff: !ambOn.value })
}
function setDireLight() {
  scene.setDirectionalLight({ color: dirColor.value, intensity: dirIntensity.value, turnOff: !dirOn.value })
}
function setSpotLight() {
  scene.setSpotLight({ color: spotColor.value, intensity: spotIntensity.value, turnOff: !spotOn.value, angle: spotAngle.value, hight: spotHight.value, distance: spotDistance.value })
}
function setSkybox() {
  if (curSkybox.value) {
    const sb = JSON.parse(curSkybox.value)
    scene.setBackground({ texturePath: sb.path, imgs: [sb.left, sb.right, sb.front, sb.back, sb.top, sb.bottom], turnOff: !skyboxOn.value })
  } else {
    scene.setBackground({ turnOff: true })
  }
}
function setGround() {
  scene.setGroundPane({ texture: curGround.value, color: groundColor.value, turnOff: !groundOn.value })
}
function setGrid() {
  scene.setGrid({ turnOff: !gridOn.value })
}
function toggleRoomEnv() { scene.toggleRoomEnviroment() }
function loadScene() {
  if (loadSceneName.value) scene.laodScene(loadSceneName.value)
}
function saveScene() {
  if (saveSceneName.value) {
    const data = scene.saveScene()
    data.scene.sceneName = saveSceneName.value
    $http.post('/scene/saveScene', data)
  }
}
function loadModel() {
  if (loadModelUrl.value) scene.loadModel(loadModelUrl.value, {})
}
function loadModelTree() { dialogStore.showModelTree(true) }

// Phase 2 actions
function setSnap() {
  scene.toggleSnap(snapOn.value)
  sceneStore.setSnap({ enabled: snapOn.value, gridSize: snapGridSize.value })
  $bus.emit('snapToggle', { enabled: snapOn.value, gridSize: snapGridSize.value })
}

function openLayerPanel() {
  dialogStore.showLayerPanel(!dialogStore.layerPanel)
}

function openTerrainTools() {
  dialogStore.showTerrainToolbar(!dialogStore.terrainToolbar)
}

function toggleBoxSelect() {
  $bus.emit('toggleBoxSelect', { active: !sceneStore.boxSelectActive })
}

// Batch operations — work on multi-selection or single active model
const hasSelection = computed(() => modelStore.hasMultiSelection || !!modelStore.activeModel)

function getTargetModelIds(): string[] {
  if (modelStore.hasMultiSelection) {
    return Array.from(scene.getSelectedModelIds)
  }
  if (modelStore.activeModel) {
    return [modelStore.activeModelId!]
  }
  return []
}

function refreshActiveSelection() {
  const activeId = modelStore.activeModelId
  modelStore.updateActiveModel(activeId ? scene.getSceneModels[activeId] || null : null)
}

function batchMoveX(delta: number) {
  const ids = getTargetModelIds()
  if (ids.length === 0) return
  ids.forEach(id => {
    const m = scene.getSceneModels[id]
    if (m) {
      m.rootObject.position.x += delta
      m.syncPositionOptions()
    }
  })
  refreshActiveSelection()
}
function batchMoveZ(delta: number) {
  const ids = getTargetModelIds()
  if (ids.length === 0) return
  ids.forEach(id => {
    const m = scene.getSceneModels[id]
    if (m) {
      m.rootObject.position.z += delta
      m.syncPositionOptions()
    }
  })
  refreshActiveSelection()
}
function batchRotate(delta: number) {
  const ids = getTargetModelIds()
  if (ids.length === 0) return
  ids.forEach(id => {
    const m = scene.getSceneModels[id]
    if (m) {
      m.rootObject.rotation.y += delta * Math.PI / 180
      m.syncPositionOptions()
    }
  })
  refreshActiveSelection()
}
function batchScale(factor: number) {
  const ids = getTargetModelIds()
  if (ids.length === 0) return
  ids.forEach(id => {
    const m = scene.getSceneModels[id]
    if (m) {
      const s = Math.max(0.01, m.rootObject.scale.x * factor)
      m.rootObject.scale.setScalar(s)
      m.syncPositionOptions()
    }
  })
  refreshActiveSelection()
}
</script>

<style scoped>
.scene-setting {
  position: absolute;
  right: 16px;
  top: 80px;
  width: 340px;
  max-height: calc(100% - 100px);
  background: rgba(12, 20, 36, 0.9);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  color: #c8d0da;
  text-align: left;
  z-index: 500;
  overflow-y: auto;
  padding-bottom: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}

.pane-slide-enter-active, .pane-slide-leave-active { transition: all 0.3s ease-out; }
.pane-slide-enter-from, .pane-slide-leave-to { transform: translateX(20px); opacity: 0; }

.setting-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.setting-head-left {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e8ecf1;
  font-size: 15px;
  font-weight: 600;
}

.setting-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #00d4ff;
  box-shadow: 0 0 8px rgba(0,212,255,0.5);
}

.setting-collapse {
  padding: 0 4px;
}

.setting-collapse :deep(.el-collapse-item__header) {
  color: #bcc8d4;
  font-size: 13px;
  padding: 0 12px;
  border-color: rgba(255,255,255,0.06);
  background: transparent;
}

.setting-collapse :deep(.el-collapse-item__wrap) {
  background: transparent;
  border-color: rgba(255,255,255,0.06);
}

.setting-collapse :deep(.el-collapse-item__content) {
  color: #c8d0da;
  padding: 8px 12px;
}

.setting-form :deep(.el-form-item__label) {
  color: #8899aa;
  font-size: 12px;
}

.light-slider {
  width: 100px;
  margin-left: 8px;
}

.view-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.view-buttons .el-button {
  font-size: 12px;
}

.batch-section {
  display: flex;
  flex-direction: column;
}

.batch-buttons {
  display: flex;
  gap: 6px;
}

.batch-message {
  font-size: 11px;
  color: #667788;
}

.setting-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0 12px;
  margin-top: 6px;
}

.action-btn {
  flex: 1;
  min-width: 0;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
}
</style>
