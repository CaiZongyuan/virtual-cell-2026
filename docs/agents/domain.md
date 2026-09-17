# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root — 本项目的**领域术语表与唯一权威定义**。
- **`docs/adr/`** — 本仓库**目前不存在**，不要主动创建。

补充材料（按需读，不要无条件全读）：

- `docs/lessons/README.md` — 教程的**唯一入口**：三层结构、阶段表、课程总表、
  两种 8 步样板、三条成绩线、算力边界、**主题权威归属表**、已知欠债。
- `docs/references/INDEX.md` — 已评估论文索引（采用 / 备选 / 排除及理由）。
- `docs/research/` — 本项目的决定与证据。**教材 → 研究文档是单向引用**，教材不复制研究文档内容。

Layout: **single-context**（`CONTEXT.md` 在根目录，无 `CONTEXT-MAP.md`，无 monorepo 信号）。

## Use the glossary's vocabulary

Issue 标题、spec、ticket、测试名里出现领域概念时，用 `CONTEXT.md` 定义的词，不要漂移到它明确避开的同义词。

本仓库高频词汇（完整定义见 `CONTEXT.md`）：

| 词 | 一句话 |
| --- | --- |
| **赌注** | 一套关于「什么让扰动响应可预测」的核心假设；领域里共五种（效应迁移 / 条件化生成 / 分解式 / 表征预训练 / 世界模型） |
| **效应迁移** | 假设扰动效应可以跨细胞背景复用 |
| **条件化生成** | 假设响应对背景与靶点都是条件依赖的，需要显式条件化 |
| **噪声地板** | 由测量与抽样造成的不可约误差下限；「改进是否真实」的阈值 |
| **课号** | `L<层>-<序号>`：L0 锚点 / L1 领域地图 / L2 模型深潜 / L3 比赛实施。**不是连续数字** |
| **阶段** | 阅读顺序，共 6 个；层编号不是阅读顺序 |
| **三条成绩线** | 生物效应线 / 群体分布线 / 工程合同线，每次实验同时记录 |

**证据分级必须用同一套写法**：`[S#]` 官方事实、`[P#]` 论文章节（未复现）、**工程假设**、
**参赛者自报**（额外一级，待复核）。四者不混写。

## Flag ADR conflicts

本仓库还没有 `docs/adr/`。真正需要记录新决策时，先看
`docs/lessons/决策记录-教程三层重构.md`（教程方向的五条裁决记在它的 §9）——
那是当前实际生效的决策记录。若某个 ticket 与它冲突，显式指出而不要静默覆盖。
