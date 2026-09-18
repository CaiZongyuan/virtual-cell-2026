# VC2026 × State 交互学习笔记

按顺序打开四份 notebook。它们都有中文解释、真实运行输出、可修改的参数和诊断题；每份也能独立从头执行。原有 `test.ipynb` 保留；`90_ref_arc_vcc2025_colab_official.ipynb` 是外部固定副本，不属于课程序列（见下文）。

| 笔记 | 学什么 | 实际运行内容 |
|---|---|---|
| [01：真实数据与 H5AD](01_vc2026_data.ipynb) | 文件职责、细胞/基因/靶点、NTC guide、CSR、raw/CP10K/log1p | 完整扫描 A/B/C 的 55,200 个细胞；QC 分布；138 个 guide 组的 PCA |
| [02：State 模型与迁移](02_state_model_and_transfer.ipynb) | 官方权重配置、基因轴覆盖、B/S/G/H、集合注意力、Energy loss、按名称迁移 | 读取固定官方 YAML；真实 NTC 张量；NumPy 教学 forward、置换性质和权重错位实验 |
| [03：微调、计数与预算](03_finetuning_counts_and_budget.ipynb) | 公共数据清单、防泄漏、原生微调命令、400-cell 输出、评分合同、GPU/内存/费用 | 教学计数生成与 H5AD 写入/读回；格式检查；可拖动的预算计算器 |
| [04：Colab 流水线 × H1 评分](04_arc_colab_h1_benchmark.ipynb) | 官方 VC2025 Colab 的 22 个 cell 映射、与 `vcc-h1` 的合同差异、126 靶点面板、防泄漏与文件分离边界 | 校验 Colab 固定副本哈希；缓存 CSV ↔ sources.json ↔ benchmark 注册表三方比对；150→126 靶点筛选并生成推理 TSV |

完整解释与正式实施边界见 [第 03 课：State 上手](../docs/lessons/03-State上手.md)；源码细节见[检查点审计](../docs/research/state-checkpoint-finetuning-audit.md)。

## 课程 → notebook 映射表

课程完成度校验（`scripts/check-lessons.py`）以本表为准判定「每课都有可运行 notebook」。首列是课号，第二列列出该课的教学 notebook。

| 课号 | notebook | 说明 |
|---|---|---|
| 00 | —（豁免） | 纯阅读课：正文已发布飞书并冻结，且早于完成度契约。官方 Colab 固定副本 `90_ref_*`/`91_ref_*` 已在下方单独声明，不属于课程序列 |
| 01 | `01_vc2026_data.ipynb` | 数据合同与真实数据审计；正文已发布飞书冻结，回指由本表补齐 |
| 02 | `06_state_anatomy.ipynb` | State 架构解剖：集合注意力的置换等变性、Energy 距离 vs MSE、残差加回与参数量分解（纯 NumPy，不装 torch）。正文 §7.3 已回指本 notebook |
| 03 | `02_state_model_and_transfer.ipynb`、`03_finetuning_counts_and_budget.ipynb` | State 接口迁移与微调落地：02 读固定官方 YAML 核对两套配置（328/2,000 vs 768/18,533）、按基因名称迁移的权重错位实验；03 做教学计数生成、H5AD 写入/读回、400-cell 输出合同检查与可拖动的预算计算器。**边界**：两个 notebook 都是纯 NumPy 教学复现，不在本机跑 `arc-state` 微调（本机装不了，正文 §6 已说明） |
| 04 | `05_noise_floor.ipynb`、`11_ablation_and_falsification.ipynb`、`09_simple_baselines.ipynb`、`04_arc_colab_h1_benchmark.ipynb` | 验证与证伪的动手材料（本课吸收了原 L1-02/L2-05/L3-01 与 L2-04 的 B0–B3）：05 测噪声地板的两种口径与缩放曲线；11 演示三类自欺机制、k 选最大虚高、判据三与「总分涨 DE 跌」的构造；09 手算 B0–B3 并把「B1 是否优于 B0」接到地板的机械判定；04 校验官方 Colab 的评分输入合同（126 靶点面板、推理 TSV、三方 SHA-256）。**边界**：四份均为离线教学，不在本地跑六指标数值评分或正式微调 |
| L1-01 | —（豁免） | 纯阅读课：§6 的「可复现实践」是**填一张赌注对照表**（材料 × 赌注 × 核心假设 × 天花板判据 × 本赛可用性），产物是读者自己的判断表，不存在需要 kernel 执行的计算。本课零算力，见 `docs/lessons/README.md` 阶段表第 1 阶段「纯阅读，零算力」 |
| 05 | `07_stack_icl_context.ipynb` | Stack 的窗口切分与查询细胞复制、双轴注意力显存与 8 GiB batch 边界、参数量手算对表、`T=5` 生成计划、上下文敏感性对照（纯 NumPy）；正文第 05 课 §8 已回指（原 `L2-02` 行随课程合并迁到本行） |
| L2-03 | `08_foundation_model_routes.ipynb` | scGPT 分层参数量与「为什么不给总数」、零表达靶点的接口可区分性、四分量 ANOVA 的 beta_frac 分档、B1 与「完美知道 Γ」上界的机会窗口（合成数据，纯 NumPy） |
| L2-04 | `09_simple_baselines.ipynb` | B0/B1 手算与 B2 相似度加权、LOCO 协议骨架与零覆盖回退 B0（合成数据，纯 NumPy）。**注**：B0–B3 的权威解释与手算口径已移至第 04 课 §6.3，本课正文只保留效应迁移族；notebook 09 由第 04 课与本课共用 |
| L2-06 | `10_model_cards.ipynb` | 六张模型卡的可核对表（附录课）：可执行程度矩阵（代码/权重/真值/面板四列机械计数）、训练条件判定（本赛 D/E/F 能否满足「需要目标背景扰动真值」）、面板交集审计（示意集合，演示差集与 patch 边界问题）、靶点身份编码分类器（可外推 vs 查找表，含 B3 的 `b_t`）、分量归因能力判定（零依赖，纯标准库） |
| L3-05 | `11_ablation_and_falsification.ipynb`、`03_finetuning_counts_and_budget.ipynb` | 最终轮的判据与彩排：11 提供消融顺序表、证伪清单与「地板当阈值」的机械判定（稳定性优先于单次最高分，§2.3）；03 提供冻结清单里的输出合同与预算复算 |

`90_ref_*` / `91_ref_*` 是官方 Colab 的固定副本与中文对照，**不属于课程序列**，见下一节；`test.ipynb` 是环境自检，同样不映射任何课程。

**至此当前全部 11 门课（含附录 L2-06）的映射已齐**，本表可直接被 `scripts/check-lessons.py` 解析。两门课标为「—（豁免）」并写明理由：`00`（正文冻结 + 早于完成度契约）与 `L1-01`（纯阅读课，产物是读者自己的填表，无计算）。豁免是**登记在案的判断**，不是放宽判定——校验脚本里对这两条各有一条带理由的 EXEMPT 记录。

一门课可以映射多份 notebook（如第 04 课从噪声地板、证伪判据、B0–B3 手算到评分合同四段），也可以多门课共用一份（如第 03 课与 L3-05 共用 `03`）。本表只声明「这门课的动手材料在哪里」，不要求一一对应。

## 官方 Colab 固定副本

`90_ref_arc_vcc2025_colab_official.ipynb` 是 Arc 官方 [STATE for Virtual Cell Challenge Colab](https://colab.research.google.com/drive/1QKOtYP7bMpdgDJEipDxaJqOchv7oQ-_l)（VC2025 版）的逐字节固定副本：22 个 cell，GPU T4 配置，SHA-256 `0b3888b9a36e6fbfc056b9e5585d825aa5a97a92f34d3bc2ff69cba064f21422`（2026-09-15 下载，与[来源审计](../docs/research/state-training-source-audit.md)记录一致）。它不是课程单元，不能在学习环境运行（需 GPU、`arc-state` 与 Python < 3.13）；`04_arc_colab_h1_benchmark` 的 cell 序号映射以它为准。Colab 是可变文档：若 Arc 更新，重新下载后哈希会变，须重新审计再更新 notebook 04 的映射，不能沿用旧序号。

`91_ref_arc_vcc2025_colab_zh.ipynb` 是它的**中文对照翻译版**（非官方翻译）：markdown 译为简体中文，代码命令未改动、仅译 `#` 注释，内嵌图片逐字节保留；cell 序号与 90 副本一一对应。翻译仅供阅读辅助，两种文本有出入时以英文原文为准。

## 准备环境

在仓库根目录运行：

```bash
uv sync --group notebook --frozen
```

然后在 VS Code 的 notebook kernel 选择器中选择本仓库 `.venv/bin/python`。从仓库根目录或 `notebook/` 启动都支持，代码会向上查找项目目录。

如果更习惯浏览器 JupyterLab，可以另用：

```bash
uv run --group notebook --with jupyterlab jupyter lab notebook/
```

浏览器方式会临时安装 JupyterLab；核心教学依赖已在 `pyproject.toml` 的 `notebook` 组与 `uv.lock` 中锁定。预算 widget 需要前端支持 ipywidgets；若未显示滑块，直接修改其前一个代码格的 `budget_table(...)` 参数即可。

学习环境使用仓库的 Python 3.13，**不安装 arc-state 或 PyTorch**。正式 State 微调另建 Python 3.11/3.12 环境，不要把两套依赖混装。第二份 notebook 的 NumPy 模型是理解接口的随机教学模型，不是官方 State 实现，也不是预训练权重。

## 数据与输出

现有输入路径：

```text
data/vcc2026-validation/
  vcc_2026_controls.zip
  controls/
    context_A.h5ad
    context_B.h5ad
    context_C.h5ad
    gene_names.csv
    pert_counts.csv
    manifest.json
```

三份课程 notebook 默认都不联网、不下载大资产、不执行正式微调或上传；04 课同样离线，所需元数据已缓存。原始 H5AD 仅以只读方式打开，表达按块读取；第一份扫描全部数据，第二/三份明确标识用于张量或生成演示的切片。

`notebook/assets/state/` 保存两组官方发布模型的原始 `config.yaml`、`hparams.yaml`，总计约 80 KB。它们包括真实基因名单，但不包括 checkpoint 张量、真实扰动表达或评估答案。`sources.json` 记录固定 revision、URL、SHA-256 和日期，第二份 notebook 会重新校验这些文件。文件中的作者本机路径只作来源信息，不能原样拿来训练。实际原始符号匹配得到旧 HVG 的 1,877/2,000 与旧 full 的 6,197/6,546 落在本地比赛面板中；未匹配项先核验别名/ID 版本，再确定真正缺测，不能静默补零。

`notebook/assets/h1-benchmark/` 保存 H1 训练靶点计数表 `pert_counts_Training.csv`（2.8 KB 公开元数据：150 个靶点的 `n_cells` 与中位 UMI）和 `sources.json`，与 `references/vcc2026-h1-benchmark` 注册表同源；04 课做缓存 ↔ sources.json ↔ 注册表三方 SHA-256 校验。H1 训练对象（约 15.48 GB）与评分参考资产由 `vcc-h1 setup` 自行下载校验，不进本目录。

运行产物在 Git 忽略的目录下：

```text
output/notebook-learning/
  01-data/      全量 QC CSV、guide PCA、PNG/SVG/PDF 图
  02-model/     模型教学的预留输出目录
  03-pipeline/  教学 H5AD、采样来源、微调命令文本
  04-bridge/    H1 推理目标 TSV（126 靶点 × 400 细胞）
```

第三份写出的 `TEACHING_ONLY_not_for_submission.h5ad` 只有一个背景/靶点的 400 行，是 NTC 无效应教学生成器的输出。文件中的 target 标签不使它成为真实扰动，也不能代表 State 预测；完整比赛行数检查失败是预期行为。正式提交需学习得到的响应、3×300×400 完整覆盖和独立评价。

已执行的 notebook 保留小型表格和图片，打开即可阅读。重新执行会刷新教学输出目录中的对应文件，不改原始数据。

## 验证记录与图表边界

2026-09-15，在本仓库 Python 3.13 学习环境中，四份 notebook 均已用新 kernel 按顺序执行成功。前三份共 65 个 Markdown/代码单元、31 个已执行代码单元，单份本机运行墙钟约 14.2 / 2.0 / 3.0 秒；04 课 9 个单元（2 个已执行代码单元）墙钟约 2.2 秒。以上包含 kernel 启动，不是 State 训练速度或其他机器的时间承诺。未进行 GPU 训练或正式六指标评分；04 课只校验哈希、复现 126 靶点面板并生成 TSV。

第一份图表使用全部 55,200 个细胞与全部 18,533 个基因；没有按 QC 阈值过滤。直方图描述细胞分布，不把细胞当作独立生物重复。PCA 每个点聚合同 guide 的 400 个细胞，共 138 组；同背景各点可能高度重叠，并非只画了三个点。归一化为每组总量到 10,000 后 log1p，全部基因参与中心化 PCA；这不能证明匿名细胞身份或排除技术批次影响。

图表使用 matplotlib，明确相同背景的配色、共享分箱、300 dpi 导出 PNG、可编辑 PDF/SVG 文字；已检查全图与坐标/图例，两个 PDF 最小文字为 8 pt。它们是教学描述性图，不作统计显著性检验，不套用论文生物重复或置信区间结论。静态绘图检查中的“未导出投稿 TIFF”“PNG 未达 600 dpi 默认值”和“宽度不是论文栏宽”提示按教学用途处理：本次提供可读的 notebook 预览、300 dpi PNG 与矢量文件，不是期刊投稿图包。图表预览和大 CSV/H5AD 可再生成，保持在忽略目录。

常见问题：找不到包时检查是否选错 kernel；找不到数据时检查 `controls/` 的实际解压层级；出现原始 dtype 为 float32 时阅读第一份的整数值检查，不能据 dtype 判断数据已经 log1p。
