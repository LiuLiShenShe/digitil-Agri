<!--
 *   三维数字孪生设计平台
 *    程序主界面
 *    Phase 2: 新增图层管理面板、地形工具栏
 *
 *  @author Sparcle
 *  @version 2.1
 -->

<template>
  <SceneContainer />
  <HeadMenu />
  <ProperityPane />
  <SceneSettingPane />
  <LayerPanel />
  <TerrainToolbar ref="terrainToolbarRef" />
  <DataVizPanel />
  <IoTDevicePanel />
  <AlertPanel />
  <CameraView />
  <SaveDialog />
  <ModelTreeDialog />
</template>

<script setup lang="ts">
import SceneContainer from '@/components/SceneContainer.vue'
import SceneSettingPane from '@/components/SceneSetting.vue'
import HeadMenu from '@/components/HeadMenu.vue'
import ProperityPane from '@/components/ProperityPane.vue'
import LayerPanel from '@/components/LayerPanel.vue'
import TerrainToolbar from '@/components/TerrainToolbar.vue'
import DataVizPanel from '@/components/DataVizPanel.vue'
import IoTDevicePanel from '@/components/IoTDevicePanel.vue'
import AlertPanel from '@/components/AlertPanel.vue'
import CameraView from '@/components/CameraView.vue'
import SaveDialog from '@/components/SaveDialog.vue'
import ModelTreeDialog from '@/components/ModelTreeDialg.vue'
</script>
