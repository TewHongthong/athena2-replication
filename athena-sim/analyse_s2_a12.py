#!/usr/bin/env python3
"""analyse_s2_a12 - ADDENDUM_study2.md, S2-A12: the two deployments of Qwen3.5-9B on the canary before (descriptive).

  python analyse_s2_a12.py [--runs runs] [--local qwen35_9b_s2] [--hosted qwen35_9b_or_s2] [--out s2_a12.md] [--json s2_a12.json]

The local deployment (qwen35_9b_s2) and the hosted deployment (qwen35_9b_or_s2) each ran the canary before on the
same dev units under condition none (run folders s2canary_before_<pin>_<pack>). Each folder is read with the reading
rules of the analysis (athena_s2/analysis.py, read_runs: the first record without an error of each key by time
stamp). On the units present in both, per pack and overall: core_ok_s2 of each deployment, the units that pass on one
deployment only, the exact two-sided McNemar p, the share of units with the same proposed name (both parsed and
equal), and the answers that could not be parsed. The comparison decides nothing and is not part of any hypothesis.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from athena.report import mcnemar_p  # noqa: E402
from athena_s2 import analysis as A  # noqa: E402

PACKS = ("godot-s2", "dotnet-runtime-s2")


def canary_units(runs_dir: str, pin: str) -> dict:
    dirs = [d for p in PACKS for d in sorted(glob.glob(os.path.join(runs_dir, f"s2canary_before_{pin}_{p}")))]
    if not dirs:
        raise SystemExit(f"no canary before run folders for {pin} in {runs_dir}")
    recs, _, error_keys = A.read_runs(dirs)
    out = {}
    for r in recs:
        if r.get("condition") == "none":
            out[(r["pack"], r["unit_id"])] = r
    return {"units": out, "error_keys": len(error_keys), "runs": [os.path.basename(d) for d in dirs]}


def compare(loc: dict, hos: dict, pack=None) -> dict:
    keys = sorted(k for k in set(loc) & set(hos) if pack is None or k[0] == pack)
    ol = [bool(A.metrics(loc[k]).get("core_ok")) for k in keys]
    oh = [bool(A.metrics(hos[k]).get("core_ok")) for k in keys]
    local_only = sum(a and not b for a, b in zip(ol, oh))
    hosted_only = sum(b and not a for a, b in zip(ol, oh))
    nl = [A.proposed(loc[k]) for k in keys]
    nh = [A.proposed(hos[k]) for k in keys]
    same = sum(a is not None and a == b for a, b in zip(nl, nh))
    n = len(keys)
    return {"pack": pack or "all", "units": n, "local_pass": sum(ol), "hosted_pass": sum(oh),
            "local": sum(ol) / n if n else None, "hosted": sum(oh) / n if n else None,
            "pass_local_only": local_only, "pass_hosted_only": hosted_only,
            "mcnemar_p": mcnemar_p(local_only, hosted_only) if n else None,
            "same_name": same, "same_name_share": same / n if n else None,
            "unparsed_local": sum(x is None for x in nl), "unparsed_hosted": sum(x is None for x in nh)}


def render(res: dict) -> str:
    def pc(x):
        return "n/a" if x is None else f"{100 * x:.1f}"
    out = ["# S2-A12: the two deployments of Qwen3.5-9B on the canary before (descriptive)", "",
           f"Local: `{res['local_pin']}` ({', '.join(res['local_runs'])}); hosted: `{res['hosted_pin']}` "
           f"({', '.join(res['hosted_runs'])}). Condition none, one round. Units only in one deployment: "
           f"local {res['local_only_units']}, hosted {res['hosted_only_units']}. The comparison decides nothing.", "",
           "| Pack | Units | core_ok_s2 local | core_ok_s2 hosted | Pass local only | Pass hosted only | McNemar p "
           "| Same name | Unparsed local | Unparsed hosted |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for r in res["rows"]:
        mp = "n/a" if r["mcnemar_p"] is None else f"{r['mcnemar_p']:.3f}"
        out.append(f"| {r['pack']} | {r['units']} | {r['local_pass']} ({pc(r['local'])}%) | {r['hosted_pass']} "
                   f"({pc(r['hosted'])}%) | {r['pass_local_only']} | {r['pass_hosted_only']} | {mp} | "
                   f"{r['same_name']} ({pc(r['same_name_share'])}%) | {r['unparsed_local']} | {r['unparsed_hosted']} |")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", default=os.path.join(HERE, "runs"))
    ap.add_argument("--local", default="qwen35_9b_s2")
    ap.add_argument("--hosted", default="qwen35_9b_or_s2")
    ap.add_argument("--out", default=None, help="write the report (markdown) here")
    ap.add_argument("--json", default=None, help="write the results (JSON) here")
    a = ap.parse_args(argv)
    lo, ho = canary_units(a.runs, a.local), canary_units(a.runs, a.hosted)
    loc, hos = lo["units"], ho["units"]
    res = {"local_pin": a.local, "hosted_pin": a.hosted, "local_runs": lo["runs"], "hosted_runs": ho["runs"],
           "local_error_keys": lo["error_keys"], "hosted_error_keys": ho["error_keys"],
           "local_only_units": len(set(loc) - set(hos)), "hosted_only_units": len(set(hos) - set(loc)),
           "rows": [compare(loc, hos, p) for p in PACKS] + [compare(loc, hos)]}
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
