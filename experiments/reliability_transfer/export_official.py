"""Verify the selected predictor against its H1 counts, then export official ABC."""

import argparse
import hashlib
import json
from pathlib import Path
import time
import zlib

import h5py
import numpy as np
import pandas as pd
from scipy import sparse

from campaign import save_json, sha
from data import cache_controls, gene_names, h5_column
from effects import transfer_counts
from export import Writer, templates
from select_candidate import read_result, require_stage


class ReleasedPredictor:
    def __init__(self, args, arm):
        self.arm = arm
        self.table_path = args.work / ("shrunk.npz" if arm == "state" else f"{arm}.npz")
        self.info = json.loads((args.work / "effects.json").read_text())
        self.protocol = json.loads((args.previous / "protocol.json").read_text())
        table_arm = "shrunk" if arm == "state" else arm
        if sha(self.table_path) != self.info["candidate_hashes"][table_arm]:
            raise ValueError("Frozen effect table changed")
        if sha(args.previous / "protocol.json") != self.info["protocol_sha256"]:
            raise ValueError("Frozen model axes changed")
        with np.load(self.table_path) as archive:
            self.tables = {k: archive[k] for k in archive.files}
        self.lookup = {t: i for i, t in enumerate(self.info["targets"])}
        self.residual = None
        if arm == "state":
            from residual import ResidualPredictor
            self.residual = ResidualPredictor(args)

    def predict(self, raw, selected, target, rng):
        # Same arithmetic/order as the frozen H1 exporter, checked against every
        # stored H1 row before any ABC export below.
        if target in self.lookup:
            i = self.lookup[target]
            delta = self.tables["deltas"][i, selected]
            mask = self.tables["masks"][i, selected]
            if self.residual is not None:
                delta = .5 * np.clip(delta, -np.log(4), np.log(4)) + .1 * self.residual.predict(raw, selected, target)[selected]
        else:
            delta, mask = np.zeros(len(selected)), np.zeros(len(selected), bool)
        return transfer_counts(raw, delta, mask, rng, shrink=1 if self.residual else .5)


def checked_release(args):
    work = args.work
    summary = json.loads((work / "final-selection.json").read_text())
    if summary["selected"] == "incumbent":
        raise ValueError("Incumbent is already published; do not create a duplicate artifact")
    if summary["local_release_passed"] is not True:
        raise ValueError("Final seed stability gate did not pass")
    baseline = json.loads((args.incumbent / "evaluation/control/manifest.json").read_text())
    incumbent = read_result(args.incumbent / "evaluation/empirical", baseline,
                            args.incumbent / "predictions/empirical.h5ad")
    results = {"incumbent": incumbent}
    for arm in ["expanded", "shrunk", "state"]:
        terminal = json.loads((work / "status" / f"{arm}-score-42.json").read_text())
        if terminal["exit_code"] != 0:
            continue
        require_stage(work, f"{arm}-score-42")
        result = read_result(work / "evaluation" / f"{arm}-seed42", baseline,
                            work / "predictions" / f"{arm}-seed42.h5ad")
        results[arm] = result
    selected = max(results, key=lambda a: results[a]["score"])
    if selected != summary["selected"]:
        raise ValueError("Selected candidate differs from actual verified scores")
    confirmation_stage = f"{selected}-score-43" if summary["confirmation_reused"] else "final-confirmation-score"
    require_stage(work, confirmation_stage)
    confirmation = read_result(work / "evaluation" / f"{selected}-seed43", baseline,
                               work / "predictions" / f"{selected}-seed43.h5ad")
    if not (confirmation["score"] >= results[selected]["score"]-.01
            and confirmation["score"] >= incumbent["score"]):
        raise ValueError("Confirmation no longer satisfies the final stability gate")
    model = ReleasedPredictor(args, selected)
    fingerprint = {"effects_sha256": sha(model.table_path), "fit_sha256": sha(work / "fit.json"),
                   "checkpoint_sha256": sha(work / "state/final.pt") if selected == "state" else None,
                   "protocol_sha256": sha(args.previous / "protocol.json"),
                   "controls_sha256": sha(args.previous / "h1-benchmark/h1_controls.h5ad")}
    for seed, result in [(42, results[selected]), (43, confirmation)]:
        exported = json.loads((work / "predictions" / f"{selected}-seed{seed}.json").read_text())
        if (exported["arm"] != selected or exported["panel"] != "h1" or exported["seed"] != seed
                or exported["sha256"] != result["prediction_sha256"]
                or any(exported.get(k) != v for k, v in fingerprint.items())):
            raise ValueError("Scored prediction provenance differs from released model")
    return model, {"released": True, "selected_arm": selected, **fingerprint,
        "checkpoint_masks_sha256": sha(work / "state/masks.npz") if selected == "state" else None,
        "selection_sha256": sha(work / "final-selection.json"),
        "original_selection_sha256": sha(work / "selection.json") if (work / "selection.json").exists() else None,
        "summary_sha256": sha(work / "final-selection.json"),
        "first_seed": results[selected], "confirmation": confirmation,
        "submission_count_limit_this_round": 1,
        "user_authorization": "Finish this round, submit the best validated result to the leaderboard, then stop work.",
        "source_revision": args.revision, "recorded_at_unix": time.time()}


def run(args):
    if (args.work / "release.json").exists() or (args.work / "predictions/official.h5ad").exists():
        raise FileExistsError("Release/export exists; review its status rather than repeating")
    model, release = checked_release(args)
    protocol = model.protocol
    positions = {g: i for i, g in enumerate(protocol["genes"])}
    targets = sorted(pd.read_csv(args.previous / "h1-benchmark/benchmark/reference_cells.csv")["target_gene"].unique())
    if len(targets) != 126:
        raise ValueError("H1 target panel changed")
    selected = np.array([positions[g] for g in protocol["h1_genes"]])
    prediction_path = args.work / "predictions" / f"{model.arm}-seed42.h5ad"
    with h5py.File(args.previous / "h1-benchmark/h1_controls.h5ad") as ctrl, h5py.File(prediction_path) as pred:
        if list(gene_names(ctrl)) != protocol["h1_genes"] or list(gene_names(pred)) != protocol["h1_genes"]:
            raise ValueError("H1 gene axis mismatch")
        if h5_column(pred["obs"], "target_gene").tolist() != [t for t in targets for _ in range(400)]:
            raise ValueError("H1 prediction row identity changed")
        controls, scored = cache_controls(ctrl), cache_controls(pred)
        if controls is None or scored is None:
            raise ValueError("Replay inputs exceed declared resident bounds")
        for i, target in enumerate(targets):
            seed = zlib.crc32(f"h1-control-baseline-v1:{target}".encode())
            rows = np.sort(np.random.default_rng(seed).choice(controls.shape[0], 400, replace=False))
            raw = controls[rows]
            raw = raw.toarray() if sparse.issparse(raw) else np.asarray(raw)
            replay = model.predict(raw, selected, target, np.random.default_rng(zlib.crc32(f"42:{target}".encode())))
            expected = scored[i*400:(i+1)*400]
            expected = expected.toarray() if sparse.issparse(expected) else np.asarray(expected)
            if not np.array_equal(replay, expected):
                raise ValueError(f"Official exporter differs from scored H1 counts: {target}")
        del controls, scored, raw, expected, replay
    (args.work / "audit").mkdir(exist_ok=True)
    save_json(args.work / "audit/exporter-parity.json", {"h1_rows": 50400, "h1_genes": 18080,
        "all_counts_exact": True, "scored_prediction_sha256": release["first_seed"]["prediction_sha256"],
        "source_revision": args.revision, "scope": "Full deterministic replay of frozen predictions, not retraining or another scored experiment"})
    save_json(args.work / "release.json", release)
    genes, targets = protocol["official_genes"], protocol["official_targets"]
    if len(genes) != 18533 or len(targets) != 300 or len(set(targets)) != 300:
        raise ValueError("Official axes changed")
    selected = np.array([positions[g] for g in genes])
    contexts = []
    for context in ["A", "B", "C"]:
        paths = []
        for path in (args.previous / "controls").rglob("*.h5ad"):
            with h5py.File(path) as h:
                if set(h5_column(h["obs"], "context")) == {context}:
                    paths.append(path)
        if len(paths) != 1:
            raise ValueError("Ambiguous official control context")
        contexts.append((context, paths[0]))
    output = args.work / "predictions/official.h5ad"
    contract = {"arm": model.arm, "panel": "abc", "decoding_seed": 42,
                "effects_sha256": release["effects_sha256"], "fit_sha256": release["fit_sha256"],
                "checkpoint_sha256": release["checkpoint_sha256"],
                "release_sha256": sha(args.work / "release.json"), "source_revision": args.revision,
                "controls_sha256": {c: sha(p) for c, p in contexts},
                "prior_strength": .5, "residual_strength": .1 if model.arm == "state" else 0}
    writer = Writer(output, genes, [{"context": c, "target_gene": t} for c, _ in contexts for t in targets for _ in range(400)], contract=contract)
    for context, path in contexts:
        with h5py.File(path) as h:
            if list(gene_names(h)) != genes:
                raise ValueError("Official control gene axis mismatch")
            controls = cache_controls(h)
            if controls is None:
                raise ValueError("Official controls exceed resident bound")
            for i, target in enumerate(targets):
                seed = int.from_bytes(hashlib.sha256(f"42:{context}:{target}".encode()).digest()[:8], "little")
                rows = templates(h, np.random.default_rng(seed))[:400]
                raw = controls[rows]
                raw = raw.toarray() if sparse.issparse(raw) else np.asarray(raw)
                seed = int.from_bytes(hashlib.sha256(f"42:{context}:{target}:decode".encode()).digest()[:8], "little")
                writer.append(model.predict(raw, selected, target, np.random.default_rng(seed)))
                if (i+1) % 25 == 0:
                    print(json.dumps({"context": context, "targets": i+1, "rows": writer.row}), flush=True)
            del controls
    result = writer.finish()
    result.update(contract, sha256=sha(output))
    save_json(output.with_suffix(".json"), result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--incumbent", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("/mnt/e/vcc2026-data"))
    parser.add_argument("--revision", required=True)
    run(parser.parse_args())
