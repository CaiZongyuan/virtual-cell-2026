# State 首次微调实验

目标：在相同数据与输入/输出适配下，比较冻结与解冻官方 State 主干的效果，并生成第一次 VC2026 官方提交。方案与证据见 [执行方案](../../docs/research/state-finetuning-replan.md)。

使用独立 Python 3.12 环境，通过 **uv** 安装依赖。用户级 `~/.config/uv/uv.toml`：

```toml
[[index]]
url = "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple"
default = true
```

先从官方 cu126 索引安装 `torch==2.7.1`，再用此目录的 `requirements.txt` 安装其余依赖。`swanboard==0.1.10b2` 是 SwanLab 0.10.1 本地看板要求的预发行版，显式固定它以使 uv 正确解析。冻结的实际环境清单保存在运行目录的 `audit/`。

## 文件职责

| 文件 | 职责 |
|---|---|
| `assets.py` | 固定权重、数据与特征下载，断点续传、范围读取、校验和 |
| `data.py` | 官方轴合同、按源顺序扫描原始 H5AD、匹配技术批次对照、训练/开发细胞隔离 |
| `model.py` | 复用官方 State，按基因名称迁移参数，连续靶点接口，缺测 mask 和整数计数转换 |
| `smoke.py` | 真实 GPU 前向/反向与计数合同检查；不作生物学评价 |
| `train.py` | 固定步数与数据顺序的两组实验、检查点、JSONL 与 SwanLab 日志 |
| `export.py` | 按背景/靶点生成稀疏 H5AD，避免构造完整稠密提交矩阵 |
| `prepare_all.sh` / `run_comparison.sh` | 顺序准备数据与执行受控实验 |
| `test_contracts.py` | 基因轴、nullable HDF5 字符串、行次序、批次匹配与计数导出的回归检查 |
| `dashboard.py` / `test_dashboard.py` | 等待首份实验数据库后启动固定端口看板，防止错误 3500 |
| `patch_vcc_memory.py` / `prep_submission.sh` | 保留 vcc prep 全部验证，减少打包时的大数组复制 |

## 运行目录

源码目录只保存代码；外部运行目录存放 `protocol.json`、`prepared/`、`runs/`、`swanlog/`、`logs/`、`audit/`、固定的 `upstream/state` 与 `upstream/h1-benchmark` 副本。大型原始资产和预测使用另一个数据目录，包含 `assets/`、`raw/`、`predictions/`。

执行代码以 `uv run --no-project --python <运行目录>/.venv/bin/python ...` 调用，避免继承仓库 Python 3.13 环境。H1 评分单独使用 `.eval-venv` 中的 `vcc-h1`，固定 `cell-eval2==0.16.0` 与 `pdex==0.3.0`。不将真实 Token 写入命令、实验配置或 SwanLab。

## 比较协议

1. 100-step GWPS pilot 只检查完整训练流程与资源，不作为受控比较的初始化。
2. 固定父权重进行 500-step 接口 warmup，主干冻结。
3. 两组都从同一个 warmup checkpoint 出发：冻结组继续训练接口，解冻组同时训练主干；各 1,500 optimizer steps，4 个 64-cell 集合/step，相同 RNG 种子与数据采样。
4. 接口学习率 `1e-4`，解冻主干 `1e-5`；AdamW，weight decay 为 0，梯度范数截断 10；前向 bf16，集合分布损失 FP32。
5. 每组按固定的源内开发细胞损失选择 checkpoint。H1 整个背景不参与微调，使用其 canonical 126-target benchmark 比较六项指标。源内开发细胞不等于未见背景验证。
6. 完整官方预测轴不等于每个基因都有监督。未测量基因不参加对应来源的损失；全部训练源均未测量的基因使用相同 NTC 权重回退。输出清单报告覆盖情况。

打包使用隔离的 `vcc-cli==0.1.0` 环境。其默认实现会复制 CSR 索引，为整份浮点矩阵分配整数性检测数组，并在 SciPy 整数行求和时整体提升到 int64。受 31 GiB 主机内存限制，本实验分块执行整数性检查和 FP64 行求和，类型转换复用本次文件读取所拥有的 CSR 结构；没有移除任何提交验证。补丁前后的打包解压结果已逐项比较 counts、obs、var，并验证跨块分数值、行总量边界、非有限值与全零扰动的拒绝行为；原始源码、前后 SHA-256 和验证记录保存在运行目录 `audit/`。

父权重 `ST-HVG-Replogle/zeroshot/jurkat` 固定 revision `bb6a9562cbbf1fd152df14cc53b4cc7517c77175`；State 源码固定 commit `9bbfe78a434a55205e4de834e1ea99f85f7a3add`。为避免加载未使用的旧 VCI 包，隔离的上游副本仅将 `FinetuneVCICountsDecoder` 的 VCI import 延迟到实例化时；保留 ST 计算路径。迁移报告列出精确复用和丢弃的参数，不声称全部权重原样加载。

## SwanLab

使用 `swanlab[dashboard]==0.10.1` 的本地模式，日志保存在运行目录 `swanlog/`。`runtime-check` 是数值检查；`pilot`、`warmup`、`frozen`、`unfrozen` 是独立实验。

```bash
run_dir=/path/to/run
uv run --no-project --python "$run_dir/.venv/bin/python" \
  "$run_dir/experiment/dashboard.py" --logdir "$run_dir/swanlog" \
  --host 127.0.0.1 --port 16906
```

通过 SSH 本地端口转发查看。图表记录训练/开发损失、梯度范数、学习率、显存、主机内存与吞吐；离线评价结果另外归档。训练损失下降不单独证明比赛得分提高。

使用 `-L 16006:127.0.0.1:16906` 将本地 16006 转发到远程看板。不要在首份日志生成前直接启动 `swanlab watch`：离线看板会留下未初始化的数据库 Proxy，之后即使生成日志，API 仍返回 3500。包装脚本等待已记录的 project，并在指定端口被占用时明确失败，避免自动换端口使链接失效。回归测试覆盖“先启动看板，再生成第一条日志”的完整进程/API 流程。

来源：[SwanLab 官方仓库](https://github.com/SwanHubX/SwanLab)、[本地看板文档](https://docs.swanlab.cn/guide_cloud/offline-board.html)。官方将轻量看板列为维护中的历史功能；本次先用它完成本地实验跟踪，未部署云端或 Docker 服务。

## 已核验的特征别名

H1 `TAZ` 的 `gene_id` 为 `ENSG00000102125`，对应 [HGNC:11577 / TAFAZZIN](https://rest.genenames.org/fetch/symbol/TAFAZZIN)。它与 H1 中独立的 `WWTR1`（`ENSG00000018408`）不同。只将特征查找映射到 `TAFAZZIN`，官方预测标签与基因轴仍保留 `TAZ`。原始核查证据在本地 `output/state-asset-audit/h1-taz-alias-resolution.json`。

首轮结果见[执行记录](../../docs/research/state-first-run-2026-09-25.md)与[精简机器可读证据](results/2026-09-25/summary.json)。

首轮模型显著差于 NTC 基线；后续实验先看[失败复盘与校准门槛](../../docs/research/state-first-run-postmortem-2026-09-25.md)。`diagnose_first_run.py` 读取旧预测并可对旧 checkpoint 做无扰动探针，结果归档在 [postmortem-diagnostics.json](results/2026-09-25/postmortem-diagnostics.json)。服务器连接、环境与看板操作见 [server/README.md](../../server/README.md)。
