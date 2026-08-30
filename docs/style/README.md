# 视觉风格素材库

这里保存供 Agent 生成或维护教程图片时复用的视觉输入，不保存文档正文消费的最终图片。

## 目录约定

- `references/`：构图、配色、图标语言或视觉风格参考图。每张图必须在下方索引中记录来源、角色和证据边界。
- `sources/`：可重复渲染的 HTML、React、CSS、canvas 等图稿源文件；依赖或渲染入口写入索引。
- `prompts/`：值得复用的生成式图片 prompt、参考图角色和人工修订记录，不包含密钥或机器地址。
- 文档采用的最终 PNG/WebP 放回对应 `docs/**/assets/`；GPT 原始母版和候选图保留在被 Git 忽略的 `output/imagegen/`。

## 使用规则

1. 生成前先从索引选择最少且相关的素材，并在 prompt 中逐张标明 `style/layout reference`、`edit target` 或其他角色。
2. 参考图只提供明确指定的视觉属性；其中的文字、数据和科学结论不能自动迁移，也不能作为项目证据。
3. 新增参考图时记录原始 URL、作者或用户提供状态、日期和版权状态；未知项明确写“待核验”。
4. 标签和机制准确性优先于风格相似度。生成式中文、数字和箭头必须人工核对，不可靠时用 HTML/CSS 确定性覆盖。

## 索引

| 文件 | 类型与角色 | 来源与状态 | 适用场景 |
|---|---|---|---|
| `references/vc2025-virtual-cell-challenge-reference.webp` | 科学信息图的 style/layout reference | 用户提供，原始 URL、作者与版权待核验；2026-08-22 归档 | 浅蓝论文图背景、A-D 分区、细胞/矩阵图标、深蓝/青/橙配色 |
| `sources/vc2025-lesson-figures.html` | HTML/CSS 教程图稿源 | 本仓库生成；无外部运行时资源 | 用 `?figure=crispri|unpaired|split|metrics|shift` 选择画面，以 Chromium 1600x900 截图 |
| `prompts/vc2025-learning-roadmap.md` | 参考图生成 prompt 与修订记录 | 本仓库生成 | 重建或调整 VC2025 学习路线总览图 |
| `sources/vc2026-data-contract-figures.html` | HTML/CSS 教程图稿源 | 本仓库生成；无外部运行时资源 | 用 `?figure=contexts|anndata` 选择画面，以 Chromium 1600x900 截图 |
| `prompts/vc2026-six-contexts.md` | GPT Image 概念插画 prompt 与科学边界 | 本仓库生成 | 重建或调整“同一目标在六个匿名背景中产生不同群体响应”的概念图 |
