#!/usr/bin/env python3
"""analyse_confirmatory - the confirmatory analysis of HYPOTHESES_v2.md (Sections 2.3 and 4) across run folders.

  python analyse_confirmatory.py runs/<dev-run> runs/<test-run> ... [--out analysis.md] [--json analysis.json]

Give every run folder of the comparison (dev runs for the eligibility rule, test runs for H1 and H3, any number of
packs and models).  Use only the runs of the selection variant that defines H1 (human ontology, kind from metadata):
runs of other variants must not be mixed in under the same condition name.

  --selection   condition name of selection in the trials (default graph)
  --packs       pack ids of the independent standards (default godot,dotnet-runtime,odoo)
  --model-field trial field that identifies the model (default backend)
  --models      comma-separated names of the models to include (default all); a name matches every model whose
                identifier contains it, e.g. luna,gemini,qwen3.5-9b,gemma-4 for the panel
  --cluster-field trial field that defines the bootstrap clusters (default file: the source file of the task;
                a trial without it falls back to its snippet id, and the report counts how many did)
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from athena import confirmatory  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dirs", nargs="+", help="run folders (each with a trials.jsonl)")
    ap.add_argument("--selection", default="graph")
    ap.add_argument("--none", default="none", dest="none_cond")
    ap.add_argument("--fulldoc", default="fulldoc")
    ap.add_argument("--packs", default=",".join(confirmatory.DEFAULT_PACKS))
    ap.add_argument("--model-field", default="backend")
    ap.add_argument("--models", default="", help="models to include (comma-separated; default all)")
    ap.add_argument("--cluster-field", default="file")
    ap.add_argument("--bootstrap", type=int, default=confirmatory.BOOT_B, help="bootstrap resamples")
    ap.add_argument("--seed", type=int, default=confirmatory.BOOT_SEED)
    ap.add_argument("--out", default=None, help="write the report (markdown) here")
    ap.add_argument("--json", default=None, help="write the full results (JSON) here")
    a = ap.parse_args(argv)
    missing = [d for d in a.run_dirs if not os.path.exists(os.path.join(d, "trials.jsonl"))]
    if missing:
        print("no trials.jsonl in: " + ", ".join(missing), file=sys.stderr)
        return 2
    try:
        res, md = confirmatory.run(a.run_dirs, packs=tuple(p.strip() for p in a.packs.split(",") if p.strip()),
                                   sel=a.selection, none_cond=a.none_cond, fulldoc=a.fulldoc,
                                   model_field=a.model_field, cluster_field=a.cluster_field, b=a.bootstrap,
                                   seed=a.seed, models=[m.strip() for m in a.models.split(",") if m.strip()])
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(md)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            f.write(confirmatory.dumps(res))
    print(md)
    print(f"({res['n_trials']} trials read; {res['n_error_keys']} keys with errors only)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
