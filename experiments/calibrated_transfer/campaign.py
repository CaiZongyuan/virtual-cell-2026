"""Small fixed-budget campaign; H1 labels belong exclusively to the scorer."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time
import zlib

import h5py
import numpy as np
import torch

from data import PreparedSource, cache_controls, gene_names
from effects import context_average, log_effect, matched_means, transfer_counts
from export import Writer
from model import build_model, expression_from_counts, load_features, normalized_features


SOURCES = ["gwps", "k562", "rpe1", "hepg2"]
CONTEXTS = {"gwps": "K562", "k562": "K562", "rpe1": "RPE1", "hepg2": "HepG2"}


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def prepare(args):
    args.work.mkdir(parents=True, exist_ok=True)
    entries, deltas, controls, masks = [], [], [], []
    for name in SOURCES:
        source = PreparedSource(args.previous / "prepared" / name)
        for group in source.groups:
            control, treated = matched_means(source, group)
            deltas.append(log_effect(control, treated, source.measured))
            controls.append(control.astype(np.float32))
            masks.append(source.measured)
            entries.append({"source": name, "target": group["target"],
                            "cells": len(group["training"]), "context": CONTEXTS[name]})
        print(json.dumps({"prepared": name, "conditions": len(source.groups)}), flush=True)
        del source
    np.savez(args.work / "effects.npz", deltas=np.stack(deltas), controls=np.stack(controls),
             masks=np.stack(masks))
    save_json(args.work / "effects.json", {"entries": entries, "sources": SOURCES,
              "protocol_sha256": sha(args.previous / "protocol.json"),
              "prepared_manifests": {s: sha(args.previous / "prepared" / s / "manifest.json") for s in SOURCES}})


def load_state(args):
    protocol = json.loads((args.previous / "protocol.json").read_text())
    features = load_features(args.root / "assets/ESM2_pert_features.pt")
    model, migration = build_model(args.previous / "upstream/state", args.root / "assets/parent/best.ckpt",
                                    protocol["genes"], features, protocol["parent_targets"], 42)
    initial = args.previous / "runs/unfrozen/best.pt"
    checkpoint = torch.load(initial, map_location="cpu", weights_only=False)
    if checkpoint["protocol"]["gene_axis_sha256"] != protocol["gene_axis_sha256"]:
        raise ValueError("Initialization gene axis mismatch")
    model.load_state_dict(checkpoint["state_dict"], strict=True)
    del checkpoint
    migration.update(initial_checkpoint_sha256=sha(initial), initial_checkpoint=str(initial),
                     parent_sha256=sha(args.root / "assets/parent/best.ckpt"))
    return model.cuda().eval(), features, protocol, migration


def contrast(model, expression, features):
    """Identical control sets in both branches; no dropout in either branch."""
    sets = len(features)
    basal = expression.reshape(sets * 64, -1)
    perturbations = features[:, None].expand(-1, 64, -1).reshape(sets * 64, -1)
    result = model({"ctrl_cell_emb": torch.cat([basal, basal]),
                    "pert_emb": torch.cat([perturbations, torch.zeros_like(perturbations)])})
    response, null = result.float().reshape(2, sets, 64, -1).unbind(0)
    return (response - null).mean(dim=1)


def train(args):
    import swanlab

    torch.set_num_threads(4)
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    model, features, protocol, report = load_state(args)
    for name, parameter in model.named_parameters():
        parameter.requires_grad_(not name.startswith("transformer_backbone."))
        if args.arm == "limited" and any(f"layers.{i}." in name for i in [6, 7]):
            parameter.requires_grad_(True)
    # Evaluation mode disables dropout without disabling gradients.
    model.eval()
    optimizer = torch.optim.AdamW([
        {"params": [p for n, p in model.named_parameters() if p.requires_grad and not n.startswith("transformer_backbone.")], "lr": 1e-4},
        {"params": [p for n, p in model.named_parameters() if p.requires_grad and n.startswith("transformer_backbone.")], "lr": 1e-5},
    ], weight_decay=0)
    with np.load(args.work / "effects.npz") as archive:
        tables = {key: archive[key] for key in archive.files}
    entries = json.loads((args.work / "effects.json").read_text())["entries"]
    lookup = {(r["source"], r["target"]): i for i, r in enumerate(entries)}
    sources = [PreparedSource(args.previous / "prepared" / name) for name in SOURCES]
    feature_map = {g: normalized_features(features, [g])[0].cuda() for g in protocol["training_targets"]}
    output = args.work / "runs" / args.arm
    output.mkdir(parents=True, exist_ok=False)
    report.update(arm=args.arm, steps=args.steps, trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad),
                  parameter_count=sum(p.numel() for p in model.parameters()), seed=42,
                  effects_sha256=sha(args.work / "effects.npz"), dropout="disabled in both branches")
    save_json(output / "provenance.json", report)
    swanlab.init(project="virtual-cell-2026", experiment_name=f"calibrated-{args.arm}-seed42",
                 group="calibrated-transfer", config=report, logdir=str(args.previous / "swanlog"), mode="local")
    rng = np.random.default_rng(42)
    start = time.monotonic()

    def loss(split, local_rng):
        # Equal biological context mass; K562's two source files share its third.
        source = sources[int(local_rng.choice(4, p=[1/6, 1/6, 1/3, 1/3]))]
        basal, vectors, desired, weights = [], [], [], []
        for _ in range(2):
            name, control, treated, measured = source.sample(local_rng, split, 64)
            index = lookup[(source.manifest["source"], name)]
            basal.append(expression_from_counts(control))
            vectors.append(feature_map[name])
            if split == "training":
                expected = tables["deltas"][index]
                mean = tables["controls"][index]
            else:
                mean = np.expm1(expression_from_counts(control)).mean(0)
                expected = log_effect(mean, np.expm1(expression_from_counts(treated)).mean(0), measured)
            desired.append(np.clip(expected, -np.log(4), np.log(4)))
            weight = np.sqrt(mean + 0.1) * measured
            weights.append(weight / weight.mean())
        model.measurement_mask.copy_(torch.from_numpy(measured.astype(np.float32)).cuda())
        x = torch.from_numpy(np.stack(basal)).cuda()
        target = torch.from_numpy(np.stack(desired)).cuda()
        weight = torch.from_numpy(np.stack(weights)).cuda()
        with torch.autocast("cuda", dtype=torch.bfloat16):
            delta = contrast(model, x, torch.stack(vectors))
        return ((delta - target).square() * weight).mean()

    with (output / "metrics.jsonl").open("w", buffering=1) as log:
        for step in range(1, args.steps + 1):
            optimizer.zero_grad(set_to_none=True)
            value = loss("training", rng)
            if not torch.isfinite(value):
                raise ValueError("Non-finite loss")
            value.backward()
            grad = torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 10, error_if_nonfinite=True)
            optimizer.step()
            if step == 1 or step % 50 == 0:
                row = {"step": step, "loss": value.item(), "grad_norm": float(grad),
                       "elapsed_seconds": time.monotonic()-start,
                       "gpu_peak_bytes": torch.cuda.max_memory_allocated(),
                       "host_peak_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}
                log.write(json.dumps(row)+"\n")
                swanlab.log({"loss/train": row["loss"], "optimization/grad_norm": row["grad_norm"],
                             "resources/gpu_GiB": row["gpu_peak_bytes"]/2**30}, step=step)
                print(json.dumps(row), flush=True)
        with torch.inference_mode():
            dev_rng = np.random.default_rng(101)
            development = float(np.mean([loss("development", dev_rng).item() for _ in range(16)]))
        row = {"steps": args.steps, "development_loss": development, "elapsed_seconds": time.monotonic()-start}
        log.write(json.dumps(row)+"\n")
    torch.save({"state_dict": model.cpu().state_dict(), "provenance": report,
                "gene_axis_sha256": protocol["gene_axis_sha256"]}, output / "final.pt")
    save_json(output / "complete.json", row)
    swanlab.finish()


def predict(args):
    torch.set_num_threads(4)
    protocol = json.loads((args.previous / "protocol.json").read_text())
    with np.load(args.work / "effects.npz") as archive:
        tables = {key: archive[key] for key in archive.files}
    entries = json.loads((args.work / "effects.json").read_text())["entries"]
    # Only public input target labels; never reference DE, moments or scale files.
    import pandas as pd
    panel = pd.read_csv(args.previous / "h1-benchmark/benchmark/reference_cells.csv")
    target_key = "target_gene" if "target_gene" in panel.columns else "target"
    targets = sorted(panel[target_key].unique())
    if len(targets) != 126:
        raise ValueError("H1 target panel differs")
    genes = protocol["h1_genes"]
    positions = {g: i for i, g in enumerate(protocol["genes"])}
    selected = np.array([positions[g] for g in genes])
    supervised = tables["masks"].any(axis=0)
    model = None
    checkpoint = None
    if args.arm != "empirical":
        model, features, _, _ = load_state(args)
        checkpoint = args.work / "runs" / args.arm / "final.pt"
        state = torch.load(checkpoint, map_location="cpu", weights_only=False)
        if state["gene_axis_sha256"] != protocol["gene_axis_sha256"]:
            raise ValueError("Prediction checkpoint axis mismatch")
        model.load_state_dict(state["state_dict"], strict=True)
        del state
        mask = np.zeros(len(positions), np.float32)
        mask[selected] = 1
        model.measurement_mask.copy_(torch.from_numpy(mask).cuda())
    output = args.work / "predictions" / f"{args.arm}.h5ad"
    contract = {"arm": args.arm, "effects_sha256": sha(args.work / "effects.npz"),
                "checkpoint_sha256": sha(checkpoint) if checkpoint else None, "shrink": 0.5,
                "seed_namespace": "h1-control-baseline-v1", "addition_seed": 42}
    writer = Writer(output, genes, [{"target_gene": t} for t in targets for _ in range(400)], contract=contract)
    diagnostics = []
    with h5py.File(args.previous / "h1-benchmark/h1_controls.h5ad") as handle:
        if list(gene_names(handle)) != genes:
            raise ValueError("Control gene axis mismatch")
        controls = cache_controls(handle)
        if controls is None:
            raise ValueError("Controls exceed in-memory bound")
        with torch.inference_mode():
            for target in targets:
                seed = zlib.crc32(f"h1-control-baseline-v1:{target}".encode())
                rows = np.sort(np.random.default_rng(seed).choice(controls.shape[0], 400, replace=False))
                raw = controls[rows].toarray()
                if model is None:
                    matches = [i for i, r in enumerate(entries) if r["target"] == target]
                    if matches:
                        delta, available = context_average(tables["deltas"][matches], tables["masks"][matches],
                                                            [entries[i]["context"] for i in matches])
                    else:
                        delta, available = np.zeros(len(positions)), np.zeros(len(positions), bool)
                else:
                    full = np.zeros((448, len(positions)), np.float32)
                    full[:, selected] = np.concatenate([raw, raw[:48]])
                    x = torch.from_numpy(expression_from_counts(full)).cuda().reshape(7, 64, -1)
                    vectors = normalized_features(features, [target]).cuda().expand(7, -1)
                    with torch.autocast("cuda", dtype=torch.bfloat16):
                        delta = contrast(model, x, vectors).mean(0).cpu().numpy()
                        if not diagnostics:
                            identity = contrast(model, x, torch.zeros_like(vectors))
                            if not torch.equal(identity, torch.zeros_like(identity)):
                                raise ValueError("NTC differential is not exactly zero")
                    available = supervised
                rng = np.random.default_rng(zlib.crc32(f"42:{target}".encode()))
                predicted = transfer_counts(raw, delta[selected], available[selected], rng)
                writer.append(predicted)
                diagnostics.append({"target": target, "effect_rms": float(np.sqrt(np.mean(delta[selected]**2))),
                                    "measured_genes": int(available[selected].sum()),
                                    "mean_depth_ratio": float(predicted.sum()/raw.sum())})
                print(json.dumps({"target": target, "rows": writer.row}), flush=True)
    result = writer.finish()
    result.update(contract)
    result["diagnostics"] = diagnostics
    save_json(output.with_suffix(".json"), result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "train", "export"])
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("/mnt/e/vcc2026-data"))
    parser.add_argument("--arm", choices=["empirical", "frozen", "limited"], default="empirical")
    parser.add_argument("--steps", type=int, default=1000)
    args = parser.parse_args()
    {"prepare": prepare, "train": train, "export": predict}[args.action](args)
