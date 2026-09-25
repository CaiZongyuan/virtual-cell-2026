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
  context exclusion; one public-pretrained State residual candidate whose exact
  specification will be committed before training or H1 evaluation.
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
