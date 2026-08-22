# 科研检索栈基准与路由依据

> 测试日期：2026-08-22（Asia/Shanghai）
> 目的：为 Virtual Cell 2026 的交互式论文检索选择默认来源和回退路径；这是检索工具测试，不是论文结论评审。

## 基准设计

统一主题为 `zero-shot single-cell perturbation prediction unseen cell context`。对自然语言证据检索改写为语义等价的问题：哪些方法能在没有目标背景扰动训练数据时预测 CRISPRi 单细胞基因表达。每个入口最多取前 5 条，观察：

- 与单细胞扰动预测任务的直接相关性；
- 已知核心论文 STATE 的命中和排序；
- DOI、年份、摘要、全文定位与引用关系等字段；
- 正式版/预印本重复和明显跨领域误召回；
- 当前机器和凭证下的可用性。

这些判断只评价检索结果是否适合进入候选池，不把搜索摘要当成论文事实。

另以已知核心论文 *Predicting cellular responses to perturbation across diverse contexts with State* 验证精确查找：Infra Scholar 使用完整题名，SciVerse `meta-search` 使用 DOI `10.1101/2025.06.26.661135` 等值过滤。

## 实测结果

| 入口 | 当前结果 | 质量观察 | 路由结论 |
|---|---|---|---|
| Infra Scholar | 成功，约 1.5 s；API 返回 10 条，本地检查前 5 条 | STATE 排名第 1；前 5 条均处于单细胞扰动预测问题域，DOI、摘要和 PDF 标记较完整 | **日常默认发现** |
| SciVerse `meta-search` | 成功，约 0.8 s | 前 5 条中 4 条直接相关，但 PerturbNet 正式版和预印本各占一条；结构化字段和 `doc_id` 最完整 | **筛选、去重前候选构建** |
| SciVerse `agentic-search` | 成功，约 1.6 s，返回 5 个 evidence hit | 5 条均处于扰动预测或跨背景建模问题域，可继续用 offset 展开原文；适合回答机制和方法问题 | **证据检索与全文定位** |
| Paper Schema | 成功，约 0.3 s；主题共 95 条，检查前 5 条 | PertEval-scFM、Departures、Wasserstein-1 OT、零样本微调、CycSeq 均为直接相关的 ML 方法或 benchmark | **ML 方法精读，不作生命科学全库** |
| OpenAlex fallback | 成功，约 2.2 s | 前 5 条中约 2 条直接相关、1 条背景相关，另有多语言 Transformer 和通用深度学习综述误召回 | **多源 Skill 无 MCP 时的补充源** |
| OpenCLI arXiv | 成功，约 1.2 s | 前 5 条仅 C3TL 直接相关，其余多为单细胞背景或无关结果 | **只做 arXiv 窄查询** |
| OpenCLI PubMed | 两次均失败；直接访问 NCBI E-utilities 也发生 TLS 连接失败 | 当前网络路径不可用，未发现可归因于适配器字段漂移的证据 | **网络恢复后用于生物医学覆盖审计** |
| OpenCLI Semantic Scholar | 匿名请求 HTTP 429 | 当前无 Key 路径不稳定 | **配置 Key 后用于引文图，不作无条件默认** |

此前同机验收还确认 SciVerse 的 `content`、`resource` 和 `meta-paper-relations` 可用；详细记录见 [SciVerse 可用服务与免费额度调查](sciverse-services-free-tier.md)。

精确查找中，Infra Scholar 把 STATE 原题名排在第 1；SciVerse DOI 硬过滤返回唯一匹配及稳定的 `unique_id`。因此已知题名适合先走默认 Scholar，已知 DOI 或需要机器可复现的唯一匹配时优先使用 SciVerse 结构化过滤，最终仍以 DOI 落地页或原文为准。

## 最佳流程

```text
INDEX 查重与缺口
  -> 一个高信号英文查询
  -> Infra Scholar 前 10 条建立候选池
  -> DOI + 题名/第一作者 + 版本关系去重
  -> 按问题补路由：
       证据/全文/图表       -> SciVerse semantic + content/resource
       年份/作者/OA/引用筛选 -> SciVerse meta-search + relations
       ML 方法/benchmark    -> Paper Schema
       系统综述/引用审计     -> nature-academic-search 的 T1->T2 多源流程
  -> DOI/出版页/预印本/官方代码核验
  -> INDEX 记录采用、备选、排除与检索台账
```

Infra Scholar 与 SciVerse 不是互相替代：前者在本次生命科学主题发现中排序最好，后者在证据定位、全文、结构过滤和方法拆解上提供了不同能力。固定串行调用所有来源会增加重复、配额和审计成本，因此只根据当前缺口展开对应分支。

## 本次调用台账

- Infra Scholar：主题查询和 STATE 完整题名查询各 1 次，共 2 次，均成功。
- SciVerse `meta-search`：主题查询和 STATE DOI 等值过滤各 1 次，共 2 次，均成功。
- SciVerse `agentic-search`：语义等价自然语言问题，2 次；第一次成功但本地摘要器使用了错误字段，第二次按 `hits` 正确复核。两次 API 均成功。
- Paper Schema：`single-cell perturbation prediction`，1 次，成功。
- OpenAlex：统一主题，1 次，成功。
- OpenCLI arXiv：统一主题，1 次，成功。
- OpenCLI PubMed：`single-cell perturbation prediction unseen context`，2 次，均为网络失败；达到本题站点调用上限。
- OpenCLI Semantic Scholar：统一主题，1 次，HTTP 429；按限流硬停止，未重试。
