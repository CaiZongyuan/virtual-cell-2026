# 下一组 State 微调候选的证据与边界（2026-09-26）

**建议只增加一个神经网络候选：固定经验效应主预测，让公开 State 主干学习有界、去公共分量的靶点特异残差。** 当前结果不足以判断 State 本身无效，也不足以断言增加训练步数即可提高 H1 分数。下文是源码与只读诊断支持的实验建议，尚未实现或验证提分；H1/Jurkat 扰动表达不进入训练。

## 已核验的事实

当前 `campaign.py` 把同一 NTC（non-targeting control，非靶向对照）集合分别输入靶点与零条件，计算两次**非负表达输出之差**；每步两组靶点独立做逐基因加权 MSE（均方误差），没有不同靶点之间的比较项。[本项目实现](../../experiments/calibrated_transfer/campaign.py)

State 固定源码 `9bbfe78a434a55205e4de834e1ea99f85f7a3add` 的 `output_space=gene` 路径为 `project_out(transformer_output + control_encoding)`，随后经过 ReLU，再返回表达值。**两个 ReLU 输出相减可以为负，不能把它诊断为“无法预测下调”。** 可证的局部风险是：某基因两个分支的激活前数值都小于零时，两个分支对该输出的梯度都为零。是否频繁出现、是否解释当前成绩，尚未测量。[上游 forward L501–519](https://github.com/ArcInstitute/state/blob/9bbfe78a434a55205e4de834e1ea99f85f7a3add/src/state/tx/models/state_transition.py#L501)

当前监督是 `log((mean_treated_CP10k+0.1)/(mean_control_CP10k+0.1))`，不是平均 `log1p(CP10k)` 的差；两者一般不相等。这是已明确改变了输出语义的适配，网络可以学习新语义，不是数学上不可能。原父权重归一化仍未完全核验。[效应表](../../experiments/calibrated_transfer/effects.py)、[权重迁移](../../experiments/state_finetune/model.py)、[公开权重审计](state-checkpoint-finetuning-audit.md)

训练标签使用全部训练细胞构成的固定效应表；开发标签却用每次抽取的 64 个处理和对照细胞估计效应，只有 16 次 Monte Carlo 开发损失。两组最后一次训练 batch 损失约 0.013，而开发约 0.135–0.139；**标签估计噪声和抽样方式不同，不能把这个差额直接称为过拟合程度。** 应用固定开发细胞伪批量效应表，并报告同一目标上的零残差/经验先验损失。[训练与开发代码](../../experiments/calibrated_transfer/campaign.py)、[完整旧结果](calibrated-transfer-run-2026-09-26.md)

## 只读源数据诊断

读取服务器既有 `effects.npz`、`effects.json` 与训练日志，不加载 H1/Jurkat 结果、不运行 GPU。1,083 个来源×靶点条件覆盖 619 个靶点；K562、RPE1、HepG2 分别覆盖 609、189、82 个，只有 **201 个靶点**在至少两个生物背景出现。GWPS 与 K562 essential 必须合并为一个背景后再做留出。

对每来源，以旧训练同样的截断效应 `d` 和归一化权重 `w=sqrt(control+0.1)×measured`，拟合不区分靶点的最佳公共向量 `m_g=sum_t(w_tg*d_tg)/sum_t(w_tg)`：

| 来源 | 全零预测损失 | 最佳公共向量损失 | 公共向量解释的加权平方量 |
|---|---:|---:|---:|
| GWPS | 0.021645 | 0.021165 | 2.21% |
| K562 essential | 0.028086 | 0.026147 | 6.90% |
| RPE1 | 0.049623 | 0.042628 | 14.10% |
| HepG2 | 0.057066 | 0.048955 | 14.21% |

这些是**训练效应表的拟合诊断**，不是交叉验证分数；第四列为 `1−loss_common/loss_zero`，不是论文 ANOVA 的解释方差。结果反对“当前加权目标主要由公共响应支配”的简单解释。H1 的 State PDS 接近 NTC 与响应塌缩相容，但还需测量模型预测在靶点间的方差、真实与预测的去均值相关，才可确定。

既有 `protocol.training_targets` 的 693 个 ESM2 单位向量（协议词典大于本轮实际 619 个训练靶点）两两余弦相似度均值 0.6293、中位数 0.6317、5%–95% 分位 0.4636–0.7882。向量有明显共同方向，**这不证明条件不可区分**，也不据此直接重置已蒸馏的 ESM 映射。第一次只读查询因 `TAZ` 别名报错；复用现有 `TAFAZZIN→TAZ` 映射后完成，不改变数据或权重。

## 一个准确、可回退的配方

残差指主预测之外的修正。其生物假设是同一基因的部分效应可以跨背景迁移，背景可能改变靶点特异响应；此处只让模型小幅修正已有经验结果。响应分解作者代码明确区分全局、细胞系、靶点和交互分量，但**没有保证 NTC 足以识别交互**。[作者 ANOVA 源码](https://github.com/xinyizhanglab/perturbation-decomposition/blob/a15214780619736d393f40240e56ba992fd416a3/decomposition/anova.py)、[已核论文与边界](../references/INDEX.md#perturbation-response-decomposition-enables-biologically-aligned-generalization-to-unseen-perturbations-and-cellular-contexts)

1. 继续使用已归档的公开 State 后代 `unfrozen/best.pt`，SHA-256 `d9e17261e9b5ea86d63c52835db22e6a305612906d2e39fbc8f82c133ac25fff`，与旧两组起点一致。把输出 ReLU 改成 Identity，把单线性 `project_out` 权重与偏置置零。保留预训练 Transformer 与已适配靶点接口；冻结 basal/mask encoder，只训练 signed readout、pert encoder 和最后两个 Transformer block，学习率分别 1e-4、1e-5，关闭 dropout。**该起点已看过所有来源，因此本候选不声称 source-LOCO 校准。**[当前加载入口 L58–71](../../experiments/calibrated_transfer/campaign.py)
2. 此时模型差分严格为 `rθ(x,t)=W·mean(hθ(x,t)−hθ(x,NTC))`，没有表达非负限制；相同 control 编码及 head bias 在差分中消掉。W 零初始化使修正从零开始，NTC 差分仍为精确零。第一步仅 head 得到有效梯度，后续主干才随 head 学习；这是可预期的初始化行为。
3. 对训练背景 c、靶点 t，`p_{−c,t}` 只由**其他训练背景**的同靶点效应构成。仅在来源与先验均实测的基因上构造 `y_ct=clip(d_ct,±ln4)−0.2×clip(p_{−c,t},±ln4)`，再减去同来源合格靶点 residual 的逐基因均值 `μ_c`。没有其他背景同靶点的条件不构造伪残差监督，不用零填充冒充缺测标签。效应表均来自训练细胞；batch-matched control 规则沿用现有实现。这里 0.2 是同期保守经验候选的固定幅度，尚非本记录确认的最优值。
4. 每步抽同一来源的两个**不同靶点** t/u，使用匹配该来源的 NTC 集合。损失取逐目标 `MSE_w(rθ,y−μ_c)` 加 `0.5×MSE_wpair(rθ_t−rθ_u,y_t−y_u)`，`wpair` 只覆盖两者共同实测基因。若为减少输入随机差而共享控制集合，须保证二者控制批次合同兼容；否则沿用各自匹配对照。该 pairwise 项是工程假设，不引用成原生 State loss。
5. 推理使用一个**仅由训练标签定义并冻结**的 anchor 靶点集合 A，对同一目标背景 NTC 求 `r̃_t=rθ_t−mean_{a∈A}(rθ_a)`。不以 H1/官方目标面板自身求均值，以免面板一变预测就变。最终施加效应 `δ_t=clip(0.2×clip(p_all,t,±ln4)+0.1×clip(r̃_t,±ln2),±ln4)`。无有效经验先验或残差未监督基因直接令修正为零。NTC 控制条件直接保持恒等，不把 anchor 均值扣到 NTC 上。与同期 `0.2×prior` 经验候选使用同一个计数生成器；以上已含幅度，不能再乘旧 decoder 的 `shrink=0.5`，实现中只应用一次缩放。

固定总预算 **6,000 optimizer steps**，一个 all-source 分支；每步两个 64-cell 集合，BF16 前向，FP32 差分/损失。旧 1,000-step 有限解冻循环约 180 秒、峰值分配显存不足 1 GiB，支持在 3090 上先运行 smoke；新配方的端到端时间与内存仍需实测，不直接倍乘为承诺。用固定开发细胞效应表报告来源诊断，不根据 H1/Jurkat 标签训练或选择训练步数。

## 校准和使用边界

**State 权重固定为 λ=0.1，不进行来源背景留出选 λ。** 同源开发细胞诊断可以判断训练是否收敛、修正是否塌缩，不能证明跨背景泛化。经验部分若做来源背景留出，必须将 K562 两文件一起排除；经验 prior 的校准不能自动转称为 State residual 的校准。

本配方只监督去公共均值的剩余分量，并没有确定目标背景公共响应的方法；固定 anchor 中心化又主动移除了模型预测的公共分量。训练时 `y−μ_c` 与推理时 anchor 中心必须按同一均值/测量 mask 规则实现，避免中心变化产生额外效应。不同背景的药物/基因响应可涉及该背景的调控网络与初始细胞状态，NTC 表达并不直接观测所有这些因果条件，**从 NTC 唯一识别交互在此没有证据保证**；小权重和经验回退只控制工程风险，不解决生物可辨识性。

严格比较为同样经验幅度/生成器的 `λ=0` 与 `λ=0.1`，并保留上一轮 incumbent。若完整 H1 六指标和预先规定的误差门槛不支持 residual，**λ=0，回到经验候选**，保留负结果。父权重预处理与历史暴露继续按未知记录；当前旧全来源后代权重则已知暴露于本轮来源，不能称它未见这些背景。

H1 已是开发集，可用于本轮固定候选的完整六指标比较；Jurkat 上一轮已做过确认，本轮不再借它选 λ 或迭代配方。官方成绩也不能补上训练暴露证明。当前经验模型的 H1 MSE 明显变差，因此最终选择须同时保留综合分、均值误差和逐靶点变化，不以 PDS 一项晋级。

## 检索台账

先读 `docs/references/INDEX.md`，复用 State、响应分解、既有微调/Stack 审计；没有新增发现缺口，因此 Scholar、SciVerse、HTTP 均 **0 次**。一手证据为固定 State 官方源码、固定响应分解官方源码及本项目实际代码/日志；未把现有转述材料当作新读论文原文。服务器只读查询 2 次（第 1 次 ESM 部分失败、第 2 次修正别名后完成）；无下载、GPU 作业或远程写入。未知项：父预处理/完整暴露、实际 dead-ReLU 比例、靶点差异保留程度、候选是否提升分数。
