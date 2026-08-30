# VC2026 六个匿名背景概念插画

## 生成配置

- 模式：`$imagegen` CLI fallback，`edit`
- 模型：`gpt-image-2`
- 质量与尺寸：`medium`，`1536x1024`
- Image 1：`../references/vc2025-virtual-cell-challenge-reference.webp`，角色为 `style/layout reference`，不是 edit target
- 原始母版：`output/imagegen/vc2026-six-contexts-imagegen.png`，由 Git 忽略
- 教程成品：`docs/lessons/assets/vc2026/six-contexts-imagegen.webp`，WebP quality 90

## Prompt

```text
Use case: scientific-educational
Asset type: conceptual section illustration for a Chinese tutorial about virtual-cell modeling
Primary request: Create a completely new scientific editorial illustration showing that the same gene perturbation can produce different population-level responses in six anonymous cellular contexts.
Input images: Image 1 is a style/layout reference only, not an edit target. Replace all original content, text, data, panels, and scientific claims. Reuse only its pale paper-like background, restrained navy/teal/coral/yellow palette, thin scientific linework, flat vector-like cell language, and orderly publication-figure composition.
Scene/backdrop: a clean pale blue-white scientific canvas
Subject: exactly six distinct shallow culture wells arranged as two rows of three. Every well contains a population of many cells, with small within-well variation but a coherent visual identity. A single identical abstract amber gene-target token is repeated above each well. Beneath each token, the corresponding cell population shifts into a visibly different but plausible expression-pattern mosaic, emphasizing target-by-context interaction at the population level.
Style/medium: polished scientific editorial illustration, flat vector-like shapes with subtle print texture, visually engaging but not photorealistic
Composition/framing: wide landscape, exactly six equal visual groups in a strict two-by-three arrangement, generous whitespace, clear repeated-target rhythm, each well visibly contains many cells rather than one cell
Color palette: pale blue-gray background, deep navy outlines, teal and blue control-state cells, coral and yellow response accents, a small amount of green for contrast
Constraints: exactly six wells; exactly one repeated identical target token associated with each well; show populations rather than individual paired before/after cells; no text; no letters; no numbers; no labels; no logos; no watermark; no citations; no DNA cutting; no organs; no literal claim that the anonymous contexts have known identities
Avoid: extra wells, a single cell representing a context, one-to-one cell trajectories, chromosomes being cut, realistic tissue histology, dark background, gradients, 3D glossy rendering, decorative blobs, tiny pseudo-text
```

## 科学边界

该图只建立“同一目标 × 不同背景 → 不同群体响应”的直觉。六个培养皿不代表 A–F 的真实形态或组织身份，颜色差异也不是实验数据。

## 生成与压缩结果

- 首次生成即满足六个培养皿、六个相同目标符号、每个背景为细胞群、无文字和无 DNA 切割等约束，未继续消耗 API 做变体。
- PNG 母版：1536 × 1024，1,983,084 bytes。
- WebP 成品：1536 × 1024，189,060 bytes；`cwebp -q 90 -m 6 -mt`，体积减少约 90.5%。
- 人工检查：没有伪文字、额外培养皿、水印或逐细胞前后配对；细胞颜色与形态仅作视觉区分，已在正文图注声明科学边界。
