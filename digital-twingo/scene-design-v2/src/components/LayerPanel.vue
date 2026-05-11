<!--
 * 图层管理面板 — 管理场景中模型的分组/图层
 -->
<template>
  <transition name="pane-slide">
    <div class="layer-panel" v-show="dialogStore.layerPanel">
      <div class="panel-head">
        <div class="panel-head-left">
          <span class="panel-dot"></span>
          <span>图层管理</span>
        </div>
        <div class="panel-head-actions">
          <el-button type="primary" :icon="Plus" circle size="small" @click="addLayer" />
          <el-button type="danger" :icon="Close" circle size="small" plain @click="close" />
        </div>
      </div>

      <div class="layer-list">
        <div
          v-for="layer in layerStore.layers"
          :key="layer.id"
          class="layer-item"
          :class="{ active: layer.id === layerStore.selectedLayerId }"
          @click="layerStore.selectLayer(layer.id)"
        >
          <div class="layer-left">
            <span class="layer-color" :style="{ background: layer.color }"></span>
            <span v-if="editingId !== layer.id" class="layer-name">{{ layer.name }}</span>
            <el-input
              v-else
              v-model="editName"
              size="small"
              class="layer-name-input"
              @blur="finishRename(layer.id)"
              @keyup.enter="finishRename(layer.id)"
            />
            <span class="layer-count">{{ layer.modelIds.size }}</span>
          </div>
          <div class="layer-right">
            <el-button
              :type="layer.visible ? 'primary' : 'info'"
              :icon="layer.visible ? View : Hide"
              size="small"
              circle
              plain
              @click.stop="toggleVisible(layer.id)"
            />
            <el-button
              :type="layer.locked ? 'warning' : 'info'"
              :icon="layer.locked ? Lock : Unlock"
              size="small"
              circle
              plain
              @click.stop="toggleLocked(layer.id)"
            />
            <el-button
              v-if="layer.id !== 'default'"
              type="danger"
              :icon="Delete"
              size="small"
              circle
              plain
              @click.stop="removeLayer(layer.id)"
            />
          </div>
        </div>
      </div>

      <div class="batch-tools" v-if="$envCfg.editMode">
        <el-divider>批量操作</el-divider>
        <div class="batch-buttons">
          <el-button size="small" @click="selectAllInLayer">全选当前层</el-button>
          <el-button size="small" @click="batchMoveToLayer">移至图层</el-button>
          <el-button size="small" type="success" @click="toggleBoxSelect">
            {{ boxSelectActive ? '退出框选' : '框选模式' }}
          </el-button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Plus, Close, View, Hide, Lock, Unlock, Delete } from '@element-plus/icons-vue'
import { useLayerStore } from '@/stores/layer'
import { useDialogStore } from '@/stores/dialog'
import { useGlobals } from '@/composables/useGlobals'

const { $envCfg, $bus } = useGlobals()
const layerStore = useLayerStore()
const dialogStore = useDialogStore()

const editingId = ref<string | null>(null)
const editName = ref('')
const boxSelectActive = ref(false)

function close() { dialogStore.showLayerPanel(false) }

function addLayer() {
  const name = `图层 ${layerStore.layers.length + 1}`
  $bus.emit('layerAdd', { name, color: '#ffffff' })
}

function removeLayer(id: string) {
  $bus.emit('layerRemove', { id })
}

function toggleVisible(id: string) {
  $bus.emit('layerToggleVisible', { id })
}

function toggleLocked(id: string) {
  $bus.emit('layerToggleLocked', { id })
}

function startRename(id: string) {
  const layer = layerStore.layers.find(l => l.id === id)
  if (!layer) return
  editingId.value = id
  editName.value = layer.name
}

function finishRename(id: string) {
  if (editName.value.trim()) {
    $bus.emit('layerRename', { id, name: editName.value.trim() })
  }
  editingId.value = null
}

function selectAllInLayer() {
  $bus.emit('layerSelectAll', { layerId: layerStore.selectedLayerId })
}

function batchMoveToLayer() {
  $bus.emit('batchMoveToLayer', { targetLayerId: layerStore.selectedLayerId })
}

function toggleBoxSelect() {
  boxSelectActive.value = !boxSelectActive.value
  $bus.emit('toggleBoxSelect', { active: boxSelectActive.value })
}
</script>

<style scoped>
.layer-panel {
  position: absolute;
  right: 16px;
  top: 360px;
  width: 300px;
  max-height: 420px;
  background: rgba(12, 20, 36, 0.92);
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

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.panel-head-left {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e8ecf1;
  font-size: 14px;
  font-weight: 600;
}

.panel-head-actions {
  display: flex;
  gap: 6px;
}

.panel-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #00d4ff;
  box-shadow: 0 0 8px rgba(0,212,255,0.5);
}

.layer-list {
  padding: 8px 0;
}

.layer-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  cursor: pointer;
  transition: background 0.15s;
}

.layer-item:hover { background: rgba(255,255,255,0.04); }
.layer-item.active { background: rgba(0,212,255,0.08); border-left: 2px solid #00d4ff; }

.layer-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.layer-color {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  flex-shrink: 0;
}

.layer-name {
  font-size: 13px;
  color: #bcc8d4;
}

.layer-name-input {
  width: 100px;
}

.layer-count {
  font-size: 11px;
  color: #667788;
  background: rgba(255,255,255,0.06);
  padding: 1px 6px;
  border-radius: 8px;
}

.layer-right {
  display: flex;
  gap: 4px;
}

.batch-tools {
  padding: 0 14px 12px;
}

.batch-tools :deep(.el-divider__text) {
  color: #667788;
  font-size: 11px;
}

.batch-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
</style>
