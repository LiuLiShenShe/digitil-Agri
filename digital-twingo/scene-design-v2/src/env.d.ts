/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module 'v-contextmenu' {
  import type { Plugin } from 'vue'
  const plugin: Plugin
  export default plugin
}

declare module 'mockjs' {
  const Mock: any
  export default Mock
}

declare module 'three' {
  export * from '@types/three'
}

export {}

declare global {
  interface Window {
    __tomatoGreenhouseVisualAcceptance?: {
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
    } | null
  }
}
