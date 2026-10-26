#!/usr/bin/env python3
"""Write the selected B1 tasks of one pack in the layout of Vol. 1 (HYPOTHESES_v2, D18).

Input   <pack>_selection.tsv     from tools/select_tasks.py (columns pack, side, rank, path, unit_index, ...)
        <pack>_pool_units.jsonl  from tools/build_pool.py (the full record of every pool unit)
Output  snippets/<language>/<prefix>_NNN.json      one snippet per task, one identifier (the target)
        violations/<language>/<snippet>__<name>__<rule>.json   its injected violation
        snippets_index.tsv, violations_index.tsv   as in Vol. 1
        tasks.tsv, tasks_summary.json              split, rank, kind, rule and method of each task; counts by split

Task ids follow (side, rank): the dev tasks first (dev rank 1 is <prefix>_001), then the test tasks. The files carry the
extra keys `pack`, `split` and `unitIndex`; validate_benchmark.py ignores them.

  python3 tools/export_tasks.py --pack godot --language cpp --selection sel/godot_selection.tsv \\
      --pool-units pool/godot_pool_units.jsonl --ontology ... --core ... --out-dir bench/godot
  python3 validate_benchmark.py --benchmark bench/godot --corpus athena-corpus/corpus_v2 --ontology ... \\
      --languages cpp --core ...
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CUR = os.path.dirname(HERE)
sys.path.insert(0, CUR)

import curate as C  # noqa: E402
import rules as R  # noqa: E402

SIDE_ORDER = ("dev", "test")
TASK_COLUMNS = ["task_id", "pack", "split", "rank", "repo", "path", "unit_index", "start_line", "end_line", "unit",
                "kind", "rule", "method", "original_name", "injected_name"]


class ExportError(Exception):
    pass


def read_selection(path, pack):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    for col in ("pack", "side", "rank", "path", "unit_index"):
        if rows and col not in rows[0]:
            raise ExportError("selection file has no column %r" % col)
    out = []
    for r in rows:
        if r["pack"] != pack:
            raise ExportError("selection row of pack %r, expected %r" % (r["pack"], pack))
        if r["side"] not in SIDE_ORDER:
            raise ExportError("unknown side %r" % r["side"])
        out.append({"side": r["side"], "rank": int(r["rank"]), "path": r["path"], "unit_index": int(r["unit_index"])})
    out.sort(key=lambda r: (SIDE_ORDER.index(r["side"]), r["rank"]))
    return out


def read_units(path):
    units = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                u = json.loads(line)
                units[(u["path"], u["unit_index"])] = u
    return units


def safe(name):
    return C._safe(name)


def export(pack, lang, selection, units, onto, out_dir):
    """Write the benchmark folder. Returns the summary dict."""
    if len(selection) > 999:
        raise ExportError("more than 999 tasks: ids are <prefix>_NNN")
    prefix = C.ID_PREFIX[lang]
    sdir = os.path.join(out_dir, "snippets", lang)
    vdir = os.path.join(out_dir, "violations", lang)
    os.makedirs(sdir, exist_ok=True)
    os.makedirs(vdir, exist_ok=True)
    snippet_rows, viol_rows, task_rows = [], [], []
    summary = {"pack": pack, "language": lang, "tasks": len(selection), "by_split": collections.Counter(),
               "by_kind": collections.defaultdict(collections.Counter),
               "by_method": collections.defaultdict(collections.Counter),
               "by_rule": collections.defaultdict(collections.Counter)}
    for i, sel in enumerate(selection, 1):
        u = units.get((sel["path"], sel["unit_index"]))
        if u is None:
            raise ExportError("selected unit (%s, %d) is not in the pool units file" % (sel["path"], sel["unit_index"]))
        sid = "%s_%03d" % (prefix, i)
        tgt, v = u["target"], u["violation"]
        snippet = {
            "id": sid,
            "language": lang,
            "source": "github:%s@%s" % (u["repo"], u["commit"]),
            "sourceDetail": ("%s lines %d-%d (%s); license %s; repo created %s; curated by %s" % (
                u["path"], u["start_line"], u["end_line"], u["unit"], u["license"], u["created_at"],
                C.PIPELINE_VERSION)),
            "standardId": onto.default_standard[lang],
            "codeContext": u["code"],
            "identifiers": [{"name": tgt["name"], "kind": tgt["kind"], "isCompliant": True}],
            "provenance": {
                "repo": u["repo"], "repoUrl": u.get("repo_url"), "license": u["license"],
                "repoCreatedAt": u["created_at"], "commit": u["commit"], "path": u["path"],
                "startLine": u["start_line"], "endLine": u["end_line"], "unit": u["unit"],
                "corpusFile": "corpus/%s/%s" % (lang, u["file"]),
            },
            "pack": pack,
            "split": sel["side"],
            "unitIndex": u["unit_index"],
        }
        _dump(os.path.join(sdir, sid + ".json"), snippet)
        vio = {
            "snippetId": sid,
            "language": lang,
            "originalName": tgt["name"],
            "injectedName": v["injected"],
            "identifierKind": tgt["kind"],
            "violatedRuleId": v["rule"],
            "injectionMethod": v["method"],
            "expectedViolationReasons": v["reasons"],
            "codeContextWithViolation": v["code"],
            "occurrencesRenamed": v["occurrences"],
            "commentOccurrencesRenamed": v["comment_occurrences"],
            "pack": pack,
            "split": sel["side"],
        }
        if v["rule"] in R.RULE_CAVEATS:
            vio["ruleCaveat"] = R.RULE_CAVEATS[v["rule"]]
        fn = "%s__%s__%s.json" % (sid, safe(tgt["name"]), v["rule"])
        _dump(os.path.join(vdir, fn), vio)
        snippet_rows.append([sid, lang, snippet["standardId"], u["repo"], u["path"], u["start_line"], u["end_line"],
                             u["unit"], 1, tgt["kind"], 1])
        viol_rows.append([sid, lang, tgt["name"], tgt["kind"], v["rule"], v["method"], v["injected"], fn])
        task_rows.append([sid, pack, sel["side"], sel["rank"], u["repo"], u["path"], u["unit_index"], u["start_line"],
                          u["end_line"], u["unit"], tgt["kind"], v["rule"], v["method"], tgt["name"], v["injected"]])
        summary["by_split"][sel["side"]] += 1
        summary["by_kind"][sel["side"]][tgt["kind"]] += 1
        summary["by_method"][sel["side"]][v["method"]] += 1
        summary["by_rule"][sel["side"]][v["rule"]] += 1
    _tsv(os.path.join(out_dir, "snippets_index.tsv"),
         ["snippet_id", "language", "standard_id", "repo", "path", "start_line", "end_line", "unit", "n_targets",
          "target_kinds", "n_violations"], snippet_rows)
    _tsv(os.path.join(out_dir, "violations_index.tsv"),
         ["snippet_id", "language", "original_name", "kind", "rule_id", "method", "injected_name", "file"], viol_rows)
    _tsv(os.path.join(out_dir, "tasks.tsv"), TASK_COLUMNS, task_rows)
    out = {"pack": pack, "language": lang, "tasks": len(selection), "by_split": dict(summary["by_split"])}
    for key in ("by_kind", "by_method", "by_rule"):
        out[key] = {side: dict(c) for side, c in summary[key].items()}
        total = collections.Counter()
        for c in summary[key].values():
            total.update(c)
        out[key]["all"] = dict(total)
    with open(os.path.join(out_dir, "tasks_summary.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return out


def _dump(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _tsv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pack", required=True)
    ap.add_argument("--language", required=True, choices=C.ALL_LANGS)
    ap.add_argument("--selection", required=True)
    ap.add_argument("--pool-units", required=True)
    ap.add_argument("--ontology", required=True)
    ap.add_argument("--core", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    import core_table
    onto = R.Ontology(a.ontology)
    problems = core_table.apply(a.core, onto)
    if problems:
        print("CORE rule table inconsistent with ontology:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2
    try:
        selection = read_selection(a.selection, a.pack)
        units = read_units(a.pool_units)
        summary = export(a.pack, a.language, selection, units, onto, a.out_dir)
    except ExportError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    print("%s: %d tasks written to %s  split %s" % (a.pack, summary["tasks"], a.out_dir, summary["by_split"]))
    print("  by kind:", summary["by_kind"]["all"])
    print("  by method:", summary["by_method"]["all"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
