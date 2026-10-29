#!/usr/bin/env python3
"""analyse_a12 - the analyses of addendum A12 (exploratory; no decision rule, no new model call).

  python analyse_a12.py --meta runs/test_*_meta --llm runs/test_*_llm
                        [--curation DIR] [--runs runs] [--out a12.md] [--json a12.json]

  --meta  test runs with the human ontology and the kind from metadata (the cells of Table IV)
  --llm   the same cells with the LLM-drafted ontology (the other side of H4)

Parts: 1 the agreement of the three rounds of a task, per cell and pooled by condition, with the units whose
rounds disagree in every cell of a model; 2 the difference H4 could detect, from the standard error of the
cluster bootstrap over source files, next to the equivalence margin of 5 pp; 3 the renames to fresh names of H6
that the scope-aware check flags, with the reason each check gives; 4 two cells read by hand and quoted.

A task is a unit_id; its score is the mean of core_ok over the repeats. Standard library only.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import random
import statistics
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from athena import confirmatory as C  # noqa: E402
from athena.passages import split_passages  # noqa: E402
from athena.report import load_trials  # noqa: E402
from athena.secondary import H4_MARGIN  # noqa: E402

PACKS = C.DEFAULT_PACKS
SPLIT = "test"
CONDITIONS = ("none", "fulldoc", "chunk", "bm25", "dense", "graph")
SELECTION = "graph"
DENSE = "dense"
Z_975 = 1.959963984540054          # two-sided 5% level
Z_80 = 0.8416212335729143          # 80% power
QUOTE_CHARS = 240                  # a quoted passage is cut at this length, marked with an ellipsis
READ_N = 10                        # trials or units read by hand in part 4
DRAFTING_MODEL = "luna"            # the model that drafted the LLM ontology (part 4, first cell)
READ_PACK_A = "godot"
READ_PACK_B = "dotnet-runtime"
READ_COND_A = "none"               # part 4, first cell: the condition in which A8 counts the misses
PREFIXES = ("p_", "r_")            # part 4, first cell: the Godot parameter prefix of A8


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


def cut(text, n=QUOTE_CHARS):
    t = " ".join((text or "").split())
    return t if len(t) <= n else t[:n] + " ..."


def index_cells(recs, model_field="backend", cluster_field="file"):
    """idx[(pack, model, condition)][unit_id] = [core_ok as 0/1 per repeat]; clusters[(pack, unit)] = source file."""
    idx: dict = defaultdict(lambda: defaultdict(list))
    clusters: dict = {}
    for r in recs:
        if r.get("task", "rename") != "rename" or r.get("split") != SPLIT:
            continue
        v = (r.get("metrics") or {}).get("core_ok")
        if v is None:
            continue
        clusters[(r.get("pack"), r["unit_id"])] = r.get(cluster_field) or r.get("snippet_id") or r["unit_id"]
        idx[(r.get("pack"), r.get(model_field), r.get("condition"))][r["unit_id"]].append(1.0 if v else 0.0)
    return idx, clusters


def models_of(idx, pack):
    return sorted({m for (p, m, _c) in idx if p == pack})


# ---------------------------------------------------------------- part 1

def part1_rounds(idx):
    """Tasks counted by the number of rounds whose suggestion core_ok accepts, per cell and pooled by condition."""
    cells, pooled = [], defaultdict(Counter)
    disagree_at: dict = defaultdict(lambda: defaultdict(set))     # (pack, model) -> unit -> conditions
    conds_of: dict = defaultdict(set)
    for pack in PACKS:
        for model in models_of(idx, pack):
            for cond in CONDITIONS:
                cell = idx.get((pack, model, cond), {})
                if not cell:
                    continue
                conds_of[(pack, model)].add(cond)
                dist, split_tasks = Counter(), 0
                for u, vals in cell.items():
                    k, n = int(round(sum(vals))), len(vals)
                    dist[f"{k}/{n}"] += 1
                    if 0 < k < n:
                        split_tasks += 1
                        disagree_at[(pack, model)][u].add(cond)
                trials = sum(len(v) for v in cell.values())
                accepted = int(round(sum(sum(v) for v in cell.values())))
                cells.append({"pack": pack, "model": model, "condition": cond, "tasks": len(cell),
                              "trials": trials, "trial_share": accepted / trials,
                              "all_accept": dist.get(f"{max(len(v) for v in cell.values())}/"
                                                     f"{max(len(v) for v in cell.values())}", 0),
                              "none_accept": dist.get("0/" + str(max(len(v) for v in cell.values())), 0),
                              "split": split_tasks, "split_share": split_tasks / len(cell),
                              "distribution": dict(sorted(dist.items()))})
                pooled[cond].update(dist)
    always = []
    for (pack, model), units in sorted(disagree_at.items()):
        for u, cs in sorted(units.items()):
            if cs == conds_of[(pack, model)]:
                always.append({"pack": pack, "model": model, "unit": u, "conditions": len(cs)})
    pooled_rows = []
    for cond in CONDITIONS:
        d = pooled.get(cond)
        if not d:
            continue
        total = sum(d.values())
        split = sum(n for k, n in d.items() if 0 < int(k.split("/")[0]) < int(k.split("/")[1]))
        pooled_rows.append({"condition": cond, "tasks": total, "split": split, "split_share": split / total,
                            "distribution": dict(sorted(d.items()))})
    return {"cells": cells, "pooled": pooled_rows, "always_disagree": always}


# ---------------------------------------------------------------- part 2

def boot(units, deltas, cluster_of, b, seed):
    """The resampling of confirmatory.cluster_bootstrap_ci (whole source files, with replacement, same seed and
    number of resamples), returning its percentile interval, the standard deviation of the resample means (the
    bootstrap standard error) and the number of clusters."""
    groups: dict = defaultdict(list)
    for u, d in zip(units, deltas):
        groups[cluster_of(u)].append(d)
    keys = sorted(groups, key=str)
    sums = [sum(groups[k]) for k in keys]
    sizes = [len(groups[k]) for k in keys]
    rng = random.Random(seed)
    k = len(keys)
    means = []
    for _ in range(b):
        s = n = 0
        for _j in range(k):
            i = rng.randrange(k)
            s += sums[i]
            n += sizes[i]
        means.append(s / n)
    ms = sorted(means)
    lo, hi = ms[int(0.025 * b)], ms[min(b - 1, int(0.975 * b))]
    se = statistics.pstdev(means) if len(means) > 1 else float("nan")
    return lo, hi, se, k


def row_from(units, deltas, cluster_of, b, seed, margin):
    lo, hi, se, k = boot(units, deltas, cluster_of, b, seed)
    mdd = (Z_975 + Z_80) * se
    return {"units": len(units), "clusters": k, "mean_diff_pp": 100 * statistics.fmean(deltas),
            "ci_low_pp": 100 * lo, "ci_high_pp": 100 * hi, "half_width_pp": 100 * (hi - lo) / 2,
            "se_pp": 100 * se, "mdd80_pp": 100 * mdd, "margin_pp": 100 * margin,
            "mdd_above_margin": None if math.isnan(mdd) else mdd > margin}


def part2_h4_power(idx_h, idx_l, clusters, b, seed, margin, rules_sent):
    """For H4 (LLM-drafted ontology minus human, selection condition) the difference the design could detect."""
    rows, pooled_units, pooled_deltas = [], [], []
    for pack in PACKS:
        pack_units, pack_deltas = [], []
        for model in sorted(set(models_of(idx_h, pack)) & set(models_of(idx_l, pack))):
            u, d, _up, _dn, _t = C.paired(idx_l.get((pack, model, SELECTION), {}),
                                          idx_h.get((pack, model, SELECTION), {}))
            if not u:
                continue
            r = row_from(u, d, lambda x, p=pack: clusters.get((p, x), x), b, seed, margin)
            rows.append(dict(pack=pack, model=model, scope="cell", **r))
            pack_units += [(pack, model, x) for x in u]
            pack_deltas += d
        if pack_units:
            r = row_from(pack_units, pack_deltas, lambda x: clusters.get((x[0], x[2]), x[2]), b, seed, margin)
            rows.append(dict(pack=pack, model="all models", scope="standard", **r))
            pooled_units += pack_units
            pooled_deltas += pack_deltas
    if pooled_units:
        r = row_from(pooled_units, pooled_deltas, lambda x: (x[0], clusters.get((x[0], x[2]), x[2])), b, seed, margin)
        rows.append(dict(pack="all standards", model="all models", scope="pooled", **r))
    return {"margin_pp": 100 * margin, "rows": rows, "rules_sent": rules_sent,
            "note_packs_without_rules": sorted(p for p, v in rules_sent.items() if v == 0)}


def rules_sent_by_pack(llm_recs):
    """Mean number of rules the selection condition sent, per pack, in the runs with the LLM-drafted ontology.
    A pack for which it is 0 has no naming rule in its draft for the kind the benchmark injects."""
    per: dict = defaultdict(list)
    for r in llm_recs:
        if r.get("split") != SPLIT or r.get("condition") != SELECTION:
            continue
        n = ((r.get("retrieval") or {}).get("n_items"))
        if n is not None:
            per[r.get("pack")].append(n)
    return {p: statistics.fmean(v) for p, v in sorted(per.items())}


# ---------------------------------------------------------------- part 3

def part3_scope(curation, runs_dir):
    """The renames to fresh names of H6 that the scope-aware check flags, with the reason each check gives.
    The renames are those make_h6_labels.py builds; the check is the one of the curation folder."""
    if not os.path.isdir(curation):
        return {"available": False, "reason": f"curation folder not found: {curation}"}
    sys.path.insert(0, curation)
    try:
        from scope_check import check_rename
        from make_h6_labels import tasks as fresh_tasks
    except Exception as e:                                        # noqa: BLE001 - reported, not raised
        return {"available": False, "reason": f"{type(e).__name__}: {e}"}
    flagged, counts, skipped = [], Counter(), Counter()
    for pack, split, uid, lang, original, injected, code in fresh_tasks(runs_dir):
        res = check_rename(lang, code, injected, original)
        if res["status"] in ("unsupported", "no_occurrence"):
            skipped[f"{pack}:{res['status']}"] += 1
            continue
        counts[f"{pack}:all"] += 1
        aware = bool(res["binding_conflict"] or res["declaration_conflict"])
        blind = bool(res["scope_blind"])
        if aware:
            counts[f"{pack}:aware"] += 1
        if blind:
            counts[f"{pack}:blind"] += 1
        if aware or blind:
            flagged.append({"pack": pack, "split": split, "unit": uid, "language": lang, "kind_from_unit": uid.split("__")[-1],
                            "from": injected, "to": original, "aware": aware, "blind": blind,
                            "binding_reasons": res["binding_reasons"], "declaration_reasons": res["declaration_reasons"],
                            "occurrences_renamed": res["occurrences_renamed"]})
    return {"available": True, "flagged": sorted(flagged, key=lambda r: (r["pack"], r["unit"])),
            "counts": dict(sorted(counts.items())), "no_verdict": dict(sorted(skipped.items()))}


# ---------------------------------------------------------------- part 4

def context_of(prompt):
    """The text of the CODING STANDARD block of a prompt built by athena.prompts.build_prompt."""
    i = (prompt or "").find("CODING STANDARD")
    j = (prompt or "").find("\nCODE\n", i)
    if i < 0 or j < 0:
        return None
    return prompt[i + len("CODING STANDARD"):j].strip("\n")


def guess_format(text):
    import re
    md = len(re.findall(r"(?m)^#{1,6} \S", text))
    rst = len(re.findall(r"(?m)^[=\-~^\"'`:.*+#<>]{3,}\s*$", text))
    return "md" if md > rst else "rst"


def passage_map(recs, pack):
    """pid -> first line of the passage, from the document the fulldoc condition of this pack sent."""
    for r in recs:
        if r.get("pack") != pack or r.get("condition") != "fulldoc" or r.get("split") != SPLIT:
            continue
        c = context_of(r.get("prompt"))
        if not c:
            continue
        body = c.split("\n", 1)
        text = body[1] if len(body) == 2 else c
        return {pid: (b.split("\n\n", 1)[0] if "\n\n" in b else b.split("\n", 1)[0])
                for pid, b in split_passages(text, guess_format(text))}
    return {}


def part4_read(recs):
    """Two cells read by hand: the drafting model on READ_PACK_A in the selection condition, and the dense
    condition on READ_PACK_B.  Both take the first READ_N by unit identifier whose suggestion core_ok rejects."""
    rejected = defaultdict(list)
    by_key = {}
    for r in recs:
        if r.get("task", "rename") != "rename" or r.get("split") != SPLIT:
            continue
        m = r.get("metrics") or {}
        by_key[(r.get("pack"), r.get("backend"), r.get("condition"), r["unit_id"], r.get("repeat"))] = r
        if m.get("core_ok") is False:
            rejected[(r.get("pack"), r.get("condition"))].append(r)

    # a) the drafting model on READ_PACK_A: parameter names that lack the p_ or r_ prefix (the measure of A8)
    a_rows = []
    params = [r for r in recs
              if r.get("task", "rename") == "rename" and r.get("split") == SPLIT
              and r.get("pack") == READ_PACK_A and r.get("condition") == READ_COND_A
              and DRAFTING_MODEL in str(r.get("backend", "")).lower()
              and r.get("kind") == "parameter" and not r.get("error")
              and (r.get("metrics") or {}).get("suggested")]
    pool = [r for r in params if not str(r["metrics"].get("suggested")).startswith(PREFIXES)]
    for r in sorted(pool, key=lambda r: (r["unit_id"], r.get("repeat", 0)))[:READ_N]:
        m = r.get("metrics") or {}
        sel = by_key.get((READ_PACK_A, r.get("backend"), SELECTION, r["unit_id"], r.get("repeat")))
        sm = (sel or {}).get("metrics") or {}
        s_sug = sm.get("suggested")
        a_rows.append({"unit": r["unit_id"], "model": r.get("backend"), "repeat": r.get("repeat"),
                       "kind": r.get("kind"), "rule": r.get("rule_id"), "original": r.get("original"),
                       "injected": r.get("injected"), "suggested": m.get("suggested"),
                       "core_ok": m.get("core_ok"), "selection_suggested": s_sug if sel else None,
                       "selection_prefix": None if not s_sug else str(s_sug).startswith(PREFIXES),
                       "selection_core_ok": sm.get("core_ok")})

    # b) the dense condition on READ_PACK_B: the first READ_N units, with what dense and selection sent
    heads = passage_map(recs, READ_PACK_B)
    b_rows, seen = [], set()
    for r in sorted(rejected.get((READ_PACK_B, DENSE), []), key=lambda r: (r["unit_id"], str(r.get("backend")),
                                                                          r.get("repeat", 0))):
        if r["unit_id"] in seen:
            continue
        seen.add(r["unit_id"])
        m = r.get("metrics") or {}
        ret = r.get("retrieval") or {}
        ids = ret.get("retrieved_ids") or []
        sel = by_key.get((READ_PACK_B, r.get("backend"), SELECTION, r["unit_id"], r.get("repeat")))
        b_rows.append({"unit": r["unit_id"], "model": r.get("backend"), "repeat": r.get("repeat"),
                       "kind": r.get("kind"), "rule": r.get("rule_id"), "injected": r.get("injected"),
                       "suggested": m.get("suggested"), "retrieved_n": ret.get("n_items"),
                       "retrieved": [{"id": i, "heading": cut(heads.get(i, "(not in the document split)"), 120)}
                                     for i in ids],
                       "dense_context": cut(context_of(r.get("prompt")) or ""),
                       "selection_context": cut(context_of(sel.get("prompt")) if sel else "") or "(no paired trial)",
                       "selection_core_ok": ((sel or {}).get("metrics") or {}).get("core_ok")})
        if len(b_rows) >= READ_N:
            break
    return {"cell_a": {"pack": READ_PACK_A, "condition": READ_COND_A, "model_token": DRAFTING_MODEL,
                       "parameter_trials": len(params), "available": len(pool), "rows": a_rows},
            "cell_b": {"pack": READ_PACK_B, "condition": DENSE,
                       "available": len(rejected.get((READ_PACK_B, DENSE), [])), "rows": b_rows}}


# ---------------------------------------------------------------- report

def render(res):
    L = ["# A12. Round-to-round disagreement, the difference H4 could detect, the flags of the scope-aware check, "
         "and two cells read by hand", "",
         "Exploratory. No decision rule, no new model call, no change to the main tables.", ""]

    p1 = res["part1"]
    L += ["## 1. The three rounds of a task", "",
          "`k/n` is the number of rounds whose suggestion `core_ok` accepts over the rounds the task has. "
          "A task is split when the rounds do not agree.", "",
          table(["pack", "model", "condition", "tasks", "trials", "trials %", "all accept", "none accept",
                 "split", "split %", "distribution"],
                [[r["pack"], r["model"], r["condition"], r["tasks"], r["trials"], pct(r["trial_share"]),
                  r["all_accept"], r["none_accept"], r["split"], pct(r["split_share"]),
                  ", ".join(f"{k}: {v}" for k, v in r["distribution"].items())] for r in p1["cells"]]), "",
          "Pooled over the cells of a condition:", "",
          table(["condition", "tasks", "split", "split %", "distribution"],
                [[r["condition"], r["tasks"], r["split"], pct(r["split_share"]),
                  ", ".join(f"{k}: {v}" for k, v in r["distribution"].items())] for r in p1["pooled"]]), ""]
    if p1["always_disagree"]:
        L += ["Units whose rounds disagree in every condition of a model:", "",
              table(["pack", "model", "unit", "conditions"],
                    [[r["pack"], r["model"], r["unit"], r["conditions"]] for r in p1["always_disagree"]]), ""]
    else:
        L += ["No unit has rounds that disagree in every condition of a model.", ""]

    p2 = res["part2"]
    L += [f"## 2. The difference H4 could detect, against its margin of {p2['margin_pp']:.0f} pp", "",
          "The standard error is the standard deviation of the resample means of the cluster bootstrap over "
          "source files, with the seed and the number of resamples of that analysis. The detectable difference "
          "is the two-sided 5% level at 80% power.", "",
          table(["pack", "model", "scope", "units", "files", "difference pp", "95% CI pp", "half-width pp",
                 "SE pp", "detectable at 80% power pp", "above the margin"],
                [[r["pack"], r["model"], r["scope"], r["units"], r["clusters"], f"{r['mean_diff_pp']:+.2f}",
                  f"[{r['ci_low_pp']:+.2f}, {r['ci_high_pp']:+.2f}]", num(r["half_width_pp"], 2),
                  num(r["se_pp"], 2), num(r["mdd80_pp"], 2),
                  "yes" if r["mdd_above_margin"] else ("n/a" if r["mdd_above_margin"] is None else "no")]
                 for r in p2["rows"]]), "",
          "Rules the selection condition sent with the LLM-drafted ontology, on average per trial: " +
          ", ".join(f"{p}: {num(v, 2)}" for p, v in p2["rules_sent"].items()) + ".", ""]
    if p2["note_packs_without_rules"]:
        L += ["Reported apart, because the draft holds no naming rule for the kind the benchmark injects, so the "
              "quantity measures coverage and not a difference: " + ", ".join(p2["note_packs_without_rules"]) + ".", ""]

    p3 = res["part3"]
    L += ["## 3. The renames to fresh names that a check flags", ""]
    if not p3["available"]:
        L += [f"Not computed: {p3['reason']}", ""]
    else:
        L += ["Counts: " + ", ".join(f"{k}: {v}" for k, v in p3["counts"].items()) + ".",
              "No verdict (the snippet does not parse, or the injected name is not in it): " +
              (", ".join(f"{k}: {v}" for k, v in p3["no_verdict"].items()) or "none") + ".", ""]
        if p3["flagged"]:
            L += [table(["pack", "split", "unit", "language", "from", "to", "scope-aware", "scope-blind",
                         "binding reasons", "declaration reasons", "occurrences"],
                        [[r["pack"], r["split"], r["unit"], r["language"], r["from"], r["to"],
                          "yes" if r["aware"] else "no", "yes" if r["blind"] else "no",
                          "; ".join(r["binding_reasons"]) or "-", "; ".join(r["declaration_reasons"]) or "-",
                          r["occurrences_renamed"]] for r in p3["flagged"]]), ""]
        else:
            L += ["No rename to a fresh name is flagged by either check.", ""]

    p4 = res["part4"]
    a, b = p4["cell_a"], p4["cell_b"]
    L += ["## 4. Two cells read by hand", "",
          f"### {a['pack']}, {a['condition']} condition, the drafting model: parameter names without the "
          f"p_ or r_ prefix ({a['available']} of {a['parameter_trials']} parameter trials, the first "
          f"{len(a['rows'])} by unit shown)", "",
          "The prefix rule lies outside the core rules, so `core_ok` can accept a name this reading rejects; "
          "addendum A8 counts such names.", "",
          table(["unit", "round", "original", "injected", "suggested", "core_ok", "selection suggestion",
                 "selection has the prefix", "selection core_ok"],
                [[r["unit"], r["repeat"], r["original"], r["injected"], r["suggested"], r["core_ok"],
                  r["selection_suggested"] or "(no paired trial)",
                  "n/a" if r["selection_prefix"] is None else ("yes" if r["selection_prefix"] else "no"),
                  r["selection_core_ok"]] for r in a["rows"]]), ""]
    L += [f"### {b['pack']}, {b['condition']} condition "
          f"({b['available']} rejected trials, the first {len(b['rows'])} units shown)", ""]
    for r in b["rows"]:
        L += [f"**{r['unit']}** ({r['model']}, round {r['repeat']}, kind {r['kind']}, rule {r['rule']}): "
              f"`{r['injected']}` to `{r['suggested']}`; {r['retrieved_n']} passages retrieved.",
              "", "Retrieved: " + ("; ".join(f"`{p['id']}` {p['heading']}" for p in r["retrieved"]) or "none"), "",
              f"Dense context: {r['dense_context']}", "",
              f"Selection context for the same unit (core_ok {r['selection_core_ok']}): {r['selection_context']}", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--meta", nargs="+", required=True)
    ap.add_argument("--llm", nargs="+", required=True)
    base = os.environ.get("ATHENA_CORPUS") or os.path.join(HERE, "..", "athena-corpus")
    ap.add_argument("--curation", default=os.path.join(base, "curation"))
    ap.add_argument("--runs", default=os.path.join(HERE, "runs"))
    ap.add_argument("--model-field", default="backend")
    ap.add_argument("--cluster-field", default="file")
    ap.add_argument("--resamples", type=int, default=C.BOOT_B)
    ap.add_argument("--seed", type=int, default=C.BOOT_SEED)
    ap.add_argument("--margin", type=float, default=H4_MARGIN)
    ap.add_argument("--skip-scope", action="store_true", help="leave part 3 out (it needs the curation folder)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    meta_dirs, llm_dirs = expand(a.meta), expand(a.llm)
    for dirs in (meta_dirs, llm_dirs):
        missing = [d for d in dirs if not os.path.exists(os.path.join(d, "trials.jsonl"))]
        if missing:
            sys.exit("no trials.jsonl in: " + ", ".join(missing))
    recs, _e1 = load_trials(meta_dirs)
    llm_recs, _e2 = load_trials(llm_dirs)
    idx_h, clusters = index_cells(recs, a.model_field, a.cluster_field)
    idx_l, clusters_l = index_cells(llm_recs, a.model_field, a.cluster_field)
    clusters = {**clusters_l, **clusters}

    res = {"part1": part1_rounds(idx_h),
           "part2": part2_h4_power(idx_h, idx_l, clusters, a.resamples, a.seed, a.margin,
                                   rules_sent_by_pack(llm_recs)),
           "part3": ({"available": False, "reason": "left out with --skip-scope"} if a.skip_scope
                     else part3_scope(os.path.abspath(a.curation), a.runs)),
           "part4": part4_read(recs),
           "settings": {"resamples": a.resamples, "seed": a.seed, "margin_pp": 100 * a.margin,
                        "meta_runs": meta_dirs, "llm_runs": llm_dirs, "python": sys.version.split()[0]}}
    text = render(res)
    print(text)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text + "\n")
    if a.json:
        json.dump(res, open(a.json, "w", encoding="utf-8"), indent=1, default=str)


if __name__ == "__main__":
    main()
