#!/usr/bin/env python3
"""Assign the injection method of every selected Study 2 task and write the benchmark in the layout of Study 1.

Input   <pack>_selection.tsv     from tools/select_tasks_s2.py
        <pack>_pool_units.jsonl  from tools/build_pool_s2.py (the verified violation of each available method)
Method  per side, the selected tasks are put in a fixed random order seeded with "athena2-s2-v1:<pack>:method:<side>".
        The side gets ceil(n/2) prefix_strip tasks on dev and floor(n/2) on test, so the pack is split in half (one
        task apart when n is odd), and the rest prefix_swap. A task with only one available method gets that method;
        the other tasks take the remaining places in the random order. If the forced tasks of one method exceed its
        places, the side cannot be balanced and the report says so.
Output  the files of tools/export_tasks.py (snippets/, violations/, the two indexes, tasks.tsv, tasks_summary.json);
        every snippet also carries a key `study2` (method, the methods available, the inferred kind and the facets of
        the target, whether the unit is top level: not a nested type, not a method defined inside its class); study2_report.json holds the method assignment, the agreement
        of the inferred kind with the kind from metadata over the tasks, and, with --study1-tasks, the tasks whose unit
        is a Study 1 task or contains one.

  python3 tools/export_tasks_s2.py --pack godot-s2 --language cpp --selection selection_s2/godot-s2_selection.tsv \\
      --pool-units pool_s2/godot-s2_pool_units.jsonl --ontology ... --core ... --out-dir bench_s2/godot-s2
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import curate as C  # noqa: E402
import export_tasks as E  # noqa: E402
import rules as R  # noqa: E402

SEED = "athena2-s2-v1"
METHODS = ("prefix_strip", "prefix_swap")


def assign_methods(selection, units, pack):
    """{(path, unit_index): method} and the report per side."""
    out, report = {}, {}
    for side in E.SIDE_ORDER:
        rows = [r for r in selection if r["side"] == side]
        order = list(rows)
        random.Random("%s:%s:method:%s" % (SEED, pack, side)).shuffle(order)
        n = len(rows)
        places = {"prefix_strip": (n + 1) // 2 if side == "dev" else n // 2}
        places["prefix_swap"] = n - places["prefix_strip"]
        avail = {(r["path"], r["unit_index"]): set(units[(r["path"], r["unit_index"])]["methods"]) for r in rows}
        forced = collections.Counter()
        free = []
        for r in order:
            k = (r["path"], r["unit_index"])
            if len(avail[k]) == 1:
                m = next(iter(avail[k]))
                out[k] = m
                forced[m] += 1
            else:
                free.append(k)
        n_strip_free = min(max(places["prefix_strip"] - forced["prefix_strip"], 0), len(free))
        for i, k in enumerate(free):
            out[k] = "prefix_strip" if i < n_strip_free else "prefix_swap"
        got = collections.Counter(out[(r["path"], r["unit_index"])] for r in rows)
        report[side] = {"tasks": n, "target": places, "assigned": {m: got[m] for m in METHODS},
                        "forced": {m: forced[m] for m in METHODS}, "balanced": all(got[m] == places[m] for m in METHODS)}
    return out, report


def read_study1_tasks(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return [{"path": r["path"], "unit_index": int(r["unit_index"]), "start_line": int(r["start_line"]),
                 "end_line": int(r["end_line"])} for r in csv.DictReader(fh, delimiter="\t")]


def study1_overlap(lang, selection, units, study1):
    same = contains = 0
    for r in selection:
        u = units[(r["path"], r["unit_index"])]
        for t in study1:
            if t["path"] != r["path"]:
                continue
            if lang == "cpp" and t["unit_index"] == r["unit_index"]:
                same += 1
                break
            if u["start_line"] <= t["start_line"] and t["end_line"] <= u["end_line"]:
                contains += 1
                break
    return {"same_unit": same, "contains_a_study1_task": contains}


def export(pack, lang, selection, units, onto, out_dir, study1=None):
    methods, assign_report = assign_methods(selection, units, pack)
    chosen = {}
    for r in selection:
        k = (r["path"], r["unit_index"])
        u = dict(units[k])
        x = u["methods"][methods[k]]
        u["target"] = {"name": x["target"]["name"], "kind": x["target"]["kind"]}
        u["violation"] = x["violation"]
        chosen[k] = (u, x)
    summary = E.export(pack, lang, selection, {k: v[0] for k, v in chosen.items()}, onto, out_dir)
    agree = collections.Counter()
    rows = sorted(selection, key=lambda r: (E.SIDE_ORDER.index(r["side"]), r["rank"]))
    for i, r in enumerate(rows, 1):
        k = (r["path"], r["unit_index"])
        u, x = chosen[k]
        sid = "%s_%03d" % (C.ID_PREFIX[lang], i)
        p = os.path.join(out_dir, "snippets", lang, sid + ".json")
        with open(p, encoding="utf-8") as fh:
            snip = json.load(fh)
        if snip["unitIndex"] != r["unit_index"] or snip["identifiers"][0]["name"] != x["target"]["name"]:
            raise E.ExportError("snippet %s does not match the selected unit" % sid)
        snip["study2"] = {"injectionMethod": methods[k], "methodsAvailable": sorted(units[k]["methods"]),
                          "targetKindInferred": x["target"]["kind_infer"], "targetFacets": x["target"]["facets"],
                          "topLevel": units[k]["top_level"]}
        E._dump(p, snip)
        agree["%s -> %s" % (x["target"]["kind"], x["target"]["kind_infer"])] += 1
    report = {"pack": pack, "language": lang, "seed": SEED, "method_assignment": assign_report,
              "kind_metadata_to_inferred": dict(agree),
              "kind_agreement": {"n": sum(agree.values()),
                                 "same": sum(v for k, v in agree.items() if k.split(" -> ")[0] == k.split(" -> ")[1])},
              "units_not_top_level": sum(1 for r in selection if not units[(r["path"], r["unit_index"])]["top_level"]),
              "tasks_inside_another_task": sum(
                  1 for a in selection for b in selection if a is not b and a["path"] == b["path"]
                  and units[(a["path"], a["unit_index"])]["start_line"] <= units[(b["path"], b["unit_index"])]["start_line"]
                  and units[(b["path"], b["unit_index"])]["end_line"] <= units[(a["path"], a["unit_index"])]["end_line"])}
    if study1 is not None:
        report["study1_overlap"] = study1_overlap(lang, selection, units, study1)
    with open(os.path.join(out_dir, "study2_report.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return summary, report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pack", required=True)
    ap.add_argument("--language", required=True, choices=["cpp", "csharp"])
    ap.add_argument("--selection", required=True)
    ap.add_argument("--pool-units", required=True)
    ap.add_argument("--ontology", required=True)
    ap.add_argument("--core", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--study1-tasks", default=None, help="tasks.tsv of the Study 1 benchmark of the same standard")
    a = ap.parse_args(argv)
    import core_table
    onto = R.Ontology(a.ontology)
    problems = core_table.apply(a.core, onto)
    if problems:
        print("CORE rule table inconsistent with ontology:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2
    try:
        selection = E.read_selection(a.selection, a.pack)
        units = E.read_units(a.pool_units)
        for r in selection:
            if (r["path"], r["unit_index"]) not in units:
                raise E.ExportError("selected unit (%s, %d) is not in the pool units file" % (r["path"], r["unit_index"]))
        summary, report = export(a.pack, a.language, selection, units, onto, a.out_dir,
                                 read_study1_tasks(a.study1_tasks) if a.study1_tasks else None)
    except E.ExportError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    print("%s: %d tasks %s; by method %s; by kind %s" % (a.pack, summary["tasks"], summary["by_split"],
                                                       summary["by_method"]["all"], summary["by_kind"]["all"]))
    for side, r in report["method_assignment"].items():
        print("  %-4s %s%s" % (side, r["assigned"], "" if r["balanced"] else "  NOT BALANCED (forced %s)" % r["forced"]))
    print("  kind from metadata = inferred: %d of %d" % (report["kind_agreement"]["same"], report["kind_agreement"]["n"]))
    if "study1_overlap" in report:
        print("  Study 1 overlap: %s" % report["study1_overlap"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
