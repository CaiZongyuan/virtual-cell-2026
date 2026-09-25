# 2026-09-25 自主微调：补充数据核验与首轮四组比较

本记录是来源核验与实验建议，不是新训练结果。先复用[论文索引](../references/INDEX.md)、[本地方案](pretrained-finetuning-local-plan.md)、[数据清单](perturbation-dataset-catalog.md)、[首轮复盘](state-first-run-postmortem-2026-09-25.md)与[官方数据合同](../Official-website/About-the-Data.md)。官方提交继续暂停。

**建议先修复对照表达校准，补入 Jurkat 作为独立确认背景，再跑 NTC、经验效应迁移、冻结 State 微调和有限解冻 State 微调四组。** 原 Replogle 大文件不会补回缺失基因；Jiang 已核实属于 CRISPRi，可在首轮之后逐通路扩展背景。Orion 的完整 H5AD 超过 500 GB 上限，若以后使用应选择流式 Parquet 子集。

## 1. 数据扩充的实际增量

CRISPRi（CRISPR interference，转录抑制）降低靶基因表达；它与破坏 DNA 的 knockout/KO 不同。NTC（non-targeting control，非靶向对照）用于估计该背景未受指定基因扰动时的表达。训练时比较扰动与匹配 NTC，才能减少把实验批次或外源刺激错当作靶基因效应的风险。

| 来源 | 本轮核实的增量 | 本轮决定 |
|---|---|---|
| Nadig Jurkat | 服务器既有四源缺少的第四个细胞背景；压缩 H5AD 1.294 GB，既有原件范围读取审计为 262,956 × 8,882 | **采用为确认集**；不参与本轮微调、超参数选择或效应库。父权重 `zeroshot/jurkat` 的留出声明仍须与作者配置相互核对 |
| Replogle 作者原件 | 作者说明 raw 文件本身已过滤至平均 >0.01 UMI/cell 的基因；scPerturb 转换代码读取同一 raw X，没有表达归一化或基因子集选择 | **排除重复下载用于补基因**；继续采用服务器压缩副本。GWPS 原件 65.83 GB 不带来新的全基因面板 |
| Jiang 六细胞系 | 明确为 CRISPRi；A549、MCF7、HT29、HAP1、BxPC3、K562；IFNβ/IFNγ/TGFβ/TNFα/insulin 五种刺激，刺激 24 h | **备选为下一批训练增量**；相对已有 K562 增加五个细胞系。先取一个通路，保留刺激与批次，使用匹配 NTC |
| X-Atlas/Orion | HCT116、HEK293T，全基因组 CRISPRi；作者 HF 卡明确稀疏 raw counts、基因 ID 映射、guide 与 batch 字段 | **备选**；按需流式筛取，完整 H5AD 559.52 GB 不进入下载单；CC BY-NC-SA 4.0 的适用性沿用既有未解决项 |
| Blair et al. Flex 多模态筛选 | 新发现候选论文，题名和预印本 DOI 经 Europe PMC 核实；搜索摘要称联合蛋白/RNA/CRISPR 与 10x Flex | **备选、暂不训练**；原文 403，未定位原始矩阵、许可和明确干预模态，不能仅凭摘要加入数据 |

Jurkat 可直接使用现有 `assets.py jurkat` 下载接口。固定资产为：

- 文件：`NadigOConner2024_jurkat.h5ad`。
- 下载：<https://zenodo.org/api/records/13350497/files/NadigOConner2024_jurkat.h5ad/content>。
- 字节数：`1,293,665,804`；MD5：`d8b05d00bfbd686d37ffdd4293bc6c8c`。
- Zenodo 记录许可：CC BY 4.0；原论文 DOI：<https://doi.org/10.1038/s41588-025-02169-3>。
- 矩阵整数性、NTC 标签、有效靶点和实际覆盖仍由下载后的文件核验，不把原论文规模当作经过本轮 ETL 后的样本数。[来源：固定 Zenodo API](https://zenodo.org/api/records/13350497)

Replogle 的“原件能否补基因”已可收敛：作者 [Figshare 描述](https://api.figshare.com/v2/articles/20029387)明确三个 raw 文件只保留 `>0.01 UMI per cell` 基因；[固定 scPerturb 转换代码](https://github.com/sanderlab/scPerturb/blob/b69f72a070a92bcbaf41e7f9897b11598109ab48/dataset_processing/scripts/ReplogleWeissman2022.py)保留 X，修改注释并处理重复符号。现有 [GWPS 文件审计](../../experiments/local_benchmark/asset-inventory-2026-09-25.json)为 1,989,578 × 8,248。因此应先使用测量 mask、保留目标 NTC 的未监督基因；不能以同源原件的更大体积推断更广的基因覆盖。Nadig 原件的 9,624/8,882 基因同样已在[前次范围读取审计](data-compute-capacity-sources.md)登记。

## 2. Jiang 的模态与规模需要修正解读

[PMC 作者稿正文](https://pmc.ncbi.nlm.nih.gov/articles/PMC12083445/)的 “Scalable and flexible Perturb-seq across cell lines and conditions” 节明确：六种细胞系均引入 `dCas9-KRAB-MeCP2` CRISPRi 系统，每通路挑选 44–61 个调控基因，每基因三条 sgRNA（single-guide RNA，向导 RNA），另有 14 个 NTC。这消除了旧目录中“尚不确定 CRISPRi/KO”的缺口。

**约 1,500 项扰动不是约 1,500 个不同靶基因。** 作者稿明确计数单位为靶基因 × 细胞系 × 刺激组合（1,626 个实验组合；其下游分析保留 1,596 组基因列表）。因此其主要价值是背景与刺激多样性，不能把该数字当作新增靶点词表规模。旧容量笔记中“与比赛 300 targets 重叠 9 个”来自参赛者派生表，本轮尚未从作者靶点表复核，不能用作最终覆盖数据。

论文的 Mixscale 根据表达响应为细胞赋予连续扰动强度，而不是简单把所有逃逸细胞二分删除。这个结果支持在后续数据清洗中记录 guide/强度异质性；它没有直接证明按 Mixscale 过滤会提高本赛模型。第一轮应保留可追溯原始计数和身份，不用模型推定的“有效性”不加记录地替换原实验标签。

[正式版 Data Availability](https://www.nature.com/articles/s41556-025-01622-z#data-availability)指向 GEO `GSE281048` 和 Zenodo `14518762`；PMC 作者稿还保留较早 Zenodo `10520190`，本轮固定正式版数据记录，不合并为额外独立实验。

以下均来自[正式记录 API](https://zenodo.org/api/records/14518762)，许可 CC BY 4.0。下载前缀为 `https://zenodo.org/api/records/14518762/files/`，后接文件名及 `/content`：

| 文件 | 字节数 | MD5 |
|---|---:|---|
| `Seurat_object_TGFB_Perturb_seq.rds` | 2,642,041,433 | `8e9b4d39a95ec5881a30be6a2df541d1` |
| `Seurat_object_IFNG_Perturb_seq.rds` | 2,915,636,149 | `0fef1f14c36906e9c40e4d1c6aae6926` |
| `Seurat_object_IFNB_Perturb_seq.rds` | 4,326,548,669 | `3eb5e7af1601bf562a5b20dea5de3dc9` |
| `Seurat_object_TNFA_Perturb_seq.rds` | 4,656,209,976 | `60ed8bff6c749b1250f8fde9c5435c2e` |
| `Seurat_object_INS_Perturb_seq.rds` | 5,601,176,410 | `c7b830dfcc020545c3f222cad5b13b34` |

合计 **20,141,612,637 bytes**。README 把 TGFB 文件写成 `TGFB1`，实际 API 文件名为 `TGFB`，下载以 API 为准。建议后续先审计最小的 TGFB 文件：读取 Seurat 的 RNA `counts`（不可用 `data`/`scale.data` 代替），导出整数稀疏矩阵、gene、guide、cell line、stimulus、replicate，并对每个 line × stimulus × replicate 配对 NTC。以上 `counts` 层是否实际保留仍待打开 RDS 核验，文件体积不能证明其内容。

## 3. Orion 的可行取数方式

[作者 HF 数据卡](https://huggingface.co/datasets/Xaira-Therapeutics/X-Atlas-Orion/blob/main/README.md)提供 `streaming=True`，按 `HCT116`/`HEK293T` split 读取；`gene_expression` 为非零基因原始计数，`gene_token_id` 通过 `metadata/gene_metadata.parquet` 映射到 Ensembl ID/符号。`gene_target`、`guide_target`、`sample`、`pass_guide_filter` 可保留扰动与批次审计信息。

优先只保留竞赛/开发靶点、匹配 NTC 和少量扩展训练靶点，设置每来源与每靶点上限。流式筛行降低落盘体积，但若 Parquet 没有按靶点组织，仍可能扫描大量远端数据；不能声称只下载命中行。其更低的中位压低效率（作者自报 HCT116 75.4%、HEK293T 51.5%）是标签分布差异，需记录来源与剂量效应，不能把它们假定成官方 >80% 效率条件。[既有容量与许可核验](perturbation-dataset-catalog.md)

## 4. 先做 1 个基线 + 3 个候选

复盘已显示旧适配模型连 NTC→NTC 都出现约 0.54–0.59 的组成 TV 偏移。这一量级的背景错误应先解决。更多样本无法自动修复输出语义；原父权重归一化和 batch 合同未解决前，新的适配实验也不能称为忠实复现原生 State。

| 组别 | 固定变化 | 用途 |
|---|---|---|
| B0：NTC 重采样 | 原始对照计数；固定种子和每条件 400 个细胞 | 全流程保守基线，复现既有 H1 分数 |
| C1：经验效应迁移 | 仅从 K562/RPE1/HepG2 的匹配扰动/对照估计收缩后的效应；无覆盖靶点回退 B0 | 低成本参考；隔离“训练标签本身能否迁移” |
| C2：冻结主干 State 差分微调 | 复用公开权重主干；只训练适配层；以同一对照集合上的 `f(x,t) − f(x,NTC)` 表示效应 | 测试保留目标背景后，已有表征能否贡献扰动效应 |
| C3：有限解冻 State 差分微调 | 与 C2 相同数据、解码与步数预算，只增加有限主干层可训练参数 | 测试微调主干的增量，不能与 C2 同时变更数据或输出合同 |

C1 是诊断参考；主模型继续遵循公开预训练权重微调，不从零预训练。C2/C3 的差分设计是本项目待验证工程假设，不是 State 原论文报告的方法。相减的两次前向必须使用相同对照集合及 batch 信息；评价关闭 dropout。对 `t=NTC` 应先得到精确零效应，避免两个不同采样集合的偏差进入差分。

计数解码可测试按基因二项 thinning（随机保留一部分原分子）与 Poisson 增量，保留未监督基因的原始计数且避免全局重新归一化。但它会改变方差、协方差及每细胞总量，不能只因均值校准便视为解决了单细胞分布。限幅和收缩系数必须由训练/开发协议确定；输出仍需非负整数、有限值及总计数上限检查。

文献依据是分层的：State 支持跨背景状态转移与公开权重迁移；[响应分解预印本](https://doi.org/10.64898/2026.07.24.740459)支持区分共享靶点效应和背景交互；[线性基线论文](https://doi.org/10.1038/s41592-025-02772-6)支持保留低复杂度参考。它们均不直接证明本轮差分 State 或计数解码会提高 VC2026 六指标。

首轮采用固定小诊断 → 完整 H1 126 targets × 400 cells × 18,080 genes → 冻结配置后的 Jurkat 确认。H1 的扰动真值、DE 缓存、参考 moments 只交给评价器；H1 已是开发背景，不能称独立测试。Jurkat 所有扰动标签和派生统计在最终配置冻结前隔离，不能在挑 C2/C3 学习率时偷看确认成绩。使用 Jurkat 留出父权重只是必要线索；预训练来源不明时仍标暴露未知。

每组记录综合分、六分项、原始归一化 MSE/NMAE、逐靶点分数、已覆盖/未覆盖靶点分组及新旧基因分组。只有低成本均值和无扰动校准通过，才消耗完整评价资源。首个完整种子后仅为获胜候选做种子复核；没有获胜者就保留 B0 和负结果，不把“比旧失败模型好”视为微调成功。

Stack 保持下一阶段候选。其公开权重和冻结教师微调入口已在[本地方案](pretrained-finetuning-local-plan.md)核验，但 15,012 原生基因、外部同靶点示例与未知原始计数映射会增加新的变量。先完成上述可归因的小比较，再开独立 Stack 原生校准实验，避免同时重做数据、模型和解码。

## 5. 500 GB 总使用上限

500 GB 是服务器本项目**总占用上限**，不是新增下载配额。执行者应在每次下载、转换和预测导出前统计项目目录、下载临时文件、环境/缓存、检查点和评分输出；并发写入也计入。四组先共用同一只读源数据，按组顺序输出，保留失败摘要及必要复现实物，不复制同源 85 GB 原件。

本轮研究只新增小型核验材料，均在 Git 忽略的 `output/autonomous-data-review-2026-09-25/`；未下载训练矩阵或权重。立即新增数据计划只有 Jurkat 1.294 GB；后续 TGFB 试点需预留 RDS + 转换矩阵 + ETL 峰值工作空间，不以 2.642 GB 文件大小估算内存。大输出预留至少 50 GB 余量，操作前无法保证总量低于 500 GB 就先缩小导出/缓存范围。

## 6. 检索台账与未解决项

Infra Scholar 顺序调用 **2 次**，每次查看前 10 条；首轮缺少 Jiang 的明确论文与模态证据，因此只做一次精炼：

1. `cross cell type CRISPRi Perturb-seq raw count public dataset Jiang 2025 transcriptional responses signal pathways multi cell lines finetuning State`。request ID `e4e869390e2c4b1d997e607c8f043052.984.17903505142074969`。命中 Replogle、X-Cell 等既有候选，未解决 Jiang 模态。
2. `"Systematic reconstruction of molecular pathway signatures using scalable single-cell perturbation screens"`。request ID `0166df9216be4b6bbc11259286d9e80e.359.17903505674964979`。命中 Jiang 预印本、Blair Flex 候选；Jiang 正式版与预印本合并为一项。其他命中仅初筛题名/摘要，未用于方法或数据决策，不扩搜。

直接 HTTP 共 **14 次**：Jiang Europe PMC 元数据、Jiang Zenodo API、Replogle Figshare API、scPerturb Zenodo API、Jiang Europe PMC 全文 XML、Jiang README、固定 scPerturb 转换脚本、Orion HF README、Blair bioRxiv HTML、Jiang 出版页、Blair Europe PMC 元数据、Jiang PMC 正文、Jiang 出版方补充 XLSX、Jiang PMC 向导表。10 次得到可用内容；4 次未完成证据读取：Jiang XML HTTP 500，Blair HTML HTTP 403，出版方补充 XLSX 达到本次小文件 10 MB 读取上限后停止，PMC XLSX 返回下载过渡 HTML。补充表失败后停止，不把 HTML 冒充 XLSX，也不从未读文件推断靶点覆盖。无 SciVerse/Paper Schema 调用。

实际用于判断的 Replogle、Nadig、Jiang、Orion、State、Stack、响应分解与线性基线均已在索引登记，本轮补充复核状态；Blair 新增为备选。缺口为 Jiang RDS 真实 counts/基因与靶点覆盖、Orion 许可与子集读取成本、Blair 全文/矩阵入口、父权重原生尺度与预训练暴露，以及所有新候选的真实六指标收益。未命中和访问失败均不等于数据不存在。
