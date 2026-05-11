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

  public loadModel(url: string, options: any, onProgress?: (pct: number) => void): any {
    this.url = url
    this.options = _.cloneDeep(options)
    if (url.endsWith('.gltf') || url.endsWith('.glb')) {
      return new Promise((resolve) => {
        this.loadGltfModel(url, onProgress).then((modelObj: any) => {
          this.setModel(modelObj, this.options)
          resolve(this)
        })
      })
    }
  }

  public get getData() {
    return this.data
  }

  public get getOptions() {
    return this.options
  }

  public get name(): string {
    if (!this.options.dataId) {
      return '未关联数据'
    }
    return this.data.name
  }

  public get animator() {
    return this.ani
  }

  public get getModelId(): string {
    return this.modelId
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
    this.options.scale = options.scale || modelObj.fitScale
    this.options.offset = options.offset || modelObj.fitOffset
    this.options.angle = options.angle || '0'

    this.rootObject.add(modelObj.obj)
    this.rootObject.userData.type = 'targetObj'
    this.rootObject.userData.modelId = this.modelId
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

  private loadGltfModel(url: string, onProgress?: (pct: number) => void) {
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
        console.error('Model load error:', url, err)
        reject(err)
      })
    })
  }
}
