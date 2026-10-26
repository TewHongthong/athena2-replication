"""Athena Vol. 2 pipeline without the Vol. 1 oracles (athena2 v0.1).

Vol. 1 handed the retriever the identifier kind from the benchmark's metadata, and graded a proposed name only
against the rules and the original name.  Here the pipeline works from what a developer's editor has:

    code + the violating name
      -> identifier kind inferred from the code alone            (curation/kind_infer.py)
      -> standard text retrieved for that kind                   (none | fulldoc | chunk | bm25 | graph)
      -> prompt -> model -> parsed suggestion
      -> mechanical rule check of the suggestion                 (kinds from the inference, not from metadata)
      -> scope-aware check of the rename in the snippet          (curation/scope_check.py)

`propose_rename` runs this for one request.  The experiment runner uses `infer` and `scope` for the same two steps
when it is started with --no-oracle, so a request and an experiment trial see the same prompt for the same code.

The two curation modules are loaded from the curation folder of this repository (`../athena-corpus/curation`, or
$ATHENA_CURATION).  They are kept out of the pack's corpus folder on purpose: the Vol. 1 corpus predates them.

Limits (v0.1): only the primary inferred kind is used (alternatives are recorded, not used); when the kind cannot
be inferred the prompt says "identifier" and the graph condition retrieves nothing specific; a rejected suggestion
is reported, not retried; the scope check covers C++, C# and Python.
"""
from __future__ import annotations

import hashlib
import importlib
import os
import re
import sys
import threading
from dataclasses import asdict, dataclass, field
from typing import Optional

VERSION = "0.1"
UNKNOWN_KIND = "identifier"          # word used in the prompt when no kind could be inferred
SCOPE_LANGUAGES = ("cpp", "csharp", "python")
CURATION_ENV = "ATHENA_CURATION"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # .../athena-sim
_IDENT = re.compile(r"^[^\W\d][\w$]*$")

# curation files that decide the inferred kind and the scope verdict; hashed into a freeze when --no-oracle is used
CURATION_FILES = ("kind_infer.py", "scope_check.py", "scope_common.py", "scope_py.py", "scope_ts.py",
                  "lang_python.py", "lang_ts.py", "tsbind.py", "libtsall.so")


class PipelineError(RuntimeError):
    """The no-oracle pipeline cannot run in this setup (missing curation folder, unsupported pack ...)."""


def curation_dir() -> str:
    return os.path.normpath(os.environ.get(CURATION_ENV) or os.path.join(ROOT, "..", "athena-corpus", "curation"))


_lock = threading.RLock()            # tree-sitter parsers are shared by the curation modules
_mods: dict = {}


def _load() -> tuple:
    with _lock:
        if not _mods:
            d = curation_dir()
            for f in ("kind_infer.py", "scope_check.py"):
                if not os.path.exists(os.path.join(d, f)):
                    raise PipelineError(f"{f} not found in {d} (set ${CURATION_ENV} to the curation folder)")
            if d not in sys.path:
                sys.path.insert(0, d)
            try:
                _mods["kind_infer"] = importlib.import_module("kind_infer")
                _mods["scope_check"] = importlib.import_module("scope_check")
            except Exception as e:           # e.g. libtsall.so built for another platform
                raise PipelineError(f"cannot load the curation modules from {d}: {type(e).__name__}: {e}") from e
        return _mods["kind_infer"], _mods["scope_check"]


NO_ORACLE_PACKS = ("public5", "godot", "dotnet-runtime", "odoo")


def check_pack(pack) -> None:
    """The kind vocabulary of the inference is the one of the public5 ontology; a pack with another vocabulary
    (gscs: procedure, boolean_variable ...) cannot be driven without its oracle kind.

    The three Vol. 2 packs are accepted although their ontologies are not the public5 one: their kind ids are
    largely the same words, and each trial records `kind_in_pack` (whether the inferred kind is one of the kinds of
    the ontology that supplies the rules), so a kind outside the pack's vocabulary is visible, not blocked."""
    if pack.id not in NO_ORACLE_PACKS:
        raise PipelineError(f"--no-oracle needs a pack whose identifier kinds the inference can produce; "
                            f"pack {pack.id!r} is not one of them (use {', '.join(NO_ORACLE_PACKS)})")
    _load()


def curation_fingerprint() -> dict:
    d = curation_dir()
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


# ---------------------------------------------------------------------------------------------- the two steps
_infer_cache: dict = {}


def infer(language: str, code: str, name: str) -> dict:
    """Identifier kind of `name` in `code`, from the code alone.  Never raises for a code problem."""
    key = (language, code, name)
    with _lock:
        if key in _infer_cache:
            return _infer_cache[key]
        ki, _ = _load()
        try:
            r = ki.infer_kind(language, code, name)
            out = {"kind": r.kind, "status": r.status, "reason": r.reason,
                   "alt_kinds": list(r.detail.get("alt_kinds", []))}
        except ValueError as e:               # unsupported language, reserved probe name in the code
            out = {"kind": None, "status": "error", "reason": str(e), "alt_kinds": []}
        if len(_infer_cache) > 50000:
            _infer_cache.clear()
        _infer_cache[key] = out
        return out


def kind_for_prompt(inferred: dict) -> str:
    return inferred.get("kind") or UNKNOWN_KIND


def scope(language: str, code: str, injected: str, suggested: Optional[str]) -> Optional[dict]:
    """Scope-aware verdict on renaming `injected` to `suggested` in `code`.

    Returns None when there is nothing to check (no valid suggestion).  `verdict` is one of
      ok            no binding and no declaration conflict
      conflict      the rename would change a binding or clash with a declaration
      unchecked     the checker does not cover this language, or the snippet does not parse
      no_change     the suggestion is the violating name itself (nothing is renamed)
      no_occurrence the violating name is not in the snippet
    """
    if not suggested or not _IDENT.match(suggested):
        return None
    if suggested == injected:
        return {"verdict": "no_change"}
    if language not in SCOPE_LANGUAGES:
        return {"verdict": "unchecked", "reason": f"no scope checker for {language}"}
    with _lock:
        _, sc = _load()
        try:
            r = sc.check_rename(language, code, injected, suggested)
        except Exception as e:                # a checker bug must be visible, but must not lose the trial
            return {"verdict": "unchecked", "reason": f"checker error: {type(e).__name__}: {e}"}
    if r["status"] == "unsupported":
        return {"verdict": "unchecked", "reason": r.get("unsupported_reason", "unsupported"),
                "scope_blind": r["scope_blind"]}
    if r["status"] == "no_occurrence":
        return {"verdict": "no_occurrence", "scope_blind": r["scope_blind"]}
    bad = r["binding_conflict"] or r["declaration_conflict"]
    return {"verdict": "conflict" if bad else "ok", "reasons": r["binding_reasons"] + r["declaration_reasons"],
            "binding_conflict": r["binding_conflict"], "declaration_conflict": r["declaration_conflict"],
            "scope_blind": r["scope_blind"], "occurrences": r["occurrences_renamed"]}


# ---------------------------------------------------------------------------------------------- one request
@dataclass
class Proposal:
    status: str                       # accepted | rejected | unchecked | no_change | no_proposal
    reason: str
    language: str
    name: str
    suggested: Optional[str]
    kind: str                         # kind used in the prompt
    kind_inferred: dict
    standard_id: str
    condition: str
    retrieval: dict = field(default_factory=dict)
    rules_failed: list = field(default_factory=list)
    scope: Optional[dict] = None
    rule_ids_applied: list = field(default_factory=list)
    reasoning: str = ""
    prompt: str = ""
    raw_response: str = ""
    model: str = ""
    usage: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def standard_for(pack, language: str) -> str:
    ids = pack.ontology.standards_for_language(language)
    if len(ids) != 1:
        raise PipelineError(f"{len(ids)} standards in pack {pack.id!r} cover {language!r} ({', '.join(ids) or 'none'}); "
                            f"pass the standard explicitly")
    return ids[0]


def propose_rename(pack, retriever, backend, *, language: str, code: str, name: str, standard_id: Optional[str] = None,
                   condition: str = "graph") -> Proposal:
    """Suggest a compliant name for `name` in `code` and check it.  `backend` must be a real model backend."""
    from .evaluate import name_for_check, parse_completion
    from .prompts import build_prompt
    from output_validator import check_naming_compliance

    if not getattr(backend, "is_llm", False) or backend.spec.startswith("replay:"):
        raise PipelineError("propose_rename needs a model backend (openai:<model> or gemini:<model>); "
                            "mock and replay backends answer from benchmark ground truth")
    if not re.search(r"(?<![\w$])" + re.escape(name) + r"(?![\w$])", code):
        raise PipelineError(f"`{name}` does not occur in the code")
    sid = standard_id or standard_for(pack, language)
    inferred = infer(language, code, name)
    kind = kind_for_prompt(inferred)
    ctx = retriever.context(condition, task="rename", standard_id=sid, language=language, kind=kind, name=name, code=code)
    prompt = build_prompt("rename", language=language, kind=kind, name=name, code=code, context=ctx.text)
    comp = backend.complete(prompt, {"unit": None, "pack": pack, "task": "rename", "condition": condition, "repeat": 0})
    parsed = parse_completion("rename", comp.text)
    base = dict(language=language, name=name, kind=kind, kind_inferred=inferred, standard_id=sid, condition=condition,
                retrieval=dict(ctx.meta), prompt=prompt, raw_response=comp.text, model=comp.model,
                usage={"prompt_tokens": comp.prompt_tokens, "completion_tokens": comp.completion_tokens,
                       "latency_s": round(comp.latency_s, 3)})
    suggested = None
    if parsed.ok and isinstance(parsed.data.get("suggested_name"), str):
        suggested = parsed.data["suggested_name"].strip().strip("`")
    if not suggested or not _IDENT.match(suggested):
        return Proposal(status="no_proposal", reason="the answer has no valid identifier" if parsed.ok
                        else "the answer could not be parsed: " + "; ".join(parsed.errors)[:200],
                        suggested=suggested, **base)
    data = parsed.data
    extra = dict(rule_ids_applied=list(data.get("rule_ids_applied") or []), reasoning=str(data.get("reasoning") or ""))
    if suggested == name:
        return Proposal(status="no_change", reason="the model kept the name", suggested=suggested, **extra, **base)
    chk = name_for_check(language, suggested)
    failed = [rid for rid in pack.core_rules(language, kind)
              if not check_naming_compliance(chk, pack.ontology.rule(rid))[0]]
    sc = scope(language, code, name, suggested)
    if sc and sc["verdict"] == "conflict":
        status, reason = "rejected", "scope check: " + "; ".join(sc.get("reasons") or ["conflict"])
    elif failed:
        status, reason = "rejected", "the name breaks " + ", ".join(failed)
    elif sc and sc["verdict"] == "ok":
        status, reason = "accepted", "no rule and no scope conflict found"
    else:
        status, reason = "unchecked", "rules pass; scope check not available: " + str((sc or {}).get("reason", "no result"))
    return Proposal(status=status, reason=reason, suggested=suggested, rules_failed=failed, scope=sc, **extra, **base)
