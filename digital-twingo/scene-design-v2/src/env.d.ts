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
