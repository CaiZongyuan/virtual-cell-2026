#!/usr/bin/env bash
# Fresh-workspace entry point after copying both experiment source directories.
set -euo pipefail
previous=${1:?previous run directory}
work=${2:?new run directory}
root=${3:?data directory}
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
export PYTHONPATH="$work/code/experiments/calibrated_transfer:$work/code/experiments/state_finetune"
code="$work/code/experiments/calibrated_transfer"
test ! -e "$work/attempts.jsonl"
test ! -e "$work/runs"
test ! -e "$work/predictions"
mkdir -p "$work/logs" "$work/audit"
usage=$(du -sb "$previous" "$work" "$root" | awk '{n+=$1} END {printf "%.0f", n}')
"$previous/.venv/bin/python" -c 'import sys; assert int(sys.argv[1]) < 450_000_000_000' "$usage"
timeout 600 "$previous/.eval-venv/bin/python" "$code/reuse_baseline.py" --previous "$previous" --work "$work" > "$work/logs/control.log" 2>&1
timeout 1800 "$previous/.venv/bin/python" "$code/campaign.py" prepare --previous "$previous" --work "$work" --root "$root" > "$work/logs/prepare.log" 2>&1
bash "$code/run_parallel.sh" "$previous" "$work" "$root"
