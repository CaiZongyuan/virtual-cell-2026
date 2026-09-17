# 论文索引

本索引记录已检索或已评估的论文，帮助快速定位证据、方法和论文间关系。摘要为便于检索的中文概述，不替代原文。当前本地材料多数未保留规范出处；其 DOI、正式版本、年份和原文链接均标为待核验。初始盘点日期：2026-08-21。

2026-09-14 的[首个模型提交方案](../research/first-submission-plan.md)复用本索引，并重核响应分解原文、线性基线原文及 STATE 官方代码说明；本轮记录见末尾台账。官方比赛用途对 Stack 的解释已更新，见其条目与[合同核验](../research/submission-contract-check.md)。

同日根据用户补充材料加入 [H1 benchmark 审计](../research/h1-benchmark-audit.md)及[参赛博客/社区审阅](../research/participant-evidence-review.md)。工程材料单独登记；博客自报排名、身份匹配与社区历史分数不作为官方事实。

**当前执行决定：STATE 是必须建立的神经网络基线，首投使用全基因 STATE 适配版；此前 Ridge-first / 无 GPU 方案已撤销。** 论文对线性基线的研究结论仍有效，但不据此降低本项目主模型标准。当前配置及代码边界见[首投方案](../research/first-submission-plan.md)与[STATE 源码审计](../research/state-training-source-audit.md)。

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
- 结论：采用为 raw-count decoder 候选，不作为主效应模型。作者公开 MIT 代码和 85M VCC checkpoint，但 H1 实验使用同一背景的 150 个监督扰动，词表为 18,080 genes，不能证明匿名新背景或直接满足 18,533-gene VC2026 合同。
- 关键词：离散扩散、全转录组、条件生成、细胞异质性、扰动预测。
- 来源：[arXiv:2603.25240v1](https://arxiv.org/abs/2603.25240v1)；[MIT 代码](https://github.com/alibaba-damo-academy/Lingshu-Cell)；[85M 权重](https://huggingface.co/bibona/lingshu-cell)；Zhang et al.；arXiv v1，2026-03-26；[本地材料](<Lingshu-Cell：面向虚拟细胞的转录组建模生成式细胞世界模型.md>)（转述材料，不替代原文）；标识、代码、权重入口与许可核验日期 2026-08-31。

### Predicting cellular responses to perturbation across diverse contexts with State

- 摘要：结合状态嵌入与集合层面的状态转移模型，从大规模观察性和扰动单细胞数据中学习跨细胞情境的扰动效应，并提出 CELL-EVAL 评估框架。
- 核心关联：比赛官方推荐背景模型，任务形式与未知细胞情境下的扰动响应预测高度一致。
- 关系：可作为 X-Cell、Lingshu-Cell、AlphaCell 的直接方法基线；CELL-EVAL 可补充竞赛指标分析。
- 结论：采用为必须先建立的神经网络主基线及首投主干；训练标准 STATE-ST，并在相同协议下评估全基因适配和后续增量。
- 关键词：状态转移、跨情境泛化、扰动效应、CELL-EVAL、集合建模。
- 来源：[DOI/bioRxiv](https://doi.org/10.1101/2025.06.26.661135)；Adduri et al.；bioRxiv 预印本；2025；本地原文未保存；[本地中文阅读材料](<使用 STATE 预测多样化情境下细胞对扰动的响应.md>)（转述材料，不替代原文）；检索日期 2026-08-21。
- 2026-09-14 复核：采用为首投前的主基线；固定 [STATE commit 9bbfe78a](https://github.com/ArcInstitute/state/tree/9bbfe78a434a55205e4de834e1ea99f85f7a3add) 核实 8 层/768/12 heads、set 512、Energy loss、Adam，以及作者 VCC starter 已使用 ESM2 连续靶点。源码的 bf16、full-gene 参数量、缺失特征回退和浮点 infer 边界详见[审计](../research/state-training-source-audit.md)；未训练或声称复现成绩。此前“STATE 首投后再做”的实施决定已撤销。
- 同日权重补全：官方 [ST-HVG-Replogle](https://huggingface.co/arcinstitute/ST-HVG-Replogle)、[ST-SE-Replogle](https://huggingface.co/arcinstitute/ST-SE-Replogle)、[st-x-replogle-full](https://huggingface.co/arcinstitute/st-x-replogle-full)、[st-se-replogle-full](https://huggingface.co/arcinstitute/st-se-replogle-full) 已有 checkpoint、config 和映射文件。抽查 HVG/zeroshot/jurkat 与 x-full/k562_0.99 分别输出 2,000 / 6,546 genes，均 328 hidden、set64、one-hot 靶点；不能把 768 宽 ESM2 starter 的默认值套给它们。首选复用/微调，再按必要性重训；本轮只读文件树和 YAML，未加载权重。版本与边界见[权重审计](../research/state-training-source-audit.md#已发布检查点补充不必从零训练)。
- 正式版本补全：规范题名如本条标题；[Cell DOI](https://doi.org/10.1016/j.cell.2026.07.052)，Adduri, Gautam, Bevilacqua et al.，2026 年 8 月；本轮由博客引文追溯并经 [Crossref](https://api.crossref.org/works/10.1016/j.cell.2026.07.052)核实书目。此前标题 **STATE: Predicting Cellular Responses to Perturbation across Diverse Contexts** 与 DOI `10.1101/2025.06.26.661135` 作为预印本版本保留，不计为独立证据。本轮未读取正式版全文，内容变化及精确 online 日期待核验，不能把 Crossref 登记日或 license 起始日当作出版日。
- 同日微调教程：新增[State 微调实战与算力预算](../lessons/10-State微调实战与算力预算.md)及[检查点微调源码审计](../research/state-checkpoint-finetuning-audit.md)。确认原生 `init_from`、resume 优先级、328 主干结构、按名称迁移需求、HVG 元数据、batch 对照匹配、冻结/LoRA 边界及 `ckpt_every_n_steps` 未生效；继承父权重的训练暴露必须纳入 LOCO。只核对小型资产和源码，未加载大权重/训练；24/48 GB 档位和 GPU-hours 是工程预留，待 pilot 测量。
- 2026-09-15 学习笔记：新增 [三份可运行 ipynb](../../notebook/README.md)，复用既有方法审计。固定上述两组已评估 HF revision，各读取 config/hparams 两份原始 YAML，共 4 次 HTTP、均成功；小型快照与 SHA/URL 保存在 [notebook/assets/state/sources.json](../../notebook/assets/state/sources.json)。无 Scholar/SciVerse 查询、无新增候选；State 保持采用。笔记执行真实 NTC 数据审计与明确标识的 NumPy 数学示例，未加载官方 checkpoint 张量、训练或报告模型成绩。
- 同轮输入覆盖：对固定 hparams 和本地 2026 基因清单做原始符号逐字比较，HVG 交集 1,877/2,000，full 交集 6,197/6,546；未匹配项可能含别名/版本差异，不能直接当作生物学缺测，更不能静默补零。该比较不代表扰动靶点训练暴露；可复算代码与实际输出见第二份 notebook。

### X-Cell: Scaling Causal Perturbation Prediction across Diverse Cellular Contexts

- 摘要：在大规模 CRISPRi Perturb-seq 汇编 X-Atlas/Pisces 上训练扩散语言模型，并融合文本、蛋白、网络、依赖性和形态学先验以预测跨情境扰动响应。
- 核心关联：直接研究零样本跨细胞背景泛化，并讨论数据量、模型规模与预测性能的缩放关系。
- 关系：数据驱动规模化路线可与 STATE 的状态转移、Lingshu-Cell 的离散生成路线比较。
- 结论：采用为核心方法与 NTC-only 测试时适配的论文证据；当前不能作为可运行主线。2026-08-30 核查未发现公开 GitHub 仓库，Hugging Face 模型页只有 README、概览图和属性文件，没有权重或数据。
- 关键词：CRISPRi、Perturb-seq、扩散语言模型、多模态先验、零样本、缩放律。
- 来源：[DOI/bioRxiv](https://doi.org/10.64898/2026.03.18.712807)；[Hugging Face 占位页](https://huggingface.co/Xaira-Therapeutics/X-Cell)；Wang et al.；bioRxiv 预印本 v1，2026-03-20；[本地中文阅读材料](<X-Cell：通过扩散语言模型扩展跨多样细胞情境的因果扰动预测.md>)（转述材料，不替代原文）；标识与公开资产核验日期 2026-08-30。

### Learning Adaptive Perturbation-Conditioned Contexts for Robust Transcriptional Response Prediction

- 摘要：AdaPert 从 STRING 蛋白相互作用图中为每个靶基因选择稀疏、扰动特异的子图，并以全局重建、非 DEG 稳健惩罚和 DEG 响应对齐三个目标减少“均值塌缩”。论文在 K562、RPE1、HepG2 和 Jurkat 四个 CRISPRi 数据集上评估未见扰动，并增加了“三个细胞系训练、整个 K562 留出”的跨细胞系实验。
- 核心关联：这是本轮新候选中与 VC2026 输入最接近的方法：模型同时接收目标背景对照细胞和连续靶基因先验；其稀疏响应门与方向/幅度损失直接对应比赛的 `reach`、`nmae` 和方向 fidelity。论文的 K562 跨细胞系 Systema 评估中，AdaPert 的 perturbation-reference 分数高于 STATE，但在另一组汇总指标中并未全面胜出，且直接跨细胞系 Perturb Mean 在 Pearson-delta 上仍更强。
- 关系：与 X-Cell 都强调多模态靶基因先验和抗塌缩训练；与 response decomposition 的低秩 target-effect 映射互补。前者可提供“哪些基因应响应”的稀疏残差，后者提供保守的跨背景效应主干。
- 结论：采用为稀疏靶基因图、响应概率头和抗塌缩 loss 的核心组件证据，不直接采用为端到端主模型。论文只在 3,352/5,000 个 HVG 的 `log1p` 空间评估，没有生成比赛要求的 18,533 基因原始计数；论文未披露参数量、硬件或训练时长，也未链接可明确识别为 AdaPert 的官方代码仓库。
- 关键词：AdaPert、CRISPRi、未见扰动、未见细胞系、STRING、稀疏子图、均值塌缩、DEG。
- 来源：[arXiv:2602.18885v2](https://arxiv.org/abs/2602.18885v2)；Piao et al.；ICML 2026；arXiv v2，2026-07-05；PDF 仅在系统临时目录作本次核验，未入库；原文、arXiv 元数据与公开代码入口核验日期 2026-08-31。

### Causal Cellular Context Transfer Learning: An Efficient Architecture for Prediction of Unseen Perturbation Effects

- 摘要：C3TL 将同一扰动在多个背景的伪批量效应聚合为扰动表示，并把同一背景中的多种已测扰动聚合为背景表示，再用轻量解码器预测新的“背景—扰动”组合。论文报告在 Replogle、Parse 和 Tahoe 的 2,000 HVG 伪批量任务上与 STATE 相近或更好，同时训练 epoch 约快 30 倍、显存约 2.1 GB。
- 核心关联：其“扰动编码与背景编码分离后再组合”的结构值得用于低秩效应模型，但论文的目标背景并非只有 NTC：主实验把目标背景 8% 的真实扰动用于训练、2% 用于验证，余下 90% 才用于测试；数据稀缺实验也至少使用 1% 的目标背景干预结果。
- 关系：与 response decomposition 都支持把响应拆成可迁移扰动分量和背景分量；与 VC2026 的关键差别是比赛在 D/E/F 中没有任何扰动真值，无法按原方法构造目标背景编码。
- 结论：备选为轻量分解架构，不作为 VC2026 零样本性能证据。当前作者 GitHub 仓库虽标 MIT，但只有 README、LICENSE 和 `.gitignore`，没有实现代码；参数量和完整训练墙钟时间也未披露。
- 关键词：C3TL、context transfer、伪批量、轻量模型、目标背景适配、STATE。
- 来源：[arXiv:2603.13051v1](https://arxiv.org/abs/2603.13051v1)；[作者仓库](https://github.com/mscholkemper/C3TL)；Scholkemper and Mukherjee；arXiv v1，2026-03-13；PDF 仅在系统临时目录作本次核验，未入库；原文、元数据、仓库树与许可核验日期 2026-08-31。

### AlphaCell: Simulating Perturbation-Induced Cellular Dynamics

- 摘要：以全基因组潜在空间、知识丰富的解码器和条件流匹配统一建模连续细胞状态转移，目标是将扰动动力学迁移到未见细胞情境。
- 核心关联：覆盖全基因组重建、生成质量和组合泛化，可启发从对照分布到扰动分布的建模。
- 关系：与 Lingshu-Cell 都以“细胞世界模型”描述生成式模拟；与 STATE 都显式建模状态转移。
- 结论：排除出端到端比赛主线。原文明确使用离散的已学习 perturbation ID，不能预测训练中未见的 target；主要实验是药物/过表达，输出为 19,253 genes 的 `log1p(CP10K)`，且没有公开代码或权重。保留条件流匹配和潜空间 decoder 为远期参考。
- 关键词：世界模型、流匹配、全基因组重建、连续状态转移、组合泛化。
- 来源：[DOI/bioRxiv](https://doi.org/10.64898/2026.03.02.709176)；Wang et al.；bioRxiv 预印本，2026-03-05；论文为 CC BY-NC-ND 4.0；[本地材料](<迈向构建 AlphaCell 世界模型：模拟扰动诱导的细胞动力学.md>)（转述材料，不替代原文）；原文标识与任务边界核验日期 2026-08-31。

### Stack: In-Context Learning of Single-Cell Biology

- 摘要：使用表格注意力在 1.49 亿个人类单细胞上学习上下文相关表征，让无标签上下文细胞在推理时充当示例，并预测条件对目标细胞群的影响。
- 核心关联：比赛提供大量未知背景的对照细胞，Stack 的上下文学习思路可能用于从这些细胞中适配背景。
- 关系：建立在大规模统一处理数据之上，与 scBaseCount 的数据路线、scGPT 的预训练路线相关。
- 结论：备选为细胞背景适配参考。2026-09-14 当前[官方 FAQ](https://virtualcellchallenge.org/faq#legal)已对 State 和 Stack 并列给出比赛用途说明：参赛使用代码视为 Non-Commercial Purpose，仍须遵守适用代码许可；非商业参赛者可使用预训练检查点，商业参赛者使用预训练权重需相应商业许可。8 月核查时“FAQ 未给 Stack 例外、须先取书面比赛许可”的判断不再作为统一前置条件；具体 checkpoint、团队身份和适用条款仍需对应核对。首投暂不依赖 Stack，是实施优先级决定。
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
- 2026-09-14 复核：通过 [Europe PMC 原文 XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12328236/fullTextXML)复核原文，继续采用为先测简单基线的依据；本轮全文仅存系统临时目录，未入库。

### Perturbation response decomposition enables biologically aligned generalization to unseen perturbations and cellular contexts

- 摘要：作者把 CRISPRi 伪批量响应分解为全局、扰动特异、细胞系特异和 `perturbation x cell line` 交互分量，并在 Replogle-Nadig 的四个细胞系中分析各分量的结构和可预测性。论文报告共享模板是低维的，目标与背景特异残差更高维；将 DepMap 共必需性先验直接对齐到响应空间的 Ridge/MLP 可在多种留出设置中匹配或超过更复杂模型。
- 核心关联：任务形式直接包含未见细胞系和未见目标组合，支持把 VC2026 主模型写成“当前 NTC 基线 + 共享 target effect + 背景模板/幅度 + 强收缩交互”，并为每个分量选择与其信息需求相符的输入，而不是端到端增加模型容量。论文的三源 Ridge/MLP 没有显式 cell-line descriptor，预测的是 source-averaged conserved component；它证明了 target-effect prior 的可迁移性，不是完整匿名背景交互的解决方案。
- 关系：为本索引中的 STATE、X-Cell 与线性基线提供共同诊断坐标；与 Ahlmann-Eltze et al. 的简单基线结论互补，也与 Shoeibi and Yousefi 对响应幅度应显式建模的结果方向一致。
- 结论：采用为当前跨背景 target-effect 模块的直接方法证据，但证据级别仍为未同行评议预印本；主要实验是富集必需基因的四个 CRISPRi screen 和伪批量终点。作者明确发现纯零样本方法不能恢复 `cell-line x perturbation` interaction，只有加入目标背景 30% 扰动后才改善，因此不能证明单细胞计数生成或 VC2026 六指标上的完整收益。
- 关键词：响应分解、CRISPRi、未见细胞背景、未见扰动、DepMap、共必需性、Ridge、MLP、伪批量。
- 来源：[DOI/bioRxiv](https://doi.org/10.64898/2026.07.24.740459)；[代码](https://github.com/xinyizhanglab/perturbation-decomposition)；Alexis Molina and Xinyi Zhang；bioRxiv 预印本，2026-07-27；代码仓库未声明 license；PDF 仅在系统临时目录作本次核验，未入库；原文、元数据和代码入口核验日期 2026-08-30。
- 2026-09-14 复核：重读 [v1 HTML 原文](https://www.biorxiv.org/content/10.64898/2026.07.24.740459v1.full)的跨细胞系、双重留出、交互分量实验和数据预处理，继续采用为 Ridge/MLP target-effect 组件证据。原文先在合并四背景的表达矩阵选 2,000 HVG；本项目首投验证改为仅从训练背景选择。作者测试过的零样本模型未恢复交互，不应升级为所有模型均不可能从 NTC 学到交互的理论结论。原文和作者 README 临时保存，未入库。

### PerturBench: Benchmarking Machine Learning Models for Cellular Perturbation Analysis

- 摘要：PerturBench 在六个遗传或化学单细胞扰动数据集上统一比较匹配式、解耦式和简单基线模型，并用 rank 指标诊断不同扰动被预测成近似同一响应的 mode collapse。论文报告没有一种架构在所有数据上占优；数据规模增大时，简单 Latent Additive 或 Decoder-Only 模型往往比复杂 VAE 更稳，而移除 CPA 的 adversarial loss 或 SAMS-VAE 的稀疏机制在多项实验中反而改善性能。
- 核心关联：支持把 VC2026 方案拆成低秩效应主干、抗塌缩诊断和独立分布生成器，并要求每个新增复杂组件先做消融；也解释了为何不能凭一项平均误差或论文 headline 判断模型优于 STATE。
- 关系：与 AdaPert 对均值塌缩的诊断一致；与 response decomposition、Ahlmann-Eltze et al. 共同支持强简单基线。其 autoencoder 在 MMD 分布指标上仍可能优于简单均值模型，说明低秩效应预测不能替代单细胞 count emitter。
- 结论：采用为模型选择、rank/mode-collapse 诊断和消融设计证据；其 cross-covariate split 仍允许模型看到目标背景中的其他扰动，不等于 VC2026 的 NTC-only 整背景留出。官方仓库当前没有可识别的 SPDX 许可或根 LICENSE，代码复用前需另行确认。
- 关键词：PerturBench、covariate transfer、Latent Additive、mode collapse、rank metric、消融、基线。
- 来源：[arXiv:2408.10609v4](https://arxiv.org/abs/2408.10609v4)；[作者仓库](https://github.com/altoslabs/perturbench)；Wu et al.；arXiv v4，2025-10-24；PDF 仅在系统临时目录作本次核验，未入库；原文、仓库与许可入口核验日期 2026-08-31。

### MORPH Predicts the Single-Cell Outcome of Genetic Perturbations Across Conditions and Data Modalities

- 摘要：MORPH 将 DepMap 共必需性向量作为连续扰动描述，通过条件生成模型预测未见扰动和背景下的单细胞结果。作者公开 MIT 代码；response decomposition 论文在统一数据与 split 中重新评估了该模型及其内部表征。
- 核心关联：支持 DepMap 是强 target prior，也提供一个可运行的条件生成对照；但重新评估显示，直接把原始 DepMap profile 通过 response-aligned Ridge/MLP 映射到响应，比 MORPH 的压缩与 attention 表征保留更多 target-specific signal。只用目标 NTC 微调也不能恢复匿名背景的 interaction。
- 关系：是 response decomposition 的主要复杂模型对照；与 AdaPert 都使用外部生物先验，但 AdaPert强调扰动特异稀疏图，MORPH 强调条件生成和跨模态先验。
- 结论：排除整模为默认主线，保留 DepMap prior、MIT 实现和条件 count decoder 为受控消融。其作者结果仍是预印本证据，不能替代 VC2026 六指标 LOCO 验证。
- 关键词：MORPH、DepMap、共必需性、条件生成、未见扰动、跨背景、response alignment。
- 来源：[DOI/bioRxiv](https://doi.org/10.1101/2025.06.27.661992)；[MIT 代码](https://github.com/uhlerlab/MORPH)；He et al.；bioRxiv 预印本，2025-07-02；原文、代码入口与许可核验日期 2026-08-31。

### In silico biological discovery with large perturbation models

- 摘要：Large Perturbation Model 把 perturbation、readout 和 context 组织为统一的 PRC tuple，以大型多实验训练和检索接口支持未测实验组合的预测，并提供 `perturblib` 数据/建模工具。
- 核心关联：PRC schema 和多实验数据接口值得用于本项目 canonical data layer；但论文的 “unseen experiment” 是已知词表内 PRC 组合，输出是实验级 z-normalized readout，不是匿名 NTC-only 背景中的 400-cell raw counts。
- 关系：与本项目的跨研究 effect bank 和 assay-aware harmonization 方向一致；相比 STATE/X-Cell，它更偏多实验统一接口和 experiment-level prediction，而不是完整单细胞分布生成。
- 结论：备选为数据接口和多实验训练参考，不作为比赛预测主模型。正式论文为 CC BY 4.0，`perturblib` 为 Apache-2.0；任务和输出合同仍需本项目自行重构。
- 关键词：Large Perturbation Model、PRC tuple、多实验、perturblib、in-silico experiment、readout。
- 来源：[DOI/Nature Computational Science](https://doi.org/10.1038/s43588-025-00870-1)；[Apache-2.0 代码](https://github.com/perturblib/perturblib)；Miladinovic et al.；正式在线 2025-10-15；原文、正式元数据、代码入口与许可核验日期 2026-08-31。

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

### MapPFN: Learning Causal Perturbation Maps in Context

- 摘要：MapPFN 是一个约 25M 参数的 prior-data fitted network，以 SERGIO 生成的合成因果干预数据预训练，再通过多模态 diffusion Transformer 和 flow matching 把观测、干预上下文及查询扰动映射为单细胞分布。作者公开了 MIT 代码、权重和合成数据，并报告预训练约需单张 80 GB A100/H100 10-36 小时。
- 核心关联：合成因果先验和推理时 in-context distribution mapping 是有价值的长期方向；但当前模型的真实数据实验依赖目标背景中的多组已测干预作为上下文，预训练和评估针对 hard CRISPR knockout，且只处理 50 基因、200 cells 的小问题。
- 关系：与 Stack 一样在推理时使用上下文样本，但 Stack 可把其他来源的扰动细胞作为 prompt，而 MapPFN 的主要收益明确来自目标背景 interventional context；与 VC2026 只提供 NTC 的合同不一致。
- 结论：排除出本赛主线；保留为赛后合成先验实验或小基因子图的研究分支。论文自己把扩展到 CRISPRi soft knockdown 和更高维基因空间列为未来工作。
- 关键词：MapPFN、prior-data fitted network、SERGIO、flow matching、interventional context、CRISPR knockout。
- 来源：[arXiv:2601.21092v3](https://arxiv.org/abs/2601.21092v3)；[代码与项目页](https://github.com/marvinsxtr/MapPFN)；Sextro, Klos and Dernbach；arXiv v3，2026-05-07；PDF 仅在系统临时目录作本次核验，未入库；原文、代码、权重入口和 MIT 许可核验日期 2026-08-31。

### ScDiVa: Masked Discrete Diffusion for Joint Modeling of Single-Cell Identity and Expression

- 摘要：ScDiVa 用 12 层、约 94.5M 参数的双向 Transformer 做掩码离散扩散，同时恢复基因身份和表达值；每个细胞只序列化熵归一化排名最高的 1,200 个基因。论文称在 5,916 万个内部细胞上用 4 张 A100 40 GB 训练 4 epochs，再在 Adamson 和 Norman 数据上微调扰动预测头。
- 核心关联：联合建模“基因是否出现”和“表达量大小”的想法可启发 count emitter，但它没有验证整细胞背景留出、未见 CRISPRi 靶点和 18,533 基因原始计数联合生成。
- 关系：与 Lingshu-Cell 同属 masked discrete generation 路线；与 AdaPert 的直接差别是 ScDiVa 主要学习观察性细胞重建，扰动任务只是下游微调，而不是以跨背景因果数据为主干。
- 结论：排除出当前比赛实现。预训练数据为不可披露的专有语料，论文未链接公开代码或 checkpoint，扰动实验只在单一数据集内部进行；无法把其自报结果当作超越 STATE 的 VC2026 证据。
- 关键词：ScDiVa、masked discrete diffusion、观察性预训练、Adamson、Norman、专有数据、count generation。
- 来源：[arXiv:2602.03477v1](https://arxiv.org/abs/2602.03477v1)；Wang et al.；arXiv v1，2026-02-03；PDF 仅在系统临时目录作本次核验，未入库；原文、arXiv 元数据和公开资产入口核验日期 2026-08-31。

### Predicting the unseen: a diffusion-based debiasing framework for transcriptional response prediction at single-cell resolution

- 摘要：dbDiffusion 用 VAE 潜空间和 classifier-free diffusion 生成未见扰动细胞，再根据相似扰动簇的历史偏差修正预测均值并构造置信区间。论文在 Yao macrophage CRISPR knockout 和 Replogle RPE1 CRISPRi 中留出同一背景内的扰动，使用 1,500 个基因的 `log1p` 表达评估。
- 核心关联：按相似扰动估计并校正系统偏差，可作为 effect calibration 的独立消融；其扩散生成器不是匿名背景迁移的已验证方案。
- 关系：与本项目的 empirical-Bayes shrinkage 和 target-effect memory 相近；与 X-Cell、ScDiVa 的区别是它从同一数据集中已测扰动的 effect-size clustering 构造未见靶点嵌入，没有解决整个细胞背景留出。
- 结论：排除出主线。作者仓库公开了脚本但未声明代码许可，正式论文为 CC BY-NC-ND 4.0；论文未披露模型参数、硬件或训练时长，也没有 full-gene raw-count 评估。
- 关键词：dbDiffusion、latent diffusion、prediction-powered inference、偏差校正、未见扰动、RPE1。
- 来源：[正式版 DOI/PNAS](https://doi.org/10.1073/pnas.2525268122)；[bioRxiv 预印本 DOI](https://doi.org/10.1101/2025.09.12.675662)；[作者仓库](https://github.com/ergan-shang/dbDiffusion)；Shang, Wei and Roeder；PNAS 正式在线 2025-12-26、预印本 v1 为 2025-09-16；PDF 仅在系统临时目录作本次核验，未入库；正式元数据、原文、代码入口与许可状态核验日期 2026-08-31。

### Response Magnitude as a Dominant Signal for Held-Out CRISPRi Perturbation Effect Prediction

- 摘要：作者在 VC2025 H1 的严格目标留出和两个外部 CRISPRi screen 上研究一个标量终点，报告四个确定性响应幅度特征的线性/树模型优于所测试的 MLP 编码器，并强调幅度与方向应分开建模。
- 核心关联：支持为下游表达方向和效应幅度建立独立预测头，并把幅度校准作为 MSE、差异表达集合和 LFC 指标的受控消融，而不是依赖深层编码器自行恢复尺度。
- 关系：与 Molina and Zhang 的分量化建模方向一致；其终点是 log Anderson-Darling 距离，不是 18,533 基因原始计数或 VC2026 六指标。
- 结论：备选为幅度建模假设来源；仅为 arXiv 预印本，模型族和终点范围有限，不作为完整转录组方案的性能证据。
- 关键词：响应幅度、CRISPRi、目标留出、VC2025、线性回归、Random Forest、跨背景迁移。
- 来源：[arXiv:2608.00152v1](https://arxiv.org/abs/2608.00152v1)；Mehrdad Shoeibi and Niloofar Yousefi；2026-07-31；PDF 仅在系统临时目录作本次核验，未入库；原文与 arXiv 元数据核验日期 2026-08-30。

## 数据与基础表征

### Mapping information-rich genotype-phenotype landscapes with genome-scale Perturb-seq

- 摘要：Replogle 等使用大规模 CRISPRi Perturb-seq 测量基因压低后的单细胞转录响应，公开 K562 全基因组、K562 essential 与 RPE1 的处理后矩阵。此处为依据官方比赛资料、作者数据记录和既有原文核验的概述。
- 核心关联：K562/RPE1 提供 State 微调的核心背景；GWPS 扩展训练靶点覆盖。不能把 essential 与 GWPS 当成两个独立细胞背景。
- 关系：与 Nadig 的 HepG2/Jurkat 共同组成 Replogle-Nadig；scPerturb 为便利副本而非另一组生物实验。
- 结论：采用为核心 CRISPRi 训练数据；优先四背景核心，再加 GWPS。实际训练行数、目标交集、基因缺测和父权重暴露仍需下载后审计。
- 关键词：CRISPRi、Perturb-seq、K562、RPE1、GWPS、State、训练数据。
- 来源：[Cell DOI](https://doi.org/10.1016/j.cell.2022.05.013)；Joseph M. Replogle et al.；Cell，2022；[作者 Figshare](https://plus.figshare.com/articles/dataset/20029387)、[PMC 原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC9380471/)；本地证据见[容量核验](../research/data-compute-capacity-sources.md)和[微调教程](../lessons/10-State微调实战与算力预算.md)，本地独立全文未保存；本轮书目核验 2026-09-14，复用 2026-08-30 数据/原文审计。

### Transcriptome-wide analysis of differential expression in perturbation atlases

- 摘要：Nadig 等研究扰动图谱中的差异表达，并公开 HepG2/Jurkat common-essential CRISPRi 单细胞数据。本条仅采用数据来源与使用范围，不扩展为已复现其统计方法。
- 核心关联：补足 State 微调的跨背景监督，与 K562/RPE1 共同支持背景留出；GEO 作者文件和压缩副本的字节校验不能混用。
- 关系：与 Replogle 数据组合；被 State 用于跨情境建模。scPerturb 文件名 `NadigOConner2024_*` 保留旧整理命名，不与 2025 正式论文重复计证据。
- 结论：采用为第一批微调核心数据；`.X` 计数、对照标签、实测基因覆盖与筛选口径在 ETL 时逐项确认。
- 关键词：CRISPRi、HepG2、Jurkat、差异表达、背景迁移、State。
- 来源：[Nature Genetics DOI](https://doi.org/10.1038/s41588-025-02169-3)；Ajay Nadig et al.；正式在线 2025-04-21；[GEO GSE264667](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE264667)；本地证据见[容量核验](../research/data-compute-capacity-sources.md)和[微调教程](../lessons/10-State微调实战与算力预算.md)，独立全文未保存；本轮书目核验 2026-09-14，复用 2026-08-30 数据审计。

### Systematic reconstruction of molecular pathway signatures using scalable single-cell perturbation screens

- 摘要：Jiang 等将 Perturb-seq 用于六个细胞系、五类信号条件下的调控与分子通路响应分析，公开五个 pathway Seurat RDS 对象。刺激条件属于背景定义，不把它们当成新增独立细胞系。
- 核心关联：可为 State 增加背景多样性，但需要 RDS 转换、刺激条件和匹配对照审计，先不作为第一轮微调前置。
- 关系：补充 Replogle/Nadig；本轮 Scholar 命中的 bioRxiv 2024 版本与 Nature Cell Biology 正式版合并，不作为独立数据证据。
- 结论：备选为第二阶段背景扩展；四背景流程跑通后再下载，单独评估增益。
- 关键词：Perturb-seq、信号通路、Mixscale、六细胞系、刺激条件、数据扩展。
- 来源：[Nature Cell Biology DOI](https://doi.org/10.1038/s41556-025-01622-z)；Longda Jiang et al.；正式在线 2025-02-26；[预印本 DOI](https://doi.org/10.1101/2024.01.29.576933)、[Zenodo 14518762](https://zenodo.org/records/14518762)；本地证据见[容量核验](../research/data-compute-capacity-sources.md)及[微调教程](../lessons/10-State微调实战与算力预算.md)，独立全文未保存；检索与书目核验 2026-09-14，复用既有数据审计。

### scPerturb harmonized datasets — Zenodo record 13350497

- 摘要：单细胞扰动数据整理与压缩 H5AD 发布记录；本次只采用其中 Replogle/Nadig 五个文件，不把整库覆盖当作已检查。
- 核心关联：四背景核心下载 4,927,873,119 bytes，加 K562 GWPS 后五个文件共 13,733,339,273 bytes，明显降低数据传输需求；下载体积不代表加载内存。
- 关系：对应上面两个研究的整理副本；训练时只选择一份来源，不与作者原件重复计样本。
- 结论：采用为便利下载源。已核对固定 record 的文件名、size、MD5、CC BY 4.0；矩阵值与来源处理差异未在本轮读取。论文的独立书目不在本次数据记录核验范围内。
- 关键词：scPerturb、H5AD、raw counts、数据整理、gzip、Replogle、Nadig。
- 来源：[Zenodo record](https://zenodo.org/records/13350497)、[API](https://zenodo.org/api/records/13350497)、[固定 Replogle 转换代码](https://github.com/sanderlab/scPerturb/blob/b69f72a070a92bcbaf41e7f9897b11598109ab48/dataset_processing/scripts/ReplogleWeissman2022.py)；版本固定为 record 13350497；本地下载单与 MD5 见[微调教程](../lessons/10-State微调实战与算力预算.md)，未下载大矩阵；核验 2026-09-14。

### DepMap 24Q4 Public — CRISPRGeneEffect.csv

- 摘要：DepMap 24Q4 公开发布中的基因依赖矩阵。首版选择 corrected `CRISPRGeneEffect.csv`，将每个基因在不同参考细胞系的依赖向量作为输入先验；不使用该发布的表达矩阵来硬猜 A/B/C 身份。
- 核心关联：为 STATE 增强版提供与 ESM2 互补的基因功能依赖特征；当前计划 PCA 50 维，再经 50→256→768 的 MLP 融入靶点条件。
- 关系：实现响应分解论文提出的依赖先验与扰动响应对齐思路；这是本项目固定版本选择，不声称逐字复现论文的特征版本或处理。
- 结论：采用为首投后 S2 的辅助先验；S0/S1 使用作者已有的 ESM2。矩阵缺失、符号映射及下载后实际内容仍须核验，预处理只在训练允许的基因样本中拟合。
- 关键词：DepMap、24Q4、CRISPRGeneEffect、基因依赖、Ridge、基因先验。
- 来源：[Figshare DOI v1](https://doi.org/10.25452/figshare.plus.27993248.v1)；DepMap/Broad；24Q4/2024；[直接文件](https://ndownloader.figshare.com/files/51064667)；API 记录文件为 428,678,699 bytes、发布许可 CC BY 4.0；核验日期 2026-09-14；本轮仅查元数据，未下载 CSV；执行设置见[首投方案](../research/first-submission-plan.md)。

### X-Atlas/Orion: Genome-wide Perturb-seq Datasets via a Scalable Fix-Cryopreserve Platform for Training Dose-Dependent Biological Foundation Models

- 摘要：X-Atlas/Orion 的规模化 Perturb-seq 数据与实验平台论文；参赛博客称其使用 HCT116、HEK293T screen。本轮只核对规范书目，未读全文或验证该博客的具体数据处理。
- 核心关联：补充主方案之外的目标与背景覆盖；需单独确认 raw counts、对照定义、扰动模态、测量基因与许可。
- 关系：与 X-Cell 同属 Xaira 相关资源，但 Orion 数据与 X-Cell 模型/权重是不同资产，不能用后者的发布状态推断前者不可用。
- 结论：备选数据候选，暂不加入首投下载单；先核查原始数据合同再决定。
- 关键词：X-Atlas、Orion、Perturb-seq、HCT116、HEK293T、数据整合。
- 来源：[DOI/bioRxiv](https://doi.org/10.1101/2025.06.11.659105)；Ann C Huang et al.；2025-06-16 预印本；[Crossref](https://api.crossref.org/works/10.1101/2025.06.11.659105)书目核验 2026-09-14；本地全文未保存；线索与边界见[材料审阅](../research/participant-evidence-review.md)。

### Genome-scale perturb-seq in primary human CD4+ T cells maps context-specific regulators of T cell programs and human immune traits

- 摘要：原代人 CD4+ T 细胞的全基因组 Perturb-seq 研究；参赛博客将其静息与刺激状态列入迁移数据。此处仅据题名、出版元数据及博客线索概述，方法与原始数据尚未核验。
- 核心关联：可提供免疫细胞状态变化下的扰动数据；不同激活状态不能自动视为多个独立细胞系，扰动模态必须核实后才可与 CRISPRi 混训。
- 关系：与 Replogle/Orion 形成博客的六个 source screen；其实际覆盖和迁移收益不是本项目已复现结论。
- 结论：备选，未核实 Methods 和 raw-count 合同前不进入首版训练。一次出版方 XML 请求仅返回 core metadata，没有全文；未确认 CRISPRi/KO 类型。
- 关键词：CD4 T cells、Perturb-seq、细胞激活、跨状态、免疫。
- 来源：[Cell DOI](https://doi.org/10.1016/j.cell.2026.08.002)；Ronghui Zhu, Emma Dann, Jun Yan et al.；出版方元数据写明 online 2026-08-28；[出版方 XML](https://api.elsevier.com/content/article/PII:S0092867426009293?httpAccept=text/xml)及 Crossref 核验 2026-09-14；本地全文未保存；[材料审阅](../research/participant-evidence-review.md)。

### Dissecting context-dependent cancer vulnerabilities using Perturb-seq — Data

- 摘要：作者公开的 DepMap 16 细胞系 Perturb-seq 数据记录，包含单细胞矩阵、metadata 和分析产物；Figshare 的 `single_cell_data.zip` 为 3,171,208,158 bytes，记录许可 CC BY 4.0。本轮只读数据 API 和作者 README，未下载矩阵。
- 核心关联：可用于跨背景及重复测量噪声研究。作者 README 明确写 differential expression between `knockouts and control guides`，不能直接当作同模态 CRISPRi 数据。
- 关系：博客用其讨论两个 guide 间一致性；本轮未复算该噪声结论，也未验证所有实验参数。
- 结论：备选为噪声/跨模态研究，排除出首版 CRISPRi 同模态直接混训；不因体积较小而优先替代已有核心数据。
- 关键词：DepMap、Perturb-seq、16 cell lines、knockout、噪声、数据资源。
- 来源：[Figshare DOI v1](https://doi.org/10.6084/m9.figshare.33273600.v1)；Lie Ward；2026-08-18；[作者代码与 README](https://github.com/broadinstitute/perturb-seq-depmap-public)；核验日期 2026-09-14；本地仅临时元数据，无矩阵；[材料审阅](../research/participant-evidence-review.md)。

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

## 工程材料与社区证据（非论文）

### The Virtual Cell Challenge — Ilyes Baali

- 摘要：参赛者对 VC2026 数据、source effect 迁移、目标对照模板和评分取舍的实践介绍；作者未公开较优版本全部细节。
- 核心关联：支持先实现透明的轻量效应基线、统一 raw-count 处理和分布生成消融，补充首投的工程顺序。
- 关系：引用 Replogle、Orion、CD4 T-cell screen、STATE 与线性基线；与本方案效应/生成解耦思路一致。
- 结论：采用工程经验，排名、269/300 覆盖、跨背景余弦和 A/B/C 身份均仅为作者自报/推断；简化评分公式、source 5 CPM gate、PCA 距离说法不能覆盖官方代码。
- 关键词：参赛博客、effect transfer、NTC、计数生成、六指标。
- 来源：[博客原文](https://ilyesbaali.me/blog/virtual-cell-challenge/)；Ilyes Baali；页面日期 2026-09-01；读取日期 2026-09-14；原始 HTML 只在临时目录，本地审阅见[报告](../research/participant-evidence-review.md)，保留正文 SHA-256；非论文，无 DOI。

### VCC 2026 evaluation on H1

- 摘要：在公开 VC2025 H1 training 数据上构造固定 126 靶点、每靶点 400 细胞的开发 benchmark，以 `cell-eval2 0.16.0` / `pdex 0.3.0` 运行六指标。H1 输出 50,400 × 18,080，参考 NTC 为 38,176 个。
- 核心关联：采用为首个完整离线评分回路及额外 H1 背景留出；保留四背景 LOCO，不用 H1 单一开发分数替代广泛泛化验证。
- 关系：复用官方评分组件、Arc H1 原始数据和冻结锚点；训练使用过 H1 扰动的 STATE/其他权重不能用于声称干净的 H1 留出结果。
- 结论：采用；代码静态核验发现 CLI 漏查 sparse 和额外 obs 列，导出器须补足。作者 control baseline 约 −0.04523 尚未实跑复现，分数不等于 A/B/C 榜单。参考 DE/moments/anchors 都只给 evaluator。
- 关键词：H1、开发 benchmark、cell-eval2、pdex、零样本、数据泄漏、CPU。
- 来源：[上游固定版本](https://github.com/forrestsheldon/vcc2026-h1-benchmark/tree/d28dd0496cc9fbf1d0088ce171208c0deb54a268)；GitHub owner `forrestsheldon`；v0.2.0，commit `d28dd049`，2026-09-05；用户本地副本 `references/vcc2026-h1-benchmark` 为 Git 忽略资料；代码 MIT，数据许可独立；核验日期 2026-09-14；[本地审计](../research/h1-benchmark-audit.md)；非论文，无 DOI。

### VC2026 社区：全基因保留、零效应分数与打包内存讨论

- 摘要：用户提供的 2026-09-02—03 讨论摘录。参与者报告恢复完整表达基因后，严重负分回到约 −0.30；之后明确撤回“先前 dense 中间步骤导致 prep OOM”的因果解释。
- 核心关联：采用为全基因输出和打包资源独立实测的经验依据；把基因计数置零与设置零效应严格区分。
- 关系：与博客的目标 NTC 模板、H1 工具的全轴合同互补；不同背景/评分版本的 raw 与 scaled 值不可直接混比。
- 结论：采用经验边界，不采用社区历史分数为本项目验收数值；OOM 原因未解决，不能因 CSR 或 50/64 GB 主机就保证成功。
- 关键词：社区讨论、基因截断、CSR、OOM、raw/scaled、撤回更正。
- 来源：用户提供的本地 `references/discuss.md`，原帖 URL/提交 ID 未提供，待核验；发言者包括 Anders Lindström、chax、Giovanni D；日期 2026-09-02—03；读取 2026-09-14；文件由 Git 忽略，必要上下文保存于[审阅](../research/participant-evidence-review.md)；非论文，无 DOI。

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

### 2026-08-31 STATE 后架构检索审计

- 目的：回答“复现 STATE 后，哪些新架构或组件在 VC2026 的未知背景、未见靶点和原始计数合同下更值得投入”，并区分论文 headline、可迁移组件和完整参赛模型证据。
- 默认发现：主调查与背景核验顺序调用 Infra Scholar 共 3 次，三个唯一查询分别为 `CRISPRi Perturb-seq zero-shot unseen cell context unseen perturbation STATE benchmark diffusion in-context response decomposition 2026`、`single-cell CRISPRi perturbation prediction unseen cell context unseen target zero-shot generative model 2025 2026` 和 `X-Cell Lingshu-Cell AlphaCell Large Perturbation Model perturbation response decomposition single-cell`。每次只调用一次；首轮已覆盖 benchmark、PerturBench、PerturbNet、dbDiffusion 与表格模型线索，后两轮用于点名候选补全，没有继续精炼。
- ML 方法补全：Paper Schema 搜索 1 次，查询为 `single-cell perturbation prediction`、年份下限 2024，返回 20 条；对 C3TL、MapPFN、AdaPert、ScDiVa 和 PerturBench 各读取结构化材料并查询方法/实验相关 evidence。该语料只覆盖已解析的 AI 论文，结果仅用于发现和定位，不用空结果推断生命科学文献不存在。
- 原文核验：回到 arXiv/bioRxiv PDF、arXiv Atom 元数据、出版方/Crossref 元数据、论文声明、作者 GitHub/Hugging Face 入口和仓库树，逐项核对目标背景可见信息、扰动模态、基因空间、输出类型、硬件及许可。新增全文评估为 C3TL、MapPFN、AdaPert、ScDiVa、dbDiffusion 和 PerturBench；response decomposition 也再次核对双重留出和 STATE one-hot vocabulary 边界。SciVerse 全文服务因环境缺少 `SCIVERSE_API_TOKEN` 未能调用；该失败没有被解释为论文未收录。
- 采用：AdaPert 的扰动特异稀疏图和抗塌缩目标、PerturBench 的 rank/mode-collapse 诊断进入主方案组件；response decomposition 的 DepMap response-aligned Ridge/MLP 保持为核心 target-effect 证据。C3TL 仅保留分解结构，MapPFN、ScDiVa 和 dbDiffusion 排除出本赛主线，理由见对应条目。
- 失败与缺口：一次 Hugging Face API TLS 连接失败，但 MapPFN 的官方 GitHub README 已提供模型和数据入口，不影响任务边界核验。C3TL 仓库只有占位文件；AdaPert 与 ScDiVa 原文未给出可复现代码/权重；dbDiffusion 代码仓库无 license。仍没有任何方法在 VC2026 六指标、18,533 基因 raw counts、目标背景仅有 NTC 的完整合同上公开胜过 STATE；这些缺口必须由本项目严格 LOCO 实验解决。

### 2026-09-14 首个模型提交方案复核

- 目的：把已有候选收敛成“先可提交，再提分”的首投模型、验证和交付安排，产出[方案](../research/first-submission-plan.md)。
- 范围与查询：先读本索引及现有实现/容量/架构文档；没有新增主题发现任务，英文主题查询 0、Scholar 调用 0、SciVerse 调用 0。本轮直接追溯已登记来源，不扩搜候选。
- 方法来源调用：共 5 次 HTTP 请求。PMC 原文页 1 次 TLS 失败，Europe PMC 原文 XML 回退 1 次成功；响应分解 bioRxiv v1 HTML 和作者 README 各 1 次成功；STATE 官方 README 1 次成功。采用结论和本轮新增边界已回写对应条目。
- 官方合同：独立核验官网 FAQ/Rules/Data/Evaluation 及 CLI，共 16 次顺序 GET，全为 HTTP 200；前端页面壳不足以核验正文，随后沿页面脚本获得实际正文。来源、调用分解、精确截止时间、最终选择规则及 Stack FAQ 时效修正见[合同核验](../research/submission-contract-check.md)。
- 候选状态：线性基线与 response decomposition 保持采用；STATE 为方法对照；AdaPert/Lingshu/X-Cell 仅复用已有组件评估，本轮未更新其资产可用性；Stack 保持备选并修正比赛许可解释。
- 缺口：尚未训练、生成或提交模型预测；没有本赛六指标或完整 LOCO 实测增益。原文预处理、目标背景信息和生成器的假设与本赛不同，必须在实施中单独验证，不能根据文献承诺排名。

### 2026-09-14 用户补充博客、H1 benchmark 与社区记录

- 范围：定向读取三份用户材料，并沿实际影响方案的原文链接核验。没有新主题查询，Scholar/SciVerse 调用均为 0。
- 网络调用：博客 1、固定版本官方指标规范 1、Crossref DOI 元数据 3、Ward Figshare 数据记录 1、作者 README 1、Zhu 出版方 XML 1，共 8 次，全部 HTTP 200。Zhu XML 只有元数据、没有全文，Methods 与扰动模态仍待核实；没有继续扩搜或下载数据。
- 本地代码核验：H1 clone 的 README、provenance、scorer/bounded/controls、工具和测试；完成 15 个 Python AST、JSON/TOML/锁文件一致性及 4 组 CLI parser 检查。未安装依赖、运行 pytest/真实评分或验证下载资产。
- 采用与备选：H1 工具和博客/讨论工程经验采用；Orion/CD4 数据候选备选；Ward KO 数据排除直接 CRISPRi 混训、保留研究备选；STATE 新增正式版书目但不重复计证据。每条均已单独登记。
- 方案更新：优先 H1 开发回路并保留四背景验证；隔离全部 H1 扰动训练信息；两套原生基因轴/输出合同；完整表达保留；全尺寸打包测 RSS。详细来源与限制见[材料审阅](../research/participant-evidence-review.md)、[H1 审计](../research/h1-benchmark-audit.md)和[首投方案](../research/first-submission-plan.md)。

### 2026-09-14 首投环境、数据与架构具体化（已被后续 STATE 主线取代）

- 用户反馈：此前方案的机器、数据与架构候选过多；本轮固定可直接分配的资源与模型默认值。
- 方法：复用已有证据，定向读取 Zenodo record 13350497 API、DepMap 24Q4 Figshare API、响应分解作者 README 各 1 次，均成功；未做新主题检索，Scholar/SciVerse 调用均为 0。
- 结果：五个 scPerturb 训练文件合计 13.733 GB；H1 原件 15.482 GB；DepMap corrected CSV 0.429 GB，新增大文件共 29.645 GB。DepMap 新登记为采用，已有论文状态保持；首投采用 50→64 维 Ridge 与固定生成器，STATE/MLP 排到首投后。
- 当前机器实测：20 逻辑 CPU、约 15.5 GiB RAM、RTX 3070 Ti Laptop 8 GiB、约 756 GiB 可用磁盘；据完整文件打包需求，执行环境请求固定为 16 vCPU / 128 GB RAM / 300 GB SSD，首投不需 GPU。128 GB 为工程资源决定，并非已实测峰值。
- 交付与缺口：当时提出用户提供服务器入口、Agent 完成下载/开发/评价；该轮 CPU/Ridge 执行配置已被用户否定，当前以 [STATE 方案](../research/first-submission-plan.md)为准。尚未取得新服务器连接、下载大数据或执行训练，运行时间与成绩待实测。

### 2026-09-14 STATE 主基线与 GPU 方案重制

- 触发：用户明确 STATE 是 baseline，要求重新制定方案。保留“先提交再提分”目标，撤销 Ridge 主模型和 STATE 后置的安排。
- 一手核验：research 分支固定 STATE/cell-load 两个官方仓库和作者 VCC Colab，共 5 个网络操作：两个仓库各一次 ls-remote 与 shallow clone、一次 notebook 下载，均成功。主代理另 GET 官方 H1 gene CSV 一次，与本地 2026 CSV 复核并集 18,536、交集 18,077；SHA 与 H1 registry 一致。无 Scholar/SciVerse 主题搜索。
- 结果：标准 STATE 已有 ESM2 连续靶点和 full-gene 路径，但默认 FP32、实际 Adam、推理仍为浮点；缺 target 存在静默回退。首投需要实现 bf16 配置、全基因测量 mask、严格覆盖检查、分块推理和原始计数适配。证据见[源码审计](../research/state-training-source-audit.md)。
- 当前配置：1×A100 80 GB、32 vCPU、128 GB RAM、500 GB SSD；标准 8 层/768/12 heads 主干；S0 项目协议基线、S1 全基因首投、S2 DepMap/辅助损失提分。统计方法保留为诊断而非主模型。
- 验证政策：H1 先整体留出；结构冻结后可加入其他背景留出及最终训练，但不得将之后的 H1 得分称为未见背景结果。没有训练、GPU 实测或线上成绩，不承诺超过 STATE 或复刻作者名次。

### 2026-09-14 STATE 预训练权重与初始化策略补全

- 用户问题：是否必须重新训练。定向核实官方已发布资产，确认存在 Replogle ST 权重，修正此前默认随机初始化的安排。
- 调用：HF列表2、模型metadata4、README4、config/hparams YAML4、作者Tahoe推理notebook1，共15次HTTP；11成功、4 README 404。首次按 `search=state` 为空，但官方命名为 ST/SE，完整作者列表命中；不将命名未命中或缺README解释为无权重。
- 结论：首先冻结既有权重做覆盖/加载/推理核验；需要新靶点和完整基因时微调适配层，只有必要时从零训练。完整GPU预算暂不作为立即采购要求。
- 未解决：未下载或加载权重，尚未核实所有目标覆盖、训练暴露与具体许可适用性；`full` 的示例仍只有6,546输出，不能直接承诺免训练完成2026提交。[细节](../research/state-training-source-audit.md#已发布检查点补充不必从零训练)

### 2026-09-14 State 微调教程检索与核验

- 产物：[详细教程](../lessons/10-State微调实战与算力预算.md)、[检查点微调审计](../research/state-checkpoint-finetuning-audit.md)，并在 README/课程路线图加入入口。
- 查询：复用本索引后，Infra Scholar 顺序调用 1 次，完整题名 `Predicting cellular responses to perturbation across diverse contexts with State`；返回并查看前 10 条。State 预印本已命中，不再精炼；Jiang 已有预印本与正式版合并。其他结果只作原始线索，未用于方法性能判断。
- 一手访问：Crossref 4（State/Replogle/Nadig/Jiang）、Zenodo 1、固定 HF tree 2、小型 data_module 2，共 9 次直接 HTTP；加 Scholar 为 10 次，全部成功。两个本地脚本先因没有 requests 未发出网络请求，改用 urllib 完成。无 SciVerse/Paper Schema 调用，不下载大型模型/数据。
- 状态：State、Replogle、Nadig 和五文件 scPerturb 来源采用；Jiang 为后续扩展备选。同步补齐此前仅在容量笔记中的独立数据条目，保留一手链接和本地教程路径。
- 关键边界：公开 checkpoint 不是当前默认 768 模型；微调有原生入口，但基因、靶点、batch 语义和父权重暴露必须审计；HVG/full 都需要正确缺测处理；`ckpt_every_n_steps` 未生效；计数与打包是额外步骤。资源档位为工程预算，不声称完成训练或比赛增益。

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
