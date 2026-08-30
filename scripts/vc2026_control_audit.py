# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "anndata>=0.13,<0.14",
#   "matplotlib>=3.10,<3.11",
#   "numpy>=2.5,<3",
#   "pandas>=3,<4",
#   "scipy>=1.18,<2",
# ]
# ///

"""Audit VC2026 validation controls and draw a reproducible teaching figure.

Figure contract
---------------
Results-level question:
    Are contexts A/B/C comparably sequenced yet distinguishable as expression
    backgrounds, rather than merely three arbitrary labels?
Evidence chain:
    a. Cell-level total UMI distribution controls sequencing depth.
    b. Detected-gene distribution measures observed library complexity.
    c. Guide-level pseudobulk PCA tests whether context separation exceeds
       within-context NTC-guide variation.
Data integrity:
    All 55,200 cells and all 18,533 genes are used. No cells, guides, or genes
    are filtered from the summaries or PCA.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import anndata as ad
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

# Mandatory editable-text settings from the project figure contract.
plt.switch_backend("Agg")
plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans", "Liberation Sans"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 7,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
    }
)

CONTEXTS = ("A", "B", "C")
COLORS = {"A": "#167B72", "B": "#3E71AD", "C": "#DC654F"}
EXPECTED_CELLS = 18_400
EXPECTED_GENES = 18_533
EXPECTED_NTC_IDS = 46
EXPECTED_CELLS_PER_NTC = 400
RASTER_DPI = 300


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit VC2026 A/B/C controls and render a teaching figure."
    )
    parser.add_argument(
        "--controls-dir",
        type=Path,
        default=Path("data/vcc2026-validation/controls"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/vc2026-control-audit"),
    )
    parser.add_argument("--chunk-size", type=int, default=512)
    parser.add_argument("--dpi", type=int, default=RASTER_DPI)
    return parser.parse_args()


def load_contract(controls_dir: Path) -> tuple[list[str], list[str]]:
    gene_frame = pd.read_csv(controls_dir / "gene_names.csv")
    pert_frame = pd.read_csv(controls_dir / "pert_counts.csv")
    if gene_frame.columns.tolist() != ["gene_name"]:
        raise ValueError(
            f"Unexpected gene_names.csv columns: {gene_frame.columns.tolist()}"
        )
    if pert_frame.columns.tolist() != ["target_gene"]:
        raise ValueError(
            f"Unexpected pert_counts.csv columns: {pert_frame.columns.tolist()}"
        )

    genes = gene_frame["gene_name"].astype(str).tolist()
    targets = pert_frame["target_gene"].astype(str).tolist()
    if len(genes) != EXPECTED_GENES or len(set(genes)) != EXPECTED_GENES:
        raise ValueError("gene_names.csv must contain 18,533 unique genes")
    if len(targets) != 300 or len(set(targets)) != 300:
        raise ValueError("pert_counts.csv must contain 300 unique targets")
    if missing := sorted(set(targets).difference(genes)):
        raise ValueError(f"Targets missing from gene list: {missing}")
    return genes, targets


def scan_context(
    path: Path,
    context: str,
    genes: list[str],
    chunk_size: int,
) -> tuple[pd.DataFrame, np.ndarray, list[str], dict[str, object]]:
    data = ad.read_h5ad(path, backed="r")
    try:
        if data.shape != (EXPECTED_CELLS, EXPECTED_GENES):
            raise ValueError(f"{path.name}: unexpected shape {data.shape}")
        if data.var_names.astype(str).tolist() != genes:
            raise ValueError(
                f"{path.name}: gene names/order do not match gene_names.csv"
            )

        required_obs = {"target_gene", "context", "ntc_id"}
        if missing := sorted(required_obs.difference(data.obs.columns)):
            raise ValueError(f"{path.name}: missing obs columns {missing}")

        target_values = set(data.obs["target_gene"].astype(str))
        context_values = set(data.obs["context"].astype(str))
        if target_values != {"non-targeting"}:
            raise ValueError(
                f"{path.name}: unexpected target_gene values {target_values}"
            )
        if context_values != {context}:
            raise ValueError(f"{path.name}: unexpected context values {context_values}")

        ntc_values = data.obs["ntc_id"].astype(str).to_numpy()
        ntc_ids = sorted(pd.unique(ntc_values).tolist())
        ntc_counts = pd.Series(ntc_values).value_counts()
        if len(ntc_ids) != EXPECTED_NTC_IDS:
            raise ValueError(f"{path.name}: expected 46 ntc_id values")
        if set(ntc_counts.astype(int)) != {EXPECTED_CELLS_PER_NTC}:
            raise ValueError(f"{path.name}: expected 400 cells per ntc_id")

        ntc_index = {ntc_id: index for index, ntc_id in enumerate(ntc_ids)}
        pseudobulk = np.zeros((len(ntc_ids), data.n_vars), dtype=np.float64)
        qc_parts: list[pd.DataFrame] = []

        stored_entries = 0
        explicit_zeros = 0
        all_finite = True
        all_nonnegative = True
        all_integral = True
        max_gene_count = 0.0

        for start in range(0, data.n_obs, chunk_size):
            stop = min(start + chunk_size, data.n_obs)
            block = data.X[start:stop].tocsr()
            values = block.data
            stored_entries += int(values.size)
            explicit_zeros += int(np.count_nonzero(values == 0))
            all_finite &= bool(np.isfinite(values).all())
            all_nonnegative &= bool((values >= 0).all())
            all_integral &= bool(np.equal(values, np.floor(values)).all())
            if values.size:
                max_gene_count = max(max_gene_count, float(values.max()))

            row_totals = np.asarray(block.sum(axis=1)).ravel()
            detected_genes = np.diff(block.indptr)
            block_ntc = ntc_values[start:stop]
            qc_parts.append(
                pd.DataFrame(
                    {
                        "cell_id": data.obs_names[start:stop].astype(str),
                        "context": context,
                        "ntc_id": block_ntc,
                        "total_umi": row_totals.astype(np.int64),
                        "detected_genes": detected_genes.astype(np.int32),
                    }
                )
            )

            for ntc_id in pd.unique(block_ntc):
                rows = np.flatnonzero(block_ntc == ntc_id)
                pseudobulk[ntc_index[ntc_id]] += np.asarray(
                    block[rows].sum(axis=0)
                ).ravel()

        qc = pd.concat(qc_parts, ignore_index=True)
        audit = {
            "context": context,
            "cells": int(data.n_obs),
            "genes": int(data.n_vars),
            "ntc_ids": len(ntc_ids),
            "cells_per_ntc_min": int(ntc_counts.min()),
            "cells_per_ntc_max": int(ntc_counts.max()),
            "x_storage": type(data.X).__name__,
            "x_dtype": str(data.X.dtype),
            "stored_entries": stored_entries,
            "explicit_zeros": explicit_zeros,
            "finite": all_finite,
            "nonnegative": all_nonnegative,
            "integral_values": all_integral,
            "max_gene_count": int(max_gene_count),
            "median_umi": float(qc["total_umi"].median()),
            "q1_umi": float(qc["total_umi"].quantile(0.25)),
            "q3_umi": float(qc["total_umi"].quantile(0.75)),
            "median_detected_genes": float(qc["detected_genes"].median()),
            "q1_detected_genes": float(qc["detected_genes"].quantile(0.25)),
            "q3_detected_genes": float(qc["detected_genes"].quantile(0.75)),
            "matrix_density": stored_entries / (data.n_obs * data.n_vars),
        }
        if not (all_finite and all_nonnegative and all_integral):
            raise ValueError(f"{path.name}: X violates raw-count requirements")
        if explicit_zeros:
            raise ValueError(
                f"{path.name}: sparse X stores {explicit_zeros} explicit zeros"
            )
        return qc, pseudobulk, ntc_ids, audit
    finally:
        data.file.close()


def calculate_pca(pseudobulk: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    library_sizes = pseudobulk.sum(axis=1)
    if np.any(library_sizes <= 0):
        raise ValueError("Pseudobulk sample with zero total count")
    log_cpm = np.log1p(pseudobulk / library_sizes[:, None] * 1_000_000)
    centered = log_cpm - log_cpm.mean(axis=0, keepdims=True)
    u, singular_values, _ = np.linalg.svd(centered, full_matrices=False)
    scores = u[:, :2] * singular_values[:2]
    explained = singular_values**2 / np.sum(singular_values**2)
    return scores, explained[:2]


def calculate_pca_separation(pca: pd.DataFrame) -> dict[str, dict[str, float]]:
    centroids = pca.groupby("context")[["pc1", "pc2"]].mean()
    result: dict[str, dict[str, float]] = {}
    for context in CONTEXTS:
        points = pca.loc[pca["context"] == context, ["pc1", "pc2"]].to_numpy()
        centroid = centroids.loc[context].to_numpy()
        within = np.linalg.norm(points - centroid, axis=1)
        rms_within = float(np.sqrt(np.mean(within**2)))
        other_centroids = centroids.drop(index=context).to_numpy()
        nearest_centroid = float(
            np.min(np.linalg.norm(other_centroids - centroid, axis=1))
        )
        result[context] = {
            "rms_within_context": rms_within,
            "max_within_context": float(np.max(within)),
            "nearest_context_centroid": nearest_centroid,
            "nearest_centroid_over_rms": nearest_centroid / rms_within,
        }
    return result


def add_panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.14,
        1.04,
        label,
        transform=ax.transAxes,
        fontsize=10,
        fontweight="bold",
        ha="left",
        va="bottom",
    )


def draw_distribution_panel(
    ax: plt.Axes,
    qc: pd.DataFrame,
    guide_summary: pd.DataFrame,
    column: str,
    guide_column: str,
    ylabel: str,
    show_reference: bool = False,
) -> None:
    arrays = [
        qc.loc[qc["context"] == context, column].to_numpy() for context in CONTEXTS
    ]
    violins = ax.violinplot(
        arrays,
        positions=np.arange(len(CONTEXTS)),
        widths=0.72,
        showmeans=False,
        showmedians=False,
        showextrema=False,
        bw_method=0.18,
    )
    for body, context in zip(violins["bodies"], CONTEXTS, strict=True):
        body.set_facecolor(COLORS[context])
        body.set_edgecolor(COLORS[context])
        body.set_alpha(0.18)
        body.set_linewidth(0.8)

    for x_position, context in enumerate(CONTEXTS):
        values = guide_summary.loc[
            guide_summary["context"] == context, guide_column
        ].to_numpy()
        jitter = np.linspace(-0.16, 0.16, num=values.size)
        ax.scatter(
            x_position + jitter,
            values,
            s=9,
            color=COLORS[context],
            alpha=0.72,
            linewidths=0,
            rasterized=True,
            zorder=3,
        )
        median = float(qc.loc[qc["context"] == context, column].median())
        ax.scatter(
            x_position,
            median,
            marker="D",
            s=25,
            facecolor="white",
            edgecolor=COLORS[context],
            linewidth=1.1,
            zorder=4,
        )
        ax.annotate(
            f"{median:,.0f}",
            (x_position, median),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            va="bottom",
            color=COLORS[context],
            fontsize=6.5,
            fontweight="bold",
        )

    if show_reference:
        ax.axhline(20_000, color="#767676", lw=0.8, ls=(0, (3, 2)), zorder=0)
        ax.text(
            0.02,
            0.95,
            "Dashed line: official median reference ≈20,000",
            transform=ax.transAxes,
            ha="left",
            va="top",
            color="#666666",
            fontsize=5.8,
        )

    ax.set_xticks(np.arange(len(CONTEXTS)), CONTEXTS)
    ax.set_xlabel("Context")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", color="#D8DEDC", linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))


def draw_figure(
    qc: pd.DataFrame,
    guide_summary: pd.DataFrame,
    pca: pd.DataFrame,
    explained: np.ndarray,
    separation: dict[str, dict[str, float]],
    output_dir: Path,
    dpi: int,
) -> list[Path]:
    fig = plt.figure(figsize=(7.09, 4.25))
    grid = fig.add_gridspec(
        2,
        2,
        width_ratios=(0.93, 1.42),
        height_ratios=(1, 1),
        left=0.09,
        right=0.985,
        bottom=0.17,
        top=0.88,
        wspace=0.34,
        hspace=0.48,
    )
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[1, 0])
    ax_c = fig.add_subplot(grid[:, 1])

    draw_distribution_panel(
        ax_a,
        qc,
        guide_summary,
        column="total_umi",
        guide_column="median_umi",
        ylabel="Total UMI per cell",
        show_reference=True,
    )
    draw_distribution_panel(
        ax_b,
        qc,
        guide_summary,
        column="detected_genes",
        guide_column="median_detected_genes",
        ylabel="Detected genes per cell",
    )

    ax_c.axhline(0, color="#D8DEDC", lw=0.7, zorder=0)
    ax_c.axvline(0, color="#D8DEDC", lw=0.7, zorder=0)
    for context in CONTEXTS:
        subset = pca.loc[pca["context"] == context]
        ax_c.scatter(
            subset["pc1"],
            subset["pc2"],
            s=9,
            color=COLORS[context],
            alpha=0.82,
            edgecolor="none",
        )
        centroid = subset[["pc1", "pc2"]].mean().to_numpy()
        pc1_min, pc1_max = float(subset["pc1"].min()), float(subset["pc1"].max())
        pc2_min, pc2_max = float(subset["pc2"].min()), float(subset["pc2"].max())
        ax_c.errorbar(
            centroid[0],
            centroid[1],
            xerr=np.array([[centroid[0] - pc1_min], [pc1_max - centroid[0]]]),
            yerr=np.array([[centroid[1] - pc2_min], [pc2_max - centroid[1]]]),
            fmt="D",
            markersize=4.2,
            color=COLORS[context],
            markeredgecolor="#182A31",
            markeredgewidth=0.6,
            elinewidth=0.8,
            capsize=2,
            zorder=4,
        )
        ax_c.annotate(
            context,
            centroid,
            xytext=(7, 5),
            textcoords="offset points",
            color=COLORS[context],
            fontsize=9,
            fontweight="bold",
        )
    ax_c.set_xlabel(f"PC1 ({explained[0] * 100:.1f}% variance)")
    ax_c.set_ylabel(f"PC2 ({explained[1] * 100:.1f}% variance)")
    ax_c.set_title(
        "NTC-guide pseudobulk PCA", loc="left", fontsize=8.5, fontweight="bold"
    )
    separation_ratios = [
        separation[context]["nearest_centroid_over_rms"] for context in CONTEXTS
    ]
    ax_c.text(
        0.51,
        0.54,
        "Nearest context centroid / guide-level RMS spread\n"
        f"= {min(separation_ratios):.0f}–{max(separation_ratios):.0f}×",
        transform=ax_c.transAxes,
        ha="center",
        va="center",
        color="#182A31",
        fontsize=6.2,
        linespacing=1.35,
        bbox={
            "boxstyle": "square,pad=0.35",
            "facecolor": "white",
            "edgecolor": "#C9D5D3",
        },
    )
    ax_c.text(
        0.01,
        0.01,
        "log1p CPM; all 18,533 genes; each point = 400 cells\n"
        "46 guide points per context overlap at this global scale",
        transform=ax_c.transAxes,
        ha="left",
        va="bottom",
        color="#5D7076",
        fontsize=5.8,
    )

    add_panel_label(ax_a, "a")
    add_panel_label(ax_b, "b")
    add_panel_label(ax_c, "c")
    fig.suptitle(
        "VC2026 controls: comparable median depth, distinct expression backgrounds",
        x=0.09,
        y=0.965,
        ha="left",
        fontsize=10,
        fontweight="bold",
    )
    fig.text(
        0.09,
        0.035,
        "Cell-level violins use all 18,400 cells per context; dots show 46 NTC-guide medians; diamonds show context medians.",
        ha="left",
        va="bottom",
        fontsize=5.8,
        color="#5D7076",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    base = output_dir / "validation-control-audit"
    outputs = [base.with_suffix(suffix) for suffix in (".svg", ".pdf", ".png")]
    fig.savefig(outputs[0])
    fig.savefig(outputs[1])
    fig.savefig(outputs[2], dpi=dpi)
    plt.close(fig)
    return outputs


def main() -> None:
    args = parse_args()
    genes, targets = load_contract(args.controls_dir)

    qc_parts: list[pd.DataFrame] = []
    pseudobulk_parts: list[np.ndarray] = []
    pseudobulk_meta: list[dict[str, str]] = []
    audits: list[dict[str, object]] = []
    for context in CONTEXTS:
        qc, pseudobulk, ntc_ids, audit = scan_context(
            args.controls_dir / f"context_{context}.h5ad",
            context,
            genes,
            args.chunk_size,
        )
        qc_parts.append(qc)
        pseudobulk_parts.append(pseudobulk)
        pseudobulk_meta.extend(
            {"context": context, "ntc_id": ntc_id} for ntc_id in ntc_ids
        )
        audits.append(audit)

    qc = pd.concat(qc_parts, ignore_index=True)
    guide_summary = (
        qc.groupby(["context", "ntc_id"], observed=True)
        .agg(
            n_cells=("cell_id", "size"),
            median_umi=("total_umi", "median"),
            q1_umi=("total_umi", lambda values: values.quantile(0.25)),
            q3_umi=("total_umi", lambda values: values.quantile(0.75)),
            median_detected_genes=("detected_genes", "median"),
            q1_detected_genes=("detected_genes", lambda values: values.quantile(0.25)),
            q3_detected_genes=("detected_genes", lambda values: values.quantile(0.75)),
        )
        .reset_index()
    )

    pseudobulk_matrix = np.vstack(pseudobulk_parts)
    scores, explained = calculate_pca(pseudobulk_matrix)
    pca = pd.DataFrame(pseudobulk_meta)
    pca["pc1"] = scores[:, 0]
    pca["pc2"] = scores[:, 1]
    separation = calculate_pca_separation(pca)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    qc.to_csv(args.output_dir / "cell-qc.csv", index=False)
    guide_summary.to_csv(args.output_dir / "ntc-guide-summary.csv", index=False)
    pca.to_csv(args.output_dir / "pseudobulk-pca.csv", index=False)
    summary = {
        "contract": {
            "genes": len(genes),
            "targets": len(targets),
            "contexts": list(CONTEXTS),
            "cells_total": len(qc),
            "pseudobulk_samples": len(pca),
            "pca_genes": len(genes),
            "pca_transform": "sum 400 cells per context x ntc_id; CPM; log1p; mean-center",
            "pca_explained_variance": {
                "pc1": float(explained[0]),
                "pc2": float(explained[1]),
            },
            "pca_separation": separation,
        },
        "contexts": audits,
    }
    (args.output_dir / "audit-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    outputs = draw_figure(
        qc,
        guide_summary,
        pca,
        explained,
        separation,
        args.output_dir,
        args.dpi,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    for output in outputs:
        print(f"wrote {output}")


if __name__ == "__main__":
    main()
