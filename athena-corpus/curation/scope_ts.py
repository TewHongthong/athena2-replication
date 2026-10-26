"""Syntax-only scope front ends for C++ and C# (tree-sitter).

A front end turns a code snippet into the same record the Python front end produces:

    {"errors": [...],                  # parse errors (the snippet cannot be analysed reliably)
     "occ": {occurrence id: key},      # every identifier occurrence -> what it is bound to
     "decls": [{"name", "kind", "key", "scope"}],
     "ext_uses": [{"name", "scope", "pos"}],   # unqualified names that no declaration in the snippet binds
     "names": {occurrence id: name}}
A key is ("src", declaration kind, declaration offset) for a name bound to a declaration inside the snippet,
("ext", name) for an unqualified name that is bound to nothing in the snippet (a member of an enclosing class, a
global, a library name), ("attr", name) for a member selected through `.`, `->` or `::`, and ("label", name).

Nothing is compiled and no header or assembly is read, so the analysis is by name and nesting only; it cannot tell
two members of different classes apart, and it does not know which overload or type a name refers to.  Offsets are
character offsets; `omap` maps an offset in the analysed text back to the text before the rename.
"""
from __future__ import annotations

import tsbind

_TS = None


def _parser():
    global _TS
    if _TS is None:
        _TS = tsbind.TreeSitter(tsbind.find_library())
    return _TS


class _Scope:
    __slots__ = ("kind", "start", "parent", "decls", "path")

    def __init__(self, kind, start, mstart, parent):
        self.kind, self.start, self.parent = kind, start, parent
        self.decls = {}                       # name -> [decl dict]
        self.path = (parent.path if parent else ()) + ((kind, mstart),)


class _Model:
    """Collects scopes, declarations and identifier occurrences, then binds the occurrences."""

    IDENT = set()

    def __init__(self, src: bytes, omap):
        self.src, self.omap = src, omap
        self.ascii = all(b < 128 for b in src)
        self.declared = set()                 # byte offsets of declaration name tokens
        self.override = {}                    # id(node) -> scope used for that node's subtree
        self.all_decls = []                   # (scope, decl)
        self.refs = []                        # (name, pos, scope, role)
        self.root = _Scope("TU", 0, omap(0), None)

    # -- offsets / text
    def cpos(self, b):
        return b if self.ascii else len(self.src[:b].decode("utf-8", errors="replace"))

    def text(self, n):
        return self.src[n.start:n.end].decode("utf-8", errors="replace")

    # -- scopes / declarations
    def new_scope(self, kind, n, parent):
        s = self.cpos(n.start)
        return _Scope(kind, s, self.omap(s), parent)

    def add_decl(self, sc, node, kind, whole_scope=None, tparam=False):
        if node is None:
            return
        while sc.kind == "template" and not tparam and sc.parent is not None:
            sc = sc.parent
        pos, end = self.cpos(node.start), self.cpos(node.end)
        whole = sc.kind in ("class", "enum") if whole_scope is None else whole_scope
        d = {"name": self.text(node), "kind": kind, "pos": pos, "visible": sc.start if whole else end}
        sc.decls.setdefault(d["name"], []).append(d)
        self.declared.add(node.start)
        self.all_decls.append((sc, d))

    # -- binding
    def lookup(self, sc, name, pos):
        s = sc
        while s is not None:
            cands = [d for d in s.decls.get(name, ()) if d["visible"] <= pos]
            if cands:
                return max(cands, key=lambda d: (d["visible"], d["pos"]))
            s = s.parent
        return None

    def finish(self, errors):
        res = {"errors": errors, "occ": {}, "decls": [], "ext_uses": [], "names": {}}
        om = self.omap
        for sc, d in self.all_decls:
            o = om(d["pos"])
            key = ("src", d["kind"], o)
            res["occ"][("d", d["kind"], o)] = key
            res["names"][("d", d["kind"], o)] = d["name"]
            res["decls"].append({"name": d["name"], "kind": d["kind"], "key": key, "scope": sc.path})
        for name, pos, sc, role in self.refs:
            o = om(pos)
            if role == "def":
                key = ("ext", name)       # declarator-id of an out-of-class member definition: not looked up
            elif role == "lex":
                d = self.lookup(sc, name, pos)
                if d is not None:
                    key = ("src", d["kind"], om(d["pos"]))
                else:
                    key = ("ext", name)
                    res["ext_uses"].append({"name": name, "scope": sc.path, "pos": o})
            else:
                key = (role, name)
            res["occ"][("r", o)] = key
            res["names"][("r", o)] = name
        return res

    def walk(self, n, sc, handler):
        child_sc = handler(self, n, sc) or sc
        if n.type in self.IDENT and n.start not in self.declared:
            self.ident(n, sc)
        for c in n.children:
            self.walk(c, self.override.get(id(c), child_sc), handler)


def _errors(root):
    return [f"parse error at byte {n.start}" for n in root.walk() if n.is_error or n.is_missing][:5]


# ======================================================================================== C++
CPP_KEYWORDS = set("""alignas alignof and and_eq asm auto bitand bitor bool break case catch char char8_t char16_t
char32_t class compl concept const consteval constexpr constinit const_cast continue co_await co_return co_yield
decltype default delete do double dynamic_cast else enum explicit export extern false float for friend goto if inline
int long mutable namespace new noexcept not not_eq nullptr operator or or_eq private protected public register
reinterpret_cast requires return short signed sizeof static static_assert static_cast struct switch template this
thread_local throw true try typedef typeid typename union unsigned using virtual void volatile wchar_t while xor
xor_eq""".split())

_CPP_WRAPPERS = ("pointer_declarator", "reference_declarator", "array_declarator", "parenthesized_declarator",
                 "attributed_declarator", "init_declarator")


def _cpp_names(d):
    """Name tokens declared by a declarator subtree."""
    if d is None:
        return []
    if d.type in ("identifier", "field_identifier"):
        return [d]
    if d.type == "structured_binding_declarator":
        return [c for c in d.children if c.type == "identifier"]
    if d.type in _CPP_WRAPPERS or d.type == "function_declarator":
        inner = d.child("declarator")
        if inner is None:
            inner = next((c for c in d.children if c.named and c.type not in ("type_qualifier", "parameter_list")
                          and not c.type.endswith("_specifier")), None)
        return _cpp_names(inner)
    return []


def _cpp_find_fd(d):
    while d is not None and d.type in _CPP_WRAPPERS:
        d = d.child("declarator") or next((c for c in d.children if c.named), None)
    return d if d is not None and d.type == "function_declarator" else None


class _Cpp(_Model):
    IDENT = {"identifier", "type_identifier", "namespace_identifier", "field_identifier", "statement_identifier"}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.defpos = set()   # start offsets of the member name in an out-of-class definition `A::name(...) {}`

    def ident(self, n, sc):
        p, role = n.parent, "lex"
        if n.type == "statement_identifier":
            role = "label"
        elif n.type == "field_identifier":
            role = "attr"
        elif n.start in self.defpos:
            role = "def"
        elif p is not None and p.type == "qualified_identifier":
            role = "attr" if p.child("name") is n else "lex"
        elif p is not None and p.type == "field_expression" and p.child("field") is n:
            role = "attr"
        self.refs.append((self.text(n), self.cpos(n.start), sc, role))


def _cpp_param_list_live(n):
    p = n.parent
    if p is None:
        return False
    if p.type in ("lambda_declarator", "catch_clause"):
        return True
    if p.type == "function_declarator":
        q = p.parent
        while q is not None and q.type in _CPP_WRAPPERS:
            q = q.parent
        return q is not None and q.type == "function_definition"
    return False


def _cpp_handler(m, n, sc):
    t = n.type
    if t == "namespace_definition":
        m.add_decl(sc, n.child("name"), "NamespaceDecl")
        return m.new_scope("namespace", n, sc)
    if t in ("class_specifier", "struct_specifier", "union_specifier"):
        nm = n.child("name")
        if nm is not None and nm.type == "type_identifier":
            m.add_decl(sc, nm, "TypeDecl")
        return sc
    if t == "field_declaration_list":
        return m.new_scope("class", n, sc)
    if t == "enum_specifier":
        m.add_decl(sc, n.child("name"), "TypeDecl")
        if any((not c.named) and c.type in ("class", "struct") for c in n.children):
            return m.new_scope("enum", n, sc)
        return sc
    if t == "enumerator":
        m.add_decl(sc, n.child("name"), "EnumConstantDecl")
        return sc
    if t == "function_definition":
        fd = _cpp_find_fd(n.child("declarator"))
        nm = fd.child("declarator") if fd is not None else None
        if nm is not None and nm.type in ("identifier", "field_identifier"):
            m.add_decl(sc, nm, "FunctionDecl")
        elif nm is not None and nm.type == "qualified_identifier":
            leaf = nm.child("name")
            if leaf is not None and leaf.type == "identifier":
                m.defpos.add(leaf.start)
        return m.new_scope("function", n, sc)
    if t == "parameter_list":
        if _cpp_param_list_live(n):
            return sc
        return m.new_scope("proto", n, sc)
    if t in ("parameter_declaration", "optional_parameter_declaration", "variadic_parameter_declaration"):
        for nm in _cpp_names(n.child("declarator")):
            m.add_decl(sc, nm, "ParmVarDecl", whole_scope=True)
        return sc
    if t in ("declaration", "field_declaration"):
        for d in n.children_of("declarator"):
            fn = _cpp_find_fd(d) is not None
            kind = "FunctionDecl" if fn else ("FieldDecl" if t == "field_declaration" else "VarDecl")
            for nm in _cpp_names(d):
                m.add_decl(sc, nm, kind)
        return sc
    if t == "for_range_loop":
        nsc = m.new_scope("for", n, sc)
        for nm in _cpp_names(n.child("declarator")):
            m.add_decl(nsc, nm, "VarDecl")
        return nsc
    if t in ("for_statement", "if_statement", "while_statement", "switch_statement"):
        return m.new_scope(t.replace("_statement", ""), n, sc)
    if t == "compound_statement":
        if n.parent is not None and n.parent.type in ("function_definition", "lambda_expression", "catch_clause"):
            return sc
        return m.new_scope("block", n, sc)
    if t == "lambda_expression":
        caps = n.child("captures")
        if caps is not None:
            m.override[id(caps)] = sc
        return m.new_scope("lambda", n, sc)
    if t == "catch_clause":
        return m.new_scope("catch", n, sc)
    if t == "template_declaration":
        return m.new_scope("template", n, sc)
    if t in ("type_parameter_declaration", "variadic_type_parameter_declaration"):
        for c in n.children:
            if c.type == "type_identifier":
                m.add_decl(sc, c, "TypeDecl", tparam=True)
        return sc
    if t == "alias_declaration":
        m.add_decl(sc, n.child("name"), "TypeDecl")
        return sc
    if t == "type_definition":
        for d in n.children_of("declarator"):
            for nm in (_cpp_names(d) or ([d] if d.type == "type_identifier" else [])):
                m.add_decl(sc, nm, "TypeDecl")
        return sc
    return sc


def analyse_cpp(code: str, omap):
    src = code.encode("utf-8")
    root, _ = _parser().parse("cpp", src)
    errors = _errors(root)
    m = _Cpp(src, omap)
    m.walk(root, m.root, _cpp_handler)
    return m.finish(errors)


# ======================================================================================== C#
CS_KEYWORDS = set("""abstract as base bool break byte case catch char checked class const continue decimal default
delegate do double else enum event explicit extern false finally fixed float for foreach goto if implicit in int
interface internal is lock long namespace new null object operator out override params private protected public
readonly ref return sbyte sealed short sizeof stackalloc static string struct switch this throw true try typeof uint
ulong unchecked unsafe ushort using virtual void volatile while""".split())

_CS_TYPES = {"class_declaration", "struct_declaration", "interface_declaration", "record_declaration",
             "record_struct_declaration"}
_CS_FUNCS = {"method_declaration", "constructor_declaration", "destructor_declaration", "operator_declaration",
             "conversion_operator_declaration", "accessor_declaration", "local_function_statement",
             "lambda_expression", "anonymous_method_expression", "delegate_declaration"}
_CS_STMT_SCOPES = {"for_statement": "for", "using_statement": "using", "fixed_statement": "fixed",
                   "lock_statement": "lock", "if_statement": "if", "while_statement": "while",
                   "switch_statement": "switch", "switch_section": "section", "switch_expression_arm": "arm",
                   "query_expression": "query"}


class _Cs(_Model):
    IDENT = {"identifier"}

    def ident(self, n, sc):
        p, role = n.parent, "lex"
        if p is not None:
            pt = p.type
            if pt in ("member_access_expression", "member_binding_expression") and p.child("name") is n:
                role = "attr"
            elif pt == "argument" and p.child("name") is n:
                role = "attr"
            elif pt in ("qualified_name", "alias_qualified_name") and p.child("name") is n:
                role = "attr"
            elif pt == "assignment_expression" and p.child("left") is n and p.parent is not None \
                    and p.parent.type == "initializer_expression":
                role = "attr"
            elif pt in ("anonymous_object_member_declarator", "name_colon", "name_equals", "expression_colon"):
                role = "attr"
            elif pt in ("labeled_statement", "goto_statement"):
                role = "label"
        self.refs.append((self.text(n), self.cpos(n.start), sc, role))


def _cs_handler(m, n, sc):
    t = n.type
    if t in ("namespace_declaration", "file_scoped_namespace_declaration"):
        return m.new_scope("namespace", n, sc)
    if t in _CS_TYPES or t == "enum_declaration":
        m.add_decl(sc, n.child("name"), "TypeDecl")
        return sc
    if t == "declaration_list":
        if n.parent is not None and n.parent.type in _CS_TYPES:
            return m.new_scope("class", n, sc)
        return sc
    if t == "enum_member_declaration_list":
        return m.new_scope("enum", n, sc)
    if t == "enum_member_declaration":
        m.add_decl(sc, n.child("name"), "EnumMember")
        return sc
    if t in _CS_FUNCS:
        nm = n.child("name")
        if t == "local_function_statement":
            m.add_decl(sc, nm, "LocalFunction", whole_scope=True)
        elif t == "method_declaration":
            m.add_decl(sc, nm, "Method")
        return m.new_scope("function", n, sc)
    if t == "property_declaration":
        m.add_decl(sc, n.child("name"), "Property")
        return sc
    if t == "event_declaration":
        m.add_decl(sc, n.child("name"), "Event")
        return sc
    if t == "parameter":
        m.add_decl(sc, n.child("name"), "Parameter", whole_scope=True)
        return sc
    if t == "implicit_parameter":
        m.add_decl(sc, n, "Parameter", whole_scope=True)
        return sc
    if t == "type_parameter":
        for c in n.children:
            if c.type == "identifier":
                m.add_decl(sc, c, "TypeParameter", whole_scope=True)
        return sc
    if t == "variable_declarator":
        m.add_decl(sc, n.child("name"), "Field" if sc.kind == "class" else "LocalVar")
        return sc
    if t == "tuple_pattern":
        for c in n.children_of("name"):
            m.add_decl(sc, c, "LocalVar")
        return sc
    if t in ("declaration_pattern", "declaration_expression", "catch_declaration", "var_pattern"):
        nm = n.child("name")
        if nm is None and t == "var_pattern":
            nm = next((c for c in n.children if c.type == "identifier"), None)
        m.add_decl(sc, nm, "LocalVar")
        return sc
    if t == "foreach_statement":
        nsc = m.new_scope("foreach", n, sc)
        left = n.child("left")
        if left is not None and left.type == "identifier":
            m.add_decl(nsc, left, "LocalVar")
        return nsc
    if t == "catch_clause":
        return m.new_scope("catch", n, sc)
    if t in ("from_clause", "let_clause", "join_clause", "join_into_clause", "query_continuation"):
        nm = n.child("name")
        if nm is None:
            nm = next((c for c in n.children if c.type == "identifier"), None)
        m.add_decl(sc, nm, "LocalVar")
        return sc
    if t in _CS_STMT_SCOPES:
        return m.new_scope(_CS_STMT_SCOPES[t], n, sc)
    if t == "block":
        p = n.parent
        if p is not None and (p.type in _CS_FUNCS or p.type == "catch_clause"):
            return sc
        return m.new_scope("block", n, sc)
    return sc


def _csharp_run(code: str, omap):
    src = code.encode("utf-8")
    root, _ = _parser().parse("csharp", src)
    errors = _errors(root)
    m = _Cs(src, omap)
    m.walk(root, m.root, _cs_handler)
    return m.finish(errors)


_CS_WRAP = "class _W {\n"


def analyse_csharp(code: str, omap):
    """A member written without its class (a constructor, for one) does not parse on its own.  When the snippet
    as given has parse errors it is analysed again inside a one-line wrapper class; offsets are shifted back so
    that every occurrence id is an offset in `code`, and the wrapper's own declaration is dropped.  A snippet
    that parses as given is analysed as given, and one that fails both ways reports its own parse errors."""
    res = _csharp_run(code, omap)
    if not res["errors"]:
        return res
    plen = len(_CS_WRAP)
    wrapped = _csharp_run(_CS_WRAP + code + "\n}", lambda o: omap(o - plen))
    if wrapped["errors"]:
        return res
    wrapped["occ"] = {k: v for k, v in wrapped["occ"].items() if k[-1] >= 0}
    wrapped["names"] = {k: v for k, v in wrapped["names"].items() if k in wrapped["occ"]}
    wrapped["decls"] = [d for d in wrapped["decls"] if d["key"][-1] >= 0]
    return wrapped
