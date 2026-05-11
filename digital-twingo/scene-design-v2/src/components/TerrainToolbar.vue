<!--
 * 地形工具栏 — 地形导入、纹理刷工具
 -->
<template>
  <transition name="pane-slide">
    <div class="terrain-toolbar" v-show="dialogStore.terrainToolbar">
      <div class="toolbar-head">
        <div class="toolbar-head-left">
          <span class="toolbar-dot"></span>
          <span>地形工具</span>
        </div>
        <el-button type="danger" :icon="Close" circle size="small" plain @click="close" />
      </div>

      <el-collapse v-model="activeTab" class="toolbar-collapse">
        <!-- 地形导入 -->
        <el-collapse-item title="地形导入" name="import">
          <el-form label-width="70px" size="small" class="toolbar-form">
            <el-form-item label="导入方式">
              <el-select v-model="importType" size="small" style="width:100%">
                <el-option label="高度图 (图片)" value="heightmap" />
                <el-option label="GeoJSON" value="geojson" />
                <el-option label="DEM 数据" value="dem" />
              </el-select>
            </el-form-item>

            <el-form-item label="文件URL" v-if="importType === 'heightmap' || importType === 'dem'">
              <el-input v-model="heightmapUrl" placeholder="输入高度图 URL" size="small" />
            </el-form-item>

            <el-form-item label="GeoJSON URL" v-if="importType === 'geojson'">
              <el-input v-model="geojsonUrl" placeholder="输入 GeoJSON URL" size="small" />
            </el-form-item>

            <el-form-item label="地形宽度">
              <el-slider v-model="terrainWidth" :min="200" :max="3000" :step="100" show-input size="small" />
            </el-form-item>

            <el-form-item label="地形深度">
              <el-slider v-model="terrainDepth" :min="200" :max="3000" :step="100" show-input size="small" />
            </el-form-item>

            <el-form-item label="高度缩放">
              <el-slider v-model="heightScale" :min="5" :max="200" show-input size="small" />
            </el-form-item>

            <el-form-item label="网格密度">
              <el-select v-model="segments" size="small">
                <el-option label="64 (低)" :value="64" />
                <el-option label="128 (中)" :value="128" />
                <el-option label="256 (高)" :value="256" />
              </el-select>
            </el-form-item>

            <el-form-item label="低处颜色">
              <el-color-picker v-model="colorLow" size="small" />
            </el-form-item>

            <el-form-item label="高处颜色">
              <el-color-picker v-model="colorHigh" size="small" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" size="small" @click="generateTerrain" :loading="generating">
                {{ generating ? '生成中...' : '生成地形' }}
              </el-button>
              <el-button size="small" @click="clearTerrain" v-if="hasTerrain">清除地形</el-button>
            </el-form-item>
          </el-form>
        </el-collapse-item>

        <!-- 纹理刷 -->
        <el-collapse-item title="纹理刷" name="brush">
          <el-form label-width="70px" size="small" class="toolbar-form">
            <el-form-item label="当前纹理">
              <el-select v-model="activeBrushTexture" size="small" style="width:100%">
                <el-option label="草地" value="grass" />
                <el-option label="泥土" value="dirt" />
                <el-option label="水泥" value="concrete" />
                <el-option label="沙地" value="sand" />
              </el-select>
            </el-form-item>

            <el-form-item label="笔刷大小">
              <el-slider v-model="brushSize" :min="10" :max="200" show-input size="small" />
            </el-form-item>

            <el-form-item label="透明度">
              <el-slider v-model="brushOpacity" :min="0.1" :max="1" :step="0.1" show-input size="small" />
            </el-form-item>

            <el-form-item label="硬度">
              <el-slider v-model="brushHardness" :min="0.1" :max="1" :step="0.1" show-input size="small" />
            </el-form-item>

            <el-form-item>
              <el-switch v-model="eraseMode" active-text="擦除" inactive-text="绘制" size="small" />
            </el-form-item>

            <el-form-item>
              <el-button
                :type="brushActive ? 'warning' : 'success'"
                size="small"
                @click="toggleBrush"
              >
                {{ brushActive ? '退出纹理刷' : '开始绘制' }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-collapse-item>

        <!-- 场景模板 -->
        <el-collapse-item title="场景模板" name="template">
          <div class="template-list">
            <div
              v-for="tpl in templates"
              :key="tpl.id"
              class="template-item"
              @click="applyTemplate(tpl.id)"
            >
              <div class="template-info">
                <span class="template-name">{{ tpl.name }}</span>
                <span class="template-desc">{{ tpl.description }}</span>
              </div>
              <el-button size="small" type="primary">应用</el-button>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Close } from '@element-plus/icons-vue'
import { useDialogStore } from '@/stores/dialog'
import { useGlobals } from '@/composables/useGlobals'
import { sceneTemplates } from '@/data/templates'

const { $bus } = useGlobals()
const dialogStore = useDialogStore()

const visible = ref(false)
const activeTab = ref('')

// Import state
const importType = ref('heightmap')
const heightmapUrl = ref('/textures/heightmap.png')
const geojsonUrl = ref('')
const terrainWidth = ref(1000)
const terrainDepth = ref(1000)
const heightScale = ref(80)
const segments = ref(128)
const colorLow = ref('#336633')
const colorHigh = ref('#88cc44')
const generating = ref(false)
const hasTerrain = ref(false)

// Brush state
const activeBrushTexture = ref('grass')
const brushSize = ref(60)
const brushOpacity = ref(0.7)
const brushHardness = ref(0.5)
const eraseMode = ref(false)
const brushActive = ref(false)

const templates = sceneTemplates

function close() { dialogStore.showTerrainToolbar(false) }
function show() { dialogStore.showTerrainToolbar(true) }

function generateTerrain() {
  generating.value = true
  const params: any = {
    type: importType.value,
    width: terrainWidth.value,
    depth: terrainDepth.value,
    segments: segments.value,
    heightScale: heightScale.value,
    colorLow: colorLow.value,
    colorHigh: colorHigh.value
  }
  if (importType.value === 'heightmap' || importType.value === 'dem') {
    params.url = heightmapUrl.value
  } else if (importType.value === 'geojson') {
    params.url = geojsonUrl.value
  }
  $bus.emit('terrainGenerate', params)
  setTimeout(() => { generating.value = false; hasTerrain.value = true }, 2000)
}

function clearTerrain() {
  $bus.emit('terrainClear')
  hasTerrain.value = false
}

function toggleBrush() {
  brushActive.value = !brushActive.value
  $bus.emit('terrainBrushToggle', {
    active: brushActive.value,
    config: {
      texture: activeBrushTexture.value,
      size: brushSize.value,
      opacity: brushOpacity.value,
      hardness: brushHardness.value,
      erase: eraseMode.value
    }
  })
}

function applyTemplate(templateId: string) {
  $bus.emit('templateApply', { id: templateId })
}

defineExpose({ show })
</script>

<style scoped>
.terrain-toolbar {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 360px;
  max-height: 520px;
  background: rgba(12, 20, 36, 0.95);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  color: #c8d0da;
  text-align: left;
  z-index: 500;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}

.pane-slide-enter-active, .pane-slide-leave-active { transition: all 0.3s ease-out; }
.pane-slide-enter-from, .pane-slide-leave-to { transform: translateX(20px); opacity: 0; }

.toolbar-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.toolbar-head-left {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e8ecf1;
  font-size: 14px;
  font-weight: 600;
}

.toolbar-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4090ff;
  box-shadow: 0 0 8px rgba(64,144,255,0.5);
}

.toolbar-collapse {
  padding: 0 4px;
}

.toolbar-collapse :deep(.el-collapse-item__header) {
  color: #bcc8d4;
  font-size: 13px;
  padding: 0 12px;
  border-color: rgba(255,255,255,0.06);
  background: transparent;
}

.toolbar-collapse :deep(.el-collapse-item__wrap) {
  background: transparent;
  border-color: rgba(255,255,255,0.06);
}

.toolbar-collapse :deep(.el-collapse-item__content) {
  color: #c8d0da;
  padding: 8px 12px;
}

.toolbar-form :deep(.el-form-item__label) {
  color: #8899aa;
  font-size: 12px;
}

.template-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.template-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}

.template-item:hover {
  background: rgba(0,212,255,0.06);
  border-color: rgba(0,212,255,0.15);
}

.template-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.template-name {
  font-size: 13px;
  color: #e8ecf1;
}

.template-desc {
  font-size: 11px;
  color: #667788;
}
</style>
