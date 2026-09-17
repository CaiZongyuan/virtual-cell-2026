# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "anndata>=0.11",
#   "numpy>=1.26",
#   "pandas>=2.2",
#   "scipy>=1.11",
# ]
# ///

"""Measure the VC2026 control-cell noise floor with two independent estimators.

What this script measures
-------------------------
「噪声地板」不是一个模型误差，而是**测量与抽样本身的误差下限**。它回答一个问题：

    在同一批对照细胞里，两个互不相交的 N 细胞样本之间的差异有多大？

这个差异**不是任何模型的错**：真值本身也只是某一次 N 细胞抽样的结果，因此任何
预测与真值的差距都不可能稳定小于它。本脚本用两种互不相同的口径估计它，
并给出把数字放回比赛尺度所需的分母。

口径 A —— 重采样 / 半集重复（resampling）
    从同一背景的对照细胞里反复抽取两个不相交的 N 细胞组，比较它们的群体表达谱。
    它直接测量「N 细胞这个样本量带来的抽样波动」，并用 delete-one jackknife
    给出一个不依赖具体抽样的无偏估计。这是**上地板**：真实差距至少会有这么大。

口径 B —— 置换零分布（permutation）
    把细胞在两个组之间随机重新分配，得到「两组之间没有真实差异」时该统计量的
    分布。它给出**判定阈值**：观测差异要超过这个分布的高端，才不能被抽样噪声解释。

为什么需要分母
--------------
平方距离本身没有单位。为了能说「这个噪声有多大」，本脚本同时测量**背景间距离**
``||b_A - b_B||^2``，把噪声表达成「从一个背景走到另一个背景的百分之多少」。
背景间距离是这批数据里唯一已知的、量级远大于噪声的真实生物差异，因此它是最自然
的尺子。它**不等于**扰动效应的量级——这一点在课文里单列为一节，不能混淆。

口径 A 与口径 B 测的东西不同，不要互相替代：A 给的是「噪声有多大」，B 给的是
「多大的差异才算超出噪声」。

输出
----
``output/noise-floor/`` 下的 ``noise_floor_results.json``、``noise_floor_table.csv``
和打印到 stdout 的 Markdown 表。所有数字都带测量条件、重复次数和波动范围。

Usage
-----
    python scripts/vc2026_noise_floor.py                       # 默认 N=400, R=200
    python scripts/vc2026_noise_floor.py --n-cells 400 --repeats 400
    python scripts/vc2026_noise_floor.py --sizes 100,200,400,800
"""

from __future__ import annotations

import os

# 必须在 import h5py / anndata 之前设置：Windows 侧经 9p 访问 WSL 仓库时，
# HDF5 的文件锁会失败（OSError: unable to lock file）。
os.environ.setdefault("HDF5_USE_FILE_LOCKING", "FALSE")

import argparse
import json
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "vcc2026-validation" / "controls"
OUT = ROOT / "output" / "noise-floor"

TARGET_SUM = 50_000.0  # 与 cell-eval2 vcc2026 preset 的伪批量归一化目标一致
CONTEXTS = ("A", "B", "C")


# --------------------------------------------------------------------------
# 群体表达谱：与 L3-01 §1 的三步一致（按基因求和 -> 归一化到 50,000 -> log1p）
# --------------------------------------------------------------------------
def pseudobulk_profile(counts: np.ndarray) -> np.ndarray:
    """counts: (cells, genes) 的原始计数 -> (genes,) 的群体表达谱。"""
    s = np.asarray(counts.sum(axis=0), dtype=np.float64).ravel()
    total = s.sum()
    if total <= 0:
        raise ValueError("空组：该细胞组的总计数为 0")
    return np.log1p(TARGET_SUM * s / total)


def jackknife_var_trace(counts: np.ndarray) -> float:
    """delete-one jackknife 估计群体表达谱自身的抽样方差迹。

    设 b_(-c) 是删掉第 c 个细胞后重算的群体表达谱，b_bar 是它们的均值，则
    估计量 Var_trace = ((n-1)/n) * sum_c ||b_(-c) - b_bar||^2。
    两个独立同大小细胞组的期望平方距离 = 2 * Var_trace。

    这正是 cell-eval2 全表达谱误差里 `unbiased` 那一项做的事：把「只因这次抽到了
    哪些细胞」带来的距离从分子里扣掉。本脚本把它单独拿出来当地板用。
    """
    x = counts
    if sparse.issparse(x):
        x = x.toarray()
    x = np.asarray(x, dtype=np.float64)
    n = x.shape[0]
    if n < 3:
        raise ValueError("jackknife 需要至少 3 个细胞")
    total = x.sum(axis=0)
    sum_sq = 0.0
    acc = np.zeros(x.shape[1], dtype=np.float64)
    for i in range(n):
        s_minus = total - x[i]
        t = s_minus.sum()
        b = np.log1p(TARGET_SUM * s_minus / t)
        sum_sq += float(b @ b)
        acc += b
    b_bar = acc / n
    return float((n - 1) / n * (sum_sq - n * float(b_bar @ b_bar)))


def sqdist(a: np.ndarray, b: np.ndarray) -> float:
    d = a - b
    return float(d @ d)


# --------------------------------------------------------------------------
# 主测量
# --------------------------------------------------------------------------
def load_context(ctx: str):
    path = DATA / f"context_{ctx}.h5ad"
    if not path.exists():
        raise FileNotFoundError(f"缺少 {path}；请先解压 data/vcc2026-validation/controls/")
    adata = ad.read_h5ad(path)
    x = adata.X
    if not sparse.issparse(x):
        x = sparse.csr_matrix(x)
    return adata, x.tocsr()


def measure_context(ctx: str, adata, x, n_cells: int, repeats: int, seed: int):
    rng = np.random.default_rng(seed + ord(ctx))
    n_total = x.shape[0]

    # 全量群体表达谱：几乎不含抽样噪声，用作该背景的「参考谱」
    prof_full = pseudobulk_profile(x[:])
    var_full = jackknife_var_trace(x[:])

    # ---- 口径 A：重采样 / 半集重复 ---------------------------------------
    dists = np.empty(repeats, dtype=np.float64)
    var_hats = np.empty(repeats, dtype=np.float64)
    corrs = np.empty(repeats, dtype=np.float64)
    for r in range(repeats):
        idx = rng.choice(n_total, size=2 * n_cells, replace=False)
        g1, g2 = idx[:n_cells], idx[n_cells:]
        b1 = pseudobulk_profile(x[g1])
        b2 = pseudobulk_profile(x[g2])
        dists[r] = sqdist(b1, b2)
        var_hats[r] = jackknife_var_trace(x[g1])
        corrs[r] = float(np.corrcoef(b1, b2)[0, 1])

    two_var = 2.0 * var_hats  # jackknife 对「两组间期望平方距离」的预测

    # ---- 口径 B：置换零分布 ----------------------------------------------
    # 把细胞在两个组之间随机重新分配。这破坏了「两组有任何系统差异」的可能，
    # 因此得到的分布就是纯抽样噪声的分布。
    perm_dists = np.empty(repeats, dtype=np.float64)
    for r in range(repeats):
        idx = rng.choice(n_total, size=2 * n_cells, replace=False)
        g1, g2 = idx[:n_cells], idx[n_cells:]
        perm_dists[r] = sqdist(pseudobulk_profile(x[g1]), pseudobulk_profile(x[g2]))

    return {
        "context": ctx,
        "n_total_cells": int(n_total),
        "n_genes": int(x.shape[1]),
        "n_cells_per_group": int(n_cells),
        "repeats": int(repeats),
        "seed": int(seed),
        "dist_mean": float(dists.mean()),
        "dist_std": float(dists.std(ddof=1)),
        "dist_p05": float(np.percentile(dists, 5)),
        "dist_p95": float(np.percentile(dists, 95)),
        "jackknife_two_var_mean": float(two_var.mean()),
        "jackknife_two_var_std": float(two_var.std(ddof=1)),
        "naive_pearson_mean": float(corrs.mean()),
        "naive_pearson_min": float(corrs.min()),
        "perm_dist_mean": float(perm_dists.mean()),
        "perm_dist_p95": float(np.percentile(perm_dists, 95)),
        "perm_dist_p99": float(np.percentile(perm_dists, 99)),
        "var_full_context": float(var_full),
        "_profile": prof_full,
    }


def scaling_curve(x, sizes, repeats, seed):
    """抽样方差随细胞数的 1/n 缩放检验。"""
    rng = np.random.default_rng(seed + 7919)
    n_total = x.shape[0]
    rows = []
    for n in sizes:
        if n * 2 > n_total:
            continue
        vs = np.empty(repeats, dtype=np.float64)
        for r in range(repeats):
            idx = rng.choice(n_total, size=n, replace=False)
            vs[r] = jackknife_var_trace(x[idx])
        rows.append({
            "n_cells": int(n),
            "var_trace_mean": float(vs.mean()),
            "var_trace_std": float(vs.std(ddof=1)),
            "two_var_mean": float(2 * vs.mean()),
            "rms_per_gene": float(np.sqrt(2 * vs.mean() / x.shape[1])),
            "repeats": int(repeats),
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="VC2026 对照细胞噪声地板测量")
    ap.add_argument("--n-cells", type=int, default=400,
                    help="每组的细胞数，默认 400（与比赛每个靶点的细胞数一致）")
    ap.add_argument("--repeats", type=int, default=200, help="重采样 / 置换重复次数")
    ap.add_argument("--sizes", type=str, default="100,200,400,800,1600",
                    help="缩放曲线使用的细胞数列表")
    ap.add_argument("--seed", type=int, default=20260917)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    sizes = [int(s) for s in args.sizes.split(",") if s.strip()]

    results = {}
    profiles = {}
    for ctx in CONTEXTS:
        adata, x = load_context(ctx)
        res = measure_context(ctx, adata, x, args.n_cells, args.repeats, args.seed)
        profiles[ctx] = res.pop("_profile")
        res["scaling"] = scaling_curve(x, sizes, max(20, args.repeats // 5), args.seed)
        res["obs_columns"] = list(map(str, adata.obs.columns))
        results[ctx] = res
        print(f"[{ctx}] cells={res['n_total_cells']} genes={res['n_genes']} "
              f"dist={res['dist_mean']:.2f}±{res['dist_std']:.2f} "
              f"2*Var={res['jackknife_two_var_mean']:.2f} "
              f"pearson={res['naive_pearson_mean']:.5f}")
        del adata, x

    # ---- 分母：背景间距离（同样做 jackknife 无偏化） ----------------------
    pairs = {}
    for a, b in (("A", "B"), ("A", "C"), ("B", "C")):
        d = sqdist(profiles[a], profiles[b])
        d_unb = d - results[a]["var_full_context"] - results[b]["var_full_context"]
        pairs[f"{a}-{b}"] = {"sqdist": float(d), "sqdist_unbiased": float(d_unb),
                             "rms_per_gene": float(np.sqrt(d_unb / results[a]["n_genes"]))}

    ref = float(np.median([p["sqdist_unbiased"] for p in pairs.values()]))

    rows = []
    for ctx, res in results.items():
        floor = res["jackknife_two_var_mean"]
        rows.append({
            "背景": ctx,
            "每组细胞数": res["n_cells_per_group"],
            "重复次数": res["repeats"],
            "半集平方距离 均值": round(res["dist_mean"], 2),
            "半集平方距离 标准差": round(res["dist_std"], 2),
            "半集平方距离 5–95%": f"{res['dist_p05']:.1f}–{res['dist_p95']:.1f}",
            "jackknife 2·Var 均值": round(floor, 2),
            "jackknife 2·Var 标准差": round(res["jackknife_two_var_std"], 2),
            "置换零分布 均值": round(res["perm_dist_mean"], 2),
            "置换零分布 95% 分位": round(res["perm_dist_p95"], 2),
            "置换零分布 99% 分位": round(res["perm_dist_p99"], 2),
            "朴素 Pearson 均值": round(res["naive_pearson_mean"], 5),
            "地板 / 背景间距离": round(floor / ref, 5),
            "地板 RMS / 基因": round(np.sqrt(floor / res["n_genes"]), 5),
        })

    df = pd.DataFrame(rows)
    pair_df = pd.DataFrame([
        {"背景对": k, "平方距离": round(v["sqdist"], 2),
         "无偏平方距离": round(v["sqdist_unbiased"], 2),
         "RMS / 基因": round(v["rms_per_gene"], 5)}
        for k, v in pairs.items()
    ])
    scale_df = pd.DataFrame([
        dict(背景=ctx, **{k: (round(v, 5) if isinstance(v, float) else v)
                          for k, v in row.items()})
        for ctx, res in results.items() for row in res["scaling"]
    ])

    payload = {
        "measured_at": pd.Timestamp.now("UTC").isoformat(),
        "config": {"n_cells_per_group": args.n_cells, "repeats": args.repeats,
                   "seed": args.seed, "target_sum": TARGET_SUM},
        "per_context": {k: {kk: vv for kk, vv in v.items() if kk != "scaling"}
                        for k, v in results.items()},
        "across_context_pairs": pairs,
        "reference_scale_median": ref,
        "scaling": {k: v["scaling"] for k, v in results.items()},
    }
    (OUT / "noise_floor_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    df.to_csv(OUT / "noise_floor_table.csv", index=False, encoding="utf-8")
    pair_df.to_csv(OUT / "noise_floor_scale.csv", index=False, encoding="utf-8")
    scale_df.to_csv(OUT / "noise_floor_scaling.csv", index=False, encoding="utf-8")

    print("\n## 口径 A / B 结果（每组 %d 细胞，%d 次重复）" % (args.n_cells, args.repeats))
    print(df.to_markdown(index=False))
    print("\n## 分母：背景间群体表达谱距离")
    print(pair_df.to_markdown(index=False))
    print("\n## 抽样方差随细胞数的缩放")
    print(scale_df.to_markdown(index=False))
    print(f"\n参考尺度（三对背景的中位数，无偏平方距离）= {ref:.2f}")
    for ctx, res in results.items():
        ratio = res["jackknife_two_var_mean"] / ref
        print(f"  {ctx}: 地板 = {ratio * 100:.2f}% 的背景间距离"
              f"（sqrt 口径 {np.sqrt(ratio) * 100:.2f}%）")
    print(f"\n产物：{OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
