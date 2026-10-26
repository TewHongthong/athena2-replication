#!/usr/bin/env python3
"""Python extractor: stdlib `ast` + `tokenize` (no third-party parser needed)."""
from __future__ import annotations

import ast
import io
import keyword
import re
import tokenize

from facts import (Decl, FileFacts, Tok, UnitCand, line_starts_of, DECL, REF, MEMBER, KWARG, IMPORT, OTHER)

_UPPER = re.compile(r"_?[A-Z][A-Z0-9_]*$")


class _Erase(ast.NodeTransformer):
    """Replace every identifier-bearing field by '_' so two parses can be compared for structure."""

    def visit_Name(self, n):
        n.id = "_"
        return n

    def visit_arg(self, n):
        n.arg = "_"
        self.generic_visit(n)
        return n

    def visit_FunctionDef(self, n):
        n.name = "_"
        self.generic_visit(n)
        return n

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, n):
        n.name = "_"
        self.generic_visit(n)
        return n

    def visit_Expr(self, n):
        # docstring-like expression statements: content may legitimately change (comment renaming)
        if isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
            n.value.value = ""
        self.generic_visit(n)
        return n

    def visit_Attribute(self, n):
        n.attr = "_"
        self.generic_visit(n)
        return n

    def visit_keyword(self, n):
        if n.arg is not None:
            n.arg = "_"
        self.generic_visit(n)
        return n

    def visit_alias(self, n):
        n.name = "_"
        n.asname = None if n.asname is None else "_"
        return n

    def visit_ImportFrom(self, n):
        n.module = None if n.module is None else "_"
        self.generic_visit(n)
        return n

    def visit_ExceptHandler(self, n):
        n.name = None if n.name is None else "_"
        self.generic_visit(n)
        return n

    def visit_Global(self, n):
        n.names = ["_"] * len(n.names)
        return n

    visit_Nonlocal = visit_Global


def _shape(src: bytes):
    """Fingerprint = (name-erased AST dump, token-type sequence). Raises SyntaxError if not parseable."""
    tree = ast.parse(src.decode("utf-8"))
    dump = ast.dump(_Erase().visit(tree), include_attributes=False)
    toks = [t.type for t in tokenize.tokenize(io.BytesIO(src).readline)]
    return dump, tuple(toks)


def extract(content: bytes) -> FileFacts:
    ls = line_starts_of(content)
    ff = FileFacts(language="python", src=content, line_starts=ls)
    try:
        text = content.decode("utf-8")
        tree = ast.parse(text)
    except (UnicodeDecodeError, SyntaxError, ValueError, RecursionError) as e:
        ff.parse_ok = False
        ff.skip_reason = "python parse failed: " + type(e).__name__
        return ff
    try:
        ff.shape = _shape(content)
    except Exception as e:  # tokenizer disagreement -> unusable for verification
        ff.parse_ok = False
        ff.skip_reason = "python tokenize failed: " + type(e).__name__
        return ff
    ff.reverify = _shape

    lines_b = content.split(b"\n")

    def boff(row: int, col_chars: int) -> int:
        lb = lines_b[row - 1]
        return ls[row - 1] + len(lb.decode("utf-8", errors="replace")[:col_chars].encode("utf-8"))

    # --- all tokens (names + comments)
    name_toks = []           # (start, end, string) incl. keywords, source order
    import_offsets = set()
    comment_spans = []
    first_sig = True         # next significant token is the first of a logical line
    in_import = False
    for t in tokenize.tokenize(io.BytesIO(content).readline):
        if t.type == tokenize.NEWLINE:
            first_sig = True
            in_import = False
            continue
        if t.type == tokenize.COMMENT:
            comment_spans.append((boff(*t.start), boff(*t.end)))
            continue
        if t.type in (tokenize.NL, tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING, tokenize.ENDMARKER):
            continue
        if t.type == tokenize.NAME:
            s_off = boff(*t.start)
            e_off = boff(*t.end)
            name_toks.append((s_off, e_off, t.string))
            if first_sig and t.string in ("import", "from"):
                in_import = True
            if in_import:
                import_offsets.add(s_off)
        first_sig = False

    tok_by_start = {}
    for s, e, string in name_toks:
        if keyword.iskeyword(string):
            continue
        role = REF
        tok_by_start[s] = Tok(s, e, string, role, "NAME")

    for off in import_offsets:      # every name token of an import statement
        tk = tok_by_start.get(off)
        if tk is not None:
            tk.role = IMPORT

    def set_role(off, role, expect=None):
        tk = tok_by_start.get(off)
        if tk is not None and (expect is None or tk.text == expect):
            tk.role = role
            return tk
        return None

    # --- role overrides from the AST
    docstring_spans = []
    fstring_refs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            end_off = boff(node.end_lineno, node.end_col_offset)
            set_role(end_off - len(node.attr.encode("utf-8")), MEMBER, node.attr)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            set_role(ls[node.lineno - 1] + node.col_offset, KWARG, node.arg)
        elif isinstance(node, ast.JoinedStr):
            names_here = set()
            for sub in ast.walk(node):
                if isinstance(sub, ast.Name):
                    names_here.add(sub.id)
                elif isinstance(sub, ast.Attribute):
                    names_here.add(sub.attr)
            if names_here:
                fstring_refs.append((ls[node.lineno - 1] + node.col_offset,
                                     boff(node.end_lineno, node.end_col_offset), names_here))
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            docstring_spans.append((ls[node.lineno - 1] + node.col_offset,
                                    boff(node.end_lineno, node.end_col_offset)))
    ff.fstring_refs = fstring_refs
    ff.comment_spans = comment_spans + docstring_spans
    doc_set = set(docstring_spans)
    string_spans = []
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr) or (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            sp = (ls[node.lineno - 1] + node.col_offset, boff(node.end_lineno, node.end_col_offset))
            if sp not in doc_set:
                string_spans.append(sp)
    ff.string_spans = string_spans

    # --- declarations
    decls = []

    def add_decl(start, name, kind, ns, exempt=None, **extra):
        tk = tok_by_start.get(start)
        if tk is None or tk.text != name:
            return None
        if tk.role != IMPORT:
            tk.role = DECL
        d = Decl(name, kind, start, start + len(name.encode("utf-8")), ns, exempt, extra)
        decls.append(d)
        return d

    def name_after_keyword(node, kw):
        start = ls[node.lineno - 1] + node.col_offset
        seen_kw = False
        for s, e, string in name_toks:
            if s < start:
                continue
            if not seen_kw:
                if string == kw:
                    seen_kw = True
                continue
            return s
        return None

    def first_param_name(fn):
        a = fn.args
        allp = list(a.posonlyargs) + list(a.args)
        return allp[0].arg if allp else None

    def dec_names(fn):
        out = set()
        for d in fn.decorator_list:
            if isinstance(d, ast.Name):
                out.add(d.id)
            elif isinstance(d, ast.Attribute):
                out.add(d.attr)
            elif isinstance(d, ast.Call):
                f = d.func
                out.add(f.id if isinstance(f, ast.Name) else getattr(f, "attr", ""))
        return out

    def visit(node, ctx, parent):
        """ctx: 'module' | 'class' | 'function' plus enclosing ClassDef for methods."""
        kind_ctx = ctx["where"]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            in_class = kind_ctx == "class"
            off = name_after_keyword(node, "def")
            if off is not None:
                if in_class:
                    decs = dec_names(node)
                    ex = None
                    n = node.name
                    if n.startswith("__") and n.endswith("__"):
                        ex = "dunder"
                    add_decl(off, n, "method", "member", ex, decorators=sorted(decs), cls=ctx.get("cls"))
                else:
                    add_decl(off, node.name, "function", "type", None)
            fp = first_param_name(node)
            args = node.args
            allargs = list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs)
            if args.vararg:
                allargs.append(args.vararg)
            if args.kwarg:
                allargs.append(args.kwarg)
            for a in allargs:
                aoff = ls[a.lineno - 1] + a.col_offset
                ex = None
                if in_class and a.arg == fp and a.arg in ("self", "cls", "mcs", "metacls"):
                    ex = "self_cls"
                elif a.arg == "_":
                    ex = "underscore"
                add_decl(aoff, a.arg, "parameter", "local", ex)
            new_ctx = {"where": "function", "cls": ctx.get("cls"), "self": fp if in_class else ctx.get("self")}
            for ch in node.body:
                visit(ch, new_ctx, node)
            return
        if isinstance(node, ast.ClassDef):
            off = name_after_keyword(node, "class")
            bases = []
            for b in node.bases:
                bases.append(b.id if isinstance(b, ast.Name) else getattr(b, "attr", ""))
            if off is not None:
                add_decl(off, node.name, "class", "type", None, bases=bases)
            new_ctx = {"where": "class", "cls": node.name, "self": None}
            for ch in node.body:
                visit(ch, new_ctx, node)
            return
        # assignments / bindings
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AnnAssign,)):
            targets = [node.target]
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            targets = [node.target]
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            targets = [it.optional_vars for it in node.items if it.optional_vars is not None]
        elif isinstance(node, ast.NamedExpr):
            targets = [node.target]
        elif isinstance(node, ast.comprehension):
            targets = [node.target]
        elif isinstance(node, ast.ExceptHandler) and node.name:
            # name token follows the 'as' keyword on the handler line
            start = ls[node.lineno - 1] + node.col_offset
            seen = False
            for s, e, string in name_toks:
                if s < start:
                    continue
                if string == "as":
                    seen = True
                    continue
                if seen:
                    add_decl(s, node.name, "variable", "local", None)
                    break
        for tgt in targets:
            for sub in ast.walk(tgt):
                if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                    off = ls[sub.lineno - 1] + sub.col_offset
                    n = sub.id
                    is_dunder = n.startswith("__") and n.endswith("__") and len(n) > 4
                    if kind_ctx == "function":
                        add_decl(off, n, "variable", "local",
                                 "underscore" if n in ("_", "__") else ("dunder" if is_dunder else None))
                    elif kind_ctx == "module":
                        kind = "constant" if (_UPPER.match(n) and len(n.lstrip("_")) > 1) else "variable"
                        add_decl(off, n, kind, "local",
                                 "underscore" if n in ("_", "__") else ("dunder" if is_dunder else None))
                    else:  # class body attribute
                        if n.startswith("__") and n.endswith("__"):
                            add_decl(off, n, "field", "member", "dunder")
                        elif _UPPER.match(n) and len(n.lstrip("_")) > 1:
                            add_decl(off, n, "constant", "member", None)
                        else:
                            add_decl(off, n, "field", "member", None)
                elif isinstance(sub, ast.Attribute) and isinstance(sub.ctx, ast.Store) \
                        and isinstance(sub.value, ast.Name) and ctx.get("self") and sub.value.id == ctx["self"] \
                        and kind_ctx == "function" and isinstance(node, (ast.Assign, ast.AnnAssign)):
                    end_off = boff(sub.end_lineno, sub.end_col_offset)
                    off = end_off - len(sub.attr.encode("utf-8"))
                    tk = tok_by_start.get(off)
                    if tk is not None and tk.text == sub.attr:
                        tk.role = DECL
                        decls.append(Decl(sub.attr, "field", off, off + len(sub.attr.encode("utf-8")), "member",
                                          None, {"via": "self"}))
        for ch in ast.iter_child_nodes(node):
            visit(ch, ctx, node)

    visit(tree, {"where": "module", "cls": None, "self": None}, None)
    # comprehension targets and lambdas params: comprehensions were visited; lambda args -> exempt params
    for node in ast.walk(tree):
        if isinstance(node, ast.Lambda):
            a = node.args
            for arg in list(a.posonlyargs) + list(a.args) + list(a.kwonlyargs) + ([a.vararg] if a.vararg else []) + ([a.kwarg] if a.kwarg else []):
                off = ls[arg.lineno - 1] + arg.col_offset
                if not any(d.start == off for d in decls):
                    add_decl(off, arg.arg, "parameter", "local", "lambda_param")

    # de-duplicate decls at the same offset (defensive)
    seen = set()
    uniq = []
    for d in decls:
        if d.start in seen:
            continue
        seen.add(d.start)
        uniq.append(d)
    ff.decls = uniq
    ff.toks = sorted(tok_by_start.values(), key=lambda t: t.start)

    # --- unit candidates: top-level defs/classes and, for classes, each method
    units = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            first = min([node.lineno] + [d.lineno for d in node.decorator_list]) - 1
            units.append(UnitCand(first, node.end_lineno - 1,
                                  ("class " if isinstance(node, ast.ClassDef) else "function ") + node.name, True))
            if isinstance(node, ast.ClassDef):
                for m in node.body:
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        f2 = min([m.lineno] + [d.lineno for d in m.decorator_list]) - 1
                        units.append(UnitCand(f2, m.end_lineno - 1, f"method {node.name}.{m.name}", False))
    ff.units = units
    return ff


def ff_line(ls, off):
    lo, hi = 0, len(ls) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if ls[mid] <= off:
            lo = mid
        else:
            hi = mid - 1
    return lo
