<!--
 *   三维数字孪生设计平台
 *    主界面头部菜单
 *
 *  @author Sparcle
 *  @version 2.1
 -->

<template>
  <el-header class="head-menu">
    <div class="head-left">
      <!-- 新Logo: SVG 内嵌 -->
      <svg class="head-logo-svg" viewBox="0 0 200 48" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#00d4ff;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#4090ff;stop-opacity:1" />
          </linearGradient>
          <linearGradient id="logoGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#00d4ff;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#60b8ff;stop-opacity:1" />
          </linearGradient>
        </defs>
        <!-- 3D cube icon -->
        <g transform="translate(6,6)">
          <polygon points="18,0 36,10 36,28 18,38 0,28 0,10" fill="none" stroke="url(#logoGrad)" stroke-width="2.5" stroke-linejoin="round"/>
          <polygon points="18,0 36,10 18,20 0,10" fill="url(#logoGrad)" opacity="0.35"/>
          <polygon points="18,20 36,10 36,28 18,38" fill="url(#logoGrad)" opacity="0.18"/>
          <polygon points="18,20 0,10 0,28 18,38" fill="url(#logoGrad)" opacity="0.25"/>
        </g>
        <!-- text -->
        <text x="52" y="22" font-family="'PingFang SC','Microsoft YaHei',sans-serif" font-size="13" font-weight="700" fill="url(#logoGrad2)">数字孪生</text>
        <text x="52" y="39" font-family="'PingFang SC','Microsoft YaHei',sans-serif" font-size="10" font-weight="400" fill="#8899aa" letter-spacing="3">DIGITAL TWIN</text>
      </svg>
      <span class="head-menu-title">{{ headTitle }}</span>
    </div>

    <el-menu
      class="head-nav-menu"
      mode="horizontal"
      background-color="transparent"
      text-color="#bcc8d4"
      active-text-color="#00d4ff"
      menu-trigger="click"
      @open="onMenuOpen"
    >
      <el-sub-menu index="1" popper-class="head-sub-menu" v-if="editMode">
        <template #title>
          <span class="nav-item">场景</span>
        </template>
        <el-menu-item index="1-1" @click="newScene">
          <span>新建</span>
        </el-menu-item>
        <el-menu-item index="1-3" @click="onSaveScene">
          <span>保存</span>
        </el-menu-item>
        <el-divider style="margin:4px 0;border-color:rgba(255,255,255,0.08)" />
        <el-menu-item v-if="sceneListLoading" index="1-loading" disabled>
          <span style="color:#8899aa;font-size:12px">场景列表加载中...</span>
        </el-menu-item>
        <el-menu-item v-else-if="sceneListError" index="1-error" @click="loadSceneList">
          <span style="color:#f56c6c;font-size:12px">{{ sceneListError }}，点击重试</span>
        </el-menu-item>
        <el-menu-item
          v-else
          v-for="(item, idx) in sceneList"
          :key="item"
          :index="'1-2-' + idx"
          @click="loadScene(item)">
          <span>打开: {{ item }}</span>
        </el-menu-item>
        <el-menu-item v-if="!sceneListLoading && !sceneListError && sceneList.length === 0" index="1-empty" disabled>
          <span style="color:#8899aa;font-size:12px">暂无已保存场景</span>
        </el-menu-item>
      </el-sub-menu>

      <el-menu-item index="2" @click="sceneSetting">
        <span class="nav-item">设置</span>
      </el-menu-item>

      <el-menu-item index="3" @click="toggleDataViz">
        <span class="nav-item">数据</span>
      </el-menu-item>

      <el-menu-item index="4" @click="toggleIotPanel">
        <span class="nav-item">IoT设备</span>
      </el-menu-item>

      <el-menu-item index="5" @click="toggleAlertPanel">
        <span class="nav-item">告警</span>
        <span class="alert-menu-badge" v-if="alertStore.unackedCount > 0">{{ alertStore.unackedCount }}</span>
      </el-menu-item>

      <el-menu-item index="6" @click="toggleCameraPanel">
        <span class="nav-item">监控</span>
      </el-menu-item>

      <el-menu-item index="7" @click="openMonitorCenter">
        <span class="nav-item">大屏</span>
      </el-menu-item>
    </el-menu>
  </el-header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Scene } from '@/lib/scene'
import { useSceneStore } from '@/stores/scene'
import { useDialogStore } from '@/stores/dialog'
import { useAlertStore } from '@/stores/alert'
import { useIotStore } from '@/stores/iot'
import { getRealtimeService } from '@/services/websocket'
import { connectIoTWebSocket, disconnectIoTWebSocket, fetchDevices, fetchAlerts } from '@/services/iotService'
import { useGlobals } from '@/composables/useGlobals'

const { $http, $envCfg, $bus } = useGlobals()
const sceneStore = useSceneStore()
const dialogStore = useDialogStore()
const alertStore = useAlertStore()
const iotStore = useIotStore()
const scene = Scene.getInstance()
const router = useRouter()

const sceneList = ref<string[]>([])
const sceneListLoading = ref(false)
const sceneListError = ref('')

const editMode = computed(() => $envCfg.editMode)
const headTitle = computed(() => {
  if (editMode.value) {
    return '场景设计'
  } else {
    return sceneStore.sceneName
  }
})

onMounted(() => {
  // Phase 4: Connect IoT WebSocket for real-time device data
  connectIoTWebSocket()

  if (editMode.value) {
    loadSceneList()
    $bus.on('sceneSaved', loadSceneList)
  } else {
    $http.get('/scene/defaultScene').then((res) => {
      if (res.data.code === 200 && res.data.data) {
        loadScene(res.data.data)
      }
    }).catch(() => {
      ElMessage.error('加载默认场景失败')
    })
  }
})

onUnmounted(() => {
  $bus.off('sceneSaved', loadSceneList)
})

function onMenuOpen(index: string) {
  if (index === '1') {
    loadSceneList()
  }
}

async function loadSceneList() {
  if (!editMode.value) return
  sceneListLoading.value = true
  sceneListError.value = ''
  try {
    const res = await $http.get('/scene/sceneList', { timeout: 8000 })
    if (res.data.code === 200 && Array.isArray(res.data.data)) {
      sceneList.value = res.data.data.filter((item: string) => !!item)
    } else {
      sceneList.value = []
      sceneListError.value = '获取场景列表失败'
    }
  } catch {
    sceneList.value = []
    sceneListError.value = '获取场景列表失败'
  } finally {
    sceneListLoading.value = false
  }
}

function sceneSetting() {
  dialogStore.showSceneSettingPane(true)
}

function toggleDataViz() {
  dialogStore.showDataVizPanel(!dialogStore.dataVizPanel)
}

function toggleIotPanel() {
  const show = !dialogStore.iotPanel
  dialogStore.showIotPanel(show)
  if (show) {
    loadIoTData()
  }
}

function toggleAlertPanel() {
  dialogStore.showAlertPanel(!dialogStore.alertPanel)
  if (dialogStore.alertPanel) {
    alertStore.setLoading(true)
    fetchAlerts().finally(() => alertStore.setLoading(false))
  }
}

function toggleCameraPanel() {
  dialogStore.showCameraPanel(!dialogStore.cameraPanel)
}

function openMonitorCenter() {
  router.push('/monitor')
}

async function loadIoTData() {
  iotStore.setLoading(true)
  await fetchDevices()
  iotStore.setLoading(false)
}

function newScene() {
  scene.newScene()
}

function onSaveScene() {
  dialogStore.showSaveDialog(true)
}

function loadScene(sceneName: string) {
  scene.laodScene(sceneName).catch(() => {
    ElMessage.error('加载场景失败: ' + sceneName)
  })
}
</script>

<style scoped>
.head-menu {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  padding: 0 20px;
  background: linear-gradient(180deg, rgba(8, 16, 30, 0.95) 0%, rgba(8, 16, 30, 0.6) 70%, transparent 100%);
  backdrop-filter: blur(10px);
  z-index: 600;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.head-left {
  display: flex;
  align-items: center;
  gap: 0;
}

.head-logo-svg {
  width: 200px;
  height: 48px;
  flex-shrink: 0;
}

.head-menu-title {
  font-size: 15px;
  color: #8899aa;
  margin-left: 12px;
  padding-left: 12px;
  border-left: 1px solid rgba(255,255,255,0.12);
  line-height: 60px;
  white-space: nowrap;
}

.head-nav-menu {
  background: transparent !important;
  border: none !important;
}

.head-nav-menu :deep(.el-menu-item),
.head-nav-menu :deep(.el-sub-menu__title) {
  border-bottom: 2px solid transparent !important;
  height: 60px;
  line-height: 60px;
  transition: all 0.25s;
}

.head-nav-menu :deep(.el-menu-item:hover),
.head-nav-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(255,255,255,0.04) !important;
  border-bottom-color: rgba(0,212,255,0.3) !important;
}

.nav-item {
  font-size: 14px;
  letter-spacing: 1px;
}

.alert-menu-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  margin-left: 4px;
  border-radius: 9px;
  background: #ff4444;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
}
</style>
