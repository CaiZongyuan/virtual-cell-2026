# SciVerse 可用服务与免费额度调查

> 调查日期：2026-08-22（Asia/Shanghai）
> 范围：SciVerse / SciBase 官方网站、开发者文档、API 页面、账户入口；未使用第三方套餐信息。
> 域名说明：用户提供的 `sciverse.opendatalab.com` 与页面 canonical 使用的 `sciverse.space` 均为官方入口。本文链接保留实际核验时使用的 OpenDataLab 域名。

## 结论先行

1. **最值得项目接入的是 Sciverse 的元数据检索、语义证据检索、原文读取和引用关系 API。** 它适合发现 CRISPRi、Perturb-seq（把基因扰动和单细胞测序结合的实验方法）、单细胞转录组及扰动预测论文，并把候选结论回到原文核验。
2. **官方没有公布一个固定的“免费用户每天 N 次”额度。** 官方只承诺“基础试用额度，具体以账号权限为准”，且明确说公开文档“不承诺固定额度”。注册账号的每日总量只能登录 [调用统计](https://sciverse.opendatalab.com/stats) 后查看。[S1][S2]
3. **`30/min` 是默认限速，不是免费日额度。** 当账号没有配置接口独立规则时，系统默认按每接口 30 请求/分钟保护；账号仍可能另有每日总量。[S2]
4. **积分、并发、每日重置时刻和下载流量上限均未公开。** 文档确认存在“每日额度重置”，但未说明几点重置或采用哪个时区。[S2][S10]
5. **Paper Schema 很强，但当前主要覆盖 100 万+ AI 会议论文。** 它适合读取扰动预测模型、机器学习方法和 benchmark 论文，不适合作为细胞生物学文献主检索源。[S9][S11]
6. **没有核实到面向普通 API 用户的机构检索接口，也没有个性化推荐 API。** 可用的是作者/期刊实体集合、引用/被引/相关工作，以及基于论文或实体的 related-paper 扩展；不能把这些宣传为机构画像或个性化推荐服务。[S5][S6][S9]

## 事实状态约定

- **已核实事实**：官方页面明确写出，本文给出来源。
- **官方未披露**：检查了官方 docs、FAQ、账户/统计、API 和 pricing 常见路径后仍无公开数值。
- **项目判断**：根据比赛任务作出的工程建议，不代表 SciVerse 官方承诺。

## 项目账号实际测试

2026-08-22 使用项目 `.env` 中的 `SCIVERSE_API_TOKEN` 做了最小真实调用；Token 未写入报告、Skill 或命令输出。当前 shell 没有设置 `HTTP_PROXY`、`HTTPS_PROXY` 或 `ALL_PROXY`，在继承当前网络环境和显式移除这些标准代理变量两种情况下，请求均返回 HTTP 200。因此可以确认**这台机器当前的实际网络路径可访问 SciVerse**，但仅凭应用层环境无法判断流量是否仍经过操作系统/TUN 代理，也不能推出所有代理出口都不会被拒绝。

| 实测入口 | 结果 | 观察 |
|---|---:|---|
| `GET /meta-catalog` | HTTP 200 | 返回 65 个账号可见字段；安装后的 `list_catalog` 脚本复测通过 |
| `POST /meta-search` | HTTP 200，约 0.33 s | 能召回零样本单细胞扰动论文；一次宽泛查询的前三条是同一 Zenodo 工作的不同版本，进入候选池前需要按 DOI、标题和版本去重 |
| `POST /agentic-search` | HTTP 200，约 2 s | 召回 CellForge、AttentionPert、PerturbDiff 等直接相关工作，证据相关性明显好于宽泛关键词检索 |
| `GET /content` | HTTP 200 | 能按 `doc_id` 和 offset 返回论文原文上下文 |
| `GET /resource` | HTTP 200 | 返回有效 JPEG，11,430 bytes，445 x 198；说明图表二进制读取链路可用 |
| `POST /meta-paper-relations` | HTTP 200 | 测试论文返回 0 条已索引关系；这是该记录无关系数据，不是接口错误 |
| `GET /paper-schema` | HTTP 200 | 返回能力契约、资源、Entity/Relation/Evidence 分类和限制；安装后的能力脚本复测通过 |
| `POST /paper-schema/search` | HTTP 200，约 83 ms | 5 条小样本均与单细胞扰动预测相关，包括 PertEval-scFM、Departures、Wasserstein-1 neural OT、零样本分子扰动预测和 CycSeq |

所有响应均未包含可用于推断账号日总量的限额响应头。Bearer API 也没有公开的 `/stats` 读取合同，所以本次实测仍无法安全、可靠地得到该账号的 `daily_limit`；精确数字需在登录态网页 [调用统计](https://sciverse.opendatalab.com/stats) 查看。

## 数据底座与更新

SciBase 官方实时概览在调查日展示：约 **4.54 亿**知识记录、**3.73 亿**文献记录、8,106 万图书记录、7,000 万专利记录、**3,055 万 AI-Ready OA 全文**和 236 万期刊/会议来源；这说明“有元数据”远多于“有可读全文”，不能假定每条检索结果都能调用 `/content`。[S12]

官方 FAQ 还称数据库覆盖 814 种语言；主流期刊/预印本源按 T+1 增量入库，全量快照按月刷新，Nature、Science、Cell 等高优先级源按天接入。[S1] 这些是平台覆盖与更新声明，不等于对某个具体生物医学来源的完整性保证，正式使用前仍应与项目默认的 Infra Scholar 检索结果做抽样召回对照。

## 服务地图与项目优先级

官方开发者目录目前列出 7 个一级 REST 入口，其中 6 个是常规文献能力，`paper-schema` 为 Beta 命名空间。[S1][S9]

| 能力 / 服务 | 官方能力边界 | Virtual Cell 2026 用途 | 优先级 |
|---|---|---|---|
| `POST /agentic-search` | 自然语言语义检索，返回 evidence chunk、标题、`doc_id`、相关度、offset/页码；**不生成最终回答**。`top_k` 1–100，未启用子查询时实际通常至多约 50 条 | 找与“CRISPRi 后的单细胞表达响应”“零样本扰动预测”“未知细胞背景泛化”等问题直接相关的证据段落；给候选论点保留可追溯位置 | **高** |
| `POST /meta-search` | 结构化元数据检索；支持论文、作者、来源期刊集合，DOI、作者、年份、期刊、语言、OA/许可、引用数、FWCI、主题等筛选/排序；不返回正文证据 | 建候选论文池、DOI 去重、按年份/引用影响/OA 许可筛选、趋势统计；作者集合可用 ORCID 关联，来源集合可用 ISSN 关联 | **高** |
| `GET /meta-catalog` | 运行时返回字段、过滤算子、排序/投影权限；样本值缓存 24 小时且不代表全集 | 在检索脚本中动态生成合法过滤器，避免字段名和账号权限变化导致流水线失效 | **中（基础设施）** |
| `GET /content` | 按 `doc_id` 和字符 offset/limit 读取 Markdown/纯文本；并非所有元数据记录都有全文；不负责判断事实 | 精读方法、数据、实验设置、限制，核验摘要/检索片段是否真的支持项目结论 | **高** |
| `GET /resource` | 按正文给出的相对路径下载图、表、PDF 等二进制资源；不搜索或解释图片 | 获取模型图、benchmark 表、补充实验图，再交给人工或多模态模型解析 | **中** |
| `POST /meta-paper-relations` | 按论文 `unique_id` 分页返回 `CITATIONS`、`REFERENCES`、`RELATED_WORKS`；关系条目不是正文证据 | 向前追参考文献、向后看被引、扩展相关工作，构建方法谱系并发现遗漏论文 | **中高** |
| `/paper-schema/*`（Beta） | 把论文解析为 Paper、Entity、Relation、Evidence、Citation、Provenance；18 个路由共享一个配额；主要覆盖 100 万+ AI 会议论文 | 对扰动预测、foundation model、单细胞 ML 方法论文做结构化精读、方法/benchmark 对比和复现材料整理 | **中（仅 ML 文献）** |

来源：`agentic-search` [S3]、`content` [S4]、`meta-search`/`meta-catalog` [S5][S6]、引用关系 [S7]、资源 [S8]、Paper Schema [S9]。

### 用户特别关心的能力边界

| 问题 | 结论 | 状态 |
|---|---|---|
| 科研检索 | 语义证据检索和结构化元数据检索均已公开 | 已核实 |
| 论文元数据 | 标题、摘要、作者、DOI、来源、年份、主题、OA/许可、引用指标等；具体字段受 Token 权限影响 | 已核实 |
| 全文 | 可按 `doc_id` 读取，但只有有全文 artifact 的记录才有 `doc_id`，并非全库覆盖 | 已核实 |
| 引用 | 可查引用、被引、相关工作；Paper Schema 还能区分完整 Reference 与已解析图边 | 已核实 |
| 作者 | `meta-search` / `meta-catalog` 支持 `collection=authors`，可用 ORCID 与论文关联；论文也有作者字段 | 已核实 |
| 机构 | SciBase 宣传企业级“机构画像/机构链接”，但公开 `meta-search` 合同只列 `papers/authors/sources`，未找到普通用户可调用的 institution collection 或机构 API | **公开 API 未核实** |
| 推荐 | 有 `RELATED_WORKS`、Paper Schema 的 related-papers 和网页“推荐阅读”工作流；它们是论文关系/相似性扩展，不是用户画像驱动的个性化推荐 | 已核实边界 |
| AI 阅读 | 通用 API 提供片段、全文和图表，不直接生成综述；上层 Skill/外部 LLM 可完成阅读。Paper Schema 提供结构对象、证据和材料包，也不是自动写作黑盒 | 已核实边界 |
| 批量数据 | SciBase 有 Hugging Face 数据入口；API 的批量下载总量、流量或文件大小免费额度没有公开 | 部分核实 / 额度未披露 |

## Agent Skills 与 SDK

### 已安装到本项目

已把两个对本项目有直接价值的 Skill 安装到项目级目录，后续 Agent 会从 `.agents/skills/` 发现它们：

| 本地路径 | 来源 | 用途与验证 |
|---|---|---|
| `.agents/skills/sciverse/` | SciVerse 的 `/.well-known/skills` 分发包 [S13] | 6 个通用检索/全文/资源工具；`list_catalog` 和 `search_papers` 已用项目 Token 实测通过 |
| `.agents/skills/sciverse-paper-schema/` | Paper Schema 文档配套仓库 [S18] | 9 个结构化论文工具；`paper_schema_capabilities` 和 `search_paper_schemas` 已实测通过 |

安装前后检查了脚本源码：网络目标限制为 `sciverse.space` 及其子域，Paper Schema 封装对路由和输入字段采用正向允许列表，未发现子进程执行或 Token 日志输出；并用项目 Token 原值扫描安装目录和本报告，未发现密钥被写入文件。未安装 Agent Tools 仓库中的 `skills/sciverse-academic-retrieval`，因为它依赖另一套无关的 `SCP-HUB-API-KEY`，不能复用当前 SciVerse Token。

### 通用 Sciverse Skill：6 个工具

官方 Skills 网页说明应以 `opendatalab/Sciverse-Agent-Tools` 仓库为准。该网页的数量文案仍写“5 个”，但调查日官方仓库的最新 README 与 canonical OpenAPI 已列出以下 **6 个**工具；新增项是 `list_paper_relations`。[S13][S17]

| Skill 工具 | 对应能力 |
|---|---|
| `list_catalog` | 元数据字段与过滤算子发现 |
| `search_papers` | 结构化论文元数据检索 |
| `semantic_search` | 自然语言证据片段检索 |
| `list_paper_relations` | 分页读取引用、被引和相关工作 |
| `read_content` | 分段读取原文 |
| `get_resource` | 获取图表和附件二进制 |

可通过 MCP server、ClawHub Skill、Python SDK 或 TypeScript SDK 使用；它们共用同一个 `SCIVERSE_API_TOKEN` 和账号配额，不会因为换成 Skill/SDK 获得另一份免费额度。[S13]

### Paper Schema Skill：9 个意图工具

`paper_schema_capabilities`、`search_paper_schemas`、`discover_related_papers`、`query_paper_entities`、`query_paper_relations`、`query_paper_citations`、`query_paper_evidence`、`resolve_paper_context`、`build_paper_materials`。[S11]

这 9 个工具封装以下 18 个 REST 路由：[S9]

| 分组 | 路由 |
|---|---|
| 能力发现 | `GET /paper-schema` |
| 论文发现 | `POST /paper-schema/search`；`POST /paper-schema/entities/related-papers`；`POST /paper-schema/schemas/{schema_id}/related-papers` |
| Entity | `POST /paper-schema/entities/search`；`GET /paper-schema/schemas/{schema_id}/entities`；`GET /paper-schema/schemas/{schema_id}/entities/{entity_id}` |
| 论文内部关系 | `POST /paper-schema/relations/search`；`GET /paper-schema/schemas/{schema_id}/relations/{relation_id}` |
| 外部引用 | `GET /paper-schema/schemas/{schema_id}/citation-summary`；`GET /paper-schema/schemas/{schema_id}/citations`；`GET /paper-schema/schemas/{schema_id}/citation-graph` |
| 证据与原文 | `POST /paper-schema/evidence/search`；`GET /paper-schema/schemas/{schema_id}/evidence/{evidence_id}`；`POST /paper-schema/resolve-provenance`；`POST /paper-schema/search-in-schema`；`POST /paper-schema/hydrate-items` |
| 研究材料 | `POST /paper-schema/materials` |

## 免费用户额度：能确认什么

### 官方明确披露

| 项目 | 官方规则 | 不应如何解读 |
|---|---|---|
| 套餐/试用 | “提供基础试用额度，具体以账号权限为准。”[S1] | 不能据此推出所有新账号额度相同 |
| 每日总量 | 配置了每日总量时，所有公开 API 与 Skills 调用计入当日用量；实际数值由账号配置驱动 [S2] | 公开页面没有“免费每天 N 次” |
| 分钟限速 | 未配置接口独立规则时，系统默认保护值为 **30 次/分钟/接口** [S2] | **这是速率保护，不是日额度，也不是并发数** |
| Paper Schema | 默认 **30 请求/分钟/用户**；18 个操作统一计入 `paper-schema` 资源；日配额与其他公开 API 共用 [S9] | 不是每个子路由各有 30/min |
| 引用关系 | 页面明确列出默认 **30 请求/分钟（用户级）** [S7] | 账号独立规则仍可能覆盖 |
| 超限 | HTTP `429`；分钟窗口恢复或每日额度重置后再试，Paper Schema 优先读 `Retry-After`/`retry_after` [S2][S9] | 不应立即并发重试 |
| Token | Token 长期有效，可注销/重建；每账号最多 10 个 [S10] | 多建 Token 不代表能绕过账号级额度 |
| 实时查看 | 登录统计页查看实时日配额、今日已用、今日剩余和各接口分钟限制 [S2] | 未登录无法看到某账号具体数值 |

### 官方未披露

截至 2026-08-22，未在官方公开页面找到以下数字：

- 免费用户固定每日调用数；
- 月度调用量或月度费用；
- 积分/credit 的发放数、消耗规则或重置周期；
- 全局并发请求数；
- 每日重置的具体时刻和时区；
- `/content` 或 `/resource` 的每日下载次数、总字节数和单文件大小上限；
- 免费、个人、团队、商业等公开套餐对照表；`/pricing` 在调查日返回 404。

因此，对“免费用户额度多少”的严谨回答是：**公开固定数值未知；只有账号登录后的统计页能给出该账号的真实日额度。公开可确认的默认值仅为 30/min/接口的分钟保护。**

首页代码中还出现“三种方式可选 · 全部免费调用”的宣传文案，但同一官方文档同时明确写“基础试用额度，具体以账号权限为准”。这最多说明 API、SDK、Skills 三种接入形态没有公开的单独入场价格，**不能解释为不限量永久免费**。[S1][S14]

### 单次请求容量不是套餐额度

这些参数有助于估算一次研究任务的调用数，但不能当作免费额度：[S3][S4][S5][S7][S8][S9]

- `agentic-search`：`top_k` 1–100；未开子查询时实际通常至多约 50；`doc_id` 硬约束集合默认最多 1,000 个。
- `meta-search`：`page_size` 1–200；浅翻页 `page * page_size <= 10000`，更深使用 cursor。
- `meta-paper-relations`：每页 1–200，默认 25。
- `content`：传 offset 时默认每次 700 个 Unicode 字符；推荐用 `next_offset`/`more` 分段读取。页面没有给出账号级文本下载总量。
- `resource`：一次按一个安全相对路径返回二进制；没有公开文件大小或账号级流量额度。
- Paper Schema：各操作另有论文数、分页、图深度、节点/边和批量项上限；例如材料包最多 20 篇，批量上下文补全最多 50 项。

## 数据许可对项目的影响

官方把“可以调用”与“可以持久化/再分发”分开：[S15]

- 书目元数据可使用、存储和再分发，包括商业用途。
- 把取得的文本作为模型的临时上下文，官方视为允许的瞬时使用。
- 把全文持久化到向量库、缓存或数据库，需在**入库时**按每条记录的 `access_license` 过滤。
- 图片可能与论文正文采用不同许可；不能仅因论文 OA 就假定图片可独立再分发。
- 官方称可按许可筛出逾 5,000 万篇允许再分发和商用的论文、逾 6,500 万篇带任一开放许可的论文。

对本仓库的直接含义：检索、临时阅读和证据核验可先做；若要建立本地全文/RAG 索引，必须保存 `unique_id`/DOI、来源、许可和抓取日期，并在写入前过滤许可，不能把所有 `/content` 结果无差别长期保存。

## 相邻产品

| 产品 | 官方开放状态 | 对本项目判断 |
|---|---|---|
| SeqStudio | 官方描述为蛋白质功能注释平台，整合 BLAST、InterProScan、Foldseek、TMHMM 和可选 LLM；支持 FASTA/PDB 及批处理。当前文档明确说尚未写公开 HTTP API、限流和鉴权，主要是在线访问/本地部署 [S1] | **低到中**。可辅助解释扰动基因编码蛋白的功能，但蛋白同源/结构功能不能直接推出 CRISPRi 后整套转录组响应；后者还受细胞背景、调控网络和细胞状态影响 |
| DianShi | 化学信息与逆合成 RAG，需要申请授权；不是注册即默认可用 [S1] | **低**。比赛核心是基因扰动，不是小分子扰动；只有研究代谢物/化合物机制时才有旁路价值 |
| Sci-Align / Sci-Evo | 官方生态页标记为“敬请期待” [S16] | **暂不可用**，不能纳入当前工程计划 |

## 建议的接入顺序

1. **保持 Infra Scholar 为默认科研检索入口**，按仓库规则继续从论文或官方原文核验；把 SciVerse 作为第二检索源和全文证据层，先测其对生命科学/单细胞主题的实际召回。
2. 用 `meta-search` 建结构化候选池，保存 DOI、`unique_id`、`doc_id`、OA/许可、年份和来源；再用 `agentic-search` 在候选 `doc_id` 集合内做语义证据召回。
3. 只对入选论文调用 `content`，并保留 offset/page/`chunk_id`；需要图表时再调用 `resource`，减少调用量和许可风险。
4. 用 `meta-paper-relations` 做引用向前/向后扩展。Paper Schema 只用于单细胞 ML/AI 方法论文，不用于判断生物学研究是否不存在。
5. 创建项目 Token 后，立即在 `/stats` 记录该账号的 `daily_limit` 和各 endpoint limit；在客户端用保守并发、429 退避和调用日志控制消耗。公开文档无法替代这一步。

建议首轮用 20–30 个已知相关论文/DOI 和 10 个项目问题做 A/B 测试，比较 Infra Scholar 与 SciVerse 的召回率、DOI 正确率、全文覆盖率、证据可定位率和每篇入选论文的平均调用数，再决定是否写入主流水线。

## 官方来源

所有页面访问日期均为 2026-08-22。

- **[S1]** [接入指南、产品总览与 FAQ](https://sciverse.opendatalab.com/docs)：7 个 API 的目录、基础试用表述、产品关系、Token/FAQ、更新频率等；公共章节可在页面中切换“调用限制”“数据使用”“常见问题”。
- **[S2]** [调用限制（接入指南内）](https://sciverse.opendatalab.com/docs#limits)：账号动态日额度、默认 30/min、统计页和 429 规则。
- **[S3]** [`agentic-search` 官方文档](https://sciverse.opendatalab.com/docs/sciverse/api/agentic-search)。
- **[S4]** [`content` 官方文档](https://sciverse.opendatalab.com/docs/sciverse/api/content)。
- **[S5]** [`meta-search` 官方文档](https://sciverse.opendatalab.com/docs/sciverse/api/meta-search)。
- **[S6]** [`meta-catalog` 官方文档](https://sciverse.opendatalab.com/docs/sciverse/api/meta-catalog)。
- **[S7]** [`meta-paper-relations` 官方文档](https://sciverse.opendatalab.com/docs/sciverse/api/meta-paper-relations)。
- **[S8]** [`resource` 官方文档](https://sciverse.opendatalab.com/docs/sciverse/api/resource)。
- **[S9]** [Paper Schema REST API](https://sciverse.opendatalab.com/docs/sciverse/api/paper-schema)：18 个路由、默认限速、共享计量与容量限制。
- **[S10]** [统一鉴权（接入指南内）](https://sciverse.opendatalab.com/docs#auth)：Token 长期有效、每账号最多 10 个。
- **[S11]** [Paper Schema Agent Skill](https://sciverse.opendatalab.com/docs/sciverse/skills/paper-schema)：9 个意图工具与 100 万+ AI 会议论文范围。
- **[S12]** [SciBase 官方概览](https://sciverse.opendatalab.com/scibase)：调查日数据规模与公开入口。
- **[S13]** [Sciverse Skills](https://sciverse.opendatalab.com/docs/sciverse/skills)：Skills 网页、MCP/SDK 接入；页面数量文案在调查日仍写 5 个。
- **[S14]** [Sciverse 在线检索首页](https://sciverse.opendatalab.com/)：“全部免费调用”界面文案及当前知识记录/全文展示。
- **[S15]** [数据使用条款（接入指南内）](https://sciverse.opendatalab.com/docs#data-usage)：元数据、全文、RAG 持久化、图片与商业使用规则。
- **[S16]** [SciVerse 生态](https://sciverse.opendatalab.com/ecosystem)：Sci-Align / Sci-Evo 开放状态。
- **[S17]** [Sciverse-Agent-Tools 官方仓库](https://github.com/opendatalab/Sciverse-Agent-Tools)：仓库 README 与 canonical OpenAPI 在调查日列出 6 个通用工具，包含 `list_paper_relations`。
- **[S18]** [Sciverse Paper Schema Skill 仓库](https://github.com/Shannon4Science/sciverse-paper-schema)：Paper Schema 的 9 个脚本、公开 manifest、输入约束与运行时说明。

## 未解决问题

以下问题只有登录项目账号或得到官方书面答复后才能补齐：

1. 新注册/免费账号实际 `daily_limit` 是多少，各接口是否有不同分钟规则？
2. “每日”按哪个时区、几点重置？
3. 是否存在未公开的并发连接、响应体、单文件或累计下载流量限制？
4. 项目账号是否开通 `authors` 集合的全部字段、引用关系字段和 Paper Schema Beta？
5. 生命科学语料的来源清单、去重策略、全文覆盖率和引用指标更新时间分别如何？
