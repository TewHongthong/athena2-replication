#!/usr/bin/env python3
"""analyse_a14 - the analysis of addendum A14 (exploratory; no decision rule, no new model call).

  python analyse_a14.py --check [--sources SHEET] [--root DIR]
  python analyse_a14.py --meta runs/test_*_meta [--sources SHEET] [--root DIR] [--out a14.md] [--json a14.json]

  --sources  the sheet of rule labels (default ../analysis/a14_rule_sources.csv)
  --root     the folder that the document paths of the sheet are relative to (default ..); the pinned documents
             are under standards/src, which fetch_standards.py rebuilds
  --meta     test runs with the human ontology and the kind from metadata (the cells of Table VI)
  --check    validate the sheet and stop; nothing is read from the trials

The sheet holds one row for each naming rule of the three human ontologies. Its label is stated (the pinned
document names the kind of identifier and the requirement), covered (a general statement of the document
includes the kind without naming it), or inferred (the document states neither). A rule labelled stated or
covered carries the words of the document in its quote; several passages are separated by " | ". Each passage is
looked up in the pinned document after runs of white space are joined, and again after backticks and asterisks
are removed from both.

Every kind of identifier in the test tasks has one core rule, so no trial is scored again: a task is kept when
the label of its core rule (the rule_id of its trials) is in a set, and dropped otherwise. Two sets are used,
stated alone and stated or covered; all tasks are shown next to them for reference.

Parts: 1 the rules and the test tasks of each label; 2 compliance for every model, standard and condition on the
kept tasks (the mean of the task means, with the cluster bootstrap over source files of the main tables); 3
selection against no standard and against the full document on the kept tasks (mean paired difference, its
cluster-bootstrap interval, and the wins, ties and losses of the paired tasks), with the outcome that the
non-inferiority rule of H3 would give on those tasks. A task is a unit_id; its score is the mean of core_ok over
its repeats. Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import math
import os
import re
import statistics
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from athena import confirmatory as C  # noqa: E402
from athena.report import load_trials  # noqa: E402

PACKS = C.DEFAULT_PACKS
SPLIT = "test"
CONDITIONS = ("none", "fulldoc", "chunk", "bm25", "dense", "graph")
SELECTION, NONE, FULLDOC = "graph", "none", "fulldoc"
LABELS = ("stated", "covered", "inferred")
NEEDS_QUOTE = ("stated", "covered")
SETS = (("all tasks", None), ("stated", ("stated",)), ("stated or covered", ("stated", "covered")))
COLUMNS = ("standard", "rule_id", "applies_to", "requirement", "severity", "description", "core", "test_tasks",
           "source_document", "label", "quote", "note")
DEFAULT_SOURCES = os.path.normpath(os.path.join(HERE, "..", "analysis", "a14_rule_sources.csv"))
DEFAULT_ROOT = os.path.normpath(os.path.join(HERE, ".."))
ONTOLOGIES = {"godot": "packs/godot/godot_ontology.json",
              "dotnet-runtime": "packs/dotnet-runtime/dotnet_ontology.json",
              "odoo": "packs/odoo/odoo_ontology.json"}


def expand(patterns):
    out = []
    for p in patterns or []:
        hit = sorted(glob.glob(p))
        out.extend(hit if hit else [p])
    return out


def pct(x, nd=1):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.{nd}f}"


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


# ---------------------------------------------------------------- the sheet

def read_sheet(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        header = tuple((h or "").strip() for h in (rd.fieldnames or []))
        rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items() if k is not None} for r in rd]
    for r in rows:
        r["label"] = r.get("label", "").lower()
    return header, rows


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def ontology_rules():
    out = {}
    for pack, rel in ONTOLOGIES.items():
        with open(os.path.join(HERE, rel), encoding="utf-8") as f:
            d = json.load(f)
        out[pack] = {n["id"] for n in d["nodes"] if n.get("type") == "NamingRule"}
    return out


def doc_path(source_document):
    m = re.match(r"(.+?)\s*\(section:", source_document)
    return (m.group(1) if m else source_document).strip()


def _ws(s):
    return re.sub(r"\s+", " ", s).strip()


def _plain(s):
    return _ws(re.sub(r"[`*]", "", s))


def find_quote(quote, text):
    """Each passage of the quote: 'found', 'found without markup', or 'not found'."""
    parts = [p.strip() for p in re.split(r"\s+\|\s+", quote) if p.strip()]
    ws_text, plain_text = _ws(text), _plain(text)
    res = []
    for p in parts:
        if _ws(p) in ws_text:
            res.append("found")
        elif _plain(p) in plain_text:
            res.append("found without markup")
        else:
            res.append("not found")
    return res


def validate(header, rows, root):
    """Return (errors, checks). An error stops the analysis; a check records how each quote was found."""
    errors, checks = [], []
    missing = [c for c in COLUMNS if c not in header]
    if missing:
        return ["columns missing from the sheet: " + ", ".join(missing)], checks
    dup = sorted(k for k, v in Counter(r["rule_id"] for r in rows).items() if v > 1)
    if dup:
        errors.append("rule_id repeated: " + ", ".join(dup))
    for pack, rules in ontology_rules().items():
        have = {r["rule_id"] for r in rows if r["standard"] == pack}
        if have != rules:
            errors.append(f"{pack}: the sheet and the ontology differ (missing from the sheet: "
                          f"{', '.join(sorted(rules - have)) or 'none'}; not in the ontology: "
                          f"{', '.join(sorted(have - rules)) or 'none'})")
    docs = {}
    for r in rows:
        rid, lab = r["rule_id"], r["label"]
        if lab not in LABELS:
            errors.append(f"{rid}: label '{r['label']}' is not one of {', '.join(LABELS)}")
            continue
        if lab in NEEDS_QUOTE and not r["quote"]:
            errors.append(f"{rid}: the label {lab} needs a quote")
            continue
        row = {"standard": r["standard"], "rule_id": rid, "label": lab, "passages": 0, "result": "no quote"}
        if r["quote"]:
            path = doc_path(r["source_document"])
            full = os.path.join(root, path)
            if not os.path.exists(full):
                row["result"] = "not checked (document absent)"
            else:
                if full not in docs:
                    with open(full, encoding="utf-8") as f:
                        docs[full] = f.read()
                found = find_quote(r["quote"], docs[full])
                row["passages"] = len(found)
                if "not found" in found:
                    row["result"] = "not found"
                    bad = [str(i + 1) for i, x in enumerate(found) if x == "not found"]
                    errors.append(f"{rid}: passage {', '.join(bad)} of the quote not found in {path}")
                elif "found without markup" in found:
                    row["result"] = "found without markup"
                else:
                    row["result"] = "found"
        checks.append(row)
    return errors, checks


# ---------------------------------------------------------------- the trials

def index_tasks(recs, model_field="backend", cluster_field="file"):
    """idx[(pack, model, condition)][unit] = [core_ok per repeat]; rule_of[(pack, unit)] = rule_id of its trials."""
    idx: dict = defaultdict(lambda: defaultdict(list))
    clusters, rule_of, conflicts = {}, {}, set()
    for r in recs:
        if r.get("task", "rename") != "rename" or r.get("split") != SPLIT or r.get("pack") not in PACKS:
            continue
        key = (r.get("pack"), r["unit_id"])
        rid = r.get("rule_id")
        if key in rule_of and rule_of[key] != rid:
            conflicts.add(key)
        rule_of.setdefault(key, rid)
        v = (r.get("metrics") or {}).get("core_ok")
        if v is None:
            continue
        clusters[key] = r.get(cluster_field) or r.get("snippet_id") or r["unit_id"]
        idx[(r.get("pack"), r.get(model_field), r.get("condition"))][r["unit_id"]].append(1.0 if v else 0.0)
    return idx, clusters, rule_of, conflicts


def models_of(idx, pack):
    return sorted({m for (p, m, _c) in idx if p == pack and m is not None})


def kept_units(rule_of, label_of, pack, labels):
    if labels is None:
        return None
    return {u for (p, u), rid in rule_of.items() if p == pack and label_of.get(rid) in labels}


def ci(units, vals, clusters, pack, b, seed):
    """The cluster bootstrap of the main tables; when every value is equal the interval is that value."""
    if min(vals) == max(vals):
        return vals[0], vals[0]
    return C.cluster_bootstrap_ci(units, vals, clusters, pack, b, seed)


def part1_counts(rows, rule_of):
    label_of = {r["rule_id"]: r["label"] for r in rows}
    out = []
    for pack in PACKS:
        for lab in LABELS:
            out.append({"pack": pack, "label": lab,
                        "core_rules": sum(1 for r in rows if r["standard"] == pack and r["label"] == lab
                                          and r["core"] == "core"),
                        "excluded_rules": sum(1 for r in rows if r["standard"] == pack and r["label"] == lab
                                              and r["core"] == "excluded"),
                        "test_tasks": sum(1 for (p, _u), rid in rule_of.items()
                                          if p == pack and label_of.get(rid) == lab)})
    used = Counter((p, rid) for (p, _u), rid in rule_of.items())
    by_rule = [{"pack": p, "rule_id": rid, "label": label_of.get(rid, "missing"), "test_tasks": n}
               for (p, rid), n in sorted(used.items(), key=lambda x: (PACKS.index(x[0][0]), -x[1], x[0][1]))]
    return {"by_label": out, "rules_of_test_tasks": by_rule,
            "rules_without_test_tasks": sum(1 for r in rows if (r["standard"], r["rule_id"]) not in used)}


def part2_compliance(idx, clusters, rule_of, label_of, b, seed):
    rows = []
    for set_name, labels in SETS:
        for pack in PACKS:
            keep = kept_units(rule_of, label_of, pack, labels)
            for model in models_of(idx, pack):
                for cond in CONDITIONS:
                    cell = idx.get((pack, model, cond), {})
                    units = sorted(u for u in cell if keep is None or u in keep)
                    row = {"set": set_name, "pack": pack, "model": model, "condition": cond, "tasks": len(units)}
                    if units:
                        vals = [sum(cell[u]) / len(cell[u]) for u in units]
                        lo, hi = ci(units, vals, clusters, pack, b, seed)
                        row.update(files=len({clusters.get((pack, u), u) for u in units}),
                                   trials=sum(len(cell[u]) for u in units), task_mean=statistics.fmean(vals),
                                   file_low=lo, file_high=hi)
                    rows.append(row)
    return rows


def part3_paired(idx, clusters, rule_of, label_of, b, seed, margin=C.NI_MARGIN):
    rows = []
    for set_name, labels in SETS:
        for pack in PACKS:
            keep = kept_units(rule_of, label_of, pack, labels)
            for model in models_of(idx, pack):
                for ref in (NONE, FULLDOC):
                    sel = {u: v for u, v in idx.get((pack, model, SELECTION), {}).items() if keep is None or u in keep}
                    oth = {u: v for u, v in idx.get((pack, model, ref), {}).items() if keep is None or u in keep}
                    units, deltas, up, dn, tie = C.paired(sel, oth)
                    row = {"set": set_name, "pack": pack, "model": model, "reference": ref, "tasks": len(units)}
                    if units:
                        lo, hi = ci(units, deltas, clusters, pack, b, seed)
                        row.update(files=len({clusters.get((pack, u), u) for u in units}),
                                   mean_diff_pp=100 * statistics.fmean(deltas), ci_low_pp=100 * lo,
                                   ci_high_pp=100 * hi, wins=up, ties=tie, losses=dn,
                                   identical=(up == 0 and dn == 0))
                        if ref == FULLDOC:
                            row["h3_rule"] = ("non-inferior" if lo > -margin
                                              else ("inferior" if hi < -margin else "inconclusive"))
                    rows.append(row)
    return rows


# ---------------------------------------------------------------- output

def render_check(path, sha, rows, errors, checks):
    L = [f"Sheet: {path}", f"sha256: {sha}", f"Rules: {len(rows)}", ""]
    cnt = Counter((r["standard"], r["label"] or "(empty)") for r in rows)
    L += [table(["standard"] + list(LABELS) + ["(empty or other)"],
                [[p] + [cnt.get((p, lab), 0) for lab in LABELS]
                 + [sum(v for (q, lab), v in cnt.items() if q == p and lab not in LABELS)] for p in PACKS]), ""]
    if checks:
        L += ["Quotes:", "", table(["standard", "rule_id", "label", "passages", "result"],
                                   [[c["standard"], c["rule_id"], c["label"], c["passages"], c["result"]]
                                    for c in checks]), ""]
    L += [f"Errors: {len(errors)}"] + [f"  - {e}" for e in errors]
    return "\n".join(L)


def render(res):
    s = res["settings"]
    L = ["# Addendum A14: compliance on the rules the documents state", "",
         f"Sheet `{s['sheet']}` (sha256 `{s['sheet_sha256']}`). Cluster bootstrap over source files with "
         f"{s['resamples']:,} resamples and seed {s['seed']}; an interval is the value itself when every value in "
         f"it is equal. Runs: {len(s['runs'])}.", ""]
    p1 = res["part1"]
    L += ["## 1. Rules and test tasks by label", "",
          table(["standard", "label", "core rules", "excluded rules", "test tasks"],
                [[r["pack"], r["label"], r["core_rules"], r["excluded_rules"], r["test_tasks"]]
                 for r in p1["by_label"]]), "",
          "The core rules of the test tasks:", "",
          table(["standard", "rule", "label", "test tasks"],
                [[r["pack"], r["rule_id"], r["label"], r["test_tasks"]] for r in p1["rules_of_test_tasks"]]), "",
          f"Rules with no test task: {p1['rules_without_test_tasks']} (counted, not analysed).", "",
          "How the quotes were found in the pinned documents:", "",
          table(["standard", "rule", "label", "passages", "result"],
                [[c["standard"], c["rule_id"], c["label"], c["passages"], c["result"]] for c in res["quotes"]]), ""]

    L += ["## 2. Compliance on the kept tasks (%, with the cluster-bootstrap interval)", ""]
    cells = defaultdict(dict)
    meta = {}
    for r in res["part2"]:
        k = (r["set"], r["pack"], r["model"])
        meta[k] = r
        cells[k][r["condition"]] = ("no task" if not r["tasks"] else
                                    f"{pct(r['task_mean'])} [{pct(r['file_low'])}, {pct(r['file_high'])}]")
    sel = [r for r in res["part2"] if r["condition"] == SELECTION]
    L += [table(["set", "standard", "model", "tasks", "files"] + list(CONDITIONS),
                [[r["set"], r["pack"], r["model"], r["tasks"], r.get("files", 0)]
                 + [cells[(r["set"], r["pack"], r["model"])].get(c, "") for c in CONDITIONS] for r in sel]), ""]

    L += ["## 3. Selection against no standard and against the full document on the kept tasks", "",
          "Mean paired difference in pp with its cluster-bootstrap interval, and the wins, ties and losses of "
          "selection over the paired tasks. The rule of H3 (non-inferior if the lower limit is above -2 pp) is "
          "applied to the kept tasks only to show whether its outcome would differ; it is not a test.", ""]

    def fmt(r):
        if not r["tasks"]:
            return "no task", ""
        return (f"{r['mean_diff_pp']:+.1f} [{r['ci_low_pp']:+.1f}, {r['ci_high_pp']:+.1f}]",
                f"{r['wins']}/{r['ties']}/{r['losses']}")

    pairs = defaultdict(dict)
    for r in res["part3"]:
        pairs[(r["set"], r["pack"], r["model"])][r["reference"]] = r
    out = []
    for (st, pack, model), d in pairs.items():
        a, b = d.get(NONE), d.get(FULLDOC)
        da, wa = fmt(a) if a else ("", "")
        db, wb = fmt(b) if b else ("", "")
        out.append([st, pack, model, (b or a or {}).get("tasks", 0), da, wa, db, wb,
                    (b or {}).get("h3_rule", "") if b and b["tasks"] else ""])
    L += [table(["set", "standard", "model", "tasks", "vs none", "W/T/L", "vs fulldoc", "W/T/L",
                 "rule of H3"], out), ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sources", default=DEFAULT_SOURCES)
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--meta", nargs="+", default=None)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--model-field", default="backend")
    ap.add_argument("--cluster-field", default="file")
    ap.add_argument("--resamples", type=int, default=C.BOOT_B)
    ap.add_argument("--seed", type=int, default=C.BOOT_SEED)
    ap.add_argument("--out", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    header, rows = read_sheet(a.sources)
    sha = sha256_of(a.sources)
    errors, checks = validate(header, rows, a.root)
    if a.check:
        print(render_check(a.sources, sha, rows, errors, checks))
        sys.exit(1 if errors else 0)
    if errors:
        sys.exit("the sheet is not ready:\n  - " + "\n  - ".join(errors))
    if not a.meta:
        sys.exit("--meta is required unless --check is given")

    dirs = expand(a.meta)
    missing = [d for d in dirs if not os.path.exists(os.path.join(d, "trials.jsonl"))]
    if missing:
        sys.exit("no trials.jsonl in: " + ", ".join(missing))
    recs, _err = load_trials(dirs)
    idx, clusters, rule_of, conflicts = index_tasks(recs, a.model_field, a.cluster_field)
    if conflicts:
        sys.exit(f"{len(conflicts)} tasks carry more than one rule_id, e.g. {sorted(conflicts)[:3]}")
    label_of = {r["rule_id"]: r["label"] for r in rows}
    unknown = sorted({rid for rid in rule_of.values() if rid not in label_of}, key=str)
    if unknown:
        sys.exit("rules of test tasks not in the sheet: " + ", ".join(map(str, unknown)))

    res = {"part1": part1_counts(rows, rule_of),
           "part2": part2_compliance(idx, clusters, rule_of, label_of, a.resamples, a.seed),
           "part3": part3_paired(idx, clusters, rule_of, label_of, a.resamples, a.seed),
           "quotes": checks,
           "settings": {"sheet": os.path.relpath(a.sources, a.root), "sheet_sha256": sha,
                        "resamples": a.resamples, "seed": a.seed, "runs": dirs}}
    text = render(res)
    print(text)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=1, default=str)


if __name__ == "__main__":
    main()
