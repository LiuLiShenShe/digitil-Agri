<!--
 *   三维数字孪生设计平台
 *    摄像头视频流面板 — Phase 4
 *    在3D场景选中摄像头模型后查看实时视频流
 *
 *  @author Sparcle
 *  @version 4.0
 -->

<template>
  <transition name="viz-slide">
    <div
      ref="panelRef"
      class="camera-panel glass-panel"
      :class="{ dragging }"
      :style="panelStyle"
      v-show="dialogStore.cameraPanel"
      @pointerdown="bringToFront"
    >
      <div class="panel-head" title="拖动移动面板，双击回到默认位置" @pointerdown="startDrag" @dblclick="resetPosition">
        <div class="panel-head-left">
          <span class="panel-dot live"></span>
          <span class="panel-title">视频监控</span>
          <span class="stream-status" v-if="streamActive" style="color: #22dd66;">● 实时</span>
          <span class="stream-status" v-else style="color: #666;">● 待连接</span>
        </div>
        <div class="panel-head-right">
          <el-button type="danger" :icon="Close" circle size="small" plain @click="closeCamera" />
        </div>
      </div>

      <!-- 摄像头选择 -->
      <div class="cam-selector">
        <el-select v-model="selectedCamera" placeholder="选择摄像头" size="small" class="cam-select" @change="onCameraChange">
          <el-option
            v-for="cam in cameraDevices"
            :key="cam.deviceId"
            :label="cam.deviceName || cam.deviceId"
            :value="cam.deviceId"
          />
        </el-select>
        <el-button size="small" plain @click="toggleStream" :type="streamActive ? 'danger' : 'primary'">
          {{ streamActive ? '停止' : '连接' }}
        </el-button>
      </div>

      <!-- 视频画面 -->
      <div class="video-container" :class="{ active: streamActive }">
        <video
          ref="videoEl"
          class="video-player"
          autoplay
          muted
          playsinline
          v-show="streamActive"
        ></video>
        <div class="video-placeholder" v-if="!streamActive">
          <span class="placeholder-icon">📹</span>
          <span class="placeholder-text">选择摄像头并点击"连接"开始查看</span>
        </div>
        <div class="video-placeholder" v-if="streamActive && streamError">
          <span class="placeholder-icon">⚠️</span>
          <span class="placeholder-text">{{ streamError }}</span>
        </div>
      </div>

      <!-- 摄像头信息 -->
      <div class="cam-info" v-if="selectedCamera">
        <div class="info-row">
          <span class="info-label">设备ID:</span>
          <span class="info-value">{{ selectedCamera }}</span>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { Close } from '@element-plus/icons-vue'
import { useDialogStore } from '@/stores/dialog'
import { useIotStore } from '@/stores/iot'
import { useDraggablePanel } from '@/composables/useDraggablePanel'

const dialogStore = useDialogStore()
const iotStore = useIotStore()
const { panelRef, panelStyle, dragging, startDrag, resetPosition, bringToFront } = useDraggablePanel({
  storageKey: 'scene-design:panel:camera',
  initialTop: 60,
  initialRight: 720,
  width: 400,
  zIndex: 740
})

const videoEl = ref<HTMLVideoElement | null>(null)
const selectedCamera = ref<string | null>(null)
const streamActive = ref(false)
const streamError = ref('')
let mediaStream: MediaStream | null = null

const cameraDevices = computed(() =>
  iotStore.devices.filter(d => d.deviceType === 'camera')
)

function onCameraChange(deviceId: string) {
  if (streamActive.value) {
    stopStream()
  }
  selectedCamera.value = deviceId
}

async function toggleStream() {
  if (streamActive.value) {
    stopStream()
    return
  }
  if (!selectedCamera.value) return

  try {
    streamError.value = ''

    // Try to use the camera stream URL if configured
    const cam = iotStore.devices.find(d => d.deviceId === selectedCamera.value)
    const streamUrl = cam?.config?.streamUrl as string | undefined

    if (streamUrl) {
      // RTSP/HLS stream — use video element src
      if (videoEl.value) {
        videoEl.value.src = streamUrl
        await videoEl.value.play()
      }
    } else {
      // Fallback: try browser camera for demo
      mediaStream = await navigator.mediaDevices.getUserMedia({ video: true })
      if (videoEl.value) {
        videoEl.value.srcObject = mediaStream
      }
    }

    streamActive.value = true
  } catch (e: any) {
    streamError.value = e.message || '无法连接视频流'
    streamActive.value = false
  }
}

function stopStream() {
  if (mediaStream) {
    mediaStream.getTracks().forEach(t => t.stop())
    mediaStream = null
  }
  if (videoEl.value) {
    videoEl.value.srcObject = null
    videoEl.value.src = ''
  }
  streamActive.value = false
  streamError.value = ''
}

function closeCamera() {
  stopStream()
  dialogStore.showCameraPanel(false)
}

onUnmounted(() => {
  stopStream()
})
</script>

<style scoped>
.camera-panel {
  position: fixed;
  width: 400px;
  background: rgba(7, 11, 24, 0.92);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 12px;
  padding: 0;
  color: #e8ecf1;
}

.camera-panel.dragging {
  cursor: grabbing;
  opacity: 0.96;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  cursor: grab;
  touch-action: none;
  user-select: none;
}

.camera-panel.dragging .panel-head {
  cursor: grabbing;
}

.panel-head-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
}

.panel-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.panel-dot.live {
  background: #22dd66;
  box-shadow: 0 0 6px #22dd66;
}

.cam-selector {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
}

.cam-select {
  flex: 1;
}

.video-container {
  margin: 0 16px;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  aspect-ratio: 16 / 9;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.video-container.active {
  border-color: rgba(0, 212, 255, 0.2);
}

.video-player {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #556;
  padding: 20px;
}

.placeholder-icon {
  font-size: 32px;
}

.placeholder-text {
  font-size: 12px;
  text-align: center;
}

.cam-info {
  padding: 12px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}

.info-row {
  display: flex;
  gap: 8px;
  font-size: 12px;
}

.info-label {
  color: #667;
}

.info-value {
  color: #aab;
  font-family: monospace;
}

.stream-status {
  font-size: 11px;
}
</style>
