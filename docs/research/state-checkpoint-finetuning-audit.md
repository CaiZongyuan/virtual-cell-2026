# State 发布检查点如何真正微调：源码与文件合同核验

日期：2026-09-14。性质：官方源码、官方发布元数据和小型配置的静态核验；**没有下载大权重或训练数据，没有安装 State 依赖，没有加载模型或运行 GPU 训练**。本文支持 VC2026 教程，不构成性能复现或资源实测。

核心结论：State 有原生 `model.kwargs.init_from` 初始化入口，可以复用已发布 ST 的参数。它不会自动继承发布模型的架构、基因顺序、靶点字典或批次映射。对于 VC2026，先验证原 checkpoint 的兼容输入，再迁移 328 维主干、靶点表示和全基因输出，比直接使用当前 768 维默认模型加一个 checkpoint 路径更可核查。

## 1. 固定来源与证据层级

| 编号 | 一手来源 |
|---|---|
| S1 | State commit [`9bbfe78a434a55205e4de834e1ea99f85f7a3add`](https://github.com/ArcInstitute/state/tree/9bbfe78a434a55205e4de834e1ea99f85f7a3add)；本地 `/tmp/vcc2026-state-plan-source` |
| S2 | cell-load commit [`9ba45e59f6f8117bb7a21371ad38d67175586d53`](https://github.com/ArcInstitute/cell-load/tree/9ba45e59f6f8117bb7a21371ad38d67175586d53)；本地 `/tmp/vcc2026-cell-load-plan-source` |
| H1 | [`arcinstitute/ST-HVG-Replogle`](https://huggingface.co/arcinstitute/ST-HVG-Replogle/tree/bb6a9562cbbf1fd152df14cc53b4cc7517c77175/zeroshot/jurkat)，revision `bb6a9562cbbf1fd152df14cc53b4cc7517c77175`，run `zeroshot/jurkat` |
| H2 | [`arcinstitute/st-x-replogle-full`](https://huggingface.co/arcinstitute/st-x-replogle-full/tree/48ad5f70215ab4c58caa5a68e77d837601d29d35/k562_0.99)，revision `48ad5f70215ab4c58caa5a68e77d837601d29d35`，run `k562_0.99` |

复用已有 [State 训练源码核验](state-training-source-audit.md) 中的 4 份发布 YAML 与 HF 元数据。本轮只新增两次固定 revision 的文件树请求，以及两个各 1,901 bytes 的 `data_module.torch` 下载；后者用 ZIP 读取与 `pickletools.dis` 检查存储字段，未执行反序列化对象构造。新增证据保存在 `/tmp/vcc2026-state-finetuning-audit/`，不入 Git。

下文“已验证”仅指本轮静态读取能支持的事实；“工程建议”指需要项目实现或试跑的方案；“待验证”不能写成已经完成。

## 2. 已发布的两个模型不是当前默认模型

| 字段 | H1：HVG / zeroshot jurkat | H2：full / k562_0.99 | 当前 `model=state` 默认 |
|---|---:|---:|---:|
| 输入与输出维数 | 2,000 / 2,000 | 6,546 / 6,546 | 从输入文件维度构造 |
| hidden_dim / hidden_size | 328 / 328 | 328 / 328 | 768 / 768 |
| Transformer 层数 | 8 | 8 | 8 |
| intermediate_size | 3,072 | 3,072 | 3,072 |
| attention heads / KV heads / head_dim | 12 / 12 / 64 | 12 / 12 / 64 | 12 / 12 / 64 |
| cell_set_len | 64 | 64 | 512 |
| pert_dim | 2,024 | 2,024 | 由特征字典决定 |
| 靶点表示 | one-hot | one-hot | 未给特征文件时为 one-hot |
| batch_dim / batch_encoder | 56 / true | 56 / true | 数据决定 / false |
| embed_key / output_space | X_hvg / gene | null / all | null / all |
| 发布训练 batch_size | 64 | 64 | 16 |
| 发布训练 lr / max_steps | 0.001 / 100,000 | 0.0001 / 80,000 | 0.0001 / 400,000 |

来源：H1 的 [config](https://huggingface.co/arcinstitute/ST-HVG-Replogle/blob/bb6a9562cbbf1fd152df14cc53b4cc7517c77175/zeroshot/jurkat/config.yaml) 与 [hparams](https://huggingface.co/arcinstitute/ST-HVG-Replogle/blob/bb6a9562cbbf1fd152df14cc53b4cc7517c77175/zeroshot/jurkat/version_0/hparams.yaml)；H2 的 [config](https://huggingface.co/arcinstitute/st-x-replogle-full/blob/48ad5f70215ab4c58caa5a68e77d837601d29d35/k562_0.99/config.yaml) 与 [hparams](https://huggingface.co/arcinstitute/st-x-replogle-full/blob/48ad5f70215ab4c58caa5a68e77d837601d29d35/k562_0.99/version_0/hparams.yaml)；S1 [state.yaml](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/configs/model/state.yaml)。

**328 不是按 12 个 heads 均分的维数；配置显式指定 `head_dim=64`。** 不要为了“整除”把 hidden_dim 改为 324/384，也不要删除 head_dim 后假定权重相容。是否能由当前依赖版本正确装载仍需要真实模型初始化确认。

H1 的 `hparams.yaml` 含有 2,000 个有序 `gene_names`；H2 含有 6,546 个。`full` 是该发布版本的全基因轴，不能理解为 VC2026 的 18,533 genes。发布 batch/steps 是配置证据，不是完成微调的必需训练量。

## 3. 最小下载单元及大小

H1 与 H2 必须以**同一 run 的权重、配置和映射**组成一个模型包。只下载一个 `best.ckpt` 后自行重建字典，会破坏输入语义。

| 同 run 文件 | H1 bytes | H2 bytes | 用途 |
|---|---:|---:|---|
| `checkpoints/best.ckpt` | 471,699,039（约 449.85 MiB） | 664,162,239（约 633.39 MiB） | 一个起始 checkpoint；不必同时下载 best/final/last |
| `config.yaml` | 2,766 | 2,736 | `state tx infer` 读取 |
| `var_dims.pkl` | 155,642 | 193,534 | `infer` 必需；维度和基因/靶点元数据 |
| `pert_onehot_map.pt` | 16,746,593 | 16,746,593 | `infer` 必需；靶点身份与向量的映射 |
| `batch_onehot_map.pkl` | 721,431 | 721,431 | 发布模型启用 batch encoder，应一起下载；当前 infer 支持旧 `.pkl` |
| `cell_type_onehot_map.pkl` | 1,799 | 1,799 | 建议保留，infer 尝试读取；不是 ST 输入主干中的细胞类型特征 |
| `version_0/hparams.yaml` | 18,468 | 56,363 | 人工审计架构、基因顺序与来源；infer 不直接读取它 |
| `data_module.torch` | 1,901 | 1,901 | 来源线索，不是推理必需，也没有打包原训练数据 |

来源：H1/H2 固定 revision [tree API H1](https://huggingface.co/api/models/arcinstitute/ST-HVG-Replogle/tree/bb6a9562cbbf1fd152df14cc53b4cc7517c77175/zeroshot/jurkat?recursive=true)、[tree API H2](https://huggingface.co/api/models/arcinstitute/st-x-replogle-full/tree/48ad5f70215ab4c58caa5a68e77d837601d29d35/k562_0.99?recursive=true)。必需性由 S1 [`_infer.py` L359–440](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/_cli/_tx/_infer.py#L359) 核实。

H1 best 的 LFS SHA-256 是 `6fa4fe9a1c8a267d88d519d335e367b80594db64d2005abf1407260afccbfa6b`；H2 best 是 `fd23d8994e1dd2e1a29e2901c3cb984836171167f488d64ce04c9c161b1e0126`。下载后应计算 SHA-256 对比。两份靶点字典的 LFS SHA 一致：`f5621cab243a5135014af3867f63f8bf75cff19aee06d0f29a1bdecd2dbf47d0`；这只证明文件相同，不证明覆盖比赛全部靶点。

模型仓库另有评估用 `.h5ad`、CSV 及其他背景/checkpoint。使用限定文件清单下载，避免为一次兼容试跑拉取全部评估预测和所有权重；下载目录置于 `/data/` 或 Git 忽略目录。

## 4. `init_from` 与 resume 是两件事

已验证控制流，来源 S1 [`_train.py` L289–400](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/_cli/_tx/_train.py#L289)：

1. 先按**当前 CLI 配置与当前数据**建立新模型、维度与映射。不会用 `init_from` 的 hparams 自动替换当前架构。
2. 检查新 run 目录中是否已经有 `checkpoints/last.ckpt`。
3. 若有，直接 `trainer.fit(..., ckpt_path=last.ckpt)`；`init_from` 不执行。这是继续既有 Lightning 训练的路径。
4. 若没有 last，且设置 `model.kwargs.init_from=...`，读取该 checkpoint 的 `state_dict`，保留**同名且形状一致**的参数，其他参数打印 skip 信息；随后 `load_state_dict(filtered_state, strict=False)`。
5. manual init 最后调用 `trainer.fit(..., ckpt_path=None)`。它不是恢复旧优化器和旧 global step；优化器由当前模型的 `configure_optimizers` 新建，当前实现是 `torch.optim.Adam(self.parameters(), lr=self.lr)`。

因此已确认的 CLI 字段为：

```text
model.kwargs.init_from=/data/checkpoints/.../checkpoints/best.ckpt
training.lr=0.00001
training.max_steps=2000
output_dir=/data/vcc2026/runs
name=state_hvg_warmstart_trial_001
```

以上 lr/steps/name 是项目试跑建议，不是官方微调配方。每次新实验使用新 run 名。不要把源权重复制为新 run 的 `last.ckpt` 来充当微调，也不必开启会删除既有目录的 `overwrite=true`。S1 [`_train.py` L43–55](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/_cli/_tx/_train.py#L43) 在训练前会重写 run 的 config，重复利用目录还可能混淆来源记录。

**`strict=False` 自身不能吞掉 shape mismatch。** 此入口能跳过尺寸不同的层，是因为它先手工过滤；它也不按生物学名称映射列/行、不报告复用参数占比、不自动验证新模型能做比赛任务。

## 5. 四类“形状相同，但含义已经错了”的问题

### 5.1 基因列

`basal_encoder.0.weight` 的每个输入列对应一个基因；`project_out.0.weight` 的每个输出行对应一个基因。即使两个文件都包含 2,000 genes，只要顺序或基因集合不同，按 tensor shape 装载仍会成功而语义错误。当前 loader 从参考 dataset 取得维度和 gene_names，原生 init_from 没有把新旧基因名单进行对齐。[S2 `get_var_dims` L347–382](https://github.com/ArcInstitute/cell-load/blob/9ba45e59f6f8117bb7a21371ad38d67175586d53/src/cell_load/data_modules/perturbation_dataloader.py#L347)

兼容试跑要严格使用发布的有序基因轴；不要重新挑一组 HVG（高变基因，指细胞间表达变化较大的基因）仍称为原 checkpoint 兼容输入。扩到 18,533 genes 时可选择：

- **原生尺寸过滤迁移：**保留兼容主干；输入和输出大矩阵的尺寸变了便整体不加载，按当前代码重新初始化。这确实是在微调预训练主干，但不是完整保留旧输入输出头。
- **项目名称对齐迁移器：**将共同基因对应的输入列、输出行与 bias 显式拷贝；新增基因按声明的策略初始化，记录复制数量。它属于要编写的适配代码。

### 5.2 扰动靶点

one-hot 向量是一组身份索引，数字位置没有跨运行的天然含义。当前 cell-load 使用 `sorted(set(keys))` 生成新 one-hot 字典；增删一个排序靠前的靶点便可能移动许多列。[S2 `generate_onehot_map` L136–154](https://github.com/ArcInstitute/cell-load/blob/9ba45e59f6f8117bb7a21371ad38d67175586d53/src/cell_load/utils/data_utils.py#L136)

保持旧表示时，可以把发布 `pert_onehot_map.pt` 作为原生 `data.kwargs.perturbation_features_file`，以复用原向量定义；必须事前断言所有训练与推理靶点存在且维数一致。这个字段接受完整 `{target: tensor}` 字典，并不要求 tensor 一定是蛋白特征。不能让 loader 对缺失靶点自动补零后继续训练。[S2 L566–590](https://github.com/ArcInstitute/cell-load/blob/9ba45e59f6f8117bb7a21371ad38d67175586d53/src/cell_load/data_modules/perturbation_dataloader.py#L566)

扩展 one-hot 可以按靶点名称复制旧列，并为新靶点添加列；新列要从有监督训练中学到作用。**一个从未获得扰动标签的随机新 one-hot 列，并没有自动获得零样本预测能力。**

迁移到 ESM2 等连续蛋白特征时，新的 `pert_dim` 由特征文件确定，不能假装旧 one-hot 参数仍有相同含义。若维数不同，原生 init_from 会跳过不匹配的 first-layer weight；同维 bias 等仍可能被复用。若恰好维数相同，原生入口会装载语义完全不同的旧 weight，需迁移器显式排除它。进一步用旧靶点表征蒸馏新 encoder 是可测试的工程方案，不是官方已验证流程。

推理中缺失靶点会回退到 control vector，来源 [S1 `_infer.py` L756–806](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/_cli/_tx/_infer.py#L756)。项目应将这一回退改成明确报错并列出缺口。

### 5.3 批次标签

这里 batch 指实验批次标签，例如不同实验板/建库批次；它与优化器的 `training.batch_size` 是两种概念。发布模型使用 `nn.Embedding(batch_dim, hidden_dim)`，按 batch 标签的索引查表并加到细胞 token 上。[S1 `state_transition.py` L188–197、L425–441](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/tx/models/state_transition.py#L188)

原生训练重新从当前数据生成 batch 字典，没有与旧映射按 label 对齐的传入接口。56 个新 batch 恰与 56 个旧 batch 同维时，直接复制 embedding 仍会把新实验指派给错误旧行；数量不同则整块被跳过。当前 infer 对陌生标签回退 index 0，这是选择一个旧实验行，**不是中性批次，也不是学到了新背景**。[S1 `_infer.py` L655–693](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/_cli/_tx/_infer.py#L655)

工程上可先在兼容推理时保留旧映射；正式迁移时显式选择按语义拷贝/扩展、设计未知批次处理，或用 `model.kwargs.batch_encoder=false` 移除它后继续适配。最后一种是模型变更，需要做消融和留出验证，不能称为保持发布模型的直接推理。也不要把未知背景 A/B/C 强行命名为某个旧细胞系来解决 batch 问题。

### 5.4 表达值的尺度

“相同 2,000/6,546 列”之外，还要有相同的归一化、log1p 与预处理尺度。两份小型 `data_module.torch` 均记录 `normalize_counts=false`，只说明 loader 当时不开这一选项，不能反推出输入 `.X` 是 raw counts，亦不能证明归一化总量恰为 10,000。发布 YAML 没有补足此前处理全部细节。

因此先核对来源数据的表达层与处理代码；如果正式迁移选择明确的 log1p(CP10K)，应声明这是新训练尺度并验证分布变化，不能当作原模型无损输入替换。`output_space=all` 只选择完整输出轴，不保证输出整数 raw counts。详见既有 [全基因、log1p 与原始计数核验](state-training-source-audit.md#全基因log1p-与原始计数)。

## 6. 从 HVG 到全基因不只是改维数

当前官方 HVG 路径（`output_space=gene`）的残差是：

```text
project_out(transformer_output + basal_encoder(control))
```

而 `output_space=all` 路径是：

```text
final_down_then_up(project_out(transformer_output) + control)
```

其中 `final_down_then_up` 是 `G → floor(G/8) → G`，中间 GELU。来源 [S1 L372–386](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/tx/models/state_transition.py#L372)、[L501–516](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/tx/models/state_transition.py#L501)。

H1 没有该 `all` 路径额外矩阵；H2 虽有，但其 G=6,546，换到 G=18,533 仍需处理尺寸变化。新的瓶颈隐藏单元没有“基因名”，不能像基因行/列一样按名字简单映射。可整体重建，或明确设计保持旧瓶颈等新的迁移架构；两者都需要记录。

仅 `G=18,533` 的额外层按代码手算就有 `2×G×floor(G/8)+G+floor(G/8)=85,865,705` 个参数。该数是矩阵形状推导，不是整个模型参数实测。还应审计基类按 `decoder_cfg` 创建的辅助 `gene_decoder`，不要只计算 forward 图中显眼的几层；[S1 `base.py` L244–252](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/tx/models/base.py#L244)。

## 7. 可以写进教程的原生微调命令骨架

以下示例是**保留 H1 的 HVG 主结构、保留旧靶点向量、主动移除旧 batch encoder 的小型适配试跑**。它不是逐字复现，也不是完整 VC2026 输出。前提是 `/data/vcc2026/aligned_hvg/` 已按发布 hparams 的 2,000 有序基因与核实后的表达尺度准备；所有靶点在发布字典中；TOML 已配置合法训练/验证分离；新 run 目录没有 `last.ckpt`。路径是拟定产物，当前仓库并没有这些就绪数据。

```bash
state tx train \
  model=state \
  model.kwargs.init_from=/data/checkpoints/ST-HVG-Replogle/zeroshot/jurkat/checkpoints/best.ckpt \
  model.kwargs.hidden_dim=328 \
  model.kwargs.cell_set_len=64 \
  model.kwargs.transformer_backbone_kwargs.hidden_size=328 \
  model.kwargs.transformer_backbone_kwargs.max_position_embeddings=64 \
  model.kwargs.transformer_backbone_kwargs.intermediate_size=3072 \
  model.kwargs.transformer_backbone_kwargs.num_hidden_layers=8 \
  model.kwargs.transformer_backbone_kwargs.num_attention_heads=12 \
  model.kwargs.transformer_backbone_kwargs.num_key_value_heads=12 \
  model.kwargs.transformer_backbone_kwargs.head_dim=64 \
  model.kwargs.batch_encoder=false \
  model.kwargs.use_batch_token=false \
  model.kwargs.freeze_pert_backbone=false \
  model.kwargs.lora.enable=false \
  data.kwargs.toml_config_path=/data/vcc2026/splits/hvg_warmstart.toml \
  data.kwargs.embed_key=X_hvg \
  data.kwargs.output_space=gene \
  data.kwargs.pert_col=target_gene \
  data.kwargs.cell_type_key=context_id \
  data.kwargs.batch_col=batch_id \
  data.kwargs.control_pert=non-targeting \
  data.kwargs.perturbation_features_file=/data/checkpoints/ST-HVG-Replogle/zeroshot/jurkat/pert_onehot_map.pt \
  data.kwargs.num_workers=4 \
  training.batch_size=2 \
  training.gradient_accumulation_steps=8 \
  training.lr=0.00001 \
  training.max_steps=2000 \
  training.val_freq=2000 \
  training.ckpt_every_n_steps=2000 \
  training.devices=1 \
  training.train_seed=42 \
  use_wandb=false \
  training.wandb_track=false \
  output_dir=/data/vcc2026/runs \
  name=state_hvg_warmstart_trial_001
```

这些字段均能在固定 S1 YAML/训练入口找到。它们没有经过 Hydra/模型运行试验；真正开始前应进行 resolved config 和小批输入检查。batch_size=2、accumulation=8 表示单 GPU 每个优化步骤累计 16 个集合；每个集合 64 个细胞，最多约 1,024 个细胞的集合输入。集合采样可重复细胞，这不等于 1,024 个互不重复的实验样本。验证间隔按 Lightning 的训练批次语义解释，不能在梯度累积后把它机械等同为相同数量的 optimizer steps。

若必须保持发布 batch_encoder=true，则要先解决旧/新 batch 字典的对应关系，不应只改这一行。若使用 H2，至少同时改为它的 checkpoint/特征/基因资产、`embed_key=null`、`output_space=all` 与严格对齐的 6,546 genes；只改 checkpoint 路径不成立。

## 8. 哪些内容必须自己实现或验证

| 需求 | 原生支持情况 | 项目工作 |
|---|---|---|
| 同结构参数初始化 | 已有 `model.kwargs.init_from` | 核对数据语义，输出逐层/按模块的加载报告 |
| 恢复同一个训练过程 | run 下 `last.ckpt` 自动优先 | 保留原 config、映射与数据合同，避免误续训 |
| 跨基因轴按名称迁移 | 原生仅按 tensor 名/shape | 显式复制共同基因行列；记录新增/遗漏与 mask |
| 跨靶点 one-hot 词表迁移 | 原生没有语义映射 | 按名称迁移列，或替换为来源明确的连续特征 |
| 同维但不同特征语义 | 原生会误认为可复制 | 迁移器显式排除对应权重，不能靠 shape 过滤 |
| 保留旧 batch embedding 的含义 | 原生训练重新生成映射 | 显式映射旧/新 batch；设计未知标签处理 |
| 只训练新头，随后逐层解冻 | 原生没有完整分阶段训练器 | 设 requires_grad 与优化器参数组，保存阶段边界 |
| 不同模块不同学习率 | 当前优化器统一 `lr` | 自写 optimizer 分组；重新初始化 optimizer 的决策明确化 |
| bf16 混合精度 | 当前 STATE Trainer 未接 `precision` | 增加 Trainer 配置并验证 energy loss 数值稳定性 |
| 18,533 genes 的整数计数输出 | 原生 infer 不能直接满足 | 计数解码/采样、文库量、整数检查、官方提交封装 |
| 原始计数矩阵上的损失 mask | 不能把缺测基因当零监督 | 预处理与 loss 联合支持缺失基因 mask |

特别注意两个看似方便的开关：

1. **`freeze_pert_backbone=true` 不是“只冻主干”。**源码冻结 `transformer_backbone` 的非 LoRA 参数，同时冻结 `project_out`；没有冻结 `pert_encoder` 和 `basal_encoder`。若扩基因后 `project_out` 是新随机层，这个开关也会冻结它。来源 [S1 L296–307](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/tx/models/state_transition.py#L296)。头部 warm-up 应自行按模块指定可训练参数，不要只靠开关名推断行为。
2. **不能未经核验就组合普通 base checkpoint 与 `lora.enable=true`。**模型构造时先调用 `apply_lora`，该函数通过 PEFT `get_peft_model` 包装主干，而 `init_from` 随后仅按完整 state_dict key 精确匹配。PEFT 通常引入 `base_model.model`、`base_layer` 等键名，因此存在普通 checkpoint 主干参数被跳过的明确风险。来源 [S1 L361–367](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/tx/models/state_transition.py#L361)、[utils L154–192](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/tx/models/utils.py#L154)、[train L369–383](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/_cli/_tx/_train.py#L369)。本轮未实例化 PEFT，故把它记录为必须验证的兼容性风险。可靠路径是先成功装载 base 参数再注入 LoRA，或显式重映射并验证权重一致；不要声称只加 enable 就已完成低成本微调。

## 9. 预训练暴露决定 LOCO 是否可信

LOCO（leave-one-context-out，留出整个细胞背景）要求模型训练没有用到该背景的扰动表达。**在微调 TOML 里留出某背景，不能消除预训练权重已经看过它的事实。**

H1 不是仅有 run 名暗示：官方 S1 [`jurkat_zeroshot.toml` L1–14](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/state_preprint_toml_files/replogle_tomls/jurkat_zeroshot.toml#L1) 明确写：

```toml
[datasets]
replogle = "/data/replogle_nogwps_v2"
[training]
replogle = "train"
[zeroshot]
"replogle.jurkat" = "test"
```

但 H1 实际发布 config 和 `data_module.torch` 存的是作者本机 `/large_storage/ctc/userspace/aadduri/revisions/replogle_nogwps_v2/jurkat_zeroshot.toml` 路径；小型 artifact 没有携带当时的 TOML 内容、哈希、训练文件清单或细胞 barcode manifest。因此可表述为**官方发布命名与配置指向 Jurkat 留出协议，仓库存在一致的明确划分例子**；还不能表述为已经逐细胞审计了实际 checkpoint 的训练暴露。不同 run 之间也不能自行推广这一结论。

H2 指向 `/data/replogle_llm/k562.toml`，并记录 `downsample=0.99`。仓库 [同名 k562.toml](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/state_preprint_toml_files/replogle_tomls/k562.toml#L1) 展示的是 fewshot 靶点留出而不是整个 K562 留出；其数据路径又不相同，不能直接证明 H2 的实际划分。`k562_0.99` 不能当作“只训练 K562”或“从未看过 K562”的证据。

工程建议：首个兼容试跑优先选 H1 的 zeroshot run，并把其对应背景作为可进一步核实的开发划分候选。正式报告列出预训练来源、已知背景/靶点暴露、微调暴露与仍缺 manifest 的项目；若需要严格干净 LOCO，应取得可核验的匹配预训练划分，或另用数据来源能够审计的 checkpoint。H1 比赛开发集是否未暴露，也不能仅凭模型 repo 名推断。

## 10. 资源估计的可用事实与缺口

本轮可引用的资源事实只有发布文件字节大小、已读架构维度，以及从矩阵形状推导的参数项。`mfu_kwargs.available_flops=6e13` 是配置里的归一化基准，不能反向当作真实 GPU 型号或训练吞吐证据；发布 max_steps 也没有 wall-clock 时间。

训练资源预算必须分开列出：模型与 Adam 状态、集合长度与 batch 导致的激活、energy loss、输入解压/密集化的 CPU 内存、数据落盘与 checkpoint 保留。微调通常减少需要重新学习的内容和搜索量，**不自动减少全参数反传的显存**。冻结参数/LoRA 主要改变梯度和优化器状态，前向激活与新全基因头仍然占内存。

在获得至少一次 100–200 steps 试跑前，“1 张 24/48/80 GB 卡、若干小时”等只能作为规划档位，不得写成已验证能够容纳或已保证完成的数值。应记录实际加载参数占比、可训练参数量、最大 CUDA allocated/reserved、CPU RSS、数据读取时间、稳定 step 时间、验证开销、样本与集合数，再外推训练时长。官方 manual-init 会 `torch.load(..., map_location=cuda)` 读取完整 checkpoint；若存在优化器状态，其瞬时/保留内存也需计入测量。[S1 `_train.py` L308–311](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/_cli/_tx/_train.py#L308)

## 11. 本轮台账与未解决项

| 操作 | 次数 | 结果 |
|---|---:|---|
| Scholar/SciVerse 或其他主题发现 | 0 | 复用已评估 State 材料，不需要扩搜 |
| 固定 revision HF tree API | 2 | 2 成功，得到当前 run 文件大小与 LFS SHA |
| 固定 revision 小型 data_module.torch | 2 | 2 成功，各 1,901 bytes，只检查序列化结构 |
| 新增模型/数据大文件下载 | 0 | 未发生 |
| 模型实例化、PyTorch 权重加载、GPU 运行 | 0 | 未发生 |

本地工具检查中系统 Python 无 PyYAML；改为仅按 YAML 明确的简单 scalar 字段与 `gene_names` 列表读取，没有为此安装依赖。其余本地路径搜索的不存在路径已修正，不属于网络失败。

仍需完成：真实 checkpoint 的软件兼容加载；训练样本来源 manifest；发布输入归一化精确尺度；2,024 靶点映射和 VC2026 面板交集；新 batch 处理与各模块迁移报告；LoRA 装载验证；新全基因输出与 raw counts 生成；实际硬件资源与官方六指标验证。本文没有新增候选论文；State 在参考文献索引中的既有条目由主教程任务统一补链接。

## 12. 教程定向复核补充：对照匹配、HVG 与 checkpoint 时机

本节仍为上述固定版本的本地静态读取，没有新增网络请求或训练。

### 12.1 `basal_mapping_strategy=batch` 不等于禁止 fallback

原生 `data.kwargs.basal_mapping_strategy=batch` 同时影响对照选择与集合采样。`BatchMappingStrategy` 在每个 dataset/split 内以 `(batch, cell_type)` 建立 NTC 池，先从同批次同背景抽样；若缺少该池，会退回同背景的其他批次。来源：[S2 batch.py L14–20、L57–74、L149–168](https://github.com/ArcInstitute/cell-load/blob/9ba45e59f6f8117bb7a21371ad38d67175586d53/src/cell_load/mapping_strategies/batch.py#L149)。数据模块还将 `use_batch=true` 传给集合 sampler，[S2 datamodule L467–479](https://github.com/ArcInstitute/cell-load/blob/9ba45e59f6f8117bb7a21371ad38d67175586d53/src/cell_load/data_modules/perturbation_dataloader.py#L467)。

教程中要求 `context × target × batch` 集合及 `context × batch` NTC 时，应显式给上述参数，并在**每个实际 dataset/split** 内检查 NTC 覆盖。仅在全部数据合并后发现同名 NTC 还不足以阻止分文件或切分后的 fallback。该检查未集成到当前原生开关，应由项目预检拒绝缺对照的条件。

### 12.2 raw `.X` 与 log `X_hvg` 可以共存，但 metadata 必须一致

`embed_key=X_hvg` 时，单行与批量主输入/监督直接读取 `/obsm/X_hvg`，不会取 raw `.X` 替代；`_fetch_obsm_expression_batch` 只取浮点矩阵，没有再次 log/exp 变换。[S2 mapping L100–110](https://github.com/ArcInstitute/cell-load/blob/9ba45e59f6f8117bb7a21371ad38d67175586d53/src/cell_load/mapping_strategies/mapping_strategies.py#L100)、[dataset L431–454](https://github.com/ArcInstitute/cell-load/blob/9ba45e59f6f8117bb7a21371ad38d67175586d53/src/cell_load/dataset/_perturbation.py#L431)、[L1067–1084](https://github.com/ArcInstitute/cell-load/blob/9ba45e59f6f8117bb7a21371ad38d67175586d53/src/cell_load/dataset/_perturbation.py#L1067)。

`is_log1p` 参数描述 `.X`，主要影响 counts downsampling 的 exp/log 处理；它不是声明 `X_hvg` 是否 log 的开关。在 `.X` 保存 raw counts、`X_hvg` 保存旧尺度表达的方案中可显式用 `+data.kwargs.is_log1p=false`，且 `model.kwargs.log1p_from_raw_counts=false`。HVG 路径下原生 downsampling 不执行，因此将此字段误设 true 不会立即改变主 HVG 数值，但其含义仍应纠正。[S2 dataset L777–786](https://github.com/ArcInstitute/cell-load/blob/9ba45e59f6f8117bb7a21371ad38d67175586d53/src/cell_load/dataset/_perturbation.py#L777)

名称合同不能只写 `.var_names` 与 `X_hvg`：`get_gene_names(output_space=gene)` 优先 `var/gene_name`，有 `var/highly_variable` 时按该 mask 过滤，缺 mask 时才尝试 `uns/hvg_names`；落到 `var/_index` 的最后 fallback 分支时并不读取 `uns/hvg_names`。[S2 dataset L1163–1212](https://github.com/ArcInstitute/cell-load/blob/9ba45e59f6f8117bb7a21371ad38d67175586d53/src/cell_load/dataset/_perturbation.py#L1163)

工程准备应明确写入 `.var['gene_name']` 与同 `X_hvg` 完全同序的 `.uns['hvg_names']`，移除冲突的 `.var['highly_variable']` 或证明它选出的有序名单完全一致。最终直接断言 `data_module.get_var_dims()['gene_names'] == parent_gene_names`，不能只核对维数。每个来源还必须确实测过这 2,000 genes；缺测时，同样不能默默补零当真值。跨来源 mask 边界也适用于 HVG 训练，不仅适用于全基因路线。

### 12.3 禁用辅助 decoder 的准确含义

`+model.kwargs.gene_decoder_bool=false` 是原生可用附加字段，基类 `_build_decoder` 会令 `gene_decoder=None`；随后 manual init 会跳过父 checkpoint 中不再存在的该模块参数。它保留 ST 的 `project_out` 主输出。来源：[S1 base.py L244–252](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/tx/models/base.py#L244)。

要避免夸大这个开关的影响：当前 loader 在 `embed_key=X_hvg, output_space=gene` 时本来就令 `store_raw_expression=false`，不会添加 `pert_cell_counts`，因此通常不触发辅助 decoder loss；`embed_key=null, output_space=all` 也得到 false。[S2 datamodule L203–210](https://github.com/ArcInstitute/cell-load/blob/9ba45e59f6f8117bb7a21371ad38d67175586d53/src/cell_load/data_modules/perturbation_dataloader.py#L203)。ST 只在 `gene_decoder is not None` 且 batch 有 `pert_cell_counts` 时计算辅助损失。[S1 L628–648](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/tx/models/state_transition.py#L628)

所以在该 pilot 中，禁用它首先是显式去除不参与主路径但仍占参数存储的辅助模块，并防止后续改变输入路线时无意引入另一条监督；它不是修复此 HVG 配置中已确定发生的重复 loss。资源统计需区分参数总量、requires_grad 参数量与本批实际有梯度的参数量。

### 12.4 `ckpt_every_n_steps` 当前没有接入 callback

固定 S1 [`get_checkpoint_callbacks` L130–149](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/tx/utils/__init__.py#L130) 接收名为 `_ckpt_every_n_steps` 的参数但完全没有使用它。实际构造为：

```python
ModelCheckpoint(
    filename="best", save_last=True, monitor="val_loss",
    mode="min", save_top_k=1, every_n_train_steps=val_freq,
)
```

因此配置 `training.ckpt_every_n_steps=500` **不会让原生代码每 500 步保存**。同一个 `val_freq` 在 Trainer 中作为 validation 的 microbatch 间隔，而在 callback 中作为 checkpoint 的 optimizer/global-step 间隔，梯度累积会使二者不一致。以 `val_freq=2000, accumulation=4` 为例，验证约每 500 optimizer steps，而保存触发间隔仍是 2,000 optimizer steps；还需按实际 Lightning 版本检查在验证之前/之后能拿到哪个 `val_loss`，不能承诺它保存了每次验证中最优的模型。

教程应删除关于该无效字段的生效承诺，或在项目训练器中明确修正 callback，使 checkpoint 按每次验证完成的指标选 best，并实现独立周期保存。`final.ckpt` 在训练结束时由训练入口另行保存，不等价于经过全部验证点选出的 best。本文第 7 节保留的原生字段骨架不能被解读为 `ckpt_every_n_steps` 已生效。
