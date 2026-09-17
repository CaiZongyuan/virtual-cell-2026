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
| **模型 / 论文式架构图**（神经网络结构、算法流程这类论文 Figure 风格的示意图） | `.agents/skills/drawio-skill` | 可编辑 `.drawio` 源（入库 `sources/`）+ 渲染截图转 WebP 入教程 |
| **系统架构 / 数据流 / 时序图 / 状态机 / 泳道** | 同上，`.agents/skills/drawio-skill` | 同上。**archify 已于 2026-09-17 卸载**，这两类图统一走 drawio |
| **概念插画 / 封面 / 风格化示意图** | 子代理经浏览器用 ChatGPT 生成，prompt 取自 `prompts/gallery-research-paper-figures.md` | 母版留 `output/imagegen/`（Git 忽略），采用版转 WebP 入教程 |
| **标签密集、要求数值或机制准确的流程图** | HTML/CSS/canvas 手绘 | 图稿源入 `sources/`，Chromium 截图后转 WebP |

硬性边界：

1. **不要拿系统架构语汇的图形工具去画论文式结构图**（用户 2026-09-17 裁决）：archify 面向系统架构，画不了 `Linear → GELU → ReLU`、残差跳线、`N×` 重复块这类结构——当时实测出来的图是错的。现在所有结构图与流程图统一走 `drawio-skill`。
2. **drawio 图必须 light 配色、简体中文标签**；风格参照论文原图，不要自创。字号、间距、连线避让与体积预算见 `AGENTS.md`「教程图片」第 9/10 条。
3. **生成式图片只是解释性插画**，不能作为实验结构、机制或数据证据。

**archify 已于 2026-09-17 卸载。** 技能本体与两个 `.claude/skills/` 符号链接都已移除；`skills-lock.json` 里的条目同步删除。只保留一张历史产物的规格 `sources/L1-01-five-bets.architecture.json` 与它的成品 WebP——规格是那张图的来源记录，要重建需先重新安装 archify。

## drawio-skill 使用约定（2026-09-17 实测）

本机**没有 draw.io CLI**（`draw.io.exe` / `drawio` 都不存在），因此走 skill 记录的浏览器回退路径，不要试图安装：

1. **渲染走 CDP，不要走 `chrome --screenshot <url>`。** 本机沙箱下 Chrome 只会渲染 `data:` URI：`file://` 与 `http://127.0.0.1:<port>` 都**退出码 0 但不写文件**（控制组 `data:text/html,<h1>x</h1>` 能出图，说明不是 Chrome 坏了）；解除沙箱后连 `data:` 也失败。而把页面塞进 `data:` URL 又撞上 Windows 命令行 32767 字符上限（render.html 37 KB + viewer 4 MB）。
   稳定通道是 **DevTools 协议**——监听端口是 bind 不是 connect，不碰沙箱的文件与网络限制：
   - `chrome.exe --headless=new --disable-gpu --no-first-run --remote-allow-origins='*' --remote-debugging-port=9222 --user-data-dir=<fresh> about:blank`（后台常驻）
   - Python（需 `websocket-client`）连 `/json` 拿 `webSocketDebuggerUrl`，然后 `Page.enable` → `Emulation.setDeviceMetricsOverride{width,height,deviceScaleFactor}` → `Page.setDocumentContent{frameId, html}` → 轮询 `Runtime.evaluate` 直到 `document.querySelectorAll('svg').length > 0` → `Page.captureScreenshot{format:"png",captureBeyondViewport:true}`。
   - viewer JS **以 base64 `data:text/javascript` 内联**：`setDocumentContent` 出来的文档没有 base URL，相对路径 `src="viewer-static.min.js"` 解析不了，外部 CDN 也连不上（Chrome 无网络）。`data:` 是绝对 URL，所以可行。
   - 参考实现已入库：`scripts/drawio-cdp-shot.py`（通用工具）。本机无 draw.io CLI 的替代路径成立，且不再需要 `--force-device-scale-factor`。
2. **不要用 `--screenshot=` + POSIX 路径**（会静默失败）；旧版记的 `--force-device-scale-factor=2` 那套只在能用 URL 直连时成立，已不适用。
3. **`perimeter=rectanglePerimeter` 是必需的**，不是可选项。draw.io 默认矩形 perimeter 按 `s=ceil(h/2)` 构造八边形，在扁矩形（例如 2px 高的汇流线）上退化成只有两端点，导致 `entryX/entryY` 的小数被吸附到端点——渲染出来就是一条斜线。扁平件上还应把 `entryY` 取 `0`/`1`（角点），不要取 `0.5`（中心线方向退化，射线直接打到左右端）。
4. **两条独立校验都要做**：结构用 skill 自带 `validate.py <file> --score`，必须 0 error 0 warning；几何用 `--dump-dom` 抓 DOM 后逐条读 `<path d="…">`。注意本机 viewer 渲染**不输出 `data-cell-id`**，要直接全局解析 `<path>`；正常结果应 0 条含 `C/Q/A/S` 曲线命令（含曲线说明某个 `entryX` 与源 `exitX` 差了 1–2px）。
5. **中文 DOM 必须用 Python `subprocess`（`encoding="utf-8"`）抓**，不要用 PowerShell 重定向，否则中文被替换成 `?`，标签内容无从核对。
6. **文字溢出**交给放大的局部截图判断（DOM 里的 `foreignObject` 是 flex 定位，算不出真实文本框）。长段说明**用 `&#xa;` 显式断行**，不要依赖 `whiteSpace=wrap`。
7. `.drawio` 里的边全部用 `edgeStyle=none` + 显式 `exitX/exitY/entryX/entryY` 或 `<Array as="points">`：几何完全由坐标决定，不依赖 router，渲染可预期。残差跳线这类端点不在形状上的线用浮动边（`sourcePoint`/`targetPoint` + 中间点）。
8. **图面可读性与体积**（2026-09-17 用户反馈后固化为硬规则，细则见 `AGENTS.md`「教程图片」）：字号只在文件顶部一份 scale 常量里写，最小不低于 12 模型 px；相邻元素垂直间距 ≥ 20 px；图例放在页眉横排，不要挤在正文左下与图注争位；长跳线要留在自己的面板内，**不得穿过其他面板的虚线边框**；导出按「显示分辨率 × 1.2–1.4」超采样后降采样，不要 2x 满分辨率入库。


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
| `sources/L2-01-state-architecture.drawio` | [L2-01](../lessons/README.md) State（ST）架构图，drawio 可编辑源；3 面板（前向路径 / 集合自注意力 / Energy 距离集合损失），配色即 "Attention Is All You Need" 原图配色（draw.io 默认调色板） | 本仓库生成；2026-09-17（r3，字号/间距/体积重做）；108 个 cell，34.7 KB，sha256 `58b313d6…`；`validate.py --score` 0 error 0 warning score 0 | 重建 State 结构图。渲染走 CDP 通道（本机沙箱下 Chrome 只认 `data:` URI，见上文「drawio-skill 使用约定」）；教程采用版 `docs/lessons/assets/vc2026-course/L2-01-state-architecture.webp`（2200×1942，172 KB，WebP q86，sha256 `54cc86c3…`） |
| `sources/L2-01-state-architecture.gen.py`<br>`sources/L2-01-state-architecture.finalize.py` | 上面那张 `.drawio` 的**生成脚本**与**降采样/压缩脚本**（`.drawio` 是生成物，不要手改） | 本仓库生成；2026-09-17 | 改字号、间距、面板布局只改 gen 脚本顶部的 scale 常量与坐标后重跑；finalize 负责 bbox 裁剪 + 超采样降采样 + WebP q86 |
| `prompts/L2-01-state-architecture-facts.md` | L2-01 架构图的**事实边界**：图上每个数字的来源与证据等级，以及「两套配置不能混用」的提醒 | 本仓库生成；2026-09-17 | 修图或引用该图前先读；防止把配置读取值/手算值写成实测值，或把 hidden 328 与 hidden 768 两套配置合并 |
| `sources/L2-02-stack-icl.drawio` | [L2-02](../lessons/L2-02-Stack与上下文学习.md) Stack 上下文学习图，drawio 可编辑源；3 面板（前向路径与双轴注意力 / 两轴代价与 8 GiB 边界 / 窗口切分与复制行后果），配色沿用 draw.io 默认调色板 | 本仓库生成；2026-09-17；125 个 cell，sha256 见 `validate.py` 记录；`validate.py --score` 0 error 0 warning score 0 | 重建 Stack 结构图。渲染走 CDP 通道（本机沙箱下 Chrome 只认 `data:` URI）；教程采用版 `docs/lessons/assets/vc2026-course/L2-02-stack-icl.webp`（2200×1958，295.8 KB，WebP q86） |
| `sources/L2-02-stack-icl.gen.py` | 上面那张 `.drawio` 的**生成脚本**（`.drawio` 是生成物，不要手改）；含末尾的**两级重归属**后处理，把面板与卡片内的绝对坐标元素改成对应 parent，以通过 validate.py 的 W-OVERLAP 同父判定 | 本仓库生成；2026-09-17 | 改字号、间距、面板布局只改脚本顶部的 `F_*` / `BAR_*` 常量与坐标后重跑。柱状图的 √ 压缩刻度写在脚本里并有注释说明为何不能用线性刻度 |
| `prompts/L2-02-stack-icl-facts.md` | L2-02 配图的**事实边界**：图上每个数字的来源与证据等级、三条硬边界（无耗时数字 / 非实测 / 两处源码与论文差异）、以及重新导出时必须保持的图面规则 | 本仓库生成；2026-09-17 | 修图或引用该图前先读；防止把手算显存写成实测值，或把 `K=256` 与 `K=512` 两档合并叙述 |

