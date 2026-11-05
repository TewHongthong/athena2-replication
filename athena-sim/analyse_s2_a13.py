#!/usr/bin/env python3
"""analyse_s2_a13 - ADDENDUM_study2.md, S2-A13: the kind used by the condition with the inferred kind (descriptive).

  python analyse_s2_a13.py [--runs runs] [--pins luna,gemini31fl,gemma4_local_s2,qwen35_9b_or_s2] [--out s2_a13.md] [--json s2_a13.json]

Reads the test infer runs of the pins in the analysis (run folders s2test_<pin>_<pack>_infer) with the reading rules of
the analysis (athena_s2/analysis.py, read_runs: the first record without an error of each key by time stamp), keeps
condition graph (selection), and compares, per task, the kind from metadata (kind) with the kind the condition used
(kind_used), with the owner that the inference read from the snippet (facets_inferred.owner). The kind used must be
the same in every model and round of a task; a task where it is not is reported. The count decides nothing and is not
part of any hypothesis.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from athena_s2 import analysis as A  # noqa: E402

PACKS = ("godot-s2", "dotnet-runtime-s2")
PINS = "luna,gemini31fl,gemma4_local_s2,qwen35_9b_or_s2"


def tasks(runs_dir: str, pins: list, pack: str) -> dict:
    dirs = [os.path.join(runs_dir, f"s2test_{p}_{pack}_infer") for p in pins]
    missing = [d for d in dirs if not os.path.isdir(d)]
    if missing:
        raise SystemExit(f"missing run folders: {', '.join(missing)}")
    recs, _, error_keys = A.read_runs(dirs)
    seen = collections.defaultdict(set)
    for r in recs:
        if r.get("condition_base") != "graph":
            continue
        owner = (r.get("facets_inferred") or {}).get("owner")
        seen[r["unit_id"]].add((r.get("kind"), r.get("kind_used"), owner))
    return {"tasks": seen, "error_keys": len(error_keys), "runs": [os.path.basename(d) for d in dirs]}


def count(pack: str, got: dict) -> dict:
    seen = got["tasks"]
    varying = sorted(u for u, s in seen.items() if len(s) != 1)
    rows = collections.Counter(next(iter(s)) for u, s in seen.items() if len(s) == 1)
    agree = sum(n for (k, used, _), n in rows.items() if k == used)
    return {"pack": pack, "tasks": len(seen), "agree": agree, "kind_used_varies": varying,
            "error_keys": got["error_keys"], "runs": got["runs"],
            "rows": [{"kind": k, "kind_used": used, "owner": owner, "tasks": n}
                     for (k, used, owner), n in sorted(rows.items(), key=lambda x: (str(x[0][0]), str(x[0][1]), str(x[0][2])))]}


def render(res: list) -> str:
    out = ["# S2-A13: the kind used by the condition with the inferred kind (descriptive)", "",
           "Test split, condition graph of the infer runs. The count decides nothing.", "",
           "| Pack | Kind from metadata | Kind used | Owner read from the snippet | Tasks |", "|---|---|---|---|---|"]
    for p in res:
        for r in p["rows"]:
            out.append(f"| {p['pack']} | {r['kind']} | {r['kind_used']} | {r['owner'] or 'n/a'} | {r['tasks']} |")
    out.append("")
    for p in res:
        out.append(f"- {p['pack']}: kind used equals the kind from metadata on {p['agree']} of {p['tasks']} tasks; "
                   f"tasks whose kind used differs between models or rounds: {len(p['kind_used_varies'])}; "
                   f"keys with errors only: {p['error_keys']}.")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", default=os.path.join(HERE, "runs"))
    ap.add_argument("--pins", default=PINS, help="comma-separated pins of the analysis")
    ap.add_argument("--out", default=None, help="write the report (markdown) here")
    ap.add_argument("--json", default=None, help="write the results (JSON) here")
    a = ap.parse_args(argv)
    pins = [p for p in a.pins.split(",") if p]
    res = [count(p, tasks(a.runs, pins, p)) for p in PACKS]
    md = render(res)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(md + "\n")
    if a.json:
        with open(a.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump(res, f, indent=2)
            f.write("\n")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
