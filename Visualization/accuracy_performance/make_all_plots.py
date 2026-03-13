#!/usr/bin/env python3
"""
Generate publication-ready plots for model accuracy vs. training time,
with consistent colors/markers across figures.

Notes:
  - Matplotlib 3.9.2
  - NumPy 1.26.4
"""

__author__ = "Michael A. Nuttall"
__date__ = "2025/09/10"
__license__ = "MIT"
__version__ = "0.5.0"

import math
from pathlib import Path
import colorsys
import numpy as np

import matplotlib
matplotlib.use("Agg")  # render-to-file (no GUI)
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib import colormaps

# ---- CONFIG ----
FILES = [
    "UAVATTACK_Results_filtered.csv",
    "2D_Results_filtered.csv",
]
OUTDIR = Path("plots_out")
OUTDIR.mkdir(parents=True, exist_ok=True)

# Color assignment policy: "model" (unique per model label) or "family"
COLOR_BY = "model"   # <-- switch to "family" if prefer one color per family

# Figure/legend
FIGSIZE = (10.5, 6.5)
PNG_DPI = 300
MARKER_SIZE = 5.2
AX_MARGIN_XY = 0.08
FONTS = {"axes.labelsize": 10, "axes.titlesize": 10,
         "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 9}
plt.rcParams.update(FONTS)


# ---- Abbreviations / families / dataset shortnames ----
def normalize_label(name: str) -> str:
    n = (name or "").strip()
    mapping = {
        "Logistic Regression": "LR",
        "Logistic Regression (SMOTE)": "LR+SM",
        "Logistic Regression (Explainability Features)": "LR+EXPL",
        "Logistic Regression (Xgboost Features)": "LR+XGBF",
        "Random Forest": "RF",
        "Random Forest (SMOTE)": "RF+SM",
        "XGBoost": "XGB",
        "MLP Classifier": "MLP",
        "LSTM Classifier": "LSTM",
        "LSTM Classifier (SMOTE)": "LSTM+SM",
        "CNN": "CNN",
        "CNN-LSTM": "C-LSTM",
        "ResNet-CNN": "ResNet",
        "ResNet-LSTM": "ResNet-LSTM",
        "StackedEnsemble_RF": "SE-RF",
        "StackedEnsemble_RF+SM": "SE-RF+SM",
    }
    return mapping.get(n, n)


def collapse_variants(short: str) -> str:
    for suf in ["+SM", "+EXPL", "+XGBF"]:
        if short.endswith(suf):
            return short.replace(suf, "")
    return short


def family_for(short: str) -> str:
    s = short
    if s.startswith("ResNet-LSTM") or s.startswith("C-LSTM"):  return "C-LSTM"
    if s.startswith("ResNet") or s == "CNN":                   return "CNN"
    if s.startswith("SE-"):                                    return "Ensemble"
    if s.startswith("RF"):                                     return "RF"
    if s.startswith("LR"):                                     return "LR"
    if s.startswith("XGB"):                                    return "XGB"
    if s.startswith("MLP"):                                    return "MLP"
    if s.startswith("LSTM"):                                   return "LSTM"
    return s


def dataset_short(name: str) -> str:
    n = (name or "").strip()
    map_ds = {
        "GPS_Data_Simplified_2D_Feature_Map.xlsx": "GPS-2D",
        "spoofing-merged-gps-only.csv": "SPOOF-GPS",
        "spoofing_ctgan_100000.csv": "CTGAN-100k",
        "spoofing_ctgan_1000000.csv": "CTGAN-1M",
        "spoofing_gc_100000.csv": "GC-100k",
        "spoofing_gc_1000000.csv": "GC-1M",
        "spoofing_tvae_100000.csv": "TVAE-100k",
        "spoofing_tvae_1000000.csv": "TVAE-1M",
    }
    return map_ds.get(n, n)


# ---- Read via helper ----
from print_csv import read_csv_dicts


def load_rows(files):
    rows = []
    for f in files:
        header, rs = read_csv_dicts(f)
        for r in rs:
            r = { (k or "").strip(): (v or "").strip() for k,v in r.items() }
            r["_source"] = Path(f).name
            rows.append(r)
    return rows


def to_arrays(rows, use_overview_labels=True):
    X, Y, M_raw, D_raw, SRC = [], [], [], [], []
    for r in rows:
        xs = r.get("train_time_sec", "")
        ys = r.get("accuracy", "")
        try:
            x = float(xs)
            y = float(ys)
            if not (math.isfinite(x) and math.isfinite(y)):
                continue
            if x <= 0:
                continue
        except Exception:
            continue
        short = normalize_label(r.get("model", "Unknown"))
        short = collapse_variants(short) if use_overview_labels else short
        ds_short = dataset_short(r.get("dataset", "Unknown"))
        X.append(x)
        Y.append(y)
        M_raw.append(short)
        D_raw.append(ds_short)
        SRC.append(r.get("_source",""))
    return np.array(X), np.array(Y), M_raw, D_raw, SRC


# ---- Color + marker styling (GLOBAL & CONSISTENT) ----
def distinct_colors(n):
    """Generate n distinct RGB tuples evenly spaced in HLS."""
    if n <= 20:
        # Prefer tab20 for <=20
        cmap = colormaps.get_cmap("tab20")
        return [cmap(i % cmap.N) for i in range(n)]
    # Evenly spaced hues, fixed lightness/saturation
    cols = []
    for i in range(n):
        h = i / float(n)
        r,g,b = colorsys.hls_to_rgb(h, 0.50, 0.65)  # lightness=0.5, sat=0.65
        cols.append((r,g,b,1.0))
    return cols


def build_style_maps(global_rows):
    # sets of labels for BOTH modes (overview vs variants)
    _, _, M_over, _, _ = to_arrays(global_rows, use_overview_labels=True)
    _, _, M_var,  _, _ = to_arrays(global_rows, use_overview_labels=False)

    models_over = sorted(set(M_over))
    models_var = sorted(set(M_var))

    # Datasets (markers shared)
    _, _, _, Dg, _ = to_arrays(global_rows, use_overview_labels=True)
    datasets = sorted(set(Dg))
    markers = ["o","s","D","^","v","<",">","P","X","*","h","H"]
    marker_map = {d: markers[i % len(markers)] for i, d in enumerate(datasets)}

    if COLOR_BY.lower() == "model":
        # Unique color per model label
        cols_over = distinct_colors(len(models_over))
        color_over = {lbl: cols_over[i] for i, lbl in enumerate(models_over)}
        cols_var = distinct_colors(len(models_var))
        color_var = {lbl: cols_var[i] for i, lbl in enumerate(models_var)}
    else:
        # One color per family (old behavior), consistently applied
        fams_over = sorted(set(family_for(m) for m in models_over))
        fam_cols = distinct_colors(len(fams_over))
        fam_color = {fam: fam_cols[i] for i, fam in enumerate(fams_over)}
        color_over = {lbl: fam_color[family_for(lbl)] for lbl in models_over}

        fams_var = sorted(set(family_for(m) for m in models_var))
        fam_cols2 = distinct_colors(len(fams_var))
        fam_color2 = {fam: fam_cols2[i] for i, fam in enumerate(fams_var)}
        color_var = {lbl: fam_color2[family_for(lbl)] for lbl in models_var}

    return color_over, color_var, marker_map


def _legend_layout(models_here, datasets_here):
    n_m, n_d = len(models_here), len(datasets_here)
    if n_m > 18 or n_d > 10:
        right = 0.55
    elif n_m > 12 or n_d > 8:
        right = 0.62
    else:
        right = 0.70
    model_ncol = 2 if n_m > 18 else 1
    ds_ncol = 2 if n_d > 10 else 1
    return right, model_ncol, ds_ncol


def scatter_figure(rows_subset, out_path, title,
                   color_map, marker_map,
                   use_overview_labels=True,
                   trim_percentiles=None):
    X, Y, M, D, _ = to_arrays(rows_subset, use_overview_labels=use_overview_labels)
    if len(X) == 0:
        print(f"No points for {out_path.name}")
        return

    xlim = None
    if trim_percentiles:
        lo, hi = np.percentile(X, trim_percentiles)
        lo = max(lo, 1e-9)
        if hi > lo:
            xlim = (lo, hi)

    models_here = sorted(set(M))
    datasets_here = sorted(set(D))
    right, model_ncol, ds_ncol = _legend_layout(models_here, datasets_here)

    fig, ax = plt.subplots(figsize=FIGSIZE)

    for m_lbl in models_here:
        for d_lbl in datasets_here:
            idx = [i for i, (mm,dd) in enumerate(zip(M,D)) if mm==m_lbl and dd==d_lbl]
            if not idx:
                continue
            xs = X[idx]
            ys = Y[idx]
            ax.plot(xs, ys, linestyle="None",
                    marker=marker_map.get(d_lbl, "o"),
                    markersize=MARKER_SIZE,
                    markerfacecolor=color_map.get(m_lbl, (0.2,0.2,0.2)),
                    markeredgecolor="black", markeredgewidth=0.3, alpha=0.9)

    ax.set_xscale("log")
    if xlim:
        ax.set_xlim(xlim)
    ax.set_xlabel("Training Time (s)")
    ax.set_ylabel("Accuracy")
    ax.set_title(title)
    ax.grid(True, linestyle=":", alpha=0.4)
    ax.margins(AX_MARGIN_XY, AX_MARGIN_XY)

    plt.subplots_adjust(right=right)

    model_handles = [Line2D([0],[0], marker="o", linestyle="",
                            markerfacecolor=color_map.get(m, (0.2,0.2,0.2)),
                            markeredgecolor="none", markersize=7)
                     for m in models_here]
    leg_models = ax.legend(model_handles, models_here, title="model",
                           loc="upper left", bbox_to_anchor=(1.02,1.00),
                           frameon=True, ncol=model_ncol, columnspacing=0.6, handletextpad=0.4)
    ax.add_artist(leg_models)

    dataset_handles = [Line2D([0],[0], marker=marker_map.get(d,"o"), linestyle="",
                              color="black", markersize=6)
                       for d in datasets_here]
    ax.legend(dataset_handles, datasets_here, title="dataset",
              loc="lower left", bbox_to_anchor=(1.02,0.00),
              frameon=True, ncol=ds_ncol, columnspacing=0.8, handletextpad=0.4)

    plt.tight_layout()
    plt.savefig(out_path.with_suffix(".pdf"), dpi=PNG_DPI, bbox_inches="tight")
    plt.savefig(out_path.with_suffix(".png"), dpi=PNG_DPI, bbox_inches="tight")
    plt.close(fig)
    print("Saved", out_path.with_suffix(".pdf").name, "and .png")


def best_by_dataset_chart(rows, out_path, use_overview_labels=False):
    grouped = {}
    for r in rows:
        try:
            acc = float((r.get("accuracy") or "").strip())
        except Exception:
            continue
        ds = dataset_short(r.get("dataset",""))
        model_short = normalize_label(r.get("model",""))
        if use_overview_labels:
            model_short = collapse_variants(model_short)
        if ds not in grouped or acc > grouped[ds]["acc"]:
            grouped[ds] = {"acc": acc, "model": model_short}

    if not grouped:
        print(f"[WARN] No best-by-dataset data for {out_path.name}")
        return

    items = sorted(grouped.items(), key=lambda kv: kv[0])
    labels = [k for k, _ in items]
    accs = [v["acc"] for _, v in items]
    models = [v["model"] for _, v in items]

    fig_h = max(3.2, 0.42*len(labels))
    fig, ax = plt.subplots(figsize=(FIGSIZE[0], fig_h))
    y = np.arange(len(labels))
    bars = ax.barh(y, accs)
    ax.set_yticks(y, labels)
    ax.set_xlabel("Accuracy")
    ax.set_title("Best Model Per Dataset (by Accuracy)")

    for rect, mdl, val in zip(bars, models, accs):
        x = rect.get_width()
        ax.text(x + 0.006, rect.get_y() + rect.get_height()/2,
                f"{mdl} ({val:.3f})", va="center", ha="left", fontsize=9)

    ax.set_xlim(0, max(1.0, max(accs) + 0.06))
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    plt.tight_layout()
    plt.savefig(out_path.with_suffix(".pdf"), dpi=PNG_DPI, bbox_inches="tight")
    plt.savefig(out_path.with_suffix(".png"), dpi=PNG_DPI, bbox_inches="tight")
    plt.close(fig)
    print("Saved", out_path.with_suffix(".pdf").name, "and .png")


# ---- MAIN ----
def main():
    rows_all = load_rows(FILES)

    # Build consistent colors/markers for both label modes:
    # - overview (collapsed labels)
    # - variants (full labels)
    color_overview, color_variants, marker_map = build_style_maps(rows_all)

    # 1) All points (untrimmed) — use overview labels/colors
    scatter_figure(rows_all, OUTDIR/"fig_all",
        title="Accuracy vs Training Time (all models, all datasets)",
        color_map=color_overview, marker_map=marker_map,
        use_overview_labels=True, trim_percentiles=None)

    # 2) All points trimmed (1–99th pct) — overview
    scatter_figure(rows_all, OUTDIR/"fig_trimmed_p1p99",
        title="Accuracy vs Training Time (all models, x trimmed to 1–99th pct)",
        color_map=color_overview, marker_map=marker_map,
        use_overview_labels=True, trim_percentiles=(1,99))

    # 3) UAVATTACK only — overview
    rows_uav = [r for r in rows_all if "UAVATTACK" in r.get("_source","")]
    if rows_uav:
        scatter_figure(rows_uav, OUTDIR/"fig_uavattack_only",
            title="Accuracy vs Training Time (UAVATTACK only)",
            color_map=color_overview, marker_map=marker_map,
            use_overview_labels=True, trim_percentiles=None)

    # 4) 2D only — overview
    rows_2d = [r for r in rows_all if "2D_" in r.get("_source","") or r.get("_source","").startswith("2D")]
    if rows_2d:
        scatter_figure(rows_2d, OUTDIR/"fig_2d_only",
            title="Accuracy vs Training Time (2D only)",
            color_map=color_overview, marker_map=marker_map,
            use_overview_labels=True, trim_percentiles=None)

    # 5) Zoomed families — use VARIANT labels/colors (keeps LR+SM, SE-RF+SM distinct)
    def rows_for_family(rows, fam_key):
        kept = []
        for r in rows:
            short = normalize_label(r.get("model",""))
            fam = family_for(short)
            if fam_key == "MLP+XGB":
                if fam in ("MLP","XGB"): kept.append(r)
            elif fam == fam_key:
                kept.append(r)
        return kept

    zoom_specs = [
        ("LR",        "fig_zoom_LR_features"),
        ("RF",        "fig_zoom_RF_features"),
        ("MLP+XGB",   "fig_zoom_MLP_XGB_features"),
        ("CNN",       "fig_zoom_CNN_family"),
        ("C-LSTM",    "fig_zoom_CLSTM_family"),
        ("Ensemble",  "fig_zoom_Ensemble_RF"),
    ]
    for fam_key, fname in zoom_specs:
        rsub = rows_for_family(rows_all, fam_key)
        if not rsub:
            continue
        scatter_figure(rsub, OUTDIR/fname,
            title=f"Accuracy vs Training Time ({fam_key} family)",
            color_map=color_variants, marker_map=marker_map,
            use_overview_labels=False, trim_percentiles=None)

    # 6) Best-by-dataset (annotated bars)
    best_by_dataset_chart(rows_all, OUTDIR/"fig_best_by_dataset", use_overview_labels=False)

    print(f"\nAll figures written to: {OUTDIR.resolve()}")


if __name__ == "__main__":
    main()
