"""Hand-written controls for the scope-aware rename check (WP3 task 3.2).

Run from the curation folder:  python3 -m unittest discover -s tests_scope -v

Every case states the expected outcome of check 2 (binding conflict) from the rules of the language, written
before the resolver was run on it.  Cases marked `blind=True` are the ones a plain word-collision screen flags;
the point of the check is that it flags the real conflicts and leaves the harmless collisions alone.
"""
from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from scope_check import check_rename  # noqa: E402

# (language, label, code, injected, suggested, expect_binding_conflict)
CASES = []


def case(lang, label, code, old, new, conflict):
    CASES.append((lang, label, code, old, new, conflict))


# ------------------------------------------------------------------------------------------------ C++
CPP_BASE = """int Foo::run(int total, int n) {
	int count = 0;
	for (int k = 0; k < n; k++) {
		int tmp = total + k;
		count += tmp;
	}
	{
		int other = 1;
		count += other;
	}
	return count;
}
"""
case("cpp", "fresh name", CPP_BASE, "count", "zzFresh", False)
case("cpp", "name used in a nested block captures the outer variable", CPP_BASE, "count", "tmp", True)
case("cpp", "name of a variable in a nested sibling block", CPP_BASE, "count", "other", True)
case("cpp", "name of a parameter in the same scope", CPP_BASE, "count", "total", True)
case("cpp", "reserved word", CPP_BASE, "count", "int", True)
case("cpp", "name only used outside the snippet scope: unused external name", CPP_BASE, "count", "scale", False)
case("cpp", "sibling scopes do not conflict",
     "void f(int a) {\n\t{ int x = a; use(x); }\n\t{ int y = a; use(y); }\n}\n", "x", "y", False)
case("cpp", "outer variable is captured by an inner declaration",
     "void f(int a) {\n\tint x = a;\n\t{ int y = 2; use(x, y); }\n}\n", "x", "y", True)
case("cpp", "inline method: field used unqualified is captured by the renamed parameter",
     "class C {\n\tint size;\n\tvoid f(int old) { size = old; }\n};\n", "old", "size", True)
case("cpp", "out-of-class method: unresolved member name is captured by the renamed parameter",
     "void C::f(int old) {\n\tsize_ = old;\n}\n", "old", "size_", True)
case("cpp", "called function is captured by the renamed parameter",
     "void f(int old) {\n\tg(old);\n}\n", "old", "g", True)
case("cpp", "renaming an out-of-class method: recursive call is captured by a parameter of the new name",
     "int Foo::run(int n) {\n\treturn n > 0 ? run(n - 1) : 0;\n}\n", "run", "n", True)
case("cpp", "renaming an out-of-class method to a fresh name",
     "int Foo::run(int n) {\n\treturn n > 0 ? run(n - 1) : 0;\n}\n", "run", "zzFresh", False)
case("cpp", "renaming an out-of-class method: same-named member of another object is not the method",
     "int Foo::run(int n) {\n\treturn other->run(n);\n}\n", "run", "n", False)
case("cpp", "member selected with . is not the local",
     "void f(Obj &o, int old) {\n\to.size = old;\n}\n", "old", "size", False)
case("cpp", "member selected with -> is not the local",
     "void f(Obj *o, int old) {\n\to->size = old;\n}\n", "old", "size", False)
case("cpp", "qualified name is not the local",
     "int f(int old) {\n\treturn Foo::size + old;\n}\n", "old", "size", False)
case("cpp", "label namespace is separate",
     "int f(int old) {\n\tif (old) goto done;\n\told++;\ndone:\n\treturn old;\n}\n", "old", "done", False)
case("cpp", "loop variable captures",
     "int f(int old, int n) {\n\tfor (int i = 0; i < n; i++) {\n\t\told += i;\n\t}\n\treturn old;\n}\n", "old", "i", True)
case("cpp", "lambda parameter captures",
     "int f(int old) {\n\tauto g = [&](int a) { return a + old; };\n\treturn g(1);\n}\n", "old", "a", True)
case("cpp", "second declaration in the same scope",
     "void f() {\n\tint old = 1;\n\tuse(old);\n\tint later = 2;\n\tuse(later);\n}\n", "old", "later", True)
case("cpp", "unscoped enumerator is visible in the enclosing scope",
     "int f(int old) {\n\tenum { A, B };\n\treturn old + A + B;\n}\n", "old", "A", True)
case("cpp", "structured binding names share the scope",
     "void f() {\n\tauto [p, q] = make();\n\tuse(p, q);\n}\n", "p", "q", True)
case("cpp", "constructor initialiser: member name and parameter of the same name",
     "Foo::Foo(int old) : size_(old) {}\n", "old", "size_", False)
case("cpp", "shadowing a field with a new local when the field is not read",
     "class C {\n\tint size;\n\tint f() { int old = 1; return old; }\n};\n", "old", "size", False)
case("cpp", "shadowing a field that is read in the body",
     "class C {\n\tint size;\n\tint f() { int old = 1; return old + size; }\n};\n", "old", "size", True)

# ------------------------------------------------------------------------------------------------ C#
CS_BASE = """class C {
	int size;
	int Helper(int v) { return v; }
	public int Run(List<int> items, int n) {
		int total = 0;
		foreach (var it in items) { total += it; }
		for (int k = 0; k < n; k++) { total += k; }
		{ int tmp = 1; total += tmp; }
		return total;
	}
}
"""
case("csharp", "fresh name", CS_BASE, "total", "zzFresh", False)
case("csharp", "name of a parameter", CS_BASE, "total", "n", True)
case("csharp", "name of a foreach variable in a nested scope", CS_BASE, "total", "it", True)
case("csharp", "name of a for variable in a nested scope", CS_BASE, "total", "k", True)
case("csharp", "name of a local in a nested block", CS_BASE, "total", "tmp", True)
case("csharp", "field read unqualified is captured by the renamed local",
     "class C {\n\tint size;\n\tint Run() { int old = 1; return old + size; }\n}\n", "old", "size", True)
case("csharp", "field only reached through this. is not captured",
     "class C {\n\tint size;\n\tvoid Set(int old) { this.size = old; }\n}\n", "old", "size", False)
case("csharp", "member selected with . is not the local",
     "class C {\n\tvoid Set(Obj o, int old) { o.Size = old; }\n}\n", "old", "Size", False)
case("csharp", "sibling blocks do not conflict",
     "class C {\n\tvoid F() {\n\t\t{ int x = 1; Use(x); }\n\t\t{ int y = 2; Use(y); }\n\t}\n}\n", "x", "y", False)
case("csharp", "method called unqualified is captured by the renamed local",
     "class C {\n\tint Helper(int v) { return v; }\n\tint Run(int old) { return Helper(old); }\n}\n", "old", "Helper", True)
case("csharp", "reserved word",
     "class C {\n\tint Run(int old) { return old; }\n}\n", "old", "class", True)
case("csharp", "named argument is not the local",
     "class C {\n\tvoid Run(int old) { Helper(x: old); }\n}\n", "old", "x", False)
case("csharp", "object initialiser member is not the local",
     "class C {\n\tFoo Make(int old) { return new Foo { Size = old }; }\n}\n", "old", "Size", False)
case("csharp", "pattern variable in the same member",
     "class C {\n\tint Run(object o, int old) {\n\t\tif (o is Foo f) { return f.A + old; }\n\t\treturn 0;\n\t}\n}\n", "old", "f", True)
case("csharp", "out variable in the same member",
     "class C {\n\tint Run(string s, int old) {\n\t\tint.TryParse(s, out var parsed);\n\t\treturn parsed + old;\n\t}\n}\n", "old", "parsed", True)
case("csharp", "lambda parameter",
     "class C {\n\tFunc<int, int> Make(int old) { return a => a + old; }\n}\n", "old", "a", True)
case("csharp", "local function parameter is a separate scope but the C# rule still rejects the shadowing",
     "class C {\n\tint Run(int old) {\n\t\tint Local(int z) { return z + old; }\n\t\treturn Local(1);\n\t}\n}\n", "old", "z", True)
case("csharp", "property read unqualified is captured",
     "class C {\n\tint Size { get; set; }\n\tint Run(int old) { return old + Size; }\n}\n", "old", "Size", True)
case("csharp", "tuple deconstruction names",
     "class C {\n\tvoid Run(int old) {\n\t\tvar (p, q) = Pair();\n\t\tUse(p, q, old);\n\t}\n}\n", "old", "q", True)
case("csharp", "using variable scope",
     "class C {\n\tvoid Run(int old) {\n\t\tusing (var s = Open()) { s.Read(old); }\n\t}\n}\n", "old", "s", True)
case("csharp", "catch variable scope",
     "class C {\n\tvoid Run(int old) {\n\t\ttry { F(old); } catch (Exception e) { Log(e); }\n\t}\n}\n", "old", "e", True)
case("csharp", "name reused after the nested scope ended",
     "class C {\n\tvoid Run() {\n\t\t{ int tmp = 1; Use(tmp); }\n\t\tint old = 2;\n\t\tUse(old);\n\t}\n}\n", "old", "tmp", True)

# Members written without their class (constructors do not parse on their own): analysed inside a wrapper class
CS_CTOR = "public Foo(int old, string name)\n{\n\tint tmp = old;\n\ttotal = old;\n\tthis.size = tmp;\n}\n"
case("csharp", "constructor without its class: fresh name", CS_CTOR, "old", "zzFresh", False)
case("csharp", "constructor without its class: name of a local", CS_CTOR, "old", "tmp", True)
case("csharp", "constructor without its class: name of another parameter", CS_CTOR, "old", "name", True)
case("csharp", "constructor without its class: field read unqualified is captured", CS_CTOR, "old", "total", True)
case("csharp", "constructor without its class: field selected through this. is not the parameter",
     CS_CTOR, "old", "size", False)
case("csharp", "constructor with a base initialiser",
     "protected Foo(int old) : base(old)\n{\n\tInit(old);\n}\n", "old", "zzFresh", False)

# ------------------------------------------------------------------------------------------------ Python
PY_BASE = """def run(items, limit):
    total = 0
    for item in items:
        total += item
    return min(total, limit)
"""
case("python", "fresh name", PY_BASE, "total", "zz_fresh", False)
case("python", "name of a parameter", PY_BASE, "total", "limit", True)
case("python", "name of the loop variable", PY_BASE, "total", "item", True)
case("python", "builtin used in the body is captured", PY_BASE, "total", "min", True)
case("python", "reserved word", PY_BASE, "total", "for", True)
case("python", "attribute selected through self is not the local",
     "class C:\n    def f(self, old):\n        self.size = old\n", "old", "size", False)
case("python", "attribute read through self is not the local",
     "class C:\n    def f(self, old):\n        return self.size + old\n", "old", "size", False)
case("python", "name in a different function is a different scope",
     "def f(old):\n    return old\n\n\ndef g(other):\n    return other\n", "old", "other", False)
case("python", "global read in the function is captured",
     "LIMIT = 3\n\n\ndef f(old):\n    return old + LIMIT\n", "old", "LIMIT", True)
case("python", "except variable",
     "def f(old):\n    try:\n        g(old)\n    except ValueError as err:\n        return err\n", "old", "err", True)


class TestControls(unittest.TestCase):
    def test_cases(self):
        wrong = []
        for lang, label, code, old, new, expect in CASES:
            r = check_rename(lang, code, old, new)
            self.assertEqual(r["status"], "ok", f"{lang}: {label}: {r}")
            if r["binding_conflict"] != expect:
                wrong.append(f"{lang}: {label}: {old} -> {new}: expected {expect}, got {r['binding_conflict']} "
                             f"{r['binding_reasons'][:2]}")
        self.assertEqual(wrong, [], "\n" + "\n".join(wrong))

    def test_every_language_has_both_outcomes(self):
        for lang in ("cpp", "csharp", "python"):
            outcomes = {c[5] for c in CASES if c[0] == lang}
            self.assertEqual(outcomes, {True, False}, lang)

    def test_scope_blind_is_a_superset_of_the_harmless_collisions(self):
        """Harmless collisions (blind flags, check 2 does not) exist in every language: that is the false alarm
        the scope-aware check removes."""
        for lang in ("cpp", "csharp", "python"):
            harmless = [c for c in CASES if c[0] == lang and not c[5]
                        and check_rename(lang, c[2], c[3], c[4])["scope_blind"]]
            self.assertTrue(harmless, lang)

    def test_unparsable_snippet_is_unsupported_not_a_conflict(self):
        for lang, code in (("cpp", "int f( {"), ("csharp", "class C { void F( {"), ("python", "def f(:\n")):
            r = check_rename(lang, code, "f", "g")
            self.assertEqual(r["status"], "unsupported", lang)
            self.assertFalse(r["binding_conflict"])

    def test_constructor_without_class_reports_source_offsets(self):
        code = "public Foo(int old)\n{\n\tUse(old);\n}\n"
        from scope_check import analyse
        info = analyse("csharp", code)
        self.assertEqual(info["errors"], [])
        offsets = sorted(k[-1] for k in info["occ"])
        self.assertTrue(offsets and offsets[0] >= 0)
        self.assertLess(offsets[-1], len(code))
        self.assertEqual(code[offsets[0]:offsets[0] + 3], "Foo")

    def test_name_not_in_snippet(self):
        r = check_rename("cpp", "int f(int a) { return a; }\n", "zzz", "b")
        self.assertEqual(r["status"], "no_occurrence")

    def test_non_ascii_source(self):
        code = "// \u00e9\u4e2d\u6587\nint f(int old) {\n\tint tmp = old;\n\treturn tmp;\n}\n"
        self.assertTrue(check_rename("cpp", code, "old", "tmp")["binding_conflict"])
        self.assertFalse(check_rename("cpp", code, "old", "zzFresh")["binding_conflict"])

    def test_deterministic(self):
        for lang, label, code, old, new, expect in CASES[:12]:
            self.assertEqual(check_rename(lang, code, old, new), check_rename(lang, code, old, new))


if __name__ == "__main__":
    unittest.main()
