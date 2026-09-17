# 事实边界：L2-03 配图 `L2-03-foundation-routes.webp`

这张图是**官方源码静态核验 + notebook 08 合成实验**的可视化，不是任何模型实例的测量记录。
改写或重新导出前先读本文件，防止把源码读取值写成实测值、把合成数据的分档当成真实面板的统计，
或把「扰动能力来自哪里」这条推论讲成「scGPT 预训练学会了扰动」。

- 源文件：`docs/style/sources/L2-03-foundation-routes.gen.py`（生成脚本，`.drawio` 是生成物，勿手改）
- 可编辑源：`docs/style/sources/L2-03-foundation-routes.drawio`（80 个 cell）
- 母版 PNG：`output/tmp/l203_v6.png`（2548×2184，1820×1560 的 1.4× 渲染，Git 忽略）
- 教程采用版：`docs/lessons/assets/vc2026-course/L2-03-foundation-routes.webp`（2200×1886，WebP q86，291.8 KB）
- 渲染通道：CDP（`scripts/drawio-cdp-shot.py`），viewer JS 以 base64 `data:` 内联

---

## 图上每个数字的来源与证据等级

### 面板 (a)：靶点身份怎样到达模型

| 图上的数字 | 值 | 来源 | 等级 |
|---|---|---|---|
| `pert_encoder` 词表大小 | **3** | `generation_model.py:80` 的 `nn.Embedding(3, d_model, padding_idx=pert_pad_id)` | **[S1]** |
| 默认 `pert_pad_id` | 2 | 同文件；教程代码把它设成 0 | **[S1]** |
| 表达值上界 `clamp(max=512)` | 512 | `generation_model.py` 的输入预处理 | **[S1]** |
| 输入嵌入是三路相加 | — | `generation_model.py:138` 的 `total_embs = src + values + perts` | **[S1]** |
| 词表条目数 | 48,292 | 本地解析 `scgpt/tokenizer/default_gene_vocab.json` | **[S1]** |
| 零表达靶点的可区分组合数 | **1**（不是 3） | notebook 08 单元 2 的 `distinct_inputs()` 实测 | **工程假设**（逻辑推论，非官方行为声明） |
| 嵌入维 / 层数 / 头数 / 前馈 | 512 / 12 / 8 / 512 | 论文实现细节 | **[P2]** |
| 结构本体手算 | ≈ 2,079 万 | notebook 08 单元 1；**不含基因嵌入** | **工程假设** |
| 基因嵌入单列 | 48,292 × 512 ≈ 2,473 万 | 同上 | **工程假设** |
| `load_param_prefixs` | encoder / value_encoder / transformer_encoder | 官方微调脚本的加载前缀列表 | **[S1]** |
| 预训练细胞数 | 3,300 万 | 论文 + README Model Zoo（brain 13.2M / blood 10.3M / heart 1.8M / lung 2.1M / kidney 814k / pan-cancer 5.7M） | **[P2]** |
| scBaseCount 细胞数 / UMI | 2.3 亿 / 平均 7,614 | scBaseCount 技术报告 | **[R1]** |
| scBaseCount 物种 / 组织 | 21 / 72 | 同上 | **[R1]** |
| AIDO Cell 输出单位 | TPM | AIDO Cell 报告 | **[R2]** |

### 面板 (b)：算力该往哪儿投

| 图上的数字 | 值 | 来源 | 等级 |
|---|---|---|---|
| 四分量分解式 | `Δ = μ + α(c) + β(t,g) + Γ(c,t,g) + ε` | `decomposition/anova.py:3` | **[S1]** |
| `beta_frac(t)` 定义 | `Var(β_t) / (Var(β_t) + mean_c Var(Γ_c,t))` | `decomposition/anova.py:68-72` | **[S1]** |
| 分档阈值 0.70 / 0.50 | — | **本图自定，不是物理常数**；图上已注明要先在公开真值面板上找拐点 | **工程假设** |
| 合成靶点数 | 40 | notebook 08 单元 4 的 `T = 40` | **工程假设** |
| 分档计数 22 / 9 / 9 | — | notebook 08 单元 4 实测 | **工程假设** |
| 曲线 7 个点 | 0.9985 / 0.9940 / 0.9764 / 0.9126 / 0.7305 / 0.4152 / 0.1496 | notebook 08 单元 5 实测，`B1 / (B1 + 完美Γ)` | **工程假设** |
| 横轴范围 0.05 → 3.20（对数） | — | 同上 `_LO` / `_HI` | **工程假设** |

## 四条硬边界

1. **两条推论是推论，不是官方行为声明。**「扰动标记只有 3 个取值，因此零表达靶点不可区分」
   与「扰动能力 100% 来自下游三套 Perturb-seq，0% 来自预训练」都从源码事实推出。
   源码事实是**[S1]**（可逐行复核），推论本身按**工程假设**对待。图上两处都写了「推论」字样，
   改图时不要删掉限定语、也不要升格成「scGPT 无法处理零表达靶点」这种更强的断言。
2. **面板 (b) 全部是合成数据。** 曲线、分档、阈值都来自 notebook 08 的合成面板，
   演示的是**机制**，不是本赛 300 个靶点的统计，也不是任何公开数据集的复现。
   图上 (b) 面板底部已显式写出这一点，重新导出时必须保留。
3. **scGPT 的规模故意不给总数。** 结构本体（≈2,079 万，不含嵌入）与基因嵌入（≈2,473 万）
   分开列、不相加，因为总量由词表主导而词表随数据版本变化。图上明确要求引用「12 层 / 512 维」。
   **把两者加成一个「≈4,552 万总参数」是错误做法**，本图刻意不提供这个数字。
4. **耗时与显存一个数字都没有。** 本图不涉及任何实测性能数字，不要代填。

## 证据等级对照

- **[S1]** 固定 commit `cebd6fae65` 的官方源码静态核验（未下载权重、未运行推理、未联网）。
  面板 (a) 的结构、行号、词表条目数、`load_param_prefixs` 均属此级。
- **[P2]** scGPT 论文（Nature Methods）正文的架构与预训练语料数字，未复现。
- **[R1] / [R2]** scBaseCount 与 AIDO Cell 的**经 MinerU 机器转换**的一手材料。
  **数字须回 PDF 复核**，等级低于源码核验。图上脚注已写明这一点。
- **[S1] 的分解式来自 `perturbation-decomposition` 仓库固定 commit `a152147806`；
  该仓库无许可证文件，仅作本地阅读，图上已注明。**

## 图面规则（重新导出时必须保持）

- 字号只在生成脚本顶部的 `F_*` 常量里定义，最小 12 模型 px。
- 相邻元素垂直间距 ≥ 20 px；两个面板的标题基线在第一阶段表上对齐。
- **坐标轴与数据曲线必须用 `fedge(..., arrow=False)`。** 默认的 `endArrow=block;endSize=8`
  在这个描边宽度下会画出一个 ~16 px 的三角形，压在 10 px 的顶点标记上，读起来像墨点。
  已踩过：v5 之前的版本轴线与曲线段都带箭头，放大后可见明显黑三角。
- **柱状条与它的文字必须写在同一个 `value` 字符串里**（用 `<div style='text-align:left'>` 排版），
  不要用「色块 + 上层文本」两个 sibling cell：前者触发 `W-OVERLAP`，后者在
  `container=1` 下会被静默裁掉、文字整段消失。已踩过：v1 的 40 个靶点分档条文字全部不见，
  而 `validate.py --score` 当时仍然 0 error —— **结构校验过了不等于画对了，必须看渲染图**。
- 校验两步都要过：`validate.py --score` 必须 0 error 0 warning（当前 score 0）；
  渲染后逐条读 `<path d>`，不应出现意外的曲线命令。
- 导出按模型宽 1820 px 渲染到 1.4×，再 LANCZOS 降到 2200 px 宽（= 模型宽的 1.21×），
  WebP q86，目标 ≤ 300 KB（当前 291.8 KB）。
