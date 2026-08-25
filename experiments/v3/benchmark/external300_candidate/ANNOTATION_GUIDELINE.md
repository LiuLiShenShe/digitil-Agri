# External300 blind annotation guideline

## 1. 角色隔离

- Reviewer A 与 Reviewer B：不得参与 KAFarmTwin/SingleAgent 方法实现，不得查看任一方法的输出、成功率或失败类型。
- Adjudicator：只在 A/B 不一致时介入；同样不得查看方法输出。
- 实验执行者：只有在 300 条全部完成审查和冻结后才能拿到 sealed Gold。
- Reviewer 可以查看 public input、Gold 草案、本规范和公开来源，但不能运行被比较方法。

## 2. 独立审查顺序

1. A、B 分别复制 `external300_review_queue.csv`，独立填写，不相互查看意见。
2. 每条只允许 `approve`、`needs_revision` 或 `reject`。
3. 两人均为 `approve` 才可直接通过。
4. 任一 `needs_revision/reject` 或两人结论不一致，必须进入第三人裁决。
5. 修改后的题目视为新版本，A、B 必须重新审查；不得由生成者自行改完后直接标记 approved。

## 3. 通用检查清单

每条任务都要回答：

- Prompt 是否自然、无歧义，并给出完成任务所需的所有契约信息？
- Gold 是否只要求 Prompt 或公开 `initial_state` 能推出的内容？
- 是否存在多个合理答案而 Gold 只接受一个？若有，补充 `allowed_variants/equivalence_groups` 或退回。
- public input 是否泄漏 required/expected/goal/critical 等答案字段？
- 任务是否与 frozen `test_v2` 只是换数字、换作物的近似复刻？若是，退回并改写场景。
- 难度标签是否合理？
- 对象 ID、时间、单位、父子关系与绑定目标是否自洽？
- 任务能否在不访问 Gold 的情况下完成？
- Gold 是否能被当前冻结 evaluator 明确评分？

## 4. 分类型检查

### scene_construction

- 植株总数、作物行、Plot、WeatherStation、Camera 数量与 prompt 完全一致。
- 每条 required edge 的端点存在。
- Camera 的观察目标公开可推断；含 Camera 的 prompt 明确要求观察目标、位姿和视场。
- hard 任务中的 Plot 层级不能与 CropRow 父节点冲突。

### asset_routing

- focus=`high_fidelity`，background=`lightweight_glb`，数量无歧义。
- 只有 prompt 明确说缺失的设备才允许 `asset_job/placeholder`。
- placeholder 的设备类型与数量必须逐一对应。

### data_binding

- 传感器 ID、metric、unit、目标作物行和 timestamp 均在 public input 中可见。
- 每个 sensor_bind 指向正确行；每个 trait_bind 指向正确关键植株。
- Gold timestamp 必须与 prompt 字符串逐字一致。
- 不接受只靠 Gold 才能知道的 trait、unit 或 target。

### rule_repair

- 本版只允许一个 critical object 和 `replace_asset` 路径。
- initial→goal 只能改变 critical object；其他对象、ID 和层级必须保持。
- 原 asset 与目标 asset 都必须在 prompt 公开。
- Camera/Sensor 的非目标合法属性必须被保留。

### memory_query

- `required_nodes/edges/bindings` 必须为空。
- query window 内记录决定 daily means/mean/latest；窗口外 interference 不得进入 Gold。
- evidence IDs 必须全部真实存在，且只包含窗口内相关记录/事件。
- 本版记录必须标注为 deterministic synthetic，不能误标成 WUR 实测值。

## 5. 裁决与冻结门槛

只有同时满足以下条件，任务才能将 `review_status` 改为 `approved`：

- A/B 两份独立记录齐全；
- 所有分歧有第三人裁决；
- 修改项完成二次复核；
- schema、Oracle、防泄漏和重复校验为 0 error；
- 每类仍为 60 条，难度仍为 15/30/15；
- `external300_review_queue.csv` 的 `final_status=approved`、`freeze_eligible=true`。

不得为了提高方法成绩而删除、降难度或修改失败题。
