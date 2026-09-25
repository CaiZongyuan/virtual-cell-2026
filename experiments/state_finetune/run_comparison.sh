#!/usr/bin/env bash
set -euo pipefail
run_dir=${1:?run directory required}
data_dir=${2:?data directory required}
uv_bin="$run_dir/bin/uv"
python_bin="$run_dir/.venv/bin/python"
for source_name in gwps hepg2 rpe1 k562; do
  while [[ ! -f "$run_dir/prepared/$source_name/manifest.json" ]]; do sleep 10; done
done
while [[ ! -f "$run_dir/runs/pilot/complete.json" ]]; do sleep 10; done
"$uv_bin" run --no-project --python "$python_bin" "$run_dir/experiment/train.py" \
  --work "$run_dir" --root "$data_dir" --phase warmup --steps 500 --sets 4 --validate-every 100
for phase_name in frozen unfrozen; do
  "$uv_bin" run --no-project --python "$python_bin" "$run_dir/experiment/train.py" \
    --work "$run_dir" --root "$data_dir" --phase "$phase_name" --steps 1500 --sets 4 \
    --validate-every 250 --initial "$run_dir/runs/warmup/best.pt"
done
