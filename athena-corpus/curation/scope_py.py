"""Python front end for the scope-aware check: ast + symtable (stdlib)."""
import ast
import builtins
import keyword
import re
import symtable

BUILTINS = set(dir(builtins))


class _Src:
    def __init__(self, code):
        self.lines = code.splitlines(keepends=True)
        self.starts = [0]
        for l in self.lines:
            self.starts.append(self.starts[-1] + len(l))
        self.code = code

    def off(self, lineno, col_bytes):
        line = self.lines[lineno - 1] if lineno - 1 < len(self.lines) else ""
        col = len(line.encode("utf-8")[:col_bytes].decode("utf-8", "ignore"))
        return self.starts[lineno - 1] + col


def _tables(t, acc):
    acc.append(t)
    for c in t.get_children():
        _tables(c, acc)
    return acc


def analyse(code, omap):
    res = {"errors": [], "occ": {}, "scopes": {}, "attrs": {}, "ext_uses": [], "unresolved_members": 0}
    try:
        tree = ast.parse(code)
        st = symtable.symtable(code, "snippet", "exec")
    except SyntaxError as e:
        res["errors"].append(f"SyntaxError: {e.msg} (line {e.lineno})")
        return res
    src = _Src(code)
    by_key = {}
    for t in _tables(st, []):
        by_key.setdefault((t.get_type(), t.get_name(), t.get_lineno()), []).append(t)

    def table_for(node):
        typ = "class" if isinstance(node, ast.ClassDef) else "function"
        name = getattr(node, "name", "lambda")
        ts = by_key.get((typ, name, node.lineno)) or []
        return ts.pop(0) if ts else None

    def sid(node):
        return ("module", 0) if node is None else (type(node).__name__, omap(src.off(node.lineno, node.col_offset)))

    # scope record: id -> {type, parent, locals:set, uses:set}
    def add_scope(s_id, table, parent):
        locs = {sy.get_name() for sy in table.get_symbols()
                if sy.is_local() or sy.is_parameter() or sy.is_imported() or sy.is_namespace()}
        res["scopes"][s_id] = {"type": table.get_type(), "parent": parent, "locals": locs, "uses": set()}

    add_scope(("module", 0), st, None)
    stack = [(st, ("module", 0), None)]  # (table, scope id, enclosing class id for self.x)

    def resolve(name):
        table, s_id, _ = stack[-1]
        try:
            sy = table.lookup(name)
        except KeyError:
            sy = None
        if sy is not None and table.get_type() != "module":
            if sy.is_local() or sy.is_parameter() or sy.is_imported() or sy.is_namespace():
                return ("attr", s_id, name) if table.get_type() == "class" else ("local", s_id, name)
            if sy.is_free():
                for t2, s2, _c in reversed(stack[:-1]):
                    if t2.get_type() == "function":
                        try:
                            if t2.lookup(name).is_local():
                                return ("local", s2, name)
                        except KeyError:
                            pass
        if name in res["scopes"][("module", 0)]["locals"]:
            return ("local", ("module", 0), name)
        return ("builtin", name)

    def occ(off_raw, key, name, load):
        o = omap(off_raw)
        res["occ"][("o", o)] = key
        if load:
            res["scopes"][stack[-1][1]]["uses"].add(name)
            if key[0] == "builtin":
                res["ext_uses"].append({"name": name, "scope": stack[-1][1]})

    def name_pos(node, kw):
        start = src.off(node.lineno, node.col_offset)
        m = re.compile(kw + r"\s+(" + re.escape(node.name) + r")\b").search(code, start)
        return m.start(1)

    def visit(node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            kw = "class" if isinstance(node, ast.ClassDef) else "def"
            occ(name_pos(node, kw), resolve(node.name), node.name, False)
            for d in node.decorator_list:
                visit(d)
            if isinstance(node, ast.ClassDef):
                for b in node.bases + [k.value for k in node.keywords]:
                    visit(b)
            else:
                for d in node.args.defaults + [x for x in node.args.kw_defaults if x is not None]:
                    visit(d)
            t = table_for(node)
            s_id = sid(node)
            add_scope(s_id, t, stack[-1][1])
            cls = s_id if isinstance(node, ast.ClassDef) else (stack[-1][1] if stack[-1][0].get_type() == "class" else stack[-1][2])
            stack.append((t, s_id, cls))
            if not isinstance(node, ast.ClassDef):
                a = node.args
                for arg in a.posonlyargs + a.args + a.kwonlyargs + ([a.vararg] if a.vararg else []) + ([a.kwarg] if a.kwarg else []):
                    occ(src.off(arg.lineno, arg.col_offset), resolve(arg.arg), arg.arg, False)
            for b in node.body:
                visit(b)
            stack.pop()
            return
        if isinstance(node, ast.Name):
            occ(src.off(node.lineno, node.col_offset), resolve(node.id), node.id, isinstance(node.ctx, ast.Load))
            return
        if isinstance(node, ast.Attribute):
            end = src.off(node.end_lineno, node.end_col_offset) - len(node.attr)
            cls = stack[-1][2]
            if isinstance(node.value, ast.Name) and node.value.id in ("self", "cls") and cls is not None:
                key = ("attr", cls, node.attr)
                if isinstance(node.ctx, ast.Store):
                    res["attrs"].setdefault(cls, set()).add(node.attr)
            else:
                key = ("member", node.attr)
                res["unresolved_members"] += 1
            visit(node.value)
            occ(end, key, node.attr, False)
            return
        if isinstance(node, ast.ExceptHandler) and node.name:
            if node.type:
                visit(node.type)
            m = re.compile(r"as\s+(" + re.escape(node.name) + r")\b").search(code, src.off(node.lineno, node.col_offset))
            occ(m.start(1), resolve(node.name), node.name, False)
            for b in node.body:
                visit(b)
            return
        if isinstance(node, ast.alias):
            nm = (node.asname or node.name).split(".")[0]
            occ(src.off(node.lineno, node.col_offset), resolve(nm), nm, False)
            return
        if isinstance(node, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            res.setdefault("unsupported", []).append(type(node).__name__)
        for c in ast.iter_child_nodes(node):
            visit(c)

    for n in tree.body:
        visit(n)
    return res


def declaration_conflicts(info, injected, suggested):
    reasons = []
    if keyword.iskeyword(suggested) or suggested in ("self", "cls"):
        reasons.append("reserved word")
    sc = info["scopes"]

    def ancestors(s):
        out = []
        p = sc[s]["parent"]
        while p is not None:
            out.append(p)
            p = sc[p]["parent"]
        return out

    for s_id, s in sc.items():
        if injected not in s["locals"]:
            continue
        if suggested in s["locals"]:
            reasons.append(f"{suggested} already in the same namespace")
        for a in ancestors(s_id):
            if sc[a]["type"] != "class" and suggested in sc[a]["locals"]:
                reasons.append(f"{suggested} declared in an enclosing scope")
        for d_id, d in sc.items():
            if s_id in ancestors(d_id):
                if suggested in d["locals"]:
                    reasons.append(f"{suggested} declared in a nested scope")
        for u in info["ext_uses"]:
            if u["name"] == suggested and (u["scope"] == s_id or s_id in ancestors(u["scope"])):
                reasons.append(f"builtin {suggested} used in scope")
    for cls, attrs in info["attrs"].items():
        names = attrs | (sc[cls]["locals"] if cls in sc else set())
        if injected in names and suggested in names:
            reasons.append(f"{suggested} already an attribute of the class")
    return sorted(set(reasons))
