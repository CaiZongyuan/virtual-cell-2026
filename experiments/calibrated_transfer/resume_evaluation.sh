#!/usr/bin/env bash
# Resume the same immutable predictions through the unchanged H1 evaluator.
set -euo pipefail
previous=${1:?previous directory}
work=${2:?campaign directory}
export PYTHONPATH="$work/code/experiments/calibrated_transfer:$work/code/experiments/state_finetune"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
test -f "$work/audit/cache-probe-green.log"
available=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
test "$available" -gt 21000000
mkdir -p "$work/status-resumed"
pids=()
for arm in empirical frozen limited; do
    (
        set +e
        /usr/bin/time -v timeout 5400 "$previous/.eval-venv/bin/python" \
            "$work/code/experiments/calibrated_transfer/score_cached_inputs.py" score \
            "$work/predictions/$arm.h5ad" --data-dir "$previous/h1-benchmark" \
            --gene-chunk 512 --de-threads 8 --output "$work/evaluation/$arm" \
            > "$work/logs/$arm-resumed.log" 2>&1
        status=$?
        "$previous/.venv/bin/python" -c 'import json,sys,time; print(json.dumps({"attempt":sys.argv[1],"exit_code":int(sys.argv[2]),"finished_at_unix":time.time(),"evaluation_resumed":True,"training_repeated":False,"log":"logs/"+sys.argv[1]+"-resumed.log"}))' "$arm" "$status" > "$work/status-resumed/$arm.json"
    ) &
    pids+=("$!")
done
for pid in "${pids[@]}"; do wait "$pid"; done
for arm in empirical frozen limited; do cat "$work/status-resumed/$arm.json" >> "$work/attempts.jsonl"; done
"$previous/.venv/bin/python" "$work/code/experiments/calibrated_transfer/summarize.py" "$work"
