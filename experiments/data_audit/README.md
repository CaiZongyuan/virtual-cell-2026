# Jiang RDS count audit

This is a data-availability audit for a future experiment, separate from the
frozen effect-calibration campaign. The source and MD5 are pinned in
[the pilot note](../../docs/research/jiang-tgfb-data-pilot-2026-09-26.md).

The server has an isolated runtime at `~/vcc2026-rds-audit/env`: R 4.5.3,
Matrix 1.7.6 and jsonlite 2.0.0. The script passed a small fixture with an unknown
root S4 class, exact sparse axes, an empty cell and rejection of fractional
counts. The full Jiang object was successfully audited on 2026-09-26 after
submission packing released memory: 236,606 cells, 33,525 genes and 605,806,920
stored RNA counts. The reader exited 0 in 106.63 seconds (123.02 seconds for the
complete stage), with peak RSS 17,153,456 KiB. Integer/count/axis checks passed.

Run only after local model scoring and native submission packing have released
memory. Use a separate process with `R_MAX_VSIZE=22G`, a process address-space
limit around 26 GiB, a bounded timeout and `/usr/bin/time -v` resource logging.
These limits may reject a larger object; the successful read applies only to
this pinned object and environment.

```bash
Rscript --vanilla audit_jiang_rds.R \
  /mnt/e/vcc2026-data/raw/jiang_tgfb.rds \
  /path/to/audit-output \
  /home/caii/vcc2026-run/protocol.json
```

The script verifies the traditional RNA counts slot, sparse structure, count
values and gene/cell axes, and records measured/nonzero gene coverage. It retains
metadata summaries and an external compressed metadata table.
`summarize_jiang.py` reviews the explicit author fields, counts matched NT controls
at two batch resolutions, and compares genes/targets with the fixed protocol and
existing effect masks. Its `--previous`, `--campaign` and `--audit` arguments point
to the original run, effect-calibration run and R output directory respectively.
The source metadata identify six cell lines, TGFB1, Rep1/Rep2, 52 target genes and
9,809 NT cells; the precise technical meaning of `sample_ID` remains unresolved.
Both `orig.ident` and `sample_ID` must be preserved before choosing a training
batch definition. This file overlaps only MED15 in the official target panel.

The first R report serialized missing category names incorrectly in barcode-well
columns. The Python review re-counted the original metadata and verified missing
totals; use `metadata-columns-reviewed.json`. The R fix labels these categories
`__MISSING__` and passed a small NA-to-JSON round-trip fixture. Counts and all
matrix checks were unaffected, so the complete matrix was not reread.

See [audit artifacts](results/2026-09-26/) and the
[interpretation and remaining gaps](../../docs/research/jiang-tgfb-data-pilot-2026-09-26.md).
The original RDS remains immutable. Large matrices and per-cell metadata stay
outside Git. This data has not entered the current training or official submission.
