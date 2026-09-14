# VC2026 数据与算力容量规划：一手证据和可执行预算

> 当前执行方案已于 2026-09-14 重制为 STATE 主基线及全基因改进版；本文保留为历史研究，资源请求和模型顺序以[首投方案](first-submission-plan.md)为准。

> 核查日期：2026-08-30
>
> 范围：只采用 Arc/比赛官方页面与 API、原始论文、作者数据仓库、作者代码/README/Colab 和本仓库实测。下载体积来自对象仓库的 `size` 字段或作者下载日志；没有下载任何大型数据文件。
>
> 单位：`GB = 10^9 bytes`，`GiB = 2^30 bytes`。比赛官网若把 GiB 数字写成“GB”，下表同时给出精确字节以消除歧义。
>
> 总体技术路线与最终轮 runbook 见 [VC2026 竞争性实施路线](completion-strategy-primary.md)。

## 1. 结论：应该准备什么

### 1.1 推荐方案

主线不是从头预训练大型基础模型，而是一个由五个可单独验收的部件组成的混合系统：

1. **STATE starter 是必须复现的强基线。** 当前榜单中名为 `STATE baseline` 的 entry 已达 0.1894；Arc 官方 VCC Colab 又证明 162M 参数版本可在单张 T4 上训练。先取得一个可重复的 STATE 输出，再谈自研模型。
2. **K562 GWPS 是 target-effect memory。** 经参赛者公开 target 列表与当前 300 targets 复算，K562 genome-wide 覆盖 272/300；它负责提供大多数当前目标的直接扰动方向。该数字属于可复算的参赛者数据审计，下载后必须从 H5AD `obs` 再独立确认。
3. **四背景 common-essential 数据学习 context transfer。** K562 essential、RPE1、HepG2、Jurkat 的公开 target 列表有 2,054 个四方交集；在这些目标上学习“已知 K562 response + 目标背景 NTC -> 新背景 response”的低秩算子。Jiang 六细胞系只在这一步跑通后加入。
4. **方向与幅度分开校准。** 在 128-256 维 response PCA 空间融合 STATE、K562 direct delta 和 context-transfer Ridge/MLP；一个 head 预测单位方向，另一个 head 预测 effect norm。榜单显示当前第一名相对 STATE 的主要收益来自 NMAE、reach 和 MSE，而不是 PDS。
5. **NTC-conditioned raw-count emitter。** 对每个 context 固定一组 construct-balanced NTC templates，在平滑 rate 上施加最终 delta，再用分层多项式/NB 生成 400 个整数细胞。集成发生在 effect/rate 层，不平均已经生成的 count matrices。Stack 只有取得有奖金竞赛的书面许可后才能进入候选。

首版数学接口应保持简单：

```text
d_final(c,t)
  = d_state(c,t)
  + lambda(c,t) * P_common[d_transfer(c,t) - d_state(c,t)]

d_transfer(c,t)
  = scale(c,t) * direction(K562_delta(t), NTC_embedding(c), target_prior(t))
```

`P_common` 只在各公共 screen 可靠测量的基因上修正 STATE；其余基因保留 STATE/NTC 预测。对 K562 未覆盖的 target，退回 ESM2/功能先验和 STATE，不虚构直接效应。

该顺序直接受 2026 合同约束：每轮要生成 `3 x 300 x 400 = 360,000` 个细胞、18,533 个基因的 raw counts，六项缩放指标等权，而最终 D/E/F 没有任何扰动训练数据。[官方数据页](../Official-website/About-the-Data.md)；[官方 FAQ](../Official-website/FAQs.md)

### 1.2 推荐机器和总预算

当前机器实测是 i7-12700H（20 threads）、15 GiB RAM、RTX 3070 Ti Laptop 8 GiB、892 GiB 可用盘。磁盘足够，RAM/VRAM 是约束。

| 档位 | 数据下载 | 工作盘 | RAM | GPU | 能完成什么 | 总算力 |
|---|---:|---:|---:|---|---|---:|
| 本机最低档 | 18-23 GB | 120 GB | 当前 15 GiB，强制 backed/chunked | RTX 8 GiB + 可选 1 次 T4 | evaluator、统计 transfer、生成器、一个 STATE starter | 10-25 T4-hours；其余本机 |
| **推荐档** | **约 43.5 GB** | **300 GB** | **32-64 GB** | T4/L4 16-24 GB 训练；A100 40 GB 做 full scoring burst | STATE + transfer operator + scale head + count emitter + 4-6 个候选 | **60-100 T4-hours，或约 20-40 A100-hours** |
| 冲刺档 | <100 GB | 600 GB | 64-128 GB | 2-4 x A100 40/80 GB | 多 seed/fold、小型 set residual、2-3 模型集成 | 100-250 A100-hours |
| 不建议 | TB 级 | 多 TB | 320 GB+ | 16 A800、32 H100 或 64-128 H200 | Lingshu/SE-600M/X-Cell 从头预训练 | 与当前增益证据不匹配 |

`[工程预算]` Arc 的 162M 参数 VCC STATE Colab 在单张 T4 上约 1.25 step/s，40k steps 约 9 小时；因此推荐档按 5-8 个训练/消融 run 加失败余量估算。当前 8 GiB GPU 可运行小型 PCA-MLP 和生成器，但默认 STATE batch 是否能放下未经实测，不把它列为正式训练资源。STATE 要求 Python `<3.13`，应使用独立 Python 3.12 环境，不修改本项目的 Python 3.13 环境。

若需要金额上限而不是 GPU-hours，推荐档可先按 **人民币 1,500-5,000 元**预留云 GPU、64 GB host 和失败重跑；冲刺档按 **8,000-30,000 元**设审批门。这只是跨供应商的采购量级，不是报价，实际先用 2,000-step pilot 的吞吐回算。

## 2. 公共训练数据的实际容量

### 2.1 原作者文件：证据上限，不是推荐下载单

| 数据 | 建议下载文件 | 精确下载字节 | GiB | 公开细胞规模 | 格式 / raw 状态 | 许可入口 |
|---|---|---:|---:|---|---|---|
| VC2025 H1 | `train/adata_Training.h5ad` | 15,482,497,461 | 14.419 | 当前对象 221,273 rows（183,097 perturbed + 38,176 NTC）x 18,080 genes | H5AD；官方称 count matrices | GCP Marketplace；仓库未给 dataset-specific license，训练前需确认条款 |
| VC2025 H1 | `validation/adata_Validation.h5ad` | 6,928,967,541 | 6.453 | 当前对象 60,751 perturbed rows x 18,080 genes | H5AD | 同上 |
| VC2025 H1 | `test/adata_Test.h5ad` | 11,950,739,168 | 11.130 | 当前对象 132,670 perturbed rows x 18,080 genes | H5AD | 同上 |
| Replogle K562 genome-wide | `K562_gwps_raw_singlecell_01.h5ad` | 65,830,941,948 | 61.310 | >2.5M cells 总体中的主体；11,258 detected constructs，过滤后 mean 183 cells/construct | raw single-cell H5AD；只保留 mean >0.01 UMI/cell genes | Figshare CC BY 4.0 |
| Replogle K562 essential | `K562_essential_raw_singlecell_01.h5ad` | 10,661,879,995 | 9.930 | 2,285 detected constructs，mean 148 cells/construct | raw single-cell H5AD | Figshare CC BY 4.0 |
| Replogle RPE1 essential | `rpe1_raw_singlecell_01.h5ad` | 8,700,873,216 | 8.103 | 2,679 detected constructs，mean 101 cells/construct | raw single-cell H5AD | Figshare CC BY 4.0 |
| Nadig HepG2 | `GSE264667_hepg2_raw_singlecell_01.h5ad` | 5,614,460,941 | 5.229 | 145,473 cells x 9,624 genes；common-essential CRISPRi | raw single-cell H5AD | GEO `GSE264667`；记录未暴露 SPDX |
| Nadig Jurkat | `GSE264667_jurkat_raw_singlecell_01.h5ad` | 9,366,490,264 | 8.722 | 262,956 cells x 8,882 genes；common-essential CRISPRi | raw single-cell H5AD | GEO `GSE264667`；记录未暴露 SPDX |
| Jiang 六细胞系 | 5 个 pathway `Seurat_object_*_Perturb_seq.rds` | 20,141,612,637 | 18.758 | 约 2.6M cells、>1,500 perturbations、6 cell lines、5 signaling contexts | Seurat RDS；5 个 pathway 对象，不是每细胞系一个文件 | Zenodo CC BY 4.0 |
| Jiang 全记录 | 上述 RDS + DE zip + bulk object + metadata | 20,469,499,781 | 19.064 | 同上 | RDS/ZIP/PDF/TXT | Zenodo CC BY 4.0 |

原作者单细胞文件的核心下载量为：

| 组成 | Bytes | GB | GiB |
|---|---:|---:|---:|
| H1 三个 processed H5AD | 34,362,204,170 | 34.362 | 32.002 |
| Replogle 三个 raw single-cell H5AD | 85,193,695,159 | 85.194 | 79.343 |
| Nadig 两个 raw single-cell H5AD | 14,980,951,205 | 14.981 | 13.953 |
| Jiang 五个 Perturb-seq RDS | 20,141,612,637 | 20.142 | 18.758 |
| **作者原件上限合计** | **154,678,463,171** | **154.678** | **144.056** |
| 若下载 Jiang Zenodo 全记录 | **155,006,350,315** | **155.006** | **144.361** |

这约 155 GB 是“全部保留作者 processed 原件”的上限路径，不是推荐路径。它不包含 H1 FASTQ、SRA reads、GEO 原始测序文件，也不重复下载 Replogle 的 normalized single-cell 副本。推荐首周使用下文已核验的 scPerturb gzip raw-count 副本，把 Replogle+Nadig 从约 100.2 GB 降到约 13.7 GB；影响最终判断的异常再回到作者文件复核。

### 2.2 H1：只取 processed H5AD，不取 FASTQ

Arc 作者仓库说明 H1 为 H1 hESC，格式是 H5AD count matrices 与 Parquet/CSV metadata，概述写作约 300,000 cells / 300 targets；对象位于 `gs://arc-institute-virtual-cell-atlas/virtual-cell-challenge/2025/`。[Arc Virtual Cell Atlas README](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/virtual-cell-challenge/README.md)

当前公开对象实际共有 414,694 rows：train 221,273（含 38,176 NTC）、validation 60,751、test 132,670；这与 README 的“约 300,000”概述不一致，可能是赛后重发布或过滤口径变化，使用时必须固定 object generation/checksum。三个 split 的 targets 为 150/50/100。H1 `gene_names.csv` 有 18,080 genes；与当前 VC2026 18,533-gene axis 的本地集合核对为交集 18,077、H1-only 3、VC2026-only 456。H1 只能作为部分共享基因的 effect/count calibration 数据，456 个 VC2026-only genes 必须由其他来源或目标 NTC 补全，不能把缺失值写成生物学 0。

GCS JSON object API 的 2025 prefix 当前列出：

- processed H5AD 合计 34,362,204,170 bytes（32.002 GiB）；
- FASTQ 合计 5,810,226,748,327 bytes（5.810 TB / 5.284 TiB）；
- 整个 prefix 合计 5,844,589,074,216 bytes。

训练本方案不需要重新比对 Flex reads，下载 FASTQ 会把 34 GB 任务无收益地放大到约 5.8 TB。Marketplace bucket 是 Requester Pays；官方仓库写明只有订阅同一项目后才有每月最多 2 TB 的免费额度。[对象 API](https://storage.googleapis.com/storage/v1/b/arc-institute-virtual-cell-atlas/o?prefix=virtual-cell-challenge%2F2025%2F&maxResults=1000)；[访问说明](https://github.com/ArcInstitute/arc-virtual-cell-atlas#accessing-the-data)

### 2.3 Replogle：不要同时下载 raw 和 normalized 单细胞副本

Figshare API 为 12 个 H5AD（3 experiments x raw/normalized x single-cell/pseudobulk）返回精确字节和 MD5。原作者说明：raw single-cell 文件只保留平均表达超过 0.01 UMI/cell 的基因；`obs` 是细胞、`var` 是基因。训练时只需三个 raw single-cell H5AD，并自行派生 pseudobulk；normalized 单细胞文件几乎再复制一次 85 GB。[Figshare API](https://api.figshare.com/v2/articles/20029387)；[数据页](https://plus.figshare.com/articles/dataset/20029387)；[原论文全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC9380471/)

论文报告筛选后超过 2.5M 个高质量细胞；补充图给出三个实验的 construct coverage：K562 GWPS 11,258 x mean 183、K562 essential 2,285 x mean 148、RPE1 2,679 x mean 101。对 K562 GWPS 的 range-only HDF5 核验得到精确形状 1,989,578 x 8,248；另外两个文件未完成相同核验，因此不能用 coverage 乘积冒充精确 `n_obs`。

### 2.4 Nadig：官网的 5.2/8.7 实际是 GiB 数字

原论文 Data Availability 指向 SRA `PRJNA1100571` 和 GEO `GSE264667`；Arc 数据页直接链接两个 raw single-cell H5AD。[Nadig et al.](https://www.nature.com/articles/s41588-025-02169-3#data-availability)；[Arc 官方数据页](../Official-website/About-the-Data.md#nadig等2025)

NCBI 的默认 WSL Fake-IP 路由持续 TLS 失败；通过官方主机名和 NCBI 实际 IP 的 `--resolve` 做只读 HEAD/range 核验后，GEO 原件为：HepG2 5,614,460,941 bytes、145,473 x 9,624；Jurkat 9,366,490,264 bytes、262,956 x 8,882。两个 `.X` 都是 HDF5 Dataset 而不是 CSR group，ETL 必须分块转稀疏，不能直接全量 concat。Arc 页面标注的“5.2 GB / 8.7 GB”数值实为 GiB 四舍五入。[GEO HepG2](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE264nnn/GSE264667/suppl/GSE264667_hepg2_raw_singlecell_01.h5ad)；[GEO Jurkat](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE264nnn/GSE264667/suppl/GSE264667_jurkat_raw_singlecell_01.h5ad)

STATE 作者 HF mirror 的两个文件分别大 163,057 和 285,804 bytes，因此 mirror 可作便利副本，但 checksum manifest 必须以选定来源为准，不能把 mirror 和 GEO 原件视为字节相同。

STATE 论文在应用 on-target knockdown 过滤后，把 Replogle K562/RPE1 与 Nadig HepG2/Jurkat 合并为 624,158 cells、1,677 perturbations、4 contexts；这是一个可复现的**模型输入规模**，不是两个 GEO 文件的原始 `n_obs`。[STATE 原文](https://doi.org/10.1101/2025.06.26.661135)

### 2.5 Jiang：20.47 GB 是五个 pathway 对象

Zenodo API 返回 CC BY 4.0 和每文件精确字节：

| 文件 | Bytes | GiB |
|---|---:|---:|
| `Seurat_object_IFNB_Perturb_seq.rds` | 4,326,548,669 | 4.029 |
| `Seurat_object_IFNG_Perturb_seq.rds` | 2,915,636,149 | 2.715 |
| `Seurat_object_TNFA_Perturb_seq.rds` | 4,656,209,976 | 4.336 |
| `Seurat_object_TGFB_Perturb_seq.rds` | 2,642,041,433 | 2.460 |
| `Seurat_object_INS_Perturb_seq.rds` | 5,601,176,410 | 5.216 |

论文报告约 2.6M cells、>1,500 perturbations、6 cell lines、5 pathways（30 biological contexts）；两个 replicates 构成 60 samples，每 pathway 约 44-61 targets、每 target 3 sgRNA，另有 14 NTC。它仍没有给出五个最终 RDS 各自的精确 cell count。原始 reads 在 GEO `GSE281048`，处理后对象在 Zenodo；本方案只需要处理后 Seurat objects。[Zenodo API](https://zenodo.org/api/records/14518762)；[Jiang et al.](https://www.nature.com/articles/s41556-025-01622-z)；[Data Availability](https://www.nature.com/articles/s41556-025-01622-z#data-availability)

### 2.6 推荐下载单：压缩 raw-count 副本 + 分阶段扩容

scPerturb Zenodo `13350497` 提供 gzip-compressed H5AD，记录许可为 CC BY 4.0。相关五个副本为：K562 GWPS 8.805 GB、K562 essential 1.547 GB、RPE1 1.237 GB、HepG2 0.851 GB、Jurkat 1.294 GB，总计 13.734 GB。[scPerturb Zenodo](https://zenodo.org/records/13350497)

对 Replogle，固定 commit `b69f72a` 的转换代码直接读取 `*_raw_singlecell_01.h5ad`，保留 `adata.X`，只统一 metadata、处理四个重复 symbol 并以 gzip 写 H5AD；没有 normalization、`log1p` 或 cell/gene subsetting。参赛者公开的 HTTP Range 审计还报告 K562 GWPS 两个版本具有相同的 1,989,578 x 8,248 matrix，三行抽查相等。前者是一手代码事实，后者是需下载后复核的参赛者证据。[scPerturb transform](https://github.com/sanderlab/scPerturb/blob/b69f72a070a92bcbaf41e7f9897b11598109ab48/dataset_processing/scripts/ReplogleWeissman2022.py)

| 批次 | 内容 | 下载量 | 作用 |
|---|---|---:|---|
| Phase 1 | 当前 controls、STATE support ZIP、K562 GWPS、四背景 transfer core、HPA v25.1 | **约 23.3 GB** | STATE starter、direct target memory、2,054-target context transfer、soft context matching |
| Phase 2 | Phase 1 + Jiang 五个 RDS | **约 43.5 GB** | 增加 6 个癌细胞系和 epithelial context diversity |
| Author audit | H1/Replogle/Nadig 作者原件，按异常选择性下载 | **最多约 69-155 GB** | 复核 harmonization、Flex count calibration；不作为首周前置条件 |

STATE support ZIP 本身为 8.717 GB，central directory 显示完全解压为 48.691 GB；它包含 H1 train/val/test templates、筛选后的外部 H5、ESM2 features 和 starter config。使用它时不要再无条件下载相同 H1 三个 GCS H5AD。

## 3. 工作空间、RAM 和下载时间

### 3.1 磁盘

推荐路径按以下方式预留；原作者 155 GB 全量路径只在审计需要时启用：

| 层 | 规划空间 |
|---|---:|
| Phase 1/2 source + STATE 解压 | 65-90 GB |
| canonical metadata、pseudobulk、HVG/PCA/DE cache | 10-30 GB |
| 5-8 个 run 的 checkpoint/log | 20-50 GB |
| 2-3 个 H5AD/VCC、打包临时副本 | 30-60 GB |
| 安全余量与 Jiang 转换 | 80-120 GB |
| **建议工作盘** | **120 GB 最低；300 GB 推荐；600 GB 冲刺** |

当前 892 GiB 可用盘足够推荐档。任何路径都不下载 H1 FASTQ 或 GEO/SRA reads；若决定长期保留全部作者原件和多个 canonical 副本，再升级到 1 TB 以上专用 NVMe。

作者的 2025 STATE support zip 给出一个现实膨胀例：远端 ZIP 为 8,716,992,349 bytes，而 ZIP central directory 中成员解压和为 48,691,267,232 bytes，约 5.59x；因此“下载只有几 GB”不能当作工作空间需求。[support zip](https://storage.googleapis.com/vcc_data_prod/datasets/state/competition_support_set.zip)

### 3.2 主机内存

- **当前 15 GiB 可做：** backed/chunked 审计、pseudobulk、Ridge、分块生成；禁止把 K562 dense payload 或多个 context `.to_memory()`。
- **32 GB 最低竞争档：** 可以更稳定地完成 scPerturb ETL、response PCA、生成和普通离线评分。
- **64 GB 推荐：** 允许 Jiang 转换、更多 DE cache 和 candidate 比较；也匹配 `cell-eval2` out-of-core 示例的 host budget。
- **128 GB 只在作者全量转换或大量并行 scoring 时需要。** 它不是统计主线的启动条件。
- **不建议一次 `anndata.concat` 全部原始文件。** STATE 作者 Colab明确标注 Replogle-Nadig concat/HVG 为 memory intensive，需 high-memory runtime；这仍只是四个数据集和 2,000 HVG。[作者 Colab](https://colab.research.google.com/drive/1Ih-KtTEsPqDQnjTh6etVv_f-gRAA86ZN)

### 3.3 网络

Phase 1 的 23.3 GB 在理想 100 Mbps 下界约 31 分钟，Phase 2 的 43.5 GB 约 58 分钟；实际由仓库限速决定，按 STATE Colab公开日志约 7-8 MB/s，应分别预算约 1-2 小时和 2-4 小时，并为断点续传留余量。GCS Requester Pays 和月度免费额度需要在下载前配置。

## 4. 模型公开算力证据

### 4.1 统计 delta / Ridge

公开论文并未为这类模型给 GPU 配置，因为核心是 pseudobulk aggregation、PCA/Ridge 和经验贝叶斯收缩。当前 20-thread CPU 配合 backed H5AD 足以启动；训练矩阵降到 128-256 response PCs 后，单 fold 预算 0.25-2 小时。全数据 pseudobulk/DE 预计算一次预算 4-12 CPU-hours，GPU 只用于可选 DE/矩阵加速。

### 4.2 小型 set encoder

推荐配置是本项目工程假设，不是论文已证明的最优值：

- 2,000 HVG 输入，set size 64；
- hidden 256-384，3-4 个 attention block；
- 低秩 full-gene decoder，总计约 10M-30M parameters；
- bf16，单卡 batch 8-32 sets，必要时 gradient accumulation；
- 当前 8 GB GPU 可做缩小 batch 的 pilot，16-24 GB 足以训练该模型；48 GB 不是启动条件。

`[规划估算]` 单 fold 在本机 RTX/T4 约 2-6 GPU-hours；只在 Ridge 和 STATE 之后仍有稳定残差时运行 3-5 个 fold/seed，总计 10-30 GPU-hours。必须用 2k-step pilot 修订，不能把这个数字写成论文事实。

### 4.3 STATE

存在三种不同容量，不能混为一个“STATE 模型”：

| 证据 | 配置 | 硬件 / 时长 |
|---|---|---|
| STATE 论文 ST on Replogle-Nadig | 624,158 cells；2,000 HVG；set 32；hidden 128；4 encoder + 4 decoder；GPT2 backbone | 论文未披露 ST GPU 数和 wall time：`unknown` |
| STATE 作者 Replogle-Nadig Colab | T4 high-memory；80k steps；batch 64；set 64；hidden 328 | notebook 可在单 T4 配置，未保存完整训练日志：wall time `unknown` |
| STATE 作者 VC2025 Colab | H1 + public support；40k steps；当前模型 162M total / 141M trainable，estimated parameter size 0.61 GB | 单 T4；公开日志约 1.25 step/s，40k 外推约 9 h |
| STATE SE paper pretraining | 600M parameters；167M cells；4 epochs；bf16；effective batch 3,072 | 4 nodes x 8 H100；wall time未披露 |

来源：[STATE paper](https://doi.org/10.1101/2025.06.26.661135)；[官方 README](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/README.md)；[model config](https://github.com/ArcInstitute/state/blob/main/src/state/configs/model/state.yaml)；[Replogle-Nadig Colab](https://colab.research.google.com/drive/1Ih-KtTEsPqDQnjTh6etVv_f-gRAA86ZN)；[VCC Colab](https://colab.research.google.com/drive/1QKOtYP7bMpdgDJEipDxaJqOchv7oQ-_l)

结论：比赛应训练 ST 或较小 residual set encoder，**不应从头训练 SE-600M**。先跑 1 个 40k-step starter（约 9 T4-hours），再运行 4-7 个真正有独立假设的 fold/消融；含失败余量，STATE 路线预留 50-80 T4-hours。嵌套验证的大部分组合由廉价 Ridge 完成，不为每个超参数重训 STATE。

### 4.4 Stack

Stack 的公开容量最完整：

- Stack-Large 为 217M parameters；checkpoint `bc_large.ckpt` 2,610,004,146 bytes，aligned checkpoint 2,613,863,242 bytes；
- 预训练数据 148.8M human scBaseCount cells，10 epochs，set 256，batch 32，bf16；
- 作者报告单张 H100 80GB + 320GB host RAM，2-3 天完成预训练，即约 48-72 H100-hours；
- alignment 使用 CELLxGENE 45M + Parse 10M，8 epochs，set 512，batch 8 x grad accumulation 4；单张 H100 80GB + 400GB host RAM；wall time未披露；
- 官方 README 仅保证在 H100 80GB 测试；更小显存上的 full generation 尚未核验。

来源：[Stack paper](https://doi.org/10.64898/2026.01.09.698608)；[官方 README](https://github.com/ArcInstitute/stack/blob/cacc2e4b09435c3e536d46237d10b50f222dd144/README.md)；[training config](https://github.com/ArcInstitute/stack/blob/main/configs/training/bc_large.yaml)；[finetuning config](https://github.com/ArcInstitute/stack/blob/main/configs/finetuning/ft_parsecg.yaml)；[Stack-Large card/API](https://huggingface.co/arcinstitute/Stack-Large)；[aligned card/API](https://huggingface.co/arcinstitute/Stack-Large-Aligned)

算力不是当前首要阻塞。代码为 CC BY-NC-SA 4.0，模型许可把直接或间接 monetary compensation 排除在 Non-Commercial Purpose 外；在奖金赛中应先取得书面许可，再决定是否花 80GB GPU 预算。[Stack model license](https://github.com/ArcInstitute/stack/blob/main/MODEL_LICENSE.md)

## 5. VC2025 获奖方案：能迁移什么，算力哪里未知

Arc 官方 wrap-up 是目前四个获奖方案唯一一致的一手公开说明；第一名和第三名的完整论文仍写作 forthcoming，未找到团队公开训练仓库。因此不能根据架构名猜参数或 GPU。[Arc VC2025 wrap-up](https://arcinstitute.org/news/virtual-cell-challenge-2025-wrap-up)

| 方案 | 官方披露的数据 / 模型 | 参数、GPU、时长 | 2026 可迁移 | 不能直接迁移 |
|---|---|---|---|---|
| 冠军 BM_xTVC / xTrimoSCPerturb | 改进 scFoundation + protein embeddings + 官网公共 perturbation 子集；DEG frequency、mean expression；pseudobulk；PDS+DES+小权重 MAE | 全部 `unknown`；论文未发布 | 多模态 target prior、统计特征、metric-aware loss | 重复 pseudobulk 不能代表 400-cell raw-count distribution；H1 内验证不证明新 context |
| 亚军 XLearning / X | 全连接网络；aggregated control、ESM-2、UMI indicator；residual delta；只用公共 Perturb-seq，含 PerturbAtlas 小型 H1 | 全部 `unknown` | residual delta、轻量 MLP、UMI/depth features | 2026 没有目标背景 perturbation，且要六项指标和 raw counts |
| 季军 Outlier / TransPert | 仅 pseudobulk 与 Wilcoxon summary；跨 cell-line similarity aggregation；global linear PDS scaling；只用公共数据 | 全部 `unknown`；manuscript forthcoming | 是本项目统计主锚的直接先例 | 2026 PDS 改为 cosine，纯正比例缩放不再改变方向排名；单细胞 DE/采样方差仍需生成器 |
| Generalist Altos / go-with-the-flow | gene-space flow matching + custom U-Net；约 7M public/challenge/internal cells；再 fine-tune H1 和 test targets | 全部 `unknown`；内部数据不可复现 | 生成 heterogeneous cells、多指标选择 | 最关键 fine-tuning 使用目标 H1 perturbations；2026 D/E/F 不提供，不能复用这一监督条件 |

本方案刻意选择了低算力、证据最强的组合：用亚军的 `residual delta + ESM2 + UMI/depth`，叠加季军的 `pseudobulk/Wilcoxon + cell-line similarity`，再以当前可运行的 STATE 作全基因基线。冠军的改进 scFoundation 和 Generalist 的 flow matching 只保留为后期参考，因为公开资料没有足够的复现合同或算力披露。

2025 到 2026 的三个合同变化决定了迁移边界：

1. 2025 是单 H1 context 且有 H1 perturbation training；2026 是匿名新 context zero-shot。
2. 2025 PDS 使用 L1，缩放可以获益；2026 PDS 使用 cosine 且移除 target panel，六项 scaled metrics 等权。
3. 2026 必须生成全 18,533-gene raw integer counts、每 target/context 400 cells；复制 pseudobulk 会丢失 Wilcoxon、DE set 和 sampling-variance 信息。

## 6. 最终输出的存储与内存下界

### 6.1 官方形状和稀疏上限

官方合同给出：

- rows = `3 contexts x 300 targets x 400 cells = 360,000`；
- columns = 18,533 genes；
- dense logical entries = `360,000 x 18,533 = 6,671,880,000`；
- sparse stored-item cap = 4,750,000,000；
- 真实实验约 5,800 nnz/cell，即约 2,088,000,000 nnz；
- dense matrix 本身是 cap 的 1.40x，必定拒绝。

来源：[官方 FAQ：稀疏度](../Official-website/FAQs.md#我的提交文件很小为什么仍因过于稠密而被拒绝)；[提交格式](../Official-website/About-the-Data.md#提交文件)

### 6.2 逻辑 CSR 内存

若采用常见的 `int32 data + int32 column indices + int64 indptr`：

```text
RAM_CSR ~= nnz * (4 + 4) + (n_rows + 1) * 8
```

在官方典型 2.088B nnz 下，仅三个 CSR arrays 就约 16.707 GB（15.56 GiB）；还没有计入 AnnData/HDF5 buffers、`obs/var`、生成 batch、复制和压缩。若达到 4.75B stored items，三个数组约 38.0 GB。因此**不能全量 materialize**。分块生成在当前 15 GiB 主机可行；若必须全量持有才需要 32-48 GB。`cell-eval2` 官方 out-of-core 示例采用 64 GiB host + 40 GiB GPU budget，推荐把完整 metric-faithful surrogate scoring 放在 A100 40 GB/64 GB RAM 的短时云任务上，本机只跑分区和开发集。[cell-eval2 out-of-core](https://github.com/ArcInstitute/cell-eval2#out-of-core-scoring)

### 6.3 本机生成微基准

`[本仓库实测，2026-08-30]` 用 4,000 cells / 10 targets 的 raw-count CSR chunk 得到：

- 23,772,026 nnz；
- gzip H5AD 47,878,505 bytes；
- write 9.916 s；
- peak RSS 1,362.5 MiB。

线性外推 90 chunks 对应完整 360,000 cells：约 2.139B nnz、4.31 GB gzip H5AD、逻辑 CSR 约 17.1 GB。考虑 merge、HDF5 metadata、模型输出和 IO 抖动，最终生成/写入规划为 20-60 分钟、每 candidate 20 GB 临时盘；保留 3 个 candidate 和打包复核建议 50-100 GB。该外推是容量基准，不是最终文件大小保证；count decoder 改变稀疏度后必须重跑。

实现要求是按 `(context,target)` 或 10-target shard 生成，立即去除显式零并写盘，绝不先构造 6.67B-entry dense array。

## 7. 当前排行榜只支持“小步胜过 STATE”，不支持盲目扩模

官方 leaderboard API 在核查时有 472 entries，panel `vcc2026-val-1`、anchor `r4`；top overall 为 0.2112235，名为 `STATE baseline` 的 entry 为 0.1894249。top 相对该 entry 的 scaled metric 差是：PDS +0.00289、MSE +0.01939、NMAE +0.04633、FID +0.01544、reach +0.05497、JAC -0.00823。[官方 leaderboard API](https://virtualcellchallenge.org/api/leaderboard)

| entry | overall | PDS | MSE | NMAE | FID | reach | JAC |
|---|---:|---:|---:|---:|---:|---:|---:|
| rank 1 `GeroAI_v12` | 0.2112 | 0.7089 | 0.1693 | 0.1838 | 0.0030 | 0.2066 | -0.0042 |
| rank 2 `STATE baseline` | 0.1894 | 0.7060 | 0.1499 | 0.1374 | -0.0125 | 0.1516 | 0.0040 |
| rank 1 - rank 2 | **+0.0218** | +0.0029 | +0.0194 | **+0.0463** | +0.0154 | **+0.0550** | -0.0082 |

前 50 名中 overall 与各 scaled metric 的描述性相关依次为 PDS 0.659、NMAE 0.607、reach 0.452、FID 0.386、MSE 0.383、JAC 0.091。它们是反复提交后的相关性，不是因果效应；但结合 rank 1/2 差值，实验优先级应是：**保住 PDS -> 校准 NMAE/reach/MSE -> 再尝试 FID -> JAC 最后**。rank 3 的 toy model 有最高 PDS 0.7559，却因 MSE=0 只排到 overall 0.1842，进一步说明不能只优化方向排名。

这是动态快照，且 entry name 是提交者标签，不证明其代码或配置。公开榜目标分可设为：先得到 `>=0.18` 的 STATE 复现，再以 `>=0.20` 作为竞争门，`>=0.21` 作为当前 leader 区间；这些只用于 A/B/C 外部校准，不保证 D/E/F。

候选相对 STATE 的上线门建议冻结为：PDS 不下降超过 0.01；`MSE + NMAE + reach` 的 scaled 总增益至少 0.08；任何单 context 不崩溃。JAC/FID 只有在不牺牲前三项时才进入集成权重。

### 7.1 参赛者经验贴能用到什么

Forrest Sheldon 的公开文章和 MIT 仓库提供了可复查的工程观察，不是官方真值：[文章](https://forrestsheldon.github.io/virtual-cell/posts/2026-08-29-exploring-the-data-i/)；[代码](https://github.com/forrestsheldon/virtual-cell-challenge-2026)。

- construct-balanced control resampling 在官方 API 当前为 rank 394、overall -0.3037，主要被 FID -1.7214 拉低。它只保留作 evaluator sanity test，不值得调参。
- 5,000 cells/context 的 UMAP 分出三个背景，B 还有低-UMI satellite；生成器应按状态/`ntc_id` 分层，是否过滤 satellite 必须由公共 truth 消融决定。
- HPA v25.1 的 3,000-variable-gene Spearman 分别把 A/B/C 首位匹配为 Jurkat E6.1、HeLa、CAL-33。这只能作为 soft retrieval feature；不能硬编码身份。若 A 的假设成立，Nadig Jurkat 是高价值 same-line calibration，因此优先下载并不亏。
- 该仓库的 target 清单与当前 300 targets 复算得到 K562 GWPS 272 个重叠、H1 13、Jiang 9、McFaline 23；K562/RPE1/HepG2/Jurkat 四方 common-essential 交集为 2,054。下载后必须从原 H5AD/RDS 再生成清单，不能把参赛者派生 CSV 当权威数据。
- 其 `10 targets -> gzip shard -> anndata.experimental.concat_on_disk` 模式与本机 1.36 GiB peak-RSS 微基准一致，适合作为低内存提交构建模式；复用代码时保留 MIT attribution。

## 8. 可执行排期与资源门

| 阶段 | 产物 | CPU/GPU 预算 | 晋级门 |
|---|---|---:|---|
| E0-E1，2-3 天 | evaluator wrapper、null baseline、格式/稀疏破坏测试 | CPU；0 GPU-h | 六指标与 `vcc prep --dry-run` 可复现 |
| 数据 ETL，3-5 天 | Phase 1 的 canonical metadata、pseudobulk、许可表、split audit | 当前 CPU；0 GPU-h | 23.3 GB source 可流式处理；无跨 study/context 泄漏 |
| E2 Ridge/delta，3-5 天 | global/weighted/Ridge/empirical-Bayes baselines | CPU；0-10 GPU-h | 双重留出稳定胜 NTC null |
| E3 STATE starter，2-3 天 | 40k-step baseline、2026 gene adapter | 10-20 T4 GPU-h | 离线 LOCO 合理；公开校准目标 >=0.18 |
| E4 scale + count，3-5 天 | direction/norm heads、400-cell raw-count sampler | CPU + 本机 GPU；10-20 GPU-h | PDS 守门，MSE/NMAE/reach 总增益 >=0.08 |
| E5 residual，3-5 天 | 可选 small set residual，3-5 fold/seed | 10-30 GPU-h | 平均和 worst-context 都胜 Ridge/STATE；否则删除 |
| ensemble/final，3-5 天 | 2-3 frozen candidates、full scoring、rehearsal | 10-20 T4-h + 10-20 A100-h | 360k 输出、稀疏度、内存和打包全部通过 |

建议总预算为 **60-100 T4 GPU-hours**，或把训练/完整评分拆成约 **20-40 A100 GPU-hours**；另留 30% 失败余量。只有 E5 显示稳定增益时才扩大到 100-250 A100-hours 的冲刺档。Stack 不在默认预算内，许可解决后另开独立资源项。

## 9. 失败、unknown 和未解决缺口

本次不把无法核验的项填成估算事实：

- NCBI 默认 WSL Fake-IP 路径返回 `SSL_ERROR_SYSCALL`；通过官方主机名 + NCBI 实际 IP 的只读 `--resolve` 才完成 Nadig HEAD/range 核验。自动下载脚本必须显式处理该网络问题。
- H1 当前公开对象是 414,694 rows，而 README 仍写约 300,000 cells；原因 unknown，必须固定 object generation 和实际 shape。
- Arc Virtual Cell Atlas 仓库没有 dataset-specific LICENSE 文件；H1 的明确再利用许可证仍需从 Marketplace subscription terms 核验。
- Jiang Zenodo 给出精确下载字节和 CC BY 4.0，但 RDS 的精确 cell count、nnz、加载后 RAM 与 GEO raw 总量 unknown；需下载后用 Seurat metadata 审计。
- STATE 论文披露 SE 为 32 H100，但没有披露 ST 的 GPU 数或 wall time；本文只把作者 T4 Colab作为可运行锚点。
- Stack 披露预训练 2-3 天和 alignment 硬件，未披露 alignment wall time；小于 80GB GPU 的正式 inference capacity unknown。
- VC2025 四个获奖方案均未公开足以核验的参数量、GPU、训练时长；第一/第三名完整方法仍为 forthcoming。
- 最终 `.vcc` 大小取决于数据稀疏度和 packer 压缩；4.31 GB 是本机 H5AD 微基准外推，不是官方保证。

## 10. 一手来源台账

- Arc 2026：[About the Data](../Official-website/About-the-Data.md)；[FAQ](../Official-website/FAQs.md)；[live leaderboard API](https://virtualcellchallenge.org/api/leaderboard)。
- Arc 2025：[winner wrap-up](https://arcinstitute.org/news/virtual-cell-challenge-2025-wrap-up)。
- H1：[Arc Virtual Cell Atlas VCC README](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/virtual-cell-challenge/README.md)；[GCS object metadata](https://storage.googleapis.com/storage/v1/b/arc-institute-virtual-cell-atlas/o?prefix=virtual-cell-challenge%2F2025%2F&maxResults=1000)。
- Replogle：[Cell paper](https://doi.org/10.1016/j.cell.2022.05.013)；[PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC9380471/)；[Figshare record/API](https://api.figshare.com/v2/articles/20029387)。
- Nadig：[Nature Genetics paper](https://doi.org/10.1038/s41588-025-02169-3)；[GEO GSE264667](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE264667)；[STATE author mirror](https://huggingface.co/datasets/arcinstitute/Replogle-Nadig-Preprint)。
- Jiang：[Nature Cell Biology paper](https://doi.org/10.1038/s41556-025-01622-z)；[Zenodo record/API](https://zenodo.org/api/records/14518762)；[GEO GSE281048](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE281048)。
- STATE：[paper](https://doi.org/10.1101/2025.06.26.661135)；[official code](https://github.com/ArcInstitute/state)；[Replogle-Nadig Colab](https://colab.research.google.com/drive/1Ih-KtTEsPqDQnjTh6etVv_f-gRAA86ZN)；[VCC Colab](https://colab.research.google.com/drive/1QKOtYP7bMpdgDJEipDxaJqOchv7oQ-_l)。
- Stack：[paper](https://doi.org/10.64898/2026.01.09.698608)；[official code](https://github.com/ArcInstitute/stack)；[Stack-Large](https://huggingface.co/arcinstitute/Stack-Large)；[Stack-Large-Aligned](https://huggingface.co/arcinstitute/Stack-Large-Aligned)。
- 参赛者工程证据：[Forrest Sheldon blog](https://forrestsheldon.github.io/virtual-cell/posts/2026-08-29-exploring-the-data-i/)；[MIT repository](https://github.com/forrestsheldon/virtual-cell-challenge-2026)。
- 推荐 harmonized raw-count 副本：[scPerturb Zenodo](https://zenodo.org/records/13350497)；[Replogle transform source](https://github.com/sanderlab/scPerturb/blob/b69f72a070a92bcbaf41e7f9897b11598109ab48/dataset_processing/scripts/ReplogleWeissman2022.py)。

检索台账：数据集、STATE 和 Stack 均沿比赛官方页给出的确定 DOI/仓库入口做一手 API/全文核验。为检查 VC2025 获奖方法是否已有后续论文，Infra Scholar 顺序调用 1 次，查询为 `Arc Virtual Cell Challenge 2025 xTrimoSCPerturb TransPert go-with-the-flow`，未命中可核验的方法论文；GitHub exact repository 查询 2 次也未发现四个团队的一手仓库。因此获奖方案参数/算力保持 `unknown`，不能把未命中写成“从未公开”。
