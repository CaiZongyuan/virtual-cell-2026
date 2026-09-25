# H1 离线 benchmark 核验与接入建议

> **2026-09-25 执行状态更新：**完整 H1 training 数据、对照和参考缓存现已在局域网服务器准备好，NTC/冻结/解冻三组六指标已实际完成，NTC 复现作者参考值。下文“未下载、未运行”为 9 月 14 日的历史审计范围；当前划分和暂停提交要求见[本地微调方案](pretrained-finetuning-local-plan.md)，成绩见[首轮记录](state-first-run-2026-09-25.md)。

> 核验日期：2026-09-14。对象：本地 `references/vcc2026-h1-benchmark`，版本 `v0.2.0`，提交 `d28dd0496cc9fbf1d0088ce171208c0deb54a268`，提交日期 2026-09-05。
>
> 本次完成代码、文档、测试和依赖锁文件的静态核验，以及无需第三方依赖的解析检查。没有安装依赖、下载 H1/发布资产、执行真实评分或测量峰值内存。因此本文区分实现可确认事实、作者报告值与工程建议。

> 后续方案修订：主模型已确定为 STATE 基线及全基因改进版。下文 M2/Ridge 的接入建议属于此前设计，工具合同与 H1 训练隔离原则保持有效；H1 先留出开发、配置冻结后加入正式训练的分阶段安排，以[当前主方案](first-submission-plan.md)为准。

## 1. 结论与定位

**适合接入，作为第一个可重复运行的完整六指标开发验收，以及一个额外的 H1 背景留出实验。** 它复用官方 `cell-eval2` 指标，实现了固定参考数据与 CPU 分块评分，能避免从零实现一套有偏差的评分器；但它使用公开的 2025 H1 训练数据，不是官方隐藏真值，也不代表 A/B/C 或 D/E/F 排行榜分数。[项目 README](../../references/vcc2026-h1-benchmark/README.md)；[固定版本代码](https://github.com/forrestsheldon/vcc2026-h1-benchmark/tree/d28dd0496cc9fbf1d0088ce171208c0deb54a268)

接入需要两个明确的边界：

- **数据边界：**若把 H1 分数称为“未见背景预测”，该次训练不能使用任何 H1 扰动细胞，包括固定 400-cell 参考之外的 H1 细胞。H1 对照可以按冻结的推理流程作为输入；参考 DE、pseudobulk moments 和 anchors 只能由评分器读取。
- **文件边界：**单独导出 H1 的 `50,400 × 18,080` 预测文件，再独立导出官方赛题的 `360,000 × 18,533` 文件。H1 验证通过不等于官方 `vcc prep` 通过。

这是从本地实现与[官方提交合同](submission-contract-check.md)推导的工程要求，不是该 benchmark 作者对本项目模型泛化能力的背书。

## 2. 来源、版本与本次核验范围

| 项目 | 核验结果 | 证据层级 |
|---|---|---|
| 仓库来源 | `https://github.com/forrestsheldon/vcc2026-h1-benchmark` | 本地 Git remote |
| 本地 HEAD / tag | `d28dd0496cc9fbf1d0088ce171208c0deb54a268` / `v0.2.0` | 本地 Git 实测；工作树干净 |
| Python package | `vcc2026-h1-benchmark==0.2.0`，Python `>=3.11,<3.13` | `pyproject.toml` |
| 指标实现 | `cell-eval2==0.16.0`，声明 source commit `5e64833518a6603a0301cbe28185d49c30f4a986` | 源码常量、provenance、lock 一致 |
| DE 后端 | `pdex==0.3.0`，CPU | 配置构造与依赖锁文件 |
| cell-eval2 wheel hash | `c78428ba705a94536e4a55464a34d1905aa5730d4f7e52ea8dbef4e7171d4fbe` | provenance 与 `uv.lock` 一致；未下载核验 wheel |
| pdex wheel hash | `fa7d805925c5ae16e3b060390bc47c47b7f79cd162cbd6a86544963ab6a44739` | 同上 |
| 声明的 resolved config hash | `e0893621789230be31d942139353568bf454bd5f168b68b5ee5ca411779d4591` | 作者 provenance；未在依赖环境重算 |
| 代码许可 | MIT | 本地 LICENSE / metadata；不重新授权 Arc 原始数据 |

来源：[DATA_PROVENANCE](../../references/vcc2026-h1-benchmark/DATA_PROVENANCE.md)、[pyproject](../../references/vcc2026-h1-benchmark/pyproject.toml)、[uv.lock](../../references/vcc2026-h1-benchmark/uv.lock)、[scorer.py](../../references/vcc2026-h1-benchmark/src/vcc_h1_eval/scorer.py)。

注意：运行时 `check()` 强制两个包的版本号，`package_provenance()` 记录已安装文件摘要，同时附上固定的声明 commit/wheel hash。它**没有把每次运行的已安装文件摘要与一个已知正确摘要强制比对**；因此同版本号的本地修改包仍需由本项目的环境锁定与代码指纹记录排除。不能将输出 manifest 中写有 source commit 误读为运行时重新验证了对应 Git tree。[artifacts.check](../../references/vcc2026-h1-benchmark/src/vcc_h1_eval/artifacts.py)；[package_provenance](../../references/vcc2026-h1-benchmark/src/vcc_h1_eval/scorer.py)

## 3. H1 数据、126 个靶点与基因轴

H1 是人胚胎干细胞系；本工具使用 Arc **2025 training** 对象，不使用 2026 验证真值。原始对象与辅助文件均从 Arc 公共 GCS 下载：[H1 H5AD](https://storage.googleapis.com/arc-institute-virtual-cell-atlas/virtual-cell-challenge/2025/train/adata_Training.h5ad)、[target counts](https://storage.googleapis.com/arc-institute-virtual-cell-atlas/virtual-cell-challenge/2025/train/pert_counts_Training.csv)、[gene names](https://storage.googleapis.com/arc-institute-virtual-cell-atlas/virtual-cell-challenge/2025/gene_names.csv)。本次未发出这些下载请求。

| 内容 | 固定合同 / 作者 provenance |
|---|---|
| 原始 H1 对象 | 221,273 cells × 18,080 genes，CSR 原始 UMI counts |
| 原始对象大小 | 15,482,497,461 bytes，约 14.419 GiB |
| 原始对象 SHA-256 | `a09977104fefb622368ca74b50c9d3c1e891733e6c83db07acfca49b0219c02b` |
| 原始对象 generation | `1765904883947296` |
| 原始 targeting panel | `pert_counts_Training.csv` 中 150 个唯一 target；代码核对其标签集合与源数据一致 |
| 保留 target | 观测细胞数 ≥400 的 126 个；其余 24 个排除 |
| 参考扰动细胞 | 每个 target 无放回抽取 400 个，共 50,400 个 |
| 参考对照 | 全部 38,176 个 `non-targeting` H1 细胞 |
| 完整表达基因轴 | 18,080，严格保留 2025 H1 `gene_names.csv` 顺序 |
| DE 基因池 | 对照细胞中逐细胞 CPM 的平均值 >5，代码要求得到 10,780 个基因 |

以上对象规模来自作者 provenance，并由代码常量与校验逻辑一致支持，**未由本次读取真实 H5AD 独立计数**。本地 clone 没有完整基因 CSV、参考细胞清单或已解压 benchmark bundle，故没有在本次列出全部 126 个实际基因名，也没有计算 H1/2026 基因轴交集。[registry](../../references/vcc2026-h1-benchmark/assets/benchmark-v1.json)；[DATA_PROVENANCE](../../references/vcc2026-h1-benchmark/DATA_PROVENANCE.md)；[target_contract / _reference_gene_universe](../../references/vcc2026-h1-benchmark/src/vcc_h1_eval/scorer.py)

参考抽样种子是 `default_rng(crc32(target))`，在该 target 的所有源行中 `choice(..., 400, replace=False)`。target 顺序继承原 CSV；公开参考清单内部按源行排序，但计算参考 pseudobulk 时保留确定性 RNG 顺序，以减少浮点规约顺序引入的微小差异。它不是每次重抽一份测试集。[reconstruct_reference_cells / assemble_reference](../../references/vcc2026-h1-benchmark/src/vcc_h1_eval/scorer.py)

单纯按 ≥400 cells 选择靶点，不能保证匹配 2026 的靶点敲低效率/响应强度分布。官方 2026 选取了 >80% 靶向敲低效率并产生强响应的靶点；H1 benchmark 的筛选依据应如实报告。[官方 Data](../Official-website/About-the-Data.md#靶标基因选择)

## 4. Frozen reference、控制组与评分锚点

普通 `setup` 下载已发布的非 count 资产包，声明 SHA-256 为 `69d85faff91516d558c553711f494176d90b49b301ebd3a89695ca78f87a12fa`。它包含参考细胞清单、参考 DE/rank 表、pseudobulk moments、generic-response baseline 和五次 split-half replicate anchor，不包含单细胞 count matrix。**没有 raw counts 不代表没有答案信息：DE 与 moments 已携带参考扰动效应。**[DATA_PROVENANCE](../../references/vcc2026-h1-benchmark/DATA_PROVENANCE.md)；[release asset builder](../../references/vcc2026-h1-benchmark/tools/build_release_asset.py)

三个对象必须区分：

| 对象 | 如何得到 | 正确用途 |
|---|---|---|
| 不变对照 baseline | 每 target 从全部 H1 NTC 中独立、无放回抽 400 个；target 之间可重用细胞 | 本地零效应 sanity check；不是缩放零点 |
| generic-response baseline | 对固定 reference 调用 Arc `build_generic_baseline`，构建所有 target 共用的通用响应 | evaluator 的 0 分参考；不得当作 H1 留出实验的训练先验 |
| replicate anchor | 固定 reference 以 base seed 0 派生五个 split seeds；每个 split 的两半互斥，控制组也显式检查互斥 | evaluator 的 1 分参考，不是五个独立实验批次 |

每个 target 的固定 400 个参考细胞被 split-half 划为约 200/200；38,176 个 controls 在两半间分开。五次拆分仍重复使用同一批原始数据，不应称为“五次独立生物学重复”。NMAE anchor 使用 full-reference DE gate 和 split-half 方向/幅度信息，源码通过官方 `_nmae_ref_from_tables` 计算，并采用最小 gate size 10。[rebuild_scale.py](../../references/vcc2026-h1-benchmark/tools/rebuild_scale.py)

普通 setup **不重算 anchors 或参考 DE**；这些重建程序属于 maintainer 工具，组装真实 reference 的路径会加载较大矩阵，不应拿普通分块评分的内存承诺套用到重建流程。[README](../../references/vcc2026-h1-benchmark/README.md)；[read_reference](../../references/vcc2026-h1-benchmark/src/vcc_h1_eval/scorer.py)；[rebuild_scale.py](../../references/vcc2026-h1-benchmark/tools/rebuild_scale.py)

README 报告不变对照 baseline 的 `avg_score ≈ -0.045230687652238`。本次未复现这一数值；接入后的首次实跑应将其作为版本/数据一致性检查，而不是模型质量目标。固定 0/1 锚点的比例也不能跨 H1、A/B/C 和 D/E/F 直接比较。[README](../../references/vcc2026-h1-benchmark/README.md)；[官方评分说明核验](submission-contract-check.md)

## 5. 评分器到底做了什么

配置由 `EvalConfig.from_preset("vcc2026")` 创建，保留官方指标与预处理语义，仅修改 `pert_col="target_gene"`、CPU、`pdex`、缓存路径及运行线程数。最终统计聚合、DE 指标派发和 reference scaling 调用官方 `cell-eval2` API；这不是单纯把新指标名字套到旧 2025 指标上。[evaluation_config / score_source](../../references/vcc2026-h1-benchmark/src/vcc_h1_eval/scorer.py)

普通 `score` 的实现顺序是：

1. 以 backed 模式打开预测和 control-only H5AD，校验 target、gene axis 和 count 值。
2. 每次只读取一个 target 的 400 行，计算官方 pseudobulk 和 moments；prediction-side NTC moments 复用真实 H1 control 的同一条结果。
3. 对参考 DE pool 的 10,780 genes，每次取 512 列；把预测与 NTC 变为逐细胞 CPM 后 `log1p`，调用 CPU `pdex` 求 Wilcoxon p 值。
4. 从线性 CPM 均值计算 clipped log2 fold change；合并所有基因块后，才按 target 做 Benjamini–Hochberg 校正，避免每块独立 FDR 改变显著性定义。
5. 调用官方指标、聚合和 frozen scale bundle，输出六项 scaled metrics 与 `avg_score`，另输出 10 项 profile aggregate 和可定义的 per-target raw results。

来源：[bounded.py](../../references/vcc2026-h1-benchmark/src/vcc_h1_eval/bounded.py)；[score_source](../../references/vcc2026-h1-benchmark/src/vcc_h1_eval/scorer.py)。

Pseudobulk 是把同类细胞汇总形成的群体表达摘要；DE（differential expression，差异表达）则比较扰动组与对照组的基因表达分布。两者的预处理不同，不能用一个 `normalize_total/log1p` 张量替代整条评分流程。PDS 的面板是 126 targets，相关 target 排除集合也随该面板变化；这正是其数值不能当作官方 300-target PDS 的原因。[scorer panel manifest](../../references/vcc2026-h1-benchmark/src/vcc_h1_eval/scorer.py)；[官方合同](submission-contract-check.md)

## 6. CLI、文件合同与静态发现的校验缺口

作者的 H1 预测合同为：sparse raw-count `X`；50,400 行；每个 canonical target 400 行；18,080 genes 原序；`obs` **只含** `target_gene`；不含 control rows；每细胞总数在 `[1, 1,000,000]`。H1 比本地官方文档多一个“细胞总量至少 1”的明确要求。[README](../../references/vcc2026-h1-benchmark/README.md)

静态审阅发现，`validate` 和 `score` 实际调用 `validate_source()`，**没有检查 sparse 存储，也没有检查额外 obs 列**；`RowSource.read()` 会把读取块转成 CSR。另一个 `validate_prediction()` helper 会检查 obs 列，但 CLI 不经过它；已有合同测试覆盖的是该 helper。输入缺少 `target_gene` 会在提取标签时失败，但带额外列不被同一路径拒绝。没有看到官方 4.75B stored-entry cap 或 obs-name 唯一性检查。[validate_command / score / validate_source / validate_prediction](../../references/vcc2026-h1-benchmark/src/vcc_h1_eval/scorer.py)；[RowSource](../../references/vcc2026-h1-benchmark/src/vcc_h1_eval/bounded.py)；[test_scorer.py](../../references/vcc2026-h1-benchmark/tests/test_scorer.py)

**本项目处理建议：**导出器主动遵守 README 的更严格合同，自己检查 CSR、基因序、唯一行名、整数、finite、总量和列集合；不能只凭 `vcc-h1 validate` 成功推断完全符合文档。该问题目前是静态确认的执行路径差异，本次没有安装依赖构造动态复现，也没有修改第三方代码。

接入时建议使用固定本地 clone 与独立环境；以下是待执行命令，不是已安装或已运行记录：

```bash
# 使用已核验版本，并按本地 uv.lock 固定依赖；先核对 Python 为 3.11/3.12。
uv sync --project references/vcc2026-h1-benchmark --frozen

# 如果已有原始 H1 对象，复用；setup 会严格校验大小和 SHA-256。
uv run --project references/vcc2026-h1-benchmark vcc-h1 setup \
  --h1 /path/to/adata_Training.h5ad --data-dir /path/to/h1-benchmark-data

uv run --project references/vcc2026-h1-benchmark vcc-h1 check \
  --data-dir /path/to/h1-benchmark-data

uv run --project references/vcc2026-h1-benchmark vcc-h1 validate prediction_h1.h5ad \
  --data-dir /path/to/h1-benchmark-data

uv run --project references/vcc2026-h1-benchmark vcc-h1 score-control-baseline \
  --data-dir /path/to/h1-benchmark-data --output /path/to/results/h1-control

uv run --project references/vcc2026-h1-benchmark vcc-h1 score prediction_h1.h5ad \
  --data-dir /path/to/h1-benchmark-data --gene-chunk 512 --de-threads 4 \
  --output /path/to/results/h1-model-seed0
```

`--data-dir` 位于子命令之后。`setup --h1` 仍会取基因/靶点小文件和非 count asset；省略 `--h1` 才会下载大 H1 对象。`--remove-source` 只删除工具管理的源文件，外部 `--h1` 文件不会被删除。删除受管源文件后日常用 `check/validate/score`；再次 `setup` 会走源文件获取流程，可能重新下载大对象。[cli.py](../../references/vcc2026-h1-benchmark/src/vcc_h1_eval/cli.py)；[artifacts.setup](../../references/vcc2026-h1-benchmark/src/vcc_h1_eval/artifacts.py)

## 7. CPU、内存、磁盘与时间边界

| 项目 | 可确认内容 | 本项目如何使用 |
|---|---|---|
| GPU | 普通评分显式 CPU / pdex，无须 GPU | 与模型训练进程分离 |
| 默认线程 | `--de-threads 4` | 首次按默认测量，避免假设线程越多越好 |
| 默认基因块 | 512；10,780 genes 共 22 块 | 内存不足可试 256/128；正整数由调用方保证 |
| 单个主 dense array | `(50,400+38,176)×512×8 = 346 MiB` | 仅此数组，不含 pdex 排序、临时拷贝、表格、CSR 或 Python 开销 |
| 行块 | 计数校验/归一化通常 256 rows；control extraction 512 rows | 原始 backed counts 分块读取 |
| 首次数据传输 | H1 原始对象约 14.419 GiB，另有小文件/asset | 作者 README 概述约 14.5 GiB |
| 首次磁盘峰值 | 作者估计约 16 GiB | 未包含本项目预测 H5AD、结果和模型；应另留余量 |
| 对照提取 | 作者报告现代笔记本约 15–25 分钟，下载后计时 | 未在当前机器测量 |
| 安装后常驻数据 | 作者报告 control-only H5AD 约 537 MB，移除受管源后约 575 MB | 不是所有实验输出总大小 |
| 评分耗时 / RSS | 本次未知 | 第一次完整 baseline 用 `/usr/bin/time -v` 记录，再决定并发数 |

346 MiB 是由源码形状推算的主数组下界式估算，不是“评分最多只用 346 MiB”。分块 DE 会重复遍历预测/NTC 的行；每个读取块先取完整行再截取基因，HDF5 解压与磁盘 I/O 可能成为瓶颈。每块原始 DE 有校验缓存，可中断后恢复；成功输出后删除本次缓存。因此相同文件再次成功评分通常仍会重新计算，不是永久 memoization。[bounded.py](../../references/vcc2026-h1-benchmark/src/vcc_h1_eval/bounded.py)；[score_source](../../references/vcc2026-h1-benchmark/src/vcc_h1_eval/scorer.py)

## 8. 泄漏与真实赛题差异

| 风险 / 差异 | 影响 | 接入要求 |
|---|---|---|
| H1 原本是公开 training set | 已用 H1 扰动训练的模型可取得记忆分数 | H1 leave-context-out 训练清单排除全部 H1 扰动；公开预训练权重若训练暴露不明，标为污染状态未知 |
| 只排除固定 400 个 reference cells | 同一 H1 背景、target、guide 的其他细胞仍暴露响应 | 不将“细胞互斥”当作“背景未见” |
| 参考 DE / moments / generic anchor 含真值摘要 | 可直接泄漏 target 效应或全局 H1 扰动方向 | 训练数据加载器不访问 `benchmark/reference_cache`、`benchmark/scale` |
| H1 得分反复选参数 | 固定公开 panel 逐渐变成开发集 | 明确称 development score；最终选择仍依靠未被反复调参的其他背景 |
| 一个 H1 背景 | 不能估计跨细胞背景稳定性 | 不替代 K562/RPE1/HepG2/Jurkat 的外层背景留出 |
| 126 targets vs 官方 300 | PDS 排名池、target exclusions、平均权重、响应强度分布改变 | 只在同一 H1 panel 内比较模型 |
| 18,080 vs 官方 18,533 genes | 不能直接用列位置复用输出；未交集基因难以评分 | H1/native 与 official/native 两个导出器，公共基因按符号映射 |
| H1 38,176 NTC vs 官方输入每背景 18,400 NTC | DE 统计能力、背景估计精度不同 | 报告此差异；不为“更像官方”私自改 canonical benchmark 后沿用原 anchors |
| H1 400-cell 重采样与 split anchors | 参考是同一来源数据的确定性分割 | 不声称复现真正独立实验重复的一致性 |

以上是根据本工具数据流和[官方合同](submission-contract-check.md)识别的评估边界。若需要未见靶点能力，另做训练时从**所有训练背景**删除 H1 评估 target 的实验；不要把其他背景已有同靶点响应的“跨背景迁移”误称“未见靶点”。这与首版 effect memory 的预期使用并不冲突，只是需要分别命名实验。

## 9. 建议如何插入当前首投方案

在 [first-submission-plan](first-submission-plan.md) 中增加一条优先的 H1 验收路径，建议顺序为：

1. **E0 / 第 1–2 天增加 H1 环境与合同验收。** 固定本次 tag/commit、`uv.lock` 和 data manifest；先 `check`，再执行标准 control baseline，保存四类结果文件、wall time 与 peak RSS。H1 大文件放外部或忽略目录。
2. **M2 首次完整离线实验增加 H1 leave-context-out。** 训练使用 Replogle/Nadig 等公共背景，H1 只给 NTC 输入；分别导出 B1、M1、M2 及至少三个生成随机种子的 H1 文件。评估六项指标、mean shifts 与 DEG 图，不只看 `avg_score`。
3. **将 H1 native exporter 作为独立验收件。** `obs` 仅 `target_gene`，完整 H1 genes；官方 exporter 仍按 A/B/C、300 targets、18,533 genes 验证。公共数据训练的 gene union/intersection 和输出补全策略需记录，不能用把 18,080 列随意补零的方式冒充处理了 assay 差异。
4. **保留原四背景 LOCO 为晋级主门槛。** H1 是额外一折及优先 smoke benchmark；原方案“至少 3/4 个背景改善”不应被一个 H1 高分自动替代。可以把 H1 用作模型失败定位、生成器检验和 assay 接近 10x Flex 的补充证据。
5. **STATE 在同协议下报告训练暴露情况。** 自训练基线可严格排除 H1；公开 checkpoint 若曾看过 H1，则其 H1 分数只作已见域方法参考，不能与干净 H1 leave-context-out 的 M2 放在同一“零样本排名”。

本次仅提出插入建议，没有修改主方案或论文索引。

## 10. 验证记录与未解决项

已实际执行且通过的轻量检查：

- 本地 Git HEAD、tag、remote、工作树状态核对。
- **15 个 Python 文件 AST 解析**，未导入第三方依赖。
- `pyproject.toml`、`uv.lock`、`benchmark-v1.json` 解析；包版本与两项 wheel hash 静态一致。
- 将 `_data_argument/parse_args` 从 CLI AST 隔离后，仅用标准库验证 **4 组参数**：setup、validate、score、score-control-baseline。没有执行对应业务命令。
- 主 DE 数组大小、基因块数、输出形状的整数计算。

已阅读但未执行的上游测试包含：CRC32 抽样确定性、全 control 保留、DE artifact schema、控制提取逐项相等、bounded DE 与官方 `compute_de` 一致、pseudobulk/moments 一致、raw metrics 一致、anchor split 与官方实现一致、scale 零/一映射、下载续传/checksum 与解包路径检查。其断言体现作者设计的验证覆盖，**不代表本次 pytest 通过**。需要完整 H1 artifact 的测试会在缺文件时跳过；尤其 frozen ACAT2 DE 校验不能由“默认测试通过”自动推出完成。[test_scorer](../../references/vcc2026-h1-benchmark/tests/test_scorer.py)；[test_controls](../../references/vcc2026-h1-benchmark/tests/test_controls.py)；[test_artifacts](../../references/vcc2026-h1-benchmark/tests/test_artifacts.py)

待首次接入实跑解决：asset/source 的真实校验和与126实际 target 清单、原生基因轴映射、baseline −0.04523 复现、CPU 峰值 RSS/耗时、M2/STATE 训练数据暴露记录、真实 H1 六指标及与四背景留出的关联。没有为填补这些缺口擅自下载或运行评分。
