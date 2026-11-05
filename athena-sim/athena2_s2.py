#!/usr/bin/env python3
"""athena2_s2 - Study 2 command line (HYPOTHESES_v2_study2): the commands of athena_sim.py on the Study 2 packs.

  python athena2_s2.py packs [--corpus <root>]                the Study 2 packs and their tasks
  python athena2_s2.py run|freeze|show|prompts --pack PACK ...  as athena_sim.py (PACK: godot-s2, dotnet-runtime-s2)
  python athena2_s2.py report runs/<run-id> [...]

The benchmark of a pack is read from --corpus or from $ATHENA_S2_BENCH/<pack> (the output of tools/export_tasks_s2.py).
Conditions: none, fulldoc, naming, chunk, bm25, dense, graph. The meta family uses the kind from the benchmark; the
infer family is graph with --no-oracle (the kind and its facets inferred from the code, curation/kind_infer_s2.py).
The grade core_ok of a Study 2 run is core_ok_s2: the core of the Study 2 pack for the kind of the task.
Model pins (--model-pin): luna, gemini31fl, qwen35_9b_s2, gemma4_local_s2 from ../models/model_pins_s2.json, the
default pin file here. A freeze also records athena_s2/*.py, this file and HYPOTHESES_v2_study2.md (athena_s2/freeze.py). See
athena_s2/install.py for how the Study 2 parts are connected to the Study 1 harness.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from athena_s2.install import install  # noqa: E402

install()

import athena_sim  # noqa: E402
from athena_s2 import packs as P  # noqa: E402

NEEDS_PACK = ("run", "freeze", "show", "prompts")


def list_packs(argv) -> int:
    corpus_root = None
    if "--corpus" in argv:
        corpus_root = argv[argv.index("--corpus") + 1]
    for name in P.S2_PACKS:
        try:
            pack = P.load_pack(name, os.path.join(corpus_root, name) if corpus_root else None)
        except FileNotFoundError as e:
            print(f"{name}: not available ({e})")
            continue
        units = pack.rename_units()
        kinds = sorted({u.kind for u in units})
        print(f"{name}: {pack.title}\n  standards: {', '.join(pack.standard_ids())}; document: {pack.standard_doc_id}"
              f"\n  rename units: {len(units)} (dev={sum(u.split == 'dev' for u in units)} "
              f"test={sum(u.split == 'test' for u in units)}); kinds: "
              + ", ".join(f"{k}={sum(u.kind == k for u in units)}" for k in kinds))
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    if argv[0] == "packs":
        return list_packs(argv[1:])
    if argv[0] in NEEDS_PACK and not any(a == "--pack" or a.startswith("--pack=") for a in argv):
        print(f"athena2_s2 {argv[0]}: --pack is required ({', '.join(P.S2_PACKS)})", file=sys.stderr)
        return 2
    return athena_sim.main(argv)


if __name__ == "__main__":
    sys.exit(main())
