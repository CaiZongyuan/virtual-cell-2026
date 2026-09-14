# VC2026：复现 STATE 之后应投入什么

> 当前执行方案已于 2026-09-14 重制为 STATE 主基线及全基因改进版；本文保留为历史研究，资源请求和模型顺序以[首投方案](first-submission-plan.md)为准。

> 核查日期：2026-08-31
> 研究问题：哪些 2025-2026 年单细胞扰动预测架构或思路，比继续微调 STATE 更值得投入？
> 证据口径：官方比赛合同 > 论文原文 > 作者代码、权重和许可证 > 工程假设。论文作者自报的跨任务指标不等同于 VC2026 成绩。

## 0. 结论先行

**不建议把 STATE 换成另一个端到端大模型。** 当前最有证据、也最可执行的路线是把 STATE 降为基线和一个候选 context encoder，再构建以下模块化系统：

1. **核心效应头：response decomposition + response-aligned DepMap MLP。** Molina and Zhang 是本轮唯一明确同时留出整个 CRISPRi 细胞背景和全部测试 target、仍得到正信号的方法证据。它证明双重留出时仍可恢复一部分跨背景保守 target effect，但不恢复匿名背景的完整 interaction；同时只预测伪批量归一化效应，不能独立完成提交。
2. **高优先级升级：AdaPert 式 target-conditioned sparse graph。** AdaPert 在四个 CRISPRi 背景的未见 target 实验中稳定胜 STATE，并在完全留出 K562、只用其余三背景训练的 Systema 实验中也胜 STATE。它最适合增强 target identity、DEG 集合和方向，而不是照搬成最终生成器。
3. **廉价非线性备选：TabICLv2 预测 response PCs。** 先把全基因响应压到 64-128 个主成分，再以冻结表格模型逐分量回归；它适合与 Ridge/MLP 在同一特征、同一 split 下公平竞争。现有论文没有做 VC2026 式 CRISPRi 双重留出，因此只能经消融晋级。
4. **单细胞计数头：先用经验计数生成器，后测 Lingshu-Cell。** Lingshu-Cell 是当前最可运行的全转录组离散生成候选：MIT 代码、85M 权重、原始 UMI 量化。但其 H1 证据使用同背景 150 个扰动监督，不能证明匿名新背景泛化。应只把它作为可替换 count decoder，与效应预测解耦。
5. **只借思路、暂不投入复现：X-Cell 的 NTC-only test-time adaptation。** X-Cell 的任务最接近比赛，但截至核查日，作者仓库仍明确写着 code/weights coming soon；`from_pretrained()` 和 `predict()` 都直接抛 `NotImplementedError`，Hugging Face 没有权重。49 亿参数版本还使用 64-128 张 H200，不能成为本项目当前主线。

一句话方案：**用 DepMap/STRING/ESM 等 target prior 预测可迁移的伪批量 delta，用目标 NTC 只做保守的 context gating 和测序分布校准，再由独立 count decoder 生成 400 个原始计数细胞；STATE 只作为基线与集成成员。**

上述方案的工程接口、V0 数学定义和首个纵向切片见[分解式模型实现规格](model-implementation-spec.md)。

### 当前榜单告诉我们先补什么

按 2026-08-30 官方榜单快照，第一名 `GeroAI_v12` 总分 0.2112，名为 `STATE baseline` 的第二名为 0.1894。第一名减去该 STATE entry 的 scaled 指标差为：

| PDS | MSE | Jaccard | NMAE | direction fidelity | reach |
|---:|---:|---:|---:|---:|---:|
| +0.0029 | +0.0194 | -0.0082 | **+0.0463** | +0.0154 | **+0.0550** |

这是排行榜事实，不是架构归因；entry 名称也不能证明其具体训练配置。但它给出明确的工程顺序：**保住 PDS，优先提高 reach、NMAE 和 MSE，Jaccard 暂不单独追。** 因此 response-aligned magnitude head、AdaPert 式高置信响应排序和 count calibration 的优先级高于扩大 backbone。这里的 `fidelity` 是差异表达方向 fidelity，不是图像领域的 Frechet Inception Distance。

## 1. 先纠正 VC2025 的事实

“VC2025 冠军是微调 STATE”不成立。Arc 官方赛后总结写明：

- 冠军 `BM_xTVC / xTrimoSCPerturb` 以改进的 **scFoundation** 为核心，结合 protein embeddings、公开扰动数据、DEG frequency、mean expression、pseudobulk 和 metric-aware 目标；官方没有把它描述为 STATE 微调。
- 亚军使用全连接 residual delta 模型，并加入 aggregated control、ESM-2 和 UMI indicator。
- 季军使用 pseudobulk/Wilcoxon 摘要、跨细胞系相似性聚合和 PDS scaling。
- 生成式 flow-matching 方案使用 H1 target perturbations 做了微调；这个监督条件在 VC2026 的匿名 D/E/F 不存在。

来源：[Arc VC2025 official wrap-up](https://arcinstitute.org/news/virtual-cell-challenge-2025-wrap-up)。因此，上一届真正可迁移的不是“继续微调 STATE”，而是 **residual delta、target prior、跨背景 retrieval、显式幅度建模和 metric-aware ensemble**。

## 2. VC2026-like 证据门槛

官方任务是：只给匿名新背景的 NTC 原始计数和 target symbol，预测 300 个 CRISPRi target 在每个背景中的 400 个细胞、18,533 基因原始整数计数。最终 D/E/F 与 A/B/C 是不同细胞系和不同 target panel；六项缩放指标等权。[官方数据合同](../Official-website/About-the-Data.md)；[官方 FAQ](../Official-website/FAQs.md)。

本调查不把“超过 STATE”按论文标题理解，而按以下六个问题逐项审查：

| 轴 | 真正接近 VC2026 的条件 |
|---|---|
| 新 context | 整个测试背景的扰动真值为 0；允许的只有 NTC |
| 新 target | target 的响应在训练所有背景中都未出现，或至少明确报告 target-held-out |
| 模态 | CRISPRi，而不是 CRISPRa、KO、过表达、药物或细胞因子 |
| 输出 | 全 18,533 基因、400-cell 分布、原始整数 counts |
| 比较 | 同数据、同 split、同指标下与 STATE 比较；否则只算间接证据 |
| 可执行性 | 代码、权重、许可证、数据和硬件合同可核验 |

目前**没有任何公开方法同时满足六项**。所以正确的工程问题不是“哪篇论文已经赢了 VC2026”，而是“哪个模块在它真正覆盖的轴上有最强证据”。

## 3. 候选总表

符号：`是` 表示论文实际验证；`否` 表示明确不支持；`部分` 表示只覆盖组合中的一轴或依赖额外监督；`未知` 表示原文没有足够合同。

| 方法 | 新 context 仅 NTC | 新 target | CRISPRi | 全基因 / raw-count 分布 | 对 STATE 的证据 | 可运行与许可 | 本项目决定 |
|---|---|---|---|---|---|---|---|
| Response decomposition + Ridge/MLP | 背景完全留出；不使用 NTC descriptor；有 double-unseen | **是** | **是** | 否；2k HVG pseudobulk delta | 同四背景 context holdout 直接比较；double-unseen 时 STATE 因 one-hot target 无法参评 | 论文 CC BY 4.0；代码仓库无 license；CPU 可重实现 | **主效应头，立即做** |
| AdaPert v2 | 是；完全留出 K562 的实验 | 是；常规实验为 target-held-out | 是 | 否；约 5k/3,352 HVG，log1p 均值 | 同 Systema 下整体胜 STATE；常规 Discrim L1 略有例外 | 未公开代码/权重/硬件 | **高优先级重实现/消融** |
| TabICL / TabPFN response-PC | 遗传实验未验证 | 是；同背景 target-held-out | 是 | 否；128-PC pseudobulk | 没有 VC-like STATE 比较 | 应用代码 MIT；TabICLv2 BSD；TabPFN 新权重 NC | **先测 TabICL，低成本备选** |
| Lingshu-Cell | 否；H1 有 150 个同背景 perturbations | H1 测试 target 留出，但训练加入与 300-target panel 重叠的外部响应 | 是 | **18,080 基因、量化 UMI 单细胞** | H1 赛后指标，不是新背景；非 VC2026 六指标 | MIT；85M 权重约 917 MB | **只作 count decoder 候选** |
| X-Cell / X-Cell-Ultra | **是；NTC-only TTA** | 评估 target 多在其他背景见过 | 是 | 约 19k 基因但 log1p CP10K 输出 | 同数据比较胜 STATE，但不是六指标 | 当前是占位代码；无权重；CC BY-NC-SA | **等待资产，只借 TTA/先验思路** |
| STATE | 原论文主跨背景实验含 30% 目标背景 perturbations；另有 zero-shot 运行 | one-hot target，未见 target 能力弱 | 是 | 2k HVG、归一化表达 | 基线本身 | 官方对本比赛有专项许可 | **保留基线/集成** |
| Stack | query 可为新背景，但 prompt 通常含另一数据集的 perturbation cells | 没有 VC-like genetic target 证据 | 生成实验主要是药物/细胞因子 | 15,012 基因、归一化表达 | 不同任务下比较 | 代码和权重/输出均 NC；奖金赛许可未澄清 | **不进提交，最多借 context attention** |
| AlphaCell | 是 | **否；原文明确依赖离散 perturbation ID** | 主要 OTF/药物，不是 CRISPRi 主证据 | 19,253 基因、log1p CP10K | 新 context 上作者报告胜 STATE，但模态不匹配 | 无代码/权重；论文 CC BY-NC-ND；1.2B decoder | **淘汰端到端复现** |
| PerturbNet | 否；原文明说不能“双未见” | 是 | 有 CRISPRi/CRISPRa | ZINB raw-count 分布，但基因面板较小 | 无 VC-like STATE 比较 | GPLv3 代码；公开处理数据/权重 | **只作 ZINB decoder 对照** |
| MORPH | NTC-only fine-tune 不能恢复 target interaction | 是 | 是 | pseudobulk / 有条件生成，不是 18,533 raw counts | decomposition 复评中弱于直接 DepMap MLP | MIT 代码；单 GPU | **淘汰整模，保留 DepMap prior** |
| C3TL | **否；使用目标背景约 8% perturbation 真值** | 部分 | 扰动基准相关 | 2k HVG pseudobulk | 报告较 STATE 快约 30 倍，但合同不同 | 约 2.1 GB VRAM | **不作 final-zero-shot 主线** |
| MapPFN | **否；context 是 interventional context** | 部分 | CRISPR KO | 仅约 50 genes | 无 VC-like 直接证据 | 约 25M；10-36 A100/H100-hours | **任务不匹配，淘汰** |
| scDiVa | 否；Adamson/Norman 上 fine-tune | 部分 | 主要同背景 CRISPR | 单细胞离散生成，但非全比赛面板 | 无严格新背景 STATE 比较 | 94.5M；用 59M proprietary cells 预训练；4xA100、4 epochs | **不投入** |
| dbDiffusion | 否；单 context target-held-out | 是 | 遗传扰动 | 约 1,500 genes | 无 VC-like 新背景比较 | 有 repo，但未声明代码 license；论文 CC BY-NC-ND | **不投入** |
| Large Perturbation Model | “未见实验”是 PRC 组合，不等于匿名 NTC-only context | in-vocabulary 组合 | 混合 CRISPR/药物 | z-normalized experiment-level readout；非 raw single-cell | 无 VC-like STATE 比较 | Apache-2.0 `perturblib`；无提交级权重合同 | **仅作多实验数据接口参考** |
| UniPert-G2CP | 否；五个 context 各自训练 | 可编码未见基因/蛋白 | 主要 KO/LINCS 到药物迁移 | 978 L1000 genes 或形态特征 | 无 VC-like STATE 比较 | UniPert GPLv3；代码公开 | **只候选 target encoder** |

## 4. 最值得投入的三条技术线

### 4.1 第一优先：response-aligned effect model

Molina and Zhang 把 CRISPRi pseudobulk delta 分解为：

```text
delta(context, target, gene)
  = global response
  + context template
  + conserved target effect
  + context x target interaction
```

他们在 K562、RPE1、HepG2、Jurkat 四个 CRISPRi screen 中发现：共享 template 低维且容易预测；target-specific residual 更高维；只看 NTC 不能恢复真正的 `context x target` interaction。把 DepMap CRISPRGeneEffect 的共必需性向量直接映射到 template-removed response，比先压缩成复杂 MORPH 表征更有效。[论文](https://doi.org/10.64898/2026.07.24.740459)；[作者代码](https://github.com/xinyizhanglab/perturbation-decomposition)。

最关键的 double-unseen 结果为 perturbed-reference Pearson：

| 留出 context | Ridge | MLP |
|---|---:|---:|
| K562 | 0.102 | 0.164 |
| RPE1 | 0.211 | 0.231 |
| HepG2 | 0.276 | 0.288 |
| Jurkat | 0.161 | 0.194 |

这里 target 同时从三个 source contexts 的训练响应中移除，目标 context 也完全留出。相比之下，论文重跑的 STATE zero-shot 对 template-removed signal 很弱。这个证据比“某模型在同细胞系 target split 上胜 STATE”更接近 VC2026。

边界同样重要：该模型主要恢复跨细胞系保守的 target component，不能恢复 target-context interaction；输出是 2,000 HVG 的伪批量归一化 delta。对比赛而言，它是**最可靠的方向/效应先验**，不是完整模拟器。

还要避免一种实现层误读：论文 4.5.1 的三源 Ridge/MLP 没有显式 cell-line descriptor，也不读取目标 NTC 来学习 target-specific response map；它把三个 source contexts 的响应合并后，预测一个 source-averaged response。double-unseen 的正结果证明“保守的、template-removed target effect 可迁移”，不证明模型恢复了匿名新背景中的完整响应。论文所有 zero-shot 模型都没有恢复 `context x target` interaction；加入 30% 目标背景扰动真值后，这个 interaction 才开始改善。因此本项目必须把 PRD 严格命名为 **target-effect / response-alignment 模块**，再由目标 NTC template、保守 context gate 和 count decoder 补齐输出合同。

### 4.2 第二优先：AdaPert 式稀疏 target graph 和 anti-collapse loss

AdaPert 针对一个常见失败模式：18k 基因中真正响应的基因很少，普通 MSE 被大量 non-responsive genes 主导，模型会向平均响应塌缩。它为每个 target 从 STRING/GO 类图中选择一个 perturbation-specific sparse subgraph，并把损失拆为：

- 全表达 reconstruction；
- non-DEG 抑噪；
- response-aware alignment，使 target graph 表征对齐其 DEG 方向。

在四个 CRISPRi context 的 target-held-out 实验中，它在 Pearson delta、PDS 和多数 DEG 指标上胜 STATE、GEARS、TxPert、MORPH；在 `train=RPE1+HepG2+Jurkat, test=K562` 的完全 context holdout 中，Systema 的 perturbation-centered Pearson delta 为 0.7826，STATE 为 0.7184，centroid accuracy 为 0.6885 对 0.6217。与此同时，常规 Discrimination L1 并非所有设置都胜 STATE，因此不能把“Systema 全胜”扩大成“六项 VC2026 全胜”。[AdaPert v2 / ICML 2026](https://arxiv.org/abs/2602.18885v2)。

适合迁移的不是整套代码，而是两个部件：

1. `target prior -> sparse graph selector -> response-PC target embedding`；
2. `mean loss + DEG direction/rank + non-DEG stability` 的多目标损失。

工程风险：论文未公开代码、权重、训练硬件；输入使用约 5,000 或 3,352 HVG 的 log1p 表达，不生成原始 counts。论文还使用 GPT-4o 补基因描述和 OpenAI text embedding；本项目应以可复核的本地 ESM2/STRING/DepMap 特征替代，避免外部模型漂移和许可证不确定性。

### 4.3 第三优先：把生成问题从效应问题中拆开

VC2026 的 PDS/MSE/NMAE 主要要求正确的群体效应；Jaccard/fidelity/reach 又读取 400 个细胞的秩和显著性。因此不能用同一模型同时承担“因果方向”和“测序噪声”而无法诊断。

推荐两级 count decoder：

1. **默认 decoder：** 从目标 NTC 分层抽样真实细胞、库大小和零模式，在 count/rate 空间施加预测 delta，并以 multinomial 或 negative-binomial 重新采样整数 UMI。它便宜、可校准、能明确控制 effect scale 和 overdispersion。
2. **升级 decoder：** Lingshu-Cell 的 masked discrete diffusion。其开源权重直接量化 UMI：0-99 保留整数，较大 counts 用近似两位有效数字的 bins；VCC checkpoint 为 85M、约 917 MB，模型按 18,080 genes 生成细胞。[论文](https://arxiv.org/abs/2603.25240)；[MIT 代码](https://github.com/alibaba-damo-academy/Lingshu-Cell)；[权重](https://huggingface.co/bibona/lingshu-cell)。

不能直接提交原 Lingshu checkpoint：它的训练含 H1 的 150 个 target 和外部数据，背景用离散 token，不会自然识别 A/B/C 或 D/E/F；词表也是 18,080 而不是 18,533。正确实验是让 Lingshu 只学习 `NTC template + desired delta -> raw cells`，或在 18,533 统一面板上训练一个更小的 residual MDDM。

## 5. 为什么其他“超过 STATE”的结果不能直接采用

### X-Cell：最接近问题，但目前不可运行

X-Cell 在 25.6M 个 CRISPRi cells、16 contexts 上训练扩散 LM，并融合 ESM2、STRING、GenePT、DepMap、Cell Painting 和 scGPT prior；X-Cell-Ultra 在全新细胞背景只用 NTC 做 self-supervised test-time adaptation，这个思路与比赛高度一致。[论文](https://doi.org/10.64898/2026.03.18.712807)。

但当前公开状态不能支撑投入：作者 [GitHub](https://github.com/xaira-therapeutics/x-cell) HEAD `7195c647` 明写 “weights and inference code coming soon”；`src/xcell/model.py` 的加载和推理均未实现；[Hugging Face](https://huggingface.co/Xaira-Therapeutics/X-Cell) 只有 README 和图片。55M 模型尚不可复现，4.9B 版本用 64-128 张 H200，缩放扫描也显示 1.6B 以后 DE Pearson 已接近平台。代码/数据声明为 CC BY-NC-SA 4.0，在奖金赛使用前还要书面确认。

因此只迁移三点：NTC-only TTA、cross-attention target priors、iterative refinement；不要复刻 4.9B 模型。

### AlphaCell：解决新 context，不解决新 target

AlphaCell 的全基因潜空间、MoE decoder 和 OT conditional flow matching 有吸引力，并在药物和过表达的新 context 任务中报告优于 STATE。但原文明确说明：flow model 使用可学习的离散 perturbation ID，**不能预测未见扰动**。[论文](https://doi.org/10.64898/2026.03.02.709176)。其输出是 19,253 gene 的 log1p CP10K，不是 raw counts；公开材料未给代码/权重或训练时间，decoder 已有 1.2B 参数。VC2026 同时换 context 和 target panel，故淘汰端到端复现，只保留“潜空间 flow 作为可选 decoder”的远期想法。

### Stack：真正需要的是 perturbed prompt，比赛只有 NTC

Stack 的 tabular attention 和 cell prompting 很适合“把另一个数据集的条件迁移到 query cells”。但论文的生成验证主要是药物/细胞因子，prompt 含相应 perturbation cells；没有证明仅凭 target symbol 和匿名 NTC 能完成 CRISPRi 双重外推。[论文](https://doi.org/10.64898/2026.01.09.698608)；[代码](https://github.com/ArcInstitute/stack)。此外代码为 CC BY-NC-SA，模型权重和输出许可证明确排除直接或间接 monetary compensation；VC2026 FAQ 只给 STATE 专项许可，没有给 Stack。没有 Arc 书面确认前不得用于提交。

### PerturbNet / MORPH：可拆模块，整模不晋级

- PerturbNet 的 GO target encoder 和 ZINB count likelihood 值得做小型消融；正式论文却明确写明不能预测“unseen perturbation on unseen cell type”，正是比赛的核心条件。[论文](https://doi.org/10.1038/s44320-025-00131-3)；[GPLv3 代码](https://github.com/welch-lab/PerturbNet)。
- MORPH 有 MIT 代码和 DepMap prior，但 response-decomposition 复评显示，原始 DepMap profile 经直接 Ridge/MLP 映射比 MORPH 中间表征更能保留 target-specific signal；目标 NTC 上无监督 fine-tune 也没有恢复 interaction。[MORPH](https://doi.org/10.1101/2025.06.27.661992)；[代码](https://github.com/uhlerlab/MORPH)。所以保留 prior，删除复杂 conditional VAE。

### TabPFN / TabICL：适合小表格回归，不是已经证明的 context model

Palla et al. 将 target effect 压到 128 response PCs，使用 target embeddings 逐 PC 回归，TabICL/TabPFN 在五个 Perturb-seq 的同背景 target-held-out 任务中胜多种专用模型；但其 genetic benchmark 没有完全留出细胞系，cell-level 跨背景实验又是 OpenProblems 药物任务。[论文](https://doi.org/10.64898/2026.06.28.735106)；[MIT 应用代码](https://github.com/royerlab/tfm-perturbation)。

TabICLv2 代码/权重为 BSD 3-Clause，适合直接消融；TabPFN 当前默认权重为 non-commercial license，奖金赛使用前需要授权。方法价值在于“强回归器 + response PCA”，不是它已经解决了 VC2026。

### C3TL、MapPFN、scDiVa、dbDiffusion、LPM、UniPert-G2CP

- **C3TL** 的高效迁移使用目标背景约 8% perturbation 真值，只有约 2.1 GB VRAM、报告比比较模型快约 30 倍，但不满足 final NTC-only。[论文](https://arxiv.org/abs/2603.13051)。
- **MapPFN** 的 context 是 interventional context；实验为 CRISPR KO、约 50 genes，25M 模型的报告训练量约 10-36 A100/H100-hours，输入合同不匹配。[论文](https://arxiv.org/abs/2601.21092)。
- **scDiVa** 是有价值的离散生成研究，但扰动实验在 Adamson/Norman 上微调，不是完全新背景；模型约 94.5M 参数，观察性预训练使用约 5,900 万个 proprietary cells，训练为 4xA100、4 epochs。[论文](https://arxiv.org/abs/2602.03477)。
- **dbDiffusion** 在单 context 的 unseen target 上去偏并生成分布，只有约 1,500 genes；代码仓库未声明 license，且没有新背景证据。[PNAS](https://doi.org/10.1073/pnas.2525268122)。
- **Large Perturbation Model** 把 perturbation/readout/context 写成 PRC tuple，适合统一多实验数据，但“unseen experiment”仍是 in-vocabulary PRC 组合；输出为 experiment-level z-normalized readout，不是 400-cell raw counts。[论文](https://doi.org/10.1038/s43588-025-00870-1)；[Apache-2.0 代码](https://github.com/perturblib/perturblib)。
- **UniPert-G2CP** 的蛋白序列 + ESM + sequence-similarity GNN 可作为未见 target encoder；主任务却是 LINCS 的遗传到化学迁移，只有 978 landmark genes，并按 cell line 独立训练。[预印本](https://doi.org/10.1101/2025.02.02.635055)；[GPLv3 代码](https://github.com/TencentAILabHealthcare/UniPert)。

## 6. 推荐模块化架构

```text
public CRISPRi responses ──> response decomposition ──> conserved target-effect memory
DepMap / STRING / ESM2 ───> Ridge/MLP + AdaPert selector ─┘
                                                   |
target-context NTC ─> set encoder / retrieval ─> conservative context gate
                                                   |
                         direction head + magnitude/DE calibration
                                                   |
target NTC raw cells ─> empirical NB decoder ──────┼─> 400 x 18,533 raw counts
                         optional residual MDDM ────┘
```

具体合同：

1. **Target encoder**：DepMap CRISPRGeneEffect PCA 为主；拼接 ESM2、STRING 和基础表达/必需性。用 modality dropout 防止某一 prior 缺失时崩溃。
2. **Effect bank**：每个公开 screen 生成匹配 NTC 的 pseudobulk log-count delta、DEG set、direction、effect norm 和 uncertainty；不把不同 assay 的绝对 scale 直接混合。
3. **Response head**：先 Ridge，再 2-layer MLP；可选 AdaPert sparse graph；输出 64-128 response PCs、独立 effect norm 和 DEG probability/direction。
4. **Context gate**：以匿名 NTC set embedding、基础 target expression、pathway activity、library-size/zero-rate 为输入，只决定 source weighting、shrinkage 和 scale。PRD 已证明 NTC 不能恢复完整 interaction，因此该模块必须有强收缩与不确定性，不能自由生成大残差。
5. **Count decoder**：从真实目标 NTC 保留细胞状态、`ntc_id`、library size 和 sparsity；施加 target delta 后生成整数 counts。只有当 Lingshu residual MDDM 在严格 LOCO 下改善 Jaccard/fidelity/reach 且不损害 PDS/MSE/NMAE，才替换经验 decoder。
6. **Ensemble**：在 effect/rate 空间对 STATE、Ridge/MLP、AdaPert-like 预测集成，而不是混合最终随机 counts；最后统一采样，降低 Monte Carlo 噪声。

## 7. 最小消融矩阵

所有 effect-head 实验固定同一个经验 count decoder；所有 decoder 实验固定同一个 effect head。外层必须 `leave-one-study-context-out`，并在留出 context 中再留 target；至少包含一个像 PRD 一样将测试 target 从全部 source contexts 移除的 double-unseen split。

| ID | 唯一变化 | 要回答的问题 | 晋级指标 |
|---|---|---|---|
| E0 | STATE starter | 可复现下界 | 六项分数、资源和失败率 |
| E1 | target mean delta | 共享 effect 能解释多少 | 对 E0 的增益 |
| E2 | DepMap Ridge, 50 PCs | response alignment 是否成立 | PDS、NMAE、reach |
| E3 | DepMap 2-layer MLP | 非线性是否稳定胜 Ridge | mean + worst-context |
| E4 | E3 + ESM2/STRING | 多 prior 是否补 target identity | double-unseen PDS/DE |
| E5 | E4 + AdaPert sparse selector | 是否减少 mean collapse | Jaccard、fidelity、reach，不牺牲 MSE |
| E6 | E4，MLP 换 TabICLv2 | 表格 ICL 是否值回推理成本 | 同 split 六项与 wall time |
| C1 | E4 + NTC context gate | NTC 是否能安全改善 scale/source weight | context swap 必须崩；worst-context 不降 |
| C2 | C1 + NTC-only TTA | X-Cell 式适配是否有独立收益 | 禁用 target label 后仍有收益 |
| G0 | NTC residual bootstrap + multinomial/NB | 经验 decoder 基线 | 六项，重点四个 DE 指标 |
| G1 | G0 + ZINB overdispersion head | gene-wise variance是否必要 | Jaccard/fidelity/reach |
| G2 | residual MDDM/Lingshu adapter | 离散扩散是否改善真实异质性 | 必须胜 G1 且不过拟合 assay |
| Z1 | E0/E4/C1 effect-space ensemble | STATE 是否提供互补残差 | 六项总分和每 context |

最低统计纪律：Ridge 为确定性；神经/随机生成配置至少 3 seeds；400-cell 生成至少做 3 次 Monte Carlo 重采样；报告每项 raw metric、scaled surrogate、三个 context 分数和最差 context，而不只报平均总分。

## 8. 数据、算力与停止规则

### 数据优先级

1. K562 GWPS：给多数比赛 target 建立直接 effect memory。
2. K562/RPE1/HepG2/Jurkat common-essential CRISPRi：训练和验证 response-aligned 跨背景映射。
3. Jiang 六细胞系 CRISPRi：扩大 context 多样性，但需单独建 assay/study batch。
4. DepMap CRISPRGeneEffect、STRING、ESM2：target prior；所有版本固定并记录许可。
5. H1 2025 Flex：只用于 Flex count calibration 与 held-out target 验证，不能代表新 context。
6. 官方 A/B/C 与未来 D/E/F NTC：只做 context conditioning、无监督适配和计数分布校准。

X-Atlas/Pisces 当前数据页面仍为 coming soon，不列入可交付依赖。

### 增量算力

| 模块 | 一手公开合同 | 本项目预算判断 |
|---|---|---|
| PRD Ridge/MLP | repo 写明 Ridge 单 cell line 约 10 min CPU；处理后数据约 90 MB | 0 GPU；首周完成 |
| TabICLv2 response-PC | 冻结模型、每个 PC 一次 forward | `[工程估算]` 8-16 GB GPU，2-10 GPU-h 完成 folds |
| AdaPert-like | 作者未披露硬件/时长，代码未公开 | `[工程估算]` 先小图/2k HVG，20-80 GPU-h；未胜 E4 即停 |
| Lingshu VCC | 85M；550k step；作者用 16xA800；精确 wall time未知 | 先只做推理；重训完整模型不在默认预算 |
| X-Cell Mini/Ultra | Mini 55M 尚无权重；Ultra 4.9B，64-128xH200 | 当前 0 预算；资产公开后再重估 |
| Stack | 217M aligned model；H100 80 GB；预训练约 2-3 days | 许可证未解决前 0 预算 |
| AlphaCell | 1.2B decoder；训练 2.2亿 observation + 9千万 perturbation profiles | 不预算 |

沿用现有容量计划：Phase 1 下载约 23.3 GB，Phase 2 约 43.5 GB；推荐 64 GB RAM、300 GB 工作盘。GPU 总预算不因本调查扩大：先把绝大多数组合放在 CPU Ridge/MLP 和冻结 TabICL 上筛掉，只有 E5/G2 过门后再批准 60-100 T4-hours 或等价的约 20-40 A100-hours。

### 停止规则

- 某模块只在同背景 target split 改善、在 LOCO 或 double-unseen 不改善：停止。
- PDS 上升但 `MSE + NMAE + reach` 明显下降：停止，不以单项榜分辩护。
- 平均提升但任一 context 崩溃：只允许进入低权重 ensemble，不作主模型。
- count decoder 只改善 UMAP 或其他非官方分布可视化，却不改善官方 DE 指标：停止。
- 需要目标背景 perturbation truth、未获许可权重或未公开关键资产：不进入 final pipeline。

## 9. 资料与检索台账

本轮先查阅 `docs/references/INDEX.md`。主调查与背景核验合计顺序执行三次 Infra Scholar 查询，每个查询只调用一次且没有继续精炼：

1. `CRISPRi Perturb-seq zero-shot unseen cell context unseen perturbation STATE benchmark diffusion in-context response decomposition 2026`
2. `single-cell CRISPRi perturbation prediction unseen cell context unseen target zero-shot generative model 2025 2026`
3. `X-Cell Lingshu-Cell AlphaCell Large Perturbation Model perturbation response decomposition single-cell`

第一轮覆盖 benchmark、PerturBench、PerturbNet、dbDiffusion 和表格模型线索；后两轮用于补全点名方法，但没有出现改变主决策的新候选，随后停止 Scholar 扩搜。另对 Paper Schema 执行一次 `single-cell perturbation prediction`、年份下限 2024 的搜索，并对 C3TL、MapPFN、AdaPert、ScDiVa 和 PerturBench 读取结构化材料与 evidence；该 AI 论文语料只作候选定位。`sciverse` 全文服务因本机未设置 `SCIVERSE_API_TOKEN` 无法调用；该失败没有被表述为未收录。之后按 DOI、arXiv/bioRxiv、出版社页面、Crossref/OpenAlex 元数据和作者仓库逐项核验，关键判断均回到论文原文、官方比赛页面和作者资产。

主要一手来源还包括：[STATE](https://doi.org/10.1101/2025.06.26.661135)、[Ahlmann-Eltze et al.](https://doi.org/10.1038/s41592-025-02772-6)、[Csendes et al.](https://doi.org/10.1186/s12864-025-11600-2)、[C3TL](https://arxiv.org/abs/2603.13051)、[MapPFN](https://arxiv.org/abs/2601.21092)、[scDiVa](https://arxiv.org/abs/2602.03477) 和 [dbDiffusion](https://doi.org/10.1073/pnas.2525268122)。

未解决缺口：A/B/C 与 D/E/F 扰动真值不可见；AdaPert 无公开代码/硬件；X-Cell 无可用权重/实现；Lingshu 未在匿名新背景评估；没有论文使用 VC2026 的六项 rule-v3 scaled score 做上述架构的同场比较。因此本文给出的是**投入顺序和可证伪实验**，不是获胜保证。
