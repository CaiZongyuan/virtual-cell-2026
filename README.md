# Virtual Cell 2026

本仓库服务于 Arc Institute 2026 Virtual Cell Challenge。目标是根据未知细胞背景中的非靶向对照单细胞转录组和待扰动基因，零样本预测 CRISPRi 扰动后的单细胞基因表达原始计数。

比赛规则、数据定义和提交格式以 [`docs/Official-website/`](docs/Official-website/) 为首要依据。论文与候选资料的采用、备选和排除记录见 [`docs/references/INDEX.md`](docs/references/INDEX.md)。

**当前方向：复用文献公开预训练权重微调，完善数据，在本地比较 State、Stack 等模型；暂停官方提交。** 分阶段执行与评价边界见[本地微调方案](docs/research/pretrained-finetuning-local-plan.md)，服务器与 SwanLab 操作见 [server/README.md](server/README.md)。

首轮已完成 State 微调、H1 六指标评价和一次有效提交，但模型显著差于 NTC 对照；结果与新增诊断见[失败复盘](docs/research/state-first-run-postmortem-2026-09-25.md)。后续先验证原生接口和表达校准，不从零预训练基础模型。未来恢复提交后使用随机公开名称，内部保留模型来源与结果映射。

课程总览、课号对照与主题归属见[课程索引](docs/lessons/README.md)。学习材料见[第 03 课：State 上手](docs/lessons/03-State上手.md)；历史预算和首投安排以当前本地方案、真实运行记录为准，不直接作为启动命令。

可运行学习版见 [notebook/](notebook/README.md)：三份 ipynb 依次探索本地 A/B/C 数据、State 配置与集合模型、计数输出与资源预算。运行 `uv sync --group notebook --frozen` 后选择仓库 `.venv` kernel；默认 CPU，已保留真实执行输出。

H1 本地评分已经跑通，后续保留开发背景并增加其他整背景留出；工具合同与训练泄漏边界见[H1 benchmark 审计](docs/research/h1-benchmark-audit.md)。

竞争性实施建议、验证门和最终轮运行顺序见[总体策略](docs/research/completion-strategy-primary.md)。

具体数据下载单、模型组合与历史算力预算见[容量规划](docs/research/data-compute-capacity-sources.md)。

STATE 之后的新架构调查、任务对齐矩阵与最小消融顺序见[架构调查](docs/research/post-state-architecture-review.md)。

此前分解式模型的领域对象和 V0 研究草案见[历史实现规格](docs/research/model-implementation-spec.md)；[首投方案](docs/research/first-submission-plan.md)保留作历史记录，当前主模型与运行顺序以本地微调方案为准。

## 仓库结构

- `docs/Official-website/`：竞赛官方页面的本地资料。
- `docs/references/`：论文阅读材料、引用图片和索引。
- `scripts/`：可复用的研究与数据处理工具。
- `AGENTS.md`：本项目的 Agent 协作与证据管理约定。

## 环境变量

复制示例文件并在本地填写真实密钥：

```bash
cp .env.example .env
```

`.env` 已被 Git 忽略；只提交不含真实值的 `.env.example`。新增外部 API 时，把密钥或环境相关配置放入 `.env`，并同步把变量名、用途和安全默认值写入 `.env.example`。
