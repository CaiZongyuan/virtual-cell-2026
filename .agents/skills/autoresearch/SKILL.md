---
name: autoresearch
description: Set up, run, or adapt Karpathy-style autonomous experiments that edit code, evaluate a fixed objective under a fixed budget, and keep or discard changes. Use for karpathy/autoresearch, autonomous model tuning, or repeated benchmark-driven optimization; not for literature search or ordinary one-off code fixes.
---

# Autoresearch

Turn a measurable research objective into a reproducible sequence of bounded experiments. Start from a measured baseline, change a coherent hypothesis, evaluate under the same conditions, and retain useful improvements with an experiment ledger.

Adapted from [karpathy/autoresearch](https://github.com/karpathy/autoresearch). This skill supplies the experiment protocol; obtain training code from the upstream repository when needed.

## Choose the scope

- For the original single-GPU language-model experiment, read [references/upstream.md](references/upstream.md) before setup or execution.
- For another model, benchmark, or codebase, read [references/adapting.md](references/adapting.md) before defining its experiment contract. Preserve the user's domain and metric.
- If asked only to explain, configure, or port the workflow, deliver that artifact. Starting training requires an execution request.

## Establish the experiment contract

Read repository instructions, the local experiment program if present, and the actual training and evaluation code. Resolve these fields from the request and repository, then record them in a short run note outside the candidate code:

| Field | Record |
| --- | --- |
| Objective | Primary metric, direction, acceptance rule, resource constraints |
| Editable scope | Candidate files and allowed types of changes |
| Fixed protocol | Evaluator, data splits, preprocessing, budget, seeds, environment |
| Execution | Setup command, experiment command, metric extraction, timeout |
| Campaign limit | Trial count or deadline, including baseline, retries, and confirmations |
| Provenance | Starting revision, hardware, dependency versions, data identity |
| Artifacts | Ledger, per-attempt logs, candidate revisions, current best revision |

Use the user's stated budget and existing authorization. If execution is requested without a campaign limit, announce a small initial batch of one baseline and up to three candidate attempts. A supplied deadline or trial count overrides this default. Explicit requests to continue until interrupted permit continued experiments within the available execution environment; they do not establish a background service or grant additional resource access.

## Prepare and measure

1. Inspect Git status and existing results. Use a dedicated `autoresearch/<tag>` branch or isolated worktree from the chosen starting revision. Preserve user edits and staged changes; never stash or reset them automatically. If their edits belong in the experiment, capture them deliberately in the starting snapshot.
2. Verify compute, dependencies, and data. Perform requested setup within available permissions. An unavailable GPU, missing dataset access, or failing baseline is a setup blocker, not evidence about a candidate.
3. Run the unmodified baseline with the exact evaluation contract. Require successful completion and a finite, valid primary metric before comparing candidates. Record both training time and total elapsed time when they differ.
4. On resume, inspect the existing ledger, logs, revision, and any running process before launching work. Reuse a baseline only when its protocol and environment still match. Preserve previous records.

## Experiment loop

1. Select one coherent hypothesis using measured bottlenecks, prior outcomes, or relevant source evidence. State the expected effect and why it might help. A coupled change is acceptable when its components test one hypothesis.
2. Modify only the candidate scope. Review the diff for evaluation or data leakage, budget bypasses, and unintended changes. An editable training file still must compute the real objective and call the fixed evaluator honestly.
3. Capture the exact candidate revision before running. Use local commits in the isolated experiment branch when permitted; otherwise preserve a patch against the base revision and its checksum. Keep large data, model outputs, logs, and secrets outside commits.
4. Run with a unique log per attempt and an enforced timeout covering startup, training, and evaluation. Bound a trial by the remaining campaign budget as well. Observe the process exit status and inspect the final metric; a printed value alone does not establish success.
5. Record every attempt before restoring code: candidate identity, metric, resources, status, hypothesis, log path, and failure reason where relevant. Missing metrics, NaN/Inf, nonzero exits, timeouts, and invalid evaluation are failures. A failure placeholder must never enter the ranking.
6. Keep a valid improvement that satisfies the contract. Prefer simpler code when quality is equivalent within the declared tolerance. Use available budget to confirm small or noisy gains, and label unconfirmed gains provisional.
7. For a rejected candidate, restore the last accepted implementation by reversing only this experiment's patch, or use a normal revert commit on the isolated branch. Preserve its measured candidate revision and logs. Do not use a repository-wide destructive reset as routine rollback.
8. Continue without asking for permission between already authorized trials. Retry a repairable candidate only within the campaign budget; record each retry. When the same infrastructure failure persists after a targeted repair and retry, stop and report the blocker instead of consuming the remaining budget.

Keep the evaluator, data split, and measurement contract fixed throughout a campaign. If one must change, begin a separately identified campaign and rerun its baseline; old and new scores are not directly comparable.

## Finish or pause

Stop at the requested limit, user interruption, exhausted budget, or a blocker that prevents meaningful experiments. Terminate and reap experiment processes when ending a bounded campaign; preserve resumable state on interruption. Do not imply that work continues after the execution environment has stopped.

Leave the best accepted implementation ready to inspect and distinguish provisional candidates. Report baseline versus best metric, completed attempts by outcome, resource use, best revision, ledger/log locations, and unresolved uncertainty. For minimization, relative improvement is `(baseline - best) / baseline` when the baseline is nonzero; report the absolute change too. Explain the practical scope of the gain, such as a particular GPU and training budget, rather than claiming general model superiority.
