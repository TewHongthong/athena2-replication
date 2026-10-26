#!/usr/bin/env python3
"""Identifier-kind inference from code alone (Athena Vol. 2, WP3 task 3.1).

Vol. 1 handed the retriever the identifier kind from the benchmark's metadata (an oracle).  Here the kind is
inferred from the snippet the model is shown: the code with the violating name in it, and nothing else.

    infer_kind(language, code, name) -> KindResult

Design (see tests_kind/ for the hand-typed expectations):
  * The target name is replaced by a neutral lower-case probe before parsing, so the casing of the violating
    name (an arbitrary corruption) carries no information.  Nothing about the original name is used.
  * The kind comes from the existing structural extractors (`lang_python`, `lang_ts`), i.e. from syntax:
    a declaration's position, modifiers and type.  The same extractors label the benchmark gold, so a
    disagreement is a disagreement about information, not about vocabulary.
  * Where the extractor decides "constant" by the casing of the NAME (Python module/class level, JS/TS module
    level), that signal is unavailable here; a structural stand-in is used instead (bound once to a literal,
    `const`), and the result lists the alternative kind in `detail["alt_kinds"]`.
  * A bare excerpt (a method without its class) is retried inside a synthetic class.
  * `kind_map` is the one place to retarget coarse kinds to an ontology's kind ids once an ontology exists.

Not done here: kinds that need more than one snippet (a method's role, a field's data type): the structural
facts the extractor records are returned in `detail["facts"]` for a later, ontology-specific mapping.
"""
from __future__ import annotations

import ast
import os
import re
import sys
import textwrap
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import lang_python  # noqa: E402
import lang_ts  # noqa: E402
import tsbind  # noqa: E402

PROBE = "kindprobe"
# Policy knobs (decided on the Vol. 1 dev split, see tools/eval_kind_public5.py):
PY_CLASS_LITERAL_IS_CONSTANT = False   # class-body `x = 1` is a field unless proven otherwise
JS_COMPOSITE_LITERAL_IS_CONSTANT = False   # `const xs = [1, 2]` / `{...}` stays a variable
LANGUAGES = ("python", "java", "csharp", "typescript", "javascript", "cpp")

OK, AMBIGUOUS, UNMODELLED, NOT_FOUND, PARSE_FAILED = "ok", "ambiguous", "unmodelled", "not_found", "parse_failed"


@dataclass
class KindResult:
    kind: Optional[str]          # coarse kind id, or None when the construct has no kind (macro, alias, ...)
    status: str                  # ok | ambiguous | unmodelled | not_found | parse_failed
    reason: str
    detail: dict = field(default_factory=dict)

    @property
    def kinds(self):
        """Primary kind first, then the alternatives the structure cannot rule out."""
        out = [self.kind] if self.kind else []
        return out + [k for k in self.detail.get("alt_kinds", []) if k not in out]


_TS = None


def _ts():
    global _TS
    if _TS is None:
        _TS = tsbind.TreeSitter(tsbind.find_library(os.path.join(HERE, "libtsall.so")))
    return _TS


def _word_re(name):
    return re.compile(r"(?<![\w$])" + re.escape(name) + r"(?![\w$])")


# ------------------------------------------------------------------------------------------ attempts

def _py_method_like(text):
    """True when the excerpt's first statement is a def that looks like a method (self/cls first parameter,
    or a method decorator)."""
    try:
        tree = ast.parse(textwrap.dedent(text))
    except (SyntaxError, ValueError, RecursionError):
        return False
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = n.args.posonlyargs + n.args.args
            if args and args[0].arg in ("self", "cls"):
                return True
            for d in n.decorator_list:
                t = ast.unparse(d)
                if t in ("staticmethod", "classmethod", "property") or t.endswith((".setter", ".getter", ".deleter")):
                    return True
        break
    return False


def _attempts(lang, text):
    if lang == "python":
        d = textwrap.dedent(text)
        wrap = "class _W:\n" + textwrap.indent(d, "    ")
        if _py_method_like(text):
            yield "class-wrap", wrap
            yield "dedent", d
        else:
            yield "raw", text
            if d != text:
                yield "dedent", d
            yield "class-wrap", wrap
    elif lang == "cpp":
        yield "raw", text
        yield "class-wrap", "struct _W {\n" + text + "\n};\n"
    else:
        yield "raw", text
        if lang == "typescript":
            yield "raw-tsx", text           # JSX in the excerpt: only the tsx grammar parses it
        yield "class-wrap", "class _W {\n" + text + "\n}\n"


def _analyze(lang, text, tsx=False):
    content = text.encode("utf-8")
    if lang == "python":
        return lang_python.extract(content)
    path = "snippet.tsx" if (lang == "typescript" and tsx) else "snippet." + lang
    return lang_ts.extract(lang, path, content, _ts())


# ------------------------------------------------------------------------------------------ Python refine

def _py_literal(v):
    if isinstance(v, ast.Constant):
        return v.value is not None and v.value is not Ellipsis
    if isinstance(v, (ast.Tuple, ast.List, ast.Set)):
        return all(_py_literal(x) for x in v.elts)
    if isinstance(v, ast.Dict):
        return all(k is not None and _py_literal(k) for k in v.keys) and all(_py_literal(x) for x in v.values)
    if isinstance(v, ast.UnaryOp):
        return _py_literal(v.operand)
    if isinstance(v, ast.BinOp):
        return _py_literal(v.left) and _py_literal(v.right)
    return False


def _py_bindings(tree, name):
    """Every binding of `name`: (value node or None, "module" | "class" | "function")."""
    out = []

    def targets_of(t):
        return [x for x in ast.walk(t) if isinstance(x, ast.Name) and x.id == name and isinstance(x.ctx, ast.Store)]

    def visit(node, top):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, ast.Assign):
                for t in ch.targets:
                    for x in targets_of(t):
                        out.append((ch.value if t is x else None, top))
            elif isinstance(ch, ast.AnnAssign):
                for x in targets_of(ch.target):
                    out.append((ch.value if ch.target is x else None, top))
            elif isinstance(ch, ast.AugAssign):
                if isinstance(ch.target, ast.Name) and ch.target.id == name:
                    out.append((None, top))
            elif isinstance(ch, (ast.For, ast.AsyncFor, ast.comprehension)):
                if targets_of(ch.target):
                    out.append((None, top))
            elif isinstance(ch, (ast.With, ast.AsyncWith)):
                for it in ch.items:
                    if it.optional_vars is not None and targets_of(it.optional_vars):
                        out.append((None, top))
            elif isinstance(ch, ast.NamedExpr):
                if isinstance(ch.target, ast.Name) and ch.target.id == name:
                    out.append((None, top))
            elif isinstance(ch, ast.ExceptHandler) and ch.name == name:
                out.append((None, top))
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                visit(ch, "function")
            elif isinstance(ch, ast.ClassDef) and top != "function":
                visit(ch, "class")
            else:
                visit(ch, top)

    visit(tree, "module")
    return out


def _py_refine(text, kind):
    """Python has no syntax for constants: a module- or class-level name bound once to a literal."""
    if kind not in ("variable", "field"):
        return kind, []
    try:
        binds = _py_bindings(ast.parse(text), PROBE)
    except (SyntaxError, ValueError, RecursionError):
        return kind, []
    if len(binds) == 1 and binds[0][0] is not None and _py_literal(binds[0][0]):
        level = binds[0][1]
        if level == "module" or (level == "class" and PY_CLASS_LITERAL_IS_CONSTANT):
            return "constant", [kind]
        if level == "class":
            return kind, ["constant"]       # a class attribute bound to a literal: field or constant, syntax cannot say
    return kind, []


# ------------------------------------------------------------------------------------------ JS/TS refine

_FUNC_SCOPE = {"function_declaration", "function_expression", "function", "arrow_function", "method_definition",
               "generator_function_declaration", "generator_function", "class_body", "class_static_block"}


def _js_literal(n):
    t = n.type
    if t in ("number", "string", "true", "false", "regex"):
        return True
    if t == "template_string":
        return not any(c.type == "template_substitution" for c in n.children)
    if t in ("parenthesized_expression", "as_expression", "satisfies_expression", "non_null_expression"):
        cs = n.named_children()
        return bool(cs) and _js_literal(cs[0])
    if t == "unary_expression":
        cs = n.named_children()
        return bool(cs) and _js_literal(cs[-1])
    if t == "binary_expression":
        cs = n.named_children()
        return len(cs) >= 2 and all(_js_literal(c) for c in cs)
    if t == "array":
        return JS_COMPOSITE_LITERAL_IS_CONSTANT and all(_js_literal(c) for c in n.named_children() if c.type != "comment")
    if t == "object":
        if not JS_COMPOSITE_LITERAL_IS_CONSTANT:
            return False
        for p in n.named_children():
            if p.type == "comment":
                continue
            if p.type != "pair":
                return False
            v = p.child("value")
            if v is None or not _js_literal(v):
                return False
        return True
    return False


def _js_refine(lang, text, kind, tsx=False):
    """JS/TS have `const` but no syntax for 'a constant by convention': module-level `const` bound to a literal."""
    if kind != "variable":
        return kind, []
    src = text.encode("utf-8")
    g = ("tsx" if tsx else "typescript") if lang == "typescript" else "javascript"
    root, _err = _ts().parse(g, src)
    for n in root.walk():
        if n.type != "variable_declarator":
            continue
        nm = n.child("name")
        if nm is None or nm.type != "identifier" or nm.text(src) != PROBE:
            continue
        decl = n.parent
        if decl is None or decl.type != "lexical_declaration" or not any(c.type == "const" for c in decl.children):
            continue
        a, top = n.parent, True
        while a is not None:
            if a.type in _FUNC_SCOPE:
                top = False
                break
            a = a.parent
        v = n.child("value")
        if top and v is not None and _js_literal(v):
            return "constant", ["variable"]
    return kind, []


# ------------------------------------------------------------------------------------------ main entry

def infer_kind(language: str, code: str, name: str, kind_map: Optional[dict] = None) -> KindResult:
    """Kind of the identifier `name` declared in `code`, from the code alone."""
    if language not in LANGUAGES:
        raise ValueError(f"unsupported language {language!r}; choose from {LANGUAGES}")
    if _word_re(PROBE).search(code):
        raise ValueError(f"the code already contains the reserved probe name {PROBE!r}")
    if not _word_re(name).search(code):
        return KindResult(None, NOT_FOUND, f"`{name}` does not occur in the code", {})
    neutral = _word_re(name).sub(PROBE, code)
    tried, best = [], None
    for label, text in _attempts(language, neutral):
        try:
            ff = _analyze(language, text, tsx=(label == "raw-tsx"))
        except Exception as e:                      # extractor bug on odd input: record, try the next attempt
            tried.append((label, "error:" + type(e).__name__))
            continue
        if not ff.parse_ok:
            tried.append((label, ff.skip_reason or "parse failed"))
            continue
        decls = sorted((d for d in ff.decls if d.name == PROBE), key=lambda d: d.start)
        nerr = len(ff.error_spans)
        tried.append((label, f"{len(decls)} decl, {nerr} error spans"))
        if decls and (best is None or nerr < best[0]):
            best = (nerr, label, text, decls)
        if decls and nerr == 0:
            break
    if best is None:
        parsed = any("decl" in r for _l, r in tried)
        return KindResult(None, NOT_FOUND if parsed else PARSE_FAILED,
                          "no declaration of the name" if parsed else "the code does not parse",
                          {"tried": tried})
    nerr, label, text, decls = best
    kinds, alts, facts = [], [], []
    for d in decls:
        k, alt = d.kind, []
        if language == "python":
            k, alt = _py_refine(text, k)
        elif language in ("typescript", "javascript"):
            k, alt = _js_refine(language, text, k, tsx=(label == "raw-tsx"))
        elif language == "cpp" and k == "function" and label == "raw":
            alt = ["method"]            # an unqualified definition may be inline in a class body that was cut off
        if kind_map:
            k = kind_map.get(k, k)
            alt = [kind_map.get(a, a) for a in alt]
        kinds.append(k)
        alts.append(alt)
        facts.append({"kind": k, **d.extra})
    detail = {"attempt": label, "parse_errors": nerr, "n_decl": len(decls), "facts": facts, "tried": tried}
    modelled = [(k, a) for k, a in zip(kinds, alts) if k is not None]
    if not modelled:
        return KindResult(None, UNMODELLED, "the declaration has no kind (macro, alias, namespace, ...)", detail)
    k, a = modelled[0]
    if a:
        detail["alt_kinds"] = a
    if len({x for x, _ in modelled}) > 1:
        detail["candidates"] = [x for x, _ in modelled]
        return KindResult(k, AMBIGUOUS, "several declarations of the name with different kinds", detail)
    return KindResult(k, OK, "from the declaration's syntax", detail)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="infer the kind of an identifier from the code alone")
    ap.add_argument("--lang", required=True, choices=LANGUAGES)
    ap.add_argument("--name", required=True)
    ap.add_argument("file")
    a = ap.parse_args(argv)
    r = infer_kind(a.lang, open(a.file, encoding="utf-8").read(), a.name)
    print(r.kind, r.status, r.reason, r.kinds)


if __name__ == "__main__":
    main()
