"""
SENTINEL AI - Model Comparison & Visualization Script
=====================================================
Trains all 3 models on the preprocessed dataset, evaluates them, and
generates publication-quality comparison charts.

The script trains the actual models on the project data and generates
6 comparison plots saved to both report/images/ and models/plots/.
"""

import os
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, roc_curve, confusion_matrix,
)
from loguru import logger

# ── Configuration ────────────────────────────────────────────────────
OUT_DIR  = "report/images"
PLOT_DIR = "models/plots"
DATA_DIR = "data"

COLORS = {
    "Random Forest": "#4FC3F7",
    "XGBoost":       "#FF7043",
    "LightGBM":      "#66BB6A",
}

FEATURE_NAMES = [
    "flow_duration", "fwd_packets_tot", "bwd_packets_tot",
    "flow_byts_s", "flow_pkts_s", "pkt_len_mean",
    "pkt_len_std", "iat_mean", "iat_std",
    "syn_flag_cnt", "ack_flag_cnt", "psh_flag_cnt",
]

# ── Helpers ──────────────────────────────────────────────────────────
def load_data():
    X_train = np.load(os.path.join(DATA_DIR, "X_train.npy"))
    X_test  = np.load(os.path.join(DATA_DIR, "X_test.npy"))
    y_train = np.load(os.path.join(DATA_DIR, "y_train.npy"))
    y_test  = np.load(os.path.join(DATA_DIR, "y_test.npy"))
    return X_train, X_test, y_train, y_test


def _style_ax(ax, title, xlabel="", ylabel=""):
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.tick_params(labelsize=10)
    ax.grid(axis="y", alpha=0.3, linestyle="--")


def _save(fig, name):
    for d in (OUT_DIR, PLOT_DIR):
        os.makedirs(d, exist_ok=True)
        fig.savefig(os.path.join(d, name), dpi=200, bbox_inches="tight",
                    facecolor="white")
    plt.close(fig)
    logger.info(f"  Saved  {name}")


# ── Training ─────────────────────────────────────────────────────────
def train_models(X_train, X_test, y_train, y_test):
    """Train all 3 models and collect real predictions."""
    configs = {
        "Random Forest": RandomForestClassifier(
            n_estimators=100, random_state=42, n_jobs=-1
        ),
        "XGBoost": XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            use_label_encoder=False, eval_metric="logloss",
            random_state=42, verbosity=0
        ),
        "LightGBM": LGBMClassifier(
            n_estimators=100, random_state=42, verbose=-1
        ),
    }

    results = {}
    for name, model in configs.items():
        logger.info(f"Training {name} ...")
        t0 = time.perf_counter()
        model.fit(X_train, y_train)
        train_time = time.perf_counter() - t0

        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        metrics = {
            "Accuracy":   round(accuracy_score(y_test, y_pred), 4),
            "Precision":  round(precision_score(y_test, y_pred), 4),
            "Recall":     round(recall_score(y_test, y_pred), 4),
            "F1-Score":   round(f1_score(y_test, y_pred), 4),
            "ROC-AUC":    round(roc_auc_score(y_test, y_prob), 4),
            "Train_Time": round(train_time, 2),
        }
        results[name] = {
            "metrics": metrics, "y_pred": y_pred,
            "y_prob": y_prob, "model": model,
        }
        logger.info(f"  {name} -> F1={metrics['F1-Score']:.4f}  AUC={metrics['ROC-AUC']:.4f}  ({train_time:.2f}s)")

    return results


# ── Plot 1: Grouped Bar Chart ───────────────────────────────────────
def plot_metric_bars(results):
    metric_names = ["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC"]
    model_names  = list(results.keys())
    x = np.arange(len(metric_names))
    width = 0.22

    fig, ax = plt.subplots(figsize=(12, 6))
    for i, name in enumerate(model_names):
        vals = [results[name]["metrics"][m] for m in metric_names]
        bars = ax.bar(x + i * width, vals, width, label=name,
                      color=COLORS[name], edgecolor="white", linewidth=0.5)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.003,
                    f"{v:.3f}", ha="center", va="bottom", fontsize=8, fontweight="bold")

    ax.set_xticks(x + width)
    ax.set_xticklabels(metric_names, fontsize=11)
    # Auto-scale y-axis
    all_vals = [results[n]["metrics"][m] for n in model_names for m in metric_names]
    ymin = max(0, min(all_vals) - 0.03)
    ax.set_ylim(ymin, 1.02)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
    _style_ax(ax, "Model Performance Comparison - All Metrics", ylabel="Score")
    ax.legend(fontsize=11, loc="lower right")
    _save(fig, "model_comparison_bar.png")


# ── Plot 2: Overlay ROC Curves ──────────────────────────────────────
def plot_roc_overlay(results, y_test):
    fig, ax = plt.subplots(figsize=(8, 7))
    for name, res in results.items():
        fpr, tpr, _ = roc_curve(y_test, res["y_prob"])
        auc = res["metrics"]["ROC-AUC"]
        ax.plot(fpr, tpr, label=f"{name}  (AUC = {auc:.3f})",
                color=COLORS[name], linewidth=2.2)

    ax.plot([0, 1], [0, 1], "--", color="grey", linewidth=1, alpha=0.6)
    _style_ax(ax, "ROC Curve Comparison - All Models",
              xlabel="False Positive Rate", ylabel="True Positive Rate")
    ax.legend(fontsize=11, loc="lower right")
    _save(fig, "roc_all_models.png")


# ── Plot 3: Confusion Matrices Side-by-Side ─────────────────────────
def plot_confusion_matrices(results, y_test):
    model_names = list(results.keys())
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for ax, name in zip(axes, model_names):
        cm = confusion_matrix(y_test, results[name]["y_pred"])
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                    xticklabels=["Benign", "Botnet"],
                    yticklabels=["Benign", "Botnet"],
                    cbar=False, annot_kws={"size": 14, "fontweight": "bold"})
        ax.set_title(name, fontsize=13, fontweight="bold", pad=10)
        ax.set_xlabel("Predicted", fontsize=11)
        ax.set_ylabel("Actual", fontsize=11)
    fig.suptitle("Confusion Matrix Comparison", fontsize=15,
                 fontweight="bold", y=1.03)
    fig.tight_layout()
    _save(fig, "confusion_matrices_all.png")


# ── Plot 4: Training Time ───────────────────────────────────────────
def plot_training_time(results):
    names  = list(results.keys())
    times  = [results[n]["metrics"]["Train_Time"] for n in names]
    colors = [COLORS[n] for n in names]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(names, times, color=colors, edgecolor="white", height=0.5)
    for bar, t in zip(bars, times):
        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height() / 2,
                f"{t:.2f}s", va="center", fontsize=11, fontweight="bold")
    _style_ax(ax, "Training Time Comparison", xlabel="Time (seconds)")
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.3, linestyle="--")
    ax.grid(axis="y", alpha=0)
    _save(fig, "training_time_bar.png")


# ── Plot 5: Feature Importance (XGBoost) ─────────────────────────────
def plot_feature_importance(results):
    model = results["XGBoost"]["model"]
    importances = model.feature_importances_

    if len(importances) == len(FEATURE_NAMES):
        feat_names = FEATURE_NAMES
    else:
        feat_names = [f"Feature_{i}" for i in range(len(importances))]

    idx = np.argsort(importances)[-10:]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh([feat_names[i] for i in idx], importances[idx],
            color="#FF7043", edgecolor="white")
    _style_ax(ax, "Top-10 Feature Importances - XGBoost Champion",
              xlabel="Importance Score")
    ax.grid(axis="x", alpha=0.3, linestyle="--")
    ax.grid(axis="y", alpha=0)
    _save(fig, "feature_importance_top10.png")


# ── Plot 6: Radar / Spider Chart ────────────────────────────────────
def plot_radar(results):
    metric_names = ["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC"]
    model_names  = list(results.keys())
    N = len(metric_names)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    for name in model_names:
        vals = [results[name]["metrics"][m] for m in metric_names]
        vals += vals[:1]
        ax.plot(angles, vals, "o-", label=name, color=COLORS[name], linewidth=2)
        ax.fill(angles, vals, alpha=0.12, color=COLORS[name])

    ax.set_thetagrids([a * 180 / np.pi for a in angles[:-1]], metric_names, fontsize=11)
    # Auto-scale radial axis
    all_vals = [results[n]["metrics"][m] for n in model_names for m in metric_names]
    ax.set_ylim(max(0, min(all_vals) - 0.03), 1.0)
    ax.set_title("Radar Comparison - All Models", fontsize=14,
                 fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), fontsize=10)
    _save(fig, "radar_comparison.png")


# ── Summary ──────────────────────────────────────────────────────────
def print_summary(results):
    metric_names = ["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC", "Train_Time"]
    rows = [{"Model": n, **{m: res["metrics"][m] for m in metric_names}}
            for n, res in results.items()]
    df = pd.DataFrame(rows).set_index("Model")

    print("\n" + "=" * 70)
    print("         SENTINEL AI - Model Benchmarking Summary")
    print("=" * 70)
    print(df.to_string(float_format="%.4f"))
    print("=" * 70)

    best = df["F1-Score"].idxmax()
    print(f"\n[CHAMPION] {best}  (F1 = {df.loc[best, 'F1-Score']:.4f},  AUC = {df.loc[best, 'ROC-AUC']:.4f})")
    print(f"[FASTEST]  {df['Train_Time'].idxmin()}  ({df['Train_Time'].min():.2f}s)\n")

    summary_path = os.path.join("models", "benchmark_summary.txt")
    with open(summary_path, "w") as f:
        f.write("SENTINEL AI - Model Benchmarking Summary\n")
        f.write("=" * 60 + "\n")
        f.write(df.to_string(float_format="%.4f") + "\n")
        f.write("=" * 60 + "\n")
        f.write(f"\nChampion: {best}  (F1={df.loc[best, 'F1-Score']:.4f})\n")
    logger.info(f"  Summary saved to {summary_path}")


# ── Main ─────────────────────────────────────────────────────────────
def main():
    logger.info("SENTINEL AI - Model Comparison Pipeline Starting ...")

    X_train, X_test, y_train, y_test = load_data()
    logger.info(f"Data loaded -> Train: {X_train.shape}  Test: {X_test.shape}")

    results = train_models(X_train, X_test, y_train, y_test)

    logger.info("Generating comparison plots ...")
    plot_metric_bars(results)
    plot_roc_overlay(results, y_test)
    plot_confusion_matrices(results, y_test)
    plot_training_time(results)
    plot_feature_importance(results)
    plot_radar(results)

    print_summary(results)
    logger.success("All comparison plots generated successfully!")
    logger.info(f"Plots saved to: {OUT_DIR}/ and {PLOT_DIR}/")


if __name__ == "__main__":
    main()
