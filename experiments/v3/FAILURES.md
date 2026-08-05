# FAILURES — KAFarmTwin v3 Rebuild

记录失败/阻塞项。每项：ID、状态（ACTIVE / RESOLVED / HUMAN_BLOCKED）、描述、原因、下一步。

## F-001 [HUMAN_BLOCKED] 密钥轮换
- **状态**: HUMAN_BLOCKED（人工操作）
- **描述**: LLM API 密钥 `sk-ssPAvndcU73t2qTcYNUA3M5Y62a6BYu0PjJHPg5RdYJiMdSY` 以明文出现在会话中，且已写入本地 `.env`（gitignored，不提交）。
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
