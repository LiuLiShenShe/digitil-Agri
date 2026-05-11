/**
 *   三维数字孪生设计平台
 *
 *  @brief Pinia store — 管理当前场景的配置参数
 *    Phase 2: 新增地形、吸附状态
 *
 *  @author Sparcle
 *  @version 2.1
 **/

import { defineStore } from 'pinia'
import { reactive, ref } from 'vue'

interface Light {
  color: string
  intent: number
  on: boolean
}

interface SpotLight extends Light {
  angle: number
  distance: number
  hight: number
}

export const useSceneStore = defineStore('scene', () => {
  // Lights
  const ambLight = reactive<Light>({ color: '#ffffff', intent: 0.6, on: false })
  const dirLight = reactive<Light>({ color: '#ffffff', intent: 1.0, on: false })
  const spotLight = reactive<SpotLight>({ color: '#ffffff', intent: 1.0, on: false, distance: 500, angle: 0, hight: 300 })

  // Background
  const background = reactive({ skybox: '', on: false })
  const groundPane = reactive({ texture: '', color: '#88cc88', on: false })
  const helperGrid = reactive({ on: false })

  // Phase 2: Terrain & Snap
  const terrain = reactive({ on: false, type: '', width: 1000, depth: 1000 })
  const snap = reactive({ enabled: false, gridSize: 10 })
  const terrainBrushActive = ref(false)
  const boxSelectActive = ref(false)

  const sceneName = ref('新建场景')

  function setAmbLight(options: Light) {
    Object.assign(ambLight, options)
  }

  function turnOffLight(light: string) {
    if (light === 'ambientLight') ambLight.on = false
    else if (light === 'directionalLight') dirLight.on = false
    else if (light === 'spotLight') spotLight.on = false
  }

  function setDirLight(options: Light) {
    Object.assign(dirLight, options)
  }

  function setSpotLight(options: SpotLight) {
    Object.assign(spotLight, options)
  }

  function turnOffBackground(obj: string) {
    if (obj === 'skybox') background.on = false
    else if (obj === 'ground') groundPane.on = false
    else if (obj === 'grid') helperGrid.on = false
  }

  function setSkybox(box: string) {
    background.skybox = box
    background.on = true
  }

  function setGroundPane(pane: any) {
    Object.assign(groundPane, pane)
  }

  function setGrid(grid: any) {
    Object.assign(helperGrid, grid)
  }

  function setSceneName(name: string) {
    sceneName.value = name
  }

  function setTerrain(t: any) {
    Object.assign(terrain, t)
  }

  function setSnap(s: any) {
    Object.assign(snap, s)
  }

  function setTerrainBrushActive(active: boolean) {
    terrainBrushActive.value = active
  }

  function setBoxSelectActive(active: boolean) {
    boxSelectActive.value = active
  }

  return {
    ambLight,
    dirLight,
    spotLight,
    background,
    groundPane,
    helperGrid,
    terrain,
    snap,
    terrainBrushActive,
    boxSelectActive,
    sceneName,
    setAmbLight,
    turnOffLight,
    setDirLight,
    setSpotLight,
    turnOffBackground,
    setSkybox,
    setGroundPane,
    setGrid,
    setSceneName,
    setTerrain,
    setSnap,
    setTerrainBrushActive,
    setBoxSelectActive
  }
})
