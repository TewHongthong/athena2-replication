#!/usr/bin/env python3
"""Study 2 identifier kinds and facets (HYPOTHESES_v2_study2; packs godot-s2 and dotnet-runtime-s2).

`extract_s2` runs the Study 1 extractor (`lang_ts.extract`, unchanged), parses the file again and adds the facets
that the Study 2 kinds need. No Study 1 file is modified, so the frozen runs of Study 1 still verify.

Every declaration carries two kinds:
  kind                  the kind from metadata (the label of the benchmark)
  extra["kind_infer"]   the kind inferred from the code
They differ only for Godot method parameters. extra["kind_s1"] keeps the Study 1 kind, extra["s2"] the facets.

Godot (cpp), parameters (packs/godot-s2/KINDS.md)
  owner          "method": the function is declared in a class, struct or union, or is defined out of class under a
                 qualified name (A::f, as in the Study 1 unit labels); "function": any other declared function
  owner_via      "class_body", "qualified" or "namespace": how the owner was decided
  prefix         "p_", "r_" or None: the start of the name in the original code
  indirection    "lref", "rref", "ptr", "array", "func" or None: the declarator closest to the name
                 (an array or function parameter is adjusted to a pointer, as in C++)
  pointee_const  for an indirection: whether the type it refers to is const (a function type is not const)
  out_by_type    an indirection to a type that is not const
  metadata kind  method: p_ -> input_parameter, r_ -> output_parameter, otherwise parameter; function: parameter
  inferred kind  method: output_parameter if out_by_type, otherwise input_parameter; function: parameter
  Lambda parameters, and parameters of declarations inside a function body, keep their Study 1 kind.

dotnet-runtime (csharp), fields (packs/dotnet-runtime-s2/KINDS.md)
  access         "public", "protected", "protected internal", "private protected", "internal" or "private"
                 (a field without an access modifier is private)
  static, const, threadstatic (the attribute ThreadStatic or ThreadStaticAttribute, also when qualified)
  kind           const -> constant; public -> public_field; protected, protected internal, private protected ->
                 field; private or internal: static with ThreadStatic -> threadstatic_field, static -> static_field,
                 otherwise instance_field. The type of the field does not matter.
  The kind is read from the syntax, so the metadata kind and the inferred kind are the same.

Units (FileFacts.units_s2; `qualifying_units` applies the criteria)
  Godot          the units of Study 1 (functions and methods), 6 to 40 lines; ff.units_s2 is ff.units, so the unit
                 index is the Study 1 index
  dotnet-runtime every class or struct declaration, nested ones included (a record is not a unit), 6 to 60 lines
  A unit qualifies when it does not overlap a parse error and holds a declaration of a Study 2 kind, that is a kind
  that can be an injection target: input_parameter, output_parameter (Godot); instance_field, static_field,
  threadstatic_field (dotnet-runtime).

  python3 facets_s2.py --corpus ../corpus_v2 --language cpp       counts of the kinds and of the agreement
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import lang_ts  # noqa: E402
from facts import UnitCand, line_of  # noqa: E402

GODOT_PREFIX_KIND = {"p_": "input_parameter", "r_": "output_parameter"}
CPP_PARAM_NODES = {"parameter_declaration", "optional_parameter_declaration", "variadic_parameter_declaration"}
_CPP_DECL_NODES = {"declaration", "field_declaration", "function_definition"}
_CPP_RETURN_WRAPPERS = {"pointer_declarator", "reference_declarator", "parenthesized_declarator",
                        "attributed_declarator"}
_CPP_NAME_WRAPPERS = {"parenthesized_declarator", "attributed_declarator", "variadic_declarator"}
_CPP_NAMESPACE_SCOPES = {"translation_unit", "declaration_list", "linkage_specification"}
_CS_THREADSTATIC = {"ThreadStatic", "ThreadStaticAttribute"}
S2_FIELD_KINDS = ("instance_field", "static_field", "threadstatic_field", "public_field", "field", "constant")
S2_KINDS = {"cpp": ("input_parameter", "output_parameter"),
            "csharp": ("instance_field", "static_field", "threadstatic_field")}
UNIT_LINES = {"cpp": (6, 40), "csharp": (6, 60)}
CS_UNIT_TYPES = {"class_declaration": "class", "struct_declaration": "struct"}


def _text(src: bytes, n) -> str:
    return src[n.start:n.end].decode("utf-8", errors="replace")


# ----------------------------------------------------------------------------------------------- Godot (C++)
def cpp_owner(fd):
    """(owner, owner_via) of the function declared by function_declarator `fd`; (None, None) when `fd` does not
    declare a function whose parameters Study 2 classifies (a pointer to function, a function type inside a
    parameter, a declaration inside a function body, a friend declaration)."""
    inner = fd.child("declarator")
    if inner is None or inner.type == "parenthesized_declarator":
        return None, None
    d = fd.parent
    while d is not None and d.type in _CPP_RETURN_WRAPPERS:      # Foo *A::f(...), Foo &f(...)
        d = d.parent
    if d is None or d.type not in _CPP_DECL_NODES:
        return None, None
    p = d.parent
    while p is not None and (p.type == "template_declaration" or p.type.startswith("preproc_")):
        p = p.parent
    if p is not None and p.type == "field_declaration_list":
        return "method", "class_body"
    if p is None or p.type in _CPP_NAMESPACE_SCOPES:
        if inner.type == "qualified_identifier":
            return "method", "qualified"
        return "function", "namespace"
    return None, None


def cpp_param_type(src: bytes, pd):
    """(name node, indirection, pointee_const) of a parameter declaration; name node None when it has no name.

    The declarators are read from the type side to the name side; the one closest to the name is the outermost
    type constructor of the parameter, and the type it refers to is made by the declarators before it."""
    layers = []                       # (constructor, const) from the type side to the name side
    d = pd.child("declarator")
    name = None
    while d is not None and not d.is_error and not d.is_missing:
        t = d.type
        if t == "pointer_declarator":
            layers.append(("ptr", any(c.type == "type_qualifier" and _text(src, c) == "const" for c in d.children)))
            d = d.child("declarator")
        elif t == "reference_declarator":
            layers.append(("rref" if d.children and d.children[0].type == "&&" else "lref", False))
            d = next((c for c in reversed(d.children) if c.named), None)
        elif t == "array_declarator":
            layers.append(("array", None))
            d = d.child("declarator")
        elif t == "function_declarator":
            layers.append(("func", False))
            d = d.child("declarator")
        elif t in _CPP_NAME_WRAPPERS:
            d = next((c for c in reversed(d.children) if c.named), None)
        elif t in ("identifier", "field_identifier"):
            name = d
            break
        else:
            break
    if not layers:
        return name, None, None
    base_const = any(c.type == "type_qualifier" and _text(src, c) == "const" for c in pd.children)

    def const_of(i):                  # is the type made by layers[0..i] const
        if i < 0:
            return base_const
        kind, q = layers[i]
        if kind == "array":           # an array of const T is const
            return const_of(i - 1)
        return bool(q)

    return name, layers[-1][0], const_of(len(layers) - 2)


def godot_param_kinds(owner, name: str, out_by_type: bool):
    """(metadata kind, inferred kind) of a parameter."""
    if owner != "method":
        return "parameter", "parameter"
    meta = GODOT_PREFIX_KIND.get(name[:2], "parameter")
    return meta, ("output_parameter" if out_by_type else "input_parameter")


def _cpp_s2(root, src: bytes, by_start: dict, diag: collections.Counter):
    for fd in root.walk():
        if fd.type != "function_declarator":
            continue
        plist = fd.child("parameters")
        if plist is None:
            continue
        owner, via = cpp_owner(fd)
        for pd in plist.children:
            if pd.type not in CPP_PARAM_NODES:
                continue
            name, ind, pconst = cpp_param_type(src, pd)
            if name is None:
                continue
            d = by_start.get(name.start)
            if d is None or d.kind != "parameter":
                diag["param_without_decl"] += 1
                continue
            if d.exempt or owner is None:
                diag["param_kept_s1" if owner is None else "param_exempt"] += 1
                continue
            out = ind is not None and not pconst
            meta, inf = godot_param_kinds(owner, d.name, out)
            d.kind = meta
            d.extra["kind_infer"] = inf
            d.extra["s2"] = {"owner": owner, "owner_via": via,
                             "prefix": d.name[:2] if d.name[:2] in GODOT_PREFIX_KIND else None,
                             "indirection": ind, "pointee_const": pconst, "out_by_type": out}
            if via == "qualified":
                q = fd.child("declarator")
                scope = q.child("scope")
                last = _text(src, scope).split("<")[0].split("::")[-1] if scope is not None else ""
                if last[:1].islower():
                    diag["qualified_scope_lowercase"] += 1


# ----------------------------------------------------------------------------------------------- dotnet (C#)
def cs_access(words) -> str:
    w = set(words)
    if "public" in w:
        return "public"
    if "protected" in w and "internal" in w:
        return "protected internal"
    if "protected" in w and "private" in w:
        return "private protected"
    if "protected" in w:
        return "protected"
    if "internal" in w:
        return "internal"
    return "private"


def cs_attribute_names(src: bytes, n) -> set:
    """Last simple name of every attribute attached to declaration `n` (System.ThreadStatic -> ThreadStatic)."""
    out = set()
    for al in n.children:
        if al.type != "attribute_list":
            continue
        for a in al.children:
            if a.type != "attribute":
                continue
            nm = a.child("name")
            while nm is not None and nm.type in ("qualified_name", "alias_qualified_name") and nm.child("name") is not None:
                nm = nm.child("name")
            if nm is not None:
                out.add(_text(src, nm))
    return out


def cs_field_kind(access: str, static: bool, const: bool, threadstatic: bool) -> str:
    if const:
        return "constant"
    if access == "public":
        return "public_field"
    if access in ("private", "internal"):
        if static and threadstatic:
            return "threadstatic_field"
        return "static_field" if static else "instance_field"
    return "field"


def _cs_s2(root, src: bytes, by_start: dict, diag: collections.Counter):
    for n in root.walk():
        if n.type != "field_declaration":
            continue
        words = lang_ts._mod_words(n, src)
        facets = {"access": cs_access(words), "static": "static" in words, "const": "const" in words,
                  "threadstatic": bool(cs_attribute_names(src, n) & _CS_THREADSTATIC)}
        kind = cs_field_kind(**facets)
        vd = next((c for c in n.children if c.type == "variable_declaration"), None)
        if vd is None:
            continue
        for v in vd.children:
            if v.type != "variable_declarator" or v.child("name") is None:
                continue
            d = by_start.get(v.child("name").start)
            if d is None:
                diag["field_without_decl"] += 1
                continue
            d.kind = kind
            d.extra["kind_infer"] = kind
            d.extra["s2"] = dict(facets)
            if d.exempt == "nonpublic_field":     # Study 1 left these out; Study 2 has kinds for them
                d.exempt = None


# ----------------------------------------------------------------------------------------------- units
def cs_type_units(root, src: bytes, line_starts) -> list:
    """One unit per class or struct declaration, in source order; top_level is False for a nested type."""
    units = []
    for n in root.walk():
        if n.type not in CS_UNIT_TYPES:
            continue
        a, nested = n.parent, False
        while a is not None:
            if a.type in lang_ts._CS_TYPE_DECLS:
                nested = True
                break
            a = a.parent
        nm = n.child("name")
        units.append(UnitCand(line_of(line_starts, n.start), line_of(line_starts, max(n.end - 1, n.start)),
                              f"{CS_UNIT_TYPES[n.type]} {_text(src, nm) if nm is not None else '?'}", not nested))
    return units


def qualifying_units(lang: str, ff) -> list:
    """(unit index, unit, reason) for every unit of ff.units_s2; reason is None when the unit qualifies, otherwise
    too_short, too_long, parse_error_in_unit or no_s2_kind (checked in this order)."""
    from curate import unit_range
    lo, hi = UNIT_LINES[lang]
    out = []
    for i, u in enumerate(ff.units_s2):
        n = u.end_line - u.start_line + 1
        reason = None
        if n < lo:
            reason = "too_short"
        elif n > hi:
            reason = "too_long"
        else:
            u_start, u_end = unit_range(ff, u)
            if any(a < u_end and b > u_start for a, b in ff.error_spans):
                reason = "parse_error_in_unit"
            elif not any(u_start <= d.start < u_end and not d.exempt and d.kind in S2_KINDS[lang] for d in ff.decls):
                reason = "no_s2_kind"
        out.append((i, u, reason))
    return out


# ----------------------------------------------------------------------------------------------- entry point
def extract_s2(lang: str, path: str, content: bytes, ts, diag: collections.Counter | None = None):
    """FileFacts of the Study 1 extractor with the Study 2 kinds and facets (see the module docstring)."""
    ff = lang_ts.extract(lang, path, content, ts)
    for d in ff.decls:
        d.extra["kind_s1"] = d.kind
        d.extra["kind_infer"] = d.kind
    ff.units_s2 = list(ff.units)
    if lang not in ("cpp", "csharp"):
        return ff
    diag = diag if diag is not None else collections.Counter()
    root, _ = ts.parse(lang_ts.grammar_for(lang, path), content)
    by_start = {d.start: d for d in ff.decls}
    (_cpp_s2 if lang == "cpp" else _cs_s2)(root, content, by_start, diag)
    if lang == "csharp":
        ff.units_s2 = cs_type_units(root, content, ff.line_starts)
    return ff


def census(corpus: str, language: str, lib: str | None = None) -> dict:
    """Counts of the Study 2 kinds over the corpus files of one language (no LLM, deterministic)."""
    from curate import load_index, parse_corpus_md
    from tsbind import TreeSitter, find_library
    ts = TreeSitter(find_library(lib))
    files = sorted(md for (lang, md) in load_index(corpus) if lang == language)
    diag = collections.Counter()
    kinds, agree, facets = collections.Counter(), collections.Counter(), collections.Counter()
    units, overlap = collections.Counter(), 0
    n_err = 0
    for md in files:
        _, content = parse_corpus_md(os.path.join(corpus, "corpus", language, md))
        if content is None:
            diag["file_without_code"] += 1
            continue
        ff = extract_s2(language, md[:-3] if md.endswith(".md") else md, content, ts, diag)
        n_err += bool(ff.error_spans)
        q = []
        for _, u, reason in qualifying_units(language, ff):
            units[reason or "qualifies"] += 1
            if reason is None:
                units[f"qualifies {u.label.split()[0]} {'top' if u.top_level else 'nested'}"] += 1
                q.append(u)
        overlap += sum(1 for a in q for b in q if a is not b and a.start_line <= b.start_line and b.end_line <= a.end_line)
        for d in ff.decls:
            s2 = d.extra.get("s2")
            if s2 is None:
                continue
            kinds[d.kind] += 1
            if language == "cpp" and s2["owner"] == "method":
                agree[f"{d.kind} -> {d.extra['kind_infer']}"] += 1
                if s2["prefix"]:
                    facets[f"{s2['prefix']} {s2['indirection'] or 'value'} const={s2['pointee_const']}"] += 1
            elif language == "csharp":
                facets[f"{s2['access']} static={s2['static']} const={s2['const']} ts={s2['threadstatic']}"] += 1
    out = {"language": language, "files": len(files), "files_with_parse_errors": n_err,
           "units": dict(sorted(units.items())), "qualifying_units_inside_another": overlap, "kinds": dict(kinds),
           "facets": dict(facets.most_common()), "diagnostics": dict(diag)}
    if language == "cpp":
        out["metadata_to_inferred"] = dict(agree.most_common())
        pre = {k: v for k, v in agree.items() if not k.startswith("parameter ")}
        same = sum(v for k, v in pre.items() if k.split(" -> ")[0] == k.split(" -> ")[1])
        out["agreement_prefixed_method_params"] = {"n": sum(pre.values()), "same": same}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", required=True, help="corpus folder with corpus/ and corpus_index.tsv")
    ap.add_argument("--language", required=True, choices=["cpp", "csharp"])
    ap.add_argument("--lib", default=None, help="tree-sitter shared library (see tsbind.find_library)")
    a = ap.parse_args(argv)
    print(json.dumps(census(a.corpus, a.language, a.lib), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
