# 基于人机协作的多智能体科学假设生成

## Multi-Agent Scientific Hypothesis Generation Based on Human-Machine Collaboration

---

### Metadata

| Field | Value |
|-------|-------|
| **Authors (CN)** | 陈子阳, 赵翔, 赵润豪, 倪子淇, 叶益聪 |
| **Authors (EN)** | Chen Ziyang, Zhao Xiang, Zhao Runhao, Ni Ziqi, Ye Yicong |
| **Affiliations (CN)** | 国防科技大学 大数据与决策实验室 (长沙 410003); 国防科技大学 空天科学学院 (长沙 410003) |
| **Affiliations (EN)** | Laboratory for Big Data and Decision, National University of Defense Technology, Changsha 410003; College of Aerospace Science and Engineering, National University of Defense Technology, Changsha 410003 |
| **Journal (CN)** | 计算机研究与发展 |
| **Journal (EN)** | Journal of Computer Research and Development |
| **Volume/Issue** | Vol. 62, No. 7, pp. 1639–1652, 2025 |
| **DOI** | 10.7544/issn1000-1239.202440552 |
| **CSTR** | 32373.14.issn1000-1239.202440552 |
| **中图法分类号** | TP391 |
| **Received** | 2024-06-20; Revised: 2024-12-31 |
| **Funding** | 国家自然科学基金 (U23A20296, 62272469); 湖南省科技创新计划 (2023RC1007) |
| **Corresponding Author** | 赵翔 (xiangzhao@nudt.edu.cn) |
| **Section Header** | 本期推荐 (Recommended in This Issue) |

---

### Page/Section Index

| Section | Pages | Block IDs |
|---------|-------|-----------|
| English Abstract | p.1 (1639) | S001–S003 |
| 中文摘要 (Chinese Abstract) | p.1 (1639) | S004–S007 |
| 引言 (Introduction) | pp.1–3 (1639–1641) | S008–S027 |
| 1. 相关工作 (Related Work) | pp.2–3 (1641–1642) | S028–S055 |
| 1.1 科学假设生成 | p.2 (1642) | S031–S038 |
| 1.2 知识增强的LLMs | pp.2–3 (1642) | S039–S048 |
| 1.3 人机协作的智能系统 | p.3 (1642–1643) | S049–S055 |
| 2. 人机协作的多智能体辩论框架 (HILMA Framework) | pp.3–7 (1643–1645) | S056–S100 |
| 2.1 基于引文网络的文献系统化检索增强方法 | pp.3–5 (1643–1644) | S057–S076 |
| 2.1.1 自顶向下的子图引文网络构建 | pp.3–4 (1643) | S059–S069 |
| 2.1.2 自底向上的文献网络综述生成 | p.4 (1644) | S070–S076 |
| 2.2 知识增强的研究想法生成 | pp.4–5 (1644) | S077–S086 |
| 2.3 人机协作的多智能体辩论迭代 | pp.5–7 (1644–1645) | S087–S097 |
| 2.4 人机协作科学假设生成平台 | p.7 (1645) | S098–S100 |
| 3. 实验 (Experiments) | pp.7–11 (1645–1648) | S101–S166 |
| 3.1 实验设置 | p.7 (1645) | S102–S106 |
| 3.2 基线模型 | pp.7–8 (1645) | S107–S115 |
| 3.3 评估设置 | pp.8–9 (1645–1646) | S116–S130 |
| 3.4 实验结果与分析 | pp.9–11 (1646–1647) | S131–S146 |
| 3.5 多步辩论评估 | p.11 (1647) | S147–S154 |
| 3.6 不同基座模型评估 | pp.11–12 (1647–1648) | S155–S159 |
| 3.7 人类评估结果 | p.12 (1648) | S160–S166 |
| 3.8 案例分析 | pp.12–13 (1648–1649) | S167–S169 |
| 4. 结论 (Conclusion) | pp.13–14 (1648–1649) | S170–S179 |
| 参考文献 (References) | pp.14–15 (1650–1651) | R001–R058 |
| 作者简介 (Author Biographies) | pp.14–15 (1651–1652) | B001–B005 |

---

### Figures Index

| Figure | Description | Source |
|--------|-------------|--------|
| Fig. 1 | HILMA Framework overview | p.1 C001 |
| Fig. 2 | Systematic literature retrieval enhancement process based on citation network | p.3 C002 |
| Fig. 3 | Human-machine collaboration hypothesis generation platform | p.7 C003 |
| Fig. 4 | The constructed artificial online evaluation platform | p.8 C004 |
| Fig. 5 | Comparison of initial hypotheses and hypotheses after human-machine collaboration | p.9 C005 |
| Fig. 6 | Impact of subgraph citation network introduction on generation quality | p.11 C006 |
| Fig. 7 | Impact of iteration count on human-machine collaboration | p.11 C007 |
| Fig. 8 | Heatmap of model win rates based on human evaluation | p.12 C008 |

### Tables Index

| Table | Description | Source |
|-------|-------------|--------|
| Table 1 | 5-Point Likert Scale Used in Model Evaluation | p.8 C009 |
| Table 2 | Comparison of Different Baselines | p.9 C010 |
| Table 3 | Comparison of Different Large Language Models | p.11 C011 |
| Table 4 | Cases of Scientific Hypothesis Generation Taking "Silicon Nitride Ceramics" as the Research Topic | p.12 C012 |

---

## English Abstract

<a id="S001"></a>
**Source:** p.1 (1639) S001

**原文 (Original Chinese):** N/A (English original)

**English:** With the explosive growth of scientific literature and the continuous deepening of research fields, researchers face significant information processing challenges when attempting to formulate novel scientific hypotheses. Although large language models (LLMs) possess considerable potential for data processing and knowledge integration, they remain limited in their ability to generate original and insightful scientific hypotheses. Existing research predominantly emphasizes utilizing LLMs to expedite and refine established theories and technologies, often overlooking the initial stages of scientific inquiry where novel hypotheses are proposed and new theories are developed -- a stage vital to scientific advancement. This study, grounded in the principles of divergent and convergent thinking from the theory of structured intelligence, proposes an innovative human-in-the-loop multi-agent framework (HILMA) for the reliable generation of scientific hypotheses. HILMA framework incorporates a real-time, systematic knowledge retrieval enhancement mechanism, dynamically integrating the latest research advancements to construct citation network subgraphs, providing LLMs with comprehensive and up-to-date scientific knowledge surveys. Additionally, the framework enhances hypothesis generation through a multi-agent argumentation approach that simulates the scientific peer review process, while also leveraging the intuition and expertise of human experts to further refine and diversify the generated hypotheses. A series of human-machine evaluations has shown that this method demonstrates significant advantages over existing baselines in generating high-quality scientific hypotheses and holds promise as a key facilitator for driving technological innovation.

<a id="S002"></a>
**Source:** p.1 (1639) S002

**原文 (Original Chinese):** N/A (English original)

**English:** **Key words:** large language models (LLMs); scientific hypothesis generation; multi-agent; human-machine collaboration; theory of structural intelligence

---

## 中文摘要 (Chinese Abstract)

<a id="S003"></a>
**Source:** p.1 (1639) S003

**原文 (Original Chinese):** 随着科学文献数量的快速增长和研究领域的不断深化，科研人员在提出创新性科学假设时面临巨大的信息处理挑战. 尽管大语言模型（large language models, LLMs）在数据处理和知识整合方面展现出巨大潜力，但它们在生成具有创新性和深度的科学假设方面仍存在许多不足. 目前的研究主要集中在如何利用 LLMs 加速已有理论和技术的推进和完善，而忽视了科学研究从无到有的初始阶段，这一阶段涉及新假设的提出和新理论的构建，是科学进步的关键. 基于结构智力理论中的发散思维和收敛思维，提出了一种创新的人机协作多智能体框架（human-in-the-loop multi-agent framework, HILMA），以实现可靠的初始科学假设生成. 该框架结合实时系统化的知识检索增强机制，通过动态整合最新科研进展，构建引文网络子图，为 LLMs 提供前沿和完备的科研知识综述. 同时，通过多智能体辩论方法模拟科学同行评审过程，并且结合人类专家的直觉和专业知识，进一步优化和精炼生成的假设，增强科学假设的多样性和论证深度. 一系列人机评估表明，与现有基线相比，HILMA 在生成高质量科学假设方面展现出显著优势，有望成为推动科技创新的关键工具.

**English:** With the rapid growth of scientific literature and the continuous deepening of research fields, researchers face enormous information processing challenges when proposing innovative scientific hypotheses. Although large language models (LLMs) have demonstrated great potential in data processing and knowledge integration, they still exhibit many deficiencies in generating scientifically innovative and deep hypotheses. Current research primarily focuses on how to use LLMs to accelerate the advancement and refinement of existing theories and technologies, while overlooking the initial "zero-to-one" stage of scientific research -- the stage involving the proposal of new hypotheses and the construction of new theories, which is key to scientific progress. Grounded in the divergent and convergent thinking principles from the theory of structural intelligence, this paper proposes an innovative human-in-the-loop multi-agent framework (HILMA) to achieve reliable initial scientific hypothesis generation. The framework incorporates a real-time, systematic knowledge retrieval enhancement mechanism, dynamically integrating the latest research advances to construct citation network subgraphs, thereby providing LLMs with cutting-edge and comprehensive scientific knowledge surveys. Simultaneously, through a multi-agent debate approach that simulates the scientific peer review process, combined with the intuition and expertise of human experts, the framework further optimizes and refines the generated hypotheses, enhancing their diversity and depth of argumentation. A series of human-machine evaluations demonstrates that HILMA exhibits significant advantages over existing baselines in generating high-quality scientific hypotheses and holds promise as a key tool for driving technological innovation.

<a id="S004"></a>
**Source:** p.1 (1639) S004

**原文 (Original Chinese):** 关键词 大语言模型；科学假设生成；多智能体；人机协作；结构智力理论

**English:** **Keywords:** large language models; scientific hypothesis generation; multi-agent; human-machine collaboration; theory of structural intelligence

---

## 引言 (Introduction)

<a id="S005"></a>
**Source:** pp.1–2 (1639–1640) S005

**原文 (Original Chinese):** 科学研究在推动社会发展和技术进步中起着至关重要的作用. 科学假设的生成是科研过程中的一个基础环节，它为实验设计和理论探索提供了方向. 然而，随着科学文献数量的急剧增加和研究领域的不断深化，研究人员在提出科学假设时面临着巨大的挑战. 一方面，研究人员需要从大量的文献中提取有价值的信息，这是一个耗时且劳力密集的过程 [1]；另一方面，创新的科学假设往往需要跨学科的知识和深入的洞察力 [2]，而这些难以通过传统方法迅速实现.

**English:** Scientific research plays a vital role in driving social development and technological progress. The generation of scientific hypotheses is a fundamental part of the research process, providing direction for experimental design and theoretical exploration. However, with the explosive growth of scientific literature and the continuous deepening of research fields, researchers face enormous challenges when proposing scientific hypotheses. On the one hand, researchers need to extract valuable information from vast amounts of literature, a time-consuming and labor-intensive process [1]; on the other hand, innovative scientific hypotheses often require cross-disciplinary knowledge and deep insight [2], which are difficult to achieve rapidly through traditional methods.

<a id="S006"></a>
**Source:** p.2 (1640) S006

**原文 (Original Chinese):** 在这种背景下，人工智能（artificial intelligence, AI），尤其是大语言模型（large language models, LLMs），因其强大的数据处理能力和信息整合能力，成为科学研究中的一种重要工具. LLMs 通过在大量的文本数据上进行训练，能够理解和生成复杂的文本信息，表现出在不同任务上处理和生成知识的能力 [3]. 例如，GPT-4 等模型不仅在文本生成上表现出色，还在诸如编程 [4]、法律 [5] 和生物医药 [6] 等专业领域展示了其应用潜力. 在科学研究领域，LLMs 已被用于各种任务，包括药物发现、医疗诊断和材料性能预测 [7]，为研究人员提供了强大的支持，特别是在快速浏览和整理大量科学文献时显示出其独特优势. 例如，LLMs 能够自动识别文献中的关键概念和关联，从而加速文献综述的编写过程.

**English:** Against this backdrop, artificial intelligence (AI), especially large language models (LLMs), has become an important tool in scientific research due to their powerful data processing and information integration capabilities. Trained on vast amounts of text data, LLMs can understand and generate complex textual information, demonstrating the ability to process and generate knowledge across different tasks [3]. For instance, models such as GPT-4 not only excel in text generation but have also shown application potential in specialized domains such as programming [4], law [5], and biomedicine [6]. In the scientific research domain, LLMs have been applied to various tasks including drug discovery, medical diagnosis, and material property prediction [7], providing researchers with powerful support, particularly demonstrating unique advantages in rapidly browsing and organizing large volumes of scientific literature. For example, LLMs can automatically identify key concepts and associations in the literature, thereby accelerating the writing of literature reviews.

<a id="S007"></a>
**Source:** p.2 (1640) S007

**原文 (Original Chinese):** 在当前的科学研究和工程实践中，大部分研究关注于如何使用 LLMs 将已有的理论或技术从初步阶段快速推进到成熟阶段 [8]，以此提升科学研究的效率，即"1~100"的过程. 这包括一些过程繁杂但对创新要求较低的任务，如自动化文献总结、科学文章撰写以及代码实现等. 尽管这一阶段的研究对技术发展和应用普及至关重要，但它依赖于已有的框架和理论基础. 然而，科学探索从无到有的初始阶段，即"0~1"的过程，在许多情况下被忽视. 这一阶段涉及到新假设的提出、初步概念的形成以及新理论的构建. 正是这些活动定义了科学研究的前沿性和创新性，提出好的科学假设是科学进步的启动器和基石 [9].

**English:** In current scientific research and engineering practice, most studies focus on how to use LLMs to rapidly advance existing theories or technologies from initial stages to maturity [8], thereby improving the efficiency of scientific research -- the "1 to 100" process. This includes tasks that are complex in procedure but require relatively low creativity, such as automated literature summarization, scientific article writing, and code implementation. Although research at this stage is crucial for technological development and application popularization, it relies on existing frameworks and theoretical foundations. However, the initial "zero-to-one" stage of scientific exploration -- where new hypotheses are proposed, preliminary concepts are formed, and new theories are constructed -- is often overlooked. It is precisely these activities that define the frontier nature and innovativeness of scientific research; proposing good scientific hypotheses is the initiator and cornerstone of scientific progress [9].

<a id="S008"></a>
**Source:** p.2 (1640) S008

**原文 (Original Chinese):** 科学假设生成指的是在科学研究的前期阶段，系统地整合现有知识并探索新的理论路径，以提出具有创新性的主张与思路的过程. 尽管 LLMs 在科学研究中提供了强大的支持，它们在科学假设生成的应用上还是存在明显的不足和局限. 首先，LLMs 依赖于大量预训练数据，这些数据无法及时反映科学的最新进展，而学术界的知识更新非常迅速，尤其是在如计算机、生物、材料等快速发展的领域，导致模型在生成假设时依赖于过时或不完整的信息 [10]，无法站在科学前沿的"巨人肩膀"上进行有效创新. 其次，虽然 LLMs 能生成看似复杂的科学内容，但这些内容在科学的准确性和深度上显得不足，缺乏真正的创新性和深度，倾向于重复训练数据中的模式，而不是提出创新的科学理论或方法 [11]. 这些挑战主要源于 LLMs 的固有局限性和科学研究的复杂需求. 这也表明，尽管 LLMs 为科学假设的生成提供了新的可能，但要实现其在科学研究中的有效应用，以及生成具备研究深度与创新性的假设，仍需深入探索和改进.

**English:** Scientific hypothesis generation refers to the process, during the early stages of scientific research, of systematically integrating existing knowledge and exploring new theoretical pathways to propose innovative assertions and ideas. Although LLMs provide powerful support in scientific research, they still exhibit clear deficiencies and limitations in their application to scientific hypothesis generation. First, LLMs rely on large amounts of pre-training data that cannot reflect the latest scientific advances in a timely manner, while knowledge in academia updates very rapidly, especially in fast-developing fields such as computer science, biology, and materials science, causing models to generate hypotheses based on outdated or incomplete information [10] and unable to stand on the "shoulders of giants" at the scientific frontier for effective innovation. Second, although LLMs can generate seemingly complex scientific content, such content falls short in scientific accuracy and depth, lacking genuine innovativeness and depth, tending to repeat patterns from training data rather than proposing innovative scientific theories or methods [11]. These challenges primarily stem from the inherent limitations of LLMs and the complex demands of scientific research. This also indicates that although LLMs offer new possibilities for scientific hypothesis generation, achieving their effective application in scientific research, and generating hypotheses with research depth and innovativeness, still requires in-depth exploration and improvement.

<a id="S009"></a>
**Source:** p.2 (1640) S009

**原文 (Original Chinese):** 科学假设决定着整个研究的质量和方向，高质量的科学假设应当能够在已有研究的基础上进一步深化和创新. 在这个步骤中，如何让 LLMs 产生创新，则成为最关键的问题. Guilford [12] 在结构智力理论中提出，创新产生于思维的发散和收敛过程之中. 发散思维是指从一个问题或主题出发，能够生成多种可能的答案或获得解决方案的能力. 这种思维模式强调的是想象力、创造力和多样性的生成. 收敛思维则是指针对特定问题找到具体、正确答案的能力. 这种思维模式更多关注逻辑推理、精确度和效率. 科学研究的创新思路就来源于对研究问题的发散思考和收敛具化. 发散过程需要在一定信息基础上，对问题和解决方案进行扩展与探索，这一过程通常通过交流、讨论和辩论来激发；而收敛过程则需要深入理解问题并对特定方向进行深入探索，而这依赖于人类专家具备的高阶洞见能力. 这些正是 LLMs 在创新过程中面临的挑战，导致发散的角度不够广泛、收敛的方向不够精准和可靠.

**English:** Scientific hypotheses determine the quality and direction of the entire research; high-quality scientific hypotheses should be able to further deepen and innovate upon existing research. At this step, how to enable LLMs to produce innovation becomes the most critical question. Guilford [12] proposed in the theory of structural intelligence that innovation arises from the processes of divergent and convergent thinking. Divergent thinking refers to the ability to generate multiple possible answers or solutions from a single problem or topic. This thinking mode emphasizes imagination, creativity, and the generation of diversity. Convergent thinking refers to the ability to find a specific, correct answer to a given problem. This thinking mode focuses more on logical reasoning, precision, and efficiency. Innovative ideas in scientific research originate from divergent thinking about research problems and convergent concretization. The divergent process requires expanding and exploring problems and solutions based on a certain information foundation, typically stimulated through communication, discussion, and debate; the convergent process requires deep understanding of the problem and in-depth exploration of specific directions, which depends on the higher-order insight capabilities possessed by human experts. These are precisely the challenges LLMs face in the innovation process, resulting in insufficient breadth of divergence and insufficient precision and reliability of convergence.

<a id="S010"></a>
**Source:** pp.2–3 (1640–1641) S010

**原文 (Original Chinese):** 为了解决 LLMs 在生成科学假设中存在的问题，本文基于结构智力理论，提出了基于人机协作的多智能体框架（human-in-the-loop multi-agent framework, HILMA）. 如图 1 所示，HILMA 框架包括基于引文网络的文献系统化检索增强、知识增强型 LLMs 研究想法生成、人机协作的多智能体辩论迭代 3 个模块. 首先，针对 LLMs 在知识动态更新上的不足这一问题，本文通过检索增强的方法为 LLMs 注入最新的科研相关知识，在无需对模型进行昂贵的重新训练或复杂的微调的情况下，通过低成本的上下文提示来弥补 LLMs 在动态知识更新上的不足，从而使其在生成科学假设时具备最新且完备的科学研究进展. 其次，通过引入基于多智能体辩论的假设迭代增强方法，以辩论方式模拟人类的发散思维，激发 LLMs 的能力，使用发散思维来产生尽可能多的初步假设. 在该框架中，不同的智能体角色负责从多个角度审视和辩论初始假设，通过丰富的讨论和批评性反馈，增加假设的多样性和深度. 这种方法模拟了科学界的同行评审过程，提升了假设的科学性和实用性. 最后，为了进一步提升 LLMs 的专业性和针对性，HILMA 框架结合了人类专家的高阶洞察力和模型的数据处理能力. 通过在辩论过程中实时引入人类学者的直觉和专业知识，以指导模型的假设生成过程，并通过收敛思维从中选择最有潜力的方案进行进一步深化和精炼. 这种协作旨在最大化利用了 LLMs 潜力和人类的洞察力，以生成更符合实际研究需求的科学假设. 这一综合策略的应用，能够显著提升 LLMs 在科学研究领域中的应用效果，使得生成的假设在质量和创新性方面满足科学研究的要求.

**English:** To address the problems LLMs face in generating scientific hypotheses, this paper proposes, based on the theory of structural intelligence, a human-in-the-loop multi-agent framework (HILMA). As shown in Fig. 1, the HILMA framework consists of three modules: systematic literature retrieval enhancement based on citation networks, knowledge-enhanced LLM research idea generation, and human-machine collaborative multi-agent debate iteration. First, to address the deficiency of LLMs in dynamic knowledge updating, this paper infuses LLMs with the latest research-relevant knowledge through a retrieval-augmented approach, using low-cost contextual prompting to compensate for LLMs' shortcomings in dynamic knowledge updating without the need for expensive retraining or complex fine-tuning, thereby equipping them with the latest and most comprehensive scientific research advances when generating hypotheses. Second, by introducing a hypothesis iteration enhancement method based on multi-agent debate, the framework simulates human divergent thinking through debate-style interaction, stimulating LLMs' capabilities and using divergent thinking to generate as many preliminary hypotheses as possible. In this framework, different agent roles are responsible for examining and debating initial hypotheses from multiple perspectives, increasing the diversity and depth of hypotheses through rich discussion and critical feedback. This approach simulates the scientific peer review process, enhancing the scientific rigor and practical utility of the hypotheses. Finally, to further enhance the professionalism and pertinence of LLMs, the HILMA framework integrates the higher-order insights of human experts with the data processing capabilities of models. By introducing human scholars' intuition and expertise in real time during the debate process to guide the model's hypothesis generation, and selecting the most promising options through convergent thinking for further deepening and refinement, this collaboration aims to maximize both the potential of LLMs and the insight of human experts, generating scientific hypotheses that better meet practical research needs. The application of this comprehensive strategy can significantly enhance the effectiveness of LLMs in scientific research, enabling the generated hypotheses to meet scientific research requirements in terms of both quality and innovativeness.

<a id="S011"></a>
**Source:** p.3 (1641) S011

**原文 (Original Chinese):** 综上所述，本文的主要贡献包括 4 个方面: 1）系统地分析了 LLMs 在处理科学创造性问题时所面临的局限性，揭示了其在发散思维和收敛思维等方面的不足；2）提出了科学文献的结构化组织查询方法，通过对文献引文网络的自适应组织和构建，有效地整合了最新的科学研究成果，确保为 LLMs 提供全面且前沿的知识；3）受结构智力理论的启发，提出了人机协作的多智能体辩论框架，可在多智能体和人类的协作下，模仿人类的发散思维和收敛思维过程，有效地产生和精炼科学假设，提升其质量与创新性；4）基于人类和模型的系列评估，实验结果证明了所提 HILMA 框架的优越性，相较于现有 LLMs 驱动的基线模型，HILMA 生成的科学假设在创新性、实用性、可行性等方面均有显著提升.

**English:** In summary, the main contributions of this paper include four aspects: 1) systematically analyzing the limitations of LLMs in handling scientifically creative problems, revealing their deficiencies in divergent and convergent thinking; 2) proposing a structured organization and query method for scientific literature, effectively integrating the latest scientific research results through adaptive organization and construction of citation networks, ensuring that LLMs are provided with comprehensive and cutting-edge knowledge; 3) inspired by the theory of structural intelligence, proposing a human-machine collaborative multi-agent debate framework that, through collaboration between multiple agents and humans, mimics the human processes of divergent and convergent thinking, effectively generating and refining scientific hypotheses to enhance their quality and innovativeness; 4) through a series of human and model evaluations, experimental results demonstrate the superiority of the proposed HILMA framework -- compared with existing LLM-driven baseline models, HILMA-generated scientific hypotheses show significant improvements in innovativeness, practicality, feasibility, and other dimensions.

---

<a id="F001"></a>
### Fig. 1. HILMA Framework

**Placed near:** p.1 S010
**Source:** p.1 (1641) C001

![Fig. 1](assets/fig1.png)

**原文图注 (Original caption):** 图1 HILMA 框架

**English caption:** Fig. 1 HILMA framework

**Reading note:** This figure illustrates the overall HILMA framework pipeline, showing how scientific literature, human insights, and multi-agent debate iteration converge to produce the final scientific hypothesis. The figure depicts the process flow: from scientific literature retrieval, through initial idea generation, multi-agent debate (with agents providing critiques and suggestions), to the final refined scientific hypothesis.

---

## 1. 相关工作 (Related Work)

<a id="S012"></a>
**Source:** p.2 (1642) S012

**原文 (Original Chinese):** 本节聚焦于 3 个与本文研究密切相关的研究方向：科学假设生成、知识增强的 LLMs，以及人机协作的智能系统. 这些领域的发展为本文研究奠定了理论基础，提供了前沿技术.

**English:** This section focuses on three research directions closely related to this study: scientific hypothesis generation, knowledge-enhanced LLMs, and human-machine collaborative intelligent systems. Developments in these fields have laid the theoretical foundation and provided cutting-edge technologies for this research.

### 1.1 科学假设生成 (Scientific Hypothesis Generation)

<a id="S013"></a>
**Source:** p.2 (1642) S013

**原文 (Original Chinese):** 基于人工智能的科学假设生成是 AI4Science 领域的核心问题，旨在利用 AI 辅助或自动化科学探索的初始阶段 [13-14]. 已有研究主要集中在研发能够从现有数据中预测新科学现象的算法和模型 [15]. 近年来，随着机器学习技术的蓬勃发展，尤其是深度神经网络在众多数据密集型任务上的成功应用，科学假设生成的研究也扩展到更复杂的科学问题求解中. LLMs 是这一趋势的新发展，如何利用其参数化知识提出合理有用的科学假设，成为了一个备受关注的问题 [16-17]. 例如，Shojaee 等人 [18] 研究借助 LLMs 的编程能力有效发现科学方程. Lu 等人 [19] 提出了关于 AI 科学家的构想，其通过设定初始模板，促使 LLMs 生成众多研究思路. 与此同时，将这些思路与现有文献中的方法进行对比，进而筛选出评分较高的研究思路，以应用于后续的实验中. 尽管在科学研究的求解和应用中对 LLMs 的探索不断深入 [20]，但它们生成的科学假设在创新性和深度方面仍存在较大不足.

**English:** AI-based scientific hypothesis generation is a core problem in the AI4Science domain, aiming to use AI to assist or automate the initial stages of scientific exploration [13-14]. Existing research has primarily focused on developing algorithms and models capable of predicting new scientific phenomena from existing data [15]. In recent years, with the vigorous development of machine learning techniques, especially the successful application of deep neural networks to numerous data-intensive tasks, research on scientific hypothesis generation has expanded to solving more complex scientific problems. LLMs represent a new development in this trend, and how to leverage their parameterized knowledge to propose reasonable and useful scientific hypotheses has become a highly regarded problem [16-17]. For example, Shojaee et al. [18] investigated leveraging LLMs' programming capabilities to effectively discover scientific equations. Lu et al. [19] proposed a vision for an AI scientist, which generates numerous research ideas by setting initial templates and prompting LLMs. Meanwhile, these ideas are compared against methods in existing literature to select higher-scoring research ideas for subsequent experiments. Although exploration of LLMs in solving and applying scientific research continues to deepen [20], the scientific hypotheses they generate still exhibit significant deficiencies in innovativeness and depth.

<a id="S014"></a>
**Source:** p.2 (1642) S014

**原文 (Original Chinese):** 本文研究基于结构智力理论中的发散思维和收敛思维，提出人机协作的多智能体框架. 通过结合实时的系统化知识检索增强机制，动态整合最新科研进展，为模型提供前沿完备的信息基础. 同时，通过多智能体辩论和人机协作，进一步优化和精炼生成的假设，增强假设的多样性和论证深度.

**English:** This study, grounded in the divergent and convergent thinking principles from the theory of structural intelligence, proposes a human-machine collaborative multi-agent framework. By incorporating a real-time, systematic knowledge retrieval enhancement mechanism that dynamically integrates the latest research advances, it provides models with a cutting-edge and comprehensive information foundation. Simultaneously, through multi-agent debate and human-machine collaboration, the generated hypotheses are further optimized and refined, enhancing their diversity and depth of argumentation.

### 1.2 知识增强的 LLMs (Knowledge-Enhanced LLMs)

<a id="S015"></a>
**Source:** p.2 (1642) S015

**原文 (Original Chinese):** LLMs 的生成阶段存在幻觉 [21-22]、有害性 [23]、伪事实性 [24] 和缺乏长时记忆 [25] 等问题，知识增强被认为是克服这些局限性的有效方法 [26]. 知识增强的 LLMs 首先使用外部检索器从特定的知识源（如百科、图谱和数据库等）检索相关的结构化和非结构化知识；然后将检索到的知识作为 LLMs 的外部上下文信息，引导 LLMs 生成以知识为基础的回答 [27].

**English:** LLMs suffer from problems in their generation phase including hallucination [21-22], harmfulness [23], pseudo-factuality [24], and lack of long-term memory [25]. Knowledge enhancement is considered an effective method to overcome these limitations [26]. Knowledge-enhanced LLMs first use an external retriever to fetch relevant structured and unstructured knowledge from specific knowledge sources (such as encyclopedias, knowledge graphs, and databases); the retrieved knowledge is then used as external contextual information to guide LLMs in generating knowledge-based responses [27].

<a id="S016"></a>
**Source:** pp.2–3 (1642) S016

**原文 (Original Chinese):** 已有研究关注于检索器和阅读器的优化，研究人员使用稀疏检索器，如 BM25 [28] 和 TF-IDF [29] 进行相关性计算并检索. 然而，稀疏方法在提取文本内容的语义特征方面存在不足 [30]. 为解决该问题，研究人员提出基于语言模型的密集检索方法，通过将文档和查询编码为稠密向量，有效地表示文本内容的语义特征 [31-32]. 一些近年来研究探索 LLMs 作为检索器的性能，Shen 等人 [33] 证明 LLMs 可以在多个基准数据集上作为零样本检索器使用；而 Ma 等人 [34] 提出了一种利用 LLMs 的 Listwise Reranker，在不使用任务特定训练数据的情况下实现了强大的重新排序效果；Sun 等人 [35] 探究了 LLMs 的相关性排名，发现经过引导的 LLMs 能够达到最先进的监督方法的性能.

**English:** Existing research has focused on optimizing retrievers and readers. Researchers have used sparse retrievers such as BM25 [28] and TF-IDF [29] for relevance computation and retrieval. However, sparse methods fall short in extracting semantic features of text content [30]. To address this, researchers have proposed dense retrieval methods based on language models, which effectively represent the semantic features of text content by encoding documents and queries as dense vectors [31-32]. Some recent studies have explored the performance of LLMs as retrievers: Shen et al. [33] demonstrated that LLMs can serve as zero-shot retrievers on multiple benchmark datasets; Ma et al. [34] proposed a Listwise Reranker utilizing LLMs that achieves strong re-ranking performance without task-specific training data; Sun et al. [35] investigated LLMs' relevance ranking and found that guided LLMs can achieve the performance of state-of-the-art supervised methods.

<a id="S017"></a>
**Source:** p.3 (1642) S017

**原文 (Original Chinese):** 知识增强模型能够准确捕捉和应用专业知识，在需要深度领域知识的科学研究中尤为重要. Jeong 等人 [36] 在生物医学领域引入知识增强的 LLMs，通过检索特定领域的文档和让 LLMs 自我反思，能够生成准确且有解释性的答案，有效地支撑了生物医学领域的发展. 此外，一些研究尝试实时更新模型的知识库，以保证其输出的时效性和准确性 [37]. 通过知识增强，不仅提高了 LLMs 在特定领域内的表现，还能够适应快速变化的科研环境，生成与当前研究前沿对齐的内容.

**English:** Knowledge-enhanced models can accurately capture and apply professional knowledge, which is particularly important in scientific research requiring deep domain knowledge. Jeong et al. [36] introduced knowledge-enhanced LLMs in the biomedical domain, generating accurate and interpretable answers by retrieving domain-specific documents and allowing LLMs to self-reflect, effectively supporting developments in the biomedical field. Additionally, some studies have attempted to update model knowledge bases in real time to ensure the timeliness and accuracy of their outputs [37]. Through knowledge enhancement, not only is the performance of LLMs in specific domains improved, but they can also adapt to rapidly changing research environments, generating content aligned with current research frontiers.

### 1.3 人机协作的智能系统 (Human-Machine Collaborative Intelligent Systems)

<a id="S018"></a>
**Source:** p.3 (1642–1643) S018

**原文 (Original Chinese):** 人机协作的智能系统强调智能系统与人类的互补性，旨在将人类的创造力和决策能力与机器的计算能力和数据处理速度相结合 [38]，协同完成特定任务. 传统研究主要集中于提高人与机器人、AI 系统等智能体交互的效率，以满足人类需求 [39]. LLMs 的兴起标志着该领域的重大转变，人类的反馈和推理在增强智能体能力方面的作用日益彰显，能够显著提升智能体的表现. 近年来的研究采用启发式规则 [40-41] 或可学习的算法引导智能体寻求人类的帮助. 此外，研究者开始重视探究特定的引导提示，以激励基于 LLMs 的智能体主动寻求人类的输入，从而在这些协作系统中构建更具互动性和协作性的应用 [42-43].

**English:** Human-machine collaborative intelligent systems emphasize the complementarity between intelligent systems and humans, aiming to combine human creativity and decision-making abilities with the computational power and data processing speed of machines [38] to collaboratively accomplish specific tasks. Traditional research has primarily focused on improving the efficiency of interaction between humans and intelligent agents such as robots and AI systems to meet human needs [39]. The rise of LLMs marks a significant shift in this field, with human feedback and reasoning playing an increasingly prominent role in enhancing agent capabilities, significantly improving agent performance. Recent studies have employed heuristic rules [40-41] or learnable algorithms to guide agents in seeking human assistance. Furthermore, researchers have begun to emphasize investigating specific guiding prompts to motivate LLM-based agents to proactively seek human input, thereby building more interactive and collaborative applications within these cooperative systems [42-43].

<a id="S019"></a>
**Source:** p.3 (1643) S019

**原文 (Original Chinese):** Feng 等人 [44] 设计了一种通用可学习的方法，通过直接规划的形式，实现人类与 LLMs 之间的高效协作. Dhillon 等人 [45] 的研究表明，通过提供 AI 辅助，可以显著提升人类用户的写作质量和效率. 李戈等人 [46] 探讨了 LLMs 在人机协同软件开发与演化中的应用及其带来的挑战，强调了人在软件开发与演化中的主导地位和可信保障的重要性. 在需求工程领域，靳东明等人 [47] 提出了 ChatModeler 框架，通过 LLMs 和人类的协同合作，优化了需求获取和建模过程. 该框架利用模型自动处理任务，减轻人类的负担，同时能根据反馈进行调整，提高需求模型的质量和交互效率.

**English:** Feng et al. [44] designed a general learnable method that achieves efficient collaboration between humans and LLMs through direct planning. Dhillon et al. [45] demonstrated that providing AI assistance can significantly improve the writing quality and efficiency of human users. Li Ge et al. [46] explored the application of LLMs in human-machine collaborative software development and evolution and the challenges they bring, emphasizing the importance of human leadership and trustworthiness assurance in software development and evolution. In the domain of requirements engineering, Jin Dongming et al. [47] proposed the ChatModeler framework, which optimizes the requirements elicitation and modeling process through collaborative cooperation between LLMs and humans. This framework leverages models to automatically handle tasks, reducing human burden while making adjustments based on feedback to improve the quality and interaction efficiency of requirements models.

<a id="S020"></a>
**Source:** p.3 (1643) S020

**原文 (Original Chinese):** 在科学研究领域，人机协作系统具备重要意义. 复杂科学问题的研究要求同时具备深厚的专业知识和高效的信息处理能力，而人类与 LLMs 在这一过程中各自具备独特的优势. 通过人机协作，能够提高科学假设的质量和创新性，共同创造出符合科学标准且创新性强的科学假设.

**English:** In the scientific research domain, human-machine collaborative systems hold significant importance. Research on complex scientific problems requires simultaneous possession of deep professional knowledge and efficient information processing capabilities, and humans and LLMs each have unique advantages in this process. Through human-machine collaboration, the quality and innovativeness of scientific hypotheses can be enhanced, jointly creating scientific hypotheses that meet scientific standards and possess strong innovativeness.

---

## 2. 人机协作的多智能体辩论框架 (Human-Machine Collaborative Multi-Agent Debate Framework)

<a id="S021"></a>
**Source:** p.3 (1643) S021

**原文 (Original Chinese):** 本文研究提出了一种新的科学假设生成框架 HILMA，旨在通过人机协作和多智能体技术，从海量的科学文献中提取和生成有价值的科学假设. 首先，HILMA 通过关键词查找与研究主题相关的文献，并且基于文献引用关系网络进行拓展和筛选，确保输入数据的质量和相关性；然后，基于系统化的文献信息，使用 LLMs 进行深入探索与分析，生成初步的科学假设；最后，利用人机协作的多智能体系统进行科学假设迭代，模拟创新孕育的思维发散和收敛过程，最终实现科学假设生成的准确性和创新性.

**English:** This paper proposes a novel scientific hypothesis generation framework, HILMA, aimed at extracting and generating valuable scientific hypotheses from massive scientific literature through human-machine collaboration and multi-agent technology. First, HILMA searches for literature related to the research topic through keywords and expands and filters based on literature citation relationship networks to ensure the quality and relevance of input data. Then, based on systematic literature information, LLMs are used for in-depth exploration and analysis to generate preliminary scientific hypotheses. Finally, a human-machine collaborative multi-agent system is employed for scientific hypothesis iteration, simulating the divergent and convergent thinking processes that nurture innovation, ultimately achieving both accuracy and innovativeness in scientific hypothesis generation.

### 2.1 基于引文网络的文献系统化检索增强方法 (Systematic Literature Retrieval Enhancement Based on Citation Networks)

<a id="S022"></a>
**Source:** p.3 (1643) S022

**原文 (Original Chinese):** 为了给 LLMs 提供系统化的科学知识，本节提出了基于引文网络的文献系统化检索增强方法. 通过对文献引文网络的自适应组织和构建，有效地整合了最新和广泛的科学研究成果，系统性地梳理不同研究点的研究脉络，确保为 LLMs 提供的知识具备前沿性和系统性. 方法主要分为 2 个部分：1）自顶向下的子图引文网络构建. 从相关研究关键词出发，查找相关中心文献，并且基于中心文献深入挖掘，构建子图引文网络. 2）自底向上的文献网络综述生成. 从各个子图引文网络出发，汇总每个子图网络的研究脉络和现状，形成高阶的子图研究综述. 二者相结合，能够实现对特定领域文献的深入挖掘和梳理，为 LLMs 提供系统可靠的文献知识来源，图 2 展示了基于引文网络的文献系统化检索增强流程.

**English:** To provide LLMs with systematic scientific knowledge, this section proposes a systematic literature retrieval enhancement method based on citation networks. Through adaptive organization and construction of literature citation networks, the method effectively integrates the latest and broadest scientific research results, systematically organizing the research context of different research points, ensuring that the knowledge provided to LLMs is cutting-edge and systematic. The method is divided into two parts: 1) Top-down subgraph citation network construction. Starting from relevant research keywords, identify related central literature and conduct in-depth exploration based on central literature to construct subgraph citation networks. 2) Bottom-up literature network review generation. Starting from each subgraph citation network, summarize the research context and current status of each subgraph network to form high-level subgraph research reviews. The combination of these two parts enables in-depth mining and organization of domain-specific literature, providing LLMs with a systematic and reliable source of literature knowledge. Fig. 2 illustrates the systematic literature retrieval enhancement process based on citation networks.

---

<a id="F002"></a>
### Fig. 2. Systematic Literature Retrieval Enhancement Process Based on Citation Network

**Placed near:** p.3 S022
**Source:** p.3 (1643) C002

![Fig. 2](assets/fig2.png)

**原文图注 (Original caption):** 图2 基于引文网络的文献系统化检索增强流程

**English caption:** Fig. 2 Systematic literature retrieval enhancement process based on citation network

**Reading note:** This figure shows the pipeline: keyword-based retrieval of related literature, construction of subgraph citation networks centered around key papers, and generation of research reviews from each subgraph network. Central literature, cited literature, citing literature, and similar literature are visually distinguished.

---

#### 2.1.1 自顶向下的子图引文网络构建 (Top-Down Subgraph Citation Network Construction)

<a id="S023"></a>
**Source:** pp.3–4 (1643) S023

**原文 (Original Chinese):** 为了在科学文献领域进行系统化检索增强，采用基于引文网络的方法，旨在构建一个结构化的文献组织和查询系统. 本节详细介绍了自顶向下的子图引文网络构建过程，包括关键词检索、文献筛选和网络拓展等步骤. 首先，利用 Semantic Scholar API [48] 进行核心关键词的检索，以获取与研究内容相关文献的数字对象唯一标识符（digital object unique identifier, DOI）. 这一步骤的关键在于选择能够准确代表研究领域核心的关键词，以确保检索结果的准确性和全面性. 由于检索结果数量庞大且杂乱，需要对文献进行筛选，保留具有重要性和影响力的中心文献. 这一步骤借助文献的被引次数、文献类型以及文献来源来进行评估和排序. 具体地，定义中心文献集合为 {c1, c2, ..., cm}，其中 m 表示中心文献的数量.

**English:** To achieve systematic retrieval enhancement in the scientific literature domain, a citation network-based method is adopted, aiming to construct a structured literature organization and query system. This section details the top-down subgraph citation network construction process, including keyword retrieval, literature filtering, and network expansion steps. First, the Semantic Scholar API [48] is used to perform core keyword searches to obtain the digital object unique identifiers (DOIs) of literature related to the research content. The key to this step lies in selecting keywords that accurately represent the core of the research domain to ensure the accuracy and comprehensiveness of retrieval results. Since the retrieval results are numerous and disorganized, literature needs to be filtered to retain central literature of importance and influence. This step evaluates and ranks literature based on citation count, literature type, and literature source. Specifically, the set of central literature is defined as {c1, c2, ..., cm}, where m denotes the number of central literature items.

<a id="S024"></a>
**Source:** p.4 (1643) S024

**原文 (Original Chinese):** 基于确定的中心文献，将从引文、被引和相关文献 3 个维度进行子图网络的拓展与构建. 具体地，通过文献的引用关系、被引关系、相关关系来构建基于特定中心文献 c 的子图引文网络，表示为 Gc = (Vc, Ec)，其中 V 表示网络的节点集合，E 表示边集合. 引用网络、被引网络、相关网络的构建过程可以通过以下公式表示：

E_cite = {(v_i, v_c) | v_i in V_cite, 文献i引用c},  (1)

E_cited = {(v_i, v_c) | v_i in V_cited, 文献i被c引用},  (2)

E_related = {(v_i, v_c) | v_i in V_related, 文献i与c相关},  (3)

G_c = (V_cite U V_cited U V_related, E_cite U E_cited U E_related).  (4)

通过以上公式，能够从一个中心文献构建出一个结构化、多维度的文献网络，该网络以中心文献为核心，囊括了与研究内容密切相关的文献以及研究的发展脉络和趋势. 为进一步的研究提供了深入的信息基础和理论支持.

**English:** Based on the identified central literature, subgraph network expansion and construction are carried out from three dimensions: citations, cited-by, and related literature. Specifically, through the citation, cited-by, and related relationships of the literature, a subgraph citation network based on a specific central literature c is constructed, denoted as G_c = (V_c, E_c), where V represents the set of nodes and E represents the set of edges. The construction processes of the citation network, cited-by network, and related network can be expressed by the following formulas:

E_cite = {(v_i, v_c) | v_i in V_cite, literature i cites c},  (1)

E_cited = {(v_i, v_c) | v_i in V_cited, literature i is cited by c},  (2)

E_related = {(v_i, v_c) | v_i in V_related, literature i is related to c},  (3)

G_c = (V_cite U V_cited U V_related, E_cite U E_cited U E_related).  (4)

Through the above formulas, a structured, multi-dimensional literature network can be constructed from a single central literature item. This network, centered on the central literature, encompasses literature closely related to the research content as well as the developmental context and trends of the research, providing a deep information foundation and theoretical support for further investigation.

#### 2.1.2 自底向上的文献网络综述生成 (Bottom-Up Literature Network Review Generation)

<a id="S025"></a>
**Source:** p.4 (1644) S025

**原文 (Original Chinese):** 尽管经过筛选，所构建的每个子图引文网络仍然较为庞大（数十篇）. 考虑到 LLMs 上下文窗口长度以及计算效率，本文采取自底而上的文献网络综述生成方法，将每个子图引文网络中的文献进行汇总，让 LLMs 生成该研究的综述. 对于每个子图引文网络 Gi = (Vi, Ei)，其每个节点表示一篇文献，LLMs 将利用节点中的文献文本信息，结合其对研究领域的深入理解，撰写研究综述. 这些综述将涵盖该子图引文网络所涉及的研究主题、研究方法、研究成果等方面. 在撰写综述的过程中，LLMs 将考虑文献之间的相互关系，以及其在研究领域中的重要性和影响力.

**English:** Despite filtering, each constructed subgraph citation network remains relatively large (dozens of papers). Considering the context window length of LLMs and computational efficiency, this paper adopts a bottom-up literature network review generation method, aggregating the literature within each subgraph citation network and having LLMs generate a research review for that network. For each subgraph citation network G_i = (V_i, E_i), where each node represents a paper, LLMs will utilize the textual information of the papers in the nodes, combined with their deep understanding of the research domain, to compose research reviews. These reviews will cover the research topics, research methods, research outcomes, and other aspects involved in the subgraph citation network. In the process of composing reviews, LLMs will consider the interrelationships among the literature as well as their importance and influence within the research domain.

<a id="S026"></a>
**Source:** p.4 (1644) S026

**原文 (Original Chinese):** 经由上述过程，每个子图引文网络 Gi 都拥有一个对应研究综述 si，其中 i in {1, 2, ..., m}，这些综述将为 LLMs 提供科学假设生成和辩论的信息基础，避免不必要的计算和重复查询. 同时，这些综述还可以为用户提供全面而系统的研究概览，促进其对后续假设生成的理解.

**English:** Through the above process, each subgraph citation network G_i possesses a corresponding research review s_i, where i in {1, 2, ..., m}. These reviews will provide LLMs with an information foundation for scientific hypothesis generation and debate, avoiding unnecessary computation and redundant queries. Simultaneously, these reviews can also provide users with a comprehensive and systematic research overview, facilitating their understanding of subsequent hypothesis generation.

<a id="S027"></a>
**Source:** p.4 (1644) S027

**原文 (Original Chinese):** 通过自顶向下的子图引文网络构建和自底向上的文献网络综述生成，建立了一个结构化、系统化的知识库，囊括了完善的具体文献和不同子领域的文献综述，为后续的假设生成和验证提供坚实的基础.

**English:** Through top-down subgraph citation network construction and bottom-up literature network review generation, a structured and systematic knowledge base has been established, encompassing comprehensive specific literature and literature reviews of different sub-domains, providing a solid foundation for subsequent hypothesis generation and validation.

### 2.2 知识增强的研究想法生成 (Knowledge-Enhanced Research Idea Generation)

<a id="S028"></a>
**Source:** p.4 (1644) S028

**原文 (Original Chinese):** 在构建了基于引文网络的文献系统化检索增强机制后，本节将探讨如何应用知识增强型 LLMs 来生成具有深度和创新性的研究想法. 该过程旨在整合结构化和系统化的文献知识，直接融入模型的推理和生成能力中，以克服传统 LLMs 生成创新科学假设的局限性.

**English:** After constructing the systematic literature retrieval enhancement mechanism based on citation networks, this section explores how to apply knowledge-enhanced LLMs to generate research ideas with depth and innovativeness. This process aims to integrate structured and systematic literature knowledge directly into the model's reasoning and generation capabilities to overcome the limitations of traditional LLMs in generating innovative scientific hypotheses.

<a id="S029"></a>
**Source:** pp.4–5 (1644) S029

**原文 (Original Chinese):** 首先，利用自顶向下的子图引文网络构建方法，得到了围绕特定中心文献组织的高度结构化的文献子集. 这些子集形成了多维度的信息，为 LLMs 提供了丰富的背景知识和上下文信息. 每个子集都是围绕其核心文献构建的. 通过分析每个子集的研究综述 {s1, s2, ..., sm}，LLMs 能够从研究意义、潜在的研究空间、未来发展趋势等角度进行评分，从而选择出最具研究潜力和价值的子集. 该选择过程可以形式化表示为

arg max(score([s1, s2, ..., sm])),  (5)

其中 score 表示 LLMs 对综述的评分.

**English:** First, using the top-down subgraph citation network construction method, highly structured literature subsets organized around specific central literature are obtained. These subsets form multi-dimensional information, providing LLMs with rich background knowledge and contextual information. Each subset is constructed around its core literature. By analyzing the research reviews of each subset {s1, s2, ..., sm}, LLMs can score them from perspectives such as research significance, potential research space, and future development trends, thereby selecting the subset with the greatest research potential and value. This selection process can be formalized as:

arg max(score([s1, s2, ..., sm])),  (5)

where score represents the LLM's rating of the reviews.

<a id="S030"></a>
**Source:** p.5 (1644) S030

**原文 (Original Chinese):** 选定研究目标后，将对对应的目标子图 G_t 中的文献进行进一步的结构化组织，使 LLMs 能够充分获取该领域的发展脉络与研究现状. 在此基础上，LLMs 将综合这些文献中的知识和其自身的语言生成能力，生成全面而有效的研究想法. 该想法生成过程可以用以下公式表示：

h_0 = LLM(P, G_t, s_t),  (6)

其中 h_0 为初始生成的科学假设，P 为指令提示（prompt），G_t 为选定的目标引文子图，s_t 为 G_t 的研究综述.

**English:** After selecting the research target, the literature within the corresponding target subgraph G_t is further structurally organized, enabling LLMs to fully grasp the developmental context and current research status of the field. On this basis, LLMs will synthesize the knowledge from these papers with their own language generation capabilities to produce comprehensive and effective research ideas. This idea generation process can be expressed by the following formula:

h_0 = LLM(P, G_t, s_t),  (6)

where h_0 is the initially generated scientific hypothesis, P is the instruction prompt, G_t is the selected target citation subgraph, and s_t is the research review of G_t.

<a id="S031"></a>
**Source:** p.5 (1644) S031

**原文 (Original Chinese):** 通过这种知识增强的方法，LLMs 生成的研究提案不仅具有更高的可信度和创新性，而且能够提升研究提案的整体质量. 知识增强型 LLMs 不仅可以加速研究想法的生成过程，而且为科学发现的第一阶段提供了更高效的支持.

**English:** Through this knowledge-enhanced approach, the research proposals generated by LLMs not only possess higher credibility and innovativeness but also improve the overall quality of research proposals. Knowledge-enhanced LLMs can not only accelerate the generation process of research ideas but also provide more efficient support for the first stage of scientific discovery.

### 2.3 人机协作的多智能体辩论迭代 (Human-Machine Collaborative Multi-Agent Debate Iteration)

<a id="S032"></a>
**Source:** p.5 (1644) S032

**原文 (Original Chinese):** 在严谨的科学研究探索中，创新性假设的孵化是一个动态且迭代的过程，要求不断质疑、修正与深化. 本节介绍一种创新的人机协作策略，通过多智能体辩论迭代机制，旨在实现科学假设的深度精炼与优化. 此方法的核心在于利用来自不同背景和专业知识的智能体（包括 LLMs 和人类专家）的多样化视角，通过辩论和批判性思考来迭代地精炼和增强初步生成的研究想法，确保每个假设都经过全面的考量和验证.

**English:** In rigorous scientific research exploration, the incubation of innovative hypotheses is a dynamic and iterative process, requiring continuous questioning, revision, and deepening. This section introduces an innovative human-machine collaboration strategy, employing a multi-agent debate iteration mechanism aimed at achieving deep refinement and optimization of scientific hypotheses. The core of this method lies in leveraging the diverse perspectives of agents from different backgrounds and areas of expertise (including LLMs and human experts) to iteratively refine and enhance the initially generated research ideas through debate and critical thinking, ensuring that each hypothesis undergoes comprehensive consideration and verification.

<a id="S033"></a>
**Source:** pp.5–6 (1644–1645) S033

**原文 (Original Chinese):** 多智能体辩论迭代的过程设计如下：1）角色分配. 每个智能体被分配一个特定角色，包括假设提出者、审阅者和中立分析师. 这些角色帮助结构化辩论，使每个智能体可以从不同的角度审视问题. 2）初始假设生成. 基于 2.2 节知识增强型 LLMs 的输出，首先形成一组初步的科学假设. 3）开放式辩论. 智能体之间进行开放式辩论，每个智能体根据其角色提出支持或反对假设的论点. 此阶段旨在揭示假设的潜在弱点和未考虑的变量. 人类专家在过程中参与并且引导智能体的辩论方向. 4）证据集成. 辩论中提出的有效点将用于修改或强化假设. 该过程包括请求更多引文子图、重新分析已有数据或引入新的科学理论. 人类专家在此过程中扮演仲裁者的角色，适时引导辩论的深度与广度，同时根据辩论进程中的关键发现，向知识增强型 LLMs 提出数据查询或模型调整的需求，以获取更多支持或反驳假设的证据. 5）迭代循环. 每次辩论后都对假设进行评估和调整，直到达到预定的科学严格性和创新性标准. 每回合辩论后，整合智能体汇总辩论要点，与人类专家共同评估假设的改进空间，从而迭代生成更加成熟与精细的假设版本. 这个过程可以多次迭代.

**English:** The multi-agent debate iteration process is designed as follows: 1) Role assignment. Each agent is assigned a specific role, including hypothesis proposer, reviewer, and neutral analyst. These roles help structure the debate, enabling each agent to examine the problem from different perspectives. 2) Initial hypothesis generation. Based on the output of knowledge-enhanced LLMs from Section 2.2, a set of preliminary scientific hypotheses is first formed. 3) Open debate. Agents engage in open debate, with each agent presenting arguments supporting or opposing the hypothesis according to its role. This stage aims to reveal potential weaknesses and unconsidered variables in the hypotheses. Human experts participate in and guide the debate direction of the agents throughout the process. 4) Evidence integration. Valid points raised during debate are used to modify or strengthen the hypotheses. This process includes requesting additional citation subgraphs, re-analyzing existing data, or introducing new scientific theories. Human experts serve as arbitrators in this process, timely guiding the depth and breadth of the debate, while also proposing data queries or model adjustment needs to knowledge-enhanced LLMs based on key findings during the debate process to obtain more evidence supporting or refuting the hypotheses. 5) Iterative loop. After each debate round, the hypotheses are evaluated and adjusted until predetermined standards of scientific rigor and innovativeness are met. After each debate round, the integrated agent summarizes the key debate points and jointly evaluates the improvement space of the hypotheses with human experts, thereby iteratively generating more mature and refined versions of the hypotheses. This process can be iterated multiple times.

<a id="S034"></a>
**Source:** p.6 (1645) S034

**原文 (Original Chinese):** 多智能体辩论迭代的主要目的是利用集体智慧来提高假设的质量和可靠性. 每个假设都经过详尽的挑战和防御，从而确保其在逻辑上的健全性和在实证基础上的坚实性，有助于揭示那些可能未被单一智能体注意到的新的研究方向或方法论问题.

**English:** The primary purpose of multi-agent debate iteration is to leverage collective intelligence to improve the quality and reliability of hypotheses. Each hypothesis undergoes thorough challenge and defense, thereby ensuring its logical soundness and empirical solidity, helping to reveal new research directions or methodological issues that might not have been noticed by a single agent.

<a id="S035"></a>
**Source:** pp.6–7 (1645) S035

**原文 (Original Chinese):** 在研究框架中，人机协作是关键的一步，它结合了人类专家的创造性思维和高阶决策能力与 LLMs 的高效数据处理和整合的能力. 此环节的核心目的是充分发挥人类与 LLMs 智能体各自的优势，共同创造出符合科学标准且创新性强的科学假设. 在这一过程中，人类专家负责提供方向性指导、深入分析和复杂决策，这包括指出未被发现的假设漏洞、提供额外的专业知识或重新定义问题的边界，而多智能体则在大数据处理、假设迭代和模式提取方面发挥作用. 人机协作模式不仅加速了科学假设的生成过程，还增强了假设的适用性和准确性，确保生成的科学假设既有深度又有广度，同时能够适应复杂多变的科研环境.

**English:** Within the research framework, human-machine collaboration is a crucial step, combining the creative thinking and higher-order decision-making capabilities of human experts with the efficient data processing and integration capabilities of LLMs. The core purpose of this step is to fully leverage the respective strengths of humans and LLM agents, jointly creating scientific hypotheses that meet scientific standards and possess strong innovativeness. In this process, human experts are responsible for providing directional guidance, in-depth analysis, and complex decision-making, including identifying undiscovered hypothesis loopholes, providing additional professional knowledge, or redefining problem boundaries, while multi-agents play a role in big data processing, hypothesis iteration, and pattern extraction. The human-machine collaboration model not only accelerates the generation process of scientific hypotheses but also enhances the applicability and accuracy of the hypotheses, ensuring that the generated scientific hypotheses possess both depth and breadth while being able to adapt to complex and changing research environments.

### 2.4 人机协作科学假设生成平台 (Human-Machine Collaborative Hypothesis Generation Platform)

<a id="S036"></a>
**Source:** p.7 (1645) S036

**原文 (Original Chinese):** 如图 3 所示，本文研究开发了一个人机协作科学假设生成平台，旨在提升科研人员在科学假设生成过程中的效率和准确性. 平台由功能区和对话区组成. 在功能区，用户可以选择 LLMs 基座和文献检索源，并控制智能体之间的对话进程及汇总最终结论. 在对话区，用户可通过对话框输入想要探索的研究主题或科学问题，平台能够根据输入自主开展系统化的文献检索、增强总结，并生成初步的科学假设. 平台允许研究人员实时监控和管理多智能体协同生成的科学假设，并在多智能体对话过程中介入和调整. 实时监控功能不仅让研究人员能够全面了解假设生成的进展，还允许他们对生成的假设进行实时评估和调整，从而确保最终生成的假设更加符合实际科研需求.

**English:** As shown in Fig. 3, this study developed a human-machine collaborative hypothesis generation platform aimed at improving the efficiency and accuracy of researchers in the scientific hypothesis generation process. The platform consists of a function area and a dialogue area. In the function area, users can select the LLM backbone and literature retrieval source, and control the dialogue process among agents and summarize final conclusions. In the dialogue area, users can input the research topic or scientific question they wish to explore through a dialogue box, and the platform can autonomously carry out systematic literature retrieval, enhanced summarization, and generate preliminary scientific hypotheses based on the input. The platform allows researchers to monitor and manage the scientific hypotheses collaboratively generated by multiple agents in real time, and to intervene and adjust during the multi-agent dialogue process. The real-time monitoring function not only enables researchers to comprehensively understand the progress of hypothesis generation but also allows them to evaluate and adjust the generated hypotheses in real time, thereby ensuring that the final generated hypotheses better meet practical research needs.

---

<a id="F003"></a>
### Fig. 3. Human-Machine Collaboration Hypothesis Generation Platform

**Placed near:** p.7 S036
**Source:** p.7 (1645) C003

![Fig. 3](assets/fig3.png)

**原文图注 (Original caption):** 图3 人机协作假设生成平台

**English caption:** Fig. 3 Human-machine collaboration hypothesis generation platform

**Reading note:** This figure shows the user interface of the developed platform, with a function area (for selecting LLM backbone, literature retrieval source, and controlling dialogue) and a dialogue area (for inputting research topics). The platform enables real-time monitoring of multi-agent hypothesis generation.

---

## 3. 实验 (Experiments)

<a id="S037"></a>
**Source:** p.7 (1645) S037

**原文 (Original Chinese):** 本节将描述数据集、模型、评估设置和实施细节.

**English:** This section describes the dataset, models, evaluation setup, and implementation details.

### 3.1 实验设置 (Experimental Setup)

<a id="S038"></a>
**Source:** p.7 (1645) S038

**原文 (Original Chinese):** 通过 Semantic Scholar 的 API 接口获取实时的学术文献信息. 在 HILMA 框架中，使用 Qwen-Max 作为基座 LLMs，版本为 qwen-max-0403，top_k 设置为 0.8，温度（temperature）设置为 0.85. 本文以材料学科为例，让 20 名材料专业的研究生就各自的研究领域提出 5 个真实的研究问题，共获得 100 个不同的研究主题. 基于 100 个材料科学的研究问题，使用 3.2 节提到的基线模型生成对应的科学假设. 每个基线共获得 100 个科学假设用于评测，共计 600 个生成的科学假设用于评估.

**English:** Real-time academic literature information was obtained through the Semantic Scholar API. In the HILMA framework, Qwen-Max was used as the backbone LLM, version qwen-max-0403, with top_k set to 0.8 and temperature set to 0.85. Taking materials science as an example, 20 materials science graduate students each proposed 5 real research questions in their respective research areas, yielding a total of 100 distinct research topics. Based on these 100 materials science research questions, the baseline models mentioned in Section 3.2 were used to generate corresponding scientific hypotheses. Each baseline obtained 100 scientific hypotheses for evaluation, totaling 600 generated scientific hypotheses for assessment.

### 3.2 基线模型 (Baseline Models)

<a id="S039"></a>
**Source:** pp.7–8 (1645) S039

**原文 (Original Chinese):** 由于科学假设生成是一个全新任务，尚无直接可用的对比基线. 因此，将完整的 HILMA 框架与下列通用基线以及消融变体进行比较：

**English:** Since scientific hypothesis generation is a novel task with no directly available comparison baselines, the complete HILMA framework is compared with the following general baselines and ablation variants:

<a id="S040"></a>
**Source:** p.8 (1645) S040

**原文 (Original Chinese):** 1）ChatGPT [49]. ChatGPT 是由 OpenAI 开发的 LLMs，能够生成连贯且具有创造性的文本，广泛应用于对话系统、内容创作和文本生成任务. 本基线使用 ChatGPT 直接生成科学假设.

**English:** 1) ChatGPT [49]. ChatGPT is an LLM developed by OpenAI capable of generating coherent and creative text, widely applied in dialogue systems, content creation, and text generation tasks. This baseline uses ChatGPT to directly generate scientific hypotheses.

<a id="S041"></a>
**Source:** p.8 (1645) S041

**原文 (Original Chinese):** 2）CoT [50]. CoT（chain-of-thought）是一种提示工程方法，旨在引导 LLMs 逐步思考，以生成更加可靠的回答. 在实验中，本基线通过在提示词中加入逐步思考的指令，引导 LLMs 进行科学假设生成.

**English:** 2) CoT [50]. CoT (chain-of-thought) is a prompt engineering method designed to guide LLMs to think step by step to generate more reliable responses. In the experiments, this baseline guides LLMs in scientific hypothesis generation by incorporating step-by-step thinking instructions into the prompts.

<a id="S042"></a>
**Source:** p.8 (1645) S042

**原文 (Original Chinese):** 3）ICL [51]. ICL（in-context learning）是一种通过上下文提示进行学习和生成的技术，依赖于提供给模型的输入上下文，以便生成相关的输出. 在实验中，使用人工撰写的科学假设样例作为上下文提示，让模型参考这些示例生成科学假设.

**English:** 3) ICL [51]. ICL (in-context learning) is a technique for learning and generating through contextual prompts, relying on the input context provided to the model to generate relevant outputs. In the experiments, manually written scientific hypothesis examples are used as contextual prompts, enabling the model to reference these examples when generating scientific hypotheses.

<a id="S043"></a>
**Source:** p.8 (1645) S043

**原文 (Original Chinese):** 4）RAG. RAG（retrieval-augmented generation）是一种结合检索和生成的技术，通过在生成过程中动态检索相关文献来增强模型的生成能力. 通过主题关键词实时检索相关的科研论文摘要，选取前 10 篇提供给 LLMs 作为辅助参考. 这一方法能够在一定程度上缓解 LLMs 知识更新不及时的问题，提供更为新颖和前沿的科研信息.

**English:** 4) RAG. RAG (retrieval-augmented generation) is a technique combining retrieval and generation, enhancing the model's generation capability by dynamically retrieving relevant literature during the generation process. Relevant research paper abstracts are retrieved in real time using topic keywords, and the top 10 are provided to LLMs as auxiliary references. This method can alleviate, to some extent, the problem of outdated LLM knowledge and provide more novel and cutting-edge research information.

<a id="S044"></a>
**Source:** p.8 (1645) S044

**原文 (Original Chinese):** 5）Multi-agent. 多智能体系统通过多个具有不同角色和功能的智能体协同工作来实现复杂任务. 本研究设计了多智能体框架基线，其中不同的智能体负责不同的任务，包括假设提出者、批评者或中立分析师. 通过智能体之间的自动化协作和辩论，迭代生成科学假设. 本文方法旨在最大化利用集体智慧，提高假设的科学性和创新性.

**English:** 5) Multi-agent. Multi-agent systems accomplish complex tasks through the collaborative work of multiple agents with different roles and functions. This study designed a multi-agent framework baseline in which different agents are responsible for different tasks, including hypothesis proposer, critic, or neutral analyst. Through automated collaboration and debate among agents, scientific hypotheses are iteratively generated. This method aims to maximize the use of collective intelligence to improve the scientific rigor and innovativeness of hypotheses.

### 3.3 评估设置 (Evaluation Setup)

<a id="S045"></a>
**Source:** p.8 (1645–1646) S045

**原文 (Original Chinese):** 鉴于科学假设生成是一个新任务，没有已知基准可以衡量其生成质量. 因此，采用基于模型的自动评估与人类评估相结合的方法，来验证实验基准模型.

**English:** Given that scientific hypothesis generation is a new task without known benchmarks for measuring generation quality, a combined approach of model-based automatic evaluation and human evaluation is adopted to validate the experimental baseline models.

<a id="S046"></a>
**Source:** p.8 (1646) S046

**原文 (Original Chinese):** 1）基于模型的评估. 参考最近使用 LLM 判断输出文本质量的范式 [52-53]，使用 GPT-4 来判断生成的科学假设的质量. 以 5 个不同的标准衡量科学假设的质量，然后要求评估模型对每个标准的生成思路进行 5 点李克特量表评分 [54]. 表 1 中提供了专家制定的用于引导评估的详细标准和提示.

**English:** 1) Model-based evaluation. Following the recent paradigm of using LLMs to judge output text quality [52-53], GPT-4 is used to assess the quality of the generated scientific hypotheses. The quality of scientific hypotheses is measured against five different criteria, and the evaluation model is then asked to rate the generated ideas for each criterion on a 5-point Likert scale [54]. Table 1 provides the detailed criteria and prompts developed by experts to guide the evaluation.

<a id="S047"></a>
**Source:** p.8 (1646) S047

**原文 (Original Chinese):** 2）基于人类的评估. 类似于基于模型的评估，同一个主题下不同基线模型生成的科学假设将被两两配对，让人类评注者在 2 个隐去了模型信息的回答之间进行成对比较，选择质量更高的科学假设. 为了实现这一目标，本研究开发了在线评估平台，如图 4 所示，标注者登录平台后，平台会自动推送针对同一个主题的匿名答案对，评注者通过点击按钮即可实现标注，能够协同自动保存并统计评注者的偏好选择结果. 为了保证人类评估的质量，专家评注者均为熟悉该领域的硕士研究生与博士研究生，且至少发表过 1 篇学术论文，评估过程共由 5 位专家评注者进行.

**English:** 2) Human-based evaluation. Similar to the model-based evaluation, scientific hypotheses generated by different baseline models for the same topic are paired, and human annotators perform pairwise comparisons between two anonymized responses to select the higher-quality scientific hypothesis. To achieve this, this study developed an online evaluation platform, as shown in Fig. 4. After annotators log in to the platform, the platform automatically pushes anonymized answer pairs for the same topic; annotators can annotate by clicking buttons, and the platform collaboratively auto-saves and tallies the annotators' preference selection results. To ensure the quality of human evaluation, the expert annotators are all master's and doctoral students familiar with the field who have published at least one academic paper; the evaluation process was conducted by a total of five expert annotators.

---

<a id="T001"></a>
### Table 1. 5-Point Likert Scale Used in Model Evaluation

**Placed near:** p.8 S046
**Source:** p.8 (1646) C009

| 评估指标 (Metric) | 评分 (Score) | 描述 (Description) |
|:--|:--|:--|
| **创新性 (Innovativeness)** | 1 | 没有任何新颖之处，重复已有的研究成果 / No novelty; repeats existing research findings |
| | 2 | 有少量新颖之处，但大部分内容是已有知识的延伸 / Minor novelty; mostly an extension of existing knowledge |
| | 3 | 有一些新的观点或方法，但总体仍基于已有的框架 / Some new viewpoints or methods, but still largely based on existing frameworks |
| | 4 | 提出了较为新颖的观点或方法，有显著的创新点 / Relatively novel viewpoints or methods with significant innovations |
| | 5 | 极具创新性，提出了全新的观点或方法，可能引发领域内的重大变革 / Extremely innovative; proposes entirely new viewpoints or methods that could trigger major changes in the field |
| **实用性 (Practicality)** | 1 | 完全没有实际应用价值，难以转化为实际应用 / No practical application value; difficult to translate into practice |
| | 2 | 有一定的理论价值，但实际应用价值有限 / Some theoretical value, but limited practical application |
| | 3 | 有一定的实际应用潜力，但需进一步研究和验证 / Some practical application potential, but requires further research and validation |
| | 4 | 具备较高的实际应用价值，具有较好的转化前景 / High practical application value with good translation prospects |
| | 5 | 极具实际应用价值，能够迅速转化为具体应用并产生显著效益 / Extremely high practical value; can be rapidly translated into specific applications with significant benefits |
| **可行性 (Feasibility)** | 1 | 完全不可行，技术或资源方面难以实现 / Completely infeasible; difficult to realize technically or resource-wise |
| | 2 | 可行性较低，面临较大的技术或资源挑战 / Low feasibility; faces significant technical or resource challenges |
| | 3 | 有一定的可行性，但需要克服一些技术或资源障碍 / Some feasibility, but requires overcoming technical or resource barriers |
| | 4 | 基本可行，技术和资源要求在可控范围内 / Basically feasible; technical and resource requirements are within controllable range |
| | 5 | 完全可行，现有技术和资源可以支持其实现 / Completely feasible; existing technology and resources can support its implementation |
| **数据支持 (Data Support)** | 1 | 完全缺乏数据支持，无法验证假设 / Completely lacking data support; hypothesis cannot be verified |
| | 2 | 数据支持有限，无法充分验证假设 / Limited data support; cannot fully verify the hypothesis |
| | 3 | 有一定的数据支持，但不完全，需进一步数据验证 / Some data support, but incomplete; requires further data verification |
| | 4 | 有较充分的数据支持，能够验证假设的大部分内容 / Fairly sufficient data support; can verify most content of the hypothesis |
| | 5 | 数据支持非常充分，能够全面验证假设 / Very sufficient data support; can comprehensively verify the hypothesis |
| **理论基础 (Theoretical Foundation)** | 1 | 缺乏理论基础，无法与现有科学理论相一致 / Lacks theoretical foundation; cannot align with existing scientific theories |
| | 2 | 理论基础薄弱，与现有科学理论存在较大矛盾 / Weak theoretical foundation; has significant contradictions with existing theories |
| | 3 | 有一定的理论基础，但与现有科学理论存在一些不一致 / Some theoretical foundation, but has some inconsistencies with existing theories |
| | 4 | 具有较好的理论基础，能够与现有科学理论相结合 / Good theoretical foundation; can integrate with existing scientific theories |
| | 5 | 理论基础非常坚实，与现有科学理论完全一致，并有可能推动理论的发展 / Very solid theoretical foundation; fully consistent with existing theories and potentially advances theoretical development |
| **整体评价 (Overall Assessment)** | 1 | 整体评价很差，假设缺乏科学价值和实际意义 / Very poor overall; hypothesis lacks scientific value and practical significance |
| | 2 | 整体评价较差，假设存在较多不足之处 / Poor overall; hypothesis has many deficiencies |
| | 3 | 整体评价一般，假设有一定价值但需改进 / Average overall; hypothesis has some value but needs improvement |
| | 4 | 整体评价较好，假设具备较高的科学价值和实际意义 / Good overall; hypothesis has high scientific value and practical significance |
| | 5 | 整体评价非常好，假设具有重要的科学价值和实际意义 / Excellent overall; hypothesis has important scientific value and practical significance |

**原文表注 (Original caption):** 表1 模型评估中使用的 5 点李克特评分量表

**English caption:** Table 1 5-Point Likert Scale Used in Model Evaluation

---

<a id="F004"></a>
### Fig. 4. The Constructed Artificial Online Evaluation Platform

**Placed near:** p.8 S047
**Source:** p.8 (1646) C004

![Fig. 4](assets/fig4.png)

**原文图注 (Original caption):** 图4 构建的人工在线评测平台

**English caption:** Fig. 4 The constructed artificial online evaluation platform

**Reading note:** This figure shows the online evaluation platform interface used for pairwise comparison of anonymous scientific hypotheses generated by different models under the same research topic.

---

### 3.4 实验结果与分析 (Experimental Results and Analysis)

<a id="S048"></a>
**Source:** p.9 (1646) S048

**原文 (Original Chinese):** 为了比较本文模型与基准方法的效果差异，对生成的科学假设数据进行了基于 LLMs 的评分测试. 表 2 展示了不同基线模型李克特量表的 GPT-4 评分结果.

**English:** To compare the performance differences between the proposed model and baseline methods, LLM-based scoring tests were conducted on the generated scientific hypothesis data. Table 2 shows the GPT-4 scoring results on the Likert scale for different baseline models.

---

<a id="T002"></a>
### Table 2. Comparison of Different Baselines

**Placed near:** p.9 S048
**Source:** p.9 (1646) C010

| 模型 (Model) | 创新性 (Innov.) | 实用性 (Pract.) | 可行性 (Feas.) | 数据支持 (Data Sup.) | 理论基础 (Theory) | 总体评价 (Overall) |
|:--|:--|:--|:--|:--|:--|:--|
| ChatGPT | 3.29 | 3.41 | 2.80 | 2.27 | 3.27 | 3.07 |
| CoT | 3.81 | 3.98 | 2.94 | 2.37 | 3.64 | 3.32 |
| ICL | 4.09 | 4.07 | 3.21 | 2.60 | 3.72 | 3.70 |
| RAG | 4.10 | 3.94 | 3.18 | 2.65 | 3.80 | 3.61 |
| Multi-agent | 4.51 | 4.20 | 3.13 | 2.46 | 4.08 | 3.96 |
| **HILMA (本文)** | **4.60** | **4.25** | **3.40** | **2.80** | **4.20** | **4.10** |

*注：黑体数值表示最优值. (Note: Bold values indicate the best scores.)*

**原文表注 (Original caption):** 表2 不同基线模型对比

**English caption:** Table 2 Comparison of Different Baselines

---

<a id="S049"></a>
**Source:** p.9 (1646) S049

**原文 (Original Chinese):** 首先，从基线模型的整体评分来看，LLMs 生成的科学假设在实用性和理论基础方面取得了相对较高的分数，这主要归因于 LLMs 在海量文本上的预训练能够掌握大量基础理论和常识知识. 然而，在创新性、可行性和数据支持 3 个评分维度上效果不佳. 这是因为 LLMs 局限于已经见过的重复知识和模式，缺乏创新性思维，并且容易提出不切实际的想法，缺乏可行性和理论支持.

**English:** First, looking at the overall scores of the baseline models, the scientific hypotheses generated by LLMs achieved relatively high scores in practicality and theoretical foundation, mainly attributable to the fact that LLMs' pre-training on massive text enables them to grasp a large amount of foundational theory and common-sense knowledge. However, they performed poorly in the three scoring dimensions of innovativeness, feasibility, and data support. This is because LLMs are confined to repetitive knowledge and patterns they have already encountered, lack innovative thinking, and tend to propose impractical ideas lacking feasibility and theoretical support.

<a id="S050"></a>
**Source:** pp.9–10 (1646–1647) S050

**原文 (Original Chinese):** 其次，通过对比 CoT，ICL，ChatGPT 的表现，可以发现通过引导 LLMs 逐步思考和提供具体的科学假设样例，能够有效地提升生成假设的质量，这说明通用的 LLMs 能力提升方法对科学假设任务也是适用的；通过检索最新的相关文献，RAG 方法能够显著提升生成的科学假设质量，这得益于模型能够获取最新的科研进展，有效地提升了创新性和数据支撑评分，使得生成的科学假设具备前沿性和有效性. 此外，得益于多智能体迭代讨论，Multi-Agent 取得了更优的模型评分，说明通过最大化利用集体智慧，能够提高假设的科学性和创新性.

**English:** Second, by comparing the performance of CoT, ICL, and ChatGPT, it can be observed that guiding LLMs to think step by step and providing concrete scientific hypothesis examples can effectively improve the quality of generated hypotheses, indicating that general LLM capability enhancement methods are also applicable to the scientific hypothesis task. By retrieving the latest relevant literature, the RAG method can significantly improve the quality of generated scientific hypotheses, benefiting from the model's access to the latest research advances, which effectively enhances innovativeness and data support scores, making the generated hypotheses cutting-edge and effective. Furthermore, thanks to multi-agent iterative discussion, Multi-Agent achieved better model scores, demonstrating that maximizing the use of collective intelligence can improve the scientific rigor and innovativeness of hypotheses.

<a id="S051"></a>
**Source:** p.10 (1647) S051

**原文 (Original Chinese):** 本文的 HILMA 框架显著优于所有的基线模型，创新性评分达到了 4.6 分，总评分是所有基线中唯一突破 4 分的模型，达到了"具备较高的科学价值和实际意义"的标准. 实验结果表明通过充分利用人类与 LLMs 智能体各自的优势，有助于创造出符合科学标准且创新性强的科学假设. 此外，实验结果突出了人机协作的重要性，在这一过程中，人类专家负责提供方向性指导、深入分析和复杂决策，而 LLMs 则通过引文网络构建、多智能体迭代等不断优化假设，增强假设的适用性和准确性，确保生成的科学假设既有深度也有广度.

**English:** The HILMA framework proposed in this paper significantly outperforms all baseline models, with an innovativeness score reaching 4.6 and a total score that is the only one among all baselines to exceed 4 points, reaching the standard of "possessing high scientific value and practical significance." The experimental results demonstrate that by fully leveraging the respective strengths of humans and LLM agents, it is possible to create scientific hypotheses that meet scientific standards and possess strong innovativeness. Furthermore, the experimental results highlight the importance of human-machine collaboration; in this process, human experts are responsible for providing directional guidance, in-depth analysis, and complex decision-making, while LLMs continuously optimize hypotheses through citation network construction and multi-agent iteration, enhancing the applicability and accuracy of the hypotheses, ensuring that the generated scientific hypotheses possess both depth and breadth.

<a id="S052"></a>
**Source:** p.10 (1647) S052

**原文 (Original Chinese):** 为了进一步验证人机协作的重要性，首先使用 HILMA 框架生成了未经讨论的初始假设，然后基于此进行人机协作，迭代生成最终的科学假设，以对比二者的评分差异. 如图 5 所示，通过人机协作迭代能够在所有指标上显著提升模型的生成效果. 这是因为人类专家能够提供方向性指导，帮助 LLMs 进行复杂决策和启发新思路. 在人机迭代过程中，一些细节错误和假设不合理的地方也能够被及时发现和改正，进一步提升假设的整体质量.

**English:** To further verify the importance of human-machine collaboration, initial hypotheses were first generated using the HILMA framework without discussion, and then human-machine collaboration was conducted based on these to iteratively generate the final scientific hypotheses, comparing the score differences between the two. As shown in Fig. 5, human-machine collaborative iteration can significantly improve the model's generation performance across all metrics. This is because human experts can provide directional guidance, helping LLMs with complex decision-making and inspiring new ideas. During the human-machine iteration process, some detailed errors and unreasonable aspects of the hypotheses can also be promptly identified and corrected, further enhancing the overall quality of the hypotheses.

---

<a id="F005"></a>
### Fig. 5. Comparison of Initial Hypotheses and Hypotheses After Human-Machine Collaboration

**Placed near:** p.10 S052
**Source:** p.9 (1647) C005

![Fig. 5](assets/fig5.png)

**原文图注 (Original caption):** 图5 初始假设与人机协作后的假设对比

**English caption:** Fig. 5 Comparison of initial hypotheses and hypotheses after human-machine collaboration

**Reading note:** This bar chart compares the scores of initial hypotheses (blue) and hypotheses after human-machine collaboration (orange) across six evaluation metrics: innovativeness (创新性), practicality (实用性), feasibility (可行性), data support (数据支持), theoretical foundation (理论基础), and overall assessment (整体评价). Collaboration improves all metrics, with the overall score rising from approximately 3.10 to 4.11.

---

<a id="F006"></a>
### Fig. 6. Impact of Subgraph Citation Network Introduction on Generation Quality

**Placed near:** p.11 S053
**Source:** p.11 (1647) C006

![Fig. 6](assets/fig6.png)

**原文图注 (Original caption):** 图6 子图引文网络的引入对生成质量的影响

**English caption:** Fig. 6 Impact of subgraph citation network introduction on generation quality

**Reading note:** This radar chart compares hypothesis quality between "based on subgraph citation network" (blue) and "based on LLM itself" (orange) across innovativeness, practicality, feasibility, data support, theoretical foundation, and overall assessment. The subgraph citation network significantly enhances innovativeness and overall assessment.

---

<a id="S053"></a>
**Source:** p.11 (1647) S053

**原文 (Original Chinese):** 图 6 展示了基于子图引文网络生成的科学假设与基于 LLMs 本身的科学假设的雷达图对比. 经过了子图引文网络能够显著增强 LLMs 生成科学假设的创新性与总体评价，表明子图引文网络能够为 LLMs 提供最新的科学文献与研究进展，帮助 LLMs 从最新研究中探索创新思路与前沿方法.

**English:** Fig. 6 shows a radar chart comparison between scientific hypotheses generated based on the subgraph citation network and those based on LLMs alone. The subgraph citation network can significantly enhance the innovativeness and overall assessment of LLM-generated scientific hypotheses, indicating that the subgraph citation network can provide LLMs with the latest scientific literature and research advances, helping LLMs explore innovative ideas and cutting-edge methods from the latest research.

### 3.5 多步辩论评估 (Multi-Step Debate Evaluation)

<a id="S054"></a>
**Source:** p.11 (1647) S054

**原文 (Original Chinese):** 为验证多轮辩论迭代的效果，开展了多轮评估实验. 基于相同的初始假设，在不同的迭代轮次终止并生成科学假设，以观察其质量随迭代轮次的变化. 如图 7 所示，经过多轮迭代，Multi-agent 和 HILMA 方法的整体质量均有所提升，这是因为在多轮辩论中，假设中存在的明显缺陷和不足能够被发现和纠正.

**English:** To verify the effect of multi-round debate iteration, multi-round evaluation experiments were conducted. Based on the same initial hypotheses, the process was terminated at different iteration rounds to generate scientific hypotheses, observing how quality changes with iteration rounds. As shown in Fig. 7, after multiple rounds of iteration, both the Multi-agent and HILMA methods showed improvement in overall quality, because obvious flaws and deficiencies in the hypotheses could be discovered and corrected during multi-round debates.

<a id="S055"></a>
**Source:** p.11 (1647–1648) S055

**原文 (Original Chinese):** 然而，注意到 Multi-agent 方法在迭代 2 轮后质量有所提升，但在后续轮次中出现了停滞甚至下降的现象. 这主要是由于多智能体缺乏对科研的深刻理解，在讨论中容易集体跑偏，过度关注无关细节，忽略了科学假设的核心内容. 相比之下，HILMA 方法的假设质量随着迭代次数的增加表现出更高的稳定性. 人类专家的高阶洞见能够及时纠正讨论中的偏差，指出问题所在，不断提升科学假设的总体质量. 这突显了人机协作的重要性.

**English:** However, it was observed that the Multi-agent method showed quality improvement after two iterations, but experienced stagnation or even decline in subsequent rounds. This is mainly because multi-agents lack deep understanding of scientific research, tend to collectively drift off-topic during discussions, over-focus on irrelevant details, and neglect the core content of the scientific hypotheses. In contrast, the HILMA method exhibited higher stability in hypothesis quality as the number of iterations increased. The higher-order insights of human experts can promptly correct deviations in discussions, point out problems, and continuously improve the overall quality of scientific hypotheses. This highlights the importance of human-machine collaboration.

---

<a id="F007"></a>
### Fig. 7. Impact of Iteration Count on Human-Machine Collaboration

**Placed near:** p.11 S054–S055
**Source:** p.11 (1648) C007

![Fig. 7](assets/fig7.png)

**原文图注 (Original caption):** 图7 迭代次数对人机协作的影响

**English caption:** Fig. 7 Impact of iteration count on human-machine collaboration

**Reading note:** Two sub-figures showing: (a) Multi-agent score changes with iteration count -- scores rise then stagnate/decline after round 2; (b) HILMA score changes with iteration count -- scores show more stable improvement across rounds. The key finding is that HILMA (with human-in-the-loop) avoids the quality degradation seen in pure multi-agent debate.

---

### 3.6 不同基座模型评估 (Evaluation of Different Base Models)

<a id="S056"></a>
**Source:** pp.11–12 (1647–1648) S056

**原文 (Original Chinese):** 表 3 展示了 HILMA 在开源模型 Llama-3（Llama3-70B-Instruct [55]）、Qwen-72B（Qwen1.5-72B-Chat [56]）和闭源模型 GPT-3.5（GPT-3.5-Turbo [57]）、通义千问（Qwen-Max [58]）上的实验效果. 结果表明，生成的假设质量与模型本身的能力密切相关，基座模型越强，生成的假设质量越高. 其中，Qwen-Max 表现出最佳的效果.

**English:** Table 3 shows the experimental results of HILMA on the open-source models Llama-3 (Llama3-70B-Instruct [55]), Qwen-72B (Qwen1.5-72B-Chat [56]), and the closed-source models GPT-3.5 (GPT-3.5-Turbo [57]) and Tongyi Qianwen (Qwen-Max [58]). The results indicate that the quality of the generated hypotheses is closely related to the capability of the model itself: the stronger the base model, the higher the quality of the generated hypotheses. Among them, Qwen-Max demonstrated the best performance.

---

<a id="T003"></a>
### Table 3. Comparison of Different Large Language Models

**Placed near:** p.11 S056
**Source:** p.11 (1648) C011

| 基座模型 (Base Model) | 创新性 (Innov.) | 实用性 (Pract.) | 可行性 (Feas.) | 数据支持 (Data Sup.) | 理论基础 (Theory) | 整体评价 (Overall) |
|:--|:--|:--|:--|:--|:--|:--|
| GPT-3.5 | 4.05 | 4.01 | 3.12 | 2.45 | 3.69 | 3.57 |
| Llama-3 | 4.08 | 4.08 | 3.07 | 2.28 | 3.87 | 3.62 |
| Qwen-72B | 4.17 | 4.00 | 3.14 | 2.51 | 3.96 | 3.77 |
| **Qwen-Max** | **4.60** | **4.25** | **3.40** | **2.80** | **4.20** | **4.10** |

**原文表注 (Original caption):** 表3 不同大语言模型对比

**English caption:** Table 3 Comparison of Different Large Language Models

---

### 3.7 人类评估结果 (Human Evaluation Results)

<a id="S057"></a>
**Source:** p.12 (1648) S057

**原文 (Original Chinese):** 对基线模型进行人工评估，图 8 展示了不同模型初始假设与人机协作后假设的对比情况. 热力图展示了在人工评测中，两两模型评测的胜率.

**English:** Human evaluation was conducted on the baseline models. Fig. 8 shows the comparison between initial hypotheses of different models and hypotheses after human-machine collaboration. The heatmap displays the pairwise win rates of models in the human evaluation.

<a id="S058"></a>
**Source:** p.12 (1648) S058

**原文 (Original Chinese):** 如图 8 所示，HILMA 框架生成假设在与其他模型的对比中胜率显著，说明其整体质量优于其他基线模型. 在初始假设的对比中，ChatGPT，RAG，Multi-agent，HILMA 的质量依次递增，其中 HILMA 框架的初始假设质量最高. 这与 3.4 节的模型评估结果一致，进一步验证了 HILMA 框架在科学假设生成中的优越性和潜力.

**English:** As shown in Fig. 8, the hypotheses generated by the HILMA framework had a significantly high win rate in comparisons with other models, indicating that its overall quality is superior to other baseline models. In the comparison of initial hypotheses, the quality of ChatGPT, RAG, Multi-agent, and HILMA increased sequentially, with the HILMA framework having the highest initial hypothesis quality. This is consistent with the model evaluation results in Section 3.4, further validating the superiority and potential of the HILMA framework in scientific hypothesis generation.

---

<a id="F008"></a>
### Fig. 8. Heatmap of Model Win Rates Based on Human Evaluation

**Placed near:** p.12 S058
**Source:** p.12 (1648) C008

![Fig. 8](assets/fig8.png)

**原文图注 (Original caption):** 图8 基于人工评估的模型胜率热力图

**English caption:** Fig. 8 Heatmap of model win rates based on human evaluation

**Reading note:** The heatmap shows pairwise model comparison win rates. HILMA achieves the highest win rates: 0.85 vs ChatGPT, 0.72 vs RAG, 0.69 vs Multi-agent. The models listed in descending order of quality are: HILMA > Multi-agent > RAG > ChatGPT.

---

### 3.8 案例分析 (Case Study)

<a id="S059"></a>
**Source:** pp.12–13 (1648–1649) S059

**原文 (Original Chinese):** 表 4 展示了以"氮化硅陶瓷"为主题词，ChatGPT，RAG，Multi-agent，HILMA 生成的科学假设. 其中，ChatGPT 的假设提出了结合材料科学和电子工程的设计思路，但缺乏对如何实现这种结合的具体细节. RAG 通过检索增强的方法，提出了微系统的概念，但同样缺少具体的实施步骤和技术细节，使得这些假设在转化为研究方案时存在一定难度. 相比之下，Multi-agent 和 HILMA 生成的科学假设则更加具体且具有可操作性. Multi-agent 详细描述了化学合成、电化学技术、量子化学计算等实验方法，并提供了清晰的研究路径. HILMA 的假设则更为全面和深入，它提出了一种多级结构的氮化硅陶瓷复合材料设计，详细阐述了每一层级材料设计的方法，给出了预期的微观结构和性能提升的理论解释. 这些详细的方法和步骤使这一假设更容易转化为实际的科研实践，具备较高的可操作性和可实施性，更符合使用者的预期.

**English:** Table 4 presents the scientific hypotheses generated by ChatGPT, RAG, Multi-agent, and HILMA using "silicon nitride ceramics" as the research topic. Among them, ChatGPT's hypothesis proposed a design approach combining materials science and electronic engineering, but lacked specific details on how to achieve this combination. RAG, through the retrieval-augmented approach, proposed the concept of a microsystem, but similarly lacked concrete implementation steps and technical details, making these hypotheses difficult to translate into research plans. In contrast, the scientific hypotheses generated by Multi-agent and HILMA were more specific and actionable. Multi-agent described in detail experimental methods such as chemical synthesis, electrochemical techniques, and quantum chemical calculations, providing a clear research path. HILMA's hypothesis was even more comprehensive and in-depth, proposing a multi-level structured silicon nitride ceramic composite material design, elaborating in detail the methods for material design at each level, and providing theoretical explanations for the expected microstructures and performance improvements. These detailed methods and steps make this hypothesis easier to translate into practical scientific research, possessing high operability and implementability, and better meeting user expectations.

---

<a id="T004"></a>
### Table 4. Cases of Scientific Hypothesis Generation Taking "Silicon Nitride Ceramics" as the Research Topic

**Placed near:** p.12 S059
**Source:** pp.12–13 (1649) C012

| 模型 (Model) | 科学假设 (Scientific Hypothesis) |
|:--|:--|
| **ChatGPT** | 我建议在硅氮化陶瓷的研究中，结合材料科学和电子工程的领域. 利用电子工程中传感器技术和材料科学中的纳米结构设计原理，设计并研发一种新型的硅氮化陶瓷传感器. 该传感器可用于高温、高压或腐蚀性环境下的测量，并具有更高的灵敏度和精准度. 这一想法受到材料科学中硅氮化陶瓷的高温稳定性和电子工程中传感器技术的启发. (I suggest combining the fields of materials science and electronic engineering in the study of silicon nitride ceramics. Using sensor technology from electronic engineering and nanostructure design principles from materials science, design and develop a novel silicon nitride ceramic sensor. This sensor can be used for measurements in high-temperature, high-pressure, or corrosive environments, with higher sensitivity and precision. This idea is inspired by the high-temperature stability of silicon nitride ceramics in materials science and sensor technology in electronic engineering.) |
| **RAG** | 我提议开发一种集成的硅氮化物微系统，该系统利用辐射热交换和优化的热响应时间来提高传感器对温度变化的敏感性. 受上述关于自由站立硅氮化物膜热耦合特性的研究启发，我们可以设计微机械谐振器，其中辐射热交换被刻意管理和利用，以增强其作为温度传感器的性能. 通过精确控制膜的尺寸、厚度和发射率，可以调整辐射热交换在总热耦合中的贡献. 此外，结合高真空环境中的实验验证，我们可以创建一个模拟平台来预测和优化这些微系统的热噪声和频率噪声特性. 这样，我们不仅可以提高现有传感器的性能，还能为未来的温度感应和热管理应用开辟新途径. (I propose developing an integrated silicon nitride microsystem that utilizes radiative heat exchange and optimized thermal response time to improve sensor sensitivity to temperature changes. Inspired by the aforementioned research on thermal coupling characteristics of free-standing silicon nitride membranes, we can design micromechanical resonators in which radiative heat exchange is deliberately managed and utilized to enhance their performance as temperature sensors...) |
| **Multi-agent** | 我提议结合氮化硅陶瓷的研究和实验，探索其在腐蚀抑制领域的应用潜力. 氮化硅陶瓷具有优异的耐磨、耐腐蚀和高温稳定性，因此可以作为一种新型的腐蚀抑制材料，特别适用于极端环境下的金属保护. 首先，可以通过化学合成方法，制备不同形貌和结构的氮化硅陶瓷颗粒或涂层，并使用表征技术（如 SEM, TEM, XRD）对其进行详细的形貌和结构分析...其次，利用电化学技术（如 EIS 和 PDP），评估氮化硅陶瓷材料对金属表面腐蚀的抑制效果...进一步，结合量子化学计算方法（如 DFT），预测氮化硅陶瓷材料在不同腐蚀介质下的吸附行为和电子转移机制...最后，探索氮化硅陶瓷与其他腐蚀抑制剂的复合应用... (I propose combining research and experiments on silicon nitride ceramics to explore their application potential in the field of corrosion inhibition. Silicon nitride ceramics possess excellent wear resistance, corrosion resistance, and high-temperature stability, making them a novel corrosion inhibition material, particularly suitable for metal protection in extreme environments. First, through chemical synthesis methods, prepare silicon nitride ceramic particles or coatings with different morphologies and structures... Second, using electrochemical techniques (such as EIS and PDP), evaluate the corrosion inhibition effect... Furthermore, combining quantum chemical computation methods (such as DFT), predict adsorption behavior and electron transfer mechanisms... Finally, explore composite applications of silicon nitride ceramics with other corrosion inhibitors...) |
| **HILMA (本文)** | 我提议，通过设计一种多级结构的氮化硅陶瓷复合材料，该材料同时整合了微纳尺度的增强相和智能响应型腐蚀抑制剂，以实现超耐腐蚀、自适应修复及显著提高机械性能的革新目标. 此复合材料的核心设计包括以下几个层次：1) 基层优化. 首先，对氮化硅基层进行成分与微观结构的双重优化，采用 Y2O3 稳定的 alpha-Si3N4 为主相，结合溶胶-凝胶法制备的超细晶粒 (<500 nm)，以确保材料本体的高强度和高韧性...2) 微米级增强相分散. 在基层内均匀分散碳化硅 (SiC) 晶须或短纤维作为第 2 相增强材料...3) 纳米级智能抑制剂包覆. 在表面微结构层，将智能响应型有机抑制剂通过原位聚合法包覆在纳米粒子表面...4) 梯度功能涂层. 最外层采用 CVD 技术沉积一层梯度功能涂层...通过综合运用先进材料科学、纳米技术和智能材料设计理念，此多级结构氮化硅陶瓷复合材料有望在极端环境下展现前所未有的耐久性和可靠性，特别适用于航空航天、深海探索及高级能源系统等对材料性能要求极高的领域. (I propose designing a multi-level structured silicon nitride ceramic composite material that integrates micro/nano-scale reinforcing phases and smart responsive corrosion inhibitors to achieve the innovative goals of ultra-corrosion resistance, self-adaptive repair, and significantly improved mechanical properties. The core design of this composite material includes the following levels: 1) Base layer optimization. First, dual optimization of the composition and microstructure of the silicon nitride base layer, using Y2O3-stabilized alpha-Si3N4 as the main phase... 2) Micro-scale reinforcing phase dispersion. Uniformly disperse silicon carbide (SiC) whiskers or short fibers within the base layer as a second-phase reinforcing material... 3) Nano-scale smart inhibitor coating. On the surface microstructure layer, coat smart responsive organic inhibitors onto nanoparticle surfaces via in-situ polymerization... 4) Gradient functional coating. Deposit a gradient functional coating on the outermost layer using CVD technology... Through comprehensive application of advanced materials science, nanotechnology, and smart material design concepts, this multi-level structured silicon nitride ceramic composite material is expected to demonstrate unprecedented durability and reliability in extreme environments, particularly suitable for aerospace, deep-sea exploration, and advanced energy systems where material performance requirements are extremely high.) |

**原文表注 (Original caption):** 表4 以"氮化硅陶瓷"为研究主题的科学假设生成案例

**English caption:** Table 4 Cases of Scientific Hypothesis Generation Taking "Silicon Nitride Ceramics" as the Research Topic

---

## 4. 结论 (Conclusion)

<a id="S060"></a>
**Source:** p.13 (1648) S060

**原文 (Original Chinese):** 在当今科学研究不断发展的背景下，创新性假设的生成变得尤为重要. 然而，面对海量科学文献和复杂的跨学科知识体系，传统的科研方法在信息处理与知识整合方面面临巨大挑战. 本文提出了一种基于人机协作的多智能体科学假设生成框架 HILMA，通过结合结构智力理论中的发散思维和收敛思维，有效地提升了科学假设的生成质量和创新性. 实验结果表明，与现有的基线模型相比，HILMA 框架在生成高质量科学假设方面展现出了显著的优势. 这不仅在理论上验证了结构智力理论在科学研究中的应用价值，更在实践中证明了人机协作在科学创新中的潜力.

**English:** Against the backdrop of continuously advancing scientific research, the generation of innovative hypotheses has become particularly important. However, faced with massive scientific literature and complex interdisciplinary knowledge systems, traditional research methods face enormous challenges in information processing and knowledge integration. This paper proposes a human-machine collaborative multi-agent scientific hypothesis generation framework, HILMA, which effectively improves the generation quality and innovativeness of scientific hypotheses by integrating the divergent and convergent thinking principles from the theory of structural intelligence. Experimental results demonstrate that, compared with existing baseline models, the HILMA framework exhibits significant advantages in generating high-quality scientific hypotheses. This not only theoretically validates the application value of the theory of structural intelligence in scientific research but also practically demonstrates the potential of human-machine collaboration in scientific innovation.

<a id="S061"></a>
**Source:** p.13 (1648–1649) S061

**原文 (Original Chinese):** HILMA 结合了多智能体和人类协作，具备广泛的可扩展性，但仍然存在一些不足，主要体现在系统化检索效率与人机协调难度上. 为了让 LLMs 具备充足且系统化的知识，HILMA 需要对大量文献进行检索、筛选和总结，这一过程涉及多次的文献 API 检索和 LLMs 的调用，耗时较长，可能影响用户体验；在人机协作上，当前市面上可用的 LLMs 均为助理模型，存在过度倾向于满足人类指令的问题，因此，人类的微小意见可能对整个协作的走向和最终生成内容产生较大影响，进而影响科学假设的完整性. 因此，如何更好地均衡人类和多智能体之间的协作需要进一步的探索研究. 此外，虽然 HILMA 是通用的科学假设生成框架，但是受限于原始数据和评测条件，目前只在材料科学领域验证了 HILMA 的效果，并且缺少实验结果的支撑，需要结合材料合成实验来进一步验证科学假设的可行性和效果.

**English:** HILMA combines multi-agent and human collaboration with broad scalability, but still has some limitations, mainly manifested in systematic retrieval efficiency and the difficulty of human-machine coordination. To equip LLMs with sufficient and systematic knowledge, HILMA needs to retrieve, filter, and summarize a large volume of literature, a process involving multiple literature API retrievals and LLM invocations, which is time-consuming and may affect user experience. In terms of human-machine collaboration, the currently available LLMs on the market are all assistant models, which have the problem of being overly inclined to satisfy human instructions. Therefore, minor human opinions can have a significant impact on the direction of the entire collaboration and the final generated content, thereby affecting the completeness of scientific hypotheses. Thus, how to better balance the collaboration between humans and multi-agents requires further exploratory research. Additionally, although HILMA is a general scientific hypothesis generation framework, limited by the original data and evaluation conditions, its effectiveness has currently only been validated in the materials science domain, and it lacks experimental result support, requiring integration with materials synthesis experiments to further validate the feasibility and effectiveness of the scientific hypotheses.

<a id="S062"></a>
**Source:** pp.13–14 (1649) S062

**原文 (Original Chinese):** 未来，拓展 HILMA 框架至不同的学科领域将成为重点探索的方向. 鉴于不同学科在研究内容和方式上存在较大差异，单一框架难以在所有学科均取得理想效果. 从数据视角来看，医学影像、电子信号、语音学等在数据处理方面对图像、信号、音视频等有着巨大需求的专业，单纯的文本增强生成往往难以达成良好的成效. 探索如何利用多模态 LLMs 实现多模态的系统化检索增强，是一个值得深入研究的方向. 多元的数据能够进一步提升假设生成的可靠性和完整性. 此外，伴随各个学科的理论和技术不断相互交叉与融合，学科交叉已成为显著趋势. 如何针对不同领域构建专家智能体，针对同一课题分配多领域角色以实现学科交叉讨论，也将是一个值得深入探究的重要内容. 通过进一步优化人机协作机制和智能体辩论策略，科学研究的效率和创新性有望得到进一步提升，为解决复杂的科学问题和推动技术进步提供新的思路和方法.

**English:** In the future, expanding the HILMA framework to different disciplinary domains will be a key direction for exploration. Given the significant differences in research content and approaches across disciplines, a single framework is difficult to achieve ideal results in all disciplines. From a data perspective, disciplines such as medical imaging, electronic signals, and phonetics have enormous demands for processing images, signals, audio, and video; purely text-based enhanced generation often struggles to achieve good results. Exploring how to leverage multimodal LLMs to achieve multimodal systematic retrieval enhancement is a direction worthy of in-depth study. Diverse data can further improve the reliability and completeness of hypothesis generation. Furthermore, as theories and technologies from various disciplines continue to intersect and integrate, interdisciplinary fusion has become a prominent trend. How to construct expert agents for different domains and assign multi-domain roles for the same topic to achieve interdisciplinary discussion will also be an important area worthy of in-depth exploration. Through further optimization of human-machine collaboration mechanisms and agent debate strategies, the efficiency and innovativeness of scientific research are expected to be further improved, providing new ideas and methods for solving complex scientific problems and promoting technological progress.

<a id="S063"></a>
**Source:** p.14 (1649) S063

**原文 (Original Chinese):** 作者贡献声明：陈子阳提出了算法思路和实验方案，并撰写论文；赵翔提出指导意见，完成论文的修改和校对；赵润豪参与了文献调研和论文修订工作；倪子淇完成了文献调研、实验数据收集和论文修订工作；叶益聪提出指导意见.

**English:** **Author Contributions:** Chen Ziyang proposed the algorithmic approach and experimental plan, and wrote the paper; Zhao Xiang provided guidance and completed the revision and proofreading of the paper; Zhao Runhao participated in literature survey and paper revision; Ni Ziqi completed literature survey, experimental data collection, and paper revision; Ye Yicong provided guidance.

---

## 参考文献 (References)

<a id="R001"></a>
**Source:** pp.14–15 (1650–1651)

**[1]** Bornmann L, Haunschild R, Mutz R. Growth rates of modern science: A latent piecewise growth curve approach to model publication numbers from established and new literature databases[J]. Humanities and Social Sciences Communications, 2021, 8(1): 1-5

**[2]** Rothenberg A. The Janusian process in scientific creativity[J]. Creativity Research Journal, 1996, 9(2/3): 207-231

**[3]** Birhane A, Kasirzadeh A, Leslie D, et al. Science in the age of large language models[J]. Nature Reviews Physics, 2023, 5(5): 277-280

**[4]** Fakhoury S, Naik A, Sakkas G, et al. LLM-based test-driven interactive code generation: User study and empirical evaluation[J]. arXiv preprint, arXiv: 2404.10100, 2024

**[5]** Wu Yiquan, Zhou Siying, Liu Yifei, et al. Precedent-enhanced legal judgment prediction with LLM and domain-model collaboration[C]//Proc of the 2023 Conf on Empirical Methods in Natural Language Processing. Stroudsburg, PA: ACL, 2023: 12060-12075

**[6]** Thirunavukarasu A J, Ting D S, Elangovan K, et al. Large language models in medicine[J]. Nature Medicine, 2023, 29(8): 1930-1940

**[7]** Liu Yiheng, Han Tianle, Ma Siyuan, et al. Summary of ChatGPT-related research and perspective towards the future of large language models[J]. Meta-Radiology, 2023, 1(2): 1-14

**[8]** Meyer J G, Urbanowicz R J, Martin P C, et al. ChatGPT and large language models in academia: Opportunities and challenges[J]. BioData Mining, 2023, 16(1): 20-31

**[9]** Walsh E, Anders K, Hancock S, et al. Reclaiming creativity in the era of impact: Exploring ideas about creative research in science and engineering[J]. Studies in Higher Education, 2013, 38(9): 1259-1273

**[10]** Chen Ziyang, Li Dongfang, Zhao Xiang, et al. Temporal knowledge question answering via abstract reasoning induction[J]. arXiv preprint, arXiv: 2311.09149, 2023

**[11]** Ziems C, Held W, Shaikh O, et al. Can large language models transform computational social science?[J]. Computational Linguistics, 2024, 50(1): 237-291

**[12]** Guilford J P. The structure of intellect[J]. Psychological Bulletin, 1956, 53(4): 267-293

**[13]** Wang Hanchen, Fu Tianfan, Du Yuanqi, et al. Scientific discovery in the age of artificial intelligence[J]. Nature, 2023, 620(7972): 47-60

**[14]** Baek J, Jauhar S K, Cucerzan S, et al. ResearchAgent: Iterative research idea generation over scientific literature with large language models[J]. arXiv preprint, arXiv: 2404.07738, 2024

**[15]** Microsoft Research AI4Science and Microsoft Azure Quantum. The impact of large language models on scientific discovery: A preliminary study using GPT-4[J]. arXiv preprint, arXiv: 2311.07361, 2023

**[16]** Majumder B P, Surana H, Agarwal D, et al. Data-driven discovery with large generative models[J]. arXiv preprint, arXiv: 2402.13610, 2024

**[17]** Qi Biqing, Zhang Kaiyan, Li Haoxiang, et al. Large language models are zero shot hypothesis proposers[J]. arXiv preprint, arXiv: 2311.05965, 2023

**[18]** Shojaee P, Meidani K, Gupta S, et al. LLM-SR: Scientific equation discovery via programming with large language models[J]. arXiv preprint, arXiv: 2404.18400, 2024

**[19]** Lu C, Lu Cong, Lange R T, et al. The AI scientist: Towards fully automated open-ended scientific discovery[J]. arXiv preprint, arXiv: 2408.06292, 2024

**[20]** Li Yunxin, Hu Baotian, Shi Haoyuan, et al. VisionGraph: Leveraging large multimodal models for graph theory problems in visual context[J]. arXiv preprint, arXiv: 2405.04950, 2024

**[21]** Ji Ziwei, Lee N, Frieske R, et al. Survey of hallucination in natural language generation[J]. ACM Computing Surveys, 2023, 55(12): 1-38

**[22]** Shuster K, Spencer P, Chen M, et al. Retrieval augmentation reduces hallucination in conversation[C]//Proc of the 2021 Conf on Empirical Methods in Natural Language Processing. Stroudsburg, PA: ACL, 2021: 3784-3803

**[23]** Wang Mengru, Yao Yunzhi, Xi Zekun, et al. Safety analysis of large model content generation based on knowledge editing[J]. Journal of Computer Research and Development, 2024, 61(5): 1143-1155 (in Chinese) (王梦如，姚云志，习泽坤，等. 基于知识编辑的大语言模型内容生成安全分析[J]. 计算机研究与发展，2024，61(5)：1143-1155)

**[24]** Wang Cunxiang, Liu Xiaoze, Yue Yuanhao, et al. Survey on factuality in large language models: Knowledge, retrieval and domain-specificity[J]. arXiv preprint, arXiv: 2310.07521, 2023

**[25]** Xu Xinchao, Gou Zhibin, Wu Wenquan, et al. Long time no see! Open-domain conversation with long-term persona memory[C]//Proc of the 60th Association for Computational Linguistics. Stroudsburg, PA: ACL, 2022: 2639-2650

**[26]** Gao Yunfan, Xiong Yun, Gao Xinyu, et al. Retrieval-augmented generation for large language models: A survey[J]. arXiv preprint, arXiv: 2312.10997, 2023

**[27]** Lewis L, Perez E, Piktus A, et al. Retrieval-augmented generation for knowledge-intensive NLP tasks[C]//Proc of the 34th Conf on Advances in Neural Information Processing Systems. Cambridge, MA: MIT, 2020: 9459-9474

**[28]** Robertson S E, Zaragoza H. The probabilistic relevance framework: BM25 and beyond[J]. Foundations and Trends in Information Retrieval, 2009, 3(4): 333-389

**[29]** Wu H, Luk P W P, Wong K F, et al. Interpreting TF-IDF term weights as making relevance decisions[J]. ACM Transactions on Information Systems, 2008, 26(3): 1-37

**[30]** Guo Jiafeng, Cai Yinqiong, Fan Yixing, et al. Semantic models for the first-stage retrieval: A comprehensive review[J]. ACM Transactions on Information Systems, 2022, 40(4): 1-42

**[31]** Bruch S, Gai S, Ingber A. An analysis of fusion functions for hybrid retrieval[J]. ACM Transactions on Information Systems, 2023, 42(1): 1-35

**[32]** Li Hang, Mourad A, Zhuang Shengyao, et al. Pseudo relevance feedback with deep language models and dense retrievers: Successes and pitfalls[J]. ACM Transactions on Information Systems, 2023, 41(3): 1-40

**[33]** Shen Tao, Long Guodong, Geng Xiubo, et al. Large language models are strong zero-shot retriever[J]. arXiv preprint, arXiv: 2304.14233, 2023

**[34]** Ma Xueguang, Zhang Xinyu, Pradeep R, et al. Zero-shot listwise document reranking with a large language model[J]. arXiv preprint, arXiv: 2304.14233, 2023

**[35]** Sun Weiwei, Yan Lingyong, Ma Xinyu, et al. Is ChatGPT good at search? Investigating large language models as re-ranking agents[C]//Proc of the 2023 Conf on Empirical Methods in Natural Language Processing. Stroudsburg, PA: ACL, 2023: 14918-14937

**[36]** Jeong M, Sohn J, Sung M, et al. Improving medical reasoning through retrieval and self-reflection with retrieval-augmented large language models[J]. arXiv preprint, arXiv: 2401.15269, 2024

**[37]** Mousavi S M, Alghisi S, Riccardi G. Is your LLM outdated? Benchmarking LLMs & alignment algorithms for time-sensitive knowledge[J]. arXiv preprint, arXiv: 2404.08700, 2024

**[38]** Wang Z, Choi D, Xu Shenyu, et al. Putting humans in the natural language processing loop: A survey[J]. arXiv preprint, arXiv: 2103.04044, 2021

**[39]** Wu Xingjiao, Xiao Luwei, Sun Yixuan, et al. A survey of human-in-the-loop for machine learning[J]. Future Generation Computer Systems, 2022, 135: 364-381

**[40]** Cai Zefan, Chang Baobao, Han Wenjuan. Human-in-the-loop through chain-of-thought[J]. arXiv preprint, arXiv: 2306.07932, 2023

**[41]** Mehta N, Teruel M, Sanz P F, et al. Improving grounded language understanding in a collaborative environment by interacting with agents through help feedback[C]//Proc of the 62nd Association for Computational Linguistics. Stroudsburg, PA: ACL, 2024: 1306-1321

**[42]** Huang Wenlong, Xia Fei, Xiao T, et al. Inner monologue: Embodied reasoning through planning with language models[J]. arXiv preprint, arXiv: 2207.05608, 2022

**[43]** Wang Xingyao, Wang Zihan, Liu Jiateng, et al. MINT: Evaluating LLMs in multi-turn interaction with tools and language feedback[J]. arXiv preprint, arXiv: 2309.10691, 2023

**[44]** Feng Xueyang, Chen Zhiyuan, Qin Yujia, et al. Large language model-based human-agent collaboration for complex task solving[J]. arXiv preprint, arXiv: 2402.122914, 2024

**[45]** Dhillon P S, Molaei S, Li Jiaqi, et al. Shaping human-AI collaboration: Varied scaffolding levels in co-writing with language models[J]. arXiv preprint, arXiv: 2402.11723, 2024

**[46]** Li Ge, Peng Xin, Wang Qianxiang, et al. Challenges from LLMs as a natural language based human-machine collaborative tool for software development and evolution[J]. Journal of Software, 2023, 34(10): 4601-4606 (in Chinese) (李戈，彭鑫，王千祥，等. 大语言模型：基于自然交互的人机协同软件开发与演化工具带来的挑战[J]. 软件学报，2023，34(10)：4601-4606)

**[47]** Jin Dongming, Jin Zhi, Chen Xiaohong, et al. ChatModeler: A human-machine collaborative and iterative requirements elicitation and modeling approach via large language models[J]. Journal of Computer Research and Development, 2024, 61(2): 338-350 (in Chinese) (靳东明，金芝，陈小红，等. ChatModeler：基于大语言模型的人机协作迭代式需求获取和建模方法[J]. 计算机研究与发展，2024，61(2)：338-350)

**[48]** Ai2. Semantic Scholar API [EB/OL]. [2024-05-17]. https://www.semanticscholar.org/product/api

**[49]** OpenAI. ChatGPT [EB/OL]. [2024-05-17]. https://chat.openai.com

**[50]** Wei J, Wang Xuezhi, Schuurmans D, et al. Chain-of-thought prompting elicits reasoning in large language models[C]//Proc of the 36th Conf on Advances in Neural Information Processing Systems. Cambridge, MA: MIT, 2022: 24824-24837

**[51]** Min S, Lyu X, Holtzman A, et al. Rethinking the role of demonstrations: What makes in-context learning work[C]//Proc of the 2022 Conf on Empirical Methods in Natural Language Processing. Stroudsburg, PA: ACL, 2022: 11048-11064

**[52]** Zheng Lianmin, Chiang W, Sheng Ying, et al. Judging LLM-as-a-Judge with MT-Bench and chatbot arena[J]. arXiv preprint, arXiv: 2306.05685, 2023

**[53]** Fu Jinlan, Ng S K, Jiang Zhengbao, et al. Gptscore: Evaluate as you desire[J]. arXiv preprint, arXiv: 2302.04166, 2023

**[54]** Joshi A, Kale S, Chandel S, et al. Likert scale: Explored and explained[J]. British Journal of Applied Science & Technology, 2015, 7(4): 396-403

**[55]** Meta. Llama3-70B-Instruct[EB/OL]. [2024-05-10]. https://huggingface.co/meta-llama

**[56]** Alibaba. Qwen1.5-72B-Chat[EB/OL]. [2024-05-10]. https://huggingface.co/Qwen/Qwen1.5-72B-Chat

**[57]** OpenAI. GPT-3.5-Turbo[EB/OL]. [2024-05-10]. https://platform.openai.com/docs/models/gpt-3-5-turbo

**[58]** Alibaba. Qwen-Max API[EB/OL]. [2024-05-10]. https://help.aliyun.com/zh/dashscope/developer-reference

---

## 作者简介 (Author Biographies)

<a id="B001"></a>
**Source:** pp.14–15 (1651–1652)

**Chen Ziyang**, born in 1999. PhD candidate. Member of CCF. His main research interests include natural language processing, knowledge graph, and large language models.

**陈子阳**, 1999 年生. 博士研究生. CCF 会员. 主要研究方向为自然语言处理、知识图谱、大语言模型.

---

<a id="B002"></a>
**Source:** p.15 (1651)

**Zhao Xiang**, born in 1986. PhD, professor. Distinguished member of CCF. His main research areas include graph data management and analysis, knowledge graphs, and big data knowledge engineering.

**赵翔**, 1986 年生. 博士，教授. CCF 杰出会员. 主要研究方向为图数据管理与分析、知识图谱、大数据知识工程.

---

<a id="B003"></a>
**Source:** p.15 (1651)

**Zhao Runhao**, born in 2002. Master candidate. His main research interests include natural language processing, knowledge graph question answering, and data fusion.

**赵润豪**, 2002 年生. 硕士研究生. 主要研究方向为自然语言处理、知识图谱问答、数据融合.

---

<a id="B004"></a>
**Source:** p.15 (1652)

**Ni Ziqi**, born in 2000. PhD candidate. Her main research interests include materials informatics and energy storage ceramics.

**倪子淇**, 2000 年生. 博士研究生. 主要研究方向为材料信息学、储能陶瓷.

---

<a id="B005"></a>
**Source:** p.15 (1652)

**Ye Yicong**, born in 1985. PhD, professor. His main research interests include materials informatics and special metal materials.

**叶益聪**, 1985 年生. 博士，教授. 主要研究方向为材料信息学、特种金属材料.

---

## 术语对照表 (Terminology Table)

| 中文术语 | English Term | Notes |
|:--|:--|:--|
| 大语言模型 (LLMs) | Large Language Models | Core technology discussed throughout the paper |
| 科学假设生成 | Scientific Hypothesis Generation | The primary task addressed by HILMA |
| 多智能体 | Multi-Agent | Multiple AI agents collaborating/debating |
| 人机协作 | Human-Machine Collaboration / Human-in-the-Loop | Key paradigm of HILMA framework |
| 结构智力理论 | Theory of Structural Intelligence | J.P. Guilford's theory [12]; foundation of HILMA's approach |
| 发散思维 | Divergent Thinking | Generating multiple possible solutions from a problem |
| 收敛思维 | Convergent Thinking | Finding the specific correct answer to a problem |
| 引文网络 | Citation Network | Graph-based representation of literature citations |
| 子图引文网络 | Subgraph Citation Network | Citation network subgraph centered on a specific paper |
| 检索增强生成 (RAG) | Retrieval-Augmented Generation | Technique combining retrieval and generation |
| 思维链 (CoT) | Chain-of-Thought | Step-by-step reasoning prompt engineering |
| 上下文学习 (ICL) | In-Context Learning | Learning from provided examples in the prompt |
| 李克特量表 | Likert Scale | 5-point rating scale used for evaluation |
| 知识增强 | Knowledge Enhancement | Augmenting LLMs with external knowledge |
| 同行评审 | Peer Review | Scientific evaluation process simulated by agents |
| HILMA | Human-in-the-Loop Multi-Agent Framework | The proposed framework |
| 氮化硅陶瓷 | Silicon Nitride Ceramics | Case study research topic |
| 材料信息学 | Materials Informatics | Domain of case study application |

---

## 阅读提示 (Reading Notes)

### 1. Paper Overview

This paper proposes HILMA, a human-in-the-loop multi-agent framework for generating scientific hypotheses, grounded in Guilford's theory of structural intelligence (specifically divergent and convergent thinking). The framework was published in the Journal of Computer Research and Development (计算机研究与发展), Vol. 62, No. 7, 2025, a leading Chinese computer science journal.

### 2. Key Innovations

- **Citation Network Subgraph Construction**: A systematic two-phase approach (top-down subgraph construction + bottom-up review generation) that provides LLMs with structured, up-to-date scientific knowledge without expensive retraining.
- **Multi-Agent Debate with Human-in-the-Loop**: Simulates the scientific peer review process using role-assigned agents (proposer, reviewer, neutral analyst), with human experts guiding the debate direction and serving as arbitrators.
- **Integration of Divergent and Convergent Thinking**: The debate mechanism stimulates divergent thinking (generating diverse hypotheses), while human expert guidance enables convergent thinking (selecting and refining the most promising directions).

### 3. Important Findings

- HILMA is the only model achieving an overall score above 4.0 on the 5-point Likert scale (4.10), indicating "high scientific value and practical significance."
- Pure multi-agent debate (without human guidance) shows quality degradation after 2 rounds -- agents tend to "drift off-topic." Human experts are critical for maintaining quality across iterations.
- The subgraph citation network significantly boosts innovativeness and overall assessment scores compared to using LLMs alone.
- Model choice matters: stronger base LLMs produce better hypotheses (Qwen-Max > Qwen-72B > Llama-3 > GPT-3.5).

### 4. Limitations and Caveats

- Domain validation is limited to materials science (100 research topics from 20 graduate students). Cross-domain applicability remains to be verified.
- No wet-lab experimental validation -- generated hypotheses have not been tested through actual materials synthesis experiments.
- Retrieval and summarization pipeline is time-consuming due to multiple API calls.
- Current LLMs (all assistant-type models) tend to over-accommodate human instructions, which may bias the collaboration outcome.
- The evaluation uses GPT-4 as a judge for model-based assessment, which may introduce LLM-as-judge biases.

### 5. Suggested Reading Order

For a quick overview: Abstract -> Section 2 (HILMA Framework) -> Section 3.4 (Experimental Results) -> Conclusion.
For in-depth understanding: Introduction -> Related Work (Section 1) -> Full Section 2 -> Full Section 3 -> Conclusion.

### 6. Related Work to Explore

- [19] Lu et al., "The AI Scientist" (arXiv: 2408.06292) -- fully automated scientific discovery
- [14] Baek et al., "ResearchAgent" (arXiv: 2404.07738) -- iterative research idea generation
- [17] Qi et al., "LLMs are zero shot hypothesis proposers" (arXiv: 2311.05965)

### 7. Extraction Quality Notes

- The PDF source uses a two-column layout. Text was extracted using pdftotext with layout preservation. Some paragraph boundaries may have been reconstructed from the source.
- Figures are placeholders (assets/fig*.png). Original figure images were not extracted from the PDF.
- The English name "HILMA" may have been reconstructed; the paper's PDF rendering should be consulted for the exact acronym expansion.
- Text on overlapping elements (Fig. 5 axis labels) showed some extraction artifacts in the source.

---

*Generated on 2026-05-30. Source: Journal of Computer Research and Development, Vol. 62, No. 7, pp. 1639-1652, 2025. DOI: 10.7544/issn1000-1239.202440552.*
