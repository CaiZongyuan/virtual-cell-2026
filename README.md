# Virtual Cell 2026

本仓库服务于 Arc Institute 2026 Virtual Cell Challenge。目标是根据未知细胞背景中的非靶向对照单细胞转录组和待扰动基因，零样本预测 CRISPRi 扰动后的单细胞基因表达原始计数。

比赛规则、数据定义和提交格式以 [`docs/Official-website/`](docs/Official-website/) 为首要依据。论文与候选资料的采用、备选和排除记录见 [`docs/references/INDEX.md`](docs/references/INDEX.md)。

以 STATE 为基线的模型选择、GPU 训练、10–14 天首投排期与验收步骤见[首投方案](docs/research/first-submission-plan.md)；当前提交格式与精确截止时间见[官方合同核验](docs/research/submission-contract-check.md)。

初始化优先复用 Arc 已发布的 Replogle STATE 检查点，先小批推理，再决定哪些层需要微调；从头训练不作为前置要求。已发布权重的结构与当前源码默认值不同，必须继承实际配置。**A100 80 GB / 150 小时是完整训练分支的备选预算，尚非启动采购要求。** 资产、源码与兼容边界见[STATE 审计](docs/research/state-training-source-audit.md)。

课程总览、课号对照与主题归属见[课程索引](docs/lessons/README.md)。按步骤学习与实施见[L3-04：State 微调实战与算力预算](docs/lessons/L3-04-State微调实战与算力预算.md)：包含分批数据下载单、预训练权重选择、`init_from` 微调命令、基因/靶点迁移、原始计数生成、H1 评分、打包，以及从单张 24 GB GPU 起步的资源测量方法。原生命令与需要自行实现的适配部分分别注明，预算尚未经过 GPU 训练实测。

可运行学习版见 [notebook/](notebook/README.md)：三份 ipynb 依次探索本地 A/B/C 数据、State 配置与集合模型、计数输出与资源预算。运行 `uv sync --group notebook --frozen` 后选择仓库 `.venv` kernel；默认 CPU，已保留真实执行输出。

首投先接入 H1 开发评分，再做多背景留出；工具合同、训练泄漏边界和资源要求见[H1 benchmark 审计](docs/research/h1-benchmark-audit.md)。

竞争性实施建议、验证门和最终轮运行顺序见[总体策略](docs/research/completion-strategy-primary.md)。

具体数据下载单、模型组合与历史算力预算见[容量规划](docs/research/data-compute-capacity-sources.md)。

STATE 之后的新架构调查、任务对齐矩阵与最小消融顺序见[架构调查](docs/research/post-state-architecture-review.md)。

此前分解式模型的领域对象和 V0 研究草案见[历史实现规格](docs/research/model-implementation-spec.md)，当前主模型与运行顺序以首投方案为准。

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
