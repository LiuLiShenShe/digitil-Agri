/**
 *   三维数字孪生设计平台
 *
 *  @brief Pinia store — 管理各全局对话框状态
 *    Phase 2: 新增图层面板、地形工具栏标志
 *
 *  @author Sparcle
 *  @version 2.1
 **/

import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDialogStore = defineStore('dialog', () => {
  const propPane = ref(false)
  const sceneSettingPane = ref(false)
  const saveDialog = ref(false)
  const modelTreeDialog = ref(false)
  const layerPanel = ref(false)
  const terrainToolbar = ref(false)
  const dataVizPanel = ref(false)
  const iotPanel = ref(false)
  const alertPanel = ref(false)
  const cameraPanel = ref(false)

  function showPropPane(show: boolean) {
    propPane.value = show
  }

  function showSceneSettingPane(show: boolean) {
    sceneSettingPane.value = show
  }

  function showSaveDialog(show: boolean) {
    saveDialog.value = show
  }

  function showModelTree(show: boolean) {
    modelTreeDialog.value = show
  }

  function showLayerPanel(show: boolean) {
    layerPanel.value = show
  }

  function showTerrainToolbar(show: boolean) {
    terrainToolbar.value = show
  }

  function showDataVizPanel(show: boolean) {
    dataVizPanel.value = show
  }

  function showIotPanel(show: boolean) {
    iotPanel.value = show
  }

  function showAlertPanel(show: boolean) {
    alertPanel.value = show
  }

  function showCameraPanel(show: boolean) {
    cameraPanel.value = show
  }

  return {
    propPane,
    sceneSettingPane,
    saveDialog,
    modelTreeDialog,
    layerPanel,
    terrainToolbar,
    dataVizPanel,
    iotPanel,
    alertPanel,
    cameraPanel,
    showPropPane,
    showSceneSettingPane,
    showSaveDialog,
    showModelTree,
    showLayerPanel,
    showTerrainToolbar,
    showDataVizPanel,
    showIotPanel,
    showAlertPanel,
    showCameraPanel
  }
})
