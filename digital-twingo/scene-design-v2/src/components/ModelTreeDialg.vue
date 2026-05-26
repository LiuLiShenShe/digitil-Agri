<!--
 *   三维数字孪生设计平台
 *    模型树选择对话框 + AI生成入口
 *
 *  @author Sparcle
 *  @version 2.2
-->

<template>
  <el-dialog v-model="dlgShow" width="960px" @opened="onOpened" @close="onClose" class="model-dialog">
    <template #header>
      <el-tabs v-model="activeTab" class="dialog-tabs">
        <el-tab-pane label="模型库" name="library" />
        <el-tab-pane label="AI 生成" name="ai" />
      </el-tabs>
    </template>

    <!-- ========== 模型库 ========== -->
    <div v-show="activeTab === 'library'" class="library-panel">
      <div class="library-sidebar">
        <div class="sidebar-header">模型分类</div>
        <div v-if="modelTreeLoading" class="tree-state">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>加载模型库...</span>
        </div>
        <div v-else-if="modelTreeError" class="tree-state error">
          <span>{{ modelTreeError }}</span>
          <el-button size="small" plain @click="loadModelTree">重试</el-button>
        </div>
        <div v-else-if="treeData.length === 0" class="tree-state">
          <el-icon><FolderOpened /></el-icon>
          <span>暂无模型数据</span>
        </div>
        <el-tree
          v-else
          :data="treeData"
          node-key="id"
          :expand-on-click-node="false"
          highlight-current
          :props="{ label: 'label', children: 'children' }"
          @node-click="onSelectChange"
          class="model-tree"
        />
      </div>
      <div class="library-preview">
        <div ref="modelView" class="preview-canvas"></div>
        <!-- 加载进度条 -->
        <div v-if="libraryLoading" class="loading-overlay">
          <div class="loading-card">
            <el-icon class="loading-icon is-loading" size="28"><Loading /></el-icon>
            <span class="loading-text">模型加载中...</span>
            <el-progress
              :percentage="libraryProgress"
              :stroke-width="6"
              :show-text="true"
              class="loading-bar"
            />
            <span class="loading-hint">首次加载较大模型可能需要几秒钟</span>
          </div>
        </div>
        <!-- 空状态提示 -->
        <div v-if="!libraryLoading && !curUrl" class="empty-hint">
          <el-icon size="40"><FolderOpened /></el-icon>
          <p>请在左侧选择模型预览</p>
        </div>
      </div>
    </div>

    <!-- ========== AI 生成 ========== -->
    <div v-show="activeTab === 'ai'" class="ai-panel">
      <div class="ai-sidebar">
        <el-upload
          :auto-upload="false"
          :show-file-list="false"
          :on-change="onImageSelected"
          accept="image/png,image/jpeg"
          drag
          class="ai-upload"
        >
          <div v-if="!uploadImage" class="upload-placeholder">
            <el-icon style="font-size:32px;color:#999"><UploadFilled /></el-icon>
            <p>拖拽或点击上传图片</p>
          </div>
          <img v-else :src="uploadImage" class="upload-preview" />
        </el-upload>

        <div class="ai-config">
          <label class="config-label">生成精度</label>
          <el-select v-model="genResolution" style="width:100%" size="small">
            <el-option label="快速 512 — 约2-3分钟" :value="512" />
            <el-option label="精细 1024 — ~2分钟" :value="1024" />
          </el-select>
        </div>

        <el-button type="primary" :disabled="!uploadImage || genBusy" :loading="genBusy" @click="startGenerate" style="width:100%">
          {{ genBusy ? '提交中...' : '开始生成 3D 模型' }}
        </el-button>

        <el-divider style="margin:4px 0">任务列表</el-divider>

        <div class="job-list">
          <div v-if="recentJobs.length === 0" class="job-empty">暂无生成任务</div>
          <div v-for="job in recentJobs" :key="job.jobId"
            :class="['job-item', job.status]"
            @click="onClickJob(job)"
          >
            <div class="job-row">
              <img v-if="job.thumbUrl" :src="job.thumbUrl" class="job-thumb" />
              <div v-else class="job-thumb-placeholder">
                <el-icon size="18"><Picture /></el-icon>
              </div>
              <div class="job-info">
                <div class="job-status">{{ jobStatusText(job) }}</div>
                <el-progress v-if="job.status === 'queued' || job.status === 'running'"
                  :percentage="job.progress" :stroke-width="4" style="margin-top:2px" />
                <div v-if="isReusableJob(job)" class="job-ok">可预览和添加</div>
                <div v-if="job.status === 'failed'" class="job-err">{{ job.errorMsg }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- AI 预览 -->
      <div class="ai-preview">
        <div ref="aiPreview" class="preview-canvas"></div>
        <div v-if="aiLoading" class="loading-overlay">
          <div class="loading-card">
            <el-icon class="loading-icon is-loading" size="28"><Loading /></el-icon>
            <span class="loading-text">模型加载中...</span>
            <el-progress :percentage="aiProgress" :stroke-width="6" class="loading-bar" />
          </div>
        </div>
        <div v-if="!aiLoading && !selectedJob" class="empty-hint">
          <el-icon size="48"><Picture /></el-icon>
          <p>选择已完成的任务预览模型</p>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="onCancel">取消</el-button>
      <el-button v-if="activeTab === 'library'" type="primary" @click="onOk" :disabled="!curUrl">确定</el-button>
      <el-button v-if="activeTab === 'ai'" type="primary" :disabled="!aiSelectedUrl" @click="onAiOk">添加生成的模型</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { Scene } from '@/lib/scene'
import { useDialogStore } from '@/stores/dialog'
import { useGlobals } from '@/composables/useGlobals'
import { UploadFilled, Picture, Loading, FolderOpened } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const { $http } = useGlobals()
const dialogStore = useDialogStore()

const dlgShow = computed({
  get: () => dialogStore.modelTreeDialog,
  set: (val) => dialogStore.showModelTree(val)
})

// ----- tabs -----
const activeTab = ref('library')
watch(activeTab, (tab) => {
  if (tab === 'ai') {
    nextTick(() => initAiPreview())
  }
})

// ----- model library -----
const modelView = ref<HTMLElement>()
const treeData = ref<any[]>([])
const modelTreeLoading = ref(false)
const modelTreeError = ref('')

interface TreeNode {
  label: string
  id: number
  pid: number
  url: string | null
  leaf: boolean
  children?: TreeNode[]
}

let previewScene: any = null
const curUrl = ref('')
let aiPreviewScene: any = null

// loading state
const libraryLoading = ref(false)
const libraryProgress = ref(0)
const aiLoading = ref(false)
const aiProgress = ref(0)
let modelTreeRequestId = 0

function requestTimeout(ms: number) {
  return new Promise<never>((_, reject) => {
    window.setTimeout(() => reject(new Error('模型库请求超时')), ms)
  })
}

async function loadModelTree() {
  const requestId = ++modelTreeRequestId
  modelTreeLoading.value = true
  modelTreeError.value = ''
  try {
    let list = await fetchModelList(true)
    if (list.length === 0) {
      list = await fetchModelList(false)
    }
    if (requestId !== modelTreeRequestId) return
    treeData.value = buildTreeData(list)
    if (treeData.value.length === 0) {
      modelTreeError.value = '模型库为空，请检查模型数据是否已导入'
    }
  } catch {
    try {
      const list = await fetchModelList(false)
      if (requestId !== modelTreeRequestId) return
      treeData.value = buildTreeData(list)
      if (treeData.value.length === 0) {
        modelTreeError.value = '模型库为空，请检查模型数据是否已导入'
      }
    } catch {
      if (requestId !== modelTreeRequestId) return
      treeData.value = []
      modelTreeError.value = '模型库加载失败，请检查后端服务'
    }
  } finally {
    if (requestId === modelTreeRequestId) {
      modelTreeLoading.value = false
    }
  }
}

async function fetchModelList(includeAi: boolean): Promise<any[]> {
  const params: any = {}
  if (includeAi) {
    const key = getOwnerKey()
    if (key) params.ownerKey = key
  }
  const res = await Promise.race([
    $http.get('/model/list', { params }),
    requestTimeout(8000)
  ])
  if (res.data.code !== 200 || !Array.isArray(res.data.data)) {
    throw new Error(res.data.data || '模型库加载失败')
  }
  return res.data.data
}

function buildTreeData(list: any[]): TreeNode[] {
  const nodes: TreeNode[] = list.map((n: any) => ({
    label: n.name || n.label || '',
    id: Number(n.id),
    pid: Number(n.parentid ?? n.parentId ?? n.pid ?? 0),
    url: n.url ?? n.modelUrl ?? null,
    leaf: Boolean(n.leaf)
  })).filter(n => Number.isFinite(n.id) && n.label)
  const map = new Map<number, TreeNode>()
  nodes.forEach(n => map.set(n.id, n))
  const roots: TreeNode[] = []
  nodes.forEach(n => {
    if (map.has(n.pid)) {
      const parent = map.get(n.pid)!
      if (!parent.children) parent.children = []
      parent.children.push(n)
    } else {
      roots.push(n)
    }
  })
  return roots
}

function onOpened() {
  nextTick(() => {
    loadModelTree()
    loadRecentJobs()
    initLibraryPreview()
    initAiPreview()
  })
}

function initLibraryPreview() {
  const el = modelView.value
  if (!el || el.clientWidth === 0) return
  if (previewScene) previewScene.removeAllModels()
  previewScene = Scene.initExtInstance(el)
  previewScene.clear()
  previewScene.setAmbientLight({ color: '#ffffff', intensity: 0.5 })
  previewScene.setDirectionalLight({ color: '#ffffff', intensity: 1.2, pos: { x: 50, y: 200, z: 100 } })
  previewScene.enableRoomEnvironment()
  previewScene.setCameraPosition({ x: 0, y: 50, z: 80 })
}

function initAiPreview() {
  if (aiPreviewScene) return
  const el = aiPreview.value
  if (!el || el.clientWidth === 0) return
  aiPreviewScene = Scene.initExtInstance(el)
  aiPreviewScene.clear()
  aiPreviewScene.setAmbientLight({ color: '#ffffff', intensity: 0.5 })
  aiPreviewScene.setDirectionalLight({ color: '#ffffff', intensity: 1.2, pos: { x: 50, y: 200, z: 100 } })
  aiPreviewScene.enableRoomEnvironment()
  aiPreviewScene.setCameraPosition({ x: 0, y: 50, z: 80 })
  if (selectedJob.value?.status === 'completed' && selectedJob.value.modelUrl) {
    aiLoading.value = true
    aiProgress.value = 0
    aiPreviewScene.loadModel(selectedJob.value.modelUrl, {}, (pct: number) => {
      aiProgress.value = pct
    }).then(() => {
      aiLoading.value = false
    }).catch(() => {
      aiLoading.value = false
    })
    aiSelectedUrl.value = selectedJob.value.modelUrl
  }
}

function onClose() {
  if (previewScene) {
    Scene.disposeExtInstance(previewScene)
    previewScene = null
  }
  if (aiPreviewScene) {
    Scene.disposeExtInstance(aiPreviewScene)
    aiPreviewScene = null
  }
  curUrl.value = ''
  aiSelectedUrl.value = ''
  libraryLoading.value = false
  libraryProgress.value = 0
  aiLoading.value = false
  aiProgress.value = 0
}

function ensureLibraryPreview(): boolean {
  const el = modelView.value
  if (!el || el.clientWidth === 0) return false
  if (!previewScene) {
    initLibraryPreview()
  }
  return !!previewScene
}

function onSelectChange(node: any) {
  if (!node.leaf || !node.url) return
  if (curUrl.value === node.url) return
  curUrl.value = node.url

  if (!ensureLibraryPreview()) return

  libraryLoading.value = true
  libraryProgress.value = 0
  previewScene.removeAllModels()
  previewScene.loadModel(node.url, {}, (pct: number) => {
    libraryProgress.value = pct
  }).then(() => {
    libraryLoading.value = false
  }).catch(() => {
    libraryLoading.value = false
    ElMessage.warning('模型加载失败，请检查模型文件')
  })
}

function onOk() {
  if (curUrl.value && previewScene) {
    Scene.getInstance().loadModel(curUrl.value, {})
    dialogStore.showModelTree(false)
  }
}

function onCancel() {
  dialogStore.showModelTree(false)
}

// ----- AI generation -----
const aiPreview = ref<HTMLElement>()
const uploadImage = ref('')
const uploadFile = ref<File | null>(null)
const genResolution = ref(512)
const genBusy = ref(false)
const recentJobs = ref<any[]>([])
const selectedJob = ref<any>(null)
const aiSelectedUrl = ref('')
let pollTimer: any = null

function onImageSelected(file: any) {
  const raw = file.raw as File
  if (!raw) return
  uploadFile.value = raw
  const reader = new FileReader()
  reader.onload = (e) => { uploadImage.value = e.target?.result as string }
  reader.readAsDataURL(raw)
}

function jobStatusText(job: any) {
  const map: Record<string, string> = { queued: '排队中', running: '生成中...', completed: '已完成', approved: '已入库', failed: '失败' }
  return map[job.status] || job.status
}

function isReusableJob(job: any): boolean {
  return (job.status === 'completed' || job.status === 'approved') && !!job.modelUrl
}

async function startGenerate() {
  if (!uploadFile.value) { ElMessage.warning('请先选择图片'); return }
  genBusy.value = true
  try {
    const base64 = await fileToBase64(uploadFile.value)
    const resp = await $http.post('/asset/jobs', {
      imageBase64: base64,
      imageFileName: uploadFile.value.name,
      ownerKey: getOwnerKey(),
      resolution: genResolution.value,
      decimationTarget: 300000,
      textureSize: 2048,
    })
    if (resp.data.code === 200) {
      ElMessage.success('任务已提交，请等待生成完成')
      recentJobs.value.unshift(resp.data.data)
      startPolling()
    } else {
      ElMessage.error(resp.data.data || '提交失败')
    }
  } catch (e: any) {
    ElMessage.error('服务异常: ' + (e.message || ''))
  }
  genBusy.value = false
}

function onClickJob(job: any) {
  selectedJob.value = job
  if (isReusableJob(job)) {
    aiSelectedUrl.value = job.modelUrl
    nextTick(() => {
      if (!aiPreviewScene) initAiPreview()
      if (aiPreviewScene) {
        aiLoading.value = true
        aiProgress.value = 0
        aiPreviewScene.removeAllModels()
        aiPreviewScene.loadModel(job.modelUrl, {}, (pct: number) => {
          aiProgress.value = pct
        }).then(() => {
          aiLoading.value = false
        }).catch(() => {
          aiLoading.value = false
        })
      }
    })
  } else if (!isReusableJob(job)) {
    aiSelectedUrl.value = ''
  }
}

async function pollJob(jobId: string) {
  try {
    const resp = await $http.get(`/asset/jobs/${jobId}`)
    if (resp.data.code === 200) {
      const updated = resp.data.data
      const idx = recentJobs.value.findIndex(j => j.jobId === jobId)
      if (idx >= 0) recentJobs.value[idx] = updated
      if (isReusableJob(updated)) {
        aiSelectedUrl.value = updated.modelUrl
        if (selectedJob.value?.jobId === jobId && aiPreviewScene) {
          aiLoading.value = true
          aiProgress.value = 0
          aiPreviewScene.removeAllModels()
          aiPreviewScene.loadModel(updated.modelUrl, {}, (pct: number) => {
            aiProgress.value = pct
          }).then(() => {
            aiLoading.value = false
          }).catch(() => {
            aiLoading.value = false
          })
        }
      }
      if (updated.status === 'completed' || updated.status === 'approved' || updated.status === 'failed') return true
    }
  } catch (e) { /* ignore */ }
  return false
}

function startPolling() {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(async () => {
    let allDone = true
    for (const job of recentJobs.value) {
      if (job.status === 'queued' || job.status === 'running') {
        allDone = false
        await pollJob(job.jobId)
      }
    }
    if (allDone) { clearInterval(pollTimer); pollTimer = null }
  }, 3000)
}

function onAiOk() {
  if (aiSelectedUrl.value && Scene.getInstance()) {
    Scene.getInstance().loadModel(aiSelectedUrl.value, {})
    dialogStore.showModelTree(false)
  }
}

function getOwnerKey(): string {
  let key = localStorage.getItem('ownerKey')
  if (!key) {
    key = 'user_' + Math.random().toString(36).slice(2, 10)
    localStorage.setItem('ownerKey', key)
  }
  return key
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      resolve(result.split(',')[1] || result)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

onMounted(() => {
  loadRecentJobs()
})

async function loadRecentJobs() {
  try {
    const resp = await $http.get('/asset/jobs', { params: { ownerKey: getOwnerKey() } })
    if (resp.data.code === 200) {
      recentJobs.value = resp.data.data || []
      if (recentJobs.value.some((j: any) => j.status === 'queued' || j.status === 'running')) {
        startPolling()
      }
    }
  } catch (e) { /* ignore */ }
}
</script>

<style scoped>
.dialog-tabs {
  margin: -30px 0 -10px 0;
}
.dialog-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
}

/* panels */
.library-panel, .ai-panel {
  display: flex;
  height: 480px;
  gap: 0;
}

.library-sidebar, .ai-sidebar {
  width: 260px;
  overflow-y: auto;
  border-right: 1px solid #e4e7ed;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.library-preview, .ai-preview {
  flex: 1;
  overflow: hidden;
  background: #0f0f1a;
  position: relative;
  border-radius: 0 4px 4px 0;
}

.preview-canvas {
  width: 100%;
  height: 100%;
}

/* sidebar */
.sidebar-header {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  padding: 6px 8px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 4px;
}

.model-tree {
  font-size: 13px;
}

.tree-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 180px;
  padding: 16px;
  color: #909399;
  font-size: 12px;
  text-align: center;
}

.tree-state.error {
  color: #f56c6c;
}

.model-tree :deep(.el-tree-node__content) {
  height: 32px;
}

.model-tree :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background-color: #ecf5ff;
  color: #409eff;
}

/* loading overlay */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 15, 26, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.loading-card {
  text-align: center;
  color: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 24px 32px;
  background: rgba(255,255,255,0.06);
  border-radius: 12px;
  backdrop-filter: blur(8px);
  min-width: 220px;
}

.loading-icon {
  color: #409eff;
}

.loading-text {
  font-size: 14px;
  font-weight: 500;
}

.loading-bar {
  width: 180px;
}

.loading-hint {
  font-size: 11px;
  color: #909399;
}

/* empty hint */
.empty-hint {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #909399;
}

.empty-hint p {
  margin-top: 8px;
  font-size: 13px;
}

/* AI panel */
.ai-upload {
  width: 100%;
}

.upload-placeholder {
  padding: 16px;
}

.upload-preview {
  max-width: 100%;
  max-height: 100px;
  object-fit: contain;
}

.ai-config {
  margin-top: 4px;
}

.config-label {
  font-size: 12px;
  color: #666;
  display: block;
  margin-bottom: 4px;
}

/* job list */
.job-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.job-empty {
  color: #999;
  text-align: center;
  padding: 16px;
  font-size: 12px;
}

.job-item {
  padding: 6px 8px;
  margin-bottom: 6px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.job-item:hover { border-color: #409EFF; box-shadow: 0 2px 8px rgba(64,158,255,0.12); }
.job-item.completed, .job-item.approved { border-left: 3px solid #67C23A; }
.job-item.failed { border-left: 3px solid #F56C6C; }
.job-item.queued, .job-item.running { border-left: 3px solid #E6A23C; }

.job-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.job-thumb {
  width: 36px;
  height: 36px;
  object-fit: cover;
  border-radius: 4px;
  flex-shrink: 0;
}

.job-thumb-placeholder {
  width: 36px;
  height: 36px;
  background: #f0f0f0;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.job-info {
  flex: 1;
  min-width: 0;
}

.job-status {
  font-size: 12px;
  font-weight: 600;
}

.job-ok {
  font-size: 10px;
  color: #67C23A;
}

.job-err {
  font-size: 10px;
  color: #F56C6C;
}
</style>
