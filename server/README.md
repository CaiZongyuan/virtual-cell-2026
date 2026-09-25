# State 实验服务器操作手册

适用于 2026-09-25 已配置的局域网 Ubuntu / WSL2 服务器。首轮实验已经完成；日常操作先查看状态和已有结果。模型效果与后续实验门槛见 [首轮复盘](../docs/research/state-first-run-postmortem-2026-09-25.md)，实验接口见 [运行说明](../experiments/state_finetune/README.md)。

## 1. 连接与目录

在本地仓库根目录 `.env` 配置 `VCC_SSH_HOST=用户名@服务器局域网IP`。密码由 SSH 交互输入；密码、私钥和 `VCC_TOKEN` 都不写入文档、命令参数、日志或 Git。`.env.example` 只保留空值。

本地执行：

```bash
source .env
ssh "${VCC_SSH_HOST:?请先配置 SSH 主机}"
```

连接后，远程 shell 中设置本次操作的路径：

```bash
run_dir="$HOME/vcc2026-run"
data_dir=/mnt/e/vcc2026-data
cd "$run_dir"
```

| 位置 | 用途 |
|---|---|
| `~/vcc2026-run/experiment/` | 本仓库 `experiments/state_finetune/` 的运行副本 |
| `bin/uv`、`.venv/` | uv 与训练、预测、SwanLab 环境，Python 3.12 |
| `.eval-venv/` | H1 benchmark 与 `cell-eval2`，和训练环境隔离 |
| `.submit-venv/` | `vcc-cli==0.1.0`，含有记录的内存优化补丁 |
| `protocol.json`、`prepared/` | 固定基因轴、靶点、数据划分与准备好的稀疏训练数据 |
| `controls/`、`h1-benchmark/` | 官方 A/B/C 对照与 H1 benchmark 资产 |
| `upstream/` | 固定版本的 State 等上游代码 |
| `runs/` | pilot、warmup、frozen、unfrozen 的权重、指标和迁移记录 |
| `swanlog/`、`logs/`、`audit/` | 看板数据库、进程输出与核验记录 |
| `evaluation/` | H1 对照、冻结组、解冻组评分 |
| `/mnt/e/vcc2026-data/assets/`、`raw/` | 父权重、ESM2 特征、原始数据 |
| `/mnt/e/vcc2026-data/predictions/` | H1/A/B/C 预测、manifest 与首轮 `.vcc` |

硬件为 RTX 3090 24 GB、约 31 GiB 主机内存。`/mnt/e/` 是大文件数据盘；不要把多 GB 预测、模型和数据复制进 Git。目录表中的相对路径以 `~/vcc2026-run/` 为根。

## 2. 共享机器资源

在远程启动计算前检查：

```bash
/usr/lib/wsl/lib/nvidia-smi
free -h
uptime
df -h "$run_dir" "$data_dir"
tmux list-sessions
ps -u "$USER" -o pid,pcpu,pmem,args --sort=-pcpu
```

WSL 的非交互 SSH 中 `nvidia-smi` 可能不在 PATH，使用上面的绝对路径。只使用空闲资源；不能从显存剩余量推断 GPU 无人使用，同时检查利用率和进程。CPU 小诊断可用 `nice -n 10`，把 `OMP_NUM_THREADS`、`OPENBLAS_NUM_THREADS`、`MKL_NUM_THREADS` 限为 1。停止任务时只定位本实验的 PID 或 tmux 会话，不使用 `killall python`、`pkill -f python` 或 GPU reset。

首轮实测：训练主机峰值约 8.9 GiB；打包峰值约 17.5 GiB。打包占用很大，应单独运行。这些是旧配置记录，不是下一次任务的资源保证。

## 3. uv 与环境

本地及服务器的 `~/.config/uv/uv.toml` 已配置：

```toml
[[index]]
url = "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple"
default = true
```

使用已建环境运行，不混用系统 Python：

```bash
"$run_dir/bin/uv" run --no-project --python "$run_dir/.venv/bin/python" -- python --version
"$run_dir/bin/uv" pip freeze --python "$run_dir/.venv/bin/python"
"$run_dir/.eval-venv/bin/vcc-h1" --help
"$run_dir/.submit-venv/bin/vcc" --help
```

重建训练环境时，先在**新目录**创建 Python 3.12 虚拟环境，再安装 `torch==2.7.1` 的 cu126 官方 wheel 和 [requirements.txt](../experiments/state_finetune/requirements.txt)。CUDA torch 来自 `https://download.pytorch.org/whl/cu126`，其余包使用 uv 的清华默认源。完整环境版本在 `audit/*environment.txt`；不要对保存首轮结果的环境直接执行批量升级。

## 4. 实时 SwanLab 网页

服务器已有 `vcc2026-dashboard` tmux 会话，监听远程 `127.0.0.1:16906`。本地网页入口：**http://127.0.0.1:16006**。

本地转发断开后，在本地独立终端执行并保持运行：

```bash
source .env
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
  -L 16006:127.0.0.1:16906 "$VCC_SSH_HOST"
```

若提示本地 16006 已占用，先检查现有转发和网页是否可用；需要另开入口时用 16007 并访问对应地址。SSH 断开只会关闭转发，tmux 内的看板继续运行。

查看远程服务输出：

```bash
tmux capture-pane -pt vcc2026-dashboard -S -40
curl -I http://127.0.0.1:16906/
```

仅在该看板会话不存在、16906 空闲时重启：

```bash
tmux new-session -d -s vcc2026-dashboard \
  "$run_dir/bin/uv run --no-project --python $run_dir/.venv/bin/python $run_dir/experiment/dashboard.py --logdir $run_dir/swanlog --host 127.0.0.1 --port 16906"
```

通过 `tmux attach -t vcc2026-dashboard` 进入，按 `Ctrl-b` 后按 `d` 离开并保持服务。首条实验日志写入前，包装脚本会等待数据库。错误 **3500** 的已知原因是直接提前启动 `swanlab watch` 后数据库 Proxy 未初始化；使用 `dashboard.py` 等待日志，并保持固定端口。访问网页成功还不等于数据库正常，应确认实验列表和曲线实际出现。

## 5. 查看结果与小规模诊断

```bash
cat "$run_dir/runs/unfrozen/complete.json"
tail -n 5 "$run_dir/runs/unfrozen/metrics.jsonl"
cat "$run_dir/evaluation/unfrozen-seed42/scores.csv"
```

H1 综合分数读取 `scores.csv` 的 `from_replicate` 列，不能读空的 `from_baseline`。SwanLab 的训练损失下降不能替代 H1 评分；官方和 H1 的评分参考点不同，不能互相换算。

同步最新实验脚本时，在**本地**执行；仅同步代码，不带数据或删除远程文件：

```bash
source .env
rsync -av --exclude '__pycache__' --exclude '.pytest_cache' \
  experiments/state_finetune/ "$VCC_SSH_HOST:~/vcc2026-run/experiment/"
```

记录运行使用的 Git commit；进行新实验时使用独立代码快照和新的运行目录，以便复核旧结果。下面是只读诊断，读取旧预测和 checkpoint、写一份新的摘要，不训练或提交：

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  nice -n 10 "$run_dir/bin/uv" run --no-project --python "$run_dir/.venv/bin/python" \
  "$run_dir/experiment/diagnose_first_run.py" \
  --work "$run_dir" --root "$data_dir" \
  --output "$run_dir/audit/postmortem-diagnostics.json" --probe-ntc
```

诊断抽取每背景前 3 个靶点的已保存预测，并可对 64 个对照细胞做 CPU FP32 的无扰动探针；它不是全量重新评分，也不是 GPU bf16 导出的逐位复现。

## 6. 新训练、导出与离线评价

首轮方案表现显著差于对照基线。新训练先遵循复盘中的校准门槛，使用新的 `--work`，保留原 `runs/`、`evaluation/` 和预测文件。`train.py` 的阶段名限定为 pilot / warmup / frozen / unfrozen，重复使用旧目录会覆盖 checkpoint；它也不提供完整优化器断点续训，`--initial` 只是加载模型权重。

训练所需工作目录包含 `protocol.json`、`prepared/`、`upstream/state/`。可复用只读数据链接，但新实验的协议变更必须另存。示例在已准备好的新目录上运行：

```bash
next_run="$HOME/vcc2026-run-next"  # 先准备独立协议和数据链接
"$run_dir/bin/uv" run --no-project --python "$run_dir/.venv/bin/python" \
  "$run_dir/experiment/train.py" --work "$next_run" --root "$data_dir" \
  --phase warmup --steps 500 --sets 4 --validate-every 100
```

旧版 `prepare_all.sh` 等待原始下载 receipt；`run_comparison.sh` 还等待 pilot 完成，随后重做 warmup 和两组训练。它们是首轮编排脚本，不能当作任意目录上的恢复按钮。

`export.py` 接受 `--panel h1|abc`、`--checkpoint`、`--output`；新模型使用新文件名。只有相同 checkpoint SHA、seed、协议和行标签才能用 `--resume` 恢复同一预测。H1 示例：

```bash
prediction="$data_dir/predictions/h1-next-seed42.h5ad"
"$run_dir/bin/uv" run --no-project --python "$run_dir/.venv/bin/python" \
  "$run_dir/experiment/export.py" --work "$next_run" --root "$data_dir" \
  --checkpoint "$next_run/runs/unfrozen/best.pt" --panel h1 --output "$prediction"
"$run_dir/.eval-venv/bin/vcc-h1" validate "$prediction" --data-dir "$run_dir/h1-benchmark"
"$run_dir/.eval-venv/bin/vcc-h1" score "$prediction" \
  --data-dir "$run_dir/h1-benchmark" --output "$next_run/evaluation/unfrozen" \
  --gene-chunk 256 --de-threads 1
```

导出还需要新工作目录中的 `h1-benchmark/` 或 `controls/`。以新的输出目录隔离评分缓存；线程数根据当前空闲资源调整。完整评价比较 NTC、候选模型和必要消融，既看六项缩放分数也看原始 MSE/NMAE。

## 7. 打包、提交与成绩查询

`prep_submission.sh` 是首轮固定文件名脚本；`patch_vcc_memory.py` 只适配已核验的 `vcc-cli==0.1.0` 源码版本。新预测先指定新的输入、输出和预检记录路径，再打包。不能拿旧 `audit/submission-prep.json` 为新文件背书。补丁保留整数、总计数和字段检查；记录位于 `audit/vcc-memory-patch*.json`。

`submit.py` 会向外上传，接收标准输入的一行 JSON 凭证（`token` 和可选 `https_proxy`），不接收命令行 Token。读取本地 `.env` 后由调用进程在内存构造 stdin；不要手工把 Token 拼进 shell 命令或 heredoc。提交前完成全量预检，并按当前任务授权执行；这份操作文档不自动发起新提交。

首轮 entry ID：`2TvmhHnxpkc8hhjCSWcG`，已发布，综合分 `−0.992407445228847`。只读查分命令（使用已经配置好的凭证 profile 或进程级 `VCC_TOKEN`）：

```bash
"$run_dir/.submit-venv/bin/vcc" --json status 2TvmhHnxpkc8hhjCSWcG
```

## 8. 网络与排障

首轮环境中远程直连外网 TLS 曾超时，下载与提交通过任务专用的临时 HTTP CONNECT 代理完成。代理、SSH 控制 socket 和反向转发都不是持久服务；重连后先检查连通性，不假定旧端口仍存在。

如确实需要代理，只对下载/提交的子进程设置 `HTTPS_PROXY`、`HTTP_PROXY`；SSH 可用 `-R 远程端口:127.0.0.1:本地代理端口` 转发已有代理。uv 的 PyPI 镜像不解决所有 Hugging Face、Zenodo 或竞赛 API 的网络问题。不要修改整机代理，也不要把代理凭证写进日志。任务结束仅关闭自己建立的代理和隧道，保留正在使用的 SwanLab 服务。

遇到内存退出，先检查 `audit/prep-resources*.txt` 和实际空闲内存；遇到训练卡住，先区分脚本等待 receipt/complete 文件与真正的计算停滞。不要自动重跑整条流水线。
