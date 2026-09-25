# 校准迁移首轮实验记录（2026-09-25–26）

**已核验的完整候选是经验效应迁移：H1 综合分由 −0.045231 提高到 0.163874，增加 0.209105；均值误差同时变差。** 两组 State 继续微调均完成 1,000 步和完整预测导出，但服务器 SSH 中断后，尚未取回并确认完整评分。Jurkat 独立背景验证尚未执行，不能称为已经确认跨背景稳定收益。

这里使用固定 H1 benchmark v0.2.0、126 targets × 400 cells、18,080 genes，以及 cell-eval2 0.16.0 / pdex 0.3.0。它是开发评分，不是官方 A/B/C 排行榜。官方提交仍暂停。

## 已完成的结果

| 方案 | H1 综合分 ↑ | 原始归一化 MSE ↓ | 原始 NMAE ↓ | 状态 |
|---|---:|---:|---:|---|
| canonical NTC 重采样 | −0.045231 | 1.002242 | 1.005045 | 既有完整基线经实际数据、配置、评分包与结果哈希复核后复用 |
| 经验效应迁移 | **0.163874** | 1.303612 | **0.986160** | 完整评分成功，退出码 0，结果哈希已核验 |
| State：主干冻结 | 待确认 | 待确认 | 待确认 | 训练、导出、H1 文件合同检查完成；评分状态待恢复连接核验 |
| State：解冻最后两层 | 待确认 | 待确认 | 待确认 | 同上 |

NTC（non-targeting control，非靶向对照）指携带不针对任何基因的向导的细胞。NTC 基线预测“没有额外扰动效应”。经验迁移则用其他背景中测到的扰动/对照变化，改变 H1 对照细胞的计数。

经验迁移的六项缩放分为：PDS 0.519174、MSE 0、NMAE −0.045985、FID 0.380326、REACH −0.008373、JAC 0.138102。增益主要来自扰动区分和差异表达指标；MSE 为 0 是缩放后的得分，不是误差为 0。

逐靶点核验：PDS 在 96/126 个靶点上改善，方向保真度在 110 个有准备数据监督的靶点上提高；未截断 MSE 仅在 4/126 个靶点上下降、106 个上升，16 个不变。因此综合分提升不能解释为每项表达预测都更准确。变化幅度、来源噪声和背景交互是后续要区分的工程假设，尚无证据把均值误差单独归因于其中某一项。

16 个无准备数据监督的靶点回退到固定 NTC，未截断 MSE、PDS 和 DE 指标均与基线相同。截断 MSE 有约 3×10⁻⁶ 的变化，这是评分器使用整个扰动面板的共享噪声校正所致；不是回退细胞被模型改写。已对照固定源码核实该行为。[逐靶点审计](../../experiments/calibrated_transfer/results/2026-09-25/audit/empirical-fallback-parity.json)

完整数值与验证清单见[基线](../../experiments/calibrated_transfer/results/2026-09-25/evaluation/control/scores.csv)、[经验迁移](../../experiments/calibrated_transfer/results/2026-09-25/evaluation/empirical/scores.csv)及各目录内 aggregates / per_target / manifest。尚只有一个生成种子，不声称统计显著性或隐藏背景的同等收益。

## 本轮微调方案与数据

State 两组都从同一个已归档 `unfrozen/best.pt` 出发，初始 SHA-256 为 `d9e17261e9b5ea86d63c52835db22e6a305612906d2e39fbc8f82c133ac25fff`，其祖先是公开 ST-HVG-Replogle 权重。本轮是已有适配模型的继续微调，父权重的原始归一化及预训练暴露仍未完全核验，不能称为原论文的严格原生复现。

主要变化是以同一对照集合上的 `f(x,target) − f(x,NTC)` 预测效应，关闭两分支 dropout；无扰动条件的差分实测为精确零。输出通过二项 thinning 和 Poisson 增量生成计数，不做全基因统一重归一化。零效应保持原始计数完全不变，未监督基因也保留原始计数。该解码器的增量与原计数成比例，不能在原本为零的位置新增表达，这是后续需检验的限制。

| 配置 | 冻结组 | 有限解冻组 |
|---|---:|---:|
| 总参数 | 62,683,264 | 62,683,264 |
| 可训练参数 | 19,937,976 | 28,000,216 |
| optimizer steps | 1,000 | 1,000 |
| 实测训练循环耗时 | 87.34 s | 180.49 s |
| 源内开发损失（诊断，不是 H1 分数） | 0.139071 | 0.135413 |

两组使用相同数据抽样顺序、seed 42、两个 64-cell 集合/step、固定末步检查点、接口学习率 1e-4、可解冻主干学习率 1e-5。训练耗时受同期评分争用影响，不能当作独立吞吐对照。训练写入本地 SwanLab。[协议与代码](../../experiments/calibrated_transfer/README.md)

训练仅使用既有 GWPS、K562 essential、RPE1、HepG2 的训练细胞划分，共 139,586 个扰动细胞、1,083 个来源×靶点条件、619 个不同靶点。两个 K562 文件计作同一生物背景。模型轴 18,536 个基因中，10,480 个有监督。

覆盖口径为：公开 H1 面板 150 个靶点中训练覆盖 129 个；实际 canonical 126 个中覆盖 **110 个**。官方 300 个中准备数据覆盖 **254 个**，其直接监督均来自 GWPS；GWPS 原始文件本来覆盖 272 个，旧筛选阈值丢掉了其中一部分。[覆盖审计](../../experiments/calibrated_transfer/results/2026-09-25/audit-target-coverage.json)

新增 Jurkat（人 T 细胞白血病细胞系）数据已下载并校验：262,956 cells × 8,882 genes，含 12,013 个 NTC，文件 1,293,665,804 bytes，MD5 `d8b05d00bfbd686d37ffdd4293bc6c8c`。本轮预留作独立确认背景，不参加训练或选模；它覆盖 50 个公开 H1 靶点，但不覆盖当前官方 300 靶点。确认将另报测量基因交集上的均值误差，不能冒称 canonical 六指标复现。[文件审计](../../experiments/calibrated_transfer/results/2026-09-25/audit-jurkat-inventory.json)

科研检索共两次 Scholar 查询、14 次一手来源 HTTP 核验，20 个已查看候选均已登记，包括备选和排除项。作者 Replogle 大文件不能补回缺测基因；Jiang 数据确认是 CRISPRi，可增加背景但须保留刺激条件；Orion 完整 H5AD 超过存储上限，后续只能考虑筛选子集。[文献与数据依据](autonomous-finetuning-data-review-2026-09-25.md)

## Stack 检查

公开 Stack-Large-Aligned 权重及基因列表已下载并通过 SHA-256 校验。RTX 3090 上，64/512-cell、FP32、batch=1 推理均成功，峰值分配显存约 0.90/1.35 GiB，未更新权重。

NTC 组成 TV 约 0.35；64-cell 中仅在已测基因上重新计算仍约 0.33，而 NTC 拆半约 0.049。未测基因只分走约 5.2% 的预测计数，不能解释主要偏移。短窗口也不是充分解释，原生 512-cell 仍约 0.35。本轮没有把这条原生输出推进完整 H1 评分，也没有证明其扰动预测不如其他方法。[完整实跑与环境记录](../../experiments/stack_native/README.md)

## 执行、存储与恢复

最近一次服务器存储盘点为 **85,618,807,895 bytes（约 85.6 GB）**，包括旧运行目录、新实验、Stack 环境、原始数据/权重/预测及 uv 缓存，低于 500 GB 限制。大文件均在外部运行目录或 Git 忽略目录，Git 只保留代码和小型结果。

完整 DE 评分远慢于训练。读缓存的 1,024-cell 复现显示磁盘后端约为内存读的 16 倍；新增预测缓存后仍保持同样的计数、行顺序和上游公式。三组同时缓存导致交换区占用上升，后改为最多两组。较短的运行上限导致多次按分块续算，所有中断和最终退出码保存在服务器 audit/logs 中。最终推荐脚本已采用更充足的运行时间和受限并发；此次实际候选仍对应原始固定训练配置，没有在看见评分后改参数。

2026-09-26 03:09（北京时间）的连接核验出现 SSH 故障。旧复用连接与独立新连接均失败；TCP 22 会被立即关闭，没有正常 SSH banner。尚不能判断主机、WSL、端口转发或网络的具体原因，也不能确认远程进程是否继续运行。完整经验迁移结果已取回本地；两组微调评分和 Jurkat 确认必须恢复连接后继续核验。

运行目录：`~/vcc2026-calibrated-20260925`；既有环境/benchmark：`~/vcc2026-run`；原始数据和权重：`/mnt/e/vcc2026-data`。恢复 SSH 后先检查现有进程，避免重复启动。新的恢复入口会拒绝与正在运行的评分器重叠，验证已完成结果的实际文件哈希，续算不完整的同一预测文件，再汇总和按预定规则选模：

```bash
# 先把仓库中的最新 calibrated_transfer 源码同步到该运行目录的 code 中。
prior_run="$HOME/vcc2026-run"
run_work="$HOME/vcc2026-calibrated-20260925"
tmux new-session -d -s vcc2026-recover \
  "PYTHONPATH='$run_work/code/experiments/calibrated_transfer:$run_work/code/experiments/state_finetune' '$prior_run/.eval-venv/bin/python' '$run_work/code/experiments/calibrated_transfer/recover_campaign.py' --previous '$prior_run' --work '$run_work' --root /mnt/e/vcc2026-data --confirm > '$run_work/recovery.log' 2>&1"
```

使用 tmux 使有界任务不依赖本地 SSH 会话。`--confirm` 仅在完整比较选出优于控制的候选后执行 Jurkat 确认；已有确认目录会触发明确停止，防止不加记录地重复使用确认集。恢复入口及最终启动器已通过语法检查，因连接中断尚未实际执行端到端恢复。官方提交不在该入口中。
