# Effect calibration and resumed submissions, 2026-09-26

Starting revision: `c76f9d6`. User authorization: continue improving scores and
start official submissions after sufficient local experimentation. The previous
submission pause is superseded. Public names remain random, with full internal
provenance. No foundation model is pretrained from scratch.

## Fixed experiment contract

- Incumbent: previous empirical transfer, H1 score 0.16387417225775552,
  raw normalized MSE 1.3036115079004935, raw NMAE 0.9861595229404151.
  Reuse only after validating actual predictions, controls, evaluator and outputs.
- H1: unchanged benchmark v0.2.0 / `d28dd0496cc9fbf1d0088ce171208c0deb54a268`,
  126 targets x 400 cells x 18,080 genes; cell-eval2 0.16.0, pdex 0.3.0,
  gene chunk 512, DE threads 8, six `from_replicate` scaled metrics.
- H1 is development data. Its perturbation labels remain confined to evaluation.
  Jurkat has already been used once for confirmation; do not inspect or retune
  against its outcomes in this round. All fitting uses K562/GWPS/RPE1/HepG2.
- Three new candidate slots: conservative multiplicative transfer (fixed strength
  0.2 instead of 0.5); additive mean transfer with strength chosen by source
  context exclusion; the public-pretrained State residual candidate below.
- Source calibration grid: 0, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0.
  Exclude *both* K562 files together when predicting K562. Fit effects from
  other contexts' training cells; score the held context's development cells
  against batch-matched NTC means. Average error ratios equally over the three
  biological contexts. This calibration is an empirical-model procedure, not
  proof that a pretrained State checkpoint never saw those contexts.
- Candidate identity includes effect table hashes, fitting protocol, strength,
  decoder, checkpoint, masks and code revision. H1 control sampling remains
  canonical; decoding seed 42 for selection. A selected candidate gets one
  additional decoding-seed evaluation (43), with canonical controls unchanged.
- Selection: retain a new candidate only if its composite exceeds incumbent by
  at least 0.01, raw MSE does not exceed incumbent MSE, and raw NMAE is at most
  1.1 times incumbent NMAE. Otherwise keep the existing incumbent. Missing,
  non-finite or unsuccessful runs never enter ranking.
- Budget: one verified incumbent, at most three new candidate configurations,
  and one selected-candidate seed confirmation. Up to 4 hours per full candidate,
  3 hours per evaluation-only resume; one targeted infrastructure repair per
  failed stage, preserving every attempt. No additional H1 parameter search.
- Server: RTX 3090, 31 GiB RAM; at most two resident scorers and only one while
  GPU training is active. Require 12 GB available before a scorer; do not allow
  concurrent stages to overcommit memory. All project storage <500,000,000,000
  bytes, including previous runs, temporary files and caches; reserve 50 GB.

## Submission gate

After all candidate slots have completed or have recorded failures/rejections,
freeze the selected configuration. Its two H1 decoding seeds must each exceed
the canonical control composite by 0.05, with raw MSE/NMAE each below twice the
control. The second seed may not fall more than 0.01 below the first. This is a
modest reproducibility check, not a statistical significance claim.

Then generate all A/B/C predictions from their provided controls and the frozen
predictor, run complete `vcc prep` target/count/axis/sparsity checks, validate the
packed artifact, record hashes and provenance, recheck account eligibility and
daily allowance, and submit once with a random `entry-<hex>` name. Respect the
official two-per-day limit; never bypass it. Poll for the official result and
record it separately from H1. No final D/E/F submission in this round.

If the new candidates fail to beat the incumbent but the incumbent passes the
same seed and artifact gates, submit that incumbent. The user has already
authorized this action; local scores alone do not substitute for the gates.

## Scientific hypotheses

The previous H1 gain accompanied worse mean error, motivating lower effect
strength. Its multiplicative count decoder cannot add molecules at zero entries.
The additive candidate instead estimates a change in normalized mean expression:
decreases thin existing molecules; increases add Poisson counts proportional to
the cell's original library size, allowing previously zero genes to be expressed.
Zero effect and unmeasured genes preserve raw counts exactly. Neither decoder
assumes that the source and destination have identical expression backgrounds.

The biological interpretation of raw zero counts is limited: a zero can mean a
gene was not active or its molecules were not sampled. Allowing additions tests
a count-generation model; it is not a claim that every zero should be filled.

Large arrays/checkpoints/predictions stay on the server. Git retains source,
small reports, all trial statuses and reproducible metadata.

## Frozen State residual specification

Continue the same public-State descendant `unfrozen/best.pt` (SHA-256
`d9e17261e9b5ea86d63c52835db22e6a305612906d2e39fbc8f82c133ac25fff`).
Replace its output ReLU with Identity and zero-initialize its single linear head.
Freeze basal/missingness encoders; train the perturbation encoder, signed head
(lr 1e-4), and last two Transformer layers (lr 1e-5). AdamW weight decay 0,
gradient norm cap 10, dropout disabled, BF16 forward and FP32 difference/loss.
Fixed 6,000 updates, seed 42; no early stopping. A two-step integration smoke run
precedes the full run and never contributes a candidate score.

For each of the 600 eligible source-target conditions (201 distinct targets),
training supervision is clipped source log effect minus 0.2 times the clipped
prior from other biological contexts, only on mutually measured genes. Four
anchor targets are drawn without replacement with seed 42 from the 41 targets
present in all four source files. Labels and model predictions both subtract
the same masked anchor mean; the source-specific anchor masks are used in
training, their per-anchor union and the supervised-gene union in inference.
This explicit anchor rule replaces the evidence note's preliminary proposal to
center labels over all eligible targets, making training/inference definitions
consistent. Anchors are frozen before H1 results and independent of test panels.

Each step samples two distinct targets from one source, with source probabilities
1/6 GWPS, 1/6 K562 essential, 1/3 RPE1, 1/3 HepG2. Each target and its anchors
receive the same 64 matched NTC cells; the two targets retain their own matched
batches. Loss = weighted centered-residual MSE + 0.5 times pairwise difference
MSE. Weights use sqrt(source control mean + 0.1), measured masks and per-vector
normalization. The four anchors add forward passes; steps do not imply equal
compute to the previous models.

Inference applies `0.2 * clip(empirical, ±ln4) + 0.1 * clip(residual, ±ln2)`
through the existing multiplicative decoder with decoder strength **1** (no
second shrink). Targets without external supervision retain NTC predictions;
genes without residual supervision receive no residual. An NTC query is exact
identity. The correction weight 0.1 is fixed, not selected with source-context
validation: the initialization already saw all training sources. Source
development-cell diagnostics measure fitting only, and never select a checkpoint.

## Candidate results

Source fitting completed on 600 conditions / 201 targets. Additive strength 0.5
minimized the declared context-balanced mean-error surrogate (ratio 0.727812).
All 619 aggregated logarithmic effect vectors exactly match the incumbent before
applying candidate-specific strength. The four count-decoder checks passed.

| Completed H1 candidate | Composite | Raw MSE | Raw NMAE |
|---|---:|---:|---:|
| Incumbent, strength 0.5 | 0.163874 | 1.303612 | 0.986160 |
| Conservative, strength 0.2 | 0.080502 | 1.018687 | 0.987548 |
| Additive mean shift, strength 0.5 | 0.057952 | 3.575863 | 1.353180 |
| State residual | 0.081697 | 1.024098 | 0.989496 |

Conservative transfer reduced mean error but failed to improve the composite;
it is not selected. All three new candidates have completed scoring and failed
the declared improvement gate. State residual gains only 0.001194 over the
conservative predictor, and the additive candidate worsens H1 mean error despite
its favorable source-context surrogate. The incumbent remains selected; its
second decoding-seed score is now running.
[Source calibration and complete score artifacts](results/2026-09-26/).
Live noncached account/allowance checks passed through the established SSH
forward; no official upload has occurred at this stage.

State completed all 6,000 updates and the full H1 export. Its fixed source
development-cell loss was 0.152172 versus zero-correction 0.171487; these are
diagnostics, not H1 scores. Peak allocated GPU memory was about 1.13 GB.

## Official artifact workflow

`select_candidate.py select` verifies actual prediction hashes, evaluator identity,
score hashes, recorded process exits and generation metadata before freezing a
candidate. After exporting/scoring decoding seed 43,
`select_candidate.py release` checks the predeclared confirmation gate and the
unchanged predictor. A release still requires a complete new ABC artifact.

`prepare_submission.py` first checks that ABC export against the release. It
creates an independent float32 storage copy, verifies every integer value and
every sparse index/pointer against the original, then runs both native
`vcc prep --dry-run` and full prep with all target/count/context checks enabled.
The storage change is exact for the allowed integer range; scored predictions
stay immutable. A fixture comparison through native packing/unpacking verified
identical counts/obs/genes, the 1,000,000-count boundary, and rejection of a
fractional value beyond the first conversion chunk. Native packing runs alone,
with its temporary files under this campaign and measured peak RSS recorded.

`official_submission.py` receives credentials only on stdin, rechecks live
eligibility/allowance, generates one opaque public name, and records the entry ID
immediately on creation. A failed/ambiguous create is never blindly repeated.
Existing entries are polled or resumed using the original ID. The private resume
file can contain an upload URL and remains server-only with mode 0600; audit
records contain only permitted IDs/statuses/numeric scores. No API token or
private upload URL is copied into Git. Credential access before release and
duplicate creation after an ambiguous attempt are covered by integration checks.

`finish_local.py` holds an exclusive controller lock, waits for the current
candidate scores, freezes selection, runs the single seed confirmation and
release check, then exports and prepares ABC. Every stage has its own exit
record and bounded timeout. It carries no credentials and stops before upload;
the already-authorized upload is then executed and monitored separately. An
explicitly named repair preserves its original failed stage record.

## Execution-environment interruption

The execution environment briefly changed to restricted networking and read-only
Git metadata while remote evaluations were running. The user restored full access
on 2026-09-26. SSH inspection confirmed all three scores completed and the
controller advanced to the second decoding-seed confirmation. Training was not
repeated. No official upload has been initiated at this stage. Existing
task/submission authorization remains valid.
See [recovery notes](../../docs/research/effect-calibration-recovery-2026-09-26.md)
and [consolidated status](results/2026-09-26/campaign-status.json).
