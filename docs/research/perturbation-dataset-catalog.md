# 公开扰动单细胞数据源清单（VC2026）

> 核验日期：2026-09-23。范围是可发现的数据源与下载合同；本轮只访问论文、作者数据记录和小型元数据，没有下载大型表达矩阵。下载前仍须核对文件版本、数据许可、原始计数和对照标签。既有首投下载决定见[首投方案](first-submission-plan.md)，本清单不自动改变它。

## 如何读这份清单

**Perturb-seq** 是把基因扰动与单细胞 RNA 测序结合，在每个细胞里记录扰动身份和表达谱的实验。**CRISPRi**（CRISPR interference）用失活 Cas9 压低目标基因转录；**CRISPR knockout/KO** 通常破坏基因功能，两者的效应强度不能直接混同。**UMI 原始计数**是对每个细胞、每个基因检测到的分子数，是比赛要求输出的量；标准化或 `log1p` 矩阵不能直接当作原始计数。化学扰动改变的是药物处理条件，不等同于靶基因 CRISPRi。

本赛给定匿名新细胞背景的未扰动对照和靶基因，预测 CRISPRi 后的单细胞原始计数；[官网](../Official-website/About-the-Data.md)允许使用有权使用的外部数据。下表的“采用”表示数据来源值得进入当前候选训练集，不表示已下载或已证明能提高分数。

## 遗传扰动：优先核查

| 数据源 | 生物背景、模态与规模 | 可取得的内容、体积和入口 | 判断与待核验项 |
|---|---|---|---|
| **Arc VC2025 H1** | H1 人胚胎干细胞；CRISPRi、10x Flex；300 个靶基因 | [作者数据说明](https://github.com/ArcInstitute/arc-virtual-cell-atlas/tree/main/virtual-cell-challenge)、[GCS Marketplace](https://console.cloud.google.com/marketplace/product/bigquery-public-data/arc-institute?project=gcp-public-data-arc-institute)；train/validation/test H5AD 共 34.36 GB，初始训练文件 15.48 GB。[体积审计](data-compute-capacity-sources.md#22-h1只取-processed-h5ad不取-fastq) | **采用，同测序化学的校准/验证源。** GCS 是 Requester Pays；2 TB/月优惠只适用于订阅同一项目的访问。使用前固定对象版本与 split，不能把 H1 基因面板缺失的 2026 基因当成零表达。 |
| **Replogle et al. 2022** | K562 全基因组及 K562/RPE1 必需基因 screen；CRISPRi；论文报告总计超过 250 万细胞 | [论文](https://doi.org/10.1016/j.cell.2022.05.013)、[作者 Figshare](https://doi.org/10.25452/figshare.plus.20029387.v1)；三个 raw single-cell H5AD 共 85.19 GB，CC BY 4.0；[scPerturb 压缩副本](https://zenodo.org/records/13350497)三文件约 11.59 GB | **采用，核心靶点与背景训练源。** K562 两个 screen 是同一个细胞背景；作者矩阵与整理副本只能选一份计样本。先核对 `X` 是否保留原始计数和目标/对照映射。 |
| **Nadig et al. 2025** | HepG2、Jurkat；common-essential CRISPRi | [论文](https://doi.org/10.1038/s41588-025-02169-3)、[GEO GSE264667](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE264667)；两件 raw H5AD 共 14.98 GB；[scPerturb 压缩副本](https://zenodo.org/records/13350497)约 2.14 GB | **采用，核心跨背景训练源。** 整理副本与 GEO 原件不能重复计样本；下载后核对 guide、对照、测量基因和稀疏化处理。[既有审计](data-compute-capacity-sources.md)。 |
| **Jiang et al. 2025** | 六个癌细胞系、五种信号刺激条件；Perturb-seq，约 260 万细胞、超过 1,500 项扰动（论文口径） | [论文](https://doi.org/10.1038/s41556-025-01622-z)、[Zenodo 14518762](https://zenodo.org/records/14518762)；五个 Seurat RDS 共 20.14 GB，CC BY 4.0 | **备选，扩展背景。** 五个文件按信号通路分，不按细胞系分；必须读 Methods 和矩阵确认每项扰动的 CRISPR 模态、刺激与匹配对照，再决定是否与 CRISPRi 合训。[既有审计](data-compute-capacity-sources.md)。 |
| **X-Atlas/Orion** | HCT116、HEK293T；两个全基因组 CRISPRi screen，约 800 万细胞 | [预印本](https://doi.org/10.1101/2025.06.11.659105)、[作者 Figshare v3](https://doi.org/10.25452/figshare.plus.29190726.v3)：两个 H5AD 共 **559.52 GB**；[作者 Hugging Face](https://huggingface.co/datasets/Xaira-Therapeutics/X-Atlas-Orion)：332 个 Parquet 文件约 **126.26 GB**，README 明确 `gene_expression` 为稀疏原始计数，可按 split 流式读取 | **备选，潜在高价值但不在首投下载单。** CC BY-NC-SA 4.0；奖金竞赛中的使用是否落在非商业许可内需先判断。作者自报 HCT116/HEK293T 中位靶向压低效率为 75.4%/51.5%，不能照搬比赛的 >80% 质量假设；需核对对照和最终可用行数。 |
| **Zhu et al. 2026 CD4 T cells** | 原代人 CD4+ T 细胞，多种激活状态；全基因组 Perturb-seq | [Cell 论文](https://doi.org/10.1016/j.cell.2026.08.002)；出版元数据可核，原始矩阵入口本轮未定位 | **备选，免疫背景。** 目前不能确认扰动是 CRISPRi 还是 KO，也未确认 raw counts、对照和许可；不进入首投训练。不同激活状态不能算成不同细胞系。 |
| **Ward/DepMap 16 细胞系** | 16 个癌细胞系；作者代码明确是 **knockout** 与对照 guide | [作者 Figshare v1](https://doi.org/10.6084/m9.figshare.33273600.v1)、[代码与 README](https://github.com/broadinstitute/perturb-seq-depmap-public)；`single_cell_data.zip` 3.17 GB，CC BY 4.0 | **备选，用于跨模态或噪声分析。** KO 不能不加标识地混作 CRISPRi。ZIP 内单细胞矩阵的计数层与完整元数据仍须下载后核验。 |

## 目录与其他扰动类型

| 资源 | 覆盖和入口 | 用途与边界 |
|---|---|---|
| **scPerturb** | [Zenodo 固定记录 13350497](https://zenodo.org/records/13350497)：54 个 RNA/蛋白 H5AD，共 43.04 GB，CC BY 4.0；含 Replogle、Nadig、Adamson、Norman、sci-Plex 等文件 | **采用为发现与压缩下载入口。** 它统一整理既有实验，不是 54 组独立的新来源；逐文件回到原论文确认模态、处理方式和计数层。当前首投只使用其中五个 Replogle/Nadig 文件。 |
| **PerturbDB** | [论文](https://doi.org/10.1093/nar/gkae777)、[数据库](http://research.gzsys.org.cn/perturbdb)：论文收集 66 个 Perturb-seq 数据集，约 451 万细胞、19 个细胞系 | **备选为来源发现与效应查询。** 它汇编已有实验，并用 Mixscape 识别有效扰动；下载矩阵是否保留未经筛选的原始计数逐数据集核验。不可把它与原始实验重复计样本。 |
| **Tahoe-100M** | [Arc 作者说明](https://github.com/ArcInstitute/arc-virtual-cell-atlas/tree/main/tahoe-100M)：约 1.006 亿细胞，多个癌症细胞系的**药物**处理，H5AD + Parquet，GCS Marketplace | **备选为化学扰动预训练/背景表征**，不是 CRISPRi 靶基因效应的直接标签。整库体积很大，GCS 收费条件同 H1；只按需要的 prefix 访问。 |
| **sci-Plex / sci-Plex-Gene-by-Environment** | [Srivatsan et al. 2020](https://doi.org/10.1126/science.aax6234)、[GEO GSE139944](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE139944)：三个癌细胞系、188 种化合物；[McFaline-Figuero et al. 2024](https://www.cell.com/cell-genomics/fulltext/S2666-979X(23)00339-7)、[GEO GSE225775](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE225775)：胶质母细胞瘤中的遗传与化学组合筛选 | **备选为跨模态/组合响应研究。** 官网将两者列为公共扰动数据；本轮未核对 GEO 文件、具体遗传扰动机制和许可，不进入直接 CRISPRi 训练集。 |

## 执行顺序与质量门

1. **先复用既定五文件**：K562 GWPS、K562 essential、RPE1、HepG2、Jurkat；再用 H1 做同化学方法的校准和留出评价。它们已有[文件级下载计划](first-submission-plan.md#2-数据和资产固定下载清单)，无须因清单扩展而推迟首投。
2. **只在验证收益后扩容**：先考察 Jiang 的额外背景，再评估 Orion 的许可、按批流式读取成本和弱 knockdown 标签；CD4 数据必须先找到一手矩阵与 Methods。
3. **每个来源进入训练前检查**：`X`/`layers` 中哪一层是非负整数 UMI、guide/target/NTC 字段、细胞背景和批次、基因 ID 与测量 mask、重复实验和来源版本。用 DOI/原始实验 ID 去重；同一细胞系的多 screen 在背景留出时一起排除。

## 检索记录与未解决缺口

- 先复用[论文索引](../references/INDEX.md)、[比赛官网副本](../Official-website/About-the-Data.md)和[既有容量审计](data-compute-capacity-sources.md)。新发现查询按顺序调用 Infra Scholar 两次：`public single-cell genetic perturbation CRISPRi Perturb-seq raw counts multi cell line dataset 2025 2026`；因缺少新多背景数据，再精炼为 `X-Atlas Orion genome-wide Perturb-seq primary CD4 T cell CRISPRi public data accession 2025 2026`。各返回 10 条；第一轮发现 PerturbDB，第二轮定位 Orion 数据 DOI。预印本、论文和数据记录合并为同一实验来源。
- 一手核验：Arc Atlas 与 Tahoe/H1 作者 README、Replogle/Orion/Ward Figshare API、Orion Hugging Face 数据卡与文件树、scPerturb/Jiang Zenodo API、PerturbDB 的 PMC 原文 XML，以及 CD4 论文的 Crossref/Europe PMC 元数据。新数据均未下载，故矩阵值、guide 覆盖及下游效果未验证。
- `www.ncbi.nlm.nih.gov` 在本机直连 TLS 失败，sci-Plex 两个 GEO 记录及 Nadig GEO 本轮没有重新访问；Nadig 仍可依赖前次[绕路核验](data-compute-capacity-sources.md)。CD4 原文与矩阵入口、Jiang 具体模态、Orion 许可在奖金竞赛中的适用性是未解决缺口。搜索未命中或页面不可达不表示数据不存在。
