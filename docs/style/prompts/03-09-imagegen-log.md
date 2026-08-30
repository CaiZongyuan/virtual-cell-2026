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
