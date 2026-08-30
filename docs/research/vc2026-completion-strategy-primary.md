# 高质量完成 Arc Virtual Cell Challenge 2026：一手资料核查与竞争性实施路线

> 核查日期：2026-08-30
>
> 研究问题：在不把论文自报结果、排行榜经验和工程猜想混为一谈的前提下，怎样完整、稳健且有竞争力地参加 VC2026？
>
> 证据优先级：Arc 官方比赛页面与官方评分代码 > 原始论文/作者仓库 > 本仓库可复核实测 > 工程假设。
>
> 当前结论不是获胜保证；D/E/F 真值尚未公开，所有模型收益都必须在严格跨背景验证中证明。
>
> 具体数据下载、当前机器适配和 GPU-hours 见 [数据与算力容量规划](vc2026-data-compute-capacity-sources.md)。

## 0. 结论先行

最有胜算的路线不是直接训练一个最大的“虚拟细胞”模型，而是先建立一个不会自欺的实验系统，再让复杂度逐级过关：

1. **把官方合同和六项评分做成不可回归的自动测试。** VC2026 要求在三个匿名新背景中，为 300 个 CRISPRi 靶点各生成 400 个细胞的 18,533 基因原始计数；最终名次只看另一组三个背景 D/E/F。格式、背景标签、目标面板或基因顺序任何一个错位，都足以让好模型失效。[官方数据说明](../Official-website/About-the-Data.md)；[官方 FAQ](../Official-website/FAQs.md)
2. **主要验证单位必须是完整细胞背景和完整研究，而不是随机细胞。** 最终轮同时改变细胞背景和扰动面板；随机 cell split 会把同一批次、同一细胞系、同一扰动的近重复信息泄漏到验证集。推荐外层采用 leave-one-study-context-out，并在留出背景内再留出目标；内层才用于调参。
3. **先做统计残差模型，再做集合生成模型。** 2025 年官方赛后总结显示，前三名都把公开扰动数据、统计摘要、目标先验或残差学习与神经网络结合；独立基准研究也警告，复杂深度模型并不自动胜过简单线性基线。[Arc 2025 wrap-up](https://arcinstitute.org/news/virtual-cell-challenge-2025-wrap-up)；[Ahlmann-Eltze et al.](https://doi.org/10.1038/s41592-025-02772-6)
4. **推荐主模型是“可迁移扰动效应 + 背景调制 + 计数生成”的混合系统。** 从目标背景 NTC 编码当前状态，从多背景公共 CRISPRi 数据学习目标效应与 target-context interaction，再以目标背景的库大小、零率和细胞状态为锚生成 400 个整数计数细胞。统计模型、STATE 类集合模型和 NTC-only 测试时适配应作为可独立消融的组件，而不是一次性捆绑。
5. **用六项指标做多目标选择，不为单一 PDS 调幅度。** `pds_cosine` 看扰动身份方向图案；表达 MSE 和 LFC NMAE 看数值幅度；三个 DE 集合/方向指标看响应基因的集合、符号和排序深度。官方总分对六项缩放分数和三个背景都等权平均。[cell-eval2 vcc2026 规范](https://github.com/ArcInstitute/cell-eval2/blob/5e64833518a6603a0301cbe28185d49c30f4a986/docs/vcc2026_metrics/vcc2026-metrics-brief.md)
6. **最终轮必须是冻结模型后的无标签域适配和生产运行。** 2026-10-22 收到 D/E/F NTC 后，只允许预先定义的 NTC 条件化、无监督适配、生成、预检和候选选择；不能临时根据猜测的细胞系身份改模型，也不能靠反复提交探索最终真值。最终截止日是 2026-11-05。[官方 FAQ](../Official-website/FAQs.md)

一句话方案：**用多研究、多细胞系 CRISPRi 数据训练一个层次化 delta 模型，以 NTC 集合编码匿名背景，以功能/共必需性先验编码靶基因；通过严格的“研究 + 背景 + 靶点”双重留出选择它，再用真实 NTC 的细胞状态和测序深度生成合法 raw counts，最后与简单统计基线做保守集成。**

### 当前 readiness gap

截至 2026-08-30，仓库可见的任务代码只有 [`scripts/vc2026_control_audit.py`](../../scripts/vc2026_control_audit.py) 和一个测试 notebook；尚未发现可复现的 `cell-eval2` evaluator wrapper、公共扰动数据 ETL/去重、跨背景 split、统计 baseline、raw-count generator 或 `.vcc` submission pipeline。这意味着项目已经完成“理解并审计输入”，但还没有形成“训练 -> 严格验证 -> 生成 -> 打包”的参赛闭环。

因此主线优先级必须是：**E0 评分与合同 -> 公共数据层 -> E2 统计 delta -> E3 count generator -> E4/E5 神经模型**。如果直接跳到 STATE/X-Cell 类大模型，失败时将无法区分数据、split、effect、count decoder 和打包哪一层出错。

## 1. 先固定官方任务合同

### 1.1 生物学任务是什么

- **CRISPRi（CRISPR interference）**用失活 Cas9 和抑制结构域降低目标基因的转录，不切断 DNA。比赛靶点被官方筛到超过 80% 的敲低效率，但“目标基因下降”不是评分重点；评分代码会排除该靶基因。[官方数据说明：靶标选择](../Official-website/About-the-Data.md#靶标基因选择)
- **Perturb-seq**把池化 CRISPR 扰动与单细胞 RNA 测序结合，从而观察每个扰动后的全转录组群体。破坏性测序不能把同一个细胞在扰动前后配对，因此模型实际学习的是“对照细胞分布 -> 扰动细胞分布”，不是逐细胞监督映射。
- **NTC（non-targeting control，非靶向对照）**是携带不靶向人基因 guide 的细胞。它给出当前匿名细胞背景、实验流程和测序深度的联合观测。
- **UMI（unique molecular identifier，唯一分子标识）**用于把扩增得到的重复读段归并为原始分子计数。比赛提交的是每个细胞、每个基因的非负整数 UMI count，而不是 `log1p` 或归一化表达。

官方生成了六个不同组织来源的细胞系，验证轮只公开 A/B/C 的 NTC，最终轮公开另外三个 D/E/F 的 NTC；具体细胞系身份不会公布。今年没有挑战赛训练集。模型输入是匿名背景 NTC 与靶基因符号，输出是 CRISPRi 后的单细胞原始计数。[官方数据说明，第 5-9 行](../Official-website/About-the-Data.md)

当轮靶点并非随机抽取：官方说明其靶向敲低效率超过 80%，并被选择为产生强 perturbation/response 的目标。[官方数据说明：靶标选择](../Official-website/About-the-Data.md#靶标基因选择) 因此离线代理赛若随机抽取大量近零效应 target，会错误估计任务难度和最佳 shrinkage；应尽量在 knockdown QC 与 effect-size 分布上匹配官方 target selection。

### 1.2 每轮不可变的形状

| 项目 | 官方合同 | 工程含义 |
|---|---:|---|
| 背景 | 3 | A/B/C 与 D/E/F 必须原样保留，不能重排 |
| 每背景 NTC | 18,400 cells | 46 个 `ntc_id`，每个 400 cells；可建模 guide 间技术变异 |
| 靶点 | 300 | 同一轮三个背景共享面板；验证和最终面板不同 |
| 每靶点每背景输出 | 恰好 400 cells | 总行数 `300 × 400 × 3 = 360,000` |
| 基因 | 18,533 | 必须严格按当轮 `gene_names.csv` 顺序 |
| `X` | raw counts | 有限、非负整数；每细胞总计数不超过 1,000,000 |
| 提交 | 一个 H5AD 打包成 `.vcc` | `obs` 只含被要求的扰动行，不含 NTC 预测 |
| 稀疏项上限 | 4,750,000,000 | 必须 CSR/CSC，删除显式零；密集矩阵天然超限 |

来源：[官方数据说明：文件与提交格式](../Official-website/About-the-Data.md#文件格式)；[官方 FAQ：原始计数和稀疏限制](../Official-website/FAQs.md#故障排除)。

这里存在一个容易误读的官方层级差异：`cell-eval2` 指标规范描述的是评分器内部可接受的通用输入，其中写有 control label 且预测细胞数不受限；比赛上传合同则明确要求**不含 NTC 行且每个 target-context 恰好 400 cells**。参赛提交必须以 `vcc prep` 和比赛数据页的严格合同为准，不能拿评分库的通用输入说明覆盖上传校验器。[评分规范](https://github.com/ArcInstitute/cell-eval2/blob/5e64833518a6603a0301cbe28185d49c30f4a986/docs/vcc2026_metrics/vcc2026-metrics-brief.md#0-scope-and-parameters)；[提交格式](../Official-website/About-the-Data.md#提交文件)

### 1.3 当前仓库实测告诉了我们什么

本仓库已经对真实 A/B/C NTC 做了全量审计，结果见 [`output/vc2026-control-audit/audit-summary.json`](../../output/vc2026-control-audit/audit-summary.json) 和生成脚本 [`scripts/vc2026_control_audit.py`](../../scripts/vc2026_control_audit.py)：

- 三个背景均满足 18,400 cells、18,533 genes、46 个 NTC guide、每 guide 400 cells；值为有限、非负整数且无显式零。
- 中位 UMI 分别约为 A 20,109、B 19,946、C 20,034；中位检测基因数约为 6,147、5,756、6,006。
- 138 个 guide-level pseudobulk 在 log-CPM PCA 上，PC1+PC2 解释约 98.8% 变异；背景质心距离约为各背景 guide 内 RMS 的 447-586 倍。
- 对当轮 300 个 target 的 NTC 基础表达做 `log1p(mean-cell CPM)` 比较，A-B、A-C、B-C 的 Pearson correlation 分别为 0.5863、0.4160、0.6046；逐 target 的三背景 CPM 最大/最小比中位数为 2.683。

这是**本项目实测**，不是 Arc 对模型性能的结论。它证明 A/B/C 的背景表达信号远大于同背景 NTC-guide 变异，并且待扰动 target 自身的基础表达明显 context-specific；它不证明背景的真实身份，也不证明“相似 NTC 必然具有相似扰动响应”。但它足以否决完全忽略 context 或只给 target 一个固定跨背景 effect 的模型。

## 2. 六项指标实际要求模型学会什么

截至核查日，官方仓库 HEAD 为 commit [`5e648335`](https://github.com/ArcInstitute/cell-eval2/commit/5e64833518a6603a0301cbe28185d49c30f4a986)，包版本是 `0.16.0`、competition `rule_version=3`。指标 brief 中的参考数值由 `0.15.0`、rule 3 bundles 测得；官方 changelog 明确说明 0.16.0 **不改变任何 scored number**，但 bundle 与 submission 的 `cell_eval2_version` 做精确、fail-closed 比较，所以 0.16.0 run 不能配 0.15.0-stamped bundle。复现记录必须同时固定 package version、commit、rule version、competition digest 和 bundle fingerprint，而不是只写“用了 vcc2026”。[vcc2026 preset](https://github.com/ArcInstitute/cell-eval2/blob/5e64833518a6603a0301cbe28185d49c30f4a986/src/cell_eval2/configs/vcc2026.yaml)；[0.16.0 changelog](https://github.com/ArcInstitute/cell-eval2/blob/5e64833518a6603a0301cbe28185d49c30f4a986/CHANGELOG.md#0160--2026-08-19)

评分器对每个 context 独立计算六项 raw metric，再用该 context 的两个实测锚点缩放：

```text
scaled = (submission_raw - context_mean_raw) /
         (experimental_replicate_raw - context_mean_raw)
```

其中 0 是“给每个扰动都输出该背景的平均扰动响应”，1 是两次真实重复实验之间的一致性。1 不是上限，也不是 100%；负分表示不如 context mean。六项 scaled score 无权重平均，再对三个 context 无权重平均。[官方 FAQ：评分](../Official-website/FAQs.md#评分)

注意：**排行榜的 0 不是 NTC。** context-mean anchor 是保留真值中多个真实扰动的平均响应；复制 NTC 是另一个更弱的 null-effect sanity baseline。

### 2.1 指标和建模含义

| 指标 | 官方计算要点 | 高分真正需要 | 单独不能证明 |
|---|---|---|---|
| `pds_cosine` | 每组细胞求和，归一到 50,000 后 `log1p`；预测 effect 与 300 个真实 effect 做 cosine distance 排名；统一移除整张 300-target panel | 不同靶点具有可区分的、方向正确的下游表达图案 | 幅度校准、DEG 集合或单细胞分布正确 |
| `expr_mse_unbiased_capped_norm` | 比较预测和真实 bulk-log profile 的平方误差，相对真实扰动离 NTC 的距离归一；用 jackknife 修正抽样噪声 | 全转录组均值和扰动强度校准 | 具体 DEG、方向排序或细胞异质性完整 |
| `de_*_direction_fidelity_yield_raw` | 预测显著基因方向正确率，同时用真实 DEG 数惩罚少报 | 方向 precision 与 coverage 同时高 | 效应幅度和未显著基因准确 |
| `de_*_direction_reach_raw` | 在真实 DEG 池中按预测置信度排序，找方向纯度仍不低于 90% 的最深前缀 | 把高置信、方向正确的响应基因排在前面 | 自己是否找到了完整显著集合 |
| `de_*_sig_jaccard` | 预测与真实显著集合的 Jaccard；漏报和误报都受罚 | DEG 集合边界和单细胞统计形状 | LFC 幅度正确 |
| `de_*_lfc_nmae` | 只在真实显著且有限 LFC 的基因上算归一化 MAE；至少 10 genes 才计入 | 真实响应基因的 LFC 幅度校准 | 非响应基因、目标身份区分或全部 perturbations |

四个 DE 指标先把每个细胞归一到 1,000,000 CPM，以实测 NTC 为共同对照，对每基因做双侧 Wilcoxon rank-sum，并在每个 perturbation 内做 Benjamini-Hochberg 校正；只检验 NTC mean > 5 CPM 的基因，`p_adj < 0.05` 为显著。除 PDS 移除整个目标 panel 外，其余五项都移除当前扰动自己的靶基因。[官方指标规范，第 1-7 节](https://github.com/ArcInstitute/cell-eval2/blob/5e64833518a6603a0301cbe28185d49c30f4a986/docs/vcc2026_metrics/vcc2026-metrics-brief.md)

因此，最明显的“捷径”无效：看到 target=`ADNP` 后只让 ADNP 自身下降不会得分；真正被评估的是 ADNP 被抑制后的下游全转录组响应。

### 2.2 指标驱动的最低诊断集

任何离线评估实现都应先通过以下破坏实验，再允许比较模型：

1. **零效应**：把同一批目标背景 NTC 复制给每个靶点；预期 raw PDS=0.5、raw LFC NMAE 约为 1。
2. **target label shuffle**：表达不变、打乱目标标签；PDS 必须显著下降，否则存在标签或真值泄漏。
3. **context swap**：交换两个背景标签；官方明确警告所有指标会接近随机，但系统不一定报格式错。[官方 FAQ，第 165-169 行](../Official-website/FAQs.md)
4. **effect scale sweep**：固定效应方向，扫描 `{0.25, 0.5, 0.75, 1, 1.5, 2}`；理想 cosine PDS 对纯线性尺度不敏感，但 raw-count 重建、`log1p`、裁剪和归一化可改变方向。PDS 论文对距离与尺度的结论不能无检查地迁移到 2026 的完整流水线。[Liu et al.](https://arxiv.org/abs/2511.16954v1)
5. **mean-cell collapse**：把同一群体均值复制 400 次；bulk 指标可能仍好，但 Wilcoxon、Jaccard 和 MSE jackknife 会看到失真的方差。
6. **gene-order permutation**：故意错开一小段列，测试合同检查必须在评分前失败。

## 3. 文献与上一届比赛能支持到哪一步

### 3.1 可以采纳的论文信号

| 来源 | 作者实际报告的结论 | 对 VC2026 的合理用途 | 不能外推的内容 |
|---|---|---|---|
| [STATE](https://doi.org/10.1101/2025.06.26.661135) | 集合级状态转移模型在超过 1 亿个扰动细胞上训练；作者报告其改善跨情境扰动效应和 DEG 识别，官方代码支持 zero-shot cell-type split | 官方可执行基线；借鉴 NTC set encoder、MMD 分布损失、完整背景留出 | 论文主要跨背景实验仍可使用目标背景约 30% 扰动，不等于 VC2026 纯零样本；主要建模 2,000 HVG log expression，也未证明直接输出本赛 18,533-gene raw counts |
| [Stack](https://doi.org/10.64898/2026.01.09.698608) | 作者以外部 perturbation cells 作 prompt、目标背景 control 作 query，并以负二项分布建模 counts；官方仓库提供代码和权重 | 输入结构与“公共扰动 + 匿名 NTC”高度相似；取得书面许可后可作 in-context baseline | 代码、权重和输出许可证都限制非商业用途，且把 monetary compensation 排除在外；在有奖金的 VC2026 中应视为许可阻塞，论文结果也不是本项目复现 |
| [X-Cell](https://doi.org/10.64898/2026.03.18.712807) | 作者在 25.6M CRISPRi cells、16 contexts 上训练扩散模型；X-Cell-Ultra 在未见背景上用无标签 NTC 测试时适配后优于其基线 | 借鉴大规模干预数据、多模态 target prior、anti-collapse loss、NTC-only TTA | 4.9B 模型和作者数据的结果不是本项目已复现能力；论文称将开放 55M 权重/数据，但核查时 GitHub 仍为 coming soon，HF 未见可用数据内容 |
| [Perturbation response decomposition](https://doi.org/10.64898/2026.07.24.740459) | 作者把响应拆为 global、perturbation、cell-line、interaction；报告 global component 可从 control expression 推断，而 target/cell-line-specific component 高维且不能只从 control 恢复；先验对齐后的线性/MLP 模型胜过其比较架构 | 直接支持层次化 delta、context encoder + target biological prior，以及“简单模型先行” | 仅四个 CRISPRi screens 的预印本作者结论；已纳入索引且代码公开，但代码仓库未声明 license，本项目尚未复现 |
| [PerturbNet](https://doi.org/10.1038/s44320-025-00131-3) | 作者用 gene functional annotations 预测未见 CRISPRa/i target 后的单细胞分布 | 作为未见 target 生成模型候选；验证功能注释/蛋白表示是否有增益 | 论文任务、数据处理和指标不是 VC2026；不能用摘要声称比赛增益 |
| [Ahlmann-Eltze et al.](https://doi.org/10.1038/s41592-025-02772-6) | 在其单/双扰动 benchmark 中，五个 foundation models 和两个深度模型没有胜过刻意简单的基线 | 要求所有神经模型跨背景稳定击败 linear/statistical baseline | 不表示所有深度模型、所有数据和 VC2026 都必然失败 |

STATE 的官方仓库当前明确支持 `[zeroshot]` 整 cell type 留出与 `[fewshot]` target 留出，并提供 `infer`；这使它适合做可复核基线，而不是只引用论文数字。[STATE README, commit `9bbfe78a`](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/README.md#state-transition-model-st)

Stack 的官方仓库是另一条技术候选：[ArcInstitute/stack](https://github.com/ArcInstitute/stack)。但当前代码采用 CC BY-NC-SA 4.0，模型许可又把“直接或间接 monetary compensation”明确排除在 Non-Commercial Purpose 之外；在总奖金 175,000 美元的 VC2026 中，应先取得 Arc 的书面许可，未取得前不得让 Stack 进入提交或集成。它仍可作为论文思想参考，但“仓库可下载”不等于“有权用于竞赛”。[Stack model license](https://github.com/ArcInstitute/stack/blob/main/MODEL_LICENSE.md)

许可证是实质风险：FAQ 对 STATE 给出了比赛专项解释，在遵守适用许可证的前提下允许使用其代码，并区分非商业参赛者与商业许可流程；这一解释不能自动扩展到 Stack。团队身份、训练数据、模型权重与输出许可必须在训练前完成清单，而不是入围后补救。[官方 FAQ：State](../Official-website/FAQs.md#法律事项)；[State model license](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/MODEL_LICENSE.md)

### 3.2 2025 获奖经验怎样迁移

Arc 官方总结中的前三名不是同一种大模型：第一名把改进的 scFoundation、蛋白 embedding、公开扰动数据、DEG frequency 和 mean-expression feature 混合，并直接对齐比赛损失；第二名使用全连接网络、aggregated control、ESM-2、UMI indicator 和 residual delta；第三名 TransPert 只用 pseudobulk/Wilcoxon summary，以 cell-line similarity 聚合不同背景的效应。Generalist Prize 则由 flow matching 单细胞生成模型获得。[Arc 2025 wrap-up](https://arcinstitute.org/news/virtual-cell-challenge-2025-wrap-up)

可迁移的是四条原则：

- 公开、多背景扰动数据是主要监督来源；
- 预测 `perturbed - control` 比直接预测绝对表达更容易迁移和校准；
- classical statistics 与 target prior 是深度模型的互补输入；
- 模型必须针对真实评分的互补维度训练和诊断。

不可直接迁移的是 2025 的伪批量复制和 L1-PDS 缩放策略。2026 的四个 DE 指标读取 400 个细胞的秩与显著性，表达 MSE 带抽样修正，PDS 改为 cosine 并移除整个 target panel；只复制均值或单纯放大效应的收益不再成立。

## 4. 推荐数据层：先统一“可比较的实验单位”

### 4.1 第一优先级数据

官方明确允许使用有权使用的公开或专有数据，并推荐以下资源：[官方数据说明：图谱与公共数据](../Official-website/About-the-Data.md#arc虚拟细胞图谱)

1. **VC2025 H1 hESC**：同为 CRISPRi + 10x Flex，化学平台最接近；适合学习 Flex count distribution、H1 target effects 和 count decoder，但只有一个背景，不能独自验证 context generalization。
2. **Replogle et al. K562/RPE1**：全基因组 CRISPRi，target coverage 大；适合 target effect 和双背景迁移。[原始论文](https://doi.org/10.1016/j.cell.2022.05.013)
3. **Nadig et al. HepG2/Jurkat**：常见必需基因的多背景 CRISPR screen，补充肝癌与 T-cell context。[原始论文](https://doi.org/10.1038/s41588-025-02169-3)
4. **Jiang et al. 六癌细胞系**：增加组织来源和 context 数；适合 leave-one-cell-line-out。[原始论文](https://doi.org/10.1038/s41556-025-01622-z)
5. **X-Atlas/Pisces 或其他可合法获得的多背景 CRISPRi**：只有在数据、metadata、许可和计算预算核验后再加入；不能因为论文规模大就默认可用。
6. **scBaseCount / CELLxGENE 观察数据**：可训练 context encoder 或寻找相似 NTC，但没有 intervention label，不能替代 Perturb-seq supervision。[Arc Virtual Cell Atlas](https://github.com/ArcInstitute/arc-virtual-cell-atlas)

### 4.2 统一时必须保留的层次

不要先把所有细胞拼成一张大表。每个 cell 至少保留：`study`、`assay/chemistry`、`batch`、`cell_line/context`、`guide/target`、`control type`、`cell_id`、`gene identifier version`、`raw-count availability` 和许可/来源。

推荐把监督样本定义为 `(study, context, target, replicate/batch)` 的 cell set，同时保存：

- raw count cells；
- NTC-matched pseudobulk 和 library-size distribution；
- target vs matched NTC 的 log-CPM delta；
- Wilcoxon/BH DE table；
- target knockdown QC；
- 目标基因的 protein/function/coessentiality embedding。

**工程假设：**首版只在不同数据集的可靠基因交集上学习 effect，再以目标背景 NTC 补全其余基因；但最终解码和评分必须回到官方 18,533-gene axis。把“训练时未测得”误写成生物学 0 会制造系统偏差。

### 4.3 去重和泄漏审计

- 按 DOI、GEO/SRA accession、原始 cell barcode/guide、数据版本与 checksum 去重；同一实验的作者 H5AD、图谱副本和二次处理版不能分居 train/test。
- 同一 cell line 在不同研究可用于评估 study shift，但外层 test 若要模拟真正新背景，应把该 cell line 的所有研究一起留出。
- 相同 target 跨 context 是允许的训练信号；target-generalization fold 则要把该 target 从所有训练 context 移除。
- 不使用 A/B/C 排行榜反推的伪标签训练；不依据文件中非官方隐藏字段猜真值；只使用官方公开字段和有权访问的外部数据。
- 最终预测必须由模型生成；公开实验/论文真值可以在规则和许可证允许的范围内用于训练或微调，但不能把已知实验结果直接复制或手工改写成最终预测。[官方 Rules](https://virtualcellchallenge.org/rules#submitting-final-entries)

## 5. 验证设计：竞争力的核心不是一个 split，而是一组压力测试

### 5.1 必须同时回答的三个问题

| 问题 | 推荐 split | 模拟的最终风险 |
|---|---|---|
| 已见 target 能否迁移到新背景？ | leave-one-study-and-context-out，target 可在其他背景出现 | D/E/F 是新细胞背景 |
| 新 target 能否在已知背景预测？ | leave-target-out，target 从全部训练背景移除 | 最终面板与验证面板不同 |
| 新 target + 新背景能否组合泛化？ | 双重留出：完整背景和一组 target 同时留出 | 最接近最坏情况的 VC2026 |

每个 outer test context 只给模型该 context 的 NTC 和 target symbols。超参数、effect scale、TTA step 数、ensemble weight、zero threshold 都在 inner contexts 选择；outer truth 只能被评分器读取一次。

### 5.2 面板和评分也要仿真

- 每个离线 fold 固定约 300-target panel 后计算 PDS；不能每个模型用不同 target 子集，因为 PDS 是面板内相对排名。
- 用 held-out truth 构建本地 context-mean 和 split-replicate anchors，得到仿官方 scaled score；anchors 只属于 evaluator，不进入训练。
- 同时报告六项 raw/scaled、三背景均值、每背景最差值、每 target 分布和 3-5 个模型随机种子。
- 模型选择用跨 outer-context 的 median rank、mean score 和 worst-context guardrail；一次平均提升若来自单一 context 或单一 metric，不足以上线。
- A/B/C leaderboard 只用于低频外部校准。团队每天最多两次提交并不意味着应该每天用满；大量自适应试探会把公开榜变成训练集。[官方 FAQ：提交次数](../Official-website/FAQs.md#参赛)

### 5.3 失败应能定位到哪一层

| 症状 | 优先怀疑 |
|---|---|
| PDS 高，MSE/NMAE 差 | target pattern 对，但 effect scale 或 count calibration 错 |
| Jaccard 高，fidelity/reach 低 | 找到相近 gene set，但方向或排序置信度错 |
| bulk 两项好，DE 四项差 | 400-cell 分布、零率、方差或 Wilcoxon 统计形状失真 |
| 所有 context 一起差 | gene axis、normalization、raw-count decoder 或 target label 错 |
| 只有一个 context 崩溃 | context encoder、硬身份匹配或 domain shift 失败 |
| label shuffle 仍高 | 真值/target leakage 或 evaluator bug |

## 6. 从能提交到强方案的实验顺序

每一级只有在严格 outer folds 上稳定超过前一级，才增加复杂度。

| 阶段 | 实现 | 主要目的 | 进入下一阶段的门槛 |
|---|---|---|---|
| E0 合同与评分器 | 固定 `cell-eval2` package/commit/rule/digest/bundle；实现 perfect/null/shuffle/scale/context-swap tests；跑 `vcc prep --dry-run` | 排除指标、版本配对和格式错误 | 所有预期性质可复现；同 seed 字节级或统计级可复现 |
| E1 NTC null | 每 context 固定抽取/重采样 400 个 NTC，复制给全部 target | 最弱但语义清楚的 zero-effect baseline | 合法 360k submission；raw PDS=0.5 sanity 成立 |
| E2 统计 delta | 对每 target 聚合训练 contexts 的 pseudobulk delta；global mean、context-similarity weighted mean、ridge/MLP target prior、empirical-Bayes shrinkage | 证明公开数据中的可迁移信号 | 双重留出六项平均稳定优于 E1；无 context 崩溃 |
| E3 单细胞 count decoder | 用 held-out context NTC 的 cell state、library size、dispersion/zero probability把 E2 delta 变成 400 raw-count cells | 把效应预测与分布生成分开调试 | bulk 不退化，DE 四项显著改善，方差/零率通过 QC |
| E4 可运行公开模型 | STATE 按官方 `[zeroshot]`/`[fewshot]` 训练并补齐 full-gene raw-count adapter；Stack 仅在取得书面比赛许可后，以公共 perturbation 作 prompt、held-out NTC 作 query | 建立公开强模型参考 | 在同一数据/split/预算下胜过 E2/E3，且许可证和推理成本可接受 |
| E5 context-target interaction | NTC set encoder + target prior + FiLM/cross-attention/residual MLP；多任务 loss | 学习 context-specific downstream effect | 多数 outer contexts/metrics 提升；target embedding shuffle 明显变差 |
| E6 NTC-only TTA | 冻结 target pathway，仅以目标 NTC 做 self-supervised/MMD alignment；步数与 LR 由 inner folds固定 | 适应 D/E/F assay/state manifold | 不看 target truth 仍稳定提升；无 collapse/forgetting |
| E7 ensemble/calibration | 统计模型、神经模型和多个 seed 在 effect/rate 层做约束集成；重新采样整数 counts | 降低 context-specific tail risk | worst-context 改善且六项无重大退化；候选不超过 2-3 个 |

E4 不是必经终点。STATE 官方预处理默认 `normalize + log1p + HVG`，而本赛要求 18,533-gene raw counts；必须验证完整基因输出、反变换、整数采样和稀疏度，不能把“官方推荐模型”误解为“直接生成合规提交”。[STATE README](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/README.md#preprocess_train)

## 7. 推荐的主模型：层次化 effect predictor + NTC-conditioned count generator

以下是**工程假设**，是根据官方指标、2025 方案和论文共同约束出的优先实现，不是论文已证明的唯一架构。

### 7.1 表达分解

对 context `c`、target `p`、gene `g`，先预测群体效应而非绝对计数：

```text
delta[c,p,g]
  = global_target_effect[p,g]
  + context_modulation[encode(NTC_c), p, g]
  + residual_interaction[c,p,g]
```

- `global_target_effect` 从所有训练 context 的同 target 扰动和 target biological prior 学习；
- `encode(NTC_c)` 用 DeepSets/set transformer 或稳定的 pseudobulk+PCA 表示匿名背景，输入只来自当轮 NTC；
- `context_modulation` 学习“同一通路在不同基础状态下怎样被放大、压低或改向”；
- `residual_interaction` 强 shrinkage 到 0，只有跨 fold 有稳定证据时才释放容量。

这种分解与 Molina/Zhang 的 response-component 结果和 2025 residual/statistical winner 都相容，但是否优于其他形式必须由双重留出决定。[response decomposition](https://doi.org/10.64898/2026.07.24.740459)；[Arc 2025 wrap-up](https://arcinstitute.org/news/virtual-cell-challenge-2025-wrap-up)

### 7.2 Target prior

按投入回报顺序测试：

1. training contexts 中该 target 的效应统计；
2. ESM-2/protein embedding；
3. gene ontology/pathway/STRING 或 coessentiality embedding；
4. target 在 NTC 中的表达、essentiality 和同模块 gene state；
5. 多模态 cross-attention。

每加入一种 prior 都做 embedding shuffle 和 matched-parameter control。X-Cell 与 PerturbNet 的作者结果支持 prior 的可能价值，但它也可能只编码 cell-line identity、target frequency 或数据集来源；没有消融就不能称为生物知识增益。[X-Cell](https://doi.org/10.64898/2026.03.18.712807)；[PerturbNet](https://doi.org/10.1038/s44320-025-00131-3)

### 7.3 Loss 设计

推荐在训练表征层同时约束：

- full-profile Huber/MSE：服务 expression MSE；
- log-fold-change MAE/CCC：服务 NMAE 和 anti-collapse；
- target-vs-other contrastive cosine：服务 PDS；
- DEG probability + sign loss + ranking loss：服务 Jaccard、fidelity、reach；
- set-level MMD/energy distance：服务群体分布而非单个均值；
- effect norm calibration：防止保守塌缩和过冲。

官方六项 scaled score 才是模型选择目标；这些可微 loss 只是 proxy。不得直接把保留 outer truth 的 DEG gate 或 official anchors喂进训练。

### 7.4 从 effect 到 400 个 raw-count cells

首版可用一个可解释生成器：

1. 从目标 context NTC 按 `ntc_id` 分层抽样 cell state 与 library size；
2. 在平滑的 NTC gene-rate 上施加 `delta[c,p]`，而不是对单个稀疏 cell 的 0 逐元素相乘；
3. 用 negative-binomial / Dirichlet-multinomial 或经验证的 count decoder 生成整数 counts；
4. 保持 target context 的 library-size、detected-gene、zero-rate 和高表达尾部；
5. 对每 target 独立生成恰好 400 cells，删除显式零，写 CSR。

关键边界：相同 pseudobulk 可以由很多错误的单细胞分布产生。必须在公共 held-out truth 上比较 per-gene mean/variance、zero fraction、library size、DEG 数量和六项指标，不能只看可视化像不像。

### 7.5 集成应发生在哪一层

不要默认把两个整数 count 矩阵逐元素平均再四舍五入；这会改变零率、方差和 gene-gene covariance。优先在以下位置集成：

- effect/log-rate 层平均或 stacking；
- 统计模型作为 shrinkage prior，神经模型只预测 residual；
- 以 model/seed mixture 分配 400 个生成细胞，但重新校准整体 pseudobulk；
- 仅在 inner folds 选择权重，并设每项 scaled metric 的最大允许退化。

## 8. 最容易让验证虚高的十类风险

| 风险 | 为什么虚高 | 防护 |
|---|---|---|
| 随机 cell split | 同一 target/context/batch 的近重复泄漏 | 按 study-context-target group 划分 |
| 同一 cell line 的不同数据版本跨 train/test | 实际是原实验副本 | accession、barcode、guide、checksum 去重 |
| 只做 target holdout | 没模拟 D/E/F 新背景 | outer leave-context-out |
| 只做 context holdout | 没测试最终新 panel | 再做 target 和双重留出 |
| 在 outer truth 上选 scale/TTA/ensemble | 直接用测试答案调参 | nested CV；outer 只评分一次 |
| 改变 PDS panel | 排名参照集合改变 | 同 fold 固定 300-target panel |
| target gene knockdown 当主要特征 | 评分排除了 target gene | 检查 non-target downstream effect |
| 硬猜匿名 cell-line identity | 错一次可让整个 context 崩溃 | soft reference mixture + NTC encoder + fallback |
| 以 leaderboard 反复调参 | A/B/C 逐渐成为训练集 | 预注册 submission hypothesis 和预算 |
| public proprietary/license 混用 | 入围后不可复现或无权披露 | 数据/model/license manifest，训练前审查 |

另一个常见误区是把 observation atlas 当成 intervention supervision。NTC 或 scBaseCount 能说明“细胞现在是什么状态”，不能单独识别“敲低某基因后哪些高维下游程序会变化”；target priors 与多背景 Perturb-seq 仍然必要。[response decomposition abstract](https://doi.org/10.64898/2026.07.24.740459)

## 9. 最终轮运行手册

### 9.1 2026-10-22 前必须冻结

- 数据版本、许可表、gene mapping、外层 folds 与全部实验记录；
- 最多 2-3 个候选模型、ensemble rule 和失败 fallback；
- NTC-only TTA 的 LR、step 数、停止规则与 seed；
- count decoder、library-size sampler、低表达置零阈值；
- 容器/lockfile、GPU/CPU/RAM 预算、chunked generation 脚本；
- `vcc prep --dry-run`、稀疏项、context/target/gene-order、整数/finite/cell-total tests；
- 完整 360,000 × 18,533 压力测试和预计运行时间。

### 9.2 收到 D/E/F 后只做预定义动作

1. 保存官方 zip、manifest、gene list、target list 的 checksum；禁止沿用 A/B/C 的 `pert_counts.csv`。
2. 对 D/E/F 分别做合同、UMI、detected genes、zero rate、`ntc_id` 和 context separation 审计。
3. 运行预定义 soft reference matching/context encoder；identity 猜测只作诊断，不成为硬分支。
4. 对每个 frozen candidate 执行相同 NTC-only TTA；保存 pre/post checkpoint 和无标签 loss curve。
5. 分块生成 counts；过程中禁止 densify，持续统计 stored entries、显式零、cell total 和 target counts。
6. 对候选做无真值 QC：NTC-relative effect norm、模型间一致性、library size、zero fraction、DEG 数、context swap sensitivity、异常 target 列表。
7. 按冻结的选择规则决定唯一 award candidate；另保留一个合法 fallback。

最终轮没有用于模型选择的排行榜，最终阶段最后一次提交进入评奖；不要把验证阶段“每天两次、看分再改”的操作习惯带入 D/E/F。另需特别检查当时安装的 `vcc` CLI：核查时本机 `vcc 0.1.0` 的默认 context 仍是 A/B/C，最终轮必须升级到官方支持版本或显式确认 D/E/F 配置，不能让旧默认值静默改写标签。

### 9.3 上传前双人/双程序检查

- 一个 H5AD，恰好 360,000 rows × 18,533 genes；
- 每个 `(context,target)` 恰好 400 rows，只有 D/E/F 和当轮 300 targets；
- 不含 `non-targeting` rows；cell index 唯一；
- `var_names` 与当轮 `gene_names.csv` 逐元素相等；
- `X` 为 sparse，值 finite/nonnegative/integer，无 explicit zero；
- 每 cell sum ≤ 1,000,000，总 stored entries ≤ 4.75B；
- `vcc prep ... --dry-run` 成功，再正式生成 `.vcc`；
- 记录输入、模型、H5AD、`.vcc` checksum、命令、环境、seed、运行时与操作者；
- 在另一环境至少解包/读取一次，确保不是单机偶然可读。

团队每天最多提交两次，但只有一个最终提交参加奖项评选；入围者还需提交可公开的方法说明，Arc 保留要求进一步验证可疑提交的权利。可复现记录和许可不是赛后文书，而是提交系统的一部分。[官方 FAQ：参赛与代码说明](../Official-website/FAQs.md#参赛)

## 10. 推荐的项目里程碑

以 2026-08-30 为起点，距离 D/E/F 发布约 53 天，最终运行窗口约 14 天：

| 截止 | 必须完成的可验收结果 |
|---|---|
| 9 月第 1 周 | E0/E1；固定 evaluator 与 submission contract；A/B/C controls 审计自动化 |
| 9 月第 2 周 | 至少 4 个公共 CRISPRi contexts 的统一数据层；study/context/target leakage audit |
| 9 月第 3 周 | E2 统计 delta 与 nested double-holdout；六项 metric dashboard |
| 9 月第 4 周 | E3 raw-count generator；完整 400-cell distribution diagnostics |
| 10 月第 1 周 | E4 STATE 可复现对照；Stack 只在书面许可通过后运行；决定是否继续投入大模型 |
| 10 月第 2 周 | E5/E6 interaction + NTC-only TTA；完整消融和 worst-context 分析 |
| 10 月 15 日前 | 冻结 2-3 个候选、ensemble rule、container 和 full-scale rehearsal |
| 10 月 22 日后 | 只做 D/E/F NTC 适配、生成、QC、打包和预定义选择 |
| 11 月 5 日前 | 提交唯一正式 candidate，并归档方法、许可、checksum 和复现说明 |

若进度落后，删减顺序应是：4.9B-scale 模型/新扩散架构 -> 多模态花哨 prior -> 复杂 count decoder；不能删的是数据去重、双重留出、统计 baseline、六项指标、raw-count 合同和最终压力测试。

## 11. 事实、结论和假设登记

### 已验证官方事实

- 六个匿名不同组织来源细胞系；A/B/C 验证，D/E/F 最终；无挑战专用训练集。
- 每轮 300 targets × 3 contexts × 400 cells，18,533 genes，raw nonnegative integer counts。
- 最终名次只由 D/E/F 决定；验证与最终分数不可直接比较。
- 六项 metrics 做 context-specific reference scaling 后等权平均；评分排除 target gene。
- 可使用有权使用的公共/专有数据；每天最多两次提交；最终只选一份参评。

### 论文/作者结论，尚未由本项目复现

- STATE 的 set-level transition/MMD 与 embedding 能改善作者 benchmark 的跨 context 预测。
- X-Cell 的 causal-data scaling、多模态 prior 和 NTC-only TTA 改善作者的 unseen-context benchmark。
- response decomposition 的 global component 可从 control 推断，而高维 target/context component 需要额外先验。
- PerturbNet 的 functional annotation 能帮助作者数据中的 unseen perturbation distribution prediction。
- 某些现有 deep/foundation models 在特定公开 benchmark 未胜过简单线性基线。

### 工程假设，必须通过本项目实验否证

- NTC set encoder + target prior + shrinkage interaction 会优于 context-similarity statistical delta。
- 用 NTC-conditioned count decoder 会同时改善四项 DE 指标且不伤 bulk 两项。
- A/B/C 的清晰 NTC separation 能转化为有用的 context modulation，而不只是批次识别。
- NTC-only TTA 在 D/E/F 会改善 domain alignment 且不产生 conservative collapse。
- 统计 + neural effect-layer ensemble 会降低 worst-context 风险。

## 12. 检索台账与未解决缺口

本研究先读取 [`docs/references/INDEX.md`](../references/INDEX.md)，再把缺口拆成两个检索问题，共执行三次顺序 Scholar API 调用：

1. 方法与可用性首查：`zero-shot single-cell CRISPRi Perturb-seq response prediction unseen cell context`
2. 因首查未返回本地核心候选 X-Cell，精炼一次：`"Scaling Causal Perturbation Prediction across Diverse Cellular Contexts" X-Cell`
3. 简单基线是否稳定的独立问题：`CRISPRi Perturb-seq zero-shot perturbation prediction unseen cell context benchmark pseudobulk baseline`

三次查询各返回 10 项且 Scholar HTTP 调用均成功。第一项新增高相关候选为 Molina & Zhang 的 response decomposition 和 PerturbNet；其余包括 scLAMBDA、时间动力学、GRN 与药物任务，因不能直接回答匿名 CRISPRi context transfer 而未进入主路线。第二项仍未直接返回 X-Cell 记录；结果中的引文/snippet 暴露了新版 bioRxiv 标识，随后通过 DOI/Crossref 与 bioRxiv 原文入口核验为 `10.64898/2026.03.18.712807`。第三项命中 response decomposition、表格模型、同行评议 benchmark 和响应幅度研究，无需精炼。选中结论均回到 DOI/Crossref 元数据、开放全文、官方 GitHub/Hugging Face、许可证或 Arc 官方页面核对；搜索摘要本身不作为证据。BMC PDF 重定向发生一次 TLS 失败，随后由 DOI 精确定位到 PubMed Central 开放全文完成核验。

未解决缺口：

- X-Cell 当前没有公开可用代码、权重或数据；Hugging Face 页只有 README、图片和属性文件。Response decomposition 有公开代码仓库，但没有声明 license；两者都不能直接当作已获许可的可运行提交方案。
- Lingshu-Cell、AlphaCell 等本地材料的规范原文标识在当前 `INDEX.md` 仍待核验，因此没有作为主方案的决定性证据。
- 本轮实际用于判断的 response decomposition、PerturbNet、Ahlmann-Eltze、Csendes、Palla、Shoeibi、Stack 和 X-Cell 均已同步到 [`INDEX.md`](../references/INDEX.md)，并标明采用、备选、可用性和许可边界。
- 官方规则、`vcc` CLI 或 `cell-eval2 rule_version` 可能在赛期更新；提交前要重新核对，而不能只依赖本次 2026-08-30 快照。
- D/E/F 身份、真值和 reference anchors 是有意保留的信息；“未知”不是检索缺口，不应试图绕过。

## 13. 关键一手来源

- Arc Institute：[2026 About the Data 本地核验页](../Official-website/About-the-Data.md)；[2026 FAQ 本地核验页](../Official-website/FAQs.md)；[官网 Data](https://virtualcellchallenge.org/datasets)；[官网 Evaluation](https://virtualcellchallenge.org/evaluation)；[Rules](https://virtualcellchallenge.org/rules)。
- Arc Institute：[`cell-eval2` vcc2026 metric brief](https://github.com/ArcInstitute/cell-eval2/blob/5e64833518a6603a0301cbe28185d49c30f4a986/docs/vcc2026_metrics/vcc2026-metrics-brief.md)；[`vcc2026.yaml`](https://github.com/ArcInstitute/cell-eval2/blob/5e64833518a6603a0301cbe28185d49c30f4a986/src/cell_eval2/configs/vcc2026.yaml)。
- Arc Institute：[VC2025 Winners and Reflections](https://arcinstitute.org/news/virtual-cell-challenge-2025-wrap-up)；[Arc Virtual Cell Atlas](https://github.com/ArcInstitute/arc-virtual-cell-atlas)。
- Adduri et al.：[STATE](https://doi.org/10.1101/2025.06.26.661135)；[official code](https://github.com/ArcInstitute/state)。
- Dong et al.：[Stack](https://doi.org/10.64898/2026.01.09.698608)；[official code](https://github.com/ArcInstitute/stack)。
- Wang et al.：[X-Cell](https://doi.org/10.64898/2026.03.18.712807)。
- Molina & Zhang：[Perturbation response decomposition](https://doi.org/10.64898/2026.07.24.740459)；[code](https://github.com/xinyizhanglab/perturbation-decomposition)（仓库未声明 license）。
- Yu et al.：[PerturbNet](https://doi.org/10.1038/s44320-025-00131-3)。
- Ahlmann-Eltze, Huber & Anders：[Deep-learning-based gene perturbation effect prediction does not yet outperform simple linear baselines](https://doi.org/10.1038/s41592-025-02772-6)。
- Liu et al.：[Effects of Distance Metrics and Scaling on the Perturbation Discrimination Score](https://arxiv.org/abs/2511.16954v1)。
