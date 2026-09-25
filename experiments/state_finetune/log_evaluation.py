"""Archive canonical H1 raw/scaled metrics and show them in SwanLab."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import swanlab

METRICS = {
    "pds_cosine": "PDS",
    "expr_mse_unbiased_capped_norm": "MSE",
    "de_wilcoxon_lfc_nmae": "NMAE",
    "de_wilcoxon_direction_fidelity_yield_raw": "FID",
    "de_wilcoxon_direction_reach_raw": "REACH",
    "de_wilcoxon_sig_jaccard": "JAC",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    path = args.result / "scores.csv"
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    marker = args.result / "swanlab-record.json"
    if marker.exists() and json.loads(marker.read_text())["scores_sha256"] == checksum:
        print("This score artifact is already recorded")
        return
    scores = pd.read_csv(path).set_index("metric")
    raw = pd.read_csv(args.result / "aggregates.csv").set_index("metric")
    if "from_replicate" not in scores.columns:
        raise ValueError(f"Expected replicate-anchored scores, found {list(scores.columns)}")
    scaled = {label: float(scores.loc[key, "from_replicate"]) for key, label in METRICS.items()}
    scaled["avg_score"] = float(scores.loc["avg_score", "from_replicate"])
    if not all(np.isfinite(value) for value in scaled.values()):
        raise ValueError("H1 score contains non-finite metrics")
    raw_values = {label: float(raw.loc[key, "raw_value"]) for key, label in METRICS.items()}
    summary = {"label": args.label, "panel": "H1 canonical 126 targets", "scaled_column": "from_replicate",
               "scaled": scaled, "raw": raw_values, "scores_sha256": checksum,
               "official_leaderboard_score": False}
    (args.result / "summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    swanlab.init(project="virtual-cell-2026", experiment_name=f"H1-{args.label}",
                 group="H1-evaluation", job_type="evaluation", mode="local",
                 logdir=str(args.work / "swanlog"), config={"panel": summary["panel"],
                 "scores_sha256": checksum, "scaled_column": "from_replicate"})
    swanlab.log({**{f"H1/scaled/{key}": value for key, value in scaled.items()},
                 **{f"H1/raw/{key}": value for key, value in raw_values.items()}}, step=0)
    swanlab.finish()
    marker.write_text(json.dumps({"scores_sha256": checksum, "label": args.label})+"\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
