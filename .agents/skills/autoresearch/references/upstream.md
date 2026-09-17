# Original karpathy/autoresearch workflow

## Source and version

Verified on 2026-09-08 against commit `228791fb499afffb54b46200aca536f79142f117`:

- [README.md](https://github.com/karpathy/autoresearch/blob/228791fb499afffb54b46200aca536f79142f117/README.md): project intent, setup, hardware, and portability.
- [program.md](https://github.com/karpathy/autoresearch/blob/228791fb499afffb54b46200aca536f79142f117/program.md): candidate scope, ledger, and research loop.
- [prepare.py](https://github.com/karpathy/autoresearch/blob/228791fb499afffb54b46200aca536f79142f117/prepare.py): data, tokenizer, constants, and evaluation.
- [train.py](https://github.com/karpathy/autoresearch/blob/228791fb499afffb54b46200aca536f79142f117/train.py): implementation and actual timing semantics.
- [pyproject.toml](https://github.com/karpathy/autoresearch/blob/228791fb499afffb54b46200aca536f79142f117/pyproject.toml): dependencies and CUDA package source.

Read the checked-out version before acting; these are verified defaults, not a promise about future revisions. These notes paraphrase the upstream protocol. No training code or data is bundled. The upstream README declares MIT; the inspected tree has no separate LICENSE file.

## Setup

The original requires a single NVIDIA GPU, Python 3.10+, and `uv`; upstream tested on H100. CPU, MPS, and alternative accelerators require an explicit port or suitable fork. Changing the platform also changes the scope of score comparisons.

When a checkout is needed, choose a new destination and clone the official URL:

```bash
git clone https://github.com/karpathy/autoresearch
```

Run these commands from that checkout as required by the requested setup:

```bash
uv sync
uv run prepare.py
```

Preparation downloads data and trains the tokenizer under `~/.cache/autoresearch/`. Inspect both `data/` and `tokenizer/` for the files the checked-out code expects. Installations and downloads can require network access and filesystem permission. Keep the pinned dependency configuration: the inspected revision uses PyTorch 2.9.1 with a CUDA 12.8 wheel source.

## Fixed and editable components

| Component | Treatment during a campaign |
| --- | --- |
| `train.py` | Candidate file: model, optimizer, hyperparameters, and training implementation |
| `prepare.py` | Fixed: data loader, tokenizer utilities, constants, `evaluate_bpb` |
| `program.md` | Human-authored experiment contract; keep outside candidate optimization |
| `pyproject.toml`, `uv.lock` | Fixed dependencies; no new candidate packages |
| `results.tsv`, run logs | Experiment artifacts outside candidate commits |

Preserve the original evaluation call and truthful loss computation even when changing `train.py`. Do not override imported constants, consume validation data for training, extend uncounted training, or return fabricated loss values.

## Metric and timing

`val_bpb` is validation bits per byte, lower is better. The evaluator sums per-token cross-entropy in nats, excludes zero-byte special tokens from both sums, then divides by `ln(2) * total_target_bytes`. Byte normalization supports comparisons across vocabulary sizes, but does not authorize changing the frozen tokenizer during this campaign.

At the inspected revision, `TIME_BUDGET = 300`, `MAX_SEQ_LEN = 2048`, and `EVAL_TOKENS = 40 * 524288`. Training time accumulates only for loop iterations with zero-based `step > 10`; startup, those initial steps, and final evaluation add elapsed time. The final timed step can slightly exceed 300 seconds. Preserve this accounting rather than treating five minutes as the total process duration.

Upstream's process timeout is ten minutes. A bounded GNU/Linux launch for an attempt, after creating the local log directory, is:

```bash
timeout --signal=TERM --kill-after=15s 600s uv run train.py > run-001.log 2>&1
```

Use a fresh log path for each attempt. Capture the command's exit status before issuing another shell command. Where GNU `timeout` is unavailable, use the execution environment's process timeout with equivalent child-process cleanup. Use a shorter limit if the campaign's remaining budget requires it. After completion, inspect:

```bash
rg '^(val_bpb|training_seconds|total_seconds|peak_vram_mb):' run-001.log
```

Inspect the log tail on failure. Upstream's GPU memory measure is peak PyTorch allocated memory; its reported utilization uses an H100 reference peak and is not portable utilization across accelerators. Five-minute runs do not guarantee twelve completed trials per hour.

## Compatible ledger

Keep the upstream five-column TSV header, with actual tab delimiters:

```text
commit	val_bpb	memory_gb	status	description
```

- `commit`: measured candidate's short Git hash; a later revert is not the measured revision.
- `val_bpb`: six decimals; upstream uses `0.000000` for failures.
- `memory_gb`: `peak_vram_mb / 1024`, one decimal; `0.0` on failure. This conversion is technically GiB despite the upstream column name.
- `status`: `keep`, `discard`, or `crash`. A valid initial baseline is `keep`.
- `description`: concise hypothesis or failure reason; avoid embedded tabs or newlines.

Keep this file outside candidate commits and append instead of truncating when resuming. Store additional attempt metadata and unique log paths in an adjacent run note or JSONL sidecar. A zero failure placeholder is not a successful zero score: rank only valid completed attempts. Timeouts and invalid summaries use `crash`, with the actual cause in the description. When Git commits are unavailable, use the alternative ledger described in [adapting.md](adapting.md), rather than inventing hashes.

## Deliberate adaptation from upstream

The original program assumes unlimited operation until interrupted and discards changes by resetting Git. This skill uses the user's campaign limit, or a stated small default batch, and preserves rejected experiments through patches or revert commits. It retains the hypothesis/evaluate/keep-or-discard method and simplicity preference. Existing execution permissions remain in force; setup never requires disabling them.
