# 外部博客阅读副本

本目录保存与 VC2026 直接相关、可复核的**外部参赛者博客**的本地 Markdown 阅读副本。

这里的文件是**机器转换的阅读副本，不是原文**。逐字引用、公式、数值和结论核验必须回到原文链接。原文中的图片以绝对 URL 保留引用，未下载到本仓库。

博客属于**参赛者自报经验**，不是官方事实。作者报告的名次、身份推断、分数和参数都必须在本地复现后才能用于本项目的决策；引用时应标注为「参赛者自报」。

> 与 `docs/references/INDEX.md` 的分工：`docs/references/` 保存论文与官方材料的阅读版；本目录保存参赛者博客。两者的条目都会登记到 `docs/references/INDEX.md` 的「工程材料与社区证据」一节，避免重复检索。

## 目录

| 本地文件 | 作者 | 发布 | 原文 |
|---|---|---|---|
| [ilyes-baali-2026-09-01-the-virtual-cell-challenge.md](ilyes-baali-2026-09-01-the-virtual-cell-challenge.md) | Ilyes Baali | 2026-09-01 | <https://ilyesbaali.me/blog/virtual-cell-challenge/> |
| [forrest-sheldon-2026-08-29-preliminaries.md](forrest-sheldon-2026-08-29-preliminaries.md) | Forrest Sheldon | 2026-08-29 | <https://forrestsheldon.github.io/virtual-cell/posts/2026-08-29-my-approach-to-the-virtual-cell/> |
| [forrest-sheldon-2026-08-29-exploring-the-data-i-cell-lines.md](forrest-sheldon-2026-08-29-exploring-the-data-i-cell-lines.md) | Forrest Sheldon | 2026-08-29 | <https://forrestsheldon.github.io/virtual-cell/posts/2026-08-29-exploring-the-data-i/> |
| [forrest-sheldon-2026-09-05-exploring-the-data-ii-crispri.md](forrest-sheldon-2026-09-05-exploring-the-data-ii-crispri.md) | Forrest Sheldon | 2026-09-05 | <https://forrestsheldon.github.io/virtual-cell/posts/2026-09-05-exploring-the-data-ii/> |
| [forrest-sheldon-2026-09-14-exploring-the-data-iii-sequencing-and-external-datasets.md](forrest-sheldon-2026-09-14-exploring-the-data-iii-sequencing-and-external-datasets.md) | Forrest Sheldon | 2026-09-14 | <https://forrestsheldon.github.io/virtual-cell/posts/2026-09-14-exploring-the-data-iii/> |

抓取日期：2026-09-17。

## 各篇与本项目的关系

### Ilyes Baali — The Virtual Cell Challenge（2026-09-01）

对 VC2026 难度来源最完整的一篇公开分析。与 00–06 课直接相关的内容：

- **「细胞背景」到底是什么**：同一份基因组、不同的开启子集。可作为L0-00生物学直觉的补充读物。
- **零不等于关闭**：测序只采样分子；约 69% 的矩阵条目为零，其中一部分是 dropout。对应L0-01 §4.3。
- **A/B/C 身份推断方法**：用单细胞伪批量与 DepMap 24Q4 的 bulk 参考谱做中心化余弦相关，作者报告 A → Jurkat（0.87）、B → HeLa（0.70）、C → CAL-33（0.76）。**这是参赛者推断，官方从未确认，不能当作已核实事实**；但如果成立，它会改变训练数据的选择策略（见下一条）。
- **效应迁移的难度上限**：同一细胞类型不同状态的效应一致性 0.25–0.33，**不同细胞类型塌到 0.016–0.037**。作者认为这是整个任务最重要的一个数字。
- **两步流水线**：先构造跨 screen 加权效应表，再乘到目标背景对照细胞上重采样。作者明确说明这**不是细胞模型**，只是绕开了建模目标状态的需要——这正是它性能封顶的原因。可作为「备选自建路线」的对照材料。
- **零方差惩罚**：预测 400 个完全相同的细胞（即使均值正确）得分约 **−0.81**。这是第 04 课「群体分布线」和三个 DE 指标需要细胞间变异的最直接证据。
- **评分公式与官方 `cell-eval` 的对照**：作者列出的六项公式是简化复述，不能替代官方代码；引用时必须回核 `ArcInstitute/cell-eval`。
- **噪声地板**：作者引用 Ward 2026 的双 guide 一致性数据，指出一部分「误差」不可约。建议在追精度之前先测量噪声地板。

### Forrest Sheldon — 四篇系列（2026-08-29 起）

- **Preliminaries**：明确的研究顺序是「数据探索 → 基线 → 超越线性 → 现代模型」。只有两人、资源有限，因此优先找**便宜的新想法**。这段对L0-00的学习动机和方法论有参考价值。
- **Exploring the Data I**：今年的实验栈（细胞系培养 → CRISPRi → 10x Flex scRNA-seq）；细胞系分类（干细胞系 H1/iPSC、工程化永生化 RPE1/HEK293、癌源 HeLa）；独立给出 A/B/C 猜测（Jurkat E6.1 / HeLa / CAL-33），与 Ilyes 的结论一致。**报告了一个采样对照细胞的负基线总分 −0.304，其中 DE 方向保真度为 −1.721**。
- **Exploring the Data II**：Cas9、guide RNA、CRISPRi 与 knockout 的区别、Perturb-seq 的实验流程。是第 0/1 课生物学机制部分最好的补充读物，讲得比大多数教材细。
- **Exploring the Data III**：把测序当作采样过程、批次效应的真实含义、以及哪些公共扰动数据集之间**可以比较**。这一篇最直接服务于L3-02「跨背景验证」和L3-04「多来源数据统一」——因为多来源统一流水线正是本项目的核心工程难点。
- 该作者同时维护 [`references/vcc2026-h1-benchmark`](../../references/vcc2026-h1-benchmark)（本项目已采用为 H1 开发基准，见 `docs/research/h1-benchmark-audit.md`）与 [`references/virtual-cell-challenge-2026`](../../references/virtual-cell-challenge-2026)。

## 转换与溯源

- 抓取工具：`curl`；HTML → Markdown 转换：Python `BeautifulSoup` + `markdownify`，正文容器取各站 `<main>`。
- 转换只做结构转换，未改写内容；标题层级、表格与公式的渲染可能与原文存在差异。
- 原站图片保留为绝对 URL，未下载；若原站改动或下线，图片将不可见。
- 版权归原作者所有。本目录仅作本地阅读与检索用途，不随仓库对外分发原文。
