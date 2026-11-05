"""The infer family of Study 2: the identifier kind and its facets inferred from the code shown to the model.

The kind comes from curation/kind_infer_s2.py (which runs the Study 1 inference, kind_infer.py, and reads the Study 2
facets with facets_s2.py). The scope-aware check and everything else of athena.pipeline are used as they are.
The curation code recorded in a freeze (curation_fingerprint) is that of Study 1 plus the files of Study 2.
"""
from __future__ import annotations

import hashlib
import importlib
import os

from athena import pipeline as P1

from .packs import S2_PACKS

VERSION = P1.VERSION + "+s2"
CURATION_FILES = P1.CURATION_FILES + ("facts.py", "facets_s2.py", "kind_infer_s2.py")
_mods: dict = {}
_cache: dict = {}


def _load():
    P1._load()                                  # the Study 1 modules, and the curation folder on sys.path
    with P1._lock:
        if "kind_infer_s2" not in _mods:
            d = P1.curation_dir()
            if not os.path.exists(os.path.join(d, "kind_infer_s2.py")):
                raise P1.PipelineError(f"kind_infer_s2.py not found in {d} (set ${P1.CURATION_ENV} to the curation folder)")
            try:
                _mods["kind_infer_s2"] = importlib.import_module("kind_infer_s2")
            except Exception as e:
                raise P1.PipelineError(f"cannot load kind_infer_s2 from {d}: {type(e).__name__}: {e}") from e
        return _mods["kind_infer_s2"]


def check_pack(pack) -> None:
    if pack.id not in S2_PACKS:
        raise P1.PipelineError(f"the Study 2 inference needs a Study 2 pack ({', '.join(S2_PACKS)}), not {pack.id!r}")
    _load()


def curation_fingerprint() -> dict:
    """As athena.pipeline.curation_fingerprint, over the Study 1 files and the Study 2 files."""
    d = P1.curation_dir()
    out = {}
    for f in CURATION_FILES:
        p = os.path.join(d, f)
        if os.path.exists(p):
            with open(p, "rb") as fh:
                b = fh.read()
            out[f] = hashlib.sha256(b.replace(b"\r\n", b"\n") if f.endswith(".py") else b).hexdigest()
        else:
            out[f] = None
    out["ALL"] = hashlib.sha256(repr(sorted(out.items())).encode()).hexdigest()
    return out


def infer(language: str, code: str, name: str) -> dict:
    """Study 2 kind of `name` in `code`, from the code alone (same record as athena.pipeline.infer, plus the Study 1
    kind and the facets). Never raises for a code problem."""
    key = (language, code, name)
    with P1._lock:
        if key in _cache:
            return _cache[key]
        ki = _load()
        try:
            r = ki.infer_kind_s2(language, code, name)
            facts = r.detail.get("facts") or [{}]
            out = {"kind": r.kind, "status": r.status, "reason": r.reason,
                   "alt_kinds": list(r.detail.get("alt_kinds", [])), "kind_s1": r.detail.get("kind_s1", r.kind),
                   "facets": {k: v for k, v in facts[0].items() if k not in ("kind", "kind_s1")}}
        except ValueError as e:
            out = {"kind": None, "status": "error", "reason": str(e), "alt_kinds": [], "kind_s1": None, "facets": {}}
        if len(_cache) > 50000:
            _cache.clear()
        _cache[key] = out
        return out


def oracle_free_kind(task, unit, pack=None) -> tuple:
    """athena.runner.oracle_free_kind with the Study 2 inference; the record also holds the Study 1 kind and the
    inferred facets."""
    from athena.runner import unit_inputs
    name, code = unit_inputs(task, unit)
    inf = infer(unit.language, code, name)
    fields = {"kind_used": P1.kind_for_prompt(inf), "kind_inferred": inf["kind"],
              "kind_status": inf["status"], "kind_alt": inf["alt_kinds"], "kind_ok": inf["kind"] == unit.kind,
              "kind_inferred_s1": inf["kind_s1"], "facets_inferred": inf["facets"]}
    if pack is not None:
        onto = getattr(pack, "rules_ontology", pack.ontology)
        fields["kind_in_pack"] = (inf["kind"] in onto.kinds) if inf["kind"] else None
    return P1.kind_for_prompt(inf), fields
