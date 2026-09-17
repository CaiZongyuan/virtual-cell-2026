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

## 工具约定（2026-09-17）

教程配图按**图的性质**选工具，不要交叉使用：

| 图的类型 | 工具 | 交付形态 |
|---|---|---|
| **科研数据图**（散点、热图、误差棒、多面板结果图） | `.agents/skills/nature-figure` | Python(matplotlib/seaborn) 或 R(ggplot2) 源图脚本 + 导出 PDF/SVG，再转 WebP 入教程 |
| **架构图 / 流程图 / 数据流 / 时序图 / 状态机** | `.agents/skills/archify` | JSON 规格（入库）+ 交付型独立 HTML（可再生产物，放被忽略的 `output/figures/`）+ 截图转 WebP 入教程 |
| **概念插画 / 封面 / 风格化示意图** | 子代理经浏览器用 ChatGPT 生成，prompt 取自 `prompts/gallery-research-paper-figures.md` | 母版留 `output/imagegen/`（Git 忽略），采用版转 WebP 入教程 |
| **标签密集、要求数值或机制准确的流程图** | HTML/CSS/canvas 手绘 | 图稿源入 `sources/`，Chromium 截图后转 WebP |

硬性边界：

1. **架构图必须 light 模式、简体中文界面**（archify 的 `meta.locale: "zh-CN"`；截图时 URL 加 `?theme=light`）。
2. **生成式图片只是解释性插画**，不能作为实验结构、机制或数据证据。
3. archify 的交付 HTML 约 800 KB 且可确定性重建，**不入库**；入库的是 JSON 规格与最终 WebP。重建命令：
   `node .agents/skills/archify/bin/archify.mjs deliver architecture <spec.json> output/figures/<name>.html --quality showcase`
4. archify 交付需要 Chrome。其环境变量探测在本机沙箱内不生效，改用 `--headless=new --screenshot` 直接截图；截图后裁掉浏览器外壳再转 WebP。

## 索引

| 文件 | 类型与角色 | 来源与状态 | 适用场景 |
|---|---|---|---|
| `references/vc2025-virtual-cell-challenge-reference.webp` | 科学信息图的 style/layout reference | 用户提供，原始 URL、作者与版权待核验；2026-08-22 归档 | 浅蓝论文图背景、A-D 分区、细胞/矩阵图标、深蓝/青/橙配色 |
| `sources/vc2025-lesson-figures.html` | HTML/CSS 教程图稿源 | 本仓库生成；无外部运行时资源 | 用 `?figure=crispri|unpaired|split|metrics|shift` 选择画面，以 Chromium 1600x900 截图 |
| `prompts/vc2025-learning-roadmap.md` | 参考图生成 prompt 与修订记录 | 本仓库生成 | 重建或调整 VC2025 学习路线总览图 |
| `sources/vc2026-data-contract-figures.html` | HTML/CSS 教程图稿源 | 本仓库生成；无外部运行时资源 | 用 `?figure=contexts|anndata` 选择画面，以 Chromium 1600x900 截图 |
| `prompts/vc2026-six-contexts.md` | GPT Image 概念插画 prompt 与科学边界 | 本仓库生成 | 重建或调整“同一目标在六个匿名背景中产生不同群体响应”的概念图 |
| `sources/03-04-figures.html` | 原第 3–4 课（现 [L3-01](../lessons/L3-01-评分指标与离线评估.md)、[L3-02](../lessons/L3-02-公开扰动数据与跨背景验证.md)）HTML/CSS 精确图源 | 本仓库生成；无外部运行时资源 | 用 `?figure=metrics|splits` 选择六指标或验证边界图，以 Chromium 1600x900 截图 |
| `sources/05-06-figures.html` | 原第 5–6 课（现[备选架构附录](../lessons/appendix/非State路线备选架构.md)）HTML/CSS 精确图源 | 本仓库生成；无外部运行时资源 | 用 `?figure=delta|encoders` 选择统计分解或双编码器图 |
| `sources/07-08-figures.html` | 原第 7–8 课（现 [L3-03](../lessons/L3-03-单细胞原始计数生成.md)、[备选架构附录](../lessons/appendix/非State路线备选架构.md)）HTML/CSS 精确图源 | 本仓库生成；无外部运行时资源 | 用 `?figure=counts|model-ladder` 选择计数生成或模型升级图 |
| `sources/09-figures.html` | 原第 9 课（现 [L3-05](../lessons/L3-05-消融集成与最终轮.md)）HTML/CSS 精确图源 | 本仓库生成；无外部运行时资源 | 用 `?figure=final` 渲染最终轮事件驱动流水线 |
| `prompts/03-metric-inspection.md` 至 `prompts/09-final-control-room-v2.md` | 原第 3–9 课 GPT Image 最终 prompt 与定向修订 | 本仓库生成；参考图只作 style/layout reference | 重建七张无文字概念插画；精确事实仍由 HTML 图承载 |
| `prompts/03-09-imagegen-log.md` | 原第 3–9 课 GPT Image 生成、QA 与压缩记录 | 本仓库生成 | 核对模型、参考图角色、母版、最终资产和压缩体积 |
| `sources/L1-01-five-bets.architecture.json` | [L1-01](../lessons/L1-01-领域地图与五种赌注.md)「五种赌注」架构图规格（archify architecture，showcase，zh-CN） | 本仓库生成；交付 HTML 为可再生产物，不入库 | 重建五种赌注地图。交付产物 `output/figures/L1-01-five-bets.html`（spec sha256 `695573f7…`，artifact sha256 `0cf83f01…`，9/9 检查通过）；教程采用版 `docs/lessons/assets/vc2026-course/L1-01-five-bets.webp`（1560×1296，55 KB） |
