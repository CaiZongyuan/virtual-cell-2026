"""Matched-budget State adapter warmup and frozen/unfrozen experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

import numpy as np
import torch
import swanlab

from data import PreparedSource
from model import build_model, expression_from_counts, load_features, normalized_features, set_trainable


def checkpoint(path, model, optimizer, protocol, step, metrics, phase):
    temporary = path.with_suffix(".tmp")
    torch.save({"state_dict": model.state_dict(), "optimizer": optimizer.state_dict(),
                "protocol": protocol, "step": step, "metrics": metrics, "phase": phase}, temporary)
    temporary.replace(path)


def run(args):
    torch.set_num_threads(6)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    protocol = json.loads((args.work / "protocol.json").read_text())
    if args.sources:
        protocol["training_sources"] = args.sources
    features = load_features(args.root / "assets/ESM2_pert_features.pt")
    sources = [PreparedSource(args.work / "prepared" / name) for name in protocol["training_sources"]]
    supervised = np.logical_or.reduce([source.measured for source in sources])
    output = args.work / "runs" / args.phase
    output.mkdir(parents=True, exist_ok=True)
    np.save(output / "supervised.npy", supervised)
    model, migration = build_model(args.work / "upstream/state", args.root / "assets/parent/best.ckpt",
                                   protocol["genes"], features, protocol["parent_targets"], args.seed)
    if args.initial:
        state = torch.load(args.initial, weights_only=False, map_location="cpu")
        if state["protocol"]["gene_axis_sha256"] != protocol["gene_axis_sha256"]:
            raise ValueError("Checkpoint gene axis mismatch")
        model.load_state_dict(state["state_dict"], strict=True)
    set_trainable(model, args.phase in {"unfrozen", "pilot"})
    model.cuda()
    groups = [
        {"params": [p for n, p in model.named_parameters() if p.requires_grad and not n.startswith("transformer_backbone.")], "lr": 1e-4},
        {"params": [p for n, p in model.named_parameters() if p.requires_grad and n.startswith("transformer_backbone.")], "lr": 1e-5},
    ]
    optimizer = torch.optim.AdamW(groups, weight_decay=0.0)
    migration.update({"trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad),
                      "phase": args.phase, "steps": args.steps, "microbatch_sets": args.sets,
                      "seed": args.seed, "training_sources": protocol["training_sources"],
                      "initial_checkpoint": str(args.initial) if args.initial else None})
    (output / "migration.json").write_text(json.dumps(migration, indent=2) + "\n")
    swanlab.init(project="virtual-cell-2026", experiment_name=f"state-{args.phase}-seed{args.seed}",
                 group="first-finetune", job_type=args.phase, config=migration,
                 logdir=str(args.work / "swanlog"), mode="local")
    feature_map = {name: normalized_features(features, [name])[0].cuda() for name in protocol["training_targets"]}
    del features
    rng = np.random.default_rng(args.seed)
    source_weights = np.array([1.0]) if len(sources) == 1 else np.array([0.6 if source.manifest["source"] == "gwps" else 0.4 / (len(sources)-1) for source in sources])
    source_weights /= source_weights.sum()

    def loss(rng, split):
        source = sources[int(rng.choice(len(sources), p=source_weights))]
        basal, targets, perturbations = [], [], []
        for _ in range(args.sets):
            name, control, treatment, mask = source.sample(rng, split, 64)
            basal.append(expression_from_counts(control))
            targets.append(expression_from_counts(treatment))
            perturbations.append(feature_map[name].expand(64, -1))
        model.measurement_mask.copy_(torch.from_numpy(mask.astype(np.float32)).cuda())
        batch = {"ctrl_cell_emb": torch.from_numpy(np.concatenate(basal)).cuda(),
                 "pert_emb": torch.cat(perturbations)}
        target = torch.from_numpy(np.stack(targets)).cuda()
        with torch.autocast("cuda", dtype=torch.bfloat16):
            prediction = model(batch).reshape(args.sets, 64, -1)
        measured = torch.from_numpy(source.measured).cuda()
        # Distribution loss is FP32 and excludes source-unmeasured genes.
        return model._compute_distribution_loss(prediction.float()[..., measured], target[..., measured]).mean()

    best = float("inf")
    start = time.monotonic()
    log = (output / "metrics.jsonl").open("a", buffering=1)
    for step in range(1, args.steps + 1):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        train_loss = loss(rng, "training")
        if not torch.isfinite(train_loss):
            raise ValueError(f"Non-finite training loss at step {step}")
        train_loss.backward()
        grad_norm = torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 10.0, error_if_nonfinite=True)
        optimizer.step()
        if step % 20 == 0 or step == 1:
            item = {"step": step, "training_loss": train_loss.item(), "grad_norm": float(grad_norm),
                    "elapsed_seconds": time.monotonic()-start,
                    "gpu_peak_bytes": torch.cuda.max_memory_allocated(),
                    "host_peak_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                    "steps_per_second": step/(time.monotonic()-start)}
            log.write(json.dumps(item)+"\n")
            dashboard = {"loss/train": item["training_loss"], "optimization/grad_norm": item["grad_norm"],
                         "resources/gpu_peak_GiB": item["gpu_peak_bytes"] / 2**30,
                         "resources/host_peak_GiB": item["host_peak_bytes"] / 2**30,
                         "throughput/steps_per_second": item["steps_per_second"],
                         "learning_rate/interface": optimizer.param_groups[0]["lr"],
                         "learning_rate/backbone": optimizer.param_groups[1]["lr"] if optimizer.param_groups[1]["params"] else 0.0}
            swanlab.log(dashboard, step=step)
            print(json.dumps({"phase": args.phase, **item}), flush=True)
        if step % args.validate_every == 0 or step == args.steps:
            model.eval()
            validation_rng = np.random.default_rng(101)
            with torch.no_grad():
                values = [loss(validation_rng, "development").item() for _ in range(16)]
            validation = float(np.mean(values))
            item = {"step": step, "development_loss": validation, "elapsed_seconds": time.monotonic()-start}
            log.write(json.dumps(item)+"\n")
            swanlab.log({"loss/development": validation}, step=step)
            print(json.dumps({"phase": args.phase, **item}), flush=True)
            if validation < best:
                best = validation
                checkpoint(output / "best.pt", model, optimizer, protocol, step, item, args.phase)
            checkpoint(output / "last.pt", model, optimizer, protocol, step, item, args.phase)
    log.close()
    swanlab.finish()
    (output / "complete.json").write_text(json.dumps({"phase": args.phase, "steps": args.steps, "best_development_loss": best})+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--phase", choices=["pilot", "warmup", "frozen", "unfrozen"], required=True)
    parser.add_argument("--sources", nargs="+")
    parser.add_argument("--initial", type=Path)
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--sets", type=int, default=2)
    parser.add_argument("--validate-every", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    run(parser.parse_args())
