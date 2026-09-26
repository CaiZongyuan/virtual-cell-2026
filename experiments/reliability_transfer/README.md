# Reliability-aware source effects, 2026-09-26

Starting revision: `02e40a8`. The user requested further improvement after the
official score remained near zero. This is a new bounded campaign; the previous
campaign and its one submitted artifact remain immutable.

## Question and fixed limits

The current official-target effects come only from GWPS, using 52–205 training
cells per admitted condition. A training-only split-half diagnostic found median
cosine 0.0396 for its 254 official targets (target gene excluded; control mean
above 0.1 CP10K). Shared controls can inflate this value. This suggests noisy
effects, but does not prove that uncertainty explains the official score.

Use all eligible source cells instead of the old 256-cell cap, retaining the old
development cells as held out. Compute matched-control mean effects and sampling
uncertainties by streaming existing public raw count files. This is data/label
preparation for public-pretrained adaptation, not foundation-model pretraining.
Jiang and Jurkat response labels are not used in this campaign.

Fixed candidates (at most three):

1. `expanded`: expanded training-cell means; same log fold change, pseudocount
   0.1, context averaging, clipping ±ln(4), and strength 0.5 as the incumbent.
2. `shrunk`: same cells, with a zero-centered normal-mixture empirical Bayes
   posterior effect per source; same aggregation, strength and count decoder.
3. `state`: public-State descendant, signed zero head and previous 6,000-step
   residual recipe, now supervised by shrunk source effects around a strength
   0.5 prior; output is shrunk prior plus fixed 0.1 residual. Only conditions
   supported by the existing prepared control sampler enter neural training.
   Parent weights and their unresolved pretraining exposure stay documented.

For each raw source, exclude the exact original rows of the existing development
split. Admit training targets in the frozen protocol with at least 32 remaining
cells in batches with at least 16 NT controls. Retain all matching controls and
training cells; K562's two files still count as one biological context. Compute
CP10K on the same measured project-axis genes as before. Sampling variance uses
treated sample variance/n and the sum of squared batch fractions times control
sample variance/n. Delta-method log-effect variance is an approximation, not a
biological replicate standard error or proof of calibrated false discoveries.

The normal-mixture prior has fixed SDs 0, .025, .05, .1, .2, .4, .8, 1.6. Fit
mixing proportions separately per source using at most 200,000 training effects
(seed 42), 100 EM steps, no H1 labels or score-based tuning. Posterior means are
bounded between zero and the input effect. This is a small custom normal-means
estimator; it is not a reproduction of multivariate mash or its reported results.

H1 benchmark stays at v0.2.0 / `d28dd0496cc9fbf1d0088ce171208c0deb54a268`,
126 × 400 cells, 18,080 genes, cell-eval2 0.16.0 / pdex 0.3.0, six
`from_replicate` metrics, gene chunk 512, DE threads 8. Canonical control sampling
and decoding seed 42 remain unchanged. Reuse the completed incumbent (0.163874)
and NTC (-0.045231) only after verifying actual prediction and output hashes and
the scoring protocol. H1 is an already-used development background.

Accept only a complete candidate with H1 composite ≥ incumbent + .01, raw MSE
≤ incumbent and raw NMAE ≤ 1.1 × incumbent. Source-context exclusion diagnostics
are reported independently, not substituted for the real score. One selected
candidate gets decoding seed 43 confirmation (drop ≤ .01, same remaining gates).
No new official entry for an unchanged incumbent. A newly improved candidate
may use one authorized submission only after full artifact checks and live daily
allowance; respect the competition's two-per-day/one-in-flight limits. Public
names remain random, and official results are separate from H1 scores.

At most one preprocessing job, two resident scorers, one scorer during GPU
training; require 12 GB available before scoring. Storage including all old runs
and caches must stay below 500 GB, with 50 GB reserved headroom. Each candidate
has a four-hour budget including scoring, preparation has two hours, and only one
targeted repair is allowed per failed stage. Preserve failed statuses; no blind
restarts. No modifications to evaluator math, hidden labels or the old artifacts.

## Entry points

`aggregate.py --previous ~/vcc2026-run --root /mnt/e/vcc2026-data --work RUN`
streams source sufficient statistics; `fit.py` produces fixed candidate tables.
`predict.py` exports the same canonical H1 panel. Stages run through the existing
bounded `effect_calibration/stage.py`; large arrays stay on the server. Small
diagnostics, code revisions, stage exits and verified scores are committed.


## Final user stopping instruction

The user requested: finish this round, submit its best result to the leaderboard,
then stop. Complete the already frozen three-arm comparison and its required
confirmation only. Do not start a new experiment, data expansion or campaign.
If the highest-scoring new candidate passes the final stability gates below,
`export_official.py` rechecks
all score/prediction hashes and replays every stored H1 count exactly before
exporting ABC from the same frozen predictor. Native full prep and live account
allowance checks remain required. If the incumbent stays best, retain its already
published entry instead of uploading an identical artifact. After the official
terminal status, finish records and commits and terminate owned helpers/jobs.


### Final ranking requested by the user

The later instruction explicitly requests submitting the best score after this
round and stopping. Final leaderboard selection therefore uses the highest valid
completed H1 composite, including the incumbent. The original automatic .01 gain
and MSE/NMAE acceptance flags remain intact as diagnostics; they are not falsely
reported as passed. No candidate parameters, evaluator, data split or seeds change.
`finalize_selection.py` runs after the original controller exits, freezes this
ranking, reuses an existing seed-43 result where applicable or confirms the chosen
candidate once. Confirmation must remain above the incumbent and within .01 of
the first seed; otherwise retain the already published incumbent. Count replay,
native full preparation and live allowance gates remain mandatory. No new training
configuration or data collection follows this final instruction.
