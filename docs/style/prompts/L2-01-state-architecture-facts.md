# L2-01 State（ST）架构图｜事实边界

对应图稿源：`docs/style/sources/L2-01-state-architecture.drawio`
采用版：`docs/lessons/assets/vc2026-course/L2-01-state-architecture.webp`

**性质：架构图不是证据。** 图上每个数字都必须能追到下面这张表；本文件用于防止修图时把「配置读取值」或「手算值」写成「实测值」。

## 逐项来源

依据主源：[STATE 训练与推理源码核验](../../research/state-training-source-audit.md)（2026-09-14，官方源码与作者 Colab 的**静态核验**：未安装依赖、未下载权重、未运行训练）。

| 图上位置 | 图上写的 | 来源 | 等级 |
|---|---|---|---|
| (a) 主干 | 输入/输出 G→768→G，8 层双向集合 Transformer，hidden 768，FFN 3,072，heads 12 / head_dim 64，双向、无 RoPE | 官方 `model=state` 默认配置与 `state_transition.py` forward 路径 | **官方事实**（静态核验） |
| (a) 前馈后的 `Linear G → G//8 → GELU → Linear G//8 → G` | 末端实际调用 `ReLU`，不是 `softplus` | 源码路径；配置里的 `softplus=true` 在该路径未生效 | **官方事实**（易错点，必须按源码不按 YAML 画） |
| (a) 第二处残差 | `predict_residual = true`，把预测加回对照表达 | 官方默认配置 | **官方事实** |
| (a) 标注「G→G/8→G 约占 8,587 万参数；8 层主干约 7,551 万」 | 手算 | 按矩阵形状手算 | **工程假设**（不是实例化实测；特征维度与完整参数量应在初始化时打印确认） |
| (a) 输入口 | 对照细胞集合（NTC），每个细胞一个 token，`cell_set_len = 64`（已发布权重）/ 512（源码默认） | 见下「两套配置」 | **官方事实**（两套值并存，图上取已发布权重） |
| (b) 集合自注意力 | 12 个头，V/K/Q 来自同一批细胞 token，双向、无因果掩码、无 RoPE | 源码 `utils.py` 禁用了 RoPE；`cell_type_onehot` 未进入预测网络 | **官方事实** |
| (c) Energy 距离 | `2·E‖P−Q‖ − E‖P−P′‖ − E‖Q−Q′‖`，标注为「标准形式」 | **标准 Energy 距离定义**，不是对官方实现逐行复刻 | **教科书/文献定义**（本项目未核验官方实现细节） |
| (c) 损失类型 | `loss=energy`、`distributional_loss=energy`，集合级、不要求逐细胞配对 | 官方配置与源码构造点 | **官方事实** |
| 图内 kicker | 结构依据 commit `9bbfe78`；未运行训练、未加载权重 | 核对记录 | **官方事实**（commit 与核验范围） |

## 两套配置不能混用

图 (a) 的维数取自**已发布权重** `ST-HVG-Replogle/zeroshot/jurkat`（8 层 / hidden 328 / set 64 / 输入输出 2,000 / one-hot 2,024），而 `Linear G → 768 → G` 的 768 来自**当前源码默认**（8 层 / hidden 768 / set 512 / 全基因输出）。

- 这两个数字**不是同一个模型**。图 (a) 画的是官方默认的全基因路径（`embed_key=null`、`output_space=all`），并把 `cell_set_len` 注成已发布权重的 64。
- 图注已写明以官方默认为准；引用时必须说明用的是哪一套，不要合并成「State 是 328 宽」或「State 是 64 个细胞」这类无主语句子。
- hidden 328 的官方配置同时有 `12 heads`、`head_dim=64`、`intermediate_size=3072`。**不要为了「能整除」自行改 head 数**，按配置复制父结构。

## 图上没有画的东西

不画 ≠ 不存在，只是这张图不承担这些内容：

- 数据划分、对照匹配、缺测基因 mask、CP10K 与 log1p 尺度（属 [L3-04](../../lessons/L3-04-State微调实战与算力预算.md) 数据处理合同）。
- 训练超参（`lr=1e-4`、Adam 而非 AdamW、`clip=10`、无内置 LR schedule、默认未启用 bf16）。
- 推理写出的是浮点、clip 到 `[0,14]`，**不是原始计数**；计数生成是另加模块。图 (a) 输出口已注明「仍是浮点 log 空间」，避免被读成可直接提交。
- SE（State Embedding）分支完全未画：SE 负责把表达变成紧凑表示，ST 才是扰动预测器，本图只讲 ST。

## 重新渲染

本机无 draw.io CLI，按 `docs/style/README.md`「drawio-skill 使用约定」走浏览器回退：

1. 改 `.drawio`（它是**生成物**：源脚本 `docs/style/sources/L2-01-state-architecture.gen.py`，字号/间距常量集中在脚本顶部，改完重跑脚本即可）后先跑 `.agents/skills/drawio-skill/scripts/validate.py <file> --score`，必须 0 error 0 warning。
2. 渲染走 CDP 通道：`scripts/drawio-cdp-shot.py <in.drawio> <viewer.js> <out.png> <w> <h> <scale> [port]`。**不要**用 `chrome --screenshot <file://…>`，本机沙箱下 Chrome 只认 `data:` URI，那种写法会静默不写文件。细节见 `docs/style/README.md`「drawio-skill 使用约定」第 1 条。
3. `--dump-dom` 抓 DOM 逐条核对 `<path d>`，应 0 条含 `C/Q/A/S`。
4. 降采样与压缩见 `docs/style/sources/L2-01-state-architecture.finalize.py`（2x 渲染 → 降到 2200 px 宽、裁到内容外接框留 20 模型 px 边距、WebP `quality=86`；当前成品 2200×1942，172 KB）。不要 2x 原样入库。
