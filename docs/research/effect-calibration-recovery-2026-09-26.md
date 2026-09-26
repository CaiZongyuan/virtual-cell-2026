# 本轮接续记录：执行环境限制与恢复（2026-09-26）

**权限已恢复。** 用户恢复 full access 后，SSH 已成功连接；三组新候选均完成评分，自动流程选中 incumbent，并进入第二生成种子复核。未重复训练或重开候选。以下保留限制期间的诊断记录，不代表当前连接状态。

当前训练与官方提交授权仍有效。最新执行环境切换为受限网络、仓库 `.git`
只读后，正常 SSH 调用返回 `Control socket ... Operation not permitted` 和
`socket: Operation not permitted`。没有请求越过沙箱，也没有改用旁路连接。
当前无法核验服务器实时状态，以下均为断连前已确认事实。

## 已验证工作

- 当前分支 `autoresearch/20260926-effect-calibration`，最后已提交修订 `2820de6`。
- 固定 H1 对照分 −0.045231；上一轮经验迁移 0.163874。
- 本轮保守强度 0.2：完整分数 0.080502、原始归一化 MSE 1.018687，退出码 0，
  预测与评分文件哈希已验证；没有达到新候选接受门槛。
- 加法迁移强度按来源背景排除校准选为 0.5；600 个条件、201 个靶点，
  来源均值误差代理比为 0.727812。
- State 残差训练完成 6,000 步及完整 H1 导出；来源开发细胞损失 0.152172，
  零修正为 0.171487。两者不是 H1 分数。
- 最后观察到 `mean_shift` 和 `state_residual` 仍在评分；其最新成绩、选模、
  第二生成种子与官方打包状态现在均待远程核验。
- 实时账户曾通过 `get_me`/`get_limits` 检查：可提交、没有 blockers、未达日限。
  真正上传前仍需重新查询。本轮尚未发起官方上传。
- 上次已发布官方条目为 `2TvmhHnxpkc8hhjCSWcG`，归档分数
  −0.992407445228847。恢复后可只读刷新其状态，并保留 panel/anchor 版本，
  避免把不同评分参照下的结果直接相减。

机器可读状态见 [campaign-status.json](../../experiments/effect_calibration/results/2026-09-26/campaign-status.json)。
本地校验仅能复核已经取回的成品，不能代替新的服务器检查。

## 恢复连接后的顺序

1. 检查现有 tmux、进程、`status/*.json`、`selection.json`、`release.json`、
   `finish-local.exit` 和错误记录；先检查再启动，复用已完成预测和评分缓存。
2. 已启动的 `vcc-cal-finish` 控制器按协议等待三组评分，选模，完成一次
   seed 43 计数生成复核，再执行 A/B/C 导出及原生预检/打包。该控制器没有
   凭证，并在准备好文件后结束。不要盲目重复训练、选模或确认。
3. 严格按 [本轮协议](../../experiments/effect_calibration/README.md) 核验门槛、
   实际文件哈希和预检结果。若已有失败，保留原状态并仅作记录清楚的针对性修复。
4. 验证完成后，用 `official_submission.py` 执行已授权的一次官方提交，
   凭证通过 stdin 传入，公开名称随机生成。已有 entry ID 时只轮询或恢复该条目。
   私有 pending upload 记录包含有权限的 URL，不得取回 Git。
5. 获取并核验真实官方分数，保存公开名、内部配置、数据/模型/预测哈希及版本映射。
   重新盘点全部项目目录、临时文件和缓存，确保总量低于 500 GB。

服务器运行目录为 `~/vcc2026-effect-calibration-20260926`；旧环境/benchmark
为 `~/vcc2026-run`，上一轮为 `~/vcc2026-calibrated-20260925`。当前环境中的旧
本地工具会话和网络转发进程已不可见，不能据此判断其他执行环境的进程状态；
恢复时先检查连接，再按需重建本任务的临时转发。

## 新数据与待保存文件

Jiang TGFB RDS 已下载且校验成功：2,642,041,433 bytes，MD5
`8e9b4d39a95ec5881a30be6a2df541d1`。独立 R 4.5.3 / Matrix 1.7.6 /
jsonlite 2.0.0 运行时及小型读取检查已完成。完整对象的 RNA 计数、基因覆盖及
line/stimulus/batch/target/NTC 映射还未审计；等评分/打包释放内存后再执行
[读取脚本](../../experiments/data_audit/audit_jiang_rds.R)。不要使用会全量解压并多次复制
大数组的 Python rdata 路径。[源码和前缀依据](rds-count-audit-readiness-2026-09-26.md)。

当前 `.git` 只读，新的数据审计脚本、说明、状态与评分版本字段保留修正只能先
保存为工作区改动。恢复 Git 写入后，重新检查所有文件大小、密钥和暂存快照，再提交。
