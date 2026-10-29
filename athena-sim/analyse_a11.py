#!/usr/bin/env python3
"""analyse_a11 - the analyses of addendum A11 (exploratory; no decision rule, no new model call).

  python analyse_a11.py --meta runs/test_*_meta [--out a11.md] [--json a11.json]

  --meta  test runs with the human ontology and the kind from metadata (the cells of Table IV)

Parts: 1 the cells of Table IV with the task as the unit (trial proportion with its Wilson interval, the mean of
the task means, a percentile bootstrap over tasks, and a cluster bootstrap over source files, both with the seed
and the number of resamples of the confirmatory analysis); 2 the same cells without the trials that ended at the
output limit, with the number removed and the paired difference between selection and each retrieval condition
before and after; 3 the size of the part of each standard that concerns naming, against the whole text sent by
fulldoc and the rules sent by selection, in characters and in tokens at the rate measured on the trials.

A task is a unit_id; its score is the mean of core_ok over the repeats. Standard library only.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import statistics
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from athena import confirmatory as C  # noqa: E402
from athena.passages import split_passages  # noqa: E402
from athena.report import load_trials, wilson  # noqa: E402

PACKS = C.DEFAULT_PACKS
SPLIT = "test"
CONDITIONS = ("none", "fulldoc", "chunk", "bm25", "dense", "graph")
RETRIEVAL = ("chunk", "bm25", "dense")
SELECTION = "graph"
LIMIT_FINISH = "length"                 # the value of `finish` of a trial that stopped at the output limit

# Part 3: a heading or a passage is counted as naming if it matches this expression (case-insensitive).
NAMING_RE = re.compile(r"\bnam(e|es|ing)\b|\bidentifier|\bcasing\b|camelcase|snake_case|pascalcase"
                       r"|\bprefix|\bsuffix|\babbreviat", re.I)


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


def ratio(x, nd=1):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:,.{nd}f}x"


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def index_cells(recs, model_field="backend", cluster_field="file", drop_at_limit=False):
    """idx[(pack, model, condition)][unit_id] = [core_ok as 0/1 per repeat]; clusters[(pack, unit)] = source file.
    With `drop_at_limit` the trials whose `finish` is the output limit are left out, and their number is counted."""
    idx: dict = defaultdict(lambda: defaultdict(list))
    clusters: dict = {}
    dropped: dict = defaultdict(int)
    for r in recs:
        if r.get("task", "rename") != "rename" or r.get("split") != SPLIT:
            continue
        v = (r.get("metrics") or {}).get("core_ok")
        if v is None:
            continue
        key = (r.get("pack"), r.get(model_field), r.get("condition"))
        clusters[(r.get("pack"), r["unit_id"])] = r.get(cluster_field) or r.get("snippet_id") or r["unit_id"]
        if r.get("finish") == LIMIT_FINISH:
            dropped[key] += 1
            if drop_at_limit:
                continue
        idx[key][r["unit_id"]].append(1.0 if v else 0.0)
    return idx, clusters, dropped


def models_of(idx, pack):
    return sorted({m for (p, m, _c) in idx if p == pack})


def cell_stats(cell, clusters, pack, b, seed):
    """Trial proportion with its Wilson interval, the mean of the task means, and the two bootstrap intervals."""
    units = sorted(cell)
    if not units:
        return None
    vals = [sum(cell[u]) / len(cell[u]) for u in units]
    k = int(round(sum(sum(cell[u]) for u in units)))
    n = sum(len(cell[u]) for u in units)
    w_lo, w_hi = wilson(k, n)
    mean_tasks = statistics.fmean(vals)
    # Wilson at the task level: the same point estimate with the number of tasks as the number of observations.
    # Added because a percentile bootstrap is degenerate in a cell in which every task scores 1.
    tw_lo, tw_hi = wilson(int(round(mean_tasks * len(units))), len(units))
    t_lo, t_hi = C.cluster_bootstrap_ci(units, vals, {}, pack, b, seed)          # each task resampled on its own
    f_lo, f_hi = C.cluster_bootstrap_ci(units, vals, clusters, pack, b, seed)    # whole source files resampled
    return {"tasks": len(units), "files": len({clusters.get((pack, u), u) for u in units}), "trials": n,
            "trial_share": k / n, "wilson_low": w_lo, "wilson_high": w_hi,
            "task_mean": mean_tasks, "task_wilson_low": tw_lo, "task_wilson_high": tw_hi,
            "task_low": t_lo, "task_high": t_hi, "file_low": f_lo, "file_high": f_hi}


def part1_intervals(idx, clusters, b, seed):
    rows = []
    for pack in PACKS:
        for model in models_of(idx, pack):
            for cond in CONDITIONS:
                s = cell_stats(idx.get((pack, model, cond), {}), clusters, pack, b, seed)
                if s:
                    rows.append(dict(pack=pack, model=model, condition=cond, **s))
    return rows


def part2_limit(recs, clusters, b, seed):
    """The cells recomputed without the trials that ended at the output limit, and the paired differences."""
    full, _c, dropped = index_cells(recs)
    kept, _c2, _d = index_cells(recs, drop_at_limit=True)
    cells, pairs = [], []
    for pack in PACKS:
        for model in models_of(full, pack):
            for cond in CONDITIONS:
                a, kcell = full.get((pack, model, cond), {}), kept.get((pack, model, cond), {})
                n_drop = dropped.get((pack, model, cond), 0)
                if not a or n_drop == 0:
                    continue
                s_all = cell_stats(a, clusters, pack, b, seed)
                s_kept = cell_stats(kcell, clusters, pack, b, seed)
                cells.append({"pack": pack, "model": model, "condition": cond, "dropped": n_drop,
                              "trials_all": s_all["trials"], "share_all": s_all["trial_share"],
                              "task_mean_all": s_all["task_mean"], "trials_kept": s_kept["trials"],
                              "share_kept": s_kept["trial_share"], "task_mean_kept": s_kept["task_mean"],
                              "change_pp": 100 * (s_kept["task_mean"] - s_all["task_mean"])})
            for cond in RETRIEVAL:
                n_drop = dropped.get((pack, model, cond), 0) + dropped.get((pack, model, SELECTION), 0)
                if n_drop == 0:
                    continue
                u1, d1, _u, _d, _t = C.paired(full.get((pack, model, SELECTION), {}), full.get((pack, model, cond), {}))
                u2, d2, _u2, _d2, _t2 = C.paired(kept.get((pack, model, SELECTION), {}), kept.get((pack, model, cond), {}))
                if not u1 or not u2:
                    continue
                pairs.append({"pack": pack, "model": model, "baseline": cond, "dropped": n_drop,
                              "diff_all_pp": 100 * statistics.fmean(d1), "tasks_all": len(u1),
                              "diff_kept_pp": 100 * statistics.fmean(d2), "tasks_kept": len(u2)})
    return {"cells": cells, "pairs": pairs, "total_dropped": sum(dropped.values())}


def count_at_limit(dirs):
    """Trials whose `finish` is the output limit in the run files, including those that also carry an error
    (`load_trials` drops those, so the number of the analysis can be smaller)."""
    kept = err = 0
    for d in dirs:
        path = os.path.join(d, "trials.jsonl")
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("finish") == LIMIT_FINISH:
                    if r.get("error"):
                        err += 1
                    else:
                        kept += 1
    return {"without_error": kept, "with_error": err}


def context_of(prompt: str) -> str | None:
    """The text of the CODING STANDARD block of a prompt built by athena.prompts.build_prompt."""
    i = prompt.find("CODING STANDARD")
    j = prompt.find("\nCODE\n", i)
    if i < 0 or j < 0:
        return None
    return prompt[i + len("CODING STANDARD"):j].strip("\n")


def guess_format(text: str) -> str:
    md = len(re.findall(r"(?m)^#{1,6} \S", text))
    rst = len(re.findall(r"(?m)^[=\-~^\"'`:.*+#<>]{3,}\s*$", text))
    return "md" if md > rst else "rst"


def naming_parts(fulltext: str):
    """The passages of the document whose heading path, or whose own text, concerns naming (part 3).

    Two selections are reported, because a document may keep its naming rules in sections of their own or as items
    of one list: `heading` takes every passage under a heading that matches, `text` takes every passage that
    matches itself. Both are built from the passages of athena.passages, as the retrieval conditions are."""
    fmt = guess_format(fulltext)
    passages = split_passages(fulltext, fmt)
    by_heading, by_text, headings = [], [], []
    for _pid, body in passages:
        head = body.split("\n\n", 1)[0] if "\n\n" in body else ""
        if head and NAMING_RE.search(head):
            by_heading.append(body)
            if head not in headings:
                headings.append(head)
        if NAMING_RE.search(body):
            by_text.append(body)
    return {"format": fmt, "passages": len(passages), "chars_all": len(fulltext),
            "heading_passages": len(by_heading), "heading_chars": sum(len(b) for b in by_heading),
            "text_passages": len(by_text), "text_chars": sum(len(b) for b in by_text),
            "headings": headings}


def part3_naming(recs):
    """Sizes of the context of each condition, of the naming part of the document, and the implied token counts."""
    ctx: dict = defaultdict(list)                     # (pack, condition) -> context lengths
    tok: dict = defaultdict(list)                     # (pack, model, condition) -> (prompt_chars, prompt_tokens)
    fulltext: dict = {}
    for r in recs:
        if r.get("task", "rename") != "rename" or r.get("split") != SPLIT:
            continue
        pack, cond, model = r.get("pack"), r.get("condition"), r.get("backend")
        p = r.get("prompt") or ""
        c = context_of(p)
        if c is not None:
            ctx[(pack, cond)].append(len(c))
            if cond == "fulldoc" and pack not in fulltext:
                body = c.split("\n", 1)
                fulltext[pack] = body[1] if len(body) == 2 else c
        if r.get("prompt_tokens") and r.get("prompt_chars"):
            tok[(pack, model, cond)].append((r["prompt_chars"], r["prompt_tokens"]))
    sizes, rows = {}, []
    for pack in PACKS:
        if pack not in fulltext:
            continue
        sizes[pack] = naming_parts(fulltext[pack])
        sizes[pack]["context_chars"] = {c: statistics.fmean(ctx[(pack, c)]) for c in CONDITIONS if ctx.get((pack, c))}
        sel_chars = sizes[pack]["context_chars"].get(SELECTION)
        if sel_chars:
            sizes[pack]["chars_ratio_fulldoc"] = sizes[pack]["context_chars"].get("fulldoc", 0) / sel_chars
            sizes[pack]["chars_ratio_naming_heading"] = (sizes[pack]["heading_chars"] / sel_chars
                                                         if sizes[pack]["heading_chars"] else float("nan"))
            sizes[pack]["chars_ratio_naming_text"] = (sizes[pack]["text_chars"] / sel_chars
                                                      if sizes[pack]["text_chars"] else float("nan"))
        for model in sorted({m for (p, m, _c) in tok if p == pack}):
            fd = tok.get((pack, model, "fulldoc"))
            gr = tok.get((pack, model, SELECTION))
            if not fd or not gr:
                continue
            fd_chars, fd_tokens = statistics.fmean([x for x, _ in fd]), statistics.fmean([y for _, y in fd])
            gr_tokens = statistics.fmean([y for _, y in gr])
            cpt = fd_chars / fd_tokens                       # characters per token, measured on the fulldoc prompts
            cut_head = sizes[pack]["chars_all"] - sizes[pack]["heading_chars"]
            cut_text = sizes[pack]["chars_all"] - sizes[pack]["text_chars"]
            # A document with no heading that concerns naming has no naming-only form by heading; it is not an
            # empty standard, so no number is reported for it.
            est_head = fd_tokens - cut_head / cpt if sizes[pack]["heading_chars"] else float("nan")
            est_text = fd_tokens - cut_text / cpt if sizes[pack]["text_chars"] else float("nan")
            rows.append({"pack": pack, "model": model, "chars_per_token": cpt,
                         "tokens_fulldoc": fd_tokens, "tokens_selection": gr_tokens,
                         "ratio_fulldoc": fd_tokens / gr_tokens if gr_tokens else float("nan"),
                         "est_tokens_naming_heading": est_head, "est_tokens_naming_text": est_text,
                         "ratio_naming_heading": est_head / gr_tokens if gr_tokens else float("nan"),
                         "ratio_naming_text": est_text / gr_tokens if gr_tokens else float("nan")})
    return {"documents": sizes, "tokens": rows}


def render(res):
    L = ["# A11. Dependence in the intervals, trials at the output limit, and the naming part of the standards",
         "", "Exploratory. No decision rule, no new model call, no change to the main tables.", ""]

    L += ["## 1. The cells of Table IV with the task as the unit", "",
          "A percentile bootstrap is degenerate in a cell in which every task scores 1, so the Wilson interval "
          "with the number of tasks as the number of observations is reported next to it.", "",
          table(["pack", "model", "condition", "tasks", "files", "trials", "trials %", "Wilson (trials)",
                 "task mean %", "Wilson (tasks)", "bootstrap over tasks", "cluster bootstrap over files"],
                [[r["pack"], r["model"], r["condition"], r["tasks"], r["files"], r["trials"],
                  pct(r["trial_share"]), f"[{pct(r['wilson_low'])}, {pct(r['wilson_high'])}]",
                  pct(r["task_mean"]), f"[{pct(r['task_wilson_low'])}, {pct(r['task_wilson_high'])}]",
                  f"[{pct(r['task_low'])}, {pct(r['task_high'])}]",
                  f"[{pct(r['file_low'])}, {pct(r['file_high'])}]"] for r in res["part1"]]), ""]

    p2 = res["part2"]
    lim = res.get("at_limit") or {}
    L += ["## 2. Without the trials that ended at the output limit", "",
          f"Trials at the output limit: {p2['total_dropped']} in the analysis "
          f"({lim.get('without_error', '?')} without an error and {lim.get('with_error', '?')} with one "
          f"in the run files).", ""]
    if p2["cells"]:
        L += [table(["pack", "model", "condition", "at limit", "trials", "task mean %", "trials kept",
                     "task mean kept %", "change pp"],
                    [[r["pack"], r["model"], r["condition"], r["dropped"], r["trials_all"], pct(r["task_mean_all"]),
                      r["trials_kept"], pct(r["task_mean_kept"]), f"{r['change_pp']:+.1f}"] for r in p2["cells"]]), ""]
    if p2["pairs"]:
        L += ["Selection against each retrieval condition, on the tasks the two share:", "",
              table(["pack", "model", "baseline", "at limit", "tasks", "difference pp", "tasks kept",
                     "difference kept pp"],
                    [[r["pack"], r["model"], r["baseline"], r["dropped"], r["tasks_all"], f"{r['diff_all_pp']:+.1f}",
                      r["tasks_kept"], f"{r['diff_kept_pp']:+.1f}"] for r in p2["pairs"]]), ""]

    p3 = res["part3"]
    L += ["## 3. The naming part of each standard", "",
          table(["pack", "format", "passages", "chars (whole)", "naming by heading: passages / chars",
                 "naming by passage text: passages / chars", "context of selection (chars)",
                 "context chars: whole / selection", "naming by heading / selection", "naming by text / selection"],
                [[pack, d["format"], d["passages"], f"{d['chars_all']:,}",
                  f"{d['heading_passages']} / {d['heading_chars']:,}",
                  f"{d['text_passages']} / {d['text_chars']:,}",
                  num(d["context_chars"].get(SELECTION, float('nan')), 0),
                  ratio(d.get("chars_ratio_fulldoc", float('nan'))),
                  ratio(d.get("chars_ratio_naming_heading", float('nan'))),
                  ratio(d.get("chars_ratio_naming_text", float('nan')))]
                 for pack, d in p3["documents"].items()]), ""]
    for pack, d in p3["documents"].items():
        L += [f"Headings counted as naming in {pack}: " + ("; ".join(d["headings"]) if d["headings"] else "none"), ""]
    L += ["Tokens of the whole prompt (template, code and standard) as the provider counted them on the trials, "
          "and the tokens a naming-only document implies at the rate of characters per token measured on the "
          "fulldoc prompts of the same cell. The ratios of the table above are of the standard text alone, so they "
          "are larger than these:", "",
          table(["pack", "model", "chars/token", "fulldoc tokens", "selection tokens", "fulldoc / selection",
                 "naming by heading (est.)", "ratio", "naming by text (est.)", "ratio"],
                [[r["pack"], r["model"], num(r["chars_per_token"], 2), num(r["tokens_fulldoc"], 0),
                  num(r["tokens_selection"], 0), ratio(r["ratio_fulldoc"]),
                  num(r["est_tokens_naming_heading"], 0), ratio(r["ratio_naming_heading"]),
                  num(r["est_tokens_naming_text"], 0), ratio(r["ratio_naming_text"])]
                 for r in p3["tokens"]]), ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--meta", nargs="+", required=True)
    ap.add_argument("--model-field", default="backend")
    ap.add_argument("--cluster-field", default="file")
    ap.add_argument("--resamples", type=int, default=C.BOOT_B)
    ap.add_argument("--seed", type=int, default=C.BOOT_SEED)
    ap.add_argument("--out", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    dirs = expand(a.meta)
    missing = [d for d in dirs if not os.path.exists(os.path.join(d, "trials.jsonl"))]
    if missing:
        sys.exit("no trials.jsonl in: " + ", ".join(missing))
    recs, _err = load_trials(dirs)
    idx, clusters, _dropped = index_cells(recs, a.model_field, a.cluster_field)
    res = {"part1": part1_intervals(idx, clusters, a.resamples, a.seed),
           "part2": part2_limit(recs, clusters, a.resamples, a.seed),
           "at_limit": count_at_limit(dirs),
           "part3": part3_naming(recs),
           "settings": {"resamples": a.resamples, "seed": a.seed, "runs": dirs}}
    text = render(res)
    print(text)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text + "\n")
    if a.json:
        json.dump(res, open(a.json, "w", encoding="utf-8"), indent=1, default=str)


if __name__ == "__main__":
    main()
