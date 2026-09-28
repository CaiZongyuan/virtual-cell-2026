# Calibrated transfer campaign, 2026-09-25

Bounded campaign: one canonical H1 control baseline and at most three candidates.
Starting repository revision: `3af3962`. Official submissions remain paused.

The first State run failed background calibration. This campaign tests an explicit
differential prediction `f(NTC, target) - f(NTC, non-targeting)` with the existing
adapted State architecture, starting from the archived `unfrozen/best.pt` descendant
of the published State checkpoint. This is continued fine-tuning of public weights,
not a reproduction of native State preprocessing. The parent's exact preprocessing
and pretraining exposure remain incompletely verified; no strict zero-shot claim.

## Frozen contract

- Development: unchanged H1 benchmark v0.2.0 at
  `d28dd0496cc9fbf1d0088ce171208c0deb54a268`, 126 × 400 cells, 18,080 genes.
  `cell-eval2==0.16.0`, `pdex==0.3.0`; all six scaled metrics, `from_replicate`.
- Reuse baseline only after checking its manifests, evaluator hashes and output
  hashes against the current environment. Candidates use the exact canonical
  control row sampling, gene axis, reference, and scale. No evaluator edits.
- Training: existing prepared GWPS/K562/RPE1/HepG2 **training** cell split only.
  Batch-matched controls; CP10000 within each measured panel; pseudocount 0.1.
  H1 and Jurkat perturbation labels never enter training or checkpoint selection.
- Confirmation: all Jurkat perturbations remain outside tuning. After selecting
  one H1 candidate, evaluate it once on eligible Jurkat targets, using matched
  NTC inputs. Report a separate mean-effect metric, not a canonical H1 score.
- C1: empirical log fold changes, average K562's two datasets within context
  before equal context averaging. This is a statistical reference, not a pretrained
  model. Per-gene availability masks prevent missing measurements becoming zeros.
- C2: differential State, backbone frozen; C3: same initialization and batches,
  last two Transformer layers also trainable. 1,000 steps each, two 64-cell sets,
  AdamW interface lr 1e-4 / backbone lr 1e-5, clip norm 10, seed 42, BF16 forward.
  Final fixed-step checkpoint used; source development loss is diagnostic only.
- Each candidate uses the same fixed 0.5 effect shrinkage and natural-log effect
  cap ±log(4). These are declared engineering hypotheses, not optimized on H1.
  Count decoding thins decreases binomially and adds Poisson counts for increases.
  Zero effect is exactly identity; unsupervised genes retain exact raw counts.
  This preserves raw counts, not normalized proportions or per-cell library size.
- Primary: H1 average scaled score (maximize). Provisional acceptance requires
  +0.01 over control and raw MSE/NMAE each <2× control. Prefer the highest score
  passing these gates; do not claim significance from a single seed.
- Each candidate has a 60-minute end-to-end timeout; setup/downloads 30 minutes.
  Total campaign limited to baseline + three candidates including failed attempts.
  RTX 3090, 31 GiB RAM; exclusive experiment GPU use after checking availability.
  Project storage including existing assets must remain below 500,000,000,000 bytes.

## Execution

Run files from this directory alongside a read-only snapshot of
`experiments/state_finetune`. Set `PYTHONPATH` to both directories.

```bash
python campaign.py prepare --previous /path/to/vcc2026-run --work /path/to/new-run
python campaign.py train --previous /path/to/vcc2026-run --work /path/to/new-run \
  --root /mnt/e/vcc2026-data --arm frozen
python campaign.py export --previous /path/to/vcc2026-run --work /path/to/new-run \
  --root /mnt/e/vcc2026-data --arm empirical
vcc-h1 score /path/to/new-run/predictions/empirical.h5ad \
  --data-dir /path/to/vcc2026-run/h1-benchmark \
  --gene-chunk 512 --de-threads 8 --output /path/to/new-run/evaluation/empirical
```

Repeat train/export for `limited`; export `frozen` after its training finishes.
Large arrays, weights, logs and predictions stay outside Git. Results summaries,
all attempt outcomes, exact commands, code hashes, timings and data receipts are
copied into the repository only after completion. Training logs use local SwanLab.

For the next fresh campaign, copy both source directories into
`$work/code/experiments/`, record the source Git revision, then run
`bash run_campaign.sh "$previous" "$work" "$root"`. The final runner validates
and reuses the archived baseline, serializes GPU work, uses one resident CPU
scorer while training is active and at most two after all exports finish.
Observed evaluation costs exceeded the initial guard estimates: the final runner
therefore allows four hours per complete candidate (including lock waits), and
the evaluation-only resume helper allows three hours. The scientific training
budget remains 1,000 updates per State arm. Earlier guard values below describe
this campaign's actual execution history, not the current recommended launcher.

Execution amendment before any candidate: the baseline recheck was stopped after
verifying that the archived baseline's actual control file, benchmark, scale,
configuration, evaluator package files and all result hashes still match. The
interrupted log and status remain in the run audit. `run_parallel.sh` resumes from
that measured baseline, serializes training/export with a GPU lock, and overlaps
CPU scoring. This changes scheduling only; scoring remains 512 genes / 8 threads,
with unchanged data and metrics. Wall times therefore include resource contention
and, where applicable, waiting for the GPU lock. It requires at least 24 GB free
RAM at launch and reserves 50 GB storage headroom.

The real 1,024-cell reading probe subsequently found repeated backed reads about
16× slower than resident reads, with identical counts and row order. The
`score_cached_inputs.py` wrapper caches the prediction as well as controls, checks
shuffled/repeated-row parity, and retains every upstream hash/count/axis/metric
check. Each prediction is bounded to 4 GiB of CSR storage. `cache_probe.py` is the
regression probe; the fixture is the first 1,024 cells of an actual prediction.

The first scoring segment is archived as interrupted for this storage fix.
`resume_evaluation.sh` resumes valid upstream DE chunks for the **same prediction
files**, with a separate 90-minute scoring timeout and at least 21 GB available
RAM at launch. This is an execution repair; training remains exactly 1,000 steps
per State arm and no candidate parameters were changed after scoring began.
All interrupted and resumed exit statuses must be retained in the final audit.
Resident scoring is limited to two concurrent processes: the first three-process
run reached about 8 GiB swap during overlapping loads. The limited-unfreeze arm
was deferred and resumed after a slot became available, retaining its audit.

## Completed results and recovery

The reboot recovery completed successfully (exit 0), reusing unchanged predictions
and 20 valid DE chunks for `limited`. No training was repeated. Final H1 scores:

| Arm | Average scaled score | Raw normalized MSE | Raw NMAE |
|---|---:|---:|---:|
| Control | -0.045231 | 1.002242 | 1.005045 |
| Empirical (keep) | **0.163874** | 1.303612 | 0.986160 |
| Frozen State | 0.062497 | 1.446909 | 1.023922 |
| Limited State | 0.056925 | 1.479596 | 1.023833 |

All candidates passed the predetermined acceptance gate; empirical had the highest
score. Its H1 MSE worsened despite the composite improvement. The one-shot Jurkat
confirmation, performed only after freezing the selection, produced a pooled
normalized mean-expression error ratio of **0.575856** against NTC=1, with 148/198
targets improved. This uses 24,865 cells and 8,283 measured project-axis genes; it
is not the canonical six-metric score. The actual confirmation targets overlap
32 public H1 targets and zero current official targets. There was no retuning.

See [results](results/2026-09-25/summary.json),
[confirmation](results/2026-09-25/confirmation/summary.json),
[artifact checks](results/2026-09-25/audit/final-verification.json), and the
[full report](../../docs/research/calibrated-transfer-run-2026-09-26.md).
The H1 result remains provisional with one generation seed. All job processes
have exited. Server project storage is 87.03 GB, below the 500 GB cap; official
submissions remain paused. Do not rerun confirmation in this completed directory.

The reporting utilities can be rerun on the small archived results without model
weights or datasets:

```bash
python experiments/calibrated_transfer/summarize.py experiments/calibrated_transfer/results/2026-09-25
python experiments/calibrated_transfer/compare_targets.py experiments/calibrated_transfer/results/2026-09-25
```

Historical `status-limited-final.json` records exit 124 before recovery. The final
recovery exit is 0; original statuses and interrupted ledgers remain in the audit.
The recovery ledger's original-process-exit placeholder is supplemented by the
original status artifacts in `audit/final-verification.json`.
