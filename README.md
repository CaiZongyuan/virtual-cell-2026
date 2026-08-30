# Virtual Cell 2026

本仓库服务于 Arc Institute 2026 Virtual Cell Challenge。目标是根据未知细胞背景中的非靶向对照单细胞转录组和待扰动基因，零样本预测 CRISPRi 扰动后的单细胞基因表达原始计数。

比赛规则、数据定义和提交格式以 [`docs/Official-website/`](docs/Official-website/) 为首要依据。论文与候选资料的采用、备选和排除记录见 [`docs/references/INDEX.md`](docs/references/INDEX.md)。

当前竞争性实施建议、验证门和最终轮运行顺序见 [`docs/research/vc2026-completion-strategy-primary.md`](docs/research/vc2026-completion-strategy-primary.md)。

具体数据下载单、模型组合、算力预算与排行榜目标见 [`docs/research/vc2026-data-compute-capacity-sources.md`](docs/research/vc2026-data-compute-capacity-sources.md)。

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
