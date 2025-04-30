#!/usr/bin/env python3
"""
run_plot_metrics.py
-------------------
As before but with consistent per-subgroup colors across roles:
  • Selection‐Rate bar charts
  • Adverse‐Impact Ratio bar charts
  • GEE odds‐ratio forest plot
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

# ── Config ──────────────────────────────────────────────────────────────
METRICS_DIR = Path("outputs/metrics")
PLOTS_DIR   = Path("outputs/plots")
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

ROLES = ["swe", "hr"]
ATTRS = ["gender", "race", "religion", "class", "lgbtq", "marginalized"]

# ── Build a global color mapping for each attribute value ────────────────
# first gather all unique values for each attribute across both rates & AIR
value_sets = {attr: set() for attr in ATTRS}

for role in ROLES:
    for suffix in ["subgroup_rates", "subgroup_air"]:
        df = pd.read_csv(METRICS_DIR / f"{role}_{suffix}.csv")
        for attr in ATTRS:
            vals = df[df["attribute"] == attr]["value"].astype(str).unique()
            value_sets[attr].update(vals)

# now assign each unique value a distinct color from tab10
cmap = plt.get_cmap("tab10")
color_map = {}
for attr in ATTRS:
    vals = sorted(value_sets[attr])
    n = len(vals)
    # sample the first n entries of tab10 (or wrap around if >10)
    cols = [cmap(i % 10) for i in range(n)]
    color_map[attr] = dict(zip(vals, cols))

# ── Plotting helpers ─────────────────────────────────────────────────────
def bar_chart(x, y, colors, title, xlabel, ylabel, lines=None, out_path=None):
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar([str(v) for v in x], y, color=[colors[str(v)] for v in x])
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, max(y)*1.1)
    if lines:
        for lvl, style in lines:
            ax.axhline(lvl, linestyle=style, color="gray")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    if out_path:
        fig.savefig(out_path, dpi=300)
    plt.close(fig)

def forest_plot(terms, ors, low, high, title, out_path=None):
    fig, ax = plt.subplots(figsize=(6, len(terms)*0.4 + 1))
    ax.errorbar(ors, terms, xerr=[ors-low, high-ors], fmt="o", color="black")
    ax.axvline(1.0, linestyle="--", color="red")
    ax.set_title(title)
    ax.set_xlabel("Odds Ratio (95% CI)")
    ax.set_ylabel("")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    if out_path:
        fig.savefig(out_path, dpi=300)
    plt.close(fig)

# ── Main ───────────────────────────────────────────────────────────────
for role in ROLES:
    # 1) Selection‐Rate charts
    sr_df = pd.read_csv(METRICS_DIR / f"{role}_subgroup_rates.csv")
    for attr in ATTRS:
        sub = sr_df[sr_df["attribute"] == attr]
        bar_chart(
            x=sub["value"],
            y=sub["selection_rate"],
            colors=color_map[attr],
            title=f"{role.upper()} Selection Rate by {attr.capitalize()}",
            xlabel=attr.capitalize(),
            ylabel="Selection Rate",
            out_path=PLOTS_DIR / f"{role}_{attr}_sr.png"
        )

    # 2) AIR charts
    air_df = pd.read_csv(METRICS_DIR / f"{role}_subgroup_air.csv")
    for attr in ATTRS:
        sub = air_df[air_df["attribute"] == attr]
        bar_chart(
            x=sub["value"],
            y=sub["AIR"],
            colors=color_map[attr],
            title=f"{role.upper()} AIR by {attr.capitalize()}",
            xlabel=attr.capitalize(),
            ylabel="Adverse-Impact Ratio",
            lines=[(1.0, "--"), (0.8, ":")],
            out_path=PLOTS_DIR / f"{role}_{attr}_air.png"
        )

    # 3) GEE forest plot
    gee = pd.read_csv(METRICS_DIR / f"{role}_gee_results.csv")
    ors  = np.exp(gee["coef"])
    low  = np.exp(gee["coef"] - 1.96 * gee["std_err"])
    high = np.exp(gee["coef"] + 1.96 * gee["std_err"])
    terms = gee["term"].tolist()

    forest_plot(
        terms=terms,
        ors=ors,
        low=low,
        high=high,
        title=f"{role.upper()} GEE Odds Ratios",
        out_path=PLOTS_DIR / f"{role}_gee_forest.png"
    )

print("✅ Colored plots saved to outputs/plots/")