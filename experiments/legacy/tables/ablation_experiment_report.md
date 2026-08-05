# 知识增强模块消融实验结果

- 任务集：`experiments/tasks/main_experiment_tasks.json` 的 30 条任务。
- 实验类型：反事实模块消融实验。
- 数据来源：为避免不同大模型调用随机性对消融结果造成干扰，复用主实验中 `Ours` 的结构化输出，并按配置脚本化关闭单个知识增强模块后重新执行评分流程。
- 配置文件：`experiments/config/ablation_variants.json`。
- AR 仅在资产路由相关任务上统计，主要衡量 F2DMAS 高保真模型、轻量 GLB、程序化模型、缺失资产占位和 TRELLIS.2 任务的选择准确性。
- VR 反映最终场景结果中的规则冲突比例，Validator 冲突率反映规则校验模块内部检查项的冲突比例。
- 由于各消融版本复用相同任务集合和基础对象输出，OC 主要反映对象实例展开程度，不作为本表的主要分析指标。

| 版本 | OC ↑ | RA ↑ | AR ↑ | VR ↓ | TC ↑ | 层级错误率 ↓ | Validator 冲突率 ↓ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ours | 0.524 | 0.815 | 0.597 | 0.007 | 0.993 | 0.000 | 0.008 |
| Ours w/o Ontology | 0.524 | 0.473 | 0.597 | 0.108 | 0.793 | 1.000 | 0.133 |
| Ours w/o Memory | 0.524 | 0.721 | 0.571 | 0.162 | 0.793 | 0.000 | 0.186 |
| Ours w/o Asset Router | 0.524 | 0.731 | 0.000 | 0.108 | 0.793 | 0.000 | 0.136 |
| Ours w/o Validator | 0.524 | 0.815 | 0.597 | 0.628 | 0.800 | 0.154 | 0.775 |

## 消融配置

- `Ours`：Full KAFarmTwin pipeline with ontology, memory, asset routing, validator, and trace enabled.
- `Ours w/o Ontology`：Disable agricultural object ontology constraints and flatten hierarchy relations.
- `Ours w/o Memory`：Disable object-level memory and history/event query evidence.
- `Ours w/o Asset Router`：Disable fidelity routing, missing-asset task generation, and asset routing trace evidence.
- `Ours w/o Validator`：Disable layout/rule validation and leave rule-repair tasks unresolved.

## 表注

消融实验基于 30 条设施农业数字孪生任务，对完整方法中的农业对象本体、对象级记忆、多保真资产路由和规则校验模块进行逐一关闭。AR 仅在资产路由相关任务上统计；VR、层级错误率和 Validator 冲突率越低越好，其余指标越高越好。由于各消融版本复用相同任务集合和基础对象输出，OC 主要反映对象实例展开程度，不作为本表的主要分析指标。

## 关键观察

- 由于消融实验复用相同基础对象输出，OC 在不同版本中保持一致，因此主要分析 RA、AR、VR、TC、层级错误率和 Validator 冲突率。
- 去掉本体后，`contains`、`belongs_to`、`has_instance` 等层级关系被压平，层级错误率显著升高。
- 去掉 Validator 后，规则修正类任务中的冲突不再被闭环修复，整体规则冲突率明显升高。
- 去掉 Asset Router 后，资产绑定、缺失资产占位和 TRELLIS.2 任务证据被移除，资产路由准确率降为最低。
- 去掉 Memory 后，数据绑定和历史查询任务中的 R8 记忆查询约束受影响，绑定与 Trace 指标下降。

## 图 9

建议图名：不同消融版本的结构可靠性对比。

图注：图中对比了完整方法与不同消融版本在关系正确率、资产路由准确率、规则通过率和 Trace 完整率上的表现，其中规则通过率由 `1 - VR` 表示。结果显示，去除 Ontology 后关系正确率明显下降，去除 Asset Router 后资产路由准确率降为 0，去除 Validator 后规则通过率显著降低，说明各知识增强模块分别对应不同的可靠性来源。

图文件：`experiments/analysis/ablation_experiment_structure_reliability.png` 和 `experiments/analysis/ablation_experiment_structure_reliability.pdf`。
