# Jiang RDS count audit

This is a data-availability audit for a future experiment, separate from the
frozen effect-calibration campaign. The source and MD5 are pinned in
[the pilot note](../../docs/research/jiang-tgfb-data-pilot-2026-09-26.md).

The server has an isolated runtime at `~/vcc2026-rds-audit/env`: R 4.5.3,
Matrix 1.7.6 and jsonlite 2.0.0. The script passed a small fixture with an unknown
root S4 class, exact sparse axes, an empty cell and rejection of fractional
counts. The full Jiang object has **not** been parsed yet.

Run only after local model scoring and native submission packing have released
memory. Use a separate process with `R_MAX_VSIZE=22G`, a process address-space
limit around 26 GiB, a bounded timeout and `/usr/bin/time -v` resource logging.
These limits may reject a larger object; they do not establish that it fits.

```bash
Rscript --vanilla audit_jiang_rds.R \
  /mnt/e/vcc2026-data/raw/jiang_tgfb.rds \
  /path/to/audit-output \
  /home/caii/vcc2026-run/protocol.json
```

The script verifies the traditional RNA counts slot, sparse structure, count
values and gene/cell axes, and records measured/nonzero gene coverage. It retains
metadata summaries and an external compressed metadata table. It does not infer
which columns mean cell line, stimulus, batch, target or NTC; those mappings must
be established from the actual fields and author provenance before training.
The original RDS remains immutable. Large matrices and per-cell metadata stay
outside Git; only small audit summaries are candidates for version control.
