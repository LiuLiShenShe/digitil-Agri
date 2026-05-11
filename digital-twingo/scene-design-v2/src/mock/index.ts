/**
 *   三维数字孪生设计平台
 *
 *    Mock API 入口 — 使用 Vite 的 import.meta.glob 替代 webpack require.context
 *
 *  @author Sparcle
 *  @version 2.0
 **/

import Mock from 'mockjs'

const modules = import.meta.glob('./modules/*.ts', { eager: true }) as Record<string, any>

Object.keys(modules).forEach(key => {
  const mod = modules[key]
  if (mod && typeof mod === 'object') {
    Object.keys(mod).forEach(handlerKey => {
      const handlers = mod[handlerKey]
      if (Array.isArray(handlers)) {
        handlers.forEach((h: any) => {
          if (h.url && h.type && h.response) {
            Mock.mock(new RegExp(h.url), h.type, h.response)
          }
        })
      }
    })
  }
})
