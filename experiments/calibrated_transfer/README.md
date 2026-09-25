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

Execution amendment before any candidate: the baseline recheck was stopped after
verifying that the archived baseline's actual control file, benchmark, scale,
configuration, evaluator package files and all result hashes still match. The
interrupted log and status remain in the run audit. `run_parallel.sh` resumes from
that measured baseline, serializes training/export with a GPU lock, and overlaps
CPU scoring. This changes scheduling only; scoring remains 512 genes / 8 threads,
with unchanged data and metrics. Wall times therefore include resource contention
and, where applicable, waiting for the GPU lock. It requires at least 24 GB free
RAM at launch and reserves 50 GB storage headroom.
