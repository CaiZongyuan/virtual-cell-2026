# Orion 分块元数据读取试点（2026-09-26）

当前可靠性实验的官方靶点监督依然全部来自 K562。因此复用已有 Orion
数据清单，核查额外背景 HCT116/HEK293T 的取数可行性；不改变已冻结的三个
候选，不读取 H1/Jurkat 或官方隐藏扰动结果。

## 来源与范围

作者 [Hugging Face 数据卡](https://huggingface.co/datasets/Xaira-Therapeutics/X-Atlas-Orion)
固定 revision `53a5bc98d49247bcf967500292575c3d3602de31`，关联
[预印本 DOI](https://doi.org/10.1101/2025.06.11.659105)、
[作者 Figshare](https://doi.org/10.25452/figshare.plus.29190726)。
数据卡仍声明 CC BY-NC-SA 4.0，本次没有发现新的竞赛使用授权；本次仅做
公开标签/元数据审计，未用 Orion 训练或提交。已有许可适用性缺口仍保留。

文件树包含 HCT116 的 109 个 Parquet 和 HEK293T 的 223 个 Parquet。
只读取各自 `Batch1` 的 `gene_target`、`guide_target`、`sample`、
`pass_guide_filter` 四列和页脚，不读取 `gene_expression` 或基因 token 列。
每个 HTTP 读取最多 2 MB、每文件累计最多 10 MB，逐次验证服务端精确响应
Range；使用临时隔离的 PyArrow 21.0.0，没有修改训练或评价环境。

## 实测标签与取数成本

| 项目 | HCT116 Batch1 | HEK293T Batch1 |
|---|---:|---:|
| 原文件 bytes | 327,620,255 | 370,263,016 |
| 细胞数 | 18,549 | 22,731 |
| Parquet row groups | 1 | 1 |
| 4 列/页脚实际读取 bytes | 337,673 | 367,238 |
| HTTP Range 请求 | 6 | 6 |
| 当前官方靶点对应的细胞 | 270 | 296 |
| 当前官方靶点的不同标签 | 168 | 160 |
| 非靶向 guide 文本对应细胞 | 891 | 1,079 |

两个批次的非靶向 guide 都明确对应 `gene_target="Non-Targeting"`，不是
此前 scPerturb 使用的小写 `non-targeting`。`sample` 分别恒为对应文件的
批次名，`pass_guide_filter` 在这两个示例中均为整数 1。以上仅限已读的两个
批次，不外推全部文件的质量或计数合同。

每个批次只有一个 row group，且含上万个不同靶点标签。这意味着按靶点筛行
可以减少落盘，但通常不能跳过这两个文件的主体计数列下载。未来应逐批下载、
筛选、验证、保存所需行后释放临时文件，不能宣称网络只传输命中的细胞。
完整 H5AD 合计约 559.52 GB 仍不适用；Parquet 总体积约 126.26 GB 来自
此前文件树核验，本次未重新下载全部文件验证这个总量。

基因元数据文件共 881,915 bytes、38,606 行，SHA-256
`33900a0dbaeafb84601c7c8ba7c6642c440774fc3f49613dab11cf1f2bf0fdbf`。
符号/token 唯一性、官方基因轴交集和两个批次的实际靶点列表均记录于
[机器可读结果](../../experiments/data_audit/results/2026-09-26/orion-metadata-pilot.json)。
元数据 token 无重复，基因符号有 22 个重复项，与官方输出轴精确匹配 18,106
个符号；重复符号和另外 427 个未匹配符号须在转换前明确处理。元数据中有某
基因不等于已经验证其非零测量；原始计数值、列表轴的一致性、
全批次靶点/对照数量和有效 knockdown 仍需下一步审计。

## 请求台账与解释边界

本次复用已有文献，没有新增论文查询。逻辑 HTTP GET 共 17 次（不计内部重定向）：作者卡与仓库 API 各
1 次，基因元数据 1 次，HCT116 页脚长度/页脚内容初探各 1 次，正式两个批次
各 6 次；均成功。早期页脚初探只用于验证 Range 合同，正式读取器的统计不
包含这两次。重定向的临时签名 URL 未保存或提交。

这份试点解决的是“能否低成本审计标签、如何匹配对照和估算后续下载成本”。
它不证明新的模型增益，不证明全部官方靶点都有足量细胞，也没有解决许可证
在具体竞赛使用方式下的适用性。源码见
[probe_orion_metadata.py](../../experiments/data_audit/probe_orion_metadata.py)。
