# Stack native calibration diagnostic

This is a bounded interface/calibration check, not a fourth H1 optimization trial.
It uses H1 NTC and external K562 NTC only, with no H1 perturbation labels or model
updates. Source and query matrices are independently aligned to the published
15,012-gene vocabulary before calling the pinned upstream API.

The aligned checkpoint and gene-list SHA-256 values are enforced by `smoke.py`.
Upstream source: `cacc2e4b09435c3e536d46237d10b50f222dd144`; HF revision:
`b09f085dac03d170b078a5c72f550ae93686e544`. Details and first-party links are in the
[source audit](../../docs/research/stack-native-transfer-readiness-2026-09-26.md).

Run in an isolated Python 3.12 environment with torch 2.7.1+cu126 and **pandas
2.3.3**. The observed environment is recorded in [environment.txt](results/2026-09-26/environment.txt).
The experiment environment adds a `.pth` reference to the existing State
environment for immutable shared dependencies; installs/overrides live only in
the separate Stack environment. The original State/evaluation environments were
not upgraded. The original loader strictly loads the public checkpoint on CPU
before moving the model to the GPU.

```bash
PYTHONPATH=/path/to/pinned/stack/src:/path/to/experiments/state_finetune \
python smoke.py --previous /path/to/previous-run --root /path/to/data \
  --assets /path/to/stack-aligned --cells 64 --output /path/to/audit/ntc.json
```

`--cells 512` checks the checkpoint's original window size. Use FP32, batch=1,
and a single GPU lock shared with training. Large prediction arrays remain in
the external audit directory; only the small diagnostic summaries enter Git.

## Measured outcome

Both window sizes ran on the RTX 3090 and produced finite nonnegative integer
counts. The model contains 217,806,513 parameters. Peak allocated GPU memory was
0.90 GiB at 64 cells and 1.35 GiB at 512 cells. These are inference measurements,
not fine-tuning capacity estimates.

| Diagnostic | 64 cells | 512 cells |
|---|---:|---:|
| Same-context NTC composition TV | 0.34984 | 0.34622 |
| K562 NTC → H1 NTC composition TV | 0.35271 | 0.34850 |
| H1 NTC split-half TV | 0.04900 | 0.01754 |
| Same-context output/input model-panel depth | 1.00128 | 0.99973 |

TV here compares average per-cell gene proportions, on the model gene axis.
The two window diagnostics use different sample sizes; they are calibration
checks, not an isolated causal estimate of changing the window. The 64-cell
follow-up separates genes actually measured in H1: conditional TV is still
0.32859 / 0.33133 for the two conditions. Only 5.22% / 5.27% of predicted count
mass falls on the 2,141 genes outside H1's measured panel. Missing target genes
therefore do not account for most of this drift.

**Do not promote native generation to a complete H1 predictor on this evidence.**
The remaining causes include assay/preprocessing mismatch and the model's
conditional generation behavior. Differential generation against a synthetic
NTC or supervised adaptation is a future hypothesis. This diagnostic does not
compare Stack's perturbation accuracy with State, nor establish H1 pretraining
exclusion.

Two setup failures are preserved in the server audit: pandas 3 returned a
`StringArray` incompatible with upstream `np.char.upper` (fixed by pinning
2.3.3), then the local harness treated the native CSR return as AnnData (fixed in
`0efd16a`). Both were followed by successful real inference. The successful
summaries are [64 cells](results/2026-09-26/ntc-smoke.json),
[512 cells](results/2026-09-26/ntc-smoke-512.json) and
[observed-panel follow-up](results/2026-09-26/ntc-observed-panel.json).
