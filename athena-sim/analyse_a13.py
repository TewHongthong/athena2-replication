#!/usr/bin/env python3
"""analyse_a13 - the results the frozen design promised but did not report, and three analyses added after
the data (exploratory; no decision rule, no new model call).

  python analyse_a13.py --meta runs/test_*_meta --infer runs/test_*_infer
                        [--canary runs/canary_*] [--supplementary runs/pilot_tank*]
                        [--anchors runs/anchor_*] [--out a13.md] [--json a13.json]

Parts 1 to 4 are registered reporting: Section 2.1 of the hypotheses file asks for the change in core_ok
between the two canary runs of every model, Section 2.2 for the development results of the supplementary
models, Section 5 for the tokens and the cost per model and standard, and Section 2.3 for the anchor packs as
the extreme points of H2.  They were computed from the frozen runs and add no decision rule.

Parts 5 to 7 were added after the data were seen: the accuracy of the inferred kind against the kind in the
unit metadata, the paired wins, ties and losses behind every mean difference of H3, and the number of source
file clusters in the test split.  Provisional values of parts 1 to 3 and 5 to 7 were computed while this
addendum was planned, so none of the seven parts is confirmatory; this is stated in the addendum itself.

A task is a unit_id; its score is the mean of core_ok over its repeats.  The kind fields are written by the
report step into trials.csv and are not in trials.jsonl, so part 5 reads the csv.  Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import os
import statistics
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from athena import confirmatory as C  # noqa: E402
from athena.report import load_trials  # noqa: E402
from athena.secondary import clopper_pearson_lower, spearman_permutation  # noqa: E402

PACKS = C.DEFAULT_PACKS
SELECTION = "graph"
FULLDOC = "fulldoc"
NONE = "none"
CONDITIONS = ("none", "fulldoc", "chunk", "bm25", "dense", "graph")
ANCHOR_PACKS = ("gscs", "public5")

# The borrowed endpoint returns its own label for each model. The first two labels name the model of the plan
# (Section 2.2); the third is the remaining one of the three and is matched to it by elimination. No weight,
# revision or quantisation is verified, which is why both names are reported.
SUPPLEMENTARY_NAMES = {
    "openai:qwen35b": "Qwen3.5 35B-A3B",
    "openai:flashnext:instruct": "Qwen3.8 Flash-Next",
    "openai:Uncensored": "Qwen3.8 27B (matched by elimination)",
}
IDENTITY_FIELDS = ("model", "provider")


def expand(patterns):
    out = []
    for p in patterns or []:
        hit = sorted(glob.glob(p))
        out.extend(hit if hit else [p])
    return out


def pct(x, nd=1):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.{nd}f}"


def num(x, nd=1):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:,.{nd}f}"


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def ok_of(r):
    v = (r.get("metrics") or {}).get("core_ok")
    return None if v is None else (1.0 if v else 0.0)


def index_cells(recs, split, model_field="backend", cluster_field="file"):
    """idx[(pack, model, condition)][unit_id] = [core_ok per repeat]; clusters[(pack, unit)] = source file."""
    idx: dict = defaultdict(lambda: defaultdict(list))
    clusters: dict = {}
    for r in recs:
        if r.get("task", "rename") != "rename" or r.get("split") != split:
            continue
        v = ok_of(r)
        if v is None:
            continue
        clusters[(r.get("pack"), r["unit_id"])] = r.get(cluster_field) or r.get("snippet_id") or r["unit_id"]
        idx[(r.get("pack"), r.get(model_field), r.get("condition"))][r["unit_id"]].append(v)
    return idx, clusters


def mcnemar_exact(b, c):
    """Two-sided exact McNemar on the discordant pairs (Section 2.1, criterion 2)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) * (0.5 ** n)
    return min(1.0, 2 * tail)


def wilson(k, n):
    if not n:
        return (float("nan"), float("nan"))
    z = 1.959963984540054
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


# ---------------------------------------------------------------- part 1

def part1_canary(dirs, model_field):
    """The change in core_ok between the canary run before the first test trial of a model and the one after
    its last, over the same units, with the exact McNemar test and the recorded identity of the model."""
    if not dirs:
        return {"available": False, "reason": "no canary run folders given"}
    before, after, identity, seen = defaultdict(dict), defaultdict(dict), defaultdict(set), set()
    for d in dirs:
        base = os.path.basename(d.rstrip(os.sep))
        if base.startswith("canary_before_"):
            side, rest = before, base[len("canary_before_"):]
        elif base.startswith("canary_after_"):
            side, rest = after, base[len("canary_after_"):]
        else:
            continue
        pin = rest
        for pack in PACKS:
            if rest.endswith("_" + pack):
                pin = rest[: -(len(pack) + 1)]
                break
        recs, _err = load_trials([d])
        seen.add(pin)
        for r in recs:
            v = ok_of(r)
            if v is None:
                continue
            side[pin][(r.get("pack"), r["unit_id"])] = v
            identity[pin].add(tuple(str(r.get(f)) for f in IDENTITY_FIELDS))
    rows, out = [], {}
    for pin in sorted(seen):
        keys = sorted(set(before[pin]) & set(after[pin]), key=str)
        if not keys:
            continue
        nb = sum(before[pin][k] for k in keys)
        na = sum(after[pin][k] for k in keys)
        b = sum(1 for k in keys if before[pin][k] == 1 and after[pin][k] == 0)
        c = sum(1 for k in keys if before[pin][k] == 0 and after[pin][k] == 1)
        p = mcnemar_exact(b, c)
        ident = sorted(identity[pin])
        out[pin] = {"units": len(keys), "before": nb / len(keys), "after": na / len(keys),
                    "delta_pp": 100 * (na - nb) / len(keys), "discordant_down": b, "discordant_up": c,
                    "mcnemar_p": p, "identity_values": [list(x) for x in ident],
                    "identity_changed": len(ident) > 1,
                    "flagged": bool(len(ident) > 1 or p < C.ALPHA)}
        rows.append([pin, len(keys), pct(nb / len(keys)), pct(na / len(keys)),
                     f"{100 * (na - nb) / len(keys):+.1f}", b, c, num(p, 3),
                     "changed" if len(ident) > 1 else "same",
                     "yes" if out[pin]["flagged"] else "no"])
    return {"available": True, "models": out, "rows": rows,
            "any_flagged": any(v["flagged"] for v in out.values())}


# ---------------------------------------------------------------- part 2

def part2_supplementary(dirs, model_field):
    """The development results of the models served from the borrowed endpoint, outside the panel.  Their
    names are the ones the endpoint gave; the weights and the quantisation are not verified or pinned."""
    if not dirs:
        return {"available": False, "reason": "no supplementary run folders given"}
    recs, _err = load_trials(dirs)
    idx, _cl = index_cells(recs, "dev", model_field)
    endpoint_names = sorted({r.get("model") for r in recs if r.get("model")})
    unmatched = sorted({m for (_p, m, _c) in index_cells(recs, "dev", model_field)[0]
                        if m not in SUPPLEMENTARY_NAMES})
    models = sorted({m for (_p, m, _c) in idx})
    cells, rows = {}, []
    for m in models:
        for pack in PACKS:
            for cond in CONDITIONS:
                d = idx.get((pack, m, cond))
                if not d:
                    continue
                means = [statistics.fmean(v) for v in d.values()]
                cells[f"{m}|{pack}|{cond}"] = {"units": len(means), "core_ok": statistics.fmean(means)}
    for m in models:
        for pack in PACKS:
            row = [SUPPLEMENTARY_NAMES.get(m, "not in the plan"), m, pack]
            for cond in CONDITIONS:
                k = f"{m}|{pack}|{cond}"
                row.append(pct(cells[k]["core_ok"]) if k in cells else "n/a")
            rows.append(row)
    vals = [v["core_ok"] for v in cells.values()]
    return {"available": True, "endpoint_names": endpoint_names, "cells": cells, "rows": rows,
            "names_in_the_plan": SUPPLEMENTARY_NAMES, "backends_not_in_the_plan": unmatched,
            "lowest_cell": min(vals) if vals else None, "highest_cell": max(vals) if vals else None}


# ---------------------------------------------------------------- part 3

def part3_cost(recs, model_field):
    """The prompt and completion tokens, the latency and the cost of the test trials, per condition and per
    standard.  The cost of a locally served model is not billed, so it is counted apart."""
    per_cond = defaultdict(lambda: {"pt": [], "ct": [], "lat": [], "cost": [], "billed": 0, "free": 0})
    per_cell = defaultdict(list)
    for r in recs:
        if r.get("task", "rename") != "rename" or r.get("split") != "test":
            continue
        cond, pack = r.get("condition"), r.get("pack")
        d = per_cond[cond]
        d["pt"].append(r.get("prompt_tokens") or 0)
        d["ct"].append(r.get("completion_tokens") or 0)
        d["lat"].append(r.get("latency_s") or 0.0)
        cu = r.get("cost_usd")
        if cu:
            d["cost"].append(cu)
            d["billed"] += 1
        else:
            d["free"] += 1
        per_cell[(pack, cond)].append(r.get("prompt_tokens") or 0)
    cond_rows, conds = [], {}
    for cond in [c for c in CONDITIONS if c in per_cond] + [c for c in per_cond if c not in CONDITIONS]:
        d = per_cond[cond]
        usd = (statistics.fmean(d["cost"]) * 100) if d["cost"] else None
        conds[cond] = {"trials": len(d["pt"]), "prompt_tokens": statistics.fmean(d["pt"]),
                       "completion_tokens": statistics.fmean(d["ct"]), "latency_s": statistics.fmean(d["lat"]),
                       "usd_per_100_billed_trials": usd, "billed_trials": d["billed"],
                       "unbilled_trials": d["free"]}
        cond_rows.append([cond, len(d["pt"]), num(statistics.fmean(d["pt"]), 0),
                          num(statistics.fmean(d["ct"]), 0), num(statistics.fmean(d["lat"]), 2),
                          num(usd, 3) if usd is not None else "not billed", d["billed"]])
    pack_rows, ratios = [], {}
    for pack in PACKS:
        row = [pack]
        vals = {}
        for cond in CONDITIONS:
            v = per_cell.get((pack, cond))
            vals[cond] = statistics.fmean(v) if v else None
            row.append(num(vals[cond], 0) if vals[cond] else "n/a")
        if vals.get(FULLDOC) and vals.get(SELECTION):
            ratios[pack] = vals[FULLDOC] / vals[SELECTION]
            row.append(f"{ratios[pack]:.1f}x")
        else:
            row.append("n/a")
        pack_rows.append(row)
    pooled = None
    if conds.get(FULLDOC) and conds.get(SELECTION):
        pooled = conds[FULLDOC]["prompt_tokens"] / conds[SELECTION]["prompt_tokens"]
    return {"available": bool(conds), "conditions": conds, "condition_rows": cond_rows,
            "pack_rows": pack_rows, "fulldoc_over_selection": ratios, "pooled_ratio": pooled}


# ---------------------------------------------------------------- part 4

def part4_anchors(dirs, model_field):
    """The anchor packs of Vol. 1 rerun with the Vol. 2 pins of the two locally served models: the zero-shot
    compliance and the compliance with selection, as the extreme points of the H2 relation.  Not counted in
    H1 and not compared with the Vol. 1 numbers.  The trials that stopped at the output limit are counted
    apart, because a trial that could not finish its answer is not evidence about the rule it was given."""
    if not dirs:
        return {"available": False,
                "reason": "no anchor run folders given; the anchor packs were not rerun"}
    recs, _err = load_trials(dirs)
    cells, fin = {}, defaultdict(Counter)
    for r in recs:
        if r.get("task", "rename") != "rename":
            continue
        fin[(r.get("pack"), r.get(model_field), r.get("condition"))][r.get("finish")] += 1
    for split in ("test", "dev"):
        idx, _cl = index_cells(recs, split, model_field)
        for (pack, model, cond), d in sorted(idx.items(), key=str):
            if cond not in (NONE, SELECTION):
                continue
            means = [statistics.fmean(v) for v in d.values()]
            f = fin[(pack, model, cond)]
            cells[f"{pack}|{model}|{cond}|{split}"] = {
                "units": len(means), "core_ok": statistics.fmean(means),
                "trials": sum(f.values()), "at_output_limit": f.get("length", 0),
                "finish": dict(f)}
    rows = []
    for key in sorted(cells):
        pack, model, cond, split = key.split("|")
        c = cells[key]
        rows.append([pack, model.split(":")[-1], split, cond, c["units"], pct(c["core_ok"]),
                     c["trials"], c["at_output_limit"]])
    gains = {}
    for key in list(cells):
        pack, model, cond, split = key.split("|")
        if cond != SELECTION:
            continue
        base = cells.get(f"{pack}|{model}|{NONE}|{split}")
        if base:
            gains[f"{pack}|{model}|{split}"] = {
                "zero_shot": base["core_ok"], "selection": cells[key]["core_ok"],
                "gain_pp": 100 * (cells[key]["core_ok"] - base["core_ok"]),
                "at_output_limit": base["at_output_limit"] + cells[key]["at_output_limit"]}
    seen = {k.split("|")[0] for k in cells}
    reasons = []
    for (pack, model, cond), f in sorted(fin.items(), key=str):
        for why, k in sorted(f.items(), key=str):
            reasons.append({"pack": pack, "model": model, "condition": cond,
                            "finish": str(why), "trials": k})
    limit = sum(c["at_output_limit"] for c in cells.values())
    return {"available": True, "cells": cells, "rows": rows, "h2_points": gains,
            "packs_seen": sorted(seen),
            "packs_missing": [p for p in ANCHOR_PACKS if p not in seen],
            "finish_reasons": reasons,
            "trials_at_the_output_limit": limit,
            "total_at_output_limit": limit}


# ---------------------------------------------------------------- part 5

def part5_kind(dirs):
    """How often the inferred kind equals the kind in the unit metadata, on the test split, with the pairs it
    confuses and the trials whose kind is wrong and whose core_ok still passes.  A drop in compliance bounds
    the effect of a wrong kind, not its rate: two kinds can share one casing rule.

    The csv of a run holds the records of every run that shares its keys, so a trial can appear more than
    once and rows with no kind field belong to the other conditions.  One record per (pack, unit, repeat,
    model) is kept, the last one read, which is what `report.load_trials` does for the json records."""
    if not dirs:
        return {"available": False, "reason": "no inferred-kind run folders given"}
    rows_read, blank, kept = Counter(), Counter(), {}
    for d in dirs:
        path = os.path.join(d, "trials.csv")
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                pack = (r.get("pack") or "").strip()
                rows_read[pack] += 1
                if not (r.get("kind_inferred") or "").strip():
                    blank[pack] += 1
                    continue
                kept[(pack, r.get("unit_id"), r.get("repeat"), r.get("backend"))] = r
    per = defaultdict(lambda: {"scored": 0, "ok": 0, "wrong_core_ok": 0, "units": set(),
                               "wrong_units": set()})
    conf, status = Counter(), Counter()
    for (pack, unit, _rep, _mdl), r in kept.items():
        p = per[pack]
        p["scored"] += 1
        p["units"].add(unit)
        inferred = (r.get("kind_inferred") or "").strip()
        truth = (r.get("kind") or "").strip()
        status[(pack, (r.get("kind_status") or "").strip() or "(blank)")] += 1
        flag = (r.get("kind_ok") or "").strip()
        good = (flag == "True") if flag in ("True", "False") else (inferred == truth)
        if good:
            p["ok"] += 1
        else:
            conf[(pack, truth or "(blank)", inferred)] += 1
            p["wrong_units"].add(unit)
            if (r.get("m_core_ok") or "").strip() == "True":
                p["wrong_core_ok"] += 1
    out, rows = {}, []
    for pack in PACKS:
        p = per.get(pack)
        if not p or not p["scored"]:
            continue
        lo, hi = wilson(p["ok"], p["scored"])
        out[pack] = {"csv_rows_read": rows_read[pack], "rows_without_a_kind_field": blank[pack],
                     "scored_trials": p["scored"], "distinct_tasks": len(p["units"]),
                     "correct": p["ok"], "accuracy": p["ok"] / p["scored"],
                     "ci_low": lo, "ci_high": hi,
                     "accuracy_lower_one_sided": clopper_pearson_lower(p["ok"], p["scored"]),
                     "wrong_trials": p["scored"] - p["ok"], "wrong_tasks": len(p["wrong_units"]),
                     "wrong_but_core_ok": p["wrong_core_ok"]}
        rows.append([pack, p["scored"], len(p["units"]), pct(p["ok"] / p["scored"], 1),
                     f"[{pct(lo)}, {pct(hi)}]", p["scored"] - p["ok"], len(p["wrong_units"]),
                     p["wrong_core_ok"]])
    return {"available": bool(out), "packs": out, "rows": rows,
            "confusions": [{"pack": k[0], "metadata_kind": k[1], "inferred_kind": k[2], "trials": v}
                           for k, v in sorted(conf.items(), key=lambda x: -x[1])],
            "kind_status": [{"pack": k[0], "status": k[1], "trials": v}
                            for k, v in sorted(status.items(), key=str)]}


# ---------------------------------------------------------------- part 6

def part6_paired(idx, clusters):
    """The paired wins, ties and losses behind the mean difference of every cell of H3, so that a cell in
    which no task differs is not read as a cell in which the difference is known to be small."""
    rows, cells = [], {}
    for pack in PACKS:
        models = sorted({m for (p, m, _c) in idx if p == pack})
        for model in models:
            for ref in (FULLDOC, NONE):
                a = idx.get((pack, model, SELECTION))
                b = idx.get((pack, model, ref))
                if not a or not b:
                    continue
                keys = sorted(set(a) & set(b))
                win = tie = loss = 0
                deltas = []
                for k in keys:
                    da = statistics.fmean(a[k]) - statistics.fmean(b[k])
                    deltas.append(da)
                    if da > 0:
                        win += 1
                    elif da < 0:
                        loss += 1
                    else:
                        tie += 1
                mean = statistics.fmean(deltas) if deltas else float("nan")
                cl = {clusters.get((pack, k), k) for k in keys}
                key = f"{pack}|{model}|{SELECTION}-vs-{ref}"
                cells[key] = {"tasks": len(keys), "clusters": len(cl), "wins": win, "ties": tie,
                              "losses": loss, "mean_diff_pp": 100 * mean,
                              "all_tasks_identical": tie == len(keys)}
                rows.append([pack, model.split(":")[-1], ref, len(keys), win, tie, loss,
                             f"{100 * mean:+.2f}", "yes" if tie == len(keys) else "no"])
    vs_full = [v for k, v in cells.items() if k.endswith(FULLDOC)]
    return {"available": bool(cells), "cells": cells, "rows": rows,
            "identical_cells_vs_fulldoc": sum(1 for v in vs_full if v["all_tasks_identical"]),
            "cells_vs_fulldoc": len(vs_full),
            "cells_with_a_loss_vs_fulldoc": sum(1 for v in vs_full if v["losses"] > 0)}


# ---------------------------------------------------------------- part 7

def part7_clusters(idx, clusters):
    """The number of source file clusters among the test tasks of each standard, which is the number the
    cluster bootstrap resamples; it is not the number of files in the pinned corpus."""
    by_pack = defaultdict(lambda: defaultdict(set))
    for (pack, _model, _cond), d in idx.items():
        for unit in d:
            by_pack[pack][clusters.get((pack, unit), unit)].add(unit)
    out, rows = {}, []
    for pack in PACKS:
        groups = by_pack.get(pack)
        if not groups:
            continue
        tasks = len({u for s in groups.values() for u in s})
        sizes = sorted((len(s) for s in groups.values()), reverse=True)
        out[pack] = {"tasks": tasks, "clusters": len(groups), "tasks_per_cluster": tasks / len(groups),
                     "largest_cluster": sizes[0], "singletons": sum(1 for s in sizes if s == 1)}
        rows.append([pack, tasks, len(groups), num(tasks / len(groups), 2), sizes[0],
                     sum(1 for s in sizes if s == 1)])
    return {"available": bool(out), "packs": out, "rows": rows}


# ---------------------------------------------------------------- part 8

def part8_h2_range(idx, anchors):
    """The zero-shot compliance of every cell next to the gain selection adds, over the three standards of
    this study and the anchor packs together.  Reported as a description of the range the evidence covers:
    the cells share tasks within a standard and the anchors reuse the packs of Vol. 1, so the points are not
    independent and no test is run on them here."""
    pts, rows = [], []
    for pack in PACKS:
        for model in sorted({m for (p, m, _c) in idx if p == pack}):
            a, b = idx.get((pack, model, SELECTION)), idx.get((pack, model, NONE))
            if not a or not b:
                continue
            keys = sorted(set(a) & set(b))
            zs = statistics.fmean([statistics.fmean(b[k]) for k in keys])
            sel = statistics.fmean([statistics.fmean(a[k]) for k in keys])
            pts.append((zs, sel - zs))
            rows.append([pack, model.split(":")[-1], "panel", pct(zs), pct(sel),
                         f"{100 * (sel - zs):+.2f}"])
    if anchors.get("available"):
        for key, g in sorted(anchors["h2_points"].items()):
            pack, model, split = key.split("|")
            if split != "test":
                continue
            pts.append((g["zero_shot"], g["selection"] - g["zero_shot"]))
            rows.append([pack, model.split(":")[-1], "anchor", pct(g["zero_shot"]),
                         pct(g["selection"]), f"{g['gain_pp']:+.2f}"])
    if len(pts) < 3:
        return {"available": False, "reason": "fewer than three cells"}
    xs = [p[0] for p in pts]
    rho = None
    try:
        rho = spearman_permutation([p[0] for p in pts], [p[1] for p in pts])[0]
    except Exception:
        rho = None
    return {"available": True, "rows": rows, "points": len(pts),
            "zero_shot_min": min(xs), "zero_shot_max": max(xs),
            "spearman_rho": rho}


# ---------------------------------------------------------------- render

def render(res):
    L = ["# Addendum A13 - the results the design promised, and three analyses added after the data", "",
         "Parts 1 to 4 are reporting the frozen plan asks for and the manuscript left out. Parts 5 to 7 were",
         "added after the data were seen. No part carries a decision rule and no part calls a model again.", ""]

    p = res["part1"]
    L += ["## Part 1. The canary runs of every model (registered: Section 2.1)", ""]
    if not p["available"]:
        L += [f"Not available: {p['reason']}", ""]
    else:
        L += [table(["model pin", "units", "core_ok before", "core_ok after", "delta (pp)",
                     "down", "up", "McNemar p", "recorded identity", "flagged"], p["rows"]), "",
              f"Models flagged by the drift criteria: {'yes' if p['any_flagged'] else 'none'}.", ""]

    p = res["part2"]
    L += ["## Part 2. The supplementary models on the development units (registered: Section 2.2)", ""]
    if not p["available"]:
        L += [f"Not available: {p['reason']}", ""]
    else:
        L += ["The names are the ones the endpoint returned; the weights, the revision and the quantisation",
              "are neither verified nor pinned, and these models were never run on the test split.", "",
              "Names returned by the endpoint: " + ", ".join(p["endpoint_names"]) + ".", "",
              table(["model in the plan", "label the endpoint returned", "standard"]
                    + list(CONDITIONS), p["rows"]), "",
              f"Lowest cell {pct(p['lowest_cell'])} and highest {pct(p['highest_cell'])} of core_ok.", ""]

    p = res["part3"]
    L += ["## Part 3. Tokens, latency and cost of the test trials (registered: Section 5)", ""]
    if not p["available"]:
        L += ["Not available.", ""]
    else:
        L += [table(["condition", "trials", "prompt tokens", "completion tokens", "latency (s)",
                     "USD per 100 billed trials", "billed trials"], p["condition_rows"]), "",
              "A locally served model is not billed, so its trials are counted in the last column only.", "",
              table(["standard"] + list(CONDITIONS) + ["fulldoc / selection"], p["pack_rows"]), ""]
        if p["pooled_ratio"]:
            L += [f"Pooled over the three standards the ratio is {p['pooled_ratio']:.1f}x, which is the length",
                  "of the Odoo guideline more than a property of the method; the ratio is reported per",
                  "standard and the pooled value is not used in a claim.", ""]

    p = res["part4"]
    L += ["## Part 4. The anchor packs (registered: Section 2.3)", ""]
    if not p["available"]:
        L += [f"Not available: {p['reason']}", ""]
    else:
        L += [table(["pack", "model", "split", "condition", "units", "core_ok", "trials",
                     "trials at the output limit"], p["rows"]), ""]
        if p["h2_points"]:
            L += [table(["pack", "model", "split", "zero-shot core_ok", "with selection", "gain (pp)"],
                        [[k.split("|")[0], k.split("|")[1].split(":")[-1], k.split("|")[2],
                          pct(g["zero_shot"]), pct(g["selection"]), num(g["gain_pp"], 2)]
                         for k, g in sorted(p["h2_points"].items())]), "",
                  "The anchor packs hold the low end of the zero-shot range that the three public standards",
                  "do not reach. A model that gains nothing on a public standard gains here, so a cell",
                  "without a difference bounds the headroom of that cell and not the method.", ""]
        cut = Counter()
        for f in p["finish_reasons"]:
            if str(f["finish"]) == "length":
                cut[str(f["condition"])] += f["trials"]
        L += [table(["pack", "model", "condition", "finish", "trials"],
                    [[f["pack"], f["model"].split(":")[-1], f["condition"], f["finish"], f["trials"]]
                     for f in p["finish_reasons"]]), ""]
        line = f"Trials that ended at the output limit: {p['trials_at_the_output_limit']}"
        if cut:
            line += ", of which " + ", ".join(f"{n} in {c}"
                                              for c, n in sorted(cut.items(), key=lambda kv: (-kv[1], kv[0])))
        L += [line + ".",
              "The limit is the one the pin fixes, no trial is dropped and the count is reported as a",
              "sensitivity.", ""]
        if len(cut) > 1 or (cut and NONE in cut):
            L += ["The trials cut short are not spread evenly over the conditions. A prompt that carries the",
                  "selected rules ends sooner than one that carries none, which the completion tokens of",
                  "Part 3 show as well, so the count sits where the model was given no rule in context and",
                  "is read as a property of the condition and not of the deployment alone.", ""]
        if p["packs_missing"]:
            L += ["Anchor packs not rerun: " + ", ".join(p["packs_missing"]) + ".", ""]
            if "public5" in p["packs_missing"]:
                L += ["The pack of that anchor is not part of the published replication package of Vol. 1",
                      "and only files derived from it are at hand, so the registered pair of anchors is",
                      "reported with one anchor run and the other recorded as a deviation.", ""]

    p = res["part5"]
    L += ["## Part 5. The accuracy of the inferred kind (added after the data)", ""]
    if not p["available"]:
        L += [f"Not available: {p['reason']}", ""]
    else:
        L += [table(["standard", "scored trials", "distinct tasks", "kind correct", "95% interval",
                     "wrong trials", "wrong tasks", "wrong and core_ok passes"], p["rows"]), "",
              "A wrong kind that selects the same casing rule leaves core_ok unchanged, so the last column",
              "says how much of the small drop in compliance a wrong kind could not have caused.", ""]
        if p["confusions"]:
            L += [table(["standard", "kind in the metadata", "kind inferred", "trials"],
                        [[c["pack"], c["metadata_kind"], c["inferred_kind"], c["trials"]]
                         for c in p["confusions"][:12]]), ""]
        L += [table(["standard", "kind_status", "trials"],
                    [[s["pack"], s["status"], s["trials"]] for s in p["kind_status"]]), ""]

    p = res["part6"]
    L += ["## Part 6. Wins, ties and losses behind the differences of H3 (added after the data)", ""]
    if not p["available"]:
        L += ["Not available.", ""]
    else:
        L += [table(["standard", "model", "reference", "tasks", "wins", "ties", "losses",
                     "mean difference (pp)", "every task identical"], p["rows"]), "",
              f"Against the full document {p['identical_cells_vs_fulldoc']} of {p['cells_vs_fulldoc']} cells",
              f"give the same score on every task, and {p['cells_with_a_loss_vs_fulldoc']} cells contain at",
              "least one task on which selection scores lower. A cell in which no task differs shows",
              "agreement between the two prompts, not a bound on the size of a difference.", ""]

    p = res["part7"]
    L += ["## Part 7. The source file clusters of the test split (added after the data)", ""]
    if not p["available"]:
        L += ["Not available.", ""]
    else:
        L += [table(["standard", "tasks", "clusters", "tasks per cluster", "largest cluster",
                     "clusters with one task"], p["rows"]), "",
              "These are the clusters the bootstrap resamples. The number of files in the pinned corpus is",
              "larger and is not the number of independent units of the test split.", ""]

    p = res["part8"]
    L += ["## Part 8. The range the H2 relation covers (added after the data)", ""]
    if not p["available"]:
        L += [f"Not available: {p['reason']}", ""]
    else:
        L += [table(["standard", "model", "role", "zero-shot core_ok", "with selection", "gain (pp)"],
                    p["rows"]), "",
              f"{p['points']} cells, zero-shot compliance from {pct(p['zero_shot_min'])} to "
              f"{pct(p['zero_shot_max'])}" + (f", Spearman rho {num(p['spearman_rho'], 2)}"
                                              if p["spearman_rho"] is not None else "") + ".",
              "The cells share tasks within a standard and the anchor packs are those of Vol. 1, so the",
              "points are not independent; the value describes the range of the evidence and is not a test.",
              ""]

    s = res["settings"]
    L += ["## Settings", "",
          table(["key", "value"], [[k, v if not isinstance(v, list) else ", ".join(map(str, v))]
                                   for k, v in s.items()]), ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--meta", nargs="+", required=True,
                    help="test runs with the human ontology and the kind from the metadata")
    ap.add_argument("--infer", nargs="+", default=None, help="test runs with the inferred kind (part 5)")
    ap.add_argument("--canary", nargs="+", default=None, help="canary_before_* and canary_after_* (part 1)")
    ap.add_argument("--supplementary", nargs="+", default=None, help="pilot runs outside the panel (part 2)")
    ap.add_argument("--anchors", nargs="+", default=None, help="anchor pack runs (part 4)")
    ap.add_argument("--model-field", default="backend")
    ap.add_argument("--cluster-field", default="file")
    ap.add_argument("--out", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    meta_dirs = expand(a.meta)
    missing = [d for d in meta_dirs if not os.path.exists(os.path.join(d, "trials.jsonl"))]
    if missing:
        sys.exit("no trials.jsonl in: " + ", ".join(missing))
    recs, _err = load_trials(meta_dirs)
    idx, clusters = index_cells(recs, "test", a.model_field, a.cluster_field)

    res = {"part1": part1_canary(expand(a.canary), a.model_field),
           "part2": part2_supplementary(expand(a.supplementary), a.model_field),
           "part3": part3_cost(recs, a.model_field),
           "part4": part4_anchors(expand(a.anchors), a.model_field),
           "part5": part5_kind(expand(a.infer)),
           "part6": part6_paired(idx, clusters),
           "part7": part7_clusters(idx, clusters),
           "part8": None,
           "settings": {"meta_runs": meta_dirs, "infer_runs": expand(a.infer),
                        "canary_runs": expand(a.canary), "supplementary_runs": expand(a.supplementary),
                        "anchor_runs": expand(a.anchors), "model_field": a.model_field,
                        "cluster_field": a.cluster_field, "python": sys.version.split()[0]}}
    res["part8"] = part8_h2_range(idx, res["part4"])
    text = render(res)
    print(text)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text + "\n")
    if a.json:
        json.dump(res, open(a.json, "w", encoding="utf-8"), indent=1, default=str)


if __name__ == "__main__":
    main()
