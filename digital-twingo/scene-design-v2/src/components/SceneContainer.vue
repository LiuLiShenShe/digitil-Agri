<!--
 *   三维数字孪生设计平台
 *    展示3D模型组件的主窗口
 *    Phase 2: 增加框选、吸附、笔刷交互
 *
 *  @author Sparcle
 *  @version 2.1
 -->

<template>
  <div class="scene" ref="sceneContainerRef" @click="onClick" @mousedown="onMouseDown" v-contextmenu:context-menu
    @pointermove="onBrushMove" @pointerdown="onBrushDown" @pointerup="onBrushUp">
  </div>
  <v-contextmenu ref="contextMenuRef" @show="showContextmenu">
    <v-contextmenu-item @click="deleteModel">删除模型</v-contextmenu-item>
    <v-contextmenu-item @click="copyModel">复制模型</v-contextmenu-item>
    <v-contextmenu-item v-if="modelStore.hasMultiSelection" @click="batchDelete">批量删除 ({{ modelStore.selectedCount }})</v-contextmenu-item>
    <v-contextmenu-item v-if="modelStore.hasMultiSelection" @click="batchCopy">批量复制 ({{ modelStore.selectedCount }})</v-contextmenu-item>
    <v-contextmenu-item v-if="modelStore.hasMultiSelection" @click="batchGroupToLayer">编组到新图层</v-contextmenu-item>
  </v-contextmenu>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Scene } from '@/lib/scene'
import type { TerrainBrush } from '@/lib/terrainBrush'
import { useModelStore } from '@/stores/model'
import { useDialogStore } from '@/stores/dialog'
import { useSceneStore } from '@/stores/scene'
import { useGlobals } from '@/composables/useGlobals'

const { $envCfg, $bus } = useGlobals()
const modelStore = useModelStore()
const dialogStore = useDialogStore()
const sceneStore = useSceneStore()
const route = useRoute()
const router = useRouter()

const sceneContainerRef = ref<HTMLElement>()
const contextMenuRef = ref<any>()

const mouseDownX = ref(0)
const mouseDownY = ref(0)
let brushActive = false
let brushInstance: TerrainBrush | null = null
let brushLayerName = 'grass'
let eraseMode = false

const curModelId = computed(() => {
  const model = modelStore.activeModel
  if (!model) return null
  return model.getModelId
})

onMounted(() => {
  const container = sceneContainerRef.value
  if (!container) return
  Scene.initInstance(container)

  const scene = Scene.getInstance()
  if ($envCfg.editMode) {
    scene.addDragSurport()
  }

  scene.setAmbientLight({ color: '#444444', intensity: 1.2 })
  scene.setBackground({})
  scene.setGrid({})

  $bus.on('winowResize', () => {
    const scene = Scene.getInstance()
    scene.resize(document.body.clientWidth, document.body.clientHeight)
  })

  // Terrain events
  $bus.on('terrainGenerate', (params: any) => {
    scene.generateTerrain(params).catch(err => console.error('Terrain generation error:', err))
  })
  $bus.on('terrainClear', () => {
    scene.removeTerrain()
  })

  // Layer events
  $bus.on('layerAdd', (opts: { name: string; color: string }) => {
    scene.createLayer(opts.name, opts.color)
  })
  $bus.on('layerRemove', (opts: { id: string }) => {
    scene.deleteLayer(opts.id)
  })
  $bus.on('layerToggleVisible', (opts: { id: string }) => {
    scene.toggleLayerVisible(opts.id)
  })
  $bus.on('layerToggleLocked', (opts: { id: string }) => {
    scene.toggleLayerLocked(opts.id)
  })
  $bus.on('layerRename', (opts: { id: string; name: string }) => {
    scene.renameLayer(opts.id, opts.name)
  })
  $bus.on('layerSelectAll', (opts: { layerId: string }) => {
    scene.selectModelsInLayer(opts.layerId)
  })
  $bus.on('batchMoveToLayer', (opts: { targetLayerId: string }) => {
    scene.moveModelsToLayer(Array.from(scene.getSelectedModelIds), opts.targetLayerId)
  })

  // Box Select
  $bus.on('toggleBoxSelect', (opts: { active: boolean }) => {
    scene.toggleBoxSelect()
    sceneStore.setBoxSelectActive(opts.active)
  })

  // Terrain Brush
  $bus.on('terrainBrushToggle', (opts: { active: boolean; config: any }) => {
    brushActive = opts.active
    if (opts.active) {
      brushInstance = scene.initTerrainBrush()
      if (scene.getGroundPane) {
        brushInstance.bindGround(scene.getGroundPane)
      }
      brushInstance.setBrushConfig({
        size: opts.config.size,
        opacity: opts.config.opacity,
        hardness: opts.config.hardness,
        texture: opts.config.texture
      })
      brushLayerName = opts.config.texture
      eraseMode = opts.config.erase
    } else {
      if (brushInstance) {
        brushInstance.endPaint()
      }
    }
    sceneStore.setTerrainBrushActive(opts.active)
  })

  // Snap
  $bus.on('snapToggle', (opts: { enabled: boolean; gridSize: number }) => {
    scene.setSnapConfig({ enabled: opts.enabled, gridSize: opts.gridSize })
    sceneStore.setSnap(opts)
  })

  // Template
  $bus.on('templateApply', (opts: { id: string }) => {
    scene.applyTemplate(opts.id)
  })

  focusFromRouteQuery()
})

onUnmounted(() => {
  const scene = Scene.getInstance()
  scene.dispose()
})

function onClick(event: any) {
  if (brushActive && brushInstance) return
  if (!mouseDownX.value || !mouseDownY.value) return
  const deltaX = event.clientX - mouseDownX.value
  const deltaY = event.clientY - mouseDownY.value
  if ((deltaX * deltaX + deltaY * deltaY) > 2) return

  const scene = Scene.getInstance()
  const selectModel = scene.selectModel(event.clientX, event.clientY)
  modelStore.updateActiveModel(selectModel)
  dialogStore.showPropPane(selectModel != null)
}

async function focusFromRouteQuery() {
  const sceneObjectId = typeof route.query.sceneObjectId === 'string' ? route.query.sceneObjectId : ''
  if (!sceneObjectId) return
  const sceneName = typeof route.query.scene === 'string' ? route.query.scene : ''
  const scene = Scene.getInstance()
  try {
    if (sceneName && sceneName !== scene.getSceneName()) {
      await scene.laodScene(sceneName)
    }
    await nextTick()
    const model = scene.focusSceneObject(sceneObjectId)
    if (model) {
      modelStore.updateActiveModel(model)
      dialogStore.showPropPane(true)
      ElMessage.success('已定位到场景对象')
    } else {
      ElMessage.warning('当前场景无可定位模型')
    }
  } catch {
    ElMessage.error('场景定位失败')
  } finally {
    router.replace({ path: '/', query: {} })
  }
}

function onMouseDown(event: any) {
  mouseDownX.value = event.clientX
  mouseDownY.value = event.clientY
}

// Brush interaction
function onBrushMove(event: PointerEvent) {
  if (!brushActive || !brushInstance) return
  const scene = Scene.getInstance()
  const hit = scene.getGroundIntersection(event)
  if (hit) {
    const { uv } = hit
    if (eraseMode) {
      brushInstance.eraseStroke(uv.u, uv.v, brushLayerName)
    } else {
      brushInstance.paintStroke(uv.u, uv.v, brushLayerName)
    }
  }
}

function onBrushDown(event: PointerEvent) {
  if (!brushActive || !brushInstance) return
  brushInstance.beginPaint()
  onBrushMove(event)
}

function onBrushUp() {
  if (!brushActive || !brushInstance) return
  brushInstance.endPaint()
}

// Context menu
function showContextmenu() {
  if (!curModelId.value && !modelStore.hasMultiSelection) {
    const cm = contextMenuRef.value as any
    if (cm) { cm.hide() }
    return
  }
}

function deleteModel() {
  if (curModelId.value) {
    const scene = Scene.getInstance()
    scene.removeModel(curModelId.value)
    modelStore.updateActiveModel(null)
    dialogStore.showPropPane(false)
  }
}

function copyModel() {
  if (curModelId.value) {
    const scene = Scene.getInstance()
    scene.copyModel(curModelId.value)
  }
}

function batchDelete() {
  const scene = Scene.getInstance()
  scene.batchDelete()
  dialogStore.showPropPane(false)
}

function batchCopy() {
  const scene = Scene.getInstance()
  scene.batchCopy()
}

function batchGroupToLayer() {
  const scene = Scene.getInstance()
  const layer = scene.createLayer('新建编组', '#4090ff')
  scene.moveModelsToLayer(Array.from(scene.getSelectedModelIds), layer.id)
}
</script>

<style scoped>
.scene {
  width: 100%;
  height: 100%;
  display: flex;
  overflow: hidden;
  padding: 0;
  background: radial-gradient(ellipse at center, #0d1a30 0%, #070b18 100%);
}
</style>
