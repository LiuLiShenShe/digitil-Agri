# KAFarmTwin 引用映射与参考文献 (v2)

- 源文件: `/data/fj/数字孪生-paper-work/论文/KAFarmTwin_公式Office可编辑版.docx`
- 输出文件: `/data/fj/数字孪生-paper-work/论文/KAFarmTwin_清除旧引文并重排参考文献.docx`
- 参考文献数量: 40
- 实际引用文献数: 40
- 规则: 每处引用 ≤ 3 条文献
- 检索/整理日期: 2026-06-03
- DOI验证: 39/40 通过 Crossref, 1/40 通过 DataCite (arXiv)

## 段落引用映射

- P012 [1-3], [4,5,7], [10-12]
  - `...为复杂系统的状态感知、过程分析和决策支持提供了重要技术路径。在设施农业中，温室生产管理正在从环境级...` → [1-3]
  - `...温室生产管理正在从环境级监测走向对象级、过程化和可追溯管理。传统监控系统通常以温度、湿度、光照和设...` → [4,5,7]
  - `...历史状态能够绑定到具体农业对象，从而支撑对象级查询、异常定位和生产过程复盘。...` → [10-12]
- P013 [6,8,9]
  - `...现有农业数字孪生和三维可视化系统主要强调监测、展示和数据汇聚，场景构建仍高度依赖人工建模、人工拖拽和...` → [6,8,9]
- P014 [13-15]
  - `...然语言需求，并通过工具调用生成对象列表、三维布局和数据绑定。但是，直接使用通用大模型或普通智能体仍...` → [13-15]
- P024 [1,4], [5-7]
  - `...数字孪生研究从制造领域逐步扩展到农业生产过程建模和智能农场管理。在农业场景中，相关工作通常关注传感器数...` → [1,4]
  - `...作通常关注传感器数据汇聚、作物状态监测、农机或温室设备管理以及三维可视化展示。这些研究证明了数字孪生在农业状态感知中...` → [5-7]
- P026 [13,14], [15,22], [15,24,25], [19,20], [16,18]
  - `...工具调用和结果汇总，使模型从单轮文本生成扩展到交互式任务执行。推理-行动框架（ReAct）强调推理与...` → [13,14]
  - `...务执行。推理-行动框架（ReAct）强调推理与行动的交替组织，工具学习框架（Toolformer）表...` → [15,22]
  - `...框架（Toolformer）表明语言模型可以学习调用外部工具，链式思维和树状搜索进一步增强了大模型的...` → [15,24,25]
  - `...，链式思维和树状搜索进一步增强了大模型的问题分解和候选探索能力，多智能体研究则进一步讨论了角色分工、任...` → [19,20]
  - `...候选探索能力，多智能体研究则进一步讨论了角色分工、任务调度和协作执行。对于数字孪生场景构建，智能体可以调用模...` → [16,18]
- P028 [26,27,30], [26,27], [28,29,32], [33-35], [30,31]
  - `...识图谱、本体、规则系统和外部记忆等方式，将符号知识引入神经模型推理过程。RAG方法能够缓解模型知识不足问题，但...` → [26,27,30]
  - `...能够缓解模型知识不足问题，但检索到的文档并不自动成为可执行约束。知识图谱和本体能够显式表示概念、属性和...` → [26,27]
  - `...性和关系，适合描述设施农业中的对象层级、设备控制关系和数据归属关系。其中，农业领域本体库和传感器语义本体为...` → [28,29,32]
  - `...念、观测指标、传感器、执行器和采样过程的规范化表示提供了参考。神经符号融合进一步强调，神经模型可负责...` → [33-35]
  - `...感知、语言理解和候选生成，符号知识可负责结构约束、规则校验和错误修正。本文将这一思想落实到数字孪生对象图构建...` → [30,31]
- P030 [16,17,31]
  - `...释性研究关注模型输出是否具有可追踪证据、可复核过程和明确的适用边界。在设施农业中，植株长势、环境状态、灌溉...` → [16,17,31]
- P032 [13,30,34]
  - `...布局、资产路由、数据绑定和校验，最终输出可加载、可绑定、可校验的对象图。...` → [13,30,34]
- P050 [33,34]
  - `...）、具有关联性状（has_trait）和关联事件（has_event）。...` → [33,34]
- P057 [13,30,34]
  - `...器和智能体执行轨迹5个模块，并将每个模块对应到后续实验指标。...` → [13,30,34]
- P065 [14,18,22]
  - `...、关系方向错误、资产不匹配或绑定缺失时，冲突被路由回相应智能体修正。...` → [14,18,22]
- P077 [36,39,40]
  - `...类型、任务重要性、资产质量和调用成本选择高保真、轻量、程序化或占位资产。...` → [36,39,40]
- P083 [37-39]
  - `...写入对象图；普通缺失设备或背景对象则生成TRELLIS.2类任务或占位模型。因此，资产库不完备会转化为可追踪的补资...` → [37-39]
- P085 [34,35]
  - `...测本体已表明，传感器、观测、采样和执行器可被统一建模为可查询的语义资源。本文将对象o_i的记忆定义为...` → [34,35]
- P091 [34,35]
  - `...据、表型指标、生产事件和智能体操作记录，使历史查询具有明确对象边界。...` → [34,35]
- P098 [21,23,31]
  - `...正10类规则。如表2所示，这些检查点覆盖对象图构建、资产绑定和执行轨迹的关键约束。...` → [21,23,31]
- P106 [17,21,22]
  - `...语义完整的前提下降低。智能体执行轨迹记录每一步的智能体、工具、输入输出、状态和耗时；文件写入、任意HTTP请求、直接数据库...` → [17,21,22]
- P107 [17,21]
  - `...规则、修正建议和执行状态均写入轨迹，便于定位具体智能体和工具调用步骤。...` → [17,21]
- P114 [13,14,39]
  - `...象管理、场景绑定、对象级记忆、资产治理、语义构建和验收聚合接口。...` → [13,14,39]
- P117 [13,14,36]
  - `...的场景输出、端到端验收、可追溯执行记录和多保真资产选择证据。...` → [13,14,36]
- P136 [13,14,19]
  - `...ce。如表4所示，所有方法共享输入约束，差异仅体现在知识是否进入工具化闭环。...` → [13,14,19]
- P143 [19,20,22]
  - `...度（ETF）。对对象、关系或绑定集合X，精确率、召回率和F1值定义为：...` → [19,20,22]
- P148 [17,21,23]
  - `...骤字段；ETF仅统计来自系统工具调用链、带有证据编号或调用编号的执行式轨迹。Direct-LLM或普通智能体生成的...` → [17,21,23]
- P190 [1,13,30]
  - `...精确率/召回率/F1值、规则冲突率，以及声明式轨迹与执行式轨迹的双层可追溯指标。公平基线结果表明，在统一模型和统一知识...` → [1,13,30]

## 参考文献

[1] Semeraro C, Lezoche M, Panetto H, et al. Digital twin paradigm: a systematic literature review[J]. Computers in Industry, 2021, 130: 103469. DOI: 10.1016/j.compind.2021.103469.
[2] Botin-Sanabria D M, Mihaita A S, Peimbert-Garcia R E, et al. Digital twin technology challenges and applications: a comprehensive review[J]. Remote Sensing, 2022, 14(6): 1335. DOI: 10.3390/rs14061335.
[3] Dihan M S, Akash A I, Tasneem Z, et al. Digital twin: data exploration, architecture, implementation and future[J]. Heliyon, 2024, 10(5): e26503. DOI: 10.1016/j.heliyon.2024.e26503.
[4] Pylianidis C, Osinga S, Athanasiadis I N. Introducing digital twins to agriculture[J]. Computers and Electronics in Agriculture, 2021, 184: 105942. DOI: 10.1016/j.compag.2020.105942.
[5] Verdouw C, Tekinerdogan B, Beulens A, et al. Digital twins in smart farming[J]. Agricultural Systems, 2021, 189: 103046. DOI: 10.1016/j.agsy.2020.103046.
[6] Nasirahmadi A, Hensel O. Toward the next generation of digitalization in agriculture based on digital twin paradigm[J]. Sensors, 2022, 22(2): 498. DOI: 10.3390/s22020498.
[7] Cesco S, Sambo P, Borin M, et al. Smart agriculture and digital twins: applications and challenges in a vision of sustainability[J]. European Journal of Agronomy, 2023, 146: 126809. DOI: 10.1016/j.eja.2023.126809.
[8] Peladarinos N, Piromalis D, Cheimaras V, et al. Enhancing smart agriculture by implementing digital twins: a comprehensive review[J]. Sensors, 2023, 23(16): 7128. DOI: 10.3390/s23167128.
[9] Escriva-Gelonch M, Liang Shu, van Schalkwyk P, et al. Digital twins in agriculture: orchestration and applications[J]. Journal of Agricultural and Food Chemistry, 2024, 72(19): 10737-10752. DOI: 10.1021/acs.jafc.4c01934.
[10] Quy V K, Hau N V, Anh D V, et al. IoT-enabled smart agriculture: architecture, applications, and challenges[J]. Applied Sciences, 2022, 12(7): 3396. DOI: 10.3390/app12073396.
[11] Finger R. Digital innovations for sustainable and resilient agricultural systems[J]. European Review of Agricultural Economics, 2023, 50(4): 1277-1309. DOI: 10.1093/erae/jbad021.
[12] Dara R, Hazrati Fard S M, Kaur J. Recommendations for ethical and responsible use of artificial intelligence in digital agriculture[J]. Frontiers in Artificial Intelligence, 2022, 5: 884192. DOI: 10.3389/frai.2022.884192.
[13] Wang Lei, Ma Chen, Feng Xueyang, et al. A survey on large language model based autonomous agents[J]. Frontiers of Computer Science, 2024, 18(6): 186345. DOI: 10.1007/s11704-024-40231-1.
[14] Li Xinyi, Wang Sai, Zeng Siqi, et al. A survey on LLM-based multi-agent systems: workflow, infrastructure, and challenges[J]. Vicinagearth, 2024, 1(1): 9. DOI: 10.1007/s44336-024-00009-2.
[15] Schick T, Dwivedi-Yu J, Dessi R, et al. Toolformer: language models can teach themselves to use tools[C]//Advances in Neural Information Processing Systems 36. La Jolla: Neural Information Processing Systems Foundation, 2023: 68539-68551. DOI: 10.52202/075280-2997.
[16] Park J S, O'Brien J, Cai C J, et al. Generative agents: interactive simulacra of human behavior[C]//Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology. New York: Association for Computing Machinery, 2023: 1-22. DOI: 10.1145/3586183.3606763.
[17] Shinn N, Cassano F, Gopinath A, et al. Reflexion: language agents with verbal reinforcement learning[C]//Advances in Neural Information Processing Systems 36. La Jolla: Neural Information Processing Systems Foundation, 2023: 8634-8652. DOI: 10.52202/075280-0377.
[18] Li Guohao, Hammoud H, Itani H, et al. CAMEL: communicative agents for "mind" exploration of large language model society[C]//Advances in Neural Information Processing Systems 36. La Jolla: Neural Information Processing Systems Foundation, 2023: 51991-52008. DOI: 10.52202/075280-2264.
[19] Wei Jason, Wang Xuezhi, Schuurmans D, et al. Chain-of-thought prompting elicits reasoning in large language models[C]//Advances in Neural Information Processing Systems 35. La Jolla: Neural Information Processing Systems Foundation, 2022: 24824-24837. DOI: 10.52202/068431-1800.
[20] Yao Shunyu, Yu Dian, Zhao Jeffrey, et al. Tree of thoughts: deliberate problem solving with large language models[C]//Advances in Neural Information Processing Systems 36. La Jolla: Neural Information Processing Systems Foundation, 2023: 11809-11822. DOI: 10.52202/075280-0517.
[21] Zhan Qiusi, Liang Zhixiang, Ying Zifan, et al. InjecAgent: benchmarking indirect prompt injections in tool-integrated large language model agents[C]//Findings of the Association for Computational Linguistics ACL 2024. Stroudsburg: Association for Computational Linguistics, 2024: 10471-10506. DOI: 10.18653/v1/2024.findings-acl.624.
[22] Zhu Feiyu, Simmons R. Bootstrapping cognitive agents with a large language model[C]//Proceedings of the AAAI Conference on Artificial Intelligence. Palo Alto: Association for the Advancement of Artificial Intelligence, 2024: 655-663. DOI: 10.1609/aaai.v38i1.27822.
[23] Zhang Xinyu, Xu Huiyu, Ba Zhongjie, et al. PrivacyAsst: safeguarding user privacy in tool-using large language model agents[J]. IEEE Transactions on Dependable and Secure Computing, 2024, 21(6): 5242-5258. DOI: 10.1109/TDSC.2024.3372777.
[24] Bran A M, Cox S, Schilter O, et al. Augmenting large language models with chemistry tools[J]. Nature Machine Intelligence, 2024, 6(5): 525-535. DOI: 10.1038/s42256-024-00832-8.
[25] Jia Jingyi, Li Qinbin. AutoTool: efficient tool selection for large language model agents[C]//Proceedings of the AAAI Conference on Artificial Intelligence. Palo Alto: Association for the Advancement of Artificial Intelligence, 2026: 31265-31273. DOI: 10.1609/aaai.v40i37.40389.
[26] Gao Yunfan, Xiong Yun, Gao Xinyu, et al. Retrieval-augmented generation for large language models: a survey[EB/OL]. arXiv:2312.10997, 2023[2026-06-03]. https://arxiv.org/abs/2312.10997. DOI: 10.48550/arXiv.2312.10997.
[27] Procko T T, Ochoa O. Graph retrieval-augmented generation for large language models: a survey[C]//2024 Conference on AI, Science, Engineering, and Technology. Piscataway: IEEE, 2024: 166-169. DOI: 10.1109/AIxSET62544.2024.00030.
[28] Ibrahim N, Aboulela S, Ibrahim A, et al. A survey on augmenting knowledge graphs (KGs) with large language models (LLMs): models, evaluation metrics, benchmarks, and challenges[J]. Discover Artificial Intelligence, 2024, 4(1): 76. DOI: 10.1007/s44163-024-00175-8.
[29] Chen Guanyu, Song Tao, Wang Quanyu, et al. Knowledge graph and large language model integration with focus on educational applications: a survey[J]. Neurocomputing, 2025, 654: 131230. DOI: 10.1016/j.neucom.2025.131230.
[30] d'Avila Garcez A, Lamb L C. Neurosymbolic AI: the 3rd wave[J]. Artificial Intelligence Review, 2023, 56(11): 12387-12406. DOI: 10.1007/s10462-023-10448-w.
[31] Longo L, Brcic M, Cabitza F, et al. Explainable artificial intelligence (XAI) 2.0: a manifesto of open challenges and interdisciplinary research directions[J]. Information Fusion, 2024, 106: 102301. DOI: 10.1016/j.inffus.2024.102301.
[32] Subagdja B, Shanthoshigaa D, Wang Zhaoxia, et al. Machine learning for refining knowledge graphs: a survey[J]. ACM Computing Surveys, 2024, 56(6): 1-38. DOI: 10.1145/3640313.
[33] Amdouni E, Bouazzouni S, Jonquet C. O'FAIRe: ontology FAIRness evaluator in the AgroPortal semantic resource repository[C]//Lecture Notes in Computer Science. Cham: Springer International Publishing, 2022: 89-94. DOI: 10.1007/978-3-031-11609-4_17.
[34] Chandra R, Agarwal S, Singh N. Semantic sensor network ontology based decision support system for forest fire management[J]. Ecological Informatics, 2022, 72: 101821. DOI: 10.1016/j.ecoinf.2022.101821.
[35] Milli M, Milli M, Lakestani S, et al. Semantic-based anomaly detection in laboratory environments using SOSA/SSN sensor ontology frameworks[J]. Pamukkale University Journal of Engineering Sciences, 2023, 29(4): 357-369. DOI: 10.5505/pajes.2022.95595.
[36] Lin Chen-Hsuan, Gao Jun, Tang Luming, et al. Magic3D: high-resolution text-to-3D content creation[C]//2023 IEEE/CVF Conference on Computer Vision and Pattern Recognition. Piscataway: IEEE, 2023: 300-309. DOI: 10.1109/CVPR52729.2023.00037.
[37] Liu Qihao, Zhang Yi, Bai Song, et al. DIRECT-3D: learning direct text-to-3D generation on massive noisy 3D data[C]//2024 IEEE/CVF Conference on Computer Vision and Pattern Recognition. Piscataway: IEEE, 2024: 6881-6891. DOI: 10.1109/CVPR52733.2024.00657.
[38] Tsalicoglou C, Manhardt F, Tonioni A, et al. TextMesh: generation of realistic 3D meshes from text prompts[C]//2024 International Conference on 3D Vision. Piscataway: IEEE, 2024: 1554-1563. DOI: 10.1109/3DV62453.2024.00154.
[39] Yang Yue, Sun Fan-Yun, Weihs L, et al. Holodeck: language guided generation of 3D embodied AI environments[C]//2024 IEEE/CVF Conference on Computer Vision and Pattern Recognition. Piscataway: IEEE, 2024: 16277-16287. DOI: 10.1109/CVPR52733.2024.01536.
[40] Xiang Jianfeng, Lv Zelong, Xu Sicheng, et al. Structured 3D latents for scalable and versatile 3D generation[C]//2025 IEEE/CVF Conference on Computer Vision and Pattern Recognition. Piscataway: IEEE, 2025: 21469-21480. DOI: 10.1109/CVPR52734.2025.02000.
