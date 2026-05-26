/**
 *   三维数字孪生设计平台
 *
 *    场景类，初始化 WebGL环境，设置相机、背景、灯光、地面
 *    Phase 2: 增加地形、图层、框选、吸附、模板、纹理刷
 *
 *  @author Sparcle
 *  @version 2.1
 **/

import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js'
import axios from 'axios'

import { useSceneStore } from '@/stores/scene'
import { useModelStore } from '@/stores/model'
import { useLayerStore } from '@/stores/layer'
import { Model } from '@/lib/model'
import { DragControl } from '@/lib/dragcontrol'
import { TerrainImporter, type TerrainOptions } from '@/lib/terrain'
import { LayerManager } from '@/lib/layerManager'
import { BoxSelector } from '@/lib/boxSelector'
import { TerrainBrush } from '@/lib/terrainBrush'
import { sceneTemplates, type SceneTemplate } from '@/data/templates'

interface TomatoGreenhouseVisualTemplate {
  templateKey: string
  greenhouse: {
    center: { x: number; y: number; z: number }
    width: number
    depth: number
    height: number
  }
  plantGrid: {
    rows: number
    columns: number
    spacingX: number
    spacingZ: number
    bedCount: number
    insideOnly: boolean
  }
  irrigation: {
    bedCount: number
    dripLineCount: number
    mainPipeLength: number
    pumpPosition: { x: number; y: number; z: number }
    valvePositions?: Array<{ x: number; y: number; z: number }>
  }
  lighting: {
    skyColor: string
    groundColor: string
    ambientIntensity: number
    directionalIntensity: number
    minimumScreenshotLuma: number
  }
  acceptance: {
    expectedTomatoesInsideGreenhouse: number
    minimumScreenshotLuma: number
    maximumTomatoScale: number
    requiresContinuousIrrigation: boolean
  }
}

interface TomatoGreenhouseSnapshot {
  templateKey: string
  greenhouse: {
    center: { x: number; y: number; z: number }
    width: number
    depth: number
    height: number
  }
  tomatoes: Array<{ x: number; y: number; z: number; scale: number }>
  irrigation: {
    bedCount: number
    dripLineCount: number
    mainPipeLength: number
    valveCount: number
  }
  lighting: {
    skyColor: string
    groundColor: string
    ambientIntensity: number
    directionalIntensity: number
    minimumScreenshotLuma: number
  }
}

const viewPositions: Record<string, number[]> = {
  origin: [500, 80, 90],
  top: [0, 500, 0],
  left: [-500, 0, 0],
  right: [500, 0, 0],
  front: [0, 0, 500],
  back: [0, 0, -500]
}

type stringKeyModel = Record<string, any>

/** Snap configuration */
export interface SnapConfig {
  gridSize: number       // tile size for grid snapping
  enabled: boolean
}

export class Scene {
  private init = false
  private width = 0
  private height = 0
  private parent: any

  private scene: any
  private renderer: any
  private camera: any
  private controls: any
  private aniMixers = [] as any[]
  private clock = new THREE.Clock()

  private ambientLight: any
  private directionalLight: any
  private spotLight: any
  private background: any
  private grid: any
  private groundPane: any

  private sceneModels = {} as stringKeyModel
  private sceneArgs = {
    sceneName: '新建场景',
    background: {} as any,
    ambientLight: {} as any,
    directionalLight: {} as any,
    spotLight: {} as any,
    grid: {} as any,
    groundPane: {} as any,
    terrain: {} as any,
    layers: [] as any[]
  }

  private lights = [] as any[]
  private selectObject: Model | null = null
  private selectedModels = new Set<string>()  // multi-select

  private textureLoader = new THREE.TextureLoader()
  private cubeTextureLoader = new THREE.CubeTextureLoader()

  private dragControl: any = null
  private boxSelector: BoxSelector | null = null

  private bgEnv: any = null
  private roomEnv: any = null
  private useRoomEnv = false

  // Phase 2 additions
  private layerManager = new LayerManager()
  private terrainMesh: THREE.Mesh | null = null
  private terrainImporter: TerrainImporter | null = null
  private terrainBrush: TerrainBrush | null = null
  private snapConfig: SnapConfig = { gridSize: 10, enabled: false }
  private snapIndicatorMesh: THREE.Mesh | null = null
  private semanticTemplateLayer: THREE.Group | null = null
  private semanticTemplateSnapshot: TomatoGreenhouseSnapshot | null = null

  private static sceneInstance = new Scene()
  private static extScenes = [] as Scene[]

  private constructor() { }

  public static getInstance(): Scene {
    return Scene.sceneInstance
  }

  public static initInstance(parent: HTMLElement | null) {
    Scene.sceneInstance.initScene(parent)
  }

  public static initExtInstance(parent: HTMLElement): Scene {
    const extScene = new Scene()
    extScene.initScene(parent)
    Scene.extScenes.push(extScene)
    return extScene
  }

  public static disposeExtInstance(scene: Scene) {
    const idx = Scene.extScenes.indexOf(scene)
    if (idx >= 0) Scene.extScenes.splice(idx, 1)
    if (scene.renderer) {
      scene.renderer.dispose()
      if (scene.renderer.domElement && scene.renderer.domElement.parentNode) {
        scene.renderer.domElement.parentNode.removeChild(scene.renderer.domElement)
      }
    }
    scene.init = false
    scene.scene = null
    scene.renderer = null
  }

  // ===== Getters =====

  public get sceneName(): string {
    return this.sceneArgs.sceneName
  }

  public get getLayerManager(): LayerManager {
    return this.layerManager
  }

  public get getSceneModels(): stringKeyModel {
    return this.sceneModels
  }

  public get getSnapConfig(): SnapConfig {
    return this.snapConfig
  }

  public get getSelectedModelIds(): Set<string> {
    return this.selectedModels
  }

  public get getDragControl(): any {
    return this.dragControl
  }

  public get getCamera(): any {
    return this.camera
  }

  public get getScene(): any {
    return this.scene
  }

  public get getTerrainBrush(): TerrainBrush | null {
    return this.terrainBrush
  }

  public get getGroundPane(): any {
    return this.groundPane
  }

  public dispose() {
    this.init = false
    if (this.dragControl) {
      this.dragControl.dispose()
      this.dragControl = null
    }
    if (this.boxSelector) {
      this.boxSelector.dispose()
      this.boxSelector = null
    }
    this.disposeBackgroundTexture()
    if (this.terrainBrush) {
      this.terrainBrush.dispose()
      this.terrainBrush = null
    }
    this.scene = null
  }

  private initScene(parent: HTMLElement | null) {
    if (this.init) {
      console.warn('Scene has been inited, and should only been inited once!')
      return
    }

    if (parent == null) {
      console.warn('Scene must has a parent container elmenet!')
      return
    }

    this.init = true
    this.parent = parent
    this.width = parent.clientWidth
    this.height = parent.clientHeight

    const renderer = new THREE.WebGLRenderer({ antialias: true, logarithmicDepthBuffer: true })
    renderer.setClearColor(new THREE.Color(0x070b18))
    renderer.setSize(this.width, this.height)
    renderer.shadowMap.enabled = true
    parent.appendChild(renderer.domElement)

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(65, this.width / this.height, 0.1, 20000)
    camera.position.set(500, 80, 90)
    camera.lookAt(scene.position)
    const controls = new OrbitControls(camera, renderer.domElement)

    this.scene = scene
    this.renderer = renderer
    this.camera = camera
    this.controls = controls

    Scene.animate()
  }

  public resize(w: number, h: number) {
    this.width = w
    this.height = h
    this.renderer.setSize(w, h)
    this.camera.aspect = this.width / this.height
  }

  public addDragSurport() {
    const dragControl = new DragControl(this.camera, this.renderer.domElement, this.snapConfig, this.scene)
    dragControl.addEventListener('dragstart', () => {
      this.controls.enabled = false
    })
    dragControl.addEventListener('dragend', () => {
      this.controls.enabled = true
      if (this.selectObject) {
        this.selectObject.syncPositionOptions()
      }
    })
    this.dragControl = dragControl

    // Box selector
    this.boxSelector = new BoxSelector(this.scene, this.camera, this.renderer.domElement)
    this.boxSelector.onSelectionComplete = (ids: string[]) => {
      if (ids.length === 0) return
      this.selectedModels.clear()
      ids.forEach(id => {
        this.selectedModels.add(id)
        if (this.sceneModels[id]) {
          this.sceneModels[id].select()
        }
      })
      this.syncMultiSelectToStore()
    }
  }

  // ================== 灯光 ======================
  public setAmbientLight(options: any) {
    const intensity = (options.intensity || (this.ambientLight ? this.ambientLight.intensity : 1.0))
    const color = (options.color || (this.ambientLight ? this.ambientLight.color : '#ffffff'))
    if (this.ambientLight) {
      this.scene.remove(this.ambientLight)
      this.ambientLight.dispose()
      this.ambientLight = undefined
      this.sceneArgs.ambientLight = undefined
    }
    if (options.turnOff) {
      useSceneStore().turnOffLight('ambientLight')
      return
    }

    this.sceneArgs.ambientLight = { color: color, intensity: intensity }
    this.ambientLight = new THREE.AmbientLight(color, intensity)
    this.scene.add(this.ambientLight)
    useSceneStore().setAmbLight({ color: color, intent: intensity, on: true })
  }

  public setDirectionalLight(options: any) {
    const intensity = (options.intensity || (this.directionalLight ? this.directionalLight.intensity : 1.0))
    const color = (options.color || (this.directionalLight ? this.directionalLight.color : '#ffffff'))
    const position = (options.position || (this.directionalLight ? this.directionalLight.position : { x: 20, y: 500, z: 200 }))

    if (this.directionalLight) {
      this.scene.remove(this.directionalLight)
      this.directionalLight.dispose()
      this.directionalLight = undefined
      this.sceneArgs.directionalLight = undefined
    }
    if (options.turnOff) {
      useSceneStore().turnOffLight('directionalLight')
      return
    }

    this.sceneArgs.directionalLight = { color: color, intensity: intensity, pos: position }
    this.directionalLight = new THREE.DirectionalLight(color, intensity)
    this.directionalLight.position.set(position.x, position.y, position.z)
    this.directionalLight.castShadow = true

    this.directionalLight.shadow.mapSize.width = 512
    this.directionalLight.shadow.mapSize.height = 512
    this.directionalLight.shadow.camera.near = 0.5
    this.directionalLight.shadow.camera.far = 800

    this.scene.add(this.directionalLight)
    useSceneStore().setDirLight({ color: color, intent: intensity, on: true })
  }

  public setSpotLight(options: any) {
    const intensity = (options.intensity || (this.spotLight ? this.spotLight.intensity : 1.0))
    const color = (options.color || (this.spotLight ? this.spotLight.color : '#ffffff'))
    let angle = options.angle
    if (angle === undefined) {
      angle = (this.sceneArgs.spotLight ? this.sceneArgs.spotLight.angle : 0)
    }
    const hight = (options.hight || (this.sceneArgs.spotLight ? this.sceneArgs.spotLight.hight : 300))
    const distance = (options.distance || (this.sceneArgs.spotLight ? this.sceneArgs.spotLight.distance : 500))

    if (this.spotLight) {
      this.scene.remove(this.spotLight)
      this.spotLight.dispose()
      this.spotLight = undefined
      this.sceneArgs.spotLight = undefined
    }
    if (options.turnOff) {
      useSceneStore().turnOffLight('spotLight')
      return
    }

    const rad = angle * Math.PI / 180.0
    const position = { x: distance * Math.cos(rad), y: hight, z: distance * Math.sin(rad) }

    this.sceneArgs.spotLight = { color: color, intensity: intensity, angle: angle, hight: hight, distance: distance }
    this.spotLight = new THREE.PointLight(color, intensity)
    this.spotLight.position.set(position.x, position.y, position.z)
    this.spotLight.castShadow = true
    this.scene.add(this.spotLight)
    useSceneStore().setSpotLight({ color: color, intent: intensity, on: true, angle: angle, hight: hight, distance: distance })
  }

  public shutdownLights() {
    this.setAmbientLight({ turnOff: true })
    this.setDirectionalLight({ turnOff: true })
    this.setSpotLight({ turnOff: true })
    for (let i = 0; i < this.lights.length; i++) {
      this.scene.remove(this.lights[i])
    }
    this.lights = []
  }

  public lightOn(): boolean {
    return (this.lights.length > 0 || !!(this.directionalLight || this.ambientLight || this.spotLight))
  }

  // ==================== 背景 =====================
  public setBackground(options: any) {
    this.disposeBackgroundTexture()
    if (options.turnOff) {
      if (!this.useRoomEnv) {
        this.scene.environment = null
      }
      useSceneStore().turnOffBackground('skybox')
      return
    }

    const texturePath = options.texturePath || import.meta.env.BASE_URL + 'textures/'
    const imgs = options.imgs || ['posx.jpg', 'negx.jpg', 'posy.jpg', 'negy.jpg', 'posz.jpg', 'negz.jpg']
    this.cubeTextureLoader.setPath(texturePath)
    const background = this.cubeTextureLoader.load(imgs, () => {
      const pmremGenerator = new THREE.PMREMGenerator(this.renderer)
      background.colorSpace = 'srgb' as any
      background.format = THREE.RGBAFormat
      background.magFilter = THREE.LinearFilter
      background.needsUpdate = true

      this.scene.environment = this.bgEnv = pmremGenerator.fromCubemap(background).texture
      this.useRoomEnv = false
      pmremGenerator.dispose()
    })

    this.background = background
    this.scene.background = this.background
    this.sceneArgs.background = { texturePath: texturePath, imgs: imgs }
    useSceneStore().setSkybox(JSON.stringify({ path: texturePath, imgs: imgs }))
  }

  private disposeBackgroundTexture() {
    if (this.background && typeof this.background.dispose === 'function') {
      this.background.dispose()
    }
    this.background = null
    if (this.scene) {
      this.scene.background = null
    }
    this.sceneArgs.background = undefined

    if (this.bgEnv) {
      this.bgEnv.dispose()
      this.bgEnv = null
    }
  }

  public toggleRoomEnviroment() {
    if (!this.roomEnv) {
      const pmremGenerator = new THREE.PMREMGenerator(this.renderer)
      const environment = new RoomEnvironment()
      this.roomEnv = pmremGenerator.fromScene(environment).texture
      pmremGenerator.dispose()
    }

    if (!this.useRoomEnv) {
      this.scene.environment = this.roomEnv
      this.useRoomEnv = true
    } else {
      this.scene.environment = this.bgEnv
      this.useRoomEnv = false
    }
  }

  public enableRoomEnvironment() {
    if (!this.roomEnv) {
      const pmremGenerator = new THREE.PMREMGenerator(this.renderer)
      const environment = new RoomEnvironment()
      this.roomEnv = pmremGenerator.fromScene(environment).texture
      pmremGenerator.dispose()
    }
    this.scene.environment = this.roomEnv
    this.useRoomEnv = true
  }

  public setDaylightBackground(color: string) {
    this.disposeBackgroundTexture()
    const nextColor = new THREE.Color(color || '#dff5ff')
    this.renderer.setClearColor(nextColor)
    this.scene.background = nextColor
    this.background = null
    this.sceneArgs.background = { color: color || '#dff5ff', type: 'daylight-color' }
  }

  public setGrid(options: any) {
    if (this.grid) {
      this.scene.remove(this.grid)
      this.grid = undefined
      this.sceneArgs.grid = undefined
    }
    if (options.turnOff) {
      useSceneStore().turnOffBackground('grid')
      return
    }

    this.grid = new THREE.Group()

    const size = options.size || 1000
    const division = options.division || 10
    const color1 = options.colorCenterLine || '#FF0000'
    const color2 = options.colorGrid || '#444444'
    this.sceneArgs.grid = { size: size, division: division, color1: color1, color2: color2 }
    const gridLine = new THREE.GridHelper(size, division, color1, color2)
    gridLine.material.opacity = 0.4
    gridLine.material.transparent = true
    this.grid.add(gridLine)

    const model = new Model()
    model.loadModel(import.meta.env.BASE_URL + 'models/dir.glb', { offset: { x: 380, y: 5, z: 200 } }).then(() => {
      model.rootObject.rotateY(90 * Math.PI / 180.0)
      this.grid.add(model.rootObject)
    })
    this.scene.add(this.grid)
    useSceneStore().setGrid({ on: true })
  }

  public setGroundPane(options: any) {
    if (this.groundPane) {
      this.scene.remove(this.groundPane)
      this.groundPane = undefined
      this.sceneArgs.groundPane = undefined
    }
    if (options.turnOff) {
      useSceneStore().turnOffBackground('ground')
      return
    }

    const width = options.width || 1000
    const height = options.height || 1000
    const planeGeometry = new THREE.PlaneGeometry(width, height)
    this.sceneArgs.groundPane = options
    let planeMaterial = null
    if (options.texture && options.texture !== '') {
      const texture = this.textureLoader.load(options.texture)
      const wrapS = options.wrapS || 2
      const wrapT = options.wrapT || 2
      texture.wrapS = texture.wrapT = THREE.RepeatWrapping
      texture.repeat.set(wrapS, wrapT)
      planeMaterial = new THREE.MeshStandardMaterial({
        map: texture,
        transparent: true,
        side: THREE.DoubleSide
      })
    } else {
      const color = options.color || '#88cc88'
      planeMaterial = new THREE.MeshStandardMaterial({
        color: color,
        side: THREE.DoubleSide
      })
    }
    this.groundPane = new THREE.Mesh(planeGeometry, planeMaterial)
    this.groundPane.rotation.x = -Math.PI / 2.0
    this.groundPane.position.y = -0.1
    this.groundPane.receiveShadow = true
    this.groundPane.userData.type = 'groundPane'
    this.scene.add(this.groundPane)
    useSceneStore().setGroundPane({ texture: options.texture, color: options.color, on: true })
  }

  public applyTomatoGreenhouseVisualTemplate(template: TomatoGreenhouseVisualTemplate, tomatoModels: Array<{ offset: { x: number; y: number; z: number }; scale: number }>) {
    this.clearSemanticTemplateLayer()
    const layer = new THREE.Group()
    layer.name = template.templateKey || 'tomato_greenhouse_visual_template'
    layer.userData.type = 'semanticVisualTemplate'
    layer.userData.templateKey = template.templateKey

    this.addGreenhouseShell(layer, template)
    this.addGreenhouseBeds(layer, template)
    this.addIrrigationNetwork(layer, template)
    this.addTemplateEquipmentMarkers(layer, template)

    this.scene.add(layer)
    this.semanticTemplateLayer = layer
    this.semanticTemplateSnapshot = {
      templateKey: template.templateKey,
      greenhouse: template.greenhouse,
      tomatoes: tomatoModels.map(item => ({
        x: item.offset.x,
        y: item.offset.y,
        z: item.offset.z,
        scale: item.scale
      })),
      irrigation: {
        bedCount: template.irrigation.bedCount,
        dripLineCount: template.irrigation.dripLineCount,
        mainPipeLength: template.irrigation.mainPipeLength,
        valveCount: template.irrigation.valvePositions?.length || 0
      },
      lighting: template.lighting
    }
  }

  public clearSemanticTemplateLayer() {
    if (!this.semanticTemplateLayer) return
    this.disposeObjectTree(this.semanticTemplateLayer)
    this.scene.remove(this.semanticTemplateLayer)
    this.semanticTemplateLayer = null
    this.semanticTemplateSnapshot = null
  }

  public getSemanticTemplateSnapshot(): TomatoGreenhouseSnapshot | null {
    return this.semanticTemplateSnapshot
  }

  private addGreenhouseShell(layer: THREE.Group, template: TomatoGreenhouseVisualTemplate) {
    const { center, width, depth, height } = template.greenhouse
    const shell = new THREE.Group()
    shell.name = 'greenhouse-shell'
    shell.position.set(center.x, center.y, center.z)

    const glassMaterial = new THREE.MeshPhysicalMaterial({
      color: '#d9fff4',
      transparent: true,
      opacity: 0.24,
      roughness: 0.18,
      metalness: 0,
      side: THREE.DoubleSide,
      transmission: 0.35
    })
    const roofMaterial = new THREE.MeshPhysicalMaterial({
      color: '#efffff',
      transparent: true,
      opacity: 0.34,
      roughness: 0.2,
      side: THREE.DoubleSide,
      transmission: 0.28
    })
    const frameMaterial = new THREE.MeshStandardMaterial({ color: '#d7e4e8', metalness: 0.25, roughness: 0.36 })

    const sideGeometry = new THREE.BoxGeometry(width, height * 0.62, 4)
    const front = new THREE.Mesh(sideGeometry, glassMaterial)
    front.position.set(0, height * 0.31, depth / 2)
    const back = front.clone()
    back.position.z = -depth / 2
    shell.add(front, back)

    const sideWallGeometry = new THREE.BoxGeometry(4, height * 0.62, depth)
    const left = new THREE.Mesh(sideWallGeometry, glassMaterial)
    left.position.set(-width / 2, height * 0.31, 0)
    const right = left.clone()
    right.position.x = width / 2
    shell.add(left, right)

    const roofShape = new THREE.Shape()
    roofShape.moveTo(-width / 2, 0)
    roofShape.lineTo(0, height * 0.38)
    roofShape.lineTo(width / 2, 0)
    roofShape.lineTo(-width / 2, 0)
    const roofGeometry = new THREE.ExtrudeGeometry(roofShape, { depth, bevelEnabled: false })
    roofGeometry.rotateX(Math.PI / 2)
    roofGeometry.translate(0, height * 0.62, depth / 2)
    const roof = new THREE.Mesh(roofGeometry, roofMaterial)
    shell.add(roof)

    const frameRadius = 3
    const makeBeam = (length: number, axis: 'x' | 'y' | 'z') => {
      const geometry = axis === 'x'
        ? new THREE.BoxGeometry(length, frameRadius, frameRadius)
        : axis === 'y'
          ? new THREE.BoxGeometry(frameRadius, length, frameRadius)
          : new THREE.BoxGeometry(frameRadius, frameRadius, length)
      return new THREE.Mesh(geometry, frameMaterial)
    }
    const yMid = height * 0.32
    ;[-width / 2, width / 2].forEach(x => {
      ;[-depth / 2, depth / 2].forEach(z => {
        const post = makeBeam(height * 0.72, 'y')
        post.position.set(x, height * 0.36, z)
        shell.add(post)
      })
    })
    ;[-depth / 2, depth / 2].forEach(z => {
      const beam = makeBeam(width, 'x')
      beam.position.set(0, yMid, z)
      shell.add(beam)
    })
    ;[-width / 2, width / 2].forEach(x => {
      const beam = makeBeam(depth, 'z')
      beam.position.set(x, yMid, 0)
      shell.add(beam)
    })

    layer.add(shell)
  }

  private addGreenhouseBeds(layer: THREE.Group, template: TomatoGreenhouseVisualTemplate) {
    const bedCount = Math.max(1, template.plantGrid.bedCount || 4)
    const { center, width, depth } = template.greenhouse
    const bedWidth = width / (bedCount + 1.2)
    const bedDepth = depth * 0.72
    const spacing = width / bedCount
    const material = new THREE.MeshStandardMaterial({ color: '#7d5a34', roughness: 0.88, metalness: 0.02 })
    const edgeMaterial = new THREE.MeshStandardMaterial({ color: '#d7c58b', roughness: 0.72 })
    for (let i = 0; i < bedCount; i++) {
      const x = center.x + (i - (bedCount - 1) / 2) * spacing * 0.82
      const bed = new THREE.Mesh(new THREE.BoxGeometry(bedWidth, 8, bedDepth), material)
      bed.position.set(x, center.y + 3.5, center.z)
      bed.receiveShadow = true
      layer.add(bed)

      const edge = new THREE.Mesh(new THREE.BoxGeometry(bedWidth + 6, 3, bedDepth + 8), edgeMaterial)
      edge.position.set(x, center.y + 1.2, center.z)
      edge.receiveShadow = true
      layer.add(edge)
    }
  }

  private addIrrigationNetwork(layer: THREE.Group, template: TomatoGreenhouseVisualTemplate) {
    const pipeMaterial = new THREE.MeshStandardMaterial({ color: '#1e7aa8', roughness: 0.42, metalness: 0.18 })
    const dripMaterial = new THREE.MeshStandardMaterial({ color: '#111820', roughness: 0.5 })
    const valveMaterial = new THREE.MeshStandardMaterial({ color: '#f5b642', roughness: 0.32, metalness: 0.12 })
    const { center, depth } = template.greenhouse
    const mainPipe = this.cylinderBetween(
      new THREE.Vector3(center.x - template.irrigation.mainPipeLength / 2, 7, center.z + depth * 0.44),
      new THREE.Vector3(center.x + template.irrigation.mainPipeLength / 2, 7, center.z + depth * 0.44),
      4,
      pipeMaterial
    )
    mainPipe.name = 'irrigation-main-pipe'
    layer.add(mainPipe)

    const lineCount = Math.max(1, template.irrigation.dripLineCount || 8)
    const usableWidth = template.greenhouse.width * 0.72
    for (let i = 0; i < lineCount; i++) {
      const x = center.x + (i - (lineCount - 1) / 2) * (usableWidth / Math.max(1, lineCount - 1))
      const line = this.cylinderBetween(
        new THREE.Vector3(x, 10, center.z - depth * 0.33),
        new THREE.Vector3(x, 10, center.z + depth * 0.34),
        1.4,
        dripMaterial
      )
      line.name = 'irrigation-drip-line'
      layer.add(line)
    }

    ;(template.irrigation.valvePositions || []).forEach((pos, index) => {
      const valve = new THREE.Mesh(new THREE.SphereGeometry(8, 16, 12), valveMaterial)
      valve.name = `irrigation-valve-${index + 1}`
      valve.position.set(pos.x, pos.y + 8, pos.z)
      layer.add(valve)
    })
  }

  private addTemplateEquipmentMarkers(layer: THREE.Group, template: TomatoGreenhouseVisualTemplate) {
    const pumpMaterial = new THREE.MeshStandardMaterial({ color: '#2f7d55', roughness: 0.5, metalness: 0.2 })
    const pump = new THREE.Mesh(new THREE.BoxGeometry(28, 18, 24), pumpMaterial)
    pump.name = 'procedural-pump-marker'
    pump.position.set(template.irrigation.pumpPosition.x, 11, template.irrigation.pumpPosition.z)
    layer.add(pump)
  }

  private cylinderBetween(start: THREE.Vector3, end: THREE.Vector3, radius: number, material: THREE.Material) {
    const direction = new THREE.Vector3().subVectors(end, start)
    const length = direction.length()
    const geometry = new THREE.CylinderGeometry(radius, radius, length, 16)
    const cylinder = new THREE.Mesh(geometry, material)
    cylinder.position.copy(start).add(end).multiplyScalar(0.5)
    cylinder.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize())
    cylinder.castShadow = true
    cylinder.receiveShadow = true
    return cylinder
  }

  private disposeObjectTree(obj: THREE.Object3D) {
    obj.traverse((child: any) => {
      if (child.geometry) {
        child.geometry.dispose()
      }
      if (child.material) {
        const materials = Array.isArray(child.material) ? child.material : [child.material]
        materials.forEach((material: any) => {
          if (material.map) material.map.dispose()
          material.dispose()
        })
      }
    })
  }

  public setCameraPosition(pos: any) {
    this.camera.position.set(pos.x, pos.y, pos.z)
  }

  // ==================== 地形 ====================
  public async generateTerrain(params: { type: string; url?: string; width?: number; depth?: number; segments?: number; heightScale?: number; colorLow?: string; colorHigh?: string }): Promise<void> {
    if (this.terrainMesh) {
      this.removeTerrain()
    }
    const options: TerrainOptions = {
      width: params.width || 1000,
      depth: params.depth || 1000,
      segments: params.segments || 128,
      heightScale: params.heightScale || 80,
      colorLow: params.colorLow || '#336633',
      colorHigh: params.colorHigh || '#99bb55'
    }
    this.terrainImporter = new TerrainImporter(options)
    try {
      if (params.type === 'heightmap' && params.url) {
        this.terrainMesh = await this.terrainImporter.loadHeightmap(params.url)
      } else if (params.type === 'geojson' && params.url) {
        this.terrainMesh = await this.terrainImporter.loadGeoJSON(params.url)
      } else if (params.type === 'dem' && params.url) {
        this.terrainMesh = await this.terrainImporter.loadHeightmap(params.url, undefined)
        this.terrainMesh.userData.terrainSource = 'dem'
      }
      if (this.terrainMesh) {
        this.scene.add(this.terrainMesh)
        this.sceneArgs.terrain = { type: params.type, options }
        // 同时更新地面颜色为不可见
        if (this.groundPane) {
          this.groundPane.material.opacity = 0
        }
        this.layerManager.addModelToLayer('terrain', 'default')
      }
    } catch (err) {
      console.error('Terrain generation failed:', err)
      throw err
    }
  }

  public removeTerrain() {
    if (this.terrainMesh) {
      this.scene.remove(this.terrainMesh)
      this.terrainMesh.geometry.dispose()
      if (Array.isArray(this.terrainMesh.material)) {
        this.terrainMesh.material.forEach(m => m.dispose())
      } else {
        this.terrainMesh.material.dispose()
      }
      this.terrainMesh = null
      this.terrainImporter = null
      this.sceneArgs.terrain = undefined
      if (this.groundPane) {
        this.groundPane.material.opacity = 1
      }
    }
  }

  // ==================== 图层管理 ====================
  public createLayer(name: string, color: string) {
    const layer = this.layerManager.createLayer(name, color)
    useLayerStore().setLayers(this.layerManager.getAllLayers())
    return layer
  }

  public deleteLayer(layerId: string) {
    this.layerManager.deleteLayer(layerId)
    useLayerStore().setLayers(this.layerManager.getAllLayers())
  }

  public toggleLayerVisible(layerId: string) {
    const layer = this.layerManager.getLayer(layerId)
    if (layer) {
      this.layerManager.setLayerVisible(layerId, !layer.visible, this.scene, this.sceneModels)
      useLayerStore().setLayers(this.layerManager.getAllLayers())
    }
  }

  public toggleLayerLocked(layerId: string) {
    const layer = this.layerManager.getLayer(layerId)
    if (layer) {
      this.layerManager.setLayerLocked(layerId, !layer.locked)
      useLayerStore().setLayers(this.layerManager.getAllLayers())
    }
  }

  public renameLayer(layerId: string, name: string) {
    this.layerManager.renameLayer(layerId, name)
    useLayerStore().setLayers(this.layerManager.getAllLayers())
  }

  public moveModelsToLayer(modelIds: string[], targetLayerId: string) {
    modelIds.forEach(mid => this.layerManager.addModelToLayer(mid, targetLayerId))
    useLayerStore().setLayers(this.layerManager.getAllLayers())
  }

  public refreshLayerStore() {
    useLayerStore().setLayers(this.layerManager.getAllLayers())
  }

  // ==================== 批量操作 ====================
  public batchMove(deltaX: number, deltaY: number, deltaZ: number) {
    this.selectedModels.forEach(modelId => {
      const model = this.sceneModels[modelId]
      if (model && !this.layerManager.isModelLocked(modelId)) {
        model.rootObject.position.x += deltaX
        model.rootObject.position.y += deltaY
        model.rootObject.position.z += deltaZ
        model.syncPositionOptions()
      }
    })
  }

  public batchRotate(angleDelta: number) {
    this.selectedModels.forEach(modelId => {
      const model = this.sceneModels[modelId]
      if (model && !this.layerManager.isModelLocked(modelId)) {
        model.rootObject.rotation.y += angleDelta * Math.PI / 180
        model.syncPositionOptions()
      }
    })
  }

  public batchScale(scaleFactor: number) {
    this.selectedModels.forEach(modelId => {
      const model = this.sceneModels[modelId]
      if (model && !this.layerManager.isModelLocked(modelId)) {
        const currentScale = model.rootObject.scale.x
        const newScale = Math.max(0.01, currentScale * scaleFactor)
        model.rootObject.scale.setScalar(newScale)
        model.syncPositionOptions()
      }
    })
  }

  public batchCopy() {
    const newIds: string[] = []
    this.selectedModels.forEach(modelId => {
      const model = this.sceneModels[modelId]
      if (model) {
        const saveData = model.saveModel()
        saveData.options.offset = {
          x: model.rootObject.position.x + 20,
          y: model.rootObject.position.y,
          z: model.rootObject.position.z + 20
        }
        this.loadModel(saveData.url, saveData.options).then((newModel) => {
          newIds.push(newModel.getModelId)
          const currentLayer = this.layerManager.getModelLayer(modelId) || 'default'
          this.layerManager.addModelToLayer(newModel.getModelId, currentLayer)
        })
      }
    })
    return newIds
  }

  public batchDelete() {
    this.selectedModels.forEach(modelId => {
      this.removeModel(modelId)
      this.layerManager.removeModel(modelId)
    })
    this.selectedModels.clear()
    this.refreshLayerStore()
  }

  public clearSelection() {
    this.selectedModels.forEach(modelId => {
      const model = this.sceneModels[modelId]
      if (model) model.deselect()
    })
    this.selectedModels.clear()
    this.syncMultiSelectToStore()
  }

  public selectModelsInLayer(layerId: string) {
    this.clearSelection()
    const modelIds = this.layerManager.getModelIdsInLayer(layerId)
    modelIds.forEach(id => {
      if (this.sceneModels[id]) {
        this.selectedModels.add(id)
        this.sceneModels[id].select()
      }
    })
    this.syncMultiSelectToStore()
  }

  private syncMultiSelectToStore() {
    // Notify model store about multi-select state
    const ids = Array.from(this.selectedModels)
    const modelStore = useModelStore()
    if (ids.length > 0 && this.sceneModels[ids[0]]) {
      modelStore.updateMultiSelection(ids.map(id => this.sceneModels[id]))
    } else {
      modelStore.updateMultiSelection([])
    }
  }

  // ==================== 吸附 ====================
  public setSnapConfig(config: Partial<SnapConfig>) {
    Object.assign(this.snapConfig, config)
    if (this.dragControl) {
      this.dragControl.setSnapConfig(this.snapConfig)
    }
  }

  public toggleSnap(enabled?: boolean) {
    this.snapConfig.enabled = enabled ?? !this.snapConfig.enabled
    if (this.dragControl) {
      this.dragControl.setSnapConfig(this.snapConfig)
    }
    if (!this.snapConfig.enabled && this.snapIndicatorMesh) {
      this.scene.remove(this.snapIndicatorMesh)
      this.snapIndicatorMesh = null
    }
  }

  /** 将世界坐标吸附到网格 */
  public snapToGrid(worldPos: THREE.Vector3): THREE.Vector3 {
    if (!this.snapConfig.enabled) return worldPos.clone()
    const gs = this.snapConfig.gridSize
    return new THREE.Vector3(
      Math.round(worldPos.x / gs) * gs,
      worldPos.y,
      Math.round(worldPos.z / gs) * gs
    )
  }

  /** 查找最近的吸附点（网格 + 模型边缘） */
  public findNearestSnapPoint(worldPos: THREE.Vector3, excludeModelId?: string): THREE.Vector3 | null {
    if (!this.snapConfig.enabled) return null

    // 网格吸附
    const gridSnapped = this.snapToGrid(worldPos)
    if (gridSnapped.distanceTo(worldPos) < 1) return gridSnapped

    // 模型边缘吸附 — 查找最近的模型边缘
    let nearestPoint: THREE.Vector3 | null = null
    let nearestDist = Infinity
    const snapThreshold = 20

    for (const modelId in this.sceneModels) {
      if (modelId === excludeModelId) continue
      const model = this.sceneModels[modelId]
      const center = model.rootObject.position.clone()

      // 对每个轴方向计算吸附
      const box3 = new THREE.Box3().setFromObject(model.rootObject)
      const size = new THREE.Vector3()
      box3.getSize(size)

      // 4 个水平方向的边缘
      const halfW = size.x / 2
      const halfD = size.z / 2
      const edges = [
        new THREE.Vector3(center.x + halfW, center.y, center.z),
        new THREE.Vector3(center.x - halfW, center.y, center.z),
        new THREE.Vector3(center.x, center.y, center.z + halfD),
        new THREE.Vector3(center.x, center.y, center.z - halfD)
      ]

      for (const edge of edges) {
        const dist = new THREE.Vector2(worldPos.x - edge.x, worldPos.z - edge.z).length()
        if (dist < snapThreshold && dist < nearestDist) {
          nearestDist = dist
          nearestPoint = edge.clone()
        }
      }
    }

    return nearestPoint
  }

  // ==================== 框选 ====================
  public toggleBoxSelect(): boolean {
    if (!this.boxSelector) return false
    return this.boxSelector.toggle()
  }

  public getBoxSelector(): BoxSelector | null {
    return this.boxSelector
  }

  // ==================== 纹理刷 ====================
  public initTerrainBrush(): TerrainBrush {
    if (!this.terrainBrush) {
      this.terrainBrush = new TerrainBrush()
    }
    return this.terrainBrush
  }

  public getTerrainBrushInstance(): TerrainBrush | null {
    return this.terrainBrush
  }

  /** 获取射线与地面的交点 (UV) */
  public getGroundIntersection(event: PointerEvent): { point: THREE.Vector3; uv: { u: number; v: number } } | null {
    if (!this.groundPane && !this.terrainMesh) return null

    const rect = this.renderer.domElement.getBoundingClientRect()
    const mouse = new THREE.Vector2(
      ((event.clientX - rect.left) / rect.width) * 2 - 1,
      -((event.clientY - rect.top) / rect.height) * 2 + 1
    )
    const raycaster = new THREE.Raycaster()
    raycaster.setFromCamera(mouse, this.camera)

    const targets = []
    if (this.terrainMesh) targets.push(this.terrainMesh)
    if (this.groundPane) targets.push(this.groundPane)

    const intersects = raycaster.intersectObjects(targets)
    if (intersects.length > 0) {
      const point = intersects[0].point
      const w = (this.groundPane?.geometry?.parameters?.width || 1000)
      const d = (this.groundPane?.geometry?.parameters?.height || 1000)
      return {
        point,
        uv: {
          u: point.x / w + 0.5,
          v: point.z / d + 0.5
        }
      }
    }
    return null
  }

  // ==================== 场景模板 ====================
  public getTemplates() {
    return sceneTemplates
  }

  public applyTemplate(templateId: string): Promise<void> {
    const tpl = sceneTemplates.find(t => t.id === templateId)
    if (!tpl) return Promise.reject(new Error(`Template not found: ${templateId}`))

    this.clear()
    const cfg = tpl.config
    this.setSceneName(cfg.sceneName)

    if (cfg.ambientLight) {
      this.setAmbientLight({ color: cfg.ambientLight.color, intensity: cfg.ambientLight.intensity })
    }
    if (cfg.directionalLight) {
      this.setDirectionalLight({ color: cfg.directionalLight.color, intensity: cfg.directionalLight.intensity, pos: cfg.directionalLight.pos })
    }
    if (cfg.groundPane) {
      this.setGroundPane(cfg.groundPane)
    }
    if (cfg.grid) {
      this.setGrid(cfg.grid)
    }

    // 加载模板中的模型
    const loadPromises = (cfg.models || []).map(m =>
      this.loadModel(m.url, {
        offset: m.offset,
        scale: m.scale,
        angle: m.angle
      }).then(model => {
        this.layerManager.addModelToLayer(model.getModelId, 'default')
      })
    )

    return Promise.all(loadPromises).then(() => {
      this.refreshLayerStore()
    })
  }

  // ================ 模型加载 =====================
  public loadModel(url: string, options: any, onProgress?: (pct: number) => void): Promise<Model> {
    const model = new Model()
    return model.loadModel(url, options, onProgress).then(() => {
      this.scene.add(model.rootObject)
      if (model.animator) {
        this.aniMixers.push(model.animator)
      }
      this.sceneModels[model.getModelId] = model
      this.layerManager.addModelToLayer(model.getModelId, 'default')
      return model
    })
  }

  public removeAllModels() {
    this.aniMixers = []
    for (const modelId in this.sceneModels) {
      this.scene.remove(this.sceneModels[modelId].rootObject)
      this.layerManager.removeModel(modelId)
    }
    this.sceneModels = {}
    this.selectedModels.clear()
    this.refreshLayerStore()
  }

  public removeModel(modelId: string) {
    if (!this.sceneModels[modelId]) return
    this.scene.remove(this.sceneModels[modelId].rootObject)
    this.layerManager.removeModel(modelId)
    delete this.sceneModels[modelId]
    this.selectedModels.delete(modelId)
  }

  public copyModel(modelId: string) {
    if (!this.sceneModels[modelId]) return
    const srcModel = this.sceneModels[modelId]
    const saveData = srcModel.saveModel()
    delete saveData.options.sceneObjectId
    saveData.options.businessObjectId = ''
    saveData.options.isDefaultBinding = false
    saveData.options.offset = {
      x: srcModel.rootObject.position.x + 20,
      y: srcModel.rootObject.position.y,
      z: srcModel.rootObject.position.z + 20
    }
    this.loadModel(saveData.url, saveData.options)
  }

  public isEmpty(): boolean {
    return Object.keys(this.sceneModels).length === 0
  }

  public setView(view: string) {
    const pos = viewPositions[view]
    this.camera.position.set(pos[0], pos[1], pos[2])
    this.controls.target.set(0, 0, 0)
  }

  public getSceneName(): string {
    return this.sceneArgs.sceneName
  }

  public focusSceneObject(sceneObjectId: string): Model | null {
    const model = this.findModelBySceneObjectId(sceneObjectId)
    if (!model) return null
    if (this.selectObject) {
      this.selectObject.deselect()
    }
    this.clearSelection()
    model.select()
    this.selectObject = model
    const position = model.rootObject.position
    this.controls.target.set(position.x, position.y, position.z)
    this.camera.position.set(position.x + 180, position.y + 120, position.z + 180)
    this.controls.update()
    const modelStore = useModelStore()
    modelStore.updateActiveModel(model)
    return model
  }

  public findModelBySceneObjectId(sceneObjectId: string): Model | null {
    for (const modelId in this.sceneModels) {
      const model = this.sceneModels[modelId] as Model
      if (model.getSceneObjectId === sceneObjectId) {
        return model
      }
    }
    return null
  }

  public clear() {
    this.shutdownLights()
    this.setBackground({ turnOff: true })
    this.setGroundPane({ turnOff: true })
    this.setGrid({ turnOff: true })
    this.clearSemanticTemplateLayer()
    this.removeTerrain()
    if (this.terrainBrush) {
      this.terrainBrush.dispose()
      this.terrainBrush = null
    }
    this.removeAllModels()
    this.layerManager = new LayerManager()
    this.selectedModels.clear()
  }

  public setSceneName(name: string) {
    this.sceneArgs.sceneName = name
    useSceneStore().setSceneName(name)
  }

  public newScene() {
    this.clear()
    this.setAmbientLight({ color: '#ffffff', intensity: 0.6 })
    this.setBackground({})
    this.setGrid({})
    this.setSceneName('新建场景')
    this.refreshLayerStore()
  }

  public saveScene() {
    const saveData: any = { scene: this.sceneArgs, models: [] as any }
    saveData.scene.layers = this.layerManager.toJSON()
    if (this.terrainBrush) {
      saveData.scene.terrainBrush = this.terrainBrush.saveLayersData()
    }
    for (const key in this.sceneModels) {
      saveData.models.push({
        ...this.sceneModels[key].saveModel(),
        layerId: this.layerManager.getModelLayer(key) || 'default'
      })
    }
    return saveData
  }

  public laodScene(sceneName: string): Promise<void> {
    return axios.get('/scene/loadScene', { params: { scene: sceneName } }).then((res) => {
      if (res.data.code !== 200) {
        console.warn('Scene load failed:', res.data.data)
        return
      }
      const sceneData = res.data.data.scene
      this.clear()

      if (sceneData.layers) {
        this.layerManager.fromJSON(sceneData.layers)
      }
      this.setSceneName(sceneName)

      if (sceneData.ambientLight && sceneData.ambientLight.color) {
        this.setAmbientLight({ color: sceneData.ambientLight.color, intensity: sceneData.ambientLight.intensity, turnOff: false })
      } else {
        this.setAmbientLight({ turnOff: true })
      }

      if (sceneData.directionalLight && sceneData.directionalLight.color) {
        this.setDirectionalLight({ color: sceneData.directionalLight.color, intensity: sceneData.directionalLight.intensity, pos: sceneData.directionalLight.pos, turnOff: false })
      } else {
        this.setDirectionalLight({ turnOff: true })
      }

      if (sceneData.spotLight && sceneData.spotLight.color) {
        const sl = sceneData.spotLight
        this.setSpotLight({
          color: sl.color,
          intensity: sl.intensity,
          turnOff: false,
          angle: sl.angle || sl.angular || 0,
          hight: sl.hight || 300,
          distance: sl.distance || 500
        })
      } else {
        this.setSpotLight({ turnOff: true })
      }

      if (sceneData.background && sceneData.background.imgs) {
        this.setBackground({ texturePath: sceneData.background.texturePath, imgs: sceneData.background.imgs, turnOff: false })
      } else {
        this.setBackground({ turnOff: true })
      }

      if (sceneData.groundPane && (sceneData.groundPane.color || sceneData.groundPane.texture)) {
        this.setGroundPane({ color: sceneData.groundPane.color, turnOff: false, texture: sceneData.groundPane.texture })
      } else {
        this.setGroundPane({ turnOff: true })
      }

      if (sceneData.grid && sceneData.grid.size) {
        this.setGrid({
          size: sceneData.grid.size,
          division: sceneData.grid.division || 10,
          color1: sceneData.grid.color1 || '#FF0000',
          color2: sceneData.grid.color2 || '#444444'
        })
      } else {
        this.setGrid({ turnOff: true })
      }

      const models = res.data.data.models
      if (models && models.length > 0) {
        const loadPromises = models.map(async (model: any) => {
          try {
            const m = await this.loadModel(model.url, model.options)
            if (model.layerId) {
              this.layerManager.addModelToLayer(m.getModelId, model.layerId)
            }
          } catch (err) {
            console.warn('Scene model load skipped:', model.url, err)
          }
        })
        return Promise.all(loadPromises).then(() => {
          this.refreshLayerStore()
        })
      }
    }).catch((err) => {
      console.error('Failed to load scene:', sceneName, err)
      throw err
    })
  }

  public selectModel(x: number, y: number): Model | null {
    const raycaster = new THREE.Raycaster()
    const mouse = new THREE.Vector2()

    mouse.x = (x / this.width) * 2 - 1
    mouse.y = -((y / this.height) * 2 - 1)
    raycaster.setFromCamera(mouse, this.camera)

    const intersects = raycaster.intersectObjects(this.scene.children)

    if (this.selectObject) {
      this.selectObject.deselect()
      this.selectObject = null

      if (this.dragControl) {
        this.dragControl._model = null
      }
    }
    this.clearSelection()

    if (intersects.length > 0) {
      let selectObj = intersects[0].object

      while (selectObj && ((!selectObj.userData.type) || (selectObj.userData.type !== 'targetObj'))) {
        if (!selectObj.parent) return null
        selectObj = selectObj.parent
      }

      if (!selectObj) return null

      this.selectObject = this.sceneModels[selectObj.userData.modelId]
      if (this.selectObject) {
        this.selectObject.select()

        if (this.dragControl) {
          this.dragControl._model = this.selectObject
        }
      }

      return this.selectObject
    }
    return null
  }

  private static animate() {
    const scene = Scene.sceneInstance

    if (!scene.init) return

    scene.controls.update()
    scene.renderer.clear()

    if (scene.aniMixers.length > 0) {
      const delta = scene.clock.getDelta()
      for (let i = 0; i < scene.aniMixers.length; i++) {
        scene.aniMixers[i].update(delta)
      }
    }
    requestAnimationFrame(Scene.animate)
    scene.renderer.render(scene.scene, scene.camera)

    Scene.extScenes.forEach((extScene) => {
      if (extScene.init) {
        extScene.controls.update()
        extScene.renderer.clear()
        extScene.renderer.render(extScene.scene, extScene.camera)
      }
    })
  }
}
