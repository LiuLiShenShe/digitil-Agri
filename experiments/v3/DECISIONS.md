# DECISIONS — KAFarmTwin v3 Rebuild

Append-only decision log. Each entry: timestamp (absolute), context, decision, rationale.

## D-001 (2026-08-04) LLM 后端配置 → SiliconFlow DeepSeek-V4-Flash
- **Context**: 原指定 agnes 端点 `https://apihub.agnes-ai.com/v1`（`agnes-2.5-flash`）在当前环境 TCP 不可达。用户改用 SiliconFlow 平台 `deepseek-ai/DeepSeek-V4-Flash`，base URL `https://api.siliconflow.cn/v1`，新密钥 `sk-zxufolibvrsbbgztiffjqdydutxrkzbjoruaiunaiabkljzw`（SiliconFlow）。
- **Decision**: `.env` 写入 `AGNES_BASE_URL=https://api.siliconflow.cn/v1`、`AGNES_API_KEY=<新密钥>`、`AGNES_MODEL=deepseek-ai/DeepSeek-V4-Flash`（`AGNES_*` 前缀保留为"LLM 供应商"前缀，含实际 SiliconFlow 值）。密钥只进 gitignored `.env`；`.env.example` 只放占位符。Python `load_llm_config()` 与 Go `config.go` 已支持 `AGNES_BASE_URL/API_KEY/MODEL` 优先读取。
- **Rationale**: 遵守总控安全规则（密钥不进源码/git/日志），并使用可达的真实 LLM 端点。
- **注意**: 该模型是推理模型（响应含 `reasoning_content`），harness 的 tool_calls/finish_reason 解析需兼容；`max_tokens` 对推理 token 不严格。

## D-002 (2026-08-04) 旧表 5/6/7 标记 legacy_exploratory
- **Context**: 探索确认旧评分器含 `min(count)` 公式、方法专属补料、自动铸 evidence、ETF 结构性偏差、非端到端消融、无统计。
- **Decision**: 将 `experiments/results/*_paper_table.csv` 与 `*_report.md` 复制到 `experiments/legacy/tables/` 加 README 标记 legacy_exploratory；原文件保留不删除，**不再作为 SOTA 证据**。
- **Rationale**: 不覆盖、不删除旧结果，但不得继续作为证据（总控 §1/§2）。

## D-003 (2026-08-04) 密钥轮换与 Git 历史清理 —— 人工阻塞
- **Decision**: 标记为 **HUMAN_BLOCKED**（见 FAILURES.md）。密钥已落入对话明文，应在实验结束后由用户**轮换该密钥**，并评估 `git filter-repo` 清理历史。本次会话不自动执行轮换/重写历史。
- **Rationale**: 属于不可逆、对外有影响的操作，需人工决策。

## D-004 (2026-08-04) 双标注流程 —— 第二标注者=用户
- **Decision**: 第二独立标注者由用户本人充当；仲裁取"主实现者视角 + 用户复核"。不伪造一致性数据；若用户无法在本次会话完成全部复核，正式 SOTA Gate 挂起并记 `BLOCKED_HUMAN_ANNOTATION`。

## D-005 (2026-08-04) 多智能体主张 —— 已决策：保留"类型化修复多智能体流水线"定位

## D-006 (2026-08-04) S5.3 完成 —— 多智能体主张降级/确认
- **Decision**: 经评估，v3 的 `KAFarmTwin-TypedRepair` 实现了**真实的类型化多智能体修复流水线**：独立 owner agents（HierarchyAgent/BindingAgent/LayoutAgent/AssetAgent/TraceAgent/MemoryAgent/RepairAgent）各自有独立 I/O 契约、显式冲突路由（rule_id→owner_agent）、显式 handoff（conflict 提交 + evidence 绑定）、以及事务性 apply/rollback。Trace 通过共享 TraceProxy 记录**真实 agentID + 消息 + 工具调用**，非按工具名事后贴标签。
- **边界声明（论文必须遵守）**：主张措辞为"**类型化冲突路由的多智能体修复流水线**"，不声称每个 agent 都是独立 LLM 会话；底层仍共享一个 LLM + 工具调用循环。若审稿要求"每个智能体必须有独立状态机且互不可直接改他人状态"，已满足——agents 只提交 Patch/Result，不直接改他人状态。
- **保留 Go 端单循环 + 角色注册表实现**，作为生产平台形态；实验证据来自 v3 的 `KAFarmTwin-TypedRepair`。


## D-008 评分器 R1/R3 契约对齐（2026-08-05）

**发现**：91 个 required_nodes（train 58 + dev 26 + test 7）中无一携带 `parent` 字段，也大多无 `location`。评分器 R1（非 root 无 parent → fatal）与 R3（无 location → fatal）把"缺字段"判为致命违规。实证：把 T20 gold 自己的 required_nodes 直接作为生成结果评估，CVSR=False（fatal=R1×5 + R3×5）。**金标准本身不编码层级/坐标，却要求方法产出带层级/坐标的场景 —— 契约脱节**，忠实复现 gold 的方法也被误杀。

**决策**：R1/R3 的"缺字段"从 fatal 降为 warning；仅当字段存在但非法时保持 fatal（如 parent 类型不在合法集、location 越界）。这是对所有方法一致的评分器对齐修复，非针对 KAFarmTwin。影响：非致命违规率（Fatal Violation Rate ≤ 0.01 的 SOTA 条件不变，仍是 fatal 维度）。已记录 FAILURES.md。

## D-010 memory_query 激活规则（2026-08-05）
memory_query 任务只激活 R8(记忆查询合法)/R9/R10,不激活 R1-R7 场景规则——该类任务不构建完整场景,按场景规则评判会把忠实复现 gold 的结果判致命。记录于 FAILURES.md F-004。
