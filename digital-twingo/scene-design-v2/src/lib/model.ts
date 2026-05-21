/**
 *   三维数字孪生设计平台
 *
 *    模型类，加载模型 (gltf格式), 自动模型适配大小、位置
 *
 *  @author Sparcle
 *  @version 2.0
 **/

import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { uuid } from './utils'
import axios from 'axios'
import { useModelStore } from '@/stores/model'
import _ from 'lodash'

const gltfLoader = new GLTFLoader()

type stringKeyData = Record<string, any>

const cropModelFiles = new Set([
  'Apple_Crop.glb',
  'Beet_Crop.glb',
  'Carrot_Crop.glb',
  'Corn_Crop.glb',
  'Lettuce_Crop.glb',
  'Pumpkin_Crop.glb',
  'Rice_Crop.glb',
  'Tomato_Crop.glb',
  'Wheat_Crop.glb'
])

export class Model {
  public rootObject = new THREE.Group()
  private options = {} as any
  private modelId: string
  private url: string
  private ani: any
  private materials = [] as any[]
  private data = {} as stringKeyData

  constructor() {
    this.modelId = uuid()
    this.url = ''
  }

  public loadModel(url: string, options: any, onProgress?: (pct: number) => void): Promise<Model> {
    this.url = url
    this.options = _.cloneDeep(options)
    if (!this.options.sceneObjectId) {
      this.options.sceneObjectId = uuid()
    }
    if (url.endsWith('.gltf') || url.endsWith('.glb')) {
      return new Promise((resolve, reject) => {
        this.loadGltfModel(url, onProgress).then((modelObj: any) => {
          this.setModel(modelObj, this.options)
          resolve(this)
        }).catch(reject)
      })
    }
    return Promise.reject(new Error(`Unsupported model format: ${url}`))
  }

  public get getData() {
    return this.data
  }

  public get getOptions() {
    return this.options
  }

  public get name(): string {
    const metaName = this.options.meta?.label || this.options.label || this.options.name
    if (metaName) {
      return metaName
    }
    if (this.data.name) {
      return this.data.name
    }
    const fileName = this.url.split('/').pop()
    if (fileName) {
      return fileName.replace(/\.(glb|gltf)$/i, '')
    }
    return this.options.dataId ? `数据#${this.options.dataId}` : '未命名模型'
  }

  public get animator() {
    return this.ani
  }

  public get getModelId(): string {
    return this.modelId
  }

  public get getSceneObjectId(): string {
    if (!this.options.sceneObjectId) {
      this.options.sceneObjectId = uuid()
    }
    return this.options.sceneObjectId
  }

  public get getBusinessObjectId(): string {
    return this.options.businessObjectId || ''
  }

  public get getAssetKey(): string {
    return this.options.assetKey || this.options.meta?.assetKey || guessAssetKeyFromUrl(this.url)
  }

  public setBusinessBinding(binding: { businessObjectId?: string; assetKey?: string; isDefaultBinding?: boolean }) {
    const nextBusinessObjectId = binding.businessObjectId || ''
    const nextAssetKey = binding.assetKey || this.getAssetKey
    const nextIsDefaultBinding = Boolean(binding.isDefaultBinding)
    if (
      this.options.businessObjectId === nextBusinessObjectId &&
      this.options.assetKey === nextAssetKey &&
      Boolean(this.options.isDefaultBinding) === nextIsDefaultBinding
    ) {
      return
    }
    this.options.businessObjectId = nextBusinessObjectId
    this.options.assetKey = nextAssetKey
    this.options.isDefaultBinding = nextIsDefaultBinding
    useModelStore().updateActiveModel(this)
  }

  public select() {
    this.materials.forEach((item) => {
      item.mat.color.set(0xff0000)
    })
  }

  public deselect() {
    this.materials.forEach((item) => {
      item.mat.color.set(item.color)
    })
  }

  public setDataId(dataId: string) {
    this.options.dataId = dataId
    this.data[dataId] = dataId
    axios.get('/datasvr/getData', { params: { dataId: dataId } }).then((res) => {
      this.setData(res.data.data)
      const modelStore = useModelStore()
      if (modelStore.activeModelId === this.modelId) {
        modelStore.updateActiveModel(this)
      }
    })
  }

  public setData(data: any) {
    for (const key in data) {
      this.data[key] = data[key]
    }
  }

  public setProp(options: any) {
    if (options.scale && (options.scale !== this.options.scale)) {
      this.options.scale = options.scale
      this.rootObject.scale.set(options.scale, options.scale, options.scale)
    }

    const same = (options.offset.x === this.options.offset.x) &&
                 (options.offset.y === this.options.offset.y) &&
                 (options.offset.z === this.options.offset.z)
    if (options.offset && (!same)) {
      this.options.offset = { x: options.offset.x, y: options.offset.y, z: options.offset.z }
      this.rootObject.position.set(options.offset.x, options.offset.y, options.offset.z)
    }

    if (options.angle && (options.angle !== this.options.angle)) {
      this.options.angle = options.angle
      this.rootObject.rotation.y = options.angle * Math.PI / 180.0
    }
  }

  public syncPositionOptions() {
    this.options.offset.x = this.rootObject.position.x
    this.options.offset.y = this.rootObject.position.y
    this.options.offset.z = this.rootObject.position.z
    useModelStore().updateActiveModel(this)
  }

  public saveModel() {
    return { url: this.url, options: _.cloneDeep(this.options) }
  }

  public setEnvMap(envMap: any) {
    this.materials.forEach((item) => {
      item.envMap = envMap
      item.envMapIntensity = 10
      item.needsUpdate = true
    })
  }

  private setModel(modelObj: any, options: any) {
    if (Number.isFinite(options.semanticScale) && options.semanticScale > 0) {
      this.options.scale = modelObj.fitScale * options.semanticScale
      delete this.options.semanticScale
    } else {
      this.options.scale = options.scale || modelObj.fitScale
    }
    this.options.offset = options.offset || modelObj.fitOffset
    this.options.angle = options.angle || '0'

    this.rootObject.add(modelObj.obj)
    this.rootObject.userData.type = 'targetObj'
    this.rootObject.userData.modelId = this.modelId
    this.rootObject.userData.sceneObjectId = this.getSceneObjectId
    this.setObjctCastShadow(this.rootObject)

    const obj = this.rootObject
    obj.scale.set(this.options.scale, this.options.scale, this.options.scale)
    obj.position.set(this.options.offset.x, this.options.offset.y, this.options.offset.z)
    obj.rotation.y = this.options.angle * Math.PI / 180.0

    if (modelObj.ani) {
      this.ani = modelObj.ani
    }

    if (options.dataId && options.dataId !== '0') {
      this.setDataId(options.dataId)
    }
  }

  private setObjctCastShadow(obj: any) {
    obj.children.forEach((childObj: any) => {
      if (childObj.material) {
        this.materials.push({ mat: childObj.material, color: childObj.material.color.getHex() })
      }
      this.setObjctCastShadow(childObj)
    })
    obj.castShadow = true
  }

  private async loadGltfModel(url: string, onProgress?: (pct: number) => void) {
    const candidates = getModelUrlCandidates(url)
    const errors = [] as string[]
    for (const candidate of candidates) {
      try {
        return await this.loadGltfModelUrl(candidate, onProgress)
      } catch (err: any) {
        errors.push(`${candidate}: ${err?.message || err || 'load failed'}`)
      }
    }
    throw new Error(`模型加载失败：${url}；已尝试 ${errors.join(' | ')}`)
  }

  private loadGltfModelUrl(url: string, onProgress?: (pct: number) => void) {
    return new Promise((resolve, reject) => {
      const loader = new GLTFLoader()
      const loadingManager = new THREE.LoadingManager()
      loadingManager.onProgress = (_url, loaded, total) => {
        if (onProgress && total > 0) {
          onProgress(Math.round((loaded / total) * 100))
        }
      }
      loader.manager = loadingManager

      loader.load(url, (gltf: any) => {
        const model = {} as any
        model.obj = gltf.scene
        if (gltf.animations.length > 0) {
          const aniMixer = new THREE.AnimationMixer(gltf.scene)
          const clip = gltf.animations[0]
          aniMixer.clipAction(clip).setDuration(clip.duration).play()
          model.ani = aniMixer
        }

        const box3 = new THREE.Box3()
        box3.expandByObject(model.obj)
        const size = new THREE.Vector3()
        box3.getSize(size)
        const scaleX = size.x > 0 ? 200 / size.x : 1
        const scaleZ = size.z > 0 ? 100 / size.z : 1
        model.fitScale = scaleX > scaleZ ? scaleZ : scaleX
        if (!isFinite(model.fitScale) || model.fitScale <= 0) model.fitScale = 1
        model.fitScale = Math.floor(model.fitScale * 100) / 100

        const center = new THREE.Vector3()
        box3.getCenter(center)

        model.fitOffset = new THREE.Vector3()
        model.fitOffset.x = model.obj.position.x - center.x
        model.fitOffset.z = model.obj.position.z - center.z

        resolve(model)
      }, (xhr: any) => {
        if (xhr.lengthComputable && onProgress) {
          onProgress(Math.round((xhr.loaded / xhr.total) * 100))
        }
      }, (err: any) => {
        reject(err)
      })
    })
  }
}

function guessAssetKeyFromUrl(url = '') {
  if (url.includes('Silo_House') || url.includes('greenhouse')) return 'greenhouse'
  if (url.includes('Tomato')) return 'tomato'
  if (url.includes('sensor')) return 'sensor'
  if (url.includes('Well') || url.includes('irrigation')) return 'irrigation'
  if (url.includes('camera')) return 'camera'
  if (url.includes('TowerWindmill')) return 'weather_station'
  return ''
}

function getModelUrlCandidates(url: string) {
  const candidates = [url]
  if (url.startsWith('/scene-assets/')) {
    candidates.push(...sceneAssetUrlCandidates(url))
  }
  const publicFallback = publicModelFallback(url)
  if (publicFallback) {
    candidates.push(publicFallback)
  }
  return uniqueStrings(candidates)
}

function sceneAssetUrlCandidates(url: string) {
  const candidates = [] as string[]
  const assetBase = (import.meta.env.VITE_SCENE_ASSET_BASEURL as string | undefined)?.trim()
  if (assetBase) {
    candidates.push(joinBaseUrl(assetBase, url))
  }

  const apiBase = ((import.meta.env.VITE_BASEURL as string | undefined) || '').trim()
  const apiOrigin = absoluteOrigin(apiBase)
  if (apiOrigin) {
    candidates.push(joinBaseUrl(apiOrigin, url))
  }

  if (import.meta.env.DEV && typeof window !== 'undefined' && window.location.port !== '9010') {
    candidates.push(`${window.location.protocol}//${window.location.hostname}:9010${url}`)
  }
  return candidates
}

function publicModelFallback(url: string) {
  const fileName = modelFileName(url)
  if (!cropModelFiles.has(fileName)) {
    return ''
  }
  return `${import.meta.env.BASE_URL}models/crops/${fileName}`
}

function modelFileName(url: string) {
  const cleanUrl = url.split(/[?#]/)[0].replace(/\\/g, '/')
  return cleanUrl.split('/').pop() || ''
}

function absoluteOrigin(url: string) {
  if (!/^https?:\/\//i.test(url)) {
    return ''
  }
  try {
    return new URL(url).origin
  } catch {
    return ''
  }
}

function joinBaseUrl(base: string, path: string) {
  return `${base.replace(/\/$/, '')}/${path.replace(/^\//, '')}`
}

function uniqueStrings(items: string[]) {
  return Array.from(new Set(items.filter(Boolean)))
}
