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

### AIDO Cell: A General-Purpose Simulator for Cell Biology

- 摘要：GenBio AI 介绍具备持久细胞状态、连续扰动、分支轨迹、多尺度多模态读出和分子设计能力的 AIDO Cell；v1.0 提供 K-562 与 Hep-G2 原型。此条为技术报告原文概述，不表示本项目已独立验证平台能力或精度。
- 核心关联：其基因敲除、敲低和过表达接口，以及对可持续更新细胞状态的强调，可作为 VC2026 单步 CRISPRi 原始计数预测之外的长期系统设计参照。
- 关系：与 Lingshu-Cell、AlphaCell 同属细胞世界模型路线；报告也比较了扰动预测、基础模型与机制模拟器，但其产品级多模态模拟范围明显宽于当前比赛任务。
- 结论：采用为 AIDO Cell 一手技术资料；具体 benchmark 结果和跨模态能力仍需结合公开数据、代码与独立评估核验。
- 关键词：AIDO Cell、世界模型、持久细胞状态、连续扰动、多模态读出、K-562、Hep-G2。
- 来源：[公开 PDF](https://genbio.ai/research/AIDO%20Cell%20V1%20-%20Technical%20Report%20-%2018%20Aug%202026.pdf)；GenBio AI Team；technical report v1.0；2026-08-18；本地 PDF 仅作核验且由 Git 忽略；[MinerU Markdown 阅读版](aido-cell-v1/aido-cell-v1.md)（机器转换，字符、公式、图表和引用以 PDF 为准）；未发现独立 SI，报告附录已包含在正文 PDF；获取与转换日期 2026-08-30。

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
- 结论：采用为核心方法与 NTC-only 测试时适配的论文证据；当前不能作为可运行主线。2026-08-30 核查未发现公开 GitHub 仓库，Hugging Face 模型页只有 README、概览图和属性文件，没有权重或数据。
- 关键词：CRISPRi、Perturb-seq、扩散语言模型、多模态先验、零样本、缩放律。
- 来源：[DOI/bioRxiv](https://doi.org/10.64898/2026.03.18.712807)；[Hugging Face 占位页](https://huggingface.co/Xaira-Therapeutics/X-Cell)；Wang et al.；bioRxiv 预印本 v1，2026-03-20；[本地中文阅读材料](<X-Cell：通过扩散语言模型扩展跨多样细胞情境的因果扰动预测.md>)（转述材料，不替代原文）；标识与公开资产核验日期 2026-08-30。

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
- 结论：备选为细胞背景适配参考；用于有奖金竞赛前存在明确许可门。官方代码为 CC BY-NC-SA 4.0，模型权重和输出许可把直接或间接 monetary compensation 排除在 Non-Commercial Purpose 之外；VC2026 FAQ 对 STATE 有专项解释，但未对 Stack 给出同样例外，因此须取得 Arc 书面确认后才能把 Stack 纳入提交候选。
- 关键词：上下文学习、表格注意力、单细胞基础模型、零样本、背景适配。
- 来源：[DOI/bioRxiv](https://doi.org/10.64898/2026.01.09.698608)；[官方代码与 README](https://github.com/ArcInstitute/stack)；[模型许可](https://github.com/ArcInstitute/stack/blob/main/MODEL_LICENSE.md)；Dong et al.；bioRxiv 预印本，2026（Crossref 首发标识 2026-01-09，bioRxiv 页面版本日期 2026-06-08）；[本地中文阅读材料](<Stack_ In-Context Learning of Single-Cell Biology.md>)（转述材料，不替代原文）；代码、标识与许可核验日期 2026-08-30。

## 基准与可迁移建模证据

### Deep-learning-based gene perturbation effect prediction does not yet outperform simple linear baselines

- 摘要：作者在 Norman 双扰动以及 Adamson、Replogle K562/RPE1 单扰动数据上，将 5 个单细胞基础模型和 GEARS、CPA 与无变化、均值、加性及低秩线性基线比较；其评测中没有一个深度模型稳定优于相应简单基线。对于未见单基因扰动，使用另一细胞系 Perturb-seq 学得的扰动表示可提高线性模型，观察性单细胞预训练表示的收益则有限。此条来自同行评议原文，不把论文使用的 L2/Pearson 指标等同于 VC2026 六指标。
- 核心关联：直接支持“先建立均值、线性和跨背景 target-effect 基线，再以冻结的跨背景协议决定是否升级模型”；也说明扰动数据预训练比只用观察性图谱预训练更接近当前任务的信息需求。
- 关系：与 Csendes et al. 的独立 benchmark 结论一致；Molina and Zhang 进一步把简单模型为何有效拆成共享、目标、背景和交互响应分量；STATE 则报告在其多情境协议下能够超过线性基线，两者应在同一 VC2026-like LOCO 协议中实证比较。
- 结论：采用为基线设计和复杂度晋级门的核心证据；不能从其同背景未见扰动实验推出匿名新背景表现，也不能直接推出任何模型的 VC2026 排名。
- 关键词：Perturb-seq、CRISPRi、未见扰动、线性基线、均值基线、基础模型、benchmark。
- 来源：[DOI](https://doi.org/10.1038/s41592-025-02772-6)；[PubMed Central 全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC12328236/)；Ahlmann-Eltze, Huber and Anders；Nature Methods 22, 1657-1661；2025；本地原文未保存；原文与元数据核验日期 2026-08-30。

### Perturbation response decomposition enables biologically aligned generalization to unseen perturbations and cellular contexts

- 摘要：作者把 CRISPRi 伪批量响应分解为全局、扰动特异、细胞系特异和 `perturbation x cell line` 交互分量，并在 Replogle-Nadig 的四个细胞系中分析各分量的结构和可预测性。论文报告共享模板是低维的，目标与背景特异残差更高维；将 DepMap 共必需性先验直接对齐到响应空间的 Ridge/MLP 可在多种留出设置中匹配或超过更复杂模型。
- 核心关联：任务形式直接包含未见细胞系和未见目标组合，支持把 VC2026 主模型写成“当前 NTC 基线 + 共享 target effect + 背景模板/幅度 + 低秩交互”，并为每个分量选择与其信息需求相符的输入，而不是端到端增加模型容量。
- 关系：为本索引中的 STATE、X-Cell 与线性基线提供共同诊断坐标；与 Ahlmann-Eltze et al. 的简单基线结论互补，也与 Shoeibi and Yousefi 对响应幅度应显式建模的结果方向一致。
- 结论：采用为当前跨背景方案的直接方法证据，但证据级别仍为未同行评议预印本；主要实验是富集必需基因的四个 CRISPRi screen 和伪批量终点，不能证明单细胞计数生成或 VC2026 六指标上的收益。
- 关键词：响应分解、CRISPRi、未见细胞背景、未见扰动、DepMap、共必需性、Ridge、MLP、伪批量。
- 来源：[DOI/bioRxiv](https://doi.org/10.64898/2026.07.24.740459)；[代码](https://github.com/xinyizhanglab/perturbation-decomposition)；Alexis Molina and Xinyi Zhang；bioRxiv 预印本，2026-07-27；代码仓库未声明 license；PDF 仅在系统临时目录作本次核验，未入库；原文、元数据和代码入口核验日期 2026-08-30。

### PerturbNet predicts single-cell responses to unseen chemical and genetic perturbations

- 摘要：PerturbNet 以条件可逆神经网络生成扰动后的单细胞状态分布，并用化学结构或基因功能注释表示训练中未见的扰动。作者在其化学、CRISPRa/CRISPRi 和编码变异任务中报告相对基线的改进；此处为同行评议原文概述，不把其自报指标迁移成 VC2026 性能。
- 核心关联：支持测试 GO/功能注释等 target prior，并提供“预测分布而非只预测均值”的生成模型候选。
- 关系：与 X-Cell、Molina and Zhang 都强调 target prior；与 VC2026 的关键差别是最终轮同时留出 target-context 组合和整个细胞背景。
- 结论：备选，不作为主模型。作者在 Discussion 中明确指出 PerturbNet 不能预测“未见扰动在未见细胞类型中的效应”，正好是 VC2026 最关键的双重外推；其价值应拆成 target encoder 或 count-generator 消融，而不是直接声称端到端适配。
- 关键词：PerturbNet、CRISPRi、CRISPRa、未见扰动、功能注释、条件可逆神经网络、单细胞分布。
- 来源：[DOI](https://doi.org/10.1038/s44320-025-00131-3)；[PubMed Central 全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC12322087/)；Yu, Qian, Song and Welch；Molecular Systems Biology 21, 960-982；正式发表，2025-07-10；本地原文未保存；原文与元数据核验日期 2026-08-30。

### Benchmarking foundation cell models for post-perturbation RNA-seq prediction

- 摘要：作者在 Adamson、Norman、Replogle K562/RPE1 上比较 scGPT、scFoundation 与均值、Elastic Net、kNN、Random Forest 基线；在其未见扰动和 Pearson-delta 协议中，训练集均值优于两个基础模型，带 GO 或文本基因特征的 Random Forest 进一步提高。论文也指出常用数据的扰动间方差偏低会放大 benchmark 误读。
- 核心关联：支持保留强均值和生物特征基线，并要求先看 delta 与目标区分而不是原始表达相关性；其结果不能直接替代匿名背景留出的验证。
- 关系：与 Ahlmann-Eltze et al. 独立得到相近结论；与 Palla et al. 的表格模型路线共同提示高维响应可先投影后用强回归器处理。
- 结论：备选为基线与评估设计证据；实验主要是同一细胞系内留出目标，使用的 Pearson 指标不是 VC2026 六指标，因此不作为跨背景性能的一手证明。
- 关键词：scGPT、scFoundation、均值基线、Random Forest、Gene Ontology、未见扰动、Pearson delta。
- 来源：[DOI](https://doi.org/10.1186/s12864-025-11600-2)；[PubMed Central 全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC12016270/)；Csendes et al.；BMC Genomics 26, 393；2025；本地原文未保存；原文与元数据核验日期 2026-08-30。

### Tabular Foundation Models Are Competitive Cellular Perturbation Predictors Across Biological Scales

- 摘要：作者以 PCA/低秩输出表示配合 TabPFN、TabICL 等表格回归器，在细胞级跨细胞类型、五个 Perturb-seq 伪批量未见扰动和其他尺度任务上与专用模型比较，并报告强竞争力。其细胞级跨背景实验使用药物扰动 OpenProblems 数据，伪批量 CRISPR 数据实验主要留出目标，而非 VC2026 的未见 CRISPRi 细胞系与目标双重留出。
- 核心关联：提供一个成本较低的候选：先预测少量高方差响应分量，再重建全基因响应；适合在 Ridge/GBDT 之后作为相同特征、相同 split 下的受控升级。
- 关系：与 Molina and Zhang 的低维对齐观点、Csendes et al. 的表格基线结果相呼应；不能据此认为 TabPFN 已在 VC2026 同构任务上优于 STATE。
- 结论：备选；预印本尚未同行评议且核心 benchmark 与比赛存在扰动模态或留出轴差异，不进入默认主模型。
- 关键词：TabPFN、TabICL、PCA、表格基础模型、跨细胞类型、Perturb-seq、伪批量。
- 来源：[DOI/bioRxiv](https://doi.org/10.64898/2026.06.28.735106)；Giovanni Palla et al.；bioRxiv 预印本，2026-07-19；PDF 仅在系统临时目录作本次核验，未入库；原文与元数据核验日期 2026-08-30。

### Response Magnitude as a Dominant Signal for Held-Out CRISPRi Perturbation Effect Prediction

- 摘要：作者在 VC2025 H1 的严格目标留出和两个外部 CRISPRi screen 上研究一个标量终点，报告四个确定性响应幅度特征的线性/树模型优于所测试的 MLP 编码器，并强调幅度与方向应分开建模。
- 核心关联：支持为下游表达方向和效应幅度建立独立预测头，并把幅度校准作为 MSE、差异表达集合和 LFC 指标的受控消融，而不是依赖深层编码器自行恢复尺度。
- 关系：与 Molina and Zhang 的分量化建模方向一致；其终点是 log Anderson-Darling 距离，不是 18,533 基因原始计数或 VC2026 六指标。
- 结论：备选为幅度建模假设来源；仅为 arXiv 预印本，模型族和终点范围有限，不作为完整转录组方案的性能证据。
- 关键词：响应幅度、CRISPRi、目标留出、VC2025、线性回归、Random Forest、跨背景迁移。
- 来源：[arXiv:2608.00152v1](https://arxiv.org/abs/2608.00152v1)；Mehrdad Shoeibi and Niloofar Yousefi；2026-07-31；PDF 仅在系统临时目录作本次核验，未入库；原文与 arXiv 元数据核验日期 2026-08-30。

## 数据与基础表征

### Transcript-specific Enrichment Enables Profiling Rare Cell States via scRNA-seq

- 摘要：作者提出 PERFF-seq，用 RNA Flow-FISH 对特定转录本定义的稀有细胞群进行富集，再使用 10x Single Cell Gene Expression Flex 获取单细胞表达；摘要为原文概述。论文的 assay rationale 明确说明 Flex 使用全转录组探针对，通过相邻杂交和随后连接检测、定量固定细胞中的转录本；扩展图进一步展示探针杂交、连接产物和 bead oligo extension。
- 核心关联：用于核验 VC2026 教程中 10x Flex 的检测信息链，解释比赛原始计数为什么来自探针连接和 UMI 去重，而不能照搬传统 3' scRNA-seq 的 poly(A) 捕获流程。
- 关系：补充 Arc 官方页面只注明 `10x Flex`、但未展开分子检测过程的缺口；论文研究问题是稀有细胞富集，不是 CRISPRi 扰动预测，也不能证明 Arc 的具体试剂参数或实验批次设置。
- 结论：采用为 Flex 检测机制参考；仅采用原文明确描述的相邻探针杂交、连接和条形码信息链，不把 PERFF-seq 的富集结论迁移到比赛。
- 关键词：10x Flex、Fixed RNA Profiling、成对探针、相邻杂交、连接、UMI、PERFF-seq。
- 来源：[DOI](https://doi.org/10.1101/2024.03.27.587039)；[bioRxiv v1 全文](https://www.biorxiv.org/content/10.1101/2024.03.27.587039v1.full)；Abay et al.；bioRxiv 预印本 v1；2024-03-27；本地原文未保存；检索与核验日期 2026-08-30。

### scBaseCount

- 摘要：用 AI Agent 工作流发现并统一处理公开 10x scRNA-seq 原始读取，构建大规模、跨物种和组织的标准化单细胞计数资源。
- 核心关联：可扩展训练数据并减少处理流程差异，但使用前必须核对数据许可、物种、组织、化学平台和比赛任务匹配度。
- 关系：可为 scGPT、Stack 及扰动模型提供观察性预训练数据；自身不直接提供所有扰动标签。
- 结论：采用为候选观察性数据源；不替代 Perturb-seq 扰动训练数据。
- 关键词：数据图谱、原始计数、统一预处理、批次效应、训练数据。
- 来源：原文链接/DOI、版本、年份待核验；[本地材料](scBaseCount.md)。

### The Landscape of Single-Cell Foundation Models: Design Principles, Applications, and Open Challenges

- 摘要：综述单细胞基础模型（single-cell foundation models, scFMs）的数据表示、模型架构、预训练目标、多模态语料、下游任务、评估和工程基础设施，并讨论生物学可信度、泛化、缩放和扰动建模等开放问题。此条为预印本原文概述。
- 核心关联：可用来建立单细胞基础模型候选、预训练数据和 benchmark 的导航图；补充表集中整理数据集、数据容器、下游任务、评测研究、设计权衡和基础设施。
- 关系：覆盖 scGPT、Stack、scBaseCount、Tahoe-100M、X-Atlas/Orion 等本项目已关注的模型与资源，但综述不是这些方法性能主张的一手证据。
- 结论：备选为领域综述和候选发现入口；影响比赛决策的具体数值与结论仍须回到原始论文、数据集或代码核验。
- 关键词：单细胞基础模型、scFM、预训练、多模态、扰动建模、benchmark、AI virtual cell。
- 来源：[DOI](https://doi.org/10.20944/preprints202608.1166.v1)；[公开 PDF](https://www.preprints.org/frontend/manuscript/173c8b1a4409ec1eafb48462e5308db9/download_pub)；Jiang et al.；Preprints.org v1；2026-08-18；[MinerU Markdown 阅读版](jiang-et-al-2026-scfm-landscape-v1/jiang-et-al-2026-scfm-landscape-v1.md)；[SI Markdown](jiang-et-al-2026-scfm-landscape-v1/jiang-et-al-2026-scfm-landscape-v1-supplementary.md)（均为机器转换，以正文与 SI PDF 为准）；本地 PDF 由 Git 忽略；获取与转换日期 2026-08-30。
- 获取记录：为定位 SI，Brave 精确查询 1 次：`"10.20944/preprints202608.1166.v1" supplementary Table S1 S6 file`；查询未直接命中本稿附件，但命中 Preprints.org 官方 `download_pub/supplementary` 路由实例，随后以本稿 ID 取得并核验包含 Table S1-S6 的官方 SI PDF；无未解决附件缺口。

### scGPT: Toward Building a Foundation Model for Single-Cell Multi-omics

- 摘要：在 3,300 多万个细胞上进行生成式 Transformer 预训练，联合学习基因与细胞表征，并迁移至注释、整合、扰动预测和基因网络推断等任务。
- 核心关联：提供基础模型和预训练表征基线，但需单独验证其在零样本 CRISPRi 分布预测上的能力。
- 关系：与 Stack 同属大规模单细胞预训练；可作为 STATE 等扰动模型的表征层参照。
- 结论：备选为预训练表征与基础模型基线。
- 关键词：Transformer、基础模型、迁移学习、基因表征、多组学。
- 来源：原文链接/DOI、版本、年份待核验；[本地材料](scGPT.md)。

## 愿景、评估与扩展路线

### What Makes a Virtual Cell a World Model? Three Gaps, Three Experiments, and a Roadmap

- 摘要：作者把虚拟细胞世界模型（virtual cell world model, VCWM）定义为维护细胞状态、结合生物与观测上下文、按干预执行状态转移并表示随时间变化结构的系统，并以三个实验区分“表征不等于动力学、预测不等于干预、多模态不等于多尺度世界模型”。此条为预印本原文概述。
- 核心关联：为判断比赛模型究竟只是单步终点预测器，还是具备可迭代、干预一致和跨尺度能力的世界模型，提供了明确的诊断维度与能力阶梯。
- 关系：概念上连接 Bunne et al. 的 AIVC 愿景与 AIDO Cell、Lingshu-Cell、AlphaCell 等具体系统；其三个实验是动机性诊断，不等于完整领域 benchmark。
- 结论：采用为世界模型术语边界和赛后评估路线参考；不作为 VC2026 直接算法基线。
- 关键词：虚拟细胞世界模型、动力学、干预、状态空间闭包、多尺度、能力阶梯。
- 来源：[DOI](https://doi.org/10.21203/rs.3.rs-10404367/v1)；[Research Square 页面](https://www.researchsquare.com/article/rs-10404367/v1)；Yu et al.；Research Square v1；2026-07-21；本地 PDF 仅作核验且由 Git 忽略；[MinerU Markdown 阅读版](yu-et-al-2026-vcwm-roadmap-v1/yu-et-al-2026-vcwm-roadmap-v1.md)（机器转换，以 PDF 为准）；落地页未列独立 SI；获取与转换日期 2026-08-30。

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

### 2026-08-30 10x Flex 检测机制检索审计

- 目的：补足 VC2026 教程中 10x Flex 由固定细胞到原始计数的信息链，避免把传统 3' scRNA-seq 的逆转录流程错误套用到 Flex。
- 查询：Infra Scholar 顺序调用 1 次，唯一查询为 `Chromium Fixed RNA Profiling probe pairs ligation UMI single-cell gene expression Flex`；返回 10 条，未精炼第二次查询，因为首条已经直接命中所需机制。
- 采用：Abay et al. 位列第 1；回到 bioRxiv v1 HTML 全文核验 assay rationale 和 Extended Data Fig. 1，确认原文明确写出全转录组探针对、相邻杂交、随后连接和 bead oligo extension，已在“数据与基础表征”中登记。
- 其余命中：仅按题名、摘要或 snippet 做初筛，涵盖 TempO-LINC、固定转录组基因分型、普通 10x Chromium 综述、使用 Flex 的疾病研究和 Visium HD 研究；它们没有进入本次机制判断，未作为项目证据或逐篇全文评估。
- 失败与缺口：10x 产品页及其只读镜像连续返回 HTTP 429；bioRxiv 原文与 Crossref DOI 元数据可访问。教程仍保留 10x 官方产品页作为厂商入口，并以可访问的 Abay et al. 原文补强机制证据；Arc 2026 具体实验参数仍只能以官方挑战说明和对应版本的 10x 用户指南为准。

### 2026-08-30 VC2026 跨背景方案检索审计

- 目的：检验复杂单细胞模型是否已在“CRISPRi + 未见细胞背景 + 未见目标 + 伪批量/单细胞输出”这一接近 VC2026 的问题上稳定胜过简单基线，并为主方案选择响应分量、目标先验和模型复杂度。
- 查询：本轮分为两个问题，共顺序调用 Infra Scholar 3 次。方法与可用性问题先查询 `zero-shot single-cell CRISPRi Perturb-seq response prediction unseen cell context`，因未返回本地核心候选 X-Cell，再精炼一次为 `"Scaling Causal Perturbation Prediction across Diverse Cellular Contexts" X-Cell`；两次均返回 10 条。简单基线是否稳健的问题另查询 `CRISPRi Perturb-seq zero-shot perturbation prediction unseen cell context benchmark pseudobulk baseline`，返回 10 条且无需精炼。三次 HTTP 调用均成功。
- 采用：Molina and Zhang 的跨细胞系响应分解进入核心方法证据；沿其原文引用回到 Ahlmann-Eltze et al. 的 Nature Methods 同行评议全文，作为简单基线和复杂度晋级门的核心证据。PerturbNet、Csendes et al.、Palla et al. 与 Shoeibi and Yousefi 因双重外推能力、留出轴、扰动模态、标量终点或预印本状态存在边界，登记为备选而非直接排名证据。Stack 和 X-Cell 的标识、代码/权重可用性及许可也已更新到对应条目。
- 其余命中：Miladinovic et al. 的 Large Perturbation Model 和 Li et al. 的综合 benchmark 作为后续多实验/OOD 候选；一篇硕士论文、一篇博士论文、扰动响应评分方法和一篇多模态对齐预印本没有进入本次判断。未查看其原文，不能据题名或 snippet 对方法有效性下结论。
- 原文核验：bioRxiv、arXiv、PubMed Central、Crossref、官方 GitHub/Hugging Face 入口和许可证均用于核验选中候选；X-Cell 精炼查询仍未直接返回论文记录，最终由结果引文线索定位 DOI 后回到 Crossref/bioRxiv 核实。BMC 出版页 PDF 重定向发生一次 TLS 失败，随后使用 DOI 精确定位的 PubMed Central 开放全文完成核验。另核对 Arc `cell-eval2` commit `5e64833518a6603a0301cbe28185d49c30f4a986`：当前包为 0.16.0、`rule_version=3`，0.16.0 不改变评分数值，但与 0.15.0 bundle 严格不兼容。
- 未解决缺口：没有公开论文能证明其方法会在保留的 D/E/F 或 VC2026 六项参考缩放总分上获胜；A/B/C 扰动真值不可见，Molina/Palla/Shoeibi 均未同行评议，最终目标面板也尚未发布。因此方案结论只能指导离线 LOCO 实验和候选优先级，不能表述为比赛成绩保证。

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
