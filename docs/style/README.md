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


## WSL → Windows Chrome 的 CDP 中转（2026-09-18 补）

上面那套 CDP 通道在**从 WSL 内部**跑时要多一跳：Chrome 装在 Windows 侧，它的调试端口默认只 bind `127.0.0.1`，而 WSL 里的 `localhost` 是**另一台机器**，直连 `127.0.0.1:9222` 会连到 WSL 自己。做法是让 Windows 侧多监听一个对外端口，把它转发给本机 Chrome：

```text
  WSL 侧渲染脚本 ──→ 127.0.0.1:9222 ──(WSL forwarder)──→ <Windows 主机 IP>:9223
                                                                  │
                                                    (Windows 侧 TcpListener 转发)
                                                                  ↓
                                                        127.0.0.1:9222  ← Chrome
```

- **Windows 侧**：起一个 `System.Net.Sockets.TcpListener`，bind **`0.0.0.0:9223`**，对每条进来的连接再开一条到 `127.0.0.1:9222` 的 TCP，做双向字节搬运。`0.0.0.0` 是必需的——只 bind `127.0.0.1` 时 WSL 的包根本到不了这个 listener。
- **WSL 侧**：把本地的 `127.0.0.1:9222` 转到 `<Windows 主机 IP>:9223`，渲染脚本仍按 `127.0.0.1:9222` 连（脚本不用改）。
- **`<Windows 主机 IP>` 是机器相关值，不要硬编码进任何脚本或文档。** 在 WSL 里用默认网关拿它：

  ```bash
  ip route show default | awk '{print $3}'      # 例：172.29.240.1（WSL 的 Windows 主机侧网关）
  ```

  WSL2 里这个地址就是 Windows 主机在虚拟网络里的地址，重启后可能变，所以每次现取。
- **它是临时通道**：只在需要渲染时起，用完关掉。不要把 9223 常驻对外监听。
- 详细命令与已知失败排查见 `scripts/html-cdp-shot.py` 顶部注释与 `scripts/drawio-cdp-shot.py`；两份脚本走的是同一个 CDP 客户端实现，只是输入源不同（HTML 图稿 vs `.drawio`）。


## 索引

| 文件 | 类型与角色 | 来源与状态 | 适用场景 |
|---|---|---|---|
| `references/vc2025-virtual-cell-challenge-reference.webp` | 科学信息图的 style/layout reference | 用户提供，原始 URL、作者与版权待核验；2026-08-22 归档 | 浅蓝论文图背景、A-D 分区、细胞/矩阵图标、深蓝/青/橙配色 |
| `sources/vc2025-lesson-figures.html` | HTML/CSS 教程图稿源 | 本仓库生成；无外部运行时资源 | 用 `?figure=crispri|unpaired|split|metrics|shift` 选择画面，以 Chromium 1600x900 截图 |
| `prompts/vc2025-learning-roadmap.md` | 参考图生成 prompt 与修订记录 | 本仓库生成 | 重建或调整 VC2025 学习路线总览图 |
| `sources/vc2026-data-contract-figures.html` | HTML/CSS 教程图稿源 | 本仓库生成；无外部运行时资源 | 用 `?figure=contexts|anndata` 选择画面，以 Chromium 1600x900 截图 |
| `prompts/vc2026-six-contexts.md` | GPT Image 概念插画 prompt 与科学边界 | 本仓库生成 | 重建或调整“同一目标在六个匿名背景中产生不同群体响应”的概念图 |
| `sources/02-state-figures.html` | [第 02 课](../lessons/02-State模型拆解.md)「State 模型拆解」HTML/CSS 精确图源；3 幅（配对不存在 / 一次 forward 的张量形状 / Energy 距离三项） | 本仓库生成；2026-09-18；无外部运行时资源 | 用 `?figure=paired\|shapes\|energy` 选择画面，以 Chromium 1600x900 截图；导出走 `scripts/html-cdp-shot.py`，成品 `docs/lessons/assets/vc2026-course/02-paired-vs-two-clouds.webp`（2200×1238，123.1 KB）、`02-forward-shapes.webp`（183.1 KB）、`02-energy-three-terms.webp`（167.0 KB），均 WebP q86 |
| `sources/03-state-finetune-figures.html` | [第 03 课](../lessons/03-State上手.md)「State 上手」HTML/CSS 精确图源；3 幅（只换两个接口 / 浮点到原始计数的空白格 / t_step 敏感性与先测后租） | 本仓库生成；2026-09-18；无外部运行时资源 | 用 `?figure=swap\|counts\|budget` 选择画面，以 Chromium 1600x900 @ `deviceScaleFactor=2` 截图；导出走 `scripts/html-cdp-shot.py`，LANCZOS 降到 2200 px → WebP q86，成品 `docs/lessons/assets/vc2026-course/03-swap.webp`（2200×1238，142 KB）、`03-counts.webp`（156 KB）、`03-budget.webp`（120 KB）。**别在图里写 LaTeX**：HTML 截图无 MathJax，`$L_i$` 会原样渲染成字面美元符号，改用 `<code>L_i</code>` |
| `sources/03-04-figures.html` | [第 04 课](../lessons/04-你怎么知道改进是真的.md)（原 L3-01，2026-09-18 并入）/ [第 03 课](../lessons/03-State上手.md)（原 L3-02 已于 2026-09-18 并入）HTML/CSS 精确图源；**文件名保留旧课号（原第 3–4 课），metrics 图内 kicker 已随第 04 课改为 `VC2026 第 04 课 · 评分指标`（2026-09-18 第二次修订）**；splits 图的原消费者已并入第 03 课，暂无正文引用，保留备复用 | 本仓库生成；无外部运行时资源 | 用 `?figure=metrics\|splits` 选择六指标或验证边界图，以 Chromium 1600x900 截图；导出走 `scripts/html-cdp-shot.py`，metrics 成品 `03-metrics-lenses.webp`（2200×1238，191 KB，WebP q86） |
| `sources/05-06-figures.html` | 原第 5–6 课（现[备选架构附录](../lessons/appendix/非State路线备选架构.md)）HTML/CSS 精确图源 | 本仓库生成；无外部运行时资源 | 用 `?figure=delta\|encoders` 选择统计分解或双编码器图 |
| `sources/04-evaluation-figures.html` | [第 04 课](../lessons/04-你怎么知道改进是真的.md)「噪声地板与消融阶梯」HTML/CSS 精确图源；2 幅（噪声地板实测三面板 / 消融 8 级阶梯） | 本仓库生成；2026-09-18；无外部运行时资源 | 用 `?figure=floor\|ladder` 选择画面，以 Chromium 1600x900 @ `deviceScaleFactor=2` 截图；导出走 `scripts/html-cdp-shot.py`，LANCZOS 降到 2200 px → WebP q86，成品 `docs/lessons/assets/vc2026-course/04-noise-floor.webp`（2200×1238，223 KB）、`04-ablation-ladder.webp`（194 KB） |
| `sources/05-stack-figures.html` | [第 05 课](../lessons/05-Stack推理时把无标签细胞当示例.md)「Stack 上下文机制」HTML/CSS 精确图源；2 幅（T=5 迭代生成计划 / 窗口切分与 137 个复制行） | 本仓库生成；2026-09-18；无外部运行时资源 | 用 `?figure=genplan\|windows` 选择画面，以 Chromium 1600x900 @ `deviceScaleFactor=2` 截图；导出走 `scripts/html-cdp-shot.py`，LANCZOS 降到 2200 px → WebP q86，成品 `docs/lessons/assets/vc2026-course/05-icl-generation-plan.webp`（2200×1238，168.5 KB）、`05-window-split-duplicates.webp`（178.9 KB） |
| `sources/07-08-figures.html` | 原第 7–8 课（counts 图原消费者 [L3-03] 已并入 [第 03 课](../lessons/03-State上手.md)，正文现用 03 课自带的 counts 图；model-ladder 图归 [备选架构附录](../lessons/appendix/非State路线备选架构.md)）HTML/CSS 精确图源 | 本仓库生成；无外部运行时资源 | 用 `?figure=counts\|model-ladder` 选择计数生成或模型升级图 |
| `sources/09-figures.html` | 原第 9 课（现 [L3-05](../lessons/L3-05-消融集成与最终轮.md)）HTML/CSS 精确图源 | 本仓库生成；无外部运行时资源 | 用 `?figure=final` 渲染最终轮事件驱动流水线 |
| `prompts/03-metric-inspection.md` 至 `prompts/09-final-control-room-v2.md` | 原第 3–9 课 GPT Image 最终 prompt 与定向修订 | 本仓库生成；参考图只作 style/layout reference | 重建七张无文字概念插画；精确事实仍由 HTML 图承载 |
| `prompts/03-09-imagegen-log.md` | 原第 3–9 课 GPT Image 生成、QA 与压缩记录；**附表含两张 HTML 图源的课号修订记录** | 本仓库生成 | 核对模型、参考图角色、母版、最终资产和压缩体积 |
| `sources/L1-01-five-bets.architecture.json` | [第 06 课](../lessons/06-其余路线全景.md)「五种赌注」架构图规格（archify architecture，showcase，zh-CN）。**文件名保留旧课号**：原 L1-01 课已于 2026-09-18 被第 06 课吸收删除 | 本仓库生成；交付 HTML 为可再生产物，不入库 | 重建五种赌注地图。交付产物 `output/figures/L1-01-five-bets.html`（spec sha256 `695573f7…`，artifact sha256 `0cf83f01…`，9/9 检查通过）；教程采用版 `docs/lessons/assets/vc2026-course/L1-01-five-bets.webp`（1560×1296，55 KB） |
| `sources/L2-01-state-architecture.drawio` | [第 02 课](../lessons/02-State模型拆解.md) State（ST）架构图，drawio 可编辑源；3 面板（前向路径 / 集合自注意力 / Energy 距离集合损失），配色即 "Attention Is All You Need" 原图配色（draw.io 默认调色板）。**文件名保留旧课号 `L2-01`**：图源是生成物且记录在溯源日志里，改名会破坏溯源（原 L2-01 课已于 2026-09-18 被 02 课吸收删除） | 本仓库生成；2026-09-17（r3，字号/间距/体积重做）；108 个 cell，34.7 KB，sha256 `58b313d6…`；`validate.py --score` 0 error 0 warning score 0 | 重建 State 结构图。渲染走 CDP 通道（本机沙箱下 Chrome 只认 `data:` URI，见上文「drawio-skill 使用约定」）；教程采用版 `docs/lessons/assets/vc2026-course/L2-01-state-architecture.webp`（2200×1942，172 KB，WebP q86，sha256 `54cc86c3…`）被 02 课 §4 引用 |
| `sources/L2-01-state-architecture.gen.py`<br>`sources/L2-01-state-architecture.finalize.py` | 上面那张 `.drawio` 的**生成脚本**与**降采样/压缩脚本**（`.drawio` 是生成物，不要手改） | 本仓库生成；2026-09-17 | 改字号、间距、面板布局只改 gen 脚本顶部的 scale 常量与坐标后重跑；finalize 负责 bbox 裁剪 + 超采样降采样 + WebP q86 |
| `prompts/L2-01-state-architecture-facts.md` | 第 02 课架构图的**事实边界**：图上每个数字的来源与证据等级，以及「两套配置不能混用」的提醒（文件名保留旧课号，理由同上） | 本仓库生成；2026-09-17 | 修图或引用该图前先读；防止把配置读取值/手算值写成实测值，或把 hidden 328 与 hidden 768 两套配置合并 |
| `sources/L2-02-stack-icl.drawio` | [第 05 课](../lessons/05-Stack推理时把无标签细胞当示例.md) Stack 上下文学习图，drawio 可编辑源；3 面板（前向路径与双轴注意力 / 两轴代价与 8 GiB 边界 / 窗口切分与复制行后果），配色沿用 draw.io 默认调色板。**文件名保留旧课号 `L2-02`**：原 L2-02 课已于 2026-09-18 被第 05 课吸收删除，成品图现由第 05 课 §0 引用 | 本仓库生成；2026-09-17；125 个 cell，sha256 见 `validate.py` 记录；`validate.py --score` 0 error 0 warning score 0 | 重建 Stack 结构图。渲染走 CDP 通道（本机沙箱下 Chrome 只认 `data:` URI）；教程采用版 `docs/lessons/assets/vc2026-course/L2-02-stack-icl.webp`（2200×1958，295.8 KB，WebP q86） |
| `sources/L2-02-stack-icl.gen.py` | 上面那张 `.drawio` 的**生成脚本**（`.drawio` 是生成物，不要手改）；含末尾的**两级重归属**后处理，把面板与卡片内的绝对坐标元素改成对应 parent，以通过 validate.py 的 W-OVERLAP 同父判定 | 本仓库生成；2026-09-17 | 改字号、间距、面板布局只改脚本顶部的 `F_*` / `BAR_*` 常量与坐标后重跑。柱状图的 √ 压缩刻度写在脚本里并有注释说明为何不能用线性刻度 |
| `prompts/L2-02-stack-icl-facts.md` | 第 05 课配图（文件名保留旧课号）的**事实边界**：图上每个数字的来源与证据等级、三条硬边界（无耗时数字 / 非实测 / 两处源码与论文差异）、以及重新导出时必须保持的图面规则 | 本仓库生成；2026-09-17 | 修图或引用该图前先读；防止把手算显存写成实测值，或把 `K=256` 与 `K=512` 两档合并叙述 |
| `sources/L2-03-foundation-routes.drawio` | [第 06 课](../lessons/06-其余路线全景.md) 基础模型路线图，drawio 可编辑源；2 面板（靶点身份怎样到达模型：scGPT 三入口与零表达靶点的接口不可区分性 / 算力该往哪儿投：beta_frac 分档与机会窗口曲线），配色沿用 draw.io 默认调色板。**文件名保留旧课号**：原 L2-03 课已于 2026-09-18 被第 06 课吸收删除；图内 kicker 已随第 06 课更新（2026-09-18 第二次修订） | 本仓库生成；2026-09-18；80 个 cell，`validate.py --score` 0 error 0 warning score 0 | 三条基础模型路线（scGPT / scBaseCount / AIDO Cell）的横向对照。渲染走 CDP 通道（本机沙箱下 Chrome 只认 `data:` URI）；教程采用版 `docs/lessons/assets/vc2026-course/L2-03-foundation-routes.webp`（2200×1886，291.8 KB，WebP q86） |
| `sources/L2-03-foundation-routes.gen.py` | 上面那张 `.drawio` 的**生成脚本**（`.drawio` 是生成物，不要手改）；含末尾的**两级重归属**后处理，把两个图框（`b_chb` / `b_cvb`）内的绝对坐标元素改成对应 parent，以通过 validate.py 的 W-OVERLAP 同父判定 | 本仓库生成；2026-09-18 | 改字号、间距、面板布局只改脚本顶部的 `F_*` 常量与坐标后重跑。`fedge(..., arrow=False)` 用于坐标轴与数据曲线——默认 `endArrow=block` 会画出压住顶点标记的黑三角 |
| `prompts/L2-03-foundation-routes-facts.md` | 第 06 课配图（文件名保留旧课号）的**事实边界**：图上每个数字的来源与证据等级、四条硬边界（两条推论不得升格为官方声明 / 面板 b 全为合成数据 / scGPT 规模刻意不给总数 / 无耗时数字）、以及两个踩过的绘图坑 | 本仓库生成；2026-09-18 | 修图或引用该图前先读；防止把「扰动能力 0% 来自预训练」这条推论写成 scGPT 官方行为，或把 2,079 万与 2,473 万加成一个「总参数量」 |
| `sources/06-route-figures.html` | [第 06 课](../lessons/06-其余路线全景.md)「靶点算力分档」HTML/CSS 精确图源；1 幅（`beta_frac` 公式与分档决策表 + 匿名背景三条边界） | 本仓库生成；2026-09-18；无外部运行时资源 | 用 `?figure=decision` 选择画面，以 Chromium 1600x840 @ `deviceScaleFactor=2` 截图；导出走 `scripts/html-cdp-shot.py`，LANCZOS 降到 2200 px → WebP q86，成品 `docs/lessons/assets/vc2026-course/06-route-decision.webp`（2200×1155，208.7 KB） |

