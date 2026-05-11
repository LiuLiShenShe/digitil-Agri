/**
 *   三维数字孪生设计平台
 *
 *    实用小工具函数
 *
 *  @author Sparcle
 *  @version 2.0
 **/

export function uuid() {
  return 'xxxxxxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

export function fmtNumber(d: number): number {
  return Math.round(d * 100) / 100
}

function getDate(d: Date): string {
  return d.getFullYear() + '-' + d.getMonth() + '-' + d.getDate()
}

export function today(): string {
  return getDate(new Date())
}

export function nextDay(): string {
  const d = new Date()
  d.setTime(d.getTime() + 24 * 60 * 60 * 1000)
  return getDate(d)
}
