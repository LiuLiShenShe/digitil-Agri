/**
 *   三维数字孪生设计平台
 *
 *  @brief Composable — 访问全局 $http, $envCfg, $bus
 *         替代原 Vuex + class-component 的 this.$xxx 模式
 **/

import { inject } from 'vue'
import type { AxiosStatic } from 'axios'
import type { Emitter } from 'mitt'

export function useGlobals() {
  const $http = inject<AxiosStatic>('$http')!
  const $envCfg = inject<{ editMode: boolean; showTest: boolean }>('$envCfg')!
  const $bus = inject<Emitter<any>>('$bus')!

  return { $http, $envCfg, $bus }
}
