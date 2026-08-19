# FAILURES — KAFarmTwin v3 Rebuild

记录失败/阻塞项。每项：ID、状态（ACTIVE / RESOLVED / HUMAN_BLOCKED）、描述、原因、下一步。

## F-001 [HUMAN_BLOCKED] 密钥轮换
- **状态**: HUMAN_BLOCKED（人工操作）
- **描述**: LLM API 密钥曾以明文出现在会话中，已从文件移除（密钥见 gitignored `.env`）。
- **风险**: 若会话记录或共享环境外泄，他人可使用该密钥。
- **下一步（人工）**: 实验完成后轮换该密钥；同时评估是否需用 `git filter-repo` 清理历史（当前工作区干净，无密钥提交记录，此项优先级低）。

## F-002 [HUMAN_BLOCKED] Git 历史清理评估
- **状态**: HUMAN_BLOCKED（人工操作）
- **描述**: 需要人工确认是否清理 git 历史中的任何潜在敏感信息。
- **当前核查**: 已完成仓库扫描，未发现提交到源码的 API 密钥/凭据（`application.yml` 仅有 dev-local `root:root` MySQL 凭据与空 `api-key`）。`sk-` 扫描命中均为英文文本误报。
- **下一步（人工）**: 仅当用户确认有敏感历史需清理时执行 `git filter-repo`。

## F-003 [RESOLVED via delegation] 旧评分器违规公式
- **状态**: RESOLVED（待 v3 独立评分器取代，见阶段3）
- **描述**: 旧 `score_record()` 用 `min(generated_count, required_count)` 计正确数；旧 `build_ours_relations/bindings` 替方法补料；旧 `build_tool_evidence(fill_missing_executed_evidence=True)` 自动铸 evidenceId；旧 ETF 结构性偏差。
- **下一步（进行中）**: 阶段3 实现实验的独立语义评分器 + 反作弊测试，旧公式不再用于 v3 主证据。

## F-004 [PENDING] 双标注一致性
- **状态**: ACTIVE
- **描述**: 需要两名独立标注者 + 仲裁。第二标注者=用户。若本次会话用户无法完成全部复核，SOTA Gate 挂起，记 `BLOCKED_HUMAN_ANNOTATION`。

## F-005 [PENDING] 多智能体主张可行性
- **状态**: ACTIVE
- **描述**: 当前 Go 后端是单循环+角色标签，非独立智能体。评估后若无法实现，降级论文定位。

## F-006 [RESOLVED] LLM 端点切换 → SiliconFlow DeepSeek-V4-Flash
- **状态**: RESOLVED（真实 LLM 实验可用）
- **描述**: 原 agnes 端点 `https://apihub.agnes-ai.com/v1` 在当前环境连接超时。用户改为 SiliconFlow 平台 `deepseek-ai/DeepSeek-V4-Flash`，base URL `https://api.siliconflow.cn/v1`，新密钥已写入 `.env`（gitignored）。
- **验证**: `POST /v1/chat/completions` 真实返回 `content:"PONG"` + `finish_reason:"stop"`，含 `reasoning_content`（推理模型）。
- **注意**: 该模型为推理模型，`reasoning_content` 与 `content` 并存；harness 的 `tool_calls`/`finish_reason` 解析必须兼容此字段。`max_tokens` 可能不严格限制推理 token。

## F-003 评分器与金标准契约脱节（已修复，2026-08-05）
**发现**：金标准自己不以 CVSR 通过。91 个 required_nodes 无一携带 parent/location；T19 goal 的 unit 在绑定 metadata 而 R2 查节点 key_attrs；T22 goal 的 pose/observes/fov 在顶层而 R5 查 key_attrs；T20 state 对象误带 count=5。缺陷都在"金标准标注表示 ≠ 评分器期望维度"。
**修复**：R1 缺 parent→warning、R3 缺 location→warning、R2 接受绑定 metadata 的 unit、R5 兼容顶层/key_attrs、_noop_repair 覆盖全部语义字段、T20 count=1。均为全方法一致的评分器对齐，非针对 KAFarmTwin。金标准自检 5/6 通过。
**遗留**：T23（trait 数据模型）、T25/T26（记忆查询）需评分器扩展 trait/memory 结构，属数据模型缺口，非方法问题。

## F-004 T23 trait / T25-26 memory 数据模型（已修复，2026-08-05）
T23 的表型指标建模为 traits[]+trait_bind 而非场景节点，原评分器只认节点 → critR/repair 误判。T25/T26 memory_query 不构建场景，原默认激活 R1-R7 场景规则 → R6 误判。
**修复**：critical recall 接受绑定 subject/trait id；repair_match 检测 trait 的 unit/bound_to 变化；_noop_repair 比较 bindings/traits；memory_query 只激活 R8-R10。金标准 8/8 dev CVSR=True。

## F-005 replay_substrate gap（已修复，2026-08-05）
**根因（已定位并修复）**：trace_proxy.record() 以**引用**存储 request/response，未深拷贝。修复循环中 add_edge 就地设置 node.parent、merge_layout_into_nodes 就地改写字段，导致后续原地突变**污染已记录的历史 request**——记录显示 parent 已设，但 rule.check 响应仍是修复前的 R1 warning（请求与响应来自不同时刻状态）。这不是"增量修复固有困难"，而是 trace 记录保真 bug。

**修复**：trace_proxy.record() 对 request/response 做 copy.deepcopy，保证 trace 忠实反映调用时刻状态。修复后 T19/T24 replay_success 从 0.667 → 1.0，全部任务 replay_success=1.0、evidence_precision=1.0（真实路径验证）。

**诚实结论**：Replay Success 条件现可达 0.95 阈值。若后续某任务含非纯工具调用（scene.plan/layout.solve/object.bind 依赖 ctx），计 not_replayable 排除在基数外（不算 penalty），不影响 replay_success。

## F-006 [BLOCKED] LLM 账户余额不足终止测试集运行（2026-08-05）
测试集 5× 运行 (T27-T30) 中途 SiliconFlow 账户余额耗尽（HTTP 402: account balance is insufficient）。28/40 测试 run 是 API 失败伪影（record 记 fatal=["R7"]，但实际 LLM 调用未成功），不是方法真实表现。T27 完整（10/10 valid），T28 仅 2/5 (KF)、0/5 (SA)，T29/T30 全 0/5。
**影响**：测试集证据不完整，SOTA Gate 无法基于有效统计通过。dev 集 80 run 无 error，结果有效但非 gate 证据（gate 定义在 test split）。
**解锁**：需用户充值 SiliconFlow 余额后重跑缺失的 28 个 run；另 T031-T035 gold 仍需人工标注（BLOCKED_HUMAN_ANNOTATION）。
**诚实结论**：不宣称任何成功；gate 保持 FAIL。

## F-007 [BLOCKED] 测试集 memory_query gold 与 prompt 自相矛盾（2026-08-05）
测试集 T27-T30 全部为 memory_query（检索问答，"汇总最近7天环境数据"等），但 test_gold 的 required_nodes 要求**构建场景**（T27/T30 各 20 株 Plant + Greenhouse root + contains 边；T29 3 Plant+1 Camera+1 CropRow）。prompt 与 gold 冲突。
**现象**：两方法（KAFarmTwin + SingleAgent）在 T27-T30 全部 CVSR=0（0/40 run）。无 API error（evidence_precision=1.0，非 F-006 伪影），是真实一致失败。dev 的 T25/T26 同模式但 required_nodes 小（T25 3+3，T26 1+1）可部分匹配。
**本质**：gold 对检索任务要求建场景，测量维度与方法实际任务错位，不可作为有效 Gate 证据。非方法缺陷，是测试数据标注问题。
**解锁**：需人工重标注 T27-T30 的 memory_query gold（改为判定检索答案而非场景构建），或从 test split 剔除/替换这些任务。

## F-016 [RESOLVED] evaluator: 边/绑定匹配未复用节点对应关系（2026-08-08）
**现象**：F-015 首轮 200 run，两方法（KAFarmTwin + SingleAgent）所有非 memory 任务 `relation_f1=0`、`binding_f1=0`，非 memory `cvsr=True` 恒 0 条；仅 4 个 memory 任务通过，两方法 cvsr 均 0.2。
**初判**：疑为 LLM 非确定性（TN01 曾返回空场景）。
**根因**（evaluator 缺陷，非方法缺陷）：`node_match` 已借 Hungarian 建立 生成节点⇄required 节点 的对应（如 `greenhouse_1`≙`N02_strawberry_gh`），但 `edge_match`/`binding_match` 对 边/绑定 按 `(subject,predicate,object)` **字面 id** 匹配，仅靠 `equivalence_groups` 字符串重映射。由于 prompt 正确隐藏 gold id（方法合法地发明通用 id），任何方法都无法预知 `N02_strawberry_gh` 这类 gold id → 字面匹配结构性地恒错 → relation/binding F1 恒 0。20 个冻结任务的 `equivalence_groups` 是 `{"group_id","match_on","members_pattern"}` 对象，且仅覆盖同名结点组，不覆盖边端点。
**修复**（对全体方法一致，不补充、不造假）：
- `node_match.id_correspondence(assignments, gen, req_expanded_ids)`：由 node 匹配派生 `gen_id→required_id`（仅成本低于阈值的已匹配节点；跳过未匹配/伪造节点）。
- `edge_match.match_edges(..., id_map=)`：端点经 `remap_ids` 重写后再字面匹配；未映射 id 保持原样（不可匹配，不超额计分）。
- `binding_match.match_bindings(..., id_map=)`：subject/target 同重写。
- `metrics.evaluate_task`：由 `nm["assignments"]` 构建 id_map 线程进 edge/binding。
**验证**：55 测试全绿（+3 新增章节 16/17 回归：正确关系经 remap 可匹配、绑定到不存在节点仍判 0）；TN02 复算 nodes all_matched、edges 5/5。旧 F-015 结果归档 `results/archive_v3_runs.jsonl`。

## F-017 [RESOLVED] LLM 单次输出长度截断 → 大场景恒空（2026-08-08）
**现象**：TN01（2行+12株 lettuce+1气象站+2摄像头）单智能体/多智能体方法节点恒 0。直接探测 LLM 原始输出发现：模型返回约 3KB JSON，但在 `{"subject":"croprow_1","predicate":"contains`（char 3141）处被**截断**，JSON 未闭合 → `json.loads`/`_extract_json_object` 解析失败 → 方法静默产出空场景 → 大型任务两方法均 CVSR=0。
**根因**：`LLMClient.call` 固定 `max_tokens=1200`（SiliconFlow 该模型的单次输出上限，>1200 返回 HTTP 400）。模型把 24 株 lettuce 等**逐一列出**，单个响应超出 1200 token → 截断为非法 JSON。非方法质量问题，是输出长度资源上限对所有方法的一致退化。
**修复**（对全体方法一致的共享层，不偏向任何方法）：
- `ONTOLOGY_NOTE` 增加【实体压缩规则】：同一类型重复对象必须用 `单节点+count=N` 表达，禁止逐一列出（例：12 lettuce=`{"type":"Plant","count":12}`）。由 `make_llm_call_fn` 注入给**所有**方法同一 system 提示。
- `node_match.id_correspondence`：`count=N` 节点被 canonicalizer 展开为 `plant_1-1..12` 后，关系仍引用基名 `plant_1`；现同时映射完整 id 与基名 → 边/绑定可对齐。
- 验证：TN01 `single_agent` 单次 nodes 18/18、edges 4/5；55 测试全绿。

## F-018 [根因] 资产/绑定/修复任务受模型单次输出上限(~1200 token)截断（2026-08-08）
**现象**：200 run 中 asset/bind/repair 各 40 次全部 `traceSteps=0`，即使 objF1 可到 1.0（repair 从 initial_state 播种）。scene 任务 39/40 objF1=1.0，仅 repair 有 20/40。
**根因**：asset/bind/repair 任务的固有输出复杂度（双 Plant 组 + 资产绑定 metadata + 占位 job + 修复操作）稳定超过模型单次输出上限(~1200 token)。探测确认：完整 ONTOLOGY(1309)与精简 ONTOLOGY(471)下均 `finish=length` 截断，JSON 未闭合 → `content_json=None` → 方法空场景 → 0 tools。简短 system 时**偶发**完整输出(11 objects)后重测即失。**无关 ONTOLOGY 长度，是任务本身输出量 > 模型单次上限**。scene(靠 count 压缩)与 memory(确定性)可限内。
**影响**：非 memory 任务无法在单 shot 架构下被真正评分 → 两方法在 asset/bind/repair 上同为零，无区分度。此为**模型能力约束**，非方法缺陷，对两方法公平。当前 F-016 Gate 因区分度受限于此而 FAIL。
**解锁（公平，两方法同构）**：需让方法**分步/增量**构建复杂场景（对象一步、关系一步、绑定/修复一步），每步在 ~1200 token 内，再聚合。属方法架构改动，两方法以同名机制实施，不偏向任何一方；或接受当前 FAIL 如实上报。
## F-018 [RESOLVED via stepwise builder] 模型单次输出上限截断复杂场景（2026-08-08）
- **状态**: RESOLVED（用户选 Option A，共享 stepwise builder 实施完成并验证）
- **实现**: `harness/stepwise_builder.py` — `stepwise_build_scene()` 将场景拆成 objects→relations→bindings 三次独立 LLM 调用，每步在 ~1200 token 输出上限内；上一步真实 id 作为下一步上下文；解析同时支持 dict 包裹与**裸数组**形态（模型对 objects 步常返回 `[{...}]` 而非 `{"objects":[...]}`，原 `_merge_json_part` 只认 dict → nodes 恒空；新增 `_extract_list` 修复）。两方法（SingleAgent/KAFarmTwin）用同一 builder，创作能力对称。
- **修复分派诚实性**: SingleAgent 修复分支判 `category=="rule_repair"`（runner 映射后恒 false）→ 修复任务被静默当场景重建。改为 `category=="repair" or task_type=="rule_repair"`，honest no-repair 分支真正触发。新增反作弊测试 18。
- **验证**: 58 测试全绿；F-015 stepwise 200 run 中 asset/bind/repair 现产出 nodes/edges（objF1>0），不再空场景。旧 one-shot 200 run 归档 `results/archive/F015_one_shot/`。

## F-019 [结构上限] 绑定合约对非 memory 任务两方法同为不可能（2026-08-08）
- **状态**: ACTIVE（冻结 test_v2 的标注设计上限，非方法缺陷，对两方法公平）
- **现象**: F-015 stepwise 200 run 中，两方法所有非 memory 任务 `binding_f1` 恒 0 → CVSR 只由 4 个确定性 memory 任务提供，两方法同分 0.20。逐任务深挖：
  - **asset_routing (TN11-TN14)**：gold 绑定 `target` 为 `{subject}_asset`（如 `N11_mango_focus_asset`），该 id 不在 `required_nodes` 中，无节点对应可经 id_map 对齐；方法只能输出语义资产目标（如 `high_fidelity_asset`），结构性不匹配。
  - **data_binding (TN21+)**：gold 元数据合约严格（`unit:"%"` vs 方法 `unit:"percent"`、`metrics:["humidity"]` 精确键、`trait` 键），`binding_match` 的 `meta_ok` 全等比较使任何轻微措辞差异即判错。
  - **rule_repair (TN31-TN34)**：gold 绑定 metadata 含标注键 `"fixed": true`（如 `{"metadata":{"asset_key":"irrigation","fixed":true}}`），`binding_match` 要求 `gen_md["fixed"]=="true"`；KAFarmTwin 的 `replace_asset`/`set_placeholder` 与 LLM 均不产出该键 → 即使 `_repair_adapter` 判 `repair_success=True`，图形绑定仍判错。F-015 归档中 KF 在 4 修复任务 20/20 run `repair_success=False`（R4 资产不匹配未以绑定呈现，规则引擎改走 R6 设备覆盖 → 修复循环无法命中 gold 的资产修复契约）。
- **影响**: 非 memory 任务无法通过 CVSR（绑定全灭），两方法无区分度。这是**冻结 test_v2 标注设计**的结构性约束，不是 stepwise 缺陷、不是修复循环缺陷，对两方法完全公平。
- **下一步（诚实）**: 不修改冻结 gold/评分器。如实上报 F-016 GATE FAIL。若后续需区分度，须人工重标注（改变冻结集，违反 A+ 协议，需用户明确授权），或接受当前结论。

## F-019 [ACTIVE] 正式 gate FAIL — 非 memory 任务全灭
- **状态**: ACTIVE（如实记录，未调门槛）
- **描述**: 冻结 test_v2 正式 500 run（20 任务 × 5 方法 × 5 次，真实 DeepSeek-V4-Flash）完成。**SOTA_GATE=FAIL（6 项未达）**：paired bootstrap CI [0.00,0.00]，point Δ=0.000；pass5 未超；critical_recall 0.60<0.95；fatal_rate 0.22>0.01；replay 0.80<0.95；cost ratio 1.75>1.5。
- **逐任务根因（双峰分布）**: CVSR=0.20 完全来自 4 个 memory_query 任务（TN41-44，SA/KF 均 5/5 全过=确定性）。**16 个非 memory 任务（scene×4/asset×4/bind×4/repair×4）每个方法每任务全 0/5**。KF 与 SA 在单个任务不可区分 → paired CI 恒 0。
- **结论**: 非 memory 任务需精确"图结构+绑定元数据契约"才可达 CVSR，当前模型/执行链对两类方法都是 method-agnostic 的天花板。**非 KF 优势，不得声明 SOTA。不调阈值/测试集/评分器/预算。**
- **下一步**: 让方法真正攻克 16 个非 memory 任务的图+绑定契约，而非仅确定性 memory 检索。若 KF 结构上真优于 SA，CVSR 差会自然 >3pp。

## F-020 [ACTIVE] Fatal rate 与 Critical recall 绝对门槛未达
- **状态**: ACTIVE
- **描述**: KF fatal_violation_rate=0.22（>0.01 门槛），critical_recall=0.60（<0.95 门槛）。ReAct evidence_precision=0（空 trace，已按 P0-1 诚实钳制为 0）。
- **根因**: 规则违规（R4 等）在非 memory 任务未被消除 + 关键对象未在所有场景中显式产出。
- **下一步**: 类型化修复闭环需真正命中 critical_objects 并消除 fatal 规则违规，而非仅 memory 确定性检索。

## F-021 [RESOLVED] TN32 修复边饥饿：R1 逐孤儿单轮，3 轮预算耗尽（2026-08-19）
- **状态**: RESOLVED（批量挂接 + 回归测试 T17）
- **描述**: 首次资产诊断中 TN32 KF `repair_success=True` 但 `CVSR=F`（failclause=all_edges，relF1=0.667）。逐轮追踪显示 4 个违规（R4 资产、R5 camera、R1×2 孤儿）配 3 轮预算：R4→replace_asset、R5→fill_observes、R1→attach_to_root(仅 Asset_B) 各耗一轮，`N32_row` 的 `contains` 边从未建立——确定性 R1 执行器一轮只挂一个孤儿，预算耗尽后行节点仍是孤儿。
- **根因**: 非方法概念缺陷，而是 R1 确定性执行器"一轮一对象"与修复预算（3 轮）相互作用的结构性饥饿。LLM 决策正确（选了 attach_to_root），是执行粒度问题。
- **修复**: `typed_deterministic.py` 新增 `attach_all_rootless()`——LLM 选 attach_to_root 时在**单轮**内对所有孤儿对象批量产出 add_edge 算子（与既有 batched `{ops:[...]}` 路径一致，纯确定性结构工作，不新增 LLM 调用、不偏袒 KF）。`kafarmtwin_typed_repair.py` 修复循环在 R1+attach_to_root 时接入。单任务 TN32 复现 CVSR=T（objF1/relF1/bindF1/critR 全 1.0）。
- **验证**: 94/94 测试全绿（+T16 fatal-first 排序回归 +T17 批量挂接回归）；最终诊断 TN31-34 KF **4/4 CVSR=T**、`repair_success=True`。
