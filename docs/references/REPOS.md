# 上游仓库索引（本地精读副本）

本索引登记为「要精读的模型与工具」而浅克隆到仓库根 `references/` 的上游代码。**`references/` 已在 `.gitignore` 中整体忽略**，因此这里的代码副本只存在本地，不进入版本库；本文件（`docs/references/REPOS.md`）才是入库的登记表。

登记的目的是可复核：任何一次基于这些代码的结论都要能说清**上游仓库、固定 commit 和读取日期**。同一上游更新后结论若变化，重新克隆并更新本表，不覆盖旧记录。

- 克隆方式：`git clone --depth 1`（浅克隆，只取默认分支最新提交）。
- 本地根目录：`references/<目录名>`。
- 收集日期：2026-09-17。
- 许可状态为**基于仓库内文件与 GitHub API 的判断，需人工复核**；标记「无许可证文件」的仓库不可再分发或用于衍生作品。

## 1. 官方工具链与主线模型（Arc Institute）

| 本地目录 | 上游 | commit | 上游日期 | 体积 | 许可 | 用途 |
|---|---|---|---|---:|---|---|
| `state` | [ArcInstitute/state](https://github.com/ArcInstitute/state) | `9bbfe78a43` | 2026-07-23 | 9 MB | 见仓库 LICENSE（SPDX 未识别） | **主线模型官方实现**：SE/ST 两种模型、训练与推理 CLI、配置。与[首投方案](../research/first-submission-plan.md) §3 固定的 commit `9bbfe78a` 一致 |
| `state-reproduce` | [ArcInstitute/state-reproduce](https://github.com/ArcInstitute/state-reproduce) | `1a29ba1aa5` | 2026-02-25 | 11 MB | **无许可证文件** | State 论文的复现分析与基线；用于理解论文数值是怎么算出来的 |
| `cell-eval` | [ArcInstitute/cell-eval](https://github.com/ArcInstitute/cell-eval) | `6928cf8bd7` | 2026-07-27 | 1 MB | MIT | **官方评分组件**（VC2025 六项指标的定义实现）。参赛者博客里的公式复述以此为准 |
| `cell-eval2` | [ArcInstitute/cell-eval2](https://github.com/ArcInstitute/cell-eval2) | `5e64833518` | 2026-08-20 | 13 MB | MIT | GPU 加速的评分实现；H1 开发基准固定使用 0.16.0 |
| `pdex` | [ArcInstitute/pdex](https://github.com/ArcInstitute/pdex) | `dcdf982d7c` | 2026-07-14 | 1 MB | MIT | 并行差异表达；六项指标中三个 DE 组件的依赖 |
| `cell-load` | [ArcInstitute/cell-load](https://github.com/ArcInstitute/cell-load) | `9ba45e59f6` | 2026-06-29 | 1 MB | MIT | State 的数据加载器；决定训练时每个集合的构造方式 |
| `arc-virtual-cell-atlas` | [ArcInstitute/arc-virtual-cell-atlas](https://github.com/ArcInstitute/arc-virtual-cell-atlas) | `4f7bb170c6` | 2026-08-28 | 2 MB | **无许可证文件** | 官方数据图谱入口与数据清单来源 |

## 2. 模型对比路线

用于教程 L2「模型深潜」的对照实现。同一课一个仓库，回答「同样的任务它怎么解」。

| 本地目录 | 上游 | commit | 上游日期 | 体积 | 许可 | 路线 |
|---|---|---|---|---:|---|---|
| `stack` | [ArcInstitute/stack](https://github.com/ArcInstitute/stack) | `cacc2e4b09` | 2026-04-27 | 3 MB | 见仓库 LICENSE（SPDX 未识别） | 上下文内学习（in-context learning） |
| `scGPT` | [bowang-lab/scGPT](https://github.com/bowang-lab/scGPT) | `cebd6fae65` | 2026-04-27 | 30 MB | MIT | 单细胞基础模型：预训练表征 + 微调 |
| `x-cell` | [xaira-therapeutics/x-cell](https://github.com/xaira-therapeutics/x-cell) | `7195c647b8` | 2026-03-16 | 2 MB | 见仓库 LICENSE（SPDX 未识别） | 扩散语言模型生成表达谱 |
| `Lingshu-Cell` | [alibaba-damo-academy/Lingshu-Cell](https://github.com/alibaba-damo-academy/Lingshu-Cell) | `0cbde2feb6` | 2026-07-23 | 3 MB | MIT | 生成式细胞世界模型 |
| `MORPH` | [uhlerlab/MORPH](https://github.com/uhlerlab/MORPH) | `445fcf9557` | 2026-08-10 | 163 MB | MIT | 跨条件、跨模态的扰动结果预测；含 `transfer_learning` 目录 |
| `perturbation-decomposition` | [xinyizhanglab/perturbation-decomposition](https://github.com/xinyizhanglab/perturbation-decomposition) | `a152147806` | 2026-07-24 | 1 MB | **无许可证文件** | 把响应分解为可迁移分量与背景特异分量 |
| `pertpy` | [scverse/pertpy](https://github.com/scverse/pertpy) | `582419c353` | 2026-09-10 | 11 MB | MIT | 扰动分析的通用工具包（差异表达、距离、混合模型） |

## 3. 数据与社区

| 本地目录 | 上游 | commit | 上游日期 | 体积 | 许可 | 用途 |
|---|---|---|---|---:|---|---|
| `scPerturb` | [sanderlab/scPerturb](https://github.com/sanderlab/scPerturb) | `b69f72a070` | 2025-02-25 | 405 MB | 见仓库 LICENSE（SPDX 未识别） | 统一化扰动数据集的来源工具与文档；`revision/` 与 `dataset_processing/` 记录了各公开 screen 是怎么被统一到同一 raw-count 流程的 |
| `vcc2026-h1-benchmark` | [forrestsheldon/vcc2026-h1-benchmark](https://github.com/forrestsheldon/vcc2026-h1-benchmark) | `d28dd0496c` | 2026-09-05 | 2 MB | MIT | **已采用的 H1 开发基准**（v0.2.0），见 [H1 benchmark 审计](../research/h1-benchmark-audit.md) |
| `virtual-cell-challenge-2026` | [forrestsheldon/virtual-cell-challenge-2026](https://github.com/forrestsheldon/virtual-cell-challenge-2026) | `9f9063cdae` | 2026-09-16 | 121 MB | MIT | 参赛者 Forrest Sheldon 的 2026 参赛代码与分析；`metadata/` 与 `reports/` 是其主要体积。与其[博客系列](../blogs/README.md)配套阅读 |

## 4. 使用与法律边界

1. **许可状态未全部核实。** 表内「无许可证文件」的两个官方仓库（`state-reproduce`、`arc-virtual-cell-atlas`）和一个模型仓库（`perturbation-decomposition`）没有随附授权文件，默认保留全部权利：可以本地阅读和核验，但在复制代码片段、再分发或用于衍生作品前必须先确认授权。
2. **数据许可与代码许可独立。** `scPerturb`、`vcc2026-h1-benchmark` 的代码许可不覆盖其引用的数据集；训练数据的使用条件要回到各数据集的原始条款与比赛规则。
3. **浅克隆不等于固定版本。** 本表的 `commit` 是收集当日的默认分支最新提交；后续 `git pull` 会推进 HEAD。任何写进结论的数值都要记录当时实际使用的 commit。
4. **体积。** 全部副本合计约 **773 MB**，均在 Git 忽略目录内，不影响仓库体积。若要删除重建，按上表逐条重新克隆即可；本表的 commit 列为重建时的对照基准。
5. **不做仓库内嵌。** 不把这些仓库改用 submodule 或复制进 `docs/`：它们的体积和许可状态都不适合入库，登记表 + 固定 commit 已满足可复核要求。

## 5. 待补

- 逐仓库核对实际许可证文本，把「SPDX 未识别」改成确定的许可结论。
- 确认 `x-cell`、`Lingshu-Cell`、`MORPH`、`stack` 是否发布了可直接使用的权重，以及权重许可是否与代码一致。
- `scPerturb` 的 `revision/`（194 MB）与 `virtual-cell-challenge-2026/metadata/`（72 MB）的具体内容尚未逐一查看，需在使用前确认是否包含可直接消费的中间产物。
