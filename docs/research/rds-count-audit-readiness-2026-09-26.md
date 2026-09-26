# Jiang TGFB RDS 原始计数审计就绪说明（2026-09-26）

> 后续执行已完成：以下保留读取前的源码核验与风险估算。现已建立隔离 R 4.5.3 / Matrix 1.7.6 / jsonlite 2.0.0 环境，并在打包退出后完成完整对象审计；文中“未安装/未读取”描述的是当时状态。实际结果见文末及[数据试点](jiang-tgfb-data-pilot-2026-09-26.md)。

**建议在本轮评分与提交打包释放内存后，用独立 R 进程读取；不要用当前 rdata 路线展开这个文件。** R 原生连接读取避免完整压缩/解压缓冲副本，但 `readRDS` 仍要构造整个对象，不是按槽随机读取。当前未安装 R，首次只需隔离的基础 R 运行时来尝试属性审计，不必先安装完整 Seurat。是否最终需要少量依赖，要以该对象的实际序列化内容判断。

本记录不改变正在评分的训练数据，也不把 Jiang 纳入本轮候选。来源沿用[数据试点](jiang-tgfb-data-pilot-2026-09-26.md)和[已有原文核验](autonomous-finetuning-data-review-2026-09-25.md)：Jiang et al.，DOI [10.1038/s41556-025-01622-z](https://doi.org/10.1038/s41556-025-01622-z)，[Zenodo 14518762](https://zenodo.org/records/14518762)，CC BY 4.0。

## 实际完成的低内存检查

- 服务器 PATH 中没有 `Rscript`/`R`；检查 `/usr/bin`、`/usr/local/bin`、`/opt`、`~/miniconda3/bin`、`~/anaconda3/bin`、`/mnt/c/Program Files/R` 未发现可用路径。这不是全盘穷举。既有训练 Python 与本地 `.venv` 均未装 rdata/pyreadr/rpy2，本地已搜索缓存也没有可复用的 rdata 源码。
- 文件已出现在 `/mnt/e/vcc2026-data/raw/jiang_tgfb.rds`，字节数 **2,642,041,433** 与固定资产一致。预期 MD5 为 `8e9b4d39a95ec5881a30be6a2df541d1`；本次未重读全文件计算 MD5，沿用父下载器的校验收据。
- **仅用 `gzip.open(...).read(2*1024*1024)` 读取了 2,097,152 个解压字节**，随后关闭。没有完整 gzip 解压、没有 RDS parser 调用、没有读取后续大向量。
- gzip magic 为 `1f8b`；解压头为 `X\n`，序列化版本3，writer R **4.1.3**，min reader **3.5.0**，编码 UTF-8。根据类型标志和前缀，最先进入 `assays` 列表中首个对象的 `counts` 槽，再进入其 `i` 整数向量，长度 **605,806,920**。`i` 类型标志为13，长度字节为 `24 1b e1 48`。[R 类型/长度源码](https://github.com/vnmabus/rdata/blob/c5a659f327b45447498d1d7c9a6c2ccd4eb93d22/rdata/parser/_parser.py#L171)
- 在这2MiB内没有到达 assay 名称 RNA、稀疏矩阵类名、Dim/Dimnames 或 `meta.data`；**不能据此前缀宣称已确认 RNA 原始计数、细胞数、基因数、稀疏矩阵类或元数据字段。** `assays[[1]]@counts@i` 很符合传统 Seurat/Matrix 稀疏结构，但类名仍待完整读取。

前缀所指 `i` 单独需要约 **2.257 GiB** 的32位整数存储。若后续确认它是通常的 double `x` + int32 `i` 的稀疏 counts，`x+i` 将需要约 **6.770 GiB**，另加列指针和名称；这是条件性下界估算，不是对象实际 RSS。不能把2.46GiB压缩体积当作解析内存。

检查时服务器 MemAvailable 约15.15GiB，swap已用约2.22GiB；因此只做了上述有界前缀和源码检查，没有启动读取对象或转换任务。

## 为什么本次不使用 Python rdata 全读

核查固定 [rdata commit `c5a659f327b45447498d1d7c9a6c2ccd4eb93d22`](https://github.com/vnmabus/rdata/tree/c5a659f327b45447498d1d7c9a6c2ccd4eb93d22)：

1. [`parse_file` L1125–1146](https://github.com/vnmabus/rdata/blob/c5a659f327b45447498d1d7c9a6c2ccd4eb93d22/rdata/parser/_parser.py#L1125) 对路径调用 `read_bytes()`，对文件对象调用无大小参数的 `read()`；传入 `gzip.open` 也不能变成流式解析，它会完整读完。
2. [`parse_data` L1240–1262](https://github.com/vnmabus/rdata/blob/c5a659f327b45447498d1d7c9a6c2ccd4eb93d22/rdata/parser/_parser.py#L1240) 对gzip调用 `gzip.decompress(data)`，产生完整解压 bytes，原始压缩 bytes 仍在调用栈中。
3. [XDR parser L14–42](https://github.com/vnmabus/rdata/blob/c5a659f327b45447498d1d7c9a6c2ccd4eb93d22/rdata/parser/_xdr.py#L14) 将 memoryview 传入 `io.BytesIO`，再对每个数值向量读取一整段 bytes，用 `np.frombuffer(...).astype(dtype, copy=True)` 转成本机字节序并强制复制。
4. 固定 [CPython 3.12.11 BytesIO 初始化 L934](https://github.com/python/cpython/blob/v3.12.11/Modules/_io/bytesio.c#L934) 仅对精确 bytes 对象复用引用；memoryview 走写入路径，并在 [L229](https://github.com/python/cpython/blob/v3.12.11/Modules/_io/bytesio.c#L229) memcpy 到内部缓冲。因此不能把这个 BytesIO 误称零拷贝。

若 C 是压缩字节数、U 是完整解压长度、A 是已解析数组、B 是当前数值向量临时 bytes，上述路径可能同时占用接近 **C+2U+A+B**，另有对象/解压/转换开销；这不是经本文件实测的峰值上限。仅首个 i 数组就可出现约2.257GiB临时 bytes与同量本机数组。禁用 ALTREP 展开也不会移除入口的整文件读取和gzip全展开。此判断针对已核提交，不泛化到未来版本或所有R读取库。

## 基础 R 能做什么，何时需要依赖

固定 [R 源码 `b4322f3207e8d99d9dc6e6fa6b80ad23c4dc2f5f`](https://github.com/wch/r-source/tree/b4322f3207e8d99d9dc6e6fa6b80ad23c4dc2f5f) 的 [`readRDS`](https://github.com/wch/r-source/blob/b4322f3207e8d99d9dc6e6fa6b80ad23c4dc2f5f/src/library/base/R/serialize.R#L49) 使用 `gzfile(file,"rb")` 和 `unserializeFromConn`。数值向量先分配最终R向量，再按8096元素静态缓冲解码填入，[整数/实数实现](https://github.com/wch/r-source/blob/b4322f3207e8d99d9dc6e6fa6b80ad23c4dc2f5f/src/main/serialize.c#L1508)；它不要求先建立完整压缩bytes和完整解压bytes。

普通S4对象（R用于Seurat等复杂对象的有名槽结构）反序列化会分配对象并读取属性。`methods::slot(object,name)` 的[读实现](https://github.com/wch/r-source/blob/b4322f3207e8d99d9dc6e6fa6b80ad23c4dc2f5f/src/library/methods/R/SClasses.R#L288)调用 `R_get_slot`；对应 [C getter](https://github.com/wch/r-source/blob/b4322f3207e8d99d9dc6e6fa6b80ad23c4dc2f5f/src/main/attrib.c#L1808)对普通槽读取属性，不需要先加载Seurat类定义。基础 `attr(..., exact=TRUE)` 也可用于此初始审计。**读取槽与运行Seurat方法不是一回事**：先不调用 `slotNames`、`validObject`、`UpdateSeuratObject`、`GetAssayData` 等依赖类/方法定义的操作。

例外有明确源码依据：`NAMESPACESXP`/`PACKAGESXP`会恢复对应命名空间，package-specific ALTREP会调用相应反序列化方法。[R恢复分支](https://github.com/wch/r-source/blob/b4322f3207e8d99d9dc6e6fa6b80ad23c4dc2f5f/src/main/serialize.c#L1897)。所以可以确认“基础槽访问无需完整Seurat”，但不能在尚未读完文件时保证“整个Seurat对象在任何R环境都无依赖可读”。若读取报明确缺包，记录包名及阶段后结束该进程，在独立环境中补最小必要依赖；不要在现有训练环境里安装整套R分析栈。

建议父流程建立专用目录下的隔离 **r-base 4.5.x**，固定实际版本与环境清单，用 `Rscript --vanilla`；`methods`是R自带包。首先只运行 `infoRDS(path)` 复核格式头，再等评分/prep退出后启动一个带资源记录的 `readRDS` 审计进程。若需正式调用稀疏矩阵方法再加 Matrix，若确认是Assay5且需其映射方法再加匹配SeuratObject；不以未知需求提前安装完整Seurat。本子任务没有创建环境或安装包。

在31GiB主机上可为首次尝试设置进程级 `R_MAX_VSIZE=22G` 并记录 `/usr/bin/time -v`，把它当作R向量堆预算；它**不是严格RSS上限**。若可用进程/容器内存硬限额，可再给独立进程约26GiB边界，同时保证没有评分/打包争用。实际对象若不能在预算内恢复，记录分配失败后停止，不通过循环重试或扩大swap争用来硬撑。

如果 counts 与归一化 data 各有相近大小的独立稀疏数组，二者合计约13.54GiB；`scale.data` 若存在为密集矩阵，额外需要 `8×基因数×细胞数` bytes。每1亿个double元素约0.745GiB。这解释了为何原生R路线更节省仍不保证整个对象装得下；实际其余槽大小尚未知。

## 精确槽与元数据审计路线

SeuratObject固定 [commit `58bf437fe058dd78913d9ef7b48008a3e24a306a`](https://github.com/satijalab/seurat-object/tree/58bf437fe058dd78913d9ef7b48008a3e24a306a) 明确：Seurat根对象包含 `assays` 和 `meta.data`，[根定义](https://github.com/satijalab/seurat-object/blob/58bf437fe058dd78913d9ef7b48008a3e24a306a/R/seurat.R#L55)；传统 Assay包含 `counts`、`data`、`scale.data`，[Assay定义](https://github.com/satijalab/seurat-object/blob/58bf437fe058dd78913d9ef7b48008a3e24a306a/R/assay.R#L43)。counts的官方定义也允许TPM等未标准化值，因此**槽名counts本身不充分证明raw UMI**；仍须结合作者来源与实际数值核验。

首次完整读取只做下列操作，不归一化、不找高变基因、不聚类、不转换整对象：

```r
obj <- readRDS(path)
root_fields <- names(attributes(obj))
assays <- attr(obj, "assays", exact = TRUE)
meta <- attr(obj, "meta.data", exact = TRUE)
stopifnot(is.list(assays), is.data.frame(meta))
assay_names <- names(assays)
stopifnot("RNA" %in% assay_names)
rna <- assays[["RNA"]]
rna_fields <- names(attributes(rna))
counts <- attr(rna, "counts", exact = TRUE)
stopifnot(!is.null(counts))
count_class <- attr(counts, "class", exact = TRUE)
dim_count <- attr(counts, "Dim", exact = TRUE)
dimnames_count <- attr(counts, "Dimnames", exact = TRUE)
x <- attr(counts, "x", exact = TRUE)
i <- attr(counts, "i", exact = TRUE)
p <- attr(counts, "p", exact = TRUE)
```

这段是待运行骨架，不是已完成审计。先保存小型字段名、类名、长度与类型摘要，**不 `str(obj)` 或打印全部属性值**。若counts槽不存在则明确停止传统Assay路线；Assay5的原始计数通常位于 `layers`，细胞/基因对应关系位于 `cells`/`features` LogMap，[定义](https://github.com/satijalab/seurat-object/blob/58bf437fe058dd78913d9ef7b48008a3e24a306a/R/assay5.R#L35)。不能擅自取第一个counts-like层、把多层合并，或用 `data`/`scale.data`代替counts。

确认传统稀疏RNA counts后，保存其与meta引用，再 `rm(obj,assays,rna); gc()` 释放无关图、降维、归一化表达等槽。只读绑定通常不复制大向量；避免对父对象作替换赋值后才删除，减少R copy-on-modify风险。

计数与轴的实际验收包括：

- `Dim` 为 genes×cells；`Dimnames[[1]]`基因名、`Dimnames[[2]]`细胞名均存在，长度与维度一致，细胞名逐元素等于 `rownames(meta)`；重复基因符号与缺失注释如实记录，不自动改名或丢掉。
- 确认类和存储结构，例如 `dgCMatrix` 的 `i` 为从0开始的基因索引、`p`为列/细胞边界。要求 `length(i)==length(x)`、`length(p)==n_cells+1`、`p[1]==0`、尾指针等于存储项数、指针单调、索引范围有效。
- `x`按最多约1百万项的小块检查有限、非负、整数值及最大值，记录显式零。不要一次执行 `is.finite(x)`、`round(x)` 等为6亿项生成临时数组。按p逐细胞统计库量（每细胞总计数）与零细胞，避免对全x做cumsum后再切片。其结果支持“与计数合同一致”，并与作者对象来源一起构成raw-count证据。
- 保存所有 `meta.data` 列名/类型、缺失比例、小型取值摘要和细胞ID。对line/stimulus/batch/replicate/guide/target这些逻辑字段先找实际列再建立显式映射；候选名称如 `cell_line`、`cell_type`、`treatment`、`orig.ident`、`gene`、`guide`只能作为搜索线索，**当前未确认这些就是作者字段**。不要把聚类 `active.ident`当细胞系，也不要按guide字符串未经说明地截断得到基因。
- NTC保留原始guide及标签，统计 cell line×stimulus×batch/replicate×target 的细胞数和匹配NTC数；每层级没有NTC则标缺口，不跨刺激/批次借对照。若stimulus元数据缺失，只能记录“作者文件级声明TGFB，逐细胞未核验”，不能默认为无刺激。论文中所有通路刺激24h及14个NT guide来自原文，实际对象是否保留全部仍待审计。

如果以后要转为H5AD，传统 **genes×cells 的 CSC** 可将同一 `x/i/p`解释成 **cells×genes 的 CSR**：新shape反转，i仍是基因列索引，p仍是细胞行边界。这避免构建完整COO或做稀疏转置副本。先验证类/方向/轴，再按块写标准HDF5 CSR和元数据；不能用 `as.matrix()`。这只是后续转换方案，本轮没有生成数据或进入训练。

本轮最终应交付小型审计JSON/CSV：来源及完整校验收据、R/包版本、读取资源峰值、真实counts槽路径/类/维度/nnz、整数与轴检查、逻辑元数据映射、分层NTC/靶点计数、与当前官方/H1靶点及基因轴的覆盖。没有读到的字段留待核验，不能把第三方Jiang派生表或论文总规模直接当本文件的实测覆盖。

## 来源台账

未新增论文、不改论文INDEX；先复用既有Jiang原文与作者README。获准后读取小型官方/作者源码，**14次HTTP，全部成功，总计620,470bytes，最大单响应176,593bytes**，均低于每响应1MiB边界：rdata/R/SeuratObject各一次commit ref与所需源码，CPython固定tag源码。下载的只是本地忽略目录中的小型源码核验材料，未由本子任务下载数据/运行时、安装包、修改原始RDS或远程环境。

源码快照及URL/SHA-256台账位于 `output/rds-count-audit-readiness-20260926/`。本次只读取2MiB解压前缀，未测完整解压长度、未加载矩阵、未运行GPU；RDS内容和实际字段仍以今后完成的资源受控审计为准。

## 后续实际执行结果

2026-09-26 03:49:49 UTC 完成原生 R 全读和计数审计。确认传统 `assays/RNA/counts`、`dgCMatrix`、33,525 genes × 236,606 cells，605,806,920 个存储项；全部有限、非负且为整数，轴与元数据顺序一致。没有安装完整 Seurat，也没有完整转成密集矩阵。

`R_MAX_VSIZE=22G`、`ulimit -v 28000000` 下，R 进程 106.63 秒，完整阶段 123.02 秒，实测峰值 RSS 17,153,456 KiB，退出 0。故此前“能否装下”的缺口对这一个固定对象已解决，不能推广为任意 Seurat 文件均可在相同内存读取。环境版本、资源日志和 counts 审计见[小型产物](../../experiments/data_audit/results/2026-09-26/)；明确元数据映射、NTC 分层和官方/H1 覆盖见[完整试点报告](jiang-tgfb-data-pilot-2026-09-26.md)。

本次未新增文献查询；复用原有作者来源完成数据层核验。Jiang 仍为下一轮训练备选，不进入本轮提交。对 `sample_ID` 技术含义与刺激信息粒度的缺口仍保留。
