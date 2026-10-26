#!/usr/bin/env python3
"""make_h6_labels - build renames.csv for H6 (HYPOTHESES_v2.md, Section 2.4).

One row per proposed rename, with the columns that `analyse_secondary.py h6 --labels` reads:
  breaks  1 if the rename conflicts with another binding in scope (ground truth), else 0
  aware   1 if the scope-aware check flags it (binding or declaration conflict)
  blind   1 if the scope-blind check flags it (the new name already occurs in the snippet as a word)
and the columns set, pack, language, id, which the analysis ignores.

Two sets of rows:
  hand   the hand-written controls of the scope check (curation/tests_scope); breaks is the outcome stated for
         each case before the resolver was run. --out holds the conflict cases only, because H6 measures false
         alarms on renames to fresh names; --out-all holds all controls and the fresh renames, for description
  fresh  one row per task of the B1 benchmark (development and test part of the three packs): the injected name
         is renamed back to the original name, a name the compliant code used before the injection, so there is
         no conflict by construction (breaks = 0)

Rows for which the check does not give a verdict (snippet that does not parse, injected name not in the snippet)
are not written; their number is printed. The Python front end needs Python 3.12 or later for the Odoo snippets.

  python make_h6_labels.py [--curation DIR] [--runs runs] [--out renames.csv] [--out-all renames_all.csv]
  --curation  folder of scope_check.py (default: $ATHENA_CORPUS/curation, else ../athena-corpus/curation)
"""
import argparse
import collections
import csv
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = re.compile(r"CODE\n```[^\n]*\n(.*?)\n```\n", re.S)
PACKS = ("godot", "dotnet-runtime", "odoo")


def load_cases(curation):
    path = os.path.join(curation, "tests_scope", "test_scope_check.py")
    spec = importlib.util.spec_from_file_location("scope_cases", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CASES


def flags(res):
    return (int(bool(res["binding_conflict"] or res["declaration_conflict"])), int(bool(res["scope_blind"])))


def tasks(runs):
    """(pack, split, unit_id, language, original, injected, code) once per task from the condition `none` of the
    development pilot and the test runs of one model; the prompt holds the snippet with the injected name."""
    seen = {}
    for pack in PACKS:
        for run in (f"pilot_luna_{pack}_meta", f"test_{pack}_luna_meta"):
            with open(os.path.join(runs, run, "trials.jsonl"), encoding="utf-8") as f:
                for line in f:
                    r = json.loads(line)
                    if r["condition"] != "none" or (pack, r["unit_id"]) in seen:
                        continue
                    m = CODE.search(r["prompt"])
                    if not m:
                        raise SystemExit(f"no code block in the prompt of {r['unit_id']}")
                    seen[(pack, r["unit_id"])] = (pack, r["split"], r["unit_id"], r["language"], r["original"],
                                                  r["injected"], m.group(1))
    return list(seen.values())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    base = os.environ.get("ATHENA_CORPUS") or os.path.join(HERE, "..", "athena-corpus")
    ap.add_argument("--curation", default=os.path.join(base, "curation"))
    ap.add_argument("--runs", default=os.path.join(HERE, "runs"))
    ap.add_argument("--out", default="renames.csv")
    ap.add_argument("--out-all", default="renames_all.csv")
    a = ap.parse_args()
    sys.path.insert(0, a.curation)
    from scope_check import check_rename

    rows, skipped = [], collections.Counter()
    for lang, label, code, old, new, conflict in load_cases(a.curation):
        aware, blind = flags(check_rename(lang, code, old, new))
        rows.append({"breaks": int(conflict), "aware": aware, "blind": blind, "set": "hand", "pack": "",
                     "language": lang, "id": label, "status": "ok"})
    for pack, split, uid, lang, original, injected, code in tasks(a.runs):
        res = check_rename(lang, code, injected, original)
        if res["status"] in ("unsupported", "no_occurrence"):
            skipped[(pack, res["status"])] += 1
            continue
        aware, blind = flags(res)
        rows.append({"breaks": 0, "aware": aware, "blind": blind, "set": "fresh", "pack": pack, "language": lang,
                     "id": f"{split}:{uid}", "status": res["status"]})
    cols = ["breaks", "aware", "blind", "set", "pack", "language", "id", "status"]
    for path, keep in ((a.out, [r for r in rows if r["set"] == "fresh" or r["breaks"]]), (a.out_all, rows)):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(keep)
        print(f"{len(keep)} rows written to {path}")
    for s in ("hand", "fresh"):
        sub = [r for r in rows if r["set"] == s]
        print(f"  {s}: {len(sub)} rows, breaks={sum(r['breaks'] for r in sub)}, aware={sum(r['aware'] for r in sub)}, "
              f"blind={sum(r['blind'] for r in sub)}")
    for k, v in sorted(skipped.items()):
        print(f"  not written {k[0]} {k[1]}: {v}")


if __name__ == "__main__":
    main()
