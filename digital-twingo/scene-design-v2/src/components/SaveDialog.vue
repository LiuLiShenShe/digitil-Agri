<!--
 *   三维数字孪生设计平台
 *    保存场景对话框
 *
 *  @author Sparcle
 *  @version 2.1
 -->

<template>
  <el-dialog title="保存当前场景" v-model="dlgShow" width="400px" class="save-dialog">
    <el-input v-model="sceneName" placeholder="输入场景名字" size="large" clearable />
    <template #footer>
      <el-button @click="onCancel" size="default">取消</el-button>
      <el-button type="primary" @click="onOk" size="default">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Scene } from '@/lib/scene'
import { useSceneStore } from '@/stores/scene'
import { useDialogStore } from '@/stores/dialog'
import { useGlobals } from '@/composables/useGlobals'

const { $http, $bus } = useGlobals()
const sceneStore = useSceneStore()
const dialogStore = useDialogStore()
const scene = Scene.getInstance()

const dlgShow = computed({
  get: () => dialogStore.saveDialog,
  set: (val) => dialogStore.showSaveDialog(val)
})

const sceneName = computed({
  get: () => sceneStore.sceneName,
  set: (val) => scene.setSceneName(val)
})

function onOk() {
  const name = sceneName.value
  $http.get('/scene/sceneList').then((res) => {
    const list = res.data.data as string[]
    if (list.includes(name)) {
      ElMessageBox.confirm(`场景 [${name}] 已经存在，是否覆盖?`, '警告', {
        confirmButtonText: '覆盖',
        cancelButtonText: '另存为',
        type: 'warning'
      }).then(() => {
        saveScene()
      }).catch(() => {
        return
      })
    } else {
      saveScene()
    }
  })
}

function onCancel() {
  dialogStore.showSaveDialog(false)
}

function saveScene() {
  const data = scene.saveScene()
  data.scene.sceneName = sceneName.value
  $http.post('/scene/saveScene', data).then(() => {
    ElMessage({ message: '场景保存成功!', type: 'success' })
    $bus.emit('sceneSaved')
    dialogStore.showSaveDialog(false)
  })
}
</script>

<style scoped>
.save-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 16px;
}
</style>
