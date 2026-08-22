# VC2025 学习路线总览图

## 生成配置

- 模式：`$imagegen` CLI fallback，`edit`
- 模型：`gpt-image-2`
- 质量与尺寸：`medium`，`1536x1024`
- Image 1：`../references/vc2025-virtual-cell-challenge-reference.webp`，角色为 `style/layout reference`，不是 edit target
- 原始母版：`output/imagegen/vc2025-learning-roadmap-ref-v2.png`，由 Git 忽略
- 教程成品：`docs/lessons/assets/vc2025/learning-roadmap-imagegen.webp`，WebP quality 90

## Prompt

```text
Use case: scientific-educational
Primary request: Create a new Chinese scientific learning-roadmap infographic for the VC2025 learning guide. Image 1 is a style and layout reference only, not an edit target: replace all original English text, data, panels, and scientific content. Reuse only its pale blue paper-figure aesthetic, A-D panel organization, clean arrows, simple cell and matrix icon language, restrained navy/cyan/orange palette, thin outlines, and dense but orderly visual hierarchy.
Scene/background: flat pale blue-white scientific figure canvas with a thin dark border
Subject: Four-panel learning flow. Panel A introduces biological intuition with NTC control cells flowing through CRISPRi perturbation to a changed single-cell expression population. Panel B shows the VC2025 H1 task split as 150 training targets, 50 validation targets, and 100 test targets. Panel C shows three complementary metrics DES, PDS, and MAE with tiny set-overlap, ranking, and error-chart icons. Panel D shows transfer to VC2026: anonymous-context NTC plus target gene flows into cross-context prediction and exactly 400 predicted cells per context-target combination.
Style/medium: publication-quality scientific editorial infographic matching only the reference image's visual grammar; flat vector-like shapes; crisp typography; no photorealism
Composition/framing: wide landscape canvas, title centered at top, panels A B C across the upper row and panel D as a full-width process strip below, strong left-to-right reading order, generous margins
Color palette: pale blue-gray background, deep navy titles, cyan control cells, coral perturbed cells, muted periwinkle matrices, small yellow accents
Text (verbatim): "VC2025 学习路线"; "A 任务直觉"; "NTC 对照"; "CRISPRi 扰动"; "单细胞表达"; "群体分布转移"; "B 2025 任务"; "H1 细胞背景"; "150 训练"; "50 验证"; "100 测试"; "C 三项指标"; "DES 响应基因"; "PDS 扰动配对"; "MAE 数值误差"; "D 迁移到 2026"; "匿名背景 NTC"; "待扰动基因"; "跨背景预测"; "400 个细胞/组合"
Constraints: scientifically correct relationships; visually distinguish NTC from perturbed populations; show 2025 as one H1 background with observed training perturbations; show 2026 as NTC-only context input; preserve exact numbers 150, 50, 100, and 400; all Chinese text legible; no citations; no logos; no watermark; do not copy source text or source data
Avoid: English prose, extra metrics, invented numbers, DNA cutting, cell before-after pairing, dark background, 3D rendering, decorative gradients, tiny unreadable text
```

## 人工修订

第一版错误地把 50 个验证扰动画成已观测。第二次定向编辑将 B 面板改为：150 个训练扰动已观测，50 个验证与 100 个测试扰动均未观测，并逐项核对 `CRISPRi`、DES、PDS、MAE 和数字标签。
