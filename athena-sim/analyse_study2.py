#!/usr/bin/env python3
"""analyse_study2 - the analysis of Study 2 (HYPOTHESES_v2_study2.md, Sections 2.2 to 2.4 and 4) across run folders.

  python analyse_study2.py runs/s2dev_* runs/s2test_* --canary runs/s2canary_* [--out study2.md] [--json study2.json]

Give the run folders of the development round (eligibility, Section 2.3) and of the test round (H1-S2 to H4-S2 and
the reports), both families (meta and infer) and every model; not the canary runs, which share their keys with the
development round. The family of a run is read from its config.json. The computation is in athena_s2/analysis.py.

  --canary         the canary run folders (names with canary_before or canary_after), for the drift check of
                   HYPOTHESES_v2.md Section 2.1; each is read on its own

  --packs          packs to include (default godot-s2,dotnet-runtime-s2)
  --models         models to include (comma-separated; a name matches every model whose name contains it; default all)
  --model-field    trial field that identifies the model (default pin: the --model-pin of the run, else the backend)
  --cluster-field  trial field that defines the bootstrap clusters (default file: the source file of the task)
  --bench          folder with one benchmark folder per pack, for the snippets (default $ATHENA_S2_BENCH)
  --keep           which record of a key written more than once is used: first (default) or last, by time stamp
  --compare-split  split of the comparisons (default test); dev runs the comparisons on the development round,
                   as a check of the procedure before the test round, and the report says so
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from athena import confirmatory  # noqa: E402
from athena_s2 import analysis  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dirs", nargs="+", help="run folders (each with a trials.jsonl and a config.json)")
    ap.add_argument("--canary", nargs="+", default=[], help="canary run folders (drift check)")
    ap.add_argument("--packs", default=",".join(analysis.PACKS))
    ap.add_argument("--models", default="")
    ap.add_argument("--model-field", default="pin")
    ap.add_argument("--cluster-field", default="file")
    ap.add_argument("--bench", default=os.environ.get("ATHENA_S2_BENCH"))
    ap.add_argument("--keep", choices=["first", "last"], default="first")
    ap.add_argument("--compare-split", choices=["test", "dev"], default="test")
    ap.add_argument("--bootstrap", type=int, default=confirmatory.BOOT_B, help="bootstrap resamples")
    ap.add_argument("--seed", type=int, default=confirmatory.BOOT_SEED)
    ap.add_argument("--out", default=None, help="write the report (markdown) here")
    ap.add_argument("--json", default=None, help="write the full results (JSON) here")
    a = ap.parse_args(argv)
    missing = [d for d in a.run_dirs + a.canary if not os.path.exists(os.path.join(d, "trials.jsonl"))]
    if missing:
        print("no trials.jsonl in: " + ", ".join(missing), file=sys.stderr)
        return 2
    try:
        res, md = analysis.run(a.run_dirs, bench_dir=a.bench, keep=a.keep, canary_dirs=a.canary,
                               packs=tuple(p.strip() for p in a.packs.split(",") if p.strip()),
                               compare_split=a.compare_split, model_field=a.model_field,
                               cluster_field=a.cluster_field, b=a.bootstrap, seed=a.seed,
                               models=[m.strip() for m in a.models.split(",") if m.strip()])
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(md + "\n")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            f.write(analysis.dumps(res) + "\n")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
