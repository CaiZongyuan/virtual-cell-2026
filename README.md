# Virtual Cell 2026

本仓库服务于 Arc Institute 2026 Virtual Cell Challenge。目标是根据未知细胞背景中的非靶向对照单细胞转录组和待扰动基因，零样本预测 CRISPRi 扰动后的单细胞基因表达原始计数。

比赛规则、数据定义和提交格式以 [`docs/Official-website/`](docs/Official-website/) 为首要依据。论文与候选资料的采用、备选和排除记录见 [`docs/references/INDEX.md`](docs/references/INDEX.md)。

## 仓库结构

- `docs/Official-website/`：竞赛官方页面的本地资料。
- `docs/references/`：论文机器转换阅读版、引用图片和相关资料；本地 PDF 默认不提交。
- `scripts/`：可复用的研究与数据处理工具。
- `AGENTS.md`：本项目的 Agent 协作与证据管理约定。

## 环境变量

复制示例文件并在本地填写真实密钥：

```bash
cp .env.example .env
```

`.env` 已被 Git 忽略；只提交不含真实值的 `.env.example`。新增外部 API 时，把密钥或环境相关配置放入 `.env`，并同步把变量名、用途和安全默认值写入 `.env.example`。

## PDF 转 Markdown

公开论文 PDF 可以通过 MinerU 精准解析 API 转成便于阅读和 Git 管理的 Markdown：

```bash
scripts/mineru-pdf-to-markdown.sh docs/references/example.pdf
```

默认输出到 PDF 同名目录：

```text
docs/references/example/
├── example.md
└── images/
```

脚本依赖 Bash、`curl`、Node.js 和 `unzip`，从 `.env` 读取 `MINERU_KEY`。默认使用官方推荐的 `vlm` 模型；可通过 `MINERU_MODEL_VERSION=pipeline` 切换。

`docs/references/` 下的 PDF 已被 Git 忽略，只作为本地转换和逐字核验输入。应提交 Markdown、正文引用图片和 `INDEX.md` 中的 DOI/原文 URL；转换完成后可按本地存储需求保留或手动删除 PDF。这样避免把可能受再分发许可限制的论文原文上传到远端，也避免 PDF 持续增大 Git 历史。

本机 WSL 使用代理的 Fake-IP DNS。脚本只在自身网络请求中清除代理变量，通过公共 DNS 获取真实 IPv4 地址并使用 `curl --resolve` 直连；它不会修改 WSL 或宿主机的全局代理设置。

MinerU 产物是机器转换阅读版，可能出现 OCR、连字、公式或版面识别错误。逐字引用、数据和公式必须回到本地 PDF 或出版方原文核验，`docs/references/INDEX.md` 应记录权威原文 URL、DOI、版本以及 Markdown 阅读版。
