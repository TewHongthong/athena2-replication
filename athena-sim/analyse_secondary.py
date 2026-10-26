#!/usr/bin/env python3
"""analyse_secondary - the secondary and exploratory analyses of HYPOTHESES_v2.md (H2 to H6; h7, the assistant comparison, is outside the scope of the study).

  python analyse_secondary.py h2 runs/<dev-or-test run> ... [--packs godot,dotnet-runtime,odoo]
  python analyse_secondary.py h4 --human runs/<run> ... --llm runs/<run> ... [--agreement-root [DIR] | --kappa labels.csv]
  python analyse_secondary.py h5 --metadata runs/<run> ... --inferred runs/<run> ...
  python analyse_secondary.py h6 --labels renames.csv
  python analyse_secondary.py h7 --assistant runs/<run> ... --ref runs/<run> ... --assistant-label A --ref-label M
                              --rules-cond C --norules-cond C --margin-pp X [--unknown-packs p1,p2]
  python analyse_secondary.py dose runs/<run> ... [--packs godot,dotnet-runtime,odoo]

Everything here is exploratory. The numeric thresholds are those of HYPOTHESES_v2.md, Section 2.4; the defaults are their
nominal values. The assistant comparison has no default margin.

  --selection   condition name of selection in the trials (default graph)
  --packs       pack ids to include (default godot,dotnet-runtime,odoo); add anchor packs for H2
  --model-field trial field that identifies the model (default backend)
  --cluster-field trial field that defines the bootstrap clusters (default file)
  --out / --json  write the report (markdown) / the full results (JSON)

h4/h5: give the runs of each variant in its own group; the same task ids must appear in both groups (the same
benchmark), and the condition name of selection must be the same in both. h6: CSV with the columns breaks, aware,
blind (0/1), one row per proposed rename, where `breaks` marks a conflict case (1) or a rename to a fresh name (0). h4 --agreement-root: kappa by
identifier kind (athena/agreement.py) over the packs of --packs; --kappa: CSV with the columns human, llm, one row per
attribute (alternative).
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from athena import agreement, confirmatory, secondary  # noqa: E402


def _packs(s: str) -> tuple:
    return tuple(p.strip() for p in s.split(",") if p.strip())


def _check(dirs) -> list:
    return [d for d in dirs if not os.path.exists(os.path.join(d, "trials.jsonl"))]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="hyp", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--selection", default="graph")
    common.add_argument("--none", default="none", dest="none_cond")
    common.add_argument("--packs", default=",".join(confirmatory.DEFAULT_PACKS))
    common.add_argument("--model-field", default="backend")
    common.add_argument("--cluster-field", default="file")
    common.add_argument("--bootstrap", type=int, default=confirmatory.BOOT_B)
    common.add_argument("--seed", type=int, default=confirmatory.BOOT_SEED)
    common.add_argument("--out", default=None)
    common.add_argument("--json", default=None)

    p = sub.add_parser("h2", parents=[common])
    p.add_argument("run_dirs", nargs="+")
    p.add_argument("--permutations", type=int, default=secondary.PERM_B)

    p = sub.add_parser("dose", parents=[common])
    p.add_argument("run_dirs", nargs="+")
    p.add_argument("--permutations", type=int, default=secondary.PERM_B)

    p = sub.add_parser("h4", parents=[common])
    p.add_argument("--human", nargs="+", required=True)
    p.add_argument("--llm", nargs="+", required=True)
    p.add_argument("--kappa", default=None)
    p.add_argument("--agreement-root", nargs="?", const=os.path.join(HERE, "packs"), default=None,
                   help="folder with packs/<pack>/*_ontology.json and packs/<pack>/llm/llm_ontology.json: kappa by "
                        "identifier kind over the packs of --packs (default folder: packs next to this script)")
    p.add_argument("--margin-pp", type=float, default=100 * secondary.H4_MARGIN)
    p.add_argument("--kappa-min", type=float, default=secondary.H4_KAPPA)

    p = sub.add_parser("h5", parents=[common])
    p.add_argument("--metadata", nargs="+", required=True)
    p.add_argument("--inferred", nargs="+", required=True)
    p.add_argument("--margin-pp", type=float, default=100 * secondary.H5_MARGIN)

    p = sub.add_parser("h6", parents=[common])
    p.add_argument("--labels", required=True)

    p = sub.add_parser("h7", parents=[common])
    p.add_argument("--assistant", nargs="+", required=True)
    p.add_argument("--ref", nargs="+", required=True)
    p.add_argument("--assistant-label", required=True, help="value of the model field of the assistant runs")
    p.add_argument("--ref-label", required=True, help="value of the model field of the reference LLM runs")
    p.add_argument("--rules-cond", required=True, help="condition name of the assistant with the rules file")
    p.add_argument("--norules-cond", required=True, help="condition name of the assistant without a rules file")
    p.add_argument("--fulldoc", default="fulldoc")
    p.add_argument("--margin-pp", type=float, default=None, help="equivalence margin in pp (no default)")
    p.add_argument("--unknown-packs", default="", help="packs whose standard the model does not know")
    return ap


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    packs = _packs(a.packs)
    kw = dict(model_field=a.model_field, cluster_field=a.cluster_field)
    if a.hyp == "h6":
        res = secondary.h6(secondary.read_h6_csv(a.labels))
        md = secondary.render_h6(res)
    else:
        groups = {"h2": [a.run_dirs] if a.hyp == "h2" else [],
                  "dose": [a.run_dirs] if a.hyp == "dose" else [],
                  "h4": [a.human, a.llm] if a.hyp == "h4" else [],
                  "h5": [a.metadata, a.inferred] if a.hyp == "h5" else [],
                  "h7": [a.assistant, a.ref] if a.hyp == "h7" else []}[a.hyp]
        missing = [d for g in groups for d in _check(g)]
        if missing:
            print("no trials.jsonl in: " + ", ".join(missing), file=sys.stderr)
            return 2
        load = secondary.load_dose if a.hyp == "dose" else secondary.load_index
        loaded = [load(g, **kw) for g in groups]
        clusters = secondary.merge_clusters(*[x[1] for x in loaded])
        if a.hyp == "h2":
            res = secondary.h2(loaded[0][0], packs, a.selection, a.none_cond, a.permutations, a.seed)
            md = secondary.render_h2(res)
        elif a.hyp == "dose":
            res = secondary.dose_response(loaded[0][0], loaded[0][4], packs, a.selection, a.none_cond,
                                          b=a.permutations, seed=a.seed)
            md = secondary.render_dose(res)
        elif a.hyp == "h4":
            if a.kappa and a.agreement_root:
                print("h4: give --kappa or --agreement-root, not both", file=sys.stderr)
                return 2
            pairs = secondary.read_kappa_csv(a.kappa) if a.kappa else None
            agr = None
            if a.agreement_root:
                try:
                    agr = agreement.compare_packs(a.agreement_root, packs)
                except ValueError as exc:
                    print(f"h4: {exc}", file=sys.stderr)
                    return 2
            res = secondary.h4(loaded[0][0], loaded[1][0], clusters, packs, a.selection, a.margin_pp / 100, pairs,
                               a.kappa_min, a.bootstrap, a.seed, agreement=agr)
            md = secondary.render_h4(res)
        elif a.hyp == "h5":
            res = secondary.h5(loaded[0][0], loaded[1][0], clusters, packs, a.selection, a.margin_pp / 100,
                               a.bootstrap, a.seed)
            md = secondary.render_h5(res)
        else:
            if a.margin_pp is None:
                print("h7 needs --margin-pp: the equivalence margin is not registered", file=sys.stderr)
                return 2
            res = secondary.h7(loaded[0][0], loaded[1][0], clusters, packs, a.assistant_label, a.ref_label,
                               a.rules_cond, a.norules_cond, a.margin_pp / 100, _packs(a.unknown_packs),
                               a.selection, a.none_cond, a.fulldoc, a.bootstrap, a.seed)
            md = secondary.render_h7(res)
        res["n_trials"] = [x[2] for x in loaded]
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(md)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            f.write(secondary.dumps(res))
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
