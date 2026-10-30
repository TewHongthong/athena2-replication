#!/usr/bin/env python3
"""make_figures - builds the two figures of the manuscript from the analysis outputs.

  python make_figures.py [--a13 ../analysis/a13.json] [--out ../manuscript]

Figure 2 plots, for every model-standard cell and for the two anchor cells, the compliance
without a standard against the compliance with rule selection; it is read from part 8 of the
A13 analysis.  Figure 3 plots the share of Godot parameter names without the required prefix
among the trials that pass the core rules; the counts are those of addendum A8, which the
core-rule checker does not cover, so they cannot be recomputed from the compliance scores.

Both figures are drawn without colour so that they carry in grey-scale print: the panel cells
and the anchor cells differ by marker, and every bar is labelled with its value.
"""
from __future__ import annotations

import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Addendum A8: trials that pass the core rules, Godot parameter tasks, pooled over the four
# models; the share whose proposed name carries neither the p_ nor the r_ prefix.
PREFIX_COUNTS = [
    ("None", 27.7, "72/260"),
    ("TF-IDF", 11.2, "29/258"),
    ("BM25", 8.5, "22/260"),
    ("Dense", 2.7, "7/262"),
    ("Full doc", 0.0, "0/264"),
    ("Selection", 0.0, "0/263"),
]

SELECTION_FLOOR = 95.9


def style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["DejaVu Serif", "Times New Roman"],
        "font.size": 8,
        "axes.labelsize": 8,
        "axes.titlesize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "grid.linewidth": 0.4,
        "grid.color": "0.85",
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
    })


def figure2(a13_path, out_dir):
    with open(a13_path, encoding="utf-8") as fh:
        res = json.load(fh)
    part8 = res.get("part8") or {}
    if not part8.get("available"):
        raise SystemExit("part 8 of the A13 analysis is not available")
    panel, anchor = [], []
    for pack, model, role, zero, sel, _gain in part8["rows"]:
        point = (float(zero), float(sel), pack, model)
        (anchor if role == "anchor" else panel).append(point)
    if not anchor:
        raise SystemExit("part 8 holds no anchor cell; run the anchors first")

    fig, ax = plt.subplots(figsize=(3.5, 3.1))
    ax.set_axisbelow(True)
    ax.grid(True, linestyle="-")
    ax.axhspan(SELECTION_FLOOR, 100, facecolor="0.9", edgecolor="none", zorder=0)
    ax.plot([0, 100], [0, 100], linestyle=":", color="0.55", linewidth=0.7, zorder=1)
    ax.scatter([p[0] for p in panel], [p[1] for p in panel], s=26, marker="o",
               facecolors="white", edgecolors="black", linewidths=0.8, zorder=3,
               label=f"model-standard cell ({len(panel)})")
    ax.scatter([p[0] for p in anchor], [p[1] for p in anchor], s=30, marker="s",
               facecolors="black", edgecolors="black", linewidths=0.8, zorder=3,
               label=f"anchor cell ({len(anchor)})")
    label_at = {"gemma": (52, 64), "qwen": (22, 46)}
    for zero, sel, _pack, model in sorted(anchor):
        gemma = "gemma" in model.lower()
        short = "Gemma 4 26B" if gemma else "Qwen3.5-9B"
        ax.annotate(f"{short}\n{zero:.1f} to {sel:.1f}", xy=(zero, sel),
                    xytext=label_at["gemma" if gemma else "qwen"], textcoords="data",
                    fontsize=6.5, ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", linewidth=0.5, color="0.45",
                                    shrinkA=2, shrinkB=4))
    ax.text(44, 101.4, f"selection: {SELECTION_FLOOR} to 100", fontsize=6.5, color="0.35",
            ha="left", va="center")
    ax.set_xlim(0, 104)
    ax.set_ylim(0, 104)
    ax.set_xticks(range(0, 101, 20))
    ax.set_yticks(range(0, 101, 20))
    ax.set_xlabel("Compliance without a standard (%)")
    ax.set_ylabel("Compliance with rule selection (%)")
    ax.legend(loc="lower left", frameon=False, handletextpad=0.4, borderpad=0.2)
    save(fig, out_dir, "fig_ceiling")
    return len(panel), len(anchor)


def figure3(out_dir):
    fig, ax = plt.subplots(figsize=(3.5, 2.3))
    ax.set_axisbelow(True)
    ax.grid(True, axis="y", linestyle="-")
    labels = [c[0] for c in PREFIX_COUNTS]
    values = [c[1] for c in PREFIX_COUNTS]
    bars = ax.bar(labels, values, width=0.62, facecolor="0.72", edgecolor="black",
                  linewidth=0.7, zorder=3)
    for bar, (_label, value, counts) in zip(bars, PREFIX_COUNTS):
        ax.annotate(f"{value:.1f}%\n{counts}", (bar.get_x() + bar.get_width() / 2, value),
                    textcoords="offset points", xytext=(0, 3), ha="center", va="bottom",
                    fontsize=6.5)
    ax.set_ylim(0, 33)
    ax.set_yticks(range(0, 31, 10))
    ax.set_ylabel("Names without the\nrequired prefix (%)")
    ax.tick_params(axis="x", length=0)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    save(fig, out_dir, "fig_prefix")
    return len(PREFIX_COUNTS)


def save(fig, out_dir, stem):
    os.makedirs(out_dir, exist_ok=True)
    for ext, dpi in (("png", 600), ("pdf", None)):
        path = os.path.join(out_dir, f"{stem}.{ext}")
        fig.savefig(path, dpi=dpi) if dpi else fig.savefig(path)
        print("wrote", path)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a13", default="../analysis/a13.json")
    ap.add_argument("--out", default="../manuscript")
    a = ap.parse_args()
    style()
    n_panel, n_anchor = figure2(a.a13, a.out)
    n_bars = figure3(a.out)
    print(f"figure 2: {n_panel} panel cells and {n_anchor} anchor cells")
    print(f"figure 3: {n_bars} conditions")


if __name__ == "__main__":
    main()
