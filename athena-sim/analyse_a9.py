#!/usr/bin/env python3
"""analyse_a9 - the descriptive analyses of addendum A9 (exploratory; no decision rule, no new model call).

  python analyse_a9.py --meta runs/test_*_meta [--llm runs/test_*_llm] [--packs-dir packs] [--labels renames_all.csv]
                       [--out a9.md] [--json a9.json]

  --meta      test runs with the human ontology and the kind from metadata (H3 and H2 are read from these)
  --llm       test runs with the LLM-drafted ontology (the rules held by the draft are read from these)
  --packs-dir folder with packs/<pack>/ (ontologies and core_rules.json; default: packs next to this script)
  --labels    renames_all.csv of make_h6_labels.py (columns set, pack, language, id, breaks, aware, blind)

Parts: 1 H3 per cell (tasks higher, lower, equal; source files; exact upper limits when no task is lower);
2 H2 as the share of the room left by none that selection closes; 3 relations in the ontologies and rules selected
per test task; 4 coverage by identifier kind; 5 confusion matrices of H6.
A task is a unit_id; its score is the mean of core_ok over the repeats. Standard library only.
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

ALPHA = 0.05
PACKS = C.DEFAULT_PACKS
SPLIT = "test"


def cp_upper(k: int, n: int, alpha: float = ALPHA) -> float:
    """One-sided upper confidence limit (level 1 - alpha) of a binomial proportion with k events in n."""
    if n <= 0:
        return float("nan")
    if k >= n:
        return 1.0

    def cdf(p):                         # P(X <= k) for X ~ Binomial(n, p); decreasing in p
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))

    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if cdf(mid) > alpha:
            lo = mid
        else:
            hi = mid
    return hi


def expand(patterns):
    out = []
    for p in patterns or []:
        hit = sorted(glob.glob(p))
        out.extend(hit if hit else [p])
    return out


def pct(x, nd=1):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.{nd}f}"


def part1_h3(idx, clusters, sel, ref):
    rows = []
    for pack in PACKS:
        for model in C.models_of(idx, pack, SPLIT):
            a, b = C._cell(idx, pack, model, sel, SPLIT), C._cell(idx, pack, model, ref, SPLIT)
            units, deltas, up, down, tie = C.paired(a, b)
            if not units:
                continue
            fl = {u: clusters.get((pack, u), u) for u in units}
            files = set(fl.values())
            f_diff = {fl[u] for u, d in zip(units, deltas) if d != 0}
            f_down = {fl[u] for u, d in zip(units, deltas) if d < 0}
            rows.append({
                "pack": pack, "model": model, "tasks": len(units), "files": len(files),
                "higher": up, "lower": down, "equal": tie, "files_with_difference": len(f_diff),
                "mean_diff_pp": 100 * statistics.fmean(deltas),
                "upper_lower_share_tasks": cp_upper(down, len(units)),
                "upper_lower_share_files": cp_upper(len(f_down), len(files)),
            })
    return rows


def part2_h2(idx, sel, none_cond):
    rows = []
    for pack in PACKS:
        for model in C.models_of(idx, pack, SPLIT):
            a, b = C._cell(idx, pack, model, sel, SPLIT), C._cell(idx, pack, model, none_cond, SPLIT)
            units, deltas, *_ = C.paired(a, b)
            if not units:
                continue
            mb = C.unit_means(b)
            base = statistics.fmean(mb[u] for u in units)
            gain = statistics.fmean(deltas)
            room = 1 - base
            rows.append({"pack": pack, "model": model, "none": base, "room": room, "gain": gain,
                         "closed": (gain / room) if room > 1e-12 else None})
    return rows


def part3_relations(packs_dir):
    out = []
    for pack in PACKS:
        files = sorted(glob.glob(os.path.join(packs_dir, pack, "*ontology*.json")))
        files += sorted(glob.glob(os.path.join(packs_dir, pack, "llm", "llm_ontology.json")))
        for f in files:
            d = json.load(open(f, encoding="utf-8"))
            rel = Counter(e.get("relation") or e.get("key") or e.get("type") for e in d.get("links", []))
            nodes = Counter(n.get("type") for n in d.get("nodes", []))
            out.append({"pack": pack, "file": os.path.relpath(f, packs_dir), "relations": dict(rel), "nodes": dict(nodes),
                        "n_overrides_or_conflicts": sum(v for k, v in rel.items()
                                                        if k and ("OVERRID" in str(k).upper() or "CONFLICT" in str(k).upper()))})
    return out


def selected_per_task(recs, sel):
    """unit -> number of rules put in the prompt by selection (taken over all models; a difference is flagged)."""
    seen = defaultdict(set)
    info = {}
    for r in recs:
        if r.get("split") != SPLIT or r.get("condition") != sel or r.get("task", "rename") != "rename":
            continue
        n = (r.get("retrieval") or {}).get("n_items")
        key = (r.get("pack"), r["unit_id"])
        seen[key].add(n)
        info[key] = (r.get("kind"), r.get("language"), r.get("rule_id"))
    return seen, info


def part3b_rules_per_task(recs_by_variant, sel):
    rows = []
    for variant, recs in recs_by_variant.items():
        seen, _ = selected_per_task(recs, sel)
        for pack in PACKS:
            ns = [min(v) for (p, _), v in seen.items() if p == pack and None not in v]
            varying = sum(1 for (p, _), v in seen.items() if p == pack and len(v) > 1)
            if not ns:
                continue
            rows.append({"variant": variant, "pack": pack, "tasks": len(ns), "min": min(ns),
                         "median": statistics.median(ns), "max": max(ns), "no_rule": sum(1 for n in ns if n == 0),
                         "differs_between_models": varying})
    return rows


def core_set(packs_dir, pack):
    d = json.load(open(os.path.join(packs_dir, pack, "core_rules.json"), encoding="utf-8"))
    return {rid for kinds in d.get("core", {}).values() for ids in kinds.values() for rid in ids}


def part4_coverage(recs_by_variant, packs_dir, sel):
    meta = recs_by_variant["human"]
    llm = recs_by_variant.get("draft")
    seen_h, info = selected_per_task(meta, sel)
    seen_d = selected_per_task(llm, sel)[0] if llm else {}
    rows = []
    for pack in PACKS:
        core = core_set(packs_dir, pack)
        agg = defaultdict(lambda: {"tasks": 0, "core_checked": 0, "human_rule": 0, "draft_rule": 0, "draft_known": 0})
        for (p, u), (kind, lang, rid) in info.items():
            if p != pack:
                continue
            a = agg[(lang, kind)]
            a["tasks"] += 1
            a["core_checked"] += 1 if rid in core else 0
            nh = min(x for x in seen_h[(p, u)] if x is not None) if any(x is not None for x in seen_h[(p, u)]) else None
            a["human_rule"] += 1 if (nh or 0) > 0 else 0
            if (p, u) in seen_d and any(x is not None for x in seen_d[(p, u)]):
                a["draft_known"] += 1
                a["draft_rule"] += 1 if min(x for x in seen_d[(p, u)] if x is not None) > 0 else 0
        for (lang, kind), a in sorted(agg.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
            rows.append({"pack": pack, "language": lang, "kind": kind, **a})
    return rows


def part5_h6(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    cm = defaultdict(lambda: Counter())
    for r in rows:
        for who in ("aware", "blind"):
            br, fl = r["breaks"] in ("1", "True", "true"), r[who] in ("1", "True", "true")
            cell = "TP" if br and fl else "FN" if br else "FP" if fl else "TN"
            for grp in (("all", "all", who), (r.get("set"), r.get("language"), who)):
                cm[grp][cell] += 1
    return [{"set": s, "language": l, "check": w, **dict(c)} for (s, l, w), c in sorted(cm.items(), key=lambda kv: tuple(map(str, kv[0])))]


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def render(res):
    L = ["# Addendum A9 - descriptive analyses (exploratory)", ""]
    L += ["## 1. H3 per cell (selection against fulldoc, test part)", "",
          "Higher/lower/equal: tasks (mean of core_ok over the repeats). Upper limits: exact one-sided 95% upper limit of the share of "
          "tasks (or source files) on which selection scores lower; over files it is the larger and is valid under clustering.", "",
          table(["pack", "model", "tasks", "files", "higher", "lower", "equal", "files with difference", "mean diff pp",
                 "upper limit, tasks %", "upper limit, files %"],
                [[r["pack"], r["model"], r["tasks"], r["files"], r["higher"], r["lower"], r["equal"], r["files_with_difference"],
                  f"{r['mean_diff_pp']:+.1f}", pct(r["upper_lower_share_tasks"]), pct(r["upper_lower_share_files"])] for r in res["h3"]]), ""]
    L += ["## 2. H2 as room closed (test part)", "",
          table(["pack", "model", "none %", "room pp", "gain pp", "share of room closed %"],
                [[r["pack"], r["model"], pct(r["none"]), pct(r["room"]), f"{100 * r['gain']:+.1f}", pct(r["closed"])] for r in res["h2"]]), ""]
    L += ["## 3. Relations in the ontologies and rules selected per task", "",
          table(["pack", "file", "relations", "node types", "overrides or conflicts"],
                [[r["pack"], r["file"], r["relations"], r["nodes"], r["n_overrides_or_conflicts"]] for r in res["relations"]]), "",
          table(["variant", "pack", "tasks", "min", "median", "max", "tasks with no rule", "tasks where models differ"],
                [[r["variant"], r["pack"], r["tasks"], r["min"], r["median"], r["max"], r["no_rule"], r["differs_between_models"]]
                 for r in res["per_task"]]), ""]
    L += ["## 4. Coverage by identifier kind (test tasks)", "",
          table(["pack", "language", "kind", "tasks", "kind checked by core rule", "human ontology holds a rule", "draft holds a rule", "tasks seen in draft runs"],
                [[r["pack"], r["language"], r["kind"], r["tasks"], r["core_checked"], r["human_rule"], r["draft_rule"], r["draft_known"]]
                 for r in res["coverage"]]), ""]
    if res.get("h6"):
        L += ["## 5. H6 confusion matrices", "",
              table(["set", "language", "check", "TP", "FN", "FP", "TN"],
                    [[r["set"], r["language"], r["check"], r.get("TP", 0), r.get("FN", 0), r.get("FP", 0), r.get("TN", 0)] for r in res["h6"]]), ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--meta", nargs="+", required=True)
    ap.add_argument("--llm", nargs="+", default=None)
    ap.add_argument("--packs-dir", default=os.path.join(HERE, "packs"))
    ap.add_argument("--labels", default=None)
    ap.add_argument("--selection", default="graph")
    ap.add_argument("--none", default="none", dest="none_cond")
    ap.add_argument("--reference", default="fulldoc")
    ap.add_argument("--model-field", default="backend")
    ap.add_argument("--cluster-field", default="file")
    ap.add_argument("--out", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    meta_dirs = expand(a.meta)
    missing = [d for d in meta_dirs if not os.path.exists(os.path.join(d, "trials.jsonl"))]
    if missing:
        sys.exit("no trials.jsonl in: " + ", ".join(missing))
    recs_h, _ = load_trials(meta_dirs)
    by_variant = {"human": recs_h}
    if a.llm:
        llm_dirs = expand(a.llm)
        recs_d, _ = load_trials(llm_dirs)
        by_variant["draft"] = recs_d
    idx, clusters = C.build_index(recs_h, a.model_field, a.cluster_field)
    res = {
        "h3": part1_h3(idx, clusters, a.selection, a.reference),
        "h2": part2_h2(idx, a.selection, a.none_cond),
        "relations": part3_relations(a.packs_dir),
        "per_task": part3b_rules_per_task(by_variant, a.selection),
        "coverage": part4_coverage(by_variant, a.packs_dir, a.selection),
    }
    if a.labels:
        res["h6"] = part5_h6(a.labels)
    text = render(res)
    print(text)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text + "\n")
    if a.json:
        json.dump(res, open(a.json, "w", encoding="utf-8"), indent=1, default=str)


if __name__ == "__main__":
    main()
