#!/usr/bin/env python3
"""Study 2 kinds and facets (facets_s2.py) on hand-written snippets. The expected tables are typed in by hand from
packs/godot-s2/KINDS.md and packs/dotnet-runtime-s2/KINDS.md; they are never read from extractor output.

  python3 -m unittest discover -s tests_s2       (from the curation folder)
"""
import collections
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import facets_s2  # noqa: E402
import tsbind  # noqa: E402

CPP = b"""void free_fn(int p_a, Foo &r_b, int x);
namespace ns {
void g(const Foo &p_c) {}
}
class B {
public:
    void m(const Foo &p_a, Foo *r_b, const char **p_c, Foo *const r_d, int p_e[], Foo &&p_f, void (*p_cb)(int),
            const char *const *p_h, int plain, Foo const *p_g);
    B(int p_size);
    template <typename T>
    void t(T &r_out) {}
#ifdef TOOLS_ENABLED
    void tool(Node *p_node);
#endif
};
void B::n(Foo const *p_g, Vector<int> &r_h, int p_v) {}
Foo *B::get(int p_i) {
    auto l = [](int p_l) { return p_l; };
    return nullptr;
}
"""

# (function, name) -> (metadata kind, inferred kind, owner, indirection, pointee_const)
CPP_EXPECTED = {
    ("free_fn", "p_a"): ("parameter", "parameter", "function", None, None),
    ("free_fn", "r_b"): ("parameter", "parameter", "function", "lref", False),
    ("free_fn", "x"): ("parameter", "parameter", "function", None, None),
    ("g", "p_c"): ("parameter", "parameter", "function", "lref", True),
    ("m", "p_a"): ("input_parameter", "input_parameter", "method", "lref", True),
    ("m", "r_b"): ("output_parameter", "output_parameter", "method", "ptr", False),
    ("m", "p_c"): ("input_parameter", "output_parameter", "method", "ptr", False),
    ("m", "r_d"): ("output_parameter", "output_parameter", "method", "ptr", False),
    ("m", "p_e"): ("input_parameter", "output_parameter", "method", "array", False),
    ("m", "p_f"): ("input_parameter", "output_parameter", "method", "rref", False),
    ("m", "p_cb"): ("input_parameter", "output_parameter", "method", "ptr", False),
    ("m", "p_h"): ("input_parameter", "input_parameter", "method", "ptr", True),
    ("m", "plain"): ("parameter", "input_parameter", "method", None, None),
    ("m", "p_g"): ("input_parameter", "input_parameter", "method", "ptr", True),
    ("B", "p_size"): ("input_parameter", "input_parameter", "method", None, None),
    ("t", "r_out"): ("output_parameter", "output_parameter", "method", "lref", False),
    ("tool", "p_node"): ("input_parameter", "output_parameter", "method", "ptr", False),
    ("n", "p_g"): ("input_parameter", "input_parameter", "method", "ptr", True),
    ("n", "r_h"): ("output_parameter", "output_parameter", "method", "lref", False),
    ("n", "p_v"): ("input_parameter", "input_parameter", "method", None, None),
    ("get", "p_i"): ("input_parameter", "input_parameter", "method", None, None),
}

CS = b"""class A {
    [ThreadStatic] private static int t_x;
    [System.ThreadStaticAttribute] static int t_y;
    internal static readonly int s_z, s_w;
    public const int K = 1;
    private const int k2 = 2;
    protected internal int pi;
    private protected int pp;
    protected int pr;
    int _a;
    private readonly bool _flag;
    public bool Flag;
    public static int Count;
    [ThreadStatic] public static int PublicTs;
    [ThreadStatic] private int notStatic;
    struct S { int _inner; }
    void M() { const int LocalK = 3; int local = 0; }
}
"""

# name -> (kind, access) ; kind_infer must equal kind
CS_EXPECTED = {
    "t_x": ("threadstatic_field", "private"), "t_y": ("threadstatic_field", "private"),
    "s_z": ("static_field", "internal"), "s_w": ("static_field", "internal"),
    "K": ("constant", "public"), "k2": ("constant", "private"),
    "pi": ("field", "protected internal"), "pp": ("field", "private protected"), "pr": ("field", "protected"),
    "_a": ("instance_field", "private"), "_flag": ("instance_field", "private"),
    "Flag": ("public_field", "public"), "Count": ("public_field", "public"),
    "PublicTs": ("public_field", "public"), "notStatic": ("instance_field", "private"),
    "_inner": ("instance_field", "private"),
}


class _Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ts = tsbind.TreeSitter(tsbind.find_library(None))


class TestGodotParams(_Base):
    def setUp(self):
        self.diag = collections.Counter()
        self.ff = facets_s2.extract_s2("cpp", "x.cpp", CPP, self.ts, self.diag)
        self.assertFalse(self.ff.error_spans)

    def _owner_fn(self, d):
        """Name of the function a parameter belongs to: the nearest function name before it on the same lines."""
        txt = CPP[:d.start].decode()
        best = None
        for fn in ("free_fn", "g", "m", "B", "t", "tool", "n", "get"):
            for pat in (f" {fn}(", f"::{fn}(", f"\n{fn}("):
                i = txt.rfind(pat)
                if i >= 0 and (best is None or i > best[0]):
                    best = (i, fn)
        return best[1]

    def test_table(self):
        got = {}
        for d in self.ff.decls:
            if d.extra.get("kind_s1") != "parameter" or d.exempt:
                continue
            s2 = d.extra["s2"]
            got[(self._owner_fn(d), d.name)] = (d.kind, d.extra["kind_infer"], s2["owner"], s2["indirection"],
                                                s2["pointee_const"])
        self.assertEqual(got, CPP_EXPECTED)

    def test_lambda_param_keeps_study1_kind(self):
        lam = [d for d in self.ff.decls if d.name == "p_l"]
        self.assertEqual(len(lam), 1)
        self.assertEqual((lam[0].kind, lam[0].extra["kind_infer"], lam[0].exempt),
                         ("parameter", "parameter", "lambda_param"))
        self.assertNotIn("s2", lam[0].extra)

    def test_other_kinds_unchanged(self):
        for d in self.ff.decls:
            if d.extra["kind_s1"] != "parameter":
                self.assertEqual(d.kind, d.extra["kind_s1"])
                self.assertEqual(d.extra["kind_infer"], d.kind)

    def test_owner_via(self):
        via = {(d.name, d.extra["s2"]["owner_via"]) for d in self.ff.decls if "s2" in d.extra}
        self.assertIn(("r_h", "qualified"), via)
        self.assertIn(("p_node", "class_body"), via)
        self.assertIn(("x", "namespace"), via)

    def test_study1_extract_unchanged(self):
        import lang_ts
        s1 = lang_ts.extract("cpp", "x.cpp", CPP, self.ts)
        self.assertEqual([(d.name, d.start, d.kind, d.exempt) for d in s1.decls],
                         [(d.name, d.start, d.extra["kind_s1"], d.exempt) for d in self.ff.decls])


class TestDotnetFields(_Base):
    def setUp(self):
        self.diag = collections.Counter()
        self.ff = facets_s2.extract_s2("csharp", "x.cs", CS, self.ts, self.diag)
        self.assertFalse(self.ff.error_spans)

    def test_table(self):
        got = {d.name: (d.kind, d.extra["s2"]["access"]) for d in self.ff.decls if "s2" in d.extra}
        self.assertEqual(got, CS_EXPECTED)
        self.assertEqual(self.diag.get("field_without_decl", 0), 0)

    def test_infer_equals_metadata_and_no_exempt(self):
        for d in self.ff.decls:
            if "s2" in d.extra:
                self.assertEqual(d.extra["kind_infer"], d.kind)
                self.assertIsNone(d.exempt)

    def test_locals_unchanged(self):
        k = {d.name: d.kind for d in self.ff.decls}
        self.assertEqual((k["LocalK"], k["local"]), ("constant", "variable"))

    def test_kind_function(self):
        f = facets_s2.cs_field_kind
        self.assertEqual(f("internal", True, False, True), "threadstatic_field")
        self.assertEqual(f("public", True, False, True), "public_field")
        self.assertEqual(f("private protected", False, False, False), "field")
        self.assertEqual(f("protected", False, True, False), "constant")


class TestOtherLanguages(_Base):
    def test_java_untouched(self):
        ff = facets_s2.extract_s2("java", "X.java", b"class X { private int a; void f(int b) {} }", self.ts)
        for d in ff.decls:
            self.assertEqual((d.kind, d.extra["kind_infer"]), (d.extra["kind_s1"], d.extra["kind_s1"]))
            self.assertNotIn("s2", d.extra)


if __name__ == "__main__":
    unittest.main()
