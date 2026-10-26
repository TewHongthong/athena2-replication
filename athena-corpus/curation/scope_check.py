#!/usr/bin/env python3
"""Scope-aware check of a proposed rename (Athena Vol. 2, WP3 task 3.2).

    check_rename(language, code, injected, suggested) -> dict

`code` is a snippet that contains the violating name `injected`; `suggested` is the name a model proposes for it.
The rename is applied the way the benchmark applies it (every whole-word occurrence of `injected` is replaced),
and three things are reported:

  scope_blind          the suggested name already occurs in the snippet as a word (the Vol. 1 collision screen)
  binding_conflict     check 2: some occurrence is bound to a different declaration after the rename than
                       before (a capture, a merge of two declarations, a split, or an unparsable result)
  declaration_conflict check 3 (IDE style): the suggested name is declared in the same, an enclosing or a nested
                       scope of the renamed declaration, is a name used from outside the snippet within that
                       scope, or is a reserved word

Front ends (syntax only; nothing is compiled and no headers or assemblies are read):
  cpp, csharp   tree-sitter parse tree (`scope_ts.py`)
  python        stdlib `ast` + `symtable` (`scope_py.py`)

Limits: names are bound by nesting and declaration order, not by type, so two members of different classes with
the same name are one entity, and an overload or a name that depends on a header is not resolved.  A snippet that
does not parse is reported as "unsupported" rather than as a conflict.  Check 2 can only be as good as the
resolver; the hand-written controls in `tests_scope/` state what is and is not expected to be caught.
"""
from __future__ import annotations

import argparse
import json
import keyword
import sys

import scope_py
import scope_ts
from scope_common import IDENTITY, OffsetMap, apply_rename, compare, word_re

LANGUAGES = ("cpp", "csharp", "python")
_ANALYSE = {"cpp": scope_ts.analyse_cpp, "csharp": scope_ts.analyse_csharp, "python": scope_py.analyse}
_KEYWORDS = {"cpp": scope_ts.CPP_KEYWORDS, "csharp": scope_ts.CS_KEYWORDS}


def _tree_declaration_conflicts(language, info, injected, suggested):
    reasons = []
    if suggested in _KEYWORDS[language]:
        reasons.append("reserved word")
    renamed = [d for d in info["decls"] if d["name"] == injected]
    others = [d for d in info["decls"] if d["name"] == suggested]
    for r in renamed:
        rs = r["scope"]
        for d in others:
            ds = d["scope"]
            if rs == ds:
                reasons.append(f"{suggested} declared in the same scope ({d['kind']})")
            elif rs[:len(ds)] == ds:
                reasons.append(f"{suggested} declared in an enclosing scope ({d['kind']})")
            elif ds[:len(rs)] == rs:
                reasons.append(f"{suggested} declared in a nested scope ({d['kind']})")
        for u in info["ext_uses"]:
            if u["name"] == suggested and u["scope"][:len(rs)] == rs:
                reasons.append(f"external name {suggested} used in the scope")
    return sorted(set(reasons))


def is_reserved(language, name):
    if language == "python":
        return keyword.iskeyword(name) or name in ("self", "cls")
    return name in _KEYWORDS[language]


def declaration_conflicts(language, info, injected, suggested):
    if language == "python":
        return scope_py.declaration_conflicts(info, injected, suggested)
    return _tree_declaration_conflicts(language, info, injected, suggested)


_VAR_KINDS = {"cpp": {"VarDecl", "ParmVarDecl"}, "csharp": {"LocalVar", "Parameter"}}


def redeclaration_reasons(language, info, name):
    """Declarations of `name` that the language rejects once the rename has introduced the name.

    C++: two variables or parameters of the same scope (an inner scope may shadow an outer one).
    C#:  a local or parameter named like another local or parameter of the same or an enclosing scope of the same
         member (CS0128, CS0136); this is stricter than C++ and is a compile error, not a change of meaning.
    Python rebinds freely, so nothing is reported for it.
    """
    kinds = _VAR_KINDS.get(language)
    if not kinds:
        return []
    ds = [d for d in info["decls"] if d["name"] == name and d["kind"] in kinds]
    reasons = []
    for i, a in enumerate(ds):
        for b in ds[i + 1:]:
            pa, pb = a["scope"], b["scope"]
            if pa == pb:
                reasons.append(f"{name} declared twice in one scope")
            elif language == "csharp":
                short, long_ = (pa, pb) if len(pa) < len(pb) else (pb, pa)
                if long_[:len(short)] == short and not any(k == "class" for k, _ in long_[len(short):]):
                    reasons.append(f"{name} redeclared in a nested scope of the same member (C#)")
    return sorted(set(reasons))


def analyse(language, code, omap=IDENTITY):
    if language not in _ANALYSE:
        raise ValueError(f"unsupported language {language!r}; choose from {LANGUAGES}")
    return _ANALYSE[language](code, omap)


def check_rename(language: str, code: str, injected: str, suggested: str) -> dict:
    out = {"language": language, "injected": injected, "suggested": suggested, "status": "ok",
           "scope_blind": suggested != injected and bool(word_re(suggested).search(code)),
           "binding_conflict": False, "binding_reasons": [],
           "declaration_conflict": False, "declaration_reasons": [], "occurrences_renamed": 0}
    before = analyse(language, code, IDENTITY)
    if before["errors"]:
        out.update(status="unsupported", unsupported_reason="; ".join(before["errors"])[:200])
        return out
    after_code, n = apply_rename(code, injected, suggested)
    out["occurrences_renamed"] = n
    if n == 0:
        out["status"] = "no_occurrence"
        return out
    after = analyse(language, after_code, OffsetMap(code, injected, suggested))
    reasons = []
    if is_reserved(language, suggested):
        reasons.append("reserved word")
    if after["errors"]:
        reasons.append("front-end error after the rename: " + "; ".join(after["errors"])[:200])
    else:
        _, why = compare(before["occ"], after["occ"])
        reasons += why
        reasons += redeclaration_reasons(language, after, suggested)
    out["binding_conflict"], out["binding_reasons"] = bool(reasons), reasons
    d3 = declaration_conflicts(language, before, injected, suggested)
    out["declaration_conflict"], out["declaration_reasons"] = bool(d3), d3
    if before.get("unsupported"):
        out["unsupported_constructs"] = sorted(set(before["unsupported"]))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Scope-aware check of a proposed rename")
    ap.add_argument("file")
    ap.add_argument("--language", required=True, choices=LANGUAGES)
    ap.add_argument("--injected", required=True, help="name in the snippet that is renamed")
    ap.add_argument("--suggested", required=True, help="proposed new name")
    a = ap.parse_args(argv)
    with open(a.file, encoding="utf-8") as f:
        code = f.read()
    json.dump(check_rename(a.language, code, a.injected, a.suggested), sys.stdout, indent=1)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
