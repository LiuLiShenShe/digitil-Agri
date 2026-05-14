# 第 3 周：接 Eino DeepAgents

## 1. 本周目标

把第 2 周的 LLM 语义解析升级成真正的后端智能体编排。
这一周的重点是：让主 Agent 负责“判断、拆解、调度”，让工具和布局器负责“执行、计算、校验”。

## 2. 本周范围

- 引入 Eino DeepAgents。
- 让主 Agent 调度场景规划、模型检索、布局求解、结果校验。
- 只开放业务白名单工具。
- 禁用 Shell、文件系统和任意写操作。
- 前端接口保持不变，仍然返回 `scenePlan / models / warnings`。

## 3. 具体任务

### 3.1 接入 Eino 依赖

引入官方要求的版本和基础配置：

- Eino `v0.5.14+`
- Tool-calling 模型
- OpenAI-compatible 或其他可用模型适配器

### 3.2 封装 `SceneBuilderAgent`

创建一个主 Agent，职责是：

- 读取用户输入
- 判断是否需要拆解任务
- 调用子 Agent 或工具
- 汇总最终场景方案

主 Agent 不直接改数据库，不直接写前端场景。

### 3.3 设计子 Agent / 工具映射

推荐先抽成 3 个逻辑子模块：

- `SemanticPlannerAgent`
- `AssetAgent`
- `LayoutAgent`

如果第一版先不做多子 Agent，也可以先用普通工具函数实现，后续再迁到 DeepAgents。

### 3.4 注册工具白名单

只保留这些业务工具：

- `model.search`
- `model.metadata`
- `scene.current`
- `scene.plan`
- `layout.solve`
- `layout.validate`

不开放：

- Shell `execute`
- 文件系统写入
- 任意 HTTP 请求
- 任意数据库写入

### 3.5 增加任务追踪和日志

记录每次智能体调用：

- 用户原始输入
- 触发的工具
- 工具返回结果摘要
- 最终场景方案
- 失败原因

这样后面才能排查“为什么这次没搭好”。

### 3.6 保持前端契约不变

前端仍然只认这类结果：

- `scenePlan`
- `models[]`
- `warnings[]`
- `missingAssets[]`

也就是说，这周是“后端实现替换”，不是“前端大改版”。

## 4. 产出物

- Eino DeepAgents 后端骨架
- `SceneBuilderAgent`
- 工具白名单
- Agent 调用日志
- 保持稳定的前端返回格式

## 5. 验收标准

- 复杂任务能自动拆成步骤。
- 系统能先查模型、再规划、再布局、再校验。
- Agent 不会因为 Shell 或文件系统误操作污染环境。
- 前端不需要改大逻辑就能继续使用。

## 6. 风险与处理

- 风险：Agent 调用变慢。  
  处理：只在复杂任务启用 DeepAgents，简单任务可以直接走规则/LLM。

- 风险：工具边界不清。  
  处理：只开放白名单，不开放底层系统能力。

- 风险：多轮调用成本高。  
  处理：控制 `MaxIteration`，并尽量把规则布局器放在确定性代码里。

## 7. 我能否完成

这周我可以完成代码接入和框架封装。
但要真正跑通，需要你提供可用的模型服务配置，以及最终选定的 Eino 版本和部署方式。
