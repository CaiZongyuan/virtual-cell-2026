# Jiang TGFB 数据试点（2026-09-26）

目的：核查额外细胞背景与测量基因覆盖，补足下一轮数据准备。当前
`effect_calibration` 的训练、预测和评分输入已经冻结，本文件不是新候选评分。

来源复用[前次一手核验](autonomous-finetuning-data-review-2026-09-25.md)：
Jiang et al.，正式版 DOI <https://doi.org/10.1038/s41556-025-01622-z>，
作者数据记录 <https://zenodo.org/records/14518762>，CC BY 4.0。

| 固定资产 | 值 |
|---|---|
| 文件 | `Seurat_object_TGFB_Perturb_seq.rds` |
| 下载 | <https://zenodo.org/api/records/14518762/files/Seurat_object_TGFB_Perturb_seq.rds/content> |
| 字节数 | 2,642,041,433 |
| MD5 | `8e9b4d39a95ec5881a30be6a2df541d1` |
| 服务器目标 | `/mnt/e/vcc2026-data/raw/jiang_tgfb.rds` |

下载复用已有断点续传与校验实现，设一小时保护，操作前保留至少 50 GB
项目存储余量。只把小型收据、来源及审计结果提交 Git。

需核查 Seurat 的原始 RNA counts、基因轴、靶点、guide、细胞系、刺激和
技术批次。刺激（stimulus）指外加的信号条件；相同基因在不同条件下的影响
可能不同，必须保留同一细胞系、刺激及批次的非靶向对照。不能把 `data` 或
`scale.data` 当作原始计数，也不能把文件体积推断为可用细胞数或基因数。

当前状态：下载完成且退出码 0；文件大小和 MD5 均通过校验。独立 R 4.5.3、Matrix 1.7.6、jsonlite 2.0.0 环境已建立，读槽、稀疏轴、空细胞与小数拒绝的小型检查已通过。完整对象的实际基因/靶点覆盖仍待核验。
读取大型 R 对象须等本轮本地评分/打包释放内存；不与两个评分器争用内存。

读法与内存依据见 [RDS 审计说明](rds-count-audit-readiness-2026-09-26.md)。SSH 权限已恢复；完整远程审计须等本轮评分/打包释放内存后执行。
