#!/usr/bin/env bash
# Resume after a verified archived baseline, with one GPU owner at a time.
set -euo pipefail
previous=${1:?previous run directory}
work=${2:?new run directory}
root=${3:?data directory}
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
export PYTHONPATH="$work/code/experiments/calibrated_transfer:$work/code/experiments/state_finetune"
python="$previous/.venv/bin/python"
script="$work/code/experiments/calibrated_transfer/campaign.py"
test -f "$work/audit/baseline-reuse.json"
test -f "$work/effects.npz"
test -f "$work/evaluation/control/scores.csv"
mkdir -p "$work/status"
usage=$(du -sb "$previous" "$work" "$root" | awk '{n+=$1} END {printf "%.0f", n}')
"$python" -c 'import sys; assert int(sys.argv[1]) < 450_000_000_000' "$usage"
available=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
test "$available" -gt 24000000
pids=()
for arm in empirical frozen limited; do
    (
        set +e
        /usr/bin/time -v timeout 14400 bash -s -- "$python" "$script" "$previous" "$work" "$root" "$arm" > "$work/logs/$arm.log" 2>&1 <<'TRIAL'
set -euo pipefail
python=$1 script=$2 previous=$3 work=$4 root=$5 arm=$6
# Training and neural export are serialized; scoring is CPU-only.
(
    flock -x 9
    if [ "$arm" != empirical ]; then
        "$python" "$script" train --previous "$previous" --work "$work" --root "$root" --arm "$arm"
    fi
    "$python" "$script" export --previous "$previous" --work "$work" --root "$root" --arm "$arm"
) 9> "$work/gpu.lock"
score_slot_locked=false
while [ "$score_slot_locked" = false ]; do
    for slot in 0 1; do
        # While training/exports are active, reserve RAM by using only slot 0.
        if [ "$slot" -eq 1 ] && { [ ! -f "$work/predictions/empirical.json" ] || [ ! -f "$work/predictions/frozen.json" ] || [ ! -f "$work/predictions/limited.json" ]; }; then
            continue
        fi
        exec {score_fd}> "$work/score-slot-$slot.lock"
        if flock -n "$score_fd"; then score_slot_locked=true; break; fi
        exec {score_fd}>&-
    done
    if [ "$score_slot_locked" = false ]; then sleep 5; fi
done
"$previous/.eval-venv/bin/vcc-h1" validate "$work/predictions/$arm.h5ad" --data-dir "$previous/h1-benchmark"
"$previous/.eval-venv/bin/python" "$work/code/experiments/calibrated_transfer/score_cached_inputs.py" score \
    "$work/predictions/$arm.h5ad" --data-dir "$previous/h1-benchmark" \
    --gene-chunk 512 --de-threads 8 --output "$work/evaluation/$arm"
TRIAL
        status=$?
        "$python" -c 'import json,sys,time; print(json.dumps({"attempt":sys.argv[1],"exit_code":int(sys.argv[2]),"finished_at_unix":time.time(),"execution":"GPU serialized, at most two resident CPU scores"}))' "$arm" "$status" > "$work/status/$arm.json"
    ) &
    pids+=("$!")
done
for pid in "${pids[@]}"; do wait "$pid"; done
for arm in empirical frozen limited; do cat "$work/status/$arm.json" >> "$work/attempts.jsonl"; done
"$python" "$work/code/experiments/calibrated_transfer/summarize.py" "$work"
