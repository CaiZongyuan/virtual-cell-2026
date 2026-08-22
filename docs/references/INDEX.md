# 论文索引

本索引记录已检索或已评估的论文，帮助快速定位证据、方法和论文间关系。摘要为便于检索的中文概述，不替代原文。当前本地材料多数未保留规范出处；其 DOI、正式版本、年份和原文链接均标为待核验。初始盘点日期：2026-08-21。

## 关系图

```text
虚拟细胞愿景与评估
  -> Virtual Cells / AIVC priorities
  -> VC2025 Cell commentary -> STATE / CELL-EVAL -> PDS 距离与尺度分析
  -> 2026 比赛：未知细胞背景下的 CRISPRi 扰动预测

训练数据与表征
  -> scBaseCount -> scGPT / Stack

扰动状态转移与生成
  -> STATE / X-Cell / Lingshu-Cell / AlphaCell
  -> UniPert-G2CP（遗传扰动向化学扰动扩展）
  -> CellHermes（以语言统一多模态知识）
```

## VC2025 任务与指标

### Virtual Cell Challenge: Toward a Turing Test for the Virtual Cell

- 摘要：Arc 团队在 Cell 发表的竞赛评论，说明首届 Virtual Cell Challenge 以单细胞基因扰动响应预测为基准，目标是推动可在新细胞情境中泛化的虚拟细胞模型和标准化评估；此处为基于 DOI 元数据与官方页面的中文概述，不替代原文。
- 核心关联：VC2025 的同行评议任务定位来源；与官方数据页、评估页和赛后总结共同构成本项目学习上一届比赛的主要证据链。
- 关系：任务愿景由 STATE 的跨情境状态转移模型和 CELL-EVAL 进一步具体化；2026 比赛把 2025 的 H1 少样本设置推进到匿名背景零样本设置。
- 结论：采用为 VC2025 任务背景与愿景参考；具体数据、提交和最终评分仍以比赛期官方页面及代码为准。
- 关键词：Virtual Cell Challenge、Perturb-seq、CRISPRi、上下文泛化、评估基准。
- 来源：[DOI](https://doi.org/10.1016/j.cell.2025.06.008)；Roohani et al.；Cell 188(13), 3370-3374；2025；本地原文未保存（出版商 PDF 获取受限）；检索日期 2026-08-21。

### Effects of Distance Metrics and Scaling on the Perturbation Discrimination Score

- 摘要：作者分析高维基因表达中的扰动区分分数（PDS），指出 PDS 对距离度量和预测效应尺度敏感；L1/L2 与 cosine 类度量即使在范数匹配后也表现不同，并给出相应几何解释。此条转述自 arXiv 摘要和原文，不表示本项目已复现实验。
- 核心关联：直接解释 VC2025 第三名方案为何用交叉验证选择全局缩放优化 PDS，也提醒 VC2026 不能把区分分数等同于表达量校准或完整生物保真度。
- 关系：回应 STATE/CELL-EVAL 中的 PDS 设计；与 Arc VC2025 赛后总结对 PDS 尺度敏感性的讨论相互印证。
- 结论：采用为 PDS 指标性质的核心参考；其分析对象和结论迁移到 `cell-eval2/vcc2026` 六指标体系时仍需单独验证。
- 关键词：PDS、距离度量、缩放、高维几何、扰动预测、评估指标。
- 来源：[arXiv 摘要](https://arxiv.org/abs/2511.16954v1)；[PDF](https://arxiv.org/pdf/2511.16954v1)；Qiyuan Liu, Qirui Zhang, Jinhong Du, Siming Zhao, Jingshu Wang；arXiv:2511.16954v1；2025；本地核验文件 `liu-et-al-2025-pds-scaling-v1.pdf`（Git 忽略，不提交）；[MinerU Markdown 阅读版](liu-et-al-2025-pds-scaling-v1/liu-et-al-2025-pds-scaling-v1.md)（机器转换，字符、公式和引用以 PDF 为准）；检索日期 2026-08-21，转换日期 2026-08-22。

## 核心方法与直接竞赛关联

### Lingshu-Cell: Generative Cellular World Models for Transcriptomic Modeling

- 摘要：以掩码离散扩散直接学习约 18,000 个基因的转录组状态分布，并在身份和扰动条件下生成细胞；本地材料报告其在 Virtual Cell Challenge H1 基准上的表现。
- 核心关联：直接覆盖全转录组生成、细胞异质性和新“身份-扰动”组合，是比赛建模方案的重要参照。
- 关系：与 AlphaCell 同属生成式世界模型路线；与 STATE、X-Cell 都处理跨情境扰动泛化。
- 结论：采用为核心方法参考；复现实验与正式出处待核验。
- 关键词：离散扩散、全转录组、条件生成、细胞异质性、扰动预测。
- 来源：原文链接/DOI、版本、年份待核验；[本地材料](<Lingshu-Cell：面向虚拟细胞的转录组建模生成式细胞世界模型.md>)。

### STATE: Predicting Cellular Responses to Perturbation across Diverse Contexts

- 摘要：结合状态嵌入与集合层面的状态转移模型，从大规模观察性和扰动单细胞数据中学习跨细胞情境的扰动效应，并提出 CELL-EVAL 评估框架。
- 核心关联：比赛官方推荐背景模型，任务形式与未知细胞情境下的扰动响应预测高度一致。
- 关系：可作为 X-Cell、Lingshu-Cell、AlphaCell 的直接方法基线；CELL-EVAL 可补充竞赛指标分析。
- 结论：采用为核心方法与评估参考；优先核验代码、权重和许可。
- 关键词：状态转移、跨情境泛化、扰动效应、CELL-EVAL、集合建模。
- 来源：[DOI/bioRxiv](https://doi.org/10.1101/2025.06.26.661135)；Adduri et al.；bioRxiv 预印本；2025；本地原文未保存；[本地中文阅读材料](<使用 STATE 预测多样化情境下细胞对扰动的响应.md>)（转述材料，不替代原文）；检索日期 2026-08-21。

### X-Cell: Scaling Causal Perturbation Prediction across Diverse Cellular Contexts

- 摘要：在大规模 CRISPRi Perturb-seq 汇编 X-Atlas/Pisces 上训练扩散语言模型，并融合文本、蛋白、网络、依赖性和形态学先验以预测跨情境扰动响应。
- 核心关联：直接研究零样本跨细胞背景泛化，并讨论数据量、模型规模与预测性能的缩放关系。
- 关系：数据驱动规模化路线可与 STATE 的状态转移、Lingshu-Cell 的离散生成路线比较。
- 结论：采用为核心方法参考；数据和算力可获得性待评估。
- 关键词：CRISPRi、Perturb-seq、扩散语言模型、多模态先验、零样本、缩放律。
- 来源：原文链接/DOI、版本、年份待核验；[本地材料](<X-Cell：通过扩散语言模型扩展跨多样细胞情境的因果扰动预测.md>)。

### AlphaCell: Simulating Perturbation-Induced Cellular Dynamics

- 摘要：以全基因组潜在空间、知识丰富的解码器和条件流匹配统一建模连续细胞状态转移，目标是将扰动动力学迁移到未见细胞情境。
- 核心关联：覆盖全基因组重建、生成质量和组合泛化，可启发从对照分布到扰动分布的建模。
- 关系：与 Lingshu-Cell 都以“细胞世界模型”描述生成式模拟；与 STATE 都显式建模状态转移。
- 结论：采用为核心方法参考；复现成本与比赛格式适配待评估。
- 关键词：世界模型、流匹配、全基因组重建、连续状态转移、组合泛化。
- 来源：原文链接/DOI、版本、年份待核验；[本地材料](<迈向构建 AlphaCell 世界模型：模拟扰动诱导的细胞动力学.md>)。

### Stack: In-Context Learning of Single-Cell Biology

- 摘要：使用表格注意力在 1.49 亿个人类单细胞上学习上下文相关表征，让无标签上下文细胞在推理时充当示例，并预测条件对目标细胞群的影响。
- 核心关联：比赛提供大量未知背景的对照细胞，Stack 的上下文学习思路可能用于从这些细胞中适配背景。
- 关系：建立在大规模统一处理数据之上，与 scBaseCount 的数据路线、scGPT 的预训练路线相关。
- 结论：备选为细胞背景适配参考；需验证是否能输出比赛要求的扰动后原始计数分布。
- 关键词：上下文学习、表格注意力、单细胞基础模型、零样本、背景适配。
- 来源：原文链接/DOI、版本、年份待核验；[本地材料](<Stack_ In-Context Learning of Single-Cell Biology.md>)。

## 数据与基础表征

### scBaseCount

- 摘要：用 AI Agent 工作流发现并统一处理公开 10x scRNA-seq 原始读取，构建大规模、跨物种和组织的标准化单细胞计数资源。
- 核心关联：可扩展训练数据并减少处理流程差异，但使用前必须核对数据许可、物种、组织、化学平台和比赛任务匹配度。
- 关系：可为 scGPT、Stack 及扰动模型提供观察性预训练数据；自身不直接提供所有扰动标签。
- 结论：采用为候选观察性数据源；不替代 Perturb-seq 扰动训练数据。
- 关键词：数据图谱、原始计数、统一预处理、批次效应、训练数据。
- 来源：原文链接/DOI、版本、年份待核验；[本地材料](scBaseCount.md)。

### scGPT: Toward Building a Foundation Model for Single-Cell Multi-omics

- 摘要：在 3,300 多万个细胞上进行生成式 Transformer 预训练，联合学习基因与细胞表征，并迁移至注释、整合、扰动预测和基因网络推断等任务。
- 核心关联：提供基础模型和预训练表征基线，但需单独验证其在零样本 CRISPRi 分布预测上的能力。
- 关系：与 Stack 同属大规模单细胞预训练；可作为 STATE 等扰动模型的表征层参照。
- 结论：备选为预训练表征与基础模型基线。
- 关键词：Transformer、基础模型、迁移学习、基因表征、多组学。
- 来源：原文链接/DOI、版本、年份待核验；[本地材料](scGPT.md)。

## 愿景、评估与扩展路线

### Virtual Cells: Predict, Explain, Discover

- 摘要：提出面向药物发现的虚拟细胞应既预测扰动后的功能反应，也解释关键生物分子相互作用，并以生物学基准和实验室在环推动发现。
- 核心关联：帮助判断竞赛分数之外的模型价值，并指导可解释性和后续实验验证。
- 关系：与 AIVC priorities 共同定义上层愿景；CELL-EVAL 提供更具体的评估实现方向。
- 结论：采用为项目愿景与评估原则参考，不作为直接算法基线。
- 关键词：虚拟细胞、药物发现、可解释性、生物学基准、实验室在环。
- 来源：原文链接/DOI、版本、年份待核验；[本地材料](<Virtual Cells 虚拟细胞：预测、解释、发现.md>)。

### How to Build the Virtual Cell with Artificial Intelligence: Priorities and Opportunities

- 摘要：将 AI 虚拟细胞定义为表示并模拟分子、细胞和组织多尺度状态的多模态大模型，并梳理数据、建模、评估和协作优先事项。
- 核心关联：建立项目的概念边界和长期路线，但不是 2026 比赛任务的具体算法说明。
- 关系：是 Virtual Cells 的互补愿景材料；为 CellHermes、UniPert 等多模态扩展提供背景。
- 结论：采用为领域背景与长期路线参考。
- 关键词：AIVC、多尺度、多模态、基础模型、开放科学。
- 来源：[DOI](https://doi.org/10.1016/j.cell.2024.11.015)；Bunne et al.；Cell 187(25), 7045-7063；正式发表版本，2024-12；[本地中文阅读材料](<如何利用人工智能构建虚拟细胞：优先事项与机遇.md>)（转述材料，不替代原文）；检索日期 2026-08-21。

### UniPert-G2CP

- 摘要：统一遗传与化学扰动因子的多模态表征，并把遗传筛选学到的表型效应迁移到数据更稀缺的化学筛选。
- 核心关联：比赛本身聚焦遗传扰动，但该工作可用于研究因果扰动表征、跨模态迁移和药物发现扩展。
- 关系：是比赛之外的扩展路线；可与 X-Cell 的多模态先验和跨情境泛化进行比较。
- 结论：备选为赛后跨模态扩展参考；当前不优先投入比赛实现。
- 关键词：遗传筛选、化学筛选、迁移学习、多模态扰动、因果建模。
- 来源：原文链接/DOI、版本、年份待核验；[本地材料](<UniPert-G2CP：从分子表征到表型建模，打通遗传筛选与化学筛选.md>)。

### CellHermes: Language Is All Omics Need

- 摘要：将转录组、蛋白互作网络等组学数据转成自然语言问答，并通过 LoRA 微调语言模型，使同一框架充当编码器、预测器和解释器。
- 核心关联：提供整合文本知识、多组学先验和机制解释的探索路线；其比赛直接收益仍需实证。
- 关系：与 X-Cell 都融合多模态生物先验；与 scGPT 相比更强调自然语言作为统一接口。
- 结论：备选为知识整合与解释路线；当前不作为核心预测方案。
- 关键词：生物语言模型、多组学、LoRA、问答、可解释性。
- 来源：原文链接/DOI、版本、年份待核验；[本地材料](<语言或许是组学所需的一切：利用 CellHermes 协调多模态数据以理解组学.md>)。

## 检索排除记录

### Self-evolving Artificial Intelligence Virtual Cells: A Closed-loop System from Multi-scale Modeling to Biomedical Applications

- 摘要：综述 AIVC 从多组学整合、多尺度建模发展到生成式智能体驱动的假设提出、虚拟扰动和闭环优化，并讨论药物发现、疾病机制与精准医学应用；摘要为作者摘要的中文概述。
- 核心关联：检索摘要提及 xTrimoSCPerturb，可作为赛后 AIVC 路线综述，但论文发表于 VC2025 结束之后，不能证明当年规则、结果或冠军方法细节。
- 关系：与 Bunne et al. 的 AIVC 愿景论文同属领域综述；比 VC2025 Cell commentary 更宽泛，也不是获奖方案原始论文。
- 结论：排除出 VC2025 核心证据链；备选为 2026 年领域进展综述，尚未全文评估。
- 关键词：AIVC、多尺度建模、多组学、生成式智能体、闭环系统、xTrimoSCPerturb。
- 来源：[DOI](https://doi.org/10.65457/CMJBM-2026-0006)；Hu et al.；Chinese Medical Journal BioMed；Crossref 正式发表日期 2026-07-27（Infra Scholar 返回 2026-01-01，日期冲突以 Crossref 元数据为当前依据）；本地原文未保存；检索日期 2026-08-21。

### Predicting Transcriptional Outcomes of Novel Multigene Perturbations with GEARS

- 摘要：GEARS 将深度学习与基因关系知识图结合，预测未在实验中出现的单基因及多基因扰动转录响应，并重点评估组合扰动和遗传互作；摘要为作者摘要的中文概述。
- 核心关联：属于单细胞遗传扰动预测的重要历史方法，可作为模型基线线索；它不记录 VC2025 的数据划分、评分实现或获奖方法。
- 关系：与 TxPert 都使用基因关系图促进分布外泛化；VC2025 只要求单基因扰动，因此 GEARS 的组合扰动主问题与比赛不完全相同。
- 结论：排除出 VC2025 事实证据链；备选为后续扰动预测基线，使用前需单独评估任务和数据适配性。
- 关键词：GEARS、知识图、Perturb-seq、多基因扰动、遗传互作、分布外预测。
- 来源：[DOI](https://doi.org/10.1038/s41587-023-01905-6)；Roohani, Huang & Leskovec；Nature Biotechnology 42, 927-935；正式发表版本，2023-08-17 在线发布、2024 卷期；本地原文未保存；检索日期 2026-08-21。

### Identifying Perturbations That Boost T-cell Infiltration into Tumours via Counterfactual Learning of Their Spatial Proteomic Profiles

- 摘要：作者以肿瘤空间蛋白组图像训练反事实模型，提出促进 T 细胞浸润的最小组合扰动，并在体外实验中验证部分候选；摘要为作者摘要的中文概述。
- 核心关联：虽同时出现“预测”和“扰动”，其输入是空间蛋白组、输出是 T 细胞浸润策略，不是 CRISPRi 后单细胞 RNA 原始计数预测。
- 关系：属于空间肿瘤生物学和反事实干预设计，与 VC2025 Perturb-seq 转录组基准只有上层概念联系。
- 结论：排除；任务、数据模态和输出均与 VC2025 不匹配。
- 关键词：空间蛋白组、T 细胞浸润、反事实学习、肿瘤、组合扰动、误匹配。
- 来源：[DOI](https://doi.org/10.1038/s41551-025-01357-0)；Wang et al.；Nature Biomedical Engineering；正式发表版本，2025-03-05；本地原文未保存；检索日期 2026-08-21。

### TxPert: Leveraging BiochemicalRelationships for Out-of-Distribution Transcriptomic Perturbation Prediction

- 摘要：TxPert 使用多种基因-基因知识网络，研究未见单基因扰动、未见双基因扰动和未见细胞系三类 OOD 转录响应预测，并扩展扰动模型评估框架；摘要为 Zenodo 作者说明的中文概述。
- 核心关联：未见细胞系的 OOD 设置与 VC2026 高度相关，但它不是 VC2025 第三名的 `TransPert`，也不能作为冠军方法来源。
- 关系：与 GEARS 同属知识图增强扰动预测；`TxPert` 与 `TransPert` 仅名称相近，后者是 Outlier 团队使用伪批量统计摘要和相似性聚合的 VC2025 方案。
- 结论：排除出 VC2025 获奖事实证据链；备选为 VC2026 方法候选，需阅读全文、代码和许可证后再决定是否采用。
- 关键词：TxPert、TransPert、名称消歧、知识图、OOD、跨细胞系、转录组扰动预测。
- 来源：Infra Scholar 返回 [Zenodo 概念 DOI 10.5281/zenodo.15348745](https://doi.org/10.5281/zenodo.15348745)、日期 2025-05-07；Zenodo 当前记录解析为 [10.5281/zenodo.15420279](https://doi.org/10.5281/zenodo.15420279)、Wilson Tu, Frederik Wenkel & Alisandra Kaye Denton、发布日期 2025-05-20；题名中的 `BiochemicalRelationships` 为源记录原样；本地原文未保存；检索日期 2026-08-21。

### Prediction of Off-target Specificity and Cell-specific Fitness of CRISPR-Cas System Using Attention Boosted Deep Learning and Network-based Gene Feature

- 摘要：作者结合序列 Transformer 特征、基因网络和细胞表达特征，预测 CRISPR-Cas9/Cas12a guide 的编辑效率、脱靶特异性和处理后细胞适应度；摘要为作者摘要的中文概述。
- 核心关联：它研究如何设计更安全有效的 sgRNA，而 VC2025 假定扰动已完成并要求预测全转录组响应；两者的预测目标不同。
- 关系：可解释为什么 guide 质量和细胞背景会影响实验，但不是 Perturb-seq 状态转移模型或比赛评分来源。
- 结论：排除；属于 CRISPR guide 设计和脱靶预测，不属于本次 VC2025 学习的核心任务。
- 关键词：CRISPR-Cas9、CRISPR-Cas12a、sgRNA、脱靶、编辑效率、细胞适应度。
- 来源：[DOI](https://doi.org/10.1371/journal.pcbi.1007480)；Liu, He & Xie；PLoS Computational Biology 15(10)；正式发表版本，2019-10-28；本地原文未保存；检索日期 2026-08-21。

### The Manatee Variational Autoencoder Model for Predicting Gene Expression Alterations Caused by Transcription Factor Perturbations

- 摘要：Manatee 使用变分自编码器预测转录因子扰动诱导的转录组，并通过 in silico screening 筛选可驱动目标细胞谱的转录因子组合；摘要为作者摘要的中文概述。
- 核心关联：同样预测扰动后的基因表达，可作为较窄的转录因子扰动方法背景；它未提供 VC2025 规则、数据或冠军方案信息。
- 关系：与 GEARS 都覆盖未完全观测的扰动结果，但 Manatee 聚焦转录因子和目标表型，VC2025 目标面板及评分要求更广。
- 结论：排除出 VC2025 事实证据链；备选方法背景，尚未评估其是否能生成比赛要求的单细胞全基因计数分布。
- 关键词：Manatee、变分自编码器、转录因子、in silico perturbation、基因表达、组合筛选。
- 来源：[DOI](https://doi.org/10.1038/s41598-024-62620-z)；Yang et al.；Scientific Reports 14；正式发表版本，2024-05-23；本地原文未保存；检索日期 2026-08-21。

### Large Language Models in Bioinformatics: A Survey

- 摘要：综述大语言模型在生物信息学中的表示学习、迁移和生成应用，其中简要覆盖 scGPT 等单细胞模型及细胞注释、扰动预测和批次校正；Infra Scholar 返回的“摘要”实为正文片段，因此这里只作检索内容概述。
- 核心关联：可提供宽泛的模型背景，但不是单细胞扰动预测的原始研究，也不包含 VC2025 的一手规则或结果。
- 关系：与本索引的 scGPT 条目存在方法背景关系；对比赛方案的证据强度低于模型论文、官方页面和代码。
- 结论：排除；范围过宽且为二手综述，不进入 VC2025 核心证据链。
- 关键词：大语言模型、生物信息学、综述、scGPT、单细胞、扰动预测。
- 来源：[DOI](https://doi.org/10.18653/v1/2025.findings-acl.184)；Wang et al.；Findings of ACL 2025；正式会议论文，2025；本地原文未保存；检索日期 2026-08-21。

### VC2025 定向检索审计说明

- 唯一查询共 2 个：`Arc Institute Virtual Cell Challenge 2025 xTrimoSCPerturb TransPert perturbation prediction` 与 `"Effects of Distance Metrics and Scaling on the Perturbation Discrimination Score"`。
- 首次查询的原始 JSON 当时未保存。为满足逐篇审计要求，2026-08-21 原样重放首次查询 1 次；截至本条更新，共发生 3 次 Scholar API 请求，但仍只有 2 个唯一查询。重放返回 10 条，均已逐篇记录：Roohani et al.、STATE 和 Bunne et al. 分别位于前文已有条目，其余 7 条位于本节。
- Scholar 结果会随索引更新而变化；本次重放没有返回此前合并说明中提到的燃料电池结果，因此删除该无法恢复到具体题名和 URL 的泛称，不把未能证明实际评估过的纯 API 噪声伪造为论文记录。
- 第二个查询采用的 PDS 论文已在“VC2025 任务与指标”中独立记录。搜索结果只用于候选发现；采用的关键结论仍回到 DOI、出版页、预印本、官方文档或代码核验。

### 2026-08-22 检索栈基准测试

- 目的：比较项目内可用的论文检索 Skill 和 API，确定默认路由、补充源和失败回退；不评审论文科学结论。
- 查询：`zero-shot single-cell perturbation prediction unseen cell context`、用于 SciVerse evidence retrieval 的语义等价自然语言问题，以及 STATE 的完整题名/DOI 精确查找。
- 来源：Infra Scholar、SciVerse meta/agentic search、Paper Schema、OpenAlex fallback、OpenCLI arXiv/PubMed/Semantic Scholar；调用次数、结果质量和错误见 [基准记录](../research/literature-search-stack-benchmark.md)。
- 处理：本次只把返回结果用于检索器相关性评估，未据搜索摘要新增项目结论；实际进入后续方案判断的论文仍须按本索引模板逐篇登记。

## 新增记录模板

新增或重新评估论文时，复制以下字段并补全；即使排除也保留记录和理由。

```markdown
### 规范标题

- 摘要：
- 核心关联：
- 关系：
- 结论：采用 / 备选 / 排除；理由：
- 关键词：
- 来源：原文 URL；DOI；版本/年份；本地原文；检索日期 YYYY-MM-DD。
```
