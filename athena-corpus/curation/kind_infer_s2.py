#!/usr/bin/env python3
"""Study 2 identifier kinds inferred from the code alone (the infer family of HYPOTHESES_v2_study2).

    infer_kind_s2(language, code, name) -> kind_infer.KindResult

The Study 1 inference (kind_infer.infer_kind, unchanged) chooses the parse of the snippet: the name is replaced by a
neutral probe and the snippet is parsed as it is or inside a synthetic class. The same text is then given to
facets_s2.extract_s2, and the kind of the probe's declaration is its inferred Study 2 kind
(extra["kind_infer"]), read from the syntax only:

  Godot (cpp)     a parameter of a function defined under a qualified name (A::f) or declared in a class body is
                  a method parameter: output_parameter for a reference or a pointer to a type that is not const,
                  input_parameter otherwise. A parameter of an unqualified function outside a class is a parameter
                  of a free function (kind parameter), also when the snippet is a method cut out of its class.
  dotnet (csharp) fields by accessibility, static, const and the ThreadStatic attribute (packs/*-s2/KINDS.md).
  Any other declaration keeps its Study 1 kind.

The result carries the Study 1 kind in detail["kind_s1"] and the Study 2 facets in detail["facts"].
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import facets_s2  # noqa: E402
import kind_infer as KI  # noqa: E402

S2_LANGUAGES = ("cpp", "csharp")


def infer_kind_s2(language: str, code: str, name: str) -> KI.KindResult:
    """Study 2 kind of the identifier `name` declared in `code`, from the code alone."""
    r = KI.infer_kind(language, code, name)
    if language not in S2_LANGUAGES or r.status in (KI.NOT_FOUND, KI.PARSE_FAILED) or "attempt" not in r.detail:
        return r
    neutral = KI._word_re(name).sub(KI.PROBE, code)
    text = dict(KI._attempts(language, neutral))[r.detail["attempt"]]
    ff = facets_s2.extract_s2(language, "snippet." + language, text.encode("utf-8"), KI._ts())
    decls = sorted((d for d in ff.decls if d.name == KI.PROBE), key=lambda d: d.start)
    kinds = [d.extra["kind_infer"] for d in decls if d.extra["kind_infer"] is not None]
    detail = dict(r.detail)
    detail["kind_s1"] = r.kind
    detail["facts"] = [{"kind": d.extra["kind_infer"], "kind_s1": d.extra["kind_s1"], **d.extra.get("s2", {})}
                       for d in decls]
    if not kinds:
        return KI.KindResult(None, KI.UNMODELLED, r.reason, detail)
    k = kinds[0]
    if k != r.kind:
        detail.pop("alt_kinds", None)          # the Study 1 alternatives are about the Study 1 kind
    if len(set(kinds)) > 1:
        detail["candidates"] = kinds
        return KI.KindResult(k, KI.AMBIGUOUS, "several declarations of the name with different kinds", detail)
    return KI.KindResult(k, KI.OK if r.status in (KI.OK, KI.AMBIGUOUS) else r.status,
                         "from the declaration's syntax", detail)
