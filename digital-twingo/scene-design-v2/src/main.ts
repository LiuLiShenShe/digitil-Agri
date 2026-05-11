/**
 *   三维数字孪生设计平台
 *
 *  @brief 基于Vue3、Element-Plus、Three.js 构建的 "三维数字孪生项目"
 *         支持 gltf 3D 模型场景构建，2D/3D 可视化展示
 *
 *    程序入口，初始化 Vue 环境，加载全局配置、组件
 *
 *  @author Sparcle
 *  @version 2.0
 *  @date 2022-7-5
 *  @copyright 2014-2022, Beijing Yupont Electric Power Tech Co., Ltd.
 **/

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import axios from 'axios'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import locale from 'element-plus/es/locale/lang/zh-cn'
import contextmenu from 'v-contextmenu'
import 'v-contextmenu/dist/themes/default.css'
import mitt from 'mitt'

if (import.meta.env.VITE_RUNMODE === 'debug') {
  console.log(import.meta.env)
}

if (import.meta.env.VITE_MOCK === 'true') {
  import('./mock')
} else {
  axios.defaults.baseURL = import.meta.env.VITE_BASEURL
}

const app = createApp(App)

// Global properties via provide
const VueEvent = mitt()
const envCfg = {
  editMode: import.meta.env.VITE_EDITMODE === 'true',
  showTest: import.meta.env.VITE_SHOWTEST === 'true'
}

app.provide('$http', axios)
app.provide('$envCfg', envCfg)
app.provide('$bus', VueEvent)

app.use(createPinia())
app.use(router)
app.use(contextmenu)
app.use(ElementPlus, { locale })
app.mount('#app')

window.addEventListener('resize', () => {
  VueEvent.emit('winowResize')
})
