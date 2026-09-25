#!/usr/bin/env bash
set -euo pipefail
run_dir=${1:?run directory required}
data_dir=${2:?data directory required}
prediction="$data_dir/predictions/abc-unfrozen-seed42.h5ad"
while [[ ! -f "$data_dir/predictions/abc-unfrozen-seed42.manifest.json" ]]; do sleep 10; done
"$run_dir/bin/uv" run --no-project --python "$run_dir/.submit-venv/bin/python" \
  "$run_dir/experiment/patch_vcc_memory.py" --audit "$run_dir/audit"
/usr/bin/time -v -o "$run_dir/audit/prep-resources.txt" \
  "$run_dir/bin/uv" run --no-project --python "$run_dir/.submit-venv/bin/python" \
  vcc --json prep "$prediction" \
  --genes "$run_dir/controls/gene_names.csv" --perts "$run_dir/controls/pert_counts.csv" \
  --contexts A,B,C --output "$data_dir/predictions/state-ft-20260925.vcc" \
  > "$run_dir/audit/submission-prep.json"
