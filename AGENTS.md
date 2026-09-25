# Virtual Cell 2026

## 项目

本仓库服务于 Arc Institute 2026 Virtual Cell Challenge。核心任务是：根据未知细胞背景的非靶向对照单细胞转录组和待扰动基因，零样本预测 CRISPRi 扰动后的单细胞基因表达原始计数。

- 竞赛规则、数据和提交格式以 `docs/Official-website/` 为首要依据；实现前核对相关页面。
- 科研检索遵循下文的分层流程；接口合同见 `docs/Infra-Agent-Research-Search-Guide.md`，当前路由依据见 `docs/research/literature-search-stack-benchmark.md`。
- 明确区分已验证事实、论文结论、工程假设和待验证猜想，并保留来源与不确定性。

## 科研检索

先查 `docs/references/INDEX.md`，复用已评估材料并识别缺口；再把问题改写为包含生物对象、任务、细胞背景和方法的高信号英文查询。每个检索任务先执行一个查询，只在结果明显缺失时精炼一次，并记录来源、查询词、调用次数、失败和未解决缺口。

### 来源路由

1. **默认发现：**使用 `$infra-scholar-search` 直接调用 Scholar HTTP API，先看前 10 条的题名、DOI、摘要、版本和来源。它是本项目日常主题检索及题名/DOI 查找的第一入口；保持顺序调用，最多不超过已验证的 QPS 3。
2. **证据与结构补全：**需要自然语言证据片段、可定位全文、图表或相关工作时使用 `$sciverse`；需要年份、作者、期刊、OA、引用量等硬筛选时先 `meta-search`，再把候选 `doc_id` 作为硬范围做语义检索。元数据结果按 DOI 和版本去重，不能把预印本与正式版当成两项独立证据。
3. **ML 方法精读：**只对单细胞机器学习方法、模型组件和 benchmark 使用 `$sciverse-paper-schema`。其语料主要是已解析的 AI 会议论文；空结果仅表示该语料未收录，不能推出生命科学文献中不存在。
4. **覆盖审计：**用户要求系统综述、跨库高召回、MeSH、严格引文核对或引用管理时使用 `$nature-academic-search`，按 PubMed/CrossRef/arXiv 的 T1 来源开始，再按需扩展 Semantic Scholar、bioRxiv/medRxiv。MCP 不可用时的 OpenAlex fallback 只作补充召回，不替代 PubMed 或原文核验。
5. **窄源工具：**OpenCLI arXiv 仅用于明确的 arXiv 题名、ID、作者或预印本查询；Semantic Scholar 仅在需要引文图或相关推荐且 API 当前可用时启用。`$nature-literature-pipeline` 只用于用户明确要求的定时文献监控或推送，不用于一次性交互检索。

### 收敛与核验

1. 合并结果时先规范化 DOI；无 DOI 时用规范化题名和第一作者识别重复。合并预印本、会议版和正式出版版，保留版本关系，并优先采用元数据更完整的正式来源。
2. 搜索返回的标题、snippet、摘要、引用数和模型生成总结都只是候选线索。影响项目决策的机制、方法、数据、指标和数值必须回到 DOI/出版页、预印本原文、数据集或官方代码核验；SciVerse 证据同时保留 `doc_id`、offset/页码和题名。
3. 一次精炼后若不再出现新的高优先级方法，且关键结论已有一手来源，即停止扩搜。若来源失败或覆盖不足，报告已检索范围和缺口；“未命中”不得表述为“研究不存在”。
4. 完成标准：所有实际用于判断的候选均在 `docs/references/INDEX.md` 中标为采用、备选或排除；检索台账完整；关键结论均有可复核的一手来源。未查看题名或摘要的原始命中不必逐条入索引。

## 协作对象

用户熟悉软件开发、AI 和 Agent，但生物学约为高中水平。生物知识会影响理解或决策时，主动教学：

1. 首次出现的术语给出中文、英文或缩写及一句话定义。
2. 按“直觉解释 -> 生物机制 -> 与比赛任务的关系 -> 对数据或模型的影响”展开；只讲当前问题需要的深度。
3. 可借用软件或机器学习类比，但要标明类比的边界，不能把类比当作生物机制。
4. 对基因表达、scRNA-seq、UMI、CRISPRi、Perturb-seq、细胞背景、批次效应等基础概念不默认用户已经掌握。
5. 发现用户的生物学前提有误时，先纠正并解释原因，再继续设计或实现。

### 教程制作

编写或修改教程、系统教学、制作或审校教程配图时，加载 [tutorial-authoring](.agents/skills/tutorial-authoring/SKILL.md)；教学深度、绘图工具、可读性和资产规则按需读取。

## 论文与文档

- `docs/references/` 保存与项目高度相关、可复核的论文阅读材料；必须在索引中保留权威原文 URL/DOI。论文 PDF 仅作本地核验输入，默认由 `.gitignore` 排除，不提交到 Git；摘要、转述、机器转换或翻译须标明性质，不能冒充原文。
- 对公开论文 PDF，如 Markdown 更便于阅读和版本管理，可运行 `scripts/mineru-pdf-to-markdown.sh` 使用 MinerU 生成带图片的机器转换阅读版；只提交 Markdown 和正文引用图片。PDF 或出版方原文仍是逐字引用、公式和数据核验的权威来源。MinerU 请求必须在进程级禁用代理并绕过 WSL Fake-IP DNS，不修改系统全局代理。
- 每次检索、阅读或新增论文后，同步更新 `docs/references/INDEX.md`。至少记录规范标题、摘要、原文链接/DOI、本地文件、与项目的核心关联、相关论文及关系、关键词、版本或年份、检索日期；缺失项明确标为待核验。
- 索引用于记录所有已评估的候选论文，不只记录最终采用的论文；说明采用、备选或排除及理由，避免重复检索。
- MinerU 和后续外部 API 的密钥、Token 或机器相关配置保存在根目录 `.env`；提交同步更新但不含真实值的 `.env.example`，不得把密钥写入脚本、文档、日志或 Git。
- 用户明确要求保存或同步到飞书时，使用飞书文档，并保存到 `纳友科技内部知识库/虚拟细胞`；同步前查看该节点的现有层级，按内容主题复用或自主创建合适的子目录。未明确要求时先保留在仓库内。

### Git 文件体积

1. 创建、下载、转换或生成文件时持续关注仓库体积；在每次 `git add` 或 `git commit` 前检查全部已修改和未跟踪文件的实际大小，重点核查 PDF、图片、音视频、压缩包、数据集、模型权重、构建产物及其他二进制文件。单文件达到 1 MiB 或相较原版本明显增大时必须评估，GitHub 的 100 MiB 硬限制不能当作可接受体积标准。
2. 只提交项目需要且适合版本管理的成品。可再生的原图、候选输出、缓存和中间产物放入 Git 忽略目录；需要入库的图片等资产在不损害用途的前提下压缩；不适合普通 Git 的大文件改用外部存储或 Git LFS，并在仓库中保留可复核的来源、校验和或获取说明。
3. 若无法安全压缩、无法判断文件是否应入库，或需要在压缩、忽略、Git LFS 与外部存储之间作产品取舍，必须在暂存或提交前向用户说明文件路径、大小、可选方案及影响，得到决定后再继续。提交前再次核对暂存快照，确保没有意外大文件、密钥或本地输出。

## Agent skills

### Issue tracker

Issues 与 specs 以 GitHub issue 形式存放在 `CaiZongyuan/virtual-cell-2026`，全部操作走 `gh` CLI（本机需先配 git `safe.directory`，见文档）。See `docs/agents/issue-tracker.md`.

### Triage labels

沿用五个标准 triage 角色名（`needs-triage` / `needs-info` / `ready-for-agent` / `ready-for-human` / `wontfix`），另加 `spec` 与 `tutorial`。See `docs/agents/triage-labels.md`.

### Domain docs

single-context：根目录 `CONTEXT.md` 是唯一术语权威，`docs/lessons/README.md` 是教程唯一入口，尚无 `docs/adr/`。See `docs/agents/domain.md`.
