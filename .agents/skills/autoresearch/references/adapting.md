# Adapting the experiment loop

Use this path when the target is not the original language-model repository. Reuse the fixed-budget, fixed-evaluation loop while deriving the actual metric, data boundaries, and editable scope from the target project.

## Write a concrete contract

Use an existing experiment specification when available. Otherwise create a concise `program.md` or equivalent run note recording the fields in the main skill. Fill those fields with executable commands and concrete file paths before launching optimization.

Choose a budget suited to the question: equal training wall time tests throughput and learning efficiency together; equal steps, examples, or tokens tests another tradeoff. Keep that choice constant within a campaign. The original 300-second budget and `val_bpb` metric apply only to the original task.

Use the project's real scoring implementation and direction, with explicit feasibility constraints such as peak memory or maximum latency. For several metrics, define how to choose among them before seeing candidate results. Keep evaluator code and its configuration outside editable candidate scope. Snapshot or hash the fixed protocol so accidental changes are detectable.

Freeze validation splits, sample identities, preprocessing, seeds or seed schedule, and measurement hardware. Hold final test data out of the tuning loop. Repeated validation selection can overfit even without training on validation samples; reserve a separate confirmation set or final evaluation where available. If an evaluator is defective, repair it as a separate task and establish a new baseline.

## Select experiments that answer the question

Start with a valid unchanged baseline, then choose candidates based on evidence: training curves, profiles, error breakdowns, and previously recorded trials. Architectural changes and hyperparameters are possible candidate axes; neither is required. Use a lightweight syntax or smoke check when it can prevent an expensive invalid run, while keeping its score separate from the full evaluation.

For noisy objectives, define an acceptance tolerance and reserve some budget for repeated runs of the incumbent and promising candidates under matching seeds. Report the number of runs and variability. A single favorable result supports a provisional candidate, not a demonstrated general improvement.

Platform, dataset, evaluator, and budget changes define new campaigns. Retain links to prior campaigns as context without ranking their raw scores together.

## Keep a reproducible ledger

Prefer the target project's existing result schema. Otherwise JSONL or TSV may record:

- Attempt ID, timestamp, measured commit or base revision plus patch checksum.
- Parent/best revision, hypothesis, and edited paths.
- Metric name, direction, value, and secondary metrics.
- Protocol identity, data identity, seeds, hardware, elapsed time, and peak memory.
- Outcome (`keep`, `discard`, `crash`), failure reason, and any provisional designation.
- Exact launch command and log/artifact paths.

Use a real serializer for JSONL or TSV records. Missing or invalid values are null/empty and always paired with a failure outcome, never treated as a numerical improvement. Preserve rejected candidate patches or commits so the ledger is reproducible.

## Domain-specific checks

For scientific or competition tasks, read official evaluation and permitted-data rules before creating the contract. Match the deployment generalization question when splitting data. For example, a perturbation predictor intended for unseen cell backgrounds needs validation that withholds relevant backgrounds; a random split of cells from the same background can test a materially easier task. Derive the actual split and raw-count or transformed-expression requirements from the target benchmark rather than assuming this example is its rule.

This workflow optimizes the defined experiment. It does not by itself validate biological mechanisms, prove transfer to unseen hardware or data, or replace an independent final evaluation.
