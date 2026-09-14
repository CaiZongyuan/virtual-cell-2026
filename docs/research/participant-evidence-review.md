# 参赛博客与社区讨论：对首投方案的修订依据

> 核验日期：2026-09-14。用户提供的来源为 Ilyes Baali 博客、本地 H1 benchmark 和社区讨论摘录。
> 本文区分参赛者自报结果、代码可核实行为、官方评分定义和本项目工程决定；未复现博客模型或社区提交。

**当前主线已由用户明确为 STATE 基线及其改进模型。** 本文的轻量效应迁移只作诊断/组件经验；H1 开发验证 → 多背景留出 → 完整 A/B/C 打包的证据仍适用。全基因保留、评分版本固定和打包内存实测是首投验收项目。[主方案](first-submission-plan.md)是执行入口；[H1 审计](h1-benchmark-audit.md)记录工具合同。

## 1. 三份材料各能支持什么

| 材料 | 可以直接采用 | 不能据此断言 |
|---|---|---|
| [Ilyes Baali 博客](https://ilyesbaali.me/blog/virtual-cell-challenge/)，页面标注 2026-09-01 | 作者自述的效应表迁移路线、统一 raw-count 处理、对照模板与生成分布的重要性 | 当前排名、最佳方法可复现、A/B/C 真实身份、各项简化公式等于官方代码 |
| [H1 benchmark v0.2.0](https://github.com/forrestsheldon/vcc2026-h1-benchmark/tree/d28dd0496cc9fbf1d0088ce171208c0deb54a268) | 固定 H1 参考、六指标开发工具、CPU 分块计算、来源指纹 | 官方保留真值、现行线上评分镜像、单一 H1 分数证明广泛跨背景泛化 |
| 用户提供的 `references/discuss.md`，2026-09-02—03 对话 | 保留全基因计数的重要性、raw/scaled 分数混用风险、打包资源需要单独验证 | 官方规则解释、未经复现的具体得分、已被作者撤回的 OOM 因果解释 |

社区文件没有原始帖子 URL、可独立核实的提交 ID 和运行环境，本次只能把它作为用户提供的经验材料。本地 `references/` 已由项目忽略；本报告保留关键上下文，H1 代码另有上游仓库与 commit，避免把本地副本当作已入库资产。

## 2. 博客对模型选择的实际增量

作者从六个 source screen 的原始计数重新估计 log2 fold change，再把效应作用到目标背景对照细胞上。来源包括 K562、HCT116、HEK293T，以及三个 CD4 T-cell 状态。作者报告 269/300 靶点在六个 screen 中均有覆盖、跨细胞类型效应余弦相似度约 0.016–0.037，并自述排名由 167 改进到 45；**这些是作者针对其数据和当时榜单的自报数字，本次没有复算。** 作者还明确保留了较优版本的具体细节。[博客：transfer](https://ilyesbaali.me/blog/virtual-cell-challenge/#transferring-effects-from-other-cell-types)；[博客：early attempts](https://ilyesbaali.me/blog/virtual-cell-challenge/#early-attempts-and-what-they-establish)

据此采用四项工程决定：

1. **先建立透明的 source-effect 基线。** 用统一处理后的公开数据拟合效应库，与 Ridge 在同一个生成器上比较，判断先验到底增加了多少信息。
2. **每新增一个 screen 都要做增量和移除实验。** 靶点覆盖高不等于迁移质量高，背景、技术平台、扰动模态和对照定义都可能不同。三个激活状态也不能当作三个独立细胞系来证明背景覆盖。
3. **效应模型与生成器分开验收。** 固定效应时比较生成器，固定生成器时比较效应；先检查均值、零率、方差，再看六指标，减少不能归因的同时改动。
4. **把 source 内重复和跨背景一致性同时报告。** 若同靶点不同 guide 本身不一致，应该降低该条效应的训练权重；不把观察到的低相关全部归因于模型能力或生物学不可迁移。

博客的背景识别给出 A≈Jurkat、B≈HeLa、C≈CAL33 的候选及参考相关性。这是作者基于 DepMap 表达匹配的推断，未获官方确认，不能写进模型的硬身份映射或作为训练真值。可作为后续软背景特征的候选；A/B/C 上的匹配也不能替代 D/E/F 的零样本推理。

## 3. 博客中不能照抄的评分与生物学说法

逐项对照的是[官方 `cell-eval2` 指标规范](https://github.com/ArcInstitute/cell-eval2/blob/5e64833518a6603a0301cbe28185d49c30f4a986/docs/vcc2026_metrics/vcc2026-metrics-brief.md)，固定 commit 与 H1 benchmark 一致；这不表示已经审计当前线上部署版本。

| 博客中的说法或简化 | 应保留的准确边界 | 对方案的影响 |
|---|---|---|
| source 对照低于 5 CPM 的效应设零，因为评分不看 | 5 CPM gate 用的是**评分背景的真实 NTC 的 mean-cell CPM**，仅约束四个 DE 指标；不能用 source gate 替代，PDS/MSE 也不受该 gate 全面排除 | source 低表达表示效应低可靠性；保留目标基线，不能删除该基因的输出计数 |
| 以理论完美值 0/1 简化 reference scaling | 实际使用实测 `b` 和 `r`：`(u-b)/(r-b)`；MSE、NMAE 另有规定截断。官方 replicate anchor 是五次细胞分半对照评分，非所有 raw metric 的理论极值 | 委托固定版本评分器及其锚点；不得手写博客公式替换 |
| 展示简化的 MSE 和 PDS | 官方还包含 bulk 归一化/log、MSE jackknife 与 cap、PDS 整个 target panel 排除及 ties 规则 | 公式只作直觉说明；模型内效应尺度扫描仍要经过 counts 和完整评分链 |
| 400 个相同细胞必然使检验退化、无法计算 | Wilcoxon 秩检验通常仍能比较常量预测组和变动对照组；真实问题是人工分布造成不可信的秩、显著性与抽样修正 | 将均值复制作为分布破坏诊断，不预设一定报错或固定得分 |
| PCA 是刚体旋转，所以二维图距离就是真实距离 | 完整正交变换保距，截到两个主成分会丢失其余方向的距离 | 二维分离可支持背景有差别，不能单靠图确认身份或所有表达几何 |
| 目标对照已经带入所有背景特性，因此无需再建模这些部分 | RNA 对照不完整观测蛋白、染色质和调控状态，且扰动可改变原有细胞亚群与变异 | NTC 清晰区分背景不证明它足以确定全部扰动响应；模板也不保证扰动后的分布正确 |

博客讨论“零效应”的损失，而社区的严重负分来自把原本有表达的基因**输出为零计数**。二者不同：效应为零意味着保留基线，计数为零则意味着完全移除观测表达。

## 4. 社区记录的结论与撤回内容

讨论中的参赛者最初保留 top-3,000 genes，把其余基因计数强制置零，报告 NMAE 为 −6、总分 −0.9912。恢复 18,533 个基因及自然稀疏计数后，报告 NMAE 0.0022、总分 −0.3033。这为“技术性截断被解读成真实下调”提供了用户自报的前后对照；数值不作为我们运行的期望值。

同一参赛者起初把 OOM 归因于 `np.tile` 曾经产生密集中间矩阵，随后在 9 月 3 日 16:00 明确纠正：`vcc prep` 只看到已经写好的 H5AD，两个约 2.08B stored entries 的磁盘稀疏文件一成一败，原因可能是资源临界，尚不确定。**稀疏生成能减少生成阶段内存，不保证打包阶段不会 OOM。**

因此首投应分别测量：

- 生成阶段：按背景和靶点写分块，保持完整基因轴，不全量 dense concat/tile。
- 保存阶段：检查矩阵值、`obs`/`var`、自然零与显式零、总 stored entries，以及 int64 行指针。
- 打包阶段：在**最终完整 H5AD** 上实际运行 `vcc prep --dry-run` 和打包，用 `/usr/bin/time -v` 记录 peak RSS、版本和文件大小；小文件通过不能替代全尺寸实测。

约 2.1B 个存储项，单份 int32 values + int32 column indices 就约 16.8 GB，若 indices 为 int64 则约 25.2 GB，另有 indptr、元数据和运行时副本；磁盘压缩大小不反映 peak RSS。这是按 dtype 推算的存储量，不是对 `vcc prep` 的内存实测。64 GB 可作为准备资源，但不作为必定成功的保证。

## 5. H1 如何加入首投顺序

H1 是人胚胎干细胞背景，与本赛一样采用 10x Flex 数据，但这是另一个细胞背景、另一套基因轴和目标面板。它的主要价值是，在获得 A/B/C 扰动真值之前，运行一个来源清楚、规模更小、使用六指标的完整开发回路。

| 项目 | H1 工具 | A/B/C 首投 |
|---|---:|---:|
| 背景 | 一个 H1 | 三个匿名背景 |
| 靶点 | 126 | 300 |
| 预测行数 | 50,400 | 360,000 |
| 基因列数 | 18,080 | 18,533 |
| 对照细胞 | 38,176 | 每背景 18,400 |
| 标签 | 工具合同要求只保留 `target_gene` | `target_gene`、`context` |
| 作用 | 开发评分、H1 背景留出 | 比赛格式与外部评估 |

采用顺序为：H1 control baseline 核对工具 → 外部 screen 训练、只用 H1 NTC 推理 → H1 六指标 → 四背景 LOCO / 双重留出 → A/B/C 全轴生成与打包。H1 reference DE、moments、generic baseline 和 anchors 只给 evaluator；不能因它们已经压缩为小文件，就把它们当作可用训练特征。

H1 只能在整个 H1 扰动数据从训练中移除时用于跨背景开发验证。任何使用过 H1 扰动数据的 STATE/Lingshu checkpoint 或 count decoder 都不满足这个条件；它们可以另报 H1 in-domain 结果，但不能与纯 H1 holdout 混报。即使只训练 H1 剩下的 24 个靶点，也已经改变为目标背景有监督的任务。

## 6. 博客带来的数据候选与书目信息

本轮仅沿博客给定标识核验，未扩展主题检索。

| 来源 | 一手核验结果 | 处理 |
|---|---|---|
| X-Atlas/Orion | [Crossref](https://api.crossref.org/works/10.1101/2025.06.11.659105)确认规范题名、Huang et al.、2025 预印本 DOI；本轮未核实 raw-count 下载合同 | 备选数据，先查模态、对照、raw count 与许可；不把 X-Cell 模型资产状态等同于 Orion 数据状态 |
| Zhu et al. CD4 T cells | [出版方记录](https://api.elsevier.com/content/article/PII:S0092867426009293?httpAccept=text/xml)确认题名、DOI `10.1016/j.cell.2026.08.002`、2026-08-28 online；本次响应只有 core metadata，没有 Methods | 备选，不能从博客的统一“knockdown”叫法确定所有 screen 都是 CRISPRi；未核实模态前不混训 |
| Ward / DepMap 16 cell lines | [Figshare v1](https://doi.org/10.6084/m9.figshare.33273600.v1)列出 single-cell ZIP 为 3,171,208,158 bytes、CC BY 4.0；[作者 README](https://github.com/broadinstitute/perturb-seq-depmap-public)明确写 `knockouts and control guides` | 备选为重复/噪声与跨模态研究，排除出首版同模态 CRISPRi 直接混训；未下载矩阵 |
| STATE 正式发表 | [Crossref](https://api.crossref.org/works/10.1016/j.cell.2026.07.052)确认 Cell 正式标题 **Predicting cellular responses to perturbation across diverse contexts with State**，Adduri et al.，2026 年 8 月 | 为现有 STATE 条目补正式版链接，保留原预印本关系；本轮未核对正式版全文改动，不重复计为独立方法证据 |

## 7. 核验台账与剩余工作

主调查共 8 次 HTTP 请求：博客 1 次、固定版本官方指标规范 1 次、Crossref 标识核验 3 次、Figshare 数据记录 1 次、Ward 官方 README 1 次、Zhu 出版方 XML 1 次。均返回 HTTP 200；Zhu XML 只有元数据，**全文核验未完成**。没有 Scholar/SciVerse 查询，没有新增全面文献搜索。博客 HTML SHA-256：`ca5c52241698b0a7f175be05e34b8df958e7bac56802ef7c368e7e84301a2ce9`，页面标注 2026-09-01。

H1 分支只读本地 clone，静态检查与限制见[审计](h1-benchmark-audit.md)。博客和 HTTP 返回体暂存系统临时目录，未复制进 Git；没有下载 H1 15.48 GB 数据、安装模型环境或执行真实六指标评分。后续实施首先用固定环境复现 H1 工具的 control baseline，再测一套由外部数据训练的模型。
