# 第 3–9 课 GPT Image 生成记录

## 统一设置

- 模式：`imagegen` skill 的 CLI fallback。当前会话没有暴露内置 `image_gen`，用户已明确要求使用 GPT imagegen。
- 模型：`gpt-image-2`。
- 调用：`edit`，每张图单独调用；`quality=medium`；请求 landscape `1536x1024`。
- 凭证与 Provider：仅在子进程环境注入 Codex 当前凭证和 custom provider `/v1` 地址；未打印、复制或写入仓库。
- Image 1：`../references/vc2025-virtual-cell-challenge-reference.webp`，角色严格为 `style/layout reference`。只继承浅色纸面、深蓝线条、青/黄/珊瑚辅助色、留白和科学编辑插画质感；不继承文字、数字、数据或机制结论。
- 生成边界：七张图都不承载精确标签、指标公式、数据规模或分子机制；这些信息由对应 HTML/CSS 图确定性绘制。
- 原始母版：保存于 Git 忽略的 `output/imagegen/`。
- 教程成品：使用 `cwebp -q 90 -m 6 -mt` 转换；保留原尺寸，不覆盖既有资产。

## Prompt 与资产

| 课 | 最终 prompt | 母版 | 母版尺寸 / 体积 | 教程 WebP | WebP 体积 |
|---:|---|---|---:|---|---:|
| 3 | [03-metric-inspection.md](03-metric-inspection.md) | `output/imagegen/vc2026-course-3-metric-inspection.png` | 1537×1023 / 1,430,537 B | `docs/lessons/assets/vc2026-course/03-metric-inspection-imagegen.webp` | 140,888 B |
| 4 | [04-public-data-bridge.md](04-public-data-bridge.md) | `output/imagegen/vc2026-course-4-public-data-bridge.png` | 1582×994 / 1,989,176 B | `docs/lessons/assets/vc2026-course/04-public-data-bridge-imagegen.webp` | 132,164 B |
| 5 | [05-context-transfer.md](05-context-transfer.md) | `output/imagegen/vc2026-course-5-context-transfer.png` | 1536×1024 / 1,431,214 B | `docs/lessons/assets/vc2026-course/05-context-transfer-imagegen.webp` | 110,704 B |
| 6 | [06-context-target.md](06-context-target.md) | `output/imagegen/vc2026-course-6-context-target.png` | 1692×930 / 1,196,424 B | `docs/lessons/assets/vc2026-course/06-context-target-imagegen.webp` | 97,074 B |
| 7 | [07-count-population.md](07-count-population.md) | `output/imagegen/vc2026-course-7-count-population.png` | 1536×1024 / 1,833,563 B | `docs/lessons/assets/vc2026-course/07-count-population-imagegen.webp` | 106,860 B |
| 8 | [08-model-workshop.md](08-model-workshop.md) | `output/imagegen/vc2026-course-8-model-workshop.png` | 1774×887 / 1,378,977 B | `docs/lessons/assets/vc2026-course/08-model-workshop-imagegen.webp` | 148,076 B |
| 9 | [09-final-control-room.md](09-final-control-room.md) + [定向修订](09-final-control-room-v2.md) | `output/imagegen/vc2026-course-9-final-control-room-v2.png` | 1774×887 / 1,478,369 B | `docs/lessons/assets/vc2026-course/09-final-control-room-imagegen.webp` | 130,656 B |

API 对部分 landscape 请求返回了同方向但不同精确尺寸的位图；转换时保留实际返回尺寸，没有拉伸。

## 人工 QA

逐张检查了主题、构图、文字、水印、箭头关系、裁切、留白和科学边界。第 3–8 课首版通过；第 9 课首版把质量门画成盾牌，偏离“数据与预测审计”的语义，因此只针对该区域做一次 edit：改为放大检查、矩阵对齐和普通勾选，其他构图保持不变。最终七张图均无可读文字或水印；图中细胞形态、颜色、装置和箭头只作概念辅助，不能作为真实细胞身份、实验机制或模型性能证据。

---

## 附：确定性图源的课号修订（2026-09-18）

上面七张是 GPT 生成的概念插画。同一批课还有一组**由 HTML/CSS 确定性绘制**的图，它们不经过模型，因此不在上表内，但同样受课号重排影响。本轮修订了两张。

### 为什么要改

课号在 2026-09-17 由连续数字改成层前缀（`第 3 课` → `L3-01`，`第 4 课` → `L3-02`）。这两张图的 kicker 里印着旧课号，读者会在图里看到已经不存在的编号。**文件名保持不变**——`03-`/`04-` 前缀记录在本节附表与 `docs/style/README.md` 里，改名会破坏溯源。

### 修订记录

| 图源（未改名） | 图内 kicker 前 → 后 | 现引用它的课 | 导出版本 |
|---|---|---|---|
| `sources/03-04-figures.html`（`?figure=metrics`） | `VC2026 第 3 课 · 评分指标` → `VC2026 L3-01 · 评分指标` | [L3-01](../../lessons/L3-01-评分指标与离线评估.md) | `docs/lessons/assets/vc2026-course/03-metrics-lenses.webp`，2200×1238，190.9 KB，WebP q86 |
| `sources/03-04-figures.html`（`?figure=splits`） | `VC2026 第 4 课 · 验证边界` → `VC2026 L3-02 · 验证边界` | [第 03 课（原 L3-02）](../../lessons/03-State上手.md) | `docs/lessons/assets/vc2026-course/04-validation-splits.webp`，2200×1238，152.0 KB，WebP q86 |

页 `<title>` 同步由「VC2026 第 3-4 课教学图」改为「VC2026 L3-01 / L3-02 教学图」。

### 导出方式

新增 `scripts/html-cdp-shot.py`（与 `scripts/drawio-cdp-shot.py` 同一 CDP 通道，理由见 `docs/style/README.md` 的「渲染走 CDP」）。流程：

1. 1600×900、`deviceScaleFactor=2` 渲染到 3200×1800 PNG；
2. Pillow LANCZOS 超采样降到 2200 px 宽（1600 × 1.375，落在 AGENTS.md「教程图片」第 10 条的 1.2–1.4 倍区间）；
3. WebP `quality=86`，单张 ≤ 300 KB。

**新脚本的一个坑（已修）**：`Page.setDocumentContent` **复用同一个 JS realm**，所以连续渲染两张图时，上一轮注入的 `URLSearchParams` 补丁仍在，第二次会把补丁再包一层，`?figure=` 静默停止解析（表现为「figure never became active」）。修法是**每次渲染开一个新 target**（`PUT /json/new?about:blank`），拿到干净的 realm；渲染完 `GET /json/close/<id>` 收掉。修后连跑三次产物字节数完全一致。

**没有修订的图（已核对无课号）**：`05-transferable-delta`、`06-context-target-encoders`、`07-count-generation`、`08-model-ladder`、`09-final-round-pipeline` 的 kicker 分别是「VC2026 · 跨背景统计基线」「VC2026 · CONTEXT × TARGET 表示」「COUNT GENERATION · …」「MODEL LADDER · …」与无 kicker，都不含课号。issue #10 把它们一并列出是保守的超集，实际需要重导出的只有上述两张。

