"""Review E, K1 (see review_e/ADDENDUM.md): identifier kind inferred without the original name.
Run in the container (clang for C++).  Output: k1_kinds.json  (one row per test unit, GSCS + Public5)."""
import ast, glob, json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
CUR = os.path.join(ROOT, "athena-corpus", "curation")
sys.path.insert(0, CUR)
sys.path.insert(0, os.path.join(ROOT, "athena-sim"))
import tsbind  # noqa: E402
import curate  # noqa: E402
from athena.evaluate import apply_rename  # noqa: E402

TS = tsbind.TreeSitter(tsbind.find_library(os.path.join(CUR, "libtsall.so")))


# ------------------------------------------------------------------ GSCS: C++ (clang JSON AST)
def cpp_kind(code, name):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "s.cpp")
        open(p, "w").write("#include <string>\n#include <vector>\nusing namespace std;\n" + code)
        r = subprocess.run(["clang++", "-std=c++17", "-fsyntax-only", "-Xclang", "-ast-dump=json", p],
                           capture_output=True, text=True, timeout=120)
        tree = json.loads(r.stdout)
    found = []

    def walk(n, parent_kind):
        k = n.get("kind")
        if n.get("name") == name and not n.get("isImplicit") and k in (
                "CXXRecordDecl", "EnumDecl", "FunctionDecl", "CXXMethodDecl", "ParmVarDecl", "FieldDecl", "VarDecl"):
            found.append((n, parent_kind))
        for c in n.get("inner", []) or []:
            walk(c, k)
    walk(tree, None)
    if not found:
        return None, "no declaration"
    n, parent = found[0]
    k = n["kind"]
    qt = (n.get("type") or {}).get("qualType", "")
    if k in ("CXXRecordDecl", "EnumDecl"):
        return "class", k
    if k in ("FunctionDecl", "CXXMethodDecl"):
        ret = qt.split("(")[0].strip()
        return ("procedure" if ret == "void" else "function"), qt
    if k == "ParmVarDecl":
        return "parameter", qt
    is_const = qt.startswith("const ") or bool(n.get("constexpr"))
    is_bool = qt.replace("const ", "").strip() == "bool"
    member = k == "FieldDecl" or parent == "CXXRecordDecl"
    if is_const:
        return "constant", qt
    if is_bool:
        return "boolean_variable", qt
    return ("field" if member else "variable"), qt


# ------------------------------------------------------------------ GSCS: Java (tree-sitter-java)
def java_kind(code, name):
    src = code.encode()
    root, _err = TS.parse("java", src)
    for n in root.walk():
        if n.type != "identifier" or n.text(src) != name or n.field != "name":
            continue
        p = n.parent
        if p.type in ("class_declaration", "interface_declaration", "enum_declaration", "record_declaration"):
            return "class", p.type
        if p.type == "method_declaration":
            t = p.child("type")
            return ("procedure" if t is not None and t.text(src) == "void" else "function"), p.type
        if p.type in ("formal_parameter", "spread_parameter"):
            return "parameter", p.type
        if p.type == "variable_declarator":
            decl = p.parent
            mods = [c for c in decl.children if c.type == "modifiers"]
            modtxt = mods[0].text(src) if mods else ""
            t = decl.child("type")
            ttxt = t.text(src) if t is not None else ""
            if re.search(r"\bfinal\b", modtxt):
                return "constant", decl.type
            if ttxt == "boolean":
                return "boolean_variable", decl.type
            return ("field" if decl.type == "field_declaration" else "variable"), decl.type
    return None, "no declaration"


# ------------------------------------------------------------------ GSCS: Python (ast)
def _boolish(v):
    if isinstance(v, ast.Constant) and isinstance(v.value, bool):
        return True
    if isinstance(v, ast.Compare):
        return True
    if isinstance(v, ast.UnaryOp) and isinstance(v.op, ast.Not):
        return True
    if isinstance(v, ast.BoolOp):
        return all(_boolish(x) for x in v.values)
    return False


def _literal(v):
    if isinstance(v, ast.Constant) and isinstance(v.value, (int, float, str)) and not isinstance(v.value, bool):
        return True
    if isinstance(v, (ast.Tuple, ast.List)):
        return all(_literal(x) for x in v.elts)
    if isinstance(v, ast.UnaryOp) and isinstance(v.op, ast.USub):
        return _literal(v.operand)
    return False


def _returns_value(fn):
    def visit(n):
        for c in ast.iter_child_nodes(n):
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                continue
            if isinstance(c, ast.Return) and c.value is not None and not (
                    isinstance(c.value, ast.Constant) and c.value.value is None):
                return True
            if visit(c):
                return True
        return False
    return visit(fn)


def py_kind(code, name, variant):
    tree = ast.parse(code)
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef) and n.name == name:
            return "class", "ClassDef"
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return ("function" if _returns_value(n) else "procedure"), "FunctionDef"
        if isinstance(n, ast.arg) and n.arg == name:
            return "parameter", "arg"
    binds, member = [], False   # values bound to the name (None = not a plain value binding)
    for n in ast.walk(tree):
        if isinstance(n, (ast.Assign, ast.AnnAssign)):
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            for t in targets:
                for x in ast.walk(t):
                    if isinstance(x, ast.Name) and x.id == name and isinstance(x.ctx, ast.Store):
                        binds.append(n.value if t is x else None)
                    if (isinstance(x, ast.Attribute) and x.attr == name and isinstance(x.value, ast.Name)
                            and x.value.id == "self" and isinstance(x.ctx, ast.Store)):
                        member = True
                        binds.append(n.value if t is x else None)
        elif isinstance(n, ast.AugAssign):
            t = n.target
            if (isinstance(t, ast.Name) and t.id == name) or (isinstance(t, ast.Attribute) and t.attr == name):
                binds.append(None)
        elif isinstance(n, (ast.For, ast.comprehension, ast.With, ast.ExceptHandler)):
            tgt = getattr(n, "target", None)
            if tgt is not None and any(isinstance(x, ast.Name) and x.id == name for x in ast.walk(tgt)):
                binds.append(None)
    if not binds:
        return None, "no declaration"
    if member:
        return "field", "self attribute"
    if all(v is not None and _boolish(v) for v in binds):
        return "boolean_variable", "bool values"
    if variant == "B" and len(binds) == 1 and binds[0] is not None and _literal(binds[0]):
        return "constant", "bound once to a literal"
    return "variable", "assignment"


def gscs_rows():
    rows = []
    base = os.path.join(ROOT, "athena-sim", "packs", "gscs", "benchmark", "violations")
    for f in sorted(glob.glob(os.path.join(base, "*", "*.json"))):
        v = json.load(open(f))
        if v["split"] != "test":
            continue
        lang, code, inj = v["language"], v["codeContextWithViolation"], v["injectedName"]
        row = dict(pack="gscs", unit_id=os.path.basename(f)[:-5], language=lang, gold=v["identifierKind"],
                   original=v["originalName"], injected=inj)
        if lang == "cpp":
            row["predA"], row["whyA"] = cpp_kind(code, inj)
            row["predB"], row["whyB"] = row["predA"], row["whyA"]
        elif lang == "java":
            row["predA"], row["whyA"] = java_kind(code, inj)
            row["predB"], row["whyB"] = row["predA"], row["whyA"]
        else:
            row["predA"], row["whyA"] = py_kind(code, inj, "A")
            row["predB"], row["whyB"] = py_kind(code, inj, "B")
        rows.append(row)
    return rows


# ------------------------------------------------------------------ Public5: the benchmark's own extractor
EXT = {"python": "py", "java": "java", "csharp": "cs", "typescript": "ts", "javascript": "js"}


def _decl_kind(lang, code, name):
    content = code.encode()
    ff = curate.analyze(lang, f"snippet.{EXT[lang]}", content, TS)
    if not ff.parse_ok and lang == "python":
        lines = code.split("\n")
        ind = min((len(l) - len(l.lstrip())) for l in lines if l.strip())
        code2 = "\n".join(l[ind:] for l in lines)
        ff = curate.analyze(lang, "snippet.py", code2.encode(), TS)
    if not ff.parse_ok:
        return None, "parse failed: " + str(ff.skip_reason)
    ks = [d.kind for d in ff.decls if d.name == name]
    if not ks:
        return None, "no declaration"
    return ks[0], ("several: " + ",".join(map(str, ks))) if len(set(ks)) > 1 else "decl"


def p5_rows():
    rows = []
    idx = set(open(os.path.join(ROOT, "p5_units.txt")).read().split())
    for f in sorted(glob.glob(os.path.join(ROOT, "athena-corpus", "benchmark", "violations", "*", "*.json"))):
        uid = os.path.basename(f)[:-5]
        if uid not in idx:
            continue
        v = json.load(open(f))
        lang = v["language"]
        s = json.load(open(os.path.join(ROOT, "athena-corpus", "benchmark", "snippets", lang, v["snippetId"] + ".json")))
        code = s["codeContext"]
        viol, n = apply_rename(code, v["originalName"], v["injectedName"])
        before, wb = _decl_kind(lang, code, v["originalName"])
        after, wa = _decl_kind(lang, viol, v["injectedName"])
        rows.append(dict(pack="public5", unit_id=uid, language=lang, gold=v["identifierKind"], original=v["originalName"],
                         injected=v["injectedName"], before=before, whyBefore=wb, predA=after, whyA=wa,
                         predB=after, whyB=wa))
    return rows


if __name__ == "__main__":
    rows = gscs_rows() + p5_rows()
    json.dump(rows, open(os.path.join(ROOT, "k1_kinds.json"), "w"), indent=1)
    print(len(rows), "rows written")
