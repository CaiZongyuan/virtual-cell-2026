# STATE 训练与推理源码核验

日期：2026-09-14。性质：官方源码与作者 Colab 的静态核验；未安装依赖、未下载训练数据或权重、未运行 GPU 训练。用于修订[首投方案](first-submission-plan.md)，不能把下列配置读取结果当作已复现的成绩或资源实测。

**结论：STATE 应是本项目必须复现的神经网络主基线。作者的 VCC starter 已经使用 ESM2 连续靶点特征，支持有特征的未见扰动；不能把“从 one-hot 改为 ESM2”包装为我们超越这个 starter 的新架构。** 当前官方 `model=state` 是 8 层、768 宽的细胞集合 Transformer，并且已经有全基因输出路径。真正需要完成的工作包括符合 2026 合同的数据划分、完整靶点覆盖、原始计数生成、可消融的模型改进，以及相同条件下的六指标比较。

## 固定来源

| 来源 | 本轮固定版本与入口 |
|---|---|
| 官方 STATE | commit `9bbfe78a434a55205e4de834e1ea99f85f7a3add`；[仓库快照](https://github.com/ArcInstitute/state/tree/9bbfe78a434a55205e4de834e1ea99f85f7a3add) |
| 官方数据加载器 cell-load | commit `9ba45e59f6f8117bb7a21371ad38d67175586d53`；源码版本号 `0.10.4`；[仓库快照](https://github.com/ArcInstitute/cell-load/tree/9ba45e59f6f8117bb7a21371ad38d67175586d53)。STATE 要求 `cell-load>=0.10.4`，正式环境仍需锁定全部依赖。 |
| 作者 VCC Colab | [公开 notebook](https://colab.research.google.com/drive/1QKOtYP7bMpdgDJEipDxaJqOchv7oQ-_l)；本轮通过 [Drive 下载入口](https://drive.google.com/uc?export=download&id=1QKOtYP7bMpdgDJEipDxaJqOchv7oQ-_l)读取 22 个 cells；下载内容 SHA-256 `0b3888b9a36e6fbfc056b9e5585d825aa5a97a92f34d3bc2ff69cba064f21422`。Colab 是可变文档，以下按本轮 cell 序号定位。 |

Colab 的数据说明仍然是 **2025 H1、200 个比赛 train/val targets**，下载 `competition_support_set.zip`，评估命令仍是旧 `cell-eval`。它是架构与训练入口的作者证据，不能直接冒充 2026 的零样本数据划分或打包规范。作者在 cell 21 明确称它为 baseline，并期望参赛者显著改进；cell 1 说明其适配了全转录组与未见扰动预测。Colab 未锁定代码版本，表中“未覆盖”对应的是将该命令用于本轮固定代码时继承的值，不证明作者最初运行 notebook 时使用相同默认值。

## 官方默认、作者 Colab、项目拟定要分开

| 项目 | 当前 `model=state` / training 默认 | 作者 VCC Colab cell 14 的显式覆盖 | 对项目的意义 |
|---|---|---|---|
| 主干 | 双向 Llama Transformer，8 层 | `model=state`，未锁 commit | 我们锁源码，再保留此架构作主基线 |
| 隐藏维度 / FFN | 768 / 3072 | 未覆盖 | 不用 256 宽的小 MLP 替代 |
| attention heads / KV heads | 12 / 12，head dim 64 | 未覆盖 | 无旋转位置编码，细胞之间双向注意力 |
| 细胞集合大小 | `cell_set_len=512` | 未覆盖 | 512 是每个集合的细胞数，不是基因数 |
| 编码 / 投影层 | `n_encoder_layers=1`、`n_decoder_layers=1` | 未覆盖 | 这里一层就是 Linear；主干仍为 8 层 Transformer |
| 残差 | `predict_residual=true` | 引言说明把残差移到最终表达空间 | 全基因路径还有下文列出的额外基因混合层 |
| 主损失 | `loss=energy`、`distributional_loss=energy` | 未覆盖 | 比较预测与真实细胞集合分布；不要求一对一的真实细胞匹配 |
| 靶点特征 | 不提供特征文件时为 one-hot | `ESM2_pert_features.pt` | 已有连续特征版本，不是只能预测训练词表内靶点 |
| 输入 / 输出 | `embed_key=null`、`output_space=all` | 未覆盖 | 从 `.X` 输入，并按完整基因轴预测；与 `X_hvg` 路线不同 |
| 学习率 | `training.lr=1e-4` | 未覆盖 | 可直接作为首次复现起点 |
| 优化器 | 源码实际 `torch.optim.Adam(..., lr=self.lr)` | 未覆盖 | **不是 AdamW**；YAML 中 `weight_decay=0.0005` 未传入这个优化器；无源码内置 LR schedule |
| steps | `400000` | `40000` | 40k 是 Colab 的训练覆盖值，不是完整默认值，也不是实测收敛承诺 |
| batch / accumulation | 16 个集合 / 1 | 未覆盖 | 默认一次前向至多 16×512 个细胞；项目可先用较小 microbatch 和梯度累积测内存 |
| 验证 / checkpoint | 每 2000 steps；clip=10；seed=42 | checkpoint 每 20000 | 正式记录 best/last/final 的选择规则 |
| 精度 | STATE 的 Trainer 未传 `precision`，为 Lightning 默认；另设 float32 matmul precision `medium` | 未覆盖 | **STATE 默认没有自动启用 bf16**。源码中的 `bf16-mixed` 只在 scGPT 分支。项目使用 bf16 必须补 Trainer 配置并验证数值。 |

字段来源：[state.yaml](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/configs/model/state.yaml)、[training/default.yaml](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/configs/training/default.yaml)、[data/perturbation.yaml](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/configs/data/perturbation.yaml)、[优化器](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/tx/models/base.py#L438)、[Trainer 构造](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/_cli/_tx/_train.py#L243)。

另有 `model=state_sm`：4 层、672 宽、8 heads、cell set 128，编码/解码各 4 层。这是独立配置，不能把它标成上述标准 STATE。共享 2,000 HVG 的评估版本也需显式指定 `embed_key=X_hvg` 等参数并标注为项目的匹配协议，不能称为逐字复现上述全基因 starter。`training.loss_fn=mse` 虽存在于通用配置，但 ST 初始化又用 `model.kwargs.loss` 构造实际集合损失；不能据此宣称默认 STATE 是 MSE 训练。[构造位置](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/tx/models/state_transition.py#L171)

## 实际网络与未知背景边界

细胞集合指同一背景、同一扰动条件下的一批细胞。每个细胞作为一个 token；一个 token 的输入包含多个基因的表达，不是一个基因对应一个 token。对照细胞给出扰动前状态，连续靶点向量指定要压低的基因。

```text
对照表达 x_i（G 维） ─ Linear(G, 768) ─┐
靶点特征 e_t（D 维）─ Linear(D, 768) ─┴─ 相加
    → 8 层双向集合 Transformer
    → Linear(768, G)
    → 加回对照 x_i
    → Linear(G, G//8) → GELU → Linear(G//8, G)
    → ReLU → G 维预测
```

这是当前 `embed_key=null, output_space=all, predict_residual=true` 的源码路径。[网络构造与 forward](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/tx/models/state_transition.py#L330)；[双向 attention 和禁用 RoPE](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/tx/models/utils.py#L197)。虽然配置有 `softplus=true`，此路径末端实际调用 `ReLU`，不能仅据 YAML 写成 Softplus 输出。

额外 `G→G//8→G` 层影响资源估计。若 `G=18,533`，仅这块就约 8,587 万参数（含 bias）；8 层 Transformer 主干约 7,551 万。若靶点特征恰为 5,120 维，按源码矩阵形状手算约 1.94 亿可训练参数，另有被冻结的 token embedding；**特征实际维度和完整参数数目应在初始化时打印确认**。这不是已经用 PyTorch 实例化得到的实测值。移除这块混合层属于我们改变架构的消融，不应悄悄称为原版复现。

ST 的 forward 默认只使用 `ctrl_cell_emb` 与 `pert_emb`；`cell_type_onehot` 没有进入预测网络。`cell_type_key` 主要参与数据分组、对照匹配和留出划分。因此匿名新背景可由真实 NTC 表达提供上下文，并不需要给 A/B/C 猜一个训练细胞系身份。

默认 `batch_encoder=false`、`use_batch_token=false`。若开启 batch encoder，推理遇到未见 batch label 会回退索引 0；这不等于学会新批次。首个严格零样本复现保持关闭，同时保证每个预测组都有自己的对照细胞，阻止 infer 的“该组没有对照便取全局对照”fallback。[batch 和对照 fallback](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/_cli/_tx/_infer.py#L654)

## ESM2 与未见靶点

ESM2 是从蛋白质氨基酸序列学习特征的预训练模型。它为编码蛋白质的靶基因提供可共享的连续输入，使网络能接收训练期间没有对应扰动标签的靶点；有输入不等于已证明能预测准确。首轮复现复用特征文件，不需要重训 ESM2。

`perturbation_features_file` 接受 `{target_name: tensor}` 字典。cell-load 将**完整字典**保存为 `pert_onehot_map`，不裁成训练中出现的靶点；文件名虽然含 onehot，内容实际可以是 ESM2 特征。`pert_dim` 从字典首个向量读取。[特征加载](https://github.com/ArcInstitute/cell-load/blob/9ba45e59f6f8117bb7a21371ad38d67175586d53/src/cell_load/data_modules/perturbation_dataloader.py#L566)、[维度读取](https://github.com/ArcInstitute/cell-load/blob/9ba45e59f6f8117bb7a21371ad38d67175586d53/src/cell_load/data_modules/perturbation_dataloader.py#L345)

两处默认 fallback 必须在项目入口改成明确失败并报告缺口：

1. 训练数据出现字典中不存在的靶点，cell-load 自动填零向量。
2. infer 出现保存映射中不存在的靶点，自动使用对照向量；缺少对照向量时另构造占位向量。[推理回退](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/_cli/_tx/_infer.py#L756)

在第一次 GPU 训练前，逐项核对所有训练靶点、H1 126 靶点、官方目标面板与 `non-targeting`。保存名称映射、维度、有限值、非意外零向量、来源和 SHA。旧 Colab 的支持包不能假定覆盖 2026 面板。无编码蛋白或无法确定序列的靶点，应先补有来源的备用表示或显式设计缺失标记，再通过同样目标留出验证；不能静默预测成 NTC。公开目标名称与序列特征可以在划分前准备，但目标背景的扰动表达标签不能用于训练或特征拟合。

## 全基因、log1p 与原始计数

`output_space=gene` 在训练器中使用 `hvg_dim`；`output_space=all` 使用 `gene_dim`。这两个命名描述基因轴范围，**不保证数值是 raw counts**。[输出维度选择](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/_cli/_tx/_train.py#L111)

官方 `preprocess_train` 会对 `.X` 做总量归一化和 log1p，再存 `X_hvg`；其中 `normalize_total(adata)` 没有显式指定 10,000。因此我们若约定 CP10K，必须自己固定 target_sum，并在训练、推理、评价中保持一致，不能从 README 猜预处理尺度。[预处理实现](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/_cli/_tx/_preprocess_train.py#L55)

当前源码也支持 `.X` 保留 raw counts、`model.kwargs.log1p_from_raw_counts=true`：进入 training/validation/predict step 时按 `counts_target_sum` 归一化，再取 log1p。若采用此路径，需显式 `+data.kwargs.is_log1p=false`；这个 loader 字段不在 STATE YAML 中，所以 Hydra 要用 `+`。不要同时让上游预处理和模型重复归一化。[模型归一化](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/tx/models/base.py#L212)、[loader 参数](https://github.com/ArcInstitute/cell-load/blob/9ba45e59f6f8117bb7a21371ad38d67175586d53/src/cell_load/data_modules/perturbation_dataloader.py#L60)

infer 写出的是浮点预测，基因空间值会 clip 到 `[0,14]`，不会自动逆归一化、恢复文库量或采样整数。代码变量名 `counts_preds` 也不足以证明结果满足 2026 raw counts 合同。[裁剪与保存](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/_cli/_tx/_infer.py#L919)

因此，首个 STATE 2026 版本仍需要独立可验证的 counts 输出接口；改进版可以训练计数分布头，但那属于我们增加的模块。所有候选共享同一基因顺序、raw counts 检查与采样种子，避免把生成器差异误判为主干提升。

各数据集必须先对齐全基因轴并记录实测/缺失基因 mask。`embed_key=null` 的主路径按输入矩阵位置读取，不能假定自动校正跨文件基因顺序；缺测基因也不能当作真实零表达监督。如果只做 HVG 训练，未建模基因要有明确补全策略；把其余基因置零不是完整基因预测。

infer 会先把整个输入 `.X` 转为 dense，并持有预测副本。[输入读取](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/_cli/_tx/_infer.py#L636)。项目应按单背景、少量靶点分片推理，再写稀疏输出；全量打包的 CPU 峰值另测，不能用 GPU 显存代替系统内存预算。

## 可核查的命令骨架

以下是**尚未执行**的原生字段骨架。文件路径是计划中的输入产物；需要完成数据对齐、特征覆盖检查与依赖锁定后才具备可运行条件。Microbatch 2、累积 8 和 2,000 steps 是本项目 pilot 配置；主干仍为官方标准结构。没有假设未实现的 bf16 开关已经生效。

```bash
state tx train \
  model=state \
  data.kwargs.toml_config_path=/data/vcc2026/splits/loco_jurkat.toml \
  data.kwargs.embed_key=null \
  data.kwargs.output_space=all \
  data.kwargs.pert_col=target_gene \
  data.kwargs.cell_type_key=context_id \
  data.kwargs.batch_col=batch_id \
  data.kwargs.control_pert=non-targeting \
  data.kwargs.perturbation_features_file=/data/vcc2026/features/esm2_all_targets.pt \
  data.kwargs.num_workers=8 \
  +data.kwargs.is_log1p=false \
  model.kwargs.log1p_from_raw_counts=true \
  model.kwargs.counts_target_sum=10000 \
  model.kwargs.batch_encoder=false \
  model.kwargs.use_batch_token=false \
  training.batch_size=2 \
  training.gradient_accumulation_steps=8 \
  training.lr=0.0001 \
  training.max_steps=2000 \
  training.val_freq=2000 \
  training.ckpt_every_n_steps=2000 \
  training.train_seed=42 \
  training.devices=1 \
  use_wandb=false \
  training.wandb_track=false \
  output_dir=/data/vcc2026/runs \
  name=state_loco_jurkat_pilot
```

整背景留出 TOML 语法来源于 [官方 zeroshot 示例](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/examples/zeroshot.toml)：

```toml
[datasets]
public_crispri = "/data/vcc2026/aligned_training/"

[training]
public_crispri = "train"

[zeroshot]
"public_crispri.Jurkat" = "test"
```

这只展示原生留出字段。正式运行另指定合法验证切分，不能把 test loss 用于选 checkpoint；`context_id` 大小写必须与真实 `obs` 一致。H1 若作为开发集，要剔除 H1 扰动表达训练暴露；作者 2025 starter 的 H1 混训结果不进入这项干净比较。

原生推理可以给某一背景的 NTC 文件加 TSV。TSV 两列是 `perturbation`、`num_cells`，每个目标 400 行输出。示例只针对一个背景，输出仍是中间浮点表达：

```bash
state tx infer \
  --model-dir /data/vcc2026/runs/state_loco_jurkat_pilot \
  --checkpoint /data/vcc2026/runs/state_loco_jurkat_pilot/checkpoints/final.ckpt \
  --adata /data/vcc2026/infer/A_controls_aligned_raw.h5ad \
  --pert-col target_gene \
  --celltype-col context_id \
  --control-pert non-targeting \
  --tsv /data/vcc2026/infer/A_targets_shard_001.tsv \
  --max-set-len 512 \
  --seed 42 \
  --output /data/vcc2026/predictions/A_state_logcp10k_shard_001.h5ad
```

原生 infer 会保留并模拟输入对照行，输出转换器还要只提取正式目标行、检查每靶点 400 cells。不要直接用 `--all-perts`，因为特征字典可以包含大量比赛面板外的基因。由于这是 pilot checkpoint，命令仅检查接口与资源，不是推荐向比赛提交 pilot 结果。

## 实施前必须消除的未核验项

- ESM2 文件实际维度、完整目标覆盖和来源；旧支持包的预处理尺度及 H1 暴露。
- 18,533 基因轴在训练来源中的实测覆盖；不完整监督如何加 mask。
- bf16 的实际 Trainer 补丁、energy loss 数值稳定性、实测参数量、显存、CPU RSS、step 时间。
- 将全基因 log1p 预测转为符合 2026 合同的整数分布，以及新增计数头的真实收益。
- 真实 source→loader→ST→infer→counts→cell-eval2 六指标端到端试跑。没有该结果，就不能声称改进优于 STATE。

本轮检索台账：先复用 `docs/references/INDEX.md` 与既有方案，不新增主题发现；Scholar / SciVerse 调用为 0。直接一手访问为两个 GitHub 仓库各一次 `ls-remote` 和一次 shallow clone，加一次 Colab 下载，共 5 个网络操作，均成功。源码与带内嵌图片的 notebook 保存在 `/tmp/`；正文只保存核验结论、必要命令、commit 和校验和，没有将候选图片、数据或权重纳入 Git。

## 已发布检查点补充：不必从零训练

用户询问是否必须重训后，2026-09-14 直接核验了 Arc 官方 Hugging Face 模型列表与文件树。**已有预训练 ST 权重，不能只依据训练教程默认所有模型都要从零训练。**

| 官方资源 | 本轮固定 revision | 已确认内容 |
|---|---|---|
| [ST-HVG-Replogle](https://huggingface.co/arcinstitute/ST-HVG-Replogle) | `bb6a9562cbbf1fd152df14cc53b4cc7517c77175` | fewshot/zeroshot 各背景的 best/final/last checkpoint、config、维度与映射文件 |
| [ST-SE-Replogle](https://huggingface.co/arcinstitute/ST-SE-Replogle) | `e324967ff4cea5ec199e29bcbb5c1f00e5b9d69c` | 相应 checkpoint 与配置；SE 输入路线需额外嵌入生成 |
| [st-x-replogle-full](https://huggingface.co/arcinstitute/st-x-replogle-full) | `48ad5f70215ab4c58caa5a68e77d837601d29d35` | 四个 `*_0.99` run 的 checkpoint 与配置；不能据名称推断训练/留出范围 |
| [st-se-replogle-full](https://huggingface.co/arcinstitute/st-se-replogle-full) | `d1441f5587ace12c46247b3703c7d25f24f8abb6` | 对应 SE 路线 checkpoint 与配置 |

四个模型 API 都返回 `gated=false`，但这不是许可证或商业使用授权判断。前三轮已经记录官方比赛用途说明；下载使用具体权重时仍需对应核对条款与训练来源。本轮四个 README 请求均 404，不能从缺 model card 推断缺权重；文件树和小型配置提供了更直接证据。

本轮实际读取两组固定 revision 的 config 与 hparams：

| 字段 | `ST-HVG-Replogle/zeroshot/jurkat` | `st-x-replogle-full/k562_0.99` |
|---|---:|---:|
| input / output dim | 2,000 / 2,000 | 6,546 / 6,546 |
| hidden dim | 328 | 328 |
| Transformer layers | 8 | 8 |
| cell set length | 64 | 64 |
| pert dim | 2,024 | 2,024 |
| pert features | one-hot，feature file=null | one-hot，feature file=null |
| batch encoder | true | true |
| 输入 / 输出 | X_hvg / gene | null / all |

所以三个概念不能混用：当前源码默认的 768 宽模型、作者 VCC Colab 的 ESM2 starter、实际已发布的这两组 328 宽 one-hot 权重。`full` 示例也只输出 6,546 genes，不是比赛 18,533。

正确执行顺序是：检查既有 checkpoint 的训练暴露/基因/靶点/版本 → 小批加载与推理 → 补提交适配 → 需要时替换/微调靶点和输出层 → 最后才考虑全量重训。改变输入输出基因轴时，相关 Linear 与 G→G//8→G 权重必须按真实结构迁移，不能简单 `strict=False` 后假定复用了完整模型。若增加 ESM2 编码器，其新参数需要训练，但不等于将所有 Transformer 权重随机重置。

另读取作者 [Tahoe inference notebook](https://colab.research.google.com/drive/1bq5v7hixnM-tZHwNdgPiuuDo6kuiwLKJ)，其 cell 5 下载 `arcinstitute/ST-HVG-Tahoe`，cell 9 直接调用 `state tx infer`；这证明已有 ST 支持直接推理流程，但 Tahoe 是药物任务，不能直接替代 CRISPRi checkpoint。

新增访问共 15 次 HTTP：2 次 HF 模型列表（带 `search=state` 的第一次为空，因为命名含 ST/SE，不能据此说不存在）、4 个模型元数据、4 个 README、4 个 YAML、1 个 notebook。11 次成功，4 次 README 404。没有下载 checkpoint/映射二进制、加载权重或运行预测；特征覆盖、训练暴露、许可适用性和真实推理能力仍待下一步验证。本轮不新增 Scholar/SciVerse 查询。
