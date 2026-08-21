本页面介绍2026年挑战赛背后的数据——您将收到什么、数据结构如何，以及您的预测结果必须采用的格式。
## 挑战赛数据集
### Arc研究所新生成的挑战赛数据集

为2026年挑战赛，我们在六种来源于不同组织的细胞系上进行了Perturb-seq实验，使用CRISPRi和10x Flex单细胞RNA测序。

这六种细胞系分为两组，每组三种：三种细胞系用于验证轮，另外三种不同的细胞系保留作为最终测试。每种细胞系仅以匿名细胞背景（cell context）发布——验证轮标记为A、B、C，最终测试标记为D、E、F。我们不会公开每个背景对应哪种细胞系。您收到的将是该背景的未扰动表达谱，这是您的模型唯一需要依赖的信息。

今年没有挑战赛训练集。任务为零样本（zero-shot）：给定表达非靶向向导RNA的细胞的表达谱，加上待预测的CRISPRi敲低靶标基因标识符，您的模型必须预测CRISPRi敲低后、经10x Flex单细胞测序所得到的扰动后表达谱。您可以自由使用为2025年挑战赛发布的H1 hESC数据，以及任何您有权使用的公共或专有数据——有关我们推荐的公共数据集，请参见下面的Arc虚拟细胞图谱。

![alt text](./assets/About-the-Data-image01.png)

---

### 2026年挑战赛数据：一个验证数据集和一个测试数据集，各包含三种细胞系，每种细胞系有300个扰动，每个扰动400个细胞

参赛者将收到：

- **验证集**（2026年8月20日发布）：背景A、B、C的非靶向对照谱——每个背景18,400个对照细胞，来自46个非靶向向导，每个向导400个细胞，每个细胞中位数约20,000个UMI——以及需要在每个背景中预测的300个基因扰动列表。针对该数据集的预测结果将驱动实时排名排行榜。

- **最终测试集**（2026年10月22日发布）：三种不同细胞系的非靶向对照谱，即背景D、E、F，并附有其各自的扰动列表。

最终排名将仅基于最终测试集上的表现。

---

### 单轮数据规模

| 项目 | 详情 |
|------|------|
| 细胞背景 | 3个（验证阶段为A、B、C；最终阶段为D、E、F） |
| 扰动数 | 300个，该轮所有三个背景共享同一组扰动 |
| 每个扰动需预测的细胞数 | 400个 |
| 完整提交包含的细胞数 | 360,000（300 × 400 × 3个背景） |
| 提供的非靶向对照细胞数 | 每个背景18,400个——46个非靶向向导 × 400个细胞，以`ntc_id`标记 |
| 基因数 | 18,533 |

扰动通过基因符号（例如`ADNP`）标记。验证轮和测试轮独立评分——由于细胞系和扰动列表不同，验证分数与最终分数在绝对意义上不可直接比较。

---

## 文件格式

参赛者在注册并登录应用程序后，可从网站或使用[`vcc`命令行工具](https://vcc-cli-wiki.virtualcellchallenge.org/) 下载对照数据。测试阶段数据包于2026年10月22日开放，结构相同，对应背景D、E、F。

### 对照数据

**验证阶段数据包：`controls.zip`**  
~630 MB  
包含每个细胞背景一个对照文件，以及两个参考文件。

| 文件 | 内容 |
|------|------|
| `context_A.h5ad` | 18,400个非靶向对照细胞 × 18,533个基因，对应细胞背景A |
| `context_B.h5ad` | 同上，对应背景B |
| `context_C.h5ad` | 同上，对应背景C |
| `gene_names.csv` | 18,533个基因符号，按您的矩阵必须使用的顺序排列 |
| `pert_counts.csv` | 待预测的扰动列表 |
| `manifest.json` | 赛季、分区、面板ID、背景及各背景细胞数 |

每个对照文件均为[AnnData H5AD](https://anndata.readthedocs.io/en/stable/)格式的基因表达文件，保存原始计数（raw counts）。

**观测（Obs）**：

| 字段 | 示例 |
|------|------|
| cell index | `A_ctrl_000000`， `A_ctrl_000001`， ... |
| target_gene | `non-targeting`（所有行） |
| context | `A`（相应背景） |
| ntc_id | `non-targeting-11`， `non-targeting-11`， ... |

`ntc_id`指明对照细胞携带的是46个非靶向向导中的哪一个——每个向导有400个细胞。`target_gene`在所有行均为`non-targeting`，因此依赖该列的键值不受影响；若想建模向导间的变异，请使用`ntc_id`。

**变量（Var）**：

| 字段 |
|------|
| gene name index |
| `SAMD11` |
| `NOC2L` |
| ... |

**对照细胞仅供模型输入**  
这些文件中的每个细胞的`target_gene`值均为`non-targeting`——它们是该细胞背景的未扰动谱，用于标识该背景。**请勿**预测对照细胞的表达值；提交含有对照细胞预测结果的将被拒绝。

---

### 扰动列表

**扰动列表：`pert_counts.csv`**  
1.9 KB  
包含300行（每个扰动一行）

| 字段名 | 描述 |
|--------|------|
| target_gene | 靶向扰动的基因符号。需要在每个细胞背景中预测所有这些基因，每个基因恰好400个细胞 |

示例：
```
target_gene
ABCD1
ACLY
ADNP
AGO1
...
```

---

## 提交文件

### 您的提交：`prediction.vcc`

您需构建一个AnnData H5AD文件，保存您对所有三个背景的预测基因表达谱，然后使用`vcc prep`将其打包为单个`.vcc`文件进行上传。内部只有一个H5AD文件，而非每个背景一个——通过`context`列来区分，该列用法与对照文件完全相同。

**观测（Obs）**：

| 字段 | 示例 |
|------|------|
| target_gene | `ABCD1`， `ABCD1`， `ACLY`， ... |
| context | `A`， `B`， `A`， ... |

- 使用基因符号，而非构建ID——例如`ADNP`，而不是`ADNP-1`。
- **不包含**非靶向行：每一行都对应您被要求预测的扰动之一。您下载的对照细胞仅供模型输入——**请勿**将它们复制到您的预测文件中。

**变量（Var）**：

| 字段 |
|------|
| gene name index |
| `SAMD11` |
| `NOC2L` |
| ... |

所有18,533个基因，按`gene_names.csv`中给出的顺序排列。

**X（表达矩阵）**：

- 原始计数（raw counts）——非负整数、有限值，且每个细胞的总计数不超过1,000,000。
- 行数为360,000，列数为18,533：正好是`pert_counts.csv`中列出的扰动，每个扰动400个细胞，每个背景中都如此。
- 请以稀疏格式存储：最多约47.5亿个存储项，在此形状下约为每个细胞13,200个非零项——显式存储的零值也会计入，因此密集数组本身就超出上限。

**打包**：

```bash
vcc prep prediction.h5ad -g gene_names.csv --perts pert_counts.csv -o prediction.vcc
```

`prep`命令会在本地验证基因集、背景标签、扰动标签、细胞计数以及原始计数要求，因此问题会在几秒钟内暴露，而无需上传数GB数据。添加`--dry-run`可仅检查而不写入文件。

---

## 靶标基因选择

靶向预测的基因均具有超过80%的靶向敲低效率，并被选为能够提供强扰动和响应，以保证挑战赛的稳健性。

---

## Arc虚拟细胞图谱

您可以使用任何您有权使用的公共或专有数据来训练您的模型。我们创建了Arc虚拟细胞图谱（Arc Virtual Cell Atlas）作为一项资源。该图谱是一个高质量、经过整理、开放的数据集集合，旨在加速虚拟细胞模型的创建。图谱包含来自超过6亿个细胞的观察性和扰动性数据（且仍在增长）。

---

### [scBaseCount ↗](https://github.com/ArcInstitute/arc-virtual-cell-atlas/tree/main/scBaseCount) 

scBaseCount是一个持续更新的单细胞RNA-seq数据库，采用AI驱动的层级代理工作流，自动发现、提取元数据并对序列读取档案（SRA）数据进行标准化预处理。

目前是最大的公共单细胞数据存储库之一，包含超过5.02亿个细胞（并持续扩展），涵盖27种生物体和75种组织。

通过不断发现、注释和重新处理原始单细胞RNA-seq数据，scBaseCount提供了一个广泛且协调统一的存储库，可作为AI驱动建模和整合性元分析的基础。

---

### [Tahoe-100M ↗](https://github.com/ArcInstitute/arc-virtual-cell-atlas/tree/main/tahoe-100M)

全球最大的单细胞数据集，由Tahoe生成并开源，包含1亿个细胞，来自约60,000项药物扰动实验，绘制了50种癌症模型对1,100多种药物治疗的反应。

---

### [2025年虚拟细胞挑战赛 ↗](https://console.cloud.google.com/marketplace/product/bigquery-public-data/arc-institute?project=gcp-public-data-arc-institute)

为Arc 2025年虚拟细胞挑战赛生成的数据集，测量人类胚胎干细胞系（H1 hESC）在单细胞水平上对扰动的反应，具有深度细胞覆盖、深度测序、高靶向敲低效率，并使用与今年竞赛相同的单细胞化学方法（10x Flex）。该数据集包含挑战赛期间使用的训练、验证和保留测试扰动数据集。

---

## 公开扰动数据集

您可以使用任何您有权使用的公共数据来训练您的模型。我们很高兴看到有许多数据生成项目正在为计算建模贡献力量，也希望挑战赛能激励更多高质量参考数据集的生成。以下是一组可能有用的公开扰动数据集，除了Arc虚拟细胞图谱之外：

---

### Replogle等，2022
- [论文](https://www.cell.com/cell/fulltext/S0092-8674(22)00597-9)
- [全部数据集](https://plus.figshare.com/articles/dataset/_Mapping_information-rich_genotype-phenotype_landscapes_with_genome-scale_Perturb-seq_Replogle_et_al_2022_processed_Perturb-seq_datasets/20029387)

[**K562全基因组**（61.3 GB）](https://plus.figshare.com/ndownloader/files/35775507)  
• [K562（9.9 GB）](https://plus.figshare.com/ndownloader/files/35773219)  
• [RPE1（8.1 GB）](https://plus.figshare.com/ndownloader/files/35775606)  

使用CRISPR干扰（CRISPRi）靶向所有表达基因，覆盖超过250万个人类细胞（K562和RPE1）的全基因组规模Perturb-seq。K562全基因组数据集包含的扰动与Arc VCC训练和验证数据集中使用的大部分基因重叠。

---

### Nadig等，2025
- [论文](https://www.nature.com/articles/s41588-025-02169-3)
- [全部数据集](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE264667)

[**HepG2**（5.2 GB）](https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSE264667&format=file&file=GSE264667%5Fhepg2%5Fraw%5Fsinglecell%5F01%2Eh5ad)  
• [Jurkat（8.7 GB）](https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSE264667&format=file&file=GSE264667%5Fjurkat%5Fraw%5Fsinglecell%5F01%2Eh5ad)  

在Jurkat和HepG2细胞中针对DepMap常见必需基因进行的单细胞CRISPR筛选。

---

### Jiang等，2025
- [论文](https://www.nature.com/articles/s41556-025-01622-z)
- [数据集](https://zenodo.org/records/14518762)

在六种不同组织来源的癌细胞系中进行的Perturb-seq实验：A549（肺）、MCF7（乳腺）、HT29（结肠）、HAP1（骨髓）、BxPC3（胰腺）和K562（骨髓）。

---

### Srivatsan等，2020
- [论文](https://www.science.org/doi/10.1126/science.aax6234)
- [数据集](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE139944)

介绍了“sci-Plex”，该方法利用“核哈希”技术，在单细胞分辨率下量化数千种独立扰动的全局转录反应，并将其应用于三种癌细胞系暴露于188种化合物的筛选。

---

### McFaline-Figuero等，2024
- [论文](https://www.cell.com/cell-genomics/fulltext/S2666-979X(23)00339-7)
- [数据集](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE225775)

介绍了sci-Plex-Gene-by-Environment，一个用于大规模组合单细胞遗传和化学筛选的平台，并将其应用于胶质母细胞瘤细胞系中化学和遗传扰动的组合筛选。