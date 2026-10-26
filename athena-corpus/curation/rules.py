#!/usr/bin/env python3
"""Ontology access + the curation rule policy (which NamingRules gate / target which identifiers).

The ontology (athena_ontology.json) is read with the standard library only. `Ontology.applicable()`
implements step 1 of graph_loader.get_applicable_rules() (rules that APPLIES_TO both the language
and the identifier kind); `crosscheck_with_graph_loader()` verifies that equivalence against the
real NetworkX implementation when networkx is installed.

POLICY (documented in curation_report.md): a rule is used as a *core* rule for a (language, kind)
only if it (a) has at least one mechanically checkable attribute (casing / prefix / suffix /
min-max length / forbiddenPatterns, casing != 'custom') and (b) applies to every identifier of
that kind (no context condition such as "only exception classes", "only test methods"). Rules
that fail (a) or (b) are listed in EXCLUDED with the reason.
"""
from __future__ import annotations

import json
import keyword
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "pipeline"))
import violation_injector as V  # noqa: E402  (vendored copy of the project's injector)
from output_validator import check_naming_compliance  # noqa: E402

DEFAULT_ONTOLOGY = os.path.join(HERE, "pipeline", "athena_ontology.json")

CORE = {
    ("python", "class"): ["PEP8-CLASS-CAPWORDS"],
    ("python", "function"): ["PEP8-FUNC-SNAKE"],
    ("python", "method"): ["PEP8-METHOD-SNAKE"],
    ("python", "variable"): ["PEP8-VAR-SNAKE", "PEP8-AVOID-CONFUSING-CHARS"],
    ("python", "constant"): ["PEP8-CONST-UPPER"],
    ("python", "parameter"): ["PEP8-PARAM-SELF-CLS"],
    ("python", "field"): ["PEP8-FIELD-PUBLIC-NO-PREFIX"],

    ("java", "class"): ["GJAVA-CLASS-PASCAL"],
    ("java", "interface"): ["GJAVA-INTERFACE-PASCAL"],
    ("java", "enum"): ["GJAVA-ENUM-PASCAL"],
    ("java", "enum_member"): ["GJAVA-ENUM-MEMBER-UPPER-SNAKE"],
    ("java", "method"): ["GJAVA-METHOD-CAMEL"],
    ("java", "field"): ["GJAVA-FIELD-CAMEL", "GJAVA-FIELD-NO-HUNGARIAN"],
    ("java", "constant"): ["GJAVA-CONSTANT-UPPER-SNAKE"],
    ("java", "variable"): ["GJAVA-VARIABLE-CAMEL", "GJAVA-IDENT-ASCII"],
    ("java", "parameter"): ["GJAVA-PARAMETER-CAMEL"],

    ("csharp", "class"): ["DOTNET-CLASS-PASCAL-NOUN"],
    ("csharp", "interface"): ["DOTNET-INTERFACE-I-PREFIX"],
    ("csharp", "enum"): ["DOTNET-ENUM-SINGULAR-OR-PLURAL", "DOTNET-ENUM-NO-ENUM-FLAGS-SUFFIX"],
    ("csharp", "enum_member"): ["DOTNET-ENUM-MEMBER-PASCAL-NOPREFIX"],
    ("csharp", "method"): ["DOTNET-METHOD-VERB-PASCAL"],
    ("csharp", "property"): ["DOTNET-PROPERTY-NOUN-PASCAL"],
    ("csharp", "field"): ["DOTNET-FIELD-PASCAL-NOPREFIX"],
    ("csharp", "constant"): ["DOTNET-CONSTANT-PASCAL"],
    ("csharp", "variable"): ["DOTNET-VARIABLE-CAMEL-DESCRIPTIVE", "DOTNET-NO-HUNGARIAN-NO-UNDERSCORE"],
    ("csharp", "parameter"): ["DOTNET-PARAMETER-CAMEL-DESCRIPTIVE"],
    ("csharp", "boolean_variable"): ["DOTNET-BOOLEAN-AFFIRMATIVE-PREFIX"],

    ("typescript", "class"): ["GTS-CLASS-PASCAL"],
    ("typescript", "interface"): ["GTS-INTERFACE-PASCAL"],
    ("typescript", "enum"): ["GTS-ENUM-PASCAL"],
    ("typescript", "enum_member"): ["GTS-ENUM-MEMBER-CONST"],
    ("typescript", "function"): ["GTS-FUNCTION-CAMEL"],
    ("typescript", "method"): ["GTS-METHOD-CAMEL"],
    ("typescript", "variable"): ["GTS-VARIABLE-CAMEL"],
    ("typescript", "constant"): ["GTS-CONSTANT-CASE"],
    ("typescript", "parameter"): ["GTS-PARAMETER-CAMEL"],
    ("typescript", "field"): ["GTS-FIELD-CAMEL"],
    ("typescript", "property"): ["GTS-PROPERTY-CAMEL"],

    ("javascript", "class"): ["AIRBNB-CLASS-PASCAL"],
    ("javascript", "method"): ["AIRBNB-METHOD-CAMEL"],
    ("javascript", "function"): ["AIRBNB-FUNCTION-CAMEL"],
    ("javascript", "variable"): ["AIRBNB-VARIABLE-CAMEL", "AIRBNB-VAR-DESCRIPTIVE"],
    ("javascript", "constant"): ["AIRBNB-CONST-UPPER"],          # exported constants; see rules_for_check()
    ("javascript", "parameter"): ["AIRBNB-PARAM-DESCRIPTIVE"],
    ("javascript", "field"): ["AIRBNB-FIELD-NO-UNDERSCORE"],
    ("javascript", "property"): ["AIRBNB-PROPERTY-CAMEL"],
}

# Rules of the ontology NOT used as core rules, with the reason (goes into the report).
EXCLUDED = {
    "PEP8-EXCEPTION-ERROR-SUFFIX": "conditional: only exception classes (applied at gate time when a base class name ends in Error/Exception; never an injection target)",
    "PEP8-PARAM-KEYWORD-TRAILING-UNDERSCORE": "conditional: only when a parameter name would collide with a keyword",
    "PEP8-FIELD-NONPUBLIC-UNDERSCORE": "conditional: non-public attributes only; its casing+prefix attributes are mutually inconsistent for the mechanical checker",
    "PEP8-FIELD-NAME-MANGLE": "conditional: name-mangling attributes only (MAY)",
    "PEP8-MODULE-SNAKE": "identifier kind 'module' is a file name, not extracted from code",
    "PEP8-PACKAGE-LOWER": "identifier kind 'package' is a directory name, not extracted from code",
    "GJAVA-METHOD-TEST-UNDERSCORE": "conditional: JUnit test methods only (test methods are exempt from the gate)",
    "GJAVA-PARAMETER-NO-SINGLE-CHAR": "conditional (public methods only) and mechanically identical to GJAVA-PARAMETER-CAMEL (casing only)",
    "GJAVA-TYPE-PARAM-STYLE": "casing 'custom' is not mechanically checkable (check_naming_compliance always reports non-compliance)",
    "GJAVA-PACKAGE-LOWERCASE": "identifier kind 'package' is not extracted",
    "DOTNET-NAMESPACE-DOTTED-PASCAL": "kind 'namespace' not extracted; dotted names cannot pass the PascalCase pattern",
    "DOTNET-TYPE-PARAM-T-PREFIX": "kind 'type_parameter' not extracted",
    "GTS-MODULE-ALIAS-CAMEL": "kind 'module' not extracted",
    "GTS-TYPEPARAM-CASE": "kind 'type_parameter' not extracted",
    "AIRBNB-ACRONYM-CASING": "no mechanically checkable attribute (casing none, no patterns)",
    "AIRBNB-METHOD-BOOLEAN-ISHAS": "conditional: boolean-returning methods only (return type unknowable in JavaScript)",
    "AIRBNB-BOOLEAN-VARIABLE-ISHAS": "kind 'boolean_variable' not extracted for JavaScript (no static types)",
    "AIRBNB-CONST-LOCAL-CAMEL": "used only at gate time for NON-exported constants (see rules_for_check)",
    "AIRBNB-MODULE-CLASS-EXPORT-PASCAL": "kind 'module' not extracted",
    "AIRBNB-MODULE-FUNCTION-EXPORT-CAMEL": "kind 'module' not extracted",
}

TARGET_KINDS = sorted({k for (_, k) in CORE})

# Known caveat texts attached to violation files
RULE_CAVEATS = {
    "PEP8-PARAM-SELF-CLS": "ontology v1 has no dedicated ordinary-parameter casing rule for Python; PEP8-PARAM-SELF-CLS is the only rule attached to kind 'parameter' that carries casing=snake_case, so it is used as the casing carrier",
    "AIRBNB-PARAM-DESCRIPTIVE": "ontology v1 has no parameter-casing rule for JavaScript; only the descriptive-name (min length / single-letter) rule is checked",
}

_RESERVED = {
    "python": set(keyword.kwlist) | {"self", "cls", "match", "case", "print", "None", "True", "False"},
    "java": set("""abstract assert boolean break byte case catch char class const continue default do double else enum extends
        final finally float for goto if implements import instanceof int interface long native new package private protected
        public return short static strictfp super switch synchronized this throw throws transient try void volatile while
        var record yield sealed permits true false null""".split()),
    "csharp": set("""abstract as base bool break byte case catch char checked class const continue decimal default delegate do double
        else enum event explicit extern false finally fixed float for foreach goto if implicit in int interface internal is
        lock long namespace new null object operator out override params private protected public readonly ref return sbyte
        sealed short sizeof stackalloc static string struct switch this throw true try typeof uint ulong unchecked unsafe
        ushort using virtual void volatile while var dynamic async await record init value get set add remove yield""".split()),
    "typescript": set("""break case catch class const continue debugger default delete do else enum export extends false finally for
        function if import in instanceof new null return super switch this throw true try typeof var void while with yield
        let static implements interface package private protected public await async of as any boolean number string symbol
        type from get set declare module namespace readonly undefined NaN Infinity arguments eval""".split()),
}
_RESERVED["javascript"] = _RESERVED["typescript"]
_RESERVED["cpp"] = set("""alignas alignof and and_eq asm auto bitand bitor bool break case catch char char8_t char16_t char32_t class compl
    concept const consteval constexpr constinit const_cast continue co_await co_return co_yield decltype default delete do
    double dynamic_cast else enum explicit export extern false float for friend goto if inline int long mutable namespace
    new noexcept not not_eq nullptr operator or or_eq private protected public register reinterpret_cast requires return
    short signed sizeof static static_assert static_cast struct switch template this thread_local throw true try typedef
    typeid typename union unsigned using virtual void volatile wchar_t while xor xor_eq final override NULL""".split())
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


# Vol. 1 hand-made special cases in rules_for_check() (Python exception classes, C# boolean variables, JavaScript
# exported constants). They stay on unless set_core() installs a per-pack table, which has no such cases.
_SPECIALS = True


def set_core(table: dict, excluded: dict | None = None) -> None:
    """Replace the CORE table (and EXCLUDED / TARGET_KINDS) in place with a per-pack table.

    `table` maps (language, kind) -> [rule ids]. The Vol. 1 special cases in rules_for_check() are switched
    off: a pack states exactly which rules every identifier of a kind must satisfy. Not called in a Vol. 1
    run, so the hard-coded tables above stay in force there.
    """
    global _SPECIALS
    CORE.clear()
    CORE.update({k: list(v) for k, v in table.items()})
    EXCLUDED.clear()
    EXCLUDED.update(excluded or {})
    TARGET_KINDS[:] = sorted({k for (_, k) in CORE})
    _SPECIALS = False


def is_valid_new_name(lang: str, name: str) -> bool:
    return bool(_IDENT_RE.match(name)) and name not in _RESERVED[lang]


class Ontology:
    def __init__(self, path: str = DEFAULT_ONTOLOGY):
        self.path = path
        with open(path, "rb") as f:
            raw = f.read()
        import hashlib
        self.sha256 = hashlib.sha256(raw).hexdigest()
        d = json.loads(raw.decode("utf-8"))
        self.nodes = {n["id"]: n for n in d["nodes"]}
        self.languages = [n["id"] for n in d["nodes"] if n["type"] == "Language"]
        self.kinds = [n["id"] for n in d["nodes"] if n["type"] == "IdentifierKind"]
        self._applies = {}
        for e in d["links"]:
            if e["relation"] == "APPLIES_TO":
                a = self._applies.setdefault(e["source"], {"lang": set(), "kind": set()})
                if e["target"] in self.languages:
                    a["lang"].add(e["target"])
                elif e["target"] in self.kinds:
                    a["kind"].add(e["target"])
        self.default_standard = {l: self.nodes[l].get("defaultStandardId") for l in self.languages}
        self.standard_name = {n["id"]: n.get("name") for n in d["nodes"] if n["type"] == "Standard"}
        self.n_nodes, self.n_links = len(d["nodes"]), len(d["links"])

    def rule(self, rid: str) -> dict:
        n = self.nodes[rid]
        return {"id": rid, **n}

    def applicable(self, lang: str, kind: str, naming_only=True) -> list:
        out = []
        for rid, a in self._applies.items():
            n = self.nodes.get(rid)
            if n is None or (naming_only and n["type"] != "NamingRule"):
                continue
            if lang in a["lang"] and kind in a["kind"]:
                out.append(rid)
        return sorted(out)

    def validate_core(self):
        """Every CORE rule must be retrievable for its (language, kind) — keeps ground truth and
        Graph-RAG retrieval consistent."""
        problems = []
        for (lang, kind), ids in CORE.items():
            app = set(self.applicable(lang, kind))
            for rid in ids:
                if rid not in app:
                    problems.append(f"{rid} is not applicable to ({lang}, {kind})")
                r = self.nodes.get(rid)
                if r is None:
                    problems.append(f"{rid} missing from ontology")
                elif r.get("casing") == "custom":
                    problems.append(f"{rid} has casing 'custom' (not mechanically checkable)")
        return problems

    def crosscheck_with_graph_loader(self, graph_loader_module):
        """Compare applicable() with graph_loader.get_applicable_rules() (needs networkx)."""
        g = graph_loader_module.load_graph(self.path)
        bad = []
        for lang in self.languages:
            for kind in self.kinds:
                mine = self.applicable(lang, kind)
                theirs = sorted(x["rule"]["id"] for x in graph_loader_module.get_applicable_rules(g, lang, kind)
                                if x["rule"].get("type") == "NamingRule")
                if mine != theirs:
                    bad.append((lang, kind, mine, theirs))
        return bad


def rules_for_check(lang: str, d) -> list:
    """Rule ids a declaration must satisfy (gate), before name normalisation."""
    ids = list(CORE.get((lang, d.kind), []))
    if not _SPECIALS:
        return ids
    if lang == "python" and d.kind == "class":
        if any(b.endswith(("Error", "Exception")) for b in d.extra.get("bases", [])):
            ids.append("PEP8-EXCEPTION-ERROR-SUFFIX")
    if lang == "csharp" and d.kind == "boolean_variable":
        ids += CORE.get((lang, d.extra.get("base_kind", "variable")), [])
    if lang == "javascript" and d.kind == "constant":
        ids = ["AIRBNB-CONST-UPPER"] if d.extra.get("exported") else ["AIRBNB-CONST-LOCAL-CAMEL"]
    return ids


def name_for_check(lang: str, d) -> str:
    n = d.name
    if lang == "python" and n.startswith("_") and not (n.startswith("__") and n.endswith("__")):
        n = n.lstrip("_")          # PEP 8 non-public marker is not part of the casing check
    return n


def gate(lang: str, d, onto: Ontology):
    """Returns list of (rule_id, [reasons]) failures for declaration `d` (empty = compliant)."""
    fails = []
    nm = name_for_check(lang, d)
    if not nm:
        return fails
    for rid in rules_for_check(lang, d):
        ok, reasons = check_naming_compliance(nm, onto.rule(rid))
        if not ok:
            fails.append((rid, reasons))
    return fails


def target_rule_ids(lang: str, d) -> list:
    """Rules against which violations are injected for target `d` (never conditional ones)."""
    return list(CORE.get((lang, d.kind), []))


def iter_candidates(standard_name: str, rule: dict):
    """Same candidate order as violation_injector.inject_violation(), as a generator so the caller
    can skip candidates that do not survive rename verification."""
    if rule.get("casing"):
        for casing_name, cand in V.casing_variants(standard_name).items():
            if casing_name != rule["casing"]:
                yield ("casing_swap", cand)
    if rule.get("forbiddenPatterns"):
        for cand in V.forbidden_pattern_candidates(rule["forbiddenPatterns"], standard_name):
            yield ("forbidden_pattern", cand)
    if rule.get("minLength"):
        for cand in V.abbreviation_candidates(standard_name):
            yield ("abbreviate", cand)
    prefix = rule.get("prefix")
    if prefix and "/" not in prefix and standard_name.lower().startswith(prefix.lower()):
        yield ("prefix_strip", standard_name[len(prefix):] or "value")
    suffix = rule.get("suffix")
    if suffix and standard_name.lower().endswith(suffix.lower()):
        yield ("suffix_strip", standard_name[: -len(suffix)] or "value")


def parity_check(standard_name: str, kind: str, rule: dict) -> bool:
    """iter_candidates()'s first verified candidate must equal the original injector's result."""
    orig = V.inject_violation(standard_name, kind, rule)
    mine = None
    for method, cand in iter_candidates(standard_name, rule):
        if cand == standard_name:
            continue
        ok, reasons = check_naming_compliance(cand, rule)
        if not ok:
            mine = (method, cand, reasons)
            break
    if orig is None:
        return mine is None
    return mine is not None and (orig.injection_method, orig.injected_name, orig.expected_violation_reasons) == mine
