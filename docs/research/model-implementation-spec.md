# VC2026 分解式模型实现规格 v0.1

> 当前执行方案已于 2026-09-14 重制为 STATE 主基线及全基因改进版；本文保留为历史研究，资源请求和模型顺序以[首投方案](first-submission-plan.md)为准。

> 日期：2026-08-31
> 状态：可进入实现的工程规格；尚未经过离线 LOCO 实验验证
> 上游决策：[STATE 后架构调查](post-state-architecture-review.md)
> 容量依据：[数据与算力容量规划](data-compute-capacity-sources.md)

本文把“response-aligned target effect + 保守 context gate + NTC-conditioned count emitter”细化为可编码、可测试和可逐项淘汰的系统。文中明确区分：

- `[官方合同]`：比赛输入、输出或评分的硬约束；
- `[论文边界]`：原论文实际证明或明确未证明的能力；
- `[工程规格]`：本项目现在决定实现的行为；
- `[待验证]`：只能由严格离线实验决定的假设。

## 1. V0 要交付什么

V0 不是最终冠军模型，而是第一个完整、可审计的纵向切片：

```text
公共 CRISPRi -> canonical effect bank -> Ridge target-effect model
                                            |
匿名背景 NTC -> identity context gate -------+
                                            |
                                  delta_log_rate [300, 18533]
                                            |
匿名背景 NTC -> molecule-transport emitter --+-> 400 raw-count cells / target
                                            |
                                  exact evaluator + submission validator
```

V0 必须回答三个问题：

1. 跨背景保守的 target effect 是否稳定胜过 NTC/null 和 target mean；
2. 同一个群体 delta 能否生成不破坏官方 DE 统计的 400-cell raw counts；
3. 每个后续模型改动能否只替换一个模块，而不改数据、评分或提交路径。

V0 明确不做：从头预训练 STATE/X-Cell/Lingshu、硬猜 A/B/C 身份、自由生成高维 context interaction、根据排行榜反推伪标签，以及把未测基因当作生物学零表达。

## 2. 系统中的五个深模块

这里使用“模块、接口、seam、adapter”的工程含义。只有已经存在至少两个实现的位置才建立 seam；单一实现不增加抽象层。

| 模块 | 小接口 | 隐藏的复杂度 | seam / adapter |
|---|---|---|---|
| Canonical Corpus | `build_corpus()`、`open_corpus()` | H5AD/RDS 读取、gene mapping、原始计数核验、批次匹配、effect bank、checksum | 真实 seam；H5AD 与 RDS source adapters |
| Effect Modeling | `fit_effect_model()`、`predict_effects()` | response PCA、target memory、prior 映射、context gate、图残差、缺失模态、uncertainty | 真实 seam；Mean/Ridge/MLP/AdaGraph/STATE adapters |
| Count Emission | `emit_counts()` | NTC 平衡抽样、fold-change 到整数 UMI、过度离散、稀疏写出、library-size QC | 真实 seam；MoleculeTransport/NB/Lingshu adapters |
| Evaluation Protocol | `evaluate_run()` | split 权限、六项指标、scaled anchors、Monte Carlo 汇总、破坏实验 | exact cell-eval 与无真值 contract-check adapters |
| Submission | `write_prediction()` | 360k 行流式 CSR、obs/var 顺序、显式零、H5AD/VCC 校验 | 当前只有一个实现，不建立 adapter seam |

删除任一模块后，其复杂度都会重新散落到多个训练脚本和 notebook，因此这些模块具有实际深度。Source adapter、effect model adapter 和 count emitter adapter 是内部 seam；不把它们全部暴露给 CLI 调用者。

## 3. 统一领域对象

### 3.1 GeneAxis

```python
GeneAxis(
    symbols: tuple[str, ...],       # 长度固定为 18_533
    symbol_to_index: Mapping[str, int],
    sha256: str,
)
```

不变量：

- `[官方合同]` 顺序必须与当轮 `gene_names.csv` 完全一致；
- symbol 唯一，不允许隐式 Ensembl/symbol 多对一；
- 所有 artifact 保存 `gene_axis_sha256`，hash 不同即拒绝拼接；
- source 未测某基因由 `measured_mask=False` 表示，不能用 count/effect `0` 代替。

### 3.2 ConditionKey

```python
ConditionKey(
    study: str,
    assay: str,
    context: str,
    target: str,       # control 统一写 non-targeting
    batch: str,
)
```

`study + assay + context + target + batch` 是最小防泄漏分组。原 accession、guide、cell barcode 和源文件 checksum 作为附加 provenance 保存，不塞进训练 feature。

### 3.3 ControlContextRef

```python
ControlContextRef(
    context: str,
    counts_uri: str,               # backed CSR/Zarr，不要求载入内存
    obs_uri: str,                  # cell_id, ntc_id, batch
    gene_axis_sha256: str,
    n_cells: int,
    qc: ControlQC,
)
```

`ControlQC` 至少包含 library-size、detected genes、zero fraction、每个 `ntc_id` 的细胞数和 pseudobulk rate。比赛输入中每个背景应为 18,400 cells、46 个 NTC guides、每 guide 400 cells。

### 3.4 EffectBank

EffectBank 是 source Perturb-seq 的训练事实表。高维数组使用 Zarr，条件与 provenance 使用 Parquet：

```text
effects.zarr
  delta_log_rate       float32 [condition, gene]
  standard_error       float32 [condition, gene]
  measured_mask        bool    [condition, gene]
  responsive_prob      float32 [condition, gene]
  direction_label      int8    [condition, gene]   # -1 / 0 / +1

conditions.parquet
  condition_id, study, assay, context, target, batch,
  n_perturbed, n_control, target_knockdown, source_checksum
```

`delta_log_rate` 的唯一含义是自然对数相对 rate：

```text
delta[c,t,g] = log(rate_perturbed[c,t,g]) - log(rate_ntc[c,g])
```

不能在同一字段混放 `log1p(CP10K)` 差、raw count 差或论文提供的 z-score。

### 3.5 TargetPriorBatch

```python
TargetPriorBatch(
    targets: tuple[str, ...],
    depmap: float32[T, D_depmap],
    esm2: float32[T, D_esm],
    string: float32[T, D_string],
    scalar_features: float32[T, D_scalar],
    availability: bool[T, 4],
    version_manifest: Mapping[str, str],
)
```

每种 prior 单独标准化并保留 availability mask。缺失 prior 用训练均值填数值、用 mask 告知模型，不允许把缺失误解释为真实零向量。

### 3.6 SplitManifest

```python
SplitManifest(
    protocol: str,
    train_condition_ids: tuple[str, ...],
    validation_condition_ids: tuple[str, ...],
    test_condition_ids: tuple[str, ...],
    held_out_contexts: tuple[str, ...],
    held_out_targets: tuple[str, ...],
    allowed_target_inputs: tuple[str, ...],
    allowed_context_inputs: tuple[str, ...],
    source_manifest_sha256: str,
    seed: int,
)
```

外层 test truth 只能被 Evaluation Protocol 打开。Effect Modeling 接收的是 `TrainingSlice` 和目标 NTC 引用，接口上不存在 `test_effects` 参数。

### 3.7 EffectPrediction

```python
EffectPrediction(
    targets: tuple[str, ...],
    delta_log_rate: float32[T, 18_533],
    responsive_prob: float32[T, 18_533],
    p_up: float32[T, 18_533],
    log_effect_norm: float32[T],
    epistemic_variance: float32[T, 18_533],
    source_weights: float32[T, S],
    manifest: PredictionManifest,
)
```

不变量：所有值有限；`responsive_prob`、`p_up` 在 `[0,1]`；未受任何 source 扰动监督且不在 core gene set 的基因默认 `delta=0`，同时 uncertainty 置高，而不是伪造效应。

### 3.8 CountPredictionRef

CountPrediction 不通过内存返回 360k x 18,533 矩阵，而返回分片 artifact 引用：

```python
CountPredictionRef(
    shards: tuple[Path, ...],
    n_cells: int,
    n_genes: int,
    stored_entries: int,
    gene_axis_sha256: str,
    manifest_path: Path,
)
```

每个 shard 是 CSR `int32`，禁止显式零。最终 obs 只包含 `target_gene` 和 `context` 所需字段，不把 template 的 `ntc_id` 写成预测细胞属性。

## 4. Canonical Corpus 的实现合同

### 4.1 Source adapter 输出

H5AD 和 RDS adapter 都只输出统一的 `CanonicalCellBatch`：

```python
CanonicalCellBatch(
    counts: BackedCSR,
    genes: tuple[str, ...],
    obs: DataFrame[cell_id, study, assay, context, target, guide, batch],
    provenance: SourceProvenance,
)
```

adapter 内部负责结构化解析，不能让下游按文件名猜 study/context。RDS 必须由固定版本的 R/Seurat 转换命令生成中间 H5AD/Zarr，并在 provenance 中保存脚本 hash。

### 4.2 Effect transform

对 condition `(c,t,b)`，先聚合 perturbed 和匹配 NTC 的 counts。用 NTC rate 作为 Dirichlet smoothing prior：

```text
base_rate[c,g] = Y_ntc[c,g] / sum_g Y_ntc[c,g]

rate[c,t,g] =
  (Y_pert[c,t,g] + tau * base_rate[c,g]) /
  (L_pert[c,t] + tau)
```

`tau` 首版只比较 `{5, 20, 100}`，由 inner folds 选择。标准误优先按 guide/batch 做 cluster bootstrap；没有 replicate 标识时才按 cell bootstrap，并在 manifest 标记较弱证据。

DEG 标签仅从训练 condition 计算：按官方代理流程做 CPM、双侧 Wilcoxon 和 condition 内 BH。外层 test DEG 只能由 evaluator 读取，不能参与 gene gate、loss weight 或 early stopping。

### 4.3 V0 core gene set

V0 不立即做带缺失值的 18,533-gene 矩阵分解：

1. 在每个 outer fold 的训练 sources 中求可靠 measured-gene 交集；
2. 只用训练 condition 的 between-perturbation variance 选 2,000 个 core genes；
3. response PCA 只在 core genes、训练 conditions 上拟合；
4. core 外但 target memory 有实测的基因使用收缩后的直接 source effect；
5. 从未受扰动监督的基因保持目标 NTC rate，不把 source 缺失填成 effect zero 后参与 loss。

`[待验证]` 只有 V0 证明有效后，才升级为带 `measured_mask` 的 full-gene weighted low-rank factorization。

## 5. Effect Modeling 细化

### 5.1 对外接口

```python
model = fit_effect_model(training_slice, target_priors, model_spec)

prediction = predict_effects(
    model=model,
    controls=target_control_context,
    targets=target_priors_for_request,
    seed=seed,
)
```

调用者不需要知道 response PCA、source retrieval、context gate 或 graph selector 的内部顺序。模型 artifact 必须包含训练 split hash、gene axis hash、prior 版本和可重放配置。

### 5.2 保守 target-effect 主干

先分别计算两个估计：

```text
d_memory(c,t) = sum_s w_s(c,t) * d_observed(s,t)
d_prior(t)    = U_response * h(target_prior(t))
```

- `d_observed(s,t)` 是 target 在 source context 的收缩 effect；
- `w_s` 由 source reliability 与 context gate 决定，非负且和为 1；
- `h` 首先是 Ridge，然后才是 2-layer MLP；
- `U_response` 是当前 outer fold 训练得到的 response basis。

有直接 memory 时按 uncertainty 做 precision blending：

```text
d_conserved =
  (precision_memory * d_memory + precision_prior * d_prior) /
  (precision_memory + precision_prior)
```

没有直接 memory 时退回 `d_prior`；prior 也缺失时退回训练 target mean，并将 uncertainty 置高。

### 5.3 方向与幅度分头

对训练 effect 定义：

```text
amplitude = log(||W_gene * delta||_2 + eps)
direction = delta / exp(amplitude)
```

Ridge/MLP 分别预测 response-PC direction 和 amplitude，最终相乘重建。这样 effect scale 可以单独校准，避免 PDS 方向正确但 MSE/NMAE 过冲或收缩。

V0 MLP 固定为两层 256 hidden units、ReLU、dropout 0.1；只有 Ridge 在所有 outer folds 通过后才训练。首轮不搜索深度，只搜索 response rank `{32,64,128}`、weight decay 和 amplitude loss weight。

### 5.4 Context gate 的能力上限

`[论文边界]` 纯 NTC 不能识别完整 `context x target` interaction。因此 V0 gate 只能输出：

```python
ContextGateOutput(
    source_weights: float32[S],       # simplex
    amplitude_multiplier: float,      # 初始限制 [0.5, 2.0]
    residual_release: float,          # 初始限制 [0.0, 0.25]
)
```

输入只含：

- NTC pseudobulk PCA 和 pathway scores；
- library size、detected genes、zero fraction；
- target 在当前 NTC 的表达；
- source 与 target NTC 的 Mahalanobis/cosine distance；
- target essentiality 和 prior availability。

V0 `IdentityGate` 使用可靠性加权 source mean、amplitude=1、residual=0。`NtcSimilarityGate` 只有在 identity gate 通过后实现。任何能直接输出 18,533-gene residual 的 gate 都超出 V0 权限。

### 5.5 AdaPert-lite，不先复刻完整 GAT

首版图模块把每个 `(target, response_gene)` 变成一行 pair features：

```text
STRING distance/confidence
DepMap coessentiality correlation
ESM2 cosine similarity
target / response-gene NTC expression
direct-memory delta and standard error
context pathway activity
```

一个共享 MLP 输出 `responsive_prob`、`p_up` 和小幅 residual。候选响应基因只取 STRING 1-2 hop、DepMap top neighbors 和 direct-memory top genes 的并集；soft top-k 比较 `{256,512,1024}`。首轮不使用 GPT 描述、Gumbel sampling 或全图 message passing。

图 residual 满足：

```text
||residual_graph||_2 <= residual_release * ||d_conserved||_2
```

只有 embedding-shuffle control 明显变差，且 LOCO 的 reach/NMAE 改善不以 MSE/PDS 退化为代价，才升级为完整 sparse GAT。

### 5.6 Loss 合同

训练 loss 只使用 training conditions：

```text
L = lambda_profile * Huber(delta_hat, delta)
  + lambda_direction * (1 - cosine(direction_hat, direction))
  + lambda_amplitude * Huber(amplitude_hat, amplitude)
  + lambda_deg * BCE(responsive_prob, training_DEG_label)
  + lambda_sign * BCE(p_up, training_direction_label)
  + lambda_rank * pairwise_target_rank_loss
```

默认只启用前三项；DEG/sign/rank 每次只加入一项做消融。官方 scaled score 是选择标准，loss 数值不是上线证据。

## 6. Count Emission 细化

### 6.1 对外接口

```python
prediction_ref = emit_counts(
    emitter=emitter_artifact,
    controls=control_context,
    effects=effect_prediction,
    cells_per_target=400,
    seed=seed,
    output_dir=output_dir,
)
```

Count Emission 不读取训练 truth，不修改 effect model，也不写最终 `.vcc`。它只负责从指定 effect 和目标 NTC 产生合法、可重放的 count shards。

### 6.2 400 个 template 的确定性平衡抽样

每个 target 从 46 个 `ntc_id` 无放回抽取 templates：

- 14 个 guides 各取 8 cells；
- 32 个 guides 各取 9 cells；
- 哪 32 个多取 1 个由 `(context, target, seed)` 的稳定 hash 决定；
- 同一 run 内不同模型必须使用同一份 template manifest，避免抽样噪声冒充模型收益。

template 的 `ntc_id` 只用于生成与审计，不进入最终预测 obs。

### 6.3 V0 MoleculeTransportEmitter

直觉：下调基因通过“稀释/删除已有 UMI”，上调基因通过“新增 UMI”实现。这样不会先构造 400 x 18,533 的 dense rate matrix。

对 context NTC rate `r_g` 和预测 `d_g`，先做 compositional centering：

```text
log_Z = log(sum_g r_g * exp(d_g))
fold_g = exp(d_g - log_Z)
```

因此 `sum_g r_g * fold_g = 1`。对 template cell `i`、library size `L_i`：

```text
fold_g <= 1:
    y_i,g ~ Binomial(x_i,g, fold_g)

fold_g > 1:
    y_i,g = x_i,g + Poisson(L_i * r_g * (fold_g - 1))
```

上调 support 仅包含 `responsive_prob >= q0` 或 top-k 响应基因；其余基因先令 `d_g=0` 再重新 center。首轮比较 `q0={0.25,0.5}`、`top-k={512,1024,2048}`。

随机采样后总 UMI 若偏离 `L_i`：

- 过多时按全细胞比例做 binomial thinning；
- 不足时按调整后 `r_g * fold_g` 从已有 support 补样；
- correction 量、最终 total 和 nonzero genes 必须写入 QC；
- 若超过目标 NTC library-size 的 `[0.5%,99.5%]` 范围则视为 emitter 失败，而不是静默裁剪。

V1 才把 Poisson addition 替换为按 source/NTC 校准的 Gamma-Poisson；V2 才考虑 ZINB 或 Lingshu residual adapter。

### 6.4 Emitter 不变量

- CSR `int32`，非负、有限、整数、无显式零；
- 每 cell 总 UMI `< 1_000_000`；
- 每 context-target 恰好 400 cells；
- gene 顺序严格等于 GeneAxis；
- 相同 seed 和相同 artifacts 统计级可复现；
- stored entries 低于官方上限并在生成中持续监控；
- `delta=0` 时输出必须退化为 NTC bootstrap，而不是另一种分布。

## 7. 防泄漏验证协议

### 7.1 三类外层 split

| 协议 | Train | Test 可见输入 | 回答的问题 |
|---|---|---|---|
| LOCO-seen-target | 3 个核心 CRISPRi contexts | 第 4 context NTC + source 中见过的 targets | 保守 effect 能否迁移背景 |
| LOCO-double-unseen | 移除 30% shared targets 在所有 source 的响应 | 第 4 context NTC + 未见 target priors | target prior 是否真能外推 |
| Study-assay holdout | 留出完整研究/化学平台 | 该研究 NTC + target symbols | 是否只学到 assay/study 标签 |

核心 LOCO 顺序固定为 K562、RPE1、HepG2、Jurkat 各做一次 test。外层 target panel 固定后，所有模型使用完全相同的 target 集合和 400-cell templates。

### 7.2 每 fold 必须重新拟合的对象

- core gene selection；
- response PCA 和 DepMap PCA；
- prior normalization；
- DEG labels、effect norm calibration；
- context feature normalization；
- ensemble weights、TTA 步数、scale 和 emitter 超参数。

外层 truth 只评分一次。任何使用 test DEG、test effect norm 或 test target response 选参数的 run 直接标记 invalid。

### 7.3 破坏实验

每个端到端候选都必须通过：

1. `perfect`：真实重复应接近 experimental anchor；
2. `ntc-null`：复制 NTC，PDS sanity 应接近随机；
3. `target-shuffle`：打乱 target prior 后 target-specific 指标应下降；
4. `context-swap`：换错 NTC 后 context gate 候选应下降；
5. `scale-sweep`：扫描 effect scale，确认 PDS 与 MSE/NMAE 的权衡；
6. `prior-mask`：逐一移除 DepMap/ESM2/STRING；
7. `delta-zero`：emitter 必须退化为 NTC bootstrap；
8. `seed-repeat`：随机 emitter 的分数波动不能大于候选模型增益。

## 8. 晋级门和停止规则

以下阈值是 `[工程规格]`，只能在 inner folds 修改一次，不能看 outer truth 后调整：

| 候选 | 晋级条件 | 立即停止条件 |
|---|---|---|
| Ridge vs target mean | 4 个 outer contexts 中至少 3 个 overall 提升；mean scaled surrogate `>= +0.01` | 任一 context overall `< -0.02` |
| MLP vs Ridge | 3 seeds 的 median 提升；worst-context 不下降 | 只在单一 context 或单一 seed 获益 |
| Multi-prior vs DepMap | double-unseen 的 PDS、NMAE 或 reach 至少两项提升 | embedding shuffle 不影响结果 |
| Context gate vs identity | 正确 context 优于 context-swap；worst-context 改善 | gate 输出长期贴边 0.5/2.0 或 swap 不降 |
| AdaPert-lite vs MLP | reach/NMAE 在至少 3 contexts 提升，MSE/PDS 平均退化各不超过 0.005 | 只增加 DEG 数却降低方向 purity |
| 新 emitter vs G0 | Jaccard/fidelity/reach 至少两项提升，PDS/MSE/NMAE 不显著下降 | Monte Carlo 方差大于模型差异 |
| Ensemble | overall 与 worst-context 同时提升 | 权重在不同 inner folds 完全不稳定 |

所有神经模型至少 3 seeds；每个随机 emitter 至少 3 次独立 count resampling。报告六项 raw/scaled surrogate、每 context、每 target 分布和 wall time，不只报总平均。

## 9. Artifact 与运行可追溯性

每个 run 保存：

```text
runs/<run_id>/
  run.json                 # git commit/diff hash、命令、环境、硬件、时间
  data_manifest.json       # source URL、checksum、license、gene axis
  split_manifest.json
  model_manifest.json
  effect_prediction.zarr
  template_manifest.parquet
  count_shards/
  scorecard.json
  qc.json
```

`data/`、`artifacts/`、`runs/` 和大预测文件继续由 Git 忽略。仓库只保存小型 schema/config、checksum manifest 模板、代码、测试和汇总报告。获奖复现说明从 run manifests 自动生成，避免赛后凭记忆补流程。

## 10. 建议代码布局

避免为每个算法建立一层浅包装。建议只有以下公共模块：

```text
src/vc2026/
  domain.py
  corpus/
    __init__.py            # build_corpus, open_corpus
    h5ad_source.py
    rds_source.py
    effect_bank.py
  modeling/
    __init__.py            # fit_effect_model, predict_effects
    mean_ridge.py
    mlp.py
    context_gate.py
    adapert_lite.py
    state_adapter.py
  emission/
    __init__.py            # emit_counts
    molecule_transport.py
    negative_binomial.py
  evaluation/
    __init__.py            # build_splits, evaluate_run
    protocols.py
    cell_eval_adapter.py
    contract_checks.py
  submission.py            # write_prediction
  cli.py

tests/
  fixtures/                # 小型稀疏 synthetic H5AD，不放真实大数据
  test_corpus_interface.py
  test_modeling_interface.py
  test_emission_interface.py
  test_evaluation_protocol.py
  test_submission_contract.py
```

测试只穿过模块接口；不要为内部 PCA helper、单个 loss 或 adapter 私有函数复制一套脆弱测试。STATE 继续运行在独立 Python 3.12 环境，通过 `EffectPrediction` artifact 接入；当前 Python 3.13 数据工具不为 STATE 改全局环境。

## 11. 首个纵向切片的实现顺序

### Slice A：合同与 synthetic fixture，1-2 天

1. `domain.py` 的不可变对象和 hash 校验；
2. 100 cells x 128 genes 的稀疏 synthetic fixture；
3. SplitManifest leakage checker；
4. emitter 的 `delta=0` 与正负 fold-change 期望测试；
5. submission shape/dtype/CSR contract test。

完成定义：不读真实大数据也能跑通 `effect -> counts -> validate`。

### Slice B：四背景 effect bank，2-4 天

1. 接入 scPerturb Replogle/Nadig H5AD；
2. canonical gene mapping 与 measured mask；
3. matched NTC effect transform、bootstrap SE、训练 DEG；
4. 生成四个 LOCO 和四个 double-unseen manifests。

完成定义：所有条件数、target overlap、缺失基因和 source checksum 可审计；无 dense concat。

### Slice C：E1/E2/G0 单 fold，2-3 天

1. target mean；
2. DepMap 50-PC Ridge；
3. IdentityGate；
4. MoleculeTransportEmitter；
5. 一个 held-out context 的完整六指标评分。

完成定义：从训练 effect bank 到合法 400-cell predictions 全链路可重复。

### Slice D：四 folds 与 MLP，3-5 天

先冻结 V0 数据与 emitter，再跑 Ridge 全 folds；只有 Ridge 晋级才训练 MLP。完成后再决定是否批准 AdaPert-lite 和 NTC gate，不提前建设 GAT/TTA。

## 12. 数据与算力分配

| 阶段 | 下载 / 磁盘 | RAM | 计算预算 |
|---|---:|---:|---:|
| Slice A | <100 MB fixtures | <4 GB | <1 CPU-hour |
| Slice B-C | Phase 1 约 23.3 GB；工作集 80-120 GB | 32 GB 可跑，64 GB 推荐 | effect ETL 4-12 CPU-hours；Ridge <2 CPU-hours/fold |
| Slice D | 同上 | 32-64 GB | MLP 全 folds/3 seeds 5-15 GPU-hours；本机 8 GB 可 pilot |
| AdaPert-lite | 额外 prior/cache 约 2-10 GB | 64 GB | 上限 20-50 T4-hours，未晋级即停 |
| STATE ensemble | support set 解压约 49 GB | high-memory host | 约 9 T4-hours/run，最多 3 个有效 runs |
| Phase 2/Jiang | 总下载约 43.5 GB；300 GB 工作盘 | 64 GB | 只在 Phase 1 LOCO 证明增益后加入 |

总推荐上限仍为 60-100 T4-hours 或约 20-40 A100-hours。当前机器的 15 GiB RAM 要求 backed/chunked ETL；RTX 3070 Ti 8 GB 只承担 MLP/小图 pilot，完整 STATE 和并行评分使用云端 16-40 GB GPU 与 64 GB host。

## 13. 下一项可执行工作

下一项不是下载全部数据或实现图网络，而是 **Slice A**：建立领域合同、synthetic sparse fixture、泄漏检查器和 MoleculeTransportEmitter 的期望测试。它会冻结后续所有 adapter 必须遵守的接口，并在没有外部训练数据的情况下先证明 raw-count 生成链路可测试。
