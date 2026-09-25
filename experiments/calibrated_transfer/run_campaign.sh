#!/usr/bin/env bash
set -euo pipefail
previous=${1:?previous run directory}
work=${2:?new run directory}
root=${3:?data directory}
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
export PYTHONPATH="$work/code/experiments/calibrated_transfer:$work/code/experiments/state_finetune"
script="$work/code/experiments/calibrated_transfer/campaign.py"
python="$previous/.venv/bin/python"
mkdir -p "$work/logs" "$work/evaluation"

storage_guard() {
    local usage
    usage=$(du -sb "$previous" "$work" "$root" | awk '{n+=$1} END {printf "%.0f", n}')
    "$python" -c 'import json,sys; print(json.dumps({"project_storage_bytes":int(sys.argv[1])})); assert int(sys.argv[1]) < 500_000_000_000' "$usage"
}

storage_guard
timeout 1800 "$python" "$script" prepare --previous "$previous" --work "$work" --root "$root" > "$work/logs/prepare.log" 2>&1
# The baseline has its own fresh output, with the unchanged upstream evaluator.
set +e
/usr/bin/time -v timeout 3600 "$previous/.eval-venv/bin/python" \
    "$work/code/experiments/state_finetune/score_cached_controls.py" score-control-baseline \
    --data-dir "$previous/h1-benchmark" --gene-chunk 512 --de-threads 8 \
    --output "$work/evaluation/control" > "$work/logs/control.log" 2>&1
status=$?
set -e
"$python" -c 'import json,sys,time; print(json.dumps({"attempt":"control","exit_code":int(sys.argv[1]),"finished_at_unix":time.time()}))' "$status" >> "$work/attempts.jsonl"
test "$status" -eq 0

for arm in empirical frozen limited; do
    storage_guard
    set +e
    /usr/bin/time -v timeout 3600 bash -s -- "$python" "$script" "$previous" "$work" "$root" "$arm" > "$work/logs/$arm.log" 2>&1 <<'TRIAL'
set -euo pipefail
python=$1 script=$2 previous=$3 work=$4 root=$5 arm=$6
if [ "$arm" != empirical ]; then
    "$python" "$script" train --previous "$previous" --work "$work" --root "$root" --arm "$arm"
fi
"$python" "$script" export --previous "$previous" --work "$work" --root "$root" --arm "$arm"
"$previous/.eval-venv/bin/vcc-h1" validate "$work/predictions/$arm.h5ad" --data-dir "$previous/h1-benchmark"
"$previous/.eval-venv/bin/python" "$work/code/experiments/state_finetune/score_cached_controls.py" score \
    "$work/predictions/$arm.h5ad" --data-dir "$previous/h1-benchmark" \
    --gene-chunk 512 --de-threads 8 --output "$work/evaluation/$arm"
TRIAL
    status=$?
    set -e
    "$python" -c 'import json,sys,time; print(json.dumps({"attempt":sys.argv[1],"exit_code":int(sys.argv[2]),"finished_at_unix":time.time()}))' "$arm" "$status" >> "$work/attempts.jsonl"
done
storage_guard
