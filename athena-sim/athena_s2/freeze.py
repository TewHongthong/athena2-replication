"""The freeze of Study 2: athena.freeze with the Study 2 code and registration added.

The fingerprint is that of Study 1 (harness version, code, pack, settings, HYPOTHESES.md, HYPOTHESES_v2.md and, with
--no-oracle, the curation code) where the code covers athena/*.py, athena_sim.py, vendor/output_validator.py,
athena_s2/*.py and athena2_s2.py, the curation code covers the Study 2 files as well (athena_s2.pipeline), and two
keys are added: the version of this package and the SHA-256 of HYPOTHESES_v2_study2.md. A frozen file of Study 2 is
verified on every key.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os

from athena import freeze as F1

from . import __version__

SIM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HYPOTHESES_S2 = os.path.join(os.path.dirname(SIM), "HYPOTHESES_v2_study2.md")
S2_KEYS = ("harness_s2_version", "hypotheses_s2_sha256")

_study1_code_hashes = F1.code_hashes
_study1_fingerprint = F1.fingerprint
_study1_verify = F1.verify


def code_hashes() -> dict:
    per = {k: v for k, v in _study1_code_hashes().items() if k != "ALL"}
    files = sorted(glob.glob(os.path.join(SIM, "athena_s2", "*.py"))) + [os.path.join(SIM, "athena2_s2.py")]
    per.update({os.path.relpath(p, SIM).replace(os.sep, "/"): F1._sha_file(p) for p in files})
    per["ALL"] = hashlib.sha256(json.dumps(per, sort_keys=True).encode()).hexdigest()
    return per


def fingerprint(args, pack) -> dict:
    fp = _study1_fingerprint(args, pack)
    fp["harness_s2_version"] = __version__
    fp["hypotheses_s2_sha256"] = F1._sha_file(HYPOTHESES_S2)
    return fp


def verify(frozen_path: str, args, pack) -> list:
    diffs = _study1_verify(frozen_path, args, pack)
    with open(frozen_path, "r", encoding="utf-8") as f:
        frozen = json.load(f)
    now = fingerprint(args, pack)
    for key in S2_KEYS:
        diffs += F1._diff(frozen.get(key), now.get(key), key + ".")
    return diffs
