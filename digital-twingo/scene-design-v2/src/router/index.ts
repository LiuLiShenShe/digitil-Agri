/**
 *   三维数字孪生设计平台
 *
 *  @brief 基于Vue3、Element-Plus、Three.js 构建的 "三维数字孪生项目"
 *
 *    页面路由配置
 *
 *  @author Sparcle
 *  @version 2.0
 *  @date 2022-8-1
 *  @copyright 2014-2022, Beijing Yupont Electric Power Tech Co., Ltd.
 **/

import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import MainView from '../views/MainView.vue'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'home',
    component: MainView
  },
  {
    path: '/monitor',
    name: 'monitor',
    component: () => import('../views/MonitorCenterView.vue')
  },
  {
    path: '/business',
    name: 'business',
    component: () => import('../views/BusinessCenterView.vue')
  },
  {
    path: '/objects',
    name: 'objects',
    component: () => import('../views/AgriculturalObjectView.vue')
  },
  {
    path: '/assistant',
    name: 'assistant',
    component: () => import('../views/AssistantView.vue')
  },
  {
    path: '/about',
    name: 'about',
    component: () => import('../views/AboutView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
