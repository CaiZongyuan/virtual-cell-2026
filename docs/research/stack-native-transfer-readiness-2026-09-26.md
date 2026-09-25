# Stack 原生跨背景推理可执行性核查（2026-09-26）

> 后续实跑已完成：Aligned 在 3090 上通过 64/512-cell 原始计数推理检查，但 NTC 组成校准未过关；已测基因上的条件 TV 仍约 0.33。详见[实跑记录与小型结果](../../experiments/stack_native/README.md)。下文保留实跑前的源码审计范围和调用依据。

**结论：存在不读取 H1 扰动真值的原生迁移操作，可以安排 RTX 3090 上 batch=1、64-cell window 的小诊断；显存和预测质量尚未实测。** 官方教程直接把某条件下的源细胞类型作为示例、目标细胞类型的对照作为查询。因此可以把外部 K562/RPE1/HepG2 的某靶点细胞作为示例、H1 NTC 作为查询。这个调用方式有源码依据；从药物示例迁移到 CRISPRi 的准确性仍是待验证假设。

本轮仅阅读已克隆官方源码及既有 HF 元数据，无网络查询、模型/数据下载、依赖安装或 GPU 作业。代码固定为 `cacc2e4b09435c3e536d46237d10b50f222dd144`。本记录不改变当前 State 四组试验。

## 可执行入口与最小诊断

官方 [tutorial-predict.ipynb](https://github.com/ArcInstitute/stack/blob/cacc2e4b09435c3e536d46237d10b50f222dd144/notebooks/tutorial-predict.ipynb)以药物处理 T 细胞为 `base_adata`，以对照 B/myeloid 细胞为 `test_adata`，按药物条件分别生成；另用源对照运行生成以获得 synthetic control。教程只提出 synthetic-control 分析，没有在推理 API 内自动相减或纠正组成偏移。

以下是**待运行调用骨架**，输入必须是已经核验的原始整数计数 AnnData；`source_ntc_raw` 与 `query_ntc_raw` 分别来自外部源背景和目标背景，均不包含目标背景扰动细胞：

```python
import torch
from stack.model_loading import load_model_from_checkpoint
from stack.data.training.datasets import load_gene_list
from stack.cli.generation import _align_genes_to_target_list

model = load_model_from_checkpoint(
    ckpt, model_class="ICL_FinetunedModel",
    device=torch.device("cpu"), strict=True,
).float().to("cuda").eval()
genes = load_gene_list(genelist)
assert len(genes) == model.n_genes
native_n_cells = model.n_cells
model.n_cells = 64  # 明确记录为缩短窗口诊断；不是原 checkpoint 窗口复现

# 必须先分别对齐，否则下游 ad.concat(join="inner") 会丢掉查询独有基因。
base = _align_genes_to_target_list(source_ntc_raw, genes, None)
query = _align_genes_to_target_list(query_ntc_raw, genes, None)
assert base.n_obs > 0 and query.n_obs >= 32
pred = model.get_incontext_prediction(
    base, query, genelist,
    prompt_ratio=0.25, context_ratio=0.25, mode="predict",
    batch_size=1, num_workers=0, random_seed=42,
    filter_organism=False,
)
```

`pred` 是模型轴上的 CSR 原始计数样本，值通常以浮点 dtype 存放但 NB 抽样值为整数；仍需检查非负、有限性和行总量。使用 `filter_organism=False` 是因为现有来源可能写 `human`，上游默认只接受精确字符串 `Homo sapiens`；混合数据过滤会破坏既定窗口行数。输入前保证这批数据确实全为人类细胞。

先做源 NTC → 目标 NTC 的群体校准，再将 `source_ntc_raw` 换成**同一来源、一个靶点**的扰动细胞试迁移；H1 扰动标签始终不进入该输入。生成是随机的，不保证 NTC→NTC 逐细胞恒等，应检查平均组成、深度和方差相对于 NTC 重采样的变化。

多步入口为 `model.get_incontext_generation(..., mode="mdm", num_steps=5, ...)`，官方 CLI 使用这一路径。首个 smoke 建议先用上述单步 `get_incontext_prediction`，便于区分模型校准与迭代行为。不要使用继承的 `predict()` 去调用 Aligned：它假定基础模型的 `forward(features)` 签名，Aligned 的 `forward` 还需要 `ground_truth_features`。[推理源码](https://github.com/ArcInstitute/stack/blob/cacc2e4b09435c3e536d46237d10b50f222dd144/src/stack/models/core/inference.py#L552)、[Aligned forward](https://github.com/ArcInstitute/stack/blob/cacc2e4b09435c3e536d46237d10b50f222dd144/src/stack/models/finetune/model.py#L17)

## 输入、排列与计数合同

| 项目 | 固定源码行为与实践含义 |
|---|---|
| 条件输入 | 没有 target-gene encoder。靶点名称只用于挑选外部示例，不进入模型前向。没有外部示例的靶点不能仅凭名字调用原生迁移 |
| 成对要求 | 推理不要求源/目标细胞一一对应，也不需要目标扰动真值；同一窗口由源示例在前、目标 NTC 查询在后组成 |
| 64-cell 排列 | 本例每窗口 32 个源示例、32 个查询；前 16 个源示例作为 prompt，不可注意其后的细胞；另 16 个为 context，查询加 learned query embedding。两组源示例均来自同一 `base` 条件，context 不是额外的源对照输入 |
| 抽样 | base 随机重排后循环使用，示例不足会复用；query 保持原顺序。最后不足一个窗口会补行，最终只保留真实 query 行；极小 query 数存在补行不足风险，smoke 用 64 query 行 |
| 数值预处理 | loader 优先读 `raw.X`，否则 `X`；映射到固定 gene list，缺基因补 0，转 float32。网络内部做 `log1p(raw counts)`；**不做 CP10k，也不可先 log1p 再传入**。AnnData 的 `.raw` 名称本身不证明其中是计数 |
| 库大小 | `observed_lib_size = mapped_features.sum(-1)`，即**模型轴内**计数和，不是完整原始转录组的 UMI 总量 |
| NB 解码 | 负二项分布（Negative Binomial, NB）允许计数方差大于均值。`mu = softmax(logits) × observed_lib_size`，`theta = softplus(...)`；推理采样的 theta 使用 prompt+context 细胞的基因逐项中位数 |
| 输出深度 | NB 均值的行和等于输入模型轴深度；独立 NB 样本的行和不固定。多步生成每次用上一次样本的深度，不能声称保留原 NTC 行总量 |
| 缺失输出 | `align_result_to_adata_numpy` 对 test-only genes 默认填 0，**不会自动保留 NTC**；CLI 本身也先裁到模型轴。完整 18,080/18,533 基因输出需要独立适配，不能把原生输出直接当完整比赛文件 |

先独立对齐 base/query 至模型轴尤其关键：若直接传入 8k 基因的源 AnnData 和 18k 基因的 H1，原生 `ad.concat(join="inner")` 会先移除 H1 独有基因；仅在后面的 loader 补零不能恢复已丢掉的查询表达。官方 CLI 的预对齐避免了这个额外损失。本记录调用同一私有 helper，必须固定源码版本；它会产生无 `.raw` 的新 AnnData。对原本未测的源基因补零是上游既有行为，仍会把缺测与真实零表达混同；源码没有缺测 mask。

来源：[gene loader](https://github.com/ArcInstitute/stack/blob/cacc2e4b09435c3e536d46237d10b50f222dd144/src/stack/data/training/datasets.py#L655)、[计数推理](https://github.com/ArcInstitute/stack/blob/cacc2e4b09435c3e536d46237d10b50f222dd144/src/stack/models/core/inference.py#L165)、[NB 参数](https://github.com/ArcInstitute/stack/blob/cacc2e4b09435c3e536d46237d10b50f222dd144/src/stack/models/core/base.py#L106)、[输出轴对齐](https://github.com/ArcInstitute/stack/blob/cacc2e4b09435c3e536d46237d10b50f222dd144/src/stack/models/utils.py#L27)。

## 权重、依赖与 3090

固定 [Stack-Large-Aligned revision](https://huggingface.co/arcinstitute/Stack-Large-Aligned/tree/b09f085dac03d170b078a5c72f550ae93686e544)，沿用[资产登记](../../experiments/local_benchmark/asset-inventory-2026-09-25.json)：

| 文件 | 字节数 | SHA-256 |
|---|---:|---|
| `bc_large_aligned.ckpt` | 2,613,863,242 | `f93cf6f42f36c8a85dc570d92e801c1fc3e1f45d55741e6bb250d178a6b6ad36` |
| `basecount_1000per_15000max.pkl` | 925,039 | `d8761dfda955b9897d3251798b72361ddd0171ef707119eaf65381bed2d85dcc` |

基因列表必须取该 pickle，不能重新选 HVG 或根据文件名构造 15,000 个基因。既有文献记录为 15,012 基因，但本轮未下载/解包该文件；实际运行须用 `len(genes) == model.n_genes` 与词表内容核对。模型卡写 217M 参数、scBaseCount 约 150M 细胞预训练，Aligned 加 CellxGene 45M + Parse PBMC 10M；**H1 预训练暴露仍未排除**，只能承诺本轮推理不输入 H1 扰动标签。

[loader](https://github.com/ArcInstitute/stack/blob/cacc2e4b09435c3e536d46237d10b50f222dd144/src/stack/model_loading.py#L17)从 `hyper_parameters.model_config` 构造模型，只去掉 `state_dict` 键的 `model.` 前缀，然后严格装载。CPU 上先加载再 `.to("cuda")` 可避免把 checkpoint 内优化器等 payload 先放到显存。CLI 虽有 `--device`，`generate()` 并未把它传给 loader；需要设备控制时走 Python 入口。

直接推理导入依赖是 `torch/numpy/pandas/scipy/anndata/h5py/psutil/tqdm/geomloss/scvi-tools`；`scvi-tools` 还会引入其依赖。完整包安装要求另含 `pytorch-lightning/PyYAML/wandb`，见 [setup.cfg](https://github.com/ArcInstitute/stack/blob/cacc2e4b09435c3e536d46237d10b50f222dd144/setup.cfg)。上游实测 Python 3.10/PyTorch 2.5.1；现有 State 环境 Python 3.12/PyTorch 2.7.1 已含多数计算依赖，但清单不含 scvi-tools。

建议隔离 `.stack-venv`，固定与现有 GPU 环境相同的 CUDA torch，不修改正在训练的环境。`--system-site-packages` 继承基础解释器全局 site-packages，不能想当然地复用兄弟 State venv；先核对 `torch.__file__`。PyTorch 2.7 的 `torch.load` 默认安全加载可能拒绝旧 Lightning 对象；上游 loader 没有传 `weights_only`。先尝试默认安全加载；如失败，仅对核过上述 SHA 的可信官方文件在局部 loader 显式选择加载方式，不全局 monkeypatch。pickle/ckpt 均按可信代码资产处理。

**不需要 flash-attn，也没有强制 H100 内核。** [attention.py](https://github.com/ArcInstitute/stack/blob/cacc2e4b09435c3e536d46237d10b50f222dd144/src/stack/modules/attention.py)使用标准 `q @ k.T` 和 softmax，支持 CPU/CUDA；显式注意力也意味着窗口扩大有二次内存成本。cell 维度由运行时 tensor 推断，没有 learned cell-position 参数，故改 `model.n_cells=64` 不改变权重形状；它改变上下文信息量，应登记。FP32、batch=1、no-grad、64-cell 的 3090 推理在结构上可行，但文件大小和参数量不能代替显存实测；本轮没有运行或给出峰值承诺。

## 现有数据能否直接用及下一步

现有 prepared `counts.npz` 是原始计数，但[准备代码](../../experiments/state_finetune/data.py)已经裁到 State/H1/比赛并集，可能额外丢失 Stack 模型基因。可复用 `manifest.json`、`groups`、`original_rows.npy`、`row_batches.npy` 的选行与 NTC 匹配规则，**从已下载 raw H5AD 重读选中行，再映射至 Stack pickle**，无需重下数据。单个条件最多数百行即可做 smoke；不能把 State 的 log-normalized 输入缓存拿来充当 Stack raw counts。

外部源同靶点示例 + H1 NTC 的推理数据能够构造；缺靶点示例、缺源基因和父权重暴露需单独记录。先只跑一个来源的 NTC→NTC，记录原生模型轴的均值组成、输入/输出深度、方差、整数性及内存。通过后才试少量外部靶点；此阶段无需 H1 扰动真值，也不作为第四个已评分优化候选。完整 H1 比较前另审计模型轴外的 NTC 保留及所有模型轴基因中的缺测影响。

微调代码确实支持“同 identity 的处理细胞与 control replacement”组织：`drug` schema 的 `condition_col` 可表达靶点、`cell_line_col` 可表达背景，replacement 只从同 identity 的 control condition 取细胞。这是结构可重用性，不能当作已验证的 CRISPRi 配方。训练需要外部已知扰动真值，但不要求 H1 真值。教师无梯度，却在每 500 steps 以 EMA=0.95 更新，并非始终固定不变的教师；推理加载仅需学生 checkpoint。[replacement 规则](https://github.com/ArcInstitute/stack/blob/cacc2e4b09435c3e536d46237d10b50f222dd144/src/stack/data/finetuning/datasets.py#L939)、[教师更新](https://github.com/ArcInstitute/stack/blob/cacc2e4b09435c3e536d46237d10b50f222dd144/src/stack/finetune/lightning.py#L275)。

检索台账：复用论文索引；Scholar、SciVerse、HTTP 调用均为 0。已核查代码 revision、README、预测 notebook、loader、CLI、core inference/attention/NB、gene loader、finetune replacement/teacher 与既有固定 HF 元数据。未新增论文，不宣称运行成功、CRISPRi 提分、严格未见 H1 预训练或完整比赛输出可直接交付。
