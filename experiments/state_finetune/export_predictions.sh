#!/usr/bin/env bash
set -euo pipefail
run_dir=${1:?run directory required}
data_dir=${2:?data directory required}
while [[ ! -f "$run_dir/runs/unfrozen/complete.json" ]]; do sleep 10; done
for phase_name in frozen unfrozen; do
  if [[ -f "$data_dir/predictions/h1-$phase_name-seed42.manifest.json" ]]; then continue; fi
  "$run_dir/bin/uv" run --no-project --python "$run_dir/.venv/bin/python" \
    "$run_dir/experiment/export.py" --work "$run_dir" --root "$data_dir" \
    --checkpoint "$run_dir/runs/$phase_name/best.pt" --panel h1 \
    --output "$data_dir/predictions/h1-$phase_name-seed42.h5ad" --resume
  "$run_dir/bin/uv" run --no-project --python "$run_dir/.eval-venv/bin/python" \
    vcc-h1 validate "$data_dir/predictions/h1-$phase_name-seed42.h5ad" \
    --data-dir "$run_dir/h1-benchmark"
done
"$run_dir/bin/uv" run --no-project --python "$run_dir/.venv/bin/python" \
  "$run_dir/experiment/export.py" --work "$run_dir" --root "$data_dir" \
  --checkpoint "$run_dir/runs/unfrozen/best.pt" --panel abc \
  --output "$data_dir/predictions/abc-unfrozen-seed42.h5ad" --resume
