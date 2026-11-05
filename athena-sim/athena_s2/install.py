"""Connect the Study 2 parts to the Study 1 harness, inside the calling process only.

The Study 1 runner and command line (athena/runner.py, athena_sim.py) look these names up when they run, so
replacing them here makes `athena_sim.main` run Study 2 without a change to any Study 1 file:

  athena.runner / athena_sim   load_pack -> athena_s2.packs.load_pack; Retriever -> RetrieverS2 (adds naming);
                               CONDITIONS, DEFAULT_CONDITIONS -> those of Study 2; oracle_free_kind -> the Study 2
                               inference; the pack choices -> godot-s2, dotnet-runtime-s2
  athena.pipeline              check_pack, curation_fingerprint, VERSION -> athena_s2.pipeline
  athena.freeze                code_hashes, fingerprint, verify -> athena_s2.freeze
  athena.pins                  DEFAULT_PINS -> models/model_pins_s2.json (the Study 2 panel; --pins still overrides it)

Everything else (prompts, conditions of Study 1, the call to the model, parsing, grading against the pack's core,
the scope-aware check, the test-split guard and the ledger) is the Study 1 code.
"""
from __future__ import annotations

import os

PINS_S2 = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "models",
                                        "model_pins_s2.json"))
_installed = False


def install() -> None:
    global _installed
    if _installed:
        return
    import athena_sim as SIM
    from athena import freeze as FZ
    from athena import pins as PN
    from athena import pipeline as PL
    from athena import runner as RN

    from . import freeze as F2
    from . import packs, retrieval
    from . import pipeline as P2

    for mod in (RN, SIM):
        mod.load_pack = packs.load_pack
        mod.Retriever = retrieval.RetrieverS2
        mod.CONDITIONS = retrieval.CONDITIONS
        mod.oracle_free_kind = P2.oracle_free_kind
    SIM.DEFAULT_CONDITIONS = retrieval.DEFAULT_CONDITIONS
    SIM.VOL2_PACKS = tuple(packs.S2_PACKS)
    SIM.ONTOLOGY_VARIANTS = ("human",)
    PL.check_pack = P2.check_pack
    PL.curation_fingerprint = P2.curation_fingerprint
    PL.VERSION = P2.VERSION
    FZ.code_hashes = F2.code_hashes
    FZ.fingerprint = F2.fingerprint
    FZ.verify = F2.verify
    PN.DEFAULT_PINS = PINS_S2
    _installed = True
