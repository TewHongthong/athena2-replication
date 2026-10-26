"""Freeze a configuration before touching the test split.

Why: the credible way to show that Athena wins is to tune it on the DEV split, freeze everything (code, prompts,
ontology, data, run settings, the written hypotheses) and run the TEST split once.  `freeze` writes a fingerprint
of all of that; `run --split test --frozen <file>` refuses to start if anything differs, and a ledger next to the
frozen file records every test run, so a second run has to be requested explicitly (--allow-rerun) and stays
visible in the results.  Mock backends are exempt: they carry no tuning risk.
"""
from __future__ import annotations

import datetime
import glob
import hashlib
import json
import os

from . import __version__

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HYPOTHESES = os.path.join(ROOT, "HYPOTHESES.md")
# the registration of the Vol. 2 study sits in the repository root, next to athena-sim/
HYPOTHESES_V2 = os.path.join(os.path.dirname(ROOT), "HYPOTHESES_v2.md")

# settings that change the numbers; workers / timeout / retries / output paths / prices do not
SETTING_KEYS = ["pack", "task", "conditions", "languages", "per_language", "limit", "seed", "top_k", "chunk_k",
                "examples", "backend", "temperature", "max_tokens", "reasoning_effort", "repeats"]
# request options added for pinned hosted models; recorded only when used, so earlier frozen files still verify
OPTIONAL_SETTING_KEYS = ["omit_temperature", "extra_body", "no_think", "model_pin", "model_pin_sha256", "no_oracle",
                         "embed_pin", "embed_pin_sha256"]


def _sha_file(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()


def code_hashes() -> dict:
    files = sorted(glob.glob(os.path.join(ROOT, "athena", "*.py"))) + [
        os.path.join(ROOT, "athena_sim.py"), os.path.join(ROOT, "vendor", "output_validator.py")]
    per = {os.path.relpath(p, ROOT).replace(os.sep, "/"): _sha_file(p) for p in files}
    per["ALL"] = hashlib.sha256(json.dumps(per, sort_keys=True).encode()).hexdigest()
    return per


def settings_of(args) -> dict:
    d = {k: getattr(args, k, None) for k in SETTING_KEYS}
    for k in OPTIONAL_SETTING_KEYS:
        v = getattr(args, k, None)
        if v:
            d[k] = v
    d["conditions"] = [c.strip() for c in str(d["conditions"]).split(",") if c.strip()]
    d["languages"] = [x.strip() for x in d["languages"].split(",")] if d["languages"] else None
    d["split"] = "test"
    return d


def fingerprint(args, pack) -> dict:
    fp = {"harness_version": __version__, "code_sha256": code_hashes(), "pack": pack.fingerprint(),
          "settings": settings_of(args), "hypotheses_sha256": _sha_file(HYPOTHESES)}
    h2 = _sha_file(HYPOTHESES_V2)
    if h2:          # recorded only when the file exists, so freezes made without it still verify
        fp["hypotheses_v2_sha256"] = h2
    if getattr(args, "no_oracle", False):      # the curation code that infers the kind and checks the scope is part of the setup
        from . import pipeline
        fp["curation_sha256"] = pipeline.curation_fingerprint()
    return fp


def write_frozen(path: str, args, pack, note: str = "") -> dict:
    fp = fingerprint(args, pack)
    fp["frozen_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    fp["note"] = note
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(fp, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return fp


def _diff(a, b, prefix=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            out += _diff(a.get(k), b.get(k), f"{prefix}{k}.")
    elif a != b:
        out.append(f"{prefix.rstrip('.')}: frozen={a!r} now={b!r}")
    return out


def verify(frozen_path: str, args, pack) -> list:
    """Differences between the frozen file and the current code / data / settings ([] = identical)."""
    with open(frozen_path, "r", encoding="utf-8") as f:
        frozen = json.load(f)
    now = fingerprint(args, pack)
    diffs = []
    for key in ("harness_version", "code_sha256", "pack", "settings", "hypotheses_sha256", "curation_sha256"):
        diffs += _diff(frozen.get(key), now.get(key), key + ".")
    if "hypotheses_v2_sha256" in frozen:        # a freeze that recorded the registration must still match it
        diffs += _diff(frozen.get("hypotheses_v2_sha256"), now.get("hypotheses_v2_sha256"), "hypotheses_v2_sha256.")
    return diffs


# ---------------------------------------------------------------------------------------------- ledger
def ledger_path(frozen_path: str) -> str:
    return frozen_path + ".ledger.jsonl"


def read_ledger(frozen_path: str) -> list:
    p = ledger_path(frozen_path)
    out = []
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    out.append(json.loads(line))
    return out


def append_ledger(frozen_path: str, **entry):
    entry["ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    with open(ledger_path(frozen_path), "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def check_test_run(frozen_path: str, args, pack, run_id: str) -> tuple:
    """Returns (error message or None, rerun flag)."""
    if not os.path.exists(frozen_path):
        return f"frozen file {frozen_path} not found (create it with: athena_sim.py freeze ...)", False
    diffs = verify(frozen_path, args, pack)
    if diffs:
        return ("the current setup differs from the frozen one, so this would not be the test you registered:\n  "
                + "\n  ".join(diffs[:12]) + ("\n  ..." if len(diffs) > 12 else "")
                + "\nRevert the change, or freeze again (the new freeze must be created BEFORE looking at test results)."), False
    other = sorted({e["run_id"] for e in read_ledger(frozen_path) if e.get("run_id") and e["run_id"] != run_id})
    if other and not getattr(args, "allow_rerun", False):
        return (f"the test split was already run under this freeze (run {', '.join(other)}). Resume that run with its "
                "--run-id, or pass --allow-rerun to run again (the rerun is recorded in the ledger and in the report)."), False
    return None, bool(other)
