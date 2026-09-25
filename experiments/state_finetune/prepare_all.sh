#!/usr/bin/env bash
set -euo pipefail
run_dir=${1:?run directory required}
data_dir=${2:?data directory required}
for source_name in gwps hepg2 rpe1 k562; do
  while [[ ! -f "$data_dir/raw/$source_name.h5ad.receipt.json" ]]; do
    sleep 10
  done
  "$run_dir/bin/uv" run --no-project --python "$run_dir/.venv/bin/python" \
    "$run_dir/experiment/data.py" prepare --work "$run_dir" --root "$data_dir" --source "$source_name"
done
