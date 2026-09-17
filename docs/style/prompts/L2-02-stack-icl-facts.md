# 事实边界：L2-02 配图 `L2-02-stack-icl.webp`

这张图是**源码静态核验 + 手算**的可视化，不是实验结果的记录。改写或重新导出前先读本文件，
防止把配置读取值、手算值写成实测值，或把预训练档（`K=256`）与后训练档（`K=512`）的
数字合并成一句话。

- 源文件：`docs/style/sources/L2-02-stack-icl.gen.py`（生成脚本，`.drawio` 是生成物，勿手改）
- 可编辑源：`docs/style/sources/L2-02-stack-icl.drawio`（125 个 cell）
- 母版 PNG：`output/tmp/L2-02-stack-icl.png`（2275×2025，Git 忽略）
- 教程采用版：`docs/lessons/assets/vc2026-course/L2-02-stack-icl.webp`（2200×1958，WebP q86）
- 渲染通道：CDP（`scripts/drawio-cdp-shot.py`），viewer JS 以 base64 `data:` 内联

---

## 图上每个数字的来源与证据等级

| 图上的数字 | 值 | 来源 | 等级 |
|---|---|---|---|
| 统一基因名单上限 `G` | 15,012 | 论文方法节 + `genelist` 文件名 `15000max` | **[P1]** |
| 基因模块 token 数 `n` / token 维 `d` | 100 / 16 | `configs/training/bc_large.yaml` 的 `n_hidden` / `token_dim` | **[S1]** |
| 层数 | 9 | 同上 `n_layers` | **[S1]** |
| 细胞内注意力头数 | 8 | `modules/attention.py` 内硬编码，**不是配置项** | **[S1]** |
| 细胞间注意力头数 | 8 | 配置 `n_heads` | **[S1]** |
| `K = 256`（预训练档） | — | `configs/training/bc_large.yaml` 的 `sample_size: 256` | **[S1]** |
| `K = 512`（后训练档） | — | `configs/finetuning/ft_parsecg.yaml` 的 `sample_size: 512` | **[S1]** |
| `n_test = 179`、`n_base = 333` | — | `inference.py::get_incontext_prediction` 的 `ratio = prompt_ratio + context_ratio`，代入 0.25 + 0.4 | **[S1]**（公式）+ **工程假设**（代入值） |
| 复制 137 / 112 / 162 行 | — | notebook 07 单元一的实测计算 | **工程假设**（逻辑复刻，未跑官方推理） |
| 细胞内 / 细胞间每层元素数 | `B·K·H·n²` / `B·H·K²` | `modules/attention.py::TabularAttentionLayer.forward` 的 reshape 形状 | **[S1]** |
| 19.5× / 156.2× / 9.8× 等倍数 | — | 上两式相除，手算 | **工程假设** |
| 最大 batch 9（`K=256`）/ 4（`K=512`） | — | notebook 07 的 `peak_bytes()`，含权重 + 9 层注意力分数 + 输出侧缓冲 | **工程假设** |
| 830 MB 参数量、2.43 GiB、23.10 GiB | — | 同上 | **工程假设** |
| 2.4×10¹¹ FLOPs 量级 | — | 按 MACs 估算（主导项 `2K²d` 与 `4ndG`） | **工程假设** |
| 217,484,712 / 193,463,912 | — | notebook 07 单元三手算，**与论文表 3 的 2.17 亿 / 1.93 亿一致** | **工程假设**（但已与官方数字对表成功） |

## 三条硬边界

1. **耗时一个数字都没有。** 图上只给 FLOPs 量级，并明写「换算不代填」。把它读成速度承诺是误读。
2. **不是实测。** 未加载权重、未运行推理、未实例化任何张量。显存是全按形状手算，不含 allocator
   碎片与 CUDA context。图上 (b) 面板右下角已显式写出这一点，改图时不要删掉。
3. **两处源码与论文的真实差异已在图上标出**，不要「修正」回去：
   - (c) 面板：决定窗口切分的是 `prompt_ratio + context_ratio`（默认 0.65），
     **不是论文正文说的「提示 25% 固定」**；
   - 正文 §4.2 提到 `query_pos_embedding` 在源码里是 `(n, d)` 而非论文写的 `R^{n·d}`。

## 两套配置不能混用

`K = 256` 与 `K = 512` 分属预训练档与后训练档。图上所有涉及 `K` 的数字（窗口切分、显存、
复制行数）都基于 `K = 512`，柱状图的横轴则**故意扫过多个 `K`** 以显示倍数随 `K` 的单调性。
改写时不要把某个 `K` 下的结论套到另一个上，也不要写成「Stack 的 `K` 是 256」这种把两档压成一句的话。

## 图面规则（重新导出时必须保持）

- 字号只在生成脚本顶部的 `F_*` 常量里定义，最小 12 模型 px。
- 相邻元素垂直间距 ≥ 20 px；柱状图的行距 `BAR_GAP = 22`。
- 柱状图用 **√(MB/320) 压缩**刻度：细胞内/细胞间跨 156 倍，线性刻度会让细胞间柱变成亚像素、
  被读成 0 反而误导。这个选择在图上以文字注明，数值以标签为准。改回线性刻度是**退化**，不要做。
- 校验两步都要过：`validate.py --score` 必须 0 error 0 warning（当前 score 0）；
  渲染后 `Page.captureScreenshot` 前的那次 `<path d>` 抽查应为 0 条含 `C/Q/A/S`。
- 导出按显示宽度 ×1.25 超采样后 LANCZOS 降采样，WebP q86，目标 ≤ 300 KB（当前 295.8 KB）。
