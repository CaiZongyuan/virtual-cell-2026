# 效应可信度与收缩：文献复核（2026-09-26）

本轮先复用 `docs/references/INDEX.md`。已有研究支持保留强统计参照，但不证明当前数据中的具体噪声来源；新的训练分半诊断和候选实验负责检验这一工程假设。

## 实际采用的证据与实现边界

- **ashr 作者实现（方法依据）**：[官方仓库](https://github.com/stephens999/ashr)，已读取作者 README。它明确输入为效应估计及其标准误，标准误越大的估计应受到更强收缩，并从数据估计收缩程度。仓库来源已由 GitHub API 确认；本轮未安装或调用 ashr，也未宣称复现该软件的统计保证。
- **Urbut et al., Flexible statistical methods for estimating and testing effects in genomic studies with multiple conditions**：[Nature Genetics](https://doi.org/10.1038/s41588-018-0268-8)，2018-11-26 在线，51:187–195 (2019)。已核出版页作者、书目和摘要；全文正文未取得。论文摘要支持跨条件效应估计及相关性建模的方向，但不能据此声称本轮实现了 mash。本轮采用其问题意识，多变量建模留作备选。

本轮自定义估计器假设每个观测 log effect 近似服从“真实效应 + 已估计方差的正态噪声”，真实效应先验是包含零点质量的固定尺度正态混合。EM 仅拟合混合权重，后验均值以方差决定逐项收缩。与 ashr/mash 的默认先验、拟合器、相关性处理和自由度处理均不相同。delta-method 方差使用细胞抽样波动，不能当作独立生物重复误差；零假设 p 值、FDR 和机制因果性均未作保证。

## 检索台账

Infra Scholar 顺序查询 2 次，先发现、因未覆盖具体收缩方法再精炼一次，均成功，各查看前 10 条。未调用 SciVerse 或 Paper Schema，不进行第三次主题查询。

- `Perturb-seq cross cell type prediction pseudobulk perturbation effect denoising empirical Bayes uncertainty`
- `"multivariate adaptive shrinkage" gene expression effect estimates Stephens Urbut`

一手 HTTP 共 7 次：Nature 出版页 1、错误的 ashr 文档路径 2、错误组织的仓库 API 1、实际 stephens999/ashr 仓库 API 1、根目录 API 1、作者 README 1；4 成功、3 个 404。错误路径均不作为方法不存在的证据，仓库已通过正确作者命名空间解决。Nature 只取得出版页摘要，不声称全文已读。

作者 README SHA-256：`baee80297e0df2e20c808c967eed88607ece691f58f4e9e4316aa7bee0a40ccd`；出版页 SHA-256：`12d29e6854a08abdd38a62707788ef64ddd1b1cde8119d05f541e397fb314b5f`。原网页留在本地忽略目录，仅提交转述和元数据。

## 候选收敛

以下是已查看题名/摘要的筛选记录，主要用于排除任务不匹配的材料。除上述一手来源外，书目、摘要和年份均仅为 Scholar 返回线索，待原文核验；缺摘要明确保留为空，不补造。完整返回题名、作者、DOI、摘要、查询和版本线索见 [search-results.json](reliability-transfer-sources-2026-09-26/search-results.json)。BuDDI 的预印本与正式版合并，不计为独立证据。

| 查询-序号 | 题名 | 决定及与本轮的关系 |
|---|---|---|
| 1-1 | [Predicting the unseen: a diffusion-based debiasing framework for transcriptional response prediction at single-cell resolution](https://doi.org/10.1101/2025.09.12.675662) | 排除：已有 dbDiffusion 条目，本轮不重开扩散生成路线。 |
| 1-2 | [Unsupervised removal of systematic background noise from droplet-based single-cell experiments using CellBender](https://doi.org/10.1038/s41592-023-01943-7) | 排除：处理空液滴/背景 RNA，不能据摘要当作扰动效应估计器。 |
| 1-3 | [Scalable multimodal mapping of macrophage regulatory architecture by integrating optical and transcriptomic pooled screens](https://www.biorxiv.org/content/10.64898/2026.05.27.728345.abstract) | 备选：新多模态筛选线索，未核数据/背景合同，本轮不采用。 |
| 1-4 | [BuDDI: Bulk Deconvolution with Domain Invariance to predict cell-type-specific perturbations from bulk](https://doi.org/10.1371/journal.pcbi.1012742) | 排除：bulk/scRNA 域迁移，输入合同不同。 |
| 1-5 | [BuDDI:<i>Bulk Deconvolution with Domain Invariance</i>to predict cell-type-specific perturbations from bulk](https://www.biorxiv.org/content/biorxiv/early/2023/10/05/2023.07.20.549951.full.pdf) | 并入同查询第 4 条正式版。 |
| 1-6 | [Interpretation, extrapolation and perturbation of single cells](https://www.nature.com/articles/s41576-025-00920-4) | 排除：综述线索，未用于具体方法判断。 |
| 1-7 | [A systematic comparison of single-cell perturbation response prediction models](https://www.science.org/doi/abs/10.1126/sciadv.aed3414) | 备选：已知模型比较主题，未以未读全文指导本轮数值设置。 |
| 1-8 | [CellPLM: Pre-training of Cell Language Model Beyond Single Cells](https://www.biorxiv.org/content/biorxiv/early/2023/10/05/2023.10.03.560734.full.pdf) | 排除：不因“去噪”关键词更换预训练主线。 |
| 1-9 | [ICAT: a novel algorithm to robustly identify cell states following perturbations in single-cell transcriptomes](https://academic.oup.com/bioinformatics/advance-article-pdf/doi/10.1093/bioinformatics/btad278/50066629/btad278.pdf) | 排除：处理细胞状态匹配，未核零样本预测合同。 |
| 1-10 | [scDisInFact: disentangled learning for integration and prediction of multi-batch multi-condition single-cell RNA-sequencing data](https://www.biorxiv.org/content/biorxiv/early/2023/05/02/2023.05.01.538975.full.pdf) | 排除：批次/条件解耦相关，但本轮没有其可复用权重合同。 |
| 2-1 | [Fine‐mapping and QTL tissue‐sharing information improves the reliability of causal gene identification](https://onlinelibrary.wiley.com/doi/pdfdirect/10.1002/gepi.22346) | 排除：QTL 精细定位应用，不直接作为 Perturb-seq 预测证据。 |
| 2-2 | [Flexible statistical methods for estimating and testing effects in genomic studies with multiple conditions](https://www.nature.com/articles/s41588-018-0268-8) | 采用问题意识、备选多变量方法：出版页摘要已核；本轮不是 mash 复现。 |
| 2-3 | [A comparison of gene expression and DNA methylation patterns across tissues and species](https://genome.cshlp.org/content/30/2/250.full.pdf) | 排除：物种/组织比较应用，仅作为收缩方法引用线索。 |
| 2-4 | [A flexible empirical Bayes approach to multivariate multiple regression, and its improved accuracy in predicting multi-tissue gene expression from genotypes](https://journals.plos.org/plosgenetics/article?id=10.1371/journal.pgen.1010539) | 备选：多变量回归拓展，当前未核全文或实施。 |
| 2-5 | [Dynamic effects of genetic variation on gene expression revealed following hypoxic stress in cardiomyocytes](https://doi.org/10.7554/elife.57345) | 排除：缺氧 eQTL 应用，不是本轮扰动预测数据。 |
| 2-6 | [Multivariate adaptive shrinkage improves cross-population transcriptome prediction and association studies in underrepresented populations](https://zenodo.org/record/7909040) | 排除：跨人群基因型预测模型，不混作 CRISPRi 数据。 |
| 2-7 | [Model-based dimensionality reduction for single-cell RNA-seq using generalized bilinear models](https://www.biorxiv.org/content/biorxiv/early/2023/04/25/2023.04.21.537881.full.pdf) | 备选：单细胞降维的不确定性线索，未核正式版本，本轮不采用。 |
| 2-8 | [Evolution of gene expression across brain regions in behaviourally divergent deer mice](https://onlinelibrary.wiley.com/doi/abs/10.1111/mec.17270) | 排除：鹿鼠表达比较，任务不同。 |
| 2-9 | [Flexible statistical methods for jointly modeling effects](http://knowledge.uchicago.edu/record/794) | 排除：Urbut 学位论文，相关方法历史线索，不计为新的验证证据。 |
| 2-10 | [Bayesian multivariate genetic analysis improves translational insights](https://doi.org/10.1016/j.isci.2023.107854) | 排除：脂质 GWAS 应用，未用于细胞扰动方法判断。 |
