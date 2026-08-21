# Infra Agent / Cloudsway 科研搜索使用指南

> 整理日期：2026-08-21  
> 适用入口：<https://docs.infra-agent.ai/zh/Smart_Search/Reader/overview/>  
> 说明：当前官方文档使用 **Cloudsway** 品牌名，`docs.infra-agent.ai` 页面也将 canonical URL 指向 `cloudsway.com`。本文只引用官方文档和第一方页面，不包含任何真实 API Key。

> **使用原则：OpenCLI/浏览器只用于首次阅读文档、登录控制台和创建凭证。初始化完成后，搜索程序直接读取本机私有配置并调用 HTTP API，不依赖浏览器登录态。**

## 1. 先分清三种能力

官方文档中存在三个相近但用途不同的产品：

| 产品 | 解决的问题 | 典型输入 | 典型输出 | 计费口径 |
| --- | --- | --- | --- | --- |
| **Cloudsway Smart Search** | 根据查询词搜索网络 | 查询词 `q` | 标题、URL、摘要、相关性分数；可选正文长摘要 | 官方页面写明“计费详情请咨询商务” |
| **Cloudsway Reader** | 读取一个已经知道的 URL | `url` | TEXT、MARKDOWN 或 HTML，另含元数据和链接 | 海外版 1 美元 / 1000 Credit；基础读取 1 Credit / URL |
| **AI Research** | 联网搜索后由 DeepSeek 模型直接综合回答 | 对话消息 | OpenAI 风格回答、推理内容、token 用量和 `reference` 来源 | DeepSeek R1/V3 Search 均为 0.016 美元 / 次 |

来源：[Smart Search 概述](https://docs.infra-agent.ai/zh/Smart_Search/Cloudsway_Smart_Search/overview/)、[Reader 概述](https://docs.infra-agent.ai/zh/Smart_Search/Reader/overview/)、[AI Research 概述](https://docs.infra-agent.ai/zh/AIResearch/overview/)、[AI Research 定价](https://docs.infra-agent.ai/zh/AIResearch/pricing/)

因此，一次可控、可追溯的科研检索通常采用：

```text
研究问题 -> Smart Search 找候选来源 -> 筛选第一方/论文页面
         -> Reader 读取选中的 URL/PDF -> 本地整理、核对并引用
```

若目标是快速得到带来源的综合答案，可改用 AI Research；若目标是建立可复核的资料集，优先使用 Smart Search + Reader，将“发现来源”和“读取正文”分开。

## 2. 账户、Workspace、余额和资源

### 2.1 登录不等于接口已经可用

官方 Quickstart 的流程是：登录控制台获取凭证、创建或购买产品资源、取得该资源的 `Endpoint`，最后调用 API。也就是说，即使账号已有余额，仍需要确认当前 Workspace 中已经存在 **Search** 或 **Reader** 资源及其 Endpoint。[Smart Search Quickstart](https://docs.infra-agent.ai/zh/Smart_Search/Cloudsway_Smart_Search/quickstart/)、[Reader Quickstart](https://docs.infra-agent.ai/zh/Smart_Search/Reader/quickstart/)

控制台中的资源在创建时归属于某个 Workspace；不同 Workspace 的资源、权限和账单相互隔离。系统有一个默认 Workspace，主账号可访问全部 Workspace，子账号需要授权。[Workspace 官方说明](https://docs.infra-agent.ai/zh/customer-care/workspace/)

### 2.2 当前账号实测结果

2026-08-21 在已登录控制台中确认：

| 项目 | 实测结果 |
| --- | --- |
| Workspace | 只有一个默认 Workspace |
| Search 资源 | 已有一个“智能搜索-学术搜索-国内版”资源，状态为启用 |
| 接口类型 | 专用学术检索 `/search/{Endpoint}/scholar`，不是公开文档中的通用 `/smart` |
| 资源限速 | QPS 3 |
| 鉴权 | 已配置一组账户 AK；调用时使用 `Authorization: Bearer ...` |
| IP 白名单 | 当前为空；后续固定部署时建议限制到可信出口 IP |
| 控制台币种 | 页面当前选择人民币 |
| 约 10 美元额度 | 未在首页、客户信息、费用监控或账单页找到可验证的余额字段 |
| 本次检索后账单 | AI Search 用量、费用均为 `0.000`，明细为 0 条；可能尚未入账、由试用额度抵扣或存在账单延迟 |

目前只能确认学术搜索资源可用，不能确认“约 10 美元”是现金余额、赠送额度还是产品试用额度，也不能据此计算剩余调用次数。Search 公开文档没有给出单价；Reader 的价格不能用于推算学术搜索费用。

### 2.3 两类凭证

官方文档区分以下两类凭证：[Workspace API Key 官方说明](https://docs.infra-agent.ai/zh/customer-care/apikey/)

| 凭证 | 归属 | 权限范围 | 数量与分账 |
| --- | --- | --- | --- |
| 子账号 Access Key（AK） | 某个账号 | 跟随该账号获授权的 Workspace，可跨多个 Workspace | 每个账号一组；账单可归集到子账号 |
| Workspace API Key | 单个 Workspace | 自动拥有该 Workspace 内资源权限，不能跨 Workspace | 一个 Workspace 可创建多组；可按项目或 Key 分账 |

Smart Search 和 Reader 的 API Reference 均以 `Authorization: Bearer {AK}` 为例，并要求使用资源对应的 `BasePath` 与 `Endpoint`。实际使用哪一种凭证，应以控制台中该资源展示的接入信息为准。[Smart Search API](https://docs.infra-agent.ai/zh/Smart_Search/Cloudsway_Smart_Search/api/)、[Reader API](https://docs.infra-agent.ai/zh/Smart_Search/Reader/api/)

安全要求：

- 不要把真实 AK/API Key 写入本仓库、Markdown、Notebook、命令历史或日志；
- 示例从环境变量或仓库外的本机私有配置读取；
- 为开发、实验和生产环境分别创建 Workspace API Key，并按需设置 IP 白名单和 QPS；
- 泄露后立即吊销或重置，并检查账单与调用记录；
- Workspace API Key 是团队共享凭证，所有有查看权限的成员都可能使用它。

## 3. 一次性控制台初始化与本机配置

公开 Quickstart 只记录了控制台的资源开通流程：登录、进入产品资源页、点击创建、从列表取得 Endpoint，然后调用 API；官方文档没有描述一个可直接输入科研问题并展示搜索结果的网页搜索框。[Smart Search Quickstart](https://docs.infra-agent.ai/zh/Smart_Search/Cloudsway_Smart_Search/quickstart/)、[Reader Quickstart](https://docs.infra-agent.ai/zh/Smart_Search/Reader/quickstart/)

因此，控制台或 OpenCLI 驱动的已登录浏览器只承担以下一次性工作：

1. 右上角或工作区切换器显示的是目标 Workspace；
2. Search / Reader 资源列表中存在状态正常的资源；
3. 创建或轮换 AK/API Key，并取得资源的完整 Endpoint；
4. 将凭证写入仓库外的本机私有配置；
5. 退出浏览器会话，后续检索全部通过 HTTP API 完成。

本机已经完成初始化，配置文件位于：

```text
/home/caii/.config/infra-agent/credentials.json
```

权限为 `600`，文件结构如下；示例中的占位符不是实际值：

```json
{
  "scholar_url": "https://<BasePath>/search/<Endpoint>/scholar",
  "ak": "<Access Key>"
}
```

该文件位于 Git 仓库之外。不要将它复制进项目目录，也不要在终端打印其内容。轮换 AK 或 Endpoint 后只更新这个文件，调用代码无需重新操作浏览器。若以后需要多人或服务器使用，应改为项目独立的 Workspace API Key 或密钥管理服务，而不是分发账户 AK。

注意：两个中文 Quickstart 页面中的产品名疑似互换。Smart Search 路径下的页面正文写“Reader API”，Reader 路径下的页面正文写“Search API”；但其最终示例路径分别是 `/smart` 和 `/read`。实际接入时应以对应 API Reference 的请求路径为准。

## 4. 当前账户的学术搜索 `/scholar`

当前账户实际开通的是国内学术搜索专用端点。它与公开文档中的通用 Smart Search 相似，但路径、字段命名和结果结构不同，代码中必须分别处理。

### 4.1 已验证接口

```text
GET https://{BasePath}/search/{Endpoint}/scholar?q={query}
Authorization: Bearer {AK}
```

实测确认：

- 不带 Bearer 凭证返回 HTTP `401`；
- 带有效凭证但缺少 `q` 返回 HTTP `400`，错误码 `1103`；
- `q` 是已验证的必填查询参数；
- 只传 `q` 时默认返回 10 条结果；
- 当前资源 QPS 为 3。

2026-08-21 已从上述本机配置直接发起一次不带 `q` 的鉴权探针，结果为 HTTP `400`、业务码 `1103`。这证明日常调用不需要浏览器会话；该探针没有执行学术搜索。

控制台没有为 `/scholar` 提供公开 API Reference 或代码示例。除 `q` 外，不要直接假设它支持通用 `/smart` 的 `count`、`freshness`、`enableContent` 等参数；如需分页或过滤，应先向官方确认或用单次低成本请求验证。

### 4.2 cURL

```bash
INFRA_CONFIG='/home/caii/.config/infra-agent/credentials.json'
infra_scholar_url=$(node -p "require('${INFRA_CONFIG}').scholar_url")
infra_scholar_ak=$(node -p "require('${INFRA_CONFIG}').ak")

curl --silent --show-error --fail-with-body --get \
  "${infra_scholar_url}" \
  --header "Authorization: Bearer ${infra_scholar_ak}" \
  --data-urlencode 'q=single-cell perturbation prediction virtual cell'
```

这些 shell 变量只存在于当前进程，不会把凭证写进命令历史。不要启用 `set -x`，也不要打印变量。完整 Endpoint 中包含账户资源标识，也应按敏感配置管理。

### 4.3 Python（Requests）

```python
import json
from pathlib import Path

import requests

config_path = Path.home() / ".config" / "infra-agent" / "credentials.json"
config = json.loads(config_path.read_text())

response = requests.get(
    config["scholar_url"],
    headers={"Authorization": f"Bearer {config['ak']}"},
    params={"q": "single-cell perturbation prediction virtual cell"},
    timeout=30,
)
response.raise_for_status()

data = response.json()
results = data.get("web_pages", {}).get("value", [])
for item in results:
    extra = item.get("extra_data", {})
    print(item.get("name"), extra.get("doi"), item.get("url"))
```

### 4.4 返回结构

`/scholar` 使用 snake_case 字段：

- `requestId`：本次请求标识；
- `query_context.original_query`：原始查询词；
- `web_pages.value`：结果数组；
- `name`、`url`、`date_published`、`snippet`、`abstract`：论文基本信息和摘要；
- `extra_data.authors`、`cite_by`、`doi`、`journal_title`、`volume`、`issue`、`first_page`、`last_page`、`pdf`：扩展学术元数据。

字段可能为空。例如本次第 5 条结果的 `abstract` 为空，因此下游代码必须使用 `.get()` 并允许缺失值。`cite_by` 是检索服务返回的引用数快照，不应视为实时、唯一或权威的引用统计。

### 4.5 本次真实查询

查询词：`single-cell perturbation prediction virtual cell`

| 项目 | 结果 |
| --- | --- |
| 时间 | 2026-08-21 |
| HTTP 状态 | `200` |
| 服务端往返耗时 | 约 1.6 秒 |
| 返回数量 | 10 条 |
| 正文/PDF/OCR | 未额外调用 |
| 账单即时变化 | 未观察到，AI Search 仍为 `0.000`、0 条明细 |

前几条结果直接命中 [State](https://www.biorxiv.org/content/10.1101/2025.06.26.661135v1)、[单细胞扰动预测模型系统比较](https://doi.org/10.1101/2024.12.23.630036)、[Virtual cells: Predict, explain, discover](https://arxiv.org/abs/2505.14613) 和 [VCWorld](https://proceedings.iclr.cc/paper_files/paper/2026/hash/767ff070c27c8954babe74eccf3fbe91-Abstract-Conference.html)。对于“虚拟细胞 + 扰动预测”主题，相关性适合第一轮候选论文筛选；但结果同时混入较早的虚拟敲除工具，仍需人工判断任务、数据模态和发布日期是否匹配。

### 4.6 `docs/references` 两篇文献的 API 测试

以下两次测试均由本机凭证直接调用 `/scholar` HTTP API，OpenCLI 没有参与搜索：

| 本地文献 | 查询结果 | 原文可得性 |
| --- | --- | --- |
| `Lingshu-Cell：面向虚拟细胞的转录组建模生成式细胞世界模型.md` | HTTP `200`，约 2.0 秒，API 返回 10 条；本次保留并检查的前 5 条均不是 Lingshu-Cell | 本次不能确认原文。由于未保留后 5 条，不能把结果表述为“全部 10 条均未命中” |
| `UniPert-G2CP：从分子表征到表型建模，打通遗传筛选与化学筛选.md` | HTTP `200`，约 1.3 秒；第 1 条命中 Cell 正式出版页，第 2 条命中 bioRxiv 预印本 | [Cell 正式原文](https://www.cell.com/cell/fulltext/S0092-8674(26)00654-9)；[bioRxiv 预印本](https://doi.org/10.1101/2025.02.02.635055) |

链接直连验证中，bioRxiv 最终解析到 `v2` 页面并返回 HTTP `200`。Cell 正式页返回 HTTP `403`，这是出版站对非浏览器客户端的访问限制，不表示链接或论文不存在。实际阅读全文时可在浏览器打开正式页，或使用 bioRxiv 版本。

这组结果说明学术 API 可以通过标题和方法关键词找到已经正式发表或发布预印本的论文，但对非常新、尚未被索引或题名不稳定的材料可能漏检。检索结果不是“原文已下载”的同义词，仍需检查出版页或 DOI 的可访问性。

## 5. 通用 Smart Search：先找到候选网页来源

### 5.1 接口

```text
GET https://{BasePath}/search/{Endpoint}/smart
Authorization: Bearer {AK}
```

`BasePath`、`Endpoint` 和凭证都从控制台取得。查询参数放在 URL query 中，没有 JSON 请求体。[Smart Search API](https://docs.infra-agent.ai/zh/Smart_Search/Cloudsway_Smart_Search/api/)

### 5.2 请求参数

| 参数 | 必填 | 类型 | 作用 |
| --- | --- | --- | --- |
| `q` | 是 | String | 搜索查询词，不能为空 |
| `count` | 否 | Short | 返回 10/20/30/40/50 条，默认 10，最大 50 |
| `freshness` | 否 | String | `Day`、`Week` 或 `Month` |
| `offset` | 否 | Short | 分页偏移，从 0 开始 |
| `enableContent` | 否 | Bool | 是否读取并返回长摘要，默认 `false` |
| `contentType` | 否 | String | 长摘要格式：`HTML`、`MARKDOWN`、`TEXT`；仅在 `enableContent=true` 时生效 |
| `contentTimeout` | 否 | Float | 长摘要读取超时秒数，默认 3 秒 |
| `mainText` | 否 | Bool | 是否返回智能关键片段；官方文档要求与 `enableContent=true` 配合 |

重复查询默认会缓存 10 分钟。设置请求头 `Pragma: no-cache` 会要求每次独立返回。公开文档没有说明缓存请求是否免计费，因此不要把缓存等同于免费。[Smart Search API](https://docs.infra-agent.ai/zh/Smart_Search/Cloudsway_Smart_Search/api/)

### 5.3 CLI（cURL）最小调用

官方没有列出独立的 Cloudsway CLI；命令行接入方式是 cURL。[Smart Search API](https://docs.infra-agent.ai/zh/Smart_Search/Cloudsway_Smart_Search/api/)

```bash
export INFRA_SEARCH_BASE_PATH='控制台显示的主机名，不含 https://'
export INFRA_SEARCH_ENDPOINT='控制台显示的 Search Endpoint'
read -rsp 'Search AK: ' INFRA_SEARCH_AK && export INFRA_SEARCH_AK
echo

curl --silent --show-error --fail-with-body --get \
  "https://${INFRA_SEARCH_BASE_PATH}/search/${INFRA_SEARCH_ENDPOINT}/smart" \
  --header "Authorization: Bearer ${INFRA_SEARCH_AK}" \
  --data-urlencode 'q=CRISPRi Perturb-seq zero-shot perturbation prediction' \
  --data-urlencode 'count=10'
```

第一次测试不要加 `Pragma: no-cache`，也先不要开启 `enableContent`。若需要限定近期论文或新闻，可加 `freshness=Month`；不要对经典论文使用该参数，否则可能过滤掉关键来源。

### 5.4 Python（Requests）

官方提供的是普通 HTTP `requests` 示例，而不是专属 Python SDK。[Smart Search API](https://docs.infra-agent.ai/zh/Smart_Search/Cloudsway_Smart_Search/api/)

```python
import os
import requests

base_path = os.environ["INFRA_SEARCH_BASE_PATH"]
endpoint = os.environ["INFRA_SEARCH_ENDPOINT"]
ak = os.environ["INFRA_SEARCH_AK"]

response = requests.get(
    f"https://{base_path}/search/{endpoint}/smart",
    headers={"Authorization": f"Bearer {ak}"},
    params={
        "q": "CRISPRi Perturb-seq zero-shot perturbation prediction",
        "count": 10,
        "enableContent": False,
    },
    timeout=30,
)
response.raise_for_status()
results = response.json().get("webPages", {}).get("value", [])

for item in results:
    print(item.get("score"), item.get("name"), item.get("url"))
```

### 5.5 返回结构

响应的原始查询位于 `queryContext.originalQuery`，结果数组位于 `webPages.value`。[Smart Search API](https://docs.infra-agent.ai/zh/Smart_Search/Cloudsway_Smart_Search/api/)

每个结果可能包含：

- `name`：页面标题；
- `url`：页面 URL；
- `datePublished`：发布时间，部分站点才有；
- `snippet`：短摘要；
- `mainText`：智能关键片段；
- `siteName`：站点名，部分结果才有；
- `contentCrawled`：长摘要是否读取成功；
- `content`：页面长摘要；
- `logo`、`imageList`：图标和图片列表，可能缺失；
- `score`：内容相关性分数。

调用方必须容忍可选字段缺失，并检查 `contentCrawled`，不要因某条结果缺少 `datePublished` 或 `siteName` 而让整个任务失败。

## 6. Reader：读取论文页、文档和 PDF

### 6.1 接口

```text
POST https://{BasePath}/search/{Endpoint}/read
Authorization: Bearer {AK}
Content-Type: application/json
```

来源：[Reader API](https://docs.infra-agent.ai/zh/Smart_Search/Reader/api/)

### 6.2 请求参数

| 参数 | 必填 | 类型 | 作用 |
| --- | --- | --- | --- |
| `url` | 是 | String | 要读取的目标 URL |
| `formats` | 否 | List | `HTML`、`TEXT`、`MARKDOWN`；默认 TEXT，官方文档要求传入时选择其中一种 |
| `mode` | 否 | String | `fast` 静态读取（默认）、`quality` 动态渲染、`auto` 自动选择 |
| `totalTimeout` | 否 | Int | 端到端总超时，单位毫秒；默认关闭 |
| `timeout` | 否 | Int | API connect 读取超时，单位毫秒，默认 30000 |
| `imageDownloadEnable` | 否 | Bool | 将图片转为 Base64；默认 `false`，会产生额外图片费用 |
| `imageInContent` | 否 | Bool | Base64 图片是否放进正文；默认 `true`，设为 `false` 时返回 `image_base64_list` |
| `pdfExtractEnable` | 否 | Bool | PDF 是否提取文本；默认 `false`，开启会产生额外费用 |
| `enhancedOcr` | 否 | Bool | 仅在 PDF 提取开启时生效的增强 OCR；默认 `false`，会产生额外费用 |

### 6.3 CLI（cURL）最小调用

```bash
export INFRA_READER_BASE_PATH='控制台显示的主机名，不含 https://'
export INFRA_READER_ENDPOINT='控制台显示的 Reader Endpoint'
read -rsp 'Reader AK: ' INFRA_READER_AK && export INFRA_READER_AK
echo

curl --silent --show-error --fail-with-body \
  --request POST \
  "https://${INFRA_READER_BASE_PATH}/search/${INFRA_READER_ENDPOINT}/read" \
  --header "Authorization: Bearer ${INFRA_READER_AK}" \
  --header 'Content-Type: application/json' \
  --data '{
    "url": "https://example.org/research-page",
    "formats": ["MARKDOWN"],
    "mode": "auto",
    "totalTimeout": 45000
  }'
```

不要在第一次调用中开启图片 Base64、PDF 提取或 OCR。先确认普通 HTML 页面可以读取，再根据目标格式逐项开启增值能力。

### 6.4 Python（Requests）

```python
import os
import requests

base_path = os.environ["INFRA_READER_BASE_PATH"]
endpoint = os.environ["INFRA_READER_ENDPOINT"]
ak = os.environ["INFRA_READER_AK"]

response = requests.post(
    f"https://{base_path}/search/{endpoint}/read",
    headers={"Authorization": f"Bearer {ak}"},
    json={
        "url": "https://example.org/research-page",
        "formats": ["MARKDOWN"],
        "mode": "auto",
        "totalTimeout": 45000,
    },
    timeout=60,
)
response.raise_for_status()
data = response.json()
print(data.get("markdown", data.get("text", "")))
```

### 6.5 返回结构

根据 `formats`，正文位于 `html`、`markdown` 或 `text`。响应还可能包含以下字段：[Reader API](https://docs.infra-agent.ai/zh/Smart_Search/Reader/api/)

- `metadata.title`、`metadata.description`、`metadata.keywords`；
- `logo`、`site_name`、`image_list`；
- `image_base64_list`；
- `pdf_pages`；
- `internal_links` 与 `external_links`。

当目标是 PDF 且 `pdfExtractEnable=false` 时，官方文档说明默认返回 Base64；开启 `pdfExtractEnable=true` 才返回解析文本，并按页产生额外费用。

## 7. AI Research：需要“搜索 + 生成答案”时使用

AI Research 提供 `Deepseek_R1_Search` 和 `Deepseek_V3_Search`，采用 OpenAI 风格的 `/chat/completions` 接口。非流式响应除标准字段外，还包含 `reference` 数组；每条来源包含 `name`、`url` 和 `snippet`。流式响应的 `reference` 位于第一个 chunk。[AI Research API](https://docs.infra-agent.ai/zh/AIResearch/api-reference/deepseek_search/)

```text
POST {basePath}/{endpointPath}/chat/completions
Authorization: Bearer {AccessKey}
Content-Type: application/json
```

主要请求字段为：

- `model`：`Deepseek_R1_Search` 或 `Deepseek_V3_Search`；
- `messages`：OpenAI 风格消息数组；
- `stream`：是否流式；
- `max_tokens`：最大生成 token 数。

AI Research 公开定价为 0.016 美元 / 次。官方 Quickstart 还写明该资源目前不能在控制台自助创建，需要联系销售在后台开通，因此即使账户有余额也不代表该 Endpoint 已存在。[AI Research Quickstart](https://docs.infra-agent.ai/zh/AIResearch/quickstart/)、[AI Research 定价](https://docs.infra-agent.ai/zh/AIResearch/pricing/)

对于科研任务，模型生成的答案只能作为线索和摘要。最终引用应打开 `reference.url`，核对作者、题名、版本、日期、方法和结论是否与原文一致。

## 8. 推荐的科研检索工作流

### 第一步：把研究问题改写成可检索查询

查询词应包含对象、任务、方法或时间约束，例如：

```text
CRISPRi Perturb-seq zero-shot perturbation prediction benchmark single-cell RNA-seq
```

第一轮只取 10 条结果，不打开长摘要。检查结果是否偏题后，再调整术语或分页；不要一开始就取 50 条并读取全部正文。

### 第二步：筛选可引用来源

依次优先保留论文出版页、预印本原文、数据仓库、项目官方文档和源代码仓库。`score` 只表示相关性，不代表来源权威性或结论正确性；`snippet` 也不能代替原文。

建议保存以下最小审计字段：

```json
{
  "query": "原始查询词",
  "retrieved_at": "ISO 8601 时间",
  "name": "结果标题",
  "url": "原始 URL",
  "date_published": "API 返回值或 null",
  "score": 0.0,
  "source_type": "publisher|preprint|repository|official-docs"
}
```

### 第三步：只读取入选 URL

普通 HTML 先用 Reader 的 `auto` 或默认 `fast`，输出 `MARKDOWN`。若内容明显缺失，再改为 `quality`。对 PDF 先确认页数、文件来源和是否真的需要全文，再开启 `pdfExtractEnable`；普通提取失败后才考虑 `enhancedOcr`。

### 第四步：交叉核对

关键事实至少回到一手来源核对。对于论文，应区分预印本与正式出版版本；对于数据集，应核对版本号、许可证和发布日期；对于数字结果，应核对表格、图注和补充材料，而不是只引用搜索摘要。

### 第五步：记录用量

调用前后查看日账单。官方账单支持日/月维度，详细账单的重要字段包括 `itemOperation`（计费项）、`usageAmount`（用量）、`unblendedCost`（原始费用）、`pricingUnit`、`currencyCode`、`loginName`、`ak` 和 `workspaceName`。[账单管理官方说明](https://docs.infra-agent.ai/zh/customer-care/billing/)

## 9. 成本控制

### 9.1 已公开的价格

Reader 海外版价格为 1 美元 / 1000 Credit，基础调用为 1 Credit / URL。增值项为：PDF 文本提取 1 Credit / 页、图片转换 2 Credit / 张并加 1 Credit 基础调用、增强 OCR 6 Credit / 页。[Reader 概述及计费](https://docs.infra-agent.ai/zh/Smart_Search/Reader/overview/)

Smart Search 的公开概述页没有给出单价，只要求咨询商务；AI Research 的两个 DeepSeek Search 型号均为 0.016 美元 / 次。[Smart Search 概述](https://docs.infra-agent.ai/zh/Smart_Search/Cloudsway_Smart_Search/overview/)、[AI Research 定价](https://docs.infra-agent.ai/zh/AIResearch/pricing/)

### 9.2 实用策略

- 搜索阶段保持 `count=10`、`enableContent=false`，先看标题、URL、摘要和分数；
- 只对入选的少量 URL 调 Reader；
- Reader 默认关闭图片 Base64、PDF 提取和增强 OCR；
- PDF 先使用普通提取，确有识别问题再开增强 OCR；
- 测试请求使用单一、公开、短小的 HTML 页面；
- 为 Search Key 设置合理 QPS，防止循环或并发程序失控；
- 按实验创建独立 Workspace API Key，任务结束后吊销；
- 设置客户端超时、最大重试次数和总调用预算；不要对 400/401/403/404 持续重试；
- 通过账单而不是估算确认实际扣费。折扣、赠送额度、缓存和套餐规则可能改变最终费用。

不要直接把“约 10 美元余额”换算成可调用次数。只有确认余额适用产品、实际单价、折扣和增值项后，换算才有意义。

## 10. 错误排查

### 10.1 Smart Search 已明确的状态

Smart Search API Reference 明确列出：`200` 表示成功，`429` 表示 QPS 超限，需要联系工作人员提升额度。[Smart Search API](https://docs.infra-agent.ai/zh/Smart_Search/Cloudsway_Smart_Search/api/)

遇到问题时按以下顺序检查：

1. BasePath 是否只填主机名、请求 URL 是否包含正确的 `/search/{Endpoint}/smart` 或 `/read`；
2. Endpoint 是否属于当前 Workspace 和正确产品；
3. `Authorization` 是否为 `Bearer <凭证>`，不要带引号或多余空格；
4. Search 的 `q` 是否非空，`count` 是否为允许的枚举值；
5. Reader 的 `Content-Type` 是否为 `application/json`，`formats` 和 `mode` 是否使用官方枚举；
6. IP 白名单是否包含当前出口 IP；
7. 是否达到 Key 的 QPS、资源 QPS、余额或套餐限制；
8. 动态页面读取不全时将 Reader 从 `fast` 改为 `auto` 或 `quality`，并适当增加超时；
9. PDF 返回 Base64 而不是正文时，检查 `pdfExtractEnable`；
10. 保存 HTTP 状态、响应体、时间和脱敏后的 Endpoint，供技术支持定位；绝不在工单或仓库中粘贴完整密钥。

### 10.2 AI Research / MaaS 公共错误码

官方 MaaS 错误码文档列出：`400` 请求格式错误、`401` 凭证无效或缺失、`403` IP 不在白名单、`404` 资源或模型不存在/不匹配、`429` 超过请求速率、`500` 服务端错误、`503` 服务不可用、`504` 网关超时。该表适用于 MaaS/AI Research，不应未经实测直接当作 Search/Reader 的完整错误契约。[MaaS 公共错误码](https://docs.infra-agent.ai/zh/maasapi/api-reference/errorcode/)

MaaS 官方还建议每次请求携带全局唯一的 `X-Request-id`，发生异常时把该 ID 提供给技术支持，以便定位后端日志；不要在不同请求间复用。[请求链路追踪](https://docs.infra-agent.ai/zh/maasapi/api-reference/questions/X-Request-id/)

## 11. 本次验收状态与后续事项

- [x] 确认默认 Workspace 中存在已启用的国内学术搜索 Endpoint；
- [x] 确认路径为 `/scholar`、QPS 为 3、Bearer 鉴权有效；
- [x] 配置账户 AK，且未把凭证明文写入仓库；
- [x] 将 AK 和完整 Endpoint 保存到仓库外的本机配置，权限为 `600`；
- [x] 不带查询词，通过纯 HTTP 鉴权探针验证配置（HTTP `400`、业务码 `1103`）；
- [x] 使用纯 HTTP API 测试 `docs/references` 中两篇文献；
- [x] 发起一次公开科研查询，记录 HTTP 状态、耗时、字段和结果质量；
- [x] 查询 AI Search 日账单；当前仍为 `0.000`、0 条明细；
- [ ] 向官方确认国内学术搜索单价、账单入账延迟和约 10 美元额度的性质；
- [ ] 固定部署位置后配置 IP 白名单；
- [ ] 优先创建项目独立的 Workspace API Key，减少账户 AK 的权限范围；
- [ ] 如需 Reader 或 AI Research，再确认对应资源是否已经开通并做独立低成本验收；
- [ ] 后续再次查看日账单，确认本次请求最终是否出现计费明细。

## 12. 官方资料索引

- [Cloudsway Smart Search 概述](https://docs.infra-agent.ai/zh/Smart_Search/Cloudsway_Smart_Search/overview/)
- [Cloudsway Smart Search Quickstart](https://docs.infra-agent.ai/zh/Smart_Search/Cloudsway_Smart_Search/quickstart/)
- [Cloudsway Smart Search API Reference](https://docs.infra-agent.ai/zh/Smart_Search/Cloudsway_Smart_Search/api/)
- [Cloudsway Reader 概述与计费](https://docs.infra-agent.ai/zh/Smart_Search/Reader/overview/)
- [Cloudsway Reader Quickstart](https://docs.infra-agent.ai/zh/Smart_Search/Reader/quickstart/)
- [Cloudsway Reader API Reference](https://docs.infra-agent.ai/zh/Smart_Search/Reader/api/)
- [AI Research 概述](https://docs.infra-agent.ai/zh/AIResearch/overview/)
- [AI Research Quickstart](https://docs.infra-agent.ai/zh/AIResearch/quickstart/)
- [AI Research 定价](https://docs.infra-agent.ai/zh/AIResearch/pricing/)
- [AI Research API Reference](https://docs.infra-agent.ai/zh/AIResearch/api-reference/deepseek_search/)
- [Workspace API Key](https://docs.infra-agent.ai/zh/customer-care/apikey/)
- [Workspace 管理](https://docs.infra-agent.ai/zh/customer-care/workspace/)
- [账单管理](https://docs.infra-agent.ai/zh/customer-care/billing/)
- [账单拆分方案](https://docs.infra-agent.ai/zh/customer-care/bill_splitting/)
- [Access Key 与账号管理](https://docs.infra-agent.ai/zh/customer-care/access-key/)
- [MaaS 公共错误码](https://docs.infra-agent.ai/zh/maasapi/api-reference/errorcode/)
- [请求链路追踪](https://docs.infra-agent.ai/zh/maasapi/api-reference/questions/X-Request-id/)

## 13. 本次资料与搜索记录

- 网站：`docs.infra-agent.ai`；查询词：`学术搜索 scholar API`；次数：1。结果过宽，未找到 `/scholar` 专用公开文档。
- OpenCLI 站点：`web`；页面：Reader 概述、Smart Search API；次数：2，均为只读。
- 网站：当前账户的 Infra Agent 学术搜索；查询词：`single-cell perturbation prediction virtual cell`；次数：1，成功。
- 网站：当前账户的 Infra Agent `/scholar` API；查询词分别为 Lingshu-Cell 和 UniPert-G2CP 题名/关键词；各 1 次，均为直接 HTTP 调用。
- 鉴权探针：当前账户的 Infra Agent `/scholar` API；不带 `q`，返回 HTTP `400`、业务码 `1103`，未执行搜索。
- 其余资料：直接读取 Infra Agent / Cloudsway 官方文档、控制台和第一方前端代码；未使用第三方教程。
- 已跳过：继续调用 `opencli web`，原因是同一非 AI 站点已达到本次问题的 2 次调用上限。
