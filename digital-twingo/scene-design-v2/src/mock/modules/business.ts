/**
 *   business mock API
 */

export const businessMock = [
  {
    url: '/business/overview',
    type: 'get',
    response: () => {
      const now = new Date().toISOString()
      const systems = [
        ['soil', '土壤墒情系统', 68],
        ['weather', '气候/气象监测', 72],
        ['irrigation', '水肥灌溉系统', 58],
        ['greenhouse', '大棚智能控制', 55],
        ['video', '视频监控系统', 42],
        ['environment', '环境监测', 48]
      ]
      return {
        code: 200,
        data: {
          updatedAt: now,
          parkName: '智慧农业示范园区',
          summary: {
            systemTotal: 6,
            demoReadyCount: 0,
            partialCount: 6,
            missingCount: 0,
            warningAlerts: 1,
            criticalAlerts: 0,
            unackedAlerts: 1,
            overallScore: 55.2,
            completionRate: 57.2
          },
          subsystems: systems.map(([key, name, rate]) => ({
            key,
            name,
            objective: '演示环境下的业务闭环验收视图。',
            status: 'warning',
            implementationLevel: 'partial',
            completionRate: rate,
            primaryDeviceIds: [],
            metrics: [
              { key: 'temperature', label: '温度', value: 24.6, unit: '°C', status: 'normal' },
              { key: 'soilMoisture', label: '墒情', value: 52.1, unit: '%', status: 'normal' }
            ],
            workflows: [
              { name: '数据接入', state: 'ready', description: '已有模拟数据接入。' },
              { name: '业务闭环', state: 'partial', description: '仍需补齐配置、处置和联动。' }
            ],
            alerts: [],
            gaps: ['缺少真实设备接入验收。', '缺少完整操作日志和权限控制。']
          }))
        }
      }
    }
  }
]
