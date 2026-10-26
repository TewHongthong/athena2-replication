"""C++ front end for the scope-aware check: clang -ast-dump=json."""
import json
import os
import subprocess
import tempfile

CLANG = ["clang++", "-std=c++17", "-fsyntax-only", "-Xclang", "-ast-dump=json"]
DECL_KINDS = {"VarDecl", "ParmVarDecl", "FieldDecl", "FunctionDecl", "CXXMethodDecl", "CXXConstructorDecl",
              "CXXDestructorDecl", "CXXRecordDecl", "EnumDecl", "EnumConstantDecl", "TypedefDecl", "TypeAliasDecl",
              "NamespaceDecl", "BindingDecl"}
SCOPE_KINDS = {"NamespaceDecl", "CXXRecordDecl", "FunctionDecl", "CXXMethodDecl", "CXXConstructorDecl",
               "CXXDestructorDecl", "LambdaExpr", "CompoundStmt", "ForStmt", "CXXForRangeStmt", "IfStmt",
               "WhileStmt", "SwitchStmt", "CXXCatchStmt"}
CPP_KEYWORDS = set("""alignas alignof and and_eq asm auto bitand bitor bool break case catch char char8_t char16_t
char32_t class compl concept const consteval constexpr constinit const_cast continue co_await co_return co_yield
decltype default delete do double dynamic_cast else enum explicit export extern false float for friend goto if inline
int long mutable namespace new noexcept not not_eq nullptr operator or or_eq private protected public register
reinterpret_cast requires return short signed sizeof static static_assert static_cast struct switch template this
thread_local throw true try typedef typeid typename union unsigned using virtual void volatile wchar_t while xor
xor_eq""".split())


def _dump(code):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "snippet.cpp")
        open(p, "w").write(code)
        r = subprocess.run(CLANG + [p], capture_output=True, text=True, timeout=120)
        errors = [l for l in r.stderr.splitlines() if " error: " in l]
        return json.loads(r.stdout) if r.stdout.strip() else None, errors, p


def _off(loc):
    if not loc:
        return None
    if "offset" in loc:
        return loc["offset"]
    for k in ("expansionLoc", "spellingLoc"):
        if k in loc and "offset" in loc[k]:
            return loc[k]["offset"]
    return None


def analyse(code, omap):
    """omap: function mapping offsets of `code` to before-rename offsets.
    Returns dict(errors, occ, decls, ext_uses)."""
    ast, errors, path = _dump(code)
    res = {"errors": errors, "occ": {}, "decls": [], "ext_uses": [], "unresolved_members": 0}
    if ast is None:
        res["errors"].append("no AST")
        return res
    state = {"file": None}

    def upd(loc):
        if not loc:
            return
        for k in ("spellingLoc", "expansionLoc"):
            if k in loc:
                upd(loc[k])
        if "file" in loc:
            state["file"] = loc["file"]

    # pass 1: walk in emission order, tag main-file nodes, collect decl ids
    main_nodes = []  # (node, scope_path)
    id2key = {}

    def walk(n, in_main, scopes, implicit):
        upd(n.get("loc"))
        rg = n.get("range") or {}
        upd(rg.get("begin"))
        upd(rg.get("end"))
        kind = n.get("kind")
        has_loc = _off(n.get("loc")) is not None or _off(rg.get("begin")) is not None
        here_main = (state["file"] == path) if has_loc else in_main
        imp = implicit or bool(n.get("isImplicit"))
        if here_main and kind in DECL_KINDS and _off(n.get("loc")) is not None:
            o = omap(_off(n["loc"]))
            id2key[n["id"]] = ("src", kind, o)
            if not imp and n.get("name"):
                main_nodes.append(("decl", n, scopes))
        elif here_main and kind in ("DeclRefExpr", "MemberExpr") and not imp:
            main_nodes.append(("ref", n, scopes))
        new_scopes = scopes
        if here_main and kind in SCOPE_KINDS and not imp:
            b = _off(rg.get("begin")) if rg.get("begin") else _off(n.get("loc"))
            new_scopes = scopes + ((kind, omap(b) if b is not None else None),)
        for c in n.get("inner", []) or []:
            walk(c, here_main, new_scopes, imp)

    for top in ast.get("inner", []):
        walk(top, False, (("TU", 0),), False)

    for typ, n, scopes in main_nodes:
        kind = n["kind"]
        if typ == "decl":
            o = omap(_off(n["loc"]))
            key = ("src", kind, o)
            res["occ"][("d", kind, o)] = key
            res["decls"].append({"name": n["name"], "kind": kind, "key": key, "scope": scopes})
        else:
            ref = n.get("referencedDecl") or ({"id": n.get("referencedMemberDecl"), "name": n.get("name"),
                                                 "kind": "member"} if kind == "MemberExpr" else None)
            if not ref or not ref.get("id"):
                continue
            end = _off((n.get("range") or {}).get("end"))
            if end is None:
                continue
            o = omap(end)
            if ref["id"] in id2key:
                key = id2key[ref["id"]]
            else:
                key = ("ext", ref.get("kind"), ref.get("name"), json.dumps(ref.get("type"), sort_keys=True))
                # unqualified external use (could be captured by a local of the same name)
                name = ref.get("name") or ""
                if name.isidentifier():
                    res["ext_uses"].append({"name": name, "scope": scopes, "pos": o})
            res["occ"][("r", o)] = key
    return res


def declaration_conflicts(info_before, injected, suggested):
    """Check 3 (IDE-style): suggested name declared in, enclosing, or nested in the scope of a renamed decl, or an
    external name used in that scope, or a reserved word."""
    reasons = []
    if suggested in CPP_KEYWORDS:
        reasons.append("reserved word")
    renamed = [d for d in info_before["decls"] if d["name"] == injected]
    others = [d for d in info_before["decls"] if d["name"] == suggested]
    for r in renamed:
        rs = r["scope"]
        for d in others:
            ds = d["scope"]
            if rs[:len(ds)] == ds:
                reasons.append(f"{suggested} declared in enclosing/same scope ({d['kind']})")
            elif ds[:len(rs)] == rs:
                reasons.append(f"{suggested} declared in nested scope ({d['kind']})")
        for u in info_before["ext_uses"]:
            if u["name"] == suggested and u["scope"][:len(rs)] == rs:
                reasons.append(f"external name {suggested} used in scope")
    return sorted(set(reasons))
