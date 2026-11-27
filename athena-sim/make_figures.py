#!/usr/bin/env python3
"""make_figures - builds the four data figures of the paper from the analysis outputs.

  python make_figures.py [--a11 ../analysis/a11.json] [--a13 ../analysis/a13.json]
                         [--study2 ../analysis/study2.json] [--out ../manuscript]

fig_s1_cells: compliance (core_ok, %) of Study 1 by standard, model, and condition on the test
tasks, with the 95% percentile interval of a cluster bootstrap over source files; values and
intervals are read from part 1 of the A11 analysis (task_mean, file_low, file_high).

fig_prefix: the share of Godot parameter names without the required prefix among the trials
that pass the core rules; the counts are those of addendum A8, which the core-rule checker does
not cover, so they cannot be recomputed from the compliance scores.

fig_ceiling: for every model-standard cell and for the two anchor cells, the compliance without
a standard against the compliance with rule selection; read from part 8 of the A13 analysis.

fig_s2_differences: the registered comparisons of Study 2 as differences in core_ok_s2
(percentage points) with their 95% cluster-bootstrap intervals and the registered margins, read
from the Study 2 analysis (h2.rows: selection minus naming; h3.fulldoc: selection minus fulldoc;
h4.rows: inferred kind minus kind from metadata).

No number is computed here that the analysis outputs (or addendum A8) do not already contain.
Every figure is drawn without colour so that it carries in grey-scale print: conditions and
cell types differ by marker, and every bar is labelled with its value.
"""
from __future__ import annotations

import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

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


def figure_ceiling(a13_path, out_dir):
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


def figure_prefix(out_dir):
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


S1_PACKS = [("godot", "Godot"), ("dotnet-runtime", ".NET runtime"), ("odoo", "Odoo")]
S1_MODELS = [("gpt-6-luna", "Luna"), ("gemini-3.1-flash-lite", "Gemini"), ("gemma-4-26b", "Gemma"), ("qwen3.5-9b", "Qwen")]
# condition key in the trial records -> label, marker, face colour, edge colour
S1_CONDS = [("none", "None", "o", "white", "black"), ("fulldoc", "Full doc", "s", "0.55", "0.55"),
            ("chunk", "TF-IDF", "^", "white", "0.45"), ("bm25", "BM25", "v", "white", "0.45"),
            ("dense", "Dense", "D", "white", "0.45"), ("graph", "Selection", "o", "black", "black")]


def model_of(key, table):
    hits = [lab for k, lab in table if k in key]
    assert len(hits) == 1, key
    return hits[0]


def figure_s1_cells(a11_path, out_dir):
    with open(a11_path, encoding="utf-8") as fh:
        rows = json.load(fh)["part1"]
    cell = {}
    for r in rows:
        cell[(r["pack"], model_of(r["model"], S1_MODELS), r["condition"])] = r
    assert len(cell) == 72
    fig, axes = plt.subplots(1, 3, figsize=(5.2, 2.6), sharey=True)
    offs = [-0.30, -0.18, -0.06, 0.06, 0.18, 0.30]
    for ax, (pack, ptitle) in zip(axes, S1_PACKS):
        for yi, (_, mlab) in enumerate(S1_MODELS):
            y0 = len(S1_MODELS) - 1 - yi
            if yi:
                ax.axhline(y0 + 0.5, color="0.88", lw=0.4, zorder=0)
            for (ck, clab, mk, fc, ec), dy in zip(S1_CONDS, offs):
                r = cell[(pack, mlab, ck)]
                m, lo, hi = 100 * r["task_mean"], 100 * r["file_low"], 100 * r["file_high"]
                ax.plot([lo, hi], [y0 - dy] * 2, color=ec, lw=0.7, zorder=1, solid_capstyle="butt")
                ax.plot([m], [y0 - dy], marker=mk, ms=3.6, mfc=fc, mec=ec, mew=0.7, ls="none", zorder=2)
        ax.set_title(ptitle)
        ax.set_xlim(75, 101)
        ax.set_xticks([80, 90, 100])
        ax.set_xticks([75, 85, 95], minor=True)
        ax.grid(axis="x", which="minor", color="0.93")
        ax.grid(axis="x")
        ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axes[0].set_yticks(range(len(S1_MODELS)))
    axes[0].set_yticklabels([lab for _, lab in reversed(S1_MODELS)])
    axes[0].set_ylim(-0.55, len(S1_MODELS) - 0.45)
    axes[1].set_xlabel("Compliance (core_ok, %), test tasks")
    handles = [Line2D([], [], marker=mk, ms=4, mfc=fc, mec=ec, mew=0.7, ls="none", label=clab) for _, clab, mk, fc, ec in S1_CONDS]
    fig.legend(handles=handles, loc="lower center", ncol=6, frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.subplots_adjust(wspace=0.12, bottom=0.25)
    save(fig, out_dir, "fig_s1_cells")
    return len(cell)


S2_PACKS = [("godot-s2", "Godot"), ("dotnet-runtime-s2", ".NET runtime")]
S2_MODELS = [("luna", "Luna"), ("gemini31fl", "Gemini"), ("gemma4_local_s2", "Gemma"), ("qwen35_9b_or_s2", "Qwen")]


def figure_s2_differences(s2_path, out_dir):
    with open(s2_path, encoding="utf-8") as fh:
        d = json.load(fh)
    panels = [("Selection \u2212 naming\n(H2-S2)", d["h2"]["rows"], -float(d["h2"]["margin_pp"]), (-5, 28)),
              ("Selection \u2212 whole\nstandard (H3-S2)", d["h3"]["fulldoc"], -float(d["h3"]["margin_pp"]), (-5, 40)),
              ("Inferred kind \u2212 kind\nfrom metadata (H4-S2)", d["h4"]["rows"], -float(d["h4"]["margin_pp"]), (-33, 5))]
    labels, ypos = [], []
    order = [(p, m) for p, _ in S2_PACKS for m, _ in S2_MODELS]
    y = {}
    k = 0
    for pi, (p, plab) in enumerate(S2_PACKS):
        for m, mlab in S2_MODELS:
            y[(p, m)] = -(k + pi * 0.8)
            labels.append(f"{plab}, {mlab}")
            ypos.append(y[(p, m)])
            k += 1
    fig, axes = plt.subplots(1, 3, figsize=(5.2, 2.9), sharey=True)
    for ax, (title, rows, margin, xlim) in zip(axes, panels):
        ax.set_xlim(*xlim)
        got = {(r["pack"], r["model"]): r for r in rows}
        assert set(got) == set(order), title
        for key in order:
            r = got[key]
            yy = y[key]
            ax.plot([r["ci_low_pp"], r["ci_high_pp"]], [yy, yy], color="black", lw=0.8, solid_capstyle="butt", zorder=1)
            ax.plot([r["mean_diff_pp"]], [yy], marker="o", ms=3.8, mfc="black", mec="black", ls="none", zorder=2)
        ax.axvline(0, color="0.55", lw=0.6, zorder=0)
        ax.axvline(margin, color="black", lw=0.7, ls=(0, (3, 2)), zorder=0)
        ax.set_title(title, fontsize=7)
        ax.grid(axis="x")
        ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    gap = (y[(S2_PACKS[0][0], S2_MODELS[-1][0])] + y[(S2_PACKS[1][0], S2_MODELS[0][0])]) / 2
    for ax in axes:
        ax.axhline(gap, color="0.80", lw=0.5, zorder=0)
    axes[0].set_yticks(ypos)
    axes[0].set_yticklabels(labels)
    axes[1].set_xlabel("Difference in core_ok_s2 (percentage points), test tasks")
    fig.subplots_adjust(wspace=0.12)
    save(fig, out_dir, "fig_s2_differences")
    return len(order)


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
    ap.add_argument("--a11", default="../analysis/a11.json")
    ap.add_argument("--a13", default="../analysis/a13.json")
    ap.add_argument("--study2", default="../analysis/study2.json")
    ap.add_argument("--out", default="../manuscript")
    a = ap.parse_args()
    style()
    n_panel, n_anchor = figure_ceiling(a.a13, a.out)
    n_bars = figure_prefix(a.out)
    with plt.rc_context({"pdf.fonttype": 42}):
        n_s1 = figure_s1_cells(a.a11, a.out)
        n_s2 = figure_s2_differences(a.study2, a.out)
    print(f"fig_ceiling: {n_panel} panel cells and {n_anchor} anchor cells")
    print(f"fig_prefix: {n_bars} conditions")
    print(f"fig_s1_cells: {n_s1} standard-model-condition cells")
    print(f"fig_s2_differences: {n_s2} standard-model cells per comparison")


if __name__ == "__main__":
    main()
